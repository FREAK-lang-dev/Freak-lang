#!/usr/bin/env python3
"""Meiya on error-heavy strict input: bounded time and memory.

Builds a probe from tools/build_llvm.fk that keeps going after errors and stops
after Meiya (borrowck), so every stage runs even when earlier stages report
diagnostics. Then, under a memory cap and a timeout per process:

* each compiler crate is compiled alone in strict mode, without its
  cross-crate definitions (the baseline in BACKEND_CHECKPOINT.md);
* a synthetic task moves one word N times in sibling branches, so every later
  move is a partial-move conflict.

Writes one JSON report. Run it once per tree to compare (for example on main
and on a branch) and pass --label to tell the reports apart.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V4 = ROOT / "src/compiler/v4"
sys.path.insert(0, str(V4))

import check_v4 as checks  # noqa: E402

CRATES = (
    "freak_span", "freak_diag", "freak_macro_api", "freak_arena", "freak_intern",
    "freak_session", "freak_target", "freak_lex", "freak_parse", "freak_expand",
    "freak_hir", "freak_resolve", "freak_ty", "freak_mir", "freak_mir_build",
    "freak_borrowck", "freak_codegen_llvm", "freak_query", "freak_driver",
    "freak_editor", "freak_snapshot", "freak_lsp",
)
STAGE = re.compile(r"v4-build-stage=(\w+) diagnostics=(\d+)")
ABORT = 'task v4_build_llvm_abort(errors: int, stage: word) -> bool {\n    if errors <= 0 { give back false }'
KEEP_GOING = 'task v4_build_llvm_abort(errors: int, stage: word) -> bool {\n    if stage != "borrowck" { give back false }\n    if errors <= 0 { give back false }'


def build_probe(out_dir: Path) -> Path:
    source = (V4 / "tools/build_llvm.fk").read_text(encoding="utf-8")
    if source.count(ABORT) != 1:
        raise SystemExit("tools/build_llvm.fk abort task changed; update meiya_error_heavy.py")
    fixture = out_dir / "meiya_probe.fk"
    fixture.write_text(source.replace(ABORT, KEEP_GOING), encoding="utf-8")
    c_source, _ = checks.transpile_fixture(checks.flattened_crates(), fixture)
    runtime = checks.RUNTIME_ROOT / "freak_runtime.c"
    checks.RUNTIME_BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    executable, _ = checks.compile_runtime_smoke(
        "clang", f"-I{checks.RUNTIME_ROOT}", runtime, checks.read_text(runtime), fixture, c_source, ())
    probe = out_dir / "meiya_probe"
    shutil.copy(executable, probe)
    return probe


def peak_rss_mb(pid: int) -> int:
    try:
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) // 1024
    except OSError:
        pass
    return 0


def run_one(probe: Path, source: Path, memory: int, timeout: float) -> dict:
    start = time.monotonic()
    proc = subprocess.Popen(
        ["prlimit", f"--as={memory}", "--", str(probe), str(source), "x86_64-unknown-linux-gnu", "unwind"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    peak = [0]

    def watch() -> None:
        while proc.poll() is None:
            peak[0] = max(peak[0], peak_rss_mb(proc.pid))
            time.sleep(0.05)

    watcher = threading.Thread(target=watch, daemon=True)
    watcher.start()
    timer = threading.Timer(timeout, proc.kill)
    timer.start()
    stages: dict[str, dict] = {}
    last = start
    tail: list[str] = []
    assert proc.stdout is not None
    for line in proc.stdout:
        match = STAGE.match(line)
        if match:
            now = time.monotonic()
            stages[match.group(1)] = {"diagnostics": int(match.group(2)), "seconds": round(now - last, 2)}
            last = now
        elif line.startswith(("v4-", "FREAK:")):
            tail.append(line.strip())
    code = proc.wait()
    timed_out = not timer.is_alive() and code < 0
    timer.cancel()
    watcher.join()
    if "borrowck" in stages:
        outcome = "meiya finished"
    elif timed_out:
        outcome = "timeout"
    elif any("out of memory" in line for line in tail):
        outcome = "memory limit"
    else:
        outcome = f"exit {code}"
    return {
        "outcome": outcome,
        "exit": code,
        "seconds": round(time.monotonic() - start, 2),
        "peak_rss_mb": peak[0],
        "stages": stages,
        "tail": tail[-3:],
    }


def synthetic_source(moves: int) -> str:
    lines = ["task eat(v: word) -> int {", " give back v.length()", "}", "task main() -> int {", ' pilot w = "ab"', " pilot t = 0"]
    for index in range(moves):
        lines += [f" if t > {index} {{", "  t = t + eat(w)", " } else {", "  t = t + 1", " }"]
    lines += [" give back t", "}"]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--label", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--memory-mib", type=int, default=2048)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--synthetic", default="100,200,400,800")
    parser.add_argument("--synthetic-timeout", type=float, default=300.0)
    args = parser.parse_args()
    memory = args.memory_mib * 1024 * 1024
    work = ROOT / "build/v4_smoke/meiya_error_heavy" / args.label
    work.mkdir(parents=True, exist_ok=True)
    probe = build_probe(work)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    report: dict = {
        "label": args.label,
        "head": head,
        "memory_mib": args.memory_mib,
        "timeout_s": args.timeout,
        "probe_sha256": hashlib.sha256(probe.read_bytes()).hexdigest(),
        "crates": {},
        "synthetic": {},
    }
    for crate in CRATES:
        source = V4 / "crates" / crate / "src/lib.fk"
        row = run_one(probe, source, memory, args.timeout)
        row["source_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
        row["lines"] = source.read_text(encoding="utf-8").count("\n")
        report["crates"][crate] = row
        print(f"{crate:20} {row['outcome']:15} {row['seconds']:7.2f}s {row['peak_rss_mb']:5}MiB", flush=True)
    for moves in [int(n) for n in args.synthetic.split(",") if n]:
        source = work / f"synthetic_{moves}.fk"
        source.write_text(synthetic_source(moves), encoding="utf-8")
        row = run_one(probe, source, memory, args.synthetic_timeout)
        report["synthetic"][str(moves)] = row
        print(f"synthetic {moves:5} moves {row['outcome']:15} {row['seconds']:7.2f}s {row['peak_rss_mb']:5}MiB", flush=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
