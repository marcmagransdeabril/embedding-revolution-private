# Idea 17: given a physical system, can we understand its function? (working notes, status: idea, not part of the book)

This file is idea 17 of [ideas.qmd](ideas.qmd); the Epilogue points to it from the section *Language, Thought and Translation*. Its sibling, idea 16 (how to embed the meaning of the formal sciences), is in [formal_sciences_meaning.md](formal_sciences_meaning.md). The two ideas share a testbed and a few sources but ask different questions. Two parts below, still called branches in the older entries. Iterate here before anything goes into a chapter or the roadmap in `index.qmd`.

Nothing below has been checked against `references/`. Claims about the literature are from search snippets or from memory and are marked (`[verify]`, "memory", or "found" with its limits in each section).

---

## Branch 1: a universal simulator that makes the learner's life harder (the testbed for this idea)

### The problem with domain simulators

SPICE exposes voltage and current. VHDL exposes logic levels and components. Modelica exposes typed ports. Each simulator hands the learner the variables, the ports, the units and the component vocabulary. The boundary and the state variables are already decided by a human, so the hardest part of understanding (what to measure, where the module edges are) is given away. A learner trained on SPICE traces has learned SPICE, not circuits.

### Requirement

A simulator whose raw observables carry no domain semantics, so the learner has to discover the variables, the modules and the function. Candidate properties:

- Observables are low-level and uniform: fields or particle states on a grid, not named signals.
- The same substrate can realize a circuit, a mechanism, a building, a reaction network.
- Human-meaningful concepts (voltage, force, logic level, port) are not in the API. They must be derived.
- Probes are free (measure anything, perturb anything), as in the Jonas & Kording setting.

### Candidates

| Substrate | What it gives | What it hides | Cost / catch |
|---|---|---|---|
| Continuum mechanics / FEM (general PDE solver) | Stress, displacement, heat, EM fields from geometry + materials | Components, ports | Circuits become a field problem (Maxwell); very expensive for large systems |
| Particle / molecular dynamics | Truly universal at one scale | Everything above atoms | Hopelessly far from function; scale gap |
| Cellular automata / lattice gas (e.g. Life, Wireworld, lattice Boltzmann) | Cheap, uniform, fully probe-able, computation exists | Domain vocabulary completely | Artificial; the "physics" is not our physics |
| Differentiable general-purpose physics engines (rigid bodies, MuJoCo/Brax-style) [verify] | Mechanisms, motors, linkages, bridges (as rigid or soft bodies) | Joint/actuator semantics if given only as raw state | Weak for electronics and chemistry |
| Multiphysics (COMSOL-like), or Modelica as a coupling layer | Coupled domains | Only if you strip the typed ports | Typed ports are exactly the semantics we want hidden |
| Bond graphs / port-Hamiltonian systems | A domain-independent energy-based formalism for electrical, mechanical, thermal, hydraulic systems (effort/flow pairs) | Domain-specific names | Already semantics-laden: effort and flow are a strong prior; useful as the *answer* representation, not the observation |

### Thoughts

1. There is probably no single simulator that is both universal and affordable. The choice is a tradeoff between realism and domain-neutrality.
2. A pragmatic design is a **two-layer experiment**: build systems in a rich domain simulator (SPICE, rigid bodies), then expose only a neutral observation interface (an array of anonymous time series with random labels and units removed). The learner never sees "V" or "I".
3. A stronger variant is **domain-randomized relabeling**: train across several simulators, with random linear mixing of observables, so that the only thing that transfers is structure. If the learner's embedding places a mechanical oscillator and an RLC oscillator together *despite* different observables, it has found something domain-independent.
4. Lattice or cellular-automaton substrates are the cleanest sandbox for a first experiment because they remove the human prior entirely, but they must be paired with at least one real-physics domain, or the result is only about toy worlds.

### Open questions

- Does the learner need to be told the observation is a "physics" system, or does that count as prior knowledge too?
- How is ground truth defined in a neutral simulator? The designer's hierarchy (modules, function) has to be recorded when the system is built.
- What is a fair comparison between a learner given neutral observables and one given SPICE-style semantic signals? The gap between them measures how much understanding is "supplied by the vocabulary".

---

## Branch 2: how do we understand a strange computing mechanism? (the method for this idea)

### Reading of the paper

Jonas & Kording show that the standard neuroscience toolkit (lesions, tuning curves, spike-word statistics, correlation) is applied *to a system whose answer we know* and fails to recover it. The deeper point is that neuroscience does not usually try to understand the brain as an alien computing mechanism. It runs descriptive analyses and hopes structure emerges. The implied question is whether there is a method that actually can do the job.

(Source: `tmp/new_references/chip.pdf`; I have read the first part only, up to the LFP section.)

### What would an actual method need to do?

Framed as the task: given an unknown system with full probing access, produce an explanation at Marr's computational, algorithmic and implementational levels.

1. **Find the boundary and interface.** What are the inputs, outputs, and state?
2. **Find the modules.** Weakly coupled substructures whose interventions have localized effects.
3. **Find each module's function.** An input-output description, ideally mapped to a known primitive (adder, register, oscillator, filter).
4. **Find the composition.** How modules combine into the whole: an algorithm.
5. **Find the purpose.** The least determined step. Needs a prior over what systems are *for*.

### Candidate approaches

