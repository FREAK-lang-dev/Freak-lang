#!/usr/bin/env python3
"""Differential gate for the V3.5 LLVM IRBuilder backend.

Every program is built twice with the same `freak`: once through the
in-process IRBuilder (the 0.16.0 default) and once with `--llvm-text`. Both
binaries run with empty stdin and their stdout, stderr and exit status must
match exactly.

The gate fails when
  * a builder build fails where the text build succeeds,
  * the bridge reports an error and the build fell back to text IR,
  * the two binaries behave differently, or
  * more modules than --max-fallbacks needed the text fallback (a lowering
    without a builder form).

Programs whose text build fails, or whose text binary times out, are reported
and skipped: they say nothing about the builder. NONDETERMINISTIC programs are
built both ways but not run ("built only"). The gate also fails when no program
was compared at run time.

Usage:
  python3 tests/v3_irbuilder_differential.py --freak <installed>/bin/freak \
      [--jobs N] [--max-fallbacks N] [--extra DIR ...] [PROGRAM.fk ...]
"""

from __future__ import annotations

import argparse
import concurrent.futures
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GLOBS = (
    "tests/suite/*.fk",
    "tests/v3_legacy/golden/*.fk",
    "tests/*.fk",
)
# Programs whose output legitimately differs run to run (network echoes,
# wall-clock timings). They are still built both ways; only the run is skipped.
NONDETERMINISTIC = {
    "tests/http_test.fk",
    "tests/speed_benchmark.fk",
}
BUILD_TIMEOUT = 600
RUN_TIMEOUT = 20


def corpus(extra: list[str], explicit: list[str]) -> list[Path]:
    if explicit:
        return [Path(p).resolve() for p in explicit]
    found: list[Path] = []
    for pattern in DEFAULT_GLOBS:
        found.extend(sorted(ROOT.glob(pattern)))
    for directory in extra:
        base = Path(directory).resolve()
        found.extend(sorted(base.glob("*.fk")))
        found.extend(sorted(base.glob("tests/*.fk")))
        found.extend(sorted(base.glob("examples/*.fk")))
    return found


def build(freak: str, source: Path, output: Path, text: bool) -> tuple[bool, str]:
    command = [freak, "build", source.name, "-o", str(output)]
    if text:
        command.append("--llvm-text")
    env = dict(os.environ)
    env["FREAK_IRBUILDER_TRACE"] = "1"
    env.setdefault("NO_COLOR", "1")
    try:
        done = subprocess.run(command, cwd=source.parent, env=env, capture_output=True,
                              text=True, errors="replace", timeout=BUILD_TIMEOUT)
    except subprocess.TimeoutExpired:
        return False, "build timed out"
    log = done.stdout + done.stderr
    return done.returncode == 0 and output.exists(), log


def trace(log: str) -> str:
    for line in log.splitlines():
        line = line.strip()
        if line.startswith("irbuilder: "):
            return line[len("irbuilder: "):]
    return "(no trace)"


def run(binary: Path) -> tuple[bytes, bytes, int] | None:
    # The caller hands over a binary copied alone into a fresh directory, so
    # both runs start from identical (empty) working directories and cannot
    # see each other's files or the build's leftovers.
    try:
        done = subprocess.run([str(binary)], cwd=binary.parent, stdin=subprocess.DEVNULL,
                              capture_output=True, timeout=RUN_TIMEOUT)
    except subprocess.TimeoutExpired:
        return None
    return done.stdout, done.stderr, done.returncode


def shown(data: bytes) -> str:
    return data.decode("utf-8", "backslashreplace")


