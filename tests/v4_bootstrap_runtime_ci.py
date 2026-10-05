#!/usr/bin/env python3
"""Narrow shipping-runtime compilation and H6 checked-source fault gate.

Run natively on Linux, macOS, or Windows. An optional Windows SDK check is
compilation evidence only; it never substitutes for native Windows execution.
The existing H6 fixture retains all ten faults and its large-size oracle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


EXPECTED = b"h6-runtime-source-read contents=true errors=true faults=true recovery=true\n"
REFUSED = b"h6-runtime-source-read contents=true errors=true faults=false recovery=true\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG", "clang"))
    parser.add_argument("--optimization", type=int, choices=(0, 2, 3), action="append")
    parser.add_argument("--sanitize", action="store_true")
    parser.add_argument("--windows-sdk", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    clang = shutil.which(args.clang)
    assert clang, args.clang
    repo = Path(__file__).resolve().parents[1]
    runtime = repo / "freakc/runtime"
    fixture = repo / "src/compiler/v4/tests/h6_source_read_checked_runtime.c"
    inputs = sorted([fixture, Path(__file__).resolve(),
                     *runtime.glob("*.c"), *runtime.glob("*.h"), *runtime.glob("*.inc"),
                     *(p for p in (repo / "third_party/llhttp").rglob("*") if p.is_file())])
    hashes = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    records = []
    env = dict(os.environ, ASAN_OPTIONS="detect_leaks=1:halt_on_error=1",
               UBSAN_OPTIONS="halt_on_error=1")

    def run(command: list[str], label: str) -> subprocess.CompletedProcess:
        result = subprocess.run(command, capture_output=True, env=env, timeout=90)
        records.append({"label": label, "command": command, "exit": result.returncode,
                        "stdout": result.stdout.decode(errors="replace"),
                        "stderr": result.stderr.decode(errors="replace")})
        return result

    strict = ["-std=c11", "-Werror=implicit-function-declaration",
              "-Werror=incompatible-pointer-types", "-Werror=int-conversion",
              "-Werror=return-type", f"-I{runtime}"]
    link = ["-lws2_32", "-lshell32"] if os.name == "nt" else ["-lm"]
    sanitizer = ["-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                 "-fno-omit-frame-pointer", "-g"] if args.sanitize else []
    try:
        with tempfile.TemporaryDirectory(prefix="freak-v4-runtime-ci-") as directory:
            work = Path(directory)
            empty, readable = work / "empty.fk", work / "readable.fk"
            empty.write_bytes(b"")
            readable.write_bytes(b"task main() -> int {\n give back 7\n}\n")
            paths = [empty, readable, work / "missing.fk", work]
            if hasattr(os, "mkfifo"):
                fifo = work / "source-fifo"
                os.mkfifo(fifo)
                paths.append(fifo)
            denied = work / "unreadable.fk"
            denied.write_bytes(b"secret")
            if os.name != "nt" and os.geteuid() != 0:
                denied.chmod(0)
                paths.append(denied)
            try:
                result = run([clang, *strict, "-fsyntax-only", str(runtime / "freak_runtime.c"),
                              str(runtime / "freak_llvm_runtime.c")], "shipping-runtime-native-syntax")
                assert result.returncode == 0, result.stderr.decode(errors="replace")
                for opt in args.optimization or (0, 2, 3):
                    executable = work / f"h6-O{opt}{'.exe' if os.name == 'nt' else ''}"
                    result = run([clang, *strict, f"-O{opt}", *sanitizer,
                                  "-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1", str(fixture),
                                  "-o", str(executable), *link], f"h6-build-O{opt}")
                    assert result.returncode == 0, result.stderr.decode(errors="replace")
                    result = run([str(executable), *(str(p) for p in paths)], f"h6-native-O{opt}")
                    expected = EXPECTED.replace(b"\n", b"\r\n") if os.name == "nt" else EXPECTED
                    assert (result.returncode, result.stdout, result.stderr) == (0, expected, b""), records[-1]

                # Prove the fixture refuses a bypassed open fault and a content
                # fault moved to an earlier allocation, without allocating GBs.
                text = fixture.read_text(encoding="utf8").replace(
                    '#include "../../../../freakc/runtime/freak_runtime.c"',
                    f'#include "{(runtime / "freak_runtime.c").as_posix()}"')
                controls = {
                    "bypassed-open-fault": text.replace("if (h6_fault == 6)", "if (0)"),
                    "wrong-content-allocation": text.replace(
                        "h6_allocations == H6_CONTENTS_ALLOCATION", "h6_allocations == 1"),
                }
                for name, source in controls.items():
                    control = work / f"{name}.c"
                    control.write_text(source, encoding="utf8")
                    executable = work / f"{name}{'.exe' if os.name == 'nt' else ''}"
                    result = run([clang, *strict, "-O2", *sanitizer, str(control),
                                  "-o", str(executable), *link], f"control-build-{name}")
                    assert result.returncode == 0, result.stderr.decode(errors="replace")
                    result = run([str(executable), *(str(p) for p in paths)], f"control-native-{name}")
                    refused = REFUSED.replace(b"\n", b"\r\n") if os.name == "nt" else REFUSED
                    assert (result.returncode, result.stdout, result.stderr) == (1, refused, b""), records[-1]

                if args.windows_sdk:
                    cross = [clang, "--target=x86_64-w64-windows-gnu",
                             f"--sysroot={args.windows_sdk}", *strict, "-fsyntax-only"]
                    for name, sources in (
                        ("shipping", [runtime / "freak_runtime.c", runtime / "freak_llvm_runtime.c"]),
                        ("h6-wide-faults", [fixture]),
                    ):
                        result = run([*cross, *(str(p) for p in sources)], f"windows-sdk-{name}")
                        assert result.returncode == 0, result.stderr.decode(errors="replace")
            finally:
                denied.chmod(0o600)
        assert hashes == {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}, "inputs changed during gate"
        report = {"ok": True, "native_platform": sys.platform, "sanitize": args.sanitize,
                  "windows_sdk_is_native_execution": False, "inputs": hashes, "records": records}
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
        print(f"bootstrap runtime: {len(records)} commands passed on {sys.platform}; ten H6 faults retained")
        return 0
    except Exception:
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps({"ok": False, "inputs": hashes, "records": records}, indent=2) + "\n", encoding="utf8")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
