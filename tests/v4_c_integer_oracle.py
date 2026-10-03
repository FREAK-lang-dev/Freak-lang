#!/usr/bin/env python3
"""Compile a header-free four-target C scalar oracle; this is not C ABI admission.

The IR/object proof requires Clang, fails on missing tools/targets and retains
source/compiler/commands/artifacts. It never links or executes a foreign binary.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
TARGET_LONG_BYTES = {
    "x86_64-unknown-linux-gnu": 8,
    "aarch64-unknown-linux-gnu": 8,
    "aarch64-apple-darwin": 8,
    "x86_64-w64-windows-gnu": 4,
}
SCALARS = ("c_int", "c_uint", "c_long", "c_ulong")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def scalar_operand(operand: str) -> dict[str, object]:
    tokens = operand.split()
    require(bool(tokens) and tokens[0] in ("i32", "i64"), "unrecognized scalar carrier")
    extensions = [token for token in tokens if token in ("signext", "zeroext")]
    require(len(extensions) <= 1, "conflicting scalar extension attributes")
    return {"carrier": tokens[0], "extension": extensions[0] if extensions else "none"}


def return_operand(prefix: str) -> dict[str, object]:
    tokens = prefix.split()
    carriers = [token for token in tokens if token in ("i32", "i64")]
    require(len(carriers) == 1, "missing or ambiguous return carrier")
    extensions = [token for token in tokens if token in ("signext", "zeroext")]
    require(len(extensions) <= 1, "conflicting return extension attributes")
    return {"carrier": carriers[0], "extension": extensions[0] if extensions else "none"}


def target_triple_matches(requested: str, observed: str) -> bool:
    if requested == "aarch64-apple-darwin":
        # Clang canonicalizes Darwin to an explicit macOS deployment triple.
        return re.fullmatch(r"(?:aarch64|arm64)-apple-(?:darwin|macosx)(?:[0-9]+(?:\.[0-9]+)*)?", observed) is not None
    return requested == observed


def parse_oracle(text: str, target: str) -> dict[str, object]:
    require(target in TARGET_LONG_BYTES, "unknown requested target")
    triples = re.findall(r'^target triple = "([^"\n]+)"$', text, re.MULTILINE)
    layouts = re.findall(r'^target datalayout = "([^"\n]+)"$', text, re.MULTILINE)
    require(len(triples) == 1 and target_triple_matches(target, triples[0]), "missing, duplicate or mismatched target triple")
    require(len(layouts) == 1 and layouts[0].startswith("e-"), "missing, duplicate or non-little-endian datalayout")
    functions: dict[str, tuple[str, list[str], str]] = {}
    for match in re.finditer(r"^define\s+([^\n]+?)\s+@(oracle_[A-Za-z0-9_]+)\(([^\n)]*)\)[^\n]*\{\n(.*?)^\}", text, re.MULTILINE | re.DOTALL):
        prefix, name, parameters, body = match.groups()
        require(name not in functions, "duplicate oracle function")
        functions[name] = (prefix, [param.strip() for param in parameters.split(",")], body)
    expected_names = {f"oracle_{mode}_{key}" for mode in ("identity", "direct", "indirect") for key in SCALARS}
    require(set(functions) == expected_names, "missing or unexpected oracle function")
    facts: dict[str, object] = {}
    for key in SCALARS:
        expected_size = TARGET_LONG_BYTES[target] if key in ("c_long", "c_ulong") else 4
        expected_signed = 1 if key in ("c_int", "c_long") else 0
        measures: dict[str, int] = {}
        for kind in ("size", "align", "signed"):
            values = re.findall(rf"^@oracle_{kind}_{key}\s*=\s*[^\n]*\bconstant i64 ([0-9]+)(?:,|\s*$)", text, re.MULTILINE)
            require(len(values) == 1, f"missing or duplicate {kind} measurement: {key}")
            measures[kind] = int(values[0])
        require(measures == {"size": expected_size, "align": expected_size, "signed": expected_signed}, f"scalar storage mismatch: {key}")
        carrier = f"i{expected_size * 8}"
        identity_prefix, identity_parameters, _ = functions[f"oracle_identity_{key}"]
        require(len(identity_parameters) == 1, "identity parameter count mismatch")
        returned = return_operand(identity_prefix)
        parameter = scalar_operand(identity_parameters[0])
        require(returned["carrier"] == parameter["carrier"] == carrier, f"identity carrier mismatch: {key}")
        for mode in ("direct", "indirect"):
            prefix, parameters, body = functions[f"oracle_{mode}_{key}"]
            require(len(parameters) == (2 if mode == "indirect" else 1), "wrapper parameter count mismatch")
            if mode == "indirect":
                require(parameters[0].split()[0] == "ptr", "callback parameter is not a pointer")
            require(return_operand(prefix) == returned and scalar_operand(parameters[-1]) == parameter, f"wrapper signature mismatch: {key}/{mode}")
            called = f"@oracle_identity_{key}" if mode == "direct" else r"%[A-Za-z0-9_.]+"
            calls = re.findall(rf"\bcall\s+([^\n]+?)\s+({called})\(([^\n)]*)\)", body)
            require(len(calls) == 1, f"missing or duplicate scalar call: {key}/{mode}")
            call_return, _, call_parameter = calls[0]
            require(return_operand(call_return) == returned and scalar_operand(call_parameter) == parameter, f"call carrier/extension mismatch: {key}/{mode}")
        facts[key] = {"width": expected_size * 8, **measures, "return": returned, "parameter": parameter}
    return {"requested_target": target, "observed_triple": triples[0], "datalayout": layouts[0], "scalars": facts}


def file_record(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clang", default=shutil.which("clang"))
    parser.add_argument("--output", type=Path, required=True, help="new empty artifact directory")
    args = parser.parse_args()
    if not args.clang:
        parser.error("Clang is required; the four-target oracle cannot be skipped")
    compiler = Path(shutil.which(args.clang) or args.clang).resolve(strict=True)
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    if any(args.output.iterdir()):
        parser.error("--output must be empty so old artifacts cannot satisfy this run")
    spec = importlib.util.spec_from_file_location("c_integer_oracle_checks", ROOT / "src/compiler/v4/check_v4.py")
    checks = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checks)
    commands: list[dict[str, object]] = []

    def execute(command: list[str], label: str) -> None:
        entry: dict[str, object] = {"command": command, "status": "started",
                                  "timeout_seconds": 120, "memory_limit_mb": 1024,
                                  "output_limit_mb": 8}
        commands.append(entry)
        (args.output / "commands.json").write_text(json.dumps(commands, indent=2) + "\n", encoding="utf-8")
        try:
            result = checks.run_with_heartbeat(command, label=label, timeout_seconds=120,
                                               memory_limit_mb=1024, output_limit_mb=8)
        except Exception as exc:
            entry.update(status="raised", error_type=type(exc).__name__)
            (args.output / "commands.json").write_text(json.dumps(commands, indent=2) + "\n", encoding="utf-8")
            raise
        entry.update(status="finished", returncode=result.returncode,
                     stdout=result.stdout, stderr=result.stderr)
        (args.output / "commands.json").write_text(json.dumps(commands, indent=2) + "\n", encoding="utf-8")
        require(result.returncode == 0, f"{label} failed: {result.stderr}")

    execute([str(compiler), "--version"], "C integer oracle compiler identity")
    source = ROOT / "tests/v4_c_integer_oracle.c"
    facts: list[dict[str, object]] = []
    for target, long_bytes in TARGET_LONG_BYTES.items():
        llvm = args.output / f"{target}.ll"
        obj = args.output / f"{target}.o"
        execute([str(compiler), f"--target={target}", "-std=c11", "-O0", "-S", "-emit-llvm",
                 f"-DFREAK_ORACLE_LONG_BYTES={long_bytes}", str(source), "-o", str(llvm)],
                f"C integer oracle IR: {target}")
        facts.append(parse_oracle(llvm.read_text(encoding="utf-8"), target))
        execute([str(compiler), f"--target={target}", "-x", "ir", "-c", str(llvm), "-o", str(obj)],
                f"C integer oracle object: {target}")
        require(obj.stat().st_size > 0, "oracle produced an empty object")
    manifest = {"compiler": file_record(compiler), "source": file_record(source),
                "driver": file_record(Path(__file__).resolve()), "commands": commands,
                "targets": facts,
                "artifacts": [file_record(path) for path in sorted(args.output.iterdir())],
                "boundary": "C cross-target IR/object proof only; no foreign execution or FREAK C ABI admission"}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("V4 C integer oracle: all four explicit targets, storage and direct/indirect carriers/extensions passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
