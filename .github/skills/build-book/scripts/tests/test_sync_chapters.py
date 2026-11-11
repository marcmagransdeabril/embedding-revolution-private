"""Unit tests for sync_chapters.py discovery and outline mapping."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent
REPO_ROOT = TESTS_DIR.parents[4]

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import sync_chapters


def test_match_existing_chapter():
    """Verify that embedding_spaces.qmd (Anatomy) matches Chapter 3 in Part I."""
    emb_file = REPO_ROOT / "chapters" / "embedding_spaces.qmd"
    match = sync_chapters.match_chapter_to_outline(emb_file)
    assert match is not None
    part_idx, ch_idx = match
    assert part_idx == 0  # Part I
    assert ch_idx == 2    # Chapter 3


def test_match_future_chapter_patterns():
    """Verify pattern matching for future chapter filenames."""
    test_cases = [
        ("properties_of_meaning.qmd", 0, 0),   # Part I, Ch 1
        ("curse_of_dimensionality.qmd", 0, 1), # Part I, Ch 2
        ("embedding_spaces.qmd", 0, 2),        # Part I, Ch 3
        ("generative_spaces.qmd", 0, 3),       # Part I, Ch 4
        ("contextual_vectors.qmd", 0, 4),      # Part I, Ch 5 (closes Part I: the geometry is learned, not designed)
        ("vector_databases.qmd", 1, 0),        # Part II, Ch 6 (opens Part II; position under review, notes/generative_chapter_plan.md D11)
        ("tangent_spaces.qmd", 1, 1),          # Part II, Ch 7
        ("graph_embeddings.qmd", 1, 2),        # Part II, Ch 8
        ("topological_deep_learning.qmd", 1, 3), # Part II, Ch 9
        ("complex_plane.qmd", 2, 0),           # Part III, Ch 10
        ("vsa_hyperdimensional.qmd", 2, 1),    # Part III, Ch 11
        ("neurosymbolic_integration.qmd", 2, 2), # Part III, Ch 12
        ("optimal_transport.qmd", 3, 0),       # Part IV, Ch 13
        ("multimodal_embeddings.qmd", 3, 1),   # Part IV, Ch 14
    ]

    for filename, expected_part, expected_ch in test_cases:
        mock_path = REPO_ROOT / "chapters" / filename
        match = sync_chapters.match_chapter_to_outline(mock_path)
        assert match is not None, f"Failed to match {filename}"
        assert match == (expected_part, expected_ch), f"Incorrect mapping for {filename}: got {match}"


def test_discover_and_build_chapters_list():
    """Verify that discover_and_build_chapters_list returns valid Quarto chapter structure."""
    chapters_struct = sync_chapters.discover_and_build_chapters_list()
    assert isinstance(chapters_struct, list)
    assert len(chapters_struct) >= 1
    assert chapters_struct[0] == "index.qmd"


def test_chapters_follow_outline_order_within_each_part():
    """Files inside each Part appear in MASTER_PARTS order (Part I: Properties,
    Dimensionality, Anatomy, ...), whichever of them currently exist."""
    chapters_struct = sync_chapters.discover_and_build_chapters_list()
    parts = [e for e in chapters_struct if isinstance(e, dict) and e["part"] != "Additional Chapters"]
    assert parts, "expected at least one populated Part"
    for entry in parts:
        indices = [
            sync_chapters.match_chapter_to_outline(REPO_ROOT / path)[1]
            for path in entry["chapters"]
        ]
        assert indices == sorted(indices), f"{entry['part']}: out of order {entry['chapters']}"
        assert len(indices) == len(set(indices)), f"{entry['part']}: two files mapped to one chapter"


def test_sync_quarto_yml_dry_run():
    """Verify that sync_quarto_yml succeeds in dry-run mode."""
    success = sync_chapters.sync_quarto_yml(dry_run=True, verbose=False)
    assert success is True


def test_solutions_file_is_listed_last_and_not_a_chapter():
    """chapters/solutions.qmd is back matter: never matched to a Part, always last."""
    chapters_struct = sync_chapters.discover_and_build_chapters_list()
    flat = []
    for entry in chapters_struct:
        flat.extend(entry["chapters"] if isinstance(entry, dict) else [entry])
    if sync_chapters.SOLUTIONS_QMD.is_file():
        assert flat[-1] == "chapters/solutions.qmd"
        assert flat.count("chapters/solutions.qmd") == 1


def test_title_comes_from_a_labelled_h1_without_its_attributes(tmp_path):
    """Step 0 of the chapter-reference plan moves titles to `# Title {#sec-ch-...}`; matching must see the bare title."""
    p = tmp_path / "x.qmd"
    p.write_text("---\nstatus: idea\n---\n\n# Vector Databases, RAG {#sec-ch-vector-databases}\n\ntext\n", encoding="utf-8")
    assert sync_chapters.extract_title_from_qmd(p) == "Vector Databases, RAG"
    q = tmp_path / "y.qmd"
    q.write_text("---\ntitle: Front Matter Title\nstatus: idea\n---\n\n## Section\n", encoding="utf-8")
    assert sync_chapters.extract_title_from_qmd(q) == "Front Matter Title"
    r = tmp_path / "z.qmd"
    r.write_text("# Plain Title\n\ntext\n", encoding="utf-8")
    assert sync_chapters.extract_title_from_qmd(r) == "Plain Title"


def test_a_chapter_matches_the_same_slot_whether_its_title_is_in_the_front_matter_or_in_an_h1(tmp_path):
    body = "text\n"
    a = tmp_path / "embedding_spaces.qmd"
    a.write_text('---\ntitle: "The Anatomy of Embedding and Latent Spaces"\n---\n\n' + body, encoding="utf-8")
    b = tmp_path / "embedding_spaces_h1.qmd"
    b.write_text("---\nstatus: definitive\n---\n\n# The Anatomy of Embedding and Latent Spaces {#sec-ch-embedding-spaces}\n\n" + body, encoding="utf-8")
    assert sync_chapters.match_chapter_to_outline(a) == sync_chapters.match_chapter_to_outline(b)


def test_generative_chapter_is_chapter_4_and_embedding_spaces_stays_chapter_3():
    """`latent_spaces` is a pattern of Chapter 3; the file name generative_spaces must not be taken for it."""
    gen = sync_chapters.match_chapter_to_outline(REPO_ROOT / "chapters" / "generative_spaces.qmd")
    emb = sync_chapters.match_chapter_to_outline(REPO_ROOT / "chapters" / "embedding_spaces.qmd")
    assert gen == (0, 3)
    assert emb == (0, 2)
    flat = [c for p in sync_chapters.discover_and_build_chapters_list()[1:] if isinstance(p, dict) for c in p["chapters"]]
    assert flat.index("chapters/generative_spaces.qmd") == flat.index("chapters/embedding_spaces.qmd") + 1
