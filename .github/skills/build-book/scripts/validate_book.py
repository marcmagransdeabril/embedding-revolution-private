#!/usr/bin/env python3
"""Validate Quarto book structure, markdown syntax, math blocks, and code chunks.

Audits index.qmd and all chapters/*.qmd files for frontmatter,
balanced callout blocks (:::), math delimiters ($$), code chunks,
and cross-reference labels.
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import Any

import yaml

from sync_solutions import (
    _ANSWERS_OPEN_RE,
    _QUESTIONS_OPEN_RE,
    SOLUTIONS_FILENAME,
    find_div_blocks,
    render_solutions,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
CHAPTERS_DIR = REPO_ROOT / "chapters"
INDEX_QMD = REPO_ROOT / "index.qmd"
REFERENCES_BIB = REPO_ROOT / "references.bib"
REFERENCES_DIR = REPO_ROOT / "references"


_UNNUMBERED_H1_RE = re.compile(r"^# .*\{[^}]*(?:\.unnumbered|-)[^}]*\}\s*$")

# Chapter references are written @sec-ch-<stem>, or [-@sec-ch-<stem>] inside "Chapters A to B", so that Quarto and
# filters/book-chapter-refs.lua number them from the order of _quarto.yml. Turn the lint on once the book is converted.
LINT_LITERAL_CHAPTERS = True
_LITERAL_CHAPTER_RE = re.compile(r"\bChapters? \d+")


class ValidationIssue:
    def __init__(self, file: Path, line: int, severity: str, message: str) -> None:
        self.file = file
        self.line = line
        self.severity = severity  # "ERROR", "WARNING"
        self.message = message

    def __str__(self) -> str:
        rel = self.file.relative_to(REPO_ROOT) if self.file.is_relative_to(REPO_ROOT) else self.file
        return f"[{self.severity}] {rel}:{self.line}: {self.message}"


def _first_h1(body: str) -> str | None:
    """The first level-1 heading outside code fences, or None."""
    in_fence = False
    for line in body.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
        elif not in_fence and re.match(r"^# \S", line):
            return line
    return None


def validate_chapter_references(path: Path, lines: list[str]) -> list[ValidationIssue]:
    """Warn on a literal "Chapter N" outside code; write @sec-ch-<stem> instead."""
    issues: list[ValidationIssue] = []
    in_fence = False
    for idx, line in enumerate(lines, start=1):
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        prose = re.sub(r"`[^`]*`", "", line)
        m = _LITERAL_CHAPTER_RE.search(prose)
        if m:
            issues.append(ValidationIssue(
                path, idx, "WARNING",
                f"literal '{m.group()}': write @sec-ch-<file-stem> (and [-@sec-ch-<file-stem>] after 'Chapters')"))
    return issues


def validate_flat_sections(path: Path, lines: list[str]) -> list[ValidationIssue]:
    """Warn on a heading deeper than level 2 outside code fences: the sections of the book are flat."""
    issues: list[ValidationIssue] = []
    in_fence = False
    for idx, line in enumerate(lines, start=1):
        if line.startswith("```"):
            in_fence = not in_fence
        elif not in_fence and re.match(r"^#{3,} \S", line):
            issues.append(ValidationIssue(
                path, idx, "WARNING",
                "heading deeper than '##': sections are flat, split the section or use italic lead-ins"))
    return issues


SECTION_WORD_LIMIT = 3200  # 8 printed pages at the ~400 words per page of the O'Reilly trim size


def validate_section_length(path: Path, text: str) -> list[ValidationIssue]:
    """Warn on a numbered section longer than SECTION_WORD_LIMIT words. A section is less than 8 pages, read in one sitting; one that is longer is discussed with the author, not cut by the tool. The count is of
    the running text: it leaves out code, display math, callouts, questions, answers, figures, tables and their captions: only the words of uninterrupted attention count."""
    issues: list[ValidationIssue] = []
    lines = text.splitlines()
    heads = [i for i, ln in enumerate(lines) if re.match(r"^## \S", ln)]
    for n, start in enumerate(heads):
        head = lines[start]
        if ".unnumbered" in head:
            continue
        body = "\n".join(lines[start + 1:heads[n + 1] if n + 1 < len(heads) else len(lines)])
        body = re.sub(r"```.*?```", "", body, flags=re.S)
        body = re.sub(r"\$\$.*?\$\$", "", body, flags=re.S)
        kept: list[str] = []
        depth, skipping = 0, False  # depth of the divs opened inside a skipped (callout, questions, answers) block
        for ln in body.splitlines():
            stripped = ln.strip()
            if skipping:
                if stripped == ":::":
                    depth -= 1
                    skipping = depth > 0
                elif stripped.startswith(":::"):
                    depth += 1
            elif re.match(r"^:::+\s*\{[^}]*\.(callout[\w-]*|questions|answers)\b", stripped):
                depth, skipping = 1, True
            elif re.match(r"^(!\[|\||: )", stripped):
                continue  # a figure and its caption, a table row, a table caption: the eye leaves the running text
            else:
                kept.append(ln)
        words = len(" ".join(kept).split())
        if words > SECTION_WORD_LIMIT:
            issues.append(ValidationIssue(
                path, start + 1, "WARNING",
                f"section of about {words:,} words of running text (about {words / 400:.1f} pages): a section is less than 8 pages; discuss it with the author (split, trim or keep)"))
    return issues


def validate_frontmatter(path: Path, text: str) -> list[ValidationIssue]:
    """Check YAML frontmatter if present."""
    issues: list[ValidationIssue] = []
    if path == INDEX_QMD:
        return issues

    # Unnumbered back-matter chapters (e.g. chapters/solutions.qmd) start with
    # `# Title {.unnumbered}` and carry no YAML frontmatter.
    first_line = next((ln for ln in text.splitlines() if ln.strip()), "")
    if _UNNUMBERED_H1_RE.match(first_line):
        return issues

    fm_match = re.match(r"^---\r?\n(.*?)\r?\n---", text, flags=re.DOTALL)
    if not fm_match:
        issues.append(ValidationIssue(path, 1, "WARNING", "Missing YAML frontmatter (--- ... ---)"))
        return issues

    raw_yaml = fm_match.group(1)
    try:
        fm = yaml.safe_load(raw_yaml)
        if not isinstance(fm, dict):
            issues.append(ValidationIssue(path, 1, "ERROR", "YAML frontmatter must be a dictionary"))
        else:
            front_title = bool(str(fm.get("title") or "").strip())
            h1_title = _first_h1(text[fm_match.end():]) is not None
            if not front_title and not h1_title:
                issues.append(ValidationIssue(path, 1, "ERROR", "YAML frontmatter missing non-empty 'title' (or give the title as a level-1 heading)"))
            elif front_title and h1_title:
                issues.append(ValidationIssue(path, 1, "WARNING", "title given twice: in the front matter and in a level-1 heading"))
    except yaml.YAMLError as e:
        issues.append(ValidationIssue(path, 1, "ERROR", f"YAML frontmatter parse error: {e}"))

    return issues


def validate_callouts(path: Path, lines: list[str]) -> list[ValidationIssue]:
    """Check balanced callout blocks (:::)."""
    issues: list[ValidationIssue] = []
    div_stack: list[int] = []

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("::: {") or stripped.startswith(":::"):
            if stripped == ":::":
                if not div_stack:
                    issues.append(ValidationIssue(path, idx, "ERROR", "Unmatched closing ':::' block"))
                else:
                    div_stack.pop()
            else:
                div_stack.append(idx)

    if div_stack:
        for open_line in div_stack:
            issues.append(ValidationIssue(path, open_line, "ERROR", f"Unclosed ':::' block opened at line {open_line}"))

    return issues


def validate_code_chunks(path: Path, text: str) -> list[ValidationIssue]:
    """Check code chunk delimiters and Python syntax in executable cells."""
    issues: list[ValidationIssue] = []
    code_pattern = re.compile(r"```\{([a-zA-Z0-9_-]+)(?:,[^}]*)?\}\r?\n(.*?)\r?\n```", re.DOTALL)

    # Check unclosed code fences
    lines = text.splitlines()
    in_fence = False
    fence_start = 0
    for idx, line in enumerate(lines, start=1):
        if line.strip().startswith("```"):
            if not in_fence:
                in_fence = True
                fence_start = idx
            else:
                in_fence = False

    if in_fence:
        issues.append(ValidationIssue(path, fence_start, "ERROR", f"Unclosed code fence opened at line {fence_start}"))

    # Validate python code syntax
    for match in code_pattern.finditer(text):
        lang = match.group(1).lower()
        chunk = match.group(2)
        start_line = text[: match.start()].count("\n") + 1

        if lang == "python":
            # Strip quarto options (|# ...)
            py_lines = []
            for cline in chunk.splitlines():
                if cline.strip().startswith("#|"):
                    continue
                py_lines.append(cline)
            py_code = "\n".join(py_lines)

            try:
                ast.parse(py_code)
            except SyntaxError as e:
                issues.append(
                    ValidationIssue(
                        path,
                        start_line + (e.lineno or 1),
                        "ERROR",
                        f"Python syntax error in executable code cell: {e.msg}",
                    )
                )

    return issues


def validate_math_delimiters(path: Path, lines: list[str]) -> list[ValidationIssue]:
    """Check basic math block delimiters ($$)."""
    issues: list[ValidationIssue] = []
    in_display_math = False
    math_start_line = 0

    for idx, line in enumerate(lines, start=1):
        # Count $$ in line outside code blocks
        if "$$" in line:
            count = line.count("$$")
            if count == 1:
                if not in_display_math:
                    in_display_math = True
                    math_start_line = idx
                else:
                    in_display_math = False
            elif count % 2 != 0:
                issues.append(ValidationIssue(path, idx, "WARNING", "Odd number of '$$' math delimiters on line"))

    if in_display_math:
        issues.append(
            ValidationIssue(
                path, math_start_line, "ERROR", f"Unclosed display math '$$' block opened at line {math_start_line}"
            )
        )

    return issues


def validate_section_breaks(path: Path, lines: list[str]) -> list[ValidationIssue]:
    """Check that chapters and special sections use {{< pagebreak >}} instead of '---' horizontal rules."""
    issues: list[ValidationIssue] = []

    # Determine frontmatter boundary
    in_frontmatter = False
    fm_end_line = 0
    if lines and lines[0].strip() == "---":
        in_frontmatter = True
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                fm_end_line = idx + 1
                break

    for idx, line in enumerate(lines, start=1):
        if idx <= fm_end_line:
            continue

        stripped = line.strip()
        if stripped in ("---", "***", "___"):
            # Check if this rule is separating sections or chapters
            issues.append(
                ValidationIssue(
                    path,
                    idx,
                    "WARNING",
                    "Found horizontal rule '---'. Parts, chapters, and special sections "
                    "(Acknowledgments, Disclaimer, Prologue, References) should be separated by "
                    "'{{< pagebreak >}}' instead of '---'.",
                )
            )

    return issues


# ------------------------------------------------------------------
# Citation / bibliography validation (references.bib)
# ------------------------------------------------------------------

_BIB_ENTRY_RE = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", re.MULTILINE)
_BIB_FIELD_RE = re.compile(r"(\w+)\s*=\s*\{(.*?)\}\s*,?\s*(?=\n\s*\w+\s*=|\n\})", re.DOTALL)
_CITEKEY_RE = re.compile(r"(?<![\w@])@([A-Za-z][\w:.#$%&\-+?<>~/]*)")
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
# Quarto cross-reference keys (e.g. @sec-intro, @tbl-binary-entropy) share the
# `@key` syntax with citations but resolve against labels, not references.bib.
_CROSSREF_RE = re.compile(r"^(?:sec|fig|tbl|eq|lst|thm|lem|cor|prp|cnj|def|exm|exr)-")
_LOCATOR_RE = re.compile(r",\s*p{1,2}\.\s*\d")


def _blank_out(text: str, span: tuple[int, int]) -> str:
    """Replace text[start:end] with same-length whitespace, preserving newlines."""
    start, end = span
    chunk = text[start:end]
    blanked = "".join(ch if ch == "\n" else " " for ch in chunk)
    return text[:start] + blanked + text[end:]


def strip_non_prose(text: str) -> str:
    """Blank out fenced code, inline code spans, math, and email-like strings.

    Preserves line numbers (and overall offsets) so callers can keep mapping
    match positions back to the original line numbers.
    """
    result = text

    for pattern in (
        re.compile(r"```.*?```", re.DOTALL),
        re.compile(r"`[^`\n]*`"),
        re.compile(r"\$\$.*?\$\$", re.DOTALL),
        re.compile(r"\$[^$\n]+\$"),
        _EMAIL_RE,
    ):
        while True:
            m = pattern.search(result)
            if not m:
                break
            result = _blank_out(result, m.span())

    return result


def extract_citekeys(text: str) -> list[tuple[str, int]]:
    """Return (citekey, line_number) pairs for every `@key` citation in prose."""
    prose = strip_non_prose(text)
    hits: list[tuple[str, int]] = []
    for m in _CITEKEY_RE.finditer(prose):
        if _CROSSREF_RE.match(m.group(1)):
            continue
        line_no = prose[: m.start()].count("\n") + 1
        hits.append((m.group(1), line_no))
    return hits


def parse_bibliography(bib_path: Path | None = None) -> dict[str, dict[str, str]]:
    """Lightweight BibTeX parser: citekey -> {field: value}. No external dependency."""
    if bib_path is None:
        bib_path = REFERENCES_BIB
    entries: dict[str, dict[str, str]] = {}
    if not bib_path.is_file():
        return entries

    text = bib_path.read_text(encoding="utf-8")
    for m in _BIB_ENTRY_RE.finditer(text):
        citekey = m.group(2)
        # Find the matching closing brace for this entry by bracket counting.
        brace_start = text.index("{", m.start())
        depth = 0
        end = brace_start
        for i in range(brace_start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        body = text[brace_start + 1 : end]
        fields: dict[str, str] = {}
        for fm in _BIB_FIELD_RE.finditer(body + "\n}"):
            fields[fm.group(1).strip().lower()] = fm.group(2).strip()
        entries[citekey] = fields

    return entries


def find_cited_keys_in_file(path: Path, text: str) -> set[str]:
    """Return the set of citekeys cited in a single .qmd file."""
    return {key for key, _ in extract_citekeys(text)}


def validate_citations(
    path: Path,
    text: str,
    known_keys: set[str] | None = None,
    strict: bool = False,
) -> list[ValidationIssue]:
    """Per-file citation checks: unresolved citekeys and legacy numbered reference lists.

    `known_keys` is the set of citekeys defined in references.bib. If None, the
    bibliography is parsed on demand (callers validating many files should parse
    once and pass the result in). When `strict` is set, also emit a heuristic
    suggestion/warning for theorem-adjacent citations missing a page locator.
    """
    issues: list[ValidationIssue] = []
    if known_keys is None:
        known_keys = set(parse_bibliography().keys())

    # 1. Unresolved citekey -> ERROR.
    for key, line_no in extract_citekeys(text):
        if key not in known_keys:
            issues.append(
                ValidationIssue(
                    path,
                    line_no,
                    "ERROR",
                    f"Unresolved citation key '@{key}' does not exist in references.bib",
                )
            )

    # 6. Missing locator on a theorem-adjacent citation -> WARNING (--strict only).
    if strict:
        lines = text.splitlines()
        theorem_words = re.compile(r"\b(Theorem|Lemma|Proof)\b")
        for idx, line in enumerate(lines, start=1):
            if theorem_words.search(line) and "@" in line and not _LOCATOR_RE.search(line):
                issues.append(
                    ValidationIssue(
                        path,
                        idx,
                        "WARNING",
                        "Citation near 'Theorem'/'Lemma'/'Proof' has no page locator (e.g. '[@key, p. 12]')",
                    )
                )

    # 5. Legacy numbered reference list -> WARNING.
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if re.match(r"^#+\s+References\b", line.strip()):
            for look in range(idx + 1, min(idx + 6, len(lines))):
                stripped = lines[look].strip()
                if not stripped:
                    continue
                if re.match(r"^\d+\.\s", stripped):
                    issues.append(
                        ValidationIssue(
                            path,
                            look + 1,
                            "WARNING",
                            "Legacy hand-numbered reference list found under '## References'; "
                            "replace with a ':::  {#refs}' div driven by references.bib.",
                        )
                    )
                break

    return issues


def validate_bibliography_corpus(cited_keys: set[str]) -> list[ValidationIssue]:
    """Corpus-wide bibliography checks: orphan entries, missing fields, broken file= paths."""
    issues: list[ValidationIssue] = []
    entries = parse_bibliography()

    for citekey, fields in entries.items():
        # 2. Orphan bib entry -> WARNING.
        if citekey not in cited_keys:
            issues.append(
                ValidationIssue(
                    REFERENCES_BIB,
                    1,
                    "WARNING",
                    f"Bibliography entry '{citekey}' is not cited anywhere in index.qmd or chapters/*.qmd",
                )
            )

        # 3. Missing required fields -> WARNING.
        # An edited volume legitimately has an editor instead of an author.
        missing = [f for f in ("author", "title", "year") if not fields.get(f)]
        if "author" in missing and fields.get("editor"):
            missing.remove("author")
        if missing:
            issues.append(
                ValidationIssue(
                    REFERENCES_BIB,
                    1,
                    "WARNING",
                    f"Bibliography entry '{citekey}' is missing required field(s): {', '.join(missing)}",
                )
            )

        # 4. Broken file= path -> ERROR.
        file_field = fields.get("file", "").strip()
        if file_field:
            if not (REFERENCES_DIR / file_field).is_file() and not Path(file_field).is_file():
                issues.append(
                    ValidationIssue(
                        REFERENCES_BIB,
                        1,
                        "ERROR",
                        f"Bibliography entry '{citekey}' has file = '{file_field}' which does not exist under references/",
                    )
                )

    return issues


def validate_questions_and_solutions(chapter_files: list[Path]) -> list[ValidationIssue]:
    """Check that every review-questions block has its solutions next to it.

    Authoring rule: each `::: {.questions}` block in a chapter is followed
    immediately (only blank lines in between) by a `::: {.answers}` block with
    the same number of items. The back-matter `solutions.qmd` is generated from
    those blocks by sync_solutions.py, so it must be current, and `ref=` is only
    legal inside it.
    """
    issues: list[ValidationIssue] = []
    chapters = [p for p in chapter_files if p.name != SOLUTIONS_FILENAME]

    for path in chapters:
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        questions = find_div_blocks(text, _QUESTIONS_OPEN_RE)
        answers = find_div_blocks(text, _ANSWERS_OPEN_RE)

        for block in answers:
            if block.ref is not None:
                issues.append(ValidationIssue(
                    path, block.start, "ERROR",
                    ".answers ref=... is only for the generated solutions.qmd; "
                    "chapters use a plain `::: {.answers}` block after the questions",
                ))
        answers = [b for b in answers if b.ref is None]

        by_start = {b.start: b for b in answers}
        paired: set[int] = set()
        for q in questions:
            nxt = next((b for b in answers if b.start > q.end), None)
            gap = lines[q.end:nxt.start - 1] if nxt else []
            if nxt is None or any(ln.strip() for ln in gap) or nxt.start in paired:
                issues.append(ValidationIssue(
                    path, q.start, "ERROR",
                    "Review questions block is not followed immediately by a `::: {.answers}` block",
                ))
                continue
            paired.add(nxt.start)
            if q.n_items != nxt.n_items:
                issues.append(ValidationIssue(
                    path, nxt.start, "ERROR",
                    f"Review questions block (line {q.start}) has {q.n_items} question(s) "
                    f"but its answers block has {nxt.n_items} solution(s)",
                ))
        for start, block in by_start.items():
            if start not in paired:
                issues.append(ValidationIssue(
                    path, start, "ERROR",
                    "`::: {.answers}` block does not directly follow a `::: {.questions}` block",
                ))

    # The back-matter file is generated: it must match what the chapters say.
    expected = render_solutions(chapters)
    solutions_path = next((p for p in chapter_files if p.name == SOLUTIONS_FILENAME), None)
    has_answers = "::: {.answers" in expected
    if solutions_path is None:
        if has_answers:
            issues.append(ValidationIssue(
                CHAPTERS_DIR / SOLUTIONS_FILENAME, 1, "ERROR",
                "Chapters contain solutions but solutions.qmd is missing; run `make sync-solutions`",
            ))
    elif solutions_path.read_text(encoding="utf-8") != expected:
        issues.append(ValidationIssue(
            solutions_path, 1, "ERROR",
            "solutions.qmd is out of date with the chapters' answers blocks; "
            "run `make sync-solutions` (never edit it by hand)",
        ))
    return issues


def validate_qmd_file(path: Path, citations: bool = True, strict: bool = False) -> list[ValidationIssue]:
    """Run all validation passes on a single .qmd file.

    `citations` controls whether the citekey-resolution pass runs (default on,
    gated by the top-level --citations/--no-citations flag). Orphan-entry and
    other corpus-wide bibliography checks are *not* run here; see
    `validate_bibliography_corpus`, which needs the full set of cited keys
    across all files and is therefore skipped in single-file (`--file`) mode.
    """
    if not path.is_file():
        return [ValidationIssue(path, 1, "ERROR", "File does not exist")]

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    issues: list[ValidationIssue] = []
    issues.extend(validate_frontmatter(path, text))
    issues.extend(validate_callouts(path, lines))
    issues.extend(validate_code_chunks(path, text))
    issues.extend(validate_math_delimiters(path, lines))
    issues.extend(validate_section_breaks(path, lines))
    if LINT_LITERAL_CHAPTERS:
        issues.extend(validate_chapter_references(path, lines))
        if path != INDEX_QMD:  # the front matter pages (prologue, notation, roadmap) are not chapters
            issues.extend(validate_flat_sections(path, lines))
            issues.extend(validate_section_length(path, text))
    if citations:
        issues.extend(validate_citations(path, text, strict=strict))

    return issues


def validate_all(verbose: bool = False, citations: bool = True, strict: bool = False) -> tuple[int, int]:
    """Validate all book files and return (errors_count, warnings_count)."""
    files_to_validate: list[Path] = []
    if INDEX_QMD.is_file():
        files_to_validate.append(INDEX_QMD)

    if CHAPTERS_DIR.is_dir():
        files_to_validate.extend(sorted(CHAPTERS_DIR.glob("*.qmd")))

    total_errors = 0
    total_warnings = 0

    known_keys = set(parse_bibliography().keys()) if citations else set()
    all_cited_keys: set[str] = set()

    for file_path in files_to_validate:
        issues = validate_qmd_file(file_path, citations=False, strict=strict)
        text = file_path.read_text(encoding="utf-8")
        if citations:
            issues.extend(validate_citations(file_path, text, known_keys=known_keys, strict=strict))
            all_cited_keys |= find_cited_keys_in_file(file_path, text)

        file_errors = sum(1 for i in issues if i.severity == "ERROR")
        file_warnings = sum(1 for i in issues if i.severity == "WARNING")

        total_errors += file_errors
        total_warnings += file_warnings

        rel = file_path.relative_to(REPO_ROOT) if file_path.is_relative_to(REPO_ROOT) else file_path
        if issues:
            print(f"Validation for {rel}: {file_errors} error(s), {file_warnings} warning(s)")
            for issue in issues:
                print(f"  {issue}")
        elif verbose:
            print(f"✓ {rel}: Valid (0 errors, 0 warnings)")

    # Corpus-level check: every review question has a matching solution.
    chapter_files = sorted(CHAPTERS_DIR.glob("*.qmd")) if CHAPTERS_DIR.is_dir() else []
    qs_issues = validate_questions_and_solutions(chapter_files)
    if qs_issues:
        qs_errors = sum(1 for i in qs_issues if i.severity == "ERROR")
        total_errors += qs_errors
        total_warnings += len(qs_issues) - qs_errors
        print(f"Validation for review questions/solutions: {qs_errors} error(s)")
        for issue in qs_issues:
            print(f"  {issue}")
    elif verbose:
        print("✓ Review questions and solutions: consistent")

    # Corpus-level bibliography checks (orphan entries, missing fields, broken
    # file= paths) require the full cited-key set, so they run once after the
    # per-file loop rather than per file.
    if citations and REFERENCES_BIB.is_file():
        corpus_issues = validate_bibliography_corpus(all_cited_keys)
        corpus_errors = sum(1 for i in corpus_issues if i.severity == "ERROR")
        corpus_warnings = sum(1 for i in corpus_issues if i.severity == "WARNING")
        total_errors += corpus_errors
        total_warnings += corpus_warnings
        if corpus_issues:
            rel = REFERENCES_BIB.relative_to(REPO_ROOT) if REFERENCES_BIB.is_relative_to(REPO_ROOT) else REFERENCES_BIB
            print(f"Validation for {rel}: {corpus_errors} error(s), {corpus_warnings} warning(s)")
            for issue in corpus_issues:
                print(f"  {issue}")
        elif verbose:
            print(f"✓ {REFERENCES_BIB.name}: Valid (0 errors, 0 warnings)")

    return total_errors, total_warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Quarto book files")
    parser.add_argument("--file", "-f", type=Path, help="Validate a specific .qmd file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print verbose output")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    parser.add_argument(
        "--citations",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Validate @citekey citations against references.bib (default: on)",
    )
    args = parser.parse_args()

    if args.file:
        issues = validate_qmd_file(args.file, citations=args.citations, strict=args.strict)
        errors = sum(1 for i in issues if i.severity == "ERROR")
        warnings = sum(1 for i in issues if i.severity == "WARNING")
        for issue in issues:
            print(issue)
        failed = errors > 0 or (args.strict and warnings > 0)
        sys.exit(1 if failed else 0)

    errors, warnings = validate_all(verbose=args.verbose, citations=args.citations, strict=args.strict)
    if errors == 0 and warnings == 0:
        print("✓ All book files passed validation.")
    elif errors == 0:
        print(f"✓ Validation passed with {warnings} warning(s).")
    else:
        print(f"✗ Validation failed with {errors} error(s) and {warnings} warning(s).", file=sys.stderr)

    failed = errors > 0 or (args.strict and warnings > 0)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
