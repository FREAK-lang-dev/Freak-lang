#!/usr/bin/env python3
"""Executable regression checks for the V3 diagnostic/codegen gate."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SENTINEL = "old artifact must survive a rejected transpile\n"


def task_body(source: str, task_name: str) -> str:
    start = source.index(f"task {task_name}")
    next_task = source.find("\ntask ", start + 1)
    return source[start:] if next_task < 0 else source[start:next_task]


def assert_builtin_signature_parity(repo: Path) -> None:
    c_source = (repo / "src/compiler/v3/emit_c.fk").read_text(encoding="utf-8")
    llvm_source = (repo / "src/compiler/v3/emit_llvm.fk").read_text(encoding="utf-8")
    checker_source = (repo / "src/compiler/v3/checker.fk").read_text(encoding="utf-8")
    c_mapped = set(
        re.findall(r'val == "([^"]+)"', task_body(c_source, "c_map_call"))
    )
    llvm_mapped = set(
        re.findall(r'val == "([^"]+)"', task_body(llvm_source, "llvm_map_call_name"))
    )
    mapped = c_mapped | llvm_mapped
    classified = set(
        re.findall(
            r'name == "([^"]+)"', task_body(checker_source, "tc_builtin_call_type")
        )
    )
    missing = sorted(mapped - classified)
    assert not missing, f"builtin return-type inventory missing: {missing}"
    unsupported_c_intrinsics = {
        "shape::alloc",
        "shape::get",
        "shape::set",
    }
    assert classified - c_mapped == unsupported_c_intrinsics
    assert classified - llvm_mapped == set()


def assert_ci_shell_contract(repo: Path) -> None:
    workflow = (repo / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    for step_name in (
        "V3 parser/type errors gate code generation",
        "V3 word replacement ownership",
    ):
        marker = f"      - name: {step_name}\n"
        start = workflow.index(marker)
        end = workflow.find("\n      - name: ", start + len(marker))
        block = workflow[start:] if end < 0 else workflow[start:end]
        assert "\n        shell: bash\n" in block, (
            f"{step_name} must use bash so $EXT expands on Windows"
        )


def assert_checker_callable_index(repo: Path) -> None:
    checker = (repo / "src/compiler/v3/checker.fk").read_text(encoding="utf-8")
    assert "task tc_callable_entry(name: word) -> int" in checker
    assert "task tc_index_callable(stmt_id: int) -> void" in checker
    for task_name in (
        "tc_task_return_type",
        "tc_impl_method_arity",
        "tc_has_impl_method",
    ):
        body = task_body(checker, task_name)
        assert "ast_top_stmts" not in body, f"{task_name} still rescans every top-level statement"


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
    assert_builtin_signature_parity(repo)
    assert_ci_shell_contract(repo)
    assert_checker_callable_index(repo)

    with tempfile.TemporaryDirectory(prefix="freak-v3-codegen-gate-") as tmp:
        tmp_path = Path(tmp)
        scale_source = tmp_path / "callable_index_scale.fk"
        scale_source.write_text(
            "\n".join(
                [f"task helper_{index}() -> int {{ give back {index} }}" for index in range(600)]
                + ["task main() { say helper_599().to_word() }"]
            )
            + "\n",
            encoding="utf-8",
        )
        scale_check = run(freak, repo, scale_source, "check")
        assert scale_check.returncode == 0, scale_check.stdout + scale_check.stderr

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

        broken_math.write_text(
            (repo / "std" / "math.fk").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        broken_version = install_home / "std" / "version.fk"
        broken_version.write_text("task broken_std() {\n", encoding="utf-8")
        std_user.write_text('say "user"\n', encoding="utf-8")
        unclosed_result = run(freak, repo, std_user, "build", "--c", env=std_env)
        assert_rejected(unclosed_result, "unclosed installed std block origin")
        unclosed_output = (unclosed_result.stdout + unclosed_result.stderr).replace(
            "\\", "/"
        )
        assert "malformed-stdlib-home/std/version.fk:1:" in unclosed_output
        assert "1 | task broken_std() {" in unclosed_output

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

        reserved_extern = tmp_path / "reserved_extern_bad.fk"
        reserved_extern.write_text(
            "extern task __freak_param_0(value: int) -> int\n"
            "task main() { say __freak_param_0(7) }\n",
            encoding="utf-8",
        )
        for backend, flag in (("LLVM", "--llvm"), ("C", "--c")):
            reserved_result = run(freak, repo, reserved_extern, "transpile", flag)
            assert_rejected(reserved_result, f"{backend} reserved extern namespace")
            assert "compiler-reserved '__freak_' prefix" in (
                reserved_result.stdout + reserved_result.stderr
            )

        builtin_task = tmp_path / "builtin_task_bad.fk"
        builtin_task.write_text(
            "task word_concat(a: word, b: word) -> word { give back a }\n"
            "task main() { say word_concat(\"a\", \"b\") }\n",
            encoding="utf-8",
        )
        for backend, flag in (("LLVM", "--llvm"), ("C", "--c")):
            builtin_task_result = run(freak, repo, builtin_task, "transpile", flag)
            assert_rejected(builtin_task_result, f"{backend} builtin task collision")
            assert "conflicts with a compiler builtin" in (
                builtin_task_result.stdout + builtin_task_result.stderr
            )

        spoofed_runtime = tmp_path / "spoof-project" / "std" / "runtime.fk"
        spoofed_runtime.parent.mkdir(parents=True)
        spoofed_runtime.write_text(
            "task llvm_fs_read(path: word) -> word { give back path }\n"
            "task main() { say \"spoof\" }\n",
            encoding="utf-8",
        )
        for backend, flag in (("LLVM", "--llvm"), ("C", "--c")):
            spoof_result = run(freak, repo, spoofed_runtime, "transpile", flag)
            assert_rejected(spoof_result, f"{backend} spoofed std runtime source")
            assert "conflicts with a compiler builtin" in (
                spoof_result.stdout + spoof_result.stderr
            )

        impl_collision = tmp_path / "impl_task_collision.fk"
        impl_collision.write_text(
            "shape Box { value: int }\n"
            "task Box_ping(value: int) -> int { give back value }\n"
            "impl Box { task ping(self) -> int { give back self.value } }\n"
            "task main() { pilot box = Box { value: 7 } say box.ping() }\n",
            encoding="utf-8",
        )
        for backend, flag in (("LLVM", "--llvm"), ("C", "--c")):
            collision_result = run(freak, repo, impl_collision, "transpile", flag)
            assert_rejected(collision_result, f"{backend} impl task lowering collision")
            assert "conflicts with another task or extern declaration" in (
                collision_result.stdout + collision_result.stderr
            )

        callable_collisions = (
            "extern task helper(value: int) -> int\n"
            "task helper(value: int) -> int { give back value }\n"
            "task main() { say helper(7).to_word() }\n",
            "extern task helper(value: int) -> int\n"
            "extern task helper(value: int) -> int\n"
            "task main() { say helper(7).to_word() }\n",
        )
        for collision_index, collision_source in enumerate(callable_collisions):
            collision_file = tmp_path / f"callable_collision_{collision_index}.fk"
            collision_file.write_text(collision_source, encoding="utf-8")
            for backend, flag in (("LLVM", "--llvm"), ("C", "--c")):
                callable_result = run(
                    freak, repo, collision_file, "transpile", flag
                )
                assert_rejected(
                    callable_result, f"{backend} task/extern collision"
                )
                assert "conflicts with another task or extern declaration" in (
                    callable_result.stdout + callable_result.stderr
                )

        extern_builtin = tmp_path / "extern_builtin_collision.fk"
        extern_builtin.write_text(
            "extern task word_concat(value: int) -> int\n"
            "task main() { say word_concat(7).to_word() }\n",
            encoding="utf-8",
        )
        for backend, flag in (("LLVM", "--llvm"), ("C", "--c")):
            extern_builtin_result = run(
                freak, repo, extern_builtin, "transpile", flag
            )
            assert_rejected(
                extern_builtin_result, f"{backend} extern/builtin collision"
            )
            assert "conflicts with a compiler builtin" in (
                extern_builtin_result.stdout + extern_builtin_result.stderr
            )

        process_args_bad = tmp_path / "process_args_v3_bad.fk"
        process_args_bad.write_text(
            "task main() { pilot values = process::args() say values }\n",
            encoding="utf-8",
        )
        for backend, flag in (("LLVM", "--llvm"), ("C", "--c")):
            process_args_result = run(
                freak, repo, process_args_bad, "transpile", flag
            )
            assert_rejected(
                process_args_result, f"{backend} process::args V3 ABI gate"
            )
            process_args_output = (
                process_args_result.stdout + process_args_result.stderr
            )
            assert "process::args() has no List<word> ABI in V3" in process_args_output
            assert "process::args_count()" in process_args_output
            assert "process::arg(index)" in process_args_output

        c_intrinsic = tmp_path / "c_shape_intrinsic_bad.fk"
        c_intrinsic.write_text(
            "task main() { pilot raw = shape::alloc(1) say raw.to_word() }\n",
            encoding="utf-8",
        )
        c_intrinsic_result = run(freak, repo, c_intrinsic, "transpile", "--c")
        assert_rejected(c_intrinsic_result, "C unsupported shape intrinsic")

        primitive_ok = tmp_path / "primitive_methods_ok.fk"
        primitive_ok.write_text(
            "pilot inferred_global = 1.5 + 2.25\n"
            "pilot __freak_param_0: int = 42\n"
            "task truth() -> bool { give back true }\n"
            "task decimal() -> num { give back 6.75 }\n"
            "task read_collision(other: int) -> int { give back __freak_param_0 }\n"
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
            "    pilot source_integer = 7\n"
            "    pilot inferred_num = source_integer.to_num()\n"
            "    say inferred_num.to_word()\n"
            "    pilot inferred_sum = 1.5 + 2.25\n"
            "    say inferred_sum.to_word()\n"
            "    pilot inferred_checksum = \"a\".checksum()\n"
            "    say (inferred_checksum > 0).to_word()\n"
            "    say (1 < 2).to_word()\n"
            "    say \"x\".contains(\"x\").to_word()\n"
            "    say truth().to_word()\n"
            "    say decimal().to_int().to_word()\n"
            "    say fs::exists(\"definitely-missing-v3-type-probe\").to_word()\n"
            "    say math::sqrt(9.0).to_int().to_word()\n"
            "    say inferred_global.to_word()\n"
            "    say read_collision(7).to_word()\n"
            "    say (source_integer.to_num() + 1.5).to_word()\n"
            "    say (\"a\".checksum() == \"a\".checksum()).to_word()\n"
            "    say \"abc\".replace(\"a\", \"z\")\n"
            "    say word_concat(\"a\", \"b\")\n"
            "    say (time::now_ms() >= 0).to_word()\n"
            "    if false { panic(\"not reached\") }\n"
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
            expected_output = [
                "7",
                "8",
                "true",
                "9",
                "7",
                "3.75",
                "true",
                "true",
                "true",
                "true",
                "6",
                "false",
                "3",
                "3.75",
                "42",
                "8.5",
                "true",
                "zbc",
                "ab",
                "true",
            ]
            actual_output = executed.stdout.strip().splitlines()
            assert actual_output == expected_output, (
                f"{backend} primitive execution mismatch\n"
                f"expected: {expected_output!r}\nactual: {actual_output!r}\n"
                f"stderr: {executed.stderr}"
            )
            if backend == "C":
                generated_c = primitive_ok.with_suffix(".fk.c").read_text(
                    encoding="utf-8"
                )
                assert "freak_time_now_ms()" in generated_c
                assert "freak_panic(" in generated_c
                assert "__freak_user_time_now_ms" not in generated_c
                assert "__freak_user_panic" not in generated_c

        builtin_marker = tmp_path / "builtin-wrapper-marker.txt"
        builtin_marker.write_text("marker", encoding="utf-8")
        builtin_wrappers = tmp_path / "builtin_wrappers.fk"
        builtin_wrappers.write_text(
            "task main() {\n"
            "    pilot mut env_value: word = process::env(\"FREAK_BUILTIN_PROBE\")\n"
            "    say env_value\n"
            "    env_value = \"released\"\n"
            f"    pilot mut listing: word = fs::list_dir(\"{tmp_path.as_posix()}\")\n"
            "    say listing.contains(\"builtin-wrapper-marker.txt\").to_word()\n"
            "    listing = \"released\"\n"
            "    pilot mut letter: word = char_to_word(65)\n"
            "    say letter\n"
            "    letter = \"released\"\n"
            "}\n",
            encoding="utf-8",
        )
        wrapper_env = os.environ.copy()
        wrapper_env["FREAK_BUILTIN_PROBE"] = "ok"
        for backend, flag in (("C", "--c"), ("LLVM", "--llvm")):
            wrapper_build = run(
                freak, repo, builtin_wrappers, "build", flag, env=wrapper_env
            )
            assert wrapper_build.returncode == 0, (
                wrapper_build.stdout + wrapper_build.stderr
            )
            wrapper_binary = builtin_wrappers.with_suffix(
                ".exe" if sys.platform == "win32" else ""
            )
            wrapper_run = subprocess.run(
                [str(wrapper_binary)],
                cwd=tmp_path,
                env=wrapper_env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
                check=False,
            )
            assert wrapper_run.returncode == 0, wrapper_run.stdout + wrapper_run.stderr
            assert wrapper_run.stdout.strip().splitlines() == ["ok", "true", "A"]

        nominal_methods = tmp_path / "nominal_primitive_names.fk"
        nominal_methods.write_text(
            "shape PrimitiveNamed { value: int }\n"
            "shape NumberBox { pad: int value: int }\n"
            "shape WordBox { value: word pad: int }\n"
            "impl PrimitiveNamed {\n"
            "    task to_word(self) -> word { give back \"shape\" }\n"
            "    task length(self) -> int { give back 77 }\n"
            "    task trim(self) -> word { give back \"nominal\" }\n"
            "}\n"
            "task consume_number(value: int) -> int { give back value }\n"
            "task main() {\n"
            "    pilot named = PrimitiveNamed { value: 1 }\n"
            "    say named.to_word()\n"
            "    say named.length().to_word()\n"
            "    say named.trim()\n"
            "    pilot number = NumberBox { pad: 9, value: 7 }\n"
            "    say consume_number(number.value).to_word()\n"
            "}\n",
            encoding="utf-8",
        )
        nominal_llvm = run(freak, repo, nominal_methods, "build", "--llvm")
        assert nominal_llvm.returncode == 0, nominal_llvm.stdout + nominal_llvm.stderr
        nominal_binary = nominal_methods.with_suffix(".exe" if sys.platform == "win32" else "")
        nominal_executed = subprocess.run(
            [str(nominal_binary)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
        assert nominal_executed.returncode == 0, nominal_executed.stdout + nominal_executed.stderr
        assert nominal_executed.stdout.strip().splitlines() == [
            "shape",
            "77",
            "nominal",
            "7",
        ]

        nominal_c = run(freak, repo, nominal_methods, "transpile", "--c")
        assert nominal_c.returncode == 0, nominal_c.stdout + nominal_c.stderr
        nominal_c_text = nominal_methods.with_suffix(".fk.c").read_text(encoding="utf-8")
        assert "__freak_user_PrimitiveNamed_to_word(" in nominal_c_text
        assert re.search(
            r"__freak_user_consume_number\(freak_llvm_shape_get\(__freak_local_\d+, 1\)\)",
            nominal_c_text,
        )
        assert not re.search(
            r"__freak_user_consume_number\(freak_word_clone\(freak_llvm_shape_get",
            nominal_c_text,
        )

        unknown_receiver = tmp_path / "unknown_receiver_field.fk"
        unknown_receiver.write_text(
            "task main() {\n"
            "    say missing_binding.value\n"
            "}\n",
            encoding="utf-8",
        )
        for backend, flag, suffix in (("C", "--c", ".c"), ("LLVM", "--llvm", ".ll")):
            artifact = Path(str(unknown_receiver) + suffix)
            artifact.write_text(SENTINEL, encoding="utf-8")
            rejected = run(freak, repo, unknown_receiver, "transpile", flag)
            assert_rejected(rejected, f"{backend} unknown field receiver gate")
            output = rejected.stdout + rejected.stderr
            assert "cannot resolve the receiver type for field 'value'" in output
            assert artifact.read_text(encoding="utf-8") == SENTINEL

        doctrine_impls = tmp_path / "doctrine_impl_owners.fk"
        doctrine_impls.write_text(
            "shape Alpha { value: int }\n"
            "shape Beta { value: int }\n"
            "impl Labelled for Alpha {\n"
            "    task label(self) -> word { give back \"alpha\" }\n"
            "}\n"
            "impl Labelled for Beta {\n"
            "    task label(self) -> word { give back \"beta\" }\n"
            "}\n"
            "task main() {\n"
            "    pilot alpha = Alpha { value: 1 }\n"
            "    pilot beta = Beta { value: 2 }\n"
            "    say alpha.label()\n"
            "    say beta.label()\n"
            "}\n",
            encoding="utf-8",
        )
        for backend, flag, suffix in (("C", "--c", ".c"), ("LLVM", "--llvm", ".ll")):
            transpiled = run(freak, repo, doctrine_impls, "transpile", flag)
            assert transpiled.returncode == 0, transpiled.stdout + transpiled.stderr
            generated = Path(str(doctrine_impls) + suffix).read_text(encoding="utf-8")
            assert "Alpha_label" in generated
            assert "Beta_label" in generated
            assert "Labelled_label" not in generated

        # The release CLI must be compiled by a current self-host stage.  This
        # full stdlib case used to expose parser errors yet continue into LLVM
        # with duplicate doctrine symbols when the stale bootstrap built it.
        math3d_probe = tmp_path / "math3d_release_probe.fk"
        math3d_probe.write_text(
            (repo / "tests" / "math3d_test.fk").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        math3d_build = run(freak, repo, math3d_probe, "build", "--llvm")
        assert math3d_build.returncode == 0, math3d_build.stdout + math3d_build.stderr
        math3d_binary = math3d_probe.with_suffix(".exe" if sys.platform == "win32" else "")
        assert math3d_binary.is_file(), math3d_binary

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
