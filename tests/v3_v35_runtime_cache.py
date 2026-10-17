#!/usr/bin/env python3
"""Installed public CLI runtime-object cache controls, with retained raw evidence.

The native gate deliberately requires a qualified installed CLI and selected
Clang. It never builds a replacement CLI or falls back to a repository compiler.
Linux strace records real child execve argv; other platforms record the declared
conservative tool-closure boundary and must receive separate native coverage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import inspect
import shlex
import signal
import subprocess
import sys
import time
import unittest
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "freak-runtime-object-v1"
EVENT = re.compile(r"^FREAK_RUNTIME_CACHE (hit|compile|fallback) (\S+) ([0-9a-f]{64})?$", re.M)
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def task_source(source: str, name: str) -> str:
    """Extract the actual FREAK task, preserving its body for native controls."""
    pattern = re.compile(rf"^task {re.escape(name)}\([^\n]+", re.M)
    match = pattern.search(source)
    if not match:
        raise AssertionError(f"missing task {name}")
    cursor = source.index("{", match.start())
    start = match.start()
    depth = 0
    quoted = False
    comment = False
    escaped = False
    for index in range(cursor, len(source)):
        ch = source[index]
        if comment:
            if ch == "\n":
                comment = False
            continue
        if quoted:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                quoted = False
            continue
        if ch == '"':
            quoted = True
        elif source[index:index + 2] == "--":
            comment = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return source[start:index + 1] + "\n"
    raise AssertionError(f"unterminated task {name}")


def fk_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t") + '"'


def dependency_harness(source: str) -> tuple[str, int]:
    # These are Make/Clang grammar examples, not a Python reimplementation.
    rows = [
        (False, "freak-cache: /a.c /b.h\n", ["/a.c", "/b.h"]),
        (False, "freak-cache: /a\\ b.h /hash\\#name.h\n", ["/a b.h", "/hash#name.h"]),
        (False, "freak-cache: /a.c \\\n /b.h\n", ["/a.c", "/b.h"]),
        (False, "freak-cache: /a.c \\\r\n\t/b.h\r\n", ["/a.c", "/b.h"]),
        (False, "freak-cache: /cash$$name.h /colon\\:name.h\n", ["/cash$name.h", "/colon:name.h"]),
        (True, r"freak-cache: C\:/a.c C:\SDK\header.h" + "\n", ["C:/a.c", r"C:\SDK\header.h"]),
        (True, r"freak-cache: C\:/Program\ Files/h.h" + "\n", ["C:/Program Files/h.h"]),
        (False, "wrong-target: /a.h\n", None),
        (False, "freak-cache:\n", None),
        (False, "freak-cache: /a.h # ignored.h\n", None),
        (False, "freak-cache: /cash$name.h\n", None),
        (False, "freak-cache: /unfinished\\", None),
        (False, "freak-cache: /unknown\\q.h\n", None),
        (False, "freak-cache: " + " /a.h" * 4097 + "\n", None),
    ]
    trace_rows = [
        ('clang version 19\n "/clang" "-cc1" "-emit-obj"\n', True),
        (' "/clang" "-cc1"\n "/as" "object.s"\n', False),
        (' "/other-clang" "-cc1"\n', False),
        (' "/clang" "-cc1"\n "/clang" "-cc1"\n', False),
        (' "/clang" "-cc1as"\n', False),
        ('clang version 19\n', False),
    ]
    chunks = [
        'pilot CLI_RUNTIME_CACHE_META_LIMIT = 1048576\npilot CLI_RUNTIME_CACHE_DEP_LIMIT = 4096\n',
        'pilot mut simulated_windows = false\npilot mut observed = 0\n',
        'task cli_is_windows() -> bool { give back simulated_windows }\n',
        'task cli_runtime_cache_raw_pin(path: word, retain: bool) -> word { array_push(observed, path) give back "pin:" + path }\n',
        'task cli_runtime_cache_canonical(path: word) -> word { give back path }\n',
        task_source((ROOT / "src/cli/build.fk").read_text(), "cli_trace_executable_token"),
        task_source(source, "cli_runtime_cache_trace_cc1"),
        task_source(source, "cli_runtime_cache_dyld_plain"),
        task_source(source, "cli_runtime_cache_run_marker"),
        task_source(source, "cli_runtime_cache_dependencies"),
        'task require(value: bool, label: word) -> void { if not value { say label process::exit(1) } }\n',
        'task main() -> int {\n',
    ]
    for index, (windows, text, expected) in enumerate(rows):
        chunks.extend([
            f"simulated_windows = {'true' if windows else 'false'}\nobserved = array_new()\n",
            f"pilot result{index} = cli_runtime_cache_dependencies({fk_quote(text)}, false)\n",
            f"require((result{index} != \"\") == {'true' if expected is not None else 'false'}, \"dependency admission {index}\")\n",
        ])
        if expected is not None:
            chunks.append(f'require(array_len(observed) == {len(expected)}, "dependency count {index}")\n')
            for item, path in enumerate(expected):
                chunks.append(f'require(array_get(observed, {item}) == {fk_quote(path)}, "dependency path {index}/{item}")\n')
        chunks.append("array_release(observed)\n")
    for index, (trace, admitted) in enumerate(trace_rows):
        chunks.append(f'require(cli_runtime_cache_trace_cc1({fk_quote(trace)}, "/clang") == {str(admitted).lower()}, "execution plan {index}")\n')
    chunks.append('require(cli_runtime_cache_dyld_plain() == (process::env("CACHE_CONTROL_DYLD_REJECT") != "1"), "DYLD refusal")\n')
    chunks.append('pilot known_digest = "' + 'a' * 64 + '"\n')
    chunks.append('require(cli_runtime_cache_run_marker(true, known_digest, "unused") == "proven:" + known_digest, "proven marker")\n')
    for reason in ("unproved-tool-support", "unavailable-tool-context", "unavailable-stage-context", "unavailable-runtime-context"):
        chunks.append(f'require(cli_runtime_cache_run_marker(false, known_digest, {fk_quote(reason)}) == {fk_quote("legacy:" + reason)}, "adverse mode {reason}")\n')
        chunks.append(f'require(cli_runtime_cache_run_marker(false, known_digest, {fk_quote(reason)}) != cli_runtime_cache_run_marker(true, known_digest, "unused"), "mode separation {reason}")\n')
    chunks.append('require(cli_runtime_cache_run_marker(true, "", "empty-proof") == "legacy:empty-proof", "empty proof is not proven")\n')
    chunks.append('say "dependency controls passed"\ngive back 0\n}\n')
    return "".join(chunks), len(rows)


def optional_stage_harness(source: str) -> str:
    # Force only the optional-stage compiler to fail, then execute the actual
    # orchestration body. The platform filesystem/lock/cleanup operations remain
    # real; the external compiler is a stub so no filesystem quota is required.
    chunks = [
        'pilot mut cli_runtime_cache_tool_complete = false\npilot mut cli_runtime_cache_paths = 0\npilot mut cli_runtime_cache_hashes = 0\npilot mut test_root_owner = 0\npilot mut observed_lto = ""\n',
        'task cli_runtime_cache_tool_identity(executable: word) -> word { cli_runtime_cache_tool_complete = true give back "tool" }\n',
        'task cli_runtime_cache_note(event: word, unit: word, key: word) -> void {}\n',
        'task cli_runtime_cache_root() -> int { give back fs::open_dir_ticket(fs::result_word(test_root_owner)) }\n',
        'task cli_runtime_cache_stage() -> int { give back fs::temp_dir("/tmp", "cache-stage-control") }\n',
        task_source(source, "cli_runtime_cache_reset"),
        task_source(source, "cli_runtime_cache_release"),
        task_source(source, "cli_runtime_cache_cleanup"),
        'task cli_runtime_cache_units(runtime_dir: word, target: word, cross: word) -> int { pilot units = array_new() array_push(units, "freak_runtime.c") give back units }\n',
        'task cli_runtime_cache_ui(runtime_dir: word, cross: word) -> bool { give back false }\n',
        'task cli_runtime_cache_stem(unit: word) -> word { give back "common" }\n',
        'task cli_runtime_cache_prepare(executable: word, tool: word, unit: word, stage: int, stem: word, runtime_dir: word, opt: word, lto: word, cross: word, ui: bool) -> word { give back "' + '0' * 64 + '" }\n',
        'task cli_runtime_cache_copy_hit(root: int, key: word, stage: int, object: word) -> bool { give back false }\n',
        'task cli_runtime_cache_compile_unit(executable: word, stage: int, stem: word, runtime_dir: word, opt: word, lto: word, cross: word, ui: bool) -> bool { observed_lto = lto give back false }\n',
        'task cli_runtime_cache_inputs_stable() -> bool { give back true }\n',
        'task cli_runtime_cache_publish(root: int, key: word, stage: int, object: word) -> void {}\n',
        'task cli_runtime_cache_link(executable: word, stage: int, units: int, transpiled: word, output: word, runtime_dir: word, opt: word, lto: word, cross: word, ui: bool) -> bool { give back false }\n',
        'task cli_host_path_join(parent: word, leaf: word) -> word { give back parent + "/" + leaf }\n',
        'task cli_build_regular_output(path: word) -> bool { give back false }\n',
        'task cli_delete_derived_artifact(path: word) -> bool { give back true }\n',
        task_source(source, "cli_runtime_cache_build"),
        'task main() -> int {\n',
        'test_root_owner = fs::temp_dir("/tmp", "cache-root-control")\n',
        'if not fs::result_ok(test_root_owner) { say "root control setup failed" give back 1 }\n',
        'pilot control_outcome = cli_runtime_cache_build("compiler", "user.c", "output", "runtime", "c", "2", "full", "")\n',
        'cli_runtime_cache_cleanup(test_root_owner)\n',
        'if control_outcome != -1 or observed_lto != "full" { say "optional-stage fallback changed" give back 1 }\n',
        'say "optional-stage fallback passed"\ngive back 0\n}\n',
    ]
    return "".join(chunks)


class SourceControls(unittest.TestCase):
    """Small source guards for review boundaries; these are not native proof."""
    def setUp(self) -> None:
        self.source = (ROOT / "src/cli/runtime_cache.fk").read_text()

    def test_gate_extracts_actual_dependency_task(self) -> None:
        harness, cases = dependency_harness(self.source)
        self.assertIn(task_source(self.source, "cli_runtime_cache_dependencies"), harness)
        self.assertEqual(cases, 14)

    def test_syntax_extractor_respects_literals_and_comments(self) -> None:
        self.assertEqual(task_source('task demo() -> void { say "}" -- }\n}\n', "demo"), 'task demo() -> void { say "}" -- }\n}\n')

    def test_no_shell_cache_commands_or_unbounded_cache_reads(self) -> None:
        self.assertNotIn("process::exec", self.source)
        self.assertNotIn("fs::read(", self.source)
        self.assertNotIn("fs::write(", self.source)
        self.assertNotIn("fs::delete(", self.source)
        self.assertIn("CLI_RUNTIME_CACHE_FILE_LIMIT = 67108864", self.source)
        self.assertIn("CLI_RUNTIME_CACHE_META_LIMIT = 1048576", self.source)
        self.assertIn("CLI_RUNTIME_CACHE_DEP_LIMIT = 4096", self.source)

    def test_publication_cleans_only_unpublished_owner(self) -> None:
        body = task_source(self.source, "cli_runtime_cache_publish")
        self.assertIn("if not completed {", body)
        self.assertNotIn("remove_relative_file", body)
        self.assertNotIn("rename_relative", body)
        self.assertIn("publish_temp_dir_checked(entry, root, key)", body)

    def test_declared_names_follow_actual_lexer_vocabulary(self) -> None:
        lexer = task_source((ROOT / "src/compiler/v3/lexer.fk").read_text(), "lex_ident_token_type")
        reserved = set(re.findall(r'lower == "([a-z_]+)"', lexer))
        code = re.sub(r'"(?:\\.|[^"\\])*"|--[^\n]*', " ", self.source)
        names = re.findall(r"\bpilot\s+(?:mut\s+)?([A-Za-z_][A-Za-z_0-9]*)", code)
        names += re.findall(r"\b([A-Za-z_][A-Za-z_0-9]*)\s*:\s*(?:int|bool|word|ByteBuffer)\b", code)
        self.assertFalse(sorted({name for name in names if name.lower() in reserved}))

    def test_optional_stage_control_uses_actual_orchestration(self) -> None:
        self.assertIn(task_source(self.source, "cli_runtime_cache_build"), optional_stage_harness(self.source))

    def test_gate_uses_the_actual_public_optimization_vocabulary(self) -> None:
        main = (ROOT / "src/cli/main.fk").read_text()
        self.assertIn('flag.starts_with("--opt=")', main)
        native = inspect.getsource(native_gate)
        self.assertNotIn("--clang" + "-opt=", native)
        self.assertIn('f"--opt={optimization}"', native)

    def test_legacy_run_fallback_does_not_enter_object_admission(self) -> None:
        build = task_source(self.source, "cli_runtime_cache_build")
        context = task_source(self.source, "cli_runtime_cache_run_context")
        self.assertIn('if tool == "" or not cli_runtime_cache_tool_complete', build)
        self.assertNotIn("cli_runtime_cache_run_marker", build)
        self.assertIn('if not complete { give back cli_runtime_cache_run_marker(false, "", "unproved-tool-support") }', context)
        run = (ROOT / "src/cli/run.fk").read_text()
        self.assertIn('CLI_RUN_CACHE_SCHEMA = "freak-run-cache-v8"', run)
        self.assertIn('"|runtime-context=" + cli_runtime_cache_run_context(', run)
        self.assertIn('if fingerprint != "" and fs::exists(binary) and fs::exists(cache_file)', run)
        self.assertIn('fs::read(cache_file) == expected_record', run)
        self.assertIn('launch_fingerprint != fingerprint', run)


class _CacheLaunch:
    """Regular-file capture and a shared, directly reapable command lifeline.

    The caller registers this owner before allocating files or launching. The
    shared helper owns parent-death containment; this adapter adds no keeper.
    """
    def __init__(self, prefix: Path, record: dict, timeout: float) -> None:
        self.prefix = prefix
        self.record = record
        self.timeout = timeout
        self.output = self.errors = None
        self.child = None
        self.keeper = None
        self.finished = False

    def launch(self, argv: list[str], cwd: Path, env: dict[str, str]):
        self.output = self.prefix.with_suffix(".stdout").open("wb")
        self.errors = self.prefix.with_suffix(".stderr").open("wb")
        options = {}
        if os.name != "nt":
            # This immutable prerequisite supplies all isolation options,
            # including an owned PGID while retaining the caller's SID.
            from v3_v35_acceptance import _CommandLifeline
            self.keeper = _CommandLifeline(self.timeout)
            self.record["keeper"] = self.keeper.context
            options = self.keeper.options(None)
        spawn = self.keeper.spawn if self.keeper is not None else subprocess.Popen
        self.child = spawn(argv, cwd=cwd, env=env, stdout=self.output,
                           stderr=self.errors, **options)
        # All steps after Popen, including readiness and PID checkpoint, are
        # inside the caller's cleanup guard. The child is already retained here.
        self.record["owned_pid"] = self.child.pid
        if self.keeper is not None:
            self.keeper.context["popen_returned"] = True
            self.keeper.registered(self.child)
            self.record["owned_pgid"] = self.keeper.context["pgid"]
        return self.child

    def finish(self, normal: bool) -> list[str]:
        if self.finished:
            return []
        self.finished = True
        notes = []
        keeper_failed = False
        if self.child is None and self.keeper is not None:
            # The shared spawn API retains the actual Popen object before its
            # constructor. A constructor interrupted after fork must still be
            # waited/reaped even though launch() never returned to its caller.
            partial = self.keeper.native
            if partial is not None and getattr(partial, "_child_created", False):
                self.child = partial
                self.record["owned_pid"] = partial.pid
                if self.keeper.context.get("pgid") == partial.pid:
                    self.record["owned_pgid"] = partial.pid
        if self.keeper is not None:
            try:
                # Normal finish also drains residual descendants and actually
                # waits/reaps the direct keeper. EOF handles abrupt owner death.
                self.keeper.finish(normal)
            except BaseException as error:
                keeper_failed = True
                notes.append(f"shared lifeline finish: {type(error).__name__}: {error}")
        if self.child is not None:
            if self.keeper is None or keeper_failed:
                # Windows remains an explicitly unqualified direct-child model.
                # A failed POSIX lifeline only uses the fallback while the
                # unreaped direct child still pins its exact owned PID/group.
                try:
                    running = self.child.poll() is None
                except BaseException as error:
                    running = True
                    notes.append(f"child status: {type(error).__name__}: {error}")
                if running:
                    try:
                        notes.extend(Evidence.stop_owned(self.child))
                    except BaseException as error:
                        notes.append(f"fallback containment: {type(error).__name__}: {error}")
                        try:
                            # Direct Popen identity still belongs to us; this
                            # call has its own poll/identity guard internally.
                            self.child.kill()
                        except BaseException as secondary:
                            notes.append(f"direct child kill: {type(secondary).__name__}: {secondary}")
            try:
                self.child.wait(timeout=5)
            except BaseException as error:
                notes.append(f"owned child reap: {type(error).__name__}: {error}")
        for channel in (self.output, self.errors):
            if channel is not None:
                try:
                    channel.close()
                except BaseException as error:
                    notes.append(f"capture close: {type(error).__name__}: {error}")
        return notes


class Evidence:
    def __init__(self, root: Path) -> None:
        root.mkdir(parents=True, exist_ok=False)
        self.root = root.resolve()
        self.report = {"schema": "freak.runtime-cache-gate.v1", "outcome": "running", "commands": [], "cases": [], "inputs": []}
        self.save()

    def save(self) -> None:
        commands = self.report["commands"]
        last = commands[-1] if commands else None
        outcome = self.report["outcome"]
        active = {"phase": "report-start"}
        if last is not None:
            active = {"phase": last["status"], "fixture": last["label"],
                      "argv": last["argv"], "pid": last.get("owned_pid")}
        if outcome.startswith("passed"):
            active = {"phase": "complete"}
        self.report["progress"] = {"outcome": outcome, "active": active,
                                   "completed_commands": sum(row["status"] == "completed" for row in commands),
                                   "completed_cases": len(self.report["cases"])}
        staging = self.root / "report.new"
        staging.write_text(json.dumps(self.report, indent=2) + "\n")
        staging.replace(self.root / "report.json")

    def pin(self, path: Path) -> None:
        path = path.resolve()
        self.report["inputs"].append({"path": str(path), "sha256": sha(path)})
        self.save()

    @staticmethod
    def stop_owned(child: subprocess.Popen[bytes]) -> list[str]:
        """Fallback while the unreaped direct child pins its private PGID.

        The normal POSIX path uses the live shared keeper to drain descendants,
        including after the tracer exits. Never use this fallback on a reaped
        leader whose numeric group identity may have been recycled.
        """
        notes: list[str] = []
        for action in ("terminate", "kill"):
            try:
                if os.name != "nt":
                    os.killpg(child.pid, signal.SIGTERM if action == "terminate" else signal.SIGKILL)
                elif child.poll() is None:
                    if action == "terminate":
                        child.terminate()
                    else:
                        child.kill()
            except ProcessLookupError:
                pass
            except BaseException as error:
                notes.append(f"owned group termination: {type(error).__name__}: {error}")
            try:
                child.wait(timeout=2 if action == "terminate" else 5)
                # A successful wait releases the direct leader's PID identity.
                # Residual POSIX group containment belongs to the live keeper;
                # a fallback must never signal this number again after reap.
                break
            except subprocess.TimeoutExpired:
                if action == "kill":
                    notes.append("owned parent did not exit after bounded kill")
            except BaseException as error:
                notes.append(f"owned parent reap: {type(error).__name__}: {error}")
                if child.returncode is not None:
                    break
        return notes

    @staticmethod
    def retain_channels(prefix: Path, record: dict, trace: bool) -> None:
        for suffix in (".stdout", ".stderr", ".execve") if trace else (".stdout", ".stderr"):
            try:
                path = prefix.with_suffix(suffix)
                record[suffix[1:]] = {"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)}
            except BaseException as error:
                record.setdefault("secondary_evidence_errors", []).append(f"{suffix}: {type(error).__name__}: {error}")

    def invoke(self, argv: list[str], cwd: Path, env: dict[str, str], label: str, *, trace: bool = False, timeout: int = 240, runtime_hook: Callable[[], None] | None = None, interrupt_runtime: bool = False) -> tuple[int, str, str]:
        number = len(self.report["commands"])
        prefix = self.root / f"{number:03}-{label}"
        trace_path = prefix.with_suffix(".execve")
        actual = list(argv)
        if trace:
            actual = ["strace", "-f", "-s", "65536", "-e", "trace=execve", "-o", str(trace_path), "--", *argv]
        record = {"argv": actual, "cwd": str(cwd), "label": label, "timeout_seconds": timeout, "status": "running"}
        self.report["commands"].append(record)
        owner = _CacheLaunch(prefix, record, timeout)
        began = time.monotonic()
        completed = False
        primary_error = None
        try:
            self.save()
            child = owner.launch(actual, cwd, env)
            self.save()
            hook_fired = False
            if runtime_hook or interrupt_runtime:
                assert trace and sys.platform.startswith("linux"), "runtime hooks require actual Linux execve tracing"
                while child.poll() is None:
                    if time.monotonic() - began >= timeout:
                        raise subprocess.TimeoutExpired(actual, timeout)
                    if not hook_fired and trace_path.is_file() and runtime_compiles(trace_path.read_text(errors="replace")):
                        hook_fired = True
                        if runtime_hook:
                            runtime_hook()
                        if interrupt_runtime:
                            os.killpg(record["owned_pgid"], signal.SIGTERM)
                    time.sleep(0.02)
                returncode = child.returncode
                assert hook_fired, "actual runtime compiler never reached the requested hook"
                record["runtime_compile_hook_fired"] = True
            else:
                returncode = child.wait(timeout=timeout)
            completed = True
            record.update(status="completed", returncode=returncode, elapsed_ms=int((time.monotonic() - began) * 1000))
        except BaseException as primary:
            primary_error = primary
            record.update(status="timed_out" if isinstance(primary, subprocess.TimeoutExpired) else "harness_failed",
                          error=f"{type(primary).__name__}: {primary}", elapsed_ms=int((time.monotonic() - began) * 1000))
            raise
        finally:
            primary = primary_error
            record["cleanup_notes"] = owner.finish(completed)
            self.retain_channels(prefix, record, trace)
            try:
                self.save()
            except BaseException as secondary:
                record.setdefault("secondary_evidence_errors", []).append(f"report publication: {type(secondary).__name__}: {secondary}")
                if primary is None:
                    raise
                primary.add_note(f"secondary command report publication: {type(secondary).__name__}: {secondary}")
        if record["cleanup_notes"]:
            raise RuntimeError("cache command containment was not confirmed: " + "; ".join(record["cleanup_notes"]))
        text = ANSI.sub("", prefix.with_suffix(".stdout").read_bytes().decode("utf-8", "replace") + prefix.with_suffix(".stderr").read_bytes().decode("utf-8", "replace"))
        return returncode, text, trace_path.read_text(errors="replace") if trace else ""

    def invoke_concurrent(self, commands: list[list[str]], cwd: Path, env: dict[str, str], *, trace: bool = True, timeout: int = 240) -> None:
        assert 0 < len(commands) <= 2, "explicit concurrency budget is at most two command children"
        owners = []
        completed = False
        began = time.monotonic()
        primary_error = None
        try:
            for index, command in enumerate(commands):
                prefix = self.root / f"concurrent-{index}"
                actual = list(command)
                if trace:
                    actual = ["strace", "-f", "-s", "65536", "-e", "trace=execve", "-o", str(prefix.with_suffix(".execve")), "--", *command]
                record = {"label": f"concurrent-writer-{index}", "argv": actual, "cwd": str(cwd), "timeout_seconds": timeout, "status": "running"}
                owner = _CacheLaunch(prefix, record, timeout)
                # Register before either capture-open or Popen can fail. Every
                # prior launch and every partially opened file remains owned.
                owners.append(owner)
                self.report["commands"].append(record)
                self.save()
                owner.launch(actual, cwd, env)
                self.save()
            deadline = time.monotonic() + timeout
            for owner in owners:
                code = owner.child.wait(timeout=max(0.01, deadline - time.monotonic()))
                owner.record.update(status="completed", returncode=code, elapsed_ms=int((time.monotonic() - began) * 1000))
                self.save()
                if code != 0:
                    text = (owner.prefix.with_suffix(".stdout").read_text(errors="replace") +
                            owner.prefix.with_suffix(".stderr").read_text(errors="replace"))
                    raise AssertionError("concurrent writer exited with status " + str(code) + ": " + text)
            completed = True
        except BaseException as primary:
            primary_error = primary
            raise
        finally:
            primary = primary_error
            notes = []
            for owner in owners:
                owner.record["cleanup_notes"] = owner.finish(completed)
                notes.extend(owner.record["cleanup_notes"])
                if owner.record["status"] != "completed":
                    owner.record.update(status="timed_out" if isinstance(primary, subprocess.TimeoutExpired) else "harness_failed",
                                        error=f"{type(primary).__name__}: {primary}")
                self.retain_channels(owner.prefix, owner.record, trace)
            try:
                self.save()
            except BaseException as secondary:
                for owner in owners:
                    owner.record.setdefault("secondary_evidence_errors", []).append(
                        f"report publication: {type(secondary).__name__}: {secondary}")
                if primary is None:
                    raise
                primary.add_note(f"secondary concurrent report publication: {type(secondary).__name__}: {secondary}")
            if primary is None and notes:
                raise RuntimeError("concurrent cache containment was not confirmed: " + "; ".join(notes))


    def case(self, label: str, **facts: object) -> None:
        self.report["cases"].append({"label": label, "outcome": "passed", **facts})
        self.save()


def events(output: str) -> list[tuple[str, str, str]]:
    return [(event, unit, key or "") for event, unit, key in EVENT.findall(output)]


def runtime_compiles(trace: str) -> int:
    # Count successful driver execve launches, not the integrated cc1 row.
    return sum('execve(' in row and '"-c"' in row and '"cpp-output"' in row and '"-###"' not in row and '= 0' in row for row in trace.splitlines())


def native_gate(args: argparse.Namespace, evidence: Evidence) -> None:
    freak = args.freak.resolve(strict=True)
    clang = args.clang.resolve(strict=True)
    payload = args.payload.resolve(strict=True)
    assert (payload / "runtime/freak_runtime.c").is_file(), payload
    assert (payload / "std/freak_abi").is_file(), payload
    assert sys.platform.startswith("linux"), "This milestone qualifies Linux reuse; Windows/macOS closure/native coverage remains pending."
    assert shutil.which("strace"), "Linux qualification requires actual execve evidence."
    for path in (freak, clang, ROOT / "src/cli/runtime_cache.fk", ROOT / "src/cli/build.fk", ROOT / "src/cli/run.fk",
                 ROOT / "src/compiler/v3/lexer.fk", ROOT / "tests/v3_v35_acceptance.py",
                 ROOT / "tests/test_v3_v35_runtime_cache_tool_resolution.py", Path(__file__)):
        evidence.pin(path)
    work = evidence.root / "work"
    work.mkdir(mode=0o700)
    owned_payload = work / "payload"
    shutil.copytree(payload, owned_payload)
    cache_parent = work / "cache"
    cache_parent.mkdir(mode=0o700)
    env = dict(os.environ, FREAK_HOME=str(owned_payload), FREAK_CLANG=str(clang), XDG_CACHE_HOME=str(cache_parent), FREAK_RUNTIME_CACHE_TRACE="1")
    env.pop("FREAK_RUNTIME_CACHE", None)
    source_a = work / "a.fk"
    source_b = work / "b.fk"
    source_a.write_text('task main() -> int { say 41 give back 0 }\n')
    source_b.write_text('task main() -> int { say 42 give back 0 }\n')

    def build(source: Path, label: str, *, target: str = "c", optimization: int = 0, lto: str = "off", selected_env: dict[str, str] | None = None, compile_count: int | None = None, cwd: Path | None = None) -> list[tuple[str, str, str]]:
        active = selected_env or env
        code, output, trace = evidence.invoke([str(freak), "build", str(source), "--" + target, f"--opt={optimization}", f"--lto={lto}"], cwd or work, active, label, trace=True)
        assert code == 0, output
        found = events(output)
        actual_count = runtime_compiles(trace)
        if compile_count is not None:
            assert actual_count == compile_count, (label, actual_count, compile_count, output, trace)
        assert sum(event == "compile" for event, _, _ in found) == actual_count, (label, found, actual_count)
        binary = source.with_suffix("")
        generated = str(source) + (".ll" if target == "llvm" else ".c")
        links = [row for row in trace.splitlines() if "execve(" in row and "= 0" in row and json.dumps(generated) in row and json.dumps(str(binary)) in row and '"-E"' not in row and '"-###"' not in row]
        assert len(links) == 1, (label, "user code was not freshly compiled/linked", links)
        assert "/freak/runtime-v1/" not in links[0], "linked a live persistent-cache pathname"
        evidence.case(label, events=found, actual_runtime_compiles=actual_count, binary_sha256=sha(binary))
        return found

    def execute(source: Path, expected: str, label: str) -> None:
        code, output, _ = evidence.invoke([str(source.with_suffix(""))], work, env, label)
        assert code == 0 and output == expected, (code, output, expected)
        evidence.case(label, stdout=output)

    cold = build(source_a, "cold-common", compile_count=1)
    assert cold and cold[0][0] == "compile", cold
    key = next(key for event, unit, key in cold if unit == "freak_runtime.c")
    root = cache_parent / "freak/runtime-v1"
    entry = root / key
    initial = {path.name: sha(path) for path in entry.iterdir() if path.is_file()}
    build(source_b, "different-program-warm", compile_count=0)
    execute(source_a, "41\n", "execute-a")
    execute(source_b, "42\n", "execute-b")
    source_b.write_text('task main() -> int { say 43 give back 0 }\n')
    build(source_b, "changed-user-warm", compile_count=0)
    execute(source_b, "43\n", "execute-changed-b")
    # The key must not depend on the directory a build starts in.
    elsewhere = work / "elsewhere"
    elsewhere.mkdir(mode=0o700)
    source_c = elsewhere / "c.fk"
    source_c.write_text('task main() -> int { say 44 give back 0 }\n')
    build(source_c, "other-directory-warm", compile_count=0, cwd=elsewhere)
    execute(source_c, "44\n", "execute-other-directory")
    assert initial == {path.name: sha(path) for path in entry.iterdir() if path.is_file()}, "warm hit mutated the entry"
    evidence.case("immutable-warm-entry", key=key)

    runtime_header = owned_payload / "runtime/freak_runtime.h"
    original_header = runtime_header.read_bytes()
    original_stat = runtime_header.stat()
    changed = original_header.replace(b"runtime", b"runtimE", 1)
    assert changed != original_header and len(changed) == len(original_header)
    runtime_header.write_bytes(changed)
    os.utime(runtime_header, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))
    build(source_b, "same-mtime-header-miss", compile_count=1)
    runtime_header.write_bytes(original_header)
    os.utime(runtime_header, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))
    build(source_b, "restored-header-hit", compile_count=0)

    runtime_inc = owned_payload / "runtime/freak_v35_http.inc"
    original_inc = runtime_inc.read_bytes()
    original_inc_stat = runtime_inc.stat()
    runtime_inc.write_bytes(original_inc + b"\n/* raw dependency cache control */\n")
    os.utime(runtime_inc, ns=(original_inc_stat.st_atime_ns, original_inc_stat.st_mtime_ns))
    build(source_b, "runtime-inc-raw-change-miss", compile_count=1)
    runtime_inc.write_bytes(original_inc)
    os.utime(runtime_inc, ns=(original_inc_stat.st_atime_ns, original_inc_stat.st_mtime_ns))
    build(source_b, "restored-runtime-inc-hit", compile_count=0)

    include_shadow = work / "sdk-shadow"
    include_shadow.mkdir()
    shadow_env = dict(env, CPATH=str(include_shadow))
    build(source_b, "sdk-search-context-cold", selected_env=shadow_env, compile_count=1)
    build(source_b, "sdk-search-context-warm", selected_env=shadow_env, compile_count=0)
    shadow = include_shadow / "stdio.h"
    shadow.write_text('#include_next <stdio.h>\n/* shadow version 01 */\n')
    build(source_b, "new-higher-priority-header-miss", selected_env=shadow_env, compile_count=1)
    shadow_stat = shadow.stat()
    shadow.write_text('#include_next <stdio.h>\n/* shadow version 02 */\n')
    os.utime(shadow, ns=(shadow_stat.st_atime_ns, shadow_stat.st_mtime_ns))
    build(source_b, "same-mtime-sdk-header-miss", selected_env=shadow_env, compile_count=1)
    execute(source_b, "43\n", "execute-sdk-shadow")

    driver_root = work / "selected-driver"
    driver_bin = driver_root / "bin"
    driver_bin.mkdir(parents=True)
    selected_driver = driver_bin / "clang"
    shutil.copy2(clang, selected_driver)
    # Preserve the selected distribution's relative library/resource layout;
    # only the test-owned executable is mutated, never the supplied SDK.
    original_lib = clang.parent.parent / "lib"
    if original_lib.is_dir():
        (driver_root / "lib").symlink_to(original_lib, target_is_directory=True)
    code, resource, _ = evidence.invoke([str(clang), "-print-resource-dir"], work, env, "selected-resource-dir")
    assert code == 0 and Path(resource.strip()).is_dir(), resource
    (driver_bin / "clang.cfg").write_text("-resource-dir=" + resource.strip() + "\n")
    driver_env = dict(env, FREAK_CLANG=str(selected_driver))
    build(source_a, "selected-driver-cold", selected_env=driver_env, compile_count=1)
    build(source_b, "selected-driver-warm", selected_env=driver_env, compile_count=0)
    original_driver_stat = selected_driver.stat()
    before_driver = sha(selected_driver)
    with selected_driver.open("ab") as stream:
        stream.write(b"FREAK runtime cache executable-byte control\n")
    os.utime(selected_driver, ns=(original_driver_stat.st_atime_ns, original_driver_stat.st_mtime_ns))
    assert sha(selected_driver) != before_driver
    build(source_b, "same-path-driver-byte-change-miss", selected_env=driver_env, compile_count=1)
    build(source_a, "changed-driver-warm", selected_env=driver_env, compile_count=0)
    code, closure, _ = evidence.invoke(["ldd", str(selected_driver)], work, driver_env, "selected-driver-loader-closure")
    assert code == 0, closure
    libraries = re.findall(r"^\s*(\S*(?:libLLVM|libclang-cpp)\S*)\s+=>\s+(/.*?)\s+\(", closure, re.M)
    assert libraries, "qualification requires a dynamic codegen support image"
    library_name, library_path = libraries[0]
    private_support = work / "selected-support"
    private_support.mkdir(mode=0o700)
    selected_support = private_support / library_name
    shutil.copy2(Path(library_path).resolve(), selected_support)
    support_env = dict(driver_env, LD_LIBRARY_PATH=str(private_support) + os.pathsep + env.get("LD_LIBRARY_PATH", ""))
    code, selected_closure, _ = evidence.invoke(["ldd", str(selected_driver)], work, support_env, "private-selected-loader-closure")
    assert code == 0 and str(selected_support) in selected_closure, selected_closure
    build(source_a, "selected-support-cold", selected_env=support_env, compile_count=1)
    build(source_b, "selected-support-warm", selected_env=support_env, compile_count=0)
    support_stat = selected_support.stat()
    with selected_support.open("ab") as stream:
        stream.write(b"FREAK runtime cache selected-support raw-byte control\n")
    os.utime(selected_support, ns=(support_stat.st_atime_ns, support_stat.st_mtime_ns))
    build(source_b, "same-path-support-byte-change-miss", selected_env=support_env, compile_count=1)
    build(source_a, "changed-support-warm", selected_env=support_env, compile_count=0)

    code, assembler_spelling, _ = evidence.invoke([str(clang), "-print-prog-name=as"], work, env, "selected-external-assembler")
    assert code == 0, assembler_spelling
    assembler_origin = shutil.which(assembler_spelling.strip()) or assembler_spelling.strip()
    private_assembler = work / "selected-assembler"
    private_assembler.mkdir(mode=0o700)
    assembler = private_assembler / "as"
    shutil.copy2(Path(assembler_origin).resolve(strict=True), assembler)
    (driver_bin / "clang.cfg").write_text("-resource-dir=" + resource.strip() + "\n-fno-integrated-as\n-B" + str(private_assembler) + "\n")
    refusal = build(source_a, "unproved-assembler-source-fallback", selected_env=driver_env, compile_count=0)
    assert not any(event == "hit" for event, _, _ in refusal), refusal
    assembler_stat = assembler.stat()
    with assembler.open("ab") as stream:
        stream.write(b"FREAK unproved assembler byte-change control\n")
    os.utime(assembler, ns=(assembler_stat.st_atime_ns, assembler_stat.st_mtime_ns))
    refusal = build(source_b, "changed-unproved-assembler-still-no-hit", selected_env=driver_env, compile_count=0)
    assert not any(event == "hit" for event, _, _ in refusal), refusal
    (driver_bin / "clang.cfg").write_text("-resource-dir=" + resource.strip() + "\n")

    for optimization in (1, 2, 3):
        build(source_a, f"O{optimization}-cold", optimization=optimization, compile_count=1)
        build(source_b, f"O{optimization}-warm", optimization=optimization, compile_count=0)
    llvm_cold = build(source_a, "llvm-bridge-cold", target="llvm", compile_count=1)
    assert any(event == "hit" and unit == "freak_runtime.c" for event, unit, _ in llvm_cold), llvm_cold
    build(source_b, "llvm-bridge-warm", target="llvm", compile_count=0)
    execute(source_b, "43\n", "execute-llvm")
    for lto in ("thin", "full"):
        build(source_a, f"{lto}-cold", lto=lto, compile_count=1)
        build(source_b, f"{lto}-warm", lto=lto, compile_count=0)
        execute(source_b, "43\n", f"execute-{lto}")

    object_path = entry / "runtime.o"
    object_bytes = object_path.read_bytes()
    object_path.write_bytes(object_bytes[:max(1, len(object_bytes) // 2)])
    truncated_hash = sha(object_path)
    build(source_a, "truncated-object-miss", compile_count=1)
    assert sha(object_path) == truncated_hash, "corrupt occupied entry was overwritten"
    object_path.write_bytes(object_bytes)
    receipt_path = entry / "receipt"
    receipt = receipt_path.read_bytes()
    receipt_path.write_bytes(receipt.replace(key.encode(), b"f" * 64, 1))
    wrong_receipt_hash = sha(receipt_path)
    build(source_b, "wrong-key-receipt-miss", compile_count=1)
    assert sha(receipt_path) == wrong_receipt_hash, "invalid occupied receipt was overwritten"
    receipt_path.write_bytes(receipt)
    build(source_b, "repaired-by-test-owner-hit", compile_count=0)
    object_path.unlink()
    foreign_object = work / "foreign-object"
    foreign_object.write_bytes(object_bytes)
    object_path.symlink_to(foreign_object)
    build(source_b, "symlink-object-miss", compile_count=1)
    assert sha(foreign_object) == hashlib.sha256(object_bytes).hexdigest() and object_path.is_symlink()
    object_path.unlink()
    object_path.write_bytes(object_bytes)
    with object_path.open("wb") as stream:
        stream.truncate(67108865)
    build(source_b, "oversized-object-miss", compile_count=1)
    assert object_path.stat().st_size == 67108865
    object_path.write_bytes(object_bytes)
    receipt_path.write_bytes(b"x" * 1048577)
    build(source_b, "oversized-receipt-miss", compile_count=1)
    assert receipt_path.stat().st_size == 1048577
    receipt_path.write_bytes(receipt)

    import fcntl
    with (root / f"{key}.lock").open("r+b") as held:
        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        build(source_a, "contended-key-uncached-object", compile_count=1)
    build(source_a, "lock-released-hit", compile_count=0)
    incomplete = entry / "receipt.saved"
    receipt_path.rename(incomplete)
    build(source_b, "partial-entry-miss", compile_count=1)
    assert not receipt_path.exists() and incomplete.read_bytes() == receipt
    incomplete.rename(receipt_path)

    # A detached partially written stage is never a candidate hit or repair
    # target. Its test-owned bytes are preserved through a successful warm hit.
    partial_stage = root / "freak-runtime-entry-interrupted-control"
    partial_stage.mkdir(mode=0o700)
    (partial_stage / "runtime.o").write_bytes(object_bytes[:17])
    build(source_b, "unpublished-partial-stage-ignored", compile_count=0)
    assert (partial_stage / "runtime.o").read_bytes() == object_bytes[:17]

    root.chmod(0o777)
    fallback = build(source_a, "insecure-root-source-fallback", compile_count=0)
    assert any(event == "fallback" and unit == "cache-root" for event, unit, _ in fallback), fallback
    assert root.stat().st_mode & 0o777 == 0o777, "foreign/insecure root was repaired"
    root.chmod(0o700)
    foreign = work / "foreign"
    foreign.mkdir()
    marker = foreign / "marker"
    marker.write_bytes(b"preserve foreign cache target\n")
    freak_container = cache_parent / "freak"
    relocated = cache_parent / "freak-owned"
    freak_container.rename(relocated)
    freak_container.symlink_to(foreign, target_is_directory=True)
    fallback = build(source_b, "symlink-root-source-fallback", compile_count=0)
    assert any(event == "fallback" and unit == "cache-root" for event, unit, _ in fallback)
    assert marker.read_bytes() == b"preserve foreign cache target\n" and list(foreign.iterdir()) == [marker]
    freak_container.unlink()
    relocated.rename(freak_container)
    disabled = dict(env, FREAK_RUNTIME_CACHE="off")
    build(source_a, "explicit-cache-off-source-build", selected_env=disabled, compile_count=0)
    unavailable = dict(env, XDG_CACHE_HOME="/proc")
    build(source_a, "unwritable-root-source-fallback", selected_env=unavailable, compile_count=0)
    default_home = work / "default-cache-home"
    default_home.mkdir(mode=0o700)
    default_env = dict(env, HOME=str(default_home), XDG_CACHE_HOME="relative-is-ignored")
    build(source_a, "relative-xdg-default-home-cold", selected_env=default_env, compile_count=1)
    build(source_b, "default-home-warm", selected_env=default_env, compile_count=0)
    assert (default_home / ".cache/freak/runtime-v1").is_dir()

    # A complete-program run hit must not bypass the same SDK closure.
    def run(label: str) -> str:
        code, output, _ = evidence.invoke([str(freak), "run", str(source_b), "--c", "--opt=0", "--lto=off"], work, shadow_env, label, trace=True)
        assert code == 0 and "43\n" in output, output
        evidence.case(label, complete_program_hit="run cache hit" in output)
        return output
    first = run("run-context-cold")
    second = run("run-context-warm")
    assert "run cache hit" not in first and "run cache hit" in second, (first, second)
    shadow_stat = shadow.stat()
    shadow.write_text('#include_next <stdio.h>\n/* shadow version 03 */\n')
    os.utime(shadow, ns=(shadow_stat.st_atime_ns, shadow_stat.st_mtime_ns))
    third = run("run-sdk-change-invalidates-program")
    assert "run cache hit" not in third, third
    assert "run cache hit" in run("run-sdk-change-warm"), "new SDK context never became fresh"

    # Opaque wrappers retain the existing whole-program cache contract. They
    # never qualify runtime-object reuse or the new hidden-tool/SDK guarantee.
    opaque_driver = work / "opaque-clang"
    opaque_driver.write_text("#!/bin/sh\nexec " + shlex.quote(str(clang)) + ' "$@"\n')
    opaque_driver.chmod(0o700)
    legacy_env = dict(shadow_env, FREAK_CLANG=str(opaque_driver))
    def legacy_run(label: str, hit: bool) -> None:
        code, output, trace = evidence.invoke([str(freak), "run", str(source_b), "--c", "--opt=0", "--lto=off"], work, legacy_env, label, trace=True)
        assert code == 0 and "43\n" in output and ("run cache hit" in output) is hit, output
        assert not any(event == "hit" for event, _, _ in events(output)), "legacy wrapper reused a runtime object"
        assert runtime_compiles(trace) == 0, "legacy wrapper used runtime object compilation"
        if hit:
            generated = json.dumps(str(source_b) + ".c")
            assert not any("execve(" in row and "= 0" in row and generated in row and '"-###"' not in row for row in trace.splitlines()), "legacy warm run compiled or linked user code"
        evidence.case(label, complete_program_hit=hit, context_scope="legacy; no new SDK/hidden-tool qualification")
    legacy_run("proven-to-legacy-context-cold", False)
    legacy_run("opaque-wrapper-legacy-warm", True)
    assert "run cache hit" not in run("legacy-to-proven-context-cold"), "legacy marker admitted a prior proven context"
    assert "run cache hit" in run("restored-proven-context-warm")

    # Compile grammar controls from the implementation, using this installed
    # CLI's normal build path and selected runtime, rather than a Python model.
    harness, cases = dependency_harness((ROOT / "src/cli/runtime_cache.fk").read_text())
    parser_source = work / "dependency-controls.fk"
    parser_source.write_text(harness)
    build(parser_source, "dependency-parser-build", compile_count=0)
    execute(parser_source, "dependency controls passed\n", "dependency-parser-execute")
    evidence.case("actual-freak-dependency-parser", controls=cases)
    from test_v3_v35_runtime_cache_tool_resolution import harness as hash_resolution_harness
    hash_source = work / "hash-resolution-controls.fk"
    hash_source.write_text(hash_resolution_harness())
    build(hash_source, "hash-resolution-control-build", compile_count=0)
    execute(hash_source, "runtime hash resolution controls passed (12 cases)\n", "hash-resolution-control-execute")
    evidence.case("actual-freak-hash-resolution", controls=12)
    for name in ("DYLD_LIBRARY_PATH", "DYLD_FRAMEWORK_PATH", "DYLD_VERSIONED_LIBRARY_PATH", "DYLD_ROOT_PATH"):
        dyld_env = dict(env, **{name: str(foreign)}, CACHE_CONTROL_DYLD_REJECT="1")
        code, output, _ = evidence.invoke([str(parser_source.with_suffix(""))], work, dyld_env, "dyld-refusal-" + name.lower())
        assert code == 0 and output == "dependency controls passed\n", output
        evidence.case("dyld-refusal-" + name.lower())
    stage_source = work / "optional-stage-controls.fk"
    stage_source.write_text(optional_stage_harness((ROOT / "src/cli/runtime_cache.fk").read_text()))
    build(stage_source, "optional-stage-control-build", compile_count=0)
    execute(stage_source, "optional-stage fallback passed\n", "optional-stage-control-execute")

    mutation_parent = work / "mutation-cache"
    mutation_parent.mkdir(mode=0o700)
    mutation_env = dict(env, XDG_CACHE_HOME=str(mutation_parent))
    try:
        code, output, _ = evidence.invoke([str(freak), "build", str(source_a), "--c", "--opt=0", "--lto=off"], work, mutation_env, "runtime-source-mutation-during-object", trace=True, runtime_hook=lambda: runtime_header.write_bytes(original_header + b"\n/* changed during native compilation */\n"))
        assert code != 0 and not source_a.with_suffix("").exists(), (code, output)
        assert not (mutation_parent / "freak/runtime-v1" / key).exists(), "published a changed-input object"
        evidence.case("runtime-source-mutation-during-object", returncode=code)
    finally:
        runtime_header.write_bytes(original_header)
        os.utime(runtime_header, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))
    alias_parent = work / "retargeted-header-cache"
    alias_parent.mkdir(mode=0o700)
    alias_env = dict(env, XDG_CACHE_HOME=str(alias_parent))
    header_old = work / "header-old.h"
    header_new = work / "header-new.h"
    header_old.write_bytes(original_header)
    header_new.write_bytes(original_header + b"\n/* different logical header target */\n")
    runtime_header.unlink()
    runtime_header.symlink_to(header_old)
    def retarget_header() -> None:
        replacement = runtime_header.with_suffix(".retarget")
        replacement.symlink_to(header_new)
        replacement.replace(runtime_header)
    try:
        code, output, _ = evidence.invoke([str(freak), "build", str(source_a), "--c", "--opt=0", "--lto=off"], work, alias_env, "logical-header-retarget-during-object", trace=True, runtime_hook=retarget_header)
        assert code != 0 and not source_a.with_suffix("").exists(), (code, output)
        admitted_keys = [found_key for event, unit, found_key in events(output) if event == "compile" and unit == "freak_runtime.c"]
        assert len(admitted_keys) == 1, ("no exact admitted key in retained compile evidence", output)
        assert not (alias_parent / "freak/runtime-v1" / admitted_keys[0]).exists(), "published a logically rebound header object"
        evidence.case("logical-header-retarget-during-object", returncode=code, refused_publication_key=admitted_keys[0])
    finally:
        runtime_header.unlink()
        runtime_header.write_bytes(original_header)
        os.utime(runtime_header, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))
    interrupted_parent = work / "interrupted-cache"
    interrupted_parent.mkdir(mode=0o700)
    interrupted_env = dict(env, XDG_CACHE_HOME=str(interrupted_parent))
    code, output, _ = evidence.invoke([str(freak), "build", str(source_a), "--c", "--opt=0", "--lto=off"], work, interrupted_env, "interrupt-runtime-writer", trace=True, interrupt_runtime=True)
    assert code != 0 and not source_a.with_suffix("").exists(), (code, output)
    assert not (interrupted_parent / "freak/runtime-v1" / key).exists(), "interrupted writer published incomplete output"
    evidence.case("interrupt-runtime-writer", returncode=code)
    build(source_a, "after-interrupted-writer-cold", selected_env=interrupted_env, compile_count=1)
    build(source_b, "after-interrupted-writer-warm", selected_env=interrupted_env, compile_count=0)

    if args.concurrent_writers:
        # Explicit opt-in: the lead must reserve two compiler children for this
        # one bounded contract. Ordinary gate invocations serialize compilation.
        concurrent_parent = work / "concurrent-cache"
        concurrent_parent.mkdir(mode=0o700)
        concurrent_env = dict(env, XDG_CACHE_HOME=str(concurrent_parent))
        seeded = build(source_a, "concurrent-root-seed", selected_env=concurrent_env, compile_count=1)
        concurrent_key = next(found_key for _, unit, found_key in seeded if unit == "freak_runtime.c")
        concurrent_root = concurrent_parent / "freak/runtime-v1"
        (concurrent_root / concurrent_key).rename(concurrent_root / (concurrent_key + "-test-owned-backup"))
        evidence.invoke_concurrent([[str(freak), "build", str(source), "--c", "--opt=0", "--lto=off"]
                                    for source in (source_a, source_b)], work, concurrent_env,
                                   trace=True, timeout=240)
        winner = concurrent_root / concurrent_key
        winner_object = winner / "runtime.o"
        winner_bytes = winner_object.read_bytes()
        expected_receipt = f"{SCHEMA}\n{concurrent_key}\n{concurrent_key}\n{len(winner_bytes)}\n{sha(winner_object)}\ncomplete\n"
        assert winner_bytes and (winner / "receipt").read_text() == expected_receipt
        build(source_a, "concurrent-complete-winner-hit", selected_env=concurrent_env, compile_count=0)
        execute(source_a, "41\n", "execute-concurrent-a")
        execute(source_b, "43\n", "execute-concurrent-b")
        evidence.case("concurrent-immutable-publication", winner=concurrent_key, bounded_compiler_children=2)
    else:
        evidence.report["concurrent_publication"] = "not run: explicit two-compiler grant required"

    # A live cache-path replacement after a hit has been copied cannot alter
    # the privately staged object consumed by the fresh program link.
    # The held-read/copy architecture is also verified in independent review.
    assert object_path.read_bytes() == object_bytes

    # Failure and complete publication controls require no injected fallbacks.
    bad_source = work / "bad.fk"
    bad_source.write_text('task main() -> int { say unknown_name give back 0 }\n')
    code, output, _ = evidence.invoke([str(freak), "build", str(bad_source), "--c"], work, env, "source-failure-preserved", trace=True)
    assert code != 0 and not bad_source.with_suffix("").exists(), output
    evidence.case("source-failure-preserved", returncode=code)
    evidence.report["boundaries"] = [
        "Linux native only at this milestone; Windows/macOS tool closure and installed archive gates remain pending.",
        "Unknown Windows DLL selection and unresolved/static support closure disable cache reuse.",
        "Private owned staging excludes arbitrary concurrent same-user pathname replacement; no anchored child-I/O primitive is claimed.",
        "Same-path driver/support bytes, external-assembler refusal, source mutation and interruption controls are prepared; native target/UI/profile qualification remains pending.",
        "Concurrent publication is opt-in and requires the root to grant two bounded compiler children; the default gate keeps one native compiler at a time.",
    ]
    for pin in evidence.report["inputs"]:
        assert sha(Path(pin["path"])) == pin["sha256"], "pinned native gate input changed: " + pin["path"]
    evidence.report["pinned_inputs_unchanged"] = True
    evidence.report["outcome"] = "passed-focused-linux"
    evidence.save()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pure", action="store_true", help="run source controls only; no compiler/native qualification")
    parser.add_argument("--freak", type=Path)
    parser.add_argument("--clang", type=Path)
    parser.add_argument("--payload", type=Path)
    parser.add_argument("--evidence-dir", type=Path)
    parser.add_argument("--concurrent-writers", action="store_true", help="reserve two bounded compiler children for publication races; requires the lead's native resource grant")
    args = parser.parse_args()
    if args.pure:
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SourceControls))
        return 0 if result.wasSuccessful() else 1
    if not all((args.freak, args.clang, args.payload, args.evidence_dir)):
        parser.error("native mode requires --freak, --clang, --payload and a new --evidence-dir")
    evidence = Evidence(args.evidence_dir)
    try:
        native_gate(args, evidence)
    except BaseException as error:
        evidence.report.update(outcome="failed", error=f"{type(error).__name__}: {error}")
        try:
            evidence.save()
        except BaseException as secondary:
            error.add_note(f"secondary final report publication: {type(secondary).__name__}: {secondary}")
        raise
    print(json.dumps({"outcome": evidence.report["outcome"], "report": str(evidence.root / "report.json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
