#!/usr/bin/env python3
"""Verify a converted Markdown file against its source PDF: LaTeX validity, image
references, a markdown->PDF round-trip render, and fuzzy-matched page samples."""
import argparse
import difflib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pymupdf
from pylatexenc.latexwalker import LatexWalker, LatexWalkerParseError

MATH_RE = re.compile(
    r'(?<!\\)\$\$(.+?)(?<!\\)\$\$|(?<!\\)\$(.+?)(?<!\\)\$|\\\[(.+?)\\\]|\\\((.+?)\\\)',
    re.S,
)
IMG_RE = re.compile(r'!\[[^\]]*\]\(([^)\s]+)')
WS_RE = re.compile(r'\s+')

# Markup noise that has no counterpart in pymupdf's raw page text, so it must
# be stripped before diffing markdown against page text for similarity. Math
# delimiters/commands are dropped but their operands (variable letters,
# numbers) are kept, since those literal characters do appear in the PDF text.
MD_LINK_RE = re.compile(r'\[([^\]]*)\]\([^)]*\)')
HTML_TAG_RE = re.compile(r'<[^>]+>')
PAGE_BREAK_RE = re.compile(r'\{\d+\}-+')
MD_EMPHASIS_RE = re.compile(r'\*\*|\*|__|`')
MD_ESCAPE_RE = re.compile(r'\\([\\`*_{}\[\]()#+\-.!])')
LATEX_COMMAND_RE = re.compile(r'\\[a-zA-Z]+')
LATEX_STRUCTURAL_RE = re.compile(r'[\\{}^_$]')


def normalize_for_match(text: str) -> str:
    text = MD_LINK_RE.sub(r'\1', text)
    text = HTML_TAG_RE.sub(' ', text)
    text = PAGE_BREAK_RE.sub(' ', text)
    text = MD_EMPHASIS_RE.sub('', text)
    text = MD_ESCAPE_RE.sub(r'\1', text)
    text = LATEX_COMMAND_RE.sub(' ', text)
    text = LATEX_STRUCTURAL_RE.sub('', text)
    return WS_RE.sub(' ', text).strip()


def repo_root(start: Path) -> Path:
    for p in (start, *start.parents):
        if (p / ".git").is_dir():
            return p
    return start


REPO_ROOT = repo_root(Path(__file__).resolve())
DEFAULT_REFERENCES = REPO_ROOT / "references"
MIN_SAMPLE, MAX_SAMPLE = 10, 20


def validate_latex(text: str) -> list[dict]:
    errors = []
    for m in MATH_RE.finditer(text):
        expr = next(g for g in m.groups() if g is not None)
        depth = 0
        for ch in expr:
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth < 0:
                    break
        if depth != 0:
            errors.append({"excerpt": expr[:80], "error": "unbalanced braces"})
            continue
        try:
            LatexWalker(expr).get_latex_nodes()
        except LatexWalkerParseError as e:
            errors.append({"excerpt": expr[:80], "error": str(e)})
    return errors


def check_images(text: str, images_dir: Path, md_dir: Path) -> list[dict]:
    issues = []
    referenced = set()
    for link in IMG_RE.findall(text):
        target = (md_dir / link).resolve()
        referenced.add(target)
        if not target.exists():
            issues.append({"type": "missing", "path": link})
    if images_dir.exists():
        for f in images_dir.iterdir():
            if f.resolve() not in referenced:
                issues.append({"type": "orphan", "path": str(f.relative_to(md_dir))})
    return issues


def roundtrip_check(md_path: Path) -> dict:
    for tool in ("pandoc", "tectonic"):
        if shutil.which(tool) is None:
            raise RuntimeError(f"'{tool}' is required for the round-trip check but was not found on PATH")
    with tempfile.TemporaryDirectory() as tmp:
        out_pdf = Path(tmp) / "roundtrip.pdf"
        proc = subprocess.run(
            ["pandoc", str(md_path), "-o", str(out_pdf), "--pdf-engine=tectonic",
             f"--resource-path={md_path.parent}"],
            capture_output=True, text=True,
        )
        stderr = proc.stderr.strip()
        # pandoc/tectonic routinely emit non-fatal "warning:" lines (overfull/
        # underfull hboxes, missing glyphs, reproducibility notes) on a
        # successful build; only a failed build counts as an error.
        status = "ok" if proc.returncode == 0 and out_pdf.exists() else "errors"
        return {"status": status, "stderr": stderr[:2000]}


def sample_page_numbers(n_pages: int) -> list[int]:
    if n_pages <= MAX_SAMPLE:
        return list(range(n_pages))
    k = min(MAX_SAMPLE, max(MIN_SAMPLE, n_pages))
    return sorted({round(i * (n_pages - 1) / (k - 1)) for i in range(k)})


def best_match_window(page_text: str, md_text: str, pad: int = 200) -> SimpleNamespace:
    sm = difflib.SequenceMatcher(None, md_text, page_text, autojunk=False)
    blocks = [b for b in sm.get_matching_blocks() if b.size > 0]
    if not blocks:
        return SimpleNamespace(similarity=0.0, excerpt="")
    best = max(blocks, key=lambda b: b.size)
    start, end = max(0, best.a - pad), min(len(md_text), best.a + best.size + pad)
    excerpt = md_text[start:end]
    similarity = difflib.SequenceMatcher(None, excerpt, page_text, autojunk=False).ratio()
    return SimpleNamespace(similarity=similarity, excerpt=excerpt)


def build_samples(pdf_path: Path, md_text: str, out_dir: Path) -> list[dict]:
    md_text = normalize_for_match(md_text)
    samples = []
    with pymupdf.open(pdf_path) as doc:
        for i in sample_page_numbers(doc.page_count):
            page = doc[i]
            png_path = out_dir / f"page_{i + 1:03d}.png"
            page.get_pixmap(dpi=150).save(png_path)
            page_text = normalize_for_match(page.get_text())
            match = best_match_window(page_text, md_text)
            samples.append({
                "page_no": i + 1,
                "image_path": str(png_path),
                "similarity": round(match.similarity, 3),
                "markdown_excerpt": match.excerpt,
            })
    return samples


def verify_one(name: str, references_dir: Path) -> dict:
    pdf = references_dir / f"{name}.pdf"
    md = references_dir / f"{name}.md"
    images_dir = references_dir / name / "images"
    text = md.read_text(encoding="utf-8")
    samples_dir = Path(tempfile.mkdtemp(prefix=f"verify-{name}-"))
    return {
        "name": name,
        "latex_errors": validate_latex(text),
        "image_issues": check_images(text, images_dir, md.parent),
        "roundtrip": roundtrip_check(md),
        "sample_pages": build_samples(pdf, text, samples_dir),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("names", nargs="*", help="markdown/pdf stem(s) under references/; default: all converted")
    ap.add_argument("--references-dir", type=Path, default=DEFAULT_REFERENCES)
    args = ap.parse_args()

    names = args.names or [p.stem for p in sorted(args.references_dir.glob("*.md"))]
    print(json.dumps([verify_one(n, args.references_dir) for n in names], indent=2))


if __name__ == "__main__":
    main()
