---
name: review-doc
description: "Review book content — a portion of text, a chapter, a git-incremental change set, or the whole book — for structure, style, grammar, cross-references, citations, referenced documents validation, factual accuracy, question/solution completeness, code consistency, notation, translation sync, and chapter-to-chapter continuity, the book's thematic contract, the consistency of its working claims (book, chapter, section) with the evidence gathered so far, whether each method's claimed advantage agrees with comparisons at scale in the literature, and rolling durability (Lindy) feedback. Always starts by clarifying the scope (unit and range). Use when: reviewing, auditing, or proofreading text, reviewing what changed since a commit/date, checking whether the book's direction still fits the accumulated evidence, or checking consistency between language versions."
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
5. **Book-level contract** — the book's own statement of what every chapter must do and how chapters hand off to each other (for this book, the roadmap in `index.qmd`: one paragraph per chapter and its "Next:" hand-off). If none exists, skip §15. **The contract fixes form, not conclusions.** This book is an exploration with no thesis to defend: the roadmap is a plan, i.e. a set of hypotheses about where the evidence will lead, and it may be wrong. See §17.
6. **Notation summary** — the book's own list of symbol and typeface conventions (for this book, "Mathematical Notation & Conventions" in `index.qmd`). If none exists, skip §16.
7. **Status annotations and durability snapshot** — each chapter is `definitive`, `provisional` or `idea` (front matter `status:`, or a class on the H1), sections may carry `{.provisional}` or `{.idea}`, the roadmap in `index.qmd` mirrors the chapter tags, and `open:` fields or `<!-- OPEN: ... -->` comments hold undecided questions. Dropped ideas live in `notes/ideas.qmd`, outside the book. Run `make status` and `make durability` once at the start. Chapters without a status are treated as `provisional`.

Read the full unit under review (not just isolated diff hunks) before commenting, so feedback accounts for surrounding context. For a paragraph/section-level review, skip checks that don't apply at that granularity (e.g. whole-chapter structure, index terms) and note which ones were skipped and why.

### Change policy (minimal intervention)
A review audits; it does not rewrite. The author's text is the default and must stay as written unless there is an objective reason to change it.
- **Order of work: fix first, then report.** Pass 1 applies the fixes in the first list below, in this order of priority: syntax, grammar, non-idiomatic usage, correctness. Pass 2 reports everything else. Do not start pass 2 items before pass 1 is done and listed.
- **Apply directly** (only inside the unit and range under review), always as the smallest edit that keeps the author's words:
  - **Syntax**: broken or mistyped cross-reference/citation syntax, unbalanced markup, math, divs or code fences, unambiguous markup errors.
  - **Grammar**: typos and misspellings; agreement, tense, article, preposition and punctuation errors with one obvious fix; inconsistent spelling of a term, number format or decimal separator against the book's own convention.
  - **Non-idiomatic usage**: calques and wrong collocations or prepositions where one natural form exists; and colon misuse (see §3), fixed by swapping the punctuation only.
  - **Correctness**: a factual or technical error (date, name, attribution, number, formula, notation) whose corrected value is verified against a source in `references/` or another cited source. Cite the source in the applied-fix entry. If the correct value is not verifiable, or the fix would change what the author argues, report it instead.
