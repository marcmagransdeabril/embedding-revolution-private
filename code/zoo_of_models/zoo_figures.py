"""The figures of the appendix "A Zoo of Models": PPMI-SVD, SGNS and GloVe run on the same toy co-occurrence matrix of twelve words in
three topics, with d = 2 so that the space can be drawn. Each figure shows what the model does with the counts, not its formula.
The counts come from one seed (0), the figures illustrate; they rank nothing. Each figure is 6.5 inches wide, the text block."""
from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.patches

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

FIGURES = Path(__file__).resolve().parents[2] / "figures" / "zoo_of_models"
TOPICS = {"royal": ["king", "queen", "crown", "throne"], "pets": ["dog", "cat", "paw", "fur"], "weather": ["rain", "snow", "cold", "wind"]}
COLOURS = {"royal": "tab:blue", "pets": "tab:green", "weather": "tab:orange"}
WORDS = [w for ws in TOPICS.values() for w in ws]
TOPIC_OF = [t for t, ws in TOPICS.items() for _ in ws]
D, K, X_MAX = 2, 3, 100


def toy_counts(rng: np.random.Generator) -> np.ndarray:
    """Symmetric co-occurrence counts X. Each word has a frequency and a hidden position on a circle (three topics, 60 degrees apart, with
    some spread); two words meet more often the closer their positions are, so a plane is enough to recover the layout."""
    freq = np.tile([4.0, 3.0, 2.0, 1.0], 3) * rng.uniform(0.8, 1.2, len(WORDS))
    angle = np.repeat(np.radians([30, 90, 150]), 4) + rng.normal(0, 0.35, len(WORDS))
    rate = 40.0 * np.outer(freq, freq) * np.exp(2.0 * np.cos(angle[:, None] - angle[None, :]) - 2.0)
    x = np.triu(rng.poisson(rate), 1)
    return x + x.T


def ppmi(x: np.ndarray) -> np.ndarray:
    p = x / x.sum()
    marginal = p.sum(axis=1)
    with np.errstate(divide="ignore"):
        pmi = np.log(p / np.outer(marginal, marginal))
    return np.maximum(pmi, 0.0)  # log 0 = -inf is cut to 0 as well


