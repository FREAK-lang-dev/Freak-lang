#!/usr/bin/env python3
"""Prove the shipping V3 compiler reaches a clean C self-host fixed point."""

from __future__ import annotations

import hashlib
import os
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


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repository_fingerprint(repo: Path) -> dict[str, str]:
    listed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repo,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert listed.returncode == 0, listed.stderr.decode("utf-8", errors="replace")
    relative_paths = listed.stdout.decode("utf-8").split("\0")
    return {
        relative: digest(repo / relative)
        for relative in relative_paths
        if relative
    }


def run(command: list[str], cwd: Path, env: dict[str, str]) -> None:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        check=False,
    )
    if result.returncode != 0:
        rendered = " ".join(command)
        raise AssertionError(
            f"command failed ({result.returncode}): {rendered}\n"
            f"{result.stdout}{result.stderr}"
        )


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    runtime_dir = repo / "freakc" / "runtime"
    runtime_c = runtime_dir / "freak_runtime.c"
    seed_c = repo / "build" / "freakc_v3.fk.c"
    compiler_sources = [repo / source for source in COMPILER_SOURCES]
    inputs = list(compiler_sources)
    inputs.extend((seed_c, runtime_c, runtime_dir / "freak_runtime.h"))
    assert all(path.is_file() for path in inputs), "V3 fixed-point input is missing"
    before = repository_fingerprint(repo)

    compiler_bytes = b"".join(path.read_bytes() for path in compiler_sources)
    assert b"<<PIPE>>" not in compiler_bytes, (
        "V3 compiler source still contains the lossy string-literal sentinel"
    )

    configured_clang = os.environ.get("FREAK_CLANG", "clang")
    clang = shutil.which(configured_clang)
    assert clang is not None, f"Clang not found: {configured_clang}"
    executable_suffix = ".exe" if sys.platform == "win32" else ""
    link_flags = ["-lws2_32"] if sys.platform == "win32" else []
    if sys.platform.startswith("linux"):
        link_flags.append("-lm")
    common_flags = [
        "-O2",
        "-w",
        "-D_CRT_SECURE_NO_WARNINGS",
        f"-I{runtime_dir}",
        *link_flags,
    ]
    env = os.environ.copy()
    env["NO_COLOR"] = "1"

    with tempfile.TemporaryDirectory(prefix="freak-v3-fixed-point-") as temporary:
        root = Path(temporary)
        aggregate = root / "freakc_v3.fk"
        aggregate.write_bytes(compiler_bytes)
        seed = root / f"freakc-seed{executable_suffix}"
        run(
            [clang, "-o", str(seed), str(seed_c), str(runtime_c), *common_flags],
            root,
            env,
        )

        previous = seed
        generated_hashes: list[str] = []
        generations: list[Path] = []
        for generation in range(1, 4):
            run([str(previous), str(aggregate), "--c"], root, env)
            emitted = Path(str(aggregate) + ".c")
            assert emitted.is_file(), f"generation {generation} emitted no C"
            generation_c = root / f"freakc-stage{generation}.c"
            shutil.copyfile(emitted, generation_c)
            generations.append(generation_c)
            generated_hashes.append(digest(generation_c))
            if generation <= 2:
                compiler = root / f"freakc-stage{generation}{executable_suffix}"
                run(
                    [
                        clang,
                        "-o",
                        str(compiler),
                        str(generation_c),
                        str(runtime_c),
                        *common_flags,
                    ],
                    root,
                    env,
                )
                previous = compiler

        assert generations[1].read_bytes() == generations[2].read_bytes(), (
            "V3 self-host fixed point failed: generation 2 and generation 3 "
            f"differ ({generated_hashes[1]} != {generated_hashes[2]})"
        )

    after = repository_fingerprint(repo)
    assert after == before, "V3 fixed-point reconstruction modified tracked repository files"
    print(f"V3 generation 1 C: {generated_hashes[0]}")
    print(f"V3 generation 2 C: {generated_hashes[1]}")
    print(f"V3 generation 3 C: {generated_hashes[2]}")
    print("V3 self-host fixed point: PASS (generation 2 == generation 3)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
