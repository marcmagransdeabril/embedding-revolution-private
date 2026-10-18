---
name: ground-truth-review
description: "Audit factual, mathematical, empirical, attribution, architectural, and taxonomic claims against reference PDFs in references/ using page-level BM25 search and on-demand page evidence verification. Use when: auditing technical claims, fact-checking chapter drafts against references/, verifying citations or bibliography entries, searching references for theorems/definitions/benchmarks, or answering where a specific concept is established in the literature."
---

# Ground-Truth Review

Audit factual, mathematical, empirical, attribution, architectural, and taxonomic claims in book chapters against the authoritative literature in `references/`.

## When to Invoke (Triggers)

Invoke this skill whenever:
- **Factual & Technical Claim Verification**: Auditing mathematical theorems, bounds, proofs, equations, empirical benchmark numbers, architectural mechanisms, or historical attributions against primary sources in `references/`.
- **Chapter Draft Fact-Checking**: Reviewing chapter drafts or manuscripts (e.g. invoked from `review-doc` §6 Citations or §8 Factual accuracy) whenever substantive technical assertions are made.
- **Citation & Bibliography Grounding**: Verifying that cited literature in `references/` actually contains and supports what the text attributes to it.
- **Literature Lookups & Queries**: Answering questions regarding where a concept, theorem, definition, formula, or empirical result is defined or proved across the reference library.

## Environment & Python Execution

All indexing, search, and page-rendering tools execute using the repository Python virtual environment (`.venv`):
- **Python Executable**: Use `.venv/bin/python` for CLI invocations (or activate with `source .venv/bin/activate`).
- **Dependencies**: Built on lightweight PyMuPDF (`pymupdf`) and SQLite FTS5 with Porter stemming. No background daemons, GPU/VLM models, or external services are needed.

## Design Principles

- **Claims are never pre-indexed on the book side.** Only `references/` (ground truth) gets a persistent index. Claims in the chapter/paragraph under review are identified live, by reading the full unit under review (already required by `review-doc/SKILL.md`) and turning each discrete assertion into a short, term-dense query — favor specific technical noun phrases likely to appear verbatim in a source (`"circular convolution"`, `"capacity bound"`), not full conversational sentences.
- **Page text/snippets are candidate pointers, not evidence.** `ground_check.py` locates candidate pages; the reviewer must inspect the actual page (via `--render-page` image inspection or full page text) before asserting any verdict.

## Execution Procedure

### Step 1: Index Check / Build
Verify that `references/.ground-index/index.sqlite` exists and is up to date. If the database file is missing or if `references/` has changed (new PDFs added):
- Run the fast PyMuPDF index builder (indexes the full corpus in ~5 seconds):
  ```bash
  .venv/bin/python .github/skills/ground-truth-review/scripts/build_index.py
  ```

### Step 2: Live Claim Extraction & Query Formulation
For each discrete assertion in the text under review, classify its claim type and construct a concise, term-dense query (typically 2–4 key terms). Formulate queries tailored to how that claim type appears in literature across the 5 claim archetypes:

1. **Theoretical / Mathematical** (theorems, bounds, algebraic properties, asymptotic complexity, formal definitions):
   - Use named theorems, concept descriptions, invariant names, or key variable terms rather than raw LaTeX equations.
   - *Examples*: `"circular convolution" capacity bound`, `"tensor product representation" unbinding`, `"bias-variance decomposition"`.
2. **Empirical / Experimental / Benchmark** (reported metrics, baseline comparisons, dataset performance, ablations, scaling laws):
   - Use dataset/benchmark name + metric + model or condition.
   - *Examples*: `"GLUE" benchmark score`, `"ImageNet" top-1 accuracy`, `"BLEU" baseline comparison`.
3. **Attribution / Historical / Priority** (who introduced an idea/algorithm/framework, priority of discovery, naming origins):
   - Use author surname + seminal concept name + optional year/milestone.
   - *Examples*: `"Smolensky" "tensor product representation"`, `"Plate" "holographic reduced"`, `"Kanerva" "hyperdimensional"`.
