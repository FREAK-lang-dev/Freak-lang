#!/usr/bin/env python3
"""Execute bounded loop storage and per-iteration ownership at native O0/O2/O3."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

from v3_checked_parsing import build_stage2, run, sanitizer_env
from v3_v35_language import require_ok

POSITIVE = {
    'repeat_body_scalar': ('task main() { pilot mut total = 0; repeat 2000000 times with i { pilot value = i; total += value % 2; } say total; }', '1000000\n'),
    'while_body_scalar': ('task main() { pilot mut total = 0; pilot mut tick = 0; while tick < 2000000 { pilot value = tick; total += value % 2; tick += 1; } say total; }', '1000000\n'),
    'for_body_scalar': ('task main() { pilot mut total = 0; for (pilot i = 0; i < 2000000; i += 1) { pilot value = i; total += value % 2; } say total; }', '1000000\n'),
    'nested_repeat_storage': ('task main() { pilot mut total = 0; repeat 800000 times with i { repeat 1 times with j { total += 1; } } say total; }', '800000\n'),
    'nested_range_storage': ('task main() { pilot mut total = 0; repeat 800000 times { for each i in 0..1 { total += 1; } } say total; }', '800000\n'),
    'nested_for_initializer': ('task main() { pilot mut total = 0; repeat 800000 times { for (pilot i = 0; i < 1; i += 1) { total += 1; } } say total; }', '800000\n'),
    'nested_foreach_storage': ('task main() { pilot values: List<int> = [1]; pilot mut total = 0; repeat 800000 times { for each value in values { total += value; } } say total; }', '800000\n'),
    'nested_training_storage': ('task main() { pilot mut total = 0; repeat 800000 times { training arc until false max 1 sessions { total += 1; } } say total; }', '800000\n'),
    'owned_continue_break': ('task main() { pilot mut total = 0; repeat 20000 times with i { pilot text = "owned" + " value"; pilot mut values: List<word> = [text + ""]; pilot mut box = Box { label: text + "" }; pilot bytes = ByteBuffer::new(); bytes.write_word(text); total += bytes.length(); bytes.release(); if i % 2 == 0 { continue; } values.push("next" + " value"); if i == 19999 { break; } } say total; }', '220000\n'),
    'typed_empty_list_storage': ('task main() { pilot mut total = 0; repeat 20000 times { pilot mut values: List<int> = []; values.push(3); pilot mut reserved: List<int> = List::with_capacity(1); reserved.push(4); total += values[0] + reserved[0]; } say total; }', '140000\n'),
    'shadowed_initializer_return': ('task choose(value: int) -> word { repeat 3 times with i { pilot text = "outer" + " owner"; if i == value { pilot text = text + " inner"; give back text; } } give back "none"; } task main() { say choose(1); }', 'outer owner inner\n'),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', type=Path)
    parser.add_argument('--clang', default=os.environ.get('FREAK_CLANG') or shutil.which('clang'))
    parser.add_argument('--optimization', choices=('O0', 'O2', 'O3'), action='append')
    parser.add_argument('--sanitize', action='store_true')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    assert args.clang, 'Clang required'
    repo = Path(__file__).resolve().parents[1]
    runtime = repo / 'freakc/runtime'
    optimizations = args.optimization or ['O0', 'O2', 'O3']
    flags = ['-g', '-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1', '-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1', '-I', str(runtime)]
    if args.sanitize:
        flags += ['-fsanitize=address,undefined', '-fno-omit-frame-pointer']
    link_flags = ['-lws2_32'] if sys.platform == 'win32' else ['-lm']
    inventory = []
    with tempfile.TemporaryDirectory(prefix='freak-v35-loop-storage-') as directory:
        root = Path(directory)
        compiler = args.compiler.resolve(strict=True) if args.compiler else build_stage2(clang=args.clang, repo=repo, root=root)
        for backend in ('c', 'llvm'):
            suffix = '.c' if backend == 'c' else '.ll'
            artifacts = {}
            for name, (program, _) in POSITIVE.items():
                source = root / f'{name}_{backend}.fk'
                source.write_text('shape Box { label: word }\n' + program + '\n')
                require_ok(run([str(compiler), str(source), '--' + backend, '--strict-borrow'], root), 'loop emission ' + name)
                artifacts[name] = str(source) + suffix
            for optimization in optimizations:
                objects = []
                for unit in ('freak_runtime.c', 'freak_llvm_runtime.c'):
                    if unit == 'freak_llvm_runtime.c' and backend == 'c':
                        continue
                    obj = root / f'{optimization}_{backend}_{unit}.o'
                    require_ok(run([args.clang, '-' + optimization, *flags, '-c', str(runtime / unit), '-o', str(obj)], root), 'loop audited runtime ' + unit)
                    objects.append(str(obj))
                for name, (_, expected) in POSITIVE.items():
                    binary = root / f'{optimization}_{name}_{backend}'
                    require_ok(run([args.clang, '-' + optimization, *flags, artifacts[name], *objects, *link_flags, '-o', str(binary)], root), 'loop link ' + name)
                    result = run([str(binary)], root, env=sanitizer_env())
                    assert result.returncode == 0 and result.stdout == expected and not result.stderr, (backend, optimization, name, result)
                    inventory.append((backend, optimization, name))
                print(f'PASS {backend} {optimization}: bounded loop storage and owned exits', flush=True)
    expected = {(backend, optimization, name) for backend in ('c', 'llvm') for optimization in optimizations for name in POSITIVE}
    assert len(inventory) == len(expected) and set(inventory) == expected
    evidence = {'contracts': len(inventory), 'optimizations': optimizations, 'sanitized': args.sanitize, 'inventory': inventory}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(evidence, indent=2) + '\n')
    print(f'V3.5 loop storage contracts: PASS ({len(inventory)} cases)', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
