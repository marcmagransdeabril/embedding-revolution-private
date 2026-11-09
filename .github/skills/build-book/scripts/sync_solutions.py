#!/usr/bin/env python3
"""Generate chapters/solutions.qmd from the solutions written inside each chapter.

Authoring model
---------------
Solutions are written next to their questions, in the chapter that asks them::

    ::: {.questions}
    1. First question.

    2. Second question.
    :::

    ::: {.answers}
    1. Solution to the first question.

    2. Solution to the second question.
    :::

Every ``.questions`` block must be followed immediately by one ``.answers``
block with the same number of items (``validate_book.py`` enforces this).
``filters/book-questions.lua`` drops those colocated ``.answers`` blocks when a
chapter is rendered, so the reader never sees them inline.

This script collects them, in book order, into the back-matter file
``chapters/solutions.qmd`` (one ``::: {.answers ref="<chapter-stem>"}`` block per
chapter, items renumbered 1..n). That file is GENERATED: never edit it by hand.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
QUARTO_YML = REPO_ROOT / "_quarto.yml"
CHAPTERS_DIR = REPO_ROOT / "chapters"
SOLUTIONS_QMD = CHAPTERS_DIR / "solutions.qmd"

SOLUTIONS_FILENAME = "solutions.qmd"

_QUESTIONS_OPEN_RE = re.compile(r"^:::+\s*\{\.questions(\s[^}]*)?\}\s*$")
_ANSWERS_OPEN_RE = re.compile(r"^:::+\s*\{\.answers(\s[^}]*)?\}\s*$")
_ANY_DIV_OPEN_RE = re.compile(r"^:::+\s*\S")
_DIV_CLOSE_RE = re.compile(r"^:::+\s*$")
_ITEM_RE = re.compile(r"^(\d+)\.(\s)")
_REF_RE = re.compile(r'ref="([^"]+)"')

GENERATED_HEADER = """\
# Solutions {.unnumbered}

<!--
GENERATED FILE. DO NOT EDIT BY HAND.

