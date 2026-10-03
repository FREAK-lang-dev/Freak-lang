"""Compiler optimization stays separate from program linking and smoke caches."""
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
SPEC = importlib.util.spec_from_file_location("compiler_opt_checks", ROOT / "src/compiler/v4/check_v4.py")
checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checks)
SPEC = importlib.util.spec_from_file_location("compiler_opt_build", ROOT / "src/compiler/v4/build_v4.py")
build = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, {"check_v4": checks}):
    SPEC.loader.exec_module(build)


class CompilerOptimizationCache(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.cache = self.work / "smoke"
        runtime = self.work / "runtime"
        runtime.mkdir()
        (runtime / "freak_runtime.c").write_text("/* test runtime */\n", encoding="utf-8")
        for attribute, value in (("RUNTIME_BUILD_ROOT", self.cache), ("RUNTIME_ROOT", runtime)):
            self.enterContext(patch.object(checks, attribute, value))
        self.enterContext(patch.object(checks, "flattened_crates", return_value="crates"))
        self.transpile = self.enterContext(patch.object(
            checks, "transpile_fixture", return_value=("int main(void) { return 0; }\n", False)))
        self.commands = []

        def compile_command(command, **kwargs):
            # Model Clang's artifact only; keep the real production cache path,
            # key, source writes and lookup so a collision causes a test failure.
            self.commands.append(command)
            output = Path(command[command.index("-o") + 1])
            flags = [item for item in command if item.startswith("-O")]
            output.write_bytes(flags[-1].encode("ascii"))
            return subprocess.CompletedProcess(command, 0, "", "")

        self.run = self.enterContext(patch.object(checks, "run_with_heartbeat", side_effect=compile_command))

    def test_levels_reuse_their_own_compiler_without_replacing_default(self):
        default = build.bootstrap("test-clang")
        default_bytes = default.read_bytes()
        artifacts = {0: default}
        for level in (1, 2, 3):
            with self.subTest(level=level):
                executable = build.bootstrap("test-clang", level)
                artifacts[level] = executable
                self.assertNotEqual(executable, default)
                self.assertEqual(executable.read_bytes(), f"-O{level}".encode("ascii"))
                self.assertEqual(default.read_bytes(), default_bytes)
                self.assertEqual(checks.RUNTIME_BUILD_ROOT, self.cache)
        self.assertEqual(len(self.commands), 4)
        for level in (3, 2, 1, 0):
            self.assertEqual(build.bootstrap("test-clang", level), artifacts[level])
        self.assertEqual(build.bootstrap("test-clang"), default)
        self.assertEqual(len(self.commands), 4, "unchanged compiler levels should hit their cache")
        self.assertEqual(default_bytes, b"-O0")

    def test_compiler_flags_invalidate_cache_even_in_same_directory(self):
        fixture = checks.V4_ROOT / "tools/build_llvm.fk"
        runtime = checks.RUNTIME_ROOT / "freak_runtime.c"
        self.cache.mkdir()
        arguments = ("test-clang", f"-I{checks.RUNTIME_ROOT}", runtime,
                     checks.read_text(runtime), fixture, "int main(void) { return 0; }\n")
        first, compiled = checks.compile_runtime_smoke(*arguments, ("-O1",))
        self.assertTrue(compiled)
        self.assertEqual(first.read_bytes(), b"-O1")
        second, compiled = checks.compile_runtime_smoke(*arguments, ("-O2",))
        self.assertTrue(compiled)
        self.assertEqual(second, first)
        self.assertEqual(second.read_bytes(), b"-O2")
        _, compiled = checks.compile_runtime_smoke(*arguments, ("-O2",))
        self.assertFalse(compiled)
        self.assertEqual(len(self.commands), 2)

    def test_failed_optimized_build_restores_default_cache_root(self):
        for failure in (RuntimeError("compiler interrupted"),
                        subprocess.CompletedProcess([], 1, "", "compiler failed")):
            with self.subTest(failure=failure), contextlib.redirect_stdout(io.StringIO()):
                if isinstance(failure, RuntimeError):
                    self.run.side_effect = failure
                    expected = RuntimeError
                else:
                    self.run.side_effect = None
                    self.run.return_value = failure
                    expected = SystemExit
                with self.assertRaises(expected):
                    build.bootstrap("test-clang", 2)
                self.assertEqual(checks.RUNTIME_BUILD_ROOT, self.cache)
                self.assertFalse(self.cache.joinpath("build_llvm.compile.sha256").exists())


class CompilerOptimizationCommand(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.source = self.work / "source.fk"
        self.source.write_text("task main() -> int { give back 0 }\n", encoding="utf-8")
        self.output = self.work / "program"

    def invoke(self, extra):
        arguments = ["build_v4.py", str(self.source), "-o", str(self.output), *extra]
        with patch.object(sys, "argv", arguments), \
                patch.object(build.shutil, "which", return_value="test-clang"), \
                patch.object(build, "host_target", return_value="host-target"), \
                patch.object(build, "bootstrap", return_value=Path("compiler")) as bootstrap, \
                patch.object(build, "emit_module", return_value="module\n") as emit, \
                patch.object(checks, "run_with_heartbeat",
                             return_value=subprocess.CompletedProcess([], 0, "", "")) as run, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(build.main(), 0)
        return bootstrap, emit, run

    def test_default_and_explicit_compiler_levels_leave_program_optimization_at_o2(self):
        for arguments, level in (([], 0), (["--compiler-opt", "0"], 0),
                                 (["--compiler-opt", "1"], 1), (["--compiler-opt=2"], 2),
                                 (["--compiler-opt", "3"], 3)):
            with self.subTest(arguments=arguments):
                bootstrap, emit, run = self.invoke(arguments)
                bootstrap.assert_called_once_with("test-clang", level)
                emit.assert_called_once_with(Path("compiler"), self.source, "host-target")
                command = run.call_args.args[0]
                self.assertEqual([item for item in command if item.startswith("-O")], ["-O2"])
                self.assertEqual(command[command.index("-o") + 1], str(self.output))

    def test_cross_target_ir_verification_does_not_inherit_compiler_optimization(self):
        bootstrap, emit, run = self.invoke([
            "--compiler-opt", "2", "--emit-llvm", "--target", "cross-target"])
        bootstrap.assert_called_once_with("test-clang", 2)
        emit.assert_called_once_with(Path("compiler"), self.source, "cross-target")
        command = run.call_args.args[0]
        self.assertIn("--target=cross-target", command)
        self.assertEqual(command[command.index("-x") + 1], "ir")
        self.assertIn("-c", command)
        self.assertFalse(any(item.startswith("-O") for item in command))
        self.assertEqual(self.output.read_bytes(), b"module\n")

    def test_invalid_compiler_level_rejects_before_tool_lookup_or_bootstrap(self):
        for value in ("-1", "4", "2.0", "not-an-int", ""):
            with self.subTest(value=value):
                stderr = io.StringIO()
                arguments = ["build_v4.py", str(self.source), "-o", str(self.output),
                             "--compiler-opt=" + value]
                with patch.object(sys, "argv", arguments), \
                        patch.object(build.shutil, "which") as which, \
                        patch.object(build, "bootstrap") as bootstrap, \
                        contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as failure:
                    build.main()
                self.assertEqual(failure.exception.code, 2)
                self.assertIn("--compiler-opt", stderr.getvalue())
                which.assert_not_called()
                bootstrap.assert_not_called()
                self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
