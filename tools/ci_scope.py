#!/usr/bin/env python3
"""Decide which CI lanes a pull request has to run.

The V3 lanes in ``.github/workflows/ci.yml`` build the V3.5 compiler, the
native CLI and Hangar, then run their contracts on Linux, macOS and Windows.
None of those lanes read the V4 crates, the V4 fixtures or the V4 harnesses,
so a pull request that only touches those files cannot change their result.
Such a pull request skips the V3 lanes; every merge queue group still runs
them.

Pull requests run the V3 lanes on Linux only. macOS and Windows runners are
the scarcest (the account shares 20 concurrent jobs, 5 of them macOS), and a
pull request is pushed many times before it lands, so the macOS and Windows
lanes run once per change, in the merge queue group, which tests the exact
commit that lands on ``main``. A manual ``workflow_dispatch`` run also gets
every platform.

This is fail-closed: any path outside the V4-only list below, a rename out of
it, an unreadable file list or a truncated one keeps the V3 lanes on.

Usage::

    python tools/ci_scope.py --event pull_request --files changed.txt
    python tools/ci_scope.py --event push

``--files`` holds one repository path per line (both sides of a rename).
The decision is printed and, under GitHub Actions, written to
``$GITHUB_OUTPUT`` as ``v3=true`` or ``v3=false``, plus ``v3_os`` (the JSON
list of hosted runners for the V3 build-and-test matrix) and ``windows``
(``true`` when the Windows V3 lanes run).
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import sys
from pathlib import Path

# Paths whose changes cannot affect the V3 lanes. Keep this list narrow: a
# file belongs here only if nothing ci.yml runs (tests, the CLI source
# manifest, the installer, the release gate) reads it. Notably NOT here:
# src/compiler/v4/tools/** (the CLI manifest compiles preview_protocol.fk),
# src/compiler/v4/native-runtime.manifest (installed by the V3 CLI),
# src/compiler/v4/bootstrap.* and v35_seed.py, freakc/**, std/**, tools/**.
V4_ONLY_PATTERNS: tuple[str, ...] = (
    "src/compiler/v4/crates/*",
    "src/compiler/v4/tests/*",
    "src/compiler/v4/examples/*",
    "src/compiler/v4/*.md",
    "src/compiler/v4/check_v4.py",
    "src/compiler/v4/build_v4.py",
    "src/compiler/v4/build_lsp.py",
    "src/compiler/v4/self_host.py",
    "tests/v4_*",
    "tests/test_v4_*.py",
    "benchmarks/v4/*",
    "v4_scale_bench.py",
    "freak-full-bible.md",
    "freak-conformance-audit.md",
    ".github/workflows/v4-ci.yml",
    ".github/workflows/v4-locked-bootstrap.yml",
)

# The pull request files API stops listing at 3000 entries.
FILE_LIST_LIMIT = 3000


def is_v4_only(path: str) -> bool:
    normalized = path.strip().replace("\\", "/")
    if not normalized or normalized.startswith("/") or ".." in normalized.split("/"):
        return False
    # fnmatch's "*" also crosses "/", so "dir/*" covers the whole subtree.
    return any(fnmatch.fnmatchcase(normalized, pattern) for pattern in V4_ONLY_PATTERNS)


def needs_v3(event: str, paths: list[str] | None) -> tuple[bool, str]:
    if event != "pull_request":
        return True, f"event {event!r} always runs the V3 lanes"
    if paths is None:
        return True, "changed-file list unavailable"
    files = [path.strip() for path in paths if path.strip()]
    if not files:
        return True, "changed-file list is empty"
    if len(files) >= FILE_LIST_LIMIT:
        return True, f"changed-file list may be truncated ({len(files)} entries)"
    outside = [path for path in files if not is_v4_only(path)]
    if outside:
        shown = ", ".join(outside[:5]) + (" ..." if len(outside) > 5 else "")
        return True, f"{len(outside)} changed path(s) outside the V4-only set: {shown}"
    return False, f"all {len(files)} changed path(s) are V4-only"


# Every platform the V3 build-and-test matrix knows. Windows has its own
# bootstrap and suite jobs in ci.yml.
FULL_V3_OS: tuple[str, ...] = ("ubuntu-latest", "macos-latest")
PULL_REQUEST_V3_OS: tuple[str, ...] = ("ubuntu-latest",)


def platforms(event: str) -> tuple[list[str], bool, str]:
    """Return (V3 matrix runners, run the Windows lanes?, reason)."""
    if event == "pull_request":
        return (
            list(PULL_REQUEST_V3_OS),
            False,
            "pull request: Linux only; macOS and Windows run in the merge queue",
        )
    return list(FULL_V3_OS), True, f"event {event!r} runs every platform"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--event", required=True)
    parser.add_argument("--files", type=Path)
    args = parser.parse_args(argv)

    paths: list[str] | None = None
    if args.files is not None:
        try:
            paths = args.files.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            print(f"ci-scope: cannot read {args.files}: {exc}", file=sys.stderr)
            paths = None

    v3, reason = needs_v3(args.event, paths)
    value = "true" if v3 else "false"
    print(f"ci-scope: v3={value} ({reason})")
    v3_os, windows, platform_reason = platforms(args.event)
    v3_os_json = json.dumps(v3_os, separators=(",", ":"))
    windows_value = "true" if windows else "false"
    print(f"ci-scope: v3_os={v3_os_json} windows={windows_value} ({platform_reason})")
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write(f"v3={value}\n")
            handle.write(f"v3_os={v3_os_json}\n")
            handle.write(f"windows={windows_value}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