- **Active experimental design, not passive recording.** The paper's methods are mostly observational or crude lesions. A learner that chooses probes (like active learning or a scientist designing experiments) could isolate single functions. This is the biggest gap in the paper's methods.
- **Program synthesis / reverse engineering.** Search for a short program that reproduces the observed behavior and aligns with the substrate (cf. automata learning, e.g. L* [verify], and program induction). Compression is the criterion.
- **Causal abstraction.** Find a coarse-grained model that commutes with interventions on the low-level system (Beckers & Halpern; Geiger et al. [verify]). Gives a precise test: the high-level explanation is right if intervening on it predicts intervening on the low level.
- **Learned structure plus symbolic read-out.** Embed low-level dynamics, cluster into modules, then fit symbolic descriptions (SINDy-style, symbolic regression) per module.
- **Mechanistic interpretability as the same problem.** Finding circuits in trained networks is an instance: a netlist (weights) is known, the function must be recovered. Connects this idea to the rest of the book.

### What the paper does not tell us

- Whether any of the above methods succeed on the 6502. The paper is a negative result for standard methods, not a test of better ones.
- Whether failure is about the methods or about the *data* (behavior from games is entangled). The authors say lesions would be cleaner with a single isolated function.

### Open questions

- What counts as "success"? Candidate: the recovered hierarchy aligns with the designer's hierarchy (module overlap) *and* supports repair and counterfactual tests.
- Is the embedding useful here, or only a convenient intermediate? One claim to test: a good embedding of subsystem behavior makes functionally equivalent modules (different transistor-level realizations of an adder) neighbors.
- How does this scale to the brain, where there is no designer's hierarchy to score against?

---

## How the two branches connect

Branch 1 designs the *testbed* (hide the human vocabulary). Branch 2 defines the *task and the methods* (recover modules and function). Together: a benchmark of increasingly complex systems in neutral observation form, scored against recorded ground-truth hierarchies.

## Next iteration

- [ ] Decide the first minimal testbed (proposal: a lattice-based or ODE-based simulator plus one SPICE-like circuit family, both exposed through the neutral interface).
- [ ] Read the remainder of Jonas & Kording and extract what they say they would do differently.
- [ ] Collect `[verify]` references into `tmp/new_references/` and check them against the ground-truth index.

---

## Iteration 2 (2026-11-17)

### Branch 1: cellular automaton (CA) as the universal substrate

Proposal: instantiate circuits and machines inside a CA; the learner sees only cell states.

- Pros: total domain-neutrality, cheap, deterministic, every cell probe-able, perturbation is trivial, ground-truth design is known because we built it.
- Known fact: some CAs are computationally universal (Game of Life, Wireworld, Rule 110), so circuits/machines can be embedded. Embedding a CPU in Life is possible but enormous (patterns of ~10^5-10^6 cells for simple machines [verify]).
- Catch 1: the embedding is a *compilation*. Wires, gates and clocks become glider streams or blocks; what the learner sees is the compiled form. That is a legitimate analogue of the transistor-to-function gap, but the compilation scheme is itself the vocabulary, and the learner might just learn it.
- Catch 2: CA "physics" has no energy, conservation laws or continuity, so results on mechanisms/bridges/natural systems need a second, continuous substrate (e.g. Lenia, lattice Boltzmann [verify]).
- Suggestion: use *several different compilations* of the same function (different CA rules, different gate encodings) so only the function is invariant across them.

### Branch 1: existing open-source general simulators (checked by search, not tested)

None is a universal "physics" simulator. They split by domain:

- Rigid/articulated bodies and contact: MuJoCo (open source, DeepMind), MJWarp, Newton (Linux Foundation, built on NVIDIA Warp), Genesis (multi-material, open source, released Dec 2024).
- Differentiable GPU frameworks: NVIDIA Warp, Taichi, JAX-based (Brax, JAX-MD) [verify].
- Continuum multiphysics (FEM): MOOSE, Elmer, FEniCS/DOLFINx, deal.II [verify]. These are the closest to "general": the same PDE machinery covers heat, elasticity, EM, fluids.
- CFD: OpenFOAM. EM: openEMS, Meep [verify]. Circuits: ngspice, Xyce. Modelica: OpenModelica.
- Closest to a universal substrate in spirit: a field/PDE solver on a grid, or particle-based (MPM in Taichi, which handles solids, fluids, snow in one framework).

### Branch 2: literature on discovery from first principles (first pass; SUPERSEDED by Iteration 3 below)

Found by search:
- Jonas & Kording 2014, "Automatic discovery of cell types and microcircuitry from neural connectomics" (arXiv 1407.4137). Unsupervised (non-parametric blockmodel) on connectomes; the abstract states it "automatically discovers the structure of a microprocessor". Closest direct precedent, but it works on the *wiring* (netlist), not on activity.

From memory, to check:
- Bongard & Lipson 2007 (PNAS), automated reverse engineering of nonlinear dynamical systems: active experiment selection (estimation-exploration). Directly addresses the "choose your probes" gap.
- Schmidt & Lipson 2009, distilling natural laws from data (symbolic regression); Brunton et al. SINDy; Udrescu & Tegmark, AI Feynman; Cranmer et al., symbolic models from deep learning.
- Iten et al. 2020, SciNet: discovering physical concepts with neural networks (latent variables that align with physical parameters).
- Liu & Tegmark and others: learning conservation laws / symmetries from data.
- Crutchfield et al., computational mechanics (epsilon-machines), including Hanson & Crutchfield on domains and particles in cellular automata: unsupervised discovery of the "intrinsic computation" of a CA. Very relevant to the CA testbed.
- Causal representation learning (Scholkopf et al. 2021); causal abstraction (Beckers & Halpern; Geiger et al.).
- Mechanistic interpretability and modularity: Filan et al. on clusterability of networks; circuit discovery in transformers. Same problem on a different substrate.
- Koopman / operator-based discovery of coherent modes; slot-based object discovery (Slot Attention) for unsupervised module/object discovery.

