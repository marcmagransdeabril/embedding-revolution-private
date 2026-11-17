# Idea 16: embedding the meaning of the formal sciences (working notes, status: idea, not part of the book)

This file is idea 16 of [ideas.qmd](ideas.qmd). Its sibling, idea 17 (given a physical system, can we understand its function?), is in [function_of_physical_systems.md](function_of_physical_systems.md).

Seeded on 2026-11-17 from a conversation. No literature review has been done for this idea; the statements below are my reading, from memory, and none is checked against `references/`.

## Trigger

An article, "Chemistry is actually geometry" (chillphysicsenjoyer.substack.com, 2026-11-16), introduces Feinberg's chemical reaction network theory: the qualitative behavior of a reaction network (oscillation, multistability, robustness) can be predicted from structure (the stoichiometric subspace, the deficiency, the linkage classes) with few or no rate constants. I read the article only up to its section on representing chemical systems; the page was truncated.

The author's observation: the same move applies to all sciences, and the geometry need not be the point. The point is meaning. Physics, mathematics, chemistry and engineering each keep their meaning in artifacts (Lean, SPICE, VHDL, AutoCAD, Simulink, reaction networks). How should a machine represent it?

## The question

The book asks what meaning becomes when it is a position in a space. For a sentence, meaning is use. For a formal artifact, meaning is a formal semantics: a map from the artifact to behavior or truth. So the question is whether to embed the syntax, the semantics, or both and a learned map between them.

## Avenues (my list, to review against the literature)

1. **Keep the artifact; embed around it.** Lean, netlists, CAD files stay as programs, and embeddings serve as index or retrieval (premise selection, code search). The artifact is ground truth.
2. **Embed the structure.** Treat the artifact as a typed graph and use graph networks with built-in symmetries (permutation invariance; rotation equivariance for molecules and CAD).
3. **Embed the behavior.** Represent a system by what it does (trajectories, transfer functions, input-output maps, operator or Koopman views), so that structurally different but equivalent systems are neighbors.
4. **Learn a simulator or surrogate.** Neural operators, learned physics engines, world models. Fast and differentiable; no guarantee.
5. **Pair a learner with a checker.** A neural model proposes; a formal tool verifies (Lean kernel, SPICE, a design-rule check). The embedding gives intuition and the formal system gives truth.
6. **Invariants as coordinates.** The Feinberg move: a few structural quantities (deficiency, conserved quantities, topological indices) that fix qualitative behavior. Lowest dimension and most interpretable, but available only where theory has found them.

The tension: avenues 1 and 6 are exact and brittle; 3 and 4 are smooth and approximate.

## What the tools expose (from memory)

| Tool | Semantics | Observable |
|---|---|---|
| Lean, Coq, Isabelle | Type theory; a proof term is a program | Proof states, terms |
| SPICE | Differential-algebraic equations of devices | Node voltages, branch currents |
| VHDL, Verilog | Logic and timing | Signals, components |
| Simulink, Modelica | Typed ports, continuous and discrete dynamics | Port variables |
| CAD | A construction sequence producing geometry | Features, boundary representation |
| Reaction network | Mass-action kinetics | Species concentrations |

## Where it could connect to the book (judged from the roadmap, not the chapter bodies)

- `neurosymbolic_integration`: formal artifacts, a checker as verifier, entailed / refuted / undetermined verdicts.
- `graph_embeddings`: netlists and reaction networks as graphs.
- `tangent_spaces_geodesics`: symmetry and equivariance, which is the substack article's geometry in the book's terms.
- `topological_deep_learning`: whether reaction networks map onto cell complexes is unchecked.
- `generative_spaces`: learned simulators and world models.

## Open questions

- Does an embedding of an artifact's behavior beat an embedding of its text on a task that needs function (equivalence, repair, design to a specification)?
- Is composition preserved (do subcircuit embeddings combine into the circuit's embedding)? Circuits and proofs are strongly compositional, so this is a cleaner test of the book's claim than language is.
- Which of these representations is the book about: vectors that stand in for the artifact, or vectors that stand in for what it means?
- Category theory (string diagrams, compositional semantics of circuits) is the formal language for composition; is it a section or a reference?

## Next steps

- [ ] Literature review: embedding Lean and other proof libraries, circuits (netlists, analog), CAD, reaction networks; equivariant networks for molecules; neural operators.
- [ ] Read the rest of the Feinberg article and check how chemical reaction network theory relates to topological deep learning.
- [ ] Decide whether idea 16 is a chapter section or stays a note, after the review.

---

## Review (2026-11-17)

The article was read in full this time (the page was fetched directly). Two corrections and one new source.

1. **What the article covers.** It works up to the *deficiency zero theorem* and stops there: species, reaction vectors, the stoichiometric subspace and compatibility classes as linear algebra, linkage classes, weak reversibility, and the deficiency δ = n − ℓ − s (complexes, linkage classes, dimension of the stoichiometric subspace). The theorem as the article states it: a deficiency-zero network that is not weakly reversible has, for any kinetics, no positive equilibrium and no cyclic trajectory with all concentrations positive; a weakly reversible one, with mass-action kinetics, has exactly one positive equilibrium in each positive stoichiometric compatibility class, asymptotically stable, and no nontrivial positive cyclic trajectory. It mentions the global attractor conjecture as unproven.
2. **Correction to "Trigger".** The trigger said the theory predicts "oscillation, multistability, robustness" from structure. The theorem the article presents *rules out* multiple positive equilibria and positive oscillations for a class of networks, for every value of the rate constants; it does not predict that oscillations occur, and the article does not discuss robustness. The deficiency one theorem (the next chapter of Feinberg's book, not in the article) concerns multiple equilibria. The point that survives, and is the useful one for this idea: a structural integer computed by linear algebra decides a qualitative behavior for all parameters at once.
3. **A classic for avenue 3 (embed the behavior).** Ashby (1956), 6/8, gives the mechanical, electrical and mathematical forms of one second-order system as isomorphic, says that "no one of the three systems has priority; any can substitute for the others", and names the practice: solving a physics problem "is essentially that of using a map—of using a convenient isomorphic representation rather than the inconvenient reality" (`ashby1956introduction`, pp. 94 to 96). Avenue 3 is this idea with a learned map. It also says where the representation stops: an isomorphism "may hold only over a certain range" (p. 97).

Still open: no literature review yet for avenues 1, 2, 4, 5 and 6 (Lean premise selection, netlist and CAD embeddings, neural operators, learner-checker pairs). Feinberg's book is not held (no open copy found); bond graphs (Paynter 1961) are the classic for a domain-independent energy representation and should be searched for avenue 2 or 3.
