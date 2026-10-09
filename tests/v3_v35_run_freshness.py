#!/usr/bin/env python3
"""Public run-cache graph freshness using an explicitly fresh native CLI."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

from windows_private_fixture import WindowsPrivateFixture
from v3_v35_acceptance import run_command as bounded_run

ANSI = re.compile(rb'\x1b\[[0-9;]*m')
MUTATOR = r'''
#include "freak_runtime.c"
int main(int argc, char **argv) {
    freak_argc = argc; freak_argv = argv;
    bool compiling = false;
    for (int i = 1; i < argc; ++i)
        if (freak_word_ends_with(freak_process_arg(i), freak_word_lit(".c")) ||
            freak_word_ends_with(freak_process_arg(i), freak_word_lit(".ll"))) compiling = true;
    freak_word path = freak_process_env(freak_word_lit("FREAK_FRESHNESS_EDIT"));
    if (compiling && path.length) {
        freak_word body = freak_process_env(freak_word_lit("FREAK_FRESHNESS_BODY"));
        int64_t result = body.length ? freak_fs_write_checked(path, body) : freak_fs_remove_checked(path);
        bool ok = freak_fs_result_ok(result); freak_fs_result_release(result);
        freak_word_release_owned(&body);
        if (!ok) return 95;
        freak_word log = freak_process_env(freak_word_lit("FREAK_FRESHNESS_LOG"));
        freak_fs_append(log, freak_word_lit("native mutation completed\n"));
        freak_word_release_owned(&log);
    }
    freak_word_release_owned(&path);
    freak_word clang = freak_process_env(freak_word_lit("FREAK_FRESHNESS_REAL_CLANG"));
    int64_t command = freak_process_command_new(clang); freak_word_release_owned(&clang);
    for (int i = 1; i < argc; ++i) freak_process_command_arg(command, freak_process_arg(i));
    int64_t state = freak_process_command_run_inherit(command, 120000);
    int status = state == 2 ? (int)freak_process_command_exit_code(command) : 96;
    freak_process_command_release(command);
    return status;
}
'''


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence_targets(evidence: Path, protected: tuple[Path, ...]) -> tuple[Path, Path]:
    """Reject output/input overlap before creating directories or receipts."""
    outputs = (evidence.absolute(), evidence.absolute().parent / (evidence.stem + '-raw'))
    inputs = tuple(path.resolve(strict=True) for path in protected)
    selected = []
    for output in outputs:
        physical = output.resolve()
        for source in inputs:
            if physical == source or physical.is_relative_to(source) or source.is_relative_to(physical):
                raise ValueError(f'evidence output overlaps protected input: {output}')
        # A fresh artifact also prevents overwriting an external hardlink to a
        # protected file and keeps earlier success/failure receipts intact.
        if output.exists() or output.is_symlink() or physical.exists():
            raise ValueError(f'evidence output must be fresh: {output}')
        selected.append(physical)
    return selected[0], selected[1]


def fixture(root: Path, private: WindowsPrivateFixture) -> dict[str, Path]:
    for name in ('app', 'bridge', 'core'):
        (root / name / 'src').mkdir(parents=True)
    private.claim_fresh_directories(root, *(root / name for name in ('app', 'bridge', 'core')),
                                    *(root / name / 'src' for name in ('app', 'bridge', 'core')))
    files = {'app': root / 'app/hangar.toml', 'bridge': root / 'bridge/hangar.toml',
             'core_manifest': root / 'core/hangar.toml', 'entry': root / 'app/src/main.fk',
             'direct': root / 'bridge/src/value.fk', 'transitive': root / 'core/src/value.fk'}
    files['app'].write_text('[project]\nname="fresh_app"\nversion="1.0.0"\nkind="app"\nentry="src/main.fk"\n'
                            '[dependencies]\nbridge={path="../bridge"}\n', encoding='utf-8')
    files['bridge'].write_text('[project]\nname="fresh_bridge"\nversion="1.0.0"\nkind="lib"\n'
                               '[modules]\nvalue="src/value.fk"\n[exports]\nvalue="value::value"\n'
                               '[dependencies]\ncore={path="../core"}\n', encoding='utf-8')
    files['core_manifest'].write_text('[project]\nname="fresh_core"\nversion="1.0.0"\nkind="lib"\n'
                                      '[modules]\nvalue="src/value.fk"\n[exports]\nvalue="value::value"\n', encoding='utf-8')
    files['entry'].write_text('use bridge::{value}\ntask main() { say "PKG_RUN=" + word_from_int(value() * 2) }\n', encoding='utf-8')
    files['direct'].write_text('use core::{value as seed}\ntask value() -> int { give back seed() + 1 }\n', encoding='utf-8')
    files['transitive'].write_text('task value() -> int { give back 20 }\n', encoding='utf-8')
    return files


def run_freshness_command(label: str, argv: list[str], cwd: Path, env: dict[str, str],
                          *, report: dict, raw: Path, save, timeout: float = 120) -> tuple[int, bytes]:
    """Keep freshness evidence fields while sharing bounded child-tree capture."""
    ordinal = len(report['commands']) + 1
    prefix = raw / f'{ordinal:03d}'
    started_ns = time.time_ns()
    environment = {key: env.get(key) for key in
                   ('FREAK_HOME', 'FREAK_CLANG', 'FREAK_FRESHNESS_EDIT', 'FREAK_FRESHNESS_BODY')}

    def checkpoint(record: dict) -> None:
        record.setdefault('started_ns', started_ns)
        record.setdefault('environment', environment)
        recording_error = None
        if 'returncode' in record:
            record.setdefault('finished_ns', time.time_ns())
            for channel in ('stdout', 'stderr'):
                path = raw / f'{ordinal:03d}-{channel}.raw'
                retained = record.get('raw_files', {}).get(channel, {})
                metadata = {'path': str(path), 'sha256': record[channel + '_sha256'],
                            'bytes': None if 'pid' in record else 0, 'written': False}
                record[channel] = metadata
                if retained.get('written'):
                    try:
                        data = Path(retained['path']).read_bytes()
                        metadata['bytes'] = len(data)
                        path.write_bytes(data)
                        metadata['written'] = True
                    except Exception as error:
                        metadata['error'] = repr(error)
                        record.setdefault('recording_errors', []).append(repr(error))
                        if recording_error is None:
                            recording_error = error
                else:
                    metadata['error'] = retained.get('error', 'raw channel was not retained')
        try:
            save()
        except Exception as error:
            if recording_error is None:
                recording_error = error
        if recording_error is not None:
            raise recording_error

    try:
        result = bounded_run(argv, cwd=cwd, env=env, label=label, prefix=prefix,
                             records=report['commands'], expected=None, timeout=timeout,
                             on_record=checkpoint)
        return result.returncode, ANSI.sub(b'', result.stdout + result.stderr)
    except BaseException as error:
        if len(report['commands']) >= ordinal:
            record = report['commands'][ordinal - 1]
            record['error'] = repr(error)
            if isinstance(error, subprocess.TimeoutExpired):
                # Bytes remain knowable even if evidence storage itself failed.
                for channel, data in (('stdout', error.output), ('stderr', error.stderr)):
                    if data is not None and channel in record:
                        record[channel]['bytes'] = len(data)
            try:
                save()
            except Exception as recording_error:
                record.setdefault('recording_errors', []).append(repr(recording_error))
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('freak', type=Path, help='fresh exact-source native CLI; never reconstructed here')
    parser.add_argument('--clang', type=Path, required=True)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--backend', choices=('both', 'c', 'llvm'), default='both')
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    freak, clang, repo = args.freak.resolve(strict=True), args.clang.absolute(), args.repo.resolve(strict=True)
    evidence, raw = evidence_targets(args.evidence, (repo, freak, clang, Path(__file__)))
    evidence.parent.mkdir(parents=True, exist_ok=True)
    raw.mkdir()
    inputs = {str(freak): sha(freak), str(clang): sha(clang), str(Path(__file__).resolve()): sha(Path(__file__).resolve())}
    report = {'status': 'RUNNING', 'host': sys.platform, 'inputs_before': inputs, 'commands': [], 'checks': []}

    def save() -> None:
        evidence.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')

    def run(label: str, argv: list[str], cwd: Path, env: dict[str, str], timeout: int = 120) -> tuple[int, bytes]:
        return run_freshness_command(label, argv, cwd, env, report=report,
                                     raw=raw, save=save, timeout=timeout)

    try:
        with tempfile.TemporaryDirectory(prefix='freak-run-graph-freshness-') as temporary:
            root = Path(temporary).resolve()
            private = WindowsPrivateFixture(root)
            home = root / 'installed payload'
            for line in (repo / 'packaging/distribution-files.manifest').read_text().splitlines():
                if not line or line.startswith('#'):
                    continue
                original, relative = line.split('|')
                destination = home / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(repo / original, destination)
            private.claim_fresh_directories(home, *(path for path in home.rglob('*') if path.is_dir()))
            report['payload_before'] = {path.relative_to(home).as_posix(): sha(path) for path in home.rglob('*') if path.is_file()}
            env = os.environ.copy()
            env.update(FREAK_HOME=str(home), FREAK_CLANG=str(clang), TMPDIR=str(root), TEMP=str(root), TMP=str(root))
            mutator_source = root / 'native mutator.c'
            mutator_source.write_text(MUTATOR, encoding='utf-8')
            mutator = root / ('native mutator.exe' if os.name == 'nt' else 'native mutator')
            code, output = run('build-native-mutation-fixture', [str(clang), '-O0', str(mutator_source), '-I', str(home / 'runtime'),
                               '-o', str(mutator), '-lws2_32' if os.name == 'nt' else '-lm'], root, env)
            assert code == 0, output
            report['mutator_sha256'] = sha(mutator)

            for backend in (('c', 'llvm') if args.backend == 'both' else (args.backend,)):
                graph_root = root / f'graph {backend} é 日本 \x27 $ &'
                files = fixture(graph_root, private)
                app = files['app'].parent
                binary = files['entry'].with_suffix('.exe' if os.name == 'nt' else '')
                cache = Path(str(binary) + '.freak-run-cache')
                lock = app / 'hangar.lock'

                def source_vector() -> dict:
                    selected = [path for path in graph_root.rglob('*') if path.is_file()
                                and '.freak' not in path.relative_to(graph_root).parts
                                and (path.suffix == '.fk' or path.name in ('hangar.toml', 'hangar.lock'))]
                    return {path.relative_to(graph_root).as_posix(): {'sha256': sha(path), 'bytes_hex': path.read_bytes().hex()}
                            for path in selected}

                def invoke(label: str, value: int | None, hit: bool | None, flags: tuple[str, ...] = (), active: dict[str, str] = env, source: Path | None = None, rejection: bytes = b'RUN ABORTED') -> None:
                    before = source_vector()
                    selected = [str(source)] if source is not None else []
                    code, output = run(f'{backend}:{label}', [str(freak), 'run', *selected, f'--{backend}', '--opt=0', '--strict-borrow', *flags], app, active)
                    report['commands'][-1]['sources_before'] = before
                    report['commands'][-1]['sources_after'] = source_vector()
                    if value is None:
                        assert code == 1 and rejection in output and b'PKG_RUN=' not in output and b'RUNNING' not in output and b'run cache hit' not in output, output
                    else:
                        assert code == 0 and re.findall(rb'^PKG_RUN=(\d+)$', output, re.M) == [str(value).encode()], output
                        assert (b'run cache hit' in output) is hit, output
                    report['checks'].append(f'{backend}:{label}')
                    report['commands'][-1]['live_sources'] = {name: sha(path) if path.exists() else None for name, path in files.items()}
                    report['commands'][-1]['artifact_sha256'] = sha(binary) if binary.exists() else None
                    report['commands'][-1]['cache_sha256'] = sha(cache) if cache.exists() else None
                    save()
                    print(f'PASS {backend}:{label}', flush=True)

                invoke('cold-run', 42, False)
                artifact, sidecar = binary.read_bytes(), cache.read_bytes()
                invoke('unchanged-cache-hit', 42, True)
                assert binary.read_bytes() == artifact and cache.read_bytes() == sidecar
                files['transitive'].write_text('task value() -> int { give back 21 }\n', encoding='utf-8')
                invoke('transitive-edit', 44, False)
                files['direct'].write_text('use core::{value as seed}\ntask value() -> int { give back seed() + 2 }\n', encoding='utf-8')
                invoke('direct-edit', 46, False)
                files['entry'].write_text('use bridge::{value}\ntask main() { say "PKG_RUN=" + word_from_int(value() * 3) }\n', encoding='utf-8')
                invoke('entry-edit', 69, False)
                files['app'].write_bytes(files['app'].read_bytes() + b'\n# exact manifest bytes changed\n')
                invoke('manifest-byte-edit', 69, False)
                before_extra = files['app'].read_bytes()
                extra = app / 'src/extra.fk'
                extra.write_text('task extra() -> int { give back 123 }\n', encoding='utf-8')
                files['app'].write_bytes(before_extra + b'[modules]\nextra="src/extra.fk"\n')
                invoke('declared-source-added', 69, False)
                extra.unlink()
                invoke('declared-source-deleted', None, None)
                extra.write_text('task extra() -> int { give back 123 }\n', encoding='utf-8')
                invoke('missing-source-recovery', 69, True)
                files['app'].write_bytes(before_extra)
                extra.unlink()
                invoke('declared-source-removed-from-manifest', 69, False)
                original_core = files['transitive'].read_bytes()
                files['transitive'].write_text('task value() -> int { give back true }\n', encoding='utf-8')
                invoke('invalid-dependency-rebuild', None, None, rejection=b'type/borrow error(s) -- code generation skipped')
                assert not cache.exists(), 'failed rebuild retained a cache proof'
                files['transitive'].write_bytes(original_core)
                invoke('failed-rebuild-recovery', 69, False)
                files['transitive'].write_bytes(original_core + b'\0')
                invoke('invalid-source-text-admission', None, None)
                files['transitive'].write_bytes(original_core)
                invoke('text-admission-recovery', 69, True)
                frozen_lock = lock.read_bytes()
                files['transitive'].write_text('task value() -> int { give back 22 }\n', encoding='utf-8')
                invoke('frozen-source-change-before-cache', None, None, ('--frozen',))
                assert lock.read_bytes() == frozen_lock
                files['transitive'].write_bytes(original_core)
                invoke('frozen-unchanged-cache-hit', 69, True, ('--frozen',))
                original_manifest = files['app'].read_bytes()
                files['app'].write_bytes(original_manifest + b'# locked manifest changed\n')
                invoke('locked-manifest-change-before-cache', None, None, ('--locked',))
                assert lock.read_bytes() == frozen_lock
                files['app'].write_bytes(original_manifest)
                invoke('locked-unchanged-cache-hit', 69, True, ('--locked',))
                lock.write_bytes(b'[lock]\nschema=999\n')
                for flags in ((), ('--locked',), ('--frozen',)):
                    invoke('invalid-lock-before-cache-' + (flags[0] if flags else 'normal'), None, None, flags)
                lock.write_bytes(frozen_lock)
                invoke('lock-recovery', 69, True)
                lock.write_bytes(frozen_lock + b'# permitted lock comment changes exact input identity\n')
                invoke('locked-valid-lock-byte-edit', 69, False, ('--locked',))
                lock.write_bytes(frozen_lock)
                invoke('lock-byte-restore', 69, False)
                snapshot = app / '.freak/graphs' / (hashlib.sha256(lock.read_bytes()).hexdigest() + '.lock')
                selected = ('--graph-snapshot=' + str(snapshot),)
                invoke('immutable-snapshot-cache-hit', 69, True, selected)
                files['transitive'].write_text('task value() -> int { give back 23 }\n', encoding='utf-8')
                invoke('snapshot-live-source-change-before-cache', None, None, selected)
                files['transitive'].write_bytes(original_core)
                snapshot_bytes = snapshot.read_bytes()
                snapshot.write_bytes(b'[lock]\nschema=999\n')
                invoke('corrupt-selected-snapshot-before-cache', None, None, selected)
                snapshot.write_bytes(snapshot_bytes)
                invoke('snapshot-recovery', 69, True, selected)

                racing = env | {'FREAK_CLANG': str(mutator), 'FREAK_FRESHNESS_REAL_CLANG': str(clang),
                                'FREAK_FRESHNESS_LOG': str(root / f'{backend}-mutation.log')}
                invoke('native-mutator-warmup', 69, False, active=racing)
                files['transitive'].write_text('task value() -> int { give back 22 }\n', encoding='utf-8')
                mutate = racing | {'FREAK_FRESHNESS_EDIT': str(files['transitive']),
                                   'FREAK_FRESHNESS_BODY': 'task value() -> int { give back 23 }\n'}
                invoke('transitive-edit-during-native-build', None, None, active=mutate)
                assert not cache.exists()
                assert files['transitive'].read_bytes() == mutate['FREAK_FRESHNESS_BODY'].encode()
                assert Path(racing['FREAK_FRESHNESS_LOG']).read_bytes() == b'native mutation completed\n'
                code, output = run(f'{backend}:immutable-build-snapshot-control', [str(binary)], root, env)
                assert code == 0 and output == b'PKG_RUN=72\n', output
                invoke('racing-build-recovery', 75, False, active=racing)
                invoke('recovered-cache-hit', 75, True, active=racing)

                # An enclosing manifest can disappear after initial admission;
                # the final decision must clear that graph, not reuse its nodes.
                files['entry'].write_text('task main() { say "PKG_RUN=7" }\n', encoding='utf-8')
                manifest_bytes = files['app'].read_bytes()
                drop_manifest = racing | {'FREAK_FRESHNESS_EDIT': str(files['app']), 'FREAK_FRESHNESS_BODY': ''}
                invoke('manifest-removed-during-native-build', None, None, active=drop_manifest)
                assert not files['app'].exists() and not cache.exists()
                invoke('standalone-after-manifest-removal', 7, False, active=racing, source=files['entry'])
                invoke('standalone-cache-hit', 7, True, active=racing, source=files['entry'])
                files['app'].write_bytes(manifest_bytes)
                invoke('manifest-reintroduced', 7, False, active=racing)

            report['payload_after'] = {path.relative_to(home).as_posix(): sha(path) for path in home.rglob('*') if path.is_file()}
            assert report['payload_before'] == report['payload_after']
        report['inputs_after'] = {name: sha(Path(name)) for name in inputs}
        assert inputs == report['inputs_after']
        report['status'] = 'PASS'
        report['residual_limits'] = 'Concurrent writers are detected at revalidation boundaries; executable launch after the final check is not serialized. Only selected declared graph inputs are compiler authorities.'
    except BaseException as error:
        report.update(status='FAIL', error=repr(error))
        raise
    finally:
        save()
    print('Public run graph freshness: PASS', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
