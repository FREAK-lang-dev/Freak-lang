#!/usr/bin/env python3
"""Execute scalar LLVM runtime aliases with the real C operations and owners."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import shutil
import sys
import tempfile
from v3_checked_parsing import build_stage2, run, sanitizer_env
from v3_v35_language import require_ok

PROGRAM = r'''
extern task freak_word_compare(left: word, right: word) -> int

task main() {
    pilot selected = process::arg(1)
    pilot path = process::arg(2)
    if selected == "io" {
        fs::write(path, "first" + char_to_word(0))
        fs::append(path, "second")
        if not fs::exists(path) { panic("written file missing"); }
        pilot contents: word = fs::read(path)
        if contents.length() != 12 or contents[5] != char_to_word(0) or contents.substring(6, 12) != "second" { panic("legacy IO lost sized content"); }
        if not fs::delete(path) or fs::exists(path) or not fs::delete(path) { panic("delete did not preserve file semantics"); }
        say "io-ok"
    } else if selected == "compare" {
        if freak_word_compare("a" + "", "b" + "") != -1 { panic("comparison order"); }
        if freak_word_compare("é" + "", "a" + "") != 1 { panic("UTF8 order"); }
        if freak_word_compare("a" + char_to_word(0) + "suffix", "a" + "") != 0 { panic("legacy NUL-prefix comparison changed"); }
        say "compare-ok"
    } else if selected == "missing-read" {
        fs::read(path)
        panic("missing read returned")
    } else if selected == "directory-write" {
        fs::write(path, "content")
        panic("directory write returned")
    } else if selected == "directory-append" {
        fs::append(path, "content")
        panic("directory append returned")
    } else if selected == "nul-path-read" {
        fs::read(path + char_to_word(0) + "suffix")
        panic("NUL read path returned")
    } else if selected == "nul-path-write" {
        fs::write(path + char_to_word(0) + "suffix", "changed")
        panic("NUL write path returned")
    } else if selected == "directory-delete" {
        if fs::delete(path) or not fs::exists(path) { panic("delete consumed directory"); }
        say "directory-preserved"
    }
}
'''


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler',type=Path)
    parser.add_argument('--runtime',type=Path)
    parser.add_argument('--clang',default=os.environ.get('FREAK_CLANG') or shutil.which('clang'))
    args=parser.parse_args();assert args.clang
    repo=Path(__file__).resolve().parents[1]
    runtime=args.runtime.resolve(strict=True) if args.runtime else repo/'freakc/runtime'
    flags=['-O2','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1','-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1','-I',str(runtime)]
    links=['-lws2_32'] if sys.platform=='win32' else ['-lm']
    with tempfile.TemporaryDirectory(prefix='freak-v35-runtime-aliases-') as directory:
        root=Path(directory)
        compiler=args.compiler.resolve(strict=True) if args.compiler else build_stage2(clang=args.clang,repo=repo,root=root)
        for backend in ('c','llvm'):
            source=root/f'consumer_{backend}.fk';source.write_text(PROGRAM)
            require_ok(run([str(compiler),str(source),'--'+backend,'--strict-borrow'],root),'alias consumer emission '+backend)
            suffix='.c' if backend=='c' else '.ll';emitted=Path(str(source)+suffix).read_text()
            if backend=='llvm':
                for name in ('read','write','append','exists','delete'):
                    assert any('call ' in line and '@freak_llvm_fs_'+name+'_native(' in line for line in emitted.splitlines()),name
                assert 'call i64 @freak_llvm_word_compare(' in emitted and '@freak_word_compare(' not in emitted
            objects=[]
            for unit in ('freak_runtime.c','freak_llvm_runtime.c'):
                if unit=='freak_llvm_runtime.c' and backend=='c':continue
                obj=root/f'{backend}_{unit}.o';require_ok(run([args.clang,*flags,'-c',str(runtime/unit),'-o',str(obj)],root),'alias runtime');objects.append(str(obj))
            binary=root/f'consumer_{backend}'
            require_ok(run([args.clang,*flags,str(source)+suffix,*objects,*links,'-o',str(binary)],root),'alias native link '+backend)
            # Controlled process termination cannot run lexical owner cleanup.
            # Successful routes above keep both ownership audits enabled.
            fatal_flags=[flag for flag in flags if not flag.startswith('-DFREAK_')]
            fatal_objects=[]
            for unit in ('freak_runtime.c','freak_llvm_runtime.c'):
                if unit=='freak_llvm_runtime.c' and backend=='c':continue
                obj=root/f'{backend}_fatal_{unit}.o';require_ok(run([args.clang,*fatal_flags,'-c',str(runtime/unit),'-o',str(obj)],root),'fatal alias runtime');fatal_objects.append(str(obj))
            fatal_binary=root/f'consumer_{backend}_fatal'
            require_ok(run([args.clang,*fatal_flags,str(source)+suffix,*fatal_objects,*links,'-o',str(fatal_binary)],root),'fatal alias native link '+backend)
            ordinary=root/'source é.fk';ordinary.write_bytes(b'original')
            fixtures=[('io',ordinary,'io-ok'),('compare',ordinary,'compare-ok'),('directory-delete',root,'directory-preserved')]
            for name,path,marker in fixtures:
                result=run([str(binary),name,str(path)],root,env=sanitizer_env())
                assert result.returncode==0 and result.stdout==marker+'\n' and not result.stderr,(backend,name,result)
            ordinary.write_bytes(b'original')
            for name,path in [('missing-read',root/'missing'),('directory-write',root),('directory-append',root),('nul-path-read',ordinary),('nul-path-write',ordinary)]:
                result=run([str(fatal_binary),name,str(path)],root,env=sanitizer_env())
                assert result.returncode==1 and not result.stdout and 'FREAK: cannot ' in result.stderr and 'Sanitizer' not in result.stderr,(backend,name,result)
                assert ordinary.read_bytes()==b'original',(backend,name,'existing prefix changed')
            print(f'PASS {backend}: native scalar IO aliases, borrowed word compare, controlled legacy errors and directory preservation',flush=True)
    print('V3.5 runtime aliases: PASS (16 native contracts)',flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
