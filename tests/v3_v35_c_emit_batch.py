#!/usr/bin/env python3
"""Exercise the actual bounded C-emission helpers against checked native IO.

The explicit host profile owns the batch lifecycle. Ordinary C and LLVM
program emission still uses immediate appends. This gate extracts the actual
helper bodies, executes both native ABIs, checks every output byte, and uses
real short-write/close/allocation failure controls rather than stub FS calls.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


PROGRAM = r'''
extern task batch_probe_reset() -> void
extern task batch_probe_fault(value: int) -> void
extern task batch_probe_appends() -> int
extern task batch_probe_done() -> void

task check_bound() -> void {
    if emt_c_batch_builder != 0 {
        if word_builder::length(emt_c_batch_builder) > 65536 { panic("batch length exceeded") }
        if word_builder::capacity(emt_c_batch_builder) > 65536 { panic("batch capacity exceeded") }
    }
}

task fragments() -> void {
    emit("start:") check_bound()
    emit("x".repeated(65535)) check_bound()
    emit("y") check_bound()
    emit("z") check_bound()
    emit("L".repeated(65537)) check_bound()
    emit(char_to_word(0)) check_bound()
    emit_line("é日本🙂") check_bound()
    emit_line("") check_bound()
    emit("") check_bound()
    emit("tail") check_bound()
}

task main() {
    pilot mode = process::arg(1)
    pilot path = process::arg(2)
    out_file = path
    if mode.ends_with("open") or mode == "nested" {
        batch_probe_reset()
        if mode == "immediate-open" { emit("failure") }
        emit_c_batch_begin()
        if mode == "nested" { emit_c_batch_begin() }
        if mode == "builder-leak-open" {
            -- Deliberately bypass the helper flush to validate its fatal audit.
            emit("pending")
            fs::append(out_file, "failure")
        }
        if mode == "empty-open" { emit("") }
        else if mode == "oversize-open" { emit("x".repeated(65537)) }
        else if mode == "limit-open" { emit("x".repeated(65536)) emit("y") }
        else { emit("tail") }
        emit_c_batch_finish()
        say "SHOULD-NOT"
        give back
    }
    fs::write(path, "")
    batch_probe_reset()
    if mode == "immediate" { fragments() }
    else if mode == "batch" {
        emit_c_batch_begin()
        fragments()
        emit_c_batch_finish()
    } else if mode == "empty" {
        emit_c_batch_begin()
        emit_c_batch_finish()
    } else if mode == "deferred" {
        emit_c_batch_begin()
        emit("final bytes")
        if batch_probe_appends() != 0 { panic("batch wrote before finish") }
        emit_c_batch_finish()
    } else if mode == "unicode" {
        emit_c_batch_begin()
        emit("🙂".repeated(16384)) check_bound()
        emit("日") check_bound()
        emit("🙂".repeated(16385)) check_bound()
        emit(char_to_word(0)) check_bound()
        emit_c_batch_finish()
    } else if mode == "sequential" {
        emit_c_batch_begin() emit("first") emit_c_batch_finish()
        out_file = ""
        out_file = path + ".ordinary"
        emit("second")
        out_file = ""
        out_file = path + ".profile"
        emit_c_batch_begin() emit_line("third") emit_c_batch_finish()
    } else if mode == "alloc" {
        emit_c_batch_begin()
        batch_probe_fault(3)
        emit("allocation")
        emit_c_batch_finish()
        say "SHOULD-NOT"
    } else {
        emit_c_batch_begin()
        emit("final bytes")
        if mode == "final-short" { batch_probe_fault(1) }
        if mode == "final-close" { batch_probe_fault(2) }
        emit_c_batch_finish()
        say "SHOULD-NOT"
    }
    if emt_c_batch_active or emt_c_batch_builder != 0 { panic("batch survived finish") }
    batch_probe_done()
}
'''


NATIVE = r'''
#if defined(_WIN32) && !defined(_WIN32_WINNT)
#define _WIN32_WINNT 0x0602
#endif
#if defined(__APPLE__) && !defined(_DARWIN_C_SOURCE)
#define _DARWIN_C_SOURCE 1
#endif
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <errno.h>
static int probe_fault;
static size_t probe_appends;
static size_t probe_sizes[64];
static size_t probe_write(const void *data, size_t size, size_t count, FILE *stream);
static int probe_close(FILE *stream);
static void *probe_realloc(void *pointer, size_t size);
#define fwrite probe_write
#define fclose probe_close
#define realloc probe_realloc
#include "freak_runtime.c"
#undef fwrite
#undef fclose
#undef realloc
static void probe_builder_exit(void) {
    if (freak_word_builder_live_count != 0) {
        fprintf(stderr, "FREAK: probe found live builder at exit\n");
        fflush(stderr);
        _Exit(89);
    }
}
static size_t probe_write(const void *data, size_t size, size_t count, FILE *stream) {
    if (freak_word_builder_live_count != 0) abort();
    if (probe_appends >= 64) abort();
    probe_sizes[probe_appends++] = size * count;
    if (probe_fault == 1) {
        probe_fault = 0;
        return count ? fwrite(data, size, count - 1, stream) : 0;
    }
    return fwrite(data, size, count, stream);
}
static int probe_close(FILE *stream) {
    int result = fclose(stream);
    if (probe_fault == 2) { probe_fault = 0; errno = EIO; return EOF; }
    return result;
}
static void *probe_realloc(void *pointer, size_t size) {
    if (probe_fault == 3) { probe_fault = 0; errno = ENOMEM; return NULL; }
    return realloc(pointer, size);
}
void batch_probe_reset(void) {
    if (freak_word_builder_live_count != 0) abort();
    if (atexit(probe_builder_exit) != 0) abort();
    probe_fault = 0; probe_appends = 0;
}
void batch_probe_fault(int64_t value) { probe_fault = (int)value; }
int64_t batch_probe_appends(void) { return (int64_t)probe_appends; }
void batch_probe_done(void) {
    if (freak_word_builder_live_count != 0 || probe_fault) abort();
    printf("writes=");
    for (size_t i = 0; i < probe_appends; ++i) printf("%s%zu", i ? "," : "", probe_sizes[i]);
    putchar('\n');
}
'''


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def helper_source(repo: Path) -> str:
    text = (repo / 'src/compiler/v3/helpers.fk').read_text(encoding='utf-8')
    start = text.index('pilot emt_c_batch_active')
    end = text.index('\ntask adjust_token_lines', start)
    return 'pilot out_file = ""\n' + text[start:end] + '\n' + PROGRAM


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', required=True, type=Path)
    parser.add_argument('--clang', default=os.environ.get('FREAK_CLANG') or shutil.which('clang'))
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--optimization', choices=('O0', 'O2', 'O3'), default='O2')
    parser.add_argument('--sanitize', action='store_true')
    args = parser.parse_args()
    repo = args.repo.resolve(strict=True)
    compiler = args.compiler.resolve(strict=True)
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    runtime = repo / 'freakc/runtime'
    inputs = [compiler, Path(__file__).resolve(), repo / 'src/compiler/v3/helpers.fk', repo / 'src/compiler/v3/emit_c.fk']
    inputs += [path for base in (runtime, repo / 'third_party/llhttp') for path in base.rglob('*') if path.is_file()]
    frozen = {str(path): digest(path) for path in inputs}
    report = {'passed': False, 'optimization': args.optimization, 'sanitized': args.sanitize,
              'inputs': frozen, 'commands': [], 'cases': []}
    env = os.environ.copy()
    if args.sanitize:
        env['ASAN_OPTIONS'] = 'halt_on_error=1:detect_leaks=1:exitcode=86'
        env['UBSAN_OPTIONS'] = 'halt_on_error=1:print_stacktrace=1'

    def run(command: list[str], *, fatal: bool = False) -> subprocess.CompletedProcess[bytes]:
        selected = env.copy()
        if fatal and args.sanitize:
            # Fatal FS APIs exit immediately and do not promise caller cleanup.
            selected['ASAN_OPTIONS'] = 'halt_on_error=1:detect_leaks=0:exitcode=86'
        result = subprocess.run(command, cwd=root, env=selected, capture_output=True, timeout=180)
        index = len(report['commands'])
        (root / f'{index:03}.stdout').write_bytes(result.stdout)
        (root / f'{index:03}.stderr').write_bytes(result.stderr)
        report['commands'].append({'argv': command, 'returncode': result.returncode,
                                   'stdout_hex': result.stdout.hex(), 'stderr_hex': result.stderr.hex()})
        return result

    try:
        source = root / 'helpers.fk'
        source.write_text(helper_source(repo), encoding='utf-8')
        adapter = root / 'native.c'
        adapter.write_text(NATIVE, encoding='utf-8')
        expected = b'start:' + b'x' * 65535 + b'yz' + b'L' * 65537 + b'\0' + 'é日本🙂\n'.encode() + b'\ntail'
        good = {'immediate': (expected, [6, 65535, 1, 1, 65537, 1, 13, 1, 0, 4]),
                'batch': (expected, [6, 65536, 1, 65537, 15, 0, 4]),
                'empty': (b'', []), 'deferred': (b'final bytes', [11]),
                'sequential': (b'first', [5, 6, 6]),
                'unicode': ('🙂'.encode() * 16384 + '日'.encode() + '🙂'.encode() * 16385 + b'\0',
                            [65536, 3, 65540, 1])}
        failures = ('immediate-open', 'final-open', 'empty-open', 'oversize-open', 'limit-open',
                    'final-short', 'final-close', 'alloc', 'nested', 'builder-leak-open')
        for backend in ('c', 'llvm'):
            emitted = Path(str(source) + ('.c' if backend == 'c' else '.ll'))
            result = run([str(compiler), str(source), '--' + backend])
            assert result.returncode == 0, result
            binary = root / (backend + ('.exe' if sys.platform == 'win32' else ''))
            command = [args.clang, '-' + args.optimization, '-g', '-o', str(binary), str(emitted), str(adapter),
                       '-I', str(runtime), '-DFREAK_WORD_FOUNDATION_AUDIT=1',
                       '-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1', '-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1']
            if backend == 'llvm': command.append(str(runtime / 'freak_llvm_runtime.c'))
            command += ['-lws2_32'] if sys.platform == 'win32' else ['-lm']
            if args.sanitize: command += ['-fsanitize=address,undefined', '-fno-omit-frame-pointer']
            result = run(command)
            assert result.returncode == 0, result
            for name, (contents, sizes) in good.items():
                path = root / f'{backend}-{name}.out'
                result = run([str(binary), name, str(path)])
                assert result.returncode == 0, (backend, name, result)
                newline = '\r\n' if os.name == 'nt' else '\n'
                assert result.stdout == ('writes=' + ','.join(map(str, sizes)) + newline).encode(), (name, result)
                assert path.read_bytes() == contents, (backend, name)
                stats_lines = [line for line in result.stderr.splitlines() if line.startswith(b'FREAK_RUNTIME_STATS ')]
                assert len(stats_lines) == (0 if name == 'empty' else 1), result.stderr
                counters = json.loads(stats_lines[0].split(b' ', 1)[1])['counters'] if stats_lines else {
                    'word_builder_growths': 0, 'word_builder_creations': 0,
                    'word_builder_finishes': 0, 'word_builder_discards': 0}
                assert counters['word_builder_growths'] == 0, counters
                assert counters['word_builder_creations'] == counters['word_builder_finishes'] + counters['word_builder_discards'], counters
                if name == 'sequential':
                    assert Path(str(path) + '.ordinary').read_bytes() == b'second'
                    assert Path(str(path) + '.profile').read_bytes() == b'third\n'
                report['cases'].append({'backend': backend, 'name': name, 'passed': True})
                print('PASS', backend, name, flush=True)
            # The original fatal FS API exits without lexical caller cleanup;
            # verify its exit1 contract with ordinary, unaudited binaries.
            fatal_binary = root / (backend + '-fatal' + ('.exe' if sys.platform == 'win32' else ''))
            fatal_command = [str(fatal_binary) if part == str(binary) else part for part in command
                             if part != '-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1' and
                             not (backend == 'llvm' and part == '-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1')]
            result = run(fatal_command)
            assert result.returncode == 0, result
            for name in failures:
                path = root / f'{backend}-{name}.out'
                if name.endswith('open') or name == 'nested': path.mkdir()
                result = run([str(fatal_binary), name, str(path)], fatal=True)
                expected_status = 89 if name == 'builder-leak-open' else 1
                assert result.returncode == expected_status and b'SHOULD-NOT' not in result.stdout, (backend, name, result)
                if name == 'alloc': assert b'out of memory' in result.stderr, result
                elif name == 'nested': assert b'C emission batch is already active' in result.stderr, result
                elif name == 'builder-leak-open': assert b'live builder' in result.stderr, result
                else: assert b'FREAK: cannot append file' in result.stderr or b'FREAK: could not complete file write' in result.stderr, result
                report['cases'].append({'backend': backend, 'name': name, 'passed': True,
                                        'intentional_leak_control': name == 'builder-leak-open'})
                print('PASS', backend, name, flush=True)
        assert len(report['cases']) == 32
        report['passed'] = True
    finally:
        report['inputs_unchanged'] = all(digest(Path(path)) == value for path, value in frozen.items())
        report['passed'] = report['passed'] and report['inputs_unchanged']
        (root / 'gate.json').write_text(json.dumps(report, indent=2) + '\n')
    assert report['passed'], 'frozen inputs changed during the gate'
    print('PASS bounded C emission helpers (32 cases)', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
