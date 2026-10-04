#!/usr/bin/env python3
"""Run every checked V4 numerical program at O0/O2/O3 with exact oracles.

ASan, UBSan/float-cast-overflow and both ownership audits are required by
default. --plain is a separate portability proof. --snapshot-control adds
the 13-body snapshot restore/sealed-module/fresh-module control. Generated
sources, LLVM, binaries, command logs and partial/final JSON remain in --work.
No missing compiler, runtime, program or optimization level is a skip.
"""
from __future__ import annotations

import argparse
import ast
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
OPTS = (0, 2, 3)
CASE_COUNT = 48
AUDIT_FLAGS = ("-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1", "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1")
SANITIZER_FLAGS = ("-g", "-fsanitize=address,undefined,float-cast-overflow",
                   "-fno-sanitize-recover=all", "-fno-omit-frame-pointer")
SNAPSHOT_FLAGS = ("valid", "restored", "sealed-stable", "module-exact")


class GateError(RuntimeError):
    pass


@dataclass(frozen=True)
class Case:
    index: int
    source: str
    stderr: str

    @property
    def exit(self) -> int:
        return 1 if self.stderr else 0


def expected_errors() -> tuple[str, ...]:
    messages = []
    for kind in ("int", "uint", "tiny"):
        messages += [f"{kind} addition overflow",
                     f"{kind} subtraction {'overflow' if kind == 'int' else 'underflow'}",
                     f"{kind} multiplication overflow",
                     f"{kind} negation {'overflow' if kind == 'int' else 'underflow'}",
                     f"{kind} division by zero", f"{kind} remainder by zero"]
        if kind == "int":
            messages += ["int division overflow", "int remainder overflow"]
    messages += [f"{source} to {target} conversion out of range" for source, target in
                 (("int", "uint"), ("int", "tiny"), ("uint", "int"), ("uint", "tiny"),
                  ("num", "int"), ("num", "uint"), ("num", "tiny"))]
    messages += [f"num to {target} conversion out of range" for target in
                 ("int", "uint", "tiny", "int", "tiny", "uint", "int", "int", "int")]
    messages += ["uint to int conversion out of range", "num to int conversion out of range",
                 "num to tiny conversion out of range", "num to tiny conversion out of range"]
    return tuple(f"FREAK V4: {message}\n" for message in messages)


def literal_expression(expression: str) -> str:
    """Read the fixture's deliberately literal-only source table, never eval it."""
    def read(node: ast.AST) -> str:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return read(node.left) + read(node.right)
        raise GateError("numeric fixture table must contain only string literals and +")
    try:
        return read(ast.parse(expression, mode="eval").body)
    except (SyntaxError, RecursionError) as exc:
        raise GateError(f"invalid numeric fixture source table: {exc}") from exc


def expected_errors_by_case() -> dict[int, str]:
    return {**dict(enumerate(expected_errors())),
            47: "FREAK V4: int to tiny conversion out of range\n"}


def fixture_table(text: str, name: str) -> dict[int, str]:
    match = re.search(r"(?ms)^task " + re.escape(name) +
                      r"\(case_id: int\) -> word \{\n(.*?)^\}", text)
    if match is None:
        raise GateError(f"missing numeric fixture function {name}")
    rows: dict[int, str] = {}
    for line in match[1].splitlines():
        row = re.fullmatch(r"\s*if case_id == (\d+) \{ give back (.*) \}\s*", line)
        if row:
            index = int(row[1])
            if index in rows:
                raise GateError(f"duplicate numeric case {index} in {name}")
            rows[index] = literal_expression(row[2])
        elif line.strip() not in ('panic("unknown checked numeric native case")', 'give back ""', ""):
            raise GateError(f"unexpected numeric fixture table row: {line}")
    return rows


