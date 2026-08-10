#!/usr/bin/env python3
"""Install and execute a release-shaped archive containing the real CI binary."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path


def run(command: list[str], cwd: Path, env: dict[str, str], timeout: int = 240) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=timeout,
        check=False,
    )


def manifest_entries(repo: Path) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for raw in (repo / "packaging" / "distribution-files.manifest").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        source, separator, destination = line.partition("|")
        assert separator and source and destination, line
        entries.append((source, destination))
    return entries


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("freak", type=Path)
    parser.add_argument("hangar", type=Path)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    freak = args.freak.resolve()
    hangar = args.hangar.resolve()
    assert freak.is_file(), freak
    assert hangar.is_file(), hangar

    with tempfile.TemporaryDirectory(prefix="freak-v3-release-install-") as tmp:
        root = Path(tmp)
        dist = root / "package" / "freak"
        bin_dir = dist / "bin"
        bin_dir.mkdir(parents=True)
        extension = ".exe" if sys.platform == "win32" else ""
        shutil.copy2(freak, bin_dir / f"freak{extension}")
        shutil.copy2(hangar, bin_dir / f"hangar{extension}")
        for source, destination in manifest_entries(repo):
            target = dist / destination
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(repo / source, target)
        shutil.copy2(
            repo / "packaging" / "distribution-files.manifest",
            dist / "distribution-files.manifest",
        )

        if sys.platform == "win32":
            for name in (
                "freak_runtime.obj",
                "freak_llvm_runtime.obj",
                "freak_ui_win32.obj",
            ):
                source = repo / "freakc" / "runtime" / name
                assert source.is_file(), f"release runtime object missing: {source}"
                shutil.copy2(source, dist / "runtime" / name)
            archive = root / "freak-windows-x64.zip"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zipped:
                for path in dist.rglob("*"):
                    if path.is_file():
                        zipped.write(path, path.relative_to(dist.parent))
        else:
            archive = root / "freak-posix.tar.gz"
            with tarfile.open(archive, "w:gz") as tarred:
                tarred.add(dist, arcname="freak")

        install_home = root / "installed"
        env = os.environ.copy()
        env.update(
            {
                "FREAK_HOME": str(install_home),
                "FREAK_INSTALL_ARCHIVE": str(archive),
                "FREAK_RELEASE_TAG": "vrelease-smoke",
                "FREAK_INSTALL_DEPS": "0",
                "FREAK_SKIP_PATH_UPDATE": "1",
            }
        )
        installer = (
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(repo / "install.ps1"),
                "-SkipDeps",
            ]
            if sys.platform == "win32"
            else ["bash", str(repo / "install.sh"), "--skip-deps"]
        )
        installed = run(installer, repo, env)
        assert installed.returncode == 0, installed.stdout + installed.stderr

        installed_freak = install_home / "bin" / f"freak{extension}"
        installed_hangar = install_home / "bin" / f"hangar{extension}"
        doctor = run([str(installed_freak), "doctor"], root, env)
        assert doctor.returncode == 0, doctor.stdout + doctor.stderr
        assert "compile, link, and execution work" in doctor.stdout

        source = root / "hello.fk"
        source.write_text('say "RELEASE_ARCHIVE_OK"\n', encoding="utf-8")
        built = run([str(installed_freak), "build", str(source)], root, env)
        assert built.returncode == 0, built.stdout + built.stderr
        if sys.platform == "win32":
            assert "Linking packaged Windows runtime objects" in built.stdout
        binary = source.with_suffix(".exe" if sys.platform == "win32" else "")
        executed = run([str(binary)], root, env)
        assert executed.returncode == 0, executed.stdout + executed.stderr
        assert executed.stdout.strip() == "RELEASE_ARCHIVE_OK"

        version = run([str(installed_hangar), "--version"], root, env)
        assert version.returncode == 0, version.stdout + version.stderr
        compiler_version = run([str(installed_freak), "version"], root, env)
        assert compiler_version.returncode == 0
        assert version.stdout.strip() == compiler_version.stdout.strip()
        help_result = run([str(installed_hangar), "--help"], root, env)
        assert help_result.returncode == 0, help_result.stdout + help_result.stderr
        assert "HANGAR" in help_result.stdout and "COMMANDS" in help_result.stdout

    print("V3 release-shaped installation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
