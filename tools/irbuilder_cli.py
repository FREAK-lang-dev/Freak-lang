#!/usr/bin/env python3
"""Fetch the pinned LLVM and link the release `freak` with the IRBuilder.

The V3.5 LLVM backend lowers programs in process through
src/compiler/v3/llvm_builder/ib_bridge.c. Release and CI builds of the CLI
link that bridge against the one LLVM release pinned in
src/compiler/v4/llvm.lock (shared with the V4 backend):

  python3 tools/irbuilder_cli.py fetch --dest .llvm      # download + verify + trim
  python3 tools/irbuilder_cli.py link --llvm .llvm \\
      --cli-c build/freakc_cli.fk.c --out build/freak    # compile + link

Linux and macOS link the LLVM static libraries into freak (no runtime LLVM
dependency; zstd is replaced by zstd_unavailable.c). On Windows freak.exe
binds the official LLVM-C.dll at run time (LoadLibrary), so the DLL ships
as runtime/LLVM-C.dll and a missing DLL only means the text IR path.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "src/compiler/v4/llvm.lock"
BRIDGE = ROOT / "src/compiler/v3/llvm_builder/ib_bridge.c"
ZSTD_STUBS = ROOT / "src/compiler/v3/llvm_builder/zstd_unavailable.c"
RUNTIME = ROOT / "freakc/runtime"
COMPONENTS = ["core", "analysis", "passes", "target", "x86", "aarch64"]


def host_key() -> str:
    machine = platform.machine().lower()
    arch = "aarch64" if machine in ("arm64", "aarch64") else "x86_64"
    if sys.platform.startswith("linux"):
        return f"linux-{arch}"
    if sys.platform == "darwin":
        return f"macos-{arch}"
    if sys.platform in ("win32", "cygwin", "msys"):
        return f"windows-{arch}"
    raise SystemExit(f"irbuilder_cli: unsupported host {sys.platform}/{machine}")


def read_lock() -> tuple[str, dict[str, tuple[str, str]], str]:
    lines = LOCK.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "FREAK-V4-LLVM-LOCK-1":
        raise SystemExit(f"irbuilder_cli: {LOCK} is not a FREAK-V4-LLVM-LOCK-1 file")
    version, url, assets = "", "", {}
    for raw in lines[1:]:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if parts[0] == "version" and len(parts) == 2:
            version = parts[1]
        elif parts[0] == "asset" and len(parts) == 4:
            assets[parts[1]] = (parts[2], parts[3])
        elif parts[0] == "url" and len(parts) == 2:
            url = parts[1]
        else:
            raise SystemExit(f"irbuilder_cli: unreadable lock line: {raw}")
    if not version or not url:
        raise SystemExit("irbuilder_cli: lock needs version and url lines")
    return version, assets, url


def wanted(member: str, windows: bool, macos: bool = False) -> str | None:
    """Map an archive member to its path under the trimmed root, or None."""
    parts = member.split("/", 1)
    if len(parts) != 2:
        return None
    rel = parts[1]
    if rel.startswith("include/llvm-c/") or rel.startswith("include/llvm/Config/"):
        return rel
    if windows:
        if rel == "bin/LLVM-C.dll":
            return rel
        return None
    if rel == "bin/llvm-config":
        return rel
    if macos and rel == "lib/libLTO.dylib":
        # The macOS release libraries are LTO bitcode; Apple's ld can only
        # read them through the matching libLTO.
        return rel
    if rel.startswith("lib/libLLVM") and rel.endswith(".a"):
        return rel
    return None


def _check_owned_dest(dest: Path, stamp: Path) -> None:
    """Only ever replace a directory this tool created (or an empty one)."""
    resolved = dest.resolve()
    protected = {Path(resolved.anchor), Path.home().resolve(), ROOT}
    if resolved in protected or ROOT.is_relative_to(resolved):
        raise SystemExit(f"irbuilder_cli: refusing to replace {dest}: it is the checkout, home or a root directory")
    if not resolved.is_dir():
        raise SystemExit(f"irbuilder_cli: refusing to replace {dest}: it is not a directory")
    if not stamp.is_file() and any(resolved.iterdir()):
        raise SystemExit(f"irbuilder_cli: refusing to replace {dest}: it is not empty and has no .freak-llvm stamp "
                         "(pick a new or empty --dest)")


def fetch(dest: Path, key: str) -> None:
    version, assets, url = read_lock()
    if key not in assets:
        raise SystemExit(f"irbuilder_cli: {LOCK.name} has no asset for {key}")
    name, digest = assets[key]
    windows = key.startswith("windows-")
    if not windows and key != host_key():
        # Trimming runs the asset's own llvm-config, which needs this host.
        raise SystemExit(f"irbuilder_cli: cannot prepare {key} on a {host_key()} host "
                         "(trimming runs its llvm-config); fetch it on a matching host")
    stamp = dest / ".freak-llvm"
    expected_stamp = f"{version} {key} {digest} layout-2\n"
    if stamp.exists() and stamp.read_text(encoding="utf-8") == expected_stamp:
        print(f"LLVM {version} ({key}) already at {dest}")
        return
    if dest.exists():
        _check_owned_dest(dest, stamp)
    link = url.replace("{version}", version).replace("{asset}", name)
    print(f"fetching {link}", flush=True)
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Build the tree in a sibling staging directory and only swap it in once it
    # is complete and stamped, so a failed fetch leaves the old tree (or
    # nothing) behind, never a half-extracted unstamped one.
    staging = Path(tempfile.mkdtemp(prefix=f".{dest.name}.staging-", dir=dest.parent))
    try:
        with tempfile.TemporaryDirectory() as scratch:
            archive = Path(scratch) / name
            sha = hashlib.sha256()
            with urllib.request.urlopen(link) as response, open(archive, "wb") as out:
                while True:
                    block = response.read(1 << 20)
                    if not block:
                        break
                    sha.update(block)
                    out.write(block)
            if sha.hexdigest() != digest:
                raise SystemExit(f"irbuilder_cli: checksum mismatch for {name}: {sha.hexdigest()} != {digest}")
            with tarfile.open(archive, "r:*") as tar:
                for member in tar:
                    if not member.isfile():
                        continue
                    rel = wanted(member.name, windows, key.startswith("macos-"))
                    if rel is None:
                        continue
                    target = staging / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with tar.extractfile(member) as src, open(target, "wb") as out:
                        shutil.copyfileobj(src, out)
                    if rel.startswith("bin/") and not windows:
                        target.chmod(0o755)
        if not windows:
            # Keep only the static libraries the IRBuilder components need.
            config = staging / "bin/llvm-config"
            names = subprocess.run([str(config), "--link-static", "--libnames", *COMPONENTS],
                                   check=True, capture_output=True, text=True).stdout.split()
            keep = set(names)
            for lib in (staging / "lib").glob("libLLVM*.a"):
                if lib.name not in keep:
                    lib.unlink()
        (staging / ".freak-llvm").write_text(expected_stamp, encoding="utf-8")
        staging.chmod(0o755)  # mkdtemp creates it 0700
        # Publish by renames only: move the old tree aside, move staging in,
        # and put the old tree back if the second rename fails.
        backup = None
        if dest.exists():
            backup = dest.with_name(f".{dest.name}.old-{staging.name.rsplit('-', 1)[-1]}")
            dest.rename(backup)
        try:
            staging.rename(dest)
        except BaseException:
            if backup is not None:
                backup.rename(dest)
            raise
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    if backup is not None:
        shutil.rmtree(backup, ignore_errors=True)
    print(f"LLVM {version} ({key}) ready at {dest}")


TARGET_INITIALIZERS = [
    f"LLVMInitialize{target}{part}"
    for target in ("X86", "AArch64")
    for part in ("TargetInfo", "Target", "TargetMC", "AsmPrinter")
]


def write_dynamic_header(include: Path, out: Path) -> None:
    """Windows: bind every LLVM C function the bridge calls through
    LoadLibrary/GetProcAddress, so freak.exe starts without LLVM-C.dll and
    only the IRBuilder needs it (runtime/LLVM-C.dll in the install)."""
    declared = set(TARGET_INITIALIZERS)
    for header in (include / "llvm-c").rglob("*.h"):
        declared.update(re.findall(r"\b(LLVM[A-Z][A-Za-z0-9]*)\s*\((?!\s*\*)", header.read_text(encoding="utf-8", errors="replace")))
    used = set(re.findall(r"\b(LLVM[A-Z][A-Za-z0-9]*)\b", BRIDGE.read_text(encoding="utf-8")))
    names = sorted(used & declared)
    lines = [
        "/* Generated by tools/irbuilder_cli.py: LLVM-C.dll bindings for ib_bridge.c. */",
        "#include <windows.h>",
        "",
    ]
    lines += [f"static __typeof__({n}) *freak_ib2_p_{n};" for n in names]
    lines += [
        "",
        "static int freak_ib2_dynamic_bind(const char *utf8_path) {",
        "    wchar_t wide[4096];",
        "    if (!MultiByteToWideChar(CP_UTF8, 0, utf8_path, -1, wide, 4096)) return 0;",
        "    HMODULE library = LoadLibraryExW(wide, NULL, LOAD_WITH_ALTERED_SEARCH_PATH);",
        "    if (!library) return 0;",
    ]
    for n in names:
        lines.append(f"    freak_ib2_p_{n} = (__typeof__({n}) *)(void *)GetProcAddress(library, \"{n}\");")
        lines.append(f"    if (!freak_ib2_p_{n}) return 0;")
    lines += ["    return 1;", "}", ""]
    lines += [f"#define {n} (*freak_ib2_p_{n})" for n in names]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(command: list[str]) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, check=True)


def link(llvm: Path, cli_c: Path, out: Path, cc: str, extra: list[str]) -> None:
    key = host_key()
    windows = key.startswith("windows-")
    include = llvm / "include"
    if not (include / "llvm-c/Core.h").exists():
        raise SystemExit(f"irbuilder_cli: {llvm} has no LLVM headers; run fetch first")
    work = Path(tempfile.mkdtemp(prefix="freak-ib-link-"))
    try:
        flags = ["-O2", "-w", "-D_CRT_SECURE_NO_WARNINGS", f"-I{RUNTIME}"]
        bridge_flags = ["-DFREAK_IB2_LINKED", f"-I{include}"]
        if windows:
            write_dynamic_header(include, work / "ib_llvm_dynamic.h")
            bridge_flags += ["-DFREAK_IB2_DYNAMIC", f"-I{work}"]
        objects = []
        for source, defines, name in (
            (cli_c, [], "cli"),
            (RUNTIME / "freak_runtime.c", ["-DFREAK_IB2_LINKED"], "runtime"),
            (BRIDGE, bridge_flags, "ib_bridge"),
        ):
            obj = work / f"{name}.o"
            run([cc, "-c", *flags, *defines, str(source), "-o", str(obj)])
            objects.append(str(obj))
        if windows:
            run([cc, "-o", str(out), *objects, "-lws2_32", *extra])
            return
        zstd = work / "zstd_unavailable.o"
        run([cc, "-c", "-O2", str(ZSTD_STUBS), "-o", str(zstd)])
        objects.append(str(zstd))
        config = str(llvm / "bin/llvm-config")
        libs = subprocess.run([config, "--link-static", "--libs", *COMPONENTS],
                              check=True, capture_output=True, text=True).stdout.split()
        # LLVM is C++: link through the matching C++ driver.
        cxx = cc
        driver = []
        if Path(cc).name == "clang":
            cxx = str(Path(cc).with_name("clang++")) if os.sep in cc else "clang++"
        elif re.fullmatch(r"clang-[0-9][0-9.]*", Path(cc).name):
            # Version-suffixed drivers (clang-20) have no fixed ++ sibling name.
            driver = ["--driver-mode=g++"]
        command = [cxx, *driver, "-o", str(out), *objects, f"-L{llvm / 'lib'}", *libs]
        if key.startswith("linux-"):
            command += ["-lz", "-lpthread", "-ldl", "-lrt", "-lm",
                        "-static-libstdc++", "-static-libgcc", "-Wl,--gc-sections", "-s"]
        else:
            lto_library = llvm / "lib/libLTO.dylib"
            if not lto_library.is_file():
                raise SystemExit(f"irbuilder_cli: {lto_library} is missing; run fetch again")
            command += ["-lz", "-lc++", "-Wl,-dead_strip", f"-Wl,-lto_library,{lto_library}"]
        run(command + extra)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    fetch_parser = sub.add_parser("fetch", help="download, verify and trim the pinned LLVM")
    fetch_parser.add_argument("--dest", required=True)
    fetch_parser.add_argument("--platform", default="", help="lock asset key (default: this host)")
    link_parser = sub.add_parser("link", help="compile the CLI C and link it with the IRBuilder")
    link_parser.add_argument("--llvm", required=True)
    link_parser.add_argument("--cli-c", required=True)
    link_parser.add_argument("--out", required=True)
    link_parser.add_argument("--cc", default=os.environ.get("FREAK_CLANG", "clang"))
    link_parser.add_argument("extra", nargs="*", help="extra linker arguments")
    args = parser.parse_args()
    if args.command == "fetch":
        fetch(Path(args.dest).resolve(), args.platform or host_key())
    else:
        link(Path(args.llvm).resolve(), Path(args.cli_c).resolve(), Path(args.out).resolve(), args.cc, args.extra)
    return 0


if __name__ == "__main__":
    sys.exit(main())
