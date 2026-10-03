#!/usr/bin/env python3
"""Compile and execute the actual native V4 word runtime proof.

Sanitizer mode is mandatory by default. Missing Clang or sanitizer support is a
failure, never a skipped success. --plain is an explicit additional portability
gate for platforms whose toolchain lacks AddressSanitizer; it is not evidence
that the sanitizer gate passed.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile


def assert_named_panic(result: subprocess.CompletedProcess[bytes], reason: str,
                       *, platform: str = sys.platform) -> None:
    # Microsoft CRT abort exits3. The probe disables abort report/UI behavior;
    # POSIX abort terminates with SIGABRT. Sanitizer/audit exits are never proof
    # of a successful bounds or UTF-8 rejection.
    expected_exit = 3 if platform == "win32" else -signal.SIGABRT
    diagnostic = ("FREAK: V4 word panic: " + reason + "\n").encode()
    stderr = result.stderr.replace(b"\r\n", b"\n") if platform == "win32" else result.stderr
    actual = (result.returncode, result.stdout, stderr)
    expected = (expected_exit, b"", diagnostic)
    if actual != expected:
        raise AssertionError(f"expected named panic {expected!r}; actual {actual!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG") or shutil.which("clang"))
    parser.add_argument("--plain", action="store_true", help="run an additional unsanitized portability gate")
    parser.add_argument("--runtime-root", type=Path)
    args = parser.parse_args()
    if not args.clang:
        parser.error("clang is required; the native runtime gate cannot be skipped")
    repo = Path(__file__).resolve().parents[1]
    runtime = (args.runtime_root or repo / "freakc/runtime").resolve()
    environment = os.environ.copy()
    environment.pop("ASAN_OPTIONS", None)
    environment.pop("LSAN_OPTIONS", None)
    environment.pop("UBSAN_OPTIONS", None)
    if not args.plain:
        environment["ASAN_OPTIONS"] = "halt_on_error=1:detect_leaks=1:exitcode=86"
        environment["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1:exitcode=85"
    with tempfile.TemporaryDirectory(prefix="freak-v4-word-runtime-") as temporary:
        binary = Path(temporary) / ("word-runtime.exe" if sys.platform == "win32" else "word-runtime")
        command = [args.clang, "-std=c11", "-O1", "-g", "-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1",
                   "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1", "-I", str(runtime),
                   str(repo / "tests/v4_word_runtime_probe.c"),
                   str(runtime / "freak_v4_word_runtime.c"), "-o", str(binary)]
        command += ["-lws2_32"] if sys.platform == "win32" else ["-lm"]
        if not args.plain:
            command += ["-fsanitize=address,undefined", "-fno-omit-frame-pointer"]
        compiled = subprocess.run(command, capture_output=True, timeout=120, env=environment)
        assert compiled.returncode == 0, compiled.stdout + compiled.stderr

        def execute(*arguments: str) -> subprocess.CompletedProcess[bytes]:
            return subprocess.run([str(binary), *arguments], cwd=temporary,
                                  capture_output=True, timeout=20, env=environment)

        accepted = execute()
        payload = b"A\0\xc3\xa9\xe4\xb8\xad\xf0\x9f\x98\x80"
        assert accepted.returncode == 0, (accepted.returncode, accepted.stdout, accepted.stderr)
        stdout = accepted.stdout.replace(b"\r\n", b"\n") if sys.platform == "win32" else accepted.stdout
        stderr = accepted.stderr.replace(b"\r\n", b"\n") if sys.platform == "win32" else accepted.stderr
        assert stdout == payload + b"\n\nv4-word-runtime=ok\n", accepted.stdout
        assert stderr == payload + b"\n", accepted.stderr

        rejected = {f"utf8-{index}": "invalid UTF-8" for index in range(13)}
        rejected.update({
            "negative-length": "negative byte length", "null-source": "null byte source",
            "source-overflow": "byte source range overflow", "consumed-word": "word value has been consumed",
            "foreign-observe": "word value is not live owned storage",
            "unknown-pointer": "word value is not live owned storage",
            "released-word": "word value is not live owned storage",
            "foreign-drop": "word value is not live owned storage",
            "double-drop": "word value is not live owned storage",
            "char-negative": "character index out of bounds", "char-end": "character index out of bounds",
            "char-overflow": "character index out of bounds", "slice-negative": "slice range out of bounds",
            "slice-reversed": "slice range out of bounds", "slice-end": "slice range out of bounds",
            "slice-overflow": "slice range out of bounds", "substring-negative": "substring range out of bounds",
            "substring-start": "substring range out of bounds", "substring-count": "substring range out of bounds",
            "substring-overflow": "substring range out of bounds",
        })
        for case, reason in rejected.items():
            failed = execute(case)
            assert_named_panic(failed, reason)
        mode = "plain portability" if args.plain else "AddressSanitizer + UndefinedBehaviorSanitizer"
        print(f"V4 word runtime: owned UTF-8/NUL/scalar bounds, {len(rejected)} named panic cases, zero owners; {mode} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
