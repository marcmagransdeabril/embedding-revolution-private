#!/usr/bin/env python3
"""Build and maintain a page-level SQLite BM25 index over reference PDFs.

Extracts per-page text and embedded PDF bookmarks (TOC) into an indexed SQLite
store (FTS5 + Porter stemming).

Pages with no text layer (scans) or an unreadable one (garbled font encodings)
are read with Tesseract OCR when the `tesseract` binary is on PATH. The PDF is
never modified: the OCR text is stored in the index with source "tesseract".
Pass --no-ocr to skip this step.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pymupdf


def repo_root(start: Path) -> Path:
    for p in (start, *start.parents):
        if (p / ".git").is_dir():
            return p
    return start


REPO_ROOT = repo_root(Path(__file__).resolve())
DEFAULT_REFERENCES = REPO_ROOT / "references"
DEFAULT_DB_PATH = DEFAULT_REFERENCES / ".ground-index" / "index.sqlite"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS pages (
    doc TEXT NOT NULL,
    page_no INTEGER NOT NULL,
    text TEXT NOT NULL,
    source TEXT NOT NULL,
    PRIMARY KEY (doc, page_no)
);

CREATE TABLE IF NOT EXISTS toc (
    doc TEXT NOT NULL,
    title TEXT NOT NULL,
    level INTEGER NOT NULL,
    page_no INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_toc_doc_page ON toc(doc, page_no);

CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
    doc UNINDEXED,
    page_no UNINDEXED,
    text,
    tokenize='porter unicode61'
);
"""


def sanitize_text(text: str) -> str:
    """Sanitize text for indexing: strip null bytes, normalize ligatures/Unicode, normalize whitespace."""
    if not text:
        return ""
    # Strip null bytes (\x00) which break SQLite / C strings
    text = text.replace("\x00", "")
    # Normalize unicode ligatures (e.g., ﬁ -> fi, ﬂ -> fl, ﬀ -> ff) and characters
    text = unicodedata.normalize("NFKC", text)
    # Normalize horizontal whitespace sequences to a single space
    text = re.sub(r"[^\S\r\n]+", " ", text)
    # Collapse 3+ newlines to 2 newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


OCR_DPI = 300
OCR_LANG = "eng"
OCR_TIMEOUT_S = 180
# Share of control characters (other than whitespace) above which a page's text layer is
# treated as unreadable. Measured on the reference corpus: correct pages stay below 0.07,
# a PDF with a broken font encoding sits above 0.11.
GARBLED_CONTROL_RATIO = 0.08


def find_tesseract() -> str | None:
    """Path of the `tesseract` binary, or None when it is not installed."""
    return shutil.which("tesseract")


def is_garbled(raw_text: str) -> bool:
    """True when extracted text is mostly control characters (broken font encoding)."""
    compact = re.sub(r"\s", "", raw_text)
    if len(compact) < 30:
        return False
    control = sum(1 for c in raw_text if ord(c) < 32 and c not in "\t\n\r")
    return control / len(compact) > GARBLED_CONTROL_RATIO


def page_needs_ocr(raw_text: str) -> bool:
    """A page needs OCR when it has no text at all or when its text layer is unreadable."""
    return not sanitize_text(raw_text) or is_garbled(raw_text)


