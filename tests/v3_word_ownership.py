#!/usr/bin/env python3
"""Prove repeated V3 word replacement releases superseded allocations."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
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
    pilot shadow_value = global_owner
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
pilot __freak_param_0: int = 42

task copy_global_shadow() -> word {
    pilot copied: word = copied
    give back copied
}

task copy_param_shadow(copied: word, __freak_param_0: int) -> word {
    if true {
        pilot copied: word = copied
        give back copied
    }
    give back ""
}

task read_generated_name_collision(other: int) -> int {
    give back __freak_param_0
}

task main() {
    pilot mut global_copy: word = copy_global_shadow()
    copied = "released"
    say global_copy
    global_copy = "released"
    pilot mut argument: word = "p" + "aram"
    pilot mut param_copy: word = copy_param_shadow(argument, 7)
    argument = "released"
    say param_copy
    param_copy = "released"
    say read_generated_name_collision(7).to_word()
    repeat 64 times {
        word_from_int(99)
    }
    pilot mut runtime_arg: word = process::arg(0)
    repeat 64 times {
        runtime_arg = process::arg(0)
    }
    say (runtime_arg.length() > 0).to_word()
    runtime_arg = "released"
}
"""

METHOD_RETURN_PROGRAM = """task replace_identity(value: word) -> word {
    give back value.replace("", "z")
}

task trim_identity(value: word) -> word {
    give back value.trim()
}

task main() {
    pilot mut replace_source: word = "a" + "b"
    pilot mut replaced: word = replace_identity(replace_source)
    replace_source = "released"
    say replaced
    replaced = "released"
    pilot mut trim_source: word = "  t" + "rim  "
    pilot mut trimmed: word = trim_identity(trim_source)
    trim_source = "released"
    say trimmed
    trimmed = "released"
}
"""

CONCAT_TEMP_PROGRAM = """task main() {
    pilot mut text: word = "seed" + "value"
    repeat 256 times {
        text = ("left" + word_from_int(7)) + ("right" + "tail")
    }
    say text
    text = "released"
    ("discard" + "ed") + ("temp" + "orary")
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

LEXICAL_LIFETIME_PROGRAM = """pilot global_final: word = "g" + "lobal"

task return_scoped(flag: bool) -> word {
    pilot first: word = "ret" + "urn"
    if flag {
        pilot nested: word = "n" + "ested"
        give back first
    }
    pilot fallback: word = "fall" + "back"
    give back fallback
}

task return_temporary() -> word {
    pilot discarded: word = "dis" + "carded"
    give back "tem" + "porary"
}

task measure_scoped() -> int {
    pilot measured: word = "num" + "ber"
    give back measured.length()
}

task return_void(flag: bool) {
    pilot owned: word = "vo" + "id"
    if flag { give back }
    say "bad void"
}

task main() {
    repeat 128 times {
        pilot scoped: word = "scope" + "owned"
        if scoped.length() != 10 { say "bad scope" }
    }
    pilot mut index = 0
    repeat 8 times {
        pilot loop_value: word = "loop" + index.to_word()
        index += 1
        if index == 2 { continue }
        if index == 4 { break }
    }
    pilot returned: word = return_scoped(true)
    say returned
    pilot fallback: word = return_scoped(false)
    say fallback
    pilot temporary: word = return_temporary()
    say temporary
    if measure_scoped() != 6 { say "bad measure" }
    return_void(true)
    say global_final
}
"""

BORROWED_TEMP_PROGRAM = """task main() {
    repeat 128 times {
        pilot measured = ("le" + "ngth").length()
        if measured != 6 { say "bad length" }
        if ("a" + "b") != "ab" { say "bad compare" }
        if not ("prefix" + "tail").starts_with("pre" + "fix") { say "bad prefix" }
        if not ("left" + "right").contains("ri" + "ght") { say "bad contains" }
        pilot piece: word = ("zero" + "one").substring(1, 3)
        if piece != "ero" { say "bad substring" }
        pilot parsed = word_to_int("7" + "")
        if parsed != 7 { say "bad parsed" }
    }
    say "temps"
}
"""

NUMERIC_WORD_PROGRAM = """task main() {
    pilot first_number: num = 1.25
    pilot second_number: num = 9.5
    pilot direct_first: word = format_num(first_number)
    pilot direct_second: word = format_num(second_number)
    pilot first: word = first_number.to_word()
    pilot second: word = second_number.to_word()
    say direct_first
    say direct_second
    say first
    say second
    pilot integer_value: int = 42
    pilot truth_value: bool = true
    pilot integer: word = integer_value.to_word()
    pilot truth: word = truth_value.to_word()
    say integer
    say truth
}
"""

SCALAR_SAY_PROGRAM = """task main() {
    say 42
    say true
    say false
    say 1.25
}
"""

NUMERIC_CONTEXT_PROGRAM = """pilot mut global_promoted: num = 2