- **Never apply a removal proposed by the pay-off step (§19)**: a section or chapter that may not pay off is reported as a proposal to discuss, and nothing is removed until the author and the reviewer agree; an agreed removal goes to `notes/ideas.qmd` with the reason.
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
- Sections should flow into each other. Flag a missing link only when the reader would actually be lost (see below); an opening or closing that already connects, in whatever form the author chose, is fine and is not to be made formulaic. Read the last paragraph of the preceding section and check that the first sentence of the current one picks up from it: no dangling demonstratives ("That", "This", "These") whose antecedent sits in an earlier section, and no abrupt change of topic. When the link is missing, propose an opening sentence that restates what the previous section established. Check the closing bridge against the actual first lines of the next section, not against its title. A section's opening says what will happen in it, besides picking up the previous section (the promise), and its ending reports on that promise in the same terms, naming only the strands that are relevant to the section among **meaning** (what the representation can now express), **computation** (what it costs, how it scales) and **limits** (what it cannot do). No strand is required: often one is enough, sometimes none beyond the bridge, and a strand with nothing to say is left out and never filled. Judge by content, not wording or length. Report only when the reader would be lost or when the ending does not answer the opening; if the section turned out differently from its announcement, the ending should say so.
- The same logic applies between consecutive chapters: the first paragraph of a chapter must pick up from the last paragraph of the previous chapter (no dangling references to material the reader has not just seen), and the chapter's closing paragraph must set up the opening of the next one. Read both chapter boundaries (end of the previous chapter, start of the next one) whenever a chapter is reviewed, and check that any "next chapter" announcement matches what the next chapter actually opens with.
- Preserve existing anecdotes, humour, and authorial voice.
- **No empty erudition.** The book exists to help the reader grasp ideas, not to display the author's learning. Flag every name-drop, historical aside, quotation, philosophical or cross-disciplinary reference, and passing technical term that the argument does not need, or that is mentioned without being explained. For each one answer two questions: (a) does the next step of the argument depend on it? (b) is it explained well enough that a reader who has never met it learns something usable? If (a) is no, propose cutting it, or moving a one-line pointer to the further-reading section. If (a) is yes but (b) is no, propose a plain-language explanation in place of the bare name or term. Typical symptoms are a thinker, theorem, or venue appended to a sentence with no consequence for what follows, a quotation that is not unpacked, jargon dropped in passing, and a closing clause that points at a deeper topic without a purpose. Report these as should-fix and show the answers to (a) and (b); do not apply them silently, since they touch voice. This does not conflict with preserving anecdotes and humour, which are kept when they make an idea easier to remember or to follow.

### 3. Grammar and usage
- Fix grammar/typos without altering style (see Change policy); keep terminology, numbers, and decimal-separators consistent across text, math, and figures.
- Flag unnatural phrasing (calques, wrong prepositions) and punctuation errors (parentheticals, dashes, ellipses, locale quotes); fix those with one natural form, report the rest; match dialogue/monologue to character voice and scene register.
- **Colon misuse.** The colon is a punctuation mark with a few jobs, not the default joint between a clause and its explanation ("X is Y: it does Z"). Treat that pattern as non-idiomatic usage. Count colons per section and fix the pattern where it recurs, and also single instances that are plainly wrong (a colon splitting a verb from its object, or after a preposition or "such as"). Fix by swapping the punctuation only, keeping the author's words. The default is a period, with the next word capitalised. A semicolon is kept for quasi-enumerations (items of a series, or parallel clauses that read as a list), never as the plain replacement of a colon. A comma or a dash is used only where a period would leave a fragment. If the period would start a sentence with a math symbol (the book does start sentences with code spans), or the fix needs a new word ("because", "so", "which") or a recast clause, that is a rewrite: report it with the proposed text and do not apply it. Report the density per section either way. Colons are correct, and left alone, when they:
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
- **Locators.** A page locator (`[@key, p. N]`) is for books only, where nothing else points a reader to the passage. For a paper, cite the key alone: a page number is an accident of the PDF version and reads oddly. A specific claim attributed to a paper (a theorem, number or benchmark) is still checked, by restricting `ground_check.py` to its PDF with `--doc` (the `file =` field), and the text may name the theorem, table, figure or section ("Table 1") when that helps the reader. The page stays the evidence unit of the grounding tool, so the report may cite a page for a paper; the book text does not. Without a locator in a book citation the grounding check cannot be targeted and degrades to a corpus-wide search.
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
- Own experiments are smoke tests and carry no ranking at scale; claims of one method beating another rest on cited comparisons at scale, checked in §19.4 with the parity audit above applied to the cited study.
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
- The declared hand-off ("Next:" line, or equivalent) of chapter N matches what chapter N+1 actually opens with, and chapter N+1's opening picks up from chapter N's close. The closing section of chapter N names what is still out of reach and which chapter ahead (or the Epilogue) takes it up; the roadmap's one-line "Next:" is the short form of that statement, and both must match what the next chapter opens with.
- Within a chapter, the beginning-end check of §2 holds for each section: its opening says what will happen and picks up the previous section, its ending reports on that promise (only the relevant strands among meaning, computation and limits, none required), and the bridge matches the next section's real first lines. The chapter's closing section synthesizes the section endings instead of adding new material.
- Recurring threads (the running example, the ledger of limits, the reasoning-in-the-space thread) stay coherent across hand-offs: nothing is dropped, redefined, or contradicted.
- Stubs are checked against the contract text, not for prose quality: the stub's sections and the roadmap must say the same thing. When both exist for one chapter, report any divergence and name which file is the source of truth for structure. For substance (what is claimed, what the chapter found) the order is evidence, then written chapters, then plan text (§17); a stub that disagrees with the roadmap because the evidence moved is a roadmap to update, not a stub to fix.
- "Next:" lines must match what the next chapter opens with, but a hand-off is a question that arose, not a step in a fixed argument. Never ask for a link that the evidence does not support.

