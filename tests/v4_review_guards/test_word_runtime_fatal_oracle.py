"""Sanitizer failures and wrong termination cannot masquerade as word panics."""
import importlib.util
from pathlib import Path
import signal
import subprocess
import unittest


SPEC = importlib.util.spec_from_file_location(
    "word_runtime_gate", Path(__file__).resolve().parents[1] / "v4_word_runtime.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class WordPanicOracle(unittest.TestCase):
    reason = "character index out of bounds"
    diagnostic = b"FREAK: V4 word panic: character index out of bounds\n"

    def result(self, code=-signal.SIGABRT, stdout=b"", stderr=None):
        return subprocess.CompletedProcess([], code, stdout,
                                           self.diagnostic if stderr is None else stderr)

    def test_exact_posix_and_crt_abort_are_the_only_accepted_terminations(self):
        gate.assert_named_panic(self.result(), self.reason, platform="linux")
        gate.assert_named_panic(self.result(3, stderr=self.diagnostic.replace(b"\n", b"\r\n")),
                                self.reason, platform="win32")
        for platform in ("linux", "win32"):
            for code in (0, 1, 85, 86, 87, 98, 99, -signal.SIGSEGV):
                with self.subTest(platform=platform, code=code), self.assertRaises(AssertionError):
                    gate.assert_named_panic(self.result(code), self.reason, platform=platform)

    def test_sanitizer_text_wrong_message_and_output_are_rejected(self):
        for text in (b"ERROR: AddressSanitizer", b"ERROR: LeakSanitizer",
                     b"UndefinedBehaviorSanitizer", b"runtime error:"):
            for stderr in (text + b"\n" + self.diagnostic, self.diagnostic + text + b"\n"):
                with self.subTest(stderr=stderr), self.assertRaises(AssertionError):
                    gate.assert_named_panic(self.result(stderr=stderr), self.reason, platform="linux")
        with self.assertRaises(AssertionError):
            gate.assert_named_panic(self.result(stdout=b"result"), self.reason, platform="linux")
        with self.assertRaises(AssertionError):
            gate.assert_named_panic(self.result(stderr=b"FREAK: V4 word panic: wrong reason\n"),
                                    self.reason, platform="linux")

    def test_crlf_cannot_masquerade_as_exact_posix_diagnostics(self):
        for platform in ("linux", "darwin"):
            with self.subTest(platform=platform), self.assertRaises(AssertionError):
                gate.assert_named_panic(self.result(stderr=self.diagnostic.replace(b"\n", b"\r\n")),
                                        self.reason, platform=platform)


if __name__ == "__main__":
    unittest.main()