4. **Architectural / Algorithmic / Implementation** (layer dimensions, binding/unbinding operations, activation functions, loss formulations, cleanup memory mechanisms):
   - Use specific component/operation names + mechanistic descriptors.
   - *Examples*: `"cleanup memory" associative`, `"Fourier transform" circular convolution`, `"Hadamard product" binding`.
5. **Taxonomic / Conceptual / Survey** (classification frameworks, paradigm comparisons, qualitative trade-offs):
   - Use taxonomy category name + classification dimensions.
   - *Examples*: `"neurosymbolic" taxonomy integration`, `"vector symbolic" binding properties`, `"representation" continuous symbolic`.

### Step 3: Candidate Retrieval (CLI & Python API)

**CLI Search**:
Run `ground_check.py` with the formulated query:
```bash
.venv/bin/python .github/skills/ground-truth-review/scripts/ground_check.py "<query>" [--top-k 5] [--doc <doc_stem>] [--floor <score>]
```
- `--top-k <N>`: Maximum number of ranked candidate hits to return (default: 5).
- `--doc <doc_stem>`: Filter search strictly to a specific document (e.g. `--doc 1990_tpr_seminal_paper`).
- `--floor <score>`: Score cutoff threshold (default: 0.0).
- **Synonym / Rewording Retry**: If `hits` is empty or returns `no_match`, retry with a reworded query (synonyms, alternate technical terms, broader/narrower phrases) before concluding absence. BM25 is lexical, so a single phrasing can miss a claim present under alternative terminology (e.g. "binding operator" vs "Hadamard product", "capacity bound" vs "crosstalk noise").

**Direct Python API** (for programmatic execution):
```python
from pathlib import Path
from scripts.ground_check import search_index

db_path = Path("references/.ground-index/index.sqlite")
res = search_index(db_path, query='"circular convolution" capacity bound', top_k=5)
for hit in res["hits"]:
    print(f"Doc: {hit['doc']}, Page: {hit['page_no']}, Section: {hit['section']}, Score: {hit['score']}")
```

### Step 4: Page Evidence Verification (Render Page to PNG)
Inspect the actual page content of candidate hits before asserting any verdict. Do not rely solely on snippet text:
- Render and view the high-resolution (150 DPI) page image:
  ```bash
  .venv/bin/python .github/skills/ground-truth-review/scripts/ground_check.py --render-page <doc_stem> <page_no>
  ```
  *(Saves rendered PNG to `references/.ground-index/renders/<doc_stem>_p<page_no>.png` for exact visual validation of formulas, proof details, tables, or diagrams.)*
- Alternatively, call `render_page_image(doc, page_no)` from Python.

### Step 5: Emit Findings & Severity Mapping (Integration with `review-doc/SKILL.md`)
Map verified evidence into review findings according to three verdict categories:

- **Supported** `(doc, page, section)`:
  - The claim is verified against the ground truth reference.
  - No error reported (optionally noted in the review summary as verified).
- **Contradicted** `(doc, page, what differs)`:
  - The source contradicts the claim in the draft (e.g. wrong bound, inverted relationship, misattributed discovery, inaccurate metric).
  - Emitted as **`blocker`** severity under §8 (Technical explanations and factual accuracy).
  - State the file and line, the exact claim in the draft, citation `(doc, page)`, what the source states, and the required correction.
- **Not found** (after synonym/analogy retries):
  - No reference in `references/` supports the assertion after thorough query reformulation and synonym searches.
  - Emitted as **`blocker`** severity under §8 (Technical explanations and factual accuracy).
  - State the file and line, the ungrounded assertion, report the nearest below-floor candidate (if any) or note that no matching reference exists, and require the author to supply a valid citation or revise the claim.

### Step 6: Multi-step Arguments
For multi-step mathematical derivations, algorithmic proofs, or conceptual chains:
- Verify each discrete step and assertion independently.
- Check for subtle term redefinitions, domain shifts, or dropped assumptions partway through the derivation.
