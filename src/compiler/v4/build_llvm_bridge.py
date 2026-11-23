"""Build the B2 LLVM bridge probe: FREAK driving LLVM in process.

The pinned LLVM comes from llvm.lock. Pass --llvm-root to use an extracted
release instead (FREAK_LLVM_ROOT works too); otherwise the archive is
downloaded into build/llvm/, its SHA-256 checked, and only the C API
headers, llvm-config and the static libraries the bridge links are kept.

The probe (tools/llvm_bridge_probe.fk) is compiled to C by V3.5 like every
other V4 tool (v35_seed.py) and linked with llvm_bridge/*.c and LLVM's
static libraries for the core, the pass pipeline and the x86-64 and AArch64
targets. No LLVM pointer crosses into FREAK; see BACKEND_DELIVERY.md.

    python src/compiler/v4/build_llvm_bridge.py -o build/llvm_bridge_probe
"""
from __future__ import annotations

import argparse
import hashlib
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path

import check_v4 as checks
import v35_seed

V4 = checks.V4_ROOT
LOCK = V4 / "llvm.lock"
BRIDGE = V4 / "llvm_bridge"
PROBE = V4 / "tools" / "llvm_bridge_probe.fk"
BRIDGE_SOURCES = (BRIDGE / "freak_llvm_bridge.c", BRIDGE / "freak_llvm_bridge_v35.c")
BRIDGE_HEADERS = (BRIDGE / "freak_llvm_bridge.h", BRIDGE / "freak_llvm_bridge_v35.h")
COMPONENTS = ("core", "analysis", "passes", "target", "x86", "aarch64")
ROOT_ENV = "FREAK_LLVM_ROOT"


def read_lock() -> tuple[str, dict[str, tuple[str, str]], str]:
    lines = LOCK.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "FREAK-V4-LLVM-LOCK-1":
        raise RuntimeError("llvm.lock has no FREAK-V4-LLVM-LOCK-1 header")
    version, url, assets = "", "", {}
    for line in lines[1:]:
        if not line.strip() or line.startswith("#"):
            continue
        fields = line.split()
        if fields[0] == "version" and len(fields) == 2:
            version = fields[1]
        elif fields[0] == "asset" and len(fields) == 4:
            assets[fields[1]] = (fields[2], fields[3])
        elif fields[0] == "url" and len(fields) == 2:
            url = fields[1]
        else:
            raise RuntimeError(f"llvm.lock: malformed line: {line}")
    if not version or not url or not assets:
        raise RuntimeError("llvm.lock needs version, url and at least one asset")
    for asset, _ in assets.values():
        if version not in asset:
            raise RuntimeError(f"llvm.lock: asset {asset} does not name version {version}")
    return version, assets, url


def host_key() -> str:
    machine = platform.machine().lower()
    arch = {"amd64": "x86_64", "x86_64": "x86_64", "arm64": "aarch64", "aarch64": "aarch64"}.get(machine, machine)
    system = {"linux": "linux", "darwin": "macos", "win32": "windows"}.get(sys.platform, sys.platform)
    return f"{system}-{arch}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def kept_member(name: str) -> bool:
    """Headers, llvm-config and static libraries; nothing else is extracted."""
    parts = name.split("/", 1)
    if len(parts) != 2:
        return False
    rest = parts[1]
    return (rest.startswith("include/llvm-c/") or rest.startswith("include/llvm/Config/")
            or rest in ("bin/llvm-config", "bin/llvm-config.exe")
            or (rest.startswith("lib/libLLVM") and rest.endswith(".a")))


def fetch_llvm(work: Path) -> Path:
    version, assets, url = read_lock()
    key = host_key()
    if key not in assets:
        raise RuntimeError(f"llvm.lock pins no LLVM {version} archive for {key}; pass --llvm-root")
    asset, expected = assets[key]
    root = work / f"llvm-{version}-{key}"
    stamp = root / ".freak-llvm-sha256"
    if stamp.is_file() and stamp.read_text(encoding="utf-8").strip() == expected:
        return root
    work.mkdir(parents=True, exist_ok=True)
    archive = work / asset
    if not archive.is_file() or sha256_file(archive) != expected:
        source = url.format(version=version, asset=asset)
        print(f"downloading {source}")
        partial = archive.with_suffix(archive.suffix + ".part")
        with urllib.request.urlopen(source, timeout=600) as response, partial.open("wb") as out:
            shutil.copyfileobj(response, out, 1 << 20)
        partial.replace(archive)
    actual = sha256_file(archive)
    if actual != expected:
        raise RuntimeError(f"LLVM archive checksum mismatch for {asset}: expected {expected}, got {actual}")
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    with tarfile.open(archive, "r:*") as tar:
        for member in tar:
            if not kept_member(member.name) or not (member.isfile() or member.isdir()):
                continue
            relative = Path(member.name.split("/", 1)[1])
            if relative.is_absolute() or ".." in relative.parts:
                raise RuntimeError(f"unsafe path in LLVM archive: {member.name}")
            target = root / relative
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with tar.extractfile(member) as data, target.open("wb") as out:
                shutil.copyfileobj(data, out, 1 << 20)
            if relative.parts[0] == "bin":
                target.chmod(0o755)
    stamp.write_text(expected + "\n", encoding="utf-8")
    return root


