#!/usr/bin/env python3
"""Prove repeated V3 word replacement releases superseded allocations."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


PROGRAM = """task identity(value: word) -> word {
    give back value
}

task observe(value: word) {
    pilot length = value.length()
}

task measure(value: word) -> int {
    give back value.length()
}

pilot mut global_owner: word = "g" + "lobal"
pilot mut global_alias: word = global_owner
pilot mut shadow_owner: word = "s" + "hadow"

task observe_shadow(shadow_owner: word) {
    pilot length = shadow_owner.length()
    say shadow_owner
}

task main() {
    pilot mut text: word = "a"
    repeat 512 times {
        text = text + "x"
    }
    text = text
    text = "done"
    say text
    pilot mut moved: word = "x" + "y"
    pilot mut alias: word = moved
    moved = "z"
    say alias
    alias = "released"
    pilot mut called: word = "c" + "all"
    pilot mut returned: word = identity(called)
    called = "reinitialized"
    say returned
    returned = "released"
    pilot mut measured_word: word = "m" + "easure"
    pilot measured = measure(measured_word)
    if measured != 7 { say "bad measure" }
    measured_word = "released"
    pilot mut observed: word = "o" + "bserve"
    repeat 128 times {
        observe(observed)
    }
    observed = "released"
    repeat 128 times {
        observe("r" + "value")
    }
    pilot mut shadow_arg: word = "a" + "rg"
    observe_shadow(shadow_arg)
    shadow_arg = "released"
    say shadow_owner
    shadow_owner = "released"
    global_owner = "reinitialized"
    say global_alias
    global_alias = "released"
    pilot mut scoped: word = "o" + "uter"
    if true {
        pilot scoped: int = 7
        if scoped == 7 { say "inner" }
    }
    say scoped
    scoped = scoped + "!"
    say scoped
    scoped = "released"
}
"""

AGGREGATE_PROGRAM = """task store(items: int, value: word) {
    array_push(items, value)
}

task main() {
    pilot items = array_new()
    pilot mut item: word = "h" + "i"
    array_push(items, item)
    item = "new"
    say array_get(items, 0)
    pilot mut extracted: word = array_get(items, 0)
    say extracted
    extracted = "released"
    say array_get(items, 0)
    repeat 128 times {
        array_set(items, 0, "x" + "y")
    }
    say array_get(items, 0)
    array_release(items)
    pilot stored_items = array_new()
    pilot mut stored_value: word = "s" + "tored"
    store(stored_items, stored_value)
    stored_value = "new"
    say array_get(stored_items, 0)
    array_release(stored_items)
    pilot joined_items = array_new()
    array_push(joined_items, "j" + "o")
    array_push(joined_items, "i" + "n")
    pilot mut joined: word = word_join(joined_items)
    say joined
    joined = "released"
    pilot literal_items = ["array", "lit" + "eral"]
    say array_get(literal_items, 1)
    array_release(literal_items)
}
"""

GLOBAL_RETURN_PROGRAM = """pilot mut global_owner: word = "g" + "lobal"

task get_global_owner() -> word {
    give back global_owner
}

task main() {
    pilot mut returned_global: word = get_global_owner()
    global_owner = "reinitialized"
    say returned_global
    returned_global = "released"
}
"""

GLOBAL_CALL_PROGRAM = """pilot mut global_owner: word = "g" + "lobal"

task shadow_global_type(global_owner: int) {
    pilot copy = global_owner
}

task shadow_global_local() {
    pilot global_owner: int = 7
    if global_owner == 7 { say "local" }
}

task observe(value: word) {
    pilot length = value.length()
}

task main() {
    shadow_global_local()
    observe(global_owner)
    say global_owner
    global_owner = "released"
}
"""

RETURN_SHADOW_PROGRAM = """pilot mut returned_word: word = "g" + "lobal"

task return_local_shadow() -> word {
    pilot returned_word: word = "l" + "ocal"
    give back returned_word
}

task return_param_shadow(returned_word: word) -> word {
    if true {
        pilot returned_word: word = "i" + "nner"
        give back returned_word
    }
    give back "fallback"
}

task main() {
    pilot mut local_result: word = return_local_shadow()
    say local_result
    local_result = "released"
    pilot mut argument: word = "a" + "rg"
    pilot mut inner_result: word = return_param_shadow(argument)
    argument = "released"
    say inner_result
    inner_result = "released"
    say returned_word
    returned_word = "released"
}
"""

SHADOW_COPY_PROGRAM = """pilot mut copied: word = "g" + "lobal"

