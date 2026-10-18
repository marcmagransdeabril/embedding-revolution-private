"""Unit tests for validate_book.py structure and syntax checker."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent
REPO_ROOT = TESTS_DIR.parents[4]

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import validate_book


def test_validate_current_workspace_files():
    """Verify that current repo files (index.qmd, chapters/embedding_spaces.qmd) pass validation."""
    errors, warnings = validate_book.validate_all(verbose=False)
    assert errors == 0, f"Expected 0 validation errors, got {errors}"


def test_validate_frontmatter():
    """Verify frontmatter validation rules."""
    valid_text = "---\ntitle: 'Test Title'\nsubtitle: 'Test Sub'\n---\n# Content"
    issues = validate_book.validate_frontmatter(Path("test.qmd"), valid_text)
    assert len([i for i in issues if i.severity == "ERROR"]) == 0

    no_title_text = "---\nsubtitle: 'No Title'\n---\n# Content"
    issues = validate_book.validate_frontmatter(Path("test.qmd"), no_title_text)
    assert any(i.severity == "ERROR" and "title" in i.message.lower() for i in issues)


def test_validate_callouts():
    """Verify balanced callout block validation."""
    balanced_lines = [
        "::: {.callout-note}",
        "Some note content",
        ":::",
    ]
    issues = validate_book.validate_callouts(Path("test.qmd"), balanced_lines)
    assert len(issues) == 0

    unclosed_lines = [
        "::: {.callout-note}",
        "Some unclosed note content",
    ]
    issues = validate_book.validate_callouts(Path("test.qmd"), unclosed_lines)
    assert any(i.severity == "ERROR" and "unclosed" in i.message.lower() for i in issues)


def test_validate_code_chunks():
    """Verify Python code cell AST syntax checking."""
    valid_py_chunk = "```{python}\nimport numpy as np\nx = np.zeros(10)\n```"
    issues = validate_book.validate_code_chunks(Path("test.qmd"), valid_py_chunk)
    assert len([i for i in issues if i.severity == "ERROR"]) == 0

    invalid_py_chunk = "```{python}\ndef broken_syntax(\n```"
    issues = validate_book.validate_code_chunks(Path("test.qmd"), invalid_py_chunk)
    assert any(i.severity == "ERROR" and "syntax" in i.message.lower() for i in issues)


def test_validate_math_delimiters():
    """Verify display math block balance checking."""
    balanced_math = [
        "Some text",
        "$$",
        "E = mc^2",
        "$$",
    ]
    issues = validate_book.validate_math_delimiters(Path("test.qmd"), balanced_math)
    assert len(issues) == 0

    unclosed_math = [
        "Some text",
        "$$",
        "E = mc^2",
    ]
    issues = validate_book.validate_math_delimiters(Path("test.qmd"), unclosed_math)
    assert any(i.severity == "ERROR" and "unclosed" in i.message.lower() for i in issues)
