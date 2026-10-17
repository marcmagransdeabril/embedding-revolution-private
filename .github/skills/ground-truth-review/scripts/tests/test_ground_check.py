"""Unit tests for Phase B query and grounding tool (ground_check.py)."""
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

from build_index import SCHEMA_SQL, init_db, save_doc_to_db
from ground_check import (
    DEFAULT_DB_PATH,
    build_fts5_query,
    render_page_image,
    resolve_toc_section,
    search_index,
)

GROUND_CHECK_SCRIPT = SCRIPTS_DIR / "ground_check.py"


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
            page.insert_text((50, 50), text)
    if toc is not None:
        doc.set_toc(toc)
    doc.save(str(path))
    doc.close()
    return path


def setup_in_memory_db() -> sqlite3.Connection:
    """Set up an in-memory SQLite database populated with test schema."""
    con = sqlite3.connect(":memory:")
    con.executescript(SCHEMA_SQL)
    return con


def test_fts5_query_sanitization_edge_cases():
    """Verifies build_fts5_query handles complex symbols, LaTeX, unclosed quotes, and keywords without SQL errors."""
    con = setup_in_memory_db()
    con.execute(
        "INSERT INTO pages (doc, page_no, text, source) VALUES (?, ?, ?, ?)",
        ("doc1", 1, "We analyze O(n log n) complex gradient descent with vectors and NEAR keywords.", "pymupdf"),
    )
    con.execute(
        "INSERT INTO pages_fts (doc, page_no, text) VALUES (?, ?, ?)",
        ("doc1", 1, "We analyze O(n log n) complex gradient descent with vectors and NEAR keywords."),
    )
    con.commit()

    edge_case_queries = [
        # LaTeX / Math
        r"$O(n \log n)$ \mathbf{x} \frac{1}{2}",
        r"\sum_{i=1}^n x_i = y",
        r"f(x) = \exp(-\mu^2 / 2\sigma^2)",
        # Unclosed and unbalanced quotes
        'unclosed "quote test',
        '"',
        '"""',
        'foo "bar baz',
        # FTS5 boolean and proximity keywords
        "AND OR NOT NEAR",
        "AND AND AND",
        "doc1 NEAR/3 gradient",
        # Colons, wildcards, brackets, braces, special characters
        "key:value * ? [array] {set} (parens) a^2 + b_1 = c",
        "special chars !@#$%^&*()_+{}[]:;'<>,.?/~`",
        # Empty and whitespace only
        "",
        "   ",
        "\t\n\r",
        "$$$ *** :::",
        # Null bytes and control characters
        "test\x00query\x07with\x00nulls",
        # Unicode ligatures
        "ﬁle ﬂow ﬀect",
    ]

    for raw_q in edge_case_queries:
        fts_q = build_fts5_query(raw_q)
        # Should not raise sqlite3.OperationalError
        result = search_index(con, raw_q)
        assert isinstance(result, dict)
        assert result["query"] == raw_q
        assert "hits" in result
        assert "confidence" in result

        if fts_q:
            # Direct SQLite match test
            cur = con.cursor()
            cur.execute(
                "SELECT doc, page_no FROM pages_fts WHERE pages_fts MATCH ?",
                (fts_q,),
            )
            rows = cur.fetchall()
            assert isinstance(rows, list)

    con.close()


def test_disjunctive_and_phrase_matching():
    """Verifies quoted phrases enforce token adjacency while unquoted terms perform disjunctive (OR) scoring."""
    con = setup_in_memory_db()

    # Doc 1: Has exact phrase "circular convolution"
    save_doc_to_db(
        con,
        "doc_exact",
        pages_rows=[("doc_exact", 1, "We use circular convolution binding for associative memory.", "pymupdf")],
        toc_rows=[],
    )
    # Doc 2: Has both words "circular" and "convolution", but separated (not adjacent)
    save_doc_to_db(
        con,
        "doc_separated",
        pages_rows=[("doc_separated", 1, "The circular buffer was processed through discrete linear convolution.", "pymupdf")],
        toc_rows=[],
    )
    # Doc 3: Has only "convolution"
    save_doc_to_db(
        con,
        "doc_single",
        pages_rows=[("doc_single", 1, "Linear convolution is a fundamental mathematical operation.", "pymupdf")],
        toc_rows=[],
    )

    # 1. Exact quoted phrase search
    res_phrase = search_index(con, '"circular convolution"')
    assert res_phrase["total_hits"] == 1
    assert res_phrase["hits"][0]["doc"] == "doc_exact"

    # 2. Unquoted multi-term search (disjunctive matching)
    res_or = search_index(con, "circular convolution")
    assert res_or["total_hits"] == 3
    # doc_exact and doc_separated match both terms so rank above doc_single
    hit_docs = [h["doc"] for h in res_or["hits"]]
    assert "doc_exact" in hit_docs
    assert "doc_separated" in hit_docs
    assert "doc_single" in hit_docs
    assert hit_docs[0] in ("doc_exact", "doc_separated")

    con.close()


