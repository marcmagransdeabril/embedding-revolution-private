# Technology chapters of the earlier plan

The book was organized by technologies until 2026-11-22. It is now organized by the properties of meaning (see `index.qmd` and `tmp/plan_properties.md`), and these twelve chapters were moved here with `git mv`, keeping their text, their section identifiers and their history. This directory is not built: `sync_chapters.py` and `validate_book.py` read only `chapters/`. Each property chapter salvaged from them, by copying, the sections it needs (a comment `salvaged from embedding-technologies-stubs/...` marks each one, and the copies keep the identifiers, so that references resolve in the new chapters). A file here is deleted only when nothing in it is left unclaimed, and only with the author's consent. The moved chapters carry the `open:` notes and the status that they had.

## embedding_spaces.qmd

Status when moved: definitive.

Salvaged by: likeness_as_nearness (counting, predicting and contrasting: done in step 2), meaning_as_generation (reconstruction), meaning_across_senses (predicting embeddings, InfoNCE across modalities); the ledger of limits goes to properties_of_meaning.

Not yet claimed: the sections "Encoder/Decoder and the Chain Rule", "Learning by Contrast: Anything" (the digits experiment), "Learning by Predicting Embeddings", "Learning by Reconstruction", "The Geometry of Meaning", "Where a Single Vector Strains" and "A Space That Cannot Yet Say No", and the twelve question blocks with answers (they leave the book with this chapter unless they are salvaged with their sections; the scripts stay in code/embedding_spaces/).

## generative_spaces.qmd

Status when moved: idea.

Salvaged by: meaning_as_generation (fork, VAE, diffusion, autoregressive, where the map stops, reconciling the families), meaning_and_truth (plausible is not true), meaning_as_path (the geometry a decoder induces).

Nothing unclaimed.

Open note when moved: Home of the debate between prediction in the space (JEPA, @sec-ch-embedding-spaces) and scaled generative models. Decide when the last two sections of @sec-ch-embedding-spaces are written. Whether the closing sections can reconcile the two families, or can only show where they differ, depends on sources not yet read (notes/ideas.qmd, idea 12).

## contextual_vectors.qmd

Status when moved: idea.

Salvaged by: meaning_in_context (from word vectors to contextual vectors, attention, nearness across layers, reasoning in text or in the space, closing), meaning_as_direction (features as directions, sparse autoencoders), meaning_as_region (is the tree in the geometry), meaning_as_arrangement (do models share a geometry), meaning_across_scales (tokenizing the senses).

Nothing unclaimed.

## vector_databases.qmd

Status when moved: idea.

Salvaged by: meaning_and_truth (retrieval-augmented generation, negation and multi-hop, remembering is not knowing), meaning_as_difference (what a fixed-dimension dot product can express), meaning_across_scales (hybrid search and multi-vector), likeness_as_nearness (from exact to approximate search).

Nothing unclaimed.

## tangent_spaces_geodesics.qmd

Status when moved: idea.

Salvaged by: meaning_as_path (tangent spaces and geodesics), meaning_as_region (hyperbolic spaces, the shape of a tree), meaning_as_arrangement (Erlangen programme, symmetries of each sense, Lie groups, gauge equivariance).

Nothing unclaimed.

Open note when moved: Thin evidence for the hyperbolic section. The held sources are the authors' own: Nickel and Kiela 2017 report, on the 82,115 nouns of WordNet, that Poincaré embeddings outperform Euclidean ones significantly on data with latent hierarchies; Tifrea et al. 2019 report that their hyperbolic GloVe is competitive on similarity and analogy and best on hypernymy, and say that no single model outperforms every baseline on every task, and that two earlier hyperbolic word embeddings were not competitive on standard tasks in high dimensions. No comparison independent of the authors, at matched dimension and compute and beyond trees, is held or known. What is durable is the counting argument (volume grows exponentially with radius, so a tree fits in few dimensions). Options: (a) keep the section, limited to hierarchies, as the closing plan already says; (b) move it to the graph chapter, next to the hierarchy of prerequisites; (c) reduce it to the counting argument and move the models to notes/ideas.qmd. Decide when a search finds an independent comparison at matched dimension (queries: hyperbolic versus Euclidean embeddings matched dimension reproducibility; hyperbolic neural networks large scale evaluation), or when the chapter is written without one. If the search finds none, say so in the section and keep (a) or (c).

## graph_embeddings.qmd

Status when moved: idea.

Salvaged by: meaning_as_difference (what a relation can be, knowledge-graph embeddings as a historical sequence, graph databases against vector databases).

