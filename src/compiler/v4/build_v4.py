"""Bootstrap V4, emit an LLVM module, and optionally link a native program."""
from __future__ import annotations

import argparse
from pathlib import Path
import platform
import re
import shutil
import sys
import tempfile

import check_v4 as checks


def native_link_command(clang: str, llvm_path: Path, output: Path) -> list[str]:
    # Match the shipping LLVM CLI: the adapter and core runtime are both needed.
    return [clang, "-w", "-O2", str(llvm_path),
            str(checks.RUNTIME_ROOT / "freak_llvm_runtime.c"),
            str(checks.RUNTIME_ROOT / "freak_runtime.c"),
            f"-I{checks.RUNTIME_ROOT}", "-o", str(output),
            *checks.runtime_platform_final_link_args()]


def host_target() -> str:
    machine = platform.machine().lower()
    if sys.platform == "linux" and machine in ("x86_64", "amd64"):
        return "x86_64-unknown-linux-gnu"
    if sys.platform == "linux" and machine in ("aarch64", "arm64"):
        return "aarch64-unknown-linux-gnu"
    if sys.platform == "darwin" and machine in ("aarch64", "arm64"):
        return "aarch64-apple-darwin"
    if sys.platform == "win32" and machine in ("x86_64", "amd64"):
        return "x86_64-w64-windows-gnu"
    raise RuntimeError(f"no V4 TargetSpec for {sys.platform}/{machine}")


def bootstrap(clang: str, compiler_opt: int = 0) -> Path:
    fixture = checks.V4_ROOT / "tools" / "build_llvm.fk"
    c_source, uses_ui = checks.transpile_fixture(checks.flattened_crates(), fixture)
    if uses_ui:
        raise RuntimeError("V4 bootstrap unexpectedly requires UI")
    runtime = checks.RUNTIME_ROOT / "freak_runtime.c"
    # Optimized compiler builds have separate artifacts from the O0 smoke
    # harness. The shared compiler cache already includes extra compiler flags.
    smoke_build_root = checks.RUNTIME_BUILD_ROOT
    if compiler_opt:
        checks.RUNTIME_BUILD_ROOT = smoke_build_root / f"compiler_O{compiler_opt}"
    try:
        checks.RUNTIME_BUILD_ROOT.mkdir(parents=True, exist_ok=True)
        executable, _ = checks.compile_runtime_smoke(
            clang, f"-I{checks.RUNTIME_ROOT}", runtime,
            checks.read_text(runtime), fixture, c_source,
            (f"-O{compiler_opt}",) if compiler_opt else (),
        )
    finally:
        checks.RUNTIME_BUILD_ROOT = smoke_build_root
    return executable


def emit_module(compiler: Path, source: Path, target: str) -> str:
    result = checks.run_with_heartbeat(
        [str(compiler), str(source.resolve()), target],
        label=f"V4 compile: {source.name}", timeout_seconds=900,
        memory_limit_mb=2048,
    )
    markers = list(re.finditer(r"^@@V4-MODULE\r?\n", result.stdout, re.MULTILINE))
    if result.returncode != 0 or len(markers) != 1:
        raise RuntimeError(f"V4 compilation failed:\n{result.stdout}{result.stderr}")
    marker = markers[0]
    prefix = result.stdout[:marker.start()]
    module = result.stdout[marker.end():]
    print(prefix.strip())
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--emit-llvm", action="store_true", help="write .ll without linking")
    parser.add_argument("--target", default=None, help="canonical freak_target triple")
    parser.add_argument("--compiler-opt", type=int, choices=(0, 1, 2, 3), default=0,
                        help="bootstrap compiler optimization level (default: 0)")
    args = parser.parse_args()
    clang = shutil.which("clang")
    if clang is None:
        parser.error("clang is required")
    if not args.source.is_file():
        parser.error(f"source file does not exist: {args.source}")
    target = args.target or host_target()
    if not args.emit_llvm and target != host_target():
        parser.error("native linking currently supports the host TargetSpec; use --emit-llvm for cross targets")
    try:
        module = emit_module(bootstrap(clang, args.compiler_opt), args.source, target)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        llvm_path = args.output if args.emit_llvm else args.output.with_suffix(".ll")
        llvm_path.write_bytes(module.encode("utf-8"))
        if args.emit_llvm:
            with tempfile.TemporaryDirectory(prefix="freak-v4-verify-") as temporary:
                result = checks.run_with_heartbeat(
                    [clang, "--target=" + target, "-x", "ir", "-c", str(llvm_path),
                     "-o", str(Path(temporary) / "module.o")],
                    label="V4 LLVM verification", timeout_seconds=120, memory_limit_mb=1024,
                )
                if result.returncode != 0:
                    raise RuntimeError(f"LLVM verification failed:\n{result.stdout}{result.stderr}")
        if not args.emit_llvm:
            result = checks.run_with_heartbeat(
                native_link_command(clang, llvm_path, args.output),
                label="V4 native link", timeout_seconds=120, memory_limit_mb=1024,
            )
            if result.returncode != 0:
                raise RuntimeError(f"LLVM native link failed:\n{result.stdout}{result.stderr}")
        print(f"built {args.output}")
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
