"""Pure-Python declared-Const boundary regressions; no compiler execution."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location("const_guard_harness", ROOT / "src/compiler/v4/check_v4.py")
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class ConstGuards(unittest.TestCase):
    def setUp(self):
        self.hir = guard.read_text(guard.crate_path("freak_hir"))
        self.ty = guard.read_text(guard.crate_path("freak_ty"))

    def test_live_storage_contract(self):
        self.assertEqual(guard.const_boundary_violations(self.hir, self.ty), [])

    def replace_type_call(self):
        body = guard.freak_task_body(self.ty, "v4_ty_const_declared_type_for_sig")
        self.assertIn("v4_hir_const_type(", body)
        return self.ty.replace(body, body.replace("v4_hir_const_type(", "hidden_const_bridge("), 1)

    def test_indirect_syntax_reconstruction_is_rejected(self):
        mutant = self.replace_type_call()
        mutant += "\ntask hidden_const_bridge(a: int, b: int) -> word { give back v4_expand_const_type(a, b) }\n"
        self.assertTrue(any("v4_expand_const_type" in f for f in guard.const_boundary_violations(self.hir, mutant)))

    def test_comments_and_literals_cannot_supply_required_calls(self):
        for decoy in ('-- v4_hir_const_type(a, b)', 'say "v4_hir_const_type(a, b)"'):
            with self.subTest(decoy=decoy):
                mutant = self.replace_type_call()
                mutant += '\ntask hidden_const_bridge(a: int, b: int) -> word {\n' + decoy + '\n give back ""\n}\n'
                self.assertTrue(any("does not consume" in f for f in guard.const_boundary_violations(self.hir, mutant)))

    def test_hir_indirect_mutation_is_rejected(self):
        body = guard.freak_task_body(self.hir, "v4_hir_const_type")
        mutant = self.hir.replace(body, "\n hidden_const_rebuild()\n" + body, 1)
        mutant += '\ntask hidden_const_rebuild() -> void { array_push(0, "value") }\n'
        self.assertTrue(any("array_push" in f for f in guard.const_boundary_violations(mutant, self.ty)))

    def test_initializer_bridge_is_rejected(self):
        mutant = self.replace_type_call()
        mutant += "\ntask hidden_const_bridge(a: int, b: int) -> word { give back v4_hir_const_init(a, b) }\n"
        self.assertTrue(any("v4_hir_const_init" in f for f in guard.const_boundary_violations(self.hir, mutant)))

    def test_missing_span_contract_is_rejected(self):
        body = guard.freak_task_body(self.ty, "v4_ty_const_declared_type_span_for_sig")
        self.assertIsNotNone(body)
        mutant = self.ty.replace(body, "\n give back V4_NO_SPAN\n", 1)
        self.assertTrue(any("does not consume v4_hir_const_type_span" in f for f in guard.const_boundary_violations(self.hir, mutant)))

    def test_cycles_terminate_and_literals_do_not_create_edges(self):
        body = guard.freak_task_body(self.ty, "v4_ty_const_name_span")
        mutant = self.ty.replace(body, '\n cyclic_const_helper()\n say "v4_lex_token_count(0)"\n' + body, 1)
        mutant += "\ntask cyclic_const_helper() -> void { cyclic_const_helper() }\n"
        self.assertEqual(guard.const_boundary_violations(self.hir, mutant), [])


if __name__ == "__main__":
    unittest.main()
