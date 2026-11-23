#!/usr/bin/env python3
"""Execute generated V4 word programs with both ownership audits enabled.

ASan and UBSan are mandatory by default. --plain adds a portability proof; it
does not substitute for the sanitizer gate. The bootstrap compiler runs once,
and each authored native program is emitted and executed in its own process.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/compiler/v4"))
import build_v4 as build  # noqa: E402


EXPECTED = {
    "owned_words.fk": "café 🐱\ncafé 🐱\ncafé 🐱!\ncafé 🐱!!\ncafé 🐱\n\nA\0B\n-42\ntrue\n12.5\n",
    "owned_word_scopes.fk": "shadow\ninner\nsurvivor\nreplacement\ndefault return cleanup\n",
    "owned_word_return_temporary.fk": "first\nsecond\ntransfer\ntransfer\n",
    "owned_word_aggregates.fk": "6\nada!\nada+\n17\nada+\n21\nx#\n8\n8\nr+++\n3\nsecond\n",
    "drops_try_native.fk": "positivekeep\nnegative\nnegative\nnegative\n13\none!\nnone\nother\nother\n",
    "drops_native.fk": ("5\n9\n3\n13\n0\nsxxxxx\nh2\n4\ntaken\nrepaired\nl\nr\nsecond\nx1\n12\nmaybe\n3\n3\n"
                        "B\nuno\nnewer\ncd\n1\nrenamed\nreset\n5\n5\n6\n9\n9\n9\n1\n53\n9\nbox\n1\n0\n"),
    "lend_abi_native.fk": ("8\n16\n3\ntrue\ntrue\ntrue\ntrue\ntrue\n7\n13\n14\n14\n28\n20\n-1\n9\n0\n30\n12\n2\n3\nada\n"
                           "4\n0\n6\ngo!!\n4\n14\n29\n29\n100\n6\n18\n4\ngo!!?\n21\n15\n8\n11\n8\nyz\nl0!\nfresher\n7\n"),
    "lists_native.fk": ("4\n6\n10\n14\n304\n0\n5\np0\np1\np2\nextra\nreplaced\nreplaced\np2\n4\ncsolo\n"
                        "one1\ntwo2\nTakeru!\nMeiya!\nSumika!\n10\n14\np0\np1\n3\n2.5\n2\n14\n"),
    "lists_nested_native.fk": ("Sumika/Takeru!/Meiya\n5\n5\n2\nKei\n13\nca\n43\n76\n3\nx\ny\nz\nz\nA!\nB!\n4\nkei\n149\n"
                               "0\n4\n15\n-1\n26\n7\n13\n5\nc\n6\nMitsurugi\n"),
    "maps_native.fk": ("10\n3\nSumika\nTakeru!\n3\n100\n9850\n34\n66\nfalse\n16\n-1\n66\n2\nuno\ntres\n"
                       "none\n6\nk\n1\n2\ntrue\ntrue\nfalse\n1\n20\n4\n"),
    "word_interpolation.fk": "Ada: count=7; rate=1.25; ready=true\nAda\ninner\nAda\nhi Ada\nleft\0right é\n{} {{name}} {name()}\nopen {name\n",
}


def assert_native_output(result, expected: str, *, platform: str | None = None) -> str:
    """Require exact output; normalize only the Windows CRT text newlines."""
    platform = sys.platform if platform is None else platform
    actual = result.stdout.replace("\r\n", "\n") if platform == "win32" else result.stdout
    if (result.returncode, actual, result.stderr) != (0, expected, ""):
        raise RuntimeError(
            "expected exit0, exact output and empty stderr; "
            f"actual exit={result.returncode}, stdout={result.stdout!r}, stderr={result.stderr!r}")
    return actual


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG") or shutil.which("clang"))
    parser.add_argument("--plain", action="store_true")
    parser.add_argument("--compiler-opt", type=int, choices=(0, 1, 2, 3), default=0)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if not args.clang:
        parser.error("clang is required; the generated native gate cannot be skipped")

    checks = build.checks
    compiler = build.bootstrap(args.clang, args.compiler_opt)
    target = build.host_target()
    report = {"target": target, "sanitizers": not args.plain,
              "ownership_audits": ["C", "LLVM"], "programs": []}
    sanitizer_variables = ("ASAN_OPTIONS", "LSAN_OPTIONS", "UBSAN_OPTIONS")
    previous = {name: os.environ.get(name) for name in sanitizer_variables}
    try:
        for name in sanitizer_variables:
            os.environ.pop(name, None)
        if not args.plain:
            os.environ["ASAN_OPTIONS"] = "halt_on_error=1:detect_leaks=1:exitcode=86"
            os.environ["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1:exitcode=85"
        with tempfile.TemporaryDirectory(prefix="freak-v4-owned-codegen-") as temporary:
            directory = Path(temporary)
            for name, expected in EXPECTED.items():
                source = checks.V4_ROOT / "examples" / name
                module = build.emit_module(compiler, source, target)
                llvm_path = directory / (name + ".ll")
                llvm_path.write_bytes(module.encode("utf-8"))
                binary = directory / (name + (".exe" if os.name == "nt" else ".native"))
                command = build.native_link_command(args.clang, llvm_path, binary)
                command += ["-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1",
                            "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1"]
                if not args.plain:
                    command += ["-g", "-fsanitize=address,undefined",
                                "-fno-omit-frame-pointer"]
                linked = checks.run_with_heartbeat(
                    command, label=f"owned word native link: {name}",
                    timeout_seconds=120, memory_limit_mb=512,
                )
                if linked.returncode != 0:
                    raise RuntimeError(f"{name} native link failed:\n{linked.stdout}{linked.stderr}")
                native = checks.run_with_heartbeat(
                    [str(binary)], label=f"owned word native execute: {name}",
                    timeout_seconds=30, memory_limit_mb=128,
                )
                actual = assert_native_output(native, expected)
                report["programs"].append({
                    "source": name,
                    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    "module_sha256": hashlib.sha256(module.encode("utf-8")).hexdigest(),
                    "stdout_sha256": hashlib.sha256(actual.encode("utf-8")).hexdigest(),
                    "status": "pass",
                })
                print(f"{name}: exact native output, zero owners, "
                      + ("plain portability PASS" if args.plain else "ASan + UBSan PASS"), flush=True)
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
