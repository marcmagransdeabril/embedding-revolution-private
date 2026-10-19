"""End-to-end integration test suite for ground index building and query retrieval.

Validates the complete indexing and retrieval pipeline via subprocess invocations
and JSON output parsing against synthetic multi-doc PDFs with TOCs and Marker overlays.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pymupdf
import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
BUILD_INDEX_SCRIPT = SCRIPTS_DIR / "build_index.py"
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
            page.insert_textbox(page.rect, text)
    if toc is not None:
        doc.set_toc(toc)
    doc.save(str(path))
    doc.close()
    return path


def run_cli(cmd: list[str]) -> tuple[int, str, str]:
    """Execute a CLI command via subprocess and return (returncode, stdout, stderr)."""
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode, res.stdout, res.stderr


@pytest.fixture
def synthetic_corpus(tmp_path: Path) -> Path:
    """Fixture providing a synthetic multi-document corpus with hierarchical/flat/empty TOCs and Marker chunk manifests."""
    references_dir = tmp_path / "references"
    references_dir.mkdir(parents=True, exist_ok=True)

    # 1. doc_theory.pdf (Hierarchical TOC)
    # p1: intro, p2: Theorem 1 capacity bound, p3: associative cleanup memory
    theory_pages = [
        "Chapter 1: Theory\nIntroduction to vector symbolic architectures, hyperdimensional computing, and theoretical foundations.",
        "Section 1.1: Capacity Bounds\nTheorem 1 capacity bound C \\approx 0.18 d with circular convolution and O(d \\log d) complexity in high dimensions.",
        "Section 1.2: Cleanup Mechanics\nAssociative cleanup memory mechanics and auto-associative item recovery in high dimensional spaces.",
    ]
    theory_toc = [
        [1, "Chapter 1: Theory", 1],
        [2, "Section 1.1: Capacity Bounds", 2],
        [2, "Section 1.2: Cleanup Mechanics", 3],
    ]
    make_synthetic_pdf(references_dir / "doc_theory.pdf", theory_pages, toc=theory_toc)

    # 2. doc_empirical.pdf (Flat TOC)
    # p1: experimental setup, p2: GLUE benchmark evaluation
    empirical_pages = [
        "Experiments\nExperimental setup, hyperparameter configurations, and evaluation protocols for large language models.",
        "Results\nGLUE benchmark evaluation with 88.4 accuracy vs 82.1 baseline on downstream classification tasks.",
    ]
    empirical_toc = [
        [1, "Experiments", 1],
        [1, "Results", 2],
    ]
    make_synthetic_pdf(references_dir / "doc_empirical.pdf", empirical_pages, toc=empirical_toc)

    # 3. doc_history_survey.pdf (No TOC, arXiv style)
    # p1: Smolensky (1990) TPR, p2: taxonomic categorization dense distributed vs sparse localist
    history_pages = [
        "Smolensky (1990) introduced Tensor Product Representations (TPR) for distributed and symbolic structure with embedded representations.",
        "Taxonomic categorization of neurosymbolic models into dense distributed vs sparse localist representations.",
    ]
    make_synthetic_pdf(references_dir / "doc_history_survey.pdf", history_pages, toc=[])

    return references_dir


def test_e2e_claim_taxonomy_retrieval(synthetic_corpus: Path):
    """Executes build_index.py via CLI and queries ground_check.py across all 5 claim archetypes."""
    # 1. Build index via CLI subprocess
    code, stdout, stderr = run_cli([
        sys.executable,
        str(BUILD_INDEX_SCRIPT),
        "--references-dir",
        str(synthetic_corpus),
    ])
    assert code == 0, f"build_index.py failed: {stderr}"
    summaries = json.loads(stdout)
    assert len(summaries) == 3
    assert all(s["status"] == "ok" for s in summaries)

    # 2. Test semantic breadth matrix across all 5 claim archetypes
    test_cases = [
        # (archetype_name, query, expected_doc, expected_page, expected_section)
        (
            "Theoretical/Math",
            "circular convolution capacity bound",
            "doc_theory",
            2,
            "Section 1.1: Capacity Bounds",
        ),
        (
            "Empirical/Benchmark",
            "GLUE benchmark accuracy 88.4",
            "doc_empirical",
            2,
            "Results",
        ),
        (
            "Attribution/History",
            "Smolensky Tensor Product Representations",
            "doc_history_survey",
            1,
            None,
        ),
        (
            "Architectural/Algorithmic",
            "associative cleanup memory",
            "doc_theory",
            3,
            "Section 1.2: Cleanup Mechanics",
        ),
        (
            "Taxonomic/Conceptual",
            "neurosymbolic dense distributed localist",
            "doc_history_survey",
            2,
            None,
        ),
    ]

    for archetype, query, exp_doc, exp_page, exp_section in test_cases:
        code, stdout, stderr = run_cli([
            sys.executable,
            str(GROUND_CHECK_SCRIPT),
            query,
            "--references-dir",
            str(synthetic_corpus),
        ])
        assert code == 0, f"ground_check.py failed for archetype {archetype}: {stderr}"
        res = json.loads(stdout)

        assert res["total_hits"] > 0, f"Expected hits for archetype {archetype} ({query}), got 0"
        assert res["confidence"] > 0.0, f"Expected confidence > 0.0 for archetype {archetype}, got {res['confidence']}"
        top_hit = res["hits"][0]
        assert top_hit["doc"] == exp_doc, f"Archetype {archetype}: expected doc {exp_doc}, got {top_hit['doc']}"
        assert top_hit["page_no"] == exp_page, f"Archetype {archetype}: expected page {exp_page}, got {top_hit['page_no']}"
        assert top_hit["section"] == exp_section, f"Archetype {archetype}: expected section {exp_section}, got {top_hit['section']}"
        assert "<b>" in top_hit["snippet"] and "</b>" in top_hit["snippet"], (
            f"Archetype {archetype}: expected highlighted snippet with <b>...</b> tags, got {top_hit['snippet']}"
        )


def test_e2e_lexical_stemming_and_math(synthetic_corpus: Path):
    """Tests morphological stemming, phrase adjacency, LaTeX/special symbol handling, and synonym rewording via CLI."""
    # Ensure index exists
    run_cli([
        sys.executable,
        str(BUILD_INDEX_SCRIPT),
        "--references-dir",
        str(synthetic_corpus),
    ])

    # 1. Porter Stemming: 'embedded representation' matches 'embedded representations'
    code, stdout, stderr = run_cli([
        sys.executable,
        str(GROUND_CHECK_SCRIPT),
        "embedded representation",
        "--references-dir",
        str(synthetic_corpus),
    ])
    assert code == 0, stderr
    res = json.loads(stdout)
    assert res["total_hits"] > 0
    assert res["hits"][0]["doc"] == "doc_history_survey"
    assert res["hits"][0]["page_no"] == 1

    # 2. Phrase Adjacency: Quoted "circular convolution" enforces exact token order
    code, stdout, stderr = run_cli([
        sys.executable,
        str(GROUND_CHECK_SCRIPT),
        '"circular convolution"',
        "--references-dir",
        str(synthetic_corpus),
    ])
    assert code == 0, stderr
    res = json.loads(stdout)
    assert res["total_hits"] > 0
    assert res["hits"][0]["doc"] == "doc_theory"
    assert res["hits"][0]["page_no"] == 2

    # Reversed quoted phrase should not match
    code, stdout, stderr = run_cli([
        sys.executable,
        str(GROUND_CHECK_SCRIPT),
        '"convolution circular"',
        "--references-dir",
        str(synthetic_corpus),
    ])
    assert code == 0, stderr
    res = json.loads(stdout)
    assert res["total_hits"] == 0

    # 3. LaTeX & Special Symbols: formulas and FTS5 keywords execute safely without SQL error
    code, stdout, stderr = run_cli([
        sys.executable,
        str(GROUND_CHECK_SCRIPT),
        r"$O(d \log d)$ \approx NEAR",
        "--references-dir",
        str(synthetic_corpus),
    ])
    assert code == 0, stderr
    res = json.loads(stdout)
    assert res["total_hits"] > 0
    assert res["hits"][0]["doc"] == "doc_theory"
    assert res["hits"][0]["page_no"] == 2

    # 4. Synonym Rewording: ungrounded terminology retry pattern
    # Initial query with alternate/synonym term not present in corpus
    code, stdout, stderr = run_cli([
        sys.executable,
        str(GROUND_CHECK_SCRIPT),
        "elementwise multiplication binding operator",
        "--references-dir",
        str(synthetic_corpus),
    ])
    assert code == 0, stderr
    res_miss = json.loads(stdout)
    assert res_miss["total_hits"] == 0

    # Retry with reworded query on the same index succeeds
    code, stdout, stderr = run_cli([
        sys.executable,
        str(GROUND_CHECK_SCRIPT),
        "circular convolution capacity",
        "--references-dir",
        str(synthetic_corpus),
    ])
    assert code == 0, stderr
    res_hit = json.loads(stdout)
    assert res_hit["total_hits"] > 0
    assert res_hit["hits"][0]["doc"] == "doc_theory"
    assert res_hit["hits"][0]["page_no"] == 2


def test_e2e_no_match_and_floor_abstention(synthetic_corpus: Path):
    """Tests sub-floor score abstention with nearest_doc suggestion and total zero-match abstention."""
    # Ensure index exists
    run_cli([
        sys.executable,
        str(BUILD_INDEX_SCRIPT),
        "--references-dir",
        str(synthetic_corpus),
    ])

    # 1. Sub-floor near miss: query matches weakly but score is below floor threshold
    code, stdout, stderr = run_cli([
        sys.executable,
        str(GROUND_CHECK_SCRIPT),
        "Introduction",
        "--floor",
        "50.0",
        "--references-dir",
        str(synthetic_corpus),
    ])
    assert code == 0, stderr
    res = json.loads(stdout)
    assert res["total_hits"] == 0
    assert res["hits"] == []
    assert res["no_match"] is not None
    assert "nearest_doc" in res["no_match"]
    assert res["no_match"]["nearest_doc"] == "doc_theory"
    assert res["no_match"]["best_score"] > 0.0
    assert res["no_match"]["best_score"] < 50.0

    # 2. Total zero match: query has no lexical overlap in corpus
    code, stdout, stderr = run_cli([
        sys.executable,
        str(GROUND_CHECK_SCRIPT),
        "quantum superconducting qubit decoherence xyz123",
        "--references-dir",
        str(synthetic_corpus),
    ])
    assert code == 0, stderr
    res = json.loads(stdout)
    assert res["total_hits"] == 0
    assert res["hits"] == []
    assert res["no_match"] is None


def test_e2e_document_filtering(synthetic_corpus: Path):
    """Tests document filtering flag (--doc) strictly isolates results to the specified document."""
    # Ensure index exists
    run_cli([
        sys.executable,
        str(BUILD_INDEX_SCRIPT),
        "--references-dir",
        str(synthetic_corpus),
    ])

    # Query term present in multiple contexts
    code, stdout, stderr = run_cli([
        sys.executable,
        str(GROUND_CHECK_SCRIPT),
        "representations",
        "--doc",
        "doc_history_survey",
        "--references-dir",
        str(synthetic_corpus),
    ])
    assert code == 0, stderr
    res = json.loads(stdout)
    assert res["total_hits"] > 0
    assert all(h["doc"] == "doc_history_survey" for h in res["hits"])

    # Restricting to another document where the term does not appear
    code, stdout, stderr = run_cli([
        sys.executable,
        str(GROUND_CHECK_SCRIPT),
        "GLUE benchmark",
        "--doc",
        "doc_theory",
        "--references-dir",
        str(synthetic_corpus),
    ])
    assert code == 0, stderr
    res = json.loads(stdout)
    assert res["total_hits"] == 0
    assert res["hits"] == []


def test_e2e_render_page_mode(synthetic_corpus: Path, tmp_path: Path):
    """Tests on-demand page PNG rendering via CLI subprocess."""
    # Default destination render
    code, stdout, stderr = run_cli([
        sys.executable,
        str(GROUND_CHECK_SCRIPT),
        "--render-page",
        "doc_theory",
        "2",
        "--references-dir",
        str(synthetic_corpus),
    ])
    assert code == 0, stderr
    res = json.loads(stdout)
    assert res["status"] == "ok"
    assert res["doc"] == "doc_theory"
    assert res["page_no"] == 2

    img_path = Path(res["image_path"])
    assert img_path.is_file(), f"Rendered image file missing at {img_path}"
    raw_bytes = img_path.read_bytes()
    assert raw_bytes.startswith(b"\x89PNG\r\n\x1a\n"), "File does not start with PNG magic header"

    # Verify image dimensions
    pix = pymupdf.open(str(img_path))
    assert pix.page_count == 1
    assert pix[0].rect.width > 0
    assert pix[0].rect.height > 0
    pix.close()

    # Custom destination render
    custom_img = tmp_path / "custom_render_p2.png"
    code, stdout, stderr = run_cli([
        sys.executable,
        str(GROUND_CHECK_SCRIPT),
        "--render-page",
        "doc_theory",
        "2",
        "--references-dir",
        str(synthetic_corpus),
        "--output-image",
        str(custom_img),
    ])
    assert code == 0, stderr
    res_custom = json.loads(stdout)
    assert res_custom["status"] == "ok"
    assert custom_img.is_file()
    assert custom_img.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


def test_e2e_pymupdf_source_tagging(synthetic_corpus: Path):
    """Tests that build_index.py tags every indexed page with source='pymupdf'."""
    code, stdout, stderr = run_cli([
        sys.executable,
        str(BUILD_INDEX_SCRIPT),
        "--references-dir",
        str(synthetic_corpus),
    ])
    assert code == 0, stderr

    code, stdout, stderr = run_cli([
        sys.executable,
        str(GROUND_CHECK_SCRIPT),
        "associative cleanup memory",
        "--references-dir",
        str(synthetic_corpus),
    ])
    assert code == 0, stderr
    res_p3 = json.loads(stdout)
    assert res_p3["total_hits"] > 0
    hit_p3 = res_p3["hits"][0]
    assert hit_p3["doc"] == "doc_theory"
    assert hit_p3["page_no"] == 3
    assert hit_p3["source"] == "pymupdf"
