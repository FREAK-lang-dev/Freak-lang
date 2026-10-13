"""HTTP timeout evidence controls; all subprocess fixtures are inert Python."""
from pathlib import Path
import json
import os
import select
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from v3_v35_http import HttpProgress


INERT_GATE = r'''
import os, sys
from pathlib import Path
from types import SimpleNamespace
import v3_v35_http as raw
import v3_v35_http_language as language

kind, root_text, report_text = sys.argv[1:]
root = Path(root_text)
runtime = root / 'runtime'
runtime.mkdir()
for name in ('freak_runtime.c', 'freak_llvm_runtime.c', 'freak_v35_http.inc'):
    (runtime / name).write_text('inert fixture only\n')
vendor = runtime / 'third_party/llhttp'
vendor.mkdir(parents=True)
(vendor / 'freak_amalgamation.inc').write_text('inert parser fixture only\n')
calls = 0

def active(progress):
    global calls
    calls += 1
    if progress is not None:
        progress.stage('inert-corpus', 'ownership-soak', case=128)
    if calls == 2:
        print('ACTIVE_SECOND_MATRIX', flush=True)
        os.read(0, 1)

def raw_run(command, **kwargs):
    return SimpleNamespace(returncode=0, stdout=b'inert version\n', stderr=b'')

def raw_exercise(exe, env, soak, progress=None):
    active(progress)
    return {'inert_fixture': True}

class InertServer:
    def __init__(self, binary, profile, env, progress=None):
        self.progress = progress
        self.cases = 17
    def checkpoint(self, phase, fixture):
        if self.progress is not None:
            self.progress.stage(phase, fixture)
    def stop(self):
        return [0, 0, 0]
    def abort(self):
        pass

def language_run(command, **kwargs):
    if len(command) == 1:
        return SimpleNamespace(returncode=1, stdout='', stderr='HTTP floor: inert control')
    if '--strict-borrow' in command:
        source = Path(command[1])
        generated = Path(str(source) + '.c')
        if source.stem.split('-')[0] in language.NEGATIVE:
            generated.unlink(missing_ok=True)
            return SimpleNamespace(returncode=1, stdout='', stderr='ByteBuffer word argument')
        generated.write_text('inert generated fixture only\n')
    return SimpleNamespace(returncode=0, stdout='', stderr='')

if kind == 'raw':
    raw.run = raw_run
    raw.exercise = raw_exercise
    sys.argv = ['raw', '--clang', sys.executable, '--runtime-root', str(runtime),
                '--optimization', '0', '--optimization', '2', '--adapter', 'c',
                '--report', report_text]
    raw.main()
else:
    std = root / 'std'
    std.mkdir()
    for name in ('json_document.fk', 'http_server.fk'):
        (std / name).write_text('inert facade fixture only\n')
    language.run = language_run
    language.Server = InertServer
    language.consumer_corpus = lambda server, soak: active(server.progress)
    sys.argv = ['language', '--compiler', sys.executable, '--clang', sys.executable,
                '--runtime-root', str(runtime), '--std-root', str(std),
                '--optimization', '0', '--optimization', '2', '--backend', 'c',
                '--report', report_text]
    language.main()
'''


