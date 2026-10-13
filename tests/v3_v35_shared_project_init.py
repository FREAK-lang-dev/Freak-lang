#!/usr/bin/env python3
"""Prepared native shared-initializer and installed public-command controls.

The pure mode checks the independent byte/entry oracle and the gate itself. It
does not execute or qualify FREAK code. Native mode requires a fresh compiler
containing the create-only filesystem primitive; public mode additionally uses
the exact supplied installed CLI, without rebuilding or substituting it.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import unittest

from v3_v35_templates import TemplateProgress, SELECTORS, expected, run

ROOT = Path(__file__).resolve().parents[1]
KINDS = ("cli", "lib", "http")
MAIN = r'''
task main() {
    pilot mode = process::arg(1)
    pilot kind = process::arg(2)
    pilot target = process::arg(3)
    pilot okay = false
    if mode == "new" { okay = cli_create_template(kind, target) }
    else if mode == "existing" { okay = cli_initialize_project(kind, target, true) }
    else if mode == "held" or mode == "retarget" {
        pilot held = fs::open_dir_ticket(target + "")
        if fs::result_ok(held) {
            pilot name = cli_template_name_from_project(held)
            pilot proceed = true
            if mode == "retarget" {
                pilot moved = fs::rename_checked(target + "", process::arg(4))
                proceed = fs::result_ok(moved)
                pilot renamed = fs::result_completed(moved)
                pilot rename_error = fs::result_error(moved)
                fs::result_release(moved)
                if proceed {
                    say "RETARGET_MOVED"
                    pilot replacement = fs::mkdir_checked(target + "")
                    proceed = fs::result_ok(replacement)
                    fs::result_release(replacement)
                    if proceed {
                        pilot foreign = fs::write_checked(target + "/foreign", "replacement directory is foreign")
                        proceed = fs::result_ok(foreign)
                        fs::result_release(foreign)
                    }
                } else if renamed { say "RETARGET_COMPLETED_ERROR " + rename_error }
                else { say "RETARGET_REFUSED " + rename_error }
            }
            if proceed { okay = cli_initialize_project_at(kind, held, name) }
            -- The borrowed root must still be usable after every API outcome.
            pilot identity = fs::directory_identity_ticket(held)
            if fs::result_ok(identity) { say "BORROWED_ROOT " + fs::result_word(identity) }
            fs::result_release(identity)
        } else { cli_template_fail("cannot open control root: " + fs::result_error(held)) }
        fs::result_release(held)
    }
    if okay { say "OK" } else { say "ERROR " + cli_template_error }
    say "CAPTURED_PATH " + cli_template_project_path
    say "CAPTURED_IDENTITY " + cli_template_project_identity
    if cli_template_retained_files { say "RETAINED true" } else { say "RETAINED false" }
}
'''

# This Linux interposer is a deliberately failing control, not runtime code.
# Root compiles it only inside the serialized native gate. It is activated for
# one exact held test-root spelling and never installed in a product payload.
FAULT_SHIM = r'''
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
static int triggered;
static int replace_directory(int parent,const char *name,const char *moved,const char *foreign) {
    int (*actual_open)(int,const char *,int,...)=dlsym(RTLD_NEXT,"openat");
    ssize_t (*actual_write)(int,const void *,size_t)=dlsym(RTLD_NEXT,"write");
    if (!actual_open || !actual_write || renameat(parent,name,parent,moved) || mkdirat(parent,name,0700)) return 0;
    int file=actual_open(parent,foreign,O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW,0600);
    if (file < 0) return 0;
    static const char bytes[]="foreign replacement directory authority";
    ssize_t written=actual_write(file,bytes,sizeof(bytes)-1);
    int synced=fsync(file),closed=close(file);
    return written == (ssize_t)sizeof(bytes)-1 && !synced && !closed;
}
static int selected(int fd,const char *leaf) {
    const char *root=getenv("FREAK_INIT_CONTROL_ROOT");
    if (!root || !*root) return 0;
    char descriptor[64],path[4097],wanted[4097];
    snprintf(descriptor,sizeof(descriptor),"/proc/self/fd/%d",fd);
    ssize_t count=readlink(descriptor,path,sizeof(path)-1);
    if (count <= 0 || count >= (ssize_t)sizeof(path)-1) return 0;
    path[count]=0;
    int size=leaf ? snprintf(wanted,sizeof(wanted),"%s/%s",root,leaf) :
                    snprintf(wanted,sizeof(wanted),"%s",root);
    return size > 0 && size < (int)sizeof(wanted) && !strcmp(path,wanted);
}
ssize_t write(int fd,const void *data,size_t size) {
    ssize_t (*actual)(int,const void *,size_t)=dlsym(RTLD_NEXT,"write");
    const char *mode=getenv("FREAK_INIT_CONTROL_MODE");
    if (!actual) { errno=ENOSYS; return -1; }
    if (mode && !strcmp(mode,"partial") && selected(fd,"README.md")) {
        if (triggered++) { errno=ENOSPC; return -1; }
        return actual(fd,data,size < 5 ? size : 5);
    }
    if (!triggered && mode && !strcmp(mode,"directory-retarget-before") && selected(fd,"README.md")) {
        triggered=1;
        int (*actual_open)(int,const char *,int,...)=dlsym(RTLD_NEXT,"openat");
        int parent=actual_open ? actual_open(AT_FDCWD,getenv("FREAK_INIT_CONTROL_ROOT"),O_RDONLY | O_DIRECTORY | O_NOFOLLOW) : -1;
        int replaced=parent >= 0 && replace_directory(parent,"src","src-held","src/foreign");
        if (parent >= 0) close(parent);
        if (!replaced) { errno=EIO; return -1; }
    }
    return actual(fd,data,size);
}
int openat(int parent,const char *path,int flags,...) {
    mode_t permissions=0;
    if (flags & O_CREAT) { va_list args; va_start(args,flags); permissions=(mode_t)va_arg(args,int); va_end(args); }
    int (*actual_open)(int,const char *,int,...)=dlsym(RTLD_NEXT,"openat");
    ssize_t (*actual_write)(int,const void *,size_t)=dlsym(RTLD_NEXT,"write");
    const char *mode=getenv("FREAK_INIT_CONTROL_MODE");
    if (!actual_open || !actual_write) { errno=ENOSYS; return -1; }
    if (!triggered && mode && !strcmp(mode,"late-manifest") &&
        (flags & (O_CREAT | O_EXCL)) == (O_CREAT | O_EXCL) &&
        !strcmp(path,"hangar.toml") && selected(parent,NULL)) {
        triggered=1;
        int foreign=actual_open(parent,path,O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW,0600);
        if (foreign < 0) return -1;
        static const unsigned char bytes[]="foreign manifest appeared after admission\0\xff";
        ssize_t written=actual_write(foreign,bytes,sizeof(bytes)-1);
        int synced=fsync(foreign),closed=close(foreign);
        if (written != (ssize_t)sizeof(bytes)-1 || synced || closed) { errno=EIO; return -1; }
    }
    if (!triggered && mode && (!strcmp(mode,"directory-retarget-after") || !strcmp(mode,"private-retarget")) &&
        (flags & (O_CREAT | O_EXCL)) == (O_CREAT | O_EXCL) &&
        !strcmp(path,"hangar.toml") && selected(parent,NULL)) {
        triggered=1;
        int replaced=!strcmp(mode,"private-retarget") ?
            replace_directory(parent,".freak",".freak-held",".freak/graph.lock") :
            replace_directory(parent,"src","src-held","src/foreign");
        if (!replaced) { errno=EIO; return -1; }
    }
    return actual_open(parent,path,flags,permissions);
}
'''
FOREIGN_MANIFEST = b"foreign manifest appeared after admission\x00\xff"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def entries(root: Path) -> dict[str, tuple]:
    """Record entries without following any directory or file link.

    Bytes, mode and identity make a replaced-but-equal file fail preservation.
    Windows ACL qualification remains a separate actual-Windows runtime gate.
    """
    result = {}

    def walk(directory: Path) -> None:
        for child in sorted(directory.iterdir()):
            metadata = child.lstat()
            relative = child.relative_to(root).as_posix()
            common = (stat.S_IMODE(metadata.st_mode), metadata.st_dev, metadata.st_ino)
            if stat.S_ISLNK(metadata.st_mode):
                result[relative] = ("link", os.readlink(child), *common)
            elif stat.S_ISDIR(metadata.st_mode):
                result[relative] = ("directory", *common)
                walk(child)
            elif stat.S_ISREG(metadata.st_mode):
                try:
                    result[relative] = ("file", child.read_bytes(), *common)
                except PermissionError:
                    result[relative] = ("unreadable-file", *common)
            else:
                result[relative] = ("other", metadata.st_mode, *common)

    walk(root)
    return result


def regular_files(root: Path) -> dict[str, bytes]:
    return {name: entry[1] for name, entry in entries(root).items()
            if entry[0] == "file" and not name.startswith(".freak/")}


def assert_preserved(before: dict[str, tuple], root: Path) -> None:
    after = entries(root)
    for relative, original in before.items():
        assert after.get(relative) == original, (relative, original, after.get(relative))


def assert_canonical(root: Path, canonical: Path, kind: str, name: str,
                     retained: dict[str, bytes] | None = None) -> None:
    required = expected(canonical, kind, name)
    required.update(retained or {})
    assert regular_files(root) == required, (kind, name, regular_files(root), required)


def creator(binary: Path, mode: str, kind: str, destination: Path, env: dict,
            progress: TemplateProgress, *, success: bool | None, extra: tuple = ()):
    result = run([binary, mode, kind, destination, *extra], cwd=destination.parent,
                 env=env, progress=progress, label="shared-init-" + mode + "-" + destination.name)
    assert result.returncode == 0 and not result.stderr, (result.returncode, result.stdout, result.stderr)
    lines = result.stdout.splitlines()
    if success is not None:
        assert ("OK" in lines) == success, (success, result.stdout)
    if success is False:
        assert any(line.startswith("ERROR ") for line in lines), result.stdout
    return result


def retarget_outcome(stdout: str, target: Path, moved: Path, canonical: Path,
                     before: dict[str, tuple], *, windows: bool) -> str:
    lines = stdout.splitlines()
    assert not any(line.startswith("RETARGET_COMPLETED_ERROR ") for line in lines), stdout
    refused = any(line.startswith("RETARGET_REFUSED ") for line in lines)
    if refused:
        assert windows and "RETARGET_MOVED" not in lines and "OK" not in lines, stdout
        assert not moved.exists() and entries(target) == before
        assert any(line.startswith("BORROWED_ROOT ") and len(line) > len("BORROWED_ROOT ") for line in lines)
        return "windows-held-root-retarget-refusal"
    assert "RETARGET_MOVED" in lines and "OK" in lines, stdout
    assert regular_files(target) == {"foreign": b"replacement directory is foreign"}
    assert_canonical(moved, canonical, "cli", "held-original")
    captured = [line[len("CAPTURED_PATH "):] for line in lines if line.startswith("CAPTURED_PATH ")]
    assert len(captured) == 1 and Path(captured[0]).resolve(strict=True) == moved.resolve(strict=True), stdout
    assert Path(captured[0]).resolve(strict=True) != target.resolve(strict=True)
    identities = [line[len("CAPTURED_IDENTITY "):] for line in lines if line.startswith("CAPTURED_IDENTITY ")]
    borrowed = [line[len("BORROWED_ROOT "):] for line in lines if line.startswith("BORROWED_ROOT ")]
    assert len(identities) == len(borrowed) == 1 and identities[0] and identities == borrowed, stdout
    return "captured-held-root-after-retarget"


def native_corpus(binary: Path, canonical: Path, root: Path, env: dict,
                  progress: TemplateProgress, fault_shim: Path | None) -> dict:
    cases = []
    for kind in KINDS:
        target = root / (kind + "-new")
        creator(binary, "new", kind, target, env, progress, success=True)
        assert_canonical(target, canonical, kind, target.name)
        before = entries(target)
        creator(binary, "new", kind, target, env, progress, success=False)
        assert entries(target) == before
        cases.append("new-and-new-only-refusal-" + kind)

        target = root / (kind + "-inplace")
        target.mkdir()
        creator(binary, "existing", kind, target, env, progress, success=True)
        assert_canonical(target, canonical, kind, target.name)
        assert (target / ".freak/graph.lock").is_file()
        before = entries(target)
        creator(binary, "existing", kind, target, env, progress, success=False)
        assert entries(target) == before
        cases.append("existing-canonical-and-manifest-refusal-" + kind)

        target = root / (kind + "-retained")
        (target / "src").mkdir(parents=True)
        (target / "src/main.fk").write_bytes(b"existing foreign source\x00\xff")
        (target / "README.md").write_bytes(b"user README\x00")
        (target / "LICENSE").mkdir()
        (target / "LICENSE/user-license").write_bytes(b"directory leaf must remain")
        before = entries(target)
        result = creator(binary, "held", kind, target, env, progress, success=True)
        assert_preserved(before, target)
        required = expected(canonical, kind, target.name)
        required.pop("LICENSE")
        required.update({"src/main.fk": b"existing foreign source\x00\xff", "README.md": b"user README\x00",
                         "LICENSE/user-license": b"directory leaf must remain"})
        assert regular_files(target) == required
        assert "RETAINED true\n" in result.stdout and "BORROWED_ROOT " in result.stdout
        cases.append("retained-files-directory-leaf-borrowed-root-" + kind)

    for variant, leaf, data in (
        ("manifest", "hangar.toml", b"retained manifest\x00\xff"),
        ("modern-lock", "hangar.lock", b"format = 2\n"),
        ("legacy-lock", "hangar.lock", b"[[package]]\nname = \"old\"\n"),
        ("malformed-lock", "hangar.lock", b"\x00\xff"),
    ):
        target = root / variant
        target.mkdir()
        (target / leaf).write_bytes(data)
        before = entries(target)
        result = creator(binary, "held", "cli", target, env, progress, success=False)
        assert entries(target) == before and "BORROWED_ROOT " in result.stdout
        assert ("hangar.toml already exists" if leaf == "hangar.toml" else "existing hangar.lock without hangar.toml") in result.stdout
        cases.append("before-effects-" + variant)

    for leaf in ("transaction.marker", "transaction.manifest.before", "transaction.lock.before", "graph.lock"):
        target = root / ("retained-" + leaf.replace(".", "-"))
        private = target / ".freak"
        private.mkdir(parents=True, mode=0o700)
        (private / leaf).write_bytes(b"retained generation authority\x00\xff")
        before = entries(target)
        result = creator(binary, "existing", "cli", target, env, progress, success=False)
        assert entries(target) == before
        assert ("existing graph.lock without hangar.toml" if leaf == "graph.lock" else
                "pending or unreadable graph transaction state") in result.stdout, result.stdout
        cases.append("before-effects-" + leaf)

    for leaf in ("hangar.toml", "hangar.lock", "src", ".freak"):
        target = root / ("directory-" + leaf.replace(".", "-"))
        target.mkdir()
        if leaf in ("src", ".freak"):
            (target / leaf).write_bytes(b"source directory slot is a file")
        else:
            (target / leaf).mkdir()
            (target / leaf / "keep").write_bytes(b"existing authority")
        before = entries(target)
        creator(binary, "existing", "cli", target, env, progress, success=False)
        assert entries(target) == before
        cases.append("before-effects-wrong-kind-" + leaf)

    if os.name != "nt":
        foreign = root / "foreign"
        foreign.mkdir()
        (foreign / "keep").write_bytes(b"foreign target\x00")
        for leaf in ("hangar.toml", "hangar.lock", "src", ".freak"):
            target = root / ("link-" + leaf.replace(".", "-"))
            target.mkdir()
            (target / leaf).symlink_to(foreign if leaf in ("src", ".freak") else root / "absent",
                                      target_is_directory=leaf in ("src", ".freak"))
            before = entries(target)
            foreign_before = entries(foreign)
            creator(binary, "existing", "cli", target, env, progress, success=False)
            assert entries(target) == before and entries(foreign) == foreign_before
            cases.append("before-effects-link-" + leaf)

        target = root / "retained-link-leaf"
        target.mkdir()
        (target / "README.md").symlink_to(foreign / "keep")
        before = entries(target)
        creator(binary, "existing", "cli", target, env, progress, success=True)
        assert_preserved(before, target)
        assert (foreign / "keep").read_bytes() == b"foreign target\x00"
        required = expected(canonical, "cli", target.name)
        required.pop("README.md")
        assert regular_files(target) == required
        cases.append("retained-link-leaf-no-follow")

        target = root / "retained-unreadable-leaf"
        target.mkdir()
        unreadable = target / "README.md"
        unreadable.write_bytes(b"unreadable user README\x00\xff")
        unreadable.chmod(0)
        before = entries(target)
        result = creator(binary, "existing", "cli", target, env, progress, success=True)
        assert_preserved(before, target)
        assert "RETAINED true\n" in result.stdout
        unreadable.chmod(0o600)
        assert unreadable.read_bytes() == b"unreadable user README\x00\xff"
        cases.append("retained-unreadable-leaf")

    # A held project is the only authority after a deliberate pathname change.
    # Windows held handles may deny the rename, itself a conservative boundary.
    target = root / "held-original"
    target.mkdir()
    before = entries(target)
    moved = root / "held-moved"
    result = creator(binary, "retarget", "cli", target, env, progress,
                     success=None, extra=(moved,))
    cases.append(retarget_outcome(result.stdout, target, moved, canonical, before, windows=os.name == "nt"))

    if fault_shim is not None:
        target = root / "actual-partial-write"
        target.mkdir()
        fault_env = env.copy()
        fault_env["LD_PRELOAD"] = str(fault_shim) + (":" + env["LD_PRELOAD"] if env.get("LD_PRELOAD") else "")
        fault_env["FREAK_INIT_CONTROL_ROOT"] = str(target)
        fault_env["FREAK_INIT_CONTROL_MODE"] = "partial"
        failed = creator(binary, "existing", "cli", target, fault_env, progress, success=False)
        partial = expected(canonical, "cli", target.name)["README.md"][:5]
        assert (target / "README.md").read_bytes() == partial
        assert not (target / "hangar.toml").exists(), regular_files(target)
        assert "creation completed, the created entry is retained" in failed.stdout, failed.stdout
        assert "created entries remain in the captured project directory" in failed.stdout, failed.stdout
        before = entries(target)
        recovered = creator(binary, "existing", "cli", target, env, progress, success=True)
        assert_preserved(before, target)
        assert "RETAINED true\n" in recovered.stdout
        assert_canonical(target, canonical, "cli", target.name, {"README.md": partial})
        cases.append("actual-partial-write-false-result-retained-and-retry")

        target = root / "actual-late-manifest"
        target.mkdir()
        fault_env["FREAK_INIT_CONTROL_ROOT"] = str(target)
        fault_env["FREAK_INIT_CONTROL_MODE"] = "late-manifest"
        failed = creator(binary, "existing", "cli", target, fault_env, progress, success=False)
        assert (target / "hangar.toml").read_bytes() == FOREIGN_MANIFEST
        assert_canonical(target, canonical, "cli", target.name, {"hangar.toml": FOREIGN_MANIFEST})
        before = entries(target)
        creator(binary, "existing", "cli", target, env, progress, success=False)
        assert entries(target) == before
        assert "without replacement" in failed.stdout and "creation completed" not in failed.stdout, failed.stdout
        cases.append("actual-late-manifest-exclusive-create-refusal-and-preservation")

        for mode in ("directory-retarget-before", "directory-retarget-after"):
            target = root / ("actual-" + mode)
            target.mkdir()
            fault_env["FREAK_INIT_CONTROL_ROOT"] = str(target)
            fault_env["FREAK_INIT_CONTROL_MODE"] = mode
            failed = creator(binary, "existing", "cli", target, fault_env, progress, success=False)
            assert "template directory identity changed during initialization: src" in failed.stdout, failed.stdout
            required = expected(canonical, "cli", target.name)
            if mode == "directory-retarget-before":
                required.pop("hangar.toml")
                assert not (target / "hangar.toml").exists()
            required = {(key.replace("src/", "src-held/", 1) if key.startswith("src/") else key): data
                        for key, data in required.items()}
            required["src/foreign"] = b"foreign replacement directory authority"
            assert regular_files(target) == required, regular_files(target)
            assert "created entries remain in the captured project directory" in failed.stdout
            cases.append("actual-" + mode + "-false-result-held-source-and-foreign-preservation")

        target = root / "actual-private-retarget"
        target.mkdir()
        fault_env["FREAK_INIT_CONTROL_ROOT"] = str(target)
        fault_env["FREAK_INIT_CONTROL_MODE"] = "private-retarget"
        failed = creator(binary, "existing", "cli", target, fault_env, progress, success=False)
        assert "template directory identity changed during initialization: .freak" in failed.stdout, failed.stdout
        assert (target / ".freak/graph.lock").read_bytes() == b"foreign replacement directory authority"
        assert not (target / ".freak-held/graph.lock").exists()
        required = expected(canonical, "cli", target.name)
        # The old, now-empty private directory may remain for truthful recovery.
        assert regular_files(target) == required
        cases.append("actual-private-retarget-false-result-owned-lock-abort-foreign-lock-preserved")

    return {"cases": cases, "canonical_kinds": 3, "preserved_entries": True,
            "consumer_postcreation_faults_verified": fault_shim is not None,
            "consumer_postcreation_fault_boundary": "actual Linux interposition" if fault_shim else "pending on this platform",
            "native_windows": os.name == "nt"}


def public_corpus(cli: Path, hangar: Path | None, canonical: Path, root: Path,
                  env: dict, progress: TemplateProgress) -> list[dict]:
    result = []
    launchers = [("freak", [cli]), ("freak-hangar", [cli, "hangar"])]
    if hangar:
        launchers.append(("hangar", [hangar]))
    for kind in KINDS:
        for label, prefix in launchers:
            name = label + "-" + kind
            command = [*prefix, "init", name, "--template=" + kind]
            created = run(command, cwd=root, env=env, progress=progress, label="public-" + name)
            assert created.returncode == 0, (command, created.stdout, created.stderr)
            target = root / name
            assert_canonical(target, canonical, kind, name)
            before = entries(target)
            refused = run(command, cwd=root, env=env, progress=progress, label="public-duplicate-" + name)
            assert refused.returncode != 0 and entries(target) == before
            result.append({"launcher": label, "template": kind, "named": True,
                           "duplicate_preserved": True})
        target = root / ("default-inplace-" + kind)
        target.mkdir()
        command = [cli, "hangar", "init", "--template", kind]
        created = run(command, cwd=target, env=env, progress=progress, label="public-inplace-" + kind)
        assert created.returncode == 0, (command, created.stdout, created.stderr)
        assert_canonical(target, canonical, kind, target.name)
        result.append({"launcher": "freak-hangar", "template": kind, "inplace": True})
    if hangar:
        for kind in KINDS:
            target = root / ("standalone-inplace-" + kind)
            target.mkdir()
            command = [hangar, "init", "--template", kind]
            created = run(command, cwd=target, env=env, progress=progress, label="public-standalone-inplace-" + kind)
            assert created.returncode == 0, (command, created.stdout, created.stderr)
            assert_canonical(target, canonical, kind, target.name)
            result.append({"launcher": "hangar", "template": kind, "inplace": True})
    for label, prefix in launchers:
        name = "default-named-" + label
        command = [*prefix, "init", name]
        created = run(command, cwd=root, env=env, progress=progress, label="public-" + name)
        assert created.returncode == 0, (command, created.stdout, created.stderr)
        target = root / name
        assert_canonical(target, canonical, "cli", name)
        before = entries(target)
        refused = run(command, cwd=root, env=env, progress=progress, label="public-duplicate-" + name)
        assert refused.returncode != 0 and entries(target) == before
        result.append({"launcher": label, "template": "cli", "named": True,
                       "duplicate_preserved": True, "default_template": True})
    for label, prefix in launchers:
        if label == "freak":
            continue
        target = root / ("default-inplace-" + label)
        target.mkdir()
        command = [*prefix, "init"]
        created = run(command, cwd=target, env=env, progress=progress, label="public-default-inplace-" + label)
        assert created.returncode == 0, (command, created.stdout, created.stderr)
        assert_canonical(target, canonical, "cli", target.name)
        result.append({"launcher": label, "template": "cli", "inplace": True, "default_template": True})
    return result


def public_expectations(with_cli: bool, with_hangar: bool) -> list[dict]:
    launchers = ("freak", "freak-hangar", "hangar") if with_hangar else ("freak", "freak-hangar")
    if not with_cli:
        return []
    result = []
    for kind in KINDS:
        result.extend({"launcher": launcher, "template": kind, "named": True, "duplicate_preserved": True}
                      for launcher in launchers)
        result.append({"launcher": "freak-hangar", "template": kind, "inplace": True})
    if with_hangar:
        result.extend({"launcher": "hangar", "template": kind, "inplace": True} for kind in KINDS)
    result.extend({"launcher": launcher, "template": "cli", "named": True,
                   "duplicate_preserved": True, "default_template": True} for launcher in launchers)
    result.extend({"launcher": launcher, "template": "cli", "inplace": True, "default_template": True}
                  for launcher in launchers if launcher != "freak")
    return result


class SharedInitProgress(TemplateProgress):
    def passed(self):
        if self.report.get("public_cli_cases") != self.report["expected_public_cli_cases"]:
            raise RuntimeError("shared initializer public CLI floor is incomplete")
        self.report["public_cli_verified"] = bool(self.report["expected_public_cli_cases"])
        super().passed()


class PureControls(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="shared-init-oracle-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve(strict=True)

    def test_oracle_records_binary_and_empty_files(self):
        (self.root / "binary").write_bytes(b"\x00\xff")
        (self.root / "empty").write_bytes(b"")
        self.assertEqual(regular_files(self.root), {"binary": b"\x00\xff", "empty": b""})

    def test_byte_change_fails_preservation(self):
        path = self.root / "keep"
        path.write_bytes(b"before")
        before = entries(self.root)
        path.write_bytes(b"after")
        with self.assertRaises(AssertionError):
            assert_preserved(before, self.root)

    def test_replacement_with_equal_bytes_fails_preservation(self):
        path = self.root / "keep"
        path.write_bytes(b"same bytes")
        before = entries(self.root)
        path.rename(self.root / "owned-old")
        path.write_bytes(b"same bytes")
        with self.assertRaises(AssertionError):
            assert_preserved(before, self.root)

    @unittest.skipIf(os.name == "nt", "POSIX permission oracle")
    def test_mode_change_fails_preservation(self):
        path = self.root / "keep"
        path.write_bytes(b"same")
        path.chmod(0o600)
        before = entries(self.root)
        path.chmod(0o644)
        with self.assertRaises(AssertionError):
            assert_preserved(before, self.root)

    @unittest.skipIf(os.name == "nt", "POSIX symlinks without privilege assumptions")
    def test_links_are_not_walked_or_read(self):
        foreign = self.root / "foreign"
        foreign.mkdir()
        (foreign / "keep").write_bytes(b"foreign")
        project = self.root / "project"
        project.mkdir()
        (project / "linked-directory").symlink_to(foreign, target_is_directory=True)
        (project / "linked-file").symlink_to(foreign / "keep")
        observed = entries(project)
        self.assertEqual(set(observed), {"linked-directory", "linked-file"})
        self.assertEqual(regular_files(project), {})

    @unittest.skipIf(os.name == "nt", "POSIX broken links without privilege assumptions")
    def test_broken_link_is_retained_entry(self):
        (self.root / "broken").symlink_to(self.root / "missing")
        self.assertEqual(entries(self.root)["broken"][0], "link")

    def test_missing_retained_entry_fails(self):
        (self.root / "keep").write_bytes(b"same")
        before = entries(self.root)
        (self.root / "keep").unlink()
        with self.assertRaises(AssertionError):
            assert_preserved(before, self.root)

    def test_canonical_oracle_requires_all_three_modern_manifests(self):
        for kind in KINDS:
            inventory = expected(ROOT / "templates/v35", kind, "shared-demo")
            manifest = inventory["hangar.toml"]
            self.assertIn(b'name = "shared-demo"', manifest)
            self.assertIn(b'kind = "lib"' if kind == "lib" else b'entry = "src/main.fk"', manifest)
            self.assertNotIn(b"@@NAME@@", b"".join(inventory.values()))

    def test_consumer_identity_collision_oracle(self):
        inventory = expected(ROOT / "templates/v35", "lib", "template-consumer")
        self.assertIn(b'name = "template-consumer-app"', inventory["examples/consumer/hangar.toml"])

    def test_runtime_control_uses_actual_module_without_stub_initializer(self):
        source = (ROOT / "src/cli/templates.fk").read_text()
        self.assertIn("task cli_initialize_project_at(", source)
        self.assertIn("cli_initialize_project_at(kind, held, name)", MAIN)
        self.assertNotIn("task cli_initialize_project", MAIN)

    def test_public_floor_cannot_pass_with_an_omitted_inplace_case(self):
        expected_cases = public_expectations(True, True)
        report = {"expected_public_cli_cases": expected_cases, "public_cli_cases": expected_cases[:-1]}
        progress = SharedInitProgress(None, report, [{"backend": "c", "optimization": 0}], [])
        with self.assertRaisesRegex(RuntimeError, "public CLI floor is incomplete"):
            progress.passed()

    def test_public_floor_cannot_omit_standalone_hangar(self):
        self.assertEqual(len(public_expectations(True, True)), 20)
        self.assertEqual(len(public_expectations(True, False)), 12)
        self.assertEqual(len(public_expectations(False, False)), 0)
        self.assertEqual([row["template"] for row in public_expectations(True, True)
                          if row["launcher"] == "hangar" and row.get("named") and not row.get("default_template")], list(KINDS))

    def test_windows_retarget_refusal_oracle_preserves_every_entry(self):
        target = self.root / "held-original"
        target.mkdir()
        (target / "keep").write_bytes(b"retained")
        before = entries(target)
        output = "RETARGET_REFUSED access denied\nBORROWED_ROOT windows:123\nERROR \n"
        self.assertEqual(retarget_outcome(output, target, self.root / "moved", ROOT / "templates/v35", before,
                                         windows=True), "windows-held-root-retarget-refusal")
        (target / "keep").write_bytes(b"changed")
        with self.assertRaises(AssertionError):
            retarget_outcome(output, target, self.root / "moved", ROOT / "templates/v35", before, windows=True)

    def test_windows_actual_retarget_oracle_requires_captured_root(self):
        target = self.root / "held-original"
        target.mkdir()
        before = entries(target)
        moved = self.root / "held-moved"
        target.rename(moved)
        for relative, data in expected(ROOT / "templates/v35", "cli", "held-original").items():
            path = moved / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        target.mkdir()
        (target / "foreign").write_bytes(b"replacement directory is foreign")
        output = "RETARGET_MOVED\nOK\nCAPTURED_PATH " + str(moved) + "\nCAPTURED_IDENTITY id123\nBORROWED_ROOT id123\n"
        self.assertEqual(retarget_outcome(output, target, moved, ROOT / "templates/v35", before, windows=True),
                         "captured-held-root-after-retarget")
        with self.assertRaises(AssertionError):
            retarget_outcome(output.replace(str(moved), str(target)), target, moved, ROOT / "templates/v35", before,
                             windows=True)

    def test_retarget_completed_durability_failure_is_never_a_refusal(self):
        target = self.root / "held-original"
        target.mkdir()
        with self.assertRaises(AssertionError):
            retarget_outcome("RETARGET_COMPLETED_ERROR sync failed\nRETARGET_REFUSED wrong\nBORROWED_ROOT id\nERROR \n",
                             target, self.root / "moved", ROOT / "templates/v35", {}, windows=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pure", action="store_true")
    parser.add_argument("--compiler", type=Path)
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG", "clang"))
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--templates-root", type=Path)
    parser.add_argument("--backend", choices=("c", "llvm"), action="append")
    parser.add_argument("--optimization", type=int, choices=(0, 2, 3), action="append")
    parser.add_argument("--cli", type=Path)
    parser.add_argument("--hangar", type=Path)
    parser.add_argument("--payload-home", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.pure:
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(PureControls))
        return 0 if result.wasSuccessful() else 1
    if not args.compiler or not args.runtime_root or not args.report:
        parser.error("native mode requires --compiler, --runtime-root and a fresh --report")
    if args.hangar and not args.cli:
        parser.error("--hangar also requires --cli")
    compiler = args.compiler.resolve(strict=True)
    runtime = args.runtime_root.resolve(strict=True)
    canonical = (args.templates_root or ROOT / "templates/v35").resolve(strict=True)
    clang = Path(shutil.which(args.clang) or args.clang).resolve(strict=True)
    generator = (ROOT / "src/cli/templates.fk").read_text()
    pinned = [compiler, clang, Path(__file__).resolve(strict=True), ROOT / "tests/v3_v35_templates.py",
              ROOT / "tests/v3_v35_acceptance.py", ROOT / "src/cli/templates.fk",
              *sorted(path for path in canonical.rglob("*") if path.is_file()),
              *sorted(path for path in runtime.rglob("*") if path.is_file())]
    if args.cli:
        pinned.append(args.cli.resolve(strict=True))
    if args.hangar:
        pinned.append(args.hangar.resolve(strict=True))
    if args.payload_home:
        pinned.extend(sorted(path for path in args.payload_home.resolve(strict=True).rglob("*") if path.is_file()))
    before = {str(path): digest(path) for path in pinned}
    env = os.environ.copy()
    selected_runtime = canonical.parents[1] / "runtime"
    if not selected_runtime.is_dir():
        selected_runtime = canonical.parents[1] / "freakc/runtime"
    env["TEMPLATE_RUNTIME"] = str(selected_runtime)
    if args.payload_home:
        env["FREAK_HOME"] = str(args.payload_home.resolve(strict=True))
    backends = args.backend or ("c", "llvm")
    optimizations = args.optimization or (0, 2, 3)
    matrices = [{"backend": backend, "optimization": optimization}
                for backend in backends for optimization in optimizations]
    evidence = {"pinned_input_sha256": before, "strict_borrow": True,
                "pure_checks_are_not_native_evidence": True, "public_cli_supplied": bool(args.cli),
                "native_windows": os.name == "nt", "shared_init_matrices": [],
                "expected_public_cli_cases": public_expectations(bool(args.cli), bool(args.hangar)),
                "public_cli_cases": [], "public_cli_verified": False}
    with SharedInitProgress(args.report, evidence, matrices, []) as progress:
        with tempfile.TemporaryDirectory(prefix="freak-shared-init-native-") as temporary:
            root = Path(temporary).resolve(strict=True)
            fault_shim = None
            if sys.platform.startswith("linux"):
                shim_source = root / "fault-control.c"
                shim_source.write_text(FAULT_SHIM, encoding="utf-8")
                fault_shim = root / "fault-control.so"
                linked = run([clang, "-O2", "-shared", "-fPIC", shim_source, "-ldl", "-o", fault_shim],
                             cwd=root, progress=progress, label="shared-init-fault-control-link")
                assert linked.returncode == 0, (linked.stdout, linked.stderr)
                evidence["fault_control_source_sha256"] = digest(shim_source)
                evidence["fault_control_image_sha256"] = digest(fault_shim)
            source = root / "shared-init.fk"
            source.write_text(SELECTORS + "\n" + generator + "\n" + MAIN, encoding="utf-8")
            for backend in backends:
                compiled = run([compiler, source, "--" + backend, "--strict-borrow"], cwd=root,
                               progress=progress, label="shared-init-compile-" + backend)
                assert compiled.returncode == 0, (compiled.stdout, compiled.stderr)
                generated = Path(str(source) + (".c" if backend == "c" else ".ll"))
                for optimization in optimizations:
                    progress.matrix_started("creator", backend, optimization)
                    binary = root / ("shared-init-" + backend + "-O" + str(optimization))
                    command = [clang, "-O" + str(optimization), generated, runtime / "freak_runtime.c",
                               "-I" + str(runtime), "-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1",
                               "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1", "-o", binary]
                    if backend == "llvm":
                        command.append(runtime / "freak_llvm_runtime.c")
                    command.extend(["-lws2_32", "-lshell32"] if os.name == "nt" else ["-lm"])
                    linked = run(command, cwd=root, progress=progress, label="shared-init-link")
                    assert linked.returncode == 0, (linked.stdout, linked.stderr)
                    cases_root = root / ("cases-" + backend + "-O" + str(optimization))
                    cases_root.mkdir()
                    corpus = native_corpus(binary, canonical, cases_root, env, progress, fault_shim)
                    evidence["shared_init_matrices"].append({"backend": backend, "optimization": optimization,
                                                             "corpus": corpus})
                    # TemplateProgress retains its exact matrix-floor contract.
                    evidence.setdefault("creator_matrices", []).append({"backend": backend, "optimization": optimization,
                                                                          "corpus": corpus})
                    progress.matrix_finished()
                    print("PASS shared initializer " + backend + " O" + str(optimization), flush=True)
            if args.cli:
                projects = root / "public-projects"
                projects.mkdir()
                evidence["public_cli_cases"] = public_corpus(args.cli.resolve(strict=True),
                    args.hangar.resolve(strict=True) if args.hangar else None, canonical, projects, env, progress)
            after = {str(path): digest(path) for path in pinned}
            assert before == after, "pinned initializer/compiler/runtime/payload inputs changed"
            evidence["pinned_inputs_unchanged"] = True
            progress.passed()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
