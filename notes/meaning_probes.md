---
title: "Meaning probes: definitions and gate rule (scratchpad)"
status: idea
date: 2026-11
---

Scratchpad, not part of the book. Written before any example is produced (plan C1, B8). Every literature claim below is a lead until a page is read in `references/` (`ground-truth-review`).

## 1. Definitions

Scope: only what the first section (nearness) needs. Extend when a later section forces it.

### Property
A claim about the geometry of a space, stated in plain words, and made testable by three things fixed before looking (plan A3):
- a **statistic** computed on the vectors (for example, the mean cosine between distinct vectors; the accuracy of an offset);
- a **null**: the same statistic on a space without the property (random Gaussian vectors, random directions, shuffled pairs, the same space centred). Every cosine is read against a null, because a common direction shared by all vectors makes raw cosines look meaningful;
- a **threshold**: the size of the gap to the null that counts, written down with its date before the numbers exist.

Each cell *property x model* is also classified as **built in** (the training objective optimises it; finding it proves nothing about meaning), **emergent** (it appears where it was not optimised for) or **absent** (plan A1). Only emergent cells support the book.

### Probe
A function from the frozen representation to an answer that a human, a dataset or a checker can judge, with a metric, a baseline and a stated shift (plan B4). One probe = one script = one number printed by `make`. A probe measures a property; the property is what we claim, the probe is what we ran.

### Rung
A step on the ladder of a test of meaning (dog, critical literacy, translator, alien). A probe sits on one rung. A section takes the highest rung it can honestly reach, or says "not applicable" (plan B2). Rungs are reported as a profile, never averaged (plan B9).

### Verdicts
One per cell *property x test x model family*, with **date**, **kind** and **family**:
- *kind*: derivation (lasts as long as its assumptions), measurement on a model family (a record of that family at that date), benchmark verdict (depends on the benchmark and its version);
- *supported*: the statistic beats the null by the threshold, the cell is emergent, and the sceptics' objections do not apply to this probe;
- *qualified*: supported only under a stated condition (centred space, one family, relation type, query words excluded);
- *contested*: the same property is supported by one probe or family and refuted by another, or a sceptic's result applies and is not answered;
- *untested*: no probe has been run. This is a legitimate verdict and is written explicitly.
A verdict is rerun when a newer model replaces the pinned one; the change is the shelf life of the property.

## 2. Gate rule (Phase 3, G1)

