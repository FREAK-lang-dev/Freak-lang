#!/usr/bin/env python3
"""Regression coverage for `freak run` freshness and installer manifests."""

from __future__ import annotations

import argparse
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
    source: Path,
    backend: str,
    env: dict[str, str],
) -> tuple[int, str]:
    proc = subprocess.run(
        [str(freak), "run", str(source), backend],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=120,
        check=False,
    )
    return proc.returncode, ANSI.sub("", proc.stdout + proc.stderr)


def assert_run(code: int, output: str, marker: str, *, cache_hit: bool) -> None:
    assert code == 0, output
    assert marker in output, output
    assert ("run cache hit" in output) is cache_hit, output


def check_installer_contracts(repo: Path) -> None:
    shell_text = (repo / "install.sh").read_text(encoding="utf-8")
    ps_text = (repo / "install.ps1").read_text(encoding="utf-8")
    release_text = (repo / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    )
    manifest_text = (repo / "packaging" / "distribution-files.manifest").read_text(
        encoding="utf-8"
    )

    for needle in (
        'STAGE_DIR="$TMPDIR_INSTALL/stage"',
        "restore_previous_payload",
        ".freak-backup-",
        "distribution-files.manifest",
        "validate_manifest_entry",
    ):
        assert needle in shell_text, f"install.sh missing {needle}"
    for needle in (
        '$StageDir = Join-Path $TmpDir "stage"',
        ".freak-backup-",
        "previous payload was restored",
        "distribution-files.manifest",
        "Get-ManifestEntries",
    ):
        assert needle in ps_text, f"install.ps1 missing {needle}"
    for needle in (
        "packaging/distribution-files.manifest",
        "dist/freak/distribution-files.manifest",
    ):
        assert needle in release_text, f"release.yml missing {needle}"
    for needle in (
        "freakc/runtime/ui/freak_ui_platform.h|runtime/ui/freak_ui_platform.h",
        "std/runtime.fk|std/runtime.fk",
        "std/zip.fk|std/zip.fk",
        "std/ui/window.fk|std/ui/window.fk",
    ):
        assert needle in manifest_text, f"distribution manifest missing {needle}"

    bash = shutil.which("bash")
    if bash:
        parsed = subprocess.run(
            [bash, "-n", "install.sh"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
        assert parsed.returncode == 0, parsed.stdout + parsed.stderr


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("freak", type=Path)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    freak = args.freak.resolve()
    assert freak.is_file(), f"FREAK CLI not found: {freak}"
    check_installer_contracts(repo)

    with tempfile.TemporaryDirectory(prefix="freak-v3-run-freshness-") as tmp:
        root = Path(tmp)
        install = root / "install with spaces"
        runtime = install / "runtime"
        std = install / "std"
        runtime.mkdir(parents=True)
        std.mkdir(parents=True)
        for name in ("freak_runtime.c", "freak_runtime.h", "freak_llvm_runtime.c"):
            shutil.copy2(repo / "freakc" / "runtime" / name, runtime / name)
        if sys.platform != "win32":
            # Old archives may contain runtime objects. They must not select
            # the raw ld.lld bundle path on POSIX; Clang must link sources.
            (runtime / "freak_runtime.o").write_bytes(b"stale object\n")
            (runtime / "freak_llvm_runtime.o").write_bytes(b"stale object\n")
        (std / "math.fk").write_text("-- freshness std v1\n", encoding="utf-8")

        isolated_home = root / "home"
        isolated_appdata = root / "appdata"
        isolated_home.mkdir()
        isolated_appdata.mkdir()
        env = os.environ.copy()
        env["FREAK_HOME"] = str(install)
        env["HOME"] = str(isolated_home)
        env["APPDATA"] = str(isolated_appdata)

        source_dir = root / "source with spaces"
        source_dir.mkdir()
        source = source_dir / "freshness.fk"
        source_arg = Path(source.name)
        source.write_text('say "CACHE_A"\n', encoding="utf-8")
        binary = source.with_suffix(".exe" if sys.platform == "win32" else "")
        sidecar = Path(str(binary) + ".freak-run-cache")

        # The common `freak run hello.fk` shape yields a slashless POSIX
        # output name, which must be launched explicitly from the cwd.
        code, output = invoke(freak, source_dir, source_arg, "--c", env)
        assert_run(code, output, "CACHE_A", cache_hit=False)
        assert binary.is_file() and sidecar.is_file()
        first_mtime = binary.stat().st_mtime_ns

        code, output = invoke(freak, source_dir, source_arg, "--c", env)
        assert_run(code, output, "CACHE_A", cache_hit=True)
        assert binary.stat().st_mtime_ns == first_mtime

        binary.write_bytes(b"externally replaced artifact\n")
        code, output = invoke(freak, source_dir, source_arg, "--c", env)
        assert_run(code, output, "CACHE_A", cache_hit=False)

        explicit_build = subprocess.run(
            [str(freak), "build", str(source), "--c"],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=120,
            check=False,
        )
        assert explicit_build.returncode == 0, explicit_build.stdout + explicit_build.stderr
        assert not sidecar.exists(), "explicit build preserved stale run proof"
        code, output = invoke(freak, source_dir, source_arg, "--c", env)
        assert_run(code, output, "CACHE_A", cache_hit=False)

        source.write_text('say "CACHE_B"\n', encoding="utf-8")
        code, output = invoke(freak, source_dir, source_arg, "--c", env)
        assert_run(code, output, "CACHE_B", cache_hit=False)

        code, output = invoke(freak, source_dir, source_arg, "--llvm", env)
        assert_run(code, output, "CACHE_B", cache_hit=False)
        code, output = invoke(freak, source_dir, source_arg, "--llvm", env)
        assert_run(code, output, "CACHE_B", cache_hit=True)

        (std / "math.fk").write_text("-- freshness std v2\n", encoding="utf-8")
        code, output = invoke(freak, source_dir, source_arg, "--llvm", env)
        assert_run(code, output, "CACHE_B", cache_hit=False)

        failing_source = source_dir / "child failure.fk"
        child_command = "cmd /c exit 7" if sys.platform == "win32" else "sh -c 'exit 7'"
        failing_source.write_text(
            f'pilot child_status = process::exec("{child_command}")\n'
            "process::exit(child_status)\n",
            encoding="utf-8",
        )
        for backend in ("--c", "--llvm"):
            code, output = invoke(freak, root, failing_source, backend, env)
            assert code == 7, output
            assert "EXIT" in output and "code 7" in output, output

        if sys.platform == "win32":
            # cmd.exe expands %NAME% even inside quotes. A literal-percent
            # project path must remain literal, and a quote-bearing expansion
            # value must never escape into shell syntax.
            windows_path_sentinel = root / "FREAK_WINDOWS_PATH_INJECTED"
            percent_source_dir = root / "%FREAK_PATH_EXPANSION%"
            percent_source_dir.mkdir()
            percent_source = percent_source_dir / "literal percent.fk"
            percent_source.write_text('say "SAFE_WINDOWS_PATH"\n', encoding="utf-8")
            mock_clang = root / "mock-clang.cmd"
            mock_clang.write_text(
                "@echo off\n"
                "setlocal DisableDelayedExpansion\n"
                ":scan\n"
                'if "%~1"=="" exit /b 2\n'
                'if "%~1"=="-o" goto output\n'
                "shift\n"
                "goto scan\n"
                ":output\n"
                "shift\n"
                f'copy /y "{freak}" "%~1" >nul\n'
                "exit /b %ERRORLEVEL%\n",
                encoding="utf-8",
            )
            percent_env = env.copy()
            percent_env["FREAK_CLANG"] = str(mock_clang)
            percent_env["FREAK_PATH_EXPANSION"] = (
                f'missing" & (echo injected>"{windows_path_sentinel}") & rem "'
            )
            code, output = invoke(
                freak,
                root,
                Path("%FREAK_PATH_EXPANSION%") / percent_source.name,
                "--c",
                percent_env,
            )
            assert_run(code, output, "COMMANDS", cache_hit=False)
            assert not windows_path_sentinel.exists(), (
                "source path expanded an environment variable into shell syntax"
            )
        else:
            path_sentinel = source_dir / "FREAK_PATH_INJECTED"
            quoted_source = source_dir / "$(touch${IFS}FREAK_PATH_INJECTED).fk"
            quoted_source.write_text('say "SAFE_PATH"\n', encoding="utf-8")
            code, output = invoke(
                freak, source_dir, Path(quoted_source.name), "--c", env
            )
            assert_run(code, output, "SAFE_PATH", cache_hit=False)
            assert not path_sentinel.exists(), "source path executed shell substitution"

            target_sentinel = source_dir / "FREAK_TARGET_INJECTED"
            malicious_target = (
                "x86_64-unknown-linux-gnu;touch${IFS}FREAK_TARGET_INJECTED"
            )
            rejected_target = subprocess.run(
                [
                    str(freak), "build", str(source_arg), "--c",
                    f"--target={malicious_target}",
                ],
                cwd=source_dir,
                env=env,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=120,
                check=False,
            )
            target_output = ANSI.sub("", rejected_target.stdout + rejected_target.stderr)
            assert rejected_target.returncode != 0, target_output
            assert "invalid target triple" in target_output, target_output
            assert not target_sentinel.exists(), "target triple executed shell syntax"

        # A failed rebuild must invalidate proof before touching the old
        # executable. Remove the staged runtime, change source, and verify the
        # prior CACHE_B binary is not run even though it remains on disk.
        (runtime / "freak_runtime.c").unlink()
        source.write_text('say "CACHE_C"\n', encoding="utf-8")
        code, output = invoke(freak, source_dir, source_arg, "--llvm", env)
        assert code != 0, output
        assert "CACHE_B" not in output, output
        assert binary.is_file(), "the stale artifact should be ignored, not required to vanish"
        assert not sidecar.exists(), "failed rebuild left stale freshness proof"

    print("V3 run freshness and installer cleanup: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
