#!/usr/bin/env python3
"""Strict-borrow builtin handle contracts on an exact native CLI, C and LLVM."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import v3_byte_buffer_foundation as byte_foundation
import v3_word_foundation as foundation


BUILDER = '''task main() {
    repeat 8 times {
        pilot builder = word_builder::new()
        pilot text = "x"
        word_builder::reserve(builder, 32)
        if word_builder::capacity(builder) < 32 { process::exit(2) }
        word_builder::append(builder, text)
        word_builder::append(builder, text)
        word_builder::append_char(builder, 121)
        word_builder::append_int(builder, 7)
        if word_builder::length(builder) != 4 { process::exit(3) }
        word_builder::clear(builder)
        word_builder::append(builder, text)
        pilot finished = word_builder::finish(builder)
        if finished != "x" or text != "x" { process::exit(4) }
        pilot spare: int = word_builder::with_capacity(1)
        word_builder::append(spare, text)
        word_builder::discard(spare)
    }
    say "builder-ok"
}
'''

SOCKET = '''task main() {
    repeat 4 times {
        pilot listener = tcp::socket_listen("127.0.0.1", 0, 1)
        if tcp::socket_status(listener) != 0 { process::exit(2) }
        tcp::socket_set_timeout(listener, 1000, 1000)
        pilot client: int = tcp::socket_connect("127.0.0.1", tcp::socket_local_port(listener))
        if tcp::socket_status(client) != 0 { process::exit(3) }
        tcp::socket_set_timeout(client, 1000, 1000)
        pilot peer = tcp::socket_accept(listener)
        if tcp::socket_status(peer) != 0 { process::exit(4) }
        tcp::socket_set_timeout(peer, 1000, 1000)
        pilot payload: ByteBuffer = ByteBuffer::new()
        pilot text = "ping"
        payload.reserve(32)
        payload.write_word(text)
        if text != "ping" { process::exit(5) }
        if tcp::socket_send(client, payload, 0, 0) != 0 { process::exit(6) }
        if tcp::socket_send_all(client, payload, 0, payload.length()) != 4 { process::exit(7) }
        if payload.status() != 0 { process::exit(8) }
        payload.release()
        tcp::socket_close(client)
        pilot received = ByteBuffer::with_capacity(4)
        repeat until received.length() >= 4 {
            if tcp::socket_receive(peer, received, 4 - received.length()) <= 0 { process::exit(9) }
        }
        if received.to_word() != "ping" { process::exit(10) }
        received.release()
        if tcp::socket_status(peer) != 0 { process::exit(11) }
        tcp::socket_close(peer)
        tcp::socket_close(listener)
    }
    say "socket-ok"
}
'''

NEGATIVE = {
    "builder_finish_twice": 'pilot b = word_builder::new()\nword_builder::finish(b)\nword_builder::finish(b)',
    "builder_after_discard": 'pilot b = word_builder::new()\nword_builder::discard(b)\nword_builder::length(b)',
    "builder_typed_finish": 'pilot b: int = word_builder::new()\nword_builder::finish(b)\nword_builder::discard(b)',
    "socket_after_close": 'pilot s = tcp::socket_listen("127.0.0.1", 0, 1)\ntcp::socket_close(s)\ntcp::socket_status(s)',
    "socket_typed_double_close": 'pilot s: int = tcp::socket_listen("127.0.0.1", 0, 1)\ntcp::socket_close(s)\ntcp::socket_close(s)',
    "buffer_after_release": 'pilot b = ByteBuffer::new()\nb.release()\nb.length()',
    "released_send_payload": 'pilot s: int = 0\npilot b = ByteBuffer::new()\nb.release()\ntcp::socket_send_all(s, b, 0, 0)',
    "array_double_release": 'pilot a: int = array_new()\narray_release(a)\narray_release(a)',
    "unknown_user_call_moves": 'pilot b = word_builder::new()\nconsume_handle(b)\nword_builder::length(b)',
    "nested_finish_consumes": 'pilot outer = word_builder::new()\npilot inner = word_builder::new()\nword_builder::append(outer, word_builder::finish(inner))\nword_builder::discard(inner)',
    "typed_legacy_close": 'pilot socket: int = 0\ntcp::close(socket)\ntcp::close(socket)',
    "typed_window_destroy": 'pilot window: int = 0\nui::destroy_window(window)\nui::get_width(window)',
}


def invoke(command: list[str], repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=repo, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=60)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cli", type=Path)
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--clang", default=shutil.which("clang"))
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    runtime = (args.runtime_root or repo / "freakc/runtime").resolve()
    cli = str(args.cli.resolve(strict=True))
    assert args.clang, "Clang is required"
    with tempfile.TemporaryDirectory(prefix="freak-strict-handles-") as directory:
        root = Path(directory)
        for name, program, expected in (("builder", BUILDER, "builder-ok"), ("socket", SOCKET, "socket-ok")):
            source = root / f"{name}.fk"
            source.write_text(program, encoding="utf-8")
            checked = invoke([cli, "check", str(source), "--strict-borrow"], repo)
            assert checked.returncode == 0, (name, checked.stdout, checked.stderr)
            for backend in ("c", "llvm"):
                emitted = invoke([cli, "transpile", str(source), f"--{backend}", "--strict-borrow"], repo)
                assert emitted.returncode == 0, (name, backend, emitted.stdout, emitted.stderr)
                generated = Path(str(source) + (".c" if backend == "c" else ".ll"))
                binary = root / f"{name}_{backend}{'.exe' if sys.platform == 'win32' else ''}"
                byte_foundation.compile_generated(args.clang, repo, runtime, generated, binary, backend)
                executed = invoke([str(binary)], root)
                assert executed.returncode == 0, (name, backend, executed.stdout, executed.stderr)
                assert executed.stdout.strip() == expected, (name, backend, executed.stdout)
                assert "ownership audit found" not in executed.stderr, executed.stderr
                counters = foundation.parse_runtime_stats(executed.stderr)["counters"]
                if name == "builder":
                    assert counters["word_builder_creations"] == 16, counters
                    assert counters["word_builder_finishes"] == counters["word_builder_discards"] == 8, counters
                else:
                    assert counters["byte_buffer_creations"] == counters["byte_buffer_releases"] == 8, counters
                print(f"PASS strict {name} {backend}", flush=True)
        for name, body in NEGATIVE.items():
            source = root / f"{name}.fk"
            source.write_text("task consume_handle(handle: int) -> void {}\ntask main() {\n" + body + "\n}\n", encoding="utf-8")
            for backend in ("c", "llvm"):
                checked = invoke([cli, "transpile", str(source), f"--{backend}", "--strict-borrow"], repo)
                assert checked.returncode != 0 and "Shirogane. You gave this away" in checked.stdout + checked.stderr, (name, backend, checked.stdout, checked.stderr)
        for name, should_pass in (("borrow_word_move", False), ("borrow_move_basic", False),
                                  ("borrow_immut_reassign", False), ("borrow_mut_reassign", True),
                                  ("borrow_copy_primitive", True)):
            checked = invoke([cli, "check", str(repo / "tests" / (name + ".fk")), "--strict-borrow"], repo)
            assert (checked.returncode == 0) == should_pass, (name, checked.stdout, checked.stderr)
            if not should_pass:
                assert "borrowck" in checked.stdout + checked.stderr, (name, checked.stdout, checked.stderr)
    print("PASS strict handle borrowing, consuming calls, and existing ownership corpus")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
