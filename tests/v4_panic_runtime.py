#!/usr/bin/env python3
"""Execute the explicit abort-only private V4 panic runtime prerequisite.

Default requires Linux ASan/UBSan; absent support fails. --plain adds portable
native proof. This does not wire FREAK panic, never/CFG or default unwinding.
Intentional abort skips atexit audits; the success control verifies zero owners.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import signal
import struct
import subprocess
import sys
import tempfile


def assert_exact_abort(result: subprocess.CompletedProcess[bytes], diagnostic: bytes,
                       *, platform: str = sys.platform) -> None:
    expected = (3 if platform == "win32" else -signal.SIGABRT, b"",
                diagnostic.replace(b"\r\n", b"\n"))
    actual = (result.returncode, result.stdout, result.stderr.replace(b"\r\n", b"\n"))
    if actual != expected:
        raise AssertionError(
            f"expected abort exit={expected[0]}, stdout empty, stderr({len(expected[2])})={expected[2][:160]!r}; "
            f"actual exit={actual[0]}, stdout({len(actual[1])})={actual[1][:160]!r}, "
            f"stderr({len(actual[2])})={actual[2][:160]!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG") or shutil.which("clang"))
    parser.add_argument("--plain", action="store_true")
    args = parser.parse_args()
    if not args.clang:
        parser.error("clang is required; the panic runtime gate cannot be skipped")
    if not args.plain and not sys.platform.startswith("linux"):
        parser.error("mandatory sanitizer proof runs on Linux; use --plain additionally on other platforms")
    repo = Path(__file__).resolve().parents[1]
    runtime = repo / "freakc/runtime"
    environment = os.environ.copy()
    for name in ("ASAN_OPTIONS", "LSAN_OPTIONS", "UBSAN_OPTIONS"):
        environment.pop(name, None)
    if not args.plain:
        environment["ASAN_OPTIONS"] = "halt_on_error=1:detect_leaks=1:exitcode=86"
        environment["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1:exitcode=85"
    large = bytearray(b"x" * 262144)
    large[0] = ord("A")
    large[1] = 0
    large[-1] = ord("Z")
    messages = {
        "empty": b"", "ascii": b"invariant failed", "unicode": "café 中 😀".encode(),
        "nul": b"A\0B", "multiline": b"first\nsecond\n", "crlf": b"first\r\nsecond",
        "large": bytes(large),
    }
    rejected = {
        "null": "word value has been consumed",
        "unknown": "word value is not live owned storage",
        "negative": "word value is not live owned storage",
        "foreign": "word value is not live owned storage",
        "stale": "word value is not live owned storage",
        "size-max": "byte length overflow", "invalid-utf8": "invalid UTF-8",
    }
    if struct.calcsize("P") > 4:
        rejected["signed-overflow"] = "byte length overflow"
    with tempfile.TemporaryDirectory(prefix="freak-v4-panic-runtime-") as temporary:
        # Check the unmodified separately linked production translation unit as
        # well as the instrumented loan-at-abort proof. Both perform real abort.
        for variant in ("direct", "loan-probe"):
            suffix = ".exe" if sys.platform == "win32" else ""
            binary = Path(temporary) / ("panic-runtime-" + variant + suffix)
            command = [args.clang, "-std=c11", "-O1", "-g",
                       "-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1", "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1",
                       "-I", str(runtime), str(repo / "tests/v4_panic_runtime_probe.c"),
                       str(runtime / "freak_v4_word_runtime.c"), "-o", str(binary)]
            if variant == "direct":
                command += ["-DFREAK_V4_PANIC_DIRECT_LINK=1", str(runtime / "freak_v4_panic_runtime.c")]
            command += ["-lws2_32"] if sys.platform == "win32" else ["-lm"]
            if not args.plain:
                command += ["-fsanitize=address,undefined", "-fno-omit-frame-pointer"]
            compiled = subprocess.run(command, env=environment, capture_output=True, timeout=120)
            assert compiled.returncode == 0, (command, compiled.stdout, compiled.stderr)

            def execute(*arguments: str) -> subprocess.CompletedProcess[bytes]:
                return subprocess.run([str(binary), *arguments], cwd=temporary,
                                      env=environment, capture_output=True, timeout=20)

            accepted = execute()
            assert (accepted.returncode, accepted.stdout.replace(b"\r\n", b"\n"), accepted.stderr) == (
                0, b"v4-panic-runtime-success=ok\n", b""), (variant, accepted.returncode, accepted.stdout, accepted.stderr)
            for case, message in messages.items():
                failed = execute(case)
                diagnostic = b"PANIC: " + message + b"\n"
                assert_exact_abort(failed, diagnostic)
                # Binary stderr on Windows preserves the sized payload exactly,
                # including an intentional CRLF and NUL, beyond normalization.
                assert failed.stderr == diagnostic, (variant, case, len(failed.stderr), len(diagnostic))
            for case, reason in rejected.items():
                failed = execute(case)
                assert_exact_abort(failed, ("FREAK: V4 word panic: " + reason + "\n").encode())
        mode = "plain portability" if args.plain else "AddressSanitizer + UndefinedBehaviorSanitizer"
        print(f"V4 panic runtime: {len(messages)} exact sized messages, {len(rejected)} named private-ABI failures, "
              f"direct + loan-probe builds, borrow alive through abort, no atexit, zero-owner success control; {mode} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
