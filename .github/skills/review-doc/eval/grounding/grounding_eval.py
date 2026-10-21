#!/usr/bin/env python3
"""End-to-end eval: does a review-doc run actually use ground-truth-review, and correctly?

Pipeline
--------
1. build:  seed draft passages with gold claims (true / false / unanswerable) taken from
           ground-truth-review/eval/gold_claims.jsonl, written under tmp/ with neutral names
           so the agent cannot infer it is being evaluated from the path.
2. run:    launch `kiro-cli chat --no-interactive --output-format stream-json` once per
           (draft, arm) and save the raw JSONL transcript.
             arm "skill": the user triggers review-doc ("review X using the review-doc skill").
             arm "plain": same request without naming the skill (control).
3. grade:  parse transcripts and score
             - process: was ground_check.py invoked? did retrieval surface the gold doc/page?
                        was the gold page rendered/inspected? was the gold file peeked at?
             - outcome: per-claim verdict vs. gold label, false-"Supported" rate,
                        blocker severity on bad claims, citation (doc, page±1) accuracy.

Only the grading half is unit-tested offline; `run` needs kiro-cli and credentials.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[4]
GOLD_CLAIMS = REPO_ROOT / ".github" / "skills" / "ground-truth-review" / "eval" / "gold_claims.jsonl"
WORK_DIR = REPO_ROOT / "tmp" / "grounding-eval"
DRAFTS_DIR = WORK_DIR / "drafts"
CASES_PATH = WORK_DIR / "cases.jsonl"
RUNS_DIR = WORK_DIR / "runs"

VERDICTS = ("Supported", "Contradicted", "Not found", "Unverifiable", "Not checked")
# Paths whose access during a run means the agent saw answer keys.
CONTAMINATION_MARKERS = ("gold_claims", "grounding-eval/cases", "eval/grounding", "build_dataset.py")

OUTPUT_CONTRACT = (
    "At the very end of your report, append one fenced ```json block containing an object "
    '{"factual_claims": [...]} with one entry per factual, mathematical, empirical or attribution '
    "assertion in the passage. Each entry has keys: "
    '"quote" (verbatim fragment of the sentence, >= 8 words), '
    '"verdict" (one of "Supported", "Contradicted", "Not found", "Unverifiable", "Not checked"), '
    '"severity" ("blocker", "should-fix", "suggestion" or "none"), '
    '"doc" (reference document stem you relied on, or null), '
    '"page" (1-based page number in that document, or null).'
)

PROMPTS = {
    "skill": (
        "Review the draft passage in {path} using the review-doc skill "
        "(.github/skills/review-doc/SKILL.md). Unit: section (the whole file). Range: full. "
        "It is a standalone excerpt not yet wired into the book, so skip §14 build/test and "
        "book-level checks (structure, index, translation). Do not modify any files. "
        + OUTPUT_CONTRACT
    ),
    "plain": (
        "Review the draft passage in {path} for correctness and quality. "
        "It is a standalone excerpt not yet wired into the book; do not run the book build. "
        "Do not modify any files. "
        + OUTPUT_CONTRACT
    ),
}


# --------------------------------------------------------------------------- build

def load_gold(path: Path = GOLD_CLAIMS) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def build_cases(
    gold: list[dict[str, Any]],
    n_drafts: int = 4,
    per_draft: tuple[int, int, int] = (2, 2, 1),
    seed: int = 7,
) -> list[dict[str, Any]]:
    """Assemble drafts of (true, false, unanswerable) claims, distinct source docs per draft.

    Distinct docs prevent a true claim and its corrupted twin from landing in the same
    passage, which would give the error away by internal contradiction.
    """
    rng = random.Random(seed)
    pools = {lbl: [g for g in gold if g["expected_label"] == lbl] for lbl in ("true", "false", "unanswerable")}
    for p in pools.values():
        rng.shuffle(p)
    used: set[str] = set()
    cases = []
    for i in range(n_drafts):
        docs_in_draft: set[str] = set()
        claims: list[dict[str, Any]] = []
        for lbl, k in zip(("true", "false", "unanswerable"), per_draft):
            for g in pools[lbl]:
                if len([c for c in claims if c["expected_label"] == lbl]) >= k:
                    break
                doc = (g.get("plausible_docs") or [None])[0]
                if g["id"] in used or (doc and doc in docs_in_draft):
                    continue
                used.add(g["id"])
                if doc:
                    docs_in_draft.add(doc)
                claims.append(g)
        rng.shuffle(claims)
        cases.append({
            "case_id": f"draft_{chr(ord('a') + i)}",
            "claims": [
                {k: c.get(k) for k in ("id", "set", "claim", "expected_label", "category",
                                       "obviousness", "plausible_docs", "target_pages")}
                for c in claims
            ],
        })
    return cases


def render_draft(case: dict[str, Any]) -> str:
    body = " ".join(c["claim"].strip() for c in case["claims"])
    return f"## Background\n\n{body}\n"


def write_cases(cases: list[dict[str, Any]]) -> None:
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    for case in cases:
        (DRAFTS_DIR / f"{case['case_id']}.qmd").write_text(render_draft(case), encoding="utf-8")
    with open(CASES_PATH, "w", encoding="utf-8") as f:
        for case in cases:
            f.write(json.dumps(case) + "\n")


# --------------------------------------------------------------------------- run

def build_prompt(arm: str, draft_path: Path | str) -> str:
    # Plain substitution: the output contract contains literal JSON braces,
    # so str.format() would treat them as placeholders.
    return PROMPTS[arm].replace("{path}", str(draft_path))


def run_one(case_id: str, arm: str, out_dir: Path, timeout: int, model: str | None) -> Path:
    draft_rel = (DRAFTS_DIR / f"{case_id}.qmd").relative_to(REPO_ROOT)
    prompt = build_prompt(arm, draft_rel)
    out = out_dir / f"{case_id}__{arm}.jsonl"
    # Write tools are deliberately NOT trusted: the review must not edit the draft.
    cmd = ["kiro-cli", "chat", "--no-interactive", "--output-format", "stream-json",
           "--trust-tools=read,shell,grep,glob,code"]
    if model:
        cmd += ["--model", model]
    cmd.append(prompt)
    t0 = time.time()
    with open(out, "w", encoding="utf-8") as fo, open(out.with_suffix(".stderr"), "w") as fe:
        try:
            subprocess.run(cmd, cwd=REPO_ROOT, stdout=fo, stderr=fe, timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            fe.write(f"\nTIMEOUT after {timeout}s\n")
    print(f"[{case_id}/{arm}] finished in {time.time() - t0:.0f}s -> {out}", flush=True)
    return out


# --------------------------------------------------------------------------- grade

@dataclass
class ToolCall:
    tool: str
    title: str
    input: dict[str, Any]
    output_text: str = ""

    @property
    def command(self) -> str:
        return str(self.input.get("command", ""))

    @property
    def blob(self) -> str:
        return f"{self.title} {json.dumps(self.input)}"


@dataclass
class Transcript:
    tool_calls: list[ToolCall]
    final_text: str
    status: str | None


def parse_transcript(lines: Iterable[str]) -> Transcript:
    calls: dict[str, ToolCall] = {}
    order: list[str] = []
    chunks: list[str] = []
    final_text: str | None = None
    status = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "runFinished":
            final_text = ev["data"].get("finalText")
            status = ev["data"].get("status")
            continue
        if ev.get("type") != "sessionUpdate":
            continue
        up = ev["data"].get("update", {})
        kind = up.get("sessionUpdate")
        if kind == "agent_message_chunk":
            c = up.get("content", {})
            if c.get("type") == "text":
                chunks.append(c.get("text", ""))
        elif kind in ("tool_call", "tool_call_update"):
            tid = up.get("toolCallId")
            if tid not in calls:
                calls[tid] = ToolCall(tool="", title="", input={})
                order.append(tid)
            tc = calls[tid]
            tool = up.get("_meta", {}).get("kiro", {}).get("toolName")
            tc.tool = tool or tc.tool
            tc.title = up.get("title") or tc.title
            if isinstance(up.get("rawInput"), dict):
                tc.input = up["rawInput"]
            raw_out = up.get("rawOutput")
            if raw_out is not None:
                tc.output_text = _flatten_output(raw_out)
            for c in up.get("content") or []:
                inner = c.get("content", {}) if isinstance(c, dict) else {}
                if inner.get("type") == "text" and not tc.output_text:
                    tc.output_text = inner.get("text", "")
    text = final_text if final_text else "".join(chunks)
    return Transcript([calls[t] for t in order], text, status)


def _flatten_output(raw: Any) -> str:
    if isinstance(raw, dict) and "items" in raw:
        parts = []
        for it in raw["items"]:
            if isinstance(it, dict) and "Json" in it:
                j = it["Json"]
                parts.append(j.get("stdout", "") if isinstance(j, dict) and "stdout" in j else json.dumps(j))
            elif isinstance(it, dict) and "Text" in it:
                parts.append(str(it["Text"]))
            else:
                parts.append(json.dumps(it))
        return "\n".join(parts)
    return raw if isinstance(raw, str) else json.dumps(raw)


GC_RE = re.compile(r"ground_check(\.py)?")
RENDER_RE = re.compile(r"--render-page\s+[\"']?([^\s\"']+)[\"']?\s+(\d+)")
API_RENDER_RE = re.compile(r"render_page_image\(\s*[\"']([^\"']+)[\"']\s*,\s*(\d+)")


def ground_check_calls(tr: Transcript) -> list[ToolCall]:
    return [tc for tc in tr.tool_calls if tc.tool == "shell" and GC_RE.search(tc.command)]


def retrieved_hits(tr: Transcript) -> list[tuple[str, int]]:
    """(doc, page) pairs surfaced by any ground_check search, from its JSON stdout."""
    hits = []
    for tc in ground_check_calls(tr):
        for m in re.finditer(r'"doc":\s*"([^"]+)",\s*"page_no":\s*(\d+)', tc.output_text):
            hits.append((m.group(1), int(m.group(2))))
    return hits


def inspected_pages(tr: Transcript) -> list[tuple[str, int]]:
    """Pages the agent rendered (CLI or API) or whose PNG/text it read."""
    pages = []
    for tc in tr.tool_calls:
        blob = tc.command if tc.tool == "shell" else tc.blob
        for rx in (RENDER_RE, API_RENDER_RE):
            for m in rx.finditer(blob):
                pages.append((Path(m.group(1)).stem if m.group(1).endswith(".pdf") else m.group(1), int(m.group(2))))
        for m in re.finditer(r"renders/([^\s\"']+)_p(\d+)\.png", blob):
            pages.append((m.group(1), int(m.group(2))))
        if tc.tool != "shell":
            continue
        docs = [m.group(1) for m in re.finditer(r"references/([^\"'\s]+?)\.pdf", blob)]
        docs += re.findall(r"doc\s*=\s*['\"]([^'\"]+)['\"]", blob)
        if not docs:
            continue
        # Direct page-text extraction via PyMuPDF (0-based index) ...
        if "pymupdf" in blob.lower() or "fitz" in blob:
            for pm in re.finditer(r"load_page\((\d+)\)|\b(?:doc|pdf|d)\[(\d+)\]", blob):
                n = int(pm.group(1) or pm.group(2))
                pages += [(d, n + 1) for d in docs]
        # ... or straight from the index's pages table (1-based page_no).
        for pm in re.finditer(r"page_no\s*(?:=|IN\s*\(|BETWEEN)\s*(\d+)", blob, flags=re.IGNORECASE):
            pages += [(d, int(pm.group(1))) for d in docs]
    return pages


def contaminated(tr: Transcript) -> bool:
    return any(any(mk in tc.blob for mk in CONTAMINATION_MARKERS) for tc in tr.tool_calls)


def _norm_ws(s: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", s.lower()))


def page_shingles(page_text: str, k: int = 8, step: int = 25) -> list[str]:
    """Normalised k-word windows sampled across a page; any one appearing verbatim in
    tool output means the agent actually pulled that page's text."""
    words = _norm_ws(page_text).split()
    return [" ".join(words[i:i + k]) for i in range(0, max(len(words) - k, 0) + 1, step)] if len(words) >= k else []


