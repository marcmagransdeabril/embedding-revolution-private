"""Rice's Theorem, question 3: programs as symbols (equidistant) versus programs as behaviour vectors (graded, no guarantee)."""
import numpy as np

from utils import distances


def bubble_sort(xs):
    xs = list(xs)
    for i in range(len(xs)):
        for j in range(len(xs) - 1 - i):
            if xs[j] > xs[j + 1]:
                xs[j], xs[j + 1] = xs[j + 1], xs[j]
    return xs


def insertion_sort(xs):
    out = []
    for x in xs:
        k = len(out)
        while k > 0 and out[k - 1] > x:
            k -= 1
        out.insert(k, x)
    return out


def sort_descending(xs):
    return sorted(xs, reverse=True)


def identity(xs):
    return list(xs)


def sort_unless_huge(xs):  # sorts every list shorter than 1,000 items and returns the longer ones unchanged
    return sorted(xs) if len(xs) < 1000 else list(xs)


PROGRAMS = [bubble_sort, insertion_sort, sort_descending, identity, sort_unless_huge]


def behaviour(program, inputs) -> np.ndarray:
    """Embedding of a program: its outputs on a fixed set of probe inputs, concatenated."""
    return np.concatenate([program(xs) for xs in inputs]).astype(float)


def main():
    rng = np.random.default_rng(0)
    probes = [rng.integers(0, 10, size=6).tolist() for _ in range(30)]  # 30 lists of 6 digits
    names = [p.__name__ for p in PROGRAMS]

    # As symbols (one-hot): five different texts, so every pair is at sqrt(2).
    onehot = distances(np.eye(len(PROGRAMS)))
    assert np.allclose(onehot[~np.eye(5, dtype=bool)], np.sqrt(2))

    # As behaviour: the distance between the output vectors on the probes.
    B = np.stack([behaviour(p, probes) for p in PROGRAMS])
    D = distances(B)
    i = names.index
    assert D[i("bubble_sort"), i("insertion_sort")] == 0
    assert D[i("bubble_sort"), i("sort_unless_huge")] == 0  # different function, indistinguishable on the probes
    assert D[i("bubble_sort"), i("sort_descending")] > D[i("bubble_sort"), i("identity")] > 0

    # A positive distance is a proof of difference (a counterexample); a zero is only an absence of evidence.
    witness = [xs for xs in probes if bubble_sort(xs) != identity(xs)][0]
    assert bubble_sort(witness) != identity(witness)
    big = list(range(1000, 0, -1))
    assert bubble_sort(big) != sort_unless_huge(big)  # the difference exists, but outside the probes

    print(names)
    print(D.round(1))
    print("sqrt(2) =", round(float(np.sqrt(2)), 3), "between any two programs seen as symbols")


if __name__ == "__main__":
    main()
