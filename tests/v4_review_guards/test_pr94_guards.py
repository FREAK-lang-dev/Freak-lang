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

    def test_commented_probe_is_rejected(self):
        source = FIXTURE.read_text(encoding="utf-8").replace('say "hir-scaling-return-missing-all="', '-- say "hir-scaling-return-missing-all="')
        self.assertTrue(self.scaling_errors(fixture_source=source))

    def test_commented_invocation_is_rejected(self):
        source = FIXTURE.read_text(encoding="utf-8").replace("    v4_hir_scaling_return_checks(before)", "    -- v4_hir_scaling_return_checks(before)")
        self.assertTrue(self.scaling_errors(fixture_source=source))

    def test_word_literal_cannot_replace_invocation(self):
        source = FIXTURE.read_text(encoding="utf-8").replace("    v4_hir_scaling_return_checks(before)", '    say "    v4_hir_scaling_return_checks(before)"')
        self.assertTrue(self.scaling_errors(fixture_source=source))

    def test_manifest_oracle_is_required_even_with_marker_elsewhere(self):
        source = HARNESS.read_text(encoding="utf-8").replace('"hir-scaling-return-missing-all=true",', '', 1)
        source += '\n# "hir-scaling-return-missing-all=true"\n'
        self.assertTrue(any("missing hir-scaling-return-missing-all=true" in e for e in self.scaling_errors(harness_source=source)))


class IndexedLookupGuards(unittest.TestCase):
    def test_live_snapshot_inventory_includes_index_resource_limit(self):
        with contextlib.redirect_stdout(io.StringIO()):
            guard.check_snapshot_inventories()

    def test_index_resource_limit_removal_is_rejected(self):
        fixtures = guard.C_ARRAY_HANDLE_RESOURCE_FIXTURES - {"hir_semantic_index_smoke.fk"}
        with patch.object(guard, "C_ARRAY_HANDLE_RESOURCE_FIXTURES", fixtures):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                with self.assertRaises(SystemExit):
                    guard.check_snapshot_inventories()
        self.assertIn("scratch-handle resource smoke limit coverage drifted", output.getvalue())

    def setUp(self):
        self.source = guard.read_text(guard.crate_path("freak_hir"))

    def changed_body(self, task, transform):
        source = guard.freak_mask_line_comments(self.source)
        body = guard.freak_task_body(source, task)
        self.assertIsNotNone(body)
        return source.replace(body, transform(body), 1)

    def test_live_indexed_contract(self):
        self.assertEqual(guard.hir_lookup_index_violations(self.source), [])

    def test_harmless_comments_and_literals_are_ignored(self):
        source = self.changed_body("v4_hir_local_annotation_count", lambda body:
            '\n-- repeat until x > 20 { v4_hir_finalize_lookup_indexes(0) }\n'
            'say "v4_hir_finalize_lookup_indexes(0) repeat"\n' + body)
        self.assertEqual(guard.hir_lookup_index_violations(source), [])

    def test_helper_indirected_lazy_rebuild_is_rejected(self):
        source = self.changed_body("v4_hir_local_annotation_count", lambda body: "\nlookup_helper(hir_id)\n" + body)
        source += "\ntask lookup_helper(hir_id: int) { v4_hir_finalize_lookup_indexes(hir_id) }\n"
        self.assertTrue(any("forbidden work" in e for e in guard.hir_lookup_index_violations(source)))

    def test_helper_indirected_global_scan_is_rejected(self):
        source = self.changed_body("v4_hir_task_return_record_id", lambda body: "\nscan_helper(hir_id)\n" + body)
        source += "\ntask scan_helper(hir_id: int) { pilot x = 0; repeat until x >= v4_hir_task_return_record_count(hir_id) { x += 1 } }\n"
        self.assertTrue(any("record rescan" in e for e in guard.hir_lookup_index_violations(source)))

    def test_helper_indirected_syntax_access_is_rejected(self):
        source = self.changed_body("v4_hir_local_annotation_type", lambda body: "\nsyntax_helper()\n" + body)
        source += "\ntask syntax_helper() { give back v4_parse_token_span(0, 0) }\n"
        self.assertTrue(any("forbidden work" in e for e in guard.hir_lookup_index_violations(source)))

    def test_recursive_scan_is_rejected(self):
        source = self.changed_body("v4_hir_local_annotation_count", lambda body: "\nrecursive_scan()\n" + body)
        source += "\ntask recursive_scan() { recursive_scan() }\n"
        self.assertTrue(any("recursive work" in e for e in guard.hir_lookup_index_violations(source)))

    def test_commented_exact_start_cannot_satisfy_contract(self):
        source = self.changed_body("v4_hir_local_annotation_at_offset", lambda body:
            body.replace("owner == item_id and start == offset", "owner == item_id") +
            "\n-- owner == item_id and start == offset\n")
        self.assertTrue(any("exact-start" in e for e in guard.hir_lookup_index_violations(source)))

    def test_literal_exact_start_cannot_satisfy_contract(self):
        source = self.changed_body("v4_hir_local_annotation_at_offset", lambda body:
            body.replace("owner == item_id and start == offset", "owner == item_id") +
            '\nsay "owner == item_id and start == offset"\n')
        self.assertTrue(any("exact-start" in e for e in guard.hir_lookup_index_violations(source)))

    def test_commented_finalize_cannot_satisfy_contract(self):
        source = self.changed_body("v4_hir_lower_expanded", lambda body:
            body.replace("v4_hir_finalize_lookup_indexes(hir_id)", "removed_finalizer(hir_id)") +
            "\n-- v4_hir_finalize_lookup_indexes(hir_id)\n")
        self.assertNotEqual(source, self.source)
        self.assertTrue(any("explicitly finalize" in e for e in guard.hir_lookup_index_violations(source)))

    def test_missing_helper_and_lexical_error_fail_closed(self):
        source = self.changed_body("v4_hir_local_annotation_count", lambda body: "\nv4_hir_missing_helper()\n" + body)
        self.assertTrue(any("helper missing" in e for e in guard.hir_lookup_index_violations(source)))
        source = self.changed_body("v4_hir_local_annotation_count", lambda body: "\n`\n" + body)
        self.assertTrue(guard.hir_lookup_index_violations(source))

    def test_ignored_finalization_failure_is_rejected(self):
        source = self.changed_body("v4_hir_lower_expanded", lambda body:
            body.replace("v4_hir_file_len = hir_id\n        give back 0 - 1", "say 0"))
        self.assertTrue(any("cannot continue" in e for e in guard.hir_lookup_index_violations(source)))

    def test_preflight_must_return_before_mutation(self):
        source = self.changed_body("v4_hir_lower_expanded", lambda body:
            body.replace("if v4_hir_lookup_handles_available(required) == false { give back 0 - 1 }",
                         "if v4_hir_lookup_handles_available(required) == false { say 0 }"))
        self.assertTrue(any("return on failed preflight" in e for e in guard.hir_lookup_index_violations(source)))
        source = self.changed_body("v4_hir_snapshot_restore", lambda body:
            body.replace("v4_hir_begin_snapshot_restore()", "") + "\nv4_hir_begin_snapshot_restore()\n")
        # Moving preflight behind the first mutation must also fail, even when
        # its spelling remains present elsewhere in the task.
        source = source.replace("pilot validation =", "v4_hir_begin_snapshot_restore()\n    pilot validation =", 1)
        self.assertTrue(any("preflight before live mutation" in e for e in guard.hir_lookup_index_violations(source)))


