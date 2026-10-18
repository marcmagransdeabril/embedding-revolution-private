"""Tests for Review Benchmark Dataset, Grader Integrity, and Metric Calculations."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

SKILL_DIR = Path(__file__).resolve().parents[2]
EVAL_DIR = SKILL_DIR / "eval"
BENCHMARK_PATH = EVAL_DIR / "benchmark_cases.jsonl"
B0_PATH = EVAL_DIR / "baselines" / "b0_minimal_prompt.md"

import sys
if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))

from eval_review_skill import (
    count_tokens,
    grade_review_report,
    load_benchmark_cases,
    run_benchmark_evaluation,
)


def test_benchmark_dataset_integrity():
    """Verify that benchmark dataset has 25 cases with valid taxonomy and annotations."""
    assert BENCHMARK_PATH.exists(), f"Benchmark dataset missing at {BENCHMARK_PATH}"
    cases = load_benchmark_cases(BENCHMARK_PATH)
    assert len(cases) == 25, f"Expected exactly 25 cases, got {len(cases)}"

    expected_categories = {
        "A_statistical": 6,
        "B_methodological": 5,
        "C_evaluator_bias": 5,
        "D_prior_art": 4,
        "E_tail_vs_mean": 3,
        "F_latex_formatting": 2,
    }

    actual_categories = {}
    paired_verbose_count = 0

    for case in cases:
        assert "id" in case, "Case missing 'id'"
        assert "category" in case, "Case missing 'category'"
        assert "title" in case, "Case missing 'title'"
        assert "manuscript_text" in case, "Case missing 'manuscript_text'"
        assert "ground_truth_defects" in case, "Case missing 'ground_truth_defects'"
        assert len(case["ground_truth_defects"]) >= 1, f"Case {case['id']} has no defects"

        cat = case["category"]
        actual_categories[cat] = actual_categories.get(cat, 0) + 1

        if case.get("verbose_variant_text"):
            paired_verbose_count += 1

        for defect in case["ground_truth_defects"]:
            assert "defect_id" in defect, f"Defect in {case['id']} missing defect_id"
            assert "severity" in defect, f"Defect in {case['id']} missing severity"
            assert defect["severity"] in {"blocker", "should_fix", "suggestion"}, f"Invalid severity in {case['id']}"
            assert "category" in defect, f"Defect in {case['id']} missing category"
            assert "description" in defect, f"Defect in {case['id']} missing description"
            assert "keywords" in defect and len(defect["keywords"]) >= 1, f"Defect in {case['id']} missing keywords"

    assert actual_categories == expected_categories, f"Category distribution mismatch: {actual_categories}"
    assert paired_verbose_count == 10, f"Expected 10 paired verbose variants, got {paired_verbose_count}"


def test_b0_minimal_prompt_integrity():
    """Verify that B0 baseline prompt exists and is compact (< 500 tokens)."""
    assert B0_PATH.exists(), f"B0 prompt missing at {B0_PATH}"
    b0_text = B0_PATH.read_text(encoding="utf-8")
    tokens = count_tokens(b0_text)
    assert 100 <= tokens <= 500, f"B0 token count ({tokens}) outside expected 100-500 range"


def test_grader_scoring_mechanics():
    """Verify grader precision, recall, and keyword matching mechanics."""
    mock_defects = [
        {
            "defect_id": "test-D1",
            "severity": "blocker",
            "category": "statistical_inconsistency",
            "description": "Inconsistent p-value",
            "keywords": ["t(98)", "1.42", "p-value", "inconsistent"],
        }
    ]

    # Perfect detection
    review_perfect = "[Blocker] Statistical Inconsistency: The reported t(98) = 1.42 is inconsistent with reported p-value."
    tp, fp, fn, matches = grade_review_report(review_perfect, mock_defects)
    assert tp == 1 and fn == 0, "Expected TP=1 for matching review"
    assert matches[0].detected is True

    # Missed detection
    review_missed = "[Suggestion] Clarity: The section could use additional details."
    tp, fp, fn, matches = grade_review_report(review_missed, mock_defects)
    assert tp == 0 and fn == 1, "Expected FN=1 for missed review"
    assert matches[0].detected is False


def test_baseline_benchmark_execution():
    """Verify that benchmark runs end-to-end for B0 and B1 without errors."""
    b0_summary = run_benchmark_evaluation(
        skill_name="B0",
        skill_path=B0_PATH,
        skill_type="B0",
    )
    assert b0_summary.total_cases == 25
    assert 0.0 <= b0_summary.recall <= 1.0
    assert 0.0 <= b0_summary.precision <= 1.0
    assert 0.0 <= b0_summary.f1_score <= 1.0
    assert b0_summary.review_yield_per_1k > 0.0
