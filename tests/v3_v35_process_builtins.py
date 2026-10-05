#!/usr/bin/env python3
"""Check native compiler process-ticket signatures and C/LLVM call emission.

This gate does not claim child-process execution proof. Runtime execution,
cleanup, and native-host parity are verified by the process runtime gate.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import tempfile

from v3_checked_parsing import build_stage2
from v3_v35_language import require_ok, run


PROGRAM = '''task main() {
    pilot native_platform: word = process::platform_name()
    pilot terminal: bool = process::stdout_is_terminal()
    pilot windows: bool = process::platform_is_windows()
    pilot executable: word = process::executable_path()
    pilot job: int = process::command_new("native helper")
    process::command_arg(job, "literal $ & % argument")
    process::command_cwd(job, "directory with spaces")
    process::command_env(job, "TEST_NAME", "value")
    process::command_unset_env(job, "INHERITED_NAME")
    pilot spawn: int = process::command_spawn(job, 1000, 4096, 4096)
    pilot state: int = process::command_run(job, 1000, 4096, 4096)
    pilot inherited: int = process::command_spawn_inherit(job, 1000)
    pilot inherited_run: int = process::command_run_inherit(job, 1000)
    say process::command_wait(job)
    say process::command_poll(job)
    say process::command_status(job)
    say process::command_exit_code(job)
    say process::command_signal(job)
    pilot error: word = process::command_error(job)
    pilot output: word = process::command_stdout(job)
    pilot diagnostic: word = process::command_stderr(job)
    pilot bytes: ByteBuffer = process::command_stdout_bytes(job)
    pilot errors: ByteBuffer = process::command_stderr_bytes(job)
    say bytes.length()
    say errors.length()
    bytes.release()
    errors.release()
    process::command_terminate(job)
    process::command_release(job)
}
'''

# Kept as an independent API inventory: emitted calls must match each public
# operation, including argument-vector and byte-output paths.
OPERATIONS = (
    "new", "arg", "cwd", "env", "unset_env", "spawn", "run", "spawn_inherit", "run_inherit",
    "wait", "poll", "status", "exit_code", "signal", "error", "stdout", "stderr",
    "stdout_bytes", "stderr_bytes", "terminate", "release",
)

NEGATIVE = {
    "platform_name_type": (
        'pilot platform: int = process::platform_name()',
        "cannot initialize int binding 'platform' with word", False,
    ),
    "platform_name_arity": (
        'process::platform_name(1)', "expects 0 argument(s), got 1", False,
    ),
    "terminal_is_bool": (
        'pilot terminal: int = process::stdout_is_terminal()',
        "cannot initialize int binding 'terminal' with bool", False,
    ),
    "terminal_arity": (
        'process::stdout_is_terminal(1)', "expects 0 argument(s), got 1", False,
    ),
    "platform_is_bool": (
        'pilot platform: int = process::platform_is_windows()',
        "cannot initialize int binding 'platform' with bool", False,
    ),
    "platform_arity": (
        'process::platform_is_windows(1)', "expects 0 argument(s), got 1", False,
    ),
    "path_is_word": (
        'pilot path: int = process::executable_path()',
        "cannot initialize int binding 'path' with word", False,
    ),
    "path_arity": (
        'process::executable_path("path")', "expects 0 argument(s), got 1", False,
    ),
    "path_is_owned": (
        'pilot path = process::executable_path()\n'
        'pilot alias = path\nsay path', "You gave this away", True,
    ),
    "inferred_payload_release": (
        'pilot bytes = process::command_stdout_bytes(1)\nbytes.release()\nbytes.length()',
        "You gave this away", True,
    ),
    "poll_ticket_type": ('process::command_poll("ticket")', "argument 1 expects int, got word", False),
    "executable_type": ('process::command_new(1)', "argument 1 expects word, got int", False),
    "environment_arity": (
        'process::command_env(1, "KEY")', "expects 3 argument(s), got 2", False,
    ),
    "capture_limit_type": (
        'process::command_run(1, 1000, "4096", 4096)',
        "argument 3 expects int, got word", False,
    ),
    "getter_ticket_type": (
        'process::command_stdout("ticket")', "argument 1 expects int, got word", False,
    ),
    "unsupported_prefix": (
        'process::command_magic(1)', "unknown callable 'process::command_magic'", False,
    ),
    "released_ticket": (
        'pilot job: int = process::command_new("helper")\n'
        'process::command_release(job)\nprocess::command_status(job)',
        "You gave this away", True,
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", type=Path, help="fresh exact-source native stage2 compiler")
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG") or shutil.which("clang"))
    args = parser.parse_args()
    assert args.clang, "Clang is required for native source reconstruction"
    repo = Path(__file__).resolve().parents[1]
    inventory = []
    with tempfile.TemporaryDirectory(prefix="freak-v35-process-compiler-") as directory:
        root = Path(directory)
        compiler = (
            args.compiler.resolve(strict=True) if args.compiler
            else build_stage2(clang=args.clang, repo=repo, root=root)
        )
        for backend in ("c", "llvm"):
            source = root / f"process_api_{backend}.fk"
            source.write_text(PROGRAM, encoding="utf-8")
            require_ok(run([str(compiler), str(source), f"--{backend}", "--strict-borrow"], root), backend)
            suffix = ".c" if backend == "c" else ".ll"
            emitted = Path(str(source) + suffix).read_text(encoding="utf-8")
            prefix = "freak_process_command_" if backend == "c" else "@freak_llvm_process_command_"
            terminal_symbol = "freak_process_stdout_is_terminal" if backend == "c" else "@freak_llvm_process_stdout_is_terminal"
            assert terminal_symbol + "(" in emitted, (backend, "stdout_is_terminal", emitted)
            if backend == "llvm":
                assert any("call " in line and terminal_symbol + "(" in line for line in emitted.splitlines()), (backend, "stdout_is_terminal", emitted)
            name_symbol = "freak_process_platform_name" if backend == "c" else "@freak_llvm_process_platform_name"
            assert name_symbol + "(" in emitted, (backend, "platform_name", emitted)
            if backend == "llvm":
                assert any("call " in line and name_symbol + "(" in line for line in emitted.splitlines()), (backend, "platform_name", emitted)
            platform_symbol = "freak_process_platform_is_windows" if backend == "c" else "@freak_llvm_process_platform_is_windows"
            assert platform_symbol + "(" in emitted, (backend, "platform_is_windows", emitted)
            if backend == "llvm":
                assert any("call " in line and platform_symbol + "(" in line for line in emitted.splitlines()), (backend, "platform_is_windows", emitted)
            path_symbol = "freak_process_executable_path" if backend == "c" else "@freak_llvm_process_executable_path"
            assert path_symbol + "(" in emitted, (backend, "executable_path", emitted)
            if backend == "llvm":
                assert any("call " in line and path_symbol + "(" in line for line in emitted.splitlines()), (backend, "executable_path", emitted)
            for operation in OPERATIONS:
                symbol = prefix + operation
                assert symbol + "(" in emitted, (backend, operation, emitted)
                if backend == "llvm":
                    # A declaration alone is insufficient: the actual call
                    # also must select the frozen runtime symbol.
                    assert any("call " in line and symbol + "(" in line for line in emitted.splitlines()), (
                        backend, operation, emitted,
                    )
            assert "__freak_user_process_command_" not in emitted, emitted
            inventory.append((backend, "positive"))
            print(f"PASS {backend} process API emission", flush=True)
            for name, (body, diagnostic, strict) in NEGATIVE.items():
                source = root / f"{name}_{backend}.fk"
                source.write_text("task main() {\n" + body + "\n}\n", encoding="utf-8")
                artifact = Path(str(source) + suffix)
                artifact.write_text("stale process output", encoding="utf-8")
                command = [str(compiler), str(source), f"--{backend}"]
                if strict:
                    command.append("--strict-borrow")
                result = run(command, root)
                output = result.stdout + result.stderr
                assert result.returncode != 0, (backend, name, output)
                assert diagnostic in output, (backend, name, diagnostic, output)
                assert not artifact.exists(), (backend, name, "stale artifact survived")
                inventory.append((backend, name))
                print(f"PASS {backend} {name}", flush=True)
    expected = {(backend, name) for backend in ("c", "llvm") for name in ("positive", *NEGATIVE)}
    assert set(inventory) == expected and len(inventory) == len(expected)
    print(f"V3.5 process compiler contracts: PASS ({len(inventory)} cases)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
