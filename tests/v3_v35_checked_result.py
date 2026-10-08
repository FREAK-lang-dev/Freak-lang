#!/usr/bin/env python3
"""Execute the closed checked-read result with exact-source native candidates.

Both native backends must select success/error explicitly and release each
carrier and cloned arm word on normal exits, returns and loop control. Native
ownership-audit negative controls establish that an omitted release is visible.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import sys
import tempfile

from v3_checked_parsing import build_stage2, sanitizer_env, run
from v3_v35_language import require_ok

PREAMBLE = 'extern task freak_fs_result_live() -> int\n'
POSITIVE = {
    'ordinary_r_shape': (
        'shape r { value: int } task main() { pilot value: r = r { value: 42 }; say value.value; say freak_fs_result_live(); }',
        '42\n0\n',
    ),
    'profile_top_level_match': (
        'check result fs::read_checked("unicode") { ok(text) -> { say text; } err(error) -> { panic(error); } } say freak_fs_result_live();',
        'snow 雪\n0\n',
    ),
    'named_repeat_and_scope': (
        'task main() { pilot text = "outer"; { pilot read = fs::read_checked("unicode"); '
        'check result read { ok(text) -> { say text; } err(error) -> { panic(error); } }; '
        'check result read { err(error) -> { panic(error); } ok(text) -> { say text; } }; } '
        'say text; say freak_fs_result_live(); }',
        'snow 雪\nsnow 雪\nouter\n0\n',
    ),
    'inline_return_and_error': (
        'task text(path: word) -> word { check result fs::read_checked(path) { '
        'ok(text) -> { give back text; } err(error) -> { if error.length() == 0 { panic("empty error"); } '
        'give back "missing"; } } }\n'
        'task main() { say text("unicode"); say text("absent"); say freak_fs_result_live(); }',
        'snow 雪\nmissing\n0\n',
    ),
    'empty_success': (
        'task main() { check result fs::read_checked("empty") { '
        'ok(text) -> { say text.length(); } err(error) -> { panic(error); } } '
        'check result fs::read_checked("absent") { ok(text) -> { panic("missing succeeded"); } '
        'err(error) -> { say error.length() > 0; } } say freak_fs_result_live(); }',
        '0\ntrue\n0\n',
    ),
    'raw_source_sized_word': (
        'task main() { check result fs::read_checked("raw") { ok(text) -> { '
        'pilot bytes = ByteBuffer::new(); bytes.write_word(text); say bytes.length(); '
        'say bytes.read_byte(); say bytes.read_byte(); say bytes.read_byte(); bytes.release(); } '
        'err(error) -> { panic(error); } } say freak_fs_result_live(); }',
        '3\n97\n0\n255\n0\n',
    ),
    'inline_loop_control': (
        'task main() { repeat 1000 times with i { check result fs::read_checked("unicode") { '
        'ok(text) -> { if i < 999 { continue; } say text; break; } '
        'err(error) -> { panic(error); } } } say freak_fs_result_live(); }',
        'snow 雪\n0\n',
    ),
    'local_return_and_unused_owner': (
        'task text() -> word { pilot read = fs::read_checked("unicode"); '
        'check result read { ok(text) -> { give back text; } err(error) -> { give back error; } } }\n'
        'task main() { { pilot unused = fs::read_checked("unicode"); } '
        'fs::read_checked("unicode"); say text(); say freak_fs_result_live(); }',
        'snow 雪\n0\n',
    ),
}
NEGATIVE = {
    'reserved_carrier_shape': ('shape CheckedReadResult { value: int } task main() {}', "conflicts with a built-in type", False),
    'alias': ('task main() { pilot a = fs::read_checked("unicode"); pilot b = a; }', 'aliases, annotations and global storage are unsupported', False),
    'reassign': ('task main() { pilot mut a = fs::read_checked("unicode"); a = fs::read_checked("unicode"); }', 'checked read result cannot be reassigned or stored', False),
    'global': ('pilot a = fs::read_checked("unicode"); task main() {}', 'aliases, annotations and global storage are unsupported', False),
    'annotation': ('task main() { pilot a: CheckedReadResult = fs::read_checked("unicode"); }', 'aliases, annotations and global storage are unsupported', False),
    'parameter': ('task use_result(a: CheckedReadResult) {} task main() {}', "unknown or non-value type 'CheckedReadResult'", False),
    'return_type': ('task read_result() -> CheckedReadResult { give back fs::read_checked("unicode"); } task main() {}', "unknown return type 'CheckedReadResult'", False),
    'list': ('task main() { pilot a = [fs::read_checked("unicode")]; }', 'checked read result cannot be passed or stored', False),
    'raw_any_call': ('task main() { pilot a = fs::read_checked("unicode"); array_push(array_new(), a); }', 'checked read result cannot be passed or stored', False),
    'equality': ('task main() { pilot a = fs::read_checked("unicode"); say a == a; }', "operator '==' does not accept CheckedReadResult and CheckedReadResult", False),
    'target': ('task main() { check result 1 { ok(text) -> {} err(error) -> {} } }', 'check result target must be a checked read result', False),
    'missing_arm': ('task main() { check result fs::read_checked("unicode") { ok(text) -> {} } }', 'requires exactly one ok arm and one err arm', False),
    'duplicate_arm': ('task main() { check result fs::read_checked("unicode") { ok(text) -> {} ok(other) -> {} err(error) -> {} } }', 'duplicate ok arm', False),
    'path_type': ('task main() { pilot a = fs::read_checked(1); }', 'argument 1 expects word, got int', False),
    'arm_escape': ('task main() { check result fs::read_checked("unicode") { ok(text) -> {} err(error) -> {} } say text; }', "unknown binding 'text'", False),
    'sibling_scope': ('task main() { check result fs::read_checked("unicode") { ok(text) -> {} err(error) -> { say text; } } }', "unknown binding 'text'", False),
    'arm_duplicate_local': ('task main() { check result fs::read_checked("unicode") { ok(text) -> { pilot text = "alias"; } err(error) -> {} } }', "duplicate binding 'text'", False),
    'partial_return': ('task text() -> word { check result fs::read_checked("unicode") { ok(text) -> { give back text; } err(error) -> {} } } task main() {}', 'may finish without giving back word', False),
    'strict_payload_move': ('task main() { check result fs::read_checked("unicode") { ok(text) -> { pilot moved = text; say text; } err(error) -> {} } }', 'You gave this away', True),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', type=Path, help='fresh exact-source native stage2 compiler')
    parser.add_argument('--clang', default=os.environ.get('FREAK_CLANG') or shutil.which('clang'))
    parser.add_argument('--optimization', choices=('O0', 'O2', 'O3'), default='O2')
    parser.add_argument('--sanitize', action='store_true', help='ASan/UBSan generated programs')
    parser.add_argument('--case', choices=tuple(POSITIVE) + tuple(NEGATIVE))
    parser.add_argument('--positive-only', action='store_true', help='execute only positive runtime cases for optimization/sanitizer parity')
    args = parser.parse_args()
    assert args.clang, 'Clang required'
    repo = Path(__file__).resolve().parents[1]
    runtime = repo / 'freakc/runtime'
    cases = []
    with tempfile.TemporaryDirectory(prefix='freak-v35-result-') as directory:
        root = Path(directory)
        (root/'unicode').write_text('snow 雪', encoding='utf-8')
        (root/'empty').write_bytes(b'')
        (root/'raw').write_bytes(b'a\x00\xff')
        compiler = args.compiler.resolve(strict=True) if args.compiler else build_stage2(clang=args.clang, repo=repo, root=root)
        for backend in ('c', 'llvm'):
            suffix = '.c' if backend == 'c' else '.ll'
            for name, (program, expected) in POSITIVE.items():
                if args.case and name != args.case:
                    continue
                source = root/f'{backend}_{name}.fk'
                source.write_text(PREAMBLE + program + '\n', encoding='utf-8')
                compile_command = [str(compiler), str(source), '--'+backend]
                if name == 'profile_top_level_match':
                    compile_command.append('--bootstrap-compat=v4-host-bootstrap-v1')
                require_ok(run(compile_command, root), 'emit '+name)
                generated = Path(str(source)+suffix)
                emitted = generated.read_text()
                if 'fs::read_checked' in program:
                    assert 'freak_fs_read_source_ticket(' in emitted if backend == 'c' else 'call i64 @freak_llvm_fs_read_source_ticket(' in emitted
                binary = root/f'{backend}_{name}'
                command = [args.clang, '-'+args.optimization, '-g', '-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1', '-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1', '-o', str(binary), str(generated)]
                if backend == 'llvm':
                    command.append(str(runtime/'freak_llvm_runtime.c'))
                command.extend([str(runtime/'freak_runtime.c'), '-I', str(runtime)])
                command.extend(['-lws2_32'] if sys.platform == 'win32' else ['-lm'])
                if args.sanitize:
                    command.extend(['-fsanitize=address,undefined', '-fno-omit-frame-pointer'])
                require_ok(run(command, root), 'link '+name)
                executed = run([str(binary)], root, env=sanitizer_env())
                require_ok(executed, 'execute '+name)
                assert executed.stdout == expected and executed.stderr == '', (backend, name, expected, executed)
                cases.append((backend,name))
                print('PASS',backend,name,flush=True)
            for name, (program, diagnostic, strict) in NEGATIVE.items():
                if args.positive_only:
                    continue
                if args.case and name != args.case:
                    continue
                source=root/f'{backend}_{name}.fk'
                source.write_text(program+'\n')
                artifact=Path(str(source)+suffix)
                artifact.write_text('stale result output')
                command=[str(compiler),str(source),'--'+backend]
                if strict:
                    command.append('--strict-borrow')
                rejected=run(command,root)
                assert rejected.returncode != 0 and diagnostic in rejected.stdout+rejected.stderr,(backend,name,diagnostic,rejected)
                assert not artifact.exists(),(backend,name,'stale artifact survived')
                cases.append((backend,name))
                print('PASS',backend,name,flush=True)
            if not args.case and not args.positive_only:
                # This deliberately omits a scalar ticket release. The audit
                # must reject it, establishing the positive ownership oracle.
                source=root/f'{backend}_leak_control.fk'
                source.write_text('task main() { fs::read_source_ticket("unicode"); }\n')
                require_ok(run([str(compiler),str(source),'--'+backend],root),'leak control emission')
                binary=root/f'{backend}_leak_control'
                command=[args.clang,'-'+args.optimization,'-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1','-o',str(binary),str(source)+suffix]
                if backend=='llvm':
                    command.append(str(runtime/'freak_llvm_runtime.c'))
                command.extend([str(runtime/'freak_runtime.c'),'-I',str(runtime)])
                command.extend(['-lws2_32'] if sys.platform=='win32' else ['-lm'])
                require_ok(run(command,root),'leak control link')
                control=run([str(binary)],root)
                assert control.returncode == 1 and 'live filesystem result(s)' in control.stderr,(backend,control)
                cases.append((backend,'leak_control'))
                print('PASS',backend,'leak_control',flush=True)
    names=(args.case,) if args.case else (tuple(POSITIVE) if args.positive_only else (*POSITIVE,*NEGATIVE,'leak_control'))
    expected={(backend,name) for backend in ('c','llvm') for name in names}
    assert len(cases)==len(expected) and set(cases)==expected
    print(f'V3.5 checked-result contracts: PASS ({len(cases)} cases)',flush=True)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
