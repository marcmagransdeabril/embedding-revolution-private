---
name: build-book
description: "Build, render, export, validate, and format the multi-chapter book in standard publishing formats (Springer 155x235mm, O'Reilly 7x9.1875in, HTML, EPUB) from chapters/*.qmd. Use when: building or rendering the book, generating PDF/HTML/EPUB, adding new chapters, syncing book chapter registry, validating chapter markdown/math/references, or configuring book styling."
---

# Build Book

Automated build system and publishing pipeline for *The Embedding Revolution*, generating production-grade books in standard publisher trim sizes (Springer monograph 155mm $\times$ 235mm, O'Reilly 7in $\times$ 9.1875in, multi-page HTML, and EPUB) from Quarto markdown (`.qmd`) chapter files.

## When to Invoke (Triggers)

Invoke this skill whenever:
- **Building / Rendering the Book**: Generating the complete book in PDF (Springer or O'Reilly), HTML website, or EPUB format.
- **Adding or Renaming Chapters**: Adding new chapter drafts into `chapters/` and synchronizing the chapter outline into `_quarto.yml`.
- **Pre-flight Validation & Linting**: Checking chapter frontmatter, math syntax (`$$`), balanced callout divs (`:::`), Python code chunks, figure labels, and cross-references.
- **Styling & Layout Customization**: Adjusting publisher geometries, LaTeX preambles, Lua filters, or HTML theme styles.
- **Exporting Standalone Artifacts**: Creating distribution builds for reading, review, or print.

---

## Environment & Prerequisites

The build pipeline leverages Quarto, TinyTeX (XeLaTeX), Pandoc, and the project Python virtual environment (`.venv`):

* **Python Virtual Environment**: `.venv/bin/python` provides the Python kernel and data science libraries (NumPy, SciPy, Matplotlib, PyTorch, etc.) for executing interactive code chunks.
* **Quarto**: Quarto CLI (v1.5+) drives multi-format document rendering and book orchestration.
* **TinyTeX / XeLaTeX**: LaTeX engine located at `~/.TinyTeX/bin/x86_64-linux` for high-precision book typography and mathematics.
* **Pandoc**: Built-in document conversion engine with custom Lua filters.

---

## Publishing Formats & Trim Sizes

| Format | Target | Trim Dimensions | Geometry & Margins | Layout Characteristics |
| :--- | :--- | :--- | :--- | :--- |
| **Springer Monograph** | `pdf-springer` / `pdf` | **155mm $\times$ 235mm** (6.1in $\times$ 9.25in) | Inner: 22mm, Outer: 20mm, Top: 24mm, Bottom: 26mm | Classic Springer Navy palette (`#003366`), Palatino/KOMA `scrbook`, running heads with chapter/section titles on alternating pages, boxed theorems and callouts. |
| **O'Reilly Standard** | `pdf-oreilly` | **7.0in $\times$ 9.1875in** (178mm $\times$ 233mm) | Inner: 0.85in, Outer: 0.75in, Top: 0.80in, Bottom: 0.85in | Distinctive O'Reilly dark red / charcoal palette, accent horizontal rules, left-border callout bars, framed code listings. |
| **Interactive Web Book** | `html` | Responsive | Flexible multi-column | Dark/light theme toggle, interactive collapsible code blocks, MathJax math, search, sidebar navigation. |
| **E-reader** | `epub` | Dynamic e-reader | Reflowable text | EPUB 3 standard, MathML equations, structured navigation. |

---

## Quick-Start Commands (Makefile)

The repository root includes a comprehensive `Makefile` wrapping all build operations:

```bash
# Build complete book (HTML + default Springer PDF)
make book

# Build specific PDF formats
make pdf-springer       # Standard Springer format (155mm x 235mm)
make pdf-oreilly        # Standard O'Reilly format (7in x 9.1875in)
make pdf FORMAT=oreilly # Select via variable

# Build HTML web book or EPUB
make html
make epub

# Pre-build validation and chapter synchronization
make validate           # Audit chapter markdown, math, and code syntax
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
# Build default Springer PDF
.venv/bin/python .github/skills/build-book/scripts/build_book.py --format pdf-springer

# Build all formats (HTML, Springer PDF, O'Reilly PDF, EPUB)
.venv/bin/python .github/skills/build-book/scripts/build_book.py --format all

# Fast draft build (skip re-executing Python code cells)
.venv/bin/python .github/skills/build-book/scripts/build_book.py --format pdf --no-execute

# Preview commands without executing
.venv/bin/python .github/skills/build-book/scripts/build_book.py --dry-run --format all
```

**Key Arguments**:
- `--format, -f`: `pdf-springer`, `pdf-oreilly`, `html`, `epub`, `all`.
- `--clean, -c`: Remove previous `_book`, `_freeze`, and temporary files before building.
- `--no-execute`: Render using cached code cell outputs.
- `--no-sync`: Skip automatic chapter registry synchronization.
- `--no-validate`: Skip syntax and math validation.

### 2. `sync_chapters.py` — Dynamic Chapter Registry
Scans `chapters/*.qmd`, maps files to the canonical Parts I–IV + Epilogue structure, and updates `_quarto.yml`:

```bash
.venv/bin/python .github/skills/build-book/scripts/sync_chapters.py --verbose
```

### 3. `validate_book.py` — Pre-flight Quality Auditor
Audits `index.qmd` and all chapter `.qmd` files for structural correctness:

```bash
.venv/bin/python .github/skills/build-book/scripts/validate_book.py --verbose
```

**Checks Performed**:
1. **Frontmatter**: Non-empty `title`, valid YAML delimiters.
2. **Callouts**: Perfectly balanced `:::` container blocks.
3. **Executable Code**: Valid Python syntax within ````{python}`` blocks.
4. **Display Math**: Balanced `$$` delimiters and valid LaTeX math environments.

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

---

## Ancillary Architecture & Customization

```text
├── _quarto.yml                  # Master Quarto book configuration
├── _quarto-springer.yml         # Springer profile (155x235mm)
├── _quarto-oreilly.yml          # O'Reilly profile (7x9.1875in)
├── index.qmd                    # Book Welcome, Preface, & Table of Contents
├── Makefile                     # Root build automation targets
├── filters/
│   ├── book-callouts.lua        # Callout box transformation filter
│   └── book-typography.lua      # Typographic non-breaking space & quote filter
├── styles/
│   ├── springer-preamble.tex    # Springer LaTeX geometry, headers, tcolorboxes
│   ├── oreilly-preamble.tex     # O'Reilly LaTeX geometry, rules, code frames
│   ├── book-theme.scss          # Modern responsive HTML web book SCSS
│   └── book.typ                 # Custom Typst book template
└── .github/skills/build-book/
    ├── SKILL.md                 # Skill definition and instructions
    └── scripts/
        ├── build_book.py        # Master build driver
        ├── sync_chapters.py     # Dynamic chapter discovery
        └── validate_book.py     # Markdown/math/code auditor
```

---

## Troubleshooting & Recovery

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `ModuleNotFoundError: No module named 'matplotlib'` | Code cell executed without virtual environment packages | Run `.venv/bin/pip install -r requirements.txt` or execute through `build_book.py` / `Makefile` which automatically sets `QUARTO_PYTHON`. |
| `! LaTeX Error: File 'fvextra.sty' not found` | First-time LaTeX package fetch | Let TinyTeX download packages via `tlmgr` automatically, or ensure `PATH` contains `~/.TinyTeX/bin/x86_64-linux`. |
| `Unclosed ':::' block` | Missing closing delimiter in chapter markdown | Run `make validate` to locate the exact file and line number. |
| `Chapters appearing in wrong order` | File naming mismatch in `chapters/` | Ensure chapter filename or title matches canonical keywords or check `sync_chapters.py` rules. |