FROZEN 2026-11 (author's decision 1). Edit only with the reason and the date recorded here.

Decision 1 (author): a negative result is acceptable. If a property turns up only in some families, or only where the loss builds it in, the most likely reading is a side effect of the experiment and of the different loss functions, and the book says so. A property that is built in is still a necessary building block: obvious, but good to know. So no outcome stops the book, and the outcomes below only decide how the chapter and the Prologue frame the result.

Counting rules:
- A cell is classified built in, emergent or absent (section 1). Built-in cells are reported and explained by the loss that builds them; they are building blocks, not findings, and they do not count towards "consistent".
- An emergent cell counts if its statistic is outside the 99th percentile of the null (1000 draws, fixed seeds), with the effect size printed.
- A property is **consistent** if it counts in at least 3 model families (for example count-based, prediction-based, contrastive text, image-text). Families that share training data are listed and a limit is stated: this is not independence (plan section 4).
- A cell with a Mode B figure only (no computation) is *untested*, not a zero.

Outcomes (framing, not stopping):
- **Go:** at least 3 properties are consistent, and at least one is difference or direction. The book argues that these are what meaning acquires as geometry, and each later chapter extends or breaks one.
- **Reframe:** properties hold only within families, or are built in by the loss (for example nearness everywhere because every loss optimises it; difference and direction objective-dependent). The book becomes a map: which structure, through which loss, gives which property, at which cost. This is already the Prologue's working frame.
- **Reconsider the title:** at most nearness holds and it is built in. The chapter then says that "meaning as geometry" is a design choice at this level, and the "revolution" OPEN comment of `index.qmd` is revisited. The book continues; only its claim is weakened.

For every built-in or absent cell the section names the loss function that explains it (similarity-trained, reconstruction, prediction, contrast), because that explanation is the result.

## 2b. Models (Mode A), pinned when first used

The model list is organised by **level** (word, token in context, phrase, sentence and paragraph, image, sound, and pairs) and by **loss**, because the loss decides what "near" means. The table is in 3.1. Nothing is downloaded until the author approves the list; version, licence and SHA-256 are recorded by the script's first run and then checked on every run (`utils.verify_sha256`).

Code lives in `code/properties_of_meaning/` (`utils.py` with tests in `.github/skills/review-code/scripts/tests/test_properties_utils.py`). Scripts there are picked up by `make test-code` automatically.

## 3. Properties (one at a time)

For each: claim, statistic, null, threshold, probe, models, sceptics, evidence in favour across algorithms, verdict (with date, kind, family).

### 3.1 Nearness is likeness
Status 2026-11: claim, levels, models, losses, statistics, null and threshold written; sources read at page level (below); no number exists yet; verdict *untested*.

Claim (plain words). Things that mean alike sit close together; things that mean differently sit far apart.

**The claim has one reading per level, and the loss chooses it.** "Alike" is not one relation. Each training objective fixes what it is rewarding, so the nearness it builds in is that relation and no other. The section therefore reports nearness per level and per loss, and the question for each cell is: what does the loss make near, and does that agree with likeness of meaning as a human or a benchmark judges it?

| Level | Candidate model (to approve) | Loss, in one line | What is near by construction | Probe (rung 0 of the dog test, plus a benchmark) | Source status |
|---|---|---|---|---|---|
| L0 word, static | LSA / SVD of PPMI (own, on the pinned text of `embedding_spaces`) | reconstruct a count matrix: rank-k least squares (Deerwester 1990, p. 5) | words whose count profiles over contexts are alike | neighbours of "dog"; SimLex-999, relatedness set | held |
| L0 word, static | word2vec skip-gram with negative sampling | predict context words from the word, with sampled negatives (Mikolov 2013, p. 1); implicitly a factorisation of a shifted PMI matrix (Levy & Goldberg 2014, p. 1) | words that occur in the same contexts | same | held |
| L0 word, static | GloVe | weighted least squares on the log of the co-occurrence counts (Pennington 2014, p. 1) | words with alike co-occurrence ratios | same | held |
| L0 word, subword | fastText | skip-gram over character n-grams | as above, plus words sharing spelling | same | to fetch |
| L1 token in context | BERT or GPT-2 hidden states | masked-word or next-word prediction | same word in similar contexts, anisotropic (Ethayarajh 2019, p. 4) | similarity of one word in two contexts ("bank") | BERT to fetch; Ethayarajh held |
| L2 phrase, chunk | average or sum of word vectors, and a sentence encoder on short spans | none for composition (average); contrastive for the encoder | words in the span, not their order (average); paraphrase (encoder) | phrase similarity set (to choose) | to choose, to fetch |
| L3 sentence, paragraph | contrastive sentence encoder (SBERT or SimCSE type) | contrast: pull paired sentences (paraphrase or entailment, or two dropout views) together, push others apart | sentences that were paired as alike | STS benchmark; negation and planted-contradiction examples (Prologue, critical literacy test) | to fetch |
| L4 image | self-supervised or supervised vision encoder | classification or augmentation-invariance | images with the same label or the same content under augmentation | image neighbours of a dog photograph | to choose |
| L5 sound | audio-text contrastive model (CLAP or BioLingual type; NatureLM-audio is held) | contrast between a clip and its caption | clips whose captions are alike | audio-to-audio and audio-to-text neighbours of a bark | NatureLM-audio held; encoder to choose |
| L6 pairs | CLIP | symmetric cross entropy over the cosine similarities of image and text in a batch (Radford 2021, p. 4 and p. 6) | an image and its own caption; nothing is said about two images or two texts | image-text retrieval; the modality gap (section 7) | held |

Combinations (image with text, sound with text) change the question: nearness is then *between* modalities and is built in only for pairs that were seen together. Whether a text and an image of a dog that were never paired sit near each other is emergent, and belongs to section 7.

The three static-word rows are the same level with three losses on the same data: this is the cleanest cell for the question "does nearness survive a change of loss?". The remaining rows are different levels with different losses, so a difference between them is not a change of loss alone (data and level change too); the note says so and does not rank them.

How the loss can bend nearness away from likeness of meaning (what the sources show):
- *The loss rewards co-occurrence, which is not similarity.* WordSim-353 raters were asked for association, not similarity; coffee and cup are rated more similar than car and train, which is what a co-occurrence loss produces (Hill 2015, p. 1; Faruqui 2016, p. 2). SimLex-999 asks for similarity only. Hill et al. report an inter-annotator agreement of rho = 0.67 for SimLex-999, and 0.611 for WS-353 (pp. 6 and 11-12 of the PDF); a model's rho is read against that ceiling. Faruqui et al. note it is not clear which of the two a word-vector model should be expected to capture (p. 2).
- *A common component dominates raw cosine.* Mu and Viswanath, p. 3, Table 1: vectors are not zero-mean; the norm of the mean is 0.69, 3.15, 0.70, 0.29 and 1.25 against average vector norms of 2.04, 8.30, 2.27, 1.14 and 2.32 (word2vec, GloVe, Rand-Walk, CBOW, Skip-gram). Removing the mean and the top d/100 directions improved similarity by 1.7% on average over seven datasets (p. 2).
- *Frequency leaks into cosine.* Schnabel 2015, PDF p. 8: a linear classifier predicts from the vector whether a word is frequent or rare (GloVe and TSCCA near 100% up to threshold 1000), and the rank of a neighbour follows a power law of its corpus frequency rank (shown for C&W); the authors write that cosine gets polluted by frequency effects. GloVe and CBOW differ widely in how much frequency they encode, so the effect depends on the loss, not on language (p. 8).
- *The loss may not pin the cosine down.* Steck 2024, p. 3: for the regularised linear model whose penalty is on the product of the two factor matrices (objective 1), any rescaling of the latent dimensions gives another solution with the same predictions and different cosines, while the dot products are unique; for the objective that penalises each factor separately (objective 2) the cosines are not changed by the rescaling. The paper's closing caution for deep models is a discussion, not a proof (abstract and p. 1).
- *Contextual models are anisotropic.* Ethayarajh 2019, pp. 1 and 4: no layer of BERT, ELMo or GPT-2 is isotropic; in GPT-2's last layer any two words have on average an almost perfect cosine; in layers 2 to 8 about 0.6. A raw cosine in these layers needs the anisotropy baseline.
- *Design choices matter as much as the algorithm.* Levy 2015 (abstract-level, page to read): much of the gain attributed to neural embeddings came from hyperparameters. This supports comparing the three L0 losses on the same data.

Read at page level in this round: Hill 2015 (pp. 1, 6, 11-12), Faruqui 2016 (p. 2), Steck 2024 (pp. 1, 3), Ethayarajh 2019 (pp. 1, 2, 4), Mu 2018 (pp. 2-3), Schnabel 2015 (p. 8). Still abstract-level: Levy 2015. Loss descriptions of Deerwester, Mikolov, Levy & Goldberg, Pennington and Radford are from the pages cited, first lines only; the full formulas are read when each model is built.

Operationalisation.
- Statistic S1 (anisotropy): `utils.mean_cosine(X)`, the mean cosine between distinct vectors of a model's vocabulary sample. Null: Gaussian random vectors of the same size (about 0). Reported raw and after `utils.center`. Ethayarajh uses the same baseline (average cosine between randomly sampled words, p. 4).
- Statistic S2 (likeness), per level: Spearman rho between the cosine of a pair and a human rating. L0: SimLex-999 and a relatedness set (WordSim-353 relatedness subset or MEN), side by side. L3: the STS benchmark. L2, L4 to L6: a benchmark to choose; if there is none, the rung is an example with a printed table and the cell is *untested* by number. Null: the same correlation with random vectors, and with the vectors centred. The ceiling (inter-annotator rho) is printed beside the score.
- Statistic S3 (frequency leak), L0 only: Spearman correlation between the cosine to a fixed query and the log corpus frequency of the neighbour, over the neighbours of a sample of queries. Null: random vectors (about 0). The same analysis for other levels is not defined and is not attempted.
- Threshold (fixed 2026-11, before any number): S2 counts as "nearness holds" if rho is above the 99th percentile of 1000 random-vector draws and is at least 0.3 (a floor chosen by the author of the note, not taken from the literature; to be confirmed). Centring is reported, not required. S1 and S3 are diagnostics: they set the verdict to *qualified* when centring changes rho by more than 0.02 or |S3| exceeds 0.2.
- Classification per cell: built in (the loss rewards the very relation the benchmark measures), partly built in (it rewards a neighbouring relation, for example co-occurrence for similarity), emergent (the pair was never trained together, for example two images in CLIP). The explanation of each cell names the loss.
- Mode B figure: a distance matrix of a handful of words; a cone of vectors with a large common mean, drawn with and without centring. Math property: the metric axioms for the cosine distance (not the cosine itself), and the failure of symmetry and the triangle inequality in human judgements (Tversky 1977, cited in the chapter).
- Open before the script: approve the model list above (author), pin vectors and benchmark files (SHA-256), decide the size of the vocabulary sample for S1 and S3.

### 3.2 Difference is a relation
TODO
### 3.3 A direction is a meaning you can move along
TODO
### 3.4 Meaning can be a region
TODO. Sceptics: none found yet.
### 3.5 Meaning can move: paths
TODO. Sceptics: none found yet.
### 3.6 Meanings combine
TODO
### 3.7 Many senses, one space
TODO
### 3.8 What is real is the arrangement
TODO
### 3.9 Meaning survives symmetries
TODO. Sceptics: none found yet.

### 3.1c Comparing two spaces: a geometry ladder (leads, 2026-11)

Context: section "Many Runs, Many Spaces" of `chapters/likeness_as_nearness.qmd`. The claim to test is **geometric**, not topological (author): what should survive a change of seed, algorithm or data is the local metric structure, who is near whom and by how much relative to the neighbours. Topology is the weaker invariant: a homeomorphism may reorder neighbours at any finite scale, so agreement of topology does not say that nearness agrees. Topological tools are kept as a diagnostic of the global side.

Ladder, from weakest to strongest (each rung asks more than the one before; the null is the same statistic between two seeds, plan "Many Runs, Many Spaces"):
- G1, neighbour ranks. Whether the k nearest neighbours of a point in one space are the neighbours in the other: trustworthiness and continuity (Venna and Kaski), the co-ranking matrix with neighbourhood intrusions and extrusions (Lee and Verleysen, "quality assessment of nonlinear dimensionality reduction based on K-ary neighborhoods"). Rank-based, local, invariant to any monotone rescaling of each space.
- G2, local relative distances. Rank correlation of the distances inside each point's neighbourhood, after normalising by the point's own nearest-neighbour distance (the local scaling that UMAP uses, to be read). This is the "local relative distances" of the author.
- G3, global metric. Departure from isometry between the two metric spaces without any coordinates: the Gromov-Wasserstein distance (Memoli 2011), plus Procrustes and CKA (Kornblith 2019, held). Needs the absolute distances.
- G4, diagnostic only. Order-based topology: clique topology (Giusti et al. 2015), which depends only on the ordering of the entries of a matrix and is invariant to nonlinear monotone transformations; and Representation Topology Divergence (Barannikov et al. 2022), the multi-scale topological dissimilarity of two point clouds with a one-to-one correspondence, which may lie in different ambient spaces. They say whether loops and voids agree, not whether nearness agrees.

Reading of the result: agreement at G1 and G2 with disagreement at G3 is the "locally similar, globally different" case (same charts, different gluing, or only that local neighbourhoods are easy to match); G4 is what could tell which. Without G4, the note does not claim to separate the two.

Provenance. Found by web search, title and abstract level only; not downloaded, not read at page level, not in `references/` or `references.bib`:
- Giusti, Pastalkova, Curto, Itskov, "Clique topology reveals intrinsic geometric structure in neural correlations", PNAS 112(44), 2015 (arXiv 1502.06172). Abstract: features invariant under nonlinear monotone transformations, depending only on the relative ordering of matrix entries.
- Barannikov et al., "Representation Topology Divergence: a Method for Comparing Neural Network Representations" (arXiv 2201.00058). Abstract: multi-scale topology dissimilarity between two point clouds of equal size with a one-to-one correspondence, possibly in different ambient spaces. A 2026 follow-up (arXiv 2606.06342) criticises RTD for asymmetry and for scores that depend on sample size; to be read before RTD is used.
- Memoli, "Gromov-Wasserstein distances and the metric approach to object matching", Found. Comput. Math. 2011. Abstract: objects as metric measure spaces, a distance based on mass transportation.
- Venna and Kaski (trustworthiness and continuity) and Lee and Verleysen (co-ranking matrix, K-ary neighbourhoods), found as titles and abstracts; the exact references are to be fixed when downloaded.
Not yet searched: the stability of persistence diagrams (bottleneck distance bounded by the Gromov-Hausdorff distance), which I cited from memory in the discussion and which must be read before it enters the text.
Next: download these into `references/`, add them to `references.bib`, read the pages that define each statistic, and write each rung's statistic, null and threshold as for 3.1.

## 4. Reading

- Schnabel 2015 (`references/2015_schnabel_evaluation_methods_unsupervised_word_embeddings.pdf`): TODO, not yet used.
- Gladkova 2016 (`references/2016_gladkova_analogy_based_detection_morphological_semantic.pdf`): TODO, not yet used.
- Across algorithms in favour: Levy 2015, Huh 2024 (held): TODO.
- Sceptics of region, paths, symmetry: TODO search.
