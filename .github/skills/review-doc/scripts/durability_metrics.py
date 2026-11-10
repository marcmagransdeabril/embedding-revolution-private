#!/usr/bin/env python3
"""Mechanical support for review-doc §17 (inquiry integrity) and §18 (durability).

Subcommands
  lint      check inquiry/ledger.yml (readings, idea tree, decision gates) against its rules and references.bib
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
# Idea tree: how much the author stands behind a node's EXISTENCE, and how far its content got.
KINDS_NODE = ("book", "part", "chapter", "section", "idea")
COMMITMENT = ("settled", "provisional", "exploratory", "parked", "dropped")
CONTENT = ("none", "stub", "outline", "draft", "written")
GATE_STATUS = ("pending", "decided", "deferred", "recurring")

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

        if e.get("open_set"):
            if not e.get("members"):
                out.append(("warn", eid, "open_set question with no members listed"))
            if not e.get("last_search"):
                out.append(("warn", eid, "open_set question with no 'last_search' date for new members"))
            elif isinstance(e["last_search"], dt.date) and (today - e["last_search"]).days > STALE_DAYS:
                out.append(("warn", eid, f"no search for new members for {(today - e['last_search']).days} days"))
            if status in ("supported",):
                out.append(("error", eid, "an open set cannot be 'supported' as complete; keep it 'leaning' or 'open'"))
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


def lint_tree(ledger: dict, root: Path) -> list[tuple[str, str, str]]:
    """Lint the idea tree and its decision gates. Severities: error, warn, info (a decision is due)."""
    out: list[tuple[str, str, str]] = []
    nodes = {str(n.get("id")): n for n in ledger.get("tree") or []}
    gates = {str(g.get("id")): g for g in ledger.get("gates") or []}
    questions = {str(q.get("id")): q for q in ledger.get("questions") or []}

    for nid, n in nodes.items():
        if n.get("kind") not in KINDS_NODE:
            out.append(("error", nid, f"kind must be one of {KINDS_NODE}"))
        if n.get("commitment") not in COMMITMENT:
            out.append(("error", nid, f"commitment must be one of {COMMITMENT}"))
        if n.get("content", "none") not in CONTENT:
            out.append(("error", nid, f"content must be one of {CONTENT}"))
        parent = n.get("parent")
        if parent is not None and str(parent) not in nodes:
            out.append(("error", nid, f"parent '{parent}' does not exist"))
        seen, cur = {nid}, parent
        while cur is not None and str(cur) in nodes:
            if str(cur) in seen:
                out.append(("error", nid, "cycle in parent chain"))
                break
            seen.add(str(cur))
            cur = nodes[str(cur)].get("parent")
        if n.get("commitment") == "dropped" and not n.get("why"):
            out.append(("error", nid, "dropped without 'why' (record what was learned, so it is not explored twice)"))
        if n.get("commitment") == "parked" and not n.get("reopen_if"):
            out.append(("warn", nid, "parked without 'reopen_if'"))
        g = n.get("gate")
        if g is not None and str(g) not in gates:
            out.append(("error", nid, f"gate '{g}' does not exist"))
        if n.get("commitment") in ("exploratory", "parked") and g is None and n.get("kind") != "idea":
            out.append(("warn", nid, f"{n['commitment']} node with no gate: nothing says when it will be decided"))
        if g is not None and str(g) in gates and gates[str(g)].get("status") == "decided" and n.get("commitment") == "exploratory":
            out.append(("warn", nid, f"gate '{g}' is decided but the node is still exploratory"))
        if n.get("file") and not (root / n["file"]).exists():
            out.append(("error", nid, f"file '{n['file']}' does not exist"))
        if n.get("question") and str(n["question"]) not in questions:
            out.append(("error", nid, f"question '{n['question']}' does not exist"))
        if parent is not None and str(parent) in nodes and nodes[str(parent)].get("commitment") == "dropped" \
                and n.get("commitment") != "dropped":
            out.append(("warn", nid, "parent is dropped but this node is not"))

    for qid, q in questions.items():
        for m in q.get("members") or []:
            if str(m) not in nodes:
                out.append(("error", qid, f"member '{m}' is not a node in the tree"))

    chapter_files = {str(p.relative_to(root)) for p in (root / "chapters").glob("*.qmd") if p.name != "solutions.qmd"}
    for f in sorted(chapter_files - {n.get("file") for n in nodes.values()}):
        out.append(("warn", f, "chapter file has no node in the tree (structure changed without a tree entry)"))

    for gid, g in gates.items():
        opts = {str(o.get("id")) for o in g.get("options") or []}
        if g.get("status") not in GATE_STATUS:
            out.append(("error", gid, f"status must be one of {GATE_STATUS}"))
        if len(opts) < 2:
            out.append(("error", gid, "a gate needs at least two options"))
        for ref in g.get("decides") or []:
            if str(ref) not in nodes and str(ref) not in questions:
                out.append(("error", gid, f"decides '{ref}' which is neither a node nor a question"))
        needed = [str(q) for q in g.get("evidence_needed") or []]
        for q in needed:
            if q not in questions:
                out.append(("error", gid, f"evidence_needed '{q}' does not exist"))
        if g.get("status") == "recurring":
            seen = g.get("last_reviewed")
            if not seen:
                out.append(("warn", gid, "recurring gate with no 'last_reviewed' date"))
            elif isinstance(seen, dt.date) and (dt.date.today() - seen).days > STALE_DAYS:
                out.append(("warn", gid, f"recurring gate not reviewed for {(dt.date.today() - seen).days} days"))
        if g.get("status") == "decided":
            if str(g.get("decision")) not in opts:
                out.append(("error", gid, "decided but 'decision' is not one of the options"))
            if not g.get("decided_on") or not g.get("because"):
                out.append(("error", gid, "decided without 'decided_on' and 'because'"))
        elif g.get("status") != "recurring" and needed and all(q in questions and questions[q].get("status") != "open" for q in needed):
            out.append(("info", gid, "decision due: every question it waits for now has a reading"))
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
        "tree": {
            "by_commitment": {c: sum(n.get("commitment") == c for n in ledger.get("tree") or []) for c in COMMITMENT},
            "gates": {g: sum(x.get("status") == g for x in ledger.get("gates") or []) for g in GATE_STATUS},
            "decisions_due": 0,
        },
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
        issues += lint_tree(load_ledger(ledger_path), root)
        metrics["tree"]["decisions_due"] = sum(s == "info" for s, _, _ in issues)
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
    if old.get("tree") != new.get("tree"):
        lines.append(f"tree: {old.get('tree')} -> {new.get('tree')}")
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
        ledger = load_ledger()
        issues = lint_ledger(ledger, set(parse_bibliography(REPO_ROOT / "references.bib")), REPO_ROOT, dt.date.today())
        issues += lint_tree(ledger, REPO_ROOT)
        for sev, eid, msg in issues:
            print(f"{sev.upper():5} {eid}: {msg}")
        print(f"{sum(s == 'error' for s, _, _ in issues)} error(s), {sum(s == 'warn' for s, _, _ in issues)} warning(s), "
              f"{sum(s == 'info' for s, _, _ in issues)} decision(s) due")
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
