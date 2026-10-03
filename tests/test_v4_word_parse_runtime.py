"""Process-free adversarial oracles for the mandatory checked-parser matrix."""
from __future__ import annotations

import argparse
import ast
import copy
import itertools
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import unittest
from unittest import mock

from tests import v4_word_parse_runtime as gate


class WordParseOracleTests(unittest.TestCase):
    def setUp(self):
        self.traps = []
        for name in ("Popen", "run", "call", "check_call", "check_output"):
            patch = mock.patch.object(subprocess, name, side_effect=AssertionError("native process forbidden in pure tests"))
            self.traps.append(patch)
            patch.start()

    def tearDown(self):
        for patch in reversed(self.traps):
            patch.stop()

    @staticmethod
    def result(status=0, stdout=b"", stderr=b""):
        return subprocess.CompletedProcess(["mock-probe"], status, stdout, stderr)

    def test_reference_int64_boundaries_and_grammar(self):
        valid = {b"0": 0, b"-0": 0, b"+0": 0, b"00042": 42, b"-007": -7,
                 b"9223372036854775807": 2**63 - 1, b"-9223372036854775808": -(2**63),
                 b"+0009223372036854775807": 2**63 - 1}
        for data, value in valid.items():
            self.assertEqual(gate.reference_parse(data), (1, value))
        for data in (b"", b"+", b"-", b"+-1", b" 0", b"0 ", b"0\n", b"0\t", b"0\r",
                     b"12junk", b"12\0junk", b"1.0", b"1e2", b"0x1", b"1_0",
                     b"9223372036854775808", b"-9223372036854775809", "１２".encode(),
                     "١".encode(), "42😀".encode()):
            self.assertEqual(gate.reference_parse(data), (0, 0), data)
        self.assertEqual(gate.reference_parse(b"0" * 262143 + b"7"), (1, 7))
        self.assertEqual(gate.reference_parse(b"9" * 262144), (0, 0))

    def test_reference_small_inputs_against_independent_regex_and_python_int(self):
        for length in range(5):
            for values in itertools.product(b"01+-x\x00 ", repeat=length):
                data = bytes(values)
                matched = re.fullmatch(rb"[+-]?[0-9]+", data)
                expected = (1, int(data)) if matched else (0, 0)
                self.assertEqual(gate.reference_parse(data), expected, data)

    def test_native_probe_static_cases_match_independent_input_book(self):
        source = (gate.ROOT / "tests/v4_word_parse_runtime_probe.c").read_text()
        rows = re.findall(r'CASE\("([^"]+)",\s*((?:"(?:[^"\\]|\\.)*"\s*)+)\);', source)
        actual = {label: ast.literal_eval(text).encode("latin1") for label, text in rows}
        expected = dict(gate.semantic_cases())
        self.assertEqual(actual, {name: data for name, data in expected.items() if not name.startswith("large-")})
        self.assertEqual(len(expected), 39)
        self.assertEqual(source.count('probe_case("large-'), 3)

    def test_complete_success_exact_output_all_platforms(self):
        expected = gate.expected_stdout()
        for platform in ("linux", "darwin", "win32"):
            gate.assert_success(self.result(stdout=expected), platform=platform)
            if platform == "win32":
                gate.assert_success(self.result(stdout=expected.replace(b"\n", b"\r\n")), platform=platform)
            for stdout in (b"", expected[:-1], expected + b"extra\n", expected.replace(b":minimum:1:-9223372036854775808", b":minimum:0:0"),
                           expected.replace(b":nul-suffix:0:0", b":nul-suffix:1:12"), expected.replace(b":positive-overflow:0:0", b":positive-overflow:1:9223372036854775807"),
                           expected.replace(b":leading-zeros:1:42", b":leading-zeros:0:0"), expected.replace(b"borrow-and-status=ok\n", b""),
                           expected.replace(b"legacy-lenient=ok\n", b"")):
                with self.subTest(platform=platform, stdout=stdout[-100:]), self.assertRaises(AssertionError):
                    gate.assert_success(self.result(stdout=stdout), platform=platform)
            for code in (1, 3, 85, 86, 87, 88, -signal.SIGABRT, -signal.SIGSEGV):
                with self.assertRaises(AssertionError):
                    gate.assert_success(self.result(code, expected), platform=platform)
            for stderr in (b"ERROR: AddressSanitizer\n", b"runtime error: overflow\n", b"ownership audit\n", b"\n"):
                with self.assertRaises(AssertionError):
                    gate.assert_success(self.result(stdout=expected, stderr=stderr), platform=platform)
        for platform in ("linux", "darwin"):
            with self.assertRaises(AssertionError):
                gate.assert_success(self.result(stdout=expected.replace(b"\n", b"\r\n")), platform=platform)

    def test_fatal_exact_reason_status_and_channels_all_platforms(self):
        for platform in ("linux", "darwin", "win32"):
            code = 3 if platform == "win32" else -signal.SIGABRT
            for reason in set(gate.rejection_cases().values()):
                diagnostic = f"FREAK: V4 word panic: {reason}\n".encode()
                gate.assert_named_panic(self.result(code, stderr=diagnostic), reason, platform=platform)
                if platform == "win32":
                    gate.assert_named_panic(self.result(code, stderr=diagnostic.replace(b"\n", b"\r\n")), reason, platform=platform)
                else:
                    with self.assertRaises(AssertionError):
                        gate.assert_named_panic(self.result(code, stderr=diagnostic.replace(b"\n", b"\r\n")), reason, platform=platform)
                for bad in ({0, 1, 2, 3, 85, 86, 87, 88, 90, 98, 99, -signal.SIGABRT, -signal.SIGSEGV} - {code}):
                    with self.assertRaises(AssertionError):
                        gate.assert_named_panic(self.result(bad, stderr=diagnostic), reason, platform=platform)
                for stderr in (b"", diagnostic[:-1], diagnostic * 2, b"FREAK: V4 word panic: wrong\n",
                               diagnostic + b"ERROR: AddressSanitizer\n", diagnostic + b"ownership audit\n"):
                    with self.assertRaises(AssertionError):
                        gate.assert_named_panic(self.result(code, stderr=stderr), reason, platform=platform)
                for stdout in (b"\n", b"\0", b"returned"):
                    with self.assertRaises(AssertionError):
                        gate.assert_named_panic(self.result(code, stdout, diagnostic), reason, platform=platform)

    def test_audit_capability_rejects_wrong_exit_or_sanitizer(self):
        for platform in ("linux", "darwin", "win32"):
            for kind, status in (("C", 87), ("LLVM", 86)):
                diagnostic = f"FREAK: {kind} ownership audit found 1 unreleased word allocation(s)\n".encode()
                gate.assert_audit(self.result(status, stderr=diagnostic), kind, platform=platform)
                for code in (0, 1, 3, 88, -signal.SIGABRT):
                    with self.assertRaises(AssertionError):
                        gate.assert_audit(self.result(code, stderr=diagnostic), kind, platform=platform)
                for stderr in (diagnostic[:-1], diagnostic + b"ERROR: LeakSanitizer\n", diagnostic.replace(b"1 unreleased", b"2 unreleased")):
                    with self.assertRaises(AssertionError):
                        gate.assert_audit(self.result(status, stderr=stderr), kind, platform=platform)
        with self.assertRaises(AssertionError):
            gate.assert_audit(self.result(), "unknown")

    def test_sanitizer_capability_requires_real_kind_report_and_exit(self):
        reports = {
            "address": b"ERROR: AddressSanitizer: heap-use-after-free\nSUMMARY: AddressSanitizer: heap-use-after-free\n",
            "undefined": b"runtime error: signed integer overflow\nSUMMARY: UndefinedBehaviorSanitizer: overflow\n",
        }
        for kind, diagnostic in reports.items():
            gate.assert_sanitizer(self.result(88, stderr=diagnostic), kind)
            for code in (0, 1, 3, 85, 86, 87, -signal.SIGABRT, -signal.SIGSEGV):
                with self.assertRaises(AssertionError):
                    gate.assert_sanitizer(self.result(code, stderr=diagnostic), kind)
            for stderr in (b"", diagnostic.split(b"SUMMARY:")[0], reports["undefined" if kind == "address" else "address"],
                           diagnostic + b"ownership audit", diagnostic + b"LeakSanitizer", diagnostic + b"FREAK: V4 word panic:"):
                with self.assertRaises(AssertionError):
                    gate.assert_sanitizer(self.result(88, stderr=stderr), kind)
            with self.assertRaises(AssertionError):
                gate.assert_sanitizer(self.result(88, b"bad", diagnostic), kind)
        with self.assertRaises(AssertionError):
            gate.assert_sanitizer(self.result(), "unknown")

    @staticmethod
    def legacy_stdout():
        return gate.expected_stdout().replace(b":empty:0:0", b":empty:1:0").replace(
            b":suffix-junk:0:0", b":suffix-junk:1:12").replace(b":nul-suffix:0:0", b":nul-suffix:1:12").replace(
            b":positive-overflow:0:0", b":positive-overflow:1:9223372036854775807").replace(
            b":negative-overflow:0:0", b":negative-overflow:1:-9223372036854775808")

    def test_legacy_control_requires_full_ordinary_wrong_results(self):
        stdout = self.legacy_stdout()
        for platform in ("linux", "darwin", "win32"):
            gate.assert_legacy_control(self.result(stdout=stdout), platform=platform)
            with self.assertRaises(AssertionError):
                gate.assert_success(self.result(stdout=stdout), platform=platform)
            for bad in (b"", stdout[:-1], stdout + b"extra\n", gate.expected_stdout(),
                        stdout.replace(b":nul-suffix:1:12", b":nul-suffix:0:0")):
                with self.assertRaises(AssertionError):
                    gate.assert_legacy_control(self.result(stdout=bad), platform=platform)
            for code in (1, 3, 86, 87, 88, -signal.SIGABRT, -signal.SIGSEGV):
                with self.assertRaises(AssertionError):
                    gate.assert_legacy_control(self.result(code, stdout), platform=platform)
            with self.assertRaises(AssertionError):
                gate.assert_legacy_control(self.result(stdout=stdout, stderr=b"sanitizer"), platform=platform)

    def test_private_boundary_inventory_has_32_and_64_bit_metadata_and_slot_poison(self):
        small, large = gate.rejection_cases(4), gate.rejection_cases(8)
        self.assertEqual(set(large) - set(small), {"signed-overflow"})
        self.assertEqual(len(small), 29)
        self.assertEqual(len(large), 30)
        for name in ("size-max", "utf8-after-overflow", "utf8-after-junk", "stale", "null"):
            self.assertIn(name, small)
        for name in ("null-tag", "null-value", "null-both", "alias-slots"):
            self.assertEqual(small[name], small[name + "-poison"])

    def test_flags_cannot_lose_audits_sanitizers_resource_limit_or_assertions(self):
        flags = [*gate.AUDIT_FLAGS, gate.ARRAY_FLAG, *gate.SANITIZER_FLAGS]
        gate.validate_build_flags(flags, True)
        for flag in flags:
            with self.assertRaises(AssertionError):
                gate.validate_build_flags([item for item in flags if item != flag], True)
        gate.validate_build_flags([*gate.AUDIT_FLAGS, gate.ARRAY_FLAG], False)
        with self.assertRaises(AssertionError):
            gate.validate_build_flags([*flags, "-DNDEBUG"], True)

    def test_sanitizer_environment_restores_prior_settings(self):
        original = {name: "inherited" for name in ("ASAN_OPTIONS", "LSAN_OPTIONS", "UBSAN_OPTIONS")}
        with mock.patch.dict(os.environ, original):
            with gate.sanitizer_environment(True):
                self.assertIn("detect_leaks=1", os.environ["ASAN_OPTIONS"])
                self.assertIn("exitcode=88", os.environ["UBSAN_OPTIONS"])
                self.assertNotIn("LSAN_OPTIONS", os.environ)
            for name in original:
                self.assertEqual(os.environ[name], "inherited")
            with self.assertRaises(RuntimeError):
                with gate.sanitizer_environment(False):
                    self.assertTrue(all(name not in os.environ for name in original))
                    raise RuntimeError("test exception")
            for name in original:
                self.assertEqual(os.environ[name], "inherited")

    @staticmethod
    def completed_report(sanitized):
        return {"sanitized": sanitized,
                "matrices": [{"opt": opt, "variant": variant, "semantics": 39}
                             for opt in (0, 2, 3) for variant in ("direct", "observer")],
                "rejections": [{"opt": opt, "variant": variant, "case": case}
                               for opt in (0, 2, 3) for variant in ("direct", "observer")
                               for case in gate.rejection_cases()],
                "capabilities": [f"audit-{kind}-O{opt}" for opt in (0, 2, 3) for kind in ("C", "LLVM")]
                                + [f"observer-O{opt}" for opt in (0, 2, 3)]
                                + ["legacy-oracle-negative"]
                                + (["sanitizer-address", "sanitizer-undefined"] if sanitized else [])}

    def test_missing_duplicate_wrong_matrix_or_capabilities_cannot_pass(self):
        for sanitized in (True, False):
            report = self.completed_report(sanitized)
            gate.validate_completion(report, sanitized)
            for field in ("matrices", "rejections", "capabilities"):
                for mutation in ("missing", "duplicate", "replaced"):
                    bad = copy.deepcopy(report)
                    if mutation == "missing":
                        bad[field].pop()
                    elif mutation == "duplicate":
                        bad[field].append(copy.deepcopy(bad[field][0]))
                    else:
                        bad[field][-1] = copy.deepcopy(bad[field][0])
                    with self.subTest(field=field, mutation=mutation), self.assertRaises(AssertionError):
                        gate.validate_completion(bad, sanitized)
            bad = copy.deepcopy(report)
            bad["matrices"][0]["semantics"] = 38
            with self.assertRaises(AssertionError):
                gate.validate_completion(bad, sanitized)
            with self.assertRaises(AssertionError):
                gate.validate_completion(report, not sanitized)
        with mock.patch.object(gate, "OPTS", (0, 2)):
            with self.assertRaises(AssertionError):
                gate.validate_completion(self.completed_report(True), True)

    def test_full_driver_matrix_with_mocked_processes_and_fixed_budgets(self):
        for plain in (False, True):
            with tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                clang = directory / "clang.mock"
                clang.write_bytes(b"mock compiler image")
                calls = []

                def run(command, **keywords):
                    calls.append((command, keywords))
                    compiler = command[0] == str(clang)
                    self.assertEqual(keywords["timeout_seconds"], 120 if compiler else 20)
                    self.assertEqual(keywords["memory_limit_mb"], 1024 if compiler else 64)
                    if compiler:
                        gate.validate_build_flags(command, not plain)
                        Path(command[command.index("-o") + 1]).write_bytes(b"mock binary")
                        return self.result()
                    if len(command) == 1:
                        if "legacy-negative" in command[0]:
                            return self.result(stdout=self.legacy_stdout())
                        return self.result(stdout=gate.expected_stdout())
                    mode = command[1]
                    if mode in gate.rejection_cases():
                        return self.result(-signal.SIGABRT, stderr=("FREAK: V4 word panic: " + gate.rejection_cases()[mode] + "\n").encode())
                    if mode.startswith("audit-"):
                        kind = mode[6:]
                        return self.result(87 if kind == "C" else 86, stderr=f"FREAK: {kind} ownership audit found 1 unreleased word allocation(s)\n".encode())
                    if mode == "cap-observer":
                        return self.result(90, stderr=b"word-parse-probe: parser allocated or freed storage\n")
                    if mode == "cap-address":
                        return self.result(88, stderr=b"ERROR: AddressSanitizer: heap-use-after-free\nSUMMARY: AddressSanitizer:\n")
                    if mode == "cap-undefined":
                        return self.result(88, stderr=b"runtime error: signed integer overflow\nSUMMARY: UndefinedBehaviorSanitizer:\n")
                    self.fail(f"unknown mock command {command}")

                checks = mock.Mock()
                checks.run_with_heartbeat.side_effect = run
                report = {"sanitized": not plain, "flags": {}, "matrices": [], "rejections": [], "capabilities": []}
                with mock.patch.object(gate, "load_checks", return_value=checks), mock.patch.object(gate.sys, "platform", "linux"):
                    gate.run_gate(argparse.Namespace(clang=str(clang), plain=plain), directory, report)
                gate.validate_completion(report, not plain)
                self.assertEqual(sum("-o" in command for command, _ in calls), 10)
                self.assertEqual(len(report["rejections"]), 180)
                self.assertEqual(len(report["capabilities"]), 10 if plain else 12)

    def test_runner_forwards_fixed_budgets_and_preserves_guard_failure_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            checks = mock.Mock()
            checks.run_with_heartbeat.return_value = self.result(stdout="output", stderr="")
            runner = gate.Runner(checks, Path(temporary))
            runner.run(["clang", "-c"], "compile", compile=True)
            self.assertEqual(checks.run_with_heartbeat.call_args.kwargs["timeout_seconds"], 120)
            self.assertEqual(checks.run_with_heartbeat.call_args.kwargs["memory_limit_mb"], 1024)
            runner.run(["probe"], "run")
            self.assertEqual(checks.run_with_heartbeat.call_args.kwargs["timeout_seconds"], 20)
            self.assertEqual(checks.run_with_heartbeat.call_args.kwargs["memory_limit_mb"], 64)
            error = subprocess.TimeoutExpired(["probe"], 20, output=b"last stdout", stderr=b"last stderr")
            checks.run_with_heartbeat.side_effect = error
            with self.assertRaises(subprocess.TimeoutExpired) as caught:
                runner.run(["probe"], "failed")
            self.assertIs(caught.exception, error)
            self.assertEqual((Path(temporary) / "003-failed.stdout").read_bytes(), b"last stdout")
            self.assertEqual((Path(temporary) / "003-failed.stderr").read_bytes(), b"last stderr")

    def test_missing_clang_and_existing_work_directory_are_failures(self):
        with mock.patch.object(gate.sys, "argv", ["gate", "--clang", ""]):
            with self.assertRaises(SystemExit) as caught:
                gate.main()
            self.assertEqual(caught.exception.code, 2)
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.object(gate.sys, "argv", ["gate", "--plain", "--clang", "mock", "--work", temporary]):
                with self.assertRaises(FileExistsError):
                    gate.main()
        with mock.patch.object(gate.sys, "argv", ["gate", "--clang", "mock"]), mock.patch.object(gate.sys, "platform", "win32"), mock.patch.object(gate.shutil, "which", return_value="mock"):
            with self.assertRaises(SystemExit) as caught:
                gate.main()
            self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
