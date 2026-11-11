# Embedding space vs latent space: gaps, errors and inconsistencies

Date: 2026-11-11. Scope: the two findings below, checked against the chapters, stubs, `index.qmd`, `references.bib` and `notes/ideas.qmd`.

Note: `tmp/` is gitignored. Back this file up if it should survive.

## The two findings

### Finding 1. Gap check against Wikipedia

Sources read in full, with See also lists and reference lists (the cited papers were not fetched; papers named below that Wikipedia does not cite are from memory and unverified):

- https://en.wikipedia.org/wiki/Latent_space
- https://en.wikipedia.org/wiki/Embedding_(machine_learning)

The core is already in the book: word2vec, GloVe, latent semantic analysis, one-hot against learned vectors, cosine, dot product and Euclidean distance, manifold hypothesis and intrinsic dimension, distance concentration, Johnson-Lindenstrauss, hyperbolic space, knowledge-graph and network embeddings, multimodal spaces.

### Finding 2. Embedding space and latent space are overlapping but different

Wikipedia treats them as synonyms. Usage in the literature is looser, and the traditions differ.

| | Embedding | Latent |
|:--|:--|:--|
| Origin | Mathematics (maps with distortion), NLP | Statistics (latent variable models, factor analysis), generative models |
| Weight of the word | Objects and the map | A generative story: unobserved cause $\mathbf{z}$ of data $x$ |
| Typical use | One direction, input to vector; similarity is the point | Both directions; sample $\mathbf{z}$ and decode |
| Typical objective | Discriminate or predict (contrast, next word) | Reconstruct or maximize likelihood |
| Meaning of distance | Similarity, by construction of the loss | Smoothness (VAE prior) or nothing in particular (plain autoencoder) |
| Typical indexing | Lookup per discrete object | Encoder output per instance |

They overlap: any hidden representation gets called latent, CLIP vectors are called both, and LSA ("latent") is one of the book's early embeddings. The SVD of the PPMI matrix, $\mathbf{M}\approx\mathbf{E}\mathbf{V}^\top$, is a linear encoder-decoder, and the chapter already says counting "pays in reconstruction error" on the PMI matrix.

Suggested convention (one sentence in Chapter 3 or in the notation summary): *embedding* when the space is defined by a similarity objective, *latent* when it comes with a decoder or a prior; a space can be both. "Embedding space" stays the book's main term.

## Gaps

Ordered by importance. Chapters 4, 6, 7, 8 and 13 are `idea` stubs, so additions there are cheap. Chapter 3's definitive part should stay untouched; provisional sections can take one sentence each.

1. **Reconstruction and generative latent spaces (autoencoders, VAEs, GANs, diffusion).** Wikipedia's main sense of "latent space", and Chapter 3 has "Latent Spaces" in its title. The chapter's four objectives (counting, prediction, contrast, predicting embeddings) lack the one that reconstructs the raw input through a bottleneck. Counting reconstructs a statistic (the PMI matrix), not the input. Only sparse autoencoders appear (Chapter 5). Cheapest fix: one entry in the "what the vector pays for" comparison of "Learning by Predicting Embeddings" (autoencoders pay for every detail, like prediction, but through a bottleneck; a VAE adds a prior so the space can be sampled). Chapter 6 could cover the geometry of generative latent spaces (the Arvanitidis paper on curvature is in `references.bib` and cited only in Chapter 1).
2. **Recommender systems and two-tower models.** Zero mentions. Largest industrial use of embeddings, and user-item matrix factorization is the same SVD and dot product as Chapter 3. One sentence in "Counting Company" (users and items instead of words and contexts) and a place in Chapter 4.
3. **Dot product against cosine in practice.** The dot product favours popular items, cosine ignores magnitude. The plan for "The Geometry of Meaning" says the norm encodes frequency, but Chapter 4's stub has no maximum inner product search (not a nearest-neighbour search).
4. **Bengio and colleagues, 2003, "A Neural Probabilistic Language Model".** The reference the *Embedding* page uses for the term; the bridge between Shannon-style prediction and word2vec. In `references.bib` as `bengio2003neural` (no PDF), cited nowhere. Belongs in "Learning by Prediction".
5. **The Prologue promises more than the chapters deliver.** Molecules, proteins and robot trajectories are named in the Prologue and `index.qmd`, but have a home only as pointers (Epilogue, Chapter 13). Tone the promise down, or give Chapter 13 a paragraph on non-human modalities.
6. Optional, smaller:
   - Siamese and triplet networks as visual ancestors of contrast (one clause in "Learning by Contrast", or leave out to keep it light).
   - Information geometry: the Fisher metric as the local form of the divergences of Shannon's theory (fits Chapter 6 and "Shannon's quantities into geometry").
   - Identifiability and disentanglement (Locatello and colleagues, 2019, from memory): echoes the gauge-freedom result of exercise 22.
   - t-SNE and UMAP as a caution about 2-D pictures; the UMAP link to topology (Chapter 8).
   - Self-organizing maps (Kohonen); choosing the dimension $d$ from intrinsic-dimension estimates.
   - Metric embeddings and distortion as a general frame (only hyperbolic distortion is covered).

