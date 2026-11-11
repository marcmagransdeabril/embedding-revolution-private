"""Tests for the status annotations and durability metrics used by review-doc §17 and §18."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import durability_metrics as dm  # noqa: E402

CH = """---
title: "T"
status: definitive
open: "Where does it go?"
---

Intro.

## Written

Body.

## Maybe {.provisional}

Unsure.

### Deeper

Still unsure.

## Settled again

End.
"""


def test_chapter_status_from_front_matter_and_from_h1_class():
    assert dm.chapter_status(CH) == "definitive"
    assert dm.chapter_status("# Epilogue {.unnumbered .idea}\n\ntext\n") == "idea"
    assert dm.chapter_status("# Epilogue {.unnumbered}\n") is None


def test_sections_carry_their_own_status_and_range():
    secs = {h["title"]: h for h in dm.sections(CH)}
    assert secs["Maybe"]["status"] == "provisional" and secs["Written"]["status"] is None
    assert secs["Maybe"]["end"] > secs["Deeper"]["line"] > secs["Maybe"]["line"]
    assert secs["Settled again"]["line"] > secs["Maybe"]["end"]


def test_headings_inside_code_fences_are_ignored():
    assert dm.sections("# A\n\n```python\n# not a heading\n```\n") == [
        {"line": 1, "level": 1, "title": "A", "status": None, "end": 5}]


def test_definitive_text_drops_provisional_sections_and_subsections():
    text = dm.definitive_text(CH)
    assert "Body." in text and "End." in text
    assert "Unsure." not in text and "Still unsure." not in text and "title:" not in text


def test_open_notes_from_front_matter_and_comments():
    assert dm.open_notes(CH) == ["Where does it go?"]
    assert dm.open_notes("<!-- OPEN: what revolution\n means -->") == ["what revolution means"]


def test_index_tags_are_read_from_roadmap_bullets():
    idx = "* **Chapter 1: A.** *(definitive)* text\n* **Epilogue: B.** *(idea)* text\n"
    assert dm.index_tags(idx) == {"Chapter 1": "definitive", "Epilogue": "idea"}


def make_book(tmp_path, chapter_status, tag):
    (tmp_path / "chapters").mkdir()
    (tmp_path / "_quarto.yml").write_text(
        "book:\n  chapters:\n  - index.qmd\n  - part: P\n    chapters:\n    - chapters/a.qmd\n  - chapters/epilogue.qmd\n"
        "  - chapters/solutions.qmd\n")
    (tmp_path / "index.qmd").write_text(f"* **Chapter 1: A.** *({tag})* x\n* **Epilogue: E.** *(idea)* y\n")
    (tmp_path / "chapters" / "a.qmd").write_text(f"---\ntitle: A\nstatus: {chapter_status}\n---\n\ntext\n")
    (tmp_path / "chapters" / "epilogue.qmd").write_text("# E {.unnumbered .idea}\n\ntext\n")
    return tmp_path


def test_status_report_flags_tag_mismatch_but_accepts_agreement(tmp_path):
    rows, problems = dm.status_report(make_book(tmp_path, "definitive", "definitive"))
    assert [r["status"] for r in rows] == ["definitive", "idea"]
    assert problems == []
    book2 = tmp_path / "b2"
    book2.mkdir()
    _, problems = dm.status_report(make_book(book2, "definitive", "idea"))
    assert any(s == "error" and "differs" in m for s, _, m in problems)


def test_status_report_flags_invalid_and_missing_status(tmp_path):
    _, problems = dm.status_report(make_book(tmp_path, "finished", "definitive"))
    assert any(s == "error" and "not one of" in m for s, _, m in problems)


def test_repo_annotations_are_consistent():
    _, problems = dm.status_report(dm.REPO_ROOT)
    assert [p for p in problems if p[0] == "error"] == []


def test_dropped_ideas_file_is_outside_the_book():
    notes = dm.REPO_ROOT / "notes" / "ideas.qmd"
    assert notes.exists()
    assert "notes/ideas.qmd" not in (dm.REPO_ROOT / "_quarto.yml").read_text(encoding="utf-8")


def test_file_metrics_reads_year_of_cited_keys():
    bib = {"a": {"year": "{1948}"}, "b": {"year": "2024"}, "c": {"year": "1956"}}
    m = dm.file_metrics("See [@a; @b; @c] and [@missing].", bib)
    assert m == {"cites": 3, "median_year": 1956, "before_1980": 2, "from_2020": 1, "from_2023": 1}


def test_perishable_relative_wording_and_titles():
    texts = {"x.qmd": "# Quantum Logic\nRecently, CLIP and LLMs appeared.\n", "y.qmd": "ImageBind. Transformer.\n"}
    assert dm.perishable_counts(texts)["CLIP/ImageBind"] == {"occurrences": 2, "files": 2}
    assert dm.relative_wording(texts) == ["x.qmd:2"]
    assert dm.fashion_titles(texts) == ["x.qmd:1: # Quantum Logic"]


def test_diff_reports_only_changes():
    base = {"date": "d", "files": {"a": {"cites": 1, "median_year": 1950, "from_2023": 0}},
            "perishable": {"T": {"occurrences": 1, "files": 1}}, "relative_wording": [], "fashion_titles": [],
            "status": {"chapters": {"idea": 1}}}
    assert dm.diff_metrics(base, base) == []
    new = {**base, "files": {"a": {"cites": 2, "median_year": 2020, "from_2023": 1}}, "relative_wording": ["a:3"],
           "status": {"chapters": {"idea": 0, "provisional": 1}}}
    out = dm.diff_metrics(base, new)
    assert any("median year 1950 -> 2020" in line for line in out)
    assert any("relative_wording: +1 new" in line for line in out)
    assert any(line.startswith("status:") for line in out)


# ---- roadmap entries written as @sec-ch-<stem> (Step 0 of notes/generative_chapter_plan.md)

def make_labelled_book(tmp_path, roadmap_keys, tag="definitive", chapters=("a", "b")):
    """A book of chapters a, b (and an epilogue) whose roadmap lists `roadmap_keys` in the given order."""
    (tmp_path / "chapters").mkdir()
    listed = "".join(f"    - chapters/{c}.qmd\n" for c in chapters)
    (tmp_path / "_quarto.yml").write_text(
        f"book:\n  chapters:\n  - index.qmd\n  - part: P\n    chapters:\n{listed}  - chapters/epilogue.qmd\n  - chapters/solutions.qmd\n")
    lines = [f"* **{k}: T.** *({tag})* x\n" for k in roadmap_keys]
    (tmp_path / "index.qmd").write_text("".join(lines) + "* **Epilogue: E.** *(idea)* y\n")
    for c in chapters:
        (tmp_path / "chapters" / f"{c}.qmd").write_text(f"---\nstatus: {tag}\n---\n\n# {c.upper()} {{#sec-ch-{c}}}\n\ntext\n")
    (tmp_path / "chapters" / "epilogue.qmd").write_text("# E {.unnumbered .idea}\n\ntext\n")
    return tmp_path


def test_index_tags_accept_a_chapter_label_in_place_of_the_number():
    idx = "* **@sec-ch-embedding-spaces: A.** *(definitive)* text\n* **Epilogue: B.** *(idea)* text\n"
    assert dm.index_tags(idx) == {"@sec-ch-embedding-spaces": "definitive", "Epilogue": "idea"}


def test_status_report_reads_roadmap_entries_by_label(tmp_path):
    rows, problems = dm.status_report(make_labelled_book(tmp_path, ["@sec-ch-a", "@sec-ch-b"]))
    assert [r["index_tag"] for r in rows] == ["definitive", "definitive", "idea"]
    assert problems == []


def test_status_report_flags_a_label_tag_mismatch(tmp_path):
    book = make_labelled_book(tmp_path, ["@sec-ch-a", "@sec-ch-b"])
    (book / "chapters" / "b.qmd").write_text("---\nstatus: idea\n---\n\n# B {#sec-ch-b}\n\ntext\n")
    _, problems = dm.status_report(book)
    assert any(s == "error" and "differs" in m for s, _, m in problems)


def test_status_report_flags_a_roadmap_in_a_different_order_than_quarto_yml(tmp_path):
    _, problems = dm.status_report(make_labelled_book(tmp_path, ["@sec-ch-b", "@sec-ch-a"]))
    assert any(s == "error" and "order" in m for s, _, m in problems)


def test_status_report_flags_a_roadmap_label_that_is_not_a_chapter(tmp_path):
    _, problems = dm.status_report(make_labelled_book(tmp_path, ["@sec-ch-a", "@sec-ch-b", "@sec-ch-gone"]))
    assert any(s == "error" and "sec-ch-gone" in m for s, _, m in problems)


def test_status_report_flags_literal_numbers_out_of_order_or_repeated(tmp_path):
    _, problems = dm.status_report(make_labelled_book(tmp_path, ["Chapter 2", "Chapter 1"]))
    assert any(s == "error" and "order" in m for s, _, m in problems)


def test_status_report_accepts_literal_numbers_in_order(tmp_path):
    _, problems = dm.status_report(make_labelled_book(tmp_path, ["Chapter 1", "Chapter 2"]))
    assert problems == []


def test_fashion_titles_look_at_roadmap_entries_written_with_a_label():
    texts = {"index.qmd": "* **@sec-ch-v: Vector Databases, RAG.** *(idea)* text\n"}
    assert len(dm.fashion_titles(texts)) == 1
