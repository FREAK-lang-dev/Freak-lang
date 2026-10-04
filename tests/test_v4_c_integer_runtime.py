"""Process-free checks for the checked32 runtime's independent gate oracles."""
from copy import deepcopy
from contextlib import ExitStack
import ast
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
NAME = "checked32_runtime_oracles_under_test"
gate = types.ModuleType(NAME)
gate.__file__ = str(ROOT / "tests/v4_c_integer_runtime.py")
sys.modules[NAME] = gate
exec(compile(Path(gate.__file__).read_bytes(), gate.__file__, "exec"), gate.__dict__)


def capability(kind="overflow"):
    detail = ("signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'"
              if kind == "overflow" else
              "division of -2147483648 by -1 cannot be represented in type 'int'")
    return {"status": 88, "stdout": "", "stderr":
            "probe.c:7:11: runtime error: " + detail + "\n"
            "SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior probe.c:7:11 in \n"}


def synthetic_report(sanitize=True, host="linux"):
    cases = gate.load_vectors()
    report = {"complete": True, "scope": "checked32 C helper prerequisite; no V4 C-width admission",
              "platform": host, "sanitized": sanitize,
              "source_hashes": {name: "a" * 64 for name in (*gate.OWNED_SOURCE_NAMES, gate.GUARD_SOURCE_NAME)},
              "compiler": {"sha256": "b" * 64, "target": "x86_64-pc-linux-gnu",
                           "selected": "/metadata/compiler-alias", "path": "/metadata/compiler"},
              "final_selected_compiler": "/metadata/compiler",
              "final_compiler_sha256": "b" * 64, "matrices": []}
    report["final_source_hashes"] = dict(report["source_hashes"])
    report["final_frozen_source_hashes"] = dict(report["source_hashes"])
    report["binary_hashes"] = {f"/metadata/O{opt}": "c" * 64 for opt in gate.OPTS}
    report["final_binary_hashes"] = dict(report["binary_hashes"])
    for opt in gate.OPTS:
        report["matrices"].append({"optimization": opt, "flags": gate.build_flags(opt, sanitize),
                                  "binary_sha256": "c" * 64, "binary_path": f"/metadata/O{opt}",
                                  "cases": [{"id": c.id, "helper": c.helper, "actual": gate.expected(c)} for c in cases],
                                  "invalid_arguments": [{"argv": list(argv), "actual": {"status": 2, "stdout": "", "stderr": ""}}
                                                        for argv in gate.INVALID_ARGUMENTS],
                                  "capabilities": [{"kind": kind, "actual": capability(kind)} for kind in gate.CAPABILITIES]
                                  if sanitize else []})
    return report


