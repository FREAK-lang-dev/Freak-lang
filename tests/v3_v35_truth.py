#!/usr/bin/env python3
"""Verify every truth-literal capitalization and standalone give/back reservation."""
from __future__ import annotations

import argparse
import itertools
import os
from pathlib import Path
import shutil
import sys
import tempfile

from v3_checked_parsing import build_stage2, run, sanitizer_env
from v3_v35_language import require_ok


def capitalizations(spelling: str) -> list[str]:
    return [''.join(chars) for chars in itertools.product(*((char, char.upper()) for char in spelling))]


SPELLINGS = [(variant, value) for literal, value in (('true', True), ('false', False), ('yes', True), ('no', False), ('hai', True), ('iie', False)) for variant in capitalizations(literal)]
PROGRAM = 'task main() {\n' + ''.join(f'    say {literal};\n' for literal, _ in SPELLINGS) + '}\n'
EXPECTED = ''.join(('true' if value else 'false') + '\n' for _, value in SPELLINGS)
PLATFORM_PROGRAM = 'task inspect(value: bool) -> bool { give back value; } task main() { pilot windows = process::platform_is_windows(); say inspect(windows); say windows; }\n'
COPY_PROGRAM = 'task inspect(value: bool) -> bool { give back value; } task main() { pilot truth = TrUe; say inspect(truth); say inspect(truth); say truth; when truth { HaI -> say "alias"; _ -> say "wrong"; } give\nback; }\n'
NEGATIVE = {f'reserved_{name}': f'task main() {{ pilot {name} = 1; }}\n' for name in ('give', 'back', 'Give', 'BACK')}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', type=Path)
    parser.add_argument('--clang', default=os.environ.get('FREAK_CLANG') or shutil.which('clang'))
    args = parser.parse_args()
    assert args.clang, 'Clang required'
    repo = Path(__file__).resolve().parents[1]
    runtime = repo / 'freakc/runtime'
    with tempfile.TemporaryDirectory(prefix='freak-v35-truth-') as directory:
        root = Path(directory)
        compiler = args.compiler.resolve(strict=True) if args.compiler else build_stage2(clang=args.clang, repo=repo, root=root)
        for backend in ('c', 'llvm'):
            suffix = '.c' if backend == 'c' else '.ll'
            for name, program, expected in (('capitalizations', PROGRAM, EXPECTED), ('copied_alias_and_return', COPY_PROGRAM, 'true\ntrue\ntrue\nalias\n'), ('native_platform_predicate', PLATFORM_PROGRAM, ('true\n' if sys.platform == 'win32' else 'false\n') * 2)):
                source = root / f'{name}_{backend}.fk'
                source.write_text(program)
                require_ok(run([str(compiler), str(source), '--' + backend, '--strict-borrow'], root), 'truth emission')
                binary = root / f'{name}_{backend}'
                units = [str(runtime / 'freak_runtime.c')]
                if backend == 'llvm':
                    units.append(str(runtime / 'freak_llvm_runtime.c'))
                flags = ['-O2', '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1', '-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1', '-I', str(runtime)]
                link_flags = ['-lws2_32'] if sys.platform == 'win32' else ['-lm']
                require_ok(run([args.clang, *flags, str(source) + suffix, *units, *link_flags, '-o', str(binary)], root), 'truth native link')
                executed = run([str(binary)], root, env=sanitizer_env())
                assert executed.returncode == 0 and executed.stdout == expected and not executed.stderr, (backend, name, executed)
            for name, program in NEGATIVE.items():
                source = root / f'{name}_{backend}.fk'
                source.write_text(program)
                artifact = Path(str(source) + suffix)
                artifact.write_text('stale truth output')
                result = run([str(compiler), str(source), '--' + backend], root)
                assert result.returncode != 0 and 'expected an identifier for binding name' in result.stdout + result.stderr, (backend, name, result)
                assert not artifact.exists(), (backend, name, 'stale artifact survived')
            print(f'PASS {backend}: all {len(SPELLINGS)} truth spellings, inferred bool copies and give/back reservation', flush=True)
    print('V3.5 truth contracts: PASS (14 programs, 76 truth spellings per backend)', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
