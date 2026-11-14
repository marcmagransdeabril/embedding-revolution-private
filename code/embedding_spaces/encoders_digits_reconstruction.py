"""Encoders and the Chain Rule, question 2: an encoder that turns an image into 16 numbers, and a decoder that checks them.

The 8x8 digits of contrast_digits_infonce.py (imported, not copied: the same 1,200 training and 597 held-out images, the same 16
dimensions, the same Adam settings). The images are clean here, without augmentation: nothing is paired with anything, the only task is
to rebuild the image from the 16 numbers. The encoder is the one of the text, 64 -> 128 (ReLU) -> 16 (no ReLU), and the decoder is its
mirror, 16 -> 128 (ReLU) -> 64 (no ReLU), trained with the squared error per pixel. The network is written as a list of layers, and the
backward pass is the loop of the box on the chain rule: each layer receives delta from above, returns the gradient of its weights and
passes a new delta down. A finite-difference check of the gradient is run before training.

Models (five seeds each, the held-out error is the squared error per pixel with the 95% bootstrap interval over the seeds and the 597
images, as in contrast_digits_infonce.py):
  one hidden layer     64 -> 128 -> 16 -> 128 -> 64
  two hidden layers    64 -> 128 -> 128 -> 16 -> 128 -> 128 -> 64   (question 3: one more layer on each side)
  linear               64 -> 16 -> 64, the same without any ReLU, trained for ten times more steps (the case of the PCA)
References, not trained: the mean image, and the PCA with 16 components (the best linear code of 16 numbers, Eckart-Young).

Also printed: the number of parameters, the training error, and the error with the ReLU of the 16 coordinates added (question 1).
Saves ../../figures/embedding_spaces/encoders_digits_reconstruction.png: one training image and one held-out image of each digit
(the first of each in the data), and their reconstructions from 16 numbers by the autoencoders with one and two hidden layers and by
the PCA (the first seed).
"""
from concurrent.futures import ProcessPoolExecutor
import os

# The matrices are tiny: one BLAS thread per process is faster than many, and the runs are spread over the cores.
for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[var] = "1"

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import contrast_digits_infonce as base  # data, Adam settings, bootstrap interval

DIM, HIDDEN, STEPS, BATCH, SEEDS, LEARNING_RATE = base.DIM, base.HIDDEN, base.STEPS, base.PREDICTOR_BATCH, base.SEEDS, base.LEARNING_RATE
X_TRAIN, X_TEST = base.train.reshape(len(base.train), 64), base.test.reshape(len(base.test), 64)
# name -> (sizes of the encoder, nonlinearity on the 16 coordinates, steps)
MODELS = {
    "one hidden layer": ([64, HIDDEN, DIM], False, STEPS),
    "two hidden layers": ([64, HIDDEN, HIDDEN, DIM], False, STEPS),
    "linear": ([64, DIM], False, 10 * STEPS),
    "ReLU on the 16 coordinates": ([64, HIDDEN, DIM], True, STEPS),
}


def layers(sizes: list[int], relu_code: bool) -> list[bool]:
    """Which layers of the autoencoder (encoder, then the mirrored decoder) are followed by a ReLU. A linear model (no hidden layer) has none.
    The layer that writes the 16 coordinates and the layer that writes the pixels have none, unless `relu_code`."""
    n = 2 * (len(sizes) - 1)  # number of weight matrices
    if len(sizes) == 2:
        return [False] * n
    relu = [True] * n
    relu[len(sizes) - 2] = relu_code  # the layer that writes the code
    relu[-1] = False  # the layer that writes the pixels
    return relu


def init(sizes: list[int], rng: np.random.Generator) -> list[dict]:
    full = sizes + sizes[::-1][1:]
    return [{"W": rng.standard_normal((a, b)) / np.sqrt(a), "b": np.zeros(b)} for a, b in zip(full[:-1], full[1:])]


def forward(params: list[dict], relu: list[bool], x: np.ndarray):
    """Returns the output, the code (the output of the layer that writes the 16 coordinates) and the inputs of every layer."""
    acts = [x]
    for layer, r in zip(params, relu):
        z = acts[-1] @ layer["W"] + layer["b"]
        acts.append(np.maximum(0, z) if r else z)
    return acts[-1], acts


