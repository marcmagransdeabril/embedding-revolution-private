"""Unit tests for sync_solutions.py: extraction of colocated answers blocks."""
from __future__ import annotations

import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import sync_solutions

CHAPTER = """\
---
title: T
---

## A

::: {.questions}
1. Q1

2. Q2
:::

::: {.answers}
1. A1

2. A2 with code:

   ```python
   1. not an item
   ::: not a div
   ```
:::

## B

::: {.questions}
1. Q3
:::

::: {.answers}
1. A3
:::
"""


def _chapter(tmp_path, name="ch1.qmd", text=CHAPTER):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_find_div_blocks_counts_items_and_ignores_code_fences(tmp_path):
    path = _chapter(tmp_path)
    blocks = sync_solutions.find_div_blocks(path.read_text(encoding="utf-8"), sync_solutions._ANSWERS_OPEN_RE)
    assert [b.n_items for b in blocks] == [2, 1]
    assert all(b.ref is None for b in blocks)


def test_render_merges_blocks_and_renumbers(tmp_path):
    out = sync_solutions.render_solutions([_chapter(tmp_path)])
    assert out.count('::: {.answers ref="ch1"}') == 1
    assert "\n3. A3\n" in out
    assert "   1. not an item" in out  # code fence content untouched
    assert out.startswith("# Solutions {.unnumbered}")


def test_render_skips_chapters_without_answers_and_solutions_file(tmp_path):
    plain = _chapter(tmp_path, "plain.qmd", "---\ntitle: P\n---\n\nNo questions.\n")
    solutions = _chapter(tmp_path, "solutions.qmd", "# Solutions {.unnumbered}\n")
    out = sync_solutions.render_solutions([plain, _chapter(tmp_path), solutions])
    assert "ref=\"plain\"" not in out and "ref=\"solutions\"" not in out
    assert 'ref="ch1"' in out


def test_ref_blocks_are_not_treated_as_colocated(tmp_path):
    path = _chapter(tmp_path, text='::: {.answers ref="x"}\n1. A\n:::\n')
    assert sync_solutions.chapter_answers(path) == []


def test_sync_solutions_writes_then_check_passes(tmp_path):
    _chapter(tmp_path)
    target = tmp_path / "solutions.qmd"
    assert sync_solutions.sync_solutions(check=True, target=target) is False  # missing -> stale
    assert sync_solutions.sync_solutions(target=target) is True
    assert target.is_file()
    assert sync_solutions.sync_solutions(check=True, target=target) is True


def test_sync_solutions_dry_run_does_not_write(tmp_path):
    _chapter(tmp_path)
    target = tmp_path / "solutions.qmd"
    assert sync_solutions.sync_solutions(dry_run=True, target=target) is True
    assert not target.exists()


def test_book_order_follows_quarto_yml_then_name(tmp_path, monkeypatch):
    qy = tmp_path / "_quarto.yml"
    qy.write_text(
        "book:\n  chapters:\n  - index.qmd\n  - part: P\n    chapters:\n    - chapters/b.qmd\n    - chapters/a.qmd\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(sync_solutions, "QUARTO_YML", qy)
    files = [tmp_path / n for n in ("a.qmd", "z.qmd", "b.qmd", "c.qmd")]
    assert [p.name for p in sync_solutions.book_order(files)] == ["b.qmd", "a.qmd", "c.qmd", "z.qmd"]


def test_repository_solutions_file_is_current():
    """chapters/solutions.qmd must match what the chapters' answers blocks generate."""
    assert sync_solutions.sync_solutions(check=True) is True
