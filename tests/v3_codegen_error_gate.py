#!/usr/bin/env python3
"""Executable regression checks for the V3 diagnostic/codegen gate."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SENTINEL = "old artifact must survive a rejected transpile\n"


def run(
    freak: Path,
    repo: Path,
    source: Path,
    *args: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    command, *flags = args
    return subprocess.run(
        [str(freak), command, str(source), *flags],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
        env=env,
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

        for backend, flag, suffix in (("LLVM", "--llvm", ".ll"), ("C", "--c", ".c")):
            borrow_bad = tmp_path / f"borrow_bad_{backend.lower()}.fk"
            borrow_bad.write_text(
                "-- checker error must gate both emitters and linkers\n"
                "-- keep the user statement beyond the prepended-stdlib line clamp\n"
                "\n"
                "task main() -> int {\n"
                '    pilot name: word = "Maverick"\n'
                '    name = "Meiya"\n'
                "    give back 0\n"
                "}\n"
                "\n"
                "main()\n",
                encoding="utf-8",
            )
            borrow_artifact = Path(str(borrow_bad) + suffix)
            borrow_artifact.write_text(SENTINEL, encoding="utf-8")
            borrow_result = run(
                freak, repo, borrow_bad, "transpile", flag, "--strict-borrow"
            )
            assert_rejected(borrow_result, f"{backend} borrow/type gate")
            assert borrow_artifact.read_text(encoding="utf-8") == SENTINEL

            borrow_artifact.unlink()
            borrow_build = run(
                freak, repo, borrow_bad, "build", flag, "--strict-borrow"
            )
            assert_rejected(borrow_build, f"{backend} borrow/type build gate")
            assert not borrow_artifact.exists()
            assert not borrow_bad.with_suffix("").exists()
            assert not borrow_bad.with_suffix(".exe").exists()

        nominal_bad = tmp_path / "nominal_bad.fk"
        nominal_bad.write_text(
            "shape Known { value: int }\n"
            "shape Other { value: int }\n"
            "impl Other { task not_a_method(self) { say \"wrong impl\" } }\n"
            "pilot known = Known { value: 7 }\n"
            "task main() {\n"
            "    pilot missing = known.not_a_field\n"
            "    known.not_a_method()\n"
            "}\n",
            encoding="utf-8",
        )
        for backend, flag, suffix in (("LLVM", "--llvm", ".ll"), ("C", "--c", ".c")):
            nominal_artifact = Path(str(nominal_bad) + suffix)
            nominal_artifact.write_text(SENTINEL, encoding="utf-8")
            nominal_result = run(freak, repo, nominal_bad, "transpile", flag)
            assert_rejected(nominal_result, f"{backend} nominal member gate")
            nominal_output = nominal_result.stdout + nominal_result.stderr
            assert "has no field 'not_a_field'" in nominal_output
            assert "has no method 'not_a_method'" in nominal_output
            assert "nominal_bad.fk:6:1" in nominal_output
            assert "nominal_bad.fk:7:1" in nominal_output
            assert "6 |     pilot missing = known.not_a_field" in nominal_output
            assert "7 |     known.not_a_method()" in nominal_output
            assert nominal_artifact.read_text(encoding="utf-8") == SENTINEL

            nominal_artifact.unlink()
            nominal_build = run(freak, repo, nominal_bad, "build", flag)
            assert_rejected(nominal_build, f"{backend} nominal member build gate")
            assert not nominal_artifact.exists()
            assert not nominal_bad.with_suffix("").exists()
            assert not nominal_bad.with_suffix(".exe").exists()

        nested_nominal_bad = tmp_path / "nested_nominal_bad.fk"
        nested_nominal_bad.write_text(
            "shape Known { value: int }\n"
            "impl Known { task again(self) -> Known { give back self } }\n"
            "pilot known = Known { value: 7 }\n"
            "extern task imported() -> Known\n"
            "task Known_spoof() { say \"not an impl\" }\n"
            "pilot shadowed = Known { value: 8 }\n"
            "task shadow_param(shadowed: int) { say shadowed.value shadowed.not_primitive() }\n"
            "task main() {\n"
            "    when known.missing_when_target {\n"
            "        known.missing_when_case -> say known.missing_when_body\n"
            "        _ -> say \"fallback\"\n"
            "    }\n"
            "    training arc until false max known.missing_max sessions { break }\n"
            "    say known.again().missing_chain\n"
            "    say imported().missing_extern\n"
            "    known.spoof()\n"
            "    shadow_param(7)\n"
            "    pilot primitive: int = 7\n"
            "    say primitive.trim()\n"
            "    say \"x\".trim(1)\n"
            "    say word_from_int(1).not_call_method()\n"
            "    say (1 + 2).missing_expr_field\n"
            "    say (\"a\" + \"b\").not_expr_method()\n"
            "    when known.value {\n"
            "        known.missing_multiline\n"
            "        ->\n"
            "        say \"case\"\n"
            "    }\n"
            "}\n",
            encoding="utf-8",
        )
        for backend, flag, suffix in (("LLVM", "--llvm", ".ll"), ("C", "--c", ".c")):
            artifact = Path(str(nested_nominal_bad) + suffix)
            artifact.write_text(SENTINEL, encoding="utf-8")
            result = run(freak, repo, nested_nominal_bad, "transpile", flag)
            assert_rejected(result, f"{backend} nested nominal traversal gate")
            output = result.stdout + result.stderr
            for member in (
                "missing_when_target",
                "missing_when_case",
                "missing_when_body",
                "missing_max",
                "missing_chain",
                "missing_extern",
            ):
                assert member in output, f"{backend}: did not validate {member}\n{output}"
            assert "has no method 'spoof'" in output
            assert "non-shape value has no fields" in output
            assert "non-shape value has no method 'not_primitive'" in output
            assert "non-shape value has no method 'trim'" in output
            assert "method 'trim' expects 0 argument(s), got 1" in output
            assert "non-shape value has no method 'not_call_method'" in output
            assert "non-shape value has no method 'not_expr_method'" in output
            assert "missing_expr_field" in output
            assert "nested_nominal_bad.fk:9:1" in output
            assert "nested_nominal_bad.fk:10:1" in output
            assert "10 |         known.missing_when_case -> say known.missing_when_body" in output
            assert "nested_nominal_bad.fk:13:1" in output
            assert "nested_nominal_bad.fk:25:1" in output
            assert "25 |         known.missing_multiline" in output
            assert artifact.read_text(encoding="utf-8") == SENTINEL

        install_home = tmp_path / "malformed-stdlib-home"
        shutil.copytree(repo / "freakc" / "runtime", install_home / "runtime")
        shutil.copytree(repo / "std", install_home / "std")
        broken_math = install_home / "std" / "math.fk"
        broken_math.write_text(
            "task broken_std() {\n    say )\n}\n", encoding="utf-8"
        )
        std_user = tmp_path / "malformed_std_user.fk"
        std_user.write_text('task main() {\n    say "user"\n}\n', encoding="utf-8")
        std_env = os.environ.copy()
        std_env["FREAK_HOME"] = str(install_home)
        std_result = run(freak, repo, std_user, "build", "--c", env=std_env)
        assert_rejected(std_result, "malformed installed std source origin")
        std_output = (std_result.stdout + std_result.stderr).replace("\\", "/")
        assert "malformed-stdlib-home/std/math.fk:2:" in std_output, std_output
        assert "2 |     say )" in std_output, std_output

        nominal_shadow_ok = tmp_path / "nominal_shadow_ok.fk"
        nominal_shadow_ok.write_text(
            "shape Known { value: int }\n"
            "pilot shadowed: int = 7\n"
            "task previous(shadowed: Known) { say shadowed.value }\n"
            "say shadowed.to_word()\n"
            "task by_param(shadowed: int) { say shadowed.to_word() }\n"
            "task main() {\n"
            "    pilot shadowed: int = 9\n"
            "    say shadowed.to_word()\n"
            "    by_param(shadowed)\n"
            "}\n",
            encoding="utf-8",
        )
        shadow_check = run(freak, repo, nominal_shadow_ok, "check")
        assert shadow_check.returncode == 0, shadow_check.stdout + shadow_check.stderr

        primitive_ok = tmp_path / "primitive_methods_ok.fk"
        primitive_ok.write_text(
            "task main() {\n"
            "    pilot integer: int = 7\n"
            "    say integer.to_word()\n"
            "    pilot decimal: num = 8.0\n"
            "    pilot decimal_int: int = decimal.to_int()\n"
            "    say decimal_int.to_word()\n"
            "    pilot truth: bool = true\n"
            "    say truth.to_word()\n"
            "    pilot text: word = \"9\"\n"
            "    pilot text_int: int = text.to_int()\n"
            "    say text_int.to_word()\n"
            "}\n",
            encoding="utf-8",
        )
        for backend, flag in (("LLVM", "--llvm"), ("C", "--c")):
            built = run(freak, repo, primitive_ok, "build", flag)
            assert built.returncode == 0, f"{backend} primitive build failed\n{built.stdout}{built.stderr}"
            binary = primitive_ok.with_suffix(".exe" if sys.platform == "win32" else "")
            executed = subprocess.run(
                [str(binary)],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
                check=False,
            )
            assert executed.returncode == 0, executed.stdout + executed.stderr
            assert executed.stdout.strip().splitlines() == ["7", "8", "true", "9"]

        check_result = run(freak, repo, parse_bad, "check")
        check_output = check_result.stdout + check_result.stderr
        assert check_result.returncode != 0, f"check accepted invalid syntax\n{check_output}"
        assert "passed" not in check_output.lower(), f"check printed PASSED\n{check_output}"

        missing_input = subprocess.run(
            [str(freak), "check"],
            cwd=repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
        assert missing_input.returncode != 0, (
            "check without a file argument exited successfully\n"
            + missing_input.stdout
            + missing_input.stderr
        )

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