**Job B — thematic contract (the chapters the contract names; for this book, Part I from Chapter 3 on, i.e. Chapters 3 to 6, and Part II, Chapters 7 to 15; state the range in these terms and not by number alone, since chapters move).**
- The opening says what the chapter will do and which limit it answers. The last section (a suggestive title: never "Conclusion", "Summary" or "Scale Test") says, in prose and in this order: what the chapter found, as findings and not as a verdict; what was achieved for the representation of meaning, citing the properties of Chapter 1 by `@sec-prop-*`; what computation did to it (cost, parallelism, improvement with scale), where the chapter's own findings say something about it, without the phrase "bitter lesson"; what is still out of reach and which chapter ahead takes it up; and, only where the chapter found one, a partial answer to the dog test or the critical literacy test. Dated and with its evidence class where it states a reading. "Undecided, and what would decide it" is a valid close; do not ask for a verdict the evidence does not reach.
- The opening and closing name the properties of meaning as geometry that the chapter develops, tied back to the Chapter 1 catalog by its `@sec-prop-*` anchors. Every anchor referenced exists. If the catalog anchors are not yet frozen, report Job B as blocked on that, not as a failure of the chapter.
- The bitter lesson is named only in the Prologue and the Epilogue. Elsewhere, cost and scaling are discussed in the terms of the approach (memory and cost per step, whether it parallelizes, whether it keeps improving with more data and compute, what it builds in that the data could have supplied). Nothing is added to state the alignment; checking it is the pay-off step (§19).
- Chapters outside the contract's range (for this book, 1 and 2) are audited for Job A only. The Epilogue follows neither the closing-section rule nor the section rule above; its first two sections (the dog test and the critical literacy test, revisited) collect the partial answers of the chapters, and its other sections start from a drawback of the existing approaches and are marked as speculation.

**Incremental scope.** Run Job A on every boundary the diff touches. Run Job B on a chapter only if the diff touches its opening, its closing section, or the contract text; otherwise list Job B as skipped and why.

**Mechanical hints (optional).** `grep` for `@sec-prop-` in the first and last section of each contracted chapter, and then two more: (a) the phrase "bitter lesson" or the name "Sutton" outside the allow-list (the Prologue and the Epilogue) is a hint to read; (b) a closing section titled "Conclusion", "Summary" or "Scale Test" is a hint to read. A hit or a miss is a hint to read the passage, not a finding by itself.

