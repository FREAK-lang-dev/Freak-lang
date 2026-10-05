#!/usr/bin/env python3
"""Verify a supplied installed native V3.5 bootstrap and its separate V4 preview.

The candidate is never rebuilt here. Python is the independent test driver;
compiled traps prove the successful installed route cannot invoke Python.
--source must contain the final frozen bootstrap.toml and byte inventory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time

WRAPPER = r'''#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <windows.h>
#include <shellapi.h>
#include <process.h>
#else
#include <unistd.h>
#endif
int main(int argc, char **argv) {
#ifdef _WIN32
    int count; wchar_t **wide = CommandLineToArgvW(GetCommandLineW(), &count);
    if (!wide) return 90;
    argc=count; argv=calloc((size_t)argc+1,sizeof(char*));
    for(int i=0;i<argc;i++) { int n=WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,wide[i],-1,NULL,0,NULL,NULL);
        argv[i]=malloc((size_t)n); if(!argv[i] || !WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,wide[i],-1,argv[i],n,NULL,NULL))return 91; }
#endif
    const char *log=getenv("FREAK_BOOTSTRAP_NATIVE_LOG");
    if(!log)return 92;
    FILE *file=fopen(log,"ab"); if(!file)return 93;
    fprintf(file,"%s\n",argv[0]); fclose(file);
    if(strstr(argv[0],"python")) return 97;
    const char *mode=getenv("FREAK_BOOTSTRAP_NATIVE_MODE");
    if(argc>2 && mode && strcmp(mode,"fail-link")==0) { fputc(0,stderr);fputc(255,stderr);return 43; }
    if(argc>2 && mode && strcmp(mode,"slow-link")==0) {
        const char *ready=getenv("FREAK_BOOTSTRAP_NATIVE_READY");
        if(ready){file=fopen(ready,"wb");if(file){fputs("ready",file);fclose(file);}}
#ifdef _WIN32
        Sleep(60000);
#else
        sleep(60);
#endif
    }
#ifdef _WIN32
    DWORD size=GetEnvironmentVariableW(L"FREAK_BOOTSTRAP_NATIVE_CLANG",NULL,0);
    wchar_t *compiler=calloc(size,sizeof(wchar_t));
    if(!size||!compiler||!GetEnvironmentVariableW(L"FREAK_BOOTSTRAP_NATIVE_CLANG",compiler,size))return 94;
    wide[0]=compiler;return (int)_wspawnv(_P_WAIT,compiler,(const wchar_t *const *)wide);
#else
    const char *compiler=getenv("FREAK_BOOTSTRAP_NATIVE_CLANG");if(!compiler)return 94;
    argv[0]=(char*)compiler;execv(compiler,argv);return 95;
#endif
}
'''
PROGRAM = 'task main() -> int {\n    say "native-v4"\n    give back 42\n}\n'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(source: Path) -> list[tuple[str, str, str]]:
    lines = (source / 'bootstrap.lock').read_text(encoding='utf-8').splitlines()
    assert lines[0] == 'FREAK-V4-BOOTSTRAP-LOCK-1' and len(lines[1].split()[1]) == 40, 'source has no frozen bootstrap lock'
    records = [tuple(line.split(' ', 2)) for line in lines[2:] if line]
    assert len(records) == 28, records
    for role, expected, relative in records:
        assert role in ('source_order', 'source', 'entry', 'metadata') and digest(source / relative) == expected, relative
    return records


def copy_source(original: Path, destination: Path, records: list[tuple[str, str, str]]) -> None:
    for _, _, relative in records:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original / relative, target)
    shutil.copy2(original / 'bootstrap.lock', destination / 'bootstrap.lock')


def rewrite_lock(source: Path, relative: str) -> None:
    lock = source / 'bootstrap.lock'
    lines = lock.read_text(encoding='utf-8').splitlines()
    for index, line in enumerate(lines[2:], 2):
        role, _, path = line.split(' ', 2)
        if path == relative:
            lines[index] = f'{role} {digest(source / path)} {path}'
    lock.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def bootstrap(candidate: Path, source: Path, output: Path, env: dict[str, str], *, locked: bool = True) -> subprocess.CompletedProcess[bytes]:
    command = [str(candidate), 'bootstrap', '--v4', '--source=' + str(source), '--output=' + str(output)]
    if locked:
        command.append('--locked')
    return subprocess.run(command, cwd=source.parent, env=env, capture_output=True, timeout=360)


def failed(process: subprocess.CompletedProcess[bytes], output: Path, parent: Path, *, stage_cleanup: bool = True) -> None:
    assert process.returncode != 0 and (process.stdout or process.stderr), process
    assert not output.exists(), (output, process.stdout, process.stderr)
    if stage_cleanup:
        assert not list(parent.glob('.freak-v4-bootstrap*')), list(parent.iterdir())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--clang', required=True, type=Path)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--source', type=Path)
    parser.add_argument('--entry-probe', action='store_true', help='mark focused native entry scope; does not establish production CLI parser')
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    candidate, clang, repo = args.candidate.resolve(strict=True), args.clang.resolve(strict=True), args.repo.resolve(strict=True)
    source = (args.source or repo / 'src/compiler/v4').resolve(strict=True)
    records = inventory(source)
    checks: list[str] = []
    limitations: list[str] = []
    with tempfile.TemporaryDirectory(prefix='freak-v35-bootstrap-') as temporary:
        root = Path(temporary).resolve()
        # Hostile paths are real arguments, including quotes, Unicode and metacharacters.
        payload = root / "installed é 日本 ' $ &"
        shutil.copytree(repo / 'freakc/runtime', payload / 'runtime')
        vendor = repo / 'third_party/llhttp'
        if vendor.exists():
            shutil.copytree(vendor, payload / 'runtime/third_party/llhttp', dirs_exist_ok=True)
        shutil.copytree(repo / 'std', payload / 'std')
        installed = payload / ('freak.exe' if os.name == 'nt' else 'freak')
        shutil.copy2(candidate, installed)
        stable_hash = digest(installed)
        tools = root / 'native-tools'
        tools.mkdir()
        wrapper_source = root / 'native-wrapper.c'
        wrapper_source.write_text(WRAPPER, encoding='utf-8')
        wrapper = tools / ('clang-wrapper.exe' if os.name == 'nt' else "clang-wrapper é ' $ &")
        command = [str(clang), '-O0', str(wrapper_source), '-o', str(wrapper)]
        if os.name == 'nt':
            command.append('-lshell32')
        built = subprocess.run(command, capture_output=True, timeout=60)
        assert built.returncode == 0, built.stderr
        for name in ('python', 'python3'):
            shutil.copy2(wrapper, tools / (name + '.exe' if os.name == 'nt' else name))
        env = {**os.environ, 'FREAK_HOME': str(payload), 'FREAK_CLANG': str(wrapper),
               'FREAK_BOOTSTRAP_NATIVE_CLANG': str(clang), 'FREAK_BOOTSTRAP_NATIVE_LOG': str(root / 'native.log')}
        # Keep SDK/system executable discovery but intercept every Python basename.
        env['PATH'] = str(tools) + os.pathsep + env.get('PATH', '')
        selected = root / "source é 日本 ' $ &"
        copy_source(source, selected, records)
        output_parent = root / "preview é 日本 ' $ &"
        output_parent.mkdir()
        output = output_parent / 'bundle'
        result = bootstrap(installed, selected, output, env)
        if result.returncode != 0:
            if args.evidence:
                args.evidence.parent.mkdir(parents=True, exist_ok=True)
                args.evidence.with_suffix('.stdout').write_bytes(result.stdout)
                args.evidence.with_suffix('.stderr').write_bytes(result.stderr)
            raise AssertionError((result.returncode, result.stdout[-4000:], result.stderr[-4000:]))
        assert output.is_dir(), output
        assert not list(output_parent.glob('.freak-v4-bootstrap*'))
        report = json.loads((output / 'bootstrap-report.json').read_text(encoding='utf-8'))
        assert report['status'] == 'verified' and report['builder_sha256'] == stable_hash
        assert report['source_inventory'] == 'byte-verified'
        assert report['source_commit'] == (selected / 'bootstrap.lock').read_text().splitlines()[1].split()[1]
        assert report['source_input_sha256'] and report['runtime_inventory_sha256']
        assert report['verification'] == ['native-identity', 'query-store-invalidation', 'scalar-stdio', 'task-arithmetic-branch', 'preview-version', 'preview-check']
        assert digest(installed) == stable_hash, 'stable compiler was replaced'
        preview = output / ('freak-v4.exe' if os.name == 'nt' else 'freak-v4')
        engine = output / ('freak-v4-engine.exe' if os.name == 'nt' else 'freak-v4-engine')
        assert digest(preview) == report['launcher_sha256'] and digest(engine) == report['engine_sha256']
        checks.append('installed native bootstrap, private runtime, identity/query/corpus, stable binary preservation')
        # Relocation and a contradictory FREAK_HOME cannot redirect the private payload.
        relocated = root / "relocated é 日本 ' $ &"
        output.rename(relocated)
        preview = relocated / preview.name
        engine = relocated / engine.name
        contradictory = {**env, 'FREAK_HOME': str(root / 'absent-payload')}
        version = subprocess.run([preview, '--version'], cwd=root, env=contradictory, capture_output=True, timeout=30)
        assert version.returncode == 0 and stable_hash.encode() in version.stdout and report['source_input_sha256'].encode() in version.stdout, version
        program = root / "program é 日本 ' $ &.fk"
        program.write_text(PROGRAM, encoding='utf-8')
        for action in ('check', 'emit', 'build'):
            destination = root / ('compiled.exe' if os.name == 'nt' else 'compiled') if action == 'build' else root / 'emitted.ll'
            command = [str(preview), action, str(program)]
            if action != 'check':
                command.append('--output=' + str(destination))
            process = subprocess.run(command, cwd=root, env=contradictory, capture_output=True, timeout=180)
            assert process.returncode == 0, (action, process.stdout, process.stderr)
            if action == 'emit':
                module = destination.read_bytes()
                assert b'define i32 @main' in module and b'@@V4-MODULE' not in module
            if action == 'build':
                executed = subprocess.run([destination], cwd=root, env=contradictory, capture_output=True, timeout=30)
                assert executed.returncode == 42 and executed.stdout == b'native-v4\n' and not executed.stderr, executed
        checks.append('relocated preview version/check/emit/build and actual native program execution')
        # Public preview error contracts include stale-output invalidation and aliases.
        program.write_text('task main() -> int { pilot broken = }\n', encoding='utf-8')
        stale = root / 'stale.ll'
        stale.write_text('prior-success')
        rejected = subprocess.run([preview, 'emit', program, '--output=' + str(stale)], cwd=root, env=contradictory, capture_output=True, timeout=120)
        assert rejected.returncode != 0 and not stale.exists(), rejected
        before = program.read_bytes()
        alias = subprocess.run([preview, 'emit', program, '--output=' + str(program)], cwd=root, env=contradictory, capture_output=True, timeout=30)
        assert alias.returncode != 0 and program.read_bytes() == before
        checks.append('preview diagnostics, nonzero status, stale invalidation, source alias protection')
        # Corrupted private payload is refused before a source can execute.
        runtime_file = relocated / 'runtime/freak_v4_word_runtime.c'
        prior = runtime_file.read_bytes()
        runtime_file.write_bytes(prior + b'\ncorrupt\n')
        corrupt = subprocess.run([preview, '--version'], env=contradictory, capture_output=True, timeout=30)
        assert corrupt.returncode != 0 and b'hash mismatch' in corrupt.stdout, corrupt
        runtime_file.write_bytes(prior)
        prior = engine.read_bytes()
        engine.write_bytes(prior + b'corrupt')
        corrupt = subprocess.run([preview, '--version'], env=contradictory, capture_output=True, timeout=30)
        assert corrupt.returncode != 0 and b'hash mismatch' in corrupt.stdout, corrupt
        engine.write_bytes(prior)
        checks.append('corrupted engine and private runtime byte inventory refused')
        # Frozen source mutations fail before creating an owned stage.
        crate = next(path for role, _, path in records if role == 'source')
        original = (selected / crate).read_bytes()
        (selected / crate).write_bytes(original + b'\n-- edited\n')
        rejected = bootstrap(installed, selected, output_parent / 'edited', env)
        failed(rejected, output_parent / 'edited', output_parent)
        assert b'byte inventory mismatch' in rejected.stdout
        (selected / crate).write_bytes(original)
        # A development syntax failure must preserve its original source location.
        (selected / crate).write_bytes(original + b'\ntask bad_bootstrap( {\n')
        rejected = bootstrap(installed, selected, output_parent / 'syntax', env, locked=False)
        failed(rejected, output_parent / 'syntax', output_parent)
        assert (str(selected / crate).encode() in rejected.stdout or str(selected / crate).encode() in rejected.stderr), rejected
        (selected / crate).write_bytes(original)
        checks.append('frozen source mutation and original-file syntax diagnostics with owned cleanup')
        for mode in ('fail-link',):
            rejected = bootstrap(installed, selected, output_parent / mode, {**env, 'FREAK_BOOTSTRAP_NATIVE_MODE': mode})
            failed(rejected, output_parent / mode, output_parent)
        missing = bootstrap(installed, selected, output_parent / 'missing-tool', {**env, 'FREAK_CLANG': str(root / 'not-a-tool')})
        failed(missing, output_parent / 'missing-tool', output_parent)
        marker = payload / 'runtime/freak_abi'
        prior = marker.read_bytes()
        marker.write_text('wrong-abi\n')
        rejected = bootstrap(installed, selected, output_parent / 'bad-runtime', env)
        failed(rejected, output_parent / 'bad-runtime', output_parent)
        marker.write_bytes(prior)
        checks.append('binary failed link, authoritative missing tool, bad runtime marker; no published output')
        prior_manifest = (selected / 'bootstrap.toml').read_bytes()
        (selected / 'bootstrap.toml').write_bytes(prior_manifest.replace(b'v4-host-bootstrap-v1', b'implicit-profile'))
        rewrite_lock(selected, 'bootstrap.toml')
        rejected = bootstrap(installed, selected, output_parent / 'profile', env)
        failed(rejected, output_parent / 'profile', output_parent)
        (selected / 'bootstrap.toml').write_bytes(prior_manifest)
        shutil.copy2(source / 'bootstrap.lock', selected / 'bootstrap.lock')
        source_hashes = {relative: digest(selected / relative) for _, _, relative in records}
        rejected = bootstrap(installed, selected, selected, env)
        assert rejected.returncode != 0 and {relative: digest(selected / relative) for _, _, relative in records} == source_hashes
        existing = output_parent / 'existing'
        existing.mkdir()
        (existing / 'prior').write_text('prior')
        rejected = bootstrap(installed, selected, existing, env)
        assert rejected.returncode != 0 and (existing / 'prior').read_text() == 'prior'
        checks.append('explicit compatibility required and source/existing-output aliases preserve bytes')
        # Normal SIGTERM is a failed attempt; a killed owner cannot publish success.
        ready = root / 'slow-ready'
        interrupted_output = output_parent / 'interrupted'
        interrupted_env = {**env, 'FREAK_BOOTSTRAP_NATIVE_MODE': 'slow-link', 'FREAK_BOOTSTRAP_NATIVE_READY': str(ready)}
        command = [str(installed), 'bootstrap', '--v4', '--source=' + str(selected), '--output=' + str(interrupted_output), '--locked']
        process = subprocess.Popen(command, cwd=root, env=interrupted_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        deadline = time.monotonic() + 120
        while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(.02)
        assert ready.exists(), process.communicate(timeout=5)
        process.terminate()
        stdout, stderr = process.communicate(timeout=30)
        assert process.returncode != 0 and not interrupted_output.exists()
        retained = list(output_parent.glob('.freak-v4-bootstrap*'))
        assert all(not (path / 'bootstrap-report.json').exists() for path in retained), retained
        if retained:
            limitations.append('Abrupt owner termination leaves an unpublished private stage; its success report is absent and it is never reused.')
        checks.append('interrupted native link exits nonzero and publishes no output/success report')
        log = (root / 'native.log').read_text(encoding='utf-8')
        assert 'python' not in log.lower(), log
        assert digest(installed) == stable_hash
        checks.append('compiled Python traps unused; stable V3 binary unchanged')
    report = {'status': 'pass', 'candidate_sha256': digest(candidate), 'clang_sha256': digest(clang),
              'scope': 'focused native orchestration entry' if args.entry_probe else 'installed public native CLI',
              'checks': checks, 'limitations': limitations}
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(report, indent=2) + '\n')
    print(f'PASS native bootstrap/preview {len(checks)} contract groups')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
