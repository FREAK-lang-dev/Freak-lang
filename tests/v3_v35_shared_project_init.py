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
                fs::result_release(moved)
                if proceed {
                    pilot replacement = fs::mkdir_checked(target + "")
                    proceed = fs::result_ok(replacement)
                    fs::result_release(replacement)
                    if proceed {
                        pilot foreign = fs::write_checked(target + "/foreign", "replacement directory is foreign")
                        proceed = fs::result_ok(foreign)
                        fs::result_release(foreign)
                    }
                } else { say "RETARGET_REFUSED" }
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
            progress: TemplateProgress, *, success: bool, extra: tuple = ()):
    result = run([binary, mode, kind, destination, *extra], cwd=destination.parent,
                 env=env, progress=progress, label="shared-init-" + mode + "-" + destination.name)
    assert result.returncode == 0 and not result.stderr, (result.returncode, result.stdout, result.stderr)
    lines = result.stdout.splitlines()
    assert ("OK" in lines) == success, (success, result.stdout)
    if not success:
        assert any(line.startswith("ERROR ") for line in lines), result.stdout
    return result


def native_corpus(binary: Path, canonical: Path, root: Path, env: dict,
                  progress: TemplateProgress) -> dict:
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
        cases.append("before-effects-" + variant)

    for leaf in ("transaction.marker", "transaction.manifest.before", "transaction.lock.before", "graph.lock"):
        target = root / ("retained-" + leaf.replace(".", "-"))
        private = target / ".freak"
        private.mkdir(parents=True)
        (private / leaf).write_bytes(b"retained generation authority\x00\xff")
        before = entries(target)
        creator(binary, "existing", "cli", target, env, progress, success=False)
        assert entries(target) == before
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
    moved = root / "held-moved"
    result = creator(binary, "retarget", "cli", target, env, progress,
                     success=os.name != "nt", extra=(moved,))
    if os.name == "nt":
        assert "RETARGET_REFUSED\n" in result.stdout and not moved.exists()
        assert entries(target) == {}
        cases.append("windows-held-root-retarget-refusal")
    else:
        assert regular_files(target) == {"foreign": b"replacement directory is foreign"}
        assert_canonical(moved, canonical, "cli", "held-original")
        assert "CAPTURED_PATH " + str(moved) + "\n" in result.stdout, result.stdout
        assert "CAPTURED_PATH " + str(target) + "\n" not in result.stdout
        cases.append("captured-held-root-after-retarget")

    return {"cases": cases, "canonical_kinds": 3, "preserved_entries": True,
            "manifest_published_last": True, "native_windows": os.name == "nt"}


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
        self.assertEqual(len(public_expectations(True, True)), 12)
        self.assertEqual(len(public_expectations(True, False)), 9)
        self.assertEqual(len(public_expectations(False, False)), 0)
        self.assertEqual([row["template"] for row in public_expectations(True, True)
                          if row["launcher"] == "hangar"], list(KINDS))


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
                    corpus = native_corpus(binary, canonical, cases_root, env, progress)
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
