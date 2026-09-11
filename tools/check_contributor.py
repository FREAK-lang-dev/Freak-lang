#!/usr/bin/env python3
"""Fast local contributor gate for FREAK.

Runs in seconds with no compiler build, no network, and no test harness.
It checks the contributor-facing surface only:

  1. Python syntax of the bootstrap-adjacent sources (freakc/, tools/).
  2. Presence of the required contributor files.
  3. README honesty markers (V3 ships self-hosted, hardened, NOT stable).
  4. CONTRIBUTING pointers to the label scheme and this gate.

Usage:
    python -u tools/check_contributor.py

Exit 0 when every check passes, 1 otherwise (failures listed on stdout).
Documented in CONTRIBUTING.md ("Fast Local Gate").
"""

from __future__ import annotations

import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SYNTAX_DIRS = (ROOT / "freakc", ROOT / "tools")

REQUIRED_FILES = (
    "README.md",
    "CONTRIBUTING.md",
    "CODEOWNERS",
    "AUTHORS.md",
    "DOCUMENTATION_AUTHORITY.md",
    ".github/labels.yml",
)

# (path, marker) pairs that must be present for the contributor docs to be
# considered intact. Markers are stable contract strings, not prose quotes.
CONTENT_MARKERS = (
    ("README.md", "actively hardened"),
    ("README.md", "not stable"),
    ("CONTRIBUTING.md", ".github/labels.yml"),
    ("CONTRIBUTING.md", "tools/check_contributor.py"),
)


def check_syntax(errors: list[str]) -> None:
    """Append syntax errors found in contributor-maintained Python trees."""
    for base in SYNTAX_DIRS:
        if not base.is_dir():
            errors.append(f"missing source dir: {base.relative_to(ROOT)}")
            continue
        for path in sorted(base.rglob("*.py")):
            try:
                py_compile.compile(str(path), doraise=True)
            except py_compile.PyCompileError as exc:
                errors.append(f"python syntax: {exc}")


def check_required_files(errors: list[str]) -> None:
    """Append errors for missing contributor-contract files."""
    for name in REQUIRED_FILES:
        if not (ROOT / name).is_file():
            errors.append(f"missing required file: {name}")


def check_content_markers(errors: list[str]) -> None:
    """Append errors for missing stable contributor documentation markers."""
    for name, marker in CONTENT_MARKERS:
        path = ROOT / name
        if not path.is_file():
            continue  # already reported above
        if marker not in path.read_text(encoding="utf-8"):
            errors.append(f"{name} is missing marker: {marker!r}")


def main() -> int:
    """Run contributor structure checks and return a process status."""
    errors: list[str] = []
    check_syntax(errors)
    check_required_files(errors)
    check_content_markers(errors)
    if errors:
        print("check_contributor: FAIL")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("check_contributor: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
