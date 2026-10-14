"""Template evidence controls; subprocess fixtures run inert Python only."""
from pathlib import Path
import io
import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from v3_v35_templates import TemplateProgress, cleanup_owned_child, creator_corpus, directory_has_entry, http_once, run


CREATORS = [{'backend': backend, 'optimization': opt}
            for backend in ('c', 'llvm') for opt in (0, 2, 3)]
INSTALLED = [{'template': kind, 'backend': backend}
             for kind in ('cli', 'lib', 'http') for backend in ('c', 'llvm')]


def posix_model():
    # Replace only the gate's OS binding. Changing shared os.name changes
    # pathlib and subprocess behavior elsewhere in the Windows test process.
    return SimpleNamespace(**{**vars(os), 'name': 'posix'})


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
        # The parent retains and matches raw bytes on every host. A text print
        # translates this marker to CRLF on Windows before it reaches the pipe.
        sys.stdout.buffer.write(b'ACTIVE_SECOND_MATRIX\n')
        sys.stdout.buffer.flush()
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
        with patch('v3_v35_templates.os', posix_model()):
            self.assertEqual(cleanup_owned_child(FakeChild(), record, timeout=5, primary=primary), (b'', b''))
        self.assertTrue(record['cleanup_failed'])
        self.assertEqual(record['cleanup_errors'], ['SystemExit', 'SystemExit', 'OSError'])

    def test_http_timeout_call_site_preserves_each_known_channel(self):
        class Socket:
            def __enter__(self):return self
            def __exit__(self, *args):pass
            def sendall(self, data):pass
            def recv(self, size):
                if getattr(self, 'sent', False):return b''
                self.sent = True
                return b'HTTP/1.1 200 OK\r\nContent-Length: 7\r\nConnection: close\r\n\r\nhealthy'

        banner = b'HTTP http://127.0.0.1:1234\n'
        for recovery in ('absent', 'stdout-only', 'stderr-only'):
            with self.subTest(recovery=recovery), tempfile.TemporaryDirectory() as directory:
                root = Path(directory);path = root / 'report.json'
                primary = subprocess.TimeoutExpired(['inert-http'], 10, output=b'first-out', stderr=b'first-err')
                secondary = (OSError('secondary capture refusal') if recovery == 'absent' else
                             subprocess.TimeoutExpired(['inert-http'], 5,
                                                       output=b'recovery-out' if recovery == 'stdout-only' else None,
                                                       stderr=b'recovery-err' if recovery == 'stderr-only' else None))
                class Child:
                    pid = 1234
                    returncode = None
                    stdout = io.BytesIO(banner)
                    calls = 0
                    def poll(self):return self.returncode
                    def kill(self):self.returncode = -9
                    def communicate(self, timeout):
                        self.calls += 1
                        raise primary if self.calls == 1 else secondary
                child = Child()
                def popen(command, **kwargs):
                    self.assertNotIn('start_new_session', kwargs)
                    self.assertEqual(kwargs['bufsize'], 0)
                    return child
                with self.assertRaises(subprocess.TimeoutExpired) as caught:
                    with TemplateProgress(path, {}, CREATORS, []) as progress:
                        with patch('v3_v35_templates.subprocess.Popen', side_effect=popen), \
                                patch('v3_v35_templates.select.select', return_value=([child.stdout], [], [])), \
                                patch('v3_v35_templates.os', posix_model()), \
                                patch('socket.create_connection', return_value=Socket()):
                            http_once(Path('inert'), root, 'c', os.environ.copy(), progress)
                self.assertIs(caught.exception, primary)
                record = TemplateProgress.read(path)['commands'][-1]
                self.assertEqual(Path(record['raw_files']['stdout']['path']).read_bytes(),
                                 banner + (b'recovery-out' if recovery == 'stdout-only' else b'first-out'))
                self.assertEqual(Path(record['raw_files']['stderr']['path']).read_bytes(),
                                 b'recovery-err' if recovery == 'stderr-only' else b'first-err')

    def test_race_timeout_call_site_preserves_completed_and_partial_children(self):
        for recovery in ('absent', 'stdout-only', 'stderr-only'):
            with self.subTest(recovery=recovery), tempfile.TemporaryDirectory() as directory:
                root = Path(directory);path = root / 'report.json'
                canonical = root / 'payload/templates/v35'
                canonical.mkdir(parents=True);(root / 'payload/runtime').mkdir()
                scratch = root / 'scratch';scratch.mkdir()
                primary = subprocess.TimeoutExpired(['inert-race'], 10, output=b'first-out', stderr=b'first-err')
                secondary = (OSError('secondary capture refusal') if recovery == 'absent' else
                             subprocess.TimeoutExpired(['inert-race'], 10,
                                                       output=b'recovery-out' if recovery == 'stdout-only' else None,
                                                       stderr=b'recovery-err' if recovery == 'stderr-only' else None))
                class Child:
                    def __init__(self, index):
                        self.pid = 1234 + index;self.index = index;self.calls = 0
                        self.returncode = 0 if index == 0 else None
                    def poll(self):return self.returncode
                    def kill(self):self.returncode = -9
                    def communicate(self, timeout):
                        self.calls += 1
                        if self.index == 0:return b'OK\n', b''
                        raise primary if self.calls == 1 else secondary
                children = []
                def popen(command, **kwargs):
                    self.assertNotIn('start_new_session', kwargs)
                    child = Child(len(children));children.append(child)
                    return child
                with self.assertRaises(subprocess.TimeoutExpired) as caught:
                    with TemplateProgress(path, {}, CREATORS, []) as progress:
                        with patch('v3_v35_templates.creator_case') as creator, \
                                patch('v3_v35_templates.tree', return_value={}), \
                                patch('v3_v35_templates.expected', return_value={}), \
                                patch('v3_v35_templates.subprocess.run', return_value=
                                      subprocess.CompletedProcess(['inert-taskkill'], 0, b'', b'')) as taskkill, \
                                patch('v3_v35_templates.subprocess.Popen', side_effect=popen):
                            creator_corpus(Path('inert'), canonical, scratch, os.environ.copy(), progress)
                self.assertIs(caught.exception, primary)
                rejected_names = [call.args[2].name for call in creator.call_args_list
                                  if not call.kwargs['success']]
                expected_rejected = [
                    'cli-demo', 'lib-demo', 'http-demo', 'sentinel', 'empty', 'regular',
                    'bad name', 'bad"name', 'bad$name', 'bad&name', 'é', '9start',
                    'CON', 'nul', 'LPT9', 'COM1', 'x' * 65, 'unknown', 'child']
                if os.name != 'nt':expected_rejected += ['linked', 'broken', 'escape']
                self.assertEqual(rejected_names, expected_rejected)
                self.assertEqual(len(children), 2)
                if os.name == 'nt':
                    self.assertEqual(taskkill.call_count, 2)
                    self.assertEqual([call.args[0] for call in taskkill.call_args_list], [
                        ['taskkill', '/PID', '1234', '/T', '/F'],
                        ['taskkill', '/PID', '1235', '/T', '/F']])
                    self.assertTrue(all(call.kwargs['timeout'] == 10
                                        for call in taskkill.call_args_list))
                else:taskkill.assert_not_called()
                records = TemplateProgress.read(path)['commands']
                self.assertEqual(len(records), 2)
                self.assertEqual(Path(records[0]['raw_files']['stdout']['path']).read_bytes(), b'OK\n')
                self.assertEqual(Path(records[0]['raw_files']['stderr']['path']).read_bytes(), b'')
                self.assertEqual(Path(records[1]['raw_files']['stdout']['path']).read_bytes(),
                                 b'recovery-out' if recovery == 'stdout-only' else b'first-out')
                self.assertEqual(Path(records[1]['raw_files']['stderr']['path']).read_bytes(),
                                 b'recovery-err' if recovery == 'stderr-only' else b'first-err')

    def test_directory_entry_oracle_never_follows_reserved_or_broken_leaves(self):
        original_name = os.name
        path_class = type(Path('.'))
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            for name in ('CON', 'nul', 'LPT9', 'COM1'):
                self.assertFalse(directory_has_entry(parent / name))
            existing = parent / 'ordinary';existing.write_bytes(b'preserve\0')
            self.assertTrue(directory_has_entry(existing))
            self.assertFalse(directory_has_entry(parent / 'absent'))
            self.assertEqual(existing.read_bytes(), b'preserve\0')
        def cannot_follow():
            self.fail('directory-entry oracle followed a candidate leaf')
        entries = [SimpleNamespace(name='NuL', exists=cannot_follow),
                   SimpleNamespace(name='broken', exists=cannot_follow)]
        parent = SimpleNamespace(iterdir=lambda: iter(entries))
        for platform in ('posix', 'nt'):
            model = posix_model();model.name = platform
            with self.subTest(platform=platform), patch('v3_v35_templates.os', model):
                self.assertEqual(directory_has_entry(SimpleNamespace(parent=parent, name='nul',
                                                                     exists=cannot_follow)),
                                 platform == 'nt')
                self.assertTrue(directory_has_entry(SimpleNamespace(parent=parent, name='broken',
                                                                    exists=cannot_follow)))
                self.assertFalse(directory_has_entry(SimpleNamespace(parent=parent, name='absent',
                                                                     exists=cannot_follow)))
                self.assertEqual(os.name, original_name)
                self.assertIs(type(Path('.')), path_class)

    def test_http_banner_and_extra_output_share_one_unbuffered_capture(self):
        class Socket:
            def __enter__(self):return self
            def __exit__(self, *args):pass
            def sendall(self, data):pass
            def recv(self, size):
                if getattr(self, 'sent', False):return b''
                self.sent = True
                return b'HTTP/1.1 200 OK\r\nContent-Length: 7\r\nConnection: close\r\n\r\nhealthy'

        emitted = b'HTTP http://127.0.0.1:1234\nEXTRA-RAW-OUTPUT\n'
        real_popen = subprocess.Popen
        children = []
        def popen(command, **kwargs):
            self.assertNotIn('start_new_session', kwargs)
            self.assertEqual(kwargs['bufsize'], 0)
            child = real_popen([sys.executable, '-B', '-c',
                               'import os,time;os.write(1,' + repr(emitted) + ');time.sleep(0.1)'], **kwargs)
            children.append(child)
            if os.name != 'nt':self.assertEqual(os.getpgid(child.pid), os.getpgrp())
            return child
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory);path = root / 'report.json'
            try:
                with self.assertRaisesRegex(RuntimeError, 'without a passing checkpoint'):
                    with TemplateProgress(path, {}, CREATORS, []) as progress:
                        with patch('v3_v35_templates.subprocess.Popen', side_effect=popen), \
                                patch('socket.create_connection', return_value=Socket()):
                            http_once(Path('inert'), root, 'c', os.environ.copy(), progress)
                        raw = Path(progress.report['commands'][-1]['raw_files']['stdout']['path']).read_bytes()
                        self.assertEqual(raw, emitted)
            finally:
                for child in children:
                    if child.poll() is None:child.kill()
                    child.communicate(timeout=5)

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
