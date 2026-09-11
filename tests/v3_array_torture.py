#!/usr/bin/env python3
"""Adversarial source-level V3 arrays: diagnostics, checked failure and ownership."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

from v3_array_rescue import execute_case, require_ok, run

COUNTERS = '''extern task freak_v3_live_arrays() -> int
extern task freak_v3_live_shapes() -> int
extern task freak_v3_live_words() -> int
'''
CHECK_ZERO = '''
task main() {
    work()
    say freak_v3_live_arrays()
    say freak_v3_live_shapes()
    say freak_v3_live_words()
}
'''
READING = '''shape Reading {
    label: word
    value: num
}
'''

POSITIVE = {
    "explicit_parameter_release": (COUNTERS + '''task dispose(items: List<word>) {
    array_release(items)
}
task work() {
    pilot items = ["caller" + " retains"]
    dispose(items)
    say items[0]
}
''' + CHECK_ZERO, ["caller retains", "0", "0", "0"]),
    "filled_owned": (COUNTERS + READING + '''task work() {
    pilot mut words = List::filled("held" + " word", 3)
    words[1] = "changed"
    for each item in words { say item }
    pilot mut shapes = List::filled(Reading { label: "filled", value: 1.25 }, 3)
    shapes[1] = Reading { label: "changed shape", value: 2.5 }
    for each item in shapes { say item.label }
}
''' + CHECK_ZERO, ["held word", "changed", "held word", "filled", "changed shape", "filled", "0", "0", "0"]),
    "owned_control": (COUNTERS + '''task early() -> word {
    for each item in ["first" + " item", "second"] {
        give back item
    }
    give back "empty"
}
task work() {
    pilot mut words = ["a" + "b", "skip", "stop"]
    for each item in words {
        if item == "skip" { continue }
        if item == "stop" { break }
        words[0] = "replaced"
        say item
    }
    say early()
}
''' + CHECK_ZERO, ["ab", "first item", "0", "0", "0"]),
    "shape_compound": (COUNTERS + READING + '''task work() {
    pilot mut values = [Reading { label: "saved" + " label", value: 1.5 }]
    values[0].value += 2
    say values[0].value
    pilot saved = values[0]
    values[0] = Reading { label: "replacement", value: 9.5 }
    say saved.label
    say saved.value
    for each item in values {
        say item.label
        break
    }
}
''' + CHECK_ZERO, ["3.5", "saved label", "3.5", "replacement", "0", "0", "0"]),
    "temporary_projection": (COUNTERS + READING + '''shape Envelope {
    inner: Reading
}
task make() -> List<Reading> {
    give back [Reading { label: "temp" + " word", value: 3.25 }]
}
task box() -> Envelope {
    give back Envelope { inner: Reading { label: "nested", value: 4.5 } }
}
task work() {
    say make()[0].label
    say make()[0].value
    say box().inner.label
    say box().inner.value
}
''' + CHECK_ZERO, ["temp word", "3.25", "nested", "4.5", "0", "0", "0"]),
    "shape_early_return": (COUNTERS + READING + '''task first() -> Reading {
    for each item in [Reading { label: "first", value: 2.5 }] {
        give back item
    }
    give back Reading { label: "fallback", value: 0 }
}
task work() {
    pilot item = first()
    say item.label
    say item.value
}
''' + CHECK_ZERO, ["first", "2.5", "0", "0", "0"]),
    "empty_and_filled": (COUNTERS + '''task work() {
    pilot words = []
    for each word in words { say "unreachable" }
    say words.length()
    pilot numbers = List::filled(2.5, 0)
    for each number in numbers { say "unreachable" }
    say numbers.length()
    pilot flags = List::filled(true, 3)
    for each flag in flags { say flag }
}
''' + CHECK_ZERO, ["0", "0", "true", "true", "true", "0", "0", "0"]),
    "nested_loop_exits": (COUNTERS + '''task work() {
    for each outer in ["a", "b"] {
        for each inner in ["skip", "keep", "stop"] {
            if inner == "skip" { continue }
            if inner == "stop" { break }
            say outer + inner
        }
    }
}
''' + CHECK_ZERO, ["akeep", "bkeep", "0", "0", "0"]),
    "single_evaluation": (COUNTERS + '''pilot mut receivers = 0
pilot mut indices = 0
pilot mut rhs_calls = 0
pilot mut shared = [10]
task receiver() -> List<int> {
    receivers += 1
    give back shared
}
task index() -> int {
    indices += 1
    give back 0
}
task rhs() -> int {
    rhs_calls += 1
    give back 5
}
task main() {
    pilot mut values = receiver()
    values[index()] += rhs()
    say receivers
    say indices
    say rhs_calls
    say shared[0]
}
''', ["1", "1", "1", "15"]),
    "receiver_replacement": ('''pilot mut shared = [10]
task replace_index() -> int {
    shared = [20]
    give back 0
}
task replace_rhs() -> int {
    shared = [30]
    give back 5
}
task main() {
    say shared[replace_index()]
    say shared[0]
    pilot saved = shared
    shared[0] += replace_rhs()
    say saved[0]
    say shared[0]
}
''', ["10", "20", "25", "30"]),
    "receiver_reads_and_length": (COUNTERS + '''pilot mut calls = 0
task create() -> List<int> {
    calls += 1
    give back [5, 6]
}
task work() {
    say create()[0]
    say create().length()
    for each value in create() { say value }
    say calls
}
''' + CHECK_ZERO, ["5", "2", "5", "6", "3", "0", "0", "0"]),
    "legacy_word_alias_release": (COUNTERS + '''task work() {
    pilot mut words = ["before" + " replacement"]
    pilot alias = words
    pilot saved = array_get(words, 0)
    array_set(words, 0, "after")
    array_release(words)
    say saved
    say alias[0]
}
''' + CHECK_ZERO, ["before replacement", "after", "0", "0", "0"]),
}

# Assert meaningful stable diagnostic fragments and no emitted artifact.
NEGATIVE = {
    "temporary_assignment": ('task make() -> List<int> { give back [1] }\nmake()[0] = 2\n', "mutable list binding"),
    "list_shape_field": ('shape Holder { values: List<int> }\n', "V3 owned shape fields do not yet support List values"),
    "num_index": ('pilot values = [1]\nsay values[0.5]\n', "index must have type int"),
    "bool_index": ('pilot values = [1]\nsay values[true]\n', "index must have type int"),
    "word_index": ('pilot values = [1]\nsay values["zero"]\n', "index must have type int"),
    "mixed_literal": ('pilot values = [1, "two"]\n', "list element expects"),
    "bool_numeric_literal": ('pilot values = [true, 1]\n', "list element expects"),
    "wrong_store": ('pilot mut values = [1]\nvalues[0] = "bad"\n', "cannot assign"),
    "narrow_num_store": ('pilot mut values = [1]\nvalues[0] = 2.5\n', "cannot assign"),
    "bool_store": ('pilot mut values = [true]\nvalues[0] = 1\n', "cannot assign"),
    "immutable_store": ('pilot values = [1]\nvalues[0] = 2\n', "mutable list binding"),
    "immutable_compound": ('pilot values = [1]\nvalues[0] += 2\n', "mutable list binding"),
    "filled_num_count": ('pilot values = List::filled(0, 2.5)\n', "expects int"),
    "filled_bool_count": ('pilot values = List::filled(0, true)\n', "expects int"),
    "filled_missing_count": ('pilot values = List::filled(0)\n', "expects 2"),
    "list_widening": ('pilot values: List<num> = [1, 2]\n', "List<int>"),
    "non_list_iteration": ('for each item in 3 { say item }\n', "for each requires a list"),
}

PANIC = {}
for label, offset in (("negative", "-1"), ("at_length", "2"), ("extreme", "9223372036854775807")):
    PANIC[f"read_{label}"] = (f'pilot values = [1, 2]\nsay values[{offset}]\n', "out of bounds")
    PANIC[f"write_{label}"] = (f'pilot mut values = [1, 2]\nvalues[{offset}] = 9\n', "out of bounds")
PANIC["empty_read"] = ('pilot values = List::filled(0, 0)\nsay values[0]\n', "out of bounds")
PANIC["negative_count"] = ('pilot values = List::filled(0, -1)\n', "negative or too large")
PANIC["overflow_count"] = ('pilot values = List::filled(0, 9223372036854775807)\n', "negative or too large")


def emission(compiler: Path, root: Path, backend: str, name: str, source: str, strict: bool = False):
    fixture = root / f"{name}_{backend}.fk"
    fixture.write_text(source, encoding="utf-8")
    command = [str(compiler), str(fixture), f"--{backend}"]
    if strict:
        command.append("--strict-borrow")
    compiled = run(command, root)
    generated = Path(str(fixture) + (".c" if backend == "c" else ".ll"))
    return compiled, generated


def expect_rejected(compiler: Path, root: Path, backend: str, name: str, source: str, diagnostic: str, strict: bool = False):
    compiled, generated = emission(compiler, root, backend, name, source, strict)
    output = compiled.stdout + compiled.stderr
    assert compiled.returncode != 0, f"{name}/{backend}: invalid source accepted\n{output}"
    assert diagnostic.lower() in output.lower(), f"{name}/{backend}: missing {diagnostic!r}\n{output}"
    assert not generated.exists(), f"{name}/{backend}: emitted invalid artifact {generated}"
    return {"case": name, "backend": backend, "kind": "diagnostic", "strict": strict}


def native_run(repo: Path, root: Path, backend: str, name: str, generated: Path):
    assert generated.is_file(), f"missing generated artifact {generated}"
    binary = root / (name + "_" + backend + (".exe" if sys.platform == "win32" else ""))
    runtime = repo / "freakc/runtime"
    clang = shutil.which(os.environ.get("FREAK_CLANG", "clang"))
    assert clang, "Clang is required"
    command = [clang, "-O2", str(generated), str(runtime / "freak_runtime.c"), "-I", str(runtime), "-o", str(binary)]
    if backend == "llvm":
        command.append(str(runtime / "freak_llvm_runtime.c"))
    command += ["-D_CRT_SECURE_NO_WARNINGS", "-lws2_32"] if sys.platform == "win32" else ["-lm", "-fsanitize=address", "-fno-omit-frame-pointer"]
    require_ok(run(command, root, 120), f"{name}/{backend} native link")
    return run([str(binary)], root)


def expect_panic(compiler: Path, repo: Path, root: Path, backend: str, name: str, source: str, diagnostic: str):
    compiled, generated = emission(compiler, root, backend, name, source)
    require_ok(compiled, f"{name}/{backend} emission")
    executed = native_run(repo, root, backend, name, generated)
    output = executed.stdout + executed.stderr
    assert executed.returncode == 1, f"{name}/{backend}: expected controlled exit 1, got {executed.returncode}\n{output}"
    assert diagnostic in output, f"{name}/{backend}: missing panic {diagnostic!r}\n{output}"
    assert "ERROR: AddressSanitizer" not in output, f"{name}/{backend}: memory safety failure\n{output}"
    return {"case": name, "backend": backend, "kind": "checked-panic"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("compiler", type=Path)
    parser.add_argument("--backend", choices=("c", "llvm"))
    parser.add_argument("--case", choices=sorted(POSITIVE | NEGATIVE | PANIC | {"strict_immutable": None, "strict_primitive": None}))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    compiler = args.compiler.resolve()
    repo = Path(__file__).resolve().parents[1]
    records = []
    with tempfile.TemporaryDirectory(prefix="freak-v3-array-torture-") as temporary:
        root = Path(temporary)
        for backend in ([args.backend] if args.backend else ["c", "llvm"]):
            for name, (source, expected) in POSITIVE.items():
                if args.case and args.case != name:
                    continue
                print(f"RUN {name}/{backend}", flush=True)
                records.append(execute_case(compiler, repo, root, backend, name, source, expected))
                print(f"PASS {name}/{backend}", flush=True)
            for name, (source, diagnostic) in NEGATIVE.items():
                if args.case and args.case != name:
                    continue
                records.append(expect_rejected(compiler, root, backend, name, source, diagnostic))
                print(f"PASS {name}/{backend}", flush=True)
            for name, (source, diagnostic) in PANIC.items():
                if args.case and args.case != name:
                    continue
                records.append(expect_panic(compiler, repo, root, backend, name, source, diagnostic))
                print(f"PASS {name}/{backend}", flush=True)
            if not args.case or args.case == "strict_primitive":
                source = "pilot mut values = [1, 2]\nvalues[0] += 3\nfor each value in values { say value }\n"
                compiled, generated = emission(compiler, root, backend, "strict_primitive", source, True)
                require_ok(compiled, f"strict_primitive/{backend} emission")
                executed = native_run(repo, root, backend, "strict_primitive", generated)
                require_ok(executed, f"strict_primitive/{backend} execution")
                assert executed.stdout.splitlines() == ["4", "2"], executed.stdout + executed.stderr
                records.append({"case": "strict_primitive", "backend": backend, "kind": "strict-native"})
                print(f"PASS strict_primitive/{backend}", flush=True)
            if not args.case or args.case == "strict_immutable":
                source, diagnostic = NEGATIVE["immutable_store"]
                records.append(expect_rejected(compiler, root, backend, "strict_immutable", source, diagnostic, True))
                print(f"PASS strict_immutable/{backend}", flush=True)
    if args.report:
        args.report.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(f"V3 array torture: PASS ({len(records)} contracts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
