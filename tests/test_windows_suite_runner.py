#!/usr/bin/env python3
"""Exercise the real PowerShell suite runner in isolated, disposable suites.

Run with ``python -B -u tests/test_windows_suite_runner.py``. PowerShell is
required; Windows also needs Clang to build one tiny executable fixture. Missing
prerequisites fail this gate rather than silently skipping its regressions.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


RUNNER = Path(__file__).resolve().parent / "suite" / "run_tests.ps1"
SOURCE = b"-- isolated runner fixture; never compiled as FREAK\n"
EXPECTED = b"expected\n"

FAKE_COMPILER = r'''param([string]$Action, [string]$Source)
if ($Action -ne "build") { exit 31 }
Add-Content -LiteralPath $env:FREAK_SUITE_TEST_BUILD_MARKER -Value "build"
$Output = [System.IO.Path]::ChangeExtension($Source, ".exe")
if (Test-Path -LiteralPath $Output) { exit 32 }
switch ($env:FREAK_SUITE_TEST_BUILD_MODE) {
    "fail" { exit 17 }
    "no-output" { exit 0 }
    "success" {
        Copy-Item -LiteralPath $env:FREAK_SUITE_TEST_HELPER -Destination $Output
        exit 0
    }
    "fail-after-output" {
        Copy-Item -LiteralPath $env:FREAK_SUITE_TEST_HELPER -Destination $Output
        exit 17
    }
    default { exit 33 }
}
'''

NATIVE_HELPER = r'''#include <stdio.h>
#include <stdlib.h>
int main(void) {
    const char *marker = getenv("FREAK_SUITE_TEST_EXEC_MARKER");
    const char *status = getenv("FREAK_SUITE_TEST_EXIT_CODE");
    FILE *file = marker ? fopen(marker, "ab") : NULL;
    if (!file) return 34;
    fputs("executed\n", file);
    fclose(file);
    puts("expected");
    return status ? atoi(status) : 0;
}
'''

POSIX_HELPER = b'''#!/bin/sh
printf 'executed\\n' >> "$FREAK_SUITE_TEST_EXEC_MARKER" || exit 34
printf 'expected\\n'
exit "${FREAK_SUITE_TEST_EXIT_CODE:-0}"
'''


class WindowsSuiteRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.powershell = next(
            (path for name in ("powershell.exe", "powershell", "pwsh")
             if (path := shutil.which(name))),
            None,
        )
        if cls.powershell is None:
            raise RuntimeError("PowerShell is required to validate the suite runner")
        cls.helper_temp = tempfile.TemporaryDirectory(prefix="freak suite helper ")
        cls.addClassCleanup(cls.helper_temp.cleanup)
        helper_root = Path(cls.helper_temp.name)
        cls.helper = helper_root / "program.exe"
        if os.name == "nt":
            clang = os.environ.get("FREAK_CLANG") or shutil.which("clang")
            if not clang:
                raise RuntimeError("Clang is required to build the Windows fixture executable")
            source = helper_root / "program.c"
            source.write_text(NATIVE_HELPER, encoding="utf-8")
            result = subprocess.run(
                [clang, "-O0", str(source), "-o", str(cls.helper)],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode or not cls.helper.is_file():
                raise RuntimeError(
                    f"Windows fixture build failed (exit {result.returncode}):\n"
                    f"{result.stdout}\n{result.stderr}"
                )
        else:
            cls.helper.write_bytes(POSIX_HELPER)
            cls.helper.chmod(0o755)

    def setUp(self) -> None:
        self.fixture_temp = tempfile.TemporaryDirectory(prefix="freak suite fixture ")
        self.addCleanup(self.fixture_temp.cleanup)
        self.repo = Path(self.fixture_temp.name) / "repo with spaces"
        self.suite = self.repo / "tests" / "suite"
        self.suite.mkdir(parents=True)
        self.runner = self.suite / "run_tests.ps1"
        shutil.copyfile(RUNNER, self.runner)
        self.compiler = self.repo / "compiler.ps1"
        self.compiler.write_text(FAKE_COMPILER, encoding="utf-8")
        self.source = self.suite / "01_fixture.fk"
        self.source.write_bytes(SOURCE)
        self.expected = self.suite / "01_fixture.expected"
        self.expected.write_bytes(EXPECTED)
        self.binary = self.source.with_suffix(".exe")
        self.exec_marker = self.repo / "program-ran.txt"
        self.build_marker = self.repo / "compiler-ran.txt"

    def put_stale_binary(self) -> None:
        shutil.copyfile(self.helper, self.binary)
        if os.name != "nt":
            self.binary.chmod(0o755)
        with self.binary.open("ab") as stream:
            stream.write(b"\n# stale generation\n")

    def run_suite(self, mode: str, *, program_exit: int = 0) -> subprocess.CompletedProcess[str]:
        expected_present = self.expected.exists()
        environment = os.environ.copy()
        environment.update({
            "FREAK_SUITE_TEST_BUILD_MODE": mode,
            "FREAK_SUITE_TEST_HELPER": str(self.helper),
            "FREAK_SUITE_TEST_EXEC_MARKER": str(self.exec_marker),
            "FREAK_SUITE_TEST_BUILD_MARKER": str(self.build_marker),
            "FREAK_SUITE_TEST_EXIT_CODE": str(program_exit),
        })
        result = subprocess.run(
            [self.powershell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
             "-File", str(self.runner), str(self.compiler)],
            cwd=self.repo, env=environment, capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(self.source.read_bytes(), SOURCE, result.stdout + result.stderr)
        self.assertEqual(self.expected.exists(), expected_present, result.stdout + result.stderr)
        if expected_present:
            self.assertEqual(self.expected.read_bytes(), EXPECTED, result.stdout + result.stderr)
        return result

    def assert_failed_without_execution(self, result: subprocess.CompletedProcess[str]) -> None:
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1, output)
        self.assertIn("FAIL  01_fixture", output)
        self.assertNotIn("PASS  01_fixture", output)
        self.assertFalse(self.exec_marker.exists(), output)

    def test_failed_compiler_cannot_run_stale_executable(self) -> None:
        self.put_stale_binary()
        result = self.run_suite("fail")
        self.assert_failed_without_execution(result)
        self.assertIn("compiler failed, exit 17", result.stdout)
        self.assertTrue(self.build_marker.exists())
        self.assertFalse(self.binary.exists())

    def test_success_without_fresh_output_cannot_run_stale_executable(self) -> None:
        self.put_stale_binary()
        result = self.run_suite("no-output")
        self.assert_failed_without_execution(result)
        self.assertIn("build produced no fresh executable", result.stdout)
        self.assertTrue(self.build_marker.exists())
        self.assertFalse(self.binary.exists())

    def test_failed_compiler_cannot_run_newly_produced_executable(self) -> None:
        result = self.run_suite("fail-after-output")
        self.assert_failed_without_execution(result)
        self.assertIn("compiler failed, exit 17", result.stdout)
        self.assertEqual(self.binary.read_bytes(), self.helper.read_bytes())

    def test_fresh_successful_build_and_matching_output_pass(self) -> None:
        self.put_stale_binary()
        result = self.run_suite("success")
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, output)
        self.assertIn("PASS  01_fixture", output)
        self.assertIn("1 passed, 0 failed, 0 skipped", output)
        self.assertEqual(self.exec_marker.read_bytes(), b"executed\n")
        self.assertEqual(self.binary.read_bytes(), self.helper.read_bytes())

    def test_nonzero_program_exit_fails_even_with_matching_output(self) -> None:
        result = self.run_suite("success", program_exit=9)
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1, output)
        self.assertIn("program failed, exit 9", output)
        self.assertNotIn("PASS  01_fixture", output)
        self.assertEqual(self.exec_marker.read_bytes(), b"executed\n")

    def test_directory_at_output_path_is_preserved_and_rejected(self) -> None:
        self.binary.mkdir()
        authored_file = self.binary / "authored-data.txt"
        authored_file.write_bytes(b"keep me\n")
        result = self.run_suite("success")
        self.assert_failed_without_execution(result)
        self.assertIn("could not remove stale generated output", result.stdout)
        self.assertEqual(authored_file.read_bytes(), b"keep me\n")
        self.assertFalse(self.build_marker.exists())

    def test_missing_expected_output_still_skips_without_touching_binary(self) -> None:
        self.put_stale_binary()
        stale_bytes = self.binary.read_bytes()
        self.expected.unlink()
        result = self.run_suite("success")
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, output)
        self.assertIn("SKIP  01_fixture", output)
        self.assertIn("0 passed, 0 failed, 1 skipped", output)
        self.assertEqual(self.binary.read_bytes(), stale_bytes)
        self.assertFalse(self.build_marker.exists())
        self.assertFalse(self.exec_marker.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
