#!/usr/bin/env python3
"""Build timers and the plain/live view contract.

- `--timings=json` prints one freak-timings/1 object with monotonic,
  millisecond-rounded laps whose top-level phases fit inside the total.
- `--timings` prints the table; malformed values are rejected up front.
- Piped output (the plain view) never moves the cursor, so CI logs stay
  readable. FREAK_LIVE=1 forces the live view and only then may the CLI
  emit cursor-up sequences.
- check, transpile and failing builds report their time too.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

CURSOR_UP = b"\x1b[1A"


def run(freak, repo, *args, env=None, timeout=600):
    merged = os.environ.copy()
    merged.pop("FREAK_LIVE", None)
    merged.pop("FREAK_TIMINGS", None)
    if env:
        merged.update(env)
    return subprocess.run([freak, *args], cwd=repo, env=merged, capture_output=True, timeout=timeout)


def timings_json(stdout: bytes) -> dict:
    for line in reversed(stdout.decode("utf-8", "replace").splitlines()):
        line = line.strip()
        if line.startswith('{"schema":"freak-timings/1"'):
            return json.loads(line)
    raise AssertionError("no freak-timings/1 line:\n" + stdout.decode("utf-8", "replace"))


def check_report(report: dict, command: str, outcome: str, phases: list) -> None:
    assert report["schema"] == "freak-timings/1", report
    assert report["clock"] == "monotonic", report
    assert report["command"] == command, report
    assert report["outcome"] == outcome, report
    total_ns = report["total_ns"]
    assert total_ns > 0 and report["total_ms"] == (total_ns + 500000) // 1000000, report
    names = [p["name"] for p in report["phases"] if p["depth"] == 0]
    for phase in phases:
        assert phase in names, (phase, names)
    top = [p for p in report["phases"] if p["depth"] == 0]
    assert sum(p["ns"] for p in top) <= total_ns, report
    for p in report["phases"]:
        assert p["ns"] >= 0 and p["start_ns"] >= 0, p
        assert p["start_ns"] + p["ns"] <= total_ns + 1000000, p
        assert p["ms"] == (p["ns"] + 500000) // 1000000 or p["ns"] == 0, p


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: v3_build_timers.py FREAK", file=sys.stderr)
        return 2
    freak = str(Path(sys.argv[1]).resolve())
    repo = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="freak-build-timers-") as tmp:
        tmp_path = Path(tmp)
        hello = tmp_path / "hello.fk"
        hello.write_text('say "timers"\n', encoding="utf-8")
        bad = tmp_path / "bad.fk"
        bad.write_text('task main() -> void {\n    pilot x: int = "nope"\n    say x\n}\n', encoding="utf-8")
        exe = tmp_path / "hello-bin"

        built = run(freak, repo, "build", str(hello), "-o", str(exe), "--timings=json")
        assert built.returncode == 0, built.stdout + built.stderr
        assert CURSOR_UP not in built.stdout, "plain (piped) output moved the cursor"
        report = timings_json(built.stdout)
        check_report(report, "build", "ok", ["Sources & packages", "Lexing", "Parsing", "Type checking", "Emit LLVM IR", "Native binary"])
        nested = [p for p in report["phases"] if p["depth"] > 0]
        assert nested, "child processes were not recorded as nested laps"
        assert b"Time:   " in built.stdout and b"ms" in built.stdout, built.stdout
        print("build --timings=json: schema, rounding and nesting OK", flush=True)

        table = run(freak, repo, "build", str(hello), "-o", str(exe), "--timings")
        assert table.returncode == 0, table.stdout + table.stderr
        assert b"TIMINGS" in table.stdout and b"Total" in table.stdout, table.stdout
        print("build --timings: table OK", flush=True)

        env_json = run(freak, repo, "check", str(hello), env={"FREAK_TIMINGS": "json"})
        assert env_json.returncode == 0, env_json.stdout + env_json.stderr
        check_report(timings_json(env_json.stdout), "check", "ok", ["Sources & packages", "Lexing", "Parsing", "Type checking"])
        assert b"no type errors found (" in env_json.stdout, env_json.stdout
        print("check via FREAK_TIMINGS=json: OK", flush=True)

        failed = run(freak, repo, "build", str(bad), "--timings=json")
        assert failed.returncode != 0, failed.stdout
        check_report(timings_json(failed.stdout), "build", "failed", ["Type checking"])
        assert b"BUILD FAILED" in failed.stdout and b"Time:   " in failed.stdout, failed.stdout
        print("failed build reports its time: OK", flush=True)

        transpiled = run(freak, repo, "transpile", str(hello), "--timings=json")
        assert transpiled.returncode == 0, transpiled.stdout + transpiled.stderr
        check_report(timings_json(transpiled.stdout), "transpile", "ok", ["Emit LLVM IR"])
        print("transpile timings: OK", flush=True)

        rejected = run(freak, repo, "build", str(hello), "--timings=xml")
        assert rejected.returncode == 1 and b"--timings must be" in rejected.stdout, rejected.stdout
        print("malformed --timings rejected: OK", flush=True)

        live = run(freak, repo, "build", str(hello), "-o", str(exe), env={"FREAK_LIVE": "1"})
        assert live.returncode == 0, live.stdout + live.stderr
        assert b"BUILD SUCCESSFUL" in live.stdout, live.stdout
        plain = run(freak, repo, "build", str(hello), "-o", str(exe), env={"FREAK_LIVE": "1", "FREAK_PLAIN": "1"})
        assert plain.returncode == 0 and CURSOR_UP not in plain.stdout, plain.stdout
        print("live view renders; FREAK_PLAIN wins over FREAK_LIVE: OK", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
