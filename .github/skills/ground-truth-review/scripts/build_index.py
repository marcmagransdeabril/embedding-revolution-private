#!/usr/bin/env python3
"""Build and maintain a page-level SQLite BM25 index over reference PDFs.

Extracts per-page text and embedded PDF bookmarks (TOC) into an indexed SQLite
store (FTS5 + Porter stemming). Supports incremental overlays from Marker chunk
manifests (.convert-chunks/<name>/manifest.json).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import unicodedata
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


def parse_paginated_md(md_text: str) -> dict[int, str]:
    """Parse marker's {N}------+ page markers into a dict of {1_based_page_no: text}."""
    parts = re.split(r'(?:^|\n)\s*\{(\d+)\}-+', md_text)
    if len(parts) <= 1:
        return {}
    pages = {}
    for i in range(1, len(parts), 2):
        page_idx = int(parts[i])  # 0-based page index from marker
        page_text = parts[i + 1] if i + 1 < len(parts) else ""
        pages[page_idx + 1] = sanitize_text(page_text)
    return pages


def parse_page_range(raw_range: Any) -> tuple[int, int] | None:
    if isinstance(raw_range, (list, tuple)) and len(raw_range) == 2:
        try:
            return int(raw_range[0]), int(raw_range[1])
        except (ValueError, TypeError):
            return None
    elif isinstance(raw_range, str):
        m = re.match(r"^(\d+)\s*[-:]\s*(\d+)$", raw_range.strip())
        if m:
            return int(m.group(1)), int(m.group(2))
        try:
            p = int(raw_range.strip())
            return p, p
        except ValueError:
            return None
    return None


def load_chunk_overlays(doc_stem: str, references_dir: Path) -> dict[int, str]:
    """Check for references/.convert-chunks/<name>/manifest.json and load done chunks.

    Returns:
        dict mapping 1-based page_no -> marker_text for done chunks.
    """
    manifest_path = references_dir / ".convert-chunks" / doc_stem / "manifest.json"
    if not manifest_path.is_file():
        # Check if full-document markdown exists as references/<doc_stem>.md
        md_file = references_dir / f"{doc_stem}.md"
        if md_file.is_file():
            try:
                md_text = md_file.read_text(encoding="utf-8")
                return parse_paginated_md(md_text)
            except Exception:
                return {}
        return {}

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    chunks = []
    if isinstance(data, list):
        chunks = data
    elif isinstance(data, dict):
        if "chunks" in data and isinstance(data["chunks"], list):
            chunks = data["chunks"]
        elif "chunks" in data and isinstance(data["chunks"], dict):
            chunks = list(data["chunks"].values())
        else:
            chunks = [v for v in data.values() if isinstance(v, dict) and "status" in v]

    overlays: dict[int, str] = {}
    manifest_dir = manifest_path.parent

    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue
        if chunk.get("status") != "done":
            continue

        page_range = parse_page_range(chunk.get("page_range"))
        md_rel = chunk.get("md_path")
        if not md_rel:
            continue

        md_path = Path(md_rel)
        if not md_path.is_absolute():
            candidate = manifest_dir / md_path
            if candidate.is_file():
                md_path = candidate
            else:
                candidate2 = references_dir / md_path
                if candidate2.is_file():
                    md_path = candidate2

        if not md_path.is_file():
            continue

        try:
            chunk_md = md_path.read_text(encoding="utf-8")
        except Exception:
            continue

        parsed_pages = parse_paginated_md(chunk_md)
        if parsed_pages:
            if page_range:
                start_p, end_p = page_range
                min_p, max_p = min(parsed_pages.keys()), max(parsed_pages.keys())
                # If marker paginated 1..N chunk-relatively:
                if min_p == 1 and start_p > 1 and max_p <= (end_p - start_p + 1):
                    for rel_p, p_text in parsed_pages.items():
                        abs_p = start_p + rel_p - 1
                        if abs_p <= end_p:
                            overlays[abs_p] = sanitize_text(p_text)
                else:
                    for p_num, p_text in parsed_pages.items():
                        if start_p <= p_num <= end_p:
                            overlays[p_num] = sanitize_text(p_text)
            else:
                for p_num, p_text in parsed_pages.items():
                    overlays[p_num] = sanitize_text(p_text)
        elif page_range:
            start_p, end_p = page_range
            if start_p == end_p:
                overlays[start_p] = sanitize_text(chunk_md)

    return overlays


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


def extract_pdf_data(pdf_path: Path, references_dir: Path) -> dict[str, Any]:
    """Extract pages, text, TOC, and manifest overlays for a PDF file."""
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

    chunk_overlays = load_chunk_overlays(doc_stem, references_dir)

    pages_rows = []
    empty_pages = []
    source_counts = {"pymupdf": 0, "marker": 0}

    for i in range(page_count):
        page_no = i + 1
        if page_no in chunk_overlays and chunk_overlays[page_no]:
            text = chunk_overlays[page_no]
            source = "marker"
        else:
            try:
                page = doc[i]
                raw_text = page.get_text()
                text = sanitize_text(raw_text)
            except Exception as e:
                warnings.append(f"Error extracting text from page {page_no}: {e}")
                text = ""
            source = "pymupdf"

        if not text:
            empty_pages.append(page_no)

        source_counts[source] = source_counts.get(source, 0) + 1
        pages_rows.append((doc_stem, page_no, text, source))

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


def index_documents(
    pdf_paths: list[Path],
    references_dir: Path,
    db_path: Path,
    force: bool = False,
    dry_run: bool = False,
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
                for s in ("pymupdf", "marker"):
                    sources.setdefault(s, 0)
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

        data = extract_pdf_data(pdf_path, references_dir)

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
    args = ap.parse_args()

    db_path = args.db_path or (args.references_dir / ".ground-index" / "index.sqlite")

    try:
        targets = resolve_pdf_targets(args.names, args.references_dir)
    except FileNotFoundError as e:
        print(json.dumps([{"status": "error", "error": str(e)}], indent=2))
        sys.exit(1)

    summaries = index_documents(
        pdf_paths=targets,
        references_dir=args.references_dir,
        db_path=db_path,
        force=args.force,
        dry_run=args.dry_run,
    )

    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
