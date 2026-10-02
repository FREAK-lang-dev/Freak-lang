"""Exercise benchmark failures that previously produced false success or hung."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
STAGES = ["lex", "parse", "hir", "resolve", "ty", "mir", "borrowck", "codegen", "module"]


@unittest.skipUnless(sys.platform.startswith("linux"), "Linux benchmark")
class BenchmarkFailures(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)

    def fake_tool(self, body: str, objects=(), symbols=()):
        tool = self.work / "compiler"
        tool.write_text(f"#!{sys.executable}\n" + body)
        tool.chmod(0o755)
        manifest = {"tool_sha256": hashlib.sha256(tool.read_bytes()).hexdigest(),
                    "profile": False, "clang": shutil.which("clang"),
                    "runtime_objects": [str(path) for path in objects],
                    "runtime_object_hashes": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                                              for path in objects},
                    "runtime_symbols": list(symbols)}
        tool.with_suffix(".manifest.json").write_text(json.dumps(manifest))
        return tool

    def emitted_program(self, exit_code=6, collision=False):
        prefix = "".join(f"v4-build-stage={stage} diagnostics=0\n" for stage in STAGES[:-1])
        prefix += "v4-errors=0\n@@V4-MODULE\n"
        triple = "aarch64-unknown-linux-gnu" if platform.machine().lower() in ("aarch64", "arm64") else "x86_64-unknown-linux-gnu"
        module = (f'target triple = "{triple}"\n'
                  f"define i32 @main() {{ ret i32 {exit_code} }}\n")
        if collision:
            module += "define i64 @bench_collision() { ret i64 1 }\n"
        stderr = "".join(f"V4BENCH stage={stage} seconds=0.001 rss_bytes=4096 "
                         "peak_bytes=4096 diagnostics=0\n" for stage in STAGES)
        stderr += "V4BENCH final peak_bytes=4096\n"
        return f"import sys\nprint({prefix + module!r}, end='')\nprint({stderr!r}, end='', file=sys.stderr)\n"

    def run_bench(self, tool, *extra):
        result = subprocess.run([sys.executable, str(ROOT / "v4_scale_bench.py"),
            "--repo", str(ROOT), "--tool", str(tool), "--shapes", "tasks", "--sizes", "1",
            "--work", str(self.work / "runs"), "--json", str(self.work / "result.json"), *extra],
            cwd=ROOT, capture_output=True, text=True, timeout=15)
        return result, json.loads((self.work / "result.json").read_text())

    @unittest.skipUnless(shutil.which("clang"), "clang required")
    def test_source_helper_measurements_compile_and_flush_at_exit(self):
        spec = importlib.util.spec_from_file_location("v4_benchmark", ROOT / "v4_scale_bench.py")
        benchmark = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(benchmark)
        declarations = """
