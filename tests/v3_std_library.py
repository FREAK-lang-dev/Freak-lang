#!/usr/bin/env python3
"""Run the std library contract fixtures through the public CLI on C and LLVM.

tests/v35_std_library.fk checks std::string, std::json, std::algorithm,
std::convert and std::version on both backends. tests/v35_std_http_client.fk
checks the std::http client (LLVM only, like std/http.fk itself) offline and
against a loopback server that also pins the exact request bytes.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]
EXE = ".exe" if os.name == "nt" else ""
SUMMARY = re.compile(rb"^std (library|http) checks (\d+) failed 0\r?$", re.M)


def build(freak: Path, source: Path, backend: str) -> Path:
    command = [str(freak), "build", source.name] + (["--c"] if backend == "c" else [])
    p = subprocess.run(command, cwd=source.parent, capture_output=True, timeout=600)
    if p.returncode:
        raise AssertionError(f"build {source.name} ({backend}) failed:\n{p.stdout.decode(errors='replace')[-4000:]}\n{p.stderr.decode(errors='replace')[-2000:]}")
    binary = source.with_suffix(EXE)
    if not binary.exists():
        raise AssertionError(f"build {source.name} ({backend}) produced no binary at {binary}")
    return binary


def run(binary: Path, *args: str, expected: int) -> None:
    p = subprocess.run([str(binary), *args], cwd=binary.parent, capture_output=True, timeout=300)
    match = SUMMARY.search(p.stdout)
    if p.returncode or not match or int(match.group(2)) != expected:
        raise AssertionError(f"{binary.name} {' '.join(args)}: exit={p.returncode}\nstdout={p.stdout.decode(errors='replace')[-4000:]}\nstderr={p.stderr.decode(errors='replace')[-2000:]}")
    print(f"PASS {binary.name} {' '.join(args)}: {match.group(0).decode().strip()}", flush=True)


class LoopbackServer:
    """Answers each request by path and records the raw request bytes."""

    def __init__(self) -> None:
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(16)
        self.sock.settimeout(60)
        self.port = self.sock.getsockname()[1]
        self.requests: list[bytes] = []
        self.errors: list[str] = []
        self.thread = threading.Thread(target=self.serve, daemon=True)
        self.thread.start()

    def serve(self) -> None:
        try:
            while True:
                try:
                    conn, _ = self.sock.accept()
                except OSError:
                    return
                with conn:
                    conn.settimeout(20)
                    data = b""
                    while b"\r\n\r\n" not in data:
                        chunk = conn.recv(4096)
                        if not chunk:
                            raise EOFError("client closed before headers")
                        data += chunk
                    head, body = data.split(b"\r\n\r\n", 1)
                    for line in head.split(b"\r\n"):
                        if line.lower().startswith(b"content-length:"):
                            length = int(line.split(b":", 1)[1])
                            while len(body) < length:
                                body += conn.recv(4096)
                    self.requests.append(head + b"\r\n\r\n" + body)
                    path = head.split(b" ")[1]
                    if path == b"/chunked":
                        conn.sendall(b"HTTP/1.1 200 OK\r\nTransfer-Encoding: Chunked\r\nX-Test:  yes \r\n\r\n"
                                     b"5\r\nhello\r\n7;ext=1\r\n, world\r\n0\r\n\r\n")
                    elif path == b"/big":
                        conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 300000\r\n\r\n" + b"x" * 300000)
                    elif path == b"/crlfbody":
                        conn.sendall(b"HTTP/1.1 202 Accepted\r\nContent-Type: text/plain\r\n\r\nline1\r\n\r\nline2")
                    else:
                        conn.sendall(b"HTTP/1.1 201 Created\r\nContent-Length: 2\r\n\r\nok")
        except Exception as exc:  # surfaced by the caller
            self.errors.append(repr(exc))

    def close(self) -> None:
        self.sock.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--freak", type=Path, default=ROOT / "build" / ("freak" + EXE))
    ap.add_argument("--backends", nargs="+", choices=("c", "llvm"), default=["c", "llvm"])
    args = ap.parse_args()
    freak = args.freak.resolve()
    with tempfile.TemporaryDirectory(prefix="freak-std-library-") as tmp:
        work = Path(tmp)
        for backend in args.backends:
            leaf = work / backend
            leaf.mkdir()
            source = leaf / "v35_std_library.fk"
            shutil.copyfile(ROOT / "tests" / "v35_std_library.fk", source)
            run(build(freak, source, backend), expected=152)
        if "llvm" in args.backends:
            leaf = work / "http"
            leaf.mkdir()
            source = leaf / "v35_std_http_client.fk"
            shutil.copyfile(ROOT / "tests" / "v35_std_http_client.fk", source)
            binary = build(freak, source, "llvm")
            run(binary, expected=10)
            server = LoopbackServer()
            try:
                run(binary, str(server.port), expected=18)
            finally:
                server.close()
            assert not server.errors, server.errors
            common = b"Host: 127.0.0.1\r\nConnection: close\r\nUser-Agent: FREAK/0.8\r\n"
            expected = [
                b"GET /chunked HTTP/1.1\r\n" + common + b"\r\n",
                b"GET /big HTTP/1.1\r\n" + common + b"\r\n",
                b"GET /crlfbody HTTP/1.1\r\n" + common + b"\r\n",
                b"PATCH /patch HTTP/1.1\r\n" + common + b"Content-Type: application/json\r\nContent-Length: 7\r\n\r\n{\"a\":1}",
                b"HEAD /h HTTP/1.1\r\n" + common + b"\r\n",
                b"POST /post HTTP/1.1\r\n" + common + b"Content-Type: text/plain\r\nContent-Length: 6\r\n\r\n" + "postΩ".encode(),
            ]
            if server.requests != expected:
                raise AssertionError(f"request bytes differ:\n{server.requests!r}\n!=\n{expected!r}")
            print("PASS std http request bytes", flush=True)
    print("PASS std library contracts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
