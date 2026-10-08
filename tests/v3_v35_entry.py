#!/usr/bin/env python3
"""Verify usable native entries, root execution and explicit call disposal."""
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

PROFILE = '--bootstrap-compat=v4-host-bootstrap-v1'
POSITIVE = {
    'void_entry': ('task main() { say "entry"; }', 'entry\n', 0, False),
    'int_entry': ('task main() -> int { say "entry"; give back 7; }', 'entry\n', 7, False),
    'ordered_globals': ('pilot first = 3\npilot second = first + 1\ntask main() { say second; }', '4\n', 0, False),
    'ignored_calls': ('task number() -> int { give back 1; } task text() -> word { give back "owned" + " result"; } task main() { number(); text(); "abc".length(); say "calls"; }', 'calls\n', 0, False),
    'bootstrap_root_and_main': ('pilot value = 1\nvalue += 1\npilot captured = value\nsay "root"\ntask main() { say captured; }', 'root\n2\n', 0, True),
    'bootstrap_root_entry': ('task hello() { say "root-entry"; }\nhello()', 'root-entry\n', 0, True),
}
NEGATIVE = {
    'missing_entry': ('task helper() {}', 'program requires a usable task main() entry'),
    'wrong_case': ('task Main() {}', 'program requires a usable task main() entry'),
    'empty': ('', 'no usable task main() entry'),
    'comments_only': ('-- comment only\n', 'program requires a usable task main() entry'),
    'entry_parameter': ('task main(value: int) {}', 'main must not declare parameters'),
    'entry_return': ('task main() -> word { give back "word"; }', 'main must return void or int'),
    'entry_extern': ('extern task main() -> int', 'main must be a task definition'),
    'root_say': ('say "skipped"\ntask main() {}', 'executable statement at top level is unsupported'),
    'root_call': ('task helper() {}\nhelper()\ntask main() {}', 'executable statement at top level is unsupported'),
    'root_assignment': ('pilot value = 1\nvalue = 2\ntask main() {}', 'executable statement at top level is unsupported'),
    'root_only': ('say "root"', 'program requires a usable task main() entry'),
    'stray_number': ('task main() { say 1 2; }', 'bare value is not a statement'),
    'stray_word': ('task main() { say "a" "b"; }', 'bare value is not a statement'),
    'stray_name': ('task main() { pilot value = 1; value; }', 'bare value is not a statement'),
    'stray_arithmetic': ('task main() { 1 + 2; }', 'bare value is not a statement'),
    'stray_index': ('task main() { "abc"[0]; }', 'bare value is not a statement'),
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
    optimizations = args.optimization or ['O2']
    flags = ['-g', '-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1', '-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1', '-I', str(runtime)]
    if args.sanitize:
        flags += ['-fsanitize=address,undefined', '-fno-omit-frame-pointer']
    link_flags = ['-lws2_32'] if sys.platform == 'win32' else ['-lm']
    inventory = []
    with tempfile.TemporaryDirectory(prefix='freak-v35-entry-') as directory:
        root = Path(directory)
        compiler = args.compiler.resolve(strict=True) if args.compiler else build_stage2(clang=args.clang, repo=repo, root=root)
        for backend in ('c', 'llvm'):
            suffix = '.c' if backend == 'c' else '.ll'
            for name, (program, diagnostic) in NEGATIVE.items():
                source = root / f'{name}_{backend}.fk'
                source.write_text(program + ('\n' if program else ''))
                artifact = Path(str(source) + suffix)
                artifact.write_text('stale entry output')
                result = run([str(compiler), str(source), '--' + backend], root)
                assert result.returncode != 0 and diagnostic in result.stdout + result.stderr, (backend, name, result)
                assert not artifact.exists(), (backend, name, 'stale artifact survived')
                inventory.append((backend, 'frontend', name))
            # A matching bootstrap filename conveys no compatibility authority.
            source = root / 'freak_driver.fk'
            source.write_text(POSITIVE['bootstrap_root_entry'][0])
            result = run([str(compiler), str(source), '--' + backend], root)
            assert result.returncode != 0 and 'program requires a usable task main() entry' in result.stdout + result.stderr
            assert not Path(str(source) + suffix).exists()
            inventory.append((backend, 'frontend', 'filename_has_no_authority'))
            for optimization in optimizations:
                for name, (program, expected, status, profile) in POSITIVE.items():
                    source = root / f'{optimization}_{name}_{backend}.fk'
                    source.write_text(program + '\n')
                    command = [str(compiler), str(source), '--' + backend]
                    if profile:
                        command.append(PROFILE)
                    else:
                        command.append('--strict-borrow')
                    require_ok(run(command, root), 'entry emission ' + name)
                    binary = root / f'{optimization}_{name}_{backend}'
                    units = [str(runtime / 'freak_runtime.c')]
                    if backend == 'llvm':
                        units.append(str(runtime / 'freak_llvm_runtime.c'))
                    require_ok(run([args.clang, '-' + optimization, *flags, str(source) + suffix, *units, *link_flags, '-o', str(binary)], root), 'entry link ' + name)
                    result = run([str(binary)], root, env=sanitizer_env())
                    assert result.returncode == status and result.stdout == expected and not result.stderr, (backend, optimization, name, result)
                    inventory.append((backend, optimization, name))
            print('PASS ' + backend + ' usable entries, root guards and call disposal', flush=True)
    evidence = {'contracts': len(inventory), 'optimizations': optimizations, 'sanitized': args.sanitize, 'inventory': inventory}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(evidence, indent=2) + '\n')
    print(f'V3.5 entry contracts: PASS ({len(inventory)} cases)', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
