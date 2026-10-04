#!/usr/bin/env python3
"""Prove bounded owning scalar Sum constructors, extraction and native cleanup.

Every listed program runs at O0/O2/O3. ASan/UBSan and both ownership audits are
mandatory by default; --plain adds portable proof. Native stdout/stderr is exact bytes on POSIX; Windows CRT text
newlines are handled only by the shared output oracle. Compiler emission/restore stays within64MiB/1024 handles.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from contextlib import contextmanager
from typing import NamedTuple

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src/compiler/v4'), str(ROOT / 'tests')]
from v4_owned_word_codegen import assert_native_output
from v4_checked_numeric_codegen import (AUDIT_FLAGS, SANITIZER_FLAGS, Runner,
    exact_result, sanitizer_environment, validate_build_flags, validate_sanitizer_probe)

OPTS = (0, 2, 3)
PREFIX = 'scalar-sum-execute stages=clean v9-restore=true old-seal=true fresh-module=true\n'

class Case(NamedTuple):
    name: str
    source: str
    stdout: str


def main_source(body: str, *, result: str = 'int', helpers: str = '') -> str:
    return helpers + 'task main() -> ' + result + ' {\n' + body + '\n}\n'


def cases() -> tuple[Case, ...]:
    relay = 'task relay(value: result<word,word>) -> result<word,word> { give back value }\n'
    return (
        Case('maybe-zero-boundaries', main_source('pilot zero: maybe<int> = some(0)\ncheck zero { got n -> { say n } nobody -> { give back 1 } }\npilot low: maybe<int> = some(-9223372036854775808)\ncheck low { got n -> { say n } nobody -> { give back 2 } }\npilot high: maybe<int> = some(9223372036854775807)\ncheck high { got n -> { say n } nobody -> { give back 3 } }\npilot absent: maybe<int> = nobody\ncheck absent { got _ -> { give back 4 } nobody -> { say "absent" } }\ngive back 0'), '0\n-9223372036854775808\n9223372036854775807\nabsent\n'),
        Case('result-empty-unicode-nul', main_source('pilot empty: result<word,word> = ok("")\ncheck result empty { ok(text) -> { say text } err(message) -> { give back 1 } }\npilot unicode: result<word,word> = err("ΟΣ İ 𐐀\\0tail")\ncheck result unicode { ok(text) -> { give back 2 } err(message) -> { say message } }\ngive back 0'), '\nΟΣ İ 𐐀\0tail\n'),
        Case('relay-self-replace', main_source('pilot mut value: result<word,word> = ok("old")\nvalue = relay(value)\nvalue = err("new")\ncheck result value { ok(text) -> { say text } err(message) -> { say message } }\ngive back 0',helpers=relay), 'new\n'),
        Case('discard-and-ignore', main_source('make()\npilot value: result<word,word> = err("ignored")\ncheck result value { ok(_) -> { } err(_) -> { } }\npilot absent: maybe<int> = nobody\ncheck absent { got _ -> { give back 1 } nobody -> { } }\nsay "clean"\ngive back 0',helpers='task make() -> result<word,word> { give back ok("discard") }\n'), 'clean\n'),
        Case('loop-continue-break', main_source('pilot mut count = 0\nrepeat until count >= 3 { pilot value: result<word,word> = ok("loop"); count += 1; check result value { ok(text) -> { say text; if count == 1 { continue } } err(message) -> { say message; break } }; if count == 2 { break } }\ngive back 0'), 'loop\nloop\n'),
        Case('nested-shadow', main_source('pilot text = "outer"\npilot value: result<word,word> = ok("inner")\ncheck result value { ok(text) -> { say text; pilot choice: maybe<int> = some(7); check choice { got text -> { say text } nobody -> { give back 1 } } } err(message) -> { say message } }\nsay text\ngive back 0'), 'inner\n7\nouter\n'),
        Case('take-return-word', main_source('pilot first: result<word,word> = ok("ok")\nsay unwrap(first)\npilot second: result<word,word> = err("err")\nsay unwrap(second)\ngive back 0',helpers='task unwrap(value: result<word,word>) -> word { check result value { ok(text) -> { give back text } err(message) -> { give back message } } }\n'), 'ok\nerr\n'),
        Case('repair-both-branches', main_source('pilot mut value: result<word,word> = ok("original")\nif true { pilot moved = relay(value); value = ok("then") } else { pilot moved = relay(value); value = err("else") }\ncheck result value { ok(text) -> { say text } err(message) -> { say message } }\ngive back 0',helpers=relay), 'then\n'),
        Case('alias-carriers', 'alias Choice = maybe<int>\nalias Outcome = result<word,word>\n'+main_source('pilot choice: Choice = some(9)\ncheck choice { got number -> { say number } nobody -> { give back 1 } }\npilot value: Outcome = ok("alias")\ncheck result value { ok(text) -> { say text } err(message) -> { say message } }\ngive back 0'), '9\nalias\n'),
        Case('inner-payload-aliases', 'alias Number = int\nalias Count = Number\nalias Text = word\nalias Letter = Text\nalias Choice = maybe<Count>\nalias Outcome = result<Letter,Letter>\ntask relay(value: Outcome) -> Outcome { give back value }\n'+main_source('pilot choice: Choice = some(0)\ncheck choice { got number -> { say number } nobody -> { give back 1 } }\npilot absent: maybe<Number> = nobody\ncheck absent { got number -> { give back 2 } nobody -> { say "absent" } }\npilot value: Outcome = ok("alias\\0payload")\npilot output = relay(value)\ncheck result output { ok(text) -> { say text } err(message) -> { give back 3 } }\npilot failed: result<Text,Text> = err("error")\ncheck result failed { ok(text) -> { give back 4 } err(message) -> { say message } }\ngive back 0'), '0\nabsent\nalias\0payload\nerror\n'),
    )



def extract_module(result, *, platform: str = sys.platform) -> str:
    actual = result.stdout.replace('\r\n', '\n') if platform == 'win32' else result.stdout
    begin, end = '@@LLVM-MODULE-BEGIN\n', '@@LLVM-MODULE-END\n'
    if result.returncode != 0 or result.stderr or not actual.startswith(PREFIX+begin) or not actual.endswith(end):
        raise RuntimeError(f'scalar Sum compiler protocol failed: {result.returncode}, {result.stdout!r}, {result.stderr!r}')
    if actual.count(begin) != 1 or actual.count(end) != 1:
        raise RuntimeError('scalar Sum compiler module markers must occur exactly once')
    module = actual[len(PREFIX+begin):-len(end)]
    if not module.strip():
        raise RuntimeError('scalar Sum compiler emitted an empty module')
    return module


def assert_case(result, case: Case, *, platform: str = sys.platform) -> None:
    assert_native_output(result, case.stdout, platform=platform)



def validate_report(report: dict, *, sanitize: bool) -> None:
    expected = {(case.name, opt) for case in cases() for opt in OPTS}
    rows = report.get('programs', [])
    if len(rows) != len(expected) or {(row.get('name'),row.get('optimization')) for row in rows} != expected:
        raise RuntimeError('scalar Sum program/optimization matrix is missing, duplicated or unknown')
    if report.get('sanitizers') is not sanitize:
        raise RuntimeError('scalar Sum report sanitizer mode does not match requested proof')
    table = {case.name:case for case in cases()}
    for row in rows:
        case = table[row['name']]
        if (row.get('status') != 'pass' or row.get('ownership_audits') != ['C','LLVM']
                or row.get('policy') != 'abort' or row.get('exit') != 0
                or row.get('stdout_sha256') != hashlib.sha256(case.stdout.encode()).hexdigest()
                or row.get('stderr_sha256') != hashlib.sha256(b'').hexdigest()):
            raise RuntimeError('scalar Sum report has a failed exact oracle, policy, audit or output fact')
    required = {f'audit-{kind}-O{opt}' for kind in ('C','LLVM') for opt in OPTS}
    if sanitize: required |= {'sanitizer-address','sanitizer-undefined'}
    controls = report.get('controls', [])
    if len(controls) != len(required) or {row.get('name') for row in controls} != required or any(row.get('status')!='pass' for row in controls):
        raise RuntimeError('scalar Sum report lacks actual sanitizer/audit capability controls')


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@contextmanager
def bounded_bootstrap_compile(checks):
    """Bound the repository's original bootstrap compiler invocation only."""
    original = checks.run_with_heartbeat

    def bounded(command, *positional, **options):
        if '-DFREAK_ARRAY_LIVE_LIMIT=1024' not in command or options.get('memory_limit_mb') != 1024:
            raise RuntimeError('unexpected scalar Sum bootstrap compiler resource contract')
        if options.get('timeout_seconds') not in (None, 120):
            raise RuntimeError('unexpected scalar Sum bootstrap compiler timeout')
        return original(command, *positional, **{**options, 'timeout_seconds':120})

    checks.run_with_heartbeat = bounded
    try:
        yield
    finally:
        checks.run_with_heartbeat = original


