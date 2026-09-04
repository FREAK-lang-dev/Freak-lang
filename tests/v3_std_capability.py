#!/usr/bin/env python3
"""Reject an older same-ABI std payload before codegen or cached execution."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import v3_word_foundation as foundation


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("freak", nargs="?", type=Path)
    parser.add_argument("--runtime-root", type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    runtime = args.runtime_root.resolve() if args.runtime_root else repo / "freakc/runtime"
    clang = os.environ.get("FREAK_CLANG") or shutil.which("clang")
    assert clang, "Clang is required"
    with tempfile.TemporaryDirectory(prefix="freak-v3-std-capability-") as temporary:
        root = Path(temporary)
        freak = args.freak.resolve() if args.freak else foundation.build_fresh_cli(
            clang=clang, repo=repo, root=root, runtime_root=runtime)
        payload = root / "selected payload"
        shutil.copytree(runtime, payload / "runtime")
        shutil.copytree(repo / "std", payload / "std")
        marker = payload / "std/freak_std_api"
        expected = marker.read_bytes()
        expected_text = expected.decode("utf-8").strip()
        env = os.environ.copy()
        env.update(FREAK_HOME=str(payload), FREAK_CLANG=clang, NO_COLOR="1")

        def invoke(*arguments: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run([str(freak), *arguments], cwd=root, env=env,
                                  capture_output=True, text=True, encoding="utf-8",
                                  errors="replace", timeout=240)

        for backend in ("--c", "--llvm"):
            warm = root / f"warm{backend}.fk"
            cold = root / f"cold{backend}.fk"
            warm.write_text('say "STD_API_EXECUTED"\n', encoding="utf-8")
            cold.write_text('say "STD_API_COLD_EXECUTED"\n', encoding="utf-8")
            binary = warm.with_suffix(".exe" if sys.platform == "win32" else "")
            proof = Path(str(binary) + ".freak-run-cache")
            for attempt in range(2):
                result = invoke("run", str(warm), backend)
                output = result.stdout + result.stderr
                assert result.returncode == 0 and "STD_API_EXECUTED" in output, output
                assert ("run cache hit" in output) == (attempt == 1), output
            saved = [(path.read_bytes(), path.stat().st_mtime_ns) for path in (binary, proof)]
            for invalid in (None, b"freak-v3-std-api-0\n", b"freak-v3-std-api-999\n"):
                if invalid is None:
                    marker.unlink()
                else:
                    marker.write_bytes(invalid)
                report = invoke("doctor", "--json")
                assert report.returncode != 0, report.stdout + report.stderr
                document = json.loads(report.stdout)
                assert document["status"] == "issues", document
                assert document["checks"]["abi"]["ok"] is True, document
                assert document["checks"]["runtime_api"]["ok"] is True, document
                assert document["checks"]["stdlib_api"] == {
                    "ok": False, "expected": expected_text,
                    "stdlib": "missing" if invalid is None else invalid.decode().strip(),
                }, document
                for operation in ("build", "run"):
                    rejected = invoke(operation, str(cold), backend)
                    output = rejected.stdout + rejected.stderr
                    assert rejected.returncode != 0, output
                    assert "stdlib api mismatch" in output.lower(), output
                    assert "STD_API_COLD_EXECUTED" not in output, output
                    assert list(root.glob(cold.name + ".*")) == [], list(root.iterdir())
                    assert not cold.with_suffix(".exe" if sys.platform == "win32" else "").exists()
                rejected = invoke("run", str(warm), backend)
                output = rejected.stdout + rejected.stderr
                assert rejected.returncode != 0 and "stdlib api mismatch" in output.lower(), output
                assert "STD_API_EXECUTED" not in output and "run cache hit" not in output, output
                assert [(path.read_bytes(), path.stat().st_mtime_ns) for path in (binary, proof)] == saved
                marker.write_bytes(expected)
                recovered = invoke("run", str(warm), backend)
                assert recovered.returncode == 0 and "run cache hit" in recovered.stdout, recovered.stdout + recovered.stderr
                assert [(path.read_bytes(), path.stat().st_mtime_ns) for path in (binary, proof)] == saved
        print("PASS C/LLVM cold build/run and warm-cache std API rejection/recovery; layout ABI unchanged")

        # Doctor --fix must detect an incompatible present marker as well as
        # a missing file, invoke the existing upgrade route, and re-read it.
        fix = root / ("fix.ps1" if sys.platform == "win32" else "fix.sh")
        if sys.platform == "win32":
            fix.write_text("param([switch]$Upgrade,[switch]$SkipDeps)\n"
                           "[IO.File]::WriteAllText((Join-Path $env:FREAK_HOME 'std/freak_std_api'), "
                           f"'{expected_text}')\nexit 0\n", encoding="utf-8")
        else:
            fix.write_text("#!/bin/sh\nset -eu\n"
                           f"printf '%s\\n' '{expected_text}' > \"$FREAK_HOME/std/freak_std_api\"\n",
                           encoding="utf-8")
            fix.chmod(0o755)
        marker.write_text("freak-v3-std-api-0\n", encoding="utf-8")
        env["FREAK_UPGRADE_SCRIPT"] = str(fix)
        fixed = invoke("doctor", "--fix")
        output = fixed.stdout + fixed.stderr
        assert fixed.returncode == 0, output
        assert "Repairing the compiler/runtime/stdlib payload" in output, output
        assert "compile, link, and execution work" in output, output
        assert marker.read_text(encoding="utf-8").strip() == expected_text
        report = invoke("doctor", "--json")
        assert report.returncode == 0, report.stdout + report.stderr
        assert json.loads(report.stdout)["checks"]["stdlib_api"]["ok"] is True
        print("PASS Doctor std API repair and full pipeline recovery")

        marker.write_text("freak-v3-std-api-0\n", encoding="utf-8")
        fix.write_text("param([switch]$Upgrade,[switch]$SkipDeps)\nexit 0\n"
                       if sys.platform == "win32" else "#!/bin/sh\nexit 0\n",
                       encoding="utf-8")
        ineffective = invoke("doctor", "--fix")
        output = ineffective.stdout + ineffective.stderr
        assert ineffective.returncode != 0, output
        assert "Stdlib API mismatch" in output, output
        assert "compile, link, and execution work" not in output, output
        assert marker.read_text(encoding="utf-8").strip() == "freak-v3-std-api-0"
        print("PASS ineffective std API repair remains fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
