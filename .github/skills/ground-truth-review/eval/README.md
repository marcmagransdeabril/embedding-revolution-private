# Ground-Truth Review Skill: Evaluation Harness (Phase E)

This directory contains the Phase E empirical validation harness for the `ground-truth-review` skill.

## Contents

- `gold_claims.jsonl`: 150 gold evaluation claims (100 corpus claims [35 true / 35 false across direct, synonym, and analogy phrasings; 30 unanswerable across anachronisms, misattributions, overly specific absent details, and off-topic queries] + 50 math claims [25 true / 25 false across obvious and subtle non-obvious errors]).
- `eval_retrieval.py`: Automated BM25 retrieval evaluation harness. Computes Doc-Recall@k (k=1,3,5), Page-Recall@k ($\pm 1$ page tolerance), MRR, query mode comparison, and score-floor abstention.
- `eval_closed_book.py`: Baseline 0 Naive Closed-Book LLM evaluation harness. Measures zero-shot accuracy, hallucination/sycophancy rate on unanswerables, subtle math error catch rate, and citation fabrication rate.
- `build_dataset.py`: Source script for constructing, reconciling, and freezing the 150 gold claims against `references/.ground-index/index.sqlite`.
- `EVAL_REPORT.md`: Comprehensive evaluation report with 3-way comparative confusion matrices and $\Delta$ added-value analysis.

## Running Evaluations

Activate the project virtual environment first:

```bash
source .venv/bin/activate
```

### 1. Run Automated BM25 Retrieval Evaluation (Tier 1)

```bash
python .github/skills/ground-truth-review/eval/eval_retrieval.py --query-mode key_terms
```

Optional flags:
- `--top-k 5`: number of top hits to evaluate (default: 5)
- `--floor 0.0`: score floor threshold (default: 0.0)
- `--query-mode {fts5, raw, key_terms}`: query preprocessing mode
- `--output-json <path>`: save results as structured JSON
- `--verbose`: print detailed per-claim breakdown

### 2. Run Closed-Book LLM Baseline (Baseline 0)

```bash
python .github/skills/ground-truth-review/eval/eval_closed_book.py
```

Optional flags:
- `--mode {simulated, live}`: simulation mode (default, deterministic) or live API
- `--model <name>`: LLM model name for live mode (e.g. `gpt-4o`)
- `--output-json <path>`: save results as JSON
- `--output-report <path>`: save markdown report

### 3. Run Test Suite

```bash
pytest .github/skills/ground-truth-review/scripts/tests/
```
