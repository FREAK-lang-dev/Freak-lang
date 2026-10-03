"""Reject false passes in generated owned-word native output evidence."""
from __future__ import annotations

import subprocess
import unittest

from tests.v4_owned_word_codegen import EXPECTED, assert_native_output


class OwnedWordOutputOracle(unittest.TestCase):
    def result(self, stdout: str, status: int = 0, stderr: str = ""):
        return subprocess.CompletedProcess(["owned-word-native"], status, stdout, stderr)

    def test_exact_output_retains_nul_and_utf8_on_every_platform(self):
        for platform in ("linux", "darwin", "win32"):
            for output in EXPECTED.values():
                with self.subTest(platform=platform, output=output):
                    self.assertEqual(assert_native_output(self.result(output), output, platform=platform), output)

    def test_crlf_text_conversion_is_accepted_only_on_windows(self):
        for output in EXPECTED.values():
            converted = output.replace("\n", "\r\n")
            self.assertEqual(assert_native_output(self.result(converted), output, platform="win32"), output)
            for platform in ("linux", "darwin"):
                with self.subTest(platform=platform, output=output), self.assertRaises(RuntimeError):
                    assert_native_output(self.result(converted), output, platform=platform)

    def test_status_stderr_and_extra_bytes_cannot_prove_success(self):
        for platform in ("linux", "darwin", "win32"):
            for output in EXPECTED.values():
                faults = [self.result(output, status=code) for code in (1, 3, 85, 86, 87, -6)]
                faults += [self.result(output, stderr="ownership audit failure\n")]
                faults += [self.result(changed) for changed in
                           ("\0" + output, output + "\0", output + "\n", output + "\r", output + "extra")]
                if "\0" in output:
                    faults.append(self.result(output.replace("\0", "")))
                for result in faults:
                    with self.subTest(platform=platform, result=result), self.assertRaises(RuntimeError):
                        assert_native_output(result, output, platform=platform)


if __name__ == "__main__":
    unittest.main()
