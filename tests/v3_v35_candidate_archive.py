#!/usr/bin/env python3
"""Verify exact candidate packaging and extracted native commands without rebuilding tools."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PureWindowsPath
from unittest.mock import patch
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract(path: Path, root: Path) -> dict[str, bytes]:
    members: dict[str, bytes] = {}
    modes: dict[str, int] = {}
    if path.name.endswith(".zip"):
        with zipfile.ZipFile(path) as archive:
            for entry in archive.infolist():
                assert entry.filename.startswith("freak/") and ".." not in entry.filename.split("/")
                if entry.is_dir():
                    continue
                members[entry.filename[6:]] = archive.read(entry)
                modes[entry.filename[6:]] = (entry.external_attr >> 16) & 0o777
                assert entry.date_time == (1980, 1, 1, 0, 0, 0) and entry.compress_type == zipfile.ZIP_STORED
    else:
        with tarfile.open(path) as archive:
            for entry in archive.getmembers():
                assert entry.name == "freak" or entry.name.startswith("freak/")
                assert ".." not in entry.name.split("/") and (entry.isfile() or entry.isdir())
                assert entry.mtime == 0 and entry.uid == entry.gid == 0
                if entry.isfile():
                    members[entry.name[6:]] = archive.extractfile(entry).read()
                    modes[entry.name[6:]] = entry.mode & 0o777
    for name, data in members.items():
        destination = root / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        expected = 0o755 if name in ("freak", "hangar", "freak.exe", "hangar.exe") else 0o644
        assert modes[name] == expected
        destination.chmod(modes[name])
    return members


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repo", "freak", "hangar", "build-record", "clang"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--provisional", action="store_true")
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    repo, freak, hangar, record_path, clang = (
        value.resolve(strict=True) for value in (args.repo, args.freak, args.hangar, args.build_record, args.clang))
    packager = Path(__file__).resolve().parents[1] / "packaging/create_candidate_archive.py"
    original_record = json.loads(record_path.read_text())
    source_hash = digest(freak.read_bytes())
    checks: list[str] = []
    with tempfile.TemporaryDirectory(prefix="freak-v35-archive-") as temporary:
        root = Path(temporary).resolve()

        def command(output: Path, *, selected_repo: Path = repo, selected_record: Path = record_path,
                    selected_freak: Path = freak, provisional: bool = args.provisional) -> list[str]:
            values = [sys.executable, str(packager), "--repo", str(selected_repo), "--freak", str(selected_freak),
                      "--hangar", str(hangar), "--build-record", str(selected_record), "--output", str(output)]
            return values + (["--provisional"] if provisional else [])

        def invoke(output: Path, **options: object) -> subprocess.CompletedProcess[bytes]:
            return subprocess.run(command(output, **options), capture_output=True, timeout=120)

        def rejected(name: str, expected: bytes, **options: object) -> None:
            options.setdefault("provisional", True)
            output = root / (name + ".tar.gz")
            result = invoke(output, **options)
            assert result.returncode != 0 and expected in result.stderr, (name, result.stdout, result.stderr)
            assert not output.exists() and not list(root.glob(".freak-candidate-*")), name
            checks.append(name)

        for suffix in (".tar.gz", ".zip"):
            first, second = root / ("candidate-one" + suffix), root / ("candidate-two" + suffix)
            left, right = invoke(first), invoke(second)
            assert left.returncode == right.returncode == 0, (left.stderr, right.stderr)
            assert first.read_bytes() == second.read_bytes(), suffix
            result = json.loads(left.stdout)
            assert result["artifact_sha256"] == digest(first.read_bytes())
            extracted = root / ("extracted " + suffix[1:] + " é 日本 ' $ &")
            files = extract(first, extracted)
            info = json.loads(files["build-info.json"])
            assert info["provisional"] is args.provisional and info["source_sha"] == original_record["source_sha"]
            if not args.provisional:
                assert info["source_clean"] and not info["unrecorded_inputs"]
            inventory = json.loads(files["payload-inventory.json"])
            assert info["input_digests"]["payload_inventory"] == digest(files["payload-inventory.json"])
            binaries = {"freak.exe", "hangar.exe"} if info["platform"]["format"] == "PE" else {"freak", "hangar"}
            payload = {line.split("|")[1] for line in files["distribution-files.manifest"].decode().splitlines()
                       if line and not line.startswith("#")}
            metadata = {"build-info.json", "build-record.json", "payload-inventory.json", "SHA256SUMS", "distribution-files.manifest"}
            assert set(files) == payload | binaries | metadata
            assert set(inventory) == payload | binaries | {"distribution-files.manifest"}
            for name, entry in inventory.items():
                assert entry["sha256"] == digest(files[name]) and entry["size"] == len(files[name])
                assert entry["mode"] == ("0755" if name in binaries else "0644")
            for line in files["SHA256SUMS"].decode().splitlines():
                expected, name = line.split("  ", 1)
                assert digest(files[name]) == expected
            assert not any(name.endswith((".py", ".pyc", ".pyo")) or ".git/" in name for name in files)
            checks.append("deterministic exact-manifest " + suffix[1:] + " with reviewable byte provenance")
            env = {**os.environ, "FREAK_HOME": str(extracted), "FREAK_CLANG": str(clang), "NO_COLOR": "1"}
            env.pop("FREAK_DOCTOR_INSTALL_COMMAND", None)
            for name in binaries:
                version = subprocess.run([extracted / name, "--version"], cwd=root, env=env, capture_output=True, timeout=30)
                assert version.returncode == 0 and info["version"].encode() in version.stdout, version
            native = extracted / ("freak.exe" if os.name == "nt" else "freak")
            doctor = subprocess.run([native, "doctor", "--json"], cwd=root, env=env, capture_output=True, timeout=60)
            diagnosis = json.loads(doctor.stdout)
            assert doctor.returncode == 0 and diagnosis["status"] == "ok", (doctor.stderr, diagnosis)
            assert diagnosis["checks"]["clang"]["probe_ok"] and diagnosis["checks"]["runtime"]["ok"]
            header = extracted / "runtime/freak_runtime.h"
            previous = header.read_bytes()
            header.unlink()
            missing = subprocess.run([native, "doctor", "--json"], cwd=root, env=env, capture_output=True, timeout=60)
            diagnosis = json.loads(missing.stdout)
            assert missing.returncode != 0 and diagnosis["status"] == "issues"
            assert not diagnosis["checks"]["runtime"]["ok"] and "freak_runtime.h" in diagnosis["checks"]["runtime"]["missing"]
            source, output = root / "outside-project.fk", root / "must-not-exist"
            source.write_text('task main() -> int {\n    say "archive-native"\n    give back 0\n}\n')
            built = subprocess.run([native, "build", source, "--c", "--output=" + str(output)],
                                   cwd=root, env=env, capture_output=True, timeout=60)
            assert built.returncode != 0 and not output.exists() and (built.stdout or built.stderr), built
            header.write_bytes(previous)
            checks.append("extracted " + suffix[1:] + " native versions/Doctor and public missing-payload failure")

        # Rewritten metadata below is used only for rejection tests, never as a
        # claim that the synthetic Git object was the original reconstruction.
        fixture = root / "input-fixture"
        fixture.mkdir()
        needed = set(original_record["all_inputs_before"]) | {"VERSION", "build/freakc_v3.fk.c"}
        for line in (repo / "packaging/distribution-files.manifest").read_text().splitlines():
            if line and not line.startswith("#"):
                needed.add(line.split("|")[0])
        for relative in needed:
            destination = fixture / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(repo / relative, destination)
        subprocess.run(["git", "init", "--quiet", str(fixture)], check=True, capture_output=True)
        subprocess.run(["git", "add", "--", *sorted(needed)], cwd=fixture, check=True, capture_output=True)
        subprocess.run(["git", "-c", "user.name=Archive fixture", "-c", "user.email=fixture@example.invalid",
                        "commit", "--quiet", "-m", "Record isolated rejection fixture"], cwd=fixture, check=True, capture_output=True)
        fixture_record = dict(original_record, source_sha=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=fixture, text=True).strip(),
            source_tree=subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=fixture, text=True).strip(),
            uncommitted_delta="")
        selected_record = root / "fixture-record.json"

        def write_record(value: dict = fixture_record) -> None:
            selected_record.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")

        incomplete = dict(fixture_record, all_inputs_before=dict(fixture_record["all_inputs_before"]),
                          all_inputs_after=dict(fixture_record["all_inputs_after"]))
        incomplete["all_inputs_before"].pop("VERSION", None)
        incomplete["all_inputs_after"].pop("VERSION", None)
        write_record(incomplete)
        rejected("final incomplete inventory", b"missing required inventory", selected_repo=fixture,
                 selected_record=selected_record, provisional=False)
        write_record()
        if args.provisional:
            rejected("final dirty original snapshot", b"clean Git HEAD", provisional=False)
        bad = dict(fixture_record, source_tree="0" * 40)
        write_record(bad)
        rejected("stale Git tree identity", b"Git tree does not match", selected_repo=fixture, selected_record=selected_record)
        bad = dict(fixture_record, source_inputs=dict(fixture_record["source_inputs"]))
        bad["source_inputs"].pop("src/compiler/v3/checker.fk")
        write_record(bad)
        rejected("incomplete compiled source inventory", b"compiled compiler/CLI source inventory", selected_repo=fixture, selected_record=selected_record)
        bad = dict(fixture_record, all_inputs_after=dict(fixture_record["all_inputs_after"]))
        key = next(iter(bad["all_inputs_after"]))
        bad["all_inputs_after"][key] = "0" * 64
        write_record(bad)
        rejected("changed reconstruction before-after", b"changed between", selected_repo=fixture, selected_record=selected_record)
        write_record()
        path = fixture / "freakc/runtime/freak_runtime.h"
        previous = path.read_bytes()
        path.write_bytes(previous + b"\nchanged\n")
        rejected("stale payload", b"stale reconstruction input", selected_repo=fixture, selected_record=selected_record)
        path.write_bytes(previous)
        tampered = root / "tampered-native"
        tampered.write_bytes(freak.read_bytes() + b"stale")
        rejected("stale native binary", b"stale supplied native", selected_freak=tampered)
        script = root / "python-disguised-as-native"
        script.write_bytes(b"#!/usr/bin/env python3\nprint('not-native')\n")
        bad = dict(fixture_record, native_hashes=dict(fixture_record["native_hashes"]))
        native_key = "freak.exe" if "freak.exe" in bad["native_hashes"] else "freak"
        bad["native_hashes"][native_key] = digest(script.read_bytes())
        write_record(bad)
        rejected("non-native executable", b"not a native", selected_repo=fixture, selected_record=selected_record, selected_freak=script)
        distribution = fixture / "packaging/distribution-files.manifest"
        original_manifest = distribution.read_bytes()
        for name, row, expected in (
            ("unsafe manifest traversal", b"VERSION|../escape\n", b"unsafe inventory path"),
            ("reserved checksum metadata", b"VERSION|SHA256SUMS\n", b"aliases candidate metadata"),
            ("reserved checksum case alias", b"VERSION|sha256sums\n", b"aliases candidate metadata"),
            ("reserved checksum parent", b"VERSION|SHA256SUMS/subfile\n", b"aliases candidate metadata"),
            ("duplicate manifest destination", b"VERSION|runtime/freak_runtime.c\n", b"duplicate distribution"),
            ("casefold metadata alias", b"VERSION|BUILD-INFO.JSON\n", b"aliases candidate metadata"),
            ("file-directory conflict", b"VERSION|runtime\n", b"both a file and a directory"),
            ("hidden Python compiler", b"VERSION|runtime/compiler.py\n", b"Python compiler/runtime"),
        ):
            distribution.write_bytes(original_manifest + row)
            bad = dict(fixture_record, all_inputs_before=dict(fixture_record["all_inputs_before"]),
                       all_inputs_after=dict(fixture_record["all_inputs_after"]))
            for inventory in ("all_inputs_before", "all_inputs_after"):
                bad[inventory]["packaging/distribution-files.manifest"] = digest(distribution.read_bytes())
            write_record(bad)
            rejected(name, expected, selected_repo=fixture, selected_record=selected_record)
        distribution.write_bytes(original_manifest)
        write_record()
        if os.name != "nt":
            external = root / "external-header"
            external.write_bytes(previous)
            path.unlink()
            path.symlink_to(external)
            rejected("symlink payload", b"symlink input", selected_repo=fixture, selected_record=selected_record)
            path.unlink()
            path.write_bytes(previous)
        existing = root / "existing.tar.gz"
        existing.write_bytes(b"preserve existing output")
        result = invoke(existing)
        assert result.returncode != 0 and existing.read_bytes() == b"preserve existing output"
        checks.append("existing output preserved")
        specification = importlib.util.spec_from_file_location("candidate_archive_under_test", packager)
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        # Logical member paths stay POSIX even on a Windows packaging host.
        nested_files = {"runtime/third_party/library/é.txt": (b"native bytes", 0o644)}
        for kind in ("zip", "tar.gz"):
            native = root / ("logical-native." + kind)
            windows = root / ("logical-windows." + kind)
            module.write_archive(native, nested_files, kind)
            with patch.object(module, "Path", PureWindowsPath):
                module.write_archive(windows, nested_files, kind)
            assert native.read_bytes() == windows.read_bytes()
            if kind == "zip":
                with zipfile.ZipFile(windows) as archive:
                    assert "freak/runtime/third_party/library/" in archive.namelist()
                    assert all("\\" not in name for name in archive.namelist())
            else:
                with tarfile.open(windows) as archive:
                    assert "freak/runtime/third_party/library" in archive.getnames()
                    assert all("\\" not in name for name in archive.getnames())
        checks.append("host-independent logical archive paths")
        argv, link, writer = sys.argv, module.os.link, module.write_archive
        raced = root / "raced.tar.gz"
        try:
            sys.argv = command(raced)[1:]
            def race(source: Path, destination: Path) -> None:
                Path(destination).write_bytes(b"concurrent creator")
                link(source, destination)
            module.os.link = race
            assert module.main() == 1 and raced.read_bytes() == b"concurrent creator"
            module.os.link = link
            failed_output = root / "failed-write.tar.gz"
            sys.argv = command(failed_output)[1:]
            def fail_write(destination: Path, files: dict, kind: str) -> None:
                destination.write_bytes(b"partial private archive")
                raise OSError("injected archive write failure")
            module.write_archive = fail_write
            assert module.main() == 1 and not failed_output.exists()
            assert not list(root.glob(".freak-candidate-*"))
        finally:
            sys.argv, module.os.link, module.write_archive = argv, link, writer
        checks.append("atomic publication race and failed private write preserve output/cleanup")
        assert digest(freak.read_bytes()) == source_hash
    report = {"status": "pass", "provisional": args.provisional, "native_sha256": source_hash,
              "source_sha": original_record["source_sha"], "packager_sha256": digest(packager.read_bytes()), "checks": checks}
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(report, indent=2) + "\n")
    print(f"PASS candidate archive {len(checks)} contract groups; provisional={args.provisional}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