def evidence_blob(tr: Transcript) -> str:
    """Tool output excluding ground_check *search* results (whose snippets are only
    candidate pointers); renders and any direct page reads stay in."""
    parts = []
    for tc in tr.tool_calls:
        if tc.tool == "shell" and GC_RE.search(tc.command) and "--render-page" not in tc.command \
                and not re.search(r"pymupdf|fitz|get_text|select\s+text", tc.command, flags=re.IGNORECASE):
            continue
        parts.append(tc.output_text)
    return _norm_ws("\n".join(parts))


def page_seen(blob: str, page_texts: list[str]) -> bool:
    return any(sh and sh in blob for t in page_texts for sh in page_shingles(t))


def load_page_texts(db_path: Path, wanted: Iterable[tuple[str, int]]) -> dict[tuple[str, int], str]:
    import sqlite3
    out: dict[tuple[str, int], str] = {}
    if not db_path.is_file():
        return out
    con = sqlite3.connect(str(db_path))
    try:
        for doc, p in set(wanted):
            row = con.execute("SELECT text FROM pages WHERE doc=? AND page_no=?", (doc, p)).fetchone()
            if row:
                out[(doc, p)] = row[0]
    finally:
        con.close()
    return out


def gold_page_keys(case: dict[str, Any]) -> list[tuple[str, int]]:
    keys = []
    for c in case["claims"]:
        for d in c.get("plausible_docs") or []:
            for p in c.get("target_pages") or []:
                keys += [(d, p + o) for o in (-1, 0, 1)]
    return keys


