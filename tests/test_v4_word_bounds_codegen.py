"""Process-free adversarial controls for generated word bounds evidence."""
from __future__ import annotations

from contextlib import ExitStack, redirect_stderr, redirect_stdout
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("word_bounds_gate", ROOT / "tests/v4_word_bounds_codegen.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)
FIXTURE = ROOT / "src/compiler/v4/tests/word_bounds_execute_smoke.fk"


def result(stdout="", stderr="", status=0):
    return subprocess.CompletedProcess(["mock"], status, stdout, stderr)


def module(case):
    instructions = ""
    for kind, count in zip(("char_at", "slice", "substring"), gate.call_counts(case)):
        for index in range(count):
            instructions += f"  %r.{kind}.{index} = call i64 @freak_v4_word_{kind}(i64 %w, i64 0)\n"
    return "define i32 @main(i32 %argc, ptr %argv) {\n" + instructions + "  ret i32 0\n}\n"


def compiler(case, body=None):
    return result(gate.prefix(case) + gate.BEGIN + (module(case) if body is None else body) + gate.END)


def complete_report(sanitize=True, platform="linux"):
    rows = []
    for case, (stdout, stderr) in enumerate(gate.OUTPUTS):
        for opt in gate.OPTS:
            for variant in gate.VARIANTS:
                rows.append({"case": case, "optimization": opt, "variant": variant, "status": "pass",
                             "exit": gate.exit_code(case, platform),
                             "stdout_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
                             "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest()})
    controls = [{"name": f"audit-{kind}-O{opt}", "status": "pass"}
                for kind in ("C", "LLVM") for opt in gate.OPTS]
    controls += [{"name": f"guard-live-O{opt}", "status": "pass"} for opt in gate.OPTS]
    if sanitize:
        controls += [{"name": "sanitizer-" + kind, "status": "pass"} for kind in ("address", "undefined")]
    return {"platform": platform, "sanitizers": sanitize, "ownership_audits": ["C", "LLVM"],
            "controls": controls, "programs": rows,
            "compiler_contracts": [{"case": case, "status": "pass"} for case in range(24)],
            "build_flags": {str(opt): [f"-O{opt}", *gate.AUDIT_FLAGS, *(gate.SANITIZER_FLAGS if sanitize else ())]
                            for opt in gate.OPTS},
            "guard_source_sha256": hashlib.sha256(gate.GUARD_SOURCE.encode()).hexdigest(),
            "abort_setup_sha256": hashlib.sha256(gate.ABORT_SETUP_SOURCE.encode()).hexdigest(),
            "generated_input_hashes": {"guard.c": "same"}, "final_generated_input_hashes": {"guard.c": "same"},
            "input_hashes": {"fixture": "same"}, "final_input_hashes": {"fixture": "same"}}


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
            bad = deepcopy(valid); bad['final_generated_input_hashes']['guard.c'] = 'changed'; mutations.append(bad)
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
        from freakc.v4_native_runtime import SOURCE_NAMES
        checks = SimpleNamespace(TESTS_ROOT=FIXTURE.parent, RUNTIME_ROOT=ROOT / 'freakc/runtime',
                                 RUNTIME_BUILD_ROOT=directory / 'unused', __file__=str(ROOT / 'src/compiler/v4/check_v4.py'),
                                 CRATE_ORDER=('freak_ty',), crate_path=lambda name: ROOT / 'src/compiler/v4/crates' / name / 'src/lib.fk',
                                 read_text=lambda path: path.read_text(encoding='utf-8'), check_flattened_crates=lambda: 'mock crates',
                                 transpile_fixture=lambda crates, fixture: ('mock source', False),
                                 compile_runtime_smoke=lambda *args: (FIXTURE, None), runtime_platform_final_link_args=lambda: [])
        build = SimpleNamespace(checks=checks, SOURCE_NAMES=SOURCE_NAMES, __file__=str(ROOT / 'src/compiler/v4/build_v4.py'), host_target=lambda: 'mock-target')
        commands = []
        class MockRunner:
            def __init__(self, checks, directory): pass
            def run(self, command, label, **limits):
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
                return result(*gate.OUTPUTS[case], gate.exit_code(case))
        with ExitStack() as mocks, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            mocks.enter_context(patch.object(gate, 'load_build', return_value=build))
            mocks.enter_context(patch.object(gate, 'Runner', MockRunner))
            mocks.enter_context(patch.object(gate.sys, 'platform', 'linux'))
            code = gate.main(['--clang', 'mock', '--work', str(directory), *(['--plain'] if plain else [])])
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
                self.assertEqual(len(emits), 24); self.assertTrue(all(row[2] == {} for row in emits))
                self.assertEqual(report['compiler']['memory_limit_mib'], 64)
                self.assertEqual(report['compiler']['live_handle_limit'], 1024)
                live_links = [row[0] for row in commands if row[1].startswith('link case') and ' live ' in row[1]]
                for command in live_links:
                    self.assertEqual(sum('bounds_guard.O' in token for token in command), 1)
                    self.assertFalse(any(Path(token).name.startswith(('freak_runtime.O', 'freak_v4_word_runtime.O')) for token in command))

    def test_broken_guard_and_sanitizer_save_failed_partial_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            for broken in ('guard', 'sanitizer'):
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


if __name__ == '__main__': unittest.main()
