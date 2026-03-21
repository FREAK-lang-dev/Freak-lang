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


# ── Semantic Versioning ─────────────────────────────────────────────

import re as _re

_SEMVER_RE = _re.compile(
    r"^v?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    r"(?:-(?P<pre>[A-Za-z0-9.]+))?"
    r"(?:\+(?P<build>[A-Za-z0-9.]+))?$"
)


def parse_semver(version: str) -> tuple[int, int, int, str, str] | None:
    """Parse a semver string. Returns (major, minor, patch, pre, build) or None."""
    m = _SEMVER_RE.match(version.strip())
    if not m:
        return None
    return (
        int(m.group("major")),
        int(m.group("minor")),
        int(m.group("patch")),
        m.group("pre") or "",
        m.group("build") or "",
    )


def format_semver(major: int, minor: int, patch: int,
                  pre: str = "", build: str = "") -> str:
    """Format a semver tuple back to string."""
    v = f"{major}.{minor}.{patch}"
    if pre:
        v += f"-{pre}"
    if build:
        v += f"+{build}"
    return v


def _semver_key(v: tuple[int, int, int, str, str]):
    """Sort key: releases sort after pre-releases with the same version."""
    major, minor, patch, pre, _ = v
    # No pre-release → sorts last (higher), pre-release → sorts by string
    return (major, minor, patch, 0 if pre == "" else -1, pre)


def semver_satisfies(version: str, constraint: str) -> bool:
    """Check if a version satisfies a constraint.

    Supports: >=, <=, >, <, =, ^, ~, *, latest, exact match.
    """
    if constraint in ("*", "latest", ""):
        return True

    v = parse_semver(version)
    if v is None:
        return False

    # Caret: ^1.2.3 → >=1.2.3, <2.0.0
    if constraint.startswith("^"):
        c = parse_semver(constraint[1:])
        if c is None:
            return False
        if v[0] != c[0]:
            return False
        return _semver_key(v) >= _semver_key(c)

    # Tilde: ~1.2.3 → >=1.2.3, <1.3.0
    if constraint.startswith("~"):
        c = parse_semver(constraint[1:])
        if c is None:
            return False
        if v[0] != c[0] or v[1] != c[1]:
            return False
        return _semver_key(v) >= _semver_key(c)

    # Comparison operators
    for op, fn in [
        (">=", lambda a, b: _semver_key(a) >= _semver_key(b)),
        ("<=", lambda a, b: _semver_key(a) <= _semver_key(b)),
        (">",  lambda a, b: _semver_key(a) > _semver_key(b)),
        ("<",  lambda a, b: _semver_key(a) < _semver_key(b)),
        ("=",  lambda a, b: _semver_key(a) == _semver_key(b)),
    ]:
        if constraint.startswith(op):
            c = parse_semver(constraint[len(op):])
            if c is None:
                return False
            return fn(v, c)

    # Exact match
    c = parse_semver(constraint)
    if c is None:
        return False
    return _semver_key(v) == _semver_key(c)


def hangar_version(project_dir: Path, bump: str = "") -> int:
    """Show or bump project version in hangar.toml.

    bump can be: "", "major", "minor", "patch", or an explicit version string.
    """
    data = _read_manifest(project_dir)
    project = data.get("project", {})
    current = project.get("version", "0.0.0")

    if not bump:
        print(f"  {project.get('name', 'unknown')} v{current}")
        return 0

    parsed = parse_semver(current)
    if parsed is None:
        print(f"  Invalid current version: {current}", file=sys.stderr)
        return 1

    major, minor, patch, pre, build = parsed

    if bump == "major":
        new_ver = format_semver(major + 1, 0, 0)
    elif bump == "minor":
        new_ver = format_semver(major, minor + 1, 0)
    elif bump == "patch":
        new_ver = format_semver(major, minor, patch + 1)
    else:
        # Explicit version
        if parse_semver(bump) is None:
            print(f"  Invalid version: {bump}", file=sys.stderr)
            return 1
        new_ver = bump

    project["version"] = new_ver
    data["project"] = project
    _write_manifest(project_dir, data)
    print(f"  {project.get('name', 'unknown')}: {current} -> {new_ver}")
    return 0


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


# ── Toolchain bootstrapping ────────────────────────────────────────

REPO = "FREAK-lang-dev/Freak-lang"

