# Question tree

Source of truth for the structure of the book (plan: `tmp/plan_tests_refactor.md`, 2026-11-26). Checked by `.github/skills/build-book/scripts/check_question_tree.py` (`make check-tree`). One question per chapter, one or two models per chapter. A model is written `Name:anchor`, where the anchor is its section in `chapters/zoo_of_models.qmd`; a model that is a testbed and not a method has the anchor `testbed`.

Order of the book: symbols (no Part), Part I, Part II, Part III, Epilogue (no Part). Row order below is the order of `_quarto.yml`.

## Parts

| Part | Title | Test |
|---|---|---|
| I | The Librarian Test | can a computer shelve and find things by meaning alone, with one fixed place for each thing? |
| II | Critical Literacy | can a representation be read critically: scale, context, truth, structure and generation? |
| III | Speculative Tests | the universal translator and alien technology: no judge exists, and a failure is not informative |

## Chapters

| Part | Chapter | Question | Models | Main text it reuses |
|---|---|---|---|---|
| I | meaning_as_likeness | what can a distance between static vectors say about likeness? | PPMI-SVD:sec-zoo-ppmi-svd, SGNS:sec-zoo-sgns | the refactored likeness chapter |
| I | meaning_as_difference | is the offset between related pairs consistent? | SGNS:sec-zoo-sgns, TransE:sec-zoo-transe | the difference stub; Tversky and "Near but Not Alike" from likeness |
| I | meaning_as_direction | is a quality a direction you can move along? | SGNS:sec-zoo-sgns | the direction stub; steering and SAE kept as candidates |
| I | meaning_as_region | does a region hold a concept better than a point? | SGNS:sec-zoo-sgns, Poincare:sec-zoo-poincare | the region stub |
| I | meaning_across_senses | does a second sense add meaning beyond the pairing? | CLIP:sec-zoo-clip, SGNS:sec-zoo-sgns | the senses stub; "Built In or Emergent?" from likeness |
| I | memory_retrieval | can the librarian find the passage that answers a question? | BM25:sec-zoo-bm25, SBERT:sec-zoo-sbert | the RAG, approximate-search and hybrid-search sections of truth and scales; the ground-truth evaluation report |
| II | meaning_across_scales | what does a fixed-size vector keep of a text as it grows? | SIF:sec-zoo-sif, SBERT:sec-zoo-sbert | the scales stub; the composition order test |
| II | meaning_in_context | does a word keep its meaning when its situation changes? | BERT:sec-zoo-bert, SGNS:sec-zoo-sgns | the context stub; anisotropy from likeness |
| II | meaning_and_truth | does truth live in the space or must it be looked up? | GPT-2 small:sec-zoo-gpt2, BM25:sec-zoo-bm25 | the truth stub, minus the retrieval sections |
| II | meaning_and_structure | what can a structured store hold that a vector cannot? | tensor product:sec-zoo-tpr, LTN:sec-zoo-ltn | composition (binding, tensor products, LTN), graph versus vector databases, neural theorem proving |
| II | meaning_as_generation | can a space be written to as well as read? | autoencoder:sec-zoo-autoencoder, VAE:sec-zoo-vae | the generation stub; path (straight line, decoder geometry) |
| III | meaning_as_arrangement | can two spaces be aligned from relations alone? | SGNS:sec-zoo-sgns, PPMI-SVD:sec-zoo-ppmi-svd | `meaning_as_arrangement` retitled The Universal Translator; the loss and many-runs tests from likeness |
| III | alien_technology | can an unknown system's function be recovered from its behaviour? | Ashby oscillators:testbed | `notes/function_of_physical_systems.md` and the alien section of the tests chapter |

## Chapters outside the Parts

| Position | Chapter | Question |
|---|---|---|
| first | symbols_without_interior | what would we like to have from a technology of meaning, given that exact meaning is out of reach? |
| last | epilogue | what do current spaces represent, and what is missing? |
