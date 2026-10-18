#!/usr/bin/env python3
"""Install a package from a registry and run a program that imports it.

A small in-process HTTP server stands in for Ordnance's read-only unit
routes, so this runs on every CI platform without network access. Windows is
the case that matters most: Hangar unpacks archives with the system tar, which
must be able to enter Hangar's private staging folder.
"""
from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ANSI = re.compile(r"\x1b\[[0-9;]*m")

LIB_MANIFEST = """[project]
name = "beacon-kit"
version = "0.1.0"
kind = "lib"

[modules]
signal = "src/signal.fk"

[exports]
beacon_value = "signal::beacon_value"
"""
LIB_SOURCE = "task beacon_value() -> int {\n    give back 42\n}\n"
APP_SOURCE = """use beacon_kit::{beacon_value}

task main() {
    pilot value = beacon_value()
    say "beacon {value}"
}
"""


def archive() -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for name, text in (("hangar.toml", LIB_MANIFEST), ("src/signal.fk", LIB_SOURCE)):
            data = text.encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o644
            tar.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


class Registry(BaseHTTPRequestHandler):
    payload = b""
    requests: list[str] = []

    def log_message(self, *args) -> None:
        pass

    def reply(self, status: int, body: bytes, kind: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        Registry.requests.append(self.path)
        if self.path == "/api/v1/units/beacon-kit":
            body = {"name": "beacon-kit", "versions": [{"version": "0.1.0"}]}
            self.reply(200, json.dumps(body).encode(), "application/json")
        elif self.path == "/api/v1/units/beacon-kit/0.1.0/download":
            self.reply(200, Registry.payload, "application/gzip")
        else:
            self.reply(404, b'{"error":"not found"}', "application/json")


def run(argv: list[str], cwd: Path, env: dict[str, str], label: str) -> str:
    result = subprocess.run(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                            capture_output=True, timeout=600)
    output = ANSI.sub("", (result.stdout + result.stderr).decode("utf-8", "replace"))
    if result.returncode != 0:
        raise AssertionError(f"{label} exited {result.returncode}:\n{output}")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freak", required=True, type=Path)
    parser.add_argument("--hangar", required=True, type=Path)
    args = parser.parse_args()
    freak = str(args.freak.resolve())
    hangar = str(args.hangar.resolve())

    Registry.payload = archive()
    server = ThreadingHTTPServer(("127.0.0.1", 0), Registry)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with tempfile.TemporaryDirectory(prefix="freak-registry-install-") as raw:
            root = Path(raw)
            home = root / "home"
            project = root / "consumer"
            home.mkdir()
            project.mkdir()
            env = dict(os.environ)
            env.update({
                "HOME": str(home), "USERPROFILE": str(home),
                "HANGAR_CONFIG_DIR": str(home / ".hangar"),
                "HANGAR_REGISTRY": f"http://127.0.0.1:{server.server_address[1]}/api/v1",
                "NO_COLOR": "1",
            })
            env.pop("HANGAR_TOKEN", None)

            # An unknown command must fail so scripts notice typos.
            unknown = subprocess.run([freak, "frobnicate"], env=env, capture_output=True, timeout=60)
            if unknown.returncode == 0:
                raise AssertionError("freak frobnicate exited 0")

            run([hangar, "init"], project, env, "hangar init")
            (project / "src").mkdir(exist_ok=True)
            (project / "src" / "main.fk").write_text(APP_SOURCE, encoding="utf-8")
            run([hangar, "add", "beacon-kit", "^0.1.0"], project, env, "hangar add from registry")
            lock = (project / "hangar.lock").read_text(encoding="utf-8")
            if "beacon-kit" not in lock or "0.1.0" not in lock:
                raise AssertionError(f"lock does not pin beacon-kit 0.1.0:\n{lock}")
            if "/api/v1/units/beacon-kit/0.1.0/download" not in Registry.requests:
                raise AssertionError(f"archive was never downloaded: {Registry.requests}")
            output = run([freak, "run"], project, env, "freak run")
            if "beacon 42" not in output:
                raise AssertionError(f"program output is missing 'beacon 42':\n{output}")
            leftovers = [p for p in project.rglob(".registry-*")]
            if leftovers:
                raise AssertionError(f"registry staging was not cleaned: {leftovers}")
            # A fresh install from the lock must reuse the cache offline.
            run([hangar, "install", "--offline"], project, env, "hangar install --offline")
    finally:
        server.shutdown()
    print("registry install: passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
