#!/usr/bin/env python3
"""Exercise V3.5 CLI argv forwarding and Doctor with a supplied native candidate.

This harness never builds a compiler or invokes a Python compiler fallback.
The supplied candidate and --repo payload must come from the same revision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from v3_final_release_gate import manifest_entries


ARGV_PROGRAM = '''task main() {
    say "FREAK_ARGV_BEGIN"
    pilot index = 1
    repeat until index >= process::args_count() {
        pilot argument: word = process::arg(index)
        say word_from_int(argument.length()) + ":" + argument
        index += 1
    }
    say "FREAK_ARGV_END"
    if process::env("FREAK_V35_TEST_INPUT") == "1" {
        say "INPUT=" + process::input()
    }
    if process::env("FREAK_V35_TEST_EXIT") == "23" { process::exit(23) }
}
'''

CLANG_WRAPPER_NARROW_BASELINE = r'''#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <process.h>
#else
#include <unistd.h>
#endif
int main(int argc, char **argv) {
    const char *compiler = getenv("FREAK_V35_TEST_REAL_CLANG");
    const char *version = getenv("FREAK_V35_TEST_VERSION");
    if (!compiler || !version) return 90;
    if (argc == 2 && strcmp(argv[1], "--version") == 0) {
        puts(version);
        return 0;
    }
    const char *log = getenv("FREAK_V35_TEST_CLANG_LOG");
    if (log) {
        FILE *out = fopen(log, "ab");
        if (!out) return 91;
        fputs("compile\n", out);
        fclose(out);
    }
    const char *broken = getenv("FREAK_V35_TEST_BROKEN_CLANG");
    if (broken && strcmp(broken, "1") == 0) return 42;
    argv[0] = (char *)compiler;
#ifdef _WIN32
    return (int)_spawnv(_P_WAIT, compiler, (const char * const *)argv);
#else
    execv(compiler, argv);
    perror("execv real Clang");
    return 92;
#endif
}
'''


CLANG_WRAPPER = r'''#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <process.h>
#include <windows.h>
#include <corecrt_startup.h>
#include <stdint.h>
#include <wchar.h>
/* CRT spawn joins strings with spaces. Escape each receiving-CRT argument,
   including argv[0], empty strings, embedded quotes and trailing backslashes. */
static wchar_t *quote_spawn_argument(const wchar_t *argument) {
    size_t length=wcslen(argument);
    if(length>(SIZE_MAX/sizeof(wchar_t)-3)/2)return NULL;
    wchar_t *quoted=calloc(length*2+3,sizeof(wchar_t));
    if(!quoted)return NULL;
    size_t used=0; quoted[used++]=L'"';
    const wchar_t *cursor=argument;
    while(*cursor) {
        size_t slashes=0;
        while(*cursor==L'\\'){slashes++;cursor++;}
        size_t escaped=(*cursor==L'"'||!*cursor)?slashes*2:slashes;
        for(size_t i=0;i<escaped;i++)quoted[used++]=L'\\';
        if(*cursor==L'"')quoted[used++]=L'\\';
        if(*cursor)quoted[used++]=*cursor++;
    }
    quoted[used++]=L'"';
    return quoted;
}
static int forward_spawn(const wchar_t *compiler,int count,wchar_t **arguments) {
#ifdef FREAK_V35_CLI_TEST_UNQUOTED_FORWARD
    /* Isolate the old joining defect with UTF-16 unchanged. The separately
       compiled original narrow wrapper covers its ASCII-only _spawnv hop. */
    return (int)_wspawnv(_P_WAIT,compiler,(const wchar_t *const *)arguments);
#else
    if(count<1||(size_t)count>SIZE_MAX/sizeof(wchar_t *)-1)return 96;
    wchar_t **quoted=calloc((size_t)count+1,sizeof(wchar_t *));
    if(!quoted)return 96;
    size_t command_length=0;
    int result=96;
    for(int i=0;i<count;i++) {
        if(!arguments[i]||!(quoted[i]=quote_spawn_argument(arguments[i])))goto done;
        size_t length=wcslen(quoted[i]);
        size_t separator=i?1:0;
        if(length>32766-separator||command_length>32766-separator-length)goto done;
        command_length+=length+separator;
    }
    result=(int)_wspawnv(_P_WAIT,compiler,(const wchar_t *const *)quoted);
done:
    for(int i=0;i<count;i++)free(quoted[i]);
    free(quoted);
    return result;
#endif
}
static wchar_t *wide_environment(const wchar_t *name) {
    DWORD capacity=GetEnvironmentVariableW(name,NULL,0);
    if(!capacity||capacity>32768)return NULL;
    wchar_t *value=calloc(capacity,sizeof(wchar_t));
    if(!value)return NULL;
    DWORD copied=GetEnvironmentVariableW(name,value,capacity);
    if(!copied||copied>=capacity){free(value);return NULL;}
    return value;
}
#else
#include <unistd.h>
#endif
int main(int argc, char **argv) {
    const char *compiler = getenv("FREAK_V35_TEST_REAL_CLANG");
    const char *version = getenv("FREAK_V35_TEST_VERSION");
    if (!compiler || !version) return 90;
    if (argc == 2 && strcmp(argv[1], "--version") == 0) {
        puts(version);
        return 0;
    }
    const char *log = getenv("FREAK_V35_TEST_CLANG_LOG");
    if (log) {
#ifdef _WIN32
        wchar_t *wide_log = wide_environment(L"FREAK_V35_TEST_CLANG_LOG");
        FILE *out = wide_log ? _wfopen(wide_log, L"ab") : NULL;
        free(wide_log);
#else
        FILE *out = fopen(log, "ab");
#endif
        if (!out) return 91;
        fputs("compile\n", out);
        fclose(out);
    }
    const char *broken = getenv("FREAK_V35_TEST_BROKEN_CLANG");
    if (broken && strcmp(broken, "1") == 0) return 42;
#ifdef _WIN32
    /* Keep the first hop's CRT parsing while recovering its Unicode values. */
    if (_configure_wide_argv(_crt_argv_unexpanded_arguments) != 0) return 94;
    int count = *__p___argc();
    wchar_t **arguments = *__p___wargv();
    if (count != argc || count < 1 || !arguments) return 95;
    wchar_t *wide_compiler = wide_environment(L"FREAK_V35_TEST_REAL_CLANG");
    if (!wide_compiler) return 90;
    wchar_t *original_argv0 = arguments[0];
    arguments[0] = wide_compiler;
    int result = forward_spawn(wide_compiler, count, arguments);
    arguments[0] = original_argv0;
    free(wide_compiler);
    return result;
#else
    argv[0] = (char *)compiler;
    execv(compiler, argv);
    perror("execv real Clang");
    return 92;
#endif
}
'''


WINDOWS_FORWARD_RECEIVER = r'''#include <stdio.h>
#include <stdlib.h>
#include <corecrt_startup.h>
#include <windows.h>
int main(void) {
    if(_configure_wide_argv(_crt_argv_unexpanded_arguments)!=0)return 90;
    int count=*__p___argc(); wchar_t **arguments=*__p___wargv();
    if(count<1||!arguments)return 91;
    puts("FREAK-V35-CLI-FORWARD-ARGV-1");printf("%d\n",count);
    for(int i=0;i<count;i++) {
        if(!arguments[i])return 92;
        int size=WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,arguments[i],-1,NULL,0,NULL,NULL);
        if(size<1)return 93;
        unsigned char *bytes=malloc((size_t)size);
        if(!bytes)return 94;
        if(WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,arguments[i],-1,(char *)bytes,size,NULL,NULL)!=size){free(bytes);return 93;}
        printf("%d:",size-1);
        for(int j=0;j<size-1;j++)printf("%02x",bytes[j]);
        putchar('\n');free(bytes);
    }
    if(fflush(stdout)!=0)return 95;
    return 23;
}
'''

def run(command: list[str], cwd: Path, env: dict[str, str], *,
        input_text: str | None = None, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, env=env, input=input_text,
                          capture_output=True, text=True, encoding="utf-8",
                          errors="strict", timeout=timeout, check=False)


def check_argv(output: subprocess.CompletedProcess[str], arguments: list[str], *,
               exit_code: int = 0) -> None:
    evidence = output.stdout + output.stderr
    assert output.returncode == exit_code, evidence
    prefix = "FREAK_ARGV_BEGIN\n"
    suffix = "FREAK_ARGV_END\n"
    assert output.stdout.count(prefix) == 1, evidence
    assert output.stdout.count(suffix) == 1, evidence
    observed = output.stdout.split(prefix, 1)[1].split(suffix, 1)[0]
    expected = "".join(f"{len(argument.encode('utf-8'))}:{argument}\n"
                       for argument in arguments)
    assert observed == expected, (observed, expected, evidence)


def check_terminal_input(command: list[str], cwd: Path, env: dict[str, str], *,
                         interrupt: bool = False) -> None:
    """Give the CLI a controlling terminal, where background reads get SIGTTIN."""
    import errno
    import pty
    import select
    import signal
    import time

    pid, terminal = pty.fork()
    if pid == 0:
        os.chdir(cwd)
        os.execve(command[0], command, env)
    output = bytearray()
    status = None
    sent = False
    deadline = time.monotonic() + 30
    try:
        while status is None and time.monotonic() < deadline:
            if select.select([terminal], [], [], 0.1)[0]:
                try:
                    chunk = os.read(terminal, 4096)
                except OSError as error:
                    if error.errno != errno.EIO:
                        raise
                    chunk = b""
                output.extend(chunk)
                assert len(output) < 1024 * 1024, "PTY fixture output exceeded 1 MiB"
                if not sent and b"FREAK_ARGV_END" in output:
                    os.write(terminal, b"\x03" if interrupt else b"tty stdin\n")
                    sent = True
            waited, child_status = os.waitpid(pid, os.WNOHANG)
            if waited:
                status = child_status
        assert status is not None, f"controlling-terminal input hung; CLI PID {pid}: {output!r}"
        while select.select([terminal], [], [], 0)[0]:
            try:
                chunk = os.read(terminal, 4096)
            except OSError as error:
                if error.errno != errno.EIO:
                    raise
                break
            if not chunk:
                break
            output.extend(chunk)
        rendered = output.decode("utf-8").replace("\r\n", "\n")
        assert os.waitstatus_to_exitcode(status) == (130 if interrupt else 0), rendered
        assert sent, rendered
        if not interrupt:
            assert "INPUT=tty stdin\n" in rendered, rendered
    finally:
        if status is None:
            # Stop only descendants of this recorded PTY launcher. The runtime
            # may own separate process groups, so killing one group is not enough.
            snapshot = subprocess.run(["ps", "-eo", "pid=,ppid="], capture_output=True,
                                      text=True, timeout=5, check=True)
            edges = [tuple(map(int, line.split())) for line in snapshot.stdout.splitlines()]
            descendants = {pid}
            previous_count = 0
            while previous_count != len(descendants):
                previous_count = len(descendants)
                descendants.update(child for child, parent in edges if parent in descendants)
            for target in sorted(descendants, reverse=True):
                try:
                    os.kill(target, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            os.waitpid(pid, 0)
        os.close(terminal)


def check_run(freak: Path, root: Path, env: dict[str, str]) -> None:
    sentinel = root / "shell-command-must-not-run"
    arguments = ["", "two words", 'double"quote', "single'quote", "trailing\\",
                 "--opt=not-a-cli-option", "--", "+03", "café🙂", "line\nbreak",
                 "tab\there", "&", "|", ">", "%PATH%", "!VAR!",
                 f"; touch {sentinel}", f"$(touch {sentinel})",
                 f"`touch {sentinel}`"]
    for backend in ("c", "llvm"):
        source = root / f"argv {backend}.fk"
        source.write_text(ARGV_PROGRAM, encoding="utf-8")
        command = [str(freak), "run", str(source), f"--{backend}", "--opt=0"]
        first = run(command + ["--", *arguments], root, env)
        check_argv(first, arguments)
        assert not sentinel.exists(), "program arguments executed as shell text"

        changed = ["different arguments", "", "--c"]
        second = run(command + ["--", *changed], root, env)
        check_argv(second, changed)
        assert "run cache hit" in second.stdout, second.stdout + second.stderr

        check_argv(run(command, root, env), [])
        check_argv(run(command + ["--"], root, env), [])

        exit_env = env.copy()
        exit_env["FREAK_V35_TEST_EXIT"] = "23"
        check_argv(run(command + ["--", "exit status"], root, exit_env),
                   ["exit status"], exit_code=23)

        input_env = env.copy()
        input_env["FREAK_V35_TEST_INPUT"] = "1"
        interactive = run(command + ["--", "stdin"], root, input_env,
                          input_text="inherited stdin\n")
        check_argv(interactive, ["stdin"])
        assert "INPUT=inherited stdin\n" in interactive.stdout, interactive.stdout
        if os.name == "posix":
            check_terminal_input(command + ["--", "terminal"], root, input_env)
            check_terminal_input(command + ["--", "terminal interrupt"], root,
                                 input_env, interrupt=True)

        rejected = run(command + ["requires delimiter"], root, env)
        assert rejected.returncode != 0, rejected.stdout + rejected.stderr
        assert "unknown or malformed flag" in rejected.stdout, rejected.stdout
        assert "FREAK_ARGV_BEGIN" not in rejected.stdout, rejected.stdout
        for subcommand in ("build", "check", "transpile"):
            rejected = run([str(freak), subcommand, str(source), "--", "argument"],
                           root, env)
            assert rejected.returncode != 0, rejected.stdout + rejected.stderr
            assert "unknown or malformed flag" in rejected.stdout, rejected.stdout
        relative = run([str(freak), "run", source.name, f"--{backend}", "--opt=0",
                        "--", "relative executable"], root, env)
        check_argv(relative, ["relative executable"])
        print(f"argv/{backend}: exact forwarding, cache, exit status, stdin, delimiter OK",
              flush=True)


def check_windows_forwarder(clang: Path, wrapper: Path, wrapper_source: Path,
                            root: Path, env: dict[str, str]) -> None:
    """Observe the actual CRT argv after each native test-wrapper second hop."""
    receiver_source = root / "forward-receiver.c"
    receiver_source.write_text(WINDOWS_FORWARD_RECEIVER, encoding="utf-8")
    receiver = root / "receiver é 日本 🙂.exe"
    wide_control = root / "unquoted wide forwarder.exe"
    narrow_source = root / "original-narrow-forwarder.c"
    narrow_source.write_text(CLANG_WRAPPER_NARROW_BASELINE, encoding="utf-8")
    narrow_control = root / "original narrow forwarder.exe"
    records = []

    def observed(command: list[str], selected: dict[str, str]) -> subprocess.CompletedProcess[str]:
        result = run(command, root, selected)
        records.append({"argv": command, "exit": result.returncode,
                        "stdout": result.stdout, "stderr": result.stderr})
        return result

    for command in ([str(clang), str(receiver_source), "-o", str(receiver)],
                    [str(clang), "-DFREAK_V35_CLI_TEST_UNQUOTED_FORWARD=1",
                     str(wrapper_source), "-o", str(wide_control)],
                    [str(clang), str(narrow_source), "-o", str(narrow_control)]):
        built = observed(command, env)
        assert built.returncode == 0, built.stdout + built.stderr

    def arguments(result: subprocess.CompletedProcess[str]) -> list[bytes]:
        assert result.returncode == 23 and result.stderr == "", records
        lines = result.stdout.splitlines()
        assert len(lines) >= 2 and lines[0] == "FREAK-V35-CLI-FORWARD-ARGV-1", records
        count = int(lines[1])
        assert count >= 1 and len(lines) == count + 2, records
        values = []
        for line in lines[2:]:
            length, encoded = line.split(":", 1)
            value = bytes.fromhex(encoded)
            assert len(encoded) == int(length) * 2 and len(value) == int(length), records
            values.append(value)
        return values

    forwarded = ["", "two words", "tab\there", "é日本🙂", '"quoted"', "tail\\",
                 "two\\\\", 'slash\\"quote', "' $ & %PATH% ; |", "*?literal"]
    selected = env.copy()
    selected.update(FREAK_V35_TEST_REAL_CLANG=str(receiver),
                    FREAK_V35_TEST_VERSION="forwarding witness")
    selected.pop("FREAK_V35_TEST_BROKEN_CLANG", None)
    selected.pop("FREAK_V35_TEST_CLANG_LOG", None)
    expected = [value.encode("utf-8") for value in (str(receiver), *forwarded)]
    fixed = arguments(observed([str(wrapper), *forwarded], selected))
    assert fixed == expected, (fixed, expected, records)
    unquoted_wide = arguments(observed([str(wide_control), *forwarded], selected))
    assert unquoted_wide != expected, "unquoted wide spawn unexpectedly preserved every argument"

    # A relative ASCII executable spelling keeps this exact old narrow-source
    # control independent of the directory's Windows codepage or Unicode name.
    ascii_receiver = root / "narrow receiver.exe"
    shutil.copy2(receiver, ascii_receiver)
    ascii_executable = r".\narrow receiver.exe"
    ascii_arguments = [value for value in forwarded if value.isascii()]
    selected["FREAK_V35_TEST_REAL_CLANG"] = ascii_executable
    narrow_expected = [value.encode("ascii") for value in (ascii_executable, *ascii_arguments)]
    unquoted_narrow = arguments(observed([str(narrow_control), *ascii_arguments], selected))
    assert unquoted_narrow != narrow_expected, "original narrow spawn unexpectedly preserved every argument"
    report = {"status": "pass", "scope": "native test-wrapper second-hop CRT argv including argv0",
              "fixed_arguments_hex": [value.hex() for value in fixed],
              "wide_joining_control_arguments_hex": [value.hex() for value in unquoted_wide],
              "original_narrow_ascii_expected_hex": [value.hex() for value in narrow_expected],
              "original_narrow_ascii_arguments_hex": [value.hex() for value in unquoted_narrow],
              "sources_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in (receiver_source, wrapper_source, narrow_source)},
              "binaries_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                  for path in (clang, receiver, wrapper, wide_control, narrow_control)},
              "commands": records}
    print("windows/forwarder: " + json.dumps(report, ensure_ascii=True), flush=True)


def check_doctor(freak: Path, clang: Path, root: Path, env: dict[str, str]) -> None:
    source = root / "clang-wrapper.c"
    wrapper = root / ("clang wrapper.exe" if os.name == "nt" else "clang wrapper")
    source.write_text(CLANG_WRAPPER, encoding="utf-8")
    built = run([str(clang), str(source), "-o", str(wrapper)], root, env)
    assert built.returncode == 0, built.stdout + built.stderr
    if os.name != "nt":
        wrapper.chmod(0o700)
    if os.name == "nt":
        check_windows_forwarder(clang, wrapper, source, root, env)

    actual = run([str(freak), "doctor", "--json"], root, env)
    assert actual.returncode == 0, actual.stdout + actual.stderr
    actual_clang = json.loads(actual.stdout)["checks"]["clang"]
    assert actual_clang["ok"] and actual_clang["version_ok"], actual_clang
    assert actual_clang["probe_ok"], actual_clang
    minimum = actual_clang["minimum_major"]
    assert isinstance(minimum, int) and minimum > 0, actual_clang

    cases = [("minimum", f"clang version {minimum}.0.0", True),
             ("old", f"clang version {minimum - 1}.9.9", False),
             ("new", f"Ubuntu clang version {minimum + 1}.0.0", True),
             ("apple", "Apple clang version 15.0.0 (clang-1500.0.40.1)", True),
             ("apple-old", "Apple clang version 14.0.0 (clang-1400.0.29.202)", False),
             ("unknown", "mystery compiler version 99.0.0", False),
             ("unknown-tab", "mystery\tcompiler version 99.0.0", False),
             ("unknown-controls", "mystery" + "".join(chr(value) for value in range(1, 32)
                                                       if value not in (10, 13)) + " version 99.0.0", False),
             ("empty", "", False),
             ("malformed", "clang version nonsense 99.0.0", False),
             ("overflow", "clang version 99999999999999999999.0.0", False)]
    for name, version, expected in cases:
        case_env = env.copy()
        case_env.update(FREAK_CLANG=str(wrapper),
                        FREAK_V35_TEST_REAL_CLANG=str(clang),
                        FREAK_V35_TEST_VERSION=version)
        checked = run([str(freak), "doctor", "--json"], root, case_env)
        report = json.loads(checked.stdout)
        check = report["checks"]["clang"]
        assert check["executable"] == str(wrapper), check
        assert check["version"] == version, check
        assert check["version_ok"] is expected and check["ok"] is expected, check
        assert checked.returncode == (0 if expected else 1), checked.stdout + checked.stderr
        human = run([str(freak), "doctor"], root, case_env)
        assert human.returncode == (0 if expected else 1), human.stdout + human.stderr
        assert "Minimum supported Clang" in human.stdout, human.stdout
        if name.startswith("apple"):
            assert check["vendor"] == "apple" and check["minimum_major"] == 15, check
        if name in ("old", "apple-old"):
            assert "older than the supported minimum" in human.stdout, human.stdout
        print(f"doctor/{name}: version and exit status OK", flush=True)

    broken_env = env.copy()
    broken_env.update(FREAK_CLANG=str(wrapper),
                      FREAK_V35_TEST_REAL_CLANG=str(clang),
                      FREAK_V35_TEST_VERSION=f"clang version {minimum}.0.0",
                      FREAK_V35_TEST_BROKEN_CLANG="1")
    broken = run([str(freak), "doctor", "--json"], root, broken_env)
    check = json.loads(broken.stdout)["checks"]["clang"]
    assert broken.returncode == 1 and check["version_ok"] and not check["probe_ok"], check
    assert not check["ok"], check
    assert not list(root.glob("freak-doctor-*-probe-*")), "Doctor retained probe artifacts"
    print("doctor/probe: --version success cannot mask compile/link failure OK", flush=True)

    missing_tool = root / "explicit missing Clang"
    missing_env = env.copy()
    missing_env["FREAK_CLANG"] = str(missing_tool)
    missing = run([str(freak), "doctor", "--json"], root, missing_env)
    check = json.loads(missing.stdout)["checks"]["clang"]
    assert missing.returncode == 1 and check["executable"] == str(missing_tool), check
    assert not check["ok"] and not check["version_ok"] and not check["probe_ok"], check
    print("doctor/override: missing explicit executable never falls back OK", flush=True)

    if os.name == "posix":
        # A distro may install only a versioned driver. Keep bare clang and
        # newer drivers out of PATH so discovery must find its declared floor.
        isolated_path = root / "only clang-15"
        isolated_path.mkdir()
        shutil.copy2(wrapper, isolated_path / "clang-15")
        # od/tr are the current installed payload-marker transport. Keep them
        # while isolating driver discovery; they do not provide another Clang.
        for tool in ("uname", "mkdir", "rm", "ld", "as", "od", "tr"):
            executable = shutil.which(tool, path=env.get("PATH"))
            assert executable, f"fixture tool missing: {tool}"
            (isolated_path / tool).symlink_to(Path(executable).resolve())
        discovery_env = env.copy()
        discovery_env.pop("FREAK_CLANG", None)
        discovery_env.update(PATH=str(isolated_path),
                             FREAK_V35_TEST_REAL_CLANG=str(clang),
                             FREAK_V35_TEST_VERSION=f"clang version {minimum}.0.0")
        discovered = run([str(freak), "doctor", "--json"], root, discovery_env)
        check = json.loads(discovered.stdout)["checks"]["clang"]
        assert discovered.returncode == 0 and check["ok"], discovered.stdout + discovered.stderr
        assert check["command"] == "clang-15", check
        print("doctor/discovery: versioned minimum-only PATH OK", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("freak", type=Path, help="native CLI candidate; never rebuilt")
    parser.add_argument("--clang", type=Path, required=True,
                        help="exact native Clang used for fixture builds")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--section", choices=("all", "run", "doctor"), default="all")
    args = parser.parse_args()
    freak, clang, repo = args.freak.resolve(), args.clang.resolve(), args.repo.resolve()
    assert freak.is_file() and clang.is_file(), "native candidate and Clang are required"
    with tempfile.TemporaryDirectory(prefix="freak-v35-cli-") as temporary:
        root = Path(temporary)
        home = root / "payload"
        for source, destination in manifest_entries(repo):
            if not destination.startswith(("runtime/", "templates/v35/")):
                continue
            target = home / destination
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        shutil.copytree(repo / "std", home / "std")
        env = os.environ.copy()
        for name in tuple(env):
            if name.startswith(("FREAK_DOCTOR_TEST_", "FREAK_V35_TEST_")):
                del env[name]
        env.update(FREAK_HOME=str(home), FREAK_CLANG=str(clang), TMPDIR=str(root),
                   TEMP=str(root), TMP=str(root))
        if args.section in ("all", "run"):
            check_run(freak, root, env)
        if args.section in ("all", "doctor"):
            check_doctor(freak, clang, root, env)
    print("V3.5 CLI: OK", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
