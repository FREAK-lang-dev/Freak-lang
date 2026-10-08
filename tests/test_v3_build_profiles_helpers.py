"""Pure helper fixtures, plus an opt-in genuine Clang display-trace witness.

FREAK_PROFILE_NATIVE_CLANG selects the native compiler; the witness aliases
its actual driver image for bounded -### probes. Ordinary fixtures never
launch a child.
"""
import json
import os
from pathlib import Path
import runpy
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import v3_build_profiles as profiles


def display_token(value):
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$") + '"'


def native_clang_probe(clang, *arguments):
    completed = subprocess.run([str(clang), *arguments], capture_output=True,
                               text=True, encoding="utf-8", timeout=30, check=False)
    assert completed.returncode == 0, (clang, completed.returncode,
                                       completed.stdout, completed.stderr)
    return completed.stdout, completed.stderr


def native_clang_frontend(output):
    frontends = []
    for line in output.splitlines():
        executable = profiles.clang_display_token(line)
        if executable is None:
            continue
        argument = profiles.clang_display_token(executable[1])
        if argument is not None and argument[0] == "-cc1":
            frontends.append(executable[0])
    assert len(frontends) == 1, ("expected one Clang frontend image", output)
    image = Path(frontends[0])
    assert image.is_absolute() and image.is_file(), ("invalid Clang frontend image", image, output)
    return image


def native_clang_driver(clang, resource_dir):
    if sys.platform != "darwin":
        return clang
    # Apple /usr/bin/clang can dispatch by argv[0], so its foo-ld alias would
    # request an unrelated developer tool. Ask the configured compiler itself
    # for the frontend image; never select another installation from PATH.
    arguments = ("-###", "-x", "c", os.devnull, "-o", os.devnull,
                 "-resource-dir", resource_dir)
    selected = "".join(native_clang_probe(clang, *arguments))
    image = native_clang_frontend(selected)
    reported, _ = native_clang_probe(image, "-print-resource-dir")
    actual_resource = Path(reported.strip())
    assert actual_resource.is_absolute() and actual_resource.is_dir(), (image, reported)
    assert actual_resource.samefile(resource_dir), ("Clang resource directory changed", clang,
                                                  image, resource_dir, actual_resource)
    direct = "".join(native_clang_probe(image, *arguments))
    assert native_clang_frontend(direct).samefile(image), ("Clang frontend image changed", image, direct)
    assert profiles.linker_from_trace(direct) == profiles.linker_from_trace(selected), (
        "Clang linker selection changed", clang, image, selected, direct)
    return image


