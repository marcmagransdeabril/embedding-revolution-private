"""Unit tests for sync_chapters.py: the order and the Parts of the question tree, the appendices and the generated solutions."""
from __future__ import annotations

import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent
REPO_ROOT = TESTS_DIR.parents[4]

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import sync_chapters


def entries(chapters):
    """Every file of the book in order, with the members of a Part inline."""
    out = []
    for c in chapters:
        out += c["chapters"] if isinstance(c, dict) else [c]
    return out


def test_the_book_starts_with_the_index_and_has_one_part_entry_per_part_of_the_tree():
    chapters, appendices = sync_chapters.discover_and_build_chapters_list()
    tree = sync_chapters.load_tree()
    parts = [c for c in chapters if isinstance(c, dict)]
    assert chapters[0] == "index.qmd"
    assert [p["part"] for p in parts] == [sync_chapters.part_page(n) for n, _ in tree.parts]
    assert all(isinstance(a, str) for a in appendices)


def test_chapters_follow_the_order_of_the_tree_whichever_of_them_exist():
    chapters, _ = sync_chapters.discover_and_build_chapters_list()
    tree = sync_chapters.load_tree()
    stems = [Path(c).stem for c in entries(chapters)[1:]]
    order = sync_chapters.book_order(tree)
    listed = [s for s in stems if s in order]
    assert listed == [s for s in order if s in listed]


def test_the_introduction_comes_first_and_the_epilogue_last_outside_the_parts():
    chapters, _ = sync_chapters.discover_and_build_chapters_list()
    assert chapters[1] == "chapters/symbols_without_interior.qmd"
    assert chapters[-1] == "chapters/epilogue.qmd"


def test_the_zoo_is_an_appendix_and_the_solutions_close_the_book():
    chapters, appendices = sync_chapters.discover_and_build_chapters_list()
    assert "chapters/zoo_of_models.qmd" not in entries(chapters)
    if (REPO_ROOT / "chapters" / "zoo_of_models.qmd").is_file():
        assert appendices[0] == "chapters/zoo_of_models.qmd"
    if sync_chapters.SOLUTIONS_QMD.is_file():
        assert appendices[-1] == "chapters/solutions.qmd"
        assert appendices.count("chapters/solutions.qmd") == 1


def test_a_chapter_outside_the_tree_is_listed_after_the_others_and_not_lost():
    chapters, _ = sync_chapters.discover_and_build_chapters_list()
    names = {Path(c).stem for c in entries(chapters)[1:]}
    on_disk = {p.stem for p in (REPO_ROOT / "chapters").glob("*.qmd")} - {"solutions", *sync_chapters.APPENDICES}
    assert on_disk <= names


def test_every_part_page_exists():
    chapters, _ = sync_chapters.discover_and_build_chapters_list()
    for c in chapters:
        if isinstance(c, dict):
            assert (REPO_ROOT / c["part"]).is_file(), c["part"]


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
