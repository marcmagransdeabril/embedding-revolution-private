#!/usr/bin/env python3
"""Sync Quarto book chapter registry (_quarto.yml) with chapters/ directory.

Discovers existing .qmd files in chapters/, maps them to the canonical
book outline (Parts I to IV + Epilogue), and updates _quarto.yml.
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

# Canonical master outline from book architecture
MASTER_PARTS = [
    {
        "part": "The Flat Vector Paradigm and Its Limits",
        "chapters": [
            {
                "num": 1,
                "title": "The Anatomy of Embedding and Latent Spaces",
                "patterns": ["embedding_spaces", "01_", "anatomy", "chapter1", "latent_spaces"],
            },
            {
                "num": 2,
                "title": "Vector Databases, RAG, and the Limits of Flat Latent Retrieval",
                "patterns": ["vector_database", "vector_db", "rag", "02_", "retrieval", "chapter2"],
            },
            {
                "num": 3,
                "title": "The Curse (and Blessing) of Dimensionality",
                "patterns": ["curse_of_dimensionality", "dimensionality", "03_", "high_dim", "chapter3"],
            },
        ],
    },
    {
        "part": "Curved Manifolds, Graphs, and Topologies",
        "chapters": [
            {
                "num": 4,
                "title": "Tangent Spaces, Geodesics, and Geometric Deep Learning",
                "patterns": ["tangent_space", "geodesic", "geometric_deep_learning", "04_", "hyperbolic", "chapter4"],
            },
            {
                "num": 5,
                "title": "From Manifolds to Knowledge Graphs: Graph Embeddings and Relational Geometry",
                "patterns": ["graph_embedding", "knowledge_graph", "05_", "relational_geometry", "chapter5"],
            },
            {
                "num": 6,
                "title": "Beyond Graphs: Topological Deep Learning",
                "patterns": ["topological_deep_learning", "topological", "06_", "simplicial", "homology", "chapter6"],
            },
        ],
    },
    {
        "part": "The Algebra of Thought: Vectors as Symbols",
        "chapters": [
            {
                "num": 7,
                "title": "The Complex Plane and Quantum Logic: Wave-Nature in Latent Space",
                "patterns": ["complex_plane", "quantum_logic", "07_", "cvnn", "complex_valued", "chapter7"],
            },
            {
                "num": 8,
                "title": "Vector Symbolic Architectures and Hyperdimensional Computing",
                "patterns": ["vector_symbolic", "vsa", "hyperdimensional", "08_", "hdc", "chapter8"],
            },
            {
                "num": 9,
                "title": "Neuro-Symbolic Integration and Emergent Compositionality",
                "patterns": ["neuro_symbolic", "neurosymbolic", "09_", "tpr", "ltn", "chapter9"],
            },
        ],
    },
    {
        "part": "Alignment, Transport, and Synthesis",
        "chapters": [
            {
                "num": 10,
                "title": "Cross-Domain Transfer and Optimal Transport",
                "patterns": ["cross_domain", "optimal_transport", "10_", "wasserstein", "chapter10"],
            },
        ],
    },
]

EPILOGUE_ENTRY = {
    "title": "Epilogue: An Algebra of Thought",
    "patterns": ["epilogue", "algebra_of_thought"],
}


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
            return line[2:].strip()

    return qmd_path.stem.replace("_", " ").title()


def match_chapter_to_outline(qmd_file: Path) -> tuple[int, int] | None:
    """Match a .qmd file to (part_idx, chapter_idx) or None."""
    stem = qmd_file.stem.lower()
    title = extract_title_from_qmd(qmd_file).lower()

    for part_idx, part_info in enumerate(MASTER_PARTS):
        for ch_idx, ch_info in enumerate(part_info["chapters"]):
            for pat in ch_info["patterns"]:
                if pat in stem or pat in title:
                    return (part_idx, ch_idx)

    # Check epilogue
    for pat in EPILOGUE_ENTRY["patterns"]:
        if pat in stem or pat in title:
            return (len(MASTER_PARTS), 0)

    return None


def discover_and_build_chapters_list() -> list[Any]:
    """Scan chapters/ directory and construct Quarto chapters structure."""
    discovered_qmds = sorted(p for p in CHAPTERS_DIR.glob("*.qmd") if p != SOLUTIONS_QMD)
    
    # Chapters structure starting with index.qmd
    chapters_struct: list[Any] = ["index.qmd"]

    # Map discovered files to parts
    part_buckets: dict[int, list[tuple[int, Path]]] = {i: [] for i in range(len(MASTER_PARTS) + 1)}
    unmatched: list[Path] = []

    for qmd in discovered_qmds:
        matched = match_chapter_to_outline(qmd)
        if matched is not None:
            part_idx, ch_idx = matched
            part_buckets[part_idx].append((ch_idx, qmd))
        else:
            unmatched.append(qmd)

    # Assemble populated parts
    for part_idx, part_info in enumerate(MASTER_PARTS):
        entries = part_buckets[part_idx]
        if entries:
            # Sort by chapter index
            entries.sort(key=lambda x: x[0])
            part_chapters = [f"chapters/{path.name}" for _, path in entries]
            chapters_struct.append({
                "part": part_info["part"],
                "chapters": part_chapters,
            })

    # Add epilogue if present
    epilogue_entries = part_buckets[len(MASTER_PARTS)]
    for _, path in epilogue_entries:
        chapters_struct.append(f"chapters/{path.name}")

    # Add any unmatched chapters
    if unmatched:
        unmatched_paths = [f"chapters/{p.name}" for p in sorted(unmatched)]
        chapters_struct.append({
            "part": "Additional Chapters",
            "chapters": unmatched_paths,
        })

    # Solutions to the review questions always close the book
    if SOLUTIONS_QMD.is_file():
        chapters_struct.append(f"chapters/{SOLUTIONS_QMD.name}")

    return chapters_struct


def sync_quarto_yml(dry_run: bool = False, verbose: bool = False) -> bool:
    """Synchronize _quarto.yml with discovered chapters."""
    if not QUARTO_YML.is_file():
        print(f"Error: {QUARTO_YML} not found", file=sys.stderr)
        return False

    with open(QUARTO_YML, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    new_chapters = discover_and_build_chapters_list()
    old_chapters = config.get("book", {}).get("chapters", [])

    if verbose:
        print("Discovered chapters structure:")
        print(yaml.dump({"chapters": new_chapters}, sort_keys=False))

    if "book" not in config:
        config["book"] = {}

    config["book"]["chapters"] = new_chapters

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
