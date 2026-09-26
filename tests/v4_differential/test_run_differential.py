"""Compiler-free input-identity regressions with bounded-adapter test doubles."""

from contextlib import nullcontext, redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import run_differential as runner


SOURCE = '-- Unicode: 雪 ☃ "quote" \\ \t\x00\x01\r\ntask main() {}\r\n'.encode("utf-8")
REJECTED_SOURCE = b"not valid source\r\n"
LIMITS = {"timeout_seconds": 17, "memory_limit_mb": 133, "output_limit_mb": 2}


def probe_payload(data: bytes) -> dict[str, object]:
    accepted = b"task main() {}" in data
    return {
        "schema": runner.V4_PROBE_SCHEMA,
        "adapter": "embedded-v4-frontend-through-ty",
        "accepted": accepted,
        "diagnostic_class": "none" if accepted else "syntax",
        "phase_summary": (
            "V4_PHASE|tokens=6|lex-diags=0|parse-nodes=2|parse-diags=0|"
            "hir-items=1|hir-diags=0|symbols=1|resolve-diags=0|"
            "signatures=1|ty-diags=0"
        ),
        "deterministic": True,
        "source_sha256": hashlib.sha256(data).hexdigest(),
        "source_bytes": len(data),
        "source_checksum": runner.stable_word_checksum(data),
        "native_program_executed": False,
        "peak_memory_bytes": 1,
    }


class InputIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        # A regression must never escape the fake adapters into a real compiler.
        for name in ("run", "Popen"):
            guard = patch.object(subprocess, name, side_effect=AssertionError("unexpected process"))
            guard.start()
            self.addCleanup(guard.stop)
        temporary = tempfile.TemporaryDirectory(prefix="freak-differential-unit-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.original = self.root / "original.fk"
        self.original.write_bytes(SOURCE)
        self.freak = self.root / "fake-freak"
        self.freak.touch()
        self.calls: list[dict[str, object]] = []
        self.cases = [self.case("case-one", self.original)]

    @staticmethod
    def case(case_id: str, source: Path) -> dict[str, object]:
        return {
            "id": case_id,
            "source": source.name,
            "source_path": source,
            "fixture_category": "compatible",
            "relationship": "equal",
            "intentional_difference_reason": "",
            "expect": {
                "v3": {"accepted": True, "diagnostic_class": "none"},
                "v4": {"accepted": True, "diagnostic_class": "none"},
            },
        }

    def run_campaign(self, after_read=None, before_frontends=None, case_filters=()):
        def fake_bounded(command, **kwargs):
            frontend = "v3" if command[1] == "check" else "v4"
            source_path = Path(command[-1] if frontend == "v3" else command[command.index("--source") + 1])
            data = source_path.read_bytes()
            self.assertNotIn(source_path, [case["source_path"] for case in self.cases])
            self.assertFalse(source_path.stat().st_mode & stat.S_IWUSR)
            payload = probe_payload(data)
            call = {"frontend": frontend, "path": source_path, "data": data,
                    "command": command, "limits": kwargs, "payload": payload}
            self.calls.append(call)
            if after_read is not None:
                after_read(call)
            if frontend == "v3":
                output = "  OK  Lexing (0ms)\n  OK  Parsing (1ms)\n"
                if payload["accepted"]:
                    output += "  OK  Type checking (2ms)\n  * PASSED -- no type errors found\n"
                else:
                    output += "  X FAILED -- syntax errors found\n"
                code = 0 if payload["accepted"] else 1
            else:
                output = json.dumps(payload) + "\n"
                code = 0
            return runner.BoundedResult(tuple(command), code, output, "", 1)

        def fake_distribution(freak, install):
            if before_frontends is not None:
                before_frontends(install.parent)
            return freak

        argv = [str(runner.HERE / "run_differential.py"), str(self.freak),
                "--timeout", "17", "--memory-limit-mb", "133", "--output-limit-mb", "2"]
        for case_id in case_filters:
            argv.extend(["--case", case_id])
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", argv), \
             patch.object(runner, "load_manifest", return_value={"cases": self.cases}), \
             patch.object(runner, "copy_adjacent_distribution", side_effect=fake_distribution), \
             patch.object(runner, "v4_host_mutex", side_effect=lambda **kwargs: nullcontext()), \
             patch.object(runner, "run_bounded", side_effect=fake_bounded), \
             redirect_stdout(stdout), redirect_stderr(stderr):
            code = runner.main()
        for call in self.calls:
            self.assertFalse(call["path"].exists(), "temporary snapshot was not cleaned up")
        return code, stdout.getvalue(), stderr.getvalue()

    @staticmethod
    def tamper(path: Path, *, delete: bool = False) -> None:
        # Read-only snapshots prevent accidental writes; deliberately bypass
        # that guard to test the independent byte-identity checks.
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
        if delete:
            path.unlink()
        else:
            path.write_bytes(REJECTED_SOURCE)

    def assert_harness_error(self, result) -> None:
        code, stdout, stderr = result
        self.assertEqual(code, 2, (stdout, stderr))
        self.assertNotIn("PASS", stdout)
        self.assertNotIn("MISMATCH", stdout)
        self.assertNotIn("compile-phase summary", stdout)
        self.assertIn("differential harness failed:", stderr)

    def test_original_is_read_once_and_all_observations_share_exact_bytes(self) -> None:
        reads = []
        read_bytes = Path.read_bytes

        def counted_read(path):
            if path == self.original:
                reads.append(path)
            return read_bytes(path)

        with patch.object(Path, "read_bytes", counted_read):
            code, stdout, stderr = self.run_campaign()
        self.assertEqual(code, 0, stderr)
        self.assertEqual(reads, [self.original])
        self.assertEqual([call["frontend"] for call in self.calls], ["v3", "v3", "v4"])
        self.assertEqual([call["data"] for call in self.calls], [SOURCE] * 3)
        self.assertEqual(len({call["path"] for call in self.calls}), 1)
        self.assertIn(f"source-sha256={hashlib.sha256(SOURCE).hexdigest()}", stdout)
        self.assertIn(f"source-bytes={len(SOURCE)}", stdout)
        self.assertIn("source=original.fk", stdout)
        for call in self.calls:
            expected = {**LIMITS, "timeout_seconds": 81 if call["frontend"] == "v4" else 17}
            self.assertEqual({key: call["limits"][key] for key in expected}, expected)
        command = self.calls[-1]["command"]
        for flag, value in (("--timeout", "17"), ("--memory-limit-mb", "133"), ("--output-limit-mb", "2")):
            self.assertEqual(command[command.index(flag) + 1], value)

    def test_editing_original_between_frontends_cannot_create_false_mismatch(self) -> None:
        def edit_original(call):
            if len(self.calls) == 2:
                self.original.write_bytes(REJECTED_SOURCE)

        code, stdout, stderr = self.run_campaign(edit_original)
        self.assertEqual(code, 0, stderr)
        self.assertIn("PASS case-one", stdout)
        self.assertEqual([call["data"] for call in self.calls], [SOURCE] * 3)
        self.assertIn(f"source-sha256={hashlib.sha256(SOURCE).hexdigest()}", stdout)

    def test_deleting_original_between_frontends_does_not_change_identity(self) -> None:
        def delete_original(call):
            if len(self.calls) == 2:
                self.original.unlink()

        code, stdout, stderr = self.run_campaign(delete_original)
        self.assertEqual(code, 0, stderr)
        self.assertIn("PASS case-one", stdout)
        self.assertEqual([call["data"] for call in self.calls], [SOURCE] * 3)
        self.assertIn(f"source-sha256={hashlib.sha256(SOURCE).hexdigest()}", stdout)

    def test_original_edit_cannot_fake_an_expected_frontend_difference(self) -> None:
        case = self.cases[0]
        case["fixture_category"] = "intentional_divergence"
        case["relationship"] = "intentional_divergence"
        case["intentional_difference_reason"] = "Test a supposed V4 rejection."
        case["expect"]["v4"] = {"accepted": False, "diagnostic_class": "syntax"}

        def edit_original(call):
            if len(self.calls) == 2:
                self.original.write_bytes(REJECTED_SOURCE)

        code, stdout, stderr = self.run_campaign(edit_original)
        self.assertEqual(code, 1, stderr)
        self.assertIn("MISMATCH case-one", stdout)
        self.assertIn("v4=accept/none", stdout)

    def test_all_selected_cases_are_captured_before_first_frontend(self) -> None:
        second = self.root / "second.fk"
        second.write_bytes(SOURCE + b"-- second\r\n")
        self.cases.append(self.case("case-two", second))

        def delete_later_original(call):
            if len(self.calls) == 1:
                second.unlink()

        code, stdout, stderr = self.run_campaign(delete_later_original)
        self.assertEqual(code, 0, stderr)
        self.assertEqual([call["data"] for call in self.calls[3:]], [SOURCE + b"-- second\r\n"] * 3)
        self.assertIn("cases=2 passed=2 mismatches=0", stdout)

    def test_unselected_sources_are_not_read(self) -> None:
        self.cases.append(self.case("unselected", self.root / "missing.fk"))
        code, stdout, stderr = self.run_campaign(case_filters=("case-one",))
        self.assertEqual(code, 0, stderr)
        self.assertIn("cases=1 passed=1 mismatches=0", stdout)

    def test_snapshot_tamper_before_first_frontend_is_a_harness_error(self) -> None:
        def tamper_before(root):
            self.tamper(root / "cases/000-case-one/source/input.fk")

        self.assert_harness_error(self.run_campaign(before_frontends=tamper_before))
        self.assertEqual(self.calls, [])

    def test_snapshot_edits_and_deletions_after_each_adapter_fail_closed(self) -> None:
        for target_call in (1, 2, 3):
            for delete in (False, True):
                with self.subTest(target_call=target_call, delete=delete):
                    self.calls = []

                    def tamper_after(call):
                        if len(self.calls) == target_call:
                            self.tamper(call["path"], delete=delete)

                    result = self.run_campaign(tamper_after)
                    self.assert_harness_error(result)
                    self.assertIn("source snapshot", result[2])
                    self.assertEqual(len(self.calls), target_call)

    def test_forged_v4_identity_cannot_follow_a_changed_original(self) -> None:
        for field in ("source_sha256", "source_bytes", "source_checksum"):
            with self.subTest(field=field):
                self.calls = []
                self.original.write_bytes(SOURCE)

                def forge_payload(call):
                    if call["frontend"] == "v4":
                        self.original.write_bytes(REJECTED_SOURCE)
                        call["payload"][field] = probe_payload(REJECTED_SOURCE)[field]

                result = self.run_campaign(forge_payload)
                self.assert_harness_error(result)
                self.assertIn("does not match the requested fixture", result[2])

    def test_forged_v4_digest_of_tampered_snapshot_is_not_accepted(self) -> None:
        def forge_payload(call):
            if call["frontend"] == "v4":
                self.tamper(call["path"])
                call["payload"].update(probe_payload(REJECTED_SOURCE))

        result = self.run_campaign(forge_payload)
        self.assert_harness_error(result)
        self.assertIn("source snapshot was changed", result[2])

    def test_snapshot_replaced_with_directory_fails_closed(self) -> None:
        def replace_snapshot(call):
            self.tamper(call["path"], delete=True)
            call["path"].mkdir()

        result = self.run_campaign(replace_snapshot)
        self.assert_harness_error(result)
        self.assertIn("source snapshot was changed", result[2])
        self.assertEqual(len(self.calls), 1)

    def test_snapshot_size_change_is_rejected_before_reading_contents(self) -> None:
        snapshot = runner.SourceSnapshot.capture(self.original, self.root / "snapshot")
        self.tamper(snapshot.path)
        with patch.object(Path, "open", side_effect=AssertionError("unexpected content read")):
            with self.assertRaisesRegex(RuntimeError, "source snapshot was changed"):
                snapshot.verify()

    def test_payload_validation_uses_captured_bytes_not_snapshot_file(self) -> None:
        snapshot = runner.SourceSnapshot.capture(self.original, self.root / "snapshot")
        self.tamper(snapshot.path)
        runner._validate_v4_probe_payload(probe_payload(SOURCE), snapshot.data)
        with self.assertRaisesRegex(RuntimeError, "digest does not match"):
            runner._validate_v4_probe_payload(probe_payload(REJECTED_SOURCE), snapshot.data)


if __name__ == "__main__":
    unittest.main()
