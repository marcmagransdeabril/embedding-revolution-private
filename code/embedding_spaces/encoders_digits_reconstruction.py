"""Encoder/Decoder and the Chain Rule, question 1: an encoder that turns an image into a few numbers, and a decoder that checks them.

The 8x8 digits of contrast_digits_infonce.py (imported, not copied: the same 1,200 training and 597 held-out images, the same Adam settings).
The images are clean here, without augmentation: the only task is to rebuild the image from the code. The encoder is the one of the text,
64 -> 128 (ReLU) -> 16 (no ReLU), and the decoder is its mirror, 16 -> 128 (ReLU) -> 64 (no ReLU), trained in PyTorch (float64) with the
squared error per pixel. The backward pass of the section is `loss.backward()` (automatic differentiation) and the update is `torch.optim.Adam`.
The initial weights are drawn with numpy, Gaussian with standard deviation 1/sqrt(inputs), and the biases start at 0.

Models (five seeds each): the autoencoder 64 -> 128 -> d -> 128 -> 64, for the size of the code d = 2, 4, 8, 16, 32 and 64 (d = 16 is the one
of the text). References, not trained: the PCA with the same number of components d (the best linear code, Eckart-Young), and the mean image,
which is the PCA with no component (d = 0). The held-out error is the squared error per pixel with the 95% bootstrap interval over the seeds
and the 597 images, as in contrast_digits_infonce.py.

Prints the rows of the table of the chapter, with the training error and the number of parameters. Saves
../../figures/embedding_spaces/encoders_digits_reconstruction.png: one held-out image of each digit (the first of each in the data), and its
reconstructions by the autoencoder and by the PCA with d = 2, 4, 8 and 16 numbers (the first seed).
"""
from concurrent.futures import ProcessPoolExecutor
import os

for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[var] = "1"

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from torch import nn

import contrast_digits_infonce as base  # data, Adam settings, bootstrap interval

torch.set_num_threads(1)
torch.set_default_dtype(torch.float64)

DIM, HIDDEN, STEPS, BATCH, SEEDS, LEARNING_RATE = base.DIM, base.HIDDEN, base.STEPS, base.PREDICTOR_BATCH, base.SEEDS, base.LEARNING_RATE
X_TRAIN, X_TEST = base.train.reshape(len(base.train), 64), base.test.reshape(len(base.test), 64)
SWEEP_DIMS = [2, 4, 8, 16, 32, 64]  # the size of the code
# name -> sizes of the encoder
MODELS = {
    "autoencoder": [64, HIDDEN, DIM],
}
SWEEP = {f"d = {d}": [64, HIDDEN, d] for d in SWEEP_DIMS if d != DIM}
ALL = MODELS | SWEEP


def autoencoder(sizes: list[int], rng: np.random.Generator) -> nn.Sequential:
    """The encoder `sizes`, then its mirror. A ReLU follows every layer except the one that writes the code and the one that writes the pixels."""
    full = sizes + sizes[::-1][1:]
    layers = []
    for i, (a, b) in enumerate(zip(full[:-1], full[1:])):
        linear = nn.Linear(a, b)
        # the same draws as the numpy version, so every seed starts from the same numbers
        linear.weight.data = torch.tensor((rng.standard_normal((a, b)) / np.sqrt(a)).T)
        linear.bias.data.zero_()
        layers.append(linear)
        code, last = i == len(sizes) - 2, i == len(full) - 2
        if not (code or last):
            layers.append(nn.ReLU())
    return nn.Sequential(*layers)


def train(job):
    name, seed = job
    sizes = ALL[name]
    rng = np.random.default_rng(seed)
    model = autoencoder(sizes, rng)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    x_train, x_test = torch.tensor(X_TRAIN), torch.tensor(X_TEST)
    for _ in range(STEPS):
        x = x_train[rng.choice(len(X_TRAIN), BATCH, replace=False)]
        loss = ((model(x) - x) ** 2).mean()
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    with torch.no_grad():
        out_test, out_train = model(x_test).numpy(), model(x_train).numpy()
    return dict(name=name, seed=seed, test=np.mean((out_test - X_TEST) ** 2, axis=1), train=float(np.mean((out_train - X_TRAIN) ** 2)),
                out=out_test, model=model, parameters=sum(p.numel() for p in model.parameters()))


if __name__ == "__main__":
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

    print("\n| $d$ | PCA | autoencoder | autoencoder minus PCA | autoencoder, training error | parameters |")
    print(f"| 0 (mean image) | {base.fmt(pca_error[0], '.4f')} | | | | |")
    for d in SWEEP_DIMS:
        mean, low, high = base.interval(ae_error[d] - pca_error[d])
        print(f"| {d} | {base.fmt(pca_error[d], '.4f')} | {base.fmt(ae_error[d], '.4f')} | {mean:+.4f} [{low:+.4f}, {high:+.4f}] "
              f"| {ae_train[d]:.4f} | {runs(d)[0]['parameters']:,} |")

    assert pca_error[64].mean() < 1e-12
    assert all(pca_error[a].mean() > pca_error[b].mean() for a, b in zip([0] + SWEEP_DIMS, SWEEP_DIMS))
    assert ae_error[DIM].mean() < 0.5 * pca_error[0].mean()
    assert base.interval(ae_error[DIM] - pca_error[DIM])[2] < 0

    base.FIGURES.mkdir(parents=True, exist_ok=True)
    picks = [int(np.argmax(base.labels_test == digit)) for digit in range(10)]
    rows = [("held-out image", X_TEST)]
    for d in [2, 4, 8, 16]:
        rows += [(f"autoencoder, $d={d}$", runs(d)[0]["out"]), (f"PCA, $d={d}$", pca(d))]
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
    path = base.FIGURES / "encoders_digits_reconstruction.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    print(f"\nsaved {path.resolve()}")
