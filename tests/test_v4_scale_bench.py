"""Exercise benchmark failures that previously produced false success or hung."""
from __future__ import annotations

import hashlib
import contextlib
import errno
import io
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
STAGES = ["lex", "parse", "hir", "resolve", "ty", "mir", "borrowck", "codegen", "module"]
LLVM_VERSION = "llvm-nm, compatible with GNU nm\nLLVM version 19.1.7\n"


def synthetic_elf_image(marker=b"LLVM tool image"):
    """Closed ELF header for process-free metadata/FD tests, not executable proof."""
    ident = b"\x7fELF\x02\x01\x01" + b"\0" * 9
    return struct.pack("<16sHHIQQQIHHHHHH", ident, 2, 62, 1, 0, 64, 0, 0,
                       64, 56, 0, 0, 0, 0) + marker


def synthetic_dynamic_elf_image(origin_path):
    """Bounded dynamic metadata for parser tests, without executable code."""
    strings = b"\0" + origin_path.encode("ascii") + b"\0"
    dynamic_offset, strings_offset = 64 + 2 * 56, 64 + 2 * 56 + 4 * 16
    size = strings_offset + len(strings)
    ident = b"\x7fELF\x02\x01\x01" + b"\0" * 9
    header = struct.pack("<16sHHIQQQIHHHHHH", ident, 2, 62, 1, 0, 64, 0, 0,
                         64, 56, 2, 0, 0, 0)
    load = struct.pack("<IIQQQQQQ", 1, 4, 0, 0x400000, 0, size, size, 4096)
    dynamic = struct.pack("<IIQQQQQQ", 2, 6, dynamic_offset,
                          0x400000 + dynamic_offset, 0, 64, 64, 8)
    tags = b"".join(struct.pack("<qQ", tag, value) for tag, value in
                    ((5, 0x400000 + strings_offset), (10, len(strings)), (29, 1), (0, 0)))
    return header + load + dynamic + tags + strings


def synthetic_origin_flags_elf_image(tag, value, *, duplicate=False):
    """Closed flag-only ELF metadata; no executable or loader proof."""
    rows = [(tag, value)] * (2 if duplicate else 1) + [(0, 0)]
    offset, length = 64 + 2 * 56, len(rows) * 16
    size = offset + length
    ident = b"\x7fELF\x02\x01\x01" + b"\0" * 9
    header = struct.pack("<16sHHIQQQIHHHHHH", ident, 2, 62, 1, 0, 64, 0, 0,
                         64, 56, 2, 0, 0, 0)
    load = struct.pack("<IIQQQQQQ", 1, 4, 0, 0x400000, 0, size, size, 4096)
    dynamic = struct.pack("<IIQQQQQQ", 2, 6, offset, 0x400000 + offset, 0, length, length, 8)
    return header + load + dynamic + b"".join(struct.pack("<qQ", *row) for row in rows)


