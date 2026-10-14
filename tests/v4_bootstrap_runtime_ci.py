#!/usr/bin/env python3
"""Narrow shipping-runtime compilation, argv and H6 checked-source fault gate.

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
    argv_fixture = repo / "tests/native_bootstrap_argv.c"
    inputs = sorted([fixture, argv_fixture, Path(__file__).resolve(),
                     *runtime.glob("*.c"), *runtime.glob("*.h"), *runtime.glob("*.inc"),
                     *(p for p in (repo / "third_party/llhttp").rglob("*") if p.is_file())])
    hashes = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    records = []
    env = dict(os.environ, ASAN_OPTIONS="detect_leaks=1:halt_on_error=1",
               UBSAN_OPTIONS="halt_on_error=1")
    env.pop("FREAK_BOOTSTRAP_ARGV_FAULT", None)
    env.pop("FREAK_BOOTSTRAP_ARGV_MODE", None)

    def run(command: list[str], label: str, overrides: dict | None = None) -> subprocess.CompletedProcess:
        result = subprocess.run(command, capture_output=True, env=dict(env, **(overrides or {})), timeout=90)
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

                # Use an actual narrow CRT entry and an actual LLVM entry calling
                # the shipping scalar setup ABI. The native Windows witness
                # records both CRT encodings; UTF-8 ACP hosts need not be lossy.
                llvm_entry = work / "argv-entry.ll"
                llvm_entry.write_text("""declare void @argv_probe_prepare(i32, ptr)
