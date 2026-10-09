"""Stdlib process controls for bounded run-freshness command evidence."""
from __future__ import annotations

from contextlib import contextmanager
import copy
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import v3_v35_run_freshness as freshness


@contextmanager
def local_subreaper():
    libc = None
    previous = ctypes.c_int()
    if sys.platform.startswith('linux'):
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.prctl(37, ctypes.byref(previous), 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), 'get local subreaper')
        if libc.prctl(36, 1, 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), 'set local subreaper')
    try:
        yield
    finally:
        if libc is not None and libc.prctl(36, previous.value, 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), 'restore local subreaper')


def assert_stopped(pid: int) -> None:
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        try:
            reaped, _ = os.waitpid(pid, os.WNOHANG)
            if reaped == pid:
                return
        except ChildProcessError:
            observed = subprocess.run(['ps', '-o', 'stat=', '-p', str(pid)],
                                      capture_output=True, timeout=1)
            if not observed.stdout.strip() or observed.stdout.strip().startswith(b'Z'):
                return
        time.sleep(0.02)
    raise AssertionError(f'owned descendant {pid} still running')


class RunFreshnessHelpers(unittest.TestCase):
    def setup_recorder(self, root: Path):
        raw = root / 'raw'
        raw.mkdir()
        report = {'status': 'RUNNING', 'commands': [], 'checks': []}
        checkpoints = []
        def save():
            checkpoints.append(copy.deepcopy(report))
            (root / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
        return report, raw, save, checkpoints

    def record(self, root: Path) -> dict:
        report = json.loads((root / 'receipt.json').read_text())
        self.assertEqual(len(report['commands']), 1)
        record = report['commands'][0]
        self.assertIn('started_ns', record)
        self.assertIn('finished_ns', record)
        self.assertIn('environment', record)
        self.assertIn('returncode', record)
        self.assertGreaterEqual(record['finished_ns'], record['started_ns'])
        return record

    def assert_raw(self, record: dict, channel: str, expected: bytes):
        self.assertTrue(record[channel]['written'])
        self.assertEqual(Path(record[channel]['path']).read_bytes(), expected)
        self.assertEqual(record[channel]['bytes'], len(expected))
        self.assertEqual(record[channel]['sha256'], hashlib.sha256(expected).hexdigest())

    def test_adverse_exit_preserves_consumer_fields_raw_and_ansi_return(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report, raw, save, checkpoints = self.setup_recorder(root)
            env = os.environ.copy() | {'FREAK_HOME': 'selected payload', 'FREAK_CLANG': 'selected clang'}
            argv = [sys.executable, '-c', "import sys; print('\x1b[1;31mout\x1b[0m'); print('err',file=sys.stderr); sys.exit(7)"]
            code, output = freshness.run_freshness_command('adverse', argv, root, env,
                                                          report=report, raw=raw, save=save, timeout=3)
            self.assertEqual(code, 7)
            self.assertEqual(output, b'out' + os.linesep.encode() + b'err' + os.linesep.encode())
            record = self.record(root)
            self.assertEqual(record['case'], 'adverse')
            self.assertEqual(record['argv'], argv)
            self.assertEqual(record['cwd'], str(root))
            self.assertEqual(record['environment'], {'FREAK_HOME': 'selected payload', 'FREAK_CLANG': 'selected clang',
                                                    'FREAK_FRESHNESS_EDIT': None, 'FREAK_FRESHNESS_BODY': None})
            self.assert_raw(record, 'stdout', b'\x1b[1;31mout\x1b[0m' + os.linesep.encode())
            self.assert_raw(record, 'stderr', b'err' + os.linesep.encode())
            self.assertEqual(Path(record['stdout']['path']).name, '001-stdout.raw')
            self.assertEqual(Path(record['stderr']['path']).name, '001-stderr.raw')
            self.assertNotIn('pid', checkpoints[0]['commands'][0])
            self.assertTrue(any('pid' in item['commands'][0] and 'returncode' not in item['commands'][0]
                                for item in checkpoints))

    def test_spawn_failure_retains_attempt_and_both_empty_streams(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report, raw, save, _ = self.setup_recorder(root)
            with self.assertRaises(FileNotFoundError):
                freshness.run_freshness_command('missing', [str(root / 'missing')], root, {},
                                                report=report, raw=raw, save=save, timeout=1)
            record = self.record(root)
            self.assertIsNone(record['returncode'])
            self.assertNotIn('pid', record)
            self.assertIn('FileNotFoundError', record['error'])
            self.assert_raw(record, 'stdout', b'')
            self.assert_raw(record, 'stderr', b'')

    def test_native_result_line_endings_preserve_raw_and_exact_values(self):
        for ending in (b'\n', b'\r\n'):
            with self.subTest(ending=ending), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                report, raw, save, _ = self.setup_recorder(root)
                expected = b'BUILD SUCCESSFUL' + ending + b'PKG_RUN=42' + ending + ending + b'OK DONE' + ending
                argv = [sys.executable, '-c', f'import sys; sys.stdout.buffer.write({expected!r})']
                code, output = freshness.run_freshness_command('native-result', argv, root, os.environ.copy(),
                                                              report=report, raw=raw, save=save, timeout=3)
                self.assertEqual(code, 0)
                self.assertEqual(freshness.run_result_values(output), [b'42'])
                self.assert_raw(self.record(root), 'stdout', expected)
        self.assertEqual(freshness.run_result_values(b'PKG_RUN=42\r\nPKG_RUN=42\n'), [b'42', b'42'])
        self.assertEqual(freshness.run_result_values(b'PKG_RUN=420\r\n'), [b'420'])
        for malformed in (b'xPKG_RUN=42\r\n', b'PKG_RUN=42 trailing\r\n',
                          b'PKG_RUN=42\r\r\n', b'PKG_RUN=-42\r\n', b'PKG_RUN=\r\n'):
            with self.subTest(malformed=malformed):
                self.assertEqual(freshness.run_result_values(malformed), [])

    def test_live_timeout_retains_original_exception_partial_channels_and_pid(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report, raw, save, _ = self.setup_recorder(root)
            argv = [sys.executable, '-c', "import sys,time; print('partial-out',flush=True); print('partial-err',file=sys.stderr,flush=True); time.sleep(60)"]
            began = time.monotonic()
            with self.assertRaises(subprocess.TimeoutExpired) as caught:
                freshness.run_freshness_command('live-timeout', argv, root, os.environ.copy(),
                                                report=report, raw=raw, save=save, timeout=0.5)
            self.assertLess(time.monotonic() - began, 8)
            self.assertEqual(caught.exception.cmd, argv)
            self.assertEqual(caught.exception.timeout, 0.5)
            self.assertEqual(caught.exception.output, b'partial-out' + os.linesep.encode())
            self.assertEqual(caught.exception.stderr, b'partial-err' + os.linesep.encode())
            record = self.record(root)
            self.assertTrue(record['timed_out'])
            self.assertGreater(record['pid'], 0)
            self.assertEqual(record['cleanup_errors'], [])
            self.assert_raw(record, 'stdout', caught.exception.output)
            self.assert_raw(record, 'stderr', caught.exception.stderr)

    @unittest.skipIf(os.name == 'nt', 'exited-parent owned-group witness is POSIX; native Windows remains separately pending')
    def test_exited_parent_pipe_retaining_descendant_is_stopped_and_reaped(self):
        self.descendant_timeout_control(parent_waits=False)

    @unittest.skipIf(os.name == 'nt', 'owned-group descendant witness is POSIX; shared Windows tree witness is separate')
    def test_live_parent_pipe_retaining_descendant_is_stopped_and_reaped(self):
        self.descendant_timeout_control(parent_waits=True)

    def descendant_timeout_control(self, *, parent_waits: bool):
        with tempfile.TemporaryDirectory() as temporary, local_subreaper():
            root = Path(temporary)
            report, raw, save, _ = self.setup_recorder(root)
            argv = [sys.executable, '-c', "import subprocess,sys; child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); print('descendant:'+str(child.pid),flush=True); print('held-error',file=sys.stderr,flush=True)"]
            if parent_waits:
                argv[-1] += '; import time; time.sleep(60)'
            descendant = None
            began = time.monotonic()
            try:
                with self.assertRaises(subprocess.TimeoutExpired) as caught:
                    freshness.run_freshness_command('exited-parent', argv, root, os.environ.copy(),
                                                    report=report, raw=raw, save=save, timeout=0.5)
                self.assertLess(time.monotonic() - began, 8)
                self.assertEqual(caught.exception.timeout, 0.5)
                descendant = int(re.search(rb'descendant:(\d+)', caught.exception.output)[1])
                record = self.record(root)
                if parent_waits:
                    self.assertNotEqual(record['returncode'], 0)
                else:
                    self.assertEqual(record['returncode'], 0)
                self.assertEqual(record['cleanup_errors'], [])
                self.assert_raw(record, 'stdout', caught.exception.output)
                self.assert_raw(record, 'stderr', b'held-error\n')
                assert_stopped(descendant)
                descendant = None
            finally:
                if descendant is not None:
                    try:
                        os.killpg(report['commands'][0]['pid'], signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    assert_stopped(descendant)

    def test_pid_checkpoint_failure_finishes_child_and_keeps_raw(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report, raw, actual_save, _ = self.setup_recorder(root)
            failed = False
            def save():
                nonlocal failed
                if report['commands'] and 'pid' in report['commands'][0] and 'returncode' not in report['commands'][0] and not failed:
                    failed = True
                    raise OSError('injected PID checkpoint failure')
                actual_save()
            with self.assertRaisesRegex(OSError, 'injected PID checkpoint failure'):
                freshness.run_freshness_command('pid-checkpoint', [sys.executable, '-c', "import time; time.sleep(.05); print('completed',flush=True)"],
                                                root, os.environ.copy(), report=report, raw=raw, save=save, timeout=3)
            record = self.record(root)
            self.assertEqual(record['returncode'], 0)
            self.assert_raw(record, 'stdout', b'completed' + os.linesep.encode())
            self.assertIn('injected PID checkpoint failure', record['error'])

    def test_raw_source_failure_does_not_replace_timeout_or_lose_other_channel(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report, raw, save, _ = self.setup_recorder(root)
            original_write = Path.write_bytes
            def write(path, data):
                if path == raw / '001.stdout':
                    raise OSError('injected source-channel write failure')
                return original_write(path, data)
            argv = [sys.executable, '-c', "import sys,time; print('retained-out',flush=True); print('retained-err',file=sys.stderr,flush=True); time.sleep(60)"]
            with patch.object(Path, 'write_bytes', new=write):
                with self.assertRaises(subprocess.TimeoutExpired) as caught:
                    freshness.run_freshness_command('source-write-failure', argv, root, os.environ.copy(),
                                                    report=report, raw=raw, save=save, timeout=0.5)
            record = self.record(root)
            self.assertEqual(caught.exception.timeout, 0.5)
            self.assertEqual(caught.exception.output, b'retained-out' + os.linesep.encode())
            self.assertFalse(record['stdout']['written'])
            self.assertEqual(record['stdout']['bytes'], len(caught.exception.output))
            self.assertIn('source-channel write failure', record['stdout']['error'])
            self.assertIn('TimeoutExpired', record['error'])
            self.assert_raw(record, 'stderr', b'retained-err' + os.linesep.encode())

    def test_raw_destination_failure_does_not_replace_spawn_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report, raw, save, _ = self.setup_recorder(root)
            original_write = Path.write_bytes
            def write(path, data):
                if path == raw / '001-stdout.raw':
                    raise OSError('injected destination-channel write failure')
                return original_write(path, data)
            with patch.object(Path, 'write_bytes', new=write):
                with self.assertRaises(FileNotFoundError):
                    freshness.run_freshness_command('destination-write-failure', [str(root / 'missing')], root, {},
                                                    report=report, raw=raw, save=save, timeout=1)
            record = self.record(root)
            self.assertIn('FileNotFoundError', record['error'])
            self.assertFalse(record['stdout']['written'])
            self.assertEqual(record['stdout']['bytes'], 0)
            self.assertIn('destination-channel write failure', record['stdout']['error'])
            self.assert_raw(record, 'stderr', b'')


if __name__ == '__main__':
    unittest.main(verbosity=2)
