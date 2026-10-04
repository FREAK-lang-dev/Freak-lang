#!/usr/bin/env python3
"""Prove generated sized stderr, immutable loans and cleanup at O0/O2/O3.

Default requires Linux ASan+UBSan and real controls; --plain is a separate
all-OS proof. Compiler cases retain 64 MiB/1024 handles. Generated-program build
and execution commands/output, modules, binaries and partial reports remain in
a required fresh --work directory.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
from v4_checked_numeric_codegen import (  # noqa: E402
    AUDIT_FLAGS, SANITIZER_FLAGS, GateError, Runner, exact_result, load_build,
    normalized, require_compile, sanitizer_environment, sha,
    validate_build_flags, validate_sanitizer_probe,
)

OPTS = (0, 2, 3)
CALL_COUNTS = (7, 2, 0)
OUTPUTS = (
    ("stdout:begin\nA\0é中😀\ninner\nA\0é中😀!\nstdout:end\n",
     "A\0é中😀\nA\0é中😀\nA\0é中😀!\ninner\nA\0é中😀!\nA\0é中😀!\nearly\0🦊\n\n"),
    ("stdout:begin\nreceiver:TEMP\0é\nreceiver:LEFT\nreceiver:RIGHT\nstdout:end\n",
     "TEMP\0é\nLEFTRIGHT\n"),
    ("ordinary:shadow\n", ""),
)
BEGIN = "@@LLVM-MODULE-BEGIN\n"
END = "@@LLVM-MODULE-END\n"


def prefix(case: int) -> str:
    if case not in range(len(OUTPUTS)):
        raise GateError("unknown stderr compiler case")
    return (f"say-err-proof case={case} calls={CALL_COUNTS[case]} borrowed=true "
            "restore=true old-seal=true fresh-module=true\n")


def fixture_sources(text: str) -> list[str]:
    """Read the closed literal/brace/Unicode fixture table; never eval source."""
    def read(node: ast.AST) -> str:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return read(node.left) + read(node.right)
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "chr" and len(node.args) == 1 and not node.keywords
                and isinstance(node.args[0], ast.Constant)
                and type(node.args[0].value) is int
                and node.args[0].value in (123, 125, 233, 20013, 128512, 129418)):
            return chr(node.args[0].value)
        raise GateError("stderr source table permits only literals, + and closed brace/Unicode chr")

    match = re.search(r"(?ms)^task v4_say_err_proof_source\(case_id: int\) -> word \{\n(.*?)^\}", text)
    if match is None:
        raise GateError("missing stderr compiler source table")
    rows = {}
    for line in match[1].splitlines():
        row = re.fullmatch(r"\s*if case_id == (\d+) \{ give back (.*) \}\s*", line)
        if row:
            index = int(row[1])
            if index in rows:
                raise GateError("duplicate stderr source case")
            try:
                rows[index] = read(ast.parse(row[2], mode="eval").body)
            except (SyntaxError, RecursionError) as exc:
                raise GateError("invalid stderr source expression") from exc
        elif line.strip() not in ('panic("unknown say-err-proof case")', 'give back ""', ""):
            raise GateError("unexpected stderr source table row")
    if set(rows) != set(range(len(OUTPUTS))):
        raise GateError("missing or unknown stderr source case")
    return [rows[index] for index in range(len(OUTPUTS))]


def extract_module(result, case: int, *, platform: str = sys.platform) -> str:
    stdout = normalized(result.stdout, platform)
    if result.returncode != 0 or result.stderr:
        raise GateError("stderr compiler did not exit cleanly")
    if (not stdout.startswith(prefix(case) + BEGIN) or not stdout.endswith(END)
            or stdout.count(BEGIN) != 1 or stdout.count(END) != 1):
        raise GateError("stderr compiler protocol mismatch")
    module = stdout[len(prefix(case) + BEGIN):-len(END)]
    if not module.strip() or not re.search(r"(?m)^define i32 @main\(", module):
        raise GateError("stderr module lacks a real native entry")
    # Anchored instructions cannot be satisfied by declarations or comments.
    calls = re.findall(r"(?m)^\s*call void @freak_v4_word_say_err\(i64 [^\n]+\)\s*$", module)
    if len(calls) != CALL_COUNTS[case]:
        raise GateError("stderr module has the wrong actual closed call count")
    if case == 2 and not re.search(r"(?m)^\s*call (?:ccc )?void @say_err\(i64 [^\n]+\)\s*$", module):
        raise GateError("ordinary say_err shadow has no actual ordinary call")
    return module


def exact_program(result, case: int, *, platform: str = sys.platform) -> None:
    stdout, stderr = OUTPUTS[case]
    exact_result(result, 0, stdout, stderr, f"stderr program {case}", platform)


def validate_report(report: dict, sanitize: bool) -> None:
    if report.get("sanitizers") is not sanitize or report.get("ownership_audits") != ["C", "LLVM"]:
        raise GateError("stderr report omits its mode or required audits")
    compiler = report.get("compiler_contracts", [])
    if ([row.get("case") for row in compiler] != list(range(len(OUTPUTS)))
            or any(row.get("status") != "pass" for row in compiler)):
        raise GateError("stderr report lacks all compiler/restore contracts")
    for opt in OPTS:
        flags = report.get("build_flags", {}).get(str(opt), [])
        validate_build_flags(flags, sanitize)
        if [flag for flag in flags if re.fullmatch(r"-O.*", flag)] != [f"-O{opt}"]:
            raise GateError("stderr report has a missing/conflicting optimization")
        if not sanitize and any(flag.startswith("-fsanitize") for flag in flags):
            raise GateError("plain stderr proof unexpectedly uses sanitizers")
    wanted = {(case, opt) for case in range(len(OUTPUTS)) for opt in OPTS}
    programs = report.get("programs", [])
    keys = [(row.get("case"), row.get("optimization")) for row in programs]
    if len(keys) != len(wanted) or set(keys) != wanted:
        raise GateError("stderr program matrix is missing or duplicated")
    for row in programs:
        stdout, stderr = OUTPUTS[row["case"]]
        if (row.get("status") != "pass" or row.get("exit") != 0
                or row.get("stdout_sha256") != hashlib.sha256(stdout.encode()).hexdigest()
                or row.get("stderr_sha256") != hashlib.sha256(stderr.encode()).hexdigest()):
            raise GateError("stderr program report has incorrect exact output/status")
    wanted_controls = {f"audit-{kind}-O{opt}" for kind in ("C", "LLVM") for opt in OPTS}
    if sanitize:
        wanted_controls |= {"sanitizer-address", "sanitizer-undefined"}
    controls = report.get("controls", [])
    names = [row.get("name") for row in controls]
    if (len(names) != len(wanted_controls) or set(names) != wanted_controls
            or any(row.get("status") != "pass" for row in controls)):
        raise GateError("stderr report lacks real sanitizer/audit controls")
    inputs = report.get("input_hashes")
    if not isinstance(inputs, dict) or not inputs or report.get("final_input_hashes") != inputs:
        raise GateError("stderr proof source inputs changed while running")


def run_gate(args, report: dict) -> None:
    build = load_build()
    from freakc.v4_native_runtime import HEADER_NAMES
    checks = build.checks
    directory = args.work.resolve()
    runner = Runner(checks, directory)
    fixture = checks.TESTS_ROOT / "say_err_execute_smoke.fk"
    runtime_paths = [checks.RUNTIME_ROOT / name for name in build.SOURCE_NAMES]
    headers = [checks.RUNTIME_ROOT / name for name in HEADER_NAMES]
    inputs = [fixture, Path(__file__), Path(__file__).with_name("test_v4_say_err_codegen.py"),
              Path(checks.__file__), Path(build.__file__), ROOT / "freakc/v4_native_runtime.py",
              ROOT / "tests/v4_checked_numeric_codegen.py", *runtime_paths, *headers,
              *(checks.crate_path(name) for name in checks.CRATE_ORDER)]
    report["input_hashes"] = {str(path.relative_to(ROOT)): sha(path) for path in inputs}
    try:
        sources = fixture_sources(checks.read_text(fixture))
        target = build.host_target()
        report["target"] = target
        identity = runner.run([args.clang, "--version"], "clang identity", timeout=10)
        require_compile(identity, "clang identity")
        if not identity.stdout.strip():
            raise GateError("Clang identity is empty")
        report["clang_identity"] = identity.stdout
        for case, source in enumerate(sources):
            (directory / f"case-{case}.fk").write_text(source, encoding="utf-8")
        compiler_dir = directory / "compiler"
        compiler_dir.mkdir()
        old_root = checks.RUNTIME_BUILD_ROOT
        checks.RUNTIME_BUILD_ROOT = compiler_dir
        try:
            c_source, ui = checks.transpile_fixture(checks.check_flattened_crates(), fixture)
            if ui:
                raise GateError("stderr compiler unexpectedly requires UI")
            try:
                probe, _ = checks.compile_runtime_smoke(
                    args.clang, f"-I{checks.RUNTIME_ROOT}", checks.RUNTIME_ROOT / "freak_runtime.c",
                    checks.read_text(checks.RUNTIME_ROOT / "freak_runtime.c"), fixture, c_source,
                    ("-DFREAK_ARRAY_LIVE_LIMIT=1024",),
                )
            except SystemExit as exc:
                raise GateError(f"stderr bootstrap compilation failed: {exc.code}") from exc
        finally:
            checks.RUNTIME_BUILD_ROOT = old_root
        report["compiler"] = {"sha256": sha(probe), "memory_limit_mib": 64, "live_handle_limit": 1024}
        modules = []
        for case in range(len(OUTPUTS)):
            emitted = runner.run([str(probe), str(case), target, "--emit"], f"emit case {case}")
            module = extract_module(emitted, case)
            llvm = directory / f"case-{case}.ll"
            llvm.write_text(module, encoding="utf-8")
            modules.append(llvm)
            report["compiler_contracts"].append({"case": case, "status": "pass", "module_sha256": sha(llvm)})
        audit = directory / "audit_probe.c"
        audit.write_text('#include "freak_runtime.h"\n#include "freak_v4_word_runtime.h"\n'
                         'int main(int argc, char **argv) {\n if (argc != 2) return 9;\n'
                         ' if (argv[1][0] == \'C\') { volatile freak_word w = freak_word_from_int(7); (void)w; }\n'
                         ' else { volatile int64_t w = freak_v4_word_from_int(7); (void)w; }\n return 0;\n}\n', encoding="utf-8")
        suffix = ".exe" if sys.platform == "win32" else ".native"
        object_suffix = ".obj" if sys.platform == "win32" else ".o"
        for opt in OPTS:
            flags = ["-w", f"-O{opt}", f"-I{checks.RUNTIME_ROOT}", *AUDIT_FLAGS]
            if not args.plain:
                flags += SANITIZER_FLAGS
            validate_build_flags(flags, not args.plain)
            report["build_flags"][str(opt)] = flags
            objects = []
            for source in runtime_paths:
                output = directory / f"{source.stem}.O{opt}{object_suffix}"
                require_compile(runner.run([args.clang, *flags, "-c", str(source), "-o", str(output)],
                                          f"compile {source.stem} O{opt}", timeout=120, memory=512), str(source))
                objects.append(str(output))
            audit_binary = directory / f"audit-probe.O{opt}{suffix}"
            require_compile(runner.run([args.clang, *flags, str(audit), *objects, "-o", str(audit_binary),
                                       *checks.runtime_platform_final_link_args()], f"link audit O{opt}", timeout=120, memory=512), "audit probe")
            for kind, status in (("C", 87), ("LLVM", 86)):
                observed = runner.run([str(audit_binary), kind], f"audit {kind} O{opt}", timeout=30, memory=128)
                exact_result(observed, status, "", f"FREAK: {kind} ownership audit found 1 unreleased word allocation(s)\n", kind)
                report["controls"].append({"name": f"audit-{kind}-O{opt}", "status": "pass"})
            for case, llvm in enumerate(modules):
                binary = directory / f"case-{case}.O{opt}{suffix}"
                require_compile(runner.run([args.clang, *flags, str(llvm), *objects, "-o", str(binary),
                                           *checks.runtime_platform_final_link_args()], f"link case {case} O{opt}", timeout=120, memory=512), "stderr program")
                observed = runner.run([str(binary)], f"execute case {case} O{opt}", timeout=30, memory=128)
                exact_program(observed, case)
                report["programs"].append({"case": case, "optimization": opt, "status": "pass",
                                           "exit": observed.returncode, "binary_sha256": sha(binary),
                                           "stdout_sha256": hashlib.sha256(normalized(observed.stdout, sys.platform).encode()).hexdigest(),
                                           "stderr_sha256": hashlib.sha256(normalized(observed.stderr, sys.platform).encode()).hexdigest()})
        if not args.plain:
            source = directory / "sanitizer_probe.c"
            source.write_text('#include <stdlib.h>\n#include <limits.h>\nint main(int argc, char **argv) {\n'
                              ' if (argc != 2) return 9;\n if (argv[1][0] == \'a\') { volatile char *p = malloc(1); free((void*)p); return p[0]; }\n'
                              ' volatile int value = INT_MAX; volatile int one = 1; return value + one;\n}\n', encoding="utf-8")
            binary = directory / ("sanitizer-probe" + suffix)
            require_compile(runner.run([args.clang, "-O0", *SANITIZER_FLAGS, str(source), "-o", str(binary)],
                                      "link sanitizer capabilities", timeout=120, memory=512), "sanitizer controls")
            for kind in ("address", "undefined"):
                observed = runner.run([str(binary), kind], f"sanitizer {kind}", timeout=30, memory=128)
                validate_sanitizer_probe(observed, kind)
                report["controls"].append({"name": "sanitizer-" + kind, "status": "pass"})
    finally:
        report["final_input_hashes"] = {str(path.relative_to(ROOT)): sha(path) for path in inputs}
    validate_report(report, not args.plain)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG") or shutil.which("clang"))
    parser.add_argument("--plain", action="store_true")
    parser.add_argument("--work", type=Path, required=True, help="new evidence directory; existing paths fail")
    args = parser.parse_args(argv)
    if not args.clang:
        parser.error("clang is required; stderr proof cannot be skipped")
    if not args.plain and not sys.platform.startswith("linux"):
        parser.error("mandatory sanitizers require Linux; use --plain additionally on other OSes")
    args.work = args.work.resolve()
    args.work.mkdir(parents=True, exist_ok=False)
    report = {"schema": "v4-say-err-codegen-v1", "passed": False, "sanitizers": not args.plain,
              "ownership_audits": ["C", "LLVM"], "compiler_contracts": [], "build_flags": {},
              "controls": [], "programs": []}
    try:
        with sanitizer_environment(not args.plain):
            run_gate(args, report)
        report["passed"] = True
        print("say_err: 3 compiler/restore cases, 9 native programs, exact sized channels, "
              + ("plain PASS" if args.plain else "ASan+UBSan PASS"), flush=True)
        return 0
    except Exception as exc:
        report["error"] = str(exc)
        print(f"say_err proof FAILED: {exc}", file=sys.stderr, flush=True)
        return 1
    finally:
        records = {str(path.relative_to(args.work)): {"sha256": sha(path), "bytes": path.stat().st_size}
                   for path in sorted(args.work.rglob("*")) if path.is_file()}
        report["artifacts"] = records
        (args.work / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
