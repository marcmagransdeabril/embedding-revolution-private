"""Control for Learning by Contrast: Words. Do the loss curves fall at the end because the step size does, or because of the iterations?

Same corpus, pairs, d = 5, K = 5 and five seeds as contrast_toy_nce.py, with four step-size schedules for the softmax predictor and for the
contrastive model: (a) linear from 0.1 to 0 over 1,000,000 iterations (the chapter), (b) constant 0.1 for 1,000,000, (c) constant 0.01
for 1,000,000, (d) linear from 0.1 to 0 over 100,000 iterations. Printed: the loss of the softmax over the vocabulary (bits per pair,
mean [95% bootstrap interval of the mean over the seeds]) at fixed iteration numbers, and at the end of the run.
"""
from concurrent.futures import ProcessPoolExecutor

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from contrast_toy_nce import D, K, cdf, nce_step, p_c, scores, softmax_loss
from prediction_toy_softmax import H_COND, LN2, SEEDS, SENTENCE_PAIRS, SENTENCES, loss, sgd_step, vocab
from utils import bootstrap_interval

SCHEDULES = {  # name: (iterations, step size at iteration t, 1-based)
    "linear 0.1 -> 0, 1M": (1_000_000, lambda t, n: 0.1 * (1 - (t - 1) / n)),
    "constant 0.1, 1M": (1_000_000, lambda t, n: 0.1),
    "constant 0.01, 1M": (1_000_000, lambda t, n: 0.01),
    "linear 0.1 -> 0, 100k": (100_000, lambda t, n: 0.1 * (1 - (t - 1) / n)),
}
CHECK = (1_000, 10_000, 100_000, 1_000_000)
POINTS = tuple(sorted({int(round(t)) for t in np.logspace(1, 6, 31)} | set(CHECK)))
FIGURE = "../../figures/embedding_spaces/contrast_toy_schedule.png"


def run(args: tuple[str, str, int]) -> list:
    model, name, seed = args
    n_iter, eta = SCHEDULES[name]
    rng = np.random.default_rng(seed)
    e = 0.1 * rng.standard_normal((len(vocab), D))
    v = 0.1 * rng.standard_normal((len(vocab), D))
    a, log_kpn = np.zeros(len(vocab)), np.log(K * p_c)
    out = {}
    for t, s in enumerate(rng.integers(len(SENTENCES), size=n_iter), start=1):
        words, neighbours = SENTENCE_PAIRS[s]
        if model == "softmax":
            sgd_step(e, v, words, neighbours, eta(t, n_iter))
        else:
            noise = np.minimum(np.searchsorted(cdf, rng.random((len(words), K)), side="right"), len(vocab) - 1)
            nce_step(e, v, a, words, neighbours, noise, log_kpn, eta(t, n_iter))
        if t in POINTS or t == n_iter:
            out[t] = loss(e, v) / LN2 if model == "softmax" else softmax_loss(scores(e, v, a))
    return out


if __name__ == "__main__":
    jobs = [(m, name, seed) for m in ("softmax", "contrast") for name in SCHEDULES for seed in SEEDS]
    with ProcessPoolExecutor() as pool:
        results = list(pool.map(run, jobs))
    print(f"H(C|W) = {H_COND / LN2:.4f} bits per pair; loss of the softmax over the vocabulary, mean [95% interval] over {len(SEEDS)} seeds")
    for m in ("softmax", "contrast"):
        print(f"\n{m}")
        print(f"{'schedule':>24} " + " ".join(f"{'t=' + format(t, ','):>24}" for t in CHECK) + f" {'end':>24}")
        for name in SCHEDULES:
            rows = [r for j, r in zip(jobs, results) if j[0] == m and j[1] == name]
            cells = []
            for t in CHECK:
                if t in rows[0]:
                    mean, lo, hi = bootstrap_interval(np.array([[r[t]] for r in rows]))
                    cells.append(f"{mean[0]:.4f} [{lo[0]:.4f}, {hi[0]:.4f}]")
                else:
                    cells.append("-")
            end = max(rows[0])
            mean, lo, hi = bootstrap_interval(np.array([[r[end]] for r in rows]))
            print(f"{name:>24} " + " ".join(f"{c:>24}" for c in cells) + f" {mean[0]:.4f} [{lo[0]:.4f}, {hi[0]:.4f}]")

    # Figure: the loss against the iterations for each schedule, one panel per model.
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.8), sharey=True)
    for ax, m in zip(axes, ("softmax", "contrast")):
        for color, name in zip(("C0", "C3", "C2", "C1"), SCHEDULES):
            rows = [r for j, r in zip(jobs, results) if j[0] == m and j[1] == name]
            t = np.array([x for x in POINTS if x in rows[0]])
            mean, lo, hi = bootstrap_interval(np.array([[r[x] for x in t] for r in rows]))
            ax.plot(t, mean, color=color, linewidth=1, label=name)
            ax.fill_between(t, lo, hi, color=color, alpha=0.25, linewidth=0)
        ax.axhline(H_COND / LN2, color="gray", linestyle="--", linewidth=0.8)
        ax.set(xscale="log", ylim=(1.8, 2.5), xlabel="iterations", title="softmax predictor" if m == "softmax" else "contrastive model")
        ax.tick_params(labelsize=7)
        ax.title.set_fontsize(8)
        ax.xaxis.label.set_size(7)
    axes[0].set_ylabel("loss of the softmax (bits per pair)", fontsize=7)
    axes[0].legend(fontsize=6)
    fig.tight_layout()
    fig.savefig(FIGURE, dpi=300, bbox_inches="tight")
