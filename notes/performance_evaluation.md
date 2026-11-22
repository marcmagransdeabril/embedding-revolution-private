---
title: "Performance evaluation across chapters (scratchpad)"
status: idea
date: 2026-11-17
---

Scratchpad, not part of the book. Benchmark and dataset names are written from memory and none is verified. Every literature number is a placeholder to extract from a PDF in `references/` (page read), never to quote from memory. Chapters are named by their file stem in the roadmap of `index.qmd` (the property chapters, `meaning_as_likeness` first). **Scope: the property chapters**; `symbols_without_interior` and `tests_of_meaning` are theoretical and get no benchmark (author, 2026-11-17). Trimmed on 2026-11-22: the chapter audit, the list of mismatches with the old Chapter 4 and the next steps were written for the technology chapters that are now stubs in `embedding-technologies-stubs/`, and were removed (they are in git, commit before this one).


## 1. The question

The pay-off step (`review-doc` §19) asks about scale, durability, limit and result. A fifth question is missing: **generalization**, the behaviour of a method outside the distribution it was trained on. Train/validation splits and bootstrapping estimate variance inside one distribution only.

Working idea: sample against existing datasets and benchmarks, which already encode shifts chosen by others, through a fixed input-output interface shared by chapters.

## 2. Principles

- Generalization is relative to a declared shift: "generalizes across X, measured on D".
- We cannot reach state of the art (hardware, time). The goal is not a score but a **calibrated position**: what the approach explained in the section scores in the literature, what we score with our smoke test, and what the best known approach scores, side by side.
- Own experiments stay smoke tests (§8, §19.4). They can falsify and illustrate, never rank methods at scale.
- **Each chapter asks one question about meaning, and its benchmark is chosen to answer that question.** The benchmark follows the question; the book's examples are not bent to fit a benchmark. A chapter whose question has no benchmark says so.
- The literature number that matters is **the one for the same approach as the section** (e.g. SVD of PPMI on a word-similarity benchmark), not the state of the art, which is context.

## 3. Per-chapter protocol (a meaning question, the five items, plus one)

For each property chapter, fill this record (the chapter already states its question, judge and null; this is the same record with the literature row added). A chapter with no honest benchmark says so (that is a result).

0. **Meaning question.** One sentence: which kind of meaning does this chapter's structure claim to capture (association, similarity, synonymy, opposition, category, hypernymy, analogy, equivalence of behaviour, ...)? The dataset and benchmark must measure that kind and not a neighbour of it.
1. **Dataset.** Name, size, licence, how to obtain it pinned, what shift it contains (train to test), and what our hardware can run (full, subsample, none).
2. **Benchmark.** Task, metric, official split, who proposed it, year, and which behaviour of the shared interface it measures (B1 classify, B2 retrieve, B3 similarity, B4 relation).
3. **Literature on current benchmark results.** Source (PDF in `references/`, page), state-of-the-art score and date, plus a score for each distinct approach family (below).
4. **Alignment of sections to the benchmark.** For each `##` section: does it present an approach that can be scored on this benchmark; does a script already produce the metric; which script or exercise would. Verdicts: aligned, partly (qualitative output only), not applicable (history, bridge, theory), gap (should have a score and has none).
5. **Reference performance of the section's approach in the literature.** For each aligned section, the score that the literature reports for the same approach (same family, same benchmark, with data scale and date), next to our smoke-test score and the state of the art for context. This is the calibration row: it shows how far our result is from the approach's own published level and why (data size, tuning, training length).
6. **Shift axis.** The test-versus-train difference used for the generalization question, and the gap (in-distribution minus shifted) with an interval.

Row format for item 5 (one line per approach):

| Section | Approach | Our result (data, size, seed interval) | Literature, same approach (source, page, data scale, year) | State of the art (context, year) | Expected effect of scale on our number |
|---|---|---|---|---|---|

## 4. Shared interface

Every method is reduced to: frozen encoder `encode(batch) -> [n, d]`, trained on the source split only (seed and hyperparameters logged), weak fixed probes (cosine kNN, ridge or logistic), metrics with intervals (§8; paired interval for differences), and one output row (method, trained on, tested on, in-distribution score, shifted score, gap). A frozen encoder plus a weak probe measures the representation, not the head.

## 5. What the new structure already covers, and what is carried over

