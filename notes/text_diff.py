#!/usr/bin/env python3
"""One-time gate for Step 0d: extract the visible text of a render (HTML, EPUB, PDF) and diff two extractions.

    text_diff.py extract <html-dir|epub|pdf> <out-dir>
    text_diff.py diff <out-dir-before> <out-dir-after>

Exit status 0 only if every extracted file is identical.
"""
import difflib
import re
import subprocess
import sys
import zipfile
from html.parser import HTMLParser
from pathlib import Path


class Text(HTMLParser):
    """Visible text; the raw .qmd that code-tools embeds in every page (a modal) is skipped, it is source, not text."""

    def __init__(self):
        super().__init__()
        self.parts, self.skip, self.modal = [], 0, 0

    def handle_starttag(self, tag, attrs):
        if tag == "div":
            if self.modal:
                self.modal += 1
            elif dict(attrs).get("id") == "quarto-embedded-source-code-modal":
                self.modal = 1
        if self.modal:
            return
        if tag in ("script", "style"):
            self.skip += 1
        elif tag in ("p", "div", "li", "h1", "h2", "h3", "h4", "tr", "br", "section"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if self.modal:
            if tag == "div":
                self.modal -= 1
            return
        if tag in ("script", "style"):
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip and not self.modal:
            self.parts.append(data)


def html_text(s: str) -> str:
    p = Text()
    p.feed(s)
    text = "".join(p.parts)
    return "\n".join(ln for ln in (re.sub(r"\s+", " ", l).strip() for l in text.splitlines()) if ln) + "\n"


def extract(src: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        for f in sorted(src.rglob("*.html")):
            if "site_libs" in f.parts:
                continue
            (out / (str(f.relative_to(src)).replace("/", "__") + ".txt")).write_text(html_text(f.read_text(encoding="utf-8")))
    elif src.suffix == ".epub":
        with zipfile.ZipFile(src) as z:
            for n in sorted(z.namelist()):
                if n.endswith((".xhtml", ".html")):
                    (out / (n.replace("/", "__") + ".txt")).write_text(html_text(z.read(n).decode("utf-8")))
    elif src.suffix == ".pdf":
        subprocess.run(["pdftotext", str(src), str(out / "raw.txt")], check=True)
        # Line breaks and hyphenation move when a reference is typeset differently, so compare the words: join
        # "hyphen + line break", drop all hyphens and page furniture is left in (a few spurious diffs are read by hand).
        raw = (out / "raw.txt").read_text(encoding="utf-8").replace("\f", "\n")
        raw = re.sub(r"(\w)-\s+(\w)", r"\1\2", raw).replace("-", "").replace("\u00ad", "")
        (out / "book.txt").write_text("\n".join(raw.split()) + "\n")
        (out / "raw.txt").unlink()
    else:
        sys.exit(f"unknown source {src}")


def diff(a: Path, b: Path) -> int:
    names = sorted({p.name for p in a.iterdir()} | {p.name for p in b.iterdir()})
    bad = 0
    for n in names:
        fa, fb = a / n, b / n
        if not fa.exists() or not fb.exists():
            print(f"ONLY IN {'before' if fa.exists() else 'after'}: {n}")
            bad += 1
            continue
        la, lb = fa.read_text().splitlines(), fb.read_text().splitlines()
        if la != lb:
            bad += 1
            print(f"DIFF {n}")
            for l in list(difflib.unified_diff(la, lb, "before", "after", lineterm="", n=0))[:12]:
                print("   ", l[:200])
    print(f"{len(names)} files compared, {bad} differ")
    return 1 if bad else 0


if __name__ == "__main__":
    if sys.argv[1] == "extract":
        extract(Path(sys.argv[2]), Path(sys.argv[3]))
    elif sys.argv[1] == "diff":
        sys.exit(diff(Path(sys.argv[2]), Path(sys.argv[3])))
