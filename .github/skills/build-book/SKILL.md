---
name: build-book
description: "Build, render, export, validate, and format the multi-chapter book in standard publishing formats (O'Reilly 7x9.1875in, HTML, EPUB) from chapters/*.qmd. Use when: building or rendering the book, generating PDF/HTML/EPUB, adding new chapters, syncing book chapter registry, validating chapter markdown/math/references/citations, or configuring book styling."
---

# Build Book

Automated build system and publishing pipeline for *The Embedding Revolution*, generating production-grade books in the O'Reilly 7in $\times$ 9.1875in print trim size, multi-page HTML, and EPUB from Quarto markdown (`.qmd`) chapter files.

## When to Invoke (Triggers)

Invoke this skill whenever:
- **Building / Rendering the Book**: Generating the complete book in PDF (O'Reilly), HTML website, or EPUB format.
- **Adding or Renaming Chapters**: Adding new chapter drafts into `chapters/` and synchronizing the chapter outline into `_quarto.yml`.
- **Pre-flight Validation & Linting**: Checking chapter frontmatter, math syntax (`$$`), balanced callout divs (`:::`), Python code chunks, figure labels, cross-references, and `@citekey` citations against `references.bib`.
- **Styling & Layout Customization**: Adjusting the publisher geometry, LaTeX preamble, Lua filters, or HTML theme styles.
- **Exporting Standalone Artifacts**: Creating distribution builds for reading, review, or print.

---

## Environment & Prerequisites

The build pipeline leverages Quarto, TinyTeX (XeLaTeX), Pandoc, and the project Python virtual environment (`.venv`):

* **Python Virtual Environment**: `.venv/bin/python` provides the Python kernel and data science libraries (NumPy, SciPy, Matplotlib, PyTorch, etc.) for executing interactive code chunks.
* **Quarto**: Quarto CLI (v1.5+) drives multi-format document rendering and book orchestration, and resolves `@citekey` citations against the `bibliography: references.bib` entry in `_quarto.yml`.
* **TinyTeX / XeLaTeX**: LaTeX engine located at `~/.TinyTeX/bin/x86_64-linux` for high-precision book typography and mathematics.
* **Pandoc**: Built-in document conversion engine with custom Lua filters.

---

## Publishing Formats & Trim Sizes

| Format | Target | Trim Dimensions | Geometry & Margins | Layout Characteristics |
| :--- | :--- | :--- | :--- | :--- |
| **O'Reilly Standard** | `pdf` | **7.0in $\times$ 9.1875in** (178mm $\times$ 233mm) | Inner: 0.85in, Outer: 0.75in, Top: 0.80in, Bottom: 0.85in | Distinctive O'Reilly dark red / charcoal palette, accent horizontal rules, left-border callout bars, framed code listings. |
| **Interactive Web Book** | `html` | Responsive | Flexible multi-column | Dark/light theme toggle, interactive collapsible code blocks, MathJax math, search, sidebar navigation. |
| **E-reader** | `epub` | Dynamic e-reader | Reflowable text | EPUB 3 standard, MathML equations, structured navigation. |

---

## Quick-Start Commands (Makefile)

The repository root includes a comprehensive `Makefile` wrapping all build operations:

```bash
# Build complete book (HTML + PDF)
make book

# Build PDF (O'Reilly 7in x 9.1875in)
make pdf

# Build HTML web book or EPUB
make html
make epub

# Pre-build validation and chapter synchronization
make validate           # Audit chapter markdown, math, code syntax, and citations
make validate-citations # Audit only @citekey citations against references.bib
make sync-chapters      # Auto-discover chapters/*.qmd and update _quarto.yml
make sync-solutions     # Regenerate chapters/solutions.qmd from the answers blocks in each chapter
make test-code          # Run the solution scripts in code/ that changed; a script whose first line is `# SKELETON` is listed and skipped

# Live editing preview server
make preview

# Clean build outputs
make clean
```

---

## Python Build Automation Scripts

Located in `.github/skills/build-book/scripts/`:

### 1. `build_book.py` — Master Build Orchestrator
Drives the entire build lifecycle with automatic environment variable injection (`QUARTO_PYTHON`, `PATH`):

```bash
# Build default PDF (O'Reilly)
.venv/bin/python .github/skills/build-book/scripts/build_book.py --format pdf

# Build all formats (HTML, PDF, EPUB)
.venv/bin/python .github/skills/build-book/scripts/build_book.py --format all

# Fast draft build (skip re-executing Python code cells)
.venv/bin/python .github/skills/build-book/scripts/build_book.py --format pdf --no-execute

# Preview commands without executing
.venv/bin/python .github/skills/build-book/scripts/build_book.py --dry-run --format all
```

**Key Arguments**:
- `--format, -f`: `pdf`, `pdf-oreilly`/`oreilly`, `html`, `epub`, `all`.
- `--clean, -c`: Remove previous `_book`, `_freeze`, and temporary files before building.
- `--no-execute`: Render using cached code cell outputs.
- `--no-sync`: Skip automatic chapter registry synchronization.
- `--no-validate`: Skip syntax, math, and citation validation.

### 2. `sync_chapters.py` — Dynamic Chapter Registry
Scans `chapters/*.qmd`, maps files to the canonical Parts I–IV + Epilogue structure, and updates `_quarto.yml`:

```bash
.venv/bin/python .github/skills/build-book/scripts/sync_chapters.py --verbose
```

### 3. `sync_solutions.py` — Solutions Generator
Collects the `::: {.answers}` blocks written inside each chapter (right after the matching `::: {.questions}` block) and generates the back-matter file `chapters/solutions.qmd` in book order. The Makefile runs it before every render; `--check` only reports whether the file is current:

```bash
.venv/bin/python .github/skills/build-book/scripts/sync_solutions.py          # regenerate
.venv/bin/python .github/skills/build-book/scripts/sync_solutions.py --check  # exit 1 if stale
```

### 4. `validate_book.py` — Pre-flight Quality Auditor
Audits `index.qmd` and all chapter `.qmd` files for structural correctness:

```bash
.venv/bin/python .github/skills/build-book/scripts/validate_book.py --verbose

# Citation checks only touch one file (no corpus-wide orphan detection)
.venv/bin/python .github/skills/build-book/scripts/validate_book.py --file chapters/embedding_spaces.qmd

# Skip citation validation entirely
.venv/bin/python .github/skills/build-book/scripts/validate_book.py --no-citations
```

**Checks Performed**:
1. **Frontmatter**: Non-empty `title` (in the front matter, or as the level-1 heading `# Title {#sec-ch-<stem>}`; both is a warning), valid YAML delimiters.
2. **Callouts**: Perfectly balanced `:::` container blocks.
3. **Executable Code**: Valid Python syntax within ````{python}`` blocks.
4. **Display Math**: Balanced `$$` delimiters and valid LaTeX math environments.
5. **Section Breaks**: `{{< pagebreak >}}` used instead of `---` horizontal rules between parts/chapters/special sections.
6. **Citations**: Every `@citekey` resolves against `references.bib`; no orphan bib entries; `file =` paths exist under `references/`; no legacy hand-numbered `## References` lists (gated by `--citations`/`--no-citations`, default on).
7. **Review questions and solutions**: every `::: {.questions}` block is followed immediately by a `::: {.answers}` block with the same number of items, and the generated `chapters/solutions.qmd` is up to date.
8. **Chapter references**: no literal `Chapter N` or `Chapters N to M` outside code (warning); see "Referring to chapters" below.

---

## Chapter Authoring Guide

### File Placement and Naming
Place new chapters in `chapters/`:
- `chapters/properties_of_meaning.qmd` (Chapter 1)
- `chapters/curse_of_dimensionality.qmd` (Chapter 2)
- `chapters/symbols_without_interior.qmd` (Chapter 3)
- `chapters/embedding_spaces.qmd` (Chapter 4)
- `chapters/generative_spaces.qmd` (Chapter 5)
- `chapters/contextual_vectors.qmd` (Chapter 6)
- `chapters/vector_databases.qmd` (Chapter 7)
- ... (the numbers are those of `_quarto.yml`; in the text, refer to chapters by label, see "Referring to chapters")

Run `make sync-chapters` to automatically register newly added files into `_quarto.yml`.
The file-to-chapter mapping lives in `MASTER_PARTS` in `scripts/sync_chapters.py`:
a file goes to the first chapter whose pattern is a substring of its filename
stem or its title, so keep patterns specific.

### Referring to chapters
Never type a chapter number: the numbers follow the order of `_quarto.yml`, so an inserted, merged or dropped chapter renumbers the book by itself.
- The label of a chapter is `sec-ch-` plus its file stem with `-` for `_`: `chapters/embedding_spaces.qmd` is `@sec-ch-embedding-spaces`.
- `@sec-ch-embedding-spaces` renders "Chapter 3". After the word "Chapters", write `[-@...]`, which renders only the number: `Chapters [-@sec-ch-vector-databases] to [-@sec-ch-multimodal-embeddings]` gives "Chapters 4 to 13". Write a reference alone (no prefix, suffix or other citation inside the brackets).
- A roadmap entry in `index.qmd` is `* **@sec-ch-<stem>: Title.** *(status)*`; `make status` reads the tag by the label and checks that the roadmap lists the chapters in the order of `_quarto.yml`.
- Why a filter: in HTML, Quarto 1.5 renders a chapter reference in a page without a chapter number (`index.qmd`, the epilogue, `solutions.qmd`) as "3 Title" and ignores `[-@...]` (quarto-dev/quarto-cli#14132). `filters/book-chapter-refs.lua` resolves every `@sec-ch-*` itself in HTML and stops the build on an unknown label; PDF and EPUB are left to Quarto. Delete the filter when Quarto fixes the bug (the text diff of the renders shows whether it still matters). Do not reference *sections* (`@sec-prop-...`) from those three pages in HTML: the same bug applies and the filter does not cover them.
- An unresolved label in PDF or EPUB is only a warning in Quarto; `make pdf`/`make epub` search the log (`.quarto/render-<format>.log`) and fail.

### Chapter Frontmatter & Structure
A chapter keeps `status:` (and `open:`) in the YAML frontmatter and gives its title as the labelled level-1 heading:

```markdown
---
status: idea
---

# The Anatomy of Embedding Spaces {#sec-ch-embedding-spaces}

::: {.callout-note}
## The Geek's Epiphany
Knowledge is a continuous, high-dimensional geometric vector.
:::
```

### Callouts and Special Blocks
* Standard callouts: `::: {.callout-note}`, `::: {.callout-tip}`, `::: {.callout-warning}`, `::: {.callout-important}`.
* Custom Geek callouts: `::: {.callout-note appearance="simple"}` with `## The Geek's Epiphany` or `## The Geek's Lens`.

### Section and Chapter Breaks
* **Page Breaks**: Parts, chapters, and special unnumbered sections (`Prologue`, `Disclaimer`, `Acknowledgments`, `References`, `Mathematical Notation`, `Code & Computational Environment`) must be separated by `{{< pagebreak >}}` rather than horizontal rules (`---`).
* In PDF/LaTeX, Quarto converts `{{< pagebreak >}}` to `\newpage` / `\clearpage`.
* In HTML and EPUB, `{{< pagebreak >}}` inserts standard CSS page breaks (`break-after: page;`).

### Citations and Bibliography
All citations resolve against the single repository-root `references.bib`, declared via `bibliography: references.bib` in `_quarto.yml`. Do not hand-number references — every chapter's reference list is generated by Pandoc from `references.bib`.

* **Citekey convention**: `surnameYYYYfirstword`, lowercase, no punctuation (e.g. `mikolov2013efficient`, `levy2014neural`). Disambiguate collisions with a trailing letter (`levy2014neurala`).
* **Required fields**: standard bibliographic fields (`author`, `title`, `year`, plus venue-specific fields) **plus one project-specific field** (no chapter numbers or topic tags: chapters get renumbered, and which chapter cites what is derived from the text):
  - `file =` — path to the PDF in `references/` when a local copy is held (empty `{}` otherwise). This is the join key `ground-truth-review` uses to go from citekey → PDF → page evidence.
  - Add `doi` or `arxiv` wherever one exists.
* **Citation style in prose**: default to narrative or parenthetical Pandoc citations (`@levy2014neural showed that…` / `…implicit matrix factorization [@levy2014neural]`). **Locators are mandatory for any specific claim** (theorem, number, benchmark): `[@levy2014neural, p. 2180]`.
* Keep inline citations sparse; push breadth into an end-of-chapter **Further Reading** section (prose + citekeys).
* End each chapter with:
  ```markdown
  {{< pagebreak >}}

  ## Further Reading {.unnumbered}

  …short prose pointers using @citekeys…

  ## References {.unnumbered}

  ::: {#refs}
  :::
  ```
  The `::: {#refs}` div is where Pandoc injects the generated bibliography.
* Run `make validate-citations` after adding or editing citations — it catches unresolved `@key`s, orphan bib entries, broken `file =` paths, and any backsliding into a hand-numbered reference list.

---

## Ancillary Architecture & Customization

```text
├── _quarto.yml                  # Master Quarto book configuration (incl. bibliography: references.bib)
├── references.bib               # Single BibTeX database for the whole book
├── references/                  # PDF corpus used by ground-truth-review (NOT the same as references.bib)
├── index.qmd                    # Book Welcome, Preface, & Table of Contents
├── Makefile                     # Root build automation targets
├── filters/
│   ├── book-callouts.lua        # Callout box transformation filter
│   ├── book-questions.lua       # Review questions: auto-numbering + question<->solution links
│   └── book-typography.lua      # Typographic non-breaking space & quote filter
├── styles/
│   ├── oreilly-preamble.tex     # O'Reilly LaTeX geometry, rules, code frames
│   ├── book-theme.scss          # Modern responsive HTML web book SCSS
│   ├── epub.css                 # EPUB stylesheet
│   └── book.typ                 # Custom Typst book template
└── .github/skills/build-book/
    ├── SKILL.md                 # Skill definition and instructions
    └── scripts/
        ├── build_book.py        # Master build driver
        ├── sync_chapters.py     # Dynamic chapter discovery
        ├── sync_solutions.py    # Generates chapters/solutions.qmd from the chapters' answers blocks
        └── validate_book.py     # Markdown/math/code/citation auditor
```

---

## Review Questions & Solutions

Same markup and numbering as the little-book. Put 2–3 questions at the end of each section as an ordered list inside `::: {.questions}`, and write the solutions **right below them**, in the same chapter file, as an ordered list inside a plain `::: {.answers}` block (same number of items, same order, only blank lines between the two blocks):

```markdown
::: {.questions}
1. First question.

2. Second question.
:::

::: {.answers}
1. First solution.

2. Second solution.
:::
```

Questions are numbered `<chapter>.<n>` automatically (cumulative per chapter). The colocated `.answers` blocks are authoring source only: `filters/book-questions.lua` removes them from the chapter, so the reader never sees them inline. `sync_solutions.py` (`make sync-solutions`, run automatically before every render) gathers them in book order into `chapters/solutions.qmd` (listed last in the book, unnumbered) with one `::: {.answers ref="<chapter-file-stem>"}` block per chapter. **`chapters/solutions.qmd` is generated: never edit it by hand.** The filter then adds the per-chapter headings in the solutions and the links between each question and its solution (HTML, EPUB, PDF). `make validate` fails if a questions block lacks its answers block, the item counts differ, `ref=` is used outside the generated file, or `solutions.qmd` is stale.

---

## Troubleshooting & Recovery

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `ModuleNotFoundError: No module named 'matplotlib'` | Code cell executed without virtual environment packages | Run `.venv/bin/pip install -r requirements.txt` or execute through `build_book.py` / `Makefile` which automatically sets `QUARTO_PYTHON`. |
| `! LaTeX Error: File 'fvextra.sty' not found` | First-time LaTeX package fetch | Let TinyTeX download packages via `tlmgr` automatically, or ensure `PATH` contains `~/.TinyTeX/bin/x86_64-linux`. |
| `Unclosed ':::' block` | Missing closing delimiter in chapter markdown | Run `make validate` to locate the exact file and line number. |
| `Chapters appearing in wrong order` | File naming mismatch in `chapters/` | Ensure chapter filename or title matches canonical keywords or check `sync_chapters.py` rules. |
| Citation renders as literal `@key` in output | Key missing from `references.bib` | Run `make validate-citations` to locate the unresolved key, then add the entry. |
| Bibliography empty / `::: {#refs}` renders as an empty div | `bibliography:` key missing from `_quarto.yml`, or `references.bib` not found relative to the project root | Confirm `_quarto.yml` has a top-level `bibliography: references.bib` and that the file exists at the repository root. |
