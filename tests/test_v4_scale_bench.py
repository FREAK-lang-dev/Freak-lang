"""Exercise benchmark failures that previously produced false success or hung."""
from __future__ import annotations

import hashlib
import contextlib
import io
import importlib.util
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
STAGES = ["lex", "parse", "hir", "resolve", "ty", "mir", "borrowck", "codegen", "module"]
LLVM_VERSION = "llvm-nm, compatible with GNU nm\nLLVM version 19.1.7\n"


class SymbolToolSelection(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.tool = self.work / "llvm-nm-real"
        self.tool.write_bytes(b"LLVM tool image")
        self.obj = self.work / "module.o"
        self.obj.write_bytes(b"native object")
        spec = importlib.util.spec_from_file_location("symbol_tool_benchmark", ROOT / "v4_scale_bench.py")
        self.benchmark = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.benchmark)

    def test_missing_llvm_reader_fails_without_using_gnu_nm(self):
        with patch.object(self.benchmark.shutil, "which",
                          side_effect=lambda name: "/usr/bin/nm" if name == "nm" else None) as which, \
                patch.object(self.benchmark, "guarded_job") as job:
            with self.assertRaisesRegex(RuntimeError, "llvm-nm is required.*install LLVM tools"):
                self.benchmark.llvm_symbol_tool(None, self.work / "selection", 10)
        which.assert_called_once_with("llvm-nm")
        job.assert_not_called()

    def test_selection_records_actual_canonical_image_and_llvm_version(self):
        alias = self.work / "llvm-nm"
        alias.symlink_to(self.tool)
        result = subprocess.CompletedProcess([], 0, LLVM_VERSION, "")
        with patch.object(self.benchmark.shutil, "which", return_value=str(alias)), \
                patch.object(self.benchmark, "guarded_job", return_value=result) as job:
            selected = self.benchmark.llvm_symbol_tool(None, self.work / "selection", 20)
        self.assertEqual(selected["requested_nm"], str(alias))
        self.assertEqual(selected["resolved_nm"], str(self.tool))
        self.assertEqual(selected["nm_version"], LLVM_VERSION)
        self.assertEqual(selected["nm_file"]["sha256"], hashlib.sha256(self.tool.read_bytes()).hexdigest())
        job.assert_called_once_with(None, [str(self.tool), "--version"],
                                    self.work / "selection/tool-version",
                                    "LLVM symbol tool version", 5, 128, 1)
        self.assertEqual(json.loads((self.work / "selection/provenance.json").read_text()), selected)

    def test_name_without_llvm_implementation_is_rejected_before_inventory(self):
        result = subprocess.CompletedProcess([], 0, "GNU nm (GNU Binutils) 2.42\n", "")
        with patch.object(self.benchmark.shutil, "which", return_value=str(self.tool)), \
                patch.object(self.benchmark, "guarded_job", return_value=result) as job:
            with self.assertRaisesRegex(RuntimeError, "does not report an LLVM symbol reader"):
                self.benchmark.defined_symbols(None, self.obj, self.work / "symbols", 10)
        self.assertEqual(job.call_count, 1)
        self.assertEqual(job.call_args.args[1], [str(self.tool), "--version"])
        metadata = json.loads((self.work / "symbols/tool-selection/provenance.json").read_text())
        self.assertEqual(metadata["nm_version"], result.stdout)

    def test_frozen_image_change_stops_before_symbol_reader_execution(self):
        selected = {"requested_nm": str(self.tool), "resolved_nm": str(self.tool),
                    "nm_file": self.benchmark.symbol_file_provenance(self.tool),
                    "nm_version": LLVM_VERSION}
        self.tool.write_bytes(b"different executable image")
        with patch.object(self.benchmark, "guarded_job") as job:
            with self.assertRaisesRegex(RuntimeError, "frozen LLVM symbol tool changed"):
                self.benchmark.defined_symbols(None, self.obj, self.work / "symbols", 10,
                                               symbol_tool=selected)
        job.assert_not_called()

    def test_pinned_selection_keeps_exports_and_unchanged_inventory_limits(self):
        version = subprocess.CompletedProcess([], 0, LLVM_VERSION, "")
        inventory = subprocess.CompletedProcess([], 0,
            "00000000 T main\n00000008 T bench_collision\n00000010 W weak_export\n", "")
        with patch.object(self.benchmark.shutil, "which", return_value=str(self.tool)) as which, \
                patch.object(self.benchmark, "guarded_job", side_effect=[version, inventory]) as job:
            selected = self.benchmark.llvm_symbol_tool(None, self.work / "selection", 10)
            exports = self.benchmark.defined_symbols(None, self.obj, self.work / "symbols", 10,
                                                    symbol_tool=selected)
        which.assert_called_once_with("llvm-nm")
        self.assertEqual(exports, {"main", "bench_collision", "weak_export"})
        self.assertEqual(job.call_count, 2)
        self.assertEqual(job.call_args.args,
            (None, [str(self.tool), "-g", "--defined-only", str(self.obj)],
             self.work / "symbols", "native symbol inventory", 10, 128, 8))
        metadata = json.loads((self.work / "symbols/provenance.json").read_text())
        self.assertEqual(metadata["nm_file"], selected["nm_file"])
        self.assertEqual(metadata["object"]["sha256"], hashlib.sha256(self.obj.read_bytes()).hexdigest())


