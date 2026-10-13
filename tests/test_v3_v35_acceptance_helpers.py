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


def send_model_deadline_response(peer: socket.socket) -> None:
    """Flush the model's rejection before closing with unread trickle input."""
    peer.sendall(b'HTTP/1.1 408 Request Timeout\r\nConnection: close\r\nContent-Length: 0\r\n\r\n')
    peer.shutdown(socket.SHUT_WR)
    # This bounds teardown only. The response and write-side EOF are already
    # sent; neither the absolute/idle deadline nor the client's oracle changes.
    finish = time.monotonic() + 1
    drained = 0
    while True:
        remaining = finish - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('deadline model teardown exceeded one second')
        peer.settimeout(remaining)
        try:
            data = peer.recv(1024)
        except ConnectionResetError:
            return
        if not data:
            return
        drained += len(data)
        assert drained <= len(acceptance.ABSOLUTE_TRICKLE_WIRE), 'unbounded model teardown input'


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


class ComparativeTrickleStall(RuntimeError):
    """A validated comparative receipt cannot distinguish an idle expiry."""

    def __init__(self, cadence, receiver_receipt, stall):
        self.evidence = {'outcome': 'REFUSED', 'scope': 'comparative idle-only helper',
                         'reason': 'trickle gap reached the idle threshold',
                         'idle_threshold_ns': acceptance.ABSOLUTE_TRICKLE_IDLE_NS,
                         'stall': stall, 'client_cadence': cadence,
                         'receiver_receipt': receiver_receipt}
        super().__init__(self.evidence['reason'])


def assert_comparative_idle_trickle(cadence: dict, receiver_receipt: dict, elapsed: float) -> None:
    """Validate the entire receipt before qualifying this idle-only control."""
    assert type(elapsed) in (int, float) and 0 <= elapsed < float('inf'), 'invalid comparative elapsed'
    assert type(cadence) is dict and set(cadence) == {
        'cuts', 'delay_seconds', 'wire_bytes', 'sends', 'first_response_ns'}, 'invalid comparative cadence metadata'
    assert type(cadence['cuts']) is list and all(type(cut) is int for cut in cadence['cuts'])
    assert cadence['cuts'] == list(acceptance.ABSOLUTE_TRICKLE_CUTS)
    assert type(cadence['delay_seconds']) is float and cadence['delay_seconds'] == acceptance.ABSOLUTE_TRICKLE_DELAY
    assert type(cadence['wire_bytes']) is int and cadence['wire_bytes'] == len(acceptance.ABSOLUTE_TRICKLE_WIRE)
    sends = cadence['sends']
    assert type(sends) is list and 0 < len(sends) <= len(acceptance.ABSOLUTE_TRICKLE_CUTS) + 1
    previous = start = 0
    completion_gaps = []
    for index, (row, end) in enumerate(zip(sends, (*acceptance.ABSOLUTE_TRICKLE_CUTS,
                                                 len(acceptance.ABSOLUTE_TRICKLE_WIRE)))):
        assert type(row) is dict and set(row) == {'start_byte', 'end_byte', 'started_ns', 'completed_ns'}
        assert all(type(row[key]) is int for key in row), 'invalid comparative send integer'
        began, completed = row['started_ns'], row['completed_ns']
        assert previous <= began <= completed, 'invalid comparative send timestamp order'
        assert (row['start_byte'], row['end_byte']) == (start, end), 'invalid comparative send byte range'
        completion_gaps.append({'kind': 'send_completion', 'send_index': index,
                                'gap_ns': completed - previous})
        previous, start = completed, end
    response = cadence['first_response_ns']
    assert type(response) is int and response >= previous, 'invalid comparative response timestamp'
    assert response <= round(elapsed * 1_000_000_000), 'invalid comparative elapsed response timestamp'

    assert type(receiver_receipt) is dict and set(receiver_receipt) == {
        'model', 'clock', 'idle_timeout_ns', 'wire_bytes', 'reads', 'expiry'}, 'invalid comparative receiver metadata'
    assert type(receiver_receipt['model']) is str and receiver_receipt['model'] == 'idle-only'
    assert type(receiver_receipt['clock']) is str and receiver_receipt['clock'] == 'receiver-monotonic-relative-ns'
    assert type(receiver_receipt['idle_timeout_ns']) is int
    assert receiver_receipt['idle_timeout_ns'] == acceptance.ABSOLUTE_TRICKLE_IDLE_NS
    assert type(receiver_receipt['wire_bytes']) is int and receiver_receipt['wire_bytes'] == cadence['wire_bytes']
    reads = receiver_receipt['reads']
    assert type(reads) is list and len(reads) <= len(acceptance.ABSOLUTE_TRICKLE_WIRE)
    received = last_received = 0
    for row in reads:
        assert type(row) is dict and set(row) == {'start_byte', 'end_byte', 'received_ns', 'data_hex'}
        assert all(type(row[key]) is int for key in ('start_byte', 'end_byte', 'received_ns'))
        assert row['start_byte'] == received < row['end_byte'] <= start, 'invalid comparative received byte range'
        assert last_received <= row['received_ns'], 'invalid comparative receiver timestamp order'
        assert type(row['data_hex']) is str
        assert row['data_hex'] == acceptance.ABSOLUTE_TRICKLE_WIRE[received:row['end_byte']].hex(), \
            'invalid comparative received bytes'
        received, last_received = row['end_byte'], row['received_ns']
    expiry = receiver_receipt['expiry']
    assert type(expiry) is dict and set(expiry) == {'expired_ns', 'last_received_ns', 'received_bytes'}
    assert all(type(expiry[key]) is int for key in expiry), 'invalid comparative expiry integer'
    assert expiry['expired_ns'] >= last_received, 'invalid comparative expiry timestamp'
    assert expiry['last_received_ns'] == last_received and expiry['received_bytes'] == received
    assert expiry['expired_ns'] - last_received >= acceptance.ABSOLUTE_TRICKLE_IDLE_NS, \
        'invalid comparative idle expiry'
    assert expiry['expired_ns'] <= round(elapsed * 1_000_000_000), 'invalid comparative elapsed expiry timestamp'
    # request() starts its client clock before connecting; the receiver starts
    # after accept and records expiry before sending the response. Its relative
    # expiry must therefore precede the client's relative first response, even
    # when connection setup or response teardown takes extra time.
    assert expiry['expired_ns'] <= response, 'invalid comparative expiry after response'

    # A later malformed row must remain fatal even if an earlier gap stalled.
    for gap in completion_gaps:
        if gap['gap_ns'] >= acceptance.ABSOLUTE_TRICKLE_IDLE_NS:
            raise ComparativeTrickleStall(cadence, receiver_receipt, gap)
    complete = len(sends) == len(acceptance.ABSOLUTE_TRICKLE_CUTS) + 1
    if not complete and response - previous >= acceptance.ABSOLUTE_TRICKLE_IDLE_NS:
        raise ComparativeTrickleStall(cadence, receiver_receipt,
                                     {'kind': 'incomplete_response_wait', 'gap_ns': response - previous})
    # A complete trickle naturally ends with the receiver's 0.25s idle wait.
    assert complete and received == len(acceptance.ABSOLUTE_TRICKLE_WIRE), 'incomplete comparative idle trickle'
    assert elapsed >= 3.2 and response >= 3_200_000_000, ('comparative idle response arrived early', elapsed)


