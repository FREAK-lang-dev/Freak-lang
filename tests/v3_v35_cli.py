#!/usr/bin/env python3
"""Exercise V3.5 CLI argv forwarding and Doctor with a supplied native candidate.

This harness never builds a compiler or invokes a Python compiler fallback.
The supplied candidate and --repo payload must come from the same revision.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


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

CLANG_WRAPPER = r'''#include <stdio.h>
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

        rejected = run(command + ["requires delimiter"], root, env)
        assert rejected.returncode != 0, rejected.stdout + rejected.stderr
        assert "unknown or malformed flag" in rejected.stdout, rejected.stdout
        assert "FREAK_ARGV_BEGIN" not in rejected.stdout, rejected.stdout
        for subcommand in ("build", "check", "transpile"):
            rejected = run([str(freak), subcommand, str(source), "--", "argument"],
                           root, env)
            assert rejected.returncode != 0, rejected.stdout + rejected.stderr
            assert "unknown or malformed flag" in rejected.stdout, rejected.stdout
        print(f"argv/{backend}: exact forwarding, cache, exit status, stdin, delimiter OK",
              flush=True)


def check_doctor(freak: Path, clang: Path, root: Path, env: dict[str, str]) -> None:
    source = root / "clang-wrapper.c"
    wrapper = root / ("clang wrapper.exe" if os.name == "nt" else "clang wrapper")
    source.write_text(CLANG_WRAPPER, encoding="utf-8")
    built = run([str(clang), str(source), "-o", str(wrapper)], root, env)
    assert built.returncode == 0, built.stdout + built.stderr
    if os.name != "nt":
        wrapper.chmod(0o700)

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
        shutil.copytree(repo / "freakc" / "runtime", home / "runtime")
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
