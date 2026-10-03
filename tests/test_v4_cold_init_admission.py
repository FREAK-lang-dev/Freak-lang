"""Pure adversarial checks for the mandatory native fault-proof oracle."""
import subprocess
import unittest

from v4_cold_init_admission import expected_output_lines, fault_cases, validate_result


class ColdAdmissionOracleTests(unittest.TestCase):
    def result(self, lines=None, code=0, stderr=""):
        lines = expected_output_lines() if lines is None else lines
        return subprocess.CompletedProcess(["probe"], code, "\n".join(lines) + "\n", stderr)

    def test_complete_manifest_passes(self):
        self.assertEqual(len(fault_cases()), 129)
        validate_result(self.result())

    def test_missing_singleton_or_bootstrap_case_fails(self):
        lines = expected_output_lines()
        for index in (0, 16, 17, 18, 21, 22, 42, 128, 129):
            with self.subTest(index=index), self.assertRaises(RuntimeError):
                validate_result(self.result(lines[:index] + lines[index + 1:]))

    def test_wrong_position_cycle_status_or_order_fails(self):
        lines = expected_output_lines()
        for wrong in ("fault|query|0|0|ok", "fault|query|1|1|ok", "fault|query|1|0|failed", "fault|expand|1|0|ok"):
            with self.subTest(wrong=wrong), self.assertRaises(RuntimeError):
                validate_result(self.result([wrong] + lines[1:]))
        with self.assertRaises(RuntimeError):
            validate_result(self.result([lines[1], lines[0]] + lines[2:]))

    def test_failure_exit_and_diagnostics_fail_even_with_complete_output(self):
        for code in (1, -6, 3):
            with self.subTest(code=code), self.assertRaises(RuntimeError):
                validate_result(self.result(code=code))
        for message in ("AddressSanitizer: error", "runtime error: overflow", "unexpected diagnostic"):
            with self.subTest(message=message), self.assertRaises(RuntimeError):
                validate_result(self.result(stderr=message))

    def test_summary_only_duplicate_case_or_missing_recovery_fails(self):
        lines = expected_output_lines()
        for wrong in ([lines[-1]], [lines[0]] + lines, lines[:-1] + [lines[-1].replace("recovery=true", "recovery=false")]):
            with self.subTest(lines=len(wrong)), self.assertRaises(RuntimeError):
                validate_result(self.result(wrong))


if __name__ == "__main__":
    unittest.main()
