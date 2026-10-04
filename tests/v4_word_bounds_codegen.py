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
from contextlib import contextmanager
import hashlib
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import signal
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
def source_module(name, path):
    """Execute exact Python source bytes; never reuse a module or bytecode."""
    if name in sys.modules:
        raise RuntimeError("bounds helper namespace already populated")
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    try:
        source = path.read_bytes()
        exec(compile(source, str(path), "exec"), module.__dict__)
        module.bounds_source_sha256 = hashlib.sha256(source).hexdigest()
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


numeric = source_module(__name__ + "_numeric", ROOT / "tests/v4_checked_numeric_codegen.py")
AUDIT_FLAGS, SANITIZER_FLAGS, GateError = numeric.AUDIT_FLAGS, numeric.SANITIZER_FLAGS, numeric.GateError
exact_result, normalized, require_compile = numeric.exact_result, numeric.normalized, numeric.require_compile
sha, validate_build_flags, validate_sanitizer_probe = numeric.sha, numeric.validate_build_flags, numeric.validate_sanitizer_probe
OUTPUT_MIB = 8  # Preserve the original central guard's per-stream cap.


def descriptor(error):
    # Failure attribution must never invoke an exception's hostile __str__.
    try:
        name = type(error).__name__
        return {"type": name[:128] if type(name) is str else "BaseException"}
    except BaseException:
        return {"type": "BaseException"}


class Evidence:
    def __init__(self):
        self.first, self.failures = None, []

    def attempt(self, stage, action):
        try:
            return action()
        except BaseException as error:
            if self.first is None:
                self.first = error
            try:
                if len(self.failures) < 8:
                    self.failures.append({"stage": stage, **descriptor(error)})
            except BaseException:
                pass

    def attach(self, primary):
        try:
            previous = object.__getattribute__(primary, "__dict__").get("bounds_secondary_failures", ())
            safe = [row for row in previous[:8] if type(row) is dict and set(row) == {"stage", "type"}
                    and all(type(value) is str and len(value) <= 128 for value in row.values())] if type(previous) is tuple else []
            primary.bounds_secondary_failures = tuple((safe + self.failures)[:8])
        except BaseException:
            pass

    def raise_first(self):
        if self.first is not None:
            self.attach(self.first)
            raise self.first


@contextmanager
def sanitizer_environment(sanitize):
    names = ("ASAN_OPTIONS", "LSAN_OPTIONS", "UBSAN_OPTIONS")
    previous = {name: os.environ.get(name) for name in names}
    cleanup = Evidence()
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
            os.environ["ASAN_OPTIONS"] = "halt_on_error=1:detect_leaks=1:exitcode=88"
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


def literal_assignment(path, name):
    tree = ast.parse(path.read_bytes())
    rows = [node.value for node in tree.body if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)]
    if len(rows) != 1:
        raise GateError("missing closed source inventory")
    return tuple(ast.literal_eval(rows[0]))


def source_names():
    inventory = ROOT / "freakc/v4_native_runtime.py"
    crates = literal_assignment(ROOT / "src/compiler/v4/check_v4.py", "CRATE_ORDER")
    names = ["tests/v4_word_bounds_codegen.py", "tests/test_v4_word_bounds_codegen.py",
             "tests/v4_checked_numeric_codegen.py", "src/compiler/v4/tests/word_bounds_execute_smoke.fk",
             "src/compiler/v4/check_v4.py", "src/compiler/v4/build_v4.py",
             *("src/compiler/v4/crates/" + name + "/src/lib.fk" for name in crates),
             *("freakc/runtime/" + name for kind in ("SOURCE_NAMES", "HEADER_NAMES")
               for name in literal_assignment(inventory, kind)),
             *(path.relative_to(ROOT).as_posix() for path in sorted((ROOT / "freakc").rglob("*.py")))]
    if len(names) != len(set(names)) or len(names) > 256:
        raise GateError("bounds source closure is duplicated or unbounded")
    if any(not (ROOT / name).is_file() or (ROOT / name).is_symlink() for name in names):
        raise GateError("bounds source closure is missing or aliased")
    return tuple(names)