def llvm_config(root: Path, *arguments: str) -> list[str]:
    tool = root / "bin" / ("llvm-config.exe" if sys.platform == "win32" else "llvm-config")
    result = subprocess.run([str(tool), *arguments], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"llvm-config {' '.join(arguments)} failed:\n{result.stderr}")
    return result.stdout.split()


def system_libraries() -> list[str]:
    """What LLVM's static libraries need from the system, by host."""
    if sys.platform == "darwin":
        return ["-lz", "-lc++"]
    if sys.platform == "win32":
        return ["-lpsapi", "-lshell32", "-lole32", "-luuid", "-ladvapi32", "-lntdll", "-lws2_32", "-lstdc++"]
    libraries = ["-lrt", "-ldl", "-lpthread", "-lm", "-lz", "-lstdc++"]
    # The release archive is built with zstd; link the shared one when no
    # development symlink is installed.
    for candidate in ("/usr/lib/x86_64-linux-gnu/libzstd.so", "/usr/lib/aarch64-linux-gnu/libzstd.so"):
        for path in (candidate, candidate + ".1"):
            if os.path.exists(path):
                return [*libraries, path]
    return [*libraries, "-lzstd"]


def check_llvm_version(root: Path) -> None:
    version, _, _ = read_lock()
    actual = llvm_config(root, "--version")
    if actual != [version]:
        raise RuntimeError(f"LLVM at {root} is {' '.join(actual)}, llvm.lock pins {version}")