def test_positive_bm25_ranking_and_floor_cutoff():
    """Verifies higher term-frequency hits rank first with positive score convention, and floor cutoffs work."""
    con = setup_in_memory_db()

    save_doc_to_db(
        con,
        "doc_dense",
        pages_rows=[("doc_dense", 1, "transformer attention mechanism transformer self attention transformer architecture", "pymupdf")],
        toc_rows=[],
    )
    save_doc_to_db(
        con,
        "doc_sparse",
        pages_rows=[("doc_sparse", 1, "an overview of attention mechanism in models", "pymupdf")],
        toc_rows=[],
    )

    # Query with positive BM25 scores
    res = search_index(con, "transformer attention")
    assert res["total_hits"] == 2
    assert res["hits"][0]["doc"] == "doc_dense"
    assert res["hits"][0]["score"] > res["hits"][1]["score"]
    assert res["hits"][0]["score"] > 0
    assert res["no_match"] is None

    best_score = res["hits"][0]["score"]

    # Floor cutoff higher than best score -> no_match populated
    res_floor_high = search_index(con, "transformer attention", floor=best_score + 10.0)
    assert res_floor_high["total_hits"] == 0
    assert res_floor_high["hits"] == []
    assert res_floor_high["confidence"] == 0.0
    assert res_floor_high["no_match"] is not None
    assert res_floor_high["no_match"]["nearest_doc"] == "doc_dense"
    assert res_floor_high["no_match"]["best_score"] == best_score

    # Floor cutoff between score 1 and score 2
    second_score = res["hits"][1]["score"]
    res_floor_mid = search_index(con, "transformer attention", floor=(best_score + second_score) / 2.0)
    assert res_floor_mid["total_hits"] == 1
    assert res_floor_mid["hits"][0]["doc"] == "doc_dense"
    assert res_floor_mid["no_match"] is None

    # Query with zero FTS matches in the corpus -> no_match is None
    res_zero = search_index(con, "quantum entanglement teleportation")
    assert res_zero["total_hits"] == 0
    assert res_zero["hits"] == []
    assert res_zero["confidence"] == 0.0
    assert res_zero["no_match"] is None

    con.close()


def test_confidence_computation():
    """Validates single hit (1.0), tie (0.0), and multi-hit score gap calculations."""
    con = setup_in_memory_db()

    # Single hit case
    save_doc_to_db(
        con,
        "doc_unique",
        pages_rows=[("doc_unique", 1, "hyperdimensional computing with holographic vectors", "pymupdf")],
        toc_rows=[],
    )
    res_single = search_index(con, "hyperdimensional holographic")
    assert res_single["total_hits"] == 1
    assert res_single["confidence"] == 1.0

    # Tie case (two identical pages in different docs)
    save_doc_to_db(
        con,
        "doc_tie1",
        pages_rows=[("doc_tie1", 1, "vector symbolic architecture binding operation", "pymupdf")],
        toc_rows=[],
    )
    save_doc_to_db(
        con,
        "doc_tie2",
        pages_rows=[("doc_tie2", 1, "vector symbolic architecture binding operation", "pymupdf")],
        toc_rows=[],
    )
    res_tie = search_index(con, "vector symbolic architecture binding")
    assert res_tie["total_hits"] >= 2
    assert res_tie["hits"][0]["score"] == res_tie["hits"][1]["score"]
    assert res_tie["confidence"] == 0.0

    con.close()