#include <stdint.h>
typedef struct { const char *data; int64_t len; } freak_word;
static const char *freak_argv[] = {"tool", "source", "target"};
static freak_word freak_word_lit(const char *text) { return (freak_word){text, 0}; }
static int64_t freak_v4_lex_text(int64_t id, freak_word source) { return id; }
static int64_t freak_v4_target_spec_new(freak_word target) { return 0; }
static freak_word freak_v4_codegen_llvm_module_text(int64_t codegen, int64_t target) { return (freak_word){0}; }
"""
        for stage, function in (
            ("parse", "parse_stream"), ("hir", "hir_lower_tree"),
            ("resolve", "resolve_lower_hir"), ("ty", "ty_lower_resolve"),
            ("mir", "mir_lower_ty"), ("borrowck", "borrowck_check_mir"),
            ("codegen", "codegen_llvm_lower_mir"),
        ):
            declarations += f"static int64_t freak_v4_{function}(int64_t id, int64_t previous) {{ return id; }}\n"
        for stage in STAGES[:-1]:
            prefix = "codegen_llvm" if stage == "codegen" else stage
            declarations += f"static int64_t freak_v4_{prefix}_diag_count(int64_t id) {{ return 0; }}\n"
        source = declarations + "static void freak_v4_build_llvm_source(freak_word source) {\n"
        source += "\n".join(statement for _, statement, _ in benchmark.INSTRUMENTATION_POINTS)
        source += "\n}\nstatic void freak_v4_build_llvm_run(void) {\n"
        source += "freak_v4_build_llvm_source((freak_word){0});\n}\n"
        source += "int main(void) { freak_v4_build_llvm_run(); return 0; }\n"
        c_path, binary = self.work / "measured.c", self.work / "measured"
        c_path.write_text(benchmark.instrument(source))
        compiled = subprocess.run([
            shutil.which("clang"), "-std=c11", "-D_POSIX_C_SOURCE=200809L",
            "-Werror=implicit-function-declaration", str(c_path), "-o", str(binary),
        ], capture_output=True, text=True, timeout=15)
        self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
        executed = subprocess.run([str(binary)], capture_output=True, text=True, timeout=5)
        self.assertEqual(executed.returncode, 0, executed.stdout + executed.stderr)
        records = executed.stderr.splitlines()
        self.assertEqual([line.split()[1] for line in records[:-1]],
                         [f"stage={stage}" for stage in STAGES])
        self.assertRegex(records[-1], r"^V4BENCH final peak_bytes=[1-9][0-9]*$")

    def test_diagnostics_fail_even_with_zero_compiler_exit(self):
        tool = self.fake_tool("print('v4-build-stage=lex diagnostics=1')\n")
        result, rows = self.run_bench(tool)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(rows[0]["status"], "diagnostics")

    def test_nonfinite_timeout_rejected_before_running_tool(self):
        marker = self.work / "executed"
        tool = self.fake_tool(f"from pathlib import Path\nPath({str(marker)!r}).touch()\n")
        for option in ("--timeout", "--build-timeout"):
            for value in ("nan", "inf"):
                with self.subTest(option=option, value=value):
                    result = subprocess.run([sys.executable, str(ROOT / "v4_scale_bench.py"),
                        "--repo", str(ROOT), "--tool", str(tool), option, value],
                        cwd=ROOT, capture_output=True, text=True, timeout=5)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertFalse(marker.exists())

    def test_quiet_stage_timeout_terminates_descendant(self):
        pid_file = self.work / "child.pid"
        tool = self.fake_tool("import subprocess,time\nfrom pathlib import Path\n"
            "child=subprocess.Popen(['" + sys.executable + "','-c','import time;time.sleep(20)'])\n"
            f"Path({str(pid_file)!r}).write_text(str(child.pid))\ntime.sleep(20)\n")
        result, rows = self.run_bench(tool, "--timeout", "0.5")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(rows[0]["status"], "failed")
        pid = int(pid_file.read_text())
        stat = Path(f"/proc/{pid}/stat")
        if stat.exists():
            state = stat.read_text().split(")", 1)[1].split()[0]
            self.assertEqual(state, "Z", f"descendant {pid} still running")

    @unittest.skipUnless(shutil.which("clang") and shutil.which("nm"), "clang and nm required")
    def test_wrong_native_exit_fails_check(self):
        tool = self.fake_tool(self.emitted_program(exit_code=42))
        result, rows = self.run_bench(tool, "--check")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(rows[0]["status"], "native-check-failed")
        self.assertIn("native-mismatch:exit=42", rows[0]["check"])

    @unittest.skipUnless(shutil.which("clang") and shutil.which("nm"), "clang and nm required")
    def test_duplicate_native_symbol_fails_before_compatibility_link(self):
        source, obj = self.work / "runtime.c", self.work / "runtime.o"
        source.write_text("long bench_collision(void) { return 2; }\n")
        subprocess.run([shutil.which("clang"), "-c", str(source), "-o", str(obj)],
                       check=True, capture_output=True, timeout=10)
        tool = self.fake_tool(self.emitted_program(collision=True), [obj], ["bench_collision"])
        result, rows = self.run_bench(tool, "--check")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("unexpected-symbol-collisions", rows[0]["check"])
        self.assertFalse((Path(rows[0]["artifacts"]) / "native").exists())


if __name__ == "__main__":
    unittest.main()
