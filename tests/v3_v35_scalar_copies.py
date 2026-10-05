#!/usr/bin/env python3
"""Execute inferred ownership and resource returns from native type facts.

Inferred task, operator, method, field and indexed int/num/bool values may be
passed and aliased repeatedly. Owned word, List and ByteBuffer inputs still
move into ordinary task calls and are rejected on later use.
ByteBuffer task results retain the scalar ABI and transfer one explicit owner.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import shutil
import sys
import tempfile
from v3_checked_parsing import build_stage2, run, sanitizer_env
from v3_v35_language import require_ok

HELPERS = '''task keep_int(value: int) -> int { give back value; }
task keep_num(value: num) -> num { give back value; }
task keep_bool(value: bool) -> bool { give back value; }
'''
POSITIVE = {
    'inferred_task_return': ('task value() -> int { give back 7; } task main() { pilot n = value(); say keep_int(n); say keep_int(n); say n; }', '7\n7\n7\n'),
    'operators_and_aliases': ('task main() { pilot n = 1 + 2; pilot alias = n; pilot negative = -alias; say keep_int(n); say keep_int(alias); say keep_int(alias); say keep_int(negative); say keep_int(negative); }', '3\n3\n3\n-3\n-3\n'),
    'method_return': ('task main() { pilot text = "some" + " text"; pilot count = text.length(); pilot starts = text.starts_with("some"); say keep_int(count); say keep_int(count); say keep_bool(starts); say keep_bool(starts); say text; }', '9\n9\ntrue\ntrue\nsome text\n'),
    'list_projection': ('task main() { pilot values: List<int> = [4, 5]; pilot first = values[0]; say keep_int(first); say keep_int(first); say values[1]; }', '4\n4\n5\n'),
    'shape_projection': ('shape Box { value: int } task main() { pilot object = Box { value: 9 }; pilot field = object.value; say keep_int(field); say keep_int(field); say object.value; }', '9\n9\n9\n'),
    'bool_and_num_return': ('task decision() -> bool { give back true; } task decimal() -> num { give back 2.5; } task main() { pilot flag = decision(); pilot number = decimal(); pilot alias = number; say keep_bool(flag); say keep_bool(flag); say keep_num(number); say keep_num(alias); say keep_num(number); }', 'true\ntrue\n2.5\n2.5\n2.5\n'),
    'scoped_identity': ('task value() -> int { give back 3; } task main() { pilot n = value(); { pilot n = "owned" + " inner"; say n; } say keep_int(n); say keep_int(n); }', 'owned inner\n3\n3\n'),
    'buffer_direct_return': ('task make() -> ByteBuffer { give back ByteBuffer::new(); } task main() { pilot bytes = make(); say bytes.length(); bytes.release(); }', '0\n'),
    'buffer_local_return': ('task make() -> ByteBuffer { pilot bytes = ByteBuffer::new(); bytes.write_word("data"); give back bytes; } task main() { pilot bytes = make(); say bytes.length(); bytes.release(); }', '4\n'),
    'buffer_parameter_return': ('task forward(bytes: ByteBuffer) -> ByteBuffer { give back bytes; } task main() { pilot input = ByteBuffer::new(); input.write_byte(9); pilot output = forward(input); say output.length(); say output.read_byte(); output.release(); }', '1\n9\n'),
    'buffer_nested_return': ('task make() -> ByteBuffer { give back ByteBuffer::new(); } task forward() -> ByteBuffer { give back make(); } task main() { pilot bytes = forward(); say bytes.length(); bytes.release(); }', '0\n'),
}
NEGATIVE = {
    'owned_word_input': 'task take(value: word) -> int { give back value.length(); } task main() { pilot text = "owned" + " input"; pilot count = take(text); say text; }',
    'owned_list_input': 'task take(value: List<int>) -> int { give back value.length(); } task main() { pilot values: List<int> = [1]; pilot count = take(values); say values.length(); }',
    'owned_buffer_input': 'task take(value: ByteBuffer) -> int { value.release(); give back 0; } task main() { pilot bytes = ByteBuffer::new(); pilot count = take(bytes); bytes.length(); }',
    'owned_word_alias': 'task main() { pilot text = "owned" + " input"; pilot alias = text; say text; }',
    'owned_buffer_forward': 'task forward(bytes: ByteBuffer) -> ByteBuffer { give back bytes; } task main() { pilot input = ByteBuffer::new(); pilot output = forward(input); input.length(); output.release(); }',
}


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler',type=Path)
    parser.add_argument('--clang',default=os.environ.get('FREAK_CLANG') or shutil.which('clang'))
    parser.add_argument('--sanitize',action='store_true')
    args=parser.parse_args()
    assert args.clang,'Clang required'
    repo=Path(__file__).resolve().parents[1]
    runtime=repo/'freakc/runtime'
    inventory=[]
    with tempfile.TemporaryDirectory(prefix='freak-v35-copy-') as directory:
        root=Path(directory)
        compiler=args.compiler.resolve(strict=True) if args.compiler else build_stage2(clang=args.clang,repo=repo,root=root)
        for backend in ('c','llvm'):
            suffix='.c' if backend=='c' else '.ll'
            for name,(program,expected) in POSITIVE.items():
                source=root/f'{backend}_{name}.fk'
                source.write_text(HELPERS+program+'\n')
                require_ok(run([str(compiler),str(source),'--'+backend,'--strict-borrow'],root),'scalar Copy emission '+name)
                binary=root/f'{backend}_{name}'
                command=[args.clang,'-O2','-g','-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1','-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1','-o',str(binary),str(source)+suffix]
                if backend=='llvm':
                    command.append(str(runtime/'freak_llvm_runtime.c'))
                command.extend([str(runtime/'freak_runtime.c'),'-I',str(runtime)])
                command.extend(['-lws2_32'] if sys.platform=='win32' else ['-lm'])
                if args.sanitize:
                    command.extend(['-fsanitize=address,undefined','-fno-omit-frame-pointer'])
                require_ok(run(command,root),'scalar Copy link '+name)
                executed=run([str(binary)],root,env=sanitizer_env())
                require_ok(executed,'scalar Copy execution '+name)
                assert executed.stdout==expected and executed.stderr=='',(backend,name,executed)
                inventory.append((backend,name))
                print('PASS',backend,name,flush=True)
            for name,program in NEGATIVE.items():
                source=root/f'{backend}_{name}.fk'
                source.write_text(program+'\n')
                artifact=Path(str(source)+suffix)
                artifact.write_text('stale scalar Copy output')
                rejected=run([str(compiler),str(source),'--'+backend,'--strict-borrow'],root)
                assert rejected.returncode!=0 and 'You gave this away' in rejected.stdout+rejected.stderr,(backend,name,rejected)
                assert not artifact.exists(),(backend,name,'stale artifact survived')
                inventory.append((backend,name))
                print('PASS',backend,name,flush=True)
    expected={(backend,name) for backend in ('c','llvm') for name in (*POSITIVE,*NEGATIVE)}
    assert set(inventory)==expected and len(inventory)==len(expected)
    print(f'V3.5 scalar Copy contracts: PASS ({len(inventory)} cases)',flush=True)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
