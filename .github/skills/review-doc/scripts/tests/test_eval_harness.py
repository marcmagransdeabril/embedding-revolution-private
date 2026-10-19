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
    """Verify that benchmark dataset has 55 cases (42 defect cases across categories A-G + 13 negative controls)."""
    assert BENCHMARK_PATH.exists(), f"Benchmark dataset missing at {BENCHMARK_PATH}"
    cases = load_benchmark_cases(BENCHMARK_PATH)
    assert len(cases) == 55, f"Expected exactly 55 cases, got {len(cases)}"

    expected_categories = {
        "A_statistical": 6,
        "B_methodological": 11,
        "C_evaluator_bias": 5,
        "D_prior_art": 10,
        "E_tail_vs_mean": 5,
        "F_latex_formatting": 2,
        "G_first_principles_fermi": 3,
        "Z_negative_control": 13,
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
    assert paired_verbose_count == 55, f"Expected 55 paired verbose variants, got {paired_verbose_count}"


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
    assert b0_summary.total_cases == 55
    assert 0.0 <= b0_summary.recall <= 1.0
    assert 0.0 <= b0_summary.precision <= 1.0
    assert 0.0 <= b0_summary.f1_score <= 1.0
    assert b0_summary.review_yield_per_1k > 0.0


def test_step1_to_step9_baseline_prompts_integrity():
    """Verify that Step 1 through Step 9 baseline prompt variants exist and are well-formed."""
    arm1a = EVAL_DIR / "baselines" / "step1_arm1a_verbose.md"
    arm1b = EVAL_DIR / "baselines" / "step1_arm1b_compact.md"
    arm2a = EVAL_DIR / "baselines" / "step2_arm2a_verbose.md"
    arm2b = EVAL_DIR / "baselines" / "step2_arm2b_compact.md"
    arm3a = EVAL_DIR / "baselines" / "step3_arm3a_verbose.md"
    arm3b = EVAL_DIR / "baselines" / "step3_arm3b_compact.md"
    arm4a = EVAL_DIR / "baselines" / "step4_arm4a_verbose.md"
    arm4b = EVAL_DIR / "baselines" / "step4_arm4b_compact.md"
    arm5a = EVAL_DIR / "baselines" / "step5_arm5a_verbose.md"
    arm5b = EVAL_DIR / "baselines" / "step5_arm5b_compact.md"
    arm6a = EVAL_DIR / "baselines" / "step6_arm6a_verbose.md"
    arm6b = EVAL_DIR / "baselines" / "step6_arm6b_compact.md"
    arm7a = EVAL_DIR / "baselines" / "step7_arm7a_verbose.md"
    arm7b = EVAL_DIR / "baselines" / "step7_arm7b_compact.md"
    arm8a = EVAL_DIR / "baselines" / "step8_arm8a_verbose.md"
    arm8b = EVAL_DIR / "baselines" / "step8_arm8b_compact.md"
    arm9a = EVAL_DIR / "baselines" / "step9_arm9a_verbose.md"
    arm9b = EVAL_DIR / "baselines" / "step9_arm9b_compact.md"

    for p in [arm1a, arm1b, arm2a, arm2b, arm3a, arm3b, arm4a, arm4b, arm5a, arm5b, arm6a, arm6b, arm7a, arm7b, arm8a, arm8b, arm9a, arm9b]:
        assert p.exists(), f"Baseline variant missing at {p}"
        text = p.read_text(encoding="utf-8")
        assert "---" in text, f"Missing YAML frontmatter in {p}"
        tokens = count_tokens(text)
        assert 1500 <= tokens <= 3500, f"Token count ({tokens}) outside reasonable bounds for {p}"

    assert count_tokens(arm2b.read_text(encoding="utf-8")) < count_tokens(arm2a.read_text(encoding="utf-8")), (
        "Arm 2B compact variant must have smaller token footprint than Arm 2A verbose"
    )
    assert count_tokens(arm3b.read_text(encoding="utf-8")) < count_tokens(arm3a.read_text(encoding="utf-8")), (
        "Arm 3B compact variant must have smaller token footprint than Arm 3A verbose"
    )
    assert count_tokens(arm4b.read_text(encoding="utf-8")) < count_tokens(arm4a.read_text(encoding="utf-8")), (
        "Arm 4B compact variant must have smaller token footprint than Arm 4A verbose"
    )
    assert count_tokens(arm5b.read_text(encoding="utf-8")) < count_tokens(arm5a.read_text(encoding="utf-8")), (
        "Arm 5B compact variant must have smaller token footprint than Arm 5A verbose"
    )
    assert count_tokens(arm6b.read_text(encoding="utf-8")) < count_tokens(arm6a.read_text(encoding="utf-8")), (
        "Arm 6B compact variant must have smaller token footprint than Arm 6A verbose"
    )
    assert count_tokens(arm7b.read_text(encoding="utf-8")) < count_tokens(arm7a.read_text(encoding="utf-8")), (
        "Arm 7B compact variant must have smaller token footprint than Arm 7A verbose"
    )
    assert count_tokens(arm8b.read_text(encoding="utf-8")) < count_tokens(arm8a.read_text(encoding="utf-8")), (
        "Arm 8B compact variant must have smaller token footprint than Arm 8A verbose"
    )
    assert count_tokens(arm9b.read_text(encoding="utf-8")) < count_tokens(arm9a.read_text(encoding="utf-8")), (
        "Arm 9B compact variant must have smaller token footprint than Arm 9A verbose"
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


def test_step4_researcher_dof_gates():
    """Verify Step 4 Incentive-Caused Bias & Researcher Degrees of Freedom decision gates and non-target regression invariance."""
    from eval_review_skill import ARM3B_PATH, ARM4A_PATH, ARM4B_PATH, compute_regression_analysis

    summary_3b = run_benchmark_evaluation(
        skill_name="Arm 3B (Baseline)",
        skill_path=ARM3B_PATH,
        skill_type="custom",
    )
    summary_4a = run_benchmark_evaluation(
        skill_name="Arm 4A",
        skill_path=ARM4A_PATH,
        skill_type="custom",
    )
    summary_4b = run_benchmark_evaluation(
        skill_name="Arm 4B",
        skill_path=ARM4B_PATH,
        skill_type="custom",
    )

    cat_b_4b = summary_4b.category_breakdown["B_methodological"]
    precision_b_4b = cat_b_4b["tp"] / (cat_b_4b["tp"] + cat_b_4b["fp"])

    # 1. Detection on Researcher DOF cases (at least 5/8 caught, 0 false alarms)
    assert cat_b_4b["tp"] >= 5, f"Expected >= 5 Category B defects caught by Step 4, got {cat_b_4b['tp']}"

    # 2. Precision >= 90%
    assert precision_b_4b >= 0.90, f"Expected >= 90% precision in Cat B, got {precision_b_4b}"

    # 3. Equal overall recall to Arm 4A
    assert summary_4b.recall == summary_4a.recall, "Arm 4B should match Arm 4A recall"

    # 4. Yield advantage (Arm 4B > Arm 4A)
    assert summary_4b.review_yield_per_1k > summary_4a.review_yield_per_1k, (
        f"Arm 4B yield ({summary_4b.review_yield_per_1k}) must exceed Arm 4A ({summary_4a.review_yield_per_1k})"
    )

    # 5. Non-target regression invariance & negative control integrity
    regr_4b = compute_regression_analysis(summary_3b, summary_4b, target_category="B_methodological")
    assert regr_4b.zero_regression_passed is True, (
        f"Step 4 introduced regressions or false alarms: {regr_4b.non_target_regressions}, FP={regr_4b.negative_control_fp_count}"
    )
    assert len(regr_4b.non_target_regressions) == 0, f"Non-target regressions found: {regr_4b.non_target_regressions}"
    assert regr_4b.negative_control_fp_count == 0, f"Negative control false positives found: {regr_4b.negative_control_fp_count}"


def test_step5_pre_mortem_gates():
    """Verify Step 5 Pre-Mortem & Inversion Failure-Mode Analysis decision gates and non-target regression invariance."""
    from eval_review_skill import ARM4B_PATH, ARM5A_PATH, ARM5B_PATH, compute_regression_analysis

    summary_4b = run_benchmark_evaluation(
        skill_name="Arm 4B (Baseline)",
        skill_path=ARM4B_PATH,
        skill_type="custom",
    )
    summary_5a = run_benchmark_evaluation(
        skill_name="Arm 5A",
        skill_path=ARM5A_PATH,
        skill_type="custom",
    )
    summary_5b = run_benchmark_evaluation(
        skill_name="Arm 5B",
        skill_path=ARM5B_PATH,
        skill_type="custom",
    )

    cat_b_5b = summary_5b.category_breakdown["B_methodological"]
    crit_recall_5b = cat_b_5b["crit_tp"] / cat_b_5b["crit_total"]
    total_recall_5b = cat_b_5b["tp"] / cat_b_5b["total"]
    precision_b_5b = cat_b_5b["tp"] / (cat_b_5b["tp"] + cat_b_5b["fp"])

    # 1. Detection on Category B failure modes and boundary conditions (at least 8 cases caught)
    assert cat_b_5b["tp"] >= 8, f"Expected >= 8 Category B defects caught by Step 5, got {cat_b_5b['tp']}"
    assert cat_b_5b["crit_tp"] >= 7, f"Expected >= 7 critical Category B defects caught by Step 5, got {cat_b_5b['crit_tp']}"

    # 2. Precision >= 90%
    assert precision_b_5b >= 0.90, f"Expected >= 90% precision in Cat B, got {precision_b_5b}"

    # 3. Equal overall recall to Arm 5A
    assert summary_5b.recall == summary_5a.recall, "Arm 5B should match Arm 5A recall"

    # 4. Yield advantage (Arm 5B > Arm 5A)
    assert summary_5b.review_yield_per_1k > summary_5a.review_yield_per_1k, (
        f"Arm 5B yield ({summary_5b.review_yield_per_1k}) must exceed Arm 5A ({summary_5a.review_yield_per_1k})"
    )

    # 5. Non-target regression invariance & negative control integrity
    regr_5b = compute_regression_analysis(summary_4b, summary_5b, target_category="B_methodological")
    assert regr_5b.zero_regression_passed is True, (
        f"Step 5 introduced regressions or false alarms: {regr_5b.non_target_regressions}, FP={regr_5b.negative_control_fp_count}"
    )
    assert len(regr_5b.non_target_regressions) == 0, f"Non-target regressions found: {regr_5b.non_target_regressions}"
    assert regr_5b.negative_control_fp_count == 0, f"Negative control false positives found: {regr_5b.negative_control_fp_count}"


def test_step6_fermi_bounds_gates():
    """Verify Step 6 First-Principles & Fermi Bounds decision gates and non-target regression invariance."""
    from eval_review_skill import ARM5B_PATH, ARM6A_PATH, ARM6B_PATH, compute_regression_analysis

    summary_5b = run_benchmark_evaluation(
        skill_name="Arm 5B (Baseline)",
        skill_path=ARM5B_PATH,
        skill_type="custom",
    )
    summary_6a = run_benchmark_evaluation(
        skill_name="Arm 6A",
        skill_path=ARM6A_PATH,
        skill_type="custom",
    )
    summary_6b = run_benchmark_evaluation(
        skill_name="Arm 6B",
        skill_path=ARM6B_PATH,
        skill_type="custom",
    )

    cat_g_6b = summary_6b.category_breakdown["G_first_principles_fermi"]
    crit_recall_6b = cat_g_6b["crit_tp"] / cat_g_6b["crit_total"]
    total_recall_6b = cat_g_6b["tp"] / cat_g_6b["total"]
    precision_g_6b = cat_g_6b["tp"] / (cat_g_6b["tp"] + cat_g_6b["fp"])

    # 1. 100% detection on Category G Fermi bound violations (3/3 cases)
    assert total_recall_6b == 1.0, f"Expected 100% Category G recall, got {total_recall_6b}"
    assert crit_recall_6b == 1.0, f"Expected 100% critical Category G recall, got {crit_recall_6b}"

    # 2. Precision >= 90%
    assert precision_g_6b >= 0.90, f"Expected >= 90% precision in Cat G, got {precision_g_6b}"

    # 3. Equal overall recall to Arm 6A
    assert summary_6b.recall == summary_6a.recall, "Arm 6B should match Arm 6A recall"

    # 4. Yield advantage (Arm 6B > Arm 6A)
    assert summary_6b.review_yield_per_1k > summary_6a.review_yield_per_1k, (
        f"Arm 6B yield ({summary_6b.review_yield_per_1k}) must exceed Arm 6A ({summary_6a.review_yield_per_1k})"
    )

    # 5. Non-target regression invariance & negative control integrity
    regr_6b = compute_regression_analysis(summary_5b, summary_6b, target_category="G_first_principles_fermi")
    assert regr_6b.zero_regression_passed is True, (
        f"Step 6 introduced regressions or false alarms: {regr_6b.non_target_regressions}, FP={regr_6b.negative_control_fp_count}"
    )
    assert len(regr_6b.non_target_regressions) == 0, f"Non-target regressions found: {regr_6b.non_target_regressions}"
    assert regr_6b.negative_control_fp_count == 0, f"Negative control false positives found: {regr_6b.negative_control_fp_count}"


def test_step7_resource_normalization_gates():
    """Verify Step 7 Resource- & Effort-Normalized Efficiency decision gates and non-target regression invariance."""
    from eval_review_skill import ARM6B_PATH, ARM7A_PATH, ARM7B_PATH, compute_regression_analysis

    summary_6b = run_benchmark_evaluation(
        skill_name="Arm 6B (Baseline)",
        skill_path=ARM6B_PATH,
        skill_type="custom",
    )
    summary_7a = run_benchmark_evaluation(
        skill_name="Arm 7A",
        skill_path=ARM7A_PATH,
        skill_type="custom",
    )
    summary_7b = run_benchmark_evaluation(
        skill_name="Arm 7B",
        skill_path=ARM7B_PATH,
        skill_type="custom",
    )

    cat_b_7b = summary_7b.category_breakdown["B_methodological"]
    crit_recall_7b = cat_b_7b["crit_tp"] / cat_b_7b["crit_total"]
    total_recall_7b = cat_b_7b["tp"] / cat_b_7b["total"]
    precision_b_7b = cat_b_7b["tp"] / (cat_b_7b["tp"] + cat_b_7b["fp"])

    # 1. 100% detection on Category B resource normalization & methodological defects (11/11 cases)
    assert total_recall_7b == 1.0, f"Expected 100% Category B recall, got {total_recall_7b}"
    assert crit_recall_7b == 1.0, f"Expected 100% critical Category B recall, got {crit_recall_7b}"

    # 2. Precision >= 90%
    assert precision_b_7b >= 0.90, f"Expected >= 90% precision in Cat B, got {precision_b_7b}"

    # 3. Equal overall recall to Arm 7A
    assert summary_7b.recall == summary_7a.recall, "Arm 7B should match Arm 7A recall"

    # 4. Yield advantage (Arm 7B > Arm 7A)
    assert summary_7b.review_yield_per_1k > summary_7a.review_yield_per_1k, (
        f"Arm 7B yield ({summary_7b.review_yield_per_1k}) must exceed Arm 7A ({summary_7a.review_yield_per_1k})"
    )

    # 5. Non-target regression invariance & negative control integrity
    regr_7b = compute_regression_analysis(summary_6b, summary_7b, target_category="B_methodological")
    assert regr_7b.zero_regression_passed is True, (
        f"Step 7 introduced regressions or false alarms: {regr_7b.non_target_regressions}, FP={regr_7b.negative_control_fp_count}"
    )
    assert len(regr_7b.non_target_regressions) == 0, f"Non-target regressions found: {regr_7b.non_target_regressions}"
    assert regr_7b.negative_control_fp_count == 0, f"Negative control false positives found: {regr_7b.negative_control_fp_count}"


def test_step8_prior_art_gates():
    """Verify Step 8 Prior-Art Grounding & Epistemic Circle of Competence decision gates and non-target regression invariance."""
    from eval_review_skill import ARM7B_PATH, ARM8A_PATH, ARM8B_PATH, compute_regression_analysis

    summary_7b = run_benchmark_evaluation(
        skill_name="Arm 7B (Baseline)",
        skill_path=ARM7B_PATH,
        skill_type="custom",
    )
    summary_8a = run_benchmark_evaluation(
        skill_name="Arm 8A",
        skill_path=ARM8A_PATH,
        skill_type="custom",
    )
    summary_8b, a8b_cases = run_benchmark_evaluation(
        skill_name="Arm 8B",
        skill_path=ARM8B_PATH,
        skill_type="custom",
        return_case_results=True,
    )

    cat_d_8b = summary_8b.category_breakdown["D_prior_art"]
    crit_recall_8b = cat_d_8b["crit_tp"] / cat_d_8b["crit_total"]
    total_recall_8b = cat_d_8b["tp"] / cat_d_8b["total"]
    precision_d_8b = cat_d_8b["tp"] / (cat_d_8b["tp"] + cat_d_8b["fp"])

    # 1. 100% detection on Category D prior-art defects (10/10 cases)
    assert total_recall_8b == 1.0, f"Expected 100% Category D recall, got {total_recall_8b}"
    assert crit_recall_8b == 1.0, f"Expected 100% critical Category D recall, got {crit_recall_8b}"

    # 2. Precision >= 90%
    assert precision_d_8b >= 0.90, f"Expected >= 90% precision in Cat D, got {precision_d_8b}"

    # 3. Equal overall recall to Arm 8A
    assert summary_8b.recall == summary_8a.recall, "Arm 8B should match Arm 8A recall"

    # 4. Yield advantage (Arm 8B > Arm 8A)
    assert summary_8b.review_yield_per_1k > summary_8a.review_yield_per_1k, (
        f"Arm 8B yield ({summary_8b.review_yield_per_1k}) must exceed Arm 8A ({summary_8a.review_yield_per_1k})"
    )

    # 5. Non-target regression invariance & negative control integrity
    regr_8b = compute_regression_analysis(summary_7b, summary_8b, target_category="D_prior_art")
    assert regr_8b.zero_regression_passed is True, (
        f"Step 8 introduced regressions or false alarms: {regr_8b.non_target_regressions}, FP={regr_8b.negative_control_fp_count}"
    )


def test_step9_statistical_consistency_gates():
    """Verify Step 9 Statistical Consistency & Anomaly Auditing decision gates and non-target regression invariance."""
    from eval_review_skill import ARM8B_PATH, ARM9A_PATH, ARM9B_PATH, compute_regression_analysis

    summary_8b = run_benchmark_evaluation(
        skill_name="Arm 8B (Baseline)",
        skill_path=ARM8B_PATH,
        skill_type="custom",
    )
    summary_9a = run_benchmark_evaluation(
        skill_name="Arm 9A",
        skill_path=ARM9A_PATH,
        skill_type="custom",
    )
    summary_9b, a9b_cases = run_benchmark_evaluation(
        skill_name="Arm 9B",
        skill_path=ARM9B_PATH,
        skill_type="custom",
        return_case_results=True,
    )

    cat_a_9b = summary_9b.category_breakdown["A_statistical"]
    crit_recall_9b = cat_a_9b["crit_tp"] / cat_a_9b["crit_total"]
    total_recall_9b = cat_a_9b["tp"] / cat_a_9b["total"]
    precision_a_9b = cat_a_9b["tp"] / (cat_a_9b["tp"] + cat_a_9b["fp"])

    # 1. 100% detection on Category A statistical defects (6/6 cases)
    assert total_recall_9b == 1.0, f"Expected 100% Category A recall, got {total_recall_9b}"
    assert crit_recall_9b == 1.0, f"Expected 100% critical Category A recall, got {crit_recall_9b}"

    # 2. Precision >= 90%
    assert precision_a_9b >= 0.90, f"Expected >= 90% precision in Cat A, got {precision_a_9b}"

    # 3. 0 false alarms on specificity negative controls
    specificity_fp = sum(r.fp for r in a9b_cases if r.case_id in {"stat-neg-001", "stat-neg-002", "stat-neg-003"})
    assert specificity_fp == 0, f"Expected 0 false alarms on statistical specificity controls, got {specificity_fp}"

    # 4. Equal overall recall to Arm 9A
    assert summary_9b.recall == summary_9a.recall, "Arm 9B should match Arm 9A recall"

    # 5. Yield advantage (Arm 9B > Arm 9A)
    assert summary_9b.review_yield_per_1k > summary_9a.review_yield_per_1k, (
        f"Arm 9B yield ({summary_9b.review_yield_per_1k}) must exceed Arm 9A ({summary_9a.review_yield_per_1k})"
    )

    # 6. Non-target regression invariance & negative control integrity
    regr_9b = compute_regression_analysis(summary_8b, summary_9b, target_category="A_statistical")
    assert regr_9b.zero_regression_passed is True, (
        f"Step 9 introduced regressions or false alarms: {regr_9b.non_target_regressions}, FP={regr_9b.negative_control_fp_count}"
    )




