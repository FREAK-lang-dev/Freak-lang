#!/usr/bin/env python3
"""V3 cross-compile target aliases, doctor --target, and run refusal."""

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

ALIASES = {
    "linux-x64": "x86_64-unknown-linux-gnu",
    "linux-arm64": "aarch64-unknown-linux-gnu",
    "windows-x64": "x86_64-w64-windows-gnu",
    "macos-arm64": "aarch64-apple-darwin",
}

BOGUS_TARGET = "freak-bogus-target-xyz"


def invoke(
    freak: Path,
    cwd: Path,
    args: list[str],
    env: dict[str, str],
    *,
    timeout: int = 180,
) -> tuple[int, str]:
    """Invoke the FREAK CLI and return its status and ANSI-free output."""
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


def normalize(triple: str) -> str:
    """Normalize spelling differences used by equivalent target triples."""
    return triple.replace("arm64", "aarch64")


def arch_family(triple: str) -> str:
    """Return the normalized architecture family for a target triple."""
    first = triple.split("-")[0] if triple else ""
    return {"arm64": "aarch64", "amd64": "x86_64"}.get(first, first)


def os_family(triple: str) -> str:
    """Return the operating-system family encoded in a target triple."""
    low = triple.lower()
    if "android" in low:
        return "android"
    if "linux" in low:
        return "linux"
    if "darwin" in low or "macos" in low or "macosx" in low:
        return "darwin"
    if "windows" in low or "msvc" in low or "mingw" in low or "w64" in low:
        return "windows"
    return ""


def same_host(triple: str, native: str) -> bool:
    """Return whether two triples identify the same executable host family."""
    return arch_family(triple) == arch_family(native) and os_family(triple) == os_family(native)


