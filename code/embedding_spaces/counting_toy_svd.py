"""From Counting to Geometry, question 1: truncated SVD of the PPMI matrix of the toy corpus (tbl-svd and tbl-patterns)."""
import numpy as np

from utils import TOY_CORPUS, cooccurrence, cosine, ppmi, truncated_svd

vocab, counts = cooccurrence([line.split() for line in TOY_CORPUS], window=1)
index = {w: i for i, w in enumerate(vocab)}
pmi = ppmi(counts)

PAIRS = [("dawn", "dusk"), ("king", "queen"), ("dawn", "king"), ("dawn", "xqzv"), ("breaks", "falls")]
DIMS = [2, 4, 5, 6, 8, 12]
# Rows of tbl-svd (PPMI, then SVD with each d), in the order of PAIRS.
TBL_SVD = {
    "PPMI": [0.04, 0.98, 0.05, 0.00, 0.33],
    2: [1.00, 1.00, 0.59, 0.00, 1.00],
    4: [1.00, 1.00, 0.09, 0.00, 1.00],
    5: [1.00, 1.00, 0.09, 0.00, 1.00],
    6: [0.48, 1.00, 0.09, 0.00, 0.68],
    8: [0.04, 1.00, 0.03, 0.00, 0.33],
    12: [0.04, 0.98, 0.05, 0.00, 0.33],
}

# tbl-svd: cosine of five pairs for the PPMI matrix and for the embeddings with increasing d.
print(f"{'':10s}" + "".join(f"{a + '-' + b:>14s}" for a, b in PAIRS))
rows = {"PPMI": [cosine(pmi[index[a]], pmi[index[b]]) for a, b in PAIRS]}
for d in DIMS:
    e = truncated_svd(pmi, d)
    # For d <= 4 the vector of `xqzv` is zero (up to rounding errors of 1e-16): the cosine is undefined, and we report 0.
    rows[d] = [0.0 if min(np.linalg.norm(e[index[a]]), np.linalg.norm(e[index[b]])) < 1e-8
               else cosine(e[index[a]], e[index[b]]) for a, b in PAIRS]
for name, row in rows.items():
    print(f"{str(name):10s}" + "".join(f"{c:14.2f}" for c in row))
    assert np.allclose(row, TBL_SVD[name], atol=0.005), (name, row)

# `breaks` and `falls` share only the neighbour `over`: similar in the embeddings, not in the PPMI matrix.
assert rows["PPMI"][4] < 0.4 and rows[5][4] > 0.99

# tbl-patterns: coordinates of eleven words along the first seven patterns (columns of U Sigma), and singular values.
u, s, _ = np.linalg.svd(pmi)
coords = u * s
WORDS = ["dawn", "dusk", "breaks", "falls", "over", "king", "queen", "wears", "rules", "xqzv", "jwk"]
print("\nword      " + "".join(f"{k:>7d}" for k in range(1, 8)))
for w in WORDS:
    print(f"{w:10s}" + "".join(f"{c:7.2f}" for c in coords[index[w], :7]))
print(f"{'sigma':10s}" + "".join(f"{x:7.2f}" for x in s[:7]))
print("sigma_8..12:", np.round(s[7:12], 2))

assert np.allclose(s[:12], [5.65, 5.19, 4.90, 4.84, 4.26, 3.49, 3.44, 3.30, 2.84, 2.51, 0.50, 0.50], atol=0.005)
# The sign of a whole column is arbitrary, so compare absolute values, and check the relative signs inside a column.
assert abs(coords[index["dawn"], 1] - 1.43) < 0.005 and abs(coords[index["falls"], 1] + 2.67) < 0.005
for k in (5, 6):  # dawn and dusk lean in opposite ways on the sixth and seventh patterns, as do breaks and falls
    assert coords[index["dawn"], k] * coords[index["dusk"], k] < 0
    assert coords[index["breaks"], k] * coords[index["falls"], k] < 0
assert np.allclose(coords[index["xqzv"], :4], 0, atol=1e-8) and abs(abs(coords[index["xqzv"], 4]) - 2.59) < 0.005

# Why d is a dial: too few dimensions merge unrelated words (dawn with king), too many keep every distinction (dawn from dusk).
assert rows[2][2] > 0.5 > rows[5][2] + 0.4 and rows[5][0] > 0.99 and rows[8][0] < 0.1