def extract_ledger(text: str) -> list[dict[str, Any]]:
    """Last fenced json block with a factual_claims list."""
    for block in reversed(re.findall(r"```json\s*(.*?)```", text, flags=re.DOTALL)):
        try:
            obj = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and isinstance(obj.get("factual_claims"), list):
            return [e for e in obj["factual_claims"] if isinstance(e, dict)]
    return []


_STOP = set("the a an of and or to in on for by with as is are be that this from at it its their".split())


def _tokens(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in _STOP and len(w) > 1}


def match_entry(claim_text: str, ledger: list[dict[str, Any]], min_overlap: float = 0.5) -> dict[str, Any] | None:
    """Best ledger entry by fraction of the entry quote's tokens found in the gold claim."""
    ct = _tokens(claim_text)
    best, best_s = None, 0.0
    for e in ledger:
        qt = _tokens(str(e.get("quote", "")))
        if not qt:
            continue
        s = len(qt & ct) / len(qt)
        if s > best_s:
            best, best_s = e, s
    return best if best_s >= min_overlap else None


def norm_verdict(v: Any) -> str | None:
    v = str(v or "").strip().lower()
    for canon in VERDICTS:
        if v.startswith(canon.lower()):
            return canon
    if v.startswith("unsupported") or v.startswith("ungrounded"):
        return "Not found"
    return None


