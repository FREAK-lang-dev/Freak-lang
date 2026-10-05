#!/usr/bin/env python3
"""Check native JSON document and sleep builtin signatures and emitted calls.

JSON parsing, generation and runtime lifetime behavior have independent native
execution gates. This verifies typed compiler admission, exact runtime symbols,
owned-buffer classification and explicit document consumption.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import tempfile

from v3_checked_parsing import build_stage2
from v3_v35_language import require_ok, run

APIS = [
    [
        "new",
        [],
        "int"
    ],
    [
        "parse",
        [
            "word"
        ],
        "int"
    ],
    [
        "parse_bytes",
        [
            "ByteBuffer"
        ],
        "int"
    ],
    [
        "ok",
        [
            "int"
        ],
        "int"
    ],
    [
        "error",
        [
            "int"
        ],
        "word"
    ],
    [
        "error_position",
        [
            "int"
        ],
        "int"
    ],
    [
        "root",
        [
            "int"
        ],
        "int"
    ],
    [
        "set_root",
        [
            "int",
            "int"
        ],
        "int"
    ],
    [
        "release",
        [
            "int"
        ],
        "void"
    ],
    [
        "kind",
        [
            "int",
            "int"
        ],
        "int"
    ],
    [
        "count",
        [
            "int",
            "int"
        ],
        "int"
    ],
    [
        "array_get",
        [
            "int",
            "int",
            "int"
        ],
        "int"
    ],
    [
        "object_get",
        [
            "int",
            "int",
            "word"
        ],
        "int"
    ],
    [
        "object_get_bytes",
        [
            "int",
            "int",
            "ByteBuffer"
        ],
        "int"
    ],
    [
        "object_key_bytes",
        [
            "int",
            "int",
            "int"
        ],
        "ByteBuffer"
    ],
    [
        "bool_value",
        [
            "int",
            "int"
        ],
        "int"
    ],
    [
        "number_text",
        [
            "int",
            "int"
        ],
        "word"
    ],
    [
        "string_word",
        [
            "int",
            "int"
        ],
        "word"
    ],
    [
        "string_bytes",
        [
            "int",
            "int"
        ],
        "ByteBuffer"
    ],
    [
        "make_null",
        [
            "int"
        ],
        "int"
    ],
    [
        "make_bool",
        [
            "int",
            "int"
        ],
        "int"
    ],
    [
        "make_number",
        [
            "int",
            "word"
        ],
        "int"
    ],
    [
        "make_string",
        [
            "int",
            "word"
        ],
        "int"
    ],
    [
        "make_string_bytes",
        [
            "int",
            "ByteBuffer"
        ],
        "int"
    ],
    [
        "make_array",
        [
            "int"
        ],
        "int"
    ],
    [
        "make_object",
        [
            "int"
        ],
        "int"
    ],
    [
        "array_append",
        [
            "int",
            "int",
            "int"
        ],
        "int"
    ],
    [
        "object_insert",
        [
            "int",
            "int",
            "word",
            "int"
        ],
        "int"
    ],
    [
        "object_insert_bytes",
        [
            "int",
            "int",
            "ByteBuffer",
            "int"
        ],
        "int"
    ],
    [
        "serialize_word",
        [
            "int"
        ],
        "word"
    ],
    [
        "serialize_bytes",
        [
            "int"
        ],
        "ByteBuffer"
    ]
]
LINES = ["task main() {", "pilot bytes = ByteBuffer::new()", "pilot doc = json_document::new()"]
for operation, params, result in APIS:
    if operation in ("new", "release"):
        continue
    arguments = ["bytes" if param == "ByteBuffer" else '"text"' if param == "word" else "doc" if index == 0 else "1" for index, param in enumerate(params)]
    call = "json_document::" + operation + "(" + ", ".join(arguments) + ")"
    if result == "ByteBuffer":
        LINES.extend(["pilot buffer_" + operation + " = " + call, "buffer_" + operation + ".release()"])
    else:
        LINES.append("say " + call)
LINES.extend(["time::sleep(0)", "bytes.release()", "json_document::release(doc)", "}"])
PROGRAM = "\n".join(LINES) + "\n"

NEGATIVE = {
    "arm_keyword_binding": ('pilot ok = 1', "expected an identifier", False),
    "unknown_keyword_namespace": ('other::ok(1)', "expected an identifier", False),
    "parse_bytes_type": ('json_document::parse_bytes(1)', "argument 1 expects ByteBuffer, got int", False),
    "bytes_key_type": ('json_document::object_get_bytes(1, 1, "key")', "argument 3 expects ByteBuffer, got word", False),
    "insert_bytes_key_type": ('json_document::object_insert_bytes(1, 1, "key", 1)', "argument 3 expects ByteBuffer, got word", False),
    "number_type": ('json_document::make_number(1, 1)', "argument 2 expects word, got int", False),
    "object_arity": ('json_document::object_insert(1, 1, "key")', "expects 4 argument(s), got 3", False),
    "owned_word_type": ('pilot value: int = json_document::string_word(1, 1)', "cannot initialize int binding 'value' with word", False),
    "status_is_int": ('if json_document::ok(1) {}', "condition must have type bool, got int", False),
    "inferred_buffer_owner": ('pilot value = json_document::string_bytes(1, 1)\nvalue.release()\nvalue.length()', "You gave this away", True),
    "released_document": ('pilot doc: int = json_document::new()\njson_document::release(doc)\njson_document::ok(doc)', "You gave this away", True),
    "unknown_operation": ('json_document::parse_magic("text")', "unknown callable 'json_document::parse_magic'", False),
    "sleep_type": ('time::sleep("milliseconds")', "argument 1 expects int, got word", False),
    "sleep_arity": ('time::sleep()', "expects 1 argument(s), got 0", False),
    "sleep_void": ('pilot value = time::sleep(0)', "binding initializer cannot have type void", False),
    "namespace_shape": ('shape json_document {}', "conflicts with a compiler builtin namespace", False),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", type=Path, help="fresh exact-source native stage2 compiler")
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG") or shutil.which("clang"))
    args = parser.parse_args()
    assert args.clang, "Clang required"
    repo = Path(__file__).resolve().parents[1]
    inventory = []
    with tempfile.TemporaryDirectory(prefix="freak-v35-json-compiler-") as directory:
        root = Path(directory)
        compiler = args.compiler.resolve(strict=True) if args.compiler else build_stage2(clang=args.clang, repo=repo, root=root)
        for backend in ("c", "llvm"):
            source = root / (backend + "_json_api.fk")
            source.write_text(PROGRAM)
            require_ok(run([str(compiler), str(source), "--" + backend, "--strict-borrow"], root), "JSON API emission")
            suffix = ".c" if backend == "c" else ".ll"
            emitted = Path(str(source) + suffix).read_text()
            prefix = "freak_json_document_" if backend == "c" else "@freak_llvm_json_document_"
            for operation, _, _ in APIS:
                symbol = prefix + operation + "("
                assert symbol in emitted, (backend, operation)
                if backend == "llvm":
                    assert any("call " in line and symbol in line for line in emitted.splitlines()), (backend, operation)
            sleep = "freak_time_sleep(" if backend == "c" else "@freak_llvm_time_sleep("
            assert sleep in emitted
            if backend == "llvm":
                assert any("call void " in line and sleep in line for line in emitted.splitlines())
            assert "__freak_user_json_document_" not in emitted
            inventory.append((backend, "positive"))
            print("PASS", backend, "JSON 31-operation and sleep emission", flush=True)
            for name, (body, diagnostic, strict) in NEGATIVE.items():
                program = body + "\ntask main() {}\n" if name == "namespace_shape" else "task main() {\n" + body + "\n}\n"
                source = root / (backend + "_" + name + ".fk")
                source.write_text(program)
                artifact = Path(str(source) + suffix)
                artifact.write_text("stale JSON output")
                command = [str(compiler), str(source), "--" + backend]
                if strict:
                    command.append("--strict-borrow")
                rejected = run(command, root)
                assert rejected.returncode != 0 and diagnostic in rejected.stdout + rejected.stderr, (backend, name, diagnostic, rejected)
                assert not artifact.exists(), (backend, name, "stale artifact survived")
                inventory.append((backend, name))
                print("PASS", backend, name, flush=True)
    expected = {(backend, name) for backend in ("c", "llvm") for name in ("positive", *NEGATIVE)}
    assert set(inventory) == expected and len(inventory) == len(expected)
    print(f"V3.5 JSON compiler contracts: PASS ({len(inventory)} cases)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
