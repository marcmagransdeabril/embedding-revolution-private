"""Question Q2 of the chapter "Meaning as Likeness" (section "Which Relations Does Nearness Tell Apart?"): which relations does the
nearness of a space tell apart? A loss trained on company rewards any relation that leaves a trace in company, so nearness is expected to
mix many relations; nearness is one number per pair, so the most it can do is put relations in an order, and two relations are
"collapsed" when the interval of the order between them holds no order.

Spaces: PPMI-SVD and SGNS of the gallery (text8, 30,000 words, d = 100, seed 0) for tests 1, 2, 3 and 5; the same two losses trained
on the second half of text8 for test 4, whose judge is counted on the first half (so that the judge is not the space itself).
Relations, each a set of unordered pairs of words of the vocabulary:
  WordNet 3.0: inflection (a shared base form, by morphy's rules and exception lists), derivation ("+"), synonym (a shared synset),
    antonym ("!"), hypernym (one IS-A step), meronym (part, member or substance), co-hyponym (the same direct hypernym); a pair takes
    the first that holds in this order, and the pairs that hold only one of them are a robustness check;
  SimLex-999 with USF: associated (not similar) and similar (not associated), the pairs in the top third of one judge and the bottom third of the other;
  BATS 3.0: its four families (inflectional, derivational, lexicographic, encyclopedic), each the union of its ten relations;
  text8, first half: direct co-occurrence (PPMI > 0 within the window of 5) and shared context only (no co-occurrence, and a cosine of
    the two PPMI rows in the top 1% of the random pairs without co-occurrence), among RANDOM_PAIRS seeded random pairs;
  controls: neither (both words in WordNet, none of its seven relations: the baseline of every AUC, as in the gallery), random pairs of
    the vocabulary, and, for test 3, random words of the same frequency band.

Five tests. (1) For each relation, the probability that one of its pairs is nearer than a pair of neither (AUC, 0.5 if the relation
leaves no trace). (2) For each two relations, the probability that a pair of the first is nearer than a pair of the second: an interval
that holds 0.5 is a collapse, one that does not is an order; the count of orders is also given with a Bonferroni-corrected interval
(normal, from the bootstrap standard error) for the number of contrasts. (3) The label of the top-5 neighbours of every word, against
random words of the same band: the share of each relation, and the share that no judge names, with a seeded sample to read. (4) The
mechanism, in the half-text spaces: the AUC of direct co-occurrence and of shared context only, the share of the cosine of random pairs
that frequency and the first-half context explain (R^2), and the effect of each relation on the cosine with and without that context
held fixed (least squares, the relation as an indicator, random pairs the reference); a relation whose effect with the context held
fixed holds zero is collapsed into shared context. (5) Whether the two losses order the relations alike: the Spearman correlation of
their AUCs against neither, and the share of the orders of test 2 that both resolve in the same direction.
Every interval is a 95% percentile bootstrap over the words of the vocabulary (RESAMPLES; FIT_RESAMPLES for the fits of test 4), the
same draws for every relation and both spaces, so that the contrasts are paired; the histogram of neither is held fixed, as in the
gallery. Test 3 resamples the query words. Test 4 samples: RANDOM_PAIRS random pairs and at most PER_RELATION pairs of each relation.

Expectation (written before the run): every relation is above neither (any relation leaves a trace in company), with inflection,
antonym and co-hyponym the nearest and hypernym and meronym the farthest; with hundreds to hundreds of thousands of pairs most of the
orders of test 2 are resolved, and the collapses are among the small sets (SimLex cells, BATS families) and between relations of
similar kind (synonym and co-hyponym); more than half of the top-5 neighbours carry no label; in test 4 the first-half context
explains most of what frequency does not, and most relation effects shrink by more than half once it is held fixed, so that the
relations collapse into shared context; the two losses order the relations alike (Spearman above 0.8).

Prints every number; saves results/relation_collapse.json and the figures relation_collapse_auc.png, relation_collapse_matrix.png,
relation_collapse_inventory.png and relation_collapse_mechanism.png (drawn by relation_collapse_figures.py).
"""
from __future__ import annotations

