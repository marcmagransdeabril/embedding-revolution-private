#!/usr/bin/env python3
"""Fail when the PDF build has a line, a formula or a table that sticks out of the text block.

LaTeX does not stop on these: it prints `Overfull \\hbox (12.3pt too wide)` in the log and goes on, and the formula or the table
runs into the margin or off the page. `_quarto.yml` asks Quarto to keep the LaTeX log (`latex-clean: false`), and this script
reads it after `make pdf`. An overflow larger than --max-pt (default 5 pt, a bit less than the outer margin of 54 pt, so
anything smaller is invisible) is an error. The report gives the size, the page, and the start of the offending line.

Usage: check_pdf_overflow.py [--log index.log] [--max-pt 5] [--list-all]
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OVERFULL = re.compile(r"^Overfull \\hbox \(([\d.]+)pt too wide\)(.*)$")
PAGE = re.compile(r"\[(\d+)(?=[\s\]]|$)")  # a page that was shipped out: [53] or [53 (the closing bracket comes lines later)


def find_log() -> Path:
    """The LaTeX log of the last XeLaTeX run of the project (Quarto names it after the first file of the book)."""
    logs = [p for p in ROOT.glob("*.log") if "XeTeX" in p.read_text(errors="replace")[:500]]
    if not logs:
        sys.exit("ERROR: no XeLaTeX log in the project root. Is `latex-clean: false` set for the pdf format in _quarto.yml?")
    return max(logs, key=lambda p: p.stat().st_mtime)


def overflows(log: Path):
    """Yields (size in pt, number of the last page shipped out, where, excerpt) for every overfull hbox of the log."""
    lines = log.read_text(errors="replace").splitlines()
    page, pdf_page, i = 0, 0, 0
    while i < len(lines):
        match = OVERFULL.match(lines[i])
        if match:
            where = match.group(2).strip() or "in a box"
            excerpt = lines[i + 1][:110] if i + 1 < len(lines) else ""
            yield float(match.group(1)), page, pdf_page, where, excerpt
            i += 3  # the line itself, its excerpt and the empty box
            continue
        if not lines[i].startswith(("Missing character", "Underfull", "Overfull")):
            for found in PAGE.findall(lines[i]):
                page, pdf_page = int(found), pdf_page + 1
        i += 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--log", type=Path, help="LaTeX log (default: the latest *.log of the project root)")
    parser.add_argument("--max-pt", type=float, default=5.0, help="largest overflow tolerated, in pt (default 5)")
    parser.add_argument("--list-all", action="store_true", help="also list the overflows below the limit")
    args = parser.parse_args()
    log = args.log or find_log()

    found = list(overflows(log))
    bad = [f for f in found if f[0] > args.max_pt]
    for size, page, pdf_page, where, excerpt in sorted(found, key=lambda f: -f[0]):
        if size > args.max_pt or args.list_all:
            flag = "ERROR" if size > args.max_pt else "minor"
            print(f"{flag}: {size:.1f}pt too wide, after page [{page}] (PDF page {pdf_page + 1}) {where}\n         {excerpt}", file=sys.stderr)
    if bad:
        print(f"\nERROR: {len(bad)} formula(s), table(s) or line(s) stick out of the text block by more than {args.max_pt:g}pt "
              f"in {log.name}. Split the formula (aligned), narrow the table (relative column widths in the separator row) "
              f"or rephrase.", file=sys.stderr)
        return 1
    print(f"No overflow above {args.max_pt:g}pt in {log.name} ({len(found)} smaller ones).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
