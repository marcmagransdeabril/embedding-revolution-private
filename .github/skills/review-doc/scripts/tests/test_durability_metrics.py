"""Tests for the ledger lint and the durability metrics used by review-doc §17 and §18."""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import durability_metrics as dm  # noqa: E402

TODAY = dt.date(2026, 11, 10)
BIB = {"rice1953classes", "levy2014neural"}


def entry(**kw):
    base = {"id": "E1", "level": "chapter", "question": "q?", "status": "open", "confidence": "none",
            "evidence": {"for": [], "against": []}, "checked": TODAY}
    base.update(kw)
    return base


def lint(*entries, log=None, root=Path("/nonexistent")):
    return dm.lint_ledger({"questions": list(entries), "log": log or []}, BIB, root, TODAY)


def messages(issues, severity=None):
    return [m for s, _, m in issues if severity in (None, s)]


def test_repo_ledger_has_no_errors():
    ledger = dm.load_ledger(dm.LEDGER)
    bib = set(dm.parse_bibliography(dm.REPO_ROOT / "references.bib"))
    issues = dm.lint_ledger(ledger, bib, dm.REPO_ROOT, TODAY)
    assert [i for i in issues if i[0] == "error"] == []


def test_open_entry_needs_nothing_else():
    assert lint(entry()) == []


def test_committed_reading_needs_evidence_falsifier_and_reading():
    out = messages(lint(entry(status="leaning")), "error")
    assert any("without any evidence" in m for m in out)
    assert any("without a falsifier" in m for m in out)
    assert any("without a reading" in m for m in out)


def test_confidence_is_capped_by_evidence_kind():
    weak = {"for": [{"src": "rice1953classes", "kind": "position"}], "against": []}
    out = messages(lint(entry(status="supported", reading="r", falsifier="f", confidence="medium", evidence=weak)), "error")
    assert any("needs at least one solid evidence kind" in m for m in out)

    solid = {"for": [{"src": "rice1953classes", "kind": "theorem"}], "against": []}
    assert messages(lint(entry(status="supported", reading="r", falsifier="f", confidence="medium", evidence=solid)), "error") == []
    # high needs a theorem or two solid sources; one replicated study is not enough
    one = {"for": [{"src": "levy2014neural", "kind": "replicated"}], "against": []}
    out = messages(lint(entry(status="supported", reading="r", falsifier="f", confidence="high", evidence=one)), "error")
    assert any("theorem or two solid" in m for m in out)


def test_high_confidence_with_opposing_evidence_needs_an_answer():
    ev = {"for": [{"src": "rice1953classes", "kind": "theorem"}],
          "against": [{"src": "levy2014neural", "kind": "single-study"}]}
    out = messages(lint(entry(status="supported", reading="r", falsifier="f", confidence="high", evidence=ev)), "error")
    assert any("answered_against" in m for m in out)


def test_roll_up_warns_when_parent_exceeds_weakest_child():
    solid = {"for": [{"src": "rice1953classes", "kind": "theorem"}], "against": [{"src": "levy2014neural", "kind": "position"}]}
    parent = entry(id="P", level="book", status="supported", reading="r", falsifier="f", confidence="medium",
                   evidence=solid, depends_on=["C"])
    child = entry(id="C", status="open", confidence="none")
    assert any("exceeds its weakest dependency" in m for m in messages(lint(parent, child), "warn"))


def test_one_sided_and_stale_entries_are_warned():
    ev = {"for": [{"src": "rice1953classes", "kind": "theorem"}], "against": []}
    old = TODAY - dt.timedelta(days=400)
    out = messages(lint(entry(status="supported", reading="r", falsifier="f", confidence="low", evidence=ev, checked=old)), "warn")
    assert any("one-sided" in m for m in out)
    assert any("not checked for 400 days" in m for m in out)


def test_unknown_source_and_dependency_are_errors():
    ev = {"for": [{"src": "nobody2099", "kind": "theorem"}], "against": []}
    out = messages(lint(entry(status="leaning", reading="r", falsifier="f", evidence=ev, depends_on=["Z"])), "error")
    assert any("neither a citekey nor an existing path" in m for m in out)
    assert any("depends_on 'Z'" in m for m in out)


def test_revised_needs_a_log_entry():
    assert any("needs an entry in log" in m for m in messages(lint(entry(status="revised")), "error"))
    assert messages(lint(entry(status="revised"), log=[{"id": "E1"}]), "error") == []


