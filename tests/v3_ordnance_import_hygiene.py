#!/usr/bin/env python3
"""Check declaration-only package loading without claiming graph resolution."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import sys
import tempfile

import v3_word_foundation as foundation


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("freak", type=Path)
    parser.add_argument("--runtime-root", type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo))
    from freakc.lexer import Lexer
    from freakc.parser import ImplBlock, Parser, ShapeDecl, TaskDecl

    library = repo / "packages/muvluv/src/muvluv.fk"
    source_text = library.read_text(encoding="utf-8")
    statements = Parser(Lexer(source_text).tokenize()).parse().statements
    assert statements, "empty library would vacuously pass import checks"
    assert all(isinstance(item, (ShapeDecl, ImplBlock, TaskDecl)) for item in statements), (
        "package must not have executable top-level statements"
    )
    assert all(not isinstance(item, TaskDecl) or item.name != "main" for item in statements)
    assert (repo / "packages/muvluv/examples/beta_early_warning.fk").is_file()

    # Use a real consumer: an empty entrypoint would miss a silently ignored
    # package. Direct assembly is deliberate until Hangar graph loading lands.
    consumer = '''
task main() {
    if required_power(1) != 10 { process::exit(1) }
    if required_power(7) != 9999 { process::exit(2) }
    if required_power(0) != 0 { process::exit(3) }
    if tier_name(5) != "Laser" { process::exit(4) }
    if tier_name(9) != "Unknown" { process::exit(5) }
    if tier_threat(1) != "MODERATE" { process::exit(6) }
    if tier_threat(3) != "HIGH" { process::exit(7) }
    if tier_threat(5) != "CRITICAL" { process::exit(8) }
    if tier_threat(7) != "EXTINCTION" { process::exit(9) }
}
'''
    clang = os.environ.get("FREAK_CLANG") or shutil.which("clang")
    assert clang, "Clang is required"
    runtime = args.runtime_root.resolve() if args.runtime_root else repo / "freakc/runtime"
    with tempfile.TemporaryDirectory(prefix="freak-v3-import-hygiene-") as temporary:
        root = Path(temporary)
        source = root / "muvluv_consumer.fk"
        source.write_text(source_text + consumer, encoding="utf-8")
        generated, _ = foundation.transpile(
            freak=args.freak.resolve(), repo=repo, source=source, backend="llvm"
        )
        binary = root / ("consumer.exe" if sys.platform == "win32" else "consumer")
        foundation.compile_generated(
            clang=clang, repo=repo, runtime_root=runtime, generated=generated,
            backend="llvm", binary=binary,
        )
        executed = foundation.run([str(binary)], root, foundation.sanitizer_env())
        assert executed.returncode == 0, executed.stdout + executed.stderr
        assert executed.stdout == "", executed.stdout
        # No builder/buffer/repetition activity means the lazy statistics
        # reporter is never registered. Both output streams must stay silent.
        assert executed.stderr == "", executed.stderr
    print("V3 Ordnance declaration-only initialization: PASS (LLVM)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
