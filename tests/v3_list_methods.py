#!/usr/bin/env python3
"""V3 List ergonomics: new/with_capacity constructors plus push/pop/clear/reserve/capacity methods.

Covers typed empty construction, owned word/shape cleanup, and diagnostics on
both native backends with C/LLVM parity.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

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
    "typed_empty_num": ('''task work() {
    pilot mut xs: List<num> = []
    say xs.length()
    say xs.capacity()
    xs.push(1.5)
    xs.push(1)
    say xs.length()
    say xs[0]
    say xs[1]
    say xs.pop()
    say xs.length()
}
task main() {
    work()
}
''', ["0", "8", "2", "1.5", "1", "1", "1"]),
    "list_new_int": ('''task work() {
    pilot mut xs: List<int> = List::new()
    say xs.length()
    xs.push(7)
    xs.push(8)
    say xs.length()
    say xs[0]
    say xs.pop()
    say xs.length()
}
task main() {
    work()
}
''', ["0", "2", "7", "8", "1"]),
    "reassign_new_word_kind": ('''task work() {
    pilot mut ws: List<word> = List::new()
    ws.push("a")
    say ws.length()
    ws = List::new()
    say ws.length()
    ws.push("b")
    say ws.length()
    say ws[0]
}
task main() {
    work()
}
''', ["1", "0", "1", "b"]),
    "with_capacity_growth": ('''task work() {
    pilot mut xs: List<int> = List::with_capacity(16)
    say xs.length()
    say xs.capacity()
    xs.push(1)
    xs.push(2)
    say xs.length()
    say xs[1]
    xs.reserve(32)
    say xs.capacity()
    say xs.length()
}
task main() {
    work()
}
''', ["0", "16", "2", "2", "32", "2"]),
    "push_pop_mixed_types": ('''task work() {
    pilot mut flags: List<bool> = List::new()
    flags.push(true)
    flags.push(false)
    say flags.pop()
    say flags[0]
    pilot mut nums: List<num> = []
    nums.push(2)
    say nums[0]
    say nums.pop()
}
task main() {
    work()
}
''', ["false", "true", "2", "2"]),
    "clear_and_iterate": ('''task work() {
    pilot mut xs = [1, 2, 3]
    say xs.length()
    xs.clear()
    say xs.length()
    xs.push(9)
    for each x in xs { say x }
    xs.clear()
    for each x in xs { say "unreachable" }
    say xs.length()
}
task main() {
    work()
}
''', ["3", "0", "9", "0"]),
    "owned_word_cleanup": (COUNTERS + '''task work() {
    pilot mut words: List<word> = []
    words.push("hello" + " world")
    words.push("second")
    say words.length()
    say words.pop()
    say words.length()
    say words[0]
    words.clear()
    say words.length()
    pilot mut more: List<word> = List::new()
    more.push("kept")
    say more.pop()
}
''' + CHECK_ZERO, ["2", "second", "1", "hello world", "0", "kept", "0", "0", "0"]),
    "owned_shape_cleanup": (COUNTERS + READING + '''task work() {
    pilot mut shapes: List<Reading> = List::new()
    shapes.push(Reading { label: "first", value: 1.5 })
    shapes.push(Reading { label: "second", value: 2.5 })
    say shapes.length()
    pilot taken = shapes.pop()
    say taken.label
    say shapes.length()
    say shapes[0].label
    shapes.clear()
    say shapes.length()
}
''' + CHECK_ZERO, ["2", "second", "1", "first", "0", "0", "0", "0"]),
    "capacity_stable": ('''task work() {
    pilot mut xs: List<int> = List::with_capacity(16)
    pilot before = xs.capacity()
    xs.push(1)
    say xs.capacity()
    say xs.length()
    xs.reserve(4)
    say xs.capacity()
}
task main() {
    work()
}
''', ["16", "1", "16"]),
}

NEGATIVE = {
    "push_wrong_type": ('pilot mut xs = [1]\nxs.push("bad")\n', "expects int"),
    "push_bool_into_int": ('pilot mut xs = [1]\nxs.push(true)\n', "expects int"),
    "push_arity": ('pilot mut xs: List<int> = []\nxs.push(1, 2)\n', "expects 1"),
    "push_missing": ('pilot mut xs: List<int> = []\nxs.push()\n', "expects 1"),
    "pop_arity": ('pilot mut xs: List<int> = []\nsay xs.pop(1)\n', "expects 0"),
    "clear_arity": ('pilot mut xs = [1]\nxs.clear(1)\n', "expects 0"),
    "capacity_arity": ('pilot xs = [1]\nsay xs.capacity(1)\n', "expects 0"),
    "reserve_wrong_type": ('pilot mut xs = [1]\nxs.reserve("big")\n', "expects int"),
    "reserve_arity": ('pilot mut xs = [1]\nxs.reserve()\n', "expects 1"),
    "immutable_push": ('pilot xs = [1]\nxs.push(2)\n', "mutable list binding"),
    "immutable_pop": ('pilot xs = [1]\nsay xs.pop()\n', "mutable list binding"),
    "immutable_clear": ('pilot xs = [1]\nxs.clear()\n', "mutable list binding"),
    "immutable_reserve": ('pilot xs = [1]\nxs.reserve(8)\n', "mutable list binding"),
    "new_arity": ('pilot mut xs: List<int> = List::new(1)\n', "expects 0"),
    "with_capacity_missing": ('pilot mut xs: List<int> = List::with_capacity()\n', "expects 1"),
    "with_capacity_wrong_type": ('pilot mut xs: List<int> = List::with_capacity("big")\n', "expects int"),
    "uninferred_new": ('pilot xs = List::new()\n', "cannot infer"),
    "uninferred_with_capacity": ('pilot xs = List::with_capacity(4)\n', "cannot infer"),
    "unannotated_new_arg": ('task take(xs: List<int>) -> int {\n    give back xs[0]\n}\ntask main() {\n    say take(List::new())\n}\n', "unresolved type"),
    "unannotated_new_return": ('task gen() -> List<int> {\n    give back List::new()\n}\ntask main() {\n    pilot xs = gen()\n    say xs.length()\n}\n', "no known type"),
    "reassign_new_nonword_kind": ('pilot mut xs: List<int> = [1]\nxs = List::new()\n', "without a known element type"),
    "reassign_with_capacity_nonword_kind": ('pilot mut xs: List<num> = []\nxs = List::with_capacity(4)\n', "without a known element type"),
    "reassign_new_scalar_receiver": ('pilot mut n = 1\nn = List::new()\n', "without a known element type"),
    "unknown_list_method": ('pilot mut xs = [1]\nxs.insert(0, 2)\n', "has no method"),
}

PANIC = {
    "pop_empty": ('pilot mut xs: List<int> = []\nsay xs.pop()\n', "out of bounds"),
    "pop_empty_word": ('pilot mut words: List<word> = []\nsay words.pop()\n', "out of bounds"),
    "pop_drained": ('pilot mut xs = [1]\nsay xs.pop()\nsay xs.pop()\n', "out of bounds"),
    "reserve_negative": ('pilot mut xs = [1]\nxs.reserve(-1)\n', "negative or too large"),
    "with_capacity_negative": ('pilot mut xs: List<int> = List::with_capacity(-1)\n', "negative or too large"),
}


def emission(compiler: Path, root: Path, backend: str, name: str, source: str):
    """Emit one list-method fixture and return its process and artifact."""
    fixture = root / f"{name}_{backend}.fk"
    fixture.write_text(source, encoding="utf-8")
    command = [str(compiler), str(fixture), f"--{backend}"]
    compiled = run(command, root)
    generated = Path(str(fixture) + (".c" if backend == "c" else ".ll"))
    return compiled, generated


def expect_rejected(compiler: Path, root: Path, backend: str, name: str, source: str, diagnostic: str):
    """Verify an invalid list-method fixture is rejected without output."""
    compiled, generated = emission(compiler, root, backend, name, source)
    output = compiled.stdout + compiled.stderr
    assert compiled.returncode != 0, f"{name}/{backend}: invalid source accepted\n{output}"
    assert diagnostic.lower() in output.lower(), f"{name}/{backend}: missing {diagnostic!r}\n{output}"
    assert not generated.exists(), f"{name}/{backend}: emitted invalid artifact {generated}"
    return {"case": name, "backend": backend, "kind": "diagnostic"}


def native_run(repo: Path, root: Path, backend: str, name: str, generated: Path):
    """Link and run one generated list-method fixture under ASan."""
    import os
    import shutil
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
    """Verify a list runtime violation exits through a checked panic."""
    compiled, generated = emission(compiler, root, backend, name, source)
    require_ok(compiled, f"{name}/{backend} emission")
    executed = native_run(repo, root, backend, name, generated)
    output = executed.stdout + executed.stderr
    assert executed.returncode == 1, f"{name}/{backend}: expected controlled exit 1, got {executed.returncode}\n{output}"
    assert diagnostic in output, f"{name}/{backend}: missing panic {diagnostic!r}\n{output}"
    assert "ERROR: AddressSanitizer" not in output, f"{name}/{backend}: memory safety failure\n{output}"
    return {"case": name, "backend": backend, "kind": "checked-panic"}


def main() -> int:
    """Run the selected V3 list-method regression matrix."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("compiler", type=Path)
    parser.add_argument("--backend", choices=("c", "llvm"))
    parser.add_argument("--case", choices=sorted(set(POSITIVE) | set(NEGATIVE) | set(PANIC)))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    compiler = args.compiler.resolve()
    repo = Path(__file__).resolve().parents[1]
    records = []
    with tempfile.TemporaryDirectory(prefix="freak-v3-list-methods-") as temporary:
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
    if args.report:
        args.report.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(f"V3 list methods: PASS ({len(records)} contracts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
