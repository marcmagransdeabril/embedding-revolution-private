#!/usr/bin/env python3
"""Sync Quarto book chapter registry (_quarto.yml) with chapters/ directory.

Discovers existing .qmd files in chapters/, puts them in the order of the
roadmap (a flat list: there are no Parts for the time being, and the appendices
and the generated solutions close the book), and updates _quarto.yml.
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

# Canonical order of the book (the roadmap of index.qmd): the introduction, the summary of the properties, one chapter per property of
# meaning, the epilogue. There are no Parts for the time being. A chapter is named by its file stem; the identifier of a chapter is
# `sec-ch-` plus the stem with hyphens, which is the key that the status tooling reads from the roadmap.
ORDER = [
    "symbols_without_interior",
    "tests_of_meaning",
    "properties_of_meaning",
    "meaning_as_likeness",
    "meaning_as_difference",
    "meaning_as_direction",
    "meaning_as_region",
    "meaning_as_path",
    "meaning_as_composition",
    "meaning_across_scales",
    "meaning_across_senses",
    "meaning_as_arrangement",
    "meaning_in_context",
    "meaning_and_truth",
    "meaning_as_generation",
    "epilogue",
]
# Appendices follow the chapters; the solutions are generated and always come last.
APPENDICES = ["curse_of_dimensionality", "zoo_of_models"]


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
    """Scan chapters/ and return the flat list of chapters in the order of the roadmap, and the list of appendices."""
    stems = {p.stem: p for p in CHAPTERS_DIR.glob("*.qmd") if p != SOLUTIONS_QMD}
    chapters: list[Any] = ["index.qmd"]
    chapters += [f"chapters/{stems[s].name}" for s in ORDER if s in stems]
    # A chapter that is not in the roadmap is listed after the others, so that it is not lost
    chapters += [f"chapters/{p.name}" for s, p in sorted(stems.items()) if s not in ORDER and s not in APPENDICES]
    appendices = [f"chapters/{stems[s].name}" for s in APPENDICES if s in stems]
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
