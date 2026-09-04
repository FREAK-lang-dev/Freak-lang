#!/usr/bin/env python3
"""Prove the frozen V3 scalar system-runtime foundation."""

from __future__ import annotations

import argparse
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

RUNTIME_PROBE = r'''#define FREAK_SYSTEM_RUNTIME_TEST_HOOKS 1
#include "freak_runtime.c"
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
static atomic_int barrier_enabled = 0;
static atomic_int barrier_snapshot_ready = 0;
static atomic_int barrier_writer_ready = 0;
static atomic_int barrier_allow_write = 0;
static atomic_int barrier_writer_done = 0;

void freak_system_test_snapshot_hook(void) {
    if (!atomic_load(&barrier_enabled)) return;
    atomic_store(&barrier_snapshot_ready, 1);
    while (!atomic_load(&barrier_writer_ready)) {}
    /* The writer is suspended immediately before its lock acquisition. This
       observes the reader's actual lock, with no timing/scheduling assumption. */
    expect(atomic_flag_test_and_set(&freak_process_environment_lock),
           "snapshot must hold environment lock before copying");
    expect(!atomic_load(&barrier_writer_done), "writer has not changed snapshot");
    atomic_store(&barrier_allow_write, 1);
}

void freak_system_test_writer_hook(void) {
    if (!atomic_load(&barrier_enabled)) return;
    atomic_store(&barrier_writer_ready, 1);
    while (!atomic_load(&barrier_allow_write)) {}
}

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
    if (atomic_load(&barrier_enabled)) {
        while (!atomic_load(&barrier_snapshot_ready)) {}
        freak_process_set_env(name, freak_word_lit("writer-A-λ"));
        atomic_store(&barrier_writer_done, 1);
        return;
    }
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
    HANDLE second_reader = CreateThread(NULL, 0, stress_reader, NULL, 0, NULL);
    expect(writer != NULL && reader != NULL && second_reader != NULL,
           "create environment stress threads");
    while (atomic_load(&stress_ready) != 3) {
    }
    atomic_store(&stress_go, 1);
    expect(WaitForSingleObject(writer, INFINITE) == WAIT_OBJECT_0,
           "join environment writer");
    expect(WaitForSingleObject(reader, INFINITE) == WAIT_OBJECT_0,
           "join environment reader");
    expect(WaitForSingleObject(second_reader, INFINITE) == WAIT_OBJECT_0,
           "join second environment reader");
    CloseHandle(writer);
    CloseHandle(reader);
    CloseHandle(second_reader);
#else
    pthread_t writer;
    pthread_t reader;
    pthread_t second_reader;
    expect(pthread_create(&writer, NULL, stress_writer, NULL) == 0,
           "create environment writer");
    expect(pthread_create(&reader, NULL, stress_reader, NULL) == 0,
           "create environment reader");
    expect(pthread_create(&second_reader, NULL, stress_reader, NULL) == 0,
           "create second environment reader");
    while (atomic_load(&stress_ready) != 3) {
    }
    atomic_store(&stress_go, 1);
    expect(pthread_join(writer, NULL) == 0, "join environment writer");
    expect(pthread_join(reader, NULL) == 0, "join environment reader");
    expect(pthread_join(second_reader, NULL) == 0, "join second environment reader");
#endif
    expect(atomic_load(&stress_failed) == 0, "serialized environment snapshots");
}

static int run_environment_barrier(void) {
    freak_word name = freak_word_lit(stress_name);
    freak_process_set_env(name, freak_word_lit("initial"));
    atomic_store(&barrier_enabled, 1);
#ifdef _WIN32
    HANDLE writer = CreateThread(NULL, 0, stress_writer, NULL, 0, NULL);
    expect(writer != NULL, "create barrier writer");
#else
    pthread_t writer;
    expect(pthread_create(&writer, NULL, stress_writer, NULL) == 0,
           "create barrier writer");
#endif
    freak_word captured = freak_process_env(name);
#ifdef _WIN32
    expect(WaitForSingleObject(writer, INFINITE) == WAIT_OBJECT_0,
           "join barrier writer");
    CloseHandle(writer);
#else
    expect(pthread_join(writer, NULL) == 0, "join barrier writer");
#endif
    expect(atomic_load(&barrier_writer_done), "writer completes after copy");
    expect(captured.length == 7 && memcmp(captured.data, "initial", 7) == 0,
           "captured bytes survive concurrent overwrite");
    freak_word_release_owned(&captured);
    puts("barrier-ok");
    return 0;
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
    if (strcmp(argv[1], "lock-probe") == 0) return run_environment_barrier();
    if (strcmp(argv[1], "audit-race") == 0) {
        run_environment_stress();
        puts("audit-race-ok");
        return 0;
    }
    if (strcmp(argv[1], "audit-leak") == 0) {
        freak_process_set_env(freak_word_lit(stress_name), freak_word_lit("owned"));
        (void)freak_process_env(freak_word_lit(stress_name));
        return 0;
    }
    if (strcmp(argv[1], "timespec") == 0 && argc == 5) {
        printf("%lld\n", (long long)freak_time_from_timespec(
            strtoll(argv[2], NULL, 10), strtoll(argv[3], NULL, 10), atoi(argv[4])));
        return 0;
    }
    if (strcmp(argv[1], "counter") == 0 && argc == 4) {
        printf("%lld\n", (long long)freak_time_from_counter(
            strtoll(argv[2], NULL, 10), strtoll(argv[3], NULL, 10)));
        return 0;
    }
    if (strcmp(argv[1], "filetime") == 0 && argc == 3) {
        printf("%lld\n", (long long)freak_time_from_filetime(strtoull(argv[2], NULL, 10)));
        return 0;
    }
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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "freak", nargs="?", type=Path,
        help="existing exact-source CLI (omit to reconstruct one outside the repo)",
    )
    parser.add_argument(
        "--runtime-root", type=Path,
        help="runtime payload to compile (defaults to the repository runtime)",
    )
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    runtime = (
        args.runtime_root.resolve() if args.runtime_root is not None
        else (repo / "freakc" / "runtime").resolve()
    )
    assert (runtime / "freak_runtime.c").is_file(), runtime
    assert (runtime / "freak_llvm_runtime.c").is_file(), runtime
    compiler = os.environ.get("FREAK_CLANG") or shutil.which("clang")
    assert compiler, "Clang is required for the C/LLVM system regression"
    suffix = ".exe" if sys.platform == "win32" else ""
    test_env = os.environ.copy()
    test_env[CAPTURE_NAME] = INITIAL_VALUE
    test_env.pop(MISSING_NAME, None)

    with tempfile.TemporaryDirectory(prefix="freak-v3-system-runtime-") as temporary:
        root = Path(temporary)
        freak = (
            args.freak.resolve() if args.freak is not None
            else foundation.build_fresh_cli(
                clang=compiler, repo=repo, root=root, runtime_root=runtime
            )
        )
        assert freak.is_file(), freak
        print(f"system runtime CLI: {freak}", flush=True)
        print(f"system runtime payload: {runtime}", flush=True)
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
            if backend == "llvm":
                assert "call void @freak_llvm_process_set_env(" in generated_text
                assert "call i64 @freak_llvm_process_set_env(" not in generated_text
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

        # Supplemental repository-bootstrap checks. Native generation and all
        # audited runtime probes above/below use the explicitly selected payload.
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

        for api in ("env", "env_var"):
            env_rejection = root / f"bootstrap_{api}_rejection.fk"
            env_rejection.write_text(
                BOOTSTRAP_ENV_REJECTION.replace("process::env(", f"process::{api}("),
                encoding="utf-8",
            )
            for action in ("check", "build", "run"):
                output = root / f"bootstrap-{api}-rejection-{action}{suffix}"
                command = [sys.executable, "-m", "freakc", action, str(env_rejection)]
                if action in ("build", "run"):
                    command.extend(["-o", str(output)])
                rejected = run(command, repo, env=bootstrap_env)
                combined = rejected.stdout + rejected.stderr
                assert rejected.returncode != 0, (api, action, combined)
                assert (
                    f"Python bootstrap does not support owned process::{api} results"
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
        race = run([str(probe_binary), "audit-race"], root, timeout=30)
        assert race.returncode == 0, race.stdout + race.stderr
        assert race.stdout.strip() == "audit-race-ok", race.stdout
        leak = run([str(probe_binary), "audit-leak"], root, timeout=30)
        assert leak.returncode == 87, leak.stdout + leak.stderr
        assert "C ownership audit found 1 unreleased word allocation(s)" in leak.stderr
        barrier = run([str(probe_binary), "lock-probe"], root, timeout=30)
        assert barrier.returncode == 0, barrier.stdout + barrier.stderr
        assert barrier.stdout.strip() == "barrier-ok", barrier.stdout

        # Negative control: remove only the snapshot acquisitions, retaining the
        # writer's lock and all probe assertions. The barrier must detect this.
        runtime_text = (runtime / "freak_runtime.c").read_text(encoding="utf-8")
        snapshot_start = runtime_text.index("static bool freak_process_environment_snapshot(")
        snapshot_end = runtime_text.index("freak_maybe_word freak_process_env_var(", snapshot_start)
        snapshot_text = runtime_text[snapshot_start:snapshot_end]
        assert snapshot_text.count("freak_process_environment_acquire();") == 2
        mutant_text = (
            runtime_text[:snapshot_start]
            + snapshot_text.replace("freak_process_environment_acquire();", "/* missing lock */")
            + runtime_text[snapshot_end:]
        )
        (root / "mutant_runtime.c").write_text(mutant_text, encoding="utf-8")
        mutant_source = root / "system_runtime_mutant.c"
        mutant_source.write_text(
            RUNTIME_PROBE.replace('#include "freak_runtime.c"', '#include "mutant_runtime.c"'),
            encoding="utf-8",
        )
        mutant_binary = root / f"system_runtime_mutant{suffix}"
        mutant_command = [
            str(mutant_binary) if arg == str(probe_binary) else
            str(mutant_source) if arg == str(probe_source) else arg
            for arg in command
        ]
        mutant_compile = run(mutant_command, repo)
        assert mutant_compile.returncode == 0, mutant_compile.stdout + mutant_compile.stderr
        mutant = run([str(mutant_binary), "lock-probe"], root, timeout=30)
        assert mutant.returncode == 2, mutant.stdout + mutant.stderr
        assert "snapshot must hold environment lock before copying" in mutant.stderr

        # Invoke the exact private conversion functions used by the OS samplers.
        # All platforms exercise POSIX and Windows conversion arithmetic.
        max_int = (1 << 63) - 1
        epoch = 116_444_736_000_000_000
        for args, expected in (
            (("timespec", 0, 0, 1), 0),
            (("timespec", 1, 999_999, 1), 1000),
            (("timespec", max_int // 1000, 807_999_999, 1), max_int),
            (("timespec", 0, 999_999_999, 0), 999_999_999),
            (("timespec", max_int // 1_000_000_000, 854_775_807, 0), max_int),
            (("filetime", epoch), 0),
            (("filetime", epoch + 9999), 0),
            (("filetime", epoch + 10000), 1),
            (("filetime", (1 << 64) - 1), (((1 << 64) - 1) - epoch) // 10000),
            (("counter", 0, 1), 0),
            (("counter", 1, 3), 333_333_333),
            (("counter", max_int - 1, max_int), 999_999_999),
            (("counter", max_int, 1_000_000_000), max_int),
        ):
            sampled = run([str(probe_binary), *map(str, args)], root, timeout=30)
            assert sampled.returncode == 0, (args, sampled.stderr)
            assert sampled.stdout.strip() == str(expected), (args, sampled.stdout, expected)
        for args, diagnostic in (
            (("timespec", -1, 0, 1), "predates the Unix epoch"),
            (("timespec", 0, -1, 1), "invalid wall clock value"),
            (("timespec", 0, 1_000_000_000, 1), "invalid wall clock value"),
            (("timespec", max_int // 1000 + 1, 0, 1), "milliseconds overflow int"),
            (("timespec", max_int // 1000, 808_000_000, 1), "milliseconds overflow int"),
            (("timespec", -1, 0, 0), "invalid monotonic clock value"),
            (("timespec", 0, -1, 0), "invalid monotonic clock value"),
            (("timespec", 0, 1_000_000_000, 0), "invalid monotonic clock value"),
            (("timespec", max_int // 1_000_000_000 + 1, 0, 0), "nanoseconds overflow int"),
            (("timespec", max_int // 1_000_000_000, 854_775_808, 0), "nanoseconds overflow int"),
            (("filetime", epoch - 1), "predates the Unix epoch"),
            (("counter", -1, 1), "cannot read the monotonic clock"),
            (("counter", 0, 0), "cannot read the monotonic clock"),
            (("counter", 0, -1), "cannot read the monotonic clock"),
            (("counter", max_int, 1), "nanoseconds overflow int"),
            (("counter", 92_233_720_369, 10), "nanoseconds overflow int"),
        ):
            sampled = run([str(probe_binary), *map(str, args)], root, timeout=30)
            assert sampled.returncode != 0, args
            assert diagnostic in sampled.stderr, (args, sampled.stderr)
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
