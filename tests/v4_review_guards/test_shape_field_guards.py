"""Pure-Python shape storage boundary regressions; no compiler execution."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location("shape_field_guard_harness", ROOT / "src/compiler/v4/check_v4.py")
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class ShapeFieldGuards(unittest.TestCase):
    def setUp(self):
        self.hir = guard.read_text(guard.crate_path("freak_hir"))
        self.ty = guard.read_text(guard.crate_path("freak_ty"))

    def test_live_storage_contract(self):
        self.assertEqual(guard.shape_field_boundary_violations(self.hir, self.ty), [])

    def replace_count_call(self, replacement):
        name = "v4_ty_shape_field_count"
        body = guard.freak_task_body(self.ty, name)
        self.assertIn("v4_hir_shape_field_count(", body)
        return self.ty.replace(body, body.replace("v4_hir_shape_field_count(", replacement + "("), 1)

    def test_hidden_token_fallback_is_rejected(self):
        mutant = self.replace_count_call("hidden_shape_bridge")
        mutant += "\ntask hidden_shape_bridge(a: int, b: int) -> int { give back v4_lex_token_count(a) }\n"
        findings = guard.shape_field_boundary_violations(self.hir, mutant)
        self.assertTrue(any("v4_lex_token_count" in f for f in findings))

    def test_comment_cannot_supply_required_call(self):
        mutant = self.replace_count_call("hidden_shape_bridge")
        mutant += "\ntask hidden_shape_bridge(a: int, b: int) -> int {\n -- v4_hir_shape_field_count(a, b)\n give back 0\n}\n"
        self.assertTrue(any("does not consume" in f for f in guard.shape_field_boundary_violations(self.hir, mutant)))

    def test_string_cannot_supply_required_call(self):
        mutant = self.replace_count_call("hidden_shape_bridge")
        mutant += '\ntask hidden_shape_bridge(a: int, b: int) -> int {\n say "v4_hir_shape_field_count(a, b)"\n give back 0\n}\n'
        self.assertTrue(any("does not consume" in f for f in guard.shape_field_boundary_violations(self.hir, mutant)))

    def test_hir_hidden_reconstruction_is_rejected(self):
        body = guard.freak_task_body(self.hir, "v4_hir_shape_field_count")
        mutant = self.hir.replace(body, "\n hidden_shape_rebuild()\n" + body, 1)
        mutant += "\ntask hidden_shape_rebuild() -> void { v4_parse_file(0) }\n"
        self.assertTrue(any("v4_parse_file" in f for f in guard.shape_field_boundary_violations(mutant, self.ty)))

    def test_generic_scope_semantics_cannot_change_silently(self):
        body = guard.freak_task_body(self.ty, "v4_ty_shape_field_type")
        self.assertIn("v4_ty_canonical_type(", body)
        mutant = self.ty.replace(body, body.replace("v4_ty_canonical_type(", "v4_ty_canonical_type_for_signature("), 1)
        self.assertTrue(guard.shape_field_boundary_violations(self.hir, mutant))

    def test_cycles_terminate_and_literals_do_not_create_edges(self):
        body = guard.freak_task_body(self.ty, "v4_ty_shape_field_count")
        mutant = self.ty.replace(body, '\n cyclic_shape_helper()\n say "v4_lex_token_count(0)"\n' + body, 1)
        mutant += "\ntask cyclic_shape_helper() -> void { cyclic_shape_helper() }\n"
        self.assertEqual(guard.shape_field_boundary_violations(self.hir, mutant), [])


if __name__ == "__main__":
    unittest.main()
