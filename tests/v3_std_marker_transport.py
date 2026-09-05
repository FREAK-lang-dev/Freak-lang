#!/usr/bin/env python3
"""Source/model checks for bounded POSIX od marker framing; no subprocesses.

The actual shell and C/LLVM decoder are exercised separately by
v3_std_capability.py using a freshly built CLI, including its 4096/4097-byte
payload and all-byte rejection cases. These checks do not substitute for that
native/platform gate.
"""
from __future__ import annotations

from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
PREFIX = b"FREAK_STD_HEX:"
SUFFIX = b":END"
C_SPACE = b" \t\n\r\v\f"


def modeled_transport(output: bytes, *, od_ok: bool = True, tr_ok: bool = True) -> bytes:
    """Model the source-guarded success chain, not the native shell itself."""
    if not od_ok or not tr_ok:
        return b""
    return PREFIX + output.translate(None, C_SPACE) + SUFFIX


def padded_hex(data: bytes) -> bytes:
    """Whitespace-heavy od-style fixture, deliberately beyond the old cap."""
    return b"".join(b"       " + b"".join(f"  {byte:02x} ".encode("ascii")
                                        for byte in data[start:start + 16]) + b"\n"
                    for start in range(0, len(data), 16))


class MarkerTransportChecks(unittest.TestCase):
    def test_source_keeps_success_chain_and_bounds(self) -> None:
        source = (REPO / "src/cli/build.fk").read_text(encoding="utf-8")
        reader = source[source.index("task cli_payload_std_api_value("):
                        source.index("task cli_payload_std_api_ok(")]
        command = next(line.strip() for line in reader.splitlines()
                       if line.strip().startswith("pilot command ="))
        expected = r'''pilot command = "if [ -f " + quoted + " ] && [ -r " + quoted + " ]; then bytes=$(LC_ALL=C od -An -v -tx1 -N 4097 2>/dev/null < " + quoted + ") && bytes=$(printf '%s' \"$bytes\" | LC_ALL=C tr -d '[:space:]') && printf 'FREAK_STD_HEX:%s:END' \"$bytes\"; fi"'''
        self.assertEqual(command, expected)
        decoder = source[source.index("task cli_std_marker_decode("):
                         source.index("task cli_payload_std_api_value(")]
        self.assertIn('if frame.length() > 16432', decoder)
        self.assertIn('if count > 4096', decoder)
        self.assertIn('not frame.ends_with(":END")', decoder)
        self.assertIn('if high >= 0 or invalid', decoder)

    def test_padded_inclusive_limit(self) -> None:
        token = b"freak-v3-std-api-1"
        data = token + b" " * (4096 - len(token))
        padded = padded_hex(data)
        self.assertGreater(len(PREFIX + padded + SUFFIX), 16432)
        framed = modeled_transport(padded)
        self.assertEqual(framed, PREFIX + data.hex().encode("ascii") + SUFFIX)
        self.assertEqual(len(framed), 8210)

    def test_over_limit_still_contains_4097_bytes(self) -> None:
        data = b"x" * 4097
        framed = modeled_transport(padded_hex(data))
        self.assertLess(len(framed), 16432)
        self.assertEqual(bytes.fromhex(framed[len(PREFIX):-len(SUFFIX)].decode("ascii")), data)
        # Canonicalization cannot truncate the sentinel byte that causes the
        # actual decoder's 4096-byte check to reject this otherwise-small frame.
        self.assertEqual(len(framed), 8212)

    def test_encoded_controls_survive_formatting_removal(self) -> None:
        data = bytes(range(256))
        spaced = b"\t\r\n\v\f".join(f"{byte:02x}".encode("ascii") for byte in data)
        framed = modeled_transport(spaced)
        self.assertEqual(framed, PREFIX + data.hex().encode("ascii") + SUFFIX)

    def test_failure_cannot_publish_partial_success_frame(self) -> None:
        partial = padded_hex(b"freak-v3-std-api-1")
        self.assertEqual(modeled_transport(partial, od_ok=False), b"")
        self.assertEqual(modeled_transport(partial, tr_ok=False), b"")

    def test_nonwhitespace_corruption_is_not_filtered(self) -> None:
        self.assertEqual(modeled_transport(b" 61 * GG ! "), PREFIX + b"61*GG!" + SUFFIX)
        self.assertEqual(modeled_transport(b""), PREFIX + SUFFIX)


if __name__ == "__main__":
    unittest.main()
