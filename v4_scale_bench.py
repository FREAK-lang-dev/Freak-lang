#!/usr/bin/env python3
"""V4 scaling benchmark: per-stage time and memory across input shapes and sizes.

Run from the repository root:

    python v4_scale_bench.py                      # default shapes and sizes
    python v4_scale_bench.py --shapes tasks long --sizes 200 800 3200
    python v4_scale_bench.py --json out.json      # keep raw numbers
    python v4_scale_bench.py --check              # also link and run each program

Each shape stresses a different cost:

    tasks   many small tasks                 -> name lookups, per-item scans
    long    few tasks with very long bodies  -> per-body statement/rvalue scans
    calls   many call sites per task         -> signature and symbol lookups
    impl    shapes, impl tasks, aliases      -> alias/shape/type signature lookups
    say     many string literals             -> literal tables, module globals
    mixed   all of the above together

"Size" is a count of generated units, not lines; the line count is reported.
Every generated program has a known exit code, checked with --check, so the
harness doubles as a correctness guard for scaling changes.

Linux only. Native monotonic-clock stage timings and cumulative Linux VmHWM
peak RSS are captured from a frozen, instrumented bootstrap compiler. Child
jobs use the V4 process-group, time, memory and output guards. Failures exit
nonzero; raw evidence and source/runtime/toolchain provenance are retained.
"""
from __future__ import annotations

import argparse
import json
import os
import hashlib
import math
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

STAGES = ["lex", "parse", "hir", "resolve", "ty", "mir", "borrowck", "codegen", "module"]


# ---------------------------------------------------------------- generators
# Each returns (source_text, expected_exit_code, expected_stdout).

def gen_tasks(n: int):
    body = ("task f{i}(a: int, b: int) -> int {{\n    pilot t = a + b\n"
            "    if t > 10 {{\n        give back t - 1\n    }}\n    give back t * 2\n}}\n")
    src = "".join(body.format(i=i) for i in range(n))
    src += "task main() -> int {\n    give back f0(1, 2)\n}\n"
    return src, 6, ""


def gen_long(n: int):
    """A handful of tasks whose bodies grow with n (n statements each)."""
    tasks = 4
    out = []
    for t in range(tasks):
        lines = [f"task long{t}(seed: int) -> int {{", "    pilot acc = seed"]
        for s in range(n):
            if s % 7 == 6:
                lines.append("    if acc > 1000 {")
                lines.append("        acc = acc - 1000")
                lines.append("    }")
            else:
                lines.append(f"    acc = acc + {(s % 5) + 1}")
        lines.append("    give back acc")
        lines.append("}")
        out.append("\n".join(lines) + "\n")

    def run(seed: int) -> int:
        acc = seed
        for s in range(n):
            if s % 7 == 6:
                if acc > 1000:
                    acc -= 1000
            else:
                acc += (s % 5) + 1
        return acc

    src = "".join(out)
    src += "task main() -> int {\n    give back long0(3) % 200\n}\n"
    return src, run(3) % 200, ""


def gen_calls(n: int):
    """n tasks, each making six calls to a small set of leaf helpers."""
    helpers = 8
    out = [f"task leaf{h}(x: int) -> int {{\n    give back x + {h}\n}}\n" for h in range(helpers)]
    for i in range(n):
        calls = " + ".join(f"leaf{(i + k) % helpers}(x)" for k in range(6))
        out.append(f"task caller{i}(x: int) -> int {{\n    pilot total = {calls}\n    give back total\n}}\n")
    src = "".join(out)
    src += "task main() -> int {\n    give back caller0(1) % 200\n}\n"
    expected = sum(1 + ((0 + k) % helpers) for k in range(6)) % 200
    return src, expected, ""


def gen_impl(n: int):
    """n shapes, each with an alias and three associated scalar tasks."""
    out = []
    for i in range(n):
        out.append(
            f"alias Score{i} = int\n"
            f"shape Unit{i} {{\n    marker: int\n}}\n"
            f"impl Unit{i} {{\n"
            f"    task add(left: Score{i}, right: Score{i}) -> Score{i} {{\n        give back left + right\n    }}\n"
            f"    task pick(flag: bool, chosen: int, other: int) -> int {{\n        if flag {{ give back chosen }}\n        give back other\n    }}\n"
            f"    task scale(value: int) -> int {{\n        give back value * {(i % 3) + 1}\n    }}\n"
            f"}}\n")
    src = "".join(out)
    src += ("task main() -> int {\n    pilot sum = Unit0::add(right: 19, left: 23)\n"
            "    give back Unit0::pick(true, Unit0::scale(sum), 0)\n}\n")
    return src, 42, ""


