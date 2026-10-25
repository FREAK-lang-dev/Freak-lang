"""Bootstrap V4, emit an LLVM module, and optionally link a native program."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import platform
import re
import shutil
import sys
import tempfile

import check_v4 as checks

from freakc.v4_native_runtime import SOURCE_NAMES


def v35_seed_module():
    """v35_seed, imported on first use.

    Gates that load this file through a frozen-source importer and never
    build the compiler must not need v35_seed in their closure. Loaders that
    import this file by path may not have its directory on sys.path."""
    if "v35_seed" not in sys.modules:
        here = str(Path(__file__).resolve().parent)
        if here not in sys.path:
            sys.path.insert(0, here)
    import v35_seed
    # Share this file's check_v4, which tests may have loaded under another name.
    v35_seed.checks = checks
    return v35_seed


# Multi-file builds swap this for a map back to each original source.
annotate_diagnostics = lambda text: text


def require_distinct_output(source: Path, output: Path) -> None:
    """Reject canonical-path and physical-file aliases before modifying output."""
    try:
        aliases = source.resolve() == output.resolve()
        source_metadata = source.stat()
        try:
            output_metadata = output.stat()
        except FileNotFoundError:
            output_metadata = None
        if aliases or (output_metadata is not None and os.path.samestat(source_metadata, output_metadata)):
            raise RuntimeError(f"output aliases source file: {output}")
    except OSError as exc:
        raise RuntimeError(f"could not establish source/output identity: {exc}") from exc


def native_link_command(clang: str, llvm_path: Path, output: Path) -> list[str]:
    # Compiler-private V4 helpers supplement the existing adapter/core runtime.
    return [clang, "-w", "-O2", str(llvm_path),
            *(str(checks.RUNTIME_ROOT / name) for name in SOURCE_NAMES),
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


# A prebuilt V4 compiler (for example the self-built stage 1 from
# self_host.py) replaces the V3.5-built one for every build and check.
COMPILER_ENV = "FREAK_V4_COMPILER"


def prebuilt_compiler() -> Path | None:
    value = os.environ.get(COMPILER_ENV, "")
    if not value:
        return None
    path = Path(value).resolve()
    if not path.is_file() or not os.access(path, os.X_OK):
        raise RuntimeError(f"{COMPILER_ENV} is not an executable file: {value}")
    return path


def bootstrap(clang: str, compiler_opt: int = 0, allow_prebuilt: bool = True) -> Path:
    """The V4 compiler: the prebuilt one when set, else built by V3.5.

    V3.5 is itself built from the committed seed C (see v35_seed.py), so no
    Python compiler is involved. allow_prebuilt=False always builds it
    (self_host.py's stage 0)."""
    prebuilt = prebuilt_compiler() if allow_prebuilt else None
    if prebuilt is not None:
        return prebuilt
    entry = checks.V4_ROOT / "tools" / "build_llvm.fk"
    name = f"freak_v4_compiler_O{compiler_opt}" if compiler_opt else "freak_v4_compiler"
    return v35_seed_module().build_tool(clang, entry, name, opt=compiler_opt)


def emit_module(compiler: Path, source: Path, target: str, panic: str = "unwind",
                root_mode: str = "strict") -> str:
    if panic not in ("unwind", "abort"):
        raise RuntimeError(f"unsupported V4 panic policy: {panic}")
    if root_mode not in ("strict", "bootstrap"):
        raise RuntimeError(f"unsupported V4 root mode: {root_mode}")
    command = [str(compiler), str(source.resolve()), target]
    if panic != "unwind" or root_mode != "strict":
        command.append(panic)
    if root_mode != "strict":
        command.append(root_mode)
    result = checks.run_with_heartbeat(
        command,
        label=f"V4 compile: {source.name}", timeout_seconds=900,
        memory_limit_mb=2048,
    )
    markers = list(re.finditer(r"^@@V4-MODULE\r?\n", result.stdout, re.MULTILINE))
    if result.returncode != 0 or len(markers) != 1:
        raise RuntimeError(f"V4 compilation failed:\n{result.stdout}{result.stderr}")
    marker = markers[0]
    prefix = result.stdout[:marker.start()]
    module = result.stdout[marker.end():]
    print(annotate_diagnostics(prefix.strip()))
    return module


class FlattenedSource:
    """Several sources joined in order, with a byte map back to each file."""

    def __init__(self, paths: list[Path]):
        self.paths = paths
        self.starts: list[int] = []
        self.texts: list[bytes] = []
        parts: list[bytes] = []
        offset = 0
        for path in paths:
            data = path.read_bytes()
            if not data.endswith(b"\n"):
                data += b"\n"
            self.starts.append(offset)
            self.texts.append(data)
            parts.append(data)
            offset += len(data)
        self.data = b"".join(parts)

    def locate(self, offset: int) -> str:
        index = 0
        while index + 1 < len(self.starts) and self.starts[index + 1] <= offset:
            index += 1
        local = offset - self.starts[index]
        text = self.texts[index][:local]
        line = text.count(b"\n") + 1
        column = local - (text.rfind(b"\n") + 1) + 1
        return f"{display_path(self.paths[index])}:{line}:{column}"

    def annotate(self, output: str) -> str:
        """Follow every diagnostic record with its original file:line:col."""
        lines = []
        for line in output.splitlines():
            lines.append(line)
            match = re.match(r"^\d+\|\d+@(\d+):\d+\|", line)
            if match:
                lines.append("  --> " + self.locate(int(match.group(1))))
        return "\n".join(lines) + ("\n" if output.endswith("\n") else "")


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(checks.repo_root()).as_posix()
    except ValueError:
        return str(path)


def compiler_sources(entry: Path) -> list[Path]:
    """The V4 crates in CRATE_ORDER, then the entry tool (self-hosting input)."""
    return [*checks.crate_paths(), entry]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, nargs="+",
                        help="one source, or several flattened in the given order")
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--emit-llvm", action="store_true", help="write .ll without linking")
    parser.add_argument("--target", default=None, help="canonical freak_target triple")
    parser.add_argument("--compiler-opt", type=int, choices=(0, 1, 2, 3), default=0,
                        help="bootstrap compiler optimization level (default: 0)")
    parser.add_argument("--compiler", type=Path, default=None,
                        help=f"use this prebuilt V4 compiler instead of building one with Python "
                             f"(same as setting {COMPILER_ENV})")
    parser.add_argument("--panic", choices=("unwind", "abort"), default="unwind",
                        help="program panic policy (default: unwind, which ends main as panicked with exit status 101; abort raises SIGABRT)")
    parser.add_argument("--bootstrap-root", action="store_true",
                        help="parse this file in bootstrap compatibility mode: V3 root pilot "
                             "globals and root statements (default: strict root scope, bible 17.4)")
    parser.add_argument("--with-crates", action="store_true",
                        help="prepend the V4 crates in CRATE_ORDER (bootstrap-sources.manifest) "
                             "to the sources; implies --bootstrap-root")
    args = parser.parse_args()
    if args.compiler is not None:
        os.environ[COMPILER_ENV] = str(args.compiler)
    clang = shutil.which("clang")
    if clang is None:
        parser.error("clang is required")
    for source in args.source:
        if not source.is_file():
            parser.error(f"source file does not exist: {source}")
    sources = list(args.source)
    if args.with_crates:
        sources = [*checks.crate_paths(), *sources]
        args.bootstrap_root = True
    try:
        # Every original source, not only the build input, must survive the build.
        for source in sources:
            require_distinct_output(source, args.output)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    flattened = None
    if len(sources) > 1:
        # Real module loading is later work; until then the build input is
        # one file, and diagnostics map back to each original source. Each
        # build gets its own flat file, so concurrent builds never share one.
        flattened = FlattenedSource(sources)
        flat_root = checks.RUNTIME_BUILD_ROOT / "flatten"
        flat_root.mkdir(parents=True, exist_ok=True)
        handle, flat_name = tempfile.mkstemp(prefix=args.output.name + ".", suffix=".flat.fk", dir=flat_root)
        args.source = Path(flat_name)
        with os.fdopen(handle, "wb") as flat_file:
            flat_file.write(flattened.data)
        global annotate_diagnostics
        annotate_diagnostics = flattened.annotate
        print(f"v4-flattened sources={len(sources)} bytes={len(flattened.data)} input={args.source}")
    else:
        args.source = sources[0]
    try:
        return build(args, parser, clang, flattened, sources)
    finally:
        if flattened is not None and not os.environ.get("FREAK_V4_KEEP_FLAT"):
            args.source.unlink(missing_ok=True)


