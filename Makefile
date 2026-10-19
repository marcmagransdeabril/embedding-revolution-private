# ==============================================================================
# The Embedding Revolution - Book Build Automation
# ==============================================================================
# Standard publishing targets (O'Reilly 7x9.1875in, HTML, EPUB)
# ==============================================================================

SHELL := /bin/bash
VENV_PYTHON := $(CURDIR)/.venv/bin/python
TINYTEX_BIN := $(HOME)/.TinyTeX/bin/x86_64-linux
EXPORT_PATH := PATH="$(TINYTEX_BIN):$(PATH)" QUARTO_PYTHON="$(VENV_PYTHON)"

.PHONY: help all book pdf html epub sync-chapters validate check preview clean

# Default target
all: book

help:
	@echo "======================================================================"
	@echo " The Embedding Revolution - Book Build System"
	@echo "======================================================================"
	@echo " make book         - Build HTML and PDF book (O'Reilly 7in x 9.1875in)"
	@echo " make pdf          - Build PDF book (O'Reilly 7in x 9.1875in)"
	@echo " make html         - Build interactive multi-page HTML book"
	@echo " make epub         - Build EPUB 3 ebook"
	@echo " make sync-chapters- Auto-discover chapters/*.qmd and update _quarto.yml"
	@echo " make validate     - Validate chapter markdown, math, and cross-references"
	@echo " make preview      - Start Quarto live preview server"
	@echo " make clean        - Clean build artifacts (_book, _freeze, .quarto)"
	@echo "======================================================================"

book: sync-chapters html pdf

sync-chapters:
	@echo "==> Synchronizing book chapters from chapters/*.qmd..."
	@$(EXPORT_PATH) $(VENV_PYTHON) .github/skills/build-book/scripts/sync_chapters.py

validate:
	@echo "==> Validating book chapters..."
	@$(EXPORT_PATH) $(VENV_PYTHON) .github/skills/build-book/scripts/validate_book.py

check: validate

pdf: sync-chapters
	@echo "==> Building PDF Book (O'Reilly Format 7in x 9.1875in)..."
	@$(EXPORT_PATH) quarto render --to pdf

html: sync-chapters
	@echo "==> Building Multi-Page HTML Book..."
	@$(EXPORT_PATH) quarto render --to html

epub: sync-chapters
	@echo "==> Building EPUB 3 Book..."
	@$(EXPORT_PATH) quarto render --to epub

preview:
	@echo "==> Launching Quarto live preview server..."
	@$(EXPORT_PATH) quarto preview

clean:
	@echo "==> Cleaning build artifacts..."
	@rm -rf _book _freeze .quarto
	@rm -f index.tex index.pdf chapters/*.html chapters/*.tex
	@echo "==> Clean complete."
