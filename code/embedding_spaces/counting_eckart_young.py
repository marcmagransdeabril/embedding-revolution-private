"""From Counting to Geometry, question 3: the truncated SVD is the best rank-d approximation (Eckart-Young)."""
import numpy as np

from utils import TOY_CORPUS, cooccurrence, cosine, ppmi

vocab, counts = cooccurrence([line.split() for line in TOY_CORPUS], window=1)
index = {w: i for i, w in enumerate(vocab)}
pmi = ppmi(counts)
u, s, vt = np.linalg.svd(pmi)
rng = np.random.default_rng(0)

print(f"{'d':>2s} {'error':>7s} {'sqrt(sum of discarded s^2)':>27s} {'best of 1000 random':>20s} {'cos(dawn,dusk)':>15s}")
for d in range(1, 9):
    approx = (u[:, :d] * s[:d]) @ vt[:d]
    error = np.linalg.norm(pmi - approx)  # Frobenius norm
    assert np.isclose(error, np.sqrt(np.sum(s[d:] ** 2)))  # the error is the energy of the discarded singular values
    # Any other rank-d matrix does worse. Candidates: project the columns of PPMI onto 1,000 random d-dimensional subspaces.
    best_random = min(np.linalg.norm(pmi - q @ q.T @ pmi)
                      for q in (np.linalg.qr(rng.normal(size=(len(vocab), d)))[0] for _ in range(1000)))
    assert best_random > error
    emb = u[:, :d] * s[:d]
    print(f"{d:2d} {error:7.2f} {np.sqrt(np.sum(s[d:] ** 2)):27.2f} {best_random:20.2f} "
          f"{cosine(emb[index['dawn']], emb[index['dusk']]):15.2f}")

# The approximation is exact when d reaches the rank of the matrix.
rank = int(np.sum(s > 1e-10))
assert np.allclose((u[:, :rank] * s[:rank]) @ vt[:rank], pmi)
print("rank of PPMI:", rank, " singular values:", s[:rank].round(2))
