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
        "### 17. Inquiry integrity",
        "### 18. Durability",
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
    sec15 = re.search(r"### 15\. Book-level contract and hand-offs(.*?)(?=### 16\.)", content, flags=re.DOTALL)
    assert sec15 is not None, "Failed to locate §15 in review-doc/SKILL.md"
    text = sec15.group(1)
    assert "Job A" in text and "Job B" in text
    assert "@sec-prop-" in text
    assert "Incremental scope" in text
    # Job B no longer asks the chapter to state a bet against the bitter lesson: the phrase is named only in the Prologue and the Epilogue.
    job_b = text.split("**Job B", 1)[1].split("**Incremental scope", 1)[0]
    assert "states the bet" not in job_b
    assert "only in the Prologue and the Epilogue" in job_b
    assert "Part I" in job_b and "Part II" in job_b, "Job B's range is stated in terms of parts, not by number alone"
    # Mechanical hints: the allow-list grep and the banned closing titles.
    hints = text.split("**Mechanical hints", 1)[1]
    assert "Sutton" in hints and "Conclusion" in hints and "Summary" in hints and "Scale Test" in hints
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


def test_inquiry_integrity_is_outcome_neutral_and_evidence_ranked():
    """§17 must keep the book exploratory: evidence outranks plan, no preferred conclusion, status-driven depth."""
    content = SKILL_MD.read_text(encoding="utf-8")
    sec = re.search(r"### 17\. Inquiry integrity(.*?)(?=### 18\.)", content, flags=re.DOTALL)
    assert sec is not None, "Failed to locate §17"
    text = sec.group(1)
    for needle in ("Outcome-neutral", "evidence, then written chapters, then plan text", "Roll-up", "Roll-down",
                   "Evidence arrival", "Balance", "Calibration", "Falsifiability", "Direction of travel",
                   "Depth follows status", "notes/ideas.qmd", "decision due", "do not choose",
                   "Open sets", "never report a missing member as incompleteness", "sorted by Lindy alignment"):
        assert needle in text, f"§17 must cover: {needle}"
    assert "ledger" not in text.lower(), "§17 must not depend on a separate ledger file"


def test_durability_section_is_rolling_and_tied_to_metrics():
    """§18 must give continuous feedback: deltas against a snapshot, tracked actions, never a blocker."""
    content = SKILL_MD.read_text(encoding="utf-8")
    sec = re.search(r"### 18\. Durability(.*?)(?=## Output)", content, flags=re.DOTALL)
    assert sec is not None, "Failed to locate §18"
    text = sec.group(1)
    for needle in ("Rolling feedback", "notes/durability.json", "notes/ideas.qmd", "never `blocker`", "One home"):
        assert needle in text, f"§18 must cover: {needle}"


def test_output_closes_with_direction_report_and_durability_block():
    content = SKILL_MD.read_text(encoding="utf-8")
    out = content.split("## Output", 1)[1]
    assert "Direction report" in out and "Durability block" in out


def test_contract_fixes_form_not_conclusions():
    """The roadmap is a plan; the contract text must not make a preset conclusion the standard."""
    content = SKILL_MD.read_text(encoding="utf-8")
    assert "fixes form, not conclusions" in content
    assert "valid close" in content


def test_section_flow_names_three_strands_and_requires_none():
    """§2: opening promises, ending answers, strands (meaning, computation, limits) are never mandatory, judged by content."""
    content = SKILL_MD.read_text(encoding="utf-8")
    sec2 = re.search(r"### 2\. Style(.*?)(?=### 3\.)", content, flags=re.DOTALL).group(1)
    for needle in ("meaning", "computation", "limits"):
        assert needle in sec2
    assert "No strand is required" in sec2
    assert "never filled" in sec2
    assert "content, not wording" in sec2


def test_payoff_step_is_a_review_step_that_adds_no_text_and_only_proposes_removals():
    """§19: scale and durability inferred by the reviewer (pointer to §18), a third question on whether a remedy solves the limit,
    no text added to the book, and a removal only proposed, never applied without the author."""
    content = SKILL_MD.read_text(encoding="utf-8")
    sec19 = re.search(r"### 19\. Pay-off step(.*?)(?=## Output)", content, flags=re.DOTALL)
    assert sec19 is not None, "Failed to locate §19 in review-doc/SKILL.md"
    text = sec19.group(1)
    assert "review step" in content.split("### 19.", 1)[1].split("\n", 1)[0]
    assert "No section, sentence or label is added to the book" in text
    assert "§18" in text and "§17" in text
    assert "Scale" in text and "Durability" in text
    assert "Does it solve the limit?" in text
    assert "Part II" in text and "not Part I" in text
    assert "fully, partly or not at all" in text
    assert "valid findings" in text
    assert "Nothing is removed until the author and the reviewer agree" in text
    assert "notes/ideas.qmd" in content.split("### Change policy", 1)[1].split("### Metacognitive", 1)[0]
    policy = re.search(r"### Change policy(.*?)(?=### Metacognitive)", content, flags=re.DOTALL).group(1)
    assert "Never apply a removal proposed by the pay-off step" in policy


def test_payoff_result_question_separates_smoke_tests_from_evidence_at_scale():
    """§19.4: rankings rest on comparisons at scale found in the literature; the book's own experiments are smoke tests;
    the question audits sentences, is not pass/fail, and reports gaps as epistemic boundaries."""
    content = SKILL_MD.read_text(encoding="utf-8")
    sec19 = re.search(r"### 19\. Pay-off step(.*?)(?=## Output)", content, flags=re.DOTALL).group(1)
    assert "4. **Result.**" in sec19
    for needle in ("systematic review or meta-analysis", "controlled comparison", "allegiance bias",
                   "smoke tests", "cannot rank methods at scale", "Question 4 is not a pass or fail",
                   "epistemic boundary"):
        assert needle in sec19, f"§19.4 must cover: {needle}"
    out = content.split("## Output", 1)[1]
    assert "§19.4" in out
