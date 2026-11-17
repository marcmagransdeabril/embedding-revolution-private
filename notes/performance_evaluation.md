---
title: "Performance evaluation across chapters (scratchpad)"
status: idea
date: 2026-11-17
---

Scratchpad, not part of the book. Benchmark and dataset names are written from memory and none is verified. Every literature number is a placeholder to extract from a PDF in `references/` (page read), never to quote from memory. Chapter numbers follow the roadmap in `index.qmd` (4 = Embedding Spaces ... 15 = Multimodal). **Scope starts at Chapter 4** (author, 2026-11-17): Chapter 3 is theoretical and gets no benchmark.

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

For each chapter from 4 on, fill this record. A chapter with no honest benchmark says so (that is a result).

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

## 5. Chapter audit (first draft)

Status of checking: I read the section headings of every chapter file and the script names referenced by Chapter 4. I did not read all section texts, run any script, or open any reference PDF for this note. The "alignment" lines for chapters 5 to 15 judge plans (stubs of 374 to 1,325 words, status `idea`), not written prose.

### Chapter 3: Symbols Without Interior (definitive): out of scope

Theoretical chapter (Shannon, Chomsky, one-hot tables, Rice), so it gets no benchmark of its own. Its scripts stay as they are. Two things carry over to Chapter 4 as reference rows, with nothing added to Chapter 3:

- **One-hot floor.** One-hot vectors score at chance on any similarity benchmark (all pairs equidistant), so they are the bottom row of the Chapter 4 table.
- **First-order counts.** Raw co-occurrence tables with no vectors are the "before geometry" row. Whether they score on association and fail on similarity is a Chapter 4 result, to be checked and not assumed.

### Chapter 4: The Anatomy of Embedding Spaces (definitive, 23,772 words; by section only the first three are definitive)

Section tags in the file (checked 2026-11-17): definitive are Counting Company, From Counting to Geometry and Learning by Prediction; provisional are Learning by Contrast: Words, Encoder/Decoder and the Chain Rule, Learning by Contrast: Anything, Learning by Predicting Embeddings, The Geometry of Meaning, Where a Single Vector Strains and A Space That Cannot Yet Say No; idea is Learning by Reconstruction. Prototype the benchmark on the three definitive sections first; the others follow as they are tagged up.

Sections: Counting Company; From Counting to Geometry; Learning by Prediction; Learning by Contrast: Words; Encoder/Decoder and the Chain Rule; Learning by Contrast: Anything; Learning by Predicting Embeddings; Learning by Reconstruction; The Geometry of Meaning; Where a Single Vector Strains; A Space That Cannot Yet Say No.

Meaning question: *are two things alike, and in what way?* The chapter's own text already separates the ways (substitutes versus associates, `sister`/`mother` versus `london`/`bed`, role versus synonymy for `darcy`), so the benchmark should too. One corpus, one set of vectors, scored on several kinds of meaning:

| Meaning kind | Benchmark candidate (to verify) | Why it is in |
|---|---|---|
| Similarity (substitutable) | SimLex-999; TOEFL synonym questions (Landauer and Dumais 1997, an SVD on counts; classic, check it is in `references/`) | The core claim of counting and SVD |
| Relatedness (association) | WordSim-353 relatedness subset, MEN | The part the chapter says vectors inherit |
| Opposition (antonyms) | Antonym-versus-synonym discrimination sets, antonym questions | Distributional vectors place opposites near each other; this is the chapter's closing limit ("A Space That Cannot Yet Say No") and already visible in the toy corpus (`dawn`–`dusk`) |
| Category | BLESS, ESSLLI or AP concept categorization | Whether neighbours share a class |
| Hypernymy | BLESS, EVALution | Vectors give symmetric similarity, hypernymy is asymmetric ("Where a Single Vector Strains") |
| Relations and analogy | Google analogy, BATS (whose categories include inflection, derivation, lexicographic and encyclopedic) | The parallelogram claim in "The Geometry of Meaning" |

The digits thread is a different kind of meaning (same digit, a category over images), with its own benchmark (see inconsistency 3).

Item 5: for each family, the literature score on the same benchmark: PPMI+SVD and tuned count models (Levy et al. 2015, cited in the chapter), SGNS and CBOW (Mikolov 2013), GloVe (Pennington 2014); LSA on TOEFL (Landauer and Dumais). Extract score, corpus size and hyperparameters, and read how scores move with corpus size, since the chapter claims "the lists should improve with more text" (line 229) and that prediction won on computation and not on geometry (line 358). Both claims become testable.

