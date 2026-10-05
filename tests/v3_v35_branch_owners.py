#!/usr/bin/env python3
"""Verify consuming owners across live and terminal native branch routes."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import sys
import tempfile

from v3_checked_parsing import build_stage2, run, sanitizer_env
from v3_v35_language import require_ok

POSITIVE = {
    'buffer_early_return': ('task choose(bytes: ByteBuffer, stop: bool) -> int { if stop { bytes.release(); give back 0; } pilot length = bytes.length(); bytes.release(); give back length + 1; } task main() { say choose(ByteBuffer::new(), true); say choose(ByteBuffer::new(), false); }', '0\n1\n'),
    'word_early_return': ('task take(text: word) { say text; } task choose(text: word, stop: bool) { if stop { take(text); give back; } say text; } task main() { choose("first" + " owner", true); choose("second" + " owner", false); }', 'first owner\nsecond owner\n'),
    'exclusive_consuming_arms': ('task choose(bytes: ByteBuffer, first: bool) -> int { if first { bytes.release(); give back 1; } else { bytes.release(); give back 2; } } task main() { say choose(ByteBuffer::new(), true); say choose(ByteBuffer::new(), false); }', '1\n2\n'),
    'terminal_else': ('task choose(bytes: ByteBuffer, first: bool) -> int { if first { say bytes.length(); } else { bytes.release(); give back 2; } bytes.release(); give back 1; } task main() { say choose(ByteBuffer::new(), true); say choose(ByteBuffer::new(), false); }', '0\n1\n2\n'),
    'nested_terminal_then': ('task choose(bytes: ByteBuffer, first: bool, second: bool) -> int { if first { if second { bytes.release(); give back 1; } else { bytes.release(); give back 2; } } pilot length = bytes.length(); bytes.release(); give back length + 3; } task main() { say choose(ByteBuffer::new(), true, true); say choose(ByteBuffer::new(), true, false); say choose(ByteBuffer::new(), false, false); }', '1\n2\n3\n'),
    'inferred_scalar_ticket': ('task choose(stop: bool) -> int { pilot read = fs::read_ticket("intentionally-missing-file"); if stop { fs::result_release(read); give back 1; } say fs::result_ok(read); say fs::result_ok(read); fs::result_release(read); give back 2; } task main() { say choose(true); say choose(false); }', '1\nfalse\nfalse\n2\n'),
    'reinitialized_owner': ('task choose(first: bool) { pilot mut bytes: ByteBuffer = ByteBuffer::new(); if first { bytes.release(); bytes = ByteBuffer::new(); } say bytes.length(); bytes.release(); } task main() { choose(true); choose(false); }', '0\n0\n'),
    'terminated_block': ('task choose(bytes: ByteBuffer) -> int { bytes.release(); give back 1; say bytes.length(); } task main() { say choose(ByteBuffer::new()); }', '1\n'),
    'partial_live_arms': ('task choose(bytes: ByteBuffer, first: bool) { if first { say bytes.length(); } else { say bytes.length(); } bytes.release(); } task main() { choose(ByteBuffer::new(), true); choose(ByteBuffer::new(), false); }', '0\n0\n'),
    'nested_loop_then_return': ('task choose(bytes: ByteBuffer, first: bool) -> int { if first { repeat 1 times { break; } bytes.release(); give back 1; } pilot length = bytes.length(); bytes.release(); give back length + 2; } task main() { say choose(ByteBuffer::new(), true); say choose(ByteBuffer::new(), false); }', '1\n2\n'),
    'dead_read_after_break': ('task main() { pilot bytes: ByteBuffer = ByteBuffer::new(); repeat 1 times { bytes.release(); break; say bytes.length(); } }', ''),
    'dead_read_after_continue': ('task main() { pilot bytes: ByteBuffer = ByteBuffer::new(); repeat 1 times { bytes.release(); continue; say bytes.length(); } }', ''),
}
NEGATIVE = {
    'move_on_live_then': 'task choose(bytes: ByteBuffer, first: bool) { if first { bytes.release(); } say bytes.length(); } task main() { choose(ByteBuffer::new(), false); }',
    'move_on_live_else': 'task choose(bytes: ByteBuffer, first: bool) { if first { say bytes.length(); } else { bytes.release(); } say bytes.length(); } task main() { choose(ByteBuffer::new(), true); }',
    'use_before_terminal': 'task choose(bytes: ByteBuffer, first: bool) { if first { bytes.release(); say bytes.length(); give back; } bytes.release(); } task main() { choose(ByteBuffer::new(), false); }',
    'incomplete_terminal_route': 'task choose(bytes: ByteBuffer, first: bool, second: bool) -> int { if first { bytes.release(); if second { give back 1; } } say bytes.length(); bytes.release(); give back 2; } task main() { say choose(ByteBuffer::new(), false, false); }',
    'word_move_on_live_route': 'task take(text: word) {} task choose(text: word, first: bool) { if first { take(text); } say text; } task main() { choose("owner" + " word", false); }',
    'prior_move_stays_moved': 'task choose(bytes: ByteBuffer, first: bool) { bytes.release(); if first { say 1; } else { say 2; } say bytes.length(); } task main() { choose(ByteBuffer::new(), false); }',
    'condition_move_stays_moved': 'task take(bytes: ByteBuffer) -> bool { bytes.release(); give back true; } task main() { pilot bytes: ByteBuffer = ByteBuffer::new(); if take(bytes) { say 1; } bytes.release(); }',
    'wrong_case_release': 'task main() { pilot bytes: ByteBuffer = ByteBuffer::new(); if true { bytes.release(); } else { bytes.release(); } bytes.release(); }',
    'break_then_unreachable_return': 'task main() { pilot bytes: ByteBuffer = ByteBuffer::new(); repeat 1 times { if true { bytes.release(); break; give back; } } say bytes.length(); bytes.release(); }',
    'continue_then_unreachable_return': 'task main() { pilot bytes: ByteBuffer = ByteBuffer::new(); repeat 1 times { if true { bytes.release(); continue; give back; } } say bytes.length(); bytes.release(); }',
    'nested_block_break_then_return': 'task main() { pilot bytes: ByteBuffer = ByteBuffer::new(); repeat 1 times { if true { bytes.release(); { break; } give back; } } say bytes.length(); bytes.release(); }',
    'conditional_break_then_return': 'task choose(bytes: ByteBuffer, stop: bool) { repeat 1 times { if true { bytes.release(); if stop { break; } give back; } } say bytes.length(); bytes.release(); } task main() { choose(ByteBuffer::new(), true); }',
    'conditional_continue_then_return': 'task choose(bytes: ByteBuffer, stop: bool) { repeat 1 times { if true { bytes.release(); if stop { continue; } give back; } } say bytes.length(); bytes.release(); } task main() { choose(ByteBuffer::new(), true); }',
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', type=Path)
    parser.add_argument('--clang', default=os.environ.get('FREAK_CLANG') or shutil.which('clang'))
    args = parser.parse_args()
    assert args.clang, 'Clang required'
    repo = Path(__file__).resolve().parents[1]
    runtime = repo / 'freakc/runtime'
    flags = ['-O2', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1', '-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1', '-I', str(runtime)]
    link_flags = ['-lws2_32'] if sys.platform == 'win32' else ['-lm']
    with tempfile.TemporaryDirectory(prefix='freak-v35-branch-owners-') as directory:
        root = Path(directory)
        compiler = args.compiler.resolve(strict=True) if args.compiler else build_stage2(clang=args.clang, repo=repo, root=root)
        for backend in ('c', 'llvm'):
            suffix = '.c' if backend == 'c' else '.ll'
            objects = []
            for unit in ('freak_runtime.c', 'freak_llvm_runtime.c'):
                if unit == 'freak_llvm_runtime.c' and backend == 'c':
                    continue
                obj = root / f'{backend}_{unit}.o'
                require_ok(run([args.clang, *flags, '-c', str(runtime / unit), '-o', str(obj)], root), 'branch runtime')
                objects.append(str(obj))
            for name, (program, expected) in POSITIVE.items():
                source = root / f'{name}_{backend}.fk'
                source.write_text(program + '\n')
                require_ok(run([str(compiler), str(source), '--' + backend, '--strict-borrow'], root), 'branch emission ' + name)
                binary = root / f'{name}_{backend}'
                require_ok(run([args.clang, *flags, str(source) + suffix, *objects, *link_flags, '-o', str(binary)], root), 'branch link ' + name)
                result = run([str(binary)], root, env=sanitizer_env())
                assert result.returncode == 0 and result.stdout == expected and not result.stderr, (backend, name, result)
            for name, program in NEGATIVE.items():
                source = root / f'{name}_{backend}.fk'
                source.write_text(program + '\n')
                output = Path(str(source) + suffix)
                output.write_text('stale artifact')
                result = run([str(compiler), str(source), '--' + backend, '--strict-borrow'], root)
                assert result.returncode != 0 and 'borrowck' in result.stdout and 'no longer belongs' in result.stdout and not output.exists(), (backend, name, result)
            print(f'PASS {backend}: {len(POSITIVE)} live/terminal owner programs, {len(NEGATIVE)} move controls', flush=True)
    print(f'V3.5 branch ownership contracts: PASS ({2 * (len(POSITIVE) + len(NEGATIVE))} contracts)', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
