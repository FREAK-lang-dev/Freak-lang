#!/usr/bin/env python3
"""V3 distribution, installer, doctor, and upgrade regression coverage."""

from __future__ import annotations

import argparse
import functools
import hashlib
import http.server
import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import urllib.request
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
        source = source.replace("\\", "/")
        destination = destination.replace("\\", "/")
        for value, prefixes in (
            (source, ("freakc/runtime/", "std/")),
            (destination, ("runtime/", "std/")),
        ):
            parts = value.split("/")
            assert not value.startswith("/"), value
            assert not (len(value) >= 2 and value[0].isalpha() and value[1] == ":"), value
            assert all(part not in ("", ".", "..") for part in parts), value
            assert value.startswith(prefixes), value
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
            "freakc/runtime/freak_abi",
            "std/freak_abi",
        }
    )
    assert actual_sources == expected_sources, (
        f"manifest missing={sorted(expected_sources - actual_sources)} "
        f"extra={sorted(actual_sources - expected_sources)}"
    )
    for source, _ in entries:
        assert (repo / source).is_file(), source

    doctor_text = (repo / "src" / "cli" / "doctor.fk").read_text(encoding="utf-8")
    runtime_destinations = []
    std_destinations = []
    for _, destination in entries:
        if destination.startswith("runtime/"):
            relative = destination.removeprefix("runtime/")
            runtime_destinations.append(relative)
        else:
            relative = destination.removeprefix("std/")
            if destination != "std/freak_abi":
                std_destinations.append(relative)
        assert f'"{relative}"' in doctor_text, (
            f"doctor inventory does not cover manifest destination {destination}"
        )
    assert f'"files_expected\\\": {len(runtime_destinations)}' in doctor_text
    assert f'"modules_expected\\\": {len(std_destinations)}' in doctor_text


