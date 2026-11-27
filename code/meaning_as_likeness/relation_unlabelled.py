"""Test 1 of Q3 of the chapter "Meaning as Likeness" (section "Is Any Relation Associated with Far Pairs?"), an exploration: is there a
relation that holds for the pairs that both spaces put far apart? Q2 found that every named relation sits near, so a relation of the far
pairs, if any, is not on the list of the judges. Here an open rater, a language model, is asked for every relation that it can think of
between two words, or none, on far pairs mixed blind with pairs of known relation and with two comparison groups. The known pairs measure
how well the rater finds a relation that is there (the control); the far pairs give a list of relations, each with its pairs, or "none";
the random and the near pairs say what that list is to be compared with.

Samples (seeded, SEED; exact, every pair scored). Two runs, each a blinded file, labelled apart and read together by the report:
  main: FAR_N pairs far in both spaces, and KNOWN_N pairs of each of the 8 relations of relation_collapse.py (WordNet and BATS), drawn
    at any cosine (the rater is not graded, so the cosine of a known pair does not matter). Far: drawn uniformly from the pairs of two
    WordNet words that hold none of the 8 relations and whose cosine is at or below the 1st percentile of that population in both
    PPMI-SVD and SGNS (the cut of each space is its own, so that it means the same in both).
  extra: more far pairs, so that the two runs hold FAR_TOTAL far pairs (a uniform sample, no pair twice), RANDOM_N random pairs with no relation (the same population at any cosine: the baseline of the far pairs), NEAR_N near pairs
    (at or above the 99th percentile of that population in both spaces: where the rater is expected to find relations that no judge
    names, which says whether it can find an unnamed relation when one is there), and RANDOM_ANY_N completely random pairs, judged or
    not (what the rater says of the pairs of two WordNet words as they come). With the known pairs (8 relations, any cosine) the five
    kinds of pair are: random with a relation, random with none, completely random, far with none and near with none.
The pairs of a run are shuffled into one blinded file (an identifier and the two words in random order); the subset, the relations and
the cosines stay in a key that only the report reads. Pairs are never repeated across subsets.

Rater: claude-opus-5.5 through `kiro-cli acp` (acp_client.py), a new session for every batch of BATCH pairs, so that no batch sees
another, and the model pinned and checked. The prompt is minimal (RATER_PROMPT): no source of the words, no list of relations, no
example. The labels carry the hash of the blinded file and the model, and labels of another sample or another model are refused.

Consolidation: the rater names relations freely ("antonym", "opposite", "opposites"), so a second pass of the same model gets the list
of distinct names alone (no pair, no subset) together with the names of the 8 relations, each with a one-line definition, and maps every
name to a canonical name of its choice (MERGE_PROMPT). A known pair is recovered when the canonical name of its relation is among the
canonical names of its answer. The map is printed in full and kept as it is: the names of a second run are added to it, never remapped.
The first run showed that "encyclopedic" absorbed vague names ("related_to"), which lowers its precision and inflates its recall.

Report. Control: for each relation, the recall (95% bootstrap interval over its pairs) and the share with any relation; for each
canonical name of a relation, the precision among the known pairs given it; the confusion of the drawn relation with the canonical
names given; the share of "none". Open subsets (far, random, near): the share with a relation, the share of "none", the relations per
pair, every canonical relation given with its count, share and pairs, and the differences between the shares of far, random and near
(95% bootstrap interval over pairs). A pair can have several relations, so the shares of relations can add up to more than 100%.

Expectation (written before the second run): the rater names a relation for few far pairs and for more random pairs, and for most near
pairs; the share of "none" among far pairs is not below that of random pairs by more than a few points, so that far is as empty of
relations as ordinary unrelated pairs, and no relation of meaning recurs among the far pairs.

Steps (python relation_unlabelled.py STEP [extra]): sample (no model; also what `make test-code` runs, together with report when the
labels and the map exist), label [--limit N] (calls the model, resumes where it stopped), consolidate (calls the model; reads the
labels of every run), report. sample prints the thresholds and the counts, never a pair.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np

import acp_client
import gallery
import relation_collapse as rc
import utils

# the strata of the unlabelled population, used by relation_unlabelled_view.py and for the far and near cuts here
STRATA = {"top 1%": (0.99, None), "bottom 1%": (None, 0.01), "middle": (0.495, 0.505)}
FAR, RANDOM_SUBSET, NEAR, RANDOM_ANY = "far in both", "random, no relation", "near in both", "random, any"
OPEN = [FAR, NEAR, RANDOM_SUBSET, RANDOM_ANY]  # the subsets whose relations are not known to the rater
FAR_N, FAR_TOTAL, RANDOM_N, RANDOM_ANY_N, NEAR_N, KNOWN_N = 200, 2000, 2000, 1000, 200, 200
SEED, BLOCK, BATCH, MERGE_CHUNK, RESAMPLES = 0, 1000, 10, 300, 1000
NONE = "none"


def output(stem: str, extension: str) -> Path:
    """Path of a file that this script makes in results/ (built from its parts, so that it is not taken for a committed data file)."""
    return utils.RESULTS / f"{stem}.{extension}"


def run_files(run: str) -> dict[str, Path]:
    """The blinded file, the key and the labels of a run ("" for the main run, "extra" for the second)."""
    s = f"_{run}" if run else ""
    return {"blind": output(f"unlabelled_blinded{s}", "csv"), "key": output(f"unlabelled_key{s}", "json"),
            "labels": output(f"unlabelled_labels{s}", "jsonl")}


RUNS = ["", "extra"]
PREFIX = {"": "p", "extra": "q"}  # the identifiers of the pairs of a run, so that they are unique across runs
BLIND, KEY, LABELS = (run_files("")[k] for k in ("blind", "key", "labels"))
CANONICAL, REPORT = output("unlabelled_canonical", "json"), output("relation_unlabelled_report", "md")
RATER_PROMPT = ("For each pair of English words below, list every relation between the two words that you can think of, each as a short "
                "name. If you know of none, give an empty list.")
RATER_FORMAT = ('Do not use any tool. Answer with one line per pair and nothing else, each line a JSON object: '
                '{"id": "<id>", "relations": ["<name>", ...]}.')
MERGE_PROMPT = ("Below is a list of names of relations that can hold between two words. Some names mean the same relation in other "
                "words. Group the names that mean the same relation and give each group a canonical name of your choice. Do not use any "
                "tool. Answer with one JSON object, and nothing else, that maps every name of the list, exactly as written, to its "
                "canonical name.")
DEFINITIONS = {"inflection": "two forms of one word (dog and dogs, run and ran)",
               "derivation": "one word derived from the other (happy and happiness)",
               "synonym": "words with the same meaning", "antonym": "words with opposite meanings",
               "hypernym": "one is a kind of the other (dog and animal)", "meronym": "one is a part or member of the other (wheel and car)",
               "co-hyponym": "two kinds of the same thing (dog and cat)",
               "encyclopedic": "a fact about the world that links them (a country and its capital, an animal and its young)"}


# --- sampling (exact passes over every pair of two WordNet words)
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


def judged_keys(size: int, pairs: dict, covered: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The words of WordNet (their indices in the vocabulary) and, sorted, the key i * m + j of every judged pair of two of them in the
    numbering of these words (0 to m - 1)."""
    cov = np.flatnonzero(covered)
    local = np.full(size, -1)
    local[cov] = np.arange(len(cov))
    judged = np.concatenate([pairs[n] for n in rc.RELATIONS])
    judged = judged[covered[judged].all(axis=1)]
    return cov, np.unique(local[judged[:, 0]].astype(np.int64) * len(cov) + local[judged[:, 1]])


