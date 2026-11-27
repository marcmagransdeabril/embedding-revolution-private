"""Tests of acp_client.py (against a fake agent) and of the steps of relation_unlabelled.py that do not need the trained spaces."""
import csv
import json
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))

import acp_client  # noqa: E402
import relation_collapse as rc  # noqa: E402
import relation_unlabelled as ru  # noqa: E402

FAKE = [sys.executable, str(HERE / "fake_acp_agent.py")]


def rater(monkeypatch, timeout=10, **env):
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    return acp_client.AcpRater(command=FAKE, timeout=timeout)


# --- acp_client
def test_ask_assembles_chunks_and_pins_model(monkeypatch):
    with rater(monkeypatch, FAKE_REPLY="a reply longer than one chunk") as r:
        assert r.ask("hi") == "a reply longer than one chunk"
        assert r.ask("again") == "a reply longer than one chunk"  # a second session on the same process


def test_permission_is_rejected(monkeypatch, tmp_path):
    out = tmp_path / "perm.json"
    with rater(monkeypatch, FAKE_PERMISSION=str(out)) as r:
        r.ask("hi")
    assert json.loads(out.read_text())["result"]["outcome"] == {"outcome": "selected", "optionId": "no"}


def test_model_not_confirmed_fails(monkeypatch):
    with rater(monkeypatch, FAKE_MODEL_IGNORED="1") as r, pytest.raises(acp_client.AcpError, match="model"):
        r.ask("hi")


def test_fallback_fails(monkeypatch):
    with rater(monkeypatch, FAKE_FALLBACK="1") as r, pytest.raises(acp_client.AcpError, match="fallback"):
        r.ask("hi")


def test_timeout_and_cleanup(monkeypatch):
    r = rater(monkeypatch, timeout=1, FAKE_HANG="1").start()
    with pytest.raises(acp_client.AcpError, match="no response"):
        r.ask("hi")
    r.close()
    assert r.process.poll() is not None


# --- sampling
def test_sample_far_is_exact_and_seeded():
    rng = np.random.default_rng(1)
    spaces = [ru.utils.unit(rng.normal(size=(60, 5)).astype(np.float32)) for _ in range(2)]
    ru.BLOCK = 7  # several blocks
    highs = [int(np.percentile(ru.gallery.to_bin(u @ u.T)[np.triu_indices(60, 1)], 20)) for u in spaces]
    labelled = np.array([0 * 60 + 1, 3 * 60 + 9], dtype=np.int64)
    keys, count = ru.sample_far(spaces, highs, labelled, 15, seed=0)
    i, j = np.triu_indices(60, 1)
    ok = np.ones(len(i), bool)
    for u, h in zip(spaces, highs):
        ok &= ru.gallery.to_bin((u[i] * u[j]).sum(1)) < h
    eligible = set((i[ok] * 60 + j[ok]).tolist()) - set(labelled.tolist())
    assert count == len(eligible) and len(keys) == 15 and set(keys.tolist()) <= eligible
    assert np.array_equal(keys, ru.sample_far(spaces, highs, labelled, 15, seed=0)[0])
    ru.BLOCK = 1000


def test_sample_far_with_lower_bounds_and_exclusions():
    rng = np.random.default_rng(2)
    spaces = [ru.utils.unit(rng.normal(size=(50, 5)).astype(np.float32)) for _ in range(2)]
    ru.BLOCK = 11
    bins = [ru.gallery.to_bin(u @ u.T) for u in spaces]
    i, j = np.triu_indices(50, 1)
    lows = [int(np.percentile(b[i, j], 80)) for b in bins]
    ok = (bins[0][i, j] >= lows[0]) & (bins[1][i, j] >= lows[1])
    eligible = set((i[ok] * 50 + j[ok]).tolist())
    excluded = np.array(sorted(list(eligible)[:2]), dtype=np.int64)
    keys, count = ru.sample_far(spaces, [ru.gallery.BINS] * 2, excluded, 5, seed=0, lows=lows)
    assert count == len(eligible) - 2 and set(keys.tolist()) <= eligible - set(excluded.tolist()) and len(keys) == 5
    ru.BLOCK = 1000


def test_sample_known_has_no_repeats_and_relations_are_complete():
    size = 50
    pairs = {name: np.array([[0, 1], [2, 3], [4, 5 + k]], dtype=np.int64) for k, name in enumerate(rc.RELATIONS)}
    known = ru.sample_known(pairs, size, 2, seed=0)
    keys = np.concatenate([ru.utils.pair_keys(v, size) for v in known.values()])
    assert len(keys) == len(set(keys.tolist()))
    held = ru.relations_of(np.array([[0, 1], [4, 5]]), pairs, size)
    assert held[0] == rc.RELATIONS and held[1] == [rc.RELATIONS[0]]


# --- labelling
def write_blind(path, n):
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "word_a", "word_b"])
        for k in range(n):
            w.writerow([f"p{k + 1:04d}", f"a{k}", f"b{k}"])


def test_parse_answer_drops_bad_lines():
    text = 'x\n{"id": "p0001", "relations": ["Opposite ", "opposite"]},\n{"id": "p9", "relations": []}\n{bad\n{"id": "p0002", "relations": []}'
    assert ru.parse_answer(text, ["p0001", "p0002"]) == {"p0001": ["opposite"], "p0002": []}


