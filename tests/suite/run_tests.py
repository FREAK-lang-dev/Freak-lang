#!/usr/bin/env python3
"""
FREAK Lite / Python Bootstrap Regression Test Suite
====================================================

Discovers test_*.fk files in the same directory, compiles and runs each one,
then compares actual output to the expected output declared in the file header.
This suite exercises ``python -m freakc``; it is not the self-hosted V3
preservation oracle. Use ``tests/v3_legacy_golden.py`` for that contract.

CI integration -- add to .github/workflows/ci.yml:

    - name: Run regression tests
      run: python tests/suite/run_tests.py

Or run manually from the repo root:

    python tests/suite/run_tests.py

Header directives (must appear as comments at the top of each .fk file):

    -- EXPECT: line of expected output
    -- EXPECT: another line
    -- EXPECT_COMPILE_ERROR: pattern to match in compile error output
    -- SKIP: reason this test is skipped

A test with EXPECT lines will be compiled AND run; actual stdout is compared
line-by-line against the expected output.

A test with EXPECT_COMPILE_ERROR is expected to FAIL compilation, and the
given pattern must appear somewhere in the compiler's stderr/diagnostics.

A test with SKIP will be reported as skipped and not executed.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


# ---------------------------------------------------------------------------
# Colour helpers (disabled when stdout is not a terminal or NO_COLOR is set)
# ---------------------------------------------------------------------------

def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

_COLOR = _supports_color()

def _green(msg: str) -> str:
    return f"\033[92m{msg}\033[0m" if _COLOR else msg

def _red(msg: str) -> str:
    return f"\033[91m{msg}\033[0m" if _COLOR else msg

def _yellow(msg: str) -> str:
    return f"\033[93m{msg}\033[0m" if _COLOR else msg

def _dim(msg: str) -> str:
    return f"\033[90m{msg}\033[0m" if _COLOR else msg

def _bold(msg: str) -> str:
    return f"\033[1m{msg}\033[0m" if _COLOR else msg


# ---------------------------------------------------------------------------
# Parse test directives from .fk file header
# ---------------------------------------------------------------------------

def parse_directives(fk_path: Path) -> dict:
    """Read EXPECT / EXPECT_COMPILE_ERROR / SKIP from comment headers."""
    result: dict = {
        "expect_lines": [],
        "expect_compile_error": None,
        "skip": None,
    }
    text = fk_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("--"):
            # Stop scanning once we hit a non-comment, non-blank line
            if stripped:
                break
            continue
        comment_body = stripped[2:].strip()
        if comment_body.startswith("EXPECT_COMPILE_ERROR:"):
            result["expect_compile_error"] = comment_body[len("EXPECT_COMPILE_ERROR:"):].strip()
        elif comment_body.startswith("EXPECT:"):
            result["expect_lines"].append(comment_body[len("EXPECT:"):].strip())
        elif comment_body.startswith("SKIP:"):
            result["skip"] = comment_body[len("SKIP:"):].strip()
    return result


# ---------------------------------------------------------------------------
# Run a single test
# ---------------------------------------------------------------------------

def run_test(fk_path: Path, repo_root: Path) -> str:
    """
    Returns one of: "pass", "fail", "skip", "error".
    Prints details inline.
    """
    directives = parse_directives(fk_path)

    # --- SKIP ---
    if directives["skip"]:
        print(f"  {_yellow('SKIP')}  {fk_path.name}: {directives['skip']}")
        return "skip"

    # Determine output binary path (place in same dir as the .fk file)
    if sys.platform == "win32":
        out_bin = fk_path.with_suffix(".exe")
    else:
        out_bin = fk_path.with_suffix("")

    # The C emitter writes <original>.c, so for test_hello.fk it becomes test_hello.c
    out_c = fk_path.with_suffix(".c")

    # --- COMPILE ---
    compile_cmd = [
        sys.executable, "-m", "freakc", "build", str(fk_path),
        "-o", str(out_bin), "--keep-c",
    ]
    try:
        compile_result = subprocess.run(
            compile_cmd,
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        print(f"  {_red('FAIL')}  {fk_path.name}: compilation timed out (60s)")
        return "fail"
    except FileNotFoundError:
        print(f"  {_red('ERR')}   {fk_path.name}: Python interpreter not found")
        return "error"

    # --- EXPECT_COMPILE_ERROR ---
    if directives["expect_compile_error"]:
        pattern = directives["expect_compile_error"]
        combined_output = compile_result.stdout + "\n" + compile_result.stderr
        if compile_result.returncode == 0:
            print(f"  {_red('FAIL')}  {fk_path.name}: expected compile error but compilation succeeded")
            _cleanup(out_bin, out_c)
            return "fail"
        if pattern.lower() in combined_output.lower():
            print(f"  {_green('PASS')}  {fk_path.name} (compile error matched)")
            _cleanup(out_bin, out_c)
            return "pass"
        else:
            print(f"  {_red('FAIL')}  {fk_path.name}: compile error did not match pattern")
            print(f"         Expected pattern: {pattern}")
            trimmed = combined_output.strip()[:400]
            for el in trimmed.splitlines()[:8]:
                print(f"         | {el}")
            _cleanup(out_bin, out_c)
            return "fail"

    # --- Normal test: should compile successfully ---
    if compile_result.returncode != 0:
        print(f"  {_red('FAIL')}  {fk_path.name}: compilation failed")
        err_output = (compile_result.stderr or compile_result.stdout).strip()
        if err_output:
            for err_line in err_output.splitlines()[:10]:
                print(f"         {err_line}")
        _cleanup(out_bin, out_c)
        return "fail"

    # --- RUN ---
    if not out_bin.exists():
        print(f"  {_red('FAIL')}  {fk_path.name}: binary not found at {out_bin}")
        _cleanup(out_bin, out_c)
        return "fail"

    try:
        run_result = subprocess.run(
            [str(out_bin)],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        print(f"  {_red('FAIL')}  {fk_path.name}: execution timed out (30s)")
        _cleanup(out_bin, out_c)
        return "fail"

    actual_lines = run_result.stdout.rstrip("\n").splitlines() if run_result.stdout.strip() else []
    expected_lines = directives["expect_lines"]

    # --- Compare output ---
    if not expected_lines:
        # No EXPECT lines: just check it ran without crashing (exit code 0)
        if run_result.returncode != 0:
            print(f"  {_red('FAIL')}  {fk_path.name}: exited with code {run_result.returncode}")
            if run_result.stderr.strip():
                for sl in run_result.stderr.strip().splitlines()[:5]:
                    print(f"         {sl}")
            _cleanup(out_bin, out_c)
            return "fail"
        print(f"  {_green('PASS')}  {fk_path.name} (ran without error)")
        _cleanup(out_bin, out_c)
        return "pass"

    ok = True
    if len(actual_lines) != len(expected_lines):
        ok = False
    else:
        for actual, expected in zip(actual_lines, expected_lines):
            if actual.strip() != expected.strip():
                ok = False
                break

    if ok:
        print(f"  {_green('PASS')}  {fk_path.name}")
    else:
        print(f"  {_red('FAIL')}  {fk_path.name}: output mismatch")
        max_show = max(len(expected_lines), len(actual_lines))
        diff_count = 0
        for i in range(min(max_show, 30)):
            exp = expected_lines[i].strip() if i < len(expected_lines) else "<missing>"
            act = actual_lines[i].strip() if i < len(actual_lines) else "<missing>"
            if exp != act:
                diff_count += 1
                if diff_count <= 10:
                    print(f"         line {i+1}:")
                    print(f"           expected: {exp}")
                    print(f"           actual:   {act}")
        if len(actual_lines) != len(expected_lines):
            print(f"         (expected {len(expected_lines)} lines, got {len(actual_lines)})")
        if diff_count > 10:
            print(f"         ... and {diff_count - 10} more mismatches")

    _cleanup(out_bin, out_c)
    return "pass" if ok else "fail"


def _cleanup(*paths: Path) -> None:
    """Remove build artifacts to keep the suite directory clean."""
    for p in paths:
        try:
            if p.exists():
                p.unlink()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Main driver
# ---------------------------------------------------------------------------

def main() -> int:
    # Determine paths
    """
    Run the FREAK Lite/Python Bootstrap regression test suite.
    
    Returns:
    	int: `1` if any tests fail or encounter errors, otherwise `0`.
    """
    suite_dir = Path(__file__).resolve().parent
    repo_root = suite_dir.parent.parent  # tests/suite -> tests -> repo root

    print(_bold("FREAK Lite / Python Bootstrap Regression Test Suite"))
    print(f"Suite directory: {suite_dir}")
    print(f"Repo root:       {repo_root}")
    print()

    # Discover tests
    test_files = sorted(suite_dir.glob("test_*.fk"))
    if not test_files:
        print(_yellow("No test_*.fk files found in suite directory."))
        return 0

    print(f"Found {len(test_files)} test(s).\n")

    passed = 0
    failed = 0
    skipped = 0
    errors = 0

    start = time.time()

    for fk_path in test_files:
        try:
            outcome = run_test(fk_path, repo_root)
        except Exception as exc:
            print(f"  {_red('ERR')}   {fk_path.name}: {exc}")
            outcome = "error"

        if outcome == "pass":
            passed += 1
        elif outcome == "fail":
            failed += 1
        elif outcome == "skip":
            skipped += 1
        else:
            errors += 1

    elapsed = time.time() - start

    # --- Summary ---
    print()
    print("=" * 50)
    total = passed + failed + skipped + errors
    parts = []
    parts.append(_green(f"{passed} passed"))
    if failed:
        parts.append(_red(f"{failed} failed"))
    else:
        parts.append("0 failed")
    if skipped:
        parts.append(_yellow(f"{skipped} skipped"))
    if errors:
        parts.append(_red(f"{errors} errors"))
    print(f"  {', '.join(parts)} / {total} total  ({elapsed:.1f}s)")
    print("=" * 50)

    if failed or errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
