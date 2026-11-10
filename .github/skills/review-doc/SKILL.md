---
name: review-doc
description: "Review book content — a portion of text, a chapter, a git-incremental change set, or the whole book — for structure, style, grammar, cross-references, citations, referenced documents validation, factual accuracy, question/solution completeness, code consistency, notation, translation sync, and chapter-to-chapter continuity and the book's thematic contract. Always starts by clarifying the scope (unit and range). Use when: reviewing, auditing, or proofreading text, reviewing what changed since a commit/date, or checking consistency between language versions."
---

# Book Review

Book-agnostic review procedure, scalable from a paragraph to the whole book.

## Setup

### Step 0: clarify the scope (always first)

Before reading or judging anything, fix the scope of the review. Two independent choices define it. **If either is ambiguous from the user's request, ask before proceeding** — do not guess, and do not default to a full-book review. A request such as "review the book" or "review chapter 3" does not fix the range: ask for it.

1. **Unit** — the content boundary:
   - **Portion of text** — a passage the user designates: a paragraph, a heading and its subsections, or a line range (`file:start-end`). If they only point at a line, take the surrounding section.
   - **Chapter** — one chapter file (plus its code/tests/translation counterparts).
   - **Several chapters** — an explicit list or range of chapters, including a hand-off pair (end of chapter N plus start of chapter N+1).
   - **Whole book** — every chapter.
2. **Range** — how much of that unit to check:
   - **Incremental, latest saved changes** — uncommitted working-tree edits: `git diff -- <paths>` (add `--staged` too if anything is staged). Review only the changed hunks plus surrounding context.
   - **Incremental, last commit(s)** — `git log -1` or `git diff HEAD~<n>..HEAD -- <paths>`; ask how many commits if not stated.
   - **Incremental, since a given date/commit/tag/branch** — `git diff <ref>..HEAD -- <paths>`; for a date, resolve it first with `git rev-list -1 --before=<date> HEAD`.
   - **Full** — the entire current content of the unit, ignoring history.

Incremental ranges and a portion-of-text unit can be combined (e.g. "the changes since `main` inside the Shannon section").

**Confirm the scope in one short block before starting**, and proceed once it is unambiguous: unit, range (with the exact git command and base ref, or the line range), the files and hunks it resolves to, and which checks will be skipped as not applicable. If the diff is empty, say so and stop. If the user's reply to a scope question is "just do it", state the scope you chose and why, then proceed.

For any range narrower than "full", still read enough surrounding context to judge flow, and still run the full build/test step (§14) — changes can break things non-locally even when the diff is small. Widen the scope only for the boundary reads described in §2 and §15, and label anything outside the selected scope as out of scope.

**Incremental reviews and hand-offs.** A changed hunk can break a link to its neighbours without the neighbours changing. When a hunk touches the first or last paragraph of a section or chapter, or a "next chapter" announcement, also read the neighbouring paragraph on the other side of that boundary and check the link (§2, §15). When a hunk renumbers, renames, or moves a section or chapter, grep the rest of the book for references to the old name or number and report stale ones as out of scope for edits but in scope for the report.

Also establish, from `AGENTS.md`, the style guide, or an already-finished chapter:

3. **Canonical chapter skeleton** — expected section structure.
4. **Style guide** — audience, tone, language and locale.
5. **Book-level contract** — the book's own statement of what every chapter must do and how chapters hand off to each other (for this book, the global argument in `index.qmd`: one paragraph per chapter with its scale test and its "Next:" hand-off). If none exists, skip §15.
6. **Notation summary** — the book's own list of symbol and typeface conventions (for this book, "Mathematical Notation & Conventions" in `index.qmd`). If none exists, skip §16.

Read the full unit under review (not just isolated diff hunks) before commenting, so feedback accounts for surrounding context. For a paragraph/section-level review, skip checks that don't apply at that granularity (e.g. whole-chapter structure, index terms) and note which ones were skipped and why.

### Change policy (minimal intervention)
A review audits; it does not rewrite. The author's text is the default and must stay as written unless there is an objective reason to change it.
- **Order of work: fix first, then report.** Pass 1 applies the fixes in the first list below, in this order of priority: syntax, grammar, non-idiomatic usage, correctness. Pass 2 reports everything else. Do not start pass 2 items before pass 1 is done and listed.
- **Apply directly** (only inside the unit and range under review), always as the smallest edit that keeps the author's words:
  - **Syntax**: broken or mistyped cross-reference/citation syntax, unbalanced markup, math, divs or code fences, unambiguous markup errors.
  - **Grammar**: typos and misspellings; agreement, tense, article, preposition and punctuation errors with one obvious fix; inconsistent spelling of a term, number format or decimal separator against the book's own convention.
  - **Non-idiomatic usage**: calques and wrong collocations or prepositions where one natural form exists; and colon misuse (see §3), fixed by swapping the punctuation only.
  - **Correctness**: a factual or technical error (date, name, attribution, number, formula, notation) whose corrected value is verified against a source in `references/` or another cited source. Cite the source in the applied-fix entry. If the correct value is not verifiable, or the fix would change what the author argues, report it instead.
