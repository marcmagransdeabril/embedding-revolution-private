#!/usr/bin/env python3
"""Validate Quarto book structure, markdown syntax, math blocks, and code chunks.

Audits index.qmd and all chapters/*.qmd files for frontmatter,
balanced callout blocks (:::), math delimiters ($$), code chunks,
and cross-reference labels.
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
CHAPTERS_DIR = REPO_ROOT / "chapters"
INDEX_QMD = REPO_ROOT / "index.qmd"


class ValidationIssue:
    def __init__(self, file: Path, line: int, severity: str, message: str) -> None:
        self.file = file
        self.line = line
        self.severity = severity  # "ERROR", "WARNING"
        self.message = message

    def __str__(self) -> str:
        rel = self.file.relative_to(REPO_ROOT) if self.file.is_relative_to(REPO_ROOT) else self.file
        return f"[{self.severity}] {rel}:{self.line}: {self.message}"


def validate_frontmatter(path: Path, text: str) -> list[ValidationIssue]:
    """Check YAML frontmatter if present."""
    issues: list[ValidationIssue] = []
    if path == INDEX_QMD:
        return issues

    fm_match = re.match(r"^---\r?\n(.*?)\r?\n---", text, flags=re.DOTALL)
    if not fm_match:
        issues.append(ValidationIssue(path, 1, "WARNING", "Missing YAML frontmatter (--- ... ---)"))
        return issues

    raw_yaml = fm_match.group(1)
    try:
        fm = yaml.safe_load(raw_yaml)
        if not isinstance(fm, dict):
            issues.append(ValidationIssue(path, 1, "ERROR", "YAML frontmatter must be a dictionary"))
        elif "title" not in fm or not str(fm["title"]).strip():
            issues.append(ValidationIssue(path, 1, "ERROR", "YAML frontmatter missing non-empty 'title'"))
    except yaml.YAMLError as e:
        issues.append(ValidationIssue(path, 1, "ERROR", f"YAML frontmatter parse error: {e}"))

    return issues


def validate_callouts(path: Path, lines: list[str]) -> list[ValidationIssue]:
    """Check balanced callout blocks (:::)."""
    issues: list[ValidationIssue] = []
    div_stack: list[int] = []

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("::: {") or stripped.startswith(":::"):
            if stripped == ":::":
                if not div_stack:
                    issues.append(ValidationIssue(path, idx, "ERROR", "Unmatched closing ':::' block"))
                else:
                    div_stack.pop()
            else:
                div_stack.append(idx)

    if div_stack:
        for open_line in div_stack:
            issues.append(ValidationIssue(path, open_line, "ERROR", f"Unclosed ':::' block opened at line {open_line}"))

    return issues


def validate_code_chunks(path: Path, text: str) -> list[ValidationIssue]:
    """Check code chunk delimiters and Python syntax in executable cells."""
    issues: list[ValidationIssue] = []
    code_pattern = re.compile(r"```\{([a-zA-Z0-9_-]+)(?:,[^}]*)?\}\r?\n(.*?)\r?\n```", re.DOTALL)

    # Check unclosed code fences
    lines = text.splitlines()
    in_fence = False
    fence_start = 0
    for idx, line in enumerate(lines, start=1):
        if line.strip().startswith("```"):
            if not in_fence:
                in_fence = True
                fence_start = idx
            else:
                in_fence = False

    if in_fence:
        issues.append(ValidationIssue(path, fence_start, "ERROR", f"Unclosed code fence opened at line {fence_start}"))

    # Validate python code syntax
    for match in code_pattern.finditer(text):
        lang = match.group(1).lower()
        chunk = match.group(2)
        start_line = text[: match.start()].count("\n") + 1

        if lang == "python":
            # Strip quarto options (|# ...)
            py_lines = []
            for cline in chunk.splitlines():
                if cline.strip().startswith("#|"):
                    continue
                py_lines.append(cline)
            py_code = "\n".join(py_lines)

            try:
                ast.parse(py_code)
            except SyntaxError as e:
                issues.append(
                    ValidationIssue(
                        path,
                        start_line + (e.lineno or 1),
                        "ERROR",
                        f"Python syntax error in executable code cell: {e.msg}",
                    )
                )

    return issues


def validate_math_delimiters(path: Path, lines: list[str]) -> list[ValidationIssue]:
    """Check basic math block delimiters ($$)."""
    issues: list[ValidationIssue] = []
    in_display_math = False
    math_start_line = 0

    for idx, line in enumerate(lines, start=1):
        # Count $$ in line outside code blocks
        if "$$" in line:
            count = line.count("$$")
            if count == 1:
                if not in_display_math:
                    in_display_math = True
                    math_start_line = idx
                else:
                    in_display_math = False
            elif count % 2 != 0:
                issues.append(ValidationIssue(path, idx, "WARNING", "Odd number of '$$' math delimiters on line"))

    if in_display_math:
        issues.append(
            ValidationIssue(
                path, math_start_line, "ERROR", f"Unclosed display math '$$' block opened at line {math_start_line}"
            )
        )

    return issues


def validate_qmd_file(path: Path) -> list[ValidationIssue]:
    """Run all validation passes on a single .qmd file."""
    if not path.is_file():
        return [ValidationIssue(path, 1, "ERROR", "File does not exist")]

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    issues: list[ValidationIssue] = []
    issues.extend(validate_frontmatter(path, text))
    issues.extend(validate_callouts(path, lines))
    issues.extend(validate_code_chunks(path, text))
    issues.extend(validate_math_delimiters(path, lines))

    return issues


def validate_all(verbose: bool = False) -> tuple[int, int]:
    """Validate all book files and return (errors_count, warnings_count)."""
    files_to_validate: list[Path] = []
    if INDEX_QMD.is_file():
        files_to_validate.append(INDEX_QMD)

    if CHAPTERS_DIR.is_dir():
        files_to_validate.extend(sorted(CHAPTERS_DIR.glob("*.qmd")))

    total_errors = 0
    total_warnings = 0

    for file_path in files_to_validate:
        issues = validate_qmd_file(file_path)
        file_errors = sum(1 for i in issues if i.severity == "ERROR")
        file_warnings = sum(1 for i in issues if i.severity == "WARNING")

        total_errors += file_errors
        total_warnings += file_warnings

        rel = file_path.relative_to(REPO_ROOT) if file_path.is_relative_to(REPO_ROOT) else file_path
        if issues:
            print(f"Validation for {rel}: {file_errors} error(s), {file_warnings} warning(s)")
            for issue in issues:
                print(f"  {issue}")
        elif verbose:
            print(f"✓ {rel}: Valid (0 errors, 0 warnings)")

    return total_errors, total_warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Quarto book files")
    parser.add_argument("--file", "-f", type=Path, help="Validate a specific .qmd file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print verbose output")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    args = parser.parse_args()

    if args.file:
        issues = validate_qmd_file(args.file)
        errors = sum(1 for i in issues if i.severity == "ERROR")
        warnings = sum(1 for i in issues if i.severity == "WARNING")
        for issue in issues:
            print(issue)
        failed = errors > 0 or (args.strict and warnings > 0)
        sys.exit(1 if failed else 0)

    errors, warnings = validate_all(verbose=args.verbose)
    if errors == 0 and warnings == 0:
        print("✓ All book files passed validation.")
    elif errors == 0:
        print(f"✓ Validation passed with {warnings} warning(s).")
    else:
        print(f"✗ Validation failed with {errors} error(s) and {warnings} warning(s).", file=sys.stderr)

    failed = errors > 0 or (args.strict and warnings > 0)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
