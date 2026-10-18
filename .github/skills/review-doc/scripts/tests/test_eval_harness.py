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
    """Verify that benchmark dataset has 31 cases (27 defect cases across categories A-F + 4 negative controls)."""
    assert BENCHMARK_PATH.exists(), f"Benchmark dataset missing at {BENCHMARK_PATH}"
    cases = load_benchmark_cases(BENCHMARK_PATH)
    assert len(cases) == 31, f"Expected exactly 31 cases, got {len(cases)}"

    expected_categories = {
        "A_statistical": 6,
        "B_methodological": 5,
        "C_evaluator_bias": 5,
        "D_prior_art": 4,
        "E_tail_vs_mean": 5,
        "F_latex_formatting": 2,
        "Z_negative_control": 4,
    }

    actual_categories = {}
    paired_verbose_count = 0

    for case in cases:
        assert "id" in case, "Case missing 'id'"
        assert "category" in case, "Case missing 'category'"
        assert "title" in case, "Case missing 'title'"
        assert "manuscript_text" in case, "Case missing 'manuscript_text'"
        assert "ground_truth_defects" in case, "Case missing 'ground_truth_defects'"

        cat = case["category"]
        actual_categories[cat] = actual_categories.get(cat, 0) + 1

        if case.get("verbose_variant_text"):
            paired_verbose_count += 1

        if cat != "Z_negative_control":
            assert len(case["ground_truth_defects"]) >= 1, f"Defect case {case['id']} has no defects"
            for defect in case["ground_truth_defects"]:
                assert "defect_id" in defect, f"Defect in {case['id']} missing defect_id"
                assert "severity" in defect, f"Defect in {case['id']} missing severity"
                assert defect["severity"] in {"blocker", "should_fix", "suggestion"}, f"Invalid severity in {case['id']}"
                assert "category" in defect, f"Defect in {case['id']} missing category"
                assert "description" in defect, f"Defect in {case['id']} missing description"
                assert "keywords" in defect and len(defect["keywords"]) >= 1, f"Defect in {case['id']} missing keywords"
        else:
            assert len(case["ground_truth_defects"]) == 0, f"Negative control {case['id']} must have 0 ground truth defects"

    assert actual_categories == expected_categories, f"Category distribution mismatch: {actual_categories}"
    assert paired_verbose_count == 31, f"Expected 31 paired verbose variants, got {paired_verbose_count}"


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
    assert b0_summary.total_cases == 31
    assert 0.0 <= b0_summary.recall <= 1.0
    assert 0.0 <= b0_summary.precision <= 1.0
    assert 0.0 <= b0_summary.f1_score <= 1.0
    assert b0_summary.review_yield_per_1k > 0.0


def test_step1_and_step2_baseline_prompts_integrity():
    """Verify that Step 1, Step 2, and Step 3 baseline prompt variants exist and are well-formed."""
    arm1a = EVAL_DIR / "baselines" / "step1_arm1a_verbose.md"
    arm1b = EVAL_DIR / "baselines" / "step1_arm1b_compact.md"
    arm2a = EVAL_DIR / "baselines" / "step2_arm2a_verbose.md"
    arm2b = EVAL_DIR / "baselines" / "step2_arm2b_compact.md"
    arm3a = EVAL_DIR / "baselines" / "step3_arm3a_verbose.md"
    arm3b = EVAL_DIR / "baselines" / "step3_arm3b_compact.md"

    for p in [arm1a, arm1b, arm2a, arm2b, arm3a, arm3b]:
        assert p.exists(), f"Baseline variant missing at {p}"
        text = p.read_text(encoding="utf-8")
        assert "---" in text, f"Missing YAML frontmatter in {p}"
        tokens = count_tokens(text)
        assert 1500 <= tokens <= 3000, f"Token count ({tokens}) outside reasonable bounds for {p}"

    assert count_tokens(arm2b.read_text(encoding="utf-8")) < count_tokens(arm2a.read_text(encoding="utf-8")), (
        "Arm 2B compact variant must have smaller token footprint than Arm 2A verbose"
    )
    assert count_tokens(arm3b.read_text(encoding="utf-8")) < count_tokens(arm3a.read_text(encoding="utf-8")), (
        "Arm 3B compact variant must have smaller token footprint than Arm 3A verbose"
    )


