"""Exercise benchmark failures that previously produced false success or hung."""
from __future__ import annotations

import hashlib
import contextlib
import io
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
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


@unittest.skipUnless(sys.platform.startswith("linux"), "Linux pinned ELF symbol reader")
class SymbolToolSelection(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name).resolve()
        self.tool = self.work / "llvm-nm-real"
        self.tool.write_bytes(b"\x7fELF LLVM tool image")
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
            replacement.write_bytes(b"\x7fELF another tool image")
            os.replace(replacement, self.tool)
            self.assertNotEqual(self.tool.stat().st_ino, inode)
            self.assertEqual(os.stat(launch["executable"]).st_ino, inode)
            self.assertEqual(os.read(descriptor, len(original)), original)
            self.assertEqual(launch["image"]["inode"], inode)
            self.assertEqual(launch["image"]["sha256"], hashlib.sha256(original).hexdigest())
        with self.assertRaises(OSError):
            os.fstat(descriptor)

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
        self.assertEqual(len(opened), 1)
        with self.assertRaises(OSError):
            os.fstat(opened[0])

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
            library_source.write_text("int bench_fd_origin(void) { return 313; }\n")
            library = self.work / "libbench_fd_origin.so"
            compiled = self.benchmark.guarded_job(build,
                [clang, "-shared", "-fPIC", str(library_source), "-o", str(library)],
                self.work / "origin-build", "native origin library", 10, 128, 8)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            link_flags = ["-L", str(self.work), "-lbench_fd_origin", "-Wl,-rpath,$ORIGIN"]
        for image, flags in ((self.tool, []), (replacement,
                ['-DIMAGE_MARKER="replacement"', '-DEXPORT_NAME="unverified_export"'])):
            compiled = self.benchmark.guarded_job(build,
                [clang, "-std=c11", *flags, str(source), *link_flags, "-o", str(image)],
                self.work / (image.name + "-build"), "native multicall image", 10, 128, 8)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
        return build, calls, replacement

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
            self.assertEqual(os.fstat(descriptor).st_ino, self.tool.stat().st_ino)
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
        observed_inodes = []
        def restore_pinned_path():
            temporary = self.work / "pinned-restore"
            temporary.write_bytes(pinned_bytes)
            temporary.chmod(0o755)
            os.replace(temporary, self.tool)
        def replace_after_validation(*args, **kwargs):
            descriptor, = kwargs["pass_fds"]
            observed = os.fstat(descriptor)
            self.assertEqual(kwargs["executable"], f"/proc/self/fd/{descriptor}")
            self.assertEqual(observed.st_ino, self.tool.stat().st_ino)
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
