"""Question Q2 of the chapter "Meaning as Likeness" (section "Similar, Related or Associated?"): which relation does the cosine of a
space follow, similarity, association, or relatedness (either of the two)?

Spaces: PPMI-SVD and SGNS of the gallery (text8, 30,000 words, d = 100, seed 0, the gallery seed; the effect of the seed is Q12).
`--spaces` adds GloVe for the section on losses. Judges: the two columns of SimLex-999, the similarity rating and the USF
free-association strength, on the pairs whose two words are in the vocabulary, and WordSim-353 as a judge of relatedness only.

Five tests. (1) The two judges are not independent: their Spearman correlation, and the ceilings of the raters (SimLex-999: 0.67,
average pairwise Spearman, Hill et al. 2015, section 4.1; its file has no individual ratings; WordSim-353: computed from its raters).
(2) The Spearman correlation of the cosine with each judge over all the pairs. (3) The four cells, top and bottom third of each judge
(a cut at zero would leave "similar, not associated" almost empty, since the pairs were drawn from USF): both, similar only,
associated only, neither; the mean cosine of each and the differences between cells, against the mean cosine of all pairs of the
vocabulary (the null of the gallery). (4) The same after the cosine expected from the frequencies alone is removed: a linear fit of the
cosine on the lower and the higher log count of the two words, on 200,000 random pairs of the vocabulary, so that random pairs have a
mean residual of zero and the null of (4) is zero. Every interval is a 95% percentile bootstrap over the words of the judged pairs
(1,000 resamples), since SimLex reuses its words across pairs; the frequency fit is held fixed. The cut at quartiles is printed as a
robustness line. (5) The cut keeps 465 of the 960 pairs, and each single cell 70 to 77, so a gap of 0.05 between the two single cells is
not resolved; the fifth test uses all the pairs: the partial Spearman correlation of the cosine with each judge, the rank of the other judge
held fixed, and the paired difference association minus similarity, for the cosine and for the residual of (4).

Predicted orders. Similarity: similar only > associated only, and associated only = neither. Association: the reverse. Relatedness:
both > each single cell > neither, and no clear gap between the two single cells. "Both > neither" holds under all three.
Expectation (written before the run): relatedness, with a lean to association.

Prints every number and a verdict per space; saves results/relation_split.json and the figures relation_split_judges.png,
relation_split_spearman.png, relation_split_cells.png and relation_split_residual.png (drawn by relation_split_figures.py).
"""
from __future__ import annotations

import argparse

import numpy as np

import relation_split_figures as figures
import utils

ALL_SPACES = {"PPMI-SVD": "ppmi_svd_s0", "SGNS": "sgns_s0", "GloVe": "glove_s0"}
GALLERY = ["PPMI-SVD", "SGNS"]
CELLS = ("both", "similar only", "associated only", "neither")
# the differences that tell the three readings apart (first cell minus second)
CONTRASTS = (("associated only", "similar only"), ("similar only", "neither"), ("associated only", "neither"),
             ("both", "similar only"), ("both", "associated only"))
SIMLEX_CEILING = 0.67  # average pairwise Spearman of the SimLex-999 raters [@hill2015simlex, section 4.1]
RANDOM_PAIRS, RESAMPLES = 200_000, 1000


def fmt(estimate: tuple[float, float, float], sign: str = "") -> str:
    """A number with its bootstrap interval, as it is printed everywhere."""
    return f"{estimate[0]:{sign}.3f} [{estimate[1]:{sign}.3f}, {estimate[2]:{sign}.3f}]"


def cells(similarity: np.ndarray, association: np.ndarray, share: float) -> dict[str, np.ndarray]:
    """Boolean mask of each of the four cells: top `share` against bottom `share` of each judge."""
    hi_s, lo_s = similarity >= np.quantile(similarity, 1 - share), similarity <= np.quantile(similarity, share)
    hi_a, lo_a = association >= np.quantile(association, 1 - share), association <= np.quantile(association, share)
    return {"both": hi_s & hi_a, "similar only": hi_s & lo_a, "associated only": lo_s & hi_a, "neither": lo_s & lo_a}