import numpy as np
from scipy import sparse
from scipy.stats import norm, spearmanr

import gallery
import relation_collapse_figures as figures
import utils

SPACES = {"PPMI-SVD": "ppmi_svd_s0", "SGNS": "sgns_s0"}
HALF_SPACES = {"PPMI-SVD": "ppmi_svd_B", "SGNS": "sgns_B"}  # trained on the second half of text8, as train_spaces.py does
WORDNET = ["inflection", "derivation", "synonym", "antonym", "hypernym", "meronym", "co-hyponym"]  # also the precedence
SIMLEX = ["associated (SimLex)", "similar (SimLex)"]  # the cells "associated only" and "similar only" of cells(), named by what they hold
BATS = ["BATS inflectional", "BATS derivational", "BATS lexicographic", "BATS encyclopedic"]
RELATIONS = WORDNET + SIMLEX + BATS
RANDOM, NEITHER, UNCOVERED, ANY_BATS = "random pairs", "neither (in WordNet)", "not in WordNet", "BATS only"
CONTEXT = ["direct co-occurrence", "shared context only"]
LABELS = WORDNET + [ANY_BATS, NEITHER, UNCOVERED]  # the labels of a neighbour in test 3, in order of precedence
BINS, K, WINDOW = gallery.BINS, 5, 5
RESAMPLES, FIT_RESAMPLES, RANDOM_PAIRS, PER_RELATION, TOP_SHARE = 1000, 200, 200_000, 20_000, 0.01


def fmt(estimate: tuple[float, float, float], sign: str = "") -> str:
    """A number with its bootstrap interval, as it is printed everywhere."""
    return f"{estimate[0]:{sign}.3f} [{estimate[1]:{sign}.3f}, {estimate[2]:{sign}.3f}]"


def cells(similarity: np.ndarray, association: np.ndarray, share: float) -> dict[str, np.ndarray]:
    """Boolean mask of each of the four cells of the two SimLex-999 judges: top `share` against bottom `share` of each (a cut at zero
    would leave "similar, not associated" almost empty, since the pairs were drawn from USF)."""
    hi_s, lo_s = similarity >= np.quantile(similarity, 1 - share), similarity <= np.quantile(similarity, share)
    hi_a, lo_a = association >= np.quantile(association, 1 - share), association <= np.quantile(association, share)
    return {"both": hi_s & hi_a, "similar only": hi_s & lo_a, "associated only": lo_s & hi_a, "neither": lo_s & lo_a}


def frequency_features(log_counts: np.ndarray) -> np.ndarray:
    """Design matrix of a pair from the log counts of its two words (n x 2): intercept, lower and higher log count (order-free)."""
    return np.column_stack([np.ones(len(log_counts)), log_counts.min(axis=1), log_counts.max(axis=1)])


# --- the judges
def random_pairs(size: int, n: int, seed: int = 0) -> np.ndarray:
    """`n` seeded pairs of distinct words of the vocabulary, drawn uniformly (repeats removed)."""
    rng = np.random.default_rng(seed)
    a = rng.integers(0, size, n)
    return utils.pair_array(zip(a, (a + rng.integers(1, size, n)) % size))


def in_vocab(pairs, index: dict[str, int]) -> np.ndarray:
    return utils.pair_array((index[a], index[b]) for a, b in pairs if a in index and b in index)


