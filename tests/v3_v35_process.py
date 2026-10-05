#!/usr/bin/env python3
"""Exercise real V3.5 shell-free launches and both scalar runtime ABIs.

This direct runtime gate does not use a Python language compiler or tracked
convenience executable. The independently compiled child exposes argv bytes,
floods both pipes, and creates adverse lifetime/status cases.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import select
import subprocess
import sys
import tempfile
import time


CHILD = r'''
#ifndef _WIN32
#define _POSIX_C_SOURCE 200809L
#endif
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#ifdef _WIN32
#include <windows.h>
#include <shellapi.h>
#include <io.h>
#include <fcntl.h>
#else
#include <unistd.h>
#include <signal.h>
#include <time.h>
#endif
static void pause_ms(int ms) {
#ifdef _WIN32
    Sleep((DWORD)ms);
#else
    struct timespec delay = {ms / 1000, (ms % 1000) * 1000000L};
    nanosleep(&delay, NULL);
#endif
}
int main(int argc, char **argv) {
    if (argc < 2) return 92;
#ifdef _WIN32
    _setmode(_fileno(stdout), _O_BINARY);
    _setmode(_fileno(stderr), _O_BINARY);
#endif
    if (strcmp(argv[1], "args") == 0) {
        for (int i = 2; i < argc; i++) {
            printf("%zu:", strlen(argv[i]));
            for (const unsigned char *p = (const unsigned char *)argv[i]; *p; p++) printf("%02x", *p);
            putchar('\n');
        }
        return 0;
    }
    if (strcmp(argv[1], "dual") == 0) {
        char bytes[1024];
        memset(bytes, 'O', sizeof(bytes));
        char errors[1024]; memset(errors, 'E', sizeof(errors));
        for (int i = 0; i < 192; i++) {
            fwrite(bytes, 1, sizeof(bytes), stdout); fflush(stdout);
            fwrite(errors, 1, sizeof(errors), stderr); fflush(stderr);
        }
        return 0;
    }
    if (strcmp(argv[1], "binary") == 0) {
        const unsigned char bytes[] = {'A', 0, 0xff, 'B'};
        fwrite(bytes, 1, sizeof(bytes), stdout); return 0;
    }
    if (strcmp(argv[1], "exit127") == 0) return 127;
    if (strcmp(argv[1], "env") == 0) {
#ifdef _WIN32
        wchar_t wide[128];
        SetLastError(ERROR_SUCCESS);
        DWORD n = GetEnvironmentVariableW(L"FREAK_V35_CHILD_ENV", wide, 128);
        if (!n && GetLastError() == ERROR_ENVVAR_NOT_FOUND) { puts("missing"); return 4; }
        char text[512];
        WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, wide, -1, text, sizeof(text), NULL, NULL);
        puts(text); return 0;
#else
        const char *value = getenv("FREAK_V35_CHILD_ENV");
        puts(value ? value : "missing"); return value ? 0 : 4;
#endif
    }
    if (strcmp(argv[1], "cwd") == 0) {
        FILE *file = fopen("cwd-marker", "rb");
        if (!file) return 6;
        fclose(file); puts("CWD_OK"); return 0;
    }
    if (strcmp(argv[1], "inherit") == 0) {
        char line[128];
        if (!fgets(line, sizeof(line), stdin)) return 9;
        printf("INHERIT:%s", line); fputs("INHERIT_ERR\n", stderr); return 0;
    }
    if (strcmp(argv[1], "sleep") == 0) { pause_ms(10000); return 0; }
#ifndef _WIN32
    if (strcmp(argv[1], "signal") == 0) { raise(SIGTERM); return 98; }
    if (strcmp(argv[1], "tree") == 0 || strcmp(argv[1], "orphan") == 0) {
        pid_t pid = fork();
        if (pid < 0) return 10;
        if (!pid) {
            pause_ms(700);
            FILE *marker = fopen(argv[2], "wb");
            if (marker) { fputs("SURVIVED", marker); fclose(marker); }
            _exit(0);
        }
        if (strcmp(argv[1], "orphan") == 0) return 0;
        pause_ms(10000); return 0;
    }
#endif
    return 93;
}
'''

WINDOWS_ARGV_WRAPPER = r'''
#ifdef _WIN32
#include <windows.h>
#include <shellapi.h>
int main(int argc, char **argv) {
    (void)argc; (void)argv;
    int count = 0;
    wchar_t **wide = CommandLineToArgvW(GetCommandLineW(), &count);
    if (!wide) return 95;
    char **utf8 = calloc((size_t)count + 1, sizeof(char *));
    if (!utf8) return 95;
    for (int i = 0; i < count; i++) {
        int size = WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, wide[i], -1, NULL, 0, NULL, NULL);
        if (size <= 0 || !(utf8[i] = malloc((size_t)size))) return 95;
        if (WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, wide[i], -1, utf8[i], size, NULL, NULL) != size) return 95;
    }
    LocalFree(wide);
    int result = native_main(count, utf8);
    for (int i = 0; i < count; i++) free(utf8[i]);
    free(utf8);
    return result;
}
#else
int main(int argc, char **argv) { return native_main(argc, argv); }
#endif
'''


HARNESS = r'''
#include "freak_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#ifdef _WIN32
#include <windows.h>
#else
#include <signal.h>
#include <unistd.h>
#endif
static void require(int condition, const char *reason) {
    if (!condition) { fprintf(stderr, "FAIL: %s\n", reason); exit(2); }
}
#ifdef USE_LLVM_ADAPTER
extern void freak_llvm_word_release_replaced(int64_t previous, int64_t replacement);
#define new_command(s) freak_llvm_process_command_new((int64_t)(intptr_t)(s))
#define argument(h,s) freak_llvm_process_command_arg(h, (int64_t)(intptr_t)(s))
#define cwd(h,s) freak_llvm_process_command_cwd(h, (int64_t)(intptr_t)(s))
#define environment(h,k,v) freak_llvm_process_command_env(h,(int64_t)(intptr_t)(k),(int64_t)(intptr_t)(v))
#define unset_environment(h,k) freak_llvm_process_command_unset_env(h,(int64_t)(intptr_t)(k))
#define run freak_llvm_process_command_run
#define spawn freak_llvm_process_command_spawn
#define wait_child freak_llvm_process_command_wait
#define terminate freak_llvm_process_command_terminate
#define release freak_llvm_process_command_release
#define status freak_llvm_process_command_status
#define exit_code freak_llvm_process_command_exit_code
#define signal_number freak_llvm_process_command_signal
#define run_inherit freak_llvm_process_command_run_inherit
#define bytes freak_llvm_process_command_stdout_bytes
#define error_bytes freak_llvm_process_command_stderr_bytes
static freak_word output(int64_t h) { return freak_llvm_word_view(freak_llvm_process_command_stdout(h)); }
static freak_word errors(int64_t h) { return freak_llvm_word_view(freak_llvm_process_command_stderr(h)); }
static freak_word error(int64_t h) { return freak_llvm_word_view(freak_llvm_process_command_error(h)); }
static void drop_word(freak_word *value) { freak_llvm_word_release_replaced((int64_t)(intptr_t)value->data, 0); *value = freak_word_lit(""); }
#else
#define new_command(s) freak_process_command_new(freak_word_lit(s))
#define argument(h,s) freak_process_command_arg(h,freak_word_lit(s))
#define cwd(h,s) freak_process_command_cwd(h,freak_word_lit(s))
#define environment(h,k,v) freak_process_command_env(h,freak_word_lit(k),freak_word_lit(v))
#define unset_environment(h,k) freak_process_command_unset_env(h,freak_word_lit(k))
#define run freak_process_command_run
#define spawn freak_process_command_spawn
#define wait_child freak_process_command_wait
#define terminate freak_process_command_terminate
#define release freak_process_command_release
#define status freak_process_command_status
#define exit_code freak_process_command_exit_code
#define signal_number freak_process_command_signal
#define run_inherit freak_process_command_run_inherit
#define bytes freak_process_command_stdout_bytes
#define error_bytes freak_process_command_stderr_bytes
#define output freak_process_command_stdout
#define errors freak_process_command_stderr
#define error freak_process_command_error
#define drop_word freak_word_release_owned
#endif
static int64_t child(const char *path, const char *mode) {
    int64_t h = new_command(path); argument(h, mode); return h;
}
static void zero_owners(void) {
    require(freak_process_command_live() == 0, "command owners conserved");
    require(freak_process_command_children() == 0, "children reaped");
    require(freak_process_command_retained_bytes() == 0, "command allocations conserved");
}
int main(int argc, char **argv) {
    require(argc == 5, "harness arguments");
    const char *path = argv[1], *directory = argv[2], *marker = argv[3], *mode = argv[4];
    if (strcmp(mode, "stale") == 0) {
        int64_t old = child(path, "exit127"); release(old);
        int64_t reused = child(path, "exit127");
        require(reused != old, "ticket generation changed");
        status(old); return 94;
    }
    if (strcmp(mode, "double") == 0) { int64_t h = child(path,"exit127"); release(h); release(h); return 94; }
    if (strcmp(mode, "foreign") == 0) { int64_t b = freak_byte_buffer_new(); status(b); return 94; }
    if (strcmp(mode, "live-audit") == 0) { new_command(path); return 0; }
    if (strcmp(mode, "text-binary") == 0) {
        int64_t h = child(path,"binary"); run(h, 2000, 1024, 1024); output(h); return 94;
    }
    if (strcmp(mode, "mutate-running") == 0) {
        int64_t h = child(path,"sleep"); spawn(h, 2000, 1024, 1024); argument(h,"late"); return 94;
    }
    if (strcmp(mode, "inherit") == 0) {
        int64_t h = child(path,"inherit");
        require(run_inherit(h, 0) == FREAK_COMMAND_EXITED && exit_code(h) == 0, "inherited standard handles");
        release(h); zero_owners(); return 0;
    }
    const char *arguments[] = {"", "a b", "\"quoted\"", "end\\", "%PATH%", "$HOME", "a&b", "\\\"", "λ雪"};
    char expected[2048]; size_t used = 0;
    int64_t h = child(path,"args");
    for (size_t i = 0; i < sizeof(arguments)/sizeof(arguments[0]); i++) {
        argument(h, arguments[i]);
        used += (size_t)snprintf(expected + used, sizeof(expected) - used, "%zu:", strlen(arguments[i]));
        for (const unsigned char *p = (const unsigned char *)arguments[i]; *p; p++)
            used += (size_t)snprintf(expected + used, sizeof(expected) - used, "%02x", *p);
        expected[used++] = '\n'; expected[used] = 0;
    }
    require(run(h, 5000, 4096, 4096) == FREAK_COMMAND_EXITED && exit_code(h) == 0, "argv child exit");
    freak_word text = output(h);
    require(text.length == used && memcmp(text.data, expected, used) == 0, "literal exact argv bytes");
    release(h);
    require(memcmp(text.data, expected, used) == 0, "capture owner survives ticket release");
    drop_word(&text);
    h = child(path,"dual");
    require(run(h, 5000, 256*1024, 256*1024) == FREAK_COMMAND_EXITED && exit_code(h) == 0, "concurrent dual-pipe drain");
    text = output(h); freak_word err = errors(h);
    require(text.length == 192*1024 && err.length == 192*1024, "complete both streams");
    for (size_t i = 0; i < text.length; i++) require(text.data[i] == 'O' && err.data[i] == 'E', "dual-stream bytes");
    drop_word(&text); drop_word(&err); release(h);
    h = child(path,"exit127");
    require(run(h, 2000, 1024, 1024) == FREAK_COMMAND_EXITED && exit_code(h) == 127, "real exit127 distinct from spawn failure");
    release(h);
    h = new_command("freak-v35-definitely-no-such-executable");
    require(run(h, 2000, 1024, 1024) == FREAK_COMMAND_SPAWN_FAILED && exit_code(h) == -1, "missing executable is spawn failure");
    text = error(h); require(text.length > 0, "spawn error diagnostic"); drop_word(&text); release(h);
    h = child(path,"cwd"); cwd(h,directory);
    require(run(h, 2000, 1024, 1024) == FREAK_COMMAND_EXITED && exit_code(h) == 0, "explicit cwd"); release(h);
    h = child(path,"cwd"); cwd(h,"freak-v35-no-such-working-directory");
    require(run(h, 2000, 1024, 1024) == FREAK_COMMAND_SPAWN_FAILED, "invalid cwd spawn failure"); release(h);
    h = child(path,"env"); environment(h,"FREAK_V35_CHILD_ENV","first"); environment(h,"FREAK_V35_CHILD_ENV","λ雪 %$&");
    require(run(h, 2000, 1024, 1024) == FREAK_COMMAND_EXITED && exit_code(h) == 0, "explicit environment");
    text = output(h); require(strcmp(text.data,"λ雪 %$&\n") == 0,"environment is literal");
    drop_word(&text); release(h);
    h = child(path,"env"); environment(h,"FREAK_V35_CHILD_ENV","present"); unset_environment(h,"FREAK_V35_CHILD_ENV");
    require(run(h, 2000, 1024, 1024) == FREAK_COMMAND_EXITED && exit_code(h) == 4, "unset removes inherited and explicit environment"); release(h);
    h = child(path,"env"); unset_environment(h,"FREAK_V35_CHILD_ENV"); environment(h,"FREAK_V35_CHILD_ENV","");
    require(run(h, 2000, 1024, 1024) == FREAK_COMMAND_EXITED && exit_code(h) == 0, "empty environment distinct from unset"); release(h);
#ifndef _WIN32
    h = child(strrchr(path,'/') + 1,"exit127"); environment(h,"PATH",directory);
    require(run(h, 2000, 1024, 1024) == FREAK_COMMAND_EXITED && exit_code(h) == 127,"explicit PATH search without shell"); release(h);
    char script[4096]; snprintf(script,sizeof(script),"%s/script-without-shebang",directory);
    h = new_command(script);
    require(run(h, 2000, 1024, 1024) == FREAK_COMMAND_SPAWN_FAILED,"ENOEXEC cannot fall back to shell"); release(h);
#endif
    h = child(path,"binary");
    require(run(h, 2000, 1024, 1024) == FREAK_COMMAND_EXITED, "binary capture");
    int64_t b = bytes(h); release(h);
    require(freak_byte_buffer_length(b) == 4, "binary length preserved");
    require(freak_byte_buffer_read_byte(b) == 'A' && freak_byte_buffer_read_byte(b) == 0 &&
            freak_byte_buffer_read_byte(b) == 255 && freak_byte_buffer_read_byte(b) == 'B', "binary bytes preserved");
    freak_byte_buffer_release(b);
    h = child(path,"dual");
    require(run(h, 5000, 17, 33) == FREAK_COMMAND_OUTPUT_LIMIT, "bounded capture terminates child");
    b = bytes(h); require(freak_byte_buffer_length(b) <= 17,"stdout limit bounds retained bytes"); freak_byte_buffer_release(b); release(h);
    h = child(path,"dual");
    require(run(h, 5000, 1024*1024, 23) == FREAK_COMMAND_OUTPUT_LIMIT,"stderr independently limited");
    b = error_bytes(h); require(freak_byte_buffer_length(b) <= 23,"stderr retained bytes bounded"); freak_byte_buffer_release(b); release(h);
    h = child(path,"sleep");
    require(run(h, 80, 1024, 1024) == FREAK_COMMAND_TIMED_OUT, "absolute timeout"); release(h);
    h = child(path,"sleep"); require(spawn(h, 5000, 1024, 1024) == FREAK_COMMAND_RUNNING,"real asynchronous spawn");
    terminate(h); require(status(h) == FREAK_COMMAND_CANCELLED && wait_child(h) == FREAK_COMMAND_CANCELLED,"cancel and idempotent wait"); release(h);
    h = child(path,"sleep"); require(spawn(h, 5000, 1024, 1024) == FREAK_COMMAND_RUNNING,"spawn before release"); release(h);
#ifndef _WIN32
    h = child(path,"signal");
    require(run(h, 2000, 1024, 1024) == FREAK_COMMAND_SIGNALED && signal_number(h) == SIGTERM, "signal distinct from exit"); release(h);
    h = child(path,"tree"); argument(h,marker);
    require(run(h, 80, 1024, 1024) == FREAK_COMMAND_TIMED_OUT,"timeout owned tree"); release(h);
    h = child(path,"orphan"); argument(h,marker);
    require(run(h, 2000, 1024, 1024) == FREAK_COMMAND_EXITED,"exited parent cannot retain writer descendants"); release(h);
#endif
    for (int repeat = 0; repeat < 96; repeat++) {
        h = child(path,"exit127"); require(run(h,2000,16,16) == FREAK_COMMAND_EXITED,"soak launch"); release(h); zero_owners();
    }
    zero_owners(); puts("PROCESS_OK"); return 0;
}
'''


def checked(command: list[str], *, timeout: int = 90, **kwargs: object) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=timeout, **kwargs)
    assert result.returncode == 0, f"{command}\n{result.stdout}\n{result.stderr}"
    return result


def controlling_terminal(command: list[str], *, cwd: Path, env: dict[str, str]) -> None:
    """pty.fork supplies a real controlling TTY/foreground process group."""
    if sys.platform == "win32":
        return
    import errno
    import pty
    import signal
    child, terminal = pty.fork()
    if child == 0:
        os.chdir(cwd)
        os.execve(command[0], command, env)
    output = bytearray()
    deadline = time.monotonic() + 10
    result = None
    try:
        os.write(terminal, b"terminal input\n")
        while time.monotonic() < deadline:
            readable, _, _ = select.select([terminal], [], [], 0.1)
            if readable:
                try:
                    data = os.read(terminal, 4096)
                except OSError as error:
                    if error.errno != errno.EIO:
                        raise
                    data = b""
                output.extend(data)
            waited, status = os.waitpid(child, os.WNOHANG)
            if waited:
                result = os.waitstatus_to_exitcode(status)
                break
        assert result == 0 and b"INHERIT:terminal input" in output and b"INHERIT_ERR" in output, (result, output)
    finally:
        if result is None:
            os.kill(child, signal.SIGKILL)
            os.waitpid(child, 0)
        os.close(terminal)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG", "clang"))
    parser.add_argument("--optimization", type=int, choices=(0, 2, 3), action="append")
    parser.add_argument("--sanitize", action="store_true", help="require ASan/UBSan and its failing control")
    args = parser.parse_args()
    compiler = shutil.which(args.clang)
    assert compiler, f"Clang not found: {args.clang}"
    repo = Path(__file__).resolve().parents[1]
    runtime = repo / "freakc" / "runtime"
    env = os.environ.copy()
    env["ASAN_OPTIONS"] = "detect_leaks=1:halt_on_error=1"
    env["UBSAN_OPTIONS"] = "halt_on_error=1"
    suffix = ".exe" if sys.platform == "win32" else ""
    with tempfile.TemporaryDirectory(prefix="freak-v35-argv-λ $ & ") as temporary:
        root = Path(temporary)
        child_source = root / "child.c"
        child_source.write_text(CHILD.replace("int main(", "static int native_main(") + WINDOWS_ARGV_WRAPPER, encoding="utf-8")
        child = root / f"argv child{suffix}"
        child_flags = ["-lshell32"] if sys.platform == "win32" else []
        checked([compiler, str(child_source), "-O2", *child_flags, "-o", str(child)], cwd=root)
        (root / "cwd-marker").write_text("ok", encoding="utf-8")
        harness_source = root / "harness.c"
        harness_source.write_text(HARNESS.replace("int main(", "static int native_main(") + WINDOWS_ARGV_WRAPPER, encoding="utf-8")
        script = root / "script-without-shebang"
        script.write_text("exit 0\n", encoding="utf-8")
        script.chmod(0o700)
        flags = ["-lws2_32", "-lshell32"] if sys.platform == "win32" else ["-lm"]
        if args.sanitize:
            flags += ["-fsanitize=address,undefined", "-fno-omit-frame-pointer", "-g"]
            control_source = root / "sanitizer-control.c"
            control_source.write_text("#include <stdlib.h>\nint main(int n,char **v){volatile char *p=malloc(1);p[n+4]=3;free((void*)p);return 0;}\n")
            control = root / f"sanitizer-control{suffix}"
            checked([compiler, str(control_source), "-O0", *flags, "-o", str(control)], cwd=root)
            failed = subprocess.run([str(control)], capture_output=True, text=True, env=env, timeout=20)
            assert failed.returncode != 0 and "AddressSanitizer" in failed.stderr, failed.stderr
        for optimization in args.optimization or (0, 2, 3):
            for adapter in ("c", "llvm"):
                parent = root / f"process-{adapter}-O{optimization}{suffix}"
                command = [compiler, str(harness_source), str(runtime / "freak_runtime.c"),
                           str(runtime / "freak_llvm_runtime.c"), f"-I{runtime}", f"-O{optimization}",
                           "-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1", "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1",
                           "-D_CRT_SECURE_NO_WARNINGS", *flags, "-o", str(parent)]
                if adapter == "llvm":
                    command.insert(1, "-DUSE_LLVM_ADAPTER=1")
                checked(command, cwd=root)
                marker = root / f"escaped-tree-{adapter}-{optimization}"
                base = [str(parent), str(child), str(root), str(marker)]
                result = checked([*base, "normal"], cwd=root, env=env)
                assert result.stdout == "PROCESS_OK\n", result.stdout
                inherited = checked([*base, "inherit"], cwd=root, env=env, input="literal input\n")
                assert inherited.stdout == "INHERIT:literal input\n", inherited.stdout
                assert inherited.stderr == "INHERIT_ERR\n", inherited.stderr
                controlling_terminal([*base, "inherit"], cwd=root, env=env)
                for case, message in (
                    ("stale", "invalid or stale command ticket"),
                    ("double", "invalid or stale command ticket"),
                    ("foreign", "invalid or stale command ticket"),
                    ("live-audit", "ownership audit found"),
                    ("text-binary", "use the bytes getter"),
                    ("mutate-running", "command was already launched"),
                ):
                    failed = subprocess.run([*base, case], cwd=root, env=env, capture_output=True,
                                            text=True, encoding="utf-8", timeout=20)
                    assert failed.returncode != 0 and message in failed.stderr, (case, failed.stdout, failed.stderr)
                # Normal lane lasted longer than the marker child's 700ms delay;
                # an escaped process tree would have materialized this file.
                assert not marker.exists(), f"descendant survived tree cleanup: {marker}"
                print(f"PASS command tickets {adapter} O{optimization}: exact argv, dual streams, lifecycle/status, limits, owners", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
