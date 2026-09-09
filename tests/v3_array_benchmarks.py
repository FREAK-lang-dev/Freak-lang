#!/usr/bin/env python3
"""Compile real vector math and measure checked 100k/1M array workloads.

Use a compiler developer shell on Windows. Each backend compiles once; reported
native medians exclude compilation. Default checks both backends. --backend llvm
permits an explicitly partial backend development run. No safety flags are removed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import tempfile
import time


def run(command: list[str], *, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=timeout)


def checked(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = run(command)
    if result.returncode:
        raise AssertionError(f"{command!r}\n{result.stdout}\n{result.stderr}")
    return result


def periodic_sum(count: int, period: int, *, square: bool = False) -> int:
    rounds, remainder = divmod(count, period)
    term = (lambda x: x * x) if square else (lambda x: x)
    return rounds * sum(map(term, range(period))) + sum(map(term, range(remainder)))


def expected(count: int) -> list[str]:
    values = periodic_sum(count, 1024)
    # Each interior stencil is previous + 2*current + next. Account separately
    # for the two excluded endpoints; this is independent of emitted loops.
    stencil = 0
    if count >= 3:
        stencil = 4 * values - 3 * ((count - 1) % 1024) - 1 - ((count - 2) % 1024)
    return list(map(str, [count, values, periodic_sum(count, 1024, square=True),
                          periodic_sum(count, 64, square=True), (count + 1) // 2,
                          periodic_sum(count, 64), stencil]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("compiler", type=Path, help="standalone V3 compiler executable")
    parser.add_argument("--cli", action="store_true", help="use the public freak transpile command")
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--backend", choices=("both", "llvm", "c"), default="both")
    parser.add_argument("--output", type=Path, required=True, help="write reproducible measurement JSON here")
    parser.add_argument("--runs", type=int, default=3)
    args = parser.parse_args()
    if args.runs < 3:
        parser.error("at least three measured native runs are required")
    repo = Path(__file__).resolve().parents[1]
    runtime = (args.runtime_root or repo / "freakc/runtime").resolve()
    compiler = args.compiler.resolve()
    clang = os.environ.get("FREAK_CLANG") or shutil.which("clang")
    if not clang:
        raise SystemExit("clang is required")
    source_text = (repo / "examples/array_math.fk").read_text(encoding="utf-8")
    report = {
        "status": "running", "platform": platform.platform(), "machine": platform.machine(),
        "python": platform.python_version(), "head": checked(["git", "-C", str(repo), "rev-parse", "HEAD"]).stdout.strip(),
        "compiler": str(compiler), "compiler_sha256": hashlib.sha256(compiler.read_bytes()).hexdigest(),
        "compiler_version": checked([str(compiler), "--version"]).stdout.strip(),
        "clang_version": checked([clang, "--version"]).stdout.strip(),
        "source_sha256": hashlib.sha256(source_text.encode()).hexdigest(),
        "runtime_sha256": hashlib.sha256((runtime / "freak_runtime.c").read_bytes()).hexdigest(),
        "native_flags": ["-O2", "-Wno-deprecated-declarations"], "measured_runs": args.runs,
        "scaling_gate": "1M median <= max(35 * 100k median, 2 seconds); coarse quadratic-regression guard",
        "backends": {},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="freak-v3-array-math-") as temporary:
            directory = Path(temporary)
            for backend in (("llvm", "c") if args.backend == "both" else (args.backend,)):
                source = directory / f"math-{backend}.fk"
                source.write_text(source_text, encoding="utf-8")
                generated = Path(str(source) + (".ll" if backend == "llvm" else ".c"))
                transpile = [str(compiler)] + (["transpile"] if args.cli else []) + [str(source), f"--{backend}"]
                started = time.perf_counter()
                checked(transpile)
                transpile_seconds = time.perf_counter() - started
                binary = directory / (f"math-{backend}.exe" if os.name == "nt" else f"math-{backend}")
                native = [clang, "-O2", "-Wno-deprecated-declarations", str(generated), str(runtime / "freak_runtime.c")]
                if backend == "llvm":
                    native.append(str(runtime / "freak_llvm_runtime.c"))
                native += ["-I", str(runtime), "-o", str(binary)]
                native += ["-lws2_32"] if os.name == "nt" else ["-lm"]
                started = time.perf_counter()
                checked(native)
                native_compile_seconds = time.perf_counter() - started
                entry = {"transpile_seconds": transpile_seconds, "native_compile_seconds": native_compile_seconds,
                         "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                         "transpile_command": transpile, "native_command": native,
                         "bounds_controls": [], "workloads": {}}
                report["backends"][backend] = entry
                for count, mode in ((4, "read-oob"), (4, "write-oob"), (4, "negative"), (0, "read-oob")):
                    result = run([str(binary), str(count), mode], timeout=15)
                    if result.returncode == 0 or "out of bounds" not in result.stderr:
                        raise AssertionError((backend, count, mode, result.returncode, result.stdout, result.stderr))
                    entry["bounds_controls"].append({"count": count, "mode": mode, "exit": result.returncode,
                                                      "diagnostic": result.stderr.strip()})
                for count in (100_000, 1_000_000):
                    wanted = expected(count)
                    warm = checked([str(binary), str(count)])
                    if warm.stdout.splitlines() != wanted:
                        raise AssertionError((backend, count, warm.stdout.splitlines(), wanted))
                    elapsed = []
                    for _ in range(args.runs):
                        started = time.perf_counter()
                        result = checked([str(binary), str(count)])
                        elapsed.append(time.perf_counter() - started)
                        if result.stdout.splitlines() != wanted:
                            raise AssertionError((backend, count, result.stdout.splitlines(), wanted))
                    entry["workloads"][str(count)] = {"seconds": elapsed, "median_seconds": statistics.median(elapsed),
                                                      "checksums": wanted}
                    print(f"{backend} {count:,}: median {statistics.median(elapsed):.4f}s; checksums verified", flush=True)
                small = entry["workloads"]["100000"]["median_seconds"]
                large = entry["workloads"]["1000000"]["median_seconds"]
                entry["scaling_ratio"] = large / small
                if large > max(small * 35, 2.0):
                    raise AssertionError(f"gross scaling regression: {backend} ratio={large / small:.2f}")
        report["status"] = "passed" if args.backend == "both" else "partial-backend-passed"
    except Exception as error:
        report["status"] = "failed"
        report["error"] = str(error)
        raise
    finally:
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{report['status']}: {args.output}")


if __name__ == "__main__":
    main()
