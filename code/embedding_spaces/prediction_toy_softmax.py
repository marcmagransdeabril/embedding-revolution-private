"""Learning by Prediction, question 3: softmax predictor on the toy corpus, trained on the cross-entropy over all pairs,
for several dimensions d and several seeds, with the analogues of tbl-svd and tbl-patterns."""
import numpy as np
import torch
import torch.nn.functional as F

from utils import TOY_CORPUS, cooccurrence, cosine, ppmi, truncated_svd

DIMS, SEEDS, STEPS = [2, 4, 5, 6, 8, 12], range(5), 30_000
vocab, counts = cooccurrence([line.split() for line in TOY_CORPUS], window=1)
index = {w: i for i, w in enumerate(vocab)}
n = counts.sum()
C = torch.tensor(counts)
P_COND = counts / counts.sum(1, keepdims=True)  # true conditional probability P(c | w)
H_COND = -(counts / n * np.log(np.where(counts > 0, P_COND, 1))).sum()  # conditional entropy H(C | W) in nats
PAIRS = [("dawn", "dusk"), ("king", "queen"), ("dawn", "king"), ("dawn", "xqzv"), ("breaks", "falls")]


def loss(e: torch.Tensor, v: torch.Tensor) -> torch.Tensor:
    """Cross-entropy of the softmax predictor, summed over all the pairs of the corpus (nats)."""
    return -(C * F.log_softmax(e @ v.T, dim=1)).sum()


def train(seed: int, d: int) -> tuple[np.ndarray, np.ndarray]:
    torch.manual_seed(seed)
    e = (0.1 * torch.randn(len(vocab), d, dtype=torch.float64)).requires_grad_()
    v = (0.1 * torch.randn(len(vocab), d, dtype=torch.float64)).requires_grad_()
    opt = torch.optim.Adam([e, v], lr=0.01)
    for _ in range(STEPS):
        opt.zero_grad()
        loss(e, v).backward()
        opt.step()
    return e.detach().numpy(), v.detach().numpy()


def cos(e: np.ndarray, a: str, b: str) -> float:
    return cosine(e[index[a]], e[index[b]])


def log_q(e: np.ndarray, v: np.ndarray, w: str, c: str) -> float:
    """ln Q(c | w) of the trained predictor."""
    x = e[index[w]] @ v.T
    return float(x[index[c]] - np.logaddexp.reduce(x))


print(f"H(C|W) = {H_COND:.4f} nats per pair\n")
svd_row = {d: [cos(truncated_svd(ppmi(counts), d), a, b) for a, b in PAIRS] for d in DIMS}
runs = {}  # d -> list of (e, v), one per seed
summary = {}
print("cosines of the pairs of tbl-svd, mean [min, max] over the seeds; the SVD value in parentheses")
print(f"{'d':>3s} {'loss':>8s} {'ln Q(king|dawn)':>17s} " + " ".join(f"{a + '-' + b:>26s}" for a, b in PAIRS))
for d in DIMS:
    runs[d] = [train(seed, d) for seed in SEEDS]
    losses = [loss(torch.tensor(e), torch.tensor(v)).item() / n for e, v in runs[d]]
    unseen = [log_q(e, v, "dawn", "king") for e, v in runs[d]]
    cosines = np.array([[cos(e, a, b) for a, b in PAIRS] for e, _ in runs[d]])
    summary[d] = (losses, cosines, unseen)
    cells = " ".join(f"{c.mean():6.2f} [{c.min():5.2f},{c.max():5.2f}] ({s:5.2f})" for c, s in zip(cosines.T, svd_row[d]))
    print(f"{d:3d} {np.mean(losses):8.4f} {min(unseen):7.1f} to {max(unseen):6.1f} {cells}")

# tbl-patterns, learned version: the coordinates of the words in E (d = 5, first seed), and the same space seen through SVD.
e5, v5 = runs[5][0]
WORDS = ["dawn", "dusk", "breaks", "falls", "over", "king", "queen", "wears", "rules", "xqzv", "jwk"]
print("\ncoordinates of E (d = 5, seed 0)")
for w in WORDS:
    print(f"{w:8s}" + "".join(f"{c:7.2f}" for c in e5[index[w]]))

# Whatever the dimension, the loss reaches H(C|W) once the predictor is rich enough, and not before.
assert min(summary[2][0]) - H_COND > 0.03
for d in DIMS[1:]:
    assert max(summary[d][0]) - H_COND < 1e-2
    assert max(summary[d][0]) - min(summary[d][0]) < 1e-3
    assert max(summary[d][2]) < -5  # the unseen pair dawn-king is pushed far below
# The observed pairs reach the true probabilities for d = 5; the dimension and the seed do not change that.
for e, v in runs[5]:
    for c in ("breaks", "the"):
        assert abs(log_q(e, v, "dawn", c) - np.log(P_COND[index["dawn"], index[c]])) < 0.05
# king and queen share every neighbour, so they stay together for every d and seed; dawn and dusk do not.
assert all(summary[d][1][:, 1].min() > 0.9 for d in DIMS)
assert summary[5][1][:, 0].max() - summary[5][1][:, 0].min() > 0.1

# An invertible change of basis, E -> E A and V -> V A^{-T}, leaves every score and the loss unchanged.
e, v = runs[5][-1]
a = np.diag([1.0, 2.0, 3.0, 4.0, 5.0])
e2, v2 = e @ a, v @ np.linalg.inv(a).T
loss2 = loss(torch.tensor(e2), torch.tensor(v2)).item() / n
print(f"\nafter E -> E A: loss/pair {loss2:.4f}, cos dawn-dusk {cos(e2, 'dawn', 'dusk'):.2f} (before {cos(e, 'dawn', 'dusk'):.2f}), "
      f"cos king-queen {cos(e2, 'king', 'queen'):.2f}")
assert np.allclose(e @ v.T, e2 @ v2.T)
assert abs(loss2 - summary[5][0][-1]) < 1e-9
assert abs(cos(e2, "dawn", "dusk") - cos(e, "dawn", "dusk")) > 0.05
