#!/usr/bin/env python3
"""V3.5 list equality (#279), split/join/contains (#280), shared word arguments (#285).

`==` / `!=` on lists used to compare container handles, so two lists with the
same contents were unequal. They now compare length and elements on LLVM and
C; lists of shapes are rejected because V3.5 shapes have no `==`.

Passing a word to a user task used to copy the whole string on every call
(LLVM always; C unless the callee passed a narrow read-only analysis). LLVM
now shares the tracked allocation with the callee, and C borrows for callees
that only read scalars such as byte_length(). Every case runs under the
ownership audit and ASan (on POSIX), and the live counters must reach zero.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from v3_array_rescue import execute_case
from v3_list_methods import expect_rejected

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

POSITIVE = {
    "list_equality": (COUNTERS + '''task names() -> List<word> { give back ["x", "y"] }
task work() {
    pilot a = ["x", "y"]
    pilot b = ["x", "y"]
    say a == b
    say a != b
    say a == ["x"]
    say names() == a
    say names() != ["x", "z"]
    pilot e: List<word> = []
    pilot f: List<word> = []
    say e == f
    say [1, 2, 3] == [1, 2, 3]
    say [1, 2, 3] == [1, 2, 4]
    say [1.5, 2] == [1.5, 2.0]
    say [true, false] == [true, true]
    pilot mut d: List<word> = []
    d.push("x" + "")
    d.push("y")
    say d == a
    d.push("z")
    say d == a
    say d != a
}
''' + CHECK_ZERO, ["true", "false", "false", "true", "true", "true", "true", "false",
                   "true", "false", "true", "false", "true", "0", "0", "0"]),
    "shared_word_arguments": (COUNTERS + '''task keep(s: word) -> word { give back s }
task grow(s: word) -> word {
    s = s + "!"
    give back s
}
task grow_in_place(s: word) -> word {
    s += "?"
    give back s
}
task reset(s: word) -> int {
    s = "fresh"
    give back s.byte_length()
}
task stash(xs: List<word>, s: word) -> int {
    xs.push(s)
    give back xs.length()
}
task twice(a: word, b: word) -> word { give back a + b }
task trimmed(s: word) -> word { give back s.trim() }
task work() {
    pilot mut s = "ab" + "cd"
    s = keep(s)
    s = keep(s)
    say s
    pilot t = keep(s)
    s = s + "e"
    say s
    say t
    pilot u = grow(s)
    say s
    say u
    pilot v = grow_in_place(s)
    say s
    say v
    say reset(s)
    say s
    pilot mut xs: List<word> = []
    say stash(xs, s)
    s += "f"
    say xs[0]
    say s
    say twice(s, s)
    pilot mut w = "  pad  " + ""
    w = trimmed(w)
    say "[{w}]"
    w = keep(w) + keep(w)
    say w
    pilot mut z = keep(s)
    z += "g"
    say z
    say s
}
''' + CHECK_ZERO, ["abcd", "abcde", "abcd", "abcde", "abcde!", "abcde", "abcde?", "5", "abcde",
                   "1", "abcde", "abcdef", "abcdefabcdef", "[pad]", "padpad", "abcdefg", "abcdef",
                   "0", "0", "0"]),
    "review_regressions": (COUNTERS + """pilot mut held = [1, 2]
task replace_held() -> List<int> {
    held = [3, 4]
    give back [1, 2]
}
pilot mut text = "a,b" + ""
task replace_text() -> word {
    text = "zz" + ""
    give back ","
}
task replace_held_value() -> int {
    held = [7, 8]
    give back 3
}
task replace_held_sep() -> word {
    held = [9]
    give back "-"
}
task keep(s: word) -> word { give back s }
task work() {
    say held == replace_held()
    say held != replace_held()
    pilot mut s = "ab" + "cd"
    s += keep(s)
    say s
    pilot items = array_new()
    array_push(items, "x" + "y")
    array_set(items, 0, array_get(items, 0))
    say array_get(items, 0)
    array_release(items)
    say text.split(replace_text()).length()
    say text
    say held.contains(replace_held_value())
    say held.join(replace_held_sep())
    say held.length()
}
task main() {
    work()
    held = [0]
    text = ""
    say freak_v3_live_arrays()
    say freak_v3_live_shapes()
    say freak_v3_live_words()
}
""", ["true", "true", "abcdabcd", "xy", "2", "zz", "true", "7-8", "1", "1", "0", "0"]),
    "split_join_contains": (COUNTERS + """task csv() -> word { give back "a,b,,c" }
