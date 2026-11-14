"""Learning by Contrast: Words, question 3: noise-contrastive estimation on the toy corpus of Learning by Prediction.

The same corpus, the same pairs, the same 1,000,000 iterations of plain stochastic gradient descent (one sentence per iteration, a step
size that decreases linearly from 0.1 to 0) and the same five seeds as prediction_toy_softmax.py, which is imported and not copied. The
softmax predictor is trained there, with d = 5. Here the contrastive model is trained with d = 5 coordinates and one learned constant
a_w per word (the extra coordinate of the text), K = 5 noise neighbours per pair drawn with the frequency of the neighbour, and the loss
of the text, -ln sigma(lam_c) - sum_i ln(1 - sigma(lam_i)) with lam = <e_w, v_c> + a_w - ln(K P_n(c)).

Both models are judged by the same number: the cross-entropy of the softmax of their scores over the whole vocabulary, in bits per
pair, which the contrastive model never computes while training. For the contrastive model we also report how far its scores are from
a normalized distribution, log2 of the sum of the exponentials of the scores of each word (zero if self-normalized).

Printed: the loss curves, the final losses, the PMI matrices of the two models against the PPMI, the effect of K on the final loss, and
the cost of one step against the size of the vocabulary. Saves the two figures used in the chapter to
../../figures/embedding_spaces/contrast_toy_loss.png and contrast_toy_pmi.png. Every band and interval is the 95% percentile bootstrap
interval of the mean over the seeds.
"""
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from time import perf_counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm

from prediction_toy_softmax import (H_COND, ITERATIONS, LEARNING_RATE, LN2, SEEDS, SENTENCE_PAIRS, SENTENCES, counts, index,
                                    log_softmax, n, sgd_step, train_curve, vocab)
from utils import bootstrap_interval, ppmi

D, K, KS = 5, 5, [1, 5, 25]  # dimension, noise neighbours per pair, and the values of K of the last table
FIGURES = Path("../../figures/embedding_spaces")
CHECKPOINTS = tuple(sorted({int(round(t)) for t in np.logspace(1, np.log10(ITERATIONS), 31)}))
ORDER = ["dawn", "dusk", "breaks", "falls", "over", "hills", "sea",  # the sky
         "king", "queen", "wears", "rules", "crown", "land",  # the court
         "the", "xqzv", "jwk"]
GROUP_ENDS = [7, 13, 14]
assert sorted(ORDER) == sorted(vocab)
perm = [index[w] for w in ORDER]
p_c = counts.sum(0) / n  # the frequency of the neighbour: the noise distribution P_n
p_w = counts.sum(1) / n
cdf = np.cumsum(p_c)
seen = counts > 0


def sigmoid(t: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-t))


def nce_step(e: np.ndarray, v: np.ndarray, a: np.ndarray, words: np.ndarray, neighbours: np.ndarray, noise: np.ndarray,
             log_kpn: np.ndarray, eta: float) -> None:
    """One step against the gradient of the summed NCE loss of the pairs. `noise` holds K noise neighbours per pair, and column 0
    of the candidates is the real one. Only the K + 1 rows of v of each pair change, not the whole vocabulary."""
    cand = np.concatenate([neighbours[:, None], noise], axis=1)  # (pairs, K + 1)
    e_w, v_c = e[words], v[cand]
    lam = np.einsum("pd,pkd->pk", e_w, v_c) + a[words][:, None] - log_kpn[cand]  # the log-odds lambda of the text
    g = sigmoid(lam)
    g[:, 0] -= 1  # sigma(lambda) - label
    np.add.at(e, words, -eta * np.einsum("pk,pkd->pd", g, v_c))  # dl/de_w = (sigma(lam_c) - 1) v_c + sum_i sigma(lam_i) v_i
    np.add.at(v, cand, -eta * g[:, :, None] * e_w[:, None, :])  # dl/dv = (sigma(lam) - label) e_w
    np.add.at(a, words, -eta * g.sum(1))  # the constant a_w is the coordinate of e_w that multiplies a 1 in v


def scores(e: np.ndarray, v: np.ndarray, a: np.ndarray) -> np.ndarray:
    return e @ v.T + a[:, None]


