"""Unit tests for build_book.py build orchestrator."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent
REPO_ROOT = TESTS_DIR.parents[4]

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import build_book


def test_build_env_contains_tinytex_and_python():
    """Verify that build environment dictionary configures PATH and QUARTO_PYTHON."""
    env = build_book.get_build_env()
    assert "PATH" in env
    if build_book.TINYTEX_DIR.is_dir():
        assert str(build_book.TINYTEX_DIR) in env["PATH"]
    if build_book.VENV_PYTHON.is_file():
        assert env.get("QUARTO_PYTHON") == str(build_book.VENV_PYTHON)


def test_dry_run_builds():
    """Verify that dry-run builds succeed across all format options."""
    for fmt in ["pdf", "html", "epub", "all"]:
        success = build_book.build_book(
            fmt=fmt,
            dry_run=True,
            sync=True,
            validate=True,
            verbose=False,
        )
        assert success is True, f"Dry-run build failed for format {fmt}"