def test_toc_section_resolution():
    """Tests scoped lookup per document, resolves multiple entries on same page (deepest level), and pre-TOC pages."""
    con = setup_in_memory_db()

    # Document with hierarchical TOC
    # Page 1: Chapter 1 (lvl 1) and Section 1.1 (lvl 2) -> deepest is lvl 2 "Section 1.1"
    # Page 3: (no direct entry) -> resolves to preceding "Section 1.1"
    # Page 5: Section 1.2 (lvl 2) -> resolves to "Section 1.2"
    toc_rows = [
        ("doc_with_toc", "Chapter 1: Foundations", 1, 1),
        ("doc_with_toc", "Section 1.1: Linear Algebra", 2, 1),
        ("doc_with_toc", "Section 1.2: Probability", 2, 5),
    ]
    pages_rows = [
        ("doc_with_toc", 1, "linear algebra foundation vector space", "pymupdf"),
        ("doc_with_toc", 3, "linear algebra matrix multiplication inner product", "pymupdf"),
        ("doc_with_toc", 5, "probability distribution gaussian variance", "pymupdf"),
    ]
    save_doc_to_db(con, "doc_with_toc", pages_rows=pages_rows, toc_rows=toc_rows)

    # Document without TOC
    save_doc_to_db(
        con,
        "doc_no_toc",
        pages_rows=[("doc_no_toc", 1, "arxiv paper without outline bookmarks", "pymupdf")],
        toc_rows=[],
    )

    # Check page 1 resolves to deepest TOC entry on page 1 ("Section 1.1: Linear Algebra")
    sec_p1 = resolve_toc_section(con, "doc_with_toc", 1)
    assert sec_p1 == "Section 1.1: Linear Algebra"

    # Check page 3 resolves to nearest preceding entry ("Section 1.1: Linear Algebra")
    sec_p3 = resolve_toc_section(con, "doc_with_toc", 3)
    assert sec_p3 == "Section 1.1: Linear Algebra"

    # Check page 5 resolves to "Section 1.2: Probability"
    sec_p5 = resolve_toc_section(con, "doc_with_toc", 5)
    assert sec_p5 == "Section 1.2: Probability"

    # Check page 0 (precedes all TOC entries) returns None
    sec_p0 = resolve_toc_section(con, "doc_with_toc", 0)
    assert sec_p0 is None

    # Check document without TOC returns None
    sec_notoc = resolve_toc_section(con, "doc_no_toc", 1)
    assert sec_notoc is None

    # Verify search_index populates section field properly
    res = search_index(con, "matrix multiplication")
    assert res["total_hits"] == 1
    assert res["hits"][0]["section"] == "Section 1.1: Linear Algebra"

    res_notoc = search_index(con, "arxiv paper")
    assert res_notoc["total_hits"] == 1
    assert res_notoc["hits"][0]["section"] is None

    con.close()


def test_document_filtering():
    """Verifies --doc restricts search results to the requested document stem."""
    con = setup_in_memory_db()

    save_doc_to_db(
        con,
        "doc_a",
        pages_rows=[("doc_a", 1, "neural network representations in vector space", "pymupdf")],
        toc_rows=[],
    )
    save_doc_to_db(
        con,
        "doc_b",
        pages_rows=[("doc_b", 1, "neural network representations in vector space", "pymupdf")],
        toc_rows=[],
    )

    # Search without filter
    res_all = search_index(con, "neural network representations")
    assert res_all["total_hits"] == 2
    assert {h["doc"] for h in res_all["hits"]} == {"doc_a", "doc_b"}

    # Search with doc_a filter
    res_filtered = search_index(con, "neural network representations", doc="doc_a")
    assert res_filtered["total_hits"] == 1
    assert res_filtered["hits"][0]["doc"] == "doc_a"

    # Search with doc_b filter
    res_filtered_b = search_index(con, "neural network representations", doc="doc_b")
    assert res_filtered_b["total_hits"] == 1
    assert res_filtered_b["hits"][0]["doc"] == "doc_b"

    con.close()


def test_page_rendering(tmp_path: Path):
    """Verifies standalone render_page_image helper outputs valid PNG bytes from synthetic PDF documents."""
    pdf_path = make_synthetic_pdf(
        tmp_path / "sample_doc.pdf",
        ["Page 1 contents with text", "Page 2 math formulas"],
    )

    # 1. Render page 1
    out_img1 = render_page_image("sample_doc", 1, references_dir=tmp_path)
    assert out_img1.is_file()
    # Check PNG magic bytes (\x89PNG\r\n\x1a\n)
    png_bytes = out_img1.read_bytes()
    assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")

    # 2. Render page 2 with custom output destination
    custom_dest = tmp_path / "custom" / "page2.png"
    out_img2 = render_page_image("sample_doc", 2, references_dir=tmp_path, output_path=custom_dest)
    assert out_img2 == custom_dest
    assert out_img2.is_file()
    assert out_img2.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

    # 3. Page out of bounds raises IndexError
    with pytest.raises(IndexError):
        render_page_image("sample_doc", 99, references_dir=tmp_path)

    # 4. Missing document raises FileNotFoundError
    with pytest.raises(FileNotFoundError):
        render_page_image("nonexistent_doc", 1, references_dir=tmp_path)


