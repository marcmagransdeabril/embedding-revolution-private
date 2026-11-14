---
name: review-code
description: "Review the solution scripts in code/<chapter>/ against the book section they belong to: formulas, notation, constants and printed numbers must agree with the text, the code must be modular and readable, use the fewest dependencies (standard library, then numpy, then pytorch where deep learning needs it), and be wired into the Makefile so that a change re-runs what depends on it. Use when: a script or the section it implements was written or changed, checking that text and code still agree, auditing imports and dependencies, adding or changing shared helpers (utils.py) and their unit tests, or checking that a change re-runs the right scripts."
---

# Code Review

Review of the scripts of `code/<chapter>/*.py` as the executable half of the book. A script exists to make a claim of the chapter checkable; this review checks that it still does.

## Scope

Fix the scope first, as in `review-doc` (Step 0): one script, one section with its scripts, a chapter, or the whole `code/` tree; and the range (uncommitted changes, last commits, since a ref, or full). A change of a script is reviewed together with the section that names it, and the reverse.

## Mechanical checks (run first)

```bash
make check-code          # unit tests of the shared helpers, then the findings below
```

`scripts/code_deps.py check` reports:
- a script imports a package outside the allowed list: `numpy`, `matplotlib` (figures), `sklearn` (the bundled digits only), `torch` (deep learning);
- a chapter names a `name.py` that does not exist;
- a file of `code/<chapter>/data/` that no script names (unused), or a script that names a data file that is not there (a member of a zip counts as there);
- the Makefile does not give a script exactly the prerequisites that its imports and data files imply. The Makefile is asked with `make -pn`, so it is the rules `make` really uses that are compared, not the generator.

Scripts are named after the section they belong to (`contrast_*.py`, `counting_*.py`), and a chapter does not have to name each one.

`make -n test-code` lists the scripts that a change would re-run (§ Wiring).

## Review procedure

1. **Map text to code.** Find the section that names the script (`grep -n "name.py" chapters/*.qmd`) and read both. List what the text states and the code must reproduce: the formulas, the notation, the constants (dimension, step size, number of seeds, $k$, ...), the numbers quoted in the text and the figures.
2. **Formulas.** Each formula of the section appears in the code once, with the same symbols or an obvious map, kept in a comment next to it (`lam` for $\lambda$, `K` for $k$). Check signs, normalizations, the base of the logarithm, `axis` of every sum and mean, and the shape of every array against the text. A change of convention in one place (e.g. $z$ renamed $\lambda$) is a change in the code, its comments and its docstring too.
3. **Constants and numbers.** Every number of the text that the script computes is printed by the script, and the script asserts the claim that the text makes about it (as `contrast_toy_nce.py` does for its figures). A number in the text that no script prints is a finding. Run the script (`make test-code`) and compare the output with the text, not the other way round.
4. **Modularity.** One idea per function, the function names and the docstring say what the text says; the top of the file says which section and question it implements, what it prints and what it saves. No function longer than a screen. Shared pieces live once, in `utils.py` of the chapter or in the script that owns them (and are imported, not copied); a script imported by another is treated as a library.
5. **Simplicity and dependencies.** Prefer the standard library, then `numpy`, then `pytorch`. A loop that reads like the formula beats a vectorized one that does not, unless the cost matters for the claim. Flag a new dependency, a framework where numpy does, and any code that is there "in case".
6. **Reproducibility.** Fixed seeds, fixed data (in the repository, or pinned by a SHA-256 that the code verifies), paths relative to the script, no network, no timings that decide a result (a timing is printed, never asserted tightly).
7. **Tests.** A helper used by more than one script has unit tests with a known answer (`scripts/tests/test_utils.py`). A new helper without a test is a finding.

## Wiring in the Makefile

- `make test-code` re-runs a script when it changes, when `utils.py` changes, or when a module it imports changes (transitively). The import rules are generated from the `import` statements by `code_deps.py make-deps` into `.code-tests/deps.mk`, which `make` rebuilds by itself. Nothing has to be maintained by hand.
- `make book` runs the unit tests of the helpers first, then the scripts, then renders.
- Only imports of modules in the same chapter directory are followed.
- Data files are dependencies too: a file of `code/<chapter>/data/` whose name appears as a string in a script or in a module it imports (`Path(__file__).parent / "data" / "pride_and_prejudice.zip"`) is a prerequisite of that script, so changing the file re-runs it. Keep the file name as a literal string in the code, so that the link can be found.
- Data that is not in the repository (downloaded, or bundled with a package) is not a file to track. Pin it with a SHA-256 that the code checks before use, as `utils.load_book()` does; a mismatch stops the script.

Beyond the dependencies, a change is safe when the scripts assert the claims of the text (they run again when something they use changes, and fail if a claim no longer holds), when the unit tests of the helpers pass, and when `make check-code` has no new finding.

## Findings

For each finding: file and line (of the script and of the section), what the text says, what the code does, the fix. Severity `blocker` when text and code disagree on a formula, a convention or a number, `major` for a missing assertion or test, an unneeded dependency or a copy of shared code, `minor` for readability. Commit fixes in a separate `review-code:` commit, as `review-doc` does.
