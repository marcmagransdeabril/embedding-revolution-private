"""Counting Company, question 1: co-occurrence counts and PPMI on the toy corpus (tbl-counting)."""
import numpy as np

from utils import TOY_CORPUS, cooccurrence, cosine, ppmi

vocab, counts = cooccurrence([line.split() for line in TOY_CORPUS], window=1)
index = {w: i for i, w in enumerate(vocab)}
pmi = ppmi(counts)

PAIRS = [("dawn", "dusk"), ("king", "queen"), ("dawn", "king"), ("dawn", "xqzv")]
reps = {"counts": counts, "PPMI": pmi}
print(f"{'pair':14s}" + "".join(f"{name:>9s}" for name in reps))
cos = {}
for a, b in PAIRS:
    cos[a, b] = [cosine(m[index[a]], m[index[b]]) for m in reps.values()]
    print(f"{a + '-' + b:14s}" + "".join(f"{c:9.2f}" for c in cos[a, b]))

# The rows of the two words of the first pair, and the total number of pairs N.
for w in ("dawn", "dusk"):
    print(w, {vocab[j]: int(counts[index[w], j]) for j in np.nonzero(counts[index[w]])[0]})
n = counts.sum()
print("N =", int(n), " PMI(dawn, breaks) =", round(float(np.log2(counts[index["dawn"], index["breaks"]] / n
      / (counts[index["dawn"]].sum() / n * counts[index["breaks"]].sum() / n))), 2),
      " PMI(dawn, the) =", round(float(np.log2(counts[index["dawn"], index["the"]] / n
      / (counts[index["dawn"]].sum() / n * counts[index["the"]].sum() / n))), 2))

# Raw counts are fooled by the frequent word `the`: dawn is closer to king than to dusk.
assert cos["dawn", "king"][0] > cos["dawn", "dusk"][0]
# PPMI removes the pull of `the` ...
assert cos["dawn", "king"][1] < 0.1
# ... but now dawn and dusk, which never stand next to the same informative word, look unrelated.
assert cos["dawn", "dusk"][1] < 0.1
