"""Real stdlib controls for retained acceptance failures and HTTP deadlines."""
from __future__ import annotations

from contextlib import redirect_stdout
import ctypes
import io
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
import threading
import time
import textwrap
import unittest
from unittest.mock import Mock, patch

import v3_v35_acceptance as acceptance
import v3_v35_hangar_lock_preservation as preservation


class AcceptanceHelpers(unittest.TestCase):
    def test_success_keeps_separate_raw_channels_and_exit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            records = []
            result = acceptance.run_command(
                [sys.executable, '-c', 'import sys; print("out"); print("err", file=sys.stderr); sys.exit(7)'],
                cwd=root, env=os.environ.copy(), label='exit', prefix=root / 'exit', records=records, expected=7)
            self.assertEqual(result.stdout, b'out' + os.linesep.encode())
            self.assertEqual(result.stderr, b'err' + os.linesep.encode())
            self.assertEqual((root / 'exit.stdout').read_bytes(), result.stdout)
            self.assertEqual((root / 'exit.stderr').read_bytes(), result.stderr)
            self.assertEqual(records[0]['returncode'], 7)

    def test_timeout_closes_inherited_pipe_descendant_and_keeps_partial_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            records = []
            code = ('import subprocess,sys,time; '
                    'child=subprocess.Popen([sys.executable,"-c","import time; time.sleep(60)"]); '
                    'print("descendant:"+str(child.pid),flush=True); '
                    'print("retained error",file=sys.stderr,flush=True); time.sleep(60)')
            began = time.monotonic()
            with self.assertRaises(subprocess.TimeoutExpired) as caught:
                acceptance.run_command([sys.executable, '-c', code], cwd=root, env=os.environ.copy(),
                                       label='inherited-pipe', prefix=root / 'timeout', records=records, timeout=0.5)
            self.assertLess(time.monotonic() - began, 8)
            self.assertEqual(caught.exception.timeout, 0.5)
            self.assertTrue(records[0]['timed_out'])
            self.assertEqual(records[0]['cleanup_errors'], [])
            self.assertEqual((root / 'timeout.stdout').read_bytes(), caught.exception.output)
            self.assertEqual((root / 'timeout.stderr').read_bytes(), b'retained error' + os.linesep.encode())
            descendant = int(re.search(rb'descendant:(\d+)', caught.exception.output)[1])
            if os.name == 'nt':
                kernel = ctypes.WinDLL('kernel32', use_last_error=True)
                kernel.OpenProcess.restype = ctypes.c_void_p
                kernel.OpenProcess.argtypes = (ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong)
                handle = kernel.OpenProcess(0x1000, False, descendant)
                if handle:
                    kernel.GetExitCodeProcess.argtypes = (ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong))
                    kernel.CloseHandle.argtypes = (ctypes.c_void_p,)
                    status = ctypes.c_ulong()
                    try:
                        self.assertTrue(kernel.GetExitCodeProcess(handle, ctypes.byref(status)))
                        self.assertNotEqual(status.value, 259)
                    finally:
                        kernel.CloseHandle(handle)
                else:
                    self.assertEqual(ctypes.get_last_error(), 87)  # PID no longer exists.
            else:
                status = Path(f'/proc/{descendant}/stat')
                if status.exists():
                    self.assertEqual(status.read_text().rsplit(')', 1)[1].split()[0], 'Z')
                else:
                    observed = subprocess.run(['ps', '-o', 'stat=', '-p', str(descendant)],
                                              capture_output=True, timeout=5)
                    self.assertTrue(not observed.stdout.strip() or observed.stdout.strip().startswith(b'Z'),
                                    observed.stdout)

    def test_secondary_timeout_preserves_original_cause_and_partial_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            primary = subprocess.TimeoutExpired(['inert'], 0.5, output=b'first', stderr=b'error')
            secondary = subprocess.TimeoutExpired(['inert'], 10, output=b'first later', stderr=b'error later')
            child = Mock(pid=42, returncode=-9, stdout=io.BytesIO(), stderr=io.BytesIO())
            child.communicate.side_effect = [primary, secondary]
            child.poll.return_value = -9
            records = []
            with patch.object(acceptance.os, 'killpg', create=True), \
                    patch.object(acceptance.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, b'', b'')), \
                    patch.object(acceptance.subprocess, 'Popen', return_value=child):
                with self.assertRaises(subprocess.TimeoutExpired) as caught:
                    acceptance.run_command(['inert'], cwd=root, env={}, label='recovery',
                                           prefix=root / 'recovery', records=records, timeout=0.5)
            self.assertIs(caught.exception, primary)
            self.assertEqual(primary.output, b'first later')
            self.assertEqual((root / 'recovery.stdout').read_bytes(), b'first later')
            self.assertEqual((root / 'recovery.stderr').read_bytes(), b'error later')
            self.assertEqual(records[0]['cleanup_errors'], ['recovery communicate exceeded 10 seconds'])
            self.assertTrue(records[0]['timed_out'])

    def test_failed_spawn_still_has_raw_files_and_command_record(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            records = []
            with self.assertRaises(FileNotFoundError):
                acceptance.run_command([str(root / 'absent')], cwd=root, env={}, label='spawn',
                                       prefix=root / 'spawn', records=records)
            self.assertEqual(records[0]['returncode'], None)
            self.assertEqual((root / 'spawn.stdout').read_bytes(), b'')
            self.assertEqual((root / 'spawn.stderr').read_bytes(), b'')

    def test_checkpoint_failure_does_not_replace_original_timeout(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            primary = subprocess.TimeoutExpired(['inert'], .5, output=b'first')
            child = Mock(pid=42, returncode=-9)
            child.communicate.side_effect = [primary, (b'retained', b'error')]
            child.poll.return_value = -9
            records = []
            def checkpoint(record):
                if record.get('timed_out'):
                    raise OSError('checkpoint write failed')
            with patch.object(acceptance.os, 'killpg', create=True), \
                    patch.object(acceptance.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, b'', b'')), \
                    patch.object(acceptance.subprocess, 'Popen', return_value=child):
                with self.assertRaises(subprocess.TimeoutExpired) as caught:
                    acceptance.run_command(['inert'], cwd=root, env={}, label='checkpoint',
                                           prefix=root / 'checkpoint', records=records, timeout=.5,
                                           on_record=checkpoint)
            self.assertIs(caught.exception, primary)
            self.assertEqual((root / 'checkpoint.stdout').read_bytes(), b'retained')
            self.assertEqual(records[0]['recording_errors'], ["OSError('checkpoint write failed')"])

    def test_pid_checkpoint_failure_finishes_child_before_raising(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            records = []
            def checkpoint(record):
                if 'pid' in record and 'returncode' not in record:
                    raise OSError('PID checkpoint write failed')
            with self.assertRaisesRegex(OSError, 'PID checkpoint write failed'):
                acceptance.run_command(
                    [sys.executable, '-c', 'import time; time.sleep(.05); print("completed", flush=True)'],
                    cwd=root, env=os.environ.copy(), label='pid-checkpoint',
                    prefix=root / 'pid-checkpoint', records=records, timeout=2, on_record=checkpoint)
            self.assertEqual(records[0]['returncode'], 0)
            self.assertEqual((root / 'pid-checkpoint.stdout').read_bytes(), b'completed' + os.linesep.encode())
            self.assertEqual(records[0]['recording_errors'], ["OSError('PID checkpoint write failed')"])

    def test_hangar_recorder_retains_adverse_exit_and_spawn_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            recorder = preservation.Recorder(root)
            status, output = recorder.run(
                [sys.executable, '-c', 'import sys; print("out"); print("err", file=sys.stderr); sys.exit(7)'],
                root, os.environ.copy(), 'adverse-exit')
            self.assertEqual(status, 7)
            self.assertIn('out', output)
            self.assertIn('err', output)
            self.assertEqual((root / '000-stdout.raw').read_bytes(), b'out' + os.linesep.encode())
            self.assertEqual((root / '000-stderr.raw').read_bytes(), b'err' + os.linesep.encode())
            with self.assertRaises(FileNotFoundError):
                recorder.run([str(root / 'absent')], root, {}, 'failed-spawn')
            checkpoint = json.loads((root / 'command-records.json').read_text())
            self.assertEqual(len(checkpoint['commands']), 2)
            self.assertEqual(checkpoint['commands'][0]['label'], 'adverse-exit')
            self.assertEqual(checkpoint['commands'][0]['exit_code'], 7)
            self.assertIsNone(checkpoint['commands'][1]['exit_code'])
            self.assertEqual((root / '001-stdout.raw').read_bytes(), b'')
            self.assertEqual((root / '001-stderr.raw').read_bytes(), b'')

    def test_hangar_windows_timeout_retains_original_cause_and_partial_channels(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            recorder = preservation.Recorder(root)
            primary = subprocess.TimeoutExpired(['inert'], .5, output=b'first', stderr=b'error')
            secondary = subprocess.TimeoutExpired(['inert'], 10, output=b'first later', stderr=b'error later')
            child = Mock(pid=42, returncode=0, stdout=io.BytesIO(), stderr=io.BytesIO())
            child.communicate.side_effect = [primary, secondary]
            child.poll.return_value = 0
            cleanup = subprocess.CompletedProcess([], 1, b'', b'absent parent')
            with patch.object(acceptance, 'os', SimpleNamespace(name='nt')), \
                    patch.object(acceptance.subprocess, 'Popen', return_value=child), \
                    patch.object(acceptance.subprocess, 'run', return_value=cleanup) as taskkill:
                with self.assertRaises(subprocess.TimeoutExpired) as caught:
                    recorder.run(['inert'], root, {}, 'inherited-pipe', timeout=.5)
            self.assertIs(caught.exception, primary)
            self.assertEqual([call.kwargs['timeout'] for call in child.communicate.call_args_list], [.5, 10])
            self.assertEqual(taskkill.call_args.args[0], ['taskkill', '/PID', '42', '/T', '/F'])
            self.assertEqual((root / '000-stdout.raw').read_bytes(), b'first later')
            self.assertEqual((root / '000-stderr.raw').read_bytes(), b'error later')
            record = json.loads((root / 'command-records.json').read_text())['commands'][0]
            self.assertTrue(record['timed_out'])
            self.assertEqual(record['cleanup_errors'], ['taskkill did not confirm tree termination',
                                                       'recovery communicate exceeded 10 seconds'])
            self.assertEqual(record['stdout']['sha256'], preservation.sha(root / '000-stdout.raw'))

    def test_windows_secondary_recovery_does_not_wait_on_active_pipe_reader(self):
        # Isolate the lock countermodel so a regression cannot hang this suite.
        code = textwrap.dedent('''
            import os, subprocess, tempfile, threading, time
            from pathlib import Path
            from types import SimpleNamespace
            from unittest.mock import Mock, patch
            import v3_v35_acceptance as acceptance
            read_fd, write_fd = os.pipe()
            stream = os.fdopen(read_fd, 'rb')
            entered = threading.Event()
            def read():
                entered.set()
                stream.read()
            reader = threading.Thread(target=read, daemon=True)
            reader.start()
            entered.wait()
            time.sleep(0.1)
            primary = subprocess.TimeoutExpired(['inert'], .5, output=b'first')
            secondary = subprocess.TimeoutExpired(['inert'], 10, output=b'retained')
            child = Mock(pid=42, returncode=0, stdout=stream, stderr=None)
            child.communicate.side_effect = [primary, secondary]
            child.poll.return_value = 0
            records = []
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                with patch.object(acceptance, 'os', SimpleNamespace(name='nt')), \\
                        patch.object(acceptance.subprocess, 'Popen', return_value=child), \\
                        patch.object(acceptance.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, b'', b'absent parent')):
                    try:
                        acceptance.run_command(['inert'], cwd=root, env={}, label='reader', prefix=root/'reader', records=records, timeout=.5)
                    except subprocess.TimeoutExpired as error:
                        assert error is primary and error.output == b'retained'
                    else:
                        raise AssertionError('original timeout was lost')
                assert (root/'reader.stdout').read_bytes() == b'retained'
                assert records[0]['cleanup_errors'] == ['taskkill did not confirm tree termination', 'recovery communicate exceeded 10 seconds']
            os.close(write_fd)
            reader.join(timeout=1)
            assert not reader.is_alive()
            stream.close()
            print('bounded recovery retained original timeout and raw output')
        ''')
        child = subprocess.Popen([sys.executable, '-c', code], cwd=Path(__file__).parent,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            stdout, stderr = child.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            child.kill()
            child.communicate(timeout=3)
            self.fail('secondary recovery blocked on an active buffered pipe reader')
        self.assertEqual(child.returncode, 0, stderr)
        self.assertIn(b'bounded recovery retained original timeout and raw output', stdout)

    def deadline_model(self, absolute: bool) -> float:
        listener = socket.socket()
        listener.bind(('127.0.0.1', 0))
        listener.listen(1)
        port = listener.getsockname()[1]
        errors = []
        def serve():
            try:
                with listener, listener.accept()[0] as peer:
                    began = last = time.monotonic()
                    while True:
                        remaining = (began + 1 if absolute else last + 0.25) - time.monotonic()
                        if remaining <= 0:
                            peer.sendall(b'HTTP/1.1 408 Request Timeout\r\nConnection: close\r\nContent-Length: 0\r\n\r\n')
                            return
                        peer.settimeout(remaining)
                        try:
                            data = peer.recv(1024)
                        except socket.timeout:
                            continue
                        if not data:
                            raise AssertionError('client closed before model deadline')
                        last = time.monotonic()
            except BaseException as error:
                errors.append(error)
        thread = threading.Thread(target=serve)
        thread.start()
        try:
            began = time.monotonic()
            status, _, body, _, termination = acceptance.request(
                port, acceptance.ABSOLUTE_TRICKLE_WIRE, cuts=acceptance.ABSOLUTE_TRICKLE_CUTS,
                delay=acceptance.ABSOLUTE_TRICKLE_DELAY)
            elapsed = time.monotonic() - began
            self.assertEqual((status, body), (408, b''))
            # A framed rejection can reset a connection with unread input.
            self.assertIn(termination, ('eof', 'reset'))
            return elapsed
        finally:
            thread.join(timeout=10)
            self.assertFalse(thread.is_alive())
            self.assertEqual(errors, [])

    def test_actual_absolute_deadline_model_passes(self):
        acceptance.assert_absolute_header_deadline(self.deadline_model(True))

    def test_actual_idle_only_model_is_rejected(self):
        elapsed = self.deadline_model(False)
        self.assertGreaterEqual(elapsed, 3.2)
        with self.assertRaises(AssertionError):
            acceptance.assert_absolute_header_deadline(elapsed)

    def test_default_local_hangar_failure_keeps_receipt_and_raw_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            outer = Path(temporary)
            repo = outer / 'repo'
            repo.mkdir()
            (repo / 'tracked').write_bytes(b'unit source')
            root = outer / 'retained'
            def fresh(prefix):
                root.mkdir()
                return str(root)
            def fail(args, selected, recorder, receipt, private):
                (selected / 'raw.stdout').write_bytes(b'failed command evidence')
                raise RuntimeError('controlled unit failure')
            output = io.StringIO()
            with patch.object(preservation, 'REPO', repo), \
                    patch.object(preservation.tempfile, 'mkdtemp', side_effect=fresh), \
                    patch.object(preservation.subprocess, 'check_output', side_effect=['tracked\n', 'unit-head\n']), \
                    patch.object(preservation, 'execute', side_effect=fail), \
                    patch.object(sys, 'argv', ['gate', '--freak', sys.executable, '--hangar', sys.executable,
                                             '--clang', sys.executable]), redirect_stdout(output):
                with self.assertRaisesRegex(RuntimeError, 'controlled unit failure'):
                    preservation.main()
            receipt = json.loads((root / 'receipt.json').read_text())
            self.assertEqual(receipt['status'], 'FAIL')
            self.assertEqual((root / 'raw.stdout').read_bytes(), b'failed command evidence')
            self.assertIn(str(root / 'receipt.json'), output.getvalue())


if __name__ == '__main__':
    unittest.main(verbosity=2)
