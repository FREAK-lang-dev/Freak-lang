#!/usr/bin/env python3
"""Qualify the opt-in scalar AST-to-LLVM-builder compiler, without publishing it.

Native qualification requires explicit current V3 compiler, LLVM 19.1.7 headers
and library, and Clang paths. --source-controls performs no compiler/native run.
All command channels, sources, outputs and terminal status remain in evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

FRONTEND = tuple(f"src/compiler/v3/{name}.fk" for name in
                 ("globals", "helpers", "lexer", "parser", "checker"))
NEW_SOURCES = tuple(f"src/compiler/v3/llvm_builder/{name}" for name in
                    ("bridge.c", "bridge.h", "emitter.fk", "main.fk"))
SDK_HEADERS = ("llvm-c/Core.h", "llvm-c/Analysis.h", "llvm-c/Target.h",
               "llvm-c/TargetMachine.h", "llvm-c/Error.h",
               "llvm-c/Transforms/PassBuilder.h", "llvm/Config/Targets.def",
               "llvm/Config/AsmPrinters.def", "llvm/Config/llvm-config.h")

# Expected observable behavior is explicit; parity alone cannot qualify three
# implementations which agree on the same wrong answer.
POSITIVE = {
    "scalar_calls": ("""
task trace(n: int) -> int { say n; give back n; }
task sum(a: int, b: int) -> int { give back a + b; }
task emit(n: int) { say n; }
task main() -> int {
    pilot n = 7; n += 5; n -= 2; n *= 3; n /= 2; n %= 11;
    say n;
    { pilot n = 99; say n; }
    say n;
    if n >= 4 { n = 123; } else { n = 456; }
    say n;
    emit(sum(trace(12), trace(5)));
    give back 23;
}
""", b"4\n99\n4\n123\n12\n5\n17\n", 23),
    "signed_branches": ("""
task choose(n: int) -> int {
    if n < 0 { if n == -5 { give back 50; } else { give back 60; } }
    else { give back n * 2; }
}
task main() {
    say choose(-5); say choose(-6); say choose(4);
    if 1 != 2 { say 1; } else { say 0; }
    if 2 <= 2 { say 2; }
    if 3 > 2 { say 3; }
    if not false { say 4; }
    if true { say 5; }
}
""", b"50\n60\n8\n1\n2\n3\n4\n5\n", 0),
    "boundaries": ("""
task main() {
    say -9223372036854775808; say 9223372036854775807;
    say -9223372036854775808 + 1; say 9223372036854775807 - 1;
    say -7 / 3; say -7 % 3; say -(-9);
}
""", b"-9223372036854775808\n9223372036854775807\n-9223372036854775807\n9223372036854775806\n-2\n-1\n9\n", 0),
    "recursive_calls": ("""
task descend(n: int) -> int {
    if n <= 0 { give back 0; } else { give back n + descend(n - 1); }
}
task main() { say descend(6); }
""", b"21\n", 0),
    "void_return": ("""
