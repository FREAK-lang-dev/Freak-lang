#!/usr/bin/env python3
"""V3 checked word parsing: strict parse_int/parse_num plus sticky status.

Covers malformed input, int/num boundary minima and maxima, junk suffixes,
and overflow/underflow on both native backends with C/LLVM parity, no-leak
runs under the ownership audits, checker negatives, and Python bootstrap
emitter fixtures proving owned format_num temporaries are released on say,
interpolation, local scope exit, reassignment, and discarded paths (with
ASan/LSan sanitizer coverage where the host linker supports it).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


COMPILER_SOURCES = (
    "src/compiler/v3/globals.fk",
    "src/compiler/v3/helpers.fk",
    "src/compiler/v3/lexer.fk",
    "src/compiler/v3/parser.fk",
    "src/compiler/v3/checker.fk",
    "src/compiler/v3/emit_c.fk",
    "src/compiler/v3/emit_llvm.fk",
    "src/compiler/v3/main.fk",
)

LIVE_WORDS_PREAMBLE = (
    "extern task freak_v3_live_words() -> int\n"
)

CASES: dict[str, tuple[str, list[str]]] = {
    "int_valid": (
        """task main() {
    say "0".parse_int()
    say parse_status()
    say "007".parse_int()
    say parse_status()
    say "+42".parse_int()
    say parse_status()
    say "-42".parse_int()
    say parse_status()
    say "9223372036854775807".parse_int()
    say parse_status()
    say "-9223372036854775808".parse_int()
    say parse_status()
}
""",
        ["0", "0", "7", "0", "42", "0", "-42", "0",
         "9223372036854775807", "0", "-9223372036854775808", "0"],
    ),
    "num_valid": (
        """task main() {
    say "3.14".parse_num()
    say parse_status()
    say "-0.5".parse_num()
    say parse_status()
    say ".5".parse_num()
    say parse_status()
    say "5.".parse_num()
    say parse_status()
    say "1e3".parse_num()
    say parse_status()
    say "1E-3".parse_num()
    say parse_status()
    say "+2.5e+2".parse_num()
    say parse_status()
    say "1.7976931348623157e308".parse_num()
    say parse_status()
}
""",
        ["3.14", "0", "-0.5", "0", "0.5", "0", "5", "0", "1000", "0",
         "0.001", "0", "250", "0", "1.797693135e+308", "0"],
    ),
    "int_malformed": (
        """task main() {
    say "".parse_int()
    say parse_status()
    parse_clear_status()
    say "+".parse_int()
    say parse_status()
    parse_clear_status()
    say "-".parse_int()
    say parse_status()
    parse_clear_status()
    say "12a".parse_int()
    say parse_status()
    parse_clear_status()
    say "a12".parse_int()
    say parse_status()
    parse_clear_status()
    say "4.5".parse_int()
    say parse_status()
    parse_clear_status()
    say " 42".parse_int()
    say parse_status()
    parse_clear_status()
    say "42 ".parse_int()
    say parse_status()
    parse_clear_status()
    say "1_000".parse_int()
    say parse_status()
    parse_clear_status()
    say "0x10".parse_int()
    say parse_status()
    parse_clear_status()
    say parse_status()
}
""",
        ["0", "1", "0", "1", "0", "1", "0", "1", "0", "1", "0", "1",
         "0", "1", "0", "1", "0", "1", "0", "1", "0"],
    ),
    "num_malformed": (
        """task main() {
    say "".parse_num()
    say parse_status()
    parse_clear_status()
    say ".".parse_num()
    say parse_status()
    parse_clear_status()
    say "+".parse_num()
    say parse_status()
    parse_clear_status()
    say "e5".parse_num()
    say parse_status()
    parse_clear_status()
    say "1e".parse_num()
    say parse_status()
    parse_clear_status()
    say "1e+".parse_num()
    say parse_status()
    parse_clear_status()
    say "abc".parse_num()
    say parse_status()
    parse_clear_status()
    say "12px".parse_num()
    say parse_status()
    parse_clear_status()
    say " 1".parse_num()
    say parse_status()
    parse_clear_status()
    say "1 ".parse_num()
    say parse_status()
    parse_clear_status()
    say "nan".parse_num()
    say parse_status()
    parse_clear_status()
    say "inf".parse_num()
    say parse_status()
    parse_clear_status()
    say "0x10".parse_num()
    say parse_status()
    parse_clear_status()
    say parse_status()
}
""",
        ["0", "1", "0", "1", "0", "1", "0", "1", "0", "1", "0", "1",
         "0", "1", "0", "1", "0", "1", "0", "1", "0", "1", "0", "1",
         "0", "1", "0"],
    ),
    "int_overflow": (
        """task main() {
    say "9223372036854775808".parse_int()
    say parse_status()
    parse_clear_status()
    say "-9223372036854775809".parse_int()
    say parse_status()
    parse_clear_status()
    say "99999999999999999999999".parse_int()
    say parse_status()
    parse_clear_status()
    say "-99999999999999999999999".parse_int()
    say parse_status()
    parse_clear_status()
    say parse_status()
}
""",
        ["0", "2", "0", "2", "0", "2", "0", "2", "0"],
    ),
    "num_overflow": (
        """task main() {
    say "1e999".parse_num()
    say parse_status()
    parse_clear_status()
    say "-1e999".parse_num()
    say parse_status()
    parse_clear_status()
    say "1e-999".parse_num()
    say parse_status()
    parse_clear_status()
    say parse_status()
}
""",
        ["0", "2", "0", "2", "0", "2", "0"],
    ),
    "sticky_status": (
        """task main() {
    say "zz".parse_int()
    say parse_status()
    say "7".parse_int()
    say parse_status()
    say "99999999999999999999999".parse_int()
    say parse_status()
    parse_clear_status()
    say parse_status()
    say "7".parse_int()
    say parse_status()
}
""",
        ["0", "1", "7", "1", "0", "1", "0", "7", "0"],
    ),
    "owned_receiver_no_leak": (
        LIVE_WORDS_PREAMBLE + """task main() {
    say ("4" + "2").parse_int()
    say parse_status()
    say ("3" + ".5").parse_num()
    say parse_status()
    say ("1" + "2x").parse_int()
    say parse_status()
    parse_clear_status()
    say freak_v3_live_words()
}
""",
        ["42", "0", "3.5", "0", "0", "1", "0"],
    ),
    "legacy_untouched": (
        """task main() {
    say "007".to_int()
    say parse_status()
    say "  42x".to_int()
    say parse_status()
    say "3.5x".to_num()
    say parse_status()
    say "old:".to_int()
    say parse_status()
}
""",
        ["7", "0", "42", "0", "3.5", "0", "0", "0"],
    ),
    "surrounding_whitespace": (
        """task main() {
    say "\\t42\\t".parse_int()
    say parse_status()
    say "\\n-7\\n".parse_int()
    say parse_status()
    say "\\t3.5\\n".parse_num()
    say parse_status()
    say "4 2".parse_int()
    say parse_status()
}
""",
        ["0", "1", "0", "1", "0", "1", "0", "1"],
    ),
}

NEGATIVES: tuple[tuple[str, str, str], ...] = (
    (
        "int_receiver",
        'task main() {\n    pilot n = 1\n    say n.parse_int()\n}\n',
        "non-shape value has no method 'parse_int'",
    ),
    (
        "num_receiver",
        'task main() {\n    pilot x = 1.5\n    say x.parse_num()\n}\n',
        "non-shape value has no method 'parse_num'",
    ),
    (
        "parse_int_arity",
        'task main() {\n    say "1".parse_int(2)\n}\n',
        "method 'parse_int' expects 0 argument(s), got 1",
    ),
    (
        "parse_num_arity",
        'task main() {\n    say "1".parse_num(1, 2)\n}\n',
        "method 'parse_num' expects 0 argument(s), got 2",
    ),
    (
        "parse_status_arity",
        'task main() {\n    say parse_status(1)\n}\n',
        "call to 'parse_status' expects 0 argument(s), got 1",
    ),
)

EMITTER_CASES: dict[str, tuple[str, list[str]]] = {
    "say_temporary": (
        'task main() {\n    say format_num(1.5)\n}\n',
        ["1.5"],
    ),
    "local_reassign": (
        'task main() {\n    pilot w = format_num(1.5)\n    say w\n    w = format_num(3.5)\n    say w\n}\n',
        ["1.5", "3.5"],
    ),
    "interpolation": (
        'task main() {\n    pilot w = format_num(1.5)\n    say "v={w}!"\n    say w\n}\n',
        ["v=1.5!", "1.5"],
    ),
    "discarded_and_nested": (
        'task main() {\n    format_num(4.5)\n    pilot n = 7\n    if n == 7 {\n        pilot inner = format_num(9.25)\n        say inner\n    }\n    say "done"\n}\n',
        ["9.25", "done"],
    ),
    "checked_parse_bootstrap": (
        'task main() {\n    say "42".parse_int()\n    say parse_status()\n    say "12a".parse_int()\n    say parse_status()\n    parse_clear_status()\n    say "1e3".parse_num()\n    say parse_status()\n    say "3.5".parse_num()\n    say parse_status()\n}\n',
        ["42", "0", "0", "1", "1000", "0", "3.5", "0"],
    ),
    "giveback_composite": (
        'task make() -> word {\n    pilot w = format_num(1.5)\n    give back w + "!"\n}\n'
        'task main() {\n    say make()\n}\n',
        ["1.5!"],
    ),
    "giveback_transfer": (
        'task make() -> word {\n    pilot w = format_num(2.5)\n    give back w\n}\n'
        'task main() {\n    say make()\n}\n',
        ["2.5"],
    ),
    "say_concat_temporary": (
        'task main() {\n    say "a" + "b"\n}\n',
        ["ab"],
    ),
    "pilot_concat_temporary": (
        'task main() {\n    pilot w = "a" + "b"\n    say w\n}\n',
        ["ab"],
    ),
    "user_word_result": (
        'task greet() -> word {\n    give back "hi"\n}\n'
        'task main() {\n    say greet()\n    pilot g = greet()\n    say g\n}\n',
        ["hi", "hi"],
    ),
    "loop_concat_accumulator": (
        'task acc(text: word) -> word {\n    pilot out = ""\n    pilot i = 0\n    repeat until i >= text.length() {\n        out = out + "z"\n        i += 1\n    }\n    give back out\n}\n'
        'task main() {\n    say acc("abcdef")\n}\n',
        ["zzzzzz"],
    ),
    "giveback_comparison": (
        'task same(a: word, b: word) -> bool {\n    give back a == b\n}\n'
        'task main() {\n    if same("x", "x") { say "true" } else { say "false" }\n'
        '    if same("x", "y") { say "true" } else { say "false" }\n}\n',
        ["true", "false"],
    ),
}


def run(
    command: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: int = 180,
) -> subprocess.CompletedProcess[str]:
    """Run a regression command and capture its decoded output."""
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def require_ok(result: subprocess.CompletedProcess[str], label: str) -> None:
    """Raise an assertion containing command output when a step fails."""
    if result.returncode:
        raise AssertionError(
            f"{label} failed ({result.returncode})\n{result.stdout}{result.stderr}"
        )


def sanitizer_env() -> dict[str, str]:
    """Return a clean environment configured for sanitizer failures."""
    env = os.environ.copy()
    env.pop("ASAN_OPTIONS", None)
    env.pop("LSAN_OPTIONS", None)
    if sys.platform.startswith("linux"):
        env["ASAN_OPTIONS"] = "halt_on_error=1:detect_leaks=1:exitcode=86"
    return env


def build_stage2(*, clang: str, repo: Path, root: Path) -> Path:
    """Rebuild an exact-current-source stage2 compiler outside the repo."""
    runtime = repo / "freakc" / "runtime"
    executable_suffix = ".exe" if sys.platform == "win32" else ""
    link_flags = ["-lws2_32"] if sys.platform == "win32" else ["-lm"]
    common = [
        "-O2",
        "-w",
        "-D_CRT_SECURE_NO_WARNINGS",
        "-I",
        str(runtime),
        *link_flags,
    ]
    aggregate = root / "freakc_v3.fk"
    aggregate.write_bytes(
        b"".join((repo / path).read_bytes() for path in COMPILER_SOURCES)
    )
    seed = root / f"freakc_seed{executable_suffix}"
    require_ok(
        run(
            [clang, "-o", str(seed), str(repo / "build/freakc_v3.fk.c"),
             str(runtime / "freak_runtime.c"), *common],
            root,
        ),
        "checked-parsing seed build",
    )
    previous = seed
    stage2: Path | None = None
    for generation in (1, 2):
        emitted = Path(str(aggregate) + ".c")
        emitted.unlink(missing_ok=True)
        require_ok(
            run([str(previous), str(aggregate), "--c"], root),
            f"checked-parsing stage{generation} emission",
        )
        stage_c = root / f"freakc_stage{generation}.c"
        shutil.copyfile(emitted, stage_c)
        stage = root / f"freakc_stage{generation}{executable_suffix}"
        require_ok(
            run(
                [clang, "-o", str(stage), str(stage_c),
                 str(runtime / "freak_runtime.c"), *common],
                root,
            ),
            f"checked-parsing stage{generation} link",
        )
        previous = stage
        stage2 = stage
    assert stage2 is not None
    return stage2


def compile_generated(
    *,
    clang: str,
    repo: Path,
    generated: Path,
    backend: str,
    binary: Path,
) -> None:
    """Link generated C or LLVM output with ownership auditing enabled."""
    runtime = repo / "freakc" / "runtime"
    command = [clang, "-g", "-O1", "-o", str(binary), str(generated)]
    if backend == "llvm":
        command.extend(
            [
                "-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1",
                str(runtime / "freak_llvm_runtime.c"),
            ]
        )
    else:
        command.append("-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1")
    command.extend([str(runtime / "freak_runtime.c"), "-I", str(runtime)])
    if sys.platform == "win32":
        command.append("-lws2_32")
    else:
        command.extend(["-lm", "-fsanitize=address", "-fno-omit-frame-pointer"])
    require_ok(run(command, repo), f"checked-parsing {backend} link")


def execute_case(
    compiler: Path, repo: Path, root: Path, backend: str, name: str
) -> dict:
    """Compile and execute one positive checked-parsing case."""
    source, expected = CASES[name]
    fixture = root / f"parse_{name}_{backend}.fk"
    fixture.write_text(source, encoding="utf-8")
    compiled = run([str(compiler), str(fixture), f"--{backend}"], root)
    require_ok(compiled, f"{name}/{backend} emission")
    generated = Path(str(fixture) + (".c" if backend == "c" else ".ll"))
    assert generated.is_file(), f"missing generated artifact: {generated}"
    generated_text = generated.read_text(encoding="utf-8")
    if backend == "c":
        if ".parse_int(" in source:
            assert "freak_word_parse_int(" in generated_text, (name, backend)
        if ".parse_num(" in source:
            assert "freak_word_parse_num(" in generated_text, (name, backend)
        if "parse_status" in source or "parse_clear_status" in source:
            assert "freak_parse_status" in generated_text, (name, backend)
        if name == "legacy_untouched":
            assert "freak_word_to_int(" in generated_text, (name, backend)
            assert "freak_word_to_num(" in generated_text, (name, backend)
            assert "freak_word_parse_" not in generated_text, (name, backend)
    else:
        if ".parse_int(" in source:
            assert "@freak_llvm_word_parse_int" in generated_text, (name, backend)
        if ".parse_num(" in source:
            assert "@freak_llvm_word_parse_num" in generated_text, (name, backend)
        if "parse_status" in source or "parse_clear_status" in source:
            assert "freak_parse_status" in generated_text, (name, backend)
        if name == "legacy_untouched":
            assert "@freak_llvm_word_to_int" in generated_text, (name, backend)
            # The shared prelude declares every runtime entry; only a call
            # instruction proves the backend selected the parse routine.
            assert "call i64 @freak_llvm_parse_num" in generated_text, (name, backend)
            # The shared prelude declares every runtime entry; only calls
            # prove selection, so gate on call instructions here.
            assert "call i64 @freak_llvm_word_parse" not in generated_text, (
                name, backend,
            )
    binary = root / (
        f"parse_{name}_{backend}.exe"
        if sys.platform == "win32"
        else f"parse_{name}_{backend}"
    )
    compile_generated(
        clang=os.environ.get("FREAK_CLANG") or shutil.which("clang") or "clang",
        repo=repo,
        generated=generated,
        backend=backend,
        binary=binary,
    )
    executed = run([str(binary)], root, sanitizer_env())
    require_ok(executed, f"{name}/{backend} execution")
    assert "ownership audit found" not in executed.stderr, (
        name, backend, executed.stderr,
    )
    assert "AddressSanitizer" not in executed.stderr, (
        name, backend, executed.stderr,
    )
    actual = executed.stdout.splitlines()
    assert actual == expected, (
        f"{name}/{backend}: expected {expected!r}, got {actual!r}\n"
        f"{executed.stderr}"
    )
    return {"case": name, "backend": backend, "output": actual}


def execute_negative(
    compiler: Path, root: Path, backend: str, name: str
) -> dict:
    """Verify one invalid parsing program is rejected before emission."""
    for case_name, source, diagnostic in NEGATIVES:
        if case_name != name:
            continue
        fixture = root / f"parse_negative_{name}_{backend}.fk"
        fixture.write_text(source, encoding="utf-8")
        compiled = run([str(compiler), str(fixture), f"--{backend}"], root)
        assert compiled.returncode != 0, (name, backend, "emission accepted")
        combined = compiled.stdout + compiled.stderr
        assert diagnostic in combined, (name, backend, combined)
        return {"case": name, "backend": backend, "diagnostic": diagnostic}
    raise AssertionError(f"unknown negative case: {name}")


def execute_emitter_case(repo: Path, root: Path, name: str) -> dict:
    """Compile and run one bootstrap-emitter behavioral regression."""
    from freakc.__main__ import transpile_checked

    source, expected = EMITTER_CASES[name]
    path = root / f"emitter_{name}.fk"
    path.write_text(source, encoding="utf-8")
    c_source, diags, _, has_errors = transpile_checked(source, path)
    assert not has_errors, (name, diags)
    assert c_source, (name, "no C emitted")
    # Behavioral cases only: the bootstrap emitter intentionally does not
    # free owned locals (V4 query caches and other global stores retain
    # aliases past scope end), so pin values here, never release emission.
    generated = root / f"emitter_{name}.c"
    generated.write_text(c_source, encoding="utf-8")
    runtime = repo / "freakc" / "runtime"
    binary = root / (
        f"emitter_{name}.exe" if sys.platform == "win32" else f"emitter_{name}"
    )
    clang = os.environ.get("FREAK_CLANG") or shutil.which("clang") or "clang"
    command = [
        clang, "-g", "-O1",
        "-o", str(binary), str(generated), str(runtime / "freak_runtime.c"),
        "-I", str(runtime),
    ]
    if sys.platform == "win32":
        command.append("-lws2_32")
    else:
        command.extend(["-lm", "-fsanitize=address", "-fno-omit-frame-pointer"])
    require_ok(run(command, repo), f"emitter {name} link")
    executed = run([str(binary)], root, sanitizer_env())
    require_ok(executed, f"emitter {name} execution")
    assert "AddressSanitizer" not in executed.stderr, (name, executed.stderr)
    actual = executed.stdout.splitlines()
    assert actual == expected, (
        f"emitter {name}: expected {expected!r}, got {actual!r}\n"
        f"{executed.stderr}"
    )
    return {"case": f"emitter/{name}", "output": actual}


def main() -> int:
    """Run the selected checked-parsing regression matrix."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "compiler",
        nargs="?",
        type=Path,
        help="fresh stage2 compiler (omit to rebuild one outside the repo)",
    )
    parser.add_argument("--case", choices=[*CASES, *EMITTER_CASES])
    parser.add_argument("--backend", choices=("c", "llvm"))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    clang = os.environ.get("FREAK_CLANG") or shutil.which("clang")
    assert clang, "clang is required for the checked-parsing regression"
    backends = [args.backend] if args.backend else ["c", "llvm"]
    records: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="freak-w5-checked-parsing-") as tmp:
        root = Path(tmp)
        compiler: Path | None = None
        selected_native = [
            name for name in CASES if args.case is None or args.case == name
        ]
        selected_emitter = [
            name for name in EMITTER_CASES
            if args.case is None or args.case == name
        ]
        if selected_native:
            compiler = (
                args.compiler.resolve()
                if args.compiler is not None
                else build_stage2(clang=clang, repo=repo, root=root)
            )
            assert compiler.is_file(), compiler
        for backend in backends:
            for name in selected_native:
                print(f"RUN {name}/{backend}", flush=True)
                records.append(execute_case(compiler, repo, root, backend, name))
                print(f"PASS {name}/{backend}", flush=True)
            for negative, _, _ in NEGATIVES:
                if args.case is not None:
                    continue
                print(f"RUN negative/{negative}/{backend}", flush=True)
                records.append(execute_negative(compiler, root, backend, negative))
                print(f"PASS negative/{negative}/{backend}", flush=True)
        for name in selected_emitter:
            if args.backend is not None:
                continue
            print(f"RUN emitter/{name}", flush=True)
            records.append(execute_emitter_case(repo, root, name))
            print(f"PASS emitter/{name}", flush=True)
    if args.report:
        args.report.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(f"V3 checked parsing: PASS ({len(records)} executions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