def frequency_features(log_counts: np.ndarray) -> np.ndarray:
    """Design matrix of a pair from the log counts of its two words (n x 2): intercept, lower and higher log count (order-free)."""
    return np.column_stack([np.ones(len(log_counts)), log_counts.min(axis=1), log_counts.max(axis=1)])


def frequency_fit(u: np.ndarray, log_counts: np.ndarray, seed: int = 0) -> tuple[np.ndarray, float]:
    """Least-squares coefficients of the cosine of random pairs of distinct words on their log counts, and the R^2 of the fit."""
    rng = np.random.default_rng(seed)
    a = rng.integers(0, len(u), RANDOM_PAIRS)
    b = (a + rng.integers(1, len(u), RANDOM_PAIRS)) % len(u)  # never the word itself
    cosine = (u[a] * u[b]).sum(axis=1)
    design = frequency_features(np.column_stack([log_counts[a], log_counts[b]]))
    coef, *_ = np.linalg.lstsq(design, cosine, rcond=None)
    residual = cosine - design @ coef
    return coef, float(1 - residual.var() / cosine.var())


def score_cells(values: np.ndarray, masks: dict[str, np.ndarray], word_pairs: np.ndarray) -> dict:
    """Mean of `values` in each cell and the contrasts between cells, each with its interval over the words."""
    mean_in = lambda m: (lambda w: utils.weighted_mean(values[m], w[m]))
    out = {name: {"n": int(m.sum()), "mean": utils.bootstrap_words(word_pairs, mean_in(m), RESAMPLES)} for name, m in masks.items()}
    for a, b in CONTRASTS:
        diff = lambda w, a=a, b=b: mean_in(masks[a])(w) - mean_in(masks[b])(w)
        out[f"{a} - {b}"] = utils.bootstrap_words(word_pairs, diff, RESAMPLES)  # same seed: the same resamples for every contrast
    return out


def reading(row: dict) -> str:
    """Which predicted order the cells follow, read from the intervals of the contrasts."""
    # interval of a - b, from the contrast stored in either order
    interval = lambda a, b: row[f"{a} - {b}"][1:] if f"{a} - {b}" in row else [-x for x in row[f"{b} - {a}"][:0:-1]]
    above = lambda a, b: interval(a, b)[0] > 0
    below = lambda a, b: interval(a, b)[1] < 0
    level = lambda a, b: not above(a, b) and not below(a, b)
    if above("similar only", "associated only") and level("associated only", "neither"):
        return "similarity"
    if above("associated only", "similar only") and level("similar only", "neither"):
        return "association"
    singles = above("similar only", "neither") and above("associated only", "neither")
    if not singles:
        return "none of the three predicted orders"
    lean = ("no lean between similarity and association" if level("associated only", "similar only") else
            f"leaning to {'association' if above('associated only', 'similar only') else 'similarity'}")
    both = "both above each single cell" if above("both", "similar only") and above("both", "associated only") else \
        "both not clearly above each single cell"
    return f"relatedness ({lean}; {both})"


def print_cells(title: str, row: dict, null: float) -> None:
    print(f"  {title} (null: {null:+.3f})")
    for name in CELLS:
        print(f"    {name:16s} n = {row[name]['n']:3d}   {fmt(row[name]['mean'], '+')}")
    for a, b in CONTRASTS:
        print(f"    {a} - {b}: {fmt(row[f'{a} - {b}'], '+')}")
    order = sorted(CELLS, key=lambda n: -row[n]["mean"][0])
    print(f"    order: {' > '.join(order)}; reading: {reading(row)}")


