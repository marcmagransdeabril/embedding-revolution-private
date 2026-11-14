"""Learning by Contrast, question 3: InfoNCE on images, with no vocabulary and no labels.

The images are the 8x8 digits bundled with scikit-learn. A positive pair is two augmented views of the same image (a shift of
at most one pixel and Gaussian noise), the negatives are the other images of the batch. A small encoder (64 -> 128 -> 16, ReLU)
is trained in numpy with the InfoNCE loss on unit-norm outputs, for several batch sizes N and several seeds. The same encoder is
also trained to predict the pixels of the other view with a squared error, through the same 16-dimensional bottleneck.
Every number is a mean with a 95% bootstrap interval over the seeds and the held-out queries.
We report, for each embedding and for raw pixels and a PCA of the same dimension, how often the other view of a held-out image is
the nearest of all the held-out views (retrieval, after centring the vectors), the alignment and the uniformity of Wang and Isola, and, for InfoNCE, the loss and
the bound log2 N - loss on the mutual information between the two views. Saves the two figures used in the chapter to
../../figures/embedding_spaces/contrast_digits_bound.png and contrast_digits_cosines.png.
"""
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import os

# The matrices are tiny: one BLAS thread per process is faster than many, and the runs are spread over the cores.
for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[var] = "1"

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.datasets import load_digits
from sklearn.neighbors import KNeighborsClassifier

BATCHES, SEEDS, STEPS = [2, 8, 32, 128], range(5), 2000
BOOTSTRAP = 5000  # resamples of the percentile bootstrap behind every 95% interval
PREDICTOR_BATCH = 128  # the predictor has no negatives, so the batch size only sets how many images it sees per step
DIM, HIDDEN, TAU, NOISE, LEARNING_RATE, TAIL = 16, 128, 0.2, 0.15, 1e-3, 200  # TAIL: last steps averaged for the loss
LN2 = float(np.log(2))  # training uses natural logarithms (nats); the results are reported in bits = nats / ln 2
FIGURES = Path("../../figures/embedding_spaces")

digits = load_digits()
images = digits.data.reshape(-1, 8, 8) / 16.0
order = np.random.default_rng(0).permutation(len(images))
train, test = images[order[:1200]], images[order[1200:]]
labels_train, labels_test = digits.target[order[:1200]], digits.target[order[1200:]]  # only used for the 5-NN reference