class FrozenProject(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def __init__(self, frozen):
        self.frozen = frozen
        self.paths = {}

    def find_spec(self, fullname, path=None, target=None):
        if fullname not in ("check_v4", "build_v4", "freakc") and not fullname.startswith("freakc."):
            return None
        relative = "src/compiler/v4/" + fullname + ".py" if fullname in ("check_v4", "build_v4") else fullname.replace(".", "/")
        source = self.frozen / relative
        package = source.is_dir()
        source = source / "__init__.py" if package else source.with_suffix(".py")
        if not source.is_file():
            raise GateError("unfrozen bootstrap module requested")
        self.paths[fullname] = source
        return importlib.util.spec_from_loader(fullname, self, origin=str(source), is_package=package)

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        path = self.paths[module.__name__]
        module.__file__ = str(path)
        exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)


def load_build(frozen):
    if any(name in ("check_v4", "build_v4", "freakc") or name.startswith("freakc.") for name in sys.modules):
        raise GateError("bootstrap import namespace already populated")
    finder = FrozenProject(frozen)
    sys.meta_path.insert(0, finder)
    try:
        build = __import__("build_v4")
    except BaseException:
        sys.meta_path.remove(finder)
        raise
    build.bounds_finder = finder
    return build


class Conservation:
    def __init__(self, args, report):
        self.directory, self.report = args.work, report
        self.frozen = self.directory / "frozen-source"
        self.expected = {name: sha(ROOT / name) for name in source_names()}
        if numeric.bounds_source_sha256 != self.expected["tests/v4_checked_numeric_codegen.py"]:
            raise GateError("loaded numeric oracle differs from frozen source closure")
        report["input_hashes"] = dict(self.expected)
        self.frozen.mkdir()
        for name, digest in self.expected.items():
            path = self.frozen / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / name).read_bytes())
            if sha(path) != digest:
                raise GateError("source changed while freezing bounds inputs")
        self.selected = Path(shutil.which(args.clang) or args.clang).absolute()
        self.clang = self.selected.resolve(strict=True)
        self.tool_hash = sha(self.clang)
        report["clang"] = {"selected": str(self.selected), "resolved": str(self.clang), "sha256": self.tool_hash}
        self.generated, self.images, self.bindings, self.modules, self.guards = {}, {}, [], {}, []
        self.finder = None
        self.bind(numeric, ("exact_result", "normalized", "require_compile", "sha", "validate_build_flags", "validate_sanitizer_probe"))
        self.bind(sys.modules[__name__], ("numeric", "source_module", "source_names", "load_build", "sha", "exact_result", "validate_report",
                                        "exact_program", "extract_module", "fixture_sources", "prefix", "call_counts", "exit_code",
                                        "OPTS", "VARIANTS", "NAMES", "OUTPUTS", "GUARD_SOURCE", "ABORT_SETUP_SOURCE", "OUTPUT_MIB"))
        self.bind(Runner, ("run",))
        self.bind(Conservation, ("check", "track", "final_pins"))
        self.check()

    def bind(self, owner, names):
        for name in names:
            value = getattr(owner, name)
            self.bindings.append((owner, name, value, getattr(value, "__code__", None)))

    def seal_build(self, build):
        self.finder = build.bounds_finder
        self.bind(self.finder, ("find_spec", "exec_module"))
        self.bind(build, ("host_target",))
        self.bind(build.checks, ("compile_runtime_smoke", "transpile_fixture", "check_flattened_crates", "transpile",
                               "Parser", "Lexer", "TypeChecker", "runtime_platform_final_link_args"))
        for name, module in tuple(sys.modules.items()):
            if name in ("check_v4", "build_v4", "freakc") or name.startswith("freakc."):
                path = Path(module.__file__)
                if not path.resolve().is_relative_to(self.frozen.resolve()):
                    raise GateError("foreign bootstrap source loaded")
                self.modules[name] = module
                for attribute, value in tuple(vars(module).items()):
                    if isinstance(value, types.FunctionType) and attribute != "run_with_heartbeat":
                        self.bind(module, (attribute,))
                    elif isinstance(value, type) and getattr(value, "__module__", None) == name:
                        self.bind(value, tuple(key for key, member in vars(value).items()
                                              if isinstance(member, (types.FunctionType, classmethod, staticmethod))))
        self.check()

    def check(self):
        python_names = tuple(path.relative_to(ROOT).as_posix() for path in sorted((ROOT / "freakc").rglob("*.py")))
        if python_names != tuple(name for name in self.expected if name.startswith("freakc/") and name.endswith(".py")):
            raise GateError("bootstrap Python source inventory changed")
        if any(sha(ROOT / name) != digest for name, digest in self.expected.items()):
            raise GateError("original bounds source conservation failed")
        if any(sha(self.frozen / name) != digest for name, digest in self.expected.items()):
            raise GateError("frozen bounds source conservation failed")
        if (self.selected.resolve(strict=True) != self.clang or sha(self.selected) != self.tool_hash or sha(self.clang) != self.tool_hash):
            raise GateError("selected/resolved Clang conservation failed")
        if any(path.name == "__pycache__" or path.suffix in (".pyc", ".pyo") for path in self.frozen.rglob("*")):
            raise GateError("frozen bootstrap bytecode is forbidden")
        if self.finder is not None and not any(value is self.finder for value in sys.meta_path):
            raise GateError("frozen project loader changed")
        if any(sys.modules.get(name) is not module for name, module in self.modules.items()):
            raise GateError("loaded bootstrap module changed")
        if self.finder is not None and any(Path(module.__file__) != self.finder.paths[name]
                                          or module.__loader__ is not self.finder for name, module in self.modules.items()):
            raise GateError("loaded bootstrap source/loader attribution changed")
        if any(checks.run_with_heartbeat is not expected or getattr(expected, "__code__", None) is not code
               for checks, expected, code in self.guards):
            raise GateError("original process guard binding changed")
        for owner, name, value, code in self.bindings:
            current = getattr(owner, name)
            if current != value or getattr(current, "__code__", None) is not code:
                raise GateError("consumed helper binding changed")
        if any(sha(path) != digest for pins in (self.generated, self.images) for path, digest in pins.items()):
            raise GateError("produced bounds source/module/image conservation failed")

    def track(self, path, *, image=False):
        self.check()
        pins = self.images if image else self.generated
        if path in self.generated or path in self.images:
            raise GateError("duplicate produced artifact identity")
        pins[path] = sha(path)
        self.check()

    def final_pins(self):
        self.check()
        report = self.report
        report["final_input_hashes"] = {name: sha(ROOT / name) for name in self.expected}
        report["frozen_input_hashes"] = {name: sha(self.frozen / name) for name in self.expected}
        report["final_clang"] = {"selected": str(self.selected), "resolved": str(self.selected.resolve(strict=True)), "sha256": sha(self.clang)}
        for key, pins in (("generated_input_hashes", self.generated), ("image_hashes", self.images)):
            report[key] = {path.relative_to(self.directory).as_posix(): digest for path, digest in pins.items()}
            report["final_" + key] = {path.relative_to(self.directory).as_posix(): sha(path) for path in pins}
        self.check()


