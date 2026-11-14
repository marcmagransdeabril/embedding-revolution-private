#!/usr/bin/env python3
"""Fail when the prose of a chapter is missing from the PDF.

LaTeX can lose text without an error (a page that does not fit, a float that swallows what follows). This script takes every
paragraph of the chapters, keeps the runs of plain words (no math, code, citations, cross-references, links), and looks for the
first and the last words of each paragraph in the text of the PDF (`pdftotext`). Spacing, hyphenation, case, ligatures and
punctuation are ignored on both sides. A paragraph with no run of --min-words plain words is not checked.

Usage: check_pdf_text.py [--pdf _book/The-Embedding-Revolution.pdf] [--min-words 5] [chapter.qmd ...]
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SKIP_LINE = re.compile(r"^\s*(\||\$\$|```|!\[|:::|#|<|---|\\|\{|\[\^|%|\|)")
REMOVE = [
    r"\$\$.*?\$\$", r"\$[^$]*\$",  # math
    r"`[^`]*`",  # code
    r"\[@[^\]]*\]", r"@[A-Za-z][\w:.-]*",  # citations and cross-references
    r"\[([^\]]*)\]\([^)]*\)",  # links: keep the text below
    r"\{[^}]*\}",  # attributes
]


def normalize(text: str) -> str:
    """Lowercase letters and digits only, with ligatures and accents decomposed."""
    text = unicodedata.normalize("NFKD", text).lower()
    return re.sub(r"[^a-z0-9]", "", text)


def paragraphs(path: Path):
    """Yields (first line number, text) of the prose paragraphs of a .qmd file."""
    lines = path.read_text(encoding="utf-8").splitlines()
    block, start, in_code, in_math, in_yaml, in_comment = [], 0, False, False, False, False
    for number, line in enumerate(lines, 1):
        if number == 1 and line.strip() == "---":
            in_yaml = True
            continue
        if in_yaml:
            in_yaml = line.strip() != "---"
            continue
        if in_comment or line.lstrip().startswith("<!--"):  # an HTML comment is not rendered
            in_comment = "-->" not in line
            if block:
                yield start, " ".join(block)
            block = []
            continue
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if line.strip() == "$$":
            in_math = not in_math
            continue
        if in_code or in_math or SKIP_LINE.match(line):
            if block:
                yield start, " ".join(block)
            block = []
            continue
        if not line.strip():
            if block:
                yield start, " ".join(block)
            block = []
            continue
        item = re.match(r"^\s*(\d+\.|[-*+])\s+", line)
        if item and block:  # a list item starts a new block
            yield start, " ".join(block)
            block = []
        if not block:
            start = number
        block.append(line[item.end():] if item else line)
    if block:
        yield start, " ".join(block)


def runs(paragraph: str, min_words: int) -> list[str]:
    """Runs of at least min_words plain words, in order."""
    text = paragraph
    for pattern in REMOVE:
        text = re.sub(pattern, lambda m: " \x00 " if not m.groups() else f" {m.group(1)} ", text)
    text = text.replace("*", " ").replace("_", " ").replace("—", " \x00 ").replace("–", " \x00 ")
    found = []
    for piece in text.split("\x00"):
        for part in re.split(r"[^\sA-Za-z'’,.;:!?()\"“”-]+|\S*\d\S*|[\\^{}=<>|]", piece):  # a number or a symbol ends a run
            words = re.findall(r"[A-Za-z][A-Za-z'’-]*[A-Za-z]|[A-Za-z]", part)
            if len(words) >= min_words:
                found.append(" ".join(words))
    return found


def missing(chapters: list[Path], pdf_text: str, min_words: int):
    haystack = normalize(pdf_text)
    for chapter in chapters:
        for line, paragraph in paragraphs(chapter):
            r = runs(paragraph, min_words)
            ends = [" ".join(r[0].split()[:min_words]), " ".join(r[-1].split()[-min_words:])] if r else []
            for snippet in dict.fromkeys(ends):
                # inline fractions make pdftotext interleave lines, so a snippet that crosses such a line is retried with 3 words
                short = " ".join(snippet.split()[-3:]) if snippet == ends[-1] else " ".join(snippet.split()[:3])
                if normalize(snippet) not in haystack and normalize(short) not in haystack:
                    yield chapter, line, snippet


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pdf", type=Path, default=ROOT / "_book" / "The-Embedding-Revolution.pdf")
    parser.add_argument("--min-words", type=int, default=5)
    parser.add_argument("chapters", nargs="*", type=Path, help="default: index.qmd and chapters/*.qmd")
    args = parser.parse_args()
    chapters = args.chapters or [ROOT / "index.qmd", *sorted((ROOT / "chapters").glob("*.qmd"))]
    pages = subprocess.run(["pdftotext", str(args.pdf), "-"], capture_output=True, text=True, check=True).stdout.split("\f")
    pdf_text = "\n".join("\n".join(page.splitlines()[1:]) for page in pages)  # without the running head of each page
    bad = list(missing([c for c in chapters if c.is_file()], pdf_text, args.min_words))
    for chapter, line, snippet in bad:
        print(f"ERROR: {chapter.relative_to(ROOT)}:{line}: not found in the PDF: \"{snippet[:90]}\"", file=sys.stderr)
    if bad:
        print(f"\nERROR: {len(bad)} paragraph(s) lost text in {args.pdf.name} (see Overfull \\vbox in the LaTeX log; "
              f"a figure with fig-pos=\"t\" or a long box near it is the usual cause).", file=sys.stderr)
        return 1
    print(f"All paragraphs of {len(chapters)} file(s) are in {args.pdf.name}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