def build(args: argparse.Namespace, parser: argparse.ArgumentParser, clang: str, flattened: FlattenedSource | None,
          sources: list[Path]) -> int:
    target = args.target or host_target()
    if not args.emit_llvm and target != host_target():
        parser.error("native linking currently supports the host TargetSpec; use --emit-llvm for cross targets")
    try:
        require_distinct_output(args.source, args.output)
        # A prebuilt compiler must survive the build too.
        prebuilt = prebuilt_compiler()
        if prebuilt is not None:
            require_distinct_output(prebuilt, args.output)
        compiler = bootstrap(clang, args.compiler_opt)
        root_mode = "bootstrap" if args.bootstrap_root else "strict"
        if root_mode != "strict":
            module = emit_module(compiler, args.source, target, args.panic, root_mode=root_mode)
        elif args.panic == "unwind":
            module = emit_module(compiler, args.source, target)
        else:
            module = emit_module(compiler, args.source, target, args.panic)
        # Compilation can take time; recheck an output that changed after the
        # initial preflight before creating directories, writing or linking.
        require_distinct_output(args.source, args.output)
        for source in sources:
            require_distinct_output(source, args.output)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.emit_llvm:
            llvm_path = args.output
            llvm_path.write_bytes(module.encode("utf-8"))
            with tempfile.TemporaryDirectory(prefix="freak-v4-verify-") as temporary:
                result = checks.run_with_heartbeat(
                    [clang, "--target=" + target, "-x", "ir", "-c", str(llvm_path),
                     "-o", str(Path(temporary) / "module.o")],
                    label="V4 LLVM verification", timeout_seconds=120, memory_limit_mb=1024,
                )
                if result.returncode != 0:
                    raise RuntimeError(f"LLVM verification failed:\n{result.stdout}{result.stderr}")
        if not args.emit_llvm:
            # Keep linker input separate from every requested output name,
            # including .ll and .LL executable paths on Windows.
            with tempfile.TemporaryDirectory(prefix="freak-v4-link-") as temporary:
                llvm_path = Path(temporary) / "module.ll"
                llvm_path.write_bytes(module.encode("utf-8"))
                result = checks.run_with_heartbeat(
                    native_link_command(clang, llvm_path, args.output),
                    label="V4 native link", timeout_seconds=120, memory_limit_mb=1024,
                )
            if result.returncode != 0:
                raise RuntimeError(f"LLVM native link failed:\n{result.stdout}{result.stderr}")
        print(f"built {args.output}")
    except RuntimeError as exc:
        message = str(exc)
        if flattened is not None:
            message = flattened.annotate(message)
        print(message, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
