#!/usr/bin/env python3
"""Mechanical support for review-doc §17 (inquiry integrity) and §18 (durability).

Subcommands
  lint      check inquiry/ledger.yml against its own rules and references.bib
  metrics   print durability proxies (source age, perishable terms, time-relative wording, titles)
  snapshot  write the current metrics to inquiry/durability.json
  diff      compare the current metrics with that snapshot

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

LEDGER = REPO_ROOT / "inquiry" / "ledger.yml"
SNAPSHOT = REPO_ROOT / "inquiry" / "durability.json"

LEVELS = ("book", "chapter", "section")
STATUSES = ("open", "leaning", "supported", "contested", "revised", "dropped")
CONFIDENCE = ("none", "low", "medium", "high")
KINDS = ("theorem", "historical", "replicated", "own-experiment", "single-study", "position", "interpretive")
# Evidence kinds that can carry a reading on their own, by the highest confidence they allow.
SOLID = {"theorem", "historical", "replicated", "own-experiment"}
STALE_DAYS = 180

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


# ---------------------------------------------------------------- ledger lint

def load_ledger(path: Path = LEDGER) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def lint_ledger(ledger: dict, bib_keys: set[str], root: Path, today: dt.date) -> list[tuple[str, str, str]]:
    """Return (severity, entry id, message) triples. Severity is 'error' or 'warn'."""
    out: list[tuple[str, str, str]] = []
    entries = ledger.get("questions") or []
    by_id: dict[str, dict] = {}
    for e in entries:
        eid = str(e.get("id", "?"))
        if eid in by_id:
            out.append(("error", eid, "duplicate id"))
        by_id[eid] = e
    log_ids = {str(item.get("id")) for item in ledger.get("log") or []}

    for eid, e in by_id.items():
        status, conf, level = e.get("status"), e.get("confidence", "none"), e.get("level")
        if level not in LEVELS:
            out.append(("error", eid, f"level must be one of {LEVELS}"))
        if status not in STATUSES:
            out.append(("error", eid, f"status must be one of {STATUSES}"))
        if conf not in CONFIDENCE:
            out.append(("error", eid, f"confidence must be one of {CONFIDENCE}"))
        if not e.get("question"):
            out.append(("error", eid, "missing question"))

        ev = e.get("evidence") or {}
        pro, con = ev.get("for") or [], ev.get("against") or []
        for item in pro + con:
            kind, src = item.get("kind"), str(item.get("src", ""))
            if kind not in KINDS:
                out.append(("error", eid, f"evidence kind '{kind}' not in {KINDS}"))
            if src and not (src in bib_keys or (root / src).exists()):
                out.append(("error", eid, f"evidence src '{src}' is neither a citekey nor an existing path"))
            if not src:
                out.append(("error", eid, "evidence item without src"))

        for child in e.get("depends_on") or []:
            if str(child) not in by_id:
                out.append(("error", eid, f"depends_on '{child}' does not exist"))

        committed = status in ("leaning", "supported", "contested")
        if committed and not (pro or con):
            out.append(("error", eid, f"status '{status}' without any evidence"))
        if committed and not e.get("falsifier"):
            out.append(("error", eid, f"status '{status}' without a falsifier"))
        if committed and not e.get("reading"):
            out.append(("error", eid, f"status '{status}' without a reading"))
        if status in ("revised", "dropped") and eid not in log_ids:
            out.append(("error", eid, f"status '{status}' needs an entry in log"))

        # Confidence is capped by the kind of evidence (see SKILL.md §17).
        if conf in ("medium", "high"):
            solid = [i for i in pro if i.get("kind") in SOLID]
            if not solid:
                out.append(("error", eid, f"confidence '{conf}' needs at least one solid evidence kind {sorted(SOLID)}"))
            elif conf == "high" and len(solid) < 2 and not any(i.get("kind") == "theorem" for i in solid):
                out.append(("error", eid, "confidence 'high' needs a theorem or two solid sources"))
        if conf == "high" and con and not e.get("answered_against"):
            out.append(("error", eid, "confidence 'high' with evidence against and no 'answered_against' note"))

        # Roll-up: a reading is no more confident than the load-bearing readings under it.
        kids = [by_id[str(c)] for c in e.get("depends_on") or [] if str(c) in by_id]
        if kids and conf in CONFIDENCE:
            weakest = min(CONFIDENCE.index(k.get("confidence", "none")) for k in kids if k.get("confidence", "none") in CONFIDENCE)
            if CONFIDENCE.index(conf) > weakest:
                out.append(("warn", eid, f"confidence '{conf}' exceeds its weakest dependency ('{CONFIDENCE[weakest]}')"))

        if committed and not con and not e.get("searched_against"):
            out.append(("warn", eid, "one-sided: no evidence against and no date when counter-evidence was searched"))
        checked = e.get("checked")
        if status != "open":
            if not checked:
                out.append(("warn", eid, "no 'checked' date"))
            elif isinstance(checked, dt.date) and (today - checked).days > STALE_DAYS:
                out.append(("warn", eid, f"not checked for {(today - checked).days} days"))
    return out


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
    hits = []
    for f, t in texts.items():
        for i, line in enumerate(t.splitlines(), 1):
            if RELATIVE_TIME.search(line):
                hits.append(f"{f}:{i}")
    return hits


def fashion_titles(texts: dict[str, str]) -> list[str]:
    hits = []
    for f, t in texts.items():
        for i, line in enumerate(t.splitlines(), 1):
            if TITLE_LINE.match(line) and FASHION.search(line):
                hits.append(f"{f}:{i}: {line.strip()[:90]}")
    return hits


def collect(root: Path = REPO_ROOT) -> dict:
    bib = parse_bibliography(root / "references.bib")
    paths = [root / "index.qmd"] + sorted(p for p in (root / "chapters").glob("*.qmd") if p.name != "solutions.qmd")
    texts = {str(p.relative_to(root)): p.read_text(encoding="utf-8") for p in paths if p.exists()}
    ledger_path = root / "inquiry" / "ledger.yml"
    ledger = load_ledger(ledger_path) if ledger_path.exists() else {}
    entries = ledger.get("questions") or []
    files = {f: file_metrics(t, bib) for f, t in texts.items()}
    # Files that are partly scratchpad: ledger key `definitive: {file: "## First scratchpad heading"}`.
    for f, heading in (ledger.get("definitive") or {}).items():
        if f in texts and heading in texts[f]:
            files[f"{f} (definitive part)"] = file_metrics(texts[f].split(heading, 1)[0], bib)
    return {
        "date": dt.date.today().isoformat(),
        "bib_entries": len(bib),
        "files": files,
        "perishable": perishable_counts(texts),
        "relative_wording": relative_wording(texts),
        "fashion_titles": fashion_titles(texts),
        "ledger": {
            "entries": len(entries),
            "by_status": {s: sum(e.get("status") == s for e in entries) for s in STATUSES},
            "lint_errors": 0,
            "lint_warnings": 0,
        },
    }


def with_lint(metrics: dict, root: Path = REPO_ROOT) -> dict:
    ledger_path = root / "inquiry" / "ledger.yml"
    if ledger_path.exists():
        bib = set(parse_bibliography(root / "references.bib"))
        issues = lint_ledger(load_ledger(ledger_path), bib, root, dt.date.today())
        metrics["ledger"]["lint_errors"] = sum(s == "error" for s, _, _ in issues)
        metrics["ledger"]["lint_warnings"] = sum(s == "warn" for s, _, _ in issues)
    return metrics


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
    if old["ledger"] != new["ledger"]:
        lines.append(f"ledger: {old['ledger']} -> {new['ledger']}")
    return lines


# ------------------------------------------------------------------------ CLI

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["lint", "metrics", "snapshot", "diff"])
    args = ap.parse_args(argv)

    if args.command == "lint":
        if not LEDGER.exists():
            print(f"No ledger at {LEDGER.relative_to(REPO_ROOT)}; nothing to lint.")
            return 0
        issues = lint_ledger(load_ledger(), set(parse_bibliography(REPO_ROOT / "references.bib")), REPO_ROOT, dt.date.today())
        for sev, eid, msg in issues:
            print(f"{sev.upper():5} {eid}: {msg}")
        print(f"{sum(s == 'error' for s, _, _ in issues)} error(s), {sum(s == 'warn' for s, _, _ in issues)} warning(s)")
        return 1 if any(s == "error" for s, _, _ in issues) else 0

    metrics = with_lint(collect())
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
