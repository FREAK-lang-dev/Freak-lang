"""Portable inventory names and exact-byte diagnostic freshness controls."""
import hashlib
import importlib.util
from pathlib import Path, PurePosixPath, PureWindowsPath
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('embedded_paths', ROOT / 'tools/embed_diagnostic_cast.py')
embedding = importlib.util.module_from_spec(spec)
spec.loader.exec_module(embedding)


class InventoryPaths(unittest.TestCase):
    def test_windows_and_posix_inventory_names_have_identical_material(self):
        data = b'{"lines":["exact bytes"]}\n'
        class Source:
            def __init__(self, relative): self.relative = relative
            def relative_to(self, root):
                self_root = embedding.DATA
                assert root == self_root
                return self.relative
            def read_bytes(self): return data
        expected = 'packs/freak.json ' + hashlib.sha256(data).hexdigest()
        for kind in (PureWindowsPath, PurePosixPath):
            self.assertEqual(embedding.inventory_fingerprints([Source(kind('packs/freak.json'))]), expected)

    def test_json_bytes_remain_part_of_the_fingerprint(self):
        class Source:
            def __init__(self, data): self.data = data
            def relative_to(self, root): return PureWindowsPath('packs/freak.json')
            def read_bytes(self): return self.data
        self.assertNotEqual(embedding.inventory_fingerprints([Source(b'{}\n')]),
                            embedding.inventory_fingerprints([Source(b'{}\r\n')]))
        self.assertNotEqual(embedding.inventory_fingerprints([Source(b'{"value":1}\n')]),
                            embedding.inventory_fingerprints([Source(b'{"value":2}\n')]))

    def test_checkout_policy_preserves_every_admitted_json_inventory_byte(self):
        paths = [ROOT / 'src/diagnostics/codes.json', ROOT / 'src/diagnostics/easter_eggs.json',
                 ROOT / 'src/diagnostics/resources.json',
                 *sorted((ROOT / 'src/diagnostics/packs').glob('*.json'))]
        for path in paths:
            relative = path.relative_to(ROOT).as_posix()
            actual = subprocess.check_output(['git', '-c', 'core.autocrlf=true', 'cat-file',
                                              '--filters', 'HEAD:' + relative], cwd=ROOT)
            self.assertEqual(actual, path.read_bytes(), relative)

    def test_authoritative_embedded_source_remains_current(self):
        self.assertEqual(embedding.generate(),
                         (ROOT / 'src/diagnostics/embedded_cast.fk').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