def load_cases(text: str) -> list[Case]:
    sources = fixture_table(text, "v4_checked_numeric_native_source")
    errors = fixture_table(text, "v4_checked_numeric_native_stderr")
    if set(sources) != set(range(CASE_COUNT)) or any(not source for source in sources.values()):
        raise GateError("numeric fixture must contain exactly all 48 nonempty cases (0..47)")
    expected = expected_errors_by_case()
    if errors != expected:
        raise GateError("numeric fixture fatal diagnostics differ from the checked helper oracle")
    return [Case(index, sources[index], errors.get(index, "")) for index in range(CASE_COUNT)]


def contract_arguments() -> list[list[str]]:
    arguments = [["6"], ["3", "256"], ["3", "257"], ["3", "10000"], ["4"],
                 *[["5", room] for room in ("0", "16", "24", "32")], ["7"]]
    for kind, text in (("int", "9223372036854775808"), ("int", "-9223372036854775809"),
                       ("int", "1u"), ("int", "1.5"), ("int", "1x"),
                       ("uint", "18446744073709551616"), ("uint", "-1"), ("tiny", "256"), ("tiny", "-1")):
        arguments.append(["0", kind, text])
    for kind, text in (("int", "9223372036854775808"), ("int", "-9223372036854775809"),
                       ("uint", "18446744073709551616u"), ("tiny", "256t")):
        arguments.append(["1", kind, text])
    for kind, text in (("num", "0.5\n call i64 @freak_v4_word_from_int(i64 1)"),
                       ("num", "nan"), ("num", "0.5f"), ("num", "0.5e3"), ("num", "0."),
                       ("num", "+0.5"), ("num", "9" * 400 + ".0"),
                       ("num", "0." + "0" * 400 + "1"),
                       ("float32", "3402823466385288598117041834845169254400.0")):
        arguments.append(["8", kind, text])
    helpers = [f"freak_v4_{kind}_{operation}" for kind in ("int", "uint", "tiny")
               for operation in ("add", "sub", "mul", "neg", "div", "mod")]
    helpers += [f"freak_v4_{target}_from_{source}" for target in ("int", "uint", "tiny", "num")
                for source in ("int", "uint", "tiny", "num") if target != source]
    helpers += ["freak_llvm_word_owned_size", "freak_v4_word_from_int", "freak_v4_process_arg", "freak_v4_fs_read"]
    for helper in helpers:
        arguments.append(["9", helper])
        arguments += [["2", helper, mode] for mode in ("body", "extern")]
    arguments += [["9", "make"], ["9", "unknown_target"], ["10"]]
    arguments += [["11", kind] for kind in ("lend", "owned", "return", "nested")]
    return arguments


def contract_stdout(arguments: list[str]) -> str | None:
    case = int(arguments[0])
    end = f"checked-numeric-contract-case-{case}=passed\n"
    if case == 3 and arguments[1] == "256":
        return None  # Full framed LLVM is independently validated and executed.
    if case in (0, 1):
        kind, text = arguments[1:]
        error = "invalid native integer literal text" if text in ("1u", "1.5", "1x") else "native integer literal out of range: " + kind
        return "checked-numeric-rejected=" + error + "\n" + end
    if case in (2, 9):
        name = arguments[1]
        symbol = "@" + name
        if name.startswith("freak_v4_word_"):
            error = ("native owned word runtime symbol conflict: " if case == 2 else "native word runtime symbol conflict: ") + symbol
        elif name.startswith(("freak_v4_int_", "freak_v4_uint_", "freak_v4_tiny_", "freak_v4_num_")):
            error = "native numeric runtime symbol conflict: " + symbol
        elif name in ("make", "unknown_target"):
            error = ("native task pointer target contract mismatch: " if name == "make" else "native task pointer target is unresolved: ") + name
        else:
            error = "native private runtime symbol conflict: " + symbol
        return ("checked-numeric-rejected=" if case == 2 else "checked-numeric-symbol-error=") + error + "\n" + end
    if case == 3:
        return "checked-numeric-graph-error=native expression nesting exceeds supported depth\n" + end
    if case == 4:
        return "checked-numeric-rejected=native expression traversal exceeds supported budget\n" + end
    if case == 5:
        room = arguments[1]
        if room not in ("0", "16", "24", "32"):
            raise GateError("unsupported numeric pressure room")
        return ("checked-numeric-pressure-cleanup-error=native owned word cleanup scratch allocation failed\n"
                "checked-numeric-pressure-publication-error=native LLVM fragment scratch allocation failed\n"
                f"checked-numeric-pressure-room={room} error=native codegen plan arena allocation failed\n" + end)
    if case == 11:
        return "checked-numeric-word-pointer-error=native word task pointer contracts are not yet supported\n" + end
    return end


