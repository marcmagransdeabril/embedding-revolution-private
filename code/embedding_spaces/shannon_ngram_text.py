"""Shannon's Boundary Problem, question 3: random text from P(word | previous n words), n = 1..3."""
import re
from collections import Counter, defaultdict

import numpy as np

from utils import load_book, sample


def windows(seq, k):
    return list(zip(*(seq[i:] for i in range(k))))


def ngram_model(words, n):
    """Map each n-word context to the counts of the words that followed it, i.e. P(next | context).
    `words` is treated as cyclic so that every context has a successor."""
    model = defaultdict(Counter)
    for *context, nxt in windows(words + words[:n], n + 1):
        model[tuple(context)][nxt] += 1
    return model


def generate(model, n, length, rng):
    out = list(list(model)[rng.integers(len(model))])  # random starting context
    while len(out) < length:
        out += sample(model[tuple(out[-n:])], 1, rng)
    return out


def main():
    words = re.findall(r"[a-z']+", load_book())
    rng = np.random.default_rng(0)
    book_8grams = set(windows(words, 8))
    copied = {}  # fraction of 8-word windows of the generated text found verbatim in the book
    for n in (1, 2, 3):
        model = ngram_model(words, n)
        text = generate(model, n, 2000, rng)
        assert all(w[-1] in model[w[:-1]] for w in windows(text, n + 1))  # only transitions seen in the book
        copied[n] = sum(w in book_8grams for w in windows(text, 8)) / (len(text) - 7)
        deterministic = sum(len(set(v)) == 1 for v in model.values()) / len(model)
        print(f"n={n}: {copied[n]:6.1%} copied, {deterministic:6.1%} contexts with one continuation\n    "
              + " ".join(text[:30]))

    assert copied[1] < 0.01  # n=1: locally plausible, globally new (Shannon's sample)
    assert copied[1] < copied[2] < copied[3]
    assert copied[3] > 0.3  # n=3: mostly the book itself, since most 3-word contexts occur once


if __name__ == "__main__":
    main()
