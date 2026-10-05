#!/usr/bin/env python3
"""Exercise project tests through a supplied native V3.5 CLI candidate.

This harness builds only a small native process fixture. It never rebuilds a
compiler or substitutes a Python compiler/project-test implementation. Candidate
and --repo payload must describe the same recorded revision.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time


HELPER = r'''#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <windows.h>
#include <process.h>
#include <io.h>
#include <fcntl.h>
#else
#include <unistd.h>
#include <signal.h>
#include <time.h>
#endif
static long process_id(void) {
#ifdef _WIN32
    return (long)_getpid();
#else
    return (long)getpid();
#endif
}
static void delay(unsigned int milliseconds) {
#ifdef _WIN32
    Sleep(milliseconds);
#else
    struct timespec duration = {milliseconds / 1000, (long)(milliseconds % 1000) * 1000000};
    while (nanosleep(&duration, &duration) != 0) {}
#endif
}
static void event(const char *kind) {
    const char *path = getenv(strcmp(kind, "python_used") == 0
                              ? "FREAK_V35_RUNNER_PYTHON_LOG" : "FREAK_V35_RUNNER_EVENTS");
    if (!path) exit(91);
#ifdef _WIN32
    HANDLE file = CreateFileA(path, FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE,
                             NULL, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE) exit(92);
    char line[80]; DWORD written;
    int length = snprintf(line, sizeof line, "%s %ld\n", kind, process_id());
    if (!WriteFile(file, line, (DWORD)length, &written, NULL) || written != (DWORD)length) exit(93);
    CloseHandle(file);
#else
    FILE *file = fopen(path, "ab");
    if (!file) exit(92);
    fprintf(file, "%s %ld\n", kind, process_id());
    if (fclose(file) != 0) exit(93);
#endif
}
int main(int argc, char **argv) {
    if (strstr(argv[0], "python")) { event("python_used"); return 97; }
    if (argc != 2) return 90;
#ifdef _WIN32
    _setmode(_fileno(stdout), _O_BINARY);
    _setmode(_fileno(stderr), _O_BINARY);
#endif
    if (strcmp(argv[1], "binary") == 0) {
        for (int value = 0; value < 256; value++) fputc(value, stdout);
        for (int value = 255; value >= 0; value--) fputc(value, stderr);
        return 0;
    }
    if (strcmp(argv[1], "flood") == 0) {
        event("start");
        char *bytes = malloc(196608);
        if (!bytes) return 94;
        memset(bytes, 'A', 196608); if (fwrite(bytes, 1, 196608, stdout) != 196608) return 95;
        memset(bytes, 'B', 196608); if (fwrite(bytes, 1, 196608, stderr) != 196608) return 96;
        fflush(stdout); fflush(stderr); free(bytes);
        delay(1000); event("stop"); return 0;
    }
    if (strcmp(argv[1], "nested_timeout") == 0) {
        event("start"); printf("PID=%ld\n", process_id()); fflush(stdout);
        delay(30000); event("stop"); return 0;
    }
    if (strcmp(argv[1], "exit") == 0) {
        fputs("child-out\n", stdout); fputs("child-err\n", stderr); return 23;
    }
#ifndef _WIN32
    if (strcmp(argv[1], "signal") == 0) {
        kill(getppid(), SIGTERM); return 0;
    }
#endif
    return 98;
}
'''


def helper_program(mode: str) -> str:
    return f'''task main() {{
    pilot job = process::command_new(process::env("FREAK_V35_RUNNER_HELPER"))
    process::command_arg(job, "{mode}")
    pilot state = process::command_run_inherit(job, 0)
    pilot code = process::command_exit_code(job)
    process::command_release(job)
    if state != 2 {{ process::exit(99) }}
    process::exit(code)
}}
'''


def project(root: Path, files: dict[str, str], *, declared: dict[str, str] | None,
            dependency: bool = False, library: bool = False) -> Path:
    root.mkdir(parents=True)
    manifest = ('[project]\nname = "runner_fixture"\nversion = "1.0.0"\n'
                f'kind = "{"lib" if library else "app"}"\n')
    if library:
        manifest += '[modules]\ncore = "src/core.fk"\n[exports]\nvalue = "core::value"\n'
        files = {**files, 'src/core.fk': 'task value() -> int { give back 7 }\n'}
    else:
        manifest += 'entry = "src/main.fk"\n'
        files = {**files, 'src/main.fk': 'task main() { say "APP ENTRY MUST NOT RUN" }\n'}
    if dependency:
        manifest += '[dependencies]\nhelper = { path = "../helper" }\n'
    if declared is not None:
        manifest += '[tests]\n'
        for name, path in declared.items():
            manifest += f'{name} = {json.dumps(path, ensure_ascii=False)}\n'
    for path, source in files.items():
        destination = root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source, encoding='utf-8')
    manifest_path = root / 'hangar.toml'
    manifest_path.write_text(manifest, encoding='utf-8')
    return manifest_path


def run_tests(freak: Path, manifest: Path, env: dict[str, str], backend: str, *,
              jobs: int = 1, timeout_ms: int = 30000, limit: int = 1048576,
              human: bool = False, extra: tuple[str, ...] = ()) -> tuple[subprocess.CompletedProcess[bytes], dict | None]:
    command = [str(freak), 'test', f'--manifest-path={manifest}', f'--{backend}',
               f'--jobs={jobs}', f'--timeout-ms={timeout_ms}', f'--stdout-limit={limit}',
               f'--stderr-limit={limit}', *extra]
    if not human:
        command.append('--json')
    # An unrelated CWD must never supply an undeclared source/package.
    process = subprocess.run(command, cwd=manifest.parent.parent, env=env,
                             capture_output=True, timeout=180, check=False)
    if human:
        return process, None
    assert not process.stderr, (command, process.returncode, process.stdout, process.stderr)
    try:
        report = json.loads(process.stdout)
    except (ValueError, UnicodeError) as error:
        raise AssertionError((command, process.returncode, process.stdout, process.stderr)) from error
    assert report['schema'] == 1 and isinstance(report['cases'], list), report
    for case in report['cases']:
        for phase in ('build', 'run'):
            child = case[phase]
            if child is None:
                continue
            assert child['encoding'] == 'hex', child
            assert len(bytes.fromhex(child['stdout_hex'])) == child['stdout_bytes'], child
            assert len(bytes.fromhex(child['stderr_hex'])) == child['stderr_bytes'], child
            assert isinstance(child['process_status'], int), child
            assert child['timed_out'] == (child['process_status'] == 5), child
    return process, report


def assert_pass(process: subprocess.CompletedProcess[bytes], report: dict, names: list[str]) -> None:
    assert process.returncode == 0 and report['error'] == '', (process, report)
    assert [case['name'] for case in report['cases']] == names, report
    assert report['summary'] == {'total': len(names), 'passed': len(names), 'failed': 0}, report
    for case in report['cases']:
        assert case['status'] == 'passed', case
        assert case['build']['process_status'] == 2 and case['build']['exit_code'] == 0, case
        assert case['run']['process_status'] == 2 and case['run']['exit_code'] == 0, case
        assert b'APP ENTRY MUST NOT RUN' not in bytes.fromhex(case['run']['stdout_hex']), case


def process_alive(pid: int) -> bool:
    if os.name == 'nt':
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.restype = ctypes.c_void_p
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        status = ctypes.c_ulong()
        try:
            assert kernel.GetExitCodeProcess(ctypes.c_void_p(handle), ctypes.byref(status))
            return status.value == 259
        finally:
            kernel.CloseHandle(ctypes.c_void_p(handle))
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    # A dead child awaiting container-init reaping owns no running resources.
    stat = Path(f'/proc/{pid}/stat')
    if stat.is_file() and stat.read_text().rsplit(') ', 1)[1].startswith('Z '):
        return False
    return True


def stop_recorded_process(pid: int) -> None:
    if not process_alive(pid):
        return
    if os.name == 'nt':
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.restype = ctypes.c_void_p
        handle = kernel.OpenProcess(1, False, pid)
        if handle:
            kernel.TerminateProcess(ctypes.c_void_p(handle), 137)
            kernel.CloseHandle(ctypes.c_void_p(handle))
    else:
        os.kill(pid, signal.SIGKILL)


def check_backend(freak: Path, root: Path, env: dict[str, str], backend: str) -> list[str]:
    checks = []
    suite = root / backend
    suite.mkdir()
    helper = suite / 'helper'
    helper.mkdir()
    helper.joinpath('hangar.toml').write_text(
        '[project]\nname = "helper"\nversion = "1.0.0"\nkind = "lib"\n'
        '[modules]\ncore = "src/core.fk"\n[exports]\napi = "core::answer"\n', encoding='utf-8')
    helper.joinpath('src').mkdir()
    dependency_source = helper / 'src/core.fk'
    dependency_source.write_text('task answer() -> int { give back 42 }\n', encoding='utf-8')
    assertions = ('use std::test::{test_assert, test_assert_int, test_assert_word}\n'
                  'use helper::{api}\n'
                  'task main() { test_assert("truth", true); test_assert_int("dependency", 42, api()); '
                  'test_assert_word("text", "hello", "hello"); say "named pass" }\n')
    manifest = project(suite / 'declared é & literal', {'tests/pass.fk': assertions},
                       declared={'declared': 'tests/pass.fk'}, dependency=True, library=True)
    process, report = run_tests(freak, manifest, env, backend)
    assert_pass(process, report, ['declared'])
    assert bytes.fromhex(report['cases'][0]['run']['stdout_hex']) == b'named pass\n', report
    checks.append('declared-library-root-and-direct-dependency')

    fallback = project(suite / 'fallback', {'tests/é &_test.fk':
        'use std::test::{test_assert}\ntask main() { test_assert("fallback", true) }\n'}, declared=None)
    process, report = run_tests(freak, fallback, env, backend)
    assert_pass(process, report, ['é &_test'])
    checks.append('structured-fallback-unicode-path')

    binary = project(suite / 'binary', {'tests/bytes.fk': helper_program('binary')},
                     declared={'bytes': 'tests/bytes.fk'})
    process, report = run_tests(freak, binary, env, backend)
    assert_pass(process, report, ['bytes'])
    captured = report['cases'][0]['run']
    assert bytes.fromhex(captured['stdout_hex']) == bytes(range(256)), captured
    assert bytes.fromhex(captured['stderr_hex']) == bytes(reversed(range(256))), captured
    process, _ = run_tests(freak, binary, env, backend, human=True)
    assert process.returncode == 0 and b'stdout (hex): 00010203' in process.stdout, process
    checks.append('binary-both-streams-and-human-fallback')

    events = Path(env['FREAK_V35_RUNNER_EVENTS'])
    events.unlink(missing_ok=True)
    declared = {name: f'tests/{name}.fk' for name in ('zeta', 'delta', 'beta', 'alpha')}
    parallel = project(suite / 'parallel', {path: helper_program('flood') for path in declared.values()},
                       declared=declared)
    process, report = run_tests(freak, parallel, env, backend, jobs=4)
    assert_pass(process, report, ['alpha', 'beta', 'delta', 'zeta'])
    for case in report['cases']:
        assert bytes.fromhex(case['run']['stdout_hex']) == b'A' * 196608, case
        assert bytes.fromhex(case['run']['stderr_hex']) == b'B' * 196608, case
    active = set()
    peak = 0
    for line in events.read_text().splitlines():
        kind, pid_text = line.split()
        pid = int(pid_text)
        if kind == 'start':
            assert pid not in active, line
            active.add(pid)
            peak = max(peak, len(active))
        elif kind == 'stop':
            assert pid in active, line
            active.remove(pid)
        else:
            raise AssertionError(line)
    assert not active and 2 <= peak <= 4, (peak, active, events.read_text())
    checks.append('parallel-fair-capture-bounded-jobs-deterministic-order')

    failures = project(suite / 'failures', {
        'tests/assert.fk': 'use std::test::{test_assert_int}\ntask main() { test_assert_int("named mismatch", 1, 2) }\n',
        'tests/exit.fk': helper_program('exit'),
        'tests/compile.fk': 'task main() { say undefined_fixture_name }\n',
    }, declared={'named': 'tests/assert.fk', 'exit': 'tests/exit.fk', 'compile': 'tests/compile.fk'})
    process, report = run_tests(freak, failures, env, backend, jobs=3)
    assert process.returncode == 1 and report['summary'] == {'total': 3, 'passed': 0, 'failed': 3}, report
    cases = {case['name']: case for case in report['cases']}
    assert cases['compile']['status'] == 'build_failed' and cases['compile']['run'] is None, cases
    assert cases['compile']['build']['exit_code'] != 0, cases
    assert cases['exit']['run']['exit_code'] == 23, cases
    assert bytes.fromhex(cases['exit']['run']['stdout_hex']) == b'child-out\n', cases
    assert bytes.fromhex(cases['exit']['run']['stderr_hex']) == b'child-err\n', cases
    assert cases['named']['run']['exit_code'] == 1, cases
    assert b'TEST FAILED [named mismatch]' in bytes.fromhex(cases['named']['run']['stdout_hex']), cases
    checks.append('named-failure-real-exit-and-compile-failure')

    timeout = project(suite / 'timeout', {'tests/hang.fk': 'task main() { repeat until false {} }\n'},
                      declared={'hang': 'tests/hang.fk'})
    process, report = run_tests(freak, timeout, env, backend, timeout_ms=5000)
    child = report['cases'][0]['run']
    assert process.returncode == 1 and child is not None and child['process_status'] == 5, report
    assert child['exit_code'] is None and child['timed_out'], child
    checks.append('deadline-on-running-test')

    events.unlink(missing_ok=True)
    nested = project(suite / 'nested-timeout', {'tests/hang.fk': helper_program('nested_timeout')},
                     declared={'nested': 'tests/hang.fk'})
    started = time.monotonic()
    try:
        process, report = run_tests(freak, nested, env, backend, timeout_ms=5000)
        assert time.monotonic() - started < 15, 'outer deadline waited for escaped nested helper'
        child = report['cases'][0]['run']
        assert process.returncode == 1 and child is not None and child['process_status'] == 5, report
        pids = [int(line.split()[1]) for line in events.read_text().splitlines() if line.startswith('start ')]
        assert len(pids) == 1, events.read_text()
        deadline = time.monotonic() + 2
        while process_alive(pids[0]) and time.monotonic() < deadline:
            time.sleep(0.01)
        assert not process_alive(pids[0]), 'outer deadline left a normal nested-ticket child alive'
    finally:
        if events.is_file():
            for line in events.read_text().splitlines():
                if line.startswith('start '):
                    stop_recorded_process(int(line.split()[1]))
    checks.append('nested-ticket-deadline-containment')

    overflow = project(suite / 'output-limit', {'tests/flood.fk':
        'task main() { repeat 50000 times { say "runner output limit" } }\n'},
        declared={'flood': 'tests/flood.fk'})
    process, report = run_tests(freak, overflow, env, backend, limit=4096)
    case = report['cases'][0]
    # A build may also reach this configured capture limit. Exercise a runtime
    # limit only after proving the child build passed under this bound.
    assert case['build']['exit_code'] == 0 and case['run'] is not None, case
    assert process.returncode == 1 and case['run']['process_status'] == 6, report
    assert case['run']['stdout_bytes'] <= 4096, case
    checks.append('runtime-output-limit')

    if os.name == 'posix':
        signaled = project(suite / 'signal', {'tests/signal.fk': helper_program('signal')},
                           declared={'signal': 'tests/signal.fk'})
        process, report = run_tests(freak, signaled, env, backend)
        child = report['cases'][0]['run']
        assert process.returncode == 1 and child['process_status'] == 4, report
        assert child['signal'] == signal.SIGTERM and child['exit_code'] is None, child
        checks.append('actual-posix-signal')

    mutation_source = ('use std::test::{test_assert_int}\nuse helper::{api}\n'
        'task main() { test_assert_int("frozen dependency", 42, api()); '
        'pilot write = fs::write_checked(process::env("FREAK_V35_RUNNER_MUTATION"), '
        '"task answer() -> int { give back 43 }\\n"); '
        'pilot success = fs::result_ok(write); fs::result_release(write); '
        'if not success { process::exit(91) } }\n')
    immutable = project(suite / 'snapshot', {'tests/a.fk': mutation_source, 'tests/b.fk': assertions},
                        declared={'a_mutate': 'tests/a.fk', 'b_frozen': 'tests/b.fk'}, dependency=True)
    mutation_env = {**env, 'FREAK_V35_RUNNER_MUTATION': str(dependency_source)}
    process, report = run_tests(freak, immutable, mutation_env, backend, jobs=1)
    assert process.returncode == 1 and report['cases'][0]['status'] == 'passed', report
    assert '43' in dependency_source.read_text(), 'mutation fixture did not run'
    assert report['cases'][1]['status'] == 'build_failed' and report['cases'][1]['run'] is None, report
    checks.append('single-immutable-graph-rejects-mid-suite-dependency-change')

    fallback_mutation = project(suite / 'fallback-snapshot', {
        'tests/a_mutate_test.fk': ('task main() { pilot write = fs::write_checked('
            'process::env("FREAK_V35_RUNNER_MUTATION"), "task main() { say 99 }\\n"); '
            'pilot success = fs::result_ok(write); fs::result_release(write); '
            'if not success { process::exit(91) } }\n'),
        'tests/b_frozen_test.fk': 'task main() { say 42 }\n',
    }, declared=None)
    changed_test = fallback_mutation.parent / 'tests/b_frozen_test.fk'
    mutation_env = {**env, 'FREAK_V35_RUNNER_MUTATION': str(changed_test)}
    process, report = run_tests(freak, fallback_mutation, mutation_env, backend, jobs=1)
    assert process.returncode == 1 and report['cases'][0]['status'] == 'passed', report
    assert '99' in changed_test.read_text(), 'fallback mutation fixture did not run'
    assert report['cases'][1]['status'] == 'build_failed' and report['cases'][1]['run'] is None, report
    checks.append('fallback-test-bytes-bound-to-single-snapshot')

    invalid = project(suite / 'empty-declared', {'tests/found_test.fk': 'task main() {}\n'}, declared={})
    process, report = run_tests(freak, invalid, env, backend)
    assert process.returncode == 1 and not report['cases'] and report['error'], report
    checks.append('empty-declaration-does-not-discover')
    for name, declaration in [('escape', '../outside.fk'), ('duplicate', 'tests/file.fk')]:
        invalid = project(suite / name, {'tests/file.fk': 'task main() {}\n'},
                          declared={'first': declaration, 'second': declaration} if name == 'duplicate'
                          else {'first': declaration})
        process, report = run_tests(freak, invalid, env, backend)
        assert process.returncode == 1 and not report['cases'] and report['error'], report
    checks.append('escape-and-duplicate-file-rejected')
    if os.name == 'posix':
        symlink = project(suite / 'symlink', {}, declared={'link': 'tests/link.fk'})
        symlink.parent.joinpath('tests').mkdir()
        symlink.parent.joinpath('tests/link.fk').symlink_to(timeout.parent / 'tests/hang.fk')
        process, report = run_tests(freak, symlink, env, backend)
        assert process.returncode == 1 and not report['cases'] and report['error'], report
        checks.append('symlink-source-rejected')
    for tree in suite.iterdir():
        if tree.is_dir():
            for source_dir in (tree / 'tests', tree / 'src'):
                if source_dir.is_dir():
                    assert not [path for path in source_dir.iterdir()
                                if path.suffix in ('.c', '.ll', '.o', '.obj', '.exe')], source_dir
    assert not list(root.glob('freak-tests-*')), 'owned output directory remained after tests'
    checks.append('owned-output-cleanup-and-no-source-sidecars')
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('freak', type=Path, help='fresh exact-source native candidate; never rebuilt')
    parser.add_argument('--clang', type=Path, required=True, help='actual native compiler for fixture only')
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--backend', choices=('both', 'c', 'llvm'), default='both')
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    freak, clang, repo = args.freak.resolve(strict=True), args.clang.resolve(strict=True), args.repo.resolve(strict=True)
    completed = {}
    with tempfile.TemporaryDirectory(prefix='freak-v35-native-tests-') as temporary:
        root = Path(temporary)
        home = root / 'payload'
        shutil.copytree(repo / 'freakc/runtime', home / 'runtime')
        shutil.copytree(repo / 'std', home / 'std')
        source = root / 'runner-helper.c'
        source.write_text(HELPER)
        helper = root / ('native helper.exe' if os.name == 'nt' else 'native helper')
        built = subprocess.run([str(clang), '-O0', str(source), '-o', str(helper)],
                               capture_output=True, timeout=60, check=False)
        assert built.returncode == 0, (built.stdout, built.stderr)
        blockers = root / 'blocked-python'
        blockers.mkdir()
        for name in (('python.exe', 'python3.exe') if os.name == 'nt' else ('python', 'python3')):
            shutil.copy2(helper, blockers / name)
        env = {name: value for name, value in os.environ.items() if not name.startswith('FREAK_V35_RUNNER_')}
        env.update(FREAK_HOME=str(home), FREAK_CLANG=str(clang), TMPDIR=str(root), TEMP=str(root), TMP=str(root),
                   FREAK_V35_RUNNER_HELPER=str(helper), FREAK_V35_RUNNER_EVENTS=str(root / 'events.log'),
                   FREAK_V35_RUNNER_PYTHON_LOG=str(root / 'python-used.log'),
                   PATH=str(blockers) + os.pathsep + env.get('PATH', ''))
        for backend in (('c', 'llvm') if args.backend == 'both' else (args.backend,)):
            completed[backend] = check_backend(freak, root, env, backend)
            print(f'PASS {backend}: {len(completed[backend])} native project-test contracts', flush=True)
        assert not root.joinpath('python-used.log').exists(), 'installed runner invoked Python'
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps({'status': 'pass', 'candidate_sha256': hashlib.sha256(freak.read_bytes()).hexdigest(),
                                            'host': sys.platform, 'checks': completed}, indent=2) + '\n')
    print('V3.5 native project tests: OK', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
