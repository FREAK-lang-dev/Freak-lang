#!/usr/bin/env python3
"""Prepare actual-task FREAK controls for pass-local runtime hash resolution.

Default mode runs Python preparation/source-boundary controls only. The lead
compiles and runs --emit-harness output separately; this script never launches
a compiler, hash utility, native program, or platform loader.
"""
from __future__ import annotations

import argparse
import re
import unittest
from pathlib import Path

from v3_v35_runtime_cache import task_source

ROOT = Path(__file__).resolve().parents[1]
CACHE_TASKS = (
    "cli_runtime_cache_field", "cli_runtime_cache_find", "cli_runtime_cache_digest",
    "cli_runtime_cache_environment", "cli_runtime_cache_dyld_plain",
    "cli_runtime_cache_hash_file", "cli_runtime_cache_support_pin",
    "cli_runtime_cache_linux_support", "cli_runtime_cache_macos_support",
    "cli_runtime_cache_tool_identity", "cli_runtime_cache_trace_cc1",
    "cli_runtime_cache_prepare",
)
BOUNDARIES = {
    "process::command_new(": "control_command_new(",
    "process::command_arg(": "control_command_arg(",
    "process::env(": "control_env(",
    "fs::result_word(": "control_stage_path(",
}


def controlled_task(source: str, name: str) -> str:
    body = task_source(source, name)
    for original, stub in BOUNDARIES.items():
        body = body.replace(original, stub)
    return body


def harness() -> str:
    cache = (ROOT / "src/cli/runtime_cache.fk").read_text()
    run = (ROOT / "src/cli/run.fk").read_text()
    lexer = (ROOT / "src/compiler/v3/lexer.fk").read_text()
    build = (ROOT / "src/cli/build.fk").read_text()
    chunks = [CONTROL_STUBS]
    for name in ("is_numeric", "is_hex_digit"):
        chunks.append(task_source(lexer, name))
    for name in ("cli_run_valid_sha256", "cli_run_sha256_from_output"):
        chunks.append(task_source(run, name))
    chunks.append(task_source(build, "cli_trace_executable_token"))
    chunks.extend(controlled_task(cache, name) for name in CACHE_TASKS)
    chunks.append(CONTROL_MAIN)
    return "\n".join(chunks)


