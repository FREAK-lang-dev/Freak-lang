#!/usr/bin/env python3
"""Prove the private borrowed-word checked integer parser at O0/O2/O3.

Default requires ASan/UBSan and both ownership audits, including real capability
controls. --plain is a separate portability matrix. Commands, source identities,
binaries and every child result remain in a fresh --work directory. This does
not admit a public FREAK maybe ABI or compiler intrinsic.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import signal
import struct
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
OPTS = (0, 2, 3)
AUDIT_FLAGS = ("-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1", "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1")
SANITIZER_FLAGS = ("-fsanitize=address,undefined", "-fno-sanitize-recover=all", "-fno-omit-frame-pointer")
COMPILE_SECONDS, COMPILE_MIB = 120, 1024
RUN_SECONDS, RUN_MIB = 20, 64
ARRAY_FLAG = "-DFREAK_ARRAY_LIVE_LIMIT=1024"


def reference_parse(data: bytes) -> tuple[int, int]:
    """Independent byte grammar and decimal length comparison, without libc."""
    negative = data.startswith(b"-")
    digits = data[1:] if data[:1] in (b"+", b"-") else data
    if not digits or any(byte < 48 or byte > 57 for byte in digits):
        return 0, 0
    significant = digits.lstrip(b"0") or b"0"
    limit = b"9223372036854775808" if negative else b"9223372036854775807"
    if len(significant) > len(limit) or (len(significant) == len(limit) and significant > limit):
        return 0, 0
    value = int(significant)
    return 1, -value if negative else value


def semantic_cases() -> tuple[tuple[str, bytes], ...]:
    return (
        ("zero", b"0"), ("plus-zero", b"+0"), ("minus-zero", b"-0"),
        ("leading-zeros", b"00042"), ("plus", b"+42"), ("minus", b"-42"),
        ("maximum", b"9223372036854775807"), ("minimum", b"-9223372036854775808"),
        ("plus-maximum", b"+9223372036854775807"), ("zero-minimum", b"-0009223372036854775808"),
        ("empty", b""), ("sign-plus", b"+"), ("sign-minus", b"-"),
        ("double-sign", b"--1"), ("mixed-sign", b"+-1"),
        ("leading-space", b" 42"), ("trailing-space", b"42 "), ("tab", b"\t42"),
        ("newline", b"42\n"), ("decimal", b"4.2"), ("exponent", b"1e2"),
        ("hex", b"0x10"), ("separator", b"1_000"), ("prefix-junk", b"x12"),
        ("suffix-junk", b"12junk"), ("nul", b"\0"), ("nul-suffix", b"12\0junk"),
        ("nul-leading", b"\x0012"), ("fullwidth-digits", "１２".encode()),
        ("arabic-digit", "١".encode()), ("unicode-space", "\u00a042".encode()),
        ("unicode-suffix", "42😀".encode()),
        ("positive-overflow", b"9223372036854775808"),
        ("negative-overflow", b"-9223372036854775809"),
        ("huge-positive", b"99999999999999999999999999999999999999"),
        ("huge-negative", b"-99999999999999999999999999999999999999"),
        ("large-leading-zeros", b"0" * 262143 + b"7"),
        ("large-suffix", b"0" * 262143 + b"x"), ("large-overflow", b"9" * 262144),
    )


def expected_stdout() -> bytes:
    rows = []
    for name, data in semantic_cases():
        tag, value = reference_parse(data)
        rows.append(f"parse-int:{name}:{tag}:{value}\n".encode())
    return b"".join(rows) + b"borrow-and-status=ok\nlegacy-lenient=ok\nv4-word-parse-runtime=ok\n"


def output_bytes(value: str | bytes) -> bytes:
    return value.encode("utf-8") if isinstance(value, str) else value


def normalized(value: str | bytes, platform: str) -> bytes:
    data = output_bytes(value)
    return data.replace(b"\r\n", b"\n") if platform == "win32" else data


def exact_result(result: subprocess.CompletedProcess, status: int, stdout: bytes, stderr: bytes,
                 *, platform: str = sys.platform) -> None:
    actual = (result.returncode, normalized(result.stdout, platform), normalized(result.stderr, platform))
    expected = (status, stdout, stderr)
    if actual != expected:
        raise AssertionError(f"expected {expected!r}; actual {actual!r}")


def assert_success(result: subprocess.CompletedProcess, *, platform: str = sys.platform) -> None:
    exact_result(result, 0, expected_stdout(), b"", platform=platform)


def assert_named_panic(result: subprocess.CompletedProcess, reason: str,
                       *, platform: str = sys.platform) -> None:
    # Word-runtime stderr uses CRT text mode on Windows. Intentional abort skips
    # atexit audits; the observer variant checks the live borrow before abort.
    status = 3 if platform == "win32" else -signal.SIGABRT
    exact_result(result, status, b"", ("FREAK: V4 word panic: " + reason + "\n").encode(),
                 platform=platform)


def assert_audit(result: subprocess.CompletedProcess, kind: str, *, platform: str = sys.platform) -> None:
    if kind not in ("C", "LLVM"):
        raise AssertionError("unknown audit capability")
    exact_result(result, 87 if kind == "C" else 86, b"",
                 f"FREAK: {kind} ownership audit found 1 unreleased word allocation(s)\n".encode(),
                 platform=platform)


def assert_legacy_control(result: subprocess.CompletedProcess, *, platform: str = sys.platform) -> None:
    stdout, stderr = normalized(result.stdout, platform), normalized(result.stderr, platform)
    lines = stdout.splitlines(keepends=True)
    cases = semantic_cases()
    if (result.returncode != 0 or stderr or len(lines) != len(cases) + 3 or
            any(not line.startswith(f"parse-int:{name}:".encode()) or not line.endswith(b"\n")
                for line, (name, _) in zip(lines, cases)) or
            lines[-3:] != [b"borrow-and-status=ok\n", b"legacy-lenient=ok\n", b"v4-word-parse-runtime=ok\n"] or
            any(line not in lines for line in (b"parse-int:empty:1:0\n", b"parse-int:suffix-junk:1:12\n",
                                               b"parse-int:nul-suffix:1:12\n",
                                               b"parse-int:positive-overflow:1:9223372036854775807\n",
                                               b"parse-int:negative-overflow:1:-9223372036854775808\n"))):
        raise AssertionError("legacy negative control did not produce complete ordinary lenient results")
    try:
        assert_success(result, platform=platform)
    except AssertionError:
        return
    raise AssertionError("checked-parser oracle accepted the legacy lenient adapter")


def assert_sanitizer(result: subprocess.CompletedProcess, kind: str) -> None:
    signatures = {
        "address": (b"ERROR: AddressSanitizer: heap-use-after-free", b"SUMMARY: AddressSanitizer:"),
        "undefined": (b"runtime error: signed integer overflow", b"SUMMARY: UndefinedBehaviorSanitizer:"),
    }
    if kind not in signatures:
        raise AssertionError("unknown sanitizer capability")
    stderr = output_bytes(result.stderr)
    if (result.returncode != 88 or output_bytes(result.stdout) != b"" or
            any(token not in stderr for token in signatures[kind]) or
            any(token in stderr for token in (b"FREAK: V4 word panic:", b"ownership audit", b"LeakSanitizer"))):
        raise AssertionError(f"missing real {kind} sanitizer capability: {result.returncode}, {stderr!r}")


def rejection_cases(pointer_bytes: int = struct.calcsize("P")) -> dict[str, str]:
    cases = {f"utf8-{index}": "invalid UTF-8" for index in range(13)}
    cases.update({"utf8-after-overflow": "invalid UTF-8", "utf8-after-junk": "invalid UTF-8",
                  "null": "word value has been consumed", "foreign": "word value is not live owned storage",
                  "unknown": "word value is not live owned storage", "negative": "word value is not live owned storage",
                  "stale": "word value is not live owned storage", "size-max": "byte length overflow"})
    for case in ("null-tag", "null-value", "null-both", "alias-slots"):
        cases[case] = cases[case + "-poison"] = "invalid checked integer result slots"
    if pointer_bytes > 4:
        cases["signed-overflow"] = "byte length overflow"
    return cases


def validate_build_flags(flags: list[str], sanitized: bool) -> None:
    required = (*AUDIT_FLAGS, ARRAY_FLAG, *(SANITIZER_FLAGS if sanitized else ()))
    if any(flag not in flags for flag in required) or "-DNDEBUG" in flags:
        raise AssertionError("required audits, resource ceiling, assertions or sanitizer flags missing")


def validate_completion(report: dict, sanitized: bool,
                        pointer_bytes: int = struct.calcsize("P")) -> None:
    matrices = {(opt, variant) for opt in (0, 2, 3) for variant in ("direct", "observer")}
    actual_matrices = [(row["opt"], row["variant"]) for row in report["matrices"]]
    rejections = {(opt, variant, case) for opt, variant in matrices for case in rejection_cases(pointer_bytes)}
    actual_rejections = [(row["opt"], row["variant"], row["case"]) for row in report["rejections"]]
    capabilities = {f"audit-{kind}-O{opt}" for opt in (0, 2, 3) for kind in ("C", "LLVM")}
    capabilities |= {f"observer-O{opt}" for opt in (0, 2, 3)} | {"legacy-oracle-negative"}
    if sanitized:
        capabilities |= {"sanitizer-address", "sanitizer-undefined"}
    if (OPTS != (0, 2, 3) or report["sanitized"] != sanitized or
            len(actual_matrices) != len(matrices) or set(actual_matrices) != matrices or
            any(row["semantics"] != 39 for row in report["matrices"]) or
            len(actual_rejections) != len(rejections) or set(actual_rejections) != rejections or
            len(report["capabilities"]) != len(capabilities) or set(report["capabilities"]) != capabilities):
        raise AssertionError("incomplete mandatory optimization/variant/capability matrix")


@contextmanager
def sanitizer_environment(sanitized: bool):
    names = ("ASAN_OPTIONS", "LSAN_OPTIONS", "UBSAN_OPTIONS")
    previous = {name: os.environ.get(name) for name in names}
    try:
        for name in names:
            os.environ.pop(name, None)
        if sanitized:
            os.environ["ASAN_OPTIONS"] = "halt_on_error=1:detect_leaks=1:exitcode=88"
            os.environ["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1:exitcode=88"
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_checks():
    path = ROOT / "src/compiler/v4/check_v4.py"
    spec = importlib.util.spec_from_file_location("word_parse_runtime_checks", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Runner:
    def __init__(self, checks, directory: Path):
        self.checks, self.directory, self.serial = checks, directory, 0

    def run(self, command: list[str], label: str, *, compile: bool = False):
        self.serial += 1
        stem = self.directory / f"{self.serial:03d}-{re.sub(r'[^a-zA-Z0-9_-]', '-', label)}"
        timeout = COMPILE_SECONDS if compile else RUN_SECONDS
        memory = COMPILE_MIB if compile else RUN_MIB
        stem.with_suffix(".command.json").write_text(json.dumps(
            {"argv": command, "timeout_seconds": timeout, "memory_limit_mib": memory}, indent=2) + "\n")
        try:
            result = self.checks.run_with_heartbeat(command, label=label, timeout_seconds=timeout,
                                                  memory_limit_mb=memory)
        except Exception as error:
            stem.with_suffix(".failure.txt").write_text(str(error), encoding="utf-8")
            for channel in ("stdout", "stderr"):
                value = getattr(error, "output" if channel == "stdout" else channel, None)
                if value is not None:
                    stem.with_suffix("." + channel).write_bytes(output_bytes(value))
            raise
        stem.with_suffix(".stdout").write_bytes(output_bytes(result.stdout))
        stem.with_suffix(".stderr").write_bytes(output_bytes(result.stderr))
        stem.with_suffix(".result.json").write_text(json.dumps({"exit": result.returncode}, indent=2) + "\n")
        return result


def run_gate(args, directory: Path, report: dict) -> None:
    checks = load_checks()
    runner = Runner(checks, directory)
    runtime = ROOT / "freakc/runtime"
    paths = [runtime / name for name in ("freak_runtime.c", "freak_runtime.h",
                                        "freak_v4_word_runtime.c", "freak_v4_word_runtime.h")]
    paths += [Path(__file__).resolve(), ROOT / "tests/v4_word_parse_runtime_probe.c",
              ROOT / "tests/test_v4_word_parse_runtime.py", ROOT / "src/compiler/v4/check_v4.py"]
    report["source_hashes"] = {str(path.relative_to(ROOT)): sha(path) for path in paths}
    clang = Path(shutil.which(args.clang) or args.clang).resolve(strict=True)
    report["clang"] = {"requested": args.clang, "resolved": str(clang), "sha256": sha(clang)}
    suffix = ".exe" if sys.platform == "win32" else ""
    platform_libs = ["-lws2_32"] if sys.platform == "win32" else ["-lm"]
    probe = ROOT / "tests/v4_word_parse_runtime_probe.c"
    production = runtime / "freak_v4_word_runtime.c"
    for opt in OPTS:
        flags = ["-std=c11", f"-O{opt}", "-g", *AUDIT_FLAGS, ARRAY_FLAG, "-I", str(runtime)]
        if not args.plain:
            flags += SANITIZER_FLAGS
        validate_build_flags(flags, not args.plain)
        report["flags"][str(opt)] = flags
        checked = runner.run([str(clang), *flags, "-Wall", "-Wextra", "-Werror", "-c", str(production),
                              "-o", str(directory / f"production.O{opt}.o")], f"production TU O{opt}", compile=True)
        if checked.returncode != 0:
            raise AssertionError(f"production TU rejected: {checked.stdout}{checked.stderr}")
        for variant in ("direct", "observer"):
            binary = directory / f"word-parse-{variant}.O{opt}{suffix}"
            command = [str(clang), *flags, str(probe)]
            if variant == "direct":
                command += ["-DFREAK_V4_WORD_PARSE_DIRECT_LINK=1", str(production)]
            command += ["-o", str(binary), *platform_libs]
            compiled = runner.run(command, f"compile {variant} O{opt}", compile=True)
            if compiled.returncode != 0:
                raise AssertionError(f"probe compilation failed: {compiled.stdout}{compiled.stderr}")
            assert_success(runner.run([str(binary)], f"semantics {variant} O{opt}"))
            report["matrices"].append({"variant": variant, "opt": opt, "semantics": len(semantic_cases()),
                                       "binary_sha256": sha(binary)})
            for case, reason in rejection_cases().items():
                assert_named_panic(runner.run([str(binary), case], f"reject {variant} O{opt} {case}"), reason)
                report["rejections"].append({"variant": variant, "opt": opt, "case": case})
            if variant == "direct":
                for kind in ("C", "LLVM"):
                    assert_audit(runner.run([str(binary), "audit-" + kind], f"audit {kind} O{opt}"), kind)
                    report["capabilities"].append(f"audit-{kind}-O{opt}")
                if not args.plain and opt == 0:
                    for kind in ("address", "undefined"):
                        assert_sanitizer(runner.run([str(binary), "cap-" + kind], f"sanitizer {kind}"), kind)
                        report["capabilities"].append("sanitizer-" + kind)
            else:
                exact_result(runner.run([str(binary), "cap-observer"], f"observer capability O{opt}"), 90, b"",
                             b"word-parse-probe: parser allocated or freed storage\n")
                report["capabilities"].append(f"observer-O{opt}")
    negative = directory / ("legacy-negative.O0" + suffix)
    flags = report["flags"]["0"]
    compiled = runner.run([str(clang), *flags, "-DFREAK_V4_WORD_PARSE_DIRECT_LINK=1",
                           "-DFREAK_V4_WORD_PARSE_LEGACY_CONTROL=1", str(probe), str(production),
                           "-o", str(negative), *platform_libs], "compile legacy oracle negative", compile=True)
    if compiled.returncode != 0:
        raise AssertionError(f"legacy negative compilation failed: {compiled.stdout}{compiled.stderr}")
    assert_legacy_control(runner.run([str(negative)], "legacy oracle negative"))
    report["capabilities"].append("legacy-oracle-negative")
    validate_completion(report, not args.plain)
    for path in paths:
        if sha(path) != report["source_hashes"][str(path.relative_to(ROOT))]:
            raise AssertionError("source changed during native proof")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG") or shutil.which("clang"))
    parser.add_argument("--plain", action="store_true")
    parser.add_argument("--work", type=Path)
    args = parser.parse_args()
    if not args.clang:
        parser.error("Clang is required; missing capabilities cannot be skipped")
    if not args.plain and not sys.platform.startswith("linux"):
        parser.error("mandatory sanitizer gate requires Linux; --plain is additional portability proof")
    if args.work:
        directory = args.work.resolve()
        directory.mkdir(parents=True, exist_ok=False)
    else:
        directory = Path(tempfile.mkdtemp(prefix="freak-v4-word-parse-"))
    report = {"complete": False, "platform": sys.platform, "sanitized": not args.plain,
              "budgets": {"compile_seconds": COMPILE_SECONDS, "compile_mib": COMPILE_MIB,
                          "run_seconds": RUN_SECONDS, "run_mib": RUN_MIB, "array_handles": 1024},
              "flags": {}, "matrices": [], "rejections": [], "capabilities": []}
    print(f"V4 checked-word parser artifacts: {directory}", flush=True)
    try:
        with sanitizer_environment(not args.plain):
            run_gate(args, directory, report)
        report["complete"] = True
    except Exception as error:
        report["failure"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        (directory / "results.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        manifest = {path.name: {"bytes": path.stat().st_size, "sha256": sha(path)}
                    for path in sorted(directory.iterdir()) if path.is_file() and path.name != "artifact-hashes.json"}
        (directory / "artifact-hashes.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"V4 checked-word parser PASS: 6 matrices, {len(report['rejections'])} private rejections, "
          f"{len(report['capabilities'])} real capabilities; {'plain' if args.plain else 'ASan/UBSan'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
