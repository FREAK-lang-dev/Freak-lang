#!/usr/bin/env python3
"""Bound benchmark inputs without executing the expensive maximum workloads."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import v3_word_foundation as foundation


LIMITS = {"cpu_integer_10m": 10_000_000, "word_dynamic_append": 1_000_000,
          "word_builder_unknown_capacity": 100_000_000}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cli", type=Path)
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG") or shutil.which("clang"))
    args = parser.parse_args()
    assert args.clang, "Clang is required"
    repo = Path(__file__).resolve().parents[1]
    runtime = (args.runtime_root or repo / "freakc/runtime").resolve()
    cli = args.cli.resolve(strict=True)
    manifest = json.loads((repo / "benchmarks/v3/manifest.json").read_text(encoding="utf-8"))
    cases = {case["id"]: case for case in manifest["cases"]}
    with tempfile.TemporaryDirectory(prefix="freak-benchmark-bounds-") as directory:
        root = Path(directory)
        for name, maximum in LIMITS.items():
            case = cases[name]
            assert case["modes"]["default"]["arguments"] == [str(maximum)]
            quick = case["modes"]["quick"]
            assert 1 <= int(quick["arguments"][0]) < maximum
            for backend in ("c", "llvm"):
                source = root / f"{name}_{backend}.fk"
                shutil.copyfile(repo / "benchmarks/v3" / case["source"], source)
                generated, _ = foundation.transpile(freak=cli, repo=repo, source=source, backend=backend)
                binary = root / f"{name}_{backend}{'.exe' if sys.platform == 'win32' else ''}"
                foundation.compile_generated(clang=args.clang, repo=repo, runtime_root=runtime,
                                             generated=generated, backend=backend, binary=binary)
                # These children have no descendants; subprocess.run terminates
                # a timed-out child. Never run the valid maximum/default here.
                for argument in ("-1", "0", str(maximum + 1), "9223372036854775807"):
                    completed = subprocess.run([str(binary), argument], capture_output=True,
                                               env=foundation.sanitizer_env(), timeout=3.0)
                    assert completed.returncode == 2, (name, backend, argument, completed)
                    assert completed.stdout == b"", (name, backend, argument, completed.stdout)
                    assert b"ownership audit found" not in completed.stderr, completed.stderr
                minimum = subprocess.run([str(binary), "1"], capture_output=True,
                                         env=foundation.sanitizer_env(), timeout=3.0)
                assert minimum.returncode == 0, (name, backend, minimum)
                expected_minimum = b"0\n" if name == "cpu_integer_10m" else b"1\n3414842651491571463\n"
                assert minimum.stdout.replace(b"\r\n", b"\n") == expected_minimum, (name, backend, minimum.stdout)
                completed = subprocess.run([str(binary), *quick["arguments"]], capture_output=True,
                                           env=foundation.sanitizer_env(), timeout=5.0)
                assert completed.returncode == quick["expected_exit_code"], (name, backend, completed)
                assert completed.stdout.replace(b"\r\n", b"\n") == quick["expected_stdout"].encode(), (name, backend, completed.stdout)
                assert b"ownership audit found" not in completed.stderr, completed.stderr
                print(f"PASS {name} {backend}: minimum/quick unchanged; invalid inputs exit 2", flush=True)
    print("PASS benchmark bounds; no maximum workload executed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
