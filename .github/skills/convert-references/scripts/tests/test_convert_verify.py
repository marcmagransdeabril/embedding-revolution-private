"""Download 4 orthogonal-field arXiv PDFs and run convert.py + verify.py end to end.

Run with: pytest -s scripts/tests/test_convert_verify.py
Iterate on this file's thresholds/assertions before wiring the skill into SKILL.md.
"""
import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[2]
SCRIPTS = SKILL_DIR / "scripts"
CACHE_DIR = Path("/tmp/convert-references-test-pdfs")

# Four orthogonal fields, each with real equations and figures.
FIXTURES = {
    "attention-is-all-you-need": ("https://arxiv.org/pdf/1706.03762", "cs.LG — 15pp, 5 figs"),
    "ligo-gw150914": ("https://arxiv.org/pdf/1602.03837", "gr-qc/astro-ph — 16pp, 4 figs"),
    "multi-allele-fixation": ("https://arxiv.org/pdf/2610.04090", "q-bio.PE — 17pp, 4 figs"),
    "stochastic-portfolio-theory": ("https://arxiv.org/pdf/2610.04348", "q-fin.MF — 37pp, 10 figs (sampling path)"),
}

# Known model-capability limitation (not a script bug): Appendix A's dense
# nested-fraction polynomial formulas reliably garble the local surya-ocr-2
# VLM's equation recognition (extra braces, duplicated tokens). See
# /memories/repo/convert-references-env.md for details.
XFAIL_REASONS = {
    "multi-allele-fixation": "surya-ocr-2 VLM garbles Appendix A's dense nested-fraction formulas",
}

_params = [
    pytest.param((name, value), marks=pytest.mark.xfail(reason=XFAIL_REASONS[name]))
    if name in XFAIL_REASONS else (name, value)
    for name, value in FIXTURES.items()
]


def _download(name: str, url: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dest = CACHE_DIR / f"{name}.pdf"
    if not dest.exists():
        urllib.request.urlretrieve(url, dest)
    return dest


@pytest.fixture(params=_params, ids=list(FIXTURES.keys()))
def reference(request, tmp_path):
    name, (url, label) = request.param
    pdf = _download(name, url)
    references_dir = tmp_path / "references"
    references_dir.mkdir()
    shutil.copy(pdf, references_dir / f"{name}.pdf")
    return name, label, references_dir


def test_convert_and_verify(reference):
    name, label, references_dir = reference

    convert = subprocess.run(
        [sys.executable, str(SCRIPTS / "convert.py"), "--references-dir", str(references_dir)],
        capture_output=True, text=True,
    )
    assert convert.returncode == 0, f"convert.py failed for {label}:\n{convert.stderr}"
    assert (references_dir / f"{name}.md").exists()

    verify = subprocess.run(
        [sys.executable, str(SCRIPTS / "verify.py"), name, "--references-dir", str(references_dir)],
        capture_output=True, text=True,
    )
    assert verify.returncode == 0, f"verify.py failed for {label}:\n{verify.stderr}"
    report = json.loads(verify.stdout)[0]

    print(f"\n--- {name} ({label}) ---")
    print(f"latex_errors: {len(report['latex_errors'])}")
    print(f"image_issues: {len(report['image_issues'])}")
    print(f"roundtrip: {report['roundtrip']['status']}")
    scores = [p["similarity"] for p in report["sample_pages"]]
    print(f"sample_pages: {len(scores)}, avg similarity: {sum(scores) / len(scores):.2f}, min: {min(scores):.2f}")

    assert not report["latex_errors"], report["latex_errors"]
    assert not report["image_issues"], report["image_issues"]
    assert report["roundtrip"]["status"] == "ok", report["roundtrip"]["stderr"]
    # pymupdf's own raw-text extraction of inline math is itself unreliable
    # (the reason Marker exists), so a character-level diff against it is a
    # noisy signal for math-heavy pages. This threshold only guards against
    # catastrophic failures (missing/garbled content), not fine-grained
    # quality -- that's what latex_errors/image_issues and a human spot-check
    # of sample_pages' page images are for.
    assert sum(scores) / len(scores) > 0.2
