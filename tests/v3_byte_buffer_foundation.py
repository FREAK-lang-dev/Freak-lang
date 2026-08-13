#!/usr/bin/env python3
"""Prove the V3 opaque ByteBuffer foundation on native and bootstrap paths."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import v3_word_foundation as foundation


NATIVE_PROGRAM = """task main() {
    pilot buffer: ByteBuffer = ByteBuffer::with_capacity(2)
    say buffer.capacity()
    buffer.reserve(32)
    say buffer.capacity()
    buffer.write_byte(65)
    buffer.write_int(0 - 42)
    buffer.write_int_be(0 - 77)
    buffer.write_word("é")
    say buffer.length()
    buffer.seek(0)
    say buffer.read_byte()
    say buffer.read_int()
    say buffer.read_int_be()
    say buffer.read_word(2)
    say buffer.position()
    say buffer.remaining()
    say buffer.read_byte()
    say buffer.status()
    buffer.seek(0)
    say buffer.position()
    buffer.clear_status()
    buffer.seek(0)
    pilot part: ByteBuffer = buffer.slice(0, 1)
    buffer.clear()
    say part.to_word()
    part.release()
    buffer.write_word("abc")
    buffer.truncate(2)
    say buffer.length()
    buffer.release()

    pilot text = ByteBuffer::new()
    text.write_word("x" + "y")
    say text.to_word()
    text.release()

    pilot invalid = ByteBuffer::new()
    invalid.write_byte(256)
    say invalid.status()
    invalid.clear_status()
    say invalid.status()
    invalid.release()

    pilot bad_capacity = ByteBuffer::with_capacity(0 - 1)
    say bad_capacity.status()
    bad_capacity.release()
}
"""

EXPECTED_NATIVE_STDOUT = [
    "2",
    "32",
    "19",
    "65",
    "-42",
    "-77",
    "é",
    "19",
    "0",
    "0",
    "1",
    "19",
    "A",
    "2",
    "xy",
    "2",
    "0",
    "2",
]

BOOTSTRAP_PROGRAM = """task main() {
    pilot buffer: ByteBuffer = ByteBuffer::with_capacity(3)
    say buffer.capacity()
    buffer.write_byte(65)
    buffer.write_int(9)
    buffer.write_int_be(10)
    say buffer.length()
    buffer.seek(0)
    say buffer.read_byte()
    say buffer.read_int()
    say buffer.read_int_be()
    pilot part: ByteBuffer = buffer.slice(0, 1)
    say part.length()
    part.release()
    buffer.release()
}
"""

NEGATIVE_PROGRAM = """task main() {
    pilot b: ByteBuffer = ByteBuffer::new(1)
    b.write_word(1)
    b.slice(0)
    b.nope()
    ByteBuffer::from("old")
}
"""

RESERVED_SHAPE_PROGRAM = """shape ByteBuffer {}

