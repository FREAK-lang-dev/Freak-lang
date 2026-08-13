#!/usr/bin/env python3
"""V3 native CLI build-profile, LTO, and cache-freshness contracts."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ANSI = re.compile(r"\x1b\[[0-9;]*m")


def invoke(
    freak: Path,
    cwd: Path,
    args: list[str],
    env: dict[str, str],
    *,
    timeout: int = 180,
) -> tuple[int, str]:
    completed = subprocess.run(
        [str(freak), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    return completed.returncode, ANSI.sub("", completed.stdout + completed.stderr)


def selected_clang(freak: Path, cwd: Path, env: dict[str, str]) -> str:
    code, output = invoke(freak, cwd, ["doctor", "--json"], env)
    assert code == 0, output
    document = json.loads(output)
    clang = document["checks"]["clang"]
    assert clang["ok"] is True, output
    command = clang["command"]
    if len(command) >= 2 and command.startswith('"') and command.endswith('"'):
        command = command[1:-1]
    resolved = shutil.which(command)
    if resolved:
        return resolved
    assert Path(command).is_file(), command
    return command


def write_recorder(root: Path, real_clang: str) -> tuple[Path, Path]:
    recorder = root / "record_clang.py"
    log = root / "clang-arguments.jsonl"
    recorder.write_text(
        """import json
import os
import subprocess
import sys
from pathlib import Path

args = sys.argv[1:]
with Path(os.environ["FREAK_PROFILE_CLANG_LOG"]).open("a", encoding="utf-8") as stream:
    stream.write(json.dumps(args) + "\\n")
if args == ["-dumpmachine"] and os.environ.get("FREAK_PROFILE_FAKE_TARGET"):
    print(os.environ["FREAK_PROFILE_FAKE_TARGET"])
    raise SystemExit(0)
if os.environ.get("FREAK_PROFILE_REJECT_LTO") == "1" and any(
    arg.startswith("-flto=") for arg in args
):
    print("recording clang: LTO deliberately unsupported", file=sys.stderr)
    raise SystemExit(86)
