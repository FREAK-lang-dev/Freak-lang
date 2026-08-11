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

GLOBAL_SCALING_PROGRAM = f"""pilot mut global_text: word = "s"

task main() {{
    repeat {APPENDS} times {{
        global_text = global_text + "x"
    }}
    say global_text.length()
    say global_text.checksum()
    global_text = ""
}}
"""

FIELD_SCALING_PROGRAM = f"""shape Box {{
    value: word
}}

task main() {{
    pilot box: Box = Box {{ value: "s" }}
    repeat {APPENDS} times {{
        box.value = box.value + "x"
    }}
    say box.value.length()
    say box.value.checksum()
    box.value = ""
}}
"""

FIELD_CORRECTNESS_PROGRAM = """shape Box {
    value: word
}

pilot mut suffix_calls: int = 0

task make_suffix() -> word {
    suffix_calls += 1
    give back "heap" + "suffix"
}

task main() {
    pilot box: Box = Box { value: "seed" }
    box.value = box.value + "12345678901"
    box.value = box.value + make_suffix()
    say box.value
    say suffix_calls
    box.value = ""
}
"""

CORRECTNESS_PROGRAM = """task main() {
    pilot mut text: word = "a" + "b"
    text = text + "123456789"
    text = text + text
    say text
    text = text + "123456789"
    text = text + ("heap" + "suffix")
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

OVERFLOW_PROBE = r"""#include "freak_runtime.h"
#include <stdint.h>
#include <string.h>

