# Plan: a new Part I chapter on similarity-trained and generative spaces

Date: 2026-11-11 (revised the same day after review). Status: plan only. Nothing in the book, the scripts or `_quarto.yml` has been changed for this chapter yet, apart from the terminology note already added to `index.qmd` ("Embedding Space or Latent Space?").

Background: `notes/emb_vs_lat.md` (gaps, errors, inconsistencies) and the discussion of 2026-11-11.

## 0. Before anything: keep the plan

**Done 2026-11-11.** `tmp/` is gitignored, so this plan and `emb_vs_lat.md` (whose comparison table section 4.3.1 reuses) were copied to `notes/` (outside the book, like `notes/ideas.qmd`). **This copy, `notes/generative_chapter_plan.md`, is the canonical one**; `tmp/generative.md` is only a pointer. They are untracked until the author commits them.

## 1. Decision summary

- **Add a new Chapter 4** to Part I, right after Chapter 3, tagged `idea`. File `chapters/generative_spaces.qmd`, label `sec-ch-generative-spaces` (D4; the name avoids the `latent_spaces` pattern of Chapter 3 in `sync_chapters.py`, see 7).
- **The durable question** (not a fashion word): *what does the training objective make distance mean, and can you get back from the vector to the data?* The chapter compares spaces trained for similarity (Chapter 3) with spaces trained to reconstruct, generate or predict.
- **Scope, final reading (author, 2026-11-11, D2/D3/D4/D8/D11/D12).** The two chapters split the field by one question: *does the model only learn a map, or does it define a distribution over the data?*
  - **Chapter 3 (embedding spaces)** covers the objectives that learn a map, from counting to prediction, **reconstruction (new section, the autoencoder)**, contrast and **prediction of embeddings (JEPA, which stays)**. Its title, "The Anatomy of Embedding and Latent Spaces", fits.
  - **Chapter 4 (generative models and their latent spaces, new)** covers the models that define a distribution: latent-variable models (VAE), denoising and diffusion, adversarial models, autoregressive models. It **ends by reconciling them with the predictive and reconstructive models of Chapter 3**, or by showing where they are similar and where they differ (4.3.7).
  - **RAG and vector databases (D11, open):** the author thinks they are an application of embedding and latent spaces, not a fundamental technology, so the chapter probably leaves Part I; where it goes is not decided. Until D11 is closed it stays where it is, and the plan numbers it as Chapter 5. Moving it later is cheap: the labels and cross-references follow `_quarto.yml`, so it is a change of `MASTER_PARTS` in `sync_chapters.py` plus the hand-offs (Step I2).
- **Old Chapters 4 to 13 become 5 to 14** (until D11 moves the vector-database chapter; the numbers are whatever `_quarto.yml` says). Chapters 1 to 3 keep their numbers (Chapter 3 gains one section, see 4.3a).
- **Step 0 first (section 1a):** replace the hand-typed "Chapter 13" by Quarto cross-references, so Quarto numbers the chapters from `_quarto.yml` and the insertion needs no renumbering. A pilot on a scratch copy worked in HTML and PDF.
- **Tone and size.** Same register as Chapter 3, light on scholarship: few citations, each where it carries a number or a theorem. Length target 15 to 18 pages for the finished chapter (it grew from 12 to 15 with JEPA and the consolidation).
- **Every section ends with exercises that reproduce its figures** (book rule), with a script under `code/generative_spaces/`.

Open decisions for the author are in section 9. The plan assumes the default in each.

## 1a. Step 0: replace text references to chapters by cross-references

**Idea (author, 2026-11-11).** Today the prose writes "Chapter 13" by hand: 206 chapter numbers on 2026-11-11 (ranges and lists counted per number) in 13 chapter files, `index.qmd` and `notes/ideas.qmd`; 197 of them in the files that are rendered. Every insertion, merge or drop, which the roadmap expects ("continue, reshape, merge or drop"), would repeat the renumbering. With cross-references Quarto numbers the chapters from their order in `_quarto.yml`, and the text follows. No literal "Chapter N" in the book refers to an outside work (checked with grep), so the conversion has no false positives of that kind.

