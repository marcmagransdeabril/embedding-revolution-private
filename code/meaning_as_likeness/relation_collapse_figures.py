"""The figures of the section "Which Relations Does Nearness Tell Apart?" (see relation_collapse.py, which computes what they
show), drawn at the width of the text block of the book (6.5 inches). Nothing is computed here."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import utils

# What each relation rests on: the letters it shares, the sense a dictionary records, what only an encyclopedia knows.
GROUPS = {
    "form": ["inflection", "derivation"],
    "sense": ["synonym", "antonym", "hypernym", "co-hyponym", "meronym"],
    "world": ["encyclopedic"],
}
GROUP_COLORS = {"form": "tab:green", "sense": "tab:brown", "world": "tab:cyan"}  # not the blue and orange of the spaces
GROUP_NAMES = {"form": "form", "sense": "sense (lexicon)", "world": "world knowledge"}


def group_of(label: str) -> str | None:
    """The group of a relation, or None for a label that is not a relation (a control, 'neither'). A count after the name, as in
    'synonym (15,731)', is ignored."""
    members = {m: g for g, ms in GROUPS.items() for m in ms}
    while label not in members and " (" in label:
        label = label.rsplit(" (", 1)[0]
    return members.get(label)


def by_group(names: list[str]) -> list[str]:
    """The names with the relations of one group together, in the order of GROUPS; the other labels keep their place at the end."""
    order = list(GROUPS)
    return sorted(names, key=lambda n: order.index(group_of(n)) if group_of(n) else len(order))


def color_ticks(labels) -> None:
    """Color each tick label by the group of its relation."""
    for text in labels:
        g = group_of(text.get_text())
        if g:
            text.set_color(GROUP_COLORS[g])


def group_legend(ax, **kwargs):
    """A legend of the four groups, to be added next to another legend with add_artist."""
    handles = [plt.Line2D([], [], marker="s", ls="", color=GROUP_COLORS[g], label=GROUP_NAMES[g]) for g in GROUPS]
    return ax.legend(handles=handles, title="relation rests on", fontsize=6, title_fontsize=6, **kwargs)


def save(fig, name: str) -> None:
    utils.FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(utils.FIGURES / f"{name}.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def errors(estimates: list) -> np.ndarray:
    """Error bars (2 x n) from (point, low, high) triples."""
    return np.array([[e[0] - e[1], e[2] - e[0]] for e in estimates]).T


def against_neither(results: dict) -> None:
    """Test 1: the probability that a pair of each relation is nearer than a pair of neither, in each space, with its interval."""
    spaces = list(results["spaces"])
    names = by_group(list(results["spaces"][spaces[0]]["against_neither"]))
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    y = np.arange(len(names))[::-1]
    for k, s in enumerate(spaces):
        est = [results["spaces"][s]["against_neither"][n] for n in names]
        ax.errorbar([e[0] for e in est], y + (k - 0.5) * 0.3, xerr=errors(est), fmt="o", ms=3, capsize=2, label=s)
    ax.axvline(0.5, color="black", lw=0.6, ls="--")
    ax.set_yticks(y, [f"{n} ({results['pairs'][n]:,})" for n in names], fontsize=6.5)
    ax.set_xlabel("probability that a pair of the relation is nearer than a pair of no relation", fontsize=8)
    color_ticks(ax.get_yticklabels())
    spaces_legend = ax.legend(fontsize=6, loc="lower right")
    group_legend(ax, loc="upper left")
    ax.add_artist(spaces_legend)
    save(fig, "relation_collapse_auc")


def inventory(all_pairs: dict, cosines: dict, labels: list[str], relations: list[str], chance: str) -> None:
    """Test 1: the number of pairs of the vocabulary with each label (top, exact counts, logarithmic scale), and for each relation
    the distribution of the cosine of its pairs in each space (below, solid) against that of the pairs of no relation (dotted); a density, so that
    sets of very different sizes can be compared."""
    spaces = list(cosines["spaces"])
    fig = plt.figure(figsize=(6.5, 7.2))
    grid = fig.add_gridspec(3, 4, height_ratios=[1.1, 1, 1], hspace=0.7, wspace=0.35)
    top = fig.add_subplot(grid[0, :])
    top.bar(range(len(labels)), [all_pairs["labels"][label] for label in labels], 0.6, color="grey")
    top.set_yscale("log")
    top.set_ylabel("number of pairs", fontsize=8)
    top.set_xticks(range(len(labels)), [l.replace(" (", "\n(") for l in labels], fontsize=6, rotation=30, ha="right")
    top.tick_params(axis="y", labelsize=6)
    color_ticks(top.get_xticklabels())
    merge = 20  # bins of 0.02 in the cosine, out of 0.001
    centres = -1 + (np.arange(cosines["bins"] // merge) + 0.5) * 2 * merge / cosines["bins"]
    density = lambda h: np.add.reduceat(np.array(h, dtype=float), np.arange(0, cosines["bins"], merge)) / (sum(h) * 2 * merge / cosines["bins"])
    for k, name in enumerate(relations):
        ax = fig.add_subplot(grid[1 + k // 4, k % 4])
        for color, s in zip(("tab:blue", "tab:orange"), spaces):
            ax.plot(centres, density(cosines["spaces"][s][name]), color=color, lw=1, label=s)
            ax.plot(centres, density(cosines["spaces"][s][chance]), color=color, lw=0.9, ls=":", label=f"no relation, {s}")
        ax.set_xlim(-0.4, 1.0)
        ax.set_title(name, fontsize=7, color=GROUP_COLORS[group_of(name)])
        ax.tick_params(labelsize=5)
        if k // 4 == 1:
            ax.set_xlabel("cosine", fontsize=6)
        if k % 4 == 0:
            ax.set_ylabel("density", fontsize=6)
    fig.legend(*ax.get_legend_handles_labels(), fontsize=6, loc="lower center", ncol=4, frameon=False)
    save(fig, "relation_collapse_inventory")
