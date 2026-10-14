#!/usr/bin/env python3
"""Guard Word ordering, inline integer checks, and retained scalar timings.

The optional performance gate compares the same 300-million-iteration program
with freshly supplied before/after and v0.14.2 compilers. All generated sources,
binaries, commands, hashes, and timing samples remain in --output-dir.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import statistics
import sys
import tempfile
import time

from v3_checked_parsing import build_stage2, run, sanitizer_env
from v3_v35_language import require_ok

LOW, HIGH = -(1 << 63), (1 << 63) - 1
PAIRS = [('', ''), ('', 'a'), ('a', ''), ('a', 'aa'), ('apple', 'banana'),
         ('Z', 'a'), ('é', 'z')]
OPERATORS = ('<', '>', '<=', '>=')


def literal(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def compare(left: bytes, right: bytes, operator: str) -> bool:
    return {'<': left < right, '>': left > right,
            '<=': left <= right, '>=': left >= right}[operator]


ORDER_PROGRAM = 'task main() {\n' + ''.join(
    f'    say {literal(left)} {operator} {literal(right)};\n'
    for left, right in PAIRS for operator in OPERATORS) + '}\n'
ORDER_EXPECTED = ''.join(
    str(compare(left.encode(), right.encode(), operator)).lower() + '\n'
    for left, right in PAIRS for operator in OPERATORS)
POSITIVE = {
    'unused_ordinary_scalar_externs': (
        'extern task freak_int_fail(a: int, b: int) -> void\n'
        + ''.join(f'extern task freak_int_{op}_inline(a: int, b: int) -> void\n' for op in ('add', 'sub', 'mul', 'div', 'rem'))
        + 'extern task freak_int_neg_inline(value: int) -> void\n'
        'task main() { say 1 + 2; }', '3\n'),
    'word_byte_order': (ORDER_PROGRAM, ORDER_EXPECTED),
    'word_temporaries_once': (
        'pilot mut ticks = 0\n'
        'task make(value: word) -> word { ticks += 1; say ticks; give back value + ""; }\n'
        'task main() { say make("a") < make("b"); say make("ab") >= make("a"); '
        'say ("a" + "b") <= ("a" + "c"); }', '1\n2\ntrue\n3\n4\ntrue\ntrue\n'),
    'word_global_snapshot': (
        'pilot mut value = "a" + "a"\n'
        'task change() -> word { value = "z" + "z"; give back "ab" + ""; }\n'
        'task main() { say value < change(); say value; }', 'true\nzz\n'),
    'word_projections': (
        'shape Box { value: word } task main() { pilot box = Box { value: "ab" + "" }; '
        'pilot values: List<word> = ["ac" + ""]; say box.value < values[0]; '
        'say values[0] >= box.value; say box.value; say values[0]; }', 'true\ntrue\nab\nac\n'),
    'word_raw_bytes': (
        'task main() { check result fs::read_checked("raw-left.bin") { ok(left) -> { '
        'check result fs::read_checked("raw-right.bin") { ok(right) -> { '
        'say left < right; say left <= right; say right > left; say right >= left; '
        'say left > "z"; } err(error) -> { panic(error); } } '
        '} err(error) -> { panic(error); } } }', 'true\ntrue\ntrue\ntrue\ntrue\n'),
    'literal_divisors': (
        'task main() { pilot value = 14; say value % 7; say value / 00007; '
        'say value / -2; say value % (-00002); }', '0\n2\n-7\n0\n'),
    'dynamic_divisors': (
        'task divisor(value: int) -> int { say value; give back value; } '
        f'task main() {{ say ({LOW}) / divisor(1); say ({LOW}) % divisor(7); '
        'say 14 / divisor(-2); say 14 % divisor(-2); }', f'1\n{LOW}\n7\n-1\n-2\n-7\n-2\n0\n'),
    'minimum_literal_divisor': (
        f'task main() {{ say 1 / ({LOW}); say ({LOW}) / ({LOW}); '
        f'say ({LOW}) % ({LOW}); }}', '0\n1\n0\n'),
    'short_circuit_checks': (
        f'task main() {{ say false and (({HIGH} + 1) == 0); '
        'say true or ((1 / 0) == 0); say (1 + 2 == 3) and (8 / 2 == 4); }', 'false\ntrue\ntrue\n'),
    'global_initializer': ('pilot initial = 5 + 6\ntask main() { say initial; }', '11\n'),
}
# V3 rejects NUL literal escapes; checked file reads preserve arbitrary bytes.
raw_program = POSITIVE['word_raw_bytes'][0]
POSITIVE['word_raw_nul_tails'] = (raw_program.replace('raw-left.bin', 'nul-left.bin').replace('raw-right.bin', 'nul-right.bin'), 'true\ntrue\ntrue\ntrue\nfalse\n')
POSITIVE['word_raw_nul_prefix'] = (raw_program.replace('raw-left.bin', 'nul-prefix.bin').replace('raw-right.bin', 'nul-left.bin'), 'true\ntrue\ntrue\ntrue\nfalse\n')
FAILURES = {
    'add_order': (f'say next({HIGH}) + next(1);', 'overflow', 'addition'),
    'subtract_order': (f'say next({LOW}) - next(1);', 'overflow', 'subtraction'),
    'multiply_order': (f'say next({HIGH}) * next(2);', 'overflow', 'multiplication'),
    'divide_zero_order': ('say next(1) / next(0);', 'division by zero', 'division'),
    'remainder_zero_order': ('say next(1) % next(0);', 'division by zero', 'remainder'),
    'divide_overflow_order': (f'say next({LOW}) / next(-1);', 'overflow', 'division'),
    'remainder_overflow_order': (f'say next({LOW}) % next(-1);', 'overflow', 'remainder'),
    'literal_leading_zero': ('say next(1) / 0000;', 'division by zero', 'division'),
    'literal_negative_zero': ('say next(1) % (-0000);', 'division by zero', 'remainder'),
    'literal_negative_one': (f'say next({LOW}) / (-0001);', 'overflow', 'division'),
}
NEGATIVE = ('"a" < 1', '1 >= "a"', '"a" <= true', 'false > "a"')
LOOP = ('task main() {\n    pilot mut i = 0\n    pilot mut t = 0\n'
        '    repeat until i >= 300000000 {\n        t = t + i % 7\n        i += 1\n'
        '    }\n    say t\n}\n')


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', type=Path)
    parser.add_argument('--before-compiler', type=Path)
    parser.add_argument('--legacy-compiler', type=Path)
    parser.add_argument('--before-runtime', type=Path)
    parser.add_argument('--legacy-runtime', type=Path)
    parser.add_argument('--clang', default=os.environ.get('FREAK_CLANG') or shutil.which('clang'))
    parser.add_argument('--optimization', choices=('O0', 'O2', 'O3'), action='append')
    parser.add_argument('--sanitize', action='store_true')
    parser.add_argument('--performance-only', action='store_true')
    parser.add_argument('--samples', type=int, default=5)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    assert args.clang, 'Clang required'
    assert bool(args.before_compiler) == bool(args.legacy_compiler), 'supply both performance comparison compilers'
    if args.legacy_compiler:
        assert args.before_runtime and args.legacy_runtime, 'bind comparison binaries to their original runtimes'
    assert not args.performance_only or args.legacy_compiler, 'performance-only needs comparison compilers'
    assert args.samples >= 3, 'at least three timing samples required'
    assert not (args.sanitize and args.legacy_compiler), 'measure optimized unsanitized binaries'
    repo = Path(__file__).resolve().parents[1]
    runtime = repo / 'freakc/runtime'
    root = args.output_dir.resolve() if args.output_dir else Path(tempfile.mkdtemp(prefix='freak-v35-prerelease-scalars-'))
    root.mkdir(parents=True, exist_ok=True)
    evidence: dict = {'output_dir': str(root), 'commands': [], 'contracts': [], 'performance': {},
                      'inputs': {str(path.relative_to(repo)): digest(path) for path in
                                 [repo / 'src/compiler/v3/emit_c.fk', repo / 'src/compiler/v3/emit_llvm.fk',
                                  runtime / 'freak_runtime.c', runtime / 'freak_runtime.h']}}

    def checked(command: list[str], label: str, env: dict | None = None):
        evidence['commands'].append(command)
        result = run(command, root, env=env)
        require_ok(result, label)
        return result

    compiler = args.compiler.resolve(strict=True) if args.compiler else build_stage2(clang=args.clang, repo=repo, root=root)
    evidence['compiler'] = {'path': str(compiler), 'sha256': digest(compiler)}
    (root / 'raw-left.bin').write_bytes(b'\x80\0b')
    (root / 'raw-right.bin').write_bytes(b'\xff\0a')
    (root / 'nul-left.bin').write_bytes(b'a\0b')
    (root / 'nul-right.bin').write_bytes(b'a\0c')
    (root / 'nul-prefix.bin').write_bytes(b'a\0')
    flags = ['-g', '-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1', '-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1', '-I', str(runtime)]
    if args.sanitize:
        flags += ['-fsanitize=address,undefined', '-fno-omit-frame-pointer']
    libraries = ['-lws2_32'] if sys.platform == 'win32' else ['-lm']
    for backend in ('c', 'llvm'):
        suffix = '.c' if backend == 'c' else '.ll'
        if not args.performance_only:
            programs = dict(POSITIVE)
            for name, (body, reason, operation) in FAILURES.items():
                programs[name] = ('pilot mut ticks = 0\n'
                                  'task next(value: int) -> int { ticks += 1; say ticks; give back value; } '
                                  'task main() { ' + body + ' say "after"; }',
                                  '1\n' if name.startswith('literal_') else '1\n2\n')
            generated = {}
            for name, (program, _) in programs.items():
                source = root / f'{backend}_{name}.fk'
                source.write_text(program + '\n', encoding='utf-8')
                if name == 'word_byte_order':
                    fixture_bytes = source.read_bytes().replace(b'\r\n', b'\n')
                    assert fixture_bytes == (program + '\n').encode('utf-8'), (
                        'Word ordering fixture must reach the compiler as UTF-8')
                checked([str(compiler), str(source), '--' + backend, '--strict-borrow'], 'emit ' + name)
                artifact = Path(str(source) + suffix)
                text = artifact.read_text(encoding='utf-8')
                if backend == 'llvm':
                    assert not re.search(r'call i64 @freak_int_\w+_checked\(', text), (name, 'out-of-line checked arithmetic')
                    for function in re.findall(r'define .*?\n\}', text, flags=re.S):
                        assert function.count('\ninteger.fail:') <= 1, (name, 'duplicated failure block')
                    if name == 'literal_divisors':
                        assert ' = sdiv i64 ' in text and ' = srem i64 ' in text
                        assert '@__freak_int_division_by_zero, i64' not in text
                        assert not re.search(r'icmp eq i64 (?:7|-2), (?:0|-1)', text), text
                elif name == 'literal_divisors':
                    assert 'freak_int_div_inline(' not in text and 'freak_int_rem_inline(' not in text, text
                generated[name] = artifact
            for index, expression in enumerate(NEGATIVE):
                source = root / f'{backend}_mixed_word_{index}.fk'
                source.write_text('task main() { say ' + expression + '; }\n', encoding='utf-8')
                artifact = Path(str(source) + suffix)
                artifact.write_text('stale scalar output', encoding='utf-8')
                rejected = run([str(compiler), str(source), '--' + backend], root)
                assert rejected.returncode != 0 and 'does not accept' in rejected.stdout + rejected.stderr, rejected
                assert not artifact.exists(), 'stale mixed-word artifact survived'
                evidence['contracts'].append((backend, 'frontend', index))
            source = root / f'{backend}_unused_reserved_fail_extern.fk'
            source.write_text('extern task __freak_int_fail(a: int, b: int) -> void\ntask main() { say 1; }\n', encoding='utf-8')
            artifact = Path(str(source) + suffix)
            artifact.write_text('stale reserved helper output', encoding='utf-8')
            rejected = run([str(compiler), str(source), '--' + backend], root)
            assert rejected.returncode != 0 and 'reserved' in rejected.stdout + rejected.stderr, rejected
            assert not artifact.exists(), 'stale reserved helper artifact survived'
            evidence['contracts'].append((backend, 'frontend', 'unused_reserved_fail_extern'))
            for optimization in args.optimization or ['O0', 'O2', 'O3']:
                objects = []
                for unit in ('freak_runtime.c', 'freak_llvm_runtime.c'):
                    if backend == 'c' and unit == 'freak_llvm_runtime.c':
                        continue
                    obj = root / f'{backend}_{optimization}_{unit}.o'
                    checked([args.clang, '-' + optimization, *flags, '-c', str(runtime / unit), '-o', str(obj)], 'runtime ' + unit)
                    objects.append(str(obj))
                for name, (_, expected) in programs.items():
                    binary = root / f'{backend}_{optimization}_{name}'
                    checked([args.clang, '-' + optimization, *flags, str(generated[name]), *objects, *libraries, '-o', str(binary)], 'link ' + name)
                    result = run([str(binary)], root, env=sanitizer_env())
                    assert result.stdout == expected, (backend, optimization, name, result)
                    if name in FAILURES:
                        _, reason, operation = FAILURES[name]
                        assert result.returncode == 1 and result.stderr == f'FREAK: integer {reason} in {operation}\n', (backend, optimization, name, result)
                    else:
                        require_ok(result, 'execute ' + name)
                        assert not result.stderr, (name, result)
                    evidence['contracts'].append((backend, optimization, name))
                print(f'PASS scalars {backend} {optimization}: {len(programs)} native cases', flush=True)
        if args.legacy_compiler:
            binaries = {}
            for label, candidate in [('before', args.before_compiler), ('after', compiler), ('v0.14.2', args.legacy_compiler)]:
                candidate = candidate.resolve(strict=True)
                candidate_runtime = {'before': args.before_runtime, 'after': runtime, 'v0.14.2': args.legacy_runtime}[label].resolve(strict=True)
                source = root / f'performance_{backend}_{label}.fk'
                source.write_text(LOOP, encoding='utf-8')
                checked([str(candidate), str(source), '--' + backend], 'performance emit ' + label)
                binary = root / f'performance_{backend}_{label}'
                units = [str(candidate_runtime / 'freak_runtime.c')]
                if backend == 'llvm':
                    units.append(str(candidate_runtime / 'freak_llvm_runtime.c'))
                checked([args.clang, '-O2', '-I', str(candidate_runtime), str(source) + suffix, *units, *libraries, '-o', str(binary)], 'performance link ' + label)
                binaries[label] = binary
                evidence['performance'].setdefault(backend, {})[label] = {
                    'compiler': str(candidate), 'compiler_sha256': digest(candidate),
                    'runtime_inputs': {str(path.relative_to(candidate_runtime)): digest(path)
                                       for path in candidate_runtime.rglob('*') if path.is_file()},
                    'generated_sha256': digest(Path(str(source) + suffix)), 'binary_sha256': digest(binary), 'seconds': []}
                warm = checked([str(binary)], 'warm benchmark')
                assert warm.stdout == '899999997\n' and not warm.stderr, warm
            # Interleave samples so changes in host load affect each version.
            for sample in range(args.samples):
                labels = list(binaries)
                if sample % 2:
                    labels.reverse()
                for label in labels:
                    start = time.perf_counter()
                    measured = checked([str(binaries[label])], 'benchmark ' + label)
                    elapsed = time.perf_counter() - start
                    assert measured.stdout == '899999997\n' and not measured.stderr, measured
                    evidence['performance'][backend][label]['seconds'].append(elapsed)
            timings = evidence['performance'][backend]
            for record in timings.values():
                record['median_seconds'] = statistics.median(record['seconds'])
            timings['after_over_v0.14.2'] = timings['after']['median_seconds'] / timings['v0.14.2']['median_seconds']
            print(f"PERFORMANCE {backend}: before={timings['before']['median_seconds']:.3f}s after={timings['after']['median_seconds']:.3f}s v0.14.2={timings['v0.14.2']['median_seconds']:.3f}s ratio={timings['after_over_v0.14.2']:.3f}", flush=True)
    report = args.report or root / 'report.json'
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    for backend, timings in evidence['performance'].items():
        assert timings['after_over_v0.14.2'] <= 1.5, (backend, timings)
    print(f"V3.5 prerelease scalars: PASS ({len(evidence['contracts'])} contracts); evidence: {report}", flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