**Pilot (done 2026-11-11, in two rounds; scratch copies deleted).** Quarto 1.5.57, HTML, PDF and EPUB, `number-sections: true` as in the book. The first round tested numbered chapters only and wrongly concluded that cross-references work everywhere. The second round tested every kind of page and found a Quarto bug.
- **Works everywhere** (numbered chapters in HTML, PDF and EPUB; every page in PDF and EPUB): a chapter heading `# Title {#sec-ch-embedding-spaces}` with `@sec-ch-embedding-spaces` renders "Chapter 3"; `Chapters [-@sec-ch-a] to [-@sec-ch-b]` renders "Chapters 3 to 4"; `* **@sec-ch-vector-databases: Title.** *(idea)*` renders "Chapter 4: Title."; a reference inside the italic plan paragraphs of the stubs renders too; `@sec-prop-nearness` renders "Section 1.1".
- **Fails: HTML, in pages without a chapter number (`index.qmd`, the epilogue, and `solutions.qmd`, which receives the answers of every chapter).** `@sec-ch-embedding-spaces` renders "3 The Anatomy of Embedding and Latent Spaces" (number and full title, no "Chapter"), and `[-@...]` is ignored, so ranges become "Chapters 3 Title to 4 Title". This is a known open bug of Quarto, still open in 1.8 and scheduled for 1.12 (quarto-dev/quarto-cli#14132, related #11292, #5946, discussion #9771). It affects exactly the pages with most of the references (the roadmap of `index.qmd`, 40 lines of the epilogue). The same pages are correct in PDF and EPUB.
- **Workaround, tested:** a project Lua filter for HTML only (prototype saved as `tmp/book-chapter-refs.lua`; installed as `filters/book-chapter-refs.lua` in Step D). It resolves every `@sec-ch-<stem>` itself, in all pages, from the order of `_quarto.yml` (a file is numbered unless its first H1 has `.unnumbered`): `@...` gives the link "Chapter N", `[-@...]` gives "N". The scratch test gave "Chapter 3", "3" and a correct link in `index`, epilogue, solutions and a numbered chapter. In the pilot it seemed to fail the build on an unknown label, but only by accident (see the Result of Step D: Quarto's `error` only logs); the installed version stops explicitly with `os.exit(1)` on an unknown label and on any form with a prefix, a suffix or several citations, and its tests check message and exit status. Quarto's own treatment is left in place for PDF and EPUB.
- **Unresolved label in PDF and EPUB:** Quarto only warns ("Unable to resolve crossref @sec-ch-...", exit status 0) and prints `?@sec-...`. So 0e must grep the logs; it is not free there. In HTML the filter already fails.
- **Existing `@sec-prop-*` references:** none in `index.qmd`, the epilogue or `solutions.qmd` today, so the same bug (they would render "1.1 Title" in HTML) does not affect the text now. Rule for the future: do not reference sections from those three pages, or extend the filter.
- **Decision D10:** closed, option A (labels in the roadmap), with the filter.

**Procedure.**
- **0a. Tooling.**
  - `validate_book.py` raises an ERROR when a file with YAML front matter has no `title` (line 71). Chapters keep `status:` and `open:` in the front matter but move the title to a labelled H1 (the epilogue already does this, `# ... {.unnumbered .idea}`). Change the validator to accept an H1 as the title; update `test_validate_book.py`.
  - `durability_metrics.py` **does** need changes. `_INDEX_TAG` (line 66) reads the roadmap tags only from `* **Chapter N: ...**  *(tag)*`, and `status_report` keys chapters as `f"Chapter {i}"` (line 164). `TITLE_LINE` (line 61) has the same literal form. Accept `* **@sec-ch-<stem>: ...**` as well, and key the roadmap entries by label, mapped to files through `_quarto.yml` order. Update `test_durability_metrics.py`.
  - `sync_chapters.py` falls back to the first `# ` line when the front matter has no title (`extract_title_from_qmd`), so the title now carries the `{#sec-ch-...}` attribute. Strip `{...}` there; matching still works on the stem.
  - `filters/book-chapter-refs.lua` (from the prototype) in the `filters:` list of the `html` format of `_quarto.yml`, first. Test it by rendering a tiny scratch book (one numbered chapter, one unnumbered page; `pytest` skips if `quarto` is missing): "Chapter 1" and "1" in both pages, a failing build on an unknown label.
  - Check with `make status` (no new warnings) and `make durability`.
- **0b. Labels.** For each of the 13 numbered chapter files (14 after the insertion), move `title: "..."` to `# Title {#sec-ch-<stem>}`, where `<stem>` is the file stem with `_` replaced by `-` (`embedding_spaces` → `sec-ch-embedding-spaces`). The epilogue and solutions stay unnumbered and unlabelled.
- **0c. Conversion script.** One-time, from the current numbering (still valid) to labels, using the "Old" column of section 3. A dry run prints every changed line and the total count (expect 206; a different count means a pattern was missed). Then hand review.
  - `Chapter N` becomes `@sec-ch-<stem>`.
  - `Chapters N to M`, `N and M`, `N, M and K` become `Chapters [-@a] to [-@b]` and so on (the plural word stays typed).
  - The 13 roadmap headings in `index.qmd` (`* **Chapter 4: Title.**`) become `* **@sec-ch-<stem>: Title.**`.
  - In scope: `chapters/*.qmd` except `solutions.qmd` (generated; it inherits the converted answers through `make sync-solutions`), `index.qmd`. `notes/ideas.qmd` is not rendered: keep its numbers but date them ("Chapter 5 as of 2026-11").
  - Excluded: the skills and README (documentation of the tooling; keep numbers or point to the roadmap).
  - Optional second pass, not part of the gate: mentions by section name ("Where a Single Vector Strains") to `[Where a Single Vector Strains](#sec-...)`, so the link survives a rename.
- **0d. Gate: the visible text must not change.** Render HTML, PDF and EPUB *before* the conversion (the baseline is step 1 of section 10) and after it. Strip the tags per chapter and diff the text. The diff must be empty. This makes the conversion exact.
- **0e. Guards.**
  - A lint in `validate_book.py` that warns on a literal `Chapters? \d+` in `chapters/*.qmd` and `index.qmd`, so new text uses references. Test it.
  - `make book` fails on "Unable to resolve crossref" in the Quarto log of PDF and EPUB (HTML fails by itself through the filter), so a dropped or renamed chapter is an error, not a silent `?@sec-...`. In the Makefile, `quarto render ... 2>&1 | tee log` and a `grep -q` on the log, keeping the exit status of `quarto`.
  - A check that the roadmap order in `index.qmd` equals the order in `_quarto.yml` (in `durability_metrics.py status`, next to the tag check).
- **0f. Effect on the rest of this plan.** Inserting the new chapter needs no renumbering pass (section 6 is the fallback only). What remains by hand are the *semantic* edits that no numbering fixes; they are listed in section 7 under "Semantic edits".

**Cost and risk.** The same mapping work as a renumbering, done once and checked by the text diff of 0d, plus one small Lua filter that works around a Quarto bug (to be deleted when Quarto 1.12 fixes #14132; the text diff shows if it still matters). Risks: a mistyped label (the lint, the filter and the build log catch it); prose where "Chapter" should stay literal (hand review; none found by grep); the changes to the validator, the durability script and `sync_chapters.py` (covered by their tests). Benefit: every later reshuffling, including the new Chapter 4 and the decisions at the Part II to IV gates, costs nothing in numbering.

## 2. Why this chapter

1. Chapter 3 tells how similarity-trained vectors are built (counting, prediction, contrast, prediction of embeddings; the autoencoder is added, see 4.3a). The most common meaning of "latent space" in machine learning, the space of an autoencoder or generative model, is not in the book (gap 1 of `notes/emb_vs_lat.md`). Only sparse autoencoders appear (old Chapter 5, new 6).
2. Whether distance means anything depends on the objective. Chapter 1's first property, *nearness is likeness* (`@sec-prop-nearness`), holds by construction in a similarity-trained space and is not automatic in a reconstruction-trained one.
3. *Meaning can move: paths* (`@sec-prop-paths`) and the thread "reasoning as a path through the space" need a way to say when the midpoint of a path is meaningful. A decoder gives a check; a contrastive embedding does not.
4. The live scale question of the book, whether prediction in latent space scales as a general method or scaled generative models absorb it, is this distinction. It was planned for old Chapter 13 (new 14) under JEPA; JEPA's mechanism stays in Chapter 3 and its debate with scaled generative models is the scale test of Chapter 4, which gives it a home before Parts II and III use it.
5. Later chapters build on it. New Chapter 7 (old 6, geodesics and curvature) needs the metric a decoder induces. New Chapter 14 (old 13, multimodal) needs the difference between what a space keeps and what it can regenerate, since text-to-image systems decode from a similarity-trained space.

## 3. Placement and numbering

| Old | New | File | Notes |
|:--|:--|:--|:--|
| 1 | 1 | `properties_of_meaning.qmd` | unchanged |
| 2 | 2 | `curse_of_dimensionality.qmd` | unchanged |
| 3 | 3 | `embedding_spaces.qmd` | gains "Learning by Reconstruction" (4.3a); "Next:" line and ledger of limits change |
| – | **4** | `generative_spaces.qmd` | **new, `idea`** |
| 4 | 5 | `vector_databases.qmd` | D11: probably leaves Part I (an application); position open |
| 5 | 6 | `contextual_vectors.qmd` | Part II gate moves to its scale test (D6) |
| 6 | 7 | `tangent_spaces_geodesics.qmd` | |
| 7 | 8 | `graph_embeddings.qmd` | |
| 8 | 9 | `topological_deep_learning.qmd` | |
| 9 | 10 | `complex_plane_quantum_logic.qmd` | |
| 10 | 11 | `vector_symbolic_architectures.qmd` | |
| 11 | 12 | `neurosymbolic_integration.qmd` | |
| 12 | 13 | `cross_domain_transfer.qmd` | |
| 13 | 14 | `multimodal_embeddings.qmd` | |

The "Old" column is the mapping for the conversion script of 0c. After Step 0, Quarto numbers headings and references from the order in `_quarto.yml`, so the "New" column needs no edit in the prose.

## 4. Chapter specification

### 4.1 Front matter and tag

```markdown
---
status: idea
open: "Home of the JEPA-against-generative scale question (here or in Chapter 14). Decide when Chapter 3's last two sections are written."
---

# <title, see D1> {#sec-ch-generative-spaces}
```

Title (D1: the title of this new chapter, open). It should name the question, not a method; now that the chapter is the latent counterpart of Chapter 3 and "latent" is the word the literature uses for these spaces, three candidates:
- "Latent Spaces: Reconstructing, Generating, Predicting, and What They Share" (names the contents and the consolidation).
- "Latent Spaces: When the Vector Has a Way Back to the Data" (names the question; the shortest to remember).
- "What the Objective Makes a Space Mean: Similarity, Reconstruction, and the Way Back" (the first candidate of the plan; it covers both chapters more than this one).

Check the chosen title against the patterns of `MASTER_PARTS` in `sync_chapters.py` (matching is a substring test on stem *and* title, first match wins).

### 4.2 Opening and closing contract (review-doc §15 Job B)

- **Opening.** States the bet this chapter's structure makes against the bitter lesson, in the book's neutral voice. Draft: a decoder is built-in knowledge that a space must be able to regenerate its data. Scale may make it unnecessary (a similarity-trained space plus enough data suffices) or may make it dominant (generation is the general method). Neither is assumed.
- **Properties named, with anchors.** `@sec-prop-nearness`, `@sec-prop-paths`, `@sec-prop-arrangement`, `@sec-prop-invariance` (the invertible-matrix freedom of Chapter 3, exercise 22, and the rotation-symmetric prior of a VAE). `@sec-prop-direction` only if the latent-arithmetic material is kept.
- **Closing.** The chapter's current reading of its scale test, dated and with its evidence class, "undecided" being valid. The hand-off to Chapter 5 (4.4).

### 4.3 Sections of Chapter 4

Each section is a stub at first (`idea`), written like the existing stubs (one italic paragraph of plan per section). Each finished section ends with the questions and answers blocks (`::: {.questions}` then `::: {.answers}`).

**The map the two chapters share** (it is the first table of Chapter 4 and the closing table of 4.3.7): two questions classify every objective. *Where is the error measured?* In the data, among sampled candidates, or in the code. *Does the model define a distribution over the data* (something to sample and to score)?

| Objective | Kind | Error measured | Distribution over the data | Chapter |
|:--|:--|:--|:--|:--|
| counting and SVD | reconstructive (of a matrix) | in the data (a matrix) | no | 3 |
| prediction of the neighbour (word2vec) | predictive | in the data (the neighbour), a softmax over the vocabulary | only of the neighbour, given the word | 3 |
| autoencoder | reconstructive | in the data (the input) | no | 3 (new) |
| contrast (InfoNCE) | contrastive (discriminative) | among sampled candidates | no | 3 |
| prediction of embeddings (JEPA) | predictive, in the code | in the code | no | 3 |
| VAE | reconstructive and generative | in the data, plus a prior on the code | yes (prior and decoder) | 4 |
| denoising and diffusion | reconstructive (of noise) and generative | in the data (noise) | yes (a score, a chain) | 4 |
| GAN | generative (adversarial) | by a discriminator | yes, implicit (can sample, cannot score) | 4 |
| autoregressive and masked models | predictive and generative | in the data (the next token) | yes (chain rule) | 4 |

The *Kind* column uses the labels of the author's suggestion (reconstructive, predictive, generative; the "hybrid" is the rows with two kinds), plus *contrastive*, which none of the three labels covers (D15).

1. **The Fork: A Map or a Distribution?**
   One-page recap of the objectives of Chapter 3, now including the autoencoder, and what they do not have: a way to draw a new point and to say how likely a point is. The table above. The terminology of the Prologue made precise (the table drafted in `notes/emb_vs_lat.md`), with the places where the literature has settled on one word (D8). The sentence that fixes the scope: flows and energy-based models are not told here (4.3, "Where the map stops").
2. **Giving the Space a Density: Latent Variable Models and the VAE.**
   The hidden-cause view (factor analysis, LSA's "latent", EM). The evidence lower bound as a reconstruction term plus a prior term, read against the autoencoder of Chapter 3: the same decoder, a prior added. What the prior buys (sampling, smoothness) and costs (posterior collapse as the cousin of the dimensional collapse of Chapter 3; holes between the codes). Identifiability: the standard prior is rotation-symmetric, so the invertible-matrix freedom of Chapter 3 survives as a rotation freedom, and disentanglement is not free.
3. **Denoising, Diffusion and the Adversarial Game.**
   Dated history, past tense. A denoising autoencoder (Chapter 3) learns the direction towards the data; chained, it is a diffusion model. Latent diffusion works in the latent space of a pretrained autoencoder, and conditioning typically comes from a similarity-trained encoder (CLIP), so the two kinds of space cooperate; this is where Chapter 14's multimodal spaces meet generation. GANs: a discriminator in place of a likelihood, which can sample and cannot score. One to two pages; the aim is the contrast, not a survey.
4. **Autoregressive and Masked Models: Predicting the Next Piece.**
   The prediction of Chapter 3 (word2vec's softmax over the neighbour) taken to the whole sequence by the chain rule is a generative model of text; Shannon's generator and the n-gram models of Chapter 3 were already one. Its hidden vectors, not a code trained for it, are the contextual vectors of Chapter 6, which is how this section hands the thread on. One page.
5. **The Geometry a Decoder Induces.**
   A decoder pulls a metric back onto the code space, so straight lines in the code are curved in the data, and the shortest path is a geodesic of the pullback metric. Anchor: `arvanitidis2018latent`. This is the one home of the pullback idea; it applies to the autoencoder of Chapter 3 as well, and Chapter 7 develops geodesics and points back. The same section answers *when is a midpoint meaningful*.
6. **Where the Map Stops.**
   Half a page: what the two chapters leave out and why (normalising flows, which are invertible and so give an exact way back; energy-based models; supervised and metric-learning embeddings, mentioned in Chapter 3 under contrast; learned states of agents, Chapter 14).
7. **Reconciling the Two Families.** *(two or three sections; the author's request, D4)*
   - *What each pays for.* The table above completed with the other columns: what keeps the space from collapsing, whether there is a decoder, what happens off the data, the typical failure. Each cell marked *structural* (follows from the objective) or *contingent* (how systems behaved at a date).
   - *A common currency: information.* The attempt at one view, in Shannon's terms, the backbone of Chapter 3. Candidate statements to check against sources before they are written: the InfoNCE objective is a lower bound on the mutual information between the two views (`oord2018representation`); the reconstruction term of the ELBO is a lower bound on the information the code keeps about the data, and the whole ELBO trades that information (distortion) against the description length of the code (rate), Shannon's rate–distortion trade-off; so both families maximise information kept about the data, one with a decoder as the variational family and one with a critic that compares candidates. If it holds, it is one inequality and one picture; the experiment's figure (a), reconstruction error against retrieval, is then a rate–distortion-like plane.
   - *Similarities and differences.* To be stated only as far as the sources and the experiment support it: a bound on information says nothing about the geometry (two encoders at the same bound can have different distances); reconstruction prices every detail by the metric on the data, while contrast prices only what separates a sample of negatives and caps at $\log_2 N$ bits; JEPA prices only what is predictable in the code; only the generative family gives a density; and there is work arguing that the mutual-information view does not explain why contrastive methods work. The result is graded: **the same family at the level of what information the code keeps, different at the level of how distance is priced and of whether there is a distribution**. "Not reducible to one objective" is a valid result.
8. **Scale Test (dated 2026).**
   Question: as data and compute grow, does generation absorb the maps of Chapter 3 (a decoder everywhere), does prediction without a decoder (JEPA) absorb generation, or do both survive because they answer different questions (what you can get back and sample, against what you can compare)? Evidence classes kept apart: a position paper (`lecun2022path`), scaled generative results, and the chapter's own toy experiment, which is small and says so. Closing reading: undecided unless the evidence moves.

### 4.3a What Chapter 3 gains

One new section, tagged `{.idea}`, **after "Learning by Predicting Embeddings"**, the last of the objectives and just before "The Geometry of Meaning" (moved there on 2026-11-11 at the author's request: "keep the order that minimizes novelty in each section, building one after the other". The order is counting, prediction, contrast, prediction of embeddings, reconstruction: contrast keeps the softmax of prediction and changes the candidates; prediction of embeddings keeps the two views and the encoder of contrast and changes the target; reconstruction goes back to the data, reuses the `predict` model of the contrast experiment and the SVD, and leads to the next chapter):

- **Learning by Reconstruction.** Prediction predicts a neighbour; reconstruction predicts the input itself through a small code. The linear case is the SVD the chapter already proves (Eckart–Young): $\mathbf{M}\approx\mathbf{E}\mathbf{V}^\top$ is a linear encoder-decoder, and "latent" in LSA is this case. The nonlinear autoencoder generalises it; a denoising autoencoder reconstructs from a corrupted input and is the first step towards Chapter 4. What the code keeps (what is needed to rebuild, brightness included) against what a contrastive code keeps (what separates); no guarantee that distance means anything. This is the author's own idea of `notes/ideas.qmd` (the autoencoder as the generalisation of Eckart–Young), now adopted. Experiment and exercises: section 5 (script `code/embedding_spaces/reconstruct_digits_ae.py`).
- The claim of the JEPA section ("the four objectives differ in what the vector pays for") becomes "the five", with reconstruction paying for every detail of the input; the intro of the chapter and the roadmap entry list five objectives.
- The ledger of limits gains one entry (4.4).

### 4.4 Hand-offs

- **Chapter 3 was split on 2026-11-11 (D17):** the new Chapter 3 is `symbols_without_interior`, "Symbols Without Interior" (Shannon, Chomsky, one-hot symbols, Rice) and the old Chapter 3 is now Chapter 4; in the rest of this plan, "Chapter 3" means the embedding-spaces chapter, which is now **Chapter 4** in the book (the numbers of the plan before D17 are not renumbered by hand; use the labels).
- **The embedding-spaces chapter gains the autoencoder and keeps JEPA** (4.3a). Its roadmap entry in `index.qmd` ("Counting, predicting, contrasting, and predicting embeddings turn Shannon's own quantities into geometry") adds reconstruction.
- **Chapter 3 to 4.** New "Next:" line for Chapter 3: *a map from data to vectors is one way to build a space; the other defines a distribution over the data, and with it a way to sample and to score.* The ledger of limits at the end of Chapter 3 gains one entry stated as a cost: the objectives of this chapter fix what distance means and none of them says how likely a point is or what lies between the data; the models of @sec-ch-generative-spaces add a distribution, and distance then no longer has to mean similarity.
- **Chapter 4 to the next chapter.** Until D11 is closed, the next chapter is the vector-database chapter and Chapter 3's old hand-off moves here: *the first limit is practical, finding the nearest vector among billions; search applies to either kind of space.* If D11 moves that chapter out of Part I, the next chapter is the contextual-vectors one and the hand-off is *the same dot-product machinery runs inside the model* (the autoregressive section of Chapter 4 already points there).
- **Chapter 14** keeps the image and video forms of JEPA and the modality gap, and points to Chapter 4 for the debate with scaled generative models.

## 5. Experiments and exercises (reproducible, reusing Chapter 3's toy)

Goal: put the objectives of both chapters on the same data and metrics as Chapter 3's contrast experiment, so that the chapters share one table of numbers and the consolidation (4.3.7) is read from data. There are two scripts, one per chapter.

**What Chapter 3 already has.** `contrast_digits_infonce.py` trains, besides InfoNCE, a `predict` model: the same encoder (64 → 128 → 16, ReLU) with a *linear* read-out of the unnormalised 16 coordinates, trained by squared error to produce the pixels of the *other* view. It is a cross-view autoencoder with a linear decoder, and it is already a row of `tbl-contrast-digits`. The new models are placed relative to it, not beside it as if new.

- **Data.** The 8×8 digits of scikit-learn, 1,200 training and 597 held-out images, the same split and augmentation (`augment`: shift of at most one pixel, Gaussian noise 0.15). Dimension $d=16$ for every model.
- **Training inputs.** Every model sees augmented views, as in Chapter 3. Autoencoders reconstruct the *other* view of the same image (a denoising, cross-view objective), so they are trained with the same invariance as InfoNCE and the retrieval comparison is fair. A plain same-view autoencoder is reported once as a reference row.
- **Library.** `numpy` with hand-written backward passes is the baseline, like every script in `code/`. D9 (closed): if PyTorch (or another library) makes a model shorter and clearer to read, use it for that model, and say so in the script header and in the table; `torch` 2.14.1 is already installed in `.venv` but is declared nowhere (the repository has no requirements file) and no script uses it yet, so the first use must also record the dependency. Rows that must reproduce Chapter 3's numbers stay in numpy.
- **Reuse.** Import `augment`, `forward`, `retrieval`, `alignment`, `uniformity`, `cosines` and the training of the InfoNCE encoder from `code/embedding_spaces/contrast_digits_infonce.py` (its top level only loads data; the run is under `if __name__ == "__main__"`). The import needs a path insertion; if that is too fragile, move the shared parts to `code/embedding_spaces/utils.py`, which the Makefile already treats as a helper of every script (`CODE_HELPERS`).

**Scripts of Chapter 3** (two, one per new or moved section; both import, and do not change, the contrast script). **Skeletons exist since 2026-11-11** (docstring with the plan, `# SKELETON` on the first line, `raise SystemExit`); the Makefile lists and skips them, so they are never stamped as passed:
  - `code/embedding_spaces/reconstruct_digits_ae.py` ("Learning by Reconstruction"):
    0. Chapter 3's `predict` (linear decoder), imported.
    1. Linear autoencoder, checked against the PCA/SVD of the same dimension (already a baseline in Chapter 3).
    2. Nonlinear autoencoder (64 → 128 → 16 → 128 → 64): model 0 with a nonlinear decoder; and its denoising variant (corrupted input, clean target).
  - `code/embedding_spaces/predict_embeddings_digits_jepa.py` ("Learning by Predicting Embeddings"):
    3. A JEPA-style model: the same encoder for the context view, a predictor (16 → 128 → 16) and a target encoder that is a moving average of the first, the loss a squared distance in the code space, no negatives and no decoder. Torch is a good candidate. It provides the exercise inherited from the plan of that section: switch the moving average off and watch the collapse.
  Measures: the list below. Figures in `figures/embedding_spaces/`. If D17 moves "Learning by Reconstruction" to Chapter 4, its script moves to `code/generative_spaces/` with it.

**Script of Chapter 4: `code/generative_spaces/generative_vs_maps_digits.py`:**
  4. VAE with a standard normal prior (same sizes). Retrieval and interpolation use the posterior mean. $\beta$ is fixed from the reconstruction alone (the largest $\beta$ whose held-out reconstruction is within a stated margin of model 2), *before* retrieval is computed, and the rule is reported.
  5. The InfoNCE encoder of Chapter 3 at $N=128$, frozen, plus a decoder (16 → 128 → 64) trained on its unit-norm codes: the "way back from a similarity code".
  6. Optional, if the run stays under a few minutes: a tiny denoising chain (a few noise levels) on the codes of the autoencoder, to show sampling from a model that defines a distribution. Dropped if it needs more than a page of code.
  The script also **collects the rows of the other script and of Chapter 3's contrast script into one table** (`tbl-generative-digits`), which is the data of the consolidation.

- **Measures** (mean over five seeds with [minimum, maximum], as in Chapter 3).
  - Reconstruction error on held-out images (pixel MSE), for every model with a decoder.
  - Retrieval of the other view among the held-out views (Chapter 3's definition).
  - Alignment, uniformity and offset (same definitions).
  - Effective rank of the codes (the exponential of the entropy of the normalised singular values), to show collapse in model 3 without the moving average and the narrow cone of the plain autoencoder.
  - Interpolation. For every model with a decoder, decode the midpoint between the codes of two held-out images and report its pixel distance to the nearest *training* image, against the same distance for the straight pixel average. For model 5 the midpoint is taken on the sphere (normalised), because the decoder was trained on unit-norm codes; the unnormalised midpoint is reported as a footnote to show the difference.
- **Figures.**
  - (a) Reconstruction error against retrieval, one point per model and seed: the "pays for every detail" against "pays for what separates" trade-off, read once the numbers exist. Chapter 4, `figures/generative_spaces/`.
  - (b) Interpolation strips for models 2, 4 and 5.
  - (c) The cosines or offsets, if needed to show a narrow cone for the autoencoder (Chapter 3).
  - (d) For the consolidation: the plane of (a) with all models joined in the order of the table of 4.3, so that "one family, different pricing" is read from the data and not from the prose. If the points do not fall on one trade-off curve, the section says so.
- **Tables.** Chapter 3 gets its own small table for the new rows, pointing to `tbl-contrast-digits`; Chapter 4 gets `tbl-generative-digits`. Both are filled from script output; no number is typed by hand.
- **Do not state results in the plan.** The prose and the answers are written after the scripts run, and the numbers are copied from their output (as for `contrast_digits_infonce.py`).
- **Exercises** (3 to 4 per chapter, each with an answer in the `::: {.answers}` block).
  - Chapter 3: (1) show that a linear autoencoder with squared error recovers the span of the top-$d$ singular vectors (link to the SVD and Eckart–Young); (2) the collapse of the JEPA-style model without the moving average, measured by the effective rank; (3) the experiment, with script name, run time and what to look at in each figure.
  - Chapter 4: (1) write the evidence lower bound of a VAE with a Gaussian posterior and prior, and say what each term pays for; (2) why is the midpoint of two codes checkable for one kind of space and not for the other; (3) the experiment and the consolidation figure.
- **Scripts run** in about a minute each (measure; Chapter 3's script trains 25 encoders for 2,000 steps, so parallelise like it with `ProcessPoolExecutor`), assert their main numbers like the other scripts, and `make test-code` picks them up through the wildcard `code/*/*.py`.

## 6. Renumbering procedure (fallback, only if Step 0 is abandoned)

With Step 0 done, skip this section.

206 chapter numbers across 15 files. Chapters 1 to 3 keep their numbers; everything from 4 up shifts by one. Generated files are rebuilt, not edited.

1. Work on a branch, so the whole change is one reviewable diff.
2. Script with a regular expression for `Chapters? N`, lists and ranges (`Chapters 6 to 12`, `Chapters 10 and 11`, `Chapters 4, 5, 8 and 9`, `Chapters 3 and 13`). Add 1 to every integer that is 4 or more. Dry run first, printing every changed line.
3. Files in scope: `chapters/*.qmd` except `solutions.qmd`, `index.qmd`, `notes/ideas.qmd`, `README.md`, and the skills (`.github/skills/build-book/SKILL.md` file list; `.github/skills/review-doc/SKILL.md` "Chapters 3 to 13").
4. Hand review: the semantic edits of section 7, plus every Epilogue mention (40 lines) read in context.
5. Checks: no "Chapter 15" anywhere; the count before and after is the same except for lines added for the new chapter; `make sync-solutions`, `make validate`, `make status`, `make book`.

## 7. Files to change (checklist, assuming Step 0 is done)

**New**
- `chapters/generative_spaces.qmd` (stub with the eight sections of 4.3, `status: idea`, labelled H1).
- `code/generative_spaces/generative_vs_maps_digits.py` and `code/embedding_spaces/reconstruct_digits_ae.py` (shared helpers go to `code/embedding_spaces/utils.py`, see 5).
- `figures/generative_spaces/` and the new figures of `figures/embedding_spaces/` (written by the scripts).

**Registration**
- `.github/skills/build-book/scripts/sync_chapters.py` (D11 may add a second change here: the vector-database chapter moves to another part, which is an edit of the same table): `MASTER_PARTS` gets the new entry with `num: 4` and patterns (`"generative_spaces"`, `"generative"`), and the later `num` values and their `"0N_"`/`"chapterN"` patterns shift by one. Add a test in `tests/test_sync_chapters.py` that `generative_spaces.qmd` maps to Chapter 4 and `embedding_spaces.qmd` still maps to Chapter 3. (Had the file been called `generative_latent_spaces.qmd`, it would have matched Chapter 3's `"latent_spaces"` pattern, because matching is a substring test where the first match wins; if D4 brings that name back, remove `"latent_spaces"` from Chapter 3's patterns.)
- `_quarto.yml`: by `make sync-chapters`, not by hand.
- `.github/skills/build-book/SKILL.md` (file list), `.github/skills/review-doc/SKILL.md` ("Chapters 3 to 13" → "3 to 14"): these keep literal numbers (excluded from Step 0).

**Semantic edits** (what no numbering fixes)
- `index.qmd`
  - New Chapter 4 paragraph in Part I with its scale test and "Next:" line, tagged `*(idea)*`, not in the voice of a written chapter.
  - The Chapter 3 roadmap entry: add reconstruction to its list of objectives ("Counting, predicting, reconstructing, contrasting, and predicting embeddings turn Shannon's own quantities into geometry") and the new "Next:" line (4.4).
  - The note "Embedding Space or Latent Space?" in the introduction: the book uses the two words interchangeably, except where the literature has settled on one for a context, with the examples of D8; where the training matters, it says which one produced the space.
  - The Part I intro sentence: add that the way a space is built decides what its distances mean.
  - The "three devices" paragraph: the range of chapters closing with a scale test starts at the new Chapter 4 (`Chapters [-@sec-ch-generative-spaces] to [-@sec-ch-multimodal-embeddings]`).
  - The old Chapter 5 scale test ("which structures of Chapters 6 to 12"): check that the converted range still means Part II and III structures and not the new Chapter 4.
  - The old Chapter 13 roadmap entry: the debate between JEPA and scaled generative models is Chapter 4's scale test and this entry points to it; its mention of "prediction in latent space (JEPA)" keeps the image and video forms.
  - Part I is now six chapters long. If D11 moves the vector-database chapter out of Part I (Step I2), the parts of `_quarto.yml` (which `make sync-chapters` writes from `MASTER_PARTS`), the Part I intro, the Chapter 3 and 4 hand-offs and the `OPEN` comment change with it.
  - The `OPEN` comment on Parts II to IV: "after the Chapter 5 scale test" becomes a reference to `sec-ch-contextual-vectors` (D6).
- `chapters/embedding_spaces.qmd`
  - Closing "Next:" hook and the ledger of limits in "Where a Single Vector Strains" (new entry, 4.4).
  - New section "Learning by Reconstruction" `{.idea}` after "Learning by Predicting Embeddings" (4.3a); the section "Learning by Predicting Embeddings" stays the fourth objective with its claim about four objectives, and the claim about reconstruction (the only objective with error measured in the data and a way back) closes the new section; the chapter introduction lists the five in this order.
  - The contrast experiment: one sentence pointing to Chapter 4 for the decoder side of the `predict` row and to the consolidation table.
- `chapters/multimodal_embeddings.qmd`: the stub says "The fourth objective of Chapter 3, now applied where it was designed"; with the new section JEPA is the fifth, so the sentence is reworded to name it ("the prediction of embeddings of Chapter 3") and points to Chapter 4 for the debate with scaled generative models. This chapter's scale test asks whether scale closes the modality gap.
- `chapters/tangent_spaces_geodesics.qmd`: point to Chapter 4 for the pullback metric instead of introducing it.
- `chapters/contextual_vectors.qmd`: sparse autoencoders now follow the autoencoder of Chapter 3 (the new section); add the pointer. The autoregressive section of Chapter 4 points here.

**Step 0** (section 1a): all numbered `chapters/*.qmd` (title to labelled H1, references converted), `index.qmd`, `validate_book.py` and `test_validate_book.py`, `durability_metrics.py` and `test_durability_metrics.py`, `sync_chapters.py` (title attribute), `filters/book-chapter-refs.lua` and the `filters:` list of the `html` format in `_quarto.yml` (by hand: `sync_chapters.py` must be checked not to overwrite it), `Makefile` (fail on unresolved references).

**Notes**
- `notes/durability.json`: re-snapshot after the author approves (`durability_metrics.py snapshot`).
- `notes/ideas.qmd`: record the decision (new chapter, reason, reopen-if) and the open durability action "decide the title"; date its literal chapter numbers.

## 8. Sources

Already in `references.bib` (check each against its PDF with `ground_check.py` before citing):
- `arvanitidis2018latent` (curvature of generative latent spaces; PDF present, cited only in Chapter 1 so far).
- `dempster1977maximum` (EM and latent variables, uncited), `hinton1986learning`, `lecun2022path` (JEPA position), `assran2023selfsupervised`, `bardes2024revisiting`, `assran2025vjepa2` (JEPA family, uncited), `wang2020understanding`, `radford2021learning` (CLIP).
- `eckart1936approximation` (PDF in `references/`) for the linear autoencoder exercise.

To add and verify, **all from memory and not yet checked** (do not cite until fetched and checked):
- Autoencoders and bottleneck: Hinton and Salakhutdinov 2006; Baldi and Hornik 1989 (linear autoencoders and PCA).
- VAE: Kingma and Welling 2014; their Foundations and Trends introduction of 2019.
- GAN: Goodfellow and colleagues 2014; DCGAN vector arithmetic (Radford and colleagues 2015).
- Diffusion: Ho and colleagues 2020; Rombach and colleagues 2022 (latent diffusion); Ramesh and colleagues 2022 (decoding from CLIP embeddings).
- Consolidation (4.3.7), all from memory and unchecked: Barber and Agakov 2003 (the variational lower bound on mutual information with a decoder); Poole and colleagues 2019 (a survey of the bounds, with InfoNCE and the reconstruction bound side by side); Alemi and colleagues 2018 (the ELBO read as a rate–distortion trade-off); Tschannen and colleagues 2020 (arguing that mutual-information maximisation does not by itself explain the success of contrastive representation learning); Shannon 1959 (rate–distortion). `oord2018representation` (InfoNCE as a lower bound on mutual information) is already in `references.bib`. Without these read, the section states no unification claim.
- Collapse and identifiability: Bowman and colleagues 2016 (posterior collapse in text VAEs); Locatello and colleagues 2019 (disentanglement is not identifiable without extra assumptions).
- Geometry of decoders: Shao and colleagues 2018; Lobashev and colleagues 2025 (Hessian geometry of diffusion latent spaces; perishable, date it if used).

Rules for use (the book's brief, discussion of 2026-11-10 on tone):
- Few citations, each at a number, a formula or a theorem. No name-drops without consequence.
- Methods told as dated history in the past tense; the question carries the chapter.
- A locator for every specific claim (`ground_check.py` finds the page).
- Run `fetch_references.py` for the new entries and `build_index.py` afterwards.

## 9. Decisions of the author

Answers of 2026-11-11. "Closed" means decided; "open" is still waiting for the author.

- **D1. Title of the new chapter.** **Closed** (author, 2026-11-11): "Latent Spaces from Generative Models". The label is `sec-ch-generative-spaces` whatever the title.
- **D2. Split between Chapters 3 and 4.** **Closed** (author, second answer of 2026-11-11, replacing my first reading): Chapter 3 is about embedding spaces and the predictive and reconstructive models (counting, prediction, reconstruction, contrast, prediction of embeddings); Chapter 4 is about generative models and ends by reconciling them with the predictive and reconstructive ones, or by showing their similarities and differences. The debate between prediction in the space (JEPA) and scaled generative models is the scale test of Chapter 4; Chapter 14 keeps the image and video forms of JEPA and the modality gap, and points back.
- **D3. Does "Learning by Predicting Embeddings" stay in Chapter 3?** **Closed: yes** (it is predictive; "see D2"). The plan's earlier idea of moving it to Chapter 4 was a misreading and is recorded as dropped in section 12.
- **D4. File name.** **Closed:** `generative_spaces.qmd`. New requirement: the chapter ends with one or more sections that consolidate the two approaches if possible and explain why they are not the same if not (4.3.7).
- **D5. When.** **Closed:** insert the chapter now (Step 0 is done).
- **D6. Part II gate.** **Closed:** Part II stays as it is, decided after the contextual-vectors scale test.
- **D7. Title in the heading.** **Closed** (done in Step E).
- **D8. Chapter 3's title and the words.** **Closed:** no retitling. The introduction says that the book uses "embedding space" and "latent space" interchangeably, except where the literature has settled on one word for a context (for example *latent semantic analysis*, *latent variable*, *latent diffusion* against *word embedding*, *embedding model*); where the training matters, it says which one produced the space. Chapter 3 leans on "embedding" and Chapter 4 on "latent" because that is what their literatures do, and the SVD, which is "latent" in LSA, is named as the case where the two chapters meet (4.3.2). The note in `index.qmd` ("Embedding Space or Latent Space?") is edited in Step I; Chapter 3's title ("The Anatomy of Embedding and Latent Spaces") and the Wave-Nature chapter's stay as they are.
- **D9. Library for the experiment.** **Closed:** numpy is the baseline and the good default; PyTorch or another library is welcome if it is easier and more didactic for a model (see section 5).
- **D10. Roadmap headings.** **Closed 2026-11-11: option A** (labels).
- **D11. Where does RAG (the vector-database chapter) belong?** **Closed for now (author, 2026-11-11), the chapter's future is open.** The author is not sure the chapter should be in the book at all ("idea phase"). For the time being: **contextual vectors is Chapter 5 and closes Part I; the vector-database chapter is Chapter 6 and opens Part II** (the swap of the two options of D11b, chosen by the author after seeing that the literal reading would move contextual vectors into Part II). Applied in Step I2. If the chapter is dropped, nothing else in the numbering changes.
- **D16. Part II as the remedies for the shortcomings of Part I** (author, steering of 2026-11-11). **Open idea, recorded as idea 10 in `notes/ideas.qmd` and in the `OPEN` comment of `index.qmd`; not applied.** Retrieval grounds generation and so patches hallucination; Part II could be the shortcomings of Part I and the remedies that were tried. The book's ledger of limits (Chapter 3) already works this way for every later chapter. One correction recorded with it: embeddings do not hallucinate, generative models do; retrieval is a remedy for Chapter 4's shortcoming, running on embeddings. The current layout already fits it (Part II opens with retrieval); only the title and intro of Part II would change. Decided at the Part II gate.
- **D12. Reading of D2.** **Closed 2026-11-11 ("yes") and then refined by the author**: see D2. The refinement moves the autoencoder to Chapter 3 and keeps JEPA there, so the first reading ("Chapter 4 covers reconstruction, generation and JEPA") no longer holds.

- **D13. Title of Chapter 3.** **Closed** (author, 2026-11-11): "The Anatomy of Embedding Spaces" (the recommended option; "Latent" is dropped because Chapter 4 owns it by name). Applied: the H1, the roadmap heading, the `SKILL.md` example and the title in `MASTER_PARTS`; the label is unchanged. The rejected-ideas entry "Retitle Chapter 3 to drop Latent, or fix embedding/latent as a rule" is now to be reworded: the retitle was adopted, the fixed rule was not.
- **D14. Is an autoencoder a generative model?** **Answered by the plan, to be reviewed.** Strictly no: its decoder generates a point from a code, but nothing says which codes are valid, so it defines no distribution to sample from or to score; with a prior (the variational autoencoder) it does. Loosely yes, and that is how the word is often used. The plan keeps the autoencoder in Chapter 3 (it is the generalisation of the SVD that the chapter already proves, and the author's own idea 2 of `notes/ideas.qmd`) and opens Chapter 4 with the variational autoencoder; both chapters state the boundary. Alternative: make the autoencoder the first section of Chapter 4. Cost of switching: moving one stub section and its script.
- **D15. Taxonomy labels** (author, steering of 2026-11-11: "divide the chapters in Reconstructive, Predictive, Generative, and Hybrid, although generative seems to be hybrid"). **Open, with a recommendation.** Use the labels as the *Kind* column of the map (4.3) and not as four chapters. Reasons: (1) the kinds overlap (a VAE is reconstructive and generative; an autoregressive model is predictive and generative; JEPA is predictive in the code), so "hybrid" is not a fourth kind but the rows with two kinds, and "generative seems hybrid" is exactly what the table shows; (2) contrast is none of the three and needs its own label (*contrastive*, or *discriminative* in the literature); (3) four chapters would split the objectives that Chapter 3 compares on one data set, and the reconciliation needs them side by side. The two questions of the map (where the error is measured; whether there is a distribution) remain the criterion; the labels are the vocabulary.

- **D17. Size of Chapter 3** (author, 2026-11-11: "it is getting out of hand, from page 31 to 84; with the proposed sections it will be enormous, a book in itself"). **Closed: option (b), split at the natural seam** (author: "b seems better"). Measured before the split (PDF of 155 pages): Chapter 3 on pages 31 to 85, of which about 39 pages of text and exercises and about 16 of bibliography; the four plan stubs still to write were planned at 9 to 13 pages more. After the split (PDF of 156 pages): **Chapter 3, "Symbols Without Interior" (first called "Symbols Without an Interior: Why Exact Meaning Is Out of Reach"), 15 pages (31 to 45)**; **Chapter 4, "The Anatomy of Embedding Spaces", about 26 pages of text (46 to 71) plus the bibliography (about 15 pages, one list for the whole of Part I so far)**. Finished, Chapter 4 should come to about 33 to 38 pages of text. Option (a) (move "Learning by Reconstruction" to the generative chapter) was not chosen; it stays in Chapter 4, where the SVD it generalises is. Reopen (a) if Chapter 4 is still too long when its stubs are written.
- **D18. Titles and ids of the two chapters from the split.** **Closed** (author, 2026-11-11, from three short options he proposed: "Symbols without interior", "Symbols without Meaning and the Orthogonal Catastrophe", "Symbols and the Orthogonal Catastrophe"): **"Symbols Without Interior"**, the first and shortest. The first half is `chapters/symbols_without_interior.qmd`, label `sec-ch-symbols-without-interior`, tagged `definitive` (all its sections were untagged, that is definitive). The second half keeps `embedding_spaces.qmd`, its label and its title "The Anatomy of Embedding Spaces". The two other options remain available (the chapter also holds Shannon, Chomsky and Rice, which the title does not name; the Orthogonal Catastrophe is its central section). The text of the chapter says "symbols with no interior" in places; the title drops the article by the author's choice."

## 10. Order of work with quality gates

**How to read it.** Each step has *Do*, *Gate* (what must be true, and the command that shows it, before the next step starts) and *Status*. If a gate fails, fix it in the same step; do not start the next one. **Checkpoint** at the end of a step means: `git status` shows only the files listed for the step, and the author commits (the assistant does not commit unless asked). Gate results are written under *Result* with the date, so the plan is also the log.

Conventions of the gates:
- "Validate" is `make validate`; baseline of 2026-11-11: passes (0 errors) and every warning is of the kind "Bibliography entry '...' is not cited anywhere" (34 at the first run; 50 later the same day, because `references.bib` was edited meanwhile by the author). So the gate is: **0 errors, and no warning other than that kind** (`make validate 2>&1 | grep -v "not cited anywhere"` prints only the header, the file line for `references.bib` and the summary).
- "Status" is `make status`; baseline: the 14 chapter lines and the `index.qmd` line of the run of 2026-11-11 (3 definitive/provisional lines, 10 `idea` lines, the epilogue), no problems line. Saved as `tmp/baseline/status.txt`.
- "Durability" is `make durability`; baseline of 2026-11-11 (against the snapshot of 2026-11-10): `embedding_spaces.qmd: median year 2009 -> 2011, ... cites 27 -> 28`; `relative_wording: +1 new, -3 resolved`; `fashion_titles: +4 new, -4 resolved`. These two lists record `file:line`, so moving a title from the front matter to an H1 shifts lines and will change them without any new problem; Step F reads them case by case.
- "Tests" is `.venv/bin/pytest .github/skills/build-book/scripts/tests .github/skills/review-doc/scripts/tests -q`; baseline before Step D: all pass (the count before Step D was not recorded; after it: 124).
- "Text diff" is `python3 notes/text_diff.py extract <render> <dir>` then `... diff <before> <after>` (HTML directory, EPUB file, PDF file). The HTML extraction skips the raw `.qmd` that `code-tools` embeds in every page (a source listing, not text; without this a title moved to a heading would show as a difference). The PDF extraction compares the stream of words with hyphens and line breaks removed, because a reference typeset as `\ref` breaks lines differently from literal text; the running page header can still move by a word, which is read by hand. It was checked to be deterministic: two extractions of the same HTML, and of two PDF renders of the same source, are identical.

### Step A. Keep the plan  (section 0)
- **Do:** copy this plan and `tmp/emb_vs_lat.md` to `notes/`.
- **Gate:** `ls notes/generative_chapter_plan.md notes/emb_vs_lat.md` shows both; `diff tmp/emb_vs_lat.md notes/emb_vs_lat.md` is empty; `grep -n "tmp/" notes/generative_chapter_plan.md` shows only the intended mentions (the gitignore remark and the rejected idea).
- **Status:** done 2026-11-11.
- **Result:** both files in `notes/`; paths inside the plan updated to `notes/`. Not committed (the author commits).

### Step B. Baseline  (needed by the text diff of 0d)
- **Do:** run `make validate`, `make status`, and render HTML, EPUB and PDF from the current sources. Save the rendered text.
- **Gate:** all three renders end with "Output created"; the logs contain no "Unable to resolve crossref" or `?@`; the extraction is deterministic (see conventions); the sources of the baseline are saved in `tmp/baseline/` (chapters, `index.qmd`, `_quarto.yml`), because the working tree has uncommitted edits to `index.qmd` and `notes/ideas.qmd` that are not in any commit.
- **Status:** done 2026-11-11.
- **Result:** `make validate` passes with 34 warnings. HTML: 16 pages, 31 s. EPUB: 18 xhtml files, 12 s. PDF: 26 s, 388,369 bytes of text. Baseline text is in `tmp/baseline/text/{html,epub,pdf}`. Note: the working tree was not clean (`index.qmd`, `notes/ideas.qmd` modified), so the baseline is "the working tree of 2026-11-11 19:58", not a commit.
- **Checkpoint:** the author commits the working tree (including `notes/`), then Step 0 can be reviewed as one diff.

### Step C. Finish the pilot  (section 1a)
- **Do:** on a scratch copy of the repository (`/tmp`, deleted afterwards), test (1) the roadmap form `* **@sec-ch-x: Title.** *(idea)*` in HTML, PDF and EPUB; (2) an unresolved label in all three; (3) a ranged reference `Chapters [-@a] to [-@b]` in EPUB; (4) a chapter whose title is in a labelled H1 with the front matter holding only `status:` and `open:`, including how the page title, the heading and `_quarto.yml` order show it; (5) every kind of page: numbered chapter, `index.qmd`, epilogue, solutions.
- **Gate:** each case has a recorded outcome (renders as expected, or does not); D10 is decided from the outcome; the scratch copy is deleted (`ls /tmp | grep pilot` shows nothing).
- **Status:** done 2026-11-11.
- **Result:** (1) works in PDF and EPUB; in HTML only through the filter. (2) PDF: warning, exit 0; HTML without filter: warning, exit 0; HTML with filter: error, exit 1; EPUB not run separately (same Quarto crossref code as PDF; the Step F check of the log covers it). (3) works in EPUB. (4) works: the page title (`<title>`) and the chapter heading show "4 Vector Databases, RAG, ..." as before, and the front matter keeps `status:`; the sidebar was not inspected separately, and the text diff of Step F covers it. (5) The bug above in HTML, in `index.qmd`, the epilogue and `solutions.qmd`; fixed by the filter in all four kinds of page. The plan changed accordingly: filter added to 0a, log grep to 0e, D10 closed. The scratch copy was deleted; the prototype is `tmp/book-chapter-refs.lua`.

### Step D. Step 0, tooling first  (0a, 0e partly)
- **Do:** change `validate_book.py` (an H1 counts as the title; the lint for literal `Chapters? \d+`, off until the conversion), `durability_metrics.py` (roadmap by label, and the order check), `sync_chapters.py` (strip `{...}` from an H1 title); install the filter from `tmp/book-chapter-refs.lua` and register it for HTML; add the failing-log check to the Makefile. Each change comes with a test written first.
- **Gate:**
  - The tests of the three skills pass, and the new tests failed before the change (red first, then green).
  - `make validate` and `make status` on the *unconverted* book give the same result as the baseline (conventions above).
  - The filter, on the unconverted book (it has no `@sec-ch-` yet), leaves the text of the HTML, EPUB and PDF renders identical to the baseline: render, extract, `text_diff.py diff` against `tmp/baseline/text/*` (empty).
  - The scratch-book test of the filter passes (0a), including the two failure cases, each checked for the **message and a non-zero exit status**.
  - `make sync-chapters` leaves the `filters:` list of `_quarto.yml` untouched (`git diff _quarto.yml` shows only the filter line).
  - A broken label in a scratch copy of the repository makes `make epub`, `make pdf` and `make html` exit non-zero with a message; the same scratch copy without the broken label builds.
- **Status:** done 2026-11-11.
- **Result:**
  - `validate_book.py`: 4 of the 6 new tests failed on the old code (the other two guard behaviour that already held); one existing test (`test_validate_frontmatter`) encoded the old rule ("a level-1 heading is not a title") and was changed to a text with no heading at all. The lint `validate_chapter_references` exists, is tested (it skips fences and inline code, and flags comments) and is switched off by `LINT_LITERAL_CHAPTERS = False` until Step F.
  - `durability_metrics.py`: 7 new tests failed on the old code, all pass now. Roadmap entries are read as `Chapter N` or `@sec-ch-<stem>`; a chapter is found by label first, then by position; the new `roadmap_order_problems` makes an error of a roadmap in a different order than `_quarto.yml`, a repeated chapter, or a label that is not a numbered chapter. `make status` prints exactly the baseline.
  - `sync_chapters.py`: 1 new test failed on the old code (the title kept `{#sec-ch-...}`); `make sync-chapters` keeps the `filters:` line.
  - Filter `filters/book-chapter-refs.lua`, 4 tests (render a scratch book with Quarto; 14 s). **Correction to the pilot:** Quarto replaces the Lua global `error` by a function that only logs, so my "fails the build" of the pilot was true by accident (the next line crashed on a nil). The filter now stops with `os.exit(1)` after writing the message, and the tests assert both. Without the tests this would have shipped as a warning.
  - Makefile: `$(call render,<fmt>)` keeps the log in `.quarto/render-<fmt>.log` and fails on "Unable to resolve crossref". In a scratch copy with `@sec-ch-nonexistent` added to a chapter: `make epub`, `make pdf` and `make html` each exit 2 with the message; the same copy with the line removed: `make epub` exit 0.
  - Text diff of the three renders against the baseline: HTML 16 files, EPUB 18 files, PDF 1 file, **0 differ**. Tests: 124 passed.
  - Note: the working tree also contains edits by the author made meanwhile (`references.bib`, `.github/skills/review-doc/SKILL.md`, its packaging test, `index.qmd`, `notes/ideas.qmd`). They are not part of Step D; the baseline text was not affected by them.
- **Checkpoint:** `git status` lists, for this step, `sync_chapters.py`, `validate_book.py`, `durability_metrics.py`, their three test files, `test_book_chapter_refs_filter.py` (new), `filters/book-chapter-refs.lua` (new), `Makefile`, `_quarto.yml`. The author commits them (with Steps A and B) before Step E.

### Step E. Step 0, labels and conversion  (0b, 0c)
- **Do:** (1) take a fresh baseline B2: render HTML, EPUB and PDF with the tooling of Step D from the *unconverted* text and extract it to `tmp/baseline2/text/` (the author may have edited chapters since Step B, and B2 isolates the conversion from those edits and from the tooling); (2) write the conversion script (dry run first); (3) move the 13 titles to labelled H1s; (4) convert references.
- **Gate:** B2 exists and `text_diff.py diff tmp/baseline/text/<fmt> tmp/baseline2/text/<fmt>` is read (differences, if any, are the author's edits and are listed here); the dry run reports exactly the number of chapter numbers that a fresh count finds (206 on 2026-11-11: recount just before) and its list of changed lines was read in full; after the conversion `grep -rnE "Chapters? [0-9]" chapters/*.qmd index.qmd` finds nothing; every `@sec-ch-` used in the text exists as a label (`grep -oh "@sec-ch-[a-z-]*" chapters/*.qmd index.qmd | sort -u` against the 13 labels, computed from the file names); the book still validates and `make status` still prints the baseline.
- **Status:** done 2026-11-11.
- **Result:**
  - B2: rendered from the committed text with the tooling of Step D; its text equals the baseline B in HTML (16 files), EPUB (18) and PDF (the author's edits since Step B did not change any text).
  - Dry run (`tmp/convert_chapter_refs.py`): **197** chapter numbers in 14 files (13 chapters and `index.qmd`; a fresh `grep` count gave the same 197), 0 inside fenced code, 0 flags (no heading, link text, "Chapter N of" or possessive). The whole list (481 lines) was read; every converted number refers to the book's own chapters. Special cases seen and fine: the `open:` strings of the front matter and `<!-- OPEN -->` comments are converted too (they are not rendered); "Chapter 5, Chapter 13, and the Epilogue" and "Chapters 3 and 13" convert per number; `(Chapter 3, "Shannon's...")` gives `(@sec-ch-embedding-spaces, "Shannon's...")`.
  - Applied: 13 titles moved to `# Title {#sec-ch-<stem>}`, 197 numbers converted, front matter of all chapters still parses (`check`: 0 problems).
  - After: `grep -rnE "Chapters? [0-9]" chapters/*.qmd index.qmd` finds nothing; no leftover "and 13"-style numbers after a reference; no line starts with `(@` (pandoc example-list syntax); the 13 labels used equal the 13 labels defined and equal the file stems; `make sync-solutions`: up to date (the answers contain no chapter reference); `make validate`: 0 errors, only "not cited" warnings; `make status`: identical to the baseline.

### Step F. Step 0, the text must not change  (0d, 0e)
- **Do:** `make sync-solutions`, then render HTML, EPUB and PDF, extract the text, diff against B2; set `LINT_LITERAL_CHAPTERS = True` in `validate_book.py`; document the convention (write `@sec-ch-<file-stem>`; `[-@...]` after "Chapters"; no reference to sections from the index, the epilogue or the solutions) in `.github/skills/build-book/SKILL.md`.
- **Gate:** the text diff against B2 is empty for HTML (16 files), EPUB (18 files) and PDF; `make validate` has 0 errors and no literal-chapter warning; `make status` prints the baseline; `make durability` is read against the conventions above (line shifts of `relative_wording` and `fashion_titles` explained, no change in perishable counts or cites); `grep -c "?@" ` on the extracted text of the three formats is 0; the guard of Step D still fails on a broken label (spot check with `make epub` in a scratch copy).
- **Status:** done 2026-11-11.
- **Result:**
  - Text diff against B2 after the conversion: **HTML 16 files, 0 differ; EPUB 18 files, 0 differ; PDF 57,863 words, 1 differs**, and that one is the running header "3.12. Where a Single Vector Strains 63" swapping places with the word "(Chapter" at a page break; the sentence is the same. (The first comparison found 4 spurious differences: the embedded source in HTML and line breaks in PDF. The extractor was improved for them and B2 re-extracted; see the conventions.)
  - `?@` in the extracted text: 0 in the three formats. The three builds (`make html`, `make epub`, `make pdf`) ended with exit status 0 and no "Unable to resolve crossref".
  - `LINT_LITERAL_CHAPTERS = True`; `make validate`: 0 errors, no literal-chapter warning; new test `test_the_book_has_no_literal_chapter_numbers`. Documented in `.github/skills/build-book/SKILL.md` ("Referring to chapters", frontmatter example, check 8).
  - `make status` equals the baseline. `make durability`: against the old snapshot it shows `fashion_titles +13/-13` and `relative_wording +2/-4`; compared with the same metrics on the commit before Step E, **fashion titles 13 → 13, relative wording 2 → 2, perishable counts equal, cites per file equal, status equal**; the 13 lines differ only in format (`title: ...` → `# ... {#sec-ch-...}`, `Chapter 4:` → `@sec-ch-...:`). So the "+13/-13" is a format change that Step M's snapshot will absorb.
  - The guard (broken label makes `make epub`/`pdf`/`html` fail) was proven in Step D with the same Makefile and filter; it was not repeated.
  - `notes/ideas.qmd` (not rendered) keeps its literal numbers, now dated at the top. Tests: 125 passed.
- **Checkpoint:** the author commits Step 0 (files: 13 chapters, `index.qmd`, `validate_book.py` + test, `build-book/SKILL.md`, `notes/ideas.qmd`, `notes/text_diff.py`, the plan).
- **Checkpoint:** the author commits Step 0 on its own (conversion, labels, lint, docs).

### Step G. Decisions  (D1, D2, D4, D5, author)
- **Do:** the author answers.
- **Gate:** each decision is written in section 9 with date and choice before Step H; the structure of 4.3 and 4.4 agrees with the answers; an answer that could be read two ways is confirmed before it changes the files.
- **Status:** done for what Step H needs. D1 (title of Chapter 4), D2 to D10 closed. **Open for later steps:** D11b (contextual vectors and the vector-database chapter, Step I2), D13 (Chapter 3's title), D14 (autoencoder in Chapter 3, to be reviewed), D15 (the labels reconstructive, predictive, generative, hybrid).

### Step H. Insert the stub and register it
- **Do:** create `chapters/generative_spaces.qmd` (labelled H1, `status: idea`, eight section stubs), its roadmap entry, the hand-off lines of the Chapter 3 roadmap entry, the new stub "Learning by Reconstruction" `{.idea}` in Chapter 3, `sync_chapters.py` and its test; copy the book-level rejected ideas of section 12 to `notes/ideas.qmd`; run `make sync-chapters`. Also, at the author's request, one phrase on supervised and metric-learning embeddings in the contrast section of Chapter 3.
- **Gate:** `git diff _quarto.yml` shows only the new line, between `embedding_spaces` and `vector_databases`; the new test passes (the file maps to Chapter 4; `embedding_spaces.qmd` still to Chapter 3); `make validate` has no new error or warning kind; `make status` lists 15 chapter lines with the new one as `idea` and no tag disagreement; the HTML build passes.
- **Status:** done 2026-11-11.
- **Result:**
  - `chapters/generative_spaces.qmd`: working title "Latent Spaces from Generative Models" (D1), eight stub sections as in 4.3, `open:` note in the front matter. The new lint caught five literal "Chapter 3" in my own stub, which were replaced by `@sec-ch-embedding-spaces`.
  - `index.qmd`: new roadmap entry (idea) with its scale test and "Next:"; the Chapter 3 entry now lists five objectives and has the new "Next:" (a map against a distribution). The Part I intro, the "three devices" paragraph and the terminology note are Step I.
  - `chapters/embedding_spaces.qmd`: new section "Learning by Reconstruction" `{.idea}` (first placed between prediction and contrast, moved after the prediction of embeddings on 2026-11-11) (it states the boundary: an autoencoder generates from a code but defines no distribution, D14); one parenthetical sentence on labels, metric learning with pairs or triplets, and the penultimate layer of a classifier in the contrast section, with an HTML comment `REVIEW` next to it (no source yet; two candidates from memory, unchecked). Not yet changed in Chapter 3: its introduction ("in four ways"), the ledger of limits and its closing hook (Step I).
  - `sync_chapters.py`: new entry (num 4, patterns `generative_spaces`, `04_`, `chapter4`), later `num` and numeric patterns shifted by one; the test `test_match_future_chapter_patterns` was updated to the new positions and `test_generative_chapter_is_chapter_4_and_embedding_spaces_stays_chapter_3` added. `git diff _quarto.yml`: exactly one added line, in the right place.
  - `make validate`: 0 errors, only the "not cited" warnings; `make status`: 15 chapter lines (including the epilogue), the new one `idea`, Chapter 3 now "4 provisional section(s), 1 idea section(s)", no problems. `make html`: exit 0, no `?@`; the sidebar and headings read "4 Latent Spaces from Generative Models" and "5 Vector Databases, RAG, ...", the roadmap reads "Chapter 4: Latent Spaces from Generative Models". Tests: all pass.
  - `notes/ideas.qmd`: eight book-level rejected ideas copied under "Dropped ideas" (the retitle entry waits for D13).
  - Not run: PDF and EPUB builds (Step I's `make book`).
- **Checkpoint:** the author commits (the new chapter, the roadmap entries, `embedding_spaces.qmd`, `sync_chapters.py` and its test, `ideas.qmd`, the plan).

### Step I. Semantic edits and full build  (section 7, "Semantic edits")
- **Do:** make the edits of section 7 and run `make book` (the three formats).
- **Gate:** the build log has no unresolved reference; the rendered roadmap shows Chapters 1 to 14 in order; the text diff against the previous render differs only in the lines of the semantic edits (every distinct change read); `grep -n "fourth objective\|four objectives\|four ways" chapters/embedding_spaces.qmd index.qmd chapters/multimodal_embeddings.qmd` finds no stale count; Chapter 3 still validates and keeps its `definitive` tag.
- **Status:** done 2026-11-11, with Step I2 before it (the order was swapped because the author decided the move first).
- **Author's ruling:** the introduction of Chapter 3 and `index.qmd` are provisional text, so they may be edited; the `definitive` tag of the chapter concerns its settled sections.
- **Result:** 11 distinct changes in 5 files against the render of Step I2, all intended (the diff was read after a token-level comparison):
  - `embedding_spaces.qmd`: the introduction says "five ways" and lists reconstructing; it ends by pointing to @sec-ch-generative-spaces; the JEPA section is the "fifth objective" and its claim says "the five objectives" and adds reconstruction; its bitter-lesson line points to the scale test of Chapter 4; the contrast experiment says its `predict` model has a linear decoder and points to Chapter 4; the ledger of limits has a new first entry (a map says nothing about how likely a point is; a model that does has distances that mean only what its training made them mean) and now follows the order of the book (generative, contextual, vector databases, ...).
  - `index.qmd`: the terminology note now says the two words are interchangeable except where the literature settled on one (with examples), and that Chapter 3 leans on "embedding" and Chapter 4 on "latent"; the multimodal entry points to Chapter 4 for the debate between prediction in latent space and scaled generative models.
  - `multimodal_embeddings.qmd`: "The fourth objective of Chapter 3" became "The prediction of embeddings of Chapter 3", with a pointer to Chapter 4's scale test; `tangent_spaces_geodesics.qmd`: points to Chapter 4 for the pullback metric; `contextual_vectors.qmd`: the sparse autoencoder is an autoencoder (Chapter 3) with a sparse code.
  - `make html`, `make epub`, `make pdf` exit 0; no "Unable to resolve crossref"; `?@` count 0 in the three extracted texts; `make validate` 0 errors; 126 tests pass. Not done: the "Chapter 3 to 4" closing hook as a separate paragraph (the introduction and the ledger carry it).
- **Checkpoint:** the author commits.

### Step I2. Move the vector-database chapter  (D11)
- **Do:** change `MASTER_PARTS` (contextual vectors last in Part I; the vector-database chapter first in Part II) and its test, run `make sync-chapters`, edit the "Next:" lines of the neighbouring chapters, the Part intros, the roadmap order of `index.qmd` and the ranges of scale tests. Also the Chapter 3 retitle (D13).
- **Gate:** `make status` has no order problem (the roadmap lists the chapters in the order of `_quarto.yml`, a check built in Step D); the text diff against the Step H render differs only in the numbers of the moved chapters, the Chapter 3 title, the hand-off lines and the part intros (every distinct change read); every cross-reference still resolves (`?@` count 0 in the three formats); the ranges "Chapters N to 14" start at the first chapter with a scale test.
- **Status:** done 2026-11-11.
- **Result:**
  - `_quarto.yml` (by `make sync-chapters`): Part I = properties, curse, embedding spaces, generative spaces, contextual vectors; Part II = vector databases, tangent spaces, graph embeddings, topological deep learning.
  - Text diff against the HTML of Step H (57 distinct changes, read all): the Chapter 3 title in sidebars and headings; the numbers 5 and 6 swapped for the two chapters, with their section numbers (5.1 to 5.9 and 6.1 to 6.6) and every cross-reference to them in the epilogue, the multimodal, properties-of-meaning and curse chapters (checked by token: only `Chapter 5`↔`Chapter 6` and two ranges); the roadmap (contextual vectors now before the Part II heading, vector databases after it); the new Part I and Part II intros; the "Next:" lines. Nothing else.
  - **One error found and fixed by the diff:** the ranges "Chapters 4 to 14" of the "three devices" paragraph and of the epilogue hook were typed with the vector-database chapter as first endpoint and had become "5 to 14" and then "6 to 14", which dropped the new chapter and contextual vectors, both with a scale test. They now start at `sec-ch-generative-spaces` and read "Chapters 4 to 14".
  - After that fix: `make html`, `make epub`, `make pdf` exit 0; no "Unable to resolve crossref" in the three logs; `?@` count 0 in the extracted text of the three formats; `make validate`: 0 errors; `make status`: no problem; tests: 126 passed.
  - Contextual stub: "The dot-product machinery of Chapter N inside the model" now points forward, so it reads "of retrieval (Chapter 6) inside the model".
  - Not done here (Step I): the Chapter 3 introduction ("in four ways"), its ledger entry and closing hook, the terminology note, the pointers in the tangent and contextual chapters. The Part II title "Structure in Vector Spaces" does not describe the retrieval chapter (D16).
- **Checkpoint:** the author commits.

### Step N. Split Chapter 3 at its seam  (D17)
- **Do:** cut `chapters/embedding_spaces.qmd` before "Counting Company"; the first part becomes `chapters/symbols_without_interior.qmd` (labelled H1, new introduction, bibliography left to the next chapter's list); the second keeps its file, label and title, with a new introduction; register the chapter in `MASTER_PARTS` (with the later numbers shifted) and test it; point every reference to a moved section at the new label; split the answers (the solutions file regroups by chapter).
- **Gate:** (1) the moved sections are byte-identical (checked by script on the two files against the original, apart from three reworded sentences that referred to "this chapter"); (2) the 26 answers regroup as 14 and 12 with identical text; (3) `make validate` 0 errors, `make status` no problem, 127 tests pass; (4) the three formats build with no unresolved reference and `?@` count 0; (5) the text diff against the render before the split, normalised for chapter, table, figure and exercise numbers and for the bibliography, shows only the intended lines (read every one); (6) every `@sec-ch-embedding-spaces` in the book was read in context (59 of them) and re-pointed when it meant a moved section.
- **Status:** done 2026-11-11.
- **Result:**
  - Files: `symbols_without_interior.qmd` (5 sections, Shannon to Rice, 14 exercises) and `embedding_spaces.qmd` (8 sections, counting to the ledger, 12 exercises); `sync_chapters.py` has the new entry (num 3, patterns `symbols_without_interior`, `interior`, `orthogonal_catastrophe`) and the later numbers shifted; a new test checks that each file is taken for its own chapter and that they are consecutive.
  - Reference edits (11 places): the staircase (roadmap and neurosymbolic stub), Shannon's boundary (contextual stub, properties chapter), relabelling invariance (cross-domain stub, two entries of the properties chapter), the hand-written dense table, Shannon's generator and the staircase in the epilogue hooks, and the n-gram models in the generative stub now point to `sec-ch-symbols-without-interior`; the other 48 stayed (anisotropy, ledger, counting, SVD, contrast, JEPA, analogy, hubness and so on belong to the embedding chapter).
  - Reworded sentences in the moved text: three in the second half ("Both the Orthogonal Catastrophe and Rice's theorem of Chapter 3...", "Shannon's word-pair generator, in Chapter 3...", "...of that chapter we wrote that predictor in linear algebra") and one in the first ("the next chapter starts by counting it").
  - Numbers: the answers of the 26 exercises regroup as 14 (symbols) and 12 (embedding), text identical after regrouping; exercises, tables and figures of the second half are renumbered by Quarto (4.1 to 4.12; Table 4.1 and so on), which is why the diff needed normalising.
  - **One error found by the PDF page count and fixed:** the first version gave the new chapter its own `{#refs}` block; in the PDF each block prints the bibliography accumulated since the previous one, so the same 98 entries appeared twice (172 pages instead of 156). The block was removed from the new chapter, as in Chapters 1 and 2; the HTML page of each chapter still lists its own references.
  - Not moved: the scripts of the first half stay in `code/embedding_spaces/` (and their figures in `figures/embedding_spaces/`), because they share `utils.py` and the data folder with the rest and no text names the directory.
  - Sizes: see D17.
- **Checkpoint:** the author commits. Next: Step J (scripts), which now builds on the chapter called "The Anatomy of Embedding Spaces" (Chapter 4).

### Step J. Scripts and experiments  (section 5)
- **Do:** write `code/embedding_spaces/reconstruct_digits_ae.py` (Chapter 4's "Learning by Reconstruction" rows), then `code/embedding_spaces/predict_embeddings_digits_jepa.py` (the JEPA rows), then `code/generative_spaces/generative_vs_maps_digits.py` (the rows of the generative chapter and the combined table), and run them.
- **Gate (each script):** it runs in about a minute (time it and write the figure here); its asserts pass; for the models shared with the contrast script (InfoNCE at N=128, `predict`), its numbers equal those of `tbl-contrast-digits` to the printed precision; the ranges over five seeds are reported; no claim is written yet. For the generative script, the beta rule is written in its header and applied before the retrieval numbers are printed. `make test-code` passes.
- **Status:** script 1 of 3 done 2026-11-11; the JEPA skeleton and the generative script are pending.
- **Result of script 1** (`reconstruct_digits_ae.py`, imports the contrast script, copies none of it; 57 to 64 s on this machine, run by `make test-code`; figure `figures/embedding_spaces/reconstruct_digits_ae.png`):
  - Reproduction (the gate): its `predict the other view` row gives retrieval 13.9% [11.7%, 15.2%], alignment 0.03, uniformity -0.28, offset 0.96, and its InfoNCE N=128 row gives 38.8% [36.7%, 41.0%], 0.28, -3.07, 0.10: the numbers of `tbl-contrast-digits`. The script asserts the retrieval of both rows and the offset and alignment of the first.
  - Eckart–Young (asserted): the linear autoencoder of the same view, trained 20,000 steps (Adam needs ten times the 2,000 of the other models to reach the optimum of a linear map), reaches the held-out error of the PCA with 16 components, 0.0266 [0.0266, 0.0266] against 0.0266, never below it (the theorem), and its decoder spans a subspace within 4.8 to 12.5 degrees of the principal one. At 2,000 steps it was 7.5% above the PCA and up to 88 degrees away on the weakest component: a convergence effect, not a failure of the theorem; this is why the longer run is used and documented.
  - Table of the script (mean over five seeds; held-out error per pixel to the other view / to the clean image; retrieval; effective rank of the codes): predict the other view 0.0869 / 0.0711, 13.9%, 9.5; linear AE same view 0.1407 / 0.1160, 10.8%, 15.0; linear AE other view 0.0888 / 0.0760, 8.1%, 10.4; AE other view 0.0859 / 0.0670, 15.4%, 13.0; AE same view 0.1450 / 0.1209, 10.3%, 14.2; denoising AE 0.1266 / 0.0243, 32.6%, 13.1; InfoNCE N=128: retrieval 38.8%, rank 11.8.
  - What the numbers show, to be examined in Step K and not yet claims: nothing trained to reproduce the pixels reaches the retrieval of the contrastive code, but the denoising autoencoder, whose target is the clean image, gets within about six points of it (32.6% against 38.8%) with much the lowest error to the clean image (0.0243); the autoencoders that copy their own noisy input (same view) do no better than raw pixels or PCA (10.3% to 10.8% against 11.1% and 10.2%) and carry the noise through; a nonlinear decoder helps a little over the linear read-out (15.4% against 13.9%, 0.0670 against 0.0711 to the clean image). The effective rank of the `predict` model (9.5 of 16) and its offset (0.96) are the narrow cone of Chapter 4's ledger. One source of the denoising result is that its target removes the augmentation noise and the shift is not undone; it would be fairer to say that the target decides what the code keeps.
  - The figure is the first version of figure (a): retrieval against the error to the clean image, one point per model and seed, with the InfoNCE retrieval as a line (it has no decoder). The version with a decoder trained on the frozen InfoNCE code is in the generative script.
- **Checkpoint:** the author commits.

### Step K. Prose and exercises, section by section
- **Do:** write each section from the script's output, apply the review-doc skill to it, then the next.
- **Gate (each section):** every number in the text appears in the script's output; `@fig-` and `@tbl-` resolve; the exercises reproduce the figures and the answers are in `::: {.answers}`; `make validate` is clean for the chapter; the review-doc checks (§15 Job B, opening and closing, §17 tags) have no finding. The tag stays `idea` or `provisional` until its evidence exists. Then decide D8.
- **Status:** pending.

### Step L. Sources  (section 8)
- **Do:** fetch and check the sources.
- **Gate:** `fetch_references.py` and `build_index.py` ran; every citation in the chapter resolves to a PDF, with the page found by `ground_check.py`; `make validate-citations` passes.
- **Status:** pending.

### Step M. Durability snapshot
- **Do:** after the author approves, `durability_metrics.py snapshot`.
- **Gate:** `make durability` shows no unexpected change against the new baseline; section 11 is fully ticked; the **[book]** rejected ideas are in `notes/ideas.qmd`.
- **Status:** pending.

## 11. Acceptance checklist

- [ ] The plan and `emb_vs_lat.md` are in `notes/`, committed.
- [ ] Step 0 done: no literal "Chapter N" left in `chapters/*.qmd` and `index.qmd`; the text diff of 0d was empty in HTML, PDF and EPUB; unresolved references fail the build; `make status` reads the roadmap tags.
- [ ] The new chapter is registered (`_quarto.yml`, `sync_chapters.py` with a test that it maps to Chapter 4 and Chapter 3 still maps to itself) and tagged `idea`, in the roadmap and in its own front matter.
- [ ] The rendered book shows Chapters 1 to 14 in order and no "?@sec-".
- [ ] The Chapter 3 hand-off, the ledger of limits and the Part I intro agree with the new chapter.
- [ ] The JEPA-against-generative question has one home (the scale test of Chapter 4); the JEPA mechanism stays in Chapter 3; Chapter 14 and Chapter 3 point to Chapter 4 for the debate.
- [ ] The embedding chapter has the new section "Learning by Reconstruction", after the prediction of embeddings, and counts five objectives everywhere (intro, roadmap, the closing claim of the reconstruction section).
- [ ] D11 is closed, and the vector-database chapter is where the author decided (Step I2).
- [ ] Chapter 4 ends with the reconciliation (4.3.7): one table over all the objectives of Chapters 3 and 4, an information-theoretic attempt at one view with every claim sourced, and a graded statement of where the two families are the same and where they are not; "not reducible to one objective" is accepted if that is what the sources and the experiment support.
- [ ] The introduction says that the two words are used interchangeably except where the literature settled on one, with examples (D8).
- [ ] The experiment includes Chapter 3's `predict` model as a row, and the script's numbers are the ones in the text.
- [ ] Each section has exercises that reproduce its figures.
- [ ] Citations are few, located and checked against the PDFs.
- [ ] `make validate`, `make test-code` and `make book` pass.
- [ ] Opening names the bet against the bitter lesson; closing states a dated reading or "undecided".
- [ ] The **[book]** rejected ideas of section 12 are in `notes/ideas.qmd`, each with why and reopen-if; ideas rejected during the work are added to section 12 as they come up.

## 12. Rejected ideas

These are ideas that came up while writing and reviewing this plan and were dropped, written in the format of `notes/ideas.qmd` (what, why, reopen if) so the same idea is not explored twice. The ones marked **[book]** are decisions about the book. Copy them to "Dropped ideas" in `notes/ideas.qmd` at step 5 of section 10, when the chapter goes in. The rest are about tooling or the experiment and stay here (and in `notes/` once section 0 is done).

### Put the generative material in Chapter 3 instead of a new chapter [book]
- **Dropped:** 2026-11-11.
- **Why:** Chapter 3 is `definitive` and already long (four objectives and a ledger of limits), and its question is how similarity becomes geometry. Reconstruction asks a different question (what distance means, and whether there is a way back), and Chapter 3 would lose its single thread.
- **Reopen if:** the new chapter is still under about 6 pages when it reaches `provisional`. Then merge it into Chapter 3 as a fifth objective, followed by the ledger.

### Leave the debate in the multimodal chapter, under JEPA [book]
- **Dropped:** 2026-11-11.
- **Why:** Parts II and III need the similarity-against-generation distinction (pullback metric in Chapter 7, decoding from CLIP in Chapter 14), and putting it last in the book means introducing it after its first use.
- **Reopen if:** D2 decides the debate's home is Chapter 14 after all. The *distinction* still stays in Chapter 4.

### Title the chapter after the methods or a fashion word [book]
- **Dropped:** 2026-11-11.
- **Examples:** "Latent Spaces", "Generative AI", "Autoencoders, VAEs and Diffusion".
- **Why:** the durability rule says a title names the question, not a method name that dates. A list of methods also turns the chapter into a survey.
- **Reopen if:** never for fashion words. A method name is fine if a method becomes the question itself (as with the SVD in Chapter 3).

### A survey of GANs and diffusion [book]
- **Dropped:** 2026-11-11.
- **Why:** both are fast-moving and outside the question. One page of dated history is enough to show that the two kinds of space work together.
- **Reopen if:** a later chapter needs a mechanism of diffusion (for example its latent geometry) as evidence. In that case, put it in that chapter.

### Gate Part II after the new Chapter 4's scale test [book]
- **Dropped:** 2026-11-11 (default of D6).
- **Why:** the Part II question is whether transformers find these structures unaided, and the contextual-vectors chapter answers it. The new chapter does not.
- **Reopen if:** the Chapter 4 scale test turns out to decide whether Part II's structures are needed (for example, if generation absorbs geometry by design).

### Keep renumbering by hand or script as the main path
- **Dropped:** 2026-11-11. It is now the fallback in section 6.
- **Why:** the roadmap expects chapters to be reshaped, merged or dropped, and each change would redo about 200 edits. Cross-references do it once.
- **Reopen if:** cross-references fail in one of the output formats and cannot be fixed.

### Leave `durability_metrics.py` unchanged in Step 0
- **Dropped:** 2026-11-11 (it was in the first draft).
- **Why:** it reads roadmap tags only from literal `* **Chapter N:` headings, so `make status` would stop checking tags without reporting an error.
- **Reopen if:** never.

### Convert `notes/ideas.qmd`, the skills and the README to cross-references
- **Dropped:** 2026-11-11.
- **Why:** none of them are rendered as part of the book, so the references would not resolve. Dated literal numbers are used instead.
- **Reopen if:** any of them is added to the book.

### Name the file `generative_latent_spaces.qmd`
- **Dropped:** 2026-11-11 (it was in the first draft).
- **Why:** `sync_chapters.py` matches by substring, and the first match wins, so the name would match Chapter 3's `latent_spaces` pattern and the file would be placed as Chapter 3.
- **Reopen if:** the pattern is removed from Chapter 3, or matching becomes exact.

### Compare a plain same-view autoencoder with InfoNCE on retrieval
- **Dropped:** 2026-11-11. It is kept as a reference row only.
- **Why:** InfoNCE is trained to be invariant to the augmentation, and a same-view autoencoder is not, so retrieval of the other view would measure the training data and not the objective. The main autoencoders reconstruct the other view.
- **Reopen if:** never as the main comparison.

### Present the autoencoder rows as new
- **Dropped:** 2026-11-11.
- **Why:** Chapter 3's `predict` model is already a cross-view autoencoder with a linear decoder, and it has a row in `tbl-contrast-digits`. Presenting the new rows as the book's first reconstruction result would be wrong, and the table would repeat itself.
- **Reopen if:** never.

### Tune β of the VAE for retrieval or for good-looking interpolations
- **Dropped:** 2026-11-11.
- **Why:** it would tune the experiment towards the story. β is fixed by a rule on reconstruction alone, before retrieval is computed.
- **Reopen if:** never. To show more than one β, report a sweep with all its values.

### Interpolate InfoNCE codes along a straight line
- **Dropped:** 2026-11-11. It is kept as a footnote.
- **Why:** the decoder of model 5 was trained on unit-norm codes. A straight-line midpoint has a norm below 1, so it is off-distribution by construction, and it would make the similarity code look worse than it is.
- **Reopen if:** never as the main measure.

### Use torch or jax for the experiment
- **Dropped:** 2026-11-11 (default of D9).
- **Why:** every script in `code/` is numpy with hand-written gradients. One library for one chapter is a new dependency for the whole book, and it changes how readers run the exercises.
- **Reopen if:** the VAE gradients in numpy grow longer than the rest of the script, or the run time goes well past a minute.

### Copy the InfoNCE code into the new script
- **Dropped:** 2026-11-11 (it was already excluded in the first draft).
- **Why:** two copies drift apart, and the shared table only holds if both chapters run the same code.
- **Reopen if:** never. Use the import or `utils.py` (section 5).

### Keep the plan only in `tmp/`
- **Dropped:** 2026-11-11.
- **Why:** `tmp/` is gitignored, and this plan and `emb_vs_lat.md` would be lost with a clean or a new checkout.
- **Reopen if:** never. Section 0 copies them to `notes/`.

### Reason "new Chapter 10 needs what a space can regenerate"
- **Dropped:** 2026-11-11 (it was in section 2, item 5, of the first draft).
- **Why:** nothing in the plan of the complex-plane chapter depends on decoding. It was a weak reason that made a strong list look weaker.
- **Reopen if:** that chapter's plan comes to use generative latent spaces.

### Rely on Quarto's own cross-references in every page
- **Dropped:** 2026-11-11 (the assumption of the first pilot and of the first draft of Step 0).
- **Why:** in HTML, pages without a chapter number (`index.qmd`, the epilogue, `solutions.qmd`) render `@sec-ch-x` as "3 Title" and ignore `[-@sec-ch-x]` (Quarto bug #14132). The first pilot only tried numbered chapters.
- **Reopen if:** Quarto fixes #14132 (milestone 1.12). Then delete `filters/book-chapter-refs.lua` and check with the text diff.

### Fix the HTML afterwards, by rewriting "3 Title" to "Chapter 3" in the rendered files
- **Dropped:** 2026-11-11.
- **Why:** the output does not say whether the source was `@x` or `[-@x]`, and ranges like "Chapters [-@a] to [-@b]" come out as "Chapters 3 Title to 4 Title". The Lua filter sees the source form.
- **Reopen if:** never.

### Keep literal numbers in `index.qmd`, the epilogue and `solutions.qmd`
- **Dropped:** 2026-11-11 (it was option B of D10).
- **Why:** `solutions.qmd` is generated from the answers in the chapters, so it receives the converted references and cannot keep literal numbers; the roadmap and the epilogue hold most of the 206 numbers, so renumbering would remain by hand where most of it is.
- **Reopen if:** never.

### Make the filter handle PDF and EPUB as well
- **Dropped:** 2026-11-11.
- **Why:** Quarto renders both correctly in every page (pilot), and a Link generated by the filter would lose the LaTeX cross-reference (`\ref`) and the EPUB internal link. Fewer formats, less to keep in sync with Quarto.
- **Reopen if:** Quarto's PDF or EPUB treatment of unnumbered pages breaks in a later version.

### Reference sections (`@sec-prop-*`) from the unnumbered pages
- **Dropped:** 2026-11-11 (no such reference exists today).
- **Why:** the same Quarto bug would render "1.1 Title" instead of "Section 1.1" in HTML, and the filter only covers chapters.
- **Reopen if:** a page without a chapter number needs to point at a section; then extend the filter to `sec-prop-*`, with the numbering taken from the headings.

### Move "Learning by Predicting Embeddings" (JEPA) from Chapter 3 to Chapter 4
- **Dropped:** 2026-11-11 (it was my reading of the author's first D2 answer, and was in the plan for about an hour).
- **Why:** the author's second answer is that Chapter 3 covers the predictive and reconstructive models and Chapter 4 the generative ones. JEPA is predictive, so it stays in Chapter 3; its debate with scaled generative models is the scale test of Chapter 4, where both are on the table. [book]
- **Reopen if:** the JEPA section grows so that Chapter 3 becomes unbalanced; then split it out, but into a section of Chapter 3's end, not into the generative chapter.

### Keep the vector-database chapter in Part I because it is already there
- **Dropped:** 2026-11-11 (author, D11, leaning).
- **Why:** it is an application of embedding and latent spaces, not a fundamental technology; Part I is about what a space is and how it is built. Which part receives it is open. [book]
- **Reopen if:** the roadmap shows that the later chapters depend on its limits (the dot-product limits of the ledger) so much that they need it before Part II.

### Fix "embedding for Chapter 3 and latent for Chapter 4" as a rule
- **Note (2026-11-11):** D13 was closed with the retitle "The Anatomy of Embedding Spaces"; what is dropped is only the fixed rule. To be copied to `notes/ideas.qmd` at the next checkpoint with its reason.
- **Dropped:** 2026-11-11 (author, D8).
- **Why:** the SVD has been called "latent" in the literature for decades (LSA), and the literature does not keep the words apart; a fixed rule would be wrong for that case. The rule the book states is the author's: interchangeable, except where the literature has settled on one word for a context. [book]
- **Reopen if:** a reader test shows the two words confuse more than they help.

### State that embedding and latent spaces are one thing, with one objective
- **Dropped:** 2026-11-11 (before it was written).
- **Why:** it is a claim that the sources may not support (a bound on mutual information does not fix the geometry, and there is published criticism of the mutual-information view of contrastive learning). The consolidation is graded and sourced instead (4.3.7). [book]
- **Reopen if:** the sources read in Step L support a stronger statement.

### Write the consolidation before the sources are read
- **Dropped:** 2026-11-11.
- **Why:** every statement of 4.3.7 about bounds comes from memory. The section is a stub until Step L has fetched and read them, and the plan lists them as unchecked.
- **Reopen if:** never.

### Mix numpy and torch in the same table without saying so
- **Dropped:** 2026-11-11.
- **Why:** models 0 to 5 must reproduce Chapter 3's numbers with Chapter 3's code; if one row uses torch, the script says so in its header and the seeds and initialisation are not comparable bit by bit. Only a model that is clearer in torch (the VAE, JEPA) may use it, and the table reports it.
- **Reopen if:** never.

### Move "Learning by Reconstruction" to the generative chapter to make Chapter 3 smaller
- **Dropped:** 2026-11-11 (option (a) of D17; the author chose the split (b)).
- **Why:** the split removes 15 pages from the embedding chapter by itself, and the autoencoder belongs next to the SVD it generalises. Moving three pages would not have solved the size. [book]
- **Reopen if:** the embedding chapter is still too long when its stubs are written.

### Give the new chapter its own bibliography block
- **Dropped:** 2026-11-11 (it was in the first version of the split).
- **Why:** in the PDF the book prints, at each `{#refs}`, the references accumulated since the previous block, so the same 98 entries were printed twice (172 pages against 156). Chapters 1 and 2 have no block either.
- **Reopen if:** the book moves to a single bibliography at the end, or to Quarto's per-chapter bibliographies in the PDF.

### Put "Learning by Reconstruction" between prediction and contrast
- **Dropped:** 2026-11-11 (it was where I first inserted the stub; the author noticed that contrast continues prediction mathematically, and asked for the order that minimises the novelty of each section).
- **Why:** the contrast section opens from the softmax problem of prediction and reuses its loss; reconstruction needs the contrast experiment (its `predict` model is the first row of the reconstruction script) and the SVD, and leads to the next chapter, so it goes last. [book]
- **Reopen if:** the sections are written and the transitions read better the other way.