def sample_far(spaces: list[np.ndarray], highs: list[int], excluded: np.ndarray, n: int, seed: int,
               lows: list[int] | None = None) -> tuple[np.ndarray, int]:
    """`n` keys drawn uniformly among the pairs not in `excluded` (sorted keys) whose bin is in [lows[s], highs[s]) in every space `s`
    (unit rows, same words; lows 0 if not given), and the number of such pairs: every candidate gets a random number, and the `n`
    smallest are kept over all blocks."""
    m, lows = len(spaces[0]), lows or [0] * len(spaces)
    best, count = np.zeros((0, 2)), 0
    for blocks_of_spaces in zip(*(blocks(u) for u in spaces)):
        rows, cols, _, upper = blocks_of_spaces[0]
        mask = upper.copy()
        for (_, _, bins, _), low, high in zip(blocks_of_spaces, lows, highs):
            mask &= (bins >= low) & (bins < high)
        r, c = np.nonzero(mask)
        keys = rows[r].astype(np.int64) * m + cols[c]
        if len(excluded):
            keys = keys[excluded[np.minimum(np.searchsorted(excluded, keys), len(excluded) - 1)] != keys]
        count += len(keys)
        rng = np.random.default_rng([seed, int(rows[0])])
        merged = np.vstack([best, np.column_stack([rng.random(len(keys)), keys])])
        best = merged[np.argsort(merged[:, 0], kind="stable")[:n]]
    return np.sort(best[:, 1].astype(np.int64)), count


