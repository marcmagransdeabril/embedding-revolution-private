"""From Counting to Geometry, question 2: PPMI + truncated SVD embeddings of the 2,000 most frequent words of a novel."""
import re
from collections import Counter

import numpy as np

from utils import load_book, ppmi

V, WINDOW, D = 2000, 2, 30
words = re.findall(r"[a-z']+", load_book())
vocab = [w for w, _ in Counter(words).most_common(V)]
index = {w: i for i, w in enumerate(vocab)}
ids = np.array([index.get(w, -1) for w in words])  # -1 for the words outside the vocabulary

counts = np.zeros((V, V))
for k in range(1, WINDOW + 1):  # pairs at distance k, in both directions
    a, b = ids[:-k], ids[k:]
    keep = (a >= 0) & (b >= 0)
    np.add.at(counts, (a[keep], b[keep]), 1)
    np.add.at(counts, (b[keep], a[keep]), 1)

pmi = ppmi(counts)
u, s, _ = np.linalg.svd(pmi)


def neighbours(m: np.ndarray, word: str, k: int = 8) -> list[str]:
    """The k words whose rows have the highest cosine similarity with the row of `word`."""
    unit = m / np.maximum(np.linalg.norm(m, axis=1, keepdims=True), 1e-12)
    sim = unit @ unit[index[word]]
    return [vocab[i] for i in np.argsort(-sim)[1:k + 1]]


emb = u[:, :D] * s[:D]
for w in ("sister", "morning", "darcy", "london"):
    print(f"{w:8s} counts: {neighbours(counts, w, 5)}\n{'':8s} PPMI:   {neighbours(pmi, w, 5)}\n{'':8s} SVD:    {neighbours(emb, w)}")

assert len({"father", "mother", "daughter", "aunt", "uncle", "cousin", "brother"} & set(neighbours(emb, "sister"))) >= 3
assert {"day", "evening"} <= set(neighbours(emb, "morning"))
assert {"bingley", "bennet"} <= set(neighbours(emb, "darcy"))