class Runner:
    """Scoped adapter retaining the original guard's exact bounded dispatch."""
    def __init__(self, checks, directory, conservation=None):
        self.checks, self.directory, self.conservation, self.serial = checks, directory, conservation, 0
        self.guard = checks.run_with_heartbeat
        if conservation is not None:
            conservation.bind(self, ("guard",))
            conservation.guards.append((checks, self.guard, getattr(self.guard, "__code__", None)))

    def run(self, argv, label, *, timeout=60, memory=64):
        self.serial += 1
        stem = self.directory / f"{self.serial:03d}-{re.sub(r'[^a-zA-Z0-9_-]', '-', label)}"
        record = {"argv": argv, "timeout_seconds": timeout, "memory_limit_mib": memory,
                  "output_limit_mib_per_stream": OUTPUT_MIB, "status": "started"}
        command_path = stem.with_suffix(".command.json")
        command_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        retention = Evidence()
        def conserve():
            if self.conservation is not None:
                self.conservation.check()
        def channel(value, name, attribute):
            data = getattr(value, attribute, None)
            if data is None and attribute == "output":
                data = getattr(value, "stdout", None)
            if data is not None:
                if type(data) is str:
                    data = data.encode("utf-8")
                if type(data) is not bytes:
                    raise GateError("unexpected raw channel payload")
                stem.with_suffix("." + name).write_bytes(data[:OUTPUT_MIB * 1048576])
        def metadata():
            stem.with_suffix(".retention.json").write_text(json.dumps({"secondary_failures": retention.failures}) + "\n", encoding="utf-8")
        try:
            conserve()
            result = self.guard(argv, label=label, timeout_seconds=timeout, memory_limit_mb=memory, output_limit_mb=OUTPUT_MIB)
        except BaseException as primary:
            try:
                retention.attempt("post-job-conservation", conserve)
                retention.attempt("failure-attribution", lambda: record.update(status="raised", error_type=descriptor(primary)["type"]))
                retention.attempt("command-attribution", lambda: command_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8"))
                retention.attempt("failure-descriptor", lambda: stem.with_suffix(".failure.txt").write_text(json.dumps(descriptor(primary)) + "\n", encoding="utf-8"))
                retention.attempt("partial-stdout", lambda: channel(primary, "stdout", "output"))
                retention.attempt("partial-stderr", lambda: channel(primary, "stderr", "stderr"))
                retention.attempt("retention-metadata", metadata)
                retention.attach(primary)
            except BaseException:
                pass
            raise
        retention.attempt("post-job-conservation", conserve)
        retention.attempt("result-attribution", lambda: record.update(status="finished", returncode=result.returncode))
        retention.attempt("command-attribution", lambda: command_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8"))
        for name in ("stdout", "stderr"):
            retention.attempt("result-" + name, lambda name=name: channel(result, name, name))
        retention.attempt("result-publication", lambda: stem.with_suffix(".result.json").write_text(
            json.dumps({"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}, indent=2) + "\n", encoding="utf-8"))
        retention.attempt("retention-metadata", metadata)
        retention.raise_first()
        return result


@contextmanager
def bootstrap_dispatch(checks, runner):
    original = checks.run_with_heartbeat
    calls = []
    def bounded(argv, *, label, memory_limit_mb=None, **kwargs):
        if memory_limit_mb != 1024 or kwargs:
            raise GateError("original bootstrap dispatch contract changed")
        calls.append(tuple(argv))
        if runner.conservation is not None:
            generated = [Path(value) for value in argv if value.endswith(".fk.c")]
            if len(generated) != 1:
                raise GateError("original bootstrap C input changed")
            runner.conservation.track(generated[0])
        return runner.run(argv, label, timeout=120, memory=1024)
    checks.run_with_heartbeat = bounded
    pins = runner.conservation
    if pins is not None:
        pins.guards[:] = [(owner, bounded, bounded.__code__) if owner is checks else (owner, expected, code)
                         for owner, expected, code in pins.guards]
    try:
        yield calls
    finally:
        checks.run_with_heartbeat = original
        if pins is not None:
            pins.guards[:] = [(owner, original, getattr(original, "__code__", None)) if owner is checks else (owner, expected, code)
                             for owner, expected, code in pins.guards]

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
    if report.get("frozen_input_hashes") != inputs:
        raise GateError("bounds proof frozen source closure changed")
    clang = report.get("clang")
    if (not isinstance(clang, dict) or set(clang) != {"selected", "resolved", "sha256"}
            or report.get("final_clang") != clang or not re.fullmatch(r"[0-9a-f]{64}", clang.get("sha256", ""))):
        raise GateError("bounds proof selected/resolved Clang is not conserved")
    if report.get("guard_source_sha256") != hashlib.sha256(GUARD_SOURCE.encode()).hexdigest():
        raise GateError("bounds report lacks the included-production live guard")
    if report.get("abort_setup_sha256") != hashlib.sha256(ABORT_SETUP_SOURCE.encode()).hexdigest():
        raise GateError("bounds report lacks the noninteractive Windows abort startup")
    generated = report.get("generated_input_hashes")
    if not isinstance(generated, dict) or not generated or report.get("final_generated_input_hashes") != generated:
        raise GateError("generated bounds sources or modules changed while running")
    images = report.get("image_hashes")
    if (not isinstance(images, dict) or not images or report.get("final_image_hashes") != images
            or any(re.fullmatch(r"[0-9a-f]{64}", digest) is None for digest in images.values())):
        raise GateError("produced bounds images changed or are absent")
    suffix = ".exe" if report["platform"] == "win32" else ".native"
    object_suffix = ".obj" if report["platform"] == "win32" else ".o"
    expected_images = {f"case-{case}.{variant}.O{opt}{suffix}" for case, opt, variant in wanted}
    expected_images |= {f"{kind}.O{opt}{suffix}" for kind in ("audit-probe", "guard-control") for opt in OPTS}
    runtime_sources = literal_assignment(ROOT / "freakc/v4_native_runtime.py", "SOURCE_NAMES")
    expected_images |= {f"{Path(source).stem}.O{opt}{object_suffix}"
                        for source in (*runtime_sources, "abort_setup.c", "bounds_guard.c") for opt in OPTS}
    expected_images.add("compiler/word_bounds_execute_smoke" + (".exe" if report["platform"] == "win32" else ""))
    if sanitize:
        expected_images.add("sanitizer-probe" + suffix)
    if set(images) != expected_images:
        raise GateError("bounds report lacks the exact bootstrap/object/control/native image closure")
    probe = report.get("compiler", {})
    if (images.get(probe.get("path")) != probe.get("sha256") or probe.get("memory_limit_mib") != 64
            or probe.get("live_handle_limit") != 1024):
        raise GateError("bootstrap compiler is not conserved with its dispatch limits")
    for row in compiler:
        if generated.get(row.get("module_path")) != row.get("module_sha256"):
            raise GateError("compiler row differs from conserved generated module")
    for row in programs:
        if images.get(row.get("binary_path")) != row.get("binary_sha256"):
            raise GateError("native row differs from conserved produced image")
    artifacts = report.get("artifacts")
    if artifacts is not None and any(artifacts.get(name, {}).get("sha256") != digest for name, digest in {**generated, **images}.items()):
        raise GateError("final artifact inventory differs from conserved source/module/image")


def run_gate(args, report: dict) -> Conservation:
    pins = Conservation(args, report)
    build = load_build(pins.frozen)
    pins.seal_build(build)
    HEADER_NAMES = literal_assignment(pins.frozen / "freakc/v4_native_runtime.py", "HEADER_NAMES")
    checks = build.checks
    directory = args.work.resolve()
    args.clang = str(pins.clang)
    runner = Runner(checks, directory, pins)
    fixture = checks.TESTS_ROOT / "word_bounds_execute_smoke.fk"
    runtime_paths = [checks.RUNTIME_ROOT / name for name in build.SOURCE_NAMES]
    headers = [checks.RUNTIME_ROOT / name for name in HEADER_NAMES]
    if (len({path.name for path in runtime_paths}) != len(runtime_paths)
            or not {"freak_runtime.c", "freak_v4_word_runtime.c"}.issubset({path.name for path in runtime_paths})
            or any(not path.is_file() for path in [*runtime_paths, *headers])):
        raise GateError("closed native runtime inputs are incomplete or duplicated")
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
            pins.track(saved)
        report["source_sha256"] = [hashlib.sha256(source.encode()).hexdigest() for source in sources]
        compiler_dir = directory / "compiler"
        compiler_dir.mkdir()
        old_root = checks.RUNTIME_BUILD_ROOT
        checks.RUNTIME_BUILD_ROOT = compiler_dir
        try:
            pins.check()
            c_source, ui = checks.transpile_fixture(checks.check_flattened_crates(), fixture)
            pins.check()
            if ui:
                raise GateError("bounds compiler unexpectedly requires UI")
            try:
                with bootstrap_dispatch(checks, runner) as dispatches:
                    probe, compiled = checks.compile_runtime_smoke(
                        args.clang, f"-I{checks.RUNTIME_ROOT}", checks.RUNTIME_ROOT / "freak_runtime.c",
                        checks.read_text(checks.RUNTIME_ROOT / "freak_runtime.c"), fixture, c_source,
                        ("-DFREAK_ARRAY_LIVE_LIMIT=1024",),
                    )
                if compiled is not True or len(dispatches) != 1:
                    raise GateError("fresh original bootstrap must dispatch exactly once")
                for path in sorted(compiler_dir.iterdir()):
                    if path != probe and path not in pins.generated:
                        generated.append(path)
                        pins.track(path)
                pins.track(probe, image=True)
            except SystemExit as exc:
                raise GateError(f"bounds bootstrap compilation failed: {exc.code}") from exc
        finally:
            checks.RUNTIME_BUILD_ROOT = old_root
        report["compiler"] = {"path": probe.relative_to(directory).as_posix(), "sha256": sha(probe), "memory_limit_mib": 64, "live_handle_limit": 1024}
        modules = []
        for case in range(len(OUTPUTS)):
            emitted = runner.run([str(probe), str(case), target, "--emit"], f"emit case {case}")
            module = extract_module(emitted, case)
            llvm = directory / f"case-{case}.ll"
            llvm.write_text(module, encoding="utf-8")
            modules.append(llvm)
            generated.append(llvm)
            pins.track(llvm)
            report["compiler_contracts"].append({"case": case, "status": "pass", "module_path": llvm.relative_to(directory).as_posix(), "module_sha256": sha(llvm)})
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
        for path in (audit, guard, startup, guard_control):
            pins.track(path)
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
                pins.track(output, image=True)
                objects[source.name] = str(output)
            direct = [objects[source.name] for source in [*runtime_paths, startup]]
            live = [objects[source.name] for source in runtime_paths
                    if source.name not in ("freak_runtime.c", "freak_v4_word_runtime.c")]
            live += [objects[startup.name], objects[guard.name]]
            audit_binary = directory / f"audit-probe.O{opt}{suffix}"
            require_compile(runner.run([args.clang, *flags, str(audit), *direct, "-o", str(audit_binary),
                                       *checks.runtime_platform_final_link_args()], f"link audit O{opt}", timeout=120, memory=512), "audit probe")
            pins.track(audit_binary, image=True)
            for kind, status in (("C", 87), ("LLVM", 86)):
                observed = runner.run([str(audit_binary), kind], f"audit {kind} O{opt}", timeout=30, memory=128)
                exact_result(observed, status, "", f"FREAK: {kind} ownership audit found 1 unreleased word allocation(s)\n", kind)
                report["controls"].append({"name": f"audit-{kind}-O{opt}", "status": "pass"})
            guard_binary = directory / f"guard-control.O{opt}{suffix}"
            require_compile(runner.run([args.clang, *flags, str(guard_control), *live, "-o", str(guard_binary),
                                       *checks.runtime_platform_final_link_args()], f"link guard O{opt}", timeout=120, memory=512), "live guard control")
            pins.track(guard_binary, image=True)
            observed = runner.run([str(guard_binary)], f"guard live O{opt}", timeout=30, memory=128)
            exact_result(observed, 91, "", GUARD_ERROR, "live guard capability")
            report["controls"].append({"name": f"guard-live-O{opt}", "status": "pass"})
            for variant, selected in (("direct", direct), ("live", live)):
                for case, llvm in enumerate(modules):
                    binary = directory / f"case-{case}.{variant}.O{opt}{suffix}"
                    require_compile(runner.run([args.clang, *flags, str(llvm), *selected, "-o", str(binary),
                                               *checks.runtime_platform_final_link_args()], f"link case {case} {variant} O{opt}", timeout=120, memory=512), "bounds program")
                    pins.track(binary, image=True)
                    observed = runner.run([str(binary)], f"execute case {case} {variant} O{opt}", timeout=30, memory=128)
                    exact_program(observed, case)
                    report["programs"].append({"case": case, "optimization": opt, "variant": variant, "status": "pass",
                                               "exit": observed.returncode, "binary_path": binary.relative_to(directory).as_posix(), "binary_sha256": sha(binary),
                                               "stdout_sha256": hashlib.sha256(normalized(observed.stdout, sys.platform).encode()).hexdigest(),
                                               "stderr_sha256": hashlib.sha256(normalized(observed.stderr, sys.platform).encode()).hexdigest()})
        if not args.plain:
            source = directory / "sanitizer_probe.c"
            source.write_text('#include <stdlib.h>\n#include <limits.h>\nint main(int argc, char **argv) {\n'
                              ' if (argc != 2) return 9;\n if (argv[1][0] == \'a\') { volatile char *p = malloc(1); free((void*)p); return p[0]; }\n'
                              ' volatile int value = INT_MAX; volatile int one = 1; return value + one;\n}\n', encoding="utf-8")
            generated.append(source)
            pins.track(source)
            report["generated_input_hashes"][str(source.relative_to(directory))] = sha(source)
            binary = directory / ("sanitizer-probe" + suffix)
            require_compile(runner.run([args.clang, "-O0", *SANITIZER_FLAGS, str(source), "-o", str(binary)],
                                      "link sanitizer capabilities", timeout=120, memory=512), "sanitizer controls")
            pins.track(binary, image=True)
            for kind in ("address", "undefined"):
                observed = runner.run([str(binary), kind], f"sanitizer {kind}", timeout=30, memory=128)
                validate_sanitizer_probe(observed, kind)
                report["controls"].append({"name": "sanitizer-" + kind, "status": "pass"})
    except BaseException as primary:
        try:
            retention = Evidence()
            retention.attempt("final-pins", pins.final_pins)
            retention.attach(primary)
        except BaseException:
            pass
        raise
    pins.final_pins()
    validate_report(report, not args.plain)
    return pins


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
    report_path = args.work / "results.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    pins = None
    try:
        with sanitizer_environment(not args.plain):
            pins = run_gate(args, report)
        pins.final_pins()
        report["artifacts"] = {path.relative_to(args.work).as_posix(): {"sha256": sha(path), "bytes": path.stat().st_size}
                               for path in sorted(args.work.rglob("*")) if path.is_file() and path != report_path}
        validate_report(report, not args.plain)
        candidate = dict(report, passed=True)
        pending = args.work / "results.pending.json"
        pending.write_text(json.dumps(candidate, indent=2) + "\n", encoding="utf-8")
        pins.check()
        os.replace(pending, report_path)
        pins.check()
        print("word bounds: 24 compiler/restore cases, 144 native programs, exact bounds and live loans, "
              + ("plain PASS" if args.plain else "ASan+UBSan PASS"), flush=True)
        return 0
    except BaseException as primary:
        try:
            retention = Evidence()
            retention.attempt("failure-attribution", lambda: report.update(passed=False, error=descriptor(primary)))
            if pins is not None:
                retention.attempt("final-pins", pins.final_pins)
            def artifacts():
                report["artifacts"] = {path.relative_to(args.work).as_posix(): {"sha256": sha(path), "bytes": path.stat().st_size}
                                       for path in sorted(args.work.rglob("*")) if path.is_file() and path != report_path}
            retention.attempt("failure-artifacts", artifacts)
            retention.attempt("failure-publication", lambda: report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8"))
            retention.attempt("failure-stderr", lambda: print("word bounds proof FAILED: " + descriptor(primary)["type"], file=sys.stderr, flush=True))
            retention.attach(primary)
        except BaseException:
            pass
        raise


if __name__ == "__main__":
    raise SystemExit(main())
