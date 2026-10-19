# The Embedding Revolution

### *Navigating High-Dimensional Knowledge Manifolds Through the Geek's Lens*

**Author: Marc Magrans de Abril**

---

## 📖 Overview

We are living through what public discourse calls the "Generative AI Revolution." But beneath the buzzwords, transformer attention heads, and probabilistic text generators lies a much deeper, quieter mathematical paradigm shift: **the Embedding Revolution**.

For centuries, human engineering and scientific modeling relied on explicit symbolic equations, discrete databases, and low-dimensional coordinate systems. Modern AI has upended this by discovering that almost any complex facet of reality—human language, protein folding, robotic trajectories, graph topologies, and logical reasoning—can be mapped onto continuous, high-dimensional geometric manifolds. Once embedded, knowledge is no longer static text or discrete tables; it becomes a geometry where semantics are vectors, analogies are parallel transports, relations are algebraic operations, and reasoning is a smooth trajectory through latent space.

Written in the personal, candid, and intellectually curious spirit of *Through the Geek's Lens*—but with a sharper technical edge for engineers, computer scientists, mathematicians, and physicists—this book explores how high-dimensional embedding spaces work, how they are generated, how they tame the bizarre geometry of high dimensions, and how they bridge classical computer science, deep learning, quantum logic, topological data analysis, and neurosymbolic architectures.

---

## 📚 Book Architecture & Single Source of Truth

The complete book roadmap, prologue, acknowledgments, disclaimers, mathematical conventions, and full chapter contents are maintained in **[index.qmd](index.qmd)** as the single source of truth.

---

## 🛠️ Environment Setup & Build Automation

This project uses Quarto and a Python virtual environment (`.venv`) for rendering book formats, executing code blocks, and running validations.

### Activate Virtual Environment

```bash
source .venv/bin/activate
```

Or run commands directly via the virtual environment:

```bash
.venv/bin/python <script.py>
.venv/bin/pytest
```

### Building the Book

The repository includes a comprehensive `Makefile` supporting multiple standard publication outputs:

```bash
# Build HTML and default PDF (Springer 155mm x 235mm)
make book

# Build format-specific PDFs
make pdf-springer   # Springer format (155mm x 235mm)
make pdf-oreilly    # O'Reilly format (7in x 9.1875in)

# Build interactive HTML book
make html

# Build EPUB 3 ebook
make epub

# Validate chapter markdown, math, and cross-references
make validate
```

