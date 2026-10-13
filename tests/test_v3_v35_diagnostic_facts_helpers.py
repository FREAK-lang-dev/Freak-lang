#!/usr/bin/env python3
"""Portable inert controls for facts host setup and durable evidence ownership."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

import v3_v35_diagnostic_facts as facts


def controlled_command(stdout=b'', stderr=b'', returncode=0, *, cleanup_failed=False):
    """Model terminal bytes only; never execute a compiler or native fixture."""
    def invoke(command, *, cwd, env, label, prefix, records, expected, timeout, on_record):
        record = {'argv': command, 'cwd': str(cwd), 'case': label, 'expected': expected,
                  'timeout_seconds': timeout, 'mock_child': True,
                  'pid': os.getpid(), 'pid_scope': 'unit interpreter, no child launched'}
        records.append(record)
        on_record(record)
        record.update(returncode=returncode, elapsed_seconds=0, cleanup_failed=cleanup_failed, raw_files={})
        for channel, data in (('stdout', stdout), ('stderr', stderr)):
            path = prefix.with_suffix('.' + channel)
            path.write_bytes(data)
            record[channel + '_sha256'] = hashlib.sha256(data).hexdigest()
            record['raw_files'][channel] = {'path': str(path), 'written': True}
        on_record(record)
        return subprocess.CompletedProcess(command, returncode, stdout, stderr)
    return invoke


def finish_matrices(evidence):
    """Exercise bookkeeping guards; these are explicitly mock contracts."""
    for backend in ('c', 'llvm'):
        evidence.matrix_started(backend)
        for name in facts.CASES:
            evidence.contract_completed(backend, name)
        evidence.matrix_finished(backend)


class FactsHostHelpers(unittest.TestCase):
    def test_selected_bin_and_resource_dlls_precede_foreign_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); bin_dir = root / 'selected' / 'bin'; bin_dir.mkdir(parents=True)
            clang = bin_dir / 'clang.exe'; clang.write_bytes(b'selected inert compiler')
            bin_dll = bin_dir / 'libclang_rt.asan_dynamic-x86_64.dll'; bin_dll.write_bytes(b'mingw ASan')
            resource = root / 'selected' / 'resource'; dll_dir = resource / 'lib' / 'windows'; dll_dir.mkdir(parents=True)
            resource_dll = dll_dir / 'clang_rt.asan_dynamic-x86_64.dll'; resource_dll.write_bytes(b'MSVC ASan')
            foreign = root / 'foreign'; foreign.mkdir(); (foreign / resource_dll.name).write_bytes(b'foreign runtime')
            result = subprocess.CompletedProcess([], 0, str(resource) + '\n', '')
            with mock.patch.object(facts, 'run', return_value=result) as query, mock.patch.object(facts, 'sanitizer_env', return_value={'PATH': str(foreign), 'preserved': 'yes'}):
                env, files = facts.native_environment(clang.resolve(), platform='win32')
            self.assertEqual(query.call_args.args[0], [str(clang.resolve()), '-print-resource-dir'])
            self.assertEqual(query.call_args.kwargs['timeout'], 10)
            self.assertEqual(env['PATH'].split(os.pathsep), [str(bin_dir.resolve()), str(dll_dir.resolve()), str(foreign)])
            self.assertEqual(set(files), {bin_dll, resource_dll}); self.assertEqual(env['preserved'], 'yes')

    def test_missing_selected_runtime_refuses_foreign_or_backup_dll(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); selected = root / 'selected'; selected.mkdir()
            clang = selected / 'clang.exe'; clang.write_bytes(b'inert')
            resource = root / 'resource'; resource.mkdir()
            (selected / 'backup_clang_rt.asan_dynamic-x86_64.dll').write_bytes(b'unrelated')
            foreign = root / 'foreign'; foreign.mkdir(); (foreign / 'clang_rt.asan_dynamic-x86_64.dll').write_bytes(b'foreign')
            with mock.patch.object(facts, 'run', return_value=subprocess.CompletedProcess([], 0, str(resource), '')), mock.patch.object(facts, 'sanitizer_env', return_value={'PATH': str(foreign)}):
                with self.assertRaises(FileNotFoundError): facts.native_environment(clang.resolve(), platform='win32')

    def test_query_failure_timeout_empty_missing_or_file_refuses(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); clang = root / 'clang.exe'; clang.write_bytes(b'inert')
            plain = root / 'not-a-directory'; plain.write_bytes(b'file')
            timeout = subprocess.TimeoutExpired([str(clang)], 10)
            choices = ((subprocess.CompletedProcess([], 2, '', 'controlled failure'), AssertionError),
                       (timeout, subprocess.TimeoutExpired),
                       (subprocess.CompletedProcess([], 0, '\n', ''), ValueError),
                       (subprocess.CompletedProcess([], 0, str(root / 'missing'), ''), FileNotFoundError),
                       (subprocess.CompletedProcess([], 0, str(plain), ''), ValueError))
            for result, kind in choices:
                with self.subTest(kind=kind.__name__, result=repr(result)), mock.patch.object(facts, 'run', side_effect=result if isinstance(result, BaseException) else None, return_value=result):
                    with self.assertRaises(kind) as raised: facts.native_environment(clang.resolve(), platform='win32')
                    if result is timeout: self.assertIs(raised.exception, timeout)

    def test_non_windows_environment_is_unchanged_without_query(self):
        for platform in ('linux', 'darwin'):
            env = {'PATH': 'unchanged', 'ASAN_OPTIONS': 'original setting'}
            with self.subTest(platform=platform), mock.patch.object(facts, 'sanitizer_env', return_value=env), mock.patch.object(facts, 'run') as query:
                actual, files = facts.native_environment(Path('unused-clang'), platform=platform)
            self.assertIs(actual, env); self.assertEqual(files, []); query.assert_not_called()

    def test_selected_clang_resolves_exact_file_and_rejects_invalid_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); clang = root / 'clang.exe'; clang.write_bytes(b'inert')
            with mock.patch.object(facts.shutil, 'which', return_value=str(clang)):
                self.assertEqual(facts.resolve_clang('selected-name'), clang.resolve())
            with mock.patch.object(facts.shutil, 'which', return_value=None):
                self.assertEqual(facts.resolve_clang(str(clang)), clang.resolve())
                with self.assertRaises(ValueError): facts.resolve_clang(str(root))
                with self.assertRaises(FileNotFoundError): facts.resolve_clang(str(root / 'missing'))

    def test_modeled_sigkill_retains_phase_source_raw_resource_and_original_cap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); report = root / 'facts.json'; source = root / 'facts_llvm.fk'; source.write_bytes(b'x' * 287605)
            emitted = Path(str(source) + '.ll'); emitted.write_bytes(b'output' * 5000)
            stdout = b'[4/4] Emitting...\n' + b'x' * 100000; stderr = b'controlled\xffstderr\r\n'
            console = io.StringIO()
            with self.assertRaises(AssertionError), contextlib.redirect_stdout(console), mock.patch.object(facts, 'run_command', side_effect=controlled_command(stdout, stderr, -9)):
                with facts.FactsEvidence(report, root) as evidence:
                    evidence.source_snapshot(source, 'llvm'); evidence.stage('compiler-emission', backend='llvm')
                    facts.require_ok(evidence.run(['inert-compiler', str(source), '--llvm'], root, emitted=emitted), 'emission')
            saved = json.loads(report.read_text()); active = saved['progress']['active']; command = saved['commands'][0]
            self.assertEqual(saved['progress']['outcome'], 'failed'); self.assertEqual(active['phase'], 'compiler-emission'); self.assertEqual(active['backend'], 'llvm'); self.assertEqual(active['returncode'], -9)
            self.assertEqual(active['resource']['python_pid'], os.getpid()); self.assertIn('resource_after', active)
            self.assertEqual(command['timeout_seconds'], 180); self.assertIsNone(command['expected']); self.assertTrue(command['mock_child'])
            snapshot = saved['source_snapshots']['llvm']; self.assertEqual(snapshot['bytes'], 287605); self.assertEqual(Path(snapshot['retained_path']).read_bytes(), source.read_bytes())
            self.assertEqual(Path(command['raw_files']['stdout']['path']).read_bytes(), stdout); self.assertEqual(Path(command['raw_files']['stderr']['path']).read_bytes(), stderr)
            output = saved['emitted_outputs'][str(emitted)]; self.assertTrue(output['stable']); self.assertEqual(output['bytes'], 30000); self.assertEqual(output['tail_bytes'], 16384)
            self.assertEqual(Path(output['tail_path']).read_bytes(), emitted.read_bytes()[-16384:])
            self.assertTrue(all(len(line) <= 4020 for line in console.getvalue().splitlines()))

    def test_failed_resource_query_has_durable_phase_and_ten_second_cap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); report = root / 'facts.json'; clang = root / 'clang.exe'; clang.write_bytes(b'inert')
            with self.assertRaises(AssertionError), contextlib.redirect_stdout(io.StringIO()), mock.patch.object(facts, 'run_command', side_effect=controlled_command(b'query output', b'query failure', 1)):
                with facts.FactsEvidence(report, root) as evidence:
                    evidence.stage('sanitizer-resource-query')
                    facts.native_environment(clang, evidence, platform='win32')
            saved = json.loads(report.read_text()); self.assertEqual(saved['progress']['outcome'], 'failed'); self.assertEqual(saved['progress']['active']['phase'], 'sanitizer-resource-query')
            self.assertEqual(saved['commands'][0]['timeout_seconds'], 10)
            self.assertEqual(Path(saved['commands'][0]['raw_files']['stderr']['path']).read_bytes(), b'query failure')

    def test_raw_bytes_and_legacy_utf8_newline_text_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); stdout = b'a\r\nb\rc\xff'; stderr = b'bad\xff\r\nline\r'
            evidence = facts.FactsEvidence(None, root); evidence.__enter__()
            with contextlib.redirect_stdout(io.StringIO()), mock.patch.object(facts, 'run_command', side_effect=controlled_command(stdout, stderr)):
                evidence.stage('inert-command'); result = evidence.run(['inert'], root)
            self.assertEqual(result.stdout, 'a\nb\nc\ufffd'); self.assertEqual(result.stderr, 'bad\ufffd\nline\n')
            for channel, data in (('stdout', stdout), ('stderr', stderr)):
                self.assertEqual(Path(evidence.report['commands'][0]['raw_files'][channel]['path']).read_bytes(), data)
            self.assertFalse(evidence.__exit__(ValueError, ValueError('modeled end'), None))

    def test_partial_contracts_cannot_pass(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            root = Path(directory); report = root / 'facts.json'
            with self.assertRaises(ValueError):
                with facts.FactsEvidence(report, root) as evidence:
                    evidence.matrix_started('c'); evidence.contract_completed('c', 'unbound'); evidence.passed()
            saved = json.loads(report.read_text()); self.assertEqual(saved['progress']['outcome'], 'failed'); self.assertEqual(saved['progress']['completed_contracts'], 1)

    def test_complete_mock_matrices_require_final_pins(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            root = Path(directory); report = root / 'facts.json'; pinned = root / 'input'; pinned.write_bytes(b'pinned')
            with facts.FactsEvidence(report, root) as evidence:
                evidence.pin(pinned); finish_matrices(evidence); evidence.passed()
            saved = json.loads(report.read_text()); self.assertEqual(saved['progress']['outcome'], 'passed'); self.assertTrue(saved['pinned_inputs_unchanged']); self.assertEqual(saved['progress']['completed_contracts'], 26)
            self.assertEqual([m['backend'] for m in saved['matrices']], ['c', 'llvm']); self.assertTrue(all(m['completed_cases'] == list(facts.CASES) for m in saved['matrices']))

    def test_normal_unfinished_exit_is_durably_failed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); report = root / 'facts.json'
            with self.assertRaises(RuntimeError):
                with facts.FactsEvidence(report, root): pass
            self.assertEqual(json.loads(report.read_text())['progress']['outcome'], 'failed')

    def test_changed_input_bytes_block_pass(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            root = Path(directory); report = root / 'facts.json'; pinned = root / 'input'; pinned.write_bytes(b'first')
            with self.assertRaises(AssertionError):
                with facts.FactsEvidence(report, root) as evidence:
                    evidence.pin(pinned); finish_matrices(evidence); pinned.write_bytes(b'changed'); evidence.passed()
            self.assertEqual(json.loads(report.read_text())['progress']['outcome'], 'failed')

    def test_same_bytes_changed_path_resolution_blocks_pass(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            root = Path(directory); report = root / 'facts.json'; first = root / 'first'; second = root / 'second'; first.write_bytes(b'same'); second.write_bytes(b'same')
            original_resolve = Path.resolve
            def changed(path, *args, **kwargs): return second if path == first else original_resolve(path, *args, **kwargs)
            with self.assertRaises(AssertionError):
                with facts.FactsEvidence(report, root) as evidence:
                    evidence.pin(first); finish_matrices(evidence)
                    with mock.patch.object(Path, 'resolve', autospec=True, side_effect=changed): evidence.passed()
            self.assertEqual(json.loads(report.read_text())['progress']['outcome'], 'failed')

    def test_recording_failure_keeps_original_interrupt_and_valid_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); report = root / 'facts.json'; evidence = facts.FactsEvidence(report, root); evidence.__enter__(); previous = report.read_bytes()
            primary = KeyboardInterrupt('original controlled operation interruption')
            with self.assertRaises(KeyboardInterrupt) as raised:
                with mock.patch.object(facts.os, 'replace', side_effect=OSError('controlled recording failure')):
                    self.assertFalse(evidence.__exit__(type(primary), primary, None)); raise primary
            self.assertIs(raised.exception, primary); self.assertEqual(report.read_bytes(), previous); self.assertEqual(json.loads(previous)['progress']['outcome'], 'running')
            self.assertEqual(primary.__notes__, ['Facts evidence recording failed: OSError']); self.assertFalse(list(root.glob('.facts.json-*')))


class FactsAtomicCleanupHelpers(unittest.TestCase):
    def primary_failure(self, primary, secondary, operation='replace'):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); report = root / 'facts.json'; evidence = facts.FactsEvidence(report, root); evidence.__enter__(); previous = report.read_bytes()
            with mock.patch.object(facts.os, operation, side_effect=primary), mock.patch.object(Path, 'unlink', side_effect=secondary):
                with self.assertRaises(type(primary)) as raised: evidence._write()
            self.assertIs(raised.exception, primary); self.assertEqual(report.read_bytes(), previous); self.assertEqual(json.loads(previous)['progress']['outcome'], 'running')
            staged = list(root.glob('.facts.json-*')); self.assertEqual(len(staged), 1)
            for path in staged:
                self.assertEqual(path.parent, root); path.unlink()
            self.assertFalse(list(root.glob('.facts.json-*')))

    def test_primary_io_error_survives_secondary_keyboard_interrupt(self):
        for operation in ('replace', 'fsync'):
            with self.subTest(operation=operation):
                primary = OSError('controlled primary ' + operation); self.primary_failure(primary, KeyboardInterrupt('secondary unlink interruption'), operation)
                self.assertEqual(primary.__notes__, ['Facts staged-file cleanup failed: KeyboardInterrupt'])

    def test_hostile_note_lookup_or_call_cannot_mask_primary(self):
        class HostileLookup(OSError):
            @property
            def add_note(self): raise KeyboardInterrupt('hostile note lookup')
        class HostileCall(OSError):
            def add_note(self, note): raise SystemExit('hostile note call')
        for kind in (HostileLookup, HostileCall):
            with self.subTest(kind=kind.__name__): self.primary_failure(kind('original recording failure'), OSError('secondary unlink failure'))

    def test_secondary_cleanup_note_is_bounded(self):
        kind = type('Cleanup' + 'x' * 1000, (OSError,), {}); primary = OSError('original recording failure'); self.primary_failure(primary, kind('secondary unlink failure'))
        self.assertEqual(primary.__notes__, ['Facts staged-file cleanup failed: ' + kind.__name__[:160]]); self.assertLessEqual(len(primary.__notes__[0]), 200)

    def test_cleanup_failure_without_local_primary_is_still_propagated(self):
        for ambient in (False, True):
            with self.subTest(ambient=ambient), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); report = root / 'facts.json'; evidence = facts.FactsEvidence(report, root); evidence.__enter__(); previous = report.read_bytes(); secondary = OSError('cleanup after successful replacement')
                def invoke():
                    with mock.patch.object(Path, 'unlink', side_effect=secondary):
                        with self.assertRaises(OSError) as raised: evidence._write()
                    self.assertIs(raised.exception, secondary)
                if ambient:
                    try: raise ValueError('unrelated caller exception')
                    except ValueError: invoke()
                else: invoke()
                self.assertNotEqual(report.read_bytes(), previous); self.assertEqual(json.loads(report.read_text())['progress']['outcome'], 'running'); self.assertFalse(list(root.glob('.facts.json-*')))


if __name__ == '__main__': unittest.main()
