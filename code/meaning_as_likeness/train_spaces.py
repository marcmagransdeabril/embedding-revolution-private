# SKELETON: written, not yet run together with the author (the experiments of phase one are run step by step); `make test-code` skips it.
"""Phase one of the chapter "Likeness as Nearness", step 1: train the spaces that the experiments compare, once, and keep them in `.cache/`.

One text (text8, 17 million words), one vocabulary (the 30,000 most frequent words), one window (5). Counting (SVD of PPMI), predicting
(SGNS) and weighted least squares (GloVe) each give 100-dimensional vectors, three seeds each; and, for the stability experiment,
the three losses are also trained on each half of the text (seed 0) and the counting model on the text with 10 per cent of its
stretches of 1,000 words removed. Training takes about an hour on 12 CPU cores; a space that is already in the cache is not trained again.
Prints, for every space, the Spearman correlation of its cosines with SimLex-999 so that a broken run is seen at once.
"""
from __future__ import annotations

import json
import time

import numpy as np
from scipy import sparse

import spaces
import utils

SIZE, DIM, WINDOW = 30_000, 100, 5
OUT = utils.CACHE / "spaces"
CHUNK, DROP = 1000, 0.10


def save(name: str, emb: np.ndarray) -> None:
    np.save(OUT / f"{name}.npy", emb.astype(np.float32))


def report(name: str, emb: np.ndarray, index: dict, simlex: list) -> None:
    score, keep = utils.pair_scores(emb, index, simlex)
    rho = utils.spearmanr(score, np.array([simlex[i][2] for i in keep])).statistic
    print(f"  {name:18s} SimLex-999 rho = {rho:.3f} on {len(keep)} pairs", flush=True)


def sgns_job(ids: np.ndarray, counts: np.ndarray, seed: int, name: str) -> np.ndarray:
    """SGNS keeps two vectors per word; the context vectors are saved apart, for the test of asymmetry of the two towers."""
    emb, ctx = spaces.sgns(ids, counts, DIM, seed)
    save(f"{name}_ctx", ctx)
    return emb


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    words = utils.load_text8()
    vocab, ids = utils.build_vocab(words, SIZE)
    index = {w: i for i, w in enumerate(vocab)}
    counts = np.bincount(ids[ids >= 0], minlength=SIZE).astype(np.float64)
    utils.cached("vocab", "json").write_text(json.dumps(vocab))
    np.save(utils.cached("counts", "npy"), counts)
    simlex = utils.load_simlex()
    print(f"text8: {len(words):,} words, vocabulary {SIZE:,} covering {counts.sum() / len(words):.1%} of them", flush=True)

    half = len(ids) // 2
    parts = {"full": ids, "A": ids[:half], "B": ids[half:]}
    rng = np.random.default_rng(0)
    chunks = len(ids) // CHUNK
    removed = rng.random(chunks) < DROP
    mask = np.repeat(~removed, CHUNK)
    kept = np.concatenate([ids[: chunks * CHUNK][mask], ids[chunks * CHUNK:]])
    np.save(utils.cached("removed_counts", "npy"), np.bincount(ids[: chunks * CHUNK][~mask][ids[: chunks * CHUNK][~mask] >= 0], minlength=SIZE))
    parts["drop10"] = kept

    cooc = {}
    for name, part in parts.items():
        t = time.time()
        cooc[name] = utils.cooccurrence(part, SIZE, WINDOW)
        print(f"co-occurrence {name}: {cooc[name].nnz:,} non-zero cells in {time.time() - t:.0f}s", flush=True)
    ppmi = {name: utils.ppmi(c) for name, c in cooc.items()}
    sparse.save_npz(utils.cached("ppmi_full", "npz"), ppmi["full"])

    jobs = []
    for seed in range(3):
        jobs += [(f"ppmi_svd_s{seed}", lambda s=seed: spaces.ppmi_svd(ppmi["full"], DIM, s)),
                 (f"glove_s{seed}", lambda s=seed: spaces.glove(cooc["full"], DIM, s)),
                 (f"sgns_s{seed}", lambda s=seed: sgns_job(parts["full"], counts, s, f"sgns_s{s}"))]
    jobs.append(("ppmi_svd_p1_s0", lambda: spaces.ppmi_svd(ppmi["full"], DIM, 0, power=1.0)))
    for part in ("A", "B"):
        jobs += [(f"ppmi_svd_{part}", lambda p=part: spaces.ppmi_svd(ppmi[p], DIM, 0)),
                 (f"glove_{part}", lambda p=part: spaces.glove(cooc[p], DIM, 0)),
                 (f"sgns_{part}", lambda p=part: sgns_job(parts[p], counts, 0, f"sgns_{p}"))]
    jobs.append(("ppmi_svd_drop10", lambda: spaces.ppmi_svd(ppmi["drop10"], DIM, 0)))

    for name, make in jobs:
        path = OUT / f"{name}.npy"
        if path.exists():
            continue
        t = time.time()
        emb = make()
        save(name, emb)
        print(f"{name}: trained in {time.time() - t:.0f}s", flush=True)
        report(name, emb, index, simlex)


if __name__ == "__main__":
    main()