@unittest.skipUnless(sys.platform.startswith("linux"), "Linux pinned ELF symbol reader")
class SymbolToolSelection(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name).resolve()
        self.tool = self.work / "llvm-nm-real"
        self.tool.write_bytes(synthetic_elf_image())
        self.tool.chmod(0o755)
        self.obj = self.work / "module.o"
        self.obj.write_bytes(b"native object")
        spec = importlib.util.spec_from_file_location("symbol_tool_benchmark", ROOT / "v4_scale_bench.py")
        self.benchmark = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.benchmark)

    def launch_kwargs(self, job):
        descriptor, = job.call_args.kwargs["pass_fds"]
        expected = {"executable": f"/proc/self/fd/{descriptor}", "pass_fds": (descriptor,)}
        self.assertEqual(job.call_args.kwargs, expected)
        with self.assertRaises(OSError):
            os.fstat(descriptor)
        return expected

    def test_missing_llvm_reader_fails_without_using_gnu_nm(self):
        with patch.object(self.benchmark.shutil, "which",
                          side_effect=lambda name: "/usr/bin/nm" if name == "nm" else None) as which, \
                patch.object(self.benchmark, "guarded_job") as job:
            with self.assertRaisesRegex(RuntimeError, "llvm-nm is required.*install LLVM tools"):
                self.benchmark.llvm_symbol_tool(None, self.work / "selection", 10)
        which.assert_called_once_with("llvm-nm")
        job.assert_not_called()

    def test_selection_records_actual_canonical_image_and_llvm_version(self):
        alias = self.work / "llvm-nm"
        alias.symlink_to(self.tool)
        result = subprocess.CompletedProcess([], 0, LLVM_VERSION, "")
        with patch.object(self.benchmark.shutil, "which", return_value=str(alias)), \
                patch.object(self.benchmark, "guarded_job", return_value=result) as job:
            selected = self.benchmark.llvm_symbol_tool(None, self.work / "selection", 20)
        self.assertEqual(selected["requested_nm"], str(alias))
        self.assertEqual(selected["selected_nm"], str(alias))
        self.assertEqual(selected["resolved_nm"], str(self.tool))
        self.assertEqual(selected["nm_version"], LLVM_VERSION)
        self.assertEqual(selected["nm_file"]["sha256"], hashlib.sha256(self.tool.read_bytes()).hexdigest())
        job.assert_called_once_with(None, [str(alias), "--version"],
                                    self.work / "selection/tool-version",
                                    "LLVM symbol tool version", 5, 128, 1,
                                    **self.launch_kwargs(job))
        self.assertEqual(json.loads((self.work / "selection/provenance.json").read_text()), selected)

    def test_parent_is_canonicalized_without_resolving_dispatch_leaf(self):
        parent_alias = self.work / "tool-directory-alias"
        parent_alias.symlink_to(self.work, target_is_directory=True)
        alias = self.work / "llvm-nm"
        alias.symlink_to(self.tool)
        requested = parent_alias / alias.name
        result = subprocess.CompletedProcess([], 0, LLVM_VERSION, "")
        with patch.object(self.benchmark.shutil, "which", return_value=str(requested)), \
                patch.object(self.benchmark, "guarded_job", return_value=result) as job:
            selected = self.benchmark.llvm_symbol_tool(None, self.work / "selection", 20)
        self.assertEqual(selected["requested_nm"], str(requested))
        self.assertEqual(selected["selected_nm"], str(alias))
        self.assertEqual(selected["resolved_nm"], str(self.tool))
        self.assertEqual(job.call_args.args[1], [str(alias), "--version"])
        self.launch_kwargs(job)

    def test_name_without_llvm_implementation_is_rejected_before_inventory(self):
        result = subprocess.CompletedProcess([], 0, "GNU nm (GNU Binutils) 2.42\n", "")
        with patch.object(self.benchmark.shutil, "which", return_value=str(self.tool)), \
                patch.object(self.benchmark, "guarded_job", return_value=result) as job:
            with self.assertRaisesRegex(RuntimeError, "does not report an LLVM symbol reader"):
                self.benchmark.defined_symbols(None, self.obj, self.work / "symbols", 10)
        self.assertEqual(job.call_count, 1)
        self.assertEqual(job.call_args.args[1], [str(self.tool), "--version"])
        metadata = json.loads((self.work / "symbols/tool-selection/provenance.json").read_text())
        self.assertEqual(metadata["nm_version"], result.stdout)

    def test_version_permission_error_keeps_pinned_tool_provenance(self):
        error = PermissionError(13, "selected symbol reader cannot execute")
        directory = self.work / "selection"
        with patch.object(self.benchmark.shutil, "which", return_value=str(self.tool)), \
                patch.object(self.benchmark, "guarded_job", side_effect=error) as job, \
                self.assertRaises(RuntimeError) as failure:
            self.benchmark.llvm_symbol_tool(None, directory, 20)
        self.assertIs(failure.exception.__cause__, error)
        self.assertIn("selected symbol reader cannot execute", str(failure.exception))
        self.assertIn("symbol-tool-provenance=", str(failure.exception))
        metadata = json.loads((directory / "provenance.json").read_text())
        self.assertEqual(metadata["requested_nm"], str(self.tool))
        self.assertEqual(metadata["selected_nm"], str(self.tool))
        self.assertEqual(metadata["resolved_nm"], str(self.tool))
        self.assertEqual(metadata["nm_file"]["sha256"], hashlib.sha256(self.tool.read_bytes()).hexdigest())
        self.assertEqual(metadata["nm_version"], "unavailable within unchanged resource limits")
        job.assert_called_once_with(None, [str(self.tool), "--version"],
                                   directory / "tool-version", "LLVM symbol tool version", 5, 128, 1,
                                   **self.launch_kwargs(job))

    def test_version_nonzero_exit_keeps_stderr_and_pinned_provenance(self):
        result = subprocess.CompletedProcess([], 2, LLVM_VERSION, "version loader failed")
        directory = self.work / "selection"
        with patch.object(self.benchmark.shutil, "which", return_value=str(self.tool)), \
                patch.object(self.benchmark, "guarded_job", return_value=result) as job, \
                self.assertRaises(RuntimeError) as failure:
            self.benchmark.llvm_symbol_tool(None, directory, 20)
        self.assertIn("version loader failed", str(failure.exception))
        self.assertIn("symbol-tool-provenance=", str(failure.exception))
        self.assertIsInstance(failure.exception.__cause__, RuntimeError)
        metadata = json.loads((directory / "provenance.json").read_text())
        self.assertEqual(metadata["resolved_nm"], str(self.tool))
        self.assertEqual(metadata["nm_file"]["sha256"], hashlib.sha256(self.tool.read_bytes()).hexdigest())
        self.assertEqual(metadata["nm_version"], "unavailable within unchanged resource limits")
        job.assert_called_once_with(None, [str(self.tool), "--version"],
                                   directory / "tool-version", "LLVM symbol tool version", 5, 128, 1,
                                   **self.launch_kwargs(job))

    def test_missing_frozen_identity_fields_fail_by_name_with_inventory_provenance(self):
        valid = {"requested_nm": str(self.tool), "selected_nm": str(self.tool),
                 "resolved_nm": str(self.tool), "nm_version": LLVM_VERSION,
                 "nm_file": self.benchmark.symbol_file_provenance(self.tool)}
        for missing in ("selected_nm", "resolved_nm", "all"):
            selected = {} if missing == "all" else {key: value for key, value in valid.items() if key != missing}
            directory = self.work / ("missing-identity-" + missing)
            with self.subTest(missing=missing), \
                    patch.object(self.benchmark, "llvm_symbol_tool", side_effect=AssertionError("explicit provenance must not select a new tool")) as selection, \
                    patch.object(self.benchmark.os, "open", side_effect=AssertionError("malformed image must not open")) as opened, \
                    patch.object(self.benchmark, "guarded_job") as job:
                with self.assertRaisesRegex(RuntimeError, "frozen LLVM symbol tool provenance lacks selected/resolved identity") as failure:
                    self.benchmark.defined_symbols(None, self.obj, directory, 10, symbol_tool=selected)
                self.assertIn("symbol-inventory-provenance=", str(failure.exception))
                self.assertIsInstance(failure.exception.__cause__, RuntimeError)
                self.assertIsInstance(failure.exception.__cause__.__cause__, KeyError)
                metadata = json.loads((directory / "provenance.json").read_text())
                self.assertEqual(metadata, {"object": self.benchmark.symbol_file_provenance(self.obj), **selected})
                selection.assert_not_called()
                opened.assert_not_called()
                job.assert_not_called()

    def test_frozen_image_change_stops_before_symbol_reader_execution(self):
        selected = {"requested_nm": str(self.tool), "selected_nm": str(self.tool),
                    "resolved_nm": str(self.tool),
                    "nm_file": self.benchmark.symbol_file_provenance(self.tool),
                    "nm_version": LLVM_VERSION}
        self.tool.write_bytes(b"different executable image")
        with patch.object(self.benchmark, "guarded_job") as job:
            with self.assertRaisesRegex(RuntimeError, "frozen LLVM symbol tool changed"):
                self.benchmark.defined_symbols(None, self.obj, self.work / "symbols", 10,
                                               symbol_tool=selected)
        job.assert_not_called()

    def test_retargeted_alias_rejects_even_identical_new_image_bytes(self):
        alias = self.work / "llvm-nm"
        alias.symlink_to(self.tool)
        selected = {"requested_nm": str(alias), "selected_nm": str(alias),
                    "resolved_nm": str(self.tool),
                    "nm_file": self.benchmark.symbol_file_provenance(self.tool),
                    "nm_version": LLVM_VERSION}
        replacement = self.work / "another-image"
        replacement.write_bytes(self.tool.read_bytes())
        alias.unlink()
        alias.symlink_to(replacement)
        with patch.object(self.benchmark, "guarded_job") as job:
            with self.assertRaisesRegex(RuntimeError, "alias mapping changed"):
                self.benchmark.defined_symbols(None, self.obj, self.work / "symbols", 10,
                                               symbol_tool=selected)
        job.assert_not_called()
        metadata = json.loads((self.work / "symbols/provenance.json").read_text())
        self.assertEqual(metadata["selected_nm"], str(alias))
        self.assertEqual(metadata["resolved_nm"], str(self.tool))

    def test_removed_alias_rejects_while_pinned_image_remains_available(self):
        alias = self.work / "llvm-nm"
        alias.symlink_to(self.tool)
        selected = {"requested_nm": str(alias), "selected_nm": str(alias),
                    "resolved_nm": str(self.tool),
                    "nm_file": self.benchmark.symbol_file_provenance(self.tool),
                    "nm_version": LLVM_VERSION}
        alias.unlink()
        with patch.object(self.benchmark, "guarded_job") as job:
            with self.assertRaisesRegex(RuntimeError, "alias mapping became unavailable"):
                self.benchmark.defined_symbols(None, self.obj, self.work / "symbols", 10,
                                               symbol_tool=selected)
        job.assert_not_called()

    def test_version_verifies_alias_mapping_before_execution(self):
        alias = self.work / "llvm-nm"
        alias.symlink_to(self.tool)
        replacement = self.work / "another-image"
        replacement.write_bytes(self.tool.read_bytes())
        original = self.benchmark.symbol_file_provenance

        def retarget_after_image_pin(path):
            metadata = original(path)
            alias.unlink()
            alias.symlink_to(replacement)
            return metadata

        with patch.object(self.benchmark.shutil, "which", return_value=str(alias)), \
                patch.object(self.benchmark, "symbol_file_provenance", side_effect=retarget_after_image_pin), \
                patch.object(self.benchmark, "guarded_job") as job:
            with self.assertRaisesRegex(RuntimeError, "alias mapping changed"):
                self.benchmark.llvm_symbol_tool(None, self.work / "selection", 10)
        job.assert_not_called()

    def test_pinned_selection_keeps_exports_and_unchanged_inventory_limits(self):
        version = subprocess.CompletedProcess([], 0, LLVM_VERSION, "")
        inventory = subprocess.CompletedProcess([], 0,
            "00000000 T main\n00000008 T bench_collision\n00000010 W weak_export\n", "")
        with patch.object(self.benchmark.shutil, "which", return_value=str(self.tool)) as which, \
                patch.object(self.benchmark, "guarded_job", side_effect=[version, inventory]) as job:
            selected = self.benchmark.llvm_symbol_tool(None, self.work / "selection", 10)
            exports = self.benchmark.defined_symbols(None, self.obj, self.work / "symbols", 10,
                                                    symbol_tool=selected)
        which.assert_called_once_with("llvm-nm")
        self.assertEqual(exports, {"main", "bench_collision", "weak_export"})
        self.assertEqual(job.call_count, 2)
        self.assertEqual(job.call_args.args,
            (None, [str(self.tool), "-g", "--defined-only", str(self.obj)],
             self.work / "symbols", "native symbol inventory", 10, 128, 8))
        self.launch_kwargs(job)
        metadata = json.loads((self.work / "symbols/provenance.json").read_text())
        self.assertEqual(metadata["nm_file"], selected["nm_file"])
        self.assertEqual(metadata["object"]["sha256"], hashlib.sha256(self.obj.read_bytes()).hexdigest())

    def test_guarded_job_forwards_bound_image_and_preserves_dispatch_argv0(self):
        alias = self.work / "llvm-nm"
        runner = Mock(return_value=subprocess.CompletedProcess([], 0, LLVM_VERSION, ""))
        self.benchmark.guarded_job(None, [str(alias), "--version"], self.work / "bound",
                                   "bound dispatch", 5, 128, 1, runner=runner,
                                   executable="/proc/self/fd/17", pass_fds=(17,))
        runner.assert_called_once_with([str(alias), "--version"], label="bound dispatch",
                                       timeout_seconds=5, memory_limit_mb=128, output_limit_mb=1,
                                       executable="/proc/self/fd/17", pass_fds=(17,))
        metadata = json.loads((self.work / "bound/command.json").read_text())
        self.assertEqual(metadata["argv0"], str(alias))
        self.assertEqual(metadata["executable"], "/proc/self/fd/17")
        self.assertEqual(metadata["pass_fds"], [17])

    def test_default_guarded_job_does_not_override_executable(self):
        runner = Mock(return_value=subprocess.CompletedProcess([], 0, "", ""))
        self.benchmark.guarded_job(None, [str(self.tool)], self.work / "default",
                                   "default dispatch", 5, 128, 1, runner=runner)
        runner.assert_called_once_with([str(self.tool)], label="default dispatch",
                                       timeout_seconds=5, memory_limit_mb=128, output_limit_mb=1)
        metadata = json.loads((self.work / "default/command.json").read_text())
        self.assertNotIn("executable", metadata)
        self.assertNotIn("pass_fds", metadata)

    def test_pinned_descriptor_survives_atomic_path_replacement_and_closes(self):
        original = self.tool.read_bytes()
        selected = {"selected_nm": str(self.tool), "resolved_nm": str(self.tool),
                    "nm_file": self.benchmark.symbol_file_provenance(self.tool)}
        with self.benchmark.frozen_symbol_tool_launch(selected) as launch:
            descriptor, = launch["pass_fds"]
            inode = os.fstat(descriptor).st_ino
            replacement = self.work / "replacement"
            replacement.write_bytes(synthetic_elf_image(b"another tool image"))
            os.replace(replacement, self.tool)
            self.assertNotEqual(self.tool.stat().st_ino, inode)
            self.assertEqual(os.stat(launch["executable"]).st_ino, inode)
            self.assertEqual(os.read(descriptor, len(original)), original)
            self.assertEqual(launch["image"]["inode"], inode)
            self.assertEqual(launch["image"]["sha256"], hashlib.sha256(original).hexdigest())
        with self.assertRaises(OSError):
            os.fstat(descriptor)

    def test_private_copy_survives_original_inplace_writes_with_frozen_bytes(self):
        import fcntl
        original = self.tool.read_bytes()
        original_stat = self.tool.stat()
        selected = {"selected_nm": str(self.tool), "resolved_nm": str(self.tool),
                    "nm_file": self.benchmark.symbol_file_provenance(self.tool)}
        with self.benchmark.frozen_symbol_tool_launch(selected) as launch:
            descriptor, = launch["pass_fds"]
            self.tool.write_bytes(synthetic_elf_image(b"replacement image"))
            self.assertEqual(self.tool.stat().st_ino, original_stat.st_ino)
            # This byte assertion rejects the prior held-original-inode strategy.
            self.assertEqual(os.read(descriptor, len(original)), original)
            image = launch["image"]
            self.assertEqual(image["sha256"], hashlib.sha256(original).hexdigest())
            self.assertEqual(image["original_image"]["inode"], original_stat.st_ino)
            self.assertNotEqual((image["device"], image["inode"]),
                                (original_stat.st_dev, original_stat.st_ino))
            self.assertEqual(fcntl.fcntl(descriptor, fcntl.F_GETFL) & os.O_ACCMODE, os.O_RDONLY)
            self.assertEqual(Path(image["private_copy"]).stat().st_mode & 0o777, 0o500)
            private_root = Path(image["private_root"])
            self.assertEqual(private_root.stat().st_mode & 0o777, 0o700)
            self.assertFalse(image["sealed"])
        self.assertFalse(private_root.exists())
        with self.assertRaises(OSError):
            os.fstat(descriptor)

    def test_original_writes_between_attestation_and_both_mocked_jobs_keep_copy_identity(self):
        original = self.tool.read_bytes()
        selected = {"selected_nm": str(self.tool), "resolved_nm": str(self.tool),
                    "nm_file": self.benchmark.symbol_file_provenance(self.tool)}
        private_images = []
        def mutate(*args, **kwargs):
            descriptor, = kwargs["pass_fds"]
            self.tool.write_bytes(synthetic_elf_image(b"replacement image"))
            self.assertEqual(os.read(descriptor, len(original)), original)
            self.assertEqual(args[1][0], str(self.tool))
            private_images.append(descriptor)
            return subprocess.CompletedProcess([], 0,
                LLVM_VERSION if args[1][-1] == "--version" else "00000000 T copy_export\n", "")
        with patch.object(self.benchmark.shutil, "which", return_value=str(self.tool)), \
                patch.object(self.benchmark, "guarded_job", side_effect=mutate):
            provenance = self.benchmark.llvm_symbol_tool(None, self.work / "copy-selection", 10)
            self.tool.write_bytes(original)
            exports = self.benchmark.defined_symbols(None, self.obj, self.work / "copy-inventory", 10,
                                                    symbol_tool=provenance)
        self.assertEqual(exports, {"copy_export"})
        self.assertEqual(provenance["nm_file"], selected["nm_file"])
        self.assertEqual(len(private_images), 2)
        for directory in ("copy-selection/tool-version", "copy-inventory"):
            image = json.loads((self.work / directory / "image.json").read_text())
            self.assertEqual(image["sha256"], selected["nm_file"]["sha256"])
            self.assertEqual(image["original_image"]["sha256"], selected["nm_file"]["sha256"])
            self.assertFalse(Path(image["private_root"]).exists())
        for descriptor in private_images:
            with self.assertRaises(OSError):
                os.fstat(descriptor)

    def test_shadow_origin_parser_admits_lookup_paths_and_rejects_escapes_and_bad_frames(self):
        for path in ("$ORIGIN", "${ORIGIN}/../lib", "/usr/lib:$ORIGIN/../plugins"):
            with self.subTest(path=path):
                image = synthetic_dynamic_elf_image(path)
                self.assertEqual(self.benchmark.symbol_elf_origin_paths(io.BytesIO(image), len(image), self.work), [path])
        for path in ("$LIB", "/other/$ORIGIN", "$ORIGIN/../$PLATFORM",
                     "$ORIGIN/" + "../" * len(self.work.parts)):
            with self.subTest(path=path), self.assertRaises(RuntimeError):
                image = synthetic_dynamic_elf_image(path)
                self.benchmark.symbol_elf_origin_paths(io.BytesIO(image), len(image), self.work)
        image = synthetic_dynamic_elf_image("$ORIGIN")
        for invalid in (image[:10], image[:64], image[:-1]):
            with self.subTest(length=len(invalid)), self.assertRaises(RuntimeError):
                self.benchmark.symbol_elf_origin_paths(io.BytesIO(invalid), len(invalid), self.work)

    def test_shadow_origin_spine_keeps_adjacent_parent_paths_and_bounds_names(self):
        with tempfile.TemporaryDirectory() as original, tempfile.TemporaryDirectory() as shadow:
            origin = Path(original)
            (origin / "bin").mkdir()
            (origin / "plugins").mkdir()
            (origin / "plugins/dependency.so").write_bytes(b"external library bytes")
            (origin / "bin/adjacent.so").write_bytes(b"adjacent library bytes")
            tool = origin / "bin/llvm-nm"
            tool.write_bytes(synthetic_elf_image())
            copied, entries = self.benchmark.symbol_shadow_origin(tool, Path(shadow))
            self.assertEqual((copied.parent / "adjacent.so").read_bytes(), b"adjacent library bytes")
            self.assertEqual((copied.parent / "../plugins/dependency.so").read_bytes(), b"external library bytes")
            self.assertGreater(entries, 0)
            self.assertFalse(copied.exists())
        with tempfile.TemporaryDirectory() as shadow, \
                patch.object(Path, "iterdir", return_value=iter([Path("/same-name")] * 2)), \
                self.assertRaisesRegex(RuntimeError, "shadow-origin slot collision"):
            self.benchmark.symbol_shadow_origin(Path("/bin/llvm-nm"), Path(shadow))
        with tempfile.TemporaryDirectory() as shadow, \
                patch.object(Path, "iterdir", return_value=iter(Path("/" + str(n)) for n in range(8193))), \
                self.assertRaisesRegex(RuntimeError, "entry limit exceeded"):
            self.benchmark.symbol_shadow_origin(Path("/bin/llvm-nm"), Path(shadow))

    def test_private_cleanup_failure_preserves_primary_or_fails_by_name(self):
        cleanup = self.benchmark.tempfile.TemporaryDirectory.cleanup
        def clean_then_fail(temporary):
            cleanup(temporary)
            raise OSError(errno.EIO, "private cleanup fault")
        for primary in (None, RuntimeError("original guard limit")):
            with self.subTest(primary=primary), \
                    patch.object(self.benchmark.tempfile.TemporaryDirectory, "cleanup", clean_then_fail), \
                    patch.object(self.benchmark.shutil, "which", return_value=str(self.tool)), \
                    patch.object(self.benchmark, "guarded_job", side_effect=primary,
                                 return_value=subprocess.CompletedProcess([], 0, LLVM_VERSION, "")), \
                    self.assertRaises(RuntimeError) as failure:
                self.benchmark.llvm_symbol_tool(None, self.work / "cleanup", 10)
            if primary is None:
                self.assertIn("private-copy cleanup failed", str(failure.exception))
            else:
                self.assertIs(failure.exception.__cause__, primary)
                self.assertIn("original guard limit", str(failure.exception))
                self.assertEqual(len(primary.__notes__), 1)
                self.assertIn("private-copy cleanup failure", primary.__notes__[0])
        try:
            raise RuntimeError("unrelated caller exception")
        except RuntimeError:
            with patch.object(self.benchmark.tempfile.TemporaryDirectory, "cleanup", clean_then_fail), \
                    patch.object(self.benchmark.shutil, "which", return_value=str(self.tool)), \
                    patch.object(self.benchmark, "guarded_job", return_value=subprocess.CompletedProcess([], 0, LLVM_VERSION, "")), \
                    self.assertRaisesRegex(RuntimeError, "private-copy cleanup failed"):
                self.benchmark.llvm_symbol_tool(None, self.work / "ambient-cleanup", 10)

    def test_private_noexec_storage_fails_before_reader_launch(self):
        with patch.object(self.benchmark.shutil, "which", return_value=str(self.tool)), \
                patch.object(self.benchmark.os, "statvfs", return_value=type("Flags", (), {"f_flag": os.ST_NOEXEC})()), \
                patch.object(self.benchmark, "guarded_job") as job, \
                self.assertRaisesRegex(RuntimeError, "private-copy storage is mounted noexec") as failure:
            self.benchmark.llvm_symbol_tool(None, self.work / "private-noexec", 10)
        self.assertIn("symbol-tool-provenance=", str(failure.exception))
        job.assert_not_called()

    def test_close_cancellation_survives_private_cleanup_fault(self):
        original_close = os.close
        original_cleanup = self.benchmark.tempfile.TemporaryDirectory.cleanup
        for failure_type in (MemoryError, KeyboardInterrupt):
            for malformed_notes in (False, True):
                with self.subTest(exception=failure_type.__name__, malformed_notes=malformed_notes):
                    primary = failure_type("descriptor close cancellation")
                    cause = ValueError("original close cause")
                    primary.__cause__ = cause
                    if malformed_notes:
                        primary.__notes__ = object()
                    closed, private_roots = [], []
                    def close_then_cancel(descriptor):
                        original_close(descriptor)
                        closed.append(descriptor)
                        raise primary
                    def clean_then_fail(temporary):
                        private_roots.append(Path(temporary.name))
                        original_cleanup(temporary)
                        raise OSError(errno.EIO, "secondary private cleanup fault")
                    observed = None
                    with patch.object(self.benchmark.shutil, "which", return_value=str(self.tool)), \
                            patch.object(self.benchmark, "guarded_job", return_value=subprocess.CompletedProcess([], 0, LLVM_VERSION, "")) as job, \
                            patch.object(self.benchmark, "close_symbol_descriptor", side_effect=close_then_cancel) as close, \
                            patch.object(self.benchmark.tempfile.TemporaryDirectory, "cleanup", clean_then_fail):
                        try:
                            self.benchmark.llvm_symbol_tool(None, self.work / "close-cancellation", 10)
                        except BaseException as error:
                            observed = error
                    self.assertIs(observed, primary)
                    self.assertIs(primary.__cause__, cause)
                    self.assertEqual(len(closed), 1)
                    close.assert_called_once_with(closed[0])
                    job.assert_called_once()
                    with self.assertRaises(OSError) as absent:
                        os.fstat(closed[0])
                    self.assertEqual(absent.exception.errno, errno.EBADF)
                    self.assertEqual(len(private_roots), 1)
                    self.assertFalse(private_roots[0].exists())
                    if not malformed_notes:
                        self.assertEqual(len(primary.__notes__), 1)
                        self.assertIn("private-copy cleanup failure: errno=5", primary.__notes__[0])

    def test_original_execute_permission_revocation_stops_both_jobs(self):
        for phase in ("version", "inventory"):
            with self.subTest(phase=phase):
                self.tool.chmod(0o755)
                selected = {"selected_nm": str(self.tool), "resolved_nm": str(self.tool),
                            "nm_file": self.benchmark.symbol_file_provenance(self.tool)}
                self.tool.chmod(0o644)
                self.assertFalse(os.access(self.tool, os.X_OK, effective_ids=True))
                with patch.object(self.benchmark.shutil, "which", return_value=str(self.tool)), \
                        patch.object(self.benchmark, "guarded_job", return_value=subprocess.CompletedProcess([], 0, LLVM_VERSION, "")) as job, \
                        self.assertRaisesRegex(RuntimeError, "execute permission was revoked or unavailable"):
                    if phase == "version":
                        self.benchmark.llvm_symbol_tool(None, self.work / "execute-version", 10)
                    else:
                        self.benchmark.defined_symbols(None, self.obj, self.work / "execute-inventory", 10,
                                                       symbol_tool=selected)
                job.assert_not_called()
                self.assertEqual(self.benchmark.symbol_file_provenance(self.tool)["sha256"],
                                 selected["nm_file"]["sha256"])
        self.tool.chmod(0o755)

    def test_execute_revocation_during_mirror_is_rechecked_before_copy_runs(self):
        original_mirror = self.benchmark.symbol_shadow_origin
        for phase in ("version", "inventory"):
            with self.subTest(phase=phase):
                self.tool.chmod(0o755)
                selected = {"selected_nm": str(self.tool), "resolved_nm": str(self.tool),
                            "nm_file": self.benchmark.symbol_file_provenance(self.tool)}
                def revoke_after_mirror(*args, **kwargs):
                    result = original_mirror(*args, **kwargs)
                    self.tool.chmod(0o644)
                    return result
                with patch.object(self.benchmark.shutil, "which", return_value=str(self.tool)), \
                        patch.object(self.benchmark, "symbol_shadow_origin", side_effect=revoke_after_mirror), \
                        patch.object(self.benchmark, "guarded_job", return_value=subprocess.CompletedProcess([], 0, LLVM_VERSION, "")) as job, \
                        self.assertRaisesRegex(RuntimeError, "execute permission was revoked or unavailable"):
                    if phase == "version":
                        self.benchmark.llvm_symbol_tool(None, self.work / "late-execute-version", 10)
                    else:
                        self.benchmark.defined_symbols(None, self.obj, self.work / "late-execute-inventory", 10,
                                                       symbol_tool=selected)
                job.assert_not_called()
        self.tool.chmod(0o755)

    def test_execute_authorization_uses_opened_inode_after_path_replacement(self):
        original_fdopen = os.fdopen
        for original_executable in (False, True):
            with self.subTest(original_executable=original_executable):
                self.tool.chmod(0o755 if original_executable else 0o644)
                selected = {"selected_nm": str(self.tool), "resolved_nm": str(self.tool),
                            "nm_file": self.benchmark.symbol_file_provenance(self.tool)}
                replacement = self.work / "permission-replacement"
                replacement.write_bytes(self.tool.read_bytes())
                replacement.chmod(0o644 if original_executable else 0o755)
                opened = []
                def replace_after_open(descriptor, *args, **kwargs):
                    opened.append(descriptor)
                    source = original_fdopen(descriptor, *args, **kwargs)
                    os.replace(replacement, self.tool)
                    return source
                with patch.object(self.benchmark.os, "fdopen", side_effect=replace_after_open):
                    if original_executable:
                        with self.benchmark.frozen_symbol_tool_launch(selected) as launch:
                            self.assertEqual(launch["argv0"], str(self.tool))
                            self.assertFalse(os.access(self.tool, os.X_OK, effective_ids=True))
                    else:
                        with self.assertRaisesRegex(RuntimeError, "execute permission was revoked or unavailable"):
                            with self.benchmark.frozen_symbol_tool_launch(selected):
                                self.fail("nonexecutable opened source reached launch")
                        self.assertTrue(os.access(self.tool, os.X_OK, effective_ids=True))
                self.assertEqual(len(opened), 1)
                with self.assertRaises(OSError) as absent:
                    os.fstat(opened[0])
                self.assertEqual(absent.exception.errno, errno.EBADF)
        self.tool.chmod(0o755)

    def test_no_origin_image_skips_busy_ancestor_inventories(self):
        def no_scan(path):
            self.fail("no-origin image scanned sibling directory " + str(path))
        with patch.dict(os.environ, {key: value for key, value in os.environ.items()
                                    if not key.startswith("LD_")}, clear=True), \
                patch.object(Path, "iterdir", no_scan), \
                patch.object(self.benchmark.shutil, "which", return_value=str(self.tool)), \
                patch.object(self.benchmark, "guarded_job", return_value=subprocess.CompletedProcess([], 0, LLVM_VERSION, "")) as job:
            selected = self.benchmark.llvm_symbol_tool(None, self.work / "no-origin", 10)
        job.assert_called_once()
        image = json.loads((self.work / "no-origin/tool-version/image.json").read_text())
        self.assertEqual(image["shadow_entries"], 0)
        self.assertFalse(image["origin_mirror_required"])
        self.assertEqual(image["sha256"], selected["nm_file"]["sha256"])
        self.assertFalse(Path(image["private_root"]).exists())
        # A simulated 8,193-name ancestor must likewise remain unobserved.
        with tempfile.TemporaryDirectory() as shadow, \
                patch.object(Path, "iterdir", return_value=iter(Path("/busy/" + str(n)) for n in range(8193))) as inventory:
            copied, count = self.benchmark.symbol_shadow_origin(self.tool, Path(shadow), uses_origin=False)
            self.assertEqual(count, 0)
            self.assertTrue(copied.parent.is_dir())
            inventory.assert_not_called()

    def test_origin_sources_and_unknown_loader_settings_cannot_take_fast_path(self):
        clean_env = {key: value for key, value in os.environ.items() if not key.startswith("LD_")}
        for name in ("LD_LIBRARY_PATH", "LD_PRELOAD", "LD_AUDIT", "LD_ORIGIN_PATH"):
            with self.subTest(name=name), patch.dict(os.environ, {**clean_env, name: "${ORIGIN}/../lib"}, clear=True):
                self.assertTrue(self.benchmark.symbol_loader_origin(self.tool.parent))
        for name, value in (("LD_LIBRARY_PATH", "$LIB"), ("LD_PRELOAD", "$ORIGIN/../$PLATFORM"),
                            ("LD_UNKNOWN", "${ORIGIN}")):
            with self.subTest(name=name, value=value), patch.dict(os.environ, {**clean_env, name: value}, clear=True), \
                    self.assertRaisesRegex(RuntimeError, "unsupported LLVM symbol reader.*origin"):
                self.benchmark.symbol_loader_origin(self.tool.parent)
        image = bytearray(synthetic_dynamic_elf_image("$ORIGIN/library.so"))
        # Turn RUNPATH into DT_NEEDED: its origin evidence is not a path-list row.
        struct.pack_into("<q", image, 64 + 2 * 56 + 2 * 16, 1)
        evidence = []
        self.assertEqual(self.benchmark.symbol_elf_origin_paths(io.BytesIO(image), len(image), self.work,
                                                              origin_evidence=evidence), [])
        self.assertEqual(evidence, ["$ORIGIN/library.so"])
        for tag in (0x6ffffefb, 0x6ffffefc, 0x7ffffffd, 0x7fffffff):
            struct.pack_into("<q", image, 64 + 2 * 56 + 2 * 16, tag)
            with self.subTest(tag=tag), self.assertRaisesRegex(RuntimeError, "unsupported LLVM symbol reader ELF loader dependency tag"):
                self.benchmark.symbol_elf_origin_paths(io.BytesIO(image), len(image), self.work)

    def test_restrictive_umask_preserves_private_image_and_spine_modes(self):
        original_umask = os.umask
        parser = self.benchmark.symbol_elf_origin_paths
        clean_env = {key: value for key, value in os.environ.items() if not key.startswith("LD_")}
        for origin in (False, True):
            with self.subTest(origin=origin):
                self.tool.write_bytes(synthetic_dynamic_elf_image("$ORIGIN") if origin else synthetic_elf_image())
                selected = {"selected_nm": str(self.tool), "resolved_nm": str(self.tool),
                            "nm_file": self.benchmark.symbol_file_provenance(self.tool)}
                modes, roots = [], []
                def parse(stream, *args, **kwargs):
                    modes.append(os.fstat(stream.fileno()).st_mode & 0o777)
                    self.assertEqual(modes[-1], 0o600)
                    return parser(stream, *args, **kwargs)
                previous = original_umask(0o777)
                try:
                    with patch.dict(os.environ, clean_env, clear=True), \
                            patch.object(self.benchmark.os, "umask", side_effect=AssertionError("production changed caller umask")), \
                            patch.object(self.benchmark, "symbol_elf_origin_paths", side_effect=parse):
                        try:
                            with self.benchmark.frozen_symbol_tool_launch(selected) as launch:
                                image = launch["image"]
                                root, copied = Path(image["private_root"]), Path(image["private_copy"])
                                roots.append(root)
                                self.assertEqual(copied.stat().st_mode & 0o777, 0o500)
                                directory = copied.parent
                                while directory.is_relative_to(root):
                                    self.assertEqual(directory.stat().st_mode & 0o777, 0o700)
                                    directory = directory.parent
                                self.assertEqual(image["origin_mirror_required"], origin)
                        except OSError as error:
                            self.fail(f"private launch failed under restrictive umask: {error}")
                finally:
                    original_umask(previous)
                self.assertEqual(modes, [0o600])
                self.assertEqual(len(roots), 1)
                self.assertFalse(roots[0].exists())

    @contextlib.contextmanager
    def faulting_copy_stream(self, stage, close_error, body_error=None):
        original_fdopen, original_open = os.fdopen, Path.open
        parser = self.benchmark.symbol_elf_origin_paths
        streams, closes = [], []
        class Proxy:
            def __init__(self, raw):
                self.raw = raw
                streams.append(raw)
            def __getattr__(self, name):
                return getattr(self.raw, name)
            def write(self, data):
                if stage == "private writer" and body_error is not None:
                    raise body_error
                return self.raw.write(data)
            def close(self):
                closes.append(self.raw.fileno())
                self.raw.close()
                raise close_error
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.close()
        def source(descriptor, *args, **kwargs):
            raw = original_fdopen(descriptor, *args, **kwargs)
            return Proxy(raw) if stage == "original source" else raw
        def opened(path, mode="r", *args, **kwargs):
            raw = original_open(path, mode, *args, **kwargs)
            if path.name == "image" and ((mode == "xb" and stage == "private writer")
                                         or (mode == "rb" and stage == "private metadata")):
                return Proxy(raw)
            return raw
        def parsed(*args, **kwargs):
            if body_error is not None and stage != "private writer":
                raise body_error
            return parser(*args, **kwargs)
        try:
            with patch.object(self.benchmark.os, "fdopen", side_effect=source), \
                    patch.object(Path, "open", opened), \
                    patch.object(self.benchmark, "symbol_elf_origin_paths", side_effect=parsed):
                yield streams, closes
        finally:
            # Exact predecessor replay can mask the primary but must not leak.
            for raw in streams:
                if not raw.closed:
                    raw.close()

    def test_copy_stream_context_setup_failure_never_acquires_a_stream(self):
        selected = {"selected_nm": str(self.tool), "resolved_nm": str(self.tool),
                    "nm_file": self.benchmark.symbol_file_provenance(self.tool)}
        original_fdopen, original_open = os.fdopen, Path.open
        original_factory = contextlib._GeneratorContextManager
        original_temporary = tempfile.TemporaryDirectory
        for stage in ("original source", "private writer", "private metadata"):
            for phase in ("construction", "early-enter"):
                for failure_type in (MemoryError, KeyboardInterrupt):
                    with self.subTest(stage=stage, phase=phase, failure=failure_type.__name__):
                        primary = failure_type("context setup failed before acquiring its stream")
                        cause = ValueError("original attributed cause")
                        primary.__cause__ = cause
                        streams, roots, fired, closes = [], [], [], []
                        class OwnedStream:
                            def __init__(self, raw, label):
                                self.raw, self.label = raw, label
                                self.descriptor = raw.fileno()
                                streams.append(self)
                            def __getattr__(self, name):
                                return getattr(self.raw, name)
                            def close(self):
                                closes.append(self.label)
                                self.raw.close()
                        def source(descriptor, *args, **kwargs):
                            return OwnedStream(original_fdopen(descriptor, *args, **kwargs), "original source")
                        def opened(path, mode="r", *args, **kwargs):
                            raw = original_open(path, mode, *args, **kwargs)
                            if path.name == "image" and mode in ("xb", "rb"):
                                return OwnedStream(raw, "private writer" if mode == "xb" else "private metadata")
                            return raw
                        def temporary(*args, **kwargs):
                            owner = original_temporary(*args, **kwargs)
                            roots.append(Path(owner.name))
                            return owner
                        def factory(function, args, kwargs):
                            if function.__name__ == "symbol_copy_stream" and args[1] == stage and phase == "construction":
                                fired.append("construction")
                                raise primary
                            return original_factory(function, args, kwargs)
                        stream_code = self.benchmark.symbol_copy_stream.__wrapped__.__code__
                        def trace(frame, event, arg):
                            if (event == "line" and frame.f_code is stream_code
                                    and frame.f_locals.get("stage") == stage and not fired):
                                fired.append("early-enter")
                                raise primary
                            return trace
                        previous_trace = sys.gettrace()
                        try:
                            with patch.object(self.benchmark.os, "fdopen", side_effect=source), \
                                    patch.object(Path, "open", opened), \
                                    patch.object(self.benchmark.tempfile, "TemporaryDirectory", side_effect=temporary), \
                                    patch.object(contextlib, "_GeneratorContextManager", factory), \
                                    patch.object(self.benchmark, "guarded_job") as job:
                                if phase == "early-enter":
                                    sys.settrace(trace)
                                try:
                                    with self.assertRaises(BaseException) as failure:
                                        with self.benchmark.frozen_symbol_tool_launch(selected):
                                            self.fail("failed context setup reached launch")
                                finally:
                                    sys.settrace(previous_trace)
                                self.assertIs(failure.exception, primary)
                                self.assertIs(primary.__cause__, cause)
                                self.assertEqual(fired, [phase])
                                job.assert_not_called()
                            self.assertEqual(len(roots), 1)
                            self.assertFalse(roots[0].exists())
                            # Check before fixture cleanup: the predecessor left
                            # its already-open target alive in the exception path.
                            self.assertTrue(all(stream.raw.closed for stream in streams),
                                            "context setup leaked its acquired stream")
                            for stream in streams:
                                with self.assertRaises(OSError) as absent:
                                    os.fstat(stream.descriptor)
                                self.assertEqual(absent.exception.errno, errno.EBADF)
                            self.assertEqual([stream.label for stream in streams],
                                             [] if stage == "original source" else
                                             ["original source"] if stage == "private writer" else
                                             ["original source", "private writer"])
                            self.assertCountEqual(closes, [stream.label for stream in streams])
                        finally:
                            sys.settrace(previous_trace)
                            for stream in streams:
                                if not stream.raw.closed:
                                    stream.raw.close()

    def test_copy_stream_acquisition_failure_has_no_close_owner(self):
        for failure_type in (OSError, MemoryError, KeyboardInterrupt):
            with self.subTest(failure=failure_type.__name__):
                primary = failure_type("stream acquisition failed")
                cause = ValueError("original attributed cause")
                primary.__cause__ = cause
                opener = Mock(side_effect=primary)
                with self.assertRaises(BaseException) as failure:
                    with self.benchmark.symbol_copy_stream(opener, "unacquired stream"):
                        self.fail("failed acquisition reached body")
                self.assertIs(failure.exception, primary)
                self.assertIs(primary.__cause__, cause)
                opener.assert_called_once_with()
                self.assertFalse(hasattr(primary, "__notes__"))

    def test_copy_stream_close_fault_preserves_primary_and_cancellation(self):
        selected = {"selected_nm": str(self.tool), "resolved_nm": str(self.tool),
                    "nm_file": self.benchmark.symbol_file_provenance(self.tool)}
        for stage in ("original source", "private writer", "private metadata"):
            for failure_type in (RuntimeError, MemoryError, KeyboardInterrupt):
                for bad_notes in (False, True):
                    with self.subTest(stage=stage, failure=failure_type.__name__, bad_notes=bad_notes):
                        primary = failure_type("copy or validation failed first")
                        cause = ValueError("original attributed cause")
                        primary.__cause__ = cause
                        if bad_notes:
                            primary.__notes__ = object()
                        secondary = OSError(errno.EINTR, "already closed " + "x" * 1024)
                        with self.faulting_copy_stream(stage, secondary, primary) as (streams, closes), \
                                self.assertRaises(BaseException) as failure:
                            with self.benchmark.frozen_symbol_tool_launch(selected):
                                self.fail("failed stream reached launch")
                        self.assertIs(failure.exception, primary)
                        self.assertIs(primary.__cause__, cause)
                        self.assertEqual(len(streams), 1)
                        self.assertEqual(len(closes), 1)
                        self.assertTrue(streams[0].closed)
                        if not bad_notes:
                            self.assertEqual(len(primary.__notes__), 1)
                            self.assertIn(stage + " stream close failure: errno=4", primary.__notes__[0])
                            self.assertLessEqual(len(primary.__notes__[0]), 380)

    def test_copy_stream_close_only_faults_are_named_or_keep_cancellation(self):
        selected = {"selected_nm": str(self.tool), "resolved_nm": str(self.tool),
                    "nm_file": self.benchmark.symbol_file_provenance(self.tool)}
        for stage in ("original source", "private writer", "private metadata"):
            for kind in (OSError, MemoryError, KeyboardInterrupt):
                with self.subTest(stage=stage, close_failure=kind.__name__):
                    secondary = kind(errno.EINTR, "already closed") if kind is OSError else kind("close cancellation")
                    with self.faulting_copy_stream(stage, secondary) as (streams, closes), \
                            self.assertRaises(BaseException) as failure:
                        with self.benchmark.frozen_symbol_tool_launch(selected):
                            self.fail("close-only stream failure reached launch")
                    if kind is OSError:
                        self.assertIsInstance(failure.exception, RuntimeError)
                        self.assertIn(stage + " stream close failed", str(failure.exception))
                        self.assertIs(failure.exception.__cause__, secondary)
                    else:
                        self.assertIs(failure.exception, secondary)
                    self.assertEqual(len(closes), 1)
                    self.assertEqual(len(streams), 1)
                    self.assertTrue(streams[0].closed)

    def test_origin_dynamic_flags_require_full_mirror_and_closed_rows(self):
        clean_env = {key: value for key, value in os.environ.items() if not key.startswith("LD_")}
        for tag, bit, label in ((30, 1, "DT_FLAGS:DF_ORIGIN"),
                                (0x6ffffffb, 0x80, "DT_FLAGS_1:DF_1_ORIGIN")):
            with self.subTest(tag=tag):
                image = synthetic_origin_flags_elf_image(tag, bit)
                evidence = []
                self.assertEqual(self.benchmark.symbol_elf_origin_paths(io.BytesIO(image), len(image), self.work,
                                                                      origin_evidence=evidence), [])
                self.assertEqual(evidence, [label])
                self.tool.write_bytes(image)
                selected = {"selected_nm": str(self.tool), "resolved_nm": str(self.tool),
                            "nm_file": self.benchmark.symbol_file_provenance(self.tool)}
                with patch.dict(os.environ, clean_env, clear=True), self.benchmark.frozen_symbol_tool_launch(selected) as launch:
                    self.assertTrue(launch["image"]["origin_mirror_required"])
                    self.assertGreater(launch["image"]["shadow_entries"], 0)
                    self.assertIn(label, launch["image"]["origin_evidence"])
                no_origin = synthetic_origin_flags_elf_image(tag, 0)
                evidence = []
                self.assertEqual(self.benchmark.symbol_elf_origin_paths(io.BytesIO(no_origin), len(no_origin), self.work,
                                                                      origin_evidence=evidence), [])
                self.assertEqual(evidence, [])
                for value, duplicate in ((bit, True), (1 << 32, False)):
                    invalid = synthetic_origin_flags_elf_image(tag, value, duplicate=duplicate)
                    with self.subTest(value=value, duplicate=duplicate), \
                            self.assertRaisesRegex(RuntimeError, "unsupported LLVM symbol reader ELF origin flags"):
                        self.benchmark.symbol_elf_origin_paths(io.BytesIO(invalid), len(invalid), self.work)

    def test_shebang_tool_rejected_before_execution(self):
        self.tool.write_bytes(b"#!/usr/bin/env python3\nprint('LLVM version 19')\n")
        with patch.object(self.benchmark.shutil, "which", return_value=str(self.tool)), \
                patch.object(self.benchmark, "guarded_job") as job:
            with self.assertRaisesRegex(RuntimeError, "native ELF image; shebang tools are unsupported"):
                self.benchmark.llvm_symbol_tool(None, self.work / "selection", 10)
        job.assert_not_called()

    def test_nonlinux_execution_rejected_before_descriptor_or_spawn(self):
        with patch.object(self.benchmark.sys, "platform", "win32"), \
                patch.object(self.benchmark.shutil, "which", return_value=str(self.tool)), \
                patch.object(self.benchmark.os, "open") as opened, \
                patch.object(self.benchmark, "guarded_job") as job:
            with self.assertRaisesRegex(RuntimeError, "requires Linux proc-fd support"):
                self.benchmark.llvm_symbol_tool(None, self.work / "selection", 10)
        opened.assert_not_called()
        job.assert_not_called()

    def test_descriptor_exhaustion_keeps_provenance_and_stops_before_spawn(self):
        error = OSError(24, "descriptor limit reached")
        with patch.object(self.benchmark.shutil, "which", return_value=str(self.tool)), \
                patch.object(self.benchmark.os, "open", side_effect=error), \
                patch.object(self.benchmark, "guarded_job") as job:
            with self.assertRaisesRegex(RuntimeError, "descriptor limit reached"):
                self.benchmark.llvm_symbol_tool(None, self.work / "selection", 10)
        job.assert_not_called()
        metadata = json.loads((self.work / "selection/provenance.json").read_text())
        self.assertEqual(metadata["nm_file"]["sha256"], hashlib.sha256(self.tool.read_bytes()).hexdigest())

    def test_missing_proc_fd_namespace_closes_descriptor_before_failure(self):
        original_stat, original_open = os.stat, os.open
        opened = []
        def record_open(*args, **kwargs):
            descriptor = original_open(*args, **kwargs)
            if isinstance(args[0], Path) and args[0].name == self.tool.name:
                opened.append(descriptor)
            return descriptor
        def missing_proc(path, *args, **kwargs):
            if str(path).startswith("/proc/self/fd/"):
                raise FileNotFoundError("proc fd namespace unavailable")
            return original_stat(path, *args, **kwargs)
        with patch.object(self.benchmark.shutil, "which", return_value=str(self.tool)), \
                patch.object(self.benchmark.os, "open", side_effect=record_open), \
                patch.object(self.benchmark.os, "stat", side_effect=missing_proc), \
                patch.object(self.benchmark, "guarded_job") as job:
            with self.assertRaisesRegex(RuntimeError, "requires Linux proc-fd support"):
                self.benchmark.llvm_symbol_tool(None, self.work / "selection", 10)
        job.assert_not_called()
        self.assertEqual(len(opened), 2)
        for descriptor in opened:
            with self.assertRaises(OSError):
                os.fstat(descriptor)

    def test_secondary_close_error_preserves_version_and_inventory_guard_failures(self):
        original_close = os.close
        for phase in ("version", "inventory"):
            with self.subTest(phase=phase):
                primary = RuntimeError("peak process memory 129 MB exceeded limit 128 MB")
                cause = OSError("original guard attribution")
                primary.__cause__ = cause
                closed = []
                def close_then_fail(descriptor):
                    original_close(descriptor)
                    closed.append(descriptor)
                    raise OSError(errno.EINTR, "secondary FD close interrupted " + "x" * 1024)
                selected = {"selected_nm": str(self.tool), "resolved_nm": str(self.tool),
                            "nm_file": self.benchmark.symbol_file_provenance(self.tool)}
                with patch.object(self.benchmark.shutil, "which", return_value=str(self.tool)), \
                        patch.object(self.benchmark, "guarded_job", side_effect=primary) as job, \
                        patch.object(self.benchmark, "close_symbol_descriptor", side_effect=close_then_fail) as close, \
                        self.assertRaises(RuntimeError) as failure:
                    if phase == "version":
                        self.benchmark.llvm_symbol_tool(None, self.work / phase, 10)
                    else:
                        self.benchmark.defined_symbols(None, self.obj, self.work / phase, 10,
                                                       symbol_tool=selected)
                self.assertIs(failure.exception.__cause__, primary)
                self.assertIs(primary.__cause__, cause)
                self.assertIn("129 MB exceeded limit 128 MB", str(failure.exception))
                self.assertEqual(len(primary.__notes__), 1)
                self.assertIn("descriptor close failure: errno=4", primary.__notes__[0])
                self.assertLessEqual(len(primary.__notes__[0]), 350)
                job.assert_called_once()
                close.assert_called_once_with(closed[0])
                with self.assertRaises(OSError) as absent:
                    os.fstat(closed[0])
                self.assertEqual(absent.exception.errno, errno.EBADF)

    def test_close_only_failure_is_named_for_version_and_inventory(self):
        original_close = os.close
        for phase in ("version", "inventory"):
            with self.subTest(phase=phase):
                error = OSError(errno.EINTR, "secondary FD close interrupted")
                closed = []
                def close_then_fail(descriptor):
                    original_close(descriptor)
                    closed.append(descriptor)
                    raise error
                selected = {"selected_nm": str(self.tool), "resolved_nm": str(self.tool),
                            "nm_file": self.benchmark.symbol_file_provenance(self.tool)}
                result = subprocess.CompletedProcess([], 0, LLVM_VERSION if phase == "version"
                                                     else "00000000 T exported\n", "")
                with patch.object(self.benchmark.shutil, "which", return_value=str(self.tool)), \
                        patch.object(self.benchmark, "guarded_job", return_value=result) as job, \
                        patch.object(self.benchmark, "close_symbol_descriptor", side_effect=close_then_fail) as close, \
                        self.assertRaisesRegex(RuntimeError, "LLVM symbol reader descriptor close failed") as failure:
                    if phase == "version":
                        self.benchmark.llvm_symbol_tool(None, self.work / phase, 10)
                    else:
                        self.benchmark.defined_symbols(None, self.obj, self.work / phase, 10,
                                                       symbol_tool=selected)
                self.assertIsInstance(failure.exception.__cause__, RuntimeError)
                self.assertIs(failure.exception.__cause__.__cause__, error)
                self.assertIn("provenance=", str(failure.exception))
                job.assert_called_once()
                close.assert_called_once_with(closed[0])
                with self.assertRaises(OSError) as absent:
                    os.fstat(closed[0])
                self.assertEqual(absent.exception.errno, errno.EBADF)

    def test_close_failure_never_retries_a_reused_descriptor(self):
        original_close, original_open = os.close, os.open
        selected = {"selected_nm": str(self.tool), "resolved_nm": str(self.tool),
                    "nm_file": self.benchmark.symbol_file_provenance(self.tool)}
        reused = []
        def close_and_reuse(descriptor):
            original_close(descriptor)
            replacement = original_open(self.obj, os.O_RDONLY | os.O_CLOEXEC)
            reused.append(replacement)
            self.assertEqual(replacement, descriptor)
            raise OSError(errno.EINTR, "already closed and reused")
        try:
            with patch.object(self.benchmark, "close_symbol_descriptor", side_effect=close_and_reuse) as close:
                with self.assertRaisesRegex(RuntimeError, "LLVM symbol reader descriptor close failed"):
                    with self.benchmark.frozen_symbol_tool_launch(selected):
                        pass
            close.assert_called_once_with(reused[0])
            self.assertEqual(os.read(reused[0], self.obj.stat().st_size), self.obj.read_bytes())
        finally:
            for descriptor in reused:
                original_close(descriptor)

    def test_secondary_note_failure_cannot_replace_primary_exception(self):
        original_close = os.close
        primary = KeyboardInterrupt("original cancellation")
        # BaseException.add_note rejects a malformed existing notes container.
        primary.__notes__ = object()
        selected = {"selected_nm": str(self.tool), "resolved_nm": str(self.tool),
                    "nm_file": self.benchmark.symbol_file_provenance(self.tool)}
        closed = []
        def close_then_fail(descriptor):
            original_close(descriptor)
            closed.append(descriptor)
            raise OSError(errno.EINTR, "secondary FD close interrupted")
        with patch.object(self.benchmark, "close_symbol_descriptor", side_effect=close_then_fail) as close:
            with self.assertRaises(KeyboardInterrupt) as failure:
                with self.benchmark.frozen_symbol_tool_launch(selected):
                    raise primary
        self.assertIs(failure.exception, primary)
        close.assert_called_once_with(closed[0])
        with self.assertRaises(OSError) as absent:
            os.fstat(closed[0])
        self.assertEqual(absent.exception.errno, errno.EBADF)

    @contextlib.contextmanager
    def failed_original_adoption(self, primary, close_effect=None):
        selected = {"selected_nm": str(self.tool), "resolved_nm": str(self.tool),
                    "nm_file": self.benchmark.symbol_file_provenance(self.tool)}
        original_open, original_close = os.open, os.close
        original_temporary = tempfile.TemporaryDirectory
        opened, scratch, owned = [], [], set()
        def record_open(path, *args, **kwargs):
            descriptor = original_open(path, *args, **kwargs)
            if Path(path) == self.tool:
                opened.append(descriptor)
                owned.add(descriptor)
            return descriptor
        def close_original(descriptor):
            # A close attempt transfers this numeric FD out of fixture ownership.
            # It may already be closed and reused before the injected error.
            owned.discard(descriptor)
            (close_effect or original_close)(descriptor)
        def record_temporary(*args, **kwargs):
            temporary = original_temporary(*args, **kwargs)
            scratch.append(Path(temporary.name))
            return temporary
        try:
            with patch.object(self.benchmark.os, "open", side_effect=record_open), \
                    patch.object(self.benchmark.os, "fdopen", side_effect=primary) as adoption, \
                    patch.object(self.benchmark.tempfile, "TemporaryDirectory", side_effect=record_temporary), \
                    patch.object(self.benchmark, "close_symbol_descriptor",
                                 side_effect=close_original) as close, \
                    patch.object(self.benchmark, "guarded_job") as job:
                with self.assertRaises(type(primary)) as failure:
                    with self.benchmark.frozen_symbol_tool_launch(selected):
                        self.fail("failed original adoption reached launch")
            self.assertIs(failure.exception, primary)
            self.assertEqual(len(opened), 1)
            adoption.assert_called_once_with(opened[0], "rb", buffering=0)
            job.assert_not_called()
            self.assertEqual(len(scratch), 1)
            self.assertFalse(scratch[0].exists())
            yield opened[0], close
        finally:
            # Replaying the predecessor must not leak the FD its oracle finds.
            for descriptor in owned:
                try:
                    original_close(descriptor)
                except OSError as error:
                    if error.errno != errno.EBADF:
                        raise

    def test_original_fdopen_failure_closes_raw_descriptor_and_preserves_primary(self):
        for failure_type in (MemoryError, KeyboardInterrupt):
            with self.subTest(exception=failure_type.__name__):
                primary = failure_type("original wrapper construction failed")
                cause = ValueError("prior attributed cause")
                primary.__cause__ = cause
                with self.failed_original_adoption(primary) as (descriptor, close):
                    # The old helper leaks this actual FD after both failures.
                    with self.assertRaises(OSError) as absent:
                        os.fstat(descriptor)
                    self.assertEqual(absent.exception.errno, errno.EBADF)
                    close.assert_called_once_with(descriptor)
                    self.assertIs(primary.__cause__, cause)
                    self.assertFalse(hasattr(primary, "__notes__"))

    def test_original_adoption_close_eintr_keeps_primary_and_bounded_note(self):
        original_close = os.close
        for failure_type in (MemoryError, KeyboardInterrupt):
            with self.subTest(exception=failure_type.__name__):
                primary = failure_type("original wrapper construction failed")
                cause = ValueError("prior attributed cause")
                primary.__cause__ = cause
                def close_then_fail(descriptor):
                    original_close(descriptor)
                    raise OSError(errno.EINTR, "already closed " + "x" * 1024)
                with self.failed_original_adoption(primary, close_then_fail) as (descriptor, close):
                    close.assert_called_once_with(descriptor)
                    with self.assertRaises(OSError) as absent:
                        os.fstat(descriptor)
                    self.assertEqual(absent.exception.errno, errno.EBADF)
                    self.assertIs(primary.__cause__, cause)
                    self.assertEqual(len(primary.__notes__), 1)
                    self.assertIn("original adoption close failure: errno=4", primary.__notes__[0])
                    self.assertLessEqual(len(primary.__notes__[0]), 350)

    def test_original_adoption_close_failure_never_retries_reused_descriptor(self):
        original_close, original_open = os.close, os.open
        primary = KeyboardInterrupt("original wrapper cancellation")
        reused = []
        def close_and_reuse(descriptor):
            original_close(descriptor)
            replacement = original_open(self.obj, os.O_RDONLY | os.O_CLOEXEC)
            reused.append(replacement)
            self.assertEqual(replacement, descriptor)
            raise OSError(errno.EINTR, "already closed and reused")
        try:
            with self.failed_original_adoption(primary, close_and_reuse) as (descriptor, close):
                close.assert_called_once_with(descriptor)
                self.assertEqual(reused, [descriptor])
                self.assertEqual(os.read(reused[0], self.obj.stat().st_size), self.obj.read_bytes())
        finally:
            for descriptor in reused:
                original_close(descriptor)

    def test_original_adoption_fixture_releases_replacement_on_assertion_failure(self):
        original_open, original_close = os.open, os.close
        claimed, replacement = [], []
        def intervening_open(path, flags, *args, **kwargs):
            if Path(path).name == "module.o" and flags == (os.O_RDONLY | os.O_CLOEXEC):
                claimed.append(original_open(path, flags, *args, **kwargs))
                descriptor = original_open(path, flags, *args, **kwargs)
                replacement.append(descriptor)
                return descriptor
            return original_open(path, flags, *args, **kwargs)
        try:
            case = SymbolToolSelection("test_original_adoption_close_failure_never_retries_reused_descriptor")
            with patch.object(os, "open", side_effect=intervening_open):
                result = unittest.TestResult()
                case.run(result)
            self.assertEqual(result.testsRun, 1)
            self.assertEqual(len(result.failures), 1)
            self.assertIn("AssertionError", result.failures[0][1])
            self.assertEqual(result.errors, [])
            self.assertEqual(result.skipped, [])
            self.assertEqual(len(claimed), 1)
            self.assertEqual(len(replacement), 1)
            self.assertNotEqual(claimed[0], replacement[0])
            # The failed nested assertion must release its own replacement and
            # must not retry the original number now owned by this control.
            with self.assertRaises(OSError) as absent:
                os.fstat(replacement[0])
            self.assertEqual(absent.exception.errno, errno.EBADF)
            try:
                os.fstat(claimed[0])
            except OSError as error:
                self.fail(f"fixture closed the intervening owner's descriptor: {error}")
        finally:
            for descriptor in replacement + claimed:
                try:
                    original_close(descriptor)
                except OSError as error:
                    if error.errno != errno.EBADF:
                        raise

    def test_original_adoption_note_failure_cannot_replace_cancellation(self):
        original_close = os.close
        primary = KeyboardInterrupt("original wrapper cancellation")
        primary.__notes__ = object()
        def close_then_fail(descriptor):
            original_close(descriptor)
            raise OSError(errno.EINTR, "already closed")
        with self.failed_original_adoption(primary, close_then_fail) as (descriptor, close):
            close.assert_called_once_with(descriptor)
            with self.assertRaises(OSError) as absent:
                os.fstat(descriptor)
            self.assertEqual(absent.exception.errno, errno.EBADF)

    def native_multicall_images(self, *, with_origin=False):
        clang = shutil.which("clang")
        self.assertIsNotNone(clang, "native multicall regression prerequisite missing: clang; install Clang")
        calls = self.work / "dispatch.txt"
        source = self.work / "multicall.c"
        source.write_text(
            '#include <stdio.h>\n#include <string.h>\n'
            '#ifndef IMAGE_MARKER\n#define IMAGE_MARKER "pinned"\n#endif\n'
            '#ifndef EXPORT_NAME\n#define EXPORT_NAME "multicall_export"\n#endif\n'
            + ('extern int bench_fd_origin(void);\n' if with_origin else
               'static int bench_fd_origin(void) { return 313; }\n') +
            'int main(int argc, char **argv) {\n'
            '    if (bench_fd_origin() != 313) return 72;\n'
            f'    FILE *log = fopen({json.dumps(str(calls))}, "a");\n'
            '    if (!log) return 70;\n'
            '    fprintf(log, "%s|%s|%s\\n", IMAGE_MARKER, argv[0], argc > 1 ? argv[1] : "");\n'
            '    if (fclose(log)) return 71;\n'
            '    const char *leaf = strrchr(argv[0], \'/\');\n'
            '    leaf = leaf ? leaf + 1 : argv[0];\n'
            '    if (strcmp(leaf, "llvm-nm")) {\n'
            '        fputs("wrong multicall dispatch leaf\\n", stderr); return 64;\n'
            '    }\n'
            '    if (argc == 2 && !strcmp(argv[1], "--version")) {\n'
            f'        fputs({json.dumps(LLVM_VERSION)}, stdout); return 0;\n'
            '    }\n'
            '    if (argc == 4 && !strcmp(argv[1], "-g") && !strcmp(argv[2], "--defined-only")) {\n'
            '        printf("00000000 T %s\\n", EXPORT_NAME); return 0;\n'
            '    }\n'
            '    return 65;\n}\n')
        replacement = self.work / "replacement-image"
        build = self.benchmark.load_build(ROOT)
        link_flags = []
        if with_origin:
            library_source = self.work / "origin.c"
            dependency_flags = []
            if with_origin in ("nested", "transitive"):
                dependency_directory = (self.tool.parent.parent / "plugins" if with_origin == "nested"
                                        else self.tool.parent)
                dependency_directory.mkdir(exist_ok=True)
                dependency_source = self.work / "dependency.c"
                dependency_source.write_text("int bench_fd_dependency(void) { return 313; }\n")
                dependency = dependency_directory / "libbench_fd_dependency.so"
                compiled = self.benchmark.guarded_job(build,
                    [clang, "-shared", "-fPIC", str(dependency_source), "-o", str(dependency)],
                    self.work / "dependency-build", "native nested origin dependency", 10, 128, 8)
                self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
                library_source.write_text("extern int bench_fd_dependency(void);\n"
                                          "int bench_fd_origin(void) { return bench_fd_dependency(); }\n")
                dependency_flags = ["-L", str(dependency_directory), "-lbench_fd_dependency"]
                if with_origin == "nested":
                    dependency_flags += ["-Wl,--enable-new-dtags", "-Wl,-rpath,$ORIGIN/../plugins"]
            else:
                library_source.write_text("int bench_fd_origin(void) { return 313; }\n")
            library = self.tool.parent / "libbench_fd_origin.so"
            compiled = self.benchmark.guarded_job(build,
                [clang, "-shared", "-fPIC", str(library_source), *dependency_flags, "-o", str(library)],
                self.work / "origin-build", "native origin library", 10, 128, 8)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            link_flags = ["-L", str(self.tool.parent), "-lbench_fd_origin", "-Wl,--enable-new-dtags", "-Wl,-rpath,$ORIGIN"]
            if with_origin in ("nested", "transitive"):
                link_flags += ["-Wl,-rpath-link," + str(dependency_directory)]
        for image, flags in ((self.tool, []), (replacement,
                ['-DIMAGE_MARKER="replacement"', '-DEXPORT_NAME="unverified_export"'])):
            compiled = self.benchmark.guarded_job(build,
                [clang, "-std=c11", *flags, str(source), *link_flags, "-o", str(image)],
                self.work / (image.name + "-build"), "native multicall image", 10, 128, 8)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
        return build, calls, replacement

    def test_origin_flag_keeps_adjacent_dlopen_plugin(self):
        clang = shutil.which("clang")
        self.assertIsNotNone(clang, "native origin flag regression prerequisite missing: clang; install Clang")
        build = self.benchmark.load_build(ROOT)
        plugin_source = self.work / "origin-flag-plugin.c"
        plugin_source.write_text("int origin_flag_value(void) { return 313; }\n")
        plugin = self.work / "origin-flag-plugin.so"
        result = self.benchmark.guarded_job(build,
            [clang, "-shared", "-fPIC", str(plugin_source), "-o", str(plugin)],
            self.work / "origin-flag-plugin-build", "native origin flag plugin", 30, 128, 8)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        source = self.work / "origin-flag-tool.c"
        source.write_text(
            '#include <dlfcn.h>\n#include <stdio.h>\n#include <string.h>\n'
            'int main(int argc, char **argv) {\n'
            '    void *plugin = dlopen("$ORIGIN/origin-flag-plugin.so", RTLD_NOW);\n'
            '    if (!plugin) { fputs("origin plugin unavailable\\n", stderr); return 71; }\n'
            '    int (*value)(void) = (int (*)(void))dlsym(plugin, "origin_flag_value");\n'
            '    if (!value || value() != 313) return 72;\n'
            '    if (dlclose(plugin)) return 73;\n'
            '    const char *leaf = strrchr(argv[0], \'/\');\n'
            '    if (strcmp(leaf ? leaf + 1 : argv[0], "llvm-nm")) return 64;\n'
            '    if (argc == 2 && !strcmp(argv[1], "--version")) {\n'
            f'        fputs({json.dumps(LLVM_VERSION)}, stdout); return 0;\n'
            '    }\n'
            '    if (argc == 4 && !strcmp(argv[1], "-g") && !strcmp(argv[2], "--defined-only")) {\n'
            '        puts("00000000 T origin_flag_export"); return 0;\n'
            '    }\n'
            '    return 65;\n}\n')
        result = self.benchmark.guarded_job(build,
            [clang, str(source), "-Wl,-z,origin", "-ldl", "-o", str(self.tool)],
            self.work / "origin-flag-tool-build", "native origin flag image", 30, 128, 8)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        alias = self.work / "llvm-nm"
        alias.symlink_to(self.tool)
        with self.tool.open("rb") as image:
            evidence = []
            self.assertEqual(self.benchmark.symbol_elf_origin_paths(image, self.tool.stat().st_size,
                                                                  self.tool.parent, origin_evidence=evidence), [])
        original = self.benchmark.guarded_job(build, [str(alias), "--version"],
            self.work / "origin-flag-original", "original origin flag image", 5, 128, 1,
            executable=str(self.tool))
        self.assertEqual((original.returncode, original.stdout, original.stderr), (0, LLVM_VERSION, ""))
        with patch.object(self.benchmark.shutil, "which", return_value=str(alias)):
            selected = self.benchmark.llvm_symbol_tool(build, self.work / "origin-flag-selection", 10)
        exports = self.benchmark.defined_symbols(build, self.obj, self.work / "origin-flag-symbols", 10,
                                                symbol_tool=selected)
        self.assertEqual(exports, {"origin_flag_export"})
        self.assertTrue(set(evidence) & {"DT_FLAGS:DF_ORIGIN", "DT_FLAGS_1:DF_1_ORIGIN"})
        for directory in ("origin-flag-selection/tool-version", "origin-flag-symbols"):
            image = json.loads((self.work / directory / "image.json").read_text())
            self.assertTrue(image["origin_mirror_required"])
            self.assertTrue(set(image["origin_evidence"]) & {"DT_FLAGS:DF_ORIGIN", "DT_FLAGS_1:DF_1_ORIGIN"})
            self.assertFalse(Path(image["private_root"]).exists())

    def test_original_inplace_mutation_executes_copy_and_rejects_old_held_inode_strategy(self):
        build, calls, replacement = self.native_multicall_images(with_origin=True)
        alias = self.work / "llvm-nm"
        alias.symlink_to(self.tool)
        original_bytes, replacement_bytes = self.tool.read_bytes(), replacement.read_bytes()
        original_identity = self.benchmark.symbol_file_provenance(self.tool)
        original_inode = self.tool.stat().st_ino
        original_job = self.benchmark.guarded_job
        for phase, arguments in (("version", ["--version"]),
                                 ("inventory", ["-g", "--defined-only", str(self.obj)])):
            with self.subTest(phase=phase):
                self.tool.write_bytes(original_bytes)
                # Reproduce the previous strategy: verify an original FD, then
                # mutate that same inode before its exec, leaving metadata stale.
                with self.tool.open("rb") as stream:
                    self.assertEqual(hashlib.sha256(stream.read()).hexdigest(), original_identity["sha256"])
                    self.tool.write_bytes(replacement_bytes)
                    self.assertEqual(self.tool.stat().st_ino, original_inode)
                    self.benchmark.save_json(self.work / ("old-inplace-" + phase) / "image.json",
                                             {"original_image": original_identity,
                                              "inode": original_inode, "strategy": "verified original FD"})
                    result = original_job(build, [str(alias), *arguments],
                        self.work / ("old-inplace-" + phase), "old inplace image negative", 5, 128, 8,
                        executable=f"/proc/self/fd/{stream.fileno()}", pass_fds=(stream.fileno(),))
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(calls.read_text().splitlines()[-1].split("|"),
                                 ["replacement", str(alias), arguments[0]])
                if phase == "inventory":
                    self.assertIn("unverified_export", result.stdout)
                self.tool.write_bytes(original_bytes)
                def mutate_after_copy(*args, **kwargs):
                    self.tool.write_bytes(replacement_bytes)
                    self.assertEqual(self.tool.stat().st_ino, original_inode)
                    return original_job(*args, **kwargs)
                with patch.object(self.benchmark.shutil, "which", return_value=str(alias)), \
                        patch.object(self.benchmark, "guarded_job", side_effect=mutate_after_copy):
                    if phase == "version":
                        self.benchmark.llvm_symbol_tool(build, self.work / "copy-inplace-version", 10)
                        directory = self.work / "copy-inplace-version/tool-version"
                    else:
                        expected = {"selected_nm": str(alias), "resolved_nm": str(self.tool),
                                    "nm_file": original_identity}
                        exports = self.benchmark.defined_symbols(build, self.obj, self.work / "copy-inplace-inventory", 10,
                                                               symbol_tool=expected)
                        self.assertEqual(exports, {"multicall_export"})
                        directory = self.work / "copy-inplace-inventory"
                self.assertEqual(calls.read_text().splitlines()[-1].split("|"),
                                 ["pinned", str(alias), arguments[0]])
                image = json.loads((directory / "image.json").read_text())
                self.assertEqual(image["sha256"], original_identity["sha256"])
                self.assertEqual(image["original_image"]["sha256"], original_identity["sha256"])
                self.assertEqual(image["original_image"]["inode"], original_inode)
                self.assertNotEqual(image["inode"], original_inode)
                self.assertFalse(image["sealed"])
                self.assertFalse(Path(image["private_root"]).exists())
        self.tool.write_bytes(original_bytes)

    def test_private_origin_keeps_adjacent_library_own_parent_origin(self):
        (self.work / "bin").mkdir()
        self.tool = self.work / "bin/llvm-nm-real"
        build, calls, _ = self.native_multicall_images(with_origin="nested")
        alias = self.work / "bin/llvm-nm"
        alias.symlink_to(self.tool)
        direct = self.benchmark.guarded_job(build, [str(alias), "--version"],
            self.work / "original-nested-origin", "original nested origin", 5, 128, 1)
        self.assertEqual(direct.returncode, 0, direct.stdout + direct.stderr)
        with patch.object(self.benchmark.shutil, "which", return_value=str(alias)):
            selected = self.benchmark.llvm_symbol_tool(build, self.work / "private-nested-origin", 10)
        exports = self.benchmark.defined_symbols(build, self.obj, self.work / "private-nested-inventory", 10,
                                                symbol_tool=selected)
        self.assertEqual(exports, {"multicall_export"})
        self.assertEqual([line.split("|") for line in calls.read_text().splitlines()],
                         [["pinned", str(alias), "--version"], ["pinned", str(alias), "--version"],
                          ["pinned", str(alias), "-g"]])

    def test_private_origin_does_not_make_main_runpath_transitive(self):
        (self.work / "bin").mkdir()
        self.tool = self.work / "bin/llvm-nm-real"
        build, calls, _ = self.native_multicall_images(with_origin="transitive")
        alias = self.work / "bin/llvm-nm"
        alias.symlink_to(self.tool)
        direct = self.benchmark.guarded_job(build, [str(alias), "--version"],
            self.work / "original-nontransitive", "original nontransitive origin", 5, 128, 1)
        self.assertEqual(direct.returncode, 127, direct.stdout + direct.stderr)
        self.assertIn("libbench_fd_dependency.so", direct.stderr)
        with patch.object(self.benchmark.shutil, "which", return_value=str(alias)), \
                self.assertRaisesRegex(RuntimeError, "llvm-nm version: exit 127"):
            self.benchmark.llvm_symbol_tool(build, self.work / "private-nontransitive", 10)
        private_stderr = (self.work / "private-nontransitive/tool-version/stderr.txt").read_text()
        self.assertIn("libbench_fd_dependency.so", private_stderr)
        self.assertFalse(calls.exists())

    def test_real_multicall_alias_dispatch_and_resolved_image_negative_control(self):
        build, calls, replacement = self.native_multicall_images()
        alias = self.work / "llvm-nm"
        alias.symlink_to(self.tool)
        negative = self.benchmark.guarded_job(build, [str(self.tool), "--version"],
            self.work / "resolved-negative", "resolved multicall negative", 5, 128, 1)
        self.assertEqual(negative.returncode, 64, negative.stdout + negative.stderr)
        self.assertIn("wrong multicall dispatch leaf", negative.stderr)
        alias.unlink()
        alias.symlink_to(replacement)
        old_path = self.benchmark.guarded_job(build, [str(alias), "--version"],
            self.work / "unbound-alias-negative", "unbound alias negative", 5, 128, 1)
        self.assertEqual(old_path.returncode, 0, old_path.stdout + old_path.stderr)
        self.assertEqual(calls.read_text().splitlines()[-1].split("|"),
                         ["replacement", str(alias), "--version"])
        alias.unlink()
        alias.symlink_to(self.tool)
        original_job = self.benchmark.guarded_job

        def retarget_after_validation(*args, **kwargs):
            self.assertEqual(args[1][0], str(alias))
            descriptor, = kwargs["pass_fds"]
            self.assertEqual(kwargs.get("executable"), f"/proc/self/fd/{descriptor}")
            self.assertNotEqual((os.fstat(descriptor).st_dev, os.fstat(descriptor).st_ino),
                                (self.tool.stat().st_dev, self.tool.stat().st_ino))
            alias.unlink()
            alias.symlink_to(replacement)
            return original_job(*args, **kwargs)

        with patch.object(self.benchmark.shutil, "which", return_value=str(alias)), \
                patch.object(self.benchmark, "guarded_job", side_effect=retarget_after_validation):
            selected = self.benchmark.llvm_symbol_tool(build, self.work / "selection", 10)
        alias.unlink()
        alias.symlink_to(self.tool)
        with patch.object(self.benchmark, "guarded_job", side_effect=retarget_after_validation):
            exports = self.benchmark.defined_symbols(build, self.obj, self.work / "symbols", 10,
                                                    symbol_tool=selected)
        self.assertEqual(exports, {"multicall_export"})
        invocations = [line.split("|") for line in calls.read_text().splitlines()]
        self.assertEqual(invocations, [["pinned", str(self.tool), "--version"],
                                      ["replacement", str(alias), "--version"],
                                      ["pinned", str(alias), "--version"],
                                      ["pinned", str(alias), "-g"]])
        self.assertEqual(selected["nm_file"]["sha256"], hashlib.sha256(self.tool.read_bytes()).hexdigest())
        self.assertNotEqual(selected["nm_file"]["sha256"], hashlib.sha256(replacement.read_bytes()).hexdigest())
        for directory, output in (("selection/tool-version", 1), ("symbols", 8)):
            command = json.loads((self.work / directory / "command.json").read_text())
            self.assertEqual(command["command"][0], str(alias))
            self.assertEqual(command["argv0"], str(alias))
            self.assertEqual(command["executable"], f'/proc/self/fd/{command["pass_fds"][0]}')
            self.assertEqual(command["memory_limit_mib"], 128)
            self.assertEqual(command["output_limit_mib"], output)

    def test_atomic_resolved_replacement_keeps_pinned_image_and_origin_library(self):
        readelf = shutil.which("readelf")
        self.assertIsNotNone(readelf, "native origin regression prerequisite missing: readelf; install binutils")
        build, calls, replacement = self.native_multicall_images(with_origin=True)
        dynamic = self.benchmark.guarded_job(build, [readelf, "--dynamic", str(self.tool)],
            self.work / "origin-dynamic", "native origin metadata", 10, 128, 8)
        self.assertEqual(dynamic.returncode, 0, dynamic.stdout + dynamic.stderr)
        self.assertIn("$ORIGIN", dynamic.stdout)
        self.assertIn("libbench_fd_origin.so", dynamic.stdout)
        alias = self.work / "llvm-nm"
        alias.symlink_to(self.tool)
        pinned_bytes, replacement_bytes = self.tool.read_bytes(), replacement.read_bytes()
        (self.work / "pinned-image").write_bytes(pinned_bytes)
        (self.work / "replacement-bytes").write_bytes(replacement_bytes)
        pinned_hash = hashlib.sha256(pinned_bytes).hexdigest()
        expected = {"selected_nm": str(alias), "resolved_nm": str(self.tool),
                    "nm_file": self.benchmark.symbol_file_provenance(self.tool)}
        self.benchmark.require_frozen_symbol_tool(expected)
        os.replace(replacement, self.tool)
        old_path = self.benchmark.guarded_job(build, [str(alias), "--version"],
            self.work / "resolved-replacement-negative", "resolved replacement negative", 5, 128, 1,
            executable=str(self.tool))
        self.assertEqual(old_path.returncode, 0, old_path.stdout + old_path.stderr)
        self.assertEqual(calls.read_text().splitlines()[-1].split("|"),
                         ["replacement", str(alias), "--version"])
        original_job = self.benchmark.guarded_job
        observed_inodes, original_inodes = [], []
        def restore_pinned_path():
            temporary = self.work / "pinned-restore"
            temporary.write_bytes(pinned_bytes)
            temporary.chmod(0o755)
            os.replace(temporary, self.tool)
        def replace_after_validation(*args, **kwargs):
            descriptor, = kwargs["pass_fds"]
            observed = os.fstat(descriptor)
            self.assertEqual(kwargs["executable"], f"/proc/self/fd/{descriptor}")
            self.assertNotEqual((observed.st_dev, observed.st_ino),
                                (self.tool.stat().st_dev, self.tool.stat().st_ino))
            original_inodes.append(self.tool.stat().st_ino)
            replacement.write_bytes(replacement_bytes)
            replacement.chmod(0o755)
            os.replace(replacement, self.tool)
            self.assertNotEqual(observed.st_ino, self.tool.stat().st_ino)
            self.assertEqual(os.stat(kwargs["executable"]).st_ino, observed.st_ino)
            observed_inodes.append(observed.st_ino)
            return original_job(*args, **kwargs)
        restore_pinned_path()
        with patch.object(self.benchmark.shutil, "which", return_value=str(alias)), \
                patch.object(self.benchmark, "guarded_job", side_effect=replace_after_validation):
            selected = self.benchmark.llvm_symbol_tool(build, self.work / "selection", 10)
        restore_pinned_path()
        with patch.object(self.benchmark, "guarded_job", side_effect=replace_after_validation):
            exports = self.benchmark.defined_symbols(build, self.obj, self.work / "symbols", 10,
                                                    symbol_tool=selected)
        self.assertEqual(exports, {"multicall_export"})
        self.assertEqual([line.split("|") for line in calls.read_text().splitlines()],
                         [["replacement", str(alias), "--version"],
                          ["pinned", str(alias), "--version"], ["pinned", str(alias), "-g"]])
        for index, (directory, output) in enumerate((("selection/tool-version", 1), ("symbols", 8))):
            image = json.loads((self.work / directory / "image.json").read_text())
            command = json.loads((self.work / directory / "command.json").read_text())
            self.assertEqual(image["sha256"], pinned_hash)
            self.assertEqual(image["inode"], observed_inodes[index])
            self.assertEqual(image["original_image"]["inode"], original_inodes[index])
            self.assertEqual(image["original_image"]["sha256"], pinned_hash)
            self.assertFalse(image["sealed"])
            self.assertEqual(command["argv0"], str(alias))
            self.assertEqual(command["executable"], image["executable"])
            self.assertEqual(command["memory_limit_mib"], 128)
            self.assertEqual(command["output_limit_mib"], output)