def judged_pairs(vocab: list[str], index: dict[str, int]) -> tuple[dict, dict, np.ndarray]:
    """The pairs of every relation of tests 1 to 3 (WordNet with its precedence, the SimLex cells, the BATS families, random pairs),
    the WordNet relations without precedence, and the WordNet coverage of the vocabulary."""
    wordnet, covered = utils.wordnet_relations(vocab)
    pairs = utils.first_label(wordnet, WORDNET, len(vocab))
    simlex = [p for p in utils.load_simlex() if p[0] in index and p[1] in index]
    similarity, association = (np.array([p[c] for p in simlex]) for c in (2, 3))
    masks = cells(similarity, association, 1 / 3)
    for name, cell in zip(SIMLEX, ("associated only", "similar only")):
        pairs[name] = in_vocab([p[:2] for p, m in zip(simlex, masks[cell]) if m], index)
    bats = utils.load_bats()
    for name, family in zip(BATS, utils.BATS_FAMILIES.values()):
        pairs[name] = in_vocab([p for rows in bats[family].values() for p in rows], index)
    pairs[RANDOM] = random_pairs(len(vocab), RANDOM_PAIRS)
    return pairs, wordnet, covered


def neither_histogram(emb: np.ndarray, covered: np.ndarray, wordnet_pairs: dict) -> np.ndarray:
    """Histogram of the cosine of the pairs of two WordNet words that hold none of its seven relations (exact, every pair scored)."""
    _, both = gallery.pair_histograms(emb, covered)
    for name in WORDNET:
        inside = wordnet_pairs[name][covered[wordnet_pairs[name]].all(axis=1)]  # an inflected form need not be in WordNet itself
        both = both - np.bincount(gallery.pair_bins(emb, inside), minlength=BINS)
    assert (both >= 0).all()
    return both


# --- the bootstrap over words, shared by tests 1, 2, 4 and 5
def word_draws(size: int, resamples: int, seed: int = 0):
    """How many times each word is drawn, first all ones (the point estimate), then `resamples` draws with replacement."""
    yield np.ones(size, dtype=np.int64)
    rng = np.random.default_rng(seed)
    for _ in range(resamples):
        yield np.bincount(rng.integers(0, size, size), minlength=size)


def histograms(bins: dict[str, np.ndarray], pairs: dict[str, np.ndarray], times: np.ndarray, names: list[str]) -> np.ndarray:
    """Histogram (names x BINS) of the cosine of the pairs of each relation, a pair weighted by the product of the draws of its words."""
    return np.stack([np.bincount(bins[n], weights=times[pairs[n][:, 0]] * times[pairs[n][:, 1]], minlength=BINS) for n in names])


def auc_matrix(h: np.ndarray) -> np.ndarray:
    """AUC of every row of `h` against every row (the probability that a pair of row a is nearer than one of row b, ties one half),
    from the histograms: sum_k h_a[k] (sum_{l<k} h_b[l] + h_b[k] / 2) / (|h_a| |h_b|)."""
    below = np.cumsum(h, axis=1) - h
    sums = h.sum(axis=1)
    return (h @ (below + 0.5 * h).T) / np.outer(sums, sums)


def interval(values: np.ndarray) -> tuple[float, float, float]:
    """(point, low, high) from the point estimate followed by its resamples, along the first axis."""
    low, high = np.nanpercentile(values[1:], [2.5, 97.5], axis=0)
    return values[0], low, high


def as_triple(est) -> list:
    return [float(est[0]), float(est[1]), float(est[2])]


