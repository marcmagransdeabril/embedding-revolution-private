#!/usr/bin/env python3
"""Query and grounding tool for page-level BM25 index over reference PDFs.

Converts queries into FTS5 expressions, executes BM25 ranking against SQLite
FTS5 index with Porter stemming, resolves TOC sections, applies score floors,
and supports on-demand page image rendering.
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


def build_fts5_query(query: str) -> str:
    """Convert user query string into a sanitized disjunctive SQLite FTS5 query.

    Handles quoted phrases, LaTeX/math expressions, special characters,
    FTS5 boolean keywords, and Unicode normalization.
    """
    if not query:
        return ""

    # Strip null bytes and non-printable control characters
    query = query.replace("\x00", "")
    query = "".join(
        ch for ch in query
        if ch in ("\t", "\n", "\r") or unicodedata.category(ch)[0] != "C"
    )
    query = unicodedata.normalize("NFKC", query)

    # Extract quoted phrases (handling unclosed quotes safely)
    phrases: list[str] = []
    cleaned_parts: list[str] = []
    last_end = 0

    # Match paired double quotes
    for m in re.finditer(r'"([^"]*)"', query):
        phrase_content = m.group(1).strip()
        words = re.findall(r"[\w]+", phrase_content, flags=re.UNICODE)
        if len(words) > 1:
            phrases.append(" ".join(words))
        elif len(words) == 1:
            phrases.append(words[0])
        cleaned_parts.append(query[last_end : m.start()])
        last_end = m.end()

    # Append remainder of string after last matched quote
    cleaned_parts.append(query[last_end:])
    remainder = " ".join(cleaned_parts)

    # For the text outside quotes, extract individual alphanumeric word tokens
    words = re.findall(r"[\w]+", remainder, flags=re.UNICODE)

    terms: list[str] = []
    seen: set[str] = set()

    for p in phrases:
        p_clean = p.strip()
        if not p_clean:
            continue
        p_lower = p_clean.lower()
        if p_lower not in seen:
            terms.append(f'"{p_clean}"')
            seen.add(p_lower)

    for w in words:
        w_clean = w.strip()
        if not w_clean:
            continue
        w_lower = w_clean.lower()
        if w_lower not in seen:
            terms.append(f'"{w_clean}"')
            seen.add(w_lower)

    if not terms:
        return ""

    return " OR ".join(terms)


def resolve_toc_section(con: sqlite3.Connection, doc: str, page_no: int) -> str | None:
    """Look up nearest preceding TOC title for the document and page (deepest level for ties on same page)."""
    cur = con.cursor()
    cur.execute(
        "SELECT title FROM toc WHERE doc = ? AND page_no <= ? ORDER BY page_no DESC, level DESC LIMIT 1",
        (doc, page_no),
    )
    row = cur.fetchone()
    return row[0] if row else None


def search_index(
    con_or_db_path: sqlite3.Connection | Path | str,
    query: str,
    top_k: int = 5,
    doc: str | None = None,
    floor: float = 0.0,
) -> dict[str, Any]:
    """Execute BM25 search over pages_fts, resolve TOC sections, and compute confidence."""
    fts_query = build_fts5_query(query)
    if not fts_query:
        return {
            "query": query,
            "total_hits": 0,
            "confidence": 0.0,
            "hits": [],
            "no_match": None,
        }

    close_con = False
    if isinstance(con_or_db_path, (str, Path)):
        con = sqlite3.connect(str(con_or_db_path))
        close_con = True
    else:
        con = con_or_db_path

    try:
        cur = con.cursor()
        if doc is not None and doc.strip():
            sql = """
            SELECT pages_fts.doc, pages_fts.page_no, -bm25(pages_fts, 0.0, 0.0, 1.0) AS score,
                   snippet(pages_fts, 2, '<b>', '</b>', '...', 32) AS snippet, p.source
            FROM pages_fts
            JOIN pages p ON p.doc = pages_fts.doc AND p.page_no = pages_fts.page_no
            WHERE pages_fts MATCH ? AND pages_fts.doc = ?
            ORDER BY score DESC
            """
            params: tuple[Any, ...] = (fts_query, doc.strip())
        else:
            sql = """
            SELECT pages_fts.doc, pages_fts.page_no, -bm25(pages_fts, 0.0, 0.0, 1.0) AS score,
                   snippet(pages_fts, 2, '<b>', '</b>', '...', 32) AS snippet, p.source
            FROM pages_fts
            JOIN pages p ON p.doc = pages_fts.doc AND p.page_no = pages_fts.page_no
            WHERE pages_fts MATCH ?
            ORDER BY score DESC
            """
            params = (fts_query,)

        try:
            raw_rows = cur.execute(sql, params).fetchall()
        except sqlite3.OperationalError:
            return {
                "query": query,
                "total_hits": 0,
                "confidence": 0.0,
                "hits": [],
                "no_match": None,
            }

        if not raw_rows:
            return {
                "query": query,
                "total_hits": 0,
                "confidence": 0.0,
                "hits": [],
                "no_match": None,
            }

        best_score = float(raw_rows[0][2])
        nearest_doc = str(raw_rows[0][0])

        if best_score < floor:
            return {
                "query": query,
                "total_hits": 0,
                "confidence": 0.0,
                "hits": [],
                "no_match": {
                    "nearest_doc": nearest_doc,
                    "best_score": best_score,
                },
            }

        filtered_rows = [r for r in raw_rows if float(r[2]) >= floor][:top_k]

        hits: list[dict[str, Any]] = []
        for r in filtered_rows:
            hit_doc = str(r[0])
            hit_page_no = int(r[1])
            hit_score = float(r[2])
            hit_snippet = str(r[3])
            hit_source = str(r[4])
            hit_section = resolve_toc_section(con, hit_doc, hit_page_no)

            hits.append({
                "doc": hit_doc,
                "page_no": hit_page_no,
                "section": hit_section,
                "score": hit_score,
                "source": hit_source,
                "snippet": hit_snippet,
            })

        if len(hits) == 1:
            confidence = 1.0
        elif len(hits) >= 2:
            s1 = float(hits[0]["score"])
            s2 = float(hits[1]["score"])
            confidence = round((s1 - s2) / (s1 + 1e-6), 4)
        else:
            confidence = 0.0

        return {
            "query": query,
            "total_hits": len(hits),
            "confidence": confidence,
            "hits": hits,
            "no_match": None,
        }
    finally:
        if close_con:
            con.close()


def render_page_image(
    doc: str,
    page_no: int,
    references_dir: Path = DEFAULT_REFERENCES,
    output_path: Path | None = None,
    dpi: int = 150,
) -> Path:
    """Render a 1-based page of a PDF document to a PNG file."""
    # Handle doc identifiers that may contain dots or end with .pdf
    doc_clean = doc.removesuffix(".pdf") if doc.endswith(".pdf") else doc
    pdf_path = references_dir / f"{doc_clean}.pdf"
    if not pdf_path.is_file():
        if (references_dir / doc).is_file():
            pdf_path = references_dir / doc
        elif Path(doc).is_file():
            pdf_path = Path(doc)
        elif (references_dir / f"{Path(doc).stem}.pdf").is_file():
            pdf_path = references_dir / f"{Path(doc).stem}.pdf"
        else:
            raise FileNotFoundError(f"PDF document not found: {doc} in {references_dir}")
    doc_stem = pdf_path.stem

    pdf_doc = pymupdf.open(pdf_path)
    try:
        if page_no < 1 or page_no > pdf_doc.page_count:
            raise IndexError(
                f"Page number {page_no} out of bounds (1..{pdf_doc.page_count}) for {doc_stem}"
            )

        page = pdf_doc[page_no - 1]
        pixmap = page.get_pixmap(dpi=dpi)

        if output_path is None:
            renders_dir = references_dir / ".ground-index" / "renders"
            renders_dir.mkdir(parents=True, exist_ok=True)
            output_path = renders_dir / f"{doc_stem}_p{page_no}.png"
        else:
            output_path.parent.mkdir(parents=True, exist_ok=True)

        pixmap.save(str(output_path))
        return output_path
    finally:
        pdf_doc.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("query", nargs="?", default="", help="claim or question to search in indexed references")
    ap.add_argument("--top-k", type=int, default=5, help="maximum number of hits to return (default: 5)")
    ap.add_argument("--doc", type=str, default=None, help="filter search to specific document stem")
    ap.add_argument("--floor", type=float, default=0.0, help="minimum BM25 score threshold (default: 0.0)")
    ap.add_argument("--render-page", nargs=2, metavar=("DOC", "PAGE_NO"), help="render page to PNG: <doc> <page_no>")
    ap.add_argument("--output-image", type=Path, default=None, help="destination path for rendered PNG image")
    ap.add_argument("--references-dir", type=Path, default=DEFAULT_REFERENCES, help="path to references directory")
    ap.add_argument("--db-path", type=Path, default=None, help="path to SQLite database file")
    args = ap.parse_args()

    # Standalone render-page mode
    if args.render_page:
        doc_stem, raw_page_no = args.render_page
        try:
            page_no = int(raw_page_no)
            out_img = render_page_image(
                doc=doc_stem,
                page_no=page_no,
                references_dir=args.references_dir,
                output_path=args.output_image,
            )
            print(json.dumps({
                "status": "ok",
                "doc": doc_stem,
                "page_no": page_no,
                "image_path": str(out_img),
            }, indent=2))
            sys.exit(0)
        except Exception as e:
            print(json.dumps({
                "status": "error",
                "error": str(e),
            }, indent=2))
            sys.exit(1)

    # Search mode
    db_path = args.db_path or (args.references_dir / ".ground-index" / "index.sqlite")
    if not db_path.is_file():
        print(json.dumps({
            "status": "error",
            "error": f"Database file not found: {db_path}. Please run build_index.py first.",
        }, indent=2))
        sys.exit(1)

    result = search_index(
        con_or_db_path=db_path,
        query=args.query,
        top_k=args.top_k,
        doc=args.doc,
        floor=args.floor,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
