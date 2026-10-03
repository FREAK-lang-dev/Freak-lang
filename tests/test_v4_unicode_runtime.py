"""Reject false successes in the native Unicode panic proof."""

from __future__ import annotations

import signal
import subprocess
import unittest

from tests.v4_unicode_runtime import assert_named_panic


class UnicodePanicOracleTests(unittest.TestCase):
    diagnostics = (
        "FREAK: V4 Unicode panic: word value is not a live owner\n",
        "FREAK: V4 word panic: invalid UTF-8\n",
    )

    def result(self, status: int, stderr: bytes, stdout: bytes = b"") -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(["unicode-probe"], status, stdout, stderr)

    def test_accept_only_exact_abort_status_and_diagnostic(self) -> None:
        for platform in ("linux", "darwin", "win32"):
            status = 3 if platform == "win32" else -signal.SIGABRT
            for diagnostic in self.diagnostics:
                outputs = (diagnostic.encode(), diagnostic.replace("\n", "\r\n").encode()) if platform == "win32" else (diagnostic.encode(),)
                for stderr in outputs:
                    with self.subTest(platform=platform, diagnostic=diagnostic, stderr=stderr):
                        assert_named_panic(self.result(status, stderr), diagnostic, platform=platform)

    def test_crlf_cannot_masquerade_as_exact_posix_diagnostics(self) -> None:
        for platform in ("linux", "darwin"):
            for diagnostic in self.diagnostics:
                with self.subTest(platform=platform, diagnostic=diagnostic), self.assertRaises(AssertionError):
                    assert_named_panic(self.result(-signal.SIGABRT, diagnostic.replace("\n", "\r\n").encode()), diagnostic, platform=platform)

    def test_wrong_exit_and_signal_never_prove_rejection(self) -> None:
        for platform in ("linux", "darwin", "win32"):
            expected = 3 if platform == "win32" else -signal.SIGABRT
            for diagnostic in self.diagnostics:
                for status in {0, 1, 2, 3, 4, 85, 86, 87, 98, 99, -signal.SIGABRT, -signal.SIGSEGV, -signal.SIGILL} - {expected}:
                    with self.subTest(platform=platform, diagnostic=diagnostic, status=status):
                        with self.assertRaises(AssertionError):
                            assert_named_panic(self.result(status, diagnostic.encode()), diagnostic, platform=platform)

    def test_sanitizer_audit_or_extra_diagnostic_never_proves_rejection(self) -> None:
        reports = (
            b"ERROR: LeakSanitizer: detected memory leaks\n",
            b"ERROR: AddressSanitizer: heap-use-after-free\n",
            b"runtime error: load of invalid value\n",
            b"FREAK: C ownership audit found 1 unreleased word allocation(s)\n",
            b"FREAK: LLVM ownership audit found 1 unreleased word allocation(s)\n",
            b"unexpected diagnostic\n",
            b"\n",
        )
        for platform in ("linux", "darwin", "win32"):
            status = 3 if platform == "win32" else -signal.SIGABRT
            for diagnostic in self.diagnostics:
                for report in reports:
                    for stderr in (diagnostic.encode() + report, report + diagnostic.encode()):
                        with self.subTest(platform=platform, diagnostic=diagnostic, stderr=stderr):
                            with self.assertRaises(AssertionError):
                                assert_named_panic(self.result(status, stderr), diagnostic, platform=platform)

    def test_wrong_or_missing_diagnostic_and_stdout_never_prove_rejection(self) -> None:
        for platform in ("linux", "darwin", "win32"):
            status = 3 if platform == "win32" else -signal.SIGABRT
            for diagnostic in self.diagnostics:
                for stderr in (b"", diagnostic.rstrip("\n").encode(), b"FREAK: wrong reason\n", diagnostic.encode() * 2):
                    with self.subTest(platform=platform, diagnostic=diagnostic, stderr=stderr):
                        with self.assertRaises(AssertionError):
                            assert_named_panic(self.result(status, stderr), diagnostic, platform=platform)
                for stdout in (b"\n", b" ", b"value\n", b"\0"):
                    with self.subTest(platform=platform, diagnostic=diagnostic, stdout=stdout):
                        with self.assertRaises(AssertionError):
                            assert_named_panic(self.result(status, diagnostic.encode(), stdout), diagnostic, platform=platform)


if __name__ == "__main__":
    unittest.main()
