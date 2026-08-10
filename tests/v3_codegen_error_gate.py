#!/usr/bin/env python3
"""Executable regression checks for the V3 diagnostic/codegen gate."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


SENTINEL = "old artifact must survive a rejected transpile\n"


def run(
    freak: Path, repo: Path, source: Path, *args: str
) -> subprocess.CompletedProcess[str]:
    command, *flags = args
    return subprocess.run(
        [str(freak), command, str(source), *flags],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def assert_rejected(result: subprocess.CompletedProcess[str], label: str) -> None:
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"{label}: invalid input exited successfully\n{output}"
    assert "code generation skipped" in output.lower(), (
        f"{label}: missing hard-gate diagnostic\n{output}"
    )
    assert "emit llvm ir" not in output.lower(), f"{label}: LLVM emitter ran\n{output}"
    assert "emit c" not in output.lower(), f"{label}: C emitter ran\n{output}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("freak", type=Path)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    freak = args.freak.resolve()
    assert freak.is_file(), f"FREAK CLI not found: {freak}"

    with tempfile.TemporaryDirectory(prefix="freak-v3-codegen-gate-") as tmp:
        tmp_path = Path(tmp)
        parse_bad = tmp_path / "parse_bad.fk"
        parse_bad.write_text('task main() {\n    say )\n}\n', encoding="utf-8")

        for backend, flag, suffix in (("LLVM", "--llvm", ".ll"), ("C", "--c", ".c")):
            artifact = Path(str(parse_bad) + suffix)
            artifact.write_text(SENTINEL, encoding="utf-8")
            result = run(freak, repo, parse_bad, "transpile", flag)
            assert_rejected(result, f"{backend} parse gate")
            assert artifact.read_text(encoding="utf-8") == SENTINEL, (
                f"{backend} parse gate overwrote the previous artifact"
            )

        borrow_bad = tmp_path / "borrow_bad.fk"
        borrow_bad.write_text(
            "task main() {\n"
            '    pilot name: word = "Maverick"\n'
            '    name = "Meiya"\n'
            "}\n",
            encoding="utf-8",
        )
        borrow_artifact = Path(str(borrow_bad) + ".ll")
        borrow_artifact.write_text(SENTINEL, encoding="utf-8")
        borrow_result = run(
            freak, repo, borrow_bad, "transpile", "--llvm", "--strict-borrow"
        )
        assert_rejected(borrow_result, "borrow/type gate")
        assert borrow_artifact.read_text(encoding="utf-8") == SENTINEL

        check_result = run(freak, repo, parse_bad, "check")
        check_output = check_result.stdout + check_result.stderr
        assert check_result.returncode != 0, f"check accepted invalid syntax\n{check_output}"
        assert "passed" not in check_output.lower(), f"check printed PASSED\n{check_output}"

        for backend, flag, suffix in (("LLVM", "--llvm", ".ll"), ("C", "--c", ".c")):
            build_bad = tmp_path / f"build_bad_{backend.lower()}.fk"
            build_bad.write_text('task main() {\n    say )\n}\n', encoding="utf-8")
            build_result = run(freak, repo, build_bad, "build", flag)
            build_output = build_result.stdout + build_result.stderr
            assert build_result.returncode != 0, (
                f"{backend} build accepted invalid syntax\n{build_output}"
            )
            assert not Path(str(build_bad) + suffix).exists(), (
                f"{backend} build emitted {suffix} for invalid input"
            )
            assert not build_bad.with_suffix("").exists(), (
                f"{backend} build emitted a binary for invalid input"
            )
            assert not build_bad.with_suffix(".exe").exists(), (
                f"{backend} build emitted a Windows binary for invalid input"
            )

    print("V3 codegen error gate: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
