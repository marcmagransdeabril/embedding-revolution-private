# SKELETON: written, not yet run together with the author (the experiments of phase one are run step by step); `make test-code` skips it.
"""Goal 2 of the chapter "Meaning as Likeness" (section "Similar, Related or Associated?"): which relation does the cosine of a space follow?

The 999 pairs of SimLex-999 are cut into the four cells of the two independent judges, the similarity rating and the strength of free
association (USF): high on both (doctor, nurse), similar only (horse, platypus), associated only (cradle, baby), and low on both
(calculus, candy). "High" is the top third of the judge and "low" the bottom third, since nearly every pair of SimLex has a non-zero USF
strength (the pairs were drawn from USF), so a cut at zero leaves the cell "similar, not associated" almost empty. The score of a cell is
the mean cosine of its pairs, and the same after the part of the cosine that follows the frequency of the two words (a linear fit on
their log counts) is removed. Expectation (written before the run): a space of company puts the associated-only cell above the
similar-only cell, the "both" cell highest and the "neither" cell lowest, so it follows relatedness (either relation) and leans to
association; the claim is read from the order of the four cells and from the interval of the difference between the two single cells.
Prints the numbers and a verdict, saves results/relation_split.json.
"""
from __future__ import annotations

import numpy as np

import utils

SPACES = {"counting (SVD of PPMI)": "ppmi_svd", "predicting (SGNS)": "sgns", "weighted least squares (GloVe)": "glove"}
CELLS = ("both", "similar only", "associated only", "neither")
THIRD = 1 / 3


def cells(similarity: np.ndarray, association: np.ndarray) -> dict[str, np.ndarray]:
    """Boolean mask of each of the four cells: top third against bottom third of each judge."""
    hi_s, lo_s = similarity >= np.quantile(similarity, 1 - THIRD), similarity <= np.quantile(similarity, THIRD)
    hi_a, lo_a = association >= np.quantile(association, 1 - THIRD), association <= np.quantile(association, THIRD)
    return {"both": hi_s & hi_a, "similar only": hi_s & lo_a, "associated only": lo_s & hi_a, "neither": lo_s & lo_a}


def frequency_residual(score: np.ndarray, log_freq: np.ndarray) -> np.ndarray:
    """What is left of the score after a linear fit on the log counts of the two words of the pair."""
    design = np.column_stack([np.ones(len(score)), log_freq])
    coef, *_ = np.linalg.lstsq(design, score, rcond=None)
    return score - design @ coef


def difference_interval(values: np.ndarray, a: np.ndarray, b: np.ndarray, resamples: int = 1000, seed: int = 0) -> tuple[float, float, float]:
    """Mean of cell `a` minus mean of cell `b`, with a percentile-bootstrap 95% interval over the pairs of each cell."""
    rng = np.random.default_rng(seed)
    x, y = values[a], values[b]
    diffs = [rng.choice(x, len(x)).mean() - rng.choice(y, len(y)).mean() for _ in range(resamples)]
    low, high = np.percentile(diffs, [2.5, 97.5])
    return float(x.mean() - y.mean()), float(low), float(high)


def main() -> None:
    _, index, counts = utils.load_vocab()
    pairs = utils.load_simlex()
    similarity, association = (np.array([p[c] for p in pairs]) for c in (2, 3))
    results: dict = {}
    for label, prefix in SPACES.items():
        per_seed = [s for s in range(3) if utils.SPACES.joinpath(f"{prefix}_s{s}.npy").exists()]
        if not per_seed:
            continue
        # one score per pair, averaged over the seeds that were trained
        scores = []
        for s in per_seed:
            score, keep = utils.pair_scores(utils.load_space(f"{prefix}_s{s}"), index, pairs)
            scores.append(score)
        score = np.mean(scores, axis=0)
        masks = {name: m[keep] for name, m in cells(similarity, association).items()}
        log_freq = np.log(np.array([[counts[index[pairs[i][0]]], counts[index[pairs[i][1]]]] for i in keep], dtype=float))
        residual = frequency_residual(score, log_freq)
        row = {name: {"n": int(m.sum()), "mean_cosine": float(score[m].mean()), "mean_residual": float(residual[m].mean()),
                      "mean_log_count": float(log_freq[m].mean())} for name, m in masks.items()}
        diff = difference_interval(residual, masks["associated only"], masks["similar only"])
        row["associated_only_minus_similar_only_residual"] = {"difference": diff[0], "low": diff[1], "high": diff[2]}
        results[label] = row

        print(f"\n{label} ({len(per_seed)} seed(s), {len(keep)} pairs in the vocabulary)")
        print(f"  {'cell':18s}{'n':>5s}{'mean cosine':>13s}{'after frequency':>17s}{'mean log count':>16s}")
        for name in CELLS:
            r = row[name]
            print(f"  {name:18s}{r['n']:>5d}{r['mean_cosine']:>13.3f}{r['mean_residual']:>+17.3f}{r['mean_log_count']:>16.2f}")
        order = sorted(CELLS, key=lambda n: -row[n]["mean_residual"])
        print(f"  order after frequency: {' > '.join(order)}")
        print(f"  associated only minus similar only: {diff[0]:+.3f} [{diff[1]:+.3f}, {diff[2]:+.3f}]")

    print("\nverdicts on the expectation of goal 2")
    for label, row in results.items():
        d = row["associated_only_minus_similar_only_residual"]
        lean = "association" if d["low"] > 0 else "similarity" if d["high"] < 0 else "no relation (the interval holds zero)"
        top_bottom = row["both"]["mean_residual"] > max(row["similar only"]["mean_residual"], row["associated only"]["mean_residual"]) > \
            min(row["similar only"]["mean_residual"], row["associated only"]["mean_residual"]) > row["neither"]["mean_residual"]
        print(f"  {label}: {"leans to " + lean if lean.startswith(("assoc","simil")) else lean}; 'both' highest and 'neither' lowest: {top_bottom}")
    utils.save_results("relation_split", results)


if __name__ == "__main__":
    main()
