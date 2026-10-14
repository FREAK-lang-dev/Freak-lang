#!/usr/bin/env python3
"""Verify native checked stat absence, metadata and handle ownership.

The C interface and LLVM scalar adapter execute the production runtime. Python
supplies independent metadata expectations; permission failures run unprivileged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile

from v3_v35_process import WINDOWS_ARGV_WRAPPER


HARNESS = r'''
#include "freak_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <windows.h>
#else
#include <dirent.h>
#endif
static void require(int value,const char *message) {
    if(!value) { fprintf(stderr,"FAIL: %s\n",message);exit(2); }
}
#ifdef USE_LLVM_ADAPTER
#define W(s) ((int64_t)(intptr_t)(s))
#define F(n) freak_llvm_fs_##n
extern void freak_llvm_word_release_replaced(int64_t,int64_t);
static freak_word error(int64_t result) { return freak_llvm_word_view(F(result_error)(result)); }
static void drop(freak_word *word) { freak_llvm_word_release_replaced((int64_t)(intptr_t)word->data,0); }
#else
#define W(s) freak_word_lit(s)
#define F(n) freak_fs_##n
#define error freak_fs_result_error
#define drop freak_word_release_owned
#endif
static size_t resources(void) {
#ifdef _WIN32
    DWORD count=0;require(GetProcessHandleCount(GetCurrentProcess(),&count),"handle counter");return count;
#elif defined(__linux__)
    DIR *directory=opendir("/proc/self/fd");require(directory!=NULL,"descriptor counter");
    size_t count=0;struct dirent *entry;
    while((entry=readdir(directory))) if(strcmp(entry->d_name,".") && strcmp(entry->d_name,"..")) count++;
    require(closedir(directory)==0,"close descriptor counter");return count;
#else
    return 0;
#endif
}
int main(int argc,char **argv) {
    require(argc==3,"arguments");size_t before=resources();
    int expected_ok=argv[2][0]=='1',expected_missing=argv[2][1]=='1';
    for(int i=0;i<128;i++) {
        int64_t result=F(stat_checked)(W(argv[1]));
        require(!!F(result_ok)(result)==expected_ok,"success classification");
        require(!!F(result_missing)(result)==expected_missing,"missing classification");
        freak_word message=error(result);
        if(expected_ok) require(message.length==0,"success has no error");
        else {
            const char *expected="could not inspect filesystem path without following links";
            require(message.length==strlen(expected) && !memcmp(message.data,expected,message.length),"preserved failure diagnostic");
        }
        drop(&message);
        if(i==0) printf("%d %d %lld %lld %lld\n",(int)F(result_ok)(result),(int)F(result_missing)(result),
            expected_ok ? (long long)F(result_kind)(result) : 0,
            expected_ok ? (long long)F(result_size)(result) : 0,
            expected_ok ? (long long)F(result_mode)(result) : 0);
        F(result_release)(result);
    }
    require(freak_fs_result_live()==0,"result ownership");require(resources()==before,"descriptor/handle ownership");return 0;
}
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clang', default=os.environ.get('FREAK_CLANG', 'clang'))
    parser.add_argument('--optimization', type=int, choices=(0, 2, 3), action='append')
    parser.add_argument('--sanitize', action='store_true')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    clang = shutil.which(args.clang)
    assert clang, args.clang
    runtime = Path(__file__).resolve().parents[1] / 'freakc' / 'runtime'
    tracked = [runtime/name for name in ('freak_runtime.c', 'freak_runtime.h', 'freak_llvm_runtime.c', 'freak_v35_fs.inc')]
    hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in tracked}
    records: list[dict] = []
    report = {'runtime_sha256': hashes, 'sanitized': args.sanitize, 'cases': records,
              'native_platform': os.name, 'permission_scope': 'POSIX child runs with real unprivileged credentials; Windows native ACL denial pending'}
    flags = ['-lws2_32', '-lshell32'] if os.name == 'nt' else ['-lm']
    environment = dict(os.environ, ASAN_OPTIONS='detect_leaks=1:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1')
    if args.sanitize:
        flags += ['-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-g']
    with tempfile.TemporaryDirectory(prefix='freak-stat λ $ ') as temporary:
        home = Path(temporary)
        home.chmod(0o755)
        source = home/'harness.c'
        source.write_text(HARNESS.replace('int main(', 'static int native_main(')+WINDOWS_ARGV_WRAPPER)
        fixture = home/'fixture'
        fixture.mkdir(mode=0o755)
        ordinary = fixture/'ordinary'
        ordinary.write_bytes(b'unchanged\x00\xffcontent')
        ordinary.chmod(0o640)
        empty = fixture/'empty'
        empty.write_bytes(b'')
        restricted = fixture/'inaccessible'
        restricted.mkdir()
        (restricted/'present').write_bytes(b'private')
        restricted.chmod(0)
        cases = [('absent', fixture/'absent', False, True),
                 ('absent-nested', fixture/'absent-parent'/'leaf', False, True),
                 ('relative-absent', Path('absent'), False, True),
                 ('parent-relative-absent', Path('../fixture/absent'), False, True),
                 ('ordinary', ordinary, True, False), ('empty', empty, True, False),
                 ('directory', fixture, True, False),
                 ('non-directory-ancestor', ordinary/'leaf', False, False)]
        if os.name != 'nt':
            cases += [('denied-existing', restricted/'present', False, False),
                      ('denied-absent', restricted/'absent', False, False)]
            for name, target in [('final-link', ordinary), ('dangling-link', fixture/'absent'),
                                 ('ancestor-link', fixture), ('broken-ancestor', fixture/'absent')]:
                (fixture/name).symlink_to(target)
            cases += [('final-link', fixture/'final-link', True, False),
                      ('final-link-trailing', str(fixture/'final-link')+'/', True, False),
                      ('dangling-link', fixture/'dangling-link', True, False),
                      ('ancestor-link-existing', fixture/'ancestor-link'/'ordinary', True, False),
                      ('ancestor-link-absent', fixture/'ancestor-link'/'absent', False, False),
                      ('broken-ancestor-absent', fixture/'broken-ancestor'/'absent', False, False)]
        try:
            if args.sanitize:
                for name, code, expected in [
                    ('address', '#include <stdlib.h>\nint main(int n,char **v){volatile char *p=malloc(1);p[n+4]=3;free((void*)p);return 0;}\n', b'AddressSanitizer'),
                    ('undefined', '#include <limits.h>\nint main(void){volatile int n=INT_MAX;return n+1;}\n', b'runtime error:')]:
                    control = home/(name+'.c')
                    control.write_text(code)
                    binary = home/name
                    compiled = subprocess.run([clang, str(control), '-O2', *flags, '-o', str(binary)], capture_output=True, timeout=60)
                    assert compiled.returncode == 0, compiled.stderr
                    result = subprocess.run([str(binary)], env=environment, capture_output=True, timeout=15)
                    assert result.returncode != 0 and expected in result.stderr, (name, result.returncode, result.stderr)
                    records.append({'case': 'positive-'+name, 'status': 'pass'})
            for adapter in ('c', 'llvm'):
                for optimization in args.optimization or (0, 2, 3):
                    binary = home/f'{adapter}-{optimization}'
                    command = [clang, str(source), str(runtime/'freak_runtime.c'), f'-I{runtime}', f'-O{optimization}',
                               '-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1', '-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1', *flags, '-o', str(binary)]
                    if adapter == 'llvm':
                        command += ['-DUSE_LLVM_ADAPTER=1', str(runtime/'freak_llvm_runtime.c')]
                    compiled = subprocess.run(command, capture_output=True, timeout=90)
                    assert compiled.returncode == 0, compiled.stderr
                    for name, path, success, missing in cases:
                        child_options = {}
                        if name.startswith('denied-') and os.geteuid() == 0:
                            def unprivileged() -> None:
                                os.setgroups([])
                                os.setgid(65534)
                                os.setuid(65534)
                            child_options['preexec_fn'] = unprivileged
                        result = subprocess.run([str(binary), str(path), f'{int(success)}{int(missing)}'], cwd=fixture,
                                                env=environment, capture_output=True, timeout=15, **child_options)
                        assert result.returncode == 0 and not result.stderr, (adapter, optimization, name, result.returncode, result.stdout, result.stderr)
                        values = list(map(int, result.stdout.split()))
                        assert values[:2] == [int(success), int(missing)], (name, values)
                        if success:
                            # The API removes a final separator before inspecting a link.
                            inspected = fixture/'final-link' if name == 'final-link-trailing' else Path(path) if Path(path).is_absolute() else fixture/Path(path)
                            info = os.lstat(inspected)
                            kind = 1 if stat.S_ISREG(info.st_mode) else 2 if stat.S_ISDIR(info.st_mode) else 3 if stat.S_ISLNK(info.st_mode) else 4
                            if os.name != 'nt':
                                assert values[2:] == [kind, info.st_size, stat.S_IMODE(info.st_mode)], (name, values, info)
                            else:
                                assert values[2] == kind and values[3] == info.st_size, (name, values)
                        records.append({'adapter': adapter, 'optimization': optimization, 'case': name, 'status': 'pass', 'repetitions': 128})
                    print(f'PASS stat missing {adapter} O{optimization}: {len(cases)} cases x128', flush=True)
        finally:
            restricted.chmod(0o700)
        assert ordinary.read_bytes() == b'unchanged\x00\xffcontent'
    assert hashes == {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in tracked}, 'runtime changed during verification'
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2)+'\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
