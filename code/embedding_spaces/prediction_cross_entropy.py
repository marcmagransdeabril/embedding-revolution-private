"""Learning by Prediction, question 2: held-out cross-entropy of add-one unigram and bigram predictors."""
import re
from collections import Counter
from math import log2

from utils import load_book

words = re.findall(r"[a-z']+", load_book())
cut = int(0.9 * len(words))
train, test = words[:cut], words[cut:]
vocab_size = len(set(words))  # vocabulary of the whole book, so that no test word has probability zero
uni = Counter(train)
big = Counter(zip(train, train[1:]))
n_train = len(train)
test_pairs = list(zip(test, test[1:]))


def cross_entropy(q) -> float:
    """Average surprisal, in bits per word, of each test word given the previous one."""
    return -sum(log2(q(w, c)) for w, c in test_pairs) / len(test_pairs)


h_uni = cross_entropy(lambda w, c: (uni[c] + 1) / (n_train + vocab_size))
h_big = cross_entropy(lambda w, c: (big[w, c] + 1) / (uni[w] + vocab_size))
unseen = sum(big[p] == 0 for p in test_pairs) / len(test_pairs)
print(f"|V| = {vocab_size}, training words = {n_train}")
print(f"unigram, add-one: {h_uni:.2f} bits/word")
print(f"bigram,  add-one: {h_big:.2f} bits/word")
print(f"test pairs never seen in training: {unseen:.0%}")

# Smaller pseudo-counts, and mixing the bigram with the unigram, show that the smoothing is the culprit.
for lam in (0.1, 0.01):
    h = cross_entropy(lambda w, c: (big[w, c] + lam) / (uni[w] + lam * vocab_size))
    print(f"bigram, add-{lam}: {h:.2f} bits/word")
h_mix = cross_entropy(lambda w, c: 0.5 * (big[w, c] / uni[w] if uni[w] else 0) + 0.5 * (uni[c] + 1) / (n_train + vocab_size))
print(f"half bigram (no smoothing) + half unigram: {h_mix:.2f} bits/word")

# Knowing the previous word should help, yet the add-one bigram compresses worse than the unigram.
assert h_big > h_uni
assert 0.25 < unseen < 0.45
assert h_mix < h_uni
