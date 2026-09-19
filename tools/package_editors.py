#!/usr/bin/env python3
"""Build release editor assets without modifying their source manifests.

Requires Node.js and `npm ci --prefix editors`. Versions come from VERSION;
Zed's grammar is pinned to the checkout commit, never a moving branch.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from release_version import ROOT, read_version


def copy_files(source: Path, destination: Path, names: list[str]) -> None:
    for name in names:
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, target)


def package(output: Path) -> list[Path]:
    version = read_version()
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise SystemExit("Expected an immutable Git SHA for the Zed grammar")
    vsce = ROOT / "editors/node_modules/@vscode/vsce/vsce"
    if not vsce.is_file():
        raise SystemExit("Run npm ci --prefix editors before packaging")
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    assets = [output / f"freak-vscode-{version}.vsix",
              output / f"freak-zed-{version}.zip"]
    with tempfile.TemporaryDirectory(prefix="freak-editors-") as temporary:
        stage = Path(temporary)
        vscode = stage / "vscode"
        copy_files(ROOT / "editors/vscode/freak-lang", vscode, [
            "package.json", "README.md", "language-configuration.json",
            "syntaxes/freak.tmLanguage.json", "icons/freak-file.svg",
            "snippets/freak.json",
        ])
        shutil.copyfile(ROOT / "LICENSE", vscode / "LICENSE")
        manifest = json.loads((vscode / "package.json").read_text(encoding="utf-8"))
        manifest["version"] = version
        (vscode / "package.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        subprocess.run([
            "node", str(vsce), "package", "--no-dependencies",
            "--out", str(assets[0]),
        ], cwd=vscode, check=True)

        zed = stage / "freak-zed"
        copy_files(ROOT / "editors/zed/freak-lang", zed, [
            "extension.toml", "README.md", "snippets/freak.json",
            "languages/freak/config.toml", "languages/freak/highlights.scm",
            "languages/freak/brackets.scm", "languages/freak/indents.scm",
            "languages/freak/outline.scm",
        ])
        shutil.copyfile(ROOT / "LICENSE", zed / "LICENSE")
        manifest_path = zed / "extension.toml"
        manifest_text = manifest_path.read_text(encoding="utf-8")
        manifest_text = re.sub(r'^version = ".*"$', f'version = "{version}"', manifest_text, flags=re.M)
        manifest_text = re.sub(r'^rev = ".*"$', f'rev = "{revision}"', manifest_text, flags=re.M)
        manifest_path.write_text(manifest_text, encoding="utf-8", newline="\n")
        with zipfile.ZipFile(assets[1], "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(zed.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(stage).as_posix())
    return assets


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for asset in package(args.output):
        print(asset)


if __name__ == "__main__":
    main()