def llvm_literal_target_flags(target: str) -> list[str]:
    # Apple Clang expands the driver triple to an SDK-versioned macOS triple.
    # Give its IR frontend the exact TargetSpec triple already in the module.
    return ['-Xclang', '-triple', '-Xclang', target] if target == 'aarch64-apple-darwin' else []


def run_gate(args, report: dict) -> None:
    import build_v4 as build
    from freakc.v4_native_runtime import HEADER_NAMES
    checks = build.checks
    work = args.work.resolve(); work.mkdir(parents=True,exist_ok=True)
    runner = Runner(checks,work)
    fixture = checks.V4_ROOT/'tests/scalar_sum_execute_smoke.fk'
    if not fixture.is_file(): raise RuntimeError('required scalar Sum compiler fixture is unavailable')
    checks.check_individual_parse([fixture])
    flat = checks.check_flattened_crates()
    source,ui = checks.transpile_fixture(flat,fixture)
    if ui: raise RuntimeError('scalar Sum compiler fixture unexpectedly requires UI')
    old_root = checks.RUNTIME_BUILD_ROOT
    checks.RUNTIME_BUILD_ROOT = work/'compiler'; checks.RUNTIME_BUILD_ROOT.mkdir(parents=True,exist_ok=True)
    try:
        runtime=checks.RUNTIME_ROOT/'freak_runtime.c'
        with bounded_bootstrap_compile(checks):
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
            flags=['--target='+target,'-w',f'-O{opt}',f'-I{checks.RUNTIME_ROOT}',*AUDIT_FLAGS]
            if not args.plain: flags+=list(SANITIZER_FLAGS)
            validate_build_flags(flags,not args.plain);objects[opt]=[]
            for name in build.SOURCE_NAMES:
                path=checks.RUNTIME_ROOT/name;output=work/f'{path.stem}.O{opt}{".obj" if sys.platform=="win32" else ".o"}'
                result=runner.run([args.clang,*flags,'-c',str(path),'-o',str(output)],f'scalar Sum runtime {path.stem} O{opt}',timeout=120,memory=512)
                if result.returncode!=0:raise RuntimeError(f'scalar Sum runtime compile failed: {result.stderr}')
                objects[opt].append(str(output))
            binary=work/f'audit-O{opt}{suffix}'
            result=runner.run([args.clang,*flags,str(audit),*objects[opt],'-o',str(binary),*checks.runtime_platform_final_link_args()],f'scalar Sum audit link O{opt}',timeout=120,memory=512)
            if result.returncode!=0:raise RuntimeError(f'scalar Sum audit compile failed: {result.stderr}')
            for kind,status in (('C',87),('LLVM',86)):
                actual=runner.run([str(binary),kind],f'scalar Sum audit {kind} O{opt}',timeout=30,memory=128)
                exact_result(actual,status,'',f'FREAK: {kind} ownership audit found 1 unreleased word allocation(s)\n',kind)
                report['controls'].append({'name':f'audit-{kind}-O{opt}','status':'pass'})
        if not args.plain:
            probe=work/'sanitizer_probe.c';probe.write_text('''#include <stdlib.h>
#include <limits.h>
int main(int argc,char **argv){if(argc!=2)return 9;if(argv[1][0]=='a'){volatile char *p=malloc(1);free((void*)p);return p[0];}volatile int x=INT_MAX;volatile int one=1;return x+one;}
''')
            binary=work/f'sanitizer-probe{suffix}'
            result=runner.run([args.clang,'--target='+target,'-O0',*SANITIZER_FLAGS,str(probe),'-o',str(binary)],'scalar Sum sanitizer link',timeout=120,memory=512)
            if result.returncode!=0:raise RuntimeError('sanitizer capability compile failed')
            for kind in ('address','undefined'):
                validate_sanitizer_probe(runner.run([str(binary),kind],f'scalar Sum sanitizer {kind}',timeout=30,memory=128),kind)
                report['controls'].append({'name':'sanitizer-'+kind,'status':'pass'})
        for case in cases():
            source_path=work/f'{case.name}.fk';source_path.write_text(case.source,encoding='utf-8')
            emitted=runner.run([str(compiler),str(source_path),target],'scalar Sum emit '+case.name,timeout=60,memory=64)
            module=extract_module(emitted);llvm=work/f'{case.name}.ll';llvm.write_bytes(module.encode())
            if '@freak_v4_process_' in module or '@freak_v4_fs_' in module or '@freak_v4_word_parse_int_checked' in module:
                raise RuntimeError('constructed carrier gate unexpectedly uses an OS/parser bridge')
            for opt in OPTS:
                binary=work/f'{case.name}-O{opt}{suffix}'
                flags=[f'-O{opt}',*AUDIT_FLAGS]
                if not args.plain:flags+=list(SANITIZER_FLAGS)
                result=runner.run([args.clang,'--target='+target,*llvm_literal_target_flags(target),*flags,str(llvm),*objects[opt],'-o',str(binary),*checks.runtime_platform_final_link_args()],f'scalar Sum link {case.name} O{opt}',timeout=120,memory=512)
                if result.returncode!=0 or result.stdout or result.stderr:raise RuntimeError(f'scalar Sum native link failed: {result.stderr}')
                result=runner.run([str(binary)],f'scalar Sum execute {case.name} O{opt}',timeout=30,memory=128)
                assert_case(result,case)
                actual=result.stdout.replace('\r\n','\n') if sys.platform=='win32' else result.stdout
                report['programs'].append({'name':case.name,'optimization':opt,'status':'pass','ownership_audits':['C','LLVM'],'policy':'abort','exit':result.returncode,'source_sha256':sha(source_path),'module_sha256':sha(llvm),'binary_sha256':sha(binary),'stdout_sha256':hashlib.sha256(actual.encode()).hexdigest(),'stderr_sha256':hashlib.sha256(result.stderr.encode()).hexdigest()})
                print(f'scalar Sum {case.name} O{opt}: exact exit/output PASS',flush=True)
    validate_report(report,sanitize=not args.plain)


def main(argv: list[str]|None=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clang',default=os.environ.get('FREAK_CLANG') or shutil.which('clang'))
    parser.add_argument('--plain',action='store_true')
    parser.add_argument('--work',type=Path,default=ROOT/'build/v4_smoke/scalar_sum_native')
    parser.add_argument('--report',type=Path)
    args=parser.parse_args(argv)
    if not args.clang:parser.error('clang is required; scalar Sum execution cannot be skipped')
    report={'platform':sys.platform,'sanitizers':not args.plain,'programs':[],'controls':[]}
    primary = None
    try:
        run_gate(args,report)
    except BaseException as error:
        primary = error
    try:
        path=args.report or args.work/'report.json'
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(report,indent=2)+'\n')
    except BaseException as publication_error:
        if primary is None:
            raise
        try:
            primary.add_note('report publication also failed: '+type(publication_error).__name__)
        except BaseException:
            pass
    if primary is not None:
        raise primary.with_traceback(primary.__traceback__)
    return 0

if __name__=='__main__':raise SystemExit(main())
