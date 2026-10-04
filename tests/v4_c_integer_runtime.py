#!/usr/bin/env python3
"""Guarded checked32 C helper prerequisite: all-OS --plain, Linux UBSan default.

No FREAK compiler or native C-width admission is involved. Every command,
channel, frozen input and binary is retained in a new external --work directory.
Importing this module executes no compiler or native process.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import types


ROOT = Path(__file__).resolve().parents[1]
OPTS = (0, 2, 3)
COMPILE_SECONDS, COMPILE_MIB = 60, 512
RUN_SECONDS, RUN_MIB = 10, 64
OUTPUT_MIB = 1
SANITIZER_FLAGS = ("-g", "-fsanitize=undefined", "-fno-sanitize-recover=all", "-fno-omit-frame-pointer")
OPERATIONS = ("add", "sub", "mul", "neg", "div", "mod", "from-int", "from-uint")
LABELS = {"add": "addition", "sub": "subtraction", "mul": "multiplication",
          "neg": "negation", "div": "division", "mod": "remainder"}
LIMITS = {"i32": (-(1 << 31), (1 << 31) - 1), "u32": (0, (1 << 32) - 1)}
OWNED_SOURCE_NAMES = (
    "freakc/runtime/freak_v4_c_integer_runtime.c",
    "freakc/runtime/freak_v4_c_integer_runtime.h",
    "tests/v4_c_integer_runtime_probe.c",
    "tests/v4_c_integer_runtime.py",
    "tests/v4_c_integer_runtime_vectors.json",
    "tests/test_v4_c_integer_runtime.py",
    "src/compiler/v4/C_INTEGER_RUNTIME_CONTRACT.md",
)
GUARD_SOURCE_NAME = "src/compiler/v4/check_v4.py"
VECTOR_PATH = ROOT / "tests/v4_c_integer_runtime_vectors.json"
INVALID_ARGUMENTS = (
    (), ("i32_add", "1"), ("u32_neg", "-1"),
    ("i32_add", "2147483648", "0"), ("u32_add", "4294967296", "0"),
    ("i32_from_int", "9223372036854775808"),
    ("u32_from_uint", "18446744073709551616"),
    ("i32_neg", "1junk"), ("u32_add", "1", "2", "extra"),
    ("i32_unknown", "1", "2"),
)
CAPABILITIES = ("overflow", "division")


class GateError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GateError(message)


@dataclass(frozen=True)
class Case:
    id: str
    kind: str
    operation: str
    lhs: int
    rhs: int | None = None

    @property
    def helper(self) -> str:
        return f"freak_v4_{self.kind}_{self.operation.replace('-', '_')}"

    @property
    def arguments(self) -> list[str]:
        fields = [self.helper.removeprefix("freak_v4_"), str(self.lhs)]
        if self.rhs is not None:
            fields.append(str(self.rhs))
        return fields


def validate_case(case: Case) -> None:
    require(isinstance(case.id, str) and re.fullmatch(r"[a-z0-9-]+", case.id) is not None,
            "invalid case identity")
    require(case.kind in LIMITS and case.operation in OPERATIONS, "unknown helper family")
    require(type(case.lhs) is int, "operand is not an integer")
    binary = case.operation in ("add", "sub", "mul", "div", "mod")
    require((type(case.rhs) is int) if binary else (case.rhs is None), "wrong helper arity")
    if case.operation.startswith("from-"):
        bounds = (-(1 << 63), (1 << 63) - 1) if case.operation == "from-int" else (0, (1 << 64) - 1)
        require(bounds[0] <= case.lhs <= bounds[1], "conversion input is outside its source type")
    else:
        lo, hi = LIMITS[case.kind]
        require(lo <= case.lhs <= hi and (not binary or lo <= case.rhs <= hi),
                "arithmetic input is outside its source type")


def expected(case: Case) -> dict[str, object]:
    """Independent unbounded-integer oracle; quotient truncates toward zero."""
    validate_case(case)
    lo, hi = LIMITS[case.kind]
    lhs, rhs, operation = case.lhs, case.rhs, case.operation
    failure = None
    if operation.startswith("from-"):
        value = lhs
        if not lo <= value <= hi:
            failure = f"{operation[5:]} to {case.kind} conversion out of range"
    elif operation in ("div", "mod"):
        if rhs == 0:
            failure = f"{case.kind} {LABELS[operation]} by zero"
            value = None
        elif case.kind == "i32" and lhs == lo and rhs == -1:
            failure = f"i32 {LABELS[operation]} overflow"
            value = None
        else:
            quotient = abs(lhs) // abs(rhs)
            if (lhs < 0) != (rhs < 0):
                quotient = -quotient
            value = quotient if operation == "div" else lhs - quotient * rhs
    else:
        if operation == "add": value = lhs + rhs
        elif operation == "sub": value = lhs - rhs
        elif operation == "mul": value = lhs * rhs
        else: value = -lhs
        if not lo <= value <= hi:
            problem = "underflow" if case.kind == "u32" and value < 0 else "overflow"
            failure = f"{case.kind} {LABELS[operation]} {problem}"
    if failure is not None:
        return {"status": 1, "stdout": "", "stderr": f"FREAK V4: {failure}\n"}
    return {"status": 0, "stdout": f"{value}\n", "stderr": ""}


def load_vectors(path: Path = VECTOR_PATH) -> tuple[Case, ...]:
    data = json.loads(path.read_text(encoding="utf-8"))
    require(type(data.get("schema")) is int and data.get("schema") == 1 and
            type(data.get("count")) is int and data.get("count") == 58 and len(data.get("cases", [])) == 58,
            "missing complete frozen58 vector dataset")
    rows = data["cases"]
    cases = []
    identities = set()
    for row in rows:
        require(set(row) == {"id", "kind", "operation", "lhs", "rhs", "expected"}, "unexpected vector fields")
        case = Case(row["id"], row["kind"], row["operation"], row["lhs"], row["rhs"])
        require(case.id not in identities, "duplicate vector identity")
        require(row["expected"] == expected(case), "frozen vector disagrees with independent numeric oracle")
        identities.add(case.id)
        cases.append(case)
    required = {f"freak_v4_{kind}_{op.replace('-', '_')}" for kind in LIMITS for op in OPERATIONS}
    require({case.helper for case in cases} == required, "missing helper vector family")
    for status in (0, 1):
        require({case.helper for case in cases if expected(case)["status"] == status} == required,
                "each helper requires a success and named failure")
    return tuple(cases)


def channel(value: str | bytes, host: str) -> str:
    text = value.decode("utf-8", errors="strict") if isinstance(value, bytes) else value
    require(isinstance(text, str), "nontext child output")
    return text.replace("\r\n", "\n") if host == "win32" else text


def observed(result: subprocess.CompletedProcess) -> dict[str, object]:
    return {"status": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def exact_result(actual: dict, wanted: dict, host: str) -> None:
    require(set(actual) == {"status", "stdout", "stderr"}, "missing or extra native result fields")
    require(type(actual["status"]) is int, "noninteger child status")
    normalized = {"status": actual["status"], "stdout": channel(actual["stdout"], host),
                  "stderr": channel(actual["stderr"], host)}
    require(normalized == wanted, f"strict native result mismatch: wanted={wanted!r}; observed={normalized!r}")


def validate_native(actual: dict, case: Case, host: str) -> None:
    exact_result(actual, expected(case), host)


def validate_capability(actual: dict, kind: str) -> None:
    require(kind in CAPABILITIES, "unknown UBSan capability")
    require(set(actual) == {"status", "stdout", "stderr"}, "missing sanitizer channels")
    stderr = channel(actual["stderr"], "linux")
    signatures = ("runtime error: signed integer overflow",) if kind == "overflow" else (
        "runtime error: division of", "cannot be represented in type")
    require(type(actual["status"]) is int and actual["status"] == 88 and
            channel(actual["stdout"], "linux") == "" and
            all(token in stderr for token in (*signatures, "SUMMARY: UndefinedBehaviorSanitizer:")) and
            "FREAK V4:" not in stderr and "AddressSanitizer" not in stderr,
            "missing real UBSan diagnostic, status88 or empty stdout")


def build_flags(optimization: int, sanitize: bool) -> list[str]:
    require(type(optimization) is int and optimization in OPTS, "unsupported optimization")
    return ["-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic", f"-O{optimization}",
            *(SANITIZER_FLAGS if sanitize else ())]


def validate_report(report: dict, cases: tuple[Case, ...], sanitize: bool) -> None:
    require(report.get("complete") is True and report.get("sanitized") is sanitize,
            "incomplete or wrong-mode runtime report")
    require(report.get("scope") == "checked32 C helper prerequisite; no V4 C-width admission",
            "wrong runtime proof scope")
    host = report.get("platform")
    require(host in ("linux", "darwin", "win32") and (not sanitize or host == "linux"),
            "wrong host for required sanitizer gate")
    expected_names = set(OWNED_SOURCE_NAMES) | {GUARD_SOURCE_NAME}
    require(set(report.get("source_hashes", {})) == expected_names and
            report.get("source_hashes") == report.get("final_source_hashes") and
            report.get("source_hashes") == report.get("final_frozen_source_hashes") and
            all(re.fullmatch(r"[0-9a-f]{64}", digest) for digest in report["source_hashes"].values()),
            "incomplete source freeze or final source conservation")
    require(report.get("compiler", {}).get("sha256") == report.get("final_compiler_sha256") and
            re.fullmatch(r"[0-9a-f]{64}", report["compiler"]["sha256"]) is not None and
            type(report["compiler"].get("selected")) is str and report["compiler"]["selected"] != "" and
            type(report["compiler"].get("path")) is str and report["compiler"]["path"] != "" and
            report["compiler"]["path"] == report.get("final_selected_compiler") and
            isinstance(report["compiler"].get("target"), str) and report["compiler"]["target"] != "",
            "missing compiler identity/target conservation")
    matrices = report.get("matrices", [])
    require([row.get("optimization") for row in matrices] == list(OPTS), "missing/duplicate optimization matrix")
    binaries = report.get("binary_hashes", {})
    require(type(binaries) is dict and len(binaries) == len(OPTS) and
            binaries == report.get("final_binary_hashes") and
            set(binaries) == {row.get("binary_path") for row in matrices},
            "missing produced binary identities or final binary conservation")
    for matrix in matrices:
        opt = matrix["optimization"]
        require(matrix.get("flags") == build_flags(opt, sanitize), "missing/altered compile or sanitizer flags")
        require(re.fullmatch(r"[0-9a-f]{64}", matrix.get("binary_sha256", "")) is not None,
                "missing native binary identity")
        require(binaries.get(matrix["binary_path"]) == matrix["binary_sha256"],
                "matrix binary differs from conserved produced binary")
        require([row.get("id") for row in matrix.get("cases", [])] == [case.id for case in cases],
                "missing/duplicate/reordered frozen native cases")
        for case, row in zip(cases, matrix["cases"]):
            require(row.get("helper") == case.helper, "native helper identity mismatch")
            validate_native(row["actual"], case, host)
        invalid = matrix.get("invalid_arguments", [])
        require([row.get("argv") for row in invalid] == [list(args) for args in INVALID_ARGUMENTS],
                "missing probe input capability controls")
        for row in invalid:
            exact_result(row["actual"], {"status": 2, "stdout": "", "stderr": ""}, host)
        capabilities = matrix.get("capabilities", [])
        require([row.get("kind") for row in capabilities] == (list(CAPABILITIES) if sanitize else []),
                "missing/extra UBSan capability controls")
        for row in capabilities:
            validate_capability(row["actual"], row["kind"])


def sha(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            result.update(block)
    return result.hexdigest()


def source_hashes() -> dict[str, str]:
    return {name: sha(ROOT / name) for name in (*OWNED_SOURCE_NAMES, GUARD_SOURCE_NAME)}


def exception_descriptor(error: BaseException) -> dict[str, str]:
    # Never format an exception or its payload while preserving another one.
    try:
        name = type(error).__name__
        if type(name) is not str:
            name = "BaseException"
        return {"type": name[:128]}
    except BaseException:
        return {"type": "BaseException"}


class _Evidence:
    """Fixed-size secondary records; each independent action still runs."""
    def __init__(self):
        self.first = None
        self.failures = []

    def attempt(self, stage, action):
        try:
            return action()
        except BaseException as error:
            if self.first is None:
                self.first = error
            try:
                if len(self.failures) < 8:
                    self.failures.append({"stage": stage, **exception_descriptor(error)})
            except BaseException:
                pass

    def attach(self, primary):
        try:
            previous = object.__getattribute__(primary, "__dict__").get("c32_secondary_failures", ())
            safe = []
            if type(previous) is tuple:
                for row in previous[:8]:
                    if (type(row) is dict and set(row) == {"stage", "type"} and
                            all(type(value) is str and len(value) <= 128 for value in row.values())):
                        safe.append(row)
            primary.c32_secondary_failures = tuple((safe + self.failures)[:8])
        except BaseException:
            pass

    def raise_first(self):
        if self.first is not None:
            self.attach(self.first)
            raise self.first


@contextmanager
def sanitizer_environment(sanitize: bool):
    names = ("ASAN_OPTIONS", "LSAN_OPTIONS", "UBSAN_OPTIONS")
    previous = {name: os.environ.get(name) for name in names}
    cleanup = _Evidence()

    def restore():
        for name, value in previous.items():
            def action(name=name, value=value):
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value
            cleanup.attempt("restore-" + name, action)

    try:
        for name in names:
            os.environ.pop(name, None)
        if sanitize:
            os.environ["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1:exitcode=88"
        yield
    except BaseException as primary:
        try:
            restore()
            cleanup.attach(primary)
        except BaseException:
            pass
        raise
    else:
        restore()
        cleanup.raise_first()


class Conservation:
    def __init__(self, clang: Path, frozen: Path, report: dict):
        self.clang, self.frozen, self.report = clang, frozen, report
        self.selected = Path(report["compiler"].get("selected", str(clang)))
        self.expected_sources = dict(report["source_hashes"])
        self.expected_compiler = report["compiler"]["sha256"]
        self.binaries = {}

    def check(self):
        require(source_hashes() == self.expected_sources, "original source conservation failed")
        require({name: sha(self.frozen / name) for name in self.expected_sources} == self.expected_sources,
                "frozen source conservation failed")
        require(self.selected.resolve(strict=True) == self.clang and
                sha(self.selected) == self.expected_compiler and sha(self.clang) == self.expected_compiler,
                "selected/resolved compiler conservation failed")
        require(all(sha(path) == digest for path, digest in self.binaries.items()),
                "produced binary conservation failed")

    def admit_binary(self, path: Path):
        self.check()
        require(path not in self.binaries, "duplicate produced binary identity")
        self.binaries[path] = sha(path)
        self.check()

    def final_pins(self):
        self.check()
        self.report["final_source_hashes"] = source_hashes()
        self.report["final_frozen_source_hashes"] = {name: sha(self.frozen / name) for name in self.expected_sources}
        self.report["final_compiler_sha256"] = sha(self.clang)
        self.report["final_selected_compiler"] = str(self.selected.resolve(strict=True))
        self.report["binary_hashes"] = {str(path): digest for path, digest in self.binaries.items()}
        self.report["final_binary_hashes"] = {str(path): sha(path) for path in self.binaries}
        self.check()


def load_checks(frozen: Path):
    # Execute the frozen source explicitly; an existing .pyc cannot substitute
    # different process guards. __file__ keeps their repo-owned cwd contract.
    name = "v4_c_integer_runtime_checks"
    module = types.ModuleType(name)
    module.__file__ = str(ROOT / GUARD_SOURCE_NAME)
    sys.modules[name] = module
    exec(compile(frozen.read_bytes(), module.__file__, "exec"), module.__dict__)
    return module


class Runner:
    def __init__(self, checks, directory: Path, conservation=None):
        self.checks, self.directory, self.serial = checks, directory, 0
        self.conservation = conservation

    def run(self, argv: list[str], label: str, *, compiling: bool = False):
        self.serial += 1
        stem = self.directory / f"{self.serial:03d}-{re.sub(r'[^a-zA-Z0-9_-]', '-', label)}"
        timeout = COMPILE_SECONDS if compiling else RUN_SECONDS
        memory = COMPILE_MIB if compiling else RUN_MIB
        record = {"argv": argv, "timeout_seconds": timeout, "memory_limit_mib": memory,
                  "output_limit_mib_per_stream": OUTPUT_MIB, "status": "started"}
        command_path = stem.with_suffix(".command.json")
        command_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        retention = _Evidence()

        def conserve():
            if self.conservation is not None:
                self.conservation.check()

        def write_channel(error_or_result, name, attribute):
            value = getattr(error_or_result, attribute, None)
            if value is not None:
                if type(value) is str:
                    value = value.encode("utf-8")
                require(type(value) is bytes, "unexpected channel payload type")
                stem.with_suffix("." + name).write_bytes(value[:OUTPUT_MIB * 1048576])

        def secondary_record():
            stem.with_suffix(".retention.json").write_text(
                json.dumps({"secondary_failures": retention.failures}, indent=2) + "\n", encoding="utf-8")

        try:
            conserve()
            result = self.checks.run_with_heartbeat(argv, label=label, timeout_seconds=timeout,
                                                  memory_limit_mb=memory, output_limit_mb=OUTPUT_MIB)
        except BaseException as primary:
            try:
                retention.attempt("failure-attribution", lambda: record.update(
                    status="raised", error_type=exception_descriptor(primary)["type"]))
                retention.attempt("post-job-conservation", conserve)
                retention.attempt("command-attribution", lambda: command_path.write_text(
                    json.dumps(record, indent=2) + "\n", encoding="utf-8"))
                retention.attempt("failure-descriptor", lambda: stem.with_suffix(".failure.txt").write_text(
                    json.dumps(exception_descriptor(primary)) + "\n", encoding="utf-8"))
                retention.attempt("partial-stdout", lambda: write_channel(primary, "stdout", "output"))
                retention.attempt("partial-stderr", lambda: write_channel(primary, "stderr", "stderr"))
                retention.attempt("retention-metadata", secondary_record)
                retention.attach(primary)
            except BaseException:
                pass
            raise
        retention.attempt("post-job-conservation", conserve)
        retention.attempt("result-attribution", lambda: record.update(status="finished", returncode=result.returncode))
        retention.attempt("command-attribution", lambda: command_path.write_text(
            json.dumps(record, indent=2) + "\n", encoding="utf-8"))
        for name in ("stdout", "stderr"):
            retention.attempt("result-" + name, lambda name=name: write_channel(result, name, name))
        retention.attempt("result-publication", lambda: stem.with_suffix(".result.json").write_text(
            json.dumps(observed(result), indent=2) + "\n", encoding="utf-8"))
        retention.attempt("retention-metadata", secondary_record)
        retention.raise_first()
        return result


def run_gate(clang: Path, directory: Path, report: dict, sanitize: bool) -> Conservation:
    frozen = directory / "frozen-source"
    for name, expected_hash in report["source_hashes"].items():
        out = frozen / name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes((ROOT / name).read_bytes())
        require(sha(out) == expected_hash, "source changed while freezing native inputs")
    conservation = Conservation(clang, frozen, report)
    conservation.check()
    cases = load_vectors(frozen / "tests/v4_c_integer_runtime_vectors.json")
    checks = load_checks(frozen / GUARD_SOURCE_NAME)
    conservation.check()
    runner = Runner(checks, directory, conservation)
    version = runner.run([str(clang), "--version"], "compiler-version", compiling=True)
    require(version.returncode == 0 and "clang" in version.stdout.lower(), "Clang identity unavailable")
    target = runner.run([str(clang), "-dumpmachine"], "compiler-target", compiling=True)
    target_text = channel(target.stdout, sys.platform)
    require(target.returncode == 0 and re.fullmatch(r"[^\s]+\n?", target_text) is not None,
            "native compiler target unavailable")
    report["compiler"].update(version=version.stdout, target=target_text.rstrip("\n"))
    runtime = frozen / "freakc/runtime"
    suffix = ".exe" if sys.platform == "win32" else ""
    for opt in OPTS:
        flags = build_flags(opt, sanitize)
        binary = directory / (f"c32-O{opt}" + suffix)
        command = [str(clang), *flags, "-I", str(runtime),
                   str(frozen / "tests/v4_c_integer_runtime_probe.c"),
                   str(runtime / "freak_v4_c_integer_runtime.c"), "-o", str(binary)]
        compiled = runner.run(command, f"compile-O{opt}", compiling=True)
        require(compiled.returncode == 0, f"checked32 O{opt} compilation failed")
        conservation.admit_binary(binary)
        matrix = {"optimization": opt, "flags": flags, "binary_path": str(binary), "binary_sha256": sha(binary),
                  "cases": [], "invalid_arguments": [], "capabilities": []}
        report["matrices"].append(matrix)
        for case in cases:
            actual = observed(runner.run([str(binary), *case.arguments], f"O{opt}-{case.id}"))
            matrix["cases"].append({"id": case.id, "helper": case.helper, "actual": actual})
            validate_native(actual, case, sys.platform)
        for index, argv in enumerate(INVALID_ARGUMENTS):
            actual = observed(runner.run([str(binary), *argv], f"O{opt}-invalid-{index}"))
            matrix["invalid_arguments"].append({"argv": list(argv), "actual": actual})
            exact_result(actual, {"status": 2, "stdout": "", "stderr": ""}, sys.platform)
        if sanitize:
            for kind in CAPABILITIES:
                actual = observed(runner.run([str(binary), "--ubsan-" + kind], f"O{opt}-ubsan-{kind}"))
                matrix["capabilities"].append({"kind": kind, "actual": actual})
                validate_capability(actual, kind)
        conservation.check()
        print(f"checked32 O{opt}: 58 vectors, 10 invalid-input controls, {len(matrix['capabilities'])} UBSan controls verified; final pins pending", flush=True)
    conservation.final_pins()
    validate_report(dict(report, complete=True), cases, sanitize)
    return conservation


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG") or shutil.which("clang"))
    parser.add_argument("--plain", action="store_true", help="all-OS portability proof; separate from mandatory Linux UBSan gate")
    parser.add_argument("--work", required=True, type=Path, help="new empty external evidence directory")
    args = parser.parse_args()
    if sys.platform not in ("linux", "darwin", "win32"):
        parser.error("checked32 native gate requires Linux, macOS or Windows")
    if not args.plain and sys.platform != "linux":
        parser.error("mandatory UBSan gate requires Linux; --plain is the separate portability matrix")
    if not args.clang:
        parser.error("Clang is required; missing sanitizer/compiler capability is a failure")
    selected = Path(shutil.which(args.clang) or args.clang).absolute()
    clang = selected.resolve(strict=True)
    if clang.name.lower() in ("cl", "cl.exe", "clang-cl", "clang-cl.exe"):
        parser.error("use the Clang C driver; O3 cannot be replaced with MSVC O2")
    directory = args.work.resolve()
    if directory.is_relative_to(ROOT):
        parser.error("--work must be outside the repository")
    directory.mkdir(parents=True, exist_ok=True)
    if any(directory.iterdir()):
        parser.error("--work must be empty; stale artifacts cannot satisfy the gate")
    report = {"complete": False, "scope": "checked32 C helper prerequisite; no V4 C-width admission",
              "platform": sys.platform, "machine": platform.machine(), "sanitized": not args.plain,
              "source_hashes": source_hashes(), "compiler": {"selected": str(selected), "path": str(clang), "sha256": sha(clang)},
              "matrices": []}
    report_path = directory / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    try:
        with sanitizer_environment(not args.plain):
            conservation = run_gate(clang, directory, report, not args.plain)
        conservation.final_pins()
        candidate = dict(report, complete=True)
        validate_report(candidate, load_vectors(directory / "frozen-source/tests/v4_c_integer_runtime_vectors.json"), not args.plain)
        pending = report_path.with_suffix(".pending.json")
        pending.write_text(json.dumps(candidate, indent=2) + "\n", encoding="utf-8")
        conservation.check()
        os.replace(pending, report_path)
        conservation.check()
        report["complete"] = True
    except BaseException as primary:
        try:
            retention = _Evidence()
            report.update(complete=False, failure=exception_descriptor(primary))
            retention.attempt("failure-report-publication", lambda: report_path.write_text(
                json.dumps(report, indent=2) + "\n", encoding="utf-8"))
            retention.attach(primary)
        except BaseException:
            pass
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
