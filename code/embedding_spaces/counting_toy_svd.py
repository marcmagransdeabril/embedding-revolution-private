"""From Counting to Geometry, question 1: truncated SVD of the PPMI matrix of the toy corpus (tbl-svd)."""
from utils import TOY_CORPUS, cooccurrence, cosine, ppmi, truncated_svd

vocab, counts = cooccurrence([line.split() for line in TOY_CORPUS], window=1)
index = {w: i for i, w in enumerate(vocab)}
pmi = ppmi(counts)
emb = truncated_svd(pmi, d=5)

PAIRS = [("dawn", "dusk"), ("king", "queen"), ("dawn", "king"), ("dawn", "xqzv")]
reps = {"PPMI": pmi, "SVD d=5": emb}
print(f"{'pair':14s}" + "".join(f"{name:>9s}" for name in reps))
cos = {}
for a, b in PAIRS:
    cos[a, b] = [cosine(m[index[a]], m[index[b]]) for m in reps.values()]
    print(f"{a + '-' + b:14s}" + "".join(f"{c:9.2f}" for c in cos[a, b]))

# `breaks` and `falls` share only the neighbour `over`: similar in the embeddings, not in the PPMI matrix.
ppmi_bf = cosine(pmi[index["breaks"]], pmi[index["falls"]])
svd_bf = cosine(emb[index["breaks"]], emb[index["falls"]])
print(f"cosine(breaks, falls): PPMI {ppmi_bf:.2f}, SVD d=5 {svd_bf:.2f}")

assert ppmi_bf < 0.4
# The rank reduction finds that `breaks` and `falls` share a neighbour (`over`), and with them dawn and dusk.
assert svd_bf > 0.99
assert cos["dawn", "dusk"][1] > 0.99 and cos["king", "queen"][1] > 0.99
assert abs(cos["dawn", "king"][1]) < 0.15 and abs(cos["dawn", "xqzv"][1]) < 0.05

# How the choice of d matters: too few dimensions merge unrelated words, too many keep every distinction.
print("\ncosine(dawn, dusk), cosine(dawn, king) for d = 1..8")
for d in range(1, 9):
    e = truncated_svd(pmi, d)
    print(d, round(cosine(e[index["dawn"]], e[index["dusk"]]), 2), round(cosine(e[index["dawn"]], e[index["king"]]), 2))
assert cosine(truncated_svd(pmi, 6)[index["dawn"]], truncated_svd(pmi, 6)[index["dusk"]]) < 0.6