### 16. Notation
Applies to any unit with mathematical symbols, units, or code and figure labels that mirror them. Compare it with the notation summary (Setup item 6):
- **Typeface by kind**: the summary assigns scalars, vectors, matrices, and sets or manifolds their own typefaces; a letter used in the wrong typeface, or a typeface borrowed for another purpose (a calligraphic letter for a loss), is a mismatch.
- **Fixed conventions**: dimension letters, information symbols, logarithm base (and where training uses another base, that it is stated), inner product, norm and cosine forms, encoder and modality symbols.
- **Collisions**: for each symbol first used in the unit, grep the chapter, its neighbours and the stubs for other meanings (the same letter for two quantities is a finding even when the summary is silent).
- **Undefined symbols**: defined at first use and not in conflict with the summary; when a symbol recurs across chapters, propose adding it to the summary rather than renaming it in the text.
- **Mirrors**: identifiers in inline code, scripts, figure axes and legends use the symbols of the prose.
A mismatch with one obvious fix inside the unit is applied directly (Change policy, syntax); a rename that touches another section or chapter is reported with the exact before and after.

### 17. Inquiry integrity (the book is an exploration)
The book has no thesis to defend. **Questions are stable; answers are revisable.** What the book currently claims is a working reading, held on stated evidence until something would change it. The prose states the readings; the annotations below say how far the author stands behind each part. Ideas that are still alive stay in the book, tagged; there is no cost to having many, until they are dropped.

**Ground rules.**
- **Outcome-neutral.** Never judge whether the book reaches a particular conclusion, supports a thesis, or follows its plan. Judge only whether claim, evidence, stated confidence and prose agree. Either outcome of a test (a structure absorbed by scale, or demanded by the problem) is an equal result, and "undecided" is a valid state. Do not ask for a conclusion, a verdict, or a tidier arc.
- **Authority for substance: evidence, then written chapters, then plan text.** Departing from the roadmap is not a defect. A roadmap or stub that lags the evidence is a finding against the roadmap.
- **Report, do not rewrite.** Proposed hedges and annotation changes are given as diffs and land only on approval (Change policy).

