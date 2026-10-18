"""Unit tests for build-book skill packaging and frontmatter compliance."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[5]
SKILL_MD = REPO_ROOT / ".github" / "skills" / "build-book" / "SKILL.md"


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter and body from a markdown file."""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", text, flags=re.DOTALL)
    assert match is not None, f"No valid YAML frontmatter delimiter found in {path}"
    frontmatter_raw, body = match.groups()
    frontmatter = yaml.safe_load(frontmatter_raw)
    assert isinstance(frontmatter, dict), f"Frontmatter in {path} must parse to a dict"
    return frontmatter, body


def test_yaml_frontmatter_and_format_validation():
    """Verify that build-book/SKILL.md contains valid YAML frontmatter matching conventions."""
    assert SKILL_MD.is_file(), f"Missing skill file at {SKILL_MD}"

    frontmatter, _ = parse_frontmatter(SKILL_MD)

    # Validate name
    assert "name" in frontmatter, "Frontmatter must contain 'name'"
    assert frontmatter["name"] == "build-book", f"Unexpected name: {frontmatter['name']}"
    assert frontmatter["name"] == SKILL_MD.parent.name, "Skill name must match parent folder name"

    # Validate description
    assert "description" in frontmatter, "Frontmatter must contain 'description'"
    desc = frontmatter["description"]
    assert isinstance(desc, str) and len(desc.strip()) > 0, "Description must be a non-empty string"
    assert "Use when:" in desc, "Description must include a 'Use when:' trigger clause"

    # Check raw frontmatter line structure
    raw_text = SKILL_MD.read_text(encoding="utf-8")
    first_block = raw_text.split("---")[1]
    desc_lines = [line for line in first_block.splitlines() if line.strip().startswith("description:")]
    assert len(desc_lines) == 1, "description key should be defined exactly once in frontmatter"
    assert "Use when:" in desc_lines[0], "description line must include 'Use when:'"


def test_procedure_and_documentation_completeness():
    """Verify that all required publishing formats and workflow components are documented."""
    assert SKILL_MD.is_file()
    _, body = parse_frontmatter(SKILL_MD)

    # Triggers and Prerequisites
    assert "When to Invoke" in body or "Triggers" in body
    assert ".venv" in body
    assert "Quarto" in body or "quarto" in body
    assert "TinyTeX" in body or "xelatex" in body.lower()

    # Formats and Dimensions
    assert "Springer" in body
    assert "155mm" in body or "155" in body
    assert "O'Reilly" in body or "oreilly" in body.lower()
    assert "7in" in body or "7.0in" in body
    assert "HTML" in body or "html" in body
    assert "EPUB" in body or "epub" in body

    # Commands and Makefile
    assert "Makefile" in body or "make" in body
    assert "make book" in body or "make pdf" in body

    # Python scripts
    assert "build_book.py" in body
    assert "sync_chapters.py" in body
    assert "validate_book.py" in body

    # Troubleshooting
    assert "Troubleshooting" in body or "Recovery" in body
