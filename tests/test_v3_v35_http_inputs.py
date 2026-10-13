"""Parser provenance controls shared by raw and ordinary-language HTTP gates."""
from pathlib import Path
import tempfile
import unittest

from v3_v35_http import runtime_inputs


class HttpInputs(unittest.TestCase):
    def runtime(self, directory):
        directory.mkdir(parents=True)
        for name in ('freak_runtime.c', 'freak_llvm_runtime.c', 'freak_v35_http.inc'):
            (directory / name).write_text('runtime sentinel\n')

    def vendor(self, directory, content):
        directory.mkdir(parents=True)
        (directory / 'freak_amalgamation.inc').write_text(content)

    def test_repository_parser_is_selected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.runtime(root / 'freakc/runtime')
            self.vendor(root / 'third_party/llhttp', 'repository parser\n')
            runtime, vendor = runtime_inputs(root)
            self.assertEqual(runtime, root / 'freakc/runtime')
            self.assertEqual((vendor / 'freak_amalgamation.inc').read_text(), 'repository parser\n')

    def test_embedded_parser_wins_over_distinct_repository_parser(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.runtime(root / 'freakc/runtime')
            self.vendor(root / 'third_party/llhttp', 'wrong parser\n')
            self.vendor(root / 'freakc/runtime/third_party/llhttp', 'selected parser\n')
            _, vendor = runtime_inputs(root)
            self.assertEqual((vendor / 'freak_amalgamation.inc').read_text(), 'selected parser\n')

    def test_direct_payload_uses_only_its_parser(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / 'payload/runtime'
            self.runtime(runtime)
            self.vendor(root / 'third_party/llhttp', 'outside parser\n')
            self.vendor(runtime / 'third_party/llhttp', 'payload parser\n')
            selected, vendor = runtime_inputs(runtime)
            self.assertEqual(selected, runtime)
            self.assertEqual((vendor / 'freak_amalgamation.inc').read_text(), 'payload parser\n')

    def test_missing_payload_parser_cannot_borrow_external_parser(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / 'payload/runtime'
            self.runtime(runtime)
            self.vendor(root / 'third_party/llhttp', 'outside parser\n')
            with self.assertRaises(FileNotFoundError):
                runtime_inputs(runtime)

    def test_incomplete_embedded_parser_cannot_borrow_repository_parser(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.runtime(root / 'freakc/runtime')
            self.vendor(root / 'third_party/llhttp', 'outside parser\n')
            (root / 'freakc/runtime/third_party/llhttp').mkdir(parents=True)
            with self.assertRaises(FileNotFoundError):
                runtime_inputs(root)


if __name__ == '__main__':
    unittest.main()
