"""The figures of the section "Similar, Related or Associated?" (see relation_split.py, which computes what they show), drawn at the
width of the text block of the book (6.5 inches). Nothing is computed here."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import utils

CELLS = ("both", "similar only", "associated only", "neither")
CONTRASTS = (("associated only", "similar only"), ("similar only", "neither"), ("associated only", "neither"))


def save(fig, name: str) -> None:
    utils.FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(utils.FIGURES / f"{name}.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def errors(estimates: list) -> np.ndarray:
    """Error bars (2 x n) from (point, low, high) triples."""
    return np.array([[e[0] - e[1], e[2] - e[0]] for e in estimates]).T


def judges(similarity: np.ndarray, association: np.ndarray, thresholds: dict, rho: tuple, suffix: str) -> None:
    """Test 1: the two judges of each SimLex-999 pair, with the thirds that cut them into the four cells."""
    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    ax.scatter(similarity, association, s=4, color="grey", alpha=0.6)
    for t in thresholds["similarity"]:
        ax.axvline(t, color="black", lw=0.6, ls="--")
    for t in thresholds["association"]:
        ax.axhline(t, color="black", lw=0.6, ls="--")
    top = association.max()
    for x, y, label in ((0.99, 0.99, "both"), (0.99, 0.01, "similar only"), (0.01, 0.99, "associated only"), (0.01, 0.01, "neither")):
        ax.text(x, y, label, fontsize=7, ha="right" if x > 0.5 else "left", va="top" if y > 0.5 else "bottom", transform=ax.transAxes,
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 1})
    ax.set_yscale("symlog", linthresh=0.5)  # most strengths are below 0.5, a few reach 9
    ax.set(xlabel="SimLex-999 similarity rating (0-10)", ylabel="USF free-association\nstrength (symlog scale)",
           ylim=(-0.05, 2 * top),
           title=f"Spearman correlation of the two judges: {rho[0]:.2f} [{rho[1]:.2f}, {rho[2]:.2f}]")
    ax.title.set_fontsize(8)
    save(fig, "relation_split_judges" + suffix)


def spearman(results: dict, suffix: str) -> None:
    """Test 2: Spearman correlation of the cosine with each judge over all its pairs, with the ceilings of the raters as lines."""
    names = list(results["spaces"])
    judges_ = list(results["spaces"][names[0]]["spearman"])
    fig, ax = plt.subplots(figsize=(6.5, 3.0))
    width = 0.8 / len(names)
    for k, name in enumerate(names):
        est = [results["spaces"][name]["spearman"][j] for j in judges_]
        ax.bar(np.arange(len(judges_)) + (k - (len(names) - 1) / 2) * width, [e[0] for e in est], width * 0.9,
               yerr=errors(est), capsize=2, label=name)
    ceiling = results["judges"]["ceiling"]
    # SimLex-999: the cited average pairwise agreement (its file has no individual ratings); WordSim-353: one rater against the mean
    # of the others, the ceiling of a correlation with a mean rating
    for x, value, label in ((0, ceiling["simlex_pairwise"], "raters, pairwise"), (2, ceiling["ws353_one_vs_rest"], "raters, one vs rest")):
        ax.hlines(value, x - 0.45, x + 0.45, color="black", lw=0.8, ls="--")
        ax.text(x - 0.45, value + 0.01, f"{label} {value:.2f}", fontsize=6, va="bottom", ha="left")
    ax.axhline(0, color="black", lw=0.5)
    ax.set_xticks(range(len(judges_)), judges_, fontsize=7)
    ax.set(ylabel="Spearman correlation\nof the cosine with the judge", ylim=(min(0, ax.get_ylim()[0]), 0.9))
    ax.legend(fontsize=6, loc="upper center")
    save(fig, "relation_split_spearman" + suffix)


def cells(results: dict, kind: str, suffix: str) -> None:
    """Tests 3 and 4: the mean of each cell in each space (left), and the contrasts between cells (right), against the null."""
    names = list(results["spaces"])
    fig, (left, right) = plt.subplots(1, 2, figsize=(6.5, 2.9), gridspec_kw={"width_ratios": [1.3, 1]})
    width = 0.8 / len(names)
    for k, name in enumerate(names):
        row = results["spaces"][name][kind]
        shift = (k - (len(names) - 1) / 2) * width
        est = [row[c]["mean"] for c in CELLS]
        bars = left.bar(np.arange(4) + shift, [e[0] for e in est], width * 0.9, yerr=errors(est), capsize=2, label=name)
        null = results["spaces"][name]["null_cosine"] if kind == "cosine" else 0.0
        left.hlines(null, -0.5, 3.5, color=bars.patches[0].get_facecolor(), lw=0.8, ls="--")
        est = [row[f"{a} - {b}"] for a, b in CONTRASTS]
        right.bar(np.arange(len(CONTRASTS)) + shift, [e[0] for e in est], width * 0.9, yerr=errors(est), capsize=2)
    left.set_xticks(range(4), [c.replace(" ", "\n") for c in CELLS], fontsize=7)
    left.set_ylabel("mean cosine" if kind == "cosine" else "mean cosine minus\nthe frequency fit", fontsize=8)
    left.legend(fontsize=6)
    right.axhline(0, color="black", lw=0.6)
    right.set_xticks(range(len(CONTRASTS)), [f"{a}\nminus\n{b}" for a, b in CONTRASTS], fontsize=6)
    right.set_ylabel("difference of the means", fontsize=8)
    fig.tight_layout()
    save(fig, f"relation_split_{kind}{suffix}" if kind == "residual" else f"relation_split_cells{suffix}")
