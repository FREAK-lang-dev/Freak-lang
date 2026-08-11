#!/usr/bin/env python3
"""Synchronize and validate FREAK's repository-wide release version."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def read_version() -> str:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not SEMVER.fullmatch(version):
        raise SystemExit(f"VERSION is not major.minor.patch: {version!r}")
    return version


def replace_exact(path: Path, pattern: str, replacement: str) -> None:
    original = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, original)
    if count == 0:
        raise SystemExit(f"could not update version contract in {path.relative_to(ROOT)}")
    path.write_text(updated, encoding="utf-8", newline="\n")


def set_version(version: str) -> None:
    if not SEMVER.fullmatch(version):
        raise SystemExit(f"version is not major.minor.patch: {version!r}")
    old_version = read_version()
    (ROOT / "VERSION").write_text(version + "\n", encoding="utf-8", newline="\n")
    replace_exact(
        ROOT / "src" / "compiler" / "v3" / "globals.fk",
        r'pilot FREAK_VERSION = "[0-9]+\.[0-9]+\.[0-9]+"',
        f'pilot FREAK_VERSION = "{version}"',
    )
    replace_exact(
        ROOT / "packaging" / "homebrew" / "freak.rb",
        r'version "[0-9]+\.[0-9]+\.[0-9]+"',
        f'version "{version}"',
    )

    scoop_path = ROOT / "packaging" / "scoop" / "freak.json"
    scoop = json.loads(scoop_path.read_text(encoding="utf-8"))
    scoop["version"] = version
    scoop["url"] = f"https://github.com/FREAK-lang-dev/Freak-lang/releases/download/v{version}/freak-windows-x64.zip"
    scoop_path.write_text(json.dumps(scoop, indent=2) + "\n", encoding="utf-8", newline="\n")

    winget_root = ROOT / "packaging" / "winget" / "manifests" / "F" / "FREAK" / "freak"
    source_dir = winget_root / old_version
    target_dir = winget_root / version
    if not target_dir.exists():
        if not source_dir.is_dir():
            raise SystemExit(f"source WinGet manifest directory missing: {source_dir}")
        shutil.copytree(source_dir, target_dir)
    for manifest in target_dir.glob("*.yaml"):
        text = manifest.read_text(encoding="utf-8")
        text = text.replace(old_version, version)
        manifest.write_text(text, encoding="utf-8", newline="\n")

    agents = ROOT / "AGENTS.md"
    replace_exact(
        agents,
        r"Public release: \*\*v[0-9]+\.[0-9]+\.[0-9]+",
        f"Public release: **v{version}",
    )
    replace_exact(
        ROOT / "README.md",
        r"(\[!\[Version\]\(https://img\.shields\.io/badge/)v[0-9]+\.[0-9]+\.[0-9]+",
        rf"\g<1>v{version}",
    )
    replace_exact(
        ROOT / "CLAUDE.md",
        r"(current release \*\*v)[0-9]+\.[0-9]+\.[0-9]+",
        rf"\g<1>{version}",
    )
    check_version(version)
    print(f"FREAK release version synchronized: {version}")


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def check_version(version: str, tag: str | None = None) -> None:
    errors: list[str] = []
    globals_text = (ROOT / "src" / "compiler" / "v3" / "globals.fk").read_text(encoding="utf-8")
    cli_text = (ROOT / "src" / "cli" / "version.fk").read_text(encoding="utf-8")
    require(f'pilot FREAK_VERSION = "{version}"' in globals_text, "FREAK_VERSION differs from VERSION", errors)
    require("pilot FREAKC_VERSION = FREAK_VERSION" in globals_text, "FREAKC_VERSION does not derive from FREAK_VERSION", errors)
    require("pilot CLI_VERSION = FREAK_VERSION" in cli_text, "CLI_VERSION does not derive from FREAK_VERSION", errors)

    homebrew = (ROOT / "packaging" / "homebrew" / "freak.rb").read_text(encoding="utf-8")
    require(f'version "{version}"' in homebrew, "Homebrew version differs from VERSION", errors)
    scoop = json.loads((ROOT / "packaging" / "scoop" / "freak.json").read_text(encoding="utf-8"))
    require(scoop.get("version") == version, "Scoop version differs from VERSION", errors)
    require(f"/v{version}/freak-windows-x64.zip" in scoop.get("url", ""), "Scoop URL differs from VERSION", errors)

    winget_dir = ROOT / "packaging" / "winget" / "manifests" / "F" / "FREAK" / "freak" / version
    manifests = sorted(winget_dir.glob("*.yaml")) if winget_dir.is_dir() else []
    require(len(manifests) == 3, f"WinGet {version} must contain exactly three manifests", errors)
    for manifest in manifests:
        text = manifest.read_text(encoding="utf-8")
        require(f"PackageVersion: {version}" in text, f"{manifest.name} PackageVersion differs", errors)
        for url_version in re.findall(r"/v([0-9]+\.[0-9]+\.[0-9]+)", text):
            require(url_version == version, f"{manifest.name} release URL differs from VERSION", errors)

    agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    require(f"Public release: **v{version}" in agents_text, "AGENTS.md public release differs from VERSION", errors)
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
    require(
        f"[![Version](https://img.shields.io/badge/v{version}-" in readme_text,
        "README.md version badge differs from VERSION",
        errors,
    )
    claude_text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    require(
        f"current release **v{version}" in claude_text,
        "CLAUDE.md current release differs from VERSION",
        errors,
    )
    require(
        "python -u tools/release_version.py set <major.minor.patch>" in claude_text,
        "CLAUDE.md does not document the authoritative release bump command",
        errors,
    )
    require(
        "hardcoded in **two files**" not in claude_text,
        "CLAUDE.md still documents obsolete hand-maintained version mirrors",
        errors,
    )
    if tag is not None:
        require(tag == f"v{version}", f"Git tag {tag!r} must equal v{version}", errors)
    if errors:
        raise SystemExit("release version invariant failed:\n- " + "\n- ".join(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check")
    check.add_argument("--tag")
    set_parser = subparsers.add_parser("set")
    set_parser.add_argument("version")
    args = parser.parse_args()
    if args.command == "set":
        set_version(args.version)
    else:
        version = read_version()
        check_version(version, args.tag)
        print(f"FREAK release version invariant: {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
