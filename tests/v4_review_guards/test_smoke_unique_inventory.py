"""Reject smoke registrations which cannot satisfy their own unique-output gate."""
import contextlib
import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('smoke_unique_inventory', ROOT / 'src/compiler/v4/check_v4.py')
checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checks)


class UniqueSmokeRegistration(unittest.TestCase):
    def check_rows(self, rows):
        smoke = {'fixture': 'unique.fk', 'expect': [], 'expect_exact': rows,
                 'expect_unique': True}
        with patch.object(checks, 'EXECUTABLE_SMOKES', [smoke]), contextlib.redirect_stdout(io.StringIO()):
            checks.check_smoke_inventory([Path('unique.fk')])

    def test_independent_output_keys_are_admitted(self):
        self.check_rows(['target-linux-c_int=i32', 'target-windows-c_long=i32'])

    def test_distinct_rows_with_the_same_output_key_are_rejected(self):
        with self.assertRaises(SystemExit) as failure:
            self.check_rows(['target=linux key=c_int i32', 'target=windows key=c_long i32'])
        self.assertEqual(failure.exception.code, 1)

    def test_duplicate_full_rows_are_rejected(self):
        with self.assertRaises(SystemExit) as failure:
            self.check_rows(['target-linux-c_int=i32', 'target-linux-c_int=i32'])
        self.assertEqual(failure.exception.code, 1)


if __name__ == '__main__':
    unittest.main()
