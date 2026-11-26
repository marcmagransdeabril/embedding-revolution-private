"""Question Q2 of the chapter "Meaning as Likeness" (section "Which Relations Does Nearness Tell Apart?"): which relations does the
nearness of a space tell apart? A loss trained on company rewards any relation that leaves a trace in company, so nearness is expected to
mix many relations; nearness is one number per pair, so it cannot say which relation holds, and the most it can do is put relations
in an order of how near their pairs are.

Spaces: PPMI-SVD and SGNS of the gallery (text8, 30,000 words, d = 100, seed 0).
Relations, each a set of unordered pairs of words of the vocabulary:
  WordNet 3.0: inflection (a shared base form, by morphy's rules and exception lists), derivation ("+"), synonym (a shared synset),
    antonym ("!"), hypernym (one IS-A step), meronym (part, member or substance), co-hyponym (the same direct hypernym, in different
    synsets); a pair that holds several counts in each, and the pairs that hold only one of them are a robustness check;
  BATS 3.0: each of its 40 relations adds its pairs to the relation of WordNet that it names (BATS_TO_RELATION: inflectional to inflection,
    derivational to derivation, the hypernyms and hyponyms to hypernym, the meronyms to meronym, the synonyms to synonym, the antonyms to
    antonym), and its encyclopedic family is the relation encyclopedic, which WordNet does not hold;
  controls: neither (both words in WordNet, none of the eight relations, from WordNet or BATS: the baseline of every AUC), random pairs
    of the vocabulary.

Three tests. (1) The label of every pair of the vocabulary (how many hold each relation and how many relations a pair holds); the share
of the neighbours of every word, by rank (1 to 1,000), that hold a relation, with a seeded sample of the nearest neighbours that no judge
names; and, for each relation, the distribution of the cosine of its pairs against that of the pairs of no relation. (2) For each
relation, the probability that one of its pairs is nearer than a pair of neither (AUC, 0.5 if the relation leaves no trace). (3) Whether
the two losses order the relations alike: the Spearman correlation of their AUCs against neither.
Every interval is a 95% percentile bootstrap over the words of the vocabulary (RESAMPLES; FIT_RESAMPLES for the shares by rank), the
same draws for every relation and both spaces; the histogram of neither is held fixed.

Expectation (written before the run): every relation is above neither (any relation leaves a trace in company), with inflection,
antonym and co-hyponym the nearest and hypernym and meronym the farthest; more than half of the nearest neighbours carry no label; the
two losses order the relations alike (Spearman above 0.8).

Prints every number; saves results/relation_collapse.json and the figures relation_collapse_auc.png, relation_collapse_inventory.png and relation_collapse_neighbours.png
(drawn by relation_collapse_figures.py).
"""
from __future__ import annotations

import numpy as np
from scipy.stats import spearmanr

import gallery
import relation_collapse_figures as figures
import utils

SPACES = {"PPMI-SVD": "ppmi_svd_s0", "SGNS": "sgns_s0"}
WORDNET = ["inflection", "derivation", "synonym", "antonym", "hypernym", "meronym", "co-hyponym"]  # the seven relations of WordNet
ENCYCLOPEDIC = "encyclopedic"  # what only an encyclopedia holds; no dictionary lists it
RELATIONS = WORDNET + [ENCYCLOPEDIC]  # the relations, whichever judge supplies their pairs
RANDOM, NEITHER, UNCOVERED = "random pairs", "no relation (in WordNet)", "not in WordNet"
# The relation that each of the 40 relations of BATS adds its pairs to, by the letter and number that start its name (I01, L07, ...)
BATS_TO_RELATION = {**{f"I{i:02d}": "inflection" for i in range(1, 11)}, **{f"D{i:02d}": "derivation" for i in range(1, 11)},
                    **{f"E{i:02d}": ENCYCLOPEDIC for i in range(1, 11)}, "L01": "hypernym", "L02": "hypernym", "L03": "hypernym",
                    "L04": "meronym", "L05": "meronym", "L06": "meronym", "L07": "synonym", "L08": "synonym", "L09": "antonym",
                    "L10": "antonym"}
