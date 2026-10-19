"""Build freak-lsp, the Maverick (V4) language server.

The server is the V4 crates plus tools/lsp_server.fk, transpiled by the
bootstrap toolchain like every other V4 tool, and linked with the C runtime
and the byte-exact stdio helpers in tools/lsp_stdio.c.

    python src/compiler/v4/build_lsp.py -o build/freak-lsp
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import check_v4 as checks

SERVER = checks.V4_ROOT / "tools" / "lsp_server.fk"
STDIO_C = checks.V4_ROOT / "tools" / "lsp_stdio.c"
STDIO_H = checks.V4_ROOT / "tools" / "lsp_stdio.h"


def default_output() -> Path:
    suffix = ".exe" if sys.platform.startswith("win") else ""
    return checks.ROOT / "build" / f"freak-lsp{suffix}"


def build(clang: str, output: Path, opt: int) -> None:
    c_source, uses_ui = checks.transpile_fixture(checks.flattened_crates(), SERVER)
    if uses_ui:
        raise RuntimeError("freak-lsp unexpectedly requires UI")
    output.parent.mkdir(parents=True, exist_ok=True)
    c_path = output.parent / "freak-lsp.fk.c"
    checks.write_text_if_changed(c_path, c_source)
    command = [
        clang, "-w", f"-O{opt}",
        "-include", str(STDIO_H),
        str(c_path),
        str(checks.RUNTIME_ROOT / "freak_runtime.c"),
        str(STDIO_C),
        f"-I{checks.RUNTIME_ROOT}",
        "-o", str(output),
        *checks.runtime_platform_final_link_args(),
        *(("-lpsapi",) if sys.platform.startswith("win") else ()),
    ]
    result = checks.run_with_heartbeat(
        command, label="freak-lsp compile", timeout_seconds=900, memory_limit_mb=2048,
    )
    if result.returncode != 0:
        raise RuntimeError(f"freak-lsp compile failed:\n{result.stdout}{result.stderr}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-o", "--output", type=Path, default=None)
    parser.add_argument("--opt", type=int, choices=(0, 1, 2, 3), default=2,
                        help="C optimization level for the server (default: 2)")
    args = parser.parse_args()
    clang = shutil.which("clang")
    if clang is None:
        parser.error("clang is required")
    output = args.output or default_output()
    try:
        build(clang, output, args.opt)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"built {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