### Chapters 5 and 6: Generative spaces, Contextual vectors (idea, stubs)

- **Chapter 5.** Dataset: MNIST for VAE, diffusion and autoregressive models. Benchmark: held-out log-likelihood or bits per dimension, sample quality, and linear-probe accuracy of the latent. Literature: VAE and diffusion results on MNIST and CIFAR-10 (to extract). Alignment: stub; one mechanism per section is possible on digits. Closing section ("plausible is not true") has no benchmark and may need a factuality benchmark (e.g. TruthfulQA, to verify).
- **Chapter 6.** Dataset: Penn Treebank for the parse-tree question. Benchmark: structural probe (UUAS, Hewitt and Manning 2019, to verify), SAE reconstruction and interpretability metrics. Literature: BERT probe scores. Alignment: "Is the Tree in the Geometry?" aligned; "Do different models share a geometry?" needs a similarity measure across models (CKA or similar, to verify). Hardware: a small pretrained BERT on CPU is feasible for probing; training is not.

### Chapters 7 to 15: Part II (idea, stubs)

| Ch | Home dataset | Benchmark | Literature for the approach | Alignment (plan) | Shift axis |
|---|---|---|---|---|---|
| 7 Vector databases | BEIR subset (to verify) | recall@k vs latency (ANN-Benchmarks); nDCG@10 | HNSW, product quantization; single-vector limits (a recent theoretical-limits paper, to verify) | Exact vs approximate is directly measurable; the dot-product limit needs a synthetic top-k test | zero-shot corpora |
| 8 Tangent spaces, geodesics | rotated and corrupted digits; WordNet nouns | accuracy under transformation; hyperbolic vs Euclidean reconstruction (Poincaré embeddings, Nickel and Kiela 2017, to verify) | same | "The Shape of a Tree" aligned; Lie-group section is theory | unseen subtrees; unseen rotations |
| 9 Graph embeddings | FB15k-237, WN18RR | MRR and Hits@10 (TransE, ComplEx, RotatE, to verify) | the sequence of models in the section is the benchmark's own history | strongly aligned; the chapter's "each model fixes a pattern" claim is testable per relation pattern | unseen entities |
| 10 Topological deep learning | TUDataset or OGB graph classification | accuracy; persistent-homology features vs plain features | to find | weak; persistent homology tests the manifold hypothesis, hard to score | structural (scaffold) |
| 11 Complex plane, quantum logic | KG sets (shared with 9); quantum-cognition order-effect data | complex vs real of equal size; fit to order effects | to find | the chapter is already conditional ("kept only if complex vectors beat real ones of the same size"), so the benchmark is its removal test | none natural |
| 12 VSA | HD classification sets (e.g. ISOLET, UCI HAR, to verify); synthetic capacity tests | accuracy and capacity vs dimension | HD computing classification papers (to find) | capacity bounds are checkable synthetically with no download | noise and dimension |
| 13 Neuro-symbolic | SCAN, COGS, CLEVR-CoGenT; RuleTaker or ProofWriter | held-out-combination accuracy | the systematicity literature (Fodor and Pylyshyn is in the roadmap; benchmark papers to find) | aligned (systematicity is a shift) | compositional |
| 14 Cross-domain transfer | MUSE bilingual lexicon (to verify); Mikolov 2013 translation matrix (not in `references/`, which holds three other Mikolov 2013 papers) | precision@1 of lexicon induction; Office-31 style domain adaptation (to verify) | to extract | Procrustes alignment is aligned and cheap | cross-lingual |
| 15 Multimodal | COCO or Flickr30k; digits and their names (existing toy) | retrieval recall@k; zero-shot ImageNet (to verify) | CLIP and successors; modality gap papers (to find) | the digit-name toy is a smoke test; scale needed for the rest | modality and style |

For each row, fill items 1 to 6 when the chapter is written. A stub gets only the plan.

## 6. Inconsistencies between current examples and the proposed baseline, and how to fix them

Found by reading the section headings, the exercise texts and the scripts' names, plus the lines cited. I have not run the scripts, and I have not read all of Chapter 4. These are mismatches with a proposed benchmark that does not exist yet, not defects of the chapter. Mismatch per item: *conflict* (the example and the benchmark disagree), *gap* (the example does not reach the benchmark) or *convention* (a reporting rule differs). Item 6 is confirmed (2026-11-17): `@tbl-learned-cosines` gives [minimum, maximum] over five starting points and `@tbl-learned-loss` a range over the runs, while the figures and the digits tables use a 95% bootstrap interval.