task accept_num(value: num) -> num {
    give back value
}

task promote_return() -> num {
    give back 7
}

task main() -> int {
    say global_promoted
    say accept_num(3)
    say promote_return()
    pilot mut local_promoted: num = 4
    say local_promoted
    local_promoted = 5
    say local_promoted
    local_promoted += 1.5
    say local_promoted
    global_promoted = 6
    say global_promoted
    say 1 + 2.5
    say 2.5 + 1
    say 1 < 2.5
    say 3.5 == 3 + 0.5
    say math::sqrt(9)
    say math::pow(2, 3)
    give back 17
}
"""

NUMERIC_SHAPE_PROGRAM = """extern task echo_num(value: num) -> num

shape Gauge {
    value: num
}

impl Gauge {
    task plus(self, amount: num) -> num {
        give back self.value + amount
    }
}

pilot gauge: Gauge = Gauge { value: 2 }

task main() {
    say gauge.value
    say echo_num(3)
    say gauge.plus(4)
    gauge.value = 5
    say gauge.value
    gauge.value += 2
    say gauge.value
    gauge.value *= 2
    say gauge.value
    gauge.value -= 1.5
    say gauge.value
    gauge.value /= 2
    say gauge.value
}
"""

NUMERIC_UNARY_PROGRAM = """task main() {
    pilot value: num = 1.5
    say -value
}
"""

SHORT_CIRCUIT_PROGRAM = """pilot mut side_effects: int = 0

task mark() -> bool {
    side_effects += 1
    give back true
}

task explode() -> bool {
    panic("short-circuit failure")
    give back true
}

