#!/usr/bin/env python3
"""Run source-level V3 array contracts through both native backends."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


CASES = {
    "owned_shapes": ('''extern task freak_v3_live_arrays() -> int
extern task freak_v3_live_shapes() -> int
extern task freak_v3_live_words() -> int
shape Reading {
    label: word
    value: num
    ready: bool
}
task work() {
    pilot mut values = [Reading { label: "first" + " reading", value: 1.5, ready: true }, Reading { label: "second", value: 2.5, ready: false }]
    pilot saved = values[0]
    values[0] = Reading { label: "replacement", value: 4.5, ready: true }
    say saved.label
    say saved.value
    for each value in values {
        say value.label
        say value.value
        say value.ready
    }
}
task main() {
    work()
    say freak_v3_live_arrays()
    say freak_v3_live_shapes()
    say freak_v3_live_words()
}
''', ["first reading", "1.5", "replacement", "4.5", "true", "second", "2.5", "false", "0", "0", "0"]),
    "single_evaluation": ('''pilot mut calls = 0
task index() -> int {
    calls += 1
    give back 0
}
task main() {
    pilot mut values = [3]
    values[index()] += 4
    say calls
    say values[0]
}
''', ["1", "7"]),
    "requested": ('''pilot mut values = [1, 2, 3, 4]
values[2] = 99
say values[0]
say values.length()
for each x in values {
    say x
}
''', ["1", "4", "1", "2", "99", "4"]),
    "numeric": ('''task main() {
    pilot mut values = [1, 2.5, 3]
    values[0] = 4
    values[2] = values[0] * values[1]
    say values[0]
    say values[2]
    pilot mut flags = [true, false, true]
    flags[1] = true
    for each flag in flags { say flag }
}
''', ["4", "10", "true", "true", "true"]),
    "word": ('''task main() {
    pilot mut words = ["a" + "b", "cd"]
    pilot extracted = words[0]
    words[0] = words[0]
    words[0] = "changed"
    say extracted
    for each item in words { say item }
}
''', ["ab", "changed", "cd"]),
    "tasks": ('''task create() -> List<int> {
    pilot values = [2, 4, 6]
    give back values
}
task total(values: List<int>) -> int {
    pilot mut sum = 0
    for each value in values { sum += value }
    give back sum
}
task main() {
    pilot values = create()
    say total(values)
    say values[1]
}
''', ["12", "4"]),
    "iteration_control": ('''task main() {
    pilot values = [1, 2, 3, 4]
    for each x in values {
        if x == 2 { continue }
        if x == 4 { break }
        say x
    }
}
''', ["1", "3"]),
}


def run(command: list[str], cwd: Path, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, encoding="utf-8",
                          errors="replace", capture_output=True, timeout=timeout)


def require_ok(result: subprocess.CompletedProcess[str], label: str) -> None:
    if result.returncode:
        raise AssertionError(f"{label} failed ({result.returncode})\n{result.stdout}{result.stderr}")


def execute_case(compiler: Path, repo: Path, root: Path, backend: str,
                 name: str, source: str, expected: list[str]) -> dict:
    fixture = root / f"{name}_{backend}.fk"
    fixture.write_text(source, encoding="utf-8")
    compiled = run([str(compiler), str(fixture), f"--{backend}"], root)
    require_ok(compiled, f"{name}/{backend} emission")
    generated = Path(str(fixture) + (".c" if backend == "c" else ".ll"))
    if not generated.is_file():
        raise AssertionError(f"missing generated artifact: {generated}")
    binary = root / (f"{name}_{backend}.exe" if sys.platform == "win32" else f"{name}_{backend}")
    runtime = repo / "freakc/runtime"
    clang = shutil.which(os.environ.get("FREAK_CLANG", "clang"))
    if not clang:
        raise AssertionError("Clang is required")
    command = [clang, "-O2", "-g", str(generated), str(runtime / "freak_runtime.c"),
               "-I", str(runtime), "-o", str(binary)]
    if backend == "llvm":
        command.append(str(runtime / "freak_llvm_runtime.c"))
    if sys.platform == "win32":
        command += ["-D_CRT_SECURE_NO_WARNINGS", "-lws2_32"]
    else:
        command += ["-lm", "-fsanitize=address", "-fno-omit-frame-pointer"]
    require_ok(run(command, root, 120), f"{name}/{backend} native link")
    started = time.perf_counter()
    result = run([str(binary)], root)
    elapsed = time.perf_counter() - started
    require_ok(result, f"{name}/{backend} execution")
    actual = result.stdout.splitlines()
    if actual != expected:
        raise AssertionError(f"{name}/{backend}: expected {expected!r}, got {actual!r}\n{result.stderr}")
    return {"case": name, "backend": backend, "seconds": elapsed, "output": actual}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("compiler", type=Path, help="fresh self-hosted V3 standalone compiler")
    parser.add_argument("--case", choices=CASES)
    parser.add_argument("--backend", choices=("c", "llvm"))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    selected = {args.case: CASES[args.case]} if args.case else CASES
    records = []
    with tempfile.TemporaryDirectory(prefix="freak-v3-array-rescue-") as temporary:
        root = Path(temporary)
        for backend in ([args.backend] if args.backend else ["c", "llvm"]):
            for name, (source, expected) in selected.items():
                print(f"RUN {name}/{backend}", flush=True)
                records.append(execute_case(args.compiler.resolve(), repo, root, backend, name, source, expected))
                print(f"PASS {name}/{backend}", flush=True)
    if args.report:
        args.report.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(f"V3 array source contracts: PASS ({len(records)} native executions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
