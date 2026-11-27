#!/usr/bin/env python3
"""Sync Quarto book chapter registry (_quarto.yml) with chapters/ directory.

The order of the book, and its three Parts, are read from notes/question_tree.md (the single source, also checked by
check_question_tree.py): the index, the chapter outside the Parts that comes first, one `part:` entry per Part (a page
`parts/part_<n>.qmd` with the chapters of the Part), the chapter outside the Parts that comes last. Appendices and the
generated solutions close the book.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
QUARTO_YML = REPO_ROOT / "_quarto.yml"
CHAPTERS_DIR = REPO_ROOT / "chapters"
INDEX_QMD = REPO_ROOT / "index.qmd"
# Back matter: solutions to the review questions of every chapter. It is not a
# numbered chapter, so it is excluded from discovery and always listed last.
SOLUTIONS_QMD = CHAPTERS_DIR / "solutions.qmd"

PARTS_DIR = REPO_ROOT / "parts"
# Appendices follow the chapters; the solutions are generated and always come last.
APPENDICES = ["zoo_of_models"]


def load_tree():
    """The question tree of notes/question_tree.md."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import check_question_tree

    return check_question_tree.parse_tree((REPO_ROOT / "notes" / "question_tree.md").read_text(encoding="utf-8"))


def part_page(number: str) -> str:
    """The page of Part `number` (a roman numeral): parts/part_i.qmd."""
    return f"parts/part_{number.lower()}.qmd"


def book_order(tree) -> list[str]:
    """The stems of the tree in the order of the book."""
    return [tree.first] + [c.stem for c in tree.chapters] + [tree.last]


def extract_title_from_qmd(qmd_path: Path) -> str:
    """Extract chapter title from YAML frontmatter or first heading."""
    if not qmd_path.is_file():
        return qmd_path.stem.replace("_", " ").title()

    text = qmd_path.read_text(encoding="utf-8")
    fm_match = re.match(r"^---\r?\n(.*?)\r?\n---", text, flags=re.DOTALL)
    if fm_match:
        try:
            fm = yaml.safe_load(fm_match.group(1))
            if isinstance(fm, dict) and "title" in fm:
                return str(fm["title"])
        except Exception:
            pass

    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            # Drop the attributes of `# Title {#sec-ch-... .unnumbered}`: only the words are matched against the outline.
            return re.sub(r"\s*\{[^}]*\}\s*$", "", line[2:]).strip()

    return qmd_path.stem.replace("_", " ").title()


def discover_and_build_chapters_list() -> tuple[list[Any], list[str]]:
    """Scan chapters/ and return the book's entries (files and Parts) in the order of the tree, and the list of appendices."""
    stems = {p.stem: p for p in CHAPTERS_DIR.glob("*.qmd") if p != SOLUTIONS_QMD}
    tree = load_tree()
    chapter = lambda s: f"chapters/{stems[s].name}"  # noqa: E731
    chapters: list[Any] = ["index.qmd"]
    if tree.first in stems:
        chapters.append(chapter(tree.first))
    for number, _title in tree.parts:
        members = [chapter(c.stem) for c in tree.chapters if c.part == number and c.stem in stems]
        chapters.append({"part": part_page(number), "chapters": members})
    if tree.last in stems:
        chapters.append(chapter(tree.last))
    # A chapter that is not in the tree is listed after the others, so that it is not lost
    known = set(book_order(tree)) | set(APPENDICES)
    chapters += [f"chapters/{p.name}" for s, p in sorted(stems.items()) if s not in known]
    appendices = [chapter(s) for s in APPENDICES if s in stems]
    if SOLUTIONS_QMD.is_file():
        appendices.append(f"chapters/{SOLUTIONS_QMD.name}")
    return chapters, appendices


def sync_quarto_yml(dry_run: bool = False, verbose: bool = False) -> bool:
    """Synchronize _quarto.yml with discovered chapters."""
    if not QUARTO_YML.is_file():
        print(f"Error: {QUARTO_YML} not found", file=sys.stderr)
        return False

    with open(QUARTO_YML, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    new_chapters, appendices = discover_and_build_chapters_list()
    old_chapters = config.get("book", {}).get("chapters", [])

    if verbose:
        print("Discovered chapters structure:")
        print(yaml.dump({"chapters": new_chapters}, sort_keys=False))

    if "book" not in config:
        config["book"] = {}

    config["book"]["chapters"] = new_chapters
    config["book"]["appendices"] = appendices

    if dry_run:
        print("[Dry Run] Would update _quarto.yml chapters list.")
        return True

    with open(QUARTO_YML, "w", encoding="utf-8") as f:
        yaml.dump(config, f, sort_keys=False, default_flow_style=False, allow_unicode=True)

    print(f"✓ Synchronized _quarto.yml with {len([p for p in CHAPTERS_DIR.glob('*.qmd') if p != SOLUTIONS_QMD])} chapter(s).")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync Quarto book chapters with chapters/ directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview chapter list without modifying _quarto.yml")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print verbose details")
    args = parser.parse_args()

    success = sync_quarto_yml(dry_run=args.dry_run, verbose=args.verbose)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
