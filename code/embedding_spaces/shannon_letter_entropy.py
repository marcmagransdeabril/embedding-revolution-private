"""Shannon's Boundary Problem, question 1: entropy of the letter distribution of a book."""
import re
from collections import Counter
from math import log2

from utils import entropy, load_book, sample

# Sanity check of `entropy`: uniform -> log2(k), certain outcome -> 0.
assert abs(entropy(Counter("abcd")) - 2) < 1e-12
assert entropy(Counter("aaaa")) == 0

letters = Counter(re.findall(r"[a-z]", load_book()))
h = entropy(letters)
print(f"letter entropy = {h:.3f} bits  (uniform alphabet: log2(26) = {log2(26):.3f})")

assert len(letters) == 26
assert [c for c, _ in letters.most_common(3)] == ["e", "t", "a"]  # classic English letter ranking
assert 4.1 < h < 4.25 < log2(26)  # uneven letter use costs ~0.5 bit below the uniform maximum

# Zeroth-order approximation: i.i.d. letters with the book's frequencies. It has the same entropy
# by construction, but none of the structure of English (no word boundaries, no spelling).
fake = sample(letters, 200_000)
h_fake = entropy(Counter(fake))
print(f"sampled letters = {''.join(fake[:60])}...  (entropy {h_fake:.3f} bits)")
assert abs(h_fake - h) < 0.01
assert Counter(fake).most_common(1)[0][0] == "e"
