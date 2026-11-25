"""Question Q3 of the chapter "Meaning as Likeness" (section "Is Any Relation Associated with Far Pairs?"): is any named relation more
frequent among far pairs than among pairs in general? relation_collapse.py (Q2) asks which relations are nearer than the pairs of no
relation; this script asks the same of the far end. A relation that nearness does not capture is not a finding (relations are unbounded
in number); a relation that is over-represented among far pairs is, since it would say that the space pushes it apart.

Spaces and relations are those of relation_collapse.py (PPMI-SVD and SGNS, text8, d = 100, seed 0; the seven relations of WordNet 3.0 with
their precedence, and the pairs that BATS adds to them, with its encyclopedic family as an eighth relation), and so are the draws of the words for the bootstrap. The null is the
cosine of the pairs of two WordNet words, all of them (exact histogram of the 1.6 x 10^8 pairs, as in the gallery). "Far" is cut at three
places: below zero, below the 5th percentile and below the 1st percentile of the null. A cut puts a pair "below" when its bin is under the
bin where the cumulative share of the null reaches the quantile (bins are 0.001 wide, so the null share below the cut is printed: it is a
little under the quantile).

Three tests. (1) For each relation, the share of its pairs below each cut and the ratio of that share to the null share under the same cut:
a ratio above 1 (the interval above 1) is a relation associated with far, a ratio below 1 a relation kept away from it. (2) The share of the
pairs of two WordNet words that hold one of the seven WordNet relations, among the pairs below the 1st percentile cut and among all pairs.
(3) The Spearman correlation between the two spaces of the ratio at the 5th percentile cut over the eight relations, to see whether the
two losses keep the same relations away from the far end. Intervals are 95% percentile bootstraps over the words (the null is held fixed).

Expectation (a first run with the same cuts, written for another question, had found no relation below the null at any cut, so this one is
not blind): no relation is associated with far in either space, antonyms included (all ratios below 1, the interval below 1); the far tail
holds a smaller share of related pairs than pairs in general; the relations of kind, with the weakest AUC of Q2, come nearest to a ratio
of 1 and forms of one word and derivations are the farthest from it.

Prints every number; saves results/relation_far.json and the figure relation_far.png (drawn by relation_far_figures.py).
"""
from __future__ import annotations

import numpy as np
from scipy.stats import spearmanr

import gallery
import relation_collapse as rc
import relation_far_figures as figures
import utils

CUTS = {"below zero": None, "5th percentile": 0.05, "1st percentile": 0.01}
ANY = "WordNet (any of seven)"


