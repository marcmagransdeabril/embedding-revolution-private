"""Question Q1 of the chapter "Meaning as Likeness" (section "A Gallery of Neighbours"): do the neighbours of words look alike, and where
do the spaces disagree? Plan and decisions: tmp/gallery.md.

Spaces: PPMI-SVD and SGNS trained on the same text (a difference comes from the loss), and two random models as nulls: Gaussian
vectors, and each trained space with its words shuffled among its vectors. There is no sampling: every pair of the 30,000-word
vocabulary (4.5 x 10^8) is scored by cosine, in blocks, and kept as a histogram. The words are shown in ten frequency bands (equal-size bands by
rank). The judge is WordNet 3.0: a pair is a synonym (shares a synset), an antonym, or neither, and "neither" is taken among the
pairs whose two words WordNet covers, so that "unrelated" is not mixed with "not covered" (the coverage per band is printed).
The statistic is the area under the curve (AUC): the probability that a synonym (or antonym) pair is nearer than a pair of neither,
0.5 under the null, with a 95% interval from resampling the words. The words themselves are drawn only to be shown: one query per band
with its nearest neighbours in each space and a control row of random words of the same band.

Expectation (written before the run): the AUC of synonyms is above 0.5 in the two trained spaces and 0.5 in both random models; the
AUC of antonyms is also above 0.5, since opposites share contexts; the spaces agree on the neighbours of frequent words more than on
those of rare words. Prints every number and a verdict for each part; saves results/gallery.json and figures/meaning_as_likeness/
gallery_neighbours.png, gallery_distributions.png, gallery_auc.png, gallery_overlap.png and gallery_edit_distance.png (drawn by gallery_figures.py).
"""
from __future__ import annotations

import numpy as np

import gallery_figures as figures
import utils

SPACES = {"PPMI-SVD": "ppmi_svd_s0", "SGNS": "sgns_s0"}  # same text, two losses: a difference between them comes from the loss
# GloVe is left out of this section: the pretrained GloVe 6B differs from the two spaces in the data as well as in the loss, so a
# difference with it cannot be assigned to the loss.
TRAINED = [*SPACES]
BANDS, BINS = 10, 2000
EDIT_PAIRS, SHUFFLES, K = 300_000, 20, 5


def fmt(estimate: tuple[float, float, float]) -> str:
    """A number with its bootstrap interval, as it is printed everywhere."""
    return f"{estimate[0]:.3f} [{estimate[1]:.3f}, {estimate[2]:.3f}]"


def band_of(size: int) -> np.ndarray:
    """Frequency band of each word: the vocabulary is sorted by frequency, so the bands are equal slices of the ranks."""
    return np.arange(size) * BANDS // size


def to_bin(cosine: np.ndarray) -> np.ndarray:
    """Bin of a cosine in [-1, 1] among BINS equal bins."""
    return np.clip(((cosine + 1) * (BINS / 2)).astype(np.int32), 0, BINS - 1)


def pair_histograms(emb: np.ndarray, covered: np.ndarray, block: int = 1000) -> tuple[np.ndarray, np.ndarray]:
    """Histogram of the cosine of every pair i < j of words, for all pairs and for the pairs of two covered words."""
    u = utils.unit(emb.astype(np.float32))
    n = len(u)
    everything = np.zeros(BINS, dtype=np.int64)
    both_covered = np.zeros_like(everything)
    for start in range(0, n, block):
        rows = np.arange(start, min(start + block, n))
        cols = np.arange(start, n)
        bins = to_bin(u[rows] @ u[cols].T)
        upper = rows[:, None] < cols[None, :]
        everything += np.bincount(bins[upper], minlength=BINS)
        both = upper & covered[rows][:, None] & covered[cols][None, :]
        both_covered += np.bincount(bins[both], minlength=BINS)
    return everything, both_covered


def pair_bins(emb: np.ndarray, pairs: np.ndarray) -> np.ndarray:
    u = utils.unit(emb.astype(np.float32))
    return to_bin((u[pairs[:, 0]] * u[pairs[:, 1]]).sum(axis=1))