- **Never apply stylistic changes**: wording, sentence structure, paragraph order, tone, register, emphasis, transitions, rhythm, examples, humour, claims, and how much to cite or explain. These are reported as `suggestion` at most, and never edited without the author's approval, even when the author asks for the review to be "thorough".
- **Style is judged against the book's style guide and its finished chapters, not against the reviewer's taste.** Raise a style finding only when the text deviates from an established convention or hurts comprehension, and cite the convention or the passage that shows it. "Could be more engaging", "I would phrase it differently" and equivalent preferences are not findings.
- **Style findings are at most `suggestion`**, unless they break an explicit rule of the style guide (then `should-fix`). They never block.
- **Smallest possible change.** When a proposal is warranted, quote the exact span and offer the minimal edit that fixes the problem, keeping the author's words, rhythm and register. Do not reformat, reflow, re-wrap, re-number, or normalise untouched text, and do not mix unrelated edits into one change.
- **Stay in range.** Do not touch or comment on text outside the selected unit/range (beyond the context and boundary reads this skill requires). Pre-existing issues found outside it go in a separate "out of scope" note, not in the findings.
- **Be stable across passes.** Do not re-raise a finding the author has already declined or left unchanged after it was reported, and do not flip a previously accepted choice back and forth. A second pass on unchanged text must produce no new style findings; if it does, the first pass was incomplete or the new finding is preference.
- **When in doubt, report instead of editing**, and ask before anything touching voice, structure, or claims.

### Metacognitive Calibration & Claim Isolation
Evaluate empirical and logical claims strictly independent of prose length, rhetorical fluency, or formatting polish. Mentally isolate each atomic claim (point estimate, baseline comparison, or inference) from narrative framing before judging soundness. Treat superlative framing or high rhetorical confidence as an alert to verify underlying data and controls.

## Checks

### 1. Structure
Sections present, ordered, and labelled per the book's skeleton. Flag deviations; never restructure silently.

### 2. Style
- Tone, register, and difficulty consistent with the rest of the book. Flag only real inconsistencies with the surrounding chapters or style guide; do not push the text toward a different voice.
- No uninterrupted stretch of text longer than ~2 pages without a break.
- Sections should flow into each other. Flag a missing link only when the reader would actually be lost (see below); an opening or closing that already connects, in whatever form the author chose, is fine and is not to be made formulaic. Read the last paragraph of the preceding section and check that the first sentence of the current one picks up from it: no dangling demonstratives ("That", "This", "These") whose antecedent sits in an earlier section, and no abrupt change of topic. When the link is missing, propose an opening sentence that restates what the previous section established. Check the closing bridge against the actual first lines of the next section, not against its title.
- The same logic applies between consecutive chapters: the first paragraph of a chapter must pick up from the last paragraph of the previous chapter (no dangling references to material the reader has not just seen), and the chapter's closing paragraph must set up the opening of the next one. Read both chapter boundaries (end of the previous chapter, start of the next one) whenever a chapter is reviewed, and check that any "next chapter" announcement matches what the next chapter actually opens with.
- Preserve existing anecdotes, humour, and authorial voice.
- **No empty erudition.** The book exists to help the reader grasp ideas, not to display the author's learning. Flag every name-drop, historical aside, quotation, philosophical or cross-disciplinary reference, and passing technical term that the argument does not need, or that is mentioned without being explained. For each one answer two questions: (a) does the next step of the argument depend on it? (b) is it explained well enough that a reader who has never met it learns something usable? If (a) is no, propose cutting it, or moving a one-line pointer to the further-reading section. If (a) is yes but (b) is no, propose a plain-language explanation in place of the bare name or term. Typical symptoms are a thinker, theorem, or venue appended to a sentence with no consequence for what follows, a quotation that is not unpacked, jargon dropped in passing, and a closing clause that points at a deeper topic without a purpose. Report these as should-fix and show the answers to (a) and (b); do not apply them silently, since they touch voice. This does not conflict with preserving anecdotes and humour, which are kept when they make an idea easier to remember or to follow.

