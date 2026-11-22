"""Unit tests for sync_chapters.py: the flat order of the roadmap, the appendices and the generated solutions."""
from __future__ import annotations

import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent
REPO_ROOT = TESTS_DIR.parents[4]

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import sync_chapters


def test_the_book_is_a_flat_list_that_starts_with_the_index():
    chapters, appendices = sync_chapters.discover_and_build_chapters_list()
    assert chapters[0] == "index.qmd"
    assert all(isinstance(c, str) for c in chapters), "there are no Parts: every entry is a file"
    assert all(isinstance(a, str) for a in appendices)


def test_chapters_follow_the_order_of_the_roadmap_whichever_of_them_exist():
    chapters, _ = sync_chapters.discover_and_build_chapters_list()
    stems = [Path(c).stem for c in chapters[1:]]
    listed = [s for s in stems if s in sync_chapters.ORDER]
    assert listed == [s for s in sync_chapters.ORDER if s in listed]


def test_the_introduction_comes_first_then_the_summary_then_the_properties_then_the_epilogue():
    order = sync_chapters.ORDER
    assert order[:3] == ["symbols_without_interior", "tests_of_meaning", "properties_of_meaning"]
    assert order[3] == "likeness_as_nearness" and order[-1] == "epilogue"


def test_the_dimensionality_chapter_is_an_appendix_and_the_solutions_close_the_book():
    chapters, appendices = sync_chapters.discover_and_build_chapters_list()
    assert "chapters/curse_of_dimensionality.qmd" not in chapters
    if (REPO_ROOT / "chapters" / "curse_of_dimensionality.qmd").is_file():
        assert appendices[0] == "chapters/curse_of_dimensionality.qmd"
    if sync_chapters.SOLUTIONS_QMD.is_file():
        assert appendices[-1] == "chapters/solutions.qmd"
        assert appendices.count("chapters/solutions.qmd") == 1


def test_a_chapter_outside_the_roadmap_is_listed_after_the_others_and_not_lost():
    chapters, _ = sync_chapters.discover_and_build_chapters_list()
    names = {Path(c).stem for c in chapters[1:]}
    on_disk = {p.stem for p in (REPO_ROOT / "chapters").glob("*.qmd")} - {"solutions", *sync_chapters.APPENDICES}
    assert on_disk <= names


def test_sync_quarto_yml_dry_run():
    assert sync_chapters.sync_quarto_yml(dry_run=True, verbose=False) is True


def test_title_comes_from_a_labelled_h1_without_its_attributes(tmp_path):
    """Titles are `# Title {#sec-ch-...}`; the bare title is what is read."""
    p = tmp_path / "x.qmd"
    p.write_text("---\nstatus: idea\n---\n\n# Vector Databases, RAG {#sec-ch-vector-databases}\n\ntext\n", encoding="utf-8")
    assert sync_chapters.extract_title_from_qmd(p) == "Vector Databases, RAG"
    q = tmp_path / "y.qmd"
    q.write_text("---\ntitle: Front Matter Title\nstatus: idea\n---\n\n## Section\n", encoding="utf-8")
    assert sync_chapters.extract_title_from_qmd(q) == "Front Matter Title"
    r = tmp_path / "z.qmd"
    r.write_text("# Plain Title\n\ntext\n", encoding="utf-8")
    assert sync_chapters.extract_title_from_qmd(r) == "Plain Title"
