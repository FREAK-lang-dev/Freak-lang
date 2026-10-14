#!/usr/bin/env python3
"""Execute pure lexical paths with native C/LLVM and independent Python oracles.

--compiler verifies the unchanged std/path.fk component with native stage2;
--freak verifies ordinary `use std::path` through the integrated public CLI.
--style-core-only is a development component gate before the native platform
predicate is integrated. It deliberately does not claim public API coverage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import ntpath
import os
from pathlib import Path
import posixpath
import random
import shutil
import subprocess
import tempfile


OPERATIONS = ('join', 'parent', 'name', 'extension', 'is_absolute', 'absolute')
AUDIT_CONTROL = r'''
#include "freak_runtime.h"
#include <stdlib.h>
int main(int count,char **arguments) {
    if(count!=2)return 70;
    char *owner=malloc(2);if(!owner)return 71;owner[0]='x';owner[1]=0;
    if(arguments[1][0]=='c')(void)freak_word_own(owner,1);
    else (void)freak_llvm_word_adopt_sized((int64_t)(intptr_t)owner,1);
    return 0;
}
'''
PROGRAM = r'''
task main() {
    pilot mut operation = process::arg(1)
    pilot style = process::arg(2)
    pilot windows = style == "windows"
    pilot mut value = process::arg(3)
    pilot mut base = process::arg(4)
    if operation.ends_with("-base-nul") {
        base = base + char_to_word(0) + "must-not-truncate"
        operation = operation.substring(0, operation.length() - 9)
    } else if operation.ends_with("-nul") {
        value = value + char_to_word(0) + "must-not-truncate"
        operation = operation.substring(0, operation.length() - 4)
    }
    if operation == "soak" {
        pilot source = "../λ/猫/./leaf.txt"
        repeat 200 times {
            pilot resolved = path_absolute_style(source.repeated(1), "/one/two", false)
            if resolved != "/one/λ/猫/leaf.txt" { panic("path soak bytes changed") }
            if source != "../λ/猫/./leaf.txt" { panic("path consumed retained source") }
        }
        say "RESULT:SOAK_OK"
        give back
    }
    if style == "native" {
        __NATIVE_DISPATCH__
    } else {
        if operation == "join" { say "RESULT:" + path_join_style(base.repeated(1), value.repeated(1), windows) }
        else if operation == "parent" { say "RESULT:" + path_parent_style(value.repeated(1), windows) }
        else if operation == "name" { say "RESULT:" + path_name_style(value.repeated(1), windows) }
        else if operation == "extension" { say "RESULT:" + path_extension_style(value.repeated(1), windows) }
        else if operation == "is_absolute" { say "RESULT:" + word_from_bool(path_is_absolute_style(value.repeated(1), windows)) }
        else if operation == "absolute" { say "RESULT:" + path_absolute_style(value.repeated(1), base.repeated(1), windows) }
        else { panic("unknown path fixture operation") }
    }
    -- The API receives explicit owned copies, so the caller keeps both words.
    if value == "__never__" or base == "__never__" { panic("unreachable") }
}
'''

NATIVE = r'''
        if operation == "join" { say "RESULT:" + path_join(base.repeated(1), value.repeated(1)) }
        else if operation == "parent" { say "RESULT:" + path_parent(value.repeated(1)) }
        else if operation == "name" { say "RESULT:" + path_name(value.repeated(1)) }
        else if operation == "extension" { say "RESULT:" + path_extension(value.repeated(1)) }
        else if operation == "is_absolute" { say "RESULT:" + word_from_bool(path_is_absolute(value.repeated(1))) }
        else if operation == "absolute" { say "RESULT:" + path_absolute(value.repeated(1), base.repeated(1)) }
        else { panic("unknown path fixture operation") }
'''


def run(command: list[str], *, cwd: Path, env: dict[str, str], timeout: int = 90):
    return subprocess.run(command, cwd=cwd, env=env, capture_output=True, timeout=timeout)


def cases() -> list[dict]:
    result: list[dict] = []

    def add(op, windows, value, base='', *, expected=None, error=None, oracle=None):
        result.append(dict(operation=op, windows=windows, value=value, base=base,
                           expected=expected, error=error, oracle=oracle))

    # The oracles operate independently on inputs, rather than reproducing the
    # Freak scanner/stack. Only agreed contracts are compared automatically.
    for windows, module, sep in ((False, posixpath, '/'), (True, ntpath, '\\')):
        roots = ['a', 'a'+sep+'b', 'λ'+sep+'猫', 'file space', 'literal%$&']
        if windows:
            roots += ['C:'+sep+'one'+sep+'two', '\\\\server\\share\\one\\two']
        else:
            roots += ['/one/two', 'one\\two']
        for value in roots:
            add('name', windows, value, expected=module.basename(value), oracle=module.__name__+'.basename')
            add('parent', windows, value, expected=module.dirname(value) or '.', oracle=module.__name__+'.dirname (empty => .)')
            for tail in ('txt', 'tar.gz', 'λ猫'):
                filename = value+'.'+tail
                add('extension', windows, filename, expected=module.splitext(module.basename(filename))[1], oracle=module.__name__+'.splitext')
        for base in ('', 'one', 'one'+sep, 'λ'+sep+'猫'):
            for leaf in ('', 'two', './two', '../two', 'λ 猫'):
                add('join', windows, leaf, base, expected=module.join(base, leaf), oracle=module.__name__+'.join')
        base = 'C:\\one\\two' if windows else '/one/two'
        rng = random.Random(731)
        for _ in range(40):
            parts = [rng.choice(('one', 'λ', '猫', '.', '..', 'file space', 'literal%$&')) for _ in range(rng.randrange(0, 7))]
            value = sep.join(parts)
            add('absolute', windows, value, base, expected=module.normpath(module.join(base, value)), oracle=module.__name__+'.normpath(join)')

    # Fixed vectors cover deliberate decisions outside Python's platform/version
    # conventions, especially qualified Windows roots and trailing separators.
    vectors = [
        ('name', False, '/one/λ/猫///', '', '猫'),
        ('parent', False, '/one/λ/猫///', '', '/one/λ'),
        ('name', False, '/one/.', '', '.'),
        ('name', False, '/one/..', '', '..'),
        ('join', False, '.././leaf', '/one//two', '/one//two/.././leaf'),
        ('name', False, 'a\\b', '', 'a\\b'),
        ('name', False, 'λ:x', '', 'λ:x'),
        ('extension', False, '.hidden', '', ''),
        ('extension', False, '..hidden', '', ''),
        ('extension', True, '..hidden', '', ''),
        ('extension', False, 'name.', '', ''),
        ('extension', False, '.hidden.tar', '', '.tar'),
        ('parent', False, '/', '', '/'),
        ('parent', False, '', '', '.'),
        ('name', False, '/', '', ''),
        ('absolute', False, '../../../../λ', '/one/two', '/λ'),
        ('absolute', False, '//one/../λ', '', '//λ'),
        ('absolute', False, '///one/../λ', '', '/λ'),
        ('absolute', False, 'λ/猫', '/base\\bytes', '/base\\bytes/λ/猫'),
        ('absolute', False, '~/$HOME', '/literal', '/literal/~/$HOME'),
        ('is_absolute', False, '\\one', '', 'false'),
        ('is_absolute', True, '\\one', '', 'false'),
        ('is_absolute', True, 'C:one', '', 'false'),
        ('is_absolute', True, 'C:', '', 'false'),
        ('is_absolute', True, 'C:\\one', '', 'true'),
        ('is_absolute', True, '\\\\server\\share', '', 'true'),
        ('parent', True, 'C:\\', '', 'C:\\'),
        ('parent', True, 'C:one', '', 'C:'),
        ('parent', True, '\\\\server\\share\\', '', '\\\\server\\share\\'),
        ('name', True, '\\\\server\\share', '', ''),
        ('name', True, 'C:\\one/λ\\猫\\\\', '', '猫'),
        ('join', True, '\\leaf', 'C:\\base', 'C:\\leaf'),
        ('join', True, '\\leaf', '\\\\server\\share\\base', '\\\\server\\share\\leaf'),
        ('join', True, 'c:leaf', 'C:\\base', 'C:\\base\\leaf'),
        ('join', True, 'D:\\leaf', 'C:\\base', 'D:\\leaf'),
        ('absolute', True, '\\λ\\猫', 'C:\\base', 'C:\\λ\\猫'),
        ('absolute', True, 'c:λ\\猫', 'C:\\base', 'C:\\base\\λ\\猫'),
        ('absolute', True, 'C:', 'C:\\base', 'C:\\base'),
        ('absolute', True, '..\\..\\..', 'C:\\base', 'C:\\'),
        ('absolute', True, '%USERPROFILE%\\$HOME', 'C:\\literal', 'C:\\literal\\%USERPROFILE%\\$HOME'),
        ('absolute', True, '..\\..\\..', '\\\\server\\share\\base', '\\\\server\\share\\'),
        ('absolute', True, '//server/share/one/../λ', '', '\\\\server\\share\\λ'),
    ]
    for op, windows, value, base, expected in vectors:
        add(op, windows, value, base, expected=expected)
    for windows in (False, True):
        for op in OPERATIONS:
            add(op+'-nul', windows, 'prefix', 'C:\\base' if windows else '/base', error='embedded NUL')
        add('absolute', windows, 'relative', 'relative-base', error='qualified absolute base')
        add('absolute-base-nul', windows, 'relative', 'C:\\base' if windows else '/base', error='embedded NUL')
        add('join-base-nul', windows, 'relative', 'C:\\base' if windows else '/base', error='embedded NUL')
    for value, error in [('\\\\server', 'incomplete Windows UNC'), ('\\\\\\share', 'invalid Windows UNC server'),
                         ('\\\\server\\\\share', 'invalid Windows UNC share'), ('\\\\?\\C:\\x', 'invalid Windows colon'),
                         ('\\\\.\\pipe', 'invalid Windows UNC server'), ('dir:file', 'invalid Windows colon'),
                         ('λ:x', 'invalid Windows colon')]:
        add('name', True, value, error=error)
    add('absolute', True, 'D:relative', 'C:\\base', error='same base drive')
    add('absolute', True, 'C:relative', '\\\\server\\share\\base', error='same base drive')
    add('absolute', True, 'relative', '\\ambiguous', error='qualified absolute base')
    add('join', True, 'C:relative', 'no-drive', error='same base drive')
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    selected = parser.add_mutually_exclusive_group(required=True)
    selected.add_argument('--compiler', type=Path)
    selected.add_argument('--freak', type=Path)
    parser.add_argument('--runtime-root', type=Path)
    parser.add_argument('--style-core-only', action='store_true')
    parser.add_argument('--clang', required=True)
    parser.add_argument('--optimization', type=int, choices=(0, 2, 3), action='append')
    parser.add_argument('--sanitize', action='store_true')
    parser.add_argument('--keep', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.style_core_only and not args.compiler:
        parser.error('--style-core-only requires --compiler')
    repo = args.repo.resolve(strict=True)
    candidate = (args.compiler or args.freak).resolve(strict=True)
    runtime = args.runtime_root.resolve(strict=True) if args.runtime_root else repo/'freakc/runtime'
    source = (repo/'std/path.fk').read_text()
    env = dict(os.environ, NO_COLOR='1', ASAN_OPTIONS='detect_leaks=1:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1')
    temporary = tempfile.TemporaryDirectory(prefix='freak-v35-paths-') if not args.keep else None
    work = args.keep.resolve() if args.keep else Path(temporary.name)
    work.mkdir(parents=True, exist_ok=True)
    unrelated = work/'unrelated-cwd'; unrelated.mkdir()
    evidence = {'status': 'PASS', 'mode': 'style component' if args.style_core_only else ('native source component' if args.compiler else 'public CLI'),
                'candidate_sha256': hashlib.sha256(candidate.read_bytes()).hexdigest(),
                'path_sha256': hashlib.sha256(source.encode()).hexdigest(), 'sanitize': args.sanitize,
                'native_host': os.name, 'records': []}
    control = work/'ownership-control.c'; control.write_text(AUDIT_CONTROL)
    executable=work/'ownership-control'
    command=[args.clang,'-O0',str(control),str(runtime/'freak_runtime.c'),'-I',str(runtime),
             '-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1','-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1','-lm']
    if os.name=='nt':command+=['-lws2_32','-lshell32']
    result=run([*command,'-o',str(executable)],cwd=unrelated,env=env);assert result.returncode==0,result.stderr
    for owner,status,diagnostic in (('c',87,b'C ownership audit found 1'),('llvm',86,b'LLVM ownership audit found 1')):
        result=run([str(executable),owner],cwd=unrelated,env=env)
        (work/f'ownership-control-{owner}.log').write_bytes(result.stdout+result.stderr)
        assert result.returncode==status and diagnostic in result.stderr,(owner,result.returncode,result.stderr)
    evidence['ownership_failing_controls']=['c_word','llvm_word']
    if args.sanitize:
        for name, code, expected in (
            ('asan', '#include <stdlib.h>\nint main(int n,char**v){volatile char*p=malloc(1);p[n+4]=1;free((void*)p);return 0;}\n', b'AddressSanitizer'),
            ('ubsan', '#include <stdint.h>\nint main(int n,char**v){volatile int64_t a=INT64_MAX;volatile int64_t b=a+n;return (int)b;}\n', b'runtime error: signed integer overflow')):
            control = work/(name+'-control.c'); control.write_text(code); executable=work/(name+'-control')
            result=run([args.clang, '-O0', '-fsanitize=address,undefined', str(control), '-o', str(executable)],cwd=unrelated,env=env)
            assert result.returncode==0, result.stderr
            result=run([str(executable)],cwd=unrelated,env=env); (work/(name+'-control.log')).write_bytes(result.stdout+result.stderr)
            assert result.returncode!=0 and expected in result.stderr, result.stderr
        evidence['failing_controls']=['asan_heap_oob','ubsan_signed_overflow']
    native_dispatch = 'panic("native dispatch is outside this component gate")' if args.style_core_only else NATIVE
    program = PROGRAM.replace('__NATIVE_DISPATCH__', native_dispatch)
    if args.compiler:
        if args.style_core_only:
            source = source.split('\ntask path_join(base: word, leaf: word)')[0]
        text = source+'\n'+program
    else:
        names = ['path_'+op for op in OPERATIONS]+['path_'+op+'_style' for op in OPERATIONS]
        text = 'use std::path::{'+', '.join(names)+'}\n'+program
    vectors = cases()
    for backend in ('c', 'llvm'):
        fixture = work/('paths-'+backend+'.fk'); fixture.write_text(text)
        command = ([str(candidate), str(fixture), '--'+backend, '--strict-borrow'] if args.compiler else
                   [str(candidate), 'transpile', str(fixture), '--'+backend, '--strict-borrow'])
        result = run(command, cwd=unrelated, env=env); (work/('emit-'+backend+'.log')).write_bytes(result.stdout+result.stderr)
        assert result.returncode==0, (backend,result.stdout,result.stderr)
        generated=Path(str(fixture)+('.c' if backend=='c' else '.ll')); assert generated.is_file()
        for opt in args.optimization or (0, 2, 3):
            binary=work/f'paths-{backend}-O{opt}'
            command=[args.clang, f'-O{opt}', str(generated), str(runtime/'freak_runtime.c'), str(runtime/'freak_llvm_runtime.c'),
                     '-I', str(runtime), '-lm']
            if os.name=='nt':command+=['-lws2_32','-lshell32']
            if args.sanitize:command+=['-fsanitize=address,undefined','-fno-omit-frame-pointer']
            fatal_binary=work/f'paths-{backend}-O{opt}-fatal'
            for executable,defines in ((binary,['-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1','-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1']),(fatal_binary,[])):
                result=run([*command,*defines,'-o',str(executable)],cwd=unrelated,env=env)
                (work/f'link-{executable.name}.log').write_bytes(result.stdout+result.stderr)
                assert result.returncode==0,result.stderr
            audit_env=dict(env)
            if os.name=='nt':
                audit_env.pop('WINDIR',None);audit_env.pop('SystemRoot',None)
            else:
                audit_env.update(WINDIR='spoofed-Windows',SystemRoot='spoofed-Windows')
            checked=0
            for style in ('styles','native') if not args.style_core_only else ('styles',):
                selected_vectors=[v for v in vectors if style=='styles' or v['windows']==(os.name=='nt')]
                for index,vector in enumerate(selected_vectors):
                    args_style=('windows' if vector['windows'] else 'posix') if style=='styles' else 'native'
                    executable=fatal_binary if vector['error'] else binary
                    result=run([str(executable),vector['operation'],args_style,vector['value'],vector['base']],cwd=unrelated,env=audit_env,timeout=15)
                    markers=(b'AddressSanitizer',b'LeakSanitizer',b'UndefinedBehaviorSanitizer',b'runtime error:',b'ownership audit found')
                    assert not any(marker in result.stderr for marker in markers),(vector,result.stderr)
                    if vector['error']:
                        # Fatal exit does not promise caller lexical cleanup.
                        assert result.returncode==1 and not result.stdout and vector['error'].encode() in result.stderr,(vector,result.returncode,result.stdout,result.stderr)
                    else:
                        expected=('RESULT:'+vector['expected']+'\n').encode()
                        assert result.returncode==0 and result.stdout.replace(b'\r\n',b'\n')==expected and not result.stderr,(vector,result.returncode,result.stdout,result.stderr)
                    evidence['records'].append(dict(backend=backend,optimization=opt,dispatch=style,**vector,status='PASS'))
                    checked+=1
            result=run([str(binary),'soak','posix','',''],cwd=unrelated,env=audit_env,timeout=15)
            assert result.returncode==0 and result.stdout.replace(b'\r\n',b'\n')==b'RESULT:SOAK_OK\n' and not result.stderr,(result.stdout,result.stderr)
            evidence['records'].append(dict(backend=backend,optimization=opt,case='200-retained-source-soak',status='PASS'))
            print(f'PASS paths {backend} O{opt}: {checked} oracle/contract cases and strict source soak',flush=True)
        prefix=source+'\n' if args.compiler else 'use std::path::{path_name_style, path_absolute_style}\n'
        for name,body,diagnostic in (
            ('wrong-type','task main(){ path_name_style(1, false) }\n',b'expects word, got int'),
            ('wrong-arity','task main(){ path_absolute_style("relative", "/base") }\n',b'expects 3 argument(s), got 2'),
            ('caller-transfer','task main(){ pilot value: word = process::arg(1)\npath_name_style(value, false)\nsay value\n}\n',b'You gave this away')):
            negative=work/f'negative-{name}-{backend}.fk';negative.write_text(prefix+body)
            command=([str(candidate),str(negative),'--'+backend,'--strict-borrow'] if args.compiler else
                     [str(candidate),'transpile',str(negative),'--'+backend,'--strict-borrow'])
            result=run(command,cwd=unrelated,env=env);log=result.stdout+result.stderr
            (work/f'negative-{name}-{backend}.log').write_bytes(log)
            assert result.returncode!=0 and diagnostic in log and str(negative).encode() in log,(name,result.returncode,log)
            evidence['records'].append(dict(backend=backend,case=name,status='PASS'))
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(evidence,indent=2)+'\n')
    return 0


if __name__=='__main__':raise SystemExit(main())