def check_static_contracts(repo: Path) -> None:
    """
    Validate static contracts across installers, release and CI workflows, compiler CLI sources, and repository attributes.
    
    Parameters:
        repo (Path): Repository root containing the files and scripts to validate.
    """
    shell_text = (repo / "install.sh").read_text(encoding="utf-8")
    ps_text = (repo / "install.ps1").read_text(encoding="utf-8")
    release_text = (repo / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    )
    ci_text = (repo / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    attributes_text = (repo / ".gitattributes").read_text(encoding="utf-8")
    hangar_text = (repo / "src" / "cli" / "hangar.fk").read_text(
        encoding="utf-8"
    )
    doctor_text = (repo / "src" / "cli" / "doctor.fk").read_text(
        encoding="utf-8"
    )
    build_text = (repo / "src" / "cli" / "build.fk").read_text(
        encoding="utf-8"
    )
    main_text = (repo / "src" / "cli" / "main.fk").read_text(encoding="utf-8")

    for needle in (
        "--with-deps",
        "FREAK_INSTALL_ARCHIVE",
        "FREAK_INSTALL_DEP_COMMAND",
        "FREAK_INSTALL_TEST_FAIL_RESTORE",
        "freak-clang-probe",
        ".freak-backup-",
        "TRANSACTION_ACTIVE",
        "reconcile_orphaned_transaction",
        "packaging/distribution-files.manifest",
        "restore_previous_payload",
        "verify_downloaded_asset",
        "SHA256SUMS",
        ".freak-install.lock",
        ".freak-stale-takeover",
        "FREAK_INSTALL_TEST_NO_PROCESS_START_TOKEN",
        "FREAK_INSTALL_TEST_PAUSE_BEFORE_LOCK_PUBLISH",
        "FREAK_INSTALL_TEST_PAUSE_AFTER_STALE_BREAKER",
        "Another FREAK installer",
    ):
        assert needle in shell_text, f"install.sh missing {needle}"
    assert 'ln -- "$INSTALL_LOCK_PREPARED" "$candidate"' in shell_text
    assert 'ln -- "$INSTALL_LOCK_PREPARED" "$breaker"' in shell_text
    assert "| awk '{ print $1 }' || true" in shell_text
    assert 'mkdir -- "$candidate"' not in shell_text, (
        "POSIX installer ownership must be complete before atomic publication"
    )
    recovery_call = shell_text.rindex("\nreconcile_orphaned_transaction\n")
    release_lookup = shell_text.index('info "Fetching latest release..."')
    staging_start = shell_text.index('ARCHIVE_PATH="$TMPDIR_INSTALL/freak.tar.gz"')
    assert recovery_call < release_lookup < staging_start, (
        "POSIX orphan recovery must run before release lookup and staging"
    )
    for needle in (
        "MartinStorsjo.LLVM-MinGW.UCRT",
        "scoop.cmd install llvm-mingw",
        "Test-ClangToolchain",
        "& $binary",
        "FREAK_INSTALL_ARCHIVE",
        "Start-DeferredBinaryReplacement",
        ".freak-upgrade-pending",
        ".freak-binary-backup",
        "freak-sha256=",
        "expectedHashes",
        "Get-Process -Id",
        "Get-FileHash",
        ".freak-backup-",
        "FREAK_INSTALL_TEST_FAIL_APPLY",
        "distribution-files.manifest",
        "Assert-DownloadedAssetChecksum",
        "SHA256SUMS",
        ".freak-install.lock",
        "FileShare]::None",
        "wait-start=",
        ".freak-upgrade-helper.lock",
        ".freak-upgrade-helper.ready",
        "FREAK_INSTALL_TEST_HELPER_START_DELAY_MS",
        "DeferredHelperUnsafe",
        "Recover-OrphanedDeferredUpgrade",
        "Recover-OrphanedPayloadTransaction",
        "LegacyV014Archive",
        "FREAK_INSTALL_TEST_PAUSE_AFTER_BACKUP",
    ):
        assert needle in ps_text, f"install.ps1 missing {needle}"
    assert "choco.exe install llvm" not in ps_text
    retired_cleanup = ps_text.rindex(
        "Remove-Item -LiteralPath `$retiredRoot -Recurse -Force"
    )
    failed_cleanup = ps_text.index(
        "Remove-Item -LiteralPath `$failed -Force", retired_cleanup
    )
    pending_cleanup = ps_text.index(
        "Remove-Item -LiteralPath `$pending -Force", failed_cleanup
    )
    assert retired_cleanup < failed_cleanup < pending_cleanup, (
        "deferred Windows upgrade must remove pending only after transaction cleanup"
    )
    unsafe_helper_guard = ps_text.index("if ($script:DeferredHelperUnsafe)")
    unsafe_helper_abort = ps_text.index(
        'Err "Could not safely roll back while the deferred binary helper remains active',
        unsafe_helper_guard,
    )
    rollback_next_cleanup = ps_text.index(
        'Remove-Item -LiteralPath "$BinDir\\freak.exe.next"', unsafe_helper_guard
    )
    assert unsafe_helper_guard < unsafe_helper_abort < rollback_next_cleanup, (
        "an unconfirmed live Windows helper must block pending/.next rollback"
    )
    for needle in (
        "packaging/distribution-files.manifest",
        "dist/freak/distribution-files.manifest",
        "dist/freak-${{ matrix.target }}${{ matrix.ext }}",
        "dist/hangar-${{ matrix.target }}${{ matrix.ext }}",
        "Pre-compile Windows runtime objects",
        "freak_runtime.obj dist/freak/runtime/",
        "freak_llvm_runtime.obj dist/freak/runtime/",
        "freak_ui_win32.obj dist/freak/runtime/",
        "LLVM_MINGW_SHA256",
        "freakc_v3_stage2",
        "raw/packaging/distribution-files.manifest",
        "Finalize and smoke exact release archive",
        "v3_final_release_gate.py",
        '--archive "$archive"',
        "--freakc",
        "--standalone-freak",
        "--standalone-hangar",
        "--tested-sha256",
        '! -name "*.tested.sha256"',
        '$2 == "freak-macos-arm64.tar.gz"',
        "sha256sum",
    ):
        assert needle in release_text, f"release workflow missing {needle}"
    assert "destination=${destination%$'\\r'}" in release_text
    assert 'read -r source destination || [[ -n "$source$destination" ]]' in release_text
    assert "freakc_v3_stage2" in ci_text
    assert "tests/v3_fixed_point.py" in ci_text
    assert release_text.index("Collect finalized release archives") < release_text.index(
        "Generate checksums"
    )
    assert "artifacts/package-manager/freak.rb" in release_text
    assert 'cp "$WINGET_DIR"/*.yaml artifacts/package-manager/winget/' in release_text
    assert "required WinGet manifest missing" in release_text
    assert "unresolved WinGet placeholder" in release_text
    assert "dist/freak/runtime/freak_runtime.o" not in release_text
    assert "packaging/distribution-files.manifest text eol=lf" in attributes_text
    assert 'doc["checks"]["stdlib"]["modules_expected"] == 11' in ci_text
    for needle in (
        "task hangar_install_freak() -> int",
        "FREAK_UPGRADE_SCRIPT",
        "migration limitations",
        "tagged installer",
    ):
        assert needle in hangar_text, f"upgrade path missing {needle}"
    for needle in (
        "modules_expected\\\": 11",
        "ui/window.fk",
        "scoop install llvm-mingw",
        "FREAK_DOCTOR_INSTALL_COMMAND",
        'process::env("TMPDIR")',
        'pilot probe_nonce: word = ""',
        "FREAK_DOCTOR_TEST_PROBE_ID",
        "FREAK_DOCTOR_TEST_FAIL_FIRST_REMOVE",
        "FREAK_DOCTOR_TEST_RETAIN_PROBE",
        "cleanup_retained",
        "cli_quote_cmd_path(probe_source)",
        "probe_run_exit == 0",
        "give back probe_ok",
        "pending_marker = cli_pending_upgrade_marker()",
        "clang toolchain ",
        "compile, link, and execution work",
        "task cli_doctor(fix_mode: bool) -> int",
    ):
        assert needle in doctor_text, f"doctor missing {needle}"
    assert "choco install llvm" not in doctor_text
    for needle in (
        "task cli_posix_canonical_executable(path: word) -> word",
        "if link_hops >= 32",
        'pilot lookup_target = "$PATH:" + argv0',
        "if resolved == \"\" or not fs::exists(resolved)",
        'if not resolved.contains("/")',
        "CLI_PAYLOAD_ERROR_PREFIX",
        "task cli_payload_is_resolution_error(value: word) -> bool",
        "task cli_is_repo_checkout_root(root: word) -> bool",
        "task cli_windows_cwd_is_shell_fallback(cwd: word) -> bool",
        "PAYLOAD RESOLUTION FAILED",
        "if not fs::exists(absolute) { give back \"\" }",
    ):
        assert needle in build_text, f"executable discovery missing {needle}"
    assert build_text.count(
        'cli_executable_path() != "" and cli_is_repo_payload_root(".")'
    ) == 2, "unresolved executable identity must disable both CWD payload fallbacks"
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
    manifest_text = (repo / "packaging" / "distribution-files.manifest").read_text(
        encoding="utf-8"
    )
    (dist / "distribution-files.manifest").write_bytes(
        manifest_text.replace("\n", "\r\n").rstrip("\r\n").encode("utf-8")
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


class QuietHttpHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


def check_downloaded_archive_checksum(repo: Path, root: Path, archive: Path) -> None:
    command = (
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
    if sys.platform == "win32":
        target = "freak-windows-x64.zip"
    else:
        platform_tag = "macos" if sys.platform == "darwin" else "linux"
        machine = platform.machine().lower()
        if machine in {"aarch64", "arm64"}:
            arch_tag = "arm64"
        elif machine in {"amd64", "x86_64"}:
            arch_tag = "x64"
        else:
            raise AssertionError(f"unsupported installer test architecture: {machine}")
        target = f"freak-{platform_tag}-{arch_tag}.tar.gz"

    if target == "freak-macos-x64.tar.gz":
        unsupported_env = os.environ.copy()
        unsupported_env.update(
            {
                "FREAK_HOME": str(root / "unsupported-macos-x64"),
                "FREAK_INSTALL_ARCHIVE": str(archive),
                "FREAK_INSTALL_DEPS": "0",
                "FREAK_SKIP_PATH_UPDATE": "1",
            }
        )
        unsupported = subprocess.run(
            command, cwd=repo, env=unsupported_env, capture_output=True, text=True,
            errors="replace", timeout=120,
        )
        unsupported_output = unsupported.stdout + unsupported.stderr
        assert unsupported.returncode != 0, unsupported_output
        assert "intel macos is not available" in unsupported_output.lower(), unsupported_output
        return

    release_root = root / "release-server"
    release = release_root / "vchecksum"
    release.mkdir(parents=True)
    served_archive = release / target
    shutil.copy2(archive, served_archive)
    expected = hashlib.sha256(served_archive.read_bytes()).hexdigest()
    (release / "SHA256SUMS").write_text(
        f"{expected}  ./{target}\n", encoding="utf-8"
    )

    # v0.14.0 shipped complete distribution archives but its SHA256SUMS lists
    # only extracted binary paths. Download the immutable historical archive,
    # verify the installer pin, and serve it with the original checksum shape.
    legacy_archive_hashes = {
        "freak-linux-x64.tar.gz": "dac2920e7bf2e4a1ce9a6a5394cdddbb2c92ed68aa587c25249e78bee4ac7bcb",
        "freak-linux-arm64.tar.gz": "eae4b954e8b361788e7c4fc1c077fa259b842d9cf2b125348b5c490fb44dd0b0",
        "freak-macos-arm64.tar.gz": "484bbca735c020b4e53e3824bb414677f05cf8b1ef93c78963dc238440e7ec51",
        "freak-windows-x64.zip": "4d1f43eb79838a100010b6b2d6a303921d75f6b0a5f947ee0104d86de3783699",
    }
    legacy_binary_hashes = {
        "freak-linux-x64.tar.gz": "5b5050ae040a6c2018715653e0d5e2cd4b9ec166df83386f5efdedde4595a459",
        "freak-linux-arm64.tar.gz": "c79234b76d4f93c12a39d00b19b510461e502f5aa104d37aeeea1b1d32a9f591",
        "freak-macos-arm64.tar.gz": "b33ef38d187814675c73ceb4e6e3fb5068836fb458ce69ad75042af04abd447a",
        "freak-windows-x64.zip": "8c80ce8df63e05162343032c26684f574c9abbc1e03d23ac560a82cd02075a36",
    }
    legacy_release = release_root / "v0.14.0"
    legacy_release.mkdir()
    legacy_archive = legacy_release / target
    assert target in legacy_archive_hashes and target in legacy_binary_hashes, target
    # Offline/restricted runners can pre-seed this exact asset. It remains
    # subject to the production immutable hash; a missing download is never
    # converted into a skipped compatibility assertion.
    prefetched_legacy = os.environ.get("FREAK_TEST_V014_ARCHIVE")
    if prefetched_legacy:
        shutil.copy2(Path(prefetched_legacy).expanduser().resolve(), legacy_archive)
    else:
        legacy_url = (
            "https://github.com/FREAK-lang-dev/Freak-lang/releases/download/"
            f"v0.14.0/{target}"
        )
        with urllib.request.urlopen(legacy_url, timeout=60) as response:
            legacy_archive.write_bytes(response.read())
    assert hashlib.sha256(legacy_archive.read_bytes()).hexdigest() == legacy_archive_hashes[target]
    if sys.platform == "win32":
        legacy_bundle = "freak-windows-x64"
        legacy_freak = "freak-windows-x64.exe"
        legacy_hangar = "hangar-windows-x64.exe"
    else:
        legacy_bundle = target.removesuffix(".tar.gz")
        legacy_freak = legacy_bundle
        legacy_hangar = legacy_bundle.replace("freak-", "hangar-", 1)
    legacy_binary_hash = legacy_binary_hashes[target]
    (legacy_release / "SHA256SUMS").write_text(
        f"{legacy_binary_hash}  ./{legacy_bundle}/{legacy_freak}\n"
        f"{legacy_binary_hash}  ./{legacy_bundle}/{legacy_hangar}\n",
        encoding="utf-8",
    )

    handler = functools.partial(QuietHttpHandler, directory=str(release_root))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base_env = os.environ.copy()
        base_env.update(
            {
                "FREAK_RELEASE_BASE": f"http://127.0.0.1:{server.server_port}",
                "FREAK_RELEASE_TAG": "vchecksum",
                "FREAK_INSTALL_DEPS": "0",
                "FREAK_SKIP_PATH_UPDATE": "1",
            }
        )
        legacy_env = base_env.copy()
        legacy_root = root / "legacy-v014-install"
        legacy_env.update(
            {"FREAK_RELEASE_TAG": "v0.14.0", "FREAK_HOME": str(legacy_root)}
        )
        legacy = subprocess.run(
            command,
            cwd=repo,
            env=legacy_env,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=120,
        )
        legacy_output = legacy.stdout + legacy.stderr
        assert legacy.returncode == 0, legacy_output
        assert "pinned immutable archive hash" in legacy_output.lower(), legacy_output
        assert "generated a compatibility manifest" in legacy_output.lower(), legacy_output
        assert (legacy_root / "distribution-files.manifest").is_file()
        assert (legacy_root / "runtime" / "freak_runtime.c").is_file()
        assert (legacy_root / "std" / "math.fk").is_file()

        valid_env = base_env.copy()
        valid_root = root / "checksum-valid"
        valid_env["FREAK_HOME"] = str(valid_root)
        verified = subprocess.run(
            command,
            cwd=repo,
            env=valid_env,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=120,
        )
        assert verified.returncode == 0, verified.stdout + verified.stderr
        assert "Verified SHA-256" in verified.stdout

        # Conflicting duplicate entries are ambiguous and must fail closed on
        # both installers before touching an existing payload.
        (release / "SHA256SUMS").write_text(
            f"{expected}  ./{target}\n{'0' * 64}  {target}\n", encoding="utf-8"
        )
        duplicate_root = root / "checksum-duplicate"
        duplicate_sentinel = duplicate_root / "std" / "preserve.fk"
        duplicate_sentinel.parent.mkdir(parents=True)
        duplicate_sentinel.write_bytes(b"old payload\n")
        duplicate_env = base_env.copy()
        duplicate_env["FREAK_HOME"] = str(duplicate_root)
        duplicate = subprocess.run(
            command,
            cwd=repo,
            env=duplicate_env,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=120,
        )
        assert duplicate.returncode != 0, duplicate.stdout + duplicate.stderr
        assert "duplicate entries" in (duplicate.stdout + duplicate.stderr).lower()
        assert duplicate_sentinel.read_bytes() == b"old payload\n"
        (release / "SHA256SUMS").write_text(
            f"{expected}  ./{target}\n", encoding="utf-8"
        )

        # Keep SHA256SUMS fixed while replacing the served archive. Integrity
        # failure must happen before extraction or any live-tree mutation.
        served_archive.write_bytes(served_archive.read_bytes() + b"tampered\n")
        rejected_root = root / "checksum-rejected"
        sentinel = rejected_root / "std" / "preserve.fk"
        sentinel.parent.mkdir(parents=True)
        sentinel.write_bytes(b"old payload\n")
        rejected_env = base_env.copy()
        rejected_env["FREAK_HOME"] = str(rejected_root)
        rejected = subprocess.run(
            command,
            cwd=repo,
            env=rejected_env,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=120,
        )
        assert rejected.returncode != 0, rejected.stdout + rejected.stderr
        assert "sha256 mismatch" in (rejected.stdout + rejected.stderr).lower()
        assert sentinel.read_bytes() == b"old payload\n"

        # Exercise the archive-missing compatibility path with the same exact
        # hash contract. The manifest deliberately has no final newline.
        fallback_release = release_root / "vfallback"
        fallback_raw = release_root / "raw"
        fallback_release.mkdir()
        if sys.platform == "win32":
            freak_asset = "freak-windows-x64.exe"
            hangar_asset = "hangar-windows-x64.exe"
        else:
            platform_tag = "macos" if sys.platform == "darwin" else "linux"
            machine = platform.machine().lower()
            arch_tag = "arm64" if machine in {"aarch64", "arm64"} else "x64"
            freak_asset = f"freak-{platform_tag}-{arch_tag}"
            hangar_asset = f"hangar-{platform_tag}-{arch_tag}"
        (fallback_release / freak_asset).write_bytes(b"standalone freak\n")
        (fallback_release / hangar_asset).write_bytes(b"standalone hangar\n")
        manifest_bytes = (repo / "packaging" / "distribution-files.manifest").read_bytes().rstrip(b"\r\n")
        raw_manifest = fallback_raw / "packaging" / "distribution-files.manifest"
        raw_manifest.parent.mkdir(parents=True)
        raw_manifest.write_bytes(manifest_bytes)
        checksum_lines: list[str] = []
        for asset in (freak_asset, hangar_asset):
            asset_path = fallback_release / asset
            checksum_lines.append(f"{hashlib.sha256(asset_path.read_bytes()).hexdigest()}  {asset}")
        for source, _ in manifest_entries(repo):
            raw_target = fallback_raw / source
            raw_target.parent.mkdir(parents=True, exist_ok=True)
            raw_target.write_bytes((repo / source).read_bytes())
            checksum_lines.append(
                f"{hashlib.sha256(raw_target.read_bytes()).hexdigest()}  raw/{source}"
            )
        checksum_lines.append(
            f"{hashlib.sha256(manifest_bytes).hexdigest()}  raw/packaging/distribution-files.manifest"
        )
        (fallback_release / "SHA256SUMS").write_text(
            "\n".join(sorted(checksum_lines)) + "\n", encoding="utf-8"
        )
        fallback_env = base_env.copy()
        fallback_env.update(
            {
                "FREAK_RELEASE_TAG": "vfallback",
                "FREAK_RAW_BASE": f"http://127.0.0.1:{server.server_port}/raw",
                "FREAK_HOME": str(root / "fallback-valid"),
            }
        )
        fallback = subprocess.run(
            command, cwd=repo, env=fallback_env, capture_output=True, text=True,
            errors="replace", timeout=120,
        )
        assert fallback.returncode == 0, fallback.stdout + fallback.stderr
        assert fallback.stdout.count("Verified SHA-256") >= 3 + len(manifest_entries(repo))

        tampered_source = fallback_raw / manifest_entries(repo)[0][0]
        tampered_source.write_bytes(tampered_source.read_bytes() + b"tampered\n")
        fallback_rejected_root = root / "fallback-rejected"
        fallback_sentinel = fallback_rejected_root / "std" / "preserve.fk"
        fallback_sentinel.parent.mkdir(parents=True)
        fallback_sentinel.write_bytes(b"old fallback payload\n")
        fallback_env["FREAK_HOME"] = str(fallback_rejected_root)
        fallback_rejected = subprocess.run(
            command, cwd=repo, env=fallback_env, capture_output=True, text=True,
            errors="replace", timeout=120,
        )
        assert fallback_rejected.returncode != 0, (
            fallback_rejected.stdout + fallback_rejected.stderr
        )
        assert "sha256 mismatch" in (
            fallback_rejected.stdout + fallback_rejected.stderr
        ).lower()
        assert fallback_sentinel.read_bytes() == b"old fallback payload\n"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def check_offline_installer(
    repo: Path, root: Path, archive: Path, entries: list[tuple[str, str]]
) -> None:
    """
    Validate offline installation, transactional upgrade, recovery, locking, and dependency behavior across platforms.
    
    Parameters:
    	repo (Path): Repository containing the installer scripts and distribution files.
    	root (Path): Temporary directory for installation fixtures and test state.
    	archive (Path): Locally generated distribution archive to install.
    	entries (list[tuple[str, str]]): Manifest source and destination pairs used to verify installed files.
    """
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

    if sys.platform == "win32":
        # Hold the old compiler without delete sharing. The installer must
        # return a staged status, retain durable pending state, then replace
        # both binaries transactionally after the lock is released.
        import ctypes.wintypes

        deferred_root = root / "deferred-upgrade"
        deferred_bin = deferred_root / "bin"
        deferred_bin.mkdir(parents=True)
        old_freak = deferred_bin / "freak.exe"
        old_hangar = deferred_bin / "hangar.exe"
        old_freak.write_bytes(b"old locked freak\n")
        old_hangar.write_bytes(b"old hangar\n")
        deferred_runtime = deferred_root / "runtime"
        deferred_runtime.mkdir()
        deferred_runtime_sentinel = deferred_runtime / "freak_runtime.c"
        deferred_runtime_sentinel.write_bytes(b"old runtime before pending barrier\n")

        create_file = ctypes.windll.kernel32.CreateFileW
        create_file.argtypes = [
            ctypes.wintypes.LPCWSTR, ctypes.wintypes.DWORD,
            ctypes.wintypes.DWORD, ctypes.wintypes.LPVOID,
            ctypes.wintypes.DWORD, ctypes.wintypes.DWORD,
            ctypes.wintypes.HANDLE,
        ]
        create_file.restype = ctypes.wintypes.HANDLE
        close_handle = ctypes.windll.kernel32.CloseHandle
        close_handle.argtypes = [ctypes.wintypes.HANDLE]
        close_handle.restype = ctypes.wintypes.BOOL
        open_process = ctypes.windll.kernel32.OpenProcess
        open_process.argtypes = [
            ctypes.wintypes.DWORD, ctypes.wintypes.BOOL, ctypes.wintypes.DWORD,
        ]
        open_process.restype = ctypes.wintypes.HANDLE
        wait_for_single_object = ctypes.windll.kernel32.WaitForSingleObject
        wait_for_single_object.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD]
        wait_for_single_object.restype = ctypes.wintypes.DWORD

        install_lock_path = install_root / ".freak-install.lock"
        install_lock_handle = create_file(
            str(install_lock_path), 0xC0000000, 0, None, 4, 0x00000080, None
        )
        assert install_lock_handle != ctypes.wintypes.HANDLE(-1).value
        runtime_before_lock_test = (install_root / "runtime" / "freak_runtime.c").read_bytes()
        try:
            contender = subprocess.run(
                command, cwd=repo, env=env, capture_output=True, text=True,
                errors="replace", timeout=30,
            )
            assert contender.returncode != 0, contender.stdout + contender.stderr
            assert "another freak installer" in (
                contender.stdout + contender.stderr
            ).lower()
            assert (install_root / "runtime" / "freak_runtime.c").read_bytes() == runtime_before_lock_test
        finally:
            assert close_handle(install_lock_handle)
            install_lock_path.unlink(missing_ok=True)

        lock_handle = create_file(
            str(old_freak), 0x80000000, 0x00000001, None, 3, 0x00000080, None
        )
        assert lock_handle != ctypes.wintypes.HANDLE(-1).value
        deferred_env = env.copy()
        deferred_env["FREAK_HOME"] = str(deferred_root)
        pending_ready = root / "windows-pending-ready.txt"
        deferred_env["FREAK_INSTALL_TEST_PAUSE_AFTER_PENDING"] = "1"
        deferred_env["FREAK_INSTALL_TEST_PENDING_READY"] = str(pending_ready)
        try:
            staged_process = subprocess.Popen(
                [*command, "-Upgrade"], cwd=repo, env=deferred_env,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                errors="replace",
            )
            pending_deadline = time.monotonic() + 15
            while time.monotonic() < pending_deadline and not pending_ready.exists():
                if staged_process.poll() is not None:
                    break
                time.sleep(0.1)
            assert pending_ready.is_file()
            assert (deferred_bin / ".freak-upgrade-pending").is_file()
            assert deferred_runtime_sentinel.read_bytes() == b"old runtime before pending barrier\n"
            staged_stdout, staged_stderr = staged_process.communicate(timeout=120)
            assert staged_process.returncode == 0, staged_stdout + staged_stderr
            assert "payload staged successfully" in staged_stdout
            time.sleep(1.5)
            assert (deferred_bin / ".freak-upgrade-pending").is_file()
            assert (deferred_bin / "freak.exe.next").is_file()
            assert old_freak.read_bytes() == b"old locked freak\n"
            # Expected hashes are captured before the helper starts. Corrupt a
            # staged binary while the live compiler is locked and prove the
            # helper rejects it without moving either old binary.
            (deferred_bin / "hangar.exe.next").write_bytes(b"tampered\n")
        finally:
            assert close_handle(lock_handle)

        failure_deadline = time.monotonic() + 30
        failure_detail = ""
        while time.monotonic() < failure_deadline:
            if (deferred_bin / ".freak-upgrade-failed").is_file():
                failure_detail = (deferred_bin / ".freak-upgrade-failed").read_text(
                    encoding="utf-8-sig"
                )
                if "staged binary hash mismatch" in failure_detail:
                    break
            time.sleep(0.25)
        assert "staged binary hash mismatch" in failure_detail, failure_detail
        assert old_freak.read_bytes() == b"old locked freak\n"
        assert old_hangar.read_bytes() == b"old hangar\n"
        assert not (deferred_bin / ".freak-binary-backup").exists()
        (deferred_bin / "hangar.exe.next").write_bytes(b"mock-hangar\n")

        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if not (deferred_bin / ".freak-upgrade-pending").exists():
                break
            time.sleep(0.25)
        assert not (deferred_bin / ".freak-upgrade-pending").exists()
        assert not (deferred_bin / ".freak-upgrade-failed").exists()
        assert not (deferred_bin / ".freak-binary-backup").exists()
        assert not (deferred_bin / ".freak-binary-retired").exists()
        assert not (deferred_bin / ".freak-upgrade-helper.lock").exists()
        assert not (deferred_bin / ".freak-upgrade-helper.ready").exists()
        assert not (deferred_bin / "freak.exe.next").exists()
        assert not (deferred_bin / "hangar.exe.next").exists()
        assert old_freak.read_bytes() == b"mock-freak\n"
        assert old_hangar.read_bytes() == b"mock-hangar\n"

        # A helper that cannot authenticate itself within the bounded startup
        # window must be killed before transaction state is rolled back. A
        # later invocation must then succeed without a delayed orphan racing
        # it after pending/.next state has been removed.
        delayed_root = root / "delayed-helper-start"
        delayed_bin = delayed_root / "bin"
        delayed_bin.mkdir(parents=True)
        delayed_freak = delayed_bin / "freak.exe"
        delayed_hangar = delayed_bin / "hangar.exe"
        delayed_freak.write_bytes(b"delayed old freak\n")
        delayed_hangar.write_bytes(b"delayed old hangar\n")
        delayed_lock = create_file(
            str(delayed_freak), 0x80000000, 0x00000001, None, 3, 0x00000080, None
        )
        assert delayed_lock != ctypes.wintypes.HANDLE(-1).value
        delayed_env = env.copy()
        delayed_env["FREAK_HOME"] = str(delayed_root)
        delayed_env["FREAK_INSTALL_TEST_HELPER_START_DELAY_MS"] = "7000"
        delayed_helper_pid_path = root / "delayed-helper-pid.txt"
        delayed_env["FREAK_INSTALL_TEST_HELPER_PID"] = str(delayed_helper_pid_path)
        try:
            delayed = subprocess.run(
                [*command, "-Upgrade"], cwd=repo, env=delayed_env,
                capture_output=True, text=True, errors="replace", timeout=120,
            )
        finally:
            assert close_handle(delayed_lock)
        delayed_output = delayed.stdout + delayed.stderr
        assert delayed.returncode != 0, delayed_output
        assert "helper did not become ready" in delayed_output.lower()
        assert delayed_helper_pid_path.is_file()
        delayed_helper_pid = int(
            delayed_helper_pid_path.read_text(encoding="utf-8-sig").strip()
        )
        helper_dead = subprocess.run(
            [
                "powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                f"if (Get-Process -Id {delayed_helper_pid} -ErrorAction SilentlyContinue) {{ exit 1 }}",
            ],
            capture_output=True, text=True, errors="replace", timeout=30,
        )
        assert helper_dead.returncode == 0, helper_dead.stdout + helper_dead.stderr
        for state_name in (
            ".freak-upgrade-pending",
            ".freak-upgrade-failed",
            ".freak-upgrade-helper.lock",
            ".freak-upgrade-helper.ready",
            ".freak-binary-backup",
            "freak.exe.next",
            "hangar.exe.next",
        ):
            assert not (delayed_bin / state_name).exists(), state_name
        assert delayed_freak.read_bytes() == b"delayed old freak\n"
        assert delayed_hangar.read_bytes() == b"delayed old hangar\n"
        assert not (delayed_root / "runtime").exists()
        assert not (delayed_root / "std").exists()

        delayed_env.pop("FREAK_INSTALL_TEST_HELPER_START_DELAY_MS")
        delayed_env.pop("FREAK_INSTALL_TEST_HELPER_PID")
        delayed_retry = subprocess.run(
            [*command, "-Upgrade"], cwd=repo, env=delayed_env,
            capture_output=True, text=True, errors="replace", timeout=120,
        )
        assert delayed_retry.returncode == 0, (
            delayed_retry.stdout + delayed_retry.stderr
        )
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if not (delayed_bin / ".freak-upgrade-pending").exists():
                break
            time.sleep(0.25)
        assert not (delayed_bin / ".freak-upgrade-pending").exists()
        assert not (delayed_bin / ".freak-upgrade-helper.lock").exists()
        assert not (delayed_bin / ".freak-upgrade-helper.ready").exists()
        assert delayed_freak.read_bytes() == b"mock-freak\n"
        assert delayed_hangar.read_bytes() == b"mock-hangar\n"

        # A killed deferred helper must not strand the installation forever.
        # A live helper still excludes contenders; once killed, the next
        # installer restores any binary backup, keeps the pending guard, and
        # commits a fresh hash-bound deferred transaction.
        orphan_root = root / "orphaned-deferred-upgrade"
        orphan_bin = orphan_root / "bin"
        orphan_bin.mkdir(parents=True)
        orphan_freak = orphan_bin / "freak.exe"
        orphan_hangar = orphan_bin / "hangar.exe"
        orphan_freak.write_bytes(b"orphan old freak\n")
        orphan_hangar.write_bytes(b"orphan old hangar\n")
        orphan_lock = create_file(
            str(orphan_freak), 0x80000000, 0x00000001, None, 3, 0x00000080, None
        )
        assert orphan_lock != ctypes.wintypes.HANDLE(-1).value
        helper_pid_path = root / "orphan-helper-pid.txt"
        orphan_env = env.copy()
        orphan_env["FREAK_HOME"] = str(orphan_root)
        orphan_env["FREAK_INSTALL_TEST_HELPER_PID"] = str(helper_pid_path)
        helper_pid = None
        try:
            orphan_staged = subprocess.run(
                [*command, "-Upgrade"], cwd=repo, env=orphan_env,
                capture_output=True, text=True, errors="replace", timeout=120,
            )
            if helper_pid_path.is_file():
                helper_pid = int(
                    helper_pid_path.read_text(encoding="utf-8-sig").strip()
                )
            assert orphan_staged.returncode == 0, (
                orphan_staged.stdout + orphan_staged.stderr
            )
            assert helper_pid is not None
            assert (orphan_bin / ".freak-upgrade-pending").is_file()
            live_contender = subprocess.run(
                [*command, "-Upgrade"], cwd=repo, env=orphan_env,
                capture_output=True, text=True, errors="replace", timeout=30,
            )
            assert live_contender.returncode != 0, (
                live_contender.stdout + live_contender.stderr
            )
            contender_output = (live_contender.stdout + live_contender.stderr).lower()
            assert (
                "replacement helper is still active" in contender_output
                or "another freak installer" in contender_output
            ), contender_output
        finally:
            try:
                if helper_pid is not None:
                    terminated = subprocess.run(
                        ["taskkill.exe", "/PID", str(helper_pid), "/F"],
                        capture_output=True, text=True, errors="replace", timeout=30,
                    )
                    process_handle = open_process(0x00100000, False, helper_pid)
                    if process_handle:
                        try:
                            assert wait_for_single_object(process_handle, 10_000) == 0, (
                                terminated.stdout + terminated.stderr
                            )
                        finally:
                            assert close_handle(process_handle)
            finally:
                assert close_handle(orphan_lock)

        orphan_env.pop("FREAK_INSTALL_TEST_HELPER_PID")
        resumed = subprocess.run(
            [*command, "-Upgrade"], cwd=repo, env=orphan_env,
            capture_output=True, text=True, errors="replace", timeout=120,
        )
        assert resumed.returncode == 0, resumed.stdout + resumed.stderr
        assert "Recovered an orphaned deferred upgrade" in resumed.stdout
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if not (orphan_bin / ".freak-upgrade-pending").exists():
                break
            time.sleep(0.25)
        assert not (orphan_bin / ".freak-upgrade-pending").exists()
        assert not (orphan_bin / ".freak-upgrade-failed").exists()
        assert not (orphan_bin / ".freak-upgrade-helper.lock").exists()
        assert not (orphan_bin / ".freak-upgrade-helper.ready").exists()
        assert orphan_freak.read_bytes() == b"mock-freak\n"
        assert orphan_hangar.read_bytes() == b"mock-hangar\n"

    # Invalid downloads and failures after the first live-tree swap must both
    # leave the exact previous installation recoverable.
    preserved_root = root / "preserved-install"
    preserved_files = {
        Path("bin") / f"freak{extension}": b"old-freak\n",
        Path("bin") / f"hangar{extension}": b"old-hangar\n",
        Path("runtime") / "freak_runtime.c": b"old-runtime\n",
        Path("std") / "math.fk": b"old-stdlib\n",
        Path("distribution-files.manifest"): b"old-manifest\n",
    }
    for relative, contents in preserved_files.items():
        target = preserved_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(contents)

    invalid_archive = root / ("invalid.zip" if sys.platform == "win32" else "invalid.tar.gz")
    invalid_archive.write_bytes(b"not a distribution archive")
    failure_env = env.copy()
    failure_env["FREAK_HOME"] = str(preserved_root)
    failure_env["FREAK_INSTALL_ARCHIVE"] = str(invalid_archive)
    rejected = subprocess.run(
        command, cwd=repo, env=failure_env, capture_output=True, text=True,
        errors="replace", timeout=120,
    )
    assert rejected.returncode != 0, rejected.stdout + rejected.stderr
    for relative, contents in preserved_files.items():
        assert (preserved_root / relative).read_bytes() == contents

    unsafe_dist = root / "unsafe-archive" / "freak"
    unsafe_bin = unsafe_dist / "bin"
    unsafe_bin.mkdir(parents=True)
    (unsafe_bin / f"freak{extension}").write_bytes(b"unsafe fixture freak\n")
    (unsafe_bin / f"hangar{extension}").write_bytes(b"unsafe fixture hangar\n")
    (unsafe_dist / "runtime").mkdir()
    (unsafe_dist / "std").mkdir()
    (unsafe_dist / "runtime" / "placeholder").write_bytes(b"runtime\n")
    (unsafe_dist / "std" / "placeholder").write_bytes(b"std\n")
    (unsafe_dist / "distribution-files.manifest").write_text(
        "std/math.fk|std/..", encoding="utf-8"
    )
    unsafe_archive = root / (
        "unsafe-manifest.zip" if sys.platform == "win32" else "unsafe-manifest.tar.gz"
    )
    if sys.platform == "win32":
        with zipfile.ZipFile(unsafe_archive, "w", zipfile.ZIP_DEFLATED) as zipped:
            for path in unsafe_dist.rglob("*"):
                if path.is_file():
                    zipped.write(path, path.relative_to(unsafe_dist.parent))
    else:
        with tarfile.open(unsafe_archive, "w:gz") as tarred:
            tarred.add(unsafe_dist, arcname="freak")
    unsafe_env = failure_env.copy()
    unsafe_env["FREAK_INSTALL_ARCHIVE"] = str(unsafe_archive)
    unsafe = subprocess.run(
        command, cwd=repo, env=unsafe_env, capture_output=True, text=True,
        errors="replace", timeout=120,
    )
    assert unsafe.returncode != 0, unsafe.stdout + unsafe.stderr
    unsafe_output = unsafe.stdout + unsafe.stderr
    assert "unsafe distribution" in unsafe_output.lower(), unsafe_output
    for relative, contents in preserved_files.items():
        assert (preserved_root / relative).read_bytes() == contents

    failure_env["FREAK_INSTALL_ARCHIVE"] = str(archive)
    failure_env["FREAK_INSTALL_TEST_FAIL_APPLY"] = "1"
    rolled_back = subprocess.run(
        command, cwd=repo, env=failure_env, capture_output=True, text=True,
        errors="replace", timeout=120,
    )
    assert rolled_back.returncode != 0, rolled_back.stdout + rolled_back.stderr
    for relative, contents in preserved_files.items():
        assert (preserved_root / relative).read_bytes() == contents
    assert not list(preserved_root.glob(".freak-apply-*"))
    assert not list(preserved_root.glob(".freak-backup-*"))

    if sys.platform == "win32":
        # A forced process death after every old path moved to backup bypasses
        # PowerShell finally/catch cleanup. The next installer must reconcile
        # that durable backup before beginning its own transaction.
        crash_ready = root / "windows-payload-crash-ready.txt"
        crash_env = failure_env.copy()
        crash_env.pop("FREAK_INSTALL_TEST_FAIL_APPLY")
        crash_env["FREAK_INSTALL_TEST_PAUSE_AFTER_BACKUP"] = "1"
        crash_env["FREAK_INSTALL_TEST_TRANSACTION_READY"] = str(crash_ready)
        crashed = subprocess.Popen(
            command, cwd=repo, env=crash_env, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, errors="replace",
        )
        try:
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline and not crash_ready.exists():
                if crashed.poll() is not None:
                    break
                time.sleep(0.1)
            assert crash_ready.is_file()
        finally:
            if crashed.poll() is None:
                terminated = subprocess.run(
                    ["taskkill.exe", "/PID", str(crashed.pid), "/T", "/F"],
                    capture_output=True, text=True, errors="replace", timeout=30,
                )
                assert terminated.returncode == 0, terminated.stdout + terminated.stderr
        crashed_stdout, crashed_stderr = crashed.communicate(timeout=30)
        assert crashed.returncode != 0, crashed_stdout + crashed_stderr
        assert len(list(preserved_root.glob(".freak-backup-*"))) == 1
        assert len(list(preserved_root.glob(".freak-apply-*"))) == 1
        for relative in preserved_files:
            assert not (preserved_root / relative).exists(), relative

        reconcile_env = crash_env.copy()
        reconcile_env.pop("FREAK_INSTALL_TEST_PAUSE_AFTER_BACKUP")
        reconcile_env.pop("FREAK_INSTALL_TEST_TRANSACTION_READY")
        reconcile_env["FREAK_INSTALL_TEST_FAIL_APPLY"] = "1"
        reconciled = subprocess.run(
            command, cwd=repo, env=reconcile_env, capture_output=True, text=True,
            errors="replace", timeout=120,
        )
        reconcile_output = reconciled.stdout + reconciled.stderr
        assert reconciled.returncode != 0, reconcile_output
        assert "Recovered the previous payload" in reconcile_output, reconcile_output
        for relative, contents in preserved_files.items():
            assert (preserved_root / relative).read_bytes() == contents
        assert not list(preserved_root.glob(".freak-apply-*"))
        assert not list(preserved_root.glob(".freak-backup-*"))

    if sys.platform != "win32":
        # Ownership metadata is complete before the shared lock is atomically
        # published. Pause one installer before publication, let a second
        # installer become the live owner using the pid-only fallback, then
        # release the first and prove it cannot overwrite the second owner.
        prepublish_ready = root / "installer-prepublish-ready.txt"
        prepublish_release = root / "installer-prepublish-release.txt"
        prepublish_env = env.copy()
        prepublish_env["FREAK_HOME"] = str(preserved_root)
        prepublish_env["FREAK_INSTALL_ARCHIVE"] = str(archive)
        prepublish_env["FREAK_INSTALL_TEST_PAUSE_BEFORE_LOCK_PUBLISH"] = "1"
        prepublish_env["FREAK_INSTALL_TEST_LOCK_PUBLISH_READY"] = str(
            prepublish_ready
        )
        prepublish_env["FREAK_INSTALL_TEST_LOCK_PUBLISH_RELEASE"] = str(
            prepublish_release
        )
        prepublisher = subprocess.Popen(
            command, cwd=repo, env=prepublish_env, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, errors="replace",
            start_new_session=True,
        )
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and not prepublish_ready.exists():
            if prepublisher.poll() is not None:
                break
            time.sleep(0.1)
        assert prepublish_ready.is_file(), prepublisher.communicate(timeout=5)

        transaction_ready = root / "installer-transaction-ready.txt"
        signal_env = env.copy()
        signal_env["FREAK_HOME"] = str(preserved_root)
        signal_env["FREAK_INSTALL_ARCHIVE"] = str(archive)
        signal_env["FREAK_INSTALL_TEST_PAUSE_AFTER_BACKUP"] = "1"
        signal_env["FREAK_INSTALL_TEST_TRANSACTION_READY"] = str(transaction_ready)
        signal_env["FREAK_INSTALL_TEST_NO_PROCESS_START_TOKEN"] = "1"
        interrupted = subprocess.Popen(
            command, cwd=repo, env=signal_env, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, errors="replace",
            start_new_session=True,
        )
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and not transaction_ready.exists():
            if interrupted.poll() is not None:
                break
            time.sleep(0.1)
        assert transaction_ready.is_file(), interrupted.communicate(timeout=5)
        prepublish_release.write_text("release\n", encoding="utf-8")
        contender_stdout, contender_stderr = prepublisher.communicate(timeout=30)
        assert prepublisher.returncode != 0, contender_stdout + contender_stderr
        assert "another freak installer" in (
            contender_stdout + contender_stderr
        ).lower()
        assert len(list(preserved_root.glob(".freak-backup-*"))) == 1
        os.killpg(interrupted.pid, signal.SIGTERM)
        interrupted_stdout, interrupted_stderr = interrupted.communicate(timeout=30)
        assert interrupted.returncode != 0, interrupted_stdout + interrupted_stderr
        for relative, contents in preserved_files.items():
            assert (preserved_root / relative).read_bytes() == contents
        assert not list(preserved_root.glob(".freak-apply-*"))
        assert not list(preserved_root.glob(".freak-backup-*"))

        # SIGKILL bypasses every shell trap. The next installer must prove the
        # recorded owner is dead, recover the stale lock, and reconcile the
        # only old payload backup before starting a new transaction.
        crash_ready = root / "installer-crash-ready.txt"
        crash_env = signal_env.copy()
        crash_env["FREAK_INSTALL_TEST_TRANSACTION_READY"] = str(crash_ready)
        crashed = subprocess.Popen(
            command, cwd=repo, env=crash_env, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, errors="replace",
            start_new_session=True,
        )
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and not crash_ready.exists():
            if crashed.poll() is not None:
                break
            time.sleep(0.1)
        assert crash_ready.is_file(), crashed.communicate(timeout=5)
        os.killpg(crashed.pid, signal.SIGKILL)
        crashed_stdout, crashed_stderr = crashed.communicate(timeout=30)
        assert crashed.returncode != 0, crashed_stdout + crashed_stderr
        assert (preserved_root / ".freak-install.lock").is_file()
        assert len(list(preserved_root.glob(".freak-backup-*"))) == 1

        # The stale-takeover election is itself durable. Kill its elected
        # owner before it can remove the stale lock, then require later
        # contenders to recover the orphaned breaker before electing one new
        # transaction owner.
        stale_breaker_ready = root / "stale-breaker-ready.txt"
        stale_breaker_env = signal_env.copy()
        stale_breaker_env["FREAK_INSTALL_TEST_PAUSE_AFTER_STALE_BREAKER"] = "1"
        stale_breaker_env["FREAK_INSTALL_TEST_STALE_BREAKER_READY"] = str(
            stale_breaker_ready
        )
        stale_breaker = subprocess.Popen(
            command, cwd=repo, env=stale_breaker_env, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, errors="replace",
            start_new_session=True,
        )
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and not stale_breaker_ready.exists():
            if stale_breaker.poll() is not None:
                break
            time.sleep(0.1)
        assert stale_breaker_ready.is_file(), stale_breaker.communicate(timeout=5)
        os.killpg(stale_breaker.pid, signal.SIGKILL)
        breaker_stdout, breaker_stderr = stale_breaker.communicate(timeout=30)
        assert stale_breaker.returncode != 0, breaker_stdout + breaker_stderr
        assert (
            preserved_root
            / ".freak-stale-takeover"
        ).is_file()

        race_processes: list[subprocess.Popen[str]] = []
        race_ready: list[Path] = []
        for contender_index in range(2):
            ready = root / f"stale-lock-race-{contender_index}.txt"
            race_ready.append(ready)
            race_env = signal_env.copy()
            race_env["FREAK_INSTALL_TEST_TRANSACTION_READY"] = str(ready)
            race_processes.append(
                subprocess.Popen(
                    command, cwd=repo, env=race_env, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, text=True, errors="replace",
                    start_new_session=True,
                )
            )
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if sum(path.exists() for path in race_ready) == 1 and any(
                process.poll() is not None for process in race_processes
            ):
                break
            time.sleep(0.1)
        assert sum(path.exists() for path in race_ready) == 1, race_ready
        winner_index = 0 if race_ready[0].exists() else 1
        loser_index = 1 - winner_index
        loser_stdout, loser_stderr = race_processes[loser_index].communicate(timeout=30)
        assert race_processes[loser_index].returncode != 0, loser_stdout + loser_stderr
        assert "another freak installer" in (
            loser_stdout + loser_stderr
        ).lower(), loser_stdout + loser_stderr
        os.killpg(race_processes[winner_index].pid, signal.SIGTERM)
        winner_stdout, winner_stderr = race_processes[winner_index].communicate(timeout=30)
        assert race_processes[winner_index].returncode != 0, winner_stdout + winner_stderr
        winner_output = winner_stdout + winner_stderr
        assert "Recovered interrupted stale-lock takeover" in winner_output
        assert "Recovered stale installer lock" in winner_output
        assert "Recovered the previous payload" in winner_output
        for relative, contents in preserved_files.items():
            assert (preserved_root / relative).read_bytes() == contents
        assert not (preserved_root / ".freak-install.lock").exists()
        assert not list(preserved_root.glob(".freak-apply-*"))
        assert not list(preserved_root.glob(".freak-backup-*"))

        # An ownerless legacy mkdir cannot be distinguished from a live old
        # installer stopped before publishing its owner. Fail closed and
        # preserve it for explicit recovery; never guess and create two owners.
        missing_owner_lock = preserved_root / ".freak-install.lock"
        missing_owner_lock.mkdir()
        missing_owner = subprocess.run(
            command, cwd=repo, env=failure_env, capture_output=True, text=True,
            errors="replace", timeout=120,
        )
        assert missing_owner.returncode != 0, missing_owner.stdout + missing_owner.stderr
        assert "ownerless legacy freak installer lock" in (
            missing_owner.stdout + missing_owner.stderr
        ).lower(), missing_owner.stdout + missing_owner.stderr
        assert missing_owner_lock.is_dir()
        missing_owner_lock.rmdir()

        # A live but reused PID is rejected as the old owner when its durable
        # process-start token differs.
        reused_pid_lock = preserved_root / ".freak-install.lock"
        reused_pid_lock.mkdir()
        (reused_pid_lock / "owner").write_text(
            f"{os.getpid()}|definitely-not-this-process-start|pid-reuse-fixture\n",
            encoding="utf-8",
        )
        reused_pid = subprocess.run(
            command, cwd=repo, env=failure_env, capture_output=True, text=True,
            errors="replace", timeout=120,
        )
        assert reused_pid.returncode != 0, reused_pid.stdout + reused_pid.stderr
        assert "Recovered stale installer lock" in reused_pid.stdout
        assert not reused_pid_lock.exists()

        # Never follow an attacker-controlled intermediate symlink while
        # inspecting or cleaning a stale lock owner.
        symlink_install = root / "symlink-lock-install"
        symlink_install.mkdir()
        external_lock = root / "external-lock-sentinel"
        external_lock.mkdir()
        external_owner = external_lock / "owner"
        external_owner.write_text("999999|dead|external-sentinel\n", encoding="utf-8")
        lock_symlink = symlink_install / ".freak-install.lock"
        lock_symlink.symlink_to(external_lock, target_is_directory=True)
        symlink_env = failure_env.copy()
        symlink_env["FREAK_HOME"] = str(symlink_install)
        symlink_attempt = subprocess.run(
            command, cwd=repo, env=symlink_env, capture_output=True, text=True,
            errors="replace", timeout=120,
        )
        assert symlink_attempt.returncode != 0, symlink_attempt.stdout + symlink_attempt.stderr
        assert "unsafe freak installer lock path" in (
            symlink_attempt.stdout + symlink_attempt.stderr
        ).lower(), symlink_attempt.stdout + symlink_attempt.stderr
        assert external_owner.read_text(encoding="utf-8").startswith("999999|")
        lock_symlink.unlink()

        # If restoration itself fails, never delete the only recoverable old
        # payload. Leave one explicit backup and remove only apply scratch.
        recovery_env = failure_env.copy()
        recovery_env["FREAK_INSTALL_TEST_FAIL_RESTORE"] = "1"
        recovery_failed = subprocess.run(
            command, cwd=repo, env=recovery_env, capture_output=True, text=True,
            errors="replace", timeout=120,
        )
        assert recovery_failed.returncode != 0, (
            recovery_failed.stdout + recovery_failed.stderr
        )
        recovery_backups = list(preserved_root.glob(".freak-backup-*"))
        assert len(recovery_backups) == 1, recovery_backups
        recovery_backup = recovery_backups[0]
        for relative, contents in preserved_files.items():
            assert (recovery_backup / relative).read_bytes() == contents
        assert not list(preserved_root.glob(".freak-apply-*"))

        # Recovery happens before any network staging. Even an immediately
        # unavailable release server must restore the old payload rather than
        # leave its only copy stranded in the durable backup.
        reconcile_env = recovery_env.copy()
        reconcile_env.pop("FREAK_INSTALL_TEST_FAIL_RESTORE")
        reconcile_env.pop("FREAK_INSTALL_ARCHIVE")
        reconcile_env["FREAK_RELEASE_BASE"] = "http://127.0.0.1:1"
        reconciled = subprocess.run(
            command, cwd=repo, env=reconcile_env, capture_output=True, text=True,
            errors="replace", timeout=120,
        )
        reconcile_output = reconciled.stdout + reconciled.stderr
        assert reconciled.returncode != 0, reconcile_output
        assert "Recovered the previous payload" in reconcile_output, reconcile_output
        for relative, contents in preserved_files.items():
            assert (preserved_root / relative).read_bytes() == contents
        assert not list(preserved_root.glob(".freak-apply-*"))
        assert not list(preserved_root.glob(".freak-backup-*"))

        broken_clang = root / "installer-version-only-clang.sh"
        broken_clang.write_text(
            "#!/usr/bin/env bash\n"
            'if [ "${1:-}" = "--version" ]; then exit 0; fi\n'
            "exit 1\n",
            encoding="utf-8",
        )
        broken_clang.chmod(0o755)
        dependency_sentinel = root / "installer-dependency-attempted.txt"
        dependency_env = env.copy()
        dependency_env["FREAK_HOME"] = str(root / "dependency-install")
        dependency_env["FREAK_CLANG"] = str(broken_clang)
        dependency_env["FREAK_INSTALL_DEPS"] = "1"
        dependency_env["FREAK_INSTALL_DEP_COMMAND"] = (
            f'printf attempted > "{dependency_sentinel}"'
        )
        dependency_command = ["bash", str(repo / "install.sh"), "--with-deps"]
        dependency_attempt = subprocess.run(
            dependency_command, cwd=repo, env=dependency_env, capture_output=True,
            text=True, errors="replace", timeout=120,
        )
        assert dependency_attempt.returncode != 0, (
            dependency_attempt.stdout + dependency_attempt.stderr
        )
        assert dependency_sentinel.is_file()

        output_only_clang = root / "installer-output-only-clang.sh"
        output_only_clang.write_text(
            "#!/usr/bin/env bash\n"
            'if [ "${1:-}" = "--version" ]; then echo "clang output-only fixture"; exit 0; fi\n'
            "output=''\n"
            "while [ $# -gt 0 ]; do\n"
            '  if [ "$1" = "-o" ]; then shift; output="$1"; break; fi\n'
            "  shift\n"
            "done\n"
            '[ -n "$output" ] || exit 1\n'
            'printf "not executable\\n" > "$output"\n'
            'chmod +x "$output"\n'
            "exit 0\n",
            encoding="utf-8",
        )
        output_only_clang.chmod(0o755)
        output_dependency_sentinel = root / "installer-output-dependency-attempted.txt"
        output_env = dependency_env.copy()
        output_env["FREAK_HOME"] = str(root / "output-dependency-install")
        output_env["FREAK_CLANG"] = str(output_only_clang)
        output_env["FREAK_INSTALL_DEP_COMMAND"] = (
            f'printf attempted > "{output_dependency_sentinel}"'
        )
        output_attempt = subprocess.run(
            dependency_command, cwd=repo, env=output_env, capture_output=True,
            text=True, errors="replace", timeout=120,
        )
        assert output_attempt.returncode != 0, output_attempt.stdout + output_attempt.stderr
        assert output_dependency_sentinel.is_file(), (
            "POSIX installer accepted a linked file that could not execute"
        )


def run_cli(
    compiler: Path | str, cwd: Path, env: dict[str, str], *args: str
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
    """
    Validate compiler diagnostics, payload discovery, ABI compatibility, toolchain probing, repair behavior, and upgrade-state handling across supported installation layouts and platforms.
    
    Parameters:
    	repo (Path): Repository containing the compiler, runtime, standard library, and manifest sources.
    	root (Path): Temporary directory used for test installations, fixtures, and probe artifacts.
    	compiler (Path): Path to the compiler executable used to run Doctor and build commands.
    	entries (list[tuple[str, str]]): Manifest source and destination pairs used to populate test payloads.
    """
    repo_compiler = compiler.resolve()
    assert repo_compiler.parent.parent == repo.resolve(), (
        "doctor discovery regression requires the real checkout compiler"
    )
    payload = root / "doctor-home"
    populate_payload(repo, payload, entries)
    # Model an archive/install layout with a second complete payload beside the
    # compiler. Explicit FREAK_HOME must still select the isolated test payload.
    checkout = root / "doctor-checkout"
    checkout_bin = checkout / "bin"
    checkout_bin.mkdir(parents=True)
    checkout_compiler = checkout_bin / compiler.name
    shutil.copy2(compiler, checkout_compiler)
    shutil.copytree(repo / "freakc" / "runtime", checkout / "runtime")
    shutil.copytree(repo / "std", checkout / "std")
    compiler = checkout_compiler
    cwd = root / "doctor-cwd"
    cwd.mkdir()
    probe_temp = root / "doctor-probes"
    probe_temp.mkdir()
    env = os.environ.copy()
    env["FREAK_HOME"] = str(payload)
    env["TEMP"] = str(probe_temp)
    env["TMP"] = str(probe_temp)
    env["TMPDIR"] = str(probe_temp)

    healthy = run_cli(compiler, cwd, env, "doctor", "--json")
    assert healthy.returncode == 0, healthy.stdout + healthy.stderr
    assert healthy.stderr == "", healthy.stderr
    report = json.loads(healthy.stdout)
    assert report["status"] == "ok"
    assert report["checks"]["clang"]["cleanup_retained"] == ""
    assert Path(report["checks"]["runtime"]["path"]).resolve() == (
        payload / "runtime"
    ).resolve()
    assert Path(report["checks"]["stdlib"]["path"]).resolve() == (
        payload / "std"
    ).resolve()
    assert report["checks"]["runtime"]["files_expected"] == 6
    assert report["checks"]["stdlib"]["modules_found"] == 11
    assert report["checks"]["stdlib"]["modules_expected"] == 11
    assert report["checks"]["abi"] == {
        "ok": True,
        "expected": "freak-v3-abi-1",
        "runtime": "freak-v3-abi-1",
        "stdlib": "freak-v3-abi-1",
    }
    assert report["checks"]["upgrade"]["pending"] is False

    # A complete-looking but mixed payload must fail before either backend
    # emits or links anything.
    abi_source = cwd / "abi_probe.fk"
    abi_source.write_text('say "abi"\n', encoding="utf-8")
    runtime_abi = payload / "runtime" / "freak_abi"
    runtime_abi.write_text("freak-v3-abi-999\n", encoding="utf-8")
    mismatched = run_cli(compiler, cwd, env, "doctor", "--json")
    assert mismatched.returncode != 0, mismatched.stdout + mismatched.stderr
    mismatch_report = json.loads(mismatched.stdout)
    assert mismatch_report["checks"]["abi"]["ok"] is False
    rejected_build = run_cli(compiler, cwd, env, "build", str(abi_source), "--c")
    assert rejected_build.returncode != 0, rejected_build.stdout + rejected_build.stderr
    assert "abi mismatch" in rejected_build.stdout.lower()
    assert not Path(str(abi_source) + ".c").exists()
    assert not abi_source.with_suffix(".exe").exists()
    assert not abi_source.with_suffix("").exists()
    shutil.copy2(repo / "freakc" / "runtime" / "freak_abi", runtime_abi)

    std_abi = payload / "std" / "freak_abi"
    std_abi.unlink()
    missing_abi = run_cli(compiler, cwd, env, "doctor", "--json")
    assert missing_abi.returncode != 0, missing_abi.stdout + missing_abi.stderr
    missing_report = json.loads(missing_abi.stdout)
    assert missing_report["checks"]["abi"]["stdlib"] == "missing"
    assert "freak_abi" in missing_report["checks"]["stdlib"]["missing"]
    shutil.copy2(repo / "std" / "freak_abi", std_abi)

    if sys.platform == "win32":
        pending = payload / "bin" / ".freak-upgrade-pending"
        pending.parent.mkdir(parents=True, exist_ok=True)
        pending.write_text("v0.14.1|wait-pid=fixture\n", encoding="utf-8")
        pending_doctor = run_cli(compiler, cwd, env, "doctor", "--json")
        assert pending_doctor.returncode != 0
        pending_report = json.loads(pending_doctor.stdout)
        assert pending_report["checks"]["upgrade"]["pending"] is True
        pending_build = run_cli(compiler, cwd, env, "build", str(abi_source), "--c")
        assert pending_build.returncode != 0
        assert "upgrade pending" in pending_build.stdout.lower()
        assert not Path(str(abi_source) + ".c").exists()
        pending.unlink()

    # Without FREAK_HOME, an installed/executable-relative payload must beat a
    # hostile project CWD that tries to shadow runtime or stdlib inputs.
    shadow_cwd = root / "doctor-shadow-cwd"
    shutil.copytree(repo / "freakc" / "runtime", shadow_cwd / "freakc" / "runtime")
    shutil.copytree(repo / "std", shadow_cwd / "std")
    shadow_env = env.copy()
    shadow_env.pop("FREAK_HOME")
    shadowed = run_cli(compiler, shadow_cwd, shadow_env, "doctor", "--json")
    assert shadowed.returncode == 0, shadowed.stdout + shadowed.stderr
    shadow_report = json.loads(shadowed.stdout)
    assert Path(shadow_report["checks"]["runtime"]["path"]).resolve() == (
        checkout / "runtime"
    ).resolve()
    assert Path(shadow_report["checks"]["stdlib"]["path"]).resolve() == (
        checkout / "std"
    ).resolve()

    # The real compiler built in this checkout must discover the checkout's
    # freakc/runtime + std payload from any project CWD. This is distinct from
    # the archive/install layout exercised by `checkout_compiler` above.
    repo_env = shadow_env.copy()
    repo_env["HOME"] = str(root / "doctor-repo-empty-home")
    repo_env["APPDATA"] = str(root / "doctor-repo-empty-appdata")
    repo_env["LOCALAPPDATA"] = str(root / "doctor-repo-empty-localappdata")
    repo_env["ProgramFiles"] = str(root / "doctor-repo-empty-program-files")
    repo_env["ProgramFiles(x86)"] = str(
        root / "doctor-repo-empty-program-files-x86"
    )
    repo_discovery = run_cli(
        repo_compiler, shadow_cwd, repo_env, "doctor", "--json"
    )
    assert repo_discovery.returncode == 0, (
        repo_discovery.stdout + repo_discovery.stderr
    )
    repo_report = json.loads(repo_discovery.stdout)
    assert Path(repo_report["checks"]["runtime"]["path"]).resolve() == (
        repo / "freakc" / "runtime"
    ).resolve()
    assert Path(repo_report["checks"]["stdlib"]["path"]).resolve() == (
        repo / "std"
    ).resolve()

    # Checkout ownership is structural, not conditional on a healthy payload.
    # A damaged <checkout>/build compiler must diagnose that checkout instead
    # of silently borrowing a complete user installation with the same ABI.
    damaged_checkout = root / "doctor-damaged-checkout"
    damaged_build = damaged_checkout / "build"
    damaged_build.mkdir(parents=True)
    damaged_compiler = damaged_build / compiler.name
    shutil.copy2(repo_compiler, damaged_compiler)
    damaged_v3 = damaged_checkout / "src" / "compiler" / "v3"
    damaged_v3.mkdir(parents=True)
    shutil.copy2(repo / "src" / "compiler" / "v3" / "main.fk", damaged_v3 / "main.fk")
    damaged_cli = damaged_checkout / "src" / "cli"
    damaged_cli.mkdir(parents=True)
    shutil.copy2(repo / "src" / "cli" / "build.fk", damaged_cli / "build.fk")
    damaged_packaging = damaged_checkout / "packaging"
    damaged_packaging.mkdir()
    shutil.copy2(
        repo / "packaging" / "distribution-files.manifest",
        damaged_packaging / "distribution-files.manifest",
    )
    shutil.copytree(repo / "freakc" / "runtime", damaged_checkout / "freakc" / "runtime")
    shutil.copytree(repo / "std", damaged_checkout / "std")
    (damaged_checkout / "std" / "math.fk").unlink()
    (damaged_checkout / "freakc" / "runtime" / "freak_abi").unlink()

    damaged_env = repo_env.copy()
    if sys.platform == "win32":
        installed_parent = root / "doctor-damaged-installed-appdata"
        installed_decoy = installed_parent / "freak"
        damaged_env["APPDATA"] = str(installed_parent)
    else:
        installed_parent = root / "doctor-damaged-installed-home"
        installed_decoy = installed_parent / ".freak"
        damaged_env["HOME"] = str(installed_parent)
    populate_payload(repo, installed_decoy, entries)

    damaged = run_cli(
        damaged_compiler, shadow_cwd, damaged_env, "doctor", "--json"
    )
    assert damaged.returncode != 0, damaged.stdout + damaged.stderr
    damaged_report = json.loads(damaged.stdout)
    assert Path(damaged_report["checks"]["runtime"]["path"]).resolve() == (
        damaged_checkout / "freakc" / "runtime"
    ).resolve()
    assert Path(damaged_report["checks"]["stdlib"]["path"]).resolve() == (
        damaged_checkout / "std"
    ).resolve()
    assert damaged_report["checks"]["abi"]["runtime"] == "missing"
    assert "math.fk" in damaged_report["checks"]["stdlib"]["missing"]
    damaged_build_result = run_cli(
        damaged_compiler,
        shadow_cwd,
        damaged_env,
        "build",
        str(abi_source),
        "--c",
    )
    assert damaged_build_result.returncode != 0
    assert "abi mismatch" in damaged_build_result.stdout.lower()
    assert not Path(str(abi_source) + ".c").exists()

    # A slashless argv[0] that cannot be found in PATH has no executable
    # identity. Even a same-named CWD decoy inside an otherwise recognizable
    # repository layout must not enable the development payload fallback.
    unresolved_cwd = root / "doctor-unresolved-slashless-cwd"
    shutil.copytree(repo / "freakc" / "runtime", unresolved_cwd / "freakc" / "runtime")
    shutil.copytree(repo / "std", unresolved_cwd / "std")
    unresolved_marker = unresolved_cwd / "src" / "compiler" / "v3" / "main.fk"
    unresolved_marker.parent.mkdir(parents=True)
    shutil.copy2(repo / "src" / "compiler" / "v3" / "main.fk", unresolved_marker)
    unresolved_decoy = unresolved_cwd / compiler.name
    unresolved_decoy.write_text("not the running compiler\n", encoding="utf-8")
    if sys.platform != "win32":
        unresolved_decoy.chmod(0o644)
    unresolved_env = repo_env.copy()
    if sys.platform == "win32":
        windows_dir = Path(unresolved_env.get("WINDIR", r"C:\Windows"))
        unresolved_env["PATH"] = str(windows_dir / "System32")
    else:
        unresolved_env["PATH"] = "/usr/bin:/bin"
    unresolved = subprocess.run(
        [compiler.name, "doctor", "--json"],
        executable=str(compiler),
        cwd=unresolved_cwd,
        env=unresolved_env,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=180,
        check=False,
    )
    assert unresolved.returncode != 0, unresolved.stdout + unresolved.stderr
    unresolved_report = json.loads(unresolved.stdout)
    assert unresolved_report["checks"]["runtime"]["path"] == ""
    assert unresolved_report["checks"]["stdlib"]["path"] == ""

    if sys.platform != "win32":
        # A slashless PATH invocation normally leaves argv[0] as `freak`. A
        # same-named non-executable project file must not replace the actual
        # executable path during payload discovery.
        decoy = shadow_cwd / compiler.name
        decoy.write_text("not the running compiler\n", encoding="utf-8")
        decoy.chmod(0o644)
        path_env = shadow_env.copy()
        path_env["PATH"] = str(compiler.parent) + os.pathsep + path_env.get("PATH", "")
        path_invocation = subprocess.run(
            [compiler.name, "doctor", "--json"],
            cwd=shadow_cwd,
            env=path_env,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=180,
            check=False,
        )
        assert path_invocation.returncode == 0, (
            path_invocation.stdout + path_invocation.stderr
        )
        path_report = json.loads(path_invocation.stdout)
        assert Path(path_report["checks"]["runtime"]["path"]).resolve() == (
            checkout / "runtime"
        ).resolve()
        assert Path(path_report["checks"]["stdlib"]["path"]).resolve() == (
            checkout / "std"
        ).resolve()
        decoy.unlink()

        # PATH shims are allowed, but their directory never owns the payload.
        # Resolve a relative leaf symlink to the real archive compiler before
        # executable-adjacent runtime/std discovery.
        symlink_home = root / "doctor-posix-symlink-home"
        populate_payload(repo, symlink_home, entries)
        symlink_bin = symlink_home / "bin"
        symlink_bin.mkdir()
        symlink_compiler = symlink_bin / compiler.name
        shutil.copy2(compiler, symlink_compiler)
        shim_dir = root / "doctor-posix-shims"
        shim_dir.mkdir()
        shim = shim_dir / compiler.name
        shim.symlink_to(Path(os.path.relpath(symlink_compiler, shim_dir)))
        symlink_env = repo_env.copy()
        symlink_env["PATH"] = (
            str(shim_dir) + os.pathsep + symlink_env.get("PATH", "")
        )
        symlinked = subprocess.run(
            [compiler.name, "doctor", "--json"],
            cwd=shadow_cwd,
            env=symlink_env,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=180,
            check=False,
        )
        assert symlinked.returncode == 0, symlinked.stdout + symlinked.stderr
        symlink_report = json.loads(symlinked.stdout)
        assert Path(symlink_report["checks"]["runtime"]["path"]).resolve() == (
            symlink_home / "runtime"
        ).resolve()
        assert Path(symlink_report["checks"]["stdlib"]["path"]).resolve() == (
            symlink_home / "std"
        ).resolve()

        # Broken and cyclic argv[0] links never acquire payload identity. Run
        # the real compiler with a deliberately different argv[0] so the
        # resolver, rather than the operating system loader, owns the failure.
        broken_shim = shim_dir / "broken-freak"
        broken_shim.symlink_to("missing-freak-target")
        cycle_a = shim_dir / "cycle-a"
        cycle_b = shim_dir / "cycle-b"
        cycle_a.symlink_to(cycle_b.name)
        cycle_b.symlink_to(cycle_a.name)
        for invalid_shim in (broken_shim, cycle_a):
            invalid_link = subprocess.run(
                [str(invalid_shim), "doctor", "--json"],
                executable=str(compiler),
                cwd=unresolved_cwd,
                env=repo_env,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=180,
                check=False,
            )
            assert invalid_link.returncode != 0, (
                invalid_link.stdout + invalid_link.stderr
            )
            invalid_report = json.loads(invalid_link.stdout)
            assert invalid_report["checks"]["runtime"]["path"] == ""
            assert invalid_report["checks"]["stdlib"]["path"] == ""

    # An executable in an archive-style <home>/bin directory owns that payload
    # even when it is incomplete. Falling through to the hostile CWD would hide
    # a damaged installation and compile attacker-controlled runtime sources.
    incomplete_home = root / "doctor-incomplete-adjacent"
    incomplete_bin = incomplete_home / "bin"
    incomplete_bin.mkdir(parents=True)
    incomplete_compiler = incomplete_bin / compiler.name
    shutil.copy2(compiler, incomplete_compiler)
    (incomplete_home / "runtime").mkdir()
    shutil.copy2(
        repo / "freakc" / "runtime" / "freak_runtime.c",
        incomplete_home / "runtime" / "freak_runtime.c",
    )
    incomplete_env = shadow_env.copy()
    incomplete_env["HOME"] = str(root / "doctor-empty-home")
    incomplete_env["APPDATA"] = str(root / "doctor-empty-appdata")
    incomplete_env["LOCALAPPDATA"] = str(root / "doctor-empty-localappdata")
    incomplete_env["ProgramFiles"] = str(root / "doctor-empty-program-files")
    incomplete_env["ProgramFiles(x86)"] = str(
        root / "doctor-empty-program-files-x86"
    )
    incomplete = run_cli(
        incomplete_compiler, shadow_cwd, incomplete_env, "doctor", "--json"
    )
    assert incomplete.returncode != 0, incomplete.stdout + incomplete.stderr
    incomplete_report = json.loads(incomplete.stdout)
    assert Path(incomplete_report["checks"]["runtime"]["path"]).resolve() == (
        incomplete_home / "runtime"
    ).resolve()
    assert Path(incomplete_report["checks"]["stdlib"]["path"]).resolve() == (
        incomplete_home / "std"
    ).resolve()
    assert incomplete_report["checks"]["abi"]["ok"] is False
    incomplete_build = run_cli(
        incomplete_compiler,
        shadow_cwd,
        incomplete_env,
        "build",
        str(abi_source),
        "--c",
    )
    assert incomplete_build.returncode != 0
    assert "abi mismatch" in incomplete_build.stdout.lower()
    assert not Path(str(abi_source) + ".c").exists()

    if sys.platform == "win32":
        resolution_error_prefix = "!freak-payload-resolution-error!"
        # WinGet exposes an alias from Microsoft/WinGet/Links rather than the
        # package's bin directory. The registered package must beat both CWD
        # and an unrelated default AppData installation.
        winget_local = root / "doctor-winget-localappdata"
        winget_home = (
            winget_local
            / "Microsoft"
            / "WinGet"
            / "Packages"
            / "FREAK.freak_fixture"
            / "freak"
        )
        populate_payload(repo, winget_home, entries)
        winget_alias_dir = winget_local / "Microsoft" / "WinGet" / "Links"
        winget_alias_dir.mkdir(parents=True)
        winget_compiler = winget_alias_dir / compiler.name
        shutil.copy2(compiler, winget_compiler)
        unrelated_appdata_home = root / "doctor-winget-appdata" / "freak"
        populate_payload(repo, unrelated_appdata_home, entries)
        winget_env = shadow_env.copy()
        winget_env["LOCALAPPDATA"] = str(winget_local)
        winget_env["APPDATA"] = str(unrelated_appdata_home.parent)
        winget_env["HOME"] = str(root / "doctor-winget-empty-home")
        winget_env["ProgramFiles"] = str(root / "doctor-winget-program-files")
        winget_env["ProgramFiles(x86)"] = str(
            root / "doctor-winget-program-files-x86"
        )
        winget = run_cli(
            winget_compiler, shadow_cwd, winget_env, "doctor", "--json"
        )
        assert winget.returncode == 0, winget.stdout + winget.stderr
        winget_report = json.loads(winget.stdout)
        assert Path(winget_report["checks"]["runtime"]["path"]).resolve() == (
            winget_home / "runtime"
        ).resolve()
        assert Path(winget_report["checks"]["stdlib"]["path"]).resolve() == (
            winget_home / "std"
        ).resolve()

        # A real Windows command invocation supplies slashless argv[0] and
        # relies on `where`. Restrict lookup to PATH so a same-named CWD file
        # cannot hide the WinGet alias that owns the package scope.
        slashless_decoy = shadow_cwd / compiler.name
        slashless_decoy.write_text("not a Windows executable\n", encoding="utf-8")
        slashless_winget_env = winget_env.copy()
        slashless_winget_env["PATH"] = (
            str(winget_alias_dir)
            + os.pathsep
            + slashless_winget_env.get("PATH", "")
        )
        slashless_winget = subprocess.run(
            [compiler.name, "doctor", "--json"],
            executable=str(winget_compiler),
            cwd=shadow_cwd,
            env=slashless_winget_env,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=180,
            check=False,
        )
        assert slashless_winget.returncode == 0, (
            slashless_winget.stdout + slashless_winget.stderr
        )
        slashless_winget_report = json.loads(slashless_winget.stdout)
        assert Path(
            slashless_winget_report["checks"]["runtime"]["path"]
        ).resolve() == (winget_home / "runtime").resolve()
        assert Path(
            slashless_winget_report["checks"]["stdlib"]["path"]
        ).resolve() == (winget_home / "std").resolve()
        slashless_decoy.unlink()

        # An alias with zero matching packages is still authoritative. Return
        # an explicit resolution error instead of falling through to a complete
        # but unrelated AppData installation or the project CWD.
        empty_winget_local = root / "doctor-winget-empty-localappdata"
        empty_packages = empty_winget_local / "Microsoft" / "WinGet" / "Packages"
        empty_packages.mkdir(parents=True)
        empty_alias_dir = empty_winget_local / "Microsoft" / "WinGet" / "Links"
        empty_alias_dir.mkdir()
        empty_alias = empty_alias_dir / compiler.name
        shutil.copy2(compiler, empty_alias)
        missing_alias_collision = empty_packages / ".freak-missing-alias-package"
        populate_payload(repo, missing_alias_collision, entries)
        empty_appdata_home = root / "doctor-winget-empty-appdata" / "freak"
        populate_payload(repo, empty_appdata_home, entries)
        empty_alias_env = winget_env.copy()
        empty_alias_env["LOCALAPPDATA"] = str(empty_winget_local)
        empty_alias_env["APPDATA"] = str(empty_appdata_home.parent)
        empty_alias_env["HOME"] = str(root / "doctor-winget-zero-empty-home")
        empty_alias_env["ProgramFiles"] = str(
            root / "doctor-winget-zero-program-files"
        )
        empty_alias_env["ProgramFiles(x86)"] = str(
            root / "doctor-winget-zero-program-files-x86"
        )
        empty_alias_result = run_cli(
            empty_alias, shadow_cwd, empty_alias_env, "doctor", "--json"
        )
        assert empty_alias_result.returncode != 0
        empty_alias_report = json.loads(empty_alias_result.stdout)
        missing_runtime = empty_alias_report["checks"]["runtime"]["path"]
        missing_std = empty_alias_report["checks"]["stdlib"]["path"]
        assert missing_runtime.startswith(
            resolution_error_prefix + "winget-missing-alias-package|"
        )
        assert missing_std.startswith(
            resolution_error_prefix + "winget-missing-alias-package|"
        )
        assert ".freak-missing-alias-package" not in missing_runtime
        assert empty_alias_report["checks"]["abi"]["runtime"] == "resolution-error"
        missing_alias_build = run_cli(
            empty_alias,
            shadow_cwd,
            empty_alias_env,
            "build",
            str(abi_source),
            "--c",
        )
        assert missing_alias_build.returncode != 0
        assert "payload resolution failed" in missing_alias_build.stdout.lower()
        assert not Path(str(abi_source) + ".c").exists()

        # An alias scope containing more than one matching package is
        # ambiguous. Neither an incomplete stale package nor two complete
        # packages may be selected by filesystem enumeration order.
        stale_package = (
            winget_local
            / "Microsoft"
            / "WinGet"
            / "Packages"
            / "FREAK.freak_stale"
        )
        ambiguous_collision = (
            winget_local
            / "Microsoft"
            / "WinGet"
            / "Packages"
            / ".freak-ambiguous-installation"
        )
        populate_payload(repo, ambiguous_collision, entries)
        stale_package.mkdir(parents=True)
        stale_ambiguous = run_cli(
            winget_compiler, shadow_cwd, winget_env, "doctor", "--json"
        )
        assert stale_ambiguous.returncode != 0
        stale_report = json.loads(stale_ambiguous.stdout)
        stale_runtime = stale_report["checks"]["runtime"]["path"]
        assert stale_runtime.startswith(
            resolution_error_prefix + "winget-ambiguous-packages|"
        )
        assert ".freak-ambiguous-installation" not in stale_runtime
        assert stale_report["checks"]["abi"]["runtime"] == "resolution-error"
        populate_payload(repo, stale_package / "freak", entries)
        complete_ambiguous = run_cli(
            winget_compiler, shadow_cwd, winget_env, "doctor", "--json"
        )
        assert complete_ambiguous.returncode != 0
        complete_report = json.loads(complete_ambiguous.stdout)
        assert complete_report["checks"]["stdlib"]["path"].startswith(
            resolution_error_prefix + "winget-ambiguous-packages|"
        )
        ambiguous_build = run_cli(
            winget_compiler,
            shadow_cwd,
            winget_env,
            "build",
            str(abi_source),
            "--c",
        )
        assert ambiguous_build.returncode != 0
        assert "payload resolution failed" in ambiguous_build.stdout.lower()
        assert not Path(str(abi_source) + ".c").exists()
        shutil.rmtree(stale_package)

        # Machine-scope aliases live under Program Files/WinGet/Links and must
        # bind to the sibling machine Packages root, not AppData or a user
        # WinGet package with the same public ABI marker.
        machine_program_files = root / "doctor-machine-program-files"
        machine_home = (
            machine_program_files
            / "WinGet"
            / "Packages"
            / "FREAK.freak_machine"
            / "freak"
        )
        populate_payload(repo, machine_home, entries)
        machine_alias_dir = machine_program_files / "WinGet" / "Links"
        machine_alias_dir.mkdir(parents=True)
        machine_compiler = machine_alias_dir / compiler.name
        shutil.copy2(compiler, machine_compiler)
        machine_env = winget_env.copy()
        machine_env["ProgramFiles"] = str(machine_program_files)
        machine = run_cli(
            machine_compiler, shadow_cwd, machine_env, "doctor", "--json"
        )
        assert machine.returncode == 0, machine.stdout + machine.stderr
        machine_report = json.loads(machine.stdout)
        assert Path(machine_report["checks"]["runtime"]["path"]).resolve() == (
            machine_home / "runtime"
        ).resolve()
        assert Path(machine_report["checks"]["stdlib"]["path"]).resolve() == (
            machine_home / "std"
        ).resolve()

        machine_pending = machine_home / "bin" / ".freak-upgrade-pending"
        machine_pending.parent.mkdir(parents=True, exist_ok=True)
        machine_pending.write_text(
            "v0.14.1|wait-pid=machine-fixture\n", encoding="utf-8"
        )
        machine_pending_doctor = run_cli(
            machine_compiler, shadow_cwd, machine_env, "doctor", "--json"
        )
        assert machine_pending_doctor.returncode != 0
        assert json.loads(machine_pending_doctor.stdout)["checks"]["upgrade"][
            "pending"
        ] is True
        for command in ("build", "run"):
            rejected = run_cli(
                machine_compiler,
                shadow_cwd,
                machine_env,
                command,
                str(abi_source),
                "--c",
            )
            assert rejected.returncode != 0
            assert "upgrade pending" in rejected.stdout.lower()
        machine_pending.unlink()

        # A non-adjacent compiler using the default AppData payload must see
        # durable deferred-upgrade state even without FREAK_HOME.
        default_appdata = root / "doctor-default-appdata"
        default_home = default_appdata / "freak"
        populate_payload(repo, default_home, entries)
        default_pending = default_home / "bin" / ".freak-upgrade-pending"
        default_pending.parent.mkdir(parents=True)
        default_pending.write_text("v0.14.1|wait-pid=fixture\n", encoding="utf-8")
        detached_bin = root / "doctor-detached" / "tools"
        detached_bin.mkdir(parents=True)
        (detached_bin.parent / "bin").mkdir()
        detached_compiler = detached_bin / compiler.name
        shutil.copy2(compiler, detached_compiler)
        default_env = shadow_env.copy()
        default_env["APPDATA"] = str(default_appdata)
        default_env["LOCALAPPDATA"] = str(root / "doctor-default-localappdata")
        default_env["HOME"] = str(root / "doctor-default-empty-home")
        default_env["ProgramFiles"] = str(root / "doctor-default-program-files")
        default_env["ProgramFiles(x86)"] = str(
            root / "doctor-default-program-files-x86"
        )
        default_doctor = run_cli(
            detached_compiler, shadow_cwd, default_env, "doctor", "--json"
        )
        assert default_doctor.returncode != 0
        default_report = json.loads(default_doctor.stdout)
        assert default_report["checks"]["upgrade"]["pending"] is True
        assert Path(default_report["checks"]["upgrade"]["marker"]).resolve() == (
            default_pending
        ).resolve()
        default_build = run_cli(
            detached_compiler,
            shadow_cwd,
            default_env,
            "build",
            str(abi_source),
            "--c",
        )
        assert default_build.returncode != 0
        assert "upgrade pending" in default_build.stdout.lower()
        assert not Path(str(abi_source) + ".c").exists()

        # cmd.exe reports WINDIR when it is launched from a UNC cwd. Reject
        # that reported directory even when a same-named, complete-payload
        # decoy exists there; existence alone is not executable identity.
        fallback_home = root / "doctor-windows-cwd-fallback-home"
        populate_payload(repo, fallback_home, entries)
        fallback_bin = fallback_home / "bin"
        fallback_bin.mkdir()
        fallback_name = "freak-windows-cwd-fallback-probe.exe"
        fallback_decoy = fallback_bin / fallback_name
        shutil.copy2(compiler, fallback_decoy)
        fallback_env = repo_env.copy()
        fallback_env.pop("WINDIR", None)
        fallback_env["SystemRoot"] = str(fallback_bin)
        fallback = subprocess.run(
            [f".\\{fallback_name}", "doctor", "--json"],
            executable=str(compiler),
            cwd=fallback_bin,
            env=fallback_env,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=180,
            check=False,
        )
        assert fallback.returncode != 0, fallback.stdout + fallback.stderr
        fallback_report = json.loads(fallback.stdout)
        assert fallback_report["checks"]["runtime"]["path"] == ""
        assert fallback_report["checks"]["stdlib"]["path"] == ""

        # Exercise the real UNC behavior when the runner exposes its temporary
        # drive through the standard localhost administrative share. Hardened
        # hosts may disable that share; the deterministic decoy case above is
        # the mandatory guard coverage on every Windows run.
        resolved_root = root.resolve()
        if len(resolved_root.drive) == 2 and resolved_root.drive[1] == ":":
            unc_root = (
                Path(rf"\\localhost\{resolved_root.drive[0]}$")
                / resolved_root.relative_to(resolved_root.anchor)
            )
            if unc_root.exists():
                unc_home_local = root / "doctor-unc-relative-home"
                populate_payload(repo, unc_home_local, entries)
                unc_bin_local = unc_home_local / "bin"
                unc_bin_local.mkdir()
                unc_name = "freak-unc-relative-probe.exe"
                unc_compiler_local = unc_bin_local / unc_name
                shutil.copy2(compiler, unc_compiler_local)
                unc_bin = unc_root / "doctor-unc-relative-home" / "bin"
                unc = subprocess.run(
                    [f".\\{unc_name}", "doctor", "--json"],
                    executable=str(unc_compiler_local),
                    cwd=unc_bin,
                    env=repo_env,
                    capture_output=True,
                    text=True,
                    errors="replace",
                    timeout=180,
                    check=False,
                )
                assert unc.returncode != 0, unc.stdout + unc.stderr
                unc_report = json.loads(unc.stdout)
                assert unc_report["checks"]["runtime"]["path"] == ""
                assert unc_report["checks"]["stdlib"]["path"] == ""

    # Direct archive use (`cd <home>/bin && ./freak`) supplies a relative
    # argv[0]. It must still resolve the executable-adjacent payload before
    # looking at CWD or another user installation.
    direct_name = f".\\{compiler.name}" if sys.platform == "win32" else f"./{compiler.name}"
    direct = subprocess.run(
        [direct_name, "doctor", "--json"],
        executable=str(compiler),
        cwd=checkout_bin,
        env=shadow_env,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=180,
        check=False,
    )
    assert direct.returncode == 0, direct.stdout + direct.stderr
    direct_report = json.loads(direct.stdout)
    assert Path(direct_report["checks"]["runtime"]["path"]).resolve() == (
        checkout / "runtime"
    ).resolve()
    assert Path(direct_report["checks"]["stdlib"]["path"]).resolve() == (
        checkout / "std"
    ).resolve()

    if sys.platform != "win32":
        read_only_cwd = root / "doctor-read-only-cwd"
        read_only_cwd.mkdir()
        read_only_cwd.chmod(0o555)
        try:
            read_only = run_cli(compiler, read_only_cwd, env, "doctor", "--json")
            read_only_full = run_cli(compiler, read_only_cwd, env, "doctor")
        finally:
            read_only_cwd.chmod(0o755)
        assert read_only.returncode == 0, read_only.stdout + read_only.stderr
        assert json.loads(read_only.stdout)["status"] == "ok"
        assert read_only_full.returncode == 0, (
            read_only_full.stdout + read_only_full.stderr
        )
        assert "compile, link, and execution work" in read_only_full.stdout
        assert not list(read_only_cwd.iterdir()), "doctor wrote into read-only cwd"

    # A pre-existing predictable candidate is not ours to delete. Atomic
    # mkdir must skip it, use the next suffix, and preserve both sentinels.
    collision_env = env.copy()
    collision_env["FREAK_DOCTOR_TEST_PROBE_ID"] = "collision"
    collision_dirs = (
        probe_temp / "freak-doctor-clang-probe-collision_0",
        probe_temp / "freak-doctor-pipeline-probe-collision_0",
    )
    for collision_dir in collision_dirs:
        collision_dir.mkdir()
        (collision_dir / "unrelated-sentinel").write_bytes(b"preserve me\n")
    collision = run_cli(compiler, cwd, collision_env, "doctor")
    assert collision.returncode == 0, collision.stdout + collision.stderr
    for collision_dir in collision_dirs:
        sentinel = collision_dir / "unrelated-sentinel"
        assert sentinel.read_bytes() == b"preserve me\n"
        assert list(collision_dir.iterdir()) == [sentinel]
        shutil.rmtree(collision_dir)
    assert not list(probe_temp.glob("freak-doctor-*-probe-collision_*"))

    if sys.platform == "win32":
        # Exercise the transient-lock retry with a shell-metacharacter-bearing
        # temp root. The test hook skips the first rmdir without weakening the
        # ownership check or the real second removal.
        retry_temp = root / "doctor & retry probes"
        retry_temp.mkdir()
        retry_env = env.copy()
        retry_env["TEMP"] = str(retry_temp)
        retry_env["TMP"] = str(retry_temp)
        retry_env["TMPDIR"] = str(retry_temp)
        retry_env["FREAK_DOCTOR_TEST_FAIL_FIRST_REMOVE"] = "1"
        retried = run_cli(compiler, cwd, retry_env, "doctor")
        assert retried.returncode == 0, retried.stdout + retried.stderr
        assert not list(retry_temp.iterdir()), list(retry_temp.iterdir())

    # If cleanup still cannot finish, Doctor fails closed and names the
    # retained owned directory instead of claiming success or deleting a
    # different path.
    retained_temp = root / "doctor-retained-probes"
    retained_temp.mkdir()
    retained_env = env.copy()
    retained_env["TEMP"] = str(retained_temp)
    retained_env["TMP"] = str(retained_temp)
    retained_env["TMPDIR"] = str(retained_temp)
    retained_env["FREAK_DOCTOR_TEST_RETAIN_PROBE"] = "1"
    retained = run_cli(compiler, cwd, retained_env, "doctor", "--json")
    assert retained.returncode != 0, retained.stdout + retained.stderr
    retained_report = json.loads(retained.stdout)
    retained_path = Path(retained_report["checks"]["clang"]["cleanup_retained"])
    assert retained_path.is_dir(), retained_path
    assert retained_path.parent.resolve() == retained_temp.resolve()
    shutil.rmtree(retained_path)
    assert not list(retained_temp.iterdir())

    retained_fix_temp = root / "doctor-retained-fix-probes"
    retained_fix_temp.mkdir()
    retained_fix_env = retained_env.copy()
    retained_fix_env["TEMP"] = str(retained_fix_temp)
    retained_fix_env["TMP"] = str(retained_fix_temp)
    retained_fix_env["TMPDIR"] = str(retained_fix_temp)
    clang_install_sentinel = root / "unexpected-clang-reinstall.txt"
    if sys.platform == "win32":
        retained_fix_env["FREAK_DOCTOR_INSTALL_COMMAND"] = (
            f'powershell -NoProfile -Command "Set-Content -LiteralPath \'{clang_install_sentinel}\' unexpected"'
        )
    else:
        retained_fix_env["FREAK_DOCTOR_INSTALL_COMMAND"] = (
            f'printf unexpected > "{clang_install_sentinel}"'
        )
    retained_fix = run_cli(compiler, cwd, retained_fix_env, "doctor", "--fix")
    assert retained_fix.returncode != 0, retained_fix.stdout + retained_fix.stderr
    assert "Probe cleanup could not finish; retained:" in retained_fix.stdout
    assert not clang_install_sentinel.exists(), (
        "Doctor reinstalled a usable Clang merely because probe cleanup was retained"
    )
    retained_fix_paths = list(retained_fix_temp.glob("freak-doctor-*-probe-*"))
    assert retained_fix_paths, retained_fix.stdout
    for path in retained_fix_paths:
        shutil.rmtree(path)

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
    assert not list(cwd.glob("freak-doctor-clang-probe-*"))
    clang_probe_artifacts = list(probe_temp.glob("freak-doctor-clang-probe-*"))
    pipeline_probe_artifacts = list(probe_temp.glob("freak-doctor-pipeline-probe-*"))
    assert not clang_probe_artifacts, clang_probe_artifacts
    assert not pipeline_probe_artifacts, pipeline_probe_artifacts

    # A backend failure after the Clang probe must clean only temp-backed
    # pipeline artifacts. In particular, an empty build result must never be
    # turned into the caller-relative path `.freak-run-cache` and deleted.
    caller_cache = cwd / ".freak-run-cache"
    caller_cache.write_bytes(b"unrelated caller cache\n")
    runtime_source = payload / "runtime" / "freak_runtime.c"
    runtime_source.write_text("#error intentional doctor pipeline failure\n", encoding="utf-8")
    failed_pipeline = run_cli(compiler, cwd, env, "doctor")
    assert failed_pipeline.returncode != 0, (
        failed_pipeline.stdout + failed_pipeline.stderr
    )
    assert caller_cache.read_bytes() == b"unrelated caller cache\n"
    failed_probe_artifacts = list(probe_temp.glob("freak-doctor-pipeline-probe-*"))
    assert not failed_probe_artifacts, failed_probe_artifacts
    shutil.copy2(repo / "freakc" / "runtime" / "freak_runtime.c", runtime_source)
    caller_cache.unlink()

    # A version/output-only fake models the Windows failure mode that motivated
    # the usable-toolchain probe. Creating a file is insufficient: doctor must
    # execute the linked probe before accepting Clang, and --fix must repair it.
    broken_clang = root / (
        "version-only-clang.cmd" if sys.platform == "win32" else "version-only-clang.sh"
    )
    repair_sentinel = root / "doctor-install-attempted.txt"
    if sys.platform == "win32":
        broken_clang.write_text(
            '@echo off\nif "%1"=="--version" (echo clang output-only fixture& exit /b 0)\n'
            ":scan\n"
            'if "%1"=="" exit /b 1\n'
            'if "%1"=="-o" goto emit\n'
            "shift\n"
            "goto scan\n"
            ":emit\n"
            "shift\n"
            '> "%~1" echo this is not an executable\n'
            "exit /b 0\n",
            encoding="utf-8",
        )
        install_fixture = root / "doctor-install-fixture.cmd"
        install_fixture.write_text(
            f'@echo off\n> "{repair_sentinel}" echo attempted\nexit /b 0\n',
            encoding="utf-8",
        )
        install_command = f'"{install_fixture}"'
    else:
        broken_clang.write_text(
            "#!/usr/bin/env bash\n"
            'if [ "${1:-}" = "--version" ]; then echo clang output-only fixture; exit 0; fi\n'
            "while [ \"$#\" -gt 0 ]; do\n"
            '  if [ "$1" = "-o" ]; then shift; printf not-executable > "$1"; exit 0; fi\n'
            "  shift\n"
            "done\n"
            "exit 1\n",
            encoding="utf-8",
        )
        broken_clang.chmod(0o755)
        install_fixture = root / "doctor-install-fixture.sh"
        install_fixture.write_text(
            "#!/usr/bin/env bash\n"
            f'printf attempted > "{repair_sentinel}"\n',
            encoding="utf-8",
        )
        install_fixture.chmod(0o755)
        install_command = f'bash "{install_fixture}"'

    broken_env = env.copy()
    broken_env["FREAK_CLANG"] = str(broken_clang)
    broken = run_cli(compiler, cwd, broken_env, "doctor", "--json")
    assert broken.returncode != 0, broken.stdout + broken.stderr
    broken_report = json.loads(broken.stdout)
    assert broken_report["checks"]["clang"]["ok"] is False
    assert not list(cwd.glob("freak-doctor-clang-probe-*"))
    assert not list(probe_temp.glob("freak-doctor-clang-probe-*"))

    broken_env["FREAK_DOCTOR_INSTALL_COMMAND"] = install_command
    fix_attempt = run_cli(compiler, cwd, broken_env, "doctor", "--fix")
    assert fix_attempt.returncode != 0, fix_attempt.stdout + fix_attempt.stderr
    assert repair_sentinel.is_file(), fix_attempt.stdout + fix_attempt.stderr
    assert not list(cwd.glob("freak-doctor-clang-probe-*"))
    assert not list(probe_temp.glob("freak-doctor-clang-probe-*"))


def check_upgrade(root: Path, compiler: Path) -> None:
    env = os.environ.copy()
    upgrade_root = root / "upgrade $(printf injected) `%FREAK_UPGRADE_PATH% ' home"
    upgrade_root.mkdir()
    env["FREAK_HOME"] = str(upgrade_root)
    env["FREAK_UPGRADE_PATH"] = "EXPANDED"
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
    sentinel_text = sentinel.read_text(encoding="utf-8")
    if sys.platform == "win32":
        assert sentinel_text == "True|True|local|1", sentinel_text
    else:
        assert sentinel_text == f"local|{upgrade_root}|--upgrade --without-deps", sentinel_text

    env["FREAK_UPGRADE_SCRIPT"] = str(failing)
    failed = run_cli(compiler, root, env, "upgrade")
    expected_failure = 7
    assert failed.returncode == expected_failure, (
        f"upgrade failure returned {failed.returncode}, expected {expected_failure}\n"
        + failed.stdout
        + failed.stderr
    )
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
        check_downloaded_archive_checksum(repo, root, archive)
        check_doctor(repo, root, compiler, entries)
        check_upgrade(root, compiler)
    print("V3 install, doctor, and upgrade: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
