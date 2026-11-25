# SKELETON: written, not yet run (the first exploration of Q3 waits for the author; running it draws the blinded sample); `make test-code` skips it.
"""First exploration for Q3 of the chapter "Meaning as Likeness": what relations, if any, hold between pairs that no judge names, at the
near and the far end of the cosine? It is open-ended on purpose: no list of relations is given to the rater.

Population: the pairs of two WordNet words (the null of Q2, 175 million per space) that hold none of the 13 judged relations of
relation_collapse.py. Per space (PPMI-SVD and SGNS of the gallery), three strata of that population, cut at the quantiles of its own
cosine distribution (so that a cut means the same in both spaces): top (at or above the 99th percentile), bottom (at or below the 1st
percentile) and middle (the 49.5th to the 50.5th percentile, the control: what a rater finds between two words that the space puts at
the typical cosine). Each stratum is sampled uniformly, N_PER pairs, from all its pairs (two passes over every pair, no
approximation). Besides, a positive control of CONTROL_PER pairs of each of the seven relations of WordNet, which are known to hold a relation.

Blinding. The pairs of all strata, of both spaces and of the positive control are shuffled into one file (`unlabelled_blinded.csv`: an
identifier and the two words, in random order), and the stratum, the space, the cosine and the judged relation stay in a key
(`unlabelled_key.json`) that the rater does not read. The rater, a language model, is given the instruction RATER_PROMPT and answers for
each identifier "relation" or "none" and a name of its own choosing if "relation" (file `unlabelled_labels.csv`; the pairs go to the rater in batches of BATCH per request, with the instruction once per batch, to keep the
cost to a few requests: `batch_requests`; the file has the hash of the
blinded file in its first line, so that labels of another sample are refused). There is no list of relations and no example. This
script then joins the labels with the key and reports, per stratum, the share of pairs with a relation (95% bootstrap interval over
the pairs), the names given, and the share of the positive control found (the rater must find it, or "none" means nothing).

Reading it. A language model finds a relation between many pairs of words, so the share in a stratum means nothing alone: what counts is
the difference between the strata and the control, and the positive control tells whether the rater detects what is there. One rater,
one prompt, 50 pairs per stratum: an exploration with intervals of about 15 points, not a measurement.

Expectation (written before the labelling): the top stratum has more pairs with a relation than the middle one, and the bottom stratum
has fewer or the same; the positive control is found in more than 90% of pairs; the names in the top stratum are of topic and
co-occurrence (field, place and event, part and whole) and not of the seven relations of WordNet; the bottom stratum gets "none" for most
pairs.

Prints the thresholds and the counts, never a pair, so that the person reading the output stays blind; saves results/unlabelled_blinded.csv
and results/unlabelled_key.json. What is done with the labels is in relation_unlabelled_analysis.py.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

import gallery
import relation_collapse as rc
import utils

STRATA = {"top 1%": (0.99, None), "bottom 1%": (None, 0.01), "middle": (0.495, 0.505)}
N_PER, CONTROL_PER, SEED, BLOCK, BATCH = 50, 8, 0, 1000, 60


def output(stem: str, extension: str) -> Path:
    """Path of a file that this script makes in results/ (built from its parts, so that it is not taken for a committed data file)."""
    return utils.RESULTS / f"{stem}.{extension}"


BLIND, KEY = output("unlabelled_blinded", "csv"), output("unlabelled_key", "json")
RATER_PROMPT = ("Below is a list of pairs of English words. Between the two words of a pair there may be some relation, or none. "
                "For each pair, answer 'relation' or 'none'. If you answer 'relation', try to give it a short name of your own choosing; "
                "there is no list to choose from.")


def blocks(u: np.ndarray):
    """Blocks of the upper triangle of the cosine matrix of the unit rows `u`: the rows, the columns, the bin of each cosine, and the mask
    of the pairs i < j."""
    for start in range(0, len(u), BLOCK):
        rows, cols = np.arange(start, min(start + BLOCK, len(u))), np.arange(start, len(u))
        yield rows, cols, gallery.to_bin(u[rows] @ u[cols].T), rows[:, None] < cols[None, :]


def unlabelled_histogram(u: np.ndarray, labelled_keys: np.ndarray) -> np.ndarray:
    """Exact histogram of the cosine of the pairs that hold none of the judged relations: all pairs, less the judged ones."""
    m = len(u)
    both = np.zeros(gallery.BINS, dtype=np.int64)
    for _, _, bins, upper in blocks(u):
        both += np.bincount(bins[upper], minlength=gallery.BINS)
    i, j = labelled_keys // m, labelled_keys % m
    judged = np.bincount(gallery.to_bin((u[i] * u[j]).sum(axis=1)), minlength=gallery.BINS)
    return both - judged


def stratum_bins(hist: np.ndarray) -> dict[str, tuple[int, int]]:
    """For each stratum the range of bins [low, high) of its pairs, from the quantiles of the histogram."""
    cumulative = np.cumsum(hist) / hist.sum()
    at = lambda q, default: default if q is None else int(np.searchsorted(cumulative, q))
    return {name: (at(lo, 0), at(hi, gallery.BINS)) for name, (lo, hi) in STRATA.items()}


def sample_strata(u: np.ndarray, labelled_keys: np.ndarray, ranges: dict, space: int) -> dict[str, np.ndarray]:
    """N_PER pairs drawn uniformly from each stratum among the pairs that hold none of the judged relations: every candidate gets a random
    number, and the N_PER smallest are kept over all blocks."""
    m = len(u)
    best = {name: np.zeros((0, 2)) for name in STRATA}  # (random number, key)
    for rows, cols, bins, upper in blocks(u):
        rng = np.random.default_rng([SEED, space, int(rows[0])])
        for name, (low, high) in ranges.items():
            r, c = np.nonzero(upper & (bins >= low) & (bins < high))
            keys = rows[r].astype(np.int64) * m + cols[c]
            free = labelled_keys[np.minimum(np.searchsorted(labelled_keys, keys), len(labelled_keys) - 1)] != keys
            merged = np.vstack([best[name], np.column_stack([rng.random(free.sum()), keys[free]])])
            best[name] = merged[np.argsort(merged[:, 0])[:N_PER]]
    return {name: b[:, 1].astype(np.int64) for name, b in best.items()}


def judged_keys(size: int, pairs: dict, covered: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The words of WordNet (their indices in the vocabulary) and, sorted, the key i * m + j of every judged pair of two of them in the
    numbering of these words (0 to m - 1)."""
    cov = np.flatnonzero(covered)
    local = np.full(size, -1)
    local[cov] = np.arange(len(cov))
    judged = np.concatenate([pairs[n] for n in rc.RELATIONS])
    judged = judged[covered[judged].all(axis=1)]
    return cov, np.unique(local[judged[:, 0]].astype(np.int64) * len(cov) + local[judged[:, 1]])


