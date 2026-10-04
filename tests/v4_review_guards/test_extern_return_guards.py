"""Compiler-free regressions for stored extern-return dependency boundaries."""
import importlib.util
import contextlib
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from freakc import auditor

SPEC = importlib.util.spec_from_file_location("extern_return_guard", ROOT / "src/compiler/v4/check_v4.py")
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class ExternReturnGuards(unittest.TestCase):
    def setUp(self):
        """Load the candidate HIR/TY sources without running the compiler."""
        self.hir = guard.read_text(guard.crate_path("freak_hir"))
        self.ty = guard.read_text(guard.crate_path("freak_ty"))

    def violations(self, hir=None, ty=None):
        """Audit live sources or supplied mutations with the production guard."""
        return guard.extern_return_boundary_violations(
            self.hir if hir is None else hir, self.ty if ty is None else ty,
        )

    def replace_body(self, source, name, replacement):
        """Replace one verified task body after masking comment decoys."""
        source = guard.freak_mask_line_comments(source)
        body = guard.freak_task_body(source, name)
        self.assertIsNotNone(body, name)
        self.assertIn(body, source)
        return source.replace(body, replacement, 1)

    def inject(self, source, name, statement):
        """Prepend active code to one verified task for a negative probe."""
        source = guard.freak_mask_line_comments(source)
        body = guard.freak_task_body(source, name)
        self.assertIsNotNone(body, name)
        self.assertIn(body, source)
        return source.replace(body, "\n" + statement + "\n" + body, 1)

    def test_live_contract(self):
        """Require the current stored-return implementation to satisfy the guard."""
        self.assertEqual(self.violations(), [])

    def test_extern_separator_scanner_is_single_pass(self):
        """Reject the legacy remaining-line prescan before separator detection."""
        parser = guard.read_text(guard.crate_path("freak_parse"))
        body = guard.freak_task_body(guard.freak_mask_line_comments(parser), "v4_parse_extern_member_end_from_start")
        self.assertIsNotNone(body)
        self.assertNotIn("v4_parse_skip_item(", body)
        self.assertEqual(body.count("repeat until"), 1)
        self.assertEqual(body.count("idx += 1"), 1)
        self.assertIn("if type_depth == 0 and value == \";\" { give back idx }", body)
        self.assertIn("if saw_body and body_depth == 0 { give back idx + 1 }", body)

    def test_snapshot_exhaustion_has_bounded_native_handle_pool(self):
        """Reject loss of the existing bounded native exhaustion-test registry."""
        self.assertEqual(guard.C_ARRAY_HANDLE_RESOURCE_LIMIT, 1024)
        fixture = "extern_return_snapshot_smoke.fk"
        self.assertIn(fixture, guard.C_ARRAY_HANDLE_RESOURCE_FIXTURES)
        with patch.object(guard, "C_ARRAY_HANDLE_RESOURCE_FIXTURES", guard.C_ARRAY_HANDLE_RESOURCE_FIXTURES - {fixture}):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                with self.assertRaises(SystemExit):
                    guard.check_snapshot_inventories()
        self.assertIn("scratch-handle resource smoke limit coverage drifted", output.getvalue())

    def test_indirect_declared_type_reconstruction(self):
        """Find forbidden syntax reads even behind a newly introduced helper."""
        for forbidden in ("v4_lex_token_value", "v4_expand_file_stream", "v4_ty_type_text", "v4_ty_task_return_from_tokens"):
            with self.subTest(forbidden=forbidden):
                mutant = self.inject(self.ty, "v4_ty_extern_declared_return_surface_type", "hidden_extern_read()")
                mutant += "\ntask hidden_extern_read() -> void { " + forbidden + "(0, 0) }\n"
                self.assertTrue(any(forbidden in f for f in self.violations(ty=mutant)))

    def test_indirect_hir_mutation_or_syntax(self):
        """Reject mutations and parser reads reachable from stored-fact accessors."""
        for forbidden in ("array_new", "array_set", "array_push", "array_release", "array_clear", "v4_parse_file_stream", "v4_hir_extern_return_prepare_owner"):
            with self.subTest(forbidden=forbidden):
                mutant = self.inject(self.hir, "v4_hir_extern_member_return_span", "hidden_extern_write()")
                mutant += "\ntask hidden_extern_write() -> void { " + forbidden + "(0, 0) }\n"
                self.assertTrue(any(forbidden in f for f in self.violations(hir=mutant)))

    def test_cold_initialization_is_not_a_storage_read(self):
        """Treat direct and indirect cold initialization as mutation, not reading."""
        for root, source in (
            ("v4_hir_extern_member_count", self.hir),
            ("v4_ty_extern_declared_return_surface_type", self.ty),
        ):
            for indirect in (False, True):
                with self.subTest(root=root, indirect=indirect):
                    statement = "hidden_extern_init()" if indirect else "v4_hir_init()"
                    mutant = self.inject(source, root, statement)
                    if indirect:
                        mutant += "\ntask hidden_extern_init() -> void { v4_hir_init() }\n"
                    findings = self.violations(hir=mutant) if root.startswith("v4_hir_") else self.violations(ty=mutant)
                    self.assertTrue(any("v4_hir_init" in f for f in findings))

    def test_missing_storage_task(self):
        """Fail closed when a required HIR accessor is absent."""
        mutant = self.hir.replace("task v4_hir_extern_member_return_span(", "task renamed_extern_span(", 1)
        self.assertTrue(any("task missing: v4_hir_extern_member_return_span" in f for f in self.violations(hir=mutant)))

    def test_comments_and_strings_do_not_supply_calls(self):
        """Keep textual decoys from satisfying the declared-surface dependency."""
        for decoy in ('-- v4_hir_extern_member_return_surface_type(0, 0, 0)', 'say "v4_hir_extern_member_return_surface_type(0, 0, 0)"'):
            with self.subTest(decoy=decoy):
                mutant = self.replace_body(self.ty, "v4_ty_extern_declared_return_surface_type", "\n" + decoy + '\n give back ""\n')
                self.assertTrue(any("does not consume stored HIR surface" in f for f in self.violations(ty=mutant)))

    def test_unknown_helper_fails_closed(self):
        """Reject an uninspectable helper instead of assuming it is read-only."""
        mutant = self.inject(self.hir, "v4_hir_extern_member_count", "unknown_extern_reader()")
        self.assertTrue(any("unknown helper: unknown_extern_reader" in f for f in self.violations(hir=mutant)))

    def test_cycles_terminate_and_literal_decoys_stay_inert(self):
        """Terminate recursive traversal without treating string content as code."""
        mutant = self.inject(self.ty, "v4_ty_extern_declared_return_surface_type", 'cyclic_extern_reader()\n say "v4_lex_token_value(0, 0)"')
        mutant += "\ntask cyclic_extern_reader() -> void { cyclic_extern_reader() }\n"
        self.assertEqual(self.violations(ty=mutant), [])

    def test_arrow_recovery_requires_active_flag_branch(self):
        """Require the sole recovery call to sit inside the stored-flag branch."""
        name = "v4_ty_extern_member_return_surface_from_hir"
        body = guard.freak_task_body(self.ty, name)
        for flag in ("false", 'true -- v4_hir_extern_member_return_has_arrow_fallback(hir_id, hir_item, member_id)\n'):
            with self.subTest(flag=flag):
                mutant = self.ty.replace(body, body.replace("v4_hir_extern_member_return_has_arrow_fallback(hir_id, hir_item, member_id)", flag), 1)
                self.assertTrue(any("must be gated" in f for f in self.violations(ty=mutant)))
        mutant = self.inject(self.ty, name, "v4_ty_extern_return_arrow_recovery(hir_id, hir_item, member_id)")
        self.assertTrue(any("must be gated" in f for f in self.violations(ty=mutant)))

    def test_declared_surface_keeps_priority(self):
        """Reject a dispatcher that bypasses a nonempty stored declaration."""
        name = "v4_ty_extern_member_return_surface_from_hir"
        body = guard.freak_task_body(self.ty, name)
        mutant = self.ty.replace(body, body.replace('surface != ""', 'surface == ""'), 1)
        self.assertTrue(any("must take priority" in f for f in self.violations(ty=mutant)))

    def test_recovery_cannot_reconstruct_declared_text(self):
        """Keep declared-type token reconstruction out of the recovery closure."""
        mutant = self.inject(self.ty, "v4_ty_extern_return_arrow_recovery", "hidden_extern_recovery()")
        mutant += "\ntask hidden_extern_recovery() -> void { v4_ty_type_text(0, 0, 0) }\n"
        self.assertTrue(any("v4_ty_type_text" in f for f in self.violations(ty=mutant)))

    def test_synthetic_and_display_consumers_are_pinned(self):
        """Require signatures, spans, displays and direct returns to use their adapters."""
        for root, required in (
            ("v4_ty_signature_return_surface_type", "v4_ty_extern_member_return_surface_from_hir"),
            ("v4_ty_signature_return_span", "v4_hir_extern_member_return_span"),
            ("v4_ty_display_for_hir_item", "v4_ty_extern_member_return_surface_from_hir"),
            ("v4_ty_extern_member_return_type", "v4_ty_canonical_type"),
        ):
            with self.subTest(root=root):
                body = guard.freak_task_body(self.ty, root)
                self.assertIsNotNone(body, root)
                replacement = body.replace(required + "(", "wrong_extern_consumer(")
                self.assertNotEqual(replacement, body, root)
                mutant = self.replace_body(self.ty, root, replacement)
                self.assertTrue(any("does not consume " + required in f for f in self.violations(ty=mutant)))


