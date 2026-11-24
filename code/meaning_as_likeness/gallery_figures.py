"""The figures of the section "A Gallery of Neighbours" (see gallery.py, which computes what they show). Each one is drawn at the width of
the text block of the book (6.5 inches), so that its type is the size it will be printed at. Nothing is computed here."""
from __future__ import annotations

import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import utils

CONTRASTS = [("synonym_vs_neither", "synonym pair nearer\nthan a pair of neither"),
             ("antonym_vs_neither", "antonym pair nearer\nthan a pair of neither"),
             ("synonym_vs_antonym", "synonym pair nearer\nthan an antonym pair")]


def save(fig, name: str) -> None:
    utils.FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(utils.FIGURES / f"{name}.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def neighbours_gallery(vocab: list[str], counts: np.ndarray, queries, controls, neighbours: dict, rule: dict) -> None:
    """One query per frequency band, from the most frequent to the rarest, with its number of occurrences in the training text, its five
    nearest neighbours in each space, and five random words of the band."""
    names = list(neighbours)
    fig, ax = plt.subplots(figsize=(6.5, 7.0))
    ax.axis("off")
    columns = ["word\n(occurrences)"] + names + ["control: random\nwords of the band"]
    xs = np.linspace(0.0, 0.82, len(columns))
    for x, c in zip(xs, columns):
        ax.text(x, 1.0, c, fontweight="bold", fontsize=6, va="top")
    marks = {v: k for k, v in rule.items()}
    for r, q in enumerate(queries):
        y = 0.94 - r * 0.094
        cells = [f"{vocab[q]}  ({int(counts[q]):,})" + (f"\n[{marks[int(q)]}]" if int(q) in marks else "")]
        cells += [" ".join(vocab[i] for i in neighbours[n][q]) for n in names] + [" ".join(vocab[i] for i in controls[r])]
        for k, (x, c) in enumerate(zip(xs, cells)):
            ax.text(x, y, c if k == 0 else textwrap.fill(c, 17), fontsize=5.6, va="top")
    save(fig, "gallery_neighbours")


def null_distribution(curves: dict, centres: np.ndarray, dim: int) -> None:
    """Density of the cosine of all pairs of words in each space, against the normal law of two random directions in `dim` dimensions,
    whose standard deviation is 1 / sqrt(dim). A shuffled space has the same curve as the one it shuffles."""
    fig, ax = plt.subplots(figsize=(6.5, 2.8))
    width = 5 * 2 / len(centres)  # bins merged five at a time: the pairs are 4.5 x 10^8, so the curve is smooth
    x = centres.reshape(-1, 5).mean(axis=1)
    for name, hist in curves.items():
        coarse = hist.reshape(-1, 5).sum(axis=1)
        ax.plot(x, coarse / coarse.sum() / width, label=name, lw=1.2)
    ax.plot(x, np.exp(-x ** 2 * dim / 2) * np.sqrt(dim / (2 * np.pi)), "k--", lw=0.8, label=f"normal, sd 1/sqrt({dim})")
    ax.set_xlim(-0.5, 0.8)
    ax.set_xlabel("cosine of a random pair of words")
    ax.set_ylabel("density")
    ax.legend(fontsize=7)
    fig.tight_layout()
    save(fig, "gallery_null")


def cosine_by_class(curves: dict, centres: np.ndarray) -> None:
    """Density of the cosine of the synonym pairs, the antonym pairs and the pairs of neither, in each trained space."""
    fig, axes = plt.subplots(1, len(curves), figsize=(6.5, 2.6), sharex=True)
    for ax, (name, c) in zip(axes, curves.items()):
        for label, hist in c.items():
            coarse = hist.reshape(-1, 20).sum(axis=1)  # 100 bins of 0.02: the classes of a few hundred pairs are too noisy at 2000 bins
            ax.plot(centres.reshape(-1, 20).mean(axis=1), coarse / coarse.sum() / 0.02, label=label, lw=1.1)
        ax.set_title(name, fontsize=8)
        ax.set_xlim(-0.4, 1)
    for ax in axes:
        ax.set_xlabel("cosine")
    axes[0].set_ylabel("density")
    axes[0].legend(fontsize=6)
    fig.tight_layout()
    save(fig, "gallery_distributions")


def auc_bars(results: dict, names: list[str]) -> None:
    """The AUC of each contrast in each space (bootstrap interval over words), with the random models as nulls."""
    fig, ax = plt.subplots(figsize=(6.5, 3.3))
    width = 0.8 / len(names)
    for k, name in enumerate(names):
        row = results["spaces"][name]["auc"]
        points = np.array([row[c][0] for c, _ in CONTRASTS])
        errors = np.array([[row[c][0] - row[c][1], row[c][2] - row[c][0]] for c, _ in CONTRASTS]).T
        ax.bar(np.arange(3) + (k - (len(names) - 1) / 2) * width, points, width * 0.9, yerr=errors, capsize=1.5, label=name,
               color="lightgrey" if "random" in name else None, edgecolor="grey" if "random" in name else None)
    ax.axhline(0.5, color="black", lw=0.6, ls="--")
    ax.set_xticks(np.arange(3), [label for _, label in CONTRASTS], fontsize=7)
    ax.set(ylabel="Probability (0.5 = no difference)", ylim=(0, 1.12))
    ax.legend(fontsize=6, ncol=5, loc="upper center")
    save(fig, "gallery_auc")


def overlap_by_band(overlap: dict) -> None:
    """Mean top-5 overlap of two spaces as a function of the frequency of the word (the vocabulary cut into ten groups of equal size,
    from the most frequent to the rarest), with the bootstrap interval over words."""
    fig, ax = plt.subplots(figsize=(6.5, 3.0))
    for (pair, per_band), style in zip(overlap.items(), ["-", "--", "-.", ":", "-", "--"]):
        mean, low, high = (np.array([b[i] for b in per_band]) for i in range(3))
        ax.plot(range(len(mean)), mean, style, lw=1.2, label=pair)
        ax.fill_between(range(len(mean)), low, high, alpha=0.2)
    ax.set(xlabel="word frequency (0 = most frequent tenth of the vocabulary)", ylabel="top-5 overlap")
    ax.legend(fontsize=6)
    save(fig, "gallery_overlap")


def edit_distance(edit: dict) -> None:
    """For the exercise on spelling: the edit distance of random pairs, and its relation to the cosine in a trained space and in a random one."""
    fig, axes = plt.subplots(1, 3, figsize=(6.5, 2.3))
    axes[0].hist(edit["edit"], bins=40, color="grey")
    axes[0].set(title="edit distance of random pairs", xlabel="normalized edit distance")
    for ax, name in zip(axes[1:], ["SGNS", "random Gaussian"]):
        ax.hist2d(edit["edit"], edit["cosine"][name], bins=40, cmap="Greys", cmin=1)
        ax.set(title=f"{name}: rho = {edit['rho'][name][0]:.3f}", xlabel="edit distance", ylabel="cosine")
    for ax in axes:
        ax.title.set_fontsize(7)
    fig.tight_layout()
    save(fig, "gallery_edit_distance")
