"""Module framing accepts platform text streams without changing payloads."""
import importlib.util
import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("llvm_framing_guard", ROOT / "src/compiler/v4/check_v4.py")
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)
BUILD_SPEC = importlib.util.spec_from_file_location("v4_build_framing_guard", ROOT / "src/compiler/v4/build_v4.py")
build = importlib.util.module_from_spec(BUILD_SPEC)
with patch.dict(sys.modules, {"check_v4": guard}):
    BUILD_SPEC.loader.exec_module(build)


class LlvmModuleFraming(unittest.TestCase):
    def test_lf_and_crlf_preserve_module_bytes(self):
        for newline in ("\n", "\r\n"):
            with self.subTest(newline=repr(newline)):
                module = 'define i32 @main() { ret i32 0 }' + newline + '@s = constant [2 x i8] c"\\0A\\00"'
                output = "@@LLVM-MODULE-BEGIN" + newline + module + newline + "@@LLVM-MODULE-END" + newline
                self.assertEqual(guard.extract_llvm_modules(output), [module])

    def test_two_modules_keep_count_and_order(self):
        output = ("diagnostics=0\r\n@@LLVM-MODULE-BEGIN\r\nfirst\r\n@@LLVM-MODULE-END\r\n"
                  "@@LLVM-MODULE-BEGIN\r\nsecond\r\n@@LLVM-MODULE-END\r\n")
        self.assertEqual(guard.extract_llvm_modules(output), ["first", "second"])

    def test_incomplete_or_embedded_markers_are_not_frames(self):
        for output in ("@@LLVM-MODULE-BEGIN\nmissing end\n",
                       "noise@@LLVM-MODULE-BEGIN\nmodule\n@@LLVM-MODULE-END\n",
                       "@@LLVM-MODULE-BEGIN\nmodule\n@@LLVM-MODULE-ENDnoise\n"):
            with self.subTest(output=output):
                self.assertEqual(guard.extract_llvm_modules(output), [])

    def test_cli_accepts_lf_and_crlf_without_changing_payload(self):
        for newline in ("\n", "\r\n"):
            with self.subTest(newline=repr(newline)):
                module = 'target triple = "x86_64-w64-windows-gnu"' + newline + 'define i32 @main() { ret i32 0 }' + newline
                result = subprocess.CompletedProcess([], 0, "v4-errors=0" + newline + "@@V4-MODULE" + newline + module, "")
                with patch.object(build.checks, "run_with_heartbeat", return_value=result), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(build.emit_module(Path("compiler"), Path("source.fk"), "target"), module)

    def test_cli_rejects_missing_duplicate_embedded_or_failed_frames(self):
        for status, output in ((0, "missing\n"),
                               (0, "@@V4-MODULE\nfirst\n@@V4-MODULE\nsecond\n"),
                               (0, "noise@@V4-MODULE\nmodule\n"),
                               (1, "@@V4-MODULE\r\nmodule\r\n")):
            with self.subTest(status=status, output=output):
                result = subprocess.CompletedProcess([], status, output, "")
                with patch.object(build.checks, "run_with_heartbeat", return_value=result), self.assertRaises(RuntimeError):
                    build.emit_module(Path("compiler"), Path("source.fk"), "target")

    def test_cli_writes_captured_crlf_bytes_once(self):
        module = 'define i32 @main() { ret i32 0 }\r\n'
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source.fk"
            output = Path(temporary) / "module.ll"
            source.write_text("task main() -> int { give back 0 }")
            arguments = ["build_v4.py", str(source), "-o", str(output), "--emit-llvm", "--target", "target"]
            with patch.object(sys, "argv", arguments), patch.object(build.shutil, "which", return_value="clang"), \
                    patch.object(build, "bootstrap", return_value=Path("compiler")), \
                    patch.object(build, "emit_module", return_value=module), \
                    patch.object(build.checks, "run_with_heartbeat", return_value=subprocess.CompletedProcess([], 0, "", "")), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(build.main(), 0)
            self.assertEqual(output.read_bytes(), module.encode("utf-8"))


if __name__ == "__main__":
    unittest.main()
