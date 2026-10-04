#!/usr/bin/env python3
"""Prove generated Unicode word bounds and borrowed receivers at O0/O2/O3.

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
import signal
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
from v4_checked_numeric_codegen import (  # noqa: E402
    AUDIT_FLAGS, SANITIZER_FLAGS, GateError, Runner, exact_result, load_build,
    normalized, require_compile, sanitizer_environment, sha,
    validate_build_flags, validate_sanitizer_probe,
)

OPTS = (0, 2, 3)
VARIANTS = ("direct", "live")
NAMES = ("unicode-borrowed", "char-negative", "char-min", "char-end", "char-max", "char-empty",
         "slice-negative", "slice-min", "slice-reversed", "slice-end", "slice-max-end", "slice-max-start",
         "substring-negative-start", "substring-min-start", "substring-negative-count", "substring-min-count",
         "substring-start", "substring-count", "substring-max-count", "substring-max-start",
         "char-order", "slice-order", "substring-order", "temporary-chain")
WORD = "A\0é中😀"
HAPPY = ("5\n11\nA\n\0\né\n中\n😀\n" + WORD + "\n\0é中\n\n\n"
         + WORD + "\n\0é中\n\né\n" + WORD + "\n" + WORD + "\n\n\n")
OUTPUTS = tuple((HAPPY if case == 0 else "receiver:" + WORD + "\né\nreceiver:\n\n" if case == 23
                 else "receiver\nindex\n" if case == 20 else "receiver\nstart\nend\n" if case == 21
                 else "receiver\nstart\ncount\n" if case == 22 else "",
                 "" if case in (0, 23) else "FREAK: V4 word panic: " +
                 ("character index out of bounds" if case in (*range(1, 6), 20)
                  else "slice range out of bounds" if case in (*range(6, 12), 21)
                  else "substring range out of bounds") + "\n") for case in range(24))


def call_counts(case: int) -> tuple[int, int, int]:
    if case == 0: return (2, 5, 4)
    if case == 23: return (1, 1, 2)
    if case in (*range(1, 6), 20): return (1, 0, 0)
    if case in (*range(6, 12), 21): return (0, 1, 0)
    if case in (*range(12, 20), 22): return (0, 0, 1)
    raise GateError("unknown bounds case")


def exit_code(case: int, platform: str = sys.platform) -> int:
    return (3 if platform == "win32" else -signal.SIGABRT) if OUTPUTS[case][1] else 0


BEGIN = "@@LLVM-MODULE-BEGIN\n"
END = "@@LLVM-MODULE-END\n"
GUARD_ERROR = "word-bounds guard detected dead or changed receiver\n"
# The production word source and registry are included unchanged. Only the
# three exported helpers and abort are renamed to probe the immutable loan.
GUARD_SOURCE = r'''#include "freak_runtime.c"
#include "freak_v4_word_runtime.h"
static int64_t bounds_owner;
static size_t bounds_length, bounds_owners;
static _Noreturn void bounds_guard_fail(void) {
    fputs("word-bounds guard detected dead or changed receiver\n", stderr);
    fflush(stderr);
    exit(91);
}
static void bounds_live(size_t new_owners) {
    size_t length = SIZE_MAX;
    if (!bounds_owner || !freak_llvm_word_owned_size(bounds_owner, &length) ||
        length != bounds_length || freak_llvm_owned_count != bounds_owners + new_owners)
        bounds_guard_fail();
}
static void bounds_begin(int64_t value) {
    bounds_owner = value;
    if (!freak_llvm_word_owned_size(value, &bounds_length)) bounds_guard_fail();
    bounds_owners = freak_llvm_owned_count;
    bounds_live(0);
}
static _Noreturn void bounds_abort(void) {
    bounds_live(0);
    abort();
}
#define freak_v4_word_char_at bounds_real_char_at
#define freak_v4_word_slice bounds_real_slice
#define freak_v4_word_substring bounds_real_substring
#define abort bounds_abort
#include "freak_v4_word_runtime.c"
#undef abort
#undef freak_v4_word_char_at
#undef freak_v4_word_slice
#undef freak_v4_word_substring
int64_t freak_v4_word_char_at(int64_t value, int64_t index) {
    bounds_begin(value);
    int64_t result = bounds_real_char_at(value, index);
    bounds_live(1);
    bounds_owner = 0;
    return result;
}
int64_t freak_v4_word_slice(int64_t value, int64_t start, int64_t end) {
    bounds_begin(value);
    int64_t result = bounds_real_slice(value, start, end);
    bounds_live(1);
    bounds_owner = 0;
    return result;
}
int64_t freak_v4_word_substring(int64_t value, int64_t start, int64_t count) {
    bounds_begin(value);
    int64_t result = bounds_real_substring(value, start, count);
    bounds_live(1);
    bounds_owner = 0;
    return result;
}
void word_bounds_guard_control(void) {
    int64_t value = freak_v4_word_from_int(7);
    bounds_begin(value);
    freak_v4_word_drop(value);
    bounds_live(0);
}
'''
ABORT_SETUP_SOURCE = r'''#include <stdlib.h>
#ifdef _WIN32
/* Test-only startup suppresses Windows CRT abort UI without changing status. */
__attribute__((constructor)) static void bounds_abort_setup(void) {
    _set_abort_behavior(0, _WRITE_ABORT_MSG | _CALL_REPORTFAULT);
}
#endif
'''


def prefix(case: int) -> str:
    if case not in range(len(OUTPUTS)):
        raise GateError("unknown bounds compiler case")
    return (f"word-bounds-proof case={case} borrowed=true "
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
                and node.args[0].value in (123, 125)):
            return chr(node.args[0].value)
        raise GateError("bounds source table permits only literals, + and closed brace/Unicode chr")

    match = re.search(r"(?ms)^task v4_word_bounds_source\(case_id: int\) -> word \{\n(.*?)^\}", text)
    if match is None:
        raise GateError("missing bounds compiler source table")
    rows = {}
    for line in match[1].splitlines():
        row = re.fullmatch(r"\s*if case_id == (\d+) \{ give back (.*) \}\s*", line)
        if row:
            index = int(row[1])
            if index in rows:
                raise GateError("duplicate bounds source case")
            try:
                rows[index] = read(ast.parse(row[2], mode="eval").body)
            except (SyntaxError, RecursionError) as exc:
                raise GateError("invalid bounds source expression") from exc
        elif line.strip() not in ('panic("unknown word-bounds-proof case")', 'give back ""', ""):
            raise GateError("unexpected bounds source table row")
    if set(rows) != set(range(len(OUTPUTS))):
        raise GateError("missing or unknown bounds source case")
    return [rows[index] for index in range(len(OUTPUTS))]


def extract_module(result, case: int, *, platform: str = sys.platform) -> str:
    stdout = normalized(result.stdout, platform)
    if result.returncode != 0 or result.stderr:
        raise GateError("bounds compiler did not exit cleanly")
    if (not stdout.startswith(prefix(case) + BEGIN) or not stdout.endswith(END)
            or stdout.count(BEGIN) != 1 or stdout.count(END) != 1):
        raise GateError("bounds compiler protocol mismatch")
    module = stdout[len(prefix(case) + BEGIN):-len(END)]
    if not module.strip() or not re.search(r"(?m)^define i32 @main\(", module):
        raise GateError("bounds module lacks a real native entry")
    # Anchored instructions cannot be supplied by comments, declarations or data.
    for kind, expected in zip(("char_at", "slice", "substring"), call_counts(case)):
        calls = re.findall(r"(?m)^\s*%[^=\n]+ = call i64 @freak_v4_word_" + kind
                           + r"\(i64 [^\n]+\)\s*$", module)
        if len(calls) != expected:
            raise GateError("bounds module has the wrong actual closed call count")

    return module


def exact_program(result, case: int, *, platform: str = sys.platform) -> None:
    stdout, bounds = OUTPUTS[case]
    exact_result(result, exit_code(case, platform), stdout, bounds, f"bounds program {case}", platform)


def validate_report(report: dict, sanitize: bool) -> None:
    if report.get("sanitizers") is not sanitize or report.get("ownership_audits") != ["C", "LLVM"]:
        raise GateError("bounds report omits its mode or required audits")
    if report.get("platform") not in ("linux", "darwin", "win32"):
        raise GateError("bounds report omits a supported native platform")
    compiler = report.get("compiler_contracts", [])
    if ([row.get("case") for row in compiler] != list(range(len(OUTPUTS)))
            or any(row.get("status") != "pass" for row in compiler)):
        raise GateError("bounds report lacks all compiler/restore contracts")
    for opt in OPTS:
        flags = report.get("build_flags", {}).get(str(opt), [])
        validate_build_flags(flags, sanitize)
        if [flag for flag in flags if re.fullmatch(r"-O.*", flag)] != [f"-O{opt}"]:
            raise GateError("bounds report has a missing/conflicting optimization")
        if not sanitize and any(flag.startswith("-fsanitize") for flag in flags):
            raise GateError("plain bounds proof unexpectedly uses sanitizers")
        if any(flag.startswith(("-U", "-fno-sanitize=")) for flag in flags):
            raise GateError("bounds report disables a required capability")
        for macro in ("FREAK_RUNTIME_OWNERSHIP_AUDIT", "FREAK_C_RUNTIME_OWNERSHIP_AUDIT"):
            definitions = [flag for flag in flags if flag.startswith("-D" + macro)]
            if definitions != ["-D" + macro + "=1"]:
                raise GateError("bounds report overrides a required ownership audit")
    wanted = {(case, opt, variant) for case in range(len(OUTPUTS)) for opt in OPTS for variant in VARIANTS}
    programs = report.get("programs", [])
    keys = [(row.get("case"), row.get("optimization"), row.get("variant")) for row in programs]
    if len(keys) != len(wanted) or set(keys) != wanted:
        raise GateError("bounds program matrix is missing or duplicated")
    for row in programs:
        stdout, bounds = OUTPUTS[row["case"]]
        if (row.get("status") != "pass" or row.get("exit") != exit_code(row["case"], report.get("platform", sys.platform))
                or row.get("stdout_sha256") != hashlib.sha256(stdout.encode()).hexdigest()
                or row.get("stderr_sha256") != hashlib.sha256(bounds.encode()).hexdigest()):
            raise GateError("bounds program report has incorrect exact output/status")
    wanted_controls = {f"audit-{kind}-O{opt}" for kind in ("C", "LLVM") for opt in OPTS}
    wanted_controls |= {f"guard-live-O{opt}" for opt in OPTS}
    if sanitize:
        wanted_controls |= {"sanitizer-address", "sanitizer-undefined"}
    controls = report.get("controls", [])
    names = [row.get("name") for row in controls]
    if (len(names) != len(wanted_controls) or set(names) != wanted_controls
            or any(row.get("status") != "pass" for row in controls)):
        raise GateError("bounds report lacks real sanitizer/audit controls")
    inputs = report.get("input_hashes")
    if not isinstance(inputs, dict) or not inputs or report.get("final_input_hashes") != inputs:
        raise GateError("bounds proof source inputs changed while running")
    if report.get("guard_source_sha256") != hashlib.sha256(GUARD_SOURCE.encode()).hexdigest():
        raise GateError("bounds report lacks the included-production live guard")
    if report.get("abort_setup_sha256") != hashlib.sha256(ABORT_SETUP_SOURCE.encode()).hexdigest():
        raise GateError("bounds report lacks the noninteractive Windows abort startup")
    generated = report.get("generated_input_hashes")
    if not isinstance(generated, dict) or not generated or report.get("final_generated_input_hashes") != generated:
        raise GateError("generated bounds sources or modules changed while running")


def run_gate(args, report: dict) -> None:
    build = load_build()
    from freakc.v4_native_runtime import HEADER_NAMES
    checks = build.checks
    directory = args.work.resolve()
    runner = Runner(checks, directory)
    fixture = checks.TESTS_ROOT / "word_bounds_execute_smoke.fk"
    runtime_paths = [checks.RUNTIME_ROOT / name for name in build.SOURCE_NAMES]
    headers = [checks.RUNTIME_ROOT / name for name in HEADER_NAMES]
    if (len({path.name for path in runtime_paths}) != len(runtime_paths)
            or not {"freak_runtime.c", "freak_v4_word_runtime.c"}.issubset({path.name for path in runtime_paths})
            or any(not path.is_file() for path in [*runtime_paths, *headers])):
        raise GateError("closed native runtime inputs are incomplete or duplicated")
    inputs = [fixture, Path(__file__), Path(__file__).with_name("test_v4_word_bounds_codegen.py"),
              Path(checks.__file__), Path(build.__file__), ROOT / "freakc/v4_native_runtime.py",
              ROOT / "tests/v4_checked_numeric_codegen.py", *runtime_paths, *headers,
              *(checks.crate_path(name) for name in checks.CRATE_ORDER)]
    report["input_hashes"] = {str(path.relative_to(ROOT)): sha(path) for path in inputs}
    generated = []
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
            saved = directory / f"case-{case}.fk"
            saved.write_text(source, encoding="utf-8")
            generated.append(saved)
        report["source_sha256"] = [hashlib.sha256(source.encode()).hexdigest() for source in sources]
        compiler_dir = directory / "compiler"
        compiler_dir.mkdir()
        old_root = checks.RUNTIME_BUILD_ROOT
        checks.RUNTIME_BUILD_ROOT = compiler_dir
        try:
            c_source, ui = checks.transpile_fixture(checks.check_flattened_crates(), fixture)
            if ui:
                raise GateError("bounds compiler unexpectedly requires UI")
            try:
                probe, _ = checks.compile_runtime_smoke(
                    args.clang, f"-I{checks.RUNTIME_ROOT}", checks.RUNTIME_ROOT / "freak_runtime.c",
                    checks.read_text(checks.RUNTIME_ROOT / "freak_runtime.c"), fixture, c_source,
                    ("-DFREAK_ARRAY_LIVE_LIMIT=1024",),
                )
            except SystemExit as exc:
                raise GateError(f"bounds bootstrap compilation failed: {exc.code}") from exc
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
            generated.append(llvm)
            report["compiler_contracts"].append({"case": case, "status": "pass", "module_sha256": sha(llvm)})
        audit = directory / "audit_probe.c"
        audit.write_text('#include "freak_runtime.h"\n#include "freak_v4_word_runtime.h"\n'
                         'int main(int argc, char **argv) {\n if (argc != 2) return 9;\n'
                         ' if (argv[1][0] == \'C\') { volatile freak_word w = freak_word_from_int(7); (void)w; }\n'
                         ' else { volatile int64_t w = freak_v4_word_from_int(7); (void)w; }\n return 0;\n}\n', encoding="utf-8")
        guard = directory / "bounds_guard.c"
        guard.write_text(GUARD_SOURCE, encoding="utf-8")
        report["guard_source_sha256"] = sha(guard)
        startup = directory / "abort_setup.c"
        startup.write_text(ABORT_SETUP_SOURCE, encoding="utf-8")
        report["abort_setup_sha256"] = sha(startup)
        guard_control = directory / "guard_control.c"
        guard_control.write_text('void word_bounds_guard_control(void);\n'
                                 'int main(void) { word_bounds_guard_control(); return 99; }\n', encoding="utf-8")
        generated += [audit, guard, startup, guard_control]
        report["generated_input_hashes"] = {str(path.relative_to(directory)): sha(path) for path in generated}
        suffix = ".exe" if sys.platform == "win32" else ".native"
        object_suffix = ".obj" if sys.platform == "win32" else ".o"
        for opt in OPTS:
            flags = ["-w", f"-O{opt}", f"-I{checks.RUNTIME_ROOT}", *AUDIT_FLAGS]
            if not args.plain:
                flags += SANITIZER_FLAGS
            validate_build_flags(flags, not args.plain)
            report["build_flags"][str(opt)] = flags
            objects = {}
            for source in [*runtime_paths, startup, guard]:
                output = directory / f"{source.stem}.O{opt}{object_suffix}"
                require_compile(runner.run([args.clang, *flags, "-c", str(source), "-o", str(output)],
                                          f"compile {source.stem} O{opt}", timeout=120, memory=512), str(source))
                objects[source.name] = str(output)
            direct = [objects[source.name] for source in [*runtime_paths, startup]]
            live = [objects[source.name] for source in runtime_paths
                    if source.name not in ("freak_runtime.c", "freak_v4_word_runtime.c")]
            live += [objects[startup.name], objects[guard.name]]
            audit_binary = directory / f"audit-probe.O{opt}{suffix}"
            require_compile(runner.run([args.clang, *flags, str(audit), *direct, "-o", str(audit_binary),
                                       *checks.runtime_platform_final_link_args()], f"link audit O{opt}", timeout=120, memory=512), "audit probe")
            for kind, status in (("C", 87), ("LLVM", 86)):
                observed = runner.run([str(audit_binary), kind], f"audit {kind} O{opt}", timeout=30, memory=128)
                exact_result(observed, status, "", f"FREAK: {kind} ownership audit found 1 unreleased word allocation(s)\n", kind)
                report["controls"].append({"name": f"audit-{kind}-O{opt}", "status": "pass"})
            guard_binary = directory / f"guard-control.O{opt}{suffix}"
            require_compile(runner.run([args.clang, *flags, str(guard_control), *live, "-o", str(guard_binary),
                                       *checks.runtime_platform_final_link_args()], f"link guard O{opt}", timeout=120, memory=512), "live guard control")
            observed = runner.run([str(guard_binary)], f"guard live O{opt}", timeout=30, memory=128)
            exact_result(observed, 91, "", GUARD_ERROR, "live guard capability")
            report["controls"].append({"name": f"guard-live-O{opt}", "status": "pass"})
            for variant, selected in (("direct", direct), ("live", live)):
                for case, llvm in enumerate(modules):
                    binary = directory / f"case-{case}.{variant}.O{opt}{suffix}"
                    require_compile(runner.run([args.clang, *flags, str(llvm), *selected, "-o", str(binary),
                                               *checks.runtime_platform_final_link_args()], f"link case {case} {variant} O{opt}", timeout=120, memory=512), "bounds program")
                    observed = runner.run([str(binary)], f"execute case {case} {variant} O{opt}", timeout=30, memory=128)
                    exact_program(observed, case)
                    report["programs"].append({"case": case, "optimization": opt, "variant": variant, "status": "pass",
                                               "exit": observed.returncode, "binary_sha256": sha(binary),
                                               "stdout_sha256": hashlib.sha256(normalized(observed.stdout, sys.platform).encode()).hexdigest(),
                                               "stderr_sha256": hashlib.sha256(normalized(observed.stderr, sys.platform).encode()).hexdigest()})
        if not args.plain:
            source = directory / "sanitizer_probe.c"
            source.write_text('#include <stdlib.h>\n#include <limits.h>\nint main(int argc, char **argv) {\n'
                              ' if (argc != 2) return 9;\n if (argv[1][0] == \'a\') { volatile char *p = malloc(1); free((void*)p); return p[0]; }\n'
                              ' volatile int value = INT_MAX; volatile int one = 1; return value + one;\n}\n', encoding="utf-8")
            generated.append(source)
            report["generated_input_hashes"][str(source.relative_to(directory))] = sha(source)
            binary = directory / ("sanitizer-probe" + suffix)
            require_compile(runner.run([args.clang, "-O0", *SANITIZER_FLAGS, str(source), "-o", str(binary)],
                                      "link sanitizer capabilities", timeout=120, memory=512), "sanitizer controls")
            for kind in ("address", "undefined"):
                observed = runner.run([str(binary), kind], f"sanitizer {kind}", timeout=30, memory=128)
                validate_sanitizer_probe(observed, kind)
                report["controls"].append({"name": "sanitizer-" + kind, "status": "pass"})
    finally:
        report["final_input_hashes"] = {str(path.relative_to(ROOT)): sha(path) for path in inputs}
        report["final_generated_input_hashes"] = {str(path.relative_to(directory)): sha(path) for path in generated}
    validate_report(report, not args.plain)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG") or shutil.which("clang"))
    parser.add_argument("--plain", action="store_true")
    parser.add_argument("--work", type=Path, required=True, help="new evidence directory; existing paths fail")
    args = parser.parse_args(argv)
    if not args.clang:
        parser.error("clang is required; bounds proof cannot be skipped")
    if not args.plain and not sys.platform.startswith("linux"):
        parser.error("mandatory sanitizers require Linux; use --plain additionally on other OSes")
    args.work = args.work.resolve()
    args.work.mkdir(parents=True, exist_ok=False)
    report = {"schema": "v4-word-bounds-codegen-v1", "platform": sys.platform, "passed": False, "sanitizers": not args.plain,
              "ownership_audits": ["C", "LLVM"], "compiler_contracts": [], "build_flags": {},
              "controls": [], "programs": []}
    try:
        with sanitizer_environment(not args.plain):
            run_gate(args, report)
        report["passed"] = True
        print("word bounds: 24 compiler/restore cases, 144 native programs, exact bounds and live loans, "
              + ("plain PASS" if args.plain else "ASan+UBSan PASS"), flush=True)
        return 0
    except Exception as exc:
        report["error"] = str(exc)
        print(f"word bounds proof FAILED: {exc}", file=sys.stderr, flush=True)
        return 1
    finally:
        records = {str(path.relative_to(args.work)): {"sha256": sha(path), "bytes": path.stat().st_size}
                   for path in sorted(args.work.rglob("*")) if path.is_file()}
        report["artifacts"] = records
        (args.work / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