### 3. Grammar and usage
- Fix grammar/typos without altering style (see Change policy); keep terminology, numbers, and decimal-separators consistent across text, math, and figures.
- Flag unnatural phrasing (calques, wrong prepositions) and punctuation errors (parentheticals, dashes, ellipses, locale quotes); fix those with one natural form, report the rest; match dialogue/monologue to character voice and scene register.
- **Colon misuse.** The colon is a punctuation mark with a few jobs, not the default joint between a clause and its explanation ("X is Y: it does Z"). Treat that pattern as non-idiomatic usage. Count colons per section and fix the pattern where it recurs, and also single instances that are plainly wrong (a colon splitting a verb from its object, or after a preposition or "such as"). Fix by swapping the punctuation only: a period, a comma, a semicolon or a dash already used in the book, keeping the author's words. If the fix needs a new word ("because", "so", "which") or a recast clause, that is a rewrite: report it with the proposed text and do not apply it. Report the density per section either way. Colons are correct, and left alone, when they:
  - introduce an enumeration or a list item ("three levels: A, B and C");
  - introduce a formal definition, a quotation, or a displayed formula or example;
  - belong to titles, captions, labels, ratios, times, citations or code;
  - open a short, deliberate announcement where the payoff is the point ("The answer is simple: …"), at most once or twice per page.
  Text the reviewer writes (proposed edits, report, applied-fix notes) follows the same rule: no colon-as-joint.
- Do not propose rewrites merely to make prose more engaging; that is taste, not a defect.

### 4. Cross-references
- Every section/figure/table reference resolves to an existing target.
- Forward references in future tense, backward references in past tense.
- A reference to a distant figure or table also names its section, so the reader knows where to look.
- Citations (`@citekey`) are *not* cross-references and are governed entirely by §6 below — do not double-report a citation issue under both tiers.

### 5. Figures and diagrams
Every image path exists; every generated diagram has its source file; captions are meaningful and in the chapter's language.

### 6. Citations and referenced documents
- Every `@citekey` cited in the unit under review resolves to an entry in `references.bib` (run `make validate-citations`); every entry with a `file =` field points at an existing PDF in `references/`; every entry whose claims are load-bearing should have a `file =` field or an explicit note that no local copy is held. Keep inline citations minimal and prefer the further-reading section.
- **Citekey hygiene**: convention `surnameYYYYfirstword` (lowercase, no punctuation, trailing letter to disambiguate collisions), no duplicate keys, no orphan entries (an entry cited nowhere in the book — `make validate-citations` reports these).
- **Specific claims require page locators**: a theorem, number, or benchmark attributed to a citation must carry a locator (`[@key, p. N]`), because the downstream `ground-truth-review` evidence unit is the page — without a locator the grounding check cannot be targeted and degrades to a corpus-wide search.
- **Referenced document validation**: Validate each document referenced or cited in the unit under review:
  1. **Existence and indexing**: Confirm that the referenced document (PDF or transcript) exists in `references/` or is cataloged as an entry in `references.bib`, and is indexed in `references/.ground-index/index.sqlite` (run `python .github/skills/ground-truth-review/scripts/build_index.py` if missing or updated). Note the three-way naming: `references.bib` (the BibTeX database), `references/` (the PDF corpus), and `references/.ground-index/index.sqlite` (the BM25 index over that corpus) are three distinct things.
  2. **Bibliographic authenticity**: Verify the metadata (authors, title, year, venue, DOI/arXiv ID) against the actual publication to catch hallucinated, mangled, or misattributed citations (flag non-existent or hallucinated references as **`blocker`**).
  3. **Claim-to-source grounding**: Verify that each cited passage, theorem, formula, or empirical metric is genuinely supported by the referenced document (invoke `ground-truth-review` / `ground_check.py`, restricting the search to the resolved `file =` document via `--doc` when one is held). Flag contradicted or ungrounded citations as **`blocker`**.
  4. **Document integrity**: Ensure the source PDF in `references/` is valid, readable, and non-corrupted — `build_index.py` reports `Failed to open PDF` for corrupt files and warns about pages with no extractable text (a scanned/OCR-less PDF that BM25 retrieval cannot reach).
  5. **Primary source attribution**: Confirm seminal discoveries and primary formulations are cited directly rather than relying exclusively on secondary surveys.

