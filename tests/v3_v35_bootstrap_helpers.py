#!/usr/bin/env python3
"""Verify the measured V4 host helpers require explicit compatibility selection.

The pinned bootstrap ledger demonstrated nine chr sites and one word_to_num
site. Ordinary source names and filenames grant no implicit helper capability.
Both backends execute the sized NUL/Unicode and floating conversion contract.
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

MODE = '--bootstrap-compat=v4-host-bootstrap-v1'
PROGRAM = '''task zero() -> word { give back chr(0); }
task main() {
    pilot nul = zero()
    pilot clone = nul
    say nul.length()
    say clone.length()
    say nul == ""
    say nul == chr(0)
    pilot bytes = ByteBuffer::new()
    bytes.write_word(clone)
    say bytes.length()
    say bytes.read_byte()
    bytes.release()
    say chr(38634)
    pilot decimal = "12" + ".5"
    say word_to_num(decimal)
    say word_to_num("-1.25")
}
'''
EXPECTED = '1\n1\nfalse\ntrue\n1\n0\n雪\n12.5\n-1.25\n'
NEGATIVE = {
    'ordinary_chr': ('task main() { say chr(0); }', "unknown callable 'chr'", False),
    'ordinary_num': ('task main() { say word_to_num("1.5"); }', "unknown callable 'word_to_num'", False),
    'matching_filename': ('task main() { say chr(0); }', "unknown callable 'chr'", False),
    'chr_type': ('task main() { say chr("zero"); }', 'argument 1 expects int, got word', True),
    'chr_arity': ('task main() { say chr(); }', 'expects 1 argument(s), got 0', True),
    'num_type': ('task main() { say word_to_num(1); }', 'argument 1 expects word, got int', True),
    'num_arity': ('task main() { say word_to_num("1", "2"); }', 'expects 1 argument(s), got 2', True),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', type=Path)
    parser.add_argument('--clang', default=os.environ.get('FREAK_CLANG') or shutil.which('clang'))
    parser.add_argument('--optimization', choices=('O0', 'O2', 'O3'), default='O2')
    parser.add_argument('--sanitize', action='store_true')
    args=parser.parse_args()
    assert args.clang, 'Clang required'
    repo=Path(__file__).resolve().parents[1]
    runtime=repo/'freakc/runtime'
    inventory=[]
    with tempfile.TemporaryDirectory(prefix='freak-v35-bootstrap-helpers-') as directory:
        root=Path(directory)
        compiler=args.compiler.resolve(strict=True) if args.compiler else build_stage2(clang=args.clang,repo=repo,root=root)
        for backend in ('c','llvm'):
            suffix='.c' if backend=='c' else '.ll'
            for name,program,expected,profile in (
                ('explicit',PROGRAM,EXPECTED,True),
                ('ordinary_user_definition','task chr(value: int) -> int { give back value + 1; } task main() { say chr(1); }','2\n',False),
            ):
                source=root/f'{backend}_{name}.fk'
                source.write_text(program,encoding='utf-8')
                command=[str(compiler),str(source),'--'+backend]+([MODE] if profile else [])
                require_ok(run(command,root),'helper emission '+name)
                emitted=Path(str(source)+suffix)
                binary=root/f'{backend}_{name}'
                command=[args.clang,'-'+args.optimization,'-g','-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1','-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1','-o',str(binary),str(emitted)]
                if backend=='llvm':
                    command.append(str(runtime/'freak_llvm_runtime.c'))
                command.extend([str(runtime/'freak_runtime.c'),'-I',str(runtime)])
                command.extend(['-lws2_32'] if sys.platform=='win32' else ['-lm'])
                if args.sanitize:
                    command.extend(['-fsanitize=address,undefined','-fno-omit-frame-pointer'])
                require_ok(run(command,root),'helper link '+name)
                executed=run([str(binary)],root,env=sanitizer_env())
                require_ok(executed,'helper execution '+name)
                assert executed.stdout==expected and executed.stderr=='',(backend,name,executed)
                inventory.append((backend,name))
                print('PASS',backend,name,flush=True)
            for name,(program,diagnostic,profile) in NEGATIVE.items():
                if name=='matching_filename':
                    source=root/f'{backend}/src/compiler/v4/crates/freak_codegen_llvm/src/lib.fk'
                    source.parent.mkdir(parents=True)
                else:
                    source=root/f'{backend}_{name}.fk'
                source.write_text(program)
                artifact=Path(str(source)+suffix)
                artifact.write_text('stale helper output')
                rejected=run([str(compiler),str(source),'--'+backend]+([MODE] if profile else []),root)
                assert rejected.returncode!=0 and diagnostic in rejected.stdout+rejected.stderr,(backend,name,diagnostic,rejected)
                assert not artifact.exists(),(backend,name,'stale artifact survived')
                inventory.append((backend,name))
                print('PASS',backend,name,flush=True)
    expected={(backend,name) for backend in ('c','llvm') for name in ('explicit','ordinary_user_definition',*NEGATIVE)}
    assert len(inventory)==len(expected) and set(inventory)==expected
    print(f'V3.5 bootstrap helper contracts: PASS ({len(inventory)} cases)',flush=True)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