# --- tests 1, 2 and 5
def order_tests(spaces: dict, pairs: dict, neither: dict, size: int) -> dict:
    """AUC of every relation against neither, AUC of every two relations, and the agreement of the two spaces, with paired intervals."""
    names = RELATIONS + [RANDOM]
    bins = {s: {n: gallery.pair_bins(emb, pairs[n]) for n in names} for s, emb in spaces.items()}
    against, between, rho = {s: [] for s in spaces}, {s: [] for s in spaces}, []
    for times in word_draws(size, RESAMPLES):
        for s in spaces:
            h = histograms(bins[s], pairs, times, names)
            against[s].append([utils.histogram_auc(row, neither[s]) for row in h])
            between[s].append(auc_matrix(h[: len(RELATIONS)]))
        a, b = (np.array(against[s][-1][: len(RELATIONS)]) for s in spaces)
        rho.append(spearmanr(a, b).statistic)
    out = {"pairs": {n: len(pairs[n]) for n in names}, "spaces": {}, "spearman_between_spaces": as_triple(interval(np.array(rho)))}
    contrasts = len(RELATIONS) * (len(RELATIONS) - 1) // 2
    z = norm.ppf(1 - 0.025 / contrasts)
    for s in spaces:
        auc, matrix = np.array(against[s]), np.array(between[s])
        point, low, high = interval(matrix)
        spread = matrix[1:].std(axis=0)
        out["spaces"][s] = {"against_neither": {n: as_triple(interval(auc[:, i])) for i, n in enumerate(names)},
                            "matrix": {"point": point.tolist(), "low": low.tolist(), "high": high.tolist(),
                                       "bonferroni_low": (point - z * spread).tolist(), "bonferroni_high": (point + z * spread).tolist()}}
    out["contrasts"], out["bonferroni_z"] = contrasts, float(z)
    return out


def resolved(matrix: dict, low: str = "low", high: str = "high") -> np.ndarray:
    """+1 where the row relation is nearer than the column one, -1 where it is farther, 0 where the interval holds 0.5 (a collapse)."""
    lo, hi = np.array(matrix[low]), np.array(matrix[high])
    return np.where(lo > 0.5, 1, np.where(hi < 0.5, -1, 0))


def agreement(result: dict) -> dict:
    """Test 5: of the contrasts of test 2, how many each space resolves, and how many both resolve the same way."""
    upper = np.triu_indices(len(RELATIONS), 1)
    signs = {s: resolved(r["matrix"])[upper] for s, r in result["spaces"].items()}
    a, b = signs.values()
    return {"resolved": {s: int((v != 0).sum()) for s, v in signs.items()}, "both_same": int(((a == b) & (a != 0)).sum()),
            "opposite": int((a * b < 0).sum()), "contrasts": len(upper[0])}


def single_label_check(spaces: dict, wordnet: dict, neither: dict, size: int) -> dict:
    """Test 1 on the WordNet pairs that hold only one of its relations (no precedence needed)."""
    single = utils.single_label(wordnet, WORDNET, size)
    return {s: {n: as_triple(utils.bootstrap_words_auc(single[n], gallery.pair_bins(emb, single[n]), neither[s], size))
                for n in WORDNET} | {"pairs": {n: len(single[n]) for n in WORDNET}} for s, emb in spaces.items()}


def bats_relations(spaces: dict, index: dict, neither: dict) -> dict:
    """Test 1 for each of the 40 relations of BATS (printed, not drawn: about 50 pairs each)."""
    out = {}
    for family, relations in utils.load_bats().items():
        for name, rows in relations.items():
            pairs = in_vocab(rows, index)
            if len(pairs) >= 10:
                out[name] = {"pairs": len(pairs)} | {s: as_triple(utils.bootstrap_words_auc(pairs, gallery.pair_bins(emb, pairs), neither[s],
                                                                                          len(index))) for s, emb in spaces.items()}
    return out


# --- test 3
def labels_of(pairs: np.ndarray, keys: dict[str, np.ndarray], bats_keys: np.ndarray, covered: np.ndarray, size: int) -> np.ndarray:
    """Index in LABELS of each pair (any order of its two words): the first WordNet relation that holds, then BATS, then neither."""
    lo, hi = pairs.min(axis=1), pairs.max(axis=1)
    key = lo.astype(np.int64) * size + hi
    out = np.where(covered[lo] & covered[hi], LABELS.index(NEITHER), LABELS.index(UNCOVERED))
    for i in range(len(WORDNET) - 1, -1, -1):  # backwards, so that the first relation in the order is the one kept
        out = np.where(np.isin(key, keys[WORDNET[i]]), i, out)
    return np.where(np.isin(key, bats_keys) & (out >= len(WORDNET)), LABELS.index(ANY_BATS), out)


