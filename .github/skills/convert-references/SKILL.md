---
name: convert-references
description: "Convert reference PDFs (books/papers) in references/ to Markdown, preserving math and figures, via Marker, then verify the result against the source PDF. Use when: adding new reference PDFs, or asked to convert/check/sync references to markdown."
---

# Convert References to Markdown

## Prerequisites
`.venv` active with `pip install -r requirements.txt`; `pandoc` and `tectonic` on `PATH` (required, not optional — the round-trip check fails hard without them).

On machines without an NVIDIA GPU, Marker needs `llama-server` (from [llama.cpp](https://github.com/ggml-org/llama.cpp) releases) on `PATH` to serve the `surya-ocr-2` VLM that recognizes equations/layout — without it, conversion fails outright. Use a Vulkan build if an iGPU is available (`llama-server --list-devices` to check) for a ~2x speedup over CPU-only.

Optional ~30% speedup on iGPU: quantize the stock F16 VLM to Q8_0 once (identical quality per verify.py) — convert.py auto-uses it if present at `~/.cache/datalab/surya/surya-2-q8_0.gguf`:

```bash
llama-quantize "$(readlink -f ~/.cache/huggingface/hub/models--datalab-to--surya-ocr-2-gguf/snapshots/*/surya-2.gguf)" \
  ~/.cache/datalab/surya/surya-2-q8_0.gguf Q8_0
```

(The F16 model is downloaded to the HF cache on first conversion; `llama-quantize` ships alongside `llama-server` and may need `LD_LIBRARY_PATH` set to its build dir.)

## Procedure
1. Run [convert.py](./scripts/convert.py) (no args = batch-convert every unconverted PDF in `references/`; pass specific PDF paths, or `--force` to reconvert). Prints the list of converted names.
2. Run [verify.py](./scripts/verify.py) on those names. It emits one JSON report per file: `latex_errors`, `image_issues`, `roundtrip` (`status` must be `ok`), and `sample_pages` (all pages if ≤20pp, else 10–20 evenly spread incl. first/last — each with a rendered PNG, a text-similarity score, and the best-matching markdown excerpt).
3. Surface `latex_errors` / `image_issues` / non-`ok` `roundtrip` directly as findings.
4. For each `sample_pages` entry, view the page PNG and compare it against its `markdown_excerpt` (text, math, figures/captions). Prioritize low-similarity pages; spot-check the rest.
5. Give the user a concise per-PDF pass/fail summary.