Gap (hypothesis, not established): most of these recover *equations or latent variables*, not *function/purpose* of a heterogeneous machine. I'm not aware of work that does all of: neutral observation, active probing, module discovery, function labeling. [verify by search before claiming this in the book].

---

## Iteration 3 (2026-11-17): literature review and book connection

Method and limits: about a dozen web searches; I read abstracts and snippets only, not full papers, and nothing here has been checked against `references/` or the ground-truth index. "Found" means the search returned the paper with the abstract saying what I attribute to it. "Memory" means I did not confirm it. It is a scoping review, not a systematic one, so "I found no work that..." means only that.

### A. Literature, grouped by what it contributes

**A1. The negative result and its follow-up (the premise)**

- Jonas & Kording, "Could a neuroscientist understand a microprocessor?", PLoS Comput Biol 13(1):e1005268, 2017 (preprint bioRxiv 2016). Found. Abstract: methods "reveal interesting structure in the data but do not meaningfully describe the hierarchy of information processing". I have read only the first part of the preprint (`tmp/new_references/chip.pdf`).
- Jonas & Kording, "Automatic discovery of cell types and microcircuitry from neural connectomics", arXiv 1407.4137 (eLife 2015, memory). Found. Unsupervised, run on the connectome (the wiring), and the abstract says it "automatically discovers the structure of a microprocessor". Closest precedent for unsupervised module discovery, but it takes the netlist as input and does not use activity or probing.
- Lazebnik, "Can a biologist fix a radio?", Cancer Cell 2002. Cited by the paper. Source of the "can you fix it" criterion of understanding.

**A2. Active experimentation and equation discovery**

- Bongard & Lipson, "Automated reverse engineering of nonlinear dynamical systems", PNAS 104(24):9943-9948, 2007. Found. Generates symbolic equations for a coupled nonlinear system from time series, "intelligently perturbing and destabilizing the system". Limits stated in the abstract: assumes ODEs and that the time series of *all* variables are observable. So it does active probing but assumes the variables are given.
- Schmidt & Lipson 2009 (symbolic regression, "Distilling free-form natural laws"), SINDy (Brunton et al. 2016), AI Feynman (Udrescu & Tegmark 2020). Memory; not searched. They need a candidate variable set.

**A3. Discovering the variables themselves**

- Iten, Metger, Wilming, del Rio, Renner, "Discovering physical concepts with neural networks", PRL 124, 010508 (2020), arXiv 1807.10300. Found. Encoder, bottleneck, decoder that answers questions; recovers the pendulum frequency, a conserved angular momentum, the number of degrees of freedom of a quantum state, and the heliocentric angles from Sun-Mars data. Small systems, one question at a time.
- Schölkopf et al., "Towards causal representation learning", arXiv 2102.11107 (2021). Found. Frames the problem as "discovery of high-level causal variables from low-level observations".
- Locatello et al., "Challenging common assumptions in the unsupervised learning of disentangled representations", ICML 2019, arXiv 1811.12359. Found. Shows theoretically that unsupervised disentanglement is "fundamentally impossible without inductive biases on both the models and the data". **This is the main theoretical warning for Branch 2:** a purely unsupervised discovery of the right variables is not identifiable; something (probes, interventions, an architectural prior) has to supply the bias.
- Locatello et al., "Object-centric learning with slot attention", arXiv 2006.15055 (2020). Found. Unsupervised object discovery in images. A candidate for "module discovery" if the observation is a spatial field (a CA grid).

**A4. Modularity and circuits, in networks and in hardware**

- Filan et al., "Neural networks are surprisingly modular" (arXiv 2003.04881) and "Clusterability in neural networks" (arXiv 2103.03386). Found. Define a module as strongly internally connected and weakly externally connected, and show that trained networks are more clusterable than random ones. Works on the weights (structure), as in the netlist case.
- Conmy et al., "Towards automated circuit discovery for mechanistic interpretability" (ACDC), arXiv 2304.14997. Found. Activation patching to find the subgraph responsible for a behavior. The behavior, dataset and metric are chosen by the researcher, i.e. the function is given and the circuit is found.
- Gate-level netlist reverse engineering in hardware security: GNN-RE (Alrahis et al., IEEE TCAD), ReIGNN (arXiv 2112.00806), GAMORA (arXiv 2303.08256). Found. Identify module boundaries and classify sub-circuits by function in netlists, GAMORA to 33 million nodes. They appear to be trained on labelled designs (supervised) [verify], and they work on structure, not on dynamics. This is the nearest existing engineering analogue of the proxy problem, and it is almost unknown outside hardware security.
- Hanson & Crutchfield, "The attractor-basin portrait of a cellular automaton", J Stat Phys 1992; Crutchfield & Hanson, "Computational mechanics of cellular automata" and "Turbulent pattern bases for cellular automata"; Crutchfield, Hanson & others on automated pattern detection (arXiv cs/0410017). Found. Identify the dominant regular domain of a CA, build a filter that locates defects, classify the particles, and derive an equation of motion for them: a description of the CA's "intrinsic computation" from space-time data. **Directly relevant to the CA testbed.** To check how automatic the procedure is.

**A5. Causal abstraction: the formal test of a high-level explanation**

