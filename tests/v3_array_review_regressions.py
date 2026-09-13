#!/usr/bin/env python3
"""Native repros for ownership and evaluation-order array review findings."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

from v3_array_rescue import require_ok, run
from v3_array_torture import CHECK_ZERO, COUNTERS, emission, expect_rejected

ROW = '''shape Row {
    label: word
    value: int
}
'''
WATCH = '''extern task array_review_watch_exit() -> void
'''
CLEAN = "review-clean arrays=0 shapes=0 words=0"
HELPER = r'''
#include "freak_runtime.h"
#include <stdio.h>
#include <stdlib.h>
static void array_review_at_exit(void) {
    long long arrays = (long long)freak_v3_live_arrays();
    long long shapes = (long long)freak_v3_live_shapes();
    long long words = (long long)freak_v3_live_words();
    if (arrays || shapes || words) {
        fprintf(stderr, "review-leak arrays=%lld shapes=%lld words=%lld\n", arrays, shapes, words);
        _Exit(92);
    }
    puts("review-clean arrays=0 shapes=0 words=0");
}
void array_review_watch_exit(void) {
    if (atexit(array_review_at_exit)) exit(93);
}
int64_t array_review_list_len(int64_t items) { return freak_v3_array_len(items); }
int64_t array_review_shape_value(int64_t row) { return freak_v3_shape_get(row, 1); }
int64_t array_review_list_first(int64_t items, int64_t ignored) {
    (void)ignored;
    return freak_v3_array_get(items, 0);
}
'''

POSITIVE = {
    "associated_owned_results": (WATCH + '''shape Token { value: num }
impl Token {
    task make(value: num) -> Token { give back Token { value: value } }
    task read(self) -> num { give back self.value }
    task values(value: num) -> List<num> { give back List::filled(value, 3) }
    task label() -> word { give back "owned" + " factory" }
    task announce() -> void { say "factory" }
}
task main() {
    array_review_watch_exit()
    pilot token = Token::make(7)
    say token.read().to_int()
    say token.read().to_int()
    pilot mut values = Token::values(2)
    values[1] = token.read()
    for each value in values { say value.to_int() }
    pilot shapes = [Token::make(9), Token::make(11)]
    for each shape_value in shapes { say shape_value.read().to_int() }
    pilot label = Token::label()
    say label
    Token::announce()
}
''', ["7", "7", "2", "7", "2", "9", "11", "owned factory", "factory", CLEAN], False),
    "filled_word_snapshot": (WATCH + '''pilot mut seed: word = "old" + " value"
task count() -> int {
    seed = "new value"
    give back 2
}
task main() {
    array_review_watch_exit()
    pilot values = List::filled(seed, count())
    say values[0]
    say values[1]
    say seed
}
''', ["old value", "old value", "new value", CLEAN], False),
    "filled_shape_snapshot": (WATCH + ROW + '''pilot mut seed = Row { label: "old" + " shape", value: 3 }
task count() -> int {
    seed = Row { label: "new shape", value: 7 }
    give back 2
}
task main() {
    array_review_watch_exit()
    pilot values = List::filled(seed, count())
    say values[0].label
    say values[1].value
    say seed.label
}
''', ["old shape", "3", "new shape", CLEAN], False),
    "shape_append_snapshot": (WATCH + ROW + '''pilot mut box = Row { label: "old" + "", value: 1 }
task suffix() -> word {
    box.label = "new"
    give back "!"
}
task main() {
    array_review_watch_exit()
    box.label = box.label + suffix()
    say box.label
}
''', ["old!", CLEAN], False),
    "list_word_assignment_snapshot": (WATCH + '''pilot mut words = ["old" + ""]
task suffix() -> word {
    words[0] = "new"
    give back "!"
}
task main() {
    array_review_watch_exit()
    words[0] = words[0] + suffix()
    say words[0]
}
''', ["old!", CLEAN], False),
    "shape_numeric_compound_snapshot": (WATCH + ROW + '''pilot mut box = Row { label: "label", value: 1 }
task increment() -> int {
    box.value = 100
    give back 5
}
task main() {
    array_review_watch_exit()
    box.value += increment()
    say box.value
}
''', ["6", CLEAN], False),
    "extern_temporary_ownership": (COUNTERS + ROW + '''extern task array_review_list_len(items: List<int>) -> int
extern task array_review_shape_value(item: Row) -> int
task work() {
    say array_review_list_len([1, 2, 3])
    say array_review_shape_value(Row { label: "temporary" + " shape", value: 42 })
}
''' + CHECK_ZERO, ["3", "42", "0", "0", "0"], False),
    "extern_global_argument_snapshot": (WATCH + '''extern task array_review_list_first(items: List<int>, ignored: int) -> int
pilot mut values = [4, 5]
task replace() -> int {
    values = [9]
    give back 0
}
task main() {
    array_review_watch_exit()
    say array_review_list_first(values, replace())
    say values[0]
}
''', ["4", "9", CLEAN], False),
    "strict_copy_iteration": (COUNTERS + '''task accept_int(value: int) {}
task accept_num(value: num) {}
task accept_bool(value: bool) {}
task work() {
    for each value in [3, 4] { accept_int(value) say value }
    for each value in [1.25] { accept_num(value) say value }
    for each value in [true] { accept_bool(value) say value }
}
''' + CHECK_ZERO, ["3", "4", "1.25", "true", "0", "0", "0"], True),
}

NEGATIVE = {
    "strict_moved_word_iteration": '''task consume(item: word) {}
task main() {
    for each item in ["owned" + " word"] {
        consume(item)
        say item
    }
}
''',
    "strict_moved_shape_iteration": ROW + '''task consume(item: Row) {}
task main() {
    for each item in [Row { label: "owned", value: 1 }] {
        consume(item)
        say item.label
    }
}
''',
    "strict_moved_word_literal": '''task consume(item: word) {}
task main() {
    pilot item = "owned" + " word"
    consume(item)
    pilot values = [item]
    say values.length()
}
''',
    "strict_moved_shape_literal": ROW + '''task consume(item: Row) {}
task main() {
    pilot item = Row { label: "owned", value: 1 }
    consume(item)
    pilot values = [item]
    say values.length()
}
''',
}


def execute(compiler: Path, repo: Path, root: Path, helper: Path, backend: str,
            name: str, source: str, expected: list[str], strict: bool) -> dict:
    compiled, generated = emission(compiler, root, backend, name, source, strict)
    require_ok(compiled, f"{name}/{backend} emission")
    assert generated.is_file(), f"missing generated source {generated}"
    binary = root / (name + "_" + backend + (".exe" if sys.platform == "win32" else ""))
    runtime = repo / "freakc/runtime"
    clang = shutil.which(os.environ.get("FREAK_CLANG", "clang"))
    assert clang, "Clang is required"
    command = [clang, "-O2", "-g", "-DFREAK_RUNTIME_OWNERSHIP_AUDIT",
               "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT", str(generated), str(helper),
               str(runtime / "freak_runtime.c"), "-I", str(runtime), "-o", str(binary)]
    if backend == "llvm":
        command.append(str(runtime / "freak_llvm_runtime.c"))
    command += ["-D_CRT_SECURE_NO_WARNINGS", "-lws2_32"] if sys.platform == "win32" else ["-lm", "-fsanitize=address", "-fno-omit-frame-pointer"]
    require_ok(run(command, root, 120), f"{name}/{backend} native link")
    executed = run([str(binary)], root)
    require_ok(executed, f"{name}/{backend} execution")
    assert executed.stdout.splitlines() == expected, f"{name}/{backend}: expected {expected!r}, got {executed.stdout!r}\n{executed.stderr}"
    return {"case": name, "backend": backend, "strict": strict, "output": expected}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("compiler", type=Path)
    parser.add_argument("--case", choices=sorted(POSITIVE | NEGATIVE))
    parser.add_argument("--backend", choices=("c", "llvm"))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    compiler = args.compiler.resolve()
    repo = Path(__file__).resolve().parents[1]
    records = []
    with tempfile.TemporaryDirectory(prefix="freak-array-review-") as temporary:
        root = Path(temporary)
        helper = root / "review_helpers.c"
        helper.write_text(HELPER, encoding="utf-8")
        for backend in ([args.backend] if args.backend else ["c", "llvm"]):
            for name, (source, expected, strict) in POSITIVE.items():
                if args.case and name != args.case:
                    continue
                print(f"RUN {name}/{backend}", flush=True)
                records.append(execute(compiler, repo, root, helper, backend, name, source, expected, strict))
                print(f"PASS {name}/{backend}", flush=True)
            for name, source in NEGATIVE.items():
                if args.case and name != args.case:
                    continue
                records.append(expect_rejected(compiler, root, backend, name, source, "You gave this away", True))
                print(f"PASS {name}/{backend}", flush=True)
    if args.report:
        args.report.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(f"V3 array review regressions: PASS ({len(records)} contracts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
