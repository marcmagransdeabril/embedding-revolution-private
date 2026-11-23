"""Question Q1 of the chapter "Meaning as Likeness" (section "A Gallery of Neighbours"): do the neighbours of words look alike, and where
do the spaces disagree? Plan and decisions: tmp/gallery.md.

Spaces: PPMI-SVD and SGNS trained on the same text (a difference comes from the loss), pretrained GloVe 6B (a difference with them
comes from the data and the loss together), and two random models as nulls: Gaussian
vectors, and each trained space with its words shuffled among its vectors. There is no sampling: every pair of the 30,000-word
vocabulary (4.5 x 10^8) is scored by cosine, in blocks, and kept as a histogram per cell of ten frequency bands (equal-size bands by
rank). The judge is WordNet 3.0: a pair is a synonym (shares a synset), an antonym, or neither, and "neither" is taken among the
pairs whose two words WordNet covers, so that "unrelated" is not mixed with "not covered" (the coverage per band is printed).
The statistic is the area under the curve (AUC): the probability that a synonym (or antonym) pair is nearer than a pair of neither,
0.5 under the null, with a 95% interval from resampling the words. The words themselves are drawn only to be shown: one query per band
with its nearest neighbours in each space and a control row of random words of the same band.

Expectation (written before the run): the AUC of synonyms is above 0.5 in the three trained spaces and 0.5 in both random models; the
AUC of antonyms is also above 0.5, since opposites share contexts; the spaces agree on the neighbours of frequent words more than on
those of rare words. Prints every number and a verdict for each part; saves results/gallery.json and figures/meaning_as_likeness/
gallery_neighbours.png, gallery_distributions.png, gallery_auc.png, gallery_overlap.png and gallery_edit_distance.png (drawn by gallery_figures.py).
"""
from __future__ import annotations

import numpy as np

import gallery_figures as figures
import utils

SPACES = {"PPMI-SVD": "ppmi_svd_s0", "SGNS": "sgns_s0"}  # same text, two losses: a difference between them comes from the loss
PRETRAINED = "GloVe 6B"  # pretrained on 6 billion words (350 times the text) with the GloVe loss: differs in both the loss and the data
# The GloVe trained on text8 (glove_s0) is left out: its SimLex-999 correlation is 0.09 against 0.27 for the other two and its
# neighbours are not words that go together, so it measures a training that did not work and not the GloVe loss.
TRAINED = [*SPACES, PRETRAINED]
BANDS, BINS, MIN_PAIRS = 10, 2000, 30
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


def pair_histograms(emb: np.ndarray, band: np.ndarray, covered: np.ndarray, present: np.ndarray, block: int = 1000) -> tuple[np.ndarray, np.ndarray]:
    """Histogram of the cosine of every pair i < j of words that the space has (`present`), per cell (band of i, band of j), for all
    pairs and for the pairs of two covered words."""
    u = utils.unit(emb.astype(np.float32))
    n = len(u)
    everything = np.zeros(BANDS * BANDS * BINS, dtype=np.int64)
    both_covered = np.zeros_like(everything)
    for start in range(0, n, block):
        rows = np.arange(start, min(start + block, n))
        cols = np.arange(start, n)
        keys = (band[rows][:, None] * BANDS + band[cols][None, :]) * BINS + to_bin(u[rows] @ u[cols].T)
        upper = (rows[:, None] < cols[None, :]) & present[rows][:, None] & present[cols][None, :]
        everything += np.bincount(keys[upper], minlength=len(everything))
        both = upper & covered[rows][:, None] & covered[cols][None, :]
        both_covered += np.bincount(keys[both], minlength=len(everything))
    return everything.reshape(BANDS * BANDS, BINS), both_covered.reshape(BANDS * BANDS, BINS)


def pair_bins(emb: np.ndarray, pairs: np.ndarray) -> np.ndarray:
    u = utils.unit(emb.astype(np.float32))
    return to_bin((u[pairs[:, 0]] * u[pairs[:, 1]]).sum(axis=1))


def cell_of(pairs: np.ndarray, band: np.ndarray) -> np.ndarray:
    return band[pairs[:, 0]] * BANDS + band[pairs[:, 1]]