int main(int argc, char** argv) {
    freak_word small = freak_word_lit("x");
    freak_word malformed = { "x", SIZE_MAX, SIZE_MAX, false };
    if (argc > 1 && strcmp(argv[1], "append") == 0) {
        freak_word_append_owned(&small, malformed, false);
        return 0;
    }
    (void)freak_word_concat(small, malformed);
    return 0;
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


def sanitizer_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("ASAN_OPTIONS", None)
    if sys.platform.startswith("linux"):
        env["ASAN_OPTIONS"] = "halt_on_error=1:detect_leaks=1:exitcode=86"
    return env


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
    if backend == "llvm":
        command.append(str(repo / "freakc" / "runtime" / "freak_llvm_runtime.c"))
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
                executed = run([str(binary)], root, sanitizer_env())
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
            correctness_text = correctness_generated.read_text(encoding="utf-8")
            direct_append_marker = (
                "freak_word_append_owned(&"
                if backend == "c"
                else "call i64 @freak_llvm_word_append_owned"
            )
            assert correctness_text.count(direct_append_marker) == 5, (
                f"{backend} correctness case lost a direct append path"
            )
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
                audit=True,
                force_move=True,
            )
            correctness_executed = run(
                [str(correctness_binary)], root, sanitizer_env()
            )
            assert correctness_executed.returncode == 0, (
                correctness_executed.stdout + correctness_executed.stderr
            )
            assert correctness_executed.stdout.strip().splitlines() == [
                "ab123456789ab123456789",
                "ab123456789ab123456789123456789heapsuffix",
                "ab123456789ab123456789123456789heapsuffixyz",
                "yz",
                "borrowed",
                "borrowed!",
                "borrowed",
            ]
            assert "ownership audit found" not in correctness_executed.stderr
            match = AUDIT_RE.search(correctness_executed.stderr)
            assert match, correctness_executed.stderr
            correctness_stats = tuple(int(value) for value in match.groups())
            expected_correctness_prefix = {
                "c": (1, 9, 7, 6),
                "llvm": (5, 5, 8, 3),
            }[backend]
            assert correctness_stats[:4] == expected_correctness_prefix, (
                correctness_stats
            )

            additional_scaling = [("global", GLOBAL_SCALING_PROGRAM)]
            if backend == "llvm":
                additional_scaling.append(("field", FIELD_SCALING_PROGRAM))
            for scaling_name, scaling_program in additional_scaling:
                extra_source = root / f"scaling_{backend}_{scaling_name}.fk"
                extra_source.write_text(scaling_program, encoding="utf-8")
                extra_transpiled = run(
                    [str(freak), "transpile", str(extra_source), flag], repo
                )
                assert extra_transpiled.returncode == 0, (
                    extra_transpiled.stdout + extra_transpiled.stderr
                )
                extra_generated = Path(str(extra_source) + suffix)
                extra_text = extra_generated.read_text(encoding="utf-8")
                helper = (
                    "freak_word_append_owned"
                    if backend == "c"
                    else "@freak_llvm_word_append_owned"
                )
                assert helper in extra_text, extra_text
                extra_binary = root / (
                    f"scaling_{backend}_{scaling_name}.exe"
                    if sys.platform == "win32"
                    else f"scaling_{backend}_{scaling_name}"
                )
                compile_generated(
                    clang=clang,
                    repo=repo,
                    generated=extra_generated,
                    backend=backend,
                    binary=extra_binary,
                    audit=True,
                    force_move=True,
                )
                extra_run = run([str(extra_binary)], root, sanitizer_env())
                assert extra_run.returncode == 0, extra_run.stdout + extra_run.stderr
                assert extra_run.stdout.strip().splitlines() == expected_stdout, (
                    extra_run.stdout
                )
                match = AUDIT_RE.search(extra_run.stderr)
                assert match, extra_run.stderr
                stats = tuple(int(value) for value in match.groups())
                assert stats[0] == 0, stats
                assert stats[1] == APPENDS, stats
                assert stats[2] == stats[3], stats
                assert 1 <= stats[3] <= 16, stats
                assert stats[4] <= 4 * len(expected_bytes), stats
                assert "ownership audit found" not in extra_run.stderr
                assert "AddressSanitizer" not in extra_run.stderr
                print(
                    f"{backend}/{scaling_name}/move: concat_calls={stats[0]} "
                    f"append_calls={stats[1]} allocations={stats[2]} "
                    f"growths={stats[3]} copied_bytes={stats[4]}"
                )

            if backend == "llvm":
                field_source = root / "field_owned_suffix_llvm.fk"
                field_source.write_text(FIELD_CORRECTNESS_PROGRAM, encoding="utf-8")
                field_transpiled = run(
                    [str(freak), "transpile", str(field_source), "--llvm"], repo
                )
                assert field_transpiled.returncode == 0, (
                    field_transpiled.stdout + field_transpiled.stderr
                )
                field_generated = Path(str(field_source) + ".ll")
                field_text = field_generated.read_text(encoding="utf-8")
                assert field_text.count(
                    "call i64 @freak_llvm_word_append_owned"
                ) == 2, "LLVM field correctness case lost a direct append path"
                field_binary = root / (
                    "field_owned_suffix.exe"
                    if sys.platform == "win32"
                    else "field_owned_suffix"
                )
                compile_generated(
                    clang=clang,
                    repo=repo,
                    generated=field_generated,
                    backend="llvm",
                    binary=field_binary,
                    audit=True,
                    force_move=True,
                )
                field_run = run([str(field_binary)], root, sanitizer_env())
                assert field_run.returncode == 0, field_run.stdout + field_run.stderr
                assert field_run.stdout.strip().splitlines() == [
                    "seed12345678901heapsuffix",
                    "1",
                ], field_run.stdout
                match = AUDIT_RE.search(field_run.stderr)
                assert match, field_run.stderr
                field_stats = tuple(int(value) for value in match.groups())
                assert field_stats[:4] == (1, 2, 3, 2), field_stats
                assert "ownership audit found" not in field_run.stderr
                assert "AddressSanitizer" not in field_run.stderr

        overflow_source = root / "concat_overflow.c"
        overflow_source.write_text(OVERFLOW_PROBE, encoding="utf-8")
        overflow_binary = root / (
            "concat_overflow.exe" if sys.platform == "win32" else "concat_overflow"
        )
        overflow_command = [
            clang,
            "-O1",
            "-o",
            str(overflow_binary),
            str(overflow_source),
            str(repo / "freakc" / "runtime" / "freak_runtime.c"),
            "-I",
            str(repo / "freakc" / "runtime"),
        ]
        if sys.platform == "win32":
            overflow_command.append("-lws2_32")
        else:
            overflow_command.append("-lm")
        overflow_compiled = run(overflow_command, repo)
        assert overflow_compiled.returncode == 0, (
            overflow_compiled.stdout + overflow_compiled.stderr
        )
        for mode, expected_error in (
            ("concat", "word concatenation size overflow"),
            ("append", "word append size overflow"),
        ):
            command = [str(overflow_binary)]
            if mode == "append":
                command.append("append")
            overflow_run = run(command, root)
            assert overflow_run.returncode != 0, mode
            assert expected_error in overflow_run.stderr, overflow_run.stderr

    if args.measure_only:
        print("V3 word concat deterministic baseline: PASS")
    else:
        print("V3 word concat linear scaling: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