class HttpProgressTests(unittest.TestCase):
    def test_success_retains_original_fields_and_all_completed_matrices(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'report.json'
            report = {'matrices': [], 'pinned_input_sha256': {'fixture': 'sentinel'}}
            with HttpProgress(path, report, 2) as progress:
                for optimization in (0, 2):
                    progress.matrix_started('adapter', 'c', optimization)
                    report['matrices'].append({'adapter': 'c', 'optimization': optimization})
                    progress.matrix_finished()
                report['pinned_inputs_unchanged'] = True
                progress.passed()
            durable = HttpProgress.read(path)
            self.assertEqual(durable['matrices'], report['matrices'])
            self.assertEqual(durable['pinned_input_sha256'], {'fixture': 'sentinel'})
            self.assertEqual(durable['progress']['outcome'], 'passed')

    def test_interruption_retains_completed_matrix_and_original_cause(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'report.json'
            report = {'matrices': []}
            cause = KeyboardInterrupt('original verification interruption')
            with self.assertRaises(KeyboardInterrupt) as caught:
                with HttpProgress(path, report, 2) as progress:
                    report['matrices'].append({'adapter': 'c', 'optimization': 0})
                    progress.matrix_finished()
                    progress.matrix_started('adapter', 'llvm', 2)
                    progress.stage('native-control', 'stale-request')
                    raise cause
            self.assertIs(caught.exception, cause)
            durable = HttpProgress.read(path)
            self.assertEqual(durable['progress']['outcome'], 'failed')
            self.assertEqual(durable['progress']['exception_type'], 'KeyboardInterrupt')
            self.assertEqual(durable['progress']['completed_matrices'], 1)
            self.assertEqual(durable['progress']['active']['fixture'], 'stale-request')

    def test_recording_failure_cannot_replace_original_cause_or_tear_previous_state(self):
        class HostileNoteError(RuntimeError):
            def add_note(self, note):
                raise KeyboardInterrupt('secondary note interruption')

        for kind in (RuntimeError, HostileNoteError):
            with self.subTest(kind=kind.__name__), tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / 'report.json'
                cause = kind('original verification failure')
                recording = None
                try:
                    with self.assertRaises(RuntimeError) as caught:
                        with HttpProgress(path, {'matrices': []}, 1) as progress:
                            progress.stage('native-control', 'wrong-domain')
                            before = path.read_bytes()
                            recording = patch.object(progress, '_write', side_effect=OSError('recording refused'))
                            recording.start()
                            raise cause
                finally:
                    if recording is not None:
                        recording.stop()
                self.assertIs(caught.exception, cause)
                self.assertEqual(path.read_bytes(), before)
                self.assertEqual(HttpProgress.read(path)['progress']['outcome'], 'running')
                self.assertFalse(list(path.parent.glob('.report.json-*')))

    def test_failed_atomic_replace_keeps_last_complete_checkpoint(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'report.json'
            progress = HttpProgress(path, {'matrices': []}, 1)
            progress.__enter__()
            before = path.read_bytes()
            with patch('v3_v35_http.os.replace', side_effect=OSError('recording refused')):
                with self.assertRaises(OSError):
                    progress.stage('matrix-compile', 'raw-harness')
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(HttpProgress.read(path)['progress']['outcome'], 'running')
            self.assertFalse(list(path.parent.glob('.report.json-*')))

    def test_incomplete_matrix_or_pin_check_cannot_pass(self):
        for pins, count in ((False, 1), (True, 0)):
            with self.subTest(pins=pins, count=count), tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / 'report.json'
                report = {'matrices': [{'adapter': 'c'}] * count,
                          'pinned_inputs_unchanged': pins}
                with self.assertRaises(RuntimeError):
                    with HttpProgress(path, report, 1) as progress:
                        progress.passed()
                self.assertEqual(HttpProgress.read(path)['progress']['outcome'], 'failed')

    def test_torn_oversized_and_inconsistent_reports_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'report.json'
            progress = HttpProgress(path, {'matrices': []}, 1)
            progress.__enter__()
            valid = json.loads(path.read_text())
            malformed = [b'{"matrices":', b'x' * (HttpProgress.MAX_REPORT_BYTES + 1)]
            for change in ({'outcome': 'passed'}, {'completed_matrices': 1},
                           {'expected_matrices': 0}, {'sequence': True}, {'schema': True}):
                report = json.loads(json.dumps(valid))
                report['progress'].update(change)
                malformed.append(json.dumps(report).encode())
            for payload in malformed:
                path.write_bytes(payload)
                with self.assertRaises((ValueError, KeyError, TypeError)):
                    HttpProgress.read(path)

    @unittest.skipIf(os.name == 'nt', 'SIGKILL/owned process-group proof runs on POSIX')
    def test_sigkill_during_second_matrix_preserves_both_gate_orchestrators(self):
        for kind, field in (('raw', 'adapter'), ('language', 'backend')):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                path = root / 'report.json'
                process = subprocess.Popen(
                    [sys.executable, '-u', '-c', INERT_GATE, kind, str(root), str(path)],
                    cwd=Path(__file__).parent, stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True,
                    bufsize=0,
                )
                pgid = os.getpgid(process.pid)
                try:
                    self.assertEqual(pgid, process.pid)
                    self.assertTrue(select.select([process.stdout], [], [], 5)[0], 'inert gate did not checkpoint')
                    lines = []
                    while True:
                        line = process.stdout.readline()
                        lines.append(line)
                        if line == b'ACTIVE_SECOND_MATRIX\n':
                            break
                        self.assertTrue(line, (lines, process.poll()))
                        self.assertTrue(select.select([process.stdout], [], [], 5)[0], 'inert gate stalled before matrix 2')
                    os.killpg(pgid, signal.SIGKILL)
                    stdout, stderr = process.communicate(timeout=5)
                    self.assertEqual(process.returncode, -signal.SIGKILL, (stdout, stderr))
                    durable = HttpProgress.read(path)
                    self.assertEqual(len(durable['matrices']), 1)
                    self.assertEqual(durable['matrices'][0][field], 'c')
                    self.assertEqual(durable['matrices'][0]['optimization'], 0)
                    self.assertEqual(durable['progress']['outcome'], 'running')
                    self.assertEqual(durable['progress']['active'], {
                        'phase': 'inert-corpus', field: 'c', 'optimization': 2,
                        'fixture': 'ownership-soak', 'case': 128,
                    })
                    with self.assertRaises(ProcessLookupError):
                        os.killpg(pgid, 0)
                finally:
                    if process.poll() is None:
                        os.killpg(pgid, signal.SIGKILL)
                    process.communicate(timeout=5)


class HttpProgressAtomicCleanup(unittest.TestCase):
    def test_secondary_cleanup_interrupt_keeps_original_error_and_previous_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.json'
            progress = HttpProgress(path, {'matrices': []}, 1)
            progress._write()
            before = path.read_bytes()
            primary = OSError('controlled replace failure')
            secondary = KeyboardInterrupt('controlled cleanup interruption')
            with patch('v3_v35_http.os.replace', side_effect=primary), \
                    patch.object(Path, 'unlink', side_effect=secondary):
                try:
                    progress._write()
                except OSError as caught:
                    self.assertIs(caught, primary)
                else:
                    self.fail('the primary error was lost')
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(primary.__notes__, ['HTTP staged-file cleanup failed: KeyboardInterrupt'])

    def test_hostile_note_attachment_cannot_replace_primary(self):
        class HostileNoteError(OSError):
            def add_note(self, note):
                raise SystemExit('secondary note interruption')

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.json'
            progress = HttpProgress(path, {'matrices': []}, 1)
            primary = HostileNoteError('controlled replace failure')
            with patch('v3_v35_http.os.replace', side_effect=primary), \
                    patch.object(Path, 'unlink', side_effect=KeyboardInterrupt('cleanup')):
                try:
                    progress._write()
                except HostileNoteError as caught:
                    self.assertIs(caught, primary)
                else:
                    self.fail('the primary error was lost')

    def test_cleanup_failure_without_primary_is_propagated(self):
        with tempfile.TemporaryDirectory() as directory:
            progress = HttpProgress(Path(directory) / 'report.json', {'matrices': []}, 1)
            secondary = KeyboardInterrupt('controlled cleanup interruption')
            with patch.object(Path, 'unlink', side_effect=secondary):
                try:
                    progress._write()
                except KeyboardInterrupt as caught:
                    self.assertIs(caught, secondary)
                else:
                    self.fail('cleanup-only failure was swallowed')

    def test_unrelated_ambient_exception_is_not_a_local_write_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            progress = HttpProgress(Path(directory) / 'report.json', {'matrices': []}, 1)
            secondary = OSError('controlled cleanup failure')
            try:
                raise RuntimeError('unrelated outer failure')
            except RuntimeError:
                with patch.object(Path, 'unlink', side_effect=secondary):
                    try:
                        progress._write()
                    except OSError as caught:
                        self.assertIs(caught, secondary)
                    else:
                        self.fail('cleanup-only failure was swallowed under ambient exception')


if __name__ == '__main__':
    unittest.main()
