#!/usr/bin/env python3
"""Source/model checks for bounded checked-ticket marker reads; no subprocesses.

The checked-byte reader and retained hex decoder are exercised separately by
v3_std_capability.py using a freshly built CLI, including its 4096/4097-byte
payload and all-byte rejection cases. The historical framing models below
remain decoder controls; they do not substitute for that native/platform gate.
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
    def test_source_anchors_bounded_reader_and_releases_tickets(self) -> None:
        source = (REPO / "src/cli/build.fk").read_text(encoding="utf-8")
        reader = source[source.index("task cli_payload_std_api_value("):
                        source.index("task cli_payload_std_api_ok(")]
        fragments = (
            "pilot info = fs::stat_checked(marker)",
            "pilot kind = fs::result_kind(info)",
            "pilot size = fs::result_size(info)",
            "fs::result_release(info)",
            'if kind != 1 { give back "unreadable" }',
            'if size > 4096 { give back "oversized-marker" }',
            "pilot directory = fs::open_dir_ticket(std_dir)",
            'pilot read = fs::read_relative_bytes_limit_ticket(directory, "freak_std_api", 4096)',
            "fs::result_release(directory)",
            "if not fs::result_ok(read)",
            "pilot bytes: ByteBuffer = fs::result_bytes(read)",
            "fs::result_release(read)",
            "give back cli_std_marker_bytes_value(bytes)",
        )
        position = 0
        for fragment in fragments:
            found = reader.find(fragment, position)
            self.assertGreaterEqual(found, position, fragment)
            position = found + len(fragment)
        for ticket in ("info", "directory", "read"):
            self.assertEqual(reader.count(f"fs::result_release({ticket})"), 2,
                             f"{ticket} needs both failure and success release paths")
        self.assertNotIn("pilot command =", reader)
        self.assertNotIn("fs::read(", reader)
        self.assertNotIn("fs::read_bytes(", reader)

    def test_checked_bytes_validate_before_conversion_and_release(self) -> None:
        source = (REPO / "src/cli/build.fk").read_text(encoding="utf-8")
        classifier = source[source.index("task cli_std_marker_bytes_value("):
                            source.index("task cli_payload_std_api_value(")]
        self.assertIn("if bytes.length() == 0", classifier)
        self.assertIn("else if bytes.length() > 4096", classifier)
        self.assertIn("bytes.seek(0)", classifier)
        self.assertIn("pilot value = bytes.read_byte()", classifier)
        self.assertIn("(value < 32 and value != 9 and value != 10 and value != 13) or value > 126", classifier)
        self.assertLess(classifier.index("if invalid {"),
                        classifier.index("contents = bytes.to_word().trim()"))
        self.assertIn('contents.contains("\\t") or contents.contains("\\r") or contents.contains("\\n")', classifier)
        self.assertEqual(classifier.count("bytes.release()"), 1)
        self.assertLess(classifier.index("bytes.release()"), classifier.index("give back contents"))

    def test_runtime_reader_enforces_regular_file_and_actual_allocation_limit(self) -> None:
        source = (REPO / "freakc/runtime/freak_v35_fs.inc").read_text(encoding="utf-8")
        reader = source[source.index("static int64_t freak_fs_read_descriptor("):
                        source.index("int64_t freak_fs_read_bytes_limit_ticket(")]
        self.assertIn("S_ISREG(metadata.st_mode)", reader)
        self.assertIn("(metadata.st_mode & _S_IFMT) == _S_IFREG", reader)
        self.assertIn("if (!regular || metadata.st_size < 0 || (uintmax_t)metadata.st_size > limit)", reader)
        self.assertLess(reader.index("if (!regular"), reader.index("freak_command_allocate(capacity,1)"))
        self.assertIn("if (capacity > limit+1) capacity=limit+1;", reader)
        self.assertIn("if (next > limit+1) next=limit+1;", reader)
        self.assertIn("if (length > limit) { complete=false; break; }", reader)
        self.assertIn("if (!freak_fs_close_write(descriptor)) complete=false;", reader)
        start = source.index("static int64_t freak_fs_read_relative_mode(")
        relative = source[start:source.index("#ifdef _WIN32\ntypedef LONG", start)]
        self.assertIn("freak_fs_anchor_parent(root,name,&leaf)", relative)
        self.assertIn("freak_fs_anchor_child(parent,leaf,false,false,false)", relative)
        self.assertIn("return freak_fs_read_descriptor(handle,descriptor,text,source,(size_t)limit);", relative)
        self.assertIn("return freak_fs_read_relative_mode(root,relative,limit,false,false);", relative)
        posix = source[source.index("#define FREAK_FS_INVALID_ANCHOR (-1)"):
                       source.index("static bool freak_fs_relative_valid(")]
        self.assertIn("O_CLOEXEC | O_NOFOLLOW | O_NONBLOCK", posix)
        self.assertIn("directory ? !S_ISDIR(info.st_mode) : !S_ISREG(info.st_mode)", posix)

    def test_retained_hex_decoder_keeps_original_bounds(self) -> None:
        source = (REPO / "src/cli/build.fk").read_text(encoding="utf-8")
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
