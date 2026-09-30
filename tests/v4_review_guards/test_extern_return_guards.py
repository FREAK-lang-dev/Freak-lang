"""Compiler-free regressions for stored extern-return dependency boundaries."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location("extern_return_guard", ROOT / "src/compiler/v4/check_v4.py")
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class ExternReturnGuards(unittest.TestCase):
    def setUp(self):
        self.hir = guard.read_text(guard.crate_path("freak_hir"))
        self.ty = guard.read_text(guard.crate_path("freak_ty"))

    def violations(self, hir=None, ty=None):
        return guard.extern_return_boundary_violations(
            self.hir if hir is None else hir, self.ty if ty is None else ty,
        )

    def replace_body(self, source, name, replacement):
        source = guard.freak_mask_line_comments(source)
        body = guard.freak_task_body(source, name)
        self.assertIsNotNone(body, name)
        self.assertIn(body, source)
        return source.replace(body, replacement, 1)

    def inject(self, source, name, statement):
        source = guard.freak_mask_line_comments(source)
        body = guard.freak_task_body(source, name)
        self.assertIsNotNone(body, name)
        self.assertIn(body, source)
        return source.replace(body, "\n" + statement + "\n" + body, 1)

    def test_live_contract(self):
        self.assertEqual(self.violations(), [])

    def test_indirect_declared_type_reconstruction(self):
        for forbidden in ("v4_lex_token_value", "v4_expand_file_stream", "v4_ty_type_text", "v4_ty_task_return_from_tokens"):
            with self.subTest(forbidden=forbidden):
                mutant = self.inject(self.ty, "v4_ty_extern_declared_return_surface_type", "hidden_extern_read()")
                mutant += "\ntask hidden_extern_read() -> void { " + forbidden + "(0, 0) }\n"
                self.assertTrue(any(forbidden in f for f in self.violations(ty=mutant)))

    def test_indirect_hir_mutation_or_syntax(self):
        for forbidden in ("array_new", "array_set", "array_push", "array_release", "array_clear", "v4_parse_file_stream", "v4_hir_extern_return_prepare_owner"):
            with self.subTest(forbidden=forbidden):
                mutant = self.inject(self.hir, "v4_hir_extern_member_return_span", "hidden_extern_write()")
                mutant += "\ntask hidden_extern_write() -> void { " + forbidden + "(0, 0) }\n"
                self.assertTrue(any(forbidden in f for f in self.violations(hir=mutant)))

    def test_missing_storage_task(self):
        mutant = self.hir.replace("task v4_hir_extern_member_return_span(", "task renamed_extern_span(", 1)
        self.assertTrue(any("task missing: v4_hir_extern_member_return_span" in f for f in self.violations(hir=mutant)))

    def test_comments_and_strings_do_not_supply_calls(self):
        for decoy in ('-- v4_hir_extern_member_return_surface_type(0, 0, 0)', 'say "v4_hir_extern_member_return_surface_type(0, 0, 0)"'):
            with self.subTest(decoy=decoy):
                mutant = self.replace_body(self.ty, "v4_ty_extern_declared_return_surface_type", "\n" + decoy + '\n give back ""\n')
                self.assertTrue(any("does not consume stored HIR surface" in f for f in self.violations(ty=mutant)))

    def test_unknown_helper_fails_closed(self):
        mutant = self.inject(self.hir, "v4_hir_extern_member_count", "unknown_extern_reader()")
        self.assertTrue(any("unknown helper: unknown_extern_reader" in f for f in self.violations(hir=mutant)))

    def test_cycles_terminate_and_literal_decoys_stay_inert(self):
        mutant = self.inject(self.ty, "v4_ty_extern_declared_return_surface_type", 'cyclic_extern_reader()\n say "v4_lex_token_value(0, 0)"')
        mutant += "\ntask cyclic_extern_reader() -> void { cyclic_extern_reader() }\n"
        self.assertEqual(self.violations(ty=mutant), [])

    def test_arrow_recovery_requires_active_flag_branch(self):
        name = "v4_ty_extern_member_return_surface_from_hir"
        body = guard.freak_task_body(self.ty, name)
        for flag in ("false", 'true -- v4_hir_extern_member_return_has_arrow_fallback(hir_id, hir_item, member_id)\n'):
            with self.subTest(flag=flag):
                mutant = self.ty.replace(body, body.replace("v4_hir_extern_member_return_has_arrow_fallback(hir_id, hir_item, member_id)", flag), 1)
                self.assertTrue(any("must be gated" in f for f in self.violations(ty=mutant)))
        mutant = self.inject(self.ty, name, "v4_ty_extern_return_arrow_recovery(hir_id, hir_item, member_id)")
        self.assertTrue(any("must be gated" in f for f in self.violations(ty=mutant)))

    def test_declared_surface_keeps_priority(self):
        name = "v4_ty_extern_member_return_surface_from_hir"
        body = guard.freak_task_body(self.ty, name)
        mutant = self.ty.replace(body, body.replace('surface != ""', 'surface == ""'), 1)
        self.assertTrue(any("must take priority" in f for f in self.violations(ty=mutant)))

    def test_recovery_cannot_reconstruct_declared_text(self):
        mutant = self.inject(self.ty, "v4_ty_extern_return_arrow_recovery", "hidden_extern_recovery()")
        mutant += "\ntask hidden_extern_recovery() -> void { v4_ty_type_text(0, 0, 0) }\n"
        self.assertTrue(any("v4_ty_type_text" in f for f in self.violations(ty=mutant)))

    def test_synthetic_and_display_consumers_are_pinned(self):
        for root, required in (
            ("v4_ty_signature_return_surface_type", "v4_ty_extern_member_return_surface_from_hir"),
            ("v4_ty_signature_return_span", "v4_hir_extern_member_return_span"),
            ("v4_ty_display_for_hir_item", "v4_ty_extern_member_return_surface_from_hir"),
            ("v4_ty_extern_member_return_type", "v4_ty_canonical_type"),
        ):
            with self.subTest(root=root):
                body = guard.freak_task_body(self.ty, root)
                mutant = self.ty.replace(body, body.replace(required + "(", "wrong_extern_consumer("), 1)
                self.assertTrue(any("does not consume " + required in f for f in self.violations(ty=mutant)))


if __name__ == "__main__":
    unittest.main()
