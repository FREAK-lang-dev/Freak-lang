#!/usr/bin/env python3
"""Prove explicit panic-abort source lowering, sealed policy and native behavior.

Every listed program runs at O0/O2/O3. ASan/UBSan and both ownership audits are
mandatory by default; --plain adds portable proof. Fatal stderr is exact bytes
on every platform. Compiler emission/restore stays within64MiB/1024 handles.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
from types import SimpleNamespace
from typing import NamedTuple

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src/compiler/v4'), str(ROOT / 'tests')]
from v4_owned_word_codegen import assert_native_output
from v4_panic_runtime import assert_exact_abort
from v4_checked_numeric_codegen import (AUDIT_FLAGS, SANITIZER_FLAGS, Runner,
    exact_result, sanitizer_environment, validate_build_flags, validate_sanitizer_probe)

OPTS = (0, 2, 3)
PREFIX = 'panic-abort-execute stages=clean v8-restore=true old-seal=true fresh-module=true policy=abort\n'

def require_native_link(result, target: str, *, platform: str = sys.platform) -> None:
    # Clang canonicalizes the supported generic Darwin triple to the selected
    # SDK version. Accept that one same-architecture diagnostic, retaining the
    # raw stderr; every other warning, output, or failed link remains an error.
    canonical_darwin = (
        platform == 'darwin' and target == 'aarch64-apple-darwin'
        and re.fullmatch(
            r'warning: overriding the module target triple with arm64-apple-macosx[0-9]+(?:\.[0-9]+){0,2} \[-Woverride-module\]\n1 warning generated\.\n',
            result.stderr,
        ) is not None
    )
    if result.returncode != 0 or result.stdout or (result.stderr and not canonical_darwin):
        raise RuntimeError(f'panic native link failed: {result.stderr}')

class Case(NamedTuple):
    name: str
    source: str
    stdout: str
    message: str | None


def main_source(body: str, *, result: str = 'int', helpers: str = '') -> str:
    return helpers + 'task main() -> ' + result + ' {\n' + body + '\n}\n'


def cases() -> tuple[Case, ...]:
    first = 'task first() -> int { say "first"; give back 1 }\n'
    take = 'task take(value: word) -> word { give back value }\n'
    allocation = ('extern [C] {\n task malloc(size: std::ffi::c_size) -> *mut std::ffi::c_void\n'
                  ' task free(value: *mut std::ffi::c_void) -> void\n}\n')
    address = ('task owned_address(value: word, pointer: *mut int) -> *mut int { say "address"; say value.length(); give back pointer }\n'
               'task borrowed_address(lend value: word, pointer: *mut int) -> *mut int { say "address"; say value.length(); give back pointer }\n'
               'task rhs_observe(lend value: word) -> int { say "rhs"; give back value.length() }\n'
               'task consume(value: word) -> int { say "consume"; say value.length(); give back 7 }\n')
    allocated = ('pilot text = "abc"\npilot raw = malloc(8)\n'
                 'trust me "assignment order" on my honor as .ace {\npilot pointer = raw.cast<int>()\n')
    released = '\nsay *pointer\nfree(raw)\ngive back 0\n}'
    return (
        Case('unicode-nul', main_source('pilot message = "AbOrT\\0ΟΣ İ 𐐀"\npanic(msg: message.to_lower())', result='never'), '', 'abort\0ος i\u0307 𐐨'),
        Case('empty', main_source('panic("")'), '', ''),
        Case('binary-before', main_source('pilot unused = first() + panic("binary")', helpers=first), 'first\n', 'binary'),
        Case('nested', main_source('panic(panic("inner"))'), '', 'inner'),
        Case('assignment-live', main_source('pilot mut value = "old"\nvalue = panic(value)'), '', 'old'),
        Case('return', main_source('give back panic("return")'), '', 'return'),
        Case('condition', main_source('if panic("condition") { give back 1 } else { give back 2 }'), '', 'condition'),
        Case('negative', main_source('give back -(panic("negative"))'), '', 'negative'),
        Case('times', main_source('repeat panic("times") times { say "suppressed" }'), '', 'times'),
        Case('until', main_source('repeat until panic("until") { say "suppressed" }'), '', 'until'),
        Case('ordinary-never', main_source('pilot value = "ordinary"\nstop(lend value)', result='never', helpers='task stop(lend value: word) -> never { panic(value) }\n'), '', 'ordinary'),
        Case('arrow-never', main_source('stop()', helpers='task stop() => panic("arrow")\n'), '', 'arrow'),
        Case('owned-temporary', main_source('pilot value = "TEMP"\npanic(take(value).to_lower())', helpers=take), '', 'temp'),
        Case('named-order', main_source('give back target(b: panic("named"), a: first())', helpers=first+'task target(a: int, b: int) -> int { give back a + b }\n'), 'first\n', 'named'),
        Case('short-and-fatal', main_source('pilot value = true and panic("and")'), '', 'and'),
        Case('short-or-fatal', main_source('pilot value = false or panic("or")'), '', 'or'),
        Case('short-happy', main_source('pilot a = false and panic("hidden-and")\npilot b = true or panic("hidden-or")\npilot value = "owned"\nsay value\nif a or not b { give back 1 }\ngive back 0'), 'owned\n', None),
        Case('shadow-task', main_source('pilot value = panic(msg: 7)\nsay value\ngive back 0', helpers='task panic(msg: int) -> int { give back msg }\n'), '7\n', None),
        Case('branch-both-terminal', main_source('say "before"\nif true { panic("then") } else { panic("else") }\nsay "suppressed"\ngive back 0'), 'before\n', 'then'),
        Case('branch-happy', main_source('pilot flag = true\nif flag { say "live"; give back 0 } else { panic("branch") }'), 'live\n', None),
        Case('assignment-rhs-before-address', main_source(allocated+'*owned_address(text, pointer) = rhs_observe(lend text)'+released, helpers=allocation+address), 'rhs\naddress\n3\n3\n', None),
        Case('raw-write-receiver-before-value', main_source(allocated+'borrowed_address(lend text, pointer).write(consume(text))'+released, helpers=allocation+address), 'address\n3\nconsume\n3\n7\n', None),
    )


def extract_module(result, *, platform: str = sys.platform) -> str:
    actual = result.stdout.replace('\r\n', '\n') if platform == 'win32' else result.stdout
    begin, end = '@@LLVM-MODULE-BEGIN\n', '@@LLVM-MODULE-END\n'
    if result.returncode != 0 or result.stderr or not actual.startswith(PREFIX+begin) or not actual.endswith(end):
        raise RuntimeError(f'panic compiler protocol failed: {result.returncode}, {result.stdout!r}, {result.stderr!r}')
    if actual.count(begin) != 1 or actual.count(end) != 1:
        raise RuntimeError('panic compiler module markers must occur exactly once')
    module = actual[len(PREFIX+begin):-len(end)]
    if not module.strip():
        raise RuntimeError('panic compiler emitted an empty module')
    return module


def assert_case(result, case: Case, *, platform: str = sys.platform) -> None:
    if case.message is None:
        assert_native_output(result, case.stdout, platform=platform)
        return
    # Only ordinary stdout text uses the Windows CRT newline convention.
    # The reviewed panic helper switches stderr to binary before writing bytes.
    stdout = result.stdout.replace('\r\n', '\n') if platform == 'win32' else result.stdout
    if stdout != case.stdout:
        raise RuntimeError(f'panic preceding effects differ: {result.stdout!r}, expected {case.stdout!r}')
    fatal = SimpleNamespace(returncode=result.returncode, stdout=b'', stderr=result.stderr.encode('utf-8'))
    try:
        assert_exact_abort(fatal, ('PANIC: '+case.message+'\n').encode('utf-8'), platform=platform)
    except AssertionError as error:
        raise RuntimeError(str(error)) from error


def validate_report(report: dict, *, sanitize: bool) -> None:
    expected = {(case.name, opt) for case in cases() for opt in OPTS}
    rows = report.get('programs', [])
    if len(rows) != len(expected) or {(row.get('name'),row.get('optimization')) for row in rows} != expected:
        raise RuntimeError('panic program/optimization matrix is missing, duplicated or unknown')
    if report.get('sanitizers') is not sanitize:
        raise RuntimeError('panic report sanitizer mode does not match requested proof')
    table = {case.name:case for case in cases()}
    for row in rows:
        case = table[row['name']]
        status = 0 if case.message is None else (3 if report.get('platform') == 'win32' else -signal.SIGABRT)
        stderr = '' if case.message is None else 'PANIC: '+case.message+'\n'
        if (row.get('status') != 'pass' or row.get('ownership_audits') != ['C','LLVM']
                or row.get('policy') != 'abort' or row.get('exit') != status
                or row.get('stdout_sha256') != hashlib.sha256(case.stdout.encode()).hexdigest()
                or row.get('stderr_sha256') != hashlib.sha256(stderr.encode()).hexdigest()):
            raise RuntimeError('panic report has a failed exact oracle, policy, audit or output fact')
    required = {f'audit-{kind}-O{opt}' for kind in ('C','LLVM') for opt in OPTS}
    if sanitize: required |= {'sanitizer-address','sanitizer-undefined'}
    controls = report.get('controls', [])
    if len(controls) != len(required) or {row.get('name') for row in controls} != required or any(row.get('status')!='pass' for row in controls):
        raise RuntimeError('panic report lacks actual sanitizer/audit capability controls')


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_gate(args, report: dict) -> None:
    import build_v4 as build
    from freakc.v4_native_runtime import HEADER_NAMES
    checks = build.checks
    work = args.work.resolve(); work.mkdir(parents=True,exist_ok=True)
    runner = Runner(checks,work)
    fixture = checks.V4_ROOT/'tests/panic_abort_execute_smoke.fk'
    if not fixture.is_file(): raise RuntimeError('required panic compiler fixture is unavailable')
    checks.check_individual_parse([fixture])
    flat = checks.check_flattened_crates()
    source,ui = checks.transpile_fixture(flat,fixture)
    if ui: raise RuntimeError('panic compiler fixture unexpectedly requires UI')
    old_root = checks.RUNTIME_BUILD_ROOT
    checks.RUNTIME_BUILD_ROOT = work/'compiler'; checks.RUNTIME_BUILD_ROOT.mkdir(parents=True,exist_ok=True)
    try:
        runtime=checks.RUNTIME_ROOT/'freak_runtime.c'
        compiler,_=checks.compile_runtime_smoke(args.clang,f'-I{checks.RUNTIME_ROOT}',runtime,checks.read_text(runtime),fixture,source,('-DFREAK_ARRAY_LIVE_LIMIT=1024',))
    finally: checks.RUNTIME_BUILD_ROOT=old_root
    target=build.host_target(); report['target']=target
    report['fixture_sha256']=sha(fixture);report['driver_sha256']=sha(Path(__file__))
    report['compiler_crate_inputs']={name:sha(checks.crate_path(name)) for name in checks.CRATE_ORDER}
    report['compiler_process_contract']={'memory_limit_mib':64,'live_handle_limit':1024}
    report['compiler_binary_sha256']=sha(compiler)
    report['compiler_generated_c_sha256']=sha(work/'compiler'/f'{fixture.name}.c')
    report['runtime_sources']={name:sha(checks.RUNTIME_ROOT/name) for name in build.SOURCE_NAMES}
    report['runtime_headers']={name:sha(checks.RUNTIME_ROOT/name) for name in HEADER_NAMES}
    report['compiler_head']=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
    suffix='.exe' if sys.platform=='win32' else '.native'
    audit=work/'audit_probe.c';audit.write_text('''#include "freak_runtime.h"
#include "freak_v4_word_runtime.h"
int main(int argc,char **argv) {
 if(argc!=2)return 9;
 if(argv[1][0]=='C'){volatile freak_word x=freak_word_from_int(7);(void)x;}
 else {volatile int64_t x=freak_v4_word_from_int(7);(void)x;}
 return 0;
}
''')
    objects={}
    with sanitizer_environment(not args.plain):
        for opt in OPTS:
            # Keep every linked object and control on the emitted module's ABI.
            # MSVC-default /DEFAULTLIB directives are invalid for the GNU PE linker.
            flags=['-w',f'-O{opt}',f'-I{checks.RUNTIME_ROOT}',*AUDIT_FLAGS]
            if not args.plain: flags+=list(SANITIZER_FLAGS)
            validate_build_flags(flags,not args.plain);objects[opt]=[]
            for name in build.SOURCE_NAMES:
                path=checks.RUNTIME_ROOT/name;output=work/f'{path.stem}.O{opt}{".obj" if sys.platform=="win32" else ".o"}'
                result=runner.run([args.clang,'--target='+target,*flags,'-c',str(path),'-o',str(output)],f'panic runtime {path.stem} O{opt}',timeout=120,memory=512)
                if result.returncode!=0:raise RuntimeError(f'panic runtime compile failed: {result.stderr}')
                objects[opt].append(str(output))
            binary=work/f'audit-O{opt}{suffix}'
            result=runner.run([args.clang,'--target='+target,*flags,str(audit),*objects[opt],'-o',str(binary),*checks.runtime_platform_final_link_args()],f'panic audit link O{opt}',timeout=120,memory=512)
            if result.returncode!=0:raise RuntimeError(f'panic audit compile failed: {result.stderr}')
            for kind,status in (('C',87),('LLVM',86)):
                actual=runner.run([str(binary),kind],f'panic audit {kind} O{opt}',timeout=30,memory=128)
                exact_result(actual,status,'',f'FREAK: {kind} ownership audit found 1 unreleased word allocation(s)\n',kind)
                report['controls'].append({'name':f'audit-{kind}-O{opt}','status':'pass'})
        if not args.plain:
            probe=work/'sanitizer_probe.c';probe.write_text('''#include <stdlib.h>
#include <limits.h>
int main(int argc,char **argv){if(argc!=2)return 9;if(argv[1][0]=='a'){volatile char *p=malloc(1);free((void*)p);return p[0];}volatile int x=INT_MAX;volatile int one=1;return x+one;}
''')
            binary=work/f'sanitizer-probe{suffix}'
            result=runner.run([args.clang,'--target='+target,'-O0',*SANITIZER_FLAGS,str(probe),'-o',str(binary)],'panic sanitizer link',timeout=120,memory=512)
            if result.returncode!=0:raise RuntimeError('sanitizer capability compile failed')
            for kind in ('address','undefined'):
                validate_sanitizer_probe(runner.run([str(binary),kind],f'panic sanitizer {kind}',timeout=30,memory=128),kind)
                report['controls'].append({'name':'sanitizer-'+kind,'status':'pass'})
        for case in cases():
            source_path=work/f'{case.name}.fk';source_path.write_text(case.source,encoding='utf-8')
            emitted=runner.run([str(compiler),str(source_path),target],'panic emit '+case.name,timeout=60,memory=64)
            module=extract_module(emitted);llvm=work/f'{case.name}.ll';llvm.write_bytes(module.encode())
            if case.message is not None and ('declare void @freak_v4_panic_abort(i64) noreturn' not in module or 'call void @freak_v4_panic_abort(i64 ' not in module):
                raise RuntimeError('fatal source has no actual reviewed abort helper')
            for opt in OPTS:
                binary=work/f'{case.name}-O{opt}{suffix}'
                flags=[f'-O{opt}',*AUDIT_FLAGS]
                if not args.plain:flags+=list(SANITIZER_FLAGS)
                result=runner.run([args.clang,'--target='+target,*flags,str(llvm),*objects[opt],'-o',str(binary),*checks.runtime_platform_final_link_args()],f'panic link {case.name} O{opt}',timeout=120,memory=512)
                require_native_link(result, target)
                result=runner.run([str(binary)],f'panic execute {case.name} O{opt}',timeout=30,memory=128)
                assert_case(result,case)
                actual=result.stdout.replace('\r\n','\n') if sys.platform=='win32' else result.stdout
                report['programs'].append({'name':case.name,'optimization':opt,'status':'pass','ownership_audits':['C','LLVM'],'policy':'abort','exit':result.returncode,'source_sha256':sha(source_path),'module_sha256':sha(llvm),'binary_sha256':sha(binary),'stdout_sha256':hashlib.sha256(actual.encode()).hexdigest(),'stderr_sha256':hashlib.sha256(result.stderr.encode()).hexdigest()})
                print(f'panic {case.name} O{opt}: exact exit/output PASS',flush=True)
    validate_report(report,sanitize=not args.plain)


def main(argv: list[str]|None=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clang',default=os.environ.get('FREAK_CLANG') or shutil.which('clang'))
    parser.add_argument('--plain',action='store_true')
    parser.add_argument('--work',type=Path,default=ROOT/'build/v4_smoke/panic_abort_native')
    parser.add_argument('--report',type=Path)
    args=parser.parse_args(argv)
    if not args.clang:parser.error('clang is required; panic execution cannot be skipped')
    report={'platform':sys.platform,'sanitizers':not args.plain,'programs':[],'controls':[]}
    try:run_gate(args,report)
    finally:
        path=args.report or args.work/'report.json';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(report,indent=2)+'\n')
    return 0

if __name__=='__main__':raise SystemExit(main())
