"""Encoder/Decoder and the Chain Rule: a 10 x 10 sample of the 8x8 digits.

The data of encoders_digits_reconstruction.py (imported through contrast_digits_infonce.py: the same split of 1,200 training and
597 held-out images). Column d holds the digit d. The first row is the held-out image of each digit that the reconstruction figure
uses (the first of each in the data), and the nine rows below are a stratified random sample of the training images: nine of each
digit, drawn at random without replacement (seed 0), 90 of the 1,200. Saves ../../figures/embedding_spaces/encoders_digits_sample.png,
about half a page of the book.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import contrast_digits_infonce as base

rng = np.random.default_rng(0)
held_out = [int(np.argmax(base.labels_test == digit)) for digit in range(10)]
drawn = [rng.choice(np.flatnonzero(base.labels_train == digit), 9, replace=False) for digit in range(10)]
print("training images per digit:", np.bincount(base.labels_train).tolist(), "-> 9 of each, 90 of", len(base.train))
grid = [base.test[held_out]] + [base.train[[drawn[digit][k] for digit in range(10)]] for k in range(9)]  # one array of 10 images per row

# Layout in inches: each image is 0.15 in wide, on a pitch of 0.3 in (a gap of 0.15 in, as wide as the image), and a gap of 0.15 in more
# separates the held-out row from the training rows.
IMAGE, PITCH, GAP, LEFT, TOP = 0.15, 0.3, 0.15, 0.25, 0.05
width = LEFT + 10 * PITCH
height = TOP + 10 * PITCH + GAP
fig = plt.figure(figsize=(width, height))
y_of = lambda r: height - TOP - (r + 1) * PITCH + (PITCH - IMAGE) / 2 - (GAP if r > 0 else 0)  # bottom of the image of row r
for r, row in enumerate(grid):
    for c, image in enumerate(row):
        ax = fig.add_axes([(LEFT + c * PITCH + (PITCH - IMAGE) / 2) / width, y_of(r) / height, IMAGE / width, IMAGE / height])
        ax.imshow(image, cmap="gray_r", vmin=0, vmax=1)
        ax.axis("off")
# Labels on the left: the held-out row, and the block of training rows.
x = (LEFT - 0.1) / width
fig.text(x, (y_of(0) + IMAGE / 2) / height, "held out", rotation=90, ha="center", va="center", fontsize=6)
fig.text(x, (y_of(1) + y_of(9) + IMAGE) / 2 / height, "random sample of the training set (90 of 1,200)", rotation=90,
         ha="center", va="center", fontsize=6)
base.FIGURES.mkdir(parents=True, exist_ok=True)
fig.savefig(base.FIGURES / "encoders_digits_sample.png", dpi=300, bbox_inches="tight")
print(f"saved {(base.FIGURES / 'encoders_digits_sample.png').resolve()}")
