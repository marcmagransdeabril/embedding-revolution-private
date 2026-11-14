"""Encoder/Decoder and the Chain Rule, questions 1 to 3: an encoder that turns an image into a few numbers, and a decoder that checks them.

The 8x8 digits of contrast_digits_infonce.py (imported, not copied: the same 1,200 training and 597 held-out images, the same Adam settings).
The images are clean here, without augmentation: nothing is paired with anything, the only task is to rebuild the image from the code.
The encoder is the one of the text, 64 -> 128 (ReLU) -> 16 (no ReLU), and the decoder is its mirror, 16 -> 128 (ReLU) -> 64 (no ReLU),
trained with the squared error per pixel. The notation is the one of the chapter: column vectors, layers p_l = W_l a_(l-1) + b_l and
a_l = phi_l(p_l) with W_l of shape (outputs, inputs) (a batch, one image per row, is a @ W.T), the encoder f and the decoder g. The network is written as a list of layers, and the backward pass is the loop of the section:
each layer receives delta from above, returns the gradient of its weights and passes a new delta down. It is written by hand in numpy
(no automatic differentiation in the training), and checked before training against central finite differences and against the
automatic differentiation of PyTorch, which is used for nothing else.

Models (five seeds each, the held-out error is the squared error per pixel with the 95% bootstrap interval over the seeds and the 597
images, as in contrast_digits_infonce.py):
  autoencoder          64 -> 128 -> d -> 128 -> 64, for the size of the code d = 2, 4, 8, 16, 32 and 64 (d = 16 is the one of the text)
  linear               64 -> 16 -> 64, the same without any ReLU, trained for ten times more steps (the case of the PCA; question 2)
  ReLU on the code     the autoencoder with d = 16 and a ReLU on the 16 coordinates (question 1)
References, not trained: the PCA with the same number of components d (the best linear code, Eckart-Young), and the mean image, which is
the PCA with no component (d = 0) and uses no code.

Also printed: the number of parameters, the training error, and the rows of the table of the chapter. Saves
../../figures/embedding_spaces/encoders_digits_reconstruction.png: one held-out image of each digit (the first of each in the data), and its
reconstructions by the autoencoder and by the PCA with d = 2, 4, 8 and 16 numbers (the first seed).
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
SWEEP_DIMS = [2, 4, 8, 16, 32, 64]  # the size of the code
# name -> (sizes of the encoder, nonlinearity on the code, steps)
MODELS = {
    "autoencoder": ([64, HIDDEN, DIM], False, STEPS),
    "linear": ([64, DIM], False, 10 * STEPS),
    "ReLU on the 16 coordinates": ([64, HIDDEN, DIM], True, STEPS),
}
SWEEP = {f"d = {d}": ([64, HIDDEN, d], False, STEPS) for d in SWEEP_DIMS if d != DIM}
ALL = MODELS | SWEEP


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
    # W has shape (outputs, inputs); the draws are those of the (inputs, outputs) layout, transposed, so every seed starts from the same numbers.
    return [{"W": (rng.standard_normal((a, b)) / np.sqrt(a)).T, "b": np.zeros(b)} for a, b in zip(full[:-1], full[1:])]


def forward(params: list[dict], relu: list[bool], x: np.ndarray):
    """Returns the output, the code (the output of the layer that writes the 16 coordinates) and the inputs of every layer."""
    acts = [x]
    for layer, r in zip(params, relu):
        p = acts[-1] @ layer["W"].T + layer["b"]  # the pre-activation p_l of every image (one per row)
        acts.append(np.maximum(0, p) if r else p)
    return acts[-1], acts


def loss_and_grads(params: list[dict], relu: list[bool], x: np.ndarray):
    """Squared error per pixel of the reconstruction of x, and its gradient by the chain rule, from the last layer to the first."""
    out, acts = forward(params, relu, x)
    error = out - x
    delta = 2 * error / error.size  # dL / d(output)
    grads = [None] * len(params)
    for i in reversed(range(len(params))):
        grads[i] = {"W": delta.T @ acts[i], "b": delta.sum(0)}  # dL/dW_l = delta_l a_(l-1)^T: the signal from above times the input of the layer
        if i > 0:
            delta = delta @ params[i]["W"]  # the signal passed down, W_l^T delta_l...
            if relu[i - 1]:
                delta = delta * (acts[i] > 0)  # ...through the ReLU of the layer below, if it has one
    return float(np.mean(error ** 2)), grads


def gradient_check(seed: int = 0) -> float:
    """Largest relative difference between the backpropagated gradient and central finite differences, on random weights."""
    rng = np.random.default_rng(seed)
    sizes = MODELS["autoencoder"][0]
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


def autograd_check(seed: int = 0) -> float:
    """Largest relative difference between the backpropagated gradient and the one of PyTorch's automatic differentiation on the
    same weights and images (float64). Also checks that PyTorch gives the ReLU the derivative 0 at 0, as the mask 1[p > 0] does."""
    import torch

    rng = np.random.default_rng(seed)
    sizes = MODELS["autoencoder"][0]
    relu = layers(sizes, False)
    params = init(sizes, rng)
    x = X_TRAIN[:8]
    _, grads = loss_and_grads(params, relu, x)
    tensors = [{k: torch.tensor(v, dtype=torch.float64, requires_grad=True) for k, v in layer.items()} for layer in params]
    a = torch.tensor(x, dtype=torch.float64)
    for layer, r in zip(tensors, relu):
        a = a @ layer["W"].T + layer["b"]
        a = torch.relu(a) if r else a
    ((a - torch.tensor(x, dtype=torch.float64)) ** 2).mean().backward()
    zero = torch.zeros(1, requires_grad=True)
    torch.relu(zero).backward()
    assert zero.grad.item() == 0.0
    return max(float(np.abs(layer[k].grad.numpy() - g[k]).max() / (np.abs(g[k]).max() + 1e-300))
               for layer, g in zip(tensors, grads) for k in ("W", "b"))


def train(job):
    name, seed = job
    sizes, relu_code, steps = ALL[name]
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
                out=out_test, out_train=out_train, params=params, parameters=sum(v.size for layer in params for v in layer.values()))


if __name__ == "__main__":
    check = gradient_check()
    print(f"gradient check: largest relative difference between backpropagation and finite differences = {check:.1e}")
    assert check < 1e-5, "the backward pass does not match the finite differences"
    auto = autograd_check()
    print(f"autograd check: largest relative difference between backpropagation and PyTorch's automatic differentiation = {auto:.1e}")
    assert auto < 1e-9, "the backward pass does not match automatic differentiation"

    with ProcessPoolExecutor() as pool:
        results = list(pool.map(train, [(name, seed) for name in ALL for seed in SEEDS]))
    by = {name: [r for r in results if r["name"] == name] for name in ALL}

    mean_image = X_TRAIN.mean(0)
    _, _, vt = np.linalg.svd(X_TRAIN - mean_image, full_matrices=False)

    def pca(d: int) -> np.ndarray:
        """Reconstruction of the held-out images from their first d principal components (d = 0 is the mean image)."""
        return mean_image + (X_TEST - mean_image) @ vt[:d].T @ vt[:d]

    def per_image(out: np.ndarray) -> np.ndarray:
        return np.mean((out - X_TEST) ** 2, axis=1)

    def runs(d: int) -> list[dict]:
        return by["autoencoder" if d == DIM else f"d = {d}"]

    pca_error = {d: per_image(pca(d))[None] for d in [0] + SWEEP_DIMS}  # one row: nothing is trained
    ae_error = {d: np.array([r["test"] for r in runs(d)]) for d in SWEEP_DIMS}  # one row per seed
    ae_train = {d: float(np.mean([r["train"] for r in runs(d)])) for d in SWEEP_DIMS}
    print(f"{len(X_TRAIN)} training images, {len(X_TEST)} held-out images; squared error per pixel of the held-out images, "
          f"mean [95% bootstrap interval over the {len(SEEDS)} seeds and the images]")

    # The table of the chapter: the error against the size d of the code, the PCA with the same number of components as reference.
    print("\n| $d$ | PCA | autoencoder | autoencoder minus PCA | autoencoder, training error | parameters |")
    print(f"| 0 (mean image) | {base.fmt(pca_error[0], '.4f')} | | | | |")
    for d in SWEEP_DIMS:
        mean, low, high = base.interval(ae_error[d] - pca_error[d])
        print(f"| {d} | {base.fmt(pca_error[d], '.4f')} | {base.fmt(ae_error[d], '.4f')} | {mean:+.4f} [{low:+.4f}, {high:+.4f}] "
              f"| {ae_train[d]:.4f} | {runs(d)[0]['parameters']:,} |")

    # The other models of the questions, all with d = 16.
    other = {name: np.array([r["test"] for r in by[name]]) for name in MODELS if name != "autoencoder"}
    print(f"\n{'':28} {'parameters':>10} {'train error':>12} {'held-out error':>26}   minus the PCA, d = {DIM}")
    for name, e in ({"autoencoder": ae_error[DIM]} | other | {f"PCA, {DIM} components": pca_error[DIM]}).items():
        params = f"{by[name][0]['parameters']:,}" if name in by else ""
        train_error = f"{np.mean([r['train'] for r in by[name]]):.4f}" if name in by else ""
        diff = ""
        if name in by:
            mean, low, high = base.interval(e - pca_error[DIM])
            diff = f"{mean:+.4f} [{low:+.4f}, {high:+.4f}]"
        print(f"{name:28} {params:>10} {train_error:>12} {base.fmt(e, '.4f'):>26}   {diff}")

    # The claims of the chapter: the error of the PCA falls with d to 0 at d = 64, a nonlinear code of 16 numbers rebuilds a held-out image
    # much better than the mean image, and better than the best linear code (the PCA).
    assert pca_error[64].mean() < 1e-12
    assert all(pca_error[a].mean() > pca_error[b].mean() for a, b in zip([0] + SWEEP_DIMS, SWEEP_DIMS))
    assert ae_error[DIM].mean() < 0.5 * pca_error[0].mean()
    assert base.interval(ae_error[DIM] - pca_error[DIM])[2] < 0

    # Figure: one held-out image of each digit (the first of each in the data), and its reconstruction from d numbers by the autoencoder
    # (the first seed) and by the PCA, for d = 2, 4, 8 and 16.
    base.FIGURES.mkdir(parents=True, exist_ok=True)
    picks = [int(np.argmax(base.labels_test == digit)) for digit in range(10)]
    shown = [2, 4, 8, 16]
    rows = [("held-out image", X_TEST)]
    for d in shown:
        rows += [(f"autoencoder, $d={d}$", runs(d)[0]["out"]), (f"PCA, $d={d}$", pca(d))]
    # Layout in inches: each image is 0.15 in wide (as in encoders_digits_sample.py), on a pitch of 0.3 in in both directions (as much padding as image, no frame).
    image, pitch, left = 0.15, 0.3, 1.1
    width, height = left + len(picks) * pitch, len(rows) * pitch
    fig = plt.figure(figsize=(width, height))
    for r, (title, imgs) in enumerate(rows):
        for c, i in enumerate(picks):
            ax = fig.add_axes([(left + c * pitch + (pitch - image) / 2) / width, (height - (r + 1) * pitch + (pitch - image) / 2) / height,
                               image / width, image / height])
            ax.imshow(np.clip(imgs[i], 0, 1).reshape(8, 8), cmap="gray_r", vmin=0, vmax=1)
            ax.axis("off")
            if c == 0:
                fig.text((left - 0.04) / width, (height - (r + 0.5) * pitch) / height, title, ha="right", va="center", fontsize=6)
    fig.savefig(base.FIGURES / "encoders_digits_reconstruction.png", dpi=300, bbox_inches="tight")
    print(f"\nsaved {(base.FIGURES / 'encoders_digits_reconstruction.png').resolve()}")