def stratified_row(syn, ant, syn_bins, ant_bins, syn_cell, ant_cell, hist_covered, size) -> dict:
    """The same three AUCs, each pair compared only with pairs of the same cell: the one that is not changed by frequency."""
    flat = lambda bins, cell: np.bincount(cell * BINS + bins, minlength=BANDS * BANDS * BINS).reshape(BANDS * BANDS, BINS)
    syn_hist, ant_hist = flat(syn_bins, syn_cell), flat(ant_bins, ant_cell)
    neither = hist_covered - syn_hist - ant_hist
    return {"synonym_vs_neither": utils.bootstrap_words_auc(syn, syn_bins, neither, size, positive_cells=syn_cell),
            "antonym_vs_neither": utils.bootstrap_words_auc(ant, ant_bins, neither, size, positive_cells=ant_cell),
            "synonym_vs_antonym": utils.bootstrap_words_auc(syn, syn_bins, ant_hist, size, positive_cells=syn_cell)}


def auc_table(emb, hist_covered, syn, ant, band) -> dict:
    """AUC of synonyms and of antonyms against the pairs of neither, and of synonyms against antonyms, pooled and for each cell with
    at least MIN_PAIRS pairs of each class involved. Intervals resample the words."""
    syn_bins, ant_bins = pair_bins(emb, syn), pair_bins(emb, ant)
    syn_cell, ant_cell = cell_of(syn, band), cell_of(ant, band)
    count = lambda bins: np.bincount(bins, minlength=BINS)
    out = {"within_band": stratified_row(syn, ant, syn_bins, ant_bins, syn_cell, ant_cell, hist_covered, len(emb))}
    for name, cells in [("pooled", [None])] + [(f"{a}-{b}", [a * BANDS + b]) for a in range(BANDS) for b in range(a, BANDS)]:
        keep_s = np.ones(len(syn), bool) if cells[0] is None else syn_cell == cells[0]
        keep_a = np.ones(len(ant), bool) if cells[0] is None else ant_cell == cells[0]
        neither = (hist_covered.sum(axis=0) if cells[0] is None else hist_covered[cells[0]]) - count(syn_bins[keep_s]) - count(ant_bins[keep_a])
        row = {"synonyms": int(keep_s.sum()), "antonyms": int(keep_a.sum())}
        if keep_s.sum() >= MIN_PAIRS:
            row["synonym_vs_neither"] = utils.bootstrap_words_auc(syn[keep_s], syn_bins[keep_s], neither, len(emb))
        if keep_a.sum() >= MIN_PAIRS:
            row["antonym_vs_neither"] = utils.bootstrap_words_auc(ant[keep_a], ant_bins[keep_a], neither, len(emb))
        if keep_s.sum() >= MIN_PAIRS and keep_a.sum() >= MIN_PAIRS:
            row["synonym_vs_antonym"] = utils.bootstrap_words_auc(syn[keep_s], syn_bins[keep_s], count(ant_bins[keep_a]), len(emb))
        out[name] = row
    return out


def shuffled_aucs(emb, hist_all, syn, ant, present, seed: int = 0) -> dict:
    """Null: the words are shuffled among the vectors, so the synonym pairs get the cosine of random pairs. The pairs of neither follow
    the cosine of all pairs, which a shuffle does not change."""
    rng = np.random.default_rng(seed)
    neither = hist_all.sum(axis=0)
    out = {"synonym_vs_neither": [], "antonym_vs_neither": []}
    for _ in range(SHUFFLES):
        moved = emb.copy()
        where = np.flatnonzero(present)
        moved[where] = emb[rng.permutation(where)]
        for key, pairs in (("synonym_vs_neither", syn), ("antonym_vs_neither", ant)):
            out[key].append(utils.bootstrap_words_auc(pairs, pair_bins(moved, pairs), neither, len(emb), resamples=100))
    # each shuffle has its own bootstrap interval over words; the table keeps the mean of the points and the widest interval
    return {k: (float(np.mean([r[0] for r in v])), float(np.min([r[1] for r in v])), float(np.max([r[2] for r in v]))) for k, v in out.items()}


