#!/usr/bin/env python3
"""Batch-convert reference PDFs to Markdown (math + figures preserved) via Marker."""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARKER_RUNNER = Path(__file__).resolve().parent / "_marker_runner.py"

IMG_LINK_RE = re.compile(r'(!\[[^\]]*\]\()([^)\s]+)')


def repo_root(start: Path) -> Path:
    for p in (start, *start.parents):
        if (p / ".git").is_dir():
            return p
    return start


REPO_ROOT = repo_root(Path(__file__).resolve())
DEFAULT_REFERENCES = REPO_ROOT / "references"


def pending_pdfs(references_dir: Path, force: bool):
    for pdf in sorted(references_dir.glob("*.pdf")):
        if force or not (references_dir / f"{pdf.stem}.md").exists():
            yield pdf


def run_marker(pdf: Path, out_dir: Path) -> Path:
    # Equations are OCR'd via the VLM in both modes regardless of force_ocr;
    # force_ocr would additionally force full-page OCR on all text, which is
    # far slower on CPU without improving math fidelity. ocr_inline_math fixes
    # inline-math glyphs that pdftext garbles (auto-on only in balanced mode).
    # Run via _marker_runner.py (not the marker_single console script) so we
    # can raise Python's recursion limit: markdownify can exceed the default
    # limit of 1000 on documents with deeply nested tables.
    subprocess.run(
        [sys.executable, str(MARKER_RUNNER), str(pdf), "--output_dir", str(out_dir),
         "--output_format", "markdown", "--paginate_output", "--ocr_inline_math", "true"],
        check=True,
    )
    matches = list(out_dir.rglob(f"{pdf.stem}.md"))
    if not matches:
        raise RuntimeError(f"marker produced no markdown for {pdf.name}")
    return matches[0]


def rewrite_image_links(text: str, name: str, filenames: set[str]) -> str:
    def repl(m: re.Match) -> str:
        prefix, path = m.groups()
        base = Path(path).name
        return f"{prefix}{name}/images/{base}" if base in filenames else m.group(0)

    return IMG_LINK_RE.sub(repl, text)


def finalize(md_file: Path, pdf: Path, references_dir: Path) -> None:
    name = pdf.stem
    dest_images = references_dir / name / "images"
    dest_images.mkdir(parents=True, exist_ok=True)
    moved = []
    for img in md_file.parent.rglob("*"):
        if img.suffix.lower() in {".png", ".jpg", ".jpeg"}:
            shutil.move(str(img), dest_images / img.name)
            moved.append(img.name)
    text = rewrite_image_links(md_file.read_text(encoding="utf-8"), name, set(moved))
    (references_dir / f"{name}.md").write_text(text, encoding="utf-8")


def convert(pdf: Path, references_dir: Path) -> str:
    with tempfile.TemporaryDirectory(prefix=f"marker-{pdf.stem}-") as tmp:
        md_file = run_marker(pdf, Path(tmp))
        finalize(md_file, pdf, references_dir)
    return pdf.stem


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdfs", nargs="*", type=Path,
                     help="specific PDFs to convert; default: all unconverted PDFs in references/")
    ap.add_argument("--references-dir", type=Path, default=DEFAULT_REFERENCES)
    ap.add_argument("--force", action="store_true", help="reconvert even if a markdown file already exists")
    args = ap.parse_args()

    targets = args.pdfs or list(pending_pdfs(args.references_dir, args.force))
    converted = [convert(pdf, args.references_dir) for pdf in targets]
    print(json.dumps(converted))


if __name__ == "__main__":
    main()