def gen_say(n: int):
    """n tasks holding four literals each; only main prints."""
    out = []
    for i in range(n):
        out.append(
            f"task talk{i}() -> void {{\n"
            f"    say \"unit {i} line one\"\n    say \"unit {i} line two\"\n"
            f"    say \"unit {i} tab\\tquote\\\"\"\n    say \"unit {i} done\"\n}}\n")
    src = "".join(out)
    src += "task main() -> int {\n    say \"bench ok\"\n    give back 7\n}\n"
    return src, 7, "bench ok\n"


def gen_mixed(n: int):
    parts = []
    q = max(1, n // 5)
    t, _, _ = gen_tasks(q)
    parts.append(t.rsplit("task main()", 1)[0])
    l, _, _ = gen_long(max(8, q // 4))
    parts.append(l.rsplit("task main()", 1)[0])
    c, _, _ = gen_calls(q)
    parts.append(c.rsplit("task main()", 1)[0])
    i, _, _ = gen_impl(q)
    parts.append(i.rsplit("task main()", 1)[0])
    s, _, _ = gen_say(q)
    parts.append(s.rsplit("task main()", 1)[0])
    src = "".join(parts)
    src += ("task main() -> int {\n    say \"bench ok\"\n"
            "    give back f0(1, 2) + Unit0::add(left: 1, right: 2)\n}\n")
    return src, 9, "bench ok\n"


GENERATORS = {"tasks": gen_tasks, "long": gen_long, "calls": gen_calls,
              "impl": gen_impl, "say": gen_say, "mixed": gen_mixed}


def load_build(repo: Path):
    sys.path.insert(0, str(repo / "src/compiler/v4"))
    import build_v4
    if build_v4.checks.ROOT.resolve() != repo:
        raise RuntimeError("benchmark imported a different checkout's build tool")
    return build_v4


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def guarded_job(build, command, directory, label, timeout, memory, output=64, runner=None):
    """All child jobs share V4's continuously polled, bounded process guard."""
    directory.mkdir(parents=True, exist_ok=True)
    save_json(directory / "command.json", {"command": command, "timeout": timeout,
              "memory_limit_mib": memory, "output_limit_mib": output})
    try:
        result = (runner or build.checks.run_with_heartbeat)(
            command, label=label, timeout_seconds=timeout,
            memory_limit_mb=memory, output_limit_mb=output,
        )
    except (RuntimeError, subprocess.TimeoutExpired) as error:
        # The shared guard retains bounded tails when a limit is exceeded.
        (directory / "failure.txt").write_text(str(error), encoding="utf-8")
        for name, value in (("stdout.txt", getattr(error, "output", "")),
                            ("stderr.txt", getattr(error, "stderr", ""))):
            if isinstance(value, bytes):
                value = value.decode("utf-8", errors="replace")
            (directory / name).write_text(value or "", encoding="utf-8")
        raise
    (directory / "stdout.txt").write_text(result.stdout, encoding="utf-8")
    (directory / "stderr.txt").write_text(result.stderr, encoding="utf-8")
    return result


def require_success(result, label):
    if result.returncode:
        raise RuntimeError(f"{label}: exit {result.returncode}\n"
                           + (result.stdout + result.stderr)[-4000:])


INSTRUMENTATION_POINTS = [
    ("lex", "int64_t stream = freak_v4_lex_text(((int64_t)0), source);", "freak_v4_lex_diag_count(stream)"),
    ("parse", "int64_t tree = freak_v4_parse_stream(((int64_t)0), stream);", "freak_v4_parse_diag_count(tree)"),
    ("hir", "int64_t hir = freak_v4_hir_lower_tree(((int64_t)0), tree);", "freak_v4_hir_diag_count(hir)"),
    ("resolve", "int64_t resolve = freak_v4_resolve_lower_hir(((int64_t)0), hir);", "freak_v4_resolve_diag_count(resolve)"),
    ("ty", "int64_t ty = freak_v4_ty_lower_resolve(((int64_t)0), resolve);", "freak_v4_ty_diag_count(ty)"),
    ("mir", "int64_t mir = freak_v4_mir_lower_ty(((int64_t)0), ty);", "freak_v4_mir_diag_count(mir)"),
    ("borrowck", "int64_t borrowck = freak_v4_borrowck_check_mir(((int64_t)0), mir);", "freak_v4_borrowck_diag_count(borrowck)"),
    ("codegen", "int64_t codegen = freak_v4_codegen_llvm_lower_mir(((int64_t)0), mir);", "freak_v4_codegen_llvm_diag_count(codegen)"),
    ("module", "freak_word module = freak_v4_codegen_llvm_module_text(codegen, target_spec);", "0"),
]

NATIVE_MEASUREMENT = r'''
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <sys/resource.h>
#include <unistd.h>
static double v4_bench_clock(void) {
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC, &now)) abort();
    return (double)now.tv_sec + (double)now.tv_nsec / 1000000000.0;
}
static long long v4_bench_peak(void) {
    /* ru_maxrss can retain the Python parent's RSS across fork/exec.
       VmHWM belongs to this post-exec address space. */
    FILE *status = fopen("/proc/self/status", "r");
    if (!status) abort();
    char line[256];
    long long kib = 0;
    while (fgets(line, sizeof(line), status)) {
        if (sscanf(line, "VmHWM: %lld kB", &kib) == 1) {
            fclose(status);
            return kib * 1024;
        }
    }
    fclose(status);
    abort();
}
static void v4_bench_final(void) {
    fprintf(stderr, "V4BENCH final peak_bytes=%lld\n", v4_bench_peak());
}
static void v4_bench_report(const char *stage, double started, long long diagnostics) {
    double elapsed = v4_bench_clock() - started;
    long pages = 0, resident = 0;
    FILE *statm = fopen("/proc/self/statm", "r");
    if (!statm || fscanf(statm, "%ld %ld", &pages, &resident) != 2) abort();
    fclose(statm);
    fprintf(stderr, "V4BENCH stage=%s seconds=%.9f rss_bytes=%lld peak_bytes=%lld diagnostics=%lld\n",
        stage, elapsed, (long long)resident * sysconf(_SC_PAGESIZE),
        v4_bench_peak(), diagnostics);
    fflush(stderr);
}
'''


def instrument(source: str) -> str:
    source_marker = "static void freak_v4_build_llvm_source(freak_word source) {"
    marker = "static void freak_v4_build_llvm_run(void) {"
    if source.count(source_marker) != 1 or source.count(marker) != 1:
        raise RuntimeError("generated C entrypoint changed; update benchmark instrumentation")
    source = source.replace(source_marker, NATIVE_MEASUREMENT + "\n" + source_marker)
    source = source.replace(marker, marker + "\n    atexit(v4_bench_final);")
    for stage, statement, diagnostics in INSTRUMENTATION_POINTS:
        if source.count(statement) != 1:
            raise RuntimeError(f"generated C {stage} boundary changed; update instrumentation")
        source = source.replace(statement,
            f"double v4_bench_{stage}_started = v4_bench_clock();\n    {statement}\n"
            f'    v4_bench_report("{stage}", v4_bench_{stage}_started, {diagnostics});')
    return source


def defined_symbols(build, path: Path, directory: Path, timeout: float) -> set[str]:
    nm = shutil.which("nm")
    if not nm:
        raise RuntimeError("nm is required for the native symbol collision check")
    result = guarded_job(build, [nm, "-g", "--defined-only", str(path)],
                         directory, "native symbol inventory", timeout, 128, 8)
    require_success(result, "nm")
    return {line.split()[-1] for line in result.stdout.splitlines() if len(line.split()) >= 2}


def build_tool(repo, work, profile, timeout, build):
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True,
                                       stderr=subprocess.STDOUT).strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise RuntimeError(f"cannot record repository head: {error}") from error
    clang = shutil.which("clang")
    if not clang:
        raise RuntimeError("clang is required")
    # Each invocation retains its compiler/runtime evidence independently.
    compiler_dir = work / "compiler" / str(time.time_ns())
    compiler_dir.mkdir(parents=True)
    # Bound the existing bootstrap's child compiler, without changing the
    # shared smoke harness or its O0 cache/flags.
    original_runner = build.checks.run_with_heartbeat
    bootstrap_jobs = 0
    def bounded_bootstrap(command, **kwargs):
        nonlocal bootstrap_jobs
        bootstrap_jobs += 1
        return guarded_job(build, command, compiler_dir / f"bootstrap-job-{bootstrap_jobs}",
                           kwargs["label"], kwargs.get("timeout_seconds") or timeout,
                           kwargs.get("memory_limit_mb") or 1024,
                           kwargs.get("output_limit_mb", 64), runner=original_runner)
    build.checks.run_with_heartbeat = bounded_bootstrap
    try:
        try:
            build.bootstrap(clang)
        except SystemExit as error:
            raise RuntimeError(f"bootstrap failed with exit {error.code}; evidence: {compiler_dir}") from error
    finally:
        build.checks.run_with_heartbeat = original_runner
    original = repo / "build/v4_smoke/build_llvm.fk.c"
    frozen = compiler_dir / "compiler-original.c"
    frozen.write_bytes(original.read_bytes())
    measured = compiler_dir / "compiler-measured.c"
    measured.write_text(instrument(frozen.read_text()), encoding="utf-8")
    runtime = compiler_dir / "runtime"
    runtime.mkdir(exist_ok=True)
    for name in ("freak_runtime.c", "freak_llvm_runtime.c", "freak_runtime.h"):
        (runtime / name).write_bytes((repo / "freakc/runtime" / name).read_bytes())
    flags = ["-pg", "-O1", "-fno-inline"] if profile else ["-O2"]
    tool = compiler_dir / ("v4c_pg" if profile else "v4c")
    command = [clang, *flags, "-w", str(measured), str(runtime / "freak_runtime.c"),
               f"-I{runtime}", "-lm", "-o", str(tool)]
    require_success(guarded_job(build, command, compiler_dir / "build", "benchmark compiler build",
                               timeout, 1024), "benchmark compiler build")
    version = guarded_job(build, [clang, "--version"], compiler_dir / "toolchain",
                          "clang version", 30, 128, 8)
    require_success(version, "clang version")
    # Native linking retains the shared adapter-before-core platform contract.
    # Audit exports first so its compatibility linker flags cannot hide duplicates.
    runtime_objects = []
    for name in ("freak_llvm_runtime", "freak_runtime"):
        obj = runtime / f"{name}.o"
        result = guarded_job(build, [clang, "-w", "-O2", "-c", str(runtime / f"{name}.c"),
                             f"-I{runtime}", "-o", str(obj)], compiler_dir / f"build-{name}",
                             f"native {name} build", timeout, 1024)
        require_success(result, name)
        runtime_objects.append(obj)
    symbols = [defined_symbols(build, obj, compiler_dir / f"symbols-{obj.stem}", timeout)
               for obj in runtime_objects]
    duplicates = sorted(symbols[0] & symbols[1])
    if duplicates:
        raise RuntimeError(f"unexpected runtime symbol collisions: {duplicates}")
    manifest = {"repository_head": head,
                "generated_c_sha256": sha256(frozen), "instrumented_c_sha256": sha256(measured),
                "tool_sha256": sha256(tool), "tool": str(tool), "clang": clang,
                "clang_version": version.stdout, "compiler_flags": flags, "profile": profile,
                "runtime_hashes": {name: sha256(runtime / name) for name in
                    ("freak_runtime.c", "freak_llvm_runtime.c", "freak_runtime.h")},
                "runtime_objects": [str(obj) for obj in runtime_objects],
                "runtime_object_hashes": {str(obj): sha256(obj) for obj in runtime_objects},
                "runtime_symbols": sorted(symbols[0] | symbols[1]), "runtime_collisions": duplicates,
                "stage_peak_scope": "cumulative native Linux VmHWM; current RSS sampled inside compiler"}
    save_json(tool.with_suffix(".manifest.json"), manifest)
    return tool, manifest


def measure(build, tool, source, triple, timeout, memory, output, directory, profile):
    started = time.perf_counter()
    previous = os.environ.get("GMON_OUT_PREFIX")
    if profile:
        os.environ["GMON_OUT_PREFIX"] = str(directory / "gmon")
    try:
        result = guarded_job(build, [str(tool), str(source), triple], directory / "compile",
                             f"V4 benchmark {directory.name}", timeout, memory, output)
    finally:
        if previous is None:
            os.environ.pop("GMON_OUT_PREFIX", None)
        else:
            os.environ["GMON_OUT_PREFIX"] = previous
    elapsed = time.perf_counter() - started
    stages = {}
    stage_names = []
    pattern = r"^V4BENCH stage=(\w+) seconds=([\d.]+) rss_bytes=(\d+) peak_bytes=(\d+) diagnostics=(\d+)$"
    for match in re.finditer(pattern, result.stderr, re.M):
        name, seconds, rss, peak, diagnostics = match.groups()
        stage_names.append(name)
        stages[name] = {"seconds": float(seconds), "rss_mb": int(rss) / 1024**2,
                        "peak_rss_mb": int(peak) / 1024**2, "diagnostics": int(diagnostics)}
    peaks = re.findall(r"^V4BENCH final peak_bytes=(\d+)$", result.stderr, re.M)
    prefix, marker, module = result.stdout.partition("@@V4-MODULE\n")
    emitted = re.findall(r"^v4-build-stage=(\w+) diagnostics=(\d+)$", prefix, re.M)
    error = ""
    if result.returncode:
        error = f"compiler-exit-{result.returncode}"
    elif any(value["diagnostics"] for value in stages.values()) or any(int(d) for _, d in emitted):
        error = "diagnostics"
    elif stage_names != STAGES or [name for name, _ in emitted] != STAGES[:-1]:
        error = "incomplete-or-unordered-stages"
    elif len(peaks) != 1 or not marker or "@@V4-MODULE" in module or not module.startswith("target triple = "):
        error = "invalid-module-or-peak-record"
    elif "v4-errors=0\n" not in prefix:
        error = "missing-zero-error-record"
    row = {"status": error or "ok", "total": elapsed,
           "peak_rss_mb": int(peaks[0]) / 1024**2 if len(peaks) == 1 else None, "stages": stages}
    if not error:
        (directory / "module.ll").write_text(module, encoding="utf-8")
        row["module_sha256"] = sha256(directory / "module.ll")
    return row


def check_program(build, manifest, directory, expect_exit, expect_out, timeout):
    obj, exe = directory / "module.o", directory / "native"
    clang = manifest["clang"]
    result = guarded_job(build, [clang, "-w", "-O2", "-c", str(directory / "module.ll"),
                         "-o", str(obj)], directory / "native-compile", "LLVM native compile", timeout, 1024)
    require_success(result, "LLVM native compile")
    symbols = defined_symbols(build, obj, directory / "native-symbols", timeout)
    collisions = sorted(symbols & set(manifest["runtime_symbols"]))
    save_json(directory / "symbol-collisions.json", collisions)
    if collisions:
        return f"unexpected-symbol-collisions:{collisions}"
    command = [clang, str(obj), *manifest["runtime_objects"], "-o", str(exe),
               *build.checks.runtime_platform_final_link_args()]
    linked = guarded_job(build, command, directory / "native-link", "LLVM native link", timeout, 1024)
    require_success(linked, "LLVM native link")
    ran = guarded_job(build, [str(exe)], directory / "native-run", "LLVM native execute", 60, 128, 8)
    if (ran.returncode, ran.stdout, ran.stderr) != (expect_exit, expect_out, ""):
        return f"native-mismatch:exit={ran.returncode},stdout={ran.stdout!r},stderr={ran.stderr!r}"
    return "pass"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--work", type=Path, help="scratch directory (default build/v4_scale_bench)")
    parser.add_argument("--shapes", nargs="+", choices=list(GENERATORS), default=list(GENERATORS))
    parser.add_argument("--sizes", nargs="+", type=int, default=[200, 400, 800, 1600])
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--build-timeout", type=float, default=120)
    parser.add_argument("--mem-limit-mb", type=int, default=2048, help="compiler process-group RSS+swap ceiling in MiB")
    parser.add_argument("--output-limit-mb", type=int, default=64, help="per-stream capture ceiling in MiB")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--profile", action="store_true", help="collect whole-run gprof; profile timings are not benchmark timings")
    parser.add_argument("--json", type=Path)
    parser.add_argument("--tool", type=Path, help="reuse a frozen instrumented tool and adjacent manifest")
    args = parser.parse_args()
    if not sys.platform.startswith("linux"):
        parser.error("native RSS measurement currently supports Linux only")
    if (any(size <= 0 for size in args.sizes)
            or not all(math.isfinite(value) for value in (args.timeout, args.build_timeout))
            or min(args.timeout, args.build_timeout, args.mem_limit_mb, args.output_limit_mb) <= 0):
        parser.error("sizes and resource limits must be positive")
    repo = args.repo.resolve()
    os.chdir(repo)
    build = load_build(repo)
    work = (args.work or repo / "build/v4_scale_bench").resolve()
    work.mkdir(parents=True, exist_ok=True)
    results = []
    failed = False
    try:
        if args.tool:
            tool = args.tool.resolve()
            manifest = json.loads(tool.with_suffix(".manifest.json").read_text())
            if sha256(tool) != manifest["tool_sha256"] or bool(args.profile) != manifest["profile"]:
                raise RuntimeError("reused compiler hash/profile mode differs from manifest")
            for path, digest in manifest["runtime_object_hashes"].items():
                if sha256(Path(path)) != digest:
                    raise RuntimeError("frozen native runtime object changed")
        else:
            tool, manifest = build_tool(repo, work, args.profile, args.build_timeout, build)
        triple = build.host_target()
        for shape in args.shapes:
            print(f"\n== {shape} ==", flush=True)
            print("  size   lines    total peak MiB " + " ".join(f"{stage:>8}" for stage in STAGES) + "  check", flush=True)
            previous = None
            for size in args.sizes:
                directory = work / f"{shape}_{size}_{time.time_ns()}"
                directory.mkdir()
                text, expect_exit, expect_stdout = GENERATORS[shape](size)
                source = directory / "source.fk"
                source.write_text(text, encoding="utf-8")
                row = {"shape": shape, "size": size, "lines": text.count("\n"), "source_sha256": sha256(source),
                       "tool_manifest": str(tool.with_suffix(".manifest.json")),
                       "tool_manifest_sha256": sha256(tool.with_suffix(".manifest.json")),
                       "compiler_head": manifest.get("repository_head"),
                       "compiler_c_sha256": manifest.get("generated_c_sha256"),
                       "tool_sha256": manifest["tool_sha256"], "artifacts": str(directory),
                       "expected_exit": expect_exit, "expected_stdout": expect_stdout, "profile": args.profile}
                try:
                    row.update(measure(build, tool, source, triple, args.timeout, args.mem_limit_mb,
                                       args.output_limit_mb, directory, args.profile))
                    if row["status"] == "ok" and args.check:
                        row["check"] = check_program(build, manifest, directory, expect_exit, expect_stdout, args.build_timeout)
                        if row["check"] != "pass":
                            row["status"] = "native-check-failed"
                    if args.profile and row["status"] == "ok":
                        gprof = shutil.which("gprof")
                        profiles = list(directory.glob("gmon.*"))
                        if not gprof or len(profiles) != 1:
                            raise RuntimeError("expected exactly one gprof data file and an available gprof")
                        result = guarded_job(build, [gprof, "-b", str(tool), str(profiles[0])],
                                             directory / "gprof", "gprof report", 60, 512, 64)
                        require_success(result, "gprof")
                except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
                    row.update(status="failed", failure=str(error))
                results.append(row)
                save_json(directory / "result.json", row)
                save_json(args.json or work / "results.json", results)
                failed |= row["status"] != "ok"
                cells = " ".join(f"{row.get('stages', {}).get(stage, {}).get('seconds', float('nan')):8.3f}" for stage in STAGES)
                peak = row.get("peak_rss_mb")
                print(f"{size:6} {row['lines']:7} {row.get('total', float('nan')):8.3f} "
                      f"{peak if peak is not None else float('nan'):8.1f} {cells}  {row.get('check', row['status'])}", flush=True)
                if row["status"] != "ok":
                    print(row.get("failure", row["status"]), flush=True)
                    break
                if previous:
                    ratio = row["lines"] / previous["lines"]
                    growth = [f"{row['stages'][stage]['seconds'] / previous['stages'][stage]['seconds']:7.2f}x"
                              if previous["stages"][stage]["seconds"] > 0.02 else "       -" for stage in STAGES]
                    print(f"       {ratio:6.2f}x {row['total']/previous['total']:7.2f}x "
                          f"{row['peak_rss_mb']/previous['peak_rss_mb']:7.2f}x " + " ".join(growth), flush=True)
                previous = row
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        save_json(args.json or work / "results.json", {"status": "build-failed", "failure": str(error), "results": results})
        print(str(error), file=sys.stderr)
        return 1
    print("\nStage peaks are cumulative native Linux VmHWM; stages under 0.02 s are not growth-rated.", flush=True)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
