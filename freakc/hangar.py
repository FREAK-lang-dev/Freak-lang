"""
FREAK Hangar — Package Manager for the FREAK language.

Manages dependencies via hangar.toml manifests and a hangar_modules/
local cache.  Registry v1 uses GitHub releases.

Subcommands:
    hangar init               Create project skeleton + hangar.toml
    hangar install             Download all deps from hangar.toml
    hangar add <name> <repo>   Add a dependency
    hangar remove <name>       Remove a dependency
"""

from __future__ import annotations

import io
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, Optional
from urllib import request
from urllib.error import URLError


# ── hangar.toml I/O ─────────────────────────────────────────────────

def _read_manifest(project_dir: Path) -> Dict[str, Any]:
    """Read hangar.toml and return parsed dict."""
    manifest = project_dir / "hangar.toml"
    if not manifest.exists():
        raise FileNotFoundError(
            f"No hangar.toml found in {project_dir}. Run 'freak hangar init' first."
        )
    # Use tomllib (Python 3.11+) with fallback to simple parser
    try:
        import tomllib  # type: ignore[import]
    except ModuleNotFoundError:
        try:
            import tomli as tomllib  # type: ignore[import,no-redef]
        except ModuleNotFoundError:
            # Minimal fallback for environments without tomllib/tomli
            return _parse_toml_simple(manifest)
    with open(manifest, "rb") as f:
        return tomllib.load(f)


def _parse_toml_simple(path: Path) -> Dict[str, Any]:
    """Very basic TOML parser for hangar.toml (handles our subset)."""
    result: Dict[str, Any] = {}
    current_section: Optional[str] = None
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("["):
                current_section = line.strip("[] ")
                # Nested tables like [dependencies]
                parts = current_section.split(".")
                d = result
                for p in parts:
                    d = d.setdefault(p, {})
                continue
            if "=" in line:
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip()
                # Parse value
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                elif val.startswith("{"):
                    # Inline table: { git = "...", version = "..." }
                    val = _parse_inline_table(val)
                elif val in ("true", "false"):
                    val = val == "true"
                else:
                    try:
                        val = int(val)
                    except ValueError:
                        pass
                # Place into current section
                if current_section:
                    parts = current_section.split(".")
                    d = result
                    for p in parts:
                        d = d.setdefault(p, {})
                    d[key] = val
                else:
                    result[key] = val
    return result


def _parse_inline_table(s: str) -> Dict[str, str]:
    """Parse { key = "val", ... } inline TOML table."""
    s = s.strip("{ }")
    result = {}
    for pair in s.split(","):
        pair = pair.strip()
        if not pair:
            continue
        k, _, v = pair.partition("=")
        k = k.strip()
        v = v.strip().strip('"')
        result[k] = v
    return result


def _write_manifest(project_dir: Path, data: Dict[str, Any]) -> None:
    """Write hangar.toml from dict."""
    manifest = project_dir / "hangar.toml"
    lines = []
    # [project]
    if "project" in data:
        lines.append("[project]")
        for k, v in data["project"].items():
            lines.append(f'{k} = "{v}"')
        lines.append("")
    # [dependencies]
    if "dependencies" in data:
        lines.append("[dependencies]")
        for name, info in data["dependencies"].items():
            if isinstance(info, dict):
                parts = ", ".join(f'{k} = "{v}"' for k, v in info.items())
                lines.append(f"{name} = {{ {parts} }}")
            else:
                lines.append(f'{name} = "{info}"')
        lines.append("")
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── Commands ────────────────────────────────────────────────────────

def hangar_init(project_dir: Path) -> int:
    """Create a new FREAK project skeleton."""
    manifest = project_dir / "hangar.toml"
    if manifest.exists():
        print(f"  hangar.toml already exists in {project_dir}", file=sys.stderr)
        return 1

    project_name = project_dir.resolve().name

    data = {
        "project": {
            "name": project_name,
            "version": "0.1.0",
        },
        "dependencies": {},
    }
    _write_manifest(project_dir, data)

    # Create src/ directory + main.fk
    src = project_dir / "src"
    src.mkdir(exist_ok=True)
    main_fk = src / "main.fk"
    if not main_fk.exists():
        main_fk.write_text(
            f'-- {project_name} — a FREAK project\n'
            f'\n'
            f'say "Hello from {project_name}!"\n',
            encoding="utf-8",
        )

    # Create hangar_modules/ directory
    modules = project_dir / "hangar_modules"
    modules.mkdir(exist_ok=True)

    print(f"  Initialized FREAK project '{project_name}'")
    print(f"  Created hangar.toml")
    print(f"  Created src/main.fk")
    print(f"  Created hangar_modules/")
    return 0


def hangar_add(project_dir: Path, pkg_name: str, repo: str,
               version: str = "latest") -> int:
    """Add a dependency to hangar.toml."""
    data = _read_manifest(project_dir)
    deps = data.setdefault("dependencies", {})

    deps[pkg_name] = {"git": repo, "version": version}
    _write_manifest(project_dir, data)
    print(f"  Added {pkg_name} ({repo} @ {version})")

    # Also install it
    return _install_one(project_dir, pkg_name, deps[pkg_name])


