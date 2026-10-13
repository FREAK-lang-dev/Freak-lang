"""Template evidence controls; subprocess fixtures run inert Python only."""
from pathlib import Path
import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from v3_v35_templates import TemplateProgress, cleanup_owned_child, run


CREATORS = [{'backend': backend, 'optimization': opt}
            for backend in ('c', 'llvm') for opt in (0, 2, 3)]
INSTALLED = [{'template': kind, 'backend': backend}
             for kind in ('cli', 'lib', 'http') for backend in ('c', 'llvm')]


def finish(progress, *, installed=True):
    for item in CREATORS:
        progress.matrix_started('creator', item['backend'], item['optimization'])
        progress.report['creator_matrices'].append(dict(item, corpus={'inert': True}))
        progress.matrix_finished()
    if installed:
        for item in INSTALLED:
            progress.matrix_started('installed-cli', item['backend'], fixture=item['template'])
            progress.report['installed_cli_matrices'].append(dict(item, build_run_test=True, failing_test_control=True))
            progress.matrix_finished()
        progress.report['installed_cli_verified'] = True
    progress.report['pinned_inputs_unchanged'] = True
    progress.passed()


INERT_GATE = r'''
from pathlib import Path
from types import SimpleNamespace
import sys
import v3_v35_templates as gate
root, report = map(Path, sys.argv[1:])
runtime = root / 'runtime'
runtime.mkdir()
(runtime / 'freak_runtime.c').write_text('inert runtime only\n')
canonical = root / 'templates'
canonical.mkdir()
calls = 0

def inert_run(command, **kwargs):
    return SimpleNamespace(returncode=0, stdout='inert version\n', stderr='')

def corpus(binary, canonical, scratch, env, progress=None):
    global calls
    calls += 1
    progress.stage('inert-creator-corpus', 'publication-race')
    if calls == 2:
        print('ACTIVE_SECOND_MATRIX', flush=True)
        sys.stdin.buffer.read(1)
    return {'inert_fixture': True}

gate.run = inert_run
gate.creator_corpus = corpus
sys.argv = ['templates', '--compiler', sys.executable, '--clang', sys.executable,
            '--runtime-root', str(runtime), '--templates-root', str(canonical),
            '--backend', 'c', '--optimization', '0', '--optimization', '2',
            '--report', str(report)]
gate.main()
'''


