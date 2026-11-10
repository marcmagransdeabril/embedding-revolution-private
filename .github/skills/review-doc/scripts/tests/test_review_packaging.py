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
    """Verify that all core sections (§1 to §16, Setup, Checks, Output) exist in SKILL.md."""
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
        "### 15. Book-level contract and hand-offs",
        "### 16. Notation",
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


def test_style_section_guards_against_empty_erudition():
    """§2 must flag unneeded or unexplained name-drops and ask the two dependency questions."""
    content = SKILL_MD.read_text(encoding="utf-8")
    sec2 = re.search(r"### 2\. Style(.*?)(?=### 3\.|\Z)", content, flags=re.DOTALL)
    assert sec2 is not None, "Failed to locate §2 in review-doc/SKILL.md"
    text = sec2.group(1)
    assert "No empty erudition" in text
    assert "does the next step of the argument depend on it" in text
    assert "explained well enough" in text


def test_scope_is_clarified_first_and_supports_incremental_and_portion():
    """Setup must start with a scope-clarification step covering git-incremental ranges and text portions."""
    content = SKILL_MD.read_text(encoding="utf-8")
    setup = re.search(r"## Setup(.*?)(?=## Checks)", content, flags=re.DOTALL)
    assert setup is not None, "Failed to locate Setup in review-doc/SKILL.md"
    text = setup.group(1)
    assert text.lstrip().startswith("### Step 0"), "Scope clarification must be the first step of Setup"
    assert "ask before proceeding" in text
    for needle in ("git diff", "git log", "<ref>..HEAD", "line range", "Portion of text"):
        assert needle in text, f"Setup must cover: {needle}"
    assert "Confirm the scope" in text, "Setup must require echoing the scope before reviewing"


def test_book_contract_section_covers_continuity_and_thematic_contract():
    """§15 must define Job A (continuity), Job B (thematic contract), incremental scoping, and report-first output."""
    content = SKILL_MD.read_text(encoding="utf-8")
    sec15 = re.search(r"### 15\. Book-level contract and hand-offs(.*?)(?=## Output)", content, flags=re.DOTALL)
    assert sec15 is not None, "Failed to locate §15 in review-doc/SKILL.md"
    text = sec15.group(1)
    assert "Job A" in text and "Job B" in text
    assert "bitter lesson" in text and "@sec-prop-" in text
    assert "Incremental scope" in text
    out = content.split("## Output", 1)[1]
    assert "Report first" in out


def test_change_policy_applies_only_non_stylistic_fixes_in_priority_order():
    """Change policy: apply syntax, grammar, idiom, correctness (in that order); never apply style."""
    content = SKILL_MD.read_text(encoding="utf-8")
    policy = re.search(r"### Change policy(.*?)(?=### Metacognitive)", content, flags=re.DOTALL)
    assert policy is not None, "Failed to locate Change policy"
    text = policy.group(1)
    assert "Order of work" in text
    order = [text.index(k) for k in ("**Syntax**", "**Grammar**", "**Non-idiomatic usage**", "**Correctness**")]
    assert order == sorted(order), "Apply-directly categories must be listed in priority order"
    assert "Never apply stylistic changes" in text


def test_colon_misuse_is_a_usage_fix_not_a_style_suggestion():
    """§3 must treat colon-as-joint as non-idiomatic usage fixed by punctuation swap only."""
    content = SKILL_MD.read_text(encoding="utf-8")
    sec3 = re.search(r"### 3\. Grammar and usage(.*?)(?=### 4\.)", content, flags=re.DOTALL)
    assert sec3 is not None, "Failed to locate §3"
    text = sec3.group(1)
    assert "Colon misuse" in text
    assert "swapping the punctuation only" in text
    assert "never apply it" not in text