def validate_contract(result: subprocess.CompletedProcess[str], arguments: list[str], platform: str = sys.platform) -> str | None:
    expected = contract_stdout(arguments)
    if expected is None:
        return parse_module(result, platform=platform, depth=True)
    exact_result(result, 0, expected, "", "compiler contract " + " ".join(arguments), platform)
    return None


def normalized(text: str, platform: str) -> str:
    # Native Windows text streams translate LF to CRLF. Stray CR remains an
    # error everywhere, and POSIX output is compared byte-for-byte as decoded.
    return text.replace("\r\n", "\n") if platform.startswith("win") else text


def exact_result(result: subprocess.CompletedProcess[str], expected_exit: int,
                 stdout: str, stderr: str, label: str, platform: str = sys.platform) -> None:
    actual = (result.returncode, normalized(result.stdout, platform), normalized(result.stderr, platform))
    if actual != (expected_exit, stdout, stderr):
        raise GateError(f"{label}: expected exit={expected_exit}, stdout={stdout!r}, stderr={stderr!r}; "
                        f"actual exit={actual[0]}, stdout={actual[1]!r}, stderr={actual[2]!r}")


def parse_module(result: subprocess.CompletedProcess[str], *, platform: str = sys.platform,
                 snapshot: bool = False, depth: bool = False) -> str:
    if result.returncode != 0:
        raise GateError(f"compiler exited {result.returncode}")
    stdout = normalized(result.stdout, platform)
    stderr = normalized(result.stderr, platform)
    if depth:
        if stdout.splitlines().count("checked-numeric-contract-case-3=passed") != 1 or stderr:
            raise GateError("deep expression admission control did not pass")
    else:
        for row in ("checked-numeric-diag=0", "checked-numeric-error=", "checked-numeric-module-nonempty=true"):
            if stdout.splitlines().count(row) != 1:
                raise GateError(f"missing/ambiguous clean compiler fact: {row}")
        expected_phases = ["lex", "parse", "hir", "resolve", "ty", "mir", "codegen", "module"]
        if snapshot:
            expected_phases += ["snapshot-build", "snapshot-validate", "snapshot-restore", "snapshot-done"]
        expected_phases += ["done"]
        if stderr.splitlines() != ["checked-numeric-phase=" + phase for phase in expected_phases]:
            raise GateError("compiler phase/error stream differs from the expected protocol")
    if snapshot:
        if stdout.splitlines().count("checked-numeric-body-count=13") != 1:
            raise GateError("snapshot control must exercise the 13-body checked_numerics example")
        for flag in SNAPSHOT_FLAGS:
            if stdout.splitlines().count(f"checked-numeric-snapshot-{flag}=true") != 1:
                raise GateError(f"snapshot control failed/missing: {flag}")
    frames = list(re.finditer(r"(?ms)^@@LLVM-MODULE-BEGIN\n(.*?)^@@LLVM-MODULE-END$", stdout))
    if (len(frames) != 1 or stdout.splitlines().count("@@LLVM-MODULE-BEGIN") != 1
            or stdout.splitlines().count("@@LLVM-MODULE-END") != 1 or not frames[0][1].strip()):
        raise GateError("compiler must emit exactly one nonempty framed LLVM module")
    frame = frames[0]
    outside = [row for row in (stdout[:frame.start()] + stdout[frame.end():]).splitlines() if row]
    if depth:
        if sorted(outside) != sorted(["checked-numeric-contract-case-3=passed", "checked-numeric-graph-error="]):
            raise GateError("unexpected deep-expression compiler output")
    else:
        allowed = r"checked-numeric-(?:diag=0|error=|module-nonempty=true|body-count=\d+|body-\d+=.* rvalues=\d+ statements=\d+ locals=\d+)"
        if snapshot:
            allowed = allowed + r"|checked-numeric-snapshot-(?:bytes=\d+|(?:valid|restored|sealed-stable|module-exact)=true)"
        if any(re.fullmatch(allowed, row) is None for row in outside):
            raise GateError("unexpected compiler output outside LLVM frame")
    if re.search(r"\b(?:fptosi|fptoui)\b", frame[1]):
        raise GateError("unchecked floating-to-integer LLVM instruction")
    return frame[1]