def same_band_controls(size: int, seed: int = 0) -> np.ndarray:
    """For every word, K random other words of its frequency band (sizes x K)."""
    rng = np.random.default_rng(seed)
    band = gallery.band_of(size)
    width = size // gallery.BANDS
    draw = rng.integers(1, width, (size, K))
    start = band * width
    return start[:, None] + (np.arange(size)[:, None] - start[:, None] + draw) % width


def unnamed_share(labels: np.ndarray, seed: int = 0) -> tuple[float, float, float]:
    """Of the pairs (queries x K) whose two words are in WordNet, the share that carries no label, with a 95% interval from resampling
    the query words (a ratio of sums, since a query can have no neighbour in WordNet)."""
    covered = labels != LABELS.index(UNCOVERED)
    unnamed, total = (labels == LABELS.index(NEITHER)).sum(axis=1), covered.sum(axis=1)
    rng = np.random.default_rng(seed)
    picks = (rng.integers(0, len(total), len(total)) for _ in range(RESAMPLES))
    boots = [unnamed[p].sum() / total[p].sum() for p in picks]
    low, high = np.percentile(boots, [2.5, 97.5])
    return float(unnamed.sum() / total.sum()), float(low), float(high)


def inventory(spaces: dict, pairs: dict, covered: np.ndarray, vocab: list[str]) -> dict:
    """Test 3: the share of each label among the top-K neighbours of every word, against random words of the same band, and the share
    of the neighbours in WordNet that no relation names."""
    size = len(vocab)
    keys = {n: utils.pair_keys(pairs[n], size) for n in WORDNET}
    bats_keys = np.concatenate([utils.pair_keys(pairs[n], size) for n in BATS])
    queries = np.repeat(np.arange(size), K)
    label = lambda neighbours: labels_of(np.column_stack([queries, neighbours.ravel()]), keys, bats_keys, covered, size).reshape(size, K)
    share = lambda labels: dict(zip(LABELS, (utils.bootstrap_mean((labels == i).mean(axis=1)) for i in range(len(LABELS)))))
    control = label(same_band_controls(size))
    out = {"control": share(control), "spaces": {}, "unnamed": {}, "unnamed_share": {"same-band control": unnamed_share(control)}}
    rng = np.random.default_rng(0)
    for s, emb in spaces.items():
        neighbours = utils.nearest(emb, np.arange(size), K)
        labels = label(neighbours)
        out["spaces"][s], out["unnamed_share"][s] = share(labels), unnamed_share(labels)
        unnamed = np.flatnonzero(labels.ravel() >= LABELS.index(NEITHER))
        out["unnamed"][s] = [(vocab[queries[i]], vocab[neighbours.ravel()[i]]) for i in rng.choice(unnamed, 30, replace=False)]
    return out


