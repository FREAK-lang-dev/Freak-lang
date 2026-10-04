#!/usr/bin/env python3
"""Run the authored Unicode17 lowercase vertical at O0/O2/O3.

ASan and UBSan are required by default; --plain is an additional portability
proof. Each compiler process keeps the existing64MiB/1024-handle contract.
Generated LLVM, binaries and exact results remain in the ignored build tree.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import subprocess

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src/compiler/v4"), str(ROOT / "tests")]
import build_v4 as build  # noqa: E402
from v4_owned_word_codegen import assert_native_output  # noqa: E402
from freakc.v4_native_runtime import HEADER_NAMES  # noqa: E402

OPTIMIZATIONS = (0, 2, 3)
EXPECTED = (
    "A\0B\na\0b\na\0b\n3\n3\n\ni\u0307\nος\nοσα\nος\u0301\n"
    "𐐨\ntemp\nnested\nalready lower\nalready lower\nloop\n"
)
PREFIX = "word-lower-execute stages=clean v8-restore=true old-seal=true fresh-module=true\n"


def extract_module(result, *, platform: str | None = None) -> str:
    platform = sys.platform if platform is None else platform
    stdout = result.stdout.replace("\r\n", "\n") if platform == "win32" else result.stdout
    if result.returncode != 0 or result.stderr:
        raise RuntimeError(f"lowercase compiler failed: {result.returncode}, {result.stderr!r}")
    begin = "@@LLVM-MODULE-BEGIN\n"
    end = "@@LLVM-MODULE-END\n"
    if not stdout.startswith(PREFIX + begin) or not stdout.endswith(end):
        raise RuntimeError("lowercase compiler protocol mismatch")
    if stdout.count(begin) != 1 or stdout.count(end) != 1:
        raise RuntimeError("lowercase compiler module markers must occur exactly once")
    module = stdout[len(PREFIX + begin):-len(end)]
    if not module.strip() or "call i64 @freak_v4_word_to_lower(i64 " not in module:
        raise RuntimeError("lowercase module is empty or has no actual closed runtime call")
    return module


def assert_complete(results: list[dict]) -> None:
    if len(results) != len(OPTIMIZATIONS):
        raise RuntimeError("lowercase optimization matrix is incomplete")
    if {row.get("optimization") for row in results} != set(OPTIMIZATIONS):
        raise RuntimeError("lowercase optimization matrix has duplicates or missing levels")
    for row in results:
        if row.get("status") != "pass" or row.get("ownership_audits") != ["C", "LLVM"]:
            raise RuntimeError("lowercase result lacks a passing exact oracle or both audits")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG") or shutil.which("clang"))
    parser.add_argument("--plain", action="store_true")
    parser.add_argument("--work", type=Path, default=ROOT / "build/v4_smoke/word_lower_native")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if not args.clang:
        parser.error("clang is required; lowercase execution cannot be skipped")
    checks = build.checks
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    checks.RUNTIME_BUILD_ROOT = work / "compiler"
    checks.RUNTIME_BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    fixture = checks.V4_ROOT / "tests/word_lower_execute_smoke.fk"
    example = checks.V4_ROOT / "examples/word_lowercase.fk"
    if not fixture.is_file() or not example.is_file():
        raise RuntimeError("required lowercase fixture/example is unavailable")
    source, ui = checks.transpile_fixture(checks.check_flattened_crates(), fixture)
    if ui:
        raise RuntimeError("lowercase compiler fixture unexpectedly requires UI")
    runtime = checks.RUNTIME_ROOT / "freak_runtime.c"
    compiler, _ = checks.compile_runtime_smoke(
        args.clang, f"-I{checks.RUNTIME_ROOT}", runtime, checks.read_text(runtime),
        fixture, source, ("-DFREAK_ARRAY_LIVE_LIMIT=1024",),
    )
    target = build.host_target()
    emitted = checks.run_with_heartbeat(
        [str(compiler), str(example), target], label="lowercase native emission/restore",
        timeout_seconds=60, memory_limit_mb=64,
    )
    (work / "compiler.stdout").write_bytes(emitted.stdout.encode("utf-8"))
    (work / "compiler.stderr").write_bytes(emitted.stderr.encode("utf-8"))
    module = extract_module(emitted)
    llvm = work / "word_lowercase.ll"
    llvm.write_bytes(module.encode("utf-8"))
    report = {"target": target, "sanitizers": not args.plain,
              "source_sha256": hashlib.sha256(example.read_bytes()).hexdigest(),
              "module_sha256": hashlib.sha256(llvm.read_bytes()).hexdigest(),
              "compiler_fixture_sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
              "compiler_assembly_sha256": hashlib.sha256(Path(checks.__file__).read_bytes()).hexdigest(),
              "compiler_crate_inputs": {name: hashlib.sha256(checks.crate_path(name).read_bytes()).hexdigest() for name in checks.CRATE_ORDER},
              "compiler_process_contract": {"memory_limit_mib": 64, "live_handle_limit": 1024},
              "compiler_binary_sha256": hashlib.sha256(compiler.read_bytes()).hexdigest(),
              "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "runtime_sources": {name: hashlib.sha256((checks.RUNTIME_ROOT / name).read_bytes()).hexdigest() for name in build.SOURCE_NAMES},
              "runtime_headers": {name: hashlib.sha256((checks.RUNTIME_ROOT / name).read_bytes()).hexdigest() for name in HEADER_NAMES},
              "programs": []}
    git = shutil.which("git")
    if git:
        head = subprocess.run([git, "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
        report["compiler_head"] = head.stdout.strip() if head.returncode == 0 else None
    variables = ("ASAN_OPTIONS", "LSAN_OPTIONS", "UBSAN_OPTIONS")
    previous = {name: os.environ.get(name) for name in variables}
    try:
        for name in variables:
            os.environ.pop(name, None)
        if not args.plain:
            os.environ["ASAN_OPTIONS"] = "halt_on_error=1:detect_leaks=1:exitcode=86"
            os.environ["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1:exitcode=85"
        for optimization in OPTIMIZATIONS:
            binary = work / f"word_lowercase-O{optimization}{'.exe' if sys.platform == 'win32' else '.native'}"
            command = build.native_link_command(args.clang, llvm, binary)
            command = [f"-O{optimization}" if re.fullmatch(r"-O[0-3]", token) else token for token in command]
            command += ["-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1", "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1"]
            if not args.plain:
                command += ["-g", "-fsanitize=address,undefined", "-fno-omit-frame-pointer"]
            linked = checks.run_with_heartbeat(command, label=f"lowercase link O{optimization}",
                                              timeout_seconds=120, memory_limit_mb=512)
            (work / f"link-O{optimization}.stdout").write_bytes(linked.stdout.encode())
            (work / f"link-O{optimization}.stderr").write_bytes(linked.stderr.encode())
            if linked.returncode != 0 or linked.stdout or linked.stderr:
                raise RuntimeError(f"lowercase link O{optimization} failed: {linked.returncode}, {linked.stdout!r}, {linked.stderr!r}")
            native = checks.run_with_heartbeat([str(binary)], label=f"lowercase execute O{optimization}",
                                              timeout_seconds=30, memory_limit_mb=128)
            (work / f"native-O{optimization}.stdout").write_bytes(native.stdout.encode())
            (work / f"native-O{optimization}.stderr").write_bytes(native.stderr.encode())
            actual = assert_native_output(native, EXPECTED)
            report["programs"].append({"optimization": optimization, "status": "pass",
                "ownership_audits": ["C", "LLVM"], "exit": native.returncode,
                "link_command": command, "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                "stdout_sha256": hashlib.sha256(actual.encode()).hexdigest()})
            print(f"lowercase O{optimization}: exact UTF-8/NUL output, both ownership audits "
                  + ("plain PASS" if args.plain else "ASan+UBSan PASS"), flush=True)
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
    assert_complete(report["programs"])
    report_path = args.report or work / "report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
