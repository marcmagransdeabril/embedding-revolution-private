"""Learning by Reconstruction: the toy of Learning by Contrast: Anything, with autoencoders instead of InfoNCE.

The data (the 8x8 digits, 1,200 training and 597 held-out images), the augmentation (a shift of at most one pixel and Gaussian noise
of 0.15), the 16-dimensional code, the Adam settings, the two fixed held-out views and every measure are those of
contrast_digits_infonce.py, which is imported and not copied. Six reconstructive models, five seeds each:

  predict the other view   the model of Learning by Contrast: Anything: encoder 64 -> 128 -> 16, linear read-out of the 16 coordinates (imported)
  linear AE, same view     64 -> 16 -> 64, no nonlinearity, input and target the same augmented view (the Eckart-Young case)
  linear AE, other view    the same, the target is the other augmented view of the image
  AE, other view           64 -> 128 -> 16 -> 128 -> 64, the target is the other view (the 'predict' model with a nonlinear decoder)
  AE, same view            the same network, input and target the same augmented view (reference row)
  denoising AE             the same network, the input is an augmented view and the target is the clean image

For each: the held-out squared error per pixel against the other view and against the clean image, the retrieval of the other view
among the held-out views, alignment, uniformity, offset (as in contrast_digits_infonce.py) and the effective rank of the codes (the
exponential of the entropy of the normalized singular values of the centred held-out codes). The InfoNCE encoder with N = 128 is run
as a reference row (it has no decoder).

The linear autoencoders are trained for 20,000 steps and the others for 2,000, the length of the contrast script: Adam needs the
longer run to reach the optimum of a linear model, which is what the Eckart-Young check is about.

Checks (they fail loudly): the 'predict' row and the InfoNCE row reproduce the numbers printed by contrast_digits_infonce.py, and
the linear autoencoder of the same view reaches, on held-out views, the error of the PCA of the same dimension (Eckart-Young) to
within 2%, with a decoder whose span is within 25 degrees of the span of the principal components (and the PCA error is never
beaten).

Saves ../../figures/embedding_spaces/reconstruct_digits_ae.png: retrieval against the held-out error to the clean image, one point
per model and seed.
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

import contrast_digits_infonce as base  # data, augmentation, encoder, measures, Adam settings

DIM, HIDDEN, STEPS, BATCH, SEEDS = base.DIM, base.HIDDEN, base.STEPS, base.PREDICTOR_BATCH, base.SEEDS
LINEAR_STEPS = 10 * STEPS  # Adam finds the principal subspace of a linear autoencoder slowly; the Eckart-Young check needs the optimum
FIGURES = base.FIGURES
CLEAN_TEST = base.test.reshape(len(base.test), 64)  # the held-out images, no augmentation
# (name, architecture, input, target); 'a' is an augmented view, 'c' another augmented view of the same image, 'x' the clean image
MODELS = {
    "linear AE, same view": ("linear", "a", "a"),
    "linear AE, other view": ("linear", "a", "c"),
    "AE, other view": ("nonlinear", "a", "c"),
    "AE, same view": ("nonlinear", "a", "a"),
    "denoising AE": ("nonlinear", "a", "x"),
}


def encode(params: dict, x: np.ndarray, arch: str):
    """The 16 coordinates z of x, and what backward needs."""
    if arch == "linear":
        return x @ params["E"] + params["e"], (x,)
    cache = base.forward(params, x)[1]
    return cache[2], cache


def decode(params: dict, z: np.ndarray, arch: str):
    """The 64 pixels reconstructed from z, and what backward needs."""
    if arch == "linear":
        return z @ params["D"] + params["d"], (z,)
    h = np.maximum(0, z @ params["W3"] + params["b3"])
    return h @ params["W4"] + params["b4"], (z, h)


def reconstruction_loss(params: dict, arch: str, a: np.ndarray, target: np.ndarray):
    """Squared error per pixel between the reconstruction of a and the target, and its gradients."""
    z, enc_cache = encode(params, a, arch)
    out, dec_cache = decode(params, z, arch)
    error = out - target
    loss = float(np.mean(error ** 2))
    grads = {k: np.zeros_like(v) for k, v in params.items()}
    dout = 2 * error / error.size
    if arch == "linear":
        grads["D"], grads["d"] = z.T @ dout, dout.sum(0)
        dz = dout @ params["D"].T
        grads["E"], grads["e"] = a.T @ dz, dz.sum(0)
    else:
        _, h = dec_cache
        grads["W4"], grads["b4"] = h.T @ dout, dout.sum(0)
        dpre = (dout @ params["W4"].T) * (h > 0)
        grads["W3"], grads["b3"] = z.T @ dpre, dpre.sum(0)
        base.backward_encoder(params, grads, enc_cache, dpre @ params["W3"].T)
    return loss, grads


def train(model: str, seed: int):
    """Adam on batches of BATCH training images, as train_encoder of contrast_digits_infonce.py (LINEAR_STEPS steps for the linear models)."""
    arch, source, target_kind = MODELS[model]
    rng = np.random.default_rng(seed)
    if arch == "linear":
        params = {"E": rng.standard_normal((64, DIM)) / 8, "e": np.zeros(DIM),
                  "D": rng.standard_normal((DIM, 64)) / np.sqrt(DIM), "d": np.zeros(64)}
    else:
        params = {"W1": rng.standard_normal((64, HIDDEN)) / 8, "b1": np.zeros(HIDDEN),
                  "W2": rng.standard_normal((HIDDEN, DIM)) / np.sqrt(HIDDEN), "b2": np.zeros(DIM),
                  "W3": rng.standard_normal((DIM, HIDDEN)) / np.sqrt(DIM), "b3": np.zeros(HIDDEN),
                  "W4": rng.standard_normal((HIDDEN, 64)) / np.sqrt(HIDDEN), "b4": np.zeros(64)}
    m = {k: np.zeros_like(v) for k, v in params.items()}
    v = {k: np.zeros_like(p) for k, p in params.items()}
    for t in range(1, (LINEAR_STEPS if arch == "linear" else STEPS) + 1):
        x = base.train[rng.choice(len(base.train), BATCH, replace=False)]
        views = {"a": base.augment(x, rng), "c": base.augment(x, rng), "x": x.reshape(len(x), 64)}
        target = views["a"] if target_kind == "a" else views[target_kind]
        _, grads = reconstruction_loss(params, arch, views["a"], target)
        for k in params:
            m[k] = 0.9 * m[k] + 0.1 * grads[k]
            v[k] = 0.999 * v[k] + 0.001 * grads[k] ** 2
            params[k] -= base.LEARNING_RATE * (m[k] / (1 - 0.9 ** t)) / (np.sqrt(v[k] / (1 - 0.999 ** t)) + 1e-8)
    return params, arch


def effective_rank(z: np.ndarray) -> float:
    s = np.linalg.svd(z - z.mean(0), compute_uv=False)
    p = s / s.sum()
    return float(np.exp(-np.sum(p * np.log(p + 1e-12))))


def principal_angle(basis_a: np.ndarray, basis_b: np.ndarray) -> float:
    """Largest principal angle (radians) between the row spaces of two matrices."""
    qa, qb = np.linalg.qr(basis_a.T)[0], np.linalg.qr(basis_b.T)[0]
    return float(np.arccos(np.clip(np.linalg.svd(qa.T @ qb, compute_uv=False).min(), -1, 1)))


def measures(z_a: np.ndarray, z_b: np.ndarray, out_a=None) -> dict:
    z = np.concatenate([z_a, z_b])
    row = dict(retrieval=base.retrieval(z_a, z_b), alignment=base.alignment(z_a, z_b), uniformity=base.uniformity(z_a),
               offset=float(np.linalg.norm(z.mean(0)) / np.linalg.norm(z, axis=1).mean()), rank=effective_rank(z))
    if out_a is not None:
        row |= dict(err_other=float(np.mean((out_a - base.VIEW_B) ** 2)), err_clean=float(np.mean((out_a - CLEAN_TEST) ** 2)),
                    err_same=float(np.mean((out_a - base.VIEW_A) ** 2)))
    return row


def run(job):
    model, seed = job
    if model == "predict the other view":
        params, _ = base.train_encoder("predict", BATCH, seed)
        z_a, z_b = (base.forward(params, view)[1][2] for view in (base.VIEW_A, base.VIEW_B))
        return dict(model=model, seed=seed, **measures(z_a, z_b, z_a @ params["W3"] + params["b3"]))
    if model == "InfoNCE, N = 128":
        params, _ = base.train_encoder("infonce", 128, seed)
        z_a, z_b = (base.forward(params, view)[1][2] for view in (base.VIEW_A, base.VIEW_B))
        return dict(model=model, seed=seed, **measures(z_a, z_b))
    params, arch = train(model, seed)
    z_a, z_b = encode(params, base.VIEW_A, arch)[0], encode(params, base.VIEW_B, arch)[0]
    row = dict(model=model, seed=seed, **measures(z_a, z_b, decode(params, z_a, arch)[0]))
    if model == "linear AE, same view":
        row["decoder"] = params["D"]
    return row


if __name__ == "__main__":
    names = ["predict the other view", *MODELS, "InfoNCE, N = 128"]
    with ProcessPoolExecutor() as pool:
        results = list(pool.map(run, [(name, seed) for name in names for seed in SEEDS]))
    by = {name: [r for r in results if r["model"] == name] for name in names}

    # Reference rows from the contrast script: the pixels and the PCA of the same dimension (a code, but no decoder trained).
    mean_train = base.train.reshape(len(base.train), 64).mean(0)
    _, _, vt = np.linalg.svd(base.train.reshape(len(base.train), 64) - mean_train, full_matrices=False)

    print(f"train images = {len(base.train)}, held-out images = {len(base.test)}, chance = {1 / len(base.test):.2%}; "
          f"linear autoencoders trained for {LINEAR_STEPS} steps, the other models for {STEPS}")
    print(f"\n{'':24} {'err other view':>16} {'err clean image':>16} {'retrieval':>20} {'alignment':>10} {'uniformity':>11}"
          f" {'offset':>7} {'eff. rank':>9}   (mean [min, max] over {len(SEEDS)} seeds)")
    for name in names:
        rs = by[name]
        col = lambda k: np.array([r[k] for r in rs])
        errs = ("", "") if name.startswith("InfoNCE") else (f"{col('err_other').mean():.4f}", f"{col('err_clean').mean():.4f}")
        print(f"{name:24} {errs[0]:>16} {errs[1]:>16} {base.fmt(col('retrieval'), '.1%'):>20} {col('alignment').mean():>10.2f} "
              f"{col('uniformity').mean():>11.2f} {col('offset').mean():>7.2f} {col('rank').mean():>9.1f}")

    # The 'predict' and InfoNCE rows are the rows of the contrast script (same seeds, same code).
    p, i = by["predict the other view"], by["InfoNCE, N = 128"]
    assert round(np.mean([r["retrieval"] for r in p]) * 100, 1) == 13.9, "the predict row no longer matches the contrast script"
    assert round(np.mean([r["retrieval"] for r in i]) * 100, 1) == 38.8, "the InfoNCE row no longer matches the contrast script"
    assert round(np.mean([r["offset"] for r in p]), 2) == 0.96 and round(np.mean([r["alignment"] for r in p]), 2) == 0.03

    # Eckart-Young: the linear autoencoder of the same view reaches the error of the PCA of the same dimension. The PCA is that of the
    # augmented training views (the distribution the autoencoder sees), and the error is measured on the held-out views, same view.
    rng = np.random.default_rng(123)
    aug = np.concatenate([base.augment(base.train, rng) for _ in range(20)])
    centre = aug.mean(0)
    pcs = np.linalg.svd(aug - centre, full_matrices=False)[2][:DIM]
    recon = (base.VIEW_A - centre) @ pcs.T @ pcs + centre
    pca_error = float(np.mean((recon - base.VIEW_A) ** 2))
    linear_error = np.array([r["err_same"] for r in by["linear AE, same view"]])
    angles = [principal_angle(r["decoder"], pcs) for r in by["linear AE, same view"]]
    print(f"\nEckart-Young: held-out same-view error of the PCA with {DIM} components = {pca_error:.4f}; "
          f"of the linear autoencoder = {linear_error.mean():.4f} [{linear_error.min():.4f}, {linear_error.max():.4f}]; "
          f"largest principal angle between its decoder and the components, per seed: "
          + ", ".join(f"{np.degrees(a):.1f} deg" for a in angles))
    assert pca_error <= linear_error.min() * 1.001, "no linear map of rank 16 can beat the PCA (Eckart-Young)"
    assert linear_error.max() <= pca_error * 1.02, "the linear autoencoder did not reach the error of the PCA"
    assert max(angles) < np.radians(25), "the linear autoencoder did not find the principal subspace"

    # Figure: retrieval of the other view against the error to the clean image, one point per model and seed.
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(4.6, 3.0))
    for k, name in enumerate(n for n in names if not n.startswith("InfoNCE")):
        ax.scatter([r["err_clean"] for r in by[name]], [r["retrieval"].mean() for r in by[name]], s=14, color=f"C{k}", label=name)
    ax.axhline(np.mean([r["retrieval"] for r in i]), color="C3", linewidth=0.8, linestyle="--", label="InfoNCE, N = 128 (no decoder)")
    ax.set(xlabel="held-out squared error to the clean image, per pixel", ylabel="retrieval of the other view")
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.legend(fontsize=6)
    ax.tick_params(labelsize=7)
    ax.xaxis.label.set_size(7)
    ax.yaxis.label.set_size(7)
    fig.tight_layout()
    fig.savefig(FIGURES / "reconstruct_digits_ae.png", dpi=300, bbox_inches="tight")
    print(f"saved {(FIGURES / 'reconstruct_digits_ae.png').resolve()}")
