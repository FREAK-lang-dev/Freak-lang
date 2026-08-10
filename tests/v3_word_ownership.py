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


PROGRAM = """task main() {
    pilot text: word = "a"
    repeat 512 times {
        text = text + "x"
    }
    text = text
    text = "done"
    say text
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
        source = root / "replace_owned.fk"
        source.write_text(PROGRAM, encoding="utf-8")

        for backend, flag, suffix in (("c", "--c", ".c"), ("llvm", "--llvm", ".ll")):
            transpiled = run([str(freak), "transpile", str(source), flag], repo)
            assert transpiled.returncode == 0, transpiled.stdout + transpiled.stderr
            generated = Path(str(source) + suffix)
            assert generated.is_file(), generated
            generated_text = generated.read_text(encoding="utf-8")
            if backend == "c":
                assert "freak_word_replace_owned" in generated_text
            else:
                assert "@freak_llvm_word_release_replaced" in generated_text

            binary = root / (f"replace_owned_{backend}.exe" if sys.platform == "win32" else f"replace_owned_{backend}")
            if sys.platform == "win32":
                built = run([str(freak), "build", str(source), flag], repo)
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
            assert executed.stdout.strip() == "done", executed.stdout
            assert "LeakSanitizer" not in executed.stderr

    print("V3 word replacement ownership: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
