# SKELETON: written, not yet run together with the author (the experiments of phase one are run step by step); `make test-code` skips it.
"""The offset test of analogies (a : a* :: b : ?) on the trained spaces; reported in the chapter on difference, run here because the spaces
are the same as those of the chapter on likeness. The standard test (3CosAdd) is a combination of three cosines, cos(x, a*) - cos(x, a) +
cos(x, b), so a failure may come from the nearness and not from the relation. Run with the input words excluded from the answers (the
correct protocol), without the exclusion (the offset then mostly returns an input word), and against two baselines that ignore the offset:
the nearest neighbour of b, and the nearest neighbour of a*. The Google analogy set, restricted to the questions whose four words are in the
30,000-word vocabulary. Prints accuracy by category; saves results/offset.json.
"""
from __future__ import annotations

import numpy as np

import utils

SPACES = {"counting (SVD of PPMI)": "ppmi_svd_s0", "predicting (SGNS)": "sgns_s0", "weighted least squares (GloVe)": "glove_s0"}


def answer(u: np.ndarray, a: np.ndarray, a_star: np.ndarray, b: np.ndarray, how: str, exclude: bool) -> np.ndarray:
    """The predicted index for each question, from unit vectors u and the indices of a, a* and b."""
    if how == "3CosAdd":
        sims = u @ u[a_star].T - u @ u[a].T + u @ u[b].T
    elif how == "nearest to b":
        sims = u @ u[b].T
    else:  # nearest to a*
        sims = u @ u[a_star].T
    if exclude:
        for ids in (a, a_star, b):
            sims[ids, np.arange(len(a))] = -np.inf
    return sims.argmax(axis=0)


def main() -> None:
    vocab, index, counts = utils.load_vocab()
    questions = utils.load_analogies()
    results: dict = {}
    for label, name in SPACES.items():
        u = utils.unit(utils.load_space(name))
        results[label] = {}
        print(f"\n{label}")
        total = {"3CosAdd": 0, "3CosAdd, inputs not excluded": 0, "nearest to b": 0, "nearest to a*": 0}
        n_all = 0
        for cat, qs in questions.items():
            qs = [q for q in qs if all(w in index for w in q)]
            if not qs:
                continue
            ids = np.array([[index[w] for w in q] for q in qs])
            a, a_star, b, b_star = ids.T
            acc = {}
            for key, (how, excl) in {"3CosAdd": ("3CosAdd", True), "3CosAdd, inputs not excluded": ("3CosAdd", False),
                                      "nearest to b": ("nearest to b", True), "nearest to a*": ("nearest to a*", True)}.items():
                pred = np.concatenate([answer(u, a[s: s + 500], a_star[s: s + 500], b[s: s + 500], how, excl) for s in range(0, len(qs), 500)])
                acc[key] = float((pred == b_star).mean())
                total[key] += int((pred == b_star).sum())
            n_all += len(qs)
            results[label][cat] = {"questions": len(qs), **acc}
            print(f"  {cat:28s} n={len(qs):5d}  " + "  ".join(f"{k} {v:.2f}" for k, v in acc.items()))
        results[label]["all"] = {"questions": n_all, **{k: v / n_all for k, v in total.items()}}
        print(f"  {'ALL':28s} n={n_all:5d}  " + "  ".join(f"{k} {v / n_all:.2f}" for k, v in total.items()))
    utils.save_results("offset", results)


if __name__ == "__main__":
    main()
