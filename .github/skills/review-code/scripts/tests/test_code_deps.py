"""Unit tests of code_deps.py on a throw-away code/ tree."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import code_deps  # noqa: E402


@pytest.fixture()
def tree(tmp_path, monkeypatch):
    chapter = tmp_path / "code" / "ch"
    chapter.mkdir(parents=True)
    (tmp_path / "chapters").mkdir()
    (chapter / "utils.py").write_text("import numpy as np\n")
    (chapter / "a.py").write_text("from utils import x\n")
    (chapter / "b.py").write_text("import a\nimport pandas\n")
    (chapter / "c.py").write_text("import numpy\n\ndef check():\n    import torch\n")
    (tmp_path / "chapters" / "ch.qmd").write_text("Run `a.py`, `b.py` and `missing.py`.\n")
    monkeypatch.setattr(code_deps, "ROOT", tmp_path)
    monkeypatch.setattr(code_deps, "CODE", tmp_path / "code")
    monkeypatch.setattr(code_deps, "CHAPTERS", tmp_path / "chapters")
    return tmp_path


def test_dependencies_are_transitive(tree):
    deps = code_deps.make_deps()
    assert ".code-tests/ch/b.ok: code/ch/a.py code/ch/utils.py" in deps
    assert ".code-tests/ch/a.ok: code/ch/utils.py" in deps


def test_third_party_import_outside_the_list_is_reported_and_torch_is_allowed(tree):
    findings = "\n".join(code_deps.check())
    assert "b.py: imports 'pandas'" in findings
    assert "c.py: imports" not in findings


def test_chapter_naming_a_missing_script_is_reported_and_unnamed_scripts_are_not(tree):
    findings = "\n".join(code_deps.check())
    assert "names missing.py" in findings
    assert "no chapter names" not in findings


def test_a_data_file_named_in_a_string_is_a_dependency_of_the_scripts_that_import_the_module(tree):
    (tree / "code" / "ch" / "data").mkdir()
    (tree / "code" / "ch" / "data" / "x.zip").write_text("")
    (tree / "code" / "ch" / "data" / "unused.zip").write_text("")
    (tree / "code" / "ch" / "utils.py").write_text('from pathlib import Path\nZIP = Path(__file__).parent / "data" / "x.zip"\n')
    deps = code_deps.make_deps()
    assert ".code-tests/ch/a.ok: code/ch/data/x.zip code/ch/utils.py" in deps
    assert ".code-tests/ch/b.ok: code/ch/a.py code/ch/data/x.zip code/ch/utils.py" in deps
    assert "unused.zip" not in deps


def test_unused_and_missing_data_files_are_reported(tree):
    (tree / "code" / "ch" / "data").mkdir()
    (tree / "code" / "ch" / "data" / "unused.zip").write_text("")
    (tree / "code" / "ch" / "a.py").write_text('NAME = "gone.csv"\n')
    findings = "\n".join(code_deps.check_data())
    assert "unused.zip: no script names this data file" in findings
    assert "a.py: names the data file gone.csv" in findings


def test_makefile_dependencies_are_compared_with_the_imports(tree, monkeypatch):
    stamp = ".code-tests/ch/b.ok"
    monkeypatch.setattr(code_deps, "makefile_deps", lambda: {stamp: {"code/ch/b.py", "code/ch/utils.py"}})
    findings = "\n".join(code_deps.check_makefile())
    assert f"{stamp} does not depend on ['code/ch/a.py']" in findings
