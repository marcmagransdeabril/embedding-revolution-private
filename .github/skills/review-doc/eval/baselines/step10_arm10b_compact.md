---
name: review_step10_arm10b
description: "Review skill variant for Step 10 Arm 10B (Compact Experimental Protocol Transparency & Demand Characteristics Checklist)."
---

# Book Review

Book-agnostic review procedure, scalable from a paragraph to the whole book.

## Setup

Two independent choices define what gets reviewed. **If either is ambiguous from the user's request, ask before proceeding** — do not guess.

1. **Unit** — the content boundary:
   - **Paragraph / section** — the specific passage the user points to (or the surrounding section if they only point at a line).
   - **Chapter** — one chapter file (plus its code/tests/translation counterparts).
   - **Whole book** — every chapter.
2. **Range** — how much of that unit to check:
   - **Latest saved changes** — uncommitted working-tree edits: `git diff -- <paths>` (add `--staged` too if anything is staged). Review only the changed hunks plus surrounding context.
   - **Last commit(s)** — `git log -1` or `git diff HEAD~<n>..HEAD -- <paths>`; ask how many commits if not stated. Review only the changed hunks plus surrounding context.
   - **Since a given date/commit/tag** — `git diff <ref>..HEAD -- <paths>`. Review only the changed hunks plus surrounding context.
   - **Full** — the entire current content of the unit, ignoring history.

For any range narrower than "full", still read enough surrounding context to judge flow, and still run the full build/test step (§14) — changes can break things non-locally even when the diff is small.

Also establish, from `AGENTS.md`, the style guide, or an already-finished chapter:

3. **Canonical chapter skeleton** — expected section structure.
4. **Style guide** — audience, tone, language and locale.

Read the full unit under review (not just isolated diff hunks) before commenting, so feedback accounts for surrounding context. Apply only uncontroversial fixes; ask before anything touching voice, structure, or claims. For a paragraph/section-level review, skip checks that don't apply at that granularity (e.g. whole-chapter structure, index terms) and note which ones were skipped and why.

### Metacognitive Calibration & Claim Isolation
Evaluate empirical and logical claims strictly independent of prose length, rhetorical fluency, or formatting polish. Mentally isolate each atomic claim (point estimate, baseline comparison, or inference) from narrative framing before judging soundness. Treat superlative framing or high rhetorical confidence as an alert to verify underlying data and controls.

## Checks

### 1. Structure
Sections present, ordered, and labelled per the book's skeleton. Flag deviations; never restructure silently.

### 2. Style
- Tone, register, and difficulty consistent with the rest of the book.
- No uninterrupted stretch of text longer than ~2 pages without a break.
- Each subsection opens by linking to the previous one and closes with a bridge to the next.
- Preserve existing anecdotes, humour, and authorial voice.

