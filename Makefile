# ==============================================================================
# The Embedding Revolution - Book Build Automation
# ==============================================================================
# Standard publishing targets for Springer (155x235mm) and O'Reilly (7x9.1875in)
# ==============================================================================

SHELL := /bin/bash
VENV_PYTHON := $(CURDIR)/.venv/bin/python
TINYTEX_BIN := $(HOME)/.TinyTeX/bin/x86_64-linux
EXPORT_PATH := PATH="$(TINYTEX_BIN):$(PATH)" QUARTO_PYTHON="$(VENV_PYTHON)"

FORMAT ?= springer

.PHONY: help all book pdf pdf-springer pdf-oreilly html epub sync-chapters validate check preview clean

# Default target
all: book

help:
	@echo "======================================================================"
	@echo " The Embedding Revolution - Book Build System"
	@echo "======================================================================"
	@echo " make book         - Build HTML and default PDF (Springer 155x235mm)"
	@echo " make pdf          - Build PDF book (uses FORMAT=springer or oreilly)"
	@echo " make pdf-springer - Build PDF in Springer format (155mm x 235mm)"
	@echo " make pdf-oreilly  - Build PDF in O'Reilly format (7in x 9.1875in)"
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
	@if [ "$(FORMAT)" = "oreilly" ]; then \
		$(MAKE) pdf-oreilly; \
	else \
		$(MAKE) pdf-springer; \
	fi

pdf-springer: sync-chapters
	@echo "==> Building Springer Format PDF (155mm x 235mm)..."
	@$(EXPORT_PATH) quarto render --to pdf --profile springer
	@cp -f _book/The-Embedding-Revolution.pdf _book/The-Embedding-Revolution-Springer.pdf 2>/dev/null || true

pdf-oreilly: sync-chapters
	@echo "==> Building O'Reilly Format PDF (7in x 9.1875in)..."
	@$(EXPORT_PATH) quarto render --to pdf --profile oreilly
	@cp -f _book/The-Embedding-Revolution.pdf _book/The-Embedding-Revolution-OReilly.pdf 2>/dev/null || true

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
