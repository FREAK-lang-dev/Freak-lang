#!/usr/bin/env python3
"""V3 distribution, installer, doctor, and upgrade regression coverage."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path


def manifest_entries(repo: Path) -> list[tuple[str, str]]:
    manifest = repo / "packaging" / "distribution-files.manifest"
    entries: list[tuple[str, str]] = []
    for raw_line in manifest.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        source, separator, destination = line.partition("|")
        assert separator and source and destination, line
        assert source.startswith(("freakc/runtime/", "std/")), source
        assert destination.startswith(("runtime/", "std/")), destination
        assert ".." not in Path(source).parts
        assert ".." not in Path(destination).parts
        entries.append((source, destination))
    assert entries
    assert len({destination for _, destination in entries}) == len(entries)
    return entries


def check_manifest(repo: Path, entries: list[tuple[str, str]]) -> None:
    actual_sources = {source for source, _ in entries}
    expected_sources = {
        path.relative_to(repo).as_posix() for path in (repo / "std").rglob("*.fk")
    }
    expected_sources.update(
        {
            "freakc/runtime/freak_runtime.c",
            "freakc/runtime/freak_runtime.h",
            "freakc/runtime/freak_llvm_runtime.c",
            "freakc/runtime/ui/win32_backend.c",
            "freakc/runtime/ui/freak_ui_platform.h",
        }
    )
    for optional in ("freakc/runtime/freak_abi", "std/freak_abi"):
        if (repo / optional).is_file():
            expected_sources.add(optional)
    assert actual_sources == expected_sources, (
        f"manifest missing={sorted(expected_sources - actual_sources)} "
        f"extra={sorted(actual_sources - expected_sources)}"
    )
    for source, _ in entries:
        assert (repo / source).is_file(), source


def check_static_contracts(repo: Path) -> None:
    shell_text = (repo / "install.sh").read_text(encoding="utf-8")
    ps_text = (repo / "install.ps1").read_text(encoding="utf-8")
    release_text = (repo / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    )
    hangar_text = (repo / "src" / "cli" / "hangar.fk").read_text(
        encoding="utf-8"
    )
    doctor_text = (repo / "src" / "cli" / "doctor.fk").read_text(
        encoding="utf-8"
    )
    main_text = (repo / "src" / "cli" / "main.fk").read_text(encoding="utf-8")

    for needle in (
        "--with-deps",
        "FREAK_INSTALL_ARCHIVE",
        "packaging/distribution-files.manifest",
        'rm -rf -- "$INSTALL_DIR/runtime" "$INSTALL_DIR/std"',
    ):
        assert needle in shell_text, f"install.sh missing {needle}"
    for needle in (
        "MartinStorsjo.LLVM-MinGW.UCRT",
        "scoop.cmd install llvm-mingw",
        "Test-ClangToolchain",
        "FREAK_INSTALL_ARCHIVE",
        "Start-DeferredBinaryReplacement",
        "distribution-files.manifest",
    ):
        assert needle in ps_text, f"install.ps1 missing {needle}"
    assert "choco.exe install llvm" not in ps_text
    for needle in (
        "packaging/distribution-files.manifest",
        "dist/freak/distribution-files.manifest",
        "dist/freak-${{ matrix.target }}${{ matrix.ext }}",
        "dist/hangar-${{ matrix.target }}${{ matrix.ext }}",
    ):
        assert needle in release_text, f"release workflow missing {needle}"
    for needle in (
        "task hangar_install_freak() -> int",
        "FREAK_UPGRADE_SCRIPT",
        "hangar_install_freak_v014_legacy_protocol",
        "tagged installer",
    ):
        assert needle in hangar_text, f"upgrade path missing {needle}"
    for needle in (
        "modules_expected\\\": 11",
        "ui/window.fk",
        "scoop install llvm-mingw",
        "compile, link, and execution work",
        "task cli_doctor(fix_mode: bool) -> int",
    ):
        assert needle in doctor_text, f"doctor missing {needle}"
    assert "choco install llvm" not in doctor_text
    assert 'if subcmd == "upgrade"' in main_text
    assert "process::exit(upgrade_res)" in main_text
    assert "process::exit(doctor_exit)" in main_text

    bash = shutil.which("bash")
    if bash:
        parsed = subprocess.run(
            [bash, "-n", "install.sh"], cwd=repo, capture_output=True, text=True
        )
        assert parsed.returncode == 0, parsed.stdout + parsed.stderr
    if sys.platform == "win32":
        command = (
            "$tokens=$null;$errors=$null;"
            "[void][System.Management.Automation.Language.Parser]::ParseFile("
            "(Resolve-Path 'install.ps1'),[ref]$tokens,[ref]$errors);"
            "if($errors.Count){$errors|%{$_.Message};exit 1}"
        )
        parsed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", command],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        assert parsed.returncode == 0, parsed.stdout + parsed.stderr


def create_distribution(
    repo: Path, root: Path, entries: list[tuple[str, str]], *, windows: bool
) -> Path:
    dist = root / "archive" / "freak"
    bin_dir = dist / "bin"
    bin_dir.mkdir(parents=True)
    extension = ".exe" if windows else ""
    (bin_dir / f"freak{extension}").write_bytes(b"mock-freak\n")
    (bin_dir / f"hangar{extension}").write_bytes(b"mock-hangar\n")
    for source, destination in entries:
        target = dist / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repo / source, target)
    shutil.copy2(
        repo / "packaging" / "distribution-files.manifest",
        dist / "distribution-files.manifest",
    )

    if windows:
        archive = root / "freak-test.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zipped:
            for path in dist.rglob("*"):
                if path.is_file():
                    zipped.write(path, path.relative_to(dist.parent))
    else:
        archive = root / "freak-test.tar.gz"
        with tarfile.open(archive, "w:gz") as tarred:
            tarred.add(dist, arcname="freak")
    return archive


def check_offline_installer(
    repo: Path, root: Path, archive: Path, entries: list[tuple[str, str]]
) -> None:
    install_root = root / "installed"
    (install_root / "std").mkdir(parents=True)
    (install_root / "std" / "retired.fk").write_text("stale", encoding="utf-8")
    env = os.environ.copy()
    env.update(
        {
            "FREAK_HOME": str(install_root),
            "FREAK_INSTALL_ARCHIVE": str(archive),
            "FREAK_RELEASE_TAG": "vtest",
            "FREAK_INSTALL_DEPS": "0",
            "FREAK_SKIP_PATH_UPDATE": "1",
        }
    )
    if sys.platform == "win32":
        command = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(repo / "install.ps1"),
            "-SkipDeps",
        ]
    else:
        command = ["bash", str(repo / "install.sh"), "--skip-deps"]
    installed = subprocess.run(
        command,
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=120,
    )
    assert installed.returncode == 0, installed.stdout + installed.stderr
    assert not (install_root / "std" / "retired.fk").exists()
    assert (install_root / "distribution-files.manifest").is_file()
    for source, destination in entries:
        assert (install_root / destination).read_bytes() == (repo / source).read_bytes()
    extension = ".exe" if sys.platform == "win32" else ""
    assert (install_root / "bin" / f"freak{extension}").is_file()
    assert (install_root / "bin" / f"hangar{extension}").is_file()


def run_cli(
    compiler: Path, cwd: Path, env: dict[str, str], *args: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(compiler), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=180,
        check=False,
    )


def populate_payload(
    repo: Path, destination: Path, entries: list[tuple[str, str]]
) -> None:
    for source, installed in entries:
        target = destination / installed
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repo / source, target)


def check_doctor(
    repo: Path, root: Path, compiler: Path, entries: list[tuple[str, str]]
) -> None:
    payload = root / "doctor-home"
    populate_payload(repo, payload, entries)
    cwd = root / "doctor-cwd"
    cwd.mkdir()
    env = os.environ.copy()
    env["FREAK_HOME"] = str(payload)

    healthy = run_cli(compiler, cwd, env, "doctor", "--json")
    assert healthy.returncode == 0, healthy.stdout + healthy.stderr
    report = json.loads(healthy.stdout)
    assert report["status"] == "ok"
    assert report["checks"]["runtime"]["files_expected"] == 5
    assert report["checks"]["stdlib"]["modules_found"] == 11
    assert report["checks"]["stdlib"]["modules_expected"] == 11

    ui_module = payload / "std" / "ui" / "window.fk"
    ui_module.unlink()
    incomplete = run_cli(compiler, cwd, env, "doctor", "--json")
    assert incomplete.returncode != 0, incomplete.stdout + incomplete.stderr
    report = json.loads(incomplete.stdout)
    assert report["status"] == "issues"
    assert report["checks"]["stdlib"]["missing"] == "ui/window.fk"
    shutil.copy2(repo / "std" / "ui" / "window.fk", ui_module)

    full = run_cli(compiler, cwd, env, "doctor")
    assert full.returncode == 0, full.stdout + full.stderr
    assert "compile, link, and execution work" in full.stdout
    assert not list(cwd.glob("_freak_doctor_probe_*")), "doctor left probe artifacts"


def check_upgrade(root: Path, compiler: Path) -> None:
    env = os.environ.copy()
    upgrade_root = root / "upgrade-home"
    upgrade_root.mkdir()
    env["FREAK_HOME"] = str(upgrade_root)
    sentinel = upgrade_root / "upgrade-sentinel.txt"
    if sys.platform == "win32":
        fixture = root / "upgrade-fixture.ps1"
        fixture.write_text(
            "param([switch]$Upgrade,[switch]$SkipDeps)\n"
            "[IO.File]::WriteAllText((Join-Path $env:FREAK_HOME "
            "'upgrade-sentinel.txt'), \"$Upgrade|$SkipDeps|"
            "$env:FREAK_RELEASE_TAG|$env:FREAK_INSTALL_UPGRADE\")\n"
            "exit 0\n",
            encoding="utf-8",
        )
        failing = root / "upgrade-fail.ps1"
        failing.write_text("param([switch]$Upgrade,[switch]$SkipDeps)\nexit 7\n")
    else:
        fixture = root / "upgrade-fixture.sh"
        fixture.write_text(
            "#!/usr/bin/env bash\nset -e\n"
            "printf '%s|%s|%s' \"$FREAK_RELEASE_TAG\" "
            "\"$FREAK_HOME\" \"$*\" > \"$FREAK_HOME/upgrade-sentinel.txt\"\n",
            encoding="utf-8",
        )
        failing = root / "upgrade-fail.sh"
        failing.write_text("#!/usr/bin/env bash\nexit 7\n", encoding="utf-8")

    env["FREAK_UPGRADE_SCRIPT"] = str(fixture)
    upgraded = run_cli(compiler, root, env, "upgrade")
    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr
    assert sentinel.is_file(), upgraded.stdout
    assert "Upgrade payload staged successfully" in upgraded.stdout

    env["FREAK_UPGRADE_SCRIPT"] = str(failing)
    failed = run_cli(compiler, root, env, "upgrade")
    assert failed.returncode != 0, failed.stdout + failed.stderr
    assert "Upgrade failed" in failed.stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("freak", type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    compiler = args.freak.resolve()
    assert compiler.is_file(), compiler

    entries = manifest_entries(repo)
    check_manifest(repo, entries)
    check_static_contracts(repo)
    with tempfile.TemporaryDirectory(prefix="freak-v3-install-doctor-") as tmp:
        root = Path(tmp)
        archive = create_distribution(
            repo, root, entries, windows=sys.platform == "win32"
        )
        check_offline_installer(repo, root, archive, entries)
        check_doctor(repo, root, compiler, entries)
        check_upgrade(root, compiler)
    print("V3 install, doctor, and upgrade: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