def test_step2_evaluator_bias_gates():
    """Verify Step 2 Evaluator Bias decision gates (100% critical recall, >=90% precision, yield advantage)."""
    arm2a = EVAL_DIR / "baselines" / "step2_arm2a_verbose.md"
    arm2b = EVAL_DIR / "baselines" / "step2_arm2b_compact.md"

    summary_2a = run_benchmark_evaluation(
        skill_name="Arm 2A",
        skill_path=arm2a,
        skill_type="custom",
    )
    summary_2b = run_benchmark_evaluation(
        skill_name="Arm 2B",
        skill_path=arm2b,
        skill_type="custom",
    )

    cat_c_2b = summary_2b.category_breakdown["C_evaluator_bias"]
    crit_recall_2b = cat_c_2b["crit_tp"] / cat_c_2b["crit_total"]
    precision_c_2b = cat_c_2b["tp"] / (cat_c_2b["tp"] + cat_c_2b["fp"])

    # 1. 100% detection on critical evaluator bias
    assert crit_recall_2b == 1.0, f"Expected 100% critical evaluator bias recall, got {crit_recall_2b}"

    # 2. Precision >= 90%
    assert precision_c_2b >= 0.90, f"Expected >= 90% precision in Cat C, got {precision_c_2b}"

    # 3. Equal overall recall to Arm 2A
    assert summary_2b.recall == summary_2a.recall, "Arm 2B should match Arm 2A recall"

    # 4. Yield advantage (Arm 2B > Arm 2A)
    assert summary_2b.review_yield_per_1k > summary_2a.review_yield_per_1k, (
        f"Arm 2B yield ({summary_2b.review_yield_per_1k}) must exceed Arm 2A ({summary_2a.review_yield_per_1k})"
    )


def test_step3_tail_metric_gates():
    """Verify Step 3 Extreme-Value & Tail vs Mean Metric decision gates and non-target regression invariance."""
    from eval_review_skill import ARM2B_PATH, compute_regression_analysis

    arm2b = ARM2B_PATH
    arm3a = EVAL_DIR / "baselines" / "step3_arm3a_verbose.md"
    arm3b = EVAL_DIR / "baselines" / "step3_arm3b_compact.md"

    summary_2b = run_benchmark_evaluation(
        skill_name="Arm 2B (Baseline)",
        skill_path=arm2b,
        skill_type="custom",
    )
    summary_3a = run_benchmark_evaluation(
        skill_name="Arm 3A",
        skill_path=arm3a,
        skill_type="custom",
    )
    summary_3b = run_benchmark_evaluation(
        skill_name="Arm 3B",
        skill_path=arm3b,
        skill_type="custom",
    )

    cat_e_3b = summary_3b.category_breakdown["E_tail_vs_mean"]
    crit_recall_3b = cat_e_3b["crit_tp"] / cat_e_3b["crit_total"]
    total_recall_3b = cat_e_3b["tp"] / cat_e_3b["total"]
    precision_e_3b = cat_e_3b["tp"] / (cat_e_3b["tp"] + cat_e_3b["fp"])

    # 1. 100% detection on Category E (5/5 cases)
    assert total_recall_3b == 1.0, f"Expected 100% Category E recall, got {total_recall_3b}"
    assert crit_recall_3b == 1.0, f"Expected 100% critical Category E recall, got {crit_recall_3b}"

    # 2. Precision >= 90%
    assert precision_e_3b >= 0.90, f"Expected >= 90% precision in Cat E, got {precision_e_3b}"

    # 3. Equal overall recall to Arm 3A
    assert summary_3b.recall == summary_3a.recall, "Arm 3B should match Arm 3A recall"

    # 4. Yield advantage (Arm 3B > Arm 3A)
    assert summary_3b.review_yield_per_1k > summary_3a.review_yield_per_1k, (
        f"Arm 3B yield ({summary_3b.review_yield_per_1k}) must exceed Arm 3A ({summary_3a.review_yield_per_1k})"
    )

    # 5. Non-target regression invariance & negative control integrity
    regr_3b = compute_regression_analysis(summary_2b, summary_3b, target_category="E_tail_vs_mean")
    assert regr_3b.zero_regression_passed is True, (
        f"Step 3 introduced regressions or false alarms: {regr_3b.non_target_regressions}, FP={regr_3b.negative_control_fp_count}"
    )
    assert len(regr_3b.non_target_regressions) == 0, f"Non-target regressions found: {regr_3b.non_target_regressions}"
    assert regr_3b.negative_control_fp_count == 0, f"Negative control false positives found: {regr_3b.negative_control_fp_count}"

