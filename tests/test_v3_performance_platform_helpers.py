"""Pure CI regression tests; no compiler, process probe or native API runs."""
import copy
import ctypes
import errno
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import v3_performance_lab as acceptance

LAB = acceptance.LAB


class PlatformHelpers(unittest.TestCase):
    def setUp(self):
        for name in ("run", "Popen"):
            guard = patch.object(subprocess, name, side_effect=AssertionError("unexpected child process"))
            guard.start()
            self.addCleanup(guard.stop)
        guard = patch.object(ctypes, "CDLL", side_effect=AssertionError("unexpected native API"))
        guard.start()
        self.addCleanup(guard.stop)
        guard = patch.object(LAB.signal, "SIGKILL", 9, create=True)
        guard.start()
        self.addCleanup(guard.stop)
        temporary = tempfile.TemporaryDirectory(prefix="freak-lab-platform-unit-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def test_darwin_only_proves_complete_exited_leader_singleton(self):
        for count, members, accepted in (
            (1, [4321], True), (0, [], False), (-1, [], False),
            (1, [4322], False), (2, [4321, 4322], False),
            (2, [4322, 4321], False), (3, [4321, 4322], False),
        ):
            with self.subTest(count=count, members=members):
                def query(pid, buffer, size):
                    self.assertEqual((pid, size), (4321, 8))
                    for index, member in enumerate(members):
                        buffer[index] = member
                    return count

                symbol = Mock(side_effect=query)
                library = SimpleNamespace(proc_listpgrppids=symbol)
                with patch.object(sys, "platform", "darwin"), \
                     patch.object(LAB, "_direct_process_exited_without_reaping", return_value=True), \
                     patch.object(ctypes, "CDLL", return_value=library) as load:
                    self.assertEqual(LAB._darwin_exited_group_is_singleton(SimpleNamespace(pid=4321)), accepted)
                load.assert_called_once_with("/usr/lib/libproc.dylib", use_errno=True)
                self.assertEqual(symbol.argtypes, [ctypes.c_int, ctypes.c_void_p, ctypes.c_int])
                self.assertEqual(symbol.restype, ctypes.c_int)

    def test_darwin_probe_fails_closed_without_exit_or_api(self):
        child = SimpleNamespace(pid=4321)
        with patch.object(sys, "platform", "linux"):
            self.assertFalse(LAB._darwin_exited_group_is_singleton(child))
        with patch.object(sys, "platform", "darwin"):
            with patch.object(LAB, "_direct_process_exited_without_reaping", return_value=False):
                self.assertFalse(LAB._darwin_exited_group_is_singleton(child))
            with patch.object(LAB, "_direct_process_exited_without_reaping", side_effect=LAB.LabError("reaped")):
                self.assertFalse(LAB._darwin_exited_group_is_singleton(child))
            with patch.object(LAB, "_direct_process_exited_without_reaping", return_value=True):
                for failure in (OSError("unavailable"), AttributeError("missing symbol")):
                    with patch.object(ctypes, "CDLL", side_effect=failure):
                        self.assertFalse(LAB._darwin_exited_group_is_singleton(child))

    def test_permission_error_is_retained_unless_singleton_proven_before_reaping(self):
        for proven in (False, True):
            order = []
            child = SimpleNamespace(pid=4321,
                                    poll=Mock(side_effect=lambda: order.append("poll") or 0),
                                    wait=Mock(return_value=0), kill=Mock())
            def proof(process):
                self.assertIs(process, child)
                order.append("proof")
                return proven
            with patch.object(sys, "platform", "darwin"), \
                 patch.object(LAB.os, "killpg", create=True, side_effect=PermissionError(errno.EPERM, "denied")), \
                 patch.object(LAB, "_darwin_exited_group_is_singleton", side_effect=proof):
                errors = LAB._terminate_process_tree(child, None)
            self.assertEqual(order, ["proof", "poll"])
            self.assertEqual(bool(errors), not proven)
            if errors:
                self.assertIn("cannot terminate POSIX process group", errors[0])
            child.kill.assert_not_called()
            child.wait.assert_called_once_with(timeout=2.0)

    def test_other_group_errors_are_not_reclassified(self):
        for failure, has_error in ((ProcessLookupError(), False), (OSError(errno.EIO, "bad"), True)):
            child = SimpleNamespace(pid=4321, poll=Mock(return_value=0), wait=Mock(return_value=0))
            with patch.object(sys, "platform", "darwin"), \
                 patch.object(LAB.os, "killpg", create=True, side_effect=failure), \
                 patch.object(LAB, "_darwin_exited_group_is_singleton") as proof:
                self.assertEqual(bool(LAB._terminate_process_tree(child, None)), has_error)
            proof.assert_not_called()

    def test_recording_and_validation_resolve_the_same_linker_alias(self):
        real = self.root / "x86_64-linux-gnu-ld.bfd"
        real.write_bytes(b"fake linker bytes; never executed")
        alias = self.root / "ld"
        other = self.root / "different-ld"
        other.write_bytes(real.read_bytes())
        original_resolve = Path.resolve

        def resolve(path, *args, **kwargs):
            return real if path == alias else original_resolve(path, *args, **kwargs)

        trace = f'"{alias}" "-o" "output"\n'.encode()
        version = subprocess.CompletedProcess([], 0, b"linker version", b"")
        with patch.object(Path, "resolve", resolve), \
             patch.object(LAB, "_run_bytes", side_effect=[subprocess.CompletedProcess([], 0, b"", trace), version]):
            identity = LAB._linker_identity_from_trace(real, ["input.o", "-o", "out"], "invocation", self.root, {}, 5.0)
        self.assertEqual(identity["observed_path"], str(alias))
        self.assertEqual(identity["path"], str(real))
        with patch.object(Path, "resolve", resolve), \
             patch.object(LAB, "_linker_identity_from_trace", return_value=identity):
            self.assertEqual(LAB._validate_linker_identity(identity, "linker", real, [], {}, 5.0, "invocation"), identity)
            substituted = copy.deepcopy(identity)
            substituted["path"] = str(other)
            with self.assertRaisesRegex(LAB.LabError, "observed and resolved linker paths differ"):
                LAB._validate_linker_identity(substituted, "linker", real, [], {}, 5.0, "invocation")
            stale = copy.deepcopy(identity)
            stale["sha256"] = "0" * 64
            with self.assertRaisesRegex(LAB.LabError, "provenance is stale"):
                LAB._validate_linker_identity(stale, "linker", real, [], {}, 5.0, "invocation")
        changed_live = dict(identity, path=str(other))
        with patch.object(Path, "resolve", resolve), \
             patch.object(LAB, "_linker_identity_from_trace", return_value=changed_live):
            with self.assertRaisesRegex(LAB.LabError, "derived by live Clang"):
                LAB._validate_linker_identity(identity, "linker", real, [], {}, 5.0, "invocation")

    def test_bare_linker_resolution_uses_recorded_environment(self):
        real = self.root / "ld.bfd"
        real.write_bytes(b"never executed")
        with patch.object(LAB.shutil, "which", return_value=str(real)) as search:
            self.assertEqual(LAB._resolve_observed_linker("ld", {"PATH": "recorded-path"}), real)
        search.assert_called_once_with("ld", path="recorded-path")
        with patch.object(LAB.shutil, "which", return_value=None):
            with self.assertRaisesRegex(LAB.LabError, "not resolvable"):
                LAB._resolve_observed_linker("ld", {"PATH": "empty"})


if __name__ == "__main__":
    unittest.main()