LABELS = WORDNET + [ENCYCLOPEDIC, NEITHER, UNCOVERED]  # the labels of a neighbour in test 1
BINS = gallery.BINS
RANK_BINS = [(1, 1), (2, 2), (3, 4), (5, 9), (10, 19), (20, 49), (50, 99), (100, 199), (200, 499), (500, 1000)]  # ranks of a neighbour
RANK_MAX = RANK_BINS[-1][1]
ANY = "any relation"  # the label of a pair that holds at least one of the eight relations
RESAMPLES, FIT_RESAMPLES, RANDOM_PAIRS = 1000, 200, 200_000


def fmt(estimate: tuple[float, float, float], sign: str = "") -> str:
    """A number with its bootstrap interval, as it is printed everywhere."""
    return f"{estimate[0]:{sign}.3f} [{estimate[1]:{sign}.3f}, {estimate[2]:{sign}.3f}]"


# --- the judges
def random_pairs(size: int, n: int, seed: int = 0) -> np.ndarray:
    """`n` seeded pairs of distinct words of the vocabulary, drawn uniformly (repeats removed)."""
    rng = np.random.default_rng(seed)
    a = rng.integers(0, size, n)
    return utils.pair_array(zip(a, (a + rng.integers(1, size, n)) % size))


def in_vocab(pairs, index: dict[str, int]) -> np.ndarray:
    return utils.pair_array((index[a], index[b]) for a, b in pairs if a in index and b in index)


def judged_pairs(vocab: list[str], index: dict[str, int]) -> tuple[dict, dict, np.ndarray]:
    """The pairs of every relation of tests 1 and 2 (each relation holds the pairs of every judge that names it, WordNet and the relations
    of BATS that belong to it, and a pair counts in every relation that it holds; and random pairs), the WordNet relations as WordNet
    gives them, and the WordNet coverage of the vocabulary."""
    wordnet, covered = utils.wordnet_relations(vocab)
    pairs = {name: wordnet[name] for name in WORDNET}  # every pair holds every relation that it has, so the sets overlap
    pairs[ENCYCLOPEDIC] = np.zeros((0, 2), dtype=np.int64)
    for relations in utils.load_bats().values():
        for name, rows in relations.items():
            pairs[BATS_TO_RELATION[name[:3]]] = np.concatenate([pairs[BATS_TO_RELATION[name[:3]]], in_vocab(rows, index)])
    for name in RELATIONS:
        pairs[name] = pairs[name][np.unique(utils.pair_keys(pairs[name], len(vocab)), return_index=True)[1]]
    pairs[RANDOM] = random_pairs(len(vocab), RANDOM_PAIRS)
    return pairs, wordnet, covered