def save(fig, name: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / f"{name}.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def draw_words(ax, points: np.ndarray, fontsize: float = 7) -> None:
    for (px, py), w, t in zip(points, WORDS, TOPIC_OF):
        ax.scatter(px, py, color=COLOURS[t], s=14, zorder=3)
        ax.annotate(w, (px, py), xytext=(3, 3), textcoords="offset points", fontsize=fontsize, color=COLOURS[t])
    ax.axhline(0, color="lightgrey", lw=0.5, zorder=0)
    ax.axvline(0, color="lightgrey", lw=0.5, zorder=0)
    ax.set_aspect("equal", adjustable="datalim")


def ppmi_svd_figure(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """The matrix with its rows in the order of a text (shuffled), the singular values, and the rows of E in the plane."""
    m = ppmi(x)
    order = rng.permutation(len(WORDS))
    u, s, _ = np.linalg.svd(m)
    e = u[:, :D] * s[:D] ** 0.5
    kept = (s[:D] ** 2).sum() / (s**2).sum()
    fig, axes = plt.subplots(1, 3, figsize=(6.5, 2.4), gridspec_kw={"width_ratios": [1.1, 0.8, 1.3]})
    im = axes[0].imshow(m[np.ix_(order, order)], cmap="Blues")
    axes[0].set_xticks(range(len(WORDS)), [WORDS[i] for i in order], rotation=90, fontsize=5)
    axes[0].set_yticks(range(len(WORDS)), [WORDS[i] for i in order], fontsize=5)
    axes[0].set_title("PPMI matrix M\n(words in arbitrary order)", fontsize=7)
    fig.colorbar(im, ax=axes[0], fraction=0.046)
    axes[1].bar(range(1, len(s) + 1), s, color=["tab:red"] * D + ["lightgrey"] * (len(s) - D))
    axes[1].set(xlabel="direction", title=f"singular values\nthe first {D} keep {kept:.0%} of $\\|M\\|_F^2$")
    axes[1].title.set_fontsize(7)
    draw_words(axes[2], e)
    axes[2].set_title("rows of E = U Σ$^{1/2}$ in the plane", fontsize=7)
    fig.tight_layout()
    save(fig, "ppmi_svd")
    print(f"PPMI-SVD: the first {D} squared singular values keep {kept:.3f} of the squared Frobenius norm")
    return e


def sgns_train(x: np.ndarray, rng: np.random.Generator, steps: int = 40000, lr: float = 0.05):
    """SGNS by plain SGD on pairs drawn from the counts, with K noise words from the unigram law to the 3/4. Returns E, V and the initial E, V."""
    n = len(WORDS)
    e0, v0 = rng.normal(0, 0.3, (n, D)), rng.normal(0, 0.3, (n, D))
    e, v = e0.copy(), v0.copy()
    pair_p = (x / x.sum()).ravel()
    noise_p = x.sum(axis=1) ** 0.75
    noise_p /= noise_p.sum()
    pairs = rng.choice(n * n, size=steps, p=pair_p)
    noises = rng.choice(n, size=(steps, K), p=noise_p)
    for p, ns in zip(pairs, noises):
        w, c = divmod(p, n)
        ew = e[w].copy()
        g_pos = 1 / (1 + np.exp(ew @ v[c])) # = 1 - sigma(e.v): the pull
        e[w] += lr * g_pos * v[c]
        v[c] += lr * g_pos * ew
        for j in ns:
            g_neg = 1 / (1 + np.exp(-(ew @ v[j])))  # = sigma(e.v): the push
            e[w] -= lr * g_neg * v[j]
            v[j] -= lr * g_neg * ew
    return e, v, e0, v0


def sgns_figure(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Left, one update of one real context and one noise word from the initial vectors (step size 1, to be visible). Right, the plane after training."""
    e, v, e0, v0 = sgns_train(x, rng)
    w, c, j, lr = WORDS.index("king"), WORDS.index("crown"), WORDS.index("rain"), 1.0
    ew, vc, vj = e0[w], v0[c], v0[j]
    pull, push = 1 / (1 + np.exp(ew @ vc)), 1 / (1 + np.exp(-(ew @ vj)))
    new = {"e_w": ew + lr * pull * vc - lr * push * vj, "v_c": vc + lr * pull * ew, "v_n": vj - lr * push * ew}
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 3.1))
    ax = axes[0]
    for label, old, key, colour in [("$\\mathbf{e}_w$ (king)", ew, "e_w", "black"), ("$\\mathbf{v}_c$ (crown, real context)", vc, "v_c", "tab:green"),
                                    ("$\\mathbf{v}_{c_i}$ (rain, noise)", vj, "v_n", "tab:red")]:
        ax.scatter(*old, color=colour, s=16, zorder=3)
        ax.scatter(*new[key], facecolors="none", edgecolors=colour, s=16, zorder=3)
        ax.add_patch(matplotlib.patches.FancyArrowPatch(old, new[key], arrowstyle="-|>", mutation_scale=8, color=colour, lw=1.2, shrinkA=2, shrinkB=2))
        ax.annotate(label, old, xytext=(4, -9), textcoords="offset points", fontsize=6.5, color=colour)
    ax.axhline(0, color="lightgrey", lw=0.5, zorder=0)
    ax.axvline(0, color="lightgrey", lw=0.5, zorder=0)
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_title("one update (step size 1): filled before, open after;\nking is pulled to crown and pushed from rain", fontsize=7)
    draw_words(axes[1], e)
    axes[1].set_title("E after 40,000 updates", fontsize=7)
    fig.tight_layout()
    save(fig, "sgns")
    d_before, d_after = np.linalg.norm(ew - vc), np.linalg.norm(new["e_w"] - new["v_c"])
    print(f"SGNS: distance king-crown {d_before:.2f} -> {d_after:.2f}; "
          f"king.rain {ew @ vj:.2f} -> {new['e_w'] @ new['v_n']:.2f}")
    return e


def glove_weight(x: np.ndarray) -> np.ndarray:
    return np.minimum((x / X_MAX) ** 0.75, 1.0)


def glove_train(x: np.ndarray, rng: np.random.Generator, epochs: int = 500, lr: float = 0.1):
    """Full-batch AdaGrad on the pairs with X > 0. Returns W, W-tilde, the biases and the fitted score for each such pair."""
    n = len(WORDS)
    i, j = np.nonzero(x)
    logx, f = np.log(x[i, j]), glove_weight(x[i, j])
    w, wt = rng.normal(0, 0.3, (n, D)), rng.normal(0, 0.3, (n, D))
    b, bt = np.zeros(n), np.zeros(n)
    accum = [np.full_like(a, 1e-8) for a in (w, wt, b, bt)]
    for _ in range(epochs):
        r = f * ((w[i] * wt[j]).sum(1) + b[i] + bt[j] - logx)
        grads = [np.zeros_like(w), np.zeros_like(wt), np.zeros_like(b), np.zeros_like(bt)]
        np.add.at(grads[0], i, r[:, None] * wt[j])
        np.add.at(grads[1], j, r[:, None] * w[i])
        np.add.at(grads[2], i, r)
        np.add.at(grads[3], j, r)
        for a, g, s in zip((w, wt, b, bt), grads, accum):
            s += g**2
            a -= lr * g / np.sqrt(s)
    return w, wt, i, j, (w[i] * wt[j]).sum(1) + b[i] + bt[j]


def glove_figure(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Left, the weight f with the pairs of the toy corpus on it. Right, the fitted score against the log count of each pair, which is the quantity fitted."""
    w, wt, i, j, score = glove_train(x, rng)
    logx, f = np.log(x[i, j]), glove_weight(x[i, j])
    same = np.array([TOPIC_OF[a] == TOPIC_OF[b] for a, b in zip(i, j)])
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 2.9))
    grid = np.geomspace(0.8, 1.5 * x.max(), 400)
    axes[0].plot(grid, glove_weight(grid), color="black", lw=1.2)
    axes[0].scatter(x[i, j][same], f[same], s=6, color="tab:blue", label="two words of one topic", zorder=3)
    axes[0].scatter(x[i, j][~same], f[~same], s=6, color="tab:red", label="two words of different topics", zorder=3)
    axes[0].axvline(X_MAX, color="grey", ls="--", lw=0.6)
    axes[0].set(xscale="log", xlim=(0.8, 1.5 * x.max()), xlabel="count $X_{ij}$ (log axis)", ylabel="weight $f(X_{ij})$", ylim=(0, 1.1))
    axes[0].set_title("the weight: rare pairs count little, frequent ones are capped", fontsize=7)
    axes[0].legend(fontsize=6, loc="lower right")
    axes[1].scatter(logx[same], score[same], s=5 + 25 * f[same], color="tab:blue", alpha=0.6)
    axes[1].scatter(logx[~same], score[~same], s=5 + 25 * f[~same], color="tab:red", alpha=0.6)
    lim = (min(logx.min(), score.min()), max(logx.max(), score.max()))
    axes[1].plot(lim, lim, color="black", lw=0.8)
    axes[1].set(xlabel="$\\log X_{ij}$", ylabel="$\\mathbf{w}_i^\\top\\tilde{\\mathbf{w}}_j + b_i + \\tilde b_j$")
    axes[1].set_title("the fit (marker size is the weight)", fontsize=7)
    fig.tight_layout()
    save(fig, "glove")
    err_rare = np.abs(score - logx)[f < 0.3].mean()
    err_common = np.abs(score - logx)[f >= 0.3].mean()
    print(f"GloVe: mean absolute error on log X is {err_rare:.2f} for the pairs with f < 0.3 and {err_common:.2f} for the others "
          f"({(f < 0.3).sum()} and {(f >= 0.3).sum()} pairs, {(f == 1).sum()} capped)")
    return w


if __name__ == "__main__":
    counts = toy_counts(np.random.default_rng(0))
    print(f"toy corpus: {len(WORDS)} words, {int(counts.sum() // 2)} co-occurrences, largest count {counts.max()}, "
          f"{(counts == 0).sum()} empty cells")
    ppmi_svd_figure(counts, np.random.default_rng(1))
    sgns_figure(counts, np.random.default_rng(2))
    glove_figure(counts, np.random.default_rng(3))