def assemble_probe(execution: str, contracts: str, target: str = "x86_64-unknown-linux-gnu") -> str:
    execution_entry = "v4_checked_numeric_execute_run()"
    contract_entry = "v4_checked_numeric_contract_run(word_to_int(process::arg(1)))"
    if not execution.rstrip().endswith(execution_entry) or not contracts.rstrip().endswith(contract_entry):
        raise GateError("numeric fixture entry point changed")
    execution = execution.rstrip()[:-len(execution_entry)]
    contracts = contracts.rstrip()[:-len(contract_entry)]
    target_boundary = 'pilot target = v4_target_spec_new("x86_64-unknown-linux-gnu")'
    if contracts.count(target_boundary) != 1:
        raise GateError("numeric contract target boundary changed")
    contracts = contracts.replace(target_boundary, "pilot target = v4_target_spec_new(" + json.dumps(target) + ")")
    boundary = '        say_err("checked-numeric-phase=snapshot-done")'
    if execution.count(boundary) != 1:
        raise GateError("numeric snapshot fixture boundary changed")
    execution = execution.replace(boundary, '''        say "checked-numeric-snapshot-sealed-stable=" + word_from_bool(v4_codegen_llvm_module_text(codegen, target) == module)
        pilot restored_codegen = v4_codegen_llvm_lower_owned_mir(0, mir)
        say "checked-numeric-snapshot-module-exact=" + word_from_bool(v4_codegen_llvm_module_text(restored_codegen, target) == module)
''' + boundary)
    contracts = contracts.replace("process::arg(3)", "process::arg(4)").replace("process::arg(2)", "process::arg(3)")
    return execution + "\n" + contracts + '''
if process::arg(1) == "--contract" {
    v4_checked_numeric_contract_run(word_to_int(process::arg(2)))
} else { v4_checked_numeric_execute_run() }
'''


def validate_build_flags(flags: list[str], sanitize: bool) -> None:
    if not set(AUDIT_FLAGS).issubset(flags):
        raise GateError("both ownership audits are mandatory")
    if sanitize and not set(SANITIZER_FLAGS).issubset(flags):
        raise GateError("ASan + UBSan/float-cast-overflow build flags are mandatory")


def validate_sanitizer_probe(result: subprocess.CompletedProcess[str], kind: str,
                             platform: str = sys.platform) -> None:
    if kind not in ("address", "undefined"):
        raise GateError("unknown required sanitizer capability")
    stderr = normalized(result.stderr, platform)
    expected_exit = 88
    marker = "ERROR: AddressSanitizer: heap-use-after-free" if kind == "address" else "runtime error: signed integer overflow"
    if result.returncode != expected_exit or result.stdout != "" or marker not in stderr:
        raise GateError(f"{kind} sanitizer capability probe did not produce its required diagnostic/exit")