def neither_histogram(emb: np.ndarray, covered: np.ndarray, pairs: dict) -> np.ndarray:
    """Histogram of the cosine of the pairs of two WordNet words that hold none of the relations, whichever judge names them (WordNet
    and BATS; exact, every pair scored). A pair that holds two relations is taken out once."""
    _, both = gallery.pair_histograms(emb, covered)
    size = len(covered)
    held = [pairs[name][covered[pairs[name]].all(axis=1)] for name in RELATIONS]  # an inflected form need not be in WordNet itself
    keys = np.unique(np.concatenate([utils.pair_keys(p, size) for p in held]))
    both = both - np.bincount(gallery.pair_bins(emb, np.column_stack([keys // size, keys % size])), minlength=BINS)
    assert (both >= 0).all()
    return both


# --- the bootstrap over words, shared by tests 2 and 3
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


# --- tests 2 and 3
def order_tests(spaces: dict, pairs: dict, neither: dict, size: int) -> dict:
    """AUC of every relation against neither, and the agreement of the two spaces, with paired intervals."""
    names = RELATIONS + [RANDOM]
    bins = {s: {n: gallery.pair_bins(emb, pairs[n]) for n in names} for s, emb in spaces.items()}
    against, rho = {s: [] for s in spaces}, []
    for times in word_draws(size, RESAMPLES):
        for s in spaces:
            h = histograms(bins[s], pairs, times, names)
            against[s].append([utils.histogram_auc(row, neither[s]) for row in h])
        a, b = (np.array(against[s][-1][: len(RELATIONS)]) for s in spaces)
        rho.append(spearmanr(a, b).statistic)
    out = {"pairs": {n: len(pairs[n]) for n in names}, "spaces": {}, "spearman_between_spaces": as_triple(interval(np.array(rho)))}
    for s in spaces:
        auc = np.array(against[s])
        out["spaces"][s] = {"against_neither": {n: as_triple(interval(auc[:, i])) for i, n in enumerate(names)}}
    return out


def single_label_check(spaces: dict, wordnet: dict, neither: dict, size: int) -> dict:
    """Test 2 on the WordNet pairs that hold only one of its relations (each such pair belongs to one relation only)."""
    single = utils.single_label(wordnet, WORDNET, size)
    return {s: {n: as_triple(utils.bootstrap_words_auc(single[n], gallery.pair_bins(emb, single[n]), neither[s], size))
                for n in WORDNET} | {"pairs": {n: len(single[n]) for n in WORDNET}} for s, emb in spaces.items()}


def bats_relations(spaces: dict, index: dict, neither: dict) -> dict:
    """Test 2 for each of the 40 relations of BATS (printed, not drawn: about 50 pairs each)."""
    out = {}
    for family, relations in utils.load_bats().items():
        for name, rows in relations.items():
            pairs = in_vocab(rows, index)
            if len(pairs) >= 10:
                out[name] = {"pairs": len(pairs)} | {s: as_triple(utils.bootstrap_words_auc(pairs, gallery.pair_bins(emb, pairs), neither[s],
                                                                                          len(index))) for s, emb in spaces.items()}
    return out


# --- test 1
def labels_of(pairs: np.ndarray, keys: dict[str, np.ndarray], covered: np.ndarray, size: int) -> np.ndarray:
    """Which of LABELS each pair holds (any order of its two words), a boolean array (pairs x LABELS). A pair holds every relation that
    it has, so its row can have several True; a pair with no relation holds NEITHER if its two words are in WordNet and UNCOVERED if not."""
    lo, hi = pairs.min(axis=1), pairs.max(axis=1)
    key = lo.astype(np.int64) * size + hi
    out = np.zeros((len(key), len(LABELS)), dtype=bool)
    for name in RELATIONS:
        out[:, LABELS.index(name)] = np.isin(key, keys[name])
    none = ~out.any(axis=1)
    out[:, LABELS.index(NEITHER)] = none & covered[lo] & covered[hi]
    out[:, LABELS.index(UNCOVERED)] = none & ~(covered[lo] & covered[hi])
    return out


def unnamed_share(labels: np.ndarray, seed: int = 0) -> tuple[float, float, float]:
    """Of the pairs (queries x ranks x LABELS) whose two words are in WordNet, the share that holds no relation, with a 95% interval from
    resampling the query words (a ratio of sums, since a query can have no neighbour in WordNet)."""
    covered = ~labels[:, :, LABELS.index(UNCOVERED)]
    unnamed, total = labels[:, :, LABELS.index(NEITHER)].sum(axis=1), covered.sum(axis=1)
    rng = np.random.default_rng(seed)
    picks = (rng.integers(0, len(total), len(total)) for _ in range(RESAMPLES))
    boots = [unnamed[p].sum() / total[p].sum() for p in picks]
    low, high = np.percentile(boots, [2.5, 97.5])
    return float(unnamed.sum() / total.sum()), float(low), float(high)


def all_pairs_inventory(pairs: dict, covered: np.ndarray) -> dict:
    """Test 1, first part: of all the pairs of the vocabulary (counted exactly, so with no interval), how many hold each label, how
    many hold any relation, and how many relations a pair holds."""
    size = len(covered)
    total, wordnet_words = size * (size - 1) // 2, int(covered.sum())
    keys = {n: utils.pair_keys(pairs[n], size) for n in RELATIONS}
    allk, held = np.unique(np.concatenate(list(keys.values())), return_counts=True)
    both = covered[allk // size] & covered[allk % size]
    inside = wordnet_words * (wordnet_words - 1) // 2
    counts = {n: len(keys[n]) for n in RELATIONS}
    counts[NEITHER] = inside - int(both.sum())
    counts[UNCOVERED] = total - len(allk) - counts[NEITHER]
    return {"pairs": total, "wordnet_pairs": inside, "labels": counts, "any_relation": len(allk), "any_relation_in_wordnet": int(both.sum()),
            "relations_per_pair": {str(k): int((held == k).sum()) for k in (1, 2, 3)} | {"4 or more": int((held >= 4).sum())},
            "alone": {n: float(np.mean(held[np.searchsorted(allk, keys[n])] == 1)) for n in RELATIONS}}


def inventory(spaces: dict, pairs: dict, covered: np.ndarray, vocab: list[str]) -> dict:
    """Test 1, second part: the share of each label among the neighbours of every word, by rank of the neighbour (RANK_BINS, up to the
    RANK_MAX-th), with a bootstrap interval over the query words, and the share of the neighbours in WordNet that no relation names."""
    size = len(vocab)
    keys = {n: utils.pair_keys(pairs[n], size) for n in RELATIONS}
    queries = np.arange(size)
    out = {"bins": [list(b) for b in RANK_BINS], "spaces": {}, "unnamed": {}, "unnamed_share": {}}
    rng = np.random.default_rng(0)
    for s, emb in spaces.items():
        neighbours = utils.nearest(emb, queries, RANK_MAX)
        out["spaces"][s], out["unnamed_share"][s] = [], []
        for first, last in RANK_BINS:
            block = neighbours[:, first - 1: last]
            width = last - first + 1
            labels = labels_of(np.column_stack([np.repeat(queries, width), block.ravel()]), keys, covered, size)
            labels = labels.reshape(size, width, len(LABELS))
            shares = {label: labels[:, :, i].mean(axis=1) for i, label in enumerate(LABELS)}
            shares[ANY] = labels[:, :, : len(RELATIONS)].any(axis=2).mean(axis=1)
            out["spaces"][s].append({label: utils.bootstrap_mean(v, FIT_RESAMPLES) for label, v in shares.items()})
            out["unnamed_share"][s].append(unnamed_share(labels))
            if first == 1:
                flat = labels.reshape(-1, len(LABELS))
                unnamed = np.flatnonzero(flat[:, LABELS.index(NEITHER):].any(axis=1))
                out["unnamed"][s] = [(vocab[queries[i]], vocab[block.ravel()[i]]) for i in rng.choice(unnamed, 30, replace=False)]
    return out


def cosine_histograms(spaces: dict, pairs: dict, neither: dict) -> dict:
    """Test 1, second part: the histogram (BINS bins of the cosine, exact) of the cosine of the pairs of each relation, of random
    pairs and of the pairs of no relation (all pairs of two WordNet words that hold none of the relations), in each space."""
    names = RELATIONS + [RANDOM]
    return {"bins": BINS, "spaces": {s: {n: np.bincount(gallery.pair_bins(emb, pairs[n]), minlength=BINS).tolist() for n in names}
                                     | {NEITHER: neither[s].tolist()} for s, emb in spaces.items()}}


# --- printing and the claims of the text
def print_orders(result: dict, single: dict, bats40: dict) -> None:
    print("pairs per relation: " + ", ".join(f"{n} {c:,}" for n, c in result["pairs"].items()))
    for s, r in result["spaces"].items():
        print(f"\n{s}: test 2, AUC against neither (95% interval over words)")
        for n, est in r["against_neither"].items():
            extra = f"   single label ({single[s]['pairs'][n]:,} pairs): {fmt(single[s][n])}" if n in WORDNET else ""
            print(f"  {n:26s} {fmt(est)}{extra}")
    print("\nBATS, each of its relations against neither: " + "; ".join(
        f"{n} ({v['pairs']}) " + " / ".join(f"{v[s][0]:.2f}" for s in result["spaces"]) for n, v in bats40.items()))


def print_all_pairs(inv: dict) -> None:
    print(f"\ntest 1, all pairs of the vocabulary: {inv['pairs']:,} pairs, {inv['wordnet_pairs']:,} of two WordNet words")
    for label, count in inv["labels"].items():
        print(f"  {label:26s} {count:>13,}  {count / inv['pairs']:.2e} of all pairs")
    print(f"  pairs that hold a relation: {inv['any_relation']:,} ({inv['any_relation'] / inv['pairs']:.3%} of all pairs, "
          f"{inv['any_relation_in_wordnet'] / inv['wordnet_pairs']:.3%} of the pairs of two WordNet words)")
    print("  relations held by a pair that holds one: " + ", ".join(f"{k}: {v:,} ({v / inv['any_relation']:.1%})"
                                                                  for k, v in inv["relations_per_pair"].items()))
    print("  share of the pairs of a relation that hold it alone: " + ", ".join(f"{n} {v:.2f}" for n, v in inv["alone"].items()))


def print_cosines(cosines: dict) -> None:
    print("\ntest 1, second part: median cosine of the pairs of each relation and of random pairs")
    middle = lambda h: -1 + (np.searchsorted(np.cumsum(h), 0.5 * np.sum(h)) + 0.5) * 2 / cosines["bins"]
    for n in [*RELATIONS, RANDOM, NEITHER]:
        print(f"  {n:16s}" + "".join(f"  {s} {middle(np.array(cosines['spaces'][s][n])):+.3f}" for s in cosines["spaces"]))


def print_inventory(inv: dict) -> None:
    print("\ntest 1: share of the neighbours of every word with each label, by rank of the neighbour (interval over the query words)")
    for s, bins in inv["spaces"].items():
        print(f"  {s}")
        print(f"  {'label':26s} " + "".join(f"{f'{a}-{b}' if a != b else str(a):>10s}" for a, b in inv["bins"]))
        for label in [*LABELS, ANY]:
            print(f"  {label:26s} " + "".join(f"{b[label][0]:10.4f}" for b in bins))
        print("  share of the neighbours in WordNet that no relation names: "
              + ", ".join(f"{u[0]:.3f} [{u[1]:.3f}, {u[2]:.3f}]" for u in inv["unnamed_share"][s]))
    for s, rows in inv["unnamed"].items():
        print(f"  {s}, nearest neighbours that no judge names (seeded sample): " + ", ".join(f"{a}/{b}" for a, b in rows))


def check_claims(results: dict) -> None:
    """The claims that the section makes; a failure means the text has to change."""
    for s, r in results["spaces"].items():
        auc = r["against_neither"]
        assert all(auc[n][1] > 0.5 for n in RELATIONS), f"{s}: every relation leaves a trace (above neither)"
        assert abs(auc[RANDOM][0] - 0.5) < 0.01, f"{s}: random pairs are at the level of neither"
        assert max(WORDNET, key=lambda n: auc[n][0]) == "inflection", f"{s}: inflection is the nearest WordNet relation"
        assert min(RELATIONS, key=lambda n: auc[n][0]) == "co-hyponym", f"{s}: co-hyponym is the farthest relation"
        by_rank = [b[ANY] for b in results["inventory"]["spaces"][s]]
        base = results["all_pairs"]["any_relation"] / results["all_pairs"]["pairs"]
        assert all(x[0] > y[0] for x, y in zip(by_rank, by_rank[1:])), f"{s}: the share of neighbours with a relation falls with the rank"
        assert by_rank[0][1] > 100 * base and by_rank[-1][1] > base, f"{s}: neighbours hold more relations than pairs in general"
        assert 1 - by_rank[0][0] > 0.5, f"{s}: most of the nearest neighbours hold no relation"
    assert results["spearman_between_spaces"][0] > 0.9, "the two losses order the relations alike"


def main() -> None:
    vocab, index, _ = utils.load_vocab()
    size = len(vocab)
    pairs, wordnet, covered = judged_pairs(vocab, index)
    spaces = {s: utils.load_space(stem) for s, stem in SPACES.items()}
    results_all = all_pairs_inventory(pairs, covered)
    print_all_pairs(results_all)
    inventory_result = inventory(spaces, pairs, covered, vocab)
    print_inventory(inventory_result)
    neither = {s: neither_histogram(emb, covered, pairs) for s, emb in spaces.items()}
    results = order_tests(spaces, pairs, neither, size)
    results["single_label"] = single_label_check(spaces, wordnet, neither, size)
    results["bats_relations"] = bats_relations(spaces, index, neither)
    results["inventory"], results["all_pairs"] = inventory_result, results_all
    results["cosines"] = cosine_histograms(spaces, pairs, neither)
    print_cosines(results["cosines"])
    print_orders(results, results["single_label"], results["bats_relations"])
    print(f"\ntest 3: Spearman of the AUCs against neither between the spaces {fmt(results['spearman_between_spaces'])}")
    utils.save_results("relation_collapse", results)
    figures.against_neither(results)
    figures.inventory(results["all_pairs"], results["cosines"], LABELS, RELATIONS, NEITHER)
    figures.neighbours(results["inventory"])
    check_claims(results)


if __name__ == "__main__":
    main()