### 7. Questions and solutions
- Every question has exactly one matching solution, in the same order, in the `::: {.answers}` block immediately after its `::: {.questions}` block in the same chapter file. `chapters/solutions.qmd` is generated by `make sync-solutions`: review the answers in the chapter, never in that file, and never edit it by hand.
- Use plain ordered lists in the source and let the build tooling generate numbering; never hardcode chapter numbers.
- Solutions concise (1–4 sentences); hints or pseudocode for coding tasks.

### 8. Technical explanations and factual accuracy
- Concepts explained before use, or carrying an explicit forward reference.
- Theory sections: strict ordering — only prior concepts, assumed background (with a short refresher), or inline definitions.
- Practical/introductory sections: early mentions are acceptable with an intuitive gloss or a forward reference, ideally both.
- Verify dates, attributions, mathematical and algorithmic properties, quantitative claims, and API/version statements against sources.
- Invoke the `ground-truth-review` skill when auditing factual, mathematical, or empirical assertions against `references/`.
- Both **Contradicted** and **Not found** findings from ground-truth review are classified as **`blocker`** severity in the review output.
- Report factual errors with the corrected value and source. Apply the correction when the Change policy allows it (verified against a source, no change to the author's argument) and list it as an applied fix with the source; otherwise report it. Never fix silently.
- For human, expert, or automated rating/evaluation studies, audit whether: (1) presentation order is counterbalanced across conditions (mitigating position/sequence bias), (2) evaluations are length- or volume-normalized to control for superficial verbosity/size bias, (3) scoring criteria are evaluated independently to prevent halo effects, and (4) evaluator/observer allegiance bias is mitigated via blinding or cross-condition masking.
- For search, screening, and multi-candidate generation tasks (convex payoffs), audit whether top-tail reach (k-max, top-decile yield, best-of-N outcomes) is evaluated or masked by central averages. Audit whether severe downside risks (p95/p99 tail latency, toxicity, catastrophic failure modes) are concealed by aggregate averages.
- Audit researcher degrees of freedom: (1) verify comparison baselines and controls received equal optimization/resource parity (compute, energy/GPU-hours, sample size, human-annotation labor, dosage, or monetary cost) rather than being tested in uncalibrated or handicapped configurations, (2) check whether custom post-hoc metrics replace pre-specified standard endpoints without validation, and (3) confirm reported gains reflect full distributions across independent replicates/seeds rather than cherry-picked runs on a Pareto frontier.
- Pre-Mortem (Inversion): Identify top 2–3 failure modes (e.g., regime/distribution shifts, boundary/edge-case inputs, saturation, degradation under stress) within claimed scope. Audit if boundary stress-tests are reported vs 'sunny-day' results. Credit declared limitations; avoid speculative out-of-scope critiques.
- Audit claims against first-principles and conservation/asymptotic bounds (physical laws, Shannon capacity, dimensional consistency, sample complexity lower bounds, hardware/bandwidth ceilings). Flag claims that mathematically or physically contradict declared experimental conditions or physical limits.
- Audit novelty and epistemic boundaries: verify claims of priority or unassisted discovery against external patents and prior art. When offline, declare an Epistemic Boundary with recommended search queries.
- Audit statistical consistency: (1) check test-statistic/df/p-value coherence (StatCheck), (2) verify discrete Likert/count means respect sample granularity (GRIM test), (3) verify FDR/Bonferroni corrections for multiple testing, (4) check SE scaling (SE ~ 1/sqrt(N)) and confidence interval overlap claims, and (5) confirm post-hoc findings are not presented as confirmatory hypotheses (anti-HARKing).
- Audit experimental protocol transparency: (1) verify verbatim prompt templates, system instructions, and generation hyperparameters (temperature, top-p, seeds) are disclosed, (2) check for stimulus contamination and few-shot exemplar leakage into test splits, (3) verify LLM-as-a-judge evaluations mitigate prompt framing demand characteristics, tone sycophancy, and position bias via neutral rubrics and counterbalanced controls, and (4) flag ungrounded persona role-play claiming unverified cognitive gains.

### 9. Markup
Correct callout/admonition usage; collect all `TODO`/`FIXME` comments into the report.

### 10. Acronyms
- Defined on first appearance as *Full Name (ACR)* or *ACR (Full Name)*, never used before definition — including in summary boxes and headings.
- Never redefined with a different expansion.
- Flag as **forced** (propose spelling it out) when two or more hold: used fewer than ~4–5 times; all uses clustered in one section; the abbreviation saves nothing over the plain term; not standard vocabulary for the target audience.

### 11. Code consistency
When executable code, pseudocode, algorithms, scripts, or computational models are present:
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
Run exactly what CI runs (CI workflow / `Makefile`): full render plus test suite. Review incomplete until both pass cleanly.

### 15. Book-level contract and hand-offs
Applies when the book declares a contract (Setup item 5) and the scope touches a chapter boundary, a chapter opening or closing, or the contract text itself. This is an editorial judgement about prose, never satisfied by inserting boilerplate; report a gap only when the passage does not do the job in whatever form the author chose.

**Job A — continuity (all chapters).**
- The declared hand-off ("Next:" line, or equivalent) of chapter N matches what chapter N+1 actually opens with, and chapter N+1's opening picks up from chapter N's close.
- Within a chapter, each section's first sentences pick up the previous section's last ones (same test as §2).
- Recurring threads (the running example, the ledger of limits, the reasoning-in-the-space thread) stay coherent across hand-offs: nothing is dropped, redefined, or contradicted.
- Stubs are checked against the contract text, not for prose quality: the stub's sections and the global argument must say the same thing. When both exist for one chapter, report any divergence and name which file is the source of truth.

**Job B — thematic contract (the chapters the contract names; for this book, Chapters 3 to 13).**
- The opening states the bet this chapter's structure makes against the bitter lesson; the closing gives the verdict (absorbed by scale, cheap, or demanded by the problem) and it follows from the chapter's own argument.
- The opening and closing name the properties of meaning as geometry that the chapter develops, tied back to the Chapter 1 catalog by its `@sec-prop-*` anchors. Every anchor referenced exists. If the catalog anchors are not yet frozen, report Job B as blocked on that, not as a failure of the chapter.
- Chapters outside the contract's range (for this book, 1 and 2) are audited for Job A only.

**Incremental scope.** Run Job A on every boundary the diff touches. Run Job B on a chapter only if the diff touches its opening, its closing, its scale test, or the contract text; otherwise list Job B as skipped and why.

**Mechanical hints (optional).** `grep` for `@sec-prop-` and for "bitter lesson" in the first and last section of each contracted chapter. A miss is a hint to read the passage, not a finding by itself.

### 16. Notation
Applies to any unit with mathematical symbols, units, or code and figure labels that mirror them. Compare it with the notation summary (Setup item 6):
- **Typeface by kind**: the summary assigns scalars, vectors, matrices, and sets or manifolds their own typefaces; a letter used in the wrong typeface, or a typeface borrowed for another purpose (a calligraphic letter for a loss), is a mismatch.
- **Fixed conventions**: dimension letters, information symbols, logarithm base (and where training uses another base, that it is stated), inner product, norm and cosine forms, encoder and modality symbols.
- **Collisions**: for each symbol first used in the unit, grep the chapter, its neighbours and the stubs for other meanings (the same letter for two quantities is a finding even when the summary is silent).
- **Undefined symbols**: defined at first use and not in conflict with the summary; when a symbol recurs across chapters, propose adding it to the summary rather than renaming it in the text.
- **Mirrors**: identifiers in inline code, scripts, figure axes and legends use the symbols of the prose.
A mismatch with one obvious fix inside the unit is applied directly (Change policy, syntax); a rename that touches another section or chapter is reported with the exact before and after.

## Output

**Report first, edit on approval.** A review run produces a report; apart from the fixes the Change policy lists under "Apply directly" (syntax, grammar, non-idiomatic usage, correctness), which are applied first and listed in the report, no prose is changed until the author approves specific items, after which each approved item lands as a separate minimal diff. Begin the report with the confirmed scope block from Setup.

Group findings into the 4-tier hierarchy:
1. **Tier 1: Fatal Blockers (Methodological, Mathematical & Factual Contradictions)** — must include explicit contrastive evidence `[Claim: ...] vs [Ground-Truth Evidence: ...]`.
2. **Tier 2: Major Methodological & Empirical Improvements (Should-Fix)** — structured with concrete, actionable remediation steps.
3. **Tier 3: Epistemic Boundary / 'Too Hard' Box** — explicitly declare unverified external claims, closed datasets, proprietary APIs/models, unindexed proofs, or offline prior art, paired with recommended verification queries.
4. **Tier 4: Minor Editorial, Typography & LaTeX Suggestions** — mechanical formatting and typo fixes.

For each finding: file/line reference, severity (blocker / should-fix / suggestion), and proposed correction (minimal, per the Change policy). List applied fixes (only those the Change policy allows) separately from items awaiting author decision, and keep style items in the latter with `suggestion` severity unless an explicit style-guide rule is broken. For whole-book reviews, group by chapter first, then by tier, with a cross-chapter summary.
