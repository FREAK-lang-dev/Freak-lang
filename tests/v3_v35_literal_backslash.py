#!/usr/bin/env python3
"""Verify anchored native operations preserve POSIX literal backslash names."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from v3_v35_process import WINDOWS_ARGV_WRAPPER


HARNESS = r'''
#include "freak_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
extern int64_t freak_llvm_fs_rename_relative_new_checked(int64_t,int64_t,int64_t,int64_t);
#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#include <dirent.h>
#endif
static void require(int ok,const char *why) { if(!ok) { fprintf(stderr,"FAIL: %s\n",why);exit(2); } }
#ifdef USE_LLVM_ADAPTER
#define W(s) ((int64_t)(intptr_t)(s))
#define F(n) freak_llvm_fs_##n
extern void freak_llvm_word_release_replaced(int64_t,int64_t);
static freak_word word(int64_t ticket) { return freak_llvm_word_view(F(result_word)(ticket)); }
static void drop(freak_word *value) { freak_llvm_word_release_replaced((int64_t)(intptr_t)value->data,0); }
#else
#define W(s) freak_word_lit(s)
#define F(n) freak_fs_##n
#define word freak_fs_result_word
#define drop freak_word_release_owned
#endif
static size_t resources(void) {
#ifdef _WIN32
    DWORD count=0;require(GetProcessHandleCount(GetCurrentProcess(),&count),"handle counter");return count;
#elif defined(__linux__)
    DIR *directory=opendir("/proc/self/fd");require(directory!=NULL,"descriptor counter");size_t count=0;struct dirent *entry;
    while((entry=readdir(directory))) if(strcmp(entry->d_name,".") && strcmp(entry->d_name,"..")) count++;
    require(closedir(directory)==0,"close counter");return count;
#else
    return 0;
#endif
}
static void read_exact(int64_t directory,const char *leaf) {
    int64_t carrier=F(read_relative_bytes_limit_ticket)(directory,W(leaf),64);
#ifdef _WIN32
    require(!F(result_ok)(carrier),"Windows rejects backslash-relative names");
#else
    require(F(result_ok)(carrier),"literal leaf read");int64_t bytes=F(result_bytes)(carrier);
    const unsigned char expected[]={'t','a','r','g','e','t',0,255};require(freak_byte_buffer_length(bytes)==sizeof(expected),"exact byte count");
    for(size_t i=0;i<sizeof(expected);i++) require(freak_byte_buffer_read_byte(bytes)==expected[i],"exact literal bytes");
    freak_byte_buffer_release(bytes);
#endif
    F(result_release)(carrier);
}
int main(int argc,char **argv) {
    require(argc==6,"arguments");size_t before=resources();
#ifndef _WIN32
    if(!strcmp(argv[4],"root")) {
        int64_t root=F(open_dir_ticket)(W("/"));require(F(result_ok)(root) && F(result_kind)(root)==2,"admit filesystem root");
        int64_t path=F(directory_path_ticket)(root);require(F(result_ok)(path),"held root path");
        freak_word spelling=word(path);require(spelling.length==1 && spelling.data[0]=='/',"canonical held root path");drop(&spelling);F(result_release)(path);
        int64_t first=F(directory_identity_ticket)(root),second=F(directory_identity_ticket)(root);
        require(F(result_ok)(first) && F(result_ok)(second),"held root identity");
        freak_word a=word(first),b=word(second);require(a.length>0 && a.length==b.length && !memcmp(a.data,b.data,a.length),"stable held root identity");
        drop(&a);drop(&b);F(result_release)(first);F(result_release)(second);F(result_release)(root);
        int64_t empty=F(open_dir_ticket)(W(""));require(!F(result_ok)(empty),"empty external path still rejected");F(result_release)(empty);
        require(freak_fs_result_live()==0,"root result ownership");require(resources()==before,"root descriptor ownership");puts("PASS");return 0;
    }
#endif
    int64_t source=F(open_dir_ticket)(W(argv[1])),destination=F(open_dir_ticket)(W(argv[2]));
    require(F(result_ok)(source) && F(result_ok)(destination),"directory admission");
#ifndef _WIN32
    if(!strcmp(argv[4],"held")) {
        char retained[4097];
        require(snprintf(retained,sizeof retained,"%s-retained",argv[1])>0 && rename(argv[1],retained)==0 && symlink(argv[5],argv[1])==0,"source ancestor swap");
        require(snprintf(retained,sizeof retained,"%s-retained",argv[2])>0 && rename(argv[2],retained)==0 && symlink(argv[5],argv[2])==0,"destination ancestor swap");
    }
#endif
    read_exact(source,argv[3]);
    int64_t publication=F(rename_relative_new_checked)(source,W(argv[3]),destination,W(argv[3]));
#ifdef _WIN32
    require(!F(result_ok)(publication) && !F(result_completed)(publication),"Windows rejects rename traversal");
#else
    require(F(result_ok)(publication) && F(result_completed)(publication),"literal leaf publication");
#endif
    F(result_release)(publication);read_exact(destination,argv[3]);
    int64_t removal=F(remove_relative_file_checked)(destination,W(argv[3]));
#ifdef _WIN32
    require(!F(result_ok)(removal) && !F(result_completed)(removal),"Windows rejects remove traversal");
#else
    require(F(result_ok)(removal) && F(result_completed)(removal),"literal leaf removal");
#endif
    F(result_release)(removal);F(result_release)(source);F(result_release)(destination);
    require(freak_fs_result_live()==0,"result ownership");require(resources()==before,"descriptor/handle ownership");puts("PASS");return 0;
}
'''

CONSUMER = '''task main() {
    pilot source_root = fs::open_dir_ticket(process::arg(1))
    pilot destination_root = fs::open_dir_ticket(process::arg(2))
    pilot leaf_name = process::arg(3)
    pilot before_read = fs::read_relative_bytes_limit_ticket(source_root, leaf_name, 64)
    say fs::result_ok(before_read)
    fs::result_release(before_read)
    pilot publication = fs::rename_relative_new_checked(source_root, leaf_name, destination_root, leaf_name)
    say fs::result_ok(publication)
    say fs::result_completed(publication)
    fs::result_release(publication)
    pilot after_read = fs::read_relative_bytes_limit_ticket(destination_root, leaf_name, 64)
    say fs::result_ok(after_read)
    fs::result_release(after_read)
    pilot removal = fs::remove_relative_file_checked(destination_root, leaf_name)
    say fs::result_ok(removal)
    fs::result_release(removal)
    fs::result_release(source_root)
    fs::result_release(destination_root)
}
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clang', default=os.environ.get('FREAK_CLANG', 'clang'))
    parser.add_argument('--compiler', type=Path)
    parser.add_argument('--optimization', type=int, choices=(0, 2, 3), action='append')
    parser.add_argument('--sanitize', action='store_true')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    clang = shutil.which(args.clang)
    assert clang, args.clang
    runtime = Path(__file__).resolve().parents[1]/'freakc'/'runtime'
    paths = [runtime/name for name in ('freak_runtime.c', 'freak_runtime.h', 'freak_llvm_runtime.c', 'freak_v35_fs.inc')]
    hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    records = []
    report = {'runtime_sha256': hashes, 'native_platform': os.name, 'sanitized': args.sanitize, 'cases': records}
    flags = ['-lws2_32', '-lshell32'] if os.name == 'nt' else ['-lm']
    if args.sanitize: flags += ['-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-g']
    environment = dict(os.environ, ASAN_OPTIONS='detect_leaks=1:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1')
    leaf = 'ordinary\\result.ll'
    with tempfile.TemporaryDirectory(prefix='freak-literal-backslash-') as temporary:
        home = Path(temporary)
        source = home/'harness.c'
        source.write_text(HARNESS.replace('int main(', 'static int native_main(')+WINDOWS_ARGV_WRAPPER)
        if args.sanitize:
            for name, code, diagnostic in [
                ('address', '#include <stdlib.h>\nint main(int n,char **v){volatile char *p=malloc(1);p[n+4]=3;free((void*)p);return 0;}\n', b'AddressSanitizer'),
                ('undefined', '#include <limits.h>\nint main(void){volatile int n=INT_MAX;return n+1;}\n', b'runtime error:')]:
                control = home/(name+'.c');control.write_text(code);binary = home/name
                subprocess.run([clang, str(control), '-O2', *flags, '-o', str(binary)], check=True, capture_output=True)
                result = subprocess.run([str(binary)], env=environment, capture_output=True, timeout=15)
                assert result.returncode != 0 and diagnostic in result.stderr, (name, result)
                records.append({'case': 'positive-'+name, 'status': 'pass'})
        def fixture(label: str) -> tuple[Path, Path, Path]:
            case = home/label;case.mkdir()
            source, destination, outside = (case/'Source λ:root\\anchor', case/'Destination α:root\\anchor', case/'outside') if os.name != 'nt' else (case/'source', case/'destination', case/'outside')
            for directory in (source, destination, outside):
                directory.mkdir(mode=0o700);(directory/'ordinary').mkdir();(directory/'ordinary'/'result.ll').write_bytes(b'slash-neighbor')
            if os.name != 'nt':
                (source/leaf).write_bytes(b'target\0\xff');(outside/leaf).write_bytes(b'outside-secret')
            return source, destination, outside
        def oracle(source: Path, destination: Path, outside: Path, held: bool) -> None:
            if held:
                source, destination = Path(str(source)+'-retained'), Path(str(destination)+'-retained')
            for directory in (source, destination, outside):
                assert (directory/'ordinary'/'result.ll').read_bytes() == b'slash-neighbor'
            if os.name != 'nt':
                assert not (source/leaf).exists() and not (destination/leaf).exists()
                assert (outside/leaf).read_bytes() == b'outside-secret'
        for adapter in ('c', 'llvm'):
            for optimization in args.optimization or (0, 2, 3):
                binary = home/f'{adapter}-{optimization}'
                command = [clang, str(source), str(runtime/'freak_runtime.c'), f'-I{runtime}', f'-O{optimization}',
                           '-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1', '-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1', *flags, '-o', str(binary)]
                if adapter == 'llvm':command += ['-DUSE_LLVM_ADAPTER=1', str(runtime/'freak_llvm_runtime.c')]
                built = subprocess.run(command, capture_output=True, timeout=90);assert built.returncode == 0, built.stderr
                for mode in ('ordinary', 'held', 'root') if os.name != 'nt' else ('ordinary',):
                    source_root, destination, outside = fixture(f'{adapter}-{optimization}-{mode}')
                    result = subprocess.run([str(binary), str(source_root), str(destination), leaf, mode, str(outside)], env=environment, capture_output=True, timeout=15)
                    assert result.returncode == 0 and not result.stderr and result.stdout.replace(b'\r\n', b'\n') == b'PASS\n', result
                    if mode != 'root': oracle(source_root, destination, outside, mode == 'held')
                    records.append({'adapter': adapter, 'optimization': optimization, 'case': mode, 'status': 'pass'})
                print(f'PASS literal backslash {adapter} O{optimization}', flush=True)
        if args.compiler:
            compiler = args.compiler.resolve(strict=True)
            report['compiler_sha256'] = hashlib.sha256(compiler.read_bytes()).hexdigest()
            source = home/'consumer.fk';source.write_text(CONSUMER)
            for adapter in ('c', 'llvm'):
                generated = Path(str(source)+('.c' if adapter == 'c' else '.ll'))
                built = subprocess.run([str(compiler), str(source), '--'+adapter, '--strict-borrow'], capture_output=True, timeout=90)
                assert built.returncode == 0, (built.stdout, built.stderr)
                for optimization in args.optimization or (0, 2, 3):
                    binary = home/f'language-bin-{adapter}-{optimization}'
                    command = [clang, str(generated), str(runtime/'freak_runtime.c'), f'-I{runtime}', f'-O{optimization}', *flags, '-o', str(binary)]
                    if adapter == 'llvm':command += [str(runtime/'freak_llvm_runtime.c')]
                    linked = subprocess.run(command, capture_output=True, timeout=90);assert linked.returncode == 0, linked.stderr
                    source_root, destination, outside = fixture(f'language-{adapter}-{optimization}')
                    result = subprocess.run([str(binary), str(source_root), str(destination), leaf], env=environment, capture_output=True, timeout=15)
                    expected = (b'false\n' if os.name == 'nt' else b'true\n')*5
                    assert result.returncode == 0 and not result.stderr and result.stdout.replace(b'\r\n', b'\n') == expected, result
                    oracle(source_root, destination, outside, False)
                    records.append({'adapter': adapter, 'optimization': optimization, 'case': 'language', 'status': 'pass'})
    assert hashes == {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}, 'runtime changed during verification'
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True);args.report.write_text(json.dumps(report, indent=2)+'\n')
    return 0


if __name__ == '__main__':raise SystemExit(main())