task work() {
    pilot parts = "a,b,,c".split(",")
    say parts.length()
    say parts.join("|")
    say "".split(",").length()
    say "abc".split("").length()
    say "one::two::three".split("::")[2]
    say csv().split(",").join("+")
    pilot lines = "# Title\nbody\n".split("\n")
    say lines.length()
    say lines.contains("body")
    say lines.contains("nope")
    say lines.contains("bo" + "dy")
    pilot sep = ", "
    say ["x", "y", "z"].join(sep)
    say [1, 2, 3].join("-")
    say [1.5, 2.0, 3].join(" ")
    say [true, false].join("/")
    say [1, 2, 3].contains(2)
    say [1, 2, 3].contains(5)
    say [1.5, 2].contains(2)
    pilot empty: List<word> = []
    say "[" + empty.join(",") + "]"
    for each p in "x y z".split(" ") { say p.to_upper() }
}
""" + CHECK_ZERO, ["4", "a|b||c", "1", "1", "three", "a+b++c", "3", "true", "false", "true",
                   "x, y, z", "1-2-3", "1.5 2 3", "true/false", "true", "false", "true", "[]",
                   "X", "Y", "Z", "0", "0", "0"]),
    # 20,000 calls with an 8 MiB word: copying it per call is ~160 GB of memcpy.
    "word_argument_is_not_copied": ('''task measure(s: word, i: int) -> int { give back s.byte_length() + i }
task peek(s: word, i: int) -> int {
    if s.char_at(i % 7) == "x" { give back 1 }
    give back 0
}
task main() {
    pilot big = "x".repeated(8388608)
    pilot mut acc = 0
    pilot mut hits = 0
    pilot mut i = 0
    repeat while i < 20000 {
        acc += measure(big, i)
        hits += peek(big, i)
        i += 1
    }
    say acc
    say hits
}
''', ["167972150000", "20000"]),
}

NEGATIVE = {
    "shape_list_equality": ('''shape P {
    x: int
}
task main() {
    pilot a = [P { x: 1 }]
    pilot b = [P { x: 1 }]
    say a == b
}
''', "P values have no '==' in V3.5"),
    "shape_list_contains": ('''shape P {
    x: int
}
task main() {
    pilot a = [P { x: 1 }]
    say a.contains(P { x: 1 })
}
''', "has no method 'contains'"),
    "split_needs_word": ('''task main() {
    say "a1b".split(1).length()
}
''', "split"),
    "mixed_list_equality": ('''task main() {
    pilot a = ["x"]
    pilot b = [1]
    say a == b
}
''', "operator '==' does not accept List<word> and List<int>"),
}

SPEED_LIMIT_SECONDS = 3.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("compiler", type=Path, help="fresh self-hosted V3 standalone compiler")
    parser.add_argument("--backend", choices=("c", "llvm"))
    parser.add_argument("--case", choices=sorted(set(POSITIVE) | set(NEGATIVE)))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    compiler = args.compiler.resolve()
    repo = Path(__file__).resolve().parents[1]
    records = []
    with tempfile.TemporaryDirectory(prefix="freak-v3-list-eq-share-") as temporary:
        root = Path(temporary)
        for backend in ([args.backend] if args.backend else ["c", "llvm"]):
            for name, (source, expected) in POSITIVE.items():
                if args.case and args.case != name:
                    continue
                print(f"RUN {name}/{backend}", flush=True)
                record = execute_case(compiler, repo, root, backend, name, source, expected)
                if name == "word_argument_is_not_copied" and record["seconds"] > SPEED_LIMIT_SECONDS:
                    raise AssertionError(
                        f"{name}/{backend}: {record['seconds']:.1f}s; word arguments are being copied per call")
                records.append(record)
                print(f"PASS {name}/{backend} ({record['seconds']:.2f}s)", flush=True)
            for name, (source, diagnostic) in NEGATIVE.items():
                if args.case and args.case != name:
                    continue
                records.append(expect_rejected(compiler, root, backend, name, source, diagnostic))
                print(f"PASS {name}/{backend}", flush=True)
    if args.report:
        args.report.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(f"V3 list equality and word sharing: PASS ({len(records)} contracts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
