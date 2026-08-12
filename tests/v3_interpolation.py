#!/usr/bin/env python3
"""Executable contracts for V3 path-only string interpolation."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


CORE_PROGRAM = '''pilot global_word: word = "global"
pilot global_int: int = 7
pilot global_num: num = 2.5
pilot global_bool: bool = true
pilot global_rendered: word = "global={global_word}|{global_int}|{global_num}|{global_bool}"

task from_params(label: word, count: int, ratio: num, ready: bool) -> word {
    pilot stored: word = "param={label}|{count}|{ratio}|{ready}"
    give back stored
}

task return_direct(label: word) -> word {
    give back "return={label}"
}

task local_shadow() -> word {
    pilot global_word: word = "local"
    give back "local={global_word}"
}

task param_shadow(global_word: word) -> word {
    give back "param-shadow={global_word}"
}

task main() {
    say "direct={global_word}|{global_int}|{global_num}|{global_bool}"
    say global_rendered
    pilot mut stored: word = "stored={global_word}|{global_int}"
    say stored
    stored = "assigned={global_num}|{global_bool}"
    say stored
    say from_params("argument", 9, 1.25, false)
    say return_direct("fresh")
    say local_shadow()
    say param_shadow("parameter")
}
'''

CORE_OUTPUT = [
    "direct=global|7|2.5|true",
    "global=global|7|2.5|true",
    "stored=global|7",
    "assigned=2.5|true",
    "param=argument|9|1.25|false",
    "return=fresh",
    "local=local",
    "param-shadow=parameter",
]

LITERAL_PROGRAM = '''task main() {
    pilot code: int = 7
    say "{}"
    say "{\\"kind\\":\\"object\\"}"
    say "!{}"
    say "code { if (x) { y } }"
    say "{score + 1}"
    say "{ name }"
    say "{true}"
    say "{TRUE}"
    say "{if}"
    say "{Task}"
    say "unmatched {name"
    say "<<PIPE>>"
    say "\\x41{code}\\x42"
    say "z\\x41{code}q\\x42"
    say "\\x41BC{code}"
}
'''

LITERAL_OUTPUT = [
    "{}",
    '{"kind":"object"}',
    "!{}",
    "code { if (x) { y } }",
    "{score + 1}",
    "{ name }",
    "{true}",
    "{TRUE}",
    "{if}",
    "{Task}",
    "unmatched {name",
    "<<PIPE>>",
    "A7B",
    "zA7qB",
    "ABC7",
]

SHAPE_PROGRAM = '''shape Profile {
    name: word
    score: int
}

impl Profile {
    task label(self) -> word {
        pilot stored: word = "self={self.name}:{self.score}"
        give back stored
    }
}

task main() {
    pilot profile: Profile = Profile { name: "Ami", score: 42 }
    say "shape={profile.name}:{profile.score}"
    say profile.label()
}
'''

OWNERSHIP_PROGRAM = '''task main() {
    pilot mut rendered: word = "start"
    pilot count: int = 17
    pilot ready: bool = true
    repeat 512 times {
        rendered = "owned={count}:{ready}"
    }
    say "{rendered}|{rendered}|{count}|{ready}"
}
'''

NEGATIVE_PROGRAMS = {
    "unknown": '''task main() {
    say "bad={missing}"
}
''',
    "non_shape": '''task main() {
    pilot value: int = 1
    say "bad={value.field}"
}
''',
    "missing_field": '''shape Box { value: int }
task main() {
    pilot box: Box = Box { value: 1 }
    say "bad={box.missing}"
}
''',
    "unsupported_terminal": '''shape Box { value: int }
task main() {
    pilot box: Box = Box { value: 1 }
    say "bad={box}"
}
''',
}

NEGATIVE_DIAGNOSTICS = {
    "unknown": "unknown interpolation binding 'missing'",
    "non_shape": "interpolation path crosses non-shape value before field 'field'",
    "missing_field": "shape 'Box' has no field 'missing'",
    "unsupported_terminal": (
        "interpolation path must end in word, int, num, or bool, got Box"
    ),
}

NEGATIVE_LINES = {
    "unknown": 2,
    "non_shape": 3,
    "missing_field": 4,
    "unsupported_terminal": 4,
}


def run(
    command: list[str],
    cwd: Path,
    env: dict[str, str],
    timeout: int = 180,
) -> subprocess.CompletedProcess[str]:
    """
    Run a subprocess and capture its text output.
    
    Parameters:
    	command (list[str]): The command and its arguments.
    	cwd (Path): The working directory for the subprocess.
    	env (dict[str, str]): Environment variables for the subprocess.
    	timeout (int): Maximum execution time in seconds.
    
    Returns:
    	subprocess.CompletedProcess[str]: The completed process result, including its exit status, standard output, and standard error.
    """
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


def assert_ok(result: subprocess.CompletedProcess[str], label: str) -> None:
    """
    Require a subprocess result to indicate successful completion.
    
    Parameters:
    	result (subprocess.CompletedProcess[str]): The completed subprocess result to verify.
    	label (str): A label identifying the subprocess in failure messages.
    """
    assert result.returncode == 0, (
        f"{label} failed ({result.returncode})\n{result.stdout}{result.stderr}"
    )


def binary_for(source: Path) -> Path:
    """Return the platform-specific executable path for a source path.
    
    Parameters:
    	source (Path): Path whose suffix is replaced with the platform executable suffix.
    
    Returns:
    	Path: Executable path ending in `.exe` on Windows and no suffix on other platforms.
    """
    return source.with_suffix(".exe" if sys.platform == "win32" else "")


def execute(binary: Path, cwd: Path, env: dict[str, str]) -> list[str]:
    """
    Run a compiled test binary and return its output lines.
    
    Parameters:
    	binary (Path): Path to the executable binary.
    	cwd (Path): Working directory for the execution.
    	env (dict[str, str]): Environment variables used by the process.
    
    Returns:
    	list[str]: Lines written to standard output.
    """
    result = run([str(binary)], cwd, env)
    assert_ok(result, f"execute {binary.name}")
    assert "ownership audit found" not in result.stderr.lower(), result.stderr
    assert "AddressSanitizer" not in result.stderr, result.stderr
    return result.stdout.splitlines()


def compile_generated(
    *,
    clang: str,
    repo: Path,
    generated: Path,
    backend: str,
    output: Path,
    env: dict[str, str],
) -> None:
    """
    Compile generated C or LLVM output with the runtime and ownership-audit settings required by the test.
    """
    command = [
        clang,
        "-g",
        "-O1",
        "-o",
        str(output),
        str(generated),
        (
            "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1"
            if backend == "c"
            else "-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1"
        ),
        "-DFREAK_WORD_CONCAT_FORCE_MOVE=1",
    ]
    if backend == "llvm":
        command.append(str(repo / "freakc" / "runtime" / "freak_llvm_runtime.c"))
    command.extend(
        [
            str(repo / "freakc" / "runtime" / "freak_runtime.c"),
            "-I",
            str(repo / "freakc" / "runtime"),
        ]
    )
    if sys.platform == "win32":
        command.append("-lws2_32")
    else:
        command.extend(["-lm", "-fsanitize=address", "-fno-omit-frame-pointer"])
    assert_ok(run(command, repo, env), f"compile {backend} ownership probe")


def build_and_run(
    *,
    freak: Path,
    repo: Path,
    source: Path,
    backend: str,
    flag: str,
    expected: list[str],
    env: dict[str, str],
) -> None:
    """Build a source program for the specified backend and verify its runtime output.
    
    Parameters:
        freak (Path): Path to the compiler executable.
        repo (Path): Repository working directory for the build command.
        source (Path): Source file to build and execute.
        backend (str): Backend name used in failure descriptions.
        flag (str): Backend-specific build flag.
        expected (list[str]): Expected output lines.
        env (dict[str, str]): Environment variables for the build and execution.
    
    Raises:
        AssertionError: If the build fails or the executable output differs from the expected output.
    """
    built = run([str(freak), "build", str(source), flag], repo, env)
    assert_ok(built, f"{backend} build {source.name}")
    assert execute(binary_for(source), source.parent, env) == expected


def assert_negative(
    result: subprocess.CompletedProcess[str],
    *,
    label: str,
    diagnostic: str,
    source: Path,
    line: int,
) -> None:
    """
    Validate a failed compilation result against its expected diagnostic and source location.
    
    Parameters:
        result (subprocess.CompletedProcess[str]): The completed compilation process.
        label (str): Label used in assertion failure messages.
        diagnostic (str): Required diagnostic text.
        source (Path): Source file expected in the diagnostic location.
        line (int): Expected source line for the diagnostic.
    """
    output = result.stdout + result.stderr
    normalized = output.replace("\\", "/")
    assert result.returncode != 0, f"{label} unexpectedly passed\n{output}"
    assert diagnostic in output, f"{label} missed diagnostic\n{output}"
    assert normalized.count("type error") == 1, (
        f"{label} emitted duplicate type diagnostics\n{output}"
    )
    assert f"/{source.name}:{line}:" in normalized, (
        f"{label} lost string-token line provenance\n{output}"
    )


def assert_absent(paths: list[Path], label: str) -> None:
    """
    Ensure that none of the specified artifact paths exist.
    
    Parameters:
    	paths (list[Path]): Paths that must be absent.
    	label (str): Description used in the failure message.
    """
    leftovers = [path for path in paths if path.exists()]
    assert not leftovers, f"{label} left artifacts: {leftovers}"


def main() -> int:
    """
    Run the V3 interpolation test suite across supported compiler backends.
    
    Returns:
    	int: 0 after all interpolation, ownership, diagnostic, and artifact checks pass.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("freak", type=Path)
    parser.add_argument("--freakc", type=Path)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    freak = args.freak.resolve()
    assert freak.is_file(), freak
    compiler_suffix = ".exe" if sys.platform == "win32" else ""
    direct = args.freakc
    if direct is None:
        direct = freak.parent / f"freakc_v3_stage2{compiler_suffix}"
    direct = direct.resolve()
    assert direct.is_file(), f"current direct V3 compiler is required: {direct}"

    configured_clang = os.environ.get("FREAK_CLANG", "clang")
    clang = shutil.which(configured_clang)
    assert clang, f"Clang not found: {configured_clang}"
    env = os.environ.copy()
    env["NO_COLOR"] = "1"
    env.pop("FREAK_HOME", None)
    env.pop("ASAN_OPTIONS", None)
    env.pop("LSAN_OPTIONS", None)
    if sys.platform != "win32":
        env["ASAN_OPTIONS"] = "halt_on_error=1"
        if sys.platform.startswith("linux"):
            env["ASAN_OPTIONS"] += ":detect_leaks=1"
            env["LSAN_OPTIONS"] = "exitcode=23"

    emitter = (repo / "src" / "compiler" / "v3" / "emit_llvm.fk").read_text(
        encoding="utf-8"
    )
    assert "llvm_emit_say_interp" not in emitter
    assert "llvm_str_has_interp" not in emitter

    with tempfile.TemporaryDirectory(prefix="freak-v3-interpolation-") as tmp:
        root = Path(tmp)
        core = root / "core.fk"
        core.write_text(CORE_PROGRAM, encoding="utf-8")
        literals = root / "literals.fk"
        literals.write_text(LITERAL_PROGRAM, encoding="utf-8")

        for backend, flag, suffix in (
            ("c", "--c", ".c"),
            ("llvm", "--llvm", ".ll"),
        ):
            build_and_run(
                freak=freak,
                repo=repo,
                source=core,
                backend=backend,
                flag=flag,
                expected=CORE_OUTPUT,
                env=env,
            )
            transpiled = run(
                [str(freak), "transpile", str(core), flag], repo, env
            )
            assert_ok(transpiled, f"{backend} audit transpile {core.name}")
            generated_path = Path(str(core) + suffix)
            generated = generated_path.read_text(encoding="utf-8")
            helper_call = (
                "freak_word_append_owned("
                if backend == "c"
                else "call i64 @freak_llvm_word_append_owned("
            )
            assert helper_call in generated, (
                f"{backend} skipped the linear append helper call"
            )
            audited_core = root / (
                f"core_audit_{backend}.exe"
                if sys.platform == "win32"
                else f"core_audit_{backend}"
            )
            compile_generated(
                clang=clang,
                repo=repo,
                generated=generated_path,
                backend=backend,
                output=audited_core,
                env=env,
            )
            assert execute(audited_core, root, env) == CORE_OUTPUT
            build_and_run(
                freak=freak,
                repo=repo,
                source=literals,
                backend=backend,
                flag=flag,
                expected=LITERAL_OUTPUT,
                env=env,
            )

        shape = root / "shape.fk"
        shape.write_text(SHAPE_PROGRAM, encoding="utf-8")
        build_and_run(
            freak=freak,
            repo=repo,
            source=shape,
            backend="llvm",
            flag="--llvm",
            expected=["shape=Ami:42", "self=Ami:42"],
            env=env,
        )
        c_shape = run([str(freak), "transpile", str(shape), "--c"], repo, env)
        assert_ok(c_shape, "C dotted interpolation transpile boundary")
        assert "freak_word_append_owned" in Path(str(shape) + ".c").read_text(
            encoding="utf-8"
        )

        ownership = root / "ownership.fk"
        ownership.write_text(OWNERSHIP_PROGRAM, encoding="utf-8")
        for backend, flag, suffix in (
            ("c", "--c", ".c"),
            ("llvm", "--llvm", ".ll"),
        ):
            transpiled = run(
                [str(freak), "transpile", str(ownership), flag], repo, env
            )
            assert_ok(transpiled, f"{backend} ownership transpile")
            generated = Path(str(ownership) + suffix)
            audited = root / (
                f"ownership_{backend}.exe"
                if sys.platform == "win32"
                else f"ownership_{backend}"
            )
            compile_generated(
                clang=clang,
                repo=repo,
                generated=generated,
                backend=backend,
                output=audited,
                env=env,
            )
            assert execute(audited, root, env) == ["owned=17:true|owned=17:true|17|true"]

        for name, program in NEGATIVE_PROGRAMS.items():
            source = root / f"negative_{name}.fk"
            source.write_text(program, encoding="utf-8")
            diagnostic = NEGATIVE_DIAGNOSTICS[name]
            line = NEGATIVE_LINES[name]
            artifacts = [
                Path(str(source) + ".c"),
                Path(str(source) + ".ll"),
                binary_for(source),
            ]
            for artifact in artifacts:
                artifact.unlink(missing_ok=True)
            checked = run([str(freak), "check", str(source)], repo, env)
            assert_negative(
                checked,
                label=f"check {name}",
                diagnostic=diagnostic,
                source=source,
                line=line,
            )
            assert_absent(artifacts, f"check {name}")
            for backend, flag in (("c", "--c"), ("llvm", "--llvm")):
                for command in ("transpile", "build"):
                    for artifact in artifacts:
                        artifact.unlink(missing_ok=True)
                    rejected = run(
                        [str(freak), command, str(source), flag], repo, env
                    )
                    assert_negative(
                        rejected,
                        label=f"{backend} {command} {name}",
                        diagnostic=diagnostic,
                        source=source,
                        line=line,
                    )
                    assert_absent(artifacts, f"{backend} {command} {name}")

                direct_artifact = Path(
                    str(source) + (".c" if backend == "c" else ".ll")
                )
                direct_artifact.unlink(missing_ok=True)
                direct_result = run(
                    [str(direct), str(source), flag], repo, env
                )
                assert_negative(
                    direct_result,
                    label=f"direct {backend} {name}",
                    diagnostic=diagnostic,
                    source=source,
                    line=line,
                )
                assert_absent([direct_artifact], f"direct {backend} {name}")

    print("V3 interpolation expression/backends/ownership gate: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
