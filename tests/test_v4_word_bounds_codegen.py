"""Process-free adversarial controls for generated word bounds evidence."""
from __future__ import annotations

from contextlib import ExitStack, redirect_stderr, redirect_stdout
from copy import deepcopy
import ast
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("word_bounds_gate", ROOT / "tests/v4_word_bounds_codegen.py")
gate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gate
SPEC.loader.exec_module(gate)
FIXTURE = ROOT / "src/compiler/v4/tests/word_bounds_execute_smoke.fk"


def result(stdout="", stderr="", status=0):
    return subprocess.CompletedProcess(["mock"], status, stdout, stderr)


class Hostile(RuntimeError):
    def __str__(self):
        raise AssertionError("exception payload must not be formatted")


def module(case):
    instructions = ""
    for kind, count in zip(("char_at", "slice", "substring"), gate.call_counts(case)):
        for index in range(count):
            instructions += f"  %r.{kind}.{index} = call i64 @freak_v4_word_{kind}(i64 %w, i64 0)\n"
    return "define i32 @main(i32 %argc, ptr %argv) {\n" + instructions + "  ret i32 0\n}\n"


def compiler(case, body=None):
    return result(gate.prefix(case) + gate.BEGIN + (module(case) if body is None else body) + gate.END)


def complete_report(sanitize=True, platform="linux"):
    digest = "a" * 64
    suffix = ".exe" if platform == "win32" else ".native"
    rows = []
    for case, (stdout, stderr) in enumerate(gate.OUTPUTS):
        for opt in gate.OPTS:
            for variant in gate.VARIANTS:
                rows.append({"case": case, "optimization": opt, "variant": variant, "status": "pass",
                             "exit": gate.exit_code(case, platform), "binary_path": f"case-{case}.{variant}.O{opt}{suffix}", "binary_sha256": digest,
                             "stdout_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
                             "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest()})
    controls = [{"name": f"audit-{kind}-O{opt}", "status": "pass"}
                for kind in ("C", "LLVM") for opt in gate.OPTS]
    controls += [{"name": f"guard-live-O{opt}", "status": "pass"} for opt in gate.OPTS]
    if sanitize:
        controls += [{"name": "sanitizer-" + kind, "status": "pass"} for kind in ("address", "undefined")]
    images = {row["binary_path"]: digest for row in rows}
    probe = "compiler/word_bounds_execute_smoke" + (".exe" if platform == "win32" else "")
    images[probe] = digest
    object_suffix = ".obj" if platform == "win32" else ".o"
    runtime = gate.literal_assignment(ROOT / "freakc/v4_native_runtime.py", "SOURCE_NAMES")
    images.update({f"{Path(name).stem}.O{opt}{object_suffix}": digest
                   for name in (*runtime, "abort_setup.c", "bounds_guard.c") for opt in gate.OPTS})
    images.update({f"{name}.O{opt}{suffix}": digest for name in ("audit-probe", "guard-control") for opt in gate.OPTS})
    if sanitize: images["sanitizer-probe" + suffix] = digest
    generated = {f"case-{case}.ll": digest for case in range(24)}
    return {"platform": platform, "sanitizers": sanitize, "ownership_audits": ["C", "LLVM"],
            "controls": controls, "programs": rows,
            "compiler_contracts": [{"case": case, "status": "pass", "module_path": f"case-{case}.ll", "module_sha256": digest} for case in range(24)],
            "compiler": {"path": probe, "sha256": digest, "memory_limit_mib": 64, "live_handle_limit": 1024},
            "clang": {"selected": "/inert/clang", "resolved": "/inert/clang", "sha256": digest},
            "final_clang": {"selected": "/inert/clang", "resolved": "/inert/clang", "sha256": digest},
            "image_hashes": images, "final_image_hashes": dict(images),
            "build_flags": {str(opt): [f"-O{opt}", *gate.AUDIT_FLAGS, *(gate.SANITIZER_FLAGS if sanitize else ())]
                            for opt in gate.OPTS},
            "guard_source_sha256": hashlib.sha256(gate.GUARD_SOURCE.encode()).hexdigest(),
            "abort_setup_sha256": hashlib.sha256(gate.ABORT_SETUP_SOURCE.encode()).hexdigest(),
            "generated_input_hashes": generated, "final_generated_input_hashes": dict(generated),
            "input_hashes": {"fixture": "same"}, "final_input_hashes": {"fixture": "same"}, "frozen_input_hashes": {"fixture": "same"}}


class WordBoundsOracles(unittest.TestCase):
    def setUp(self):
        # Every method is process-free, including mock orchestration and errors.
        self.traps = ExitStack()
        self.addCleanup(self.traps.close)
        for api in ("Popen", "run", "check_output", "call", "check_call"):
            self.traps.enter_context(patch.object(subprocess, api, side_effect=AssertionError("actual process is forbidden")))

    def test_exact_unicode_nul_empty_and_abort_platforms(self):
        for platform in ("linux", "darwin", "win32"):
            for case, (stdout, stderr) in enumerate(gate.OUTPUTS):
                with self.subTest(platform=platform, case=case):
                    gate.exact_program(result(stdout, stderr, gate.exit_code(case, platform)), case, platform=platform)
        self.assertEqual(len(gate.WORD), 5)
        self.assertEqual(len(gate.WORD.encode()), 11)
        self.assertIn("\0é中\n", gate.OUTPUTS[0][0])
        self.assertEqual(gate.OUTPUTS[20][0], "receiver\nindex\n")
        self.assertEqual(gate.OUTPUTS[21][0], "receiver\nstart\nend\n")
        self.assertEqual(gate.OUTPUTS[22][0], "receiver\nstart\ncount\n")

    def test_fatal_rejects_wrong_signal_sanitizer_audit_or_guard(self):
        stdout, stderr = gate.OUTPUTS[21]
        impostors = [result(stdout, stderr, code) for code in (0, 1, 3, 85, 86, 87, 88, 91, -11)]
        impostors += [result(stdout + "bounds-returned\n", stderr, -6), result(stdout.replace("start\n", ""), stderr, -6),
                      result("receiver\nend\nstart\n", stderr, -6), result(stdout, stderr + "audit\n", -6),
                      result(stdout, "AddressSanitizer: error\n", -6), result(stdout, gate.GUARD_ERROR, -6)]
        for impostor in impostors:
            with self.subTest(impostor=impostor), self.assertRaises(gate.GateError):
                gate.exact_program(impostor, 21, platform="linux")

    def test_success_rejects_lost_nul_released_receiver_or_extra_output(self):
        stdout, stderr = gate.OUTPUTS[0]
        for faulty in (result(stdout.replace("\0", "")), result(stdout.replace("11\n", "5\n", 1)),
                       result(stdout, "FREAK: LLVM ownership audit found 1 unreleased word allocation(s)\n"),
                       result(stdout + "extra\n"), result(stdout, status=86)):
            with self.assertRaises(gate.GateError):
                gate.exact_program(faulty, 0, platform="linux")

    def test_windows_crlf_only_and_posix_cr_remains_visible(self):
        for case in (0, 21):
            stdout, stderr = gate.OUTPUTS[case]
            converted = result(stdout.replace("\n", "\r\n"), stderr.replace("\n", "\r\n"), gate.exit_code(case, "win32"))
            gate.exact_program(converted, case, platform="win32")
            with self.assertRaises(gate.GateError):
                gate.exact_program(result(stdout, stderr + "\r", gate.exit_code(case, "win32")), case, platform="win32")
            for platform in ("linux", "darwin"):
                with self.assertRaises(gate.GateError):
                    gate.exact_program(converted, case, platform=platform)

    def test_compiler_requires_complete_protocol_actual_calls(self):
        for case in range(24):
            self.assertEqual(gate.extract_module(compiler(case), case), module(case))
        clean = compiler(0)
        faults = [result(clean.stdout + "extra\n"), result(clean.stdout, "audit\n"), result(clean.stdout, status=1),
                  result(clean.stdout.replace("borrowed=true", "borrowed=false")),
                  result(clean.stdout.replace(gate.BEGIN, gate.BEGIN + gate.BEGIN)),
                  compiler(0, module(0).replace("  %r.char_at.0 = call", "  ; %r.char_at.0 = call")),
                  compiler(0, module(0).replace("  %r.char_at.0 = call", "declare")),
                  compiler(0, module(0).replace("  ret i32", "  %extra = call i64 @freak_v4_word_slice(i64 %w)\n  ret i32")),
                  compiler(0, module(0).replace("define i32 @main", "; define i32 @main")),
                  result(clean.stdout.replace("\n", "\r\n"))]
        for faulty in faults:
            with self.assertRaises(gate.GateError): gate.extract_module(faulty, 0, platform="linux")
        gate.extract_module(result(clean.stdout.replace("\n", "\r\n")), 0, platform="win32")

    def test_source_table_is_closed_and_contains_signed_extremes(self):
        text = FIXTURE.read_text(encoding="utf-8")
        sources = gate.fixture_sources(text)
        self.assertEqual(len(sources), 24)
        self.assertIn('observe(lend value)', sources[0])
        self.assertIn('say value\n pilot empty', sources[0])
        self.assertIn('char_at(-9223372036854775808)', sources[2])
        self.assertIn('slice(9223372036854775807, 9223372036854775807)', sources[11])
        self.assertIn('substring(0, -9223372036854775808)', sources[15])
        self.assertIn('receiver().slice(start(), end())', sources[21])
        self.assertIn('.slice(1, 4).substring(0, 2).char_at(1)', sources[23])
        faults = [text.replace('if case_id == 23', 'if case_id == 22', 1),
                  '\n'.join(line for line in text.splitlines() if not line.strip().startswith('if case_id == 1 { give back')),
                  text.replace('chr(123)', 'chr(0)', 1), text.replace('chr(123)', 'chr(True)', 1),
                  text.replace('chr(123)', 'chr(123.0)', 1), text.replace('chr(123)', 'chr(123, 1)', 1),
                  text.replace('chr(123)', "__import__('os').system('false')", 1)]
        for faulty in faults:
            with self.assertRaises(gate.GateError): gate.fixture_sources(faulty)

    def test_live_guard_calls_unchanged_production_and_detects_stale_owner(self):
        self.assertIn('#include "freak_runtime.c"', gate.GUARD_SOURCE)
        self.assertIn('#include "freak_v4_word_runtime.c"', gate.GUARD_SOURCE)
        self.assertIn('freak_llvm_owned_count != bounds_owners + new_owners', gate.GUARD_SOURCE)
        self.assertIn('bounds_live(0);\n    abort();', gate.GUARD_SOURCE)
        self.assertEqual(gate.GUARD_SOURCE.count('bounds_live(1);'), 3)
        self.assertIn('freak_v4_word_drop(value);\n    bounds_live(0);', gate.GUARD_SOURCE)

    def test_report_rejects_missing_duplicate_flags_controls_or_input_drift(self):
        for sanitize in (False, True):
            valid = complete_report(sanitize); gate.validate_report(valid, sanitize)
            mutations = []
            for key in ('programs', 'compiler_contracts', 'controls'):
                bad = deepcopy(valid); bad[key].pop(); mutations.append(bad)
                bad = deepcopy(valid); bad[key][-1] = bad[key][0]; mutations.append(bad)
            for key, value in (('exit', 88), ('status', 'skip'), ('variant', 'fake'), ('stdout_sha256', 'lost-nul'), ('stderr_sha256', 'wrong-error')):
                bad = deepcopy(valid); bad['programs'][0][key] = value; mutations.append(bad)
            for key in ('guard_source_sha256', 'abort_setup_sha256'):
                bad = deepcopy(valid); bad[key] = 'changed'; mutations.append(bad)
            bad = deepcopy(valid); bad['final_input_hashes']['fixture'] = 'changed'; mutations.append(bad)
            bad = deepcopy(valid); bad['final_generated_input_hashes']['case-0.ll'] = 'changed'; mutations.append(bad)
            bad = deepcopy(valid); bad['final_image_hashes'][bad['programs'][0]['binary_path']] = 'b' * 64; mutations.append(bad)
            bad = deepcopy(valid); bad['programs'][0]['binary_sha256'] = 'b' * 64; mutations.append(bad)
            bad = deepcopy(valid); bad['compiler_contracts'][0]['module_sha256'] = 'b' * 64; mutations.append(bad)
            bad = deepcopy(valid); bad['final_clang']['sha256'] = 'b' * 64; mutations.append(bad)
            bad = deepcopy(valid); bad['frozen_input_hashes']['fixture'] = 'changed'; mutations.append(bad)
            bad = deepcopy(valid)
            del bad['image_hashes']['audit-probe.O0.native']; del bad['final_image_hashes']['audit-probe.O0.native']
            mutations.append(bad)
            bad = deepcopy(valid)
            del bad['image_hashes']['bounds_guard.O3.o']; del bad['final_image_hashes']['bounds_guard.O3.o']
            mutations.append(bad)
            bad = deepcopy(valid); bad['build_flags']['2'].remove(gate.AUDIT_FLAGS[0]); mutations.append(bad)
            bad = deepcopy(valid); bad['build_flags']['3'].append('-O0'); mutations.append(bad)
            bad = deepcopy(valid); bad['build_flags']['3'].append('-DFREAK_RUNTIME_OWNERSHIP_AUDIT=0'); mutations.append(bad)
            bad = deepcopy(valid); bad['build_flags']['3'].append('-fno-sanitize=all'); mutations.append(bad)
            bad = deepcopy(valid); bad['sanitizers'] = not sanitize; mutations.append(bad)
            if sanitize:
                bad = deepcopy(valid); bad['build_flags']['0'].remove(gate.SANITIZER_FLAGS[1]); mutations.append(bad)
            else:
                bad = deepcopy(valid); bad['build_flags']['0'].append('-fsanitize=address'); mutations.append(bad)
            for faulty in mutations:
                with self.assertRaises(gate.GateError): gate.validate_report(faulty, sanitize)

    def mock_gate(self, directory, *, plain, broken=None):
        # Run the actual new Runner, Conservation, main and original bootstrap
        # function source. Only the central guard and transpiler are inert.
        checks = ModuleType('word_bounds_inert_checks')
        checks.__dict__.update(TESTS_ROOT=FIXTURE.parent, RUNTIME_ROOT=ROOT / 'freakc/runtime',
                               RUNTIME_BUILD_ROOT=directory / 'unused', __file__=str(ROOT / 'src/compiler/v4/check_v4.py'),
                               read_text=lambda path: path.read_text(encoding='utf-8'), check_flattened_crates=lambda: 'inert crates',
                               transpile_fixture=lambda crates, fixture: ('inert C source', False),
                               transpile=lambda *args: None, Parser=type('InertParser', (), {}),
                               Lexer=type('InertLexer', (), {}), TypeChecker=type('InertTypeChecker', (), {}),
                               runtime_platform_final_link_args=lambda: [], runtime_platform_link_args=lambda: [],
                               runtime_platform_cache_parts=lambda include: (), Path=Path, sys=sys,
                               rel=lambda path: path.name,
                               hash_text=lambda *parts: hashlib.sha256(''.join(parts).encode()).hexdigest(),
                               write_text_if_changed=lambda path, text: path.write_text(text, encoding='utf-8'))
        tree = ast.parse((ROOT / 'src/compiler/v4/check_v4.py').read_bytes())
        original = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'compile_runtime_smoke')
        exec(compile(ast.Module(body=[original], type_ignores=[]), 'inert-original-bootstrap-source', 'exec'), checks.__dict__)
        finder = gate.FrozenProject(directory / 'frozen-source')
        build = SimpleNamespace(checks=checks, SOURCE_NAMES=gate.literal_assignment(ROOT / 'freakc/v4_native_runtime.py', 'SOURCE_NAMES'),
                                bounds_finder=finder, host_target=lambda: 'inert-target')
        commands = []
        def inert_guard(command, *, label, **limits):
            commands.append((command, label, limits))
            if command[-1] == '--version': return result('mock clang identity\n')
            if command[-1] == '--emit': return compiler(int(command[1]))
            if '-o' in command:
                Path(command[command.index('-o') + 1]).write_bytes(b'mock native binary'); return result()
            if 'audit-probe' in command[0]:
                kind = command[1]
                return result('', f'FREAK: {kind} ownership audit found 1 unreleased word allocation(s)\n', 87 if kind == 'C' else 86)
            if 'guard-control' in command[0]: return result('', '' if broken == 'guard' else gate.GUARD_ERROR, 91)
            if 'sanitizer-probe' in command[0]:
                message = 'ERROR: AddressSanitizer: heap-use-after-free\n' if command[1] == 'address' else 'runtime error: signed integer overflow\n'
                return result('', '' if broken == 'sanitizer' else message, 88)
            case = int(Path(command[0]).name.split('.')[0].split('-')[1])
            if broken == 'image' and label == 'execute case 23 live O3':
                (directory / 'case-0.direct.O0.native').write_bytes(b'changed prior image')
            if broken == 'module' and label == 'execute case 23 live O3':
                (directory / 'case-0.ll').write_bytes(b'changed prior module')
            return result(*gate.OUTPUTS[case], gate.exit_code(case))
        checks.run_with_heartbeat = inert_guard
        tool = directory.parent / (directory.name + '-inert-clang')
        tool.write_bytes(b'inert tool identity; never executed')
        with ExitStack() as mocks, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            mocks.enter_context(patch.object(gate, 'load_build', return_value=build))
            mocks.enter_context(patch.object(gate.sys, 'platform', 'linux'))
            mocks.enter_context(patch.object(sys, 'meta_path', [finder, *sys.meta_path]))
            try:
                code = gate.main(['--clang', str(tool), '--work', str(directory), *(['--plain'] if plain else [])])
            except gate.GateError:
                code = 1
        return code, json.loads((directory / 'results.json').read_text()), commands

    def test_mock_complete_matrices_use_guard_and_serialized_compiler_limits(self):
        with tempfile.TemporaryDirectory() as temporary:
            for plain in (False, True):
                code, report, commands = self.mock_gate(Path(temporary) / str(plain), plain=plain)
                self.assertEqual(code, 0, report.get('error')); self.assertTrue(report['passed'])
                gate.validate_report(report, not plain)
                self.assertEqual(len(report['programs']), 144)
                self.assertEqual(len(report['controls']), 9 if plain else 11)
                emits = [row for row in commands if row[1].startswith('emit case')]
                self.assertEqual(len(emits), 24)
                self.assertTrue(all(row[2] == {'timeout_seconds': 60, 'memory_limit_mb': 64, 'output_limit_mb': 8} for row in emits))
                bootstrap = [row for row in commands if row[1].startswith('runtime compile:')]
                self.assertEqual(len(bootstrap), 1)
                self.assertEqual(bootstrap[0][2], {'timeout_seconds': 120, 'memory_limit_mb': 1024, 'output_limit_mb': 8})
                self.assertEqual(len(list((Path(temporary) / str(plain)).glob('*.command.json'))), len(commands))
                self.assertEqual(len(commands), 356 if plain else 359)
                for _, label, limits in commands:
                    if label == 'clang identity': expected = (10, 64)
                    elif label.startswith('runtime compile:'): expected = (120, 1024)
                    elif label.startswith('emit case'): expected = (60, 64)
                    elif label.startswith(('compile ', 'link ')): expected = (120, 512)
                    else: expected = (30, 128)
                    self.assertEqual(limits, {'timeout_seconds': expected[0], 'memory_limit_mb': expected[1], 'output_limit_mb': 8})
                self.assertEqual(report['compiler']['memory_limit_mib'], 64)
                self.assertEqual(report['compiler']['live_handle_limit'], 1024)
                live_links = [row[0] for row in commands if row[1].startswith('link case') and ' live ' in row[1]]
                for command in live_links:
                    self.assertEqual(sum('bounds_guard.O' in token for token in command), 1)
                    self.assertFalse(any(Path(token).name.startswith(('freak_runtime.O', 'freak_v4_word_runtime.O')) for token in command))

    def test_broken_guard_and_sanitizer_save_failed_partial_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            for broken in ('guard', 'sanitizer', 'image', 'module'):
                code, report, _ = self.mock_gate(Path(temporary) / broken, plain=False, broken=broken)
                self.assertEqual(code, 1); self.assertFalse(report['passed']); self.assertIn('error', report)
                self.assertTrue(report['artifacts'])

    def test_existing_work_and_off_linux_default_fail_before_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = Path(temporary) / 'results.json'; marker.write_bytes(b'historical proof')
            with self.assertRaises(FileExistsError): gate.main(['--clang', 'mock', '--plain', '--work', temporary])
            self.assertEqual(marker.read_bytes(), b'historical proof')
            directory = Path(temporary) / 'must-not-create'
            with patch.object(gate.sys, 'platform', 'win32'), patch.object(gate.shutil, 'which', return_value='mock'), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as failure: gate.main(['--clang', 'mock', '--work', str(directory)])
                self.assertEqual(failure.exception.code, 2); self.assertFalse(directory.exists())

    def test_actual_runner_first_cause_and_raw_channels_survive_retention_faults(self):
        with tempfile.TemporaryDirectory() as temporary:
            for primary_kind in (RuntimeError, KeyboardInterrupt, Hostile):
                for secondary_kind in (MemoryError, KeyboardInterrupt):
                    folder = Path(temporary) / (primary_kind.__name__ + secondary_kind.__name__)
                    folder.mkdir()
                    primary = primary_kind('first cause'); cause = ValueError('explicit cause')
                    primary.__cause__ = cause
                    primary.stdout = b'raw\0stdout\n'; primary.stderr = 'raw é stderr\n'
                    def guard(*args, **kwargs): raise primary
                    real_write = Path.write_text
                    def writing(path, *args, **kwargs):
                        if path.name.endswith('.failure.txt'): raise secondary_kind('secondary retention')
                        return real_write(path, *args, **kwargs)
                    runner = gate.Runner(SimpleNamespace(run_with_heartbeat=guard), folder)
                    with patch.object(Path, 'write_text', writing), self.assertRaises(primary_kind) as raised:
                        runner.run(['INERT-NOT-EXECUTED'], 'first-cause')
                    self.assertIs(raised.exception, primary); self.assertIs(primary.__cause__, cause)
                    self.assertEqual((folder / '001-first-cause.stdout').read_bytes(), primary.stdout)
                    self.assertEqual((folder / '001-first-cause.stderr').read_bytes(), primary.stderr.encode())
                    metadata = json.loads((folder / '001-first-cause.retention.json').read_text())
                    self.assertEqual(metadata['secondary_failures'][0], {'stage': 'failure-descriptor', 'type': secondary_kind.__name__})

    def test_actual_runner_retains_independent_success_channels_and_limits(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary); calls = []
            def guard(argv, **kwargs):
                calls.append(kwargs)
                return result('raw\0stdout\n', 'raw stderr\n')
            runner = gate.Runner(SimpleNamespace(run_with_heartbeat=guard), folder)
            real_write = Path.write_bytes; primary = MemoryError('channel retention')
            def writing(path, data):
                if path.suffix == '.stdout': raise primary
                return real_write(path, data)
            with patch.object(Path, 'write_bytes', writing), self.assertRaises(MemoryError) as raised:
                runner.run(['INERT-NOT-EXECUTED'], 'native', timeout=30, memory=128)
            self.assertIs(raised.exception, primary)
            self.assertEqual(calls, [{'label': 'native', 'timeout_seconds': 30, 'memory_limit_mb': 128, 'output_limit_mb': 8}])
            self.assertEqual((folder / '001-native.stderr').read_bytes(), b'raw stderr\n')
            self.assertTrue((folder / '001-native.result.json').is_file())

    def test_main_preserves_body_first_cause_with_failed_report_and_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            for primary_kind in (RuntimeError, KeyboardInterrupt, Hostile):
                for secondary_kind in (MemoryError, KeyboardInterrupt):
                    folder = Path(temporary) / (primary_kind.__name__ + secondary_kind.__name__)
                    primary = primary_kind('first body cause'); cause = ValueError('explicit cause'); primary.__cause__ = cause
                    entered = []
                    def body(args, report): entered.append(True); raise primary
                    real_write = Path.write_text
                    def writing(path, *args, **kwargs):
                        if entered and path.name == 'results.json': raise secondary_kind('report secondary')
                        return real_write(path, *args, **kwargs)
                    with patch.object(gate, 'run_gate', body), patch.object(Path, 'write_text', writing), \
                            patch.object(Path, 'rglob', side_effect=secondary_kind('artifact secondary')), \
                            redirect_stderr(io.StringIO()), self.assertRaises(primary_kind) as raised:
                        gate.main(['--plain', '--clang', 'INERT-NOT-EXECUTED', '--work', str(folder)])
                    self.assertIs(raised.exception, primary); self.assertIs(primary.__cause__, cause)
                    self.assertFalse(json.loads((folder / 'results.json').read_text())['passed'])
                    self.assertEqual([row['stage'] for row in primary.bounds_secondary_failures], ['failure-artifacts', 'failure-publication'])

    def test_success_candidate_publication_failure_keeps_durable_false(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / 'work'; primary = MemoryError('success publication')
            fake_pins = SimpleNamespace(final_pins=lambda: None, check=lambda: None)
            real_write = Path.write_text
            def writing(path, *args, **kwargs):
                if path.name == 'results.pending.json': raise primary
                return real_write(path, *args, **kwargs)
            with patch.object(gate, 'run_gate', return_value=fake_pins), patch.object(gate, 'validate_report', return_value=None), \
                    patch.object(Path, 'write_text', writing), redirect_stdout(io.StringIO()) as stdout, \
                    redirect_stderr(io.StringIO()), self.assertRaises(MemoryError) as raised:
                gate.main(['--plain', '--clang', 'INERT-NOT-EXECUTED', '--work', str(folder)])
            self.assertIs(raised.exception, primary); self.assertNotIn('PASS', stdout.getvalue())
            report = json.loads((folder / 'results.json').read_text())
            self.assertFalse(report['passed']); self.assertEqual(report['error'], {'type': 'MemoryError'})

    def test_restore_failure_prevents_success_candidate_publication(self):
        class Environment(dict):
            def __setitem__(self, name, value):
                if value == 'caller-ASAN': raise MemoryError('restore after success body')
                return super().__setitem__(name, value)
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / 'work'
            with patch.object(gate.os, 'environ', Environment(ASAN_OPTIONS='caller-ASAN')), \
                    patch.object(gate, 'run_gate', return_value=SimpleNamespace(final_pins=lambda: None)), \
                    redirect_stdout(io.StringIO()) as stdout, redirect_stderr(io.StringIO()), self.assertRaises(MemoryError):
                gate.main(['--plain', '--clang', 'INERT-NOT-EXECUTED', '--work', str(folder)])
            self.assertNotIn('PASS', stdout.getvalue()); self.assertFalse((folder / 'results.pending.json').exists())
            self.assertFalse(json.loads((folder / 'results.json').read_text())['passed'])

    def test_run_gate_preserves_identity_first_cause_with_failed_final_pins(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            for primary_kind in (RuntimeError, KeyboardInterrupt):
                primary = primary_kind('identity first cause'); cause = ValueError('explicit cause'); primary.__cause__ = cause
                def guard(*args, **kwargs): raise primary
                def final_pins(): raise MemoryError('final hash secondary')
                pins = SimpleNamespace(frozen=ROOT, clang=Path('INERT-NOT-EXECUTED'), seal_build=lambda build: None,
                                       bind=lambda *args: None, check=lambda: None, guards=[], final_pins=final_pins)
                checks = SimpleNamespace(TESTS_ROOT=FIXTURE.parent, RUNTIME_ROOT=ROOT / 'freakc/runtime',
                                         run_with_heartbeat=guard, read_text=lambda path: path.read_text())
                build = SimpleNamespace(checks=checks, host_target=lambda: 'inert-target',
                                        SOURCE_NAMES=gate.literal_assignment(ROOT / 'freakc/v4_native_runtime.py', 'SOURCE_NAMES'))
                with patch.object(gate, 'Conservation', return_value=pins), patch.object(gate, 'load_build', return_value=build), \
                        self.assertRaises(primary_kind) as raised:
                    gate.run_gate(SimpleNamespace(work=folder, clang='INERT-NOT-EXECUTED', plain=True), {})
                self.assertIs(raised.exception, primary); self.assertIs(primary.__cause__, cause)
                self.assertEqual(primary.bounds_secondary_failures[-1], {'stage': 'final-pins', 'type': 'MemoryError'})

    def test_environment_independently_restores_after_all_first_causes(self):
        class Environment(dict):
            def __init__(self):
                super().__init__({name: 'caller-' + name for name in ('ASAN_OPTIONS', 'LSAN_OPTIONS', 'UBSAN_OPTIONS')})
                self.fail = False; self.actions = []
            def __setitem__(self, name, value):
                if value.startswith('caller-'):
                    self.actions.append(name)
                    if self.fail and name == 'ASAN_OPTIONS': raise MemoryError('restore secondary')
                return super().__setitem__(name, value)
        for primary_kind in (RuntimeError, KeyboardInterrupt, Hostile):
            environment = Environment(); primary = primary_kind('body first cause')
            with patch.object(gate.os, 'environ', environment), self.assertRaises(primary_kind) as raised:
                with gate.sanitizer_environment(True):
                    self.assertEqual(environment['ASAN_OPTIONS'], 'halt_on_error=1:detect_leaks=1:exitcode=88')
                    self.assertEqual(environment['UBSAN_OPTIONS'], 'halt_on_error=1:print_stacktrace=1:exitcode=88')
                    environment.fail = True; raise primary
            self.assertIs(raised.exception, primary)
            self.assertEqual(environment.actions, ['ASAN_OPTIONS', 'LSAN_OPTIONS', 'UBSAN_OPTIONS'])
            self.assertEqual(environment['LSAN_OPTIONS'], 'caller-LSAN_OPTIONS')
            self.assertEqual(environment['UBSAN_OPTIONS'], 'caller-UBSAN_OPTIONS')
        environment = Environment()
        with patch.object(gate.os, 'environ', environment), self.assertRaises(MemoryError):
            with gate.sanitizer_environment(False): environment.fail = True
        self.assertEqual(environment.actions, ['ASAN_OPTIONS', 'LSAN_OPTIONS', 'UBSAN_OPTIONS'])

    def test_loader_rejects_preloads_and_executes_frozen_source_without_bytecode(self):
        with tempfile.TemporaryDirectory() as temporary:
            frozen = Path(temporary)
            for name in ('build_v4', 'check_v4', 'freakc', 'freakc.lexer'):
                foreign = ModuleType(name); foreign.__file__ = '/external/impostor.py'
                with patch.dict(sys.modules, {name: foreign}), self.assertRaises(gate.GateError): gate.load_build(frozen)
            (frozen / 'src/compiler/v4').mkdir(parents=True)
            (frozen / 'freakc').mkdir()
            (frozen / 'src/compiler/v4/build_v4.py').write_text('import check_v4 as checks\n')
            (frozen / 'src/compiler/v4/check_v4.py').write_text('from freakc.lexer import literal\n')
            (frozen / 'freakc/__init__.py').write_text('')
            (frozen / 'freakc/lexer.py').write_text('literal = "exact frozen source"\n')
            before = dict(sys.modules); before_meta = list(sys.meta_path)
            try:
                build = gate.load_build(frozen)
                self.assertEqual(build.checks.literal, 'exact frozen source')
                for name in ('build_v4', 'check_v4', 'freakc', 'freakc.lexer'):
                    self.assertTrue(Path(sys.modules[name].__file__).is_relative_to(frozen))
                self.assertFalse(list(frozen.rglob('*.pyc'))); self.assertFalse(list(frozen.rglob('__pycache__')))
            finally:
                sys.meta_path[:] = before_meta
                for name in tuple(sys.modules):
                    if name not in before: del sys.modules[name]

    def test_conservation_full_closure_tool_binding_and_image_checks(self):
        names = gate.source_names()
        self.assertEqual(set(name for name in names if name.startswith('freakc/') and name.endswith('.py')),
                         set(path.relative_to(ROOT).as_posix() for path in (ROOT / 'freakc').rglob('*.py')))
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary); tool = folder / 'inert-clang'; tool.write_bytes(b'never execute this tool')
            report = {}; pins = gate.Conservation(SimpleNamespace(work=folder, clang=str(tool)), report)
            for image in (False, True):
                path = folder / ('probe.o' if image else 'case.ll'); path.write_bytes(b'produced bytes')
                pins.track(path, image=image); path.write_bytes(b'changed bytes')
                with self.assertRaises(gate.GateError): pins.check()
                path.write_bytes(b'produced bytes'); pins.check()
            original = tool.read_bytes(); tool.write_bytes(b'different tool')
            with self.assertRaises(gate.GateError): pins.check()
            tool.write_bytes(original)
            frozen = pins.frozen / 'freakc/lexer.py'; original = frozen.read_bytes(); frozen.write_bytes(b'changed bootstrap')
            with self.assertRaises(gate.GateError): pins.check()
            frozen.write_bytes(original)
            checks = SimpleNamespace(run_with_heartbeat=lambda *args, **kwargs: result())
            runner = gate.Runner(checks, folder, pins)
            with patch.object(checks, 'run_with_heartbeat', lambda *args, **kwargs: result()), self.assertRaises(gate.GateError): pins.check()
            with patch.object(runner, 'guard', lambda *args, **kwargs: result()), self.assertRaises(gate.GateError): pins.check()
            pins.final_pins()
            self.assertEqual(report['input_hashes'], report['frozen_input_hashes'])
            self.assertEqual(report['image_hashes'], report['final_image_hashes'])


if __name__ == '__main__': unittest.main()