def build(clang: str, root: Path, output: Path, opt: int) -> Path:
    check_llvm_version(root)
    include = llvm_config(root, "--includedir")[0]
    libraries = (*llvm_config(root, "--libfiles", *COMPONENTS, "--link-static"), *system_libraries())
    major = read_lock()[0].split(".")[0]
    built = v35_seed.build_tool(
        clang, PROBE, "llvm_bridge_probe", opt=opt,
        extra=("-include", str(BRIDGE / "freak_llvm_bridge_v35.h"), f"-I{BRIDGE}", f"-I{include}",
               f"-DFREAK_LB_LLVM_MAJOR={major}"),
        extra_sources=BRIDGE_SOURCES, key_files=(*BRIDGE_HEADERS, LOCK),
        libraries=libraries, source=PROBE.read_text(encoding="utf-8"),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    if built.resolve() != output.resolve():
        shutil.copy2(built, output)
    return output


# Exact probe report, in order. Layout lines are the targets' own answers.
PROBE_EXPECTED = [
    "lb-probe llvm-major={major}",
    "lb-probe refused=type ticket as value code -3",
    "lb-probe refused=load from a non-pointer code -3",
    "lb-probe refused=second terminator code -10",
    "lb-probe refused=mixed operand types code -3",
    "lb-probe refused=duplicate symbol code -4",
    "lb-probe refused=forged ticket code -2",
    "lb-probe refused=call argument type code -3",
    "lb-probe refused=call with too few arguments code -4",
    "lb-probe refused=unknown attribute code -4",
    "lb-probe verify=0",
    "lb-probe optimize=0",
    "lb-probe object=0",
    "lb-probe ir=0",
    "lb-probe refused=released session code -1",
    "lb-probe refused=unterminated block code -7",
    "lb-probe refused=unknown triple code -6",
    "lb-probe layout x86_64-unknown-linux-gnu=size=16 align=8 offset1=8 ptr=8 i128-align=16",
    "lb-probe layout aarch64-unknown-linux-gnu=size=16 align=8 offset1=8 ptr=8 i128-align=16",
    "lb-probe layout aarch64-apple-darwin=size=16 align=8 offset1=8 ptr=8 i128-align=16",
    "lb-probe layout x86_64-w64-windows-gnu=size=16 align=8 offset1=8 ptr=8 i128-align=16",
    "lb-probe live-sessions=0",
    "lb-probe failures=0",
]

# Calls every function the probe built; the object is linked into this.
DRIVER_C = r"""
#include <stdint.h>
#include <stdio.h>
int64_t probe_sum(int64_t);
int64_t probe_max(int64_t, int64_t);
int64_t probe_call(int64_t);
double probe_scale(int64_t);
int64_t probe_pair_sum(const int64_t*);
int64_t probe_hello(void);
int main(void) {
    int64_t pair[2] = { 40, 2 };
    printf("sum %lld %lld %lld\n", (long long)probe_sum(10), (long long)probe_sum(1), (long long)probe_sum(-5));
    printf("max %lld %lld\n", (long long)probe_max(-3, 4), (long long)probe_max(9, 2));
    printf("call %lld\n", (long long)probe_call(4));
    printf("scale %.2f\n", probe_scale(3));
    printf("pair %lld\n", (long long)probe_pair_sum(pair));
    fflush(stdout);
    printf("hello %lld\n", (long long)probe_hello());
    return 0;
}
"""
DRIVER_EXPECTED = "sum 55 1 1\nmax 4 9\ncall 14\nscale 7.50\npair 42\nhello from the LLVM bridge\nhello 7\n"


def check(clang: str, probe: Path) -> None:
    """Run the probe at O0..O3 on the host and link and run its object."""
    from build_v4 import host_target

    major = read_lock()[0].split(".")[0]
    expected = [line.format(major=major) for line in PROBE_EXPECTED]
    triple = host_target()
    work = checks.RUNTIME_BUILD_ROOT / "llvm_bridge"
    work.mkdir(parents=True, exist_ok=True)
    driver = work / "driver.c"
    driver.write_text(DRIVER_C, encoding="utf-8")
    for level in range(4):
        out = work / f"O{level}"
        if out.exists():
            shutil.rmtree(out)
        out.mkdir()
        ran = checks.run_with_heartbeat([str(probe), str(out), triple, str(level)],
                                        label=f"LLVM bridge probe O{level}", timeout_seconds=120, memory_limit_mb=1024)
        lines = ran.stdout.splitlines()
        if ran.returncode != 0 or lines != expected or ran.stderr:
            raise RuntimeError(f"LLVM bridge probe O{level} report differs:\n{ran.stdout}{ran.stderr}")
        executable = out / ("driver.exe" if sys.platform == "win32" else "driver")
        linked = checks.run_with_heartbeat([clang, "-w", str(driver), str(out / "probe.o"), "-o", str(executable)],
                                           label=f"LLVM bridge object link O{level}", timeout_seconds=120, memory_limit_mb=512)
        if linked.returncode != 0:
            raise RuntimeError(f"LLVM bridge object did not link at O{level}:\n{linked.stdout}{linked.stderr}")
        executed = checks.run_with_heartbeat([str(executable)], label=f"LLVM bridge object run O{level}",
                                             timeout_seconds=30, memory_limit_mb=128)
        if executed.returncode != 0 or executed.stdout.replace("\r\n", "\n") != DRIVER_EXPECTED:
            raise RuntimeError(f"LLVM bridge object misbehaved at O{level}:\n{executed.stdout}{executed.stderr}")
        module = (out / "probe.ll").read_text(encoding="utf-8")
        if f'target triple = "{triple}"' not in module or "@probe_sum" not in module:
            raise RuntimeError(f"LLVM bridge module text at O{level} lacks its triple or functions")
        print(f"LLVM bridge: O{level} probe report exact, object links and runs on {triple}")


def resolve_root(argument: Path | None) -> Path:
    if argument is not None:
        return argument.resolve()
    if os.environ.get(ROOT_ENV):
        return Path(os.environ[ROOT_ENV]).resolve()
    return fetch_llvm(checks.ROOT / "build" / "llvm")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-o", "--output", type=Path, default=checks.ROOT / "build" / "llvm_bridge_probe")
    parser.add_argument("--llvm-root", type=Path, default=None,
                        help=f"an extracted LLVM release matching llvm.lock (or set {ROOT_ENV})")
    parser.add_argument("--opt", type=int, choices=(0, 1, 2, 3), default=0,
                        help="C optimization level for the probe (default: 0)")
    parser.add_argument("--fetch-only", action="store_true", help="download and trim LLVM, then stop")
    parser.add_argument("--check", action="store_true",
                        help="also run the probe at O0..O3 and link and run its object (the B2 gate)")
    args = parser.parse_args()
    clang = shutil.which("clang")
    if clang is None:
        parser.error("clang is required")
    try:
        root = resolve_root(args.llvm_root)
        if args.fetch_only:
            print(f"llvm {root}")
            return 0
        build(clang, root, args.output, args.opt)
        if args.check:
            check(clang, args.output)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"built {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