def stage_native_clang_alias(clang, alias):
    """Keep loader dependencies while exposing a genuine compiler alias."""
    if sys.platform == "win32":
        # Windows copies need the selected image's adjacent DLLs; symlinks may
        # require privileges that the native test runner does not have.
        shutil.copy2(clang, alias)
        for companion in clang.resolve().parent.iterdir():
            if companion.is_file() and companion.suffix.lower() == ".dll":
                shutil.copy2(companion, alias.parent / companion.name)
        return []
    # Resolving executable-relative shared libraries must keep the original
    # image location. Clang still prints argv[0] with this driver flag.
    alias.symlink_to(clang)
    return ["-no-canonical-prefixes"]


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
            found = profiles.linker_from_trace(f' {display_token(alias)} "-o" "output"\n')
        self.assertEqual(found, alias.absolute())
        self.assertEqual(found.name, "ld")

    def test_linker_named_compiler_frontends_are_skipped(self):
        compiler = self.root / "foo-ld"
        linker = self.root / "ld"
        compiler.write_bytes(b"compiler fixture")
        linker.write_bytes(b"linker fixture")
        for role in ("-cc1", "-cc1as"):
            for argument in (role, f'"{role}"'):
                with self.subTest(role=role, argument=argument):
                    trace = f' {display_token(compiler)} {argument} "input.c"\n {display_token(linker)} "-o" "output"\n'
                    self.assertEqual(profiles.linker_from_trace(trace), linker.absolute())
        # Role is the immediate argument, not arbitrary later linker text.
        self.assertEqual(profiles.linker_from_trace(f'{display_token(linker)} "-o" "-cc1"\n'), linker.absolute())

    def test_clang_display_escapes_preserve_the_exact_linker_path(self):
        spelling = 'SDK dollar $ é 日本'
        if os.name != "nt":
            spelling += ' quote " slash \\'
        directory = self.root / spelling
        directory.mkdir()
        linker = directory / "ld"
        linker.write_bytes(b"escaped linker fixture")
        self.assertEqual(profiles.linker_from_trace(f' {display_token(linker)} "-o" "output"\n'), linker.absolute())

    def test_windows_display_tokens_decode_without_shell_interpretation(self):
        spelling = 'C:\\SDK quote " dollar $ é 日本\\ld.exe'
        displayed = spelling.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$")
        self.assertEqual(profiles.clang_display_token(f' "{displayed}" "-o"'), (spelling, ' "-o"'))
        self.assertEqual(profiles.clang_display_token('ld\t-cc1'), ("ld", "-cc1"))

    def test_malformed_display_tokens_never_select_an_existing_prefix(self):
        rejected = self.root / "foo-ld"
        linker = self.root / "ld"
        rejected.write_bytes(b"must not select")
        linker.write_bytes(b"valid linker")
        displayed = display_token(rejected)
        malformed = (
            f'{displayed}suffix "-o" "output"',
            displayed[:-1] + '\\"',
            displayed[:-1],
            f'{rejected}" "-o" "output"',
            f'{displayed} "\\q"',
            f'{displayed} "-cc1',
            f'{displayed} "-cc1"suffix',
        )
        # An unknown escape can also spell an existing host path on POSIX.
        if os.name != "nt":
            escaped = self.root / r"bad\q"
            escaped.mkdir()
            (escaped / "ld").write_bytes(b"must not select unknown escape")
            malformed += (f'"{escaped / "ld"}" "-o" "output"',)
        for line in malformed:
            with self.subTest(line=line):
                self.assertEqual(profiles.linker_from_trace(line + f'\n{display_token(linker)} "-o" "output"\n'),
                                 linker.absolute())
                with self.assertRaisesRegex(AssertionError, "did not expose a linker command"):
                    profiles.linker_from_trace(line + "\n")

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
                companion = origin / "mspdbcore.dll"
                companion.write_bytes(b"same SDK PDB helper")
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
                        overrides = profiles.linker_override_arguments(controlled)
                        if platform == "win32":
                            name = "link.exe" if role == "off" else "lld-link"
                            self.assertEqual(overrides, ["-B" + str(controlled.absolute().parent),
                                                         "-fuse-ld=" + name])
                        else:
                            self.assertEqual(overrides, ["--ld-path=" + str(controlled.absolute())])
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
                        copied_companion = controlled.parent / companion.name
                        if platform == "win32" and role == "off":
                            self.assertEqual(copied_companion.read_bytes(), companion.read_bytes())
                        else:
                            self.assertFalse(copied_companion.exists())
                    self.assertEqual(len(calls), 4)
                    thin_flags = calls[2][3]
                    self.assertIn("-fuse-ld=ld" if platform == "darwin" else "-fuse-ld=lld", thin_flags)

    def test_msvc_companions_are_bounded_to_selected_bin_and_matching_families(self):
        origin = self.root / "selected SDK bin"
        origin.mkdir()
        private = self.root / "private bin"
        private.mkdir()
        actual = origin / "link.exe"
        actual.write_bytes(b"real selected linker")
        selected = private / actual.name
        selected.write_bytes(actual.read_bytes())
        wanted = ("mspdbcore.dll", "mspdb140.dll", "msobj140.dll", "mspdbsrv.exe",
                  "MSPDBST.DLL", "vcruntime140.dll", "vcruntime140_1.dll",
                  "msvcp140.dll", "concrt140.dll")
        excluded = ("cl.exe", "c1.dll", "c1xx.dll", "c2.dll", "other.dll",
                    "mspdbcore.dll.bak", "mspdbcmf.exe", "notes.txt")
        for name in (*wanted, *excluded):
            (origin / name).write_bytes(("selected-version:" + name).encode())
        nested = origin / "another-target"
        nested.mkdir()
        (nested / "mspdb999.dll").write_bytes(b"wrong architecture/version")
        (origin / "msobj_directory.dll").mkdir()
        # A similarly named DLL elsewhere must never be searched or copied.
        (self.root / "mspdb999.dll").write_bytes(b"wrong external version")
        profiles.stage_msvc_linker_dependencies(actual, selected)
        self.assertEqual({path.name for path in private.iterdir()}, {"link.exe", *wanted})
        before = {name: (private / name).read_bytes() for name in wanted}
        for name in wanted:
            self.assertEqual(before[name], (origin / name).read_bytes())
        with patch.object(sys, "platform", "win32"):
            profiles.mutate_fake_linker(selected, "dll-test")
        self.assertNotEqual(selected.read_bytes(), actual.read_bytes())
        for name in wanted:
            self.assertEqual((private / name).read_bytes(), before[name])
            self.assertEqual((origin / name).read_bytes(), before[name])

    def test_absent_companions_are_not_fabricated_and_copy_errors_propagate(self):
        origin = self.root / "bin"
        origin.mkdir()
        actual = origin / "link.exe"
        actual.write_bytes(b"linker")
        private = self.root / "private"
        private.mkdir()
        destination = private / actual.name
        with patch.object(profiles.shutil, "copy2") as copy:
            profiles.stage_msvc_linker_dependencies(actual, destination)
            copy.assert_not_called()
        self.assertEqual(list(private.iterdir()), [])
        companion = origin / "mspdbcore.dll"
        companion.write_bytes(b"PDB")
        with patch.object(profiles.shutil, "copy2", side_effect=PermissionError("fixture")) as copy:
            with self.assertRaises(PermissionError):
                profiles.stage_msvc_linker_dependencies(actual, destination)
            copy.assert_called_once_with(companion, private / companion.name)

    def test_native_clang_windows_alias_preserves_only_selected_adjacent_dlls(self):
        origin = self.root / "selected compiler"
        origin.mkdir()
        clang = origin / "clang.exe"
        clang.write_bytes(b"selected compiler image")
        companions = {"LLVM.dll": b"selected LLVM", "libclang-cpp.DLL": b"selected Clang"}
        for name, contents in companions.items():
            (origin / name).write_bytes(contents)
        for name in ("clang-cl.exe", "LLVM.dll.bak", "notes.txt"):
            (origin / name).write_bytes(b"unrelated tool")
        nested = origin / "other architecture"
        nested.mkdir()
        (nested / "LLVM.dll").write_bytes(b"wrong architecture")
        (origin / "directory.dll").mkdir()
        (self.root / "external.dll").write_bytes(b"unselected compiler")
        private = self.root / "private compiler"
        private.mkdir()
        alias = private / "foo-ld.exe"
        with patch.object(sys, "platform", "win32"):
            self.assertEqual(stage_native_clang_alias(clang, alias), [])
        self.assertEqual({path.name for path in private.iterdir()}, {alias.name, *companions})
        self.assertEqual(alias.read_bytes(), clang.read_bytes())
        for name, contents in companions.items():
            self.assertEqual((private / name).read_bytes(), contents)
            self.assertEqual((origin / name).read_bytes(), contents)

    def test_native_clang_configured_alias_copy_failure_propagates(self):
        origin = self.root / "compiler"
        origin.mkdir()
        clang = origin / "clang.exe"
        clang.write_bytes(b"compiler")
        dll = origin / "LLVM.dll"
        dll.write_bytes(b"private dependency")
        alias = self.root / "foo-ld.exe"
        with patch.object(sys, "platform", "win32"), patch.object(shutil, "copy2", side_effect=[None, PermissionError("fixture")]) as copy:
            with self.assertRaises(PermissionError):
                stage_native_clang_alias(clang, alias)
        self.assertEqual(copy.call_args_list[0].args, (clang, alias))
        self.assertEqual(copy.call_args_list[1].args, (dll.resolve(), alias.parent / dll.name))

    def clang_dispatch_fixture(self):
        configured = self.root / "selected developer dispatcher"
        configured.write_bytes(b"configured dispatcher")
        origin = self.root / "selected SDK é 日本 ' $"
        origin.mkdir()
        image = origin / "clang"
        image.write_bytes(b"selected driver image")
        other = self.root / "unselected clang"
        other.write_bytes(b"another compiler")
        linker = origin / "ld"
        linker.write_bytes(b"selected linker")
        resource = origin / "resources"
        resource.mkdir()
        trace = f'{display_token(image)} "-cc1" "input.c"\n{display_token(linker)} "-o" "output"\n'
        return configured, image, other, linker, resource, trace

    def test_macos_dispatcher_uses_its_own_frontend_and_resource_identity(self):
        configured, image, _, _, resource, trace = self.clang_dispatch_fixture()
        replies = [subprocess.CompletedProcess([], 0, "", trace),
                   subprocess.CompletedProcess([], 0, str(resource) + "\n", ""),
                   subprocess.CompletedProcess([], 0, "", trace)]
        with patch.object(sys, "platform", "darwin"), patch.object(subprocess, "run", side_effect=replies) as launch:
            self.assertEqual(native_clang_driver(configured, str(resource)), image)
        commands = [call.args[0] for call in launch.call_args_list]
        self.assertEqual(commands[0], [str(configured), "-###", "-x", "c", os.devnull,
                                       "-o", os.devnull, "-resource-dir", str(resource)])
        self.assertEqual(commands[1], [str(image), "-print-resource-dir"])
        self.assertEqual(commands[2], [str(image), *commands[0][1:]])
        for call in launch.call_args_list:
            self.assertEqual(call.kwargs["timeout"], 30)
            self.assertFalse(call.kwargs["check"])
        self.assertEqual(configured.read_bytes(), b"configured dispatcher")
        self.assertEqual(image.read_bytes(), b"selected driver image")

    def test_macos_dispatcher_rejects_unusable_or_ambiguous_frontend_images(self):
        configured, image, other, linker, resource, trace = self.clang_dispatch_fixture()
        invalid = ("", f'{display_token(image)} "-cc1as"\n',
                   '"clang" "-cc1"\n',
                   f'{display_token(self.root / "absent clang")} "-cc1"\n',
                   f'{display_token(resource)} "-cc1"\n',
                   trace + f'{display_token(other)} "-cc1"\n',
                   f'{display_token(image)}suffix "-cc1"\n',
                   f'{display_token(linker)} "-o" "-cc1"\n')
        for output in invalid:
            with self.subTest(output=output), patch.object(sys, "platform", "darwin"), patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "", output)) as launch:
                with self.assertRaises(AssertionError):
                    native_clang_driver(configured, str(resource))
                self.assertEqual(launch.call_count, 1)

    def test_macos_dispatcher_rejects_different_or_invalid_resource_directory(self):
        configured, _, _, _, resource, trace = self.clang_dispatch_fixture()
        other_resource = self.root / "another toolchain resources"
        other_resource.mkdir()
        for reported in ("", "relative-resource", str(self.root / "absent resource"), str(other_resource)):
            replies = [subprocess.CompletedProcess([], 0, "", trace),
                       subprocess.CompletedProcess([], 0, reported + "\n", "")]
            with self.subTest(reported=reported), patch.object(sys, "platform", "darwin"), patch.object(subprocess, "run", side_effect=replies) as launch:
                with self.assertRaises(AssertionError):
                    native_clang_driver(configured, str(resource))
                self.assertEqual(launch.call_count, 2)

    def test_macos_dispatcher_rejects_redirected_image_or_changed_linker(self):
        configured, image, other, linker, resource, trace = self.clang_dispatch_fixture()
        other_linker = self.root / "ld"
        other_linker.write_bytes(b"unselected linker")
        invalid = (f'{display_token(other)} "-cc1"\n{display_token(linker)} "-o"\n',
                   f'{display_token(image)} "-cc1"\n{display_token(other_linker)} "-o"\n')
        for direct in invalid:
            replies = [subprocess.CompletedProcess([], 0, "", trace),
                       subprocess.CompletedProcess([], 0, str(resource) + "\n", ""),
                       subprocess.CompletedProcess([], 0, "", direct)]
            with self.subTest(direct=direct), patch.object(sys, "platform", "darwin"), patch.object(subprocess, "run", side_effect=replies) as launch:
                with self.assertRaises(AssertionError):
                    native_clang_driver(configured, str(resource))
                self.assertEqual(launch.call_count, 3)

    def test_macos_configured_probe_failure_keeps_both_streams_and_path(self):
        configured, image, _, _, resource, trace = self.clang_dispatch_fixture()
        for failure_at in range(3):
            # Each probe can fail independently; no later probe is attempted.
            replies = [subprocess.CompletedProcess([], 0, "", trace),
                       subprocess.CompletedProcess([], 0, str(resource) + "\n", ""),
                       subprocess.CompletedProcess([], 0, "", trace)]
            replies[failure_at] = subprocess.CompletedProcess([], 72, "selected SDK output", "driver lookup failed")
            with self.subTest(failure_at=failure_at), patch.object(sys, "platform", "darwin"), patch.object(subprocess, "run", side_effect=replies) as launch:
                with self.assertRaises(AssertionError) as failed:
                    native_clang_driver(configured, str(resource))
                self.assertIn("selected SDK output", str(failed.exception))
                self.assertIn("driver lookup failed", str(failed.exception))
                self.assertIn(str(configured if failure_at == 0 else image), str(failed.exception))
                self.assertEqual(launch.call_count, failure_at + 1)

    def test_non_macos_driver_selection_keeps_the_configured_image_without_probe(self):
        configured = self.root / "clang.exe"
        configured.write_bytes(b"configured compiler")
        for platform in ("linux", "win32"):
            with self.subTest(platform=platform), patch.object(sys, "platform", platform):
                self.assertEqual(native_clang_driver(configured, "unused resources"), configured)

    def test_ignored_override_still_fails(self):
        for platform, name in (("linux", "ld"), ("darwin", "ld"), ("win32", "link.exe")):
            with self.subTest(platform=platform):
                case = self.root / platform
                case.mkdir()
                actual = case / name
                actual.write_bytes(b"original")
                with patch.object(sys, "platform", platform), patch.object(profiles, "trace_linker", return_value=actual):
                    with self.assertRaisesRegex(AssertionError, "ignored the controlled linker"):
                        profiles.controlled_linkers(case, "unused-clang")

    def test_windows_uses_basenames_and_keeps_lld_flavor(self):
        private = self.root / "private tools with spaces"
        private.mkdir()
        with patch.object(sys, "platform", "win32"):
            for name, flavor in (("link.exe", "link.exe"), ("lld-link.exe", "lld-link")):
                with self.subTest(name=name):
                    selected = private / name
                    selected.write_bytes(b"never executed")
                    overrides = profiles.linker_override_arguments(selected)
                    self.assertEqual(overrides, ["-B" + str(private.absolute()), "-fuse-ld=" + flavor])
                    self.assertNotEqual(flavor, "link")  # Avoid VS's special discovery branch.
                    self.assertEqual(Path(flavor).name, flavor)  # Never an absolute -fuse-ld path.
                    traced = selected.with_suffix("") if name == "lld-link.exe" else selected
                    self.assertEqual(profiles.linker_from_trace(f'{display_token(traced)} "-out:unused"\n'),
                                     selected.absolute())
            # MinGW uses generic GetLinkerPath, not the MSVC basename protocol.
            mingw = private / "ld.lld.exe"
            self.assertEqual(profiles.linker_override_arguments(mingw),
                             ["--ld-path=" + str(mingw.absolute())])

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

    def test_trace_and_recorder_pass_exact_same_final_overrides(self):
        for platform, name in (("linux", "ld.lld"), ("darwin", "ld"),
                               ("win32", "link.exe"), ("win32", "lld-link.exe"),
                               ("win32", "ld.lld.exe")):
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
                    overrides = profiles.linker_override_arguments(selected)
                    result = subprocess.CompletedProcess([], 0, f'{display_token(selected)} "-o" "unused"\n', "")
                    with patch.object(subprocess, "run", return_value=result) as launch:
                        self.assertEqual(profiles.trace_linker(str(real_clang), flags, linker_path=selected,
                                                              original_dir=origin), selected.absolute())
                    trace_args = launch.call_args.args[0]
                    self.assertEqual(trace_args[-len(overrides):], overrides)
                    self.assertEqual(trace_args[-len(overrides)-2:-len(overrides)], flags)
                    self.assertTrue(launch.call_args.kwargs["env"]["PATH"].startswith(str(origin) + os.pathsep))
                    self.assertEqual(launch.call_args.kwargs["timeout"], 30)
                    recorder = case / "record_clang.py"
                    # Model the native builder boundary; this pure test executes
                    # the recorder script, never a Windows launcher or compiler.
                    native_wrapper = case / "native-profile-recorder" / "record-clang.exe"
                    with patch.object(profiles, "windows_python_driver", return_value=native_wrapper) as build:
                        wrapper, log = profiles.write_recorder(case, str(real_clang))
                    if platform == "win32":
                        build.assert_called_once_with(native_wrapper.parent, str(real_clang), recorder)
                        self.assertEqual(wrapper, native_wrapper)
                        self.assertFalse(wrapper.exists())  # No modeled bytes are claimed as a PE.
                    else:
                        build.assert_not_called()
                        self.assertEqual(wrapper, case / "record-clang")
                        self.assertTrue(wrapper.is_file())
                    environment = {"FREAK_PROFILE_REAL_CLANG": str(real_clang),
                                   "FREAK_PROFILE_CLANG_LOG": str(log),
                                   "FREAK_PROFILE_LINKER_OVERRIDE": json.dumps(overrides),
                                   "FREAK_PROFILE_LINKER_ORIGIN": str(origin), "PATH": "preserved-path"}
                    args = ["input with spaces.c", *flags]
                    with patch.dict(os.environ, environment, clear=True), patch.object(sys, "argv", [str(recorder), *args]), patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as launch:
                        with self.assertRaises(SystemExit) as stopped:
                            runpy.run_path(str(recorder), run_name="__main__")
                    self.assertEqual(stopped.exception.code, 0)
                    self.assertEqual(launch.call_args.args[0], [str(real_clang), *args, *overrides])
                    self.assertEqual(launch.call_args.kwargs["env"]["PATH"], str(origin) + os.pathsep + "preserved-path")
                    self.assertEqual(json.loads(log.read_text()), args)