def cut_bins(null_hist: np.ndarray) -> dict[str, int]:
    """The bin of each cut: pairs whose bin is under it are below the cut (zero is the middle of the cosine range)."""
    cumulative = np.cumsum(null_hist) / null_hist.sum()
    return {name: gallery.BINS // 2 if q is None else int(np.searchsorted(cumulative, q)) for name, q in CUTS.items()}


def wordnet_union(pure: dict, covered: np.ndarray) -> np.ndarray:
    """The pairs of two WordNet words that hold any of the seven relations of WordNet (each once, under its first relation)."""
    return np.concatenate([pure[n][covered[pure[n]].all(axis=1)] for n in rc.WORDNET])


def measure(spaces: dict, pairs: dict, pure: dict, covered: np.ndarray, size: int) -> dict:
    """Tests 1 to 3, with the same draws of the words for every relation and both spaces."""
    judged = {**{n: pairs[n] for n in rc.RELATIONS}, rc.RANDOM: pairs[rc.RANDOM], ANY: wordnet_union(pure, covered)}
    names = list(judged)
    state = {}
    for s, emb in spaces.items():
        _, both = gallery.pair_histograms(emb, covered)
        cuts = cut_bins(both)
        state[s] = {"null": both, "cuts": cuts, "bins": {n: gallery.pair_bins(emb, judged[n]) for n in names},
                    "null_share": {c: float(both[:k].sum() / both.sum()) for c, k in cuts.items()}}
    share = {s: {c: [] for c in CUTS} for s in spaces}
    rates = {s: [] for s in spaces}
    for times in rc.word_draws(size, rc.RESAMPLES):
        for s in spaces:
            st = state[s]
            h = rc.histograms(st["bins"], judged, times, names)
            for c in CUTS:
                share[s][c].append(h[:, : st["cuts"][c]].sum(axis=1) / h.sum(axis=1))
            k, row = st["cuts"]["1st percentile"], names.index(ANY)
            rates[s].append([h[row, :k].sum() / st["null"][:k].sum(), h[row].sum() / st["null"].sum()])
    out = {"pairs": {n: len(judged[n]) for n in names}, "spaces": {}}
    ratio_draws = {}
    for s in spaces:
        null = state[s]["null_share"]
        ratios = {c: np.array(share[s][c]) / null[c] for c in CUTS}
        ratio_draws[s] = ratios["5th percentile"][:, : len(rc.RELATIONS)]
        out["spaces"][s] = {"null_share": null, "cuts": state[s]["cuts"],
                            "share": {c: {n: rc.as_triple(rc.interval(np.array(share[s][c])[:, i])) for i, n in enumerate(names)} for c in CUTS},
                            "ratio": {c: {n: rc.as_triple(rc.interval(ratios[c][:, i])) for i, n in enumerate(names)} for c in CUTS},
                            "related_among_far": rc.as_triple(rc.interval(np.array(rates[s])[:, 0])),
                            "related_among_all": rc.as_triple(rc.interval(np.array(rates[s])[:, 1]))}
    a, b = ratio_draws.values()
    out["spearman_between_spaces"] = rc.as_triple(rc.interval(np.array([spearmanr(x, y).statistic for x, y in zip(a, b)])))
    return out


def print_results(result: dict) -> None:
    print("pairs per relation: " + ", ".join(f"{n} {c:,}" for n, c in result["pairs"].items()))
    for s, r in result["spaces"].items():
        print(f"\n{s}: share of the pairs of each relation below each cut, and its ratio to the null share (null in the header)")
        print("  " + "; ".join(f"{c}: null {r['null_share'][c]:.3f}" for c in CUTS))
        for n in result["pairs"]:
            print(f"  {n:26s}" + "".join(f"  {c} {rc.fmt(r['share'][c][n])} ratio {rc.fmt(r['ratio'][c][n])}" for c in CUTS))
        print(f"  test 2: share of the pairs of two WordNet words that hold a relation, among the lowest 1%: {rc.fmt(r['related_among_far'])}; "
              f"among all: {rc.fmt(r['related_among_all'])}")
    print(f"\ntest 3: Spearman between the spaces of the ratio at the 5th percentile cut, {rc.fmt(result['spearman_between_spaces'])}")


def check_claims(result: dict) -> None:
    """The claims that the section makes; a failure means the text has to change."""
    for s, r in result["spaces"].items():
        for cut in CUTS:
            assert all(r["ratio"][cut][n][2] < 1 for n in rc.RELATIONS), f"{s}: a relation is associated with far at {cut}"
        assert r["related_among_far"][2] < r["related_among_all"][1], f"{s}: the far tail holds no fewer relations than all pairs"
        assert r["ratio"]["5th percentile"]["antonym"][2] < 1, f"{s}: antonyms are not associated with far"


def main() -> None:
    vocab, index, _ = utils.load_vocab()
    pairs, wordnet, covered = rc.judged_pairs(vocab, index)
    pure = utils.first_label(wordnet, rc.WORDNET, len(vocab))
    spaces = {s: utils.load_space(stem) for s, stem in rc.SPACES.items()}
    result = measure(spaces, pairs, pure, covered, len(vocab))
    print_results(result)
    utils.save_results("relation_far", result)
    figures.ratios(result, [n for n in result["pairs"] if n != ANY])  # no row named after a judge
    check_claims(result)


if __name__ == "__main__":
    main()