def loss_and_grads(params: list[dict], relu: list[bool], x: np.ndarray):
    """Squared error per pixel of the reconstruction of x, and its gradient by the chain rule, from the last layer to the first."""
    out, acts = forward(params, relu, x)
    error = out - x
    delta = 2 * error / error.size  # dL / d(output)
    grads = [None] * len(params)
    for i in reversed(range(len(params))):
        grads[i] = {"W": acts[i].T @ delta, "b": delta.sum(0)}  # the signal from above times the input of the layer
        if i > 0:
            delta = delta @ params[i]["W"].T  # the signal passed down...
            if relu[i - 1]:
                delta = delta * (acts[i] > 0)  # ...through the ReLU of the layer below, if it has one
    return float(np.mean(error ** 2)), grads


def gradient_check(seed: int = 0) -> float:
    """Largest relative difference between the backpropagated gradient and central finite differences, on random weights."""
    rng = np.random.default_rng(seed)
    sizes = MODELS["two hidden layers"][0]
    relu = layers(sizes, False)
    params = init(sizes, rng)
    x = X_TRAIN[:8]
    _, grads = loss_and_grads(params, relu, x)
    worst = 0.0
    for _ in range(40):
        i, key = rng.integers(len(params)), rng.choice(["W", "b"])
        idx = tuple(rng.integers(s) for s in params[i][key].shape)
        old, eps = params[i][key][idx], 1e-6
        params[i][key][idx] = old + eps
        up = loss_and_grads(params, relu, x)[0]
        params[i][key][idx] = old - eps
        down = loss_and_grads(params, relu, x)[0]
        params[i][key][idx] = old
        numeric, exact = (up - down) / (2 * eps), grads[i][key][idx]
        worst = max(worst, abs(numeric - exact) / (abs(numeric) + abs(exact) + 1e-12))
    return worst


def train(job):
    name, seed = job
    sizes, relu_code, steps = MODELS[name]
    relu = layers(sizes, relu_code)
    rng = np.random.default_rng(seed)
    params = init(sizes, rng)
    m = [{k: np.zeros_like(v) for k, v in layer.items()} for layer in params]
    s = [{k: np.zeros_like(v) for k, v in layer.items()} for layer in params]
    for t in range(1, steps + 1):
        _, grads = loss_and_grads(params, relu, X_TRAIN[rng.choice(len(X_TRAIN), BATCH, replace=False)])
        for layer, g, m_l, s_l in zip(params, grads, m, s):
            for k in layer:
                m_l[k] = 0.9 * m_l[k] + 0.1 * g[k]
                s_l[k] = 0.999 * s_l[k] + 0.001 * g[k] ** 2
                layer[k] -= LEARNING_RATE * (m_l[k] / (1 - 0.9 ** t)) / (np.sqrt(s_l[k] / (1 - 0.999 ** t)) + 1e-8)
    out_test = forward(params, relu, X_TEST)[0]
    out_train = forward(params, relu, X_TRAIN)[0]
    return dict(name=name, seed=seed, test=np.mean((out_test - X_TEST) ** 2, axis=1), train=float(np.mean((out_train - X_TRAIN) ** 2)),
                out=out_test, out_train=out_train, parameters=sum(v.size for layer in params for v in layer.values()))


