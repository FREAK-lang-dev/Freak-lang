#!/usr/bin/env python3
"""Verify exact native Clang launches and owned explicit build outputs.

The supplied candidate is never rebuilt. --entry-probe exercises the owned
setter/build functions through a recorded temporary native entry; it establishes
no public CLI flag-parsing or dependency-graph evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


WRAPPER = r'''#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <windows.h>
#include <shellapi.h>
#include <process.h>
#else
#include <unistd.h>
#endif
static void log_arguments(int argc, char **argv) {
    const char *path = getenv("FREAK_V35_BUILD_LOG");
    if (!path) exit(91);
    FILE *file = fopen(path, "ab"); if (!file) exit(92);
    fprintf(file, "BEGIN %d\n", argc);
    for (int index = 0; index < argc; index++) {
        const unsigned char *byte = (const unsigned char *)argv[index];
        while (*byte) fprintf(file, "%02x", *byte++);
        fputc('\n', file);
    }
    fputs("END\n", file); if (fclose(file) != 0) exit(93);
}
int main(int argc, char **argv) {
#ifdef _WIN32
    int count; wchar_t **wide = CommandLineToArgvW(GetCommandLineW(), &count);
    if (!wide) return 94;
    argc = count; argv = calloc((size_t)argc + 1, sizeof(char *));
    if (!argv) return 95;
    for (int index = 0; index < argc; index++) {
        int size = WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, wide[index], -1, NULL, 0, NULL, NULL);
        argv[index] = malloc((size_t)size);
        if (!argv[index] || !WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, wide[index], -1, argv[index], size, NULL, NULL)) return 96;
    }
#endif
    log_arguments(argc, argv);
    const char *version = getenv("FREAK_V35_BUILD_VERSION");
    if (argc == 2 && strcmp(argv[1], "--version") == 0 && version) { puts(version); return 0; }
    const char *mode = getenv("FREAK_V35_BUILD_MODE");
    if (argc > 2 && mode) {
        if (strcmp(mode, "missing_output") == 0) return 0;
        if (strcmp(mode, "binary_failure") == 0) {
            fputc(0, stdout); fputc(255, stdout); fputc(0, stderr); fputc(128, stderr); return 43;
        }
        if (strcmp(mode, "partial_failure") == 0) {
            for (int index = 1; index + 1 < argc; index++) if (strcmp(argv[index], "-o") == 0) {
#ifdef _WIN32
                FILE *file = _wfopen(wide[index + 1], L"wb");
#else
                FILE *file = fopen(argv[index + 1], "wb");
#endif
                if (!file) return 97;
                fputs("untrusted partial compiler output", file); fclose(file);
            }
            return 42;
        }
    }
#ifdef _WIN32
    DWORD size = GetEnvironmentVariableW(L"FREAK_V35_BUILD_REAL_CLANG", NULL, 0);
    wchar_t *compiler = calloc(size, sizeof(wchar_t));
    if (!size || !compiler || !GetEnvironmentVariableW(L"FREAK_V35_BUILD_REAL_CLANG", compiler, size)) return 98;
    wide[0] = compiler;
    return (int)_wspawnv(_P_WAIT, compiler, (const wchar_t *const *)wide);
#else
    const char *compiler = getenv("FREAK_V35_BUILD_REAL_CLANG"); if (!compiler) return 98;
    argv[0] = (char *)compiler; execv(compiler, argv); perror("execv native Clang"); return 99;
#endif
}
'''

PROGRAM = 'task main() { say "NATIVE_BUILD_OK é 日本" }\n'


def logs(path: Path) -> list[list[str]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding='ascii').splitlines()
    records = []
    index = 0
    while index < len(lines):
        header = lines[index].split()
        assert header[0] == 'BEGIN', lines[index]
        count = int(header[1])
        args = [bytes.fromhex(line).decode('utf-8') for line in lines[index + 1:index + 1 + count]]
        assert lines[index + count + 1] == 'END', lines[index:]
        records.append(args)
        index += count + 2
    return records


def run_build(candidate: Path, source: Path, output: str, backend: str, opt: int, env: dict[str, str], *,
              entry_probe: bool, lto: str = 'off', cross: str = '', extra: tuple[str, ...] = ()) -> subprocess.CompletedProcess[bytes]:
    if entry_probe:
        assert not extra, 'entry probe does not establish flag parser behavior'
        command = [str(candidate), str(source), output, backend, str(opt), lto, cross]
    else:
        command = [str(candidate), 'build', str(source), f'--{backend}', f'--opt={opt}', f'--lto={lto}']
        if output:
            command.append('--output=' + output)
        if cross:
            command.append('--target=' + cross)
        command.extend(extra)
    return subprocess.run(command, cwd=source.parent, env=env, capture_output=True, timeout=180, check=False)


def assert_failed(process: subprocess.CompletedProcess[bytes], output: Path) -> None:
    assert process.returncode != 0, (process.stdout, process.stderr)
    assert not output.exists() and not Path(str(output) + '.freak-run-cache').exists(), (output, process.stdout, process.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path, help='native candidate; no rebuild or bootstrap fallback')
    parser.add_argument('--clang', type=Path, required=True)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--entry-probe', action='store_true')
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    candidate, clang, repo = args.candidate.resolve(strict=True), args.clang.resolve(strict=True), args.repo.resolve(strict=True)
    checks = []
    limitations = []
    with tempfile.TemporaryDirectory(prefix='freak-v35-build-') as temporary:
        root = Path(temporary).resolve()
        payload = root / 'payload é & %LITERAL%'
        shutil.copytree(repo / 'freakc/runtime', payload / 'runtime')
        shutil.copytree(repo / 'std', payload / 'std')
        wrapper_source = root / 'clang-wrapper.c'
        wrapper_source.write_text(WRAPPER, encoding='utf-8')
        wrapper = root / ('clang é & literal.exe' if os.name == 'nt' else "clang é ' $ & literal")
        command = [str(clang), '-O0', str(wrapper_source), '-o', str(wrapper)]
        if os.name == 'nt':
            command.append('-lshell32')
        compiled = subprocess.run(command, capture_output=True, timeout=60, check=False)
        assert compiled.returncode == 0, (compiled.stdout, compiled.stderr)
        logfile = root / 'driver-arguments.log'
        env = {name: value for name, value in os.environ.items() if not name.startswith('FREAK_V35_BUILD_')}
        env.update(FREAK_HOME=str(payload), FREAK_CLANG=str(wrapper), FREAK_V35_BUILD_REAL_CLANG=str(clang),
                   FREAK_V35_BUILD_LOG=str(logfile), TMPDIR=str(root), TEMP=str(root), TMP=str(root))
        project = root / 'source project é & %LITERAL%'
        project.mkdir()
        name = 'input é & %LITERAL%.fk' if os.name == 'nt' else "input é '$(touch INJECTED)' ; $ &.fk"
        source = project / name
        source.write_text(PROGRAM, encoding='utf-8')
        outputs = root / 'owned outputs é & %LITERAL%'
        outputs.mkdir()
        for backend in ('c', 'llvm'):
            for opt in (0, 2, 3):
                logfile.unlink(missing_ok=True)
                output = outputs / (f'{backend} O{opt}.exe' if os.name == 'nt' else f'{backend} O{opt}')
                process = run_build(candidate, source, str(output), backend, opt, env, entry_probe=args.entry_probe)
                assert process.returncode == 0 and output.is_file(), (backend, opt, process.stdout, process.stderr)
                executed = subprocess.run([str(output)], cwd=project, capture_output=True, timeout=10, check=False)
                assert executed.returncode == 0 and executed.stdout.decode('utf-8') == 'NATIVE_BUILD_OK é 日本\n', executed
                records = logs(logfile)
                compilation = [record for record in records if '-o' in record]
                assert len(compilation) == 1, records
                record = compilation[0]
                assert record[0] == str(wrapper), record
                assert record[record.index('-o') + 1] == str(output), record
                suffix = '.c' if backend == 'c' else '.ll'
                assert str(output) + suffix in record and '-O' + str(opt) in record, record
                assert record[record.index('-I') + 1] == str(payload / 'runtime'), record
                assert str(payload / 'runtime/freak_runtime.c') in record, record
                if backend == 'llvm':
                    assert str(payload / 'runtime/freak_llvm_runtime.c') in record, record
                assert source.read_text(encoding='utf-8') == PROGRAM
                assert not project.joinpath('INJECTED').exists(), 'shell interpreted a source path'
                assert not Path(str(source) + suffix).exists(), 'explicit output left an adjacent source sidecar'
                checks.append(f'{backend}-O{opt}-exact-argv-real-compile-execute')
                print('PASS', checks[-1], flush=True)

        lto_outputs = root / 'LTO outputs é & literal'
        lto_outputs.mkdir()
        for backend, lto in (('c', 'thin'), ('llvm', 'full')):
            logfile.unlink(missing_ok=True)
            output = lto_outputs / (f'{backend}-{lto}.exe' if os.name == 'nt' else f'{backend}-{lto}')
            process = run_build(candidate, source, str(output), backend, 2, env, entry_probe=args.entry_probe, lto=lto)
            assert process.returncode == 0 and output.is_file(), (backend, lto, process.stdout, process.stderr)
            executed = subprocess.run([str(output)], capture_output=True, timeout=10, check=False)
            assert executed.returncode == 0 and executed.stdout.decode('utf-8') == 'NATIVE_BUILD_OK é 日本\n', executed
            record = next(record for record in logs(logfile) if '-o' in record)
            assert ('-flto=thin' if lto == 'thin' else '-flto') in record, record
            assert ('-fuse-ld=ld' if os.sys.platform == 'darwin' else '-fuse-ld=lld') in record, record
            checks.append(f'{backend}-{lto}-preserves-lto-driver-policy')
            print('PASS', checks[-1], flush=True)

        # Some LLVM LLD releases expand '%' in the output parent's temporary
        # filename model. Classify that SDK behavior with a direct invocation;
        # FREAK must either preserve success or fail without a stale artifact.
        direct_source = root / 'direct-linker-probe.c'
        direct_source.write_text('int main(void) { return 0; }\n')
        direct_output = outputs / ('direct-lto.exe' if os.name == 'nt' else 'direct-lto')
        direct_flags = ['-flto=thin', '-fuse-ld=ld' if os.sys.platform == 'darwin' else '-fuse-ld=lld']
        direct = subprocess.run([str(clang), *direct_flags, str(direct_source), '-o', str(direct_output)],
                                capture_output=True, timeout=60, check=False)
        output = outputs / ('percent-lto.exe' if os.name == 'nt' else 'percent-lto')
        output.write_bytes(b'stale LTO executable')
        process = run_build(candidate, source, str(output), 'c', 2, env, entry_probe=args.entry_probe, lto='thin')
        if direct.returncode == 0:
            assert process.returncode == 0 and output.is_file(), (process.stdout, process.stderr)
            executed = subprocess.run([str(output)], capture_output=True, timeout=10, check=False)
            assert executed.returncode == 0 and executed.stdout.decode('utf-8') == 'NATIVE_BUILD_OK é 日本\n', executed
            checks.append('percent-output-lto-real-compile-execute')
        else:
            assert b'cannot open output file' in direct.stderr, direct
            assert_failed(process, output)
            assert b'cannot open output file' in process.stdout, process
            limitations.append({'scope': 'host Clang/LLD LTO output in percent-containing parent',
                                'direct_exit_code': direct.returncode,
                                'direct_stderr': direct.stderr.decode('utf-8', errors='backslashreplace')})
            checks.append('independent-percent-lld-failure-preserves-fail-closed-build')

        triple_probe = subprocess.run([str(clang), '-dumpmachine'], capture_output=True, text=True, timeout=10, check=False)
        assert triple_probe.returncode == 0, triple_probe
        host_triple = triple_probe.stdout.strip()
        logfile.unlink(missing_ok=True)
        output = outputs / ('host-target.exe' if os.name == 'nt' else 'host-target')
        process = run_build(candidate, source, str(output), 'c', 0, env, entry_probe=args.entry_probe, cross=host_triple)
        assert process.returncode == 0 and output.is_file(), (process.stdout, process.stderr)
        executed = subprocess.run([str(output)], capture_output=True, timeout=10, check=False)
        assert executed.returncode == 0 and executed.stdout.decode('utf-8') == 'NATIVE_BUILD_OK é 日本\n', executed
        record = next(record for record in logs(logfile) if '-o' in record)
        assert '--target=' + host_triple in record, record
        checks.append('explicit-host-target-single-argv-field')

        for mode in ('partial_failure', 'missing_output', 'binary_failure'):
            output = outputs / ('failure.exe' if os.name == 'nt' else 'failure')
            output.write_bytes(b'previous trusted binary')
            Path(str(output) + '.freak-run-cache').write_bytes(b'previous success proof')
            failed_env = {**env, 'FREAK_V35_BUILD_MODE': mode}
            process = run_build(candidate, source, str(output), 'c', 0, failed_env, entry_probe=args.entry_probe)
            assert_failed(process, output)
            if mode == 'binary_failure':
                assert b'binary output (hex): 00ff' in process.stdout and b'binary output (hex): 0080' in process.stdout, process
            checks.append('untrusted-output-' + mode)
            print('PASS', checks[-1], flush=True)

        for version in ('clang version 14.0.0', 'Apple clang version 14.0.0', 'mystery compiler 99'):
            logfile.unlink(missing_ok=True)
            output = outputs / ('old.exe' if os.name == 'nt' else 'old')
            output.write_bytes(b'stale binary')
            process = run_build(candidate, source, str(output), 'llvm', 0, {**env, 'FREAK_V35_BUILD_VERSION': version}, entry_probe=args.entry_probe)
            assert_failed(process, output)
            assert b'Minimum supported Clang' in process.stdout, process
            assert logs(logfile) and not any('-o' in record for record in logs(logfile)), logs(logfile)
        checks.append('minimum-vendor-floor-before-native-compile')

        output = outputs / ('override.exe' if os.name == 'nt' else 'override')
        output.write_bytes(b'stale binary')
        logfile.unlink(missing_ok=True)
        process = run_build(candidate, source, str(output), 'c', 0, {**env, 'FREAK_CLANG': str(root / 'missing authoritative compiler')}, entry_probe=args.entry_probe)
        assert_failed(process, output)
        assert b'Clang version probe failed' in process.stdout, process
        assert not logs(logfile), 'broken authoritative override fell back to installed Clang'
        checks.append('authoritative-missing-driver-no-fallback')
        if os.name == 'nt':
            script = root / 'unsupported compiler.cmd'
            script.write_text('@echo clang version 19.0.0\r\n@echo unexpected > AMBIENT_CMD_FALLBACK\r\n')
            output.write_bytes(b'stale binary')
            process = run_build(candidate, source, str(output), 'c', 0, {**env, 'FREAK_CLANG': str(script)}, entry_probe=args.entry_probe)
            assert_failed(process, output)
            assert b'Clang version probe failed' in process.stdout and not project.joinpath('AMBIENT_CMD_FALLBACK').exists(), process
            checks.append('cmd-override-unsupported-spawn-no-ambient-shell')

        for destination in (str(source), 'relative-output'):
            before = source.read_bytes()
            logfile.unlink(missing_ok=True)
            process = run_build(candidate, source, destination, 'c', 0, env, entry_probe=args.entry_probe)
            assert process.returncode != 0 and source.read_bytes() == before, process
            assert not logs(logfile), 'invalid output ran a compiler'
        checks.append('source-alias-and-relative-output-before-invalidation')
        if os.name == 'posix':
            linked = outputs / 'source-link'
            linked.symlink_to(source)
            process = run_build(candidate, source, str(linked), 'c', 0, env, entry_probe=args.entry_probe)
            assert process.returncode != 0 and linked.is_symlink() and source.read_text(encoding='utf-8') == PROGRAM, process
            checks.append('output-symlink-preserved-and-rejected')

        source.write_bytes(b'')
        empty_output = outputs / ('empty.exe' if os.name == 'nt' else 'empty')
        process = run_build(candidate, source, str(empty_output), 'c', 0, env, entry_probe=args.entry_probe)
        assert process.returncode == 0 and empty_output.is_file(), (process.stdout, process.stderr)
        executed = subprocess.run([str(empty_output)], capture_output=True, timeout=10, check=False)
        assert executed.returncode == 0, executed
        checks.append('valid-empty-source-is-not-read-failure')
        source.write_text('task main() { say missing_name }\n')
        process = run_build(candidate, source, str(empty_output), 'c', 0, env, entry_probe=args.entry_probe)
        assert_failed(process, empty_output)
        checks.append('type-error-invalidates-stale-executable')
        source.unlink()
        empty_output.write_bytes(b'stale missing-source binary')
        process = run_build(candidate, source, str(empty_output), 'c', 0, env, entry_probe=args.entry_probe)
        assert_failed(process, empty_output)
        assert b'Could not read file' in process.stdout, process
        checks.append('missing-source-owned-error-and-stale-invalidation')
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps({'status': 'pass', 'candidate_sha256': hashlib.sha256(candidate.read_bytes()).hexdigest(),
                                            'entry_probe': args.entry_probe, 'checks': checks,
                                            'limitations': limitations}, indent=2) + '\n')
    print('V3.5 native build contracts: OK', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