def judges(similarity: np.ndarray, association: np.ndarray, word_pairs: np.ndarray, ws_ratings: np.ndarray) -> dict:
    """Test 1: the correlation of the two judges of SimLex-999, and the ceilings of the raters."""
    rho = utils.bootstrap_words(word_pairs, lambda w: utils.weighted_spearman(similarity, association, w), RESAMPLES)
    ws_one_vs_rest, ws_pairwise = utils.ceiling(ws_ratings)
    print(f"test 1: Spearman of similarity and association over {len(word_pairs)} SimLex-999 pairs in the vocabulary "
          f"({len(ws_ratings)} WordSim-353 pairs): {fmt(rho)}")
    print(f"  pairs with zero association: {int((association == 0).sum())}")
    print(f"  ceilings: SimLex-999 {SIMLEX_CEILING:.2f} (cited, average pairwise); WordSim-353 {ws_pairwise:.3f} (average pairwise, "
          f"0.61 in Hill et al.), {ws_one_vs_rest:.3f} (one rater against the mean of the others)")
    return {"rho": rho, "pairs": len(word_pairs), "ws353_pairs": len(ws_ratings), "zero_association": int((association == 0).sum()),
            "ceiling": {"simlex_pairwise": SIMLEX_CEILING, "ws353_pairwise": ws_pairwise, "ws353_one_vs_rest": ws_one_vs_rest}}


def check_claims(results: dict) -> None:
    """The claims that the section makes about the two gallery spaces; a failure means the text has to change."""
    assert 0 < results["judges"]["rho"][1], "the two judges are correlated"
    for name, row in results["spaces"].items():
        for kind in ("cosine", "residual"):
            assert reading(row[kind]).startswith("relatedness (no lean"), f"{name}, {kind}: the order is no longer relatedness"
        assert row["frequency_fit"]["r2"] < 0.1, f"{name}: frequency explains little of the cosine of random pairs"
        gap = row["spearman_association_minus_similarity"]
        assert gap[1] < 0 < gap[2], f"{name}: the whole-set correlations no longer hold zero between them"
        for kind in ("cosine", "residual"):
            part = row["partial_spearman"][kind]
            assert part["similarity"][1] > 0 and part["association"][1] > 0, f"{name}, {kind}: each judge keeps a partial correlation"
            assert part["association minus similarity"][1] < 0 < part["association minus similarity"][2], \
                f"{name}, {kind}: the partial correlations no longer hold zero between them"