def softmax_loss(s: np.ndarray) -> float:
    """Cross-entropy of the softmax of the scores s over the whole vocabulary, in bits per pair of the corpus."""
    return float(-(counts * log_softmax(s)).sum() / n / LN2)


def log2_normalizer(s: np.ndarray) -> float:
    """Mean over the words (weighted by their frequency) of |log2 sum_c exp(s_wc)|: zero if the scores are self-normalized."""
    return float(np.sum(p_w * np.abs(np.log(np.exp(s).sum(1))) / LN2))


def train_nce(args: tuple[int, int]):
    """NCE with K noise neighbours per pair. Returns the vectors and, at each checkpoint, (loss, normalizer) as above."""
    seed, k = args
    rng = np.random.default_rng(seed)
    e = 0.1 * rng.standard_normal((len(vocab), D))
    v = 0.1 * rng.standard_normal((len(vocab), D))
    a = np.zeros(len(vocab))
    log_kpn = np.log(k * p_c)
    curve = []
    for t, s in enumerate(rng.integers(len(SENTENCES), size=ITERATIONS), start=1):
        words, neighbours = SENTENCE_PAIRS[s]
        noise = np.minimum(np.searchsorted(cdf, rng.random((len(words), k)), side="right"), len(vocab) - 1)
        nce_step(e, v, a, words, neighbours, noise, log_kpn, LEARNING_RATE * (1 - (t - 1) / ITERATIONS))
        if t in CHECKPOINTS:
            sc = scores(e, v, a)
            curve.append((softmax_loss(sc), log2_normalizer(sc)))
    return e, v, a, np.array(curve)


def train_softmax(seed: int):
    e, v, curve = train_curve(seed, D, CHECKPOINTS)
    return e, v, np.array(curve) / LN2


def pmi_bits(s: np.ndarray) -> np.ndarray:
    """log2 (exp(s) / P(c)) of the scores s: the PMI of the pair if exp(s) is Q(c | w)."""
    return (s - np.log(p_c)) / LN2


def step_times(sizes=(10**3, 10**4, 10**5), pairs: int = 10, repeats: int = 30) -> dict:
    """Microseconds for one step on `pairs` pairs with a vocabulary of the given size (random vectors, d = D, K noise words)."""
    out = {}
    for size in sizes:
        rng = np.random.default_rng(0)
        e, v, a = 0.1 * rng.standard_normal((size, D)), 0.1 * rng.standard_normal((size, D)), np.zeros(size)
        words, neighbours = rng.integers(size, size=pairs), rng.integers(size, size=pairs)
        noise, log_kpn = rng.integers(size, size=(pairs, K)), np.full(size, np.log(K / size))
        t0 = perf_counter()
        for _ in range(repeats):
            sgd_step(e, v, words, neighbours, 1e-3)
        t1 = perf_counter()
        for _ in range(repeats):
            nce_step(e, v, a, words, neighbours, noise, log_kpn, 1e-3)
        t2 = perf_counter()
        out[size] = ((t1 - t0) / repeats * 1e6, (t2 - t1) / repeats * 1e6)
    return out