- Beckers & Halpern, "Abstracting causal models", AAAI 2019. Found. Successively stricter definitions of when a high-level causal model is an abstraction of a low-level one, based on interventions.
- Geiger et al., "Causal abstractions of neural networks", NeurIPS 2021, arXiv 2106.02997, and "Causal abstraction: a theoretical foundation for mechanistic interpretability", arXiv 2301.04709. Found. Align high-level variables with low-level representations and verify with interchange interventions.
- Limit: the theory *tests* a proposed high-level model; it does not find one. And more than one high-level model can be a faithful abstraction, so "the" function is not unique.

**A6. Behavior learned without understanding; how to test for understanding**

- Clemens, "Learning device models with recurrent neural networks", arXiv 1805.07869 (2018). Found. RNNs imitate devices from input-output observation, up to a 16550 UART. Prediction without explanation.
- Weiss, Goldberg & Yahav, extracting automata from RNNs with L* (arXiv 1711.09576; authors from memory). Found. Query-based extraction of a minimal automaton from a black box. Finite-state only.
- Vafa et al., "Evaluating the world model implicit in a generative model", NeurIPS 2024, arXiv 2406.03689. Found. Metrics from the Myhill-Nerode theorem (sequence compression and distinction) show models can do well on their task and still hold an incoherent world model. A ready-made test of "does the model hold the right state structure".
- Vafa et al., "What has a foundation model found? Using inductive bias to probe for world models", arXiv 2507.06952. Found. Models trained on orbital trajectories "consistently fail to apply Newtonian mechanics when adapted to new physics tasks"; they behave as if they use task-specific heuristics. Evidence for the book that good prediction in a physics simulator does not imply recovery of the law.

**A7. Substrate for the testbed**

- Lenia (Chan, arXiv 1812.05433), neural cellular automata (review arXiv 2604.24990), "A path to universal neural cellular automata" (arXiv 2505.13058). Found. Continuous and learnable CA substrates.
- Minoza (2026 preprint), "Modularity, not integration, is the architectural basis of universal computation". Found as a preprint only. Claims universal computation in elementary CA arises from modular composition. If it holds, it would support the idea that modules are findable in a CA; not evaluated.

### B. What the review says about the gap

Separate abilities, each already done somewhere:

| Ability needed by the proxy problem | Closest existing work | What it assumes |
|---|---|---|
| Choose probes actively | Bongard & Lipson 2007 | ODE class; all variables observable |
| Discover the variables | SciNet; causal representation learning | Small systems; inductive bias (Locatello: unavoidable) |
| Find modules | Filan; GNN-RE/GAMORA; Jonas-Kording 2015 | Wiring or netlist given; GNN-RE supervised |
| Find intrinsic computation of a CA | Crutchfield et al. | CA space-time given; hand-guided domain filters (to check) |
| Verify an explanation | Causal abstraction (Geiger, Beckers-Halpern) | A hypothesis is supplied |
| Test for a coherent world model | Vafa et al. | A known ground-truth automaton |

Not found in this search: a single method that starts from neutral observations of a heterogeneous system, chooses its own probes, discovers the variables and the modules, and labels their function, scored against a known design hierarchy. That is the combination the proxy problem asks for. The claim is "not found in about a dozen searches", which is not the same as "does not exist"; before writing it in the book it needs a proper search (e.g. "reverse engineering" + "circuit" + "unsupervised", "automated scientific discovery" + "system identification", "compositional" + "program synthesis from traces").

Theory that bounds what any method can do:
- Rice's theorem (already in `symbols_without_interior.qmd`): no general procedure decides a non-trivial semantic property of an arbitrary program. Function can be recovered for restricted classes only.
- Identifiability (Locatello et al. 2019): unsupervised recovery of the right latent variables needs an inductive bias.
- Realization theory / minimal realizations (Kalman; memory, not searched): input-output data fix a system only up to equivalence.
- Causal abstraction: many high-level models can be faithful to the same low level system.

### C. Where this connects to the book

I read the roadmap in `index.qmd`, the epilogue's section headings, and grepped the chapters for related terms. I did not read the chapter bodies, so the fit for each chapter is judged from the roadmap paragraph.

| Chapter (status) | Fit | What it would take from this idea |
|---|---|---|
| **Epilogue** (idea) | **Best home for the thought experiment** | The Epilogue already keeps a register of thought experiments (the universal translator is one) and collects the answers of the dog test and the critical literacy test. The alien artifact fits as a third entry: it varies the *substrate* (a mechanism instead of the senses or a text) and asks what a representation of behavior keeps. Both thought experiments are about two systems with no shared vocabulary. It also fits the neuroscience and biology readings the Epilogue plans (Lazebnik, Jonas & Kording). |
| **symbols_without_interior** (definitive) | Strong, but a pointer only | Rice's theorem is already there as the reason that meaning (what a program does) cannot be read off its text. Jonas & Kording is the empirical counterpart: even with the full netlist and unlimited probes, standard analyses fail. Suggest a cross-reference from the Epilogue, not an edit to a definitive chapter. |
| **contextual_vectors** (idea) | **Best technical home for Branch 2's methods** | "Looking inside" a transformer is the same problem on a different substrate: weights are the netlist, behavior is the output. Circuit discovery, causal abstraction and modularity (A4, A5) belong here. |
| **neurosymbolic_integration** (idea) | **Best home for Branch 1 (formal knowledge)** | Lean, SPICE, Simulink and CAD as formal artifacts, the "LLM proposes, checker verifies" pattern, and the entailed / refuted / undetermined verdict of the critical literacy test. A circuit simulator is also a checker. |
| **graph_embeddings** (idea) | Strong for netlists | A netlist is a graph; GNN-RE and GAMORA are graph embeddings used for function identification; reaction networks are graphs. |
| **tangent_spaces_geodesics** (idea) | Good for "chemistry is geometry" | Symmetry and equivariance (rotations, E(3)) as what a representation should be invariant to; the substack article's idea in the book's terms. |
| **topological_deep_learning** (idea) | Possible | Reaction networks and Feinberg-style structure on complexes; I have not checked how closely chemical reaction network theory maps to cell complexes. |
| **cross_domain_transfer** (idea) | **Best home for the experiment** | The test "do an RLC oscillator, a chemical oscillator and a mechanical oscillator land together" is an alignment problem between spaces learned from different substrates, with an isometry ambiguity. The book's smoke tests are small experiments, so a CA or ODE testbed fits here. |
| **generative_spaces** (idea) | Moderate | Learned simulators, SciNet-style bottlenecks, and Vafa et al.'s evidence that prediction does not imply a recovered law. |
| curse_of_dimensionality, multimodal, VSA, complex_plane | Weak | No direct link found. |