class TemplateProgressTests(unittest.TestCase):
    def test_success_preserves_legacy_fields_and_parent_matrix_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.json'
            report = {'pinned_input_sha256': {'fixture': 'sentinel'}, 'strict_borrow': True}
            with TemplateProgress(path, report, CREATORS, INSTALLED) as progress:
                finish(progress)
            durable = TemplateProgress.read(path)
            self.assertEqual(durable['pinned_input_sha256'], {'fixture': 'sentinel'})
            self.assertTrue(durable['strict_borrow'])
            self.assertEqual(durable['progress']['outcome'], 'passed')
            self.assertEqual(durable['progress']['completed_matrices'], 12)
            self.assertEqual(len(durable['creator_matrices']), 6)
            self.assertEqual(len(durable['installed_cli_matrices']), 6)
            self.assertEqual([item['kind'] for item in durable['matrices']], ['creator'] * 6 + ['installed-cli'] * 6)

    def test_selected_options_and_optional_cli_preserve_original_semantics(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.json'
            selected = [{'backend': 'llvm', 'optimization': 2}]
            with TemplateProgress(path, {}, selected, []) as progress:
                progress.report['creator_matrices'].append(dict(selected[0], corpus={'inert': True}))
                progress.matrix_finished()
                progress.report['pinned_inputs_unchanged'] = True
                progress.passed()
            durable = TemplateProgress.read(path)
            self.assertFalse(durable['installed_cli_verified'])
            self.assertEqual(durable['progress']['completed_matrices'], 1)

    def test_interruption_retains_completed_matrices_and_active_fixture(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.json'
            primary = KeyboardInterrupt('original verification interruption')
            with self.assertRaises(KeyboardInterrupt) as caught:
                with TemplateProgress(path, {}, CREATORS, INSTALLED) as progress:
                    progress.report['creator_matrices'].append(CREATORS[0])
                    progress.matrix_finished()
                    progress.matrix_started('creator', 'c', 2)
                    progress.stage('creator-run', 'malformed-invalid-utf8')
                    raise primary
            self.assertIs(caught.exception, primary)
            durable = TemplateProgress.read(path)
            self.assertEqual(durable['progress']['outcome'], 'failed')
            self.assertEqual(durable['progress']['exception_type'], 'KeyboardInterrupt')
            self.assertEqual(durable['progress']['completed_matrices'], 1)
            self.assertEqual(durable['progress']['active'], {
                'phase': 'creator-run', 'matrix': 'creator', 'backend': 'c',
                'optimization': 2, 'fixture': 'malformed-invalid-utf8'})

    def test_failed_recording_preserves_original_even_with_hostile_notes(self):
        class HostileNoteError(RuntimeError):
            def add_note(self, note):
                raise SystemExit('secondary note failure')

        for exception in (RuntimeError, HostileNoteError):
            with self.subTest(exception=exception.__name__), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'report.json'
                primary = exception('original verification cause')
                with self.assertRaises(exception) as caught:
                    with TemplateProgress(path, {}, CREATORS, []) as progress:
                        progress.stage('creator-run', 'sentinel-no-clobber')
                        before = path.read_bytes()
                        with patch.object(progress, '_write', side_effect=KeyboardInterrupt('secondary recording failure')):
                            # Exercise __exit__ while checkpoint storage is unavailable.
                            progress.__exit__(type(primary), primary, None)
                            raise primary
                self.assertIs(caught.exception, primary)
                durable = TemplateProgress.read(path)
                self.assertEqual(durable['progress']['outcome'], 'failed')
                self.assertNotEqual(path.read_bytes(), before)

    def test_atomic_replace_failure_keeps_complete_previous_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.json'
            with self.assertRaises(OSError):
                with TemplateProgress(path, {}, CREATORS, []) as progress:
                    before = path.read_bytes()
                    with patch('v3_v35_templates.os.replace', side_effect=OSError('replace denied')):
                        progress.stage('creator-run', 'no-clobber')
            self.assertEqual(TemplateProgress.read(path)['progress']['outcome'], 'failed')
            self.assertFalse(list(path.parent.glob('.report.json-*')))
            self.assertEqual(json.loads(before)['progress']['outcome'], 'running')

    def test_local_atomic_cleanup_failure_cannot_replace_primary(self):
        class HostileNoteError(OSError):
            def add_note(self, note):
                raise KeyboardInterrupt('secondary note interruption')

        for exception in (OSError, HostileNoteError):
            with self.subTest(exception=exception.__name__), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'report.json'
                progress = TemplateProgress(path, {}, CREATORS, [])
                path.parent.mkdir(parents=True, exist_ok=True)
                progress._write()
                before = path.read_bytes()
                primary = exception('controlled replace refusal')
                with patch('v3_v35_templates.os.replace', side_effect=primary), \
                        patch.object(Path, 'unlink', side_effect=SystemExit('cleanup refusal')):
                    with self.assertRaises(exception) as caught:
                        progress._write()
                self.assertIs(caught.exception, primary)
                self.assertEqual(path.read_bytes(), before)

    def test_cleanup_failure_without_local_primary_propagates_under_ambient_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.json'
            progress = TemplateProgress(path, {}, CREATORS, [])
            secondary = KeyboardInterrupt('cleanup-only failure')
            try:
                raise RuntimeError('unrelated outer exception')
            except RuntimeError:
                with patch.object(Path, 'unlink', side_effect=secondary):
                    with self.assertRaises(KeyboardInterrupt) as caught:
                        progress._write()
            self.assertIs(caught.exception, secondary)

    def test_stale_pass_report_is_quarantined_and_never_admitted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.json'
            with TemplateProgress(path, {}, CREATORS, INSTALLED) as previous:
                finish(previous)
            previous_bytes = path.read_bytes()
            with self.assertRaises(RuntimeError):
                with TemplateProgress(path, {}, CREATORS, INSTALLED) as current:
                    durable = TemplateProgress.read(path)
                    self.assertEqual(durable['progress']['outcome'], 'running')
                    self.assertEqual(durable['progress']['completed_matrices'], 0)
                    self.assertNotEqual(durable['progress']['run_id'], previous.run_id)
                    self.assertEqual(Path(durable['previous_report']['path']).read_bytes(), previous_bytes)
                    self.assertEqual(durable['previous_report']['scope'], 'preceding invocation')
                    self.assertNotEqual(current.logs, previous.logs)
            self.assertEqual(TemplateProgress.read(path)['progress']['outcome'], 'failed')

    def test_stale_quarantine_refusal_keeps_previous_bytes_and_never_enters(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.json'
            path.write_bytes(b'old report must remain preceding evidence')
            primary = OSError('quarantine denied')
            with patch('v3_v35_templates.os.replace', side_effect=primary):
                with self.assertRaises(OSError) as caught:
                    with TemplateProgress(path, {}, CREATORS, []) as progress:
                        self.fail('an unquarantined stale report entered a new run')
            self.assertIs(caught.exception, primary)
            self.assertEqual(path.read_bytes(), b'old report must remain preceding evidence')

    @unittest.skipIf(os.name == 'nt', 'unprivileged symlinks are not portable on Windows')
    def test_report_symlink_is_quarantined_without_writing_its_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / 'sentinel'
            target.write_bytes(b'preserve unrelated work')
            path = root / 'report.json'
            path.symlink_to(target)
            with self.assertRaises(RuntimeError):
                with TemplateProgress(path, {}, CREATORS, []) as progress:
                    self.assertFalse(path.is_symlink())
                    self.assertTrue(Path(progress.report['previous_report']['path']).is_symlink())
            self.assertEqual(target.read_bytes(), b'preserve unrelated work')

    def test_incomplete_misordered_or_duplicate_matrix_cannot_pass(self):
        for mutation in ('missing', 'duplicate', 'backend', 'optimization', 'installed', 'inputs'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'report.json'
                with self.assertRaises(RuntimeError):
                    with TemplateProgress(path, {}, CREATORS, INSTALLED) as progress:
                        progress.report['creator_matrices'] = [dict(item) for item in CREATORS]
                        progress.report['installed_cli_matrices'] = [dict(item) for item in INSTALLED]
                        progress.report['installed_cli_verified'] = True
                        progress.report['pinned_inputs_unchanged'] = True
                        if mutation == 'missing':progress.report['creator_matrices'].pop()
                        if mutation == 'duplicate':progress.report['creator_matrices'][1] = dict(CREATORS[0])
                        if mutation == 'backend':progress.report['creator_matrices'][0]['backend'] = 'llvm'
                        if mutation == 'optimization':progress.report['creator_matrices'][0]['optimization'] = 3
                        if mutation == 'installed':progress.report['installed_cli_verified'] = False
                        if mutation == 'inputs':progress.report['pinned_inputs_unchanged'] = False
                        progress.matrix_finished()
                        progress.passed()
                self.assertEqual(json.loads(path.read_text())['progress']['outcome'], 'failed')

    def test_clean_incomplete_exit_is_explicitly_failed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.json'
            with self.assertRaisesRegex(RuntimeError, 'without a passing checkpoint'):
                with TemplateProgress(path, {}, CREATORS, INSTALLED):
                    pass
            self.assertEqual(TemplateProgress.read(path)['progress']['outcome'], 'failed')

    def test_torn_oversized_and_inconsistent_reports_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.json'
            with TemplateProgress(path, {}, CREATORS, INSTALLED) as progress:
                finish(progress)
            valid = json.loads(path.read_text())
            malformed = [b'{"progress":', b'x' * (TemplateProgress.MAX_REPORT_BYTES + 1)]
            for change in ({'completed_matrices': 0}, {'completed_creator_matrices': True},
                           {'expected_matrices': 1}, {'sequence': 0}, {'active': {'phase': 'creator-run'}}):
                bad = json.loads(json.dumps(valid));bad['progress'].update(change)
                malformed.append(json.dumps(bad).encode())
            for key, value in (('pinned_inputs_unchanged', False), ('installed_cli_verified', False), ('matrices', [])):
                bad = json.loads(json.dumps(valid));bad[key] = value
                malformed.append(json.dumps(bad).encode())
            for data in malformed:
                path.write_bytes(data)
                with self.assertRaises((ValueError, KeyError, TypeError)):
                    TemplateProgress.read(path)

    def test_command_retains_raw_bytes_status_and_original_text_normalization(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory);path = root / 'report.json'
            with self.assertRaises(RuntimeError):
                with TemplateProgress(path, {}, CREATORS, []) as progress:
                    result = run([sys.executable, '-c', "import os;os.write(1,b'line\\r\\nnext\\rend\\n');os.write(2,b'error\\r\\n');raise SystemExit(7)"],
                                 cwd=root, env=os.environ.copy(), timeout=10, progress=progress, label='inert-output')
                    self.assertEqual((result.returncode, result.stdout, result.stderr), (7, 'line\nnext\nend\n', 'error\n'))
                    record = progress.report['commands'][-1]
                    self.assertEqual(record['timeout_seconds'], 10)
                    self.assertEqual(Path(record['raw_files']['stdout']['path']).read_bytes(), b'line\r\nnext\rend\n')
                    self.assertEqual(Path(record['raw_files']['stderr']['path']).read_bytes(), b'error\r\n')

    def test_command_timeout_retains_partial_channels_and_first_cause(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory);path = root / 'report.json'
            with self.assertRaises(subprocess.TimeoutExpired):
                with TemplateProgress(path, {}, CREATORS, []) as progress:
                    run([sys.executable, '-c', "import os,time;os.write(1,b'partial-out\\n');os.write(2,b'partial-error\\n');time.sleep(30)"],
                        cwd=root, env=os.environ.copy(), timeout=0.2, progress=progress, label='inert-timeout')
            report = TemplateProgress.read(path);record = report['commands'][-1]
            self.assertTrue(record['timed_out'])
            self.assertFalse(record['cleanup_failed'])
            self.assertIsNotNone(record['returncode'])
            self.assertEqual(Path(record['raw_files']['stdout']['path']).read_bytes(), b'partial-out\n')
            self.assertEqual(Path(record['raw_files']['stderr']['path']).read_bytes(), b'partial-error\n')
            self.assertEqual(report['progress']['exception_type'], 'TimeoutExpired')

    def test_process_record_failure_preserves_primary_and_attempts_both_channels(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory);path = root / 'report.json'
            primary = AssertionError('original race assertion')
            with self.assertRaises(AssertionError) as caught:
                with TemplateProgress(path, {}, CREATORS, []) as progress:
                    record = progress.process_record(['inert'], cwd=root, label='inert-race', timeout=10)
                    with patch.object(Path, 'write_bytes', side_effect=KeyboardInterrupt('secondary channel refusal')) as writes, \
                            patch.object(progress, '_write', side_effect=OSError('secondary checkpoint refusal')):
                        progress.process_finished(record, None, b'out', b'err', primary)
                        self.assertEqual(writes.call_count, 2)
                        raise primary
            self.assertIs(caught.exception, primary)
            self.assertEqual(TemplateProgress.read(path)['progress']['outcome'], 'failed')

    def test_hostile_process_cleanup_preserves_primary(self):
        class FakeChild:
            pid = 1234
            returncode = None
            def poll(self):raise SystemExit('secondary poll refusal')
            def kill(self):raise KeyboardInterrupt('secondary kill refusal')
            def communicate(self, timeout):raise OSError('secondary capture refusal')
        class HostileError(RuntimeError):
            def add_note(self, note):raise KeyboardInterrupt('secondary note refusal')

        primary = HostileError('original corpus failure');record = {}
        with patch('v3_v35_templates.os.name', 'posix'), patch('v3_v35_templates.os.killpg', side_effect=OSError('secondary tree refusal')):
            self.assertEqual(cleanup_owned_child(FakeChild(), record, timeout=5, primary=primary), (b'', b''))
        self.assertTrue(record['cleanup_failed'])
        self.assertEqual(record['cleanup_errors'], ['SystemExit', 'OSError', 'SystemExit', 'OSError'])

    def test_killed_main_retains_active_second_matrix_and_prior_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory);path = root / 'report.json'
            env = os.environ.copy()
            env['PYTHONPATH'] = str(Path(__file__).resolve().parent) + os.pathsep + env.get('PYTHONPATH', '')
            child = subprocess.Popen([sys.executable, '-c', INERT_GATE, str(root), str(path)],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
            messages = queue.Queue()
            reader = threading.Thread(target=lambda: [messages.put(line) for line in child.stdout], daemon=True)
            reader.start()
            try:
                for _ in range(3):
                    if messages.get(timeout=5) == b'ACTIVE_SECOND_MATRIX\n':break
                else:self.fail('inert gate did not reach its second matrix')
                durable = TemplateProgress.read(path)
                self.assertEqual(durable['progress']['completed_matrices'], 1)
                self.assertEqual(durable['progress']['expected_matrices'], 2)
                self.assertEqual(durable['progress']['active'], {'phase': 'inert-creator-corpus', 'matrix': 'creator',
                                 'backend': 'c', 'optimization': 2, 'fixture': 'publication-race'})
                child.kill();child.wait(timeout=5)
                self.assertEqual(TemplateProgress.read(path)['progress']['outcome'], 'running')
            finally:
                if child.poll() is None:child.kill()
                child.communicate(timeout=5)
                reader.join(timeout=5)


if __name__ == '__main__':
    unittest.main()