CONTROL_STUBS = r'''
pilot CLI_RUNTIME_CACHE_SCHEMA = "freak-runtime-object-v1"
pilot CLI_RUNTIME_CACHE_META_LIMIT = 1048576
pilot FREAK_V3_ABI = "control-abi"
pilot FREAK_V3_RUNTIME_API = "control-api"
pilot CLI_VERSION = "control-cli"
pilot FREAKC_VERSION = "control-compiler"
pilot cli_runtime_cache_profile = "o2"
pilot cli_runtime_cache_policy = "default"
pilot cli_runtime_cache_stats = "off"
pilot mut cli_runtime_cache_tool_complete = false
pilot mut cli_tool_capture_problem = ""
pilot mut control_windows = false
pilot mut control_macos = false
pilot mut control_sha_mode = 0
pilot mut control_generation = 0
pilot mut control_hash_failure = 0
pilot mut control_driver_changed = false
pilot mut control_library_changed = false
pilot mut control_lookup_count = 0
pilot mut control_windows_hash_count = 0
pilot mut control_hash_paths = 0
pilot mut control_hash_tools = 0
pilot mut control_program = ""
pilot mut control_arguments = 0

task require(value: bool, label: word) -> void {
    if not value { say "FAILED: " + label process::exit(1) }
}
task cli_is_windows() -> bool { give back control_windows }
task cli_is_macos() -> bool { give back control_macos }
task control_env(name: word) -> word { give back "" }
task cli_run_resolve_program(name: word) -> word {
    if name == "clang" { give back "/clang" }
    if name == "sha256sum" {
        control_lookup_count += 1
        if control_sha_mode == 1 or control_sha_mode == 2 { give back "" }
        if control_sha_mode == 3 { give back "./unresolvable-sha256sum" }
        if control_generation == 0 { give back "./first path/'sha256sum" }
        give back "./second path/sha256sum"
    }
    if name == "shasum" {
        control_lookup_count += 1
        if control_sha_mode == 2 { give back "" }
        give back "./fallback path/shasum"
    }
    if name == "ldd" { give back "/ldd" }
    if name == "otool" { give back "/otool" }
    give back ""
}
task cli_runtime_cache_canonical(path: word) -> word {
    if path == "" or path == "./unresolvable-sha256sum" { give back "" }
    if path.starts_with("./") { give back "/" + path.substring(2, path.length() - 2) }
    give back path
}
task cli_run_tool_version(path: word, allow_nonzero: bool) -> word { give back "clang version 19" }
task control_digest(path: word) -> word {
    if path == "/clang" {
        if control_driver_changed { give back "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd" }
        give back "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    }
    if path == "/libs/one" {
        if control_library_changed { give back "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee" }
        give back "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    }
    if path == "/libs/two" { give back "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc" }
    give back ""
}
task cli_run_windows_file_sha256(path: word) -> word {
    control_windows_hash_count += 1
    give back control_digest(path)
}
task control_command_new(program: word) -> int {
    control_program = program
    if control_arguments != 0 { array_release(control_arguments) }
    control_arguments = array_new()
    give back 1
}
task control_command_arg(command: int, argument: word) -> void { array_push(control_arguments, argument) }
task cli_tool_capture(command: int, include_stderr: bool) -> word {
    cli_tool_capture_problem = ""
    if control_program.contains("sha256sum") or control_program.contains("shasum") {
        pilot expected_count = 2
        if control_program.contains("/shasum") {
            expected_count = 4
            require(array_get(control_arguments, 0) == "-a" and array_get(control_arguments, 1) == "256", "shasum format arguments")
        }
        require(array_len(control_arguments) == expected_count, "one file per hash command")
        require(array_get(control_arguments, expected_count - 2) == "--", "hash argv separator")
        pilot path = array_get(control_arguments, expected_count - 1)
        array_push(control_hash_paths, path)
        array_push(control_hash_tools, control_program)
        if control_hash_failure == 1 { cli_tool_capture_problem = "nonzero hash utility" give back "" }
        if control_hash_failure == 2 { give back "malformed digest" }
        give back control_digest(path) + "  " + path + "\n"
    }
    if control_program == "/ldd" {
        give back "linux-vdso.so.1 (0x100)\nlibone.so => /libs/one (0x200)\n/libs/two (0x300)\n"
    }
    if control_program == "/otool" {
        pilot path = array_get(control_arguments, 1)
        if path == "/clang" {
            give back "/clang:\n/libs/one (compatibility version 1.0.0, current version 1.0.0)\n/libs/two (compatibility version 1.0.0, current version 1.0.0)\n"
        }
        give back path + ":\n"
    }
    if array_get(control_arguments, 0) == "-print-resource-dir" { give back "/sdk/clang/19\n" }
    if array_get(control_arguments, 0) == "-dumpmachine" { give back "x86_64-control-linux\n" }
    if array_get(control_arguments, 0) == "-###" { give back "clang version 19\n \"/clang\" \"-cc1\"\n" }
    require(false, "unexpected external command")
    give back ""
}
task cli_first_line(text: word) -> word {
    pilot position = 0
    repeat until position >= text.length() {
        if text.char_at(position) == "\n" { give back text.substring(0, position) }
        position += 1
    }
    give back text
}
task cli_runtime_cache_raw_pin(path: word, retain: bool) -> word { give back "fixed-source-pin:" + path }
task cli_runtime_cache_preprocess(executable: word, source: word, stage: int, stem: word, runtime_dir: word, opt: word, lto: word, cross: word, ui: bool) -> bool { give back true }
task cli_runtime_cache_snapshot_hash(stage: int, stem: word) -> word { give back "fixed-snapshot" }
task cli_runtime_cache_dependencies(text: word, retain: bool) -> word { give back "fixed-dependency-pins" }
task cli_runtime_cache_read_text(stage: int, name: word) -> word { give back "fixed-depfile" }
task control_stage_path(stage: int) -> word { give back "/stage" }
task cli_host_path_join(parent: word, leaf: word) -> word { give back parent + "/" + leaf }
task cli_runtime_cache_compile_args(command: int, input: word, output: word, runtime_dir: word, opt: word, lto: word, cross: word, ui: bool, snapshot: bool) -> void {}
task reset_pass() -> void {
    control_lookup_count = 0
    control_windows_hash_count = 0
    if control_hash_paths != 0 { array_release(control_hash_paths) }
    if control_hash_tools != 0 { array_release(control_hash_tools) }
    control_hash_paths = array_new()
    control_hash_tools = array_new()
}
task require_hashes(tool: word) -> void {
    require(array_len(control_hash_paths) == 3, "driver and both support images freshly hashed")
    require(array_get(control_hash_paths, 0) == "/clang", "fresh driver bytes")
    require(array_get(control_hash_paths, 1) == "/libs/one", "fresh first support bytes")
    require(array_get(control_hash_paths, 2) == "/libs/two", "fresh second support bytes")
    pilot position = 0
    repeat until position >= array_len(control_hash_tools) {
        require(array_get(control_hash_tools, position) == tool, "pass-local absolute utility for every image")
        position += 1
    }
}
task object_key(identity: word) -> word {
    give back cli_runtime_cache_prepare("clang", identity, "freak_runtime.c", 1, "common", "/runtime", "2", "off", "", false)
}
'''

