"""Learning by Contrast: Words, question 2: the cost of adding books in a new language, with counting, prediction and contrast.

The book is Pride and Prejudice (the pinned text of utils.py, tokenized as in prediction_cross_entropy.py), with a window of one word on
each side. The new books are modelled by a second copy of it in another language: the same number of words and pairs and the same size of
vocabulary, with no word in common with the first (a stand-in with the right size, not a translation). Counted, per epoch over the new
books and for d = 100 and K = 5:
  counting    the entries of the co-occurrence matrix before and after (dense), its non-zero entries, and the cost of the SVD of the dense
              matrix (about N^3 multiply-adds), which has to be redone on the whole matrix;
  prediction  the multiply-adds of the scores of one pair, N d, with N the vocabulary on which the softmax normalizes, and the rows of V
              that one step changes (N);
  contrast    the same for K + 1 candidates: (K + 1) d multiply-adds and K + 1 rows, whatever N.
The numbers are operation counts, not timings.
"""
import re
from collections import Counter

from utils import load_book

D, K = 100, 5
words = re.findall(r"[a-z']+", load_book())
vocab = len(set(words))
pairs = 2 * (len(words) - 1)  # (word, neighbour) pairs with a window of one word on each side
distinct = len(Counter(zip(words, words[1:])) | Counter(zip(words[1:], words)))  # non-zero entries of the symmetric matrix C

print(f"one book: {len(words):,} words, vocabulary |V| = {vocab:,}, {pairs:,} pairs, {distinct:,} non-zero entries of C "
      f"({distinct / vocab ** 2:.2%} of the {vocab ** 2:,} entries)")
both = 2 * vocab  # the second book shares no word with the first
print(f"two books in two languages: N = {both:,} words; the entries of C grow from {vocab ** 2:,} to {both ** 2:,} (x{both ** 2 / vocab ** 2:.0f}), "
      f"the non-zero ones from {distinct:,} to {2 * distinct:,} (x2)")
print(f"\nmultiply-adds of an SVD of the dense matrix (about N^3): {vocab ** 3:.2e} before, {both ** 3:.2e} after (x{both ** 3 / vocab ** 3:.0f})")
print(f"\none epoch over the new book ({pairs:,} pairs), d = {D}, K = {K}")
print(f"{'':12} {'rows of V per step':>20} {'multiply-adds per pair':>24} {'per epoch':>12}")
for name, rows in (("prediction", both), ("contrast", K + 1)):
    cost = rows * D
    print(f"{name:12} {rows:>20,} {cost:>24,} {pairs * cost:>12.2e}")
print(f"\nthe softmax step costs {both / (K + 1):,.0f} times the contrast step with the two languages "
      f"({vocab / (K + 1):,.0f} times with the first language alone)")
print(f"parameters of the two matrices E and V: {2 * vocab * D:,} before, {2 * both * D:,} after (both methods)")