def auc_table(emb, hist_covered, syn, ant) -> dict:
    """AUC of synonyms and of antonyms against the pairs of neither, and of synonyms against antonyms. Intervals resample the words."""
    syn_bins, ant_bins = pair_bins(emb, syn), pair_bins(emb, ant)
    count = lambda bins: np.bincount(bins, minlength=BINS)
    neither = hist_covered - count(syn_bins) - count(ant_bins)
    return {"synonyms": len(syn), "antonyms": len(ant),
            "synonym_vs_neither": utils.bootstrap_words_auc(syn, syn_bins, neither, len(emb)),
            "antonym_vs_neither": utils.bootstrap_words_auc(ant, ant_bins, neither, len(emb)),
            "synonym_vs_antonym": utils.bootstrap_words_auc(syn, syn_bins, count(ant_bins), len(emb))}


def shuffled_aucs(emb, hist_all, syn, ant, seed: int = 0) -> dict:
    """Null: the words are shuffled among the vectors, so the synonym pairs get the cosine of random pairs. The pairs of neither follow
    the cosine of all pairs, which a shuffle does not change."""
    rng = np.random.default_rng(seed)
    neither = hist_all
    out = {"synonym_vs_neither": [], "antonym_vs_neither": []}
    for _ in range(SHUFFLES):
        moved = emb[rng.permutation(len(emb))]
        for key, pairs in (("synonym_vs_neither", syn), ("antonym_vs_neither", ant)):
            out[key].append(utils.bootstrap_words_auc(pairs, pair_bins(moved, pairs), neither, len(emb), resamples=100))
    # each shuffle has its own bootstrap interval over words; the table keeps the mean of the points and the widest interval
    return {k: (float(np.mean([r[0] for r in v])), float(np.min([r[1] for r in v])), float(np.max([r[2] for r in v]))) for k, v in out.items()}


def edit_against_cosine(spaces: dict, vocab: list[str], seed: int = 0) -> dict:
    """On a seeded sample of EDIT_PAIRS pairs (the one sample left: the edit distance of 4.5 x 10^8 pairs is too slow in Python):
    the normalized edit distance of the two words, and its Spearman correlation with the cosine in each space."""
    rng = np.random.default_rng(seed)
    pairs = rng.integers(0, len(vocab), (EDIT_PAIRS, 2))
    pairs = pairs[pairs[:, 0] != pairs[:, 1]]
    edit = np.array([utils.edit_distance(vocab[i], vocab[j]) for i, j in pairs])
    out = {"pairs": pairs, "edit": edit, "rho": {}, "close_in_spelling": {}}
    close = edit <= 0.34
    for name, emb in spaces.items():
        u = utils.unit(emb.astype(np.float32))
        cosine = (u[pairs[:, 0]] * u[pairs[:, 1]]).sum(axis=1)
        out["rho"][name] = utils.spearman_interval(edit, cosine, resamples=200)
        out["close_in_spelling"][name] = (int(close.sum()), utils.bootstrap_mean(cosine[close]), utils.bootstrap_mean(cosine))
        out.setdefault("cosine", {})[name] = cosine
    return out


def anchors(pairs: np.ndarray, cosine: np.ndarray, vocab: list[str], seed: int = 0) -> dict:
    """Ten seeded pairs at low, medium and high cosine: from the lowest 1% of the sample, the middle 1% and the highest 0.1%."""
    rng = np.random.default_rng(seed)
    q = np.quantile(cosine, [0.01, 0.495, 0.505, 0.999])
    zones = {"low": cosine <= q[0], "medium": (cosine >= q[1]) & (cosine <= q[2]), "high": cosine >= q[3]}
    out = {}
    for name, zone in zones.items():
        pick = rng.choice(np.flatnonzero(zone), 10, replace=False)
        out[name] = [(vocab[pairs[i, 0]], vocab[pairs[i, 1]], round(float(cosine[i]), 3)) for i in pick]
    return out


