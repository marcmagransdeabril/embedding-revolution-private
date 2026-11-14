# ==============================================================================
# The Embedding Revolution - Book Build Automation
# ==============================================================================
# Standard publishing targets (O'Reilly 7x9.1875in, HTML, EPUB)
# ==============================================================================

SHELL := /bin/bash
VENV_PYTHON := $(CURDIR)/.venv/bin/python
TINYTEX_BIN := $(HOME)/.TinyTeX/bin/x86_64-linux
EXPORT_PATH := PATH="$(TINYTEX_BIN):$(PATH)" QUARTO_PYTHON="$(VENV_PYTHON)"

# Solution scripts (code/<chapter>/*.py) are re-run only when they or their shared helper change
CODE_HELPERS := $(wildcard code/*/utils.py)
# A script whose first line is `# SKELETON` is a plan for a script, not a script: it is listed and skipped, never stamped as passed.
CODE_SKELETONS := $(shell grep -l '^\# SKELETON' $(wildcard code/*/*.py) 2>/dev/null)
CODE_SCRIPTS := $(filter-out $(CODE_HELPERS) $(CODE_SKELETONS),$(wildcard code/*/*.py))
CODE_STAMPS  := $(CODE_SCRIPTS:code/%.py=.code-tests/%.ok)

.PHONY: help all book pdf check-overflow html epub diagrams sync-chapters sync-solutions test-code validate validate-citations status durability check preview clean

# Default target
all: book

help:
	@echo "======================================================================"
	@echo " The Embedding Revolution - Book Build System"
	@echo "======================================================================"
	@echo " make book              - Run code tests, then build HTML and PDF book (O'Reilly 7in x 9.1875in)"
	@echo " make diagrams          - Compile the TikZ diagrams in diagrams/*/*.tex to PDF (PDF book) and PNG (HTML, EPUB)"
	@echo " make test-code         - Run the solution scripts in code/ that changed since their last pass"
	@echo " make pdf               - Build PDF book (O'Reilly 7in x 9.1875in); fails if a formula, table or line sticks out of the text block"
	@echo " make check-overflow    - Check the LaTeX log of the last PDF build for such overflows"
	@echo " make html              - Build interactive multi-page HTML book"
	@echo " make epub              - Build EPUB 3 ebook"
	@echo " make sync-chapters     - Auto-discover chapters/*.qmd and update _quarto.yml"
	@echo " make sync-solutions    - Regenerate chapters/solutions.qmd from the answers blocks in each chapter"
	@echo " make validate          - Validate chapter markdown, math, and cross-references"
	@echo " make validate-citations- Validate @citekey citations against references.bib"
	@echo " make status            - Chapter statuses (definitive, provisional, idea), open questions, tag consistency"
	@echo " make durability        - Durability metrics and their change since the last snapshot"
	@echo " make preview           - Start Quarto live preview server"
	@echo " make clean             - Clean build artifacts (_book, _freeze, .quarto)"
	@echo "======================================================================"

book: diagrams test-code sync-chapters sync-solutions html pdf

# TikZ diagrams: diagrams/<chapter>/<name>.tex -> .pdf (vector, for the PDF book) and .png (300 dpi, for HTML and EPUB)
# Chapters reference the .pdf; filters/tikz-img.lua swaps it for the .png outside LaTeX.
DIAGRAM_TEX := $(wildcard diagrams/*/*.tex)
DIAGRAM_PDF := $(DIAGRAM_TEX:.tex=.pdf)
DIAGRAM_PNG := $(DIAGRAM_TEX:.tex=.png)

diagrams: $(DIAGRAM_PDF) $(DIAGRAM_PNG)

diagrams/%.pdf: diagrams/%.tex diagrams/preamble.tex
	@echo "==> Compiling $<..."
	@cd $(dir $<) && $(EXPORT_PATH) lualatex --interaction=nonstopmode $(notdir $<) > $(notdir $(basename $<)).log 2>&1 \
		|| { tail -n 30 $(notdir $(basename $<)).log; exit 1; }
	@rm -f $(basename $<).aux $(basename $<).log

diagrams/%.png: diagrams/%.pdf
	@pdftoppm -png -r 300 -singlefile $< $(basename $<)

test-code: $(CODE_STAMPS)
	@for f in $(CODE_SKELETONS); do echo "==> Skipped (skeleton, not implemented): $$f"; done

.code-tests/%.ok: code/%.py $(CODE_HELPERS)
	@echo "==> Running $<..."
	@mkdir -p $(@D)
	@cd $(<D) && $(VENV_PYTHON) $(<F)
	@touch $@

sync-chapters:
	@echo "==> Synchronizing book chapters from chapters/*.qmd..."
	@$(EXPORT_PATH) $(VENV_PYTHON) .github/skills/build-book/scripts/sync_chapters.py

# chapters/solutions.qmd is GENERATED from the `::: {.answers}` blocks that sit
# right after each `::: {.questions}` block in the chapters. Never edit it by hand.
sync-solutions:
	@echo "==> Generating chapters/solutions.qmd from the chapters' answers blocks..."
	@$(VENV_PYTHON) .github/skills/build-book/scripts/sync_solutions.py

validate:
	@echo "==> Validating book chapters..."
	@$(EXPORT_PATH) $(VENV_PYTHON) .github/skills/build-book/scripts/validate_book.py

validate-citations:
	@echo "==> Validating @citekey citations against references.bib..."
	@$(EXPORT_PATH) $(VENV_PYTHON) .github/skills/build-book/scripts/validate_book.py --citations

# Status annotations live in the chapters and in the roadmap of index.qmd (see review-doc §17).
status:
	@$(VENV_PYTHON) .github/skills/review-doc/scripts/durability_metrics.py status

# Proxies for review-doc §18. Run `... snapshot` after a review to record a new baseline.
durability:
	@$(VENV_PYTHON) .github/skills/review-doc/scripts/durability_metrics.py diff

check: validate

# Quarto only warns about a cross-reference it cannot resolve (exit status 0, "?@sec-..." in the text). A chapter that
# was renamed or dropped must stop the build, so the log is kept in .quarto/ and searched. HTML also stops by itself
# (filters/book-chapter-refs.lua). Usage: $(call render,<format>)
define render
	@mkdir -p .quarto
	@set -o pipefail; $(EXPORT_PATH) quarto render --to $(1) --no-clean 2>&1 | tee .quarto/render-$(1).log
	@if grep -aq "Unable to resolve crossref" .quarto/render-$(1).log; then \
	  echo "ERROR: unresolved cross-references in the $(1) build (a label is misspelt, or its chapter was renamed or dropped):" >&2; \
	  grep -a "Unable to resolve crossref" .quarto/render-$(1).log | sort -u >&2; exit 1; fi
endef

pdf: diagrams sync-chapters sync-solutions
	@echo "==> Building PDF Book (O'Reilly Format 7in x 9.1875in)..."
	@rm -f index.log
	$(call render,pdf)
	@$(MAKE) --no-print-directory check-overflow

# LaTeX only warns (`Overfull \hbox`) about a formula, a table or a line wider than the text block, and the PDF is written anyway.
# `latex-clean: false` in _quarto.yml keeps the log, and the script fails the build on an overflow above 5pt (about the margin).
check-overflow:
	@echo "==> Checking the PDF for formulas, tables and lines that stick out of the text block..."
	@$(VENV_PYTHON) .github/skills/build-book/scripts/check_pdf_overflow.py

html: diagrams sync-chapters sync-solutions
	@echo "==> Building Multi-Page HTML Book..."
	$(call render,html)

epub: diagrams sync-chapters sync-solutions
	@echo "==> Building EPUB 3 Book..."
	$(call render,epub)

preview: sync-solutions
	@echo "==> Launching Quarto live preview server..."
	@$(EXPORT_PATH) quarto preview

clean:
	@echo "==> Cleaning build artifacts..."
	@rm -rf _book _freeze .quarto .code-tests
	@rm -f index.tex index.pdf index.log index.aux index.toc The-Embedding-Revolution.tex chapters/*.html chapters/*.tex
	@echo "==> Clean complete."
