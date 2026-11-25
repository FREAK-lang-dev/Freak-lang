"""Architecture lane A1/A3/A4 guards: freak_ty token allowlist, TY source
identity shim, HIR method facts, codegen boundary and the Runtime MIR stage.
Pure Python; no compiler execution."""
import contextlib
import importlib.util
import io
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

    def test_declaration_after_shim_body_is_not_exempt(self):
        header = "task v4_ty_source_stream_revision(stream_id: int) -> int {"
        body = guard.freak_task_body(self.ty, "v4_ty_source_stream_revision")
        self.assertIsNotNone(body)
        shim = header + body + "}\n"
        self.assertIn(shim, self.ty)
        ty = self.ty.replace(shim, shim + "\npilot v4_ty_probe_ready = v4_lex_ready\n", 1)
        found = self.violations(ty=ty)
        self.assertTrue(
            any("v4_ty_source_stream_revision (outside its body) bypasses the source identity shim: v4_lex_ready" in v for v in found),
            found,
        )

    def test_shim_with_extra_syntax_read_is_rejected(self):
        body = guard.freak_task_body(self.ty, "v4_ty_source_tree_file")
        self.assertIsNotNone(body)
        ty = self.ty.replace(body, "\n    pilot probe = v4_lex_token_value(0, 0)" + body, 1)
        found = self.violations(ty=ty)
        self.assertTrue(any("v4_ty_source_tree_file reads v4_lex_token_value" in v for v in found), found)

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

    def test_method_count_token_walk_is_rejected(self):
        body = guard.freak_task_body(self.ty, "v4_ty_doctrine_method_count")
        self.assertIsNotNone(body)
        ty = self.ty.replace(body, body.replace("give back v4_hir_method_count(", "pilot walked = v4_ty_skip_item(0, 0, 0)\n    give back v4_hir_method_count(", 1), 1)
        found = self.violations(ty=ty)
        self.assertTrue(any("v4_ty_doctrine_method_count walks method tokens" in v for v in found), found)

    def test_method_return_rebuilt_from_tokens_is_rejected(self):
        body = guard.freak_task_body(self.ty, "v4_ty_hir_method_return_surface_type")
        self.assertIsNotNone(body)
        ty = self.ty.replace(body, body.replace("give back v4_ty_unknown", "give back v4_ty_type_text(0, 0, 0)", 1), 1)
        found = self.violations(ty=ty)
        self.assertTrue(any("reconstructs a declared type from tokens" in v for v in found), found)

    def test_method_arrow_fallback_must_stay_pinned(self):
        ty = self.ty.replace("task v4_ty_hir_method_arrow_return_fallback(", "task v4_ty_hir_method_arrow_return_fallback_renamed(", 1)
        found = self.violations(ty=ty)
        self.assertTrue(any("method arrow shorthand return fallback is not separately pinned" in v for v in found), found)

    def test_extern_param_reader_without_hir_arm_is_rejected(self):
        body = guard.freak_task_body(self.ty, "v4_ty_signature_param_name")
        self.assertIsNotNone(body)
        arm = "    pilot extern_member = v4_ty_signature_extern_param_member(ty_id, sig_id)\n"
        self.assertIn(arm, body)
        stripped = body.replace(arm, "", 1)
        stripped = "\n".join(line for line in stripped.split("\n") if "v4_hir_extern_param_name" not in line)
        found = self.violations(ty=self.ty.replace(body, stripped, 1))
        self.assertTrue(any("v4_ty_signature_param_name has no HIR extern parameter arm" in v for v in found), found)

    def test_param_reader_token_fallback_is_rejected(self):
        body = guard.freak_task_body(self.ty, "v4_ty_signature_param_mode")
        self.assertIsNotNone(body)
        ty = self.ty.replace(body, body.replace('give back ""', 'give back v4_lex_token_value(v4_ty_signature_stream_id(ty_id), 0)', 1), 1)
        self.assertNotEqual(ty, self.ty)
        found = self.violations(ty=ty)
        self.assertTrue(any("v4_ty_signature_param_mode reads task parameters from tokens" in v for v in found), found)

    def test_restored_nonordinary_param_fallback_task_is_rejected(self):
        ty = self.ty + "\ntask v4_ty_nonordinary_signature_param_count_fallback(ty_id: int, sig_id: int) -> int {\n    give back 0\n}\n"
        found = self.violations(ty=ty)
        self.assertIn("TY still defines a token fallback for task parameters", found)

    def test_extern_param_member_must_check_hir_range(self):
        body = guard.freak_task_body(self.ty, "v4_ty_signature_extern_param_member")
        self.assertIsNotNone(body)
        ty = self.ty.replace(body, body.replace(" or member_id >= v4_hir_extern_member_count(hir_id, hir_item)", "", 1), 1)
        found = self.violations(ty=ty)
        self.assertIn("extern parameter dispatch does not check the HIR member range", found)

    def test_codegen_forbids_syntax_and_hir_access(self):
        forbidden = dict(guard.CRATE_BOUNDARY_FORBIDDEN["freak_codegen_llvm"])
        for label in ("lexer access", "parser access", "HIR access", "resolve access", "expansion access"):
            self.assertIn(label, forbidden)
        self.assertNotIn("v4_lex_", self.codegen)
        self.assertNotIn("v4_hir_", self.codegen)


    def boundary_violations(self, crate, mutate, target=None):
        """Run the crate boundary gate with one crate's (or file's) text mutated."""
        target = guard.crate_path(crate) if target is None else target
        original = guard.read_text

        def patched(path):
            text = original(path)
            return mutate(text) if Path(path) == target else text

        guard.read_text = patched
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                guard.check_crate_boundaries()
        except SystemExit:
            return out.getvalue()
        finally:
            guard.read_text = original
        return ""

    def mir_build_type_arg_violations(self, mutate):
        source = mutate(guard.read_text(guard.crate_path("freak_mir_build")))
        return guard.mir_build_method_type_arg_violations(source)

    def test_method_type_arg_readers_are_clean(self):
        self.assertEqual(self.mir_build_type_arg_violations(lambda text: text), [])

    def test_method_type_arg_token_pairing_is_rejected(self):
        body = guard.freak_task_body(guard.read_text(guard.crate_path("freak_mir_build")), "v4_mir_method_type_arg_open")
        self.assertIsNotNone(body)
        found = self.mir_build_type_arg_violations(
            lambda text: text.replace(body, "\n    pilot next_token = v4_mir_skip_trivia(stream_id, method_token + 1)\n    give back next_token\n", 1)
        )
        self.assertIn("v4_mir_method_type_arg_open does not read HIR method type argument facts", found)
        self.assertIn("v4_mir_method_type_arg_open reads method type arguments from tokens: v4_mir_skip_trivia", found)

    def test_method_type_arg_text_from_tokens_is_rejected(self):
        found = self.mir_build_type_arg_violations(
            lambda text: text.replace(
                "type_text = v4_mir_compact_type_text(v4_hir_method_type_arg_type_text(v4_mir_build_hir_id, row))",
                "type_text = v4_mir_compact_type_text(v4_ty_type_text(stream_id, method_token, open_token))",
                1,
            )
        )
        self.assertIn("v4_mir_reject_method_type_args reads method type arguments from tokens: v4_ty_type_text", found)

    def test_generic_call_shape_bracket_scan_is_rejected(self):
        found = self.mir_build_type_arg_violations(
            lambda text: text.replace(
                "give back v4_mir_method_type_arg_open(stream_id, method_token, open_token) >= 0",
                'give back v4_lex_token_syntax_value(stream_id, method_token + 1) == "<"',
                1,
            )
        )
        self.assertIn("generic instance method call shape does not read HIR method type argument facts", found)

    def test_method_type_args_need_the_lowered_hir_file(self):
        found = self.mir_build_type_arg_violations(
            lambda text: text.replace("v4_parse_stream_id(v4_hir_tree_id(hir_id)) != stream_id", "false", 1)
        )
        self.assertIn("method type argument facts are read without checking the lowered HIR file", found)

    def test_raw_pointer_cast_token_walk_is_rejected(self):
        found = self.mir_build_type_arg_violations(
            lambda text: text.replace(
                "if v4_span_start(v4_hir_method_type_arg_after_close_span(v4_mir_build_hir_id, row)) != open_offset {",
                "if v4_mir_skip_trivia(stream_id, type_close + 1) != open_token {",
                1,
            )
        )
        self.assertIn("raw-pointer cast does not read HIR method type argument facts: v4_hir_method_type_arg_after_close_span", found)
        self.assertIn("raw-pointer cast reads its type argument list from tokens: type_close + 1", found)

    def test_raw_pointer_cast_text_from_tokens_is_rejected(self):
        found = self.mir_build_type_arg_violations(
            lambda text: text.replace(
                "v4_mir_compact_type_text(v4_hir_method_type_arg_type_text(v4_mir_build_hir_id, row))\n        target_pointee = v4_ty_canonical_type",
                "v4_mir_compact_type_text(v4_ty_type_text(stream_id, type_open + 1, open_token))\n        target_pointee = v4_ty_canonical_type",
                1,
            )
        )
        self.assertIn("raw-pointer cast reads its type argument list from tokens: v4_ty_type_text", found)

    def test_boundary_gate_runs_method_type_arg_guard(self):
        found = self.boundary_violations(
            "freak_mir_build",
            lambda text: text.replace("give back v4_mir_method_type_arg_open(stream_id, method_token, open_token) >= 0", "give back false", 1),
        )
        self.assertIn("generic instance method call shape does not read HIR method type argument facts", found)

    def test_codegen_meiya_call_is_rejected(self):
        found = self.boundary_violations(
            "freak_codegen_llvm",
            lambda text: text + "\ntask v4_arch_lane_probe(file_id: int, mir_id: int) -> int {\n    give back v4_borrowck_check_mir(file_id, mir_id)\n}\n",
        )
        self.assertIn("boundary violation: freak_codegen_llvm owns Meiya access", found)

    def test_codegen_must_use_runtime_mir_handoff(self):
        found = self.boundary_violations(
            "freak_codegen_llvm",
            lambda text: text.replace("error = v4_mir_transform_runtime(file_id, mir_id, borrow_id)", 'error = ""', 1),
        )
        self.assertIn("boundary missing: freak_codegen_llvm Runtime MIR handoff", found)

    def test_transform_llvm_emission_is_rejected(self):
        found = self.boundary_violations(
            "freak_mir_transform",
            lambda text: text + "\ntask v4_arch_lane_probe() -> int {\n    give back v4_codegen_llvm_file_count()\n}\n",
        )
        self.assertIn("boundary violation: freak_mir_transform owns LLVM emission", found)

    def test_transform_syntax_access_is_rejected(self):
        found = self.boundary_violations(
            "freak_mir_transform",
            lambda text: text + "\ntask v4_arch_lane_probe(tree_id: int) -> int {\n    give back v4_parse_stream_id(tree_id)\n}\n",
        )
        self.assertIn("boundary violation: freak_mir_transform owns parser access", found)

    def test_transform_sits_between_meiya_and_codegen(self):
        order = guard.CRATE_ORDER
        self.assertLess(order.index("freak_borrowck"), order.index("freak_mir_transform"))
        self.assertLess(order.index("freak_mir_transform"), order.index("freak_codegen_llvm"))
        self.assertNotIn("v4_borrowck_", self.codegen)

    def test_transform_is_a_development_crate_not_a_frozen_bootstrap_source(self):
        frozen = guard.read_text(guard.V4_ROOT / "bootstrap-sources.manifest").splitlines()
        self.assertNotIn("crates/freak_mir_transform/src/lib.fk", frozen)
        self.assertIn("crates/freak_mir_transform/src/lib.fk", guard.CRATE_SOURCE_PATHS)
        self.assertEqual(self.boundary_violations(None, lambda text: text, guard.V4_ROOT / "bootstrap-sources.manifest"), "")

    def test_frozen_bootstrap_order_drift_is_rejected(self):
        def swap(text):
            lines = text.splitlines(keepends=True)
            lines[0], lines[1] = lines[1], lines[0]
            return "".join(lines)

        found = self.boundary_violations(None, swap, guard.V4_ROOT / "bootstrap-sources.manifest")
        self.assertIn("frozen bootstrap-sources.manifest must stay an ordered subsequence", found)


if __name__ == "__main__":
    unittest.main()
