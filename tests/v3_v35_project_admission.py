#!/usr/bin/env python3
"""Exercise physical project discovery, platform roots, and no-follow leaves.

The supplied compiler builds the current CLI sources; the supplied payload is
used only for its unchanged runtime/std files. Windows path parsing is exercised
on every host, while filesystem execution remains native to the running host.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

import v3_word_foundation as foundation
from v3_v35_hangar import probe_transpile, require_resource_conservation, task_source
from v3_v35_package_sources import PROGRAM, package_probe_source


def extended_windows_path(path: str) -> str:
    """Preserve the kernel's DOS/UNC spelling for these physical test roots."""
    if path.startswith("\\\\?\\"):
        return path
    if path.startswith("\\\\"):
        return "\\\\?\\UNC\\" + path[2:]
    return "\\\\?\\" + path


def assert_manifest_selection(actual: str, physical_manifest: Path) -> None:
    expected = str(physical_manifest)
    if os.name == "nt":
        expected = extended_windows_path(expected)
    assert actual == "manifest:" + expected + "\n", (actual, expected)
    reported = actual[len("manifest:"):-1]
    assert Path(reported).samefile(physical_manifest), (reported, physical_manifest)


def run_gate(compiler: Path, clang: Path, payload: Path, root: Path) -> list[str]:
    repo = Path(__file__).resolve().parents[1]
    runtime = payload / "runtime"
    sources = (repo / "src/cli/package_sources.fk").read_text(encoding="utf-8")
    checks: list[str] = []

    def passed(name: str) -> None:
        checks.append(name)
        print("PASS", name, flush=True)

    def execute(binary: Path, *arguments: str, cwd: Path | None = None) -> str:
        result = foundation.run([str(binary), *arguments], cwd or root,
                                foundation.sanitizer_env(), timeout=45)
        assert result.returncode == 0, (result.args, result.returncode, result.stdout, result.stderr)
        require_resource_conservation(foundation, result.stderr)
        return result.stdout

    helpers = "\n".join(task_source(sources, name) for name in (
        "package_path_byte_length", "package_path_root_length",
        "package_parent_path", "package_leaf_path"))
    posix_cases = [
        ("/", "/", ""), ("/parent/file.fk", "/parent", "file.fk"),
        ("relative.fk", ".", "relative.fk"), ("", ".", ""),
        ("/日本/Ω/last.fk", "/日本/Ω", "last.fk"),
        ("/parent/Literal\\source.fk", "/parent", "Literal\\source.fk"),
        ("/parent/Colon:Name.fk", "/parent", "Colon:Name.fk"),
    ]
    windows_cases = [
        ("C:\\", "C:\\", ""), ("C:/", "C:/", ""),
        ("C:\\source.fk", "C:\\", "source.fk"),
        ("C:/日本/Ω/source.fk", "C:/日本/Ω", "source.fk"),
        ("\\\\?\\C:\\", "\\\\?\\C:\\", ""),
        ("//?/C:/source.fk", "//?/C:/", "source.fk"),
        ("\\\\?\\C:\\日本\\Ω\\source.fk", "\\\\?\\C:\\日本\\Ω", "source.fk"),
        ("\\\\server\\share", "\\\\server\\share", "share"),
        ("\\\\server\\share\\", "\\\\server\\share\\", ""),
        ("\\\\server\\share\\source.fk", "\\\\server\\share\\", "source.fk"),
        ("//server/share/日本/source.fk", "//server/share/日本", "source.fk"),
        ("\\\\?\\UNC\\server\\share", "\\\\?\\UNC\\server\\share", "share"),
        ("\\\\?\\UNC\\server\\share\\", "\\\\?\\UNC\\server\\share\\", ""),
        ("\\\\?\\UNC\\server\\share\\source.fk", "\\\\?\\UNC\\server\\share\\", "source.fk"),
        ("//?/UNC/日本/共有/Ω/source.fk", "//?/UNC/日本/共有/Ω", "source.fk"),
        ("\\\\?\\C:\\" + "long-日本\\" * 36 + "source.fk",
         "\\\\?\\C:\\" + "long-日本\\" * 35 + "long-日本", "source.fk"),
    ]
    for backend in ("c", "llvm"):
        for windows, cases in ((False, posix_cases), (True, windows_cases)):
            program = root / f"paths-{backend}-{windows}.fk"
            program.write_text(helpers.replace("process::platform_is_windows()", str(windows).lower()) +
                               '\ntask main() { say package_parent_path(process::arg(1)) '
                               'say package_leaf_path(process::arg(1)) }\n', encoding="utf-8")
            generated = probe_transpile(foundation, None, compiler, repo, program, backend)
            binary = program.with_suffix(".exe" if os.name == "nt" else "")
            foundation.compile_generated(clang=str(clang), repo=repo, runtime_root=runtime,
                                         generated=generated, backend=backend, binary=binary)
            for path, parent, leaf in cases:
                assert execute(binary, path) == parent + "\n" + leaf + "\n", (backend, path, parent, leaf)
            passed(f"{backend}:actual-path-helpers:{'windows-model' if windows else 'posix-model'}:{len(cases)}")

        program = root / f"discovery-{backend}.fk"
        program.write_text(package_probe_source(repo) + "\n" + PROGRAM, encoding="utf-8")
        generated = probe_transpile(foundation, None, compiler, repo, program, backend)
        binary = program.with_suffix(".exe" if os.name == "nt" else "")
        foundation.compile_generated(clang=str(clang), repo=repo, runtime_root=runtime,
                                     generated=generated, backend=backend, binary=binary)
        physical = root / f"physical-{backend}-日本-Ω"
        nested = physical / "nested"
        nested.mkdir(parents=True)
        manifest = physical / "hangar.toml"
        dependency = root / f"dep-{backend}-日本"
        dependency.mkdir()
        (dependency / "hangar.toml").write_text('[project]\nname="dep"\nversion="1.0.0"\nkind="lib"\n[modules]\ncore="core.fk"\n[exports]\nvalue="core::value"\n', encoding="utf-8")
        (dependency / "core.fk").write_text('task value() -> int { give back 42 }\n', encoding="utf-8")
        manifest.write_text('[project]\nname="admission"\nversion="1.0.0"\nkind="app"\nentry="main.fk"\n'
                            '[dependencies]\ndep={path="../' + dependency.name + '"}\n', encoding="utf-8")
        (physical / "main.fk").write_text('task main() { say "ADMITTED" }\n', encoding="utf-8")
        assert_manifest_selection(execute(binary, str(nested / "selected.fk"), "discover"), manifest)
        passed(f"{backend}:nearest-physical-unicode-project-and-local-dependency")
        standalone = root / f"standalone-{backend}"
        standalone.mkdir()
        assert execute(binary, str(standalone / "main.fk"), "discover") == "standalone\n"
        assert not (standalone / ".freak").exists()
        passed(f"{backend}:standalone-walk-terminates-at-host-root")
        absent = execute(binary, str(root / "missing" / "main.fk"), "discover")
        assert absent.startswith("error:cannot inspect source's enclosing project directory:"), absent
        passed(f"{backend}:missing-parent-remains-error")
        not_directory = root / f"not-directory-{backend}"
        not_directory.write_bytes(b"ordinary file")
        rejected = execute(binary, str(not_directory / "main.fk"), "discover")
        assert rejected.startswith("error:cannot inspect source's enclosing project directory:"), rejected
        passed(f"{backend}:non-directory-parent-remains-error")
        if os.name != "nt":
            alias = root / f"alias-{backend}"
            alias.symlink_to(physical, target_is_directory=True)
            assert_manifest_selection(execute(binary, str(alias / "nested" / "main.fk"), "discover"), manifest)
            assert_manifest_selection(execute(binary, str(alias / "main.fk"), "discover"), manifest)
            passed(f"{backend}:directory-alias-adopted-as-physical-project")
            rejected = execute(binary, str(alias / "hangar.toml"), "ordinary")
            assert rejected.startswith("error:") and "without following links" in rejected, rejected
            passed(f"{backend}:explicit-manifest-alias-still-refused")
            dependency_alias = root / f"dep-alias-{backend}"
            dependency_alias.symlink_to(dependency, target_is_directory=True)
            previous_manifest = manifest.read_bytes()
            previous_lock = manifest.with_name("hangar.lock").read_bytes()
            manifest.write_bytes(previous_manifest.replace(dependency.name.encode(), dependency_alias.name.encode()))
            rejected = execute(binary, str(physical / "main.fk"), "discover")
            assert rejected.startswith("error:") and "without following links" in rejected, rejected
            assert manifest.with_name("hangar.lock").read_bytes() == previous_lock
            manifest.write_bytes(previous_manifest)
            passed(f"{backend}:local-dependency-alias-refused-with-lock-preserved")
            unsafe = root / f"unsafe-{backend}"
            unsafe.mkdir()
            (unsafe / "hangar.toml").symlink_to(manifest)
            rejected = execute(binary, str(unsafe / "main.fk"), "discover")
            assert rejected.startswith("error:cannot read enclosing package manifest:"), rejected
            passed(f"{backend}:manifest-link-remains-error")
            broken = root / f"broken-{backend}"
            broken.symlink_to(root / "missing", target_is_directory=True)
            rejected = execute(binary, str(broken / "main.fk"), "discover")
            assert rejected.startswith("error:cannot inspect source's enclosing project directory:"), rejected
            passed(f"{backend}:broken-directory-alias-remains-error")

    # A current-source public CLI provides actual build/run evidence, alongside
    # the sanitizer/audit probes above. Its compiler/runtime inputs are unchanged.
    cli_source = root / "current-cli.fk"
    cli_source.write_bytes(b"".join((repo / path).read_bytes() for path in foundation.CLI_SOURCES))
    generated = probe_transpile(foundation, None, compiler, repo, cli_source, "c")
    cli = root / ("freak.exe" if os.name == "nt" else "freak")
    linked = foundation.run([str(clang), "-w", "-O2", str(generated), str(runtime / "freak_runtime.c"),
                             "-I", str(runtime), "-o", str(cli), *(["-lws2_32"] if os.name == "nt" else ["-lm"])], repo)
    assert linked.returncode == 0, linked.stdout + linked.stderr
    environment = os.environ.copy()
    environment.update({"FREAK_HOME": str(payload), "NO_COLOR": "1", "PATH": str(clang.parent) + os.pathsep + environment.get("PATH", "")})
    physical = root / "public-日本-Ω"
    physical = physical.joinpath(*(["long-component-日本-Ω"] * 12))
    physical.mkdir(parents=True)
    (physical / "main.fk").write_text('task main() { say "ADMITTED" }\n', encoding="utf-8")
    selected = physical / "main.fk"
    if os.name != "nt":
        alias = root / "public-alias"
        alias.symlink_to(physical, target_is_directory=True)
        selected = alias / "main.fk"
    for backend in ("c", "llvm"):
        output = root / (f"public-{backend}.exe" if os.name == "nt" else f"public-{backend}")
        built = foundation.run([str(cli), "build", str(selected), "--" + backend, "--opt=0", "--output=" + str(output)], root, environment)
        assert built.returncode == 0 and output.is_file(), (built.returncode, built.stdout, built.stderr)
        result = foundation.run([str(output)], root)
        assert result.returncode == 0 and result.stdout == "ADMITTED\n" and not result.stderr, result
        passed(f"public:{backend}:unicode-long-directory-alias-standalone-build-and-run")
    leaf = physical / "linked.fk"
    if os.name != "nt":
        leaf.symlink_to(physical / "main.fk")
        unchanged = foundation.run([str(cli), "transpile", str(leaf), "--c"], root, environment)
        assert unchanged.returncode == 0 and Path(str(leaf) + ".c").is_file(), unchanged
        passed("public:standalone-selected-source-link-behavior-unchanged")
    manifest = physical / "hangar.toml"
    manifest.write_text('[project]\nname="admission"\nversion="1.0.0"\nkind="app"\nentry="main.fk"\n', encoding="utf-8")
    for backend in ("c", "llvm"):
        output = root / (f"project-{backend}.exe" if os.name == "nt" else f"project-{backend}")
        built = foundation.run([str(cli), "build", str(selected), "--" + backend, "--opt=0", "--output=" + str(output)], root, environment)
        assert built.returncode == 0 and output.is_file(), (built.returncode, built.stdout, built.stderr)
        result = foundation.run([str(output)], root)
        assert result.returncode == 0 and result.stdout == "ADMITTED\n" and not result.stderr, result
        passed(f"public:{backend}:unicode-long-directory-alias-project-build-and-run")
    if os.name != "nt":
        # Immutable project admission must reject a declared source link. A
        # standalone caller-selected link has no package containment contract.
        manifest.write_text('[project]\nname="admission"\nversion="1.0.0"\nkind="app"\nentry="linked.fk"\n', encoding="utf-8")
        rejected = foundation.run([str(cli), "build", str(leaf), "--c", "--output=" + str(root / "rejected")], root, environment)
        assert rejected.returncode != 0 and not (root / "rejected").exists(), rejected
        assert "Package error:" in rejected.stdout, rejected
        passed("public:declared-source-leaf-symlink-still-refused")
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", type=Path, required=True)
    parser.add_argument("--clang", type=Path, required=True)
    parser.add_argument("--payload-home", type=Path, required=True)
    parser.add_argument("--probe-root", type=Path)
    args = parser.parse_args()
    if args.probe_root:
        args.probe_root.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="freak-project-admission-") as temporary:
        root = args.probe_root.resolve() if args.probe_root else Path(temporary).resolve()
        checks = run_gate(args.compiler.resolve(strict=True), args.clang.resolve(strict=True), args.payload_home.resolve(strict=True), root)
        (root / "report.json").write_text(json.dumps({"host": os.name, "checks": checks,
            "package_sources_sha256": hashlib.sha256((Path(__file__).resolve().parents[1] / "src/cli/package_sources.fk").read_bytes()).hexdigest(),
            "windows_filesystem_execution_claimed": os.name == "nt"}, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
