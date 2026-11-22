"""Learning by Prediction, question 4: the PMI matrix seen by counting (PPMI), by the SVD (rank 5) and by the softmax
predictor (d = 5), as 16 x 16 heatmaps with the words grouped by theme. Saves the figure used in the chapter to
../../figures/embedding_spaces/prediction_toy_pmi.png."""
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm

from prediction_toy_softmax import SEEDS, counts, index, log_softmax, n, train, vocab
from utils import ppmi

D = 5
FIGURE = Path("../../figures/embedding_spaces/prediction_toy_pmi.png")
ORDER = ["dawn", "dusk", "breaks", "falls", "over", "hills", "sea",  # the sky
         "king", "queen", "wears", "rules", "crown", "land",  # the court
         "the", "xqzv", "jwk"]
GROUP_ENDS = [7, 13, 14]  # the figure separates the sky, the court, `the` and the nonsense pair
assert sorted(ORDER) == sorted(vocab)
perm = [index[w] for w in ORDER]

seen = counts > 0
p_c = counts.sum(0) / n
M = ppmi(counts)  # (a) PPMI in bits
u, s, vt = np.linalg.svd(M)
M_svd = (u[:, :D] * s[:D]) @ vt[:D]  # (b) best rank-D approximation of M


def learned_pmi(e: np.ndarray, v: np.ndarray) -> np.ndarray:
    """log2 Q(c | w) / P(c), the predictor's counterpart of the PMI (unclipped, in bits)."""
    return (log_softmax(e @ v.T) - np.log(p_c)) / np.log(2)


if __name__ == "__main__":
    with ProcessPoolExecutor() as pool:
        runs = list(pool.map(train, [(seed, D) for seed in SEEDS]))
    learned = [learned_pmi(e, v) for e, v in runs]  # unclipped
    clipped = [np.maximum(x, 0) for x in learned]  # (c) clipped at 0, like the PPMI

    # Clipping changes the unseen cells (PMI = -infinity) and the observed pairs with a negative PMI.
    with np.errstate(divide="ignore", invalid="ignore"):
        pmi = np.log2(counts / n / np.outer(counts.sum(1) / n, p_c))
    print(f"observed pairs with negative PMI (clipped to 0 in the PPMI): {int((seen & (pmi < 0)).sum())}")

    frobenius = lambda a: float(np.linalg.norm(a - M))
    err_svd = frobenius(M_svd)
    err_learned = [frobenius(c) for c in clipped]
    worst = [float(np.abs((x - pmi)[seen]).max()) for x in learned]  # unclipped, against the PMI itself
    print(f"Frobenius error to the PPMI matrix, all {M.size} cells: SVD rank {D} {err_svd:.2f} "
          f"(observed pairs only {np.linalg.norm((M_svd - M)[seen]):.2f}), "
          f"predictor {np.mean(err_learned):.2f} [{min(err_learned):.2f}, {max(err_learned):.2f}] over {len(runs)} seeds")
    print(f"largest difference between the predictor and the PMI on an observed pair: {max(worst):.2f} bits (seed values "
          f"{', '.join(f'{w:.2f}' for w in worst)})")
    print(f"unseen pairs: SVD from {M_svd[~seen].min():.2f} to {M_svd[~seen].max():.2f} bits; predictor (unclipped, "
          f"seed 0) from {learned[0][~seen].min():.1f} to {learned[0][~seen].max():.1f} bits, all seeds from "
          f"{min(x[~seen].min() for x in learned):.1f} to {max(x[~seen].max() for x in learned):.1f}")
    a = M_svd
    print(f"SVD fills in pairs that never occur: dusk-breaks {a[index['dusk'], index['breaks']]:.2f}, "
          f"dawn-falls {a[index['dawn'], index['falls']]:.2f} (PPMI 0)")

    # The predictor reproduces the PPMI of the observed pairs in every run; the SVD does not.
    assert max(worst) < 0.2
    assert max(err_learned) < 0.5 and err_svd > 5

    # The figure: (a) PPMI, (b) SVD, (c) predictor, same colour scale, words grouped by theme.
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    norm = TwoSlopeNorm(vmin=-1, vcenter=0, vmax=4)
    fig, axes = plt.subplots(1, 3, figsize=(6.4, 2.9), sharey=True)
    panels = [("(a) PPMI", M), (f"(b) SVD, rank {D}", M_svd), (f"(c) predictor, $d={D}$", clipped[0])]
    for ax, (title, matrix) in zip(axes, panels):
        image = ax.imshow(matrix[np.ix_(perm, perm)], cmap="RdBu_r", norm=norm, interpolation="nearest")
        ax.set_title(title, fontsize=8)
        ax.set_xticks(range(len(ORDER)), ORDER, rotation=90, fontsize=5)
        ax.set_yticks(range(len(ORDER)), ORDER, fontsize=5)
        ax.tick_params(length=0)
        for end in GROUP_ENDS:
            ax.axhline(end - 0.5, color="black", linewidth=0.4)
            ax.axvline(end - 0.5, color="black", linewidth=0.4)
    colorbar = fig.colorbar(image, ax=axes, shrink=0.8, pad=0.02)
    colorbar.set_label("bits", fontsize=7)
    colorbar.ax.tick_params(labelsize=6)
    fig.savefig(FIGURE, dpi=300, bbox_inches="tight")
    print(f"saved {FIGURE.resolve()}")
