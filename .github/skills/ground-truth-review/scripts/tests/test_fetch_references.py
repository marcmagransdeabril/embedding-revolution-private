"""Offline unit tests for fetch_references.py (no network: downloads are replaced by synthetic PDFs)."""
from __future__ import annotations

import sys
from pathlib import Path

import pymupdf
import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import fetch_references as fr

BIB = """% comment
@article{shannon1948mathematical,
  author   = {Shannon, Claude E.},
  title    = {A Mathematical Theory of Communication},
  year     = {1948},
  file     = {1948_shannon.pdf}
}

@article{rice1953classes,
  author   = {Rice, H. G.},
  title    = {Classes of Recursively Enumerable Sets and Their Decision Problems},
  year     = {1953},
  file     = {}
}

@inproceedings{noFileField,
  author = {Levy, Omer and Goldberg, Yoav},
  title  = {Neural Word Embedding as Implicit Matrix Factorization},
  year   = {2014},
  keywords = {ch01},
}
"""


def make_pdf(text: str, pages: int = 1) -> bytes:
    doc = pymupdf.open()
    for _ in range(pages):
        if text:
            doc.new_page().insert_textbox(pymupdf.Rect(36, 36, 560, 780), text, fontsize=10)
        else:
            doc.new_page()
    data = doc.tobytes()
    doc.close()
    return data + b"\n%" + b"x" * 1000  # padded: real PDFs are never tiny


def test_parse_bib_fields_and_keys():
    entries = fr.parse_bib(BIB)
    assert [e["key"] for e in entries] == ["shannon1948mathematical", "rice1953classes", "noFileField"]
    assert entries[1]["fields"]["title"].startswith("Classes of Recursively")
    assert entries[1]["fields"]["file"] == ""


def test_missing_entries_checks_the_directory(tmp_path):
    (tmp_path / "1948_shannon.pdf").write_bytes(b"%PDF-")
    todo = fr.missing_entries(fr.parse_bib(BIB), tmp_path)
    assert [e["key"] for e in todo] == ["rice1953classes", "noFileField"]
    (tmp_path / "1948_shannon.pdf").unlink()  # a file= field naming an absent PDF counts as missing too
    assert len(fr.missing_entries(fr.parse_bib(BIB), tmp_path)) == 3


def test_set_file_field_replaces_and_adds():
    text = BIB
    for key, name in (("rice1953classes", "1953_rice.pdf"), ("noFileField", "2014_levy.pdf")):
        entry = next(e for e in fr.parse_bib(text) if e["key"] == key)
        text = fr.set_file_field(text, entry, name)
    fields = {e["key"]: e["fields"] for e in fr.parse_bib(text)}
    assert fields["rice1953classes"]["file"] == "1953_rice.pdf"
    assert fields["noFileField"]["file"] == "2014_levy.pdf" and fields["noFileField"]["keywords"] == "ch01"
    assert fields["shannon1948mathematical"]["file"] == "1948_shannon.pdf"  # untouched


def test_pdf_name_convention_and_uniqueness():
    entry = fr.parse_bib(BIB)[1]
    name = fr.pdf_name(entry, set())
    assert name == "1953_rice_classes_recursively_enumerable_sets_decision.pdf"
    assert fr.pdf_name(entry, {name}) == "1953_rice_classes_recursively_enumerable_sets_decision_2.pdf"


def test_check_pdf_accepts_matching_title_and_rejects_others():
    title = "Classes of Recursively Enumerable Sets and Their Decision Problems"
    good = make_pdf("CLASSES OF RECURSIVELY ENUMERABLE SETS AND THEIR DECISION PROBLEMS by H. G. Rice " + "word " * 80)
    other = make_pdf("A Latent Variable Model Approach to PMI-based Word Embeddings " + "word " * 80)
    assert fr.check_pdf(good, title, trusted=False)[0]
    assert not fr.check_pdf(other, title, trusted=True)[0]
    assert not fr.check_pdf(b"<html>not a pdf</html>" * 100, title, trusted=True)[0]


def test_scan_is_accepted_only_from_a_trusted_source():
    scan = make_pdf("")  # no text layer
    assert fr.check_pdf(scan, "Some Title Here", trusted=True)[0]
    assert not fr.check_pdf(scan, "Some Title Here", trusted=False)[0]


def test_no_bib_file_is_reported_and_nothing_is_created(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["fetch_references.py", "--bib", str(tmp_path / "absent.bib"),
                                      "--references-dir", str(tmp_path / "refs")])
    assert fr.main() == 0
    assert "No BibTeX file" in capsys.readouterr().out
    assert not (tmp_path / "refs").exists()


def test_end_to_end_with_stubbed_download(tmp_path, monkeypatch, capsys):
    bib = tmp_path / "references.bib"
    bib.write_text(BIB, encoding="utf-8")
    refs = tmp_path / "references"
    pdf = make_pdf("CLASSES OF RECURSIVELY ENUMERABLE SETS AND THEIR DECISION PROBLEMS " + "word " * 80)
    monkeypatch.setattr(fr, "download", lambda e: (pdf, "stub") if e["key"] == "rice1953classes" else None)
    monkeypatch.setattr(sys, "argv", ["fetch_references.py", "--bib", str(bib), "--references-dir", str(refs), "--no-index"])
    (refs).mkdir()
    (refs / "1948_shannon.pdf").write_bytes(b"%PDF-")
    assert fr.main() == 0
    out = capsys.readouterr().out
    assert "Downloaded 1, still missing 1" in out and "noFileField" in out
    assert (refs / "1953_rice_classes_recursively_enumerable_sets_decision.pdf").is_file()
    assert "file     = {1953_rice_classes_recursively_enumerable_sets.pdf}" in bib.read_text() or \
        "1953_rice_classes_recursively_enumerable_sets_decision.pdf" in bib.read_text()
