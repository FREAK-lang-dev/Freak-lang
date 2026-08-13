#!/usr/bin/env python3
"""Prove V3 word repetition and opaque builders on the C and LLVM backends."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


COMPILER_SOURCES = (
    "src/compiler/v3/globals.fk",
    "src/compiler/v3/helpers.fk",
    "src/compiler/v3/lexer.fk",
    "src/compiler/v3/parser.fk",
    "src/compiler/v3/checker.fk",
    "src/compiler/v3/emit_c.fk",
    "src/compiler/v3/emit_llvm.fk",
    "src/compiler/v3/main.fk",
)

CLI_SOURCES = (
    "std/version.fk",
    "src/compiler/v3/globals.fk",
    "src/compiler/v3/helpers.fk",
    "src/compiler/v3/lexer.fk",
    "src/compiler/v3/parser.fk",
    "src/compiler/v3/checker.fk",
    "src/compiler/v3/emit_c.fk",
    "src/compiler/v3/emit_llvm.fk",
    "src/cli/version.fk",
    "src/cli/toml.fk",
    "src/cli/lockfile.fk",
    "src/cli/build.fk",
    "src/cli/run.fk",
    "src/cli/hangar.fk",
    "src/cli/doctor.fk",
    "src/cli/audit.fk",
    "src/cli/main.fk",
)


FOUNDATION_PROGRAM = """task make_pattern() -> word {
    give back "na" + "ka"
}

task main() {
    say "ha".repeated(3)
    say "".repeated(9).length()
    say "x".repeated(0).length()
    say "x".repeated(0 - 2).length()
    say make_pattern().repeated(1)
    say "é".repeated(3).length()

    pilot known = word_builder::with_capacity(64)
    say word_builder::capacity(known)
    word_builder::append(known, "alpha")
    word_builder::append(known, ":" + "beta")
    word_builder::append_char(known, 128578)
    word_builder::append_int(known, 0 - 42)
    say word_builder::length(known)
    pilot known_word = word_builder::finish(known)
    say known_word

    pilot dynamic = word_builder::new()
    word_builder::append(dynamic, "0123456789")
    word_builder::append(dynamic, "abcdefghij")
    say word_builder::capacity(dynamic)
    say word_builder::length(dynamic)
    word_builder::clear(dynamic)
    say word_builder::capacity(dynamic)
    word_builder::append(dynamic, "z")
    say word_builder::length(dynamic)
    pilot dynamic_word = word_builder::finish(dynamic)
    say dynamic_word

    pilot reserved = word_builder::new()
    word_builder::reserve(reserved, 48)
    word_builder::reserve(reserved, 12)
    say word_builder::capacity(reserved)
    word_builder::discard(reserved)

    pilot empty = word_builder::new()
    pilot empty_word = word_builder::finish(empty)
    say empty_word.length()
}
"""

EXPECTED_STDOUT = [
    "hahaha",
    "0",
    "0",
    "0",
    "naka",
    "6",
    "64",
    "17",
    "alpha:beta🙂-42",
    "32",
    "20",
    "32",
    "1",
    "z",
    "48",
    "0",
]

STALE_FINISH_PROGRAM = """task main() {
    pilot builder = word_builder::new()
    pilot alias = builder
    word_builder::append(builder, "done")
    pilot value = word_builder::finish(builder)
    say value
    say word_builder::capacity(alias)
}
"""

STALE_DISCARD_PROGRAM = """task main() {
    pilot builder = word_builder::new()
    pilot alias = builder
    word_builder::discard(builder)
    word_builder::append(alias, "nope")
}
"""

LEAK_PROGRAM = """task main() {
    pilot builder = word_builder::new()
    word_builder::append(builder, "live")
    say word_builder::length(builder)
}
"""

STDLIB_PROGRAM = """task main() {
    say string_repeat("go", 3)
    say string_repeat("stop", 0).length()
    say string_repeat("é", 2).length()
}
"""

NEGATIVE_PROGRAM = """shape word_builder {}

