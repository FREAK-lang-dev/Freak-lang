#!/usr/bin/env python3
"""Execute the private V4 process/fs runtime prerequisite.

Default requires Linux AddressSanitizer + UndefinedBehaviorSanitizer; missing
compiler/sanitizer support fails. --plain is an additional portability proof,
not a sanitizer success. This does not verify typed FREAK result lowering.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG") or shutil.which("clang"))
    parser.add_argument("--plain", action="store_true")
    args = parser.parse_args()
    if not args.clang:
        parser.error("clang is required; system runtime checks cannot be skipped")
    if not args.plain and not sys.platform.startswith("linux"):
        parser.error("the mandatory sanitizer proof runs on Linux; use --plain additionally on other platforms")
    repo = Path(__file__).resolve().parents[1]
    runtime = repo / "freakc/runtime"
    environment = os.environ.copy()
    for key in ("ASAN_OPTIONS", "LSAN_OPTIONS", "UBSAN_OPTIONS"):
        environment.pop(key, None)
    if not args.plain:
        environment["ASAN_OPTIONS"] = "halt_on_error=1:detect_leaks=1:exitcode=86"
        environment["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1:exitcode=85"

    with tempfile.TemporaryDirectory(prefix="freak-v4-system-runtime-") as temporary:
        root = Path(temporary)
        binary = root / ("system 雪😀.exe" if sys.platform == "win32" else "system 雪😀")
        command = [args.clang, "-std=c11", "-O1", "-g",
                   "-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1", "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1",
                   "-I", str(runtime), str(repo / "tests/v4_system_runtime_probe.c"),
                   str(runtime / "freak_v4_word_runtime.c"), "-o", str(binary)]
        command += ["-lws2_32", "-lshell32"] if sys.platform == "win32" else ["-lm"]
        if not args.plain:
            command += ["-fsanitize=address,undefined", "-fno-omit-frame-pointer"]
        compiled = subprocess.run(command, capture_output=True, timeout=120, env=environment)
        assert compiled.returncode == 0, (command, compiled.stdout, compiled.stderr)

        empty = root / "empty 雪.txt"
        empty.write_bytes(b"")
        text = root / "text 中😀.bin"
        text.write_bytes(b"A\0\xc3\xa9\xe4\xb8\xad\xf0\x9f\x98\x80")
        missing = root / "missing.txt"
        directory = root / "directory"
        directory.mkdir()
        nonregular = root / "fifo"
        if sys.platform == "win32":
            nonregular.mkdir()
        else:
            os.mkfifo(nonregular)
        invalid = root / "invalid-utf8.bin"
        invalid.write_bytes(b"\xed\xa0\x80")
        parameters = ["--accepted", str(empty), str(text), str(missing), str(directory),
                      str(nonregular), str(invalid), "", "space value", 'quote"value',
                      "backslash\\", "escaped\\\\\"quote", "line\nvalue", "Aé中😀"]

        def execute(arguments: list[str]) -> subprocess.CompletedProcess[bytes]:
            return subprocess.run([str(binary), *arguments], cwd=temporary,
                                  capture_output=True, timeout=20, env=environment)

        def platform_newlines(data: bytes) -> bytes:
            # POSIX observations stay byte-exact; only the Windows CRT uses CRLF.
            return data.replace(b"\r\n", b"\n") if sys.platform == "win32" else data

        accepted = execute(parameters)
        assert accepted.returncode == 0, (accepted.returncode, accepted.stdout, accepted.stderr)
        assert accepted.stderr == b"", accepted.stderr
        expected = [str(binary), *parameters]
        expected_lines = [f"arg:{index}:{value.encode('utf-8').hex()}".encode()
                          for index, value in enumerate(expected)]
        expected_lines.append(b"v4-system-runtime=ok")
        assert platform_newlines(accepted.stdout) == b"\n".join(expected_lines) + b"\n", accepted.stdout

        rejected = {
            "--checked-null-tag": "invalid checked argument result slots",
            "--checked-null-payload": "invalid checked argument result slots",
            "--checked-null-slots": "invalid checked argument result slots",
            "--checked-aliased-slots": "invalid checked argument result slots",
            "--negative-argc": "invalid argument vector",
            "--huge-argc": "invalid argument vector",
            "--null-argv": "invalid argument vector",
            "--snapshot-allocation": "argument snapshot allocation failed",
            "--argument-allocation": "argument snapshot allocation failed",
            "--invalid-result-slots": "invalid filesystem result slots",
            "--aliased-result-slots": "invalid filesystem result slots",
            "--foreign-path": "filesystem path is not a live owned word",
            "--unknown-path": "filesystem path is not a live owned word",
            "--stale-path": "filesystem path is not a live owned word",
        }
        if sys.platform != "win32":
            rejected["--null-argument"] = "invalid argument vector"
            rejected["--invalid-argument"] = "argument is not valid UTF-8"
        else:
            rejected["--invalid-wide-argument"] = "argument is not valid Unicode"
        for case, reason in rejected.items():
            arguments = [case]
            if case == "--invalid-wide-argument":
                arguments.append("\ud800")
            failed = execute(arguments)
            expected_error = ("FREAK: V4 system runtime: " + reason + "\n").encode()
            assert failed.returncode == 1, (case, failed.returncode, failed.stdout, failed.stderr)
            assert failed.stdout == b"", (case, failed.stdout)
            assert platform_newlines(failed.stderr) == expected_error, (case, failed.stderr)
        # Neither POSIX nor Windows process argument vectors can carry NUL.
        try:
            execute(["argument\0cannot-cross-os-argv"])
        except ValueError:
            pass
        else:
            raise AssertionError("subprocess admitted an embedded NUL argument")

        mode = "plain portability" if args.plain else "AddressSanitizer + UndefinedBehaviorSanitizer"
        print(f"V4 system runtime: raw/checked owned UTF-8 argv and Unicode paths, sized NUL/empty/error reads, "
              f"pre-read path size rejection, 13 I/O/storage faults, {len(rejected)} named failures, "
              f"zero owners/descriptors; {mode} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
