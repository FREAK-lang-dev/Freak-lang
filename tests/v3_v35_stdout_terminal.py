#!/usr/bin/env python3
"""Verify native stdout terminal detection through C and LLVM runtime APIs.

Real pipes, files and POSIX PTYs provide independent output-stream oracles.
Optional source consumers exercise the self-hosted compiler's actual binding.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import select
import shutil
import subprocess
import tempfile


HARNESS = r'''
#include "freak_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <windows.h>
#include <io.h>
#endif
static void require(int ok,const char *why) { if(!ok) { fprintf(stderr,"FAIL: %s\n",why);exit(2); } }
int main(int argc,char **argv) {
#ifdef _WIN32
    if(argc==3 && !strcmp(argv[1],"console")) {
        FreeConsole();require(AllocConsole(),"allocate real console");
        require(freopen("CONOUT$","w",stdout)!=NULL,"CRT console stdout");
    }
#endif
    if(argc==3 && !strcmp(argv[1],"redirect")) require(freopen(argv[2],"wb",stdout)!=NULL,"redirect CRT stdout");
#ifdef USE_LLVM_ADAPTER
#define TERMINAL freak_llvm_process_stdout_is_terminal
#else
#define TERMINAL freak_process_stdout_is_terminal
#endif
    int actual=(int)TERMINAL();
    for(int i=0;i<1024;i++) require((int)TERMINAL()==actual,"stable allocation-free detection");
#ifdef _WIN32
    if(argc==3 && !strcmp(argv[1],"console")) {
        require(actual==1,"actual Windows console");
        require(freopen(argv[2],"wb",stdout)!=NULL,"redirect console CRT stream");
        require(TERMINAL()==0,"redirected console is no longer stdout terminal");actual=0;
    }
#endif
    printf("%d\n",actual);require(fflush(stdout)==0,"flush fixture result");return 0;
}
'''

CONSUMER = '''task main() {
    say process::stdout_is_terminal()
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
    paths = [runtime/name for name in ('freak_runtime.c', 'freak_runtime.h', 'freak_llvm_runtime.c')]
    hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    records: list[dict] = []
    report = {'runtime_sha256': hashes, 'sanitized': args.sanitize, 'cases': records, 'native_platform': os.name}
    environment = dict(os.environ, ASAN_OPTIONS='detect_leaks=1:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1')
    flags = ['-lws2_32', '-lshell32'] if os.name == 'nt' else ['-lm']
    if args.sanitize:
        flags += ['-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-g']
    with tempfile.TemporaryDirectory(prefix='freak-terminal-') as temporary:
        home = Path(temporary)
        source = home/'harness.c'
        source.write_text(HARNESS)
        if args.sanitize:
            for name, code, diagnostic in [
                ('address', '#include <stdlib.h>\nint main(int n,char **v){volatile char *p=malloc(1);p[n+4]=3;free((void*)p);return 0;}\n', b'AddressSanitizer'),
                ('undefined', '#include <limits.h>\nint main(void){volatile int n=INT_MAX;return n+1;}\n', b'runtime error:')]:
                control = home/(name+'.c')
                control.write_text(code)
                binary = home/name
                compiled = subprocess.run([clang, str(control), '-O2', *flags, '-o', str(binary)], capture_output=True, timeout=60)
                assert compiled.returncode == 0, compiled.stderr
                result = subprocess.run([str(binary)], env=environment, capture_output=True, timeout=15)
                assert result.returncode != 0 and diagnostic in result.stderr, (name, result)
                records.append({'case': 'positive-'+name, 'status': 'pass'})

        def execute(binary: Path, label: str, expected_false: bytes, expected_true: bytes, environment: dict, language: bool = False) -> None:
            result = subprocess.run([str(binary)], env=environment, capture_output=True, timeout=15)
            assert result.returncode == 0 and result.stdout.replace(b'\r\n', b'\n') == expected_false and not result.stderr, (label, result)
            records.append({'case': label+'-pipe', 'status': 'pass'})
            fake_terminal = dict(environment, TERM='xterm-256color', COLORTERM='truecolor', FORCE_COLOR='1')
            result = subprocess.run([str(binary)], env=fake_terminal, capture_output=True, timeout=15)
            assert result.returncode == 0 and result.stdout.replace(b'\r\n', b'\n') == expected_false and not result.stderr, (label, result)
            records.append({'case': label+'-pipe-forged-environment', 'status': 'pass'})
            output = home/(label+'-file')
            with output.open('wb') as file:
                result = subprocess.run([str(binary)], stdout=file, stderr=subprocess.PIPE, env=fake_terminal, timeout=15)
            assert result.returncode == 0 and not result.stderr and output.read_bytes().replace(b'\r\n', b'\n') == expected_false
            records.append({'case': label+'-file', 'status': 'pass'})
            if os.name == 'nt':
                if not language:
                    console_file = home/(label+'-console-redirect')
                    result = subprocess.run([str(binary), 'console', str(console_file)], env=environment, capture_output=True, timeout=15)
                    assert result.returncode == 0 and not result.stderr and console_file.read_bytes().replace(b'\r\n', b'\n') == expected_false, (label, result)
                    records.append({'case': label+'-real-console-then-CRT-redirect', 'status': 'pass'})
            else:
                import pty
                for term in ('xterm-256color', ''):
                    master, slave = pty.openpty()
                    try:
                        result = subprocess.run([str(binary)], stdout=slave, stderr=subprocess.PIPE, env=dict(environment, TERM=term), timeout=15)
                        assert result.returncode == 0 and not result.stderr, (label, term, result)
                        assert select.select([master], [], [], 5)[0], (label, 'PTY output timeout')
                        received = os.read(master, 4096)
                        assert result.returncode == 0 and not result.stderr and received.replace(b'\r\n', b'\n') == expected_true, (label, term, result, received)
                    finally:
                        os.close(slave)
                        os.close(master)
                    records.append({'case': label+'-PTY-'+('TERM' if term else 'no-TERM'), 'status': 'pass'})
                if not language:
                    master, slave = pty.openpty()
                    redirected = home/(label+'-CRT-redirect')
                    try:
                        result = subprocess.run([str(binary), 'redirect', str(redirected)], stdout=slave, stderr=subprocess.PIPE, env=fake_terminal, timeout=15)
                        assert result.returncode == 0 and not result.stderr and redirected.read_bytes() == expected_false, (label, result)
                    finally:
                        os.close(slave)
                        os.close(master)
                    records.append({'case': label+'-PTY-then-CRT-redirect', 'status': 'pass'})

        for adapter in ('c', 'llvm'):
            for optimization in args.optimization or (0, 2, 3):
                binary = home/f'{adapter}-{optimization}'
                command = [clang, str(source), str(runtime/'freak_runtime.c'), f'-I{runtime}', f'-O{optimization}', *flags, '-o', str(binary)]
                if adapter == 'llvm':
                    command += ['-DUSE_LLVM_ADAPTER=1', str(runtime/'freak_llvm_runtime.c')]
                compiled = subprocess.run(command, capture_output=True, timeout=90)
                assert compiled.returncode == 0, compiled.stderr
                execute(binary, f'{adapter}-O{optimization}', b'0\n', b'1\n', environment)
                print(f'PASS stdout terminal {adapter} O{optimization}', flush=True)
        if args.compiler:
            compiler = args.compiler.resolve(strict=True)
            report['compiler_sha256'] = hashlib.sha256(compiler.read_bytes()).hexdigest()
            consumer = home/'consumer.fk'
            consumer.write_text(CONSUMER)
            for adapter in ('c', 'llvm'):
                generated = Path(str(consumer)+('.c' if adapter == 'c' else '.ll'))
                compiled = subprocess.run([str(compiler), str(consumer), '--'+adapter, '--strict-borrow'], capture_output=True, timeout=90)
                assert compiled.returncode == 0, compiled.stderr
                assert 'freak_'+('llvm_' if adapter == 'llvm' else '')+'process_stdout_is_terminal' in generated.read_text()
                for optimization in args.optimization or (0, 2, 3):
                    binary = home/f'language-{adapter}-{optimization}'
                    command = [clang, str(generated), str(runtime/'freak_runtime.c'), f'-I{runtime}', f'-O{optimization}', *flags, '-o', str(binary)]
                    if adapter == 'llvm':
                        command += [str(runtime/'freak_llvm_runtime.c')]
                    linked = subprocess.run(command, capture_output=True, timeout=90)
                    assert linked.returncode == 0, linked.stderr
                    execute(binary, f'language-{adapter}-O{optimization}', b'false\n', b'true\n', environment, language=True)
                    print(f'PASS source stdout terminal {adapter} O{optimization}', flush=True)
    assert hashes == {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}, 'runtime changed during verification'
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2)+'\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
