# SKELETON: written, not yet run together with the author (the experiments of phase one are run step by step); `make test-code` skips it.
"""Goal 4 of the chapter "Meaning as Likeness" (section "Is Likeness a Distance? Tversky's Three Axioms"): four smoke tests of which axioms of
a distance each score of a trained space keeps, run on the trained spaces and on random vectors of the same dimension.

Expectation (written before the run): Euclidean distance and angle keep all three axioms; the dot product loses constant self-similarity
(minimality); two towers (the word and the context vectors of SGNS) are asymmetric; and mutual neighbours fall below one even for symmetric
scores. What is NOT run: the three axioms against human judgements of likeness (Tversky's own data are not held), so this section says what
a trained score does and not what people do. Prints the numbers, saves results/axioms.json and figures/meaning_as_likeness/axioms.png.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import skew

import utils

TOP = 10_000
rng = np.random.default_rng(0)


def minimality(emb: np.ndarray, counts: np.ndarray) -> dict:
    """The dot product as a similarity: is a word always its own nearest, and is its self-similarity constant?"""
    x = emb[:TOP]
    own = (x * x).sum(axis=1)
    higher = 0
    for s in range(0, TOP, 1000):
        sims = x[s: s + 1000] @ x.T
        sims[np.arange(len(sims)), np.arange(s, s + len(sims))] = -np.inf
        higher += int((sims.max(axis=1) > own[s: s + 1000]).sum())
    return {"self_dot_cv": float(own.std() / own.mean()), "self_dot_vs_log_frequency": float(utils.spearmanr(own, np.log(counts[:TOP])).statistic),
            "words_with_a_higher_dot_elsewhere": higher / TOP}


def symmetry(emb: np.ndarray, ctx: np.ndarray, n: int = 200_000) -> dict:
    """Two towers: the score of the pair (a, b) is e_a . v_b, and the score of (b, a) is e_b . v_a."""
    a, b = rng.integers(0, TOP, n), rng.integers(0, TOP, n)
    s_ab = (emb[a] * ctx[b]).sum(axis=1)
    s_ba = (emb[b] * ctx[a]).sum(axis=1)
    return {"rho_ab_ba": float(utils.spearmanr(s_ab, s_ba).statistic),
            "mean_relative_asymmetry": float(np.mean(np.abs(s_ab - s_ba) / (np.abs(s_ab) + np.abs(s_ba) + 1e-12)))}


def triangle(emb: np.ndarray, n: int = 1_000_000) -> dict:
    """Violations of d(a,c) <= d(a,b) + d(b,c) on random triples, for three readings of 'distance' from one space."""
    x = emb[:TOP]
    u = utils.unit(x)
    a, b, c = rng.integers(0, TOP, (3, n))
    cos = lambda p, q: (u[p] * u[q]).sum(axis=1)
    out = {}
    d = {"Euclidean": lambda p, q: np.linalg.norm(x[p] - x[q], axis=1),
         "angle (arccos)": lambda p, q: np.arccos(np.clip(cos(p, q), -1, 1)),
         "1 - cosine": lambda p, q: 1 - cos(p, q)}
    for name, f in d.items():
        out[name] = float(np.mean(f(a, c) > f(a, b) + f(b, c) + 1e-9))
    return out


def triangle_on_chains(emb: np.ndarray) -> float:
    """The same test for 1 - cosine on the triples that matter: a and c both among the ten nearest neighbours of b."""
    x = emb[:TOP]
    u = utils.unit(x)
    nn = utils.nearest(x, np.arange(TOP), 10)
    bad = tot = 0
    for b in range(TOP):
        n = nn[b]
        cb = u[n] @ u[b]
        cc = u[n] @ u[n].T
        for i in range(10):
            for j in range(i + 1, 10):
                tot += 1
                bad += (1 - cc[i, j]) > (1 - cb[i]) + (1 - cb[j]) + 1e-9
    return bad / tot


def mutual(emb: np.ndarray, k: int = 10) -> dict:
    nn = utils.nearest(emb[:TOP], np.arange(TOP), k)
    sets = [set(r) for r in nn]
    mutual_share = float(np.mean([w in sets[n] for w in range(TOP) for n in nn[w]]))
    occ = np.bincount(nn.ravel(), minlength=TOP)  # how many times a word is a neighbour of another (k-occurrence)
    return {"mutual_share": mutual_share, "k_occurrence_skewness": float(skew(occ)), "k_occurrence_max": int(occ.max()), "never_a_neighbour": float(np.mean(occ == 0))}


def main() -> None:
    vocab, index, counts = utils.load_vocab()
    results: dict = {}
    spaces = {"SVD of PPMI": utils.load_space("ppmi_svd_s0"), "SGNS": utils.load_space("sgns_s0"), "GloVe": utils.load_space("glove_s0"),
              "random (Gaussian)": rng.standard_normal((len(vocab), 100)).astype(np.float32)}
    ctx = {"SGNS two towers": (utils.load_space("sgns_s0"), utils.load_space("sgns_s0_ctx")),
           "random two towers": (rng.standard_normal((TOP, 100)), rng.standard_normal((TOP, 100)))}
    print("T1 minimality (the dot product as a similarity; the cosine and the distances give 1 and 0 by construction)")
    for name, emb in spaces.items():
        results.setdefault(name, {})["minimality"] = r = minimality(emb, counts)
        print(f"  {name:20s} self dot varies by {r['self_dot_cv']:.2f} (std/mean), correlates with log frequency {r['self_dot_vs_log_frequency']:+.2f}; "
              f"{r['words_with_a_higher_dot_elsewhere']:.1%} of the words have another word with a higher dot product than their own")
    print("T2 symmetry (cosine, dot product and distances are symmetric; two towers are not)")
    for name, (e, c) in ctx.items():
        results.setdefault(name, {})["symmetry"] = r = symmetry(e, c)
        print(f"  {name:20s} rho between s(a,b) and s(b,a) {r['rho_ab_ba']:+.2f}; mean relative asymmetry {r['mean_relative_asymmetry']:.2f}")
    print("T3 triangle inequality: share of random triples that violate it")
    for name, emb in spaces.items():
        results[name]["triangle"] = r = triangle(emb)
        results[name]["triangle_on_chains_1_minus_cosine"] = c = triangle_on_chains(emb)
        print(f"  {name:20s} " + ", ".join(f"{k} {v:.4f}" for k, v in r.items()) + f"; 1 - cosine on neighbour triples {c:.4f}")
    print("T4 mutual neighbours (k = 10; the score is symmetric, the neighbour relation is not)")
    for name, emb in spaces.items():
        results[name]["mutual"] = r = mutual(emb)
        print(f"  {name:20s} {r['mutual_share']:.1%} of the neighbour relations are mutual; k-occurrence skewness {r['k_occurrence_skewness']:.1f}, "
              f"max {r['k_occurrence_max']}, {r['never_a_neighbour']:.1%} of the words are nobody's neighbour")
    utils.save_results("axioms", results)

    utils.FIGURES.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(1, 3, figsize=(9, 3))
    names = list(spaces)
    ax[0].bar(names, [results[n]["minimality"]["words_with_a_higher_dot_elsewhere"] for n in names])
    ax[0].set_title("minimality: dot product,\nwords with a higher dot elsewhere", fontsize=8)
    ax[1].bar(names, [results[n]["mutual"]["mutual_share"] for n in names])
    ax[1].set_title("mutual share of the 10 neighbours", fontsize=8)
    ax[2].bar(names, [results[n]["triangle"]["1 - cosine"] for n in names])
    ax[2].set_title("triples violating the triangle\ninequality for 1 - cosine", fontsize=8)
    for a in ax:
        a.tick_params(axis="x", labelrotation=60, labelsize=6)
    fig.tight_layout()
    fig.savefig(utils.FIGURES / "axioms.png", dpi=200)


if __name__ == "__main__":
    main()
