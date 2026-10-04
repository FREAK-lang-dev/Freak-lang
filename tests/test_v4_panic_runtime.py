"""Prove crashes, sanitizer exits and polluted output cannot satisfy panic gates."""
from __future__ import annotations

import signal
import subprocess
import unittest

from tests.v4_panic_runtime import assert_exact_abort


class PanicAbortOracleTests(unittest.TestCase):
    diagnostics = (b"PANIC: \n", "PANIC: café 中😀\n".encode(), b"PANIC: A\0B\n",
                   b"PANIC: first\r\nsecond\n",
                   b"FREAK: V4 word panic: word value is not live owned storage\n")

    @staticmethod
    def result(status: int, stderr: bytes, stdout: bytes = b"") -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(["panic-probe"], status, stdout, stderr)

    def test_exact_abort_and_binary_diagnostics(self) -> None:
        for platform in ("linux", "darwin", "win32"):
            status = 3 if platform == "win32" else -signal.SIGABRT
            for diagnostic in self.diagnostics:
                with self.subTest(platform=platform, diagnostic=diagnostic):
                    assert_exact_abort(self.result(status, diagnostic), diagnostic, platform=platform)

    def test_changed_newline_bytes_are_rejected(self) -> None:
        for platform in ("linux", "darwin", "win32"):
            status = 3 if platform == "win32" else -signal.SIGABRT
            for diagnostic in self.diagnostics:
                changed = {diagnostic.replace(b"\n", b"\r\n"), diagnostic.replace(b"\r\n", b"\n")}
                for stderr in changed - {diagnostic}:
                    with self.subTest(platform=platform, diagnostic=diagnostic, stderr=stderr):
                        with self.assertRaises(AssertionError):
                            assert_exact_abort(self.result(status, stderr), diagnostic, platform=platform)

    def test_wrong_exit_or_signal_is_rejected(self) -> None:
        statuses = {0, 1, 2, 3, 4, 85, 86, 87, 98, 99, -signal.SIGABRT, -signal.SIGSEGV, -signal.SIGILL}
        for platform in ("linux", "darwin", "win32"):
            expected = 3 if platform == "win32" else -signal.SIGABRT
            for diagnostic in self.diagnostics:
                for status in statuses - {expected}:
                    with self.subTest(platform=platform, diagnostic=diagnostic, status=status):
                        with self.assertRaises(AssertionError):
                            assert_exact_abort(self.result(status, diagnostic), diagnostic, platform=platform)

    def test_sanitizer_audit_and_deferred_output_is_rejected(self) -> None:
        reports = (b"ERROR: AddressSanitizer: heap-use-after-free\n",
                   b"ERROR: LeakSanitizer: detected memory leaks\n",
                   b"runtime error: load of invalid value\n",
                   b"FREAK: LLVM ownership audit found 1 unreleased word allocation(s)\n",
                   b"FREAK: C ownership audit found 1 unreleased word allocation(s)\n",
                   b"panic-atexit-ran\n", b"unexpected diagnostic\n", b"\n")
        for platform in ("linux", "darwin", "win32"):
            status = 3 if platform == "win32" else -signal.SIGABRT
            for diagnostic in self.diagnostics:
                for report in reports:
                    for stderr in (report + diagnostic, diagnostic + report):
                        with self.subTest(platform=platform, diagnostic=diagnostic, stderr=stderr):
                            with self.assertRaises(AssertionError):
                                assert_exact_abort(self.result(status, stderr), diagnostic, platform=platform)

    def test_wrong_reason_truncated_nul_or_stdout_is_rejected(self) -> None:
        for platform in ("linux", "darwin", "win32"):
            status = 3 if platform == "win32" else -signal.SIGABRT
            for diagnostic in self.diagnostics:
                for stderr in (b"", b"PANIC: wrong reason\n", diagnostic.rstrip(b"\n"), diagnostic * 2,
                               diagnostic.partition(b"\0")[0] if b"\0" in diagnostic else b"wrong prefix\n"):
                    with self.subTest(platform=platform, diagnostic=diagnostic, stderr=stderr):
                        with self.assertRaises(AssertionError):
                            assert_exact_abort(self.result(status, stderr), diagnostic, platform=platform)
                for stdout in (b" ", b"\n", b"panic-returned\n", b"\0"):
                    with self.subTest(platform=platform, diagnostic=diagnostic, stdout=stdout):
                        with self.assertRaises(AssertionError):
                            assert_exact_abort(self.result(status, diagnostic, stdout), diagnostic, platform=platform)


if __name__ == "__main__":
    unittest.main()