task main() {
    pilot mut value: word = "x"
    value += "y"
    say "x".repeated("three")
    word_builder::append(1, 2)
}
"""

RUNTIME_PROBE = r'''#include "freak_runtime.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern void freak_llvm_word_release_replaced(int64_t previous, int64_t replacement);

static int check_utf8_and_ints(void) {
    static const char utf8[] = "\xc3\xa9";
    static const char repeated_utf8[] = "\xc3\xa9\xc3\xa9\xc3\xa9";
    freak_word c_repeat = freak_word_repeated(freak_word_lit(utf8), 3);
    if (!c_repeat.heap || c_repeat.length != 6 ||
            memcmp(c_repeat.data, repeated_utf8, 6) != 0) return 10;
    freak_word_release_owned(&c_repeat);
    freak_word one = freak_word_repeated(freak_word_lit("owned"), 1);
    if (!one.heap || one.data == (const char*)"owned" || strcmp(one.data, "owned") != 0) return 14;
    freak_word_release_owned(&one);

    int64_t llvm_repeat = freak_llvm_word_repeated((int64_t)utf8, 3);
    if (strlen((const char*)llvm_repeat) != 6 ||
            memcmp((const char*)llvm_repeat, repeated_utf8, 6) != 0) return 11;
    freak_llvm_word_release_replaced(llvm_repeat, 0);
    int64_t llvm_one = freak_llvm_word_repeated((int64_t)"owned", 1);
    if (llvm_one == (int64_t)"owned" || strcmp((const char*)llvm_one, "owned") != 0) return 15;
    freak_llvm_word_release_replaced(llvm_one, 0);

    int64_t c_builder = freak_word_builder_with_capacity(64);
    freak_word_builder_append_int(c_builder, INT64_MIN);
    freak_word_builder_append(c_builder, freak_word_lit(":"));
    freak_word_builder_append_int(c_builder, INT64_MAX);
    freak_word c_value = freak_word_builder_finish(c_builder);
    if (strcmp(c_value.data, "-9223372036854775808:9223372036854775807") != 0) return 12;
    freak_word_release_owned(&c_value);

    int64_t llvm_builder = freak_llvm_word_builder_with_capacity(64);
    freak_llvm_word_builder_append_int(llvm_builder, INT64_MIN);
    freak_llvm_word_builder_append(llvm_builder, (int64_t)":");
    freak_llvm_word_builder_append_int(llvm_builder, INT64_MAX);
    int64_t llvm_value = freak_llvm_word_builder_finish(llvm_builder);
    if (strcmp((const char*)llvm_value, "-9223372036854775808:9223372036854775807") != 0) return 13;
    freak_llvm_word_release_replaced(llvm_value, 0);
    return 0;
}

int main(int argc, char** argv) {
    const char* mode = argc > 1 ? argv[1] : "correctness";
    if (strcmp(mode, "repeat-c-overflow") == 0) {
        freak_word malformed = { "x", SIZE_MAX, SIZE_MAX, false };
        (void)freak_word_repeated(malformed, 2);
        return 0;
    }
    if (strcmp(mode, "repeat-llvm-overflow") == 0) {
        (void)freak_llvm_word_repeated((int64_t)"xx", INT64_MAX);
        return 0;
    }
    if (strcmp(mode, "builder-overflow") == 0) {
        int64_t builder = freak_word_builder_new();
        freak_word malformed = { "x", SIZE_MAX, SIZE_MAX, false };
        freak_word_builder_append(builder, malformed);
        return 0;
    }
    if (strcmp(mode, "bad-char") == 0) {
        int64_t builder = freak_word_builder_new();
        int64_t scalar = argc > 2 ? strtoll(argv[2], NULL, 10) : 0xd800;
        freak_word_builder_append_char(builder, scalar);
        return 0;
    }
    if (strcmp(mode, "negative-capacity") == 0) {
        (void)freak_word_builder_with_capacity(-1);
        return 0;
    }
    if (strcmp(mode, "stale-c") == 0) {
        int64_t builder = freak_word_builder_new();
        int64_t alias = builder;
        freak_word value = freak_word_builder_finish(builder);
        freak_word_release_owned(&value);
        (void)freak_word_builder_new();
        return (int)freak_word_builder_length(alias);
    }
    if (strcmp(mode, "stale-llvm") == 0) {
        int64_t builder = freak_llvm_word_builder_new();
        int64_t alias = builder;
        int64_t value = freak_llvm_word_builder_finish(builder);
        freak_llvm_word_release_replaced(value, 0);
        (void)freak_llvm_word_builder_new();
        return (int)freak_llvm_word_builder_length(alias);
    }
    return check_utf8_and_ints();
}
'''

AUDIT_RE = re.compile(
    r"FREAK word foundation audit: repeat_calls=(\d+) "
    r"repeat_allocations=(\d+) repeat_copied_bytes=(\d+) "
    r"builder_creations=(\d+) builder_allocations=(\d+) "
    r"builder_growths=(\d+) builder_copied_bytes=(\d+) "
    r"builder_finishes=(\d+) builder_discards=(\d+)"
)


def run(
    command: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: int = 180,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def sanitizer_env(*, detect_leaks: bool = True) -> dict[str, str]:
    env = os.environ.copy()
    env.pop("ASAN_OPTIONS", None)
    env.pop("LSAN_OPTIONS", None)
    if sys.platform.startswith("linux"):
        env["ASAN_OPTIONS"] = (
            "halt_on_error=1:detect_leaks=1:exitcode=86"
            if detect_leaks
            else "halt_on_error=1:detect_leaks=0"
        )
    return env


def compile_generated(
    *,
    clang: str,
    repo: Path,
    runtime_root: Path,
    generated: Path,
    backend: str,
    binary: Path,
) -> None:
    command = [
        clang,
        "-g",
        "-O1",
        "-DFREAK_WORD_FOUNDATION_AUDIT=1",
        "-o",
        str(binary),
        str(generated),
    ]
    if backend == "llvm":
        command.extend(
            [
                "-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1",
                str(runtime_root / "freak_llvm_runtime.c"),
            ]
        )
    else:
        command.append("-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1")
    command.extend([str(runtime_root / "freak_runtime.c"), "-I", str(runtime_root)])
    if sys.platform == "win32":
        command.append("-lws2_32")
    else:
        command.extend(["-lm", "-fsanitize=address", "-fno-omit-frame-pointer"])
    compiled = run(command, repo)
    assert compiled.returncode == 0, compiled.stdout + compiled.stderr


def build_fresh_cli(*, clang: str, repo: Path, root: Path, runtime_root: Path) -> Path:
    """Reconstruct an exact-current-source V3 compiler and full CLI outside the repo."""
    executable_suffix = ".exe" if sys.platform == "win32" else ""
    link_flags = ["-lws2_32"] if sys.platform == "win32" else ["-lm"]
    common = [
        "-O2",
        "-w",
        "-D_CRT_SECURE_NO_WARNINGS",
        "-I",
        str(runtime_root),
        *link_flags,
    ]
    compiler_aggregate = root / "freakc_v3.fk"
    compiler_aggregate.write_bytes(
        b"".join((repo / path).read_bytes() for path in COMPILER_SOURCES)
    )
    seed = root / f"freakc_seed{executable_suffix}"
    seed_build = run(
        [
            clang,
            "-o",
            str(seed),
            str(repo / "build/freakc_v3.fk.c"),
            str(runtime_root / "freak_runtime.c"),
            *common,
        ],
        root,
    )
    assert seed_build.returncode == 0, seed_build.stdout + seed_build.stderr

    previous = seed
    stage2: Path | None = None
    for generation in (1, 2):
        emitted = Path(str(compiler_aggregate) + ".c")
        emitted.unlink(missing_ok=True)
        generated = run([str(previous), str(compiler_aggregate), "--c"], root)
        assert generated.returncode == 0, generated.stdout + generated.stderr
        stage_c = root / f"freakc_stage{generation}.c"
        shutil.copyfile(emitted, stage_c)
        stage = root / f"freakc_stage{generation}{executable_suffix}"
        compiled = run(
            [
                clang,
                "-o",
                str(stage),
                str(stage_c),
                str(runtime_root / "freak_runtime.c"),
                *common,
            ],
            root,
        )
        assert compiled.returncode == 0, compiled.stdout + compiled.stderr
        previous = stage
        stage2 = stage
    assert stage2 is not None

    cli_aggregate = root / "freakc_cli.fk"
    cli_aggregate.write_bytes(
        b"".join((repo / path).read_bytes() for path in CLI_SOURCES)
    )
    generated_cli = run([str(stage2), str(cli_aggregate), "--c"], root)
    assert generated_cli.returncode == 0, generated_cli.stdout + generated_cli.stderr
    cli = root / f"freak{executable_suffix}"
    linked_cli = run(
        [
            clang,
            "-o",
            str(cli),
            str(Path(str(cli_aggregate) + ".c")),
            str(runtime_root / "freak_runtime.c"),
            *common,
        ],
        root,
    )
    assert linked_cli.returncode == 0, linked_cli.stdout + linked_cli.stderr
    return cli


def transpile(
    *, freak: Path, repo: Path, source: Path, backend: str
) -> tuple[Path, str]:
    flag = "--c" if backend == "c" else "--llvm"
    suffix = ".c" if backend == "c" else ".ll"
    result = run([str(freak), "transpile", str(source), flag], repo)
    assert result.returncode == 0, result.stdout + result.stderr
    generated = Path(str(source) + suffix)
    assert generated.is_file(), generated
    return generated, generated.read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "freak",
        nargs="?",
        type=Path,
        help="existing exact-source CLI (omit to reconstruct one outside the repo)",
    )
    parser.add_argument(
        "--runtime-root",
        type=Path,
        help="runtime payload to compile (defaults to the repository runtime)",
    )
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    runtime_root = (
        args.runtime_root.resolve()
        if args.runtime_root is not None
        else (repo / "freakc" / "runtime").resolve()
    )
    assert (runtime_root / "freak_runtime.c").is_file(), runtime_root
    assert (runtime_root / "freak_llvm_runtime.c").is_file(), runtime_root
    clang = os.environ.get("FREAK_CLANG") or shutil.which("clang")
    assert clang, "clang is required for the word foundation regression"
    executable_suffix = ".exe" if sys.platform == "win32" else ""

    with tempfile.TemporaryDirectory(prefix="freak-v3-word-foundation-") as tmp:
        root = Path(tmp)
        freak = (
            args.freak.resolve()
            if args.freak is not None
            else build_fresh_cli(
                clang=clang, repo=repo, root=root, runtime_root=runtime_root
            )
        )
        assert freak.is_file(), freak
        for backend in ("c", "llvm"):
            source = root / f"foundation_{backend}.fk"
            source.write_text(FOUNDATION_PROGRAM, encoding="utf-8")
            generated, generated_text = transpile(
                freak=freak, repo=repo, source=source, backend=backend
            )
            repeat_marker = (
                "freak_word_repeated(" if backend == "c" else "@freak_llvm_word_repeated"
            )
            builder_prefix = (
                "freak_word_builder_" if backend == "c" else "@freak_llvm_word_builder_"
            )
            assert repeat_marker in generated_text, generated_text
            for operation in (
                "new",
                "with_capacity",
                "reserve",
                "capacity",
                "length",
                "clear",
                "append",
                "append_char",
                "append_int",
                "finish",
                "discard",
            ):
                assert builder_prefix + operation in generated_text, (
                    backend,
                    operation,
                )
            assert "word +=" not in generated_text

            binary = root / f"foundation_{backend}{executable_suffix}"
            compile_generated(
                clang=clang,
                repo=repo,
                runtime_root=runtime_root,
                generated=generated,
                backend=backend,
                binary=binary,
            )
            executed = run([str(binary)], root, sanitizer_env())
            assert executed.returncode == 0, executed.stdout + executed.stderr
            assert executed.stdout.strip().splitlines() == EXPECTED_STDOUT, (
                backend,
                executed.stdout,
            )
            audit_match = AUDIT_RE.search(executed.stderr)
            assert audit_match, executed.stderr
            stats = tuple(int(value) for value in audit_match.groups())
            assert stats == (6, 3, 16, 4, 4, 3, 48, 3, 1), (backend, stats)
            assert "ownership audit found" not in executed.stderr
            assert "AddressSanitizer" not in executed.stderr
            print(
                f"{backend}: repeat_calls={stats[0]} repeat_allocations={stats[1]} "
                f"repeat_copied_bytes={stats[2]} builder_allocations={stats[4]} "
                f"builder_growths={stats[5]} builder_copied_bytes={stats[6]}"
            )

            for name, program, diagnostic in (
                (
                    "stale_finish",
                    STALE_FINISH_PROGRAM,
                    "invalid or stale word builder handle in capacity",
                ),
                (
                    "stale_discard",
                    STALE_DISCARD_PROGRAM,
                    "invalid or stale word builder handle in append",
                ),
            ):
                failure_source = root / f"{name}_{backend}.fk"
                failure_source.write_text(program, encoding="utf-8")
                failure_generated, _ = transpile(
                    freak=freak, repo=repo, source=failure_source, backend=backend
                )
                failure_binary = root / f"{name}_{backend}{executable_suffix}"
                compile_generated(
                    clang=clang,
                    repo=repo,
                    runtime_root=runtime_root,
                    generated=failure_generated,
                    backend=backend,
                    binary=failure_binary,
                )
                failed = run(
                    [str(failure_binary)],
                    root,
                    sanitizer_env(detect_leaks=False),
                )
                assert failed.returncode != 0, (backend, name)
                assert diagnostic in failed.stderr, failed.stderr

            leak_source = root / f"leak_{backend}.fk"
            leak_source.write_text(LEAK_PROGRAM, encoding="utf-8")
            leak_generated, _ = transpile(
                freak=freak, repo=repo, source=leak_source, backend=backend
            )
            leak_binary = root / f"leak_{backend}{executable_suffix}"
            compile_generated(
                clang=clang,
                repo=repo,
                runtime_root=runtime_root,
                generated=leak_generated,
                backend=backend,
                binary=leak_binary,
            )
            leaked = run(
                [str(leak_binary)], root, sanitizer_env(detect_leaks=False)
            )
            assert leaked.returncode != 0, backend
            assert "word builder ownership audit found 1 live builder(s)" in leaked.stderr

            stdlib_source = root / f"string_repeat_{backend}.fk"
            stdlib_source.write_bytes(
                (repo / "std/string.fk").read_bytes()
                + b"\n"
                + STDLIB_PROGRAM.encode("utf-8")
            )
            stdlib_generated, stdlib_text = transpile(
                freak=freak, repo=repo, source=stdlib_source, backend=backend
            )
            assert repeat_marker in stdlib_text, stdlib_text
            stdlib_binary = root / f"string_repeat_{backend}{executable_suffix}"
            compile_generated(
                clang=clang,
                repo=repo,
                runtime_root=runtime_root,
                generated=stdlib_generated,
                backend=backend,
                binary=stdlib_binary,
            )
            stdlib_run = run([str(stdlib_binary)], root, sanitizer_env())
            assert stdlib_run.returncode == 0, (
                stdlib_run.stdout + stdlib_run.stderr
            )
            assert stdlib_run.stdout.strip().splitlines() == ["gogogo", "0", "4"]
            assert "ownership audit found" not in stdlib_run.stderr

        negative = root / "word_foundation_negative.fk"
        negative.write_text(NEGATIVE_PROGRAM, encoding="utf-8")
        checked = run([str(freak), "check", str(negative)], repo)
        negative_output = checked.stdout + checked.stderr
        assert checked.returncode != 0, negative_output
        assert "conflicts with a compiler builtin namespace" in negative_output
        assert "assignment operator '+=' does not accept word and word" in negative_output
        assert "method 'repeated' argument 1 expects int, got word" in negative_output
        assert "call to 'word_builder::append' argument 2 expects word, got int" in negative_output
        assert not Path(str(negative) + ".c").exists()
        assert not Path(str(negative) + ".ll").exists()

        bootstrap_source = root / "bootstrap_string_repeat.fk"
        bootstrap_source.write_text(
            "task string_repeat(s: word, count: int) -> word {\n"
            "    give back s.repeated(count)\n"
            "}\n"
            "task main() { say string_repeat(\"yo\", 2) }\n",
            encoding="utf-8",
        )
        bootstrap_binary = root / f"bootstrap_string_repeat{executable_suffix}"
        bootstrap_build = run(
            [
                sys.executable,
                "-m",
                "freakc",
                "build",
                str(bootstrap_source),
                "-o",
                str(bootstrap_binary),
            ],
            repo,
        )
        assert bootstrap_build.returncode == 0, (
            bootstrap_build.stdout + bootstrap_build.stderr
        )
        bootstrap_run = run([str(bootstrap_binary)], root)
        assert bootstrap_run.returncode == 0, (
            bootstrap_run.stdout + bootstrap_run.stderr
        )
        assert bootstrap_run.stdout.strip() == "yoyo", bootstrap_run.stdout

        runtime_probe = root / "word_foundation_runtime_probe.c"
        runtime_probe.write_text(RUNTIME_PROBE, encoding="utf-8")
        runtime_binary = root / f"word_foundation_runtime_probe{executable_suffix}"
        runtime_command = [
            clang,
            "-O1",
            "-o",
            str(runtime_binary),
            str(runtime_probe),
            str(runtime_root / "freak_runtime.c"),
            "-I",
            str(runtime_root),
        ]
        if sys.platform == "win32":
            runtime_command.append("-lws2_32")
        else:
            runtime_command.append("-lm")
        runtime_compiled = run(runtime_command, repo)
        assert runtime_compiled.returncode == 0, (
            runtime_compiled.stdout + runtime_compiled.stderr
        )
        correctness = run([str(runtime_binary)], root)
        assert correctness.returncode == 0, correctness.stdout + correctness.stderr
        for mode, diagnostic in (
            ("repeat-c-overflow", "word repetition size overflow"),
            ("repeat-llvm-overflow", "word repetition size overflow"),
            ("builder-overflow", "word builder size overflow"),
            ("negative-capacity", "word builder capacity must be non-negative"),
            ("stale-c", "invalid or stale word builder handle in length"),
            ("stale-llvm", "invalid or stale word builder handle in length"),
        ):
            failed = run([str(runtime_binary), mode], root)
            assert failed.returncode != 0, mode
            assert diagnostic in failed.stderr, (mode, failed.stderr)
        for scalar in ("-1", "0", "55296", "1114112"):
            failed = run([str(runtime_binary), "bad-char", scalar], root)
            assert failed.returncode != 0, scalar
            assert (
                "word builder append_char requires a non-NUL Unicode scalar"
                in failed.stderr
            ), (scalar, failed.stderr)

    print("V3 word repetition and builder foundation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
