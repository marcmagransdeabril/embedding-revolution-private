# Plan: a new Part I chapter on similarity-trained and generative spaces

Date: 2026-11-11 (revised the same day after review). Status: plan only. Nothing in the book, the scripts or `_quarto.yml` has been changed for this chapter yet, apart from the terminology note already added to `index.qmd` ("Embedding Space or Latent Space?").

Background: `notes/emb_vs_lat.md` (gaps, errors, inconsistencies) and the discussion of 2026-11-11.

## 0. Before anything: keep the plan

**Done 2026-11-11.** `tmp/` is gitignored, so this plan and `emb_vs_lat.md` (whose comparison table section 4.3.1 reuses) were copied to `notes/` (outside the book, like `notes/ideas.qmd`). **This copy, `notes/generative_chapter_plan.md`, is the canonical one**; `tmp/generative.md` is only a pointer. They are untracked until the author commits them.

## 1. Decision summary

- **Add a new Chapter 4** to Part I, right after Chapter 3, tagged `idea`. File `chapters/generative_spaces.qmd`, label `sec-ch-generative-spaces` (D4; the name avoids the `latent_spaces` pattern of Chapter 3 in `sync_chapters.py`, see 7).
- **The durable question** (not a fashion word): *what does the training objective make distance mean, and can you get back from the vector to the data?* The chapter compares spaces trained for similarity (Chapter 3) with spaces trained to reconstruct or generate.
- **Old Chapters 4 to 13 become 5 to 14.** Chapters 1 to 3 keep their numbers.
- **Step 0 first (section 1a):** replace the hand-typed "Chapter 13" by Quarto cross-references, so Quarto numbers the chapters from `_quarto.yml` and the insertion needs no renumbering. A pilot on a scratch copy worked in HTML and PDF.
- **Tone and size.** Same register as Chapter 3, light on scholarship: few citations, each where it carries a number or a theorem. Length target 12 to 15 pages for the finished chapter.
- **Every section ends with exercises that reproduce its figures** (book rule), with a script under `code/generative_spaces/`.

Open decisions for the author are in section 9. The plan assumes the default in each.

## 1a. Step 0: replace text references to chapters by cross-references

**Idea (author, 2026-11-11).** Today the prose writes "Chapter 13" by hand: 206 chapter numbers (ranges and lists counted per number) in 13 chapter files, `index.qmd` and `notes/ideas.qmd`. Every insertion, merge or drop, which the roadmap expects ("continue, reshape, merge or drop"), would repeat the renumbering. With cross-references Quarto numbers the chapters from their order in `_quarto.yml`, and the text follows. No literal "Chapter N" in the book refers to an outside work (checked with grep), so the conversion has no false positives of that kind.

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
- **0b. Labels.** For each of the 14 numbered chapter files, move `title: "..."` to `# Title {#sec-ch-<stem>}`, where `<stem>` is the file stem with `_` replaced by `-` (`embedding_spaces` → `sec-ch-embedding-spaces`). The epilogue and solutions stay unnumbered and unlabelled.
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

1. Chapter 3 tells how similarity-trained vectors are built (counting, prediction, contrast, prediction of embeddings). The most common meaning of "latent space" in machine learning, the space of an autoencoder or generative model, is not in the book (gap 1 of `notes/emb_vs_lat.md`). Only sparse autoencoders appear (old Chapter 5, new 6).
2. Whether distance means anything depends on the objective. Chapter 1's first property, *nearness is likeness* (`@sec-prop-nearness`), holds by construction in a similarity-trained space and is not automatic in a reconstruction-trained one.
3. *Meaning can move: paths* (`@sec-prop-paths`) and the thread "reasoning as a path through the space" need a way to say when the midpoint of a path is meaningful. A decoder gives a check; a contrastive embedding does not.
4. The live scale question of the book, whether prediction in latent space scales as a general method or scaled generative models absorb it, is this distinction. It is planned for old Chapter 13 (new 14) under JEPA, and it needs a home before Parts II and III use it.
5. Later chapters build on it. New Chapter 7 (old 6, geodesics and curvature) needs the metric a decoder induces. New Chapter 14 (old 13, multimodal) needs the difference between what a space keeps and what it can regenerate, since text-to-image systems decode from a similarity-trained space.

## 3. Placement and numbering

