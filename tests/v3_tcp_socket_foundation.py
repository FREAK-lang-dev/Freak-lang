#!/usr/bin/env python3
"""Prove the managed V3 TCP socket floor on loopback only."""

from __future__ import annotations

import argparse
import errno
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from types import SimpleNamespace

import v3_byte_buffer_foundation as byte_foundation
import v3_word_foundation as foundation


SERVER_PROGRAM = r'''task main() {
    pilot expected = word_to_int(process::arg(1))
    pilot connection_limit = word_to_int(process::arg(2))
    pilot listener = tcp::socket_listen("127.0.0.1", 0, 8)
    say "READY " + word_from_int(tcp::socket_local_port(listener))
    pilot connection = 0
    repeat until connection >= connection_limit {
        pilot client = tcp::socket_accept(listener)
        pilot received: ByteBuffer = ByteBuffer::new()
        pilot finished = false
        repeat until received.length() >= expected or finished {
            pilot count = tcp::socket_receive(client, received, 65536)
            if count == 0 {
                if tcp::socket_eof(client) or tcp::socket_status(client) != 0 {
                    finished = true
                }
            }
        }
        say received.length()
        if received.length() > 0 {
            received.seek(0)
            say received.read_byte()
            received.seek(0)
        }
        say tcp::socket_send_all(client, received, 0, received.length())
        received.release()
        tcp::socket_close(client)
        connection += 1
    }
    tcp::socket_close(listener)
}
'''


CLIENT_PROGRAM = r'''task main() {
    pilot port = word_to_int(process::arg(1))
    pilot client = tcp::socket_connect("127.0.0.1", port)
    pilot payload: ByteBuffer = ByteBuffer::with_capacity(1048576)
    payload.write_byte(0)
    payload.write_byte(255)
    payload.write_word("x".repeated(1048574))
    say tcp::socket_send(client, payload, 0, 0)
    say tcp::socket_send(client, payload, 0, 1)
    say tcp::socket_send_all(client, payload, 1, payload.length() - 1)
    pilot reply: ByteBuffer = ByteBuffer::new()
    repeat until reply.length() >= 4 or tcp::socket_eof(client) {
        tcp::socket_receive(client, reply, 4)
    }
    reply.seek(0)
    say reply.read_byte()
    say reply.read_byte()
    say reply.read_byte()
    say reply.read_byte()
    say tcp::socket_receive(client, reply, 1)
    say tcp::socket_eof(client)
    say tcp::socket_status(client)
    reply.release()
    payload.release()
    tcp::socket_close(client)
}
'''


STATUS_PROGRAM = r'''task main() {
    pilot invalid = tcp::socket_connect("", 80)
    say tcp::socket_status(invalid)
    pilot failed_accept = tcp::socket_accept(invalid)
    say tcp::socket_status(failed_accept)
    tcp::socket_close(failed_accept)
    tcp::socket_close(invalid)

    pilot listener = tcp::socket_listen("127.0.0.1", 0, 1)
    say tcp::socket_status(listener)
    say tcp::socket_local_port(listener) > 0
    pilot data: ByteBuffer = ByteBuffer::new()
    say tcp::socket_send(listener, data, 0, 0)
    say tcp::socket_status(listener)
    data.release()
    tcp::socket_close(listener)

}
'''


CONNECTED_STATUS_PROGRAM = r'''task main() {
    pilot port = word_to_int(process::arg(1))
    pilot client = tcp::socket_connect("127.0.0.1", port)
    pilot destination: ByteBuffer = ByteBuffer::new()
    say tcp::socket_receive(client, destination, 0)
    say destination.length()
    say tcp::socket_status(client)
    destination.release()
    tcp::socket_close(client)
}
'''


TIMEOUT_PROGRAM = r'''task main() {
    pilot port = word_to_int(process::arg(1))
    pilot client = tcp::socket_connect("127.0.0.1", port)
    tcp::socket_set_timeout(client, 100, 100)
    pilot destination: ByteBuffer = ByteBuffer::new()
    say tcp::socket_receive(client, destination, 8)
    say tcp::socket_status(client)
    destination.release()
    tcp::socket_close(client)
}
'''


