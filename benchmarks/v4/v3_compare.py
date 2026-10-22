"""Time V3 and V4 on the same generated programs, source to LLVM module.

Both compilers stop at LLVM IR text: V3 with ``--llvm`` (it writes
``<source>.ll``), V4 through the frozen benchmark compiler that
``v4_scale_bench.py`` builds (it prints the module on stdout). Native linking
and program runtime are not measured. Sources come from the scaling benchmark
generators, so every shape here is also a ``v4_scale_bench.py`` shape.

Run from the repository root after building both compilers::

    python -B -u v4_scale_bench.py --shapes tasks --sizes 10 --work /tmp/v4b
    python -B -u benchmarks/v4/v3_compare.py --v3 build/freakc_v3_stage2 \\
        --v4 /tmp/v4b/compiler/*/v4c --shapes tasks long calls loops \\
        --sizes 200 800 1600 --repeats 3 --json /tmp/v3_compare.json

Each cell is the median wall time of ``--repeats`` runs; samples alternate
which compiler runs first, and the JSON records the order. A row is reported
only when both compilers exit 0; failures are kept in the JSON.
"""

import argparse
import json
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import v4_scale_bench as bench  # noqa: E402


def timed(command, cwd, timeout):
    started = time.perf_counter()
    result = subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=timeout)
    return time.perf_counter() - started, result


def run_v3(v3, source, timeout):
    elapsed, result = timed([str(v3), source.name, "--llvm"], source.parent, timeout)
    module = source.with_name(source.name + ".ll")
    ok = result.returncode == 0 and module.exists() and module.stat().st_size > 0
    size = module.stat().st_size if module.exists() else 0
    if module.exists():
        module.unlink()
    return elapsed, ok, size, result.returncode


def run_v4(v4, source, triple, timeout):
    elapsed, result = timed([str(v4), str(source), triple], source.parent, timeout)
    marker = b"@@V4-MODULE\n"
    ok = result.returncode == 0 and marker in result.stdout and b"v4-errors=0\n" in result.stdout
    size = len(result.stdout.partition(marker)[2])
    return elapsed, ok, size, result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--v3", type=Path, required=True)
    parser.add_argument("--v4", type=Path, required=True)
    parser.add_argument("--shapes", nargs="+", choices=list(bench.GENERATORS), default=["tasks", "long", "calls", "loops"])
    parser.add_argument("--sizes", nargs="+", type=int, default=[200, 800, 1600])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument("--triple", default="x86_64-unknown-linux-gnu")
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    # Runs change into the scratch source directory, so pin both tools first.
    v3 = args.v3.resolve()
    v4 = args.v4.resolve()

    rows = []
    print(f"{'shape':>6} {'size':>6} {'lines':>7} {'v3 s':>8} {'v4 s':>8} {'v4/v3':>7}")
    with tempfile.TemporaryDirectory(prefix="freak-v3-compare-") as scratch:
        for shape in args.shapes:
            for size in args.sizes:
                text, _, _ = bench.GENERATORS[shape](size)
                source = Path(scratch) / f"{shape}_{size}.fk"
                source.write_text(text, encoding="utf-8")
                row = {"shape": shape, "size": size, "lines": text.count("\n"), "v3": [], "v4": [], "order": []}
                runners = {"v3": lambda path: run_v3(v3, path, args.timeout),
                           "v4": lambda path: run_v4(v4, path, args.triple, args.timeout)}
                for sample in range(args.repeats):
                    # Alternate which compiler goes first so cache warmth is shared.
                    order = ("v3", "v4") if sample % 2 == 0 else ("v4", "v3")
                    row["order"].append(list(order))
                    for name in order:
                        try:
                            elapsed, ok, module_bytes, code = runners[name](source)
                        except subprocess.TimeoutExpired:
                            elapsed, ok, module_bytes, code = args.timeout, False, 0, "timeout"
                        row[name].append({"sample": sample, "seconds": elapsed, "ok": ok, "module_bytes": module_bytes, "exit": code})
                both = all(run["ok"] for run in row["v3"] + row["v4"])
                if both:
                    row["v3_median"] = statistics.median(run["seconds"] for run in row["v3"])
                    row["v4_median"] = statistics.median(run["seconds"] for run in row["v4"])
                    row["ratio"] = row["v4_median"] / row["v3_median"]
                    print(f"{shape:>6} {size:>6} {row['lines']:>7} {row['v3_median']:>8.3f} {row['v4_median']:>8.3f} {row['ratio']:>6.2f}x")
                else:
                    print(f"{shape:>6} {size:>6} {row['lines']:>7} failed: "
                          f"v3={[run['exit'] for run in row['v3']]} v4={[run['exit'] for run in row['v4']]}")
                rows.append(row)
    if args.json:
        args.json.write_text(json.dumps({"host": platform.platform(), "python": platform.python_version(),
                                         "v3": str(v3), "v4": str(v4), "repeats": args.repeats,
                                         "rows": rows}, indent=2) + "\n", encoding="utf-8")
    return 0 if all("ratio" in row for row in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
