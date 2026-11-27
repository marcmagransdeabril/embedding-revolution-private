"""Unit tests of the helpers shared by the solution scripts (embedding-technologies-stubs-v1/code/embedding_spaces/utils.py, the dissolved chapter on the objectives): each one is small and has a known answer."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

UTILS_DIR = Path(__file__).resolve().parents[5] / "embedding-technologies-stubs-v1" / "code" / "embedding_spaces"
sys.path.insert(0, str(UTILS_DIR))
import utils  # noqa: E402


def test_cooccurrence_is_symmetric_and_counts_neighbours_inside_the_sentence():
    vocab, c = utils.cooccurrence([["a", "b", "c"], ["a", "b"]], window=1)
    assert vocab == ["a", "b", "c"]
    assert np.array_equal(c, c.T)
    assert c[0, 1] == 2 and c[1, 2] == 1 and c[0, 2] == 0  # a-b in both sentences, a-c too far apart


def test_ppmi_of_independent_words_is_zero_and_of_unseen_pairs_is_zero():
    independent = np.outer([1.0, 2.0], [3.0, 1.0])  # P(w, c) = P(w) P(c)
    assert np.allclose(utils.ppmi(independent), 0)
    assert utils.ppmi(np.array([[4.0, 0.0], [0.0, 4.0]]))[0, 1] == 0


def test_ppmi_of_a_perfectly_associated_pair_in_bits():
    m = utils.ppmi(np.array([[4.0, 0.0], [0.0, 4.0]]))
    assert m[0, 0] == pytest.approx(1.0)  # P(w,c) = 1/2, P(w) = P(c) = 1/2 -> log2(2)


def test_truncated_svd_with_full_rank_keeps_all_inner_products():
    rng = np.random.default_rng(0)
    m = rng.standard_normal((5, 5))
    e = utils.truncated_svd(m, 5)
    assert np.allclose(e @ e.T, m @ m.T)


def test_cosine_of_parallel_orthogonal_and_zero_vectors():
    assert utils.cosine(np.array([1.0, 0]), np.array([2.0, 0])) == pytest.approx(1.0)
    assert utils.cosine(np.array([1.0, 0]), np.array([0, 1.0])) == pytest.approx(0.0)
    assert utils.cosine(np.zeros(2), np.array([1.0, 0])) == 0.0


def test_bootstrap_interval_contains_the_mean_and_is_reproducible():
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    mean, low, high = utils.bootstrap_interval(x, resamples=500)
    assert mean == pytest.approx(3.0) and low <= mean <= high
    assert utils.bootstrap_interval(x, resamples=500)[1] == low


def test_load_book_checks_the_pinned_text():
    text = utils.load_book()
    assert "pride and prejudice" in text and text == text.lower()
