#!/usr/bin/env python3
"""Verify V4 checked integer helpers against an arbitrary-precision oracle.

Each optimization level links the actual runtime as a separate C translation
unit. Successful boundary/random vectors run in a batch; named failures run in
fresh processes and must exit 1 with exactly one fixed diagnostic. --sanitize
adds an UndefinedBehaviorSanitizer build without replacing any ordinary build.
This is a helper ABI test; FREAK compiler/operator integration is a separate gate.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import tempfile


LIMITS = {"int": (-(1 << 63), (1 << 63) - 1), "uint": (0, (1 << 64) - 1), "tiny": (0, 255)}
OPERATIONS = ("add", "sub", "mul", "neg", "div", "mod")
LABELS = {"add": "addition", "sub": "subtraction", "mul": "multiplication", "neg": "negation", "div": "division", "mod": "remainder"}


@dataclass(frozen=True)
class Case:
    kind: str
    operation: str
    lhs: int
    rhs: int = 0

    @property
    def helper(self) -> str:
        return f"{self.kind}_{self.operation}"

    @property
    def line(self) -> str:
        return f"{self.helper} {self.lhs} {self.rhs}"


def oracle(case: Case) -> tuple[int | None, str | None]:
    """Use mathematical integers, with division truncated toward zero."""
    lower, upper = LIMITS[case.kind]
    lhs, rhs, op = case.lhs, case.rhs, case.operation
    if op in ("div", "mod"):
        if rhs == 0:
            return None, f"FREAK V4: {case.kind} {LABELS[op]} by zero\n"
        if case.kind == "int" and lhs == lower and rhs == -1:
            return None, f"FREAK V4: int {LABELS[op]} overflow\n"
        quotient = abs(lhs) // abs(rhs)
        if (lhs < 0) != (rhs < 0):
            quotient = -quotient
        value = quotient if op == "div" else lhs - quotient * rhs
    elif op == "add":
        value = lhs + rhs
    elif op == "sub":
        value = lhs - rhs
    elif op == "mul":
        value = lhs * rhs
    elif op == "neg":
        value = -lhs
    else:
        raise AssertionError(f"unknown operation: {op}")
    if not lower <= value <= upper:
        failure = "underflow" if case.kind != "int" and value < 0 else "overflow"
        return None, f"FREAK V4: {case.kind} {LABELS[op]} {failure}\n"
    return value, None


def cases() -> tuple[list[Case], list[Case]]:
    """Cover both range edges and sign branches, then sample full-width values."""
    vectors: dict[Case, None] = {}
    priority: dict[Case, None] = {}
    for kind, (lower, upper) in LIMITS.items():
        forced = [
            Case(kind, "add", upper, 1), Case(kind, "add", 1, upper),
            Case(kind, "sub", lower, 1), Case(kind, "sub", lower, upper),
            Case(kind, "mul", upper, 2), Case(kind, "mul", 2, upper),
            Case(kind, "neg", lower if kind == "int" else 1),
            Case(kind, "div", upper, 0), Case(kind, "mod", upper, 0),
            Case(kind, "div", 0, 0), Case(kind, "mod", 0, 0),
        ]
        if kind == "int":
            forced.extend([
                Case(kind, "add", lower, -1), Case(kind, "add", -1, lower),
                Case(kind, "sub", upper, -1), Case(kind, "sub", upper, lower),
                Case(kind, "mul", lower, -1), Case(kind, "mul", -1, lower),
                Case(kind, "mul", lower, 2), Case(kind, "mul", 2, lower),
                Case(kind, "mul", -3037000500, -3037000500),
                Case(kind, "div", lower, -1), Case(kind, "mod", lower, -1),
            ])
        for case in forced:
            priority[case] = None
            vectors[case] = None
        boundaries = {lower, lower + 1, upper, upper - 1, 0, 1, 2, 3, 7, upper // 2, upper // 2 + 1}
        if kind == "int":
            boundaries.update({-1, -2, -3, -7, -3037000499, -3037000500, 3037000499, 3037000500})
        if kind == "uint":
            boundaries.update({(1 << 32) - 1, 1 << 32, (1 << 63) - 1, 1 << 63})
        for lhs in sorted(boundaries):
            vectors[Case(kind, "neg", lhs)] = None
            for rhs in sorted(boundaries):
                for op in OPERATIONS:
                    if op != "neg":
                        vectors[Case(kind, op, lhs, rhs)] = None
        random_source = random.Random(f"FREAK V4 checked arithmetic {kind}")
        for _ in range(400):
            lhs = random_source.randint(lower, upper)
            rhs = random_source.randint(lower, upper)
            vectors[Case(kind, "neg", lhs)] = None
            for op in OPERATIONS:
                if op != "neg":
                    vectors[Case(kind, op, lhs, rhs)] = None
    # Every tiny left operand is checked at/next to its exact add/mul bound.
    # This catches all 256 distinct byte limits without forking 65,536 failures.
    for lhs in range(256):
        for op, bound in (("add", 255 - lhs), ("mul", 255 // lhs if lhs else 255), ("sub", lhs)):
            for rhs in {0, 1, bound, min(255, bound + 1), 255}:
                vectors[Case("tiny", op, lhs, rhs)] = None
        for rhs in (1, 2, 3, 255):
            vectors[Case("tiny", "div", lhs, rhs)] = None
            vectors[Case("tiny", "mod", lhs, rhs)] = None
    successful: list[Case] = []
    rejected: dict[Case, None] = {case: None for case in priority if oracle(case)[1]}
    extra_failures: Counter[str] = Counter()
    for case in vectors:
        if oracle(case)[1] is None:
            successful.append(case)
        elif case not in rejected and extra_failures[case.helper] < 12:
            rejected[case] = None
            extra_failures[case.helper] += 1
    required = {f"{kind}_{op}" for kind in LIMITS for op in OPERATIONS}
    assert {case.helper for case in successful} == required
    assert {case.helper for case in rejected} == required
    return successful, list(rejected)


def driver_source() -> str:
    declarations = []
    for kind in LIMITS:
        signed = kind == "int"
        c_type = {"int": "int64_t", "uint": "uint64_t", "tiny": "uint8_t"}[kind]
        parser = "signed_value" if signed else "unsigned_value"
        formatter = 'printf("%" PRId64 "\\n", (int64_t)result);' if signed else 'printf("%" PRIu64 "\\n", (uint64_t)result);'
        for op in OPERATIONS:
            operands = f"({c_type}){parser}(lhs)"
            if op != "neg":
                operands += f", ({c_type}){parser}(rhs)"
            checks = ''
            if kind == "tiny":
                checks = 'if (unsigned_value(lhs) > UINT8_MAX || unsigned_value(rhs) > UINT8_MAX) exit(2);'
            declarations.append(f'''    if (strcmp(operation, "{kind}_{op}") == 0) {{
        {checks}
        {c_type} result = freak_v4_{kind}_{op}({operands});
        {formatter}
        return;
    }}''')
    return r'''#include "freak_v4_numeric_runtime.h"
#include <errno.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int64_t signed_value(const char *text) {
    char *end;
    intmax_t value;
    errno = 0;
    value = strtoimax(text, &end, 10);
    if (errno || *end || value < INT64_MIN || value > INT64_MAX) exit(2);
    return (int64_t)value;
}

static uint64_t unsigned_value(const char *text) {
    char *end;
    uintmax_t value;
    errno = 0;
    if (*text == '-') exit(2);
    value = strtoumax(text, &end, 10);
    if (errno || *end || value > UINT64_MAX) exit(2);
    return (uint64_t)value;
}

static void execute(const char *operation, const char *lhs, const char *rhs) {
''' + "\n".join(declarations) + r'''
    exit(2);
}

int main(int argc, char **argv) {
    if (argc == 2 && strcmp(argv[1], "--batch") == 0) {
        char line[128], operation[16], lhs[32], rhs[32], extra;
        while (fgets(line, sizeof(line), stdin)) {
            if (sscanf(line, "%15s %31s %31s %c", operation, lhs, rhs, &extra) != 3) return 2;
            execute(operation, lhs, rhs);
        }
        return ferror(stdin) ? 2 : 0;
    }
    if (argc != 4) return 2;
    execute(argv[1], argv[2], argv[3]);
    return 0;
}
'''


def run(command: list[str], *, source: str | None = None, timeout: int = 30, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, input=source, capture_output=True, text=True, timeout=timeout, env=env)


def verify(binary: Path, successes: list[Case], failures: list[Case], env: dict[str, str]) -> dict:
    output = run([str(binary), "--batch"], source="\n".join(case.line for case in successes) + "\n", env=env)
    assert output.returncode == 0 and not output.stderr, f"successful vectors failed: exit {output.returncode}\n{output.stderr}"
    actual = output.stdout.splitlines()
    assert len(actual) == len(successes), f"missing successful vector results: {len(actual)} of {len(successes)}"
    for case, value in zip(successes, actual):
        expected = str(oracle(case)[0])
        assert value == expected, f"{case.line}: expected {expected}, got {value}"
    # Repeat every named failure in a new process: no state or previous failure
    # may change the diagnostic, exit status, or absence of a result.
    for case in failures:
        expected = oracle(case)[1]
        for _ in range(2):
            rejected = run([str(binary), case.helper, str(case.lhs), str(case.rhs)], timeout=10, env=env)
            assert rejected.returncode == 1, f"{case.line}: expected exit 1, got {rejected.returncode}\n{rejected.stderr}"
            assert rejected.stdout == "", f"{case.line}: failed operation produced a result: {rejected.stdout!r}"
            assert rejected.stderr == expected, f"{case.line}: expected {expected!r}, got {rejected.stderr!r}"
    return {"successful_vectors": len(successes), "rejected_vectors": len(failures), "rejected_processes": 2 * len(failures), "helpers": 18}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", help="Clang or MSVC cl executable (defaults to FREAK_CLANG or clang)")
    parser.add_argument("--optimization", action="append", choices=("0", "2", "3"), help="repeat to select optimization levels; default: 0, 2, 3 (MSVC: 0, 2)")
    parser.add_argument("--sanitize", action="store_true", help="also run a Clang -O2 UndefinedBehaviorSanitizer build")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    compiler = args.compiler or os.environ.get("FREAK_CLANG") or shutil.which("clang")
    if not compiler:
        parser.error("clang is required; set FREAK_CLANG or pass --compiler")
    is_msvc = Path(compiler).name.lower() in ("cl", "cl.exe")
    optimizations = args.optimization or (["0", "2"] if is_msvc else ["0", "2", "3"])
    if is_msvc and (args.sanitize or "3" in optimizations):
        parser.error("MSVC supports these tests at levels 0 and 2; --sanitize and level 3 require Clang")
    repo = Path(__file__).resolve().parents[1]
    runtime = repo / "freakc" / "runtime"
    successful, rejected = cases()
    runtime_env = dict(os.environ)
    runtime_env["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
    report = {"compiler": compiler, "scope": "native checked integer helper ABI", "builds": []}
    with tempfile.TemporaryDirectory(prefix="freak-v4-numeric-") as temporary:
        root = Path(temporary)
        source = root / "numeric_driver.c"
        source.write_text(driver_source(), encoding="utf-8")
        builds = [(level, False) for level in dict.fromkeys(optimizations)]
        if args.sanitize:
            builds.append(("2", True))
        for level, sanitize in builds:
            name = f"numeric_O{level}" + ("_ubsan" if sanitize else "")
            binary = root / (name + (".exe" if os.name == "nt" else ""))
            if is_msvc:
                command = [compiler, "/nologo", "/std:c11", "/W4", "/WX", "/Od" if level == "0" else "/O2", f"/I{runtime}", str(source), str(runtime / "freak_v4_numeric_runtime.c"), f"/Fe:{binary}", f"/Fo:{root}{os.sep}"]
            else:
                command = [compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic", f"-O{level}", f"-I{runtime}", str(source), str(runtime / "freak_v4_numeric_runtime.c"), "-o", str(binary)]
                if sanitize:
                    command.extend(["-g", "-fsanitize=undefined", "-fno-sanitize-recover=all"])
            compiled = run(command, timeout=120)
            assert compiled.returncode == 0, f"{name} build failed\n{compiled.stdout}\n{compiled.stderr}"
            result = verify(binary, successful, rejected, runtime_env)
            result.update({"optimization": f"O{level}", "undefined_behavior_sanitizer": sanitize, "status": "pass"})
            report["builds"].append(result)
            print(f"{name}: {result['helpers']} helpers, {result['successful_vectors']} values, {result['rejected_processes']} named failures PASS", flush=True)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
