"""Shannon's Boundary Problem, question 2: entropy of the word distribution of a book."""
import re
from collections import Counter

from utils import entropy, load_book, sample

text = load_book()
words = re.findall(r"[a-z']+", text)
h_letter = entropy(Counter(re.findall(r"[a-z]", text)))
h_word = entropy(Counter(words))

# Per-character comparison: a word plus the following space spans (mean length + 1) characters.
h_per_char = h_word / (sum(map(len, words)) / len(words) + 1)
print(f"word entropy = {h_word:.2f} bits/word, {h_per_char:.2f} bits/char (letters alone: {h_letter:.2f})")

assert 9 < h_word < 11  # thousands of equally "available" symbols instead of 26
assert h_word > h_letter  # larger alphabet, more surprise per symbol...
assert h_per_char < h_letter / 2  # ...but far less per character: words encode spelling constraints

# Zeroth-order word model: i.i.d. words with the book's frequencies. Same entropy as the book,
# but the word order (and so any meaning) is gone.
fake = sample(Counter(words), len(words))
h_fake = entropy(Counter(fake))
print(f"sampled words = {' '.join(fake[:20])} ...  (entropy {h_fake:.2f} bits/word)")
assert abs(h_fake - h_word) < 0.1  # rare words are under-sampled, so slightly below the book's value
