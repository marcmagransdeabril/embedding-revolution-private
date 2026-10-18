#!/usr/bin/env python3
"""Automated BM25 retrieval evaluation harness for Ground-Truth Review (Phase E).

Evaluates Doc-Recall@k, Page-Recall@k (with +/-1 page tolerance), MRR, and
Score-Floor Abstention across 150 gold claims without an LLM in the loop.
Imports ground_check directly for high-performance deterministic evaluation.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

# Ensure scripts directory is importable
SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from ground_check import (
    DEFAULT_DB_PATH,
    build_fts5_query,
    resolve_toc_section,
    search_index,
)

EVAL_DIR = Path(__file__).resolve().parent
DEFAULT_CLAIMS_PATH = EVAL_DIR / "gold_claims.jsonl"


def extract_key_terms(claim_text: str) -> str:
    """Extract key technical noun phrases and terms from a claim for query routing."""
    # Remove citation parentheticals e.g. (1990), (2013), et al.
    cleaned = re.sub(r"\(\d{4}\)", "", claim_text)
    cleaned = re.sub(r"et al\.", "", cleaned)
    # Extract quoted phrases if present
    quotes = re.findall(r'"([^"]*)"', cleaned)
    # Remove common conversational stop phrases
    stop_phrases = [
        "smolensky", "hastie", "gelman", "bronstein", "rostami", "hamilton", "bishop",
        "frady", "hirose", "kleyko", "hajij", "hitzler", "sarker",
        "demonstrates that", "shows that", "proves that", "states that", "describes",
        "proposes the", "establishes", "categorize", "conclude that", "formulates",
        "according to", "in their paper", "in the reference", "the authors",
    ]
    for sp in stop_phrases:
        cleaned = re.sub(re.escape(sp), " ", cleaned, flags=re.IGNORECASE)

    words = re.findall(r"[\w\\{}^_+\-=]+", cleaned)
    # Keep words with length >= 3 or math symbols
    filtered = [w for w in words if len(w) >= 3 or any(c in w for c in "\\{}^_+-=")]
    combined = quotes + filtered
    return " ".join(combined[:12])


def evaluate_single_claim(
    con: sqlite3.Connection,
    claim_item: dict[str, Any],
    top_k: int = 5,
    floor: float = 0.0,
    query_mode: str = "fts5",
) -> dict[str, Any]:
    """Evaluate retrieval performance for a single gold claim."""
    claim_id = claim_item["id"]
    claim_text = claim_item["claim"]
    expected_label = claim_item["expected_label"]
    plausible_docs = claim_item.get("plausible_docs", [])
    target_pages = claim_item.get("target_pages", [])

    if query_mode == "raw":
        query = claim_text
    elif query_mode == "key_terms":
        query = extract_key_terms(claim_text)
    else:  # "fts5" default
        query = claim_text

    result = search_index(con, query=query, top_k=top_k, floor=floor)
    hits = result.get("hits", [])
    no_match = result.get("no_match")

    # Evaluate Doc-Recall and Page-Recall for answerable claims
    is_unanswerable = expected_label == "unanswerable"
    doc_hit_ranks: list[int] = []
    page_hit_ranks: list[int] = []

    if not is_unanswerable and plausible_docs:
        target_doc = plausible_docs[0]
        # Target page tolerance set (+/- 1 page)
        expanded_target_pages = set()
        for p in target_pages:
            expanded_target_pages.update({p - 1, p, p + 1})

        for rank, hit in enumerate(hits, start=1):
            hit_doc = hit["doc"]
            hit_page = hit["page_no"]

            # Doc match
            if hit_doc in plausible_docs or hit_doc == target_doc:
                doc_hit_ranks.append(rank)
                # Page match with tolerance
                if hit_page in expanded_target_pages:
                    page_hit_ranks.append(rank)

    # Abstention check for unanswerable
    abstained = len(hits) == 0

    return {
        "id": claim_id,
        "set": claim_item["set"],
        "expected_label": expected_label,
        "category": claim_item.get("category"),
        "obviousness": claim_item.get("obviousness"),
        "error_type": claim_item.get("error_type"),
        "query": query,
        "hits_count": len(hits),
        "top_score": hits[0]["score"] if hits else (no_match["best_score"] if no_match else 0.0),
        "top_doc": hits[0]["doc"] if hits else (no_match["nearest_doc"] if no_match else None),
        "doc_recall_at_1": 1 if doc_hit_ranks and doc_hit_ranks[0] <= 1 else 0,
        "doc_recall_at_3": 1 if doc_hit_ranks and doc_hit_ranks[0] <= 3 else 0,
        "doc_recall_at_5": 1 if doc_hit_ranks and doc_hit_ranks[0] <= 5 else 0,
        "doc_mrr": 1.0 / doc_hit_ranks[0] if doc_hit_ranks else 0.0,
        "page_recall_at_1": 1 if page_hit_ranks and page_hit_ranks[0] <= 1 else 0,
        "page_recall_at_3": 1 if page_hit_ranks and page_hit_ranks[0] <= 3 else 0,
        "page_recall_at_5": 1 if page_hit_ranks and page_hit_ranks[0] <= 5 else 0,
        "page_mrr": 1.0 / page_hit_ranks[0] if page_hit_ranks else 0.0,
        "abstained": abstained,
        "correct_abstention": 1 if (is_unanswerable and abstained) else (0 if is_unanswerable else None),
        "false_retrieval_on_unanswerable": 1 if (is_unanswerable and not abstained) else 0,
    }


def compute_metrics(eval_records: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute aggregate retrieval metrics across evaluation records."""
    answerable = [r for r in eval_records if r["expected_label"] != "unanswerable"]
    unanswerable = [r for r in eval_records if r["expected_label"] == "unanswerable"]

    n_ans = len(answerable)
    n_unans = len(unanswerable)

    metrics: dict[str, Any] = {
        "total_claims": len(eval_records),
        "answerable_count": n_ans,
        "unanswerable_count": n_unans,
    }

    if n_ans > 0:
        metrics["doc_recall@1"] = sum(r["doc_recall_at_1"] for r in answerable) / n_ans
        metrics["doc_recall@3"] = sum(r["doc_recall_at_3"] for r in answerable) / n_ans
        metrics["doc_recall@5"] = sum(r["doc_recall_at_5"] for r in answerable) / n_ans
        metrics["doc_mrr"] = sum(r["doc_mrr"] for r in answerable) / n_ans

        metrics["page_recall@1"] = sum(r["page_recall_at_1"] for r in answerable) / n_ans
        metrics["page_recall@3"] = sum(r["page_recall_at_3"] for r in answerable) / n_ans
        metrics["page_recall@5"] = sum(r["page_recall_at_5"] for r in answerable) / n_ans
        metrics["page_mrr"] = sum(r["page_mrr"] for r in answerable) / n_ans

    if n_unans > 0:
        metrics["correct_abstention_rate"] = sum(1 for r in unanswerable if r["abstained"]) / n_unans
        metrics["unanswerable_false_retrieval_rate"] = sum(1 for r in unanswerable if not r["abstained"]) / n_unans

    return metrics


