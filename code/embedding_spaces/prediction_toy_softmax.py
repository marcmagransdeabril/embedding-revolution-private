"""Learning by Prediction, question 3: softmax predictor on the toy corpus, trained on the cross-entropy over all pairs."""
import numpy as np
import torch
import torch.nn.functional as F

from utils import TOY_CORPUS, cooccurrence, cosine, ppmi, truncated_svd

D, STEPS = 5, 30_000
vocab, counts = cooccurrence([line.split() for line in TOY_CORPUS], window=1)
index = {w: i for i, w in enumerate(vocab)}
n = counts.sum()
C = torch.tensor(counts)
P_COND = counts / counts.sum(1, keepdims=True)  # true conditional probability P(c | w)
H_COND = -(counts / n * np.log(np.where(counts > 0, P_COND, 1))).sum()  # conditional entropy H(C | W) in nats


def loss(e: torch.Tensor, v: torch.Tensor) -> torch.Tensor:
    """Cross-entropy of the softmax predictor, summed over all the pairs of the corpus (nats)."""
    return -(C * F.log_softmax(e @ v.T, dim=1)).sum()


def train(seed: int) -> tuple[np.ndarray, np.ndarray]:
    torch.manual_seed(seed)
    e = (0.1 * torch.randn(len(vocab), D, dtype=torch.float64)).requires_grad_()
    v = (0.1 * torch.randn(len(vocab), D, dtype=torch.float64)).requires_grad_()
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


svd = truncated_svd(ppmi(counts), D)
print(f"H(C|W) = {H_COND:.4f} nats per pair")
print(f"SVD d=5: dawn-dusk {cos(svd, 'dawn', 'dusk'):.2f}, king-queen {cos(svd, 'king', 'queen'):.2f}")

losses, dawn_dusk, king_queen = [], [], []
for seed in range(5):
    e, v = train(seed)
    pair_loss = loss(torch.tensor(e), torch.tensor(v)).item() / n
    losses.append(pair_loss)
    dawn_dusk.append(cos(e, "dawn", "dusk"))
    king_queen.append(cos(e, "king", "queen"))
    t = lambda c: np.log(P_COND[index["dawn"], index[c]])  # noqa: E731 - true ln P(c | dawn)
    print(f"seed {seed}: loss/pair {pair_loss:.4f}  "
          f"ln Q(breaks|dawn) {log_q(e, v, 'dawn', 'breaks'):.2f} (ln P = {t('breaks'):.2f})  "
          f"ln Q(the|dawn) {log_q(e, v, 'dawn', 'the'):.2f} (ln P = {t('the'):.2f})  "
          f"ln Q(king|dawn) {log_q(e, v, 'dawn', 'king'):.1f}  "
          f"cos dawn-dusk {dawn_dusk[-1]:.2f}  cos king-queen {king_queen[-1]:.2f}")
    # The observed pairs reach the true probabilities; the unseen pair dawn-king is pushed far below.
    assert abs(log_q(e, v, "dawn", "breaks") - t("breaks")) < 0.05
    assert abs(log_q(e, v, "dawn", "the") - t("the")) < 0.05
    assert log_q(e, v, "dawn", "king") < -5

# The loss reaches the conditional entropy, the bound of the first section, in every run.
assert max(losses) - H_COND < 1e-2
assert max(losses) - min(losses) < 1e-3
assert min(king_queen) > 0.95
assert max(dawn_dusk) - min(dawn_dusk) > 0.1

# An invertible change of basis, E -> E A and V -> V A^{-T}, leaves every score and the loss unchanged.
a = np.diag([1.0, 2.0, 3.0, 4.0, 5.0])
e2, v2 = e @ a, v @ np.linalg.inv(a).T
loss2 = loss(torch.tensor(e2), torch.tensor(v2)).item() / n
print(f"after E -> E A: loss/pair {loss2:.4f}, cos dawn-dusk {cos(e2, 'dawn', 'dusk'):.2f}, "
      f"cos king-queen {cos(e2, 'king', 'queen'):.2f}")
assert np.allclose(e @ v.T, e2 @ v2.T)
assert abs(loss2 - losses[-1]) < 1e-9
assert abs(cos(e2, "dawn", "dusk") - dawn_dusk[-1]) > 0.05
