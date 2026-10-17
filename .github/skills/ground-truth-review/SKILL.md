---
name: ground-truth-review
description: "Audit factual, mathematical, empirical, attribution, architectural, and taxonomic claims against reference PDFs in references/ using page-level BM25 search and page evidence verification. Use when: verifying technical claims, fact-checking chapter drafts against references/, or auditing citations."
---

# Ground-Truth Review

Audit factual, mathematical, empirical, attribution, architectural, and taxonomic claims in book chapters against the authoritative literature in `references/`.

## Design Principles

- **Claims are never pre-indexed on the book side.** Only `references/` (ground truth) gets a persistent index. Claims in the chapter/paragraph under review are identified live, by reading the full unit under review (already required by `review/SKILL.md`) and turning each discrete assertion (theoretical, empirical, historical/attribution, architectural, or taxonomic) into a short, term-dense query — favor specific technical noun phrases likely to appear verbatim in a source (`"circular convolution"`, `"capacity bound"`), not a full sentence.
- **Page text/snippets are candidate pointers, not evidence.** `ground_check.py` only locates candidate pages; the reviewer must inspect the actual page (via `--render-page` image inspection or full page text) before asserting any verdict.

## Execution Procedure

### Step 0: Background Daemon Check
Check pidfile liveness for the background conversion daemon (`references/.convert-chunks/daemon.pid`). If pending chunks exist and the daemon is inactive or stalled:
- Launch one detached daemon instance before proceeding:
  ```bash
  systemd-run --user --scope -p CPUQuota=200% -p MemoryMax=4G -- python .github/skills/convert-references/scripts/convert.py --chunked --watch & disown
  ```

### Step 1: Index Check
Verify that `references/.ground-index/index.sqlite` exists and is up to date. If the database file is missing or if `references/` has changed (new PDFs added or chunk conversions completed):
- Run the index builder:
  ```bash
  python .github/skills/ground-truth-review/scripts/build_index.py
  ```

### Step 2: Claim Extraction & Query Formulation
For each discrete assertion in the text under review, classify its claim type and construct a concise, term-dense query (typically 2–4 key terms). Formulate queries tailored to how that claim type appears in the literature across the 5 claim archetypes:

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

### Step 3: Candidate Retrieval
Run `ground_check.py` with the formulated query:
```bash
python .github/skills/ground-truth-review/scripts/ground_check.py "<query>"
```
- **Synonym / Rewording Retry**: If `hits` is empty or returns `no_match`, retry with a reworded query (synonyms, alternate technical terms, broader/narrower phrases) before concluding absence. BM25 is lexical, so a single phrasing can miss a claim present under alternative terminology (e.g. "binding operator" vs "Hadamard product", "capacity bound" vs "crosstalk noise").

### Step 4: Page Evidence Verification
Inspect the actual page content of candidate hits before asserting any verdict. Do not rely solely on snippet text:
- Render and view the page image:
  ```bash
  python .github/skills/ground-truth-review/scripts/ground_check.py "<query>" --render-page <page_num> --doc <doc_stem>
  ```
- Alternatively, inspect the full page text or markdown transcript to verify equations, diagrams, surrounding assumptions, and context.

### Step 5: Emit Findings & Severity Mapping (Integration with `review/SKILL.md`)
Map the verified evidence into review findings according to three verdict categories:

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
