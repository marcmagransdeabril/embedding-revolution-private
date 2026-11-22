"""The three ways of building a word space from the same text that the chapter compares: counting (SVD of the PPMI matrix), predicting
(skip-gram with negative sampling, SGNS) and weighted least squares on the log counts (GloVe).

All of them take what `utils` builds (the indices of the words of the text and the symmetric co-occurrence counts), run on the CPU, and
return one vector per word. They are written to be read, not to be the fastest: the point is that the three losses see the same text,
the same vocabulary and the same window.
"""
from __future__ import annotations

import numpy as np
import torch
from scipy import sparse
from sklearn.utils.extmath import randomized_svd


def ppmi_svd(m: sparse.csr_matrix, d: int, seed: int, power: float = 0.5) -> np.ndarray:
    """Rows of U_d Sigma_d^power, the truncated SVD of the PPMI matrix (power 1 is the E = U_d Sigma_d of the text, 0.5 the usual choice)."""
    u, s, _ = randomized_svd(m, n_components=d, n_iter=5, random_state=seed)
    return (u * s ** power).astype(np.float32)


def skipgram_pairs(ids: np.ndarray, window: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """(center, context) pairs of a text of word indices, as in word2vec: each position draws a window size between 1 and `window`,
    so the nearer words are seen more often. Positions with index -1 (out-of-vocabulary or subsampled away) are removed first."""
    ids = ids[ids >= 0]
    size = rng.integers(1, window + 1, len(ids))
    centers, contexts = [], []
    for offset in range(1, window + 1):
        use = size[: len(ids) - offset] >= offset
        a, b = ids[:-offset][use], ids[offset:][use]
        centers += [a, b]
        contexts += [b, a]
    c, x = np.concatenate(centers), np.concatenate(contexts)
    order = rng.permutation(len(c))
    return c[order], x[order]


def subsample(ids: np.ndarray, counts: np.ndarray, t: float, rng: np.random.Generator) -> np.ndarray:
    """Drop each occurrence of word w with probability 1 - sqrt(t / f(w)) (the frequent words of the text are thinned out)."""
    freq = counts / counts.sum()
    keep_p = np.minimum(1.0, np.sqrt(t / freq))
    out = ids.copy()
    drop = (ids >= 0) & (rng.random(len(ids)) > keep_p[np.maximum(ids, 0)])
    out[drop] = -1
    return out


def sgns(ids: np.ndarray, counts: np.ndarray, d: int, seed: int, epochs: int = 3, window: int = 5, negatives: int = 5,
         batch: int = 16384, lr: float = 0.01, t: float = 1e-4) -> tuple[np.ndarray, np.ndarray]:
    """Skip-gram with negative sampling: -log sigma(e_w . v_c) - sum_i log sigma(-e_w . v_{c_i}) for k noise words drawn from the unigram
    distribution to the power 3/4, minimised with Adam. Returns the word vectors e_w and the context vectors v_c (two towers)."""
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    v = len(counts)
    emb = torch.nn.Parameter((torch.rand(v, d) - 0.5) / d)
    ctx = torch.nn.Parameter(torch.zeros(v, d))
    opt = torch.optim.Adam([emb, ctx], lr=lr)
    noise = torch.tensor(counts ** 0.75, dtype=torch.float)
    noise /= noise.sum()
    total = None
    step = 0
    for epoch in range(epochs):
        c, x = skipgram_pairs(subsample(ids, counts, t, rng), window, rng)
        if total is None:
            total = epochs * (len(c) // batch)
        for s in range(0, len(c) - batch + 1, batch):
            for g in opt.param_groups:
                g["lr"] = lr * max(0.01, 1 - step / total)
            w = torch.from_numpy(c[s: s + batch]).long()
            p = torch.from_numpy(x[s: s + batch]).long()
            n = torch.multinomial(noise, batch * negatives, replacement=True).view(batch, negatives)
            e = emb[w]
            pos = torch.nn.functional.logsigmoid((e * ctx[p]).sum(-1))
            neg = torch.nn.functional.logsigmoid(-torch.einsum("bd,bkd->bk", e, ctx[n])).sum(-1)
            loss = -(pos + neg).mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
            step += 1
    return emb.detach().numpy(), ctx.detach().numpy()


def glove(counts: sparse.csr_matrix, d: int, seed: int, epochs: int = 15, batch: int = 100_000, lr: float = 0.05,
          x_max: float = 100.0, alpha: float = 0.75) -> np.ndarray:
    """Weighted least squares on the log counts: sum f(C_wc) (e_w . v_c + b_w + b'_c - ln C_wc)^2 over the pairs that occur, with
    f(x) = min(1, (x / x_max)^alpha), minimised with Adam. Returns e_w + v_c, as the authors suggest."""
    torch.manual_seed(seed)
    coo = counts.tocoo()
    rows, cols = torch.from_numpy(coo.row).long(), torch.from_numpy(coo.col).long()
    x = torch.from_numpy(coo.data).float()
    weight = torch.clamp((x / x_max) ** alpha, max=1.0)
    target = torch.log(x)
    v = counts.shape[0]
    e = torch.nn.Parameter((torch.rand(v, d) - 0.5) / d)
    c = torch.nn.Parameter((torch.rand(v, d) - 0.5) / d)
    be, bc = torch.nn.Parameter(torch.zeros(v)), torch.nn.Parameter(torch.zeros(v))
    opt = torch.optim.Adam([e, c, be, bc], lr=lr)
    g = torch.Generator().manual_seed(seed)
    for _ in range(epochs):
        order = torch.randperm(len(x), generator=g)
        for s in range(0, len(x), batch):
            i = order[s: s + batch]
            r, k = rows[i], cols[i]
            err = (e[r] * c[k]).sum(-1) + be[r] + bc[k] - target[i]
            loss = (weight[i] * err ** 2).mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
    return (e + c).detach().numpy()