| Old | New | File | Notes |
|:--|:--|:--|:--|
| 1 | 1 | `properties_of_meaning.qmd` | unchanged |
| 2 | 2 | `curse_of_dimensionality.qmd` | unchanged |
| 3 | 3 | `embedding_spaces.qmd` | unchanged; "Next:" line and ledger of limits change |
| – | **4** | `generative_spaces.qmd` | **new, `idea`** |
| 4 | 5 | `vector_databases.qmd` | |
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

Title candidates, all naming the question and none a fashion word (D1):
- "What the Objective Makes a Space Mean: Similarity, Reconstruction, and the Way Back"
- "Two Ways to Build a Space: Similarity and Generation"

Check the chosen title against the patterns of `MASTER_PARTS` in `sync_chapters.py` (matching is a substring test on stem *and* title, first match wins).

### 4.2 Opening and closing contract (review-doc §15 Job B)

- **Opening.** States the bet this chapter's structure makes against the bitter lesson, in the book's neutral voice. Draft: a decoder is built-in knowledge that a space must be able to regenerate its data. Scale may make it unnecessary (a similarity-trained space plus enough data suffices) or may make it dominant (generation is the general method). Neither is assumed.
- **Properties named, with anchors.** `@sec-prop-nearness`, `@sec-prop-paths`, `@sec-prop-arrangement`, `@sec-prop-invariance` (the invertible-matrix freedom of Chapter 3, exercise 22, and the rotation-symmetric prior of a VAE). `@sec-prop-direction` only if the latent-arithmetic material is kept.
- **Closing.** The chapter's current reading of its scale test, dated and with its evidence class, "undecided" being valid. The hand-off to Chapter 5 (4.4).

### 4.3 Sections

Each section is a stub at first (`idea`), written like the existing stubs (one italic paragraph of plan per section). Each finished section ends with the questions and answers blocks (`::: {.questions}` then `::: {.answers}`).

1. **The Fork: What Does Distance Mean?**
   One-page recap of what Chapter 3 built (similarity defines distance; no way back). Name the question. The Prologue's terminology note made precise in one table (the one drafted in `notes/emb_vs_lat.md`). Hook: Chapter 3's "Learning by Predicting Embeddings", which already drops the decoder, and Chapter 3's pixel predictor, which already keeps one (section 5).
2. **Reconstruction and the Bottleneck: The Autoencoder.**
   Pay for every detail through a small code. The linear case is the SVD of Chapter 3 ($\mathbf{M}\approx\mathbf{E}\mathbf{V}^\top$ is a linear encoder-decoder; Eckart–Young is `eckart1936approximation`). Nonlinear autoencoders; what the code keeps (what is needed to rebuild, brightness included) against what a contrastive code keeps (what separates). No guarantee that distance means anything.