declare void @freak_llvm_setup_args(i64, i64)
declare i32 @argv_probe_run()
define i32 @main(i32 %argc, ptr %argv) {
  call void @argv_probe_prepare(i32 %argc, ptr %argv)
  %count = sext i32 %argc to i64
  %arguments = ptrtoint ptr %argv to i64
  call void @freak_llvm_setup_args(i64 %count, i64 %arguments)
  %result = call i32 @argv_probe_run()
  ret i32 %result
}
""", encoding="utf8")
                vector = ["plain", "", "é 日本", "🙂𝄞", 'a"b', "ends\\",
                          'slash\\"quoted', "' $ &", "*?literal",
                          "--output=" + str(work / "preview é 日本 ' $ &" / "bundle")]
                argv_executables = {}
                for opt in args.optimization or (0, 2, 3):
                    for backend in ("C", "LLVM"):
                        executable = work / f"argv-{backend}-O{opt}{'.exe' if os.name == 'nt' else ''}"
                        extra = (["-DARGV_LLVM_MAIN", str(llvm_entry)] if backend == "LLVM" else [])
                        result = run([clang, *strict, f"-O{opt}", *sanitizer,
                                      "-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1", str(argv_fixture),
                                      *extra, "-o", str(executable), *link], f"argv-build-{backend}-O{opt}")
                        assert result.returncode == 0, result.stderr.decode(errors="replace")
                        argv_executables[backend] = executable
                        result = run([str(executable), *vector], f"argv-native-{backend}-O{opt}")
                        assert result.returncode == 0 and not result.stderr, records[-1]
                        lines = result.stdout.decode("ascii").splitlines()
                        expected_args = [str(executable), *vector]
                        for prefix in (("arg", "crt-wide") if os.name == "nt" else ("arg", "crt-narrow")):
                            actual = [line for line in lines if line.startswith(prefix + " ")]
                            assert actual == [f"{prefix} {i} {value.encode('utf8').hex()}"
                                              for i, value in enumerate(expected_args)], records[-1]
                        assert lines[-3:] == ["argv-apis-ok", "argv-exit-after-ok", "argv-exit-before-ok"], records[-1]
                        if os.name == "nt":
                            narrow = [line.split(" ", 2)[2] for line in lines if line.startswith("crt-narrow ")]
                            wide = [line.split(" ", 2)[2] for line in lines if line.startswith("crt-wide ")]
                            records[-1]["crt_narrow_matches_utf8"] = narrow == wide

                for backend, executable in argv_executables.items():
                    result = run([str(executable), *vector], f"argv-bounds-control-{backend}",
                                 {"FREAK_BOOTSTRAP_ARGV_MODE": "bounds"})
                    expected_error = b"PANIC: Argument index out of bounds\n"
                    if os.name == "nt": expected_error = expected_error.replace(b"\n", b"\r\n")
                    assert result.returncode == 1 and result.stderr == expected_error, records[-1]
                    result = run([str(executable), *vector], f"argv-ownership-control-{backend}",
                                 {"FREAK_BOOTSTRAP_ARGV_MODE": "leak"})
                    assert result.returncode == 86 and b"LLVM ownership audit found 1 unreleased word allocation" in result.stderr, records[-1]
                    if os.name == "nt":
                        faults = {
                            1: "could not decode Unicode argument vector",
                            2: "out of memory decoding arguments",
                            3: "out of memory decoding arguments",
                            4: "out of memory decoding arguments",
                            5: "argument is not valid Unicode",
                            6: "could not encode Unicode argument",
                            7: "invalid Unicode argument vector",
                            8: "argument is not valid Unicode",
                        }
                        for fault, message in faults.items():
                            result = run([str(executable), *vector], f"argv-fault-{backend}-{fault}",
                                         {"FREAK_BOOTSTRAP_ARGV_FAULT": str(fault)})
                            assert (result.returncode, result.stdout, result.stderr) == (
                                1, b"argv-failed-cleanly\r\n", f"FREAK: {message}\r\n".encode()), records[-1]

                if os.name == "nt":
                    # A permissive UTF-16 conversion must fail the real lone-
                    # surrogate oracle, independently of the API-error hooks.
                    production = (runtime / "freak_runtime.c").read_text(encoding="utf8")
                    start = production.index("static BOOL CALLBACK freak_args_windows_initialize")
                    end = production.index("static void freak_args_windows_prepare", start)
                    checked = production[start:end]
                    assert checked.count("WC_ERR_INVALID_CHARS") == 2
                    permissive = work / "permissive-runtime.c"
                    permissive.write_text(production[:start] + checked.replace("WC_ERR_INVALID_CHARS", "0")
                                          + production[end:], encoding="utf8")
                    control = work / "permissive-argv.c"
                    control.write_text(argv_fixture.read_text(encoding="utf8").replace(
                        '#include "../freakc/runtime/freak_runtime.c"',
                        f'#include "{permissive.as_posix()}"'), encoding="utf8")
                    executable = work / "permissive-argv.exe"
                    result = run([clang, *strict, "-O2", *sanitizer, str(control),
                                  "-o", str(executable), *link], "argv-permissive-control-build")
                    assert result.returncode == 0, result.stderr.decode(errors="replace")
                    result = run([str(executable), *vector], "argv-permissive-control-native",
                                 {"FREAK_BOOTSTRAP_ARGV_FAULT": "8"})
                    assert result.returncode == 72 and result.stderr == (
                        b"argv unexpected failure callback\r\n"), records[-1]

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
                        ("argv-wide", [argv_fixture]),
                    ):
                        result = run([*cross, *(str(p) for p in sources)], f"windows-sdk-{name}")
                        assert result.returncode == 0, result.stderr.decode(errors="replace")
                if os.name == "nt" or args.windows_sdk:
                    windows = ([clang, *strict, "-fsyntax-only"] if os.name == "nt" else cross)
                    for version in ("0x0602", "0x0a00"):
                        result = run([*windows, "-Werror=macro-redefined", f"-D_WIN32_WINNT={version}",
                                      str(runtime / "freak_runtime.c"),
                                      str(runtime / "freak_llvm_runtime.c"), str(fixture)],
                                     f"windows-api-supported-{version}")
                        assert result.returncode == 0, result.stderr.decode(errors="replace")
                    result = run([*windows, "-D_WIN32_WINNT=0x0601",
                                  str(runtime / "freak_runtime.c")], "windows-api-unsupported-0x0601")
                    assert result.returncode != 0 and (
                        b"FREAK checked filesystem requires _WIN32_WINNT >= 0x0602 (Windows 8)"
                        in result.stderr), records[-1]
            finally:
                denied.chmod(0o600)
        assert hashes == {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}, "inputs changed during gate"
        report = {"ok": True, "native_platform": sys.platform, "sanitize": args.sanitize,
                  "windows_sdk_is_native_execution": False, "inputs": hashes, "records": records}
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
        print(f"bootstrap runtime: {len(records)} commands passed on {sys.platform}; ten H6 faults retained; exact argv APIs verified")
        return 0
    except Exception:
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps({"ok": False, "inputs": hashes, "records": records}, indent=2) + "\n", encoding="utf8")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
