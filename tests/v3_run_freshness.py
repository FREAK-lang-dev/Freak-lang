#!/usr/bin/env python3
"""Regression coverage for `freak run` freshness and installer manifests."""

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


def selected_clang(freak: Path, cwd: Path, env: dict[str, str]) -> str:
    report = subprocess.run(
        [str(freak), "doctor", "--json"], cwd=cwd, env=env,
        capture_output=True, text=True, errors="replace", timeout=120,
        check=False,
    )
    document = json.loads(report.stdout)
    assert document["checks"]["clang"]["ok"] is True, report.stdout + report.stderr
    command = document["checks"]["clang"]["command"]
    if len(command) >= 2 and command.startswith('"') and command.endswith('"'):
        command = command[1:-1]
    resolved = shutil.which(command)
    if resolved:
        return resolved
    assert Path(command).is_file(), command
    return command


def check_installer_contracts(repo: Path) -> None:
    shell_text = (repo / "install.sh").read_text(encoding="utf-8")
    ps_text = (repo / "install.ps1").read_text(encoding="utf-8")
    release_text = (repo / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    )
    manifest_text = (repo / "packaging" / "distribution-files.manifest").read_text(
        encoding="utf-8"
    )
    run_text = (repo / "src" / "cli" / "run.fk").read_text(encoding="utf-8")

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
        "Pre-compile Windows runtime objects",
        "freak_runtime.obj dist/freak/runtime/",
        "freak_llvm_runtime.obj dist/freak/runtime/",
        "freak_ui_win32.obj dist/freak/runtime/",
        "LLVM_MINGW_SHA256",
    ):
        assert needle in release_text, f"release.yml missing {needle}"
    for needle in (
        "freakc/runtime/ui/freak_ui_platform.h|runtime/ui/freak_ui_platform.h",
        "std/runtime.fk|std/runtime.fk",
        "std/zip.fk|std/zip.fk",
        "std/ui/window.fk|std/ui/window.fk",
    ):
        assert needle in manifest_text, f"distribution manifest missing {needle}"
    for needle in (
        'CLI_RUN_CACHE_SCHEMA = "freak-run-cache-v6"',
        "task cli_run_clang_identity",
        "command -v ",
        "certutil -hashfile",
        "sha256sum ",
    ):
        assert needle in run_text, f"run cache identity missing {needle}"

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
        # Keep a competing checkout stdlib beside the compiler so this test
        # proves explicit FREAK_HOME inputs drive both cache fingerprints and
        # rebuilds on every platform, not only when the test binary is isolated.
        checkout = root / "checkout-like"
        checkout_bin = checkout / "build"
        checkout_bin.mkdir(parents=True)
        checkout_freak = checkout_bin / freak.name
        shutil.copy2(freak, checkout_freak)
        shutil.copytree(repo / "std", checkout / "std")
        freak = checkout_freak
        install = root / "install with spaces"
        runtime = install / "runtime"
        std = install / "std"
        runtime.mkdir(parents=True)
        std.mkdir(parents=True)
        for name in ("freak_runtime.c", "freak_runtime.h", "freak_llvm_runtime.c"):
            shutil.copy2(repo / "freakc" / "runtime" / name, runtime / name)
        runtime_abi = runtime / "freak_abi"
        shutil.copy2(repo / "freakc" / "runtime" / "freak_abi", runtime_abi)
        runtime_api = runtime / "freak_runtime_api"
        shutil.copy2(
            repo / "freakc" / "runtime" / "freak_runtime_api", runtime_api
        )
        if sys.platform == "win32":
            runtime_ui = runtime / "ui"
            runtime_ui.mkdir()
            for name in ("win32_backend.c", "freak_ui_platform.h"):
                shutil.copy2(repo / "freakc" / "runtime" / "ui" / name, runtime_ui / name)
        if sys.platform != "win32":
            # Old archives may contain runtime objects. They must not select
            # the raw ld.lld bundle path on POSIX; Clang must link sources.
            (runtime / "freak_runtime.o").write_bytes(b"stale object\n")
            (runtime / "freak_llvm_runtime.o").write_bytes(b"stale object\n")
        (std / "math.fk").write_text("-- freshness std v1\n", encoding="utf-8")
        shutil.copy2(repo / "std" / "freak_abi", std / "freak_abi")
        shutil.copy2(repo / "std" / "freak_std_api", std / "freak_std_api")

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

        # Runtime API capability gates apply before the warm-cache fast path.
        # A missing or incompatible marker must not launch or mutate the cached
        # executable/proof, and restoring the exact marker must recover the
        # same cache entry without rebuilding.
        cached_binary = binary.read_bytes()
        cached_sidecar = sidecar.read_bytes()
        for marker_value in (
            None,
            "freak-v3-runtime-api-1\n",
            "freak-v3-runtime-api-999\n",
        ):
            if marker_value is None:
                runtime_api.unlink()
            else:
                runtime_api.write_text(marker_value, encoding="utf-8")
            code, output = invoke(freak, source_dir, source_arg, "--c", env)
            assert code != 0, output
            assert "runtime api mismatch" in output.lower(), output
            assert "CACHE_A" not in output, output
            assert binary.read_bytes() == cached_binary
            assert sidecar.read_bytes() == cached_sidecar

            shutil.copy2(
                repo / "freakc" / "runtime" / "freak_runtime_api", runtime_api
            )
            code, output = invoke(freak, source_dir, source_arg, "--c", env)
            assert_run(code, output, "CACHE_A", cache_hit=True)
            assert binary.stat().st_mtime_ns == first_mtime
            assert binary.read_bytes() == cached_binary
            assert sidecar.read_bytes() == cached_sidecar

        # Cold build/run must reject an older same-ABI runtime before emitting
        # either backend. Keep the warm artifact beside it to also prove that
        # a rejected cold operation cannot invalidate unrelated cache entries.
        cold_source = source_dir / "runtime-api-cold.fk"
        cold_source.write_text('say "COLD_API_EXECUTED"\n', encoding="utf-8")
        cold_binary = cold_source.with_suffix(
            ".exe" if sys.platform == "win32" else ""
        )
        cold_outputs = (
            Path(str(cold_source) + ".c"),
            Path(str(cold_source) + ".ll"),
            cold_binary,
            Path(str(cold_binary) + ".freak-run-cache"),
        )
        try:
            for marker_value in (None, "freak-v3-runtime-api-1\n"):
                if marker_value is None:
                    runtime_api.unlink()
                else:
                    runtime_api.write_text(marker_value, encoding="utf-8")
                for backend in ("--c", "--llvm"):
                    for operation in ("build", "run"):
                        rejected = subprocess.run(
                            [str(freak), operation, cold_source.name, backend],
                            cwd=source_dir, env=env, capture_output=True,
                            text=True, errors="replace", timeout=120, check=False,
                        )
                        output = ANSI.sub("", rejected.stdout + rejected.stderr)
                        assert rejected.returncode != 0, output
                        assert "runtime api mismatch" in output.lower(), output
                        assert "COLD_API_EXECUTED" not in output, output
                        assert not any(path.exists() for path in cold_outputs), (
                            operation, backend, cold_outputs, output
                        )
                        assert binary.read_bytes() == cached_binary
                        assert sidecar.read_bytes() == cached_sidecar
        finally:
            shutil.copy2(
                repo / "freakc" / "runtime" / "freak_runtime_api", runtime_api
            )

        # Build invalidation is ordered proof-first. If the cache proof cannot
        # be removed, the old executable is preserved; if only the executable
        # is undeletable, its proof is already gone before the build rejects.
        blocked_source = source_dir / "blocked-invalidation.fk"
        blocked_source.write_text('say "BLOCKED_INVALIDATION"\n', encoding="utf-8")
        blocked_arg = Path(blocked_source.name)
        blocked_binary = blocked_source.with_suffix(
            ".exe" if sys.platform == "win32" else ""
        )
        blocked_sidecar = Path(str(blocked_binary) + ".freak-run-cache")
        code, output = invoke(freak, source_dir, blocked_arg, "--c", env)
        assert_run(code, output, "BLOCKED_INVALIDATION", cache_hit=False)
        assert blocked_binary.is_file() and blocked_sidecar.is_file()

        original_binary = blocked_binary.read_bytes()
        blocked_sidecar.unlink()
        blocked_sidecar.mkdir()
        blocked_cache_result = subprocess.run(
            [str(freak), "build", str(blocked_source), "--c"],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=120,
            check=False,
        )
        blocked_cache_output = ANSI.sub(
            "", blocked_cache_result.stdout + blocked_cache_result.stderr
        )
        assert blocked_cache_result.returncode != 0, blocked_cache_output
        assert "untrusted stale artifact" in blocked_cache_output.lower()
        assert blocked_sidecar.is_dir()
        assert blocked_binary.read_bytes() == original_binary
        blocked_sidecar.rmdir()

        code, output = invoke(freak, source_dir, blocked_arg, "--c", env)
        assert_run(code, output, "BLOCKED_INVALIDATION", cache_hit=False)
        assert blocked_sidecar.is_file()
        blocked_binary.unlink()
        blocked_binary.mkdir()
        blocked_binary_result = subprocess.run(
            [str(freak), "build", str(blocked_source), "--c"],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=120,
            check=False,
        )
        blocked_binary_output = ANSI.sub(
            "", blocked_binary_result.stdout + blocked_binary_result.stderr
        )
        assert blocked_binary_result.returncode != 0, blocked_binary_output
        assert "untrusted stale artifact" in blocked_binary_output.lower()
        assert blocked_binary.is_dir()
        assert not blocked_sidecar.exists(), (
            "undeletable binary retained a stale freshness proof"
        )
        blocked_binary.rmdir()

        # WinGet upgrades remove versioned LLVM-MinGW directories. A stale
        # persisted FREAK_CLANG must fall through to normal discovery rather
        # than masking the replacement toolchain that is already available.
        stale_source = source_dir / "stale-clang-override.fk"
        stale_source.write_text('say "STALE_CLANG_RECOVERED"\n', encoding="utf-8")
        stale_env = env.copy()
        stale_env["FREAK_CLANG"] = str(
            root / "removed-llvm-mingw-version" / "bin" / "clang.exe"
        )
        code, output = invoke(
            freak, source_dir, Path(stale_source.name), "--c", stale_env
        )
        assert_run(code, output, "STALE_CLANG_RECOVERED", cache_hit=False)

        # Version text alone is not a toolchain identity. Two wrappers can
        # advertise the same version while selecting different compiler
        # bytes. Replacing the selected executable must invalidate the cache.
        real_clang = selected_clang(freak, root, env)
        clang_wrapper = root / (
            "clang-fingerprint.cmd" if sys.platform == "win32" else "clang-fingerprint.sh"
        )
        if sys.platform == "win32":
            wrapper_template = (
                "@echo off\n"
                "rem fixture generation {generation}\n"
                'if "%~1"=="--version" (echo clang identical-version fixture& exit /b 0)\n'
                f'"{real_clang}" %*\n'
            )
        else:
            wrapper_template = (
                "#!/bin/sh\n"
                "# fixture generation {generation}\n"
                'if [ "$1" = "--version" ]; then echo "clang identical-version fixture"; exit 0; fi\n'
                f'exec \'{real_clang}\' "$@"\n'
            )
        clang_env = env.copy()
        clang_env["FREAK_CLANG"] = str(clang_wrapper)
        clang_wrapper.write_text(wrapper_template.format(generation=1), encoding="utf-8")
        if sys.platform != "win32":
            clang_wrapper.chmod(0o755)
        code, output = invoke(freak, source_dir, source_arg, "--c", clang_env)
        assert_run(code, output, "CACHE_A", cache_hit=False)
        code, output = invoke(freak, source_dir, source_arg, "--c", clang_env)
        assert_run(code, output, "CACHE_A", cache_hit=True)
        clang_wrapper.write_text(wrapper_template.format(generation=2), encoding="utf-8")
        if sys.platform != "win32":
            clang_wrapper.chmod(0o755)
        code, output = invoke(freak, source_dir, source_arg, "--c", clang_env)
        assert_run(code, output, "CACHE_A", cache_hit=False)

        # A warm cache never bypasses distribution integrity. Changing only
        # the ABI marker must reject the run before the cached program starts.
        runtime_abi.write_text("freak-v3-abi-999\n", encoding="utf-8")
        code, output = invoke(freak, source_dir, source_arg, "--c", env)
        assert code != 0, output
        assert "abi mismatch" in output.lower(), output
        assert "CACHE_A" not in output, output
        shutil.copy2(repo / "freakc" / "runtime" / "freak_abi", runtime_abi)

        if sys.platform == "win32":
            pending = install / "bin" / ".freak-upgrade-pending"
            pending.parent.mkdir(parents=True, exist_ok=True)
            pending.write_text("vfixture|wait-pid=fixture\n", encoding="utf-8")
            code, output = invoke(freak, source_dir, source_arg, "--c", env)
            assert code != 0, output
            assert "upgrade pending" in output.lower(), output
            assert "CACHE_A" not in output, output
            pending.unlink()

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

        if sys.platform == "win32":
            # Windows release archives ship one coherent COFF runtime bundle.
            # Break the source fallbacks after producing those objects and
            # prove both backends still link and run through the Clang driver.
            clang = selected_clang(freak, root, env)
            runtime_sources = {
                runtime / "freak_runtime.c": (runtime / "freak_runtime.c").read_bytes(),
                runtime / "freak_llvm_runtime.c": (
                    runtime / "freak_llvm_runtime.c"
                ).read_bytes(),
            }
            runtime_objects = (
                runtime / "freak_runtime.obj",
                runtime / "freak_llvm_runtime.obj",
                runtime / "freak_ui_win32.obj",
            )
            legacy_runtime_objects = (
                runtime / "freak_runtime.o",
                runtime / "freak_llvm_runtime.o",
                runtime / "freak_ui_win32.o",
            )
            object_commands = (
                [clang, "-c", str(runtime / "freak_runtime.c"), "-I", str(runtime),
                 "-O2", "-w", "-D_CRT_SECURE_NO_WARNINGS", "-o", str(runtime_objects[0])],
                [clang, "-c", str(runtime / "freak_llvm_runtime.c"), "-I", str(runtime),
                 "-O2", "-w", "-D_CRT_SECURE_NO_WARNINGS", "-DFREAK_HAS_UI",
                 "-o", str(runtime_objects[1])],
                [clang, "-c", str(runtime / "ui" / "win32_backend.c"),
                 "-I", str(runtime / "ui"), "-O2", "-w",
                 "-D_CRT_SECURE_NO_WARNINGS", "-o", str(runtime_objects[2])],
            )
            for command in object_commands:
                compiled_object = subprocess.run(
                    command, cwd=root, env=env, capture_output=True, text=True,
                    errors="replace", timeout=120, check=False,
                )
                assert compiled_object.returncode == 0, (
                    compiled_object.stdout + compiled_object.stderr
                )

            object_doctor = subprocess.run(
                [str(freak), "doctor", "--json"], cwd=root, env=env,
                capture_output=True, text=True, errors="replace", timeout=120,
                check=False,
            )
            object_report = json.loads(object_doctor.stdout)
            assert object_report["checks"]["runtime"]["precompiled_objects"] is True

            object_env = env.copy()
            object_env["FREAK_CLANG"] = clang
            missing_ui_object = runtime / "freak_ui_win32.obj.partial"
            runtime_objects[2].replace(missing_ui_object)
            try:
                partial_doctor = subprocess.run(
                    [str(freak), "doctor", "--json"], cwd=root, env=object_env,
                    capture_output=True, text=True, errors="replace", timeout=120,
                    check=False,
                )
                partial_report = json.loads(partial_doctor.stdout)
                assert partial_report["checks"]["runtime"]["precompiled_objects"] is False
                code, output = invoke(
                    freak, source_dir, source_arg, "--llvm", object_env
                )
                assert_run(code, output, "CACHE_B", cache_hit=False)
                assert "Compiling native binary" in output, output
                assert "Linking packaged Windows runtime objects" not in output, output
            finally:
                missing_ui_object.replace(runtime_objects[2])

            # Release objects are built by pinned LLVM-MinGW, while an
            # otherwise usable installed Clang may target a different Windows
            # ABI family. Force only the packaged-object link to fail and
            # prove the CLI transparently retries from runtime sources.
            fallback_driver = root / "bundle-fallback-driver.py"
            fallback_driver.write_text(
                "import pathlib, subprocess, sys\n"
                f"real = {clang!r}\n"
                "if any(pathlib.Path(arg).name.lower() == 'freak_runtime.obj' for arg in sys.argv[1:]):\n"
                "    raise SystemExit(86)\n"
                "raise SystemExit(subprocess.call([real, *sys.argv[1:]]))\n",
                encoding="utf-8",
            )
            fallback_wrapper = root / "bundle-fallback-clang.cmd"
            fallback_wrapper.write_text(
                f'@python "{fallback_driver}" %*\n', encoding="utf-8"
            )
            fallback_env = env.copy()
            fallback_env["FREAK_CLANG"] = str(fallback_wrapper)
            code, output = invoke(
                freak, source_dir, source_arg, "--llvm", fallback_env
            )
            assert_run(code, output, "CACHE_B", cache_hit=False)
            assert "Linking packaged Windows runtime objects" in output, output
            assert "retrying runtime sources" in output, output
            assert "Compiling native binary" in output, output

            try:
                for runtime_source in runtime_sources:
                    runtime_source.write_text(
                        "#error source fallback must not be compiled in object mode\n",
                        encoding="utf-8",
                    )
                code, output = invoke(
                    freak, source_dir, source_arg, "--c", object_env
                )
                assert_run(code, output, "CACHE_B", cache_hit=False)
                assert "Linking packaged Windows runtime objects" in output, output
                code, output = invoke(
                    freak, source_dir, source_arg, "--llvm", object_env
                )
                assert_run(code, output, "CACHE_B", cache_hit=False)
                assert "Linking packaged Windows runtime objects" in output, output
                for current_object, legacy_object in zip(
                    runtime_objects, legacy_runtime_objects
                ):
                    current_object.replace(legacy_object)
                code, output = invoke(
                    freak, source_dir, source_arg, "--llvm", object_env
                )
                assert_run(code, output, "CACHE_B", cache_hit=False)
                assert "Linking packaged Windows runtime objects" in output, output
            finally:
                for runtime_source, contents in runtime_sources.items():
                    runtime_source.write_bytes(contents)
                for runtime_object in runtime_objects:
                    runtime_object.unlink(missing_ok=True)
                for runtime_object in legacy_runtime_objects:
                    runtime_object.unlink(missing_ok=True)

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
            mock_linker = root / "ld.lld.exe"
            shutil.copy2(freak, mock_linker)
            mock_clang = root / "mock-clang.cmd"
            mock_clang.write_text(
                "@echo off\n"
                "setlocal DisableDelayedExpansion\n"
                'if "%~1"=="--version" (echo clang mock-version& exit /b 0)\n'
                'if "%~1"=="-dumpmachine" (echo x86_64-w64-windows-gnu& exit /b 0)\n'
                f'if "%~1"=="-###" (echo "{mock_linker}" "-out:nul"& exit /b 0)\n'
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
                percent_source,
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

        # A failed rebuild must invalidate both the freshness proof and the old
        # executable. Remove the staged runtime, change source, and verify the
        # prior CACHE_B artifact cannot be mistaken for a successful rebuild.
        (runtime / "freak_runtime.c").unlink()
        source.write_text('say "CACHE_C"\n', encoding="utf-8")
        code, output = invoke(freak, source_dir, source_arg, "--llvm", env)
        assert code != 0, output
        assert "CACHE_B" not in output, output
        assert not binary.exists(), "failed rebuild preserved an untrusted stale binary"
        assert not sidecar.exists(), "failed rebuild left stale freshness proof"

    print("V3 run freshness and installer cleanup: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
