"""Build freak-lsp, the Maverick (V4) language server.

The server is the V4 crates plus tools/lsp_server.fk, compiled to C by the
native V3.5 compiler like every other V4 tool (see v35_seed.py), and linked
with the C runtime and the byte-exact stdio helpers in tools/lsp_stdio.c.

    python src/compiler/v4/build_lsp.py -o build/freak-lsp
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import check_v4 as checks
import v35_seed

SERVER = checks.V4_ROOT / "tools" / "lsp_server.fk"
STDIO_C = checks.V4_ROOT / "tools" / "lsp_stdio.c"
STDIO_H = checks.V4_ROOT / "tools" / "lsp_stdio.h"


def default_output() -> Path:
    suffix = ".exe" if sys.platform.startswith("win") else ""
    return checks.ROOT / "build" / f"freak-lsp{suffix}"


def build(clang: str, output: Path, opt: int) -> None:
    built = v35_seed.build_tool(
        clang, SERVER, "freak-lsp", opt=opt,
        extra=("-include", str(STDIO_H)), extra_sources=(STDIO_C,), key_files=(STDIO_H,),
        libraries=("-lpsapi",) if sys.platform.startswith("win") else (),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    if built.resolve() != output.resolve():
        shutil.copy2(built, output)


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
