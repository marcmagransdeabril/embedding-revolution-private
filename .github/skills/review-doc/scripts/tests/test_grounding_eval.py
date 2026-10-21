"""Offline tests for the review-doc → ground-truth-review end-to-end grader.

Transcripts are synthetic but mirror the kiro-cli `--output-format stream-json` shape
observed from a real run (sessionUpdate/tool_call/tool_call_update/runFinished).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

GROUNDING_DIR = Path(__file__).resolve().parents[2] / "eval" / "grounding"
if str(GROUNDING_DIR) not in sys.path:
    sys.path.insert(0, str(GROUNDING_DIR))

import grounding_eval as ge  # noqa: E402

CASE = {
    "case_id": "draft_x",
    "claims": [
        {"id": "t1", "set": "corpus", "expected_label": "true",
         "claim": "Smolensky (1990) proposes the tensor product as the variable binding mechanism for roles and fillers.",
         "plausible_docs": ["1990_tpr_seminal_paper"], "target_pages": [1]},
        {"id": "f1", "set": "math", "expected_label": "false",
         "claim": "In Ridge regression the penalty term is lambda times the L1 norm of the coefficient vector beta.",
         "plausible_docs": ["2013_elements_of_statistical_learning"], "target_pages": [70]},
        {"id": "u1", "set": "corpus", "expected_label": "unanswerable",
         "claim": "Gelman et al. benchmark R-hat convergence diagnostics on GPT-4 sampling traces in their 2013 edition.",
         "plausible_docs": ["2013_gelman_bayesian_data_analysis"], "target_pages": []},
    ],
}


def _tool(tid: str, command: str, stdout: str, tool: str = "shell") -> list[str]:
    start = {"type": "sessionUpdate", "data": {"update": {
        "sessionUpdate": "tool_call", "toolCallId": tid, "title": f"Running: {command}",
        "kind": "execute", "rawInput": {"command": command}, "_meta": {"kiro": {"toolName": tool}}}}}
    done = {"type": "sessionUpdate", "data": {"update": {
        "sessionUpdate": "tool_call_update", "toolCallId": tid, "status": "completed",
        "rawInput": {"command": command},
        "rawOutput": {"items": [{"Json": {"exit_status": "exit status: 0", "stdout": stdout, "stderr": ""}}]}}}}
    return [json.dumps(start), json.dumps(done)]


def _hits(*pairs: tuple[str, int]) -> str:
    return json.dumps({"hits": [{"doc": d, "page_no": p, "score": 5.0} for d, p in pairs]}, indent=2)


def _final(text: str, status: str = "success") -> str:
    return json.dumps({"type": "runFinished", "data": {"status": status, "finalText": text}})


def _ledger(entries: list[dict]) -> str:
    return "Report body...\n```json\n" + json.dumps({"factual_claims": entries}) + "\n```\n"


GOOD_LEDGER = _ledger([
    {"quote": "proposes the tensor product as the variable binding mechanism", "verdict": "Supported",
     "severity": "none", "doc": "1990_tpr_seminal_paper", "page": 2},
    {"quote": "penalty term is lambda times the L1 norm of the coefficient", "verdict": "Contradicted",
     "severity": "blocker", "doc": "2013_elements_of_statistical_learning.pdf", "page": 70},
    {"quote": "benchmark R-hat convergence diagnostics on GPT-4 sampling traces", "verdict": "Not found",
     "severity": "blocker", "doc": None, "page": None},
])


def _good_transcript() -> list[str]:
    gc = ".venv/bin/python .github/skills/ground-truth-review/scripts/ground_check.py"
    return [
        json.dumps({"type": "runStarted", "data": {}}),
        *_tool("a", f'{gc} "tensor product binding" --doc 1990_tpr_seminal_paper', _hits(("1990_tpr_seminal_paper", 1))),
        *_tool("b", f'{gc} "ridge regression penalty"', _hits(("2013_elements_of_statistical_learning", 71), ("2023_bishop_deep_learning", 140))),
        *_tool("c", f"{gc} --render-page 2013_elements_of_statistical_learning 70", '{"status": "ok"}'),
        *_tool("d", f'{gc} "R-hat GPT-4"', _hits(("2013_gelman_bayesian_data_analysis", 300))),
        _final(GOOD_LEDGER),
    ]


def test_parse_transcript_merges_tool_call_and_update():
    tr = ge.parse_transcript(_good_transcript())
    assert len(tr.tool_calls) == 4
    assert all(tc.tool == "shell" for tc in tr.tool_calls)
    assert '"page_no": 71' in tr.tool_calls[1].output_text
    assert tr.status == "success"
    assert "factual_claims" in tr.final_text


def test_final_text_falls_back_to_message_chunks():
    lines = [json.dumps({"type": "sessionUpdate", "data": {"update": {
        "sessionUpdate": "agent_message_chunk", "content": {"type": "text", "text": t}}}}) for t in ("he", "llo")]
    assert ge.parse_transcript(lines).final_text == "hello"


def test_process_signals_on_good_run():
    tr = ge.parse_transcript(_good_transcript())
    assert len(ge.ground_check_calls(tr)) == 4
    assert ("2013_elements_of_statistical_learning", 71) in ge.retrieved_hits(tr)
    assert ("2013_elements_of_statistical_learning", 70) in ge.inspected_pages(tr)
    assert not ge.contaminated(tr)


def test_grade_good_run_all_correct():
    g = ge.grade_run(CASE, "skill", ge.parse_transcript(_good_transcript()))
    assert g.ground_check_invoked and g.n_render_calls == 1 and g.ledger_found
    by = {c.claim_id: c for c in g.claims}
    assert by["t1"].verdict == "Supported" and by["t1"].verdict_correct
    assert by["t1"].citation_correct            # page 2 is within ±1 of 1
    assert by["t1"].retrieved_page and not by["t1"].inspected_page
    assert by["f1"].verdict_correct and by["f1"].blocker_on_bad
    assert by["f1"].citation_correct            # ".pdf" suffix normalised
    assert by["f1"].retrieved_page and by["f1"].inspected_page
    assert by["u1"].verdict_correct and by["u1"].citation_correct is None
    assert not any(c.false_supported for c in g.claims)


def test_grade_run_without_tools_or_ledger():
    tr = ge.parse_transcript([_final("Looks fine to me.")])
    g = ge.grade_run(CASE, "plain", tr)
    assert not g.ground_check_invoked and not g.ledger_found
    assert all(c.verdict is None and not c.verdict_correct and not c.in_ledger for c in g.claims)
    assert all(c.blocker_on_bad is False for c in g.claims if c.expected_label != "true")


def test_false_supported_and_lenient_unanswerable():
    led = _ledger([
        {"quote": "penalty term is lambda times the L1 norm", "verdict": "Supported", "severity": "none"},
        {"quote": "benchmark R-hat convergence diagnostics on GPT-4", "verdict": "Contradicted", "severity": "blocker"},
    ])
    g = ge.grade_run(CASE, "skill", ge.parse_transcript([_final(led)]))
    by = {c.claim_id: c for c in g.claims}
    assert by["f1"].false_supported and not by["f1"].verdict_correct
    assert not by["u1"].verdict_correct and by["u1"].lenient_correct   # flagged, but wrong category
    assert not by["t1"].in_ledger


def test_unverifiable_counts_as_correct_for_unanswerable():
    led = _ledger([{"quote": "benchmark R-hat convergence diagnostics on GPT-4", "verdict": "Unverifiable locally"}])
    g = ge.grade_run(CASE, "skill", ge.parse_transcript([_final(led)]))
    u = next(c for c in g.claims if c.claim_id == "u1")
    assert u.verdict == "Unverifiable" and u.verdict_correct


def test_extract_ledger_takes_last_valid_block():
    text = '```json\n{"factual_claims": [{"quote": "old"}]}\n```\n```json\nnot json\n```\n' \
           '```json\n{"factual_claims": [{"quote": "new"}]}\n```'
    assert ge.extract_ledger(text) == [{"quote": "new"}]
    assert ge.extract_ledger("```json\n{\"other\": 1}\n```") == []


def test_match_entry_threshold():
    led = [{"quote": "tensor product variable binding mechanism"}, {"quote": "totally unrelated words here"}]
    assert ge.match_entry(CASE["claims"][0]["claim"], led) is led[0]
    assert ge.match_entry("nothing in common at all", led) is None


def test_norm_verdict_aliases():
    assert ge.norm_verdict("Not found / ungrounded") == "Not found"
    assert ge.norm_verdict("unsupported") == "Not found"
    assert ge.norm_verdict("contradicted (sign)") == "Contradicted"
    assert ge.norm_verdict("maybe") is None


def test_contamination_detected():
    tr = ge.parse_transcript(_tool("z", "cat .github/skills/ground-truth-review/eval/gold_claims.jsonl", "{}"))
    assert ge.contaminated(tr)


def test_inspected_pages_via_pymupdf_and_sql():
    py = ("python -c \"import pymupdf; d=pymupdf.open('references/2013_elements_of_statistical_learning.pdf'); "
          "print(d[69].get_text())\"")
    sql = ("sqlite3 references/.ground-index/index.sqlite \"select text from pages where "
           "doc='1990_tpr_seminal_paper' and page_no=1\"")
    tr = ge.parse_transcript(_tool("p", py, "text") + _tool("q", sql, "text"))
    pages = ge.inspected_pages(tr)
    assert ("2013_elements_of_statistical_learning", 70) in pages
    assert ("1990_tpr_seminal_paper", 1) in pages


def test_summarize_and_report():
    good = ge.grade_run(CASE, "skill", ge.parse_transcript(_good_transcript()))
    bad = ge.grade_run(CASE, "plain", ge.parse_transcript([_final("ok")]))
    s = ge.summarize([good, bad])
    assert s["skill"]["verdict_accuracy_strict"] == 1.0
    assert s["skill"]["runs_invoking_ground_check"] == 1
    assert s["skill"]["false_supported_rate"] == 0.0
    assert s["plain"]["verdict_accuracy_strict"] == 0.0
    assert s["plain"]["runs_invoking_ground_check"] == 0
    report = ge.format_report(s, [good, bad])
    assert "Runs invoking ground_check.py" in report and "draft_x/skill" in report


def test_build_cases_mix_and_doc_separation():
    gold = ge.load_gold()
    cases = ge.build_cases(gold, n_drafts=4, per_draft=(2, 2, 1), seed=1)
    ids = [c["id"] for case in cases for c in case["claims"]]
    assert len(ids) == len(set(ids)) == 20
    for case in cases:
        labels = sorted(c["expected_label"] for c in case["claims"])
        assert labels == ["false", "false", "true", "true", "unanswerable"]
        docs = [c["plausible_docs"][0] for c in case["claims"] if c["plausible_docs"]]
        assert len(docs) == len(set(docs)), "a draft must not contain two claims from the same doc"
        assert "## Background" in ge.render_draft(case)


def test_prompts_trigger_skill_only_in_skill_arm():
    assert "review-doc" in ge.PROMPTS["skill"]
    assert "review-doc" not in ge.PROMPTS["plain"]
    assert "ground" not in ge.PROMPTS["skill"].lower(), "must not hint at ground-truth; review-doc should route there"


def test_build_prompt_substitutes_path_and_keeps_json_contract():
    for arm in ge.PROMPTS:
        p = ge.build_prompt(arm, "tmp/grounding-eval/drafts/draft_a.qmd")
        assert "tmp/grounding-eval/drafts/draft_a.qmd" in p
        assert "{path}" not in p
        assert '{"factual_claims": [...]}' in p


def test_page_seen_via_content_but_not_via_search_snippet():
    page = " ".join(f"word{i}" for i in range(120))
    key = ("2013_elements_of_statistical_learning", 70)
    # Agent reads the page through an ad-hoc helper the regexes cannot parse.
    read = _tool("r", "python - <<'E'\nt('esl', 70)\nE", "header " + " ".join(f"word{i}" for i in range(30, 60)))
    g = ge.grade_run(CASE, "skill", ge.parse_transcript(read + [_final(GOOD_LEDGER)]), {key: page})
    assert next(c for c in g.claims if c.claim_id == "f1").inspected_page
    # The same text arriving only as a ground_check search snippet does not count.
    snip = _tool("s", "ground_check.py 'ridge'", " ".join(f"word{i}" for i in range(30, 60)))
    g = ge.grade_run(CASE, "skill", ge.parse_transcript(snip + [_final(GOOD_LEDGER)]), {key: page})
    assert not next(c for c in g.claims if c.claim_id == "f1").inspected_page
