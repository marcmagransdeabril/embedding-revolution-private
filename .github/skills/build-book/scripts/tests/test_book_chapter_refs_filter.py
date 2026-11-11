"""filters/book-chapter-refs.lua: chapter references in HTML, including pages without a chapter number.

Quarto 1.5 renders @sec-ch-x as "3 Title" in an unnumbered page (quarto-dev/quarto-cli#14132); the filter makes it
"Chapter 3" there and everywhere in HTML. These tests render a scratch book with `quarto`, so they are skipped
when it is not installed.
"""
from __future__ import annotations

import html
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]
FILTER = REPO_ROOT / "filters" / "book-chapter-refs.lua"

pytestmark = pytest.mark.skipif(shutil.which("quarto") is None, reason="quarto is not installed")

REFS = "REFS: @sec-ch-alpha, [-@sec-ch-beta], and Chapters [-@sec-ch-alpha] to [-@sec-ch-beta]."


def make_book(tmp_path: Path, extra: str = "") -> Path:
    (tmp_path / "chapters").mkdir()
    (tmp_path / "filters").mkdir()
    shutil.copy(FILTER, tmp_path / "filters" / FILTER.name)
    (tmp_path / "_quarto.yml").write_text(
        "project:\n  type: book\n"
        "book:\n  title: T\n  chapters:\n  - index.qmd\n  - chapters/alpha.qmd\n  - chapters/beta_two.qmd\n"
        "  - chapters/epilogue.qmd\n"
        "format:\n  html:\n    number-sections: true\n    filters:\n    - filters/book-chapter-refs.lua\n",
        encoding="utf-8")
    (tmp_path / "index.qmd").write_text(f"# Preface {{.unnumbered}}\n\n{REFS}\n", encoding="utf-8")
    (tmp_path / "chapters" / "alpha.qmd").write_text(f"---\nstatus: idea\n---\n\n# Alpha {{#sec-ch-alpha}}\n\n{REFS}\n", encoding="utf-8")
    # beta_two checks that the label of chapters/beta_two.qmd is sec-ch-beta-two (underscores become hyphens)
    (tmp_path / "chapters" / "beta_two.qmd").write_text("# Beta {#sec-ch-beta-two}\n\ntext\n", encoding="utf-8")
    (tmp_path / "chapters" / "epilogue.qmd").write_text(f"# Epilogue {{.unnumbered}}\n\n{REFS}\n{extra}\n", encoding="utf-8")
    return tmp_path


def render(book: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["quarto", "render", "--to", "html"], cwd=book, capture_output=True, text=True, timeout=300)


def sentence(book: Path, page: str) -> str:
    s = (book / "_book" / page).read_text(encoding="utf-8")
    i = s.index("REFS:")
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s[i:s.index("</p>", i)])))


def test_chapter_references_read_chapter_n_in_every_kind_of_page(tmp_path):
    book = make_book(tmp_path)
    book_text = (book / "index.qmd").read_text().replace("sec-ch-beta]", "sec-ch-beta-two]").replace("sec-ch-beta,", "sec-ch-beta-two,")
    (book / "index.qmd").write_text(book_text)
    for f in ("chapters/alpha.qmd", "chapters/epilogue.qmd"):
        p = book / f
        p.write_text(p.read_text().replace("sec-ch-beta]", "sec-ch-beta-two]"))
    r = render(book)
    assert r.returncode == 0, r.stderr[-800:]
    expected = "REFS: Chapter 1, 2, and Chapters 1 to 2."
    for page in ("index.html", "chapters/alpha.html", "chapters/epilogue.html"):
        assert sentence(book, page) == expected, page


def test_the_links_point_to_the_chapter_file_from_the_root_and_from_chapters(tmp_path):
    book = make_book(tmp_path)
    for f in ("index.qmd", "chapters/alpha.qmd", "chapters/epilogue.qmd"):
        p = book / f
        p.write_text(p.read_text().replace("sec-ch-beta", "sec-ch-beta-two"))
    assert render(book).returncode == 0
    assert 'href="./chapters/alpha.html#sec-ch-alpha">Chapter 1</a>' in (book / "_book" / "index.html").read_text()
    assert 'href="../chapters/alpha.html#sec-ch-alpha">Chapter 1</a>' in (book / "_book" / "chapters" / "epilogue.html").read_text()


def test_an_unknown_label_stops_the_build(tmp_path):
    book = make_book(tmp_path, extra="See @sec-ch-nonexistent.")
    for f in ("index.qmd", "chapters/alpha.qmd", "chapters/epilogue.qmd"):
        p = book / f
        p.write_text(p.read_text().replace("sec-ch-beta", "sec-ch-beta-two"))
    r = render(book)
    assert r.returncode != 0
    assert "no numbered chapter for @sec-ch-nonexistent" in r.stdout + r.stderr


def test_a_reference_with_a_prefix_stops_the_build(tmp_path):
    book = make_book(tmp_path, extra="See [Chapter -@sec-ch-alpha].")
    for f in ("index.qmd", "chapters/alpha.qmd", "chapters/epilogue.qmd"):
        p = book / f
        p.write_text(p.read_text().replace("sec-ch-beta", "sec-ch-beta-two"))
    r = render(book)
    assert r.returncode != 0
    assert "write a chapter reference alone" in r.stdout + r.stderr
