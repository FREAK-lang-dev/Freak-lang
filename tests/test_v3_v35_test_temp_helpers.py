#!/usr/bin/env python3
"""Check exact public-test output framing, including pipe-backed Windows CRLF."""
from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import v3_v35_test_temp as admission
from v3_v35_test_temp import OUTPUT, result_report


class TestTempOutput(unittest.TestCase):
    def report(self, output):
        phase = {"process_status": 2, "exit_code": 0, "encoding": "hex",
                 "timed_out": False, "stdout_hex": output.hex(), "stdout_bytes": len(output),
                 "stderr_hex": "", "stderr_bytes": 0}
        value = {"schema": 1, "error": "", "summary": {"total": 1, "passed": 1, "failed": 0},
                 "cases": [{"name": "temporary_parent", "status": "passed",
                            "build": dict(phase), "run": dict(phase)}]}
        return SimpleNamespace(returncode=0, stdout=json.dumps(value).encode(), stderr=b"")

    def fixture(self, root, windows=None):
        filename = "test_0.exe" if (os.name == "nt" if windows is None else windows) else "test_0"
        return str(root / "freak-tests-probe" / filename).encode()

    def test_lf_and_crlf_accept_the_same_two_exact_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            for windows, newline in ((False, b"\n"), (True, b"\n"), (True, b"\r\n")):
                with self.subTest(windows=windows, newline=newline), \
                        patch.object(admission, "os", SimpleNamespace(name="nt" if windows else "posix")):
                    output = OUTPUT + newline + self.fixture(root, windows) + newline
                    value = result_report(self.report(output), passed=True, selected=root, physical_parent=root)
                    self.assertEqual(bytes.fromhex(value["cases"][0]["run"]["stdout_hex"]), output)

    def test_posix_keeps_its_exact_lf_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            output = OUTPUT + b"\r\n" + self.fixture(root, False) + b"\r\n"
            with patch.object(admission, "os", SimpleNamespace(name="posix")):
                with self.assertRaises(AssertionError):
                    result_report(self.report(output), passed=True, selected=root, physical_parent=root)

    def test_normalization_preserves_strict_output_structure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            path = self.fixture(root)
            for output in (OUTPUT + b"\r" + path + b"\r",
                           OUTPUT + b"\n" + path,
                           OUTPUT + b"\n" + path + b"\nextra\n",
                           b"wrong\n" + path + b"\n",
                           OUTPUT + b"\r\n" + path + b"\r\n\r\n"):
                with self.subTest(output=output):
                    with self.assertRaises(AssertionError):
                        result_report(self.report(output), passed=True, selected=root, physical_parent=root)

    def test_crlf_cannot_admit_an_unrelated_temporary_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            output = OUTPUT + b"\r\n" + self.fixture(root / "unrelated") + b"\r\n"
            with self.assertRaises(AssertionError):
                result_report(self.report(output), passed=True, selected=root, physical_parent=root)


if __name__ == "__main__":
    unittest.main()