def validate_report(report: dict, sanitize: bool, snapshot: bool) -> None:
    if report.get("sanitizers") is not sanitize or report.get("snapshot_control") is not snapshot:
        raise GateError("gate report mode mismatch")
    if report.get("ownership_audits") != ["C", "LLVM"]:
        raise GateError("gate report omits required ownership audits")
    contracts = report.get("compiler_contracts", [])
    expected_contracts = contract_arguments()
    if len(contracts) != len(expected_contracts) or [row.get("arguments") for row in contracts] != expected_contracts or any(row.get("status") != "pass" for row in contracts):
        raise GateError("gate report lacks all 141 exact process-isolated compiler contracts")
    for opt in OPTS:
        flags = report.get("build_flags", {}).get(str(opt), [])
        validate_build_flags(flags, sanitize)
    wanted = {(f"case-{index}", opt) for index in range(CASE_COUNT) for opt in OPTS}
    wanted |= {(name, opt) for name in ("checked_numerics", "depth256") for opt in OPTS}
    rows = report.get("programs", [])
    seen = [(row.get("program"), row.get("optimization")) for row in rows]
    if len(seen) != len(wanted) or set(seen) != wanted or any(row.get("status") != "pass" for row in rows):
        raise GateError("gate report has missing, duplicate, failed or incomplete optimization cases")
    for row in rows:
        name = row["program"]
        stdout, stderr, status = "", "", 0
        if name.startswith("case-"):
            index = int(name[5:])
            if index in expected_errors_by_case():
                stderr, status = expected_errors_by_case()[index], 1
        if name == "checked_numerics":
            stdout = "checked numerics passed\n"
        if (row.get("exit") != status
                or row.get("stdout_sha256") != hashlib.sha256(stdout.encode()).hexdigest()
                or row.get("stderr_sha256") != hashlib.sha256(stderr.encode()).hexdigest()):
            raise GateError("gate report has incorrect native exit/output evidence")
    required_controls = {f"audit-{kind}-O{opt}" for kind in ("C", "LLVM") for opt in OPTS}
    if sanitize:
        required_controls |= {"sanitizer-address", "sanitizer-undefined"}
    controls = report.get("controls", [])
    if len(controls) != len(required_controls) or {row.get("name") for row in controls} != required_controls or any(row.get("status") != "pass" for row in controls):
        raise GateError("gate report lacks working sanitizer/audit capability controls")
    if snapshot and report.get("snapshot_facts") != {flag: True for flag in SNAPSHOT_FLAGS}:
        raise GateError("gate report lacks accepted restore, preserved seal or fresh regeneration")


