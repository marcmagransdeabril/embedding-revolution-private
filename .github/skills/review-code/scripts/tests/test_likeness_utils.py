"""Unit tests of the helpers of the chapter "Meaning as Likeness" (code/meaning_as_likeness/utils.py): each one is small and has a known answer."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

# Loaded under its own name: every chapter directory has its own `utils`.
_PATH = Path(__file__).resolve().parents[5] / "code" / "meaning_as_likeness" / "utils.py"
_spec = importlib.util.spec_from_file_location("meaning_as_likeness_utils", _PATH)
utils = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(utils)


def test_fetch_stops_on_a_file_that_does_not_match_its_pin(tmp_path, monkeypatch):
    monkeypatch.setattr(utils, "CACHE", tmp_path)
    (tmp_path / "x.zip").write_bytes(b"not the pinned file")
    with pytest.raises(ValueError):
        utils.fetch("http://example.org/x.zip", "0" * 64)


def test_fetch_accepts_a_file_that_matches_its_pin(tmp_path, monkeypatch):
    monkeypatch.setattr(utils, "CACHE", tmp_path)
    (tmp_path / "x.zip").write_bytes(b"abc")
    sha = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert utils.fetch("http://example.org/x.zip", sha) == tmp_path / "x.zip"


def test_cooccurrence_counts_both_directions_and_skips_the_words_left_out():
    c = utils.cooccurrence(np.array([0, 1, 2, -1, 0], dtype=np.int32), 3, 1).toarray()
    assert np.array_equal(c, c.T)
    assert c[0, 1] == 1 and c[1, 2] == 1 and c[0, 2] == 0 and c.sum() == 4  # the left-out word makes no pair with its neighbours


def test_ppmi_of_a_perfectly_associated_pair_is_one_bit_and_of_independent_words_zero():
    m = utils.ppmi(sparse.csr_matrix(np.array([[0.0, 4.0], [4.0, 0.0]], dtype=np.float32))).toarray()
    assert m[0, 1] == pytest.approx(1.0) and m[0, 0] == 0
    independent = sparse.csr_matrix(np.outer([1.0, 2.0], [1.0, 2.0]).astype(np.float32))
    assert utils.ppmi(independent).nnz == 0


def test_ceiling_of_raters_who_agree_is_one():
    ratings = np.tile(np.arange(20.0)[:, None], (1, 4))
    one_vs_rest, pairwise = utils.ceiling(ratings)
    assert one_vs_rest == pytest.approx(1.0) and pairwise == pytest.approx(1.0)


def test_nearest_excludes_the_word_itself_and_orders_by_cosine():
    emb = np.array([[1.0, 0], [0.9, 0.1], [0, 1.0], [-1.0, 0]])
    nn = utils.nearest(emb, np.array([0]), 2)
    assert list(nn[0]) == [1, 2]


def test_neighbour_overlap_is_the_share_of_neighbours_in_common():
    assert utils.neighbour_overlap(np.array([[1, 2, 3, 4]]), np.array([[3, 4, 5, 6]])) == pytest.approx([0.5])


def test_spearman_interval_contains_the_correlation_and_is_reproducible():
    x = np.arange(50.0)
    y = x + np.random.default_rng(0).normal(0, 5, 50)
    rho, low, high = utils.spearman_interval(x, y, resamples=200)
    assert low <= rho <= high and utils.spearman_interval(x, y, resamples=200)[1] == low


def test_edit_distance_has_known_values():
    assert utils.edit_distance("kitten", "sitting") == pytest.approx(3 / 7)
    assert utils.edit_distance("dog", "dog") == 0 and utils.edit_distance("", "ab") == 1


def test_auc_from_histogram_matches_the_pairwise_definition():
    # negatives at scores 0 (x2), 1 (x1), 3 (x1); positives at scores 1 and 2; P(pos > neg) with ties as one half
    negatives = np.array([2, 1, 0, 1])
    expected = (np.mean([2 > 0, 2 > 0, 2 > 1, 2 > 3]) + np.mean([1 > 0, 1 > 0, 0.5, 1 > 3])) / 2
    assert utils.auc_against_histogram(np.array([1, 2]), negatives) == pytest.approx(expected)
    assert utils.auc_against_histogram(np.array([1, 2]), negatives, np.array([1, 0])) == pytest.approx(np.mean([1, 1, 0.5, 0]))


def test_auc_of_scores_with_no_structure_is_one_half():
    rng = np.random.default_rng(0)
    negatives = np.bincount(rng.integers(0, 50, 100_000), minlength=50)
    assert utils.auc_against_histogram(rng.integers(0, 50, 5_000), negatives) == pytest.approx(0.5, abs=0.02)


def test_bootstrap_interval_contains_the_point_estimate_and_is_narrow_for_many_pairs():
    rng = np.random.default_rng(1)
    pairs = np.sort(rng.integers(0, 200, (3_000, 2)), axis=1)
    bins = rng.integers(0, 50, 3_000) + 5
    negatives = np.bincount(rng.integers(0, 50, 100_000), minlength=60)
    point, low, high = utils.bootstrap_words_auc(pairs, bins, negatives, 200, resamples=50)
    assert low <= point <= high and high - low < 0.1


def test_wordnet_pairs_reads_synonyms_and_antonyms_from_data_files(tmp_path, monkeypatch):
    import io
    import tarfile
    big = "00000001 00 a 02 big 0 large 0 001 ! 00000002 a 0101 | gloss"
    small = "00000002 00 a 01 small 0 001 ! 00000001 a 0101 | gloss"
    data = {"noun": "  license line\n", "verb": "", "adv": "", "adj": f"  license line\n{big}\n{small}\n"}
    path = tmp_path / "wn.tar.gz"
    with tarfile.open(path, "w:gz") as tar:
        for kind, text in data.items():
            blob = text.encode()
            info = tarfile.TarInfo(f"WordNet-3.0/dict/data.{kind}")
            info.size = len(blob)
            tar.addfile(info, io.BytesIO(blob))
    monkeypatch.setattr(utils, "fetch", lambda url, sha: path)
    index = {"big": 0, "large": 1, "small": 2, "huge": 3}
    synonyms, antonyms, covered = utils.wordnet_pairs(index)
    assert synonyms.tolist() == [[0, 1]]
    assert antonyms.tolist() == [[0, 2]]  # small is the antonym of big and large is not listed with it: the pointer is word to word
    assert covered.tolist() == [True, True, True, False]


def test_bootstrap_mean_interval_covers_the_mean_and_shrinks_with_more_items():
    rng = np.random.default_rng(0)
    small, large = rng.normal(0, 1, 50), rng.normal(0, 1, 5_000)
    m1, l1, h1 = utils.bootstrap_mean(small, 200)
    m2, l2, h2 = utils.bootstrap_mean(large, 200)
    assert l1 <= m1 <= h1 and l2 <= m2 <= h2 and (h2 - l2) < (h1 - l1) / 5
    assert utils.bootstrap_mean(np.array([1.0, 1.0, 1.0]), 50) == (1.0, 1.0, 1.0)


def test_mean_cosine_is_exact_over_all_pairs_and_its_interval_covers_it():
    rng = np.random.default_rng(0)
    u = utils.unit(rng.normal(0.3, 1, (60, 5)).astype(np.float32))
    brute = np.mean([u[i] @ u[j] for i in range(60) for j in range(60) if i != j])
    assert utils.mean_cosine(u) == pytest.approx(brute, abs=1e-6)
    mean, low, high = utils.bootstrap_mean_cosine(u, 100)
    assert low <= mean <= high and mean == pytest.approx(brute, abs=1e-6)


def test_bootstrap_words_point_is_the_unweighted_statistic_and_the_interval_covers_it():
    rng = np.random.default_rng(1)
    pairs = rng.integers(0, 200, (500, 2))
    values = rng.normal(size=500)
    point, low, high = utils.bootstrap_words(pairs, lambda w: utils.weighted_mean(values, w), resamples=300)
    assert point == pytest.approx(values.mean())
    assert low < point < high


def test_bootstrap_words_is_wider_when_pairs_share_words():
    # the same 500 values, attached once to 500 pairs of distinct words and once to pairs drawn from 10 words; when the value of a
    # pair follows its words, resampling the words moves whole groups of pairs together, so the interval widens
    rng = np.random.default_rng(2)
    distinct = np.arange(1000).reshape(500, 2)
    shared = rng.integers(0, 10, (500, 2))
    word_effect = rng.normal(size=10)
    values = word_effect[shared[:, 0]] + word_effect[shared[:, 1]]
    stat = lambda w: utils.weighted_mean(values, w)
    _, lo_d, hi_d = utils.bootstrap_words(distinct, stat, resamples=300)
    _, lo_s, hi_s = utils.bootstrap_words(shared, stat, resamples=300)
    assert hi_s - lo_s > 2 * (hi_d - lo_d)


def test_weighted_mean_and_spearman_repeat_items_by_their_weights():
    assert utils.weighted_mean(np.array([1.0, 3.0]), np.array([3, 1])) == pytest.approx(1.5)
    assert np.isnan(utils.weighted_mean(np.array([1.0]), np.array([0])))
    x = np.array([1.0, 2.0, 3.0, 4.0])
    assert utils.weighted_spearman(x, x, np.array([1, 2, 0, 1])) == pytest.approx(1.0)
    assert utils.weighted_spearman(x, -x, np.ones(4, dtype=int)) == pytest.approx(-1.0)
    assert np.isnan(utils.weighted_spearman(x, x, np.array([1, 1, 0, 0])))


def test_weighted_partial_spearman_removes_the_shared_judge():
    rng = np.random.default_rng(3)
    z = rng.normal(size=400)
    x, y = z + 0.3 * rng.normal(size=400), z + 0.3 * rng.normal(size=400)
    ones = np.ones(400, dtype=int)
    assert utils.weighted_spearman(x, y, ones) > 0.8  # correlated only through z
    assert abs(utils.weighted_partial_spearman(x, y, z, ones)) < 0.2
    assert np.isnan(utils.weighted_partial_spearman(x, y, z, np.array([1, 1] + [0] * 398)))


def test_pair_array_orders_each_pair_and_drops_repeats_and_self_pairs():
    assert utils.pair_array([(3, 1), (1, 3), (2, 2), (0, 4)]).tolist() == [[0, 4], [1, 3]]
    assert utils.pair_array([]).shape == (0, 2)


def test_first_label_keeps_each_pair_under_the_first_relation_only():
    relations = {"a": np.array([[0, 1], [1, 2]]), "b": np.array([[0, 1], [2, 3]])}
    first = utils.first_label(relations, ["a", "b"], 5)
    assert first["a"].tolist() == [[0, 1], [1, 2]] and first["b"].tolist() == [[2, 3]]
    single = utils.single_label(relations, ["a", "b"], 5)
    assert single["a"].tolist() == [[1, 2]] and single["b"].tolist() == [[2, 3]]


def test_base_forms_follow_the_rules_of_morphy_and_its_exceptions():
    lemmas = {"walk", "church", "go", "big"}
    assert utils.base_forms("walked", "v", lemmas, {}) == {"walk"}
    assert utils.base_forms("churches", "n", lemmas, {}) == {"church"}
    assert utils.base_forms("went", "v", lemmas, {"went": ["go"]}) == {"go"}
    assert utils.base_forms("walk", "v", lemmas, {}) == {"walk"}  # a lemma is its own base form
    assert utils.base_forms("s", "n", {""}, {}) == set()  # a rule never strips the whole word


def test_inflection_pairs_join_the_forms_of_one_base_and_not_two_bases():
    vocab = ["walk", "walked", "walking", "talk", "went", "go"]
    lemmas = {"n": set(), "v": {"walk", "talk", "go"}, "a": set()}
    pairs = utils.inflection_pairs(vocab, lemmas, {"n": {}, "v": {"went": ["go"]}, "a": {}})
    named = {(vocab[a], vocab[b]) for a, b in pairs}
    assert named == {("walk", "walked"), ("walk", "walking"), ("walked", "walking"), ("went", "go")}


def test_wordnet_pointers_tell_semantic_from_lexical_pointers():
    # offset, file, type, 2 words, 2 pointers: a hypernym between synsets (0000) and an antonym from word 2 to word 1 of its target
    fields = "00001 03 n 02 dog 0 hound 0 002 @ 00002 n 0000 ! 00003 n 0201 | gloss".split()
    assert list(utils.wordnet_pointers(fields, ["dog", "hound"])) == [("@", "00002", "n", None, 0), ("!", "00003", "n", "hound", 1)]


def test_histogram_auc_is_one_half_for_equal_histograms_and_one_for_separated_ones():
    h = np.array([1.0, 2.0, 3.0])
    assert utils.histogram_auc(h, h) == pytest.approx(0.5)
    assert utils.histogram_auc(np.array([0.0, 0.0, 5.0]), np.array([4.0, 0.0, 0.0])) == pytest.approx(1.0)
    assert utils.histogram_auc(np.array([1.0, 0.0]), np.array([0.0, 1.0])) == pytest.approx(0.0)
