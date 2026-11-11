"""Unit tests for validate_book.py structure and syntax checker."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent
REPO_ROOT = TESTS_DIR.parents[4]

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import validate_book


def test_validate_current_workspace_files():
    """Verify that current repo files (index.qmd, chapters/embedding_spaces.qmd) pass validation."""
    errors, warnings = validate_book.validate_all(verbose=False)
    assert errors == 0, f"Expected 0 validation errors, got {errors}"


def test_validate_frontmatter():
    """Verify frontmatter validation rules."""
    valid_text = "---\ntitle: 'Test Title'\nsubtitle: 'Test Sub'\n---\n# Content"
    issues = validate_book.validate_frontmatter(Path("test.qmd"), valid_text)
    assert len([i for i in issues if i.severity == "ERROR"]) == 0

    # A level-1 heading counts as the title since Step 0 of the chapter-reference plan, so this text has none.
    no_title_text = "---\nsubtitle: 'No Title'\n---\nContent"
    issues = validate_book.validate_frontmatter(Path("test.qmd"), no_title_text)
    assert any(i.severity == "ERROR" and "title" in i.message.lower() for i in issues)


def test_validate_callouts():
    """Verify balanced callout block validation."""
    balanced_lines = [
        "::: {.callout-note}",
        "Some note content",
        ":::",
    ]
    issues = validate_book.validate_callouts(Path("test.qmd"), balanced_lines)
    assert len(issues) == 0

    unclosed_lines = [
        "::: {.callout-note}",
        "Some unclosed note content",
    ]
    issues = validate_book.validate_callouts(Path("test.qmd"), unclosed_lines)
    assert any(i.severity == "ERROR" and "unclosed" in i.message.lower() for i in issues)


def test_validate_code_chunks():
    """Verify Python code cell AST syntax checking."""
    valid_py_chunk = "```{python}\nimport numpy as np\nx = np.zeros(10)\n```"
    issues = validate_book.validate_code_chunks(Path("test.qmd"), valid_py_chunk)
    assert len([i for i in issues if i.severity == "ERROR"]) == 0

    invalid_py_chunk = "```{python}\ndef broken_syntax(\n```"
    issues = validate_book.validate_code_chunks(Path("test.qmd"), invalid_py_chunk)
    assert any(i.severity == "ERROR" and "syntax" in i.message.lower() for i in issues)


def test_validate_math_delimiters():
    """Verify display math block balance checking."""
    balanced_math = [
        "Some text",
        "$$",
        "E = mc^2",
        "$$",
    ]
    issues = validate_book.validate_math_delimiters(Path("test.qmd"), balanced_math)
    assert len(issues) == 0

    unclosed_math = [
        "Some text",
        "$$",
        "E = mc^2",
    ]
    issues = validate_book.validate_math_delimiters(Path("test.qmd"), unclosed_math)
    assert any(i.severity == "ERROR" and "unclosed" in i.message.lower() for i in issues)


def test_validate_citations_unresolved_key():
    """Verify an unresolved citekey is flagged as an ERROR."""
    text = "Some prose citing [@totally_unknown_key_2099, p. 3] a claim."
    issues = validate_book.validate_citations(Path("test.qmd"), text, known_keys=set())
    assert any(i.severity == "ERROR" and "unresolved" in i.message.lower() for i in issues)


def test_validate_citations_resolved_key():
    """Verify a citekey present in known_keys produces no error."""
    text = "Some prose citing [@shannon1948mathematical, p. 3] a claim."
    issues = validate_book.validate_citations(Path("test.qmd"), text, known_keys={"shannon1948mathematical"})
    assert len([i for i in issues if i.severity == "ERROR"]) == 0


def test_validate_citations_ignores_code_fence_and_inline_code():
    """Verify citekey-like strings inside fenced/inline code are not flagged."""
    text = (
        "```python\n"
        "x = [@not_a_real_citation]\n"
        "```\n"
        "Inline `@also_not_a_citation` span.\n"
        "Real citation [@shannon1948mathematical].\n"
    )
    issues = validate_book.validate_citations(Path("test.qmd"), text, known_keys={"shannon1948mathematical"})
    assert len([i for i in issues if i.severity == "ERROR"]) == 0


def test_validate_citations_ignores_math():
    """Verify citekey-like strings inside math delimiters are not flagged."""
    text = "The expression $x@y$ and $$a@b$$ are math, not citations."
    issues = validate_book.validate_citations(Path("test.qmd"), text, known_keys=set())
    assert len([i for i in issues if i.severity == "ERROR"]) == 0


def test_validate_citations_ignores_quarto_crossrefs():
    """Verify Quarto cross-references (@sec-, @tbl-, ...) are not treated as citations."""
    text = "See @sec-hyperbolic-spaces and (@tbl-binary-entropy), but cite [@unknown2099key]."
    issues = validate_book.validate_citations(Path("test.qmd"), text, known_keys=set())
    errors = [i for i in issues if i.severity == "ERROR"]
    assert len(errors) == 1
    assert "unknown2099key" in errors[0].message


def test_validate_citations_ignores_email_addresses():
    """Verify email-like strings are not mistaken for citations."""
    text = "Contact the author at jane.doe@example.com for questions."
    issues = validate_book.validate_citations(Path("test.qmd"), text, known_keys=set())
    assert len(issues) == 0


def test_validate_citations_legacy_numbered_list():
    """Verify a hand-numbered '## References' list is flagged as a legacy list."""
    text = "## References {.unnumbered}\n\n1. Author, A. (2020). Title.\n2. Another, B.\n"
    issues = validate_book.validate_citations(Path("test.qmd"), text, known_keys=set())
    assert any(i.severity == "WARNING" and "legacy" in i.message.lower() for i in issues)


def test_validate_citations_refs_div_not_flagged_as_legacy():
    """Verify a well-formed '::: {#refs}' div does not trigger the legacy-list warning."""
    text = "## References {.unnumbered}\n\n::: {#refs}\n:::\n"
    issues = validate_book.validate_citations(Path("test.qmd"), text, known_keys=set())
    assert not any("legacy" in i.message.lower() for i in issues)


def test_parse_bibliography_orphan_and_missing_fields(tmp_path):
    """Verify orphan-entry and missing-required-field detection on a scratch bib file."""
    bib_path = tmp_path / "scratch.bib"
    bib_path.write_text(
        "@article{cited_entry,\n"
        "  author = {Doe, Jane},\n"
        "  title = {A Cited Paper},\n"
        "  year = {2020},\n"
        "  file = {}\n"
        "}\n"
        "@article{orphan_entry,\n"
        "  author = {Roe, Jim},\n"
        "  title = {An Uncited Paper},\n"
        "  year = {2021},\n"
        "  file = {}\n"
        "}\n"
        "@article{missing_fields_entry,\n"
        "  title = {Only Title}\n"
        "}\n"
        "@book{edited_volume_entry,\n"
        "  editor = {Doe, Jane},\n"
        "  title = {An Edited Volume},\n"
        "  year = {2011},\n"
        "  file = {}\n"
        "}\n",
        encoding="utf-8",
    )
    original_bib = validate_book.REFERENCES_BIB
    try:
        validate_book.REFERENCES_BIB = bib_path
        issues = validate_book.validate_bibliography_corpus({"cited_entry"})
    finally:
        validate_book.REFERENCES_BIB = original_bib

    messages = [i.message for i in issues]
    assert any("orphan_entry" in m and "not cited" in m for m in messages)
    assert any("missing_fields_entry" in m and "missing required field" in m for m in messages)
    assert not any("edited_volume_entry" in m and "missing required field" in m for m in messages)
    assert not any("cited_entry" in m and "not cited" in m for m in messages)


def test_validate_bibliography_corpus_broken_file_path(tmp_path):
    """Verify a `file =` field pointing at a non-existent PDF is flagged as an ERROR."""
    bib_path = tmp_path / "scratch.bib"
    bib_path.write_text(
        "@article{broken_file_entry,\n"
        "  author = {Doe, Jane},\n"
        "  title = {A Paper},\n"
        "  year = {2020},\n"
        "  file = {does_not_exist_xyz.pdf}\n"
        "}\n",
        encoding="utf-8",
    )
    original_bib = validate_book.REFERENCES_BIB
    try:
        validate_book.REFERENCES_BIB = bib_path
        issues = validate_book.validate_bibliography_corpus({"broken_file_entry"})
    finally:
        validate_book.REFERENCES_BIB = original_bib

    assert any(
        i.severity == "ERROR" and "broken_file_entry" in i.message and "does not exist" in i.message
        for i in issues
    )


def test_validate_section_breaks():
    """Verify that horizontal rules separating sections trigger warnings to use page breaks."""
    clean_lines = [
        "# Chapter 1",
        "Some introductory text.",
        "{{< pagebreak >}}",
        "## Acknowledgments {.unnumbered}",
        "Thank you all.",
    ]
    issues = validate_book.validate_section_breaks(Path("test.qmd"), clean_lines)
    assert len(issues) == 0

    rule_separated_lines = [
        "# Chapter 1",
        "Some introductory text.",
        "---",
        "## Acknowledgments {.unnumbered}",
        "Thank you all.",
    ]
    issues = validate_book.validate_section_breaks(Path("test.qmd"), rule_separated_lines)
    assert len(issues) == 1
    assert issues[0].severity == "WARNING"
    assert "pagebreak" in issues[0].message.lower()



def test_validate_frontmatter_allows_unnumbered_back_matter():
    """Back-matter chapters start with an unnumbered H1 and need no YAML."""
    text = "# Solutions {.unnumbered}\n\nBody\n"
    assert validate_book.validate_frontmatter(Path("solutions.qmd"), text) == []


def _write_chapter(tmp_path, chapter_text, name="ch1.qmd"):
    """Write a chapter plus the solutions.qmd generated from it; return both."""
    import sync_solutions

    ch = tmp_path / name
    ch.write_text(chapter_text, encoding="utf-8")
    sol = tmp_path / "solutions.qmd"
    sol.write_text(sync_solutions.render_solutions([ch]), encoding="utf-8")
    return [ch, sol]


_FM = "---\ntitle: T\n---\n\n"


def test_validate_questions_and_solutions_consistent(tmp_path):
    files = _write_chapter(
        tmp_path,
        _FM + "::: {.questions}\n1. Q one\n\n2. Q two\n:::\n\n::: {.answers}\n1. A one\n\n2. A two\n:::\n",
    )
    assert validate_book.validate_questions_and_solutions(files) == []


def test_validate_questions_and_solutions_two_sections(tmp_path):
    files = _write_chapter(
        tmp_path,
        _FM
        + "::: {.questions}\n1. Q one\n:::\n\n::: {.answers}\n1. A one\n:::\n\n"
        + "## Next\n\nText.\n\n"
        + "::: {.questions}\n1. Q two\n:::\n\n::: {.answers}\n1. A two\n:::\n",
    )
    assert validate_book.validate_questions_and_solutions(files) == []


def test_validate_questions_and_solutions_count_mismatch(tmp_path):
    files = _write_chapter(
        tmp_path,
        _FM + "::: {.questions}\n1. Q one\n\n2. Q two\n:::\n\n::: {.answers}\n1. A one\n:::\n",
    )
    issues = validate_book.validate_questions_and_solutions(files)
    assert len(issues) == 1 and "2 question(s) but its answers block has 1 solution(s)" in issues[0].message


def test_validate_questions_without_answers_block(tmp_path):
    files = _write_chapter(tmp_path, _FM + "::: {.questions}\n1. Q one\n:::\n\nMore text.\n")
    issues = validate_book.validate_questions_and_solutions(files)
    assert any("not followed immediately" in i.message for i in issues)


def test_validate_answers_must_directly_follow_questions(tmp_path):
    files = _write_chapter(
        tmp_path,
        _FM + "::: {.questions}\n1. Q one\n:::\n\nSome text in between.\n\n::: {.answers}\n1. A one\n:::\n",
    )
    issues = validate_book.validate_questions_and_solutions(files)
    assert any("not followed immediately" in i.message for i in issues)
    assert any("does not directly follow" in i.message for i in issues)


def test_validate_orphan_answers_block(tmp_path):
    files = _write_chapter(tmp_path, _FM + "::: {.answers}\n1. A one\n:::\n")
    issues = validate_book.validate_questions_and_solutions(files)
    assert any("does not directly follow" in i.message for i in issues)


def test_validate_ref_only_allowed_in_generated_solutions(tmp_path):
    files = _write_chapter(
        tmp_path,
        _FM + '::: {.questions}\n1. Q\n:::\n\n::: {.answers ref="ch1"}\n1. A\n:::\n',
    )
    issues = validate_book.validate_questions_and_solutions(files)
    assert any("only for the generated solutions.qmd" in i.message for i in issues)


def test_validate_stale_solutions_file(tmp_path):
    files = _write_chapter(
        tmp_path,
        _FM + "::: {.questions}\n1. Q one\n:::\n\n::: {.answers}\n1. A one\n:::\n",
    )
    files[1].write_text("# Solutions {.unnumbered}\n\nhand edited\n", encoding="utf-8")
    issues = validate_book.validate_questions_and_solutions(files)
    assert len(issues) == 1 and "out of date" in issues[0].message


def test_validate_missing_solutions_file(tmp_path):
    files = _write_chapter(
        tmp_path,
        _FM + "::: {.questions}\n1. Q one\n:::\n\n::: {.answers}\n1. A one\n:::\n",
    )
    issues = validate_book.validate_questions_and_solutions(files[:1])
    assert len(issues) == 1 and "solutions.qmd is missing" in issues[0].message


# ---- chapter titles in a labelled H1, and literal chapter numbers (Step 0 of notes/generative_chapter_plan.md)

def test_validate_frontmatter_accepts_a_labelled_h1_as_the_title():
    """A chapter may keep status/open in the front matter and give its title as `# Title {#sec-ch-...}`."""
    text = "---\nstatus: idea\n---\n\n# A Title {#sec-ch-a}\n\nBody\n"
    assert validate_book.validate_frontmatter(Path("a.qmd"), text) == []


def test_validate_frontmatter_still_requires_some_title():
    text = "---\nstatus: idea\n---\n\nBody without a heading\n"
    issues = validate_book.validate_frontmatter(Path("a.qmd"), text)
    assert any(i.severity == "ERROR" and "title" in i.message.lower() for i in issues)


def test_a_heading_inside_a_code_fence_is_not_a_title():
    text = "---\nstatus: idea\n---\n\n```python\n# not a title\n```\n"
    issues = validate_book.validate_frontmatter(Path("a.qmd"), text)
    assert any(i.severity == "ERROR" and "title" in i.message.lower() for i in issues)


def test_a_second_level_heading_is_not_a_title():
    text = "---\nstatus: idea\n---\n\n## A section\n"
    issues = validate_book.validate_frontmatter(Path("a.qmd"), text)
    assert any(i.severity == "ERROR" and "title" in i.message.lower() for i in issues)


def test_validate_frontmatter_warns_when_the_title_is_given_twice():
    text = "---\ntitle: A\n---\n\n# A {#sec-ch-a}\n"
    issues = validate_book.validate_frontmatter(Path("a.qmd"), text)
    assert [i.severity for i in issues] == ["WARNING"]
    assert "twice" in issues[0].message


def test_literal_chapter_references_are_flagged_outside_code():
    lines = [
        "See Chapter 3 and Chapters 4 to 6.",
        "```",
        "Chapter 9 inside a fence",
        "```",
        "An inline `Chapter 2` is code.",
        "The book has chapters, and Chapter [-@sec-ch-a] is a reference.",
        "<!-- OPEN: after the Chapter 5 scale test -->",
    ]
    issues = validate_book.validate_chapter_references(Path("a.qmd"), lines)
    assert [(i.line, i.severity) for i in issues] == [(1, "WARNING"), (7, "WARNING")]
    assert "sec-ch-" in issues[0].message


def test_literal_chapter_lint_is_off_until_enabled(tmp_path, monkeypatch):
    p = tmp_path / "a.qmd"
    p.write_text("---\ntitle: A\n---\n\nSee Chapter 3.\n", encoding="utf-8")
    monkeypatch.setattr(validate_book, "LINT_LITERAL_CHAPTERS", False)
    assert not any("sec-ch-" in i.message for i in validate_book.validate_qmd_file(p, citations=False))
    monkeypatch.setattr(validate_book, "LINT_LITERAL_CHAPTERS", True)
    assert any("sec-ch-" in i.message for i in validate_book.validate_qmd_file(p, citations=False))
