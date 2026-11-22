"""Unit tests of the helpers of the introduction (code/symbols_without_interior/utils.py): each one is small and has a known answer."""
from __future__ import annotations

import importlib.util
from collections import Counter
from math import log2
from pathlib import Path

import numpy as np
import pytest

# Loaded under its own name: code/embedding_spaces/utils.py is also called `utils`.
_PATH = Path(__file__).resolve().parents[5] / "code" / "symbols_without_interior" / "utils.py"
_spec = importlib.util.spec_from_file_location("symbols_without_interior_utils", _PATH)
utils = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(utils)


def test_entropy_of_fair_coin_and_of_a_certain_outcome():
    assert utils.entropy(Counter("hhtt")) == pytest.approx(1.0)
    assert utils.entropy(Counter("hhhh")) == pytest.approx(0.0)


def test_entropy_of_uniform_distribution_is_log2_of_its_size():
    assert utils.entropy(Counter(range(8))) == pytest.approx(log2(8))


def test_distances_is_symmetric_with_zero_diagonal():
    d = utils.distances(np.array([[0.0, 0], [3, 4]]))
    assert np.allclose(d, d.T) and d[0, 1] == pytest.approx(5.0) and np.all(np.diag(d) == 0)


def test_load_book_checks_the_pinned_text():
    text = utils.load_book()
    assert "pride and prejudice" in text and text == text.lower()
