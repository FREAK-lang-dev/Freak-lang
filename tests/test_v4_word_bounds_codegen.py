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

    def native_build_calls(self):
        tree = ast.parse(Path(gate.__file__).read_text(encoding="utf-8"))
        run_gate = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "run_gate")
        targets = [node.value for node in ast.walk(run_gate) if isinstance(node, ast.Assign)
                   and any(isinstance(name, ast.Name) and name.id == "target" for name in node.targets)]
        self.assertEqual(len(targets), 1)
        self.assertEqual(ast.unparse(targets[0]), "build.host_target()")
        calls = {}
        for node in ast.walk(run_gate):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "run" and len(node.args) > 1):
                continue
            label = node.args[1]
            if isinstance(label, ast.JoinedStr): label = label.values[0]
            if isinstance(label, ast.Constant) and label.value in (
                    "compile ", "link audit O", "link guard O", "link case ", "link sanitizer capabilities", "emit case "):
                self.assertNotIn(label.value, calls)
                calls[label.value] = node
        self.assertEqual(set(calls), {"compile ", "link audit O", "link guard O", "link case ", "link sanitizer capabilities", "emit case "})
        return calls

    def native_build_contexts(self):
        for target, libraries in (("x86_64-w64-windows-gnu", ["-lws2_32", "-lshell32"]),
                                  ("x86_64-unknown-linux-gnu", ["-lm"]), ("aarch64-apple-darwin", [])):
            for sanitized in (False, True):
                for opt in gate.OPTS:
                    flags = ["-w", f"-O{opt}", "-Iruntime", *gate.AUDIT_FLAGS]
                    if sanitized: flags += gate.SANITIZER_FLAGS
                    values = {"args": SimpleNamespace(clang="clang"), "target": target, "flags": flags,
                              "source": Path("source.c"), "output": Path("runtime.obj"), "audit": Path("audit.c"),
                              "audit_binary": Path("audit-probe.exe"), "guard_control": Path("guard.c"),
                              "guard_binary": Path("guard-control.exe"), "llvm": Path("module.ll"),
                              "binary": Path("program.exe"), "selected": ["runtime.obj", "guard.obj"],
                              "direct": ["runtime.obj", "abort.obj"], "live": ["runtime.obj", "guard.obj"],
                              "probe": Path("compiler.exe"), "case": 17, "str": str,
                              "SANITIZER_FLAGS": gate.SANITIZER_FLAGS,
                              "checks": SimpleNamespace(runtime_platform_final_link_args=lambda: libraries)}
                    expected = {
                        "compile ": [*flags, "-c", "source.c", "-o", "runtime.obj"],
                        "link audit O": [*flags, "audit.c", "runtime.obj", "abort.obj", "-o", "audit-probe.exe", *libraries],
                        "link guard O": [*flags, "guard.c", "runtime.obj", "guard.obj", "-o", "guard-control.exe", *libraries],
                        "link case ": [*flags, "module.ll", "runtime.obj", "guard.obj", "-o", "program.exe", *libraries],
                        "link sanitizer capabilities": ["-O0", *gate.SANITIZER_FLAGS, "source.c", "-o", "program.exe"],
                    }
                    yield target, sanitized, opt, values, expected

    def assert_native_build_command(self, call, values, expected):
        command = compile(ast.Expression(call.args[0]), gate.__file__, "eval")
        argv = eval(command, {"__builtins__": {}}, values)
        self.assertEqual(argv, ["clang", "--target=" + values["target"], *expected])
        self.assertEqual({keyword.arg: ast.literal_eval(keyword.value) for keyword in call.keywords},
                         {"timeout": 120, "memory": 512})

    def test_all_native_build_stages_pin_the_emitted_host_target(self):
        calls = self.native_build_calls()
        for target, sanitized, opt, values, expected in self.native_build_contexts():
            emission = compile(ast.Expression(calls["emit case "].args[0]), gate.__file__, "eval")
            self.assertEqual(eval(emission, {"__builtins__": {}}, values), ["compiler.exe", "17", target, "--emit"])
            for label, tail in expected.items():
                with self.subTest(target=target, sanitized=sanitized, opt=opt, stage=label):
                    self.assert_native_build_command(calls[label], values, tail)

    def test_each_missing_native_build_target_is_rejected(self):
        calls = self.native_build_calls()
        for label in ("compile ", "link audit O", "link guard O", "link case ", "link sanitizer capabilities"):
            mutant = deepcopy(calls[label])
            original = mutant.args[0].elts
            self.assertIsInstance(original[1], ast.JoinedStr)
            self.assertEqual(ast.unparse(original[1]), "f'--target={target}'")
            mutant.args[0].elts = [original[0], *original[2:]]
            for target, sanitized, opt, values, expected in self.native_build_contexts():
                with self.subTest(target=target, sanitized=sanitized, opt=opt, stage=label), self.assertRaises(AssertionError):
                    self.assert_native_build_command(mutant, values, expected[label])

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

    def test_ascii_unicode_fixture_preserves_original_source_bytes(self):
        text = FIXTURE.read_bytes()
        self.assertTrue(text.isascii())
        sources = gate.fixture_sources(text.decode("ascii"))
        # Original accepted UTF-8 programs, captured before ASCII construction.
        expected = (
            '13679f1d2642d2fca2451e51c57a3a311e643cbbe33101bab5349c8f46c0724e',
            'bed1c9180bdec67dbb0f8b2f2c773694ad6740bba2a1e7f408f8a15b6bcc5c95',
            '0bed6d1d1e5b67066cd1ecd884982df7675d7b42ef2c1f9714613bad7d2a0be0',
            'f6f8989e77a575efdc2c78f5efd994832fbf355dbb2b7254b00b52a9d6ac0034',
            '1c64fc67027bb9f54118a4f3d9617ffca51b1250bfb5134fddda323111a7d001',
            '32263fa947b7b4f84bbb6ff9a6fee658b255d7d9c20351eaf25c9ef104c4bdba',
            'ad89e5b09b951032c802beb766834049781c7ac9f76651330c0a2c4bb4465607',
            '4910bc66dba22b78dd18f12674a67e150f53b0dd482bd54a703e58c8ef644788',
            '78badba2966d1b7b95a04a8acbe7cb2b1e1417199d67b75205ae3fe94b9404bc',
            '6c9181a1a0286d538988c817905e3e677c8f054a6f6aef5bf3c76dc243870f1d',
            '89ad7a194ee899ded88978d29434c395bfee9f20cb845cfe105998c711a7ed93',
            '7653e7906432e88a0469f0556140335cc35d785c425a4e7ac9f260cb281ff22b',
            '021ea9cc71453e20c8cde0ee7b41618dfa6466a57ccda28cd624ec66b878597d',
            'eec5bdda358cf995a358ac861ea6f55faf1652f59d6aa8e35b2b95d7190d8fb6',
            'f9a64b699fc29b166edb78ea4db452064923ee208f93efa9c013415a0ecfc5a4',
            'b361f9692b9a650564555aea577cda8693eaffa2cac3b2c86bad34af6e1c76cd',
            'f26024621cd70be240a00325a1b6128dcd21ec36578ba166bd4f31472ffe5676',
            '91977d9a69dedf797d76674578d032200af6f4a8d7db96d8e74a731a2ce143ba',
            '46afff6fd1da9239bdf2914f5341af7ea12b88583df53cd94039a05bf40e8872',
            '302e1140dada04dbf8aec0c95e90c9df016883c85ca2bfcc71f2e66ee046ba8d',
            'e9892947813968b46d6f7c9cb618ab4493a30982a66b4eb4b26f69f16e467ccc',
            'b161f9a76f02cdcee42af70ce7ca22f1f09b4ffb2e4cc6b195da352547a57be6',
            'f9d24170a7eff1a04f686689b368bc31f95194b3fadfde6d56fc3c78d7151c73',
            '03063b8f2cce6886e7914f50457e530cb67b114850bf80ce2624892c64fa3dad',
        )
        self.assertEqual(tuple(hashlib.sha256(source.encode("utf-8")).hexdigest() for source in sources), expected)
        for code in (0, 65, 232, 234, 304, 20012, 20014, 128511, 128513, 1114112):
            with self.subTest(code=code), self.assertRaises(gate.GateError):
                gate.fixture_sources(text.decode("ascii").replace("chr(233)", f"chr({code})", 1))

    def test_live_guard_calls_unchanged_production_and_detects_stale_owner(self):
        self.assertIn('#include "freak_runtime.c"', gate.GUARD_SOURCE)
        self.assertIn('#include "freak_v4_word_runtime.c"', gate.GUARD_SOURCE)
        self.assertIn('freak_llvm_owned_count != bounds_owners + new_owners', gate.GUARD_SOURCE)
        self.assertIn('bounds_live(0);\n    abort();', gate.GUARD_SOURCE)
        self.assertEqual(gate.GUARD_SOURCE.count('bounds_live(1);'), 3)
        self.assertIn('freak_v4_word_drop(value);\n    bounds_live(0);', gate.GUARD_SOURCE)

    def test_raw_lf_and_crlf_fixture_preserve_program_bytes_and_closed_table(self):
        lf = FIXTURE.read_bytes().decode("ascii").replace("\r\n", "\n")
        expected = gate.fixture_sources(lf)
        crlf = lf.replace("\n", "\r\n")
        self.assertNotEqual(lf.encode(), crlf.encode())
        for text in (lf, crlf):
            with self.subTest(transport="CRLF" if text == crlf else "LF"):
                self.assertEqual([source.encode("utf-8") for source in gate.fixture_sources(text)],
                                 [source.encode("utf-8") for source in expected])
                for faulty in (text.replace("chr(233)", "chr(234)", 1),
                               text.replace("chr(233)", "chr(True)", 1),
                               text.replace("chr(233)", "chr(233.0)", 1),
                               text.replace("chr(233)", "chr(233, 1)", 1),
                               text.replace("chr(233)", "__import__('os').system('false')", 1),
                               text.replace("if case_id == 23", "if case_id == 22", 1)):
                    with self.assertRaises(gate.GateError):
                        gate.fixture_sources(faulty)

    def test_generated_source_bytes_remain_exact_under_windows_text_io(self):
        original_write, original_read = Path.write_text, Path.read_text
        recipe = FIXTURE.read_bytes().decode("ascii").replace("\r\n", "\n")
        expected = gate.fixture_sources(recipe)
        def windows_write(path, text, encoding=None, errors=None, newline=None):
            physical = text.replace("\n", "\r\n") if newline is None else text
            return original_write(path, physical, encoding=encoding, errors=errors, newline="\n")
        def raw_fixture_read(path, *args, **kwargs):
            if path == FIXTURE:
                return recipe.replace("\n", "\r\n")
            return original_read(path, *args, **kwargs)
        with tempfile.TemporaryDirectory() as temporary:
            for plain in (False, True):
                directory = Path(temporary) / str(plain)
                with patch.object(Path, "write_text", windows_write), patch.object(Path, "read_text", raw_fixture_read):
                    code, report, commands = self.mock_gate(directory, plain=plain)
                self.assertEqual(code, 0, report.get("error"))
                self.assertTrue(report["passed"])
                gate.validate_report(report, not plain)
                self.assertEqual([hashlib.sha256(source.encode()).hexdigest() for source in expected], report["source_sha256"])
                for case, source in enumerate(expected):
                    self.assertEqual((directory / f"case-{case}.fk").read_bytes(), source.encode("utf-8"))
                    self.assertEqual((directory / f"case-{case}.ll").read_bytes(), module(case).encode("utf-8"))
                self.assertEqual((directory / "bounds_guard.c").read_bytes(), gate.GUARD_SOURCE.encode("utf-8"))
                self.assertEqual((directory / "abort_setup.c").read_bytes(), gate.ABORT_SETUP_SOURCE.encode("utf-8"))
                names = ("audit_probe.c", "bounds_guard.c", "abort_setup.c", "guard_control.c")
                if not plain:
                    names += ("sanitizer_probe.c",)
                for name in names:
                    self.assertNotIn(b"\r", (directory / name).read_bytes())
                runtime_count = len(gate.literal_assignment(ROOT / "freakc/v4_native_runtime.py", "SOURCE_NAMES"))
                self.assertEqual(len(commands), 26 + 3 * (runtime_count + 103) + (0 if plain else 3))

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
            # The inert pipeline models Linux even when these real helpers
            # captured another host at import. Bind defaults before sealing.
            mocks.enter_context(patch.object(gate.exit_code, '__defaults__', ('linux',)))
            mocks.enter_context(patch.object(gate.extract_module, '__kwdefaults__', {'platform': 'linux'}))
            mocks.enter_context(patch.object(gate.exact_program, '__kwdefaults__', {'platform': 'linux'}))
            mocks.enter_context(patch.object(sys, 'meta_path', [finder, *sys.meta_path]))
            try:
                code = gate.main(['--clang', str(tool), '--work', str(directory), *(['--plain'] if plain else [])])
            except gate.GateError:
                code = 1
        return code, json.loads((directory / 'results.json').read_text()), commands

    def test_mock_linux_platform_restores_windows_bound_oracles(self):
        name = 'word_bounds_windows_model'
        with patch.object(sys, 'platform', 'win32'):
            modeled = gate.source_module(name, ROOT / 'tests/v4_word_bounds_codegen.py')
        try:
            self.assertEqual(modeled.exit_code.__defaults__, ('win32',))
            self.assertEqual(modeled.exact_program.__kwdefaults__, {'platform': 'win32'})
            originals = (modeled.exit_code.__defaults__, modeled.extract_module.__kwdefaults__,
                         modeled.exact_program.__kwdefaults__)
            with patch.dict(globals(), gate=modeled), tempfile.TemporaryDirectory() as temporary:
                code, report, _ = self.mock_gate(Path(temporary) / 'windows-import', plain=True)
            self.assertEqual(code, 0, report.get('error'))
            self.assertTrue(report['passed'])
            self.assertEqual(report['platform'], 'linux')
            self.assertTrue(all(row['exit'] == modeled.exit_code(row['case'], 'linux')
                                for row in report['programs']))
            for observed, original in zip((modeled.exit_code.__defaults__, modeled.extract_module.__kwdefaults__,
                                          modeled.exact_program.__kwdefaults__), originals):
                self.assertIs(observed, original)
            self.assertEqual(modeled.exit_code(1), 3)
        finally:
            sys.modules.pop(name + '_numeric', None)
            sys.modules.pop(name, None)

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
                runtime_count = len(gate.literal_assignment(ROOT / 'freakc/v4_native_runtime.py', 'SOURCE_NAMES'))
                self.assertEqual(len(commands), 26 + 3 * (runtime_count + 103) + (0 if plain else 3))
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

    def test_bootstrap_entry_and_restore_failures_preserve_cause_and_registry(self):
        def original(*args, **kwargs): raise AssertionError('guard body is forbidden')
        for primary_kind in (RuntimeError, KeyboardInterrupt):
            for secondary_kind in (MemoryError, KeyboardInterrupt):
                primary = primary_kind('body first cause'); cause = ValueError('explicit cause'); primary.__cause__ = cause
                secondary = secondary_kind('helper restore'); actions = []
                class Checks:
                    def __init__(self): self.value = original; self.fail = False
                    @property
                    def run_with_heartbeat(self): return self.value
                    @run_with_heartbeat.setter
                    def run_with_heartbeat(self, value):
                        actions.append('restore' if value is original else 'install')
                        if self.fail and value is original:
                            self.fail = False; raise secondary
                        self.value = value
                checks = Checks(); registry = [(checks, original, gate.function_seal(original))]
                snapshot = tuple(registry); pins = SimpleNamespace(guards=registry)
                with self.assertRaises(primary_kind) as raised:
                    with gate.bootstrap_dispatch(checks, SimpleNamespace(conservation=pins)):
                        checks.fail = True; raise primary
                self.assertIs(raised.exception, primary); self.assertIs(primary.__cause__, cause)
                self.assertIs(checks.value, original); self.assertIs(pins.guards, registry)
                self.assertEqual(tuple(registry), snapshot); self.assertEqual(actions, ['install', 'restore', 'restore'])
                self.assertEqual(primary.bounds_secondary_failures[0], {'stage': 'restore-bootstrap-helper', 'type': secondary_kind.__name__})
        for primary_kind in (MemoryError, KeyboardInterrupt):
            primary = primary_kind('setup after mutation'); entered = []
            class EntryChecks:
                def __init__(self): self.value = original
                @property
                def run_with_heartbeat(self): return self.value
                @run_with_heartbeat.setter
                def run_with_heartbeat(self, value):
                    self.value = value
                    if value is not original: raise primary
            checks = EntryChecks(); registry = [(checks, original, gate.function_seal(original))]
            snapshot = tuple(registry); pins = SimpleNamespace(guards=registry)
            with self.assertRaises(primary_kind) as raised:
                with gate.bootstrap_dispatch(checks, SimpleNamespace(conservation=pins)): entered.append(True)
            self.assertIs(raised.exception, primary); self.assertFalse(entered)
            self.assertIs(checks.value, original); self.assertEqual(tuple(registry), snapshot)
        tree = ast.parse((ROOT / 'tests/v4_word_bounds_codegen.py').read_bytes())
        bootstrap = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'bootstrap_dispatch')
        line = next(node.lineno for node in ast.walk(bootstrap) if isinstance(node, ast.Assign)
                    and isinstance(node.value, ast.ListComp)
                    and any(isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name)
                            and target.value.id == 'registry' for target in node.targets))
        function = gate.bootstrap_dispatch.__wrapped__
        for primary_kind in (MemoryError, KeyboardInterrupt):
            primary = primary_kind('setup after helper install'); checks = SimpleNamespace(run_with_heartbeat=original)
            registry = [(checks, original, gate.function_seal(original))]; snapshot = tuple(registry)
            pins = SimpleNamespace(guards=registry); entered = []
            def trace(frame, event, arg):
                if event == 'line' and frame.f_code is function.__code__ and frame.f_lineno == line: raise primary
                return trace
            previous_trace = sys.gettrace()
            sys.settrace(trace)
            try:
                with self.assertRaises(primary_kind) as raised:
                    with gate.bootstrap_dispatch(checks, SimpleNamespace(conservation=pins)): entered.append(True)
            finally: sys.settrace(previous_trace)
            self.assertIs(raised.exception, primary); self.assertFalse(entered)
            self.assertIs(checks.run_with_heartbeat, original); self.assertEqual(tuple(registry), snapshot)

    def test_bootstrap_registry_restore_is_independent_and_failure_blocks_success(self):
        def original(*args, **kwargs): raise AssertionError('guard body is forbidden')
        for secondary_kind in (MemoryError, KeyboardInterrupt):
            checks = SimpleNamespace(run_with_heartbeat=original); primary = secondary_kind('registry restore')
            class Registry(list):
                fail = False
                def __setitem__(self, key, value):
                    if self.fail:
                        self.fail = False; raise primary
                    return super().__setitem__(key, value)
            registry = Registry([(checks, original, gate.function_seal(original))]); snapshot = tuple(registry)
            pins = SimpleNamespace(guards=registry)
            with self.assertRaises(secondary_kind) as raised:
                with gate.bootstrap_dispatch(checks, SimpleNamespace(conservation=pins)): registry.fail = True
            self.assertIs(raised.exception, primary); self.assertIs(checks.run_with_heartbeat, original)
            self.assertEqual(tuple(registry), snapshot)

    def test_run_gate_runtime_root_entry_and_restore_preserve_first_cause(self):
        with tempfile.TemporaryDirectory() as temporary:
            for primary_kind in (RuntimeError, KeyboardInterrupt):
                for secondary_kind in (MemoryError, KeyboardInterrupt):
                    folder = Path(temporary) / (primary_kind.__name__ + secondary_kind.__name__); folder.mkdir()
                    old_root = folder / 'caller-root'; primary = primary_kind('pure transpiler first cause')
                    cause = ValueError('explicit cause'); primary.__cause__ = cause; secondary = secondary_kind('root restoration')
                    events = []
                    class Checks(SimpleNamespace):
                        def __setattr__(self, name, value):
                            if name == 'RUNTIME_BUILD_ROOT' and self.__dict__.get('fail_restore') and value == old_root:
                                self.fail_restore = False; events.append('restore-failed'); raise secondary
                            super().__setattr__(name, value)
                    def transpile(*args): checks.fail_restore = True; events.append('pure-transpiler'); raise primary
                    def guard(argv, **kwargs): events.append('inert-identity'); return result('inert identity\n')
                    checks = Checks(TESTS_ROOT=FIXTURE.parent, RUNTIME_ROOT=ROOT / 'freakc/runtime', RUNTIME_BUILD_ROOT=old_root,
                                    run_with_heartbeat=guard, read_text=lambda path: path.read_text(),
                                    check_flattened_crates=lambda: 'inert', transpile_fixture=transpile)
                    pins = SimpleNamespace(frozen=ROOT, clang=Path('INERT-NOT-EXECUTED'), seal_build=lambda build: None,
                                           bind=lambda *args: None, check=lambda: None, track=lambda *args, **kwargs: None,
                                           guards=[], final_pins=lambda: None)
                    build = SimpleNamespace(checks=checks, host_target=lambda: 'inert-target',
                                            SOURCE_NAMES=gate.literal_assignment(ROOT / 'freakc/v4_native_runtime.py', 'SOURCE_NAMES'))
                    with patch.object(gate, 'Conservation', return_value=pins), patch.object(gate, 'load_build', return_value=build), \
                            self.assertRaises(primary_kind) as raised:
                        gate.run_gate(SimpleNamespace(work=folder, clang='INERT-NOT-EXECUTED', plain=True), {})
                    self.assertIs(raised.exception, primary); self.assertIs(primary.__cause__, cause)
                    self.assertEqual(checks.RUNTIME_BUILD_ROOT, old_root)
                    self.assertEqual(events, ['inert-identity', 'pure-transpiler', 'restore-failed'])
                    self.assertEqual(primary.bounds_secondary_failures[0], {'stage': 'restore-runtime-root', 'type': secondary_kind.__name__})
            for primary_kind in (MemoryError, KeyboardInterrupt):
                primary = primary_kind('root entry after mutation'); entered = []
                class EntryChecks:
                    def __init__(self): self.value = 'caller-root'
                    @property
                    def RUNTIME_BUILD_ROOT(self): return self.value
                    @RUNTIME_BUILD_ROOT.setter
                    def RUNTIME_BUILD_ROOT(self, value):
                        self.value = value
                        if value == 'temporary-root': raise primary
                checks = EntryChecks()
                with self.assertRaises(primary_kind) as raised:
                    with gate.temporary_runtime_root(checks, 'temporary-root'): entered.append(True)
                self.assertIs(raised.exception, primary); self.assertFalse(entered)
                self.assertEqual(checks.RUNTIME_BUILD_ROOT, 'caller-root')

    def test_consumed_defaults_descriptors_and_data_are_qualified_before_dispatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            for key, changed in (('timeout', None), ('memory', 512)):
                folder = Path(temporary) / key; folder.mkdir(); tool = folder / 'inert-clang'; tool.write_bytes(b'never execute')
                calls = []
                def guard(argv, **kwargs): calls.append(kwargs); return result()
                pins = gate.Conservation(SimpleNamespace(work=folder, clang=str(tool)), {})
                runner = gate.Runner(SimpleNamespace(run_with_heartbeat=guard), folder, pins)
                defaults = gate.Runner.run.__kwdefaults__; original = defaults[key]
                try:
                    defaults[key] = changed
                    with self.assertRaises(gate.GateError): pins.check()
                    with self.assertRaises(gate.GateError): runner.run(['INERT-NOT-EXECUTED'], 'emit case 0')
                    self.assertFalse(calls)
                finally: defaults[key] = original
                pins.check()
                code = gate.Runner.run.__code__
                try:
                    gate.Runner.run.__code__ = code.replace()
                    with self.assertRaises(gate.GateError): pins.check()
                finally: gate.Runner.run.__code__ = code
                pins.check()
                class EqualCallable:
                    __code__ = gate.Runner.run.__code__
                    def __eq__(self, other): raise AssertionError('arbitrary equality must not run')
                with patch.object(gate.Runner, 'run', EqualCallable()), self.assertRaises(gate.GateError): pins.check()
                holder = SimpleNamespace(config={'seconds': 60}); pins.bind(holder, ('config',))
                holder.config['seconds'] = None
                with self.assertRaises(gate.GateError): pins.check()
                holder.config['seconds'] = 60; pins.check()
                def helper(seconds=60): return seconds
                owner = SimpleNamespace(helper=helper); pins.bind(owner, ('helper',))
                try:
                    helper.__defaults__ = (None,)
                    with self.assertRaises(gate.GateError): pins.check()
                finally: helper.__defaults__ = (60,)
                pins.check()

    def test_context_restore_entry_failures_recover_independent_caller_state(self):
        for context_name in ('bootstrap_dispatch', 'temporary_runtime_root'):
            for primary_kind in (RuntimeError, KeyboardInterrupt, None):
                for secondary_kind in (MemoryError, KeyboardInterrupt):
                    def original(*args, **kwargs): raise AssertionError('guard body is forbidden')
                    checks = SimpleNamespace(run_with_heartbeat=original, RUNTIME_BUILD_ROOT='caller-root')
                    registry = [(checks, original, gate.function_seal(original))]; snapshot = tuple(registry)
                    pins = SimpleNamespace(guards=registry); runner = SimpleNamespace(conservation=pins)
                    primary = primary_kind('body first cause') if primary_kind else None
                    cause = ValueError('explicit cause')
                    if primary is not None: primary.__cause__ = cause
                    secondary = secondary_kind('restore function entry'); triggered = []
                    function = getattr(gate, context_name).__wrapped__
                    def trace(frame, event, arg):
                        if event == 'call' and frame.f_code.co_filename == function.__code__.co_filename \
                                and frame.f_code.co_qualname == context_name + '.<locals>.restore':
                            triggered.append(True); raise secondary
                        return trace
                    previous_trace = sys.gettrace(); sys.settrace(trace)
                    try:
                        expected = primary if primary is not None else secondary
                        with self.assertRaises(type(expected)) as raised:
                            context = gate.bootstrap_dispatch(checks, runner) if context_name == 'bootstrap_dispatch' \
                                else gate.temporary_runtime_root(checks, 'temporary-root')
                            with context:
                                if primary is not None: raise primary
                    finally: sys.settrace(previous_trace)
                    self.assertEqual(triggered, [True]); self.assertIs(raised.exception, expected)
                    if primary is not None: self.assertIs(primary.__cause__, cause)
                    self.assertIs(checks.run_with_heartbeat, original); self.assertIs(pins.guards, registry)
                    self.assertEqual(tuple(registry), snapshot); self.assertEqual(checks.RUNTIME_BUILD_ROOT, 'caller-root')
                    stage = 'restore-bootstrap-dispatch' if context_name == 'bootstrap_dispatch' else 'restore-runtime-dispatch'
                    self.assertEqual(expected.bounds_secondary_failures[0], {'stage': stage, 'type': secondary_kind.__name__})

    def test_consumed_context_generator_and_closure_leaves_are_sealed_before_dispatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary); tool = folder / 'inert-clang'; tool.write_bytes(b'never execute')
            source = folder / 'inert.fk.c'; source.write_bytes(b'inert generated C; never compiled')
            calls = []
            def guard(argv, **kwargs): calls.append(kwargs); return result()
            pins = gate.Conservation(SimpleNamespace(work=folder, clang=str(tool)), {})
            checks = SimpleNamespace(run_with_heartbeat=guard); runner = gate.Runner(checks, folder, pins)
            wrapper = gate.bootstrap_dispatch; leaf = wrapper.__wrapped__; original_code = leaf.__code__
            nested = next(code for code in original_code.co_consts if isinstance(code, gate.types.CodeType) and code.co_name == 'bounded')
            self.assertIn(120, nested.co_consts)
            replacement = nested.replace(co_consts=tuple(None if type(value) is int and value == 120 else value for value in nested.co_consts))
            mutated = original_code.replace(co_consts=tuple(replacement if value is nested else value for value in original_code.co_consts))
            try:
                leaf.__code__ = mutated
                with self.assertRaises(gate.GateError): pins.check()
                with self.assertRaises(gate.GateError):
                    with gate.bootstrap_dispatch(checks, runner):
                        checks.run_with_heartbeat([str(source)], label='runtime compile: inert', memory_limit_mb=1024)
                self.assertFalse(calls); self.assertIs(checks.run_with_heartbeat, guard)
            finally: leaf.__code__ = original_code
            pins.check()
            original_defaults = leaf.__defaults__
            try:
                leaf.__defaults__ = (None,)
                with self.assertRaises(gate.GateError): pins.check()
            finally: leaf.__defaults__ = original_defaults
            pins.check()
            def different_leaf(*args, **kwargs): raise AssertionError('foreign leaf must not run')
            try:
                wrapper.__wrapped__ = different_leaf
                with self.assertRaises(gate.GateError): pins.check()
            finally: wrapper.__wrapped__ = leaf
            pins.check()
            cell = next(cell for cell in wrapper.__closure__ if cell.cell_contents is leaf)
            try:
                cell.cell_contents = different_leaf
                self.assertIs(wrapper.__wrapped__, leaf)
                with self.assertRaises(gate.GateError): pins.check()
            finally: cell.cell_contents = leaf
            pins.check(); self.assertFalse(calls)

    def test_evidence_dispatch_entry_failures_cannot_skip_mandatory_restoration(self):
        for context_name in ('bootstrap_dispatch', 'temporary_runtime_root'):
            for primary_kind in (RuntimeError, KeyboardInterrupt, None):
                for secondary_kind in (MemoryError, KeyboardInterrupt):
                    def original(*args, **kwargs): raise AssertionError('guard body is forbidden')
                    checks = SimpleNamespace(run_with_heartbeat=original, RUNTIME_BUILD_ROOT='caller-root')
                    registry = [(checks, original, gate.function_seal(original))]; snapshot = tuple(registry)
                    pins = SimpleNamespace(guards=registry); runner = SimpleNamespace(conservation=pins)
                    primary = primary_kind('body first cause') if primary_kind else None
                    cause = ValueError('explicit cause')
                    if primary is not None: primary.__cause__ = cause
                    secondary = secondary_kind('evidence dispatch entry'); triggered = []
                    stage = 'restore-bootstrap-dispatch' if context_name == 'bootstrap_dispatch' else 'restore-runtime-dispatch'
                    def trace(frame, event, arg):
                        if event == 'call' and frame.f_code is gate.Evidence.attempt.__code__ and frame.f_locals.get('stage') == stage:
                            triggered.append(True); raise secondary
                        return trace
                    previous_trace = sys.gettrace(); sys.settrace(trace)
                    try:
                        expected = primary if primary is not None else secondary
                        with self.assertRaises(type(expected)) as raised:
                            context = gate.bootstrap_dispatch(checks, runner) if context_name == 'bootstrap_dispatch' \
                                else gate.temporary_runtime_root(checks, 'temporary-root')
                            with context:
                                if primary is not None: raise primary
                    finally: sys.settrace(previous_trace)
                    self.assertEqual(triggered, [True]); self.assertIs(raised.exception, expected)
                    if primary is not None: self.assertIs(primary.__cause__, cause)
                    self.assertIs(checks.run_with_heartbeat, original); self.assertIs(pins.guards, registry)
                    self.assertEqual(tuple(registry), snapshot); self.assertEqual(checks.RUNTIME_BUILD_ROOT, 'caller-root')
                    self.assertEqual(expected.bounds_secondary_failures[0], {'stage': stage, 'type': secondary_kind.__name__})

    def test_reporting_entry_failure_follows_restoration_and_preserves_first_error(self):
        for context_name in ('bootstrap_dispatch', 'temporary_runtime_root'):
            for primary_kind in (RuntimeError, KeyboardInterrupt, None):
                for secondary_kind in (MemoryError, KeyboardInterrupt):
                    def original(*args, **kwargs): raise AssertionError('guard body is forbidden')
                    primary = primary_kind('body first cause') if primary_kind else None
                    cause = ValueError('explicit cause')
                    if primary is not None: primary.__cause__ = cause
                    cleanup_error = MemoryError('first restoration error'); report_error = secondary_kind('report entry')
                    target_name = 'run_with_heartbeat' if context_name == 'bootstrap_dispatch' else 'RUNTIME_BUILD_ROOT'
                    target_value = original if context_name == 'bootstrap_dispatch' else 'caller-root'
                    class Checks(SimpleNamespace):
                        def __setattr__(self, name, value):
                            if name == target_name and getattr(self, 'fail', False) and value is target_value:
                                self.fail = False; raise cleanup_error
                            super().__setattr__(name, value)
                    checks = Checks(run_with_heartbeat=original, RUNTIME_BUILD_ROOT='caller-root', fail=False)
                    registry = [(checks, original, gate.function_seal(original))]; snapshot = tuple(registry)
                    pins = SimpleNamespace(guards=registry); runner = SimpleNamespace(conservation=pins); triggered = []
                    def trace(frame, event, arg):
                        if event == 'call' and frame.f_code is gate.Evidence.attach.__code__:
                            self.assertIs(checks.run_with_heartbeat, original); self.assertIs(pins.guards, registry)
                            self.assertEqual(tuple(registry), snapshot); self.assertEqual(checks.RUNTIME_BUILD_ROOT, 'caller-root')
                            triggered.append(True); raise report_error
                        return trace
                    previous_trace = sys.gettrace(); sys.settrace(trace)
                    try:
                        expected = primary if primary is not None else cleanup_error
                        with self.assertRaises(type(expected)) as raised:
                            context = gate.bootstrap_dispatch(checks, runner) if context_name == 'bootstrap_dispatch' \
                                else gate.temporary_runtime_root(checks, 'temporary-root')
                            with context:
                                if primary is not None: raise primary
                                checks.fail = True
                    finally: sys.settrace(previous_trace)
                    self.assertEqual(triggered, [True]); self.assertIs(raised.exception, expected)
                    if primary is not None: self.assertIs(primary.__cause__, cause)
                    self.assertIs(checks.run_with_heartbeat, original); self.assertIs(pins.guards, registry)
                    self.assertEqual(tuple(registry), snapshot); self.assertEqual(checks.RUNTIME_BUILD_ROOT, 'caller-root')


if __name__ == '__main__': unittest.main()