CONTROL_MAIN = r'''
task main() -> int {
    reset_pass()
    pilot first_identity = cli_runtime_cache_tool_identity("clang")
    require(first_identity != "" and cli_runtime_cache_tool_complete, "initial Linux identity")
    require(control_lookup_count == 1, "one initial SHA selection")
    require_hashes("/first path/'sha256sum")
    pilot first_key = object_key(first_identity)
    require(first_key.length() == 64, "actual initial object key")

    reset_pass()
    control_generation = 1
    pilot second_identity = cli_runtime_cache_tool_identity("clang")
    require(control_lookup_count == 1, "next pass selects utility again")
    require_hashes("/second path/sha256sum")
    require(second_identity == first_identity and object_key(second_identity) == first_key, "utility plumbing leaves content identity/key unchanged")

    reset_pass()
    control_driver_changed = true
    pilot driver_identity = cli_runtime_cache_tool_identity("clang")
    require_hashes("/second path/sha256sum")
    require(driver_identity != first_identity and object_key(driver_identity) != first_key, "same-path driver bytes cannot hit the old key")
    control_driver_changed = false

    reset_pass()
    control_library_changed = true
    pilot library_identity = cli_runtime_cache_tool_identity("clang")
    require_hashes("/second path/sha256sum")
    require(library_identity != first_identity and object_key(library_identity) != first_key, "same-path support bytes cannot hit the old key")
    control_library_changed = false

    reset_pass()
    control_sha_mode = 1
    pilot fallback_identity = cli_runtime_cache_tool_identity("clang")
    require(control_lookup_count == 2, "one primary and one fallback lookup")
    require_hashes("/fallback path/shasum")
    require(fallback_identity == first_identity and object_key(fallback_identity) == first_key, "SHA-format fallback preserves identity and key")

    reset_pass()
    control_sha_mode = 2
    require(cli_runtime_cache_tool_identity("clang") == "" and not cli_runtime_cache_tool_complete, "missing utilities refuse cache admission")
    require(control_lookup_count == 2 and array_len(control_hash_paths) == 0, "no image hashing with a missing utility")

    reset_pass()
    control_sha_mode = 3
    require(cli_runtime_cache_tool_identity("clang") == "" and not cli_runtime_cache_tool_complete, "unresolvable selected utility refuses admission")
    require(control_lookup_count == 1 and array_len(control_hash_paths) == 0, "failed selected utility does not silently choose a fallback")
    control_sha_mode = 0

    reset_pass()
    control_hash_failure = 1
    require(cli_runtime_cache_tool_identity("clang") == "" and not cli_runtime_cache_tool_complete, "failed hash utility refuses admission")
    require(control_lookup_count == 1 and array_len(control_hash_paths) == 1, "failed hash does not skip to support images")

    reset_pass()
    control_hash_failure = 2
    require(cli_runtime_cache_tool_identity("clang") == "" and not cli_runtime_cache_tool_complete, "malformed digest refuses admission")
    require(control_lookup_count == 1 and array_len(control_hash_paths) == 1, "malformed hash does not skip to support images")
    control_hash_failure = 0

    reset_pass()
    control_macos = true
    pilot macos_identity = cli_runtime_cache_tool_identity("clang")
    require(macos_identity != "" and cli_runtime_cache_tool_complete, "resolved macOS closure")
    require(control_lookup_count == 1, "one SHA selection across macOS closure")
    require_hashes("/second path/sha256sum")
    control_macos = false

    reset_pass()
    control_windows = true
    pilot windows_identity = cli_runtime_cache_tool_identity("clang")
    require(windows_identity != "" and not cli_runtime_cache_tool_complete, "Windows remains unproved closure")
    require(control_lookup_count == 0 and control_windows_hash_count == 1, "Windows retains native SHA utility path")
    require(array_len(control_hash_paths) == 0, "no POSIX utility hashing on Windows")

    array_release(control_hash_paths)
    array_release(control_hash_tools)
    if control_arguments != 0 { array_release(control_arguments) }
    say "runtime hash resolution controls passed (11 cases)"
    give back 0
}
'''


