# SKELETON: not implemented, skipped by `make test-code` (see notes/ideas.qmd, idea 13).
"""Learning by Predicting Embeddings: a joint-embedding predictive model on the toy of Learning by Contrast: Anything.

Same data, split, augmentation, dimension and measures as contrast_digits_infonce.py, which is imported, not copied.

Model: a context encoder, a predictor (16 -> 128 -> 16) and a target encoder that is a moving average of the context encoder
(no gradient through it); the loss is a squared distance in the code space between the prediction and the target code of the
other view. No negatives and no decoder.
Runs (five seeds each): with the moving average; with the target encoder tied to the context encoder (collapse expected);
optionally with a variance term in place of the moving average.
Measures: effective rank of the codes (collapse), retrieval of the other view, alignment and uniformity.
Figure: effective rank during training with and without the moving average (../../figures/embedding_spaces/).
PyTorch is a candidate for the stop-gradient and the moving average; if used, say so here and record the dependency.
"""
raise SystemExit("skeleton: not implemented")