@contextmanager
def sanitizer_environment(sanitize: bool):
    names = ("ASAN_OPTIONS", "LSAN_OPTIONS", "UBSAN_OPTIONS")
    previous = {name: os.environ.get(name) for name in names}
    try:
        for name in names:
            os.environ.pop(name, None)
        if sanitize:
            os.environ["ASAN_OPTIONS"] = "halt_on_error=1:detect_leaks=1:exitcode=88"
            # Combined ASan/UBSan share common runtime flags, including exitcode.
            os.environ["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1:exitcode=88"
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_build():
    sys.path.insert(0, str(ROOT / "src/compiler/v4"))
    import build_v4
    return build_v4


class Runner:
    def __init__(self, checks, directory: Path):
        self.checks = checks
        self.directory = directory
        self.serial = 0

    def run(self, command: list[str], label: str, *, timeout: int = 60, memory: int = 64):
        self.serial += 1
        stem = self.directory / f"{self.serial:03d}-{re.sub(r'[^a-zA-Z0-9_-]', '-', label)}"
        stem.with_suffix(".command.json").write_text(json.dumps(command, indent=2) + "\n", encoding="utf-8")
        try:
            result = self.checks.run_with_heartbeat(command, label=label, timeout_seconds=timeout, memory_limit_mb=memory)
        except Exception as exc:
            stem.with_suffix(".failure.txt").write_text(str(exc), encoding="utf-8")
            raise
        stem.with_suffix(".stdout").write_bytes(result.stdout.encode("utf-8"))
        stem.with_suffix(".stderr").write_bytes(result.stderr.encode("utf-8"))
        stem.with_suffix(".result.json").write_text(json.dumps({"exit": result.returncode, "memory_limit_mib": memory,
                                                               "timeout_seconds": timeout}, indent=2) + "\n", encoding="utf-8")
        return result


def require_compile(result, label: str) -> None:
    if result.returncode != 0:
        raise GateError(f"{label} failed with exit {result.returncode}: {result.stdout}{result.stderr}")


def run_gate(args, report: dict) -> None:
    build = load_build()
    from freakc.v4_native_runtime import HEADER_NAMES
    checks = build.checks
    target = build.host_target()
    report["target"] = target
    directory = args.work.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    runner = Runner(checks, directory)
    fixture = checks.TESTS_ROOT / "checked_numeric_execute_smoke.fk"
    contract_fixture = checks.TESTS_ROOT / "checked_numeric_contract_smoke.fk"
    execution, contracts = checks.read_text(fixture), checks.read_text(contract_fixture)
    cases = load_cases(execution)
    report["fixture_sources"] = {fixture.name: sha(fixture), contract_fixture.name: sha(contract_fixture)}
    report["driver_sha256"] = sha(Path(__file__))
    report["compiler_assembly_sha256"] = sha(Path(checks.__file__))
    report["compiler_crate_inputs"] = {name: sha(checks.crate_path(name)) for name in checks.CRATE_ORDER}
    git = shutil.which("git")
    if git:
        head = subprocess.run([git, "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
        report["compiler_head"] = head.stdout.strip() if head.returncode == 0 else None
    assembled = assemble_probe(execution, contracts, target)
    (directory / "probe.fk").write_text(assembled, encoding="utf-8")
    probe_fixture = checks.TESTS_ROOT / "checked_numeric_probe.fk"
    c_source, diagnostics, uses_ui = checks.transpile(checks.check_flattened_crates() + "\n" + assembled,
                                                     probe_fixture.with_suffix(".flat.fk"))
    if diagnostics or not c_source or uses_ui:
        raise GateError(f"numeric compiler assembly failed: {diagnostics}")
    old_root = checks.RUNTIME_BUILD_ROOT
    checks.RUNTIME_BUILD_ROOT = directory
    try:
        try:
            probe, _ = checks.compile_runtime_smoke(args.clang, f"-I{checks.RUNTIME_ROOT}",
                                                   checks.RUNTIME_ROOT / "freak_runtime.c",
                                                   checks.read_text(checks.RUNTIME_ROOT / "freak_runtime.c"),
                                                   probe_fixture, c_source,
                                                   (f"-DFREAK_ARRAY_LIVE_LIMIT={checks.C_ARRAY_HANDLE_RESOURCE_LIMIT}",))
        except SystemExit as exc:
            raise GateError(f"numeric bootstrap C compilation failed: exit {exc.code}") from exc
    finally:
        checks.RUNTIME_BUILD_ROOT = old_root
    report["compiler"] = {"sha256": sha(probe), "memory_limit_mib": 64,
                          "live_handle_limit": checks.C_ARRAY_HANDLE_RESOURCE_LIMIT,
                          "generated_c_sha256": sha(directory / "checked_numeric_probe.fk.c")}
    if checks.C_ARRAY_HANDLE_RESOURCE_LIMIT != 1024:
        raise GateError("numeric compiler live-handle contract changed from 1024")
    runtime_paths = [checks.RUNTIME_ROOT / name for name in build.SOURCE_NAMES]
    header_paths = [checks.RUNTIME_ROOT / name for name in HEADER_NAMES]
    if not runtime_paths or not header_paths or any(not path.is_file() for path in [*runtime_paths, *header_paths]):
        raise GateError("central native runtime source inventory is unavailable/incomplete")
    report["runtime_sources"] = {path.name: sha(path) for path in runtime_paths}
    report["runtime_headers"] = {path.name: sha(path) for path in header_paths}
    deep_module = None
    for index, arguments in enumerate(contract_arguments()):
        result = runner.run([str(probe), "--contract", *arguments], f"compiler contract {index}")
        module = validate_contract(result, arguments)
        if module is not None:
            deep_module = module
            (directory / "depth256.ll").write_bytes(module.encode("utf-8"))
        report["compiler_contracts"].append({"arguments": arguments, "status": "pass",
                                            "stdout_sha256": hashlib.sha256(normalized(result.stdout, sys.platform).encode()).hexdigest()})
    if deep_module is None:
        raise GateError("depth256 compiler/native control is missing")
    storage = directory / "native_storage.c"
    storage.write_text("#include <stdint.h>\nstatic uint8_t storage[8];\nuint8_t *numeric_case_storage(void) { return storage; }\n", encoding="utf-8")
    audit_probe = directory / "audit_probe.c"
    audit_probe.write_text('''#include "freak_runtime.h"
#include "freak_v4_word_runtime.h"
int main(int argc, char **argv) {
    if (argc != 2) return 9;
    if (argv[1][0] == 'C') { volatile freak_word value = freak_word_from_int(7); (void)value; }
    else { volatile int64_t value = freak_v4_word_from_int(7); (void)value; }
    return 0;
}
''', encoding="utf-8")
    suffix = ".exe" if sys.platform.startswith("win") else ".native"
    object_suffix = ".obj" if sys.platform.startswith("win") else ".o"
    objects = {}
    for opt in OPTS:
        flags = ["-w", f"-O{opt}", f"-I{checks.RUNTIME_ROOT}", *AUDIT_FLAGS]
        if not args.plain:
            flags += SANITIZER_FLAGS
        validate_build_flags(flags, not args.plain)
        report["build_flags"][str(opt)] = flags
        objects[opt] = []
        for source in [*runtime_paths, storage]:
            output = directory / (source.stem + f".O{opt}" + object_suffix)
            require_compile(runner.run([args.clang, *flags, "-c", str(source), "-o", str(output)],
                                      f"compile {source.stem} O{opt}", timeout=120, memory=512), str(source))
            objects[opt].append(str(output))
        binary = directory / (f"audit-probe.O{opt}" + suffix)
        require_compile(runner.run([args.clang, *flags, str(audit_probe), *objects[opt], "-o", str(binary),
                                   *checks.runtime_platform_final_link_args()], f"link audit O{opt}", timeout=120, memory=512), "audit probe")
        for kind, status in (("C", 87), ("LLVM", 86)):
            result = runner.run([str(binary), kind], f"audit {kind} O{opt}", timeout=30, memory=128)
            exact_result(result, status, "", f"FREAK: {kind} ownership audit found 1 unreleased word allocation(s)\n", f"audit {kind} O{opt}")
            report["controls"].append({"name": f"audit-{kind}-O{opt}", "status": "pass"})
    if not args.plain:
        source = directory / "sanitizer_probe.c"
        source.write_text('''#include <stdlib.h>
#include <limits.h>
int main(int argc, char **argv) {
    if (argc != 2) return 9;
    if (argv[1][0] == 'a') { volatile char *p = malloc(1); free((void *)p); return p[0]; }
    volatile int value = INT_MAX; volatile int one = 1; return value + one;
}
''', encoding="utf-8")
        binary = directory / ("sanitizer-probe" + suffix)
        require_compile(runner.run([args.clang, "-O0", *SANITIZER_FLAGS, str(source), "-o", str(binary)],
                                  "link sanitizer capabilities", timeout=120, memory=512), "sanitizer probe")
        for kind in ("address", "undefined"):
            result = runner.run([str(binary), kind], f"sanitizer {kind}", timeout=30, memory=128)
            validate_sanitizer_probe(result, kind)
            report["controls"].append({"name": "sanitizer-" + kind, "status": "pass"})
    modules = []
    for case in cases:
        name = f"case-{case.index}"
        (directory / (name + ".fk")).write_text(case.source, encoding="utf-8")
        result = runner.run([str(probe), "--case", str(case.index), target], "emit " + name)
        module = parse_module(result)
        (directory / (name + ".ll")).write_bytes(module.encode("utf-8"))
        modules.append((name, module, case.exit, "", case.stderr))
    source = checks.V4_ROOT / "examples" / "checked_numerics.fk"
    report["fixture_sources"][source.name] = sha(source)
    command = [str(probe), str(source), target]
    if args.snapshot_control:
        command += ["--snapshot", str(directory / "checked_numerics.mir-snapshot")]
    positive = runner.run(command, "emit checked_numerics snapshot" if args.snapshot_control else "emit checked_numerics")
    positive_module = parse_module(positive, snapshot=args.snapshot_control)
    (directory / "checked_numerics.ll").write_bytes(positive_module.encode("utf-8"))
    modules.append(("checked_numerics", positive_module, 0, "checked numerics passed\n", ""))
    if args.snapshot_control:
        report["snapshot_facts"] = {flag: True for flag in SNAPSHOT_FLAGS}
    modules.append(("depth256", deep_module, 0, "", ""))
    for name, module, status, stdout, stderr in modules:
        llvm = directory / (name + ".ll")
        llvm.write_bytes(module.encode("utf-8"))
        for opt in OPTS:
            binary = directory / (name + f".O{opt}" + suffix)
            require_compile(runner.run([args.clang, *report["build_flags"][str(opt)], str(llvm), *objects[opt],
                                       "-o", str(binary), *checks.runtime_platform_final_link_args()],
                                      f"link {name} O{opt}", timeout=120, memory=512), name)
            result = runner.run([str(binary)], f"execute {name} O{opt}", timeout=30, memory=128)
            exact_result(result, status, stdout, stderr, f"{name} O{opt}")
            report["programs"].append({"program": name, "optimization": opt, "status": "pass",
                                       "exit": result.returncode, "module_sha256": sha(llvm),
                                       "stdout_sha256": hashlib.sha256(normalized(result.stdout, sys.platform).encode()).hexdigest(),
                                       "stderr_sha256": hashlib.sha256(normalized(result.stderr, sys.platform).encode()).hexdigest()})
        print(f"{name}: O0/O2/O3 exact PASS", flush=True)
    validate_report(report, not args.plain, args.snapshot_control)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG") or shutil.which("clang"))
    parser.add_argument("--plain", action="store_true", help="explicit portability proof; sanitizers are mandatory by default")
    parser.add_argument("--snapshot-control", action="store_true", help="require 13-body snapshot restore and both module equality controls")
    parser.add_argument("--work", type=Path, default=ROOT / "build/v4_smoke/checked_numeric_codegen")
    parser.add_argument("--json", type=Path, help="partial/final report (default: WORK/results.json)")
    args = parser.parse_args(argv)
    if not args.clang:
        parser.error("clang is required; numerical native checks cannot be skipped")
    args.work.mkdir(parents=True, exist_ok=True)
    output = args.json or args.work / "results.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {"schema": "v4-checked-numeric-codegen-v1", "passed": False,
              "sanitizers": not args.plain, "snapshot_control": args.snapshot_control,
              "ownership_audits": ["C", "LLVM"], "build_flags": {}, "controls": [], "programs": [], "compiler_contracts": []}
    try:
        with sanitizer_environment(not args.plain):
            run_gate(args, report)
        report["passed"] = True
        print("checked numerical native gate PASS" + (" (plain portability)" if args.plain else " (ASan + UBSan)"), flush=True)
        return 0
    except Exception as exc:
        report["error"] = str(exc)
        print(f"checked numerical native gate FAILED: {exc}", file=sys.stderr, flush=True)
        return 1
    finally:
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
