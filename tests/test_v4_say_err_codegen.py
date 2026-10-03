"""Process-free adversarial controls for sized stderr and its evidence gate."""
from __future__ import annotations

from contextlib import ExitStack, redirect_stderr
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
SPEC = importlib.util.spec_from_file_location("say_err_gate", ROOT / "tests/v4_say_err_codegen.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)
FIXTURE = ROOT / "src/compiler/v4/tests/say_err_execute_smoke.fk"


def result(stdout="", stderr="", status=0):
    return subprocess.CompletedProcess(["mock"], status, stdout, stderr)


def module(case):
    instructions = "  call void @freak_v4_word_say_err(i64 %w)\n" * gate.CALL_COUNTS[case]
    if case == 2:
        instructions += "  call void @say_err(i64 %w)\n"
    return "define i32 @main(i32 %argc, ptr %argv) {\n" + instructions + "  ret i32 0\n}\n"


def compiler(case, body=None):
    return result(gate.prefix(case) + gate.BEGIN + (module(case) if body is None else body) + gate.END)


def complete_report(sanitize=True):
    rows = []
    for case, (stdout, stderr) in enumerate(gate.OUTPUTS):
        for opt in gate.OPTS:
            rows.append({"case": case, "optimization": opt, "status": "pass", "exit": 0,
                         "stdout_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
                         "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest()})
    controls = [{"name": f"audit-{kind}-O{opt}", "status": "pass"}
                for kind in ("C", "LLVM") for opt in gate.OPTS]
    if sanitize:
        controls += [{"name": "sanitizer-" + kind, "status": "pass"} for kind in ("address", "undefined")]
    return {"sanitizers": sanitize, "ownership_audits": ["C", "LLVM"], "controls": controls,
            "programs": rows, "compiler_contracts": [{"case": case, "status": "pass"} for case in range(3)],
            "build_flags": {str(opt): [f"-O{opt}", *gate.AUDIT_FLAGS, *(gate.SANITIZER_FLAGS if sanitize else ())]
                            for opt in gate.OPTS},
            "input_hashes": {"fixture": "same"}, "final_input_hashes": {"fixture": "same"}}


class SayErrOracles(unittest.TestCase):
    def test_full_sized_outputs_on_linux_macos_windows(self):
        for platform in ("linux", "darwin", "win32"):
            for case, (stdout, stderr) in enumerate(gate.OUTPUTS):
                with self.subTest(platform=platform, case=case):
                    gate.exact_program(result(stdout, stderr), case, platform=platform)

    def test_windows_crlf_only_and_posix_cr_is_visible(self):
        stdout, stderr = gate.OUTPUTS[0]
        converted = result(stdout.replace("\n", "\r\n"), stderr.replace("\n", "\r\n"))
        gate.exact_program(converted, 0, platform="win32")
        for platform in ("linux", "darwin"):
            with self.subTest(platform=platform), self.assertRaises(gate.GateError):
                gate.exact_program(converted, 0, platform=platform)
        with self.assertRaises(gate.GateError):
            gate.exact_program(result(stdout, stderr + "\r"), 0, platform="win32")

    def test_separate_channels_receiver_once_and_exact_bytes(self):
        stdout, stderr = gate.OUTPUTS[1]
        impostors = [result(stderr, stdout), result(stdout + "receiver:LEFT\n", stderr),
                     result(stdout.replace("receiver:LEFT\n", ""), stderr),
                     result(stdout, stderr.replace("\0", "")),
                     result(stdout.replace("é", "e"), stderr),
                     result(stdout, stderr.replace("LEFTRIGHT", "RIGHTLEFT")),
                     result(stdout, stderr + "FREAK: LLVM ownership audit found 1 unreleased word allocation(s)\n")]
        impostors += [result(stdout, stderr, code) for code in (1, 3, 85, 86, 87, 88, -6, -11)]
        for impostor in impostors:
            with self.subTest(impostor=impostor), self.assertRaises(gate.GateError):
                gate.exact_program(impostor, 1)

    def test_compiler_requires_real_calls_and_complete_protocol(self):
        for case in range(3):
            self.assertEqual(gate.extract_module(compiler(case), case), module(case))
        clean = compiler(0)
        faults = [result(clean.stdout + "extra\n"), result(clean.stdout, "audit\n"),
                  result(clean.stdout, status=1), result(clean.stdout.replace("borrowed=true", "borrowed=false")),
                  result(clean.stdout.replace(gate.BEGIN, gate.BEGIN + gate.BEGIN)),
                  compiler(0, module(0).replace("  call void", "  ; call void")),
                  compiler(0, module(0).replace("  call void", "declare void")),
                  compiler(0, module(0).replace("  ret i32", "  call void @freak_v4_word_say_err(i64 %w)\n  ret i32")),
                  compiler(0, module(0).replace("define i32 @main", "; define i32 @main")),
                  result(clean.stdout.replace("\n", "\r\n"))]
        for malformed in faults:
            with self.subTest(malformed=malformed), self.assertRaises(gate.GateError):
                gate.extract_module(malformed, 0, platform="linux")
        gate.extract_module(result(clean.stdout.replace("\n", "\r\n")), 0, platform="win32")
        with self.assertRaises(gate.GateError):
            gate.extract_module(compiler(2, module(2).replace("  call void @say_err", "  ; call void @say_err")), 2)

    def test_fixture_table_is_closed_and_receiver_borrow_is_observable(self):
        text = FIXTURE.read_text(encoding="utf-8")
        sources = gate.fixture_sources(text)
        self.assertEqual(len(sources), 3)
        self.assertIn('report(lend value)', sources[0])
        self.assertIn('say value\n early()', sources[0])
        self.assertIn('receiver("LEFT") + receiver("RIGHT")', sources[1])
        self.assertIn('task say_err(value: word)', sources[2])
        faults = [text.replace("if case_id == 2", "if case_id == 1", 1),
                  "\n".join(line for line in text.splitlines() if not line.strip().startswith("if case_id == 1 { give back")),
                  text.replace("chr(123)", "chr(0)", 1),
                  text.replace("chr(123)", "__import__('os').system('false')", 1)]
        for malformed in faults:
            with self.assertRaises(gate.GateError):
                gate.fixture_sources(malformed)

    def test_report_missing_duplicate_channel_flags_or_controls_fail(self):
        for sanitize in (False, True):
            valid = complete_report(sanitize)
            gate.validate_report(valid, sanitize)
            mutations = []
            missing = deepcopy(valid); missing["programs"].pop(); mutations.append(missing)
            duplicate = deepcopy(valid); duplicate["programs"][-1] = duplicate["programs"][0]; mutations.append(duplicate)
            noise = deepcopy(valid); noise["programs"][0]["stderr_sha256"] = "lost-nul"; mutations.append(noise)
            swapped = deepcopy(valid); swapped["programs"][0]["stdout_sha256"] = swapped["programs"][0]["stderr_sha256"]; mutations.append(swapped)
            failed = deepcopy(valid); failed["programs"][0]["exit"] = 86; mutations.append(failed)
            skipped = deepcopy(valid); skipped["compiler_contracts"][0]["status"] = "skip"; mutations.append(skipped)
            compiler_missing = deepcopy(valid); compiler_missing["compiler_contracts"].pop(); mutations.append(compiler_missing)
            audit = deepcopy(valid); audit["build_flags"]["2"].remove(gate.AUDIT_FLAGS[0]); mutations.append(audit)
            opt = deepcopy(valid); opt["build_flags"]["3"] += ["-O0"]; mutations.append(opt)
            no_control = deepcopy(valid); no_control["controls"].pop(); mutations.append(no_control)
            duplicate_control = deepcopy(valid); duplicate_control["controls"][-1] = duplicate_control["controls"][0]; mutations.append(duplicate_control)
            drift = deepcopy(valid); drift["final_input_hashes"]["fixture"] = "changed"; mutations.append(drift)
            no_inputs = deepcopy(valid); no_inputs.pop("input_hashes"); no_inputs.pop("final_input_hashes"); mutations.append(no_inputs)
            mode = deepcopy(valid); mode["sanitizers"] = not sanitize; mutations.append(mode)
            if sanitize:
                disabled = deepcopy(valid); disabled["build_flags"]["0"].remove(gate.SANITIZER_FLAGS[1]); mutations.append(disabled)
            else:
                hidden = deepcopy(valid); hidden["build_flags"]["0"].append("-fsanitize=address"); mutations.append(hidden)
            for malformed in mutations:
                with self.subTest(sanitize=sanitize, malformed=malformed), self.assertRaises(gate.GateError):
                    gate.validate_report(malformed, sanitize)

    def mock_gate(self, directory, *, plain, broken_control=False):
        from freakc.v4_native_runtime import SOURCE_NAMES
        checks = SimpleNamespace(TESTS_ROOT=FIXTURE.parent, RUNTIME_ROOT=ROOT / "freakc/runtime",
                                 RUNTIME_BUILD_ROOT=directory / "unused",
                                 __file__=str(ROOT / "src/compiler/v4/check_v4.py"),
                                 CRATE_ORDER=("freak_ty",),
                                 crate_path=lambda name: ROOT / "src/compiler/v4/crates" / name / "src/lib.fk",
                                 read_text=lambda path: path.read_text(encoding="utf-8"),
                                 check_flattened_crates=lambda: "mock flattened compiler",
                                 transpile_fixture=lambda flat, fixture: ("mock generated C", False),
                                 runtime_platform_final_link_args=lambda: [])
        def compile_probe(*args):
            binary = checks.RUNTIME_BUILD_ROOT / "compiler.native"
            binary.write_bytes(b"mock compiler")
            return binary, False
        checks.compile_runtime_smoke = compile_probe
        build = SimpleNamespace(checks=checks, SOURCE_NAMES=SOURCE_NAMES, host_target=lambda: "x86_64-unknown-linux-gnu",
                                __file__=str(ROOT / "src/compiler/v4/build_v4.py"))
        commands = []
        class MockRunner:
            def __init__(self, checks, directory):
                pass
            def run(self, command, label, **limits):
                commands.append((command, label, limits))
                if command[-1] == "--version":
                    return result("mock clang identity\n")
                if command[-1] == "--emit":
                    return compiler(int(command[1]))
                if "-o" in command:
                    Path(command[command.index("-o") + 1]).write_bytes(b"mock native binary")
                    return result()
                if "audit-probe" in command[0]:
                    kind = command[1]
                    return result("", f"FREAK: {kind} ownership audit found 1 unreleased word allocation(s)\n", 87 if kind == "C" else 86)
                if "sanitizer-probe" in command[0]:
                    if broken_control:
                        return result(status=88)
                    diagnostic = "ERROR: AddressSanitizer: heap-use-after-free\n" if command[1] == "address" else "runtime error: signed integer overflow\n"
                    return result("", diagnostic, 88)
                case = int(Path(command[0]).name.split(".")[0].split("-")[1])
                return result(*gate.OUTPUTS[case])
        with patch.object(gate, "load_build", return_value=build), patch.object(gate, "Runner", MockRunner):
            code = gate.main(["--clang", "mock-clang", "--work", str(directory), *( ["--plain"] if plain else [])])
        return code, json.loads((directory / "results.json").read_text()), commands

    def test_mocked_complete_plain_and_sanitized_matrix_uses_no_process(self):
        with tempfile.TemporaryDirectory() as temporary, ExitStack() as traps:
            for api in ("Popen", "run", "check_output", "call", "check_call"):
                traps.enter_context(patch.object(subprocess, api, side_effect=AssertionError("actual process is forbidden")))
            for plain in (False, True):
                directory = Path(temporary) / ("plain" if plain else "sanitized")
                code, evidence, commands = self.mock_gate(directory, plain=plain)
                self.assertEqual(code, 0)
                self.assertTrue(evidence["passed"])
                gate.validate_report(evidence, not plain)
                self.assertEqual(len(evidence["programs"]), 9)
                self.assertEqual(len(evidence["controls"]), 6 if plain else 8)
                emits = [row for row in commands if row[1].startswith("emit case")]
                self.assertEqual(len(emits), 3)
                self.assertTrue(all(row[2] == {} for row in emits))  # Runner defaults are the 64MiB/60s SDK gate.
                self.assertEqual(evidence["compiler"]["live_handle_limit"], 1024)

    def test_broken_real_capability_preserves_failed_partial_report(self):
        with tempfile.TemporaryDirectory() as temporary, redirect_stderr(io.StringIO()):
            code, evidence, _ = self.mock_gate(Path(temporary) / "failed", plain=False, broken_control=True)
            self.assertEqual(code, 1)
            self.assertFalse(evidence["passed"])
            self.assertIn("required diagnostic/exit", evidence["error"])
            self.assertEqual(len(evidence["programs"]), 9)
            self.assertEqual(len(evidence["controls"]), 6)

    def test_existing_evidence_directory_is_never_reused(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            marker = directory / "results.json"
            marker.write_bytes(b"historical proof")
            with self.assertRaises(FileExistsError):
                gate.main(["--clang", "mock", "--plain", "--work", str(directory)])
            self.assertEqual(marker.read_bytes(), b"historical proof")

    def test_default_sanitizers_fail_closed_off_linux(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(gate.sys, "platform", "win32"), patch.object(gate.shutil, "which", return_value="mock-clang"), redirect_stderr(io.StringIO()):
            directory = Path(temporary) / "must-not-create"
            with self.assertRaises(SystemExit) as failure:
                gate.main(["--clang", "mock", "--work", str(directory)])
            self.assertEqual(failure.exception.code, 2)
            self.assertFalse(directory.exists())


if __name__ == "__main__":
    unittest.main()