def test_file_metrics_reads_year_of_cited_keys():
    bib = {"a": {"year": "{1948}"}, "b": {"year": "2024"}, "c": {"year": "1956"}}
    m = dm.file_metrics("See [@a; @b; @c] and [@missing].", bib)
    assert m == {"cites": 3, "median_year": 1956, "before_1980": 2, "from_2020": 1, "from_2023": 1}


def test_perishable_relative_wording_and_titles():
    texts = {"x.qmd": "# Quantum Logic\nRecently, CLIP and LLMs appeared.\n", "y.qmd": "ImageBind. Transformer.\n"}
    counts = dm.perishable_counts(texts)
    assert counts["CLIP/ImageBind"] == {"occurrences": 2, "files": 2}
    assert dm.relative_wording(texts) == ["x.qmd:2"]
    assert dm.fashion_titles(texts) == ["x.qmd:1: # Quantum Logic"]


def test_diff_reports_only_changes():
    base = {"date": "d", "files": {"a": {"cites": 1, "median_year": 1950, "from_2023": 0}},
            "perishable": {"T": {"occurrences": 1, "files": 1}}, "relative_wording": [], "fashion_titles": [],
            "ledger": {"entries": 1}}
    assert dm.diff_metrics(base, base) == []
    new = {**base, "files": {"a": {"cites": 2, "median_year": 2020, "from_2023": 1}},
           "relative_wording": ["a:3"]}
    out = dm.diff_metrics(base, new)
    assert any("median year 1950 -> 2020" in line for line in out)
    assert any("relative_wording: +1 new" in line for line in out)


def tree_lint(ledger, root=Path("/nonexistent")):
    ledger.setdefault("chapters_checked", True)
    return dm.lint_tree(ledger, root)


def test_repo_tree_has_no_errors():
    ledger = dm.load_ledger(dm.LEDGER)
    assert [i for i in dm.lint_tree(ledger, dm.REPO_ROOT) if i[0] == "error"] == []


def test_dropped_node_needs_why_and_exploratory_needs_gate():
    ledger = {"tree": [
        {"id": "A", "parent": None, "kind": "idea", "commitment": "dropped"},
        {"id": "B", "parent": None, "kind": "chapter", "commitment": "exploratory"}]}
    out = tree_lint(ledger)
    assert ("error", "A", "dropped without 'why' (record what was learned, so it is not explored twice)") in out
    assert any(i[1] == "B" and "no gate" in i[2] for i in out)


def test_gate_decided_needs_option_and_reason_and_due_is_reported():
    base = {"tree": [], "questions": [{"id": "Q", "status": "leaning"}]}
    opts = [{"id": "a"}, {"id": "b"}]
    pending = {**base, "gates": [{"id": "G", "status": "pending", "options": opts, "evidence_needed": ["Q"]}]}
    assert ("info", "G", "decision due: every question it waits for now has a reading") in tree_lint(pending)
    bad = {**base, "gates": [{"id": "G", "status": "decided", "options": opts, "decision": "z"}]}
    msgs = [m for _, _, m in tree_lint(bad)]
    assert any("not one of the options" in m for m in msgs) and any("without 'decided_on'" in m for m in msgs)


def test_recurring_gate_is_never_due():
    base = {"tree": [], "questions": [{"id": "Q", "status": "leaning"}]}
    g = {"id": "G", "status": "recurring", "options": [{"id": "a"}, {"id": "b"}], "evidence_needed": ["Q"],
         "last_reviewed": dt.date.today()}
    assert not [i for i in tree_lint({**base, "gates": [g]}) if i[0] in ("info", "error")]


def test_open_set_is_never_complete_and_needs_a_search_date():
    q = entry(id="S", open_set=True, members=["n"], status="supported", reading="r", falsifier="f", confidence="low",
              evidence={"for": [{"src": "rice1953classes", "kind": "interpretive"}], "against": []})
    issues = lint(q)
    assert any("open set cannot be 'supported'" in m for m in messages(issues, "error"))
    assert any("no 'last_search'" in m for m in messages(issues, "warn"))


def test_chapter_file_without_node_is_reported(tmp_path):
    (tmp_path / "chapters").mkdir()
    (tmp_path / "chapters" / "x.qmd").write_text("x")
    assert any("no node in the tree" in m for _, _, m in dm.lint_tree({"tree": []}, tmp_path))
