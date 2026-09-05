#!/usr/bin/env python3
"""Length-preserving Word producers/consumers, including dynamic embedded NUL.

Optional exact-source CLI/runtime payload follows v3_word_foundation.py. Every
native child is bounded; network peers are exclusively owned loopback sockets.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import threading

import v3_word_foundation as foundation


CORE = '''task identity(value: word) -> word { give back value }
task main() {
    pilot zero = char_to_word(0)
    pilot value = "a" + zero + "B"
    say zero.length()
    say value.length()
    say value.char_at(1).length()
    say value.char_at(1) == zero
    say value == "a"
    say identity(value) == value
    say value.substring(1, 2) == zero + "B"
    say value.repeated(3).length()
    say value.contains(zero + "B")
    say value.starts_with("a" + zero)
    say value.ends_with(zero + "B")
    say value.to_upper() == "A" + zero + "B"
    say value.to_lower() == "a" + zero + "b"
    say (" " + value + " ").trim() == value
    say value.replace(zero, "xy") == "axyB"
    say value.replace("a", zero).length()
    say value.replace("", "ignored") == value
    pilot snapshot = value + "|tail\\nend"
    say snapshot.snapshot_escape().snapshot_unescape() == snapshot
    say snapshot.snapshot_line_count()
    say snapshot.snapshot_line(0).snapshot_field_count()
    say snapshot.snapshot_line(0).snapshot_field_raw(0) == value
    say value.checksum() != "a".checksum()
    pilot items = array_new()
    array_push(items, value)
    array_push(items, zero)
    pilot joined = word_join(items)
    say joined == value + zero
    pilot builder = word_builder::new()
    word_builder::append(builder, value)
    word_builder::append(builder, zero)
    say word_builder::length(builder)
    say word_builder::finish(builder) == joined
    pilot bytes = ByteBuffer::new()
    bytes.write_word(value)
    say bytes.length()
    bytes.seek(1)
    say bytes.read_byte()
    say bytes.to_word().length()
    say bytes.status()
    bytes.release()
    pilot mut growing: word = value
    repeat 100 times { growing = growing + zero + "x" }
    say growing.length()
    say growing.substring(0, 3) == value
    say growing.ends_with(zero + "x")
    say value
}
'''
CORE_LINES = ["1", "3", "1", "true", "false", "true", "true", "9",
              *(["true"] * 7), "3", "true", "true", "2", "2", "true",
              "true", "true", "4", "true", "3", "0", "0", "3", "203",
              "true", "true", "a\0B"]

RAW = r'''#include "freak_runtime.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>
extern int64_t freak_llvm_char_to_word(int64_t);
extern int64_t freak_llvm_word_char_at(int64_t,int64_t);
extern int64_t freak_llvm_word_clone(int64_t);
extern void freak_llvm_print_str(int64_t);
extern void freak_llvm_word_release_replaced(int64_t,int64_t);
int main(int argc, char **argv) {
    if (argc > 1 && !strcmp(argv[1], "null_length"))
        freak_llvm_word_adopt_sized(0, 1);
    if (argc > 1 && !strcmp(argv[1], "overflow"))
        freak_llvm_word_adopt_sized(1, SIZE_MAX);
    char *data = malloc(4); memcpy(data, "a\0b", 4);
    int64_t value = freak_llvm_word_adopt_sized((int64_t)data, 3);
    assert(freak_llvm_word_adopt(value) == value);
    assert(freak_llvm_word_size(value) == 3);
    assert(freak_llvm_word_view(value).length == 3);
    freak_llvm_print_str(value);
    int64_t zero = freak_llvm_word_char_at(value, 1);
    assert(freak_llvm_word_size(zero) == 1);
    assert(freak_llvm_word_size((int64_t)"") == 0);
    assert(freak_llvm_word_size((int64_t)"a\0b") == 1);
    int64_t copied = freak_llvm_word_clone(zero);
    assert(freak_llvm_word_size(copied) == 1);
    freak_llvm_word_release_replaced(copied, 0);
    if (argc > 1 && !strcmp(argv[1], "conflict"))
        freak_llvm_word_adopt_sized(value, 1);
    if (argc > 1 && !strcmp(argv[1], "leak")) return 0;
    freak_llvm_word_release_replaced(value, 0);
    /* Borrowed static char_at remains valid without registering an owner. */
    assert(freak_llvm_word_size(zero) == 1);
    return 0;
}
'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("freak", nargs="?", type=Path)
    parser.add_argument("--runtime-root", type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    runtime = (args.runtime_root or repo / "freakc/runtime").resolve()
    clang = os.environ.get("FREAK_CLANG") or shutil.which("clang")
    assert clang, "clang required"
    suffix = ".exe" if sys.platform == "win32" else ""
    with tempfile.TemporaryDirectory(prefix="freak-word-length-") as tmp:
        root = Path(tmp)
        freak = args.freak.resolve() if args.freak else foundation.build_fresh_cli(
            clang=clang, repo=repo, root=root, runtime_root=runtime)
        env = foundation.sanitizer_env()
        env.setdefault("FREAK_HOME", str(repo))
        std_runtime = (repo / "std/runtime.fk" if args.runtime_root is None else
                       runtime.parent / "std/runtime.fk")
        if args.runtime_root is not None and not std_runtime.is_file():
            std_runtime = runtime.parent.parent / "std/runtime.fk"
        assert std_runtime.is_file(), std_runtime
        # CLI build marks only selected std/runtime.fk as trusted internal
        # source. Preserve that path provenance instead of concatenating it
        # into a user source (which must be rejected as builtin spoofing).
        payload = root / "payload"
        shutil.copytree(runtime, payload / "runtime")
        shutil.copytree(std_runtime.parent, payload / "std")
        env["FREAK_HOME"] = str(payload)

        def build(name: str, source: str, backend: str, *, audit: bool = True) -> Path:
            path = root / f"{name}_{backend}.fk"
            path.write_text(source, encoding="utf-8")
            mode = "build" if backend == "llvm" and "fs::" in source else "transpile"
            proc = subprocess.run([str(freak), mode, str(path), "--" + backend],
                                  cwd=root, env=env, capture_output=True, timeout=90)
            assert proc.returncode == 0, proc.stdout + proc.stderr
            generated = Path(str(path) + (".c" if backend == "c" else ".ll"))
            binary = root / (name + "_" + backend + suffix)
            command = [clang, "-O1", "-g", "-DFREAK_WORD_CONCAT_FORCE_MOVE=1",
                       "-DFREAK_WORD_FOUNDATION_AUDIT=1", "-I", str(runtime),
                       str(generated), str(runtime / "freak_runtime.c")]
            if audit:
                command += ["-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1",
                            "-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1"]
            if backend == "llvm": command.append(str(runtime / "freak_llvm_runtime.c"))
            command += ["-lws2_32"] if sys.platform == "win32" else ["-lm", "-fsanitize=address"]
            proc = subprocess.run(command + ["-o", str(binary)], capture_output=True, timeout=90)
            assert proc.returncode == 0, proc.stdout + proc.stderr
            return binary

        def run(binary: Path, *argv: str, stdin: bytes = b"", expected: bytes | None = None,
                code: int = 0) -> subprocess.CompletedProcess:
            proc = subprocess.run([str(binary), *argv], input=stdin, capture_output=True,
                                  cwd=root, env=env, timeout=20)
            assert proc.returncode == code, (binary, proc.returncode, proc.stdout, proc.stderr)
            if expected is not None:
                assert proc.stdout.replace(b"\r\n", b"\n") == expected, (binary, proc.stdout, expected)
            return proc

        fixture = root / "nul.bin"
        fixture.write_bytes(b"a\0B")
        for backend in ("c", "llvm"):
            print(f"[{backend}] transforms, ownership, forced-moving append", flush=True)
            core = run(build("core", CORE, backend), expected=("\n".join(CORE_LINES) + "\n").encode())
            stats = [json.loads(line.removeprefix("FREAK_RUNTIME_STATS "))["counters"]
                     for line in core.stderr.decode().splitlines() if line.startswith("FREAK_RUNTIME_STATS ")]
            assert len(stats) == 1, core.stderr
            for key, count in {"word_repeat_calls": 1, "word_repeat_allocations": 1,
                               "word_repeat_copied_bytes": 9, "word_builder_copied_bytes": 4,
                               "word_builder_finishes": 1, "byte_buffer_copied_bytes": 3}.items():
                assert stats[0][key] == count, (key, stats)
            # Main's snapshot-array ownership must compose with binary Word
            # lengths, including cleanup of a temporary source after splitting.
            snapshots = '''task main() {
                pilot zero = char_to_word(0)
                pilot lines = ("a" + zero + "b\\n" + zero + "\\n").snapshot_lines()
                say array_len(lines)
                say array_get(lines, 0).length()
                say array_get(lines, 0) == "a" + zero + "b"
                say array_get(lines, 1) == zero
                say array_get(lines, 2).length()
                pilot joined = word_join(lines)
                say joined.length()
                say joined == "a" + zero + "b" + zero
                pilot empty = "".snapshot_lines()
                say array_len(empty)
                array_release(empty)
            }'''
            run(build("binary_snapshots", snapshots, backend),
                expected=b"3\n3\ntrue\ntrue\n0\n4\ntrue\n0\n")
            producers = '''task main() {
                pilot value = fs::read(process::arg(1))
                say value.length()
                say value.char_at(1).length()
                fs::write(process::arg(2), value)
                fs::append(process::arg(2), value)
                pilot first = ask("")
                say first.length()
                pilot second = process::input()
                say second.length()
            }'''
            output = root / f"output_{backend}.bin"
            run(build("producers", producers, backend), str(fixture), str(output),
                stdin=b"x\0y\nz\0w\n", expected=b"3\n1\n3\n3\n")
            assert output.read_bytes() == b"a\0Ba\0B"
            # A native helper produces binary stdout without shell quoting of NUL.
            helper = root / ("capture_helper" + suffix)
            if not helper.exists():
                helper_source = root / "capture_helper.c"
                helper_source.write_text('#include <stdio.h>\nint main(void){fwrite("a\\0B",1,3,stdout);return 0;}')
                subprocess.run([clang, str(helper_source), "-o", str(helper)], check=True, timeout=60)
            capture = 'task main() { pilot value = process::exec_capture(process::arg(1)) say value.length() say value.char_at(1).length() }'
            run(build("capture", capture, backend), f'"{helper}"', expected=b"3\n1\n")
            print(f"[{backend}] source socket/env boundaries and legacy binary receive/send", flush=True)
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0)); listener.listen(); listener.settimeout(0.2)
                port = listener.getsockname()[1]
                boundary = '''task main() {
                    pilot host = "127.0.0.1" + char_to_word(0)
                    say host.length()
                    pilot connection = tcp::socket_connect(host, process::arg(1).to_int())
                    say tcp::socket_status(connection)
                    tcp::socket_close(connection)
                    pilot server = tcp::socket_listen(host, 0, 1)
                    say tcp::socket_status(server)
                    tcp::socket_close(server)
                }'''
                run(build("boundary", boundary, backend), str(port), expected=b"10\n1\n1\n")
                try:
                    connection, _ = listener.accept()
                except TimeoutError:
                    pass
                else:
                    connection.close(); raise AssertionError("NUL host connected")
            for name, operation in (
                ("env_name", 'say process::env("FREAK_LENGTH_TEST" + char_to_word(0))'),
                ("set_name", 'process::set_env("FREAK_LENGTH_TEST" + char_to_word(0), "x")'),
                ("set_value", 'process::set_env("FREAK_LENGTH_TEST", "x" + char_to_word(0))')):
                proc = run(build(name, "task main() { " + operation + " }", backend, audit=False), code=1)
                assert b"environment" in proc.stderr, proc.stderr
            for receive in ("recv", "recv_all"):
                errors: list[BaseException] = []
                with socket.socket() as listener:
                    listener.bind(("127.0.0.1", 0)); listener.listen(); listener.settimeout(15)
                    def peer() -> None:
                        try:
                            with listener.accept()[0] as connection:
                                connection.settimeout(10)
                                connection.sendall(b"a\0B")
                                connection.shutdown(socket.SHUT_WR)
                                reply = b""
                                while len(reply) < 3:
                                    part = connection.recv(3 - len(reply))
                                    if not part: break
                                    reply += part
                                assert reply == b"a\0B", reply
                        except BaseException as error: errors.append(error)
                    source = '''task main() {
                        pilot client = tcp::connect("127.0.0.1", process::arg(1).to_int())
                        pilot value = tcp::RECEIVE(client, 3)
                        say value.length()
                        say tcp::send(client, value)
                        tcp::close(client)
                    }'''.replace("RECEIVE", receive)
                    if receive == "recv":
                        # One-byte reads are deterministic despite legal TCP
                        # fragmentation and exercise a NUL-only producer.
                        source = source.replace("pilot value = tcp::recv(client, 3)",
                            "pilot first = tcp::recv(client, 1)\n"
                            "pilot zero = tcp::recv(client, 1)\n"
                            "pilot last = tcp::recv(client, 1)\n"
                            "pilot value = first + zero + last")
                    binary = build(receive, source, backend)
                    thread = threading.Thread(target=peer, daemon=True); thread.start()
                    try: run(binary, str(listener.getsockname()[1]), expected=b"3\n3\n")
                    finally: thread.join(timeout=16)
                    assert not thread.is_alive() and not errors, errors
        raw = root / "raw.c"; raw.write_text(RAW, encoding="utf-8")
        binary = root / ("raw" + suffix)
        command = [clang, "-O1", "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1",
                   "-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1", "-I", str(runtime), str(raw),
                   str(runtime / "freak_runtime.c"), str(runtime / "freak_llvm_runtime.c"),
                   "-o", str(binary)]
        command += ["-lws2_32"] if sys.platform == "win32" else ["-lm", "-fsanitize=address"]
        subprocess.run(command, check=True, capture_output=True, timeout=90)
        run(binary, expected=b"a\0b")
        for mode in ("null_length", "overflow"):
            assert b"invalid owned word length" in run(binary, mode, code=1).stderr
        assert b"unreleased word allocation" in run(binary, "leak", code=86).stderr
        # Do not enable the audit on the fatal-contract path: its atexit guard
        # deliberately overrides exit(1) while the test-owned word remains live.
        proc = run(binary, "conflict", code=86)
        assert b"conflicting owned word length" in proc.stderr
    print("PASS: embedded-NUL Word length parity (C/LLVM, producers, boundaries, ownership)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