Recommendation (author decides): keep this out of the roadmap as a new chapter for now. The cheapest consistent placement is
1. a thought experiment in the Epilogue, with working title "The Alien Circuit", tagged `{.idea}`;
2. a pointer from `neurosymbolic_integration` (formal artifacts) and from `contextual_vectors` (circuit discovery);
3. optionally, a small smoke test in `cross_domain_transfer` with a minimal CA or ODE testbed.

This keeps the book's scope (meaning as geometry) and its status convention, and a full chapter could be reconsidered if the experiment works.

Risks to flag:
- Scope creep: the book is about embeddings of meaning, and this idea is about function of mechanisms. The link is that "function" is the meaning of an artifact, but the book must make that claim and not assume it.
- The review is a scoping pass from abstracts. Nothing here is fit to cite until the papers are in `references/` and checked.
- The substack article (Feinberg's deficiency theorems) was read only to the representation section (the page was truncated at 8000 characters).

### D. Next steps

- [ ] Download the found papers into `tmp/new_references/` and run the ground-truth review on them (priority: Locatello 2019, Bongard & Lipson 2007, Geiger et al. 2023, Vafa et al. 2024/2025, Crutchfield-Hanson CA papers, GNN-RE).
- [ ] Do a focused search for the combination in section B.
- [ ] Read the rest of Jonas & Kording (LFP, dimensionality reduction, Granger causality, discussion).
- [ ] Decide placement (Epilogue thought experiment vs. chapter) and the first testbed.

---

## Iteration 4 (2026-11-17): impossibility results on unsupervised induction of function

Question: are there impossibility results on how much can be induced about the function of a system without supervision?

Method and limits: about seven further searches; abstracts and snippets only; nothing read in full or checked against `references/`. "Found" = a search result states it. "Memory" = not confirmed. Several statements below come from secondary summaries (marked) and must be checked against the primary source before the book cites them.

### A. Results found

| Result | What it says (as found) | Source | Relevance |
|---|---|---|---|
| **Gold 1967, identification in the limit** | Even the class of regular languages is not identifiable in the limit from positive data alone (finite families are). | Gold, *Information and Control* 10 (1967); statement found in a 2025 summary (arXiv 2511.05759), not in the primary text | Passive observation of positive examples is not enough for a rich class. |
| **Identification with traces (2026)** | Adds computational traces from the machine to Gold's paradigm; with perfect traces the class of all recursively enumerable languages becomes identifiable in the limit. | ICLR 2026 paper "Language identification in the limit with computational trace" (found by title; authors not captured) | The observation regime changes the result. Seeing inside the machine moves the problem from impossible to possible. Perfect traces are an idealization. |
| **Moore 1956, gedanken-experiments** | No finite sequence of input-output observations is sufficient to uniquely identify a finite-state machine; Ashby published similar results. | Moore, *Automata Studies* (1956); statement found in the introduction of arXiv 1201.3672, a secondary source | Black-box identification is only up to behavioral equivalence, and without a bound on the number of states no finite experiment rules out hidden states. Whether the experiment is possible with a known bound on the states: memory [verify]. |
| **Nonlinear ICA is not identifiable** | Without constraints, recovery of independent sources from a nonlinear mixture is non-identifiable (Hyvarinen & Pajunen 1999); extensions that use temporal structure or auxiliary variables restore identifiability (arXiv 1805.08651); recovery of quantized factors can be possible (arXiv 2306.16334, which states that identifiability of independent factors is impossible in the unsupervised i.i.d. setting under a general nonlinear map). | Hyvarinen & Pajunen 1999 (via a secondary summary); arXiv 1805.08651; arXiv 2306.16334 | The latent variables of a system cannot be recovered from passive i.i.d. data alone; extra structure (time, interventions, discreteness) can fix it. |
| **Locatello et al. 2019** | Unsupervised learning of disentangled representations is fundamentally impossible without inductive biases on both the model and the data. | arXiv 1811.12359, ICML 2019 | The same point for disentanglement. |
| **Causal hierarchy** | Observational data alone cannot predict the effects of interventions, even for an arbitrarily expressive neural net (arXiv 2107.00793); assumption-free causal inference is possible only in a meager set of structural causal models (Ibeling & Icard, arXiv 2107.08558). | arXiv 2107.00793 (authors from memory: Xia, Lee, Bengio, Bareinboim); arXiv 2107.08558 | Justifies active probing: recording a system passively cannot give its causal structure, so Jonas & Kording's setting (arbitrary experiments) is the favorable case, and a method that cannot work there cannot work with passive data. |
| **Non-identifiability of circuit explanations** | Experiments on small networks show "overwhelming evidence of non-identifiability": multiple circuits replicate the behavior, a circuit has multiple interpretations, several algorithms are causally aligned with the network. Empirical result, not a theorem. | Meloux et al., ICLR 2025 (arXiv 2502.20914) | Even with the full network and perfect interventions, the explanation of function is not unique. Another paper reports the same combinatorial explosion (2026 survey summary, not checked). |
| **No free lunch** | Averaged over a uniform distribution of problems, no learner beats another; no learner solves all problems. A paper ties it to Kolmogorov complexity and the role of inductive biases (arXiv 2304.05366); another says the theorem applies equally to meta-learning (arXiv 2609.34458, preprint). | Wolpert 1996 (memory); arXiv 2304.05366; arXiv 2609.34458 | Any learner needs a prior. The theorem averages over all targets, which is not a world anyone learns in (the Epilogue section *What Finite Data Cannot Fix* says the same). |
| **Query learning of black boxes** | Learning automata by queries (Angluin) is the standard black-box method; extracting Horn envelopes from a neural network in polynomial time is as hard as learning CNFs in polynomial time (arXiv 2305.12143). | Angluin 1987 (memory); arXiv 2305.12143 | Efficient exact learning has hard cases even with queries. Worst-case exponential time is stated for Horn envelopes. |
| **Rice's theorem; Kolmogorov and Solomonoff** | Already in the book (`symbols_without_interior.qmd`, and the Epilogue plan: Kolmogorov complexity is incomputable; Solomonoff's prediction is optimal and incomputable). | In the book | No general procedure decides a non-trivial semantic property of an arbitrary program, so function is recoverable only for restricted classes (bounded size, finite state, a declared hypothesis class). |