class LookupProbeAudit(unittest.TestCase):
    def setUp(self):
        self.fixture = FIXTURE.with_name("hir_semantic_index_smoke.fk")

    def errors(self, fixture_source=None, harness_source=None):
        read = Path.read_text
        def selected(path, *args, **kwargs):
            if path == self.fixture and fixture_source is not None:
                return fixture_source
            if path == HARNESS and harness_source is not None:
                return harness_source
            return read(path, *args, **kwargs)
        with patch.object(Path, "read_text", selected):
            return auditor._hir_semantic_index_errors(self.fixture, HARNESS)

    def test_live_probe_and_scaling_contract(self):
        self.assertEqual(self.errors(), [])
        self.assertEqual(auditor._hir_lookup_scaling_errors(FIXTURE, HARNESS), [])

    def test_removed_top_level_invocation_not_replaced_by_declaration(self):
        source = self.fixture.read_text(encoding="utf-8")
        source = source.replace("\nv4_hir_semantic_index_run()", "\n-- v4_hir_semantic_index_run()")
        self.assertTrue(any("missing active" in e for e in self.errors(fixture_source=source)))

    def test_commented_probe_or_literal_invocation_is_rejected(self):
        source = self.fixture.read_text(encoding="utf-8")
        self.assertTrue(self.errors(fixture_source=source.replace('say "hir-index-logarithmic-probes="', '-- say "hir-index-logarithmic-probes="')))
        self.assertTrue(self.errors(fixture_source=source.replace("\nv4_hir_semantic_index_run()", '\nsay "v4_hir_semantic_index_run()"')))

    def test_removed_manifest_and_oracle_are_rejected(self):
        source = HARNESS.read_text(encoding="utf-8")
        self.assertTrue(self.errors(harness_source=source.replace('"fixture": "hir_semantic_index_smoke.fk"', '"fixture": "missing.fk"')))
        self.assertTrue(self.errors(harness_source=source.replace('"hir-index-logarithmic-probes=true",', '') + '\n# "hir-index-logarithmic-probes=true"'))

    def test_resource_workload_cannot_be_weakened(self):
        source = self.fixture.read_text(encoding="utf-8")
        for old, new in (("v4_hir_index_payload(1, 1, 512)", "v4_hir_index_payload(1, 1, 8)"),
                         ("build_steps <= 512 * 9 * 3", "build_steps <= 512 * 9 * 30"),
                         ("iteration >= 32", "iteration >= 2")):
            self.assertTrue(self.errors(fixture_source=source.replace(old, new)), old)


if __name__ == "__main__":
    unittest.main()
