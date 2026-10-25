#!/usr/bin/env python3
"""Check that V4 compiles itself to a fixed point (tier 2, stages 1 and 2).

Steps:
  stage 0  the Python-built V4 tool compiles the 22 crates plus
           tools/build_llvm.fk (bootstrap mode) to an LLVM module
  stage 1  that module is linked into a native V4 compiler
  stage 2  the stage 1 compiler compiles the same sources again

The run passes when every stage reports 0 diagnostics and the stage 2
module is byte-identical to the stage 0 module. A stage 2 binary built
from it would then be the stage 1 binary, so the bootstrap is a fixed
point. Each compile prints its wall time and peak memory.

This takes about 20 minutes and needs about 6 GB free for stage 0.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import build_v4
import check_v4 as checks

MODULE_MARKER = "@@V4-MODULE\n"


def timed(command: list[str], stdout_path: Path, label: str) -> int:
    """Run a command, print its wall time and peak RSS, return its exit code."""
    started = time.monotonic()
    stderr_path = stdout_path.with_suffix(".err")
    with stdout_path.open("wb") as out, stderr_path.open("wb") as err:
        process = subprocess.Popen(command, stdout=out, stderr=err)
        if hasattr(os, "wait4"):
            # wait4 reports this process's own peak, not a running maximum.
            _, status, usage = os.wait4(process.pid, 0)
            process.returncode = os.waitstatus_to_exitcode(status)
            peak = f"{usage.ru_maxrss // (1024 * 1024 if sys.platform == 'darwin' else 1024)}MB"
        else:
            process.wait()
            peak = "unmeasured"
    elapsed = time.monotonic() - started
    print(f"{label}: exit={process.returncode} elapsed={elapsed:.1f}s peak-memory={peak}", flush=True)
    errors = stderr_path.read_text(encoding="utf-8", errors="replace")
    if errors:
        sys.stderr.write(errors[:4000])
    return process.returncode


def split_module(stdout_path: Path, label: str) -> bytes:
    data = stdout_path.read_bytes()
    marker = MODULE_MARKER.encode()
    if data.count(marker) != 1:
        raise RuntimeError(f"{label}: expected one module marker")
    prefix, module = data.split(marker)
    text = prefix.decode("utf-8", "replace")
    print(text.strip())
    if "v4-errors=0" not in text:
        raise RuntimeError(f"{label}: compile reported errors")
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--work", type=Path, default=checks.RUNTIME_BUILD_ROOT / "self_host",
                        help="directory for the flat source, modules and stage 1 binary")
    parser.add_argument("--opt", type=int, choices=(0, 1, 2, 3), default=1,
                        help="clang optimization level for the stage 1 link (default 1)")
    args = parser.parse_args()
    clang = shutil.which("clang")
    if clang is None:
        print("clang is required", file=sys.stderr)
        return 1
    target = build_v4.host_target()
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    flat = work / "compiler.flat.fk"
    flat.write_bytes(build_v4.FlattenedSource(build_v4.compiler_sources(checks.V4_ROOT / "tools" / "build_llvm.fk")).data)
    print(f"flattened compiler: {flat} ({flat.stat().st_size} bytes)")

    tool = build_v4.bootstrap(clang)
    stage0_out = work / "stage0.out"
    code = timed([str(tool), str(flat), target, "unwind", "bootstrap"], stage0_out, "stage 0 compile")
    if code != 0:
        return 1
    stage0 = split_module(stage0_out, "stage 0")
    stage0_ll = work / "stage0.ll"
    stage0_ll.write_bytes(stage0)

    stage1 = work / ("freak_v4_stage1" + (".exe" if sys.platform == "win32" else ""))
    link = build_v4.native_link_command(clang, stage0_ll, stage1)
    link[2] = f"-O{args.opt}"
    linked = subprocess.run(link, capture_output=True, text=True)
    if linked.returncode != 0:
        print(f"stage 1 link failed:\n{linked.stdout}{linked.stderr}", file=sys.stderr)
        return 1
    print(f"stage 1 compiler: {stage1}")

    stage2_out = work / "stage2.out"
    code = timed([str(stage1), str(flat), target, "unwind", "bootstrap"], stage2_out, "stage 2 compile")
    if code != 0:
        return 1
    stage2 = split_module(stage2_out, "stage 2")
    (work / "stage2.ll").write_bytes(stage2)

    digest0 = hashlib.sha256(stage0).hexdigest()
    digest2 = hashlib.sha256(stage2).hexdigest()
    print(f"stage 0 module sha256 {digest0}")
    print(f"stage 2 module sha256 {digest2}")
    if stage0 != stage2:
        print("FAIL: stage 2 module differs from stage 0 (no fixed point)", file=sys.stderr)
        return 1
    print("fixed point: stage 2 module is byte-identical to stage 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
