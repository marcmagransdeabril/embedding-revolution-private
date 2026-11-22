# SKELETON: written, not yet run together with the author (the experiments of phase one are run step by step); `make test-code` skips it.
"""Goal 1 of the chapter "Meaning as Likeness" (section "The Loss Decides What Is Near"): does the loss decide which likeness is near?

Three losses (SVD of PPMI, SGNS, GloVe) on one text, against two judges of likeness on the same 999 word pairs of SimLex-999, the
similarity rating and the strength of free association (USF), and against the 353 pairs of WordSim-353; the unreduced PPMI rows are the
null, the agreement between raters is the ceiling, and three seeds give the noise. Expectation (written before the run, see the chapter):
the three losses agree with each other, they agree with the judge of association more than with the judge of similarity, and all stay
below the ceiling. Also run: the same comparison for growing amounts of text (counting model only), since "use" is a claim about quantity.
Prints the numbers and a verdict for each part of the expectation, saves results/loss_agreement.json and
figures/meaning_as_likeness/loss_agreement.png.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import sparse

import spaces
import utils

SEEDS = (0, 1, 2)
METHODS = {"counting (SVD of PPMI)": "ppmi_svd", "predicting (SGNS)": "sgns", "weighted least squares (GloVe)": "glove"}
SIMLEX_CEILING = 0.67  # Hill, Reichart and Korhonen (2015), p. 11: average pairwise Spearman correlation of the raters


def judged(pairs, columns):
    """The judge columns as arrays, in the order of the pairs."""
    return {name: np.array([p[col] for p in pairs]) for name, col in columns.items()}


def ppmi_row_scores(ppmi: sparse.csr_matrix, index, pairs):
    """Cosine of the unreduced PPMI rows (the null: the same counts with no reduction)."""
    keep = np.array([i for i, p in enumerate(pairs) if p[0] in index and p[1] in index])
    a = ppmi[[index[pairs[i][0]] for i in keep]]
    b = ppmi[[index[pairs[i][1]] for i in keep]]
    num = np.asarray(a.multiply(b).sum(axis=1)).ravel()
    den = np.sqrt(np.asarray(a.multiply(a).sum(axis=1)).ravel() * np.asarray(b.multiply(b).sum(axis=1)).ravel())
    return np.divide(num, den, out=np.zeros_like(num), where=den > 0), keep


def main() -> None:
    vocab, index, counts = utils.load_vocab()
    simlex = utils.load_simlex()
    ws, ratings = utils.load_ws353()
    judges = {"SimLex similarity": (simlex, 2), "SimLex association (USF)": (simlex, 3), "WordSim-353": (ws, 2)}
    ws_one_vs_rest, ws_pairwise = utils.ceiling(ratings)
    print(f"ceilings: WordSim-353 one rater against the mean of the others {ws_one_vs_rest:.3f}, mean pairwise {ws_pairwise:.3f}; "
          f"SimLex-999 mean pairwise {SIMLEX_CEILING} (from the paper)\n")

    ppmi = sparse.load_npz(utils.cached("ppmi_full", "npz"))
    results: dict = {"ceiling": {"WordSim-353 one-vs-rest": ws_one_vs_rest, "WordSim-353 pairwise": ws_pairwise, "SimLex pairwise": SIMLEX_CEILING}}
    table: dict[str, dict[str, list[float]]] = {}
    for label, prefix in METHODS.items():
        table[label] = {j: [] for j in judges}
        for seed in SEEDS:
            emb = utils.load_space(f"{prefix}_s{seed}")
            for j, (pairs, col) in judges.items():
                score, keep = utils.pair_scores(emb, index, pairs)
                table[label][j].append(float(utils.spearmanr(score, np.array([pairs[i][col] for i in keep])).statistic))
    table["unreduced PPMI rows (null)"] = {}
    for j, (pairs, col) in judges.items():
        score, keep = ppmi_row_scores(ppmi, index, pairs)
        table["unreduced PPMI rows (null)"][j] = [float(utils.spearmanr(score, np.array([pairs[i][col] for i in keep])).statistic)]

    def cell(v: list[float]) -> str:
        return f"{v[0]:.3f}" if len(v) == 1 else f"{np.mean(v):.3f} ({np.min(v):.3f}-{np.max(v):.3f})"

    print(f"{'Spearman rho with the judge':36s}" + "".join(f"{j:>28s}" for j in judges))
    for label, row in table.items():
        print(f"{label:36s}" + "".join(f"{cell(v):>28s}" for v in row.values()))
    results["spearman"] = {label: {j: v for j, v in row.items()} for label, row in table.items()}

    # agreement between the losses on random pairs of the 10,000 most frequent words, and seed against seed
    rng = np.random.default_rng(0)
    a, b = rng.integers(0, 10_000, 200_000), rng.integers(0, 10_000, 200_000)
    keep = a != b
    a, b = a[keep], b[keep]

    def cos(emb):
        u = utils.unit(emb)
        return (u[a] * u[b]).sum(axis=1)

    scores = {f"{p}_s{s}": cos(utils.load_space(f"{p}_s{s}")) for p in METHODS.values() for s in SEEDS}
    names = list(METHODS.values())
    cross = np.array([[utils.spearmanr(scores[f"{x}_s0"], scores[f"{y}_s0"]).statistic for y in names] for x in names])
    seed_gap = {p: float(np.mean([utils.spearmanr(scores[f"{p}_s{i}"], scores[f"{p}_s{j}"]).statistic for i in SEEDS for j in SEEDS if i < j])) for p in names}
    print("\nagreement of the cosines on 200,000 random pairs (Spearman), losses against each other (seed 0):")
    print("                    " + "".join(f"{n:>12s}" for n in names))
    for n, row in zip(names, cross):
        print(f"{n:20s}" + "".join(f"{v:>12.3f}" for v in row))
    print("seed against seed within a loss:", {k: round(v, 3) for k, v in seed_gap.items()})
    results["agreement_between_losses"] = {x: {y: float(cross[i, j]) for j, y in enumerate(names)} for i, x in enumerate(names)}
    results["agreement_between_seeds"] = seed_gap

    # amount of text: counting model on the first fraction of the text
    words = utils.load_text8()
    _, ids = utils.build_vocab(words, len(vocab))  # same vocabulary as the trained spaces (rebuilt from the same text)
    growth = {}
    for frac in (0.01, 0.03, 0.1, 0.3, 1.0):
        part = ids[: int(len(ids) * frac)]
        emb = spaces.ppmi_svd(utils.ppmi(utils.cooccurrence(part, len(vocab), 5)), 100, 0)
        growth[frac] = {}
        for j, (pairs, col) in judges.items():
            score, keep = utils.pair_scores(emb, index, pairs)
            growth[frac][j] = float(utils.spearmanr(score, np.array([pairs[i][col] for i in keep])).statistic)
        print(f"text fraction {frac:5.2f} ({len(part):>10,} words): " + ", ".join(f"{j} {v:.3f}" for j, v in growth[frac].items()))
    results["amount_of_text"] = {str(k): v for k, v in growth.items()}

    # verdicts on the expectation
    print("\nverdicts on the expectation of goal 1")
    off_diag = cross[np.triu_indices(3, 1)]
    best_judge = max(np.mean(v) for lab, row in table.items() if "null" not in lab for j, v in row.items() if j != "SimLex association (USF)")
    print(f"  the three losses agree with each other: rho between {off_diag.min():.2f} and {off_diag.max():.2f} (seed against seed: {min(seed_gap.values()):.2f} to {max(seed_gap.values()):.2f})")
    for label, row in table.items():
        if "null" in label:
            continue
        sim, assoc = np.mean(row["SimLex similarity"]), np.mean(row["SimLex association (USF)"])
        print(f"  {label}: association {assoc:.3f} {'>' if assoc > sim else '<='} similarity {sim:.3f}")
    print(f"  best score against any judge {best_judge:.3f}; ceilings {SIMLEX_CEILING} (SimLex, pairwise) and {ws_one_vs_rest:.2f} (WordSim-353, one rater against the others)")
    utils.save_results("loss_agreement", results)

    utils.FIGURES.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 3.6))
    labels = [l for l in table if "null" not in l] + ["unreduced PPMI rows (null)"]
    width = 0.8 / len(judges)
    for k, j in enumerate(judges):
        means = [np.mean(table[l][j]) for l in labels]
        errs = [np.std(table[l][j]) if len(table[l][j]) > 1 else 0 for l in labels]
        ax.bar(np.arange(len(labels)) + k * width, means, width, yerr=errs, label=j)
    ax.axhline(SIMLEX_CEILING, color="k", ls="--", lw=1, label="SimLex ceiling (pairwise raters)")
    ax.set_xticks(np.arange(len(labels)) + width)
    ax.set_xticklabels([l.replace(" (", "\n(") for l in labels], fontsize=7)
    ax.set_ylabel("Spearman correlation with the judge")
    ax.legend(fontsize=6)
    fig.tight_layout()
    fig.savefig(utils.FIGURES / "loss_agreement.png", dpi=200)


if __name__ == "__main__":
    main()