task main() {}
"""

STALE_PROGRAM = """task main() {
    pilot buffer: ByteBuffer = ByteBuffer::new()
    pilot alias: ByteBuffer = buffer
    buffer.release()
    say alias.status()
}
"""

DOUBLE_RELEASE_PROGRAM = """task main() {
    pilot buffer: ByteBuffer = ByteBuffer::new()
    buffer.release()
    buffer.release()
}
"""

STRICT_BORROW_OK_PROGRAM = """task main() {
    pilot buffer: ByteBuffer = ByteBuffer::new()
    buffer.write_byte(65)
    say buffer.length()
    buffer.seek(0)
    say buffer.read_byte()
    say buffer.status()
    buffer.release()
}
"""

STRICT_USE_AFTER_RELEASE_PROGRAM = """task main() {
    pilot buffer = ByteBuffer::new()
    buffer.release()
    say buffer.status()
}
"""

STRICT_DOUBLE_RELEASE_PROGRAM = """task main() {
    pilot buffer: ByteBuffer = ByteBuffer::new()
    buffer.release()
    buffer.release()
}
"""

STRICT_ALIAS_AFTER_RELEASE_PROGRAM = """task main() {
    pilot buffer = ByteBuffer::new()
    pilot alias = buffer
    alias.release()
    say alias.length()
}
"""

BYTES_FIXTURE_STDOUT = ["5", "Hello", "0", "1", "5", "ell", "bytes module OK"]

RUNTIME_PROBE = r'''#include "freak_runtime.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void expect(int condition, const char* message) {
    if (!condition) {
        fprintf(stderr, "probe failure: %s\n", message);
        exit(2);
    }
}

static void expect_invalid_utf8(const uint8_t* bytes, size_t length) {
    freak_byte_buffer_handle buffer = freak_byte_buffer_new();
    for (size_t i = 0; i < length; i += 1) {
        freak_byte_buffer_write_byte(buffer, bytes[i]);
    }
    freak_word word = freak_byte_buffer_to_word(buffer);
    expect(word.length == 0 && !word.heap, "invalid UTF-8 returns empty literal");
    expect(freak_byte_buffer_status(buffer) == 3, "invalid UTF-8 status");
    freak_byte_buffer_release(buffer);

    buffer = freak_byte_buffer_new();
    for (size_t i = 0; i < length; i += 1) {
        freak_byte_buffer_write_byte(buffer, bytes[i]);
    }
    word = freak_byte_buffer_read_word(buffer, (int64_t)length);
    expect(word.length == 0 && !word.heap, "invalid UTF-8 read returns empty literal");
    expect(freak_byte_buffer_status(buffer) == 3, "invalid UTF-8 read status");
    expect(freak_byte_buffer_position(buffer) == 0, "invalid UTF-8 read keeps cursor");
    freak_byte_buffer_release(buffer);
}

static void check_table_growth_slice(void) {
    freak_byte_buffer_handle handles[64];
    handles[0] = freak_byte_buffer_new();
    freak_byte_buffer_write_word(handles[0], freak_word_lit("abc"));
    for (size_t i = 1; i < 64; i += 1) {
        handles[i] = freak_byte_buffer_new();
    }
    /* All 64 table slots are now live. slice() must grow/move the table and
       then re-resolve its source record before copying. */
    freak_byte_buffer_handle slice = freak_byte_buffer_slice(handles[0], 1, 2);
    freak_word word = freak_byte_buffer_to_word(slice);
    expect(word.length == 2 && memcmp(word.data, "bc", 2) == 0, "slice across table realloc");
    freak_word_release_owned(&word);
    freak_byte_buffer_release(slice);
    for (size_t i = 0; i < 64; i += 1) {
        freak_byte_buffer_release(handles[i]);
    }
}

static int normal(void) {
    freak_byte_buffer_handle buffer = freak_byte_buffer_with_capacity(2);
    expect(buffer < 0, "ByteBuffer handle uses negative domain");
    expect(freak_byte_buffer_capacity(buffer) == 2, "initial capacity");
    freak_byte_buffer_reserve(buffer, 64);
    expect(freak_byte_buffer_capacity(buffer) == 64, "reserve");
    freak_byte_buffer_write_byte(buffer, 0xab);
    freak_byte_buffer_write_int(buffer, INT64_C(-72623859790382856));
    freak_byte_buffer_write_int_be(buffer, INT64_C(-123456789));
    freak_byte_buffer_write_word(buffer, freak_word_lit("ok"));
    expect(freak_byte_buffer_length(buffer) == 19, "write length");
    freak_byte_buffer_seek(buffer, 0);
    expect(freak_byte_buffer_read_byte(buffer) == 0xab, "read byte");
    expect(freak_byte_buffer_read_int(buffer) == INT64_C(-72623859790382856), "LE int");
    expect(freak_byte_buffer_read_int_be(buffer) == INT64_C(-123456789), "BE int");
    freak_word read = freak_byte_buffer_read_word(buffer, 2);
    expect(read.length == 2 && memcmp(read.data, "ok", 2) == 0, "read word");
    freak_word_release_owned(&read);
    expect(freak_byte_buffer_remaining(buffer) == 0, "remaining");
    expect(freak_byte_buffer_read_byte(buffer) == 0, "OOB neutral byte");
    expect(freak_byte_buffer_status(buffer) == 1, "OOB status");
    freak_byte_buffer_seek(buffer, 0);
    expect(freak_byte_buffer_position(buffer) == 19, "sticky blocks seek");
    freak_byte_buffer_clear_status(buffer);
    freak_byte_buffer_seek(buffer, 0);
    expect(freak_byte_buffer_position(buffer) == 0, "status recovery");
    freak_byte_buffer_handle slice = freak_byte_buffer_slice(buffer, 0, 1);
    expect(slice < 0 && slice != buffer, "slice receives independent handle");
    freak_byte_buffer_clear(buffer);
    expect(freak_byte_buffer_length(buffer) == 0, "clear length");
    expect(freak_byte_buffer_read_byte(slice) == 0xab, "slice copied bytes");
    freak_byte_buffer_release(slice);
    freak_byte_buffer_release(buffer);

    freak_byte_buffer_handle bad = freak_byte_buffer_with_capacity(-1);
    expect(freak_byte_buffer_status(bad) == 2, "negative capacity status");
    expect(freak_byte_buffer_capacity(bad) == 0, "state visible while sticky");
    freak_byte_buffer_clear_status(bad);
    freak_byte_buffer_write_byte(bad, 256);
    expect(freak_byte_buffer_status(bad) == 2, "byte range status");
    freak_byte_buffer_clear_status(bad);
    freak_byte_buffer_truncate(bad, 1);
    expect(freak_byte_buffer_status(bad) == 1, "truncate bounds status");
    freak_byte_buffer_release(bad);

    static const uint8_t nul[] = {0};
    static const uint8_t continuation[] = {0x80};
    static const uint8_t overlong2[] = {0xc0, 0x80};
    static const uint8_t overlong3[] = {0xe0, 0x80, 0x80};
    static const uint8_t surrogate[] = {0xed, 0xa0, 0x80};
    static const uint8_t overlong4[] = {0xf0, 0x80, 0x80, 0x80};
    static const uint8_t too_large[] = {0xf4, 0x90, 0x80, 0x80};
    static const uint8_t bad_lead[] = {0xf5, 0x80, 0x80, 0x80};
    static const uint8_t truncated[] = {0xe2, 0x82};
    expect_invalid_utf8(nul, sizeof(nul));
    expect_invalid_utf8(continuation, sizeof(continuation));
    expect_invalid_utf8(overlong2, sizeof(overlong2));
    expect_invalid_utf8(overlong3, sizeof(overlong3));
    expect_invalid_utf8(surrogate, sizeof(surrogate));
    expect_invalid_utf8(overlong4, sizeof(overlong4));
    expect_invalid_utf8(too_large, sizeof(too_large));
    expect_invalid_utf8(bad_lead, sizeof(bad_lead));
    expect_invalid_utf8(truncated, sizeof(truncated));

    static const uint8_t emoji[] = {0xf0, 0x9f, 0x99, 0x82};
    freak_byte_buffer_handle valid = freak_byte_buffer_new();
    for (size_t i = 0; i < sizeof(emoji); i += 1) {
        freak_byte_buffer_write_byte(valid, emoji[i]);
    }
    freak_word valid_word = freak_byte_buffer_to_word(valid);
    expect(valid_word.length == 4 && valid_word.heap, "valid UTF-8 copied word");
    freak_word_release_owned(&valid_word);
    freak_byte_buffer_release(valid);

    check_table_growth_slice();

    puts("runtime-ok");
    return 0;
}

int main(int argc, char** argv) {
    if (argc == 1) return normal();
    if (strcmp(argv[1], "forged") == 0) return (int)freak_byte_buffer_status(0);
    if (strcmp(argv[1], "forged_negative") == 0) {
        return (int)freak_byte_buffer_status(INT64_MIN);
    }
    if (strcmp(argv[1], "stale") == 0) {
        int64_t buffer = freak_byte_buffer_new();
        freak_byte_buffer_release(buffer);
        return (int)freak_byte_buffer_status(buffer);
    }
    if (strcmp(argv[1], "double") == 0) {
        int64_t buffer = freak_byte_buffer_new();
        freak_byte_buffer_release(buffer);
        freak_byte_buffer_release(buffer);
        return 0;
    }
    if (strcmp(argv[1], "builder") == 0) {
        return (int)freak_byte_buffer_status(freak_word_builder_new());
    }
    if (strcmp(argv[1], "array") == 0) {
        return (int)freak_byte_buffer_status(freak_array_new());
    }
    if (strcmp(argv[1], "buffer_as_builder") == 0) {
        return (int)freak_word_builder_capacity(freak_byte_buffer_new());
    }
    if (strcmp(argv[1], "buffer_as_array") == 0) {
        int64_t buffer = freak_byte_buffer_new();
        int64_t result = freak_array_len(buffer);
        freak_byte_buffer_release(buffer);
        expect(result == 0, "array rejects ByteBuffer domain");
        return 0;
    }
    return 3;
}
'''


def run(
    command: list[str],
    cwd: Path,
    *,
    env: dict[str, str] | None = None,
    timeout: int = 240,
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


def compile_generated(
    compiler: str,
    repo: Path,
    runtime: Path,
    generated: Path,
    binary: Path,
    backend: str,
) -> None:
    command = [
        compiler,
        "-O1",
        "-DFREAK_WORD_FOUNDATION_AUDIT=1",
        "-o",
        str(binary),
        str(generated),
    ]
    if backend == "llvm":
        command.extend(
            ["-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1", str(runtime / "freak_llvm_runtime.c")]
        )
    else:
        command.append("-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1")
    command.extend([str(runtime / "freak_runtime.c"), "-I", str(runtime)])
    if sys.platform == "win32":
        command.append("-lws2_32")
    else:
        command.extend(["-lm", "-fsanitize=address", "-fno-omit-frame-pointer"])
    result = run(command, repo)
    assert result.returncode == 0, result.stdout + result.stderr


def assert_stats(
    stderr: str,
    *,
    creations: int,
    minimum_allocations: int,
    minimum_growths: int,
    minimum_copied_bytes: int,
) -> None:
    stats = foundation.parse_runtime_stats(stderr)
    counters = stats["counters"]
    byte_names = {
        "byte_buffer_creations",
        "byte_buffer_allocations",
        "byte_buffer_growths",
        "byte_buffer_copied_bytes",
        "byte_buffer_releases",
    }
    assert byte_names <= set(counters), counters
    assert counters["byte_buffer_creations"] == creations, counters
    assert counters["byte_buffer_releases"] == creations, counters
    assert counters["byte_buffer_allocations"] >= minimum_allocations, counters
    assert counters["byte_buffer_growths"] >= minimum_growths, counters
    assert counters["byte_buffer_copied_bytes"] >= minimum_copied_bytes, counters
    assert counters["byte_buffer_allocations"] >= counters["byte_buffer_growths"], counters


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    runtime = repo / "freakc" / "runtime"
    compiler = (
        os.environ.get("FREAK_CLANG")
        or (shutil.which("gcc") if sys.platform == "win32" else None)
        or shutil.which("clang")
        or shutil.which("cc")
    )
    assert compiler, "a C/LLVM compiler is required"
    suffix = ".exe" if sys.platform == "win32" else ""

    with tempfile.TemporaryDirectory(prefix="freak-v3-byte-buffer-") as temporary:
        root = Path(temporary)
        freak = foundation.build_fresh_cli(
            clang=compiler, repo=repo, root=root, runtime_root=runtime
        )

        for backend in ("c", "llvm"):
            source = root / f"byte_buffer_{backend}.fk"
            source.write_text(NATIVE_PROGRAM, encoding="utf-8")
            generated, generated_text = foundation.transpile(
                freak=freak, repo=repo, source=source, backend=backend
            )
            prefix = (
                "freak_byte_buffer_" if backend == "c" else "@freak_llvm_byte_buffer_"
            )
            for operation in (
                "new",
                "with_capacity",
                "release",
                "status",
                "clear_status",
                "reserve",
                "capacity",
                "length",
                "position",
                "remaining",
                "clear",
                "truncate",
                "seek",
                "write_byte",
                "write_int",
                "write_int_be",
                "write_word",
                "read_byte",
                "read_int",
                "read_int_be",
                "read_word",
                "slice",
                "to_word",
            ):
                assert prefix + operation in generated_text, (backend, operation)
            binary = root / f"byte_buffer_{backend}{suffix}"
            compile_generated(compiler, repo, runtime, generated, binary, backend)
            executed = run([str(binary)], root)
            assert executed.returncode == 0, executed.stdout + executed.stderr
            assert executed.stdout.strip().splitlines() == EXPECTED_NATIVE_STDOUT, (
                backend,
                executed.stdout,
            )
            assert "ownership audit found" not in executed.stderr, executed.stderr
            assert_stats(
                executed.stderr,
                creations=5,
                minimum_allocations=4,
                minimum_growths=2,
                minimum_copied_bytes=25,
            )

            fixture_source = root / f"bytes_fixture_{backend}.fk"
            shutil.copyfile(repo / "tests" / "bytes.fk", fixture_source)
            fixture_generated, _ = foundation.transpile(
                freak=freak, repo=repo, source=fixture_source, backend=backend
            )
            fixture_binary = root / f"bytes_fixture_{backend}{suffix}"
            compile_generated(
                compiler,
                repo,
                runtime,
                fixture_generated,
                fixture_binary,
                backend,
            )
            fixture_run = run([str(fixture_binary)], root)
            assert fixture_run.returncode == 0, fixture_run.stdout + fixture_run.stderr
            assert fixture_run.stdout.strip().splitlines() == BYTES_FIXTURE_STDOUT, (
                backend,
                fixture_run.stdout,
            )
            assert_stats(
                fixture_run.stderr,
                creations=2,
                minimum_allocations=3,
                minimum_growths=1,
                minimum_copied_bytes=8,
            )

            for name, program in (
                ("stale", STALE_PROGRAM),
                ("double", DOUBLE_RELEASE_PROGRAM),
            ):
                failure_source = root / f"{name}_{backend}.fk"
                failure_source.write_text(program, encoding="utf-8")
                failure_generated, _ = foundation.transpile(
                    freak=freak, repo=repo, source=failure_source, backend=backend
                )
                failure_binary = root / f"{name}_{backend}{suffix}"
                compile_generated(
                    compiler,
                    repo,
                    runtime,
                    failure_generated,
                    failure_binary,
                    backend,
                )
                failed = run([str(failure_binary)], root)
                assert failed.returncode != 0, (backend, name)
                assert "invalid or stale ByteBuffer handle" in failed.stderr, failed.stderr

        negative = root / "byte_buffer_negative.fk"
        negative.write_text(NEGATIVE_PROGRAM, encoding="utf-8")
        rejected = run([str(freak), "check", str(negative)], repo)
        output = rejected.stdout + rejected.stderr
        assert rejected.returncode != 0, output
        for diagnostic in (
            "call to 'ByteBuffer::new' expects 0 argument(s), got 1",
            "method 'write_word' argument 1 expects word, got int",
            "method 'slice' expects 2 argument(s), got 1",
            "has no method 'nope'",
            "unknown callable 'ByteBuffer::from'",
        ):
            assert diagnostic in output, (diagnostic, output)
        assert not Path(str(negative) + ".c").exists()
        assert not Path(str(negative) + ".ll").exists()

        reserved_shape = root / "byte_buffer_reserved_shape.fk"
        reserved_shape.write_text(RESERVED_SHAPE_PROGRAM, encoding="utf-8")
        reserved = run([str(freak), "check", str(reserved_shape)], repo)
        reserved_output = reserved.stdout + reserved.stderr
        assert reserved.returncode != 0, reserved_output
        assert "conflicts with a compiler builtin namespace" in reserved_output

        strict_ok = root / "byte_buffer_strict_ok.fk"
        strict_ok.write_text(STRICT_BORROW_OK_PROGRAM, encoding="utf-8")
        strict_checked = run(
            [str(freak), "check", str(strict_ok), "--strict-borrow"], repo
        )
        assert strict_checked.returncode == 0, strict_checked.stdout + strict_checked.stderr

        for name, program, binding in (
            ("use_after_release", STRICT_USE_AFTER_RELEASE_PROGRAM, "buffer"),
            ("double_release", STRICT_DOUBLE_RELEASE_PROGRAM, "buffer"),
            ("alias_after_release", STRICT_ALIAS_AFTER_RELEASE_PROGRAM, "alias"),
        ):
            strict_failure = root / f"byte_buffer_strict_{name}.fk"
            strict_failure.write_text(program, encoding="utf-8")
            strict_rejected = run(
                [str(freak), "check", str(strict_failure), "--strict-borrow"], repo
            )
            strict_output = strict_rejected.stdout + strict_rejected.stderr
            assert strict_rejected.returncode != 0, (name, strict_output)
            assert "You gave this away" in strict_output, (name, strict_output)
            assert f"'{binding}'" in strict_output, (name, strict_output)
            assert not Path(str(strict_failure) + ".c").exists()
            assert not Path(str(strict_failure) + ".ll").exists()

        bootstrap = root / "bootstrap_byte_buffer.fk"
        bootstrap.write_text(BOOTSTRAP_PROGRAM, encoding="utf-8")
        bootstrap_binary = root / f"bootstrap_byte_buffer{suffix}"
        built = run(
            [
                sys.executable,
                "-m",
                "freakc",
                "build",
                str(bootstrap),
                "-o",
                str(bootstrap_binary),
            ],
            repo,
        )
        assert built.returncode == 0, built.stdout + built.stderr
        bootstrap_run = run([str(bootstrap_binary)], root)
        assert bootstrap_run.returncode == 0, bootstrap_run.stdout + bootstrap_run.stderr
        assert bootstrap_run.stdout.strip().splitlines() == ["3", "17", "65", "9", "10", "1"]

        bootstrap_stale = root / "bootstrap_byte_buffer_stale.fk"
        bootstrap_stale.write_text(STALE_PROGRAM, encoding="utf-8")
        bootstrap_stale_binary = root / f"bootstrap_byte_buffer_stale{suffix}"
        stale_build = run(
            [
                sys.executable,
                "-m",
                "freakc",
                "build",
                str(bootstrap_stale),
                "-o",
                str(bootstrap_stale_binary),
            ],
            repo,
        )
        assert stale_build.returncode == 0, stale_build.stdout + stale_build.stderr
        stale_run = run([str(bootstrap_stale_binary)], root)
        assert stale_run.returncode != 0, stale_run.stdout + stale_run.stderr
        assert "invalid or stale ByteBuffer handle" in stale_run.stderr, stale_run.stderr

        bootstrap_rejections = (
            (
                "read_word",
                "pilot b: ByteBuffer = ByteBuffer::new()\nsay b.read_word(0)",
                "Python bootstrap does not support owned ByteBuffer word results",
            ),
            (
                "to_word",
                "pilot b: ByteBuffer = ByteBuffer::new()\nsay b.to_word()",
                "Python bootstrap does not support owned ByteBuffer word results",
            ),
            (
                "legacy_from",
                'ByteBuffer::from("old")',
                "unknown ByteBuffer builtin 'ByteBuffer::from'",
            ),
            (
                "shape",
                "shape ByteBuffer {}",
                "conflicts with a compiler builtin namespace",
            ),
        )
        for name, body, diagnostic in bootstrap_rejections:
            source = root / f"bootstrap_reject_{name}.fk"
            if body.startswith("shape"):
                program = body + "\ntask main() {}\n"
            else:
                program = "task main() {\n" + body + "\n}\n"
            source.write_text(program, encoding="utf-8")
            output_c = source.with_suffix(".c")
            output_binary = root / f"bootstrap_reject_{name}{suffix}"
            for action in ("check", "build", "run"):
                output_c.unlink(missing_ok=True)
                output_binary.unlink(missing_ok=True)
                command = [sys.executable, "-m", "freakc", action, str(source)]
                if action in ("build", "run"):
                    command.extend(["-o", str(output_binary)])
                result = run(command, repo)
                output = result.stdout + result.stderr
                assert result.returncode != 0, (name, action, output)
                assert diagnostic in output, (name, action, diagnostic, output)
                assert not output_c.exists(), (name, action, output_c)
                assert not output_binary.exists(), (name, action, output_binary)

        runtime_probe = root / "byte_buffer_runtime_probe.c"
        runtime_probe.write_text(RUNTIME_PROBE, encoding="utf-8")
        runtime_binary = root / f"byte_buffer_runtime_probe{suffix}"
        command = [
            compiler,
            "-O1",
            "-DFREAK_WORD_FOUNDATION_AUDIT=1",
            "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1",
            "-DFREAK_BYTE_BUFFER_FORCE_TABLE_MOVE=1",
            "-o",
            str(runtime_binary),
            str(runtime_probe),
            str(runtime / "freak_runtime.c"),
            "-I",
            str(runtime),
        ]
        if sys.platform == "win32":
            command.append("-lws2_32")
        else:
            command.extend(["-lm", "-fsanitize=address", "-fno-omit-frame-pointer"])
        compiled = run(command, repo)
        assert compiled.returncode == 0, compiled.stdout + compiled.stderr
        executed = run([str(runtime_binary)], root)
        assert executed.returncode == 0, executed.stdout + executed.stderr
        assert executed.stdout.strip() == "runtime-ok", executed.stdout
        assert_stats(
            executed.stderr,
            creations=87,
            minimum_allocations=24,
            minimum_growths=21,
            minimum_copied_bytes=77,
        )

        for case in (
            "forged",
            "forged_negative",
            "stale",
            "double",
            "builder",
            "array",
            "buffer_as_builder",
        ):
            failed = run([str(runtime_binary), case], root)
            assert failed.returncode != 0, case
            assert "invalid or stale" in failed.stderr, (case, failed.stderr)
        cross_domain = run([str(runtime_binary), "buffer_as_array"], root)
        assert cross_domain.returncode == 0, cross_domain.stdout + cross_domain.stderr

    print("v3 ByteBuffer foundation: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
