#!/usr/bin/env python3
"""Native public legacy Hangar lock admission and exact preservation controls.

A public build produces a genuine lock v2. Legacy commands must decline it
before effects; this gate does not claim graph-aware install/update support.
"""
from __future__ import annotations

import argparse
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
        return result.returncode, ANSI.sub("", (result.stdout + result.stderr).decode("utf-8", "replace"))


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
    for invocation in invocations:
        rejected(diamond, invocation, recorder, env, report,
                 "unsupported lock schema; expected legacy [[package]] records", "genuine-v2")

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
    for invocation in invocations:
        for label, (contents, expected) in cases.items():
            cwd = root / f"{invocation[0]}-{label}"
            project(cwd, contents, private)
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
                                ("quoted-source", (LEGACY.replace('"owner/left"', "'owner/left#literal'") +
                                 '[[package]]\nname = "keeper"\nversion = "0.1.0"\nsource = "owner/\\\"quoted\\\""\n').encode())):
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
            assert packages == ([{"name": "keeper", "version": "0.1.0", "source": 'owner/"quoted"', "sha256": ""}]
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
