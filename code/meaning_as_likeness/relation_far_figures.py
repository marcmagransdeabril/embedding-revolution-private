"""The figure of the section "Is Any Relation Associated with Far Pairs?" (see relation_far.py, which computes what it shows), drawn at the
width of the text block of the book (6.5 inches). Nothing is computed here."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import relation_collapse_figures as base


def ratios(result: dict, names: list[str]) -> None:
    """For each relation, the ratio of its share of pairs below the 5th percentile cut (left) and below zero (right) to the share of the
    null under the same cut, in each space, with the bootstrap interval. The dashed line at 1 is a relation that is no more frequent
    among far pairs than pairs in general."""
    spaces = list(result["spaces"])
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 3.6), sharey=True)
    y = np.arange(len(names))[::-1]
    for ax, cut in zip(axes, ("5th percentile", "below zero")):
        for k, s in enumerate(spaces):
            est = [result["spaces"][s]["ratio"][cut][n] for n in names]
            ax.errorbar([e[0] for e in est], y + (k - 0.5) * 0.3, xerr=base.errors(est), fmt="o", ms=3, capsize=2, label=s)
        ax.axvline(1, color="black", lw=0.6, ls="--")
        ax.set_title(f"pairs {cut}" if cut.startswith("below") else f"pairs below the {cut} of the null", fontsize=7)
        ax.set_xlabel("share of the relation / share of the null", fontsize=7)
        ax.tick_params(labelsize=6)
    axes[0].set_yticks(y, [f"{n} ({result['pairs'][n]:,})" for n in names], fontsize=6)
    axes[0].legend(fontsize=6, loc="center right")
    base.save(fig, "relation_far")
