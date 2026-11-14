"""Learning by Prediction, question 3: softmax predictor on the toy corpus, trained with plain stochastic gradient
descent (numpy only) by sampling sentences with repetition, for several dimensions d and several seeds, with the
analogues of tbl-svd and tbl-patterns."""
from concurrent.futures import ProcessPoolExecutor
import os

# The matrices are tiny: one BLAS thread per process is faster than many, and the runs are spread over the cores.
for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[var] = "1"

import numpy as np

from utils import TOY_CORPUS, cooccurrence, cosine, ppmi, truncated_svd

DIMS, SEEDS, ITERATIONS, LEARNING_RATE = [2, 4, 5, 6, 8, 12], range(5), 1_000_000, 0.1
LN2 = float(np.log(2))  # training uses natural logarithms (nats); the results are reported in bits = nats / ln 2
PAIRS = [("dawn", "dusk"), ("king", "queen"), ("dawn", "king"), ("dawn", "xqzv"), ("breaks", "falls")]
WORDS = ["dawn", "dusk", "breaks", "falls", "over", "king", "queen", "wears", "rules", "xqzv", "jwk"]
SENTENCES = [line.split() for line in TOY_CORPUS]
vocab, counts = cooccurrence(SENTENCES, window=1)
index = {w: i for i, w in enumerate(vocab)}
n = counts.sum()
P_COND = counts / counts.sum(1, keepdims=True)  # true conditional probability P(c | w)
H_COND = -(counts / n * np.log(np.where(counts > 0, P_COND, 1))).sum()  # conditional entropy H(C | W) in nats

# The (word, neighbour) pairs of each sentence, with a window of one word on each side, as counted in C.
SENTENCE_PAIRS = []
for sentence in SENTENCES:
    ids = [index[w] for w in sentence]
    SENTENCE_PAIRS.append((np.array(ids[:-1] + ids[1:]), np.array(ids[1:] + ids[:-1])))


def log_softmax(x: np.ndarray) -> np.ndarray:
    x = x - x.max(axis=-1, keepdims=True)
    return x - np.log(np.exp(x).sum(axis=-1, keepdims=True))


def loss(e: np.ndarray, v: np.ndarray) -> float:
    """Cross-entropy of the softmax predictor, averaged over all the pairs of the corpus (nats per pair)."""
    return float(-(counts * log_softmax(e @ v.T)).sum() / n)


def sgd_step(e: np.ndarray, v: np.ndarray, words: np.ndarray, neighbours: np.ndarray, eta: float) -> None:
    """One step of size eta against the gradient of the summed loss of the pairs (words[i], neighbours[i])."""
    e_w = e[words]
    q = np.exp(log_softmax(e_w @ v.T))  # Q(. | w) for each pair
    q[np.arange(len(neighbours)), neighbours] -= 1  # Q(c' | w) - delta_{c'c}
    np.add.at(e, words, -eta * (q @ v))  # dl/de_w = sum_c' (Q(c' | w) - delta_{c'c}) v_c'
    v -= eta * (q.T @ e_w)  # dl/dv_c' = (Q(c' | w) - delta_{c'c}) e_w, summed over the pairs


def train_curve(seed: int, d: int, checkpoints: tuple = ()) -> tuple[np.ndarray, np.ndarray, list]:
    """Plain SGD: at each iteration draw one sentence at random, with repetition, and take one step of size eta
    against the gradient of the loss of its pairs; eta decreases linearly from LEARNING_RATE to 0.
    Returns e, v and the loss (nats per pair, whole corpus) after each iteration number listed in `checkpoints`."""
    rng = np.random.default_rng(seed)
    e = 0.1 * rng.standard_normal((len(vocab), d))
    v = 0.1 * rng.standard_normal((len(vocab), d))
    curve = []
    for t, s in enumerate(rng.integers(len(SENTENCES), size=ITERATIONS), start=1):
        sgd_step(e, v, *SENTENCE_PAIRS[s], LEARNING_RATE * (1 - (t - 1) / ITERATIONS))
        if t in checkpoints:
            curve.append(loss(e, v))
    return e, v, curve


def train(args: tuple[int, int]) -> tuple[np.ndarray, np.ndarray]:
    """The trained vectors of train_curve for (seed, d)."""
    return train_curve(*args)[:2]


def cos(e: np.ndarray, a: str, b: str) -> float:
    return cosine(e[index[a]], e[index[b]])


def prob(e: np.ndarray, v: np.ndarray, w: str, c: str) -> float:
    """Q(c | w) of the trained predictor."""
    return float(np.exp(log_softmax(e[index[w]] @ v.T)[index[c]]))


def coordinates(e: np.ndarray, w: str) -> str:
    return "".join(f"{x:7.2f}" for x in e[index[w]])