class ExternReturnAuditGuards(unittest.TestCase):
    """Reject loss of active separator probes or their native checker oracles."""

    fixture_name = "extern_return_separator_smoke.fk"
    invocation = "v4_extern_separator_run()"

    @classmethod
    def setUpClass(cls):
        """Read the registered fixture and literal harness once for mutations."""
        cls.tests = ROOT / "src/compiler/v4/tests"
        cls.fixture = cls.tests / cls.fixture_name
        cls.harness = ROOT / "src/compiler/v4/check_v4.py"
        cls.source = cls.fixture.read_text(encoding="utf-8")
        cls.manifest = cls.harness.read_text(encoding="utf-8")
        cls.labels = next(
            smoke["expect"] for smoke in guard.EXECUTABLE_SMOKES
            if smoke["fixture"] == cls.fixture.name
        )

    def separator_errors(self, source=None, manifest=None, missing=False):
        """Exercise the production audit inventory with one isolated fixture."""
        original_read = Path.read_text
        original_probe = auditor._hir_lookup_probe_errors

        def selected_read(path, *args, **kwargs):
            if path == self.fixture:
                if missing:
                    raise FileNotFoundError(self.fixture.name)
                return self.source if source is None else source
            if path == self.harness:
                return self.manifest if manifest is None else manifest
            return original_read(path, *args, **kwargs)

        def selected_probe(fixture, harness, labels, invocations):
            if fixture == self.fixture:
                return original_probe(fixture, harness, labels, invocations)
            return []

        with patch.object(Path, "read_text", selected_read), patch.object(
            auditor, "_hir_lookup_probe_errors", selected_probe,
        ):
            return auditor._hir_extern_return_probe_errors(self.tests, self.harness)

    def test_live_extern_inventory(self):
        """Require all four live fixtures, invocations and literal oracles."""
        self.assertEqual(auditor._hir_extern_return_probe_errors(self.tests, self.harness), [])

    def test_separator_fixture_and_registration_are_required(self):
        """Fail when either the source fixture or its native registration is lost."""
        self.assertTrue(any("unreadable" in error for error in self.separator_errors(missing=True)))
        mutant = self.manifest.replace(
            '"fixture": "' + self.fixture_name + '"',
            '"fixture": "renamed_separator.fk"', 1,
        )
        self.assertNotEqual(mutant, self.manifest)
        self.assertIn("EXECUTABLE_SMOKES: missing " + self.fixture.name, self.separator_errors(manifest=mutant))

    def test_separator_invocation_cannot_be_a_comment_or_definition(self):
        """A task declaration and commented call cannot stand in for execution."""
        invocation = "\n" + self.invocation
        self.assertEqual(self.source.count(invocation), 1)
        mutant = self.source.replace(invocation, "\n-- " + self.invocation, 1)
        self.assertTrue(any(self.invocation in error for error in self.separator_errors(source=mutant)))

    def test_each_separator_probe_is_active_and_required(self):
        """Reject every removed probe even when its original text is a comment."""
        for oracle in self.labels:
            label = oracle.removesuffix("true")
            needle = 'say "' + label + '" + word_from_bool('
            with self.subTest(label=label):
                self.assertEqual(self.source.count(needle), 1)
                mutant = self.source.replace(needle, 'say "inactive=" + word_from_bool(', 1)
                mutant += "\n-- " + needle + "true)\n"
                self.assertTrue(any(label in error for error in self.separator_errors(source=mutant)))

    def test_each_separator_true_oracle_is_required(self):
        """False expectations and commented true decoys cannot satisfy the audit."""
        for oracle in self.labels:
            with self.subTest(oracle=oracle):
                self.assertEqual(self.manifest.count('"' + oracle + '"'), 1)
                mutant = self.manifest.replace('"' + oracle + '"', '"' + oracle.removesuffix("true") + 'false"', 1)
                mutant += '\n# "' + oracle + '"\n'
                self.assertTrue(any(oracle in error for error in self.separator_errors(manifest=mutant)))


class ExternNestedArrowAuditGuards(ExternReturnAuditGuards):
    """Apply every negative audit mutation to the isolated nested fixture too."""

    fixture_name = "extern_return_nested_arrow_smoke.fk"
    invocation = "v4_extern_nested_arrow_run()"


if __name__ == "__main__":
    unittest.main()