The property chapters state a question, a judge and a null before each experiment, and the scale test of each chapter asks what the literature reports at scale, so §2 and §3 are partly applied by the structure itself. Carried over from the removed chapter audit, as leads and not as facts:

- **One benchmark per kind of meaning**, chosen by the question and not by the example: similarity (SimLex-999; TOEFL synonyms, Landauer and Dumais 1997), relatedness (WordSim-353 relatedness subset, MEN), opposition (antonym discrimination sets), category (BLESS, ESSLLI), hypernymy (BLESS, EVALution), relations and analogy (Google analogy, BATS). Used by `meaning_as_likeness`, `meaning_as_difference` and `meaning_as_direction`; each name is a lead until the PDF is read.
- **Floors**: one-hot vectors score at chance on any similarity benchmark, and raw first-order counts are the "before geometry" row.
- **Coverage**: a small corpus leaves most benchmark pairs outside the vocabulary; report the share of covered pairs and score only those.
- **Seeds**: one rule, a bootstrap interval of the mean over seeds for a claim, the range as an extra; pairs resampled for benchmark scores.
- **Scale**: where a chapter claims that more text or more compute changes a ranking, a curve of the score against corpus size on the same data decides it.
- **Published settings**: the benchmark script uses the published defaults (dimension around 100 to 300, windows of five or more); toy settings stay in the text.
- **Two criteria**: loss (fit to the corpus) and benchmark score (meaning) can rank methods differently; report both and say which question each answers.

## 6. What the reviewer checks (draft §19.5, Generalization)

1. Which shift axis does the claim concern, and does the text name it?
2. Which dataset encodes it, and is the test truly outside the training distribution (shared source, annotators, contamination)?
3. In-distribution score, shifted score, gap, with intervals.
4. Is the ranking against the competing method stable across shifts? Report the worst shift.
5. Parity: same data, compute and tuning. Data can explain more than the objective, so a loss comparison with different data is confounded.
6. Is our number placed against the literature number for the same approach (item 5), with the reason for the difference?
7. "No evidence outside the training distribution" is a valid answer (epistemic boundary with queries).

## 7. Constraints

- Dependencies per `review-code`: standard library, numpy, then pytorch where needed. Probes are numpy.
- Datasets pinned by version and checksum, fetched by a script wired into the `Makefile`, never committed. Stated skip if offline. Where a dataset is too large to keep, the pinned URL and checksum are what the repo holds (author, 2026-11-17).
- Intervals per §8 (resample seeds and test items; paired intervals for differences).
- Shared helpers (probes, metrics, gap table) in one `utils.py` with unit tests.
- Runs of minutes on CPU where possible; larger sets use a declared fixed subsample.

## 8. Risks

- **Probe confound.** A weak probe favours cosine-friendly geometry. Report kNN and linear.
- **Data versus objective.** Match data before comparing objectives.
- **Contamination.** Pretrained encoders may have seen test sets. Prefer encoders trained here, or state it.
- **Toy-scale bias.** Closed-form methods look better at small scale. State the expected direction of scale for each number (§17.6).
- **Table inflation.** Keep one dataset per chapter in the book, the full tables in script output.
- **Metric shopping.** Fix metrics and shift pairs before running (anti-HARKing).
- **Memory-sourced names.** Every benchmark and paper above is a lead, not a fact, until opened and read.

## 9. Decisions and open questions

Decided by the author, 2026-11-17:

- **Results enter the book text**, in each section, after the toy example (any toy example that helps the reader understand the results). This departs from §19, which says the pay-off step adds no text to the book, so §19 and §17 need a matching note once the plan is applied.
- **Which sections show results.** Each section that presents a new method toward the chapter's meaning question shows its benchmark result, next to the benchmark result of the same method at state-of-the-art computing and implementation (the calibration row, item 5), so the reader sees the distance between the toy, our smoke test and the published level. Sections that present no method (history, bridge, theory) show none.
- **Data too big to keep** is not committed; the pinned URL and checksum are kept (Constraints, section 7 of this note).
- **Touching the repo** (downloads, scripts, chapter edits) waits until the plan is applied.

Still open:

- Shared `generalization/` package or per-chapter scripts?
- For chapters about symmetry, topology and logic, is the equivalent an invariance or capacity test rather than a shift test?
- How to present the gap across chapters without implying a ranking at scale?
