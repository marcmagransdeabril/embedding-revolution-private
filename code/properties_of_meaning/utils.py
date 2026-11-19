"""Shared helpers for the scripts of Chapter 2 (properties of meaning): cosine, centring, the common-direction statistic and the pinned-file check.

Nothing is trained here. The scripts read pre-computed vectors; a file that is not in the repository is pinned by a SHA-256
that `verify_sha256` checks before use, and a mismatch stops the script.
"""
import hashlib
from pathlib import Path

import numpy as np


def unit(x: np.ndarray) -> np.ndarray:
    """Rows scaled to length 1 (a zero row stays zero)."""
    x = np.atleast_2d(np.asarray(x, dtype=float))
    n = np.linalg.norm(x, axis=1, keepdims=True)
    return np.divide(x, n, out=np.zeros_like(x), where=n > 0)


def cosine_matrix(x: np.ndarray, y: np.ndarray | None = None) -> np.ndarray:
    """Cosine similarity between every row of x and every row of y (of x with itself when y is None)."""
    u = unit(x)
    return u @ (u if y is None else unit(y)).T


def center(x: np.ndarray) -> np.ndarray:
    """Subtract the mean vector: the space seen from its centre, without the direction shared by all vectors."""
    x = np.asarray(x, dtype=float)
    return x - x.mean(axis=0, keepdims=True)


def mean_cosine(x: np.ndarray) -> float:
    """Mean cosine between distinct rows: 0 for an isotropic cloud, close to 1 when all vectors share a direction."""
    c = cosine_matrix(x)
    n = len(c)
    return float((c.sum() - np.trace(c)) / (n * (n - 1)))


def random_vectors(n: int, dim: int, seed: int = 0) -> np.ndarray:
    """The null space: n Gaussian vectors in dim dimensions, with a fixed seed."""
    return np.random.default_rng(seed).standard_normal((n, dim))


def verify_sha256(path: Path, expected: str) -> bytes:
    """Bytes of the file, if its SHA-256 is the pinned one; ValueError otherwise."""
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"{path} does not match the pinned SHA-256")
    return data