FAILURE_STATUS_PROGRAM = r'''task main() {
    pilot refused_port = word_to_int(process::arg(1))
    pilot occupied_port = word_to_int(process::arg(2))
    pilot unresolved = tcp::socket_connect("freak-network-test.invalid", 80)
    say tcp::socket_status(unresolved)
    tcp::socket_close(unresolved)
    pilot refused = tcp::socket_connect("127.0.0.1", refused_port)
    say tcp::socket_status(refused)
    tcp::socket_close(refused)
    pilot blocked = tcp::socket_listen("127.0.0.1", occupied_port, 1)
    say tcp::socket_status(blocked)
    tcp::socket_close(blocked)
    pilot bad_backlog = tcp::socket_listen("127.0.0.1", 0, 0)
    say tcp::socket_status(bad_backlog)
    tcp::socket_close(bad_backlog)
}
'''


STALE_PROGRAM = r'''task main() {
    pilot socket_handle = tcp::socket_connect("", 80)
    tcp::socket_close(socket_handle)
    say tcp::socket_status(socket_handle)
}
'''


DOUBLE_CLOSE_PROGRAM = r'''task main() {
    pilot socket_handle = tcp::socket_connect("", 80)
    tcp::socket_close(socket_handle)
    tcp::socket_close(socket_handle)
}
'''


GENERATION_PROGRAM = r'''task main() {
    pilot old_handle = tcp::socket_connect("", 80)
    tcp::socket_close(old_handle)
    pilot fresh_handle = tcp::socket_connect("", 80)
    say tcp::socket_status(old_handle)
    tcp::socket_close(fresh_handle)
}
'''


LEAK_PROGRAM = r'''task main() {
    pilot leaked = tcp::socket_listen("127.0.0.1", 0, 1)
    say tcp::socket_status(leaked)
}
'''


BOOTSTRAP_PROGRAM = r'''task main() {
    pilot invalid = tcp::socket_connect("", 80)
    if tcp::socket_status(invalid) != 1 { process::exit(2) }
    tcp::socket_close(invalid)
    pilot listener = tcp::socket_listen("127.0.0.1", 0, 1)
    if tcp::socket_status(listener) != 0 { process::exit(3) }
    if tcp::socket_local_port(listener) <= 0 { process::exit(4) }
    tcp::socket_set_timeout(listener, 0, 0)
    if tcp::socket_status(listener) != 0 { process::exit(5) }
    tcp::socket_close(listener)
    say "bootstrap-tcp-ok"
}
'''


NEGATIVE_PROGRAM = r'''task main() {
    pilot buffer: ByteBuffer = ByteBuffer::new()
    tcp::socket_connect(1, 80)
    tcp::socket_send(1, 2, 0, 0)
    tcp::socket_receive(1, buffer)
    tcp::socket_nope(1)
    buffer.release()
}
'''


RUNTIME_FORGERY_PROBE = r'''#include "freak_runtime.h"
#include <stdint.h>
int main(void) {
    freak_byte_buffer_handle buffer = freak_byte_buffer_new();
    (void)freak_tcp_socket_status(buffer);
    return 0;
}
'''


RUNTIME_HOST_SIZE_PROBE = r'''#include "freak_runtime.h"
#include <stdint.h>

static freak_word hostile_host(void) {
    freak_word host;
    host.data = (const char*)(uintptr_t)1;
    host.length = SIZE_MAX;
    host.char_count = 0;
    host.heap = false;
    return host;
}

int main(void) {
    freak_tcp_socket_handle connected = freak_tcp_socket_connect(hostile_host(), 80);
    if (freak_tcp_socket_status(connected) != FREAK_TCP_SOCKET_STATUS_INVALID_ARGUMENT) {
        return 2;
    }
    freak_tcp_socket_close(connected);

    freak_tcp_socket_handle listener = freak_tcp_socket_listen(hostile_host(), 0, 1);
    if (freak_tcp_socket_status(listener) != FREAK_TCP_SOCKET_STATUS_INVALID_ARGUMENT) {
        return 3;
    }
    freak_tcp_socket_close(listener);

    const char embedded[] = "127.0.0.1\0.invalid";
    freak_word nul_host = {embedded, sizeof(embedded) - 1, 0, false};
    connected = freak_tcp_socket_connect(nul_host, 80);
    if (freak_tcp_socket_status(connected) != FREAK_TCP_SOCKET_STATUS_INVALID_ARGUMENT) {
        return 4;
    }
    freak_tcp_socket_close(connected);
    listener = freak_tcp_socket_listen(nul_host, 0, 1);
    if (freak_tcp_socket_status(listener) != FREAK_TCP_SOCKET_STATUS_INVALID_ARGUMENT) {
        return 5;
    }
    freak_tcp_socket_close(listener);
    return 0;
}
'''