def _near(page: int | None, targets: list[int]) -> bool:
    return page is not None and any(abs(int(page) - t) <= 1 for t in targets)


def _doc_ok(doc: Any, plausible: list[str]) -> bool:
    if not doc:
        return False
    d = Path(str(doc)).stem if str(doc).endswith(".pdf") else str(doc)
    return d in plausible


@dataclass
class ClaimGrade:
    claim_id: str
    expected_label: str
    set: str
    retrieved_doc: bool
    retrieved_page: bool
    inspected_page: bool
    in_ledger: bool
    verdict: str | None
    verdict_correct: bool
    lenient_correct: bool          # unanswerable: any non-Supported verdict counts
    false_supported: bool
    blocker_on_bad: bool | None    # None for true claims
    citation_correct: bool | None  # None for unanswerable


@dataclass
class RunGrade:
    case_id: str
    arm: str
    status: str | None
    ground_check_invoked: bool
    n_ground_check_calls: int
    n_render_calls: int
    contaminated: bool
    ledger_found: bool
    claims: list[ClaimGrade] = field(default_factory=list)


EXPECTED = {"true": "Supported", "false": "Contradicted", "unanswerable": "Not found"}


def grade_run(case: dict[str, Any], arm: str, tr: Transcript,
              page_texts: dict[tuple[str, int], str] | None = None) -> RunGrade:
    gc = ground_check_calls(tr)
    hits = retrieved_hits(tr)
    inspected = inspected_pages(tr)
    blob = evidence_blob(tr) if page_texts else ""
    ledger = extract_ledger(tr.final_text)
    rg = RunGrade(
        case_id=case["case_id"], arm=arm, status=tr.status,
        ground_check_invoked=bool(gc), n_ground_check_calls=len(gc),
        n_render_calls=sum(1 for tc in gc if "--render-page" in tc.command),
        contaminated=contaminated(tr), ledger_found=bool(ledger),
    )
    for c in case["claims"]:
        docs = c.get("plausible_docs") or []
        pages = c.get("target_pages") or []
        lbl = c["expected_label"]
        e = match_entry(c["claim"], ledger)
        v = norm_verdict(e.get("verdict")) if e else None
        sev = str(e.get("severity", "")).lower() if e else ""
        if lbl == "unanswerable":
            correct = v in ("Not found", "Unverifiable")
            lenient = v is not None and v not in ("Supported", "Not checked")
        else:
            correct = v == EXPECTED[lbl]
            lenient = correct
        rg.claims.append(ClaimGrade(
            claim_id=c["id"], expected_label=lbl, set=c.get("set", ""),
            retrieved_doc=any(d in docs for d, _ in hits),
            retrieved_page=bool(pages) and any(d in docs and _near(p, pages) for d, p in hits),
            inspected_page=bool(pages) and (
                any(d in docs and _near(p, pages) for d, p in inspected)
                or page_seen(blob, [page_texts[(d, p + o)] for d in docs for p in pages for o in (-1, 0, 1)
                                    if page_texts and (d, p + o) in page_texts])),
            in_ledger=e is not None,
            verdict=v,
            verdict_correct=correct,
            lenient_correct=lenient,
            false_supported=(lbl != "true" and v == "Supported"),
            blocker_on_bad=None if lbl == "true" else sev.startswith("blocker"),
            citation_correct=None if lbl == "unanswerable" else (
                e is not None and _doc_ok(e.get("doc"), docs) and _near(_to_int(e.get("page")), pages)),
        ))
    return rg