# --- test 4
def first_half_judge(size: int) -> tuple[sparse.csr_matrix, sparse.csr_matrix]:
    """PPMI of the first half of text8 (window WINDOW), and its rows scaled to length 1 (the context of a word, for the overlap)."""
    _, ids = utils.build_vocab(utils.load_text8(), size)  # the vocabulary of train_spaces.py, so the same indices
    m = utils.ppmi(utils.cooccurrence(ids[: len(ids) // 2], size, WINDOW))
    norms = np.sqrt(np.asarray(m.multiply(m).sum(axis=1)).ravel())
    return m, (sparse.diags(np.divide(1, norms, out=np.zeros_like(norms), where=norms > 0)) @ m).tocsr()


def context_features(m: sparse.csr_matrix, rows: sparse.csr_matrix, pairs: np.ndarray, chunk: int = 5_000) -> np.ndarray:
    """(PPMI of the pair, cosine of the two PPMI rows) in the first half, for each pair (n x 2)."""
    out = np.empty((len(pairs), 2))
    for s in range(0, len(pairs), chunk):
        a, b = pairs[s: s + chunk, 0], pairs[s: s + chunk, 1]
        out[s: s + chunk, 0] = np.asarray(m[a, b]).ravel()
        out[s: s + chunk, 1] = np.asarray(rows[a].multiply(rows[b]).sum(axis=1)).ravel()
    return out


def mechanism_sample(pairs: dict, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """The pairs of test 4: the random pairs, and at most PER_RELATION seeded pairs of each relation; with the label of each
    (-1 for the random pairs, else the index in RELATIONS)."""
    rng = np.random.default_rng(seed)
    parts, labels = [pairs[RANDOM]], [np.full(len(pairs[RANDOM]), -1)]
    for i, n in enumerate(RELATIONS):
        p = pairs[n] if len(pairs[n]) <= PER_RELATION else pairs[n][rng.choice(len(pairs[n]), PER_RELATION, replace=False)]
        parts.append(p)
        labels.append(np.full(len(p), i))
    return np.concatenate(parts), np.concatenate(labels)


def designs(log_counts: np.ndarray, features: np.ndarray, labels: np.ndarray) -> dict[str, np.ndarray]:
    """The design matrices of test 4: frequency (intercept, lower and higher log count), frequency and first-half context (PPMI and
    overlap of the rows), and each of them with one indicator per relation (random pairs are the reference)."""
    frequency = frequency_features(log_counts)
    context = np.column_stack([frequency, features])
    onehot = (labels[:, None] == np.arange(len(RELATIONS))[None, :]).astype(float)
    return {"frequency": frequency, "context": context, "frequency + relations": np.column_stack([frequency, onehot]),
            "context + relations": np.column_stack([context, onehot])}


def weighted_fit(x: np.ndarray, y: np.ndarray, w: np.ndarray) -> tuple[np.ndarray, float]:
    """Least squares of y on x with integer weights w, and the weighted R^2."""
    r = np.sqrt(w)
    coef, *_ = np.linalg.lstsq(x * r[:, None], y * r, rcond=None)
    residual = y - x @ coef
    mean = np.average(y, weights=w)
    return coef, float(1 - (w * residual ** 2).sum() / (w * (y - mean) ** 2).sum())


def context_groups(sample: np.ndarray, labels: np.ndarray, features: np.ndarray) -> dict[str, np.ndarray]:
    """Relations 10 and 11 among the random pairs: direct co-occurrence (PPMI > 0), shared context only (PPMI = 0 and an overlap in
    the top TOP_SHARE of the random pairs without co-occurrence), and the rest."""
    random = labels == -1
    apart = random & (features[:, 0] == 0)
    threshold = np.quantile(features[apart, 1], 1 - TOP_SHARE)
    groups = {CONTEXT[0]: random & (features[:, 0] > 0), CONTEXT[1]: apart & (features[:, 1] >= threshold)}
    groups["other random pairs"] = random & ~groups[CONTEXT[0]] & ~groups[CONTEXT[1]]
    return {n: sample[m] for n, m in groups.items()} | {"threshold": threshold}


def mechanism(log_counts: np.ndarray, pairs: dict) -> dict:
    """Test 4 in the half-text spaces: the AUC of the two context relations, the R^2 of frequency and context on random pairs, and the
    effect of each relation on the cosine without and with the context held fixed."""
    m, rows = first_half_judge(len(log_counts))
    sample, labels = mechanism_sample(pairs)
    features = context_features(m, rows, sample)
    groups = context_groups(sample, labels, features)
    threshold = float(groups.pop("threshold"))
    x = designs(log_counts[sample], features, labels)
    random = labels == -1
    spaces = {s: utils.unit(utils.load_space(stem)) for s, stem in HALF_SPACES.items()}
    out = {"pairs": {n: len(p) for n, p in groups.items()}, "overlap_threshold": threshold, "spaces": {}}
    names = list(groups)
    for s, u in spaces.items():
        bins = {n: gallery.to_bin((u[p[:, 0]] * u[p[:, 1]]).sum(axis=1)) for n, p in groups.items()}
        y = (u[sample[:, 0]] * u[sample[:, 1]]).sum(axis=1)
        aucs, r2, effects = [], [], []
        for k, times in enumerate(word_draws(len(u), RESAMPLES)):
            aucs.append(auc_matrix(histograms(bins, groups, times, names))[:2])
            if k > FIT_RESAMPLES:
                continue
            w = times[sample[:, 0]] * times[sample[:, 1]]
            r2.append([weighted_fit(x[d][random], y[random], w[random])[1] for d in ("frequency", "context")])
            effects.append([weighted_fit(x[d], y, w)[0][-len(RELATIONS):] for d in ("frequency + relations", "context + relations")])
        aucs, r2, effects = np.array(aucs), np.array(r2), np.array(effects)
        out["spaces"][s] = {"auc": {f"{a} vs {b}": as_triple(interval(aucs[:, i, j])) for i, a in enumerate(names[:2])
                                    for j, b in enumerate(names) if i != j},
                            "r2_random": {d: as_triple(interval(r2[:, k])) for k, d in enumerate(("frequency", "frequency + context"))},
                            "effect": {n: {d: as_triple(interval(effects[:, k, i])) for k, d in enumerate(("without context", "with context"))}
                                       for i, n in enumerate(RELATIONS)}}
    return out


# --- printing and the claims of the text
def print_orders(result: dict, single: dict, bats40: dict) -> None:
    print("pairs per relation: " + ", ".join(f"{n} {c:,}" for n, c in result["pairs"].items()))
    for s, r in result["spaces"].items():
        print(f"\n{s}: test 1, AUC against neither (95% interval over words)")
        for n, est in r["against_neither"].items():
            extra = f"   single label ({single[s]['pairs'][n]:,} pairs): {fmt(single[s][n])}" if n in WORDNET else ""
            print(f"  {n:26s} {fmt(est)}{extra}")
        signs = resolved(r["matrix"])
        strict = resolved(r["matrix"], "bonferroni_low", "bonferroni_high")
        upper = np.triu_indices(len(RELATIONS), 1)
        print(f"  test 2: {(signs[upper] != 0).sum()} of {result['contrasts']} contrasts resolved at 95% "
              f"({(strict[upper] != 0).sum()} with Bonferroni, z = {result['bonferroni_z']:.2f}); collapsed:")
        for i, j in zip(*upper):
            if signs[i, j] == 0:
                print(f"    {RELATIONS[i]} ~ {RELATIONS[j]}: {r['matrix']['point'][i][j]:.3f} "
                      f"[{r['matrix']['low'][i][j]:.3f}, {r['matrix']['high'][i][j]:.3f}]")
    print("\nBATS, each of its relations against neither: " + "; ".join(
        f"{n} ({v['pairs']}) " + " / ".join(f"{v[s][0]:.2f}" for s in result["spaces"]) for n, v in bats40.items()))


def print_inventory(inv: dict) -> None:
    print(f"\ntest 3: share of the top-{K} neighbours of every word with each label (interval over the query words)")
    print(f"  {'label':22s} " + "".join(f"{s:>26s}" for s in [*inv["spaces"], "same-band control"]))
    for label in LABELS:
        cells = [inv["spaces"][s][label] for s in inv["spaces"]] + [inv["control"][label]]
        print(f"  {label:22s} " + "".join(f"{fmt(c):>26s}" for c in cells))
    print("  share of the neighbours in WordNet that no relation names: "
          + "; ".join(f"{s} {fmt(v)}" for s, v in inv["unnamed_share"].items()))
    for s, rows in inv["unnamed"].items():
        print(f"  {s}, neighbours that no judge names (seeded sample): " + ", ".join(f"{a}/{b}" for a, b in rows))


def print_mechanism(mech: dict) -> None:
    print(f"\ntest 4 (spaces of the second half, judge of the first half): pairs {mech['pairs']}, overlap threshold "
          f"{mech['overlap_threshold']:.3f}")
    for s, r in mech["spaces"].items():
        print(f"  {s}: " + "; ".join(f"AUC {k} {fmt(v)}" for k, v in r["auc"].items()))
        print("    R^2 on random pairs: " + "; ".join(f"{k} {fmt(v)}" for k, v in r["r2_random"].items()))
        for n, e in r["effect"].items():
            kept = e["with context"][0] / e["without context"][0] if e["without context"][0] else float("nan")
            print(f"    {n:26s} effect without context {fmt(e['without context'], '+')}, with context {fmt(e['with context'], '+')}"
                  f" (kept {kept:.0%})")


def check_claims(results: dict) -> None:
    """The claims that the section makes; a failure means the text has to change."""
    for s, r in results["spaces"].items():
        auc = r["against_neither"]
        assert all(auc[n][1] > 0.5 for n in RELATIONS), f"{s}: every relation leaves a trace (above neither)"
        assert abs(auc[RANDOM][0] - 0.5) < 0.01, f"{s}: random pairs are at the level of neither"
        assert max(WORDNET, key=lambda n: auc[n][0]) == "inflection", f"{s}: inflection is the nearest WordNet relation"
        assert min(RELATIONS, key=lambda n: auc[n][0]) == "co-hyponym", f"{s}: co-hyponym is the farthest relation"
        assert results["agreement"]["resolved"][s] >= 60, f"{s}: most of the 78 orders are resolved"
        assert results["inventory"]["unnamed_share"][s][1] > 0.6, f"{s}: most neighbours in WordNet carry no label"
    assert results["agreement"]["opposite"] == 0, "the two losses never resolve an order in opposite directions"
    assert results["spearman_between_spaces"][0] > 0.9, "the two losses order the relations alike"
    assert results["inventory"]["unnamed_share"]["same-band control"][1] > 0.95, "random words of the band carry almost no label"
    for s, r in results["mechanism"]["spaces"].items():
        assert r["auc"]["shared context only vs direct co-occurrence"][1] > 0.5, f"{s}: shared context is nearer than co-occurrence"
        assert r["r2_random"]["frequency + context"][0] < 0.2, f"{s}: the first-half context explains little of the cosine"
        for n, e in r["effect"].items():
            kept = e["with context"][0] / e["without context"][0]
            assert e["with context"][1] > 0 and 0.4 < kept < 0.8, f"{s}, {n}: the relation keeps part of its effect"


def main() -> None:
    vocab, index, counts = utils.load_vocab()
    size = len(vocab)
    pairs, wordnet, covered = judged_pairs(vocab, index)
    spaces = {s: utils.load_space(stem) for s, stem in SPACES.items()}
    neither = {s: neither_histogram(emb, covered, pairs) for s, emb in spaces.items()}
    results = order_tests(spaces, pairs, neither, size)
    results["agreement"] = agreement(results)
    results["single_label"] = single_label_check(spaces, wordnet, neither, size)
    results["bats_relations"] = bats_relations(spaces, index, neither)
    print_orders(results, results["single_label"], results["bats_relations"])
    print(f"\ntest 5: Spearman of the AUCs against neither between the spaces {fmt(results['spearman_between_spaces'])}; "
          f"contrasts {results['agreement']}")
    results["inventory"] = inventory(spaces, pairs, covered, vocab)
    print_inventory(results["inventory"])
    results["mechanism"] = mechanism(np.log(counts.astype(float)), pairs)
    print_mechanism(results["mechanism"])
    utils.save_results("relation_collapse", results)
    figures.against_neither(results)
    figures.matrix(results, RELATIONS)
    figures.inventory(results["inventory"], LABELS)
    figures.mechanism(results["mechanism"], RELATIONS)
    check_claims(results)


if __name__ == "__main__":
    main()
