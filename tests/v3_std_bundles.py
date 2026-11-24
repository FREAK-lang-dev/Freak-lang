#!/usr/bin/env python3
"""Signed std bundles: install, select, roll back, pin, update and refusals.

Usage: python tests/v3_std_bundles.py build/freak[.exe]

Covers the client side of out-of-band std updates (src/cli/std_*.fk):
- a bundle signed by a trusted key installs, is selected, and builds on the
  LLVM and C backends use its modules; the build says which std it used;
- unsigned, foreign-key, tampered, pinned-module-carrying and non-fitting
  bundles are refused and leave the store unchanged;
- rollback walks the selection history back to the bundled std;
- a damaged stored bundle is skipped with a notice (bundled std builds);
- a project std.lock wins over the user's selection, and a pin that is not
  installed fails the build with a clear message;
- hangar std update/list read a signed index over HTTP, take patches only
  unless --minor, skip yanked versions, and refuse an older index serial.
Throwaway keys are pure-Python seeds (tools/std_bundle.py), so no packages
are needed. FREAK_STD_STORE=1 lets a checkout compiler use the store.
"""
from __future__ import annotations

import functools
import hashlib
import http.server
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import std_bundle  # noqa: E402

TRUSTED = "seed:" + "11" * 32
FOREIGN = "seed:" + "22" * 32
ANSI = re.compile(r"\x1b\[[0-9;]*m")
PROGRAM = 'task main() {\n    pilot m = std_bundle_marker()\n    say "marker={m}"\n}\n'


def plain(text: bytes) -> str:
    return ANSI.sub("", text.decode("utf-8", "replace"))


class Harness:
    def __init__(self, freak: Path, work: Path):
        self.freak = freak
        self.work = work
        self.config = work / "hangar-config"
        public = std_bundle.raw_public(std_bundle.load_key(TRUSTED))
        self.env = os.environ.copy()
        for name in ("FREAK_LIVE", "FREAK_TIMINGS", "FREAK_STD", "FREAK_STD_SOURCE", "FREAK_HOME"):
            self.env.pop(name, None)
        self.env.update({"HANGAR_CONFIG_DIR": str(self.config), "FREAK_STD_STORE": "1",
                         "FREAK_STD_TRUSTED_KEY": public, "FREAK_PLAIN": "1"})

    def run(self, *args: str, cwd: Path | None = None, extra: dict | None = None, timeout: int = 600):
        env = dict(self.env)
        if extra:
            env.update(extra)
        result = subprocess.run([str(self.freak), *args], cwd=cwd or self.work, env=env,
                                capture_output=True, timeout=timeout)
        return result.returncode, plain(result.stdout + result.stderr)

    def hangar(self, *args: str, cwd: Path | None = None, extra: dict | None = None):
        return self.run("hangar", *args, cwd=cwd, extra=extra)

    def expect(self, label: str, outcome, code: int | None, *needles: str) -> str:
        status, text = outcome
        if code is not None and status != code:
            raise AssertionError(f"{label}: exit {status}, wanted {code}\n{text}")
        for needle in needles:
            if needle not in text:
                raise AssertionError(f"{label}: missing {needle!r}\n{text}")
        print(f"PASS {label}")
        return text

    def store(self) -> list[str]:
        root = self.config / "std" / "store"
        return sorted(p.name for p in root.iterdir() if not p.name.startswith(".")) if root.exists() else []


def make_std(work: Path, name: str, marker: str) -> Path:
    target = work / name
    shutil.copytree(REPO / "std", target)
    with (target / "math.fk").open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(f'\ntask std_bundle_marker() -> word {{\n    give back "{marker}"\n}}\n')
    return target


def pack(work: Path, std_dir: Path, version: str, key: str = TRUSTED, **options: str) -> Path:
    out = work / f"std-{version}.fkstd"
    command = [sys.executable, str(REPO / "tools/std_bundle.py"), "pack", "--version", version,
               "--compiler", options.pop("compiler", ">=0.15.2"), "--key", key, "--out", str(out),
               "--std-dir", str(std_dir)]
    for option, value in options.items():
        command += ["--" + option.replace("_", "-"), value]
    subprocess.run(command, check=True, capture_output=True)
    return out


