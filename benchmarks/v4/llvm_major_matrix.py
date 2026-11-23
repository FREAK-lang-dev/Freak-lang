"""Which LLVM majors accept the V4 text backend's modules (backend lane B0).

Emits a module for every program in src/compiler/v4/examples with
build_v4.py --emit-llvm, compiles each module with the host Clang and with
the Clang inside each requested `ziglang` wheel (`zig cc` reads .ll files),
links every object against the V4 native runtime with the host Clang, runs
it, and compares stdout, stderr and exit status with the host build.

The zig wheels pin these Clang releases: 0.10.1.post1 = 15.0.7,
0.11.0 = 16.0.6, 0.12.0 = 17.0.6, 0.13.0 = 18.1.x, 0.14.0 = 19.1.7,
0.15.1 = 20.1.2. Each goes in its own virtual environment made with uv.

Run from the repository root (Linux x86-64, needs clang and uv)::

    python -B -u benchmarks/v4/llvm_major_matrix.py --work /tmp/llvm-matrix \\
        --zig 0.10.1.post1 0.11.0 0.12.0 0.14.0 0.15.1

Results on 2026-11-23 (host Clang 18.1.3): all 50 modules compile on every
release from 15 to 20, and the 48 programs that link without extra C
fixtures behave identically on all of them. llvm_text_floor.py records the
floor this establishes.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V4 = ROOT / "src" / "compiler" / "v4"
sys.path.insert(0, str(ROOT))
from freakc.v4_native_runtime import SOURCE_NAMES  # noqa: E402

RUNTIME = ROOT / "freakc" / "runtime"


def run(command: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(command, capture_output=True, text=True, **kwargs)


def zig_python(work: Path, version: str) -> Path:
    venv = work / f"zig-{version}"
    python = venv / "bin" / "python"
    if not python.exists():
        run(["uv", "venv", "-q", "-p", "3.10", str(venv)], check=True)
        run(["uv", "pip", "install", "-q", "-p", str(python), f"ziglang=={version}"], check=True)
    return python


def behaviour(executable: Path) -> dict:
    try:
        result = run([str(executable)], timeout=20)
        return {"exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.TimeoutExpired:
        return {"exit": "timeout"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--zig", nargs="+", default=["0.10.1.post1", "0.11.0", "0.12.0", "0.14.0", "0.15.1"])
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()
    work = args.work.resolve()
    (work / "ll").mkdir(parents=True, exist_ok=True)

    modules: list[Path] = []
    for source in sorted((V4 / "examples").glob("*.fk")):
        module = work / "ll" / (source.stem + ".ll")
        result = run([sys.executable, str(V4 / "build_v4.py"), str(source), "-o", str(module), "--emit-llvm"])
        if result.returncode == 0:
            modules.append(module)
        else:
            print(f"skip {source.name}: V4 does not emit it")

    runtime_objects = []
    (work / "rt").mkdir(exist_ok=True)
    for name in SOURCE_NAMES:
        obj = work / "rt" / (Path(name).stem + ".o")
        run(["clang", "-w", "-O2", "-c", str(RUNTIME / name), f"-I{RUNTIME}", "-o", str(obj)], check=True)
        runtime_objects.append(str(obj))

    compilers = {"host": ["clang"]}
    for version in args.zig:
        compilers[version] = [str(zig_python(work, version)), "-m", "ziglang", "cc"]
    versions = {key: run([*cmd, "--version"]).stdout.splitlines()[0] for key, cmd in compilers.items()}

    report: dict = {"versions": versions, "modules": len(modules), "results": {}}
    reference: dict[str, dict] = {}
    for key, command in compilers.items():
        compiled = linked = same = 0
        failures: list[str] = []
        for module in modules:
            obj = work / key / (module.stem + ".o")
            obj.parent.mkdir(exist_ok=True)
            result = run([*command, "-c", "-O2", "-w", str(module), "-o", str(obj)])
            if result.returncode != 0:
                failures.append(f"{module.stem}: compile: {result.stderr.strip().splitlines()[:1]}")
                continue
            compiled += 1
            executable = obj.with_suffix(".native")
            result = run(["clang", str(obj), *runtime_objects, "-o", str(executable), "-lm", "-Wl,-z,muldefs"])
            if result.returncode != 0:
                continue  # programs that need extra C fixtures link in their own gates
            linked += 1
            observed = behaviour(executable)
            if key == "host":
                reference[module.stem] = observed
                same += 1
            elif reference.get(module.stem) == observed:
                same += 1
            else:
                failures.append(f"{module.stem}: behaviour differs from host")
        report["results"][key] = {"compiled": compiled, "linked": linked, "same": same, "failures": failures}
        print(f"{versions[key]}: compiled={compiled}/{len(modules)} linked={linked} same={same} failures={len(failures)}")
        for failure in failures[:5]:
            print("  " + failure)
    if args.json:
        args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if all(not r["failures"] for r in report["results"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