task copy_global_shadow() -> word {
    pilot copied: word = copied
    give back copied
}

task copy_param_shadow(copied: word) -> word {
    pilot copied: word = copied
    give back copied
}

task main() {
    pilot mut global_copy: word = copy_global_shadow()
    copied = "released"
    say global_copy
    global_copy = "released"
    pilot mut argument: word = "p" + "aram"
    pilot mut param_copy: word = copy_param_shadow(argument)
    argument = "released"
    say param_copy
    param_copy = "released"
}
"""

METHOD_SHAPE_PROGRAM = """shape Counter {
    value: int
}

shape Message {
    code: int
    value: word
}

shape Trailer {
    first: int
    second: int
    value: int
}

impl Message {
    task observe(self, value: word) {
        pilot length = value.length()
    }

    task store_value(self, value: word) {
        self.value = value
    }
}

pilot message = Message { code: 7, value: "initial" }

task get_message() -> Message {
    give back message
}

task read_message(value: Message) -> word {
    give back value.value
}

task main() {
    pilot mut replacement: word = "x" + "y"
    message.value = replacement
    replacement = "released"
    say message.value
    pilot mut extracted: word = message.value
    message.value = "replaced"
    say extracted
    extracted = "released"
    pilot mut method_value: word = "m" + "ethod"
    message.observe(method_value)
    method_value = "new"
    say method_value
    message.observe("r" + "value")
    message.value = "f" + "ield"
    message.observe(message.value)
    say message.value
    pilot mut self_value: word = "s" + "elf"
    message.store_value(self_value)
    self_value = "released"
    say message.value
    pilot returned_message: Message = get_message()
    pilot mut read_value: word = read_message(returned_message)
    say read_value
    read_value = "released"
    message.value = "released"
}
"""


def run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=180,
        check=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("freak", type=Path)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    freak = args.freak.resolve()
    assert freak.is_file(), freak

    with tempfile.TemporaryDirectory(prefix="freak-v3-word-ownership-") as tmp:
        root = Path(tmp)
        cases = (
            ("strict", PROGRAM, ["--strict-borrow"], ["done", "xy", "call", "arg", "shadow", "global", "inner", "outer", "outer!"], ("c", "llvm")),
            ("global_return", GLOBAL_RETURN_PROGRAM, [], ["global"], ("c", "llvm")),
            ("global_call", GLOBAL_CALL_PROGRAM, [], ["local", "global"], ("c", "llvm")),
            ("return_shadow", RETURN_SHADOW_PROGRAM, [], ["local", "inner", "global"], ("c", "llvm")),
            ("shadow_copy", SHADOW_COPY_PROGRAM, [], ["global", "param"], ("c", "llvm")),
            ("aggregate", AGGREGATE_PROGRAM, [], ["hi", "hi", "hi", "xy", "stored", "join", "literal"], ("c", "llvm")),
            ("method_shape", METHOD_SHAPE_PROGRAM, [], ["xy", "xy", "new", "field", "self", "self"], ("llvm",)),
        )
        for case_name, program, extra_flags, expected_output, backends in cases:
            source = root / f"replace_owned_{case_name}.fk"
            source.write_text(program, encoding="utf-8")
            for backend, flag, suffix in (("c", "--c", ".c"), ("llvm", "--llvm", ".ll")):
                if backend not in backends:
                    continue
                transpiled = run([str(freak), "transpile", str(source), flag, *extra_flags], repo)
                assert transpiled.returncode == 0, transpiled.stdout + transpiled.stderr
                generated = Path(str(source) + suffix)
                assert generated.is_file(), generated
                generated_text = generated.read_text(encoding="utf-8")
                if backend == "c":
                    assert "freak_word_replace_owned" in generated_text
                    if case_name == "strict":
                        assert "freak_word_clone(moved)" in generated_text
                        assert "freak_identity(freak_word_clone(called))" in generated_text
                        assert "freak_observe(freak_word_clone(observed))" in generated_text
                        assert "freak_observe(freak_word_concat(" in generated_text
                        assert "freak_observe_shadow(freak_word_clone(shadow_arg))" in generated_text
                        assert "global_alias = freak_word_clone(global_owner)" in generated_text
                        assert "freak_word_release_owned(&__freak_param_value)" in generated_text
                    elif case_name == "aggregate":
                        assert "freak_array_push_owned(items, freak_word_clone(item))" in generated_text
                        assert "freak_array_set_owned(items, 0, freak_word_concat(" in generated_text
                        assert "freak_array_release_owned(items)" in generated_text
                        assert "freak_word_join_owned(joined_items)" in generated_text
                        assert "({ int64_t __arr = freak_array_new();" in generated_text
                        assert "freak_array_push_owned(__arr, freak_word_concat(" in generated_text
                        assert "freak_array_get" in generated_text
                    elif case_name == "global_call":
                        assert "freak_observe(freak_word_clone(global_owner))" in generated_text
                    elif case_name == "global_return":
                        assert "__freak_return_value = freak_word_clone(global_owner)" in generated_text
                    elif case_name == "return_shadow":
                        assert "freak_return_local_shadow" in generated_text
                        assert "freak_return_param_shadow" in generated_text
                else:
                    assert "@freak_llvm_word_release_replaced" in generated_text
                    assert "@freak_llvm_word_clone" in generated_text

                binary = root / (f"replace_owned_{case_name}_{backend}.exe" if sys.platform == "win32" else f"replace_owned_{case_name}_{backend}")
                if sys.platform == "win32":
                    built = run([str(freak), "build", str(source), flag, *extra_flags], repo)
                    assert built.returncode == 0, built.stdout + built.stderr
                    produced = source.with_suffix(".exe")
                    shutil.copy2(produced, binary)
                else:
                    clang = os.environ.get("FREAK_CLANG") or shutil.which("clang")
                    assert clang, "clang is required for the ownership sanitizer regression"
                    command = [
                        clang,
                        "-g",
                        "-O1",
                        "-fsanitize=address",
                        "-fno-omit-frame-pointer",
                        "-o",
                        str(binary),
                        str(generated),
                    ]
                    if backend == "llvm":
                        command.append("-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1")
                        command.extend(
                            [
                                str(repo / "freakc" / "runtime" / "freak_llvm_runtime.c"),
                                str(repo / "freakc" / "runtime" / "freak_runtime.c"),
                            ]
                        )
                    else:
                        command.append(str(repo / "freakc" / "runtime" / "freak_runtime.c"))
                    command.extend(["-I", str(repo / "freakc" / "runtime"), "-lm"])
                    compiled = run(command, repo)
                    assert compiled.returncode == 0, compiled.stdout + compiled.stderr

                sanitizer_env = os.environ.copy()
                sanitizer_env["ASAN_OPTIONS"] = "halt_on_error=1"
                if sys.platform.startswith("linux"):
                    sanitizer_env["ASAN_OPTIONS"] += ":detect_leaks=1"
                    sanitizer_env["LSAN_OPTIONS"] = "exitcode=23"
                executed = run([str(binary)], root, sanitizer_env)
                assert executed.returncode == 0, executed.stdout + executed.stderr
                assert executed.stdout.strip().splitlines() == expected_output, executed.stdout
                assert "LeakSanitizer" not in executed.stderr
                assert "ownership audit found" not in executed.stderr

        if sys.platform != "win32":
            # Negative control: LLVM allocations are globally reachable, so
            # LSan alone cannot prove tracker cleanup. The test-only audit must
            # independently reject one deliberately retained tracker entry.
            clang = os.environ.get("FREAK_CLANG") or shutil.which("clang")
            assert clang, "clang is required for the ownership audit control"
            audit_source = root / "ownership_audit_control.c"
            audit_source.write_text(
                "#include <stdint.h>\n"
                "#include <stdlib.h>\n"
                "extern int64_t freak_llvm_word_adopt(int64_t);\n"
                "int main(void) {\n"
                "    char *owned = (char *)malloc(2);\n"
                "    if (!owned) return 2;\n"
                "    owned[0] = 'x'; owned[1] = '\\0';\n"
                "    freak_llvm_word_adopt((int64_t)owned);\n"
                "    return 0;\n"
                "}\n",
                encoding="utf-8",
            )
            audit_binary = root / "ownership_audit_control"
            audit_compiled = run(
                [
                    clang,
                    "-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1",
                    "-o",
                    str(audit_binary),
                    str(audit_source),
                    str(repo / "freakc" / "runtime" / "freak_runtime.c"),
                    "-I",
                    str(repo / "freakc" / "runtime"),
                    "-lm",
                ],
                repo,
            )
            assert audit_compiled.returncode == 0, audit_compiled.stdout + audit_compiled.stderr
            audit_executed = run([str(audit_binary)], root)
            assert audit_executed.returncode == 86, audit_executed.stdout + audit_executed.stderr
            assert "ownership audit found 1 unreleased word allocation" in audit_executed.stderr

    print("V3 word replacement ownership: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