### 3. Grammar and usage
- Fix grammar and typos without altering style.
- Consistent terminology within the chapter and across chapters.
- Consistent number and decimal-separator formatting in text, math, and figures.
- Idiomatic phrasing: flag correct-but-unnatural wording, calques, wrong prepositions.
- Punctuation: parentheticals closed on both sides, correct dashes, ellipses, and locale-appropriate quotation marks.
- Dialogue and internal monologue match the character's voice and the scene's register.
- Suggest (don't apply) rewrites that would make the text more engaging.

### 4. Cross-references
- Every section/figure/table reference resolves to an existing target.
- Forward references in future tense, backward references in past tense.
- A reference to a distant figure or table also names its section, so the reader knows where to look.

### 5. Figures and diagrams
Every image path exists; every generated diagram has its source file; captions are meaningful and in the chapter's language.

### 6. Citations and referenced documents
- Every citation key exists in the bibliography; every empirical claim is sourced; keep inline citations minimal and prefer the further-reading section.
- **Referenced document validation**: Validate each document referenced or cited in the unit under review:
  1. **Existence and indexing**: Confirm that the referenced document (PDF or transcript) exists in `references/` or is cataloged in the bibliography, and is indexed in `references/.ground-index/index.sqlite` (run `python .github/skills/ground-truth-review/scripts/build_index.py` if missing or updated).
  2. **Bibliographic authenticity**: Verify the metadata (authors, title, year, venue, DOI/arXiv ID) against the actual publication to catch hallucinated, mangled, or misattributed citations (flag non-existent or hallucinated references as **`blocker`**).
  3. **Claim-to-source grounding**: Verify that each cited passage, theorem, formula, or empirical metric is genuinely supported by the referenced document (invoke `ground-truth-review` / `ground_check.py`). Flag contradicted or ungrounded citations as **`blocker`**.
  4. **Document integrity**: Ensure the source PDF in `references/` is valid, readable, and non-corrupted; if markdown conversion is used, verify document health with `convert-references` (`verify.py`).
  5. **Primary source attribution**: Confirm seminal discoveries and primary formulations are cited directly rather than relying exclusively on secondary surveys.

### 7. Questions and solutions
- Every question has exactly one matching solution, in the same order and the same file.
- Use plain ordered lists in the source and let the build tooling generate numbering; never hardcode chapter numbers.
- Solutions concise (1–4 sentences); hints or pseudocode for coding tasks.

### 8. Technical explanations and factual accuracy
- Concepts explained before use, or carrying an explicit forward reference.
- Theory sections: strict ordering — only prior concepts, assumed background (with a short refresher), or inline definitions.
- Practical/introductory sections: early mentions are acceptable with an intuitive gloss or a forward reference, ideally both.
- Verify dates, attributions, mathematical and algorithmic properties, quantitative claims, and API/version statements against sources.
- Invoke the `ground-truth-review` skill when auditing factual, mathematical, or empirical assertions against `references/`.
- Both **Contradicted** and **Not found** findings from ground-truth review are classified as **`blocker`** severity in the review output.
- Report factual errors with the corrected value and source; never fix them silently.
- For LLM-as-a-judge or human rating studies, audit whether: (1) presentation order is counterbalanced across conditions (mitigating position bias), (2) evaluations are length-normalized or controlled for verbosity bias, (3) scoring criteria are evaluated independently to prevent halo effects, and (4) model family self-enhancement is mitigated via blinding or cross-model evaluators.
- For search, generation, and multi-candidate tasks (convex payoffs), audit whether top-tail reach (k-max, top-decile yield, pass@k) is evaluated or masked by central averages. Audit whether severe downside risks (p95/p99 tail latency, out-of-distribution failure modes) are concealed by aggregate averages.
- Audit researcher degrees of freedom: (1) verify comparison baselines and controls received equal optimization/resource parity (compute, energy/GPU-hours, sample size, human-annotation labor, dosage, or monetary cost) rather than being tested in uncalibrated or handicapped configurations, (2) check whether custom post-hoc metrics replace pre-specified standard endpoints without validation, and (3) confirm reported gains reflect full distributions across independent replicates/seeds rather than cherry-picked runs on a Pareto frontier.
- Pre-Mortem (Inversion): Identify top 2–3 failure modes (e.g., distribution shift, out-of-vocabulary, memory/bandwidth saturation, adversarial fragility) within claimed scope. Audit if boundary stress-tests are reported vs 'sunny-day' results. Credit declared limitations; avoid speculative out-of-scope critiques.
- Audit claims against first-principles and conservation/asymptotic bounds (physical laws, Shannon capacity, dimensional consistency, sample complexity lower bounds, hardware/bandwidth ceilings). Flag claims that mathematically or physically contradict declared experimental conditions or physical limits.
- Audit novelty and epistemic boundaries: verify claims of priority or unassisted discovery against external patents and prior art. When offline, declare an Epistemic Boundary with recommended search queries.
- Audit statistical consistency: (1) check test-statistic/df/p-value coherence (StatCheck), (2) verify discrete Likert/count means respect sample granularity (GRIM test), (3) verify FDR/Bonferroni corrections for multiple testing, (4) check SE scaling (SE ~ 1/sqrt(N)) and confidence interval overlap claims, and (5) confirm post-hoc findings are not presented as confirmatory hypotheses (anti-HARKing).
- Audit experimental protocol transparency: (1) verify full verbatim prompt templates, system instructions, and generation hyperparameters (temperature, top-p, seeds) are disclosed, (2) check for stimulus contamination and in-context exemplar leakage into evaluation splits, (3) verify LLM-as-a-judge evaluations mitigate prompt framing demand characteristics, tone sycophancy, and position bias via neutral rubrics and counterbalanced controls, and (4) flag ungrounded persona role-play claiming unverified cognitive gains.

### 9. Markup
Correct use of the book's callout/admonition environments. Collect all `TODO`/`FIXME` comments into the report.

### 10. Acronyms
- Defined on first appearance as *Full Name (ACR)* or *ACR (Full Name)*, never used before definition — including in summary boxes and headings.
- Never redefined with a different expansion.
- Flag as **forced** (propose spelling it out) when two or more hold: used fewer than ~4–5 times; all uses clustered in one section; the abbreviation saves nothing over the plain term; not standard vocabulary for the target audience.

### 11. Code consistency
- Every script referenced in the text exists, and the prose matches what it actually does.
- Inline snippets may be excerpted or simplified but must not contradict the full script's logic or API.
- **Inline snippets are usually not executed by CI.** A passing build does not mean a snippet runs. Trace each snippet's calls against the tested source, or run it. Watch for "readable" simplifications the real API does not support (e.g. an operator the library doesn't implement) — verify method-level compatibility, not just mathematical equivalence.
- Comments in embedded samples must be in the chapter's language, even if the source scripts use another.
- If code is mirrored to another repo or package, confirm the mirrored copy matches the current tested version.

### 12. Index
Add terms introduced by the chapter; drop terms whose content was removed.

### 13. Translation parity
If another language version exists:
- **Structure** — same headings in the same order with the same anchors; same count of questions, figures, tables, code blocks, cross-references, and citations.
- **Content** — every paragraph has a counterpart, nothing silently added or dropped; if the source changed after translation, list the sections needing re-translation. Solutions must match.
- **Assets** — translated diagram sources and localized user-facing strings in code output exist.
- **Quality** — established target-language technical vocabulary, natural prose (not translationese), anecdotes and humour preserved or adapted.

### 14. Build and test
Run exactly what CI runs (check the CI workflow and `Makefile`): typically a full render plus the test suite. The review is not complete until these pass cleanly.

## Output

Group findings by check. For each: file and line reference, severity (blocker / should-fix / suggestion), and a proposed correction. For substantive and methodological findings, explicitly contrast the author's claimed conclusion against the raw empirical evidence (e.g. `[Claim: ...] vs [Evidence: ...]`). List applied fixes separately from items awaiting the author's decision. For a whole-book review, group by chapter first, then by check, and add a short cross-chapter summary (recurring issues, terminology drift, index/translation gaps spanning multiple chapters).
