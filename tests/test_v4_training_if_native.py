"""Reject unbound runtime identities before native training/conditional jobs."""
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('training_if_native_inventory', ROOT / 'tests/v4_training_if_native.py')
gate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gate
SPEC.loader.exec_module(gate)


def frozen_report(sanitize=False):
    paths = gate.runtime_inventory_paths(ROOT / 'freakc/runtime')
    report = {'inputs_before': {'src/compiler/v4/native-runtime.manifest': gate.sha(ROOT / 'src/compiler/v4/native-runtime.manifest')},
              'compiler_process_contract': {'memory_limit_mib':64, 'live_handle_limit':1024, 'timeout_seconds':60},
              'bootstrap_process_contract': {'memory_limit_mib':1024, 'live_handle_limit':1024, 'timeout_seconds':120},
              'programs': [], 'controls': [], 'compiler_contracts': [], 'sanitizers': sanitize,
              'target':'x86_64-unknown-linux-gnu', 'jobs':247 + (3 if sanitize else 0)}
    for key, group in paths.items():
        report[key] = {name: gate.sha(path) for name, path in group.items()}
        report['inputs_before'].update({path.relative_to(ROOT).as_posix(): gate.sha(path) for path in group.values()})
    report['inputs_after'] = dict(report['inputs_before'])
    for family, case, status, stdout in gate.CASES:
        for opt in gate.OPTS:
            report['programs'].append({'family': family, 'case':case, 'optimization':opt,
                'status':'pass', 'exit':status, 'stdout_sha256':hashlib.sha256(stdout.encode()).hexdigest(),
                'stderr_sha256':hashlib.sha256(b'').hexdigest(), 'ownership_audits':['C', 'LLVM']})
    names = [f'audit-{kind}-O{opt}' for kind in ('C','LLVM') for opt in gate.OPTS]
    if sanitize:
        names += ['sanitizer-address','sanitizer-undefined']
    report['controls'] = [{'name':name,'status':'pass'} for name in names]
    report['compiler_contracts'] = [{'case':case,'status':'pass'} for case in gate.ADVERSE_CASES]
    return report


