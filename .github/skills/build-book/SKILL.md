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

### 3. `validate_book.py` — Pre-flight Quality Auditor
Audits `index.qmd` and all chapter `.qmd` files for structural correctness:

```bash
.venv/bin/python .github/skills/build-book/scripts/validate_book.py --verbose

# Citation checks only touch one file (no corpus-wide orphan detection)
.venv/bin/python .github/skills/build-book/scripts/validate_book.py --file chapters/embedding_spaces.qmd

# Skip citation validation entirely
.venv/bin/python .github/skills/build-book/scripts/validate_book.py --no-citations
```

**Checks Performed**:
1. **Frontmatter**: Non-empty `title`, valid YAML delimiters.
2. **Callouts**: Perfectly balanced `:::` container blocks.
3. **Executable Code**: Valid Python syntax within ````{python}`` blocks.
4. **Display Math**: Balanced `$$` delimiters and valid LaTeX math environments.
5. **Section Breaks**: `{{< pagebreak >}}` used instead of `---` horizontal rules between parts/chapters/special sections.
6. **Citations**: Every `@citekey` resolves against `references.bib`; no orphan bib entries; `file =` paths exist under `references/`; no legacy hand-numbered `## References` lists (gated by `--citations`/`--no-citations`, default on).

---

## Chapter Authoring Guide

### File Placement and Naming
Place new chapters in `chapters/`:
- `chapters/embedding_spaces.qmd` (Chapter 1)
- `chapters/vector_databases.qmd` (Chapter 2)
- `chapters/curse_of_dimensionality.qmd` (Chapter 3)
- `chapters/tangent_spaces_geodesics.qmd` (Chapter 4)
- ...

Run `make sync-chapters` to automatically register newly added files into `_quarto.yml`.

### Chapter Frontmatter & Structure
Each chapter file should begin with YAML frontmatter:

```markdown
---
title: "The Anatomy of Embedding and Latent Spaces"
subtitle: "From Shannon's Bits to High-Dimensional Geometric Knowledge"
author: "Marc Magrans de Abril"
jupyter: python3
---

# Introduction: The Epistemological Leap {#sec-intro}

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
* **Required fields**: standard bibliographic fields (`author`, `title`, `year`, plus venue-specific fields) **plus two project-specific fields**:
  - `file =` — path to the PDF in `references/` when a local copy is held (empty `{}` otherwise). This is the join key `ground-truth-review` uses to go from citekey → PDF → page evidence.
  - `keywords =` — chapter tags (`ch01`) and section tags (`blueprint2`), used to generate per-chapter further-reading lists and audit coverage.
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
        └── validate_book.py     # Markdown/math/code/citation auditor
```

---

## Review Questions & Solutions

Same markup and numbering as the little-book. Put 2–3 questions at the end of each section as an ordered list inside `::: {.questions}`; they are numbered `<chapter>.<n>` automatically (cumulative per chapter). Write the answers in `chapters/solutions.qmd` (listed last in the book, unnumbered), one `::: {.answers ref="<chapter-file-stem>"}` block per chapter, same order as the questions. `filters/book-questions.lua` adds the numbers, the per-chapter headings in the solutions, and the links between each question and its solution (HTML, EPUB, PDF). `make validate` fails if a chapter's question and solution counts differ or a `ref` is unknown.

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
