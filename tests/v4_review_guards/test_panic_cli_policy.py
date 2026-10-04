"""Panic policy reaches module compilation and fails before output mutation."""
import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("panic_cli_checks", ROOT / "src/compiler/v4/check_v4.py")
checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checks)
SPEC = importlib.util.spec_from_file_location("panic_cli_build", ROOT / "src/compiler/v4/build_v4.py")
build = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, {"check_v4": checks}):
    SPEC.loader.exec_module(build)


class PanicCliPolicy(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.source = Path(temporary.name) / "source.fk"
        self.output = Path(temporary.name) / "existing.ll"
        self.source.write_text('task main() -> int { give back 0 }\n')
        self.output.write_bytes(b"existing-output\x00\r\n")

    def test_emit_policy_preserves_default_arguments_and_platform_module_bytes(self):
        for policy in ("unwind", "abort"):
            for newline in ("\n", "\r\n"):
                with self.subTest(policy=policy, newline=newline):
                    module = "define i32 @main() { ret i32 0 }" + newline
                    result = subprocess.CompletedProcess([], 0, "@@V4-MODULE" + newline + module, "")
                    with patch.object(checks, "run_with_heartbeat", return_value=result) as run, \
                            contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(build.emit_module(Path("compiler"), self.source, "target", policy), module)
                    command = ["compiler", str(self.source.resolve()), "target"]
                    if policy == "abort":
                        command.append("abort")
                    run.assert_called_once_with(command, label="V4 compile: source.fk", timeout_seconds=900, memory_limit_mb=2048)

    def test_direct_invalid_policy_never_starts_compilation(self):
        for policy in ("", "ABORT", "catch", "abort\x00", "abort "):
            with self.subTest(policy=policy), patch.object(checks, "run_with_heartbeat") as run, \
                    self.assertRaisesRegex(RuntimeError, "unsupported V4 panic policy"):
                build.emit_module(Path("compiler"), self.source, "target", policy)
            run.assert_not_called()

    def test_cli_invalid_policy_preserves_output_before_tool_lookup(self):
        for policy in ("", "ABORT", "catch", "abort "):
            with self.subTest(policy=policy), \
                    patch.object(sys, "argv", ["build_v4.py", str(self.source), "-o", str(self.output), "--panic=" + policy]), \
                    patch.object(build.shutil, "which") as which, \
                    patch.object(build, "bootstrap") as bootstrap, \
                    patch.object(checks, "run_with_heartbeat") as run, \
                    contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as failure:
                build.main()
            self.assertEqual(failure.exception.code, 2)
            which.assert_not_called()
            bootstrap.assert_not_called()
            run.assert_not_called()
            self.assertEqual(self.output.read_bytes(), b"existing-output\x00\r\n")

    def test_policies_share_compiler_identity_and_reach_module_emission(self):
        for arguments, policy in (([], "unwind"), (["--panic=unwind"], "unwind"), (["--panic=abort"], "abort")):
            with self.subTest(policy=policy, arguments=arguments), \
                    patch.object(sys, "argv", ["build_v4.py", str(self.source), "-o", str(self.output), "--emit-llvm", "--target=target", "--compiler-opt=2", *arguments]), \
                    patch.object(build.shutil, "which", return_value="clang"), \
                    patch.object(build, "bootstrap", return_value=Path("compiler-O2")) as bootstrap, \
                    patch.object(build, "emit_module", return_value="new-module\r\n") as emit, \
                    patch.object(checks, "run_with_heartbeat", return_value=subprocess.CompletedProcess([], 0, "", "")) as run, \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(build.main(), 0)
            bootstrap.assert_called_once_with("clang", 2)
            expected = [Path("compiler-O2"), self.source, "target"]
            if policy == "abort":
                expected.append("abort")
            emit.assert_called_once_with(*expected)
            self.assertEqual(self.output.read_bytes(), b"new-module\r\n")
            self.assertEqual(run.call_count, 1)
            self.assertIn("--target=target", run.call_args.args[0])

    def test_failed_policy_module_keeps_existing_output_and_skips_link(self):
        with patch.object(sys, "argv", ["build_v4.py", str(self.source), "-o", str(self.output), "--panic=abort"]), \
                patch.object(build.shutil, "which", return_value="clang"), \
                patch.object(build, "host_target", return_value="target"), \
                patch.object(build, "bootstrap", return_value=Path("compiler")), \
                patch.object(build, "emit_module", side_effect=RuntimeError("module rejected")), \
                patch.object(checks, "run_with_heartbeat") as run, \
                contextlib.redirect_stdout(io.StringIO()) as stdout, \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            self.assertEqual(build.main(), 1)
        self.assertEqual(self.output.read_bytes(), b"existing-output\x00\r\n")
        run.assert_not_called()
        self.assertNotIn("built ", stdout.getvalue())
        self.assertIn("module rejected", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
