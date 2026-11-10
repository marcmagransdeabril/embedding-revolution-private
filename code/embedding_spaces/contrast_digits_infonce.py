"""Learning by Contrast, question 3: InfoNCE on images, with no vocabulary and no labels.

The images are the 8x8 digits bundled with scikit-learn. A positive pair is two augmented views of the same image (a shift of
at most one pixel and Gaussian noise), the negatives are the other images of the batch. A small encoder (64 -> 128 -> 16, ReLU)
is trained in numpy with the InfoNCE loss on unit-norm outputs, for several batch sizes N and several seeds. The same encoder is
also trained to predict the pixels of the other view with a squared error, through the same 16-dimensional bottleneck.
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

BATCHES, SEEDS, STEPS = [2, 8, 32, 128], range(5), 2000
PREDICTOR_BATCH = 128  # the predictor has no negatives, so the batch size only sets how many images it sees per step
DIM, HIDDEN, TAU, NOISE, LEARNING_RATE, TAIL = 16, 128, 0.2, 0.15, 1e-3, 200  # TAIL: last steps averaged for the loss
LN2 = float(np.log(2))  # training uses natural logarithms (nats); the results are reported in bits = nats / ln 2
FIGURES = Path("../../figures/embedding_spaces")

images = load_digits().data.reshape(-1, 8, 8) / 16.0
order = np.random.default_rng(0).permutation(len(images))
train, test = images[order[:1200]], images[order[1200:]]


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
    return params, float(np.mean(losses[-TAIL:]))


def unit(x: np.ndarray) -> np.ndarray:
    return x / np.linalg.norm(x, axis=1, keepdims=True)


def retrieval(a: np.ndarray, b: np.ndarray) -> float:
    """Fraction of the rows i for which the row of b most similar (cosine) to a[i] is b[i].

    The vectors are centred first, on the mean of all the held-out views, for every method alike: a shared offset (the predictor's
    vectors put 96% of their norm in it) would otherwise make all the cosines high and handicap the method that has one.
    """
    mean = np.concatenate([a, b]).mean(0)
    return float(np.mean(np.argmax(unit(a - mean) @ unit(b - mean).T, axis=1) == np.arange(len(a))))


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


def run(job):
    kind, batch, seed = job
    params, loss = train_encoder(kind, batch, seed)
    ea, eb = (forward(params, view)[1][2] for view in (VIEW_A, VIEW_B))  # z, before the normalization
    return dict(kind=kind, batch=batch, seed=seed, loss=loss / LN2 if kind == "infonce" else loss,
                retrieval=retrieval(ea, eb), alignment=alignment(ea, eb), uniformity=uniformity(ea),
                views=(ea, eb) if seed == 0 else None)


# Two fixed views of every held-out image: the task is to find, for each view in A, the other view of the same image in B.
VIEW_A, VIEW_B = augment(test, np.random.default_rng(1)), augment(test, np.random.default_rng(2))


def fmt(x, f, spread=True):
    x = np.asarray(x)
    return f"{x.mean():{f}} [{x.min():{f}}, {x.max():{f}}]" if spread else f"{x.mean():{f}}"


if __name__ == "__main__":
    mean_train = train.reshape(len(train), 64).mean(0)
    _, _, vt = np.linalg.svd(train.reshape(len(train), 64) - mean_train, full_matrices=False)
    pca = lambda x: (x - mean_train) @ vt[:DIM].T
    print(f"train images = {len(train)}, held-out images = {len(test)}, chance = {1 / len(test):.2%}")

    jobs = [("infonce", n, s) for n in BATCHES for s in SEEDS] + [("predict", PREDICTOR_BATCH, s) for s in SEEDS]
    with ProcessPoolExecutor() as pool:
        results = list(pool.map(run, jobs))

    baselines = {"raw pixels": (VIEW_A, VIEW_B), f"PCA, {DIM} dimensions": (pca(VIEW_A), pca(VIEW_B))}
    rows = {name: dict(retrieval=[retrieval(a, b)], alignment=[alignment(a, b)], uniformity=[uniformity(a)])
            for name, (a, b) in baselines.items()}
    raw = rows["raw pixels"]["retrieval"][0]
    groups = {"predict the other view": [r for r in results if r["kind"] == "predict"]}
    groups |= {f"InfoNCE, N = {n}": [r for r in results if r["kind"] == "infonce" and r["batch"] == n] for n in BATCHES}
    for name, rs in groups.items():
        rows[name] = {k: [r[k] for r in rs] for k in ("retrieval", "alignment", "uniformity")}

    print(f"\n{'':24} {'loss (bits)':>18} {'bound (bits)':>18} {'retrieval':>20} {'alignment':>10} {'uniformity':>11}"
          f"   (mean [min, max] over {len(SEEDS)} seeds)")
    for name, r in rows.items():
        cells = ["", ""]
        if name.startswith("InfoNCE"):
            n = int(name.split("= ")[1])
            loss = np.array([x["loss"] for x in groups[name]])
            assert loss.min() >= 0 and (np.log2(n) - loss).max() <= np.log2(n)  # the bound can never exceed log2 N
            cells = [fmt(loss, ".2f"), fmt(np.log2(n) - loss, ".2f")]
        print(f"{name:24} {cells[0]:>18} {cells[1]:>18} {fmt(r['retrieval'], '.1%'):>20} "
              f"{np.mean(r['alignment']):>10.2f} {np.mean(r['uniformity']):>11.2f}")
    # With the largest batch, every seed beats the raw pixels (the claim of the section).
    assert min(rows[f"InfoNCE, N = {BATCHES[-1]}"]["retrieval"]) > raw

    # Figure 1: (a) the bound against log2 N, under its cap; (b) the retrieval against the batch size.
    FIGURES.mkdir(parents=True, exist_ok=True)
    logs = np.log2(BATCHES)
    bound = np.array([[np.log2(n) - x["loss"] for x in groups[f"InfoNCE, N = {n}"]] for n in BATCHES])
    found = np.array([rows[f"InfoNCE, N = {n}"]["retrieval"] for n in BATCHES])
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.4, 2.6))
    ax1.plot([0, 7.5], [0, 7.5], "--", color="gray", linewidth=0.8, label=r"cap $\log_2 N$")
    ax1.errorbar(logs, bound.mean(1), [bound.mean(1) - bound.min(1), bound.max(1) - bound.mean(1)], marker="o", markersize=3,
                 linewidth=1, color="C3", label=r"bound $\log_2 N - \mathcal{L}$")
    ax1.set(xlabel=r"$\log_2 N$ (bits)", ylabel="bits", title="(a) the bound under its cap")
    ax1.legend(fontsize=6)
    ax2.errorbar(BATCHES, found.mean(1), [found.mean(1) - found.min(1), found.max(1) - found.mean(1)], marker="o", markersize=3,
                 linewidth=1, color="C3", label="InfoNCE")
    for name, color in (("raw pixels", "C0"), (f"PCA, {DIM} dimensions", "C2")):
        ax2.axhline(rows[name]["retrieval"][0], color=color, linewidth=0.8, linestyle=":", label=name)
    ax2.axhline(np.mean(rows["predict the other view"]["retrieval"]), color="C1", linewidth=0.8, linestyle="--",
                label="predict the other view")
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