def sample_known(pairs: dict, size: int, n: int, seed: int) -> dict[str, np.ndarray]:
    """`n` pairs (vocabulary indices) of each relation, drawn uniformly at any cosine, no pair drawn twice."""
    rng, taken, out = np.random.default_rng(seed), set(), {}
    for name in rc.RELATIONS:
        rows = pairs[name][[k not in taken for k in utils.pair_keys(pairs[name], size)]]
        out[name] = rows[np.sort(rng.choice(len(rows), min(n, len(rows)), replace=False))]
        taken |= set(utils.pair_keys(out[name], size).tolist())
    return out


def relations_of(rows: np.ndarray, pairs: dict, size: int) -> list[list[str]]:
    """Every one of the 8 relations that each pair holds."""
    keys = utils.pair_keys(rows, size)
    member = {name: np.isin(keys, utils.pair_keys(pairs[name], size)) for name in rc.RELATIONS}
    return [[name for name in rc.RELATIONS if member[name][k]] for k in range(len(rows))]


def sample_rows(subsets: dict[str, np.ndarray], spaces: dict, pairs: dict, size: int) -> list[dict]:
    """Every pair of the subsets (vocabulary indices) with its subset, relations, cosines and words (the key)."""
    rows = []
    for subset, chosen in subsets.items():
        cosines = {name: (u[chosen[:, 0]] * u[chosen[:, 1]]).sum(axis=1) for name, u in spaces.items()}
        held = relations_of(chosen, pairs, size)
        for k, (a, b) in enumerate(chosen):
            rows.append({"subset": subset, "relations": held[k], "words": [int(a), int(b)],
                         "cosine": {name: round(float(c[k]), 3) for name, c in cosines.items()}})
    return rows


def space_cuts(spaces: dict, cov: np.ndarray, labelled_keys: np.ndarray) -> tuple[list[tuple[int, int]], dict]:
    """For each space the bins [low, high) of its top 1% and its bottom 1% (among the unjudged pairs of two WordNet words), and what to
    print about them."""
    ranges, info = [], {}
    for name, u in spaces.items():
        hist = unlabelled_histogram(u[cov], labelled_keys)
        strata = stratum_bins(hist)
        ranges.append((strata["top 1%"][0], strata["bottom 1%"][1]))
        info[name] = {"far cut": round(float(ranges[-1][1] / gallery.BINS * 2 - 1), 3),
                      "near cut": round(float(ranges[-1][0] / gallery.BINS * 2 - 1), 3), "unlabelled": int(hist.sum())}
    return ranges, info


