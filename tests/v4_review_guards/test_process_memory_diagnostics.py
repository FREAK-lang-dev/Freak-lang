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

                def wait():
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
                process.wait.assert_called_once_with()
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

    def cleanup_retry_fixture(self, platform, failure_phase, *, persistent=False):
        process = SimpleNamespace(pid=10, returncode=None, stdout=io.BytesIO(), stderr=io.BytesIO())
        process.poll = lambda: process.returncode
        events = []
        running_group = {10, 11}
        reaped = False
        attempts = {"terminate": 0, "wait": 0}
        handle = object()
        job = None

        if platform == "windows":
            # Exercise the real WindowsJob terminate/close methods through a
            # mocked kernel API; ctypes and a Windows host are unnecessary.
            job = checks.WindowsJob.__new__(checks.WindowsJob)
            job.handle = handle

        def terminate(*args):
            events.append("job-terminate" if job is not None else "killpg")
            if job is not None:
                self.assertEqual(args, (handle, 1))
                self.assertIs(job.handle, handle)
            else:
                self.assertEqual(args, (10, 9))
            attempts["terminate"] += 1
            if failure_phase == "terminate" and (persistent or attempts["terminate"] == 1):
                raise OSError("temporary termination failure")
            running_group.clear()
            return 1

        def wait():
            nonlocal reaped
            events.append("wait")
            if job is not None:
                self.assertIs(job.handle, handle)
            attempts["wait"] += 1
            if failure_phase == "wait" and (persistent or attempts["wait"] == 1):
                raise OSError("temporary reaping failure")
            process.returncode = -9
            reaped = True
            return process.returncode

        def close_handle(actual_handle):
            events.append("job-close")
            self.assertIs(actual_handle, handle)
            self.assertFalse(running_group)
            self.assertTrue(reaped)
            return 1

        if job is not None:
            job.kernel32 = SimpleNamespace(
                TerminateJobObject=Mock(side_effect=terminate),
                CloseHandle=Mock(side_effect=close_handle),
            )
        process.kill = Mock(side_effect=lambda: events.append("kill"))
        process.wait = Mock(side_effect=wait)
        tree = checks.ProcessTree(process, job)
        original_close = tree.close

        def close():
            events.append("close")
            self.assertFalse(running_group)
            self.assertTrue(reaped)
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
                    expected = ["diagnostic", terminate_event]
                    if phase == "wait":
                        expected += ["kill", "wait"]
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

    def test_persistent_cleanup_failure_retains_retryable_handle_and_is_bounded(self):
        for platform in ("posix", "windows"):
            for phase in ("terminate", "wait"):
                with self.subTest(platform=platform, failure=phase):
                    fixture = self.cleanup_retry_fixture(platform, phase, persistent=True)
                    with self.assertRaises(RuntimeError) as failure:
                        checks.run_with_heartbeat(["unused"], label="persistent limit", memory_limit_mb=1)
                    terminate_event = "job-terminate" if platform == "windows" else "killpg"
                    attempt_events = [terminate_event]
                    if phase == "wait":
                        attempt_events += ["kill", "wait"]
                    # Two attempts inside each closure invocation. The outer
                    # exception handler can still retry the same open tree.
                    self.assertEqual(fixture.events, ["diagnostic"] + attempt_events * 4)
                    self.assertEqual(fixture.attempts["terminate"], 4)
                    self.assertEqual(fixture.attempts["wait"], 4 if phase == "wait" else 0)
                    fixture.close.assert_not_called()
                    fixture.capture.assert_called_once_with()
                    self.assertIsNone(fixture.process.returncode)
                    self.assertEqual(bool(fixture.running_group), phase == "terminate")
                    if platform == "windows":
                        fixture.job.kernel32.CloseHandle.assert_not_called()
                        self.assertIs(fixture.job.handle, fixture.handle)
                    self.assertIsInstance(failure.exception.__cause__, OSError)
                    self.assertIn("temporary", str(failure.exception.__cause__))
                    message = str(failure.exception)
                    self.assertIn("persistent limit process-tree cleanup failed after 2 attempts", message)
                    self.assertIn("exceeded memory limit: peak=2.0MB limit=1MB", message)
                    self.assertIn('memory-sample={"diagnostic_error":"capture unavailable"}', message)
                    self.assertNotIn("secret", message)


class SymbolInventoryProvenance(unittest.TestCase):
    def test_failure_context_keeps_tool_and_object_identity_after_temp_deletion(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
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
            self.assertEqual(commands[1][0], [str(nm), "-g", "--defined-only", str(obj)])
            self.assertEqual([command[2] for command in commands], [128, 128])
            self.assertEqual(commands[0][1], 5)
            self.assertEqual(commands[1][1], 10)
        self.assertIn(hashlib.sha256(b"tiny object").hexdigest(), message)
        self.assertIn("observed=134.3MB limit=128MB", message)

    def test_failed_version_validation_retains_original_failure_and_stops_inventory(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
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
            job.assert_called_once_with(None, [str(nm), "--version"],
                directory / "diagnostic/tool-selection/tool-version", "LLVM symbol tool version", 1, 128, 1)

    def test_success_keeps_collision_symbols_with_validated_llvm_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
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
                (None, [str(nm), "-g", "--defined-only", str(obj)],
                 directory / "work", "native symbol inventory", 10, 128, 8))


if __name__ == "__main__":
    unittest.main()
