#!/usr/bin/env python3
"""Prove repeated V3 word replacement releases superseded allocations."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


PROGRAM = """task identity(value: word) -> word {
    give back value
}

task observe(value: word) {
    pilot length = value.length()
}

task measure(value: word) -> int {
    give back value.length()
}

pilot mut global_owner: word = "g" + "lobal"
pilot mut global_alias: word = global_owner

task main() {
    pilot mut text: word = "a"
    repeat 512 times {
        text = text + "x"
    }
    text = text
    text = "done"
    say text
    pilot mut moved: word = "x" + "y"
    pilot mut alias: word = moved
    moved = "z"
    say alias
    alias = "released"
    pilot mut called: word = "c" + "all"
    pilot mut returned: word = identity(called)
    called = "reinitialized"
    say returned
    returned = "released"
    pilot mut measured_word: word = "m" + "easure"
    pilot measured = measure(measured_word)
    if measured != 7 { say "bad measure" }
    measured_word = "released"
    pilot mut observed: word = "o" + "bserve"
    repeat 128 times {
        observe(observed)
    }
    observed = "released"
    global_owner = "reinitialized"
    say global_alias
    global_alias = "released"
}
"""

GLOBAL_RETURN_PROGRAM = """pilot mut global_owner: word = "g" + "lobal"

task get_global_owner() -> word {
    give back global_owner
}

task main() {
    pilot mut returned_global: word = get_global_owner()
    global_owner = "reinitialized"
    say returned_global
    returned_global = "released"
}
"""


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("freak", type=Path)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    freak = args.freak.resolve()
    assert freak.is_file(), freak

    with tempfile.TemporaryDirectory(prefix="freak-v3-word-ownership-") as tmp:
        root = Path(tmp)
        cases = (
            ("strict", PROGRAM, ["--strict-borrow"], ["done", "xy", "call", "global"]),
            ("global_return", GLOBAL_RETURN_PROGRAM, [], ["global"]),
        )
        for case_name, program, extra_flags, expected_output in cases:
            source = root / f"replace_owned_{case_name}.fk"
            source.write_text(program, encoding="utf-8")
            for backend, flag, suffix in (("c", "--c", ".c"), ("llvm", "--llvm", ".ll")):
                transpiled = run([str(freak), "transpile", str(source), flag, *extra_flags], repo)
                assert transpiled.returncode == 0, transpiled.stdout + transpiled.stderr
                generated = Path(str(source) + suffix)
                assert generated.is_file(), generated
                generated_text = generated.read_text(encoding="utf-8")
                if backend == "c":
                    assert "freak_word_replace_owned" in generated_text
                    if case_name == "strict":
                        assert "freak_word_clone(moved)" in generated_text
                        assert "value = freak_word_clone(value)" in generated_text
                        assert "global_alias = freak_word_clone(global_owner)" in generated_text
                        assert "freak_word_release_owned(&value)" in generated_text
                    else:
                        assert "__freak_return_value = freak_word_clone(global_owner)" in generated_text
                else:
                    assert "@freak_llvm_word_release_replaced" in generated_text
                    assert "@freak_llvm_word_clone" in generated_text

                binary = root / (f"replace_owned_{case_name}_{backend}.exe" if sys.platform == "win32" else f"replace_owned_{case_name}_{backend}")
                if sys.platform == "win32":
                    built = run([str(freak), "build", str(source), flag, *extra_flags], repo)
                    assert built.returncode == 0, built.stdout + built.stderr
                    produced = source.with_suffix(".exe")
                    shutil.copy2(produced, binary)
                else:
                    clang = os.environ.get("FREAK_CLANG") or shutil.which("clang")
                    assert clang, "clang is required for the ownership sanitizer regression"
                    command = [
                        clang,
                        "-g",
                        "-O1",
                        "-fsanitize=address",
                        "-fno-omit-frame-pointer",
                        "-o",
                        str(binary),
                        str(generated),
                    ]
                    if backend == "llvm":
                        command.extend(
                            [
                                str(repo / "freakc" / "runtime" / "freak_llvm_runtime.c"),
                                str(repo / "freakc" / "runtime" / "freak_runtime.c"),
                            ]
                        )
                    else:
                        command.append(str(repo / "freakc" / "runtime" / "freak_runtime.c"))
                    command.extend(["-I", str(repo / "freakc" / "runtime"), "-lm"])
                    compiled = run(command, repo)
                    assert compiled.returncode == 0, compiled.stdout + compiled.stderr

                sanitizer_env = os.environ.copy()
                sanitizer_env["ASAN_OPTIONS"] = "halt_on_error=1"
                if sys.platform.startswith("linux"):
                    sanitizer_env["ASAN_OPTIONS"] += ":detect_leaks=1"
                    sanitizer_env["LSAN_OPTIONS"] = "exitcode=23"
                executed = run([str(binary)], root, sanitizer_env)
                assert executed.returncode == 0, executed.stdout + executed.stderr
                assert executed.stdout.strip().splitlines() == expected_output, executed.stdout
                assert "LeakSanitizer" not in executed.stderr

    print("V3 word replacement ownership: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