class FrozenRuntimeInventory(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.repo = self.work / "repo"
        from freakc.v4_native_runtime import SOURCE_NAMES, HEADER_NAMES
        self.sources, self.headers = SOURCE_NAMES, HEADER_NAMES
        runtime = self.repo / "freakc/runtime"
        runtime.mkdir(parents=True)
        for name in (*self.sources, *self.headers):
            (runtime / name).write_text(f"frozen contents for {name}\n")
        original = self.repo / "build/v4_smoke/build_llvm.fk.c"
        original.parent.mkdir(parents=True)
        original.write_text("original compiler\n")
        spec = importlib.util.spec_from_file_location("frozen_runtime_benchmark", ROOT / "v4_scale_bench.py")
        self.benchmark = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.benchmark)
        self.build = SimpleNamespace(checks=SimpleNamespace(run_with_heartbeat=object()),
                                     bootstrap=lambda clang: None)
        self.jobs = []

        def job(build, command, directory, label, *args, **kwargs):
            self.jobs.append(command)
            if "-o" in command:
                artifact = Path(command[command.index("-o") + 1])
                artifact.write_bytes((artifact.name + " compiled").encode())
            return subprocess.CompletedProcess(command, 0, "test Clang version\n", "")

        self.enterContext(patch.object(self.benchmark, "guarded_job", side_effect=job))
        self.enterContext(patch.object(self.benchmark, "instrument", return_value="measured compiler\n"))
        self.symbol_tool = {"resolved_nm": "verified-test-llvm-nm", "nm_version": LLVM_VERSION,
                            "nm_file": {"sha256": "pinned-test-image"}}
        self.enterContext(patch.object(self.benchmark, "llvm_symbol_tool", return_value=self.symbol_tool))
        self.enterContext(patch.object(self.benchmark.shutil, "which", return_value="test-clang"))
        self.enterContext(patch.object(self.benchmark.subprocess, "check_output", return_value="pinned-head\n"))

    def test_later_runtime_object_collision_stops_before_manifest_publication(self):
        exports = [{f"unique_{i}"} for i in range(len(self.sources))]
        exports[2].add("later_collision")
        exports[5].add("later_collision")
        with patch.object(self.benchmark, "defined_symbols", side_effect=exports) as symbols:
            with self.assertRaisesRegex(RuntimeError, "unexpected runtime symbol collisions.*later_collision"):
                self.benchmark.build_tool(self.repo, self.work / "runs", False, 30, self.build)
        self.assertEqual(symbols.call_count, len(self.sources))
        self.assertFalse(list((self.work / "runs").rglob("*.manifest.json")))

    def test_manifest_freezes_hashes_and_symbols_for_every_runtime_input(self):
        exports = [{f"unique_{i}"} for i in range(len(self.sources))]
        with patch.object(self.benchmark, "defined_symbols", side_effect=exports):
            tool, manifest = self.benchmark.build_tool(self.repo, self.work / "runs", False, 30, self.build)
        self.assertEqual(len(manifest["runtime_objects"]), 6)
        self.assertEqual(set(manifest["runtime_hashes"]), set((*self.sources, *self.headers)))
        self.assertEqual(len(manifest["runtime_hashes"]), 12)
        self.assertEqual(manifest["runtime_symbols"], [f"unique_{i}" for i in range(6)])
        self.assertEqual(manifest["runtime_collisions"], [])
        self.assertEqual(manifest["symbol_tool"], self.symbol_tool)
        for name, digest in manifest["runtime_hashes"].items():
            frozen = tool.parent / "runtime" / name
            self.assertEqual(digest, hashlib.sha256(frozen.read_bytes()).hexdigest())
            (self.repo / "freakc/runtime" / name).write_text("source changed after freezing\n")
            self.assertEqual(digest, hashlib.sha256(frozen.read_bytes()).hexdigest())
        self.assertEqual(set(manifest["runtime_object_hashes"]), set(manifest["runtime_objects"]))
        for name, digest in manifest["runtime_object_hashes"].items():
            self.assertEqual(digest, hashlib.sha256(Path(name).read_bytes()).hexdigest())


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
static freak_word freak_v4_target_spec_new(freak_word target) { return target; }
static freak_word freak_v4_codegen_llvm_module_text(int64_t codegen, freak_word target) { return (freak_word){0}; }
"""
        for stage, function in (
            ("parse", "parse_stream"), ("hir", "hir_lower_tree"),
            ("resolve", "resolve_lower_hir"), ("ty", "ty_lower_resolve"),
            ("mir", "mir_lower_ty"), ("borrowck", "borrowck_check_mir"),
            ("codegen", "codegen_llvm_lower_owned_mir"),
        ):
            declarations += f"static int64_t freak_v4_{function}(int64_t id, int64_t previous) {{ return id; }}\n"
        for stage in STAGES[:-1]:
            prefix = "codegen_llvm" if stage == "codegen" else stage
            declarations += f"static int64_t freak_v4_{prefix}_diag_count(int64_t id) {{ return 0; }}\n"
        source = declarations + "static void freak_v4_build_llvm_source(freak_word source) {\n"
        source += 'freak_word target_spec = freak_v4_target_spec_new(freak_word_lit("target"));\n'
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

    def test_instrumentation_matches_the_production_bootstrap(self):
        """Catch statement drift in the real generated source before native CI."""
        spec = importlib.util.spec_from_file_location("v4_benchmark_production", ROOT / "v4_scale_bench.py")
        benchmark = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(benchmark)
        build = benchmark.load_build(ROOT)
        generated, uses_ui = build.checks.transpile_fixture(
            build.checks.flattened_crates(), build.checks.V4_ROOT / "tools" / "build_llvm.fk",
        )
        self.assertFalse(uses_ui)
        measured = benchmark.instrument(generated)
        for stage in STAGES:
            self.assertEqual(measured.count(f'v4_bench_report("{stage}",'), 1)
        source_entry = "static void freak_v4_build_llvm_source(freak_word source) {"
        self.assertLess(measured.index("static double v4_bench_clock"), measured.index(source_entry))
        self.assertIn("static void freak_v4_build_llvm_run(void) {\n    atexit(v4_bench_final);", measured)
        module_statement = "freak_word module = freak_v4_codegen_llvm_module_text(codegen, target_spec);"
        self.assertIn(module_statement, measured)
        with self.assertRaisesRegex(RuntimeError, "generated C module boundary changed"):
            benchmark.instrument(generated.replace(module_statement, module_statement.replace("target_spec", "changed_target")))

    def test_diagnostics_fail_even_with_zero_compiler_exit(self):
        tool = self.fake_tool("print('v4-build-stage=lex diagnostics=1')\n")
        result, rows = self.run_bench(tool)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(rows[0]["status"], "diagnostics")

    def test_git_provenance_failure_writes_structured_build_failure(self):
        spec = importlib.util.spec_from_file_location("v4_benchmark_failure", ROOT / "v4_scale_bench.py")
        benchmark = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(benchmark)
        destination = self.work / "result.json"
        error = subprocess.CalledProcessError(128, ["git", "rev-parse", "HEAD"])
        arguments = ["v4_scale_bench.py", "--repo", str(ROOT), "--work", str(self.work / "runs"),
                     "--json", str(destination), "--shapes", "tasks", "--sizes", "1"]
        with patch.object(sys, "argv", arguments), patch.object(benchmark, "load_build", return_value=object()), \
                patch.object(benchmark.subprocess, "check_output", side_effect=error), \
                contextlib.redirect_stderr(io.StringIO()) as captured:
            self.assertEqual(benchmark.main(), 1)
        result = json.loads(destination.read_text())
        self.assertEqual(result["status"], "build-failed")
        self.assertEqual(result["results"], [])
        self.assertIn("cannot record repository head", result["failure"])
        self.assertNotIn("Traceback", captured.getvalue())

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

    @unittest.skipUnless(shutil.which("clang"), "clang required")
    def test_wrong_native_exit_fails_check(self):
        tool = self.fake_tool(self.emitted_program(exit_code=42))
        result, rows = self.run_bench(tool, "--check")
        context = json.dumps(rows, indent=2) + "\n" + result.stdout + result.stderr
        self.assertEqual(result.returncode, 1, context)
        self.assertEqual(rows[0]["status"], "native-check-failed", context)
        self.assertIn("native-mismatch:exit=42", rows[0]["check"], context)

    @unittest.skipUnless(shutil.which("clang"), "clang required")
    def test_duplicate_native_symbol_fails_before_compatibility_link(self):
        source, obj = self.work / "runtime.c", self.work / "runtime.o"
        source.write_text("long bench_collision(void) { return 2; }\n")
        subprocess.run([shutil.which("clang"), "-c", str(source), "-o", str(obj)],
                       check=True, capture_output=True, timeout=10)
        tool = self.fake_tool(self.emitted_program(collision=True), [obj], ["bench_collision"])
        result, rows = self.run_bench(tool, "--check")
        context = json.dumps(rows, indent=2) + "\n" + result.stdout + result.stderr
        self.assertEqual(result.returncode, 1, context)
        self.assertEqual(rows[0].get("status"), "native-check-failed", context)
        self.assertIn("unexpected-symbol-collisions", rows[0]["check"], context)
        self.assertFalse((Path(rows[0]["artifacts"]) / "native").exists())

    @unittest.skipUnless(shutil.which("clang"), "clang required")
    def test_native_inventory_matches_independent_elf_exports_on_the_same_object(self):
        spec = importlib.util.spec_from_file_location("native_symbol_benchmark", ROOT / "v4_scale_bench.py")
        benchmark = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(benchmark)
        build = benchmark.load_build(ROOT)
        source, obj = self.work / "exports.c", self.work / "exports.o"
        source.write_text(
            "int global_data = 3;\n"
            "int common_data __attribute__((common));\n"
            "static int local_helper(void) { return 1; }\n"
            "int bench_collision(void) { return local_helper(); }\n"
            "__attribute__((weak)) int weak_export(void) { return global_data; }\n"
            "extern int undefined_export(void);\n"
            "int calls_undefined(void) { return undefined_export(); }\n")
        compiled = benchmark.guarded_job(build,
            [shutil.which("clang"), "-O0", "-c", str(source), "-o", str(obj)],
            self.work / "exports-build", "native export control", 10, 1024)
        self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
        exported = benchmark.defined_symbols(build, obj, self.work / "exports-symbols", 10)
        readelf = shutil.which("readelf")
        self.assertIsNotNone(readelf, "readelf is required for independent same-object ELF parity")
        reference = benchmark.guarded_job(build, [readelf, "--wide", "--syms", str(obj)],
                                         self.work / "elf-reference", "ELF symbol reference", 10, 128, 8)
        self.assertEqual(reference.returncode, 0, reference.stdout + reference.stderr)
        expected = set()
        for line in reference.stdout.splitlines():
            fields = line.split()
            if len(fields) >= 8 and fields[4] in {"GLOBAL", "WEAK"} and fields[6] != "UND":
                expected.add(fields[7])
        self.assertEqual(expected, {"global_data", "common_data", "bench_collision",
                                    "weak_export", "calls_undefined"})
        self.assertEqual(exported, expected)

    @unittest.skipUnless(shutil.which("clang"), "clang required")
    def test_noncolliding_native_exports_link_and_execute(self):
        source, obj = self.work / "runtime.c", self.work / "runtime.o"
        source.write_text("long other_export(void) { return 2; }\n")
        subprocess.run([shutil.which("clang"), "-c", str(source), "-o", str(obj)],
                       check=True, capture_output=True, timeout=10)
        tool = self.fake_tool(self.emitted_program(), [obj], ["other_export"])
        result, rows = self.run_bench(tool, "--check")
        context = json.dumps(rows, indent=2) + "\n" + result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, context)
        self.assertEqual(rows[0]["status"], "ok", context)
        self.assertEqual(rows[0]["check"], "pass", context)


if __name__ == "__main__":
    unittest.main()
