"""Counting Company, question 2: random text from the estimates of P(c | w) given by a window-one co-occurrence matrix."""
import re
from collections import Counter, defaultdict

import numpy as np

from utils import load_book, sample


def count_neighbours(words: list[str], symmetric: bool) -> dict[str, Counter]:
    """C[w][c] = number of times c stands right before or after w (symmetric), or right after w only."""
    counts = defaultdict(Counter)
    for w, c in zip(words, words[1:]):
        counts[w][c] += 1
        if symmetric:
            counts[c][w] += 1
    return counts


def generate(counts: dict[str, Counter], start: str, length: int, rng: np.random.Generator) -> list[str]:
    """Markov chain: from w, draw the next word c with probability P(c | w) = C[w, c] / sum_c' C[w, c']."""
    out = [start]
    while len(out) < length:
        # `sample` draws from the empirical distribution count / total of the row. Words with an empty row
        # (the last word of the book in the directed case) restart the chain from a random word.
        out += sample(counts[out[-1]], 1, rng) if counts[out[-1]] else [start]
    return out


def main():
    words = re.findall(r"[a-z']+", load_book())
    in_order = set(zip(words, words[1:]))  # pairs that stand in this order in the book
    results = {}
    for name, symmetric in (("symmetric", True), ("directed", False)):
        counts = count_neighbours(words, symmetric)
        rng = np.random.default_rng(1)
        text = generate(counts, "the", 2000, rng)
        results[name] = np.mean([pair in in_order for pair in zip(text, text[1:])])
        print(f"{name:9s} {results[name]:6.1%} of the generated pairs stand in this order in the book\n    "
              + " ".join(text[:30]))

    assert results["directed"] == 1.0  # the directed chain only follows transitions seen in the book
    assert results["symmetric"] < 0.8  # the symmetric one steps backwards in a sizeable fraction of its moves


if __name__ == "__main__":
    main()
