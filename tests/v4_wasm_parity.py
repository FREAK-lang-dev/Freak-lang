"""V4 wasm lane: every runnable V4 example must behave identically as a
native program and as a wasm32-unknown-wasip1 module run under Node's WASI.

For each src/compiler/v4/examples/*.fk with a native build, the lane builds
the host binary and the .wasm with the same V4 compiler, runs both, and
compares exit status, stdout and stderr byte for byte. A generated program
adds number formatting edge cases (the platform layer's own %g). Examples the
host cannot build are reported and skipped; an example that builds natively
but not as wasm, or that behaves differently, fails the lane.

Needs clang 18+ with wasm-ld (lld) and Node 20+.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V4_ROOT = ROOT / "src" / "compiler" / "v4"
sys.path.insert(0, str(V4_ROOT))
sys.path.insert(0, str(ROOT))

import build_v4  # noqa: E402
import check_v4  # noqa: E402
import wasm_target  # noqa: E402

RUNNER = V4_ROOT / "wasm" / "run_wasi.mjs"
WASM = wasm_target.TRIPLE

# Examples whose wasm build must stop with this reason. Each is a boundary
# that is right on the four 64-bit targets and wrong on wasm32, so the lane
# pins the refusal instead of skipping the example.
WASM_FENCED = {
    # c_isize callbacks: ssize_t is 32-bit on wasm32 (Web lane W5).
    "indirect_calls": "pointer-sized C integers at this C boundary are not yet supported on wasm32-unknown-wasip1",
    # Declares runtime helpers that take int64_t as c_isize (ssize_t).
    "literal_say": "function signature mismatch: freak_llvm_process_args_count",
}

# Number formatting the platform layer must print exactly like glibc %g:
# rounding ties, exponent switches, denormals, huge values and signed zero.
NUM_FORMAT_SOURCE = """task main() -> int {
    say 0.1 + 0.2
    say 1.0 / 3.0
    say 2.0 / 3.0
    say 123456.5
    say 1234565.0
    say 1234575.0
    say 999999.5
    say 9999995.0
    say 0.000123456789
    say 0.0001
    say 0.00001
    say 100000.0
    say 1000000.0
    say 2.5
    say 0.5
    say 0.0 - 1.5
    pilot mut big = 1.0
    pilot mut i = 0
    repeat until i >= 308 {
        big = big * 10.0
        i += 1
    }
    say big
    say big * 1.7976
    pilot mut small = 1.0
    i = 0
    repeat until i >= 320 {
        small = small / 10.0
        i += 1
    }
    say small
    say small / 100000.0
    pilot mut third = 1.0
    i = 0
    repeat until i >= 40 {
        third = third / 3.0
        i += 1
    }
    say third
    say 0.0 - 0.0
    give back 0
}
"""


def run(command: list[str], timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(command, capture_output=True, timeout=timeout)


def node_command() -> list[str]:
    node = shutil.which("node")
    if node is None:
        raise SystemExit("the V4 wasm lane needs Node 20+ (node not found)")
    return [node, "--no-warnings", str(RUNNER)]


def build_case(compiler: Path, clang: str, source: Path, work: Path) -> dict:
    case = {"name": source.stem}
    native_bin = work / (source.stem + (".exe" if sys.platform == "win32" else ".native"))
    try:
        native_ll = work / (source.stem + ".native.ll")
        native_ll.write_text(build_v4.emit_module(compiler, source, build_v4.host_target()), encoding="utf-8")
    except RuntimeError as exc:
        case["skip"] = "no native build: " + str(exc).strip().splitlines()[-1][:160]
        return case
    linked = run(build_v4.native_link_command(clang, native_ll, native_bin), timeout=180)
    if linked.returncode != 0:
        case["skip"] = "native link failed"
        return case
    started = time.monotonic()
    try:
        wasm_ll = work / (source.stem + ".wasm.ll")
        wasm_ll.write_text(build_v4.emit_module(compiler, source, WASM), encoding="utf-8")
        wasm_target.link(clang, wasm_ll, work / (source.stem + ".wasm"), check_v4.RUNTIME_BUILD_ROOT / "wasm_runtime")
    except RuntimeError as exc:
        reason = WASM_FENCED.get(source.stem)
        if reason and reason in str(exc):
            case["fenced"] = reason
        else:
            case["fail"] = "wasm build failed: " + str(exc).strip()[-2000:]
        return case
    if source.stem in WASM_FENCED:
        case["fail"] = "wasm build passed a pinned fence: " + WASM_FENCED[source.stem]
        return case
    case["wasm_build_s"] = time.monotonic() - started
    case["native_bin"] = native_bin
    case["wasm"] = work / (source.stem + ".wasm")
    return case


def compare(case: dict, node: list[str]) -> dict:
    if "skip" in case or "fail" in case or "fenced" in case:
        return case
    native = run([str(case["native_bin"])])
    wasm = run([*node, str(case["wasm"])])
    case["native"] = (native.returncode, native.stdout, native.stderr)
    case["wasm_result"] = (wasm.returncode, wasm.stdout, wasm.stderr)
    case["bytes"] = case["wasm"].stat().st_size
    if case["native"] != case["wasm_result"]:
        diffs = []
        if native.returncode != wasm.returncode:
            diffs.append(f"exit native={native.returncode} wasm={wasm.returncode}")
        if native.stdout != wasm.stdout:
            diffs.append(f"stdout native={native.stdout[:400]!r} wasm={wasm.stdout[:400]!r}")
        if native.stderr != wasm.stderr:
            diffs.append(f"stderr native={native.stderr[:400]!r} wasm={wasm.stderr[:400]!r}")
        case["fail"] = "; ".join(diffs)
    return case


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("examples", nargs="*", help="example stems to run (default: all)")
    parser.add_argument("--jobs", type=int, default=min(8, os.cpu_count() or 2))
    args = parser.parse_args(argv)
    clang = shutil.which("clang")
    if clang is None:
        raise SystemExit("clang is required")
    error = wasm_target.linker_error(clang)
    if error:
        raise SystemExit(error)
    node = node_command()
    probe = run([node[0], "--version"])
    print(f"V4 wasm lane: {wasm_target._clang_identity(clang)}; node {probe.stdout.decode().strip()}")
    build_v4.require_supported_clang(clang)
    compiler = build_v4.bootstrap(clang, 0)

    sources = sorted((V4_ROOT / "examples").glob("*.fk"))
    if args.examples:
        wanted = set(args.examples)
        sources = [path for path in sources if path.stem in wanted]
    check_v4.RUNTIME_BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    wasm_target.runtime_objects(clang, check_v4.RUNTIME_BUILD_ROOT / "wasm_runtime")
    with tempfile.TemporaryDirectory(prefix="freak-v4-wasm-", dir=check_v4.RUNTIME_BUILD_ROOT) as temporary:
        work = Path(temporary)
        if not args.examples:
            generated = work / "wasm_num_format.fk"
            generated.write_text(NUM_FORMAT_SOURCE, encoding="utf-8")
            sources.append(generated)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
            built = list(pool.map(lambda source: build_case(compiler, clang, source, work), sources))
            results = list(pool.map(lambda case: compare(case, node), built))

    passed = [case for case in results if not ({"fail", "skip", "fenced"} & case.keys())]
    fenced = [case for case in results if "fenced" in case]
    skipped = [case for case in results if "skip" in case]
    failed = [case for case in results if "fail" in case]
    for case in passed:
        rc, out, err = case["native"]
        print(f"  same  {case['name']}: exit={rc} stdout={len(out)}B stderr={len(err)}B wasm={case['bytes']}B")
    for case in fenced:
        print(f"  fence {case['name']}: {case['fenced']}")
    for case in skipped:
        print(f"  skip  {case['name']}: {case['skip']}")
    for case in failed:
        print(f"  FAIL  {case['name']}: {case['fail']}")
    sizes = sorted(case["bytes"] for case in passed)
    if sizes:
        print(f"wasm sizes: min={sizes[0]}B median={sizes[len(sizes) // 2]}B max={sizes[-1]}B")
    print(f"V4 wasm lane: same={len(passed)} fenced={len(fenced)} skipped={len(skipped)} failed={len(failed)}")
    if not passed:
        print("V4 wasm lane ran no programs")
        return 1
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
