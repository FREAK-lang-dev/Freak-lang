#!/usr/bin/env python3
"""Prove the frozen V3 scalar system-runtime foundation."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import v3_word_foundation as foundation


CAPTURE_NAME = "FREAK_V3_SYSTEM_CAPTURE"
EMPTY_NAME = "FREAK_V3_SYSTEM_EMPTY"
MISSING_NAME = "FREAK_V3_SYSTEM_DEFINITELY_MISSING"
INITIAL_VALUE = "original-λ"
UPDATED_VALUE = "changed-雪 ;&|$() ' quote"

NATIVE_PROGRAM = f'''task main() {{
    pilot captured: word = process::env("{CAPTURE_NAME}")
    say captured
    process::set_env("{CAPTURE_NAME}", "{UPDATED_VALUE}")
    say captured
    say process::env("{CAPTURE_NAME}")
    process::set_env("{EMPTY_NAME}", "")
    say process::env("{EMPTY_NAME}").length()
    say process::env("{MISSING_NAME}").length()
    say process::pid()
    say time::now_ms()
    pilot first = time::monotonic_ns()
    pilot second = time::monotonic_ns()
    say first
    say second
}}
'''

BOOTSTRAP_PROGRAM = f'''task main() {{
    process::set_env("{CAPTURE_NAME}", "{UPDATED_VALUE}")
    say process::pid()
    say time::now_ms()
    pilot first = time::monotonic_ns()
    pilot second = time::monotonic_ns()
    say first
    say second
}}
'''

BOOTSTRAP_ENV_REJECTION = f'''task main() {{
    say process::env("{CAPTURE_NAME}")
}}
'''

BOOTSTRAP_AUDIT_PROGRAM = f'''task main() {{
    process::set_env("{CAPTURE_NAME}", "{UPDATED_VALUE}")
    pilot pid = process::pid()
    pilot wall = time::now_ms()
    pilot monotonic = time::monotonic_ns()
}}
'''

NEGATIVE_PROGRAM = '''task main() {
    say time::now_ms(1)
    say time::monotonic_ns("bad")
    say process::pid(1)
    say process::env(1)
    process::set_env("name", 1)
}
'''

NEGATIVE_DIAGNOSTICS = (
    "call to 'time::now_ms' expects 0 argument(s), got 1",
    "call to 'time::monotonic_ns' expects 0 argument(s), got 1",
    "call to 'process::pid' expects 0 argument(s), got 1",
    "call to 'process::env' argument 1 expects word, got int",
    "call to 'process::set_env' argument 2 expects word, got int",
)

RUNTIME_PROBE = r'''#include "freak_runtime.h"
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#ifdef _WIN32
#include <windows.h>
#else
#include <pthread.h>
#include <unistd.h>
#endif

static void expect(int condition, const char* message) {
    if (!condition) {
        fprintf(stderr, "probe failure: %s\n", message);
        exit(2);
    }
}

static freak_word raw_word(const char* data, size_t length) {
    freak_word value;
    value.data = data;
    value.length = length;
    value.char_count = length;
    value.heap = false;
    return value;
}

static const char* stress_name = "FREAK_V3_SYSTEM_CONCURRENT";
static atomic_int stress_failed = 0;
static atomic_int stress_ready = 0;
static atomic_int stress_go = 0;

static void stress_wait_for_start(void) {
    atomic_fetch_add(&stress_ready, 1);
    while (atomic_load(&stress_go) == 0) {
    }
}

static int stress_value_valid(freak_word value) {
    static const char* expected[] = {
        "initial", "writer-A-λ", "writer-B-雪 ;&|$()"
    };
    for (size_t i = 0; i < sizeof(expected) / sizeof(expected[0]); i += 1) {
        size_t length = strlen(expected[i]);
        if (value.length == length && memcmp(value.data, expected[i], length) == 0) {
            return 1;
        }
    }
    return 0;
}

static void stress_writer_body(void) {
    freak_word name = freak_word_lit(stress_name);
    stress_wait_for_start();
    for (int i = 0; i < 4000; i += 1) {
        freak_process_set_env(
            name,
            freak_word_lit((i & 1) ? "writer-A-λ" : "writer-B-雪 ;&|$()"));
    }
}

static void stress_reader_body(void) {
    freak_word name = freak_word_lit(stress_name);
    stress_wait_for_start();
    for (int i = 0; i < 8000; i += 1) {
        freak_word direct = freak_process_env(name);
        if (!direct.heap || !stress_value_valid(direct)) {
            atomic_store(&stress_failed, 1);
        }
        freak_word_release_owned(&direct);
        freak_maybe_word maybe = freak_process_env_var(name);
        if (!maybe.has_value || !maybe.value.heap || !stress_value_valid(maybe.value)) {
            atomic_store(&stress_failed, 1);
        }
        freak_word_release_owned(&maybe.value);
    }
}

#ifdef _WIN32
static DWORD WINAPI stress_writer(LPVOID unused) {
    (void)unused;
    stress_writer_body();
    return 0;
}

static DWORD WINAPI stress_reader(LPVOID unused) {
    (void)unused;
    stress_reader_body();
    return 0;
}
#else
static void* stress_writer(void* unused) {
    (void)unused;
    stress_writer_body();
    return NULL;
}

static void* stress_reader(void* unused) {
    (void)unused;
    stress_reader_body();
    return NULL;
}
#endif

static void run_environment_stress(void) {
    freak_process_set_env(freak_word_lit(stress_name), freak_word_lit("initial"));
#ifdef _WIN32
    HANDLE writer = CreateThread(NULL, 0, stress_writer, NULL, 0, NULL);
    HANDLE reader = CreateThread(NULL, 0, stress_reader, NULL, 0, NULL);
    expect(writer != NULL && reader != NULL, "create environment stress threads");
    while (atomic_load(&stress_ready) != 2) {
    }
    atomic_store(&stress_go, 1);
    expect(WaitForSingleObject(writer, INFINITE) == WAIT_OBJECT_0,
           "join environment writer");
    expect(WaitForSingleObject(reader, INFINITE) == WAIT_OBJECT_0,
           "join environment reader");
    CloseHandle(writer);
    CloseHandle(reader);
#else
    pthread_t writer;
    pthread_t reader;
    expect(pthread_create(&writer, NULL, stress_writer, NULL) == 0,
           "create environment writer");
    expect(pthread_create(&reader, NULL, stress_reader, NULL) == 0,
           "create environment reader");
    while (atomic_load(&stress_ready) != 2) {
    }
    atomic_store(&stress_go, 1);
    expect(pthread_join(writer, NULL) == 0, "join environment writer");
    expect(pthread_join(reader, NULL) == 0, "join environment reader");
#endif
    expect(atomic_load(&stress_failed) == 0, "serialized environment snapshots");
}

static int normal(void) {
    freak_word name = freak_word_lit("FREAK_V3_SYSTEM_π");
    freak_process_set_env(name, freak_word_lit("first-λ"));
    freak_word captured = freak_process_env(name);
    expect(captured.heap, "nonempty environment value is owned");
    expect(captured.length == strlen("first-λ"), "captured length");
    freak_process_set_env(name, freak_word_lit("second-雪 ;&|$() ' quote"));
    expect(memcmp(captured.data, "first-λ", captured.length) == 0,
           "captured value survives overwrite");
    freak_word current = freak_process_env(name);
    expect(current.heap && current.data != captured.data, "environment reads are independent");
    expect(current.length == strlen("second-雪 ;&|$() ' quote") &&
           memcmp(current.data, "second-雪 ;&|$() ' quote", current.length) == 0,
           "Unicode/metacharacter round trip");
    freak_word_release_owned(&captured);
    freak_word_release_owned(&current);

    freak_process_set_env(name, freak_word_lit("legacy-first"));
    freak_maybe_word legacy = freak_process_env_var(name);
    expect(legacy.has_value && legacy.value.heap, "legacy env_var owned snapshot");
    freak_process_set_env(name, freak_word_lit("legacy-second"));
    expect(legacy.value.length == strlen("legacy-first") &&
           memcmp(legacy.value.data, "legacy-first", legacy.value.length) == 0,
           "legacy env_var snapshot survives overwrite");
    freak_maybe_word legacy_current = freak_process_env_var(name);
    expect(legacy_current.has_value && legacy_current.value.heap &&
           legacy_current.value.data != legacy.value.data,
           "legacy env_var snapshots are independent");
    freak_word_release_owned(&legacy.value);
    freak_word_release_owned(&legacy_current.value);

    freak_process_set_env(freak_word_lit("FREAK_V3_SYSTEM_EMPTY_DIRECT"), freak_word_lit(""));
    freak_word empty = freak_process_env(freak_word_lit("FREAK_V3_SYSTEM_EMPTY_DIRECT"));
    freak_word missing = freak_process_env(freak_word_lit("FREAK_V3_SYSTEM_MISSING_DIRECT"));
    expect(empty.length == 0 && missing.length == 0, "empty and missing V3 sentinel");
    freak_maybe_word empty_maybe =
        freak_process_env_var(freak_word_lit("FREAK_V3_SYSTEM_EMPTY_DIRECT"));
    freak_maybe_word missing_maybe =
        freak_process_env_var(freak_word_lit("FREAK_V3_SYSTEM_MISSING_DIRECT"));
    expect(empty_maybe.has_value && empty_maybe.value.length == 0,
           "legacy env_var preserves present empty");
    expect(!missing_maybe.has_value && missing_maybe.value.length == 0,
           "legacy env_var preserves missing");

    run_environment_stress();

    uint64_t pid = freak_process_pid();
#ifdef _WIN32
    expect(pid == (uint64_t)GetCurrentProcessId(), "exact Windows PID");
#else
    expect(pid == (uint64_t)getpid(), "exact POSIX PID");
#endif
    int64_t epoch = freak_time_now_ms();
    int64_t host_epoch = (int64_t)time(NULL) * 1000;
    expect(epoch >= host_epoch - 2000 && epoch <= host_epoch + 2000, "Unix epoch milliseconds");
    int64_t first = freak_time_monotonic_ns();
    int64_t second = freak_time_monotonic_ns();
    expect(first >= 0 && second >= first, "monotonic nanoseconds");
    puts("runtime-ok");
    return 0;
}

int main(int argc, char** argv) {
    if (argc == 1) return normal();
    if (strcmp(argv[1], "empty-name") == 0) {
        freak_process_env(freak_word_lit(""));
    } else if (strcmp(argv[1], "equals-name") == 0) {
        freak_process_set_env(freak_word_lit("BAD=NAME"), freak_word_lit("x"));
    } else if (strcmp(argv[1], "nul-name") == 0) {
        static const char bad[] = {'A', '\0', 'B'};
        freak_process_env(raw_word(bad, sizeof(bad)));
    } else if (strcmp(argv[1], "nul-value") == 0) {
        static const char bad[] = {'A', '\0', 'B'};
        freak_process_set_env(freak_word_lit("FREAK_V3_BAD_VALUE"), raw_word(bad, sizeof(bad)));
    } else if (strcmp(argv[1], "utf8-name") == 0) {
        static const char bad[] = {(char)0xc0, (char)0x80};
        freak_process_env(raw_word(bad, sizeof(bad)));
    } else if (strcmp(argv[1], "utf8-value") == 0) {
        static const char bad[] = {(char)0xed, (char)0xa0, (char)0x80};
        freak_process_set_env(freak_word_lit("FREAK_V3_BAD_UTF8"), raw_word(bad, sizeof(bad)));
    } else if (strcmp(argv[1], "huge-name") == 0) {
        freak_process_env(raw_word("A", SIZE_MAX));
    } else if (strcmp(argv[1], "huge-value") == 0) {
        freak_process_set_env(
            freak_word_lit("FREAK_V3_HUGE_VALUE"), raw_word("A", SIZE_MAX));
    } else {
        return 3;
    }
    return 0;
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
        "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1",
        "-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1",
        "-o",
        str(binary),
        str(generated),
    ]
    if backend == "llvm":
        command.append(str(runtime / "freak_llvm_runtime.c"))
    command.extend([str(runtime / "freak_runtime.c"), "-I", str(runtime)])
    if sys.platform == "win32":
        command.append("-lws2_32")
    else:
        command.extend(["-lm", "-fsanitize=address", "-fno-omit-frame-pointer"])
    result = run(command, repo)
    assert result.returncode == 0, result.stdout + result.stderr


def assert_execution(result: subprocess.CompletedProcess[str], pid: int, start_ms: int, end_ms: int) -> None:
    assert result.returncode == 0, result.stdout + result.stderr
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 9, lines
    assert lines[:5] == [INITIAL_VALUE, INITIAL_VALUE, UPDATED_VALUE, "0", "0"], lines
    assert int(lines[5]) == pid, (pid, lines)
    epoch_ms = int(lines[6])
    assert start_ms - 2000 <= epoch_ms <= end_ms + 2000, (epoch_ms, start_ms, end_ms)
    first_ns = int(lines[7])
    second_ns = int(lines[8])
    assert first_ns >= 0 and second_ns >= first_ns, lines
    assert "ownership audit found" not in result.stderr, result.stderr


def assert_bootstrap_execution(
    result: subprocess.CompletedProcess[str], pid: int, start_ms: int, end_ms: int
) -> None:
    assert result.returncode == 0, result.stdout + result.stderr
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 4, lines
    assert int(lines[0]) == pid, (pid, lines)
    epoch_ms = int(lines[1])
    assert start_ms - 2000 <= epoch_ms <= end_ms + 2000, (
        epoch_ms,
        start_ms,
        end_ms,
    )
    first_ns = int(lines[2])
    second_ns = int(lines[3])
    assert first_ns >= 0 and second_ns >= first_ns, lines


def execute_with_pid(binary: Path, cwd: Path, env: dict[str, str]) -> tuple[subprocess.CompletedProcess[str], int, int, int]:
    start_ms = time.time_ns() // 1_000_000
    process = subprocess.Popen(
        [str(binary)],
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    stdout, stderr = process.communicate(timeout=30)
    end_ms = time.time_ns() // 1_000_000
    return (
        subprocess.CompletedProcess([str(binary)], process.returncode, stdout, stderr),
        process.pid,
        start_ms,
        end_ms,
    )


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
    test_env = os.environ.copy()
    test_env[CAPTURE_NAME] = INITIAL_VALUE
    test_env.pop(MISSING_NAME, None)

    with tempfile.TemporaryDirectory(prefix="freak-v3-system-runtime-") as temporary:
        root = Path(temporary)
        freak = foundation.build_fresh_cli(
            clang=compiler, repo=repo, root=root, runtime_root=runtime
        )
        shutil.copytree(runtime, root / "runtime")
        shutil.copytree(repo / "std", root / "std")
        cli_env = os.environ.copy()
        cli_env["FREAK_HOME"] = str(root)
        cli_env["FREAK_CLANG"] = compiler

        for backend in ("c", "llvm"):
            source = root / f"system_runtime_{backend}.fk"
            source.write_text(NATIVE_PROGRAM, encoding="utf-8")
            generated, generated_text = foundation.transpile(
                freak=freak, repo=repo, source=source, backend=backend
            )
            expected_symbols = (
                (
                    "freak_time_now_ms",
                    "freak_time_monotonic_ns",
                    "freak_process_pid",
                    "freak_process_env",
                    "freak_process_set_env",
                )
                if backend == "c"
                else (
                    "@freak_llvm_time_now_ms",
                    "@freak_llvm_time_monotonic_ns",
                    "@freak_llvm_process_pid",
                    "@freak_llvm_process_env",
                    "@freak_llvm_process_set_env",
                )
            )
            for symbol in expected_symbols:
                assert symbol in generated_text, (backend, symbol)
            binary = root / f"system_runtime_{backend}{suffix}"
            compile_generated(compiler, repo, runtime, generated, binary, backend)
            executed, pid, start_ms, end_ms = execute_with_pid(binary, root, test_env)
            assert_execution(executed, pid, start_ms, end_ms)

        negative = root / "system_runtime_negative.fk"
        negative.write_text(NEGATIVE_PROGRAM, encoding="utf-8")
        for action in ("check", "build"):
            for backend in ("--c", "--llvm"):
                output = negative.with_suffix(suffix)
                command = [str(freak), action, str(negative), backend]
                result = run(command, repo, env=cli_env)
                combined = result.stdout + result.stderr
                assert result.returncode != 0, (action, backend, combined)
                for diagnostic in NEGATIVE_DIAGNOSTICS:
                    assert diagnostic in combined, (diagnostic, combined)
                assert not output.exists(), output
                assert not Path(str(negative) + ".c").exists()
                assert not Path(str(negative) + ".ll").exists()

        bootstrap_source = root / "system_runtime_bootstrap.fk"
        bootstrap_source.write_text(BOOTSTRAP_PROGRAM, encoding="utf-8")
        bootstrap_binary = root / f"system_runtime_bootstrap{suffix}"
        bootstrap_env = test_env.copy()
        bootstrap_env["FREAK_CLANG"] = compiler
        built = run(
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
            env=bootstrap_env,
        )
        assert built.returncode == 0, built.stdout + built.stderr
        executed, pid, start_ms, end_ms = execute_with_pid(
            bootstrap_binary, root, bootstrap_env
        )
        assert_bootstrap_execution(executed, pid, start_ms, end_ms)

        audit_source = root / "system_runtime_bootstrap_audit.fk"
        audit_source.write_text(BOOTSTRAP_AUDIT_PROGRAM, encoding="utf-8")
        audit_binary = root / f"system_runtime_bootstrap_audit{suffix}"
        kept = run(
            [
                sys.executable,
                "-m",
                "freakc",
                "build",
                str(audit_source),
                "--keep-c",
                "-o",
                str(audit_binary),
            ],
            repo,
            env=bootstrap_env,
        )
        assert kept.returncode == 0, kept.stdout + kept.stderr
        audit_c = audit_source.with_suffix(".c")
        assert audit_c.exists(), audit_c
        audit_command = [
            compiler,
            "-O1",
            "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1",
            "-o",
            str(audit_binary),
            str(audit_c),
            str(runtime / "freak_runtime.c"),
            "-I",
            str(runtime),
        ]
        if sys.platform == "win32":
            audit_command.append("-lws2_32")
        else:
            audit_command.append("-lm")
        audited_compile = run(audit_command, repo)
        assert audited_compile.returncode == 0, (
            audited_compile.stdout + audited_compile.stderr
        )
        audited = run([str(audit_binary)], root, env=bootstrap_env)
        assert audited.returncode == 0, audited.stdout + audited.stderr
        assert "ownership audit found" not in audited.stderr, audited.stderr

        env_rejection = root / "bootstrap_env_rejection.fk"
        env_rejection.write_text(BOOTSTRAP_ENV_REJECTION, encoding="utf-8")
        for action in ("check", "build", "run"):
            output = root / f"bootstrap-env-rejection-{action}{suffix}"
            command = [sys.executable, "-m", "freakc", action, str(env_rejection)]
            if action in ("build", "run"):
                command.extend(["-o", str(output)])
            rejected = run(command, repo, env=bootstrap_env)
            combined = rejected.stdout + rejected.stderr
            assert rejected.returncode != 0, (action, combined)
            assert (
                "Python bootstrap does not support owned process::env results"
                in combined
            ), combined
            assert not output.exists(), output
            assert not env_rejection.with_suffix(".c").exists()

        for action in ("check", "build", "run"):
            output = root / f"bootstrap-negative-{action}{suffix}"
            command = [sys.executable, "-m", "freakc", action, str(negative)]
            if action in ("build", "run"):
                command.extend(["-o", str(output)])
            result = run(command, repo, env=bootstrap_env)
            combined = result.stdout + result.stderr
            assert result.returncode != 0, (action, combined)
            for diagnostic in NEGATIVE_DIAGNOSTICS:
                assert diagnostic in combined, (diagnostic, combined)
            assert not output.exists(), output
            assert not Path(str(negative) + ".c").exists()

        nul_source = root / "bootstrap_source_nul.fk"
        nul_source.write_text(
            'task main() {\n    say "before\0after"\n}\n', encoding="utf-8"
        )
        for action in ("check", "build", "run"):
            output = root / f"bootstrap-nul-{action}{suffix}"
            command = [sys.executable, "-m", "freakc", action, str(nul_source)]
            if action in ("build", "run"):
                command.extend(["-o", str(output)])
            rejected = run(command, repo, env=bootstrap_env)
            combined = rejected.stdout + rejected.stderr
            assert rejected.returncode != 0, (action, combined)
            assert "NUL byte in source is not supported" in combined, combined
            assert not output.exists(), output
            assert not nul_source.with_suffix(".c").exists()

        probe_source = root / "system_runtime_probe.c"
        probe_source.write_text(RUNTIME_PROBE, encoding="utf-8")
        probe_binary = root / f"system_runtime_probe{suffix}"
        command = [
            compiler,
            "-O1",
            "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1",
            "-o",
            str(probe_binary),
            str(probe_source),
            str(runtime / "freak_runtime.c"),
            "-I",
            str(runtime),
        ]
        if sys.platform == "win32":
            command.append("-lws2_32")
        else:
            command.extend(
                ["-lm", "-pthread", "-fsanitize=address", "-fno-omit-frame-pointer"]
            )
        compiled = run(command, repo)
        assert compiled.returncode == 0, compiled.stdout + compiled.stderr
        normal = run([str(probe_binary)], root)
        assert normal.returncode == 0, normal.stdout + normal.stderr
        assert normal.stdout.strip() == "runtime-ok", normal.stdout
        assert "ownership audit found" not in normal.stderr, normal.stderr
        for case, diagnostic in (
            ("empty-name", "invalid environment variable name"),
            ("equals-name", "invalid environment variable name"),
            ("nul-name", "invalid environment variable name"),
            ("nul-value", "invalid environment variable value"),
            ("utf8-name", "not valid UTF-8"),
            ("utf8-value", "not valid UTF-8"),
            ("huge-name", "environment variable name is too large"),
            ("huge-value", "environment variable is too large"),
        ):
            failed = run([str(probe_binary), case], root)
            assert failed.returncode != 0, case
            assert diagnostic in failed.stderr, (case, failed.stderr)

    print("v3 system runtime foundation: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