def resign(bundle: bytes, edit) -> bytes:
    """Rebuild a bundle after edit(frames) changes its frames; re-signs std.toml."""
    frames: list[tuple[str, bytes]] = []
    view = bundle[len(b"freak-std-bundle 1\n"):]
    while not view.startswith(b"end\n"):
        header, _, view = view.partition(b"\n")
        _, name, length = header.decode().split(" ")
        frames.append((name, view[: int(length)]))
        view = view[int(length) + 1:]
    frames = edit(frames)
    manifest = dict(frames)["std.toml"]
    signature = std_bundle.load_key(TRUSTED).sign(
        std_bundle.MANIFEST_PREFIX + hashlib.sha256(manifest).hexdigest().encode()).hex()
    out = b"freak-std-bundle 1\n"
    for name, data in frames:
        if name == "std.toml.sig":
            data = (signature + "\n").encode()
        out += std_bundle.frame(name, data)
    return out + b"end\n"


def with_runtime_frame(frames):
    runtime = (REPO / "std/runtime.fk").read_bytes()
    out = []
    for name, data in frames:
        if name == "std.toml":
            data += f'"runtime.fk" = "{hashlib.sha256(runtime).hexdigest()}"\n'.encode()
        out.append((name, data))
    out.append(("runtime.fk", runtime))
    return out


def edit_manifest(old: bytes, new: bytes):
    def edit(frames):
        return [(name, data.replace(old, new) if name == "std.toml" else data) for name, data in frames]
    return edit


