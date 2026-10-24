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


# Toy corpus of the Counting to Geometry section: one sentence per line, no punctuation. `xqzv` and `jwk`
# occur only next to each other, so they carry no information about any other word.
TOY_CORPUS = """the dawn breaks over the hills
the dusk falls over the hills
the dawn breaks over the sea
the dusk falls over the sea
the dawn breaks over the sea
the king wears the crown
the queen wears the crown
the king rules the land
the queen rules the land
the king rules the land
the xqzv jwk
the jwk xqzv jwk
the xqzv jwk jwk xqzv""".split("\n")


def cooccurrence(sentences: list[list[str]], window: int = 1) -> tuple[list[str], np.ndarray]:
    """Vocabulary (sorted) and symmetric matrix C with C[w, c] = number of times c lies within `window`
    words of w, inside the same sentence."""
    vocab = sorted({w for s in sentences for w in s})
    index = {w: i for i, w in enumerate(vocab)}
    counts = np.zeros((len(vocab), len(vocab)))
    for s in sentences:
        for i, w in enumerate(s):
            for j in range(max(0, i - window), min(len(s), i + window + 1)):
                if j != i:
                    counts[index[w], index[s[j]]] += 1
    return vocab, counts


def ppmi(counts: np.ndarray, alpha: float = 1.0) -> np.ndarray:
    """Positive pointwise mutual information in bits, max(0, log2 P(w,c) / (P(w) P_alpha(c))).
    alpha < 1 smooths the context distribution P_alpha(c) ~ count(c)^alpha, which lowers the bonus
    that very rare contexts get."""
    total = counts.sum()
    p_w = counts.sum(1) / total
    p_c = counts.sum(0) ** alpha
    p_c = p_c / p_c.sum()
    with np.errstate(divide="ignore", invalid="ignore"):
        pmi = np.log2(counts / total / np.outer(p_w, p_c))
    return np.where(counts > 0, np.maximum(pmi, 0), 0)  # unseen pairs (PMI = -inf) and negative PMI become 0


def truncated_svd(m: np.ndarray, d: int) -> np.ndarray:
    """Rows of U_d Sigma_d (powers of Sigma: see the exercises): the d-dimensional embeddings of the rows of m."""
    u, s, _ = np.linalg.svd(m)
    return u[:, :d] * s[:d]


def cosine(u: np.ndarray, v: np.ndarray) -> float:
    """Cosine of the angle between u and v (0 if one of them is the zero vector)."""
    n = np.linalg.norm(u) * np.linalg.norm(v)
    return float(u @ v / n) if n else 0.0
