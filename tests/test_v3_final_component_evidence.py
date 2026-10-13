#!/usr/bin/env python3
"""Exercise retained component channels and active context through real children."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from v3_final_release_gate import run_child_gate


PROGRAM = """
import json, os, sys, time
from pathlib import Path
report = Path(sys.argv[2])
report.write_text(json.dumps({
    'matrices': [{'adapter': 'c', 'optimization': 0}],
    'progress': {'outcome': 'running', 'matrix': {'adapter': 'llvm', 'optimization': 2},
                 'phase': 'corpus', 'fixture': 'fragmented-request'}
}))
os.write(1, b'component-out\\n')
os.write(2, b'component-err\\n')
if sys.argv[3] == 'timeout': time.sleep(20)
sys.exit(int(sys.argv[3]) if sys.argv[3] != 'timeout' else 0)
"""


class ComponentEvidence(unittest.TestCase):
    def execute(self, root: Path, mode: str) -> None:
        run_child_gate(label="controlled component", repo=root, cwd=root,
                       env=os.environ.copy(), timeout=1,
                       evidence_dir=root / "evidence",
                       command=[sys.executable, "-u", "-c", PROGRAM,
                                "--report", str(root / "child.json"), mode])

    def retained(self, root: Path, expected: int | None) -> dict:
        prefix = root / "evidence/components/controlled-component"
        value = json.loads(prefix.with_suffix(".json").read_text())
        self.assertEqual(value["component"], "controlled component")
        record, = value["records"]
        self.assertEqual(record["timeout_seconds"], 1)
        if expected is not None:
            self.assertEqual(record["returncode"], expected)
        for channel, token in (("stdout", b"component-out"), ("stderr", b"component-err")):
            raw = prefix.with_suffix("." + channel).read_bytes()
            self.assertIn(token, raw)
            self.assertEqual(record[channel + "_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertTrue(record["raw_files"][channel]["written"])
        snapshot = record["child_report"]
        self.assertEqual(snapshot["completed_matrices"], 1)
        self.assertEqual(snapshot["progress"]["outcome"], "running")
        self.assertEqual(snapshot["progress"]["matrix"], {"adapter": "llvm", "optimization": 2})
        self.assertEqual(snapshot["progress"]["fixture"], "fragmented-request")
        self.assertEqual(snapshot["sha256"], hashlib.sha256((root / "child.json").read_bytes()).hexdigest())
        self.assertFalse(prefix.with_suffix(".json.tmp").exists())
        return record

    def test_timeout_retains_separate_raw_channels_and_active_matrix(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(subprocess.TimeoutExpired) as raised:
                self.execute(root, "timeout")
            record = self.retained(root, None)
            self.assertTrue(record["timed_out"])
            self.assertIsNotNone(record["returncode"])
            self.assertIn(b"component-out", raised.exception.output)
            self.assertIn(b"component-err", raised.exception.stderr)

    def test_success_and_failure_both_retain_actual_status_and_channels(self):
        for status in (0, 7):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                if status:
                    with self.assertRaisesRegex(AssertionError, "failed \\(7\\)"):
                        self.execute(root, str(status))
                else:
                    self.execute(root, str(status))
                record = self.retained(root, status)
                self.assertNotIn("timed_out", record)


if __name__ == "__main__":
    unittest.main()
