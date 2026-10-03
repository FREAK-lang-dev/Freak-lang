"""Exact C text-stream expectations retain payload and platform line endings."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("native_stdout_guard", ROOT / "src/compiler/v4/check_v4.py")
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class NativeTextStdout(unittest.TestCase):
    def test_posix_retains_every_character(self):
        for platform in ("linux", "darwin"):
            with self.subTest(platform=platform), patch.object(guard.sys, "platform", platform):
                self.assertEqual(guard.expected_native_stdout("a\nb\r\nc\r"), "a\nb\r\nc\r")

    def test_windows_expands_each_written_lf(self):
        with patch.object(guard.sys, "platform", "win32"):
            self.assertEqual(guard.expected_native_stdout("a\nb\r\nc\r"), "a\r\nb\r\r\nc\r")

    def test_empty_and_utf8_payloads_are_retained(self):
        with patch.object(guard.sys, "platform", "win32"):
            self.assertEqual(guard.expected_native_stdout(""), "")
            self.assertEqual(guard.expected_native_stdout("caf\u00e9 \u65e5\u672c\n"), "caf\u00e9 \u65e5\u672c\r\n")


if __name__ == "__main__":
    unittest.main()
