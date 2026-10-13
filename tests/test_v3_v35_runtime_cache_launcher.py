"""Cache gate launch ownership controls; no compiler, SDK, build or server.

Mocked failures exercise exact checkpoint/capture boundaries. POSIX inert
Python controls require the committed shared command lifeline and retain raw
channels; they do not qualify native Windows or compiler behavior.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import v3_v35_acceptance as acceptance
import v3_v35_runtime_cache as cache


class ModelChild:
    def __init__(self, pid: int, outcome=0):
        self.pid = pid
        self.returncode = None
        self.outcome = outcome
        self.waits = []
        self._child_created = True

    def wait(self, timeout=None):
        self.waits.append(timeout)
        if isinstance(self.outcome, BaseException):
            error, self.outcome = self.outcome, -9
            raise error
        if self.returncode is None:
            self.returncode = self.outcome
        return self.returncode

    def poll(self):
        return self.returncode

    def terminate(self):
        self.returncode = -15

    def kill(self):
        self.returncode = -9


class ModelLifeline:
    def __init__(self, timeout):
        self.timeout = timeout
        self.context = {"mode": "inert contract model", "registered": False}
        self.child = None
        self.native = None
        self.finishes = []
        self.registration_error = None
        self.finish_error = None

    def options(self, preexec_fn):
        assert preexec_fn is None
        return {"start_new_session": False, "process_group": 0}

    def registered(self, child):
        self.child = child
        self.context.update(pgid=child.pid, native_pid=child.pid, registered=True)
        if self.registration_error is not None:
            raise self.registration_error
        return self.context

    def spawn(self, command, **options):
        self.native = subprocess.Popen(command, **options)
        return self.native

    def finish(self, normal):
        self.finishes.append(normal)
        if self.child is not None and self.child.poll() is None:
            self.child.returncode = -9
        if self.finish_error is not None:
            raise self.finish_error
        self.context.update(keeper_reaped=True, group_drained=True)


class LaunchBoundaryModels(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="cache-launch-model-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.evidence = cache.Evidence(self.root / "evidence")
        self.children = []
        self.keepers = []
        self.output_handles = []
        self.child_outcomes = []
        self.registration_error_at = None
        self.finish_error = None
        self.launch_error_at = None

        def keeper(timeout):
            value = ModelLifeline(timeout)
            value.finish_error = self.finish_error
            if self.registration_error_at == len(self.keepers):
                value.registration_error = self.primary
            self.keepers.append(value)
            return value

        def popen(argv, **options):
            if cache.os.name != "nt":
                self.assertIs(options["start_new_session"], False)
                self.assertEqual(options["process_group"], 0)
            else:
                self.assertNotIn("process_group", options)
                self.assertNotIn("start_new_session", options)
            if self.launch_error_at == len(self.children):
                raise self.primary
            outcome = self.child_outcomes.pop(0) if self.child_outcomes else 0
            child = ModelChild(740000 + len(self.children), outcome)
            self.children.append(child)
            options["stdout"].write(b"raw stdout\x00\xff\n")
            options["stdout"].flush()
            options["stderr"].write(b"raw stderr\xfe\n")
            options["stderr"].flush()
            if argv[0] == "strace":
                # A synthetic trace tests launcher routing only. It is never
                # included in native compiler/cache qualification evidence.
                Path(argv[argv.index("-o") + 1]).write_text('1 execve("/inert-clang", ["clang", "-c", "cpp-output"], []) = 0\n')
            self.output_handles.extend((options["stdout"], options["stderr"]))
            return child

        self.addCleanup(patch.stopall)
        patch.object(acceptance, "_CommandLifeline", side_effect=keeper, create=True).start()
        patch.object(cache.subprocess, "Popen", side_effect=popen).start()
        patch.object(cache, "os", SimpleNamespace(name="posix", killpg=Mock(
            side_effect=AssertionError("unexpected real group signaling in model")))).start()

    def invoke(self):
        return self.evidence.invoke(["inert-model"], self.root, {}, "model", timeout=240)

    def assert_contained(self, normal=False):
        self.assertTrue(all(child.poll() is not None for child in self.children))
        self.assertTrue(all(keeper.finishes == [normal] for keeper in self.keepers))
        self.assertTrue(all(handle.closed for handle in self.output_handles))

    def assert_raw(self, record):
        for name, expected in (("stdout", b"raw stdout\x00\xff\n"), ("stderr", b"raw stderr\xfe\n")):
            receipt = record[name]
            self.assertEqual(Path(receipt["path"]).read_bytes(), expected)
            self.assertEqual(receipt["sha256"], hashlib.sha256(expected).hexdigest())

    def test_normal_completion_drains_reaps_and_retains_raw_files(self):
        code, _, _ = self.invoke()
        self.assertEqual(code, 0)
        self.assert_contained(normal=True)
        row, = self.evidence.report["commands"]
        self.assertEqual(row["status"], "completed")
        self.assertEqual(row["owned_pid"], row["owned_pgid"])
        self.assert_raw(row)

    def test_pid_checkpoint_oserror_is_the_same_primary_and_contains_child(self):
        primary = OSError("controlled post-Popen PID checkpoint failure")
        original = self.evidence.save
        def fail():
            if self.evidence.report["commands"][-1].get("owned_pid"):
                raise primary
            original()
        self.evidence.save = fail
        with self.assertRaises(OSError) as raised:
            self.invoke()
        self.assertIs(raised.exception, primary)
        self.assert_contained()
        row, = self.evidence.report["commands"]
        self.assertEqual(row["status"], "harness_failed")
        self.assert_raw(row)
        self.assertTrue(row["secondary_evidence_errors"])

    def test_pid_checkpoint_keyboardinterrupt_is_preserved(self):
        primary = KeyboardInterrupt("controlled post-spawn interruption")
        original = self.evidence.save
        def fail():
            if self.evidence.report["commands"][-1].get("owned_pid"):
                raise primary
            original()
        self.evidence.save = fail
        with self.assertRaises(KeyboardInterrupt) as raised:
            self.invoke()
        self.assertIs(raised.exception, primary)
        self.assert_contained()
        self.assert_raw(self.evidence.report["commands"][0])

    def test_wait_timeout_and_keyboardinterrupt_keep_primary(self):
        for primary in (subprocess.TimeoutExpired(["inert"], 240), KeyboardInterrupt("wait interrupted")):
            with self.subTest(primary=type(primary).__name__):
                self.child_outcomes = [primary]
                before = len(self.children)
                with self.assertRaises(type(primary)) as raised:
                    self.invoke()
                self.assertIs(raised.exception, primary)
                self.assertIsNotNone(self.children[before].poll())
                self.assertEqual(self.keepers[before].finishes, [False])
                self.assert_raw(self.evidence.report["commands"][-1])

    def test_registration_failure_still_owns_the_returned_child(self):
        self.primary = KeyboardInterrupt("readiness interrupted")
        self.registration_error_at = 0
        with self.assertRaises(KeyboardInterrupt) as raised:
            self.invoke()
        self.assertIs(raised.exception, self.primary)
        self.assert_contained()
        self.assert_raw(self.evidence.report["commands"][0])

    def test_popen_failure_finishes_the_prepared_lifeline(self):
        self.primary = OSError("controlled Popen failure")
        self.launch_error_at = 0
        with self.assertRaises(OSError) as raised:
            self.invoke()
        self.assertIs(raised.exception, self.primary)
        self.assertEqual(self.keepers[0].finishes, [False])
        self.assertEqual(self.children, [])

    def test_primary_timeout_survives_lifeline_finish_and_final_save_failures(self):
        primary = subprocess.TimeoutExpired(["inert"], 240)
        self.child_outcomes = [primary]
        self.finish_error = OSError("secondary lifeline error")
        original = self.evidence.save
        def fail():
            rows = self.evidence.report["commands"]
            if rows and rows[-1]["status"] == "timed_out":
                raise OSError("secondary terminal checkpoint error")
            original()
        self.evidence.save = fail
        with self.assertRaises(subprocess.TimeoutExpired) as raised:
            self.invoke()
        self.assertIs(raised.exception, primary)
        self.assert_raw(self.evidence.report["commands"][0])
        self.assertIn("secondary lifeline error", str(self.evidence.report["commands"][0]["cleanup_notes"]))
        self.assertTrue(self.evidence.report["commands"][0]["secondary_evidence_errors"])

    def test_concurrent_second_capture_open_failure_contains_first_child(self):
        primary = OSError("controlled second stderr open failure")
        real_open = Path.open
        opened = []
        def capture(path, *args, **kwargs):
            if path.name == "concurrent-1.stderr":
                raise primary
            stream = real_open(path, *args, **kwargs)
            if path.name == "concurrent-1.stdout":
                opened.append(stream)
            return stream
        with patch.object(Path, "open", capture), self.assertRaises(OSError) as raised:
            self.evidence.invoke_concurrent([["first"], ["second"]], self.root, {}, trace=False)
        self.assertIs(raised.exception, primary)
        self.assertEqual(len(self.children), 1)
        self.assert_contained()
        self.assertTrue(opened and all(channel.closed for channel in opened))
        self.assert_raw(self.evidence.report["commands"][0])

    def test_concurrent_second_launch_and_registration_failures_contain_both_owners(self):
        self.primary = OSError("controlled second Popen failure")
        self.launch_error_at = 1
        with self.assertRaises(OSError) as raised:
            self.evidence.invoke_concurrent([["first"], ["second"]], self.root, {}, trace=False)
        self.assertIs(raised.exception, self.primary)
        self.assert_contained()
        self.assertEqual(len(self.keepers), 2)
        self.assert_raw(self.evidence.report["commands"][0])

    def test_concurrent_second_registration_interruption_keeps_both_raw_channels(self):
        self.primary = KeyboardInterrupt("controlled second registration interruption")
        self.registration_error_at = 1
        with self.assertRaises(KeyboardInterrupt) as raised:
            self.evidence.invoke_concurrent([["first"], ["second"]], self.root, {}, trace=False)
        self.assertIs(raised.exception, self.primary)
        self.assert_contained()
        self.assertEqual(len(self.children), 2)
        for row in self.evidence.report["commands"]:
            self.assert_raw(row)

    def test_windows_direct_child_model_preserves_primary_and_raw_without_tree_claim(self):
        primary = subprocess.TimeoutExpired(["inert-Windows-model"], 240)
        self.child_outcomes = [primary]
        # Patch this module's platform view only; changing global os.name would
        # make pathlib construct an unsupported WindowsPath on the POSIX host.
        with patch.object(cache, "os", SimpleNamespace(name="nt")), patch.object(cache, "signal", SimpleNamespace(SIGTERM=15)):
            with self.assertRaises(subprocess.TimeoutExpired) as raised:
                self.invoke()
        self.assertIs(raised.exception, primary)
        self.assertEqual(self.keepers, [])
        self.assertIsNotNone(self.children[0].returncode)
        self.assertTrue(all(handle.closed for handle in self.output_handles))
        row, = self.evidence.report["commands"]
        self.assertNotIn("owned_pgid", row)
        self.assertNotIn("keeper", row)
        self.assert_raw(row)

    def test_third_concurrent_command_is_rejected_before_allocation_or_launch(self):
        with self.assertRaisesRegex(AssertionError, "at most two"):
            self.evidence.invoke_concurrent([["a"], ["b"], ["c"]], self.root, {}, trace=False)
        self.assertEqual(self.children, [])
        self.assertEqual(self.evidence.report["commands"], [])

    def test_concurrent_nonzero_status_keeps_diagnostics_and_contains_other_writer(self):
        self.child_outcomes = [7, 0]
        with self.assertRaises(AssertionError) as raised:
            self.evidence.invoke_concurrent([["first"], ["second"]], self.root, {}, trace=False)
        self.assertIn("status 7", str(raised.exception))
        self.assertIn("raw stdout", str(raised.exception))
        self.assertIn("raw stderr", str(raised.exception))
        self.assertEqual(self.children[0].returncode, 7)
        self.assert_contained()
        for row in self.evidence.report["commands"]:
            self.assert_raw(row)

    def test_trace_runtime_interrupt_routes_to_owned_group_and_retains_exact_argv(self):
        signalled = []
        def interrupt(pgid, action):
            signalled.append((pgid, action))
            self.children[0].returncode = -15
        argv = ["inert-sdk", "a b", "$literal;[]"]
        with patch.object(cache.os, "killpg", side_effect=interrupt), patch.object(cache, "sys", SimpleNamespace(platform="linux")):
            code, _, trace = self.evidence.invoke(argv, self.root, {}, "trace-model", trace=True, interrupt_runtime=True)
        row, = self.evidence.report["commands"]
        self.assertEqual(code, -15)
        self.assertEqual(row["argv"][:7], ["strace", "-f", "-s", "65536", "-e", "trace=execve", "-o"])
        self.assertEqual(row["argv"][-4:], ["--", *argv])
        self.assertEqual(row["timeout_seconds"], 240)
        self.assertTrue(row["runtime_compile_hook_fired"])
        self.assertEqual(signalled, [(row["owned_pgid"], signal.SIGTERM)])
        self.assertTrue(trace)
        self.assert_contained(normal=True)
        self.assert_raw(row)

    def test_terminal_save_failure_inside_ambient_except_is_this_invocations_failure(self):
        primary = OSError("terminal cache evidence publication failed")
        original = self.evidence.save
        def checkpoint():
            if "cleanup_notes" in self.evidence.report["commands"][-1]:
                raise primary
            original()
        self.evidence.save = checkpoint
        ambient = ValueError("unrelated handled caller exception")
        try:
            raise ambient
        except ValueError:
            with self.assertRaises(OSError) as raised:
                self.invoke()
        self.assertIs(raised.exception, primary)
        self.assertFalse(getattr(ambient, "__notes__", []))
        self.assert_contained(normal=True)
        self.assert_raw(self.evidence.report["commands"][0])

    def test_concurrent_terminal_save_failure_does_not_modify_ambient_exception(self):
        primary = OSError("terminal concurrent evidence publication failed")
        original = self.evidence.save
        def checkpoint():
            if all("cleanup_notes" in row for row in self.evidence.report["commands"]):
                raise primary
            original()
        self.evidence.save = checkpoint
        ambient = ValueError("unrelated handled concurrent caller exception")
        try:
            raise ambient
        except ValueError:
            with self.assertRaises(OSError) as raised:
                self.evidence.invoke_concurrent([["first"], ["second"]], self.root, {}, trace=False)
        self.assertIs(raised.exception, primary)
        self.assertFalse(getattr(ambient, "__notes__", []))
        self.assert_contained(normal=True)
        for row in self.evidence.report["commands"]:
            self.assert_raw(row)

    def test_unexpected_fallback_error_preserves_timeout_and_closes_both_captures(self):
        primary = subprocess.TimeoutExpired(["inert-Windows-model"], 240)
        self.child_outcomes = [primary]
        with patch.object(cache, "os", SimpleNamespace(name="nt")), patch.object(cache.Evidence, "stop_owned", side_effect=OSError("secondary fallback failure")):
            with self.assertRaises(subprocess.TimeoutExpired) as raised:
                self.invoke()
        self.assertIs(raised.exception, primary)
        self.assertIsNotNone(self.children[0].returncode)
        self.assertTrue(all(handle.closed for handle in self.output_handles))
        row, = self.evidence.report["commands"]
        self.assertIn("secondary fallback failure", str(row["cleanup_notes"]))
        self.assert_raw(row)


@unittest.skipUnless(os.name == "posix" and hasattr(acceptance, "_CommandLifeline"), "committed POSIX lifeline prerequisite required")
class InertLifelineControls(unittest.TestCase):
    # These controls deliberately run in an ordinary owner process; no reviewer
    # subreaper is installed to hide a detached-keeper leak.
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="cache-launch-inert-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def ready(self, path):
        deadline = time.monotonic() + 3
        while not path.is_file() and time.monotonic() < deadline:
            time.sleep(.01)
        self.assertTrue(path.is_file(), "inert child readiness exceeded three seconds")
        return json.loads(path.read_text())

    def command(self, ready):
        return [sys.executable, "-B", "-u", "-c",
                'import json,os,time;from pathlib import Path;'
                'os.write(1,bytes.fromhex("7061727469616c00ff"));'
                'os.write(2,bytes.fromhex("6572726f72fe"));'
                f'Path({str(ready)!r}).write_text(json.dumps({{"pid":os.getpid(),"pgid":os.getpgrp(),"sid":os.getsid(0)}}));'
                'time.sleep(60)']

    def assert_reaped(self, row):
        self.assertEqual(row["cleanup_notes"], [])
        self.assertTrue(row["keeper"]["keeper_reaped"])
        self.assertTrue(row["keeper"]["lifeline_released"])
        self.assertEqual(row["owned_pid"], row["owned_pgid"])
        self.assertEqual(row["keeper"]["sid"], os.getsid(0))
        for pid in (row["owned_pid"], row["keeper"]["keeper_pid"]):
            with self.assertRaises(ChildProcessError):
                os.waitpid(pid, os.WNOHANG)
            with self.assertRaises(ProcessLookupError):
                os.kill(pid, 0)

    def assert_partial_raw(self, row):
        for name, expected in (("stdout", bytes.fromhex("7061727469616c00ff")), ("stderr", bytes.fromhex("6572726f72fe"))):
            receipt = row[name]
            self.assertEqual(Path(receipt["path"]).read_bytes(), expected)
            self.assertEqual(receipt["sha256"], hashlib.sha256(expected).hexdigest())

    def test_normal_owner_reaps_the_direct_keeper_without_a_subreaper(self):
        if sys.platform.startswith("linux"):
            import ctypes
            prior = ctypes.c_int()
            self.assertEqual(ctypes.CDLL(None).prctl(37, ctypes.byref(prior), 0, 0, 0), 0)
            self.assertEqual(prior.value, 0, "ordinary-owner control must not install a subreaper")
        evidence = cache.Evidence(self.root / "evidence")
        survivor = subprocess.Popen([sys.executable, "-B", "-c", "import time;time.sleep(60)"])
        try:
            code, output, _ = evidence.invoke([sys.executable, "-B", "-u", "-c", "print('INERT_OK',flush=True)"], self.root, os.environ.copy(), "inert-normal", timeout=3)
            self.assertIsNone(survivor.poll(), "unrelated direct child was disturbed")
        finally:
            survivor.kill()
            survivor.wait(timeout=3)
        self.assertEqual((code, output), (0, "INERT_OK\n"))
        row, = evidence.report["commands"]
        self.assert_reaped(row)
        self.assertNotEqual(row["owned_pid"], os.getsid(0))
        self.assertEqual(row["status"], "completed")

    def test_real_pid_checkpoint_failures_reap_direct_child_and_keeper(self):
        for index, primary in enumerate((OSError("inert PID checkpoint"), KeyboardInterrupt("inert checkpoint interruption"))):
            with self.subTest(primary=type(primary).__name__):
                evidence = cache.Evidence(self.root / f"checkpoint-{index}")
                ready = self.root / f"checkpoint-ready-{index}"
                original = evidence.save
                failed = False
                def checkpoint():
                    nonlocal failed
                    row = evidence.report["commands"][-1]
                    if row.get("owned_pid") and not failed:
                        failed = True
                        identity = self.ready(ready)
                        self.assertEqual(identity["pid"], row["owned_pid"])
                        raise primary
                    original()
                evidence.save = checkpoint
                with self.assertRaises(type(primary)) as raised:
                    evidence.invoke(self.command(ready), self.root, os.environ.copy(), "checkpoint", timeout=3)
                self.assertIs(raised.exception, primary)
                row, = evidence.report["commands"]
                self.assertEqual(row["status"], "harness_failed")
                self.assert_reaped(row)
                self.assert_partial_raw(row)
                self.assertEqual(json.loads((evidence.root / "report.json").read_text())["commands"][0]["status"], "harness_failed")

    def test_inner_popen_constructor_interrupt_keeps_regular_file_bytes_and_owned_object(self):
        evidence = cache.Evidence(self.root / "constructor")
        ready = self.root / "constructor-ready"
        primary = KeyboardInterrupt("inert constructor interruption")
        original = acceptance._OwnedCommandPopen._execute_child
        def constructor(child, command, *args, **options):
            original(child, command, *args, **options)
            if "-I" not in command:
                self.ready(ready)
                raise primary
        # Interrupt inside CPython's constructor, so its exception handler runs.
        # Unlike PIPE captures, these streams belong to _CacheLaunch throughout.
        with patch.object(acceptance._OwnedCommandPopen, "_execute_child", constructor):
            with self.assertRaises(KeyboardInterrupt) as raised:
                evidence.invoke(self.command(ready), self.root, os.environ.copy(), "constructor", timeout=3)
        self.assertIs(raised.exception, primary)
        row, = evidence.report["commands"]
        self.assertFalse(row["keeper"]["popen_returned"])
        self.assert_reaped(row)
        self.assert_partial_raw(row)

    def test_real_timeout_retains_raw_and_reaps_both_direct_children(self):
        evidence = cache.Evidence(self.root / "timeout")
        ready = self.root / "timeout-ready"
        with self.assertRaises(subprocess.TimeoutExpired):
            evidence.invoke(self.command(ready), self.root, os.environ.copy(), "timeout", timeout=1)
        row, = evidence.report["commands"]
        self.assertEqual(row["status"], "timed_out")
        self.assertEqual(self.ready(ready)["pid"], row["owned_pid"])
        self.assert_reaped(row)
        self.assert_partial_raw(row)

    def test_actual_sigint_after_readiness_preserves_first_cause_and_raw(self):
        evidence = cache.Evidence(self.root / "sigint")
        ready = self.root / "sigint-ready"
        def interrupt():
            self.ready(ready)
            os.kill(os.getpid(), signal.SIGINT)
        sender = threading.Thread(target=interrupt)
        sender.start()
        try:
            with self.assertRaises(KeyboardInterrupt):
                evidence.invoke(self.command(ready), self.root, os.environ.copy(), "sigint", timeout=3)
        finally:
            sender.join(timeout=3)
        self.assertFalse(sender.is_alive())
        row, = evidence.report["commands"]
        self.assertEqual(row["status"], "harness_failed")
        self.assert_reaped(row)
        self.assert_partial_raw(row)

    def test_concurrent_capture_failure_stops_live_first_child_and_preserves_bytes(self):
        evidence = cache.Evidence(self.root / "concurrent")
        ready = self.root / "concurrent-ready"
        primary = OSError("inert second capture failure")
        original = Path.open
        def capture(path, *args, **kwargs):
            if path.name == "concurrent-1.stderr":
                self.ready(ready)
                raise primary
            return original(path, *args, **kwargs)
        with patch.object(Path, "open", capture):
            with self.assertRaises(OSError) as raised:
                evidence.invoke_concurrent([self.command(ready), [sys.executable, "-c", "pass"]], self.root, os.environ.copy(), trace=False, timeout=3)
        self.assertIs(raised.exception, primary)
        first, second = evidence.report["commands"]
        self.assert_reaped(first)
        self.assert_partial_raw(first)
        self.assertEqual(second["status"], "harness_failed")
        self.assertNotIn("owned_pid", second)


@unittest.skipUnless(sys.platform.startswith("linux"), "Linux inert adoption controls; no Windows native tree qualification")
class InertParentDeathControls(unittest.TestCase):
    """Adopt only recorded orphans after intentionally killing their owner.

    The normal-owner test above has no subreaper. These parent-death controls
    temporarily adopt killed inert descendants solely to reap their zombies;
    product helpers still wait their own direct keepers during normal cleanup.
    """
    def setUp(self):
        import ctypes
        self.libc = ctypes.CDLL(None, use_errno=True)
        prior = ctypes.c_int()
        self.assertEqual(self.libc.prctl(37, ctypes.byref(prior), 0, 0, 0), 0)
        self.assertEqual(self.libc.prctl(36, 1, 0, 0, 0), 0)
        self.addCleanup(lambda: self.assertEqual(self.libc.prctl(36, prior.value, 0, 0, 0), 0))
        self.temporary = tempfile.TemporaryDirectory(prefix="cache-owner-death-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.identities = {}
        self.parents = []
        self.addCleanup(self.cleanup_owned)

    @staticmethod
    def identity(pid):
        try:
            text = Path(f"/proc/{pid}/stat").read_text()
        except FileNotFoundError:
            return None
        fields = text[text.rindex(")") + 2:].split()
        return {"pid": pid, "state": fields[0], "pgid": int(fields[2]),
                "sid": int(fields[3]), "start_ticks": int(fields[19])}

    def remember(self, pids):
        for pid in pids:
            value = self.identity(pid)
            self.assertIsNotNone(value, "owned inert process disappeared before identity capture")
            self.identities[pid] = value

    def cleanup_owned(self):
        # Capture still-live descendants of exact owned parents before killing
        # them, even if fixture readiness/report assertions failed early. This
        # only follows the kernel child relation rooted at our Popen objects.
        pending = [parent.pid for parent in self.parents if parent.poll() is None]
        seen = set()
        while pending:
            pid = pending.pop()
            if pid in seen:
                continue
            seen.add(pid)
            current = self.identity(pid)
            if current is not None:
                self.identities.setdefault(pid, current)
                try:
                    children = Path(f"/proc/{pid}/task/{pid}/children").read_text()
                except FileNotFoundError:
                    continue
                pending.extend(int(value) for value in children.split())
        for pid, expected in self.identities.items():
            current = self.identity(pid)
            if current is not None and current["start_ticks"] == expected["start_ticks"] and current["state"] != "Z":
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        for parent in self.parents:
            if parent.poll() is None:
                parent.kill()
            parent.wait(timeout=3)
        self.gone(list(self.identities))

    def gone(self, pids):
        remaining = set(pids)
        deadline = time.monotonic() + 3
        while remaining and time.monotonic() < deadline:
            for pid in tuple(remaining):
                try:
                    waited, _ = os.waitpid(pid, os.WNOHANG)
                except ChildProcessError:
                    waited = 0
                if waited == pid or self.identity(pid) is None:
                    remaining.remove(pid)
            if remaining:
                time.sleep(.01)
        self.assertEqual(remaining, set(), "recorded owned inert processes survived")

    def ready(self, path, parent=None):
        deadline = time.monotonic() + 3
        while not path.is_file() and time.monotonic() < deadline:
            if parent is not None:
                self.assertIsNone(parent.poll(), "outer owner exited before readiness")
            time.sleep(.01)
        self.assertTrue(path.is_file(), "inert nested fixture did not become ready")
        return json.loads(path.read_text())

    def script(self, evidence_name, command):
        return ('import os,sys\nfrom pathlib import Path\n'
                f'sys.path.insert(0,{str(Path(cache.__file__).parent)!r})\n'
                'from v3_v35_runtime_cache import Evidence\n'
                f'Evidence(Path({str(self.root/evidence_name)!r})).invoke({command!r},'
                f'Path({str(self.root)!r}),os.environ.copy(),"nested",timeout=60)\n')

    def leaf_command(self):
        ready = self.root / "leaf-ready"
        code = ('import json,os,subprocess,sys,time\nfrom pathlib import Path\n'
                'child=subprocess.Popen([sys.executable,"-B","-c","import time;time.sleep(60)"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\n'
                'os.write(1,b"nested\\x00\\xff");os.write(2,b"leaf\\xfe")\n'
                f'Path({str(ready)!r}).write_text(json.dumps({{"pid":os.getpid(),"pgid":os.getpgrp(),"sid":os.getsid(0),"grandchild":child.pid}}))\n'
                'time.sleep(60)\n')
        return [sys.executable, "-B", "-u", "-c", code]

    def row(self, evidence_name):
        report = self.root / evidence_name / "report.json"
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            if report.is_file():
                rows = json.loads(report.read_text())["commands"]
                if rows and rows[0].get("owned_pid"):
                    return rows[0]
            time.sleep(.01)
        self.fail("nested owned PID checkpoint was not retained")

    def assert_leaf_raw(self, evidence_name):
        self.assertEqual((self.root/evidence_name/"000-nested.stdout").read_bytes(), b"nested\x00\xff")
        self.assertEqual((self.root/evidence_name/"000-nested.stderr").read_bytes(), b"leaf\xfe")

    def test_parent_hard_kill_drains_two_nested_groups_and_grandchild(self):
        inner = [sys.executable, "-B", "-u", "-c", self.script("inner", self.leaf_command())]
        outer = self.script("outer", inner)
        parent = subprocess.Popen([sys.executable, "-B", "-u", "-c", outer], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, process_group=0)
        self.parents.append(parent)
        survivor = subprocess.Popen([sys.executable, "-B", "-c", "import time;time.sleep(60)"])
        try:
            ready = self.ready(self.root/"leaf-ready", parent)
            outer_row, inner_row = self.row("outer"), self.row("inner")
            pids = [parent.pid, outer_row["owned_pid"], outer_row["keeper"]["keeper_pid"], inner_row["owned_pid"], inner_row["keeper"]["keeper_pid"], ready["grandchild"]]
            self.remember(pids)
            self.assertEqual(ready["pid"], inner_row["owned_pid"])
            self.assertEqual(ready["pgid"], ready["pid"])
            self.assertEqual(ready["sid"], os.getsid(0))
            self.assertEqual(len({parent.pid, outer_row["owned_pgid"], inner_row["owned_pgid"]}), 3)
            os.killpg(parent.pid, signal.SIGKILL)
            parent.wait(timeout=3)
            self.assertEqual(parent.returncode, -signal.SIGKILL)
            self.gone(pids)
            self.assert_leaf_raw("inner")
            self.assertIsNone(survivor.poll(), "unrelated survivor was disturbed")
        finally:
            survivor.kill()
            survivor.wait(timeout=3)

    def test_real_outer_release_timeout_contains_cache_group_and_keeps_primary(self):
        from v3_final_release_gate import run_child_gate
        outer = self.script("cache-child", self.leaf_command())
        primary = None
        try:
            run_child_gate(label="inert cache owner", command=[sys.executable, "-B", "-u", "-c", outer], repo=cache.ROOT, cwd=self.root,
                           env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), timeout=1, evidence_dir=self.root/"parent-evidence")
        except subprocess.TimeoutExpired as error:
            primary = error
        self.assertIsInstance(primary, subprocess.TimeoutExpired)
        ready = self.ready(self.root/"leaf-ready")
        child_row = self.row("cache-child")
        component = json.loads((self.root/"parent-evidence/components/inert-cache-owner.json").read_text())
        parent_row, = component["records"]
        self.assertTrue(parent_row["timed_out"])
        self.assertTrue(parent_row["keeper"]["keeper_reaped"])
        self.assertEqual(child_row["owned_pid"], ready["pid"])
        self.assertNotEqual(child_row["owned_pgid"], parent_row["pid"])
        # These identities are now killed/adopted zombies. A process that has
        # already been reaped needs no signal; collect only recorded children.
        pids = [child_row["owned_pid"], child_row["keeper"]["keeper_pid"], ready["grandchild"]]
        for pid in pids:
            current = self.identity(pid)
            if current is not None:
                self.identities[pid] = current
        self.gone(pids)
        self.assert_leaf_raw("cache-child")
        with self.assertRaises(ChildProcessError):
            os.waitpid(parent_row["keeper"]["keeper_pid"], os.WNOHANG)

    def test_normal_tracer_exit_drains_residual_group_without_changing_success(self):
        evidence = cache.Evidence(self.root/"normal-residual")
        code = ('import subprocess,sys;'
                'child=subprocess.Popen([sys.executable,"-B","-c","import time;time.sleep(60)"]);'
                'print(child.pid,flush=True)')
        returncode, output, _ = evidence.invoke([sys.executable,"-B","-u","-c",code], self.root, os.environ.copy(), "residual", timeout=3)
        self.assertEqual(returncode, 0)
        row, = evidence.report["commands"]
        self.assertEqual(row["returncode"], 0)
        self.assertEqual(row["keeper"]["finish"], "normal group drain")
        self.assertTrue(row["keeper"]["keeper_reaped"])
        self.assertEqual(row["cleanup_notes"], [])
        descendant = int(output)
        current = self.identity(descendant)
        if current is not None:
            self.identities[descendant] = current
        self.gone([descendant])
        for pid in (row["owned_pid"], row["keeper"]["keeper_pid"]):
            with self.assertRaises(ChildProcessError):
                os.waitpid(pid, os.WNOHANG)


if __name__ == "__main__":
    unittest.main()
