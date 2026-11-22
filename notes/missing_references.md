# Missing references

PDFs that could not be found as open copies. Save each one in `references/` as `YYYY_surname_firstwords.pdf`, set `file = {...}` in `references.bib` and run `.venv/bin/python .github/skills/ground-truth-review/scripts/fetch_references.py` to refresh the ground-truth index. Until then a claim that cites them is "unverifiable locally", not wrong.

## Classics (philosophy, logic, language)

| Author | Year | Title | Citekey | Note |
|---|---|---|---|---|
| Frege, Gottlob | 1918 | Der Gedanke (English: "The Thought", Mind 1956) | not yet in the bib | Thoughts and the third realm |
| Frege, Gottlob | 1891 | Funktion und Begriff (English: "Function and Concept") | not yet in the bib | |
| Frege, Gottlob | 1950 | The Foundations of Arithmetic, translated by J. L. Austin | `frege1884grundlagen` | Only the German original of 1884 is held; the context principle is quoted in English |
| Saussure, Ferdinand de | 1916 | Cours de linguistique générale | `saussure1916cours` | Cited in `properties_of_meaning` and the epilogue |
| Saussure, Ferdinand de | 1959 | Course in General Linguistics, translated by W. Baskin | `saussure1916cours` | English edition, if the French one stays missing |
| Aristotle | c. 350 BC | Categories (translation by E. M. Edghill, 1926) | not yet in the bib | Archive.org has only a text file |
| Peirce, Charles S. | 1931–1958 | Collected Papers of Charles Sanders Peirce | `peirce1931collected` | `chance_love_and_logic` (1923) is held instead, with two of the essays |
| Whorf, Benjamin Lee | 1956 | Language, Thought, and Reality: Selected Writings | `whorf1956language` | |
| Kripke, Saul A. | 1982 | Wittgenstein on Rules and Private Language | `kripke1982wittgenstein` | |
| Goodman, Nelson | 1955 | Fact, Fiction, and Forecast | `goodman1955fact` | |
| Putnam, Hilary | 1981 | Reason, Truth and History | `putnam1981reason` | |
| Grice, H. P. | 1957 | Meaning (The Philosophical Review 66) | `grice1957meaning` | Not cited in any chapter yet |
| Montague, Richard | 1970 | Universal Grammar (Theoria 36) | `montague1970universal` | |
| Lewis, David | 1970 | General Semantics (Synthese 22) | not yet in the bib | Possible-worlds semantics |
| Austin, J. L. | 1962 | How to Do Things with Words | not yet in the bib | |
| Husserl, Edmund | 1900–1901 | Logische Untersuchungen | not yet in the bib | |
| Hume, David | 1739 | A Treatise of Human Nature | not yet in the bib | Only the Enquiry (1748) is held |
| Hobbes, Thomas | 1651 | Leviathan | not yet in the bib | Public domain; copies exist on Archive.org but were not fetched |

## Other bib entries without a PDF

Entries with an empty `file` field that I did not try to fetch, because they are not classics of meaning or logic. Run `fetch_references.py --dry-run` for the current list.

- Chomsky, 1957, Syntactic Structures; 1959, A Review of B. F. Skinner's Verbal Behavior; 1963, The Algebraic Theory of Context-Free Languages; 1965, Aspects of the Theory of Syntax; 1968, The Sound Pattern of English; 1980, Rules and Representations; 1981, Lectures on Government and Binding; 1986, Knowledge of Language; 1995, The Minimalist Program
- Jakobson, 1952, Preliminaries to Speech Analysis; 1956, Fundamentals of Language
- Hauser, Chomsky and Fitch, 2002, The Faculty of Language
- Berwick and Chomsky, 2016, Why Only Us
- Norvig, 2011, On Chomsky and the Two Cultures of Statistical Learning
- Miller and Chomsky, 1963, Finitary Models of Language Users
- Nagel, 1974, What Is It Like to Be a Bat?
- Chalmers, 1995, Facing Up to the Problem of Consciousness
- Polanyi, 1966, The Tacit Dimension
- Newman, 1928, Mr. Russell's "Causal Theory of Perception"
- Du Bois-Reymond, 1872, Über die Grenzen des Naturerkennens; Hilbert, 1930, Naturerkennen und Logik
- Kolmogorov, 1965, Three Approaches to the Quantitative Definition of Information
- Minsky and Papert, 1969, Perceptrons
- Gold, 1967, Language Identification in the Limit
- Moore, 1956, Gedanken-Experiments on Sequential Machines
- Good, 1953, The Population Frequencies of Species
- Simon, 1962, The Architecture of Complexity
- Tversky and Kahneman, 1974, Judgment under Uncertainty
- Nisbett and Wilson, 1977, Telling More than We Can Know
- Knight, 1921, Risk, Uncertainty and Profit
- Mac Lane, 1971, Categories for the Working Mathematician
- Thom, 1975, Structural Stability and Morphogenesis
- Eco, 1984, Semiotics and the Philosophy of Language
- Priest, 2002, Beyond the Limits of Thought; Franzén, 2005, Gödel's Theorem
- Nagarjuna, 1995, The Fundamental Wisdom of the Middle Way
- Benjamin, 1923, Die Aufgabe des Übersetzers; Steiner, 1975, After Babel
- Taleb, 2020, Statistical Consequences of Fat Tails
- Lazebnik, 2002, Can a Biologist Fix a Radio?
- Bongard and Lipson, 2007, Automated Reverse Engineering of Nonlinear Dynamical Systems
- Feinberg, 2019, Foundations of Chemical Reaction Network Theory
- Swift, 1726, Gulliver's Travels; Carroll, 1871, Through the Looking-Glass; Calvino, 1986, The Uses of Literature; Moretti, 2005, Graphs, Maps, Trees
- Krishnamurti, 1999, The Limits of Thought
- Queen, 2026, The Shelf Life of LLM Findings

## Held, but with a caveat

| Citekey | Held | Caveat |
|---|---|---|
| `tarski1944semantic` | 12-page excerpt from the "Theories of Truth" reader | May not be the complete paper |
| `wittgenstein1922tractatus` | Nordic Wittgenstein Review tree-structured edition | Check that the English text is Ogden's translation |
| `godel1931formal`, `tarski1944semantic`, `davidson1974very` | Copies hosted on university course pages | Replace by the publisher's version if one is available |
| `carnap1928aufbau` | Archive.org scan of the German original | Copyright status not checked |
| `kant1781critique`, `frege1879begriffsschrift`, `carnap1928aufbau`, `bacon1620novum` | Scans OCRed with English-only Tesseract | German and Latin text is noisy; confirm quotations by rendering the page |
