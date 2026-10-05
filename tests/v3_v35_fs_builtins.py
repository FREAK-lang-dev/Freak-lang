#!/usr/bin/env python3
"""Check native compiler signatures and actual calls for filesystem result tickets.

Runtime behavior, OS errors and publication atomicity have separate execution
gates. This gate verifies the public compiler boundary and owner consumption.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import tempfile

from v3_checked_parsing import build_stage2
from v3_v35_language import require_ok, run


PROGRAM = '''task main() {
    pilot text: int = fs::read_ticket("path")
    pilot binary: int = fs::read_bytes_ticket("path")
    pilot source: int = fs::read_source_ticket("path")
    pilot bytes: ByteBuffer = ByteBuffer::new()
    pilot write: int = fs::write_checked("path", "text")
    pilot write_bytes: int = fs::write_bytes_checked("path", bytes)
    pilot append: int = fs::append_checked("path", "text")
    pilot rename: int = fs::rename_checked("old", "new")
    pilot publish: int = fs::rename_new_checked("old", "new")
    pilot mkdir: int = fs::mkdir_checked("path")
    pilot remove: int = fs::remove_checked("path")
    pilot rmdir: int = fs::rmdir_checked("path")
    pilot exclusive: int = fs::exclusive_create("path", "text")
    pilot temporary: int = fs::temp_dir("parent", "prefix")
    pilot canonical: int = fs::canonical_path("path")
    pilot stat: int = fs::stat_checked("path")
    pilot directory: int = fs::list_dir_checked("path")
    say fs::result_ok(text)
    pilot payload: word = fs::result_word(text)
    pilot error: word = fs::result_error(text)
    pilot raw: ByteBuffer = fs::result_bytes(binary)
    say fs::result_kind(stat)
    say fs::result_size(stat)
    say fs::result_mode(stat)
    say fs::result_count(directory)
    pilot entry: word = fs::result_entry(directory, 0)
    pilot digest: word = fs::sha256_bytes(bytes)
    raw.release()
    bytes.release()
    fs::result_release(text)
}
'''

OPERATIONS = (
    "read_ticket", "read_bytes_ticket", "read_source_ticket",
    "write_checked", "write_bytes_checked", "append_checked",
    "rename_checked", "rename_new_checked", "mkdir_checked", "remove_checked",
    "rmdir_checked", "exclusive_create", "temp_dir", "canonical_path",
    "stat_checked", "list_dir_checked", "result_ok", "result_word",
    "result_error", "result_bytes", "result_kind", "result_size", "result_mode",
    "result_count", "result_entry", "result_release", "sha256_bytes",
)

NEGATIVE = {
    "inferred_payload_release": (
        'pilot bytes = fs::result_bytes(1)\nbytes.release()\nbytes.length()',
        "You gave this away", True,
    ),
    "write_payload_type": (
        'fs::write_checked("path", 1)', "argument 2 expects word, got int", False,
    ),
    "write_bytes_type": (
        'fs::write_bytes_checked("path", "bytes")',
        "argument 2 expects ByteBuffer, got word", False,
    ),
    "entry_index_type": (
        'fs::result_entry(1, "index")', "argument 2 expects int, got word", False,
    ),
    "digest_input_type": (
        'fs::sha256_bytes(1)', "argument 1 expects ByteBuffer, got int", False,
    ),
    "temporary_arity": (
        'fs::temp_dir("parent")', "expects 2 argument(s), got 1", False,
    ),
    "unsupported_prefix": (
        'fs::result_magic(1)', "unknown callable 'fs::result_magic'", False,
    ),
    "released_ticket": (
        'pilot ticket: int = fs::read_ticket("path")\n'
        'fs::result_release(ticket)\nfs::result_ok(ticket)',
        "You gave this away", True,
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", type=Path, help="fresh exact-source native stage2 compiler")
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG") or shutil.which("clang"))
    args = parser.parse_args()
    assert args.clang, "Clang is required for native source reconstruction"
    repo = Path(__file__).resolve().parents[1]
    inventory = []
    with tempfile.TemporaryDirectory(prefix="freak-v35-fs-compiler-") as directory:
        root = Path(directory)
        compiler = (
            args.compiler.resolve(strict=True) if args.compiler
            else build_stage2(clang=args.clang, repo=repo, root=root)
        )
        for backend in ("c", "llvm"):
            source = root / f"filesystem_api_{backend}.fk"
            source.write_text(PROGRAM, encoding="utf-8")
            require_ok(run([str(compiler), str(source), f"--{backend}", "--strict-borrow"], root), backend)
            suffix = ".c" if backend == "c" else ".ll"
            emitted = Path(str(source) + suffix).read_text(encoding="utf-8")
            prefix = "freak_fs_" if backend == "c" else "@freak_llvm_fs_"
            for operation in OPERATIONS:
                symbol = prefix + operation
                assert symbol + "(" in emitted, (backend, operation, emitted)
                if backend == "llvm":
                    assert any("call " in line and symbol + "(" in line for line in emitted.splitlines()), (
                        backend, operation, emitted,
                    )
            assert "__freak_user_fs_" not in emitted, emitted
            inventory.append((backend, "positive"))
            print(f"PASS {backend} filesystem API emission", flush=True)
            for name, (body, diagnostic, strict) in NEGATIVE.items():
                source = root / f"{name}_{backend}.fk"
                source.write_text("task main() {\n" + body + "\n}\n", encoding="utf-8")
                artifact = Path(str(source) + suffix)
                artifact.write_text("stale filesystem output", encoding="utf-8")
                command = [str(compiler), str(source), f"--{backend}"]
                if strict:
                    command.append("--strict-borrow")
                result = run(command, root)
                output = result.stdout + result.stderr
                assert result.returncode != 0, (backend, name, output)
                assert diagnostic in output, (backend, name, diagnostic, output)
                assert not artifact.exists(), (backend, name, "stale artifact survived")
                inventory.append((backend, name))
                print(f"PASS {backend} {name}", flush=True)
    expected = {(backend, name) for backend in ("c", "llvm") for name in ("positive", *NEGATIVE)}
    assert set(inventory) == expected and len(inventory) == len(expected)
    print(f"V3.5 filesystem compiler contracts: PASS ({len(inventory)} cases)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
