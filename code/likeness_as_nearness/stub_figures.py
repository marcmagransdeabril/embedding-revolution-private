# SKELETON: placeholder figures of chapters/likeness_as_nearness.qmd; the numbers are invented to show the expected shape.
"""Draw the stubs of the figures of the chapter "Likeness as Nearness". Nothing here is measured: every panel carries
the watermark STUB, and each stub is to be replaced by a script that computes the real figure and drops the marker."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parents[2] / "figures" / "likeness_as_nearness"
rng = np.random.default_rng(0)


def stamp(ax):
    """Mark a panel as invented data."""
    ax.text(0.5, 0.5, "STUB", transform=ax.transAxes, ha="center", va="center", fontsize=40, color="grey", alpha=0.25, rotation=25)


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT / f"{name}.png", dpi=150)
    plt.close(fig)


def loss_agreement():
    """Expected: the three losses agree with an association judge more than with a similarity judge."""
    fig, ax = plt.subplots(figsize=(6, 3.5))
    names = ["PPMI+SVD", "SGNS", "GloVe"]
    x = np.arange(3)
    ax.bar(x - 0.2, [0.62, 0.66, 0.64], 0.4, label="association judge")
    ax.bar(x + 0.2, [0.38, 0.42, 0.40], 0.4, label="similarity judge")
    ax.axhline(0.78, ls="--", color="k", label="human ceiling")
    ax.set_xticks(x, names)
    ax.set_ylabel("Spearman ρ with the judge")
    ax.legend(fontsize=8)
    stamp(ax)
    save(fig, "stub_loss_agreement")


def centring():
    """Expected: removing the mean and the top directions raises the correlation with the judge, and lowers the one with frequency."""
    fig, ax = plt.subplots(figsize=(6, 3.5))
    x = np.arange(3)
    ax.bar(x - 0.2, [0.40, 0.35, 0.30], 0.4, label="raw cosine")
    ax.bar(x + 0.2, [0.48, 0.44, 0.41], 0.4, label="centred, top-3 removed")
    ax.errorbar(x - 0.2, [0.40, 0.35, 0.30], yerr=0.03, fmt="none", color="k")
    ax.errorbar(x + 0.2, [0.48, 0.44, 0.41], yerr=0.03, fmt="none", color="k")
    ax.axhline(0.0, color="grey", lw=1, label="shuffled-label null")
    ax.set_xticks(x, ["static", "sentence encoder", "contextual, last layer"])
    ax.set_ylabel("Spearman ρ with the judge")
    ax.legend(fontsize=8)
    stamp(ax)
    save(fig, "stub_centring")


def radius_density():
    """Expected: the likeness of the neighbours inside a fixed radius falls as the region gets sparser."""
    fig, ax = plt.subplots(figsize=(6, 3.5))
    d = rng.uniform(0.2, 1.0, 300)
    ax.scatter(d, 4.5 - 3 * d + rng.normal(0, 0.5, 300), s=8, alpha=0.6)
    ax.set_xlabel("distance to the k-th neighbour (local density)")
    ax.set_ylabel("judged likeness of neighbours inside ε")
    stamp(ax)
    save(fig, "stub_radius_density")


def axioms():
    """Expected: the four smoke tests of the Tversky section against random vectors of the same dimension."""
    fig, axes = plt.subplots(1, 4, figsize=(9, 3))
    panels = [("(a) a·b > a·a", 0.18, 0.00), ("(b) mutual top-k", 0.35, 0.10), ("(c) triangle violations of 1−cos", 0.05, 0.12), ("(d) attention antisym/sym", 0.9, 0.0)]
    for ax, (title, trained, null) in zip(axes, panels):
        ax.bar(["trained", "random"], [trained, null], color=["C0", "C7"])
        ax.set_title(title, fontsize=8)
        stamp(ax)
    save(fig, "stub_axioms")


def many_spaces():
    """Expected: the gap between seeds is the noise floor; algorithm and corpus gaps count only above it."""
    fig, ax = plt.subplots(figsize=(6, 3.5))
    labels = ["seed", "algorithm", "corpus"]
    means = np.array([0.80, 0.62, 0.45])
    ax.bar(labels, means, yerr=0.04, color=["C7", "C0", "C1"])
    ax.axhline(means[0], ls="--", color="k", label="noise floor")
    ax.set_ylabel("overlap of the 10 nearest neighbours")
    ax.legend(fontsize=8)
    stamp(ax)
    save(fig, "stub_many_spaces")


if __name__ == "__main__":
    for draw in (loss_agreement, centring, radius_density, axioms, many_spaces):
        draw()
