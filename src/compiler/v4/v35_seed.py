"""Build V4 tools with the native V3.5 compiler instead of Python freakc.

The chain has no Python compiler in it:

  build/freakc_v3.fk.c   committed C for an older V3 compiler (the seed)
        | clang
  seed V3                compiles the current V3 sources twice:
        |                generation 1 is built by the seed, generation 2
        |                by generation 1, so the result is current V3.5
  V3.5                   compiles the 22 V4 crates plus a tool entry
        |                (tools/build_llvm.fk, tools/lsp_server.fk, ...)
        |                to C in the V4 host profile
        |                (--bootstrap-compat=v4-host-bootstrap-v1)
        | clang
  the V4 tool

Python only drives the steps and caches the outputs. Each output is keyed
by the hash of everything that went into it, so an unchanged tree reuses it.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import sys

import check_v4 as checks

SEED_C = checks.ROOT / "build" / "freakc_v3.fk.c"
# The V3 compiler, in the order the CLI build concatenates it
# (packaging/cli-sources.manifest without the CLI files).
V3_SOURCES = tuple(checks.ROOT / "src" / "compiler" / "v3" / name for name in (
    "globals.fk", "helpers.fk", "lexer.fk", "parser.fk",
    "checker.fk", "emit_c.fk", "emit_llvm.fk", "main.fk",
))
HOST_PROFILE = "--bootstrap-compat=v4-host-bootstrap-v1"
EXE = ".exe" if sys.platform.startswith("win") else ""
# The generated C uses these constructs on purpose; -w keeps the logs short.
C_FLAGS = ("-w", "-D_CRT_SECURE_NO_WARNINGS")


def work_root() -> Path:
    return checks.RUNTIME_BUILD_ROOT / "v35_seed"


def _label(path: Path) -> str:
    try:
        return checks.rel(path.resolve())
    except ValueError:
        return str(path)


def _digest(*parts: bytes | str) -> str:
    sha = hashlib.sha256()
    for part in parts:
        data = part.encode("utf-8") if isinstance(part, str) else part
        sha.update(len(data).to_bytes(8, "little"))
        sha.update(data)
    return sha.hexdigest()


def _runtime_c() -> Path:
    return checks.RUNTIME_ROOT / "freak_runtime.c"


def _runtime_key() -> str:
    # The runtime header and C are inputs of every stage.
    return _digest(*(path.read_bytes() for path in sorted(checks.RUNTIME_ROOT.glob("freak_runtime.*"))))


def _cached(stamp: Path, output: Path, key: str) -> bool:
    try:
        return output.is_file() and stamp.read_text(encoding="utf-8").strip() == key
    except OSError:
        return False


def _run(command: list[str], label: str, timeout: int = 900, memory_mb: int = 4096) -> None:
    result = checks.run_with_heartbeat(command, label=label, timeout_seconds=timeout,
                                       memory_limit_mb=memory_mb)
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed (exit {result.returncode}):\n"
                           f"{result.stdout[-8000:]}{result.stderr[-8000:]}")


def _clang_c(clang: str, sources: list[Path], output: Path, opt: int, label: str,
             extra: tuple[str, ...] = (), libraries: tuple[str, ...] = ()) -> None:
    command = [clang, f"-O{opt}", *C_FLAGS, *extra, *(str(path) for path in sources),
               f"-I{checks.RUNTIME_ROOT}", "-o", str(output),
               *checks.runtime_platform_final_link_args(), *libraries]
    _run(command, label, timeout=900, memory_mb=4096)


def v35_compiler(clang: str) -> Path:
    """The current V3.5 compiler, built from the committed seed C."""
    work = work_root() / "v3"
    work.mkdir(parents=True, exist_ok=True)
    aggregate_text = b"".join(path.read_bytes() for path in V3_SOURCES)
    key = _digest("v35-compiler-v1", clang, SEED_C.read_bytes(), aggregate_text, _runtime_key())
    compiler = work / f"freakc_v35{EXE}"
    stamp = work / "freakc_v35.sha256"
    if _cached(stamp, compiler, key):
        return compiler
    seed = work / f"freakc_seed{EXE}"
    _clang_c(clang, [SEED_C, _runtime_c()], seed, 2, "V3 seed compile")
    aggregate = work / "freakc_v3.fk"
    aggregate.write_bytes(aggregate_text)
    previous = seed
    for generation in (1, 2):
        emitted = work / "freakc_v3.fk.c"
        emitted.unlink(missing_ok=True)
        # V3 writes <input>.c next to its input.
        _run([str(previous), str(aggregate), "--c"], f"V3.5 generation {generation} transpile")
        stage_c = work / f"freakc_gen{generation}.c"
        shutil.copyfile(emitted, stage_c)
        stage = work / f"freakc_gen{generation}{EXE}"
        _clang_c(clang, [stage_c, _runtime_c()], stage, 2, f"V3.5 generation {generation} compile")
        previous = stage
    shutil.copyfile(previous, compiler)
    compiler.chmod(0o755)
    stamp.write_text(key, encoding="utf-8")
    return compiler


def tool_source(entry: Path) -> str:
    """The V4 crates in CRATE_ORDER, then the tool entry (as the old fixture host built it)."""
    return checks.fixture_source(checks.flattened_crates(), entry)


def build_tool(clang: str, entry: Path, name: str, opt: int = 0,
               extra: tuple[str, ...] = (), extra_sources: tuple[Path, ...] = (),
               libraries: tuple[str, ...] = (), source: str | None = None,
               key_files: tuple[Path, ...] = ()) -> Path:
    """Compile the crates plus entry with V3.5 and link a native V4 tool.

    source replaces the entry text when a caller patches the entry first.
    key_files are other inputs (such as an -include header) whose bytes must
    invalidate the cached tool."""
    compiler = v35_compiler(clang)
    work = work_root() / name
    work.mkdir(parents=True, exist_ok=True)
    text = tool_source(entry) if source is None else source
    inputs = [path.read_bytes() for path in (*extra_sources, *key_files)]
    key = _digest("v35-tool-v1", clang, compiler.read_bytes(), text, _runtime_key(), str(opt),
                  *extra, *libraries, *inputs)
    output = work / f"{name}{EXE}"
    stamp = work / f"{name}.sha256"
    if _cached(stamp, output, key):
        return output
    flat = work / f"{name}.fk"
    flat.write_text(text, encoding="utf-8", newline="\n")
    emitted = work / f"{name}.fk.c"
    emitted.unlink(missing_ok=True)
    _run([str(compiler), str(flat), "--c", HOST_PROFILE], f"V3.5 transpile: {_label(entry)}")
    if not emitted.is_file():
        raise RuntimeError(f"V3.5 wrote no C for {_label(entry)}")
    output.unlink(missing_ok=True)
    _clang_c(clang, [emitted, _runtime_c(), *extra_sources], output, opt,
             f"V4 tool compile: {name}", extra, libraries)
    stamp.write_text(key, encoding="utf-8")
    return output
