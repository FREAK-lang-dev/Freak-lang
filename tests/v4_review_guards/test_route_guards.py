"""Pure-Python route declaration boundary regressions; no compiler execution."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location("route_guard_harness", ROOT / "src/compiler/v4/check_v4.py")
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class RouteGuards(unittest.TestCase):
    def setUp(self):
        self.hir = guard.read_text(guard.crate_path("freak_hir"))
        self.ty = guard.read_text(guard.crate_path("freak_ty"))
        self.editor = guard.read_text(guard.crate_path("freak_editor"))

    def violations(self, hir=None, ty=None, editor=None):
        return guard.route_boundary_violations(
            self.hir if hir is None else hir,
            self.ty if ty is None else ty,
            self.editor if editor is None else editor,
        )

    def replace_body(self, source, name, replacement):
        body = guard.freak_task_body(source, name)
        self.assertIsNotNone(body, name)
        return source.replace(body, replacement, 1)

    def inject(self, source, name, statement):
        body = guard.freak_task_body(source, name)
        self.assertIsNotNone(body, name)
        return source.replace(body, "\n" + statement + "\n" + body, 1)

    def test_live_storage_contract(self):
        self.assertEqual(self.violations(), [])

    def test_missing_metadata_contracts_are_rejected(self):
        for suffix in (
            "count", "name", "name_span", "segment_span", "has_payload", "field_count",
            "field_name", "field_name_span", "field_surface_type", "field_type_span", "field_segment_span",
        ):
            with self.subTest(suffix=suffix):
                mutant = self.replace_body(self.ty, "v4_ty_route_case_" + suffix, "\n give back 0\n")
                self.assertTrue(any("does not consume v4_hir_route_case_" + suffix in f for f in self.violations(ty=mutant)))
        mutant = self.replace_body(self.hir, "v4_hir_route_is_variant", "\n hidden_route_form()\n give back false\n")
        mutant += "\ntask hidden_route_form() -> void { v4_hir_item_decl_keyword(0, 0) }\n"
        self.assertTrue(any("v4_hir_item_decl_keyword" in f for f in self.violations(hir=mutant)))

    def test_comments_and_strings_cannot_supply_required_calls(self):
        for decoy in ('-- v4_hir_route_case_name(0, 0, 0)', 'say "v4_hir_route_case_name(0, 0, 0)"'):
            with self.subTest(decoy=decoy):
                mutant = self.replace_body(self.ty, "v4_ty_route_case_name", "\n" + decoy + '\n give back ""\n')
                self.assertTrue(any("does not consume v4_hir_route_case_name:" in f for f in self.violations(ty=mutant)))

    def test_indirect_ty_syntax_reconstruction_is_rejected(self):
        for forbidden in ("v4_lex_token_value", "v4_ty_route_case_segment_start", "v4_ty_type_text", "v4_expand_file_stream"):
            with self.subTest(forbidden=forbidden):
                mutant = self.inject(self.ty, "v4_ty_route_case_field_surface_type", "hidden_route_bridge()")
                mutant += "\ntask hidden_route_bridge() -> void { " + forbidden + "(0, 0, 0) }\n"
                self.assertTrue(any(forbidden in f for f in self.violations(ty=mutant)))

    def test_indirect_hir_syntax_or_mutation_is_rejected(self):
        for forbidden in (
            "v4_expand_file_stream", "v4_parse_file_stream", "v4_hir_item_decl_keyword",
            "array_set", "array_push", "array_new", "array_release", "array_pop", "array_clear",
            "v4_hir_lower_route", "v4_hir_route_prepare_owner",
        ):
            with self.subTest(forbidden=forbidden):
                mutant = self.inject(self.hir, "v4_hir_route_case_field_name", "hidden_route_rebuild()")
                mutant += "\ntask hidden_route_rebuild() -> void { " + forbidden + "(0) }\n"
                self.assertTrue(any(forbidden in f for f in self.violations(hir=mutant)))

    def test_editor_metadata_cannot_indirectly_read_tokens(self):
        for root in ("v4_editor_route_case_name_span", "v4_editor_route_field_name_span"):
            with self.subTest(root=root):
                mutant = self.inject(self.editor, root, "hidden_route_editor_bridge()")
                mutant += "\ntask hidden_route_editor_bridge() -> void { v4_lex_token_span(0, 0) }\n"
                self.assertTrue(any("v4_lex_token_span" in f for f in self.violations(editor=mutant)))

    def test_declaration_matchers_must_consume_semantic_spans(self):
        for root, required in (
            ("v4_editor_route_case_decl_id_at_token", "v4_ty_route_case_name_span"),
            ("v4_editor_route_field_decl_case_name_at_token", "v4_ty_route_case_field_name_span"),
        ):
            with self.subTest(root=root):
                mutant = self.replace_body(self.editor, root, "\n give back v4_lex_token_span(0, 0)\n")
                self.assertTrue(any("does not consume " + required in f for f in self.violations(editor=mutant)))
                mutant = self.inject(self.editor, root, "v4_lex_token_value(0, 0)")
                self.assertTrue(any("v4_lex_token_value" in f for f in self.violations(editor=mutant)))

    def test_canonical_field_adapter_retains_semantic_operations(self):
        for required in ("v4_ty_apply_signature_generics", "v4_ty_canonical_type"):
            with self.subTest(required=required):
                body = guard.freak_task_body(self.ty, "v4_ty_route_case_field_type")
                self.assertIn(required + "(", body)
                mutant = self.ty.replace(body, body.replace(required + "(", "hidden_route_semantic_noop("), 1)
                mutant += '\ntask hidden_route_semantic_noop() -> word { give back "int" }\n'
                self.assertTrue(any("does not consume " + required in f for f in self.violations(ty=mutant)))
        mutant = self.inject(self.ty, "v4_ty_route_case_field_type", "v4_ty_canonical_type_for_signature(0, 0, \"int\")")
        self.assertTrue(any("v4_ty_canonical_type_for_signature" in f for f in self.violations(ty=mutant)))

    def test_cycles_and_literal_decoys_terminate_without_false_positives(self):
        mutant = self.inject(self.ty, "v4_ty_route_case_name", 'cyclic_route_helper()\n say "v4_lex_token_count(0)"')
        mutant += "\ntask cyclic_route_helper() -> void { cyclic_route_helper() }\n"
        self.assertEqual(self.violations(ty=mutant), [])

    def test_discriminants_cursor_discovery_and_generic_declarations_remain_out_of_scope(self):
        ty = self.inject(self.ty, "v4_ty_route_case_explicit_discriminant_text_by_sig", "v4_lex_token_value(0, 0)")
        ty = self.inject(ty, "v4_ty_signature_generic_count", "v4_lex_token_value(0, 0)")
        editor = self.inject(self.editor, "v4_editor_route_case_name_for_payload_token", "v4_lex_token_value(0, 0)")
        self.assertEqual(self.violations(ty=ty, editor=editor), [])

    def test_unresolved_metadata_helpers_are_rejected(self):
        mutant = self.inject(self.hir, "v4_hir_route_case_name", "v4_hir_missing_route_helper()")
        self.assertTrue(any("task missing: v4_hir_missing_route_helper" in f for f in self.violations(hir=mutant)))

    def test_discriminant_segments_require_stored_spans_and_bounded_conversion(self):
        for root in ("v4_ty_route_case_segment_start", "v4_ty_route_case_segment_end"):
            for decoy in (
                '-- v4_hir_route_case_segment_span(0, 0, 0)',
                'say "v4_hir_route_case_segment_span(0, 0, 0)"',
            ):
                with self.subTest(root=root, decoy=decoy):
                    mutant = self.replace_body(self.ty, root, "\n" + decoy + "\n give back 0\n")
                    violations = self.violations(ty=mutant)
                    self.assertTrue(any("route segment adapter does not consume v4_hir_route_case_segment_span: " + root in f for f in violations))
                    self.assertTrue(any("route segment adapter does not consume v4_ty_first_token_at_or_after: " + root in f for f in violations))

    def test_discriminant_segments_cannot_indirectly_resplit_cases(self):
        for forbidden in (
            "v4_lex_token_value", "v4_lex_token_type", "v4_ty_type_text",
            "v4_ty_route_is_case_separator", "v4_ty_route_body_open_token",
            "v4_ty_route_body_close_token", "v4_expand_file_stream",
        ):
            with self.subTest(forbidden=forbidden):
                mutant = self.inject(self.ty, "v4_ty_route_case_segment_end", "hidden_route_segment_bridge()")
                mutant += "\ntask hidden_route_segment_bridge() -> void { " + forbidden + "(0) }\n"
                self.assertTrue(any("route segment adapter reconstructs case boundaries: " + forbidden in f for f in self.violations(ty=mutant)))

    def test_discriminant_segments_cannot_use_generic_metadata_exemptions(self):
        mutant = self.inject(self.ty, "v4_ty_route_case_segment_end", "v4_ty_signature_generic_count(ty_id, sig_id)")
        self.assertTrue(any("route segment adapter reconstructs case boundaries: v4_lex_token_value" in f for f in self.violations(ty=mutant)))


if __name__ == "__main__":
    unittest.main()