def _to_int(x: Any) -> int | None:
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


def _rate(xs: list[bool]) -> float | None:
    return round(sum(xs) / len(xs), 3) if xs else None


def summarize(grades: list[RunGrade]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for arm in sorted({g.arm for g in grades}):
        runs = [g for g in grades if g.arm == arm]
        cl = [c for g in runs for c in g.claims]
        ans = [c for c in cl if c.expected_label != "unanswerable"]
        bad = [c for c in cl if c.expected_label != "true"]
        out[arm] = {
            "runs": len(runs),
            "runs_completed": sum(g.status == "success" for g in runs),
            "runs_invoking_ground_check": sum(g.ground_check_invoked for g in runs),
            "mean_ground_check_calls": round(sum(g.n_ground_check_calls for g in runs) / max(len(runs), 1), 1),
            "runs_contaminated": sum(g.contaminated for g in runs),
            "runs_with_ledger": sum(g.ledger_found for g in runs),
            "claims": len(cl),
            "claim_coverage_in_ledger": _rate([c.in_ledger for c in cl]),
            "retrieval_doc_hit": _rate([c.retrieved_doc for c in ans]),
            "retrieval_page_hit": _rate([c.retrieved_page for c in ans]),
            "gold_page_inspected": _rate([c.inspected_page for c in ans]),
            "verdict_accuracy_strict": _rate([c.verdict_correct for c in cl]),
            "verdict_accuracy_lenient": _rate([c.lenient_correct for c in cl]),
            "by_label": {
                lbl: {
                    "n": len(sub := [c for c in cl if c.expected_label == lbl]),
                    "strict": _rate([c.verdict_correct for c in sub]),
                    "lenient": _rate([c.lenient_correct for c in sub]),
                    "verdicts": {v: sum(c.verdict == v for c in sub) for v in (*VERDICTS, None)},
                } for lbl in ("true", "false", "unanswerable")
            },
            "false_supported_rate": _rate([c.false_supported for c in bad]),
            "blocker_on_bad_claims": _rate([bool(c.blocker_on_bad) for c in bad]),
            "citation_accuracy": _rate([bool(c.citation_correct) for c in ans]),
        }
    return out


def format_report(summary: dict[str, Any], grades: list[RunGrade]) -> str:
    arms = list(summary)
    rows = [
        ("Runs completed", "runs_completed"), ("Runs invoking ground_check.py", "runs_invoking_ground_check"),
        ("Mean ground_check calls / run", "mean_ground_check_calls"), ("Runs touching answer keys", "runs_contaminated"),
        ("Runs with parseable ledger", "runs_with_ledger"), ("Claim coverage in ledger", "claim_coverage_in_ledger"),
        ("Retrieval: gold doc surfaced", "retrieval_doc_hit"), ("Retrieval: gold page ±1 surfaced", "retrieval_page_hit"),
        ("Gold page ±1 inspected", "gold_page_inspected"), ("Verdict accuracy (strict)", "verdict_accuracy_strict"),
        ("Verdict accuracy (lenient)", "verdict_accuracy_lenient"), ("False 'Supported' on false/unanswerable", "false_supported_rate"),
        ("Blocker on false/unanswerable", "blocker_on_bad_claims"), ("Citation (doc, page±1) correct", "citation_accuracy"),
    ]
    lines = ["| Metric | " + " | ".join(arms) + " |", "|---|" + "---|" * len(arms)]
    for name, key in rows:
        lines.append(f"| {name} | " + " | ".join(str(summary[a][key]) for a in arms) + " |")
    lines += ["", "| Arm | Label | n | strict | lenient | verdicts |", "|---|---|---|---|---|---|"]
    for a in arms:
        for lbl, d in summary[a]["by_label"].items():
            vs = ", ".join(f"{k}={v}" for k, v in d["verdicts"].items() if v)
            lines.append(f"| {a} | {lbl} | {d['n']} | {d['strict']} | {d['lenient']} | {vs} |")
    lines += ["", "| Run | Claim | Label | Verdict | Retrieved page | Inspected page | Citation |", "|---|---|---|---|---|---|---|"]
    for g in grades:
        for c in g.claims:
            lines.append(f"| {g.case_id}/{g.arm} | {c.claim_id} | {c.expected_label} | {c.verdict} | "
                         f"{c.retrieved_page} | {c.inspected_page} | {c.citation_correct} |")
    return "\n".join(lines)


def grade_dir(run_dir: Path, cases_path: Path = CASES_PATH,
              db_path: Path = REPO_ROOT / "references" / ".ground-index" / "index.sqlite",
              ) -> tuple[dict[str, Any], list[RunGrade]]:
    cases = {c["case_id"]: c for c in (json.loads(l) for l in open(cases_path, encoding="utf-8") if l.strip())}
    page_texts = load_page_texts(db_path, [k for c in cases.values() for k in gold_page_keys(c)])
    grades = []
    for t in sorted(run_dir.glob("*__*.jsonl")):
        case_id, arm = t.stem.split("__")
        if case_id not in cases:
            continue
        with open(t, encoding="utf-8") as f:
            grades.append(grade_run(cases[case_id], arm, parse_transcript(f), page_texts))
    return summarize(grades), grades


# --------------------------------------------------------------------------- CLI

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="write seeded drafts + cases.jsonl under tmp/grounding-eval")
    b.add_argument("--drafts", type=int, default=4)
    b.add_argument("--seed", type=int, default=7)
    r = sub.add_parser("run", help="run kiro-cli on every (draft, arm) and grade")
    r.add_argument("--arms", nargs="+", default=["skill", "plain"], choices=list(PROMPTS))
    r.add_argument("--cases", nargs="*", default=None, help="subset of case ids")
    r.add_argument("--parallel", type=int, default=4)
    r.add_argument("--timeout", type=int, default=1200)
    r.add_argument("--model", default=None)
    g = sub.add_parser("grade", help="grade an existing run directory")
    g.add_argument("run_dir", type=Path)
    for p in (r, g):
        p.add_argument("--output-json", type=Path, default=None)
    args = ap.parse_args()

    if args.cmd == "build":
        cases = build_cases(load_gold(), n_drafts=args.drafts, seed=args.seed)
        write_cases(cases)
        print(f"Wrote {len(cases)} drafts to {DRAFTS_DIR} and {CASES_PATH}")
        return

    if args.cmd == "run":
        if not CASES_PATH.is_file():
            write_cases(build_cases(load_gold()))
        ids = [json.loads(l)["case_id"] for l in open(CASES_PATH) if l.strip()]
        ids = [i for i in ids if not args.cases or i in args.cases]
        run_dir = RUNS_DIR / time.strftime("%Y%m%dT%H%M%S")
        run_dir.mkdir(parents=True, exist_ok=True)
        jobs = [(i, a) for i in ids for a in args.arms]
        with ThreadPoolExecutor(max_workers=args.parallel) as ex:
            list(ex.map(lambda j: run_one(j[0], j[1], run_dir, args.timeout, args.model), jobs))
    else:
        run_dir = args.run_dir

    summary, grades = grade_dir(run_dir)
    print(format_report(summary, grades))
    out = args.output_json or (run_dir / "summary.json")
    out.write_text(json.dumps({"summary": summary, "runs": [asdict(g) for g in grades]}, indent=2), encoding="utf-8")
    print(f"\nSaved {out}")


if __name__ == "__main__":
    sys.exit(main())