def serve(directory: Path):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
    handler.log_message = lambda *args: None
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def sign_probe(h: Harness, work: Path) -> None:
    """Run src/cli/std_sign.fk directly on public-key encodings RFC 8032 rejects."""
    seed = std_bundle.load_key(TRUSTED)
    public = std_bundle.raw_public(seed)
    message = "freak-std-probe"
    signature = seed.sign(message.encode()).hex()
    # y = p + 1 reduces to y = 1 (the identity point) if y >= p is not refused,
    # and 01 00..00 80 is that point with a sign bit although x = 0.
    cases = [
        ("canonical key unpacks", public, 1),
        ("canonical identity unpacks", "01" + "00" * 31, 1),
        ("y = p refused", "ed" + "ff" * 30 + "7f", 0),
        ("y = p + 1 refused", "ee" + "ff" * 30 + "7f", 0),
        ("x = 0 with sign bit refused", "01" + "00" * 30 + "80", 0),
    ]
    body = "task main() {\n"
    for index, (_, key, _) in enumerate(cases):
        body += f'    pilot k{index} = stdsig_unpack_neg(stdsig_hex_bytes("{key}", 32)).length()\n'
        body += f'    say "case{index}=" + word_from_int(k{index})\n'
    body += f'    if stdsig_verify("{message}", "{signature}", "{public}") {{ say "verify=yes" }} else {{ say "verify=no" }}\n'
    body += f'    if stdsig_verify("{message}x", "{signature}", "{public}") {{ say "forged=yes" }} else {{ say "forged=no" }}\n'
    body += "}\n"
    probe = work / "sign_probe.fk"
    probe.write_text((REPO / "src/cli/std_sign.fk").read_text(encoding="utf-8") + "\n" + body, encoding="utf-8")
    text = h.expect("std_sign probe runs", h.run("run", str(probe)), 0, "verify=yes", "forged=no")
    for index, (label, _, unpacks) in enumerate(cases):
        line = next((part for part in text.split() if part.startswith(f"case{index}=")), "")
        got = int(line.split("=")[1]) if line else -1
        if (got > 0) != bool(unpacks):
            raise AssertionError(f"{label}: unpacked length {got}\n{text}")
        print(f"PASS {label}")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    freak = Path(sys.argv[1]).resolve()
    with tempfile.TemporaryDirectory(prefix="freak-std-bundles-") as temporary:
        work = Path(temporary)
        h = Harness(freak, work)
        (work / "p.fk").write_text(PROGRAM, encoding="utf-8")
        (work / "uses_std.fk").write_text('task main() {\n    pilot a = std_abs(0 - 7)\n    say "abs={a}"\n}\n', encoding="utf-8")
        sign_probe(h, work)

        h.expect("status with an empty store", h.hangar("std", "status"), 0, "Active:   std 0.16.0", "(bundled)")

        one = pack(work, make_std(work, "std-a", "bundle-one"), "0.16.1")
        before = h.store()
        h.expect("foreign key refused", h.hangar("std", "install", str(pack(work, work / "std-a", "0.16.1", FOREIGN))),
                 1, "not signed by a FREAK release key")
        one = pack(work, work / "std-a", "0.16.1")
        tampered = work / "tampered.fkstd"
        data = one.read_bytes()
        tampered.write_bytes(data.replace(b'give back "bundle-one"', b'give back "bundle-0ne"'))
        h.expect("tampered file refused", h.hangar("std", "install", str(tampered)), 1, "does not match std.toml")
        carrying = work / "carrying.fkstd"
        carrying.write_bytes(resign(data, with_runtime_frame))
        h.expect("pinned module refused", h.hangar("std", "install", str(carrying)), 1, "may not carry pinned module runtime")
        escaping = work / "escaping.fkstd"
        escaping.write_bytes(resign(data, edit_manifest(b'version = "0.16.1"', b'version = "../escape"')))
        h.expect("signed path-like version refused", h.hangar("std", "install", str(escaping)), 1, "std.version must be")
        assert not (h.config / "std" / "escape").exists()
        remapped = work / "remapped.fkstd"
        remapped.write_bytes(resign(data, edit_manifest(b'math = "always math.fk"', b'math = "always string.fk"')))
        h.expect("module mapped to another file refused", h.hangar("std", "install", str(remapped)), 1, "module math must load math.fk")
        h.expect("foreign API refused", h.hangar("std", "install", str(pack(work, work / "std-a", "0.16.1", std_api="freak-v3-std-api-99"))),
                 1, "does not fit this compiler")
        h.expect("compiler range refused", h.hangar("std", "install", str(pack(work, work / "std-a", "0.16.1", compiler=">=9.0.0"))),
                 1, "supports compilers >=9.0.0")
        assert h.store() == before == [], h.store()

        one = pack(work, work / "std-a", "0.16.1")
        h.expect("install 0.16.1", h.hangar("std", "install", str(one)), 0, "std 0.16.1 installed and selected")
        h.expect("status shows 0.16.1", h.hangar("std", "status"), 0, "Active:   std 0.16.1", "(selected)")
        h.expect("same bundle reinstalls cleanly", h.hangar("std", "install", str(one)), 0, "installed and selected")
        h.expect("LLVM build uses 0.16.1", h.run("run", "p.fk"), 0, "std 0.16.1 (updated)", "marker=bundle-one")
        h.expect("C build uses 0.16.1", h.run("run", "p.fk", "--c"), 0, "marker=bundle-one")

        two = pack(work, make_std(work, "std-b", "bundle-two"), "0.16.2")
        h.expect("install 0.16.2", h.hangar("std", "install", str(two)), 0, "std 0.16.2 installed")
        # Selection and history are one file: a failed write changes neither.
        selected = h.config / "std" / "selected"
        state = selected.read_bytes()
        fail_selected = {"FREAK_STD_TEST_FAIL_WRITE": "selected"}
        h.expect("failed use changes nothing", h.hangar("std", "use", "0.16.1", extra=fail_selected), 1, "NOT CHANGED")
        assert selected.read_bytes() == state, selected.read_text()
        h.expect("failed rollback changes nothing", h.hangar("std", "rollback", extra=fail_selected), 1, "NOT CHANGED")
        assert selected.read_bytes() == state, selected.read_text()
        assert not list(selected.parent.glob("selected.new*")), list(selected.parent.glob("selected.new*"))
        h.expect("rollback to 0.16.1", h.hangar("std", "rollback"), 0, "Rolled back", "Selected std 0.16.1.")
        h.expect("rollback to bundled", h.hangar("std", "rollback"), 0, "Selected the bundled std 0.16.0.")
        h.expect("nothing left to roll back", h.hangar("std", "rollback"), 1, "No earlier std selection")
        h.expect("bundled std lacks the marker", h.run("build", "p.fk"), 1, "unknown callable 'std_bundle_marker'")

        # A folder sync failure after the rename still leaves the new selection.
        h.expect("use 0.16.1 despite a sync failure", h.hangar("std", "use", "0.16.1", extra={"FREAK_STD_TEST_FAIL_WRITE": "sync:selected"}),
                 0, "could not sync its folder", "Selected std 0.16.1.")
        h.expect("synced-late selection is active", h.hangar("std", "status"), 0, "Active:   std 0.16.1")
        stored_math = h.config / "std" / "store" / "0.16.1" / "math.fk"
        original = stored_math.read_bytes()
        stored_math.write_bytes(original + b"\n-- edited\n")
        damaged = h.expect("damaged store falls back", h.run("build", "p.fk"), 1,
                           "selected std 0.16.1 is not used", "does not match its manifest")
        assert "unknown callable 'std_bundle_marker'" in damaged, damaged
        h.expect("bundled std works after the fallback", h.run("run", "uses_std.fk"), 0,
                 "selected std 0.16.1 is not used", "abs=7")
        h.expect("reinstall repairs a damaged version", h.hangar("std", "install", str(one)), 0,
                 "Replacing the damaged std 0.16.1", "installed and selected")
        assert stored_math.read_bytes() == original
        h.expect("repaired version builds", h.run("run", "p.fk"), 0, "std 0.16.1 (updated)", "marker=bundle-one")
        h.expect("use unknown version refused", h.hangar("std", "use", "0.16.7"), 1, "is not installed")
        h.expect("path-like version refused", h.hangar("std", "use", ".."), 1, "hangar std")
        h.expect("empty version parts refused", h.hangar("std", "pin", "0..1"), 1, "hangar std")
        h.expect("extra prune arguments refused", h.hangar("std", "prune", "--all", "--keep", "5"), 1, "hangar std")
        assert "0.16.1" in h.store() and "0.16.2" in h.store(), h.store()
        h.expect("unsigned store copy refused", h.run("build", "p.fk", extra={"FREAK_STD_TRUSTED_KEY": ""}), 1,
                 "not signed by a key this compiler trusts")

        project = work / "proj"
        h.expect("project init", h.hangar("init", str(project)), 0)
        (project / "src" / "main.fk").write_text(PROGRAM, encoding="utf-8")
        h.expect("pin 0.16.2", h.hangar("std", "pin", "0.16.2", cwd=project), 0, "Pinned this project to std 0.16.2")
        h.expect("select bundled", h.hangar("std", "use", "bundled"), 0)
        h.expect("project pin wins", h.run("run", "src/main.fk", cwd=project), 0, "std 0.16.2 (pinned by std.lock)", "marker=bundle-two")
        h.expect("use reports the project pin", h.hangar("std", "use", "0.16.1", cwd=project), 0,
                 "Selected std 0.16.1.", "Builds here still use std 0.16.2 (pinned by")
        h.expect("select bundled again", h.hangar("std", "use", "bundled"), 0)
        # A failed rewrite keeps the old pin.
        pin_before = (project / "std.lock").read_bytes()
        h.expect("failed repin", h.hangar("std", "pin", cwd=project, extra={"FREAK_STD_TEST_FAIL_WRITE": "std.lock"}), 1, "NOT PINNED")
        assert (project / "std.lock").read_bytes() == pin_before, "failed repin lost std.lock"
        assert not list(project.glob("std.lock.new*")), list(project.glob("std.lock.new*"))
        h.expect("repin keeps the old pin until replaced", h.run("run", "src/main.fk", cwd=project), 0, "marker=bundle-two")
        (project / "std.lock").write_text('version = "0.16.2"\nmanifest_sha256 = "abc\n', encoding="utf-8")
        h.expect("unterminated lock value refused", h.run("build", "src/main.fk", cwd=project), 1, "std.lock is malformed")
        (project / "std.lock").write_text('version = "0.16.2"\nmanifest_sha256 = ""\n', encoding="utf-8")
        h.expect("empty lock digest refused", h.run("build", "src/main.fk", cwd=project), 1, "malformed manifest_sha256")
        (project / "std.lock").write_text('version = "0.16.2"\n', encoding="utf-8")
        h.expect("omitted lock digest allowed", h.run("run", "src/main.fk", cwd=project), 0, "marker=bundle-two")
        (project / "std.lock").write_bytes(pin_before)
        # A sync failure after the rename (ok = false, completed = true) still
        # publishes the new pin: repin 0.16.2 -> 0.16.1 and build with it.
        h.expect("repin despite a sync failure", h.hangar("std", "pin", "0.16.1", cwd=project, extra={"FREAK_STD_TEST_FAIL_WRITE": "sync:std.lock"}),
                 0, "could not sync its folder", "Pinned this project to std 0.16.1")
        h.expect("synced-late pin is active", h.run("run", "src/main.fk", cwd=project), 0, "std 0.16.1 (pinned by std.lock)", "marker=bundle-one")
        (project / "std.lock").write_bytes(pin_before)
        h.expect("pin bundled by number", h.hangar("std", "pin", "0.16.0", cwd=project), 0, "Pinned this project to the bundled std")
        h.expect("bundled pin builds", h.run("build", "src/main.fk", cwd=project), 1, "unknown callable 'std_bundle_marker'")
        (project / "std.lock").write_text('version = "0.16.0"\nmanifest_sha256 = "' + "0" * 64 + '"\n', encoding="utf-8")
        h.expect("numeric pin of the bundled number checks its digest", h.run("build", "src/main.fk", cwd=project), 1, "pins std 0.16.0")
        h.expect("pin current selection", h.hangar("std", "pin", cwd=project), 0, "Pinned this project to the bundled std")
        (project / "std.lock").write_text('version = "0.16.9"\n', encoding="utf-8")
        h.expect("missing pin fails the build", h.run("build", "src/main.fk", cwd=project), 1, "pins std 0.16.9")
        h.expect("unpin", h.hangar("std", "unpin", cwd=project), 0, "Removed the std pin")
        assert not (project / "std.lock").exists()

        site = work / "site"
        site.mkdir()
        three = pack(work, make_std(work, "std-c", "bundle-three"), "0.16.3")
        four = pack(work, make_std(work, "std-d", "bundle-four"), "0.16.4")
        minor = pack(work, make_std(work, "std-e", "bundle-minor"), "0.17.0")
        for bundle in (three, four, minor):
            shutil.copy(bundle, site / bundle.name)

        def publish(serial: int, key: str = TRUSTED):
            subprocess.run([sys.executable, str(REPO / "tools/std_bundle.py"), "index", "--serial", str(serial),
                            "--key", key, "--out", str(site), "--yank", "0.16.4", str(three), str(four), str(minor)],
                           check=True, capture_output=True)

        truncated = work / "truncated.fkstd"
        truncated.write_bytes(three.read_bytes()[:-40])
        for label, extra_args in (("index refuses a truncated bundle", ["--serial", "1", str(truncated)]),
                                  ("index refuses a negative serial", ["--serial", "-1", str(three)])):
            refused = subprocess.run([sys.executable, str(REPO / "tools/std_bundle.py"), "index", "--key", TRUSTED,
                                      "--out", str(work / "refused-index"), *extra_args], capture_output=True)
            assert refused.returncode != 0 and not (work / "refused-index" / "index.txt").exists(), (label, refused)
            print(f"PASS {label}")

        server = serve(site)
        try:
            source = {"FREAK_STD_SOURCE": f"http://127.0.0.1:{server.server_address[1]}"}
            publish(5, FOREIGN)
            h.expect("foreign index refused", h.hangar("std", "update", extra=source), 1, "index is not signed")
            publish(5)
            h.expect("use 0.16.2 before update", h.hangar("std", "use", "0.16.2"), 0)
            h.expect("list the index", h.hangar("std", "list", extra=source), 0, "std 0.16.3  fits", "std 0.16.4  yanked", "std 0.17.0  fits")
            h.expect("patch update skips yanked and minor", h.hangar("std", "update", extra=source), 0, "std 0.16.2 -> 0.16.3")
            h.expect("no newer patch", h.hangar("std", "update", extra=source), 0, "is the newest that fits", "hangar std update --minor")
            h.expect("minor update", h.hangar("std", "update", "--minor", extra=source), 0, "std 0.16.3 -> 0.17.0")
            h.expect("update result builds", h.run("run", "p.fk"), 0, "marker=bundle-minor")
            publish(4)
            h.expect("older index serial refused", h.hangar("std", "update", extra=source), 1, "refusing a rollback")
        finally:
            server.shutdown()

        h.expect("prune keeps the newest and the selected", h.hangar("std", "prune", "--keep", "1"), 0, "Removed std 0.16.1")
        assert h.store() == ["0.17.0"], h.store()
        h.expect("bundled override", h.run("run", "p.fk", extra={"FREAK_STD": "bundled"}), 1, "unknown callable 'std_bundle_marker'")
    print("std bundles: all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
