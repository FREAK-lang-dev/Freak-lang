#!/usr/bin/env python3
"""Execute V3.5 syntax contracts with a freshly reconstructed native compiler."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from v3_checked_parsing import build_stage2


POSITIVE = {
    "semicolon_statements": (
        'pilot answer = 7;\n'
        'task value() -> int { pilot local = answer + 1; give back local; }\n'
        'task main() { pilot a = 1; a += 2; say a; say value(); }\n',
        "3\n8\n",
    ),
    "semicolon_bare_return": (
        'task finish() { say "before"; give back; say "unreachable"; }\n'
        'task main() { finish(); say "after"; }\n',
        "before\nafter\n",
    ),
    "semicolon_nested": (
        'task main() {\n'
        '    pilot count = 0;\n'
        '    repeat 3 times { if count == 1 { count += 1; continue; }; '
        'say count; count += 1; };\n'
        '    say "done; still text"; -- ; in a comment stays a comment\n'
        '}\n',
        "0\n2\ndone; still text\n",
    ),
    "semicolon_when_arm": (
        'task main() { pilot x = 1; when x { 1 -> say "one"; }; '
        'when x { 0 -> say "zero"; 1 -> { say "nested"; }; _ -> say "other"; }; }\n',
        "one\nnested\n",
    ),
    "newline_compatibility": (
        'task value() -> int {\n'
        '    pilot count = 4\n'
        '    give back count\n'
        '}\n'
        'task main() {\n'
        '    say value()\n'
        '}\n',
        "4\n",
    ),
    "while_aliases_and_until": (
        'task main() { pilot n = 0; while n < 3 { say n; n += 1; } '
        'repeat while n < 5 { say n; n += 1; } '
        'repeat until n >= 7 { say n; n += 1; } '
        'while false { say "wrong"; } say n; }\n',
        "0\n1\n2\n3\n4\n5\n6\n7\n",
    ),
    "while_reevaluates_condition": (
        'pilot calls = 0;\n'
        'task next() -> bool { calls += 1; give back calls < 4; }\n'
        'task main() { while next() { say calls; } say calls; }\n',
        "1\n2\n3\n4\n",
    ),
    "while_nested_control_and_return": (
        'task early() -> word { pilot n = 0; repeat while true { '
        'pilot text = "owned" + " result"; n += 1; '
        'if n < 2 { continue; } give back text; } give back "unreachable"; }\n'
        'task main() { pilot outer = 0; while outer < 3 { outer += 1; '
        'if outer == 2 { continue; } pilot inner = 0; repeat while true { '
        'inner += 1; if inner == 2 { break; } say outer; } } say early(); }\n',
        "1\n3\nowned result\n",
    ),
    "counted_forms_and_control": (
        'task main() { for each i in 0..4 { if i == 1 { continue; } say i; } '
        'for each i in 0..=4 step 2 { say i; } '
        'repeat 4 times with i { if i == 1 { continue; } if i == 3 { break; } say i; } '
        'for (pilot i = 0; i < 4; i += 1) { if i == 1 { continue; } '
        'if i == 3 { break; } say i; } }\n',
        "0\n2\n3\n0\n2\n4\n0\n2\n0\n2\n",
    ),
    "counted_capture_and_scope": (
        'task start(value: int) -> int { say "start"; give back value; }\n'
        'task finish(value: int) -> int { say "finish"; give back value + 3; }\n'
        'task stride() -> int { say "step"; give back 2; }\n'
        'task main() { pilot i = 4; for each i in start(i)..finish(i) step stride() '
        '{ say i; } say i; repeat i times with i { say i; } say i; '
        'for (pilot i = i - 3; i < 3; i += 1) { say i; } say i; '
        'pilot with = 2; pilot step = 1; repeat with times with k { say k + step; } }\n',
        "start\nfinish\nstep\n4\n6\n4\n0\n1\n2\n3\n4\n1\n2\n4\n1\n2\n",
    ),
    "counted_empty_backwards_and_edges": (
        'task main() { for each i in 2..2 { panic("empty"); } '
        'for each i in 3..1 { panic("backwards"); } '
        'for each i in 3..=1 { panic("inclusive backwards"); } '
        'repeat 0 times with i { panic("zero"); } '
        'repeat -2 times with i { panic("negative"); } '
        'for each i in -3..2 step 2 { say i; } '
        'pilot passes = 0; for each i in 9223372036854775806..=9223372036854775807 '
        '{ passes += 1; if passes > 3 { panic("overflow repeated"); } say i; } '
        'for each i in 9223372036854775807..=9223372036854775807 step 2 { say i; } '
        'say 1.5; say 1.; }\n',
        "-3\n-1\n1\n9223372036854775806\n9223372036854775807\n9223372036854775807\n1.5\n1\n",
    ),
    "counted_nested_owned_cleanup": (
        'task early() -> word { repeat 3 times with i { '
        'pilot text = "owned" + " loop"; if i < 1 { continue; } give back text; } '
        'give back "wrong"; }\n'
        'task main() { for each i in 0..2 { repeat 3 times with i { '
        'pilot text = "temporary" + " word"; if i == 1 { continue; } '
        'for (pilot i = 0; i < 2; i += 1) { say i; break; } } say i; } say early(); }\n',
        "0\n0\n0\n0\n0\n1\nowned loop\n",
    ),
    "counted_for_projection_step": (
        'task main() { pilot mut xs: List<int> = [0]; '
        'for (pilot i = 0; i < 2; xs[0] += 1) { i += 1; } say xs[0]; }\n',
        "2\n",
    ),
    "repeat_with_constant_stack": (
        'task main() { pilot total = 0; repeat 2000000 times with i { total += 1; } say total; }\n',
        "2000000\n",
    ),
}

NEGATIVE = {
    "semicolon_missing_rhs": (
        'task main() { say 1 + ; }\n',
        "unexpected ';'",
        ";",
    ),
    "semicolon_identifier_column": (
        'task main() { say 1; pilot = 2; }\n',
        "expected an identifier for binding name",
        "=",
    ),
    "while_reserved_identifier": (
        'task main() { pilot while = 1; }\n',
        "expected an identifier for binding name",
        "while",
    ),
    "while_condition_type": (
        'task main() { while 1 { say 1; } }\n',
        "repeat while condition must have type bool, got int",
        None,
    ),
    "repeat_while_condition_type": (
        'task main() { repeat while "yes" { say 1; } }\n',
        "repeat while condition must have type bool, got word",
        None,
    ),
    "range_bound_type": (
        'task main() { for each i in 1.5..3 { say i; } }\n',
        "argument 1 expects int, got num", None,
    ),
    "range_step_type": (
        'task main() { for each i in 0..3 step 1.5 { say i; } }\n',
        "argument 3 expects int, got num", None,
    ),
    "range_zero_step": (
        'task main() { for each i in 0..3 step 0 { say i; } }\n',
        "range step must be positive", None,
    ),
    "range_negative_step": (
        'task main() { for each i in 0..3 step -1 { say i; } }\n',
        "range step must be positive", None,
    ),
    "repeat_count_type": (
        'task main() { repeat 2.5 times with i { say i; } }\n',
        "repeat count must have type int, got num", None,
    ),
    "counted_for_initializer_type": (
        'task main() { for (pilot i = 0.5; i < 3; i += 1) { say i; } }\n',
        "counted for initializer must have type int", None,
    ),
    "counted_for_condition_type": (
        'task main() { for (pilot i = 0; 3; i += 1) { say i; } }\n',
        "counted for condition must have type bool, got int", None,
    ),
    "counted_for_step_type": (
        'task main() { for (pilot i = 0; i < 3; i += 1.5) { say i; } }\n',
        "counted for assignment step must have type int", None,
    ),
    "range_binder_scope": (
        'task main() { for each i in 0..1 { say i; } say i; }\n',
        "unknown binding 'i'", None,
    ),
    "repeat_binder_scope": (
        'task main() { repeat 1 times with i { say i; } say i; }\n',
        "unknown binding 'i'", None,
    ),
    "counted_for_binder_scope": (
        'task main() { for (pilot i = 0; i < 1; i += 1) { say i; } say i; }\n',
        "unknown binding 'i'", None,
    ),
    "range_binder_immutable": (
        'task main() { for each i in 0..2 { i = 9; say i; } }\n',
        "iteration binding 'i' is immutable", None,
    ),
    "repeat_binder_immutable": (
        'task main() { repeat 2 times with i { i = 9; say i; } }\n',
        "iteration binding 'i' is immutable", None,
    ),
    "counted_for_fixed_initializer": (
        'task main() { for (fixed pilot i = 0; i < 2; i += 1) { say i; } }\n',
        "counted for initializer must start with pilot", "fixed",
    ),
}

FAULT = {
    "range_dynamic_zero_step": 'task main() { pilot step = 0; for each i in 0..3 step step { say i; } say "after"; }\n',
    "range_dynamic_negative_step": 'task main() { pilot step = -2; for each i in 0..3 step step { say i; } say "after"; }\n',
}


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=180, check=False,
    )


def require_ok(result: subprocess.CompletedProcess[str], label: str) -> None:
    assert result.returncode == 0, (
        label, result.returncode, result.stdout, result.stderr,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--compiler", type=Path,
        help="exact-current-source native stage2 compiler; omit to reconstruct",
    )
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG") or shutil.which("clang"))
    parser.add_argument("--backend", choices=("c", "llvm"))
    parser.add_argument("--optimization", choices=("O0", "O2", "O3"), default="O2")
    parser.add_argument("--case", choices=tuple(POSITIVE) + tuple(NEGATIVE) + tuple(FAULT))
    args = parser.parse_args()
    assert args.clang, "Clang is required; Python transpilation is not a fallback"
    repo = Path(__file__).resolve().parents[1]
    runtime = repo / "freakc/runtime"
    suffix = ".exe" if sys.platform == "win32" else ""
    backends = (args.backend,) if args.backend else ("c", "llvm")
    executed_cases = []
    with tempfile.TemporaryDirectory(prefix="freak-v35-language-") as directory:
        root = Path(directory)
        compiler = (
            args.compiler.resolve(strict=True) if args.compiler
            else build_stage2(clang=args.clang, repo=repo, root=root)
        )
        for backend in backends:
            for name, (program, expected) in POSITIVE.items():
                if args.case and args.case != name:
                    continue
                source = root / f"{name}_{backend}.fk"
                source.write_text(program, encoding="utf-8")
                require_ok(run([str(compiler), str(source), f"--{backend}"], root), name)
                generated = Path(str(source) + (".c" if backend == "c" else ".ll"))
                binary = root / f"{name}_{backend}{suffix}"
                command = [args.clang, "-" + args.optimization, "-o", str(binary), str(generated)]
                if backend == "llvm":
                    command.append(str(runtime / "freak_llvm_runtime.c"))
                command.extend([str(runtime / "freak_runtime.c"), "-I", str(runtime)])
                command.extend(["-lws2_32"] if sys.platform == "win32" else ["-lm"])
                require_ok(run(command, root), f"link {name} {backend}")
                executed = run([str(binary)], root)
                require_ok(executed, f"execute {name} {backend}")
                assert executed.stdout == expected, (name, backend, expected, executed.stdout)
                assert executed.stderr == "", (name, backend, executed.stderr)
                executed_cases.append((backend, name))
                print(f"PASS {backend} {name}", flush=True)
            for name, (program, diagnostic, offending_token) in NEGATIVE.items():
                if args.case and args.case != name:
                    continue
                source = root / f"{name}_{backend}.fk"
                source.write_text(program, encoding="utf-8")
                artifact = Path(str(source) + (".c" if backend == "c" else ".ll"))
                artifact.write_text("stale output must be rejected", encoding="utf-8")
                rejected = run([str(compiler), str(source), f"--{backend}"], root)
                output = rejected.stdout + rejected.stderr
                assert rejected.returncode != 0, (name, backend, output)
                assert diagnostic in output, (name, backend, output)
                column = program.index(offending_token) + 1 if offending_token else 1
                assert f"{source}:1:{column}" in output, (name, backend, column, output)
                assert not artifact.exists(), (name, backend, "stale output survived")
                executed_cases.append((backend, name))
                print(f"PASS {backend} {name}", flush=True)
            for name, program in FAULT.items():
                if args.case and args.case != name:
                    continue
                source = root / f"{name}_{backend}.fk"
                source.write_text(program, encoding="utf-8")
                require_ok(run([str(compiler), str(source), f"--{backend}"], root), name)
                generated = Path(str(source) + (".c" if backend == "c" else ".ll"))
                binary = root / f"{name}_{backend}{suffix}"
                command = [args.clang, "-" + args.optimization, "-o", str(binary), str(generated)]
                if backend == "llvm":
                    command.append(str(runtime / "freak_llvm_runtime.c"))
                command.extend([str(runtime / "freak_runtime.c"), "-I", str(runtime)])
                command.extend(["-lws2_32"] if sys.platform == "win32" else ["-lm"])
                require_ok(run(command, root), f"link fault {name} {backend}")
                executed = run([str(binary)], root)
                assert executed.returncode == 1, (name, backend, executed.returncode, executed.stderr)
                assert executed.stdout == "", (name, backend, executed.stdout)
                assert "PANIC: range step must be positive" in executed.stderr, (name, backend, executed.stderr)
                executed_cases.append((backend, name))
                print(f"PASS {backend} {name}", flush=True)
    expected_names = [args.case] if args.case else list(POSITIVE) + list(NEGATIVE) + list(FAULT)
    expected_inventory = {(backend, name) for backend in backends for name in expected_names}
    assert len(executed_cases) == len(expected_inventory)
    assert set(executed_cases) == expected_inventory
    print(f"V3.5 language contracts: PASS ({len(executed_cases)} cases)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
