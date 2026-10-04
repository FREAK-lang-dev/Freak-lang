"""Adversarial pure controls for the numerical native gate's success oracle."""
from __future__ import annotations

from copy import deepcopy
from contextlib import redirect_stderr
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("v4_checked_numeric_codegen", ROOT / "tests/v4_checked_numeric_codegen.py")
gate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gate
SPEC.loader.exec_module(gate)
FIXTURES = ROOT / "src/compiler/v4/tests"


def result(status=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(["probe"], status, stdout, stderr)


def compiler_output(snapshot=False, module='define i32 @main() { ret i32 0 }\n'):
    stdout = "checked-numeric-diag=0\nchecked-numeric-body-count=13\n"
    stdout += "checked-numeric-error=\nchecked-numeric-module-nonempty=true\n"
    phases = ["lex", "parse", "hir", "resolve", "ty", "mir", "codegen", "module"]
    if snapshot:
        stdout += "".join(f"checked-numeric-snapshot-{flag}=true\n" for flag in gate.SNAPSHOT_FLAGS)
        phases += ["snapshot-build", "snapshot-validate", "snapshot-restore", "snapshot-done"]
    phases += ["done"]
    stdout += "@@LLVM-MODULE-BEGIN\n" + module + "@@LLVM-MODULE-END\n"
    stderr = "".join("checked-numeric-phase=" + phase + "\n" for phase in phases)
    return result(stdout=stdout, stderr=stderr)


def report(sanitize=True, snapshot=True):
    rows = []
    for name in [*[f"case-{index}" for index in range(gate.CASE_COUNT)], "checked_numerics", "depth256"]:
        stdout, stderr, status = "", "", 0
        if name.startswith("case-") and int(name[5:]) in gate.expected_errors_by_case():
            stderr, status = gate.expected_errors_by_case()[int(name[5:])], 1
        if name == "checked_numerics":
            stdout = "checked numerics passed\n"
        for opt in gate.OPTS:
            rows.append({"program": name, "optimization": opt, "status": "pass", "exit": status,
                         "stdout_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
                         "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest()})
    controls = [{"name": f"audit-{kind}-O{opt}", "status": "pass"} for kind in ("C", "LLVM") for opt in gate.OPTS]
    if sanitize:
        controls += [{"name": "sanitizer-" + kind, "status": "pass"} for kind in ("address", "undefined")]
    flags = [*gate.AUDIT_FLAGS, *(gate.SANITIZER_FLAGS if sanitize else ())]
    return {"sanitizers": sanitize, "snapshot_control": snapshot, "ownership_audits": ["C", "LLVM"],
            "build_flags": {str(opt): list(flags) for opt in gate.OPTS}, "controls": controls,
            "programs": rows, "snapshot_facts": {flag: True for flag in gate.SNAPSHOT_FLAGS},
            "compiler_contracts": [{"arguments": args, "status": "pass"} for args in gate.contract_arguments()]}


class NumericGateOracles(unittest.TestCase):
    def test_all_48_fixture_sources_and_41_fatal_oracles(self):
        text = (FIXTURES / "checked_numeric_execute_smoke.fk").read_text()
        cases = gate.load_cases(text)
        self.assertEqual(len(cases), 48)
        self.assertEqual(sum(case.exit == 1 for case in cases), 41)
        self.assertEqual(cases[45].exit, 0)
        self.assertIn("0.1", cases[45].source)
        self.assertIn("16777217", cases[46].source)
        self.assertIn('pointer.write(value)', cases[47].source)
        self.assertIn('value = 258', cases[47].source)
        self.assertEqual(cases[47].stderr, "FREAK V4: int to tiny conversion out of range\n")

    def test_missing_duplicate_and_oracle_drift_are_errors(self):
        text = (FIXTURES / "checked_numeric_execute_smoke.fk").read_text()
        bad_inputs = [text.replace("if case_id == 46", "if case_id == 0", 1),
                      "\n".join(row for row in text.splitlines() if "if case_id == 46" not in row),
                      text.replace("int addition overflow", "int addition underflow", 1)]
        for malformed in bad_inputs:
            with self.subTest(malformed=malformed[:60]), self.assertRaises(gate.GateError):
                gate.load_cases(malformed)
        with self.assertRaises(gate.GateError):
            gate.literal_expression('__import__("os").system("bad")')

    def test_fatal_reason_exit_signal_sanitizer_and_extra_output_rejected(self):
        expected = gate.expected_errors()[0]
        gate.exact_result(result(1, "", expected), 1, "", expected, "fatal")
        impostors = [result(86, "", expected), result(-11, "", expected),
                     result(3221225477, "", expected), result(0, "", expected),
                     result(1, "extra\n", expected), result(1, "", expected + "extra\n"),
                     result(1, "", "FREAK V4: int division by zero\n"),
                     result(86, "", "ERROR: AddressSanitizer: heap-use-after-free\n"),
                     result(1, "", expected + "FREAK: LLVM ownership audit found 1 unreleased word allocation(s)\n")]
        for impostor in impostors:
            with self.subTest(exit=impostor.returncode, stderr=impostor.stderr), self.assertRaises(gate.GateError):
                gate.exact_result(impostor, 1, "", expected, "fatal")

    def test_success_must_have_exact_output_and_zero_owners(self):
        for impostor in (result(0, "expected\nextra\n"), result(1, "expected\n"),
                         result(0, "expected\n", "runtime error: overflow\n"),
                         result(86, "expected\n", "FREAK: LLVM ownership audit found 1 unreleased word allocation(s)\n")):
            with self.assertRaises(gate.GateError):
                gate.exact_result(impostor, 0, "expected\n", "", "success")

    def test_windows_crlf_is_explicit_and_posix_cr_is_rejected(self):
        gate.exact_result(result(1, "x\r\n", "error\r\n"), 1, "x\n", "error\n", "windows", "win32")
        with self.assertRaises(gate.GateError):
            gate.exact_result(result(1, "", "error\r\n"), 1, "", "error\n", "linux", "linux")

    def test_sanitizer_exit_without_its_diagnostic_is_not_capability(self):
        gate.validate_sanitizer_probe(result(88, "", "ERROR: AddressSanitizer: heap-use-after-free\n"), "address")
        gate.validate_sanitizer_probe(result(88, "", "runtime error: signed integer overflow\n"), "undefined")
        for impostor in (result(88), result(86, "", "ERROR: AddressSanitizer: heap-use-after-free\n"),
                         result(88, "extra", "ERROR: AddressSanitizer: heap-use-after-free\n")):
            with self.assertRaises(gate.GateError):
                gate.validate_sanitizer_probe(impostor, "address")

    def test_module_protocol_rejects_error_noise_empty_duplicate_and_poison(self):
        self.assertIn("define", gate.parse_module(compiler_output()))
        impostors = [compiler_output(module=""), compiler_output(module="%x = fptosi double 1.0 to i64\n")]
        clean = compiler_output()
        impostors += [result(1, clean.stdout, clean.stderr),
                      result(0, clean.stdout + "PANIC: hidden failure\n", clean.stderr),
                      result(0, clean.stdout + "@@LLVM-MODULE-BEGIN\n", clean.stderr),
                      result(0, clean.stdout.replace("diag=0", "diag=1"), clean.stderr),
                      result(0, clean.stdout, clean.stderr + "runtime error: bad\n")]
        for impostor in impostors:
            with self.assertRaises(gate.GateError):
                gate.parse_module(impostor)

    def test_snapshot_needs_restore_old_seal_and_fresh_exact_module(self):
        valid = compiler_output(snapshot=True)
        gate.parse_module(valid, snapshot=True)
        for flag in gate.SNAPSHOT_FLAGS:
            for replacement in ("false", ""):
                changed = valid.stdout.replace(f"snapshot-{flag}=true", f"snapshot-{flag}={replacement}")
                with self.subTest(flag=flag), self.assertRaises(gate.GateError):
                    gate.parse_module(result(0, changed, valid.stderr), snapshot=True)
        with self.assertRaises(gate.GateError):
            gate.parse_module(result(0, valid.stdout.replace("body-count=13", "body-count=1"), valid.stderr), snapshot=True)

    def test_assembly_retains_fixtures_and_checks_snapshot_both_ways(self):
        execution = (FIXTURES / "checked_numeric_execute_smoke.fk").read_text()
        contracts = (FIXTURES / "checked_numeric_contract_smoke.fk").read_text()
        assembled = gate.assemble_probe(execution, contracts, "aarch64-apple-darwin")
        self.assertIn('v4_target_spec_new("aarch64-apple-darwin")', assembled)
        self.assertIn("v4_codegen_llvm_module_text(codegen, target) == module", assembled)
        self.assertIn("v4_codegen_llvm_module_text(restored_codegen, target) == module", assembled)
        with self.assertRaises(gate.GateError):
            gate.assemble_probe(execution.replace("snapshot-done", "changed-boundary"), contracts)

    def test_all_141_compiler_contracts_have_exact_closed_success_oracles(self):
        args = gate.contract_arguments()
        self.assertEqual(len(args), 141)
        self.assertEqual(len({tuple(row) for row in args}), 141)
        for row in args:
            stdout = gate.contract_stdout(row)
            if stdout is not None:
                gate.validate_contract(result(0, stdout), row)
                with self.assertRaises(gate.GateError):
                    gate.validate_contract(result(0, stdout + "extra\n"), row)
                with self.assertRaises(gate.GateError):
                    gate.validate_contract(result(86, stdout), row)

    def test_pressure_requires_each_distinct_allocation_boundary(self):
        for room in ("0", "16", "24", "32"):
            arguments = ["5", room]
            expected = ("checked-numeric-pressure-cleanup-error=native owned word cleanup scratch allocation failed\n"
                        "checked-numeric-pressure-publication-error=native LLVM fragment scratch allocation failed\n"
                        f"checked-numeric-pressure-room={room} error=native codegen plan arena allocation failed\n"
                        "checked-numeric-contract-case-5=passed\n")
            gate.validate_contract(result(0, expected), arguments)
            for line in expected.splitlines(keepends=True)[:3]:
                with self.subTest(room=room, missing=line), self.assertRaises(gate.GateError):
                    gate.validate_contract(result(0, expected.replace(line, "")), arguments)
            old_error = ("native LLVM fragment scratch allocation failed" if room in ("0", "16")
                         else "missing clean Meiya result for native word ownership lowering" if room == "24"
                         else "Meiya errors prevent native word ownership lowering")
            old = f"checked-numeric-pressure-room={room} error={old_error}\nchecked-numeric-contract-case-5=passed\n"
            with self.subTest(room=room, obsolete=old_error), self.assertRaises(gate.GateError):
                gate.validate_contract(result(0, old), arguments)
        with self.assertRaises(gate.GateError):
            gate.contract_stdout(["5", "49"])

    def test_report_requires_every_case_opt_audit_sanitizer_and_contract(self):
        valid = report()
        gate.validate_report(valid, True, True)
        mutations = []
        missing = deepcopy(valid); missing["programs"].pop(); mutations.append(missing)
        duplicate = deepcopy(valid); duplicate["programs"][-1] = duplicate["programs"][0]; mutations.append(duplicate)
        failed = deepcopy(valid); failed["programs"][0]["exit"] = 86; mutations.append(failed)
        wrong_output = deepcopy(valid); wrong_output["programs"][0]["stderr_sha256"] = "bad"; mutations.append(wrong_output)
        missing_audit = deepcopy(valid); missing_audit["ownership_audits"] = ["LLVM"]; mutations.append(missing_audit)
        missing_flag = deepcopy(valid); missing_flag["build_flags"]["2"].remove(gate.AUDIT_FLAGS[0]); mutations.append(missing_flag)
        no_sanitizer = deepcopy(valid); no_sanitizer["build_flags"]["0"].remove(gate.SANITIZER_FLAGS[1]); mutations.append(no_sanitizer)
        no_control = deepcopy(valid); no_control["controls"].pop(); mutations.append(no_control)
        no_contract = deepcopy(valid); no_contract["compiler_contracts"].pop(); mutations.append(no_contract)
        no_fresh = deepcopy(valid); no_fresh["snapshot_facts"]["module-exact"] = False; mutations.append(no_fresh)
        for malformed in mutations:
            with self.assertRaises(gate.GateError):
                gate.validate_report(malformed, True, True)

    def test_plain_mode_is_distinct_and_still_requires_audits(self):
        valid = report(False, False)
        gate.validate_report(valid, False, False)
        with self.assertRaises(gate.GateError):
            gate.validate_report(valid, True, False)
        valid["build_flags"]["3"].remove(gate.AUDIT_FLAGS[1])
        with self.assertRaises(gate.GateError):
            gate.validate_report(valid, False, False)

    def test_sanitizer_environment_overrides_and_restores_external_options(self):
        with patch.dict(os.environ, {"ASAN_OPTIONS": "exitcode=0", "UBSAN_OPTIONS": "halt_on_error=0", "LSAN_OPTIONS": "exitcode=0"}):
            with gate.sanitizer_environment(True):
                self.assertIn("exitcode=88", os.environ["ASAN_OPTIONS"])
                self.assertNotIn("LSAN_OPTIONS", os.environ)
            self.assertEqual(os.environ["ASAN_OPTIONS"], "exitcode=0")
            self.assertEqual(os.environ["UBSAN_OPTIONS"], "halt_on_error=0")
            self.assertEqual(os.environ["LSAN_OPTIONS"], "exitcode=0")

    def test_failure_writes_partial_report_and_cannot_return_success(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            messages = io.StringIO()
            with patch.object(gate, "run_gate", side_effect=gate.GateError("missing cases")), redirect_stderr(messages):
                self.assertEqual(gate.main(["--clang", "fake", "--work", str(path)]), 1)
            self.assertIn("FAILED: missing cases", messages.getvalue())
            import json
            evidence = json.loads((path / "results.json").read_text())
            self.assertFalse(evidence["passed"])
            self.assertEqual(evidence["error"], "missing cases")


if __name__ == "__main__":
    unittest.main()