task main() {
    say false and mark()
    say true or mark()
    say false and explode()
    say true or explode()
    say side_effects
}
"""

UI_ABI_PROGRAM = """task draw_probe() {
    ui::stroke_rect(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    ui::draw_line(11, 12, 13, 14, 15, 16, 17, 18, 19, 20)
}

task main() {
    say "ui abi"
}
"""

WRAPPER_EXTERN_TOP_LEVEL_PROGRAM = """extern task freak_main() -> void

say "top wrapper"
"""

WRAPPER_EXTERN_INIT_PROGRAM = """extern task freak_init_globals() -> void

task main() {
    say "init wrapper"
}
"""

LOOP_EVALUATION_PROGRAM = """pilot mut repeat_limit_calls: int = 0
pilot mut training_limit_calls: int = 0
pilot mut training_until_calls: int = 0
pilot mut zero_limit_calls: int = 0
pilot mut forbidden_until_calls: int = 0

task repeat_limit() -> int {
    repeat_limit_calls += 1
    give back 3
}

task training_limit() -> int {
    training_limit_calls += 1
    give back 2
}

task training_until() -> bool {
    training_until_calls += 1
    give back false
}

task zero_limit() -> int {
    zero_limit_calls += 1
    give back 0
}

task forbidden_until() -> bool {
    forbidden_until_calls += 1
    give back false
}

task main() {
    pilot mut body_count: int = 0
    repeat repeat_limit() times {
        body_count += 1
    }
    training arc until training_until() max training_limit() sessions {
        body_count += 1
    }
    training arc until forbidden_until() max zero_limit() sessions {
        body_count += 100
    }
    say repeat_limit_calls
    say training_limit_calls
    say training_until_calls
    say zero_limit_calls
    say forbidden_until_calls
    say body_count
}
"""

WHEN_COLLISION_PROGRAM = """task main() {
    pilot COLLISION_NAME: word = "sentinel"
    when "a" + "b" {
        "ab" -> say COLLISION_NAME
        _ -> say "bad collision"
    }
}
"""

WHEN_STACK_PROGRAM = """task main() {
    pilot mut matches: int = 0
    repeat 250000 times {
        when "a" + "b" {
            "ab" -> matches += 1
            _ -> matches += 1000000
        }
    }
    say matches
}
"""

TOP_LEVEL_GLOBAL_PROGRAM = """pilot top_level: word = "top" + "level"
say top_level
"""

WHEN_LIFETIME_PROGRAM = """task return_from_when() -> word {
    when "ret" + "urn" {
        "return" -> give back "matched"
        _ -> give back "fallback"
    }
    give back "unreachable"
}

task main() {
    repeat 3 times {
        when "con" + "tinue" {
            "continue" -> continue
            _ -> say "bad continue"
        }
        say "bad after continue"
    }
    repeat 3 times {
        when "br" + "eak" {
            "break" -> break
            _ -> say "bad break"
        }
        say "bad after break"
    }
    when "al" + "pha" {
        "alpha" -> say "word"
        _ -> say "bad word"
    }
    pilot numeric_choice: num = 2.5
    when numeric_choice {
        2.5 -> say "num"
        _ -> say "bad num"
    }
    when 1 {
        1.0 -> say "mixed"
        _ -> say "bad mixed"
    }
    say return_from_when()
}
"""

PREDICATE_OWNERSHIP_PROGRAM = """task main() {
    if ("pre" + "dicate") == "predicate" { say "if" }
    pilot mut spins = 0
    repeat until ("spin" + spins.to_word()) == "spin2" {
        spins += 1
    }
    say spins
    pilot mut training_count = 0
    training arc until ("session" + training_count.to_word()) == "session1" max 3 sessions {
        training_count += 1
    }
    say training_count
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
    parser.add_argument(
        "--runtime-root",
        type=Path,
        help="runtime payload to compile (defaults to the repository runtime)",
    )
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    runtime_root = (
        args.runtime_root.resolve()
        if args.runtime_root is not None
        else (repo / "freakc" / "runtime").resolve()
    )
    assert (runtime_root / "freak_runtime.c").is_file(), runtime_root
    assert (runtime_root / "freak_llvm_runtime.c").is_file(), runtime_root
    freak = args.freak.resolve()
    assert freak.is_file(), freak
    windows_build_script = (repo / "build_cli.bat").read_text(encoding="utf-8")
    assert "call :remove_final_aliases" in windows_build_script
    assert "for %%F in (build\\freak.exe build\\hangar.exe build\\freakc.exe build\\freakc_v3.exe)" in windows_build_script
    assert windows_build_script.count("call :copy_final_alias") == 3
    assert "--self-test-remove-intermediate" in windows_build_script
    assert "call :remove_intermediate" in windows_build_script
    assert "call :append_source" in windows_build_script
    assert "call :copy_intermediate" in windows_build_script
    assert "fc /b \"%~1\" \"%~2\"" in windows_build_script
    assert windows_build_script.count("-lws2_32") >= 4
    runtime_source = (runtime_root / "freak_runtime.c").read_text(encoding="utf-8")
    assert runtime_source.count("word replacement size overflow") >= 4
    assert runtime_source.count("(SIZE_MAX -") >= 2
    assert runtime_source.count("freak_word_replace_owned(&result") >= 4
    assert "return freak_word_own(buf, (size_t)n);" in runtime_source
    assert "return freak_word_own(buf, (size_t)total);" in runtime_source
    assert "#ifdef FREAK_C_RUNTIME_OWNERSHIP_AUDIT" in runtime_source
    assert "return freak_word_own(buf, (size_t)len);" in runtime_source
    llvm_runtime_source = (runtime_root / "freak_llvm_runtime.c").read_text(
        encoding="utf-8"
    )
    assert llvm_runtime_source.count("return freak_llvm_word_adopt((int64_t)buf);") >= 2
    assert re.search(r"void freak_llvm_ui_stroke_rect\([^\n]+int64_t thickness\)", llvm_runtime_source)
    assert re.search(r"void freak_llvm_ui_draw_line\([^\n]+int64_t thickness\)", llvm_runtime_source)
    assert "freak_ui_stroke_rect(h, x, y, w, hh, r, g, b, a, thickness);" in llvm_runtime_source
    assert "freak_ui_draw_line(h, x1, y1, x2, y2, r, g, b, a, thickness);" in llvm_runtime_source

    with tempfile.TemporaryDirectory(prefix="freak-v3-word-ownership-") as tmp:
        root = Path(tmp)
        if sys.platform == "win32":
            stage_directory = root / "locked-stage2-output.fk.c"
            stage_directory.mkdir()
            fail_closed = run(
                [
                    str(repo / "build_cli.bat"),
                    "--self-test-remove-intermediate",
                    str(stage_directory),
                ],
                root,
            )
            assert fail_closed.returncode != 0, fail_closed.stdout + fail_closed.stderr
            assert "Expected intermediate file but found a directory" in fail_closed.stdout
            assert stage_directory.is_dir()
        listing_dir = root / "listing"
        listing_dir.mkdir()
        for entry_index in range(128):
            (listing_dir / f"entry-{entry_index:03d}.txt").write_text(
                "ownership probe\n", encoding="utf-8"
            )
        fs_list_program = (
            "task main() {\n"
            f'    pilot mut listing: word = fs::list_dir("{listing_dir.as_posix()}")\n'
            "    repeat 64 times {\n"
            f'        listing = fs::list_dir("{listing_dir.as_posix()}")\n'
            "    }\n"
            '    say listing.contains("entry-127.txt").to_word()\n'
            '    listing = "released"\n'
            "}\n"
        )
        tcp_listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp_listener.bind(("127.0.0.1", 0))
        tcp_listener.listen(2)
        tcp_port = tcp_listener.getsockname()[1]
        tcp_server_failures: list[str] = []

        def serve_tcp_ownership_probe() -> None:
            try:
                for payload in (b"recv", b"all"):
                    connection, _ = tcp_listener.accept()
                    with connection:
                        connection.sendall(payload)
            except BaseException as exc:  # surfaced after the executable exits
                tcp_server_failures.append(repr(exc))
            finally:
                tcp_listener.close()

        tcp_server = threading.Thread(target=serve_tcp_ownership_probe, daemon=True)
        tcp_server.start()
        tcp_program = (
            "task main() {\n"
            f'    pilot first = tcp_connect("127.0.0.1", {tcp_port})\n'
            "    say tcp_recv(first, 4)\n"
            "    tcp_close(first)\n"
            f'    pilot second = tcp_connect("127.0.0.1", {tcp_port})\n'
            "    tcp_recv_all(second, 3)\n"
            "    tcp_close(second)\n"
            '    pilot mut marker: word = "o" + "wned"\n'
            '    marker = "released"\n'
            "}\n"
        )
        cases = (
            ("strict", PROGRAM, ["--strict-borrow"], ["done", "xy", "call", "arg", "shadow", "global", "inner", "outer", "outer!"], ("c", "llvm")),
            ("global_return", GLOBAL_RETURN_PROGRAM, [], ["global"], ("c", "llvm")),
            ("global_call", GLOBAL_CALL_PROGRAM, [], ["local", "global"], ("c", "llvm")),
            ("return_shadow", RETURN_SHADOW_PROGRAM, [], ["local", "inner", "global"], ("c", "llvm")),
            ("shadow_copy", SHADOW_COPY_PROGRAM, [], ["global", "param", "42", "true"], ("c", "llvm")),
            ("method_return", METHOD_RETURN_PROGRAM, [], ["ab", "trim"], ("c", "llvm")),
            ("concat_temp", CONCAT_TEMP_PROGRAM, [], ["left7righttail"], ("c", "llvm")),
            ("aggregate", AGGREGATE_PROGRAM, [], ["hi", "hi", "hi", "xy", "stored", "join", "literal"], ("c", "llvm")),
            ("fs_list", fs_list_program, [], ["true"], ("c", "llvm")),
            ("tcp_owned", tcp_program, [], ["recv"], ("c",)),
            ("method_shape", METHOD_SHAPE_PROGRAM, [], ["xy", "xy", "new", "field", "self", "self"], ("llvm",)),
            ("lexical_lifetime", LEXICAL_LIFETIME_PROGRAM, [], ["return", "fallback", "temporary", "global"], ("c", "llvm")),
            ("borrowed_temp", BORROWED_TEMP_PROGRAM, [], ["temps"], ("c", "llvm")),
            ("numeric_word", NUMERIC_WORD_PROGRAM, [], ["1.25", "9.5", "1.25", "9.5", "42", "true"], ("c", "llvm")),
            ("scalar_say", SCALAR_SAY_PROGRAM, [], ["42", "true", "false", "1.25"], ("c", "llvm")),
            ("numeric_context", NUMERIC_CONTEXT_PROGRAM, [], ["2", "3", "7", "4", "5", "6.5", "6", "3.5", "3.5", "true", "true", "3", "8"], ("c", "llvm")),
            ("numeric_shape", NUMERIC_SHAPE_PROGRAM, [], ["2", "3", "6", "5", "7", "14", "12.5", "6.25"], ("c", "llvm")),
            ("numeric_unary", NUMERIC_UNARY_PROGRAM, [], ["-1.5"], ("c", "llvm")),
            ("short_circuit", SHORT_CIRCUIT_PROGRAM, [], ["false", "true", "false", "true", "0"], ("c", "llvm")),
            ("ui_abi", UI_ABI_PROGRAM, [], ["ui abi"], ("c", "llvm")),
            ("wrapper_extern_top_level", WRAPPER_EXTERN_TOP_LEVEL_PROGRAM, [], ["top wrapper"], ("c", "llvm")),
            ("wrapper_extern_init", WRAPPER_EXTERN_INIT_PROGRAM, [], ["init wrapper"], ("c", "llvm")),
            ("loop_evaluation", LOOP_EVALUATION_PROGRAM, [], ["1", "1", "2", "1", "0", "5"], ("c", "llvm")),
            ("when_collision", WHEN_COLLISION_PROGRAM, [], ["sentinel"], ("c", "llvm")),
            ("when_stack", WHEN_STACK_PROGRAM, [], ["250000"], ("c", "llvm")),
            ("top_level_global", TOP_LEVEL_GLOBAL_PROGRAM, [], ["toplevel"], ("c", "llvm")),
            ("when_lifetime", WHEN_LIFETIME_PROGRAM, [], ["word", "num", "mixed", "matched"], ("c", "llvm")),
            ("predicate_ownership", PREDICATE_OWNERSHIP_PROGRAM, [], ["if", "2", "1"], ("c", "llvm")),
        )
        for case_name, program, extra_flags, expected_output, backends in cases:
            source = root / f"replace_owned_{case_name}.fk"
            source.write_text(program, encoding="utf-8")
            for backend, flag, suffix in (("c", "--c", ".c"), ("llvm", "--llvm", ".ll")):
                if backend not in backends:
                    continue
                if case_name == "when_collision" and backend == "c":
                    probe = run([str(freak), "transpile", str(source), flag, *extra_flags], repo)
                    assert probe.returncode == 0, probe.stdout + probe.stderr
                    probe_text = Path(str(source) + suffix).read_text(encoding="utf-8")
                    target_match = re.search(r"__freak_when_target_(\d+)", probe_text)
                    assert target_match, probe_text
                    collision_name = f"__freak_when_owned_{target_match.group(1)}"
                    source.write_text(program.replace("COLLISION_NAME", collision_name), encoding="utf-8")
                transpiled = run([str(freak), "transpile", str(source), flag, *extra_flags], repo)
                assert transpiled.returncode == 0, transpiled.stdout + transpiled.stderr
                generated = Path(str(source) + suffix)
                assert generated.is_file(), generated
                generated_text = generated.read_text(encoding="utf-8")
                if backend == "c":
                    assert "freak_word_release_owned" in generated_text, case_name
                    if case_name not in {
                        "lexical_lifetime",
                        "borrowed_temp",
                        "numeric_word",
                        "scalar_say",
                        "numeric_context",
                        "numeric_shape",
                        "numeric_unary",
                        "short_circuit",
                        "ui_abi",
                        "wrapper_extern_top_level",
                        "wrapper_extern_init",
                        "loop_evaluation",
                        "when_collision",
                        "when_stack",
                        "top_level_global",
                        "when_lifetime",
                        "predicate_ownership",
                    }:
                        assert "freak_word_replace_owned" in generated_text, case_name
                    if case_name == "strict":
                        assert re.search(r"freak_word_clone\(__freak_local_\d+\)", generated_text)
                        assert re.search(r"__freak_user_identity\(freak_word_clone\(__freak_local_\d+\)\)", generated_text)
                        assert re.search(r"__freak_user_observe\(freak_word_clone\(__freak_local_\d+\)\)", generated_text)
                        assert "__freak_user_observe(freak_word_concat_consuming(" in generated_text
                        assert re.search(r"__freak_user_observe_shadow\(freak_word_clone\(__freak_local_\d+\)\)", generated_text)
                        assert re.search(r"__freak_global_\d+ = freak_word_clone\(__freak_global_\d+\)", generated_text)
                        assert "freak_word_release_owned(&__freak_param_0)" in generated_text
                    elif case_name == "aggregate":
                        assert re.search(r"freak_array_push_owned\(__freak_local_\d+, freak_word_clone\(__freak_local_\d+\)\)", generated_text)
                        assert re.search(r"freak_array_set_owned\(__freak_local_\d+, 0, freak_word_concat_consuming\(", generated_text)
                        assert re.search(r"freak_array_release_owned\(__freak_local_\d+\)", generated_text)
                        assert re.search(r"freak_word_join_owned\(__freak_local_\d+\)", generated_text)
                        assert re.search(r"\(\{ int64_t __freak_array_\d+ = freak_array_new\(\);", generated_text)
                        assert re.search(r"freak_array_push_owned\(__freak_array_\d+, freak_word_concat_consuming\(", generated_text)
                        assert "freak_array_get" in generated_text
                    elif case_name == "global_call":
                        assert re.search(r"__freak_user_observe\(freak_word_clone\(__freak_global_\d+\)\)", generated_text)
                    elif case_name == "global_return":
                        assert re.search(r"__freak_return_value = freak_word_clone\(__freak_global_\d+\)", generated_text)
                    elif case_name == "return_shadow":
                        assert "__freak_user_return_local_shadow" in generated_text
                        assert "__freak_user_return_param_shadow" in generated_text
                    elif case_name == "shadow_copy":
                        assert re.search(r"__freak_return_value = __freak_global_\d+;", generated_text)
                        assert "freak_word_release_owned(&__freak_say_value)" in generated_text
                        assert "freak_word_release_owned(&__freak_discarded_word)" in generated_text
                    elif case_name == "concat_temp":
                        assert generated_text.count("freak_word_concat_consuming") >= 4
                    elif case_name == "tcp_owned":
                        assert "freak_tcp_recv(" in generated_text
                        assert "freak_tcp_recv_all(" in generated_text
                        assert generated_text.count("freak_word_release_owned") >= 2
                    elif case_name == "lexical_lifetime":
                        assert generated_text.count("freak_word_release_owned") >= 8
                        assert re.search(
                            r"freak_word __freak_return_value = __freak_local_\d+;\s+"
                            r"freak_word_release_owned\(&__freak_local_\d+\);",
                            generated_text,
                        )
                    elif case_name == "borrowed_temp":
                        assert "__freak_borrow_arg_" in generated_text
                        assert generated_text.count("freak_word_release_owned(&__freak_borrow_arg_") >= 5
                    elif case_name == "numeric_word":
                        assert generated_text.count("freak_format_num") >= 4
                    elif case_name == "scalar_say":
                        assert "freak_word_from_int" in generated_text
                        assert "freak_word_from_bool" in generated_text
                        assert "freak_format_num" in generated_text
                    elif case_name == "numeric_context":
                        assert "double __freak_return_value" in generated_text
                        assert "freak_format_num" in generated_text
                        assert "int64_t __freak_native_main_result = 0;" in generated_text
                        assert "return (int)__freak_native_main_result;" in generated_text
                    elif case_name == "numeric_shape":
                        assert "extern double echo_num(double" in generated_text
                        assert "freak_llvm_shape_get" in generated_text
                        assert "freak_llvm_shape_set" in generated_text
                    elif case_name == "numeric_unary":
                        assert "freak_format_num" in generated_text
                    elif case_name == "short_circuit":
                        assert "&&" in generated_text
                        assert "||" in generated_text
                    elif case_name == "ui_abi":
                        assert re.search(r"freak_ui_stroke_rect\([^;]+, 10\)", generated_text)
                        assert re.search(r"freak_ui_draw_line\([^;]+, 20\)", generated_text)
                    elif case_name == "wrapper_extern_top_level":
                        assert "extern void freak_main(void);" in generated_text
                        assert "void __freak_generated_top_level(void) {" in generated_text
                        assert "    __freak_generated_top_level();" in generated_text
                        assert not re.search(r"(?m)^void freak_main\(void\) \{", generated_text)
                    elif case_name == "wrapper_extern_init":
                        assert "extern void freak_init_globals(void);" in generated_text
                        assert "void __freak_generated_init_globals(void) {" in generated_text
                        assert "    __freak_generated_init_globals();" in generated_text
                        assert not re.search(r"(?m)^void freak_init_globals\(void\) \{", generated_text)
                    elif case_name == "loop_evaluation":
                        assert "__freak_repeat_limit_" in generated_text
                        assert "__freak_arc_limit_" in generated_text
                    elif case_name == "when_collision":
                        assert "sentinel" in generated_text
                    elif case_name == "when_lifetime":
                        assert "freak_word_eq(__freak_when_target_" in generated_text
                        assert "freak_word_release_owned(&__freak_when_target_" in generated_text
                else:
                    assert "@freak_llvm_word_release_replaced" in generated_text
                    assert "@freak_llvm_word_clone" in generated_text
                    if case_name == "concat_temp":
                        assert generated_text.count("@freak_llvm_word_release_replaced") >= 4
                    elif case_name == "lexical_lifetime":
                        assert generated_text.count("@freak_llvm_word_release_replaced") >= 8
                        assert "return.dead." in generated_text
                    elif case_name == "borrowed_temp":
                        assert generated_text.count("@freak_llvm_word_release_replaced") >= 10
                    elif case_name == "numeric_word":
                        assert generated_text.count("call i64 @freak_llvm_format_num") >= 2
                        assert generated_text.count("call i64 @freak_llvm_word_from_num") >= 2
                    elif case_name == "scalar_say":
                        assert "@freak_llvm_word_from_int" in generated_text
                        assert "@freak_llvm_word_from_bool" in generated_text
                        assert "@freak_llvm_format_num" in generated_text
                    elif case_name == "numeric_context":
                        assert generated_text.count("sitofp i64") >= 8
                        assert "fadd double" in generated_text
                        assert "fcmp olt double" in generated_text
                        assert "call i64 @freak_llvm_math_pow" in generated_text
                        assert re.search(r"= call i64 @__freak_user_main\(\)", generated_text)
                        assert re.search(r"= trunc i64 %t\d+ to i32", generated_text)
                    elif case_name == "numeric_shape":
                        assert generated_text.count("sitofp i64") >= 4
                        assert "call i64 @echo_num" in generated_text
                        assert "call i64 @__freak_user_Gauge_plus" in generated_text
                        assert generated_text.count("call void @freak_llvm_shape_set") >= 5
                        assert "fadd double" in generated_text
                        assert "fmul double" in generated_text
                        assert "fsub double" in generated_text
                        assert "fdiv double" in generated_text
                    elif case_name == "numeric_unary":
                        assert "fsub double 0.0" in generated_text
                    elif case_name == "short_circuit":
                        assert "logic.short." in generated_text
                        assert "logic.rhs." in generated_text
                        assert "phi i64" in generated_text
                    elif case_name == "ui_abi":
                        ten_i64 = r"i64 [^,\)]+(?:, i64 [^,\)]+){9}"
                        assert re.search(r"call void @freak_llvm_ui_stroke_rect\(" + ten_i64 + r"\)", generated_text)
                        assert re.search(r"call void @freak_llvm_ui_draw_line\(" + ten_i64 + r"\)", generated_text)
                        assert "declare void @freak_llvm_ui_stroke_rect(i64, i64, i64, i64, i64, i64, i64, i64, i64, i64)" in generated_text
                        assert "declare void @freak_llvm_ui_draw_line(i64, i64, i64, i64, i64, i64, i64, i64, i64, i64)" in generated_text
                    elif case_name == "wrapper_extern_top_level":
                        assert "declare void @freak_main()" in generated_text
                        assert "define void @__freak_generated_top_level()" in generated_text
                        assert "call void @__freak_generated_top_level()" in generated_text
                        assert "define void @freak_main()" not in generated_text
                    elif case_name == "wrapper_extern_init":
                        assert "declare void @freak_init_globals()" in generated_text
                        assert "define void @__freak_generated_init_globals()" in generated_text
                        assert "call void @__freak_generated_init_globals()" in generated_text
                        assert "define void @freak_init_globals()" not in generated_text
                    elif case_name == "loop_evaluation":
                        assert "loop.until." in generated_text
                        assert re.search(
                            r"br i1 %t\d+, label %loop\.until\.\d+, label %loop\.end\.\d+",
                            generated_text,
                        )
                    elif case_name == "when_stack":
                        assert "%when_target_v" not in generated_text
                        assert "call void @freak_llvm_word_release_replaced(i64 %t" in generated_text
                    elif case_name == "when_lifetime":
                        assert "@freak_llvm_word_eq" in generated_text
                        assert "fcmp oeq double" in generated_text
                        assert "sitofp i64 1 to double" in generated_text
                        assert "%when_target_v" not in generated_text

                if case_name in {"numeric_shape", "ui_abi"} and backend == "c":
                    continue

                binary = root / (f"replace_owned_{case_name}_{backend}.exe" if sys.platform == "win32" else f"replace_owned_{case_name}_{backend}")
                clang = os.environ.get("FREAK_CLANG") or shutil.which("clang")
                assert clang, "clang is required for the ownership regression"
                command = [clang, "-g", "-O1", "-o", str(binary), str(generated)]
                if case_name == "numeric_shape" and backend == "llvm":
                    extern_probe = root / "extern_numeric_probe.c"
                    extern_probe.write_text(
                        "#include <stdint.h>\n"
                        "int64_t echo_num(int64_t value) { return value; }\n",
                        encoding="utf-8",
                    )
                    command.append(str(extern_probe))
                if case_name == "short_circuit" and backend == "llvm":
                    panic_probe = root / "llvm_panic_probe.c"
                    panic_probe.write_text(
                        "#include <stdint.h>\n"
                        "#include <stdlib.h>\n"
                        "void freak_llvm_panic(int64_t message) { (void)message; abort(); }\n",
                        encoding="utf-8",
                    )
                    command.append(str(panic_probe))
                if sys.platform != "win32":
                    command.extend(["-fsanitize=address", "-fno-omit-frame-pointer"])
                if backend == "llvm":
                    command.append("-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1")
                    command.extend(
                        [
                            str(runtime_root / "freak_llvm_runtime.c"),
                            str(runtime_root / "freak_runtime.c"),
                        ]
                    )
                else:
                    command.append("-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1")
                    command.append(str(runtime_root / "freak_runtime.c"))
                command.extend(["-I", str(runtime_root)])
                if sys.platform == "win32":
                    command.append("-lws2_32")
                else:
                    command.append("-lm")
                compiled = run(command, repo)
                assert compiled.returncode == 0, compiled.stdout + compiled.stderr

                sanitizer_env = os.environ.copy()
                sanitizer_env["ASAN_OPTIONS"] = "halt_on_error=1"
                if sys.platform.startswith("linux"):
                    sanitizer_env["ASAN_OPTIONS"] += ":detect_leaks=1"
                    sanitizer_env["LSAN_OPTIONS"] = "exitcode=23"
                executed = run([str(binary)], root, sanitizer_env)
                expected_exit = 17 if case_name == "numeric_context" else 0
                assert executed.returncode == expected_exit, executed.stdout + executed.stderr
                assert executed.stdout.strip().splitlines() == expected_output, executed.stdout
                assert "LeakSanitizer" not in executed.stderr
                assert "ownership audit found" not in executed.stderr

        tcp_server.join(timeout=30)
        assert not tcp_server.is_alive(), "TCP ownership probe server did not finish"
        assert not tcp_server_failures, tcp_server_failures

        # Negative controls prove both deterministic runtime audits reject one
        # deliberately retained allocation, including on Windows where LSan is
        # not part of the compiler matrix.
        clang = os.environ.get("FREAK_CLANG") or shutil.which("clang")
        assert clang, "clang is required for the ownership audit controls"
        llvm_audit_source = root / "llvm_ownership_audit_control.c"
        llvm_audit_source.write_text(
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
        llvm_audit_binary = root / (
            "llvm_ownership_audit_control.exe"
            if sys.platform == "win32"
            else "llvm_ownership_audit_control"
        )
        llvm_audit_command = [
            clang,
            "-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1",
            "-o",
            str(llvm_audit_binary),
            str(llvm_audit_source),
            str(runtime_root / "freak_runtime.c"),
            "-I",
            str(runtime_root),
        ]
        if sys.platform == "win32":
            llvm_audit_command.append("-lws2_32")
        else:
            llvm_audit_command.append("-lm")
        llvm_audit_compiled = run(llvm_audit_command, repo)
        assert llvm_audit_compiled.returncode == 0, llvm_audit_compiled.stdout + llvm_audit_compiled.stderr
        llvm_audit_executed = run([str(llvm_audit_binary)], root)
        assert llvm_audit_executed.returncode == 86, llvm_audit_executed.stdout + llvm_audit_executed.stderr
        assert "LLVM ownership audit found 1 unreleased word allocation" in llvm_audit_executed.stderr

        c_audit_source = root / "c_ownership_audit_control.c"
        c_audit_source.write_text(
            '#include "freak_runtime.h"\n'
            "#include <stdlib.h>\n"
            "int main(void) {\n"
            "    char *owned = (char *)malloc(2);\n"
            "    if (!owned) return 2;\n"
            "    owned[0] = 'x'; owned[1] = '\\0';\n"
            "    (void)freak_word_own(owned, 1);\n"
            "    return 0;\n"
            "}\n",
            encoding="utf-8",
        )
        c_audit_binary = root / (
            "c_ownership_audit_control.exe"
            if sys.platform == "win32"
            else "c_ownership_audit_control"
        )
        c_audit_command = [
            clang,
            "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1",
            "-o",
            str(c_audit_binary),
            str(c_audit_source),
            str(runtime_root / "freak_runtime.c"),
            "-I",
            str(runtime_root),
        ]
        if sys.platform == "win32":
            c_audit_command.append("-lws2_32")
        else:
            c_audit_command.append("-lm")
        c_audit_compiled = run(c_audit_command, repo)
        assert c_audit_compiled.returncode == 0, c_audit_compiled.stdout + c_audit_compiled.stderr
        c_audit_executed = run([str(c_audit_binary)], root)
        assert c_audit_executed.returncode == 87, c_audit_executed.stdout + c_audit_executed.stderr
        assert "C ownership audit found 1 unreleased word allocation" in c_audit_executed.stderr

    print("V3 word replacement ownership: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