class OwnedCommandCleanupControls(unittest.TestCase):
    """Inert owned-child controls; every fake PID signal is intercepted."""

    def child(self, effects):
        child = Mock(pid=123456789, returncode=None,
                     stdout=io.BytesIO(), stderr=io.BytesIO())
        child.communicate.side_effect = effects
        child.poll.side_effect = lambda: child.returncode
        child.kill.side_effect = lambda: setattr(child, 'returncode', -9)
        child.wait.side_effect = lambda **kwargs: child.returncode
        return child

    def invoke(self, root, child, records, *, checkpoint=None, windows=False):
        from types import SimpleNamespace
        platform = SimpleNamespace(name='nt') if windows else acceptance.os
        cleanup = subprocess.CompletedProcess([], 0, b'tree stopped', b'')
        with patch.object(acceptance, 'os', platform), \
                patch.object(acceptance.subprocess, 'Popen', return_value=child), \
                patch.object(acceptance.subprocess, 'run', return_value=cleanup) as taskkill, \
                patch.object(platform, 'killpg', create=True) as group_kill:
            try:
                acceptance.run_command(['inert'], cwd=root, env={}, label='owned-error',
                                       prefix=root / 'owned-error', records=records,
                                       timeout=120, on_record=checkpoint)
            except BaseException as error:
                return error, taskkill, group_kill
        self.fail('the original command failure was lost')

    def test_communicate_interrupt_and_exception_stop_owned_tree_and_reap(self):
        for windows in (False, True):
            for primary in (KeyboardInterrupt('controlled interruption'),
                            RuntimeError('controlled communicate failure')):
                with self.subTest(windows=windows, cause=type(primary).__name__), \
                        tempfile.TemporaryDirectory() as temporary:
                    root, records = Path(temporary), []
                    child = self.child([primary, (b'partial stdout', b'partial stderr')])
                    error, taskkill, group_kill = self.invoke(root, child, records, windows=windows)
                    self.assertIs(error, primary)
                    self.assertEqual([call.kwargs['timeout'] for call in child.communicate.call_args_list], [120, 10])
                    child.kill.assert_called_once_with()
                    child.wait.assert_called_once_with(timeout=5)
                    self.assertEqual((root / 'owned-error.stdout').read_bytes(), b'partial stdout')
                    self.assertEqual((root / 'owned-error.stderr').read_bytes(), b'partial stderr')
                    self.assertEqual(records[0]['returncode'], -9)
                    self.assertEqual(records[0]['error'], repr(primary))
                    self.assertEqual(records[0]['cleanup_errors'], [])
                    self.assertFalse(records[0]['cleanup_failed'])
                    self.assertNotIn('timed_out', records[0])
                    if windows:
                        taskkill.assert_called_once_with(
                            ['taskkill', '/PID', '123456789', '/T', '/F'],
                            capture_output=True, timeout=10)
                        group_kill.assert_not_called()
                    else:
                        group_kill.assert_called_once_with(child.pid, acceptance.signal.SIGKILL)
                        taskkill.assert_not_called()

    def test_pid_checkpoint_interrupt_cleans_up_before_original_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, records = Path(temporary), []
            primary = KeyboardInterrupt('controlled PID checkpoint interruption')
            child = self.child([(b'checkpoint stdout', b'checkpoint stderr')])
            def checkpoint(record):
                if 'pid' in record and 'returncode' not in record:
                    raise primary
            error, _, group_kill = self.invoke(root, child, records, checkpoint=checkpoint)
            self.assertIs(error, primary)
            child.communicate.assert_called_once_with(timeout=10)
            child.kill.assert_called_once_with()
            child.wait.assert_called_once_with(timeout=5)
            group_kill.assert_called_once()
            self.assertEqual(records[0]['error'], repr(primary))
            self.assertEqual((root / 'owned-error.stdout').read_bytes(), b'checkpoint stdout')
            self.assertEqual((root / 'owned-error.stderr').read_bytes(), b'checkpoint stderr')

    def test_prelaunch_interrupt_never_terminates_an_unowned_pid(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, records = Path(temporary), []
            primary = KeyboardInterrupt('controlled initial checkpoint interruption')
            child = self.child([])
            def checkpoint(record):
                raise primary
            error, taskkill, group_kill = self.invoke(root, child, records, checkpoint=checkpoint)
            self.assertIs(error, primary)
            child.communicate.assert_not_called()
            child.kill.assert_not_called()
            child.wait.assert_not_called()
            taskkill.assert_not_called()
            group_kill.assert_not_called()
            self.assertIsNone(records[0]['returncode'])
            self.assertEqual((root / 'owned-error.stdout').read_bytes(), b'')
            self.assertEqual((root / 'owned-error.stderr').read_bytes(), b'')
            self.assertEqual(records[0]['recording_errors'], [repr(primary)])

    def test_cleanup_failures_keep_original_cause_partial_channels_and_checkpoint(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, records, terminal = Path(temporary), [], []
            primary = RuntimeError('controlled primary failure')
            primary.output, primary.stderr = b'first stdout', b'first stderr'
            recovery = RuntimeError('controlled capture failure')
            recovery.output, recovery.stderr = b'last stdout', b'last stderr'
            child = self.child([primary, recovery])
            child.poll.side_effect = RuntimeError('controlled poll failure')
            child.kill.side_effect = OSError('controlled kill failure')
            child.wait.side_effect = subprocess.TimeoutExpired(['inert'], 5)
            checkpoint_error = KeyboardInterrupt('controlled terminal checkpoint interruption')
            def checkpoint(record):
                if 'returncode' in record:
                    terminal.append(dict(record))
                    raise checkpoint_error
            with patch.object(acceptance.subprocess, 'Popen', return_value=child), \
                    patch.object(acceptance.os, 'killpg', side_effect=OSError('controlled group kill failure')):
                with self.assertRaises(RuntimeError) as caught:
                    acceptance.run_command(['inert'], cwd=root, env={}, label='owned-error',
                                           prefix=root / 'owned-error', records=records,
                                           timeout=120, on_record=checkpoint)
            self.assertIs(caught.exception, primary)
            self.assertEqual((root / 'owned-error.stdout').read_bytes(), b'last stdout')
            self.assertEqual((root / 'owned-error.stderr').read_bytes(), b'last stderr')
            child.kill.assert_called_once_with()
            child.wait.assert_called_once_with(timeout=5)
            self.assertTrue(child.stdout.closed and child.stderr.closed)
            self.assertTrue(records[0]['cleanup_failed'])
            self.assertEqual(records[0]['cleanup_errors'], [
                "OSError('controlled group kill failure')", "RuntimeError('controlled poll failure')",
                "OSError('controlled kill failure')", repr(recovery),
                repr(child.wait.side_effect), 'direct child termination was not confirmed'])
            self.assertEqual(records[0]['error'], repr(primary))
            self.assertEqual(records[0]['recording_errors'], [repr(checkpoint_error)])
            self.assertEqual(terminal[-1]['stdout_sha256'], acceptance.sha(root / 'owned-error.stdout'))
            self.assertEqual(terminal[-1]['stderr_sha256'], acceptance.sha(root / 'owned-error.stderr'))

    def test_windows_capture_failure_defers_reader_close_and_reaps_direct_child(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, records = Path(temporary), []
            primary = KeyboardInterrupt('controlled interruption')
            recovery = subprocess.TimeoutExpired(['inert'], 10, output=b'last stdout', stderr=b'last stderr')
            child = self.child([primary, recovery])
            error, taskkill, _ = self.invoke(root, child, records, windows=True)
            self.assertIs(error, primary)
            taskkill.assert_called_once()
            child.wait.assert_called_once_with(timeout=5)
            self.assertFalse(child.stdout.closed or child.stderr.closed)
            self.assertEqual(records[0]['reader_cleanup'], 'deferred until inherited pipes reach EOF')
            self.assertEqual(records[0]['cleanup_errors'], ['recovery communicate exceeded 10 seconds'])
            self.assertTrue(records[0]['cleanup_failed'])
            self.assertEqual((root / 'owned-error.stdout').read_bytes(), b'last stdout')
            self.assertEqual((root / 'owned-error.stderr').read_bytes(), b'last stderr')

    def test_secondary_cleanup_interruptions_preserve_first_cause_and_channels(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as temporary:
            root, records = Path(temporary), []
            primary = RuntimeError('controlled primary failure')
            primary.output, primary.stderr = b'first stdout', b'first stderr'
            tree_error = KeyboardInterrupt('controlled taskkill interruption')
            capture_error = KeyboardInterrupt('controlled capture interruption')
            child = self.child([primary, capture_error])
            with patch.object(acceptance, 'os', SimpleNamespace(name='nt')), \
                    patch.object(acceptance.subprocess, 'Popen', return_value=child), \
                    patch.object(acceptance.subprocess, 'run', side_effect=tree_error):
                with self.assertRaises(RuntimeError) as caught:
                    acceptance.run_command(['inert'], cwd=root, env={}, label='owned-error',
                                           prefix=root / 'owned-error', records=records, timeout=120)
            self.assertIs(caught.exception, primary)
            child.kill.assert_called_once_with()
            child.wait.assert_called_once_with(timeout=5)
            self.assertEqual(records[0]['cleanup_errors'], [repr(tree_error), repr(capture_error)])
            self.assertTrue(records[0]['cleanup_failed'])
            self.assertEqual(records[0]['error'], repr(primary))
            self.assertEqual((root / 'owned-error.stdout').read_bytes(), b'first stdout')
            self.assertEqual((root / 'owned-error.stderr').read_bytes(), b'first stderr')

    def test_timeout_uses_one_cleanup_and_keeps_original_timeout(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, records = Path(temporary), []
            primary = subprocess.TimeoutExpired(['inert'], 120, output=b'first', stderr=b'first error')
            child = self.child([primary, (b'first later', b'first error later')])
            error, _, group_kill = self.invoke(root, child, records)
            self.assertIs(error, primary)
            self.assertEqual(primary.timeout, 120)
            self.assertEqual((primary.output, primary.stderr), (b'first later', b'first error later'))
            group_kill.assert_called_once_with(child.pid, acceptance.signal.SIGKILL)
            child.kill.assert_called_once_with()
            child.wait.assert_called_once_with(timeout=5)
            self.assertEqual([call.kwargs['timeout'] for call in child.communicate.call_args_list], [120, 10])
            self.assertTrue(records[0]['timed_out'])
            self.assertFalse(records[0]['cleanup_failed'])


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

    def deadline_model(self, absolute: bool, *, observe_cadence: bool = False) -> float:
        listener = socket.socket()
        listener.bind(('127.0.0.1', 0))
        listener.listen(1)
        port = listener.getsockname()[1]
        errors = []
        observations = []
        receiver_receipt = {'model': 'absolute' if absolute else 'idle-only',
                            'clock': 'receiver-monotonic-relative-ns',
                            'idle_timeout_ns': acceptance.ABSOLUTE_TRICKLE_IDLE_NS,
                            'wire_bytes': len(acceptance.ABSOLUTE_TRICKLE_WIRE),
                            'reads': [], 'expiry': None}
        def serve():
            try:
                with listener, listener.accept()[0] as peer:
                    began = last = time.monotonic()
                    received = 0
                    while True:
                        remaining = (began + 1 if absolute else last + 0.25) - time.monotonic()
                        # A delayed server thread can resume with fragments
                        # already queued. Idle expiry must inspect that queue;
                        # the absolute deadline still expires unconditionally.
                        data = available_idle_input(peer) if remaining <= 0 and not absolute else None
                        if remaining <= 0 and data is None:
                            expired = time.monotonic()
                            receiver_receipt['expiry'] = {'expired_ns': round((expired - began) * 1_000_000_000),
                                                          'last_received_ns': round((last - began) * 1_000_000_000),
                                                          'received_bytes': received}
                            observations.append({'event': 'expired', 'seconds': expired - began,
                                                 'idle_seconds': time.monotonic() - last,
                                                 'queued_bytes': None})
                            send_model_deadline_response(peer)
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
                        receiver_receipt['reads'].append({'start_byte': received, 'end_byte': received + len(data),
                                                          'received_ns': round((last - began) * 1_000_000_000),
                                                          'data_hex': data.hex()})
                        received += len(data)
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
            cadence = {} if observe_cadence else None
            with patch.object(acceptance.select, 'select', side_effect=pacer):
                status, _, body, _, termination = acceptance.request(
                    port, acceptance.ABSOLUTE_TRICKLE_WIRE, cuts=acceptance.ABSOLUTE_TRICKLE_CUTS,
                    delay=acceptance.ABSOLUTE_TRICKLE_DELAY, trickle_cadence=cadence)
            elapsed = time.monotonic() - began
            print('HTTP deadline model: ' + json.dumps({'absolute': absolute,
                                                       'elapsed_seconds': elapsed,
                                                       'client_cadence': pacer.observations,
                                                       'observed_cadence': cadence,
                                                       'server_observations': observations,
                                                       'receiver_receipt': receiver_receipt}))
            self.assertEqual((status, body), (408, b''))
            # A framed rejection can reset a connection with unread input.
            self.assertIn(termination, ('eof', 'reset'))
            if observe_cadence:
                self.observed_trickle_cadence = cadence
                self.observed_receiver_receipt = receiver_receipt
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

    def test_deadline_response_half_closes_before_draining_unread_input(self):
        peer = Mock()
        peer.recv.side_effect = [b'queued input', b'']
        with patch.object(time, 'monotonic', side_effect=[10, 10.25, 10.5]):
            send_model_deadline_response(peer)
        self.assertEqual(peer.method_calls[0].args,
                         (b'HTTP/1.1 408 Request Timeout\r\nConnection: close\r\nContent-Length: 0\r\n\r\n',))
        self.assertEqual(peer.method_calls[1].args, (socket.SHUT_WR,))
        self.assertEqual([call[0] for call in peer.method_calls],
                         ['sendall', 'shutdown', 'settimeout', 'recv', 'settimeout', 'recv'])
        self.assertEqual(peer.settimeout.call_args_list[0].args, (0.75,))
        self.assertEqual(peer.settimeout.call_args_list[1].args, (0.5,))

    def test_deadline_response_drain_preserves_its_absolute_cleanup_bound(self):
        peer = Mock()
        peer.recv.return_value = b'x'
        with patch.object(time, 'monotonic', side_effect=[10, 10.5, 11.1]):
            with self.assertRaisesRegex(TimeoutError, 'teardown exceeded one second'):
                send_model_deadline_response(peer)
        peer.recv.assert_called_once_with(1024)

    def test_deadline_response_drain_refuses_excess_input(self):
        peer = Mock()
        peer.recv.return_value = b'x' * (len(acceptance.ABSOLUTE_TRICKLE_WIRE) + 1)
        with self.assertRaisesRegex(AssertionError, 'unbounded model teardown input'):
            send_model_deadline_response(peer)

    def test_deadline_response_keeps_send_failure_fatal(self):
        peer = Mock()
        primary = OSError('controlled model response failure')
        peer.sendall.side_effect = primary
        with self.assertRaises(OSError) as caught:
            send_model_deadline_response(peer)
        self.assertIs(caught.exception, primary)
        peer.shutdown.assert_not_called()
        peer.recv.assert_not_called()

    def test_deadline_response_accepts_peer_reset_after_half_close(self):
        peer = Mock()
        peer.recv.side_effect = ConnectionResetError('peer finished')
        send_model_deadline_response(peer)
        peer.shutdown.assert_called_once_with(socket.SHUT_WR)

    def test_actual_idle_only_model_is_rejected(self):
        elapsed = self.deadline_model(False, observe_cadence=True)
        try:
            assert_comparative_idle_trickle(self.observed_trickle_cadence, self.observed_receiver_receipt, elapsed)
        except ComparativeTrickleStall as refusal:
            print('HTTP comparative idle control: ' + json.dumps(refusal.evidence))
            return
        self.assertGreaterEqual(elapsed, 3.2)
        with self.assertRaises(AssertionError):
            acceptance.assert_absolute_header_deadline(elapsed)

    def comparative_idle_evidence(self, *, count=33, response_gap=250_000_000,
                                 completion_gap=100_000_000, blocked_send=False):
        wire = acceptance.ABSOLUTE_TRICKLE_WIRE
        sends, reads = [], []
        previous = start = 0
        # A receiver clock started later can expire before a sub-250ms client
        # response wait. Keep those controls valid across the ordered origins.
        receiver_offset = max(0, 250_000_000 - response_gap)
        for index, end in enumerate((*acceptance.ABSOLUTE_TRICKLE_CUTS, len(wire))[:count]):
            completed = 0 if index == 0 else previous + (completion_gap if index == 8 else 100_000_000)
            sends.append({'start_byte': start, 'end_byte': end,
                          'started_ns': previous if blocked_send and index == 8 else completed,
                          'completed_ns': completed})
            reads.append({'start_byte': start, 'end_byte': end, 'received_ns': max(0, completed - receiver_offset),
                          'data_hex': wire[start:end].hex()})
            previous, start = completed, end
        cadence = {'cuts': list(acceptance.ABSOLUTE_TRICKLE_CUTS),
                   'delay_seconds': acceptance.ABSOLUTE_TRICKLE_DELAY, 'wire_bytes': len(wire),
                   'sends': sends, 'first_response_ns': previous + response_gap}
        receipt = {'model': 'idle-only', 'clock': 'receiver-monotonic-relative-ns',
                   'idle_timeout_ns': acceptance.ABSOLUTE_TRICKLE_IDLE_NS, 'wire_bytes': len(wire),
                   'reads': reads, 'expiry': {'expired_ns': reads[-1]['received_ns'] + 250_000_000,
                                             'last_received_ns': reads[-1]['received_ns'], 'received_bytes': start}}
        return cadence, receipt, (previous + max(response_gap, 250_000_000)) / 1_000_000_000

    def test_comparative_idle_complete_cadence_admits_terminal_idle_wait(self):
        for response_gap in (250_000_000, 300_000_000):
            with self.subTest(response_gap=response_gap):
                cadence, receipt, elapsed = self.comparative_idle_evidence(response_gap=response_gap)
                assert_comparative_idle_trickle(cadence, receipt, elapsed)
                self.assertEqual(len(cadence['sends']), 33)
                self.assertEqual(receipt['expiry']['received_bytes'], len(acceptance.ABSOLUTE_TRICKLE_WIRE))
                self.assertGreaterEqual(elapsed, 3.2)
                with self.assertRaises(AssertionError):
                    acceptance.assert_absolute_header_deadline(elapsed)
                with self.assertRaisesRegex(AssertionError, 'stalled trickle response wait'):
                    acceptance.assert_absolute_trickle_cadence(cadence)

    def test_comparative_idle_partial_249ms_response_remains_fatal(self):
        for response_gap in (249_000_000, 249_999_999):
            with self.subTest(response_gap=response_gap):
                cadence, receipt, elapsed = self.comparative_idle_evidence(count=9, response_gap=response_gap)
                with self.assertRaisesRegex(AssertionError, 'incomplete comparative idle trickle'):
                    assert_comparative_idle_trickle(cadence, receipt, elapsed)

    def test_comparative_idle_partial_250ms_or_300ms_response_is_refused(self):
        for count, response_gap in ((9, 250_000_000), (9, 300_000_000), (32, 250_000_000)):
            with self.subTest(count=count, response_gap=response_gap):
                cadence, receipt, elapsed = self.comparative_idle_evidence(count=count, response_gap=response_gap)
                with self.assertRaises(ComparativeTrickleStall) as caught:
                    assert_comparative_idle_trickle(cadence, receipt, elapsed)
                evidence = caught.exception.evidence
                self.assertEqual(evidence['outcome'], 'REFUSED')
                self.assertEqual(evidence['scope'], 'comparative idle-only helper')
                self.assertEqual(evidence['stall'], {'kind': 'incomplete_response_wait', 'gap_ns': response_gap})
                self.assertIs(evidence['client_cadence'], cadence)
                self.assertIs(evidence['receiver_receipt'], receipt)

    def test_comparative_idle_completion_stall_and_blocked_send_are_refused(self):
        for gap, blocked in ((250_000_000, False), (300_000_000, False), (300_000_000, True)):
            with self.subTest(gap=gap, blocked=blocked):
                cadence, receipt, elapsed = self.comparative_idle_evidence(
                    count=9, response_gap=100_000_000, completion_gap=gap, blocked_send=blocked)
                with self.assertRaises(ComparativeTrickleStall) as caught:
                    assert_comparative_idle_trickle(cadence, receipt, elapsed)
                self.assertEqual(caught.exception.evidence['stall'],
                                 {'kind': 'send_completion', 'send_index': 8, 'gap_ns': gap})
        # A first blocked send can expire before the receiver observes bytes.
        cadence, receipt, elapsed = self.comparative_idle_evidence(count=1, response_gap=100_000_000)
        cadence['sends'][0]['completed_ns'] = 300_000_000
        cadence['first_response_ns'] = 400_000_000
        receipt['reads'] = []
        receipt['expiry'] = {'expired_ns': 250_000_000, 'last_received_ns': 0, 'received_bytes': 0}
        with self.assertRaises(ComparativeTrickleStall) as caught:
            assert_comparative_idle_trickle(cadence, receipt, 0.4)
        self.assertEqual(caught.exception.evidence['stall'],
                         {'kind': 'send_completion', 'send_index': 0, 'gap_ns': 300_000_000})

    def test_comparative_idle_early_stall_cannot_hide_later_malformed_receipt(self):
        mutations = (
            lambda cadence, receipt: cadence['cuts'].__setitem__(0, True),
            lambda cadence, receipt: cadence.__setitem__('delay_seconds', '0.1'),
            lambda cadence, receipt: cadence.__setitem__('wire_bytes', float(cadence['wire_bytes'])),
            lambda cadence, receipt: cadence['sends'][-1].__setitem__('start_byte', True),
            lambda cadence, receipt: cadence['sends'][-1].__setitem__('end_byte', 999),
            lambda cadence, receipt: cadence['sends'][-1].__setitem__('started_ns', -1),
            lambda cadence, receipt: cadence['sends'][-1].__setitem__('completed_ns', float('nan')),
            lambda cadence, receipt: cadence['sends'][-1].__setitem__('extra', 0),
            lambda cadence, receipt: cadence.__setitem__('first_response_ns', None),
            lambda cadence, receipt: receipt.__setitem__('model', 'absolute'),
            lambda cadence, receipt: receipt.__setitem__('clock', 'client-monotonic-relative-ns'),
            lambda cadence, receipt: receipt.__setitem__('idle_timeout_ns', 300_000_000),
            lambda cadence, receipt: receipt.__setitem__('wire_bytes', 1),
            lambda cadence, receipt: receipt['reads'][-1].__setitem__('end_byte', 999),
            lambda cadence, receipt: receipt['reads'][-1].__setitem__('received_ns', False),
            lambda cadence, receipt: receipt['reads'][-1].__setitem__('data_hex', '00'),
            lambda cadence, receipt: receipt['reads'][-1].__setitem__('extra', 0),
            lambda cadence, receipt: receipt['expiry'].__setitem__('expired_ns', float('inf')),
            lambda cadence, receipt: receipt['expiry'].__setitem__('last_received_ns', 0),
            lambda cadence, receipt: receipt['expiry'].__setitem__('received_bytes', 999),
            lambda cadence, receipt: receipt['expiry'].__setitem__('expired_ns', receipt['expiry']['last_received_ns']),
            lambda cadence, receipt: receipt['expiry'].__setitem__('expired_ns', cadence['first_response_ns'] + 1),
        )
        for index, mutate in enumerate(mutations):
            with self.subTest(mutation=index):
                cadence, receipt, elapsed = self.comparative_idle_evidence(count=10, completion_gap=300_000_000)
                mutate(cadence, receipt)
                with self.assertRaises(AssertionError):
                    assert_comparative_idle_trickle(cadence, receipt, elapsed)

    def test_comparative_idle_expiry_must_precede_response_even_with_long_teardown(self):
        for count, gap in ((33, 100_000_000), (9, 100_000_000), (9, 300_000_000)):
            with self.subTest(count=count, completion_gap=gap):
                cadence, receipt, elapsed = self.comparative_idle_evidence(count=count, completion_gap=gap)
                self.assertEqual(receipt['expiry']['expired_ns'], cadence['first_response_ns'])
                if count == 33:
                    assert_comparative_idle_trickle(cadence, receipt, elapsed)
                else:
                    with self.assertRaises(ComparativeTrickleStall):
                        assert_comparative_idle_trickle(cadence, receipt, elapsed)
                # Additional elapsed teardown time cannot legitimize an expiry
                # one nanosecond after the response it supposedly caused.
                receipt['expiry']['expired_ns'] += 1
                with self.assertRaisesRegex(AssertionError, 'expiry after response'):
                    assert_comparative_idle_trickle(cadence, receipt, elapsed + 1)

    def test_comparative_idle_valid_cadence_with_early_response_remains_fatal(self):
        cadence, receipt, elapsed = self.comparative_idle_evidence(count=9, response_gap=100_000_000)
        acceptance.assert_absolute_header_deadline(elapsed)
        acceptance.assert_absolute_trickle_cadence(cadence)
        with self.assertRaisesRegex(AssertionError, 'incomplete comparative idle trickle'):
            assert_comparative_idle_trickle(cadence, receipt, elapsed)
        cadence, receipt, elapsed = self.comparative_idle_evidence(response_gap=100_000_000)
        for row in cadence['sends']:
            row['started_ns'] //= 4
            row['completed_ns'] //= 4
        for row in receipt['reads']:
            row['received_ns'] //= 4
        receipt['expiry']['last_received_ns'] //= 4
        receipt['expiry']['expired_ns'] = receipt['expiry']['last_received_ns'] + 250_000_000
        cadence['first_response_ns'] = 1_050_000_000
        for elapsed in (1.05, 3.45):
            with self.subTest(elapsed=elapsed), self.assertRaisesRegex(AssertionError, 'comparative idle response arrived early'):
                assert_comparative_idle_trickle(cadence, receipt, elapsed)

    def test_comparative_idle_live_refusal_emits_structured_evidence_and_keeps_malformed_fatal(self):
        cadence, receipt, elapsed = self.comparative_idle_evidence(count=9, response_gap=300_000_000)
        self.observed_trickle_cadence, self.observed_receiver_receipt = cadence, receipt
        output = io.StringIO()
        with patch.object(self, 'deadline_model', return_value=elapsed), \
                patch.object(acceptance, 'assert_absolute_header_deadline') as oracle, redirect_stdout(output):
            self.test_actual_idle_only_model_is_rejected()
        oracle.assert_not_called()
        evidence = json.loads(output.getvalue().removeprefix('HTTP comparative idle control: '))
        self.assertEqual(evidence['outcome'], 'REFUSED')
        self.assertEqual(evidence['client_cadence'], cadence)
        self.assertEqual(evidence['receiver_receipt'], receipt)
        receipt['reads'][-1]['received_ns'] = None
        output = io.StringIO()
        with patch.object(self, 'deadline_model', return_value=elapsed), redirect_stdout(output):
            with self.assertRaises(AssertionError):
                self.test_actual_idle_only_model_is_rejected()
        self.assertEqual(output.getvalue(), '')

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

    def test_observed_trickle_rejects_idle_stall_inside_absolute_window(self):
        outer = self
        class Transport:
            def __init__(self, stall, stall_kind):
                self.now = 0.0
                self.stall = stall
                self.stall_kind = stall_kind
                self.sends = 0
                self.waits = 0
                self.replied = False
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def settimeout(self, seconds):
                outer.assertEqual(seconds, 10)
            def setsockopt(self, *args):
                outer.assertEqual(args, (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1))
            def sendall(self, data):
                self.sends += 1
                if self.sends == 9 and self.stall_kind == 'send':
                    self.now += self.stall
            def select(self, readers, writers, errors, seconds):
                outer.assertEqual((readers, writers, errors, seconds), ([self], [], [], 0.1))
                self.waits += 1
                self.now += self.stall if self.waits == 9 and self.stall_kind == 'wait' else seconds
                return ([self], [], []) if self.waits == 9 else ([], [], [])
            def recv(self, limit):
                outer.assertEqual(limit, 65536)
                if self.replied:
                    return b''
                self.replied = True
                return b'HTTP/1.1 408 Request Timeout\r\nConnection: close\r\nContent-Length: 0\r\n\r\n'
        for stall_kind, stall in (('wait', 0.1), ('wait', 0.249), ('wait', 0.25),
                                  ('wait', 0.30), ('send', 0.30)):
            with self.subTest(stall=stall, stall_kind=stall_kind), tempfile.TemporaryDirectory() as temporary:
                peer = Transport(stall, stall_kind)
                cadence = {}
                transcript = Path(temporary) / 'stall'
                with patch.object(acceptance.socket, 'create_connection', return_value=peer), \
                        patch.object(acceptance.select, 'select', side_effect=peer.select), \
                        patch.object(acceptance.time, 'monotonic_ns', side_effect=lambda: round(peer.now * 1_000_000_000)):
                    status, _, body, _, termination = acceptance.request(
                        1, acceptance.ABSOLUTE_TRICKLE_WIRE, cuts=acceptance.ABSOLUTE_TRICKLE_CUTS,
                        delay=acceptance.ABSOLUTE_TRICKLE_DELAY, trickle_cadence=cadence,
                        transcript=transcript)
                self.assertEqual((status, body, termination), (408, b'', 'eof'))
                # An idle-only refusal following a 0.30s sender stall used to
                # satisfy this unchanged elapsed oracle at about 1.10 seconds.
                acceptance.assert_absolute_header_deadline(peer.now)
                retained = json.loads(transcript.with_suffix('.transport.json').read_text())
                self.assertEqual(retained['trickle_cadence'], cadence)
                self.assertEqual(len(cadence['sends']), 9)
                if stall < 0.25:
                    acceptance.assert_absolute_trickle_cadence(cadence)
                else:
                    with self.assertRaisesRegex(AssertionError, 'stalled trickle'):
                        acceptance.assert_absolute_trickle_cadence(cadence)

    def test_observed_absolute_trickle_admits_or_refuses_real_transport(self):
        acceptance.assert_absolute_header_deadline(self.deadline_model(True, observe_cadence=True))
        cadence = self.observed_trickle_cadence
        completed = [0, *(row['completed_ns'] for row in cadence['sends']), cadence['first_response_ns']]
        largest_gap = max(end - start for start, end in zip(completed, completed[1:]))
        if largest_gap < 250_000_000:
            acceptance.assert_absolute_trickle_cadence(cadence)
        else:
            # A paused real host is valid evidence that this control must be
            # refused; it supplies no deadline PASS for the native service.
            with self.assertRaisesRegex(AssertionError, 'stalled trickle'):
                acceptance.assert_absolute_trickle_cadence(cadence)

    def test_observed_trickle_rejects_blocked_send_and_invalid_evidence(self):
        cadence = {'cuts': list(acceptance.ABSOLUTE_TRICKLE_CUTS),
                   'delay_seconds': acceptance.ABSOLUTE_TRICKLE_DELAY,
                   'wire_bytes': len(acceptance.ABSOLUTE_TRICKLE_WIRE),
                   'sends': [{'start_byte': 0, 'end_byte': 1,
                              'started_ns': 0, 'completed_ns': 100_000_000}],
                   'first_response_ns': 200_000_000}
        acceptance.assert_absolute_trickle_cadence(cadence)
        for started, completed, response in ((0, 300_000_000, 400_000_000), (200_000_000, 100_000_000, 200_000_000),
                                              (0, float('nan'), 200_000_000), (0, 100_000_000, None),
                                              (0, 100_000_000, float('inf'))):
            with self.subTest(started=started, completed=completed, response=response):
                changed = {**cadence, 'sends': [{**cadence['sends'][0], 'started_ns': started,
                                              'completed_ns': completed}],
                           'first_response_ns': response}
                with self.assertRaises(AssertionError):
                    acceptance.assert_absolute_trickle_cadence(changed)

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