def evaluate_suite(
    claims_path: Path | str = DEFAULT_CLAIMS_PATH,
    db_path: Path | str = DEFAULT_DB_PATH,
    top_k: int = 5,
    floor: float = 0.0,
    query_mode: str = "fts5",
) -> dict[str, Any]:
    """Run full evaluation suite over claims JSONL file."""
    claims_file = Path(claims_path)
    if not claims_file.is_file():
        raise FileNotFoundError(f"Claims file not found: {claims_file}")

    claims: list[dict[str, Any]] = []
    with open(claims_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                claims.append(json.loads(line))

    con = sqlite3.connect(str(db_path))
    start_time = time.perf_counter()

    records = [
        evaluate_single_claim(con, c, top_k=top_k, floor=floor, query_mode=query_mode)
        for c in claims
    ]
    elapsed = time.perf_counter() - start_time
    con.close()

    # Overall metrics
    overall = compute_metrics(records)

    # Breakdowns
    by_set: dict[str, Any] = {}
    for s in ("corpus", "math"):
        subset = [r for r in records if r["set"] == s]
        if subset:
            by_set[s] = compute_metrics(subset)

    by_category: dict[str, Any] = {}
    categories = sorted(list({r["category"] for r in records if r["category"] is not None}))
    for cat in categories:
        subset = [r for r in records if r["category"] == cat]
        if subset:
            by_category[cat] = compute_metrics(subset)

    by_obviousness: dict[str, Any] = {}
    for obv in ("obvious", "non-obvious"):
        subset = [r for r in records if r["obviousness"] == obv]
        if subset:
            by_obviousness[obv] = compute_metrics(subset)

    # Score floor sensitivity sweep (evaluated instantaneously on raw hits)
    floor_sweep: list[dict[str, Any]] = []
    for test_floor in (0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0):
        sweep_records: list[dict[str, Any]] = []
        for r, c in zip(records, claims):
            # check if top score passes test_floor
            passed_floor = r["top_score"] >= test_floor
            abstained = not passed_floor or r["hits_count"] == 0
            is_unans = r["expected_label"] == "unanswerable"

            sweep_r = dict(r)
            sweep_r["abstained"] = abstained
            if not passed_floor:
                sweep_r["doc_recall_at_1"] = 0
                sweep_r["doc_recall_at_3"] = 0
                sweep_r["doc_recall_at_5"] = 0
                sweep_r["page_recall_at_1"] = 0
                sweep_r["page_recall_at_3"] = 0
                sweep_r["page_recall_at_5"] = 0
            sweep_records.append(sweep_r)

        m = compute_metrics(sweep_records)
        floor_sweep.append({
            "floor": test_floor,
            "doc_recall@3": m.get("doc_recall@3", 0.0),
            "page_recall@3": m.get("page_recall@3", 0.0),
            "correct_abstention_rate": m.get("correct_abstention_rate", 0.0),
        })

    return {
        "status": "ok",
        "claims_count": len(claims),
        "elapsed_seconds": round(elapsed, 4),
        "queries_per_second": round(len(claims) / max(elapsed, 1e-6), 1),
        "query_mode": query_mode,
        "floor": floor,
        "top_k": top_k,
        "overall": overall,
        "by_set": by_set,
        "by_category": by_category,
        "by_obviousness": by_obviousness,
        "floor_sweep": floor_sweep,
        "records": records,
    }


def format_report(results: dict[str, Any]) -> str:
    """Format evaluation results into a clean markdown report."""
    lines: list[str] = []
    lines.append("# Phase E BM25 Retrieval Evaluation Report")
    lines.append("")
    lines.append(f"- **Total Claims**: {results['claims_count']}")
    lines.append(f"- **Query Mode**: `{results['query_mode']}` | **Score Floor**: `{results['floor']}` | **Top-K**: `{results['top_k']}`")
    lines.append(f"- **Runtime**: {results['elapsed_seconds']} s ({results['queries_per_second']} queries/sec)")
    lines.append("")

    lines.append("## 1. Overall Performance")
    lines.append("")
    ov = results["overall"]
    lines.append("| Metric | Value | Percentage |")
    lines.append("|---|---|---|")
    lines.append(f"| **Doc-Recall@1** | {ov.get('doc_recall@1', 0.0):.4f} | {ov.get('doc_recall@1', 0.0)*100:.1f}% |")
    lines.append(f"| **Doc-Recall@3** | {ov.get('doc_recall@3', 0.0):.4f} | {ov.get('doc_recall@3', 0.0)*100:.1f}% |")
    lines.append(f"| **Doc-Recall@5** | {ov.get('doc_recall@5', 0.0):.4f} | {ov.get('doc_recall@5', 0.0)*100:.1f}% |")
    lines.append(f"| **Doc-MRR** | {ov.get('doc_mrr', 0.0):.4f} | — |")
    lines.append(f"| **Page-Recall@1** (±1 page) | {ov.get('page_recall@1', 0.0):.4f} | {ov.get('page_recall@1', 0.0)*100:.1f}% |")
    lines.append(f"| **Page-Recall@3** (±1 page) | {ov.get('page_recall@3', 0.0):.4f} | {ov.get('page_recall@3', 0.0)*100:.1f}% |")
    lines.append(f"| **Page-Recall@5** (±1 page) | {ov.get('page_recall@5', 0.0):.4f} | {ov.get('page_recall@5', 0.0)*100:.1f}% |")
    lines.append(f"| **Page-MRR** | {ov.get('page_mrr', 0.0):.4f} | — |")
    if "correct_abstention_rate" in ov:
        lines.append(f"| **Correct Abstention Rate (Unanswerable)** | {ov.get('correct_abstention_rate', 0.0):.4f} | {ov.get('correct_abstention_rate', 0.0)*100:.1f}% |")
    lines.append("")

    lines.append("## 2. Breakdown by Set")
    lines.append("")
    lines.append("| Set | Count | Doc-Recall@1 | Doc-Recall@3 | Doc-Recall@5 | Page-Recall@3 | Page-Recall@5 |")
    lines.append("|---|---|---|---|---|---|---|")
    for s_name, s_met in results["by_set"].items():
        ans_count = s_met.get("answerable_count", s_met.get("total_claims", 0))
        lines.append(
            f"| `{s_name}` | {ans_count} | {s_met.get('doc_recall@1', 0.0)*100:.1f}% | {s_met.get('doc_recall@3', 0.0)*100:.1f}% | {s_met.get('doc_recall@5', 0.0)*100:.1f}% | {s_met.get('page_recall@3', 0.0)*100:.1f}% | {s_met.get('page_recall@5', 0.0)*100:.1f}% |"
        )
    lines.append("")

    lines.append("## 3. Breakdown by Phrasing & Category (Set `corpus`)")
    lines.append("")
    lines.append("| Category | Count | Doc-Recall@1 | Doc-Recall@3 | Page-Recall@3 | Page-Recall@5 | Abstention Rate |")
    lines.append("|---|---|---|---|---|---|---|")
    for cat_name, cat_met in results["by_category"].items():
        cnt = cat_met["total_claims"]
        d1 = f"{cat_met.get('doc_recall@1', 0.0)*100:.1f}%" if "doc_recall@1" in cat_met else "—"
        d3 = f"{cat_met.get('doc_recall@3', 0.0)*100:.1f}%" if "doc_recall@3" in cat_met else "—"
        p3 = f"{cat_met.get('page_recall@3', 0.0)*100:.1f}%" if "page_recall@3" in cat_met else "—"
        p5 = f"{cat_met.get('page_recall@5', 0.0)*100:.1f}%" if "page_recall@5" in cat_met else "—"
        abs_r = f"{cat_met.get('correct_abstention_rate', 0.0)*100:.1f}%" if "correct_abstention_rate" in cat_met else "—"
        lines.append(f"| `{cat_name}` | {cnt} | {d1} | {d3} | {p3} | {p5} | {abs_r} |")
    lines.append("")

    lines.append("## 4. Breakdown by Obviousness (Set `math`)")
    lines.append("")
    lines.append("| Obviousness | Count | Doc-Recall@3 | Doc-Recall@5 | Page-Recall@3 | Page-Recall@5 | Page-MRR |")
    lines.append("|---|---|---|---|---|---|---|")
    for obv_name, obv_met in results["by_obviousness"].items():
        cnt = obv_met["total_claims"]
        lines.append(
            f"| `{obv_name}` | {cnt} | {obv_met.get('doc_recall@3', 0.0)*100:.1f}% | {obv_met.get('doc_recall@5', 0.0)*100:.1f}% | {obv_met.get('page_recall@3', 0.0)*100:.1f}% | {obv_met.get('page_recall@5', 0.0)*100:.1f}% | {obv_met.get('page_mrr', 0.0):.4f} |"
        )
    lines.append("")

    lines.append("## 5. Score Floor Sensitivity Analysis")
    lines.append("")
    lines.append("| Floor Threshold | Doc-Recall@3 | Page-Recall@3 | Unanswerable Abstention Rate |")
    lines.append("|---|---|---|---|")
    for item in results["floor_sweep"]:
        lines.append(
            f"| `{item['floor']:.1f}` | {item['doc_recall@3']*100:.1f}% | {item['page_recall@3']*100:.1f}% | {item['correct_abstention_rate']*100:.1f}% |"
        )
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate BM25 retrieval over gold claims dataset.")
    parser.add_argument("--claims-file", type=Path, default=DEFAULT_CLAIMS_PATH, help="Path to gold_claims.jsonl")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH, help="Path to index.sqlite")
    parser.add_argument("--top-k", type=int, default=5, help="Number of top hits to evaluate (default: 5)")
    parser.add_argument("--floor", type=float, default=0.0, help="Score floor threshold (default: 0.0)")
    parser.add_argument("--query-mode", choices=["fts5", "raw", "key_terms"], default="fts5", help="Query construction mode")
    parser.add_argument("--output-json", type=Path, default=None, help="Save evaluation summary as JSON")
    parser.add_argument("--verbose", action="store_true", help="Print per-claim evaluation detail")

    args = parser.parse_args()

    results = evaluate_suite(
        claims_path=args.claims_file,
        db_path=args.db_path,
        top_k=args.top_k,
        floor=args.floor,
        query_mode=args.query_mode,
    )

    if args.verbose:
        for r in results["records"]:
            print(f"[{r['id']}] set={r['set']} label={r['expected_label']} cat={r['category']} doc_rec@3={r['doc_recall_at_3']} page_rec@3={r['page_recall_at_3']} abstained={r['abstained']}")

    report = format_report(results)
    print(report)

    if args.output_json:
        # Exclude bulky raw records from summary JSON unless requested
        out_data = {k: v for k, v in results.items() if k != "records"}
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(out_data, f, indent=2)
        print(f"\nSaved evaluation summary JSON to {args.output_json}")


if __name__ == "__main__":
    main()