| # | Mismatch with the proposed benchmark | Kind | Short fix | Cost |
|---|---|---|---|---|
| 1 | The toy corpus (13 sentences, themes sky and court, nonsense `xqzv`) has words absent from every standard word list, so no benchmark can score it | gap | Keep it as the mechanism demo and say so; add one bridge paragraph or exercise running the same pipeline on a real corpus scored on SimLex | low |
| 2 | *Pride and Prejudice* (about 128,000 words, 2,000 words kept) is a single novel; benchmark pairs are largely uncovered and the lists are biased (`bennet` as a sister, `mr`, `he`, `she` as neighbours of `darcy`) | conflict | Add one larger corpus (text8 or similar) beside it for scoring; report coverage (share of benchmark pairs inside the vocabulary) and score only the covered pairs | medium (download, memory for the SVD of a larger matrix) |
| 3 | The digits thread (8×8, 1,797 images; autoencoder, InfoNCE, JEPA) is the same pipeline on a different kind of meaning (same digit), and chapter-level word benchmarks do not apply | conflict | State two meaning questions in the chapter: words (similarity) and images (category). Score digits with kNN and linear probe accuracy, shift to MNIST or USPS downsampled to 8×8 (resolution mismatch must be stated) | medium |
| 4 | Chapter 4 compares methods on the toy corpus by loss versus the conditional entropy $H(C \mid W)$ (floor 1.8507 bits) and by cosines, while the benchmark compares by Spearman or accuracy; the two criteria can rank methods differently | convention | Report both and say which question each answers; the loss is about fitting the corpus, the benchmark about meaning. The text already says error is not quality (line 239) | low |
| 5 | The toy corpus shows `dawn`–`dusk` at cosine 1.00 for SVD and $-0.45$ for the predictor, i.e. an antonym-like pair that counting merges. A benchmark on opposition would test this, but the toy example is chosen as a clean demonstration, not as a benchmark | gap, and an opportunity | Use it as the bridge into the antonym benchmark: toy mechanism, then the real test. Do not change the toy | low |
| 6 | Seed variability is shown as the range over five runs in some tables (`@tbl-learned-cosines`, `@tbl-learned-loss`), while §8 says a min-max range is not a confidence interval and the figure on contrast already uses a 95% bootstrap interval of the mean over five seeds | convention | Apply one rule: bootstrap interval of the mean over seeds for the claims, range as an extra. Add pair-level resampling for benchmark scores (the pair list is the finite test set) | low |
| 7 | Chapter 4 is organized by learning method (count, predict, contrast, reconstruct), the benchmark by kind of meaning | conflict of axes | Produce a matrix, method by meaning kind, as script output; the chapter text keeps its method order and quotes only the cells it argues from | medium |
| 8 | The text promises improvement with more text (line 229) and that prediction won on computation, not geometry (line 358); both are untested claims at our scale | gap (§17 calibration) | Add a corpus-size curve (benchmark score against number of tokens) for count and predict families on the same data. The curve decides whether the claims stay as written | medium |
| 9 | Hyperparameters in the chapter ($d$ from 2 to 12, window of one or two words) are tuned for clarity, while published benchmark scores use $d$ around 100 to 300 and windows of five or more | convention | In the benchmark script use the published defaults and say so; the toy values stay in the text | low |
| 10 | Chapters 5 to 15 are stubs whose planned examples are not yet fixed | not yet a conflict | Write the meaning question and the benchmark in each stub before the examples, so the examples are chosen to feed it | low |

### Order of fixes (short plan)

1. Decide the open question on results in the book text, and the scope (Chapter 4 first). Without these, nothing below lands in the right place.
2. Write the meaning question and the benchmark for Chapter 4 in the chapter front matter or a notes file. No prose changes yet.
3. Build the shared scoring script (inconsistencies 4, 6, 7, 9) and run it on the existing book vectors and on one larger corpus (2).
4. Run the digits probe with the MNIST/USPS shift (3).
5. Review the results against the text, then decide, item by item, which claims need a hedge or an added sentence (8, 5, 1). Changes to the chapters go through the author (change policy).
6. For stubs, add the meaning question and the benchmark to the plan text as each chapter is taken up (10).