def main(names: list[str]) -> None:
    _, index, counts = utils.load_vocab()
    log_counts = np.log(counts.astype(float))
    simlex = utils.load_simlex()
    ws_pairs, ws_ratings = utils.load_ws353()
    keep = [i for i, p in enumerate(simlex) if p[0] in index and p[1] in index]
    word_pairs = np.array([[index[simlex[i][0]], index[simlex[i][1]]] for i in keep])
    similarity, association = (np.array([simlex[i][c] for i in keep]) for c in (2, 3))
    ws_keep = [i for i, p in enumerate(ws_pairs) if p[0] in index and p[1] in index]
    ws_words = np.array([[index[ws_pairs[i][0]], index[ws_pairs[i][1]]] for i in ws_keep])
    relatedness = np.array([ws_pairs[i][2] for i in ws_keep])

    results: dict = {"judges": judges(similarity, association, word_pairs, ws_ratings[ws_keep]), "spaces": {}}
    masks = cells(similarity, association, 1 / 3)
    quartiles = cells(similarity, association, 1 / 4)
    results["thresholds"] = {judge: [float(np.quantile(v, 1 / 3)), float(np.quantile(v, 2 / 3))]
                             for judge, v in (("similarity", similarity), ("association", association))}
    pair_cosine = lambda u, w: (u[w[:, 0]] * u[w[:, 1]]).sum(axis=1)
    for name in names:
        u = utils.unit(utils.load_space(ALL_SPACES[name]))
        cosine, ws_cosine = pair_cosine(u, word_pairs), pair_cosine(u, ws_words)
        coef, r2 = frequency_fit(u, log_counts)
        residual = cosine - frequency_features(log_counts[word_pairs]) @ coef
        spearman = {judge: utils.bootstrap_words(w, lambda x, s=s, j=j: utils.weighted_spearman(s, j, x), RESAMPLES)
                    for judge, w, s, j in (("similarity", word_pairs, cosine, similarity),
                                           ("association", word_pairs, cosine, association),
                                           ("relatedness (WordSim-353)", ws_words, ws_cosine, relatedness))}
        # paired: the same resamples of the same pairs for the two judges of SimLex-999
        gap = utils.bootstrap_words(word_pairs, lambda x: utils.weighted_spearman(cosine, association, x)
                                    - utils.weighted_spearman(cosine, similarity, x), RESAMPLES)
        partial = {}
        for kind, values in (("cosine", cosine), ("residual", residual)):
            part = {judge: utils.bootstrap_words(word_pairs, lambda x, j=j, o=o: utils.weighted_partial_spearman(values, j, o, x), RESAMPLES)
                    for judge, j, o in (("similarity", similarity, association), ("association", association, similarity))}
            part["association minus similarity"] = utils.bootstrap_words(
                word_pairs, lambda x: utils.weighted_partial_spearman(values, association, similarity, x)
                - utils.weighted_partial_spearman(values, similarity, association, x), RESAMPLES)
            partial[kind] = part
        row = {"partial_spearman": partial, "null_cosine": utils.mean_cosine(u), "frequency_fit": {"coef": coef.tolist(), "r2": r2}, "spearman": spearman,
               "spearman_association_minus_similarity": gap,
               "cosine": score_cells(cosine, masks, word_pairs), "residual": score_cells(residual, masks, word_pairs),
               "quartiles": {"cosine": score_cells(cosine, quartiles, word_pairs),
                             "residual": score_cells(residual, quartiles, word_pairs)}}
        results["spaces"][name] = row

        print(f"\n{name}")
        print("  test 2: Spearman of the cosine with " + "; ".join(f"{j} {fmt(v)}" for j, v in spearman.items()))
        print(f"    association minus similarity (paired): {fmt(gap, '+')}")
        print_cells("test 3: mean cosine per cell", row["cosine"], row["null_cosine"])
        print(f"  frequency fit on {RANDOM_PAIRS:,} random pairs: cosine = {coef[0]:+.3f} {coef[1]:+.4f} lower log count "
              f"{coef[2]:+.4f} higher log count, R^2 = {r2:.3f}")
        for kind, part in partial.items():
            print(f"  test 5: partial Spearman of the {kind} with " + "; ".join(f"{j} {fmt(v, '+')}" for j, v in part.items()))
        print_cells("test 4: mean residual per cell", row["residual"], 0.0)
        for kind in ("cosine", "residual"):
            q = row["quartiles"][kind]
            print(f"  quartiles, {kind}: n = {[q[c]['n'] for c in CELLS]}, associated only - similar only "
                  f"{fmt(q['associated only - similar only'], '+')}; reading: {reading(q)}")

    print("\nverdicts on the expectation (relatedness, leaning to association)")
    for name, row in results["spaces"].items():
        print(f"  {name}: raw cosine: {reading(row['cosine'])}; after frequency: {reading(row['residual'])}")
    suffix = "" if names == GALLERY else "_" + "_".join(n.lower().replace("-", "") for n in names)
    utils.save_results("relation_split" + suffix, results)
    figures.judges(similarity, association, results["thresholds"], results["judges"]["rho"], suffix)
    figures.spearman(results, suffix)
    figures.cells(results, "cosine", suffix)
    figures.cells(results, "residual", suffix)
    if names == GALLERY:
        check_claims(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--spaces", nargs="+", choices=list(ALL_SPACES), default=GALLERY)
    main(parser.parse_args().spaces)
