# SKELETON: written, not yet run together with the author (the experiments of phase one are run step by step); `make test-code` skips it.
"""Method and goal 3 of the chapter "Meaning as Likeness" (section "Reading Nearness Correctly").

Method. A raw cosine mixes likeness with the mean vector of the space, with a few dominant directions and with the frequency of the words.
Expectation: centring on the mean and removing the top directions raise the correlation with the judge and lower the correlation with
frequency, against a shuffled-label null and a random-vector null, with a bootstrap over pairs.
Goal 3. A family is a connected set and not a ball: (a) among the neighbours of a word, pairs that are not neighbours of each other are
common (a chain), and the cosine of two neighbours is about the product of their cosines to the word, as if they shared only its direction;
(b) a fixed radius means a different judged likeness in a dense region than in a sparse one, so the rank of the neighbour is the safer measure.
Prints the numbers and a verdict, saves results/reading_nearness.json and figures/meaning_as_likeness/reading_nearness.png.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import utils

SPACES = {"counting (SVD of PPMI)": "ppmi_svd_s0", "predicting (SGNS)": "sgns_s0", "weighted least squares (GloVe)": "glove_s0"}
TOP = 10_000  # the words of the neighbourhood analyses: the 10,000 most frequent
rng = np.random.default_rng(0)


def correct(emb: np.ndarray, remove: int) -> np.ndarray:
    """Subtract the mean vector and remove the `remove` strongest principal directions ("all but the top")."""
    x = emb - emb.mean(axis=0, keepdims=True)
    if remove:
        _, _, vt = np.linalg.svd(x[:TOP], full_matrices=False)
        x = x - (x @ vt[:remove].T) @ vt[:remove]
    return x


def frequency_leak(emb: np.ndarray, counts: np.ndarray, n: int = 100_000) -> float:
    """Spearman correlation between the cosine of random pairs and the mean log frequency of the two words (zero if the cosine is blind to frequency)."""
    a, b = rng.integers(0, TOP, n), rng.integers(0, TOP, n)
    keep = a != b
    a, b = a[keep], b[keep]
    u = utils.unit(emb)
    return float(utils.spearmanr((u[a] * u[b]).sum(axis=1), (np.log(counts[a]) + np.log(counts[b])) / 2).statistic)


def shuffled_null(score: np.ndarray, judge: np.ndarray, n: int = 500) -> float:
    """The 95th percentile of |rho| when the judge is permuted (what a correlation must exceed to be more than chance)."""
    return float(np.percentile([abs(utils.spearmanr(score, rng.permutation(judge)).statistic) for _ in range(n)], 95))


def method(results: dict) -> None:
    vocab, index, counts = utils.load_vocab()
    simlex = utils.load_simlex()
    ws, _ = utils.load_ws353()
    judges = {"SimLex similarity": (simlex, 2), "SimLex association": (simlex, 3), "WordSim-353": (ws, 2)}
    results["method"] = {}
    print("METHOD: raw against corrected cosine (rho with each judge [95% bootstrap interval over pairs]; rho with frequency)")
    random_space = rng.standard_normal((len(vocab), 100)).astype(np.float32)
    for label, name in list(SPACES.items()) + [("random vectors (null)", None)]:
        emb = random_space if name is None else utils.load_space(name)
        results["method"][label] = {}
        for remove in (None, 0, 1, 3, 10):
            x = emb if remove is None else correct(emb, remove)
            tag = "raw" if remove is None else f"centred, top {remove} removed"
            row = {}
            for j, (pairs, col) in judges.items():
                score, keep = utils.pair_scores(x, index, pairs)
                rho, lo, hi = utils.spearman_interval(score, np.array([pairs[i][col] for i in keep]), resamples=300)
                row[j] = (rho, lo, hi)
            leak = frequency_leak(x, counts)
            results["method"][label][tag] = {"judges": row, "frequency": leak}
            print(f"  {label:32s} {tag:24s} " + " ".join(f"{j.split()[-1][:5]} {r:+.3f} [{lo:+.3f},{hi:+.3f}]" for j, (r, lo, hi) in row.items()) + f"  freq {leak:+.3f}")
        score, keep = utils.pair_scores(emb, index, simlex)
        results["method"][label]["shuffled_label_null_95"] = shuffled_null(score, np.array([simlex[i][2] for i in keep]))
    print("  (shuffled-label null: |rho| above", {k: round(v["shuffled_label_null_95"], 3) for k, v in results["method"].items()}, "is not chance)")


def neighbourhoods(label: str, emb: np.ndarray, results: dict) -> None:
    """Goal 3 (a): chains among the ten nearest neighbours of each of the 10,000 most frequent words."""
    u = utils.unit(emb[:TOP])
    nn = utils.nearest(emb[:TOP], np.arange(TOP), 10)
    sims_random = (u[rng.integers(0, TOP, 200_000)] * u[rng.integers(0, TOP, 200_000)]).sum(axis=1)
    tau = np.percentile(sims_random, 99)
    near_sets = [set(r) for r in nn]
    closed = total = chains = both_near = 0
    excess = []
    for b in range(TOP):
        nb = nn[b]
        cb = u[nb] @ u[b]
        for i in range(len(nb)):
            for j in range(i + 1, len(nb)):
                a, c = nb[i], nb[j]
                total += 1
                closed += (c in near_sets[a]) or (a in near_sets[c])
                cac = float(u[a] @ u[c])
                excess.append(cac - cb[i] * cb[j])
                if cb[i] > tau and cb[j] > tau:
                    both_near += 1
                    chains += cac < tau
    results["chains"][label] = {"closure_rate": closed / total, "mean_excess_cosine": float(np.mean(excess)),
                                "chain_rate": chains / max(both_near, 1), "tau": float(tau), "triples_both_near": both_near}
    print(f"  {label:32s} neighbours of a word that are neighbours of each other: {closed / total:.2f}; "
          f"cos(a,c) minus cos(a,b)cos(b,c): {np.mean(excess):+.3f}; chains (a~b, b~c, a!~c) among {both_near:,} triples with both near: {chains / max(both_near, 1):.2f} (tau {tau:.2f})")


def radius_against_rank(label: str, emb: np.ndarray, index: dict, results: dict) -> dict:
    """Goal 3 (b): inside each density tertile, the correlation with the SimLex similarity of the cosine and of the rank of the neighbour."""
    simlex = utils.load_simlex()
    u = utils.unit(emb)
    pairs = [p for p in simlex if p[0] in index and p[1] in index and index[p[0]] < len(u) and index[p[1]] < len(u)]
    ia = np.array([index[p[0]] for p in pairs])
    ib = np.array([index[p[1]] for p in pairs])
    judge = np.array([p[2] for p in pairs])
    cos = (u[ia] * u[ib]).sum(axis=1)

    def rank_and_density(q, other):
        sims = u[q] @ u.T
        sims[np.arange(len(q)), q] = -np.inf
        rank = (sims > sims[np.arange(len(q)), other][:, None]).sum(axis=1) + 1
        kth = -np.partition(-sims, 10, axis=1)[:, 9]  # cosine to the 10th neighbour: small means a sparse region
        return rank, kth

    r_ab, d_a = rank_and_density(ia, ib)
    r_ba, d_b = rank_and_density(ib, ia)
    rank_score = -(np.log(r_ab) + np.log(r_ba)) / 2
    density = (d_a + d_b) / 2
    edges = np.quantile(density, [1 / 3, 2 / 3])
    tert = np.digitize(density, edges)
    out = {}
    for t, name in enumerate(["sparse", "middle", "dense"]):
        m = tert == t
        out[name] = {"pairs": int(m.sum()), "rho_cosine": float(utils.spearmanr(cos[m], judge[m]).statistic),
                     "rho_rank": float(utils.spearmanr(rank_score[m], judge[m]).statistic),
                     "mean_cosine": float(cos[m].mean()), "mean_judged_inside_band": None}
        band = m & (cos >= np.quantile(cos, 0.7)) & (cos < np.quantile(cos, 0.9))
        out[name]["mean_judged_inside_band"] = float(judge[band].mean()) if band.sum() >= 10 else None
    results["radius_rank"][label] = out
    print(f"  {label:32s} " + "; ".join(f"{n}: rho cos {v['rho_cosine']:+.3f}, rho rank {v['rho_rank']:+.3f}, mean judged in the same cosine band {v['mean_judged_inside_band']:.2f}" for n, v in out.items() if v['mean_judged_inside_band'] is not None))
    return out


def main() -> None:
    results: dict = {"chains": {}, "radius_rank": {}}
    method(results)
    vocab, index, counts = utils.load_vocab()
    print("\nGOAL 3 (a): chains among the ten nearest neighbours")
    for label, name in SPACES.items():
        neighbourhoods(label, utils.load_space(name), results)
    print("\nGOAL 3 (b): a fixed cosine band against the rank, by density of the region (SimLex-999 pairs within the 10,000 most frequent words)")
    fig, ax = plt.subplots(figsize=(6, 3.4))
    for label, name in SPACES.items():
        out = radius_against_rank(label, utils.load_space(name)[:TOP], index, results)
        ax.plot(list(out), [out[k]["rho_cosine"] for k in out], "o--", label=f"{label}, cosine")
        ax.plot(list(out), [out[k]["rho_rank"] for k in out], "s-", label=f"{label}, rank")
    ax.set_xlabel("density of the region (cosine to the 10th neighbour)")
    ax.set_ylabel("rho with SimLex similarity")
    ax.legend(fontsize=5)
    fig.tight_layout()
    utils.FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(utils.FIGURES / "reading_nearness.png", dpi=200)
    utils.save_results("reading_nearness", results)


if __name__ == "__main__":
    main()
