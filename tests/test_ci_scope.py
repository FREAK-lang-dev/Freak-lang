"""Pin the fail-closed V3 lane scope used by ci.yml on pull requests."""

from __future__ import annotations

import ast
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import ci_scope  # noqa: E402


class CiScope(unittest.TestCase):
    def test_push_always_runs_v3(self) -> None:
        self.assertTrue(ci_scope.needs_v3("push", ["src/compiler/v4/crates/a.fk"])[0])
        self.assertTrue(ci_scope.needs_v3("push", None)[0])

    def test_v4_only_pull_request_skips_v3(self) -> None:
        files = [
            "src/compiler/v4/crates/freak_mir/src/lib.fk",
            "src/compiler/v4/tests/mir_smoke.fk",
            "src/compiler/v4/examples/hello.fk",
            "src/compiler/v4/check_v4.py",
            "src/compiler/v4/RELEASE_CHECKLIST.md",
            "tests/v4_safety/cases/move.fk",
            "tests/v4_owned_word_codegen.py",
            "tests/test_v4_word_bounds_codegen.py",
            "benchmarks/v4/sibling_loop_scaling.md",
            "freak-full-bible.md",
            "freak-conformance-audit.md",
            ".github/workflows/v4-ci.yml",
        ]
        v3, reason = ci_scope.needs_v3("pull_request", files)
        self.assertFalse(v3, reason)

    def test_shared_paths_keep_v3(self) -> None:
        for path in [
            "src/compiler/v3/parser.fk",
            "src/compiler/v4/tools/preview_protocol.fk",
            "src/compiler/v4/native-runtime.manifest",
            "src/compiler/v4/bootstrap.lock",
            "src/compiler/v4/v35_seed.py",
            "freakc/runtime/freak_runtime.c",
            "std/json.fk",
            "tools/ci_scope.py",
            "tests/v3_v4_bootstrap_ci.py",
            ".github/workflows/ci.yml",
            "README.md",
            "VERSION",
            "src/compiler/v4/../v3/main.fk",
        ]:
            with self.subTest(path=path):
                self.assertTrue(ci_scope.needs_v3("pull_request", ["src/compiler/v4/check_v4.py", path])[0])

    def test_unknown_or_truncated_lists_keep_v3(self) -> None:
        self.assertTrue(ci_scope.needs_v3("pull_request", None)[0])
        self.assertTrue(ci_scope.needs_v3("pull_request", [])[0])
        many = ["src/compiler/v4/tests/x%d.fk" % i for i in range(ci_scope.FILE_LIST_LIMIT)]
        self.assertTrue(ci_scope.needs_v3("pull_request", many)[0])

    def test_main_writes_github_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            files = Path(tmp) / "files.txt"
            files.write_text("src/compiler/v4/crates/a.fk\n", encoding="utf-8")
            output = Path(tmp) / "out.txt"
            import os

            old = os.environ.get("GITHUB_OUTPUT")
            os.environ["GITHUB_OUTPUT"] = str(output)
            try:
                ci_scope.main(["--event", "pull_request", "--files", str(files)])
                ci_scope.main(["--event", "pull_request", "--files", str(Path(tmp) / "missing.txt")])
            finally:
                if old is None:
                    del os.environ["GITHUB_OUTPUT"]
                else:
                    os.environ["GITHUB_OUTPUT"] = old
            self.assertEqual(output.read_text(encoding="utf-8"), "v3=false\nv3=true\n")

    def test_v3_lanes_never_read_v4_only_paths(self) -> None:
        """Every script ci.yml runs, and the local modules it imports, stays
        clear of the V4-only paths (only the shared manifest is allowed)."""
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        seeds = set(re.findall(r"(?:tests|tools)/[A-Za-z0-9_/]*\.py", workflow))
        self.assertTrue(seeds)
        self.assertNotIn("audit-conformance", workflow)
        for source in (ROOT / "packaging/cli-sources.manifest").read_text(encoding="utf-8").splitlines():
            with self.subTest(cli_source=source):
                self.assertFalse(ci_scope.is_v4_only(source))
        seen: set[Path] = set()
        todo = [ROOT / seed for seed in seeds]
        bases = [ROOT, ROOT / "tests", ROOT / "tools"]
        while todo:
            path = todo.pop()
            if path in seen or not path.exists():
                continue
            seen.add(path)
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                modules: list[str] = []
                if isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    modules = [node.module] + [f"{node.module}.{alias.name}" for alias in node.names]
                for module in modules:
                    for base in [path.parent, *bases]:
                        stem = base / module.replace(".", "/")
                        for candidate in (stem.with_suffix(".py"), stem / "__init__.py"):
                            if candidate.exists():
                                todo.append(candidate)
        for path in sorted(seen):
            relative = path.relative_to(ROOT).as_posix()
            with self.subTest(script=relative):
                self.assertFalse(ci_scope.is_v4_only(relative), "ci.yml runs a V4-only file")
        forbidden = re.compile(
            r"compiler/v4/(crates|tests|examples|check_v4|build_v4|build_lsp|self_host)"
            r"|tests/v4_|benchmarks/v4|v4_scale_bench"
        )
        # freakc/auditor.py reads check_v4.py for audit-conformance, which
        # ci.yml never runs; the V4 lanes own that command. ci_scope.py only
        # names the V4-only paths.
        allowed = {"freakc/auditor.py", "tools/ci_scope.py"}
        for path in sorted(seen):
            relative = path.relative_to(ROOT).as_posix()
            if relative in allowed:
                continue
            with self.subTest(reader=relative):
                self.assertIsNone(forbidden.search(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
