"""Learning by Prediction, question 2: held-out cross-entropy of the maximum likelihood unigram and bigram predictors."""
import re
from collections import Counter
from math import log2

from utils import load_book

words = re.findall(r"[a-z']+", load_book())
cut = int(0.9 * len(words))
train, test = words[:cut], words[cut:]
uni = Counter(train)
big = Counter(zip(train, train[1:]))
n_train = len(train)
test_pairs = list(zip(test, test[1:]))


def unigram(w: str, c: str) -> float:
    """Maximum likelihood Q(c) = C_c / T (ignores the previous word w)."""
    return uni[c] / n_train


def bigram(w: str, c: str) -> float:
    """Maximum likelihood Q(c | w) = C_wc / C_w (zero when w or the pair was never seen in training)."""
    return big[w, c] / uni[w] if uni[w] else 0.0


def cross_entropy(q, pairs) -> float:
    """Average surprisal, in bits per word, of the second word of each pair given the first."""
    return -sum(log2(q(w, c)) for w, c in pairs) / len(pairs)


n = len(test_pairs)
print(f"training words = {n_train}, test pairs = {n}")
defined = {}
for name, q in (("unigram", unigram), ("bigram", bigram)):
    defined[name] = [p for p in test_pairs if q(*p) > 0]
    zero = n - len(defined[name])
    print(f"{name}: probability zero on {zero / n:.1%} of the test pairs, so its cross-entropy on the test text is infinite;"
          f" on the other {len(defined[name]) / n:.1%} it is {cross_entropy(q, defined[name]):.2f} bits/word")

# Compare the two models on the pairs where the bigram is defined (all of them have a word seen in training).
h_uni = cross_entropy(unigram, defined["bigram"])
h_big = cross_entropy(bigram, defined["bigram"])
print(f"on the pairs where the bigram is defined: unigram {h_uni:.2f}, bigram {h_big:.2f} bits/word")

# The bigram is sharper where it has seen the pair, but silent on a third of the text.
assert h_big < h_uni
assert 0.25 < 1 - len(defined["bigram"]) / n < 0.45
assert 0 < 1 - len(defined["unigram"]) / n < 0.05
