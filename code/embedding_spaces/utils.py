"""Shared helpers for the solution scripts: cached Project Gutenberg download and Shannon entropy."""
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
