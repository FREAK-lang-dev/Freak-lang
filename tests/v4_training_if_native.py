#!/usr/bin/env python3
"""Run bounded training/conditional programs at O0/O2/O3 with exact oracles.

Compiler fixtures supply both the persisted source and the sealed LLVM module.
Default requires ASan/UBSan and both ownership audits; --plain adds portability.
Original Runner caps/logs, runtime inventory and Darwin deployment helpers are
shared with the numerical/scalar-Sum gates. Every run needs a fresh --work.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests'), str(ROOT / 'src/compiler/v4')]
from v4_checked_numeric_codegen import (AUDIT_FLAGS, OPTS, SANITIZER_FLAGS, Runner,
    exact_result, normalized, sanitizer_environment, sha, validate_build_flags,
    validate_sanitizer_probe)
from v4_scalar_sum_codegen import native_link_module, native_link_target

# Closed (family, case, exit, stdout) matrix; stderr is always exactly empty.
CASES = (
    ('training', 0, 3, ''), ('training', 1, 4, ''),
    ('training', 2, 0, ''), ('training', 3, 0, ''),
    ('training', 4, 2, ''), ('training', 5, 3, ''),
    ('training', 6, 1, ''), ('training', 7, 9, ''),
    ('training', 8, 9, ''), ('training', 9, 3, ''),
    ('training', 10, 2, ''), ('training', 11, 2, '0\ncap\n1\ncap\n2\ncap\n'),
    ('training', 12, 0, 'condition\n'), ('training', 13, 1, '0\ncap\n1\n'),
    ('training', 14, 3, ''), ('training', 15, 1, ''),
    ('training', 16, 0, ''), ('training', 17, 3, 'loop\nloop\nloop\n'),
    ('if', 0, 0, '1\n2\n3\n'), ('if', 1, 0, '1\n2\n3\n4\n5\n'),
    ('if', 2, 0, 'live\n4\n'), ('if', 3, 0, '1\n2\n3\n'),
    ('if', 4, 2, ''), ('if', 5, 0, 'minus\nzero!\nfresh\n'),
    ('if', 6, 0, '3\n'), ('if', 7, 0, '}\n1\n3\ntail\n4\n'),
)
FIXTURES = {'training': 'mir_training_cap_contract_smoke.fk',
            'if': 'mir_if_terminal_contract_smoke.fk'}
ADVERSE_CASES = (20, 21, 22, 23, 24, 25, 30)


def prefix(family: str, case: int) -> str:
    if family == 'training':
        return f'training-cap case={case} identity=true Meiya=true restore=true old-seal=true fresh-module=true\n'
    return f'if-terminal case={case} edges=true Meiya=true restore=true old-seal=true fresh-module=true\n'


def extract_module(result, family: str, case: int) -> str:
    actual = normalized(result.stdout, sys.platform)
    opening = prefix(family, case) + '@@LLVM-MODULE-BEGIN\n'
    closing = '@@LLVM-MODULE-END\n'
    if (result.returncode != 0 or result.stderr or not actual.startswith(opening)
            or not actual.endswith(closing) or actual.count('@@LLVM-MODULE-BEGIN\n') != 1
            or actual.count(closing) != 1):
        raise RuntimeError('training/conditional compiler protocol failed')
    module = actual[len(opening):-len(closing)]
    if not module.strip():
        raise RuntimeError('training/conditional compiler emitted an empty module')
    return module


def runtime_inventory_names() -> dict[str, tuple[str, ...]]:
    from freakc import v4_native_runtime as inventory
    if Path(inventory.__file__).resolve() != (ROOT / 'freakc/v4_native_runtime.py').resolve():
        raise RuntimeError('runtime inventory imported from a different checkout')
    rows = inventory.read_inventory(ROOT / 'src/compiler/v4/native-runtime.manifest')
    names = {
        'runtime_sources': tuple(name for role, name in rows if role == 'source'),
        'runtime_headers': tuple(name for role, name in rows
                                 if role == 'header' and not name.startswith('third_party/')),
        'runtime_vendor_headers': tuple(name for role, name in rows
                                        if role == 'header' and name.startswith('third_party/')),
    }
    if tuple(len(group) for group in names.values()) != (7, 11, 6):
        raise RuntimeError('central runtime inventory changed; review the closed plan')
    return names


def runtime_inventory_paths(runtime_root: Path) -> dict[str, dict[str, Path]]:
    from freakc import v4_native_runtime as inventory
    return {key: {name: inventory.runtime_file(runtime_root, name) for name in names}
            for key, names in runtime_inventory_names().items()}


def validate_runtime_inventory(report: dict) -> None:
    inputs = report.get('inputs_before', {})
    manifest_key = 'src/compiler/v4/native-runtime.manifest'
    if inputs.get(manifest_key) != sha(ROOT / manifest_key):
        raise RuntimeError('native runtime inventory differs from its frozen compiler input')
    for key, paths in runtime_inventory_paths(ROOT / 'freakc/runtime').items():
        observed = report.get(key, {})
        if not isinstance(observed, dict) or set(observed) != set(paths):
            raise RuntimeError('incomplete or unexpected frozen ' + key + ' identity')
        for name, path in paths.items():
            pinned = inputs.get(path.relative_to(ROOT).as_posix())
            if observed[name] != pinned or pinned != sha(path):
                raise RuntimeError('runtime identity differs from its frozen compiler input: ' + name)


def validate_report(report: dict, sanitize: bool) -> None:
    validate_runtime_inventory(report)
    if (report.get('compiler_process_contract') !=
            {'memory_limit_mib':64, 'live_handle_limit':1024, 'timeout_seconds':60}
            or report.get('bootstrap_process_contract') !=
            {'memory_limit_mib':1024, 'live_handle_limit':1024, 'timeout_seconds':120}):
        raise RuntimeError('compiler/bootstrap resource contract changed')
    wanted = {(family, case, opt) for family, case, _, _ in CASES for opt in OPTS}
    rows = report['programs']
    if len(rows) != len(wanted) or {(r['family'], r['case'], r['optimization']) for r in rows} != wanted:
        raise RuntimeError('native case matrix is missing, duplicate or unknown')
    oracles = {(family, case): (status, stdout) for family, case, status, stdout in CASES}
    for row in rows:
        status, stdout = oracles[row['family'], row['case']]
        if (row['status'] != 'pass' or row['exit'] != status
                or row['stdout_sha256'] != hashlib.sha256(stdout.encode()).hexdigest()
                or row['stderr_sha256'] != hashlib.sha256(b'').hexdigest()
                or row['ownership_audits'] != ['C', 'LLVM']):
            raise RuntimeError('native report contradicts its exact closed oracle')
    required = {f'audit-{kind}-O{opt}' for kind in ('C', 'LLVM') for opt in OPTS}
    if sanitize:
        required |= {'sanitizer-address', 'sanitizer-undefined'}
    controls = report['controls']
    if (report['sanitizers'] is not sanitize or len(controls) != len(required)
            or {r['name'] for r in controls} != required
            or any(r['status'] != 'pass' for r in controls)):
        raise RuntimeError('native report lacks actual audit/sanitizer controls')
    if (len(report['compiler_contracts']) != len(ADVERSE_CASES)
            or {r['case'] for r in report['compiler_contracts']} != set(ADVERSE_CASES)
            or any(r['status'] != 'pass' for r in report['compiler_contracts'])):
        raise RuntimeError('native report lacks preserved diagnostic/hostile-join contracts')
    # 2 bootstrap + 21 runtime objects + 9 audit jobs + 7 adverse contracts +
    # 26 source reads + 26 emits + 78 links + 78 executions. SAN adds 3 jobs.
    expected_jobs = 247 + (3 if sanitize else 0) + (1 if report['target'] == 'aarch64-apple-darwin' else 0)
    if report['jobs'] != expected_jobs or report['inputs_before'] != report['inputs_after']:
        raise RuntimeError('native job count or input conservation differs from the closed plan')


@contextmanager
def recorded_bootstrap(checks, runner):
    original = checks.run_with_heartbeat
    def execute(command, *, label, memory_limit_mb):
        if memory_limit_mb != 1024 or '-DFREAK_ARRAY_LIVE_LIMIT=1024' not in command:
            raise RuntimeError('bootstrap resource/handle contract changed')
        # MSVC LINK prints import-library notices for this runtime's exports.
        # Select the quiet LLD linker while keeping the exact stream guard.
        argv = [*command, '-fuse-ld=lld'] if sys.platform == 'win32' else command
        result = runner.run(argv, label, timeout=120, memory=1024)
        if result.returncode != 0 or result.stdout or result.stderr:
            raise RuntimeError('bounded bootstrap compile failed')
        return result
    checks.run_with_heartbeat = execute
    try:
        yield
    finally:
        checks.run_with_heartbeat = original


def run_gate(args, report: dict) -> None:
    import build_v4 as build
    from freakc.v4_native_runtime import HEADER_NAMES
    checks = build.checks
    work = args.work.resolve()
    names = runtime_inventory_names()
    if (tuple(build.SOURCE_NAMES) != names['runtime_sources']
            or tuple(HEADER_NAMES) != names['runtime_headers']
            or checks.C_ARRAY_HANDLE_RESOURCE_LIMIT != 1024):
        raise RuntimeError('central runtime/handle inventory changed; review the closed plan')
    runtime_paths = runtime_inventory_paths(checks.RUNTIME_ROOT)
    paths = [checks.crate_path(name) for name in checks.CRATE_ORDER]
    paths += [checks.TESTS_ROOT / name for name in FIXTURES.values()]
    paths += [path for group in runtime_paths.values() for path in group.values()]
    paths += [Path(__file__), Path(checks.__file__), ROOT / 'src/compiler/v4/build_v4.py',
              ROOT / 'src/compiler/v4/native-runtime.manifest',
              ROOT / 'freakc/v4_native_runtime.py', ROOT / 'tests/v4_checked_numeric_codegen.py',
              ROOT / 'tests/v4_scalar_sum_codegen.py', ROOT / 'tests/test_v4_training_if_native.py']
    def pins():
        return {path.relative_to(ROOT).as_posix(): sha(path) for path in paths}
    report['inputs_before'] = pins()
    report['compiler_process_contract'] = {'memory_limit_mib':64, 'live_handle_limit':1024, 'timeout_seconds':60}
    report['bootstrap_process_contract'] = {'memory_limit_mib':1024, 'live_handle_limit':1024, 'timeout_seconds':120}
    report.update({key: {name: sha(path) for name, path in group.items()}
                   for key, group in runtime_paths.items()})
    validate_runtime_inventory(report)

    class PinnedRunner(Runner):
        def run(self, *args, **kwargs):
            if pins() != report['inputs_before']:
                raise RuntimeError('training input identity changed during proof')
            validate_runtime_inventory(report)
            result = super().run(*args, **kwargs)
            if pins() != report['inputs_before']:
                raise RuntimeError('training input identity changed during proof')
            validate_runtime_inventory(report)
            return result

    # Retain the original subprocess guard and verify inputs around every job.
    runner = PinnedRunner(SimpleNamespace(run_with_heartbeat=checks.run_with_heartbeat), work)
    flat = checks.check_flattened_crates()
    compilers = {}
    for family, name in FIXTURES.items():
        fixture = checks.TESTS_ROOT / name
        source, ui = checks.transpile_fixture(flat, fixture)
        if ui:
            raise RuntimeError('compiler fixture unexpectedly requires UI')
        old_root = checks.RUNTIME_BUILD_ROOT
        directory = work / ('compiler-' + family)
        directory.mkdir()
        checks.RUNTIME_BUILD_ROOT = directory
        try:
            runtime = checks.RUNTIME_ROOT / 'freak_runtime.c'
            with recorded_bootstrap(checks, runner):
                compiler, compiled_now = checks.compile_runtime_smoke(
                    args.clang, f'-I{checks.RUNTIME_ROOT}', runtime, checks.read_text(runtime),
                    fixture, source, ('-DFREAK_ARRAY_LIVE_LIMIT=1024',))
            if not compiled_now:
                raise RuntimeError('fresh compiler unexpectedly reused a cached binary')
        finally:
            checks.RUNTIME_BUILD_ROOT = old_root
        compilers[family] = compiler
        report['compilers'][family] = {'binary_sha256':sha(compiler),
            'generated_c_sha256':sha(directory / (fixture.name + '.c'))}
    target = build.host_target()
    report['target'] = target
    selected = native_link_target(args.clang, runner, work, target, report)
    report['native_target'] = selected
    suffix = '.exe' if sys.platform == 'win32' else '.native'
    audit = work / 'audit.c'
    audit.write_bytes(b'#include "freak_runtime.h"\n#include "freak_v4_word_runtime.h"\n'
        b'int main(int argc,char **argv){if(argc!=2)return 9;'
        b'if(argv[1][0]==\'C\'){volatile freak_word x=freak_word_from_int(7);(void)x;}'
        b'else{volatile int64_t x=freak_v4_word_from_int(7);(void)x;}return 0;}\n')
    objects = {}
    with sanitizer_environment(not args.plain):
        for opt in OPTS:
            flags = ['--target='+selected, '-w', f'-O{opt}', f'-I{checks.RUNTIME_ROOT}', *AUDIT_FLAGS]
            if not args.plain:
                flags += list(SANITIZER_FLAGS)
            validate_build_flags(flags, not args.plain)
            objects[opt] = []
            report['build_flags'][str(opt)] = flags
            for name in build.SOURCE_NAMES:
                path = checks.RUNTIME_ROOT / name
                output = work / f'{path.stem}.O{opt}{".obj" if sys.platform=="win32" else ".o"}'
                result = runner.run([args.clang, *flags, '-c', str(path), '-o', str(output)],
                                    f'runtime {path.stem} O{opt}', timeout=120, memory=512)
                exact_result(result, 0, '', '', name)
                objects[opt].append(str(output))
            binary = work / (f'audit-O{opt}' + suffix)
            result = runner.run([args.clang, *flags, str(audit), *objects[opt], '-o', str(binary),
                                *checks.runtime_platform_final_link_args()], f'audit link O{opt}', timeout=120, memory=512)
            exact_result(result, 0, '', '', 'audit link')
            for kind, status in (('C',87), ('LLVM',86)):
                result = runner.run([str(binary), kind], f'audit {kind} O{opt}', timeout=30, memory=128)
                exact_result(result, status, '', f'FREAK: {kind} ownership audit found 1 unreleased word allocation(s)\n', kind)
                report['controls'].append({'name':f'audit-{kind}-O{opt}', 'status':'pass'})
        if not args.plain:
            probe = work / 'sanitizer.c'
            probe.write_bytes(b'#include <stdlib.h>\n#include <limits.h>\nint main(int argc,char **argv){'
                b'if(argc!=2)return 9;if(argv[1][0]==\'a\'){volatile char *p=malloc(1);free((void*)p);return p[0];}'
                b'volatile int x=INT_MAX;volatile int one=1;return x+one;}\n')
            binary = work / ('sanitizer' + suffix)
            result = runner.run([args.clang, '--target='+selected, '-O0', *SANITIZER_FLAGS, str(probe), '-o', str(binary)],
                                'sanitizer link', timeout=120, memory=512)
            exact_result(result, 0, '', '', 'sanitizer link')
            for kind in ('address', 'undefined'):
                validate_sanitizer_probe(runner.run([str(binary), kind], 'sanitizer '+kind, timeout=30, memory=128), kind)
                report['controls'].append({'name':'sanitizer-'+kind, 'status':'pass'})
        for case in ADVERSE_CASES:
            expected = (f'if-terminal case={case} named=true no-module=true\n' if case != 30 else
                'if-terminal case=30 canonical=true hostile-live=true hostile-detached=true recovered=true old-seal=true\n')
            result = runner.run([str(compilers['if']), str(case), target], f'if contract {case}')
            exact_result(result, 0, expected, '', 'if contract')
            report['compiler_contracts'].append({'case':case, 'status':'pass'})
        for family, case, status, stdout in CASES:
            stem = f'{family}-{case}'
            source_result = runner.run([str(compilers[family]), str(case), target, '--source'], stem+' source')
            text = normalized(source_result.stdout, sys.platform)
            if source_result.returncode != 0 or source_result.stderr or not text.startswith('task ') or not text.endswith('\n\n'):
                raise RuntimeError('compiler fixture source protocol failed')
            source_path = work / (stem + '.fk')
            source_path.write_bytes(text[:-1].encode('utf-8'))
            emitted = runner.run([str(compilers[family]), str(case), target, '--emit'], stem+' emit')
            module = extract_module(emitted, family, case)
            llvm = work / (stem + '.ll')
            llvm.write_bytes(module.encode('utf-8'))
            link_llvm = llvm
            if selected != target:
                link_llvm = work / (stem + '.link.ll')
                link_llvm.write_bytes(native_link_module(module, target, selected).encode('utf-8'))
            for opt in OPTS:
                binary = work / (f'{stem}-O{opt}' + suffix)
                flags = [f'-O{opt}', *AUDIT_FLAGS]
                if not args.plain:
                    flags += list(SANITIZER_FLAGS)
                validate_build_flags(flags, not args.plain)
                result = runner.run([args.clang, '--target='+selected, *flags, str(link_llvm), *objects[opt],
                    '-o', str(binary), *checks.runtime_platform_final_link_args()], f'{stem} link O{opt}', timeout=120, memory=512)
                exact_result(result, 0, '', '', 'native link')
                result = runner.run([str(binary)], f'{stem} execute O{opt}', timeout=30, memory=128)
                exact_result(result, status, stdout, '', 'native execute')
                report['programs'].append({'family':family, 'case':case, 'optimization':opt,
                    'status':'pass', 'exit':result.returncode, 'ownership_audits':['C','LLVM'],
                    'source_sha256':sha(source_path), 'module_sha256':sha(llvm),
                    'link_module_sha256':sha(link_llvm), 'binary_sha256':sha(binary),
                    'stdout_sha256':hashlib.sha256(normalized(result.stdout, sys.platform).encode()).hexdigest(),
                    'stderr_sha256':hashlib.sha256(normalized(result.stderr, sys.platform).encode()).hexdigest()})
                print(f'{stem} O{opt}: exact exit/output PASS', flush=True)
    report['jobs'] = runner.serial
    report['inputs_after'] = pins()
    validate_report(report, not args.plain)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clang', default=os.environ.get('FREAK_CLANG') or shutil.which('clang'))
    parser.add_argument('--plain', action='store_true')
    parser.add_argument('--work', type=Path, required=True)
    args = parser.parse_args(argv)
    if not args.clang:
        parser.error('clang is required; native checks cannot be skipped')
    args.work = args.work.resolve()
    if args.work.exists():
        parser.error('--work must be fresh; retained evidence is never overwritten')
    args.work.mkdir(parents=True)
    report = {'schema':'v4-training-if-native-v1', 'passed':False, 'platform':sys.platform,
              'sanitizers':not args.plain, 'compilers':{}, 'controls':[], 'compiler_contracts':[],
              'programs':[], 'build_flags':{}}
    primary = None
    try:
        run_gate(args, report)
        report['passed'] = True
    except BaseException as error:
        primary = error
        report['failure_type'] = type(error).__name__
    try:
        (args.work / 'report.json').write_bytes((json.dumps(report, indent=2)+'\n').encode('utf-8'))
    except BaseException as publication_error:
        if primary is None:
            raise
        try:
            primary.add_note('report publication also failed: '+type(publication_error).__name__)
        except BaseException:
            pass
    if primary is not None:
        raise primary.with_traceback(primary.__traceback__)
    print('training/conditional native gate PASS', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