**Status annotations.** `definitive`: the chapter should exist, and what is written is settled. `provisional`: it probably exists, but its shape or place is not settled. `idea`: a question, not yet a decision. A section class overrides the chapter status for that section. In scope:
- **Depth follows status.** `definitive`: all checks. `provisional`: §1, §4, §6, §8, §15 Job A, §17, §18 only. `idea`: judge design signals (the question, the sources chosen, the hedges) against the roadmap (§15 Job A) and §17, §18, and skip the rest, saying so in the scope block.
- **Tags must agree.** `make status` reports a roadmap tag that differs from its chapter, and a chapter with no tag.
- **Shape changes are visible.** A chapter or section added, removed, moved, retitled or re-tagged in the range is reported. Material that is dropped moves to `notes/ideas.qmd` with the reason and what would bring it back. Text that still leans on a dropped idea is stale. Do not re-raise a dropped idea; raise it when new evidence meets its "reopen if".
- **Decisions are the author's.** An `open:` field or OPEN comment states what is undecided, the options and how the evidence decides. When the evidence it names now exists, report "decision due" with the question, the options, and what the evidence says for each; do not choose. Prose that treats an undecided question as decided (an `idea` chapter's roadmap paragraph in the voice of a written chapter, a title that asserts what "revolution" means) is a roll-down finding.
- **Open ideas follow the classics.** `notes/ideas.qmd` keeps the open ideas sorted by Lindy alignment: classics (before 1980, held in `references/`, page read) that say the same thing, directly or by analogy, and classics that point against. A review re-reads each listed classic page, adds new evidence to the right entry, and re-sorts. An idea backed only by recent sources is explored later, and one with a classic against it is written as a test, not as a claim.
- **Arrival.** When a range starts a new chapter, ask: does its question still matter given what the written chapters found, is it answerable with sources or experiments that exist, and does it duplicate another chapter?
- **Open sets.** Where a list is open by design (Chapter 1's properties of meaning), never report a missing member as incompleteness. Report text that claims closure ("the properties are ..."); no search for new members recorded in the last 180 days, with a proposed way to look (an expert read, a survey search, what each later chapter needs from the space); a member with no source other than the author, or that no chapter tests; overlapping members (merge candidates); and a need of a later chapter that no member states.

**Checks on claims.** Take the claims of the unit (sections for a section, the chapter's opening and closing claims for a chapter, the Prologue and roadmap for the book) and ask:
1. **Roll-up.** A claim at one level is no more confident than the claims under it, unless independent lines converge (say why). Flag a chapter claim with no section carrying it, and a finding in a section that no chapter-level claim takes into account (a question may be emerging).
2. **Roll-down.** Openings, roadmap paragraphs, hand-offs and the Prologue must not state as settled what the sections below found open, caveated or contradicted. A caveat in a section that the opening still ignores is `should-fix`.
3. **Evidence arrival** (essential in incremental ranges). For every new or changed citation, number, script or figure in the range, name the claims it bears on and whether it supports, weakens or is neutral. Evidence that bears on a claim that stayed as it was is a finding; so is a claim that became stronger or weaker with no new evidence.
4. **Balance.** For each committed claim (a ranking of methods above all, checked against comparisons at scale in §19.4), is there evidence against, and has counter-evidence been searched for? If not, report it under the epistemic-boundary tier with the strongest opposing source or experiment you can name and two or three concrete search queries. Check that opposing evidence is represented fairly. A single-study, position or interpretive source is never the only support for a step, and small-N results carry N and status in the same sentence. Own experiments are held to the resource parity and protocol checks of §8.
5. **Calibration.** Compare modal strength with the evidence: "shows", "proves", plain "is" need a theorem, a primary historical fact, a replicated result or an own experiment; "suggests", "points to" fit weaker kinds. Prose stronger than the evidence is `should-fix` (propose the minimal hedge). Also check scope: a result on a toy corpus or one model family stated as a property of language or of vectors in general.
6. **Falsifiability.** A committed claim says, or lets the reader see, what would change it: the result that would reverse it. A claim no result could move is flagged. The pay-off step (§19) checks this too; it adds no text to the book.
7. **Direction of travel.** Use `git log -p` on the range for `index.qmd`, the chapter and `notes/ideas.qmd`. List claims that changed direction, questions added, dropped, reworded or reordered, and the evidence behind each. Watch for these patterns: every new source confirming; confidence rising with no new solid evidence; a question quietly reworded so that the answer fits; an idea kept alive after the evidence turned against it.
8. **Ripeness.** `idea` or `provisional` chapters whose evidence is now enough to tag up; chapters with much evidence gathered and no claim; closing sections without a date.

### 18. Durability (Lindy), rolling
How long a claim, source or framing stays true and useful. Distinct from §17: that asks how well supported a reading is now; this asks how long it will stay so. A claim that is long-lived but weakly supported is a candidate for exploration; a short-lived one held with high confidence needs a date. Durability findings are `suggestion` or `should-fix`, never `blocker`, and a perishable item is not wrong, only misplaced if it is undated or repeated. Baseline and rationale: `tmp/lindy_review.md` (2026-11-10), whose open actions are kept in `notes/ideas.qmd`.

**Shelf life by claim type.** Theorem or derivation, primary historical fact: indefinite, main text. Conceptual frame from an old tradition, replicated regularity: decades, with the scope in which it holds. Single-study or small-N result: uncertain, N and caveat in the same sentence. System or method description (CLIP, HNSW, RoPE, a specific model): 1 to 10 years, dated history in past tense. Position paper, forecast, contested hypothesis: attributed, with the test that decides it. The author's own synthesis: marked as such.

**Checks on the unit.**
1. Each perishable item sits in a sentence that dates it; limits are marked structural (theorem, counting argument) or contingent (how systems behaved at a date); no exercise's lesson depends on how good a current model is.
2. **Gradient.** Syntheses and endings must not rest on younger evidence than the middle. Use the per-file median year and the 2023+ count from the metrics (for a definitive chapter with provisional sections, its definitive part is reported separately).
3. **Titles.** Chapter and section titles name the question, not a fashion word (`fashion_titles` in the metrics). Titles are cross-referenced, so rename early.
4. **Organising bet.** A section organised around named methods ages with them; one organised around the durable question that they answered does not.
5. **One home per fast-moving claim.** Other places ask the question and point (`perishable` blast radius in the metrics). Reasoning in space or in text, JEPA, representation convergence, linear representation each have one home chapter.
6. **Contested hypotheses** (linear representation, Platonic convergence, sparse-autoencoder features) are attributed, with the test and what it found, never stated as findings.
7. **Credibility outside the author's field** (traditions read through translations and secondary works, clinical claims): specialist sources, "resembles" where the link is interpretive, "anticipated" only for a documented line of influence or an exact correspondence, and a domain read-through before publication.
8. Undated records and relative wording (`relative_wording` in the metrics); code dependencies limited to slow-drifting libraries; data pinned; gitignored `references/` and `tmp/` backed up.

**Rolling feedback.** Every review ends with a durability block: (i) metric changes since `notes/durability.json`, stated as improved or worsened with the numbers; (ii) the state of the open durability actions in `notes/ideas.qmd`, checking in the text whether "done" ones really are; (iii) up to three next actions ranked by low cost and high effect, as proposed new entries there. After the author approves the review, `durability_metrics.py snapshot` records the new baseline.

### 19. Pay-off step (a review step, never text in the book)
This replaces the "scale test" that earlier plans wrote into every chapter. No section, sentence or label is added to the book to answer it. For every section (and, for the third question, every chapter) that presents a method, a finding or a remedy, the reviewer infers the answers itself from the text, the ground truth (the cited sources, `references/`, the formal results) and its knowledge of the history and the state of the art at the review date, and reports each with its evidence. The questions:
1. **Scale.** Does the method align with computational efficiency and scalability: cost per step and memory, whether it parallelizes, whether it keeps improving with more data and compute, and what it builds in that the data could have supplied? Structural or contingent, dated (§17, §18).
2. **Durability.** Is what the section teaches a durable finding, worth learning (Lindy, §18): a theorem, a derivation, a replicated regularity or a question that has lasted, rather than a method that will be replaced?
3. **Does it solve the limit?** For the remedies of Part II and the proposals of the Epilogue (not Part I): does the remedy remove the limit it is presented against, fully, partly or not at all, and at what price (cost, a restriction of the case, a new limit it creates)? A proposal that is speculation is judged on whether it would remove the limit if it worked, and must say that it is speculation.
4. **Result.** Does the best evidence available at scale agree with what the text says about this method against the one before it (ranking, effect size, cost)? Locate the strongest comparison, in this order: a systematic review or meta-analysis; a controlled comparison run once data and compute were large enough; the authors' own comparison, which carries allegiance bias. Audit it under §8 (equal tuning and compute for the baselines, scale, date, full distributions over replicates) and compare it with the text. The book's own exercises and experiments are smoke tests. They can falsify (a loss that misses an analytic floor, a mechanism that fails), illustrate, and check how a cost grows with size, but they cannot rank methods at scale: the book does not have the compute, and a toy scale favours closed-form methods over those that need data. The text must not present them as if they did. The reviewer cannot verify the truth at scale either; it checks that the evidence exists, is represented fairly, and is dated and scoped (§18).

Reading the answers:
- Yes to question 1 or 2: the section pays off.
- No to both: the section, or the chapter if most of its sections fail, may not pay off. Report it as a proposal to discuss (`should-fix`) with its reasoning. Nothing is removed until the author and the reviewer agree (Change policy).
- A method that lost to scale can still pay off if why it lost is a durable finding (hand-built features against learned ones, one-hot tables against vectors). Durability is judged on what the reader learns, not on the method's survival, which keeps the review outcome-neutral (§17).
- Question 3 is not a pass or fail: "partly" and "not at all" are valid findings that the chapter's closing section reports as what is still out of reach.
- Question 4 is not a pass or fail either; it audits the sentences that rank, not the method. Report a ranking, effect size or cost claim with no located source (propose the citation, with a page locator only for a book, §6); a text stronger than its source or contradicting it (§17 calibration and roll-down); a smoke test presented as evidence of a ranking; and a smoke test that does not say what result would falsify it and in which direction scale is expected to bias it (§17.6). Evidence that is mixed is stated as mixed in the text. When no comparison at scale can be found, declare it an epistemic boundary with search queries; the text then says that none is known.
- Sections that present no method, finding or remedy (history that sets up a question, a bridge, an exercise) are not assessed. On an `idea` chapter the step is run on the plan only and reported as a `suggestion`.
- When the reviewer's answer and the text disagree (the text claims a method scales and the review finds it does not, or the reverse; the text says a limit is removed and the review says partly), that is a correctness finding (§8, §17 roll-down), reported separately from the pay-off.

## Output

**Report first, edit on approval.** A review run produces a report; apart from the fixes the Change policy lists under "Apply directly" (syntax, grammar, non-idiomatic usage, correctness), which are applied first and listed in the report, no prose is changed until the author approves specific items, after which each approved item lands as a separate minimal diff. Begin the report with the confirmed scope block from Setup.

Group findings into the 4-tier hierarchy:
1. **Tier 1: Fatal Blockers (Methodological, Mathematical & Factual Contradictions)** — must include explicit contrastive evidence `[Claim: ...] vs [Ground-Truth Evidence: ...]`.
2. **Tier 2: Major Methodological & Empirical Improvements (Should-Fix)** — structured with concrete, actionable remediation steps.
3. **Tier 3: Epistemic Boundary / 'Too Hard' Box** — explicitly declare unverified external claims, closed datasets, proprietary APIs/models, unindexed proofs, or offline prior art, paired with recommended verification queries.
4. **Tier 4: Minor Editorial, Typography & LaTeX Suggestions** — mechanical formatting and typo fixes.

For each finding: file/line reference, severity (blocker / should-fix / suggestion), and proposed correction (minimal, per the Change policy). List applied fixes (only those the Change policy allows) separately from items awaiting author decision, and keep style items in the latter with `suggestion` severity unless an explicit style-guide rule is broken. For whole-book reviews, group by chapter first, then by tier, with a cross-chapter summary.

**Where §17 and §18 findings go.** A text claim that the evidence contradicts is Tier 1 (`[Claim: ...] vs [Ground-Truth Evidence: ...]`). Prose more confident than the evidence, a broken roll-up, evidence that moved nothing, an unfalsifiable claim, durability gaps, a section that may not pay off (§19), and a ranking or "better/cheaper" claim with no located at-scale source or resting on a smoke test (§19.4) are Tier 2; a ranking that the cited at-scale source contradicts is Tier 1. Counter-evidence never searched for, and the absence of any comparison at scale, are Tier 3, with the queries. Moves with no stated reason and stale plan text are reported as requests to the author, not as defects of the text.

**Close every report with two blocks.**
1. **Direction report**, by level (book, chapter, section): claims touched; decisions due (`open:` fields and OPEN comments); changes of status and ideas moved to `notes/ideas.qmd`; proposed hedges and status changes as diffs; chapters ripe to re-tag; new questions the evidence suggests; plan text that now lags the evidence; the next evidence that would move the most (an experiment, a source, a counter-example to look for). State plainly when the direction still fits the evidence. It is not a finding that nothing moved.
2. **Durability block** (§18).
