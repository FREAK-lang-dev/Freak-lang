#!/usr/bin/env python3
"""Truthful Hangar failure and prior-generation preservation acceptance cases.

This first slice deliberately does not claim transactional replacement, lock v2,
package graph compilation, or archive/platform verification. Pass fresh native
binaries explicitly; Python is only an independent orchestration/oracle path.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from unittest import mock
from urllib.error import URLError

ANSI = re.compile(r"\x1b\[[0-9;]*m")
MANIFEST = '[project]\nname = "consumer"\nversion = "0.1.0"\n\n[dependencies]\n'
LOCK = ('# Prior verified generation\n[[package]]\nname = "existing"\n'
        'version = "1.0.0"\nsource = "owner/existing"\nsha256 = "' + 'a' * 64 + '"\n')
NATIVE_CASES = (
    "missing-add-argument", "missing-remove-argument", "unknown-command",
    "unavailable-registry-add", "unavailable-registry-install", "invalid-package-name",
    "failed-git-add", "failed-git-install", "failed-git-update",
    "preserved-existing-add", "preserved-existing-update", "unavailable-publication",
)


def snapshot(root: Path) -> dict[str, bytes]:
    result = {}
    for path in [root / "hangar.toml", root / "hangar.lock", root / "previous-build",
                 root / "previous-build.freak-run-cache"]:
        if path.exists():
            result[str(path.relative_to(root))] = path.read_bytes()
    modules = root / "hangar_modules" / "existing"
    if modules.exists():
        for path in sorted(modules.rglob("*")):
            if path.is_file():
                result[str(path.relative_to(root))] = path.read_bytes()
    return result


def project(root: Path, dependency: str = "") -> None:
    root.mkdir()
    (root / "hangar.toml").write_text(MANIFEST + dependency, encoding="utf-8")
    (root / "hangar.lock").write_text(LOCK, encoding="utf-8")
    package = root / "hangar_modules" / "existing"
    package.mkdir(parents=True)
    (package / "existing.fk").write_text('task value() -> int { give back 42 }\n', encoding="utf-8")
    (package / "hangar.toml").write_text('[project]\nname = "existing"\nversion = "1.0.0"\n', encoding="utf-8")
    (root / "previous-build").write_bytes(b"previous native executable\x00")
    (root / "previous-build.freak-run-cache").write_bytes(b"previous success proof\n")


def failed_git(tool_root: Path, clang: Path) -> None:
    tool_root.mkdir()
    source = tool_root / "git-failure.c"
    source.write_text('#include <stdio.h>\nint main(void) { fputs("injected Git fetch failure\\n", stderr); return 23; }\n', encoding="ascii")
    executable = tool_root / ("git.exe" if os.name == "nt" else "git")
    result = subprocess.run([str(clang), str(source), "-o", str(executable)],
                            capture_output=True, text=True, timeout=30, check=False)
    if result.returncode:
        raise AssertionError("Could not build native failure injector: " + result.stdout + result.stderr)


def native(freak: Path, hangar: Path, clang: Path, root: Path) -> None:
    tool_root = root / "tools"
    failed_git(tool_root, clang)
    env = os.environ.copy()
    env["PATH"] = str(tool_root) + os.pathsep + env.get("PATH", "")
    env["NO_COLOR"] = "1"
    cases = {
        "missing-add-argument": (["add"], "", "Usage:"),
        "missing-remove-argument": (["remove"], "", "Usage:"),
        "unknown-command": (["not-a-hangar-command"], "", "Unknown hangar command"),
        "unavailable-registry-add": (["add", "missing"], "", "Registry package sources are unavailable"),
        "unavailable-registry-install": (["install"], 'missing = "^1.0"\n', "Registry package sources are unavailable"),
        "invalid-package-name": (["add", "../escape", "owner/repository"], "", "Invalid package name"),
        "failed-git-add": (["add", "missing", "owner/repository"], "", "Could not fetch missing"),
        "failed-git-install": (["install"], 'missing = { git = "owner/repository", version = "latest" }\n', "Could not fetch missing"),
        "failed-git-update": (["update", "missing"], 'missing = { git = "owner/repository", version = "latest" }\n', "Could not fetch missing"),
        "preserved-existing-add": (["add", "existing", "owner/repository"], "", "Cannot safely replace existing"),
        "preserved-existing-update": (["update", "existing"], 'existing = { git = "owner/repository", version = "latest" }\n', "Cannot safely replace existing"),
        "unavailable-publication": (["publish"], "", "Publication is unavailable"),
    }
    assert tuple(cases) == NATIVE_CASES, "Failure acceptance inventory drift"
    for invocation, binary, prefix in [("freak", freak, ["hangar"]), ("standalone", hangar, [])]:
        for name, (args, dependency, diagnostic) in cases.items():
            cwd = root / f"{invocation}-{name}"
            project(cwd, dependency)
            before = snapshot(cwd)
            completed = subprocess.run([str(binary), *prefix, *args], cwd=cwd, env=env,
                                       capture_output=True, text=True, encoding="utf-8",
                                       errors="replace", timeout=30, check=False)
            output = ANSI.sub("", completed.stdout + completed.stderr)
            assert completed.returncode > 0, (name, completed.returncode, output)
            assert diagnostic in output, (name, output)
            assert "INSTALLED" not in output and "PUBLISHED" not in output, (name, output)
            assert snapshot(cwd) == before, (name, "prior generation changed")
            assert not (cwd / "hangar_modules" / "missing").exists(), (name, "failed dependency materialized")
            assert not (root / "escape").exists(), (name, "package escaped project")
            print(f"native:{invocation}:{name}:passed")


def python_compatibility(root: Path) -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from freakc import hangar as module
    for name, existing, operation in [("fetch-install", False, "install"),
                                       ("fetch-add", False, "add"),
                                       ("existing-add", True, "add")]:
        cwd = root / ("python-" + name)
        dependency = 'missing = { git = "owner/repository", version = "latest" }\n' if operation == "install" else ""
        project(cwd, dependency)
        package = "existing" if existing else "missing"
        before = snapshot(cwd)
        with mock.patch.object(module.request, "urlopen", side_effect=URLError("injected failure")), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = module.hangar_install(cwd) if operation == "install" else module.hangar_add(cwd, package, "owner/repository")
        assert result == 1, (name, result)
        assert snapshot(cwd) == before, (name, "prior generation changed")
        assert not (cwd / "hangar_modules" / "missing").exists(), (name, "stub created")
        print(f"python:{name}:passed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freak", type=Path)
    parser.add_argument("--hangar", type=Path)
    parser.add_argument("--clang", type=Path)
    parser.add_argument("--python-only", action="store_true")
    parser.add_argument("--list", action="store_true", help="Print the expected native case inventory")
    args = parser.parse_args()
    if args.list:
        for invocation in ("freak", "standalone"):
            for case in NATIVE_CASES:
                print(f"native:{invocation}:{case}")
        return 0
    if not args.python_only and not all((args.freak, args.hangar, args.clang)):
        parser.error("fresh --freak, --hangar, and native --clang paths are required")
    with tempfile.TemporaryDirectory(prefix="freak-v35-hangar-") as temporary:
        root = Path(temporary)
        python_compatibility(root)
        if not args.python_only:
            native(args.freak.resolve(strict=True), args.hangar.resolve(strict=True),
                   args.clang.resolve(strict=True), root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
