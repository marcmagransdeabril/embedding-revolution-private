# SKELETON: written, not yet run (there are no labels yet: the rater has not seen the blinded sample of relation_unlabelled.py); `make test-code` skips it.
"""Analysis of the labels of the first exploration of Q3 (see relation_unlabelled.py for the design, the blinding and the expectation): joins
the labels of the rater (`data/unlabelled_labels.csv`: a first line `# blinded sha256 <hash of results/unlabelled_blinded.csv>`, then
`id,answer,name`) with the key, and reports per stratum the share of pairs with a relation (95% bootstrap interval over the pairs), the
names given, and the share of the positive control found."""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np

import relation_collapse as rc
import relation_unlabelled as ru
import utils

LABELS = Path(__file__).parent / "data" / f"unlabelled_labels.{'csv'}"  # a literal name once the labels exist
RESAMPLES = 1000


def read_labels(key: dict) -> dict[str, tuple[bool, str]]:
    """The labels of the rater: identifier -> (a relation was found, its name). Refused if they are for another blinded file."""
    first, *rest = LABELS.read_text().splitlines()
    if first != f"# blinded sha256 {ru.blind_hash()}":
        raise ValueError(f"{LABELS} was made for another sample than {ru.BLIND}")
    labels = {r["id"]: (r["answer"].strip().lower() == "relation", r["name"].strip().lower()) for r in csv.DictReader(rest)}
    assert set(labels) == set(key), "every pair of the blinded file needs exactly one label"
    return labels


def analyse(key: dict, labels: dict) -> dict:
    """Share of the pairs with a relation per stratum (bootstrap over the pairs), the names given, the positive control."""
    rng = np.random.default_rng(ru.SEED)
    out = {"strata": {}, "names": {}}
    groups: dict[tuple, list[str]] = {}
    for ident, row in key.items():
        groups.setdefault((row["space"], row["stratum"]), []).append(ident)
    for (space, stratum), idents in groups.items():
        found = np.array([labels[i][0] for i in idents], dtype=float)
        boots = [found[rng.integers(0, len(found), len(found))].mean() for _ in range(RESAMPLES)]
        label = f"{space} | {stratum}" if space else stratum
        out["strata"][label] = {"n": len(idents), "relation": [float(found.mean()), *map(float, np.percentile(boots, [2.5, 97.5]))]}
        out["names"][label] = Counter(labels[i][1] for i in idents if labels[i][0]).most_common()
    out["control_by_relation"] = {r: float(np.mean([labels[i][0] for i, row in key.items() if row["judged"] == r])) for r in rc.WORDNET}
    return out


def print_analysis(result: dict, key: dict, labels: dict) -> None:
    for label, r in result["strata"].items():
        print(f"{label:24s} n = {r['n']:3d}  relation found in {rc.fmt(r['relation'])}")
    print("positive control, by relation: " + ", ".join(f"{k} {v:.0%}" for k, v in result["control_by_relation"].items()))
    for label in result["names"]:
        print(f"\n{label}: names given: " + "; ".join(f"{n} ({c})" for n, c in result["names"][label]))
    print("\nthe pairs, by stratum")
    for label in result["strata"]:
        space, _, stratum = label.rpartition(" | ")
        for ident, row in key.items():
            if row["stratum"] == (stratum or label) and (row["space"] or "") == space:
                print(f"  {label:24s} {row['words'][0]}/{row['words'][1]} cos {row['cosine']}: "
                      + (labels[ident][1] if labels[ident][0] else "none"))


def check_claims(result: dict) -> None:
    """Only the validity of the rater is asserted; what the strata show is read, not asserted."""
    assert np.mean(list(result["control_by_relation"].values())) > 0.9, "the rater does not find the relations of WordNet"


def main() -> None:
    key = json.loads(ru.KEY.read_text())
    labels = read_labels(key)
    result = analyse(key, labels)
    print_analysis(result, key, labels)
    utils.save_results("unlabelled", result)
    check_claims(result)


if __name__ == "__main__":
    main()