Not yet claimed: "Representing Graphs in Vector Spaces" (message passing) and the closing section "Arrows That Point One Way", whose plan text was rewritten in meaning_as_difference.

## topological_deep_learning.qmd

Status when moved: idea.

Salvaged by: meaning_as_arrangement (what pairwise structure cannot express, cochains and boundary operators, Hodge theory, measuring the shape of a representation).

Not yet claimed: the closing section "More Than Pairs".

Open note when moved: Thin evidence. The framework paper held in references/ (Hajij et al.) is the authors' own work, evaluated on four datasets (Human Body, COSEG, SHREC11 and a graph-classification benchmark), and it names its own limits: combinatorial cost in time and memory, dependence on the choice of architecture, difficulty of interpretation and few datasets with higher-order structure. No controlled comparison at scale and independent of the authors is held, and none is known to the author yet. What is durable is the mathematics (boundary operators, the Hodge decomposition, homology). Options: (a) keep the chapter, written around the mathematics and around persistent homology as a tool to test the manifold hypothesis, with the networks told as dated history; (b) merge it as the last section of the graph chapter (More Than Pairs); (c) keep only persistent homology, in the manifold-hypothesis section of the curse-of-dimensionality chapter, and move the rest to notes/ideas.qmd with the reason. Decide when the graph chapter is written, or when a search finds a comparison on a large benchmark that the authors did not run (queries: topological neural network benchmark comparison with message-passing GNNs; higher-order GNN reproducibility). If the search finds none, (b) or (c).

## complex_plane_quantum_logic.qmd

Status when moved: idea.

Salvaged by: meaning_as_region (concepts as subspaces).

Not yet claimed: phase as position and period, complex and hypercomplex weights, unitary dynamics, interference, quantum decision making, and the closing section "Can a Space Say No?"; the chapter was conditional on complex vectors beating real ones of the same size, and none of these has a test yet.

Open note when moved: The chapter earns its place only if complex or hypercomplex vectors beat real ones of the same size, in the representation of meaning or in compute, on a parameter-matched comparison. The comparisons that the book runs are smoke tests at small scale. The verdict rests on parameter-matched comparisons at scale in the literature, and where none exists the section says so. Each section below names the comparison. A section whose comparison shows no gain is dropped to notes/ideas.qmd with the check that failed it, and when no section is left the chapter is removed from the book and from the roadmap in index.qmd. Quantum hardware is out of scope.

## vector_symbolic_architectures.qmd

Status when moved: idea.

Salvaged by: meaning_as_composition (all the sections).

Nothing unclaimed.

Open note when moved: Thin evidence, and overlap. The held sources are a survey (Kleyko et al.) and a capacity analysis (Clarkson et al.) that ties the four common architectures to sketching and Bloom filters. A keyword search of both found no comparison at scale with learned encoders, and the survey itself says the field is hard to track. This is not a full read. What is durable is theory: near-orthogonality and the capacity bounds. Two overlaps. The capacity bounds are already cited in the curse-of-dimensionality chapter (Room for Exponentially Many Directions), and binding is also the subject of Smolensky's tensor product representations in the neuro-symbolic chapter. Options: (a) keep the chapter, written around the binding problem of the ledger of limits and the capacity theory, with the applications told as dated history; (b) merge binding, bundling and permutation into the neuro-symbolic chapter next to tensor product representations, and leave the capacity bounds in the curse chapter; (c) keep it short as a section of the neuro-symbolic chapter. Decide when the neuro-symbolic chapter is written, or when a search finds a comparison with learned encoders at matched compute that the proponents did not run (queries: hyperdimensional computing versus neural network matched accuracy energy; vector symbolic architecture benchmark independent evaluation). If the search finds none, (b) or (c).

## neurosymbolic_integration.qmd

Status when moved: idea.

Salvaged by: meaning_as_composition (systematicity, poverty of the stimulus, bridging, logic tensor networks, tensor product representations, emergent structure), meaning_and_truth (neural theorem proving, reaching "false").

Not yet claimed: the closing section "Parts That Know Their Place", rewritten in meaning_as_composition.

## cross_domain_transfer.qmd

Status when moved: idea.

Salvaged by: meaning_as_arrangement (gauge freedom, aligning two spaces, optimal transport, domain adaptation, zero-shot transfer, principles and parameters, same map different north).

Nothing unclaimed.

## multimodal_embeddings.qmd

Status when moved: idea.

Salvaged by: meaning_across_senses (all the sections but one), meaning_as_path (motion and time).

Nothing unclaimed.
