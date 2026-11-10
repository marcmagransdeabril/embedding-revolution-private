#!/usr/bin/env python3
"""Mechanical support for review-doc: status of the book's parts and durability proxies.

Subcommands
  status    table of chapter statuses (definitive | provisional | idea), open questions, consistency problems
  metrics   durability proxies (source age, perishable terms, time-relative wording, titles) as JSON
  snapshot  write the current metrics to notes/durability.json
  diff      compare the current metrics with that snapshot

Status annotations live in the text itself:
  chapters   front matter `status:` (or a class on the H1 for files without front matter) and optional `open:`
  sections   a heading class, `## Title {.provisional}` or `{.idea}`; no class means the chapter's status
  roadmap    a tag `*(status)*` after each chapter title in index.qmd; `<!-- OPEN: ... -->` comments
The script measures; it never judges. Every number is a hint for the reviewer to read the passage.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import statistics
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / ".github" / "skills" / "build-book" / "scripts"))
from validate_book import extract_citekeys, parse_bibliography  # noqa: E402

SNAPSHOT = REPO_ROOT / "notes" / "durability.json"
STATUSES = ("definitive", "provisional", "idea")

# Perishable terms: how many files one change in the field would force us to edit.
PERISHABLE = {
    "LLM/GPT/BERT": r"\b(LLMs?|GPT\S*|BERT)\b",
    "JEPA/world model": r"\b(JEPA|world models?|LeCun)\b",
    "Platonic/convergence": r"\b(Platonic|convergence)\b",
    "Transformer": r"\bTransformers?\b",
    "linear representation/steering": r"\b(linear representation|steering)\b",
    "chain of thought": r"\b(chain[- ]of[- ]thought|CoT)\b",
    "latent reasoning": r"\b(Coconut|latent reasoning|pause tokens?|recurrent depth)\b",
    "BYOL/VICReg/data2vec": r"\b(BYOL|VICReg|data2vec)\b",
    "CLIP/ImageBind": r"\b(CLIP|ImageBind)\b",
    "agents": r"\b(agentic|agents?)\b",
    "ANN products": r"\b(ColBERT|HNSW|IVFFlat|product quantization)\b",
    "RAG": r"\b(RAG|retrieval-augmented)\b",
    "RoPE": r"\bRoPE\b",
    "sparse autoencoders": r"\b(sparse autoencoders?|SAEs?)\b",
}
RELATIVE_TIME = re.compile(
    r"\b(recently|currently|nowadays|these days|state[- ]of[- ]the[- ]art|latest|cutting[- ]edge|"
    r"at present|up[- ]to[- ]date|last (?:few )?(?:years|decades)|modern)\b",
    re.IGNORECASE,
)
FASHION = re.compile(
    r"\b(RAG|Retrieval-Augmented|Transformers?|Quantum|Topological Deep Learning|Agentic|LLMs?|GPT|"
    r"Neural Theorem Proving|Databases)\b"
)
TITLE_LINE = re.compile(r"^(?:#{1,3} .*|title: .*|\* \*\*Chapter \d+:.*)$")

_FRONT = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)
_HEADING = re.compile(r"^(#{1,6}) (.*?)(?:\s*\{([^}]*)\})?\s*$")
_OPEN_COMMENT = re.compile(r"<!--\s*OPEN:(.*?)-->", re.DOTALL)
_INDEX_TAG = re.compile(r"^\* \*\*(Chapter \d+|Epilogue): .*?\.\*\*\s*\*\((\w+)\)\*", re.MULTILINE)


# --------------------------------------------------------------------- status

def front_matter(text: str) -> dict:
    m = _FRONT.match(text)
    if not m:
        return {}
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return {}
    return fm if isinstance(fm, dict) else {}


def _classes(attrs: str | None) -> list[str]:
    return re.findall(r"\.([\w-]+)", attrs or "")


def chapter_status(text: str) -> str | None:
    """`status:` in the front matter, else a status class on the first H1, else None."""
    st = front_matter(text).get("status")
    if st:
        return str(st)
    for line in text.splitlines():
        m = _HEADING.match(line)
        if m and len(m.group(1)) == 1:
            found = [c for c in _classes(m.group(3)) if c in STATUSES]
            return found[0] if found else None
    return None


def sections(text: str) -> list[dict]:
    """Headings with their own status class (if any) and the line range they cover."""
    lines = text.splitlines()
    heads = []
    in_code = False
    for i, line in enumerate(lines):
        if line.startswith("```"):
            in_code = not in_code
        m = None if in_code else _HEADING.match(line)
        if m:
            cls = [c for c in _classes(m.group(3)) if c in STATUSES]
            heads.append({"line": i + 1, "level": len(m.group(1)), "title": m.group(2).strip(), "status": cls[0] if cls else None})
    for k, h in enumerate(heads):
        end = len(lines)
        for nxt in heads[k + 1:]:
            if nxt["level"] <= h["level"]:
                end = nxt["line"] - 1
                break
        h["end"] = end
    return heads


def open_notes(text: str) -> list[str]:
    notes = [" ".join(m.strip().split()) for m in _OPEN_COMMENT.findall(text)]
    fm_open = front_matter(text).get("open")
    return ([str(fm_open)] if fm_open else []) + notes


def definitive_text(text: str) -> str:
    """The text without the sections tagged provisional or idea; front matter dropped."""
    lines = _FRONT.sub("", text, count=1).splitlines() if _FRONT.match(text) else text.splitlines()
    offset = len(text.splitlines()) - len(lines)
    drop: set[int] = set()
    for h in sections(text):
        if h["status"] in ("provisional", "idea"):
            drop.update(range(h["line"] - offset - 1, h["end"] - offset))
    return "\n".join(l for i, l in enumerate(lines) if i not in drop)


def book_order(root: Path) -> list[str]:
    """Chapter files in book order, from _quarto.yml (index and solutions excluded)."""
    cfg = yaml.safe_load((root / "_quarto.yml").read_text(encoding="utf-8")) or {}
    out: list[str] = []

    def walk(items):
        for it in items:
            if isinstance(it, str):
                out.append(it)
            elif isinstance(it, dict):
                walk(it.get("chapters") or [])

    walk(cfg.get("book", {}).get("chapters") or [])
    return [f for f in out if f not in ("index.qmd", "chapters/solutions.qmd")]


def index_tags(index_text: str) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in _INDEX_TAG.finditer(index_text)}


def status_report(root: Path = REPO_ROOT) -> tuple[list[dict], list[tuple[str, str, str]]]:
    """Rows (one per chapter) and (severity, where, message) problems."""
    rows, problems = [], []
    order = book_order(root)
    tags = index_tags((root / "index.qmd").read_text(encoding="utf-8"))
    numbered = [f for f in order if not f.endswith("epilogue.qmd")]
    expected_keys = {f: (f"Chapter {i}" if i else None) for i, f in enumerate(numbered, 1)}
    for f in order:
        text = (root / f).read_text(encoding="utf-8")
        st = chapter_status(text)
        secs = sections(text)
        key = "Epilogue" if f.endswith("epilogue.qmd") else expected_keys.get(f)
        rows.append({
            "file": f, "status": st,
            "provisional_sections": sum(h["status"] == "provisional" and h["level"] > 1 for h in secs),
            "idea_sections": sum(h["status"] == "idea" and h["level"] > 1 for h in secs),
            "open": len(open_notes(text)), "index_tag": tags.get(key),
        })
        if st is None:
            problems.append(("warn", f, "no status (front matter `status:` or a class on the H1)"))
        elif st not in STATUSES:
            problems.append(("error", f, f"status '{st}' is not one of {STATUSES}"))
        if tags.get(key) is None:
            problems.append(("warn", f, f"no status tag for '{key}' in the roadmap of index.qmd"))
        elif st and tags[key] != st:
            problems.append(("error", f, f"roadmap tag '{tags[key]}' differs from the chapter status '{st}'"))
        for h in secs:
            if h["status"] and h["status"] == st and h["level"] > 1:
                problems.append(("warn", f"{f}:{h['line']}", f"section tag '{h['status']}' repeats the chapter status"))
    return rows, problems


# -------------------------------------------------------------------- metrics

def _year(fields: dict[str, str]) -> int | None:
    m = re.search(r"\d{4}", fields.get("year", ""))
    return int(m.group()) if m else None


def file_metrics(text: str, bib: dict[str, dict[str, str]]) -> dict:
    keys = {k for k, _ in extract_citekeys(text)} & set(bib)
    years = sorted(y for y in (_year(bib[k]) for k in keys) if y)
    return {
        "cites": len(years),
        "median_year": int(statistics.median(years)) if years else None,
        "before_1980": sum(y < 1980 for y in years),
        "from_2020": sum(y >= 2020 for y in years),
        "from_2023": sum(y >= 2023 for y in years),
    }


def perishable_counts(texts: dict[str, str]) -> dict[str, dict]:
    result = {}
    for name, pattern in PERISHABLE.items():
        rx = re.compile(pattern)
        per_file = {f: len(rx.findall(t)) for f, t in texts.items()}
        per_file = {f: n for f, n in per_file.items() if n}
        result[name] = {"occurrences": sum(per_file.values()), "files": len(per_file)}
    return result


def relative_wording(texts: dict[str, str]) -> list[str]:
    return [f"{f}:{i}" for f, t in texts.items() for i, line in enumerate(t.splitlines(), 1) if RELATIVE_TIME.search(line)]


def fashion_titles(texts: dict[str, str]) -> list[str]:
    return [f"{f}:{i}: {line.strip()[:90]}" for f, t in texts.items()
            for i, line in enumerate(t.splitlines(), 1) if TITLE_LINE.match(line) and FASHION.search(line)]


def collect(root: Path = REPO_ROOT) -> dict:
    bib = parse_bibliography(root / "references.bib")
    paths = [root / "index.qmd"] + sorted(p for p in (root / "chapters").glob("*.qmd") if p.name != "solutions.qmd")
    texts = {str(p.relative_to(root)): p.read_text(encoding="utf-8") for p in paths if p.exists()}
    files = {f: file_metrics(t, bib) for f, t in texts.items()}
    # Settled part of a definitive chapter that also holds provisional sections, reported separately.
    for f, t in texts.items():
        if chapter_status(t) == "definitive" and any(h["status"] for h in sections(t)):
            files[f"{f} (definitive part)"] = file_metrics(definitive_text(t), bib)
    rows, problems = status_report(root)
    return {
        "date": dt.date.today().isoformat(),
        "bib_entries": len(bib),
        "files": files,
        "perishable": perishable_counts(texts),
        "relative_wording": relative_wording(texts),
        "fashion_titles": fashion_titles(texts),
        "status": {
            "chapters": {s: sum(r["status"] == s for r in rows) for s in STATUSES},
            "provisional_sections": sum(r["provisional_sections"] for r in rows),
            "idea_sections": sum(r["idea_sections"] for r in rows),
            "open_questions": sum(r["open"] for r in rows) + len(open_notes(texts["index.qmd"])),
            "problems": len(problems),
        },
    }


def diff_metrics(old: dict, new: dict) -> list[str]:
    """Human-readable changes between two metric dicts; empty when nothing moved."""
    lines: list[str] = []
    for f, n in new["files"].items():
        o = old["files"].get(f)
        if o is None:
            lines.append(f"new file {f}: {n['cites']} cites, median {n['median_year']}")
        elif (o["median_year"], o["from_2023"], o["cites"]) != (n["median_year"], n["from_2023"], n["cites"]):
            lines.append(f"{f}: median year {o['median_year']} -> {n['median_year']}, "
                         f"2023+ {o['from_2023']} -> {n['from_2023']}, cites {o['cites']} -> {n['cites']}")
    for name, n in new["perishable"].items():
        o = old["perishable"].get(name, {"occurrences": 0, "files": 0})
        if (o["occurrences"], o["files"]) != (n["occurrences"], n["files"]):
            lines.append(f"perishable '{name}': {o['occurrences']} in {o['files']} files -> {n['occurrences']} in {n['files']}")
    for key in ("relative_wording", "fashion_titles"):
        gone, added = set(old[key]) - set(new[key]), set(new[key]) - set(old[key])
        if added or gone:
            lines.append(f"{key}: +{len(added)} new, -{len(gone)} resolved")
    if old.get("status") != new.get("status"):
        lines.append(f"status: {old.get('status')} -> {new.get('status')}")
    return lines


# ------------------------------------------------------------------------ CLI

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["status", "metrics", "snapshot", "diff"])
    args = ap.parse_args(argv)

    if args.command == "status":
        rows, problems = status_report()
        for r in rows:
            extra = []
            if r["provisional_sections"]:
                extra.append(f"{r['provisional_sections']} provisional section(s)")
            if r["idea_sections"]:
                extra.append(f"{r['idea_sections']} idea section(s)")
            if r["open"]:
                extra.append(f"{r['open']} open question(s)")
            print(f"{(r['status'] or '?'):12} {r['file']}" + (f"  [{', '.join(extra)}]" if extra else ""))
        n_index = len(open_notes((REPO_ROOT / "index.qmd").read_text(encoding="utf-8")))
        print(f"{'':12} index.qmd  [{n_index} open question(s)]")
        for sev, where, msg in problems:
            print(f"{sev.upper():5} {where}: {msg}")
        return 1 if any(s == "error" for s, _, _ in problems) else 0

    metrics = collect()
    if args.command == "metrics":
        print(json.dumps(metrics, indent=2, ensure_ascii=False))
    elif args.command == "snapshot":
        SNAPSHOT.parent.mkdir(exist_ok=True)
        SNAPSHOT.write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {SNAPSHOT.relative_to(REPO_ROOT)}")
    else:
        if not SNAPSHOT.exists():
            print("No snapshot yet; run `snapshot` first.")
            return 0
        old = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        changes = diff_metrics(old, metrics)
        print(f"Since snapshot of {old['date']}:" if changes else f"No change since snapshot of {old['date']}.")
        print("\n".join(f"  {c}" for c in changes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
