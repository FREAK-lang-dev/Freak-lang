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

from windows_private_fixture import WindowsPrivateFixture

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


class Zeros(io.RawIOBase):
    """A stream of zero bytes, so a huge entry costs no memory."""

    def __init__(self, size: int) -> None:
        self.left = size

    def readable(self) -> bool:
        return True

    def readinto(self, buffer) -> int:
        count = min(len(buffer), self.left)
        buffer[:count] = bytes(count)
        self.left -= count
        return count


def archive(kind: str = "good") -> bytes:
    manifest = LIB_MANIFEST.replace("beacon-kit", kind) if kind != "good" else LIB_MANIFEST
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz", compresslevel=1, format=tarfile.GNU_FORMAT,
                      encoding="utf-8", errors="surrogateescape") as tar:
        for name, text in (("hangar.toml", manifest), ("src/signal.fk", LIB_SOURCE)):
            data = text.encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o644
            tar.addfile(info, io.BytesIO(data))
        if kind == "linky":
            link = tarfile.TarInfo("src/escape.fk")
            link.type = tarfile.SYMTYPE
            link.linkname = "../../outside.fk"
            tar.addfile(link)
        if kind in ("bomb", "badname"):
            # 300 MiB of zeros: a tiny download that would fill a disk. The
            # badname copy hides it behind a name that is not valid UTF-8.
            name = "assets/filler.bin" if kind == "bomb" else "assets/filler\udcff.bin"
            big = tarfile.TarInfo(name)
            big.size = 300 * 1024 * 1024
            tar.addfile(big, Zeros(big.size))
    return buffer.getvalue()


class Registry(BaseHTTPRequestHandler):
    payloads: dict[str, bytes] = {}
    requests: list[str] = []
    authorized: list[str] = []

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
        if self.headers.get("Authorization"):
            Registry.authorized.append(self.path)
        parts = self.path.split("/")
        # /api/v1/units/<name> and /api/v1/units/<name>/0.1.0/download
        name = parts[4] if len(parts) > 4 else ""
        if name in Registry.payloads and len(parts) == 5:
            body = {"name": name, "versions": [{"version": "0.1.0"}]}
            self.reply(200, json.dumps(body).encode(), "application/json")
        elif name in Registry.payloads and parts[5:] == ["0.1.0", "download"]:
            self.reply(200, Registry.payloads[name], "application/gzip")
        elif self.path == "/api/v1/auth/whoami":
            self.reply(401, b'{"error":"unauthorized"}', "application/json")
        else:
            self.reply(404, b'{"error":"not found"}', "application/json")

    do_POST = do_GET


def run(argv: list[str], cwd: Path, env: dict[str, str], label: str, expect: int = 0) -> str:
    result = subprocess.run(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                            capture_output=True, timeout=600)
    output = ANSI.sub("", (result.stdout + result.stderr).decode("utf-8", "replace"))
    if (result.returncode == 0) != (expect == 0):
        raise AssertionError(f"{label} exited {result.returncode}:\n{output}")
    return output


def refused(argv: list[str], cwd: Path, env: dict[str, str], label: str, needle: str) -> None:
    output = run(argv, cwd, env, label, expect=1)
    if needle not in output:
        raise AssertionError(f"{label}: expected '{needle}' in:\n{output}")


def write_project(path: Path, manifest: str, private: WindowsPrivateFixture) -> None:
    path.mkdir()
    (path / "src").mkdir()
    private.claim_fresh_directories(path, path / "src")
    (path / "hangar.toml").write_text(manifest, encoding="utf-8")
    (path / "src" / "main.fk").write_text("task main() {\n    say 1\n}\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freak", required=True, type=Path)
    parser.add_argument("--hangar", required=True, type=Path)
    args = parser.parse_args()
    freak = str(args.freak.resolve())
    hangar = str(args.hangar.resolve())

    Registry.payloads = {"beacon-kit": archive(), "linky": archive("linky"), "bomb": archive("bomb"),
                        "badname": archive("badname")}
    server = ThreadingHTTPServer(("127.0.0.1", 0), Registry)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with tempfile.TemporaryDirectory(prefix="freak-registry-install-") as raw:
            root = Path(raw)
            # Windows Hangar only writes into folders with a private owner ACL.
            private = WindowsPrivateFixture(root)
            home = root / "home"
            project = root / "consumer"
            home.mkdir()
            project.mkdir()
            private.claim_fresh_directories(home, project)
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

            # #193 and links: hostile archives are refused before unpacking.
            refused([hangar, "add", "linky", "^0.1.0"], project, env, "add archive with a link", "link or special file")
            refused([hangar, "add", "bomb", "^0.1.0"], project, env, "add archive bomb", "MiB")
            run([hangar, "add", "badname", "^0.1.0"], project, env, "add archive with a non-UTF-8 name", expect=1)
            if any(root.rglob("filler*")) or (root / "outside.fk").exists():
                raise AssertionError("a refused archive was unpacked")

            # #197: a mistyped publish option never publishes.
            requests = len(Registry.requests)
            refused([hangar, "publish", "--dryrun"], project, env, "publish --dryrun", "Nothing was published")
            if len(Registry.requests) != requests:
                raise AssertionError("publish with an unknown option contacted the registry")

            # #196: a bare pre-0.15.1 token is only for the default registry.
            (home / ".hangar").mkdir(exist_ok=True)
            (home / ".hangar" / "credentials").write_text("legacy-secret-token\n", encoding="utf-8")
            run([hangar, "auth", "status"], project, env, "auth status with legacy token", expect=1)
            if Registry.authorized:
                raise AssertionError(f"legacy token was sent to a custom registry: {Registry.authorized}")
            (home / ".hangar" / "credentials").unlink()

            # #195: a lockless project from the old hangar init still installs.
            legacy = root / "legacy"
            write_project(legacy, '[project]\nname = "legacy"\nversion = "0.1.0"\n\n[dependencies]\n', private)
            run([hangar, "install"], legacy, env, "install in a legacy project")

            # An explicit empty kind is a declaration, so it is reported, not
            # silently treated as a legacy project.
            empty_kind = root / "empty-kind"
            write_project(empty_kind, '[project]\nname = "empty-kind"\nversion = "0.1.0"\nkind = ""\n', private)
            run([hangar, "install"], empty_kind, env, "install with an empty kind", expect=1)

            # #194: a symlinked module is refused before upload.
            library = root / "linked-lib"
            write_project(library, '[project]\nname = "linked-lib"\nversion = "0.1.0"\nkind = "lib"\n\n'
                          '[modules]\nsignal = "src/signal.fk"\n\n[exports]\nvalue = "signal::value"\n',
                          private)
            (root / "real.fk").write_text("task value() -> int {\n    give back 1\n}\n", encoding="utf-8")
            try:
                (library / "src" / "signal.fk").symlink_to(root / "real.fk")
            except OSError:
                print("registry install: symlinks unavailable here, skipped the publish link case")
            else:
                refused([hangar, "publish", "--dry-run"], library, env, "publish a symlinked module", "regular file")
    finally:
        server.shutdown()
    print("registry install: passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