## Errors

Found and fixed during this review (all in `chapters/embedding_spaces.qmd`, section "Learning by Contrast", unless noted):

- Units: $\mathrm{PMI}-\ln k$ mixed bits and nats. Fixed (clause "PMI measured in nats"; later the equation was removed in the compression and the shifted-PMI sentence kept with a citation).
- Attribution: the 30-billion-word Mikolov result used the hierarchical softmax, not negative sampling (`mikolov2013distributed`, p. 7). Replaced by the paper's own claim for negative sampling (faster, better vectors for frequent words, p. 2).
- Lost statement: the "change of accounting" (contrast pays only for what separates the positive from the alternatives) was removed in the compression, while the next section's plan and the Chapter 13 stub rely on it. Re-added.
- Orphan bibliography entry `oliveiraesilva2014empirical`, left after the author dropped the citation. Removed.

Still open:

- Line 10 of the chapter: typo "adn" ("dangers adn opportunities"). Fixed on 2026-11-11.
- Rice exercise, answer 12: "Its error rate grows with the difficulty and the adversarial nature of the programs" is an empirical claim about LLMs with no source or date.
- Answers in "Learning by Prediction" are numbered 20 to 23 by hand, while the review skill says never to hardcode numbers.

Quirks on the Wikipedia pages (not book errors, unverified beyond the pages themselves):

- *Latent space* says the dimension is "usually lower" than the feature space. Not true of overcomplete dictionaries such as sparse autoencoders. It also describes embedding as both a technique and its result, while *Embedding (machine learning)* defines it as a technique that reduces dimension.
- *Latent space* cites the Arvanitidis paper as 2021 (the arXiv revision); the book's entry says ICLR 2018.

## Inconsistencies

- **Terminology.** The book uses the two terms as synonyms and never defines either: 31 lines contain "latent" and 9 contain "embedding space". Titles and headings mix them: Chapter 3 ("Embedding and Latent Spaces"), Chapter 9 ("Wave-Nature in Latent Space"), "Hyperbolic Latent Spaces" (Chapter 6), "Latent Space" in an Epilogue heading, "persistent homology in latent spaces" (Chapter 8), "latent manifolds" (Chapter 12), "latent coordinates" (Chapter 7). The notation summary in `index.qmd` defines neither term.
- **One method, two names.** "Learning by Predicting Embeddings" (section title) against "latent prediction" and "toy latent predictor" in the same section's plan.
- **Title against content.** Chapter 3 promises latent spaces but covers embedding spaces (see Gap 1).
- **Past tense about a stub.** "Chapter 2 showed…" (Chapter 3) depends on a provisional stub whose `open:` field allows merging into Chapter 3 or splitting.
- **Prologue against body.** See Gap 5.

## Next steps (for the author to decide)

1. Choose the embedding/latent convention and put the sentence in Chapter 3 or the notation summary; then align the headings and the "latent prediction" wording.
2. Decide Gaps 1 to 4 (one sentence or one plan entry each).
3. Decide Gap 5 (tone down the Prologue, or add a paragraph in Chapter 13).
4. Fix the typo in line 10; source or hedge the LLM error-rate claim.