def test_cli_subprocess_execution(tmp_path: Path):
    """Verifies ground_check.py CLI subprocess execution and JSON outputs."""
    ref_dir = tmp_path / "references"
    db_path = ref_dir / ".ground-index" / "index.sqlite"

    pdf1 = make_synthetic_pdf(
        ref_dir / "bishop-prml.pdf",
        [
            "Chapter 1 Introduction to Pattern Recognition and Machine Learning",
            "Probability density estimation and Gaussian distributions",
        ],
        toc=[[1, "Chapter 1: Introduction", 1]],
    )

    # Initialize and populate DB
    con = init_db(db_path)
    save_doc_to_db(
        con,
        "bishop-prml",
        pages_rows=[
            ("bishop-prml", 1, "Chapter 1 Introduction to Pattern Recognition and Machine Learning", "pymupdf"),
            ("bishop-prml", 2, "Probability density estimation and Gaussian distributions", "pymupdf"),
        ],
        toc_rows=[("bishop-prml", "Chapter 1: Introduction", 1, 1)],
    )
    con.close()

    # 1. Standard search via CLI
    cmd = [
        sys.executable,
        str(GROUND_CHECK_SCRIPT),
        "Gaussian distributions",
        "--references-dir",
        str(ref_dir),
        "--db-path",
        str(db_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    out_json = json.loads(proc.stdout)
    assert out_json["total_hits"] == 1
    assert out_json["hits"][0]["doc"] == "bishop-prml"
    assert out_json["hits"][0]["page_no"] == 2
    assert out_json["hits"][0]["section"] == "Chapter 1: Introduction"
    assert "<b>Gaussian</b>" in out_json["hits"][0]["snippet"]

    # 2. Search with --doc filter
    cmd_doc = [
        sys.executable,
        str(GROUND_CHECK_SCRIPT),
        "Gaussian distributions",
        "--doc",
        "bishop-prml",
        "--references-dir",
        str(ref_dir),
        "--db-path",
        str(db_path),
    ]
    proc_doc = subprocess.run(cmd_doc, capture_output=True, text=True, check=True)
    out_doc_json = json.loads(proc_doc.stdout)
    assert out_doc_json["total_hits"] == 1

    # 3. Search with high --floor -> no_match
    cmd_floor = [
        sys.executable,
        str(GROUND_CHECK_SCRIPT),
        "Gaussian distributions",
        "--floor",
        "500.0",
        "--references-dir",
        str(ref_dir),
        "--db-path",
        str(db_path),
    ]
    proc_floor = subprocess.run(cmd_floor, capture_output=True, text=True, check=True)
    out_floor_json = json.loads(proc_floor.stdout)
    assert out_floor_json["total_hits"] == 0
    assert out_floor_json["hits"] == []
    assert out_floor_json["no_match"]["nearest_doc"] == "bishop-prml"

    # 4. Standalone render-page mode via CLI
    cmd_render = [
        sys.executable,
        str(GROUND_CHECK_SCRIPT),
        "--render-page",
        "bishop-prml",
        "1",
        "--references-dir",
        str(ref_dir),
    ]
    proc_render = subprocess.run(cmd_render, capture_output=True, text=True, check=True)
    out_render_json = json.loads(proc_render.stdout)
    assert out_render_json["status"] == "ok"
    assert Path(out_render_json["image_path"]).is_file()

    # 5. Missing database error handling
    cmd_missing_db = [
        sys.executable,
        str(GROUND_CHECK_SCRIPT),
        "any query",
        "--db-path",
        str(tmp_path / "nonexistent.sqlite"),
    ]
    proc_missing = subprocess.run(cmd_missing_db, capture_output=True, text=True)
    assert proc_missing.returncode != 0
    out_missing_json = json.loads(proc_missing.stdout)
    assert out_missing_json["status"] == "error"