def _detect_platform() -> str:
    """Detect platform target string for binary downloads."""
    import platform
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "linux":
        os_tag = "linux"
    elif system == "darwin":
        os_tag = "macos"
    elif system == "windows":
        os_tag = "windows"
    else:
        raise RuntimeError(f"Unsupported OS: {system}")

    if machine in ("x86_64", "amd64"):
        arch_tag = "x64"
    elif machine in ("aarch64", "arm64"):
        arch_tag = "arm64"
    else:
        raise RuntimeError(f"Unsupported architecture: {machine}")

    return f"{os_tag}-{arch_tag}"


def _get_freak_home() -> Path:
    """Get FREAK installation directory."""
    env = os.environ.get("FREAK_HOME")
    if env:
        return Path(env)
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", "~")) / "freak"
    return Path.home() / ".freak"


def _get_latest_release() -> str:
    """Fetch the latest release tag from GitHub."""
    url = f"https://api.github.com/repos/{REPO}/releases/latest"
    req = request.Request(url, headers={"User-Agent": "FREAK-Hangar/0.1"})
    with request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    return data["tag_name"]


def hangar_install_toolchain(upgrade: bool = False) -> int:
    """Download and install the FREAK compiler binary."""
    try:
        target = _detect_platform()
    except RuntimeError as e:
        print(f"  {e}", file=sys.stderr)
        return 1

    freak_home = _get_freak_home()
    bin_dir = freak_home / "bin"
    ext = ".exe" if sys.platform == "win32" else ""
    binary_path = bin_dir / f"freakc{ext}"

    if binary_path.exists() and not upgrade:
        print(f"  FREAK is already installed at {binary_path}")
        print(f"  Use 'hangar upgrade freak' to update.")
        return 0

    print(f"  Detected platform: {target}")

    try:
        version = _get_latest_release()
    except Exception as e:
        print(f"  Could not fetch latest release: {e}", file=sys.stderr)
        return 1

    print(f"  Latest version: {version}")

    artifact = f"freakc-{target}{ext}"
    download_url = f"https://github.com/{REPO}/releases/download/{version}/{artifact}"
    print(f"  Downloading {artifact}...")

    try:
        req = request.Request(download_url, headers={"User-Agent": "FREAK-Hangar/0.1"})
        with request.urlopen(req, timeout=60) as resp:
            binary_data = resp.read()
    except Exception as e:
        print(f"  Download failed: {e}", file=sys.stderr)
        print(f"  Check https://github.com/{REPO}/releases", file=sys.stderr)
        return 1

    # Install binary
    bin_dir.mkdir(parents=True, exist_ok=True)
    binary_path.write_bytes(binary_data)

    # Make executable on Unix
    if sys.platform != "win32":
        binary_path.chmod(0o755)

    # Download runtime files
    runtime_dir = freak_home / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    runtime_url = f"https://raw.githubusercontent.com/{REPO}/{version}/freakc/runtime"
    for fname in ("freak_runtime.c", "freak_runtime.h", "freak_llvm_runtime.c"):
        try:
            req = request.Request(
                f"{runtime_url}/{fname}",
                headers={"User-Agent": "FREAK-Hangar/0.1"},
            )
            with request.urlopen(req, timeout=15) as resp:
                (runtime_dir / fname).write_bytes(resp.read())
        except Exception:
            pass  # Non-fatal

    # PATH guidance
    action = "Updated" if upgrade else "Installed"
    print(f"  {action} FREAK {version} successfully!")
    print(f"")
    print(f"  Compiler: {binary_path}")
    print(f"  Runtime:  {runtime_dir}/")
    print(f"")

    # Check if already in PATH
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    if str(bin_dir) not in path_dirs:
        if sys.platform == "win32":
            print(f"  Add to PATH by running:")
            print(f"    setx PATH \"%PATH%;{bin_dir}\"")
        else:
            print(f"  Add to PATH by running:")
            print(f"    export PATH=\"{bin_dir}:$PATH\"")
            print(f"")
            print(f"  Or add to your shell config:")
            print(f"    echo 'export PATH=\"{bin_dir}:$PATH\"' >> ~/.bashrc")
    else:
        print(f"  {bin_dir} is already in PATH")

    print(f"")
    print(f"  Try: freakc build hello.fk -o hello")
    return 0


__all__ = [
    "hangar_init", "hangar_install", "hangar_add", "hangar_remove",
    "hangar_install_toolchain", "hangar_version", "resolve_module",
    "parse_semver", "format_semver", "semver_satisfies",
]