def ocr_png(png: bytes, tesseract: str, lang: str = OCR_LANG) -> str:
    """Run Tesseract on one PNG image passed through stdin; return the recognised text."""
    env = dict(os.environ, OMP_THREAD_LIMIT="1")  # one thread per process, parallelism is across pages
    proc = subprocess.run(
        [tesseract, "stdin", "stdout", "-l", lang],
        input=png,
        capture_output=True,
        timeout=OCR_TIMEOUT_S,
        env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", "replace").strip() or f"tesseract exit {proc.returncode}")
    return proc.stdout.decode("utf-8", "replace")


def extract_and_normalize_toc(doc: pymupdf.Document, doc_stem: str) -> tuple[list[tuple[str, str, int, int]], list[str]]:
    """Extract and validate TOC bookmarks from PDF.

    Returns:
        (toc_rows, warnings)
        toc_rows: list of (doc_stem, title, level, page_no)
    """
    try:
        raw_toc = doc.get_toc()
    except Exception as e:
        return [], [f"Error reading TOC outline: {e}"]

    if not raw_toc:
        return [], []

    toc_rows = []
    warnings = []
    page_count = doc.page_count

    for item in raw_toc:
        if not item or len(item) < 3:
            continue
        try:
            level = int(item[0]) if item[0] is not None else 1
            if level < 1:
                level = 1
        except (ValueError, TypeError):
            level = 1

        raw_title = str(item[1]) if item[1] is not None else ""
        title = sanitize_text(raw_title)
        if not title:
            title = "Untitled"

        try:
            page_no = int(item[2]) if item[2] is not None else 1
        except (ValueError, TypeError):
            warnings.append(f"Invalid page number in TOC entry '{title}': {item[2]}")
            continue

        # PyMuPDF doc.get_toc() returns 1-based page numbers
        if page_no < 1 or page_no > page_count:
            warnings.append(f"TOC entry '{title}' page {page_no} out of bounds (1..{page_count})")
            continue

        toc_rows.append((doc_stem, title, level, page_no))

    return toc_rows, warnings


def init_db(db_path: Path) -> sqlite3.Connection:
    """Initialize SQLite database with required tables, handling corruption gracefully."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        con = sqlite3.connect(str(db_path))
        con.execute("PRAGMA foreign_keys = ON")
        con.executescript(SCHEMA_SQL)
        con.commit()
        return con
    except sqlite3.DatabaseError:
        if db_path.exists():
            try:
                con.close()
            except Exception:
                pass
            db_path.unlink()
        con = sqlite3.connect(str(db_path))
        con.execute("PRAGMA foreign_keys = ON")
        con.executescript(SCHEMA_SQL)
        con.commit()
        return con


def extract_pdf_data(pdf_path: Path, ocr: bool = True, ocr_lang: str = OCR_LANG) -> dict[str, Any]:
    """Extract pages, text, and TOC for a PDF file.

    Pages without a readable text layer are OCRed with Tesseract when `ocr` is true and the
    binary is available; otherwise they are indexed as empty and a warning says why.
    """
    doc_stem = pdf_path.stem
    warnings: list[str] = []

    try:
        doc = pymupdf.open(pdf_path)
    except Exception as e:
        return {
            "doc": doc_stem,
            "status": "error",
            "error": f"Failed to open PDF: {e}",
            "warnings": [f"Failed to open PDF: {e}"],
            "page_count": 0,
            "toc_entries": 0,
            "outline_status": "error",
            "sources": {},
            "empty_pages": [],
            "pages": [],
            "toc": [],
        }

    page_count = doc.page_count
    if page_count == 0:
        doc.close()
        return {
            "doc": doc_stem,
            "status": "error",
            "error": "PDF has 0 pages",
            "warnings": ["PDF has 0 pages"],
            "page_count": 0,
            "toc_entries": 0,
            "outline_status": "empty document",
            "sources": {},
            "empty_pages": [],
            "pages": [],
            "toc": [],
        }

    toc_rows, toc_warnings = extract_and_normalize_toc(doc, doc_stem)
    warnings.extend(toc_warnings)

    pages_rows = []
    empty_pages = []
    source_counts = {"pymupdf": 0}
    source = "pymupdf"

    # Pass 1: text layer, and the list of pages that need OCR.
    texts: list[str] = []
    ocr_pages: list[int] = []  # 0-based indices
    for i in range(page_count):
        try:
            raw_text = doc[i].get_text()
            if page_needs_ocr(raw_text):
                ocr_pages.append(i)
                # Never index an unreadable text layer; blank pages stay blank.
                text = ""
            else:
                text = sanitize_text(raw_text)
        except Exception as e:
            warnings.append(f"Error extracting text from page {i + 1}: {e}")
            text = ""
        texts.append(text)

    # Pass 2: OCR. Rendering stays in this thread (PyMuPDF is not thread-safe); Tesseract
    # processes run in parallel.
    ocr_done: set[int] = set()
    tesseract = find_tesseract() if (ocr and ocr_pages) else None
    if ocr_pages and tesseract:
        workers = min(os.cpu_count() or 2, 8)
        failures = 0
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {}
            for i in ocr_pages:
                try:
                    png = doc[i].get_pixmap(dpi=OCR_DPI, colorspace=pymupdf.csGRAY).tobytes("png")
                except Exception as e:
                    warnings.append(f"Could not render page {i + 1} for OCR: {e}")
                    failures += 1
                    continue
                futures[i] = pool.submit(ocr_png, png, tesseract, ocr_lang)
            for i, fut in futures.items():
                try:
                    ocr_text = sanitize_text(fut.result())
                except Exception as e:
                    warnings.append(f"OCR failed on page {i + 1}: {e}")
                    continue
                if ocr_text:
                    texts[i] = ocr_text
                    ocr_done.add(i)
        if ocr_done:
            warnings.append(f"{len(ocr_done)} page(s) read with Tesseract OCR (text layer missing or unreadable)")
    elif ocr_pages and ocr:
        warnings.append(
            f"{len(ocr_pages)} page(s) have no readable text layer and tesseract is not installed, "
            "so they are indexed as empty (install tesseract and run build_index.py --force <pdf>)"
        )

    for i in range(page_count):
        page_no = i + 1
        page_source = "tesseract" if i in ocr_done else source
        if not texts[i]:
            empty_pages.append(page_no)
        source_counts[page_source] = source_counts.get(page_source, 0) + 1
        pages_rows.append((doc_stem, page_no, texts[i], page_source))

    doc.close()

    if empty_pages:
        warnings.append(f"{len(empty_pages)} page(s) have no extractable text (e.g. page {empty_pages[0]})")

    outline_status = (
        f"embedded outline ({len(toc_rows)} entries)"
        if toc_rows
        else "no embedded outline"
    )

    return {
        "doc": doc_stem,
        "status": "ok",
        "page_count": page_count,
        "toc_entries": len(toc_rows),
        "outline_status": outline_status,
        "sources": source_counts,
        "empty_pages": empty_pages,
        "warnings": warnings,
        "pages": pages_rows,
        "toc": toc_rows,
    }


def save_doc_to_db(con: sqlite3.Connection, doc_stem: str, pages_rows: list, toc_rows: list) -> None:
    """Idempotently reindex a document in SQLite (delete existing, bulk insert fresh)."""
    with con:
        con.execute("DELETE FROM pages WHERE doc = ?", (doc_stem,))
        con.execute("DELETE FROM toc WHERE doc = ?", (doc_stem,))
        con.execute("DELETE FROM pages_fts WHERE doc = ?", (doc_stem,))

        if pages_rows:
            con.executemany(
                "INSERT INTO pages (doc, page_no, text, source) VALUES (?, ?, ?, ?)",
                pages_rows,
            )
            con.executemany(
                "INSERT INTO pages_fts (doc, page_no, text) VALUES (?, ?, ?)",
                [(row[0], row[1], row[2]) for row in pages_rows],
            )

        if toc_rows:
            con.executemany(
                "INSERT INTO toc (doc, title, level, page_no) VALUES (?, ?, ?, ?)",
                toc_rows,
            )


def resolve_pdf_targets(names: list[str], references_dir: Path) -> list[Path]:
    """Resolve CLI target names to Path objects."""
    if not names:
        return sorted(references_dir.glob("*.pdf"))
    targets = []
    for name in names:
        p = Path(name)
        if p.is_file() and p.suffix.lower() == ".pdf":
            targets.append(p)
        elif (references_dir / p).is_file():
            targets.append(references_dir / p)
        elif (references_dir / f"{p.stem}.pdf").is_file():
            targets.append(references_dir / f"{p.stem}.pdf")
        elif (references_dir / f"{name}.pdf").is_file():
            targets.append(references_dir / f"{name}.pdf")
        else:
            raise FileNotFoundError(f"PDF not found: {name} in {references_dir}")
    return targets


def prune_missing_docs(
    con: sqlite3.Connection,
    references_dir: Path,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """Remove indexed documents whose source PDF no longer exists in references_dir.

    Compares the set of doc stems present in the `pages` table against the PDFs
    currently on disk and deletes any orphaned rows (pages, toc, pages_fts).
    """
    cur = con.cursor()
    cur.execute("SELECT DISTINCT doc FROM pages")
    indexed_docs = {row[0] for row in cur.fetchall()}

    existing_stems = {p.stem for p in references_dir.glob("*.pdf")}
    stale_docs = sorted(indexed_docs - existing_stems)

    summaries = []
    for doc_stem in stale_docs:
        if not dry_run:
            with con:
                con.execute("DELETE FROM pages WHERE doc = ?", (doc_stem,))
                con.execute("DELETE FROM toc WHERE doc = ?", (doc_stem,))
                con.execute("DELETE FROM pages_fts WHERE doc = ?", (doc_stem,))
        summaries.append({
            "doc": doc_stem,
            "status": "pruned" if not dry_run else "would_prune",
            "page_count": 0,
            "toc_entries": 0,
            "outline_status": "removed (source PDF no longer in references/)",
            "sources": {},
            "empty_pages": [],
            "warnings": [],
        })

    return summaries


def index_documents(
    pdf_paths: list[Path],
    db_path: Path,
    force: bool = False,
    dry_run: bool = False,
    references_dir: Path | None = None,
    prune: bool = True,
    ocr: bool = True,
    ocr_lang: str = OCR_LANG,
) -> list[dict[str, Any]]:
    """Build or audit index for specified PDF files."""
    summaries = []

    con: sqlite3.Connection | None = None
    if not dry_run:
        con = init_db(db_path)

    for pdf_path in pdf_paths:
        doc_stem = pdf_path.stem

        if not force and not dry_run and con is not None:
            cur = con.cursor()
            cur.execute("SELECT COUNT(*) FROM pages WHERE doc = ?", (doc_stem,))
            count = cur.fetchone()[0]
            if count > 0:
                cur.execute("SELECT COUNT(*) FROM toc WHERE doc = ?", (doc_stem,))
                toc_count = cur.fetchone()[0]
                cur.execute("SELECT source, COUNT(*) FROM pages WHERE doc = ? GROUP BY source", (doc_stem,))
                sources = dict(cur.fetchall())
                sources.setdefault("pymupdf", 0)
                summaries.append({
                    "doc": doc_stem,
                    "status": "already_indexed",
                    "page_count": count,
                    "toc_entries": toc_count,
                    "outline_status": f"embedded outline ({toc_count} entries)" if toc_count else "no embedded outline",
                    "sources": sources,
                    "empty_pages": [],
                    "warnings": [],
                })
                continue

        data = extract_pdf_data(pdf_path, ocr=ocr, ocr_lang=ocr_lang)

        if data["status"] == "ok" and not dry_run and con is not None:
            save_doc_to_db(con, doc_stem, data["pages"], data["toc"])

        summary = {
            "doc": data["doc"],
            "status": data["status"],
            "page_count": data["page_count"],
            "toc_entries": data["toc_entries"],
            "outline_status": data["outline_status"],
            "sources": data["sources"],
            "empty_pages": data["empty_pages"],
            "warnings": data["warnings"],
        }
        if "error" in data:
            summary["error"] = data["error"]
        summaries.append(summary)

    if prune and references_dir is not None:
        prune_con = con
        opened_for_prune = False
        if prune_con is None and db_path.exists():
            prune_con = sqlite3.connect(str(db_path))
            opened_for_prune = True
        if prune_con is not None:
            summaries.extend(prune_missing_docs(prune_con, references_dir, dry_run=dry_run))
            if opened_for_prune:
                prune_con.close()

    if con is not None:
        con.close()

    return summaries


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("names", nargs="*", help="specific PDF names/paths to index; default: all in references/")
    ap.add_argument("--references-dir", type=Path, default=DEFAULT_REFERENCES, help="path to references directory")
    ap.add_argument("--db-path", type=Path, default=None, help="path to SQLite database file")
    ap.add_argument("--force", action="store_true", help="reindex documents even if already in database")
    ap.add_argument("--dry-run", action="store_true", help="audit and validate without creating/modifying SQLite DB")
    ap.add_argument(
        "--no-prune",
        action="store_true",
        help="skip removing indexed documents whose source PDF no longer exists in references-dir",
    )
    ap.add_argument("--no-ocr", action="store_true", help="do not OCR pages that have no readable text layer")
    ap.add_argument("--ocr-lang", default=OCR_LANG, help="Tesseract language(s) for OCR, e.g. eng or eng+fra (default: eng)")
    args = ap.parse_args()

    db_path = args.db_path or (args.references_dir / ".ground-index" / "index.sqlite")

    try:
        targets = resolve_pdf_targets(args.names, args.references_dir)
    except FileNotFoundError as e:
        print(json.dumps([{"status": "error", "error": str(e)}], indent=2))
        sys.exit(1)

    summaries = index_documents(
        pdf_paths=targets,
        db_path=db_path,
        force=args.force,
        dry_run=args.dry_run,
        references_dir=args.references_dir,
        prune=not args.no_prune,
        ocr=not args.no_ocr,
        ocr_lang=args.ocr_lang,
    )

    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
