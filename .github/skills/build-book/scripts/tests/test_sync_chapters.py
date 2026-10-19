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
    """Verify that embedding_spaces.qmd pattern matches Chapter 1 in Part I."""
    emb_file = REPO_ROOT / "chapters" / "embedding_spaces.qmd"
    match = sync_chapters.match_chapter_to_outline(emb_file)
    assert match is not None
    part_idx, ch_idx = match
    assert part_idx == 0  # Part I
    assert ch_idx == 0    # Chapter 1


def test_match_future_chapter_patterns():
    """Verify pattern matching for future chapter filenames."""
    test_cases = [
        ("embedding_spaces.qmd", 0, 0),       # Part I, Ch 1
        ("vector_databases.qmd", 0, 1),       # Part I, Ch 2
        ("curse_of_dimensionality.qmd", 0, 2), # Part I, Ch 3
        ("tangent_spaces.qmd", 1, 0),         # Part II, Ch 4
        ("graph_embeddings.qmd", 1, 1),       # Part II, Ch 5
        ("topological_deep_learning.qmd", 1, 2), # Part II, Ch 6
        ("complex_plane.qmd", 2, 0),          # Part III, Ch 7
        ("vsa_hyperdimensional.qmd", 2, 1),   # Part III, Ch 8
        ("neurosymbolic_integration.qmd", 2, 2), # Part III, Ch 9
        ("optimal_transport.qmd", 3, 0),      # Part IV, Ch 10
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


def test_sync_quarto_yml_dry_run():
    """Verify that sync_quarto_yml succeeds in dry-run mode."""
    success = sync_chapters.sync_quarto_yml(dry_run=True, verbose=False)
    assert success is True