## 7. What the reviewer checks (draft §19.5, Generalization)

1. Which shift axis does the claim concern, and does the text name it?
2. Which dataset encodes it, and is the test truly outside the training distribution (shared source, annotators, contamination)?
3. In-distribution score, shifted score, gap, with intervals.
4. Is the ranking against the competing method stable across shifts? Report the worst shift.
5. Parity: same data, compute and tuning. Data can explain more than the objective, so a loss comparison with different data is confounded.
6. Is our number placed against the literature number for the same approach (item 5), with the reason for the difference?
7. "No evidence outside the training distribution" is a valid answer (epistemic boundary with queries).

## 8. Constraints

- Dependencies per `review-code`: standard library, numpy, then pytorch where needed. Probes are numpy.
- Datasets pinned by version and checksum, fetched by a script wired into the `Makefile`, never committed. Stated skip if offline. Where a dataset is too large to keep, the pinned URL and checksum are what the repo holds (author, 2026-11-17).
- Intervals per §8 (resample seeds and test items; paired intervals for differences).
- Shared helpers (probes, metrics, gap table) in one `utils.py` with unit tests.
- Runs of minutes on CPU where possible; larger sets use a declared fixed subsample.

## 9. Risks

- **Probe confound.** A weak probe favours cosine-friendly geometry. Report kNN and linear.
- **Data versus objective.** Match data before comparing objectives.
- **Contamination.** Pretrained encoders may have seen test sets. Prefer encoders trained here, or state it.
- **Toy-scale bias.** Closed-form methods look better at small scale. State the expected direction of scale for each number (§17.6).
- **Table inflation.** Keep one dataset per chapter in the book, the full tables in script output.
- **Metric shopping.** Fix metrics and shift pairs before running (anti-HARKing).
- **Memory-sourced names.** Every benchmark and paper above is a lead, not a fact, until opened and read.

## 10. Decisions and open questions

Decided by the author, 2026-11-17:

- **Results enter the book text**, in each section, after the toy example (any toy example that helps the reader understand the results). This departs from §19, which says the pay-off step adds no text to the book, so §19 and §17 need a matching note once the plan is applied.
- **Which sections show results.** Each section that presents a new method toward the chapter's meaning question shows its benchmark result, next to the benchmark result of the same method at state-of-the-art computing and implementation (the calibration row, item 5), so the reader sees the distance between the toy, our smoke test and the published level. Sections that present no method (history, bridge, theory) show none.
- **Data too big to keep** is not committed; the pinned URL and checksum are kept (Constraints, section 8 of this note).
- **Touching the repo** (downloads, scripts, chapter edits) waits until the plan is applied.

Still open:

- Shared `generalization/` package or per-chapter scripts?
- For chapters about symmetry, topology and logic, is the equivalent an invariance or capacity test rather than a shift test?
- How to present the gap across chapters without implying a ranking at scale?

## 11. Next steps (proposal)

1. Verify the benchmark and paper leads for Chapter 4 (open the PDFs in `references/`, download missing ones with `ground-truth-review`), and fill items 2, 3 and 5 for it first. State on 2026-11-17:
   - Papers downloaded and checked against their titles: SimLex-999 (`hill2015simlex`), Agirre et al. 2009 on the similarity and relatedness subsets of WordSim-353 (`agirre2009study`), BLESS (`baroni2011how`) and BATS (`gladkova2016analogy`). To add by hand (publisher sites block scripts): Landauer and Dumais 1997 (`landauer1997solution`), MEN (Bruni et al. 2014), the original WordSim-353 paper (Finkelstein et al. 2002) and Rubenstein and Goodenough 1965. None of the downloaded papers has been read beyond the abstracts and the pages quoted in `ideas.qmd`, idea 18.
   - Data: SimLex-999, WordSim-353, MEN, BLESS, BATS, text8. Record each URL, version and checksum in the fetch script; datasets that are large are not committed (Constraints, section 8 of this note).
2. Prototype chapter 4 words: SimLex-999 and analogy scores for SVD-PPMI and SGNS on Pride and Prejudice and on text8, next to the one-hot floor (chance) and first-order counts.
3. Prototype chapter 4 digits: kNN and linear probe accuracy of AE, contrastive and PCA codes on digits, then MNIST and USPS as the shift.
4. Draft §19.5 in `review-doc` and the calibration line in §17, after the decision on results in the book text.