if __name__ == "__main__":
    print(f"H(C|W) = {H_COND / LN2:.4f} bits per pair; {ITERATIONS:,} iterations, eta from {LEARNING_RATE} to 0, d = {D}, "
          f"K = {K}, noise = frequency of the neighbour, {len(SEEDS)} seeds\n")
    with ProcessPoolExecutor() as pool:
        soft_jobs = [pool.submit(train_softmax, s) for s in SEEDS]
        nce_jobs = {k: [pool.submit(train_nce, (s, k)) for s in SEEDS] for k in KS}
        soft = [j.result() for j in soft_jobs]
        nce = {k: [j.result() for j in jobs] for k, jobs in nce_jobs.items()}
    soft_curve = np.array([c for _, _, c in soft])  # (seeds, checkpoints)
    nce_curve = np.array([c for _, _, _, c in nce[K]])  # (seeds, checkpoints, 2)

    # The loss curves, mean and 95% interval over the seeds.
    t = np.array(CHECKPOINTS)
    soft_mean, soft_low, soft_high = bootstrap_interval(soft_curve)
    loss_mean, loss_low, loss_high = bootstrap_interval(nce_curve[:, :, 0])
    norm_mean, norm_low, norm_high = bootstrap_interval(nce_curve[:, :, 1])
    print("loss (bits per pair) of the softmax over the whole vocabulary, mean [95% interval] over the seeds")
    print(f"{'iterations':>10} {'prediction':>24} {'contrast':>24} {'|log2 Z| contrast':>22}")
    for i in sorted({*range(0, len(t), 3), len(t) - 1}):
        print(f"{t[i]:>10,} {soft_mean[i]:>8.4f} [{soft_low[i]:.4f}, {soft_high[i]:.4f}] "
              f"{loss_mean[i]:>8.4f} [{loss_low[i]:.4f}, {loss_high[i]:.4f}] {norm_mean[i]:>8.4f} [{norm_low[i]:.4f}, {norm_high[i]:.4f}]")
    plateau = (t >= 10**3) & (t <= 3 * 10**5)  # while the step size is still large
    print(f"mean over the checkpoints between 10^3 and 3 x 10^5 iterations: prediction {soft_mean[plateau].mean():.3f}, "
          f"contrast {loss_mean[plateau].mean():.3f} bits; mean width of the 95% interval {np.mean(soft_high[plateau] - soft_low[plateau]):.3f} "
          f"and {np.mean(loss_high[plateau] - loss_low[plateau]):.3f} bits")

    # The final loss against K: the same optimum, a different noise around it.
    print(f"\nfinal loss against K (bits per pair, mean [95% interval] over the seeds; softmax {soft_mean[-1]:.4f}, floor "
          f"{H_COND / LN2:.4f}), and the normalization |log2 Z| of the scores at the end")
    at_1e4 = int(np.argmax(t >= 10**4))
    for k in KS:
        c = np.array([run[3] for run in nce[k]])
        m, lo, hi = bootstrap_interval(c[:, -1, 0])
        z, zlo, zhi = bootstrap_interval(c[:, -1, 1])
        m4, lo4, hi4 = bootstrap_interval(c[:, at_1e4, 0])
        print(f"K = {k:>2}: {m:.4f} [{lo:.4f}, {hi:.4f}]   |log2 Z| {z:.4f} [{zlo:.4f}, {zhi:.4f}]   rows of V per pair {k + 1}   "
              f"loss at {t[at_1e4]:,} iterations {m4:.4f} [{lo4:.4f}, {hi4:.4f}]")

    # The PMI matrices (clipped at 0, like the PPMI): mean and width of the 95% interval over the seeds.
    soft_pmi = np.array([np.maximum(0, (log_softmax(e @ v.T) - np.log(p_c)) / LN2) for e, v, _ in soft])
    nce_raw = np.array([pmi_bits(scores(e, v, a)) for e, v, a, _ in nce[K]])
    nce_pmi = np.maximum(0, nce_raw)
    ppmi_matrix = ppmi(counts)
    summary = {}
    for name, stack in (("prediction", soft_pmi), ("contrast", nce_pmi)):
        mean, low, high = bootstrap_interval(stack)
        error = [float(np.linalg.norm(m - ppmi_matrix)) for m in stack]
        worst = [float(np.abs(m - ppmi_matrix)[seen].max()) for m in stack]
        summary[name] = (mean, high - low)
        widest = np.dstack(np.unravel_index(np.argsort(-(high - low).ravel())[:3], high.shape))[0]
        print(f"\n{name}: Frobenius error to the PPMI matrix {np.mean(error):.2f} [{min(error):.2f}, {max(error):.2f}] over the seeds; "
              f"largest difference on an observed pair {max(worst):.2f} bits; width of the interval of the mean: "
              f"mean over cells {(high - low).mean():.3f}, largest {(high - low).max():.3f} bits, at "
              + ", ".join(f"{vocab[i]}-{vocab[j]} {(high - low)[i, j]:.3f}" for i, j in widest))
    print(f"contrast, unseen pairs (unclipped): from {nce_raw[:, ~seen].min():.1f} to {nce_raw[:, ~seen].max():.1f} bits")

    # The cost of one step with the vocabulary.
    print("\nmicroseconds per step on 10 pairs (numpy, one thread), softmax against NCE with K = 5, and the rows of V that change")
    for size, (us_soft, us_nce) in step_times().items():
        print(f"|V| = {size:>7,}: softmax {us_soft:9.1f}  (rows changed {size:>7,})   NCE {us_nce:7.1f}  (rows changed at most {10 * (K + 1)})")

    # The numbers the chapter relies on.
    assert soft_mean[0] > 3.5 and loss_mean[0] > 3.0  # both start far from the floor
    assert soft_high[-1] < H_COND / LN2 + 0.01  # the softmax reaches the floor
    assert loss_high[-1] < H_COND / LN2 + 0.05, "NCE does not get within 0.05 bits of the conditional entropy"
    assert norm_high[-1] < 0.1, "the scores of NCE are not self-normalized"
    assert max(float(np.abs(m - ppmi_matrix)[seen].max()) for m in nce_pmi) < 0.5

    # Figure 1: the loss and the normalization against the iterations.
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.4, 2.6))
    for mean, low, high, color, label in ((soft_mean, soft_low, soft_high, "C0", "prediction (softmax)"),
                                          (loss_mean, loss_low, loss_high, "C3", f"contrast (NCE, $K={K}$)")):
        ax1.plot(t, mean, color=color, linewidth=1, label=label)
        ax1.fill_between(t, low, high, color=color, alpha=0.25, linewidth=0)
    ax1.axhline(H_COND / LN2, color="gray", linestyle="--", linewidth=0.8, label=r"$H(C \mid W)$")
    ax1.set(xscale="log", xlabel="iterations", ylabel="loss of the softmax (bits per pair)", title="(a) loss")
    ax1.legend(fontsize=6)
    ax2.plot(t, norm_mean, color="C3", linewidth=1)
    ax2.fill_between(t, norm_low, norm_high, color="C3", alpha=0.25, linewidth=0)
    ax2.set(xscale="log", yscale="log", xlabel="iterations", ylabel=r"$|\log_2 \sum_c e^{s_{wc}}|$ (bits)", title="(b) normalization of NCE")
    for ax in (ax1, ax2):
        ax.tick_params(labelsize=7)
        ax.title.set_fontsize(8)
        ax.xaxis.label.set_size(7)
        ax.yaxis.label.set_size(7)
    fig.tight_layout()
    fig.savefig(FIGURES / "contrast_toy_loss.png", dpi=300, bbox_inches="tight")

    # Figure 2: the PMI matrix of each model, mean over the seeds (left column) and width of the 95% interval of the mean (right column).
    fig, axes = plt.subplots(2, 2, figsize=(6.4, 5.6), sharey=True, layout="constrained")
    mean_scale = TwoSlopeNorm(vmin=-1, vcenter=0, vmax=4)
    width_scale = plt.Normalize(0, max(width.max() for _, width in summary.values()))
    panels = [("(a) prediction: mean", summary["prediction"][0], "RdBu_r", mean_scale),
              ("(b) prediction: 95% interval", summary["prediction"][1], "viridis", width_scale),
              ("(c) contrast: mean", summary["contrast"][0], "RdBu_r", mean_scale),
              ("(d) contrast: 95% interval", summary["contrast"][1], "viridis", width_scale)]
    images = []
    for ax, (title, matrix, cmap, norm) in zip(axes.ravel(), panels):
        images.append(ax.imshow(matrix[np.ix_(perm, perm)], cmap=cmap, norm=norm, interpolation="nearest"))
        ax.set_title(title, fontsize=8)
        ax.set_xticks(range(len(ORDER)), ORDER, rotation=90, fontsize=5)
        ax.set_yticks(range(len(ORDER)), ORDER, fontsize=5)
        ax.tick_params(length=0)
        for end in GROUP_ENDS:
            ax.axhline(end - 0.5, color="black", linewidth=0.4)
            ax.axvline(end - 0.5, color="black", linewidth=0.4)
    for image, column in ((images[0], 0), (images[1], 1)):
        bar = fig.colorbar(image, ax=axes[:, column], shrink=0.8, pad=0.02)
        bar.set_label("bits", fontsize=7)
        bar.ax.tick_params(labelsize=6)
    fig.savefig(FIGURES / "contrast_toy_pmi.png", dpi=300, bbox_inches="tight")
    print(f"\nsaved {(FIGURES / 'contrast_toy_loss.png').resolve()} and {(FIGURES / 'contrast_toy_pmi.png').resolve()}")
