#!/usr/bin/env python3
"""Native public legacy Hangar lock admission and exact preservation controls.

A public build produces a genuine lock v2. Legacy commands must decline it
before effects; this gate does not claim graph-aware install/update support.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
import time
import tomllib

from v3_final_release_gate import manifest_entries
from v3_v35_acceptance import run_command
from windows_private_fixture import WindowsPrivateFixture

REPO = Path(__file__).resolve().parents[1]
ANSI = re.compile(r"\x1b\[[0-9;]*m")
PREFIX = "  Hangar legacy command refused hangar.lock: "
SUFFIX = ("  Existing project state was preserved; graph-aware Hangar commands "
          "are required for lock v2.\n")
WRITER_PREFIX = "  Hangar legacy writer refused project graph: "
WRITERS = (
    ("add", "missing", "https://example.invalid/missing"),
    ("install",), ("update",), ("update", "left"),
    ("remove", "left"), ("audit", "--fix"),
)
VERSION_BUMPS = ("patch", "minor", "major", "2.3.4")
COMMANDS = (
    ("add", "missing", "https://example.invalid/missing"),
    ("install",), ("update",), ("update", "left"),
    ("remove", "left"), ("audit",), ("audit", "--fix"), ("outdated",),
)
LEGACY = ('[[package]]\nname = "left"\nversion = "0.1.0"\n'
          'source = "owner/left"\n')


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(root: Path, readable_handles: dict[Path, int] | None = None) -> dict:
    result = {}
    for path in sorted(root.rglob("*")):
        info = path.lstat()
        relative = path.relative_to(root).as_posix()
        if stat.S_ISLNK(info.st_mode):
            result[relative] = ["symlink", os.readlink(path)]
        elif stat.S_ISDIR(info.st_mode):
            result[relative] = ["directory", stat.S_IMODE(info.st_mode)]
        else:
            assert stat.S_ISREG(info.st_mode), (path, "unexpected fixture file kind")
            if readable_handles and path in readable_handles:
                handle = readable_handles[path]
                held = os.fstat(handle)
                assert (info.st_dev, info.st_ino) == (held.st_dev, held.st_ino), "unreadable fixture was replaced"
                data = os.pread(handle, info.st_size, 0)
                digest = hashlib.sha256(data).hexdigest()
            else:
                digest = sha(path)
            result[relative] = ["file", info.st_size, stat.S_IMODE(info.st_mode), digest]
    return result


def comparison_output(stdout: bytes, stderr: bytes) -> str:
    """Compare LF/CRLF transport after raw channels have been retained.

    Normalize each channel separately so a CR/LF split across channels cannot
    manufacture a normalized line ending. Preserve lone CR and all other text.
    """
    transported = stdout.replace(b"\r\n", b"\n") + stderr.replace(b"\r\n", b"\n")
    return ANSI.sub("", transported.decode("utf-8", "replace"))


class Recorder:
    def __init__(self, root: Path):
        self.root = root
        self.records = []

    def checkpoint(self):
        target = self.root / "command-records.json"
        temporary = target.with_suffix(".tmp")
        temporary.write_text(json.dumps({"runner_pid": os.getpid(), "commands": self.records}, indent=2) + "\n")
        temporary.replace(target)

    def run(self, argv: list[str], cwd: Path, env: dict, label: str,
            timeout: int = 60, demote: bool = False) -> tuple[int, str]:
        index = len(self.records)
        began = time.time_ns()
        prefix = self.root / f"{index:03d}-command"

        def unprivileged():
            os.setgroups([])
            os.setgid(65534)
            os.setuid(65534)

        def retain(record):
            record.update(label=label, started_ns=began, demote_to_uid_65534=demote)
            if "returncode" in record:
                record.update(exit_code=record["returncode"], finished_ns=time.time_ns())
                for stream in ("stdout", "stderr"):
                    data = prefix.with_suffix("." + stream).read_bytes()
                    path = self.root / f"{index:03d}-{stream}.raw"
                    path.write_bytes(data)
                    record[stream] = {"path": str(path), "bytes": len(data), "sha256": sha(path)}
            self.checkpoint()

        result = run_command(argv, cwd=cwd, env=env, label=label, prefix=prefix,
                             records=self.records, expected=None, timeout=timeout,
                             preexec_fn=unprivileged if demote else None, on_record=retain)
        return result.returncode, comparison_output(result.stdout, result.stderr)


def fixtures(root: Path, clang: Path, recorder: Recorder, env: dict,
             private: WindowsPrivateFixture) -> Path:
    tools = root / "tools"
    tools.mkdir()
    private.claim_fresh_directories(tools)
    source = tools / "git-attempt.c"
    source.write_text(r'''#include <stdio.h>
#include <stdlib.h>
int main(void) {
    const char *report = getenv("FREAK_HANGAR_GIT_REPORT");
    if (!report) return 29;
    FILE *file = fopen(report, "ab");
    if (!file) return 30;
    fputs("attempted Git\n", file);
    if (fclose(file)) return 31;
    fputs("injected Git attempt\n", stderr);
    return 23;
}
''', encoding="ascii")
    git = tools / ("git.exe" if os.name == "nt" else "git")
    code, output = recorder.run([str(clang), str(source), "-o", str(git)], tools, env,
                                "compile-native-git-witness")
    assert code == 0, output
    return git


def project(root: Path, lock: bytes | None, private: WindowsPrivateFixture) -> None:
    root.mkdir()
    (root / "hangar.toml").write_text(
        '[project]\nname = "preservation"\nversion = "0.1.0"\n'
        '[dependencies]\nleft = { git = "owner/left", version = "0.1.0" }\n',
        encoding="utf-8")
    if lock is not None:
        (root / "hangar.lock").write_bytes(lock)
    installed = root / "hangar_modules" / "left"
    installed.mkdir(parents=True)
    (installed / "left.fk").write_text("task value() -> int { give back 42 }\n")
    (installed / "hangar.toml").write_text('[project]\nname = "left"\nversion = "0.1.0"\n')
    (root / "previous-build").write_bytes(b"previous compiled output\x00")
    (root / "previous-build.freak-run-cache").write_bytes(b"previous cache proof\n")
    private.claim_fresh_directories(root, root / "hangar_modules", installed)


def rejected(root: Path, invocation: tuple[str, Path, list[str]], recorder: Recorder,
             env: dict, report: Path, expected: str, label: str,
             demote: bool = False, readable_handles: dict[Path, int] | None = None) -> None:
    name, binary, prefix = invocation
    before = snapshot(root, readable_handles)
    for index, args in enumerate(COMMANDS):
        code, output = recorder.run([str(binary), *prefix, *args], root, env,
                                    f"{name}:{label}:{index}", demote=demote)
        assert code == 1, (label, args, code, output)
        if expected.endswith(":"):
            assert output.startswith(PREFIX + expected), (label, args, output)
            assert output.endswith("\n" + SUFFIX), output
        else:
            assert output == PREFIX + expected + "\n" + SUFFIX, (label, args, output)
        assert snapshot(root, readable_handles) == before, (label, args, "project generation changed")
        assert report.read_bytes() == b"", (label, args, "Git was attempted")
    print(f"native:{name}:{label}:preserved:{len(COMMANDS)}", flush=True)


@contextlib.contextmanager
def held_graph_lock(path: Path):
    # The runtime creates the lock file first, with its checked ownership.
    # POSIX uses the same flock. On Windows the live read/write handle conflicts
    # with the runtime's exclusive NtCreateFile share mode; byte locks do not.
    with path.open("rb+") as handle:
        if os.name != "nt":
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def writer_controls(root: Path, invocation: tuple[str, Path, list[str]],
                    recorder: Recorder, env: dict, report: Path,
                    private: WindowsPrivateFixture) -> None:
    name, binary, prefix = invocation
    cwd = root / f"{name}-writer-lock"
    project(cwd, LEGACY.encode(), private)
    original = snapshot(cwd)
    # A real early body return seeds the native owned private directory/file.
    code, output = recorder.run([str(binary), *prefix, "remove", "absent"], cwd, env,
                                f"{name}:writer:seed-native-lock")
    assert code == 1 and "Package 'absent' is not in hangar.toml" in output, output
    assert "ownership audit" not in output and report.read_bytes() == b"", output
    seeded = snapshot(cwd)
    assert set(seeded) - set(original) == {".freak", ".freak/graph.lock"}, seeded
    assert {key: seeded[key] for key in original} == original
    graph = cwd / ".freak/graph.lock"
    assert graph.is_file() and graph.read_bytes() == b""
    with held_graph_lock(graph):
        before = snapshot(cwd)
        for index, command in enumerate(WRITERS):
            code, output = recorder.run([str(binary), *prefix, *command], cwd, env,
                                        f"{name}:writer:held:{index}")
            assert code == 1 and output == (WRITER_PREFIX + "cannot hold graph.lock: " +
                "directory transaction lock is held or not a private regular file\n"), (command, output)
            assert snapshot(cwd) == before and report.read_bytes() == b"", (command, output)
        for command in (("audit",), ("outdated",)):
            code, output = recorder.run([str(binary), *prefix, *command], cwd, env,
                                        f"{name}:writer:held-read-only:{command[0]}")
            assert code == 0 and WRITER_PREFIX not in output and "ownership audit" not in output, output
            assert snapshot(cwd) == before and report.read_bytes() == b"", output
    # Presence alone does not exclude writers; an existing free lock is usable.
    code, output = recorder.run([str(binary), *prefix, "audit", "--fix"], cwd, env,
                                f"{name}:writer:free-existing-lock")
    assert code == 0 and "Computed SHA-256:" in output and "ownership audit" not in output, output
    assert report.read_bytes() == b"" and graph.read_bytes() == b""
    with held_graph_lock(graph):
        pass

    # Refuse retained journals under the held lock without trying recovery.
    marker = cwd / ".freak/transaction.marker"
    marker.write_bytes(b"retained graph transaction, deliberately uninterpreted\n")
    backup = cwd / ".freak/transaction.manifest.before"
    backup.write_bytes(b"retained manifest before image\n")
    before = snapshot(cwd)
    for index, command in enumerate(WRITERS):
        code, output = recorder.run([str(binary), *prefix, *command], cwd, env,
                                    f"{name}:writer:pending-journal:{index}")
        assert code == 1 and output == (WRITER_PREFIX +
            "pending or unreadable graph transaction.marker; graph-aware recovery is required\n"), (command, output)
        assert snapshot(cwd) == before and report.read_bytes() == b"", (command, output)
    # A non-file marker must also fail closed and retain its contents.
    marker.unlink()
    marker.mkdir()
    private.claim_fresh_directories(marker)
    (marker / "retained").write_bytes(b"not a journal file\n")
    before = snapshot(cwd)
    code, output = recorder.run([str(binary), *prefix, "remove", "left"], cwd, env,
                                f"{name}:writer:non-file-journal")
    assert code == 1 and output == (WRITER_PREFIX +
        "pending or unreadable graph transaction.marker; graph-aware recovery is required\n"), output
    assert snapshot(cwd) == before and report.read_bytes() == b"", output
    print(f"native:{name}:writer:common-held-lock-and-journal:preserved", flush=True)


def writer_manifest_controls(root: Path, invocation: tuple[str, Path, list[str]],
                             recorder: Recorder, env: dict, report: Path,
                             private: WindowsPrivateFixture) -> None:
    name, binary, prefix = invocation
    cases = (
        ("missing", None), ("empty", b""),
        ("malformed", b'[project\nname = "preservation"\n'),
        ("non-file", "directory"), ("nul", b'[project]\nname = "bad\x00name"\n'),
        ("invalid-utf8", b'[project]\nname = "bad\xffname"\n'),
        ("oversize", b"#" + b"x" * 1048576),
    )
    commands = (*WRITERS, *(("version", bump) for bump in VERSION_BUMPS))
    for label, contents in cases:
        cwd = root / f"{name}-writer-manifest-{label}"
        project(cwd, LEGACY.encode(), private)
        manifest = cwd / "hangar.toml"
        if contents is None:
            manifest.unlink()
        elif contents == "directory":
            manifest.unlink()
            manifest.mkdir()
            private.claim_fresh_directories(manifest)
            (manifest / "retained").write_bytes(b"not a project manifest\n")
        else:
            manifest.write_bytes(contents)
        before = snapshot(cwd)
        for index, command in enumerate(commands):
            code, output = recorder.run([str(binary), *prefix, *command], cwd, env,
                                        f"{name}:writer-manifest:{label}:{index}")
            assert code == 1, (label, command, code, output)
            if label == "missing":
                assert output == "  No hangar.toml found. Run 'hangar init' first.\n", output
            elif label == "malformed":
                assert output.startswith("  Invalid manifest ") and "unterminated table header" in output, output
            else:
                assert output.startswith(WRITER_PREFIX) and "project manifest" in output, output
            assert snapshot(cwd) == before and report.read_bytes() == b"", (label, command, output)
            assert not (cwd / ".freak").exists(), (label, command)
    print(f"native:{name}:writer:manifest-before-private-files:preserved", flush=True)


def writer_version_controls(root: Path, invocation: tuple[str, Path, list[str]],
                            recorder: Recorder, env: dict, report: Path,
                            private: WindowsPrivateFixture, diamond: Path) -> None:
    name, binary, prefix = invocation
    cwd = root / f"{name}-writer-version"
    project(cwd, LEGACY.encode(), private)
    before = snapshot(cwd)
    code, output = recorder.run([str(binary), *prefix, "version"], cwd, env,
                                f"{name}:version:display-without-private")
    assert code == 0 and output == "  preservation v0.1.0\n", output
    assert snapshot(cwd) == before and not (cwd / ".freak").exists() and report.read_bytes() == b""
    code, output = recorder.run([str(binary), *prefix, "remove", "absent"], cwd, env,
                                f"{name}:version:seed-native-lock")
    assert code == 1 and "Package 'absent' is not in hangar.toml" in output, output
    graph = cwd / ".freak/graph.lock"
    assert graph.is_file() and graph.read_bytes() == b""
    held_message = WRITER_PREFIX + "cannot hold graph.lock: directory transaction lock is held or not a private regular file\n"
    with held_graph_lock(graph):
        before = snapshot(cwd)
        for bump in VERSION_BUMPS:
            code, output = recorder.run([str(binary), *prefix, "version", bump], cwd, env,
                                        f"{name}:version:held:{bump}")
            assert code == 1 and output == held_message, output
            assert snapshot(cwd) == before and report.read_bytes() == b"", output
        code, output = recorder.run([str(binary), *prefix, "version"], cwd, env,
                                    f"{name}:version:held-display")
        assert code == 0 and output == "  preservation v0.1.0\n" and snapshot(cwd) == before, output
    versions = ("0.1.1", "0.2.0", "1.0.0", "2.3.4")
    for bump, expected in zip(VERSION_BUMPS, versions):
        before = snapshot(cwd)
        manifest_before = tomllib.loads((cwd / "hangar.toml").read_text())
        code, output = recorder.run([str(binary), *prefix, "version", bump], cwd, env,
                                    f"{name}:version:free:{bump}")
        assert code == 0 and output.endswith(f" -> {expected}\n"), output
        manifest_after = tomllib.loads((cwd / "hangar.toml").read_text())
        manifest_before["project"]["version"] = expected
        assert manifest_after == manifest_before, (manifest_before, manifest_after)
        after = snapshot(cwd)
        assert {key: value for key, value in after.items() if key != "hangar.toml"} == {
            key: value for key, value in before.items() if key != "hangar.toml"}, output
        assert graph.read_bytes() == b"" and report.read_bytes() == b""
        with held_graph_lock(graph):
            pass
    marker = cwd / ".freak/transaction.marker"
    marker.write_bytes(b"retained graph transaction\n")
    (cwd / ".freak/transaction.manifest.before").write_bytes(b"retained before image\n")
    before = snapshot(cwd)
    pending_message = WRITER_PREFIX + "pending or unreadable graph transaction.marker; graph-aware recovery is required\n"
    for bump in VERSION_BUMPS:
        code, output = recorder.run([str(binary), *prefix, "version", bump], cwd, env,
                                    f"{name}:version:pending:{bump}")
        assert code == 1 and output == pending_message and snapshot(cwd) == before, output
    code, output = recorder.run([str(binary), *prefix, "version"], cwd, env,
                                f"{name}:version:pending-display")
    assert code == 0 and output == "  preservation v2.3.4\n" and snapshot(cwd) == before, output
    marker.unlink()
    marker.mkdir()
    private.claim_fresh_directories(marker)
    (marker / "retained").write_bytes(b"not a journal file\n")
    before = snapshot(cwd)
    code, output = recorder.run([str(binary), *prefix, "version", "patch"], cwd, env,
                                f"{name}:version:non-file-journal")
    assert code == 1 and output == pending_message and snapshot(cwd) == before, output
    before = snapshot(diamond)
    # A lock v2 project bumps through the graph-aware writer; run it on a copy
    # so the shared diamond fixture keeps its generation.
    bumped = diamond.parent / f"{name}-version-graph-v2"
    shutil.copytree(diamond, bumped)
    private.claim_fresh_directories(bumped, *(path for path in bumped.rglob("*") if path.is_dir()))
    current = tomllib.loads((bumped / "hangar.toml").read_text())["project"]["version"]
    major, minor, patch = (int(part) for part in current.split("."))
    code, output = recorder.run([str(binary), *prefix, "version", "patch"], bumped, env,
                                f"{name}:version:graph-v2:patch")
    assert code == 0, output
    assert tomllib.loads((bumped / "hangar.toml").read_text())["project"]["version"] == f"{major}.{minor}.{patch + 1}", output
    assert tomllib.loads((bumped / "hangar.lock").read_text())["lock"]["schema"] == 2, output
    assert snapshot(diamond) == before and report.read_bytes() == b"", output
    manifest = tomllib.loads((diamond / "hangar.toml").read_text())["project"]
    code, output = recorder.run([str(binary), *prefix, "version"], diamond, env,
                                f"{name}:version:graph-v2-display")
    assert code == 0 and output == f"  {manifest['name']} v{manifest['version']}\n", output
    assert snapshot(diamond) == before and report.read_bytes() == b"", output
    print(f"native:{name}:writer:version-serialization-and-readonly:preserved", flush=True)


def audit_failed_repair_controls(root: Path, invocation: tuple[str, Path, list[str]],
                                 recorder: Recorder, env: dict, report: Path,
                                 private: WindowsPrivateFixture) -> None:
    name, binary, prefix = invocation
    cwd = root / f"{name}-audit-failed-repair"
    project(cwd, (LEGACY + 'sha256 = ""\n').encode(), private)
    code, output = recorder.run([str(binary), *prefix, "audit", "--fix"], cwd, env,
                                f"{name}:audit-repair:seed")
    assert code == 0 and "Computed SHA-256:" in output, output
    lock = cwd / "hangar.lock"
    lock.write_bytes(lock.read_bytes() + b"# retained lock comment\n")
    canonical = lock.read_bytes()
    digest = tomllib.loads(canonical.decode())["package"][0]["sha256"]
    assert re.fullmatch("[0-9a-f]{64}", digest), digest
    before = snapshot(cwd)
    code, output = recorder.run([str(binary), *prefix, "audit"], cwd, env,
                                f"{name}:audit-repair:clean")
    assert code == 0 and "ALL CLEAR" in output and "1 packages verified" in output, output
    assert snapshot(cwd) == before and report.read_bytes() == b""
    installed = cwd / "hangar_modules/left"
    (installed / "left.fk").write_text("task value() -> int { give back 999 }\n-- tampered package\n")
    before = snapshot(cwd)
    for label, command in (("tampered", ("audit",)), ("failed", ("audit", "--fix")),
                           ("failed-again", ("audit", "--fix")), ("still-tampered", ("audit",))):
        code, output = recorder.run([str(binary), *prefix, *command], cwd, env,
                                    f"{name}:audit-repair:{label}")
        assert code == 1 and "INTEGRITY FAILURE" in output and "ALL CLEAR" not in output, output
        if len(command) == 2:
            assert "Cannot safely replace left" in output and "NOT REPAIRED" in output, output
        assert snapshot(cwd) == before and lock.read_bytes() == canonical and report.read_bytes() == b"", output
        assert tomllib.loads(lock.read_text())["package"][0]["sha256"] == digest
    shutil.rmtree(installed)
    failure_report = root / f"{name}-audit-repair-git-attempts.raw"
    failure_report.write_bytes(b"")
    failed_env = {**env, "FREAK_HANGAR_GIT_REPORT": str(failure_report)}
    code, output = recorder.run([str(binary), *prefix, "audit", "--fix"], cwd, failed_env,
                                f"{name}:audit-repair:missing-fetch-failure")
    assert code == 1 and "Git package fetch failed" in output and "NOT REPAIRED" in output, output
    assert "ALL CLEAR" not in output and lock.read_bytes() == canonical and not installed.exists(), output
    assert failure_report.read_bytes() == b"attempted Git\n" and report.read_bytes() == b"", output
    assert not tuple((cwd / "hangar_modules").glob(".hangar-stage-*")), "owned staging survived failed fetch"
    before = snapshot(cwd)
    code, output = recorder.run([str(binary), *prefix, "audit"], cwd, env,
                                f"{name}:audit-repair:still-missing")
    assert code == 1 and "MISSING" in output and "ALL CLEAR" not in output, output
    assert snapshot(cwd) == before and lock.read_bytes() == canonical and report.read_bytes() == b""
    print(f"native:{name}:audit:failed-repair-keeps-expected-hash:preserved", flush=True)


def integrity_failure_tools(root: Path, clang: Path, recorder: Recorder, env: dict,
                            private: WindowsPrivateFixture) -> dict[str, Path]:
    tools = root / "integrity-tools"
    tools.mkdir()
    private.claim_fresh_directories(tools)
    source = tools / "integrity-failure.c"
    source.write_text(r'''#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int argc, char **argv) {
    if (argc == 2 && !strcmp(argv[1], "--version")) {
        const char *version = getenv("FREAK_HANGAR_ARCHIVE_VERSION");
        if (version && !strcmp(version, "failed")) {
            fputs("injected archive version failure\n", stderr);
            return 23;
        }
        puts(version && !strcmp(version, "unknown") ? "unsupported archive tool" :
             version && !strcmp(version, "libarchive") ? "bsdtar 3.7.4 - libarchive 3.7.4" :
             "tar (GNU tar) controlled archive witness");
        return 0;
    }
    const char *version = getenv("FREAK_HANGAR_ARCHIVE_VERSION");
    if (version && !strcmp(version, "libarchive")) {
        int stable_option = 0;
        for (int i = 1; i + 1 < argc; ++i) {
            if (!strcmp(argv[i], "--options") && !strcmp(argv[i + 1], "gzip:!timestamp")) stable_option = 1;
        }
        if (!stable_option) {
            fputs("required stable gzip option was not supplied\n", stderr);
            return 32;
        }
    }
    const char *report = getenv("FREAK_HANGAR_INTEGRITY_REPORT");
    const char *kind = getenv("FREAK_HANGAR_INTEGRITY_KIND");
    if (!report || !kind) return 29;
    FILE *file = fopen(report, "ab");
    if (!file) return 30;
    fprintf(file, "attempted %s tool\n", kind);
    if (fclose(file)) return 31;
    fputs("injected integrity tool failure\n", stderr);
    return 23;
}
''', encoding="ascii")
    binary = tools / ("failure.exe" if os.name == "nt" else "failure")
    code, output = recorder.run([str(clang), str(source), "-o", str(binary)], tools, env,
                                "compile-native-integrity-failure-witness")
    assert code == 0, output
    report = root / "integrity-tool-positive.raw"
    report.write_bytes(b"")
    witness_env = {**env, "FREAK_HANGAR_INTEGRITY_REPORT": str(report),
                   "FREAK_HANGAR_INTEGRITY_KIND": "archive"}
    code, output = recorder.run([str(binary), "controlled-attempt"], root, witness_env,
                                "native-integrity-failure-witness-positive-control")
    assert code == 23 and output == "injected integrity tool failure\n", output
    assert report.read_bytes() == b"attempted archive tool\n"
    directories = {}
    for kind, names in (("archive", ("tar",)),
                        ("hash", ("certutil",) if os.name == "nt" else ("sha256sum", "shasum"))):
        directory = tools / kind
        directory.mkdir()
        private.claim_fresh_directories(directory)
        for name in names:
            shutil.copy2(binary, directory / (name + ".exe" if os.name == "nt" else name))
        directories[kind] = directory
    return directories


def audit_hash_failure_controls(root: Path, invocation: tuple[str, Path, list[str]],
                               recorder: Recorder, env: dict, report: Path,
                               private: WindowsPrivateFixture, tools: dict[str, Path]) -> None:
    name, binary, prefix = invocation
    cwd = root / f"{name}-audit-hash-failure"
    project(cwd, (LEGACY + 'sha256 = ""\n').encode(), private)
    code, output = recorder.run([str(binary), *prefix, "audit", "--fix"], cwd, env,
                                f"{name}:integrity-failure:seed")
    assert code == 0 and "Computed SHA-256:" in output, output
    lock = cwd / "hangar.lock"
    lock.write_bytes(lock.read_bytes() + b"# retain expected checksum on tool failure\n")
    canonical = lock.read_bytes()
    digest = tomllib.loads(canonical.decode())["package"][0]["sha256"]
    assert re.fullmatch("[0-9a-f]{64}", digest)
    before = snapshot(cwd)
    for kind, directory in tools.items():
        failure_report = root / f"{name}-integrity-{kind}-attempts.raw"
        failed_env = {**env, "PATH": str(directory) + os.pathsep + env["PATH"],
                      "FREAK_HANGAR_INTEGRITY_REPORT": str(failure_report),
                      "FREAK_HANGAR_INTEGRITY_KIND": kind}
        expected_attempts = 2 if kind == "hash" and os.name != "nt" else 1
        for mode, command in (("readonly", ("audit",)), ("fix", ("audit", "--fix"))):
            failure_report.write_bytes(b"")
            code, output = recorder.run([str(binary), *prefix, *command], cwd, failed_env,
                                        f"{name}:integrity-failure:{kind}:{mode}")
            assert code == 1 and "Could not compute hash for left" in output, output
            assert "ALL CLEAR" not in output and "  OK left" not in output, output
            if mode == "fix":
                assert "Cannot safely replace left" in output and "NOT REPAIRED" in output, output
            assert failure_report.read_bytes() == (f"attempted {kind} tool\n".encode() * expected_attempts)
            assert snapshot(cwd) == before and lock.read_bytes() == canonical and report.read_bytes() == b"", output
            assert tomllib.loads(lock.read_text())["package"][0]["sha256"] == digest
    # Unknown/failed capability queries must not invoke an archive. A known
    # libarchive whose stable option fails must not retry without the option.
    for version in ("unknown", "failed", "libarchive"):
        failure_report = root / f"{name}-integrity-capability-{version}.raw"
        failed_env = {**env, "PATH": str(tools["archive"]) + os.pathsep + env["PATH"],
                      "FREAK_HANGAR_INTEGRITY_REPORT": str(failure_report),
                      "FREAK_HANGAR_INTEGRITY_KIND": "archive",
                      "FREAK_HANGAR_ARCHIVE_VERSION": version}
        for mode, command in (("readonly", ("audit",)), ("fix", ("audit", "--fix"))):
            failure_report.write_bytes(b"")
            code, output = recorder.run([str(binary), *prefix, *command], cwd, failed_env,
                                        f"{name}:integrity-capability:{version}:{mode}")
            assert code == 1 and "Could not compute hash for left" in output, output
            assert "ALL CLEAR" not in output and "  OK left" not in output, output
            if version != "libarchive":
                assert "cannot identify supported native tar capabilities" in output, output
            if mode == "fix":
                assert "Cannot safely replace left" in output and "NOT REPAIRED" in output, output
            assert failure_report.read_bytes() == (b"attempted archive tool\n" if version == "libarchive" else b"")
            assert snapshot(cwd) == before and lock.read_bytes() == canonical and report.read_bytes() == b"", output
            assert tomllib.loads(lock.read_text())["package"][0]["sha256"] == digest
    code, output = recorder.run([str(binary), *prefix, "audit"], cwd, env,
                                f"{name}:integrity-failure:working-tools-recovery")
    assert code == 0 and "ALL CLEAR" in output and "1 packages verified" in output, output
    assert snapshot(cwd) == before and report.read_bytes() == b""
    # A deliberately absent checksum remains UNVERIFIED without invoking tools.
    unverified = root / f"{name}-audit-unverified-compatibility"
    project(unverified, LEGACY.encode(), private)
    failure_report = root / f"{name}-unverified-integrity-attempts.raw"
    failure_report.write_bytes(b"")
    failed_env = {**env, "PATH": str(tools["archive"]) + os.pathsep + env["PATH"],
                  "FREAK_HANGAR_INTEGRITY_REPORT": str(failure_report),
                  "FREAK_HANGAR_INTEGRITY_KIND": "archive"}
    before = snapshot(unverified)
    code, output = recorder.run([str(binary), *prefix, "audit"], unverified, failed_env,
                                f"{name}:integrity-failure:absent-checksum-compatibility")
    assert code == 0 and "UNVERIFIED" in output and "0 packages verified" in output, output
    assert snapshot(unverified) == before and failure_report.read_bytes() == b"" and report.read_bytes() == b""

    # A requested checksum repair must fail if the checksum cannot be computed.
    # Seed the writer's private lock first so each failed repair must preserve
    # the complete project, including comments in the previously unhashed lock.
    code, output = recorder.run([str(binary), *prefix, "remove", "absent"], unverified, env,
                                f"{name}:unverified-fix:seed-native-lock")
    assert code == 1 and "Package 'absent' is not in hangar.toml" in output, output
    unverified_lock = unverified / "hangar.lock"
    unverified_lock.write_bytes(unverified_lock.read_bytes() + b"# preserve unhashed lock on failed repair\n")
    unverified_canonical = unverified_lock.read_bytes()
    before = snapshot(unverified)
    failures = [(kind, directory, None) for kind, directory in tools.items()]
    failures.extend(("archive", tools["archive"], version) for version in ("unknown", "failed", "libarchive"))
    for kind, directory, version in failures:
        failure_report.write_bytes(b"")
        failed_env = {**env, "PATH": str(directory) + os.pathsep + env["PATH"],
                      "FREAK_HANGAR_INTEGRITY_REPORT": str(failure_report),
                      "FREAK_HANGAR_INTEGRITY_KIND": kind}
        if version is not None:
            failed_env["FREAK_HANGAR_ARCHIVE_VERSION"] = version
        code, output = recorder.run([str(binary), *prefix, "audit", "--fix"], unverified, failed_env,
                                    f"{name}:unverified-fix:{kind}:{version or 'native-failure'}")
        assert code == 1 and "Could not compute hash for left" in output and "NOT REPAIRED" in output, output
        assert "ALL CLEAR" not in output and "Computed SHA-256:" not in output, output
        expected_attempts = 0 if version in ("unknown", "failed") else 2 if kind == "hash" and os.name != "nt" else 1
        assert failure_report.read_bytes() == f"attempted {kind} tool\n".encode() * expected_attempts
        assert snapshot(unverified) == before and unverified_lock.read_bytes() == unverified_canonical and report.read_bytes() == b"", output
        assert tomllib.loads(unverified_lock.read_text())["package"][0].get("sha256", "") == ""
    code, output = recorder.run([str(binary), *prefix, "audit", "--fix"], unverified, env,
                                f"{name}:unverified-fix:working-tools-recovery")
    assert code == 0 and "Computed SHA-256:" in output and "1 packages verified" in output, output
    assert re.fullmatch("[0-9a-f]{64}", tomllib.loads(unverified_lock.read_text())["package"][0]["sha256"])
    after = snapshot(unverified)
    assert {key: value for key, value in after.items() if key != "hangar.lock"} == {
        key: value for key, value in before.items() if key != "hangar.lock"}, output
    assert report.read_bytes() == b""
    code, output = recorder.run([str(binary), *prefix, "audit"], unverified, env,
                                f"{name}:unverified-fix:recovered-readonly")
    assert code == 0 and "ALL CLEAR" in output and "1 packages verified" in output, output
    assert snapshot(unverified) == after and report.read_bytes() == b"", output
    print(f"native:{name}:audit:failed-tools-never-claim-verification:preserved", flush=True)


def audit_stable_hash_controls(root: Path, invocation: tuple[str, Path, list[str]],
                               recorder: Recorder, env: dict, report: Path,
                               private: WindowsPrivateFixture) -> None:
    name, binary, prefix = invocation
    cwd = root / f"{name}-audit-stable-archive"
    project(cwd, (LEGACY + 'sha256 = ""\n').encode(), private)
    code, output = recorder.run([str(binary), *prefix, "audit", "--fix"], cwd, env,
                                f"{name}:integrity-stability:seed")
    assert code == 0 and "Computed SHA-256:" in output, output
    canonical = (cwd / "hangar.lock").read_bytes()
    digest = tomllib.loads(canonical.decode())["package"][0]["sha256"]
    assert re.fullmatch("[0-9a-f]{64}", digest)
    before = snapshot(cwd)
    proof = {"expected_sha256": digest, "delayed_audits": [], "atime_changes": []}
    for label, command in (("across-second", ("audit",)),
                           ("changed-atime", ("audit",)),
                           ("across-second-fix", ("audit", "--fix"))):
        if label == "changed-atime":
            installed = cwd / "hangar_modules" / "left"
            for path in (installed, *sorted(installed.rglob("*"))):
                info = path.stat()
                os.utime(path, ns=(info.st_atime_ns - 10_000_000_000, info.st_mtime_ns))
                changed = path.stat()
                assert changed.st_atime_ns != info.st_atime_ns and changed.st_mtime_ns == info.st_mtime_ns
                proof["atime_changes"].append({"path": path.relative_to(cwd).as_posix(),
                    "old_atime_ns": info.st_atime_ns, "new_atime_ns": changed.st_atime_ns,
                    "unchanged_mtime_ns": changed.st_mtime_ns})
            assert snapshot(cwd) == before, "atime control changed package bytes/kinds/modes"
        began_ns = time.time_ns()
        time.sleep(1.1)
        code, output = recorder.run([str(binary), *prefix, *command], cwd, env,
                                    f"{name}:integrity-stability:{label}")
        finished_ns = time.time_ns()
        assert finished_ns // 1_000_000_000 > began_ns // 1_000_000_000
        assert code == 0 and "ALL CLEAR" in output and "1 packages verified" in output, output
        assert "INTEGRITY FAILURE" not in output and "Reinstalling" not in output, output
        assert snapshot(cwd) == before and (cwd / "hangar.lock").read_bytes() == canonical and report.read_bytes() == b"", output
        proof["delayed_audits"].append({"label": label, "began_ns": began_ns, "finished_ns": finished_ns})
    (recorder.root / f"{name}-integrity-stability-proof.json").write_text(json.dumps(proof, indent=2) + "\n")
    print(f"native:{name}:audit:delayed-and-atime-hashes-stable:preserved", flush=True)


def init_generation_controls(root: Path, invocation: tuple[str, Path, list[str]],
                             recorder: Recorder, env: dict, report: Path,
                             private: WindowsPrivateFixture, diamond: Path) -> None:
    """Orphan generations must never be initialized or recovered implicitly."""
    name, binary, prefix = invocation
    cases = (
        ("legacy-lock", "lock", LEGACY.encode()),
        ("genuine-v2", "lock", (diamond / "hangar.lock").read_bytes()),
        ("unsupported-lock", "lock", b"lock.schema = 99\n"),
        ("empty-legacy-generation", "lock", b"# retained empty legacy generation\n"),
        ("non-file-lock", "directory-lock", None),
        ("empty-graph-lock", "graph", b""),
        ("nonempty-graph-lock", "graph", b"retained writer state\x00"),
        ("non-file-graph-lock", "directory-graph", None),
        ("non-file-private", "private-file", None),
        ("journal-marker", "journal", "transaction.marker"),
        ("journal-manifest-before", "journal", "transaction.manifest.before"),
        ("journal-lock-before", "journal", "transaction.lock.before"),
        ("non-file-journal", "directory-journal", None),
        ("non-file-manifest", "directory-manifest", None),
    )

    def decline(cwd: Path, label: str, *, command: list[str] | None = None,
                demote: bool = False, readable_handles: dict[Path, int] | None = None):
        before = snapshot(cwd, readable_handles)
        code, output = recorder.run([str(binary), *prefix, *(command or ["init"])], cwd, env,
                                    f"{name}:init-generation:{label}", demote=demote)
        assert code == 1 and output.startswith((PREFIX, WRITER_PREFIX)), (label, code, output)
        assert "INITIALIZED" not in output and "ownership audit" not in output, output
        assert snapshot(cwd, readable_handles) == before and report.read_bytes() == b"", (label, output)

    for label, kind, contents in cases:
        cwd = root / f"{name}-init-generation-{label}"
        project(cwd, None, private)
        (cwd / "hangar.toml").unlink()
        if kind == "lock":
            (cwd / "hangar.lock").write_bytes(contents)
        elif kind == "directory-lock":
            (cwd / "hangar.lock").mkdir()
            (cwd / "hangar.lock/retained").write_bytes(b"retained lock directory\n")
        elif kind == "private-file":
            (cwd / ".freak").write_bytes(b"not a private directory\n")
        elif kind == "directory-manifest":
            (cwd / "hangar.toml").mkdir()
            (cwd / "hangar.toml/retained").write_bytes(b"retained manifest directory\n")
        else:
            state = cwd / ".freak"
            state.mkdir(mode=0o700)
            private.claim_fresh_directories(state)
            if kind == "graph":
                (state / "graph.lock").write_bytes(contents)
                (state / "graph.lock").chmod(0o600)
            elif kind == "directory-graph":
                (state / "graph.lock").mkdir()
                (state / "graph.lock/retained").write_bytes(b"retained graph lock directory\n")
            elif kind == "journal":
                (state / contents).write_bytes(b"retained graph transaction authority\n")
            else:
                assert kind == "directory-journal"
                (state / "transaction.marker").mkdir()
                (state / "transaction.marker/retained").write_bytes(b"retained journal directory\n")
        decline(cwd, label)

    # Use the runtime's own checked lock creation, then remove only the
    # fixture's manifest. Held and free orphan graph locks both retain authority.
    cwd = root / f"{name}-init-generation-held"
    project(cwd, LEGACY.encode(), private)
    code, output = recorder.run([str(binary), *prefix, "remove", "absent"], cwd, env,
                                f"{name}:init-generation:seed-native-lock")
    assert code == 1 and "Package 'absent' is not in hangar.toml" in output, output
    assert "ownership audit" not in output and report.read_bytes() == b"", output
    (cwd / "hangar.toml").unlink()
    (cwd / "hangar.lock").unlink()
    graph = cwd / ".freak/graph.lock"
    assert graph.is_file() and graph.read_bytes() == b""
    with held_graph_lock(graph):
        decline(cwd, "concurrent-held-writer")
    decline(cwd, "free-retained-writer")
    with held_graph_lock(graph):
        pass

    # Preserve ordinary existing-empty and genuinely absent target behavior.
    for label in ("existing-empty", "absent-target"):
        parent = root / f"{name}-init-generation-{label}"
        parent.mkdir()
        private.claim_fresh_directories(parent)
        target = parent / "fresh-project"
        if label == "existing-empty":
            target.mkdir()
            private.claim_fresh_directories(target)
        code, output = recorder.run([str(binary), *prefix, "init", "fresh-project"], parent, env,
                                    f"{name}:init-generation:{label}")
        assert code == 0 and "INITIALIZED" in output and "ownership audit" not in output, output
        assert tomllib.loads((target / "hangar.toml").read_text()) == {
            "project": {"name": "fresh-project", "version": "0.1.0"}}, output
        assert (target / "src/main.fk").read_text() == (
            '-- fresh-project -- a FREAK project\n\nsay "Hello from fresh-project!"\n')
        assert (target / "hangar_modules").is_dir() and not (target / "hangar.lock").exists()
        assert report.read_bytes() == b"" and not tuple(target.glob(".freak/transaction.*")), output
        assert (target / ".freak/graph.lock").is_file() == (label == "existing-empty")
        before = snapshot(target)
        code, output = recorder.run([str(binary), *prefix, "init", "fresh-project"], parent, env,
                                    f"{name}:init-generation:{label}:duplicate")
        assert code == 1 and "hangar.toml already exists in fresh-project" in output, output
        assert snapshot(target) == before and report.read_bytes() == b"", output

    # Equivalent terminal directory spellings must select the same host leaf.
    spellings = ["fresh-project/", "fresh-project///", "fresh-project/.",
                 "fresh-project/./"]
    if os.name == "nt":
        spellings += ["fresh-project\\", "fresh-project\\."]
    else:
        spellings += ["literal\\project", "literal\\project/"]
    for index, spelling in enumerate(spellings):
        parent = root / f"{name}-init-target-spelling-{index}"
        parent.mkdir()
        private.claim_fresh_directories(parent)
        leaf = "literal\\project" if spelling.startswith("literal") else "fresh-project"
        target = parent / leaf
        # Preserve the neighbor the old cosmetic basename would have selected.
        neighbor = parent / "project"
        neighbor.mkdir()
        (neighbor / "retained").write_bytes(b"unrelated neighbor\x00\xff\n")
        before_neighbor = snapshot(neighbor)
        code, output = recorder.run([str(binary), *prefix, "init", spelling], parent, env,
                                    f"{name}:init-authority:host-target-spelling:{index}")
        assert code == 0 and "INITIALIZED" in output and "ownership audit" not in output, output
        assert (target / "hangar.toml").is_file() and (target / "src/main.fk").is_file(), output
        assert (target / "hangar_modules").is_dir() and not (target / "hangar.lock").exists()
        assert snapshot(neighbor) == before_neighbor and report.read_bytes() == b"", output
        assert set(entry.name for entry in parent.iterdir()) == {leaf, "project"}, output

    parent = root / f"{name}-init-generation-target-file"
    parent.mkdir()
    private.claim_fresh_directories(parent)
    (parent / "target").write_bytes(b"retained non-directory target\n")
    decline(parent, "target-file", command=["init", "target"])

    if os.name != "nt":
        # Real POSIX symlinks and permission-denial probes, not Windows shims.
        for entry in ("lock", "manifest", "private", "graph"):
            cwd = root / f"{name}-init-generation-symlink-{entry}"
            project(cwd, None, private)
            (cwd / "hangar.toml").unlink()
            retained = cwd / "retained-target"
            retained.write_bytes(b"retained link target\n")
            destination = {"lock": cwd / "hangar.lock", "manifest": cwd / "hangar.toml",
                           "private": cwd / ".freak", "graph": cwd / ".freak/graph.lock"}[entry]
            if entry == "graph":
                destination.parent.mkdir(mode=0o700)
                private.claim_fresh_directories(destination.parent)
            destination.symlink_to(retained)
            decline(cwd, "symlink-" + entry)
        parent = root / f"{name}-init-generation-target-symlink"
        parent.mkdir()
        target = parent / "retained-target"
        target.mkdir()
        private.claim_fresh_directories(parent, target)
        (target / "retained").write_bytes(b"retained directory target\n")
        (parent / "link").symlink_to(target, target_is_directory=True)
        decline(parent, "target-symlink", command=["init", "link"])
        for entry in ("hangar.lock", "hangar.toml"):
            cwd = root / f"{name}-init-generation-unreadable-{entry}"
            project(cwd, None, private)
            (cwd / "hangar.toml").unlink()
            denied = cwd / entry
            denied.write_bytes(LEGACY.encode())
            handle = os.open(denied, os.O_RDONLY)
            try:
                denied.chmod(0)
                decline(cwd, "unreadable-" + entry, demote=os.geteuid() == 0,
                        readable_handles={denied: handle})
            finally:
                os.close(handle)
                denied.chmod(0o644)
    print(f"native:{name}:init:orphan-generation-and-ordinary-targets:preserved", flush=True)


def init_effect_authority_controls(root: Path, invocation: tuple[str, Path, list[str]],
                                   recorder: Recorder, env: dict, report: Path,
                                   private: WindowsPrivateFixture) -> None:
    """Body refusal releases its own fresh lock; retained files stay exact."""
    name, binary, prefix = invocation
    parent = root / f"{name}-init-owned-rollback"
    parent.mkdir()
    target = parent / "fresh-project"
    target.mkdir()
    state = target / ".freak"
    state.mkdir(mode=0o700)
    private.claim_fresh_directories(parent, target, state)
    (target / "src").write_bytes(b"foreign non-directory source entry\n")
    before = snapshot(target)
    code, output = recorder.run([str(binary), *prefix, "init", "fresh-project"], parent, env,
                                f"{name}:init-authority:failed-body-rollback")
    assert code == 1 and output.startswith(WRITER_PREFIX), output
    assert "INITIALIZED" not in output and "ownership audit" not in output, output
    assert snapshot(target) == before and report.read_bytes() == b"", output
    assert not (state / "graph.lock").exists() and not tuple(state.glob("lock-abort*"))
    (target / "src").unlink()
    code, output = recorder.run([str(binary), *prefix, "init", "fresh-project"], parent, env,
                                f"{name}:init-authority:retry-after-failure")
    assert code == 0 and "INITIALIZED" in output and "ownership audit" not in output, output
    assert tomllib.loads((target / "hangar.toml").read_text()) == {
        "project": {"name": "fresh-project", "version": "0.1.0"}}, output
    assert (target / "src/main.fk").read_bytes() == (
        b'-- fresh-project -- a FREAK project\n\nsay "Hello from fresh-project!"\n')
    assert report.read_bytes() == b"" and (state / "graph.lock").read_bytes() == b""

    target = root / f"{name}-init-retained-nongraph-files"
    target.mkdir()
    source = target / "src"
    source.mkdir()
    modules = target / "hangar_modules"
    modules.mkdir()
    private.claim_fresh_directories(target, source, modules)
    retained = b"retained source bytes\x00\xff\n"
    (source / "main.fk").write_bytes(retained)
    (modules / "retained").write_bytes(b"retained module\n")
    old_source = snapshot(source)
    old_modules = snapshot(modules)
    code, output = recorder.run([str(binary), *prefix, "init"], target, env,
                                f"{name}:init-authority:retained-nongraph-files")
    assert code == 0 and "INITIALIZED" in output and "ownership audit" not in output, output
    assert snapshot(source) == old_source and snapshot(modules) == old_modules
    assert report.read_bytes() == b"" and (target / "hangar.toml").is_file()

    if os.name == "nt":
        # A real permissive Windows DACL, never a POSIX permission shim.
        import ctypes
        import ctypes.wintypes as wintypes
        target = root / f"{name}-init-public-private-acl"
        target.mkdir()
        state = target / ".freak"
        state.mkdir()
        private.claim_fresh_directories(target, state)
        security = ctypes.WinDLL("advapi32", use_last_error=True)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        convert = security.ConvertStringSecurityDescriptorToSecurityDescriptorW
        convert.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.DWORD)]
        convert.restype = wintypes.BOOL
        apply = security.SetFileSecurityW
        apply.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_void_p]
        apply.restype = wintypes.BOOL
        kernel.LocalFree.argtypes = [ctypes.c_void_p]
        kernel.LocalFree.restype = ctypes.c_void_p
        descriptor = ctypes.c_void_p()
        assert convert("D:P(A;;FA;;;WD)", 1, ctypes.byref(descriptor), None), ctypes.get_last_error()
        try:
            assert apply(str(state), 0x80000004, descriptor), ctypes.get_last_error()
        finally:
            kernel.LocalFree(descriptor)
        before = snapshot(target)
        code, output = recorder.run([str(binary), *prefix, "init"], target, env,
                                    f"{name}:init-authority:permissive-Windows-parent-ACL")
        assert code == 1 and "private owned directory" in output, output
        assert "INITIALIZED" not in output and "ownership audit" not in output, output
        assert snapshot(target) == before and report.read_bytes() == b"", output
        assert not (state / "graph.lock").exists()
        # The ordinary lock path must check the held parent before both create
        # and reopen. Every legacy writer uses that same admission boundary.
        for retained_lock in (False, True):
            target = root / f"{name}-legacy-public-private-acl-{int(retained_lock)}"
            target.mkdir()
            state = target / ".freak"
            state.mkdir()
            private.claim_fresh_directories(target, state)
            (target / "hangar.toml").write_text(
                '[project]\nname = "private-parent"\nversion = "0.1.0"\n', encoding="utf-8")
            if retained_lock:
                (state / "graph.lock").write_bytes(b"retained ordinary lock\n")
            descriptor = ctypes.c_void_p()
            assert convert("D:P(A;;FA;;;WD)", 1, ctypes.byref(descriptor), None), ctypes.get_last_error()
            try:
                assert apply(str(state), 0x80000004, descriptor), ctypes.get_last_error()
            finally:
                kernel.LocalFree(descriptor)
            before = snapshot(target)
            for index, command in enumerate((*WRITERS, *(("version", bump) for bump in VERSION_BUMPS))):
                code, output = recorder.run([str(binary), *prefix, *command], target, env,
                                            f"{name}:legacy-authority:permissive-Windows-parent-ACL:{int(retained_lock)}:{index}")
                # Without hangar.lock these route to the graph-aware writers,
                # which refuse at the same private-directory boundary (or
                # earlier, for a dependency the manifest does not declare).
                assert code == 1 and ("requires a private owned directory" in output
                                      or "is not a dependency of this project" in output), output
                assert snapshot(target) == before and report.read_bytes() == b"", output
                assert (state / "graph.lock").exists() == retained_lock
    print(f"native:{name}:init:owned-rollback-and-retained-files:preserved", flush=True)


def execute(args, root: Path, recorder: Recorder, receipt: dict,
            private: WindowsPrivateFixture) -> None:
    freak = args.freak.resolve(strict=True)
    hangar = args.hangar.resolve(strict=True)
    clang = args.clang.resolve(strict=True)
    if args.freak_home:
        home = args.freak_home.resolve(strict=True)
    else:
        home = root / "payload"
        for source, relative in manifest_entries(REPO):
            destination = home / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        # Every directory in this walk was just created from immutable inputs.
        # Runtime-created graph/output directories are never normalized here.
        private.claim_fresh_directories(home, *(path for path in home.rglob("*") if path.is_dir()))
    receipt["payload_inputs"] = {path.relative_to(home).as_posix(): sha(path)
                                 for path in home.rglob("*") if path.is_file()}
    env = os.environ.copy()
    env.update(NO_COLOR="1", FREAK_HOME=str(home), FREAK_CLANG=str(clang))
    git = fixtures(root, clang, recorder, env, private)
    report = root / "git-attempts.raw"
    report.write_bytes(b"")
    report.chmod(0o666)
    env["FREAK_GIT"] = str(git)
    env["FREAK_HANGAR_GIT_REPORT"] = str(report)
    env["PATH"] = str(git.parent) + os.pathsep + env.get("PATH", "")
    code, output = recorder.run([str(git), "controlled-attempt"], root, env,
                                "native-git-witness-positive-control")
    assert code == 23 and output == "injected Git attempt\n", output
    assert report.read_bytes() == b"attempted Git\n", "Git witness did not record actual execution"
    report.write_bytes(b"")
    invocations = [("freak", freak, ["hangar"]), ("standalone", hangar, [])]
    diamond = root / "diamond"
    source_project = REPO / "examples/v35/package-consumer"
    copied_directories = tuple(path.relative_to(source_project)
                               for path in source_project.rglob("*") if path.is_dir())
    shutil.copytree(source_project, diamond)
    private.claim_fresh_directories(diamond, *(diamond / path for path in copied_directories))
    manifest = diamond / "hangar.toml"
    manifest.write_text(manifest.read_text().replace('left = { path = "left" }',
                                                  'left = { path = "left", version = "0.1.0" }'))
    output_path = diamond / "previous-build"
    code, output = recorder.run([str(freak), "build", "--c", "--strict-borrow",
                                 "--output=" + str(output_path)], diamond, env,
                                "produce-real-version-qualified-v2", timeout=180)
    assert code == 0 and output_path.is_file(), output
    graph = tomllib.loads((diamond / "hangar.lock").read_text())
    assert graph["lock"]["schema"] == 2 and graph["lock"]["node_count"] == 4
    assert graph["lock"]["edge_count"] == 4, graph["lock"]
    (diamond / "previous-build.freak-run-cache").write_bytes(b"retained cache proof\n")
    installed = diamond / "hangar_modules" / "left"
    installed.parent.mkdir()
    installed.mkdir()
    private.claim_fresh_directories(installed.parent, installed)
    (installed / "owned-source.fk").write_text("-- retained working tree\n")
    receipt["genuine_v2"] = {"schema": 2, "nodes": 4, "edges": 4,
                             "lock_sha256": sha(diamond / "hangar.lock"),
                             "snapshot": snapshot(diamond)}
    # A genuine lock v2 project is graph-owned: every project command routes to
    # the graph-aware version. audit and outdated are read-only and must leave
    # project state untouched.
    graph_read_only = ((("audit",), "HANGAR AUDIT"), (("audit", "--fix"), "HANGAR AUDIT"),
                       (("outdated",), "HANGAR OUTDATED"))
    for name, binary, prefix in invocations:
        lock_before = (diamond / "hangar.lock").read_bytes()
        manifest_before = manifest.read_bytes()
        code, output = recorder.run([str(binary), *prefix, "install"], diamond, env,
                                    f"{name}:genuine-v2:graph-install")
        assert code == 0, output
        assert (diamond / "hangar.lock").read_bytes() == lock_before, output
        assert manifest.read_bytes() == manifest_before and report.read_bytes() == b"", output
        before = snapshot(diamond)
        for index, (args, banner) in enumerate(graph_read_only):
            code, output = recorder.run([str(binary), *prefix, *args], diamond, env,
                                        f"{name}:genuine-v2:{index}")
            assert code == 0, (args, code, output)
            assert banner in output and "legacy" not in output, (args, output)
            assert snapshot(diamond) == before and report.read_bytes() == b"", (args, output)
        print(f"native:{name}:genuine-v2:graph-routed:{len(graph_read_only)}", flush=True)

    cases = {
        "unknown-schema": (b"lock.schema = 99\n", "unsupported lock schema; expected legacy [[package]] records"),
        "empty": (b"", "empty lock document"),
        "partial": (b'[[package]]\nname = "left"\n', "partial legacy package entry: name, version and source are required"),
        "partial-tail": ((LEGACY + '\n[[package]]\nname = "tail"\n').encode(), "partial legacy package entry: name, version and source are required"),
        "binary": (b"# legacy\n\x00\xff", "legacy lock must be UTF-8 text without NUL"),
        "binary-comment": (b"# legacy\x01\n", "legacy lock must be UTF-8 text without NUL"),
        "duplicate-name": ((LEGACY + LEGACY).encode(), "duplicate legacy package name"),
        "duplicate-key": ((LEGACY + 'name = "other"\n').encode(), "duplicate legacy package field"),
        "unknown-field": ((LEGACY + 'future = "discarded"\n').encode(), "unknown legacy package field"),
        "truncated-quote": (b'[[package]]\nname = "left\n', "malformed quoted legacy value"),
        "trailing-data": ((LEGACY + 'sha256 = "" rubbish\n').encode(), "malformed quoted legacy value"),
        "unquoted": (LEGACY.replace('"0.1.0"', "true").encode(), "legacy package fields must be quoted strings"),
        "bad-checksum": ((LEGACY + 'sha256 = "bad"\n').encode(), "invalid legacy SHA-256"),
        "long-line": (b"#" + b"x" * 8192 + b"\n", "legacy lock line exceeds byte limit"),
        "oversize": (b"#" + b"x" * 1048576, "cannot read legacy lock:"),
    }
    receipt["rejected_formats"] = list(cases)
    # These are additional controls, leaving every prior format control intact.
    right = '[[package]]\nname = "right"\nversion = "0.1.0"\nsource = "owner/right"\n'
    git_fields = {
        "invalid-revision": (LEGACY.replace('"0.1.0"', '"--unsafe"').encode(), "invalid legacy Git revision"),
        "invalid-source": (LEGACY.replace('"owner/left"', '"owner/left#literal"').encode(), "invalid legacy Git source"),
        "second-invalid-revision": ((LEGACY + right.replace('"0.1.0"', '"--unsafe"')).encode(), "invalid legacy Git revision"),
        "second-invalid-source": ((LEGACY + right.replace('"owner/right"', '"owner/right#literal"')).encode(), "invalid legacy Git source"),
    }
    receipt["rejected_git_fields"] = list(git_fields)
    integrity_tools = integrity_failure_tools(root, clang, recorder, env, private)
    for invocation in invocations:
        for label, (contents, expected) in (*cases.items(), *git_fields.items()):
            cwd = root / f"{invocation[0]}-{label}"
            project(cwd, contents, private)
            if label.startswith("second-invalid-"):
                # No first package is present. If admission is late, installation
                # reaches the Git witness before the malformed second record.
                shutil.rmtree(cwd / "hangar_modules/left")
                manifest = cwd / "hangar.toml"
                manifest.write_text(manifest.read_text() +
                    'right = { git = "owner/right", version = "0.1.0" }\n')
            rejected(cwd, invocation, recorder, env, report, expected, label)
        cwd = root / f"{invocation[0]}-non-file"
        project(cwd, None, private)
        (cwd / "hangar.lock").mkdir()
        (cwd / "hangar.lock" / "retained").write_bytes(b"not a lock file")
        rejected(cwd, invocation, recorder, env, report, "cannot read legacy lock:", "non-file")
        if os.name != "nt":
            cwd = root / f"{invocation[0]}-unreadable"
            project(cwd, LEGACY.encode(), private)
            lock = cwd / "hangar.lock"
            handle = os.open(lock, os.O_RDONLY)
            try:
                lock.chmod(0)
                rejected(cwd, invocation, recorder, env, report, "cannot read legacy lock:",
                         "unreadable", demote=os.geteuid() == 0, readable_handles={lock: handle})
            finally:
                os.close(handle)
                lock.chmod(0o644)
        for label, contents in (("empty-generation", b"# Generated empty legacy generation\n\n"),
                                ("optional-checksum", LEGACY.encode()),
                                ("empty-checksum", (LEGACY + 'sha256 = ""\n').encode()),
                                ("quoted-source", (LEGACY.replace('"owner/left"', "'https://example.invalid/owner/left#literal'") +
                                 '[[package]]\nname = "keeper"\nversion = "0.1.0"\nsource = "https://example.invalid/owner/\\\"quoted\\\"#literal"\n').encode())):
            cwd = root / f"{invocation[0]}-{label}"
            project(cwd, contents, private)
            if label == "quoted-source":
                keeper = cwd / "hangar_modules" / "keeper"
                keeper.mkdir()
                private.claim_fresh_directories(keeper)
                (keeper / "keeper.fk").write_text("-- retained second legacy package\n")
            before = snapshot(cwd)
            code, output = recorder.run([str(invocation[1]), *invocation[2], "audit"], cwd, env,
                                        f"{invocation[0]}:{label}:audit")
            assert code == 0 and PREFIX not in output, output
            assert snapshot(cwd) == before and report.read_bytes() == b"", output
            code, output = recorder.run([str(invocation[1]), *invocation[2], "remove", "left"], cwd, env,
                                        f"{invocation[0]}:{label}:remove")
            assert code == 0 and PREFIX not in output, output
            assert "left" not in tomllib.loads((cwd / "hangar.toml").read_text()).get("dependencies", {})
            assert not (cwd / "hangar_modules" / "left").exists()
            packages = tomllib.loads((cwd / "hangar.lock").read_text()).get("package", [])
            assert packages == ([{"name": "keeper", "version": "0.1.0", "source": 'https://example.invalid/owner/"quoted"#literal', "sha256": ""}]
                                if label == "quoted-source" else []), packages
            if label == "quoted-source":
                assert (cwd / "hangar_modules/keeper/keeper.fk").read_text() == "-- retained second legacy package\n"
            assert report.read_bytes() == b"", output
            print(f"native:{invocation[0]}:{label}:legacy-success", flush=True)

        # Let the native compatibility hasher establish the platform-specific
        # archive checksum. Case normalization must not trigger a reinstall.
        cwd = root / f"{invocation[0]}-checksum-case"
        project(cwd, (LEGACY + 'sha256 = ""\n').encode(), private)
        code, output = recorder.run([str(invocation[1]), *invocation[2], "audit", "--fix"],
                                    cwd, env, f"{invocation[0]}:checksum:seed")
        assert code == 0 and "Computed SHA-256:" in output, output
        canonical = (cwd / "hangar.lock").read_bytes()
        digest = tomllib.loads(canonical.decode())["package"][0]["sha256"]
        assert re.fullmatch("[0-9a-f]{64}", digest), digest
        assert any(character in "abcdef" for character in digest), digest
        variants = (("lower", digest), ("upper", digest.upper()),
                    ("mixed", "".join(character.upper() if index % 2 else character
                                       for index, character in enumerate(digest))))
        for label, checksum in variants:
            (cwd / "hangar.lock").write_bytes(canonical.replace(digest.encode(), checksum.encode()))
            before = snapshot(cwd)
            code, output = recorder.run([str(invocation[1]), *invocation[2], "audit"],
                                        cwd, env, f"{invocation[0]}:checksum:{label}:audit")
            assert code == 0 and "ALL CLEAR" in output and "1 packages verified" in output, output
            assert "INTEGRITY FAILURE" not in output and "Reinstalling" not in output, output
            assert snapshot(cwd) == before and report.read_bytes() == b"", output
            code, output = recorder.run([str(invocation[1]), *invocation[2], "audit", "--fix"],
                                        cwd, env, f"{invocation[0]}:checksum:{label}:audit-fix")
            assert code == 0 and "ALL CLEAR" in output and "1 packages verified" in output, output
            assert "INTEGRITY FAILURE" not in output and "Reinstalling" not in output, output
            after = snapshot(cwd)
            assert {key: value for key, value in after.items() if key != "hangar.lock"} == {
                key: value for key, value in before.items() if key != "hangar.lock"}, output
            assert (cwd / "hangar.lock").read_bytes() == canonical and report.read_bytes() == b"", output
        print(f"native:{invocation[0]}:checksum-case:legacy-success", flush=True)

        writer_controls(root, invocation, recorder, env, report, private)
        writer_manifest_controls(root, invocation, recorder, env, report, private)
        writer_version_controls(root, invocation, recorder, env, report, private, diamond)
        audit_failed_repair_controls(root, invocation, recorder, env, report, private)
        audit_hash_failure_controls(root, invocation, recorder, env, report, private, integrity_tools)
        audit_stable_hash_controls(root, invocation, recorder, env, report, private)
        init_generation_controls(root, invocation, recorder, env, report, private, diamond)
        init_effect_authority_controls(root, invocation, recorder, env, report, private)

        # Explicit toolchain bootstrap does not use the project's lock. A
        # controlled local installer exits 23 and records actual execution.
        marker = root / f"{invocation[0]}-toolchain-marker"
        script = root / (f"{invocation[0]}-installer.ps1" if os.name == "nt" else f"{invocation[0]}-installer.sh")
        script.write_text("Set-Content -LiteralPath $env:FREAK_HANGAR_TOOLCHAIN_REPORT -Value bypassed\nexit 23\n"
                          if os.name == "nt" else 'printf bypassed > "$FREAK_HANGAR_TOOLCHAIN_REPORT"\nexit 23\n')
        bypass_env = env.copy()
        bypass_env.update(FREAK_UPGRADE_SCRIPT=str(script), FREAK_HANGAR_TOOLCHAIN_REPORT=str(marker),
                          FREAK_HOME=str(root / f"{invocation[0]}-toolchain-home"))
        before = snapshot(diamond)
        code, output = recorder.run([str(invocation[1]), *invocation[2], "install", "freak"], diamond,
                                    bypass_env, f"{invocation[0]}:toolchain-bypass")
        assert code == 23 and marker.read_text().strip() == "bypassed" and PREFIX not in output, output
        assert snapshot(diamond) == before and report.read_bytes() == b"", output
        print(f"native:{invocation[0]}:toolchain-bypass:executed", flush=True)
    receipt["git_attempts"] = report.read_bytes().decode()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freak", type=Path, required=True)
    parser.add_argument("--hangar", type=Path, required=True)
    parser.add_argument("--clang", type=Path, required=True)
    parser.add_argument("--freak-home", type=Path,
                        help="existing test payload; otherwise stage the current distribution manifest")
    parser.add_argument("--probe-root", type=Path)
    args = parser.parse_args()
    if args.probe_root:
        root = args.probe_root.resolve()
        protected_inputs = [REPO, args.freak.resolve(), args.hangar.resolve(), args.clang.resolve()]
        if args.freak_home:
            protected_inputs.append(args.freak_home.resolve())
        for protected in protected_inputs:
            assert root != protected and root not in protected.parents and protected not in root.parents, (root, protected)
        root.mkdir(parents=True, exist_ok=False)
    else:
        # Retain raw commands and failed receipts from local default runs too.
        root = Path(tempfile.mkdtemp(prefix="freak-hangar-preservation-"))
    private = WindowsPrivateFixture(root)
    # POSIX permission-denial controls may execute as an unprivileged child.
    root.chmod(0o755)
    recorder = Recorder(root)
    names = subprocess.check_output(["git", "ls-files"], cwd=REPO, text=True).splitlines()
    before = {name: sha(REPO / name) for name in names}
    receipt = {"status": "RUNNING", "runner_pid": os.getpid(), "source_head":
               subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
               "inputs_before": before, "driver_sha256": sha(Path(__file__)),
               "images": {str(path.resolve()): sha(path.resolve()) for path in (args.freak, args.hangar, args.clang)},
               "commands": recorder.records, "qualification": "native component gate; no full release or graph-aware Hangar claim"}
    try:
        execute(args, root, recorder, receipt, private)
        after = {name: sha(REPO / name) for name in names}
        assert before == after, "source changed during native acceptance"
        receipt.update(status="PASS", inputs_after=after, inputs_unchanged=True,
                       windows_fixture=private.report)
        print("Native Hangar lock preservation: PASS", flush=True)
    except BaseException as error:
        receipt.update(status="FAIL", error=repr(error))
        raise
    finally:
        receipt_path = root / "receipt.json"
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
        print(f"Hangar preservation evidence: {receipt_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
