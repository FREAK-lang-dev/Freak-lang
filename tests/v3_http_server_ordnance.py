#!/usr/bin/env python3
"""Exercise the in-tree V3 HTTP server as a direct-compile acceptance app."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

import v3_byte_buffer_foundation as byte_foundation
import v3_word_foundation as foundation


SUCCESS_BODY = b'{"message":"FREAKING WORKS"}'


def run(
    command: list[str], cwd: Path, *, timeout: int = 300
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def request(port: int, fragments: list[bytes]) -> bytes:
    with socket.create_connection(("127.0.0.1", port), timeout=5) as client:
        for fragment in fragments:
            try:
                client.sendall(fragment)
            except (BrokenPipeError, ConnectionResetError):
                break
        response = bytearray()
        while True:
            try:
                chunk = client.recv(65536)
            except ConnectionResetError:
                break
            if not chunk:
                break
            response.extend(chunk)
        return bytes(response)


def exercise(binary: Path, root: Path) -> None:
    process = subprocess.Popen(
        [str(binary), "0", "3"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        assert process.stdout is not None
        ready = process.stdout.readline().strip()
        assert ready.startswith("ORDNANCE_READY "), ready
        port = int(ready.split()[1])
        assert 0 < port <= 65535

        success = request(
            port,
            [
                b"GET /hello HTTP/1.1\r\nHo",
                b"st: 127.0.0.1\r\nConnection: close\r\n",
                b"\r\n",
            ],
        )
        assert success.startswith(b"HTTP/1.1 200 OK\r\n"), success
        headers, body = success.split(b"\r\n\r\n", 1)
        assert b"Content-Type: application/json" in headers
        assert b"Content-Length: 28" in headers
        assert b"Connection: close" in headers
        assert body == SUCCESS_BODY, body

        malformed = request(port, [b"POST /hello HTTP/1.1\r\n\r\n"])
        assert malformed.startswith(b"HTTP/1.1 400 Bad Request\r\n"), malformed
        assert malformed.endswith(b"bad request"), malformed

        oversize = request(port, [b"X" * 65537, b"\r\n\r\n"])
        assert oversize.startswith(b"HTTP/1.1 400 Bad Request\r\n"), oversize

        stdout_tail, stderr = process.communicate(timeout=20)
        assert process.returncode == 0, stdout_tail + stderr
        assert stdout_tail == "", stdout_tail
        assert "ownership audit found" not in stderr, stderr
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    runtime = repo / "freakc" / "runtime"
    package = repo / "packages" / "http-server"
    source = package / "src" / "main.fk"
    compiler = (
        os.environ.get("FREAK_CLANG")
        or shutil.which("gcc")
        or shutil.which("clang")
        or shutil.which("cc")
    )
    assert compiler, "a C/LLVM compiler is required"
    assert source.is_file()
    manifest = (package / "hangar.toml").read_text(encoding="utf-8")
    assert 'name = "http-server"' in manifest
    assert 'version = "0.1.0"' in manifest
    assert "tcp::socket_listen" in source.read_text(encoding="utf-8")
    assert "65536" in source.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory(prefix="freak-v3-http-server-") as temporary:
        root = Path(temporary)
        freak = foundation.build_fresh_cli(
            clang=compiler, repo=repo, root=root, runtime_root=runtime
        )
        for backend in ("c", "llvm"):
            generated, generated_text = foundation.transpile(
                freak=freak, repo=repo, source=source, backend=backend
            )
            prefix = "freak_tcp_socket_" if backend == "c" else "@freak_llvm_tcp_socket_"
            for operation in (
                "listen",
                "accept",
                "status",
                "eof",
                "local_port",
                "send_all",
                "receive",
                "close",
            ):
                assert prefix + operation in generated_text, (backend, operation)
            binary = root / f"http_server_{backend}{'.exe' if sys.platform == 'win32' else ''}"
            byte_foundation.compile_generated(
                compiler, repo, runtime, generated, binary, backend
            )
            exercise(binary, root)

    print("v3 HTTP server ordnance tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
