"""From Counting to Geometry, question 1: co-occurrence counts, PPMI and truncated SVD on the toy corpus."""
import numpy as np

from utils import TOY_CORPUS, cooccurrence, cosine, ppmi, truncated_svd

vocab, counts = cooccurrence([line.split() for line in TOY_CORPUS], window=1)
index = {w: i for i, w in enumerate(vocab)}
pmi = ppmi(counts)
emb = truncated_svd(pmi, d=5)

PAIRS = [("dawn", "dusk"), ("king", "queen"), ("dawn", "king"), ("dawn", "xqzv")]
reps = {"counts": counts, "PPMI": pmi, "SVD d=5": emb}
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
# The rank reduction finds that `breaks` and `falls` share a neighbour (`over`), and with them dawn and dusk.
assert cosine(emb[index["breaks"]], emb[index["falls"]]) > 0.99
assert cos["dawn", "dusk"][2] > 0.99 and cos["king", "queen"][2] > 0.99
assert abs(cos["dawn", "king"][2]) < 0.15 and abs(cos["dawn", "xqzv"][2]) < 0.05

# How the choice of d matters: too few dimensions merge unrelated words, too many keep every distinction.
print("\ncosine(dawn, dusk), cosine(dawn, king) for d = 1..8")
for d in range(1, 9):
    e = truncated_svd(pmi, d)
    print(d, round(cosine(e[index["dawn"]], e[index["dusk"]]), 2), round(cosine(e[index["dawn"]], e[index["king"]]), 2))
assert cosine(truncated_svd(pmi, 6)[index["dawn"]], truncated_svd(pmi, 6)[index["dusk"]]) < 0.6