def displayed_queries(vocab: list[str], band: np.ndarray, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """One seeded query per band, and for each five random words of the same band (the control row)."""
    rng = np.random.default_rng(seed)
    queries = np.array([rng.choice(np.flatnonzero(band == b)) for b in range(BANDS)])
    controls = np.array([rng.choice(np.flatnonzero((band == b) & (np.arange(len(vocab)) != q)), K, replace=False)
                         for b, q in enumerate(queries)])
    return queries, controls


def overlaps(spaces: dict) -> tuple[dict, dict]:
    """Top-K neighbours of every word in each space, and the overlap of each two spaces for each word."""
    everyone = np.arange(len(next(iter(spaces.values()))))
    neighbours = {name: utils.nearest(emb, everyone, K) for name, emb in spaces.items()}
    names = list(spaces)
    per_word = {}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            per_word[f"{a} / {b}"] = utils.neighbour_overlap(neighbours[a], neighbours[b])
    return neighbours, per_word


def cosine_sd(hist: np.ndarray) -> float:
    """Standard deviation of the cosine of the pairs counted in a histogram over [-1, 1] (bins of width 2 / BINS, taken at their centre)."""
    centres = (np.arange(BINS) + 0.5) / BINS * 2 - 1
    mean = (hist * centres).sum() / hist.sum()
    return float(np.sqrt((hist * (centres - mean) ** 2).sum() / hist.sum()))


def analyse_space(name: str, emb: np.ndarray, syn, ant, covered) -> tuple[dict, dict]:
    """The AUC tables of one space, with the shuffled-vocabulary null, printed; and the curves to draw."""
    everything, both = pair_histograms(emb, covered)
    table = auc_table(emb, both, syn, ant)
    baseline = utils.bootstrap_mean_cosine(utils.unit(emb.astype(np.float32)))
    print(f"\n{name}: mean cosine of all {len(emb) * (len(emb) - 1) // 2:,} pairs of words (95% interval over words) {fmt(baseline)}")
    null = shuffled_aucs(emb, everything, syn, ant)
    print(f"\n{name}: AUC over {both.sum():,} covered pairs of {len(emb):,} words (95% interval over words)")
    for contrast in ("synonym_vs_neither", "antonym_vs_neither", "synonym_vs_antonym"):
        print(f"  {contrast:20s} {fmt(table[contrast])}")
    print(f"  shuffled vocabulary ({SHUFFLES} shuffles, mean and widest bootstrap interval): synonyms {fmt(null['synonym_vs_neither'])}, "
          f"antonyms {fmt(null['antonym_vs_neither'])}")
    assert all(0.45 < null[k][0] < 0.55 for k in null), "the shuffled vocabulary must give 0.5"
    spread = cosine_sd(everything)
    print(f"  standard deviation of the cosine of all pairs: {spread:.3f}")
    if name == "random Gaussian":
        assert 0.45 < table["synonym_vs_neither"][0] < 0.55, "random vectors must give 0.5"
        return {"auc": table, "shuffled_vocabulary": null, "mean_cosine": baseline, "cosine_sd": spread}, {"all pairs": everything}
    sb, ab = pair_bins(emb, syn), pair_bins(emb, ant)
    neither = both - np.bincount(sb, minlength=BINS) - np.bincount(ab, minlength=BINS)
    return ({"auc": table, "shuffled_vocabulary": null, "mean_cosine": baseline, "cosine_sd": spread},
            {"synonyms": np.bincount(sb, minlength=BINS), "antonyms": np.bincount(ab, minlength=BINS), "neither (covered words)": neither,
             "all pairs": everything})


def report_expectations(results: dict) -> None:
    for contrast in ("synonym_vs_neither", "antonym_vs_neither"):
        ok = [n for n in TRAINED if results["spaces"][n]["auc"][contrast][1] > 0.5]
        print(f"expectation, {contrast} above 0.5 (lower end of the interval): holds in {len(ok)} of {len(TRAINED)} trained spaces"
              + ("" if len(ok) == len(TRAINED) else f" (fails in {', '.join(set(TRAINED) - set(ok))})"))


def report_edit_distance(spaces: dict, vocab, results: dict) -> dict:
    edit = edit_against_cosine(spaces, vocab)
    print(f"\nedit distance of {len(edit['edit']):,} random pairs: mean {fmt(utils.bootstrap_mean(edit['edit']))}, "
          f"1st percentile {np.quantile(edit['edit'], 0.01):.2f}")
    for name in spaces:
        n, near, overall = edit["close_in_spelling"][name]
        print(f"  {name:16s} Spearman(edit, cosine) = {fmt(edit['rho'][name])}; {n} pairs close in spelling have mean cosine "
              f"{fmt(near)} against {fmt(overall)} for all")
    results["edit_distance"] = {"rho": edit["rho"], "close_in_spelling": edit["close_in_spelling"], "mean": utils.bootstrap_mean(edit["edit"])}
    results["anchors"] = {name: anchors(edit["pairs"], edit["cosine"][name], vocab) for name in spaces}
    for zone, rows in results["anchors"]["SGNS"].items():
        print(f"  SGNS {zone} cosine: " + ", ".join(f"{a}/{b} {c}" for a, b, c in rows))
    return edit


def report_neighbours(spaces: dict, vocab, counts: np.ndarray, band, results: dict) -> None:
    trained = {n: spaces[n] for n in TRAINED}
    neighbours, per_word = overlaps(trained)
    results["overlap_per_band"] = {pair: [utils.bootstrap_mean(v[band == b]) for b in range(BANDS)] for pair, v in per_word.items()}
    for pair, per_band in results["overlap_per_band"].items():
        print(f"top-{K} overlap {pair} per band (frequent to rare; bootstrap over words):\n  " + " ".join(fmt(x) for x in per_band))
    queries, controls = displayed_queries(vocab, band)
    mean_overlap = np.mean([v[queries] for v in per_word.values()], axis=0)
    rule = {"lowest overlap": int(queries[mean_overlap.argmin()]), "highest overlap": int(queries[mean_overlap.argmax()])}
    results["discussed_queries"] = {k: vocab[v] for k, v in rule.items()}
    print("queries discussed in the text: " + ", ".join(f"{k}: {vocab[v]}" for k, v in rule.items()))
    figures.neighbours_gallery(vocab, counts, queries, controls, neighbours, rule)


def main() -> None:
    utils.FIGURES.mkdir(parents=True, exist_ok=True)
    vocab, index, counts = utils.load_vocab()
    size = len(vocab)
    band = band_of(size)
    syn, ant, covered = utils.wordnet_pairs(index)
    print(f"WordNet 3.0 on the {size:,} words: {covered.sum():,} covered, {len(syn):,} synonym pairs, {len(ant):,} antonym pairs")
    coverage = [utils.bootstrap_mean(covered[band == b].astype(float)) for b in range(BANDS)]
    print("coverage per band (bootstrap over words): " + " ".join(fmt(c) for c in coverage))

    spaces = {name: utils.load_space(stem) for name, stem in SPACES.items()}
    spaces["random Gaussian"] = np.random.default_rng(0).standard_normal(spaces["SGNS"].shape).astype(np.float32)

    results = {"vocabulary": size, "synonym_pairs": len(syn), "antonym_pairs": len(ant), "covered_words": int(covered.sum()),
               "coverage_per_band": coverage, "spaces": {}}
    curves = {}
    for name, emb in spaces.items():
        results["spaces"][name], curves[name] = analyse_space(name, emb, syn, ant, covered)
    report_expectations(results)
    edit = report_edit_distance(spaces, vocab, results)
    report_neighbours(spaces, vocab, counts, band, results)
    utils.save_results("gallery", results)
    centres = (np.arange(BINS) + 0.5) / BINS * 2 - 1
    figures.null_distribution({n: curves[n]["all pairs"] for n in [*TRAINED, "random Gaussian"]}, centres, spaces["SGNS"].shape[1])
    figures.cosine_by_class({n: {k: v for k, v in curves[n].items() if k != "all pairs"} for n in TRAINED}, centres)
    figures.auc_bars(results, TRAINED + ["random Gaussian"])
    figures.overlap_by_band(results["overlap_per_band"])
    figures.edit_distance(edit)


if __name__ == "__main__":
    main()
