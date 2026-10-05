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
    parser.add_argument("--case", choices=tuple(POSITIVE) + tuple(NEGATIVE))
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
                command = [args.clang, "-O2", "-o", str(binary), str(generated)]
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
    expected_names = [args.case] if args.case else list(POSITIVE) + list(NEGATIVE)
    expected_inventory = {(backend, name) for backend in backends for name in expected_names}
    assert len(executed_cases) == len(expected_inventory)
    assert set(executed_cases) == expected_inventory
    print(f"V3.5 language contracts: PASS ({len(executed_cases)} cases)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