Memory only, not searched: structural identifiability in system identification (Bellman & Astrom 1970), Kalman's minimal realization theory, the cryptographic hardness of learning finite automata from random examples (Kearns & Valiant), Angluin's hardness results for membership queries alone, the Chaitin result that a formal system cannot prove high complexity.

### B. What these results say, grouped

1. **Equivalence-class limits.** Input-output behavior fixes a system only up to an equivalence class (Moore; realization theory; causal abstraction; non-identifiable circuits). "The function" must be defined modulo that class. This is not a failure of the learner. It also means a benchmark must score a recovered explanation against the *class* of faithful explanations, not against the designer's one hierarchy.
2. **Prior-dependence limits.** Gold, no free lunch, nonlinear ICA and Locatello et al. say that induction from passive unlabelled data needs a bias. "From first principles" cannot mean "without a prior"; it means a declared prior. Candidate priors that suit mechanisms: simplicity (short description), modularity (weak coupling between parts), sparsity of interactions, independence of causal mechanisms (Scholkopf et al.). Each should be stated and tested, since a method that "discovers" modules under a modularity prior has not shown modules exist.
3. **Observation-regime limits.** The same class of systems can be unlearnable from passive data and learnable with interventions or traces (causal hierarchy; Gold with traces). The proxy problem sits at the favorable end (unlimited probes, internal state visible). This makes it a fair test: failure there is not a data limit (Jonas & Kording's point), it is a method limit or a prior limit.
4. **Computability limits.** Rice's theorem rules out a general method for arbitrary programs; the claim to test is that a method works for a declared class (bounded size, a given substrate, a hierarchy of modules).

What I did not find: a theorem that covers the whole proxy problem (neutral observations of a heterogeneous mechanism, chosen probes, discovery of variables, modules and function). The pieces above bound each ability separately. The positive results (traces, interventions, auxiliary variables) suggest where progress is possible: more access, not more passive data.

### C. Consequences for the experiment design

- State the equivalence relation that defines "same function" (behavioral equivalence, bisimulation, or equivalence under interventions on declared ports) and score against it.
- Include negative controls: pairs of systems with different structure and identical behavior under the allowed probes, where a correct learner must report ambiguity, not pick one.
- State the prior of each method, and run each method on systems where the prior holds and where it fails (non-modular systems, densely coupled systems).
- Report the probe budget and the access level (passive, intervention, internal trace) as part of the result, since the theory says they change what is identifiable.
- Treat a method that finds an explanation as a hypothesis for the equivalence class, not as "the" explanation (Meloux et al.).

### D. Next steps (additions)

- [ ] Read the primary sources of the table, in this order: Moore 1956, Gold 1967, Locatello et al. 2019, the Ibeling-Icard and Xia et al. causal hierarchy papers, Meloux et al. 2025, the ICLR 2026 trace paper.
- [ ] Check the memory-only items before they are cited.

---

## Iteration 5 (2026-11-17): review against the sources

A review of iterations 1 to 4. The sources below are now held in `references/` (citekeys in `references.bib`, block "Ideas 16 and 17") and were checked with `ground_check.py` and by reading the pages named. Earlier iterations are left as written; this section corrects them where the sources disagree. Not held: Moore 1956 (read through Fields 2013), Gold 1967 (publisher download blocked; read through Peng et al. 2026), Lazebnik 2002, Bongard & Lipson 2007 (abstract only), Simon 1962, Feinberg 2019.

### A. Corrections to earlier iterations

1. **Jonas & Kording did not probe the chip actively.** "Our behavioral mechanisms are entirely passive"; they "just simulated booting" three games, and the only interventions were single-transistor lesions (`jonas2017could`, pp. 13 and 16 of the PLoS version). So iteration 4 B.3 ("the proxy problem sits at the favorable end ... failure there is not a data limit (Jonas & Kording's point)") overstates what they tested. Their point is about the *amount* of data ("the availability of unlimited data ... is in no way sufficient", p. 2), not about the kind of access. Whether active probing would succeed on the 6502 is open, and they say so: "Tasks that isolate one kind of computation would be needed" (p. 16).
2. **The proxy problem is their own proposal.** "It may be an important intermediate step for neuroscience to develop methods that allow understanding a processor. Because they can be simulated in any computer and arbitrarily perturbed, they are a great testbed" (p. 16). The earlier claim that our version is "the harder, open version" of their problem should credit them for proposing it. What remains new here is the ladder of heterogeneous systems, the neutral observation interface, and scoring against equivalence classes.
3. **Jonas & Kording 2015 found transistor types in one region, not "the structure of a microprocessor".** The arXiv abstract says it "automatically discovers the structure of a microprocessor"; the eLife abstract says it reveals "interesting structure" in it. The result is for a region containing the registers X, Y and S: types that "mirror the known structure", e.g. clocked transistors that retain state and a type that controls the registers' access to the data bus (`jonas2015automatic`, p. 11). Inputs are the wiring and the positions of the transistors.
4. **Moore's theorem is about finite experiments, not about equivalence classes.** Moore's second theorem, as quoted by Fields: "Given any machine S and any multiple experiment performed on S, there exist other machines experimentally distinguishable from S for which the original experiment would have had the same outcome" (Moore 1956, p. 140, via `fields2013bell`, p. 2). Finite observations put a lower bound on the size of the state space, never an upper bound. That belongs under limits of finite data (iteration 4 B.2), not under equivalence-class limits (B.1). The equivalence-class point has its own classic: Ashby (item B1 below).
5. **Locatello et al.'s impossibility is for i.i.d. observation.** Their setting is "where factors of variations are not observable at all, i.e. we only observe samples from P(x)" (`locatello2019challenging`, p. 3). It says nothing about a learner that intervenes, which is the proxy problem's setting. Hyvärinen & Pajunen's result is of the same kind: "if the space of mixing functions is not limited, there exists always an infinity of solutions"; with a conformal mixing in two dimensions the solution is unique up to a rotation (`hyvarinen1999nonlinear`, p. 2, OCR). Khemakhem et al. restore identifiability with an observed auxiliary variable (`khemakhem2020variational`, p. 3).
6. **Gold, read correctly, supports the access argument.** Gold's negative result is for positive data only (regular languages not identifiable from text; `peng2026language`, pp. 2 and 6). An experimenter who chooses inputs and sees outputs is closer to Gold's informant, for which richer classes are learnable in the limit (stated in secondary summaries; not checked against Gold's text). Peng, Saberi & Velegkas (ICLR 2026) prove that with perfect computational traces the recursively enumerable languages become identifiable in the limit (p. 1, Theorem 3.1 p. 13). The ICLR web abstract says "computable languages"; the PDF says recursively enumerable.
7. **The causal hierarchy is more specific than "passive data is not enough".** The Causal Hierarchy Theorem says the layers "almost never" collapse, in a measure-theoretic sense (`bareinboim2022pearl`, pp. 22 and 23). Ibeling & Icard's topological version concerns inferring counterfactuals from experimental or observational data (`ibeling2021topological`, pp. 1 and 2). Consequence for the testbed, my reading: a deterministic simulator that can be reset and replayed gives the experimenter the counterfactual layer directly (the same exogenous state, a different intervention), which no experiment on an animal can. The simulator is therefore more favorable than "unlimited probes" suggests, and a result in it does not transfer to a system that cannot be replayed.
8. **Meloux et al. is empirical, on Boolean functions and MLPs small enough to enumerate every candidate explanation** (`meloux2025everything`, p. 1). They also discuss dropping the demand for a unique explanation in favor of predictive or manipulability standards. Correct as stated in iteration 4.
9. **Goldblum et al. argue against the strong reading of no free lunch.** "Real-world problems disproportionately generate low-complexity data", neural networks share that preference, and one learner with a simplicity bias can serve "seemingly disparate problems" (`goldblum2024no`, p. 1). This is evidence *for* a general prior (simplicity) and against the claim that each system needs its own bias. Iteration 4 cited the paper only for the impossibility side.
10. **Hardware reverse engineering is supervised.** GNN-RE labels gates by sub-circuit class with GNNs trained on a generated, labelled dataset (`alrahis2022gnnre`, pp. 2 and 3); Gamora is multi-task node classification with labels (`wu2023gamora`, p. 4). Both work on the netlist, not on dynamics. Resolves the `[verify]` of iteration 3.
11. **Computational mechanics of CAs is partly by hand.** Domains are found "by inspection" in simple cases; complex patterns "require the automatic inference technique of ε-machine reconstruction" (`hanson1997computational`, p. 5). Resolves the "to check" of iteration 3.
12. **Small confirmations.** Weiss, Goldberg & Yahav (ICML 2018) is the L* paper; Clemens models six devices up to a 16550 UART (p. 3); Conmy et al. automate only the search for connections, with the behavior, metric and dataset chosen by the researcher (p. 1); Filan et al. define a module as "groups of neurons with strong internal connectivity but weak external connectivity" (p. 1); Vafa et al. 2024 is restricted to a reality "governed by a deterministic finite automaton" (p. 1); Vafa et al. 2025 report that orbital-trajectory models "consistently fail to apply Newtonian mechanics" on new tasks (p. 1).

### B. New evidence

**B1. A classic that states the problem (Lindy).** Ashby, *An Introduction to Cybernetics* (1956), chapter 6, "The Black Box" (`ashby1956introduction`). It poses the same problem, with the same examples:
- An engineer with a sealed box, inputs and outputs, "to deduce what he can of its contents"; the clinician who tests a patient with aphasia to deduce brain mechanisms (p. 86).
- "Let us make no assumptions at all about the nature of the Box and its contents, which might be something, say, that has just fallen from a Flying Saucer" (p. 87). This is the alien-artifact thought experiment, seventy years earlier.
- The questions: "What properties of the Box's contents are discoverable and what are fundamentally not discoverable?" and "What methods should be used if the Box is to be investigated efficiently?" (p. 87).
- The answer for a determinate box: the protocol of experiments identifies the mechanism "up to an isomorphism" and "cannot possibly be made to give more" (6/8, p. 94).
- The example: a spring, a wheel and a viscous trough are isomorphic to an inductance-resistance-capacitance circuit and to a second-order differential equation; "cover the central parts of the mechanism and the two machines are indistinguishable throughout an infinite number of tests" (pp. 95 and 96). This is the smoke test proposed in iteration 3 (do the oscillators of different substrates land together?).
- The digital computer "can be programmed to become isomorphic with any dynamic system whatever" (p. 96), which bears on Branch 1's question about a universal simulator.

**B2. A formal definition of reverse engineering, with an undecidability result.** Gurushankar & Grover, "A minimal intervention definition of reverse engineering a neural circuit" (arXiv 2110.00889, 2021), written in response to Jonas & Kording and Lazebnik. Their requirement: an agent that claims to have reverse-engineered a circuit must be able to give a minimal set of interventions that changes its input-output behavior to a desired one, under bounded rationality. Under assumptions on the model they show the goal is undecidable by reduction to Rice's theorem, and they give canonical systems where it can be done (p. 1). Iteration 4 said "a theorem that covers the whole proxy problem" was not found; this is a theorem for one formalization of it, and it must be read before that sentence is kept.

**B3. A counter-example with full access.** Marom et al. (2009): reverse engineering a neuro-system with a known mechanism, in a "static environment, primitive task and practically unlimited access to every piece of relevant information", gave "a perfectly valid but wrong induction of the system's design principle" (`marom2009precarious`, p. 1). This supports the equivalence-class warning with an experiment, and it is the strongest evidence against expecting success at the favorable end.

**B4. Prior art for the benchmark.**
- Geng, Chen, Arumugam & Griffiths (2025): LLMs reverse-engineering black-box programs, formal languages and equations from passive versus active data; passive observation plateaus below Bayesian inference, and intervening improves results (`geng2025large`, abstract). Direct evidence for the observation-regime point, at a small scale and with LLMs as learners.
- Gogleva et al., LUCA (arXiv 2611.03100, November 2026): a synthetic world with known ground truth, where agents learn unknown regulatory systems by budgeted experimentation, then predict interventions, diagnose faults and attempt rescues (Lazebnik's "fix it"). The authors' note on version 3 says its results "should not be relied upon pending correction"; the *design* is prior art, the numbers are not evidence.
- Haspel et al. (2023): argue that a complete state-dependent input-output description of C. elegans is now possible because every neuron can be perturbed and observed optically (`haspel2023time`, abstract).
- Brown (2014) retells the neuroscientists-and-computer parable (`brown2014tale`); a perspective, not evidence.

So the "not found" of iteration 3 B needs narrowing: benchmarks with known ground truth and budgeted experiments exist (LUCA, Geng et al.), with LLM agents and hand-given variables. Not found remains: neutral observations without the domain vocabulary, discovery of modules, and scoring against an equivalence class.

### C. What changes in the argument

- The question "what does it mean to understand a circuit?" has at least three formal answers in hand: up to isomorphism of the canonical representation (Ashby 1956), causal abstraction that commutes with interventions (Beckers & Halpern 2019; Geiger et al.), and minimal interventions that achieve a target behavior (Gurushankar & Grover 2021, Lazebnik's "fix it" made formal). The idea should choose among them or compare them, not invent a fourth.
- The impossibility results split into two families that the earlier text mixed: limits of finite or passive data (Moore, Gold on text, nonlinear ICA, Locatello, the causal hierarchy), which access can relax; and limits that access cannot relax (equivalence up to isomorphism, Ashby; non-unique explanations, Meloux et al. and Marom et al.; undecidability for unrestricted classes, Rice and Gurushankar & Grover).
- Three Epilogue sections already plan the philosophical side: *What Finite Data Cannot Fix* (Hume, Goodman, Kripke, no free lunch), *Does Structure Fix Meaning?* (Newman: structure only up to isomorphism, which is Ashby's result for machines) and *What a System Cannot Say About Itself* (Rice). The new paragraph should point to them and not restate them. Its own contribution is the access axis (passive, intervention, replay, trace) and the engineering classic (Ashby), which no section has.

### D. Next steps (replace iteration 4 D)

- [ ] Read Gurushankar & Grover in full (assumptions of the undecidability result; the canonical systems where it works).
- [ ] Read Ashby chapter 6 to the end (6/9 to 6/20: homomorphisms and the lattice of simplifications, which is the coarse-graining of causal abstraction) and S.13/15 (how much information a Black Box can give).
- [ ] Find an open copy of Moore 1956 and of Gold 1967, or ask the author for them.
- [ ] Decide the definition of understanding (C, first bullet) before the testbed.
