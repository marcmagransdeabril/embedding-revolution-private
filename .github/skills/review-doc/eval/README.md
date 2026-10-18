# Review Skill Benchmark Suite & Evaluation Harness

This directory contains the standardized, reproducible Golden Review Benchmark Suite and automated evaluation harness for measuring empirical reviewer performance, defect recall ($R$), precision ($P$), harmonic $F_1$, critical blocker recall ($R_{\text{crit}}$), token footprint ($L_{\text{skill}}$), and Review Yield per Token ($\text{Yield}_{\text{review}}$).

## Directory Layout
- `benchmark_cases.jsonl`: Curated $N=25$ test cases across 6 defect categories with ground-truth annotations and 10 paired verbosity variants.
- `eval_review_skill.py`: Benchmark evaluation runner and metric calculation engine.
- `baselines/b0_minimal_prompt.md`: Minimal 300-token prompt baseline ($B_0$).

## Benchmark Taxonomies (25 Cases)

| Category | Cases | Description & Injected Flaws |
|---|---|---|
| **A. Statistical & Mathematical** | 6 (`stat-001`–`006`) | Inconsistent $p$-values vs $t/F/df$, impossible discrete Likert means (GRIM test violations), uncorrected multiple testing, CI non-overlap contradictions. |
| **B. Methodological & Confounds** | 5 (`method-001`–`005`) | Uncontrolled reasoning token / compute budgets, asymmetric prompt optimization, HARKing, test set contamination, missing ablations. |
| **C. Evaluator & LLM Biases** | 5 (`bias-001`–`005`) | Un-counterbalanced LLM judge order (position bias), verbosity/length confounds, collinear multi-attribute halo effects, self-enhancement bias. |
| **D. Prior Art & Retrieval** | 4 (`prior-001`–`004`) | Presenting known commercial/patented technologies (GaN RF heating, ultrasonic thawing) or established literature (TPR, LTN) as novel inventions without prior-art attribution. |
| **E. Metric Alignment (Tail vs Mean)** | 3 (`metric-001`–`003`) | Central averages masking extreme top-tail yield differences in ideation/generation, inverted pass@1 vs pass@$k$ under budget, tail latency spikes. |
| **F. LaTeX, Floats & Formatting** | 2 (`format-001`–`002`) | Unresolved references (`??`), broken floats, missing captions, overfull `\hbox`. |

## Metrics & Yield Definitions
1. **Defect Recall ($R$)**: $TP / (TP + FN)$
2. **Defect Precision ($P$)**: $TP / (TP + FP)$
3. **Harmonic Quality Score ($F_1$)**: $2 \cdot \frac{P \cdot R}{P + R}$
4. **Critical Blocker Recall ($R_{\text{crit}}$)**: Recall restricted to fatal methodological flaws and statistical errors.
5. **Skill Token Footprint ($L_{\text{skill}}$)**: Token count using `cl100k_base`.
6. **Review Yield per 1,000 Tokens ($\text{Yield}_{\text{review}}$)**:
   $$\text{Yield}_{\text{review}} = \frac{\text{True Defects Identified}}{\text{Total Review Tokens (Input + Output)}} \times 10^3$$
7. **Length-Invariance Gap**: $(R_{\text{concise}} - R_{\text{verbose}})$ measured across the 10 paired concise vs. $3\times$ verbose variants.

## Running the Benchmark
```bash
python3 .github/skills/review/eval/eval_review_skill.py --output-json tmp/review_skill_baseline_calibration.json
```
