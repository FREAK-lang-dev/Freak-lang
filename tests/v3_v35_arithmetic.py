#!/usr/bin/env python3
"""Execute native integer, bounds and conversion semantics through both emitters.

Exact Python integer arithmetic supplies the legal-result oracle. Hostile cases
must stop with a FREAK diagnostic before observable continuation or host UB.
Runtime objects are compiled once per optimization and reused for small cases.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

from v3_checked_parsing import build_stage2, run, sanitizer_env
from v3_v35_integers import oracle
from v3_v35_language import require_ok

LOW, HIGH = -(1 << 63), (1 << 63) - 1
VALUES = (LOW, LOW + 1, -10, -1, 0, 1, 2, 9, 10, HIGH - 1, HIGH)
LEGAL = [(operation, left, right, expected)
         for operation, left, right in itertools.product(('add', 'sub', 'mul', 'div', 'rem'), VALUES, VALUES)
         if (expected := oracle(operation, left, right)) is not None]
SYMBOLS = {'add': '+', 'sub': '-', 'mul': '*', 'div': '/', 'rem': '%'}
ORACLE_PROGRAM = 'task main() {\n' + ''.join(
    f'    say ({left}) {SYMBOLS[operation]} ({right});\n'
    for operation, left, right, _ in LEGAL) + '}\n'
ORACLE_EXPECTED = ''.join(f'{expected}\n' for *_, expected in LEGAL)
POSITIVE = {
    'bigint_oracle': (ORACLE_PROGRAM, ORACLE_EXPECTED),
    'decimal_and_minimum': ('task main() { say 00015; say -00015; say 0009223372036854775807; say -0009223372036854775808; }', f'15\n-15\n{HIGH}\n{LOW}\n'),
    'compound_local': ('task main() { pilot mut value = 50; value += 3; value -= 5; value *= 2; value /= 5; value %= 7; say value; }', '5\n'),
    'compound_global_order': ('pilot mut value = 10\ntask change() -> int { value = 100; give back 2; } task main() { value += change(); say value; }', '12\n'),
    'compound_projections': ('shape Box { value: int } task main() { pilot mut values: List<int> = [50]; values[0] += 3; values[0] -= 5; values[0] *= 2; values[0] /= 5; values[0] %= 7; say values[0]; pilot mut box = Box { value: 50 }; box.value += 3; box.value -= 5; box.value *= 2; box.value /= 5; box.value %= 7; say box.value; }', '5\n5\n'),
    'operator_evaluation_once': ('pilot mut ticks = 0\ntask next(value: int) -> int { ticks += 1; say ticks; give back value; } task main() { say FINAL FORM next(3); say next(2) NAKAMA next(5); say PLUS ULTRA next(4); say TSUNDERE next(6); say next(1) + next(2); }', '1\n9\n2\n3\n8\n4\n8\n5\n-6\n6\n7\n3\n'),
    'word_index_result': ('task make() -> word { give back "a" + "bc"; } task main() { pilot byte = make()[1]; say byte; say byte.length(); say "abc"[0]; }', 'b\n1\na\n'),
    'word_index_global_snapshot': ('pilot mut text = "a" + "bc"\ntask change() -> int { text = "new" + " value"; give back 1; } task main() { say text[change()]; say text; }', 'b\nnew value\n'),
    'word_index_raw_source': ('task main() { check result fs::read_checked("raw-input.bin") { ok(value) -> { pilot nul = value[1]; pilot byte = value[2]; say nul.length(); say byte.length(); pilot bytes = ByteBuffer::new(); bytes.write_word(nul); bytes.write_word(byte); say bytes.length(); say bytes.read_byte(); say bytes.read_byte(); bytes.release(); } err(error) -> { panic(error); } } }', '1\n1\n2\n0\n255\n'),
    'finite_conversion': ('task main() { say (3.9).to_int(); say (-3.9).to_int(); say (-9223372036854775808.0).to_int(); say (9223372036854774784.0).to_int(); }', f'3\n-3\n{LOW}\n9223372036854774784\n'),
}
FATAL = {
    'add_high': (f'say {HIGH} + 1;', 'integer overflow'),
    'subtract_low': (f'say ({LOW}) - 1;', 'integer overflow'),
    'multiply_high': (f'say {HIGH} * 2;', 'integer overflow'),
    'divide_zero': ('say 1 / 0;', 'division by zero'),
    'remainder_zero': ('say 1 % 0;', 'division by zero'),
    'divide_minimum': (f'say ({LOW}) / (-1);', 'integer overflow'),
    'remainder_minimum': (f'say ({LOW}) % (-1);', 'integer overflow'),
    'negate_minimum': (f'say -({LOW});', 'integer overflow'),
    'tsundere_minimum': (f'say TSUNDERE ({LOW});', 'integer overflow'),
    'plus_ultra': (f'say PLUS ULTRA {HIGH};', 'integer overflow'),
    'final_form': ('say FINAL FORM 3037000500;', 'integer overflow'),
    'nakama_sum': (f'say {HIGH} NAKAMA 1;', 'integer overflow'),
    'nakama_product': ('say 4611686018427387903 NAKAMA 3;', 'integer overflow'),
    'compound_add': (f'pilot mut value = {HIGH}; value += 1;', 'integer overflow'),
    'compound_subtract': (f'pilot mut value = {LOW}; value -= 1;', 'integer overflow'),
    'compound_multiply': (f'pilot mut value = {HIGH}; value *= 2;', 'integer overflow'),
    'compound_divide': (f'pilot mut value = {LOW}; value /= -1;', 'integer overflow'),
    'compound_remainder': (f'pilot mut value = {LOW}; value %= -1;', 'integer overflow'),
    'array_compound': (f'pilot mut values: List<int> = [{HIGH}]; values[0] += 1;', 'integer overflow'),
    'field_compound': (f'pilot mut box = Box {{ value: {HIGH} }}; box.value += 1;', 'integer overflow'),
    'word_negative': ('say "abc"[-1];', 'word index out of range'),
    'word_equal_length': ('say "abc"[3];', 'word index out of range'),
    'word_empty': ('say ""[0];', 'word index out of range'),
    'word_huge': (f'say "abc"[{HIGH}];', 'word index out of range'),
    'num_nan': ('say math::sqrt(-1.0).to_int();', 'num to int conversion out of range'),
    'num_infinity': ('say math::pow(2.0, 1024.0).to_int();', 'num to int conversion out of range'),
    'num_negative_infinity': ('say (-math::pow(2.0, 1024.0)).to_int();', 'num to int conversion out of range'),
    'num_upper': ('say (9223372036854775808.0).to_int();', 'num to int conversion out of range'),
    'num_below_lower': ('say (-9223372036854777856.0).to_int();', 'num to int conversion out of range'),
}
NEGATIVE = {
    'positive_oversized': f'say {HIGH + 1};',
    'negative_oversized': f'say {LOW - 1};',
    'huge_positive': 'say 99999999999999999999999999999999999;',
    'leading_oversized': f'say 000{HIGH + 1};',
    'unsigned_magnitude_in_call': f'say word_from_int({HIGH + 1});',
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
    optimizations = args.optimization or ['O0', 'O2', 'O3']
    repo = Path(__file__).resolve().parents[1]
    runtime = repo / 'freakc/runtime'
    inventory = []
    flags = ['-g', '-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1', '-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1', '-I', str(runtime)]
    if args.sanitize:
        flags += ['-fsanitize=address,undefined', '-fno-omit-frame-pointer']
    link_flags = ['-lws2_32'] if sys.platform == 'win32' else ['-lm']
    with tempfile.TemporaryDirectory(prefix='freak-v35-arithmetic-') as directory:
        root = Path(directory)
        (root / 'raw-input.bin').write_bytes(b'A\0\xff')
        compiler = args.compiler.resolve(strict=True) if args.compiler else build_stage2(clang=args.clang, repo=repo, root=root)
        sources = {}
        for backend in ('c', 'llvm'):
            suffix = '.c' if backend == 'c' else '.ll'
            for name, (program, _) in POSITIVE.items():
                source = root / f'{backend}_{name}.fk'
                source.write_text(program + '\n')
                require_ok(run([str(compiler), str(source), '--' + backend, '--strict-borrow'], root), 'positive emission ' + name)
                sources[(backend, name)] = Path(str(source) + suffix)
            for name, (body, _) in FATAL.items():
                source = root / f'{backend}_{name}.fk'
                source.write_text('shape Box { value: int } task main() { ' + body + ' say "after"; }\n')
                require_ok(run([str(compiler), str(source), '--' + backend, '--strict-borrow'], root), 'fatal emission ' + name)
                sources[(backend, name)] = Path(str(source) + suffix)
            for name, body in NEGATIVE.items():
                source = root / f'{backend}_{name}.fk'
                source.write_text('task main() { ' + body + ' }\n')
                artifact = Path(str(source) + suffix)
                artifact.write_text('stale arithmetic output')
                rejected = run([str(compiler), str(source), '--' + backend], root)
                assert rejected.returncode != 0 and 'integer literal is outside the signed 64-bit range' in rejected.stdout + rejected.stderr, (backend, name, rejected)
                assert not artifact.exists(), (backend, name, 'stale artifact survived')
                inventory.append((backend, 'frontend', name))
            for optimization in optimizations:
                objects = []
                for unit in ('freak_runtime.c', 'freak_llvm_runtime.c'):
                    if unit == 'freak_llvm_runtime.c' and backend == 'c':
                        continue
                    obj = root / f'{backend}_{optimization}_{unit}.o'
                    require_ok(run([args.clang, '-' + optimization, *flags, '-c', str(runtime / unit), '-o', str(obj)], root), 'audited runtime object ' + unit)
                    objects.append(str(obj))
                for name, (_, expected) in POSITIVE.items():
                    binary = root / f'{backend}_{optimization}_{name}'
                    require_ok(run([args.clang, '-' + optimization, *flags, str(sources[(backend, name)]), *objects, *link_flags, '-o', str(binary)], root), 'positive link ' + name)
                    executed = run([str(binary)], root, env=sanitizer_env())
                    require_ok(executed, 'positive execution ' + name)
                    assert executed.stdout == expected and not executed.stderr, (backend, optimization, name, executed)
                    inventory.append((backend, optimization, name))
                for name, (_, diagnostic) in FATAL.items():
                    binary = root / f'{backend}_{optimization}_{name}'
                    require_ok(run([args.clang, '-' + optimization, *flags, str(sources[(backend, name)]), *objects, *link_flags, '-o', str(binary)], root), 'fatal link ' + name)
                    executed = run([str(binary)], root, env=sanitizer_env())
                    assert executed.returncode > 0 and diagnostic in executed.stderr and executed.stdout == '', (backend, optimization, name, executed)
                    assert 'runtime error:' not in executed.stderr and 'Sanitizer' not in executed.stderr, (backend, optimization, name, executed)
                    inventory.append((backend, optimization, name))
                print(f'PASS {backend} {optimization}: {len(LEGAL)} bigint oracle results, {len(POSITIVE)} positive and {len(FATAL)} controlled failures', flush=True)
    expected = {(backend, 'frontend', name) for backend in ('c', 'llvm') for name in NEGATIVE}
    expected |= {(backend, opt, name) for backend in ('c', 'llvm') for opt in optimizations for name in (*POSITIVE, *FATAL)}
    assert set(inventory) == expected and len(inventory) == len(expected)
    evidence = {'contracts': len(inventory), 'bigint_results_per_matrix': len(LEGAL), 'optimizations': optimizations, 'sanitized': args.sanitize, 'inventory': inventory}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(evidence, indent=2) + '\n')
    print(f'V3.5 arithmetic and bounds contracts: PASS ({len(inventory)} cases)', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