def report_cosines(runs: dict[int, list]) -> dict[int, tuple]:
    """The learned counterpart of tbl-svd: loss, Q(king | dawn) and the cosines of PAIRS, with the SVD in parentheses."""
    print("cosines of the pairs of tbl-svd, mean [min, max] over the seeds; the SVD value in parentheses")
    print(f"{'d':>3s} {'loss (bits)':>11s} {'log2 Q(king|dawn)':>19s} " + " ".join(f"{a + '-' + b:>26s}" for a, b in PAIRS))
    summary = {}
    for d, trained in runs.items():
        losses = [loss(e, v) for e, v in trained]
        unseen = [np.log(prob(e, v, "dawn", "king")) for e, v in trained]
        cosines = np.array([[cos(e, a, b) for a, b in PAIRS] for e, _ in trained])
        svd = [cos(truncated_svd(ppmi(counts), d), a, b) for a, b in PAIRS]
        cells = " ".join(f"{c.mean():6.2f} [{c.min():5.2f},{c.max():5.2f}] ({s:5.2f})" for c, s in zip(cosines.T, svd))
        print(f"{d:3d} {np.mean(losses) / LN2:11.4f} {min(unseen) / LN2:9.1f} to {max(unseen) / LN2:6.1f} {cells}")
        summary[d] = (losses, cosines, unseen)
    return summary


def report_probabilities(trained: list) -> None:
    """The learned coordinates of the words (tbl-patterns) of the first seed, and the observed probabilities."""
    print("\ncoordinates of E (d = 5, seed 0)")
    for w in WORDS:
        print(f"{w:8s}" + coordinates(trained[0][0], w))
    for c in ("breaks", "the"):
        q = [prob(e, v, "dawn", c) for e, v in trained]
        print(f"Q({c} | dawn) at d = 5: min {min(q):.3f}, max {max(q):.3f} (true {P_COND[index['dawn'], index[c]]:.3f})")


def compare_two_runs(run_a: tuple, run_b: tuple) -> dict:
    """The loss fixes E V^T, not E: two runs with d = 5 end with the same loss and different vectors. They differ by
    a change of basis that is close to a rotation (the best one, from an orthogonal Procrustes problem, is R), and a
    rotation keeps every cosine between words."""
    (e_a, v_a), (e_b, v_b) = run_a, run_b
    print(f"\nd = 5, seed 0 against seed 1: loss/pair {loss(e_a, v_a) / LN2:.4f} and {loss(e_b, v_b) / LN2:.4f} bits")
    print(f"{'':>14s} {'seed 0':>7s} {'seed 1':>7s}")
    for a, b in PAIRS:
        print(f"{a + '-' + b:>14s} {cos(e_a, a, b):7.2f} {cos(e_b, a, b):7.2f}")
    same_word = {w: cosine(e_a[index[w]], e_b[index[w]]) for w in ("dawn", "dusk", "king", "queen")}
    print("cosine between the vectors of the same word in the two runs: "
          + ", ".join(f"{w} {c:.2f}" for w, c in same_word.items()))
    print("\ncoordinates of E (d = 5), seed 0 then seed 1")
    for w in same_word:
        print(f"{w:8s}" + coordinates(e_a, w) + "   |" + coordinates(e_b, w))

    left, _, right = np.linalg.svd(e_a.T @ e_b)
    gap = np.linalg.norm(e_a - e_b) / np.linalg.norm(e_b)
    gap_rotated = np.linalg.norm(e_a @ (left @ right) - e_b) / np.linalg.norm(e_b)
    print(f"relative distance between E of the two runs: {gap:.2f}; after the best rotation: {gap_rotated:.2f}")
    return {"loss_gap": abs(loss(e_a, v_a) - loss(e_b, v_b)), "same_word": same_word, "gap": gap, "rotated": gap_rotated}


def check(summary: dict, trained: list, two_runs: dict) -> None:
    # The loss gets close to H(C|W) once the predictor is rich enough, and not before.
    assert min(summary[2][0]) - H_COND > 0.03
    for d in DIMS[1:]:
        assert max(summary[d][0]) - H_COND < 1e-2
        assert max(summary[d][2]) < -5  # the unseen pair dawn-king is pushed far below
    # The observed pairs approach the true probabilities for d = 5; the seed does not change that.
    for e, v in trained:
        for c in ("breaks", "the"):
            assert abs(prob(e, v, "dawn", c) - P_COND[index["dawn"], index[c]]) < 0.05
    # king and queen share every neighbour, so they stay together for every d and seed; the SVD also put dawn and dusk
    # together, but the predictor does not, and the cosine of dawn and king changes from run to run.
    assert all(summary[d][1][:, 1].min() > 0.8 for d in DIMS)
    assert summary[5][1][:, 0].max() < 0.5
    assert summary[5][1][:, 2].max() - summary[5][1][:, 2].min() > 0.1
    # Two runs with d = 5 reach the same loss and different vectors, which are the same up to a rotation.
    assert two_runs["loss_gap"] < 1e-2
    assert max(two_runs["same_word"].values()) < 0.5
    assert two_runs["gap"] > 1 and two_runs["rotated"] < 0.1


if __name__ == "__main__":
    print(f"H(C|W) = {H_COND / LN2:.4f} bits per pair ({H_COND:.4f} nats); {ITERATIONS:,} iterations of SGD, "
          f"eta from {LEARNING_RATE} to 0\n")
    with ProcessPoolExecutor() as pool:
        results = list(pool.map(train, [(seed, d) for d in DIMS for seed in SEEDS]))
    runs = {d: results[i * len(SEEDS):(i + 1) * len(SEEDS)] for i, d in enumerate(DIMS)}  # d -> [(e, v)] per seed

    summary = report_cosines(runs)
    report_probabilities(runs[5])
    check(summary, runs[5], compare_two_runs(runs[5][0], runs[5][1]))