def to_vocab(keys: np.ndarray, cov: np.ndarray) -> np.ndarray:
    """The pairs of vocabulary indices of keys in the numbering of the WordNet words."""
    return np.column_stack([cov[keys // len(cov)], cov[keys % len(cov)]])


def draw_main(vocab: list[str], pairs: dict, covered: np.ndarray) -> tuple[list[dict], dict]:
    """The main run: FAR_N far pairs and KNOWN_N pairs of each relation, with what to print (cuts and counts)."""
    size, spaces = len(vocab), {name: utils.unit(utils.load_space(stem).astype(np.float32)) for name, stem in rc.SPACES.items()}
    cov, labelled_keys = judged_keys(size, pairs, covered)
    ranges, info = space_cuts(spaces, cov, labelled_keys)
    keys, info["far in both"] = sample_far([u[cov] for u in spaces.values()], [h for _, h in ranges], labelled_keys, FAR_N, SEED)
    subsets = {FAR: to_vocab(keys, cov), **sample_known(pairs, size, KNOWN_N, SEED)}
    info["subsets"] = {s: len(c) for s, c in subsets.items()}
    return sample_rows(subsets, spaces, pairs, size), info


def draw_extra(vocab: list[str], pairs: dict, covered: np.ndarray) -> tuple[list[dict], dict]:
    """The second run: the far pairs that complete the main run to FAR_TOTAL, NEAR_N near pairs and RANDOM_N random pairs, none of them
    judged, RANDOM_ANY_N pairs drawn at random from all the pairs of two WordNet words, judged or not, none already drawn, and no pair in
    two subsets."""
    size, spaces = len(vocab), {name: utils.unit(utils.load_space(stem).astype(np.float32)) for name, stem in rc.SPACES.items()}
    cov, labelled_keys = judged_keys(size, pairs, covered)
    local = np.full(size, -1)
    local[cov] = np.arange(len(cov))
    index = {w: i for i, w in enumerate(vocab)}
    old = [tuple(sorted(int(local[index[w]]) for w in v["words"])) for v in json.loads(KEY.read_text()).values()]
    old = [i * len(cov) + j for i, j in old if i >= 0 and j >= 0]  # every pair of the main run that is of two WordNet words
    far_drawn = sum(v["subset"] == FAR for v in json.loads(KEY.read_text()).values())
    excluded = np.unique(np.concatenate([labelled_keys, old])).astype(np.int64)
    ranges, info = space_cuts(spaces, cov, labelled_keys)
    unit = [u[cov] for u in spaces.values()]
    far, info["far in both"] = sample_far(unit, [h for _, h in ranges], excluded, FAR_TOTAL - far_drawn, SEED)
    excluded = np.unique(np.concatenate([excluded, far]))
    near, info["near in both"] = sample_far(unit, [gallery.BINS] * 2, excluded, NEAR_N, SEED + 2, lows=[lo for lo, _ in ranges])
    excluded = np.unique(np.concatenate([excluded, near]))
    anywhere, info["random"] = sample_far(unit[:1], [gallery.BINS], excluded, RANDOM_N, SEED + 1)
    # completely random: any pair of two WordNet words, judged or not (the judged ones are 0.26% of them), apart from the pairs drawn
    keep = np.unique(np.concatenate([old, far, near, anywhere])).astype(np.int64)
    natural, info["random any"] = sample_far(unit[:1], [gallery.BINS], keep, RANDOM_ANY_N, SEED + 3)
    subsets = {FAR: to_vocab(far, cov), NEAR: to_vocab(near, cov), RANDOM_SUBSET: to_vocab(anywhere, cov), RANDOM_ANY: to_vocab(natural, cov)}
    info["subsets"] = {s: len(c) for s, c in subsets.items()}
    return sample_rows(subsets, spaces, pairs, size), info


def blind(rows: list[dict], vocab: list[str], run: str = "") -> dict[str, dict]:
    """Shuffle the sample, give each pair an identifier and a random order of its two words, and write the blinded file and the key."""
    files, rng = run_files(run), np.random.default_rng(SEED + 1 + len(run))
    key = {}
    files["blind"].parent.mkdir(exist_ok=True)
    with files["blind"].open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "word_a", "word_b"])
        for k, i in enumerate(rng.permutation(len(rows))):
            row, flip = rows[i], bool(rng.integers(2))
            a, b = row["words"][::-1] if flip else row["words"]
            ident = f"{PREFIX[run]}{k + 1:04d}"
            writer.writerow([ident, vocab[a], vocab[b]])
            key[ident] = {**row, "words": [vocab[a], vocab[b]]}
    files["key"].write_text(json.dumps(key, indent=1))
    return key


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def step_sample(run: str = "") -> None:
    files = run_files(run)
    if files["blind"].exists() and files["key"].exists():
        print(f"{files['blind'].name} exists; delete it and {files['key'].name} to draw the sample again")
        return
    if run and not KEY.exists():
        raise SystemExit("draw the main sample first")
    vocab, index, _ = utils.load_vocab()
    pairs, _, covered = rc.judged_pairs(vocab, index)
    rows, info = (draw_extra if run else draw_main)(vocab, pairs, covered)
    blind(rows, vocab, run)
    for name in rc.SPACES:
        print(f"  {name}: of {info[name]['unlabelled']:,} unlabelled pairs, 1st percentile at cosine {info[name]['far cut']}, "
              f"99th percentile at {info[name]['near cut']}")
    print("  pairs available: " + ", ".join(f"{k} {info[k]:,}" for k in ("far in both", "near in both", "random") if k in info))
    print("  subsets: " + ", ".join(f"{s} {n}" for s, n in info["subsets"].items()))
    print(f"sample of {len(rows)} pairs written to {files['blind'].name} (key in {files['key'].name}, read only by the report)")


# --- labelling
def normalise(name: str) -> str:
    return re.sub(r"\s+", " ", str(name).strip().lower())


def parse_answer(text: str, ids: list[str]) -> dict[str, list[str]]:
    """The relations of each id of the batch found in the answer (one JSON object per line); ids not in the batch, malformed lines and
    malformed entries are dropped."""
    found = {}
    for line in text.splitlines():
        line = line.strip().rstrip(",")
        if not line.startswith("{"):
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(item, dict) or item.get("id") not in ids or not isinstance(item.get("relations"), list):
            continue
        found[item["id"]] = sorted({normalise(r) for r in item["relations"] if isinstance(r, str) and normalise(r)})
    return found


def batch_prompt(batch: list[dict]) -> str:
    return f"{RATER_PROMPT}\n{RATER_FORMAT}\n\n" + "\n".join(f"{r['id']}: {r['word_a']} / {r['word_b']}" for r in batch)


def read_labels(path: Path = LABELS) -> tuple[dict, dict[str, list[str]]]:
    """The header (hash of the blinded file, model) and the labels of the file of labels."""
    if not path.exists():
        return {}, {}
    lines = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return lines[0], {item["id"]: item["relations"] for item in lines[1:]}


def label(rater, blind_path: Path = BLIND, labels_path: Path = LABELS, model: str = acp_client.MODEL, limit: int | None = None) -> int:
    """Label every pair of the blinded file not yet labelled, in batches of BATCH (one session each), appending to the file of labels;
    an id missing from an answer is asked again once, in a batch of its own. Returns the number of batches sent."""
    header = {"blind_sha256": file_hash(blind_path), "model": model}
    old, done = read_labels(labels_path)
    if old and old != header:
        raise SystemExit(f"{labels_path.name} is for another sample or model ({old}); move it away to label this one")
    if not old:
        labels_path.write_text(json.dumps(header) + "\n")
    todo = [r for r in csv.DictReader(blind_path.open()) if r["id"] not in done]
    sent = 0
    with labels_path.open("a") as out:
        for start in range(0, len(todo), BATCH):
            if limit is not None and sent >= limit:
                break
            batch = todo[start: start + BATCH]
            found = parse_answer(rater.ask(batch_prompt(batch)), [r["id"] for r in batch])
            for row in batch:
                if row["id"] not in found:
                    found.update(parse_answer(rater.ask(batch_prompt([row])), [row["id"]]))
            for row in batch:
                if row["id"] in found:
                    out.write(json.dumps({"id": row["id"], "relations": found[row["id"]]}) + "\n")
            out.flush()
            sent += 1
            missing = [r["id"] for r in batch if r["id"] not in found]
            print(f"  batch {sent}: {len(batch) - len(missing)} of {len(batch)} labelled" + (f", missing {missing}" if missing else ""))
    return sent


# --- consolidation
def parse_map(text: str) -> dict[str, str]:
    """The JSON object of an answer (between its first { and its last }), as normalised names and canonical names."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return {}
    try:
        item = json.loads(text[start: end + 1])
    except json.JSONDecodeError:
        return {}
    return {normalise(k): normalise(v) for k, v in item.items() if isinstance(k, str) and isinstance(v, str) and normalise(v)} \
        if isinstance(item, dict) else {}


def merge_prompt(names: list[str], canonical: list[str]) -> str:
    lines = [f"- {n}: {DEFINITIONS[n]}" if n in DEFINITIONS else f"- {n}" for n in names]
    known = ("\nCanonical names already chosen for other names (use one of them when the relation is the same): "
             + "; ".join(canonical) + "\n") if canonical else ""
    return f"{MERGE_PROMPT}\n{known}\n" + "\n".join(lines)


def consolidate(rater, names: list[str], base: dict[str, str] | None = None) -> dict[str, str]:
    """A canonical name for every name and for the 8 relations, asked in chunks of MERGE_CHUNK names (the 8 relations first). The names
    of `base` (an earlier map) keep their canonical name and are not asked again; names missing from an answer are asked again once."""
    mapping = dict(base or {})
    todo = [n for n in list(rc.RELATIONS) + sorted(set(names) - set(rc.RELATIONS)) if n not in mapping]
    for start in range(0, len(todo), MERGE_CHUNK):
        chunk = todo[start: start + MERGE_CHUNK]
        got = parse_map(rater.ask(merge_prompt(chunk, sorted(set(mapping.values())))))
        mapping.update({n: got[n] for n in chunk if n in got})
        missing = [n for n in chunk if n not in mapping]
        if missing:
            got = parse_map(rater.ask(merge_prompt(missing, sorted(set(mapping.values())))))
            mapping.update({n: got[n] for n in missing if n in got})
    missing = [n for n in todo if n not in mapping]
    if missing:
        raise SystemExit(f"no canonical name for {len(missing)} names, e.g. {missing[:5]}; run consolidate again")
    return mapping


def existing_runs() -> list[str]:
    return [run for run in RUNS if run_files(run)["blind"].exists()]


def load_runs() -> tuple[dict, dict[str, list[str]], str, dict[str, str]]:
    """The key and the labels of every run together (identifiers are unique across runs), the model, and the hash of each file of
    labels; every file must be complete, for the same model, and belong to its blinded file."""
    key, labels, models, hashes = {}, {}, set(), {}
    for run in existing_runs():
        files = run_files(run)
        header, got = read_labels(files["labels"])
        if header.get("blind_sha256") != file_hash(files["blind"]):
            raise SystemExit(f"the labels of run {run or 'main'!r} do not belong to its sample")
        run_key = json.loads(files["key"].read_text())
        if set(got) != set(run_key):
            raise SystemExit(f"run {run or 'main'!r}: {len(set(run_key) - set(got))} pairs have no label")
        key.update(run_key)
        labels.update(got)
        models.add(header["model"])
        hashes[run or "main"] = file_hash(files["labels"])
    if len(models) != 1:
        raise SystemExit(f"labels of several models: {sorted(models)}")
    return key, labels, models.pop(), hashes


def step_consolidate(rater) -> None:
    _, labels, model, hashes = load_runs()
    base = {}
    if CANONICAL.exists():
        old = json.loads(CANONICAL.read_text())
        if old["model"] != model:
            raise SystemExit("the map is of another model; move it away")
        base = old["map"]
    mapping = consolidate(rater, sorted({n for rs in labels.values() for n in rs}), base)
    CANONICAL.write_text(json.dumps({"labels_sha256": hashes, "model": model, "map": mapping}, indent=1, sort_keys=True))
    added = sorted(set(mapping) - set(base))
    groups: dict[str, list[str]] = {}
    for name, canon in mapping.items():
        groups.setdefault(canon, []).append(name)
    print(f"{len(mapping)} names in {len(groups)} canonical relations, {len(added)} added to the map in {CANONICAL.name}:")
    for canon, members in sorted(groups.items(), key=lambda g: -len(g[1])):
        print(f"  {canon}: {', '.join(sorted(m for m in members if m in added))}")


# --- report
def rate(hits: np.ndarray, seed: int = SEED) -> list[float]:
    """A share and its 95% bootstrap interval over the pairs (NaN for no pair)."""
    return list(utils.bootstrap_mean(hits.astype(float), RESAMPLES, seed)) if len(hits) else [float("nan")] * 3


def difference(a: np.ndarray, b: np.ndarray, seed: int = SEED) -> list[float]:
    """The difference of the shares of two independent groups of pairs (a minus b), and its 95% bootstrap interval."""
    rng = np.random.default_rng(seed)
    boots = [a[rng.integers(0, len(a), len(a))].mean() - b[rng.integers(0, len(b), len(b))].mean() for _ in range(RESAMPLES)]
    low, high = np.percentile(boots, [2.5, 97.5])
    return [float(a.mean() - b.mean()), float(low), float(high)]


def precision(given: np.ndarray, correct: np.ndarray, seed: int = SEED) -> list[float]:
    """Share of the pairs given a name that hold it, and its 95% bootstrap interval over the pairs."""
    if not given.any():
        return [float("nan")] * 3
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(RESAMPLES):
        pick = rng.integers(0, len(given), len(given))
        if given[pick].any():
            boots.append(correct[pick].sum() / given[pick].sum())
    low, high = np.percentile(boots, [2.5, 97.5])
    return [float(correct.sum() / given.sum()), float(low), float(high)]


def analyse(key: dict, labels: dict[str, list[str]], mapping: dict[str, str]) -> dict:
    """The control (recall, precision, confusion, none), the open subsets (far, random, near: the share with a relation and the canonical
    relations given, each with its pairs) and the differences between their shares, from the key, the labels and the canonical map."""
    canon_of = {r: mapping[r] for r in rc.RELATIONS}
    given = {i: sorted({mapping[n] for n in labels[i]}) for i in key}
    known = [i for i in key if key[i]["subset"] in rc.RELATIONS]
    control = {"recall": {}, "any relation": {}, "none": {}, "precision": {}, "confusion": {}, "shared canonical names": {}}
    for relation in rc.RELATIONS:
        ids = [i for i in known if key[i]["subset"] == relation]
        control["recall"][relation] = rate(np.array([canon_of[relation] in given[i] for i in ids]))
        control["any relation"][relation] = rate(np.array([bool(given[i]) for i in ids]))
        control["none"][relation] = rate(np.array([not given[i] for i in ids]))
        row = {c: sum(c in given[i] for i in ids) for c in dict.fromkeys(canon_of.values())}
        row["other names only"] = sum(bool(given[i]) and not set(given[i]) & set(canon_of.values()) for i in ids)
        row[NONE] = sum(not given[i] for i in ids)
        control["confusion"][relation] = {"pairs": len(ids), **row}
    for canon in dict.fromkeys(canon_of.values()):
        held = {r for r, c in canon_of.items() if c == canon}
        control["precision"][canon] = {"relations": sorted(held),
                                       "value": precision(np.array([canon in given[i] for i in known]),
                                                          np.array([canon in given[i] and bool(held & set(key[i]["relations"])) for i in known]))}
        if len(held) > 1:
            control["shared canonical names"][canon] = sorted(held)
    control["none"]["all known"] = rate(np.array([not given[i] for i in known]))
    opened, related = {}, {}
    for subset in OPEN:
        ids = [i for i in key if key[i]["subset"] == subset]
        if not ids:
            continue
        related[subset] = np.array([bool(given[i]) for i in ids])
        groups: dict[str, list[str]] = {}
        for i in ids:
            for canon in given[i] or [NONE]:
                groups.setdefault(canon, []).append(i)
        listing = []
        for canon, members in sorted(groups.items(), key=lambda g: (-len(g[1]), g[0])):
            hits = np.array([i in set(members) for i in ids])
            listing.append({"relation": canon, "count": len(members), "share": rate(hits),
                            "pairs": [{"id": i, "words": key[i]["words"], "cosine": key[i]["cosine"],
                                       "names": [n for n in labels[i] if mapping[n] == canon]} for i in members]})
        opened[subset] = {"pairs": len(ids), "any relation": rate(related[subset]), "none": rate(~related[subset]),
                          "judged by a dictionary": rate(np.array([bool(key[i]["relations"]) for i in ids])),
                          "relations per pair": rate(np.array([len(given[i]) for i in ids])), "groups": listing}
    differences = {f"{a} minus {b}": difference(related[a], related[b])
                   for a, b in ((FAR, RANDOM_SUBSET), (NEAR, RANDOM_SUBSET), (NEAR, FAR), (RANDOM_SUBSET, RANDOM_ANY), (FAR, RANDOM_ANY)) if a in related and b in related}
    return {"control": control, "open": opened, "differences": differences, "known pairs": len(known)}


def pct(v: list[float]) -> str:
    return "n/a" if np.isnan(v[0]) else f"{100 * v[0]:.1f}% [{100 * v[1]:.1f}, {100 * v[2]:.1f}]"


NONE_SHOWN = 40  # pairs of the group "none" listed in the report (all are in the json)


def markdown(result: dict, model: str) -> str:
    c, out = result["control"], []
    sizes = ", ".join(f"{s['pairs']} {name} pairs" for name, s in result["open"].items())
    out += [f"# Q3, test 1: an open rater on far pairs ({model})", "",
            f"{result['known pairs']} known pairs (control) and {sizes}, mixed blind. Intervals: 95% bootstrap over the pairs.", "",
            "## Control", "", "| relation | canonical name | recall | any relation | none |", "|---|---|---|---|---|"]
    name_of = {r: canon for canon, v in c["precision"].items() for r in v["relations"]}
    out += [f"| {r} | {name_of[r]} | {pct(c['recall'][r])} | {pct(c['any relation'][r])} | {pct(c['none'][r])} |" for r in rc.RELATIONS]
    out += ["", f"None among all known pairs: {pct(c['none']['all known'])}.", "",
            "| canonical name | relations | precision among known pairs |", "|---|---|---|"]
    out += [f"| {canon} | {', '.join(v['relations'])} | {pct(v['value'])} |" for canon, v in c["precision"].items()]
    if c["shared canonical names"]:
        out += ["", "Relations merged into one canonical name (their recall and precision are not separate): "
                + "; ".join(f"{k}: {', '.join(v)}" for k, v in c["shared canonical names"].items()) + "."]
    columns = [k for k in next(iter(c["confusion"].values())) if k != "pairs"]
    out += ["", "Confusion (pairs of each drawn relation given each canonical name; a pair can be given several):", "",
            "| drawn | pairs | " + " | ".join(columns) + " |", "|---|---|" + "---|" * len(columns)]
    out += [f"| {r} | {row['pairs']} | " + " | ".join(str(row[k]) for k in columns) + " |" for r, row in c["confusion"].items()]
    out += ["", "## Open subsets", "", "| subset | pairs | with a relation | none | relations per pair | held in a dictionary |", "|---|---|---|---|---|---|"]
    out += [f"| {name} | {s['pairs']} | {pct(s['any relation'])} | {pct(s['none'])} | {s['relations per pair'][0]:.3f} | "
            f"{pct(s['judged by a dictionary'])} |"
            for name, s in result["open"].items()]
    if result["differences"]:
        out += ["", "Difference of the share with a relation (percentage points, 95% interval): "
                + "; ".join(f"{k} {100 * v[0]:+.1f} [{100 * v[1]:+.1f}, {100 * v[2]:+.1f}]" for k, v in result["differences"].items()) + "."]
    for name, s in result["open"].items():
        out += ["", f"## {name}", "", "| relation | pairs | share |", "|---|---|---|"]
        out += [f"| {g['relation']} | {g['count']} | {pct(g['share'])} |" for g in s["groups"]]
        for g in s["groups"]:
            shown = g["pairs"][:NONE_SHOWN] if g["relation"] == NONE else g["pairs"]
            out += ["", f"### {name}: {g['relation']} ({g['count']})" + (f", first {NONE_SHOWN}" if len(shown) < len(g["pairs"]) else ""), ""]
            out += [f"- {p['words'][0]} / {p['words'][1]} (" + ", ".join(f"{k} {v}" for k, v in p["cosine"].items()) + ")"
                    + (f": {', '.join(p['names'])}" if p["names"] else "") for p in shown]
    return "\n".join(out) + "\n"


def step_report() -> None:
    key, labels, model, hashes = load_runs()
    merged = json.loads(CANONICAL.read_text())
    if merged["labels_sha256"] != hashes or merged["model"] != model:
        raise SystemExit("the labels, the map and the samples do not belong together: run consolidate")
    result = analyse(key, labels, merged["map"])
    result["model"] = model
    utils.save_results("relation_unlabelled", result)
    REPORT.write_text(markdown(result, model))
    c = result["control"]
    print("control (recall, 95% interval):")
    for r in rc.RELATIONS:
        print(f"  {r}: {pct(c['recall'][r])}; any relation {pct(c['any relation'][r])}")
    for name, s in result["open"].items():
        print(f"{name}: {s['pairs']} pairs, with a relation {pct(s['any relation'])}; "
              + ", ".join(f"{g['relation']} {g['count']}" for g in s["groups"][:8]))
    for k, v in result["differences"].items():
        print(f"  {k}: {100 * v[0]:+.1f} points [{100 * v[1]:+.1f}, {100 * v[2]:+.1f}]")
    print(f"report in {REPORT.name}")


def main(argv: list[str]) -> None:
    step = argv[0] if argv else "sample"
    run = "extra" if "extra" in argv else ""
    if step == "sample":
        step_sample(run)
        if not argv and LABELS.exists() and CANONICAL.exists():
            try:
                step_report()
            except SystemExit as stop:  # a run still being labelled, or a map to extend: nothing to report yet
                print(f"report skipped: {stop}")
    elif step == "label":
        limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else None
        files = run_files(run)
        with acp_client.AcpRater() as rater:
            label(rater, files["blind"], files["labels"], limit=limit)
        _, labels = read_labels(files["labels"])
        print(f"{len(labels)} of {len(json.loads(files['key'].read_text()))} pairs labelled")
    elif step == "consolidate":
        with acp_client.AcpRater() as rater:
            step_consolidate(rater)
    elif step == "report":
        step_report()
    else:
        raise SystemExit("usage: python relation_unlabelled.py [sample | label [--limit N] | consolidate | report] [extra]")


if __name__ == "__main__":
    main(sys.argv[1:])