def draw_sample(vocab: list[str], pairs: dict, covered: np.ndarray) -> tuple[list[dict], dict]:
    """Every pair of the sample with its stratum, space, cosine and words (the key), and the thresholds in cosines, for printing."""
    cov, labelled_keys = judged_keys(len(vocab), pairs, covered)
    rows, thresholds = [], {}
    for s, (name, stem) in enumerate(rc.SPACES.items()):
        u = utils.unit(utils.load_space(stem)[cov].astype(np.float32))
        hist = unlabelled_histogram(u, labelled_keys)
        ranges = stratum_bins(hist)
        centres = (np.arange(gallery.BINS) + 0.5) / gallery.BINS * 2 - 1
        thresholds[name] = {k: [round(float(centres[min(a, gallery.BINS - 1)]), 3), round(float(centres[min(b, gallery.BINS) - 1]), 3),
                                int(hist[a:b].sum())] for k, (a, b) in ranges.items()}
        for stratum, keys in sample_strata(u, labelled_keys, ranges, s).items():
            i, j = keys // len(cov), keys % len(cov)
            for a, b in zip(i, j):
                rows.append({"space": name, "stratum": stratum, "cosine": round(float(u[a] @ u[b]), 3), "words": [cov[a], cov[b]], "judged": None})
    rng = np.random.default_rng(SEED)
    for relation in rc.WORDNET:
        free = pairs[relation][covered[pairs[relation]].all(axis=1)]
        for a, b in free[rng.choice(len(free), CONTROL_PER, replace=False)]:
            rows.append({"space": None, "stratum": "positive control", "cosine": None, "words": [int(a), int(b)], "judged": relation})
    return rows, thresholds


def blind(rows: list[dict], vocab: list[str]) -> dict[str, dict]:
    """Shuffle the sample, give each pair an identifier and a random order of its two words, and write the blinded file."""
    rng = np.random.default_rng(SEED + 1)
    key = {}
    BLIND.parent.mkdir(exist_ok=True)
    with BLIND.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "word_a", "word_b"])
        for k, i in enumerate(rng.permutation(len(rows))):
            row, flip = rows[i], bool(rng.integers(2))
            a, b = (row["words"][::-1] if flip else row["words"])
            ident = f"p{k + 1:03d}"
            writer.writerow([ident, vocab[a], vocab[b]])
            key[ident] = {**row, "words": [vocab[a], vocab[b]]}
    KEY.write_text(json.dumps(key, indent=1))
    return key


def batch_requests() -> list[str]:
    """The requests to a rater that is an API, one per BATCH pairs of the blinded file, each with the instruction once (a request per
    pair would repeat it 356 times). The answers are read back as lines `id,answer,name`."""
    lines = [f"{r['id']}: {r['word_a']} / {r['word_b']}" for r in csv.DictReader(BLIND.open())]
    ask = "Answer one line per pair, as: id,answer,name (the name empty if the answer is none)."
    return [f"{RATER_PROMPT}\n{ask}\n\n" + "\n".join(lines[k: k + BATCH]) for k in range(0, len(lines), BATCH)]


def blind_hash() -> str:
    return hashlib.sha256(BLIND.read_bytes()).hexdigest()


def main() -> None:
    vocab, index, _ = utils.load_vocab()
    if BLIND.exists() and KEY.exists():
        print(f"{BLIND.name} exists; delete it and {KEY.name} to draw the sample again")
        return
    pairs, _, covered = rc.judged_pairs(vocab, index)
    rows, thresholds = draw_sample(vocab, pairs, covered)
    blind(rows, vocab)
    print(f"sample of {len(rows)} pairs written to {BLIND.name} (key in {KEY.name}, not to be read before the labels are written)")
    for space, ranges in thresholds.items():
        print(f"  {space}: " + "; ".join(f"{k}: cosine {a} to {b}, {n:,} pairs" for k, (a, b, n) in ranges.items()))
    print(f"the rater labels it in {len(batch_requests())} batches of {BATCH}; see relation_unlabelled_analysis.py for what is done with the labels")


if __name__ == "__main__":
    main()
