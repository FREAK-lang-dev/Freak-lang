#!/usr/bin/env python3
"""Create a byte-verified candidate archive from explicitly supplied native tools."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import struct
import subprocess
import tarfile
import tempfile
import unicodedata
import zipfile

COMPILER_SOURCES = tuple(f"src/compiler/v3/{name}.fk" for name in (
    "globals", "helpers", "lexer", "parser", "checker", "emit_c", "emit_llvm", "main"))
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
LIMIT = 64 * 1024 * 1024
METADATA = ("build-info.json", "build-record.json", "payload-inventory.json",
            "SHA256SUMS", "distribution-files.manifest")


class ArchiveError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ArchiveError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def logical(path: str) -> str:
    require(isinstance(path, str) and path and len(path.encode("utf-8")) <= 4096,
            "inventory path must be a nonempty bounded string")
    require(not path.startswith("/") and "\\" not in path, "unsafe inventory path: " + path)
    for part in path.split("/"):
        require(part not in ("", ".", "..") and not part.endswith((".", " "))
                and not any(ord(ch) < 32 or ord(ch) == 127 or ch in '<>:"|?*' for ch in part),
                "unsafe inventory path: " + path)
        require(part.casefold() not in (".git", "__pycache__", ".cache"), "non-product inventory path: " + path)
        stem = part.split(".")[0].upper()
        require(stem not in {"CON", "PRN", "AUX", "NUL"}
                and not re.fullmatch(r"(?:COM|LPT)[1-9]", stem),
                "nonportable inventory path: " + path)
    return path


def ordinary(path: Path, *, directory: bool = False) -> os.stat_result:
    for ancestor in (*reversed(path.parents), path):
        info = ancestor.lstat()
        require(not stat.S_ISLNK(info.st_mode)
                and not getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400),
                "symlink input or path component: " + str(ancestor))
        if ancestor != path or directory:
            require(stat.S_ISDIR(info.st_mode), "expected ordinary directory: " + str(ancestor))
    info = path.lstat()
    require(stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode),
            "expected ordinary " + ("directory: " if directory else "file: ") + str(path))
    return info


def read(path: Path, limit: int = LIMIT) -> bytes:
    ordinary(path)
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0))
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_size <= limit,
                "input is not a bounded ordinary file: " + str(path))
        with os.fdopen(fd, "rb", closefd=False) as stream:
            data = stream.read(limit + 1)
        after = os.fstat(fd)
        require(len(data) <= limit and len(data) == before.st_size
                and (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
                == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
                "input changed during its bounded read: " + str(path))
        return data
    finally:
        os.close(fd)


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        require(key not in result, "duplicate build-record key: " + key)
        result[key] = value
    return result


def digest_map(value: object, name: str) -> dict[str, str]:
    require(isinstance(value, dict) and bool(value), "missing inventory: " + name)
    for path, digest in value.items():
        logical(path)
        require(isinstance(digest, str) and SHA256.fullmatch(digest) is not None,
                "invalid SHA256 in " + name + ": " + path)
    return value


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", "core.fsmonitor=false", "--no-pager", *args], cwd=repo,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"}, capture_output=True, timeout=15)
    require(result.returncode == 0 and len(result.stdout) <= 1024 * 1024,
            "cannot inspect the explicit Git source snapshot")
    return result.stdout.decode("utf-8").strip()


def native_identity(data: bytes) -> dict[str, str]:
    if data.startswith(b"\x7fELF"):
        require(len(data) >= 20 and data[4] in (1, 2) and data[5] in (1, 2), "invalid ELF binary")
        machine = int.from_bytes(data[18:20], "little" if data[5] == 1 else "big")
        require(int.from_bytes(data[16:18], "little" if data[5] == 1 else "big") in (2, 3),
                "supplied ELF image is not an executable")
        return {"format": "ELF", "architecture": {62: "x86_64", 183: "aarch64"}.get(machine, str(machine))}
    if data.startswith(b"MZ"):
        require(len(data) >= 64, "invalid PE binary")
        offset = int.from_bytes(data[60:64], "little")
        require(offset + 24 <= len(data) and data[offset:offset + 4] == b"PE\0\0", "invalid PE binary")
        machine = int.from_bytes(data[offset + 4:offset + 6], "little")
        flags = int.from_bytes(data[offset + 22:offset + 24], "little")
        require(flags & 2 and not flags & 0x2000, "supplied PE image is not an executable")
        return {"format": "PE", "architecture": {0x8664: "x86_64", 0xAA64: "aarch64"}.get(machine, str(machine))}
    if data[:4] in (b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf"):
        require(len(data) >= 16, "invalid Mach-O binary")
        machine = struct.unpack("<I" if data[:4] == b"\xcf\xfa\xed\xfe" else ">I", data[4:8])[0]
        require(struct.unpack("<I" if data[:4] == b"\xcf\xfa\xed\xfe" else ">I", data[12:16])[0] == 2,
                "supplied Mach-O image is not an executable")
        return {"format": "Mach-O", "architecture": {0x1000007: "x86_64", 0x100000C: "aarch64"}.get(machine, str(machine))}
    raise ArchiveError("supplied product executable is not a native ELF, PE, or Mach-O image")


def manifest(data: bytes) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    names: set[str] = set()
    sources: set[str] = set()
    for line in data.decode("utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split("|")
        require(len(parts) == 2, "distribution manifest row must be source|destination")
        source, destination = (logical(part) for part in parts)
        folded = unicodedata.normalize("NFC", destination).casefold()
        require(folded not in names and source not in sources, "duplicate distribution source/destination")
        reserved_paths = {name.casefold() for name in (*METADATA, "freak", "hangar", "freak.exe", "hangar.exe")}
        require(folded not in reserved_paths
                and not any(folded.startswith(reserved + "/") for reserved in reserved_paths),
                "distribution destination aliases candidate metadata or executable")
        require(not destination.lower().endswith((".py", ".pyc", ".pyo")), "Python compiler/runtime files are not candidate payload")
        names.add(folded)
        sources.add(source)
        rows.append((source, destination))
    require(bool(rows), "distribution manifest is empty")
    require(not any("/".join(name.split("/")[:index]) in names
                    for name in names for index in range(1, len(name.split("/")))),
            "distribution destination is both a file and a directory")
    return rows


def native_hash(record: dict, name: str) -> str:
    hashes = record.get("native_hashes")
    require(isinstance(hashes, dict), "missing native binary inventory")
    keys = [key for key in (name, name + ".exe") if key in hashes]
    require(len(keys) == 1 and isinstance(hashes[keys[0]], str) and SHA256.fullmatch(hashes[keys[0]]) is not None,
            "missing or ambiguous native binary hash: " + name)
    return hashes[keys[0]]


def snapshot(repo: Path, freak: Path, hangar: Path, build_record: Path, provisional: bool) -> tuple[dict, dict[str, tuple[bytes, int]]]:
    ordinary(repo, directory=True)
    raw_record = read(build_record, 8 * 1024 * 1024)
    record = json.loads(raw_record, object_pairs_hook=unique_object)
    require(isinstance(record, dict) and record.get("status") == "pass"
            and record.get("inputs_unchanged") is True, "build record does not describe a successful unchanged reconstruction")
    before = digest_map(record.get("all_inputs_before"), "all_inputs_before")
    after = digest_map(record.get("all_inputs_after"), "all_inputs_after")
    require(before == after, "reconstruction inputs changed between before/after inventories")
    source_inputs = digest_map(record.get("source_inputs"), "source_inputs")
    runtime_inputs = digest_map(record.get("runtime_inputs"), "runtime_inputs")
    source_sha = record.get("source_sha")
    require(isinstance(source_sha, str) and COMMIT.fullmatch(source_sha) is not None, "invalid source commit in build record")
    head = git(repo, "rev-parse", "HEAD")
    tree = git(repo, "rev-parse", "HEAD^{tree}")
    dirty = git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    require(provisional or (head == source_sha and not dirty and not record.get("uncommitted_delta")),
            "final archive requires clean Git HEAD matching the build record; use --provisional for an explicit interim snapshot")
    require(record.get("source_tree") is None or record["source_tree"] == tree,
            "recorded Git tree does not match the explicit source checkout")
    captured = {path: read(repo / path) for path in before}
    for path, expected in before.items():
        require(sha(captured[path]) == expected, "stale reconstruction input hash: " + path)
    for name, mapping in (("source_inputs", source_inputs), ("runtime_inputs", runtime_inputs)):
        require(all(before.get(path) == digest for path, digest in mapping.items()),
                name + " is inconsistent with the before/after inventory")
    # Admission and publication use the same captured bytes. Reopening a
    # manifest could admit a transient generation restored before validation.
    for path in ("packaging/cli-sources.manifest", "packaging/distribution-files.manifest"):
        if path not in captured:
            captured[path] = read(repo / path)
    cli_manifest = captured["packaging/cli-sources.manifest"]
    cli_paths = [logical(line) for line in cli_manifest.decode("utf-8").splitlines()]
    require(len(set(cli_paths)) == len(cli_paths), "duplicate CLI source inventory")
    require(set(source_inputs) == set(COMPILER_SOURCES) | set(cli_paths),
            "compiled compiler/CLI source inventory does not match the authoritative CLI manifest")
    distribution = captured["packaging/distribution-files.manifest"]
    rows = manifest(distribution)
    required = set(source_inputs) | {"packaging/cli-sources.manifest", "packaging/distribution-files.manifest",
                                    "VERSION", "build/freakc_v3.fk.c"} | {source for source, _ in rows}
    for folder in ("freakc/runtime", "third_party/llhttp", "std"):
        for path in (repo / folder).rglob("*"):
            require(not path.is_symlink(), "symlink inside build input inventory: " + str(path))
            if path.is_file():
                required.add(path.relative_to(repo).as_posix())
    embedding = repo / "tools/embed_diagnostic_cast.py"
    if embedding.exists():
        required.add(embedding.relative_to(repo).as_posix())
    for path in (repo / "src/diagnostics").rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            required.add(path.relative_to(repo).as_posix())
    require(set(runtime_inputs) == {path.relative_to(repo).as_posix()
                                  for path in (repo / "freakc/runtime").glob("freak*") if path.is_file()},
            "runtime input inventory does not match the reconstructed runtime")
    missing = sorted(required - before.keys())
    require(provisional or not missing, "final build record is missing required inventory: " + ", ".join(missing))
    for path in required - captured.keys():
        captured[path] = read(repo / path)
    version = captured["VERSION"].decode("ascii").strip()
    require(re.fullmatch(r"\d+\.\d+\.\d+", version) is not None, "invalid product VERSION")
    require(provisional or record.get("source_tree") == tree, "final record is missing exact Git source-tree identity")
    require(record.get("version") is None or record["version"] == version, "recorded product version is stale")
    require(provisional or record.get("version") == version, "final record is missing product version")
    toolchain = record.get("toolchain", record.get("build_tools"))
    require(provisional or isinstance(toolchain, dict) and bool(toolchain), "final record is missing build-time tool fingerprints")
    if toolchain is not None:
        require(isinstance(toolchain, dict), "invalid recorded toolchain")
        for name, tool in toolchain.items():
            require(isinstance(tool, dict) and isinstance(tool.get("path"), str)
                    and isinstance(tool.get("sha256"), str) and SHA256.fullmatch(tool["sha256"]) is not None
                    and isinstance(tool.get("version"), str) and bool(tool["version"]),
                    "incomplete build-time tool fingerprint: " + name)
    require(provisional or "clang" in toolchain and toolchain["clang"]["path"] == record.get("clang"),
            "final record does not fingerprint its selected Clang executable")
    require(provisional or isinstance(record.get("host"), dict)
            and all(isinstance(record["host"].get(key), str) and record["host"][key] for key in ("os", "machine")),
            "final record is missing build-host identity")
    binaries = {"freak": read(freak), "hangar": read(hangar)}
    for name, data in binaries.items():
        require(sha(data) == native_hash(record, name), "stale supplied native binary hash: " + name)
    compiler_sha = native_hash(record, "freakc_stage2")
    identity = native_identity(binaries["freak"])
    require(native_identity(binaries["hangar"]) == identity, "native product images have different platform identities")
    suffix = ".exe" if identity["format"] == "PE" else ""
    files = {destination: (captured[source], 0o644) for source, destination in rows}
    files.update({name + suffix: (data, 0o755) for name, data in binaries.items()})
    files["distribution-files.manifest"] = (distribution, 0o644)
    markers = {}
    for key, path in (("runtime_abi", "runtime/freak_abi"), ("runtime_api", "runtime/freak_runtime_api"),
                      ("std_abi", "std/freak_abi"), ("std_api", "std/freak_std_api")):
        require(path in files, "required product capability marker is not distributed: " + path)
        markers[key] = files[path][0].decode("ascii").strip()
        require(markers[key] and "\n" not in markers[key], "invalid product capability marker: " + path)
    require(markers["runtime_abi"] == markers["std_abi"], "runtime/stdlib ABI markers disagree")
    require("runtime/v4-native.manifest" in files, "missing private V4 runtime inventory")
    for line in files["runtime/v4-native.manifest"][0].decode("utf-8").splitlines():
        if line and not line.startswith("#"):
            parts = line.split(" ")
            require(len(parts) == 2 and parts[0] in ("source", "header", "asset", "marker")
                    and "runtime/" + logical(parts[1]) in files, "private V4 runtime inventory is not closed by the distribution manifest")
    inventory = canonical({path: {"sha256": sha(data), "size": len(data), "mode": format(mode, "04o")}
                           for path, (data, mode) in sorted(files.items())})
    info = {
        "schema": 1, "product": "FREAK", "version": version, "compiler_generation": "V3",
        "provisional": provisional, "source_sha": source_sha, "git_head": head, "git_tree": tree,
        "source_clean": not bool(dirty), "platform": identity, "build_host": record.get("host"), "capability_markers": markers,
        "build_tools": {"declared_clang": record.get("clang"), "recorded_toolchain": toolchain,
                        "native_stage2_sha256": compiler_sha, "seed_c_sha256": before.get("build/freakc_v3.fk.c"),
                        "archive_builder_sha256": sha(read(Path(__file__).absolute()))},
        "input_digests": {"build_record": sha(raw_record), "compiler_cli": sha(canonical(source_inputs)),
                         "runtime": sha(canonical(runtime_inputs)), "before": sha(canonical(before)),
                         "after": sha(canonical(after)), "distribution_manifest": sha(distribution),
                         "payload_inventory": sha(inventory)},
        "unrecorded_inputs": missing,
        "scope": "explicit provisional component snapshot" if provisional else "clean source and complete byte-verified reconstruction inventory",
    }
    files["build-info.json"] = (canonical(info), 0o644)
    files["build-record.json"] = (raw_record, 0o644)
    files["payload-inventory.json"] = (inventory, 0o644)
    files["SHA256SUMS"] = ("".join(sha(data) + "  " + path + "\n"
                                   for path, (data, _) in sorted(files.items())).encode("utf-8"), 0o644)
    # All archive data comes from these captured bytes, never from a later reopen.
    for path, data in captured.items():
        require(read(repo / path) == data, "source input changed while preparing archive: " + path)
    require(git(repo, "rev-parse", "HEAD") == head, "Git HEAD changed while preparing archive")
    require(provisional or not git(repo, "status", "--porcelain=v1", "--untracked-files=all"),
            "final Git snapshot became dirty while preparing archive")
    return info, files


def write_archive(path: Path, files: dict[str, tuple[bytes, int]], kind: str) -> None:
    directories = {"freak"}
    for name in files:
        directories.update("freak/" + parent.as_posix() for parent in PurePosixPath(name).parents if str(parent) != ".")
    if kind == "tar.gz":
        with path.open("wb") as raw, gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                for name in sorted(directories):
                    entry = tarfile.TarInfo(name)
                    entry.type, entry.mode = tarfile.DIRTYPE, 0o755
                    archive.addfile(entry)
                for name, (data, mode) in sorted(files.items()):
                    entry = tarfile.TarInfo("freak/" + name)
                    entry.size, entry.mode = len(data), mode
                    archive.addfile(entry, io.BytesIO(data))
    else:
        # Stored members avoid compressor-version differences in ZIP output.
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
            for name in sorted(directories):
                entry = zipfile.ZipInfo(name + "/", date_time=(1980, 1, 1, 0, 0, 0))
                entry.create_system, entry.external_attr = 3, (stat.S_IFDIR | 0o755) << 16 | 0x10
                archive.writestr(entry, b"")
            for name, (data, mode) in sorted(files.items()):
                entry = zipfile.ZipInfo("freak/" + name, date_time=(1980, 1, 1, 0, 0, 0))
                entry.create_system, entry.external_attr = 3, (stat.S_IFREG | mode) << 16
                archive.writestr(entry, data)
    with path.open("r+b") as raw:
        os.fsync(raw.fileno())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repo", "freak", "hangar", "build-record", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--provisional", action="store_true", help="explicit interim archive; retain hash checks and disclose incomplete inventory")
    parser.add_argument("--format", choices=("tar.gz", "zip"))
    args = parser.parse_args()
    try:
        repo, freak, hangar, build_record, output = (
            Path(os.path.abspath(value)) for value in (args.repo, args.freak, args.hangar, args.build_record, args.output))
        ordinary(output.parent, directory=True)
        require(not os.path.lexists(output), "archive output already exists; its bytes were preserved")
        require(args.provisional or not output.is_relative_to(repo),
                "final archive output must be outside the source checkout")
        kind = args.format or ("zip" if output.name.endswith(".zip") else "tar.gz" if output.name.endswith(".tar.gz") else "")
        require(kind in ("tar.gz", "zip"), "archive output must end in .tar.gz/.zip or select --format")
        info, files = snapshot(repo, freak, hangar, build_record, args.provisional)
        with tempfile.TemporaryDirectory(prefix=".freak-candidate-", dir=output.parent) as temporary:
            staged = Path(temporary) / "archive"
            write_archive(staged, files, kind)
            artifact_sha = sha(read(staged, 256 * 1024 * 1024))
            # Hard-link publication is atomic and refuses an existing destination.
            os.link(staged, output)
            durable = True
            if os.name != "nt":
                try:
                    directory = os.open(output.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
                    try:
                        os.fsync(directory)
                    finally:
                        os.close(directory)
                except OSError:
                    durable = False
            report = {"status": "pass" if durable else "published-durability-failed", "published": True,
                      "provisional": args.provisional, "source_sha": info["source_sha"],
                      "artifact_sha256": artifact_sha, "payload_inventory_sha256": info["input_digests"]["payload_inventory"],
                      "format": kind, "files": len(files), "output": str(output)}
            print(canonical(report).decode("utf-8"), end="")
            return 0 if durable else 1
    except (ArchiveError, OSError, ValueError, UnicodeError, subprocess.SubprocessError) as error:
        print("candidate archive: " + str(error), file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
