"""The checked-read probe must always receive the intended file type."""
import importlib.util
import os
from pathlib import Path
import stat
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("source_fifo_guard", ROOT / "src/compiler/v4/check_v4.py")
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


@unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX FIFO")
class SourceFifo(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.fifo = self.root / "fifo"

    def assert_fifo(self):
        self.assertTrue(stat.S_ISFIFO(self.fifo.lstat().st_mode))

    def test_create_and_reuse_fifo(self):
        guard.prepare_source_fifo(self.fifo)
        inode = self.fifo.lstat().st_ino
        guard.prepare_source_fifo(self.fifo)
        self.assert_fifo()
        self.assertEqual(self.fifo.lstat().st_ino, inode)

    def test_replace_regular_file(self):
        self.fifo.write_text("stale")
        guard.prepare_source_fifo(self.fifo)
        self.assert_fifo()

    def test_replace_symlinks_without_touching_targets(self):
        target = self.root / "target"
        target.write_text("preserve")
        for destination in (target, self.root / "missing"):
            self.fifo.symlink_to(destination)
            guard.prepare_source_fifo(self.fifo)
            self.assert_fifo()
            self.assertEqual(target.read_text(), "preserve")
            self.fifo.unlink()

    def test_replace_empty_directory(self):
        self.fifo.mkdir()
        guard.prepare_source_fifo(self.fifo)
        self.assert_fifo()

    def test_preserve_nonempty_directory(self):
        self.fifo.mkdir()
        contents = self.fifo / "preserve"
        contents.write_text("data")
        with self.assertRaises(OSError):
            guard.prepare_source_fifo(self.fifo)
        self.assertEqual(contents.read_text(), "data")


if __name__ == "__main__":
    unittest.main()
