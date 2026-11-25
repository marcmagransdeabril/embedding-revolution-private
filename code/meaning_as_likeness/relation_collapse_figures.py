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
    ax.set_xlabel("probability that a pair of the relation is nearer than a pair of neither", fontsize=8)
    color_ticks(ax.get_yticklabels())
    spaces_legend = ax.legend(fontsize=6, loc="lower right")
    group_legend(ax, loc="upper left")
    ax.add_artist(spaces_legend)
    save(fig, "relation_collapse_auc")


def matrix(results: dict, relations: list[str]) -> None:
    """Test 2: the probability that a pair of the row relation is nearer than a pair of the column relation, in each space; a cell
    whose interval holds 0.5 (the two relations are collapsed) is marked with a dot."""
    spaces = list(results["spaces"])
    fig, axes = plt.subplots(1, len(spaces), figsize=(6.5, 3.6), sharey=True)
    for ax, s in zip(axes, spaces):
        m = results["spaces"][s]["matrix"]
        point, low, high = (np.array(m[k]) for k in ("point", "low", "high"))
        image = ax.imshow(point, cmap="RdBu_r", vmin=0, vmax=1)
        collapsed = (low <= 0.5) & (high >= 0.5) & ~np.eye(len(relations), dtype=bool)
        rows, cols = np.nonzero(collapsed)
        ax.scatter(cols, rows, s=6, color="black", marker="o")
        ax.set_xticks(range(len(relations)), relations, rotation=90, fontsize=5.5)
        ax.set_yticks(range(len(relations)), relations, fontsize=5.5)
        color_ticks(ax.get_xticklabels())
        color_ticks(ax.get_yticklabels())
        ax.set_title(s, fontsize=8)
    bar = fig.colorbar(image, ax=axes, shrink=0.7)
    bar.set_label("row pair nearer than column pair", fontsize=7)
    bar.ax.tick_params(labelsize=6)
    group_legend(axes[0], loc="upper center", bbox_to_anchor=(1.0, -0.42), ncol=4, frameon=False)
    save(fig, "relation_collapse_matrix")


def inventory(inv: dict, labels: list[str]) -> None:
    """Test 3: the share of the top neighbours of every word with each label, in each space and for random words of the same band."""
    columns = {**inv["spaces"], "same-band control": inv["control"]}
    fig, ax = plt.subplots(figsize=(6.5, 3.0))
    width = 0.8 / len(columns)
    for k, (name, shares) in enumerate(columns.items()):
        est = [shares[label] for label in labels]
        ax.bar(np.arange(len(labels)) + (k - (len(columns) - 1) / 2) * width, [e[0] for e in est], width * 0.9, yerr=errors(est),
               capsize=1.5, label=name, color="lightgrey" if "control" in name else None, edgecolor="grey" if "control" in name else None)
    ax.set_xticks(range(len(labels)), [l.replace(" (", "\n(") for l in labels], fontsize=6, rotation=30, ha="right")
    ax.set_ylabel("share of the neighbours", fontsize=8)
    color_ticks(ax.get_xticklabels())
    ax.legend(fontsize=6)
    save(fig, "relation_collapse_inventory")


def mechanism(mech: dict, relations: list[str]) -> None:
    """Test 4: the effect of each relation on the cosine without and with the first-half context held fixed, in each half-text space."""
    spaces = list(mech["spaces"])
    relations = by_group(relations)
    fig, axes = plt.subplots(1, len(spaces), figsize=(6.5, 3.4), sharey=True)
    y = np.arange(len(relations))[::-1]
    for ax, s in zip(axes, spaces):
        for k, kind in enumerate(("without context", "with context")):
            est = [mech["spaces"][s]["effect"][n][kind] for n in relations]
            ax.errorbar([e[0] for e in est], y + (k - 0.5) * 0.3, xerr=errors(est), fmt="o", ms=3, capsize=2, label=kind)
        ax.axvline(0, color="black", lw=0.6)
        r2 = mech["spaces"][s]["r2_random"]
        ax.set_title(f"{s} (R$^2$ of random pairs: frequency {r2['frequency'][0]:.2f},\nwith context {r2['frequency + context'][0]:.2f})",
                     fontsize=7)
        ax.set_xlabel("effect on the cosine", fontsize=7)
        ax.tick_params(labelsize=6)
    axes[0].set_yticks(y, relations, fontsize=6)
    color_ticks(axes[0].get_yticklabels())
    axes[0].legend(fontsize=6, loc="lower right")
    save(fig, "relation_collapse_mechanism")
