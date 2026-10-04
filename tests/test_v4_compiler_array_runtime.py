"""Process-free hostile oracles for the private compiler-array prerequisite."""
from __future__ import annotations

from contextlib import redirect_stdout, redirect_stderr
import ast
import copy
import importlib.util
import io
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

# Source-forcing import keeps pure tests independent of ignored repository pyc.
_path = Path(__file__).with_name("v4_compiler_array_runtime.py")
_spec = importlib.util.spec_from_file_location("private_array_gate_pure", _path)
gate = importlib.util.module_from_spec(_spec)
exec(compile(_path.read_bytes(), str(_path), "exec"), gate.__dict__)


class CompilerArrayOracleTests(unittest.TestCase):
    def setUp(self):
        self.api_traps = []
        for name in ("Popen", "run", "call", "check_call", "check_output"):
            trap = mock.patch.object(subprocess, name, side_effect=AssertionError("actual process forbidden in pure test"))
            self.api_traps.append(trap.start())
            self.addCleanup(trap.stop)
        self.addCleanup(self.assert_no_actual_process)

    def assert_no_actual_process(self):
        self.assertTrue(all(trap.call_count == 0 for trap in self.api_traps))

    @staticmethod
    def result(status=0, stdout=b"", stderr=b""):
        return subprocess.CompletedProcess(["process-free-probe"], status, stdout, stderr)

    def test_positive_exact_rows_status_channels_and_platform(self):
        for platform in ("linux", "darwin", "win32"):
            for _, case in gate.POSITIVE_CASES:
                expected = gate.positive_stdout(case)
                gate.assert_positive(self.result(stdout=expected), case, platform=platform)
                if platform == "win32":
                    gate.assert_positive(self.result(stdout=expected.replace(b"\n", b"\r\n")), case, platform=platform)
                else:
                    with self.assertRaises(AssertionError):
                        gate.assert_positive(self.result(stdout=expected.replace(b"\n", b"\r\n")), case, platform=platform)
                for stdout in (b"", expected[:-1], expected + b"extra\n", expected.replace(b"=ok", b"=false")):
                    with self.subTest(platform=platform, case=case), self.assertRaises(AssertionError):
                        gate.assert_positive(self.result(stdout=stdout), case, platform=platform)
                for status in (1, 3, 85, 86, 87, 88, -signal.SIGABRT, -signal.SIGSEGV):
                    with self.assertRaises(AssertionError):
                        gate.assert_positive(self.result(status, expected), case, platform=platform)
                for stderr in (b"\n", b"ownership audit\n", b"ERROR: AddressSanitizer\n"):
                    with self.assertRaises(AssertionError):
                        gate.assert_positive(self.result(stdout=expected, stderr=stderr), case, platform=platform)
        self.assertEqual(len(gate.NORMAL_ROWS), 5)

    def test_rejections_require_exact_abort_or_exit_not_arbitrary_failure(self):
        for platform in ("linux", "darwin", "win32"):
            for case in (*gate.EXIT_CASES, *gate.ABORT_CASES):
                if case in gate.EXIT_CASES:
                    status, stderr = 1, gate.EXIT_CASES[case].encode()
                else:
                    status = 3 if platform == "win32" else -signal.SIGABRT
                    stderr = f"FREAK: V4 word panic: {gate.ABORT_CASES[case]}\n".encode()
                gate.assert_rejection(self.result(status, stderr=stderr), case, platform=platform)
                for changed in (b"", stderr[:-1], stderr + b"unexpected-atexit\n", stderr.replace(b"FREAK:", b"PANIC:")):
                    with self.assertRaises(AssertionError):
                        gate.assert_rejection(self.result(status, stderr=changed), case, platform=platform)
                for wrong in (0, 85, 86, 87, 88, -signal.SIGSEGV):
                    with self.assertRaises(AssertionError):
                        gate.assert_rejection(self.result(wrong, stderr=stderr), case, platform=platform)
                with self.assertRaises(AssertionError):
                    gate.assert_rejection(self.result(status, b"unwanted\n", stderr), case, platform=platform)
                if platform == "win32":
                    gate.assert_rejection(self.result(status, stderr=stderr.replace(b"\n", b"\r\n")), case, platform=platform)
                else:
                    with self.assertRaises(AssertionError):
                        gate.assert_rejection(self.result(status, stderr=stderr.replace(b"\n", b"\r\n")), case, platform=platform)

    def test_both_actual_ownership_audits_required(self):
        for kind, status in (("C", 87), ("LLVM", 86)):
            stderr = f"FREAK: {kind} ownership audit found 1 unreleased word allocation(s)\n".encode()
            gate.assert_audit(self.result(status, stderr=stderr), kind)
            for wrong in (0, 1, 3, 88, -signal.SIGABRT):
                with self.assertRaises(AssertionError):
                    gate.assert_audit(self.result(wrong, stderr=stderr), kind)
            for mutated in (b"", stderr + b"extra\n", stderr.replace(b"1 unreleased", b"2 unreleased")):
                with self.assertRaises(AssertionError):
                    gate.assert_audit(self.result(status, stderr=mutated), kind)

    def test_sanitizer_capability_needs_exact_kind_diagnostic_and_exit(self):
        examples = {
            "address": b"ERROR: AddressSanitizer: heap-use-after-free\nSUMMARY: AddressSanitizer:\n",
            "undefined": b"runtime error: signed integer overflow\nSUMMARY: UndefinedBehaviorSanitizer:\n",
        }
        for kind, stderr in examples.items():
            gate.assert_sanitizer(self.result(88, stderr=stderr), kind)
            for wrong in (0, 1, 3, 86, 87, -signal.SIGSEGV):
                with self.assertRaises(AssertionError):
                    gate.assert_sanitizer(self.result(wrong, stderr=stderr), kind)
            for mutated in (b"", stderr.splitlines()[0], stderr + b"ownership audit\n", stderr + b"LeakSanitizer\n"):
                with self.assertRaises(AssertionError):
                    gate.assert_sanitizer(self.result(88, stderr=mutated), kind)
            with self.assertRaises(AssertionError):
                gate.assert_sanitizer(self.result(88, stderr=examples["undefined" if kind == "address" else "address"]), kind)

    @staticmethod
    def complete_report(sanitized):
        return {
            "sanitized": sanitized,
            "positives": [{"opt": opt, "profile": profile, "case": case, "binary_sha256": "a" * 64}
                          for opt in (0, 2, 3) for profile, case in gate.POSITIVE_CASES],
            "production": [{"opt": opt, "profile": profile, "object_sha256": "b" * 64}
                           for opt in (0, 2, 3) for profile in ("pressure", "dynamic", "retire", "capacity")],
            "rejections": [{"opt": opt, "case": case} for opt in (0, 2, 3)
                           for case in (*gate.EXIT_CASES, *gate.ABORT_CASES)],
            "capabilities": [f"audit-{kind}-O{opt}" for opt in (0, 2, 3) for kind in ("C", "LLVM")] +
                            (["sanitizer-address", "sanitizer-undefined"] if sanitized else []),
        }

    def test_matrix_requires_all_levels_profiles_exact_rows_and_capabilities(self):
        for sanitized in (False, True):
            complete = self.complete_report(sanitized)
            gate.validate_completion(complete, sanitized)
            self.assertEqual((len(complete["positives"]), len(complete["production"]), len(complete["rejections"])), (18, 12, 45))
            for key in ("positives", "production", "rejections", "capabilities"):
                for index in range(len(complete[key])):
                    changed = copy.deepcopy(complete)
                    del changed[key][index]
                    with self.assertRaises(AssertionError):
                        gate.validate_completion(changed, sanitized)
                changed = copy.deepcopy(complete)
                changed[key].append(copy.deepcopy(changed[key][0]))
                with self.assertRaises(AssertionError):
                    gate.validate_completion(changed, sanitized)
            changed = copy.deepcopy(complete)
            changed["positives"][0]["binary_sha256"] = "unknown"
            with self.assertRaises(AssertionError):
                gate.validate_completion(changed, sanitized)
            with self.assertRaises(AssertionError):
                gate.validate_completion(complete, not sanitized)

    def test_required_flags_cannot_disable_assertions_audits_or_quota(self):
        for sanitized in (False, True):
            for profile, flags in gate.PROFILES.items():
                required = [*gate.AUDIT_FLAGS, "-DFREAK_ARRAY_LIVE_LIMIT=1024", *flags,
                            *(gate.SANITIZER_FLAGS if sanitized else ())]
                gate.validate_flags(required, profile, sanitized)
                for index in range(len(required)):
                    with self.assertRaises(AssertionError):
                        gate.validate_flags(required[:index] + required[index + 1:], profile, sanitized)
                with self.assertRaises(AssertionError):
                    gate.validate_flags(required + ["-DNDEBUG"], profile, sanitized)

    def test_legacy_namespace_source_fence_rejects_expansion_or_missing_admission(self):
        source = (gate.ROOT / "freakc/runtime/freak_llvm_runtime.c").read_text()
        gate.namespace_source_guard(source)
        for old, new in (("#define FREAK_LLVM_MAX_ARRAYS 1024", "#define FREAK_LLVM_MAX_ARRAYS 2048"),
                         ("if (handle < 0) return -1;", "if (handle == -1) return -1;"),
                         ("slot >= freak_llvm_array_count", "slot > freak_llvm_array_count"),
                         ("freak_llvm_array_count >= FREAK_LLVM_MAX_ARRAYS", "freak_llvm_array_count > FREAK_LLVM_MAX_ARRAYS")):
            self.assertIn(old, source)
            start = 0 if old.startswith("#define") else source.index("static int64_t freak_llvm_array_slot_for_handle(")
            changed = source[:start] + source[start:].replace(old, new, 1)
            with self.subTest(mutation=old), self.assertRaises(AssertionError):
                gate.namespace_source_guard(changed)

    def test_runner_central_budgets_and_raw_channels_retained(self):
        result = self.result(stdout="hello\x00world\n", stderr="")
        guarded = mock.Mock(return_value=result)
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            runner = gate.Runner(SimpleNamespace(run_with_heartbeat=guarded), directory)
            for compiled, expected in ((False, (60, 64)), (True, (120, 1024))):
                self.assertIs(runner.run(["mock-tool", "argument"], "bounded job", compile_job=compiled), result)
                kwargs = guarded.call_args.kwargs
                self.assertEqual((kwargs["timeout_seconds"], kwargs["memory_limit_mb"]), expected)
                self.assertEqual(kwargs["output_limit_mb"], 8)
            self.assertTrue(any(path.read_bytes() == b"hello\x00world\n" for path in directory.glob("*.stdout")))

    def test_complete_guarded_driver_matrix_is_wired_and_tool_changes_fail_closed(self):
        # Assertions retain the load-time host even when Linux dispatch below
        # exercises sanitizer wiring. Windows CRT abort is 3; POSIX is -SIGABRT.
        host_abort_status = 3 if sys.platform == "win32" else -signal.SIGABRT
        for sanitized, change_tool in ((False, False), (True, False), (True, True)):
            with self.subTest(sanitized=sanitized, change_tool=change_tool), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp)
                clang = directory / "fake-clang"
                clang.write_bytes(b"process-free mocked tool image")
                calls = []

                def guarded(command, **kwargs):
                    calls.append((command, kwargs))
                    if "-o" in command:
                        artifact = Path(command[command.index("-o") + 1])
                        artifact.write_bytes(kwargs["label"].encode())
                        return self.result()
                    case = command[-1]
                    if case in gate.PROFILE_ROWS or case == "normal":
                        return self.result(stdout=gate.positive_stdout(case))
                    if case in gate.EXIT_CASES:
                        return self.result(1, stderr=gate.EXIT_CASES[case].encode())
                    if case in gate.ABORT_CASES:
                        return self.result(host_abort_status, stderr=f"FREAK: V4 word panic: {gate.ABORT_CASES[case]}\n".encode())
                    if case.startswith("sanitizer-"):
                        text = (b"ERROR: AddressSanitizer: heap-use-after-free\nSUMMARY: AddressSanitizer:\n"
                                if case.endswith("address") else
                                b"runtime error: signed integer overflow\nSUMMARY: UndefinedBehaviorSanitizer:\n")
                        return self.result(88, stderr=text)
                    kind = "C" if case == "audit-c-word" else "LLVM"
                    if change_tool and kwargs["label"] == "audit LLVM O3":
                        clang.write_bytes(b"mutated mocked tool image")
                    return self.result(87 if kind == "C" else 86,
                                       stderr=f"FREAK: {kind} ownership audit found 1 unreleased word allocation(s)\n".encode())

                report = {"sanitized": sanitized, "flags": {}, "production": [], "positives": [],
                          "rejections": [], "capabilities": []}
                args = SimpleNamespace(clang=str(clang), plain=not sanitized)
                with mock.patch.object(sys, "platform", "linux"), \
                        mock.patch.object(gate, "load_checks", return_value=SimpleNamespace(run_with_heartbeat=guarded)), \
                        gate.proof_environment(directory, sanitized) as prefix:
                    if change_tool:
                        with self.assertRaisesRegex(AssertionError, "identity changed"):
                            gate.run_gate(args, directory, report, prefix)
                        self.assertNotIn("final_conservation", report)
                    else:
                        gate.run_gate(args, directory, report, prefix)
                        self.assertTrue(report["final_conservation"])
                    self.assertFalse(prefix.exists())
                self.assertEqual(len(calls), 95 if sanitized else 93)
                for command, kwargs in calls:
                    self.assertEqual(kwargs["output_limit_mb"], 8)
                    expected = (120, 1024) if "-o" in command else (60, 64)
                    self.assertEqual((kwargs["timeout_seconds"], kwargs["memory_limit_mb"]), expected)

    def test_guarded_driver_matrix_with_windows_result_defaults(self):
        spec = importlib.util.spec_from_file_location("private_array_gate_windows_pure", _path)
        windows_gate = importlib.util.module_from_spec(spec)
        # Dependencies are already loaded on the real host; source-load only
        # the gate to capture Windows defaults without importing native _winapi.
        with mock.patch.object(sys, "platform", "win32"):
            exec(compile(_path.read_bytes(), str(_path), "exec"), windows_gate.__dict__)
            for case, diagnostic in windows_gate.ABORT_CASES.items():
                stderr = f"FREAK: V4 word panic: {diagnostic}\n".encode()
                windows_gate.assert_rejection(self.result(3, stderr=stderr), case)
                with self.assertRaises(AssertionError):
                    windows_gate.assert_rejection(self.result(-signal.SIGABRT, stderr=stderr), case)
            with mock.patch.dict(globals(), gate=windows_gate):
                self.test_complete_guarded_driver_matrix_is_wired_and_tool_changes_fail_closed()

    def test_runner_secondary_artifact_properties_preserve_primary(self):
        class Primary(RuntimeError):
            @property
            def output(self):
                raise MemoryError("secondary output attribution")

            @property
            def stderr(self):
                raise KeyboardInterrupt("secondary stderr attribution")

            def __str__(self):
                raise AssertionError("error formatting forbidden")

        primary = Primary()
        primary.__cause__ = ValueError("original cause")
        guarded = mock.Mock(side_effect=primary)
        with tempfile.TemporaryDirectory() as tmp:
            runner = gate.Runner(SimpleNamespace(run_with_heartbeat=guarded), Path(tmp))
            with self.assertRaises(Primary) as caught:
                runner.run(["mock-native"], "first cause")
            self.assertIs(caught.exception, primary)
            self.assertIs(caught.exception.__cause__, primary.__cause__)

    def test_environment_cleanup_preserves_primary_and_attempts_every_restore(self):
        names = ("ASAN_OPTIONS", "LSAN_OPTIONS", "UBSAN_OPTIONS", "PYTHONPYCACHEPREFIX", "PYTHONDONTWRITEBYTECODE")
        for primary_type in (RuntimeError, KeyboardInterrupt):
            for cleanup_type in (MemoryError, KeyboardInterrupt):
                with self.subTest(primary=primary_type.__name__, cleanup=cleanup_type.__name__), tempfile.TemporaryDirectory() as tmp:
                    primary = primary_type("body")
                    primary.__cause__ = ValueError("original cause")
                    secondary = cleanup_type("restore")
                    attempted = []
                    saved = {name: "saved-" + name for name in names}
                    class RestoreFault(dict):
                        def __setitem__(self, name, value):
                            if value == saved.get(name):
                                attempted.append(name)
                                if name == "ASAN_OPTIONS":
                                    raise secondary
                            super().__setitem__(name, value)
                    with mock.patch.object(gate.os, "environ", RestoreFault(saved)):
                        try:
                            with gate.proof_environment(Path(tmp), True):
                                raise primary
                        except BaseException as propagated:
                            self.assertIs(propagated, primary)
                            self.assertIs(propagated.__cause__, primary.__cause__)
                        else:
                            self.fail("body failure was swallowed")
                    self.assertEqual(attempted, list(names))
        # With successful body, the first cleanup failure remains primary while
        # every remaining independent restore is still attempted.
        for first_type in (MemoryError, KeyboardInterrupt):
            with self.subTest(success_body_first_cleanup=first_type.__name__), tempfile.TemporaryDirectory() as tmp:
                saved = {name: "saved-" + name for name in names}
                first, second = first_type("first restore"), MemoryError("later restore")
                first.__cause__ = ValueError("first cleanup cause")
                attempted = []
                class RestoreFault(dict):
                    def __setitem__(self, name, value):
                        if value == saved.get(name):
                            attempted.append(name)
                            if name == "ASAN_OPTIONS":
                                raise first
                            if name == "LSAN_OPTIONS":
                                raise second
                        super().__setitem__(name, value)
                with mock.patch.object(gate.os, "environ", RestoreFault(saved)):
                    try:
                        with gate.proof_environment(Path(tmp), True):
                            pass
                    except BaseException as propagated:
                        self.assertIs(propagated, first)
                        self.assertIs(propagated.__cause__, first.__cause__)
                    else:
                        self.fail("cleanup failure was swallowed")
                self.assertEqual(attempted, list(names))

    def test_cleanup_dispatch_setup_preserves_primary_and_remaining_restores(self):
        names = ("ASAN_OPTIONS", "LSAN_OPTIONS", "UBSAN_OPTIONS", "PYTHONPYCACHEPREFIX", "PYTHONDONTWRITEBYTECODE")
        for primary_type in (RuntimeError, KeyboardInterrupt):
            for secondary_type in (MemoryError, KeyboardInterrupt):
                with self.subTest(primary=primary_type.__name__, secondary=secondary_type.__name__), tempfile.TemporaryDirectory() as tmp:
                    primary, secondary = primary_type("body"), secondary_type("cleanup setup")
                    primary.__cause__ = ValueError("original cause")
                    before = {name: os.environ.get(name) for name in names}
                    old_prefix, old_write, old_trace = sys.pycache_prefix, sys.dont_write_bytecode, sys.gettrace()
                    tree = ast.parse(Path(gate.__file__).read_bytes())
                    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "proof_environment")
                    # Exact old1fd replay injects at its allocating local
                    # function definition; current source injects at the first
                    # protected dispatch entry, before any action executes.
                    nested = next((node for node in ast.walk(function) if isinstance(node, ast.FunctionDef) and node.name == "restore"), None)
                    triggered = []
                    def trace(frame, event, arg):
                        if frame.f_code.co_filename == gate.__file__ and not triggered:
                            old_boundary = nested is not None and event == "line" and frame.f_code.co_name == "proof_environment" and frame.f_lineno == nested.lineno
                            current_boundary = nested is None and event == "call" and frame.f_code.co_name == "restore_proof_environment"
                            if old_boundary or current_boundary:
                                triggered.append(frame.f_lineno)
                                raise secondary
                        return trace
                    try:
                        sys.settrace(trace)
                        try:
                            with gate.proof_environment(Path(tmp), True):
                                raise primary
                        except BaseException as propagated:
                            self.assertIs(propagated, primary)
                            self.assertIs(propagated.__cause__, primary.__cause__)
                        else:
                            self.fail("body failure was swallowed")
                        self.assertEqual(len(triggered), 1)
                        self.assertEqual({name: os.environ.get(name) for name in names}, before)
                        self.assertEqual(sys.dont_write_bytecode, old_write)
                    finally:
                        sys.settrace(old_trace)
                        sys.pycache_prefix, sys.dont_write_bytecode = old_prefix, old_write
                        for name, value in before.items():
                            if value is None:
                                os.environ.pop(name, None)
                            else:
                                os.environ[name] = value

    def test_each_guarded_job_rejects_transient_source_binary_and_selected_alias_drift(self):
        original_legacy = (gate.ROOT / "freakc/runtime/freak_llvm_runtime.c").read_bytes()
        for mutation in ("source", "binary", "alias"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                legacy = repo / "freakc/runtime/freak_llvm_runtime.c"
                legacy.parent.mkdir(parents=True)
                legacy.write_bytes(original_legacy)
                source = repo / "source.txt"
                source.write_bytes(b"frozen source")
                selected, image, replacement = (repo / name for name in ("selected-clang", "real-clang", "other-clang"))
                selected.write_bytes(b"simulated selected name")
                image.write_bytes(b"frozen compiler image")
                replacement.write_bytes(b"different compiler image")
                retargeted = False
                calls = []
                original_resolve = Path.resolve
                def resolve(path, *args, **kwargs):
                    if path == selected:
                        return replacement if retargeted else image
                    return original_resolve(path, *args, **kwargs)
                def guarded(command, **kwargs):
                    nonlocal retargeted
                    calls.append(command)
                    if "-o" in command:
                        Path(command[command.index("-o") + 1]).write_bytes(kwargs["label"].encode())
                        if len(calls) == 1 and mutation == "source":
                            source.write_bytes(b"source changed between compile jobs")
                        elif len(calls) == 2 and mutation == "source":
                            source.write_bytes(b"frozen source")
                        if len(calls) == 1 and mutation == "alias":
                            retargeted = True
                        return self.result()
                    case = command[-1]
                    if case == "normal" and mutation == "binary":
                        Path(command[0]).write_bytes(b"changed pressure executable")
                    elif case == "quota" and mutation == "binary":
                        Path(command[0]).write_bytes(b"compile pressure O0")
                    if case == "normal" or case in gate.PROFILE_ROWS:
                        return self.result(stdout=gate.positive_stdout(case))
                    if case in gate.EXIT_CASES:
                        return self.result(1, stderr=gate.EXIT_CASES[case].encode())
                    if case in gate.ABORT_CASES:
                        return self.result(-signal.SIGABRT, stderr=f"FREAK: V4 word panic: {gate.ABORT_CASES[case]}\n".encode())
                    kind = "C" if case == "audit-c-word" else "LLVM"
                    return self.result(87 if kind == "C" else 86,
                                       stderr=f"FREAK: {kind} ownership audit found 1 unreleased word allocation(s)\n".encode())
                report = {"sanitized": False, "flags": {}, "production": [], "positives": [],
                          "rejections": [], "capabilities": []}
                with mock.patch.object(sys, "platform", "linux"), mock.patch.object(gate, "ROOT", repo), \
                        mock.patch.object(gate, "head_identity", return_value="a" * 40), \
                        mock.patch.object(gate, "source_paths", return_value=(source, legacy)), \
                        mock.patch.object(Path, "resolve", resolve), \
                        mock.patch.object(gate, "load_checks", return_value=SimpleNamespace(run_with_heartbeat=guarded)), \
                        gate.proof_environment(repo, False) as prefix:
                    with self.assertRaisesRegex(AssertionError, "identity changed"):
                        gate.run_gate(SimpleNamespace(clang=str(selected), plain=True), repo, report, prefix)
                self.assertNotIn("final_conservation", report)
                self.assertLess(len(calls), 93, "transient corruption must stop before complete matrix")

    def test_environment_restored_after_cancellation_without_cache_writes(self):
        names = ("ASAN_OPTIONS", "LSAN_OPTIONS", "UBSAN_OPTIONS", "PYTHONPYCACHEPREFIX", "PYTHONDONTWRITEBYTECODE")
        before = {name: os.environ.get(name) for name in names}
        old_prefix, old_write = sys.pycache_prefix, sys.dont_write_bytecode
        with tempfile.TemporaryDirectory() as tmp:
            prefix = Path(tmp) / "unused-source-cache"
            with self.assertRaises(KeyboardInterrupt):
                with gate.proof_environment(Path(tmp), True) as actual:
                    self.assertEqual(actual, prefix)
                    self.assertEqual(os.environ["PYTHONPYCACHEPREFIX"], str(prefix))
                    self.assertEqual(os.environ["PYTHONDONTWRITEBYTECODE"], "1")
                    self.assertTrue(sys.dont_write_bytecode)
                    self.assertFalse(prefix.exists())
                    raise KeyboardInterrupt("cancel")
            self.assertFalse(prefix.exists())
        self.assertEqual(before, {name: os.environ.get(name) for name in names})
        self.assertEqual((sys.pycache_prefix, sys.dont_write_bytecode), (old_prefix, old_write))

    def test_source_forcing_check_module_never_reads_bytecode(self):
        with tempfile.TemporaryDirectory() as tmp:
            with gate.proof_environment(Path(tmp), False) as prefix:
                with mock.patch("importlib._bootstrap_external._compile_bytecode", side_effect=AssertionError("cached input forbidden")):
                    checks = gate.load_checks()
                self.assertTrue(callable(checks.run_with_heartbeat))
                self.assertFalse(prefix.exists())

    def test_success_publication_failure_never_prints_pass_and_preserves_first_cause(self):
        for primary in (MemoryError("publication"), KeyboardInterrupt("publication")):
            with tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp) / "fresh"
                output = io.StringIO()
                with mock.patch.object(sys, "argv", ["gate", "--plain", "--clang", "mock-clang", "--work", str(directory)]), \
                        mock.patch.object(gate, "run_gate"), \
                        mock.patch.object(gate, "publish", side_effect=[primary, MemoryError("recovery")]), redirect_stdout(output):
                    with self.assertRaises(type(primary)) as caught:
                        gate.main()
                self.assertIs(caught.exception, primary)
                self.assertNotIn("PASS", output.getvalue())

    def test_publication_drift_is_rechecked_before_any_final_pass(self):
        for changed_when in ("before-publication", "during-publication"):
            with self.subTest(phase=changed_when), tempfile.TemporaryDirectory() as tmp:
                source = Path(tmp) / "controlled-source"
                source.write_bytes(b"frozen source")
                digest = gate.sha(source)
                directory = Path(tmp) / "fresh"
                output = io.StringIO()
                class ReturnedIdentity:
                    def pin(self, **kwargs):
                        if gate.sha(source) != digest:
                            raise AssertionError("publication source identity changed")
                identity = ReturnedIdentity()
                def verified(*args):
                    if changed_when == "before-publication":
                        source.write_bytes(b"changed on environment restore boundary")
                    return identity
                def publisher(*args):
                    source.write_bytes(b"changed while publishing artifacts")
                with mock.patch.object(sys, "argv", ["gate", "--plain", "--clang", "mock-clang", "--work", str(directory)]), \
                        mock.patch.object(gate, "run_gate", side_effect=verified), \
                        mock.patch.object(gate, "publish", side_effect=publisher), redirect_stdout(output):
                    with self.assertRaisesRegex(AssertionError, "publication source identity changed"):
                        gate.main()
                self.assertNotIn("PASS", output.getvalue())

    def test_missing_clang_and_nonlinux_sanitizer_are_explicit_failures(self):
        for argv, platform in ((["gate"], "linux"), (["gate", "--clang", "mock-clang"], "win32")):
            with mock.patch.object(sys, "argv", argv), mock.patch.object(sys, "platform", platform), \
                    mock.patch.object(gate.shutil, "which", return_value=None), \
                    mock.patch.dict(os.environ, {}, clear=True), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as caught:
                    gate.main()
                self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