3. **Giving the Space a Density: Latent Variable Models and the VAE.**
   The hidden-cause view (factor analysis, LSA's "latent", EM). The evidence lower bound as a reconstruction term plus a prior term. What the prior buys (sampling, smoothness) and costs (posterior collapse as the cousin of the dimensional collapse of Chapter 3; holes between the codes). Identifiability: the standard prior is rotation-symmetric, so the invertible-matrix freedom of Chapter 3 survives as a rotation freedom, and disentanglement is not free.
4. **Generation Without a Single Vector: GANs and Diffusion.**
   Dated history, past tense. Latent diffusion works in the latent space of a pretrained autoencoder, and conditioning typically comes from a similarity-trained encoder (CLIP). So the two kinds of space cooperate, and this is where Chapter 14's multimodal spaces meet generation. One page; the aim is the contrast, not a survey.
5. **The Geometry a Decoder Induces.**
   A decoder pulls a metric back onto the code space, so straight lines in the code are curved in the data, and the shortest path is a geodesic of the pullback metric. Anchor: `arvanitidis2018latent`. This is the one home of the pullback idea; Chapter 7 develops geodesics and points back. The same section answers *when is a midpoint meaningful*.
6. **Side by Side: What Each Kind of Space Keeps.**
   The comparison table (meaning of distance, decoder, density, off-data points, typical failure, geometry), each row marked *structural* (follows from the objective) or *contingent* (how systems behaved at a date), plus the experiment of section 5.
7. **Scale Test (dated 2026).**
   Question: as data and compute grow, does generation absorb similarity-trained spaces (a decoder everywhere), does prediction without a decoder absorb generation, or do both survive because they answer different questions (what you can get back, against what you can compare)? Evidence classes kept apart: a position paper (the JEPA argument), scaled generative results, and the chapter's own toy experiment, which is small and says so. Closing reading: undecided unless the evidence moves.

### 4.4 Hand-offs

- **Chapter 3 to 4.** New "Next:" line for Chapter 3: *similarity is one way to build a space; the other keeps a way back to the data.* The ledger of limits at the end of Chapter 3 gains one entry stated as a cost: a similarity-trained space has no way back, so nothing checks the points between; a generative space has a way back, but distance no longer has to mean similarity (home: @sec-ch-generative-spaces).
- **Chapter 4 to 5.** The old Chapter 3 hand-off moves here: *the first limit is practical, finding the nearest vector among billions.* The nearest-neighbour search of Chapter 5 applies to either kind of space.

## 5. Experiment and exercises (reproducible, reusing Chapter 3's toy)

Goal: put the comparison of 4.3.6 on the same data and metrics as Chapter 3's contrast experiment, so the two chapters share numbers.

**What Chapter 3 already has.** `contrast_digits_infonce.py` trains, besides InfoNCE, a `predict` model: the same encoder (64 → 128 → 16, ReLU) with a *linear* read-out of the unnormalised 16 coordinates, trained by squared error to produce the pixels of the *other* view. It is a cross-view autoencoder with a linear decoder, and it is already a row of `tbl-contrast-digits`. The new models are placed relative to it, not beside it as if new.

- **Data.** The 8×8 digits of scikit-learn, 1,200 training and 597 held-out images, the same split and augmentation (`augment`: shift of at most one pixel, Gaussian noise 0.15). Dimension $d=16$ for every model.
- **Training inputs.** Every model sees augmented views, as in Chapter 3. Autoencoders reconstruct the *other* view of the same image (a denoising, cross-view objective), so they are trained with the same invariance as InfoNCE and the retrieval comparison is fair. A plain same-view autoencoder is reported once as a reference row.
- **Models.** `numpy` with hand-written backward passes, like every script in `code/` (D9; no new dependency).
  0. Chapter 3's `predict` (linear decoder), imported, not retrained differently.
  1. Linear autoencoder (check against the PCA/SVD of the same dimension, already a baseline in Chapter 3).
  2. Nonlinear autoencoder (64 → 128 → 16 → 128 → 64): model 0 with a nonlinear decoder.
  3. VAE with a standard normal prior (same sizes). Retrieval and interpolation use the posterior mean. $\beta$ is fixed from the reconstruction alone (the largest $\beta$ whose held-out reconstruction is within a stated margin of model 2), *before* retrieval is computed, and the rule is reported.
  4. The InfoNCE encoder of Chapter 3 at $N=128$.
  5. Model 4 frozen, plus a decoder (16 → 128 → 64) trained on its unit-norm codes: the "way back from a similarity code".
- **Reuse.** Import `augment`, `forward`, `retrieval`, `alignment`, `uniformity`, `cosines` and the training of model 4 from `code/embedding_spaces/contrast_digits_infonce.py` (its top level only loads data; the run is under `if __name__ == "__main__"`). The import needs a path insertion; if that is too fragile, move the shared parts to `code/embedding_spaces/utils.py`, which the Makefile already treats as a helper of every script (`CODE_HELPERS`).
- **Measures** (mean over five seeds with [minimum, maximum], as in Chapter 3).
  - Reconstruction error on held-out images (pixel MSE).
  - Retrieval of the other view among the held-out views (Chapter 3's definition).
  - Alignment, uniformity and offset (same definitions).
  - Interpolation. For every model with a decoder, decode the midpoint between the codes of two held-out images and report its pixel distance to the nearest *training* image, against the same distance for the straight pixel average. For model 5 the midpoint is taken on the sphere (normalised), because the decoder was trained on unit-norm codes; the unnormalised midpoint is reported as a footnote to show the difference.
- **Figures** (saved in `figures/generative_spaces/`).
  - (a) Reconstruction error against retrieval, one point per model and seed: the "pays for every detail" against "pays for what separates" trade-off, read once the numbers exist.
  - (b) Interpolation strips for models 2, 3 and 5.
  - (c) The cosines or offsets, if needed to show a narrow cone for the autoencoder.
- **Table.** Default: extend `tbl-contrast-digits` in Chapter 3 with a pointer, and give Chapter 4 its own `tbl-generative-digits` that repeats rows 0 and 4 for reference. Both are filled from script output; no number is typed by hand.
- **Do not state results in the plan.** The prose and the answers are written after the script runs, and the numbers are copied from its output (as for `contrast_digits_infonce.py`).
- **Exercises** (3 to 4, each with an answer in the `::: {.answers}` block).
  1. Show that a linear autoencoder with squared error recovers the span of the top-$d$ singular vectors (link to Chapter 3's SVD and Eckart–Young).
  2. Write the evidence lower bound of a VAE with a Gaussian posterior and prior, and say what each term pays for.
  3. Why is the midpoint of two codes checkable for one kind of space and not for the other?
  4. The experiment, with the script name, run time and what to look at in each figure.
- **Script** `code/generative_spaces/ae_vs_infonce_digits.py`. It asserts its main numbers like the other scripts, runs in about a minute (measure; Chapter 3's script trains 25 encoders for 2,000 steps, this one trains 30 models, so parallelise like it with `ProcessPoolExecutor`), and saves the figures. `make test-code` picks it up through the wildcard `code/*/*.py`.

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
- `chapters/generative_spaces.qmd` (stub with the sections of 4.3, `status: idea`, labelled H1).
- `code/generative_spaces/` (the script; shared helpers go to `code/embedding_spaces/utils.py`, see 5).
- `figures/generative_spaces/` (written by the script).

**Registration**
- `.github/skills/build-book/scripts/sync_chapters.py`: `MASTER_PARTS` gets the new entry with `num: 4` and patterns (`"generative_spaces"`, `"generative"`), and the later `num` values and their `"0N_"`/`"chapterN"` patterns shift by one. Add a test in `tests/test_sync_chapters.py` that `generative_spaces.qmd` maps to Chapter 4 and `embedding_spaces.qmd` still maps to Chapter 3. (Had the file been called `generative_latent_spaces.qmd`, it would have matched Chapter 3's `"latent_spaces"` pattern, because matching is a substring test where the first match wins; if D4 brings that name back, remove `"latent_spaces"` from Chapter 3's patterns.)
- `_quarto.yml`: by `make sync-chapters`, not by hand.
- `.github/skills/build-book/SKILL.md` (file list), `.github/skills/review-doc/SKILL.md` ("Chapters 3 to 13" → "3 to 14"): these keep literal numbers (excluded from Step 0).

**Semantic edits** (what no numbering fixes)
- `index.qmd`
  - New Chapter 4 paragraph in Part I with its scale test and "Next:" line, tagged `*(idea)*`, not in the voice of a written chapter.
  - The Chapter 3 "Next:" line (4.4).
  - The Part I intro sentence: add that the way a space is built decides what its distances mean.
  - The "three devices" paragraph: the range of chapters closing with a scale test starts at the new Chapter 4 (`Chapters [-@sec-ch-generative-spaces] to [-@sec-ch-multimodal-embeddings]`).
  - The old Chapter 5 scale test ("which structures of Chapters 6 to 12"): check that the converted range still means Part II and III structures and not the new Chapter 4.
  - The old Chapter 13 roadmap entry: the JEPA scale question points to Chapter 4 (D2).
  - The `OPEN` comment on Parts II to IV: "after the Chapter 5 scale test" becomes a reference to `sec-ch-contextual-vectors` (D6).
- `chapters/embedding_spaces.qmd`
  - Closing "Next:" hook and the ledger of limits in "Where a Single Vector Strains" (new entry, 4.4).
  - The plan of "Learning by Predicting Embeddings": the JEPA mechanism stays; the debate moves to Chapter 4 (D2, D3).
  - The contrast experiment: one sentence pointing to Chapter 4 for the decoder side of the `predict` row.
- `chapters/multimodal_embeddings.qmd`: scale-test wording if D2 moves the JEPA question; pointers to Chapter 4.
- `chapters/tangent_spaces_geodesics.qmd`: point to Chapter 4 for the pullback metric instead of introducing it.
- `chapters/contextual_vectors.qmd`: sparse autoencoders now follow Chapter 4's autoencoder; add the pointer.

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
- Collapse and identifiability: Bowman and colleagues 2016 (posterior collapse in text VAEs); Locatello and colleagues 2019 (disentanglement is not identifiable without extra assumptions).
- Geometry of decoders: Shao and colleagues 2018; Lobashev and colleagues 2025 (Hessian geometry of diffusion latent spaces; perishable, date it if used).

Rules for use (the book's brief, discussion of 2026-11-10 on tone):
- Few citations, each at a number, a formula or a theorem. No name-drops without consequence.
- Methods told as dated history in the past tense; the question carries the chapter.
- A locator for every specific claim (`ground_check.py` finds the page).
- Run `fetch_references.py` for the new entries and `build_index.py` afterwards.

## 9. Open decisions for the author

- **D1. Title.** One of the two candidates in 4.1, or another that names the question.
- **D2. Home of the JEPA-against-generative debate.** Default: Chapter 4's scale test. Chapter 3 keeps the mechanism (collapse and how to avoid it), Chapter 14 keeps the image and video forms and the modality gap, and both point to Chapter 4 for the debate (one home per fast-moving claim).
- **D3. Does Chapter 3's "Learning by Predicting Embeddings" stay in Chapter 3?** Default yes: it is the last of four objectives for building embeddings. Only the *comparison with generation* moves.
- **D4. File name.** Default `generative_spaces.qmd` (avoids the Chapter 3 pattern collision, section 7). The title is independent of it.
- **D5. When.** Default: Step 0 now (it pays off whatever happens to the new chapter), then the chapter. Alternative: Step 0 only, and leave the idea in `notes/ideas.qmd` and the `OPEN` comment until the chapter is wanted.
- **D6. Part II gate.** The `OPEN` comment says Part II is decided after the Chapter 5 scale test (contextual vectors). With the new chapter that is the Chapter 6 test. Default: the gate stays on contextual vectors, not on the new Chapter 4. Confirm.
- **D7. Title in the heading.** Step 0 moves each chapter title from the front matter to a labelled `#` heading (the epilogue already does it). Confirm.
- **D8. Chapter 3's title.** "The Anatomy of Embedding and Latent Spaces" (tagged `definitive`) claims latent spaces, which the new chapter now owns in their generative sense, and the terminology note in `index.qmd` separates the two words. Options: keep it (the note says the book uses the words loosely), or retitle to "The Anatomy of Embedding Spaces". Old Chapter 9's "Wave-Nature in Latent Space" is the same question at a smaller scale. Default: keep both titles until Chapter 4 is `provisional`, then decide.
- **D9. Library for the experiment.** Default numpy with hand-written gradients, like the rest of `code/`. Adding torch or jax is a new dependency for the whole book; choose it only if the VAE makes numpy impractical.
- **D10. Roadmap headings (0a).** **Closed 2026-11-11: option A** (labels, `durability_metrics.py` updated). The bold-colon form renders correctly in PDF and EPUB, and in HTML through the filter (pilot, 1a). Option B (literal numbers) is no longer needed.

## 10. Order of work with quality gates

**How to read it.** Each step has *Do*, *Gate* (what must be true, and the command that shows it, before the next step starts) and *Status*. If a gate fails, fix it in the same step; do not start the next one. **Checkpoint** at the end of a step means: `git status` shows only the files listed for the step, and the author commits (the assistant does not commit unless asked). Gate results are written under *Result* with the date, so the plan is also the log.

Conventions of the gates:
- "Validate" is `make validate`; baseline of 2026-11-11: passes (0 errors) and every warning is of the kind "Bibliography entry '...' is not cited anywhere" (34 at the first run; 50 later the same day, because `references.bib` was edited meanwhile by the author). So the gate is: **0 errors, and no warning other than that kind** (`make validate 2>&1 | grep -v "not cited anywhere"` prints only the header, the file line for `references.bib` and the summary).
- "Status" is `make status`; baseline: the 14 chapter lines and the `index.qmd` line of the run of 2026-11-11 (3 definitive/provisional lines, 10 `idea` lines, the epilogue), no problems line. Saved as `tmp/baseline/status.txt`.
- "Durability" is `make durability`; baseline of 2026-11-11 (against the snapshot of 2026-11-10): `embedding_spaces.qmd: median year 2009 -> 2011, ... cites 27 -> 28`; `relative_wording: +1 new, -3 resolved`; `fashion_titles: +4 new, -4 resolved`. These two lists record `file:line`, so moving a title from the front matter to an H1 shifts lines and will change them without any new problem; Step F reads them case by case.
- "Tests" is `.venv/bin/pytest .github/skills/build-book/scripts/tests .github/skills/review-doc/scripts/tests -q`; baseline before Step D: all pass (the count before Step D was not recorded; after it: 124).
- "Text diff" is `.venv/bin/python tmp/text_diff.py extract <render> <dir>` then `... diff <before> <after>` (HTML, EPUB, PDF). It was checked to be deterministic: two extractions of the same HTML, and of two PDF renders of the same source, are identical.

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
- **Do:** (1) take a fresh baseline B2: render HTML, EPUB and PDF with the tooling of Step D from the *unconverted* text and extract it to `tmp/baseline2/text/` (the author may have edited chapters since Step B, and B2 isolates the conversion from those edits and from the tooling); (2) write the conversion script (dry run first); (3) move the 14 titles to labelled H1s; (4) convert references.
- **Gate:** B2 exists and `text_diff.py diff tmp/baseline/text/<fmt> tmp/baseline2/text/<fmt>` is read (differences, if any, are the author's edits and are listed here); the dry run reports exactly the number of chapter numbers that a fresh count finds (206 on 2026-11-11: recount just before) and its list of changed lines was read in full; after the conversion `grep -rnE "Chapters? [0-9]" chapters/*.qmd index.qmd` finds nothing; every `@sec-ch-` used in the text exists as a label (`grep -oh "@sec-ch-[a-z-]*" chapters/*.qmd index.qmd | sort -u` against the 14 labels, computed from the file names); the book still validates and `make status` still prints the baseline.
- **Status:** next.

### Step F. Step 0, the text must not change  (0d, 0e)
- **Do:** `make sync-solutions`, then render HTML, EPUB and PDF, extract the text, diff against B2; set `LINT_LITERAL_CHAPTERS = True` in `validate_book.py`; document the convention (write `@sec-ch-<file-stem>`; `[-@...]` after "Chapters"; no reference to sections from the index, the epilogue or the solutions) in `.github/skills/build-book/SKILL.md`.
- **Gate:** the text diff against B2 is empty for HTML (16 files), EPUB (18 files) and PDF; `make validate` has 0 errors and no literal-chapter warning; `make status` prints the baseline; `make durability` is read against the conventions above (line shifts of `relative_wording` and `fashion_titles` explained, no change in perishable counts or cites); `grep -c "?@" ` on the extracted text of the three formats is 0; the guard of Step D still fails on a broken label (spot check with `make epub` in a scratch copy).
- **Status:** pending.
- **Checkpoint:** the author commits Step 0 on its own (conversion, labels, lint, docs).

### Step G. Decisions  (D1, D2, D4, D5, author)
- **Do:** the author answers.
- **Gate:** each decision is written next to its default in section 9 (date and choice) before Step H. If D5 says "Step 0 only", stop here and record the idea in `notes/ideas.qmd`.
- **Status:** pending.

### Step H. Insert the stub and register it
- **Do:** create `chapters/generative_spaces.qmd` (labelled H1, `status: idea`, the sections of 4.3 as stubs), the roadmap entry, the hand-off lines, the ledger entry, `sync_chapters.py` and its test; copy the **[book]** entries of section 12 to `notes/ideas.qmd`; run `make sync-chapters`.
- **Gate:** `git diff _quarto.yml` shows only the new line, between `embedding_spaces` and `vector_databases`; the new test passes (the file maps to Chapter 4; `embedding_spaces.qmd` still to Chapter 3); `make validate` has no new error or warning kind; `make status` lists 15 chapter lines with the new one as `idea` and no tag disagreement.
- **Status:** pending.

### Step I. Semantic edits and full build  (section 7, "Semantic edits")
- **Do:** make the edits of section 7 and run `make book`.
- **Gate:** the build log has no unresolved reference; the rendered roadmap in HTML shows Chapters 1 to 14 in order and the PDF text has "Chapter 14" and no "Chapter 15"; the text diff against the Step F render differs only in the lines of the new chapter, the hand-offs and the semantic edits (read every differing line); each file of the "Semantic edits" list has a changed line, or a note here saying why not.
- **Status:** pending.
- **Checkpoint:** the author commits.

### Step J. Script and experiment  (section 5)
- **Do:** write `code/generative_spaces/ae_vs_infonce_digits.py` and run it.
- **Gate:** it runs in about a minute (time it and write the figure here); its asserts pass; for the models shared with Chapter 3 (InfoNCE at N=128, `predict`), its numbers equal those of `tbl-contrast-digits` to the printed precision; the ranges over five seeds are reported; the β rule is written in the script header and was applied before the retrieval numbers were printed (the code orders the steps this way); `make test-code` passes. No claim is written yet.
- **Status:** pending.

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
- [ ] The JEPA-against-generative question has one home, and the other chapters point to it.
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
