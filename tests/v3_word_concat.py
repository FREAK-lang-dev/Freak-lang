#!/usr/bin/env python3
"""Prove repeated V3 word self-concatenation has linear copy work."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


APPENDS = 8192
SCALING_PROGRAM = f"""task main() {{
    pilot mut text: word = "s"
    repeat {APPENDS} times {{
        text = text + "x"
    }}
    say text.length()
    say text.checksum()
}}
"""

CORRECTNESS_PROGRAM = """task main() {
    pilot mut text: word = "a" + "b"
    text = text + text
    say text
    pilot suffix: word = "y" + "z"
    text = text + suffix
    say text
    say suffix
    pilot source: word = "borrow" + "ed"
    pilot derived: word = source + "!"
    say source
    say derived
    say source
}
"""

AUDIT_RE = re.compile(
    r"FREAK concat audit: concat_calls=(\d+) append_calls=(\d+) "
    r"allocations=(\d+) growths=(\d+) copied_bytes=(\d+)"
)


def run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=180,
        check=False,
    )


def stable_checksum(data: bytes) -> int:
    value = 14695981039346656037
    for byte in data:
        value ^= byte
        value = (value * 1099511628211) & ((1 << 64) - 1)
    return value & ((1 << 63) - 1)


def compile_generated(
    *,
    clang: str,
    repo: Path,
    generated: Path,
    backend: str,
    binary: Path,
    audit: bool,
    force_move: bool,
) -> None:
    command = [clang, "-g", "-O1", "-o", str(binary), str(generated)]
    if backend == "llvm":
        command.append("-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1")
    else:
        command.append("-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1")
    if audit:
        command.append("-DFREAK_WORD_CONCAT_AUDIT=1")
    if force_move:
        command.append("-DFREAK_WORD_CONCAT_FORCE_MOVE=1")
    command.extend(
        [
            str(repo / "freakc" / "runtime" / "freak_runtime.c"),
            "-I",
            str(repo / "freakc" / "runtime"),
        ]
    )
    if sys.platform == "win32":
        command.append("-lws2_32")
    else:
        command.extend(["-lm", "-fsanitize=address", "-fno-omit-frame-pointer"])
    compiled = run(command, repo)
    assert compiled.returncode == 0, compiled.stdout + compiled.stderr


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("freak", type=Path)
    parser.add_argument(
        "--measure-only",
        action="store_true",
        help="print the pre-optimization deterministic work baseline",
    )
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    freak = args.freak.resolve()
    assert freak.is_file(), freak
    clang = os.environ.get("FREAK_CLANG") or shutil.which("clang")
    assert clang, "clang is required for the concat regression"

    expected_bytes = b"s" + (b"x" * APPENDS)
    expected_stdout = [str(len(expected_bytes)), str(stable_checksum(expected_bytes))]

    with tempfile.TemporaryDirectory(prefix="freak-v3-word-concat-") as tmp:
        root = Path(tmp)
        for backend, flag, suffix in (("c", "--c", ".c"), ("llvm", "--llvm", ".ll")):
            source = root / f"scaling_{backend}.fk"
            source.write_text(SCALING_PROGRAM, encoding="utf-8")
            transpiled = run([str(freak), "transpile", str(source), flag], repo)
            assert transpiled.returncode == 0, transpiled.stdout + transpiled.stderr
            generated = Path(str(source) + suffix)
            generated_text = generated.read_text(encoding="utf-8")
            if not args.measure_only:
                helper = (
                    "freak_word_append_owned"
                    if backend == "c"
                    else "@freak_llvm_word_append_owned"
                )
                assert helper in generated_text, generated_text

            modes = (False,) if args.measure_only else (False, True)
            for force_move in modes:
                mode = "move" if force_move else "normal"
                binary = root / (
                    f"scaling_{backend}_{mode}.exe"
                    if sys.platform == "win32"
                    else f"scaling_{backend}_{mode}"
                )
                compile_generated(
                    clang=clang,
                    repo=repo,
                    generated=generated,
                    backend=backend,
                    binary=binary,
                    audit=True,
                    force_move=force_move,
                )
                env = os.environ.copy()
                env["ASAN_OPTIONS"] = "halt_on_error=1:detect_leaks=1"
                executed = run([str(binary)], root, env)
                assert executed.returncode == 0, executed.stdout + executed.stderr
                assert executed.stdout.strip().splitlines() == expected_stdout, executed.stdout
                match = AUDIT_RE.search(executed.stderr)
                assert match, executed.stderr
                stats = tuple(int(value) for value in match.groups())
                concat_calls, append_calls, allocations, growths, copied_bytes = stats
                print(
                    f"{backend}/{mode}: concat_calls={concat_calls} "
                    f"append_calls={append_calls} allocations={allocations} "
                    f"growths={growths} copied_bytes={copied_bytes}"
                )
                if args.measure_only:
                    expected_quadratic = APPENDS * (APPENDS + 3) // 2
                    assert stats == (APPENDS, 0, APPENDS, 0, expected_quadratic), stats
                else:
                    assert concat_calls == 0, stats
                    assert append_calls == APPENDS, stats
                    assert allocations == growths, stats
                    assert 1 <= growths <= 16, stats
                    assert copied_bytes <= 4 * len(expected_bytes), stats
                assert "ownership audit found" not in executed.stderr
                assert "AddressSanitizer" not in executed.stderr

            if args.measure_only:
                continue

            correctness_source = root / f"correctness_{backend}.fk"
            correctness_source.write_text(CORRECTNESS_PROGRAM, encoding="utf-8")
            correctness_transpiled = run(
                [str(freak), "transpile", str(correctness_source), flag], repo
            )
            assert correctness_transpiled.returncode == 0, (
                correctness_transpiled.stdout + correctness_transpiled.stderr
            )
            correctness_generated = Path(str(correctness_source) + suffix)
            correctness_binary = root / (
                f"correctness_{backend}.exe"
                if sys.platform == "win32"
                else f"correctness_{backend}"
            )
            compile_generated(
                clang=clang,
                repo=repo,
                generated=correctness_generated,
                backend=backend,
                binary=correctness_binary,
                audit=False,
                force_move=True,
            )
            correctness_executed = run([str(correctness_binary)], root)
            assert correctness_executed.returncode == 0, (
                correctness_executed.stdout + correctness_executed.stderr
            )
            assert correctness_executed.stdout.strip().splitlines() == [
                "abab",
                "ababyz",
                "yz",
                "borrowed",
                "borrowed!",
                "borrowed",
            ]
            assert "ownership audit found" not in correctness_executed.stderr

    if args.measure_only:
        print("V3 word concat deterministic baseline: PASS")
    else:
        print("V3 word concat linear scaling: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
