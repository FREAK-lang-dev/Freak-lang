"""Time V4 programs with and without the runtime helper attributes (B0).

Codegen marks every ``@freak_v4_`` runtime helper ``nounwind`` and the word
and array queries that allocate nothing ``readonly`` (see
``v4_codegen_llvm_runtime_declare_attributes``). This script builds each
program once with ``build_v4.py --emit-llvm``, makes a second module with
those attributes removed from the ``declare`` lines, links both the way
``build_v4.py`` links, and runs them alternately::

    python -B -u benchmarks/v4/runtime_helper_attributes.py --repeats 5 \\
        --json /tmp/runtime_helper_attributes.json

Programs: the three kernels of ``runtime_helper_attributes.fk`` and the tier
1 hot loop (``int_checked_hot_loop.fk``), which calls no helper and so must
not move. Outputs of the two builds must match exactly. Each cell is the
median wall time of ``--repeats`` runs, start-up included.
"""

import argparse
import json
import platform
import re
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V4 = ROOT / "src" / "compiler" / "v4"
HERE = Path(__file__).resolve().parent

# (label, source, arguments, what the attributes allow)
CASES = (
    ("length in a loop condition", "runtime_helper_attributes.fk", ("0", "300000"),
     "text.length() is asked once per inner loop instead of every pass"),
    ("three queries per pass", "runtime_helper_attributes.fk", ("1", "3000000"),
     "starts_with is asked once; ends_with and contains stay, because a "
     "helper that may panic must run before the next one is reached"),
    ("control: new word per pass", "runtime_helper_attributes.fk", ("2", "1000000"),
     "nothing moves: to_lower allocates"),
    ("tier 1 hot loop", "int_checked_hot_loop.fk", ("100000000", "7"),
     "nothing moves: no helper in the loop"),
)

ATTRIBUTES = re.compile(r"^(declare [^\n]*@freak_v4_\w+\([^\n]*\))(?: readonly)? nounwind$", re.M)


def strip_attributes(module: str) -> str:
    return ATTRIBUTES.sub(r"\1", module)


def build_module(source: Path, out: Path) -> str:
    result = subprocess.run([sys.executable, "-B", str(V4 / "build_v4.py"), str(source), "-o", str(out),
                             "--emit-llvm"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True)
    if result.returncode != 0:
        raise SystemExit(f"build_v4.py failed for {source.name}:\n{result.stdout}")
    return out.read_text(encoding="utf-8")


def link(clang: str, module: Path, exe: Path) -> None:
    sys.path.insert(0, str(V4))
    import build_v4  # noqa: E402
    result = subprocess.run(build_v4.native_link_command(clang, module, exe), cwd=ROOT,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if result.returncode != 0:
        raise SystemExit(f"link failed for {module.name}:\n{result.stdout}")


def run(exe: Path, arguments) -> tuple[float, str]:
    started = time.perf_counter()
    result = subprocess.run([str(exe), *arguments], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, timeout=600)
    elapsed = time.perf_counter() - started
    if result.returncode != 0:
        raise SystemExit(f"{exe.name} {' '.join(arguments)} exited {result.returncode}: {result.stderr}")
    return elapsed, result.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--clang", default="clang")
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    rows = []
    with tempfile.TemporaryDirectory(prefix="freak-v4-helper-attributes-") as scratch:
        work = Path(scratch)
        built = {}
        for source in sorted({case[1] for case in CASES}):
            stem = Path(source).stem
            marked = work / f"{stem}.ll"
            text = build_module(HERE / source, marked)
            plain = strip_attributes(text)
            if plain == text:
                raise SystemExit(f"{source}: codegen marked no runtime helper; nothing to compare")
            if "nounwind" in "\n".join(line for line in plain.splitlines() if "@freak_v4_" in line and line.startswith("declare")):
                raise SystemExit(f"{source}: a helper attribute survived stripping")
            unmarked = work / f"{stem}.plain.ll"
            unmarked.write_text(plain, encoding="utf-8")
            built[source] = (work / f"{stem}.plain", work / f"{stem}.marked")
            link(args.clang, unmarked, built[source][0])
            link(args.clang, marked, built[source][1])
        print(f"{'case':<28} {'without s':>10} {'with s':>8} {'speed-up':>9}")
        for label, source, arguments, note in CASES:
            plain_exe, marked_exe = built[source]
            samples = {"without": [], "with": []}
            outputs = set()
            for repeat in range(args.repeats):
                order = (("without", plain_exe), ("with", marked_exe))
                if repeat % 2:
                    order = order[::-1]
                for name, exe in order:
                    elapsed, output = run(exe, arguments)
                    samples[name].append(elapsed)
                    outputs.add(output)
            if len(outputs) != 1:
                raise SystemExit(f"{label}: outputs differ: {sorted(outputs)}")
            without = statistics.median(samples["without"])
            with_attributes = statistics.median(samples["with"])
            rows.append({"case": label, "source": source, "arguments": list(arguments), "note": note,
                         "output": outputs.pop().strip(), "without_s": samples["without"],
                         "with_s": samples["with"], "median_without_s": without,
                         "median_with_s": with_attributes, "speedup": without / with_attributes})
            print(f"{label:<28} {without:>10.3f} {with_attributes:>8.3f} {without / with_attributes:>8.2f}x")
    if args.json:
        clang_version = subprocess.run([args.clang, "--version"], stdout=subprocess.PIPE, text=True).stdout.splitlines()[0]
        args.json.write_text(json.dumps({"platform": platform.platform(), "machine": platform.machine(),
                                         "clang": clang_version, "repeats": args.repeats, "rows": rows},
                                        indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
