"""check_question_tree.py: the question tree of notes/question_tree.md against itself, the chapter files, the zoo and _quarto.yml."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_question_tree as cqt  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[5]

TREE = """# Tree

## Parts

| Part | Title | Test |
|---|---|---|
| I | One | q |
| II | Two | q |

## Chapters

| Part | Chapter | Question | Models | Main text it reuses |
|---|---|---|---|---|
| I | alpha | is a thing near? | A:sec-zoo-a, B:sec-zoo-b | x |
| II | beta | is a thing far? | A:sec-zoo-a | y |

## Chapters outside the Parts

| Position | Chapter | Question |
|---|---|---|
| first | first | what first? |
| last | last | what last? |
"""


def rows(text=TREE):
    return cqt.parse_tree(text)


def test_parse_reads_chapters_in_order():
    r = rows()
    assert [c.stem for c in r.chapters] == ["alpha", "beta"]
    assert r.chapters[0].models == [("A", "sec-zoo-a"), ("B", "sec-zoo-b")]
    assert r.first == "first" and r.last == "last"


def test_clean_tree_has_no_findings():
    assert cqt.check_tree(rows()) == []


def test_two_questions_in_one_chapter_is_a_finding():
    bad = TREE.replace("is a thing near?", "is a thing near? and is it far?")
    assert any("one question" in f for f in cqt.check_tree(rows(bad)))


def test_missing_question_mark_is_a_finding():
    bad = TREE.replace("is a thing near?", "is a thing near")
    assert any("question" in f for f in cqt.check_tree(rows(bad)))


def test_three_models_is_a_finding():
    bad = TREE.replace("A:sec-zoo-a, B:sec-zoo-b", "A:sec-zoo-a, B:sec-zoo-b, C:sec-zoo-c")
    assert any("models" in f for f in cqt.check_tree(rows(bad)))


def test_no_model_is_a_finding():
    bad = TREE.replace("| A:sec-zoo-a | y |", "|  | y |")
    assert any("models" in f for f in cqt.check_tree(rows(bad)))


def test_duplicate_chapter_is_a_finding():
    bad = TREE.replace("| II | beta |", "| II | alpha |")
    assert any("twice" in f for f in cqt.check_tree(rows(bad)))


def test_outside_question_is_checked():
    assert any("outside" in f or "first" in f for f in cqt.check_tree(rows(TREE.replace("what first?", "what first"))))


def test_missing_last_row_is_a_finding():
    bad = TREE.replace("| last | last | what last? |\n", "")
    assert any("first and the last" in f for f in cqt.check_tree(rows(bad)))


def test_short_row_is_a_finding_not_a_crash():
    bad = TREE.replace("| II | beta | is a thing far? | A:sec-zoo-a | y |", "| II | beta | is a thing far? |")
    assert any("5 cells" in f for f in cqt.check_tree(rows(bad)))


def test_parts_table_must_match_part_column():
    bad = TREE.replace("| II | Two | q |\n", "")
    assert any("Parts table" in f for f in cqt.check_tree(rows(bad)))


def test_bad_anchor_is_a_finding():
    bad = TREE.replace("A:sec-zoo-a, B", "A:zoo-a, B")
    assert any("anchor" in f for f in cqt.check_tree(rows(bad)))


def write_chapter(root, stem, body, status="idea"):
    (root / "chapters").mkdir(exist_ok=True)
    (root / "chapters" / f"{stem}.qmd").write_text(f"---\nstatus: {status}\n---\n\n# T {{#sec-ch-{stem}}}\n\n{body}", encoding="utf-8")


GOOD_BODY = ("Intro @sec-zoo-a @sec-zoo-b.\n\n## Question and Answer {#sec-x}\n\n*Next:* y.\n\n## Exercises {#sec-e}\n\n"
             "::: {.questions}\n1. q\n:::\n\n::: {.answers}\n1. a\n:::\n")


def test_chapter_with_template_has_no_findings(tmp_path):
    write_chapter(tmp_path, "alpha", GOOD_BODY)
    c = rows().chapters[0]
    assert cqt.check_chapter(c, tmp_path) == []


def test_missing_sections_and_model_are_findings(tmp_path):
    write_chapter(tmp_path, "alpha", "Intro @sec-zoo-a.\n")
    found = cqt.check_chapter(rows().chapters[0], tmp_path)
    assert any("Question and Answer" in f for f in found)
    assert any("Exercises" in f for f in found)
    assert any("Next" in f for f in found)
    assert any("sec-zoo-b" in f for f in found)


def test_exercises_are_counted_per_chapter_not_per_block(tmp_path):
    block = "::: {.questions}\n" + "\n".join(f"{i}. q" for i in range(1, 7)) + "\n:::\n\n::: {.answers}\n1. a\n:::\n\n"
    write_chapter(tmp_path, "alpha", GOOD_BODY.split("::: {.questions}")[0] + block + block)
    assert any("12 exercises" in f for f in cqt.check_chapter(rows().chapters[0], tmp_path))


def test_testbed_model_needs_no_citation_in_chapter(tmp_path):
    write_chapter(tmp_path, "beta", GOOD_BODY)
    c = cqt.Chapter("II", "beta", "q?", [("Osc", "testbed")])
    assert cqt.check_chapter(c, tmp_path) == []


def test_chapter_missing_from_quarto_is_a_finding(tmp_path):
    (tmp_path / "_quarto.yml").write_text("book:\n  chapters:\n  - index.qmd\n  - chapters/first.qmd\n  - chapters/last.qmd\n", encoding="utf-8")
    assert cqt.check_quarto(rows(), tmp_path)


def test_more_than_ten_exercises_is_a_finding(tmp_path):
    items = "\n".join(f"{i}. q" for i in range(1, 12))
    body = GOOD_BODY.split("::: {.questions}")[0] + f"::: {{.questions}}\n{items}\n:::\n"
    write_chapter(tmp_path, "alpha", body)
    assert any("exercises" in f for f in cqt.check_chapter(rows().chapters[0], tmp_path))


def test_zoo_anchor_must_exist(tmp_path):
    (tmp_path / "chapters").mkdir()
    (tmp_path / "chapters" / "zoo_of_models.qmd").write_text("## A {#sec-zoo-a}\n", encoding="utf-8")
    found = cqt.check_zoo(rows(), tmp_path)
    assert found == [f"zoo: model B of chapter alpha has no section {{#sec-zoo-b}} in chapters/zoo_of_models.qmd"]


def test_testbed_needs_no_zoo_anchor(tmp_path):
    (tmp_path / "chapters").mkdir()
    (tmp_path / "chapters" / "zoo_of_models.qmd").write_text("", encoding="utf-8")
    r = rows(TREE.replace("A:sec-zoo-a | y", "Osc:testbed | y").replace("A:sec-zoo-a, B:sec-zoo-b", "Osc:testbed"))
    assert cqt.check_zoo(r, tmp_path) == []


def test_quarto_yml_must_follow_the_tree(tmp_path):
    yml = ("book:\n  chapters:\n  - index.qmd\n  - chapters/first.qmd\n  - part: One\n    chapters:\n    - chapters/alpha.qmd\n"
           "  - part: Two\n    chapters:\n    - chapters/beta.qmd\n  - chapters/last.qmd\n")
    (tmp_path / "_quarto.yml").write_text(yml, encoding="utf-8")
    assert cqt.check_quarto(rows(), tmp_path) == []
    swapped = yml.replace("alpha", "TMP").replace("beta", "alpha").replace("TMP", "beta")
    (tmp_path / "_quarto.yml").write_text(swapped, encoding="utf-8")
    assert cqt.check_quarto(rows(), tmp_path)


def test_repository_tree_is_clean():
    text = (REPO_ROOT / "notes" / "question_tree.md").read_text(encoding="utf-8")
    r = cqt.parse_tree(text)
    assert len(r.chapters) == 13
    assert cqt.check_tree(r) == []


def test_model_without_colon_or_twice_is_a_finding():
    assert any("Name:anchor" in f for f in cqt.check_tree(rows(TREE.replace("A:sec-zoo-a, B", "A, B"))))
    assert any("twice" in f for f in cqt.check_tree(rows(TREE.replace("B:sec-zoo-b", "A:sec-zoo-a"))))


def test_part_titles_must_match(tmp_path):
    yml = ("book:\n  chapters:\n  - chapters/first.qmd\n  - part: Wrong\n    chapters:\n    - chapters/alpha.qmd\n"
           "  - part: Two\n    chapters:\n    - chapters/beta.qmd\n  - chapters/last.qmd\n")
    (tmp_path / "_quarto.yml").write_text(yml, encoding="utf-8")
    assert any("Part titles" in f for f in cqt.check_quarto(rows(), tmp_path))