raise SystemExit(subprocess.run([os.environ["FREAK_PROFILE_REAL_CLANG"], *args]).returncode)
""",
        encoding="utf-8",
    )
    if sys.platform == "win32":
        wrapper = root / "record-clang.cmd"
        wrapper.write_text(
            f'@"{sys.executable}" "{recorder}" %*\n', encoding="utf-8"
        )
    else:
        wrapper = root / "record-clang"
        wrapper.write_text(
            f'#!/bin/sh\nexec "{sys.executable}" "{recorder}" "$@"\n',
            encoding="utf-8",
        )
        wrapper.chmod(0o755)
    assert Path(real_clang).is_file(), real_clang
    return wrapper, log


def read_log(log: Path) -> list[list[str]]:
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]


def compile_entries(log: Path) -> list[list[str]]:
    return [
        args
        for args in read_log(log)
        if "--version" not in args
        and "-dumpmachine" not in args
        and not any("print-prog-name" in arg for arg in args)
    ]


def binary_path(source: Path) -> Path:
    return source.with_suffix(".exe" if sys.platform == "win32" else "")


def assert_binary(binary: Path, marker: str) -> None:
    completed = subprocess.run(
        [str(binary.resolve())],
        cwd=binary.parent,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert marker in completed.stdout, completed.stdout + completed.stderr


def check_static_contract(repo: Path) -> None:
    main = (repo / "src" / "cli" / "main.fk").read_text(encoding="utf-8")
    build = (repo / "src" / "cli" / "build.fk").read_text(encoding="utf-8")
    run = (repo / "src" / "cli" / "run.fk").read_text(encoding="utf-8")
    help_text = (repo / "src" / "cli" / "version.fk").read_text(encoding="utf-8")

    for needle in (
        'profile = "plus03"',
        'opt = "3"',
        'runtime_policy = "plus03"',
        'if lto_seen == "" { lto = "thin" }',
        'cli_flag_error("unknown or malformed flag " + flag)',
        'cli_flag_error("+03 cannot be combined with --opt")',
        'cli_flag_error("+03 cannot disable LTO")',
        'cli_flag_error("LTO is not supported with --target; use --lto=off")',
    ):
        assert needle in main, f"profile parser missing {needle}"
    for needle in (
        'give back " -flto=thin"',
        'give back " -flto=full"',
        'give back " -fuse-ld=lld"',
        'give back " -fuse-ld=ld"',
        "task cli_clang_target_triple",
        "task cli_linker_program_name",
        'give back "lld-link.exe"',
        'give back "ld.lld.exe"',
        'give back "link.exe"',
        'lto == "off" and runtime_obj_ext != ""',
        'profile_label = "+03 — FINAL FORM"',
        "No non-LTO fallback was attempted",
    ):
        assert needle in build, f"build profile contract missing {needle}"
    for forbidden in ("-Ofast", "-ffast-math", "-march=native"):
        assert forbidden not in build, f"unsafe optimization flag present: {forbidden}"
    for needle in (
        'CLI_RUN_CACHE_SCHEMA = "freak-run-cache-v5"',
        '"|target=" + target + "|profile=" + profile + "|clang-opt=" + opt + "|lto=" + lto',
        '"|runtime-policy=" + runtime_policy + "|runtime-stats=" + runtime_stats',
        '"|linker=" + cli_run_linker_identity',
        '"|link-plan=" + link_plan',
    ):
        assert needle in run, f"run cache contract missing {needle}"
    assert "+03 — FINAL FORM" in help_text
    assert "--lto[=MODE]" in help_text


def assert_invalid_preserves_artifacts(
    freak: Path,
    root: Path,
    source: Path,
    flags: list[str],
    env: dict[str, str],
    *,
    command: str = "build",
) -> None:
    artifacts = [
        binary_path(source),
        Path(str(source) + ".c"),
        Path(str(source) + ".ll"),
        source.with_suffix(".obj"),
        Path(str(binary_path(source)) + ".freak-run-cache"),
    ]
    expected: dict[Path, bytes] = {}
    for index, artifact in enumerate(artifacts):
        payload = f"sentinel-{command}-{index}\n".encode()
        artifact.write_bytes(payload)
        expected[artifact] = payload
    code, output = invoke(freak, root, [command, str(source), *flags], env)
    assert code != 0, output
    for artifact, payload in expected.items():
        assert artifact.read_bytes() == payload, (
            f"invalid flags mutated {artifact} for {command} {' '.join(flags)}\n{output}"
        )


def build_and_record(
    freak: Path,
    root: Path,
    source: Path,
    flags: list[str],
    env: dict[str, str],
    log: Path,
) -> tuple[str, list[list[str]]]:
    log.unlink(missing_ok=True)
    code, output = invoke(freak, root, ["build", str(source), *flags], env)
    assert code == 0, output
    assert_binary(binary_path(source), "PROFILE_MATRIX_OK")
    entries = compile_entries(log)
    assert entries, f"recording Clang saw no compilation for {' '.join(flags)}\n{output}"
    flattened = [arg for entry in entries for arg in entry]
    for forbidden in ("-Ofast", "-ffast-math", "-march=native"):
        assert forbidden not in flattened, (forbidden, entries)
    return output, entries


def check_real_profile_matrix(
    freak: Path,
    root: Path,
    env: dict[str, str],
    log: Path,
    native_target: str,
) -> None:
    source = root / "profile-matrix.fk"
    source.write_text('say "PROFILE_MATRIX_OK"\n', encoding="utf-8")
    for backend in ("--c", "--llvm"):
        for level in range(4):
            output, entries = build_and_record(
                freak,
                root,
                source,
                [backend, f"--opt={level}", "--lto=off"],
                env,
                log,
            )
            assert f"Profile: O{level}" in output, output
            flattened = [arg for entry in entries for arg in entry]
            assert f"-O{level}" in flattened, entries
            assert not any(arg.startswith("-flto=") for arg in flattened), entries

        output, entries = build_and_record(
            freak, root, source, [backend, "+03"], env, log
        )
        flattened = [arg for entry in entries for arg in entry]
        assert "+03 — FINAL FORM" in output, output
        assert "-O3" in flattened and "-flto=thin" in flattened, entries
        assert any(arg.endswith("freak_runtime.c") for arg in flattened), entries
        if backend == "--llvm":
            assert any(arg.endswith("freak_llvm_runtime.c") for arg in flattened), entries

        _, alias_entries = build_and_record(
            freak, root, source, [backend, "--opt=3", "--lto"], env, log
        )
        alias_flat = [arg for entry in alias_entries for arg in entry]
        assert "-flto=thin" in alias_flat, alias_entries

        _, full_entries = build_and_record(
            freak, root, source, [backend, "--opt=3", "--lto=full"], env, log
        )
        full_flat = [arg for entry in full_entries for arg in entry]
        assert "-O3" in full_flat and "-flto=full" in full_flat, full_entries

    _, cross_off_entries = build_and_record(
        freak,
        root,
        source,
        ["--c", "--opt=2", "--lto=off", f"--target={native_target}"],
        env,
        log,
    )
    cross_off_flat = [arg for entry in cross_off_entries for arg in entry]
    assert f"--target={native_target}" in cross_off_flat, cross_off_entries
    assert not any(arg.startswith("-flto=") for arg in cross_off_flat), cross_off_entries


def check_invalid_flags(
    freak: Path, root: Path, env: dict[str, str]
) -> None:
    source = root / "invalid-profile.fk"
    source.write_text('say "INVALID_MUST_NOT_RUN"\n', encoding="utf-8")
    invalid_builds = (
        ["--unknown"],
        ["--opt="],
        ["--opt=30"],
        ["--opt=4"],
        ["--opt=2", "--opt=3"],
        ["--c", "--llvm"],
        ["--lto=wat"],
        ["+03", "--opt=3"],
        ["+03", "--lto=off"],
        ["--target="],
        ["--target=x86_64;bad"],
        ["--c", "--unknown"],
        ["--llvm", "--unknown"],
        ["+03", "--target=x86_64-unknown-linux-gnu"],
        ["--lto", "--target=x86_64-unknown-linux-gnu"],
        ["--lto=full", "--target=x86_64-unknown-linux-gnu"],
    )
    for flags in invalid_builds:
        assert_invalid_preserves_artifacts(freak, root, source, list(flags), env)
    for command in ("check", "transpile"):
        for flags in (["+03"], ["--opt=3"], ["--lto"]):
            assert_invalid_preserves_artifacts(
                freak, root, source, list(flags), env, command=command
            )
    assert_invalid_preserves_artifacts(
        freak,
        root,
        source,
        ["+03", "--target=x86_64-unknown-linux-gnu"],
        env,
        command="run",
    )


def check_strict_transpile_compatibility(
    freak: Path, root: Path, env: dict[str, str]
) -> None:
    source = root / "strict-transpile.fk"
    source.write_text(
        "task main() -> int {\n"
        "    pilot counter = 0\n"
        "    counter = counter + 1\n"
        "    give back counter\n"
        "}\n"
        "main()\n",
        encoding="utf-8",
    )
    generated = Path(str(source) + ".c")
    invocations = (
        ["transpile", str(source), "--strict-borrow", "--c"],
        [str(source), "--strict-borrow", "--c"],
    )
    for args in invocations:
        generated.write_bytes(b"stale generated C\n")
        code, output = invoke(freak, root, args, env)
        assert code != 0, output
        assert "only valid for build" not in output, output
        assert "sworn to silence" in output.lower(), output
        assert not generated.exists(), (args, output)


def check_unsupported_lto(
    freak: Path,
    root: Path,
    env: dict[str, str],
    log: Path,
) -> None:
    source = root / "unsupported-lto.fk"
    source.write_text('say "NO_LTO_FALLBACK"\n', encoding="utf-8")
    binary = binary_path(source)
    binary.write_bytes(b"stale executable\n")
    log.unlink(missing_ok=True)
    rejecting_env = env.copy()
    rejecting_env["FREAK_PROFILE_REJECT_LTO"] = "1"
    code, output = invoke(
        freak, root, ["build", str(source), "--c", "+03"], rejecting_env
    )
    assert code != 0, output
    assert "LTO BUILD FAILED" in output and "No non-LTO fallback was attempted" in output
    assert not binary.exists(), "a rejected valid rebuild must not leave the stale binary"
    compiles = compile_entries(log)
    assert len(compiles) == 1, compiles
    assert "-flto=thin" in compiles[0], compiles


def assert_run_cache(
    freak: Path,
    root: Path,
    source: Path,
    flags: list[str],
    env: dict[str, str],
    *,
    hit: bool,
) -> None:
    code, output = invoke(freak, root, ["run", str(source), "--c", *flags], env)
    assert code == 0 and "CACHE_PROFILE_OK" in output, output
    assert ("run cache hit" in output) is hit, output


def check_cache_separation(
    freak: Path, root: Path, env: dict[str, str]
) -> None:
    source = root / "profile-cache.fk"
    source.write_text('say "CACHE_PROFILE_OK"\n', encoding="utf-8")
    binary = binary_path(source)

    assert_run_cache(freak, root, source, [], env, hit=False)
    assert_run_cache(freak, root, source, [], env, hit=True)
    binary.write_bytes(binary.read_bytes() + b"stale-tail")
    assert_run_cache(freak, root, source, [], env, hit=False)
    assert_run_cache(freak, root, source, ["--opt=3"], env, hit=False)
    assert_run_cache(freak, root, source, ["--opt=3"], env, hit=True)
    assert_run_cache(freak, root, source, ["--opt=3", "--lto"], env, hit=False)
    assert_run_cache(
        freak, root, source, ["--opt=3", "--lto=thin"], env, hit=True
    )
    assert_run_cache(freak, root, source, ["+03"], env, hit=False)
    assert_run_cache(freak, root, source, ["+03"], env, hit=True)
    assert_run_cache(freak, root, source, ["+03", "--lto=full"], env, hit=False)


def create_fake_linkers(root: Path, real_clang: str) -> dict[str, Path]:
    names = {
        "gnu": "ld.lld.exe" if sys.platform == "win32" else "ld.lld",
        "msvc_off": "link.exe" if sys.platform == "win32" else "link",
        "msvc_lto": "lld-link.exe" if sys.platform == "win32" else "lld-link",
    }
    programs: dict[str, Path] = {}
    for role, name in names.items():
        destination = root / name
        shutil.copy2(real_clang, destination)
        if sys.platform != "win32":
            destination.chmod(0o755)
        programs[role] = destination
    return programs


def mutate_fake_linker(path: Path, marker: str) -> None:
    with path.open("ab") as stream:
        stream.write(f"\nFREAK-LINKER-{marker}\n".encode())


def check_linker_identity_selection(
    freak: Path,
    root: Path,
    env: dict[str, str],
    log: Path,
    real_clang: str,
) -> None:
    source = root / "linker-cache.fk"
    source.write_text('say "CACHE_PROFILE_OK"\n', encoding="utf-8")
    programs = create_fake_linkers(root, real_clang)
    scenarios = (
        ("x86_64-w64-windows-gnu", [], "gnu", "msvc_off"),
        ("x86_64-pc-windows-msvc", [], "msvc_off", "gnu"),
        ("x86_64-w64-windows-gnu", ["--lto=thin"], "gnu", "msvc_lto"),
        ("x86_64-pc-windows-msvc", ["--lto=thin"], "msvc_lto", "gnu"),
    )
    controlled_env = env.copy()
    for index, (target, flags, selected_role, unrelated_role) in enumerate(scenarios):
        controlled_env["FREAK_PROFILE_FAKE_TARGET"] = target
        assert_run_cache(freak, root, source, flags, controlled_env, hit=False)
        assert_run_cache(freak, root, source, flags, controlled_env, hit=True)
        mutate_fake_linker(programs[unrelated_role], f"unrelated-{index}")
        assert_run_cache(freak, root, source, flags, controlled_env, hit=True)
        mutate_fake_linker(programs[selected_role], f"selected-{index}")
        assert_run_cache(freak, root, source, flags, controlled_env, hit=False)
    assert ["-dumpmachine"] in read_log(log), read_log(log)


def clang_target(real_clang: str) -> str:
    completed = subprocess.run(
        [real_clang, "-dumpmachine"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )
    target = completed.stdout.strip()
    assert completed.returncode == 0 and re.fullmatch(r"[A-Za-z0-9_.-]+", target), (
        completed.stdout + completed.stderr
    )
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("freak", type=Path)
    parser.add_argument("--clang", type=Path)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    freak = args.freak.resolve()
    assert freak.is_file(), f"FREAK CLI not found: {freak}"
    check_static_contract(repo)

    with tempfile.TemporaryDirectory(prefix="freak-v3-build-profiles-") as tmp:
        root = Path(tmp)
        base_env = os.environ.copy()
        real_clang = (
            str(args.clang.resolve())
            if args.clang is not None
            else selected_clang(freak, root, base_env)
        )
        wrapper, log = write_recorder(root, real_clang)
        env = base_env.copy()
        env["FREAK_CLANG"] = str(wrapper)
        env["FREAK_PROFILE_REAL_CLANG"] = real_clang
        env["FREAK_PROFILE_CLANG_LOG"] = str(log)

        check_invalid_flags(freak, root, env)
        check_strict_transpile_compatibility(freak, root, env)
        check_real_profile_matrix(freak, root, env, log, clang_target(real_clang))
        check_unsupported_lto(freak, root, env, log)
        check_cache_separation(freak, root, env)
        check_linker_identity_selection(freak, root, env, log, real_clang)

    print("v3_build_profiles: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