class PreparationControls(unittest.TestCase):
    def test_actual_tasks_change_only_named_external_boundaries(self) -> None:
        source = (ROOT / "src/cli/runtime_cache.fk").read_text()
        generated = harness()
        for name in CACHE_TASKS:
            controlled = controlled_task(source, name)
            self.assertIn(controlled, generated)
            for original, stub in BOUNDARIES.items():
                controlled = controlled.replace(stub, original)
            self.assertEqual(controlled, task_source(source, name))

    def test_production_key_and_admission_tasks_are_in_the_control(self) -> None:
        generated = harness()
        self.assertIn('object_key(driver_identity) != first_key', generated)
        self.assertIn('object_key(library_identity) != first_key', generated)
        self.assertIn('array_len(control_hash_paths) == 3', generated)
        self.assertIn('control_lookup_count == 2', generated)
        self.assertIn('control_windows_hash_count == 1', generated)

    def test_freak_declarations_use_actual_lexer_vocabulary(self) -> None:
        lexer = task_source((ROOT / "src/compiler/v3/lexer.fk").read_text(), "lex_ident_token_type")
        reserved = set(re.findall(r'lower == "([a-z_]+)"', lexer))
        code = re.sub(r'"(?:\\.|[^"\\])*"|--[^\n]*', " ", harness())
        names = re.findall(r"\bpilot\s+(?:mut\s+)?([A-Za-z_][A-Za-z_0-9]*)", code)
        names += re.findall(r"\b([A-Za-z_][A-Za-z_0-9]*)\s*:\s*(?:int|bool|word|ByteBuffer)\b", code)
        self.assertFalse(sorted({name for name in names if name.lower() in reserved}))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-harness", type=Path, help="write a new FREAK fixture for the lead's separate native verification")
    args = parser.parse_args()
    if args.emit_harness is not None:
        with args.emit_harness.open("x", encoding="utf-8") as stream:
            stream.write(harness())
        return 0
    outcome = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(PreparationControls))
    return 0 if outcome.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