class FrozenRuntimeInventory(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.repo = self.work / "repo"
        from freakc.v4_native_runtime import SOURCE_NAMES, HEADER_NAMES
        self.sources, self.headers = SOURCE_NAMES, HEADER_NAMES
        runtime = self.repo / "freakc/runtime"
        runtime.mkdir(parents=True)
        for name in (*self.sources, *self.headers):
            (runtime / name).write_text(f"frozen contents for {name}\n")
        original = self.repo / "build/v4_smoke/build_llvm.fk.c"
        original.parent.mkdir(parents=True)
        original.write_text("original compiler\n")
        spec = importlib.util.spec_from_file_location("frozen_runtime_benchmark", ROOT / "v4_scale_bench.py")
        self.benchmark = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.benchmark)
        self.build = SimpleNamespace(checks=SimpleNamespace(run_with_heartbeat=object()),
                                     bootstrap=lambda clang: None)
        self.jobs = []

        def job(build, command, directory, label, *args, **kwargs):
            self.jobs.append(command)
            if "-o" in command:
                artifact = Path(command[command.index("-o") + 1])
                artifact.write_bytes((artifact.name + " compiled").encode())
            return subprocess.CompletedProcess(command, 0, "test Clang version\n", "")

        self.enterContext(patch.object(self.benchmark, "guarded_job", side_effect=job))
        self.enterContext(patch.object(self.benchmark, "instrument", return_value="measured compiler\n"))
        self.symbol_tool = {"resolved_nm": "verified-test-llvm-nm", "nm_version": LLVM_VERSION,
                            "nm_file": {"sha256": "pinned-test-image"}}
        self.enterContext(patch.object(self.benchmark, "llvm_symbol_tool", return_value=self.symbol_tool))
        self.enterContext(patch.object(self.benchmark.shutil, "which", return_value="test-clang"))
        self.enterContext(patch.object(self.benchmark.subprocess, "check_output", return_value="pinned-head\n"))

    def test_later_runtime_object_collision_stops_before_manifest_publication(self):
        exports = [{f"unique_{i}"} for i in range(len(self.sources))]
        exports[2].add("later_collision")
        exports[5].add("later_collision")
        with patch.object(self.benchmark, "defined_symbols", side_effect=exports) as symbols:
            with self.assertRaisesRegex(RuntimeError, "unexpected runtime symbol collisions.*later_collision"):
                self.benchmark.build_tool(self.repo, self.work / "runs", False, 30, self.build)
        self.assertEqual(symbols.call_count, len(self.sources))
        self.assertFalse(list((self.work / "runs").rglob("*.manifest.json")))

    def test_manifest_freezes_hashes_and_symbols_for_every_runtime_input(self):
        exports = [{f"unique_{i}"} for i in range(len(self.sources))]
        with patch.object(self.benchmark, "defined_symbols", side_effect=exports):
            tool, manifest = self.benchmark.build_tool(self.repo, self.work / "runs", False, 30, self.build)
        self.assertEqual(len(manifest["runtime_objects"]), 6)
        self.assertEqual(set(manifest["runtime_hashes"]), set((*self.sources, *self.headers)))
        self.assertEqual(len(manifest["runtime_hashes"]), 12)
        self.assertEqual(manifest["runtime_symbols"], [f"unique_{i}" for i in range(6)])
        self.assertEqual(manifest["runtime_collisions"], [])
        self.assertEqual(manifest["symbol_tool"], self.symbol_tool)
        for name, digest in manifest["runtime_hashes"].items():
            frozen = tool.parent / "runtime" / name
            self.assertEqual(digest, hashlib.sha256(frozen.read_bytes()).hexdigest())
            (self.repo / "freakc/runtime" / name).write_text("source changed after freezing\n")
            self.assertEqual(digest, hashlib.sha256(frozen.read_bytes()).hexdigest())
        self.assertEqual(set(manifest["runtime_object_hashes"]), set(manifest["runtime_objects"]))
        for name, digest in manifest["runtime_object_hashes"].items():
            self.assertEqual(digest, hashlib.sha256(Path(name).read_bytes()).hexdigest())


