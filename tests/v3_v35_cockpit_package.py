#!/usr/bin/env python3
"""Verify ordinary cockpit module/package binding with a native candidate.

--probe is the native binding component probe from v3_v35_package_binding.py.
--freak uses the integrated public CLI. Native Windows windows are a separate
gate; replay links deterministic platform ABI functions and preserves every
production Freak source byte.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

import v3_cockpit_compat as legacy
import v3_v35_package_binding as binding


MOCK_UI = r'''
#include "freak_runtime.h"
#include <stdint.h>
static int polls;
int64_t freak_ui_create_window_word(freak_word title,int64_t width,int64_t height,int64_t flags) { (void)title;(void)width;(void)height;(void)flags;return 1; }
void freak_ui_show_window(int64_t h) { (void)h; }
void freak_ui_set_title_word(int64_t h,freak_word title) { (void)h;(void)title; }
int64_t freak_ui_window_should_close(int64_t h) { (void)h;return 0; }
void freak_ui_destroy_window(int64_t h) { (void)h; }
int64_t freak_ui_poll_events(int64_t h) { (void)h;return polls++ == 0 ? -1 : 0; }
#define EVENT(name) int64_t freak_ui_event_##name(int64_t i) { (void)i;return 0; }
EVENT(kind) EVENT(key) EVENT(pressed) EVENT(repeat) EVENT(character)
EVENT(mouse_x) EVENT(mouse_y) EVENT(button) EVENT(scroll_dy) EVENT(width)
EVENT(height) EVENT(gained)
void freak_ui_begin_frame(int64_t h) { (void)h; }
void freak_ui_end_frame(int64_t h) { (void)h; }
void freak_ui_set_clip(int64_t h,int64_t x,int64_t y,int64_t w,int64_t t) { (void)h;(void)x;(void)y;(void)w;(void)t; }
void freak_ui_reset_clip(int64_t h) { (void)h; }
void freak_ui_clear(int64_t h,int64_t r,int64_t g,int64_t b,int64_t a) { (void)h;(void)r;(void)g;(void)b;(void)a; }
void freak_ui_fill_rect(int64_t h,int64_t x,int64_t y,int64_t w,int64_t t,int64_t r,int64_t g,int64_t b,int64_t a) { (void)h;(void)x;(void)y;(void)w;(void)t;(void)r;(void)g;(void)b;(void)a; }
void freak_ui_stroke_rect(int64_t h,int64_t x,int64_t y,int64_t w,int64_t t,int64_t r,int64_t g,int64_t b,int64_t a,int64_t thickness) { (void)h;(void)x;(void)y;(void)w;(void)t;(void)r;(void)g;(void)b;(void)a;(void)thickness; }
void freak_ui_fill_circle(int64_t h,int64_t x,int64_t y,int64_t radius,int64_t r,int64_t g,int64_t b,int64_t a) { (void)h;(void)x;(void)y;(void)radius;(void)r;(void)g;(void)b;(void)a; }
void freak_ui_draw_line(int64_t h,int64_t x,int64_t y,int64_t w,int64_t t,int64_t r,int64_t g,int64_t b,int64_t a,int64_t thickness) { (void)h;(void)x;(void)y;(void)w;(void)t;(void)r;(void)g;(void)b;(void)a;(void)thickness; }
int64_t freak_ui_draw_text_word(int64_t h,freak_word text,int64_t x,int64_t y,int64_t r,int64_t g,int64_t b,int64_t size,int64_t bold,int64_t italic) { (void)h;(void)x;(void)y;(void)r;(void)g;(void)b;(void)size;(void)bold;(void)italic;return text.length*7; }
int64_t freak_ui_get_width(int64_t h) { (void)h;return 320; }
int64_t freak_ui_get_height(int64_t h) { (void)h;return 240; }
int64_t freak_ui_measure_text_word(freak_word text,int64_t size,int64_t bold,int64_t italic) { (void)size;(void)bold;(void)italic;return text.length*7; }
'''


def emit(args: argparse.Namespace, root: Path, source: Path, backend: str,
         generated: Path, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[bytes]:
    if args.probe:
        return binding.run([str(args.probe.resolve()), str(root), str(source), backend, str(generated)], cwd=cwd, env=env)
    result = binding.run([str(args.freak.resolve()), 'transpile', str(source), f'--{backend}',
                          f'--manifest-path={root / "hangar.toml"}'], cwd=cwd, env=env)
    emitted = Path(str(source) + ('.c' if backend == 'c' else '.ll'))
    if result.returncode == 0 and emitted.is_file():
        shutil.copyfile(emitted, generated)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--runtime-root', type=Path)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--probe', type=Path)
    choice.add_argument('--freak', type=Path)
    parser.add_argument('--clang', required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--keep', type=Path)
    parser.add_argument('--sanitize', action='store_true')
    args = parser.parse_args()
    repo = args.repo.resolve()
    package = repo / 'packages/cockpit'
    runtime = args.runtime_root.resolve() if args.runtime_root else repo / 'freakc/runtime'
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    temporary = tempfile.TemporaryDirectory(prefix='v35-cockpit-package-') if not args.keep else None
    work = args.keep.resolve() if args.keep else Path(temporary.name)
    work.mkdir(parents=True, exist_ok=True)
    copied = work / 'source-tree/ordinary-cockpit'
    shutil.copytree(package, copied)
    unrelated = work / 'unrelated-cwd'
    unrelated.mkdir()
    # A same-named poison directory cannot influence declared package loading.
    poison = unrelated / 'packages/cockpit/src/ui.fk'
    poison.parent.mkdir(parents=True)
    poison.write_text('THIS CWD COCKPIT MUST NEVER BE LOADED\n')
    env = os.environ.copy()
    env['FREAK_BINDING_TEST_STD'] = str(repo / 'std')
    env['NO_COLOR'] = '1'
    if args.sanitize:
        env['ASAN_OPTIONS'] = 'detect_leaks=1:abort_on_error=1'
        env['UBSAN_OPTIONS'] = 'halt_on_error=1:print_stacktrace=1'
    mock = work / 'ui-platform-replay.c'
    mock.write_text(MOCK_UI)
    if args.sanitize:
        control = work / 'sanitizer-control.c'
        control.write_text('#include <stdlib.h>\nint main(void){volatile int offset=8;volatile int *p=malloc(sizeof(int));p[offset]=1;free((void*)p);return 0;}\n')
        control_binary = work / 'sanitizer-control'
        linked = binding.run([args.clang, '-O2', '-fsanitize=address,undefined', str(control), '-o', str(control_binary)], cwd=unrelated, env=env)
        if linked.returncode:
            raise RuntimeError('sanitizer failing control did not link')
        failed = binding.run([str(control_binary)], cwd=unrelated, env=env)
        (work / 'sanitizer-control.log').write_bytes(failed.stdout + failed.stderr)
        if failed.returncode == 0 or not (b'Sanitizer' in failed.stderr or b'runtime error' in failed.stderr):
            raise RuntimeError('sanitizer environment did not detect its failing control')
    api_symbols = sorted(set(re.findall(r'\bcockpit_\w+\b', legacy.PURE_PROGRAM)))
    consumer = work / 'source-tree/external-app'
    source_text = 'use cockpit::{\n    ' + ',\n    '.join(api_symbols) + '\n}\n' + legacy.PURE_PROGRAM
    binding.write_project(consumer, 'cockpit_consumer', {'src/main.fk': source_text}, entry='src/main.fk', dependencies={'cockpit': '../ordinary-cockpit'})
    records: list[dict] = []
    cases = [('external-public-consumer', consumer, consumer / 'src/main.fk', legacy.PURE_STDOUT, False),
             ('declared-pure-test', copied, copied / 'tests/pure.fk', [], False),
             ('shared-private-state-replay', copied, copied / 'tests/replay.fk', legacy.REPLAY_STDOUT, True)]
    for case, graph_root, source, expected, use_mock in cases:
        for backend in ('c', 'llvm'):
            generated = work / f'{case}.{"c" if backend == "c" else "ll"}'
            result = emit(args, graph_root, source, backend, generated, unrelated, env)
            (work / f'emit-{case}-{backend}.log').write_bytes(result.stdout + result.stderr)
            if result.returncode or not generated.is_file():
                raise RuntimeError(f'{case}/{backend} native emission failed: {work / f"emit-{case}-{backend}.log"}')
            for opt in ((2,) if args.sanitize else (0, 2, 3)):
                binary = work / f'{case}-{backend}-O{opt}'
                command = [args.clang, f'-O{opt}', '-I', str(runtime), str(generated),
                           str(runtime / 'freak_runtime.c'), str(runtime / 'freak_llvm_runtime.c')]
                if use_mock:
                    command.extend(['-DFREAK_HAS_UI', str(mock)])
                if args.sanitize:
                    command.extend(['-fsanitize=address,undefined', '-fno-omit-frame-pointer'])
                command.extend(['-DFREAK_WORD_FOUNDATION_AUDIT=1', '-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1' if backend == 'c' else '-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1', '-lm', '-o', str(binary)])
                compiled = binding.run(command, cwd=unrelated, env=env)
                (work / f'link-{case}-{backend}-O{opt}.log').write_bytes(compiled.stdout + compiled.stderr)
                if compiled.returncode:
                    raise RuntimeError(f'{case}/{backend}/O{opt} failed to link')
                executed = binding.run([str(binary)], cwd=unrelated, env=env)
                (work / f'run-{case}-{backend}-O{opt}.log').write_bytes(executed.stdout + executed.stderr)
                if executed.returncode or executed.stdout.decode().strip().splitlines() != expected or b'ownership audit found' in executed.stderr:
                    raise RuntimeError(f'{case}/{backend}/O{opt} failed: {executed.stdout!r} {executed.stderr!r}')
                records.append({'case': case, 'backend': backend, 'opt': opt, 'status': 'PASS', 'mock_platform': use_mock})
    # Each declared example parses its real self imports and links against the
    # same platform ABI. The deterministic poll closes the example's own window
    # on its first frame; interactive Windows behavior is a separate gate.
    for example in ('smoke', 'showcase', 'calculator', 'settings'):
        for backend in ('c', 'llvm'):
            generated = work / f'example-{example}.{"c" if backend == "c" else "ll"}'
            source = copied / f'examples/{example}.fk'
            emitted = emit(args, copied, source, backend, generated, unrelated, env)
            (work / f'emit-example-{example}-{backend}.log').write_bytes(emitted.stdout + emitted.stderr)
            if emitted.returncode or not generated.is_file():
                raise RuntimeError(f'{example}/{backend} declared example did not emit')
            binary = work / f'example-{example}-{backend}'
            command = [args.clang, '-O2', '-DFREAK_HAS_UI', '-DFREAK_WORD_FOUNDATION_AUDIT=1',
                       '-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1' if backend == 'c' else '-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1',
                       '-I', str(runtime), str(generated), str(runtime / 'freak_runtime.c'),
                       str(runtime / 'freak_llvm_runtime.c'), str(mock)]
            if args.sanitize:
                command.extend(['-fsanitize=address,undefined', '-fno-omit-frame-pointer'])
            command.extend(['-lm', '-o', str(binary)])
            linked = binding.run(command, cwd=unrelated, env=env)
            (work / f'link-example-{example}-{backend}.log').write_bytes(linked.stdout + linked.stderr)
            if linked.returncode:
                raise RuntimeError(f'{example}/{backend} example link failed')
            executed = binding.run([str(binary)], cwd=unrelated, env=env)
            (work / f'run-example-{example}-{backend}.log').write_bytes(executed.stdout + executed.stderr)
            if executed.returncode or executed.stdout or b'ownership audit found' in executed.stderr:
                raise RuntimeError(f'{example}/{backend} example shutdown failed: {executed.stdout!r} {executed.stderr!r}')
            records.append({'case': 'declared-example-shutdown', 'example': example, 'backend': backend, 'status': 'PASS', 'mock_platform': True})
    # Public consumers cannot reach shared mutable state or implementation tasks.
    for symbol in ('cockpit_ui_focused_input', 'cockpit_popup_result_value', 'cockpit_panel_can_begin'):
        (consumer / 'src/main.fk').write_text(f'use cockpit::{{{symbol}}}\ntask main() {{}}\n')
        for backend in ('c', 'llvm'):
            result = emit(args, consumer, consumer / 'src/main.fk', backend, work / f'private-{symbol}-{backend}', unrelated, env)
            log = result.stdout + result.stderr
            (work / f'negative-{symbol}-{backend}.log').write_bytes(log)
            if result.returncode == 0 or b'missing public export' not in log or f'{consumer / "src/main.fk"}:1:15'.encode() not in log:
                raise RuntimeError(f'private cockpit symbol admitted or lost original span: {symbol}: {log!r}')
            records.append({'case': 'private-symbol-rejected', 'symbol': symbol, 'backend': backend, 'status': 'PASS'})
    evidence = {'status': 'PASS', 'mode': 'public CLI' if args.freak else 'native binding component',
                'scope': 'ordinary package and deterministic platform replay; native Windows window gate separate',
                'candidate_sha256': hashlib.sha256((args.freak or args.probe).read_bytes()).hexdigest(),
                'manifest_sha256': hashlib.sha256((package / 'hangar.toml').read_bytes()).hexdigest(),
                'sanitize': args.sanitize, 'records': records}
    args.evidence.write_text(json.dumps(evidence, indent=2) + '\n')
    print(f'PASS {len(records)} ordinary cockpit package checks')


if __name__ == '__main__':
    main()
