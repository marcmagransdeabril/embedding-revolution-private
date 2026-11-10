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
CODE_SCRIPTS := $(filter-out $(CODE_HELPERS),$(wildcard code/*/*.py))
CODE_STAMPS  := $(CODE_SCRIPTS:code/%.py=.code-tests/%.ok)

.PHONY: help all book pdf html epub sync-chapters sync-solutions test-code validate validate-citations validate-inquiry durability check preview clean

# Default target
all: book

help:
	@echo "======================================================================"
	@echo " The Embedding Revolution - Book Build System"
	@echo "======================================================================"
	@echo " make book              - Run code tests, then build HTML and PDF book (O'Reilly 7in x 9.1875in)"
	@echo " make test-code         - Run the solution scripts in code/ that changed since their last pass"
	@echo " make pdf               - Build PDF book (O'Reilly 7in x 9.1875in)"
	@echo " make html              - Build interactive multi-page HTML book"
	@echo " make epub              - Build EPUB 3 ebook"
	@echo " make sync-chapters     - Auto-discover chapters/*.qmd and update _quarto.yml"
	@echo " make sync-solutions    - Regenerate chapters/solutions.qmd from the answers blocks in each chapter"
	@echo " make validate          - Validate chapter markdown, math, and cross-references"
	@echo " make validate-citations- Validate @citekey citations against references.bib"
	@echo " make validate-inquiry - Lint inquiry/ledger.yml (readings, evidence, falsifiers, roll-up)"
	@echo " make durability        - Durability metrics and their change since the last snapshot"
	@echo " make preview           - Start Quarto live preview server"
	@echo " make clean             - Clean build artifacts (_book, _freeze, .quarto)"
	@echo "======================================================================"

book: test-code sync-chapters sync-solutions html pdf

test-code: $(CODE_STAMPS)

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

# inquiry/ledger.yml holds the book's questions, current readings and evidence (review-doc §17).
validate-inquiry:
	@echo "==> Linting inquiry/ledger.yml..."
	@$(VENV_PYTHON) .github/skills/review-doc/scripts/durability_metrics.py lint

# Proxies for review-doc §18. Run `... snapshot` after a review to record a new baseline.
durability:
	@$(VENV_PYTHON) .github/skills/review-doc/scripts/durability_metrics.py diff

check: validate

pdf: sync-chapters sync-solutions
	@echo "==> Building PDF Book (O'Reilly Format 7in x 9.1875in)..."
	@$(EXPORT_PATH) quarto render --to pdf --no-clean

html: sync-chapters sync-solutions
	@echo "==> Building Multi-Page HTML Book..."
	@$(EXPORT_PATH) quarto render --to html --no-clean

epub: sync-chapters sync-solutions
	@echo "==> Building EPUB 3 Book..."
	@$(EXPORT_PATH) quarto render --to epub --no-clean

preview: sync-solutions
	@echo "==> Launching Quarto live preview server..."
	@$(EXPORT_PATH) quarto preview

clean:
	@echo "==> Cleaning build artifacts..."
	@rm -rf _book _freeze .quarto .code-tests
	@rm -f index.tex index.pdf chapters/*.html chapters/*.tex
	@echo "==> Clean complete."
