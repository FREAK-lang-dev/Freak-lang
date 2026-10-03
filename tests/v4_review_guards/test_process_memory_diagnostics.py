"""Resource failures retain bounded process/tool evidence after scratch cleanup."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("memory_diagnostic_checks", ROOT / "src/compiler/v4/check_v4.py")
checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checks)
SPEC = importlib.util.spec_from_file_location("memory_diagnostic_benchmark", ROOT / "v4_scale_bench.py")
benchmark = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(benchmark)


def stat_record(pid, pgid, start=100):
    fields = ["S", "1", str(pgid), *(["0"] * 16), str(start)]
    return f"{pid} (nm (helper)) " + " ".join(fields)


class ProcessMemoryDiagnostics(unittest.TestCase):
    def setUp(self):
        self.windows_job_type = checks.WindowsJob
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.proc = Path(temporary.name)
        self.enterContext(patch.object(checks, "POSIX_PROC_ROOT", self.proc))

    def process(self, pid, pgid, rss, swap=0):
        entry = self.proc / str(pid)
        entry.mkdir()
        (entry / "stat").write_text(stat_record(pid, pgid), encoding="ascii")
        (entry / "status").write_text(f"VmRSS: {rss} kB\nVmSwap: {swap} kB\n", encoding="ascii")
        (entry / "cmdline").write_bytes(b"nm\0secret-token\0--password=secret\0")
        (entry / "maps").write_text("001-002 r-xp 000 01:02 1 /lib/libLLVM-19.so\n", encoding="ascii")
        return entry

    def test_only_matching_group_contributes_and_rss_plus_swap_is_exact(self):
        self.process(10, 10, 20, 3)
        self.process(11, 10, 40, 5)
        self.process(12, 99, 9999, 9999)
        sample = {}
        self.assertEqual(checks.posix_process_group_memory_bytes(10, sample=sample), 68 * 1024)
        self.assertEqual(sample["process_count"], 2)
        self.assertEqual([row["pid"] for row in sample["processes"]], [11, 10])
        self.assertEqual(sample["processes"][0]["start_ticks"], 100)

    def test_recycled_pid_or_changed_group_is_not_counted(self):
        self.process(10, 10, 20)
        changing = self.process(11, 10, 9999)
        original_read = Path.read_text
        for replacement in (stat_record(11, 10, start=101), stat_record(11, 99)):
            reads = 0

            def read(path, *args, **kwargs):
                nonlocal reads
                if path == changing / "stat":
                    reads += 1
                    return stat_record(11, 10) if reads == 1 else replacement
                return original_read(path, *args, **kwargs)

            with self.subTest(replacement=replacement), patch.object(Path, "read_text", read):
                sample = {}
                self.assertEqual(checks.posix_process_group_memory_bytes(10, sample=sample), 20 * 1024)
                self.assertEqual([row["pid"] for row in sample["processes"]], [10])

    def test_large_group_keeps_total_and_top_contributors_with_bounded_redaction(self):
        for pid in range(10, 30):
            entry = self.process(pid, 10, pid)
            (entry / "cmdline").write_bytes(b"secret-token" * 1000)
            mappings = "".join(f"001-002 r-xp 000 01:02 1 /lib/lib{i}.so\n" for i in range(400))
            (entry / "maps").write_text("001-002 r-xp 000 01:02 1 /lib/libLLVM-19.so\n" + mappings)
        sample = {}
        self.assertEqual(checks.posix_process_group_memory_bytes(10, sample=sample), sum(range(10, 30)) * 1024)
        self.assertEqual(sample["processes_omitted"], 12)
        with patch.object(checks.os, "readlink", return_value="/usr/bin/nm"):
            text = checks.process_memory_diagnostics(sample)
        self.assertLess(len(text), 16384)
        self.assertNotIn("secret-token", text)
        rows = json.loads(text)["processes"]
        self.assertEqual(len(rows), 8)
        self.assertEqual([row["pid"] for row in rows], list(range(29, 21, -1)))
        self.assertTrue(all(row["cmdline"]["truncated"] for row in rows))
        self.assertTrue(all(row["libraries_truncated"] for row in rows))
        self.assertTrue(all("libLLVM-19.so" in row["libraries"] for row in rows))

    def test_later_pid_reuse_keeps_observed_memory_without_mixing_identity_details(self):
        entry = self.process(10, 10, 20)
        sample = {}
        checks.posix_process_group_memory_bytes(10, sample=sample)
        (entry / "stat").write_text(stat_record(10, 10, start=101), encoding="ascii")
        with patch.object(checks.os, "readlink") as readlink:
            diagnostic = json.loads(checks.process_memory_diagnostics(sample))
        self.assertEqual(diagnostic["memory_bytes"], 20 * 1024)
        self.assertEqual(diagnostic["processes"][0]["identity_status"], "changed-or-gone")
        readlink.assert_not_called()

    def test_ps_fallback_retains_existing_rss_measurement(self):
        result = subprocess.CompletedProcess([], 0, "10 20\n10 30\n99 9999\n", "")
        with patch.object(checks, "POSIX_PROC_ROOT", self.proc / "absent"), \
                patch.object(checks.subprocess, "run", return_value=result):
            sample = {}
            self.assertEqual(checks.posix_process_group_memory_bytes(10, sample=sample), 50 * 1024)
        self.assertEqual(sample["sampler"], "ps-rss")
        self.assertEqual(json.loads(checks.process_memory_diagnostics(sample))["memory_bytes"], 50 * 1024)

    def test_windows_job_peak_is_retained_without_procfs_attribution(self):
        job = SimpleNamespace(memory_bytes=lambda: 2 * 1024 * 1024)
        tree = checks.ProcessTree(SimpleNamespace(pid=10), job)
        self.assertEqual(tree.memory_bytes(), 2 * 1024 * 1024)
        job.memory_bytes = lambda: 1024
        self.assertEqual(tree.memory_bytes(), 1024)
        diagnostic = json.loads(tree.memory_diagnostics())
        self.assertEqual(diagnostic["sampler"], "windows-job")
        self.assertEqual(diagnostic["memory_bytes"], 2 * 1024 * 1024)
        self.assertEqual(diagnostic["processes"], [])

    def test_limit_failure_captures_identity_before_termination(self):
        entry = self.process(10, 10, 2048)
        process = SimpleNamespace(pid=10, returncode=None, stdout=io.BytesIO(), stderr=io.BytesIO())
        process.poll = lambda: process.returncode
        tree = checks.ProcessTree(process, None)
        events = []
        original_diagnostic = tree.memory_diagnostics

        def diagnostic():
            events.append("diagnostic")
            self.assertIsNone(process.returncode)
            return original_diagnostic()

        def terminate():
            events.append("terminate")
            process.returncode = -9
            (entry / "stat").unlink()

        with patch.object(checks.ProcessTree, "spawn", return_value=tree), \
                patch.object(tree, "terminate", side_effect=terminate), \
                patch.object(tree, "memory_diagnostics", side_effect=diagnostic), \
                patch.object(checks.os, "readlink", return_value="/usr/bin/nm"), \
                self.assertRaises(RuntimeError) as failure:
            checks.run_with_heartbeat(["unused"], label="test limit", memory_limit_mb=1)
        self.assertEqual(events, ["diagnostic", "terminate"])
        message = str(failure.exception)
        self.assertIn("limit=1MB", message)
        self.assertIn('"exe":"/usr/bin/nm"', message)
        self.assertIn('"rss_bytes":2097152', message)
        self.assertNotIn("secret-token", message)

    def test_persistent_optional_capture_failures_cannot_bypass_tree_cleanup(self):
        self.process(10, 10, 2048)
        faults = (
            (checks, "process_memory_diagnostics", RuntimeError("secret diagnostic payload")),
            (checks.os, "readlink", RuntimeError("secret enrichment payload")),
            (checks.json, "dumps", TypeError("secret serialization payload")),
        )
        for target, attribute, error in faults:
            with self.subTest(failure=attribute):
                process = SimpleNamespace(pid=10, returncode=None, stdout=io.BytesIO(), stderr=io.BytesIO())
                process.poll = lambda: process.returncode
                tree = checks.ProcessTree(process, None)
                events = []
                running_group = {10, 11}
                original_diagnostic = tree.memory_diagnostics

                def diagnostic():
                    events.append("diagnostic")
                    return original_diagnostic()

                def kill_group(group_id, signal):
                    events.append("killpg")
                    running_group.clear()

                def wait(*, timeout):
                    self.assertEqual(timeout, 5)
                    events.append("wait")
                    process.returncode = -9
                    return process.returncode

                process.kill = Mock(side_effect=lambda: events.append("kill"))
                process.wait = Mock(side_effect=wait)
                with patch.object(checks.ProcessTree, "spawn", return_value=tree), \
                        patch.object(checks.os, "killpg", side_effect=kill_group, create=True) as killpg, \
                        patch.object(checks.signal, "SIGKILL", 9, create=True), \
                        patch.object(tree, "close", side_effect=lambda: events.append("close")) as close, \
                        patch.object(tree, "memory_diagnostics", side_effect=diagnostic) as capture, \
                        patch.object(target, attribute, side_effect=error) as fault, \
                        self.assertRaises(RuntimeError) as failure:
                    checks.run_with_heartbeat(["unused"], label="test limit", memory_limit_mb=1)
                self.assertEqual(events, ["diagnostic", "killpg", "kill", "wait", "close"])
                # This fixture models POSIX cleanup even on a Windows host.
                killpg.assert_called_once_with(10, 9)
                process.kill.assert_called_once_with()
                process.wait.assert_called_once_with(timeout=5)
                close.assert_called_once_with()
                capture.assert_called_once_with()
                fault.assert_called_once()
                self.assertFalse(running_group)
                self.assertEqual(process.returncode, -9)
                message = str(failure.exception)
                self.assertIn("test limit exceeded memory limit: observed=2.0MB limit=1MB", message)
                self.assertIn('memory-sample={"diagnostic_error":"capture unavailable"}', message)
                self.assertNotIn("secret", message)

    def test_post_termination_peak_breach_survives_failed_serialization(self):
        process = SimpleNamespace(pid=10, returncode=None, stdout=io.BytesIO(), stderr=io.BytesIO())
        process.poll = lambda: process.returncode
        tree = checks.ProcessTree(process, None)
        events = []
        running_group = {11}

        def wait(*, timeout):
            events.append("wait")
            process.returncode = 0
            return process.returncode

        def kill_group(group_id, signal):
            events.append("killpg")
            running_group.clear()

        process.wait = Mock(side_effect=wait)
        process.kill = Mock()
        with patch.object(checks.ProcessTree, "spawn", return_value=tree), \
                patch.object(tree, "memory_bytes", side_effect=[0, 0, 0, 2 * 1024 * 1024]), \
                patch.object(checks.os, "killpg", side_effect=kill_group, create=True) as killpg, \
                patch.object(checks.signal, "SIGKILL", 9, create=True), \
                patch.object(tree, "close", side_effect=lambda: events.append("close")) as close, \
                patch.object(checks.json, "dumps", side_effect=TypeError("secret serialization payload")) as serialize, \
                self.assertRaises(RuntimeError) as failure:
            checks.run_with_heartbeat(["unused"], label="late peak", memory_limit_mb=1)
        self.assertEqual(events, ["wait", "killpg", "close"])
        killpg.assert_called_once_with(10, 9)
        process.wait.assert_called_once_with(timeout=0.25)
        process.kill.assert_not_called()
        close.assert_called_once_with()
        serialize.assert_called_once()
        self.assertFalse(running_group)
        message = str(failure.exception)
        self.assertIn("late peak exceeded memory limit: peak=2.0MB limit=1MB", message)
        self.assertIn('memory-sample={"diagnostic_error":"capture unavailable"}', message)
        self.assertNotIn("secret", message)

    def cleanup_retry_fixture(self, platform, failure_phase, *, persistent=False, bool_failure=False, fallback_faults=(), permission_failure=False):
        process = SimpleNamespace(pid=10, returncode=None, stdout=io.BytesIO(), stderr=io.BytesIO())
        process.poll = lambda: process.returncode
        events = []
        running_group = {10, 11}
        reaped = False
        attempts = {"terminate": 0, "kill": 0, "wait": 0, "close": 0}
        last_error = 0
        handle = object()
        job = None

        if platform == "windows":
            # Exercise the real WindowsJob terminate/close methods through a
            # mocked kernel API; ctypes and a Windows host are unnecessary.
            job = checks.WindowsJob.__new__(checks.WindowsJob)
            job.handle = handle

        def terminate(*args):
            nonlocal last_error
            events.append("job-terminate" if job is not None else "killpg")
            if job is not None:
                self.assertEqual(args, (handle, 1))
                self.assertIs(job.handle, handle)
            else:
                self.assertEqual(args, (10, 9))
            attempts["terminate"] += 1
            if failure_phase == "terminate" and (persistent or attempts["terminate"] == 1):
                if bool_failure:
                    last_error = 5
                    return 0
                if permission_failure:
                    raise PermissionError(1, "group signal denied")
                raise OSError("temporary termination failure")
            running_group.clear()
            return 1

        def wait(*, timeout):
            nonlocal reaped
            self.assertEqual(timeout, 5)
            events.append("wait")
            attempts["wait"] += 1
            if "wait" in fallback_faults:
                raise OSError(13, "secret reaping payload")
            if failure_phase == "wait" and (persistent or attempts["wait"] == 1):
                raise OSError("temporary reaping failure")
            if 10 in running_group:
                raise subprocess.TimeoutExpired(["unused"], timeout)
            process.returncode = -9
            reaped = True
            return process.returncode

        def close_handle(actual_handle):
            nonlocal last_error
            events.append("job-close")
            self.assertIs(actual_handle, handle)
            attempts["close"] += 1
            if "close" in fallback_faults or (failure_phase == "close" and (persistent or attempts["close"] == 1)):
                last_error = 5
                return 0
            running_group.clear()  # KILL_ON_JOB_CLOSE fallback.
            return 1

        if job is not None:
            job.ctypes = SimpleNamespace(
                get_last_error=Mock(side_effect=lambda: last_error),
                WinError=Mock(side_effect=lambda code: OSError(code, "Windows API failure")),
            )
            job.kernel32 = SimpleNamespace(
                TerminateJobObject=Mock(side_effect=terminate),
                CloseHandle=Mock(side_effect=close_handle),
            )
        def kill():
            events.append("kill")
            attempts["kill"] += 1
            if "kill" in fallback_faults:
                raise OSError(12, "secret direct kill payload")
            running_group.discard(10)

        process.kill = Mock(side_effect=kill)
        process.wait = Mock(side_effect=wait)
        tree = checks.ProcessTree(process, job)
        original_close = tree.close

        def close():
            events.append("close")
            if job is None and "close" in fallback_faults:
                raise OSError(14, "secret close payload")
            original_close()

        def diagnostic():
            events.append("diagnostic")
            raise TypeError("secret persistent serialization payload")

        self.enterContext(patch.object(checks.ProcessTree, "spawn", return_value=tree))
        self.enterContext(patch.object(tree, "memory_bytes", return_value=2 * 1024 * 1024))
        capture = self.enterContext(patch.object(tree, "memory_diagnostics", side_effect=diagnostic))
        close_mock = self.enterContext(patch.object(tree, "close", side_effect=close))
        # Both paths must be exercised on every host, including Windows CI.
        self.enterContext(patch.object(checks.os, "killpg", side_effect=terminate, create=True))
        self.enterContext(patch.object(checks.signal, "SIGKILL", 9, create=True))
        return SimpleNamespace(
            process=process, tree=tree, job=job, handle=handle, events=events,
            running_group=running_group, attempts=attempts, capture=capture, close=close_mock,
        )

    def test_transient_termination_and_reaping_failures_retry_before_closing(self):
        for platform in ("posix", "windows"):
            for phase in ("terminate", "wait"):
                with self.subTest(platform=platform, failure=phase):
                    fixture = self.cleanup_retry_fixture(platform, phase)
                    with self.assertRaises(RuntimeError) as failure:
                        checks.run_with_heartbeat(["unused"], label="retry limit", memory_limit_mb=1)
                    terminate_event = "job-terminate" if platform == "windows" else "killpg"
                    expected = ["diagnostic", terminate_event, "kill"]
                    if phase == "wait":
                        expected += ["wait"]
                    expected += [terminate_event, "kill", "wait", "close"]
                    if platform == "windows":
                        expected += ["job-close"]
                        fixture.job.kernel32.CloseHandle.assert_called_once_with(fixture.handle)
                        self.assertIsNone(fixture.job.handle)
                    self.assertEqual(fixture.events, expected)
                    self.assertFalse(fixture.running_group)
                    self.assertEqual(fixture.process.returncode, -9)
                    fixture.close.assert_called_once_with()
                    fixture.capture.assert_called_once_with()
                    self.assertEqual(fixture.attempts["terminate"], 2)
                    self.assertEqual(fixture.attempts["wait"], 2 if phase == "wait" else 1)
                    message = str(failure.exception)
                    self.assertIn("retry limit exceeded memory limit: observed=2.0MB limit=1MB", message)
                    self.assertIn('memory-sample={"diagnostic_error":"capture unavailable"}', message)
                    self.assertNotIn("secret", message)

    def test_persistent_cleanup_failure_attempts_independent_final_fallback(self):
        for platform in ("posix", "windows"):
            for phase in ("terminate", "wait"):
                with self.subTest(platform=platform, failure=phase):
                    fixture = self.cleanup_retry_fixture(platform, phase, persistent=True)
                    with self.assertRaises(RuntimeError) as failure:
                        checks.run_with_heartbeat(["unused"], label="persistent limit", memory_limit_mb=1)
                    terminate_event = "job-terminate" if platform == "windows" else "killpg"
                    attempt_events = [terminate_event, "kill"]
                    if phase == "wait":
                        attempt_events += ["wait"]
                    expected = ["diagnostic"] + attempt_events * 2 + ["kill", "close"]
                    if platform == "windows":
                        expected += ["job-close"]
                    expected += ["wait"] * (2 if phase == "wait" else 1)
                    self.assertEqual(fixture.events, expected)
                    self.assertEqual(fixture.attempts["terminate"], 2)
                    self.assertEqual(fixture.attempts["wait"], 4 if phase == "wait" else 1)
                    fixture.close.assert_called_once_with()
                    fixture.capture.assert_called_once_with()
                    self.assertEqual(fixture.process.returncode, None if phase == "wait" else -9)
                    self.assertEqual(fixture.running_group, {11} if platform == "posix" and phase == "terminate" else set())
                    if platform == "windows":
                        fixture.job.kernel32.CloseHandle.assert_called_once_with(fixture.handle)
                        self.assertIsNone(fixture.job.handle)
                    self.assertIsInstance(failure.exception.__cause__, OSError)
                    self.assertIn("temporary", str(failure.exception.__cause__))
                    message = str(failure.exception)
                    self.assertIn("persistent limit process-tree cleanup failed after 2 attempts", message)
                    self.assertIn("exceeded memory limit: peak=2.0MB limit=1MB", message)
                    self.assertIn('memory-sample={"diagnostic_error":"capture unavailable"}', message)
                    self.assertNotIn("secret", message)
                    self.assertEqual(len(failure.exception.cleanup_errors), 4 if phase == "wait" else 2)
                    self.assertIs(failure.exception.cleanup_errors[0][1], failure.exception.__cause__)

    def test_windows_bool_zero_transient_failures_retry_with_original_guard(self):
        for phase in ("terminate", "close"):
            with self.subTest(failure=phase):
                fixture = self.cleanup_retry_fixture("windows", phase, bool_failure=True)
                with self.assertRaises(RuntimeError) as failure:
                    checks.run_with_heartbeat(["unused"], label="Windows BOOL retry", memory_limit_mb=1)
                if phase == "terminate":
                    expected = ["diagnostic", "job-terminate", "kill", "job-terminate", "kill", "wait", "close", "job-close"]
                    expected_close_count = 1
                else:
                    expected = ["diagnostic", "job-terminate", "kill", "wait", "close", "job-close", "job-terminate", "close", "job-close"]
                    expected_close_count = 2
                self.assertEqual(fixture.events, expected)
                self.assertFalse(fixture.running_group)
                self.assertEqual(fixture.process.returncode, -9)
                self.assertIsNone(fixture.job.handle)
                self.assertEqual(fixture.close.call_count, expected_close_count)
                self.assertEqual(fixture.job.kernel32.CloseHandle.call_count, expected_close_count)
                fixture.job.ctypes.get_last_error.assert_called_once_with()
                fixture.job.ctypes.WinError.assert_called_once_with(5)
                fixture.capture.assert_called_once_with()
                message = str(failure.exception)
                self.assertIn("Windows BOOL retry exceeded memory limit: observed=2.0MB limit=1MB", message)
                self.assertIn('memory-sample={"diagnostic_error":"capture unavailable"}', message)
                self.assertNotIn("secret", message)

    def test_independent_final_fallback_faults_are_bounded_and_all_causes_retained(self):
        for platform in ("posix", "windows"):
            for faults in ((), ("kill",), ("wait",), ("close",), ("kill", "close"), ("kill", "wait", "close")):
                with self.subTest(platform=platform, faults=faults):
                    fixture = self.cleanup_retry_fixture(
                        platform, "terminate", persistent=True,
                        bool_failure=platform == "windows", permission_failure=platform == "posix",
                        fallback_faults=faults,
                    )
                    with self.assertRaises(RuntimeError) as failure:
                        checks.run_with_heartbeat(["unused"], label="final fallback", memory_limit_mb=1)
                    terminate_event = "job-terminate" if platform == "windows" else "killpg"
                    expected = ["diagnostic", terminate_event, "kill", terminate_event, "kill"]
                    expected += ["kill"] * (2 if "kill" in faults else 1)
                    for _ in range(2 if "close" in faults else 1):
                        expected += ["close"] + (["job-close"] if platform == "windows" else [])
                    unreapable = "wait" in faults or ("kill" in faults and (platform == "posix" or "close" in faults))
                    expected += ["wait"] * (2 if unreapable else 1)
                    self.assertEqual(fixture.events, expected)
                    self.assertEqual(fixture.attempts["terminate"], 2)
                    self.assertEqual(fixture.attempts["kill"], 4 if "kill" in faults else 3)
                    fixture.capture.assert_called_once_with()
                    self.assertEqual(fixture.close.call_count, 2 if "close" in faults else 1)
                    self.assertEqual(fixture.process.wait.call_count, 2 if unreapable else 1)
                    self.assertEqual(fixture.process.returncode, None if unreapable else -9)
                    if platform == "windows":
                        self.assertIs(fixture.job.handle, fixture.handle if "close" in faults else None)
                        self.assertEqual(bool(fixture.running_group), "close" in faults)
                    else:
                        self.assertIn(11, fixture.running_group)  # Launcher kill cannot prove descendants stopped.
                    errors = failure.exception.cleanup_errors
                    expected_error_count = 2 + (4 if "kill" in faults else 0)
                    expected_error_count += 2 * (int(unreapable) + int("close" in faults))
                    self.assertEqual(len(errors), expected_error_count)
                    self.assertIs(failure.exception.__cause__, errors[0][1])
                    self.assertEqual(failure.exception.__cause__.errno, 5 if platform == "windows" else 1)
                    observed = {(stage, getattr(error, "errno", None)) for stage, error in errors}
                    self.assertIn(("group termination", 5 if platform == "windows" else 1), observed)
                    for stage, errno, enabled in (
                        ("launcher kill", 12, "kill" in faults),
                        ("launcher reap", 13, "wait" in faults),
                        ("resource close", 5 if platform == "windows" else 14, "close" in faults),
                    ):
                        if enabled:
                            self.assertIn((stage, errno), observed)
                    if unreapable and "wait" not in faults:
                        self.assertIn(("launcher reap", None), observed)
                    message = str(failure.exception)
                    self.assertIn("exceeded memory limit: peak=2.0MB limit=1MB", message)
                    self.assertIn('memory-sample={"diagnostic_error":"capture unavailable"}', message)
                    self.assertNotIn("secret", message)
                    self.assertLess(len(message), 2048)
                    known_closed = platform == "windows" and not unreapable and "close" not in faults
                    self.assertIn("tree-closed=" + str(known_closed), message)

    def test_final_cleanup_failure_retains_output_and_timeout_guard_context(self):
        def thread(*, target, args, daemon):
            return SimpleNamespace(start=lambda: target(*args), join=lambda timeout: None)

        for guard in ("output", "timeout"):
            with self.subTest(guard=guard):
                fixture = self.cleanup_retry_fixture("posix", "terminate", persistent=True, permission_failure=True)
                stdout_payload = b"A" * (1024 * 1024 + 3000) + b"stdout-final-tail"
                stderr_payload = b"B" * (1024 * 1024 + 5000) + b"stderr-final-tail"
                fixture.process.stdout = io.BytesIO(stdout_payload)
                fixture.process.stderr = io.BytesIO(stderr_payload)
                command = ["unused", "full-command"]
                artifacts = self.proc / guard
                with patch.object(checks.threading, "Thread", side_effect=thread), \
                        patch.object(checks.time, "monotonic", side_effect=[0, 2, 2]), \
                        self.assertRaises(RuntimeError) as failure:
                    benchmark.guarded_job(
                        None, command, artifacts, "fallback guard",
                        1 if guard == "timeout" else None, None,
                        1 if guard == "output" else 8, runner=checks.run_with_heartbeat,
                    )
                error = failure.exception
                fixture.capture.assert_not_called()
                self.assertFalse(fixture.running_group - {11})
                self.assertEqual(fixture.process.returncode, -9)
                self.assertIs(error.__cause__, error.cleanup_errors[0][1])
                self.assertEqual(error.__cause__.errno, 1)
                self.assertEqual(error.guard_trigger, guard)
                self.assertEqual(error.stdout_total_bytes, len(stdout_payload))
                self.assertEqual(error.stderr_total_bytes, len(stderr_payload))
                self.assertEqual(error.guard_error.stdout_total_bytes, len(stdout_payload))
                self.assertEqual(error.guard_error.stderr_total_bytes, len(stderr_payload))
                self.assertTrue(error.output.endswith(stdout_payload[-2000:].decode()))
                self.assertTrue(error.stderr.endswith(stderr_payload[-2000:].decode()))
                self.assertEqual(error.guard_error.output, error.output)
                self.assertEqual(error.guard_error.stderr, error.stderr)
                self.assertEqual((artifacts / "stdout.txt").read_text(), error.output)
                self.assertEqual((artifacts / "stderr.txt").read_text(), error.stderr)
                self.assertEqual(json.loads((artifacts / "command.json").read_text())["command"], command)
                message = str(error)
                self.assertEqual((artifacts / "failure.txt").read_text(), message)
                self.assertIn("stdout-tail=" + stdout_payload[-2000:].decode(), message)
                self.assertIn("stderr-tail=" + stderr_payload[-2000:].decode(), message)
                if guard == "output":
                    self.assertIn("exceeded output limit: stdout=1.0MB stderr=1.0MB limit=1MB-per-stream", message)
                    self.assertIsInstance(error.guard_error, RuntimeError)
                else:
                    self.assertIn("exceeded timeout: limit=1s", message)
                    self.assertIsInstance(error.guard_error, subprocess.TimeoutExpired)
                    self.assertIs(error.guard_error.cmd, command)
                    self.assertEqual(error.guard_error.timeout, 1)
                self.assertIn("tree-closed=False", message)

    def test_failed_cleanup_joins_deferred_readers_before_freezing_guard_evidence(self):
        for guard in ("output", "timeout"):
            with self.subTest(guard=guard):
                fixture = self.cleanup_retry_fixture("posix", "terminate", persistent=True, permission_failure=True)
                stdout_prefix = b"A" * (1024 * 1024 + 3000)
                stderr_prefix = b"B" * (1024 * 1024 + 5000)
                stdout_tail = b"DEFERRED-STDOUT-FINAL-TAIL\n"
                stderr_tail = b"DEFERRED-STDERR-FINAL-TAIL\n"
                stdout_payload = stdout_prefix + stdout_tail
                stderr_payload = stderr_prefix + stderr_tail
                fixture.process.stdout = io.BytesIO(stdout_payload)
                fixture.process.stderr = io.BytesIO(stderr_payload)
                workers = []

                def thread(*, target, args, daemon):
                    pipe = args[0]
                    prefix_size = len(stdout_prefix) if pipe is fixture.process.stdout else len(stderr_prefix)

                    def start():
                        # Scheduling a reader does not synchronously drain it.
                        self.assertEqual(pipe.tell(), 0)
                        fixture.events.append("reader-start")

                    def join(*, timeout):
                        self.assertEqual(timeout, 5)
                        # Reader waits must never delay guard enforcement. Both
                        # termination attempts and the final fallback preceded
                        # this bounded wait, even though a descendant remains.
                        self.assertEqual(fixture.attempts["terminate"], 2)
                        self.assertEqual(fixture.attempts["kill"], 3)
                        self.assertEqual(fixture.process.returncode, -9)
                        fixture.process.wait.assert_called_once_with(timeout=5)
                        self.assertTrue(fixture.running_group)
                        fixture.events.append("reader-join")
                        target(pipe)

                    worker = SimpleNamespace(
                        start=Mock(side_effect=start), join=Mock(side_effect=join),
                        target=target, pipe=pipe, prefix_size=prefix_size,
                    )
                    workers.append(worker)
                    return worker

                delivered_prefix = False

                def memory_bytes():
                    nonlocal delivered_prefix
                    if not delivered_prefix:
                        # Model independent scheduling after both starts. The
                        # final bytes stay pending until join after cleanup.
                        self.assertEqual(len(workers), 2)
                        for worker in workers:
                            worker.start.assert_called_once_with()
                            worker.target(io.BytesIO(worker.pipe.read(worker.prefix_size)))
                            worker.join.assert_not_called()
                        delivered_prefix = True
                    return 2 * 1024 * 1024

                command = ["unused", "deferred-command"]
                artifacts = self.proc / ("deferred-" + guard)
                with patch.object(checks.threading, "Thread", side_effect=thread), \
                        patch.object(fixture.tree, "memory_bytes", side_effect=memory_bytes), \
                        patch.object(checks.time, "monotonic", side_effect=[0, 2, 2]), \
                        patch.object(checks.subprocess, "Popen", side_effect=AssertionError("actual process forbidden")), \
                        self.assertRaises(RuntimeError) as failure:
                    benchmark.guarded_job(
                        None, command, artifacts, "deferred guard",
                        1 if guard == "timeout" else None, None,
                        1 if guard == "output" else 8, runner=checks.run_with_heartbeat,
                    )
                error = failure.exception
                for worker in workers:
                    worker.join.assert_called_once_with(timeout=5)
                    self.assertTrue(worker.pipe.closed)
                self.assertLess(fixture.events.index("wait"), fixture.events.index("reader-join"))
                self.assertIs(error.__cause__, error.cleanup_errors[0][1])
                self.assertEqual(error.guard_trigger, guard)
                self.assertEqual(error.stdout_total_bytes, len(stdout_payload))
                self.assertEqual(error.stderr_total_bytes, len(stderr_payload))
                self.assertEqual(error.guard_error.stdout_total_bytes, len(stdout_payload))
                self.assertEqual(error.guard_error.stderr_total_bytes, len(stderr_payload))
                self.assertTrue(error.output.endswith(stdout_tail.decode()))
                self.assertTrue(error.stderr.endswith(stderr_tail.decode()))
                self.assertEqual(error.guard_error.output, error.output)
                self.assertEqual(error.guard_error.stderr, error.stderr)
                self.assertEqual((artifacts / "stdout.txt").read_text(), error.output)
                self.assertEqual((artifacts / "stderr.txt").read_text(), error.stderr)
                self.assertEqual((artifacts / "failure.txt").read_text(), str(error))
                self.assertEqual(json.loads((artifacts / "command.json").read_text())["command"], command)
                self.assertIn("stdout-tail=" + stdout_payload[-2000:].decode(), str(error))
                self.assertIn("stderr-tail=" + stderr_payload[-2000:].decode(), str(error))
                if guard == "timeout":
                    self.assertIsInstance(error.guard_error, subprocess.TimeoutExpired)
                    self.assertIs(error.guard_error.cmd, command)
                    self.assertEqual(error.guard_error.timeout, 1)
                else:
                    self.assertIsInstance(error.guard_error, RuntimeError)

    def test_windows_bool_zero_persistent_failures_keep_handle_and_os_cause(self):
        for phase in ("terminate", "close"):
            with self.subTest(failure=phase):
                fixture = self.cleanup_retry_fixture("windows", phase, bool_failure=True, persistent=True)
                with self.assertRaises(RuntimeError) as failure:
                    checks.run_with_heartbeat(["unused"], label="Windows BOOL persistent", memory_limit_mb=1)
                if phase == "terminate":
                    expected = ["diagnostic", "job-terminate", "kill", "job-terminate", "kill", "kill", "close", "job-close", "wait"]
                    self.assertFalse(fixture.running_group)
                    self.assertEqual(fixture.process.returncode, -9)
                    fixture.process.wait.assert_called_once_with(timeout=5)
                    fixture.close.assert_called_once_with()
                    fixture.job.kernel32.CloseHandle.assert_called_once_with(fixture.handle)
                    self.assertIsNone(fixture.job.handle)
                else:
                    expected = ["diagnostic", "job-terminate", "kill", "wait", "close", "job-close"]
                    expected += ["job-terminate", "close", "job-close"]
                    expected += ["close", "job-close"] * 2 + ["wait"]
                    self.assertFalse(fixture.running_group)
                    self.assertEqual(fixture.process.returncode, -9)
                    self.assertEqual(fixture.process.wait.call_count, 2)
                    self.assertEqual(fixture.close.call_count, 4)
                    self.assertEqual(fixture.job.kernel32.CloseHandle.call_count, 4)
                    self.assertIs(fixture.job.handle, fixture.handle)
                self.assertEqual(fixture.events, expected)
                fixture.capture.assert_called_once_with()
                self.assertEqual(fixture.job.ctypes.get_last_error.call_count, 4 if phase == "close" else 2)
                self.assertEqual(fixture.job.ctypes.WinError.call_count, 4 if phase == "close" else 2)
                self.assertIsInstance(failure.exception.__cause__, OSError)
                self.assertEqual(failure.exception.__cause__.errno, 5)
                message = str(failure.exception)
                self.assertIn("Windows BOOL persistent process-tree cleanup failed after 2 attempts", message)
                self.assertIn("exceeded memory limit: peak=2.0MB limit=1MB", message)
                self.assertIn('memory-sample={"diagnostic_error":"capture unavailable"}', message)
                self.assertNotIn("secret", message)

    def test_on_time_completion_cleanup_crossing_deadline_is_not_a_timeout(self):
        fixture = self.cleanup_retry_fixture("posix", "terminate", persistent=True, permission_failure=True)
        fixture.process.stdout = io.BytesIO(b"completed-output")
        fixture.process.stderr = io.BytesIO(b"completed-stderr")
        original_wait = fixture.process.wait

        def wait(*, timeout):
            if timeout < 5:
                fixture.process.returncode = 0
                fixture.running_group.discard(10)
                return 0
            return original_wait(timeout=timeout)

        def thread(*, target, args, daemon):
            return SimpleNamespace(start=lambda: target(*args), join=lambda timeout: None)

        fixture.process.wait = Mock(side_effect=wait)
        with patch.object(checks.threading, "Thread", side_effect=thread), \
                patch.object(checks.time, "monotonic", side_effect=[0, 0.25, 20]), \
                self.assertRaises(RuntimeError) as failure:
            checks.run_with_heartbeat(["unused"], label="completed cleanup", timeout_seconds=1)
        error = failure.exception
        self.assertEqual(error.guard_trigger, "completed")
        self.assertIsNone(error.guard_error)
        self.assertNotIn("exceeded timeout", str(error))
        self.assertEqual(error.output, "completed-output")
        self.assertEqual(error.stderr, "completed-stderr")
        self.assertIs(error.__cause__, error.cleanup_errors[0][1])

    def invalid_windows_job(self, stage, mapped_errno=9):
        job = self.windows_job_type.__new__(self.windows_job_type)
        job.handle = 47  # A numeric value could be reused for a different kernel object.
        error = OSError(mapped_errno, "private Windows error payload")
        error.winerror = 6
        job.ctypes = SimpleNamespace(get_last_error=Mock(return_value=6), WinError=Mock(return_value=error))
        job.kernel32 = SimpleNamespace(
            TerminateJobObject=Mock(return_value=0 if stage == "terminate" else 1),
            CloseHandle=Mock(return_value=0 if stage == "close" else 1),
            AssignProcessToJobObject=Mock(return_value=0 if stage == "assign" else 1),
            QueryInformationJobObject=Mock(side_effect=AssertionError("retired identity used")),
        )
        return job, error

    def test_windows_invalid_handle_is_terminal_without_api_reuse(self):
        for stage in ("terminate", "close"):
            for errno in (9, 13):
                with self.subTest(stage=stage, mapped_errno=errno):
                    job, error = self.invalid_windows_job(stage, errno)
                    with self.assertRaises(OSError) as failure:
                        getattr(job, stage)()
                    self.assertIs(failure.exception, error)
                    self.assertIsNone(job.handle)
                    self.assertIs(job.invalid_handle_error, error)
                    before = {name: method.call_count for name, method in vars(job.kernel32).items()}
                    for action in (job.terminate, job.close, lambda: job.assign(SimpleNamespace(_handle=99))):
                        with self.assertRaises(OSError) as repeated:
                            action()
                        self.assertIs(repeated.exception, error)
                    self.assertIsNone(job.memory_bytes())
                    self.assertEqual(before, {name: method.call_count for name, method in vars(job.kernel32).items()})
                    job.ctypes.get_last_error.assert_called_once_with()
                    job.ctypes.WinError.assert_called_once_with(6)

        job, error = self.invalid_windows_job("assign")
        with self.assertRaises(OSError) as failure:
            job.assign(SimpleNamespace(_handle=99))
        self.assertIs(failure.exception, error)
        self.assertEqual(job.handle, 47)  # Assign has two handles; the process may be invalid.
        self.assertIsNone(getattr(job, "invalid_handle_error", None))
        job.terminate()
        job.close()
        self.assertIsNone(job.handle)

        job, error = self.invalid_windows_job("close", mapped_errno=6)
        error.winerror = 5
        job.ctypes.get_last_error.return_value = 5
        with self.assertRaises(OSError):
            job.close()
        self.assertEqual(job.handle, 47)  # An errno6 mapping alone is never Win32 invalid6.
        self.assertIsNone(getattr(job, "invalid_handle_error", None))
        job.kernel32.CloseHandle.return_value = 1
        job.close()
        self.assertIsNone(job.handle)

    def test_windows_invalid_handle_cleanup_is_unconfirmed_and_preserves_cause(self):
        for stage in ("terminate", "close"):
            with self.subTest(stage=stage):
                fixture = self.cleanup_retry_fixture("windows", stage, bool_failure=True, persistent=True)
                error = OSError(9, "private invalid handle payload")
                error.winerror = 6
                fixture.job.ctypes.get_last_error = Mock(return_value=6)
                fixture.job.ctypes.WinError = Mock(return_value=error)
                with self.assertRaises(RuntimeError) as failure:
                    checks.run_with_heartbeat(["unused"], label="invalid Job", memory_limit_mb=1)
                retained = failure.exception
                self.assertIs(retained.__cause__, error)
                self.assertIs(retained.cleanup_errors[0][1], error)
                self.assertIsNone(fixture.job.handle)
                self.assertIs(fixture.job.invalid_handle_error, error)
                self.assertEqual(fixture.job.kernel32.TerminateJobObject.call_count, 1)
                self.assertEqual(fixture.job.kernel32.CloseHandle.call_count, 1 if stage == "close" else 0)
                fixture.process.kill.assert_called()
                if stage == "terminate":
                    fixture.process.wait.assert_called_once_with(timeout=5)
                else:
                    self.assertEqual(fixture.process.wait.call_count, 2)
                self.assertEqual(fixture.running_group, {11} if stage == "terminate" else set())
                self.assertIn("tree-closed=False", str(retained))
                self.assertIn("resource-closed=False", str(retained))
                self.assertIn("errno=9:winerror=6", str(retained))
                self.assertNotIn("private invalid handle payload", str(retained))
                self.assertEqual(len(retained.cleanup_errors), 4)

    def test_cached_invalid_error_clears_launcher_fault_between_attempts(self):
        fixture = self.cleanup_retry_fixture("windows", "terminate", bool_failure=True, persistent=True)
        invalid = OSError(9, "private invalid handle payload")
        invalid.winerror = 6
        fixture.job.ctypes.get_last_error = Mock(return_value=6)
        fixture.job.ctypes.WinError = Mock(return_value=invalid)
        original_kill = fixture.process.kill
        launcher_fault = OSError(12, "private launcher payload")
        kill_calls = 0

        def kill():
            nonlocal kill_calls
            kill_calls += 1
            if kill_calls == 1:
                raise launcher_fault
            original_kill()

        fixture.process.kill = Mock(side_effect=kill)
        with self.assertRaises(RuntimeError) as failure:
            checks.run_with_heartbeat(["unused"], label="cached invalid Job", memory_limit_mb=1)
        self.assertIs(failure.exception.__cause__, invalid)
        children = [error for stage, error in failure.exception.cleanup_errors if stage == "launcher kill"]
        self.assertEqual(children, [launcher_fault])
        self.assertIsNone(invalid.launcher_cleanup_error)
        self.assertEqual(fixture.job.kernel32.TerminateJobObject.call_count, 1)
        fixture.job.kernel32.CloseHandle.assert_not_called()
        self.assertIn("tree-closed=False", str(failure.exception))

    def startup_rollback_fixture(self, phase, faults):
        process = SimpleNamespace(pid=10, _handle=object(), returncode=None)
        process.poll = lambda: process.returncode
        events = []
        running_group = set() if phase == "popen" else {10}
        attempts = {"job": 0, "kill": 0, "wait": 0, "close": 0}
        assigned = False
        exit_requested = False
        last_error = 0
        handle = object()
        job = self.windows_job_type.__new__(self.windows_job_type)
        job.handle = handle
        startup_error = OSError({"assign": 7, "resume": 8, "popen": 10}[phase], "original startup failure")

        def fails(step):
            attempts[step] += 1
            count = faults.get(step, 0)
            return count is None or attempts[step] <= count

        def win_error(code):
            return startup_error if code == startup_error.errno else OSError(code, "cleanup API failure")

        def assign(job_handle, process_handle):
            nonlocal last_error, assigned
            events.append("assign")
            self.assertIs(job_handle, handle)
            self.assertIs(process_handle, process._handle)
            if phase == "assign":
                last_error = 7
                return 0
            assigned = True
            running_group.add(11)
            return 1

        def resume(process_handle):
            events.append("resume")
            self.assertIs(process_handle, process._handle)
            return -1

        def terminate(job_handle, code):
            nonlocal last_error, exit_requested
            events.append("job-terminate")
            self.assertIs(job_handle, handle)
            self.assertIs(job.handle, handle)
            self.assertEqual(code, 1)
            if fails("job"):
                last_error = 5
                return 0
            if assigned:
                exit_requested = True
                running_group.clear()
            return 1

        def kill():
            nonlocal exit_requested
            events.append("kill")
            if fails("kill"):
                raise OSError(11, "direct kill failure")
            exit_requested = True
            running_group.discard(10)

        def wait(*, timeout):
            events.append("wait")
            self.assertEqual(timeout, 5)
            if fails("wait"):
                raise OSError(9, "reaping failure")
            if not exit_requested:
                raise subprocess.TimeoutExpired(["unused"], timeout)
            process.returncode = -9
            return process.returncode

        def close(job_handle):
            nonlocal last_error, exit_requested
            events.append("job-close")
            self.assertIs(job_handle, handle)
            self.assertIs(job.handle, handle)
            if fails("close"):
                last_error = 5
                return 0
            if assigned:
                exit_requested = True
                running_group.clear()
            return 1

        def popen(command, **kwargs):
            events.append("popen")
            self.assertEqual(command, ["unused"])
            self.assertEqual(kwargs["creationflags"], 0x00000004)
            self.assertNotIn("start_new_session", kwargs)
            if phase == "popen":
                raise startup_error
            return process

        job.ctypes = SimpleNamespace(get_last_error=lambda: last_error, WinError=Mock(side_effect=win_error))
        job.kernel32 = SimpleNamespace(
            AssignProcessToJobObject=Mock(side_effect=assign),
            TerminateJobObject=Mock(side_effect=terminate),
            CloseHandle=Mock(side_effect=close),
        )
        job.ntdll = SimpleNamespace(NtResumeProcess=Mock(side_effect=resume), RtlNtStatusToDosError=Mock(return_value=8))
        process.kill = Mock(side_effect=kill)
        process.wait = Mock(side_effect=wait)
        self.enterContext(patch.object(checks.sys, "platform", "win32"))
        self.enterContext(patch.object(checks, "WindowsJob", return_value=job))
        self.enterContext(patch.object(checks.subprocess, "Popen", side_effect=popen))
        return SimpleNamespace(
            job=job, process=process, handle=handle, events=events,
            attempts=attempts, running_group=running_group, startup_error=startup_error,
        )

    def test_windows_startup_failure_rolls_back_despite_job_bool_zero(self):
        for phase in ("assign", "resume"):
            for transient in (None, "kill", "wait", "close"):
                with self.subTest(startup=phase, transient=transient):
                    faults = {"job": None}
                    if transient is not None:
                        faults[transient] = 1
                    fixture = self.startup_rollback_fixture(phase, faults)
                    with self.assertRaises(OSError) as failure:
                        checks.ProcessTree.spawn(["unused"], 1024)
                    prefix = ["popen", "assign"] + (["resume"] if phase == "resume" else [])
                    expected = prefix + ["job-terminate"] * 2 + ["kill"] * (2 if transient == "kill" else 1)
                    expected += ["wait"] * (2 if transient == "wait" else 1)
                    expected += ["job-close"] * (2 if transient == "close" else 1)
                    self.assertEqual(fixture.events, expected)
                    self.assertIs(failure.exception, fixture.startup_error)
                    self.assertFalse(fixture.running_group)
                    self.assertEqual(fixture.process.returncode, -9)
                    self.assertIsNone(fixture.job.handle)
                    if phase == "assign":
                        fixture.job.ntdll.NtResumeProcess.assert_not_called()

    def test_windows_popen_failure_retries_job_close_and_preserves_original_error(self):
        for persistent in (False, True):
            with self.subTest(persistent=persistent):
                fixture = self.startup_rollback_fixture("popen", {"close": None if persistent else 1})
                with self.assertRaises((RuntimeError, OSError)) as failure:
                    checks.ProcessTree.spawn(["unused"], 1024)
                self.assertEqual(fixture.events, ["popen", "job-close", "job-close"])
                fixture.process.kill.assert_not_called()
                fixture.process.wait.assert_not_called()
                fixture.job.kernel32.TerminateJobObject.assert_not_called()
                if persistent:
                    self.assertIs(fixture.job.handle, fixture.handle)
                    self.assertIn("rollback failed", str(failure.exception))
                    self.assertEqual(failure.exception.__cause__.errno, 5)
                    self.assertIs(failure.exception.__context__, fixture.startup_error)
                else:
                    self.assertIsNone(fixture.job.handle)
                    self.assertIs(failure.exception, fixture.startup_error)

    def test_windows_startup_persistent_faults_are_bounded_and_all_cleanup_is_attempted(self):
        for failed_step in ("kill", "wait", "close"):
            with self.subTest(failure=failed_step):
                fixture = self.startup_rollback_fixture("assign", {"job": None, failed_step: None})
                with self.assertRaises(RuntimeError) as failure:
                    checks.ProcessTree.spawn(["unused"], 1024)
                expected = ["popen", "assign", "job-terminate", "job-terminate"]
                expected += ["kill"] * (2 if failed_step == "kill" else 1)
                expected += ["wait"] * (2 if failed_step in ("kill", "wait") else 1)
                expected += ["job-close"] * (2 if failed_step == "close" else 1)
                if failed_step in ("kill", "wait"):
                    expected += ["wait", "wait"]
                self.assertEqual(fixture.events, expected)
                self.assertIn("rollback failed after bounded retries", str(failure.exception))
                self.assertIs(failure.exception.__context__, fixture.startup_error)
                if failed_step == "kill":
                    self.assertEqual(fixture.running_group, {10})
                    self.assertIsNone(fixture.process.returncode)
                    self.assertIsInstance(failure.exception.__cause__, subprocess.TimeoutExpired)
                elif failed_step == "wait":
                    self.assertFalse(fixture.running_group)
                    self.assertIsNone(fixture.process.returncode)
                    self.assertEqual(failure.exception.__cause__.errno, 9)
                else:
                    self.assertFalse(fixture.running_group)
                    self.assertEqual(fixture.process.returncode, -9)
                    self.assertIs(fixture.job.handle, fixture.handle)
                    self.assertEqual(failure.exception.__cause__.errno, 5)

    def test_windows_startup_invalid_handle_close_is_not_reused(self):
        for phase in ("assign", "resume", "popen"):
            with self.subTest(phase=phase):
                fixture = self.startup_rollback_fixture(phase, {"job": None, "close": None})
                invalid = OSError(9, "private invalid close payload")
                invalid.winerror = 6
                original_last_error = fixture.job.ctypes.get_last_error
                original_win_error = fixture.job.ctypes.WinError
                original_close = fixture.job.kernel32.CloseHandle
                close_failed = False

                def close(handle):
                    nonlocal close_failed
                    original_close(handle)
                    close_failed = True
                    return 0

                fixture.job.kernel32.CloseHandle = Mock(side_effect=close)
                fixture.job.ctypes.get_last_error = lambda: 6 if close_failed else original_last_error()
                fixture.job.ctypes.WinError = Mock(side_effect=lambda code: invalid if code == 6 else original_win_error(code))
                with self.assertRaises(RuntimeError) as failure:
                    checks.ProcessTree.spawn(["unused"], 1024)
                self.assertIs(failure.exception.__cause__, invalid)
                self.assertIs(failure.exception.__context__, fixture.startup_error)
                self.assertIsNone(fixture.job.handle)
                self.assertIs(fixture.job.invalid_handle_error, invalid)
                fixture.job.kernel32.CloseHandle.assert_called_once_with(fixture.handle)
                self.assertIn("rollback failed after bounded retries", str(failure.exception))
                if phase == "popen":
                    fixture.process.kill.assert_not_called()
                    fixture.process.wait.assert_not_called()
                else:
                    fixture.process.kill.assert_called_once_with()
                    fixture.process.wait.assert_called_once_with(timeout=5)

    def test_windows_assigned_launcher_reaps_after_job_close_fallback(self):
        fixture = self.startup_rollback_fixture("resume", {"job": None, "kill": None})
        with self.assertRaises(OSError) as failure:
            checks.ProcessTree.spawn(["unused"], 1024)
        self.assertIs(failure.exception, fixture.startup_error)
        self.assertEqual(fixture.events, ["popen", "assign", "resume", "job-terminate", "job-terminate", "kill", "kill", "wait", "wait", "job-close", "wait"])
        self.assertFalse(fixture.running_group)
        self.assertEqual(fixture.process.returncode, -9)
        self.assertIsNone(fixture.job.handle)


class SymbolInventoryProvenance(unittest.TestCase):
    def test_failure_context_keeps_tool_and_object_identity_after_temp_deletion(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary).resolve()
            nm, obj = directory / "selected-nm", directory / "module.o"
            nm.write_bytes(b"fake tool")
            obj.write_bytes(b"tiny object")
            commands = []

            def job(build, command, work, label, timeout, memory, output):
                commands.append((command, timeout, memory, output))
                if command[1] == "--version":
                    return subprocess.CompletedProcess(command, 0, "llvm-nm, compatible with GNU nm\nLLVM version 19.1.7\n", "")
                raise RuntimeError('native symbol inventory exceeded memory limit: observed=134.3MB limit=128MB\nmemory-sample={"processes":[]}')

            with patch.object(benchmark.shutil, "which", return_value=str(nm)), \
                    patch.object(benchmark, "guarded_job", side_effect=job), \
                    self.assertRaises(RuntimeError) as failure:
                benchmark.defined_symbols(None, obj, directory / "diagnostic", 10)
            message = str(failure.exception)
            metadata = json.loads(message.split("symbol-inventory-provenance=", 1)[1])
            self.assertEqual(metadata["object"]["size_bytes"], 11)
            self.assertEqual(metadata["object"]["sha256"], hashlib.sha256(b"tiny object").hexdigest())
            self.assertEqual(metadata["nm_version"], "llvm-nm, compatible with GNU nm\nLLVM version 19.1.7\n")
            self.assertEqual(commands[1][0], [str(nm.resolve()), "-g", "--defined-only", str(obj)])
            self.assertEqual([command[2] for command in commands], [128, 128])
            self.assertEqual(commands[0][1], 5)
            self.assertEqual(commands[1][1], 10)
        self.assertIn(hashlib.sha256(b"tiny object").hexdigest(), message)
        self.assertIn("observed=134.3MB limit=128MB", message)

    def test_failed_version_validation_retains_original_failure_and_stops_inventory(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary).resolve()
            nm = directory / "selected-llvm-nm"
            nm.write_bytes(b"LLVM tool")
            obj = directory / "module.o"
            obj.write_bytes(b"object")
            with patch.object(benchmark.shutil, "which", return_value=str(nm)), \
                    patch.object(benchmark, "guarded_job", side_effect=RuntimeError("original tool version limit")) as job, \
                    self.assertRaises(RuntimeError) as failure:
                benchmark.defined_symbols(None, obj, directory / "diagnostic", 1)
            message = str(failure.exception)
            self.assertIn("original tool version limit", message)
            self.assertIn("unavailable within unchanged resource limits", message)
            job.assert_called_once_with(None, [str(nm.resolve()), "--version"],
                directory / "diagnostic/tool-selection/tool-version", "LLVM symbol tool version", 1, 128, 1)

    def test_success_keeps_collision_symbols_with_validated_llvm_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary).resolve()
            nm, obj = directory / "llvm-nm", directory / "module.o"
            nm.write_bytes(b"LLVM tool")
            obj.write_bytes(b"object")
            version = subprocess.CompletedProcess([], 0, "llvm-nm, compatible with GNU nm\nLLVM version 19.1.7\n", "")
            inventory = subprocess.CompletedProcess([], 0, "00000000 T main\n00000008 T bench_collision\n", "")
            with patch.object(benchmark.shutil, "which", return_value=str(nm)), \
                    patch.object(benchmark, "guarded_job", side_effect=[version, inventory]) as job:
                self.assertEqual(benchmark.defined_symbols(None, obj, directory / "work", 10),
                                 {"main", "bench_collision"})
            self.assertEqual(job.call_count, 2)
            self.assertEqual(job.call_args.args,
                (None, [str(nm.resolve()), "-g", "--defined-only", str(obj)],
                 directory / "work", "native symbol inventory", 10, 128, 8))

    def test_alias_spelling_executes_and_hashes_the_resolved_image(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary).resolve()
            alias = directory / "short-spelling" / "llvm-nm"
            canonical_parent = directory / "canonical-tools"
            canonical_parent.mkdir()
            selected = canonical_parent / alias.name
            tool = directory / "canonical-llvm-nm"
            obj = directory / "module.o"
            tool.write_bytes(b"canonical LLVM executable")
            obj.write_bytes(b"object")
            resolved = tool.resolve()
            original_resolve = Path.resolve

            def resolve(path, *args, **kwargs):
                if path == alias.parent:
                    return canonical_parent
                if path in (alias, selected):
                    return resolved
                return original_resolve(path, *args, **kwargs)

            version = subprocess.CompletedProcess([], 0,
                "llvm-nm, compatible with GNU nm\nLLVM version 19.1.7\n", "")
            inventory = subprocess.CompletedProcess([], 0,
                "00000000 T main\n00000008 T bench_collision\n", "")
            with patch.object(benchmark.shutil, "which", return_value=str(alias)), \
                    patch.object(Path, "resolve", resolve), \
                    patch.object(benchmark, "guarded_job", side_effect=[version, inventory]) as job:
                self.assertEqual(benchmark.defined_symbols(None, obj, directory / "work", 10),
                                 {"main", "bench_collision"})
            self.assertEqual([call.args[1][0] for call in job.call_args_list],
                             [str(selected), str(selected)])
            metadata = json.loads((directory / "work/provenance.json").read_text())
            self.assertEqual(metadata["requested_nm"], str(alias))
            self.assertEqual(metadata["selected_nm"], str(selected))
            self.assertEqual(metadata["resolved_nm"], str(resolved))
            self.assertEqual(metadata["nm_file"]["sha256"],
                             hashlib.sha256(tool.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
