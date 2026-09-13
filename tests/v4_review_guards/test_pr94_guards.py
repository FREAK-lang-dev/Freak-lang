"""Pure-Python regression tests; importing the harness does not run a compiler."""
import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from freakc import auditor

HARNESS = ROOT / "src/compiler/v4/check_v4.py"
FIXTURE = ROOT / "src/compiler/v4/tests/hir_snapshot_scaling_smoke.fk"
SPEC = importlib.util.spec_from_file_location("pr94_guard_harness", HARNESS)
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class TaskReturnGuards(unittest.TestCase):
    def test_call_graph_cycles_and_unknown_roots(self):
        source = "task a() { b() }\ntask b() { c() }\ntask c() { a() }\ntask d() {}"
        with patch.object(guard, "freak_task_names", wraps=guard.freak_task_names) as names:
            self.assertEqual(guard.freak_task_call_closure(source, {"a", "unknown"}), {"a", "b", "c"})
            self.assertEqual(names.call_count, 1)

    def test_explicit_analysis_discovers_names_once(self):
        source = guard.read_text(guard.crate_path("freak_ty"))
        with patch.object(guard, "freak_task_names", wraps=guard.freak_task_names) as names:
            self.assertEqual(guard.task_return_explicit_call_closure_violations(source), [])
            self.assertEqual(names.call_count, 1)

    def test_commented_adapter_still_mutates_and_rejects_fallback(self):
        original_read = guard.read_text
        ty_path = guard.crate_path("freak_ty")
        source = original_read(ty_path)
        body = guard.freak_task_body(source, "v4_ty_ordinary_task_explicit_return_from_hir")
        # Locate in masked source, then introduce a harmless real line comment.
        commented = guard.freak_mask_line_comments(source).replace(
            body, "\n    -- comment must not disable the mutation probe\n" + body, 1,
        )
        self.assertNotEqual(commented, source)
        with patch.object(guard, "read_text", side_effect=lambda p: commented if p == ty_path else original_read(p)):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                guard.check_task_return_hir_boundary()
        self.assertIn("helper-indirected fallback rejected", output.getvalue())

    def scaling_errors(self, fixture_source=None, harness_source=None):
        read = Path.read_text
        def selected(path, *args, **kwargs):
            if path == FIXTURE and fixture_source is not None:
                return fixture_source
            if path == HARNESS and harness_source is not None:
                return harness_source
            return read(path, *args, **kwargs)
        with patch.object(Path, "read_text", selected):
            return auditor._task_return_scaling_errors(FIXTURE, HARNESS)

    def test_live_scaling_contract(self):
        self.assertEqual(self.scaling_errors(), [])

    def test_removed_probe_is_rejected_with_harness_markers_unchanged(self):
        source = FIXTURE.read_text(encoding="utf-8").replace('say "hir-scaling-return-missing-all="', 'say "removed-probe="')
        self.assertTrue(any("missing return scaling probe" in e for e in self.scaling_errors(fixture_source=source)))

    def test_removed_probe_invocation_is_rejected(self):
        source = FIXTURE.read_text(encoding="utf-8").replace("    v4_hir_scaling_return_checks(before)", "")
        self.assertTrue(self.scaling_errors(fixture_source=source))

    def test_manifest_entry_is_required(self):
        source = HARNESS.read_text(encoding="utf-8").replace('"fixture": "hir_snapshot_scaling_smoke.fk"', '"fixture": "different_fixture.fk"')
        self.assertTrue(any("missing hir_snapshot_scaling_smoke.fk" in e for e in self.scaling_errors(harness_source=source)))

    def test_manifest_oracle_is_required_even_with_marker_elsewhere(self):
        source = HARNESS.read_text(encoding="utf-8").replace('"hir-scaling-return-missing-all=true",', '', 1)
        source += '\n# "hir-scaling-return-missing-all=true"\n'
        self.assertTrue(any("missing hir-scaling-return-missing-all=true" in e for e in self.scaling_errors(harness_source=source)))


if __name__ == "__main__":
    unittest.main()