class TrainingRuntimeInventory(unittest.TestCase):
    def test_exact_declared_groups_match_physical_frozen_inputs(self):
        report = frozen_report()
        self.assertEqual({key:len(names) for key,names in gate.runtime_inventory_names().items()},
                         {'runtime_sources':7, 'runtime_headers':11, 'runtime_vendor_headers':6})
        gate.validate_runtime_inventory(report)
        self.assertTrue(all('\\' not in key for key in report['inputs_before']))

    def test_every_entry_requires_exact_name_and_frozen_physical_hash(self):
        clean = frozen_report()
        for key, group in gate.runtime_inventory_paths(ROOT / 'freakc/runtime').items():
            for name, path in group.items():
                frozen_key = path.relative_to(ROOT).as_posix()
                variants = []
                missing = deepcopy(clean); del missing[key][name]; variants.append(missing)
                extra = deepcopy(clean); extra[key]['extra.h'] = 'a'*64; variants.append(extra)
                renamed = deepcopy(clean); renamed[key]['replacement.h'] = renamed[key].pop(name); variants.append(renamed)
                forged = deepcopy(clean); forged[key][name] = 'a'*64; variants.append(forged)
                unbound = deepcopy(clean); unbound['inputs_before'][frozen_key] = 'a'*64; variants.append(unbound)
                both = deepcopy(unbound); both[key][name] = 'a'*64; variants.append(both)
                missing_pin = deepcopy(clean); del missing_pin['inputs_before'][frozen_key]; variants.append(missing_pin)
                for index, report in enumerate(variants):
                    with self.subTest(key=key, name=name, mutation=index), self.assertRaises(RuntimeError):
                        gate.validate_runtime_inventory(report)

    def test_manifest_and_declared_array_substitutions_reject(self):
        clean = frozen_report()
        for value in (None, 'a'*64):
            changed = deepcopy(clean)
            if value is None:
                del changed['inputs_before']['src/compiler/v4/native-runtime.manifest']
            else:
                changed['inputs_before']['src/compiler/v4/native-runtime.manifest'] = value
            with self.assertRaisesRegex(RuntimeError, 'inventory differs'):
                gate.validate_runtime_inventory(changed)
        import build_v4 as build
        substitute = tuple(build.SOURCE_NAMES[:-1]) + ('same-count-replacement.c',)
        with tempfile.TemporaryDirectory() as work, patch.object(build, 'SOURCE_NAMES', substitute), \
                patch.object(build.checks, 'check_flattened_crates', side_effect=AssertionError('must reject before flattening')):
            with self.assertRaisesRegex(RuntimeError, 'central runtime/handle inventory changed'):
                gate.run_gate(SimpleNamespace(work=Path(work), clang='never-run', plain=True), {})

    def test_changed_physical_bytes_cannot_match_a_frozen_report(self):
        clean = frozen_report(); real_sha = gate.sha
        with tempfile.TemporaryDirectory() as work:
            replacement = Path(work) / 'changed-input'
            for key, group in gate.runtime_inventory_paths(ROOT / 'freakc/runtime').items():
                for name, path in group.items():
                    replacement.write_bytes(path.read_bytes() + b'\nchanged after freezing\n')
                    with self.subTest(key=key, name=name), patch.object(gate, 'sha', side_effect=lambda observed:
                            real_sha(replacement) if observed == path else real_sha(observed)):
                        with self.assertRaisesRegex(RuntimeError, 'runtime identity differs'):
                            gate.validate_runtime_inventory(clean)

    def test_inventory_is_checked_before_the_actual_first_bootstrap_job(self):
        import build_v4 as build
        checks = build.checks; real_sha = gate.sha
        paths = gate.runtime_inventory_paths(checks.RUNTIME_ROOT)
        clean_vendor = frozen_report()['runtime_vendor_headers']
        # Only transpilation is stubbed. The real run_gate bootstrap wrapper
        # must reject changed inputs before Runner can launch any native job.
        for key, group in paths.items():
            for name, path in group.items():
                with self.subTest(key=key, name=name), tempfile.TemporaryDirectory() as work:
                    replacement = Path(work) / 'changed-input'; replacement.write_bytes(path.read_bytes()+b'\nchanged before bootstrap\n')
                    state = {'changed':False}
                    def changed_sha(observed):
                        return real_sha(replacement) if state['changed'] and observed == path else real_sha(observed)
                    def attempt_bootstrap(*args, **kwargs):
                        state['changed'] = True
                        checks.run_with_heartbeat(['never-run', '-DFREAK_ARRAY_LIVE_LIMIT=1024'],
                                                  label='first bootstrap', memory_limit_mb=1024)
                        self.fail('a changed runtime input reached native compilation')
                    with patch.object(gate, 'sha', side_effect=changed_sha), \
                            patch.object(checks, 'check_flattened_crates', return_value=''), \
                            patch.object(checks, 'transpile_fixture', return_value=('not compiled', False)), \
                            patch.object(checks, 'compile_runtime_smoke', side_effect=attempt_bootstrap), \
                            patch.object(gate.Runner, 'run', side_effect=AssertionError('native command reached')):
                        report = {}
                        with self.assertRaisesRegex(RuntimeError, 'input identity changed during proof'):
                            gate.run_gate(SimpleNamespace(work=Path(work), clang='never-run', plain=True), report)
                        self.assertEqual(report['runtime_vendor_headers'], clean_vendor)

    def test_clean_first_bootstrap_reaches_original_runner_guard(self):
        import build_v4 as build
        checks = build.checks
        def attempt_bootstrap(*args, **kwargs):
            checks.run_with_heartbeat(['never-run', '-DFREAK_ARRAY_LIVE_LIMIT=1024'],
                                      label='first bootstrap', memory_limit_mb=1024)
        with tempfile.TemporaryDirectory() as work, \
                patch.object(checks, 'check_flattened_crates', return_value=''), \
                patch.object(checks, 'transpile_fixture', return_value=('not compiled', False)), \
                patch.object(checks, 'compile_runtime_smoke', side_effect=attempt_bootstrap), \
                patch.object(gate.Runner, 'run', side_effect=AssertionError('original Runner reached')):
            with self.assertRaisesRegex(AssertionError, 'original Runner reached'):
                gate.run_gate(SimpleNamespace(work=Path(work), clang='never-run', plain=True), {})

    def test_native_oracles_audits_and_process_caps_still_reject_forgery(self):
        for sanitize in (False, True):
            clean = frozen_report(sanitize); gate.validate_report(clean, sanitize)
            variants = []
            wrong_exit = deepcopy(clean); wrong_exit['programs'][0]['exit'] = 99; variants.append(wrong_exit)
            wrong_stdout = deepcopy(clean); wrong_stdout['programs'][0]['stdout_sha256'] = 'a'*64; variants.append(wrong_stdout)
            missing_audit = deepcopy(clean); missing_audit['controls'].pop(); variants.append(missing_audit)
            missing_adverse = deepcopy(clean); missing_adverse['compiler_contracts'].pop(); variants.append(missing_adverse)
            wrong_jobs = deepcopy(clean); wrong_jobs['jobs'] += 1; variants.append(wrong_jobs)
            for field in ('compiler_process_contract','bootstrap_process_contract'):
                for cap in ('memory_limit_mib','live_handle_limit','timeout_seconds'):
                    changed = deepcopy(clean); changed[field][cap] += 1; variants.append(changed)
            for index, report in enumerate(variants):
                with self.subTest(sanitized=sanitize, mutation=index), self.assertRaises(RuntimeError):
                    gate.validate_report(report, sanitize)


if __name__ == '__main__':
    unittest.main()
