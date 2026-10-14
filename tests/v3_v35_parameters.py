#!/usr/bin/env python3
"""Execute adversarial parameter names, shadowed owners and returned values."""
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
    'entry_label': ('task choose(entry: int) -> int { give back entry + 1; } task main() { say choose(4); }', '5\n'),
    'argument_prefix': ('task choose(x: int, arg_x: int) -> int { give back x + arg_x; } task main() { say choose(4, 8); }', '12\n'),
    'register_and_local_prefixes': ('task choose(r0: int, binding_local_1: int, checked_owner_3: int) -> int { pilot value = r0 + binding_local_1 + checked_owner_3; give back value; } task main() { say choose(1, 2, 3); }', '6\n'),
    'returned_word_parameter': ('task choose(entry: word) -> word { give back entry; } task main() { say choose("owned" + " parameter"); }', 'owned parameter\n'),
    'word_argument_prefix': ('task choose(x: word, arg_x: word) -> word { give back x + arg_x; } task main() { say choose("first" + " ", "second" + " owner"); }', 'first second owner\n'),
    'shadowed_word_parameter': ('task choose(entry: word) -> word { if true { pilot entry = entry + " inner"; give back entry; } give back entry; } task main() { say choose("outer" + " owner"); }', 'outer owner inner\n'),
    'global_return_with_word_parameters': ('pilot global = "global" + " owner"\ntask choose(first: word, second: word) -> word { say first; say second; give back global + ""; } task main() { say choose("first" + " owner", "second" + " owner"); say global; }', 'first owner\nsecond owner\nglobal owner\nglobal owner\n'),
    'bare_global_return_with_word_parameters': ('pilot global = "global" + " owner"\ntask choose(first: word, second: word) -> word { say first; say second; give back global; } task main() { say choose("first" + " owner", "second" + " owner"); }', 'first owner\nsecond owner\nglobal owner\n'),
    'owned_list_parameter': ('task choose(entry: List<int>, arg_entry: int) -> int { give back entry[0] + arg_entry; } task main() { pilot values: List<int> = [4]; say choose(values, 3); }', '7\n'),
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
    with tempfile.TemporaryDirectory(prefix='freak-v35-parameters-') as directory:
        root = Path(directory)
        compiler = args.compiler.resolve(strict=True) if args.compiler else build_stage2(clang=args.clang, repo=repo, root=root)
        for backend in ('c', 'llvm'):
            suffix = '.c' if backend == 'c' else '.ll'
            objects = []
            for unit in ('freak_runtime.c', 'freak_llvm_runtime.c'):
                if unit == 'freak_llvm_runtime.c' and backend == 'c':
                    continue
                obj = root / f'{backend}_{unit}.o'
                require_ok(run([args.clang, *flags, '-c', str(runtime / unit), '-o', str(obj)], root), 'parameter runtime')
                objects.append(str(obj))
            for name, (program, expected) in POSITIVE.items():
                source = root / f'{name}_{backend}.fk'
                source.write_text(program + '\n')
                require_ok(run([str(compiler), str(source), '--' + backend, '--strict-borrow'], root), 'parameter emission ' + name)
                binary = root / f'{name}_{backend}'
                require_ok(run([args.clang, *flags, str(source) + suffix, *objects, *link_flags, '-o', str(binary)], root), 'parameter link ' + name)
                result = run([str(binary)], root, env=sanitizer_env())
                assert result.returncode == 0 and result.stdout == expected and not result.stderr, (backend, name, result)
            print(f'PASS {backend}: parameter collisions, owner shadows and returned values', flush=True)
    print(f'V3.5 parameter contracts: PASS ({len(POSITIVE) * 2} native programs)', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