def check(freak: str, source: Path, scratch: Path) -> dict:
    label = source.relative_to(ROOT).as_posix() if source.is_relative_to(ROOT) else str(source)
    work = Path(tempfile.mkdtemp(prefix="ib-", dir=scratch))
    copy_root = work / "src"
    project = next((d for d in [source.parent, *source.parent.parents][:3] if (d / "hangar.toml").exists()), None)
    if project is not None:
        shutil.copytree(project, copy_root, ignore=shutil.ignore_patterns(
            "hangar_modules", "hangar_cache", ".git", "*.ll", "*.obj", "*.o"))
        local = copy_root / source.relative_to(project)
    else:
        copy_root.mkdir()
        shutil.copy2(source, copy_root / source.name)
        local = copy_root / source.name
    suffix = ".exe" if os.name == "nt" else ".bin"
    (work / "text").mkdir()
    (work / "ib").mkdir()
    text_bin = work / "text" / f"program{suffix}"
    ib_bin = work / "ib" / f"program{suffix}"
    result = {"program": label}

    text_ok, text_log = build(freak, local, text_bin, text=True)
    if not text_ok:
        result["status"] = "skip"
        result["reason"] = "text build fails"
        return result
    ib_ok, ib_log = build(freak, local, ib_bin, text=False)
    path = trace(ib_log)
    result["path"] = path
    if not ib_ok:
        result["status"] = "fail"
        result["reason"] = "builder build failed:\n" + ib_log[-3000:]
        return result
    if path.startswith("text (IRBuilder:"):
        result["status"] = "fail"
        result["reason"] = "bridge error, fell back to text: " + path
        return result

    if label in NONDETERMINISTIC:
        result["status"] = "fallback" if path != "irbuilder" else "built"
        shutil.rmtree(work, ignore_errors=True)
        return result
    def staged(binary: Path, name: str) -> Path:
        place = work / name
        place.mkdir()
        return Path(shutil.copy2(binary, place / binary.name))

    text_run = run(staged(text_bin, "run-text"))
    if text_run is None:
        result["status"] = "skip"
        result["reason"] = "text binary timed out"
        return result
    ib_run = run(staged(ib_bin, "run-ib"))
    if ib_run is None:
        result["status"] = "fail"
        result["reason"] = "builder binary timed out, text binary did not"
        return result
    if ib_run != text_run:
        result["status"] = "fail"
        result["reason"] = (
            "behavior differs\n--- text (exit %d)\n%s%s\n--- irbuilder (exit %d)\n%s%s"
            % (text_run[2], shown(text_run[0][-1500:]), shown(text_run[1][-500:]),
               ib_run[2], shown(ib_run[0][-1500:]), shown(ib_run[1][-500:])))
        return result
    result["status"] = "fallback" if path != "irbuilder" else "pass"
    shutil.rmtree(work, ignore_errors=True)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--freak", required=True, help="freak binary inside an installed layout")
    parser.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    parser.add_argument("--max-fallbacks", type=int, default=0)
    parser.add_argument("--extra", action="append", default=[], help="extra directory of .fk programs")
    parser.add_argument("programs", nargs="*")
    args = parser.parse_args()

    freak = str(Path(args.freak).resolve())
    programs = corpus(args.extra, args.programs)
    scratch = Path(tempfile.mkdtemp(prefix="freak-ib-diff-"))
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for result in pool.map(lambda p: check(freak, p, scratch), programs):
            results.append(result)
            mark = {"pass": "ok  ", "built": "bld ", "fallback": "text", "skip": "skip",
                    "fail": "FAIL"}[result["status"]]
            print(f"{mark}  {result['program']}" + (f"  [{result.get('reason') or result.get('path')}]" if result["status"] in ("skip", "fallback") else ""), flush=True)

    passed = [r for r in results if r["status"] == "pass"]
    built = [r for r in results if r["status"] == "built"]
    fallbacks = [r for r in results if r["status"] == "fallback"]
    skipped = [r for r in results if r["status"] == "skip"]
    failed = [r for r in results if r["status"] == "fail"]
    for r in failed:
        print(f"\n==== FAIL {r['program']}\n{r['reason']}")
    print(f"\nIRBuilder differential: {len(passed)} identical, {len(built)} built only, "
          f"{len(fallbacks)} text fallback, {len(skipped)} skipped, {len(failed)} failed")
    if not failed:
        shutil.rmtree(scratch, ignore_errors=True)
    if failed:
        return 1
    if len(fallbacks) > args.max_fallbacks:
        print(f"too many text fallbacks: {len(fallbacks)} > {args.max_fallbacks}")
        return 1
    if not passed:
        print("no program was compared at run time")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
