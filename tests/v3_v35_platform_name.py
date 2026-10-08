#!/usr/bin/env python3
"""Verify native host names through both runtime ABIs and optional source calls."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


HARNESS = r'''
#include "freak_runtime.h"
#include <stdio.h>
#ifdef USE_LLVM_ADAPTER
extern void freak_llvm_word_release_replaced(int64_t,int64_t);
#endif
int main(void) {
    for(int i=0;i<1024;i++) {
#ifdef USE_LLVM_ADAPTER
        int64_t value=freak_llvm_process_platform_name();
        freak_word name=freak_llvm_word_view(value);
#else
        freak_word name=freak_process_platform_name();
#endif
        if(i==0) { fwrite(name.data,1,name.length,stdout);putchar('\n'); }
#ifdef USE_LLVM_ADAPTER
        freak_llvm_word_release_replaced(value,0);
#else
        freak_word_release_owned(&name);
#endif
    }
    return 0;
}
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clang', default=os.environ.get('FREAK_CLANG', 'clang'))
    parser.add_argument('--compiler', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    clang = shutil.which(args.clang)
    assert clang, args.clang
    runtime = Path(__file__).resolve().parents[1]/'freakc'/'runtime'
    paths = [runtime/name for name in ('freak_runtime.c', 'freak_runtime.h', 'freak_llvm_runtime.c')]
    hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    expected = ('windows' if sys.platform == 'win32' else 'macos' if sys.platform == 'darwin' else 'linux' if sys.platform.startswith('linux') else 'unknown').encode()+b'\n'
    flags = ['-lws2_32', '-lshell32'] if os.name == 'nt' else ['-lm']
    environment = dict(os.environ, OS='Windows_NT', OSTYPE='darwin', FREAK_PLATFORM='invented')
    cases = []
    with tempfile.TemporaryDirectory(prefix='freak-native-platform-') as temporary:
        home = Path(temporary)
        source = home/'harness.c'
        source.write_text(HARNESS)
        for adapter in ('c', 'llvm'):
            binary = home/adapter
            command = [clang, str(source), str(runtime/'freak_runtime.c'), f'-I{runtime}', '-O2',
                       '-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1', '-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1', *flags, '-o', str(binary)]
            if adapter == 'llvm': command += ['-DUSE_LLVM_ADAPTER=1', str(runtime/'freak_llvm_runtime.c')]
            built = subprocess.run(command, capture_output=True, timeout=90)
            assert built.returncode == 0, built.stderr
            result = subprocess.run([str(binary)], env=environment, capture_output=True, timeout=15)
            assert result.returncode == 0 and not result.stderr and result.stdout.replace(b'\r\n', b'\n') == expected, result
            cases.append({'adapter': adapter, 'case': 'native-and-forged-env', 'repetitions': 1024, 'status': 'pass'})
        if args.compiler:
            compiler = args.compiler.resolve(strict=True)
            source = home/'consumer.fk'
            source.write_text('task main() { say process::platform_name() }\n')
            for adapter in ('c', 'llvm'):
                generated = Path(str(source)+('.c' if adapter == 'c' else '.ll'))
                built = subprocess.run([str(compiler), str(source), '--'+adapter, '--strict-borrow'], capture_output=True, timeout=90)
                assert built.returncode == 0, (built.stdout, built.stderr)
                assert 'freak_'+('llvm_' if adapter == 'llvm' else '')+'process_platform_name' in generated.read_text()
                binary = home/('language-'+adapter)
                command = [clang, str(generated), str(runtime/'freak_runtime.c'), f'-I{runtime}', '-O2', *flags, '-o', str(binary)]
                if adapter == 'llvm': command += [str(runtime/'freak_llvm_runtime.c')]
                linked = subprocess.run(command, capture_output=True, timeout=90)
                assert linked.returncode == 0, linked.stderr
                result = subprocess.run([str(binary)], env=environment, capture_output=True, timeout=15)
                assert result.returncode == 0 and not result.stderr and result.stdout.replace(b'\r\n', b'\n') == expected, result
                cases.append({'adapter': adapter, 'case': 'native-language', 'status': 'pass'})
    assert hashes == {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}, 'runtime changed during verification'
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps({'runtime_sha256': hashes, 'native_platform': sys.platform, 'cases': cases}, indent=2)+'\n')
    print(f'PASS native platform name: {len(cases)} cases', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
