"""Shared helpers for the scripts of the introduction (symbols without interior): the pinned Project Gutenberg text, Shannon entropy
and the toy vocabulary of the one-hot table."""
import hashlib
import zipfile
from collections import Counter
from math import log2
from pathlib import Path

import numpy as np

# The numbers in the book (entropies, word counts, nearest neighbours) are computed on this exact text, so it is
# kept in the repository instead of being downloaded. Source: https://www.gutenberg.org/cache/epub/1342/pg1342.txt,
# retrieved 2026-11-10 (identical to the copy used since 2026-11-05). Public domain, with the Project Gutenberg
# header and licence left intact.
BOOK_ZIP = Path(__file__).parent / "data" / "pride_and_prejudice.zip"
BOOK_NAME = "pg1342.txt"
BOOK_SHA256 = "3f6bb9d6f78e0293b56acd4714dd68cb7d6d1d293402031ce9d5a216bcaf9d75"


def load_book() -> str:
    """Lowercased book body (Gutenberg header and licence removed), read from the pinned zip."""
    with zipfile.ZipFile(BOOK_ZIP) as z:
        data = z.read(BOOK_NAME)
    if hashlib.sha256(data).hexdigest() != BOOK_SHA256:
        raise ValueError(f"{BOOK_ZIP} does not contain the pinned text (sha256 mismatch)")
    raw = data.decode("utf-8-sig")
    body = raw.split("*** START OF", 1)[1].split("***", 1)[1].split("*** END OF", 1)[0]
    return body.lower()


def entropy(counts: Counter) -> float:
    """Shannon entropy in bits of the empirical distribution given by `counts`."""
    n = sum(counts.values())
    return -sum(c / n * log2(c / n) for c in counts.values())


def sample(counts: Counter, k: int, rng: np.random.Generator | None = None) -> list:
    """k i.i.d. draws from the empirical distribution p_i = count_i / total."""
    rng = rng or np.random.default_rng(0)
    symbols = list(counts)
    p = np.array([counts[s] for s in symbols]) / sum(counts.values())
    return rng.choice(symbols, size=k, p=p).tolist()


# Toy vocabulary of the Orthogonal Catastrophe section, in the order of the one-hot table.
WORDS = ["dawn", "dusk", "king", "queen", "xqzv"]
# Hand-made dense vectors (illustrative values, not learned), one row per word. The features are
# time of day, person, royal, male and brightness; the meaningless `xqzv` gets a small noise vector.
DENSE = np.array([
    [1, 0, 0, 0.0, 0.4],  # dawn
    [1, 0, 0, 0.0, -0.4],  # dusk
    [0, 1, 1, 0.5, 0.0],  # king
    [0, 1, 1, -0.5, 0.0],  # queen
    [0.2, -0.3, 0.1, 0.3, -0.1],  # xqzv
])


def distances(x: np.ndarray) -> np.ndarray:
    """Matrix of Euclidean distances between the rows of x."""
    return np.linalg.norm(x[:, None, :] - x[None, :, :], axis=-1)
