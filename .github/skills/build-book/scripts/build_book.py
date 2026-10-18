#!/usr/bin/env python3
"""Build book in publishing formats (Springer 155x235mm, O'Reilly 7x9.1875in, HTML, EPUB).

CLI driver for Quarto book compilation with automatic environment
configuration (Python venv, TinyTeX path, format presets, validation).
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[4]
VENV_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"
TINYTEX_DIR = Path.home() / ".TinyTeX" / "bin" / "x86_64-linux"
OUTPUT_DIR = REPO_ROOT / "_book"


def get_build_env() -> dict[str, str]:
    """Prepare environment dictionary with TinyTeX on PATH and QUARTO_PYTHON set."""
    env = os.environ.copy()
    current_path = env.get("PATH", "")
    
    if TINYTEX_DIR.is_dir():
        env["PATH"] = f"{TINYTEX_DIR}:{current_path}"
    
    if VENV_PYTHON.is_file():
        env["QUARTO_PYTHON"] = str(VENV_PYTHON)

    return env


def clean_build_artifacts() -> None:
    """Remove previous build outputs."""
    for path in [REPO_ROOT / "_book", REPO_ROOT / "_freeze", REPO_ROOT / ".quarto"]:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
    for ext in ["*.tex", "*.html"]:
        for f in (REPO_ROOT / "chapters").glob(ext):
            f.unlink(missing_ok=True)


def run_command(cmd: Sequence[str], dry_run: bool = False, verbose: bool = False) -> bool:
    """Execute a CLI command within repository root."""
    cmd_str = " ".join(cmd)
    print(f"==> Running: {cmd_str}")
    if dry_run:
        return True

    env = get_build_env()
    res = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        env=env,
        capture_output=not verbose,
        text=True,
    )
    if res.returncode != 0:
        print(f"✗ Command failed with code {res.returncode}", file=sys.stderr)
        if not verbose and res.stderr:
            print(res.stderr, file=sys.stderr)
        return False
    return True


def render_format(
    target_format: str,
    output_dir: Path,
    no_execute: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> bool:
    """Render a specific book format."""
    quarto_bin = shutil.which("quarto") or "quarto"
    cmd = [quarto_bin, "render"]

    if target_format == "html":
        cmd.extend(["--to", "html"])
    elif target_format in ("pdf", "pdf-springer", "springer"):
        cmd.extend(["--to", "pdf", "--profile", "springer"])
    elif target_format in ("pdf-oreilly", "oreilly"):
        cmd.extend(["--to", "pdf", "--profile", "oreilly"])
    elif target_format == "epub":
        cmd.extend(["--to", "epub"])
    else:
        print(f"Unknown format: {target_format}", file=sys.stderr)
        return False

    if no_execute:
        cmd.append("--no-execute")

    if output_dir != OUTPUT_DIR:
        cmd.extend(["--output-dir", str(output_dir)])

    success = run_command(cmd, dry_run=dry_run, verbose=verbose)
    if not success:
        return False

    # Retain distinct format filenames if in standard output directory
    if not dry_run and output_dir == OUTPUT_DIR:
        default_pdf = OUTPUT_DIR / "The-Embedding-Revolution.pdf"
        if target_format in ("pdf-springer", "springer") and default_pdf.is_file():
            shutil.copy2(default_pdf, OUTPUT_DIR / "The-Embedding-Revolution-Springer.pdf")
        elif target_format in ("pdf-oreilly", "oreilly") and default_pdf.is_file():
            shutil.copy2(default_pdf, OUTPUT_DIR / "The-Embedding-Revolution-OReilly.pdf")

    return True


def inspect_outputs(target_format: str) -> None:
    """Print summary of generated files."""
    if not OUTPUT_DIR.is_dir():
        return

    print("\n📦 Build Artifacts Summary:")
    for item in sorted(OUTPUT_DIR.iterdir()):
        if item.is_file():
            size_kb = item.stat().st_size / 1024
            print(f"  • {item.name:<32} ({size_kb:.1f} KB)")


def build_book(
    fmt: str = "pdf-springer",
    output_dir: Path = OUTPUT_DIR,
    clean: bool = False,
    sync: bool = True,
    validate: bool = True,
    no_execute: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> bool:
    """Main build workflow."""
    print("======================================================================")
    print(f" Building Book: The Embedding Revolution [Format: {fmt}]")
    print("======================================================================")

    if clean:
        print("Cleaning previous build artifacts...")
        if not dry_run:
            clean_build_artifacts()

    # Step 1: Sync chapters
    if sync:
        from sync_chapters import sync_quarto_yml
        print("Syncing chapter registry...")
        if not sync_quarto_yml(dry_run=dry_run, verbose=verbose):
            return False

    # Step 2: Validate
    if validate:
        from validate_book import validate_all
        print("Validating chapter markdown...")
        errors, warnings = validate_all(verbose=verbose)
        if errors > 0:
            print(f"✗ Aborting build due to {errors} validation error(s).", file=sys.stderr)
            return False

    # Step 3: Render requested format(s)
    formats_to_build: list[str] = []
    if fmt == "all":
        formats_to_build = ["html", "pdf-springer", "pdf-oreilly", "epub"]
    elif fmt in ("pdf", "springer"):
        formats_to_build = ["pdf-springer"]
    elif fmt == "oreilly":
        formats_to_build = ["pdf-oreilly"]
    else:
        formats_to_build = [fmt]

    for f in formats_to_build:
        print(f"\n==> Building format: {f}")
        success = render_format(
            f,
            output_dir=output_dir,
            no_execute=no_execute,
            dry_run=dry_run,
            verbose=verbose,
        )
        if not success:
            print(f"✗ Failed to build format: {f}", file=sys.stderr)
            return False

    if not dry_run:
        inspect_outputs(fmt)

    print("\n✓ Book build completed successfully.")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Build The Embedding Revolution book")
    parser.add_argument(
        "--format",
        "-f",
        default="pdf-springer",
        choices=["all", "pdf", "pdf-springer", "springer", "pdf-oreilly", "oreilly", "html", "epub"],
        help="Target format (default: pdf-springer)",
    )
    parser.add_argument("--output-dir", "-o", type=Path, default=OUTPUT_DIR, help="Custom output directory")
    parser.add_argument("--clean", "-c", action="store_true", help="Clean artifacts before build")
    parser.add_argument("--no-sync", action="store_true", help="Skip chapter registry synchronization")
    parser.add_argument("--no-validate", action="store_true", help="Skip chapter validation")
    parser.add_argument("--no-execute", action="store_true", help="Skip Python cell execution (use cached outputs)")
    parser.add_argument("--dry-run", action="store_true", help="Show build steps without executing")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # Add script dir to sys.path so helper modules can be imported
    sys.path.insert(0, str(Path(__file__).resolve().parent))

    success = build_book(
        fmt=args.format,
        output_dir=args.output_dir,
        clean=args.clean,
        sync=not args.no_sync,
        validate=not args.no_validate,
        no_execute=args.no_execute,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