def run(
    command: list[str],
    cwd: Path,
    *,
    timeout: int = 300,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def compile_source(
    freak: Path,
    compiler: str,
    repo: Path,
    runtime: Path,
    root: Path,
    name: str,
    program: str,
    backend: str,
) -> tuple[Path, str]:
    source = root / f"{name}_{backend}.fk"
    source.write_text(program, encoding="utf-8")
    generated, generated_text = foundation.transpile(
        freak=freak, repo=repo, source=source, backend=backend
    )
    binary = root / f"{name}_{backend}{'.exe' if sys.platform == 'win32' else ''}"
    byte_foundation.compile_generated(
        compiler, repo, runtime, generated, binary, backend
    )
    return binary, generated_text


def loopback_listener() -> tuple[socket.socket, int]:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    return listener, listener.getsockname()[1]


def bounded_readline(
    process: subprocess.Popen[str], *, timeout: float = 10.0
) -> str:
    assert process.stdout is not None
    result: list[str] = []
    failure: list[BaseException] = []

    def read() -> None:
        try:
            result.append(process.stdout.readline())
        except BaseException as error:
            # Transport every worker failure to the caller, including cancellation;
            # narrowing to Exception would strand SystemExit/KeyboardInterrupt here.
            failure.append(error)

    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    reader.join(timeout)
    assert not reader.is_alive(), "server readiness line exceeded its deadline"
    if failure:
        raise failure[0]
    assert result, "server readiness reader returned no result"
    return result[0]


def exercise_server(binary: Path, root: Path, payloads: list[bytes]) -> None:
    process = subprocess.Popen(
        [str(binary), str(len(payloads[0])), str(len(payloads))],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        ready = bounded_readline(process).strip()
        assert ready.startswith("READY "), ready
        port = int(ready.split()[1])
        echoed: list[bytes] = []
        for payload in payloads:
            with socket.create_connection(("127.0.0.1", port), timeout=5) as client:
                midpoint = max(1, len(payload) // 3)
                client.sendall(payload[:midpoint])
                client.sendall(payload[midpoint:])
                received = bytearray()
                while len(received) < len(payload):
                    chunk = client.recv(min(65536, len(payload) - len(received)))
                    if not chunk:
                        break
                    received.extend(chunk)
                echoed.append(bytes(received))
        stdout_tail, stderr = process.communicate(timeout=20)
        assert process.returncode == 0, stdout_tail + stderr
        assert echoed == payloads
        lines = stdout_tail.strip().splitlines()
        expected_lines: list[str] = []
        for payload in payloads:
            expected_lines.extend([str(len(payload)), str(payload[0]), str(len(payload))])
        assert lines == expected_lines, (lines, expected_lines)
        assert "ownership audit found" not in stderr, stderr
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)


def exercise_managed_listener_exclusive(binary: Path, root: Path) -> None:
    """A managed listener must prevent a raw SO_REUSEADDR bind to its port."""
    process = subprocess.Popen(
        [str(binary), "1", "1"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        ready = bounded_readline(process).strip()
        assert ready.startswith("READY "), ready
        port = int(ready.split()[1])

        challenger = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            challenger.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            rebound = False
            try:
                challenger.bind(("127.0.0.1", port))
                rebound = True
            except OSError as error:
                # Exclusive Windows listeners may reject reuse with WSAEACCES;
                # POSIX reports EADDRINUSE. Other socket errors are not proof.
                expected_errors = {errno.EADDRINUSE}
                if sys.platform == "win32":
                    expected_errors.update((errno.EACCES, errno.WSAEADDRINUSE, errno.WSAEACCES))
                assert error.errno in expected_errors, error
            assert not rebound, "managed listener allowed a second bind to its live port"
        finally:
            challenger.close()

        with socket.create_connection(("127.0.0.1", port), timeout=5) as client:
            client.sendall(b"Z")
            assert client.recv(1) == b"Z"
        stdout_tail, stderr = process.communicate(timeout=20)
        assert process.returncode == 0, stdout_tail + stderr
        assert stdout_tail.strip().splitlines() == ["1", "90", "1"], stdout_tail
        assert "ownership audit found" not in stderr, stderr
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)


def exercise_client(binary: Path, root: Path) -> None:
    listener, port = loopback_listener()
    received = bytearray()

    def serve() -> None:
        with listener:
            connection, _ = listener.accept()
            with connection:
                while len(received) < 1048576:
                    chunk = connection.recv(65536)
                    if not chunk:
                        break
                    received.extend(chunk)
                connection.sendall(bytes((0, 255, 79, 75)))

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    executed = run([str(binary), str(port)], root, timeout=60)
    thread.join(timeout=5)
    assert not thread.is_alive(), "loopback client helper did not exit"
    assert executed.returncode == 0, executed.stdout + executed.stderr
    assert executed.stdout.strip().splitlines() == [
        "0", "1", "1048575", "0", "255", "79", "75", "0", "true", "0"
    ], executed.stdout
    assert len(received) == 1048576
    assert received[:2] == bytes((0, 255))
    assert received[2:] == b"x" * 1048574
    assert "ownership audit found" not in executed.stderr, executed.stderr


def exercise_connected_status(binary: Path, root: Path, *, timeout_case: bool) -> None:
    listener, port = loopback_listener()

    def serve() -> None:
        with listener:
            connection, _ = listener.accept()
            with connection:
                if timeout_case:
                    threading.Event().wait(0.35)

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    executed = run([str(binary), str(port)], root, timeout=10)
    thread.join(timeout=2)
    assert executed.returncode == 0, executed.stdout + executed.stderr
    expected = ["0", "10"] if timeout_case else ["0", "0", "1"]
    assert executed.stdout.strip().splitlines() == expected, executed.stdout


def exercise_failure_statuses(binary: Path, root: Path) -> None:
    unused = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    unused.bind(("127.0.0.1", 0))
    refused_port = unused.getsockname()[1]
    unused.close()

    occupied = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Raw reuse listener first, then managed listener: the managed endpoint
    # must refuse to hijack a live port even if the incumbent allows reuse.
    occupied.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    occupied.bind(("127.0.0.1", 0))
    occupied.listen(1)
    occupied_port = occupied.getsockname()[1]
    try:
        executed = run(
            [str(binary), str(refused_port), str(occupied_port)], root, timeout=15
        )
    finally:
        occupied.close()
    assert executed.returncode == 0, executed.stdout + executed.stderr
    assert executed.stdout.strip().splitlines() == ["2", "4", "5", "1"], (
        executed.stdout,
        executed.stderr,
    )


def check_readiness_reader_failures() -> None:
    """Reader exceptions must reach the caller unchanged, including cancellation."""
    for expected in (OSError("read failed"), SystemExit(17), KeyboardInterrupt()):
        class FailedStream:
            def readline(self) -> str:
                raise expected

        try:
            bounded_readline(SimpleNamespace(stdout=FailedStream()))
        except type(expected) as actual:
            assert actual is expected, (actual, expected)
        else:
            raise AssertionError("readiness reader swallowed its failure")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("freak", nargs="?", type=Path,
                        help="existing exact-source CLI; omit to reconstruct")
    parser.add_argument("--runtime-root", type=Path,
                        help="runtime payload to compile; defaults to repository")
    args = parser.parse_args()
    check_readiness_reader_failures()
    repo = Path(__file__).resolve().parents[1]
    runtime = (args.runtime_root or repo / "freakc" / "runtime").resolve()
    assert (runtime / "freak_runtime.c").is_file(), runtime
    assert (runtime / "freak_llvm_runtime.c").is_file(), runtime
    compiler = os.environ.get("FREAK_CLANG") or shutil.which("clang")
    assert compiler, "Clang is required for the C and LLVM networking matrix"
    compiler_identity = run([compiler, "--version"], repo, timeout=30)
    assert compiler_identity.returncode == 0, compiler_identity.stderr
    assert "clang" in (compiler_identity.stdout + compiler_identity.stderr).lower(), (
        "FREAK_CLANG must name a Clang-compatible driver"
    )

    with tempfile.TemporaryDirectory(prefix="freak-v3-tcp-socket-") as temporary:
        root = Path(temporary)
        freak = args.freak.resolve() if args.freak else foundation.build_fresh_cli(
            clang=compiler, repo=repo, root=root, runtime_root=runtime
        )
        assert freak.is_file(), freak

        for backend in ("c", "llvm"):
            binaries: dict[str, Path] = {}
            for name, program in (
                ("server", SERVER_PROGRAM),
                ("client", CLIENT_PROGRAM),
                ("status", STATUS_PROGRAM),
                ("connected_status", CONNECTED_STATUS_PROGRAM),
                ("timeout", TIMEOUT_PROGRAM),
                ("failure_status", FAILURE_STATUS_PROGRAM),
                ("stale", STALE_PROGRAM),
                ("double_close", DOUBLE_CLOSE_PROGRAM),
                ("generation", GENERATION_PROGRAM),
                ("leak", LEAK_PROGRAM),
            ):
                binary, generated = compile_source(
                    freak, compiler, repo, runtime, root, name, program, backend
                )
                binaries[name] = binary
                prefix = "freak_tcp_socket_" if backend == "c" else "@freak_llvm_tcp_socket_"
                assert prefix in generated, (backend, name)

            payload = bytes((index * 37) & 255 for index in range(32768))
            exercise_server(binaries["server"], root, [payload, payload, payload])
            exercise_managed_listener_exclusive(binaries["server"], root)
            exercise_client(binaries["client"], root)

            status = run([str(binaries["status"])], root)
            assert status.returncode == 0, status.stdout + status.stderr
            assert status.stdout.strip().splitlines() == [
                "1", "1", "0", "true", "0", "9"
            ]

            exercise_connected_status(
                binaries["connected_status"], root, timeout_case=False
            )
            exercise_connected_status(binaries["timeout"], root, timeout_case=True)
            exercise_failure_statuses(binaries["failure_status"], root)

            for name in ("stale", "double_close", "generation"):
                failed = run([str(binaries[name])], root)
                assert failed.returncode != 0, (backend, name)
                assert "invalid or stale TCP socket handle" in failed.stderr, failed.stderr

            leaked = run([str(binaries["leak"])], root)
            assert leaked.stdout.strip() == "0", (backend, leaked.stdout, leaked.stderr)
            assert leaked.returncode == 89, (backend, leaked.returncode, leaked.stderr)
            leak_diagnostics = [
                line
                for line in leaked.stderr.splitlines()
                if line.startswith("FREAK: TCP socket ownership audit")
            ]
            assert leak_diagnostics == [
                "FREAK: TCP socket ownership audit found 1 live socket(s)"
            ], (backend, leaked.stderr)

        negative = root / "tcp_socket_negative.fk"
        negative.write_text(NEGATIVE_PROGRAM, encoding="utf-8")
        rejected = run([str(freak), "check", str(negative)], repo)
        output = rejected.stdout + rejected.stderr
        assert rejected.returncode != 0, output
        for diagnostic in (
            "argument 1 expects word, got int",
            "argument 2 expects ByteBuffer, got int",
            "expects 3 argument(s), got 2",
            "unknown callable 'tcp::socket_nope'",
        ):
            assert diagnostic in output, (diagnostic, output)

        # LLVM words carry a NUL-terminated pointer, not a pointer/length pair.
        # Bytes after its terminator are not part of that ABI value. Prove the
        # source path rejects an embedded-NUL host before either backend emits
        # code; the raw C length-bearing boundary is covered separately below.
        for operation in ("connect", "listen"):
            nul_source = root / f"nul_host_{operation}.fk"
            arguments = "80" if operation == "connect" else "0, 1"
            nul_source.write_text(
                'task main() { pilot endpoint = tcp::socket_' + operation
                + '("127.0.0.1\\x00.invalid", ' + arguments + ') }\n',
                encoding="utf-8",
            )
            for flag, suffix in (("--c", ".c"), ("--llvm", ".ll")):
                rejected_nul = run([str(freak), "transpile", str(nul_source), flag], repo)
                output = rejected_nul.stdout + rejected_nul.stderr
                assert rejected_nul.returncode != 0, output
                assert "embedded NUL escape is not supported" in output, output
                assert not Path(str(nul_source) + suffix).exists()

        bootstrap = root / "bootstrap_tcp_socket.fk"
        bootstrap.write_text(BOOTSTRAP_PROGRAM, encoding="utf-8")
        bootstrap_binary = root / f"bootstrap_tcp_socket{'.exe' if sys.platform == 'win32' else ''}"
        # Exercise bootstrap emission against the selected installed runtime
        # too: its build command otherwise hardcodes the repository payload.
        sys.path.insert(0, str(repo))
        from freakc.__main__ import transpile_checked as bootstrap_transpile
        bootstrap_c, diagnostics, _, has_errors = bootstrap_transpile(
            BOOTSTRAP_PROGRAM, bootstrap
        )
        assert not has_errors and bootstrap_c is not None, diagnostics
        bootstrap_generated = bootstrap.with_suffix(".c")
        bootstrap_generated.write_text(bootstrap_c, encoding="utf-8")
        byte_foundation.compile_generated(
            compiler, repo, runtime, bootstrap_generated, bootstrap_binary, "c"
        )
        bootstrap_run = run([str(bootstrap_binary)], root)
        assert bootstrap_run.returncode == 0, bootstrap_run.stdout + bootstrap_run.stderr
        assert bootstrap_run.stdout.strip() == "bootstrap-tcp-ok"

        forgery_source = root / "tcp_socket_forgery.c"
        forgery_source.write_text(RUNTIME_FORGERY_PROBE, encoding="utf-8")
        forgery_binary = root / f"tcp_socket_forgery{'.exe' if sys.platform == 'win32' else ''}"
        command = [
            compiler,
            "-O1",
            "-o",
            str(forgery_binary),
            str(forgery_source),
            str(runtime / "freak_runtime.c"),
            "-I",
            str(runtime),
        ]
        if sys.platform == "win32":
            command.append("-lws2_32")
        else:
            command.append("-lm")
        compiled = run(command, repo)
        assert compiled.returncode == 0, compiled.stdout + compiled.stderr
        forged = run([str(forgery_binary)], root)
        assert forged.returncode != 0
        assert "invalid or stale TCP socket handle" in forged.stderr, forged.stderr

        host_size_source = root / "tcp_socket_host_size.c"
        host_size_source.write_text(RUNTIME_HOST_SIZE_PROBE, encoding="utf-8")
        host_size_binary = root / f"tcp_socket_host_size{'.exe' if sys.platform == 'win32' else ''}"
        host_size_command = [
            compiler,
            "-O1",
            "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1",
            "-o",
            str(host_size_binary),
            str(host_size_source),
            str(runtime / "freak_runtime.c"),
            "-I",
            str(runtime),
        ]
        if sys.platform == "win32":
            host_size_command.append("-lws2_32")
        else:
            host_size_command.append("-lm")
        host_size_compiled = run(host_size_command, repo)
        assert host_size_compiled.returncode == 0, (
            host_size_compiled.stdout + host_size_compiled.stderr
        )
        host_size = run([str(host_size_binary)], root)
        assert host_size.returncode == 0, host_size.stdout + host_size.stderr
        assert "ownership audit found" not in host_size.stderr, host_size.stderr

    print("v3 TCP socket foundation tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
