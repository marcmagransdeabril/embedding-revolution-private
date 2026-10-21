"""Unit tests for Phase C skill packaging, frontmatter compliance, and review integration."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[5]
SKILLS_DIR = REPO_ROOT / ".github" / "skills"
GT_SKILL_MD = SKILLS_DIR / "ground-truth-review" / "SKILL.md"


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
    """Verify that ground-truth-review/SKILL.md contains valid YAML frontmatter matching conventions."""
    assert GT_SKILL_MD.is_file(), f"Missing skill file at {GT_SKILL_MD}"

    frontmatter, _ = parse_frontmatter(GT_SKILL_MD)

    # Validate name
    assert "name" in frontmatter, "Frontmatter must contain 'name'"
    assert frontmatter["name"] == "ground-truth-review", f"Unexpected name: {frontmatter['name']}"
    assert frontmatter["name"] == GT_SKILL_MD.parent.name, "Skill name must match parent folder name"

    # Validate description
    assert "description" in frontmatter, "Frontmatter must contain 'description'"
    desc = frontmatter["description"]
    assert isinstance(desc, str) and len(desc.strip()) > 0, "Description must be a non-empty string"
    assert "Use when:" in desc, "Description must include a 'Use when:' trigger clause"

    # Check raw frontmatter line structure (single-line description string)
    raw_text = GT_SKILL_MD.read_text(encoding="utf-8")
    first_block = raw_text.split("---")[1]
    desc_lines = [line for line in first_block.splitlines() if line.strip().startswith("description:")]
    assert len(desc_lines) == 1, "description key should be defined exactly once in frontmatter"
    assert "Use when:" in desc_lines[0], "description line must include 'Use when:'"


def test_procedure_and_execution_completeness():
    """Verify that all required workflow steps and environment requirements are fully documented."""
    assert GT_SKILL_MD.is_file()
    _, body = parse_frontmatter(GT_SKILL_MD)

    # When to Invoke (Triggers) and Environment
    assert "When to Invoke" in body or "Triggers" in body
    assert ".venv" in body
    assert "python" in body.lower()

    # Step 1: Index Check / Build
    assert "Step 1" in body or "1." in body
    assert "index.sqlite" in body
    assert "build_index.py" in body

    # Step 2: Live Claim Extraction & Query Formulation
    assert "Step 2" in body or "2." in body
    assert "Query Formulation" in body or "query formulation" in body.lower()

    # Step 3: Candidate Retrieval
    assert "Step 3" in body or "3." in body
    assert "ground_check.py" in body
    assert "search_index" in body
    assert "no_match" in body or "retry" in body.lower()
    assert "synonym" in body.lower() or "reword" in body.lower()

    # Step 4: Page Evidence Verification
    assert "Step 4" in body or "4." in body
    assert "--render-page" in body

    # Step 5: Emit Findings & Severity Mapping
    assert "Step 5" in body or "5." in body
    assert "Supported" in body
    assert "Contradicted" in body
    assert "Not found" in body
    assert "blocker" in body

    # Step 6: Multi-step Arguments
    assert "Step 6" in body or "6." in body
    assert "Multi-step" in body or "multi-step" in body.lower()


def test_verdict_severity_recommendation():
    """Verify the skill recommends blocker severity for Contradicted and Not found verdicts.

    This skill is standalone: it must not reference any caller skill. Callers
    (e.g. review-doc) own the dependency and test their own linkage.
    """
    _, gt_body = parse_frontmatter(GT_SKILL_MD)
    assert "blocker" in gt_body, "ground-truth-review/SKILL.md must recommend blocker for Contradicted/Not found"


def test_no_back_reference_to_callers():
    """Dependency is one-way: ground-truth-review must not reference review-doc."""
    raw = GT_SKILL_MD.read_text(encoding="utf-8")
    assert "review-doc" not in raw, "ground-truth-review must not reference review-doc (would create a cycle)"


def test_claim_taxonomy_coverage():
    """Verify that the query formulation guide explicitly covers all 5 claim archetypes."""
    _, body = parse_frontmatter(GT_SKILL_MD)

    archetypes = [
        ("Theoretical / Mathematical", ["theorem", "bound", "circular convolution", "tensor product representation"]),
        ("Empirical / Experimental / Benchmark", ["metric", "GLUE", "ImageNet", "benchmark"]),
        ("Attribution / Historical / Priority", ["surname", "Smolensky", "Plate", "discovery"]),
        ("Architectural / Algorithmic / Implementation", ["cleanup memory", "Fourier transform", "operation"]),
        ("Taxonomic / Conceptual / Survey", ["neurosymbolic", "taxonomy", "vector symbolic"]),
    ]

    for archetype_title, expected_keywords in archetypes:
        # Check archetype heading / name
        assert archetype_title.split("/")[0].strip() in body or archetype_title in body, (
            f"Missing archetype '{archetype_title}' in ground-truth-review/SKILL.md"
        )
        # Check that at least some representative keywords or examples appear
        found_keywords = [kw for kw in expected_keywords if kw.lower() in body.lower()]
        assert len(found_keywords) >= 1, (
            f"Archetype '{archetype_title}' lacks expected keywords/examples: {expected_keywords}"
        )