task selected(n: int) { if n == 0 { give back; } say n; }
task main() { selected(0); selected(9); }
""", b"9\n", 0),
    "empty_main": ("task main() {}\n", b"", 0),
    "negative_status": ("task main() -> int { give back -1; }\n", b"", 255),
    "argument_bound": (
        "task edge(" + ",".join(f"n{i}: int" for i in range(64)) +
        ") -> int { give back n0 + n63; } task main() { say edge(" +
        ",".join(str(i) for i in range(64)) + "); }\n", b"63\n", 0),
}

RUNTIME_FAILURE = {
    "addition_overflow": ("9223372036854775807 + 1", "overflow in addition"),
    "subtraction_overflow": ("-9223372036854775808 - 1", "overflow in subtraction"),
    "multiplication_overflow": ("9223372036854775807 * 2", "overflow in multiplication"),
    "negation_overflow": ("-(-9223372036854775808)", "overflow in negation"),
    "division_zero": ("12 / 0", "division by zero in division"),
    "division_overflow": ("-9223372036854775808 / -1", "overflow in division"),
    "remainder_zero": ("12 % 0", "division by zero in remainder"),
    "remainder_overflow": ("-9223372036854775808 % -1", "overflow in remainder"),
}
UNSUPPORTED = {
    "word": 'task main() { say "not supported"; }\n',
    "num": "task main() { say 1.5; }\n",
    "promoted_num_binding": "task main() { pilot n: num = 1; }\n",
    "parameter_bound": ("task wide(" + ",".join(f"n{i}: int" for i in range(65)) +
                        ") {} task main() {}\n"),
    "loop": "task main() { pilot n = 0; repeat while n < 3 { n += 1; } }\n",
    "short_circuit": "task main() { if true and false { say 1; } }\n",
    "global": "pilot n = 4; task main() { say n; }\n",
    "extern": "extern task native() -> int; task main() { say native(); }\n",
    "list": "task main() { pilot xs = [1, 2]; say xs[0]; }\n",
    "eventually": "task main() { eventually { say 1; } }\n",
    "builtin": "task main() { say time::now_ms(); }\n",
    "word_signature": 'task take(n: word) {} task main() { take("word"); }\n',
    "bool_local": "task main() { pilot n = true; if n { say 1; } }\n",
    "unreachable_word": 'task main() { give back; say "still unsupported"; }\n',
}
FRONTEND_FAILURE = {
    "unbound": ("task main() { say missing; }\n", "type error: unknown binding 'missing' (line 1)", 1),
    "type": ('task main() { pilot n: int = "word"; }\n', "type error: cannot initialize int binding 'n' with word (line 1)", 1),
    "fixed": ("task main() { fixed pilot n = 1; n = 2; }\n", "type error: fixed pilot cannot be modified (line 1)", 1),
    "call_arity": ("task f(n: int) {} task main() { f(); }\n", "type error: call to 'f' expects 1 argument(s), got 0 (line 1)", 1),
    "minimum_magnitude": ("task main() { say 9223372036854775808; }\n", "type error: integer literal is outside the signed 64-bit range (line 1)", 1),
    "syntax": ("task main() { say ; }\n", "error: unexpected ';' — this token cannot start an expression", 19),
    "empty": ("", "type error: program requires a usable task main() entry or executable script statements (line 1)", 1),
}

BRIDGE_CONTROL = r'''
#include "bridge.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define REQUIRE(x) do { if (!(x)) { fprintf(stderr, "bridge control failed:%d\n", __LINE__); return 90; } } while (0)
static int64_t session(void) { return freak_ib_session_new(freak_word_lit("control"), 0); }
static int64_t function(int64_t s, const char *name) {
    int64_t f = freak_ib_function(s, freak_word_lit(name), 0, 1);
    freak_ib_position(s, freak_ib_block(s, f, freak_word_lit("entry")));
    return f;
}
static int error_contains(int64_t s, const char *expected) {
    freak_word error = freak_ib_error(s);
    int found = strstr(error.data, expected) != NULL;
    freak_word_release_owned(&error);
    return found;
}
int main(int argc, char **argv) {
    REQUIRE(argc == 3);
    int64_t s = session(); REQUIRE(s > 0);
    int64_t f = function(s, "__freak_user_main"); REQUIRE(f > 0);
    int64_t v = freak_ib_integer(s, 7); REQUIRE(v > 0);
    const char *mode = argv[1];
    if (!strcmp(mode, "wrong-kind")) {
        REQUIRE(!freak_ib_load(s, f)); REQUIRE(error_contains(s, "wrong-kind"));
    } else if (!strcmp(mode, "cross-session")) {
        int64_t other = session(); REQUIRE(other > 0);
        int64_t foreign = freak_ib_integer(other, 3);
        REQUIRE(!freak_ib_negate(s, foreign)); REQUIRE(error_contains(s, "cross-session"));
        REQUIRE(freak_ib_session_release(other));
    } else if (!strcmp(mode, "cross-function")) {
        int64_t slot = freak_ib_slot(s); REQUIRE(slot > 0);
        function(s, "__freak_user_other");
        REQUIRE(!freak_ib_load(s, slot)); REQUIRE(error_contains(s, "another function"));
    } else if (!strcmp(mode, "wrong-type")) {
        int64_t boolean = freak_ib_boolean(s, 1);
        REQUIRE(!freak_ib_arithmetic(s, 0, boolean, v)); REQUIRE(error_contains(s, "type"));
    } else if (!strcmp(mode, "terminated")) {
        REQUIRE(freak_ib_return(s, v)); REQUIRE(!freak_ib_negate(s, v));
        REQUIRE(error_contains(s, "terminated"));
    } else if (!strcmp(mode, "argument-count")) {
        int64_t callee = freak_ib_function(s, freak_word_lit("__freak_user_callee"), 1, 1);
        REQUIRE(freak_ib_call_begin(s, callee)); REQUIRE(!freak_ib_call_end(s));
        REQUIRE(error_contains(s, "incomplete"));
    } else if (!strcmp(mode, "reserved-name")) {
        REQUIRE(!freak_ib_function(s, freak_word_lit("freak_int_add_checked"), 0, 0));
        REQUIRE(error_contains(s, "prefix"));
    } else if (!strcmp(mode, "verifier")) {
        REQUIRE(!freak_ib_emit_object(s, freak_word_lit(argv[2])));
        REQUIRE(error_contains(s, "terminator"));
    } else if (!strcmp(mode, "existing-output") || !strcmp(mode, "symlink-output")) {
        REQUIRE(freak_ib_return(s, v)); REQUIRE(freak_ib_native_main(s, f));
        REQUIRE(!freak_ib_emit_object(s, freak_word_lit(argv[2])));
        REQUIRE(error_contains(s, "exclusively"));
    } else if (!strcmp(mode, "missing-parent")) {
        REQUIRE(freak_ib_return(s, v)); REQUIRE(freak_ib_native_main(s, f));
        REQUIRE(!freak_ib_emit_object(s, freak_word_lit(argv[2])));
        REQUIRE(error_contains(s, "exclusively"));
    } else if (!strcmp(mode, "session-limit")) {
        int64_t others[7];
        for (unsigned i = 0; i < 7; ++i) { others[i] = session(); REQUIRE(others[i] > 0); }
        REQUIRE(!session()); REQUIRE(error_contains(0, "session limit"));
        for (unsigned i = 0; i < 7; ++i) REQUIRE(freak_ib_session_release(others[i]));
    } else if (!strcmp(mode, "ticket-limit")) {
        while (freak_ib_live_tickets() < 65535) REQUIRE(freak_ib_integer(s, 1) > 0);
        REQUIRE(!freak_ib_integer(s, 1)); REQUIRE(error_contains(s, "ticket limit"));
    } else { REQUIRE(0); }
    /* The getter is an independent C word owner after session disposal. */
    freak_word detached = freak_ib_error(s);
    int64_t old_session = s;
    REQUIRE(freak_ib_session_release(s));
    REQUIRE(!freak_ib_session_release(old_session));
    REQUIRE(!freak_ib_integer(old_session, 1));
    REQUIRE(!freak_ib_session_release(INT64_MAX));
    REQUIRE(detached.data != NULL); freak_word_release_owned(&detached);
    REQUIRE(!freak_ib_live_sessions()); REQUIRE(!freak_ib_live_tickets());
    puts("builder-bridge-control-ok");
    return 0;
}
'''


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_exception(error: BaseException) -> str:
    try:
        return repr(error)[:500]
    except BaseException:
        return "exception representation failed"


def assert_frontend_diagnostic(name: str, source: Path, stdout: bytes, stderr: bytes) -> None:
    """Match the current human diagnostic, not optional in-memory fact codes."""
    source_text, message, column = FRONTEND_FAILURE[name]
    assert not stderr, (name, stderr)
    # Ignore only SGR colour sequences; preserve every message/path/span byte.
    display = re.sub(rb"\x1b\[[0-9;]*m", b"", stdout).decode("utf-8")
    assert message + f"\n --> {source}:1:{column}\n" in display, (name, display)
    original_line = source_text.rstrip("\r\n")
    frame = "1 | " + original_line + "\n  | " + " " * (column - 1) + "^\n"
    assert frame in display, (name, display)
    assert "Experimental LLVM IRBuilder object:" not in display, (name, display)


def sdk_closure(include: Path) -> list[Path]:
    """Pin the selected C API headers and every project include they consume."""
    pending = list(SDK_HEADERS)
    seen: set[str] = set()
    while pending:
        relative = pending.pop()
        if relative in seen:
            continue
        seen.add(relative)
        text = (include / relative).read_text()
        for child in re.findall(r'^\s*#\s*include\s+[<"]((?:llvm-c|llvm)/[^>"]+)[>"]', text, re.M):
            if child not in seen:
                pending.append(child)
    return [include / relative for relative in sorted(seen)]


class SourceControls(unittest.TestCase):
    """Independent ABI/source-authority checks; these do not qualify codegen."""
    def test_freak_extern_matches_c_host_abi(self):
        root = Path(__file__).resolve().parents[1]
        emitter = (root / NEW_SOURCES[2]).read_text()
        header = (root / NEW_SOURCES[1]).read_text()
        externs = re.findall(r"extern task (freak_ib_\w+)\(([^)]*)\) -> (\w+)", emitter)
        prototypes = dict(re.findall(r"(freak_ib_\w+)\(([^;]*)\);", header))
        self.assertEqual(set(prototypes), {name for name, _, _ in externs})
        for name, params, result in externs:
            types = [part.split(":")[1].strip() for part in params.split(",") if part]
            native = prototypes[name].strip()
            native_types = [] if native == "void" else [part.strip().split()[0] for part in native.split(",")]
            self.assertEqual(native_types, ["freak_word" if t == "word" else "int64_t" for t in types], name)
            c_result = re.search(r"(int64_t|freak_word)\s+" + name + r"\(", header).group(1)
            self.assertEqual(c_result, "freak_word" if result == "word" else "int64_t", name)

    def test_frontend_cleanup_covers_its_actual_initialized_handles(self):
        root = Path(__file__).resolve().parents[1]
        globals_text = (root / FRONTEND[0]).read_text()
        frontend = "".join((root / name).read_text() for name in FRONTEND)
        initialized = set(re.findall(r"^pilot (\w+)\s*=\s*0\s*$", globals_text, re.M)) & set(re.findall(r"\b(\w+)\s*=\s*array_new\(\)", frontend))
        cleanup = (root / NEW_SOURCES[3]).read_text().split("task ib_release_frontend()", 1)[1]
        self.assertEqual(initialized, set(re.findall(r"array_release\((\w+)\)", cleanup)))

    def test_builder_constructs_ir_and_keeps_existing_frontend_authority(self):
        root = Path(__file__).resolve().parents[1]
        bridge = (root / NEW_SOURCES[0]).read_text()
        emitter = (root / NEW_SOURCES[2]).read_text()
        for forbidden in ("LLVMParseIR", "LLVMParseBitcode", "llvm_emit_line", "emit_llvm_program", "fs::append"):
            self.assertNotIn(forbidden, bridge + emitter)
        self.assertIn("LLVMBuildCall2", bridge)
        self.assertIn("LLVMBuildLoad2", bridge)
        self.assertIn("LLVMVerifyModule", bridge)
        self.assertIn("LLVMTargetMachineEmitToMemoryBuffer", bridge)
        self.assertEqual(len(FRONTEND), 5)
        self.assertEqual(len(set(POSITIVE) | set(RUNTIME_FAILURE) | set(UNSUPPORTED) | set(FRONTEND_FAILURE)),
                         len(POSITIVE) + len(RUNTIME_FAILURE) + len(UNSUPPORTED) + len(FRONTEND_FAILURE))

    def test_owned_native_launcher_drains_on_every_interruption(self):
        for failure in (KeyboardInterrupt("interrupted"), SystemExit(23),
                        subprocess.TimeoutExpired(["inert"], 180)):
            with self.subTest(kind=type(failure).__name__), tempfile.TemporaryDirectory() as directory:
                evidence = Evidence(Path(directory))
                child = Mock(pid=999999, returncode=None)
                child.poll.return_value = None
                child.wait.side_effect = [failure, -9]
                def launch(*_, **kwargs):
                    kwargs["stdout"].write(b"partial stdout\n")
                    kwargs["stderr"].write(b"partial stderr\n")
                    return child
                with patch.object(subprocess, "Popen", side_effect=launch), \
                        patch.object(os, "killpg", create=True) as group_kill:
                    with self.assertRaises(type(failure)) as caught:
                        evidence.run(["inert"], "interruption", {})
                    self.assertIs(caught.exception, failure)
                    group_kill.assert_called_once_with(child.pid, 9)
                    child.kill.assert_called_once_with()
                    self.assertEqual(child.wait.call_count, 2)
                    self.assertEqual(child.wait.call_args.kwargs, {"timeout": 5})
                self.assertEqual((Path(directory) / "command-0000.stdout").read_bytes(), b"partial stdout\n")
                self.assertEqual((Path(directory) / "command-0000.stderr").read_bytes(), b"partial stderr\n")

    def test_secondary_cleanup_failures_preserve_the_first_exception(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence = Evidence(Path(directory))
            primary = KeyboardInterrupt("original interruption")
            child = Mock(pid=999999, returncode=None)
            child.poll.return_value = None
            child.wait.side_effect = [primary, RuntimeError("reap failed")]
            child.kill.side_effect = SystemExit("kill failed")
            with patch.object(subprocess, "Popen", return_value=child), \
                    patch.object(os, "killpg", create=True, side_effect=PermissionError("denied")):
                with self.assertRaises(KeyboardInterrupt) as caught:
                    evidence.run(["inert"], "secondary cleanup", {})
            self.assertIs(caught.exception, primary)
            self.assertEqual(child.wait.call_count, 2)
            self.assertIn("cleanup_errors", evidence.records[0])

    def test_frontend_oracle_uses_exact_message_and_original_source_span(self):
        source = Path("/retained/original-source.fk")
        for name, (source_text, message, column) in FRONTEND_FAILURE.items():
            with self.subTest(case=name):
                original_line = source_text.rstrip("\r\n")
                display = (message + f"\n --> {source}:1:{column}\n1 | " + original_line +
                           "\n  | " + " " * (column - 1) + "^\n").encode()
                assert_frontend_diagnostic(name, source, display, b"")
                for changed in (display.replace(message.encode(), b"some other failure"),
                                display.replace(str(source).encode(), b"/different-source.fk"),
                                display.replace(f":1:{column}\n".encode(), b":2:1\n"),
                                display.replace(b"^\n", b"\n"),
                                display.replace(("1 | " + original_line).encode(), b"1 | changed source")):
                    with self.assertRaises(AssertionError):
                        assert_frontend_diagnostic(name, source, changed, b"")
                with self.assertRaises(AssertionError):
                    assert_frontend_diagnostic(name, source, display, b"unexpected stderr")


class Evidence:
    def __init__(self, root: Path):
        root.mkdir(parents=True, exist_ok=True)
        self.root = root
        self.records: list[dict] = []
        self.report = {"schema": "freak.llvm-builder-experiment.v1", "outcome": "RUNNING",
                       "commands": self.records, "completed": []}
        self.write()

    def write(self):
        temporary = self.root / "report.json.staged"
        temporary.write_text(json.dumps(self.report, indent=2) + "\n")
        temporary.replace(self.root / "report.json")

    def run(self, argv: list[str], label: str, env: dict, expected: int | None = 0):
        # Native qualification is Linux-only. Regular files retain partial raw
        # channels without inherited-pipe capture or reader-thread cleanup.
        prefix = self.root / f"command-{len(self.records):04d}"
        record = {"case": label, "argv": argv, "cwd": str(self.root),
                  "expected": expected, "timeout_seconds": 180}
        self.records.append(record)
        child = None
        channels = {}
        primary = None
        cleanup_errors = []
        started = time.monotonic()
        try:
            self.write()
            for channel in ("stdout", "stderr"):
                channels[channel] = prefix.with_suffix("." + channel).open("xb")
            child = subprocess.Popen(argv, cwd=self.root, env=env,
                                     stdout=channels["stdout"], stderr=channels["stderr"],
                                     start_new_session=True)
            record.update(pid=child.pid, process_tree="owned native Linux process group")
            self.write()
            child.wait(timeout=180)
        except BaseException as error:
            primary = error
            record["error"] = safe_exception(error)
            record["timed_out"] = isinstance(error, subprocess.TimeoutExpired)
            if child is not None:
                # Target only the fresh launcher's group. Every cleanup step is
                # bounded/protected and cannot replace the triggering exception.
                try:
                    os.killpg(child.pid, 9)
                except ProcessLookupError:
                    pass
                except BaseException as secondary:
                    cleanup_errors.append("group kill: " + safe_exception(secondary))
                try:
                    if child.poll() is None: child.kill()
                except BaseException as secondary:
                    cleanup_errors.append("child kill: " + safe_exception(secondary))
                try:
                    child.wait(timeout=5)
                except BaseException as secondary:
                    cleanup_errors.append("child reap: " + safe_exception(secondary))
            raise
        finally:
            secondary_failure = None
            for channel, stream in channels.items():
                try:
                    stream.close()
                except BaseException as secondary:
                    cleanup_errors.append(channel + " close: " + safe_exception(secondary))
                    if secondary_failure is None: secondary_failure = secondary
            record.update(elapsed_seconds=time.monotonic() - started,
                          returncode=child.returncode if child is not None else None)
            record["raw_files"] = {}
            for channel in ("stdout", "stderr"):
                path = prefix.with_suffix("." + channel)
                try:
                    if path.exists():
                        record["raw_files"][channel] = {"path": str(path), "bytes": path.stat().st_size,
                                                        "sha256": digest(path)}
                except BaseException as secondary:
                    cleanup_errors.append(channel + " retain: " + safe_exception(secondary))
                    if secondary_failure is None: secondary_failure = secondary
            if cleanup_errors: record["cleanup_errors"] = cleanup_errors
            try:
                self.write()
            except BaseException as secondary:
                if secondary_failure is None: secondary_failure = secondary
            if primary is not None:
                for note in cleanup_errors:
                    try: primary.add_note(note[:500])
                    except BaseException: pass
                if secondary_failure is not None:
                    try: primary.add_note("evidence cleanup failed: " + safe_exception(secondary_failure))
                    except BaseException: pass
            elif secondary_failure is not None:
                raise secondary_failure
        stdout = prefix.with_suffix(".stdout").read_bytes()
        stderr = prefix.with_suffix(".stderr").read_bytes()
        if expected is not None:
            assert child.returncode == expected, (label, child.returncode, stdout[-4000:], stderr[-4000:])
        return subprocess.CompletedProcess(argv, child.returncode, stdout, stderr)


def native(args) -> int:
    if sys.platform != "linux":
        raise RuntimeError("this prototype gate currently qualifies native Linux only")
    repo = Path(__file__).resolve().parents[1]
    compiler, clang, library = (path.resolve(strict=True) for path in
                               (args.compiler, args.clang, args.llvm_library))
    include = args.llvm_include.resolve(strict=True)
    root = args.evidence_dir.resolve()
    if root.exists() and any(root.iterdir()):
        raise RuntimeError("evidence directory must be fresh; failed attempts are retained")
    evidence = Evidence(root)
    env = os.environ.copy()
    env.pop("LD_PRELOAD", None)
    env["LD_LIBRARY_PATH"] = str(library.parent) + (":" + env["LD_LIBRARY_PATH"] if env.get("LD_LIBRARY_PATH") else "")
    if args.sanitize:
        env["ASAN_OPTIONS"] = "detect_leaks=1:halt_on_error=1:exitcode=86"
        env["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
    inputs = [repo / path for path in (*FRONTEND, *NEW_SOURCES)]
    inputs.append(Path(__file__).resolve(strict=True))
    runtime = repo / "freakc/runtime"
    inputs += [compiler, clang, library, *sdk_closure(include)]
    inputs += [path for directory in (runtime, repo / "third_party/llhttp")
               for path in sorted(directory.rglob("*")) if path.is_file()]
    pins = {str(path): digest(path) for path in inputs}
    evidence.report["input_sha256"] = pins
    evidence.write()
    try:
        aggregate = root / "experimental-host.fk"
        aggregate.write_bytes(b"\n".join((repo / path).read_bytes() for path in (*FRONTEND, NEW_SOURCES[2], NEW_SOURCES[3])))
        evidence.run([str(compiler), str(aggregate), "--c"], "C-host frontend emission", env)
        host = root / "freakc-irbuilder-experimental"
        common = ["-O2", "-I", str(runtime)]
        evidence.run([str(clang), *common, str(aggregate) + ".c", str(repo / NEW_SOURCES[0]),
                      "-I", str(include), str(runtime / "freak_runtime.c"), str(library),
                      "-Wl,-rpath," + str(library.parent), "-lm", "-o", str(host)], "experimental C-host link", env)
        evidence.run([str(host), "--help"], "experimental explicit identity", env)
        controls = root / "bridge-controls.c"; controls.write_text(BRIDGE_CONTROL)
        control = root / "bridge-controls"
        sanitizer = ["-fsanitize=address,undefined", "-fno-omit-frame-pointer"] if args.sanitize else []
        evidence.run([str(clang), *common, *sanitizer, str(controls), str(repo / NEW_SOURCES[0]),
                      "-I", str(repo / "src/compiler/v3/llvm_builder"), "-I", str(include),
                      str(runtime / "freak_runtime.c"), str(library), "-Wl,-rpath," + str(library.parent),
                      "-lm", "-o", str(control)], "C bridge lifetime/control link", env)
        control_modes = ("wrong-kind", "cross-session", "cross-function", "wrong-type", "terminated",
                         "argument-count", "reserved-name", "verifier", "existing-output", "symlink-output",
                         "missing-parent", "session-limit", "ticket-limit")
        for mode in control_modes:
            output = root / f"control-{mode}.o"
            sentinel = root / "sentinel"; sentinel.write_bytes(b"preserved sentinel\n")
            if mode == "existing-output": output.write_bytes(b"preserved existing output\n")
            if mode == "symlink-output": output.symlink_to(sentinel)
            if mode == "missing-parent": output = root / "missing-parent" / "control.o"
            result = evidence.run([str(control), mode, str(output)], "bridge " + mode, env)
            assert result.stdout == b"builder-bridge-control-ok\n" and not result.stderr, (mode, result)
            assert sentinel.read_bytes() == b"preserved sentinel\n"
            if mode == "existing-output": assert output.read_bytes() == b"preserved existing output\n"
            elif mode == "symlink-output": assert output.is_symlink() and output.read_bytes() == sentinel.read_bytes()
            else: assert not output.exists(), (mode, output)
            evidence.report["completed"].append("bridge:" + mode); evidence.write()
        cases = dict(POSITIVE)
        for name, (expression, failure) in RUNTIME_FAILURE.items():
            cases[name] = ("task main() { say " + expression + "; }\n", b"", 1)
        for opt in (0, 2, 3):
            for name, (source_text, wanted_stdout, wanted_status) in cases.items():
                source = root / f"{name}-O{opt}.fk"; source.write_text(source_text)
                observed = []
                for backend in ("c", "llvm", "builder"):
                    if backend == "builder":
                        evidence.run([str(host), str(source), f"--opt={opt}"], f"{name} O{opt} builder emission", env)
                        emitted = Path(str(source) + ".builder.o")
                    else:
                        evidence.run([str(compiler), str(source), "--" + backend, "--strict-borrow", f"--opt={opt}"], f"{name} O{opt} {backend} emission", env)
                        emitted = Path(str(source) + (".c" if backend == "c" else ".ll"))
                    assert emitted.is_file() and emitted.stat().st_size > 0
                    binary = root / f"{name}-O{opt}-{backend}"
                    units = [str(runtime / "freak_runtime.c")]
                    if backend != "c": units.append(str(runtime / "freak_llvm_runtime.c"))
                    evidence.run([str(clang), f"-O{opt}", "-I", str(runtime), str(emitted), *units,
                                  "-lm", "-o", str(binary)], f"{name} O{opt} {backend} native link", env)
                    result = evidence.run([str(binary)], f"{name} O{opt} {backend} execution", env, expected=wanted_status)
                    assert result.stdout == wanted_stdout, (name, backend, result.stdout)
                    wanted_error = ("FREAK: integer " + RUNTIME_FAILURE[name][1] + "\n").encode() if name in RUNTIME_FAILURE else b""
                    assert result.stderr == wanted_error, (name, backend, result.stderr)
                    observed.append((result.returncode, result.stdout, result.stderr))
                assert observed[0] == observed[1] == observed[2], (name, opt, observed)
                evidence.report["completed"].append(f"parity:{name}:O{opt}"); evidence.write()
        for group, cases in (("unsupported", UNSUPPORTED), ("frontend", FRONTEND_FAILURE)):
            for name, fixture in cases.items():
                source_text = fixture if group == "unsupported" else fixture[0]
                source = root / f"negative-{group}-{name}.fk"; source.write_text(source_text)
                output = Path(str(source) + ".builder.o"); output.write_bytes(b"stale object\n")
                unrelated = Path(str(source) + ".c"); unrelated.write_bytes(b"unrelated C output\n")
                result = evidence.run([str(host), str(source)], f"{group}:{name}", env, expected=None)
                assert result.returncode != 0 and not output.exists(), (group, name, result)
                assert unrelated.read_bytes() == b"unrelated C output\n"
                if group == "unsupported": assert b"experimental IRBuilder backend:" in result.stdout
                else: assert_frontend_diagnostic(name, source, result.stdout, result.stderr)
                evidence.report["completed"].append(group + ":" + name); evidence.write()
        source = root / "bad-option.fk"; source.write_text("task main() {}\n")
        for options in (["--opt=4"], ["--llvm"], ["--opt=0", "--opt=2"]):
            output = Path(str(source) + ".builder.o"); output.write_bytes(b"stale object\n")
            result = evidence.run([str(host), str(source), *options], "bad options " + " ".join(options), env, expected=None)
            assert result.returncode != 0 and not output.exists()
        assert all(digest(Path(path)) == expected for path, expected in pins.items()), "input changed during qualification"
        evidence.report.update(outcome="PASS", platforms=["native-linux"], optimizations=[0, 2, 3],
                               parity_cases=len(POSITIVE) + len(RUNTIME_FAILURE), shim_sanitized=args.sanitize,
                               source_controls="separate pure gate")
        evidence.write()
        print("Experimental LLVM builder: PASS (native Linux O0/O2/O3 scalar parity and negatives)")
        return 0
    except BaseException as error:
        evidence.report.update(outcome="FAIL", error=safe_exception(error))
        try: evidence.write()
        except BaseException as secondary:
            try: error.add_note("failed to retain experiment report: " + safe_exception(secondary))
            except BaseException: pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-controls", action="store_true")
    parser.add_argument("--compiler", type=Path)
    parser.add_argument("--clang", type=Path)
    parser.add_argument("--llvm-include", type=Path)
    parser.add_argument("--llvm-library", type=Path)
    parser.add_argument("--evidence-dir", type=Path)
    parser.add_argument("--sanitize", action="store_true", help="instrument the C shim controls with ASan/UBSan")
    args = parser.parse_args()
    if args.source_controls:
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SourceControls))
        return 0 if result.wasSuccessful() else 1
    if not all((args.compiler, args.clang, args.llvm_include, args.llvm_library, args.evidence_dir)):
        parser.error("native gate requires explicit --compiler, --clang, --llvm-include, --llvm-library and fresh --evidence-dir")
    return native(args)


if __name__ == "__main__":
    raise SystemExit(main())
