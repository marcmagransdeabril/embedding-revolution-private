"""Unit tests of check_pdf_overflow.py on small synthetic LaTeX logs."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_pdf_overflow as cpo  # noqa: E402

LOG = """This is XeTeX
[67]
File: figure.png Graphic file (type bmp)
<figure.png>

Overfull \\vbox (275.99127pt too high) has occurred while \\output is active []

[68] [69]
Overfull \\hbox (12.5pt too wide) in paragraph at lines 10--11
[]\\TU/x/m/n/10 some line that sticks out
[]

[70]
"""


def test_vertical_and_horizontal_overflows_are_found(tmp_path):
    log = tmp_path / "index.log"
    log.write_text(LOG)
    found = list(cpo.overflows(log))
    assert [round(f[0], 1) for f in found] == [276.0, 12.5]
    assert "does not fit" in found[0][3] and found[0][1] == 67  # the last page shipped out before it
    assert found[1][1] == 69


def test_main_fails_on_a_page_that_does_not_fit_and_passes_on_a_clean_log(tmp_path, monkeypatch, capsys):
    log = tmp_path / "index.log"
    log.write_text(LOG)
    monkeypatch.setattr(sys, "argv", ["check_pdf_overflow.py", "--log", str(log)])
    assert cpo.main() == 1
    assert "too high" in capsys.readouterr().err
    log.write_text("This is XeTeX\n[1] [2]\n")
    assert cpo.main() == 0
