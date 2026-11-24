#!/usr/bin/env python3
"""Build, sign and index FREAK std bundles (.fkstd).

A std bundle carries the unpinned std modules plus a signed std.toml; the
compiler checks it natively (src/cli/std_sign.fk, src/cli/std_commands.fk).

    python tools/std_bundle.py pubkey KEY
        Print the raw Ed25519 public key (64 hex) of an OpenSSH or PEM
        private key, or of an OpenSSH .pub file. This is what goes into
        FREAK_STD_TRUSTED_KEYS in src/cli/std_store.fk.

    python tools/std_bundle.py pack --version 0.16.1 --compiler ">=0.16.0 <0.18.0" \\
            --key KEY --out dist/std-0.16.1.fkstd [--std-dir std]
        Bundle every unpinned module that std/std.toml lists.

    python tools/std_bundle.py index --serial 3 --key KEY --out dist BUNDLE... [--yank 0.16.0]
        Write dist/index.txt and dist/index.txt.sig for the given bundles.

KEY is a path, "env:NAME" to read the private key text from an environment
variable (CI secrets), or "seed:<64 hex>" for a throwaway test key. Paths and
env keys need the `cryptography` package; seed keys are pure Python.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path

PINNED = {"runtime", "ui", "http_server"}
MANIFEST_PREFIX = b"freak-std-manifest-v1\n"
INDEX_PREFIX = b"freak-std-index-v1\n"
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


class SeedKey:
    """Pure-Python RFC 8032 Ed25519 signer for "seed:<64 hex>" keys (tests, no
    third-party packages). Release keys use OpenSSH/PEM via `cryptography`."""

    P = 2**255 - 19
    L = 2**252 + 27742317777372353535851937790883648493
    D = -121665 * pow(121666, P - 2, P) % P

    def __init__(self, seed: bytes):
        digest = hashlib.sha512(seed).digest()
        scalar = bytearray(digest[:32])
        scalar[0] &= 248
        scalar[31] &= 127
        scalar[31] |= 64
        self.scalar = int.from_bytes(scalar, "little")
        self.prefix = digest[32:]
        self.public = self.encode(self.mul(self.scalar, self.base()))

    @classmethod
    def add(cls, a, b):
        p, d = cls.P, cls.D
        x1, y1, z1, t1 = a
        x2, y2, z2, t2 = b
        aa = (y1 - x1) * (y2 - x2) % p
        bb = (y1 + x1) * (y2 + x2) % p
        cc = t1 * 2 * d * t2 % p
        dd = z1 * 2 * z2 % p
        e, f, g, h = bb - aa, dd - cc, dd + cc, bb + aa
        return (e * f % p, g * h % p, f * g % p, e * h % p)

    @classmethod
    def mul(cls, scalar: int, point):
        result = (0, 1, 1, 0)
        while scalar:
            if scalar & 1:
                result = cls.add(result, point)
            point = cls.add(point, point)
            scalar >>= 1
        return result

    @classmethod
    def base(cls):
        p = cls.P
        y = 4 * pow(5, p - 2, p) % p
        xx = (y * y - 1) * pow(cls.D * y * y + 1, p - 2, p) % p
        x = pow(xx, (p + 3) // 8, p)
        if (x * x - xx) % p:
            x = x * pow(2, (p - 1) // 4, p) % p
        if x & 1:
            x = p - x
        return (x, y, 1, x * y % p)

    @classmethod
    def encode(cls, point) -> bytes:
        p = cls.P
        x, y, z, _ = point
        zi = pow(z, p - 2, p)
        x, y = x * zi % p, y * zi % p
        return (y | ((x & 1) << 255)).to_bytes(32, "little")

    def sign(self, message: bytes) -> bytes:
        r = int.from_bytes(hashlib.sha512(self.prefix + message).digest(), "little") % self.L
        encoded_r = self.encode(self.mul(r, self.base()))
        k = int.from_bytes(hashlib.sha512(encoded_r + self.public + message).digest(), "little") % self.L
        return encoded_r + ((r + k * self.scalar) % self.L).to_bytes(32, "little")


def load_key(spec: str):
    if spec.startswith("seed:"):
        return SeedKey(bytes.fromhex(spec[5:]))
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    data = os.environ[spec[4:]].encode() if spec.startswith("env:") else Path(spec).read_bytes()
    if b"OPENSSH PRIVATE KEY" in data:
        key = serialization.load_ssh_private_key(data, password=None)
    else:
        key = serialization.load_pem_private_key(data, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise SystemExit("std signing keys must be Ed25519")
    return key


def raw_public(key) -> str:
    if isinstance(key, SeedKey):
        return key.public.hex()
    from cryptography.hazmat.primitives import serialization

    return key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()


def pubkey(spec: str) -> str:
    text = Path(spec).read_text(errors="replace") if not spec.startswith(("env:", "seed:")) else ""
    if text.startswith("ssh-ed25519 "):
        from cryptography.hazmat.primitives import serialization

        public = serialization.load_ssh_public_key(text.encode())
        return public.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()
    return raw_public(load_key(spec))


def parse_manifest(text: str) -> dict[str, list[tuple[str, str]]]:
    sections: dict[str, list[tuple[str, str]]] = {}
    section = ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            sections.setdefault(section, [])
            continue
        name, _, value = line.partition("=")
        sections.setdefault(section, []).append((name.strip().strip('"'), value.strip().strip('"')))
    return sections


def frame(name: str, data: bytes) -> bytes:
    return f"file {name} {len(data)}\n".encode() + data + b"\n"


def pack(args: argparse.Namespace) -> None:
    if not SEMVER.match(args.version):
        raise SystemExit(f"not a release version: {args.version}")
    std_dir = Path(args.std_dir)
    manifest = parse_manifest((std_dir / "std.toml").read_text(encoding="utf-8"))
    info = dict(manifest.get("std", []))
    modules = manifest.get("modules", [])
    if {name for name, _ in modules} & PINNED != PINNED:
        raise SystemExit("std.toml must list runtime, ui and http_server")
    files: list[tuple[str, bytes]] = []
    for name, entry in modules:
        if name in PINNED:
            continue
        _, _, relative = entry.partition(" ")
        files.append((relative, (std_dir / relative).read_bytes()))
    lines = [
        "# FREAK std bundle manifest (generated by tools/std_bundle.py).",
        "[std]",
        f'version = "{args.version}"',
        f'std_api = "{args.std_api or info["std_api"]}"',
        f'abi = "{args.abi or info["abi"]}"',
        f'runtime_api = "{args.runtime_api or info["runtime_api"]}"',
        f'compiler = "{args.compiler}"',
        "",
        "[modules]",
    ]
    lines += [f'{name} = "{entry}"' for name, entry in modules]
    lines += ["", "[files]"]
    lines += [f'"{relative}" = "{hashlib.sha256(data).hexdigest()}"' for relative, data in files]
    manifest_bytes = ("\n".join(lines) + "\n").encode()
    key = load_key(args.key)
    signature = key.sign(MANIFEST_PREFIX + hashlib.sha256(manifest_bytes).hexdigest().encode()).hex()
    out = b"freak-std-bundle 1\n" + frame("std.toml", manifest_bytes) + frame("std.toml.sig", (signature + "\n").encode())
    for relative, data in files:
        out += frame(relative, data)
    out += b"end\n"
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(out)
    print(f"{target}  std {args.version}  sha256 {hashlib.sha256(out).hexdigest()}")


def read_bundle(path: Path) -> tuple[dict[str, str], bytes]:
    data = path.read_bytes()
    header = b"freak-std-bundle 1\nfile std.toml "
    if not data.startswith(header):
        raise SystemExit(f"{path} is not a std bundle")
    rest = data[len(header):]
    length_text, _, rest = rest.partition(b"\n")
    manifest = rest[: int(length_text)].decode()
    return dict(parse_manifest(manifest).get("std", [])), data


def index(args: argparse.Namespace) -> None:
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = ["freak-std-index 1", f"serial {args.serial}"]
    for bundle in args.bundles:
        info, data = read_bundle(Path(bundle))
        yanked = "yes" if info["version"] in (args.yank or []) else "no"
        lines.append(" ".join(["std", info["version"], hashlib.sha256(data).hexdigest(), info["std_api"],
                               info["abi"], info["runtime_api"], yanked, info["compiler"]]))
    text = ("\n".join(lines) + "\n").encode()
    key = load_key(args.key)
    (out_dir / "index.txt").write_bytes(text)
    (out_dir / "index.txt.sig").write_text(key.sign(INDEX_PREFIX + hashlib.sha256(text).hexdigest().encode()).hex() + "\n")
    print(out_dir / "index.txt")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    key_parser = commands.add_parser("pubkey")
    key_parser.add_argument("key")
    pack_parser = commands.add_parser("pack")
    pack_parser.add_argument("--version", required=True)
    pack_parser.add_argument("--compiler", required=True)
    pack_parser.add_argument("--key", required=True)
    pack_parser.add_argument("--out", required=True)
    pack_parser.add_argument("--std-dir", default="std")
    pack_parser.add_argument("--std-api")
    pack_parser.add_argument("--abi")
    pack_parser.add_argument("--runtime-api")
    index_parser = commands.add_parser("index")
    index_parser.add_argument("--serial", type=int, required=True)
    index_parser.add_argument("--key", required=True)
    index_parser.add_argument("--out", required=True)
    index_parser.add_argument("--yank", action="append")
    index_parser.add_argument("bundles", nargs="+")
    args = parser.parse_args()
    if args.command == "pubkey":
        print(pubkey(args.key))
    elif args.command == "pack":
        pack(args)
    else:
        index(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
