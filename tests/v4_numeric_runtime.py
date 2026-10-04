#!/usr/bin/env python3
"""Verify V4 checked arithmetic and conversions against numerical oracles.

Each optimization level links the actual runtime as a separate C translation
unit. Successful boundary/random vectors run in a batch; named failures run in
fresh processes and must exit 1 with exactly one fixed diagnostic. Conversion
vectors carry exact binary64 bits, including NaNs and boundary-adjacent values.
--sanitize adds an UndefinedBehaviorSanitizer/float-cast-overflow build without
replacing any ordinary build.
This is a helper ABI test; FREAK compiler/operator integration is a separate gate.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import random
import shutil
import subprocess
import struct
import tempfile


LIMITS = {"int": (-(1 << 63), (1 << 63) - 1), "uint": (0, (1 << 64) - 1), "tiny": (0, 255)}
OPERATIONS = ("add", "sub", "mul", "neg", "div", "mod")
LABELS = {"add": "addition", "sub": "subtraction", "mul": "multiplication", "neg": "negation", "div": "division", "mod": "remainder"}
CONVERSIONS = (("int", "uint"), ("uint", "int"), ("tiny", "int"), ("tiny", "uint"), ("int", "tiny"), ("uint", "tiny"), ("int", "num"), ("uint", "num"), ("tiny", "num"), ("num", "int"), ("num", "uint"), ("num", "tiny"))


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


@dataclass(frozen=True)
class ConversionCase:
    target: str
    source: str
    value: int  # IEEE 754 bits when source is num; numerical value otherwise.

    @property
    def helper(self) -> str:
        return f"{self.target}_from_{self.source}"

    @property
    def line(self) -> str:
        value = f"{self.value:016x}" if self.source == "num" else str(self.value)
        return f"{self.helper} {value} 0"


def num_bits(value: float) -> int:
    return struct.unpack(">Q", struct.pack(">d", value))[0]


def bits_num(value: int) -> float:
    return struct.unpack(">d", struct.pack(">Q", value))[0]


def conversion_oracle(case: ConversionCase) -> tuple[str | None, str | None]:
    if case.target == "num":
        return f"{num_bits(float(case.value)):016x}", None
    value = bits_num(case.value) if case.source == "num" else case.value
    message = f"FREAK V4: {case.source} to {case.target} conversion out of range\n"
    if case.source == "num":
        if not math.isfinite(value):
            return None, message
        value = math.trunc(value)
    lower, upper = LIMITS[case.target]
    if not lower <= value <= upper:
        return None, message
    return str(value), None


def expected(case: Case | ConversionCase) -> tuple[str | None, str | None]:
    if isinstance(case, ConversionCase):
        return conversion_oracle(case)
    value, message = oracle(case)
    return str(value) if value is not None else None, message


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


def conversion_cases() -> tuple[list[ConversionCase], list[ConversionCase]]:
    vectors: dict[ConversionCase, None] = {}
    priority: dict[ConversionCase, None] = {}
    for target, source in CONVERSIONS:
        if source == "num":
            numeric_values = [
                0.0, -0.0, 0.5, -0.5, 1.0, -1.0,
                math.nextafter(-1.0, 0.0), math.nextafter(-1.0, -math.inf),
                2.9, -2.9, 255.0, 255.9, 256.0,
                math.nextafter(256.0, 0.0), math.nextafter(256.0, math.inf),
                -(2.0 ** 63), math.nextafter(-(2.0 ** 63), -math.inf),
                math.nextafter(-(2.0 ** 63), 0.0),
                2.0 ** 63, math.nextafter(2.0 ** 63, 0.0),
                math.nextafter(2.0 ** 63, math.inf),
                2.0 ** 64, math.nextafter(2.0 ** 64, 0.0),
                math.nextafter(2.0 ** 64, math.inf),
                math.nan, math.inf, -math.inf,
            ]
            values = [num_bits(value) for value in numeric_values]
            # Quiet/signaling NaNs of both signs and varied payloads are checked
            # as inputs through memcpy, without platform text-parser behavior.
            values.extend([0x7FF8000000000042, 0xFFF8000000000042, 0x7FF0000000000001, 0xFFF0000000000001])
        else:
            lower, upper = LIMITS[source]
            values = sorted({lower, lower + 1, upper, upper - 1, 0, 1, 2, 254, 255, 256, (1 << 53) - 1, 1 << 53, (1 << 53) + 1, (1 << 63) - 1})
            if source == "int":
                values.extend([-1, -2, -255, -256, -((1 << 53) + 1)])
            if source == "uint":
                values.extend([1 << 63, (1 << 63) + 1])
            values = [value for value in values if lower <= value <= upper]
        for value in values:
            case = ConversionCase(target, source, value)
            priority[case] = None
            vectors[case] = None
        random_source = random.Random(f"FREAK V4 checked conversion {target} {source}")
        if source == "tiny":
            samples = range(256)
        elif source == "num":
            samples = [random_source.getrandbits(64) for _ in range(400)]
        else:
            samples = [random_source.randint(*LIMITS[source]) for _ in range(400)]
        for value in samples:
            vectors[ConversionCase(target, source, value)] = None
    successful = []
    rejected = {case: None for case in priority if conversion_oracle(case)[1]}
    extra_failures: Counter[str] = Counter()
    for case in vectors:
        if conversion_oracle(case)[1] is None:
            successful.append(case)
        elif case not in rejected and extra_failures[case.helper] < 12:
            rejected[case] = None
            extra_failures[case.helper] += 1
    assert {case.helper for case in successful} == {f"{target}_from_{source}" for target, source in CONVERSIONS}
    assert {case.helper for case in rejected} == {"int_from_uint", "uint_from_int", "tiny_from_int", "tiny_from_uint", "int_from_num", "uint_from_num", "tiny_from_num"}
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
    for target, source in CONVERSIONS:
        c_type = {"int": "int64_t", "uint": "uint64_t", "tiny": "uint8_t", "num": "double"}
        parser = {"int": "signed_value", "uint": "unsigned_value", "tiny": "unsigned_value", "num": "num_value"}[source]
        operands = f"({c_type[source]}){parser}(lhs)"
        checks = 'if (unsigned_value(lhs) > UINT8_MAX) exit(2);' if source == "tiny" else ''
        formatter = {
            "int": 'printf("%" PRId64 "\\n", (int64_t)result);',
            "uint": 'printf("%" PRIu64 "\\n", (uint64_t)result);',
            "tiny": 'printf("%" PRIu64 "\\n", (uint64_t)result);',
            "num": 'print_num(result);',
        }[target]
        declarations.append(f'''    if (strcmp(operation, "{target}_from_{source}") == 0) {{
        {checks}
        {c_type[target]} result = freak_v4_{target}_from_{source}({operands});
        {formatter}
        return;
    }}''')
    return r'''#if defined(_WIN32) && !defined(_CRT_SECURE_NO_WARNINGS)
/* Width-bounded sscanf below is shared with the portable C11 probe. */
#define _CRT_SECURE_NO_WARNINGS 1
#endif
#include "freak_v4_numeric_runtime.h"
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

static double num_value(const char *text) {
    char *end;
    uintmax_t parsed;
    uint64_t bits;
    double value;
    errno = 0;
    if (*text == '-') exit(2);
    parsed = strtoumax(text, &end, 16);
    if (errno || *end || parsed > UINT64_MAX) exit(2);
    bits = (uint64_t)parsed;
    memcpy(&value, &bits, sizeof(value));
    return value;
}

static void print_num(double value) {
    uint64_t bits;
    memcpy(&bits, &value, sizeof(bits));
    printf("%016" PRIx64 "\n", bits);
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


def verify(binary: Path, successes: list[Case | ConversionCase], failures: list[Case | ConversionCase], env: dict[str, str]) -> dict:
    output = run([str(binary), "--batch"], source="\n".join(case.line for case in successes) + "\n", env=env)
    assert output.returncode == 0 and not output.stderr, f"successful vectors failed: exit {output.returncode}\n{output.stderr}"
    actual = output.stdout.splitlines()
    assert len(actual) == len(successes), f"missing successful vector results: {len(actual)} of {len(successes)}"
    for case, value in zip(successes, actual):
        wanted = expected(case)[0]
        assert value == wanted, f"{case.line}: expected {wanted}, got {value}"
    # Repeat every named failure in a new process: no state or previous failure
    # may change the diagnostic, exit status, or absence of a result.
    for case in failures:
        wanted = expected(case)[1]
        for _ in range(2):
            rejected = run([str(binary), *case.line.split()], timeout=10, env=env)
            assert rejected.returncode == 1, f"{case.line}: expected exit 1, got {rejected.returncode}\n{rejected.stderr}"
            assert rejected.stdout == "", f"{case.line}: failed operation produced a result: {rejected.stdout!r}"
            assert rejected.stderr == wanted, f"{case.line}: expected {wanted!r}, got {rejected.stderr!r}"
    return {"successful_vectors": len(successes), "successful_arithmetic_vectors": sum(isinstance(case, Case) for case in successes), "successful_conversion_vectors": sum(isinstance(case, ConversionCase) for case in successes), "rejected_vectors": len(failures), "rejected_processes": 2 * len(failures), "helpers": len({case.helper for case in successes})}


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
    converted, conversion_rejected = conversion_cases()
    successful = successful + converted
    rejected = rejected + conversion_rejected
    runtime_env = dict(os.environ)
    runtime_env["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
    tested_sources = [runtime / "freak_v4_numeric_runtime.c", runtime / "freak_v4_numeric_runtime.h", Path(__file__).resolve()]
    report = {"compiler": compiler, "scope": "native checked arithmetic and numerical conversion helper ABI", "source_sha256": {str(path.relative_to(repo)): hashlib.sha256(path.read_bytes()).hexdigest() for path in tested_sources}, "builds": []}
    with tempfile.TemporaryDirectory(prefix="freak-v4-numeric-") as temporary:
        root = Path(temporary)
        source = root / "numeric_driver.c"
        source.write_text(driver_source(), encoding="utf-8")
        report["driver_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
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
                    command.extend(["-g", "-fsanitize=undefined,float-cast-overflow", "-fno-sanitize-recover=all"])
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
