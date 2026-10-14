"""Pure adversarial controls for the lowercase native/compiler oracles."""
import ast
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("lower_gate", Path(__file__).with_name("v4_word_lower_codegen.py"))
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class WordLowerOracle(unittest.TestCase):
    def result(self, stdout, *, code=0, stderr=""):
        return SimpleNamespace(returncode=code, stdout=stdout, stderr=stderr)

    def module(self):
        return gate.PREFIX + "@@LLVM-MODULE-BEGIN\ncall i64 @freak_v4_word_to_lower(i64 %value)\n@@LLVM-MODULE-END\n"

    def test_exact_nul_unicode_output(self):
        self.assertEqual(gate.assert_native_output(self.result(gate.EXPECTED), gate.EXPECTED, platform="linux"), gate.EXPECTED)

    def test_wrong_exit_and_signal(self):
        for code in (1, -11, 85, 86):
            with self.subTest(code=code), self.assertRaises(RuntimeError):
                gate.assert_native_output(self.result(gate.EXPECTED, code=code), gate.EXPECTED, platform="linux")

    def test_sanitizer_audit_extra_output(self):
        for stderr in ("AddressSanitizer error\n", "runtime ownership audit\n", "undefined behavior\n"):
            with self.subTest(stderr=stderr), self.assertRaises(RuntimeError):
                gate.assert_native_output(self.result(gate.EXPECTED, stderr=stderr), gate.EXPECTED, platform="linux")
        for stdout in (gate.EXPECTED + "extra\n", gate.EXPECTED.replace("\0", ""), gate.EXPECTED.replace("\u0307", "")):
            with self.subTest(stdout=stdout), self.assertRaises(RuntimeError):
                gate.assert_native_output(self.result(stdout), gate.EXPECTED, platform="linux")

    def test_posix_crlf_is_not_hidden(self):
        for platform in ("linux", "darwin"):
            with self.subTest(platform=platform), self.assertRaises(RuntimeError):
                gate.assert_native_output(self.result(gate.EXPECTED.replace("\n", "\r\n")), gate.EXPECTED, platform=platform)

    def test_windows_text_newlines_only(self):
        gate.assert_native_output(self.result(gate.EXPECTED.replace("\n", "\r\n")), gate.EXPECTED, platform="win32")
        with self.assertRaises(RuntimeError):
            gate.assert_native_output(self.result(gate.EXPECTED + "\r"), gate.EXPECTED, platform="win32")

    def test_compiler_exact_protocol(self):
        self.assertIn("@freak_v4_word_to_lower", gate.extract_module(self.result(self.module()), platform="linux"))

    def test_compiler_failure_and_forged_protocol(self):
        for stdout in (self.module() + "extra\n", self.module().replace("old-seal=true", "old-seal=false"),
                       self.module().replace("call i64 @freak_v4_word_to_lower", "declare i64 @freak_v4_word_to_lower"),
                       self.module().replace("@@LLVM-MODULE-BEGIN\n", "@@LLVM-MODULE-BEGIN\n@@LLVM-MODULE-BEGIN\n"),
                       self.module().replace("\n", "\r\n")):
            with self.subTest(stdout=stdout), self.assertRaises(RuntimeError):
                gate.extract_module(self.result(stdout), platform="linux")
        for code, stderr in ((1, ""), (0, "audit\n")):
            with self.subTest(code=code), self.assertRaises(RuntimeError):
                gate.extract_module(self.result(self.module(), code=code, stderr=stderr))

    def test_complete_matrix_requires_both_audits(self):
        rows = [{"optimization": opt, "status": "pass", "ownership_audits": ["C", "LLVM"]} for opt in gate.OPTIMIZATIONS]
        gate.assert_complete(rows)
        for bad in (rows[:-1], rows + rows[:1], [rows[0]] * 3,
                    [dict(row, ownership_audits=["C"]) for row in rows],
                    [dict(row, status="skip") for row in rows]):
            with self.subTest(bad=bad), self.assertRaises(RuntimeError):
                gate.assert_complete(bad)


    def test_windows_link_selects_lld_and_conserves_every_original_argument(self):
        clang = r"C:\Program Files\LLVM\bin\clang.exe"
        llvm = Path("module é 日本 ' $ &.ll")
        binary = Path("word_lowercase-O0.exe")
        original = gate.build.native_link_command(clang, llvm, binary)
        selected = gate.lowercase_link_command(clang, llvm, binary, platform="win32")
        self.assertEqual(selected, original + ["-fuse-ld=lld"])
        self.assertEqual(selected.count("-fuse-ld=lld"), 1)

    def test_non_windows_link_command_is_exactly_unchanged(self):
        llvm, binary = Path("word_lowercase.ll"), Path("word_lowercase.native")
        original = gate.build.native_link_command("clang", llvm, binary)
        for platform in ("linux", "darwin", "freebsd"):
            with self.subTest(platform=platform):
                self.assertEqual(gate.lowercase_link_command("clang", llvm, binary,
                                                            platform=platform), original)

    def test_actual_link_call_uses_running_platform_selection(self):
        source = Path(gate.__file__).read_text(encoding="utf-8")
        main = next(node for node in ast.parse(source).body
                    if isinstance(node, ast.FunctionDef) and node.name == "main")
        assignment = next(node for node in ast.walk(main)
                          if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)
                          and isinstance(node.value.func, ast.Name)
                          and node.value.func.id == "lowercase_link_command")
        expression = compile(ast.Expression(assignment.value), "actual-native-link-call", "eval")
        llvm, binary = Path("word_lowercase.ll"), Path("word_lowercase.exe")
        for platform in ("linux", "darwin", "win32"):
            with self.subTest(platform=platform), patch.object(gate.sys, "platform", platform):
                original = gate.build.native_link_command("clang", llvm, binary)
                selected = eval(expression, {"lowercase_link_command": gate.lowercase_link_command,
                                "args": SimpleNamespace(clang="clang"), "llvm": llvm, "binary": binary})
                self.assertEqual(selected, original + (["-fuse-ld=lld"] if platform == "win32" else []))

    def test_actual_link_guard_still_rejects_all_nonempty_output_and_failure(self):
        main = next(node for node in ast.parse(Path(gate.__file__).read_text(encoding="utf-8")).body
                    if isinstance(node, ast.FunctionDef) and node.name == "main")
        guard = next(node for node in ast.walk(main)
                     if isinstance(node, ast.If) and "linked.returncode" in ast.unparse(node.test))
        program = compile(ast.fix_missing_locations(ast.Module(body=[guard], type_ignores=[])),
                          "actual-native-link-guard", "exec")
        exec(program, {"linked": self.result(""), "optimization": 0})
        notice = "   Creating library word_lowercase-O0.lib and object word_lowercase-O0.exp\r\n"
        for actual in (self.result("", code=1), self.result("", code=-11),
                       self.result("", code=86), self.result(notice), self.result("extra\n"),
                       self.result("", stderr="warning\n"),
                       self.result("", stderr="lld-link: error: undefined symbol\n")):
            with self.subTest(actual=actual), self.assertRaises(RuntimeError):
                exec(program, {"linked": actual, "optimization": 0})


if __name__ == "__main__":
    unittest.main()
