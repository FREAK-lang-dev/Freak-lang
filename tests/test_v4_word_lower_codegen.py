"""Pure adversarial controls for the lowercase native/compiler oracles."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

spec = importlib.util.spec_from_file_location("lower_gate", Path(__file__).with_name("v4_word_lower_codegen.py"))
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class WordLowerOracle(unittest.TestCase):
    def result(self, stdout, *, code=0, stderr=""):
        return SimpleNamespace(returncode=code, stdout=stdout, stderr=stderr)

    def module(self):
        return gate.PREFIX + "@@LLVM-MODULE-BEGIN\ncall i64 @freak_v4_word_to_lower(i64 %value)\n@@LLVM-MODULE-END\n"

    def test_exact_nul_unicode_output(self):
        self.assertEqual(gate.assert_native_output(self.result(gate.EXPECTED), gate.EXPECTED, platform="linux"), gate.EXPECTED)

    def test_wrong_exit_and_signal(self):
        for code in (1, -11, 85, 86):
            with self.subTest(code=code), self.assertRaises(RuntimeError):
                gate.assert_native_output(self.result(gate.EXPECTED, code=code), gate.EXPECTED, platform="linux")

    def test_sanitizer_audit_extra_output(self):
        for stderr in ("AddressSanitizer error\n", "runtime ownership audit\n", "undefined behavior\n"):
            with self.subTest(stderr=stderr), self.assertRaises(RuntimeError):
                gate.assert_native_output(self.result(gate.EXPECTED, stderr=stderr), gate.EXPECTED, platform="linux")
        for stdout in (gate.EXPECTED + "extra\n", gate.EXPECTED.replace("\0", ""), gate.EXPECTED.replace("\u0307", "")):
            with self.subTest(stdout=stdout), self.assertRaises(RuntimeError):
                gate.assert_native_output(self.result(stdout), gate.EXPECTED, platform="linux")

    def test_posix_crlf_is_not_hidden(self):
        for platform in ("linux", "darwin"):
            with self.subTest(platform=platform), self.assertRaises(RuntimeError):
                gate.assert_native_output(self.result(gate.EXPECTED.replace("\n", "\r\n")), gate.EXPECTED, platform=platform)

    def test_windows_text_newlines_only(self):
        gate.assert_native_output(self.result(gate.EXPECTED.replace("\n", "\r\n")), gate.EXPECTED, platform="win32")
        with self.assertRaises(RuntimeError):
            gate.assert_native_output(self.result(gate.EXPECTED + "\r"), gate.EXPECTED, platform="win32")

    def test_compiler_exact_protocol(self):
        self.assertIn("@freak_v4_word_to_lower", gate.extract_module(self.result(self.module()), platform="linux"))

    def test_compiler_failure_and_forged_protocol(self):
        for stdout in (self.module() + "extra\n", self.module().replace("old-seal=true", "old-seal=false"),
                       self.module().replace("call i64 @freak_v4_word_to_lower", "declare i64 @freak_v4_word_to_lower"),
                       self.module().replace("@@LLVM-MODULE-BEGIN\n", "@@LLVM-MODULE-BEGIN\n@@LLVM-MODULE-BEGIN\n"),
                       self.module().replace("\n", "\r\n")):
            with self.subTest(stdout=stdout), self.assertRaises(RuntimeError):
                gate.extract_module(self.result(stdout), platform="linux")
        for code, stderr in ((1, ""), (0, "audit\n")):
            with self.subTest(code=code), self.assertRaises(RuntimeError):
                gate.extract_module(self.result(self.module(), code=code, stderr=stderr))

    def test_complete_matrix_requires_both_audits(self):
        rows = [{"optimization": opt, "status": "pass", "ownership_audits": ["C", "LLVM"]} for opt in gate.OPTIMIZATIONS]
        gate.assert_complete(rows)
        for bad in (rows[:-1], rows + rows[:1], [rows[0]] * 3,
                    [dict(row, ownership_audits=["C"]) for row in rows],
                    [dict(row, status="skip") for row in rows]):
            with self.subTest(bad=bad), self.assertRaises(RuntimeError):
                gate.assert_complete(bad)


if __name__ == "__main__":
    unittest.main()