This file is produced by .github/skills/build-book/scripts/sync_solutions.py
(run `make sync-solutions`) from the answers blocks written inside each
chapter, immediately after the matching review-questions block. Edit the
solutions there; `make validate` fails if this file is out of date.
-->
"""


@dataclass
class DivBlock:
    """A fenced div found in a chapter: where it is and what it contains."""

    start: int          # 1-based line of the opening `:::`
    end: int            # 1-based line of the closing `:::`
    attrs: str          # text inside `{...}` after the class name
    body: list[str]     # raw lines between the opening and closing fences

    @property
    def n_items(self) -> int:
        return len(top_level_item_indices(self.body))

    @property
    def ref(self) -> str | None:
        m = _REF_RE.search(self.attrs)
        return m.group(1) if m else None


def _is_fence(line: str) -> bool:
    return line.strip().startswith("```")


def top_level_item_indices(lines: list[str]) -> list[int]:
    """Indices of the lines that start a top-level ordered-list item."""
    out: list[int] = []
    in_fence = False
    for i, raw in enumerate(lines):
        if _is_fence(raw):
            in_fence = not in_fence
            continue
        if not in_fence and _ITEM_RE.match(raw):
            out.append(i)
    return out


def find_div_blocks(text: str, open_re: re.Pattern[str]) -> list[DivBlock]:
    """Return every top-level fenced div whose opening line matches `open_re`.

    Fenced code blocks are skipped; nested divs inside a matching div are
    tolerated (their fences are balanced and kept in the body).
    """
    blocks: list[DivBlock] = []
    in_fence = False
    current: dict | None = None
    depth = 0
    for lineno, raw in enumerate(text.splitlines(), start=1):
        if _is_fence(raw):
            in_fence = not in_fence
            if current is not None:
                current["body"].append(raw)
            continue
        if in_fence:
            if current is not None:
                current["body"].append(raw)
            continue
        line = raw.strip()
        if current is None:
            m = open_re.match(line)
            if m:
                current = {"start": lineno, "attrs": m.group(1) or "", "body": []}
                depth = 1
            continue
        if _DIV_CLOSE_RE.match(line):
            depth -= 1
            if depth == 0:
                blocks.append(DivBlock(current["start"], lineno, current["attrs"].strip(), current["body"]))
                current = None
                continue
        elif _ANY_DIV_OPEN_RE.match(line):
            depth += 1
        current["body"].append(raw)
    return blocks


def renumber_items(lines: list[str], start: int = 1) -> tuple[list[str], int]:
    """Renumber top-level list items sequentially; return (lines, next_number)."""
    out = list(lines)
    n = start
    for i in top_level_item_indices(lines):
        out[i] = _ITEM_RE.sub(lambda m: f"{n}.{m.group(2)}", lines[i], count=1)
        n += 1
    return out, n


def _trim_blank_edges(lines: list[str]) -> list[str]:
    start, end = 0, len(lines)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return lines[start:end]


def chapter_answers(path: Path) -> list[DivBlock]:
    """Colocated `.answers` blocks (those without `ref=`) of a chapter file."""
    text = path.read_text(encoding="utf-8")
    return [b for b in find_div_blocks(text, _ANSWERS_OPEN_RE) if b.ref is None]


def book_order(files: list[Path]) -> list[Path]:
    """Sort chapter files in `_quarto.yml` order; unlisted files follow by name."""
    listed: list[str] = []
    if QUARTO_YML.is_file():
        config = yaml.safe_load(QUARTO_YML.read_text(encoding="utf-8")) or {}

        def walk(entries: list) -> None:
            for entry in entries or []:
                if isinstance(entry, str):
                    listed.append(entry)
                elif isinstance(entry, dict):
                    walk(entry.get("chapters", []))

        walk((config.get("book") or {}).get("chapters", []))

    def key(p: Path) -> tuple[int, int, str]:
        rel = f"chapters/{p.name}"
        return (0, listed.index(rel), p.name) if rel in listed else (1, 0, p.name)

    return sorted(files, key=key)


def render_solutions(chapter_files: list[Path]) -> str:
    """Return the full text of solutions.qmd for the given chapter files."""
    parts: list[str] = [GENERATED_HEADER]
    for path in book_order([p for p in chapter_files if p.name != SOLUTIONS_FILENAME]):
        blocks = chapter_answers(path)
        if not blocks:
            continue
        merged: list[str] = []
        counter = 1
        for block in blocks:
            body, counter = renumber_items(_trim_blank_edges(block.body), counter)
            if merged:
                merged.append("")
            merged.extend(body)
        parts.append("\n".join([f'::: {{.answers ref="{path.stem}"}}', *merged, ":::"]) + "\n")
    return "\n".join(parts)


def chapter_files_in(chapters_dir: Path = CHAPTERS_DIR) -> list[Path]:
    return sorted(p for p in chapters_dir.glob("*.qmd") if p.name != SOLUTIONS_FILENAME)


def sync_solutions(dry_run: bool = False, check: bool = False, target: Path | None = None) -> bool:
    """Regenerate solutions.qmd. With `check`, only report whether it is current."""
    target = target or SOLUTIONS_QMD
    expected = render_solutions(chapter_files_in(target.parent))
    has_answers = "::: {.answers" in expected
    current = target.read_text(encoding="utf-8") if target.is_file() else None

    if not has_answers and current is None:
        print("No colocated solutions found; nothing to generate.")
        return True
    if current == expected:
        print(f"✓ {target.name} is up to date.")
        return True
    if check:
        print(f"✗ {target.name} is out of date; run `make sync-solutions`.", file=sys.stderr)
        return False
    if dry_run:
        print(f"[Dry Run] Would rewrite {target.name}.")
        return True
    target.write_text(expected, encoding="utf-8")
    print(f"✓ Generated {target.name} from the answers blocks of the chapters.")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate chapters/solutions.qmd from colocated answers blocks")
    parser.add_argument("--check", action="store_true", help="Exit 1 if solutions.qmd is out of date (writes nothing)")
    parser.add_argument("--dry-run", action="store_true", help="Report what would change without writing")
    args = parser.parse_args()
    sys.exit(0 if sync_solutions(dry_run=args.dry_run, check=args.check) else 1)


if __name__ == "__main__":
    main()
