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
