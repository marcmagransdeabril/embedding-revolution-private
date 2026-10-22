"""The Discrete Collapse, question 3: one-hot geometry is blind to renaming, a meaningful one is not."""
import itertools

import numpy as np

from utils import DENSE, WORDS, distances

ONE_HOT = np.eye(len(WORDS))

# Every one of the 5! = 120 renamings leaves the one-hot distances unchanged.
d = distances(ONE_HOT)
for perm in itertools.permutations(range(len(WORDS))):
    assert np.allclose(distances(ONE_HOT[list(perm)]), d)
print("one-hot: all 120 relabellings give exactly the same distance matrix")

# Exchange the labels `dawn` and `king`: the vector of each word is given to the other one.
swap = [WORDS.index(w) for w in ("king", "dusk", "dawn", "queen", "xqzv")]
d_dense = distances(DENSE)
d_swapped = distances(DENSE[swap])
assert not np.allclose(d_dense, d_swapped)
i, j = WORDS.index("dawn"), WORDS.index("dusk")
print(f"dense: d(dawn, dusk) = {d_dense[i, j]:.2f} before the swap, {d_swapped[i, j]:.2f} after it")
