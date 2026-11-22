# SKELETON: written, not yet run together with the author (the experiments of phase one are run step by step); `make test-code` skips it.
"""Goal 5 of the chapter "Meaning as Likeness" (section "Many Runs, Many Spaces"): what survives a change of seed, of loss and of text,
and a part of the text removed?

Expectation (written before the run): seeds differ least, losses more and texts most; removing a part of the text that does not mention a
word moves its neighbours no more than a change of text does; and only the local neighbourhood survives all of them (the overlap of the
nearest neighbours is higher than the agreement of the global geometry). The measure is a rotation-invariant one, the overlap of the k nearest
neighbours of 2,000 words, with the seed gap as the noise floor; the global geometry is the Spearman correlation of the cosines of 200,000
random pairs. Prints the numbers and verdicts, saves results/stability.json and figures/meaning_as_likeness/stability.png.
"""
from __future__ import annotations

import itertools

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import utils

METHODS = {"counting": "ppmi_svd", "predicting": "sgns", "least squares": "glove"}
KS = (1, 5, 10, 50)
rng = np.random.default_rng(0)


def comparisons() -> dict[str, list[tuple[str, str]]]:
    c: dict[str, list[tuple[str, str]]] = {"seed": [], "loss": [], "text half": [], "text with 10% removed": []}
    for p in METHODS.values():
        c["seed"] += [(f"{p}_s{i}", f"{p}_s{j}") for i, j in itertools.combinations(range(3), 2)]
        c["text half"].append((f"{p}_A", f"{p}_B"))
    c["loss"] = [(f"{x}_s0", f"{y}_s0") for x, y in itertools.combinations(METHODS.values(), 2)]
    c["text with 10% removed"] = [("ppmi_svd_s0", "ppmi_svd_drop10")]
    return c


def main() -> None:
    vocab, index, counts = utils.load_vocab()
    queries = np.sort(rng.choice(np.arange(200, 10_000), 2000, replace=False))
    removed = np.load(utils.cached("removed_counts", "npy"))
    a, b = rng.integers(0, 10_000, 200_000), rng.integers(0, 10_000, 200_000)
    ok = a != b
    a, b = a[ok], b[ok]
    cache: dict[str, tuple] = {}

    def neighbours(name: str):
        if name not in cache:
            emb = utils.load_space(name)
            u = utils.unit(emb)
            cache[name] = (utils.nearest(emb, queries, max(KS)), (u[a] * u[b]).sum(axis=1))
        return cache[name]

    results: dict = {}
    print("overlap of the k nearest neighbours of 2,000 words (mean over words), and agreement of the global geometry (rho of 200,000 cosines)")
    summary: dict[str, dict[int, float]] = {}
    for kind, pairs in comparisons().items():
        rows = {k: [] for k in KS}
        rsa = []
        for x, y in pairs:
            (nx, sx), (ny, sy) = neighbours(x), neighbours(y)
            for k in KS:
                rows[k].append(utils.neighbour_overlap(nx[:, :k], ny[:, :k]))
            rsa.append(float(utils.spearmanr(sx, sy).statistic))
        mean = {k: float(np.mean(rows[k])) for k in KS}
        summary[kind] = mean
        results[kind] = {"overlap": {str(k): mean[k] for k in KS}, "global_rho": float(np.mean(rsa)), "comparisons": [f"{x} vs {y}" for x, y in pairs]}
        print(f"  {kind:24s} " + "  ".join(f"k={k}: {mean[k]:.3f}" for k in KS) + f"   global rho {np.mean(rsa):.3f}   ({len(pairs)} comparison(s))")

    # the removed part: words that do not occur in it, against words that do
    (nx, _), (ny, _) = neighbours("ppmi_svd_s0"), neighbours("ppmi_svd_drop10")
    seed_floor = float(np.mean([utils.neighbour_overlap(neighbours(f"ppmi_svd_s{i}")[0][:, :10], neighbours(f"ppmi_svd_s{j}")[0][:, :10]).mean() for i, j in itertools.combinations(range(3), 2)]))
    over = utils.neighbour_overlap(nx[:, :10], ny[:, :10])
    in_removed = removed[queries] > 0
    results["removed_part"] = {"words_not_in_removed_part": int((~in_removed).sum()), "overlap_not_in_removed": float(over[~in_removed].mean()) if (~in_removed).any() else None,
                               "words_in_removed_part": int(in_removed.sum()), "overlap_in_removed": float(over[in_removed].mean()), "seed_floor_counting": seed_floor}
    print(f"\n  counting, 10% of the text removed, k = 10: words that do not occur in the removed part ({(~in_removed).sum()}): "
          f"{results['removed_part']['overlap_not_in_removed']}; words that do ({in_removed.sum()}): {over[in_removed].mean():.3f}; seed floor {seed_floor:.3f}")

    # by frequency of the word
    print("\n  by frequency of the word (terciles of the 2,000 queries), overlap at k = 10:")
    order = np.argsort(counts[queries])[::-1]
    terciles = np.array_split(order, 3)
    results["by_frequency"] = {}
    for kind, pairs in comparisons().items():
        vals = []
        for tert in terciles:
            vals.append(float(np.mean([utils.neighbour_overlap(neighbours(x)[0][tert, :10], neighbours(y)[0][tert, :10]).mean() for x, y in pairs])))
        results["by_frequency"][kind] = vals
        print(f"    {kind:24s} common {vals[0]:.3f}, middle {vals[1]:.3f}, rare {vals[2]:.3f}")

    print("\nverdicts on the expectation of goal 5")
    s10 = {k: v[10] for k, v in summary.items()}
    print(f"  order at k = 10: " + " > ".join(f"{k} {v:.2f}" for k, v in sorted(s10.items(), key=lambda kv: -kv[1])) + "   (expected: seed > loss > text)")
    print(f"  local against global: overlap at k = 10 across the three kinds of change {min(s10.values()):.2f}-{max(s10.values()):.2f}; global rho "
          f"{min(r['global_rho'] for r in results.values() if 'global_rho' in r):.2f}-{max(r['global_rho'] for r in results.values() if 'global_rho' in r):.2f}")
    utils.save_results("stability", results)

    utils.FIGURES.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6, 3.4))
    for kind, mean in summary.items():
        ax.plot(KS, [mean[k] for k in KS], "o-", label=kind)
    ax.set_xscale("log")
    ax.set_xlabel("k nearest neighbours")
    ax.set_ylabel("overlap of the neighbours")
    ax.legend(fontsize=6)
    fig.tight_layout()
    fig.savefig(utils.FIGURES / "stability.png", dpi=200)


if __name__ == "__main__":
    main()