@unittest.skipUnless(sys.platform.startswith("linux"), "Linux benchmark")
class BenchmarkFailures(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)

    def require_native_tools(self, *names):
        tools = {name: shutil.which(name) for name in names}
        missing = [name for name, path in tools.items() if not path]
        if missing:
            self.fail("native benchmark regression prerequisite missing: "
                      + ", ".join(missing)
                      + "; install LLVM/Clang and binutils before running required native checks")
        return tools

    def test_missing_native_prerequisites_fail_by_name(self):
        with patch.object(shutil, "which", return_value=None), \
                self.assertRaisesRegex(AssertionError,
                    "prerequisite missing: clang, llvm-nm, readelf"):
            self.require_native_tools("clang", "llvm-nm", "readelf")

    def test_native_prerequisite_preflight_returns_selected_tools(self):
        with patch.object(shutil, "which", side_effect=lambda name: "/tools/" + name):
            self.assertEqual(self.require_native_tools("clang", "llvm-nm", "readelf"),
                             {name: "/tools/" + name for name in ("clang", "llvm-nm", "readelf")})

    def test_missing_native_dependencies_stop_feature_checks_before_execution(self):
        for name in ("test_wrong_native_exit_fails_check",
                     "test_duplicate_native_symbol_fails_before_compatibility_link",
                     "test_native_inventory_matches_independent_elf_exports_on_the_same_object",
                     "test_noncolliding_native_exports_link_and_execute"):
            with self.subTest(test=name), \
                    patch.object(shutil, "which", return_value=None), \
                    patch.object(subprocess, "run") as run, \
                    self.assertRaisesRegex(AssertionError, "prerequisite missing: clang, llvm-nm"):
                getattr(self, name)()
            run.assert_not_called()

    def fake_tool(self, body: str, objects=(), symbols=()):
        tool = self.work / "compiler"
        tool.write_text(f"#!{sys.executable}\n" + body)
        tool.chmod(0o755)
        manifest = {"tool_sha256": hashlib.sha256(tool.read_bytes()).hexdigest(),
                    "profile": False, "clang": shutil.which("clang"),
                    "runtime_objects": [str(path) for path in objects],
                    "runtime_object_hashes": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                                              for path in objects},
                    "runtime_symbols": list(symbols)}
        tool.with_suffix(".manifest.json").write_text(json.dumps(manifest))
        return tool

    def emitted_program(self, exit_code=6, collision=False):
        prefix = "".join(f"v4-build-stage={stage} diagnostics=0\n" for stage in STAGES[:-1])
        prefix += "v4-errors=0\n@@V4-MODULE\n"
        triple = "aarch64-unknown-linux-gnu" if platform.machine().lower() in ("aarch64", "arm64") else "x86_64-unknown-linux-gnu"
        module = (f'target triple = "{triple}"\n'
                  f"define i32 @main() {{ ret i32 {exit_code} }}\n")
        if collision:
            module += "define i64 @bench_collision() { ret i64 1 }\n"
        stderr = "".join(f"V4BENCH stage={stage} seconds=0.001 rss_bytes=4096 "
                         "peak_bytes=4096 diagnostics=0\n" for stage in STAGES)
        stderr += "V4BENCH final peak_bytes=4096\n"
        return f"import sys\nprint({prefix + module!r}, end='')\nprint({stderr!r}, end='', file=sys.stderr)\n"

    def run_bench(self, tool, *extra):
        result = subprocess.run([sys.executable, str(ROOT / "v4_scale_bench.py"),
            "--repo", str(ROOT), "--tool", str(tool), "--shapes", "tasks", "--sizes", "1",
            "--work", str(self.work / "runs"), "--json", str(self.work / "result.json"), *extra],
            cwd=ROOT, capture_output=True, text=True, timeout=15)
        return result, json.loads((self.work / "result.json").read_text())

    def test_source_helper_measurements_compile_and_flush_at_exit(self):
        tools = self.require_native_tools("clang")
        spec = importlib.util.spec_from_file_location("v4_benchmark", ROOT / "v4_scale_bench.py")
        benchmark = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(benchmark)
        declarations = """
#include <stdint.h>
typedef struct { const char *data; int64_t len; } freak_word;
static const char *freak_argv[] = {"tool", "source", "target"};
static freak_word freak_word_lit(const char *text) { return (freak_word){text, 0}; }
static int64_t freak_v4_lex_text(int64_t id, freak_word source) { return id; }
static freak_word freak_v4_target_spec_new(freak_word target) { return target; }
static freak_word freak_v4_codegen_llvm_module_text(int64_t codegen, freak_word target) { return (freak_word){0}; }
"""
        for stage, function in (
            ("parse", "parse_stream"), ("hir", "hir_lower_tree"),
            ("resolve", "resolve_lower_hir"), ("ty", "ty_lower_resolve"),
            ("mir", "mir_lower_ty"), ("borrowck", "borrowck_check_mir"),
            ("codegen", "codegen_llvm_lower_owned_mir"),
        ):
            declarations += f"static int64_t freak_v4_{function}(int64_t id, int64_t previous) {{ return id; }}\n"
        for stage in STAGES[:-1]:
            prefix = "codegen_llvm" if stage == "codegen" else stage
            declarations += f"static int64_t freak_v4_{prefix}_diag_count(int64_t id) {{ return 0; }}\n"
        source = declarations + "static void freak_v4_build_llvm_source(freak_word source) {\n"
        source += 'freak_word target_spec = freak_v4_target_spec_new(freak_word_lit("target"));\n'
        source += "\n".join(statement for _, statement, _ in benchmark.INSTRUMENTATION_POINTS)
        source += "\n}\nstatic void freak_v4_build_llvm_run(void) {\n"
        source += "freak_v4_build_llvm_source((freak_word){0});\n}\n"
        source += "int main(void) { freak_v4_build_llvm_run(); return 0; }\n"
        c_path, binary = self.work / "measured.c", self.work / "measured"
        c_path.write_text(benchmark.instrument(source))
        compiled = subprocess.run([
            tools["clang"], "-std=c11", "-D_POSIX_C_SOURCE=200809L",
            "-Werror=implicit-function-declaration", str(c_path), "-o", str(binary),
        ], capture_output=True, text=True, timeout=15)
        self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
        executed = subprocess.run([str(binary)], capture_output=True, text=True, timeout=5)
        self.assertEqual(executed.returncode, 0, executed.stdout + executed.stderr)
        records = executed.stderr.splitlines()
        self.assertEqual([line.split()[1] for line in records[:-1]],
                         [f"stage={stage}" for stage in STAGES])
        self.assertRegex(records[-1], r"^V4BENCH final peak_bytes=[1-9][0-9]*$")

    def test_instrumentation_matches_the_production_bootstrap(self):
        """Catch statement drift in the real generated source before native CI."""
        spec = importlib.util.spec_from_file_location("v4_benchmark_production", ROOT / "v4_scale_bench.py")
        benchmark = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(benchmark)
        build = benchmark.load_build(ROOT)
        generated, uses_ui = build.checks.transpile_fixture(
            build.checks.flattened_crates(), build.checks.V4_ROOT / "tools" / "build_llvm.fk",
        )
        self.assertFalse(uses_ui)
        measured = benchmark.instrument(generated)
        for stage in STAGES:
            self.assertEqual(measured.count(f'v4_bench_report("{stage}",'), 1)
        source_entry = "static void freak_v4_build_llvm_source(freak_word source) {"
        self.assertLess(measured.index("static double v4_bench_clock"), measured.index(source_entry))
        self.assertIn("static void freak_v4_build_llvm_run(void) {\n    atexit(v4_bench_final);", measured)
        module_statement = "freak_word module = freak_v4_codegen_llvm_module_text(codegen, target_spec);"
        self.assertIn(module_statement, measured)
        with self.assertRaisesRegex(RuntimeError, "generated C module boundary changed"):
            benchmark.instrument(generated.replace(module_statement, module_statement.replace("target_spec", "changed_target")))

    def test_diagnostics_fail_even_with_zero_compiler_exit(self):
        tool = self.fake_tool("print('v4-build-stage=lex diagnostics=1')\n")
        result, rows = self.run_bench(tool)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(rows[0]["status"], "diagnostics")

    def test_git_provenance_failure_writes_structured_build_failure(self):
        spec = importlib.util.spec_from_file_location("v4_benchmark_failure", ROOT / "v4_scale_bench.py")
        benchmark = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(benchmark)
        destination = self.work / "result.json"
        error = subprocess.CalledProcessError(128, ["git", "rev-parse", "HEAD"])
        arguments = ["v4_scale_bench.py", "--repo", str(ROOT), "--work", str(self.work / "runs"),
                     "--json", str(destination), "--shapes", "tasks", "--sizes", "1"]
        with patch.object(sys, "argv", arguments), patch.object(benchmark, "load_build", return_value=object()), \
                patch.object(benchmark.subprocess, "check_output", side_effect=error), \
                contextlib.redirect_stderr(io.StringIO()) as captured:
            self.assertEqual(benchmark.main(), 1)
        result = json.loads(destination.read_text())
        self.assertEqual(result["status"], "build-failed")
        self.assertEqual(result["results"], [])
        self.assertIn("cannot record repository head", result["failure"])
        self.assertNotIn("Traceback", captured.getvalue())

    def test_nonfinite_timeout_rejected_before_running_tool(self):
        marker = self.work / "executed"
        tool = self.fake_tool(f"from pathlib import Path\nPath({str(marker)!r}).touch()\n")
        for option in ("--timeout", "--build-timeout"):
            for value in ("nan", "inf"):
                with self.subTest(option=option, value=value):
                    result = subprocess.run([sys.executable, str(ROOT / "v4_scale_bench.py"),
                        "--repo", str(ROOT), "--tool", str(tool), option, value],
                        cwd=ROOT, capture_output=True, text=True, timeout=5)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertFalse(marker.exists())

    def test_quiet_stage_timeout_terminates_descendant(self):
        pid_file = self.work / "child.pid"
        tool = self.fake_tool("import subprocess,time\nfrom pathlib import Path\n"
            "child=subprocess.Popen(['" + sys.executable + "','-c','import time;time.sleep(20)'])\n"
            f"Path({str(pid_file)!r}).write_text(str(child.pid))\ntime.sleep(20)\n")
        result, rows = self.run_bench(tool, "--timeout", "0.5")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(rows[0]["status"], "failed")
        pid = int(pid_file.read_text())
        stat = Path(f"/proc/{pid}/stat")
        if stat.exists():
            state = stat.read_text().split(")", 1)[1].split()[0]
            self.assertEqual(state, "Z", f"descendant {pid} still running")

    def test_wrong_native_exit_fails_check(self):
        self.require_native_tools("clang", "llvm-nm")
        tool = self.fake_tool(self.emitted_program(exit_code=42))
        result, rows = self.run_bench(tool, "--check")
        context = json.dumps(rows, indent=2) + "\n" + result.stdout + result.stderr
        self.assertEqual(result.returncode, 1, context)
        self.assertEqual(rows[0]["status"], "native-check-failed", context)
        self.assertIn("native-mismatch:exit=42", rows[0]["check"], context)

    def test_duplicate_native_symbol_fails_before_compatibility_link(self):
        tools = self.require_native_tools("clang", "llvm-nm")
        source, obj = self.work / "runtime.c", self.work / "runtime.o"
        source.write_text("long bench_collision(void) { return 2; }\n")
        subprocess.run([tools["clang"], "-c", str(source), "-o", str(obj)],
                       check=True, capture_output=True, timeout=10)
        tool = self.fake_tool(self.emitted_program(collision=True), [obj], ["bench_collision"])
        result, rows = self.run_bench(tool, "--check")
        context = json.dumps(rows, indent=2) + "\n" + result.stdout + result.stderr
        self.assertEqual(result.returncode, 1, context)
        self.assertEqual(rows[0].get("status"), "native-check-failed", context)
        self.assertIn("unexpected-symbol-collisions", rows[0]["check"], context)
        self.assertFalse((Path(rows[0]["artifacts"]) / "native").exists())

    def test_native_inventory_matches_independent_elf_exports_on_the_same_object(self):
        tools = self.require_native_tools("clang", "llvm-nm", "readelf")
        spec = importlib.util.spec_from_file_location("native_symbol_benchmark", ROOT / "v4_scale_bench.py")
        benchmark = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(benchmark)
        build = benchmark.load_build(ROOT)
        source, obj = self.work / "exports.c", self.work / "exports.o"
        source.write_text(
            "int global_data = 3;\n"
            "int common_data __attribute__((common));\n"
            "static int local_helper(void) { return 1; }\n"
            "int bench_collision(void) { return local_helper(); }\n"
            "__attribute__((weak)) int weak_export(void) { return global_data; }\n"
            "extern int undefined_export(void);\n"
            "int calls_undefined(void) { return undefined_export(); }\n")
        compiled = benchmark.guarded_job(build,
            [tools["clang"], "-O0", "-c", str(source), "-o", str(obj)],
            self.work / "exports-build", "native export control", 10, 1024)
        self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
        exported = benchmark.defined_symbols(build, obj, self.work / "exports-symbols", 10)
        reference = benchmark.guarded_job(build, [tools["readelf"], "--wide", "--syms", str(obj)],
                                         self.work / "elf-reference", "ELF symbol reference", 10, 128, 8)
        self.assertEqual(reference.returncode, 0, reference.stdout + reference.stderr)
        expected = set()
        for line in reference.stdout.splitlines():
            fields = line.split()
            if len(fields) >= 8 and fields[4] in {"GLOBAL", "WEAK"} and fields[6] != "UND":
                expected.add(fields[7])
        self.assertEqual(expected, {"global_data", "common_data", "bench_collision",
                                    "weak_export", "calls_undefined"})
        self.assertEqual(exported, expected)

    def test_noncolliding_native_exports_link_and_execute(self):
        tools = self.require_native_tools("clang", "llvm-nm")
        source, obj = self.work / "runtime.c", self.work / "runtime.o"
        source.write_text("long other_export(void) { return 2; }\n")
        subprocess.run([tools["clang"], "-c", str(source), "-o", str(obj)],
                       check=True, capture_output=True, timeout=10)
        tool = self.fake_tool(self.emitted_program(), [obj], ["other_export"])
        result, rows = self.run_bench(tool, "--check")
        context = json.dumps(rows, indent=2) + "\n" + result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, context)
        self.assertEqual(rows[0]["status"], "ok", context)
        self.assertEqual(rows[0]["check"], "pass", context)


if __name__ == "__main__":
    unittest.main()
