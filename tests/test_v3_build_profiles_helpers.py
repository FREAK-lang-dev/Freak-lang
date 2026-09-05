"""Pure fixture tests: no Clang, linker, compiler or native child is launched."""
import json
import os
from pathlib import Path
import runpy
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import v3_build_profiles as profiles


class ControlledLinkerHelpers(unittest.TestCase):
    def setUp(self):
        guard = patch.object(subprocess, "run", side_effect=AssertionError("unexpected child process"))
        guard.start()
        self.addCleanup(guard.stop)
        temporary = tempfile.TemporaryDirectory(prefix="freak-linker-unit-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_trace_keeps_driver_alias_instead_of_symlink_target(self):
        alias = self.root / "ld"
        alias.write_bytes(b"linker fixture")
        with patch.object(Path, "resolve", side_effect=AssertionError("alias resolved away")):
            found = profiles.linker_from_trace(f' "{alias}" "-o" "output"\n')
        self.assertEqual(found, alias.absolute())
        self.assertEqual(found.name, "ld")

    def test_controlled_roles_forward_or_copy_without_relocating_posix_binary(self):
        for platform, names in (("linux", ("ld", "ld.lld")),
                                ("darwin", ("ld", "ld")),
                                ("win32", ("link.exe", "lld-link.exe"))):
            with self.subTest(platform=platform):
                case = self.root / platform
                case.mkdir()
                origin = case / "SDK space ' dollar $"
                origin.mkdir()
                actuals = {role: origin / name for role, name in zip(("off", "thin"), names)}
                for actual in actuals.values():
                    actual.write_bytes(b"original linker bytes")
                calls = []

                def trace(_clang, flags, *, linker_path=None, original_dir=None):
                    role = "thin" if "-flto=thin" in flags else "off"
                    calls.append((role, linker_path, original_dir, flags))
                    if linker_path is None:
                        return actuals[role]
                    self.assertEqual(original_dir, actuals[role].parent)
                    return linker_path.absolute()

                with patch.object(sys, "platform", platform), patch.object(profiles, "trace_linker", side_effect=trace):
                    selected = profiles.controlled_linkers(case, "unused-clang")
                    self.assertEqual(set(selected), {"off", "thin"})
                    self.assertNotEqual(selected["off"][0], selected["thin"][0])
                    for role, (controlled, actual) in selected.items():
                        self.assertEqual(actual, actuals[role])
                        self.assertEqual(controlled.name, actual.name)
                        original_bytes = actual.read_bytes()
                        previous = controlled.read_bytes()
                        override = profiles.linker_override_argument(controlled)
                        prefix = "-fuse-ld=" if platform == "win32" else "--ld-path="
                        self.assertEqual(override, prefix + str(controlled.absolute()))
                        if platform == "win32":
                            self.assertEqual(previous, original_bytes)
                        else:
                            expected = f'#!/bin/sh\nexec {shlex.quote(str(actual))} "$@"\n'
                            self.assertEqual(controlled.read_text(), expected)
                            self.assertEqual(shlex.split(expected.splitlines()[1]), ["exec", str(actual), "$@"])
                        profiles.mutate_fake_linker(controlled, "unit")
                        self.assertNotEqual(controlled.read_bytes(), previous)
                        self.assertEqual(actual.read_bytes(), original_bytes)
                        if platform != "win32":
                            self.assertTrue(controlled.read_text().endswith("# FREAK-LINKER-unit\n"))
                    self.assertEqual(len(calls), 4)
                    thin_flags = calls[2][3]
                    self.assertIn("-fuse-ld=ld" if platform == "darwin" else "-fuse-ld=lld", thin_flags)

    def test_ignored_override_still_fails(self):
        actual = self.root / "ld"
        actual.write_bytes(b"original")
        with patch.object(sys, "platform", "linux"), patch.object(profiles, "trace_linker", return_value=actual):
            with self.assertRaisesRegex(AssertionError, "ignored the controlled linker"):
                profiles.controlled_linkers(self.root, "unused-clang")

    def test_version_identity_keeps_error_status_and_both_streams(self):
        linker = self.root / "ld"
        environment = {"PATH": "original-tools"}
        result = subprocess.CompletedProcess([], 1, b"version banner\n", b"unsupported --version\n")
        with patch.object(subprocess, "run", return_value=result) as launch:
            self.assertEqual(profiles.linker_version_identity(linker, environment),
                             (1, b"version banner\n", b"unsupported --version\n"))
        self.assertEqual(launch.call_args.args[0], [str(linker), "--version"])
        self.assertEqual(launch.call_args.kwargs["env"], environment)
        self.assertEqual(launch.call_args.kwargs["timeout"], 30)

    def test_trace_and_recorder_pass_exact_same_final_override(self):
        for platform, name in (("linux", "ld.lld"), ("darwin", "ld"),
                               ("win32", "link.exe"), ("win32", "ld.lld.exe")):
            with self.subTest(platform=platform, name=name):
                case = self.root / (platform + name)
                case.mkdir()
                selected = case / name
                selected.write_bytes(b"controlled")
                real_clang = case / "clang"
                real_clang.write_bytes(b"never executed")
                flags = ["-flto=thin", "-fuse-ld=ld" if platform == "darwin" else "-fuse-ld=lld"]
                origin = case / "original tools"
                origin.mkdir()
                with patch.object(sys, "platform", platform):
                    override = profiles.linker_override_argument(selected)
                    result = subprocess.CompletedProcess([], 0, f'"{selected}" "-o" "unused"\n', "")
                    with patch.object(subprocess, "run", return_value=result) as launch:
                        self.assertEqual(profiles.trace_linker(str(real_clang), flags, linker_path=selected,
                                                              original_dir=origin), selected.absolute())
                    trace_args = launch.call_args.args[0]
                    self.assertEqual(trace_args[-1], override)
                    self.assertEqual(trace_args[-3:-1], flags)
                    self.assertTrue(launch.call_args.kwargs["env"]["PATH"].startswith(str(origin) + os.pathsep))
                    self.assertEqual(launch.call_args.kwargs["timeout"], 30)
                    _, log = profiles.write_recorder(case, str(real_clang))
                    recorder = case / "record_clang.py"
                    environment = {"FREAK_PROFILE_REAL_CLANG": str(real_clang),
                                   "FREAK_PROFILE_CLANG_LOG": str(log),
                                   "FREAK_PROFILE_LINKER_OVERRIDE": override,
                                   "FREAK_PROFILE_LINKER_ORIGIN": str(origin), "PATH": "preserved-path"}
                    args = ["input with spaces.c", *flags]
                    with patch.dict(os.environ, environment, clear=True), patch.object(sys, "argv", [str(recorder), *args]), patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as launch:
                        with self.assertRaises(SystemExit) as stopped:
                            runpy.run_path(str(recorder), run_name="__main__")
                    self.assertEqual(stopped.exception.code, 0)
                    self.assertEqual(launch.call_args.args[0], [str(real_clang), *args, override])
                    self.assertEqual(launch.call_args.kwargs["env"]["PATH"], str(origin) + os.pathsep + "preserved-path")
                    self.assertEqual(json.loads(log.read_text()), args)


if __name__ == "__main__":
    unittest.main()
