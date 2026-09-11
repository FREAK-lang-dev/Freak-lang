"""Unit tests for the fast contributor gate; no compiler or child process is run."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_gate():
    spec = importlib.util.spec_from_file_location(
        "check_contributor_under_test", REPO_ROOT / "tools" / "check_contributor.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gate = _load_gate()


class ContributorGateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="freak-contributor-gate-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        root_guard = patch.object(gate, "ROOT", self.root)
        root_guard.start()
        self.addCleanup(root_guard.stop)

    def write(self, relative: str, content: str = "") -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_syntax_check_accepts_valid_python_and_reports_every_failure(self):
        valid_dir = self.root / "valid"
        self.write("valid/ok.py", "answer = 42\n")
        invalid = self.write("valid/broken.py", "def broken(:\n")
        missing_dir = self.root / "missing"

        errors: list[str] = []
        with patch.object(gate, "SYNTAX_DIRS", (valid_dir, missing_dir)):
            gate.check_syntax(errors)

        self.assertEqual(len(errors), 2, errors)
        self.assertTrue(any("python syntax:" in error and str(invalid) in error for error in errors))
        self.assertIn("missing source dir: missing", errors)

    def test_required_files_rejects_missing_paths_and_directories(self):
        self.write("present.md", "ready\n")
        (self.root / "directory.md").mkdir()

        errors: list[str] = []
        with patch.object(
            gate, "REQUIRED_FILES", ("present.md", "missing.md", "directory.md")
        ):
            gate.check_required_files(errors)

        self.assertEqual(
            errors,
            [
                "missing required file: missing.md",
                "missing required file: directory.md",
            ],
        )

    def test_content_markers_report_each_missing_marker_but_skip_missing_files(self):
        self.write("README.md", "actively hardened, not stable\n")
        self.write("CONTRIBUTING.md", "See .github/labels.yml\n")

        errors: list[str] = []
        markers = (
            ("README.md", "actively hardened"),
            ("README.md", "not stable"),
            ("CONTRIBUTING.md", "tools/check_contributor.py"),
            ("already-reported-missing.md", "irrelevant"),
        )
        with patch.object(gate, "CONTENT_MARKERS", markers):
            gate.check_content_markers(errors)

        self.assertEqual(
            errors,
            ["CONTRIBUTING.md is missing marker: 'tools/check_contributor.py'"],
        )

    def test_main_runs_all_checks_and_prints_pass_for_valid_fixture(self):
        syntax_dir = self.root / "sources"
        self.write("sources/valid.py", "value = 'ok'\n")
        self.write("README.md", "actively hardened and not stable\n")
        self.write("CONTRIBUTING.md", "labels live in .github/labels.yml\n")

        output = io.StringIO()
        with (
            patch.object(gate, "SYNTAX_DIRS", (syntax_dir,)),
            patch.object(gate, "REQUIRED_FILES", ("README.md", "CONTRIBUTING.md")),
            patch.object(
                gate,
                "CONTENT_MARKERS",
                (
                    ("README.md", "actively hardened"),
                    ("README.md", "not stable"),
                    ("CONTRIBUTING.md", ".github/labels.yml"),
                ),
            ),
            contextlib.redirect_stdout(output),
        ):
            result = gate.main()

        self.assertEqual(result, 0)
        self.assertEqual(output.getvalue(), "check_contributor: PASS\n")

    def test_main_aggregates_failures_and_returns_nonzero(self):
        def syntax_failure(errors: list[str]) -> None:
            errors.append("syntax failed")

        def required_failure(errors: list[str]) -> None:
            errors.append("required file failed")

        def marker_failure(errors: list[str]) -> None:
            errors.append("marker failed")

        output = io.StringIO()
        with (
            patch.object(gate, "check_syntax", side_effect=syntax_failure),
            patch.object(gate, "check_required_files", side_effect=required_failure),
            patch.object(gate, "check_content_markers", side_effect=marker_failure),
            contextlib.redirect_stdout(output),
        ):
            result = gate.main()

        self.assertEqual(result, 1)
        self.assertEqual(
            output.getvalue().splitlines(),
            [
                "check_contributor: FAIL",
                "  - syntax failed",
                "  - required file failed",
                "  - marker failed",
            ],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