def hangar_remove(project_dir: Path, pkg_name: str) -> int:
    """Remove a dependency from hangar.toml and delete cached files."""
    data = _read_manifest(project_dir)
    deps = data.get("dependencies", {})

    if pkg_name not in deps:
        print(f"  Package '{pkg_name}' is not in hangar.toml", file=sys.stderr)
        return 1

    del deps[pkg_name]
    _write_manifest(project_dir, data)

    # Remove cached files
    cache_dir = project_dir / "hangar_modules" / pkg_name
    if cache_dir.exists():
        shutil.rmtree(cache_dir)

    print(f"  Removed {pkg_name}")
    return 0


def hangar_install(project_dir: Path) -> int:
    """Install all dependencies from hangar.toml."""
    data = _read_manifest(project_dir)
    deps = data.get("dependencies", {})

    if not deps:
        print("  No dependencies to install.")
        return 0

    errors = 0
    for name, info in deps.items():
        if isinstance(info, str):
            info = {"git": info, "version": "latest"}
        result = _install_one(project_dir, name, info)
        if result != 0:
            errors += 1

    if errors:
        print(f"  {errors} package(s) failed to install.", file=sys.stderr)
        return 1

    print(f"  All {len(deps)} package(s) installed.")
    return 0


def _install_one(project_dir: Path, name: str, info: Dict[str, str]) -> int:
    """Download and extract a single package."""
    modules_dir = project_dir / "hangar_modules"
    modules_dir.mkdir(exist_ok=True)
    pkg_dir = modules_dir / name

    repo = info.get("git", "")
    version = info.get("version", "latest")

    if not repo:
        print(f"  No git repository specified for {name}", file=sys.stderr)
        return 1

    # Construct download URL
    if version == "latest":
        # Download default branch as zip
        url = f"https://github.com/{repo}/archive/refs/heads/main.zip"
    else:
        url = f"https://github.com/{repo}/archive/refs/tags/v{version}.zip"

    print(f"  Fetching {name} from {repo}...")

    try:
        req = request.Request(url, headers={"User-Agent": "FREAK-Hangar/0.1"})
        with request.urlopen(req, timeout=30) as resp:
            zip_data = resp.read()
    except URLError as e:
        # Check if it's a network issue or the repo doesn't exist
        print(f"  Could not fetch {name}: {e}", file=sys.stderr)
        print(f"  Creating stub module for offline development...", file=sys.stderr)
        _create_stub_module(pkg_dir, name)
        return 0
    except Exception as e:
        print(f"  Could not fetch {name}: {e}", file=sys.stderr)
        _create_stub_module(pkg_dir, name)
        return 0

    # Extract zip
    try:
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            # Find .fk files in the archive
            fk_files = [n for n in zf.namelist() if n.endswith(".fk")]
            if not fk_files:
                # Extract everything (might have src/ subfolder)
                fk_files = zf.namelist()

            if pkg_dir.exists():
                shutil.rmtree(pkg_dir)
            pkg_dir.mkdir(parents=True)

            for fk in fk_files:
                # Extract to flat structure, stripping top-level dir
                parts = fk.split("/")
                if len(parts) > 1:
                    # Skip the top-level directory name from GitHub
                    local_path = pkg_dir / "/".join(parts[1:])
                else:
                    local_path = pkg_dir / fk

                if fk.endswith("/"):
                    local_path.mkdir(parents=True, exist_ok=True)
                else:
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    local_path.write_bytes(zf.read(fk))

        print(f"  Installed {name} -> hangar_modules/{name}/")
        return 0
    except Exception as e:
        print(f"  Failed to extract {name}: {e}", file=sys.stderr)
        _create_stub_module(pkg_dir, name)
        return 0


def _create_stub_module(pkg_dir: Path, name: str) -> None:
    """Create a stub module for offline development."""
    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)
    pkg_dir.mkdir(parents=True)
    stub = pkg_dir / f"{name}.fk"
    stub.write_text(
        f"-- {name} (stub module — install with 'freak hangar install')\n"
        f"-- This stub was created because the package could not be downloaded.\n\n",
        encoding="utf-8",
    )
    print(f"  Created stub: hangar_modules/{name}/{name}.fk")


# ── Module resolution ───────────────────────────────────────────────

def resolve_module(module_name: str, search_dirs: list[Path]) -> Optional[Path]:
    """Resolve a module name to a .fk file path.

    Searches in order:
    1. Current directory (local modules)
    2. hangar_modules/<module_name>/
    3. hangar_modules/<module_name>/src/
    """
    for d in search_dirs:
        # Direct file
        p = d / f"{module_name}.fk"
        if p.exists():
            return p
        # Directory module (mod.fk inside)
        p = d / module_name / f"{module_name}.fk"
        if p.exists():
            return p
        # src/ convention
        p = d / module_name / "src" / f"{module_name}.fk"
        if p.exists():
            return p
    return None


__all__ = [
    "hangar_init", "hangar_install", "hangar_add", "hangar_remove",
    "resolve_module",
]
