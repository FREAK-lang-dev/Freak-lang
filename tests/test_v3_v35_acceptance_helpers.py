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


def available_idle_input(peer: socket.socket) -> bytes | None:
    """Read queued input before declaring an idle timeout after scheduling delay."""
    peer.settimeout(0)
    try:
        return peer.recv(1024)
    except BlockingIOError:
        return None


class TricklePacer:
    """Keep this comparative model on its first completed send's schedule."""

    def __init__(self, wait, clock):
        self.wait = wait
        self.clock = clock
        self.anchor = None
        self.fragments = 0
        self.observations = []

    def __call__(self, readers, writers, errors, seconds):
        now = self.clock()
        if self.anchor is None:
            self.anchor = now
        self.fragments += 1
        due = self.anchor + self.fragments * seconds
        effective = max(0, min(seconds, due - now))
        row = {'fragment_index': self.fragments,
               'send_completed_seconds': now - self.anchor,
               'scheduled_wait_end_seconds': due - self.anchor,
               'requested_seconds': seconds, 'effective_seconds': effective}
        if len(self.observations) < 64:
            self.observations.append(row)
        try:
            result = self.wait(readers, writers, errors, effective)
        except BaseException as error:
            row['error_type'] = type(error).__name__
            raise
        row['returned_seconds'] = self.clock() - self.anchor
        row['readable'] = bool(result[0])
        return result


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

    def test_raw_write_failure_preserves_timeout_and_attempts_both_channels(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            records, checkpoints, attempts = [], [], []
            write_bytes = Path.write_bytes
            def fail_stdout(path, data):
                attempts.append(path.name)
                if path.name == 'raw-timeout.stdout':
                    raise OSError('stdout evidence unavailable')
                return write_bytes(path, data)
            code = ('import sys,time; print("partial",flush=True); '
                    'print("error",file=sys.stderr,flush=True); time.sleep(60)')
            with patch.object(Path, 'write_bytes', fail_stdout):
                with self.assertRaises(subprocess.TimeoutExpired) as caught:
                    acceptance.run_command([sys.executable, '-c', code], cwd=root,
                                           env=os.environ.copy(), label='raw-timeout',
                                           prefix=root / 'raw-timeout', records=records,
                                           timeout=.5, on_record=lambda record: checkpoints.append(dict(record)))
            self.assertEqual(attempts, ['raw-timeout.stdout', 'raw-timeout.stderr'])
            self.assertEqual(caught.exception.output, b'partial' + os.linesep.encode())
            self.assertEqual((root / 'raw-timeout.stderr').read_bytes(), caught.exception.stderr)
            self.assertTrue(records[0]['timed_out'])
            self.assertIsNotNone(records[0]['returncode'])
            self.assertIn('elapsed_seconds', checkpoints[-1])
            self.assertEqual(records[0]['recording_errors'], ["OSError('stdout evidence unavailable')"])
            self.assertFalse(records[0]['raw_files']['stdout']['written'])
            self.assertTrue(records[0]['raw_files']['stderr']['written'])

    def test_raw_write_failures_after_success_keep_first_error_and_terminal_checkpoint(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            records, checkpoints, attempts = [], [], []
            errors = [OSError('stdout unavailable'), OSError('stderr unavailable')]
            def fail_write(path, data):
                attempts.append(path.name)
                raise errors[len(attempts) - 1]
            with patch.object(Path, 'write_bytes', fail_write):
                with self.assertRaises(OSError) as caught:
                    acceptance.run_command([sys.executable, '-c', 'print("done")'], cwd=root,
                                           env=os.environ.copy(), label='raw-success',
                                           prefix=root / 'raw-success', records=records,
                                           on_record=lambda record: checkpoints.append(dict(record)))
            self.assertIs(caught.exception, errors[0])
            self.assertEqual(attempts, ['raw-success.stdout', 'raw-success.stderr'])
            self.assertEqual(records[0]['returncode'], 0)
            self.assertEqual(checkpoints[-1]['returncode'], 0)
            self.assertEqual(records[0]['recording_errors'], [repr(error) for error in errors])
            self.assertTrue(all(not item['written'] for item in records[0]['raw_files'].values()))

    def test_raw_write_failure_does_not_replace_pid_checkpoint_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            records, attempts = [], []
            primary = OSError('PID checkpoint unavailable')
            def checkpoint(record):
                if 'pid' in record and 'returncode' not in record:
                    raise primary
            def fail_write(path, data):
                attempts.append(path.name)
                raise OSError('raw evidence unavailable')
            with patch.object(Path, 'write_bytes', fail_write):
                with self.assertRaises(OSError) as caught:
                    acceptance.run_command([sys.executable, '-c', 'print("done")'], cwd=root,
                                           env=os.environ.copy(), label='raw-pid',
                                           prefix=root / 'raw-pid', records=records, on_record=checkpoint)
            self.assertIs(caught.exception, primary)
            self.assertEqual(attempts, ['raw-pid.stdout', 'raw-pid.stderr'])
            self.assertEqual(records[0]['returncode'], 0)
            self.assertEqual(records[0]['recording_errors'][0], repr(primary))
            self.assertEqual(len(records[0]['recording_errors']), 3)

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
        observations = []
        def serve():
            try:
                with listener, listener.accept()[0] as peer:
                    began = last = time.monotonic()
                    while True:
                        remaining = (began + 1 if absolute else last + 0.25) - time.monotonic()
                        # A delayed server thread can resume with fragments
                        # already queued. Idle expiry must inspect that queue;
                        # the absolute deadline still expires unconditionally.
                        data = available_idle_input(peer) if remaining <= 0 and not absolute else None
                        if remaining <= 0 and data is None:
                            observations.append({'event': 'expired', 'seconds': time.monotonic() - began,
                                                 'idle_seconds': time.monotonic() - last,
                                                 'queued_bytes': None})
                            peer.sendall(b'HTTP/1.1 408 Request Timeout\r\nConnection: close\r\nContent-Length: 0\r\n\r\n')
                            return
                        if data is None:
                            peer.settimeout(remaining)
                            try:
                                data = peer.recv(1024)
                            except socket.timeout:
                                continue
                        if not data:
                            raise AssertionError('client closed before model deadline')
                        last = time.monotonic()
                        if len(observations) < 64:
                            observations.append({'event': 'read', 'seconds': last - began,
                                                 'bytes': len(data)})
            except BaseException as error:
                errors.append(error)
        thread = threading.Thread(target=serve)
        thread.start()
        try:
            began = time.monotonic()
            # The receiver still uses real absolute/idle clocks. Only this
            # model's sender avoids adding a new relative wait after every
            # delayed send. This cannot compensate for a host pause >0.25s.
            pacer = TricklePacer(acceptance.select.select, time.monotonic)
            with patch.object(acceptance.select, 'select', side_effect=pacer):
                status, _, body, _, termination = acceptance.request(
                    port, acceptance.ABSOLUTE_TRICKLE_WIRE, cuts=acceptance.ABSOLUTE_TRICKLE_CUTS,
                    delay=acceptance.ABSOLUTE_TRICKLE_DELAY)
            elapsed = time.monotonic() - began
            print('HTTP deadline model: ' + json.dumps({'absolute': absolute,
                                                       'elapsed_seconds': elapsed,
                                                       'client_cadence': pacer.observations,
                                                       'server_observations': observations}))
            self.assertEqual((status, body), (408, b''))
            # A framed rejection can reset a connection with unread input.
            self.assertIn(termination, ('eof', 'reset'))
            return elapsed
        finally:
            thread.join(timeout=10)
            self.assertFalse(thread.is_alive())
            self.assertEqual(errors, [])

    def test_trickle_pacer_removes_extra_wait_after_delayed_send(self):
        clock = Mock(side_effect=[10, 10.14, 10.32, 10.32])
        result = ([], [], [])
        wait = Mock(return_value=result)
        peer = object()
        pacer = TricklePacer(wait, clock)
        self.assertIs(pacer([peer], [], [], 0.1), result)
        self.assertIs(pacer([peer], [], [], 0.1), result)
        self.assertEqual(wait.call_args_list[0].args[:3], ([peer], [], []))
        self.assertAlmostEqual(wait.call_args_list[0].args[3], 0.1)
        self.assertEqual(wait.call_args_list[1].args, ([peer], [], [], 0))
        self.assertEqual(len(pacer.observations), 2)
        self.assertAlmostEqual(pacer.observations[1]['scheduled_wait_end_seconds'], 0.2)

    def test_trickle_pacer_returns_early_readability_without_extra_wait(self):
        peer = object()
        result = ([peer], [], [])
        wait = Mock(return_value=result)
        pacer = TricklePacer(wait, Mock(return_value=10))
        self.assertIs(pacer([peer], [], [], 0.1), result)
        wait.assert_called_once()
        self.assertEqual(pacer.observations[0]['returned_seconds'], 0)
        self.assertTrue(pacer.observations[0]['readable'])

    def test_trickle_pacer_preserves_original_wait_error(self):
        primary = OSError('controlled select failure')
        wait = Mock(side_effect=primary)
        clock = Mock(return_value=10)
        pacer = TricklePacer(wait, clock)
        with self.assertRaises(OSError) as caught:
            pacer([object()], [], [], 0.1)
        self.assertIs(caught.exception, primary)
        wait.assert_called_once()
        clock.assert_called_once()
        self.assertEqual(pacer.observations[0]['error_type'], 'OSError')

    def test_trickle_pacer_scheduling_countermodel_preserves_idle_deadline(self):
        # Inert scheduling costs, not a reproduction of Darwin's TCP stack.
        class Transport:
            def __init__(self, absolute, stall):
                self.absolute, self.stall = absolute, stall
                self.now = self.last = 0
                self.expired = self.replied = False
                self.waits = 0
                self.sent, self.delivered = [], []
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def settimeout(self, seconds):
                self_timeout.assertEqual(seconds, 10)
            def setsockopt(self, *args):
                self_timeout.assertEqual(args, (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1))
            def deadline(self):
                return 1 if self.absolute else self.last + 0.25
            def sendall(self, data):
                self.sent.append(data)
                self.now += 0.06
                if self.deadline() <= self.now:
                    self.expired = True
                if not self.expired:
                    self.last = self.now
                    self.delivered.append(data)
            def select(self, readers, writers, errors, seconds):
                self_timeout.assertEqual((readers, writers, errors), ([self], [], []))
                self_timeout.assertTrue(0 <= seconds <= 0.1)
                self.waits += 1
                overhead = self.stall if self.waits == 13 else 0.04
                if self.expired:
                    self.now += overhead
                    return [self], [], []
                returned = self.now + seconds + overhead
                if self.deadline() <= returned:
                    self.now = self.deadline()
                    self.expired = True
                    return [self], [], []
                self.now = returned
                return [], [], []
            def recv(self, limit):
                self_timeout.assertEqual(limit, 65536)
                if self.replied:
                    return b''
                if not self.expired:
                    self.now = self.deadline()
                    self.expired = True
                self.replied = True
                return b'HTTP/1.1 408 Request Timeout\r\nConnection: close\r\nContent-Length: 0\r\n\r\n'
        self_timeout = self
        cuts = acceptance.ABSOLUTE_TRICKLE_CUTS
        wire = acceptance.ABSOLUTE_TRICKLE_WIRE
        pieces = [wire[start:end] for start, end in zip((0, *cuts), (*cuts, len(wire)))]
        for absolute, paced, stall in ((False, False, 0.10), (False, True, 0.10),
                                      (True, False, 0.10), (True, True, 0.10),
                                      (False, True, 0.30)):
            peer = Transport(absolute, stall)
            wait = TricklePacer(peer.select, lambda: peer.now) if paced else peer.select
            with patch.object(acceptance.socket, 'create_connection', return_value=peer), \
                    patch.object(acceptance.select, 'select', side_effect=wait):
                status, _, body, _, termination = acceptance.request(
                    1, wire, cuts=cuts, delay=acceptance.ABSOLUTE_TRICKLE_DELAY)
            self.assertEqual((status, body, termination), (408, b'', 'eof'))
            self.assertEqual(peer.sent, pieces[:len(peer.sent)])
            if absolute:
                acceptance.assert_absolute_header_deadline(peer.now)
            elif paced and stall == 0.10:
                self.assertEqual(peer.delivered, pieces)
                self.assertGreaterEqual(peer.now, 3.2)
                with self.assertRaises(AssertionError):
                    acceptance.assert_absolute_header_deadline(peer.now)
            else:
                # A real gap longer than0.25s still expires; no idle grace.
                self.assertLess(peer.now, 3.2)
                self.assertLess(len(peer.delivered), len(pieces))

    def test_idle_expiry_reads_queued_input_without_waiting(self):
        peer = Mock()
        peer.recv.return_value = b'queued fragments'
        self.assertEqual(available_idle_input(peer), b'queued fragments')
        peer.settimeout.assert_called_once_with(0)
        peer.recv.assert_called_once_with(1024)

    def test_idle_expiry_with_empty_queue_remains_expired(self):
        peer = Mock()
        peer.recv.side_effect = BlockingIOError()
        self.assertIsNone(available_idle_input(peer))
        peer.settimeout.assert_called_once_with(0)
        peer.recv.assert_called_once_with(1024)

    def test_idle_expiry_preserves_eof_and_socket_error(self):
        peer = Mock()
        peer.recv.return_value = b''
        self.assertEqual(available_idle_input(peer), b'')
        primary = ConnectionResetError('peer reset')
        peer.recv.side_effect = primary
        with self.assertRaises(ConnectionResetError) as caught:
            available_idle_input(peer)
        self.assertIs(caught.exception, primary)

    def test_actual_absolute_deadline_model_passes(self):
        acceptance.assert_absolute_header_deadline(self.deadline_model(True))

    def test_actual_idle_only_model_is_rejected(self):
        elapsed = self.deadline_model(False)
        self.assertGreaterEqual(elapsed, 3.2)
        with self.assertRaises(AssertionError):
            acceptance.assert_absolute_header_deadline(elapsed)

    def test_trickle_transport_avoids_delayed_ack_idle_refusal(self):
        # Deterministic transport countermodel, not a Darwin TCP reproduction:
        # an unacknowledged first byte queues later small writes for 0.3s.
        # The idle-only receiver must see every 0.1s fragment before its 0.25s
        # timer expires; TCP_NODELAY removes the queue without changing timing.
        outer = self
        class FragmentTransport:
            def __init__(self):
                self.now = self.last_received = 0.0
                self.nodelay = False
                self.sent = []
                self.options = []
                self.replied = False
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def settimeout(self, seconds):
                outer.assertEqual(seconds, 10)
            def setsockopt(self, level, option, value):
                outer.assertEqual(self.sent, [])
                outer.assertEqual((level, option, value), (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1))
                self.options.append((level, option, value))
                self.nodelay = bool(value)
            def sendall(self, data):
                self.sent.append(data)
                if self.nodelay or len(self.sent) == 1 or self.now >= 0.3:
                    self.last_received = self.now
            def select(self, readers, writers, errors, seconds):
                outer.assertEqual((readers, writers, errors), ([self], [], []))
                outer.assertEqual(seconds, 0.1)
                deadline = self.last_received + 0.25
                if deadline <= self.now + seconds:
                    self.now = deadline
                    return [self], [], []
                self.now += seconds
                return [], [], []
            def recv(self, limit):
                outer.assertEqual(limit, 65536)
                if self.replied:
                    return b''
                self.now = self.last_received + 0.25
                self.replied = True
                return b'HTTP/1.1 408 Request Timeout\r\nConnection: close\r\nContent-Length: 0\r\n\r\n'
        peer = FragmentTransport()
        with patch.object(acceptance.socket, 'create_connection', return_value=peer), \
                patch.object(acceptance.select, 'select', side_effect=peer.select):
            status, _, body, _, termination = acceptance.request(
                1, acceptance.ABSOLUTE_TRICKLE_WIRE, cuts=acceptance.ABSOLUTE_TRICKLE_CUTS,
                delay=acceptance.ABSOLUTE_TRICKLE_DELAY)
        self.assertEqual((status, body, termination), (408, b'', 'eof'))
        self.assertGreaterEqual(peer.now, 3.2)
        self.assertEqual(peer.options, [(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)])
        self.assertEqual(peer.sent, [acceptance.ABSOLUTE_TRICKLE_WIRE[start:end]
                                   for start, end in zip((0, *acceptance.ABSOLUTE_TRICKLE_CUTS),
                                                         (*acceptance.ABSOLUTE_TRICKLE_CUTS, len(acceptance.ABSOLUTE_TRICKLE_WIRE)))])
        with self.assertRaises(AssertionError):
            acceptance.assert_absolute_header_deadline(peer.now)

    def test_request_socket_option_failure_preserves_transport_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            transcript = Path(temporary) / 'option-failure'
            primary = OSError('controlled TCP_NODELAY failure')
            with patch.object(acceptance.socket, 'create_connection') as connect:
                peer = connect.return_value.__enter__.return_value
                peer.setsockopt.side_effect = primary
                with self.assertRaises(OSError) as caught:
                    acceptance.request(1, acceptance.ABSOLUTE_TRICKLE_WIRE,
                                       cuts=acceptance.ABSOLUTE_TRICKLE_CUTS,
                                       delay=acceptance.ABSOLUTE_TRICKLE_DELAY, transcript=transcript)
                self.assertIs(caught.exception, primary)
                peer.sendall.assert_not_called()
                peer.setsockopt.assert_called_once_with(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.assertEqual(transcript.with_suffix('.request').read_bytes(), acceptance.ABSOLUTE_TRICKLE_WIRE)
            self.assertEqual(transcript.with_suffix('.response').read_bytes(), b'')
            self.assertEqual(json.loads(transcript.with_suffix('.transport.json').read_text()),
                             {'termination': 'incomplete', 'response_bytes': 0, 'request_bytes_sent_lower_bound': 0})

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