class Checked32Oracles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = gate.load_vectors()

    def test_frozen58_math_and_all16_success_failure_families(self):
        self.assertEqual(len(self.cases), 58)
        counts = {status: [c for c in self.cases if gate.expected(c)["status"] == status] for status in (0, 1)}
        self.assertEqual([len(counts[0]), len(counts[1])], [29, 29])
        self.assertEqual({c.helper for c in counts[0]}, {c.helper for c in counts[1]})
        self.assertEqual(len({c.helper for c in self.cases}), 16)

    def test_division_truncates_and_remainder_keeps_numerator_sign(self):
        self.assertEqual(gate.expected(gate.Case("quotient", "i32", "div", -7, 2)),
                         {"status": 0, "stdout": "-3\n", "stderr": ""})
        self.assertEqual(gate.expected(gate.Case("remainder", "i32", "mod", -7, 2)),
                         {"status": 0, "stdout": "-1\n", "stderr": ""})
        self.assertEqual(gate.expected(gate.Case("remainder", "i32", "mod", 7, -2))["stdout"], "1\n")

    def test_signed_minimum_division_and_remainder_both_fail(self):
        for op, label in (("div", "division"), ("mod", "remainder")):
            self.assertEqual(gate.expected(gate.Case("minimum", "i32", op, -(1 << 31), -1)),
                             {"status": 1, "stdout": "", "stderr": f"FREAK V4: i32 {label} overflow\n"})

    def test_all_zero_divisors_fail_with_exact_operation_diagnostic(self):
        for kind in ("i32", "u32"):
            for op, label in (("div", "division"), ("mod", "remainder")):
                self.assertEqual(gate.expected(gate.Case("zero", kind, op, 0, 0)),
                                 {"status": 1, "stdout": "", "stderr": f"FREAK V4: {kind} {label} by zero\n"})

    def test_unsigned_maximum_product_and_sign_conversion_are_checked(self):
        maximum = (1 << 32) - 1
        self.assertEqual(maximum * maximum, 18446744065119617025)
        self.assertLess(maximum * maximum, (1 << 64) - 1)
        self.assertEqual(gate.expected(gate.Case("product", "u32", "mul", maximum, maximum))["stderr"],
                         "FREAK V4: u32 multiplication overflow\n")
        self.assertEqual(gate.expected(gate.Case("sign", "i32", "from-uint", maximum))["stderr"],
                         "FREAK V4: uint to i32 conversion out of range\n")
        self.assertEqual(gate.expected(gate.Case("sign", "u32", "from-int", -1))["stderr"],
                         "FREAK V4: int to u32 conversion out of range\n")

    def test_arithmetic_and_conversion_input_types_are_exact(self):
        invalid = [gate.Case("unknown", "i32", "mystery", 0), gate.Case("boolean", "i32", "neg", True),
                   gate.Case("arity", "i32", "add", 1), gate.Case("arity", "i32", "neg", 1, 0),
                   gate.Case("wide", "i32", "add", 1 << 31, 0),
                   gate.Case("wide", "u32", "from-uint", 1 << 64)]
        for case in invalid:
            with self.subTest(case=case), self.assertRaises(gate.GateError):
                gate.expected(case)

    def test_native_oracle_rejects_status_and_channel_drift(self):
        for case in (self.cases[0], next(c for c in self.cases if gate.expected(c)["status"] == 1)):
            wanted = gate.expected(case)
            gate.validate_native(wanted, case, "linux")
            mutations = [dict(wanted, status=0 if wanted["status"] else 1), dict(wanted, status=True),
                         dict(wanted, stdout=wanted["stdout"] + "extra\n"),
                         dict(wanted, stderr=wanted["stderr"] + "extra\n"),
                         dict(wanted, stdout=wanted["stdout"].rstrip("\n")) if wanted["stdout"] else dict(wanted, stdout="0\n")]
            if wanted["stderr"]:
                mutations.append(dict(wanted, stderr=wanted["stderr"].rstrip("\n")))
            for actual in mutations:
                with self.subTest(case=case.id, actual=actual), self.assertRaises(gate.GateError):
                    gate.validate_native(actual, case, "linux")

    def test_windows_normalizes_only_crlf(self):
        case = next(c for c in self.cases if gate.expected(c)["status"] == 1)
        actual = dict(gate.expected(case), stderr=gate.expected(case)["stderr"].replace("\n", "\r\n"))
        gate.validate_native(actual, case, "win32")
        with self.assertRaises(gate.GateError):
            gate.validate_native(actual, case, "linux")
        for bad in (actual["stderr"] + "\r\n", actual["stderr"].replace("\r\n", "\r")):
            with self.assertRaises(gate.GateError):
                gate.validate_native(dict(actual, stderr=bad), case, "win32")

    def test_real_ubsan_capability_requires_both_diagnostics_and_exact_status(self):
        for kind in gate.CAPABILITIES:
            correct = capability(kind)
            gate.validate_capability(correct, kind)
            bad = [dict(correct, status=0), dict(correct, status=1), dict(correct, status=True),
                   dict(correct, stdout="0\n"), dict(correct, stderr=""),
                   dict(correct, stderr=correct["stderr"].replace("SUMMARY: UndefinedBehaviorSanitizer:", "summary missing")),
                   dict(correct, stderr=correct["stderr"].replace("runtime error:", "not an error:")),
                   dict(correct, stderr="FREAK V4: " + correct["stderr"])]
            for actual in bad:
                with self.subTest(kind=kind, actual=actual), self.assertRaises(gate.GateError):
                    gate.validate_capability(actual, kind)

    def test_plain_and_sanitized_reports_are_distinct_complete_matrices(self):
        for sanitize in (False, True):
            gate.validate_report(synthetic_report(sanitize), self.cases, sanitize)
        for host in ("darwin", "win32"):
            gate.validate_report(synthetic_report(False, host), self.cases, False)
            with self.assertRaises(gate.GateError):
                gate.validate_report(synthetic_report(True, host), self.cases, True)

    def test_report_rejects_incomplete_cases_flags_capabilities_or_conservation(self):
        good = synthetic_report()
        bad_reports = []
        changed = deepcopy(good); changed["complete"] = False; bad_reports.append(changed)
        changed = deepcopy(good); changed["matrices"].pop(); bad_reports.append(changed)
        changed = deepcopy(good); changed["matrices"][2]["optimization"] = 2; bad_reports.append(changed)
        changed = deepcopy(good); changed["matrices"][0]["cases"].pop(); bad_reports.append(changed)
        changed = deepcopy(good); changed["matrices"][0]["cases"].reverse(); bad_reports.append(changed)
        changed = deepcopy(good); changed["matrices"][0]["flags"].remove("-fsanitize=undefined"); bad_reports.append(changed)
        changed = deepcopy(good); changed["matrices"][0]["capabilities"].pop(); bad_reports.append(changed)
        changed = deepcopy(good); changed["matrices"][0]["invalid_arguments"].pop(); bad_reports.append(changed)
        changed = deepcopy(good); changed["final_source_hashes"].pop(gate.GUARD_SOURCE_NAME); bad_reports.append(changed)
        changed = deepcopy(good); changed["final_frozen_source_hashes"].pop(gate.GUARD_SOURCE_NAME); bad_reports.append(changed)
        changed = deepcopy(good); changed["final_compiler_sha256"] = "d" * 64; bad_reports.append(changed)
        changed = deepcopy(good); changed["final_selected_compiler"] = "/changed"; bad_reports.append(changed)
        changed = deepcopy(good); changed["compiler"].pop("selected"); bad_reports.append(changed)
        changed = deepcopy(good); changed["final_binary_hashes"]["/metadata/O0"] = "d" * 64; bad_reports.append(changed)
        changed = deepcopy(good); changed["matrices"][0]["binary_path"] = "/metadata/unknown"; bad_reports.append(changed)
        changed = deepcopy(good); changed["matrices"][0]["cases"][0]["actual"]["stderr"] = "unexpected\n"; bad_reports.append(changed)
        for index, report in enumerate(bad_reports):
            with self.subTest(index=index), self.assertRaises(gate.GateError):
                gate.validate_report(report, self.cases, True)

    def test_frozen_vectors_reject_duplicate_bad_or_missing_rows(self):
        good = json.loads(gate.VECTOR_PATH.read_text())
        malformed = []
        bad = deepcopy(good); bad["cases"][1]["id"] = bad["cases"][0]["id"]; malformed.append(bad)
        bad = deepcopy(good); bad["cases"][0]["expected"]["stdout"] = "wrong\n"; malformed.append(bad)
        bad = deepcopy(good); bad["cases"].pop(); malformed.append(bad)
        bad = deepcopy(good); bad["schema"] = True; malformed.append(bad)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bad.json"
            for bad in malformed:
                path.write_text(json.dumps(bad))
                with self.assertRaises(gate.GateError):
                    gate.load_vectors(path)

    def test_runtime_header_freezes_exact16_prototypes_and_diagnostics(self):
        header = (ROOT / "freakc/runtime/freak_v4_c_integer_runtime.h").read_text()
        source = (ROOT / "freakc/runtime/freak_v4_c_integer_runtime.c").read_text()
        prototypes = re.findall(r"^(int32_t|uint32_t) (freak_v4_[iu]32_[a-z_]+)\(([^\n]*)\);$", header, re.M)
        self.assertEqual(len(prototypes), 16)
        self.assertEqual({name for _, name, _ in prototypes}, {c.helper for c in self.cases})
        for result, name, args in prototypes:
            self.assertEqual(result, "int32_t" if "_i32_" in name else "uint32_t")
            if name.endswith("_from_int"):
                self.assertEqual(args, "int64_t value")
            elif name.endswith("_from_uint"):
                self.assertEqual(args, "uint64_t value")
            elif name.endswith("_neg"):
                self.assertEqual(args, result + " value")
            else:
                self.assertEqual(args, result + " lhs, " + result + " rhs")
        diagnostics = {"FREAK V4: " + reason + "\n" for reason in re.findall(r'freak_v4_c_integer_fail\("([^"\n]+)"\)', source)}
        expected = {gate.expected(c)["stderr"] for c in self.cases if gate.expected(c)["status"] == 1}
        self.assertEqual(len(diagnostics), 18)
        self.assertEqual(diagnostics, expected)

    def test_runner_uses_central_bounds_and_retains_partial_failure(self):
        class FakeGuard:
            def run_with_heartbeat(self, argv, **kwargs):
                self.received = (argv, kwargs)
                raise subprocess.TimeoutExpired(argv, kwargs["timeout_seconds"], output=b"partial\n", stderr=b"failed\n")
        fake = FakeGuard()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            runner = gate.Runner(fake, directory)
            with self.assertRaises(subprocess.TimeoutExpired):
                runner.run(["fake-child"], "bounded")
            self.assertEqual(fake.received[1], {"label": "bounded", "timeout_seconds": 10,
                                                "memory_limit_mb": 64, "output_limit_mb": 1})
            record = json.loads((directory / "001-bounded.command.json").read_text())
            self.assertEqual(record["status"], "raised")
            self.assertEqual((directory / "001-bounded.stdout").read_bytes(), b"partial\n")
            self.assertEqual((directory / "001-bounded.stderr").read_bytes(), b"failed\n")

    def test_sanitizer_environment_is_clean_and_restored(self):
        names = ("ASAN_OPTIONS", "LSAN_OPTIONS", "UBSAN_OPTIONS")
        previous = {name: os.environ.get(name) for name in names}
        try:
            for name in names:
                os.environ[name] = "disabled-by-caller"
            with gate.sanitizer_environment(True):
                self.assertNotIn("ASAN_OPTIONS", os.environ)
                self.assertNotIn("LSAN_OPTIONS", os.environ)
                self.assertEqual(os.environ["UBSAN_OPTIONS"], "halt_on_error=1:print_stacktrace=1:exitcode=88")
            self.assertTrue(all(os.environ[name] == "disabled-by-caller" for name in names))
            with gate.sanitizer_environment(False):
                self.assertTrue(all(name not in os.environ for name in names))
        finally:
            for name, value in previous.items():
                if value is None: os.environ.pop(name, None)
                else: os.environ[name] = value