def augment(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """One random view of each image: shifted by -1, 0 or 1 pixel in each direction (zero fill), plus Gaussian noise."""
    n = len(x)
    padded = np.pad(x, ((0, 0), (1, 1), (1, 1)))
    rows = np.arange(8)[None, :] + rng.integers(0, 3, n)[:, None]
    cols = np.arange(8)[None, :] + rng.integers(0, 3, n)[:, None]
    shifted = padded[np.arange(n)[:, None, None], rows[:, :, None], cols[:, None, :]]
    return np.clip(shifted + NOISE * rng.standard_normal(shifted.shape), 0, 1).reshape(n, 64)


def forward(params: dict, x: np.ndarray):
    """Encoder: x -> relu(x W1 + b1) -> h W2 + b2 = z. Returns the unit-norm embeddings z / ||z|| and what backward needs."""
    h = np.maximum(0, x @ params["W1"] + params["b1"])
    z = h @ params["W2"] + params["b2"]
    norm = np.linalg.norm(z, axis=1, keepdims=True)
    return z / norm, (x, h, z, norm)


def backward_encoder(params: dict, grads: dict, cache, dz: np.ndarray) -> None:
    """Add to `grads` the gradient of the encoder parameters, given dL/dz."""
    x, h, _, _ = cache
    dh = (dz @ params["W2"].T) * (h > 0)
    grads["W2"] += h.T @ dz
    grads["b2"] += dz.sum(0)
    grads["W1"] += x.T @ dh
    grads["b1"] += dh.sum(0)


def infonce(params: dict, a: np.ndarray, c: np.ndarray):
    """InfoNCE of the views a (anchors) and c (candidates): the i-th candidate is the positive of the i-th anchor.

    Returns the loss in nats and its gradients. With the scores S = <u_a, u_c> / tau, the loss is the softmax cross-entropy
    of picking the diagonal, so dL/dS = (softmax(S) - I) / N, the same 'predicted minus observed' as in Learning by Prediction.
    """
    n = len(a)
    (ua, cache_a), (uc, cache_c) = forward(params, a), forward(params, c)
    scores = ua @ uc.T / TAU
    scores -= scores.max(1, keepdims=True)
    log_q = scores - np.log(np.exp(scores).sum(1, keepdims=True))
    loss = -np.mean(np.diag(log_q))
    dscores = np.exp(log_q)
    dscores[np.arange(n), np.arange(n)] -= 1
    dscores /= n
    grads = {k: np.zeros_like(v) for k, v in params.items()}
    for du, cache, u in ((dscores @ uc / TAU, cache_a, ua), (dscores.T @ ua / TAU, cache_c, uc)):
        norm = cache[3]
        backward_encoder(params, grads, cache, (du - u * (u * du).sum(1, keepdims=True)) / norm)  # through z / ||z||
    return loss, grads


def predictor_loss(params: dict, a: np.ndarray, c: np.ndarray):
    """Squared error per pixel between the pixels of the other view c and a linear read-out of the 16 coordinates z of a."""
    _, cache = forward(params, a)
    z = cache[2]
    error = z @ params["W3"] + params["b3"] - c
    loss = np.mean(error ** 2)
    grads = {k: np.zeros_like(v) for k, v in params.items()}
    dpred = 2 * error / error.size
    grads["W3"], grads["b3"] = z.T @ dpred, dpred.sum(0)
    backward_encoder(params, grads, cache, dpred @ params["W3"].T)
    return loss, grads


def train_encoder(kind: str, batch: int, seed: int):
    """Train with Adam for STEPS steps on batches of `batch` training images. Returns the parameters and the final loss."""
    rng = np.random.default_rng(seed)
    params = {"W1": rng.standard_normal((64, HIDDEN)) / 8, "b1": np.zeros(HIDDEN),
              "W2": rng.standard_normal((HIDDEN, DIM)) / np.sqrt(HIDDEN), "b2": np.zeros(DIM)}
    if kind == "predict":
        params |= {"W3": rng.standard_normal((DIM, 64)) / np.sqrt(DIM), "b3": np.zeros(64)}
    loss_fn = infonce if kind == "infonce" else predictor_loss
    m = {k: np.zeros_like(v) for k, v in params.items()}
    v = {k: np.zeros_like(p) for k, p in params.items()}
    losses = []
    for t in range(1, STEPS + 1):
        x = train[rng.choice(len(train), batch, replace=False)]
        loss, grads = loss_fn(params, augment(x, rng), augment(x, rng))
        losses.append(loss)
        for k in params:
            m[k] = 0.9 * m[k] + 0.1 * grads[k]
            v[k] = 0.999 * v[k] + 0.001 * grads[k] ** 2
            params[k] -= LEARNING_RATE * (m[k] / (1 - 0.9 ** t)) / (np.sqrt(v[k] / (1 - 0.999 ** t)) + 1e-8)
    return params, np.array(losses[-TAIL:])


def unit(x: np.ndarray) -> np.ndarray:
    return x / np.linalg.norm(x, axis=1, keepdims=True)


def retrieval(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """For each row i, whether the row of b most similar (cosine) to a[i] is b[i] (the mean of this vector is the retrieval).

    The vectors are centred first, on the mean of all the held-out views, for every method alike: a shared offset (the predictor's
    vectors put 96% of their norm in it) would otherwise make all the cosines high and handicap the method that has one.
    """
    mean = np.concatenate([a, b]).mean(0)
    return np.argmax(unit(a - mean) @ unit(b - mean).T, axis=1) == np.arange(len(a))


def alignment(a: np.ndarray, b: np.ndarray) -> float:
    """Mean squared distance between the unit-norm embeddings of the two views of the same image (smaller is better)."""
    return float(np.mean(np.sum((unit(a) - unit(b)) ** 2, axis=1)))


def uniformity(a: np.ndarray) -> float:
    """log of the mean of exp(-2 d^2) over the pairs of different images of the unit-norm embeddings (more negative = more spread)."""
    u = unit(a)
    d2 = np.sum((u[:, None, :] - u[None, :, :]) ** 2, axis=-1)
    return float(np.log(np.mean(np.exp(-2 * d2)[~np.eye(len(u), dtype=bool)])))


def cosines(a: np.ndarray, b: np.ndarray):
    """Cosines between the views of the same image (positives) and of different images (negatives)."""
    c = unit(a) @ unit(b).T
    return np.diag(c), c[~np.eye(len(c), dtype=bool)]


def heldout_loss(params: dict, batch: int, seed: int, batches: int = 100) -> float:
    """InfoNCE loss (nats) on batches of held-out images with fresh augmentations, so the bound does not rely on training images."""
    rng = np.random.default_rng(1000 + seed)
    return float(np.mean([infonce(params, augment(x, rng), augment(x, rng))[0]
                          for x in (test[rng.choice(len(test), batch, replace=False)] for _ in range(batches))]))


def run(job):
    kind, batch, seed = job
    params, tail = train_encoder(kind, batch, seed)
    loss = float(tail.mean())
    ea, eb = (forward(params, view)[1][2] for view in (VIEW_A, VIEW_B))  # z, before the normalization
    z = np.concatenate([ea, eb])
    return dict(kind=kind, batch=batch, seed=seed, loss=loss / LN2 if kind == "infonce" else loss,
                heldout=heldout_loss(params, batch, seed) / LN2 if kind == "infonce" else None,
                hits=retrieval(ea, eb), tail=tail / LN2 if kind == "infonce" else tail, alignment=alignment(ea, eb), uniformity=uniformity(ea),
                offset=float(np.linalg.norm(z.mean(0)) / np.linalg.norm(z, axis=1).mean()),  # length of the mean vector / mean length
                views=(ea, eb) if seed == 0 else None)


# Two fixed views of every held-out image: the task is to find, for each view in A, the other view of the same image in B.
VIEW_A, VIEW_B = augment(test, np.random.default_rng(1)), augment(test, np.random.default_rng(2))


def interval(x, rng=np.random.default_rng(12345)):
    """Mean and 95% percentile-bootstrap interval of x, an array of shape (runs, items) or (runs,).

    Two levels of resampling, as the two sources of noise are different: the runs (seeds: initialization and training batches) are drawn
    with replacement, and then the items inside each drawn run (the 597 held-out queries, or the last training steps) too. With one run
    (raw pixels, PCA: nothing is trained) only the items are resampled. With five runs the interval is itself approximate, and a
    bootstrap of five seeds is known to be narrow, so the intervals are a guide to the size of the noise and not an exact coverage.
    """
    x = np.asarray(x, dtype=float)
    x = x[:, None] if x.ndim == 1 else x
    runs, items = x.shape
    pick_run = rng.integers(0, runs, (BOOTSTRAP, runs))
    pick_item = rng.integers(0, items, (BOOTSTRAP, runs, items))
    means = x[pick_run[:, :, None], pick_item].mean(axis=(1, 2))
    return x.mean(), *np.percentile(means, [2.5, 97.5])


def fmt(x, f):
    mean, low, high = interval(x)
    return f"{mean:{f}} [{low:{f}}, {high:{f}}]"


if __name__ == "__main__":
    mean_train = train.reshape(len(train), 64).mean(0)
    _, _, vt = np.linalg.svd(train.reshape(len(train), 64) - mean_train, full_matrices=False)
    pca = lambda x: (x - mean_train) @ vt[:DIM].T
    print(f"train images = {len(train)}, held-out images = {len(test)}, chance = {1 / len(test):.2%}")
    knn = KNeighborsClassifier(5).fit(train.reshape(len(train), 64), labels_train).score(test.reshape(len(test), 64), labels_test)
    print(f"reference: 5-nearest-neighbour digit accuracy on the raw pixels = {knn:.1%} (labels are not used anywhere else)")

    jobs = [("infonce", n, s) for n in BATCHES for s in SEEDS] + [("predict", PREDICTOR_BATCH, s) for s in SEEDS]
    with ProcessPoolExecutor() as pool:
        results = list(pool.map(run, jobs))

    baselines = {"raw pixels": (VIEW_A, VIEW_B), f"PCA, {DIM} dimensions": (pca(VIEW_A), pca(VIEW_B))}
    rows = {name: dict(hits=retrieval(a, b)[None], alignment=[alignment(a, b)], uniformity=[uniformity(a)])
            for name, (a, b) in baselines.items()}
    groups = {"predict the other view": [r for r in results if r["kind"] == "predict"]}
    groups |= {f"InfoNCE, N = {n}": [r for r in results if r["kind"] == "infonce" and r["batch"] == n] for n in BATCHES}
    for name, rs in groups.items():
        rows[name] = {k: np.array([r[k] for r in rs]) for k in ("hits", "alignment", "uniformity", "offset")}
        rows[name]["tail"] = np.array([r["tail"] for r in rs])
    raw = rows["raw pixels"]["hits"].mean()

    def retrieval_of(name):
        return interval(rows[name]["hits"])

    print(f"\n{'':24} {'loss (bits)':>22} {'bound (bits)':>22} {'retrieval':>24} {'alignment':>22} {'uniformity':>22} {'offset':>22}"
          f"   (mean [95% bootstrap interval], {len(SEEDS)} seeds x {len(test)} queries)")
    for name, r in rows.items():
        cells = ["", ""]
        if name.startswith("InfoNCE"):
            n = int(name.split("= ")[1])
            cells = [fmt(r["tail"], ".2f"), fmt(np.log2(n) - r["tail"], ".2f")]
            assert r["tail"].min() >= 0 and (np.log2(n) - r["tail"].mean(1)).max() <= np.log2(n)  # the bound can never exceed log2 N
        print(f"{name:24} {cells[0]:>22} {cells[1]:>22} {fmt(r['hits'], '.1%'):>24} {fmt(r['alignment'], '.2f'):>22} "
              f"{fmt(r['uniformity'], '.2f'):>22} {(fmt(r['offset'], '.2f') if 'offset' in r else ''):>22}")
        if name.startswith("InfoNCE"):
            held = np.array([x["heldout"] for x in groups[name]])
            print(f"{'':24} bound on held-out images: {np.log2(n) - held.mean():.2f} bits "
                  f"(differs from the training bound by {abs(held.mean() - r['tail'].mean()):.2f})")
    # The methods are scored on the same 597 queries, so their difference with the raw pixels is bootstrapped on pairs, which is tighter
    # than comparing two separate intervals.
    print("\nretrieval minus raw pixels (percentage points, paired 95% bootstrap interval):")
    for name, r in rows.items():
        if name != "raw pixels":
            mean, low, high = interval(r["hits"].astype(float) - rows["raw pixels"]["hits"])
            print(f"{name:24} {100 * mean:+.1f} [{100 * low:+.1f}, {100 * high:+.1f}]")
    # With the largest batch, every seed beats the raw pixels (the claim of the section), and the 95% interval of the mean excludes it.
    largest = rows[f"InfoNCE, N = {BATCHES[-1]}"]["hits"]
    assert largest.mean(1).min() > raw and retrieval_of(f"InfoNCE, N = {BATCHES[-1]}")[1] > interval(rows["raw pixels"]["hits"])[2]

    # Figure 1: (a) the bound against log2 N, under its cap; (b) the retrieval against the batch size. Error bars and bands: 95% intervals.
    FIGURES.mkdir(parents=True, exist_ok=True)
    logs = np.log2(BATCHES)
    bound = [interval(np.log2(n) - rows[f"InfoNCE, N = {n}"]["tail"]) for n in BATCHES]
    found = [retrieval_of(f"InfoNCE, N = {n}") for n in BATCHES]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.4, 2.6))
    ax1.plot([0, 7.5], [0, 7.5], "--", color="gray", linewidth=0.8, label=r"cap $\log_2 N$")
    mean, low, high = np.array(bound).T
    ax1.errorbar(logs, mean, [mean - low, high - mean], marker="o", markersize=3, linewidth=1, capsize=2, color="C3",
                 label=r"bound $\log_2 N - \ell_N$")
    ax1.set(xlabel=r"$\log_2 N$ (bits)", ylabel="bits", title="(a) the bound under its cap")
    ax1.legend(fontsize=6)
    mean, low, high = np.array(found).T
    ax2.errorbar(BATCHES, mean, [mean - low, high - mean], marker="o", markersize=3, linewidth=1, capsize=2, color="C3", label="InfoNCE")
    for name, color, style in (("raw pixels", "C0", ":"), (f"PCA, {DIM} dimensions", "C2", ":"), ("predict the other view", "C1", "--")):
        mean, low, high = retrieval_of(name)
        ax2.axhline(mean, color=color, linewidth=0.8, linestyle=style, label=name)
        ax2.axhspan(low, high, color=color, alpha=0.15, linewidth=0)
    ax2.set(xscale="log", xlabel="batch size $N$", ylabel="retrieval of the other view", title="(b) retrieval")
    ax2.set_xticks(BATCHES, [str(n) for n in BATCHES])
    ax2.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax2.legend(fontsize=6)
    for ax in (ax1, ax2):
        ax.tick_params(labelsize=7)
        ax.title.set_fontsize(8)
        ax.xaxis.label.set_size(7)
        ax.yaxis.label.set_size(7)
    fig.tight_layout()
    fig.savefig(FIGURES / "contrast_digits_bound.png", dpi=300, bbox_inches="tight")

    # Figure 2: cosines between the held-out views, of the same image (positives) and of different images (negatives).
    seed0 = {r["kind"] + str(r["batch"]): r["views"] for r in results if r["seed"] == 0}
    panels = [("(a) raw pixels", baselines["raw pixels"]), ("(b) predict the other view", seed0["predict128"]),
              ("(c) InfoNCE, $N=2$", seed0["infonce2"]), ("(d) InfoNCE, $N=128$", seed0["infonce128"])]
    fig, axes = plt.subplots(1, 4, figsize=(6.4, 2.2), sharex=True, sharey=True)
    for ax, (title, (a, b)) in zip(axes, panels):
        positive, negative = cosines(a, b)
        bins = np.linspace(-1, 1, 41)
        ax.hist(negative, bins=bins, density=True, color="gray", alpha=0.7, label="other images")
        ax.hist(positive, bins=bins, density=True, color="C3", alpha=0.7, label="same image")
        ax.set_title(title, fontsize=7)
        ax.tick_params(labelsize=6)
        ax.set_xlabel("cosine", fontsize=7)
    axes[0].set_ylabel("density", fontsize=7)
    axes[0].legend(fontsize=5)
    fig.tight_layout()
    fig.savefig(FIGURES / "contrast_digits_cosines.png", dpi=300, bbox_inches="tight")
    print(f"saved {(FIGURES / 'contrast_digits_bound.png').resolve()} and {(FIGURES / 'contrast_digits_cosines.png').resolve()}")
