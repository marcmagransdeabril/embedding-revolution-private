"""Learning by Prediction, question 3: SGNS on the toy corpus, trained on the expected loss over all pairs."""
import numpy as np
import torch
import torch.nn.functional as F

from utils import TOY_CORPUS, cooccurrence, cosine, ppmi, truncated_svd

K, D, STEPS = 2, 5, 30_000
vocab, counts = cooccurrence([line.split() for line in TOY_CORPUS], window=1)
index = {w: i for i, w in enumerate(vocab)}
n = counts.sum()
p_w = counts.sum(1) / n  # the matrix is symmetric, so this is also P(c)
C = torch.tensor(counts)
NOISE = torch.tensor(K * np.outer(counts.sum(1), p_w))  # expected noise count k * C_w * P(c) of each pair


def loss(e: torch.Tensor, u: torch.Tensor) -> torch.Tensor:
    x = e @ u.T
    return -(C * F.logsigmoid(x)).sum() - (NOISE * F.logsigmoid(-x)).sum()


def train(seed: int) -> tuple[np.ndarray, np.ndarray]:
    torch.manual_seed(seed)
    e = (0.1 * torch.randn(len(vocab), D, dtype=torch.float64)).requires_grad_()
    u = (0.1 * torch.randn(len(vocab), D, dtype=torch.float64)).requires_grad_()
    opt = torch.optim.Adam([e, u], lr=0.01)
    for _ in range(STEPS):
        opt.zero_grad()
        loss(e, u).backward()
        opt.step()
    return e.detach().numpy(), u.detach().numpy()


def cos(e: np.ndarray, a: str, b: str) -> float:
    return cosine(e[index[a]], e[index[b]])


with np.errstate(divide="ignore"):
    target = np.log(counts / n / np.outer(p_w, p_w)) - np.log(K)  # PMI - ln k, in nats
svd = truncated_svd(ppmi(counts), D)
print(f"SVD d=5: dawn-dusk {cos(svd, 'dawn', 'dusk'):.2f}, king-queen {cos(svd, 'king', 'queen'):.2f}")

losses, dawn_dusk, king_queen = [], [], []
for seed in range(5):
    e, u = train(seed)
    x = e @ u.T
    pair_loss = loss(torch.tensor(e), torch.tensor(u)).item() / n
    losses.append(pair_loss)
    dawn_dusk.append(cos(e, "dawn", "dusk"))
    king_queen.append(cos(e, "king", "queen"))
    print(f"seed {seed}: loss/pair {pair_loss:.4f}  "
          f"dawn.breaks {x[index['dawn'], index['breaks']]:.2f} (PMI - ln k = {target[index['dawn'], index['breaks']]:.2f})  "
          f"dawn.the {x[index['dawn'], index['the']]:.2f} (PMI - ln k = {target[index['dawn'], index['the']]:.2f})  "
          f"dawn.king {x[index['dawn'], index['king']]:.1f}  "
          f"cos dawn-dusk {dawn_dusk[-1]:.2f}  cos king-queen {king_queen[-1]:.2f}")
    # Observed pairs reach the shifted PMI; the unseen pair dawn-king is pushed far below zero.
    assert abs(x[index["dawn"], index["breaks"]] - target[index["dawn"], index["breaks"]]) < 0.05
    assert abs(x[index["dawn"], index["the"]] - target[index["dawn"], index["the"]]) < 0.05
    assert x[index["dawn"], index["king"]] < -5

# Same loss in every run, different cosines: the data fix the scores E U^T, not the word vectors E.
assert max(losses) - min(losses) < 1e-3
assert min(king_queen) > 0.97
assert max(dawn_dusk) - min(dawn_dusk) > 0.1

# An invertible change of basis, E -> E A and U -> U A^{-T}, leaves every score and the loss unchanged.
a = np.diag([1.0, 2.0, 3.0, 4.0, 5.0])
e2, u2 = e @ a, u @ np.linalg.inv(a).T
loss2 = loss(torch.tensor(e2), torch.tensor(u2)).item() / n
print(f"after E -> E A: loss/pair {loss2:.4f}, cos dawn-dusk {cos(e2, 'dawn', 'dusk'):.2f}, "
      f"cos king-queen {cos(e2, 'king', 'queen'):.2f}")
assert np.allclose(e @ u.T, e2 @ u2.T)
assert abs(loss2 - losses[-1]) < 1e-9
assert abs(cos(e2, "dawn", "dusk") - dawn_dusk[-1]) > 0.05
