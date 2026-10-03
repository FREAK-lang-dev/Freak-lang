"""V4 output paths must never replace their source through an existing alias."""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("identity_checks", ROOT / "src/compiler/v4/check_v4.py")
checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checks)
SPEC = importlib.util.spec_from_file_location("identity_build", ROOT / "src/compiler/v4/build_v4.py")
build = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, {"check_v4": checks}):
    SPEC.loader.exec_module(build)

SOURCE_BYTES = b"task main() -> int { give back 0 }\n-- preserve these exact source bytes\r\n"


class SourceOutputIdentity(unittest.TestCase):
    def invoke(self, source, output, emit_llvm, emit_side_effect=None):
        """Exercise the production command without invoking a compiler or linker."""
        arguments = ["build_v4.py", str(source), "-o", str(output)]
        if emit_llvm:
            arguments.append("--emit-llvm")
        stderr = io.StringIO()
        with patch.object(sys, "argv", arguments), \
                patch.object(build.shutil, "which", return_value="clang"), \
                patch.object(build, "host_target", return_value="target"), \
                patch.object(build, "bootstrap", return_value=Path("compiler")) as bootstrap, \
                patch.object(build, "emit_module", return_value="module\n", side_effect=emit_side_effect) as emit, \
                patch.object(build.checks, "run_with_heartbeat", return_value=subprocess.CompletedProcess([], 0, "", "")) as run, \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
            status = build.main()
        return status, stderr.getvalue(), bootstrap.call_count, emit.call_count, run.call_count

    def assert_rejected(self, source, output, emit_llvm, early=True, emit_side_effect=None):
        """Rejection keeps the complete source and every alias intact."""
        result = self.invoke(source, output, emit_llvm, emit_side_effect)
        self.assertEqual(result[0], 1, result)
        self.assertIn("output aliases source file", result[1])
        self.assertEqual(result[2:4], (0, 0) if early else (1, 1))
        self.assertEqual(result[4], 0)
        self.assertEqual(source.read_bytes(), SOURCE_BYTES)
        self.assertEqual(output.read_bytes(), SOURCE_BYTES)

    def test_direct_normalized_and_hardlink_aliases_rejected_before_bootstrap(self):
        """Both output modes reject path spelling and physical-file aliases."""
        for emit_llvm in (False, True):
            for kind in ("direct", "normalized", "hardlink"):
                with self.subTest(emit_llvm=emit_llvm, kind=kind), tempfile.TemporaryDirectory() as temporary:
                    directory = Path(temporary)
                    source = directory / "source.fk"
                    source.write_bytes(SOURCE_BYTES)
                    if kind == "direct":
                        output = source
                    elif kind == "normalized":
                        nested = directory / "nested"
                        nested.mkdir()
                        output = nested / ".." / "source.fk"
                    else:
                        output = directory / "output.ll"
                        os.link(source, output)
                    before = sorted(p.name for p in directory.iterdir())
                    self.assert_rejected(source, output, emit_llvm)
                    self.assertEqual(sorted(p.name for p in directory.iterdir()), before)

    def test_source_and_output_symlink_aliases_rejected(self):
        """Following either input or output symlinks cannot overwrite the target."""
        for emit_llvm in (False, True):
            for kind in ("source", "output", "both"):
                with self.subTest(emit_llvm=emit_llvm, kind=kind), tempfile.TemporaryDirectory() as temporary:
                    directory = Path(temporary)
                    original = directory / "original.fk"
                    original.write_bytes(SOURCE_BYTES)
                    source, output = original, original
                    try:
                        if kind in ("source", "both"):
                            source = directory / "source.fk"
                            source.symlink_to(original.name)
                        if kind in ("output", "both"):
                            output = directory / "output.ll"
                            output.symlink_to(original.name)
                    except (OSError, NotImplementedError) as exc:
                        self.skipTest(f"host does not permit creating symlinks: {exc}")
                    self.assert_rejected(source, output, emit_llvm)
                    self.assertEqual(original.read_bytes(), SOURCE_BYTES)
                    if source != original:
                        self.assertTrue(source.is_symlink())
                    if output != original:
                        self.assertTrue(output.is_symlink())

    def test_case_alias_obeys_actual_filesystem_identity(self):
        """Case aliases are rejected on case-insensitive filesystems only."""
        for emit_llvm in (False, True):
            with self.subTest(emit_llvm=emit_llvm), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                source = directory / "Source.fk"
                source.write_bytes(SOURCE_BYTES)
                output = directory / "source.fk"
                if output.exists() and source.samefile(output):
                    self.assert_rejected(source, output, emit_llvm)
                else:
                    self.assertEqual(self.invoke(source, output, emit_llvm)[0], 0)
                    self.assertEqual(source.read_bytes(), SOURCE_BYTES)

    def test_alias_created_during_compilation_is_rechecked(self):
        """The output identity is checked again before any writing or linking."""
        for emit_llvm in (False, True):
            with self.subTest(emit_llvm=emit_llvm), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                source = directory / "source.fk"
                output = directory / "output.ll"
                source.write_bytes(SOURCE_BYTES)

                def replace_output(*args):
                    """Model an alias introduced after the first successful preflight."""
                    os.link(source, output)
                    return "module\n"

                self.assert_rejected(source, output, emit_llvm, early=False, emit_side_effect=replace_output)

    def test_identity_errors_fail_closed_before_bootstrap(self):
        """Permission and symlink-resolution failures cannot authorize writing."""
        for emit_llvm in (False, True):
            for failure in (PermissionError("identity unavailable"), RuntimeError("symlink loop")):
                with self.subTest(emit_llvm=emit_llvm, failure=type(failure)), tempfile.TemporaryDirectory() as temporary:
                    source = Path(temporary) / "source.fk"
                    output = Path(temporary) / "output.ll"
                    source.write_bytes(SOURCE_BYTES)
                    with patch.object(Path, "resolve", side_effect=failure):
                        result = self.invoke(source, output, emit_llvm)
                    self.assertEqual(result[0], 1, result)
                    self.assertEqual(result[2:], (0, 0, 0))
                    self.assertEqual(source.read_bytes(), SOURCE_BYTES)
                    self.assertFalse(output.exists())

    def test_distinct_missing_or_existing_outputs_remain_supported(self):
        """Safe outputs are not rejected merely for sharing a directory or bytes."""
        for emit_llvm in (False, True):
            for exists in (False, True):
                with self.subTest(emit_llvm=emit_llvm, exists=exists), tempfile.TemporaryDirectory() as temporary:
                    source = Path(temporary) / "source.fk"
                    output = Path(temporary) / "nested" / "output.ll"
                    source.write_bytes(SOURCE_BYTES)
                    if exists:
                        output.parent.mkdir()
                        output.write_bytes(SOURCE_BYTES)
                    result = self.invoke(source, output, emit_llvm)
                    self.assertEqual(result[0], 0, result)
                    self.assertEqual(result[2:], (1, 1, 1))
                    self.assertTrue(output.parent.is_dir())
                    self.assertEqual(source.read_bytes(), SOURCE_BYTES)
                    if emit_llvm:
                        self.assertEqual(output.read_bytes(), b"module\n")

    def test_source_stat_and_output_permission_errors_fail_closed(self):
        """Only a missing output may bypass the physical-identity comparison."""
        for emit_llvm in (False, True):
            for location, failure in (("source", FileNotFoundError("source disappeared")),
                                      ("source", PermissionError("source unavailable")),
                                      ("output", PermissionError("output unavailable"))):
                with self.subTest(emit_llvm=emit_llvm, location=location, failure=type(failure)), tempfile.TemporaryDirectory() as temporary:
                    source = Path(temporary) / "source.fk"
                    output = Path(temporary) / "output.ll"
                    source.write_bytes(SOURCE_BYTES)
                    original_stat = Path.stat
                    source_calls = 0

                    def stat(path, *args, **kwargs):
                        """Allow initial CLI admission, then fail the identity check."""
                        nonlocal source_calls
                        if path == source:
                            source_calls += 1
                            if location == "source" and source_calls > 1:
                                raise failure
                        if path == output and location == "output":
                            raise failure
                        return original_stat(path, *args, **kwargs)

                    with patch.object(Path, "stat", stat):
                        result = self.invoke(source, output, emit_llvm)
                    self.assertEqual(result[0], 1, result)
                    self.assertIn("could not establish source/output identity", result[1])
                    self.assertEqual(result[2:], (0, 0, 0))
                    self.assertEqual(source.read_bytes(), SOURCE_BYTES)
                    self.assertFalse(output.exists())

    def test_real_command_line_rejects_direct_and_hardlink_aliases(self):
        """The public CLI rejects aliases in both modes without touching source bytes."""
        for emit_llvm in (False, True):
            for hardlink in (False, True):
                with self.subTest(emit_llvm=emit_llvm, hardlink=hardlink), tempfile.TemporaryDirectory() as temporary:
                    directory = Path(temporary)
                    source = directory / "source.fk"
                    source.write_bytes(SOURCE_BYTES)
                    output = directory / "output.ll" if hardlink else source
                    if hardlink:
                        os.link(source, output)
                    command = [sys.executable, "-B", str(ROOT / "src/compiler/v4/build_v4.py"),
                               str(source), "-o", str(output)]
                    if emit_llvm:
                        command.append("--emit-llvm")
                    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=20)
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertIn("output aliases source file", result.stderr)
                    self.assertEqual(result.stdout, "")
                    self.assertEqual(source.read_bytes(), SOURCE_BYTES)
                    self.assertEqual(output.read_bytes(), SOURCE_BYTES)


if __name__ == "__main__":
    unittest.main()
