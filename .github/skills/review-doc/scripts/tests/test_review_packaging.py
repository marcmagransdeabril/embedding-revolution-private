"""Tests for Review Skill packaging, YAML frontmatter, and invariant consistency."""
from __future__ import annotations

import re
from pathlib import Path
import pytest
import yaml

SKILL_DIR = Path(__file__).resolve().parents[2]
SKILL_MD = SKILL_DIR / "SKILL.md"


def test_yaml_frontmatter_and_format_validation():
    """Verify that SKILL.md contains valid YAML frontmatter with required fields."""
    assert SKILL_MD.exists(), f"SKILL.md missing at {SKILL_MD}"
    content = SKILL_MD.read_text(encoding="utf-8")
    
    parts = content.split("---", 2)
    assert len(parts) >= 3, "SKILL.md must start with --- YAML frontmatter ---"
    
    frontmatter = yaml.safe_load(parts[1])
    assert isinstance(frontmatter, dict), "Frontmatter must be a YAML dictionary"
    assert frontmatter.get("name") == "review", "Skill name must be 'review'"
    assert "description" in frontmatter and len(frontmatter["description"]) > 20, "Skill description must be descriptive"


def test_required_sections_present():
    """Verify that all core sections (§1 to §14, Setup, Checks, Output) exist in SKILL.md."""
    content = SKILL_MD.read_text(encoding="utf-8")
    
    required_sections = [
        "## Setup",
        "## Checks",
        "### 1. Structure",
        "### 2. Style",
        "### 3. Grammar and usage",
        "### 4. Cross-references",
        "### 5. Figures and diagrams",
        "### 6. Citations",
        "### 7. Questions and solutions",
        "### 8. Technical explanations and factual accuracy",
        "### 9. Markup",
        "### 10. Acronyms",
        "### 11. Code consistency",
        "### 12. Index",
        "### 13. Translation parity",
        "### 14. Build and test",
        "## Output",
    ]
    
    for section in required_sections:
        assert section in content, f"Missing required section in SKILL.md: {section}"


def test_cross_skill_linkage_and_severity_invariant():
    """Verify linkage to ground-truth-review and blocker classification in SKILL.md."""
    content = SKILL_MD.read_text(encoding="utf-8")
    
    assert "ground-truth-review" in content, "SKILL.md must link to ground-truth-review skill"
    assert "blocker" in content.lower(), "SKILL.md must specify blocker severity"
    assert "should-fix" in content.lower() or "should fix" in content.lower(), "SKILL.md must specify should-fix severity"
    assert "suggestion" in content.lower(), "SKILL.md must specify suggestion severity"
