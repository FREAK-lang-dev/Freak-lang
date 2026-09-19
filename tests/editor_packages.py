#!/usr/bin/env python3
"""Validate the installable artifacts, not just their source manifests."""
import argparse
import json
import subprocess
import tomllib
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify(artifacts: Path) -> None:
    version = (ROOT / "VERSION").read_text().strip()
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    with zipfile.ZipFile(artifacts / f"freak-vscode-{version}.vsix") as archive:
        names = set(archive.namelist())
        manifest = json.loads(archive.read("extension/package.json"))
        assert manifest["version"] == version
        xml = ET.fromstring(archive.read("extension.vsixmanifest"))
        identity = xml.find("{*}Metadata/{*}Identity")
        assert identity is not None and identity.attrib["Version"] == version
        assert identity.attrib["Publisher"] == manifest["publisher"]
        for item in manifest["contributes"]["languages"]:
            assert ".fk" in item["extensions"]
            for filename in [item["configuration"], *item["icon"].values()]:
                assert "extension/" + filename.removeprefix("./") in names
        for kind in ("grammars", "snippets"):
            for item in manifest["contributes"][kind]:
                assert "extension/" + item["path"].removeprefix("./") in names
        snippets = json.loads(archive.read("extension/snippets/freak.json"))
        assert "extension/LICENSE.txt" in names
        assert not any("node_modules/" in name for name in names)

    with zipfile.ZipFile(artifacts / f"freak-zed-{version}.zip") as archive:
        manifest = tomllib.loads(archive.read("freak-zed/extension.toml").decode())
        assert manifest["id"] == "freak-lang" and manifest["schema_version"] == 1
        assert manifest["version"] == version
        grammar = manifest["grammars"]["freak"]
        assert grammar["rev"] == sha
        assert grammar["repository"] == "https://github.com/FREAK-lang-dev/Freak-lang"
        assert (ROOT / grammar["path"] / "src/parser.c").is_file()
        language = tomllib.loads(archive.read("freak-zed/languages/freak/config.toml").decode())
        assert language["grammar"] == "freak" and "fk" in language["path_suffixes"]
        assert manifest["snippets"] == ["snippets/freak.json"]
        assert snippets == json.loads(archive.read("freak-zed/snippets/freak.json"))
        for name in ("highlights", "outline", "brackets", "indents"):
            assert archive.read(f"freak-zed/languages/freak/{name}.scm")
        assert archive.read("freak-zed/LICENSE")

    for editor in ("vscode", "zed"):
        source = ROOT / f"editors/{editor}/freak-lang/snippets/freak.json"
        assert snippets == json.loads(source.read_text(encoding="utf-8"))
    assert {item["prefix"] for item in snippets.values()} == {
        "task", "pilot", "fixed", "if", "repeat", "foreach", "shape", "say", "giveback",
    }
    print(f"Editor artifact contracts passed for {version} @ {sha}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    verify(parser.parse_args().artifacts)