@unittest.skipUnless(os.environ.get("FREAK_PROFILE_NATIVE_CLANG"), "set FREAK_PROFILE_NATIVE_CLANG for the real driver trace witness")
class NativeLinkerAliasTrace(unittest.TestCase):
    def test_genuine_compiler_alias_foo_ld_selects_the_later_linker(self):
        clang = Path(os.environ["FREAK_PROFILE_NATIVE_CLANG"]).absolute()
        resource = subprocess.run([str(clang), "-print-resource-dir"], capture_output=True,
                                  text=True, encoding="utf-8", timeout=30, check=False)
        self.assertEqual(resource.returncode, 0, resource.stdout + resource.stderr)
        self.assertTrue(Path(resource.stdout.strip()).is_dir())
        image = native_clang_driver(clang, resource.stdout.strip())
        with tempfile.TemporaryDirectory(prefix="freak-real-linker-role-") as directory:
            spelling = "compiler é 日本 ' $ &"
            if os.name != "nt":
                spelling += ' quote " slash \\'
            tools = Path(directory) / spelling
            tools.mkdir()
            alias = tools / ("foo-ld.exe" if sys.platform == "win32" else "foo-ld")
            flags = [*stage_native_clang_alias(image, alias), "-resource-dir", resource.stdout.strip()]
            trace = subprocess.run([str(alias), "-###", "-x", "c", os.devnull, "-o", os.devnull,
                                    *flags], capture_output=True,
                                   text=True, encoding="utf-8", timeout=30, check=False)
            self.assertEqual(trace.returncode, 0, trace.stdout + trace.stderr)
            output = trace.stdout + trace.stderr
            self.assertIn(f'{display_token(alias)} "-cc1"', output)
            selected = profiles.linker_from_trace(output)
            self.assertNotEqual(selected, alias)
            self.assertTrue(selected.is_file())
            self.assertEqual(profiles.trace_linker(str(alias), flags), selected)


if __name__ == "__main__":
    unittest.main()
