"""Visual exploration before the rater of relation_unlabelled.py (Q3 of the chapter "Meaning as Likeness"): what the cosine of the pairs that
no judge names looks like, where the strata of the exploration fall, whether the two spaces agree on what is extreme there, and whether
the extremes are a matter of rare words. No pair is shown or printed, so that the person who will label the sample stays blind to it.

Population and cuts are those of relation_unlabelled.py: the pairs of two WordNet words that hold none of the 13 judged relations, and the
strata at the 1st percentile, the middle (49.5 to 50.5) and the 99th percentile of the cosine of that population in each space. Three
figures: relation_unlabelled_distribution.png (exact density of the cosine of the unlabelled and of the judged pairs, with the strata),
relation_unlabelled_agreement.png (the cosine in the two spaces of RANDOM_PAIRS random unlabelled pairs) and relation_unlabelled_frequency.png
(the cosine against the rank of the rarer word of the pair, in each space). Prints the cuts, the Spearman correlation between the two
spaces, how many of the pairs of each extreme in one space are in the same extreme in the other, and the Spearman correlation of the cosine
with the rank of the rarer word.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr

import gallery
import relation_collapse as rc
import relation_collapse_figures as base
import relation_unlabelled as ru
import utils

RANDOM_PAIRS = 400_000
COLOURS = {"top 1%": "tab:red", "bottom 1%": "tab:blue", "middle": "tab:grey"}


def centres() -> np.ndarray:
    return (np.arange(gallery.BINS) + 0.5) / gallery.BINS * 2 - 1


def judged_histogram(u: np.ndarray, keys: np.ndarray) -> np.ndarray:
    """Histogram of the cosine of the judged pairs (keys i * m + j)."""
    i, j = keys // len(u), keys % len(u)
    return np.bincount(gallery.to_bin((u[i] * u[j]).sum(axis=1)), minlength=gallery.BINS)


def random_unlabelled(m: int, keys: np.ndarray, seed: int = 0) -> np.ndarray:
    """RANDOM_PAIRS seeded pairs of distinct WordNet words (numbered 0 to m - 1, i < j) that are not judged."""
    rng = np.random.default_rng(seed)
    a = rng.integers(0, m, RANDOM_PAIRS)
    b = (a + rng.integers(1, m, RANDOM_PAIRS)) % m
    pairs = np.column_stack([np.minimum(a, b), np.maximum(a, b)])
    key = pairs[:, 0].astype(np.int64) * m + pairs[:, 1]
    return pairs[keys[np.minimum(np.searchsorted(keys, key), len(keys) - 1)] != key]


def main() -> None:
    vocab, index, _ = utils.load_vocab()
    pairs, _, covered = rc.judged_pairs(vocab, index)
    cov, keys = ru.judged_keys(len(vocab), pairs, covered)
    sample = random_unlabelled(len(cov), keys)
    state = {}
    for name, stem in rc.SPACES.items():
        u = utils.unit(utils.load_space(stem)[cov].astype(np.float32))
        hist = ru.unlabelled_histogram(u, keys)
        ranges = ru.stratum_bins(hist)
        state[name] = {"hist": hist, "judged": judged_histogram(u, keys), "ranges": ranges,
                       "cosine": (u[sample[:, 0]] * u[sample[:, 1]]).sum(axis=1),
                       "cuts": {k: (float(centres()[min(a, gallery.BINS - 1)]), float(centres()[min(b, gallery.BINS) - 1])) for k, (a, b) in ranges.items()}}
        print(f"{name}: " + "; ".join(f"{k}: cosine {a:.3f} to {b:.3f}" for k, (a, b) in state[name]["cuts"].items()))
    distribution(state)
    agreement(state, sample)
    frequency(state, cov, sample)


def distribution(state: dict) -> None:
    """Exact density of the cosine of the unlabelled and the judged pairs, in each space, with the three strata of the exploration."""
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 2.8), sharey=True)
    x = centres()
    for ax, (name, st) in zip(axes, state.items()):
        for label, hist, colour in (("unlabelled pairs", st["hist"], "black"), ("judged pairs", st["judged"], "tab:orange")):
            ax.semilogy(x, np.maximum(hist / hist.sum() / (2 / gallery.BINS), 1e-7), color=colour, lw=0.9, label=label)
        for k, (a, b) in st["cuts"].items():
            ax.axvspan(a, b, color=COLOURS[k], alpha=0.25, lw=0, label=k)
        ax.set_title(name, fontsize=8)
        ax.set_xlabel("cosine", fontsize=7)
        ax.set_xlim(-0.5, 1.0)
        ax.set_ylim(1e-6, 30)
        ax.tick_params(labelsize=6)
    axes[0].set_ylabel("density of pairs", fontsize=7)
    axes[1].legend(fontsize=5.5, loc="upper right")
    fig.tight_layout()
    base.save(fig, "relation_unlabelled_distribution")


def agreement(state: dict, sample: np.ndarray) -> None:
    """The cosine of the same random unlabelled pairs in the two spaces, with the cuts of each; prints how the extremes overlap."""
    (a, sa), (b, sb) = state.items()
    fig, ax = plt.subplots(figsize=(3.4, 3.2))
    image = ax.hexbin(sa["cosine"], sb["cosine"], gridsize=70, bins="log", mincnt=1, cmap="viridis")
    for k, (lo, hi) in sa["cuts"].items():
        ax.axvspan(lo, hi, color=COLOURS[k], alpha=0.15, lw=0)
    for k, (lo, hi) in sb["cuts"].items():
        ax.axhspan(lo, hi, color=COLOURS[k], alpha=0.15, lw=0)
    ax.set(xlim=(-0.5, 1.0), ylim=(-0.5, 1.0))
    ax.set_xlabel(f"cosine in {a}", fontsize=7)
    ax.set_ylabel(f"cosine in {b}", fontsize=7)
    ax.tick_params(labelsize=6)
    fig.colorbar(image, ax=ax, shrink=0.8).set_label("pairs (log)", fontsize=6)
    fig.tight_layout()
    base.save(fig, "relation_unlabelled_agreement")
    print(f"Spearman correlation of the cosine of {RANDOM_PAIRS:,} random unlabelled pairs between the spaces: "
          f"{spearmanr(sa['cosine'], sb['cosine']).statistic:.3f}")
    for k in ("top 1%", "bottom 1%"):
        inside = lambda st: (st["cosine"] >= st["cuts"][k][0]) & (st["cosine"] <= st["cuts"][k][1])
        both = inside(sa) & inside(sb)
        print(f"  {k}: {inside(sa).sum()} pairs in {a}, {inside(sb).sum()} in {b}, {both.sum()} in both; "
              f"{both.sum() / inside(sa).sum():.0%} of those of {a} are in the same stratum in {b}")


def frequency(state: dict, cov: np.ndarray, sample: np.ndarray) -> None:
    """The cosine against the (log) rank of the rarer word of the pair, in each space: whether the extremes are a matter of rare words."""
    rank = np.log10(cov[sample].max(axis=1) + 1)
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 2.8), sharey=True)
    for ax, (name, st) in zip(axes, state.items()):
        image = ax.hexbin(rank, st["cosine"], gridsize=60, bins="log", mincnt=1, cmap="viridis")
        for k, (lo, hi) in st["cuts"].items():
            ax.axhspan(lo, hi, color=COLOURS[k], alpha=0.15, lw=0)
        ax.set_title(name, fontsize=8)
        ax.set_ylim(-0.5, 1.0)
        ax.set_xlabel("log10 rank of the rarer word (1 = most frequent)", fontsize=7)
        ax.tick_params(labelsize=6)
        print(f"{name}: Spearman correlation of the cosine with the rank of the rarer word {spearmanr(rank, st['cosine']).statistic:+.3f}")
    axes[0].set_ylabel("cosine", fontsize=7)
    fig.tight_layout()
    base.save(fig, "relation_unlabelled_frequency")


if __name__ == "__main__":
    main()
