"""Process-free checks for the checked32 runtime's independent gate oracles."""
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import types
import unittest


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
              "compiler": {"sha256": "b" * 64, "target": "x86_64-pc-linux-gnu"},
              "final_compiler_sha256": "b" * 64, "matrices": []}
    report["final_source_hashes"] = dict(report["source_hashes"])
    for opt in gate.OPTS:
        report["matrices"].append({"optimization": opt, "flags": gate.build_flags(opt, sanitize),
                                  "binary_sha256": "c" * 64,
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
        changed = deepcopy(good); changed["final_compiler_sha256"] = "d" * 64; bad_reports.append(changed)
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


if __name__ == "__main__":
    unittest.main()
