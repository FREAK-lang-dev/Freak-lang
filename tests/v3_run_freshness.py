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
        'rm -rf -- "$INSTALL_DIR/runtime" "$INSTALL_DIR/std"',
        "distribution-files.manifest",
        "validate_manifest_entry",
    ):
        assert needle in shell_text, f"install.sh missing {needle}"
    for needle in (
        '$StageDir = Join-Path $TmpDir "stage"',
        "Remove-Item -LiteralPath $target -Recurse -Force",
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
        install = root / "install"
        runtime = install / "runtime"
        std = install / "std"
        runtime.mkdir(parents=True)
        std.mkdir(parents=True)
        for name in ("freak_runtime.c", "freak_runtime.h", "freak_llvm_runtime.c"):
            shutil.copy2(repo / "freakc" / "runtime" / name, runtime / name)
        (std / "math.fk").write_text("-- freshness std v1\n", encoding="utf-8")

        isolated_home = root / "home"
        isolated_appdata = root / "appdata"
        isolated_home.mkdir()
        isolated_appdata.mkdir()
        env = os.environ.copy()
        env["FREAK_HOME"] = str(install)
        env["HOME"] = str(isolated_home)
        env["APPDATA"] = str(isolated_appdata)

        source = root / "freshness.fk"
        source.write_text('say "CACHE_A"\n', encoding="utf-8")
        binary = source.with_suffix(".exe" if sys.platform == "win32" else "")
        sidecar = Path(str(binary) + ".freak-run-cache")

        code, output = invoke(freak, root, source, "--c", env)
        assert_run(code, output, "CACHE_A", cache_hit=False)
        assert binary.is_file() and sidecar.is_file()
        first_mtime = binary.stat().st_mtime_ns

        code, output = invoke(freak, root, source, "--c", env)
        assert_run(code, output, "CACHE_A", cache_hit=True)
        assert binary.stat().st_mtime_ns == first_mtime

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
        code, output = invoke(freak, root, source, "--c", env)
        assert_run(code, output, "CACHE_A", cache_hit=False)

        source.write_text('say "CACHE_B"\n', encoding="utf-8")
        code, output = invoke(freak, root, source, "--c", env)
        assert_run(code, output, "CACHE_B", cache_hit=False)

        code, output = invoke(freak, root, source, "--llvm", env)
        assert_run(code, output, "CACHE_B", cache_hit=False)
        code, output = invoke(freak, root, source, "--llvm", env)
        assert_run(code, output, "CACHE_B", cache_hit=True)

        (std / "math.fk").write_text("-- freshness std v2\n", encoding="utf-8")
        code, output = invoke(freak, root, source, "--llvm", env)
        assert_run(code, output, "CACHE_B", cache_hit=False)

        # A failed rebuild must invalidate proof before touching the old
        # executable. Remove the staged runtime, change source, and verify the
        # prior CACHE_B binary is not run even though it remains on disk.
        (runtime / "freak_runtime.c").unlink()
        source.write_text('say "CACHE_C"\n', encoding="utf-8")
        code, output = invoke(freak, root, source, "--llvm", env)
        assert code != 0, output
        assert "CACHE_B" not in output, output
        assert binary.is_file(), "the stale artifact should be ignored, not required to vanish"
        assert not sidecar.exists(), "failed rebuild left stale freshness proof"

    print("V3 run freshness and installer cleanup: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