if __name__ == "__main__":
    check = gradient_check()
    print(f"gradient check: largest relative difference between backpropagation and finite differences = {check:.1e}")
    assert check < 1e-5, "the backward pass does not match the finite differences"

    with ProcessPoolExecutor() as pool:
        results = list(pool.map(train, [(name, seed) for name in MODELS for seed in SEEDS]))
    by = {name: [r for r in results if r["name"] == name] for name in MODELS}

    mean_image = X_TRAIN.mean(0)
    _, _, vt = np.linalg.svd(X_TRAIN - mean_image, full_matrices=False)
    pca_out = mean_image + (X_TEST - mean_image) @ vt[:DIM].T @ vt[:DIM]
    errors = {"mean image": np.mean((mean_image - X_TEST) ** 2, axis=1)[None], f"PCA, {DIM} components": np.mean((pca_out - X_TEST) ** 2, axis=1)[None]}
    errors |= {name: np.array([r["test"] for r in rs]) for name, rs in by.items()}
    print(f"\n{len(X_TRAIN)} training images, {len(X_TEST)} held-out images; squared error per pixel of the held-out images, "
          f"mean [95% bootstrap interval over the {len(SEEDS)} seeds and the images]")
    print(f"{'':28} {'parameters':>10} {'train error':>12} {'held-out error':>26}")
    for name, e in errors.items():
        params = f"{by[name][0]['parameters']:,}" if name in by else ""
        train_error = f"{np.mean([r['train'] for r in by[name]]):.4f}" if name in by else ""
        print(f"{name:28} {params:>10} {train_error:>12} {base.fmt(e, '.4f'):>26}")
    print("\nheld-out error of each model minus the PCA (paired over the images, 95% bootstrap interval):")
    for name in by:
        mean, low, high = base.interval(errors[name] - errors[f"PCA, {DIM} components"])
        print(f"{name:28} {mean:+.4f} [{low:+.4f}, {high:+.4f}]")
    mean, low, high = base.interval(errors["two hidden layers"] - errors["one hidden layer"])
    print(f"{'two minus one hidden layer':28} {mean:+.4f} [{low:+.4f}, {high:+.4f}]")

    # The claims of the chapter: a nonlinear code of 16 numbers keeps what is needed to rebuild a held-out image, much better than the
    # mean image, and at least as well as the best linear code (the PCA).
    assert errors["one hidden layer"].mean() < 0.5 * errors["mean image"].mean()
    assert base.interval(errors["one hidden layer"] - errors[f"PCA, {DIM} components"])[2] < 0

    # Figure: one held-out image of each digit, and its reconstruction from 16 numbers.
    base.FIGURES.mkdir(parents=True, exist_ok=True)
    # Top block: training images (the autoencoder and the PCA were fitted on them). Bottom block: held-out images (never seen in fitting).
    pca_train = mean_image + (X_TRAIN - mean_image) @ vt[:DIM].T @ vt[:DIM]
    blocks = [
        ("training", X_TRAIN, base.labels_train, "out_train", pca_train),
        ("held-out", X_TEST, base.labels_test, "out", pca_out),
    ]
    # One thin row above each block holds its title; the blocks share the columns (one digit per column).
    fig = plt.figure(figsize=(6.4, 5.0))
    grid = fig.add_gridspec(10, 10, height_ratios=[0.45, 1, 1, 1, 1, 0.45, 1, 1, 1, 1], hspace=0.08, wspace=0.08)
    for b, (kind, images, labels, key, pca_images) in enumerate(blocks):
        top = 5 * b
        title_ax = fig.add_subplot(grid[top, :])
        title_ax.axis("off")
        title_ax.text(0.5, 0.2, f"{kind} images" + (" (red frame): never used to fit anything" if kind == "held-out" else ": used to fit the models"),
                      ha="center", va="center", fontsize=8, weight="bold", color="tab:red" if kind == "held-out" else "black")
        picks = [int(np.argmax(labels == digit)) for digit in range(10)]
        rows = [(f"{kind} image", images), ("one hidden layer", by["one hidden layer"][0][key]),
                ("two hidden layers", by["two hidden layers"][0][key]), (f"PCA, {DIM}", pca_images)]
        for r, (title, imgs) in enumerate(rows):
            for c, i in enumerate(picks):
                ax = fig.add_subplot(grid[top + 1 + r, c])
                ax.imshow(np.clip(imgs[i], 0, 1).reshape(8, 8), cmap="gray_r", vmin=0, vmax=1)
                ax.set_xticks([])
                ax.set_yticks([])
                if kind == "held-out":
                    for spine in ax.spines.values():
                        spine.set_edgecolor("tab:red")
                if c == 0:
                    ax.set_ylabel(title, rotation=0, ha="right", va="center", fontsize=7)
    fig.savefig(base.FIGURES / "encoders_digits_reconstruction.png", dpi=300, bbox_inches="tight")
    print(f"\nsaved {(base.FIGURES / 'encoders_digits_reconstruction.png').resolve()}")
