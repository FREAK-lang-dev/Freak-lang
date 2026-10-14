#!/usr/bin/env python3
"""Reconstruct the native CLI and verify the installed locked V4 command."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

import v3_word_foundation as foundation
from v4_locked_source import materialize


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tracked_inputs(repo: Path) -> dict[str, str]:
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=repo)
    return {os.fsdecode(name): digest(repo / os.fsdecode(name))
            for name in names.split(b"\0") if name}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--clang", default="clang")
    args = parser.parse_args()
    repo = args.repo.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    build = output / "reconstruction"
    build.mkdir()
    clang = Path(shutil.which(args.clang) or args.clang).resolve(strict=True)
    started = time.monotonic()
    before = tracked_inputs(repo)
    report = {
        "status": "running",
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
        "tree": subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=repo, text=True).strip(),
        "host": {"os": platform.system(), "machine": platform.machine()},
        "clang": {"path": str(clang), "sha256": digest(clang),
                  "version": subprocess.check_output([str(clang), "--version"], text=True).strip()},
        "tracked_inputs_before": before,
        "commands": [],
    }
    original_run = foundation.run

    def recorded_run(command: list[str], cwd: Path, env: dict[str, str] | None = None, timeout: int = 180):
        result = original_run(command, cwd, env, timeout)
        report["commands"].append({"argv": command, "cwd": str(cwd),
                                   "returncode": result.returncode,
                                   "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
                                   "stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest()})
        return result

    foundation.run = recorded_run
    try:
        cli = foundation.build_fresh_cli(clang=str(clang), repo=repo, root=build,
                                         runtime_root=repo / "freakc/runtime")
        report["cli_sha256"] = digest(cli)
        frozen_source, report["locked_source_profile"] = materialize(repo, output / "locked-source-checkout")
        command = [sys.executable, "-B", "-u", str(repo / "tests/v3_v35_bootstrap_native.py"),
                   str(cli), "--clang", str(clang), "--repo", str(repo),
                   "--source", str(frozen_source), "--git-checkout", str(frozen_source),
                   "--evidence", str(output / "public-contracts.json")]
        print("Verifying installed public locked V4 command", flush=True)
        result = subprocess.run(command, cwd=output, timeout=900)
        report["commands"].append({"argv": command, "cwd": str(output), "returncode": result.returncode})
        if result.returncode:
            raise RuntimeError("installed public bootstrap contracts failed")
        report["status"] = "pass"
    except BaseException as error:
        report["status"] = "fail"
        report["error"] = str(error)
        raise
    finally:
        foundation.run = original_run
        report["tracked_inputs_after"] = tracked_inputs(repo)
        report["inputs_unchanged"] = before == report["tracked_inputs_after"]
        report["clang_unchanged"] = report["clang"]["sha256"] == digest(clang)
        if not report["inputs_unchanged"] or not report["clang_unchanged"]:
            report["status"] = "fail"
        report["elapsed_seconds"] = time.monotonic() - started
        (output / "reconstruction.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({key: report[key] for key in ("status", "head", "elapsed_seconds", "inputs_unchanged")}), flush=True)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
