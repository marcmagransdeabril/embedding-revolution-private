"""Unit tests of the helpers of Chapter 2 (code/properties_of_meaning/utils.py): each one is small and has a known answer."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import numpy as np
import pytest

# Loaded under its own name: code/embedding_spaces/utils.py and code/symbols_without_interior/utils.py are also called `utils`.
_PATH = Path(__file__).resolve().parents[5] / "code" / "properties_of_meaning" / "utils.py"
_spec = importlib.util.spec_from_file_location("properties_of_meaning_utils", _PATH)
utils = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(utils)


def test_cosine_of_parallel_orthogonal_and_opposite_vectors():
    c = utils.cosine_matrix(np.array([[1.0, 0.0]]), np.array([[2.0, 0.0], [0.0, 3.0], [-1.0, 0.0]]))
    assert c == pytest.approx(np.array([[1.0, 0.0, -1.0]]))


def test_unit_keeps_a_zero_row_at_zero():
    assert utils.unit(np.array([[3.0, 4.0], [0.0, 0.0]])) == pytest.approx(np.array([[0.6, 0.8], [0.0, 0.0]]))


def test_center_gives_zero_mean():
    assert utils.center(np.array([[1.0, 2.0], [3.0, 4.0]])).mean(axis=0) == pytest.approx([0.0, 0.0])


def test_mean_cosine_is_one_for_a_shared_direction_and_small_for_random_vectors():
    assert utils.mean_cosine(np.array([[1.0, 0.0], [2.0, 0.0], [3.0, 0.0]])) == pytest.approx(1.0)
    assert abs(utils.mean_cosine(utils.random_vectors(200, 300))) < 0.01


def test_centring_removes_a_common_offset():
    x = utils.random_vectors(200, 50) + 5.0  # every vector shares the direction (1, ..., 1)
    assert utils.mean_cosine(x) > 0.9
    assert abs(utils.mean_cosine(utils.center(x))) < 0.02


def test_random_vectors_are_reproducible():
    assert np.array_equal(utils.random_vectors(3, 4, seed=1), utils.random_vectors(3, 4, seed=1))


def test_verify_sha256_accepts_the_pinned_file_and_rejects_another(tmp_path):
    f = tmp_path / "x.bin"
    f.write_bytes(b"abc")
    assert utils.verify_sha256(f, hashlib.sha256(b"abc").hexdigest()) == b"abc"
    with pytest.raises(ValueError):
        utils.verify_sha256(f, hashlib.sha256(b"abd").hexdigest())
