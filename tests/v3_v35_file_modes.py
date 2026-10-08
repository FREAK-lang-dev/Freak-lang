#!/usr/bin/env python3
"""Verify held-file permission metadata and checked staged-file mode changes."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
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
#include <unistd.h>
#include <dirent.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <stdarg.h>
#include <errno.h>
#endif
static void require(int ok,const char *why) { if(!ok) { fprintf(stderr,"FAIL: %s\n",why);exit(2); } }
#ifdef USE_LLVM_ADAPTER
#define W(s) ((int64_t)(intptr_t)(s))
#define F(n) freak_llvm_fs_##n
extern void freak_llvm_word_release_replaced(int64_t,int64_t);
static freak_word error(int64_t r) { return freak_llvm_word_view(F(result_error)(r)); }
static void drop(freak_word *w) { freak_llvm_word_release_replaced((int64_t)(intptr_t)w->data,0); }
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
    DIR *directory=opendir("/proc/self/fd");require(directory!=NULL,"descriptor counter");size_t count=0;struct dirent *entry;
    while((entry=readdir(directory))) if(strcmp(entry->d_name,".") && strcmp(entry->d_name,"..")) count++;
    require(closedir(directory)==0,"close counter");return count;
#else
    return 0;
#endif
}
static const char *scenario="",*outside="";static int armed=0,changed=0,chmod_calls=0,sync_calls=0;
#ifdef TEST_INTERPOSE
extern int __real_openat(int,const char *,int,...),__real_fchmod(int,mode_t),__real_fsync(int),__real_close(int);
extern int __real_fstat(int,struct stat *);
int __wrap_fstat(int file,struct stat *info) {
    int status=__real_fstat(file,info);
    if(armed && status==0 && S_ISREG(info->st_mode) && !strcmp(scenario,"foreign-file-metadata")) info->st_uid=geteuid()+1;
    return status;
}
int __wrap_openat(int parent,const char *name,int flags,...) {
    mode_t permissions=0;if(flags&O_CREAT) { va_list args;va_start(args,flags);permissions=va_arg(args,int);va_end(args); }
    int file=__real_openat(parent,name,flags,permissions);
    if(armed && file>=0 && !changed && !strcmp(scenario,"ancestor-race") && (flags&O_DIRECTORY) && !strcmp(name,"pivot")) {
        require(renameat(parent,"pivot",parent,"retained")==0 && symlinkat(outside,parent,"pivot")==0,"swap ancestor fixture");changed=1;
    }
    return file;
}
int __wrap_fchmod(int file,mode_t mode) {
    chmod_calls++;
    if(!strcmp(scenario,"chmod-fault")) { errno=EIO;return -1; }
    int status=__real_fchmod(file,mode);
    if(!strcmp(scenario,"file-exchange") && !changed && status==0) {
        char from[4097],retained[4097],secret[4097];
        require(snprintf(from,sizeof from,"%s/a",outside)>0 && snprintf(retained,sizeof retained,"%s/retained",outside)>0 &&
            snprintf(secret,sizeof secret,"%s/secret",outside)>0,"exchange paths");
        require(rename(from,retained)==0 && symlink(secret,from)==0,"swap file fixture");changed=1;
    }
    return status;
}
int __wrap_fsync(int file) { sync_calls++;if(!strcmp(scenario,"sync-fault")) { errno=EIO;return -1; }return __real_fsync(file); }
int __wrap_close(int file) {
    struct stat info;int ordinary=fstat(file,&info)==0 && S_ISREG(info.st_mode);
    int status=__real_close(file);
    if(armed && ordinary && !strcmp(scenario,"close-fault")) { errno=EIO;return -1; }return status;
}
#endif
int main(int argc,char **argv) {
    require(argc==6,"arguments");scenario=argv[4];outside=argv[5];size_t before=resources();
    int64_t root=F(open_dir_ticket)(W(argv[1]));require(F(result_ok)(root),"root admission");
    if(!strcmp(scenario,"metadata")) {
        int64_t read=F(read_relative_bytes_limit_ticket)(root,W(argv[2]),4096);require(F(result_ok)(read),"bounded read");
        printf("%lld ",(long long)F(result_mode)(read));F(result_release)(read);
        char path[4097];require(snprintf(path,sizeof path,"%s/%s",argv[1],argv[2])>0,"metadata path");
        read=F(read_bytes_ticket)(W(path));require(F(result_ok)(read),"ordinary read");printf("%lld\n",(long long)F(result_mode)(read));F(result_release)(read);
    } else {
        armed=1;
        int64_t result=F(set_mode_relative_checked)(root,W(argv[2]),strtoll(argv[3],NULL,10));
        printf("%d %d\n",(int)F(result_ok)(result),(int)F(result_completed)(result));
        freak_word message=error(result);require(F(result_ok)(result) ? message.length==0 : message.length>0,"checked diagnostic");drop(&message);
        F(result_release)(result);
        if(!strcmp(scenario,"sync-fault")) require(chmod_calls==1 && sync_calls==1,"fault reached real mode update and sync");
        if(!strcmp(scenario,"chmod-fault")) require(chmod_calls==1 && sync_calls==0,"failed chmod prevents sync");
        if(!strcmp(scenario,"native-foreign-parent") || !strcmp(scenario,"foreign-file-metadata")) require(chmod_calls==0 && sync_calls==0,"foreign ownership prevents mutation");
    }
    F(result_release)(root);require(freak_fs_result_live()==0,"result ownership");require(resources()==before,"descriptor/handle ownership");return 0;
}
'''

CONSUMER = '''task main() {
    pilot root = fs::open_dir_ticket(process::arg(1))
    pilot mut name = process::arg(2)
    if process::arg(3) == "nul" { name = name + char_to_word(0) + "suffix" }
    pilot change_ticket = fs::set_mode_relative_checked(root, name, 420)
    say fs::result_ok(change_ticket)
    say fs::result_completed(change_ticket)
    fs::result_release(change_ticket)
    fs::result_release(root)
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
    records: list[dict] = []
    report = {'runtime_sha256': hashes, 'native_platform': sys.platform, 'sanitized': args.sanitize, 'cases': records}
    if os.name != 'nt':
        report['native_uid'] = os.geteuid()
        report['foreign_file_scope'] = 'native uid65534 child under owned parent' if os.geteuid() == 0 else 'fault-injected held-file fstat owner; native foreign-file fixture requires privilege'
    flags = ['-lws2_32', '-lshell32'] if os.name == 'nt' else ['-lm']
    if args.sanitize:
        flags += ['-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-g']
    environment = dict(os.environ, ASAN_OPTIONS='detect_leaks=1:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1')
    with tempfile.TemporaryDirectory(prefix='freak-mode λ $ ') as temporary:
        home = Path(temporary)
        home.chmod(0o755)
        source = home/'harness.c'
        source.write_text(HARNESS.replace('int main(', 'static int native_main(')+WINDOWS_ARGV_WRAPPER)
        if args.sanitize:
            for name, code, diagnostic in [
                ('address', '#include <stdlib.h>\nint main(int n,char **v){volatile char *p=malloc(1);p[n+4]=3;free((void*)p);return 0;}\n', b'AddressSanitizer'),
                ('undefined', '#include <limits.h>\nint main(void){volatile int n=INT_MAX;return n+1;}\n', b'runtime error:')]:
                control = home/(name+'.c')
                control.write_text(code)
                binary = home/name
                subprocess.run([clang, str(control), '-O2', *flags, '-o', str(binary)], check=True, capture_output=True)
                result = subprocess.run([str(binary)], env=environment, capture_output=True, timeout=15)
                assert result.returncode != 0 and diagnostic in result.stderr, (name, result)
                records.append({'case': 'positive-'+name, 'status': 'pass'})

        def fixture(label: str) -> tuple[Path, Path]:
            parent = home/label
            parent.mkdir(mode=0o755)
            root, outside = parent/'root', parent/'outside'
            root.mkdir(mode=0o700)
            outside.mkdir(mode=0o700)
            (root/'a').write_bytes(b'unchanged\x00\xffcontent')
            (root/'a').chmod(0o600)
            (outside/'secret').write_bytes(b'outside-secret')
            (outside/'secret').chmod(0o640)
            return root, outside

        for adapter in ('c', 'llvm'):
            for optimization in args.optimization or (0, 2, 3):
                binary = home/f'{adapter}-{optimization}'
                command = [clang, str(source), str(runtime/'freak_runtime.c'), f'-I{runtime}', f'-O{optimization}',
                           '-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1', '-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1', *flags, '-o', str(binary)]
                if adapter == 'llvm':
                    command += ['-DUSE_LLVM_ADAPTER=1', str(runtime/'freak_llvm_runtime.c')]
                if sys.platform.startswith('linux'):
                    command += ['-DTEST_INTERPOSE=1', '-Wl,--wrap=openat', '-Wl,--wrap=fchmod', '-Wl,--wrap=fsync', '-Wl,--wrap=close', '-Wl,--wrap=fstat']
                compiled = subprocess.run(command, capture_output=True, timeout=90)
                assert compiled.returncode == 0, (compiled.stdout, compiled.stderr)
                names = ['metadata', '600', '640', '644', '751', '000', '777', 'negative', 'privilege', 'sticky', 'out-of-range', 'missing', 'directory', 'unsafe']
                if os.name != 'nt':
                    names += ['link', 'ancestor-link', 'hardlink', 'unsafe-parent']
                    if os.geteuid() == 0:
                        names += ['foreign-file']
                    elif Path('/etc/hosts').is_file() and Path('/etc').stat().st_uid != os.geteuid() and not Path('/etc').stat().st_mode & 0o022:
                        names += ['native-foreign-parent']
                if sys.platform.startswith('linux'):
                    names += ['ancestor-race', 'file-exchange', 'chmod-fault', 'sync-fault', 'close-fault', 'foreign-file-metadata']
                for name in names:
                    root, outside = fixture(f'{adapter}-{optimization}-{name}')
                    fixture_root = root
                    relative, mode = 'a', int(name, 8) if name.isdigit() else 0o644
                    expected = [0, 0] if os.name == 'nt' else [1, 1]
                    if name in ('negative', 'privilege', 'sticky', 'out-of-range', 'missing', 'directory', 'unsafe', 'link', 'ancestor-link', 'hardlink', 'unsafe-parent', 'native-foreign-parent', 'foreign-file', 'foreign-file-metadata', 'chmod-fault'):
                        expected = [0, 0]
                    if name in ('sync-fault', 'close-fault', 'file-exchange'):
                        expected = [0, 1]
                    if name == 'negative': mode = -1
                    if name == 'privilege': mode = 0o4000
                    if name == 'sticky': mode = 0o1000
                    if name == 'out-of-range': mode = 0o10000
                    if name == 'missing': relative = 'absent'
                    if name == 'directory': relative = 'directory'; (root/relative).mkdir()
                    if name == 'unsafe': relative = '../outside/secret'
                    if name == 'link': relative = 'link'; (root/relative).symlink_to(outside/'secret')
                    if name == 'hardlink': relative = 'hardlink'; os.link(outside/'secret', root/relative)
                    if name in ('ancestor-link', 'ancestor-race'):
                        relative = 'pivot/a'
                        if name == 'ancestor-link': (root/'pivot').symlink_to(outside, target_is_directory=True)
                        else:
                            (root/'pivot').mkdir(); (root/'a').rename(root/relative)
                    if name == 'unsafe-parent': root.chmod(0o777)
                    foreign_before = None
                    if name == 'native-foreign-parent':
                        root, relative = Path('/etc'), 'hosts'
                        foreign_before = ((root/relative).read_bytes(), (root/relative).stat())
                    if name == 'foreign-file':
                        root.chown(65534, 65534)
                        (root/'a').chmod(0o644)
                    fault_context = str(root) if name == 'file-exchange' else str(outside)
                    if name == 'file-exchange': (root/'secret').write_bytes(b'entry-swap-secret'); (root/'secret').chmod(0o640)
                    if name == 'metadata': (root/'a').chmod(0o4751)
                    child_options = {}
                    if name == 'foreign-file' and os.geteuid() == 0:
                        def unprivileged() -> None:
                            os.setgroups([]); os.setgid(65534); os.setuid(65534)
                        child_options['preexec_fn'] = unprivileged
                    result = subprocess.run([str(binary), str(root), relative, str(mode), name, fault_context], env=environment,
                                            capture_output=True, timeout=15, **child_options)
                    assert result.returncode == 0 and not result.stderr, (adapter, optimization, name, result.returncode, result.stdout, result.stderr)
                    values = list(map(int, result.stdout.split()))
                    wanted_values = ([0, 0] if os.name == 'nt' else [0o4751, 0o4751]) if name == 'metadata' else expected
                    assert values == wanted_values, (name, values, wanted_values)
                    if foreign_before:
                        assert (root/relative).read_bytes() == foreign_before[0]
                        after = (root/relative).stat()
                        fields = ('st_dev', 'st_ino', 'st_mode', 'st_uid', 'st_gid', 'st_size', 'st_nlink', 'st_mtime_ns', 'st_ctime_ns')
                        assert all(getattr(after, field) == getattr(foreign_before[1], field) for field in fields)
                        root = fixture_root
                    assert (outside/'secret').read_bytes() == b'outside-secret'
                    if os.name != 'nt':
                        assert stat.S_IMODE((outside/'secret').stat().st_mode) == 0o640
                        if name == 'file-exchange':
                            inspected = root/'retained'
                            assert (root/'a').is_symlink() and (root/'secret').read_bytes() == b'entry-swap-secret' and stat.S_IMODE((root/'secret').stat().st_mode) == 0o640
                        elif name == 'ancestor-race': inspected = root/'retained'/'a'
                        else: inspected = root/'a'
                        actual_mode = stat.S_IMODE(inspected.stat().st_mode)
                        wanted = 0o4751 if name == 'metadata' else mode if expected[1] else 0o644 if name == 'foreign-file' else 0o600
                        assert actual_mode == wanted, (name, oct(actual_mode), oct(wanted))
                        inspected.chmod(0o600)
                    inspected = inspected if os.name != 'nt' else root/'a'
                    assert inspected.read_bytes() == b'unchanged\x00\xffcontent'
                    records.append({'adapter': adapter, 'optimization': optimization, 'case': name, 'status': 'pass'})
                print(f'PASS file modes {adapter} O{optimization}: {len(names)} native cases', flush=True)
        if args.compiler:
            compiler = args.compiler.resolve(strict=True)
            report['compiler_sha256'] = hashlib.sha256(compiler.read_bytes()).hexdigest()
            consumer = home/'consumer.fk'
            consumer.write_text(CONSUMER)
            for adapter in ('c', 'llvm'):
                generated = Path(str(consumer)+('.c' if adapter == 'c' else '.ll'))
                compiled = subprocess.run([str(compiler), str(consumer), '--'+adapter, '--strict-borrow'], capture_output=True, timeout=90)
                assert compiled.returncode == 0, (compiled.stdout, compiled.stderr)
                assert 'freak_'+('llvm_' if adapter == 'llvm' else '')+'fs_set_mode_relative_checked' in generated.read_text()
                for optimization in args.optimization or (0, 2, 3):
                    binary = home/f'language-{adapter}-{optimization}'
                    command = [clang, str(generated), str(runtime/'freak_runtime.c'), f'-I{runtime}', f'-O{optimization}', *flags, '-o', str(binary)]
                    if adapter == 'llvm': command += [str(runtime/'freak_llvm_runtime.c')]
                    compiled = subprocess.run(command, capture_output=True, timeout=90)
                    assert compiled.returncode == 0, compiled.stderr
                    for name in ('ordinary', 'nul', 'unsafe'):
                        root, outside = fixture(f'language-{adapter}-{optimization}-{name}')
                        relative = '../outside/secret' if name == 'unsafe' else 'a'
                        result = subprocess.run([str(binary), str(root), relative, name], env=environment, capture_output=True, timeout=15)
                        expected = b'true\ntrue\n' if name == 'ordinary' and os.name != 'nt' else b'false\nfalse\n'
                        assert result.returncode == 0 and not result.stderr and result.stdout.replace(b'\r\n', b'\n') == expected, (name, result)
                        if os.name != 'nt': assert stat.S_IMODE((root/'a').stat().st_mode) == (0o644 if name == 'ordinary' else 0o600)
                        assert (root/'a').read_bytes() == b'unchanged\x00\xffcontent' and (outside/'secret').read_bytes() == b'outside-secret'
                        records.append({'adapter': adapter, 'optimization': optimization, 'case': 'language-'+name, 'status': 'pass'})
    assert hashes == {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}, 'runtime changed during verification'
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True); args.report.write_text(json.dumps(report, indent=2)+'\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
