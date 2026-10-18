#!/usr/bin/env python3
"""Unit tests for Phase E evaluation harness: gold_claims.jsonl, eval_retrieval, and eval_closed_book."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

import pytest

# Ensure script and eval directories are importable
SKILL_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
EVAL_DIR = SKILL_ROOT / "eval"

for d in (str(SCRIPTS_DIR), str(EVAL_DIR)):
    if d not in sys.path:
        sys.path.insert(0, d)

from eval_closed_book import (
    evaluate_closed_book_suite,
    format_closed_book_report,
    simulated_closed_book_inference,
)
from eval_retrieval import (
    compute_metrics,
    evaluate_single_claim,
    evaluate_suite,
    extract_key_terms,
    format_report,
)
import ground_check


GOLD_CLAIMS_PATH = EVAL_DIR / "gold_claims.jsonl"


def test_gold_claims_dataset_integrity():
    """Validates the schema, distribution, and grounding invariants of gold_claims.jsonl."""
    assert GOLD_CLAIMS_PATH.is_file(), f"Missing gold_claims.jsonl at {GOLD_CLAIMS_PATH}"

    claims: list[dict[str, Any]] = []
    with open(GOLD_CLAIMS_PATH, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            assert line, f"Empty line {idx} in gold_claims.jsonl"
            claim = json.loads(line)
            claims.append(claim)

    assert len(claims) == 150, f"Expected exactly 150 claims, got {len(claims)}"

    # Check ID uniqueness
    ids = [c["id"] for c in claims]
    assert len(ids) == len(set(ids)), "Claim IDs must be unique"

    corpus_claims = [c for c in claims if c["set"] == "corpus"]
    math_claims = [c for c in claims if c["set"] == "math"]

    assert len(corpus_claims) == 100, f"Expected 100 corpus claims, got {len(corpus_claims)}"
    assert len(math_claims) == 50, f"Expected 50 math claims, got {len(math_claims)}"

    # Corpus distribution: 35 true, 35 false, 30 unanswerable
    c_true = [c for c in corpus_claims if c["expected_label"] == "true"]
    c_false = [c for c in corpus_claims if c["expected_label"] == "false"]
    c_unans = [c for c in corpus_claims if c["expected_label"] == "unanswerable"]

    assert len(c_true) == 35, f"Expected 35 true corpus claims, got {len(c_true)}"
    assert len(c_false) == 35, f"Expected 35 false corpus claims, got {len(c_false)}"
    assert len(c_unans) == 30, f"Expected 30 unanswerable corpus claims, got {len(c_unans)}"

    # Phrasing categories in corpus true/false
    for c in c_true + c_false:
        assert c["category"] in ("direct", "synonym", "analogy"), f"Invalid category for answerable corpus claim: {c['category']}"
        assert len(c["plausible_docs"]) >= 1
        assert len(c["target_pages"]) >= 1
        assert all(isinstance(p, int) and p > 0 for p in c["target_pages"])
        assert isinstance(c["target_quote"], str) and len(c["target_quote"]) > 0

    # Unanswerable claims invariants
    for c in c_unans:
        assert c["category"] in ("anachronism", "misattribution", "overly-specific-absent", "off-topic-adjacent"), (
            f"Invalid unanswerable category: {c['category']}"
        )
        assert c["target_pages"] == []
        assert c["target_quote"] is None

    # Math distribution: 25 true, 25 false
    m_true = [c for c in math_claims if c["expected_label"] == "true"]
    m_false = [c for c in math_claims if c["expected_label"] == "false"]

    assert len(m_true) == 25, f"Expected 25 true math claims, got {len(m_true)}"
    assert len(m_false) == 25, f"Expected 25 false math claims, got {len(m_false)}"

    for c in math_claims:
        assert c["obviousness"] in ("obvious", "non-obvious")
        assert len(c["plausible_docs"]) >= 1
        assert len(c["target_pages"]) >= 1
        assert all(isinstance(p, int) and p > 0 for p in c["target_pages"])
        assert isinstance(c["target_quote"], str) and len(c["target_quote"]) > 0


def test_eval_retrieval_metrics_computation():
    """Tests compute_metrics and tolerance scoring in eval_retrieval."""
    mock_records = [
        {
            "id": "c1",
            "set": "corpus",
            "expected_label": "true",
            "doc_recall_at_1": 1,
            "doc_recall_at_3": 1,
            "doc_recall_at_5": 1,
            "doc_mrr": 1.0,
            "page_recall_at_1": 1,
            "page_recall_at_3": 1,
            "page_recall_at_5": 1,
            "page_mrr": 1.0,
            "abstained": False,
        },
        {
            "id": "c2",
            "set": "corpus",
            "expected_label": "false",
            "doc_recall_at_1": 0,
            "doc_recall_at_3": 1,
            "doc_recall_at_5": 1,
            "doc_mrr": 0.5,
            "page_recall_at_1": 0,
            "page_recall_at_3": 1,
            "page_recall_at_5": 1,
            "page_mrr": 0.5,
            "abstained": False,
        },
        {
            "id": "c3",
            "set": "corpus",
            "expected_label": "unanswerable",
            "abstained": True,
        },
    ]

    metrics = compute_metrics(mock_records)
    assert metrics["total_claims"] == 3
    assert metrics["answerable_count"] == 2
    assert metrics["unanswerable_count"] == 1
    assert metrics["doc_recall@1"] == 0.5
    assert metrics["doc_recall@3"] == 1.0
    assert metrics["page_recall@1"] == 0.5
    assert metrics["page_recall@3"] == 1.0
    assert metrics["correct_abstention_rate"] == 1.0


def test_eval_retrieval_extract_key_terms():
    """Tests key term extraction for query preprocessing."""
    text = "Smolensky (1990) demonstrates that tensor product representations bind variables and fillers."
    terms = extract_key_terms(text)
    assert "tensor" in terms
    assert "product" in terms
    assert "representations" in terms
    assert "(1990)" not in terms


def test_eval_closed_book_simulation():
    """Tests Baseline 0 closed-book simulation metrics and report formatting."""
    results = evaluate_closed_book_suite(GOLD_CLAIMS_PATH, mode="simulated")
    assert results["status"] == "ok"
    assert results["claims_count"] == 150
    assert 0.5 <= results["overall_accuracy"] <= 0.85
    assert results["unanswerable_hallucination_rate"] > 0.5  # Closed-book models hallucinate on missing topics
    assert results["citation_hallucination_rate"] > 0.8  # Closed-book models fail to cite exact pages

    report = format_closed_book_report(results)
    assert "# Baseline 0: Naive Closed-Book LLM Evaluation Report" in report
    assert "Confusion Matrix" in report
