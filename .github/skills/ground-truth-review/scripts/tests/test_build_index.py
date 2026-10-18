"""Unit tests for Phase A index builder (build_index.py) using fast in-memory synthetic PDFs."""
from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

import pymupdf
import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from build_index import (
    DEFAULT_DB_PATH,
    extract_and_normalize_toc,
    extract_pdf_data,
    index_documents,
    init_db,
    load_chunk_overlays,
    parse_paginated_md,
    resolve_pdf_targets,
    sanitize_text,
    save_doc_to_db,
)

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
BUILD_INDEX_SCRIPT = SCRIPTS_DIR / "build_index.py"


def make_synthetic_pdf(
    path: Path,
    pages_text: list[str],
    toc: list[list[Any]] | None = None,
) -> Path:
    """Create a synthetic PDF file for testing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open()
    for text in pages_text:
        page = doc.new_page()
        if text:
            page.insert_textbox(page.rect, text)
    if toc is not None:
        doc.set_toc(toc)
    doc.save(str(path))
    doc.close()
    return path


def test_schema_and_fts5_initialization(tmp_path: Path):
    """Verifies table creation, triggers/indices, Porter stemming, and corruption recovery."""
    db_path = tmp_path / "test_index.sqlite"
    con = init_db(db_path)

    # Check tables
    cur = con.cursor()
    tables = {r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert "pages" in tables
    assert "toc" in tables
    assert "pages_fts" in tables

    # Check index
    indices = {r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()}
    assert "idx_toc_doc_page" in indices

    # Check Porter stemming in FTS5
    con.execute(
        "INSERT INTO pages_fts (doc, page_no, text) VALUES (?, ?, ?)",
        ("doc_stem_test", 1, "We constructed dense vector embeddings for neural networks."),
    )
    con.commit()

    # Search with stem variation 'embedded' or 'embedding'
    res = cur.execute(
        "SELECT doc, page_no FROM pages_fts WHERE pages_fts MATCH 'embedded'"
    ).fetchall()
    assert len(res) == 1
    assert res[0] == ("doc_stem_test", 1)

    con.close()

    # Verify corruption recovery
    db_path.write_bytes(b"NOT A SQLITE FILE GARBAGE DATA")
    con2 = init_db(db_path)
    cur2 = con2.cursor()
    tables2 = {r[0] for r in cur2.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert "pages" in tables2
    assert "pages_fts" in tables2
    con2.close()


def test_toc_normalization_and_edge_cases(tmp_path: Path):
    """Tests hierarchical TOCs, missing TOCs, and corrupt/out-of-range TOC page references."""
    ref_dir = tmp_path / "references"
    db_path = ref_dir / ".ground-index" / "index.sqlite"

    # 1. Hierarchical TOC
    hierarchical_toc = [
        [1, "Chapter 1: Foundations", 1],
        [2, "Section 1.1: Linear Algebra", 1],
        [3, "Subsection 1.1.1: Vector Spaces", 2],
        [1, "Chapter 2: Methods", 3],
    ]
    pdf_hier = make_synthetic_pdf(
        ref_dir / "hierarchical.pdf",
        ["Page 1 intro", "Page 2 math", "Page 3 methods"],
        toc=hierarchical_toc,
    )

    # 2. Missing TOC (e.g. arXiv paper)
    pdf_no_toc = make_synthetic_pdf(
        ref_dir / "no_toc.pdf",
        ["Page 1 abstract", "Page 2 conclusion"],
        toc=[],
    )

    summaries = index_documents(
        [pdf_hier, pdf_no_toc],
        references_dir=ref_dir,
        db_path=db_path,
        force=True,
    )

    assert len(summaries) == 2

    # Check hierarchical
    assert summaries[0]["toc_entries"] == 4
    assert "embedded outline (4 entries)" in summaries[0]["outline_status"]

    # Check missing TOC
    assert summaries[1]["toc_entries"] == 0
    assert summaries[1]["outline_status"] == "no embedded outline"

    # Verify SQLite TOC table rows
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    toc_hier_rows = cur.execute("SELECT title, level, page_no FROM toc WHERE doc = 'hierarchical' ORDER BY rowid").fetchall()
    assert toc_hier_rows == [
        ("Chapter 1: Foundations", 1, 1),
        ("Section 1.1: Linear Algebra", 2, 1),
        ("Subsection 1.1.1: Vector Spaces", 3, 2),
        ("Chapter 2: Methods", 1, 3),
    ]

    toc_no_rows = cur.execute("SELECT COUNT(*) FROM toc WHERE doc = 'no_toc'").fetchone()[0]
    assert toc_no_rows == 0
    con.close()

    # 3. Corrupt TOC (out of bounds, negative, invalid page numbers) tested on normalize function
    corrupt_toc = [
        [1, "Valid Section", 1],
        [1, "Negative Page", -2],
        [1, "Zero Page", 0],
        [1, "Out of Bounds Page", 999],
        [2, "Invalid Type Page", "not_a_number"],
    ]

    # Use a dummy mock doc with page_count=5 and custom get_toc
    class MockDoc:
        page_count = 5
        def get_toc(self):
            return corrupt_toc

    toc_rows, warnings = extract_and_normalize_toc(MockDoc(), "corrupt_stem")  # type: ignore
    assert toc_rows == [("corrupt_stem", "Valid Section", 1, 1)]
    assert len(warnings) == 4
    assert any("out of bounds" in w for w in warnings)
    assert any("Invalid page number" in w for w in warnings)


def test_text_sanitization_and_ligatures(tmp_path: Path):
    """Tests null-byte stripping, unicode ligatures (NFKC), whitespace normalization, and empty pages."""
    raw = "T\x00est ﬁle with ﬂow and ﬀ ligatures \x00\x00 and   multiple   spaces\n\n\nand newlines"
    cleaned = sanitize_text(raw)
    assert "\x00" not in cleaned
    assert "file" in cleaned
    assert "flow" in cleaned
    assert "ff" in cleaned
    assert "multiple spaces" in cleaned
    assert "\n\n\n" not in cleaned

    ref_dir = tmp_path / "references"
    db_path = ref_dir / ".ground-index" / "index.sqlite"

    pdf = make_synthetic_pdf(
        ref_dir / "sanitized.pdf",
        [
            "Page 1 contains \x00null bytes and \ufb01 ligatures.",
            "",  # Empty page
            "Page 3 contains normal text.",
        ],
    )

    summaries = index_documents([pdf], references_dir=ref_dir, db_path=db_path, force=True)
    assert len(summaries) == 1
    assert summaries[0]["empty_pages"] == [2]
    assert any("no extractable text" in w for w in summaries[0]["warnings"])

    # Verify SQLite FTS5 search works
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    res = cur.execute("SELECT page_no, text FROM pages WHERE doc = 'sanitized' ORDER BY page_no").fetchall()
    assert len(res) == 3
    assert res[1][1] == ""  # Page 2 is empty string
    assert "null bytes" in res[0][1]
    assert "\x00" not in res[0][1]

    fts_res = cur.execute("SELECT page_no FROM pages_fts WHERE pages_fts MATCH 'ligatures'").fetchall()
    assert fts_res == [(1,)]
    con.close()


def test_idempotent_reindexing(tmp_path: Path):
    """Reindexing a document cleanly replaces all rows without orphaned or duplicate FTS5 rows."""
    ref_dir = tmp_path / "references"
    db_path = ref_dir / ".ground-index" / "index.sqlite"

    pdf_path = ref_dir / "mutable_doc.pdf"
    make_synthetic_pdf(
        pdf_path,
        ["Original Page 1 alpha", "Original Page 2 beta", "Original Page 3 gamma"],
        toc=[[1, "Ch 1", 1], [1, "Ch 2", 2], [1, "Ch 3", 3]],
    )

    # First index pass
    s1 = index_documents([pdf_path], references_dir=ref_dir, db_path=db_path, force=True)
    assert s1[0]["page_count"] == 3
    assert s1[0]["toc_entries"] == 3

    con = sqlite3.connect(str(db_path))
    assert con.execute("SELECT COUNT(*) FROM pages WHERE doc = 'mutable_doc'").fetchone()[0] == 3
    assert con.execute("SELECT COUNT(*) FROM toc WHERE doc = 'mutable_doc'").fetchone()[0] == 3
    assert con.execute("SELECT COUNT(*) FROM pages_fts WHERE doc = 'mutable_doc'").fetchone()[0] == 3
    con.close()

    # Second pass without force: should report already_indexed
    s2 = index_documents([pdf_path], references_dir=ref_dir, db_path=db_path, force=False)
    assert s2[0]["status"] == "already_indexed"

    # Modify PDF: reduce to 2 pages with new content
    make_synthetic_pdf(
        pdf_path,
        ["Updated Page 1 delta", "Updated Page 2 epsilon"],
        toc=[[1, "Updated Ch 1", 1]],
    )

    # Reindex with force=True
    s3 = index_documents([pdf_path], references_dir=ref_dir, db_path=db_path, force=True)
    assert s3[0]["page_count"] == 2
    assert s3[0]["toc_entries"] == 1

    con = sqlite3.connect(str(db_path))
    assert con.execute("SELECT COUNT(*) FROM pages WHERE doc = 'mutable_doc'").fetchone()[0] == 2
    assert con.execute("SELECT COUNT(*) FROM toc WHERE doc = 'mutable_doc'").fetchone()[0] == 1
    assert con.execute("SELECT COUNT(*) FROM pages_fts WHERE doc = 'mutable_doc'").fetchone()[0] == 2

    # Old text gamma should not match
    assert con.execute("SELECT COUNT(*) FROM pages_fts WHERE pages_fts MATCH 'gamma'").fetchone()[0] == 0
    # New text delta should match
    assert con.execute("SELECT COUNT(*) FROM pages_fts WHERE pages_fts MATCH 'delta'").fetchone()[0] == 1
    con.close()


def test_manifest_chunk_overlays(tmp_path: Path):
    """Mocks manifest.json with done and pending chunks, verifying marker text overrides pymupdf text."""
    ref_dir = tmp_path / "references"
    db_path = ref_dir / ".ground-index" / "index.sqlite"

    doc_stem = "chunked_doc"
    pdf_path = make_synthetic_pdf(
        ref_dir / f"{doc_stem}.pdf",
        [
            "PyMuPDF Raw Text 1",
            "PyMuPDF Raw Text 2",
            "PyMuPDF Raw Text 3",
            "PyMuPDF Raw Text 4",
        ],
    )

    # Create chunk directory and manifest
    chunk_dir = ref_dir / ".convert-chunks" / doc_stem
    chunk_dir.mkdir(parents=True, exist_ok=True)

    chunk1_md = chunk_dir / "chunk1.md"
    chunk1_md.write_text(
        "{0}------------------------------------\nMarker High Fidelity Text Page 1\n"
        "{1}------------------------------------\nMarker High Fidelity Text Page 2\n",
        encoding="utf-8",
    )

    manifest_data = {
        "doc": doc_stem,
        "chunks": [
            {
                "chunk_id": "chunk_001",
                "page_range": [1, 2],
                "status": "done",
                "md_path": "chunk1.md",
            },
            {
                "chunk_id": "chunk_002",
                "page_range": [3, 4],
                "status": "pending",
                "md_path": "chunk2.md",
            },
        ],
    }
    (chunk_dir / "manifest.json").write_text(json.dumps(manifest_data), encoding="utf-8")

    summaries = index_documents([pdf_path], references_dir=ref_dir, db_path=db_path, force=True)
    assert len(summaries) == 1
    assert summaries[0]["sources"] == {"marker": 2, "pymupdf": 2}

    con = sqlite3.connect(str(db_path))
    rows = con.execute("SELECT page_no, text, source FROM pages WHERE doc = ? ORDER BY page_no", (doc_stem,)).fetchall()
    con.close()

    assert rows[0] == (1, "Marker High Fidelity Text Page 1", "marker")
    assert rows[1] == (2, "Marker High Fidelity Text Page 2", "marker")
    assert rows[2] == (3, "PyMuPDF Raw Text 3", "pymupdf")
    assert rows[3] == (4, "PyMuPDF Raw Text 4", "pymupdf")


def test_dry_run_flag(tmp_path: Path):
    """Verifies dry-run emits structured summary without creating or modifying the SQLite DB."""
    ref_dir = tmp_path / "references"
    db_path = ref_dir / ".ground-index" / "index.sqlite"

    pdf_path = make_synthetic_pdf(
        ref_dir / "sample.pdf",
        ["Page 1 text", "Page 2 text"],
        toc=[[1, "Intro", 1]],
    )

    # In-memory API dry-run
    summaries = index_documents([pdf_path], references_dir=ref_dir, db_path=db_path, dry_run=True)
    assert len(summaries) == 1
    assert summaries[0]["status"] == "ok"
    assert summaries[0]["page_count"] == 2
    assert summaries[0]["toc_entries"] == 1
    assert not db_path.exists()
    assert not (ref_dir / ".ground-index").exists()

    # CLI dry-run subprocess
    cmd = [
        sys.executable,
        str(BUILD_INDEX_SCRIPT),
        "--references-dir",
        str(ref_dir),
        "--dry-run",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    cli_summary = json.loads(proc.stdout)
    assert len(cli_summary) == 1
    assert cli_summary[0]["doc"] == "sample"
    assert cli_summary[0]["page_count"] == 2
    assert not db_path.exists()


def test_error_handling(tmp_path: Path):
    """Verifies graceful handling of corrupt, empty, and missing PDF inputs."""
    ref_dir = tmp_path / "references"
    db_path = ref_dir / ".ground-index" / "index.sqlite"
    ref_dir.mkdir(parents=True, exist_ok=True)

    # 1. Corrupt PDF
    corrupt_pdf = ref_dir / "corrupt.pdf"
    corrupt_pdf.write_bytes(b"%PDF-1.4\ncorrupt garbage bytes that are not a valid pdf header")

    # 2. Empty 0-byte file
    empty_pdf = ref_dir / "empty.pdf"
    empty_pdf.write_bytes(b"")

    summaries = index_documents([corrupt_pdf, empty_pdf], references_dir=ref_dir, db_path=db_path, force=True)
    assert len(summaries) == 2
    assert summaries[0]["status"] == "error"
    assert "error" in summaries[0]
    assert summaries[1]["status"] == "error"

    # 3. Target resolution error
    with pytest.raises(FileNotFoundError):
        resolve_pdf_targets(["non_existent_doc"], ref_dir)
