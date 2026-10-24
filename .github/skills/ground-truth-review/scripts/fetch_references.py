#!/usr/bin/env python3
"""Download the references of references.bib that are missing from references/, then refresh the ground-truth index.

Workflow (all paths are relative to the project root, never absolute):

1. Check that ``references.bib`` exists. If it does not, report it and stop (nothing to sync).
2. Find the entries whose ``file =`` field is empty or names a PDF that is not in ``references/``.
3. For each of them, try legitimate open sources only, in this order:
   an explicit ``pdf_url`` field, the ``url`` field when it points to a PDF, arXiv, ACL Anthology,
   Unpaywall (needs the UNPAYWALL_EMAIL environment variable), OpenAlex (by DOI, then by title).
   No shadow libraries (Sci-Hub, Anna's Archive, ...) are used.
4. Check every download (a real PDF whose first pages contain the words of the title) before keeping it,
   save it as ``references/YYYY_surname_firstwords.pdf`` and write the name in the ``file =`` field.
5. Run the index builder, so that new PDFs are searchable by ``ground_check.py`` (skip with --no-index).

Entries that cannot be found are listed at the end so that a PDF can be added by hand.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pymupdf

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parents[3]  # scripts -> ground-truth-review -> skills -> .github -> project root
DEFAULT_BIB = REPO_ROOT / "references.bib"
DEFAULT_REFERENCES = REPO_ROOT / "references"

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"
STOP_WORDS = {
    "a", "an", "and", "the", "of", "on", "in", "for", "to", "with", "from", "by", "at", "as", "or", "is", "are",
    "its", "their", "using", "via", "towards", "toward", "into", "about", "some", "one", "another",
}
MIN_TITLE_MATCH = 0.6  # fraction of the title words that must appear in the first pages of a downloaded PDF


# --------------------------------------------------------------------------- BibTeX
def parse_bib(text: str) -> list[dict]:
    """Entries of a BibTeX file as dicts: key, type, fields (lowercase names), span of the entry in `text`."""
    entries = []
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text):
        if m.group(1).lower() in {"comment", "string", "preamble"}:
            continue
        depth, i = 1, m.end()
        while i < len(text) and depth:
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            i += 1
        body = text[m.end():i - 1]
        entries.append({"key": m.group(2), "type": m.group(1).lower(), "fields": parse_fields(body), "span": (m.start(), i)})
    return entries


def parse_fields(body: str) -> dict[str, str]:
    fields, pos = {}, 0
    name_re = re.compile(r"\s*(\w+)\s*=\s*")
    while (m := name_re.match(body, pos)):
        name, pos = m.group(1).lower(), m.end()
        if pos < len(body) and body[pos] == "{":
            depth, start = 1, pos + 1
            pos += 1
            while pos < len(body) and depth:
                depth += {"{": 1, "}": -1}.get(body[pos], 0)
                pos += 1
            value = body[start:pos - 1]
        elif pos < len(body) and body[pos] == '"':
            end = body.index('"', pos + 1)
            value, pos = body[pos + 1:end], end + 1
        else:
            end = re.compile(r"[,\s}]").search(body, pos)
            end = end.start() if end else len(body)
            value, pos = body[pos:end], end
        fields[name] = value.strip()
        comma = re.compile(r"\s*,?").match(body, pos)
        pos = comma.end()
    return fields


def clean_tex(s: str) -> str:
    """Plain text from a BibTeX value: drop braces and accent/command escapes."""
    s = re.sub(r"\\[`'\"^~=.]\{?([A-Za-z])\}?", r"\1", s)
    s = re.sub(r"\\[A-Za-z]+\s*", " ", s)
    return re.sub(r"\s+", " ", re.sub(r"[{}]", "", s)).strip()


def title_words(title: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", clean_tex(title).lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 2]


def first_author_surname(author: str) -> str:
    first = re.split(r"\s+and\s+", author.strip())[0]
    surname = first.split(",")[0] if "," in first else first.split()[-1]
    return re.sub(r"[^a-z]", "", clean_tex(surname).lower()) or "unknown"


def pdf_name(entry: dict, taken: set[str]) -> str:
    """YYYY_surname_firstwords.pdf, made unique among `taken`."""
    f = entry["fields"]
    words = title_words(f.get("title", ""))[:5] or [entry["key"]]
    base = f"{f.get('year', 'nd')}_{first_author_surname(f.get('author', ''))}_{'_'.join(words)}"
    name, n = f"{base}.pdf", 2
    while name in taken:
        name, n = f"{base}_{n}.pdf", n + 1
    return name


def missing_entries(entries: list[dict], references_dir: Path) -> list[dict]:
    """Entries whose `file =` field is empty or names a PDF that is not in references_dir."""
    out = []
    for e in entries:
        name = e["fields"].get("file", "").strip()
        if not name or not (references_dir / name).is_file():
            out.append(e)
    return out


def set_file_field(text: str, entry: dict, name: str) -> str:
    """Return `text` with the `file` field of `entry` set to `name` (added if the entry has none)."""
    start, end = entry["span"]
    block = text[start:end]
    if re.search(r"\bfile\s*=\s*\{[^}]*\}", block):
        block = re.sub(r"(\bfile\s*=\s*)\{[^}]*\}", lambda m: f"{m.group(1)}{{{name}}}", block, count=1)
    else:
        block = re.sub(r",?\s*\}\s*$", f",\n  file     = {{{name}}}\n}}", block.rstrip(), count=1)
    return text[:start] + block + text[end:]


# --------------------------------------------------------------------------- network and PDF checks
def http_get(url: str, timeout: int = 60) -> tuple[bytes | None, str]:
    """Body of `url` (None on failure) and the reason. One retry after a 429 (rate limit)."""
    for attempt in range(2):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/pdf,application/json,*/*"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read(), "ok"
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt == 0:
                time.sleep(min(int(e.headers.get("Retry-After", 15) or 15), 60))
                continue
            return None, f"HTTP {e.code}"
        except Exception as e:  # network errors, timeouts, bad URLs
            return None, type(e).__name__
    return None, "HTTP 429"


def fetch_json(url: str):
    body, _ = http_get(url, timeout=30)
    try:
        return json.loads(body) if body else None
    except ValueError:
        return None


def pdf_text(data: bytes, pages: int = 3) -> tuple[bool, str]:
    """(is a readable PDF, text of its first pages)."""
    if not data or len(data) < 1000 or b"%PDF-" not in data[:1024]:
        return False, ""
    try:
        with pymupdf.open(stream=data, filetype="pdf") as doc:
            if doc.page_count == 0:
                return False, ""
            return True, " ".join(doc[i].get_text() for i in range(min(pages, doc.page_count)))
    except Exception:
        return False, ""


def check_pdf(data: bytes, title: str, trusted: bool) -> tuple[bool, str]:
    """Accept a download if it is a PDF whose first pages contain most words of the title.
    A PDF without a text layer (a scan) cannot be checked: it is accepted only from a `trusted` source."""
    ok, text = pdf_text(data)
    if not ok:
        return False, "not a readable PDF"
    words = title_words(title)
    if len(text.strip()) < 200:
        return (True, "scan, title not checked") if trusted else (False, "scan from an unverifiable source")
    if not words:
        return True, "no title words to check"
    haystack = re.sub(r"[^a-z0-9]+", " ", text.lower())
    share = sum(w in haystack for w in words) / len(words)
    return (share >= MIN_TITLE_MATCH), f"{share:.0%} of the title words found"


# --------------------------------------------------------------------------- sources (open access only)
def candidate_urls(entry: dict):
    """Yield (source, url, trusted). `trusted` means the source is tied to the work by an identifier or by the author."""
    f = entry["fields"]
    doi = f.get("doi", "").strip()
    eprint = re.sub(r"^arxiv:", "", f.get("eprint", "").strip(), flags=re.I)
    url = f.get("url", "").strip()
    email = os.environ.get("UNPAYWALL_EMAIL", "").strip()

    if f.get("pdf_url"):
        yield "pdf_url field", f["pdf_url"].strip(), True
    if url.lower().endswith(".pdf"):
        yield "url field", url, True
    if m := re.match(r"https?://arxiv\.org/abs/(.+)", url):
        eprint = eprint or m.group(1)
    if eprint:
        yield "arXiv", f"https://arxiv.org/pdf/{eprint}", True
    if m := re.match(r"https?://aclanthology\.org/([\w.-]+?)/?$", url):
        yield "ACL Anthology", f"https://aclanthology.org/{m.group(1)}.pdf", True
    if doi.startswith("10.18653/v1/"):
        yield "ACL Anthology", f"https://aclanthology.org/{doi[len('10.18653/v1/'):]}.pdf", True
    if doi and email:
        data = fetch_json(f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email={urllib.parse.quote(email)}")
        for loc in ([data.get("best_oa_location")] if data else []) + (data.get("oa_locations", []) if data else []):
            if loc and (loc.get("url_for_pdf") or loc.get("url")):
                yield "Unpaywall", loc.get("url_for_pdf") or loc["url"], True
    mailto = f"&mailto={urllib.parse.quote(email)}" if email else ""
    if doi:
        work = fetch_json(f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi)}?select=locations,best_oa_location{mailto}")
        for loc in ([work.get("best_oa_location")] + work.get("locations", [])) if work else []:
            if loc and loc.get("pdf_url"):
                yield "OpenAlex (DOI)", loc["pdf_url"], True
    title = clean_tex(f.get("title", ""))
    if len(title) > 15:
        res = fetch_json(f"https://api.openalex.org/works?filter=title.search:{urllib.parse.quote(title)}&per_page=3&select=locations,best_oa_location{mailto}")
        for work in (res or {}).get("results", []):
            for loc in [work.get("best_oa_location")] + work.get("locations", []):
                if loc and loc.get("pdf_url"):
                    yield "OpenAlex (title search)", loc["pdf_url"], False


def download(entry: dict) -> tuple[bytes, str] | None:
    """First verified PDF for `entry`, with a description of where it came from."""
    title = entry["fields"].get("title", "")
    seen: set[str] = set()
    for source, url, trusted in candidate_urls(entry):
        if url in seen:
            continue
        seen.add(url)
        data, why = http_get(url)
        if data is None:
            print(f"    {source}: {why} <- {url}")
            continue
        explicit = source == "pdf_url field"  # the author of the bib file vouches for it
        ok, note = (pdf_text(data)[0], "explicit pdf_url") if explicit else check_pdf(data, title, trusted)
        print(f"    {source}: {'accepted' if ok else 'rejected'} ({note}) <- {url}")
        if ok:
            return data, f"{source}: {url}"
        time.sleep(0.5)
    if not seen:
        print("    no open-access source found (no pdf_url, arXiv id, DOI or PDF link, and no open copy by title)")
    return None


# --------------------------------------------------------------------------- main
def refresh_index(references_dir: Path) -> None:
    from build_index import index_documents, resolve_pdf_targets

    db_path = references_dir / ".ground-index" / "index.sqlite"
    summaries = index_documents(pdf_paths=resolve_pdf_targets([], references_dir), db_path=db_path,
                                references_dir=references_dir, prune=True)
    counts: dict[str, int] = {}
    for s in summaries:
        counts[s["status"]] = counts.get(s["status"], 0) + 1
    print(f"Index {db_path.relative_to(references_dir.parent) if db_path.is_relative_to(references_dir.parent) else db_path}: "
          + ", ".join(f"{n} {status}" for status, n in sorted(counts.items())))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bib", type=Path, default=DEFAULT_BIB, help="BibTeX file (default: references.bib in the project root)")
    ap.add_argument("--references-dir", type=Path, default=DEFAULT_REFERENCES, help="PDF directory (default: references/)")
    ap.add_argument("--only", nargs="*", default=[], help="citekeys to fetch (default: every missing entry)")
    ap.add_argument("--dry-run", action="store_true", help="list the missing references and stop")
    ap.add_argument("--no-index", action="store_true", help="do not refresh the ground-truth index afterwards")
    args = ap.parse_args()

    if not args.bib.is_file():
        print(f"No BibTeX file at {args.bib}: nothing to download. (Index not refreshed.)")
        return 0
    args.references_dir.mkdir(parents=True, exist_ok=True)

    text = args.bib.read_text(encoding="utf-8")
    entries = parse_bib(text)
    todo = [e for e in missing_entries(entries, args.references_dir) if not args.only or e["key"] in args.only]
    print(f"{args.bib.name}: {len(entries)} entries, {len(todo)} without a PDF in {args.references_dir.name}/")

    got, failed = [], []
    if not args.dry_run:
        taken = {p.name for p in args.references_dir.glob("*.pdf")}
        for n, entry in enumerate(todo, 1):
            print(f"[{n}/{len(todo)}] {entry['key']}: {clean_tex(entry['fields'].get('title', ''))[:70]}")
            found = download(entry)
            if not found:
                failed.append(entry)
                continue
            data, source = found
            name = pdf_name(entry, taken)
            taken.add(name)
            (args.references_dir / name).write_bytes(data)
            # Re-parse after each edit: the spans of the later entries moved.
            text = set_file_field(text, next(e for e in parse_bib(text) if e["key"] == entry["key"]), name)
            args.bib.write_text(text, encoding="utf-8")
            got.append((entry["key"], name))
            print(f"    saved {name} ({len(data) / 1024:.0f} KB)")
    else:
        failed = todo

    print(f"\nDownloaded {len(got)}, still missing {len(failed)}")
    for e in failed:
        f = e["fields"]
        print(f"  - {e['key']}: {clean_tex(f.get('title', ''))} ({f.get('year', '?')}); add the PDF to {args.references_dir.name}/ "
              f"and set file = {{...}}, or put a legal direct link in a pdf_url field")
    if not args.no_index and not args.dry_run:
        sys.path.insert(0, str(SCRIPTS_DIR))
        refresh_index(args.references_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
