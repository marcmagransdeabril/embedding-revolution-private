#!/usr/bin/env python3
"""Post-commit review nudge: never blocks a commit, asks for a review-doc pass afterwards.

Flow:
  1. You (or the model) commit test changes normally.
  2. On the next `shell` tool call, if commits since the last reviewed commit touched test
     files, this hook blocks that ONE call (exit 2) and tells the model to run review-doc on
     those commits and to put any fixes in a separate commit. It notifies once per pending
     review, so the review's own commands (git diff, make, ...) are never blocked.
  3. The model finishes by running `review_gate.py stamp`, which records HEAD as reviewed.

Usage:
  review_gate.py          preToolUse hook (hook event as JSON on stdin).
                          Exit 0 = allow, exit 2 = block (stderr goes to the model).
  review_gate.py stamp    record HEAD as reviewed.

A "test file" is a file under a `tests/` directory or named `test_*.py` / `*_test.py`.
State lives in tmp/.review-doc-state.json (gitignored).
"""

from __future__ import annotations

import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

STATE = Path("tmp/.review-doc-state.json")
COMMIT_RE = re.compile(r"\bgit\b[^;&|\n]*\bcommit\b")
SKILL = ".github/skills/review-doc/SKILL.md"


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, text=True)


def is_test(path: str) -> bool:
    parts = path.split("/")
    name = parts[-1]
    return (
        "tests" in parts[:-1]
        or fnmatch.fnmatch(name, "test_*.py")
        or fnmatch.fnmatch(name, "*_test.py")
    )


def load_state(head: str) -> dict:
    try:
        state = json.loads(STATE.read_text())
    except (OSError, json.JSONDecodeError):
        state = {}
    base = state.get("reviewed")
    valid = (
        base
        and git("rev-parse", "--verify", f"{base}^{{commit}}").returncode == 0
        and git("merge-base", "--is-ancestor", base, head).returncode == 0
    )
    if not valid:  # first run, or history rewritten: start from HEAD, never review history
        state = {"reviewed": head, "notified": None}
        save_state(state)
    return state


def save_state(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state) + "\n")


def main() -> int:
    head = git("rev-parse", "HEAD").stdout.strip()
    if not head:
        return 0  # no commits yet
    state = load_state(head)

    if len(sys.argv) > 1 and sys.argv[1] == "stamp":
        save_state({"reviewed": head, "notified": None})
        print(f"review-doc: HEAD {head[:9]} recorded as reviewed.")
        return 0

    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0  # unparsable event: never block on our own failure
    command = (event.get("tool_input") or {}).get("command", "")
    if COMMIT_RE.search(command) or "review_gate.py" in command:
        return 0  # commits and the stamp command always go through

    base = state["reviewed"]
    if base == head or state.get("notified") == base:
        return 0
    names = git("diff", "--name-only", f"{base}..{head}").stdout.splitlines()
    tests = sorted(p for p in names if is_test(p))
    if not tests:
        return 0

    state["notified"] = base  # notify once per pending review
    save_state(state)
    commits = git("log", "--oneline", f"{base}..{head}").stdout.strip()
    listing = "\n".join(f"  - {p}" for p in tests)
    print(
        "Test files were committed since the last review-doc pass. Your command was not "
        "run; run it again after starting the review.\n"
        f"Commits:\n{commits}\nTest files:\n{listing}\n\n"
        f"Read {SKILL} and run the review-doc skill now, with this scope already fixed "
        "(do not ask the user for it):\n"
        "  unit  = the test files listed above\n"
        f"  range = incremental, since commit {base[:9]} (git diff {base[:9]}..HEAD -- <files>)\n"
        "Keep the review strictly limited to this scope:\n"
        "  - Review only the changed hunks (plus the surrounding context needed to judge "
        "them). Do not review the rest of those files, other chapters, or the whole book.\n"
        "  - Edit only the changed hunks. Anything wrong outside them (including stale "
        "references elsewhere) is reported in the findings, never fixed.\n"
        "  - Running the existing build/test commands is fine; widening the review or "
        "editing outside the changes is not, unless the user explicitly asked for a "
        "larger scope in this conversation.\n"
        "Commits:\n"
        "  - Never amend or rewrite the commits above. Put review fixes in a NEW commit "
        "whose message starts with `review-doc:`, staging only the files you fixed "
        "(no `git add -A`), so the user can diff or revert the review separately.\n"
        "  - If there is nothing to fix, make no commit.\n"
        "When finished, run:\n"
        "  python3 .kiro/hooks/review_gate.py stamp\n"
        "and report the findings to the user.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