class Checked32FailureControls(unittest.TestCase):
    """Real driver control flow with non-executable fixtures; no native proof."""
    def setUp(self):
        self.stack = ExitStack()
        self.process_attempts = {name: 0 for name in ("Popen", "run", "call", "check_call", "check_output")}
        for name in self.process_attempts:
            def forbidden(*args, name=name, **kwargs):
                self.process_attempts[name] += 1
                raise AssertionError("process API forbidden: " + name)
            self.stack.enter_context(patch.object(subprocess, name, forbidden))
        self.temporary = self.stack.enter_context(tempfile.TemporaryDirectory())
        # The real driver resolves both its compiler and evidence directory.
        # Match that identity even when a host temp path uses an alias.
        self.directory = Path(self.temporary).resolve()

    def tearDown(self):
        self.stack.close()
        self.assertFalse(any(self.process_attempts.values()), self.process_attempts)
        self.assertNotIn("v4_c_integer_runtime_checks", sys.modules)

    def fixture(self):
        root, frozen = self.directory / "original", self.directory / "frozen"
        for name in (*gate.OWNED_SOURCE_NAMES, gate.GUARD_SOURCE_NAME):
            data = (ROOT / name).read_bytes()
            for base in (root, frozen):
                path = base / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        compiler = self.directory / "non-executable-compiler"
        compiler.write_bytes(b"never execute this compiler fixture")
        self.stack.enter_context(patch.object(gate, "ROOT", root))
        report = {"complete": False, "source_hashes": gate.source_hashes(),
                  "compiler": {"selected": str(compiler), "path": str(compiler), "sha256": gate.sha(compiler)},
                  "matrices": []}
        tracker = gate.Conservation(compiler, frozen, report)
        return root, frozen, compiler, report, tracker

    def test_runner_hostile_formatter_getter_and_each_retention_fault_keep_primary(self):
        raw_text, raw_bytes = Path.write_text, Path.write_bytes
        for primary_type in (RuntimeError, KeyboardInterrupt):
            for fault in ("command", "failure", "stdout", "stderr", "retention", "getter"):
                with self.subTest(primary=primary_type.__name__, fault=fault):
                    reads, writes = [], []
                    secondary = MemoryError("secondary evidence failure")
                    class Hostile(primary_type):
                        output, stderr = b"partial stdout\n", b"partial stderr\n"
                        def __str__(self):
                            raise AssertionError("primary must never be formatted")
                        def __getattribute__(self, name):
                            if name in ("output", "stderr"):
                                reads.append(name)
                                if fault == "getter" and name == "output":
                                    raise secondary
                            return super().__getattribute__(name)
                    primary, cause = Hostile("guard failed"), ValueError("explicit earlier cause")
                    primary.__cause__ = cause
                    class Guard:
                        def run_with_heartbeat(self, *args, **kwargs):
                            raise primary
                    work = self.directory / (primary_type.__name__ + "-" + fault)
                    work.mkdir()
                    text_count = 0
                    def text_write(path, data, *args, **kwargs):
                        nonlocal text_count
                        writes.append(path.suffix)
                        if path.name.endswith(".command.json"):
                            text_count += 1
                            if fault == "command" and text_count == 2:
                                raise secondary
                        if ((fault == "failure" and path.suffix == ".txt") or
                                (fault == "retention" and path.name.endswith(".retention.json"))):
                            raise secondary
                        return raw_text(path, data, *args, **kwargs)
                    def bytes_write(path, data, *args, **kwargs):
                        writes.append(path.suffix)
                        if path.suffix == "." + fault:
                            raise secondary
                        return raw_bytes(path, data, *args, **kwargs)
                    with patch.object(Path, "write_text", text_write), patch.object(Path, "write_bytes", bytes_write):
                        with self.assertRaises(primary_type) as seen:
                            gate.Runner(Guard(), work).run(["never-executed-child"], "fault")
                    self.assertIs(seen.exception, primary)
                    self.assertIs(primary.__cause__, cause)
                    self.assertEqual(reads, ["output", "stderr"])
                    self.assertIn(".stderr", writes)
                    self.assertTrue(primary.c32_secondary_failures)
                    self.assertTrue(all(set(row) == {"stage", "type"} for row in primary.c32_secondary_failures))
                    record = json.loads((work / "001-fault.command.json").read_text())
                    self.assertNotEqual(record["status"], "finished")

    def test_successful_guard_surfaces_first_publication_failure_after_later_channels(self):
        first, later = MemoryError("first output publication"), KeyboardInterrupt("later stderr publication")
        attempts, raw = [], Path.write_bytes
        class Guard:
            def run_with_heartbeat(self, argv, **kwargs):
                return subprocess.CompletedProcess(argv, 0, "stdout\n", "stderr\n")
        def write(path, data, *args, **kwargs):
            attempts.append(path.suffix)
            if path.suffix == ".stdout": raise first
            if path.suffix == ".stderr": raise later
            return raw(path, data, *args, **kwargs)
        with patch.object(Path, "write_bytes", write), self.assertRaises(MemoryError) as seen:
            gate.Runner(Guard(), self.directory).run(["never-executed"], "success")
        self.assertIs(seen.exception, first)
        self.assertEqual(attempts, [".stdout", ".stderr"])
        self.assertTrue((self.directory / "001-success.result.json").exists())
        self.assertEqual([row["type"] for row in first.c32_secondary_failures], ["MemoryError", "KeyboardInterrupt"])

    def test_failed_recovery_record_update_still_attempts_pins_and_all_retention(self):
        tree = ast.parse(Path(gate.__file__).read_bytes())
        target = next(node.lineno for node in ast.walk(tree)
                      if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and
                      isinstance(node.func.value, ast.Name) and node.func.value.id == "record" and
                      node.func.attr == "update" and any(keyword.arg == "status" and
                      isinstance(keyword.value, ast.Constant) and keyword.value.value == "raised"
                      for keyword in node.keywords))
        for primary_type in (RuntimeError, KeyboardInterrupt):
            for secondary_type in (MemoryError, KeyboardInterrupt):
                with self.subTest(primary=primary_type.__name__, secondary=secondary_type.__name__):
                    primary, cause = primary_type("guard failed"), ValueError("prior cause")
                    primary.__cause__ = cause
                    primary.output, primary.stderr = b"partial stdout", b"partial stderr"
                    secondary, pins, fired = secondary_type("recovery update failed"), [], []
                    class Pins:
                        def check(self): pins.append("check")
                    class Guard:
                        def run_with_heartbeat(self, *args, **kwargs): raise primary
                    work = self.directory / (primary_type.__name__ + "-" + secondary_type.__name__)
                    work.mkdir()
                    def trace(frame, event, argument):
                        if (event == "line" and frame.f_code.co_filename == gate.__file__ and
                                frame.f_code.co_name == "<lambda>" and frame.f_lineno == target):
                            fired.append(target)
                            raise secondary
                        return trace
                    previous = sys.gettrace()
                    try:
                        sys.settrace(trace)
                        with self.assertRaises(primary_type) as seen:
                            gate.Runner(Guard(), work, Pins()).run(["never-executed"], "recovery")
                    finally:
                        sys.settrace(previous)
                    self.assertEqual(fired, [target])
                    self.assertIs(seen.exception, primary)
                    self.assertIs(primary.__cause__, cause)
                    self.assertEqual(pins, ["check", "check"])
                    self.assertEqual((work / "001-recovery.stdout").read_bytes(), primary.output)
                    self.assertEqual((work / "001-recovery.stderr").read_bytes(), primary.stderr)
                    self.assertEqual(json.loads((work / "001-recovery.failure.txt").read_text()),
                                     {"type": primary_type.__name__})
                    self.assertEqual(json.loads((work / "001-recovery.retention.json").read_text())
                                     ["secondary_failures"][0]["stage"], "failure-attribution")
                    self.assertEqual(primary.c32_secondary_failures[0]["type"], secondary_type.__name__)

    def test_environment_restores_all_variables_and_keeps_body_failure(self):
        names = ("ASAN_OPTIONS", "LSAN_OPTIONS", "UBSAN_OPTIONS")
        for primary_type in (RuntimeError, KeyboardInterrupt):
            for restore_type in (MemoryError, KeyboardInterrupt):
                with self.subTest(body=primary_type.__name__, restore=restore_type.__name__):
                    primary, cause = primary_type("body failed"), ValueError("earlier cause")
                    primary.__cause__ = cause
                    secondary, calls = restore_type("restore failed"), []
                    class Environment(dict):
                        armed = False
                        def __setitem__(self, key, value):
                            if self.armed:
                                calls.append(key)
                                if key == "ASAN_OPTIONS": raise secondary
                            super().__setitem__(key, value)
                    env = Environment({name: "original" for name in names})
                    with patch.object(os, "environ", env), self.assertRaises(primary_type) as seen:
                        with gate.sanitizer_environment(True):
                            env.armed = True
                            raise primary
                    self.assertIs(seen.exception, primary)
                    self.assertIs(primary.__cause__, cause)
                    self.assertEqual(calls, list(names))
                    self.assertEqual(env["LSAN_OPTIONS"], "original")
                    self.assertEqual(env["UBSAN_OPTIONS"], "original")

    def test_environment_success_surfaces_first_cleanup_failure_after_all_attempts(self):
        first, calls = MemoryError("first restore"), []
        class Environment(dict):
            armed = False
            def __setitem__(self, key, value):
                if self.armed:
                    calls.append(key)
                    raise first if key == "ASAN_OPTIONS" else KeyboardInterrupt("later restore")
                super().__setitem__(key, value)
        names = ("ASAN_OPTIONS", "LSAN_OPTIONS", "UBSAN_OPTIONS")
        env = Environment({name: "original" for name in names})
        with patch.object(os, "environ", env), self.assertRaises(MemoryError) as seen:
            with gate.sanitizer_environment(True):
                env.armed = True
        self.assertIs(seen.exception, first)
        self.assertEqual(calls, list(names))

    def test_conservation_rejects_every_original_and_frozen_input(self):
        root, frozen, _, report, tracker = self.fixture()
        tracker.check()
        for base in (root, frozen):
            for name in report["source_hashes"]:
                path, data = base / name, (base / name).read_bytes()
                with self.subTest(base=base.name, name=name):
                    path.write_bytes(data + b"drift")
                    with self.assertRaises(gate.GateError): tracker.check()
                    path.write_bytes(data)
        tracker.final_pins()
        self.assertEqual(report["final_source_hashes"], report["final_frozen_source_hashes"])

    def test_conservation_rejects_compiler_bytes_alias_resolution_and_known_binary(self):
        _, _, compiler, _, tracker = self.fixture()
        data = compiler.read_bytes()
        compiler.write_bytes(data + b"drift")
        with self.assertRaises(gate.GateError): tracker.check()
        compiler.write_bytes(data)
        raw_resolve = Path.resolve
        def changed_alias(path, *args, **kwargs):
            if path == tracker.selected: return self.directory / "other-compiler"
            return raw_resolve(path, *args, **kwargs)
        with patch.object(Path, "resolve", changed_alias), self.assertRaises(gate.GateError): tracker.check()
        binary = self.directory / "non-executable-binary"
        binary.write_bytes(b"metadata fixture")
        tracker.admit_binary(binary)
        binary.write_bytes(b"changed metadata fixture")
        with self.assertRaises(gate.GateError): tracker.final_pins()

    def test_runner_pre_post_conservation_and_primary_guard_failure(self):
        _, frozen, _, _, tracker = self.fixture()
        path = frozen / gate.OWNED_SOURCE_NAMES[0]
        data, calls = path.read_bytes(), []
        class Guard:
            failure = None
            def run_with_heartbeat(self, argv, **kwargs):
                calls.append(argv)
                path.write_bytes(data + b"drift during callback")
                if self.failure is not None: raise self.failure
                return subprocess.CompletedProcess(argv, 0, "", "")
        guard = Guard()
        path.write_bytes(data + b"pre-job drift")
        with self.assertRaises(gate.GateError): gate.Runner(guard, self.directory, tracker).run(["fake"], "pre")
        self.assertFalse(calls)
        path.write_bytes(data)
        with self.assertRaises(gate.GateError): gate.Runner(guard, self.directory, tracker).run(["fake"], "post")
        for kind in (RuntimeError, KeyboardInterrupt):
            path.write_bytes(data)
            primary, cause = kind("guard failed"), ValueError("prior cause")
            primary.__cause__ = cause
            guard.failure = primary
            with self.assertRaises(kind) as seen:
                gate.Runner(guard, self.directory, tracker).run(["fake"], "primary-" + kind.__name__)
            self.assertIs(seen.exception, primary)
            self.assertIs(primary.__cause__, cause)
            self.assertEqual(primary.c32_secondary_failures[0]["stage"], "post-job-conservation")

    def test_actual_run_gate_rejects_copied_source_drift_before_second_callback(self):
        _, _, compiler, report, _ = self.fixture()
        work, callbacks = self.directory / "gate-work", []
        work.mkdir()
        class MetadataOnly:
            def run_with_heartbeat(self, argv, **kwargs):
                callbacks.append(argv)
                copied = work / "frozen-source" / gate.OWNED_SOURCE_NAMES[0]
                copied.write_bytes(copied.read_bytes() + b"external copied-source drift")
                return subprocess.CompletedProcess(argv, 0, "clang metadata fixture\n", "")
        with patch.object(gate, "load_checks", lambda _: MetadataOnly()), self.assertRaises(gate.GateError):
            gate.run_gate(compiler, work, report, False)
        self.assertEqual(len(callbacks), 1)
        self.assertIs(report["complete"], False)

    def test_main_keeps_primary_when_failure_publication_or_retention_allocation_fails(self):
        compiler = self.directory / "non-executable-compiler"
        compiler.write_bytes(b"never execute")
        raw = Path.write_text
        for fault in ("publication", "allocation"):
            primary, cause = KeyboardInterrupt("guard cancellation"), ValueError("prior cause")
            primary.__cause__ = cause
            work = self.directory / fault
            reports = []
            def no_gate(*args, **kwargs):
                if fault == "allocation":
                    def no_evidence(): raise MemoryError("allocation failed")
                    self.stack.enter_context(patch.object(gate, "_Evidence", no_evidence))
                raise primary
            def write(path, data, *args, **kwargs):
                if path == work / "report.json":
                    reports.append(data)
                    if len(reports) == 2: raise MemoryError("failure publication failed")
                return raw(path, data, *args, **kwargs)
            with patch.object(sys, "argv", ["gate", "--plain", "--clang", str(compiler), "--work", str(work)]), \
                    patch.object(gate, "run_gate", no_gate), patch.object(Path, "write_text", write), \
                    self.assertRaises(KeyboardInterrupt) as seen:
                gate.main()
            self.assertIs(seen.exception, primary)
            self.assertIs(primary.__cause__, cause)
            self.assertIs(json.loads((work / "report.json").read_text())["complete"], False)

    def test_main_final_publication_drift_fails_and_retains_incomplete_report(self):
        _, _, compiler, _, _ = self.fixture()
        raw = Path.write_text
        for stage in ("before-replace", "after-replace"):
            work = self.directory / stage
            changed = work / "frozen-source" / gate.OWNED_SOURCE_NAMES[0]
            def metadata_gate(clang, directory, report, sanitize):
                for name in report["source_hashes"]:
                    target = directory / "frozen-source" / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes((gate.ROOT / name).read_bytes())
                return gate.Conservation(clang, directory / "frozen-source", report)
            def write(path, data, *args, **kwargs):
                result = raw(path, data, *args, **kwargs)
                if stage == "before-replace" and path.name == "report.pending.json":
                    changed.write_bytes(changed.read_bytes() + b"drift before publication")
                return result
            raw_replace = os.replace
            def replace(source, target):
                raw_replace(source, target)
                if stage == "after-replace": changed.write_bytes(changed.read_bytes() + b"drift after publication")
            with patch.object(sys, "argv", ["gate", "--plain", "--clang", str(compiler), "--work", str(work)]), \
                    patch.object(gate, "run_gate", metadata_gate), patch.object(gate, "validate_report", lambda *args: None), \
                    patch.object(Path, "write_text", write), patch.object(os, "replace", replace), \
                    self.assertRaises(gate.GateError):
                gate.main()
            self.assertIs(json.loads((work / "report.json").read_text())["complete"], False)

    def test_main_failed_recovery_report_update_still_attempts_failure_publication(self):
        tree = ast.parse(Path(gate.__file__).read_bytes())
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
        target = next(node.lineno for node in ast.walk(main) if isinstance(node, ast.Call) and
                      isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and
                      node.func.value.id == "report" and node.func.attr == "update")
        compiler = self.directory / "non-executable-compiler"
        compiler.write_bytes(b"never execute")
        raw = Path.write_text
        for primary_type in (RuntimeError, KeyboardInterrupt):
            for secondary_type in (MemoryError, KeyboardInterrupt):
                with self.subTest(primary=primary_type.__name__, secondary=secondary_type.__name__):
                    primary, cause = primary_type("main failed"), ValueError("prior cause")
                    primary.__cause__ = cause
                    secondary, fired, writes = secondary_type("recovery report update failed"), [], []
                    work = self.directory / (primary_type.__name__ + "-" + secondary_type.__name__)
                    def no_gate(*args, **kwargs): raise primary
                    def write(path, data, *args, **kwargs):
                        if path == work / "report.json": writes.append(data)
                        return raw(path, data, *args, **kwargs)
                    def trace(frame, event, argument):
                        if (event == "line" and frame.f_code.co_filename == gate.__file__ and
                                frame.f_code.co_name == "<lambda>" and frame.f_lineno == target):
                            fired.append(target)
                            raise secondary
                        return trace
                    previous = sys.gettrace()
                    try:
                        with patch.object(gate, "run_gate", no_gate), patch.object(Path, "write_text", write), \
                                patch.object(sys, "argv", ["gate", "--plain", "--clang", str(compiler), "--work", str(work)]):
                            sys.settrace(trace)
                            with self.assertRaises(primary_type) as seen: gate.main()
                    finally:
                        sys.settrace(previous)
                    self.assertEqual(fired, [target])
                    self.assertIs(seen.exception, primary)
                    self.assertIs(primary.__cause__, cause)
                    self.assertEqual(len(writes), 2)
                    self.assertTrue(all(json.loads(value)["complete"] is False for value in writes))
                    self.assertEqual(primary.c32_secondary_failures[0]["stage"], "failure-report-attribution")


if __name__ == "__main__":
    unittest.main()