def test_label_resumes_and_refuses_other_sample(monkeypatch, tmp_path):
    blind, labels, log = tmp_path / "blind.csv", tmp_path / "labels.jsonl", tmp_path / "log"
    write_blind(blind, 25)
    with rater(monkeypatch, FAKE_REPLY="ECHO_IDS", FAKE_LOG=str(log)) as r:
        assert ru.label(r, blind, labels, limit=2) == 2
        assert len(ru.read_labels(labels)[1]) == 20
        assert ru.label(r, blind, labels) == 1
    header, got = ru.read_labels(labels)
    assert header["model"] == acp_client.MODEL and len(got) == 25 and got["p0003"] == ["r-a2"]
    assert len(log.read_text().splitlines()) == 3  # every pair asked once, in batches of 10
    write_blind(blind, 26)
    with pytest.raises(SystemExit, match="another sample"):
        ru.label(None, blind, labels)


def test_missing_id_is_asked_again(monkeypatch, tmp_path):
    blind, labels, log = tmp_path / "blind.csv", tmp_path / "labels.jsonl", tmp_path / "log"
    write_blind(blind, 3)
    with rater(monkeypatch, FAKE_REPLY='{"id": "p0001", "relations": []}', FAKE_LOG=str(log)) as r:
        ru.label(r, blind, labels)
    assert ru.read_labels(labels)[1] == {"p0001": []}
    assert len(log.read_text().splitlines()) == 3  # the batch, then p0002 and p0003 alone


# --- consolidation
def test_consolidate_maps_every_name_and_the_relations(monkeypatch):
    ru.MERGE_CHUNK = 4
    with rater(monkeypatch, FAKE_REPLY="MAP") as r:
        mapping = ru.consolidate(r, ["opposite", "part of", "same topic"])
    ru.MERGE_CHUNK = 300
    assert set(mapping) == set(rc.RELATIONS) | {"opposite", "part of", "same topic"}
    assert mapping["opposite"] == "c-opposite" and mapping["antonym"] == "c-antonym"


def test_consolidate_keeps_the_base_map(monkeypatch):
    base = {r: r for r in rc.RELATIONS} | {"opposite": "antonym"}
    with rater(monkeypatch, FAKE_REPLY="MAP") as r:
        mapping = ru.consolidate(r, ["opposite", "part of"], base)
    assert mapping["opposite"] == "antonym" and mapping["part of"] == "c-part of" and len(mapping) == len(base) + 1


# --- report
def test_difference_of_shares():
    a, b = np.array([1] * 30 + [0] * 70), np.array([1] * 10 + [0] * 90)
    d = ru.difference(a, b)
    assert d[0] == pytest.approx(0.2) and d[1] < 0.2 < d[2] and d[1] > 0


def test_analyse_recall_precision_and_open_groups():
    key = {"p1": {"subset": "antonym", "relations": ["antonym"], "words": ["hot", "cold"], "cosine": {"S": 0.5}},
           "p2": {"subset": "antonym", "relations": ["antonym"], "words": ["up", "down"], "cosine": {"S": 0.4}},
           "p3": {"subset": "synonym", "relations": ["synonym", "antonym"], "words": ["x", "y"], "cosine": {"S": 0.3}},
           "f1": {"subset": ru.FAR, "relations": [], "words": ["cat", "tax"], "cosine": {"S": -0.2}},
           "f2": {"subset": ru.FAR, "relations": [], "words": ["dog", "law"], "cosine": {"S": -0.3}}}
    labels = {"p1": ["opposite"], "p2": [], "p3": ["antonym", "same meaning"], "f1": ["rhyme", "both nouns"], "f2": []}
    mapping = {r: r for r in rc.RELATIONS} | {"opposite": "antonym", "same meaning": "synonym", "rhyme": "rhyme", "both nouns": "noun"}
    result = ru.analyse(key, labels, mapping)
    c = result["control"]
    assert c["recall"]["antonym"][0] == 0.5 and c["recall"]["synonym"][0] == 1.0
    assert c["precision"]["antonym"]["value"][0] == 1.0  # p3 is given antonym and holds it
    assert c["confusion"]["antonym"][ru.NONE] == 1 and c["none"]["all known"][0] == pytest.approx(1 / 3)
    far = {g["relation"]: g for g in result["open"][ru.FAR]["groups"]}
    assert far["rhyme"]["count"] == 1 and far[ru.NONE]["count"] == 1 and far["rhyme"]["pairs"][0]["names"] == ["rhyme"]
    assert far["noun"]["share"][0] == 0.5 and result["open"][ru.FAR]["any relation"][0] == 0.5
    assert result["differences"] == {} and "## far in both" in ru.markdown(result, "m")


def test_analyse_compares_open_subsets():
    mapping = {r: r for r in rc.RELATIONS} | {"x": "x"}
    key = {f"a{i}": {"subset": ru.FAR, "relations": [], "words": ["w", "v"], "cosine": {"S": -0.2}} for i in range(40)}
    key |= {f"b{i}": {"subset": ru.RANDOM_SUBSET, "relations": [], "words": ["w", "v"], "cosine": {"S": 0.0}} for i in range(40)}
    key |= {f"c{i}": {"subset": ru.NEAR, "relations": [], "words": ["w", "v"], "cosine": {"S": 0.5}} for i in range(40)}
    labels = {i: ["x"] if (i[0] == "c" or (i[0] == "b" and int(i[1:]) < 10)) else [] for i in key}
    labels |= {i: [] for i in key if i[0] == "a"}
    result = ru.analyse(key, labels, mapping)
    assert result["open"][ru.NEAR]["any relation"][0] == 1.0 and result["open"][ru.FAR]["any relation"][0] == 0.0
    assert result["differences"][f"{ru.FAR} minus {ru.RANDOM_SUBSET}"][0] == pytest.approx(-0.25)
    assert result["differences"][f"{ru.NEAR} minus {ru.RANDOM_SUBSET}"][0] == pytest.approx(0.75)
    assert result["open"][ru.FAR]["judged by a dictionary"][0] == 0.0 and ru.RANDOM_ANY not in result["open"]
