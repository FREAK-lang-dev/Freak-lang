"""Architecture lane A1/A3 guards: freak_ty token allowlist, TY source identity
shim and codegen boundary. Pure Python; no compiler execution."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location("architecture_lane_harness", ROOT / "src/compiler/v4/check_v4.py")
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class ArchitectureLaneGuards(unittest.TestCase):
    def setUp(self):
        self.ty = guard.read_text(guard.crate_path("freak_ty"))
        self.codegen = guard.read_text(guard.crate_path("freak_codegen_llvm"))

    def violations(self, ty=None, codegen=None):
        return guard.architecture_lane_violations(
            self.ty if ty is None else ty,
            self.codegen if codegen is None else codegen,
        )

    def append_task(self, source, body):
        return source + "\ntask v4_arch_lane_probe(tree_id: int) -> int {\n" + body + "\n}\n"

    def test_current_tree_is_clean(self):
        self.assertEqual(self.violations(), [])

    def test_identity_helper_outside_shim_is_rejected(self):
        ty = self.append_task(self.ty, "    give back v4_parse_stream_id(tree_id)")
        found = self.violations(ty=ty)
        self.assertTrue(
            any("v4_arch_lane_probe bypasses the source identity shim: v4_parse_stream_id" in v for v in found),
            found,
        )

    def test_identity_global_outside_shim_is_rejected(self):
        ty = self.append_task(self.ty, "    if v4_lex_ready == 0 { give back 0 }\n    give back 1")
        found = self.violations(ty=ty)
        self.assertTrue(any("bypasses the source identity shim: v4_lex_ready" in v for v in found), found)

    def test_identity_helper_in_comment_is_ignored(self):
        ty = self.append_task(self.ty, "    -- v4_parse_stream_id(tree_id) is read through the shim\n    give back 0")
        self.assertEqual(self.violations(ty=ty), [])

    def test_shim_that_stops_wrapping_is_rejected(self):
        body = guard.freak_task_body(self.ty, "v4_ty_source_tree_stream")
        self.assertIsNotNone(body)
        ty = self.ty.replace(body, "\n    give back tree_id\n", 1)
        found = self.violations(ty=ty)
        self.assertTrue(any("v4_ty_source_tree_stream no longer wraps v4_parse_stream_id" in v for v in found), found)

    def test_missing_shim_task_is_rejected(self):
        ty = self.ty.replace("task v4_ty_source_ready()", "task v4_ty_source_ready_renamed()", 1)
        found = self.violations(ty=ty)
        self.assertTrue(any("source identity shim v4_ty_source_ready" in v for v in found), found)

    def test_new_token_helper_in_ty_is_rejected(self):
        ty = self.append_task(self.ty, "    give back v4_lex_token_kind_probe(tree_id)")
        found = self.violations(ty=ty)
        self.assertTrue(
            any("freak_ty transitional lexer allowlist drift: added=v4_lex_token_kind_probe" in v for v in found),
            found,
        )

    def test_removed_token_helper_in_ty_must_shrink_allowlist(self):
        ty = guard.freak_mask_line_comments(self.ty)
        # Drop every use of one allowlisted helper; the allowlist must shrink with it.
        ty = ty.replace("v4_lex_is_digit(", "v4_ty_probe_digit(")
        found = self.violations(ty=ty)
        self.assertTrue(
            any("freak_ty transitional lexer allowlist drift: removed=v4_lex_is_digit" in v for v in found),
            found,
        )

    def test_new_codegen_ty_name_lookup_is_rejected(self):
        codegen = self.codegen + "\ntask v4_codegen_llvm_probe(name: word) -> int {\n    give back v4_ty_shape_field_id_for_name(0, 0, name)\n}\n"
        found = self.violations(codegen=codegen)
        self.assertTrue(
            any("TY name lookup allowlist drift: added=v4_ty_shape_field_id_for_name" in v for v in found),
            found,
        )

    def test_codegen_forbids_syntax_and_hir_access(self):
        forbidden = dict(guard.CRATE_BOUNDARY_FORBIDDEN["freak_codegen_llvm"])
        for label in ("lexer access", "parser access", "HIR access", "resolve access", "expansion access"):
            self.assertIn(label, forbidden)
        self.assertNotIn("v4_lex_", self.codegen)
        self.assertNotIn("v4_hir_", self.codegen)


if __name__ == "__main__":
    unittest.main()