def edit_against_cosine(spaces: dict, vocab: list[str], common: np.ndarray, seed: int = 0) -> dict:
    """On a seeded sample of EDIT_PAIRS pairs (the one sample left: the edit distance of 4.5 x 10^8 pairs is too slow in Python):
    the normalized edit distance of the two words, and its Spearman correlation with the cosine in each space."""
    rng = np.random.default_rng(seed)
    pairs = rng.integers(0, len(vocab), (EDIT_PAIRS, 2))
    pairs = pairs[(pairs[:, 0] != pairs[:, 1]) & common[pairs[:, 0]] & common[pairs[:, 1]]]
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


def displayed_queries(vocab: list[str], band: np.ndarray, common: np.ndarray, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """One seeded query per band, and for each five random words of the same band (the control row)."""
    rng = np.random.default_rng(seed)
    queries = np.array([rng.choice(np.flatnonzero((band == b) & common)) for b in range(BANDS)])
    controls = np.array([rng.choice(np.flatnonzero((band == b) & common & (np.arange(len(vocab)) != q)), K, replace=False)
                         for b, q in enumerate(queries)])
    return queries, controls


def overlaps(spaces: dict, common: np.ndarray) -> tuple[dict, dict]:
    """Top-K neighbours of every word that all the spaces have (the neighbours are in the whole vocabulary, in each space the rows of
    words that the space lacks are zero and never near), and the overlap of each two spaces for each such word (NaN for the others)."""
    everyone = np.arange(len(common))
    neighbours = {name: utils.nearest(emb, everyone, K) for name, emb in spaces.items()}
    names = list(spaces)
    per_word = {}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            overlap = utils.neighbour_overlap(neighbours[a], neighbours[b])
            overlap[~common] = np.nan
            per_word[f"{a} / {b}"] = overlap
    return neighbours, per_word


def analyse_space(name: str, emb: np.ndarray, present: np.ndarray, band, syn, ant, covered) -> tuple[dict, dict]:
    """The AUC tables of one space, with the shuffled-vocabulary null, printed; and the curves to draw."""
    keep_s, keep_a = present[syn].all(axis=1), present[ant].all(axis=1)
    syn, ant = syn[keep_s], ant[keep_a]
    everything, both = pair_histograms(emb, band, covered, present)
    table = auc_table(emb, both, syn, ant, band)
    baseline = utils.bootstrap_mean_cosine(utils.unit(emb[present].astype(np.float32)))
    print(f"\n{name}: mean cosine of all {present.sum() * (present.sum() - 1) // 2:,} pairs of words (95% interval over words) {fmt(baseline)}")
    null = shuffled_aucs(emb, everything, syn, ant, present)
    print(f"\n{name}: AUC over {both.sum():,} covered pairs of {present.sum():,} words (95% interval over words); pooled, and within frequency band")
    for contrast in ("synonym_vs_neither", "antonym_vs_neither", "synonym_vs_antonym"):
        print(f"  {contrast:20s} pooled {fmt(table['pooled'][contrast])}   within band {fmt(table['within_band'][contrast])}")
    print(f"  shuffled vocabulary ({SHUFFLES} shuffles, mean and widest bootstrap interval): synonyms {fmt(null['synonym_vs_neither'])}, "
          f"antonyms {fmt(null['antonym_vs_neither'])}")
    assert all(0.45 < null[k][0] < 0.55 for k in null), "the shuffled vocabulary must give 0.5"
    if name == "random Gaussian":
        assert 0.45 < table["pooled"]["synonym_vs_neither"][0] < 0.55, "random vectors must give 0.5"
        return {"auc": table, "shuffled_vocabulary": null, "mean_cosine": baseline}, {"all pairs": everything.sum(axis=0)}
    sb, ab = pair_bins(emb, syn), pair_bins(emb, ant)
    neither = both.sum(axis=0) - np.bincount(sb, minlength=BINS) - np.bincount(ab, minlength=BINS)
    return {"auc": table, "shuffled_vocabulary": null, "mean_cosine": baseline}, {"synonyms": np.bincount(sb, minlength=BINS), "antonyms": np.bincount(ab, minlength=BINS),
                                                         "neither (covered words)": neither}


def report_cells_and_expectations(results: dict) -> None:
    for name in TRAINED:
        cells = {c: r for c, r in results["spaces"][name]["auc"].items() if c != "within_band"}
        usable = {c: r for c, r in cells.items() if c != "pooled" and "antonym_vs_neither" in r}
        print(f"\n{name}: {len(usable)} of 55 band cells have at least {MIN_PAIRS} antonym pairs; AUC against neither in each "
              "(cell = bands of the two words; synonyms, antonyms): " + "; ".join(
                  f"{c} {fmt(r['synonym_vs_neither'])}, {fmt(r['antonym_vs_neither'])} (n {r['synonyms']}, {r['antonyms']})" for c, r in usable.items()))
    for contrast in ("synonym_vs_neither", "antonym_vs_neither"):
        for where in ("pooled", "within_band"):
            ok = [n for n in TRAINED if results["spaces"][n]["auc"][where][contrast][1] > 0.5]
            print(f"expectation, {contrast} above 0.5 ({where}, lower end of the interval): holds in {len(ok)} of {len(TRAINED)} trained spaces"
                  + ("" if len(ok) == len(TRAINED) else f" (fails in {', '.join(set(TRAINED) - set(ok))})"))


def report_edit_distance(spaces: dict, vocab, common: np.ndarray, results: dict) -> dict:
    edit = edit_against_cosine(spaces, vocab, common)
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


def report_neighbours(spaces: dict, vocab, band, common: np.ndarray, results: dict) -> None:
    trained = {n: spaces[n] for n in TRAINED}
    neighbours, per_word = overlaps(trained, common)
    results["overlap_per_band"] = {pair: [utils.bootstrap_mean(v[(band == b) & common]) for b in range(BANDS)] for pair, v in per_word.items()}
    for pair, per_band in results["overlap_per_band"].items():
        print(f"top-{K} overlap {pair} per band (frequent to rare; bootstrap over words):\n  " + " ".join(fmt(x) for x in per_band))
    queries, controls = displayed_queries(vocab, band, common)
    mean_overlap = np.mean([v[queries] for v in per_word.values()], axis=0)
    rule = {"lowest overlap": int(queries[mean_overlap.argmin()]), "highest overlap": int(queries[mean_overlap.argmax()]),
            "drawn at random": int(np.random.default_rng(1).choice(queries))}
    results["discussed_queries"] = {k: vocab[v] for k, v in rule.items()}
    print("queries discussed in the text: " + ", ".join(f"{k}: {vocab[v]}" for k, v in rule.items()))
    figures.neighbours_gallery(vocab, queries, controls, neighbours, rule)


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
    spaces[PRETRAINED], pretrained_has = utils.load_glove6b(index)
    spaces["random Gaussian"] = np.random.default_rng(0).standard_normal(spaces["SGNS"].shape).astype(np.float32)
    present = {name: np.ones(size, dtype=bool) for name in spaces}
    present[PRETRAINED] = pretrained_has
    print(f"{PRETRAINED}: {pretrained_has.sum():,} of the {size:,} words are in the pretrained file (the others, mostly pieces of LaTeX and of "
          "accented words in text8, are left out of its statistics and of every comparison between spaces)")
    common = np.logical_and.reduce(list(present.values()))

    results = {"vocabulary": size, "synonym_pairs": len(syn), "antonym_pairs": len(ant), "covered_words": int(covered.sum()),
               "coverage_per_band": coverage, "words_in_pretrained": int(pretrained_has.sum()), "spaces": {}}
    curves = {}
    for name, emb in spaces.items():
        results["spaces"][name], curves[name] = analyse_space(name, emb, present[name], band, syn, ant, covered)
    report_cells_and_expectations(results)
    edit = report_edit_distance(spaces, vocab, common, results)
    report_neighbours(spaces, vocab, band, common, results)
    utils.save_results("gallery", results)
    figures.cosine_by_class({n: curves[n] for n in TRAINED}, (np.arange(BINS) + 0.5) / BINS * 2 - 1)
    figures.auc_bars(results, TRAINED + ["random Gaussian"])
    figures.overlap_by_band(results["overlap_per_band"])
    figures.edit_distance(edit)


if __name__ == "__main__":
    main()
