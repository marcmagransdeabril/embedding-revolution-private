"""Shared helpers for the solution scripts: cached Project Gutenberg download, Shannon entropy and a toy vocabulary."""
import tempfile
import urllib.request
from collections import Counter
from math import log2
from pathlib import Path

import numpy as np

URL = "https://www.gutenberg.org/cache/epub/1342/pg1342.txt"
PATH = Path(tempfile.gettempdir()) / "embedding_revolution" / "pride_and_prejudice.txt"


def load_book() -> str:
    """Lowercased book body (Gutenberg header and licence removed). Downloaded only if not cached in the temp dir."""
    if not PATH.exists():
        PATH.parent.mkdir(parents=True, exist_ok=True)
        part = PATH.with_suffix(".part")
        urllib.request.urlretrieve(URL, part)
        part.replace(PATH)  # atomic: an interrupted download never leaves a truncated book
    raw = PATH.read_text(encoding="utf-8-sig")
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
