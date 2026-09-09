#!/usr/bin/env python3
"""Final release-shaped acceptance gate for the frozen self-hosted V3 compiler."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import zipfile
from pathlib import Path


def run(
    command: list[str],
    cwd: Path,
    env: dict[str, str],
    *,
    timeout: int = 240,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def show_output(result: subprocess.CompletedProcess[str]) -> str:
    return (result.stdout or "") + (result.stderr or "")


def require_ok(result: subprocess.CompletedProcess[str], label: str) -> None:
    assert result.returncode == 0, (
        f"{label} failed ({result.returncode})\n{show_output(result)}"
    )


def manifest_entries(repo: Path) -> list[tuple[Path, str]]:
    manifest = repo / "packaging" / "distribution-files.manifest"
    entries: list[tuple[Path, str]] = []
    seen: set[str] = set()
    for raw_line in manifest.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        source_text, separator, destination = line.partition("|")
        assert separator and source_text and destination, raw_line
        source_text = source_text.replace("\\", "/")
        destination = destination.replace("\\", "/")
        for value in (source_text, destination):
            parts = value.split("/")
            assert not value.startswith("/"), value
            assert not (len(value) >= 2 and value[0].isalpha() and value[1] == ":"), value
            assert all(part not in ("", ".", "..") for part in parts), value
        if source_text.startswith("freakc/runtime/"):
            assert destination == "runtime/" + source_text.removeprefix(
                "freakc/runtime/"
            ), (source_text, destination)
        else:
            assert source_text.startswith("std/"), source_text
            assert destination == source_text, (source_text, destination)
        source = (repo / source_text).resolve()
        source.relative_to(repo.resolve())
        assert source.is_file(), source
        assert destination not in seen, destination
        seen.add(destination)
        entries.append((source, destination))
    assert entries, "distribution manifest is empty"
    return entries


def compile_windows_runtime_objects(repo: Path, destination: Path, env: dict[str, str]) -> None:
    configured = env.get("FREAK_CLANG", "clang")
    clang = shutil.which(configured)
    assert clang, f"Clang not found for Windows release objects: {configured}"
    commands = (
        (
            repo / "freakc" / "runtime" / "freak_runtime.c",
            repo / "freakc" / "runtime",
            destination / "freak_runtime.obj",
            [],
        ),
        (
            repo / "freakc" / "runtime" / "freak_llvm_runtime.c",
            repo / "freakc" / "runtime",
            destination / "freak_llvm_runtime.obj",
            ["-DFREAK_HAS_UI"],
        ),
        (
            repo / "freakc" / "runtime" / "ui" / "win32_backend.c",
            repo / "freakc" / "runtime" / "ui",
            destination / "freak_ui_win32.obj",
            [],
        ),
    )
    for source, include, output, extra in commands:
        command = [
            clang,
            "-c",
            str(source),
            "-I",
            str(include),
            "-O2",
            "-w",
            "-D_CRT_SECURE_NO_WARNINGS",
            *extra,
            "-o",
            str(output),
        ]
        require_ok(run(command, repo, env), f"compile {output.name}")


def create_release_archive(
    *,
    repo: Path,
    root: Path,
    freak: Path,
    hangar: Path,
    entries: list[tuple[Path, str]],
    env: dict[str, str],
) -> Path:
    extension = ".exe" if sys.platform == "win32" else ""
    payload = root / "package" / "freak"
    bin_dir = payload / "bin"
    bin_dir.mkdir(parents=True)
    shutil.copy2(freak, bin_dir / f"freak{extension}")
    shutil.copy2(hangar, bin_dir / f"hangar{extension}")
    for source, destination in entries:
        target = payload / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    shutil.copy2(
        repo / "packaging" / "distribution-files.manifest",
        payload / "distribution-files.manifest",
    )

    if sys.platform == "win32":
        runtime = payload / "runtime"
        runtime.mkdir(exist_ok=True)
        compile_windows_runtime_objects(repo, runtime, env)
        archive = root / "freak-windows-x64.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
            for path in sorted(payload.rglob("*")):
                if path.is_file():
                    output.write(path, path.relative_to(payload.parent))
    else:
        machine = platform.machine().lower()
        arch = "arm64" if machine in ("arm64", "aarch64") else "x64"
        target = "macos" if sys.platform == "darwin" else "linux"
        archive = root / f"freak-{target}-{arch}.tar.gz"
        with tarfile.open(archive, "w:gz") as output:
            output.add(payload, arcname="freak")
    assert archive.is_file() and archive.stat().st_size > 0, archive
    return archive


def normalized_archive_member(raw_name: str) -> str:
    name = raw_name.replace("\\", "/")
    while name.startswith("./"):
        name = name[2:]
    name = name.rstrip("/")
    assert name and not name.startswith("/"), raw_name
    assert not (len(name) >= 2 and name[0].isalpha() and name[1] == ":"), raw_name
    assert all(part not in ("", ".", "..") for part in name.split("/")), raw_name
    return name


def archive_files(archive: Path) -> tuple[dict[str, bytes], set[str]]:
    files: dict[str, bytes] = {}
    directories: set[str] = set()
    if archive.suffix.lower() == ".zip":
        with zipfile.ZipFile(archive) as source:
            for info in source.infolist():
                name = normalized_archive_member(info.filename)
                mode = (info.external_attr >> 16) & 0o170000
                assert not stat.S_ISLNK(mode), (
                    f"release archive contains a symlink: {name}"
                )
                if info.is_dir():
                    assert name not in directories and name not in files, name
                    directories.add(name)
                    continue
                assert name not in files, name
                assert name not in directories, name
                files[name] = source.read(info)
    else:
        with tarfile.open(archive, "r:gz") as source:
            for member in source.getmembers():
                name = normalized_archive_member(member.name)
                if member.isdir():
                    assert name not in directories and name not in files, name
                    directories.add(name)
                    continue
                assert member.isfile(), f"release archive contains non-file member: {name}"
                handle = source.extractfile(member)
                assert handle is not None, name
                assert name not in files, name
                assert name not in directories, name
                files[name] = handle.read()
    return files, directories


def expected_archive_directories(files: set[str]) -> set[str]:
    result: set[str] = set()
    for name in files:
        parts = name.split("/")
        for depth in range(1, len(parts)):
            result.add("/".join(parts[:depth]))
    return result


def assert_archive_directory_closure(
    directories: set[str], files: set[str]
) -> None:
    allowed = expected_archive_directories(files)
    assert directories <= allowed, (
        f"release archive has unexpected directories: "
        f"{sorted(directories - allowed)}"
    )


def assert_archive_safety_controls(root: Path) -> None:
    traversal = root / "unsafe-directory-traversal.zip"
    with zipfile.ZipFile(traversal, "w") as output:
        output.writestr("../escape/", b"")
    try:
        archive_files(traversal)
    except AssertionError:
        pass
    else:
        raise AssertionError("archive traversal directory was accepted")

    unexpected = root / "unexpected-empty-directory.zip"
    with zipfile.ZipFile(unexpected, "w") as output:
        output.writestr("freak/extra/", b"")
    _, directories = archive_files(unexpected)
    try:
        assert_archive_directory_closure(directories, {"freak/bin/freak"})
    except AssertionError:
        pass
    else:
        raise AssertionError("unexpected archive directory was accepted")


def assert_archive_contract(
    archive: Path, entries: list[tuple[Path, str]], repo: Path
) -> dict[str, bytes]:
    extension = ".exe" if sys.platform == "win32" else ""
    expected = {
        f"freak/bin/freak{extension}",
        f"freak/bin/hangar{extension}",
        "freak/distribution-files.manifest",
        *(f"freak/{destination}" for _, destination in entries),
    }
    if sys.platform == "win32":
        expected.update(
            {
                "freak/runtime/freak_runtime.obj",
                "freak/runtime/freak_llvm_runtime.obj",
                "freak/runtime/freak_ui_win32.obj",
            }
        )
    files, directories = archive_files(archive)
    assert set(files) == expected, (
        f"release archive closure mismatch: missing={sorted(expected - set(files))} "
        f"extra={sorted(set(files) - expected)}"
    )
    assert_archive_directory_closure(directories, expected)
    assert all(files[name] for name in files), "release archive contains an empty file"
    assert files["freak/distribution-files.manifest"] == (
        repo / "packaging" / "distribution-files.manifest"
    ).read_bytes(), "release archive contains a stale distribution manifest"
    for source, destination in entries:
        assert files[f"freak/{destination}"] == source.read_bytes(), destination
    return files


def installer_command(repo: Path) -> list[str]:
    if sys.platform == "win32":
        return [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(repo / "install.ps1"),
            "-SkipDeps",
        ]
    return ["bash", str(repo / "install.sh"), "--skip-deps"]


def install_archive(
    *, repo: Path, root: Path, archive: Path, env: dict[str, str]
) -> tuple[Path, dict[str, str]]:
    install_home = root / "installed"
    install_env = env.copy()
    install_env.update(
        {
            "FREAK_HOME": str(install_home),
            "FREAK_INSTALL_ARCHIVE": str(archive),
            "FREAK_RELEASE_TAG": "vfinal-release-gate",
            "FREAK_INSTALL_DEPS": "0",
            "FREAK_SKIP_PATH_UPDATE": "1",
            "NO_COLOR": "1",
        }
    )
    installed = run(installer_command(repo), root, install_env, timeout=300)
    require_ok(installed, "install exact release archive")
    return install_home, install_env


def assert_installed_payload(
    *,
    archive_files_by_name: dict[str, bytes],
    install_home: Path,
    entries: list[tuple[Path, str]],
) -> tuple[Path, Path]:
    extension = ".exe" if sys.platform == "win32" else ""
    freak = install_home / "bin" / f"freak{extension}"
    hangar = install_home / "bin" / f"hangar{extension}"
    assert freak.read_bytes() == archive_files_by_name[f"freak/bin/freak{extension}"]
    assert hangar.read_bytes() == archive_files_by_name[f"freak/bin/hangar{extension}"]
    assert (install_home / "distribution-files.manifest").read_bytes() == (
        archive_files_by_name["freak/distribution-files.manifest"]
    )
    for _, destination in entries:
        assert (install_home / destination).read_bytes() == (
            archive_files_by_name[f"freak/{destination}"]
        )
    if sys.platform == "win32":
        for name in (
            "freak_runtime.obj",
            "freak_llvm_runtime.obj",
            "freak_ui_win32.obj",
        ):
            assert (install_home / "runtime" / name).read_bytes() == (
                archive_files_by_name[f"freak/runtime/{name}"]
            )
    expected = archive_payload_fingerprint(archive_files_by_name)
    actual = payload_fingerprint(install_home)
    assert actual == expected, (
        "installed payload closure mismatch: "
        f"missing={sorted(set(expected) - set(actual))} "
        f"extra={sorted(set(actual) - set(expected))}"
    )
    return freak, hangar


def isolated_runtime_env(root: Path, inherited: dict[str, str]) -> dict[str, str]:
    env = inherited.copy()
    env.pop("FREAK_HOME", None)
    env["NO_COLOR"] = "1"
    for name in ("HOME", "APPDATA", "LOCALAPPDATA", "USERPROFILE"):
        location = root / f"empty-{name.lower()}"
        location.mkdir(exist_ok=True)
        env[name] = str(location)
    if sys.platform == "win32":
        for name in ("ProgramFiles", "ProgramFiles(x86)"):
            location = root / f"empty-{name.lower().replace('(', '-').replace(')', '')}"
            location.mkdir(exist_ok=True)
            env[name] = str(location)
    return env


def assert_exact_installed_discovery(
    *, freak: Path, hangar: Path, install_home: Path, root: Path, env: dict[str, str]
) -> None:
    hostile = root / "hostile-repo-shaped-cwd"
    for directory in (
        hostile / "runtime",
        hostile / "std",
        hostile / "src" / "compiler" / "v3",
    ):
        directory.mkdir(parents=True, exist_ok=True)
    (hostile / "runtime" / "freak_abi").write_text("hostile-runtime\n", encoding="utf-8")
    (hostile / "std" / "freak_abi").write_text("hostile-stdlib\n", encoding="utf-8")
    (hostile / "std" / "math.fk").write_text("say )\n", encoding="utf-8")
    (hostile / "src" / "compiler" / "v3" / "main.fk").write_text(
        "say )\n", encoding="utf-8"
    )

    doctor_json = run([str(freak), "doctor", "--json"], hostile, env, timeout=300)
    require_ok(doctor_json, "installed doctor JSON")
    report = json.loads(doctor_json.stdout)
    assert report["status"] == "ok", report
    assert Path(report["checks"]["runtime"]["path"]).resolve() == (
        install_home / "runtime"
    ).resolve()
    assert Path(report["checks"]["stdlib"]["path"]).resolve() == (
        install_home / "std"
    ).resolve()
    doctor = run([str(freak), "doctor"], hostile, env, timeout=300)
    require_ok(doctor, "installed doctor full pipeline")
    assert "compile, link, and execution work" in doctor.stdout

    hello = hostile / "installed_hello.fk"
    hello.write_text('say "FINAL_RELEASE_INSTALLED_OK"\n', encoding="utf-8")
    built = run([str(freak), "build", str(hello)], hostile, env, timeout=300)
    require_ok(built, "installed compiler build")
    if sys.platform == "win32":
        assert "Linking packaged Windows runtime objects" in built.stdout
    binary = hello.with_suffix(".exe" if sys.platform == "win32" else "")
    executed = run([str(binary)], hostile, env)
    require_ok(executed, "installed compiler executable")
    assert executed.stdout.strip() == "FINAL_RELEASE_INSTALLED_OK"

    compiler_version = run([str(freak), "version"], hostile, env)
    hangar_version = run([str(hangar), "--version"], hostile, env)
    require_ok(compiler_version, "installed compiler version")
    require_ok(hangar_version, "installed Hangar version")
    assert compiler_version.stdout.strip() == hangar_version.stdout.strip()
    print("PASS exact installed binary + executable-adjacent Doctor discovery")


def assert_installed_abi_mismatch(
    *, freak: Path, install_home: Path, root: Path, env: dict[str, str]
) -> None:
    source = root / "abi_mismatch.fk"
    source.write_text('say "must not compile"\n', encoding="utf-8")
    binary = source.with_suffix(".exe" if sys.platform == "win32" else "")
    outputs = (
        Path(str(source) + ".c"),
        Path(str(source) + ".ll"),
        binary,
        Path(str(binary) + ".freak-run-cache"),
    )
    for component in ("runtime", "std"):
        bad_home = root / f"abi-mismatch-{component}"
        shutil.copytree(install_home / "runtime", bad_home / "runtime")
        shutil.copytree(install_home / "std", bad_home / "std")
        (bad_home / component / "freak_abi").write_text(
            "freak-v3-abi-stale\n", encoding="utf-8"
        )
        bad_env = env.copy()
        bad_env["FREAK_HOME"] = str(bad_home)
        for backend in ("--c", "--llvm"):
            for output_path in outputs:
                output_path.unlink(missing_ok=True)
            rejected = run([str(freak), "build", str(source), backend], root, bad_env)
            output = show_output(rejected)
            assert rejected.returncode != 0, output
            assert "abi mismatch" in output.lower(), output
            assert not any(path.exists() for path in outputs), outputs
        doctor = run([str(freak), "doctor", "--json"], root, bad_env)
        assert doctor.returncode != 0, show_output(doctor)
        assert json.loads(doctor.stdout)["status"] == "issues"
    print("PASS installed runtime/std ABI mismatch fail-closed gates")


def payload_fingerprint(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}

    def visit(directory: Path, prefix: str = "") -> None:
        for entry in sorted(os.scandir(directory), key=lambda item: item.name):
            relative = f"{prefix}/{entry.name}" if prefix else entry.name
            if entry.is_symlink():
                result[relative] = f"symlink:{os.readlink(entry.path)}"
            elif entry.is_dir(follow_symlinks=False):
                result[relative] = "directory"
                visit(Path(entry.path), relative)
            elif entry.is_file(follow_symlinks=False):
                digest = hashlib.sha256(Path(entry.path).read_bytes()).hexdigest()
                result[relative] = f"file:{digest}"
            else:
                result[relative] = f"special:{stat.S_IFMT(os.lstat(entry.path).st_mode)}"

    visit(root)
    return result


def archive_payload_fingerprint(files: dict[str, bytes]) -> dict[str, str]:
    result: dict[str, str] = {}
    for archive_name, data in sorted(files.items()):
        assert archive_name.startswith("freak/"), archive_name
        relative = archive_name.removeprefix("freak/")
        parts = relative.split("/")
        for depth in range(1, len(parts)):
            result["/".join(parts[:depth])] = "directory"
        result[relative] = f"file:{hashlib.sha256(data).hexdigest()}"
    return result


def assert_exact_archive_upgrade(
    *,
    repo: Path,
    freak: Path,
    install_home: Path,
    archive: Path,
    archive_payload: dict[str, bytes],
    entries: list[tuple[Path, str]],
    root: Path,
    env: dict[str, str],
) -> None:
    upgrade_env = env.copy()
    upgrade_env.update(
        {
            "FREAK_HOME": str(install_home),
            "FREAK_INSTALL_ARCHIVE": str(archive),
            "FREAK_RELEASE_TAG": "vfinal-release-gate",
            "FREAK_INSTALL_DEPS": "0",
            "FREAK_SKIP_PATH_UPDATE": "1",
            "FREAK_UPGRADE_SCRIPT": str(
                repo / ("install.ps1" if sys.platform == "win32" else "install.sh")
            ),
        }
    )
    rollback_sentinel = install_home / "std" / "rollback-sentinel.fk"
    rollback_sentinel.write_text("preserve rollback state\n", encoding="utf-8")
    before = payload_fingerprint(install_home)
    failed_env = upgrade_env.copy()
    failed_env["FREAK_INSTALL_TEST_FAIL_APPLY"] = "1"
    failed = run([str(freak), "upgrade"], root, failed_env, timeout=300)
    failed_output = show_output(failed)
    assert failed.returncode != 0, failed_output
    assert "restored" in failed_output.lower() or "upgrade failed" in failed_output.lower(), (
        failed_output
    )
    assert payload_fingerprint(install_home) == before, (
        "failed exact-archive upgrade did not restore the previous payload"
    )

    extension = ".exe" if sys.platform == "win32" else ""
    installed_hangar = install_home / "bin" / f"hangar{extension}"
    installed_hangar.write_bytes(
        installed_hangar.read_bytes() + b"\nFREAK_FINAL_GATE_STALE_HANGAR\n"
    )
    assert installed_hangar.read_bytes() != archive_payload[
        f"freak/bin/hangar{extension}"
    ], "successful-upgrade binary replacement precondition was not established"

    if sys.platform == "win32":
        retry_observed = root / "windows-upgrade-retry-observed.txt"
        pending_cleanup_ready = root / "windows-upgrade-pending-cleanup-ready.txt"
        pending_cleanup_release = root / "windows-upgrade-pending-cleanup-release.txt"
        upgrade_env["FREAK_INSTALL_TEST_HELPER_START_DELAY_MS"] = "1500"
        upgrade_env["FREAK_INSTALL_TEST_RETIRED_CLEANUP_FAILURES"] = "205"
        upgrade_env["FREAK_INSTALL_TEST_TERMINAL_CLEANUP_FAILURES"] = "205"
        upgrade_env["FREAK_INSTALL_TEST_RETRY_OBSERVED"] = str(retry_observed)
        upgrade_env["FREAK_INSTALL_TEST_PENDING_CLEANUP_READY"] = str(
            pending_cleanup_ready
        )
        upgrade_env["FREAK_INSTALL_TEST_PENDING_CLEANUP_RELEASE"] = str(
            pending_cleanup_release
        )
    succeeded = run([str(freak), "upgrade"], root, upgrade_env, timeout=300)
    require_ok(succeeded, "successful exact-archive upgrade")
    assert "Upgrade payload staged successfully" in succeeded.stdout

    bin_dir = install_home / "bin"
    pending = bin_dir / ".freak-upgrade-pending"
    if sys.platform == "win32":
        try:
            ready_deadline = time.monotonic() + 120
            while (
                not pending_cleanup_ready.exists()
                and time.monotonic() < ready_deadline
            ):
                time.sleep(0.1)
            assert pending_cleanup_ready.exists(), (
                "deferred helper never reached the terminal shared-lock window"
            )
            assert pending.exists(), "terminal shared-lock window did not retain pending"
            assert not (bin_dir / ".freak-upgrade-helper.lock").exists(), (
                "terminal shared-lock barrier fired before helper-lock cleanup"
            )
            assert not (bin_dir / ".freak-upgrade-helper.ready").exists(), (
                "terminal shared-lock barrier fired before helper-ready cleanup"
            )
            contender = run([str(freak), "upgrade"], root, upgrade_env, timeout=120)
        finally:
            pending_cleanup_release.write_text("release\n", encoding="utf-8")
        contender_output = show_output(contender).lower()
        assert contender.returncode != 0, contender_output
        assert "another freak installer" in contender_output, contender_output
    if pending.exists():
        guarded = run([str(freak), "doctor", "--json"], root, upgrade_env)
        guarded_report = json.loads(guarded.stdout)
        if guarded.returncode == 0:
            assert not pending.exists(), (
                "Doctor accepted an upgrade that was still durably pending"
            )
        else:
            assert guarded_report["checks"]["upgrade"]["pending"] is True
    deadline = time.monotonic() + 180
    durable_state = (
        pending,
        bin_dir / ".freak-upgrade-failed",
        bin_dir / ".freak-upgrade-helper.lock",
        bin_dir / ".freak-upgrade-helper.ready",
        bin_dir / "freak.exe.next",
        bin_dir / "hangar.exe.next",
    )
    while any(path.exists() for path in durable_state) and time.monotonic() < deadline:
        time.sleep(0.25)
    assert not [path for path in durable_state if path.exists()], durable_state
    if sys.platform == "win32":
        observed = retry_observed.read_text(encoding="utf-8-sig")
        assert "retired binary cleanup did not complete" in observed, observed
        assert "terminal transaction cleanup did not complete" in observed, observed
    assert not rollback_sentinel.exists(), "successful upgrade retained stale std payload"
    assert_installed_payload(
        archive_files_by_name=archive_payload,
        install_home=install_home,
        entries=entries,
    )
    healthy = run([str(freak), "doctor", "--json"], root, upgrade_env, timeout=300)
    require_ok(healthy, "post-upgrade installed Doctor")
    assert json.loads(healthy.stdout)["status"] == "ok"
    print("PASS exact-archive rollback + public upgrade routing")


def run_child_gate(
    *, label: str, command: list[str], repo: Path, cwd: Path, env: dict[str, str], timeout: int
) -> None:
    result = run(command, cwd, env, timeout=timeout)
    require_ok(result, label)
    output = show_output(result).strip()
    if output:
        print(output)
    print(f"PASS final component [{label}]")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("freak", nargs="?", type=Path)
    parser.add_argument("hangar", nargs="?", type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--freakc", required=True, type=Path)
    parser.add_argument("--standalone-freak", type=Path)
    parser.add_argument("--standalone-hangar", type=Path)
    parser.add_argument("--tested-sha256", type=Path)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    direct = args.freakc.resolve()
    assert direct.is_file(), f"current direct V3 compiler is required: {direct}"
    if args.archive is not None:
        assert args.freak is None and args.hangar is None
        supplied_archive = args.archive.resolve()
        assert supplied_archive.is_file(), supplied_archive
        assert args.standalone_freak is not None
        assert args.standalone_hangar is not None
        standalone_freak = args.standalone_freak.resolve()
        standalone_hangar = args.standalone_hangar.resolve()
        assert standalone_freak.is_file(), standalone_freak
        assert standalone_hangar.is_file(), standalone_hangar
        assert args.tested_sha256 is not None
    else:
        assert args.freak is not None and args.hangar is not None
        freak = args.freak.resolve()
        hangar = args.hangar.resolve()
        assert freak.is_file(), freak
        assert hangar.is_file(), hangar
        supplied_archive = None
        standalone_freak = freak
        standalone_hangar = hangar

    entries = manifest_entries(repo)
    base_env = os.environ.copy()
    base_env["NO_COLOR"] = "1"
    with tempfile.TemporaryDirectory(prefix="freak-v3-final-release-") as temporary:
        root = Path(temporary)
        assert_archive_safety_controls(root)
        archive = supplied_archive or create_release_archive(
            repo=repo,
            root=root,
            freak=freak,
            hangar=hangar,
            entries=entries,
            env=base_env,
        )
        archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
        archive_payload = assert_archive_contract(archive, entries, repo)
        extension = ".exe" if sys.platform == "win32" else ""
        assert archive_payload[f"freak/bin/freak{extension}"] == (
            standalone_freak.read_bytes()
        )
        assert archive_payload[f"freak/bin/hangar{extension}"] == (
            standalone_hangar.read_bytes()
        )
        install_home, install_env = install_archive(
            repo=repo, root=root, archive=archive, env=base_env
        )
        installed_freak, installed_hangar = assert_installed_payload(
            archive_files_by_name=archive_payload,
            install_home=install_home,
            entries=entries,
        )
        assert hashlib.sha256(archive.read_bytes()).hexdigest() == archive_hash

        isolated_env = isolated_runtime_env(root, install_env)
        assert_exact_installed_discovery(
            freak=installed_freak,
            hangar=installed_hangar,
            install_home=install_home,
            root=root,
            env=isolated_env,
        )
        assert_installed_abi_mismatch(
            freak=installed_freak,
            install_home=install_home,
            root=root,
            env=isolated_env,
        )

        python = sys.executable
        golden_poison = root / "golden-inherited-poison"
        golden_poison.mkdir()
        golden_env = isolated_env.copy()
        golden_env["FREAK_HOME"] = str(golden_poison)
        run_child_gate(
            label="legacy golden corpus",
            command=[
                python,
                "-u",
                str(repo / "tests" / "v3_legacy_golden.py"),
                str(installed_freak),
                "--internal-child",
                "--expected-poison",
                str(golden_poison),
            ],
            repo=repo,
            cwd=root / "hostile-repo-shaped-cwd",
            env=golden_env,
            timeout=900,
        )
        children = (
            (
                "negative parser/type corpus",
                [
                    python,
                    "-u",
                    str(repo / "tests" / "v3_codegen_error_gate.py"),
                    str(installed_freak),
                    "--freakc",
                    str(direct),
                ],
                1800,
            ),
            (
                "word ownership suite",
                [
                    python,
                    "-u",
                    str(repo / "tests" / "v3_word_ownership.py"),
                    str(installed_freak),
                    "--runtime-root",
                    str(install_home / "runtime"),
                ],
                1800,
            ),
            (
                "concat scaling suite",
                [
                    python,
                    "-u",
                    str(repo / "tests" / "v3_word_concat.py"),
                    str(installed_freak),
                    "--runtime-root",
                    str(install_home / "runtime"),
                ],
                1200,
            ),
        )
        children += tuple(
            (
                label,
                [
                    python, "-u", str(repo / "tests" / script),
                    str(installed_freak), "--runtime-root",
                    str(install_home / "runtime"),
                ],
                1200,
            )
            for label, script in (
                ("word repetition and builder", "v3_word_foundation.py"),
                ("Word embedded-NUL parity", "v3_word_length_parity.py"),
                ("strict builtin handle borrows", "v3_strict_handle_borrows.py"),
                ("bounded benchmark inputs", "v3_benchmark_bounds.py"),
                ("managed ByteBuffer", "v3_byte_buffer_foundation.py"),
                ("system runtime", "v3_system_runtime_foundation.py"),
                ("managed TCP sockets", "v3_tcp_socket_foundation.py"),
                ("HTTP server Ordnance", "v3_http_server_ordnance.py"),
                ("UI clipping mechanisms", "v3_ui_clipping.py"),
                ("COCKPIT widgets and native lifecycle", "v3_cockpit_compat.py"),
                ("Ordnance import hygiene", "v3_ordnance_import_hygiene.py"),
                ("standard-library capability", "v3_std_capability.py"),
            )
        )
        hostile_cwd = root / "hostile-repo-shaped-cwd"
        for label, command, timeout in children:
            run_child_gate(
                label=label,
                command=command,
                repo=repo,
                cwd=hostile_cwd,
                env=isolated_env,
                timeout=timeout,
            )
        assert_exact_archive_upgrade(
            repo=repo,
            freak=installed_freak,
            install_home=install_home,
            archive=archive,
            archive_payload=archive_payload,
            entries=entries,
            root=root,
            env=isolated_env,
        )
        assert hashlib.sha256(archive.read_bytes()).hexdigest() == archive_hash

        if args.tested_sha256 is not None:
            tested_sha = args.tested_sha256.resolve()
            tested_sha.parent.mkdir(parents=True, exist_ok=True)
            tested_sha.write_text(
                f"{archive_hash}  {archive.name}\n", encoding="utf-8"
            )

    print("V3 FINAL RELEASE GATE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
