#!/usr/bin/env python3
"""Build the first FREAK Academy WASM-backed lesson evaluator."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SOURCE_REL = Path("learning") / "wasm" / "academy-wasm-evaluator.c"
SOURCE = ROOT / SOURCE_REL
DEFAULT_OUTPUT_DIR = ROOT / "build" / "academy-wasm"
WASM_NAME = "academy-wasm-evaluator.wasm"
MANIFEST_NAME = "academy-wasm-evaluator-manifest.json"
EXPORTS = [
    "memory",
    "academy_protocol_version",
    "academy_wasm_evaluator_version",
    "academy_supported_lesson_count",
    "academy_input_offset",
    "academy_input_capacity",
    "academy_last_stdout_offset",
    "academy_last_stdout_length",
    "academy_last_message_offset",
    "academy_last_message_length",
    "academy_evaluate_hello_freak",
    "academy_evaluate_variables",
]


class WasmEvaluatorError(Exception):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_wasm_evaluator(output_dir: Path, compiler: str = "clang") -> dict[str, Any]:
    compiler_path = shutil.which(compiler)
    if compiler_path is None:
        raise WasmEvaluatorError(
            f"{compiler} was not found. Install LLVM clang with wasm32 support to build the Academy WASM evaluator."
        )
    if not SOURCE.exists():
        raise WasmEvaluatorError(f"WASM evaluator source not found: {SOURCE}")

    output_dir.mkdir(parents=True, exist_ok=True)
    wasm_path = output_dir / WASM_NAME
    manifest_path = output_dir / MANIFEST_NAME

    cmd = [
        compiler_path,
        "--target=wasm32",
        "-nostdlib",
        "-O2",
        "-Wl,--no-entry",
        "-Wl,--export-memory",
        *[f"-Wl,--export={name}" for name in EXPORTS if name != "memory"],
        str(SOURCE),
        "-o",
        str(wasm_path),
    ]
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=30)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit code {result.returncode}"
        raise WasmEvaluatorError(f"clang could not build the Academy WASM evaluator: {detail}")

    manifest = {
        "schemaVersion": 1,
        "artifactStatus": "wasm-preview-basics-evaluator",
        "workerProtocolVersion": 1,
        "sourcePath": SOURCE_REL.as_posix(),
        "wasmPath": WASM_NAME,
        "sha256": sha256_file(wasm_path),
        "bytes": wasm_path.stat().st_size,
        "target": "wasm32",
        "supportedLessons": ["hello-freak", "variables"],
        "toolchain": {
            "compiler": compiler_path,
            "command": cmd,
        },
        "exports": EXPORTS,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the FREAK Academy WASM evaluator artifact.")
    parser.add_argument(
        "output",
        nargs="?",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory to receive the .wasm and manifest. Defaults to build/academy-wasm.",
    )
    parser.add_argument(
        "--compiler",
        default="clang",
        help="C compiler command to use. Defaults to clang.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the success manifest or failure object as JSON.",
    )
    args = parser.parse_args(argv)

    try:
        manifest = build_wasm_evaluator(Path(args.output), compiler=args.compiler)
    except WasmEvaluatorError as exc:
        if args.json:
            print(json.dumps({"ok": False, "reason": str(exc)}, indent=2, sort_keys=True))
        else:
            print(f"Academy WASM evaluator unavailable: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0

    print(f"Academy WASM evaluator built in {args.output}")
    print(f"  wasm: {manifest['wasmPath']} ({manifest['bytes']} bytes)")
    print(f"  manifest: {MANIFEST_NAME}")
    print("  status: wasm-preview-basics-evaluator")
    print("  supported lessons: hello-freak, variables")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
