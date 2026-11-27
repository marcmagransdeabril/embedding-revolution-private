#!/usr/bin/env python3
"""Check notes/question_tree.md, and the book against it.

The tree is the structure of the book: one question per chapter, one or two models per chapter, the chapters in order,
grouped in Parts. Checks, in stages (a stage is run by a flag, so that the checker can run before the book has been
restructured):

  (default)   the tree itself: one question each, one or two models, valid zoo anchors, no chapter twice.
  --files     each chapter file has the template (Question and Answer, Next, Exercises), names its models by their zoo
              anchors, and has at most 10 exercises.
  --zoo       each model anchor exists in chapters/zoo_of_models.qmd.
  --quarto    _quarto.yml lists the chapters in the order and the Parts of the tree.
  --all       all of the above.

Exit status 1 when there is a finding.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
TREE = REPO_ROOT / "notes" / "question_tree.md"
ANCHOR = re.compile(r"^sec-zoo-[a-z0-9-]+$")
MAX_EXERCISES = 10


@dataclass
class Chapter:
    part: str
    stem: str
    question: str
    models: list[tuple[str, str]]


@dataclass
class Tree:
    chapters: list[Chapter] = field(default_factory=list)
    first: str = ""
    last: str = ""
    outside: dict[str, str] = field(default_factory=dict)  # stem -> question of the chapters outside the Parts
    parts: list[tuple[str, str]] = field(default_factory=list)  # (number, title), in order
    errors: list[str] = field(default_factory=list)


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _table(text: str, heading: str) -> list[list[str]]:
    """The body rows of the first table after the level-2 `heading`."""
    m = re.search(rf"^## {re.escape(heading)}\s*$", text, re.M)
    if not m:
        return []
    out, seen = [], 0
    for line in text[m.end():].splitlines():
        if line.startswith("## "):
            break
        if line.startswith("|"):
            seen += 1
            if seen > 2:  # header and separator
                out.append(_cells(line))
    return out


def parse_tree(text: str) -> Tree:
    tree = Tree()
    for r in _table(text, "Parts"):
        if len(r) == 3:
            tree.parts.append((r[0], r[1]))
        else:
            tree.errors.append(f"tree: a row of the Parts table must have 3 cells: {r}")
    for r in _table(text, "Chapters"):
        if len(r) != 5:
            tree.errors.append(f"tree: a row of the Chapters table must have 5 cells, not {len(r)}: {r}")
            continue
        part, stem, question, models, _ = r
        pairs = []
        for item in filter(None, (s.strip() for s in models.split(","))):
            name, sep, anchor = item.rpartition(":")
            if not sep:
                tree.errors.append(f"tree: model '{item}' of {stem} must be written Name:anchor")
                continue
            pairs.append((name.strip(), anchor.strip()))
        tree.chapters.append(Chapter(part, stem, question, pairs))
    for r in _table(text, "Chapters outside the Parts"):
        if len(r) != 3:
            tree.errors.append(f"tree: a row of the outside-Parts table must have 3 cells: {r}")
            continue
        pos, stem, question = r
        tree.outside[stem] = question
        if pos == "first":
            tree.first = stem
        elif pos == "last":
            tree.last = stem
    return tree


def check_tree(tree: Tree) -> list[str]:
    found, seen = list(tree.errors), set()
    for stem, q in tree.outside.items():
        if not q.endswith("?") or q.count("?") != 1:
            found.append(f"tree: {stem} must have one question ending with a question mark")
    if len(tree.parts) != len({c.part for c in tree.chapters}) or [p for p, _ in tree.parts] != list(dict.fromkeys(c.part for c in tree.chapters)):
        found.append("tree: the Parts table and the Part column of the Chapters table disagree")
    for c in tree.chapters:
        if c.stem in seen:
            found.append(f"tree: chapter {c.stem} is listed twice")
        seen.add(c.stem)
        if not c.question.endswith("?"):
            found.append(f"tree: the question of {c.stem} must end with a question mark")
        elif c.question.count("?") != 1:
            found.append(f"tree: {c.stem} must have one question, it has {c.question.count('?')}")
        if len({n for n, _ in c.models}) != len(c.models):
            found.append(f"tree: {c.stem} lists a model twice")
        if c.stem in tree.outside:
            found.append(f"tree: {c.stem} is both in a Part and outside the Parts")
        if not 1 <= len(c.models) <= 2:
            found.append(f"tree: {c.stem} must have one or two models, it has {len(c.models)}")
        for name, anchor in c.models:
            if not name or not (ANCHOR.match(anchor) or anchor == "testbed"):
                found.append(f"tree: model '{name}' of {c.stem} has a bad anchor '{anchor}' (sec-zoo-... or testbed)")
    if not tree.first or not tree.last:
        found.append("tree: the first and the last chapter outside the Parts must be given")
    return found


def _chapter_text(stem: str, root: Path) -> str | None:
    p = root / "chapters" / f"{stem}.qmd"
    return p.read_text(encoding="utf-8") if p.exists() else None


def check_chapter(c: Chapter, root: Path) -> list[str]:
    text = _chapter_text(c.stem, root)
    if text is None:
        return [f"{c.stem}: chapters/{c.stem}.qmd does not exist"]
    found = []
    if not re.search(r"^## Question and Answer\b", text, re.M):
        found.append(f"{c.stem}: no section '## Question and Answer'")
    if not re.search(r"^\*Next:\*", text, re.M):
        found.append(f"{c.stem}: no line starting '*Next:*'")
    if not re.search(r"^## Exercises\b", text, re.M):
        found.append(f"{c.stem}: no section '## Exercises'")
    for name, anchor in c.models:
        if anchor != "testbed" and f"@{anchor}" not in text:
            found.append(f"{c.stem}: model {name} is not cited by its zoo anchor @{anchor}")
    n = sum(len(re.findall(r"^\d+\. ", b, re.M)) for b in re.findall(r"::: \{\.questions\}\n(.*?)\n:::", text, re.S))
    if n > MAX_EXERCISES:
        found.append(f"{c.stem}: {n} exercises, at most {MAX_EXERCISES}")
    return found


def check_zoo(tree: Tree, root: Path) -> list[str]:
    zoo = _chapter_text("zoo_of_models", root) or ""
    ids = set(re.findall(r"\{#(sec-zoo-[a-z0-9-]+)", zoo))
    return [f"zoo: model {name} of chapter {c.stem} has no section {{#{anchor}}} in chapters/zoo_of_models.qmd"
            for c in tree.chapters for name, anchor in c.models if anchor != "testbed" and anchor not in ids]


def _part_title(part: str, root: Path) -> str | None:
    """The title of a Part: the value of `part:`, or the first heading of the page it names."""
    if not str(part).endswith(".qmd"):
        return part
    page = root / part
    if not page.exists():
        return None
    m = re.search(r"^# (.*?)(?:\s*\{[^}]*\})?\s*$", page.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else None


def check_quarto(tree: Tree, root: Path) -> list[str]:
    cfg = yaml.safe_load((root / "_quarto.yml").read_text(encoding="utf-8"))
    flat, groups = [], []
    for entry in cfg["book"]["chapters"]:
        if isinstance(entry, dict):
            stems = [Path(e if isinstance(e, str) else e["file"]).stem for e in entry.get("chapters", [])]
            groups.append(stems)
            flat += stems
        else:
            flat.append(Path(entry).stem)
    expected = [tree.first] + [c.stem for c in tree.chapters] + [tree.last]
    found = []
    if [s for s in flat if s != "index"] != expected:
        found.append(f"quarto: chapters are {[s for s in flat if s != 'index']}, the tree says {expected}")
    by_part: dict[str, list[str]] = {}
    for c in tree.chapters:
        by_part.setdefault(c.part, []).append(c.stem)
    if groups != list(by_part.values()):
        found.append(f"quarto: Parts group {groups}, the tree says {list(by_part.values())}")
    titles = [_part_title(e["part"], root) for e in cfg["book"]["chapters"] if isinstance(e, dict)]
    if titles != [t for _, t in tree.parts]:
        found.append(f"quarto: Part titles are {titles}, the tree says {[t for _, t in tree.parts]}")
    return found


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    for flag in ("files", "zoo", "quarto", "all"):
        ap.add_argument(f"--{flag}", action="store_true")
    ap.add_argument("--root", type=Path, default=REPO_ROOT)
    ap.add_argument("--tree", type=Path, default=None)
    a = ap.parse_args(argv)
    tree = parse_tree((a.tree or a.root / "notes" / "question_tree.md").read_text(encoding="utf-8"))
    found = check_tree(tree)
    if a.files or a.all:
        for c in tree.chapters:
            found += check_chapter(c, a.root)
        for stem in (tree.first, tree.last):
            if _chapter_text(stem, a.root) is None:
                found.append(f"{stem}: chapters/{stem}.qmd does not exist")
    if a.zoo or a.all:
        found += check_zoo(tree, a.root)
    if a.quarto or a.all:
        found += check_quarto(tree, a.root)
    for f in found:
        print(f"[FINDING] {f}")
    print(f"question tree: {len(found)} finding(s)" if found else "question tree: no findings")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