def native_triple(env: dict[str, str]) -> str:
    """Ask the configured Clang for the native target triple."""
    configured = env.get("FREAK_CLANG", "clang")
    candidates = [configured, "clang"]
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved is None and Path(candidate).is_file():
            resolved = candidate
        if resolved is None:
            continue
        completed = subprocess.run(
            [resolved, "-dumpmachine"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
        rendered = completed.stdout.strip()
        if completed.returncode == 0 and re.fullmatch(r"[A-Za-z0-9_.-]+", rendered):
            return rendered
    raise AssertionError("could not determine the native clang target triple")


def check_static_contract(repo: Path) -> None:
    """Verify source-level target helpers, diagnostics, and help contracts."""
    build = (repo / "src" / "cli" / "build.fk").read_text(encoding="utf-8")
    run = (repo / "src" / "cli" / "run.fk").read_text(encoding="utf-8")
    doctor = (repo / "src" / "cli" / "doctor.fk").read_text(encoding="utf-8")
    main = (repo / "src" / "cli" / "main.fk").read_text(encoding="utf-8")
    help_text = (repo / "src" / "cli" / "version.fk").read_text(encoding="utf-8")
    for alias, triple in ALIASES.items():
        assert f'if value == "{alias}" {{ give back "{triple}" }}' in build, alias
        assert f'if triple == "{triple}" {{ give back "{alias}" }}' in build, alias
    for needle in (
        "task cli_resolve_target_alias(value: word) -> word",
        "task cli_canonical_target_is_supported(triple: word) -> bool",
        "task cli_host_can_execute_target(cross: word) -> bool",
        "task cli_host_native_triple() -> word",
        "task cli_link_is_windows(cross: word) -> bool",
    ):
        assert needle in build, f"target helper missing {needle}"
    assert "pilot is_win = cli_link_is_windows(cross)" in build, (
        "link inputs must follow the target OS, not the host OS"
    )
    for needle in (
        "FOREIGN TARGET",
        "freak run refused --target=",
        "freak run only executes binaries the host can run",
        "cli_host_can_execute_target(cross)",
    ):
        assert needle in run, f"run refusal missing {needle}"
    for needle in (
        "task cli_doctor_target_report(raw: word, triple: word, json_mode: bool) -> int",
        "task cli_doctor_target_json(raw: word, triple: word) -> int",
        "task cli_doctor_target_libc(triple: word) -> word",
        "task cli_doctor_target_sysroot_note(triple: word) -> word",
        "task cli_doctor_target_runtime_note(triple: word) -> word",
        "Target libc and runtime support matrix:",
        "Known-unsupported features for cross targets:",
        "Termux/Android",
        "Unsupported target:",
    ):
        assert needle in doctor, f"doctor target report missing {needle}"
    for needle in (
        "cli_resolve_target_alias(tval)",
        "cli_doctor_target_report(doctor_target_raw, doctor_target, json_mode)",
        "--target requires a safe target triple or alias",
    ):
        assert needle in main, f"doctor dispatch missing {needle}"
    for alias in ALIASES:
        assert alias in help_text, f"help text missing alias {alias}"
    assert "pass through" in help_text, "help text missing passthrough note"


def check_doctor_alias_mapping(
    freak: Path, root: Path, env: dict[str, str]
) -> None:
    """Verify every alias maps consistently in text and JSON doctor output."""
    for alias, triple in ALIASES.items():
        code, output = invoke(freak, root, ["doctor", f"--target={alias}"], env)
        assert f"Mapping: {alias} -> {triple}" in output, output
        assert triple in output, output
        assert "Target libc and runtime support matrix:" in output, output
        assert "Known-unsupported features for cross targets:" in output, output
        code_json, output_json = invoke(
            freak, root, ["doctor", "--json", f"--target={alias}"], env
        )
        document = json.loads(output_json)
        target = document["checks"]["target"]
        assert target["requested"] == alias, output_json
        assert target["resolved"] == triple, output_json
        assert target["known"] is True, output_json
        assert "linux-x64" in target["supported_aliases"], output_json
        assert target["clang"]["command"] != "", output_json
        assert code == code_json, output + output_json


def check_raw_passthrough(
    freak: Path, root: Path, env: dict[str, str], native: str
) -> None:
    """Verify canonical triples pass through doctor without alias rewriting."""
    for triple in ALIASES.values():
        code, output = invoke(freak, root, ["doctor", f"--target={triple}"], env)
        assert "raw triple passthrough" in output, output
        assert triple in output, output
        assert code == 0 or "linker" in output.lower(), output
    code, output = invoke(freak, root, ["doctor", f"--target={native}"], env)
    if normalize(native) in {normalize(known) for known in ALIASES.values()}:
        assert code == 0, output
        assert native in output, output
    else:
        assert code != 0, output
        assert "Unsupported target" in output, output


def check_doctor_bogus_target(
    freak: Path, root: Path, env: dict[str, str]
) -> None:
    """Verify doctor rejects an unknown target in text and JSON modes."""
    code, output = invoke(freak, root, ["doctor", f"--target={BOGUS_TARGET}"], env)
    assert code != 0, output
    assert "Unsupported target" in output, output
    assert "Supported aliases: linux-x64, linux-arm64, windows-x64, macos-arm64" in output, output
    assert "Fix:" in output, output
    code_json, output_json = invoke(
        freak, root, ["doctor", "--json", f"--target={BOGUS_TARGET}"], env
    )
    assert code_json != 0, output_json
    document = json.loads(output_json)
    assert document["status"] == "issues", output_json
    target = document["checks"]["target"]
    assert target["requested"] == BOGUS_TARGET, output_json
    assert target["known"] is False, output_json
    assert target["ok"] is False, output_json


def check_native_alias_build(
    freak: Path, root: Path, env: dict[str, str], native: str
) -> None:
    """Verify the native alias builds an executable that runs successfully."""
    alias = next(
        (name for name, triple in ALIASES.items() if same_host(triple, native)),
        None,
    )
    assert alias is not None, f"native triple {native} has no test alias"
    source = root / "alias-native.fk"
    source.write_text('say "ALIAS_NATIVE_OK"\n', encoding="utf-8")
    code, output = invoke(freak, root, ["build", str(source), f"--target={alias}"], env)
    assert code == 0, output
    binary = source.with_suffix(".exe" if sys.platform == "win32" else "")
    completed = subprocess.run(
        [str(binary.resolve())],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "ALIAS_NATIVE_OK" in completed.stdout, completed.stdout


def check_native_alias_run(
    freak: Path, root: Path, env: dict[str, str], native: str
) -> None:
    """Verify ``freak run`` accepts and executes the native target alias."""
    # P1-2 live proof: a native alias must execute via freak run, not refuse.
    alias = next(
        (name for name, triple in ALIASES.items() if same_host(triple, native)),
        None,
    )
    assert alias is not None, f"native triple {native} has no test alias"
    source = root / "alias-native.fk"
    assert source.is_file(), "alias-native.fk missing (build check runs first)"
    code, output = invoke(freak, root, ["run", str(source), f"--target={alias}"], env)
    assert code == 0, output
    assert "ALIAS_NATIVE_OK" in output, output
    assert "FOREIGN TARGET" not in output, output


def check_foreign_run_refusal(
    freak: Path, root: Path, env: dict[str, str], native: str, foreign: str
) -> None:
    """Verify foreign-target run refusal leaves existing artifacts untouched."""
    source = root / "foreign-run.fk"
    source.write_text('say "FOREIGN_MUST_NOT_RUN"\n', encoding="utf-8")
    binary = source.with_suffix(".exe" if sys.platform == "win32" else "")
    artifacts = [
        binary,
        Path(str(source) + ".c"),
        Path(str(source) + ".ll"),
        source.with_suffix(".obj"),
        Path(str(binary) + ".freak-run-cache"),
    ]
    foreign_alias = next(name for name, triple in ALIASES.items() if triple == foreign)
    for flag in (f"--target={foreign}", f"--target={foreign_alias}"):
        expected: dict[Path, bytes] = {}
        for index, artifact in enumerate(artifacts):
            payload = f"sentinel-{flag}-{index}\n".encode()
            artifact.write_bytes(payload)
            expected[artifact] = payload
        code, output = invoke(freak, root, ["run", str(source), flag], env)
        assert code != 0, output
        assert "FOREIGN TARGET" in output, output
        assert "freak build" in output, output
        assert foreign in output, output
        for artifact, payload in expected.items():
            assert artifact.read_bytes() == payload, (
                f"foreign run mutated {artifact} for {flag}\n{output}"
            )
    assert not same_host(foreign, native), (native, foreign)


def check_help_text(freak: Path, root: Path, env: dict[str, str]) -> None:
    """Verify CLI help advertises aliases and raw target passthrough."""
    code, output = invoke(freak, root, ["help"], env)
    assert code == 0, output
    for alias in ALIASES:
        assert alias in output, output
    assert "pass through" in output, output
    assert "--target" in output, output


def main() -> int:
    """Run the V3 target-alias regression suite."""
    parser = argparse.ArgumentParser()
    parser.add_argument("freak", type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    freak = args.freak.resolve()
    assert freak.is_file(), freak

    check_static_contract(repo)
    env = os.environ.copy()
    native = native_triple(env)
    # A truly foreign target differs in OS family (family matching now lets
    # same-host aliases execute, so byte-inequality is no longer foreign).
    foreign = next(
        (triple for triple in ALIASES.values() if os_family(triple) != os_family(native)),
        None,
    )
    if foreign is None:
        foreign = next(
            (triple for triple in ALIASES.values() if arch_family(triple) != arch_family(native)),
            None,
        )
    if foreign is None:
        foreign = next(triple for triple in ALIASES.values() if triple != native)
    assert foreign is not None, "no foreign test target available"
    with tempfile.TemporaryDirectory(prefix="freak-w4-target-aliases-") as tmp:
        root = Path(tmp)
        check_doctor_alias_mapping(freak, root, env)
        check_raw_passthrough(freak, root, env, native)
        check_doctor_bogus_target(freak, root, env)
        check_native_alias_build(freak, root, env, native)
        check_native_alias_run(freak, root, env, native)
        check_foreign_run_refusal(freak, root, env, native, foreign)
        check_help_text(freak, root, env)
    print(f"V3 target aliases: OK (native={native} foreign={foreign})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
