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
    assert frontmatter.get("name") == "review-doc", "Skill name must be 'review-doc'"
    assert frontmatter["name"] == SKILL_DIR.name, "Skill name must match directory name"
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


def test_section8_delegates_to_ground_truth_review():
    """§8 must delegate to ground-truth-review and map Contradicted/Not found to blocker.

    review-doc owns this dependency; ground-truth-review must not reference review-doc.
    """
    content = SKILL_MD.read_text(encoding="utf-8")
    sec8 = re.search(
        r"### 8\. Technical explanations and factual accuracy(.*?)(?=### 9\.|\Z)",
        content,
        flags=re.DOTALL,
    )
    assert sec8 is not None, "Failed to locate §8 in review-doc/SKILL.md"
    text = sec8.group(1)
    assert "ground-truth-review" in text
    assert "Contradicted" in text and "Not found" in text
    assert "blocker" in text


def test_referenced_documents_validation_step():
    """Verify that SKILL.md contains a procedure for validating referenced documents."""
    content = SKILL_MD.read_text(encoding="utf-8")
    content_lower = content.lower()
    
    assert "referenced document" in content_lower or "referenced documents" in content_lower, (
        "SKILL.md must contain a referenced document validation step"
    )
    assert "build_index.py" in content or "references/.ground-index" in content, (
        "SKILL.md must reference the ground index or index build script for referenced documents"
    )
    assert "bibliographic" in content_lower or "metadata" in content_lower, (
        "SKILL.md must specify bibliographic/metadata validation for references"
    )
