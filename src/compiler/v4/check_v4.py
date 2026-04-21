from __future__ import annotations

import sys
import shutil
import subprocess
from pathlib import Path


CRATE_ORDER = [
    "freak_span",
    "freak_diag",
    "freak_arena",
    "freak_intern",
    "freak_session",
    "freak_lex",
    "freak_parse",
    "freak_hir",
    "freak_resolve",
    "freak_ty",
    "freak_mir",
    "freak_borrowck",
    "freak_query",
    "freak_driver",
    "freak_editor",
    "freak_snapshot",
    "freak_lsp",
]


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "freakc").is_dir() and (parent / "src" / "compiler" / "v4").is_dir():
            return parent
    raise RuntimeError("could not locate repository root")


ROOT = repo_root()
V4_ROOT = ROOT / "src" / "compiler" / "v4"
CRATES_ROOT = V4_ROOT / "crates"
TESTS_ROOT = V4_ROOT / "tests"
RUNTIME_ROOT = ROOT / "freakc" / "runtime"
RUNTIME_BUILD_ROOT = ROOT / "build" / "v4_smoke"

EXECUTABLE_SMOKES = [
    {
        "name": "query invalidation",
        "fixture": "query_invalidation_smoke.fk",
        "expect": [
            "invalidation-contract|path=invalidate.fk",
            "health-diff|",
            "lex-invalidations-added=",
            "editor-invalidations-added=",
        ],
    },
    {
        "name": "LSP dispatch",
        "fixture": "lsp_dispatch_smoke.fk",
        "expect": [
            "ok|initialize",
            "ok|textDocument/didOpen",
            "ok|textDocument/hover",
            "invalidation-contract|path=dispatch.fk",
            "error|unknown/method|-32601|method not found",
        ],
    },
    {
        "name": "unit snapshot restore/diff/health",
        "fixture": "unit_snapshot_smoke.fk",
        "expect": [
            "00-unit-snapshot-restore ok=1",
            "00-unit-diff|format=freak-00-unit-snapshot-diff-v1",
            "00-unit-health|format=freak-00-unit-health-v1",
            "health-diff|",
            "ok|workspace/unitSnapshotRestore",
        ],
    },
    {
        "name": "MIR loop desugaring",
        "fixture": "mir_loop_desugar_smoke.fk",
        "expect": [
            "for-stmt-kind=Loop",
            "for-stmt-lhs=item",
            "for-stmt-rhs=squad",
            "for-block-cond=for each item in squad",
            "training-stmt-kind=Loop",
            "training-stmt-lhs=power >= 8",
            "training-stmt-rhs=max 4",
            "training-block-cond=training arc until power >= 8 max 4 with growth",
            "loop-diagnostics=0",
            "bad-growth-diagnostics=1",
            "bad-growth-message=training arc with growth must mutate condition subject",
        ],
    },
    {
        "name": "typed task signatures",
        "fixture": "ty_smoke.fk",
        "expect": [
            "main-signature=task main(...) -> int",
            "helper-signature=task helper(...) -> word",
            "flag-signature=task flag(...) -> bool",
            "main-return=int",
            "helper-return=word",
            "flag-return=bool",
            "signature-count=5",
        ],
    },
    {
        "name": "MIR call return typing",
        "fixture": "mir_call_return_smoke.fk",
        "expect": [
            "helper-param-count=1",
            "helper-param0-name=power",
            "helper-param0-type=int",
            "helper-body-locals=1",
            "helper-local0-name=power",
            "helper-local0-ty=int",
            "helper-return-rvalue-kind=UseLocal",
            "helper-return-rvalue-ty=int",
            "helper-return-place-ty=int",
            "call-rvalue-kind=Call",
            "call-rvalue-text=helper ( 7 )",
            "call-rvalue-op=helper",
            "call-rvalue-ty=int",
            "call-local-ty=int",
            "return-rvalue-kind=UseLocal",
            "return-rvalue-ty=int",
            "return-place-ty=int",
            "good-diagnostics=0",
            "bad-return-diagnostics=1",
            "bad-return-message=return type mismatch",
            "bad-return-help=bad expects int but got word",
            "bad-arity-diagnostics=1",
            "bad-arity-message=call arity mismatch",
            "bad-arity-help=helper expects 1 arguments but got 0",
            "bad-arg-diagnostics=1",
            "bad-arg-message=call argument type mismatch",
            "bad-arg-help=helper argument 1 expects int but got word",
        ],
    },
    {
        "name": "MIR local declaration typing",
        "fixture": "mir_local_decl_smoke.fk",
        "expect": [
            "decl-local0-name=x",
            "decl-local0-ty=int",
            "decl-local0-rvalue-ty=int",
            "decl-local0-place-ty=int",
            "decl-local1-name=mood",
            "decl-local1-ty=word",
            "decl-local1-rvalue-ty=word",
            "decl-local1-place-ty=word",
            "decl-good-diagnostics=0",
            "decl-bad-diagnostics=1",
            "decl-bad-message=local declaration type mismatch",
            "decl-bad-help=x expects int but got word",
        ],
    },
    {
        "name": "MIR typed assignment",
        "fixture": "mir_assignment_smoke.fk",
        "expect": [
            "assign-body-locals=2",
            "assign-local0-name=power",
            "assign-local0-ty=int",
            "assign-local1-name=x",
            "assign-local1-ty=int",
            "assign-param-stmt-kind=Assign",
            "assign-param-lhs=power",
            "assign-param-rhs=8",
            "assign-param-place-ty=int",
            "assign-param-rvalue-ty=int",
            "assign-compound-stmt-kind=Assign",
            "assign-compound-lhs=x",
            "assign-compound-rhs=2",
            "assign-compound-place-ty=int",
            "assign-compound-rvalue-ty=int",
            "assign-good-diagnostics=0",
            "bad-param-assign-diagnostics=1",
            "bad-param-assign-message=assignment type mismatch",
            "bad-param-assign-help=cannot assign word into int",
            "bad-local-update-diagnostics=1",
            "bad-local-update-message=invalid binary operation",
            "bad-local-update-help=Add between int and word",
        ],
    },
    {
        "name": "MIR modulo typing",
        "fixture": "mir_mod_smoke.fk",
        "expect": [
            "mod-body-locals=3",
            "mod-local0-name=power",
            "mod-local0-ty=int",
            "mod-local1-name=left",
            "mod-local1-ty=int",
            "mod-local2-name=result",
            "mod-local2-ty=int",
            "mod-binary-stmt-kind=LocalInit",
            "mod-binary-lhs=result",
            "mod-binary-rhs=left % 4",
            "mod-binary-rvalue-kind=Binary",
            "mod-binary-op=Mod",
            "mod-binary-ty=int",
            "mod-update-stmt-kind=Assign",
            "mod-update-lhs=result",
            "mod-update-rhs=2",
            "mod-update-place-ty=int",
            "mod-update-rvalue-ty=int",
            "mod-good-diagnostics=0",
            "bad-mod-diagnostics=1",
            "bad-mod-message=invalid binary operation",
            "bad-mod-help=Mod between word and int",
            "bad-mod-update-diagnostics=1",
            "bad-mod-update-message=invalid binary operation",
            "bad-mod-update-help=Mod between int and word",
        ],
    },
    {
        "name": "MIR unary negation",
        "fixture": "mir_unary_smoke.fk",
        "expect": [
            "unary-body-locals=4",
            "unary-local0-name=power",
            "unary-local0-ty=int",
            "unary-local1-name=x",
            "unary-local1-ty=int",
            "unary-literal-kind=Unary",
            "unary-literal-op=Neg",
            "unary-literal-ty=int",
            "unary-literal-operand-kind=ConstInt",
            "unary-literal-operand-ty=int",
            "unary-local-kind=Unary",
            "unary-local-op=Neg",
            "unary-local-ty=int",
            "unary-local-operand-kind=UseLocal",
            "unary-local-operand-ty=int",
            "unary-binary-kind=Binary",
            "unary-binary-op=Add",
            "unary-binary-ty=int",
            "unary-binary-rhs-kind=Unary",
            "unary-binary-rhs-ty=int",
            "unary-good-diagnostics=0",
            "bad-unary-diagnostics=1",
            "bad-unary-message=invalid unary operation",
            "bad-unary-help=Neg on word",
        ],
    },
    {
        "name": "MIR boolean unary not",
        "fixture": "mir_not_smoke.fk",
        "expect": [
            "not-body-locals=4",
            "not-local0-name=flag",
            "not-local0-ty=bool",
            "not-local1-name=ready",
            "not-local1-ty=bool",
            "not-keyword-kind=Unary",
            "not-keyword-op=Not",
            "not-keyword-ty=bool",
            "not-keyword-operand-kind=UseLocal",
            "not-keyword-operand-ty=bool",
            "not-bang-kind=Unary",
            "not-bang-op=Not",
            "not-bang-ty=bool",
            "not-bang-operand-kind=UseLocal",
            "not-bang-operand-ty=bool",
            "not-literal-kind=Unary",
            "not-literal-op=Not",
            "not-literal-ty=bool",
            "not-literal-operand-kind=ConstBool",
            "not-literal-operand-ty=bool",
            "not-good-diagnostics=0",
            "bad-not-diagnostics=1",
            "bad-not-message=invalid unary operation",
            "bad-not-help=Not on int",
            "bad-bang-diagnostics=1",
            "bad-bang-message=invalid unary operation",
            "bad-bang-help=Not on word",
        ],
    },
    {
        "name": "MIR boolean binary operators",
        "fixture": "mir_bool_binary_smoke.fk",
        "expect": [
            "bool-binary-body-locals=6",
            "bool-binary-local0-name=left",
            "bool-binary-local0-ty=bool",
            "bool-binary-local3-name=both",
            "bool-binary-local3-ty=bool",
            "bool-binary-and-kind=Binary",
            "bool-binary-and-op=And",
            "bool-binary-and-ty=bool",
            "bool-binary-and-lhs-kind=UseLocal",
            "bool-binary-and-lhs-ty=bool",
            "bool-binary-and-rhs-kind=UseLocal",
            "bool-binary-and-rhs-ty=bool",
            "bool-binary-or-kind=Binary",
            "bool-binary-or-op=Or",
            "bool-binary-or-ty=bool",
            "bool-binary-or-lhs-kind=UseLocal",
            "bool-binary-or-lhs-ty=bool",
            "bool-binary-or-rhs-kind=UseLocal",
            "bool-binary-or-rhs-ty=bool",
            "bool-binary-guard-kind=Binary",
            "bool-binary-guard-op=And",
            "bool-binary-guard-ty=bool",
            "bool-binary-guard-lhs-kind=Binary",
            "bool-binary-guard-lhs-op=Gt",
            "bool-binary-guard-lhs-ty=bool",
            "bool-binary-guard-rhs-kind=UseLocal",
            "bool-binary-guard-rhs-ty=bool",
            "bool-binary-good-diagnostics=0",
            "bad-and-diagnostics=1",
            "bad-and-message=invalid binary operation",
            "bad-and-help=And between bool and int",
            "bad-or-diagnostics=1",
            "bad-or-message=invalid binary operation",
            "bad-or-help=Or between word and bool",
        ],
    },
    {
        "name": "MIR parenthesized expressions",
        "fixture": "mir_grouping_smoke.fk",
        "expect": [
            "group-body-locals=5",
            "group-local0-name=power",
            "group-local0-ty=int",
            "group-local2-name=x",
            "group-local2-ty=int",
            "group-sum-kind=Binary",
            "group-sum-op=Add",
            "group-sum-ty=int",
            "group-sum-lhs-kind=UseLocal",
            "group-sum-lhs-ty=int",
            "group-sum-rhs-kind=ConstInt",
            "group-sum-rhs-ty=int",
            "group-mul-kind=Binary",
            "group-mul-op=Mul",
            "group-mul-ty=int",
            "group-mul-rhs-kind=Binary",
            "group-mul-rhs-op=Add",
            "group-mul-rhs-ty=int",
            "group-not-kind=Unary",
            "group-not-op=Not",
            "group-not-ty=bool",
            "group-not-operand-kind=Binary",
            "group-not-operand-op=And",
            "group-not-operand-ty=bool",
            "group-good-diagnostics=0",
            "bad-group-diagnostics=1",
            "bad-group-message=invalid binary operation",
            "bad-group-help=Add between int and word",
        ],
    },
    {
        "name": "MIR typed if conditions",
        "fixture": "mir_if_condition_smoke.fk",
        "expect": [
            "if-body-blocks=4",
            "if-entry-term=If",
            "if-entry-cond=power > 4 and ( ready or false )",
            "if-entry-target=1",
            "if-entry-else=3",
            "if-branch-stmt-kind=Branch",
            "if-branch-lhs=power > 4 and ( ready or false )",
            "if-branch-rvalue-kind=Binary",
            "if-branch-rvalue-op=And",
            "if-branch-rvalue-ty=bool",
            "if-branch-lhs-kind=Binary",
            "if-branch-lhs-op=Gt",
            "if-branch-lhs-ty=bool",
            "if-branch-rhs-kind=Binary",
            "if-branch-rhs-op=Or",
            "if-branch-rhs-ty=bool",
            "if-good-diagnostics=0",
            "bad-if-diagnostics=1",
            "bad-if-message=if condition must be bool",
            "bad-if-help=got int",
        ],
    },
    {
        "name": "MIR typed loop conditions",
        "fixture": "mir_loop_condition_smoke.fk",
        "expect": [
            "loop-cond-body-blocks=5",
            "repeat-block-term=If",
            "repeat-block-cond=until power > 4 and ready",
            "repeat-stmt-kind=Loop",
            "repeat-stmt-lhs=power > 4 and ready",
            "repeat-stmt-rvalue-kind=Binary",
            "repeat-stmt-rvalue-op=And",
            "repeat-stmt-rvalue-ty=bool",
            "repeat-lhs-kind=Binary",
            "repeat-lhs-op=Gt",
            "repeat-lhs-ty=bool",
            "repeat-rhs-kind=UseLocal",
            "repeat-rhs-ty=bool",
            "training-cond-block-term=If",
            "training-cond-block-cond=training arc until power >= 8 or ready max 4",
            "training-cond-stmt-kind=Loop",
            "training-cond-stmt-lhs=power >= 8 or ready",
            "training-cond-stmt-rvalue-kind=Binary",
            "training-cond-stmt-rvalue-op=Or",
            "training-cond-stmt-rvalue-ty=bool",
            "training-cond-lhs-kind=Binary",
            "training-cond-lhs-op=Ge",
            "training-cond-lhs-ty=bool",
            "training-cond-rhs-kind=UseLocal",
            "training-cond-rhs-ty=bool",
            "loop-cond-good-diagnostics=0",
            "bad-repeat-diagnostics=1",
            "bad-repeat-message=repeat-until condition must be bool",
            "bad-repeat-help=got int",
            "bad-training-diagnostics=1",
            "bad-training-message=training-arc condition must be bool",
            "bad-training-help=got int",
            "bad-training-max-diagnostics=1",
            "bad-training-max-message=training arc max sessions must be numeric",
            "bad-training-max-help=got bool",
        ],
    },
    {
        "name": "MIR repeat-N-times lowering",
        "fixture": "mir_repeat_times_smoke.fk",
        "expect": [
            "times-body-blocks=3",
            "times-entry-term=If",
            "times-entry-cond=_repeat_i > 0",
            "times-loop-stmt-kind=Loop",
            "times-loop-stmt-lhs=repeat n times",
            "times-loop-rvalue-kind=Binary",
            "times-loop-rvalue-op=Gt",
            "times-loop-rvalue-ty=bool",
            "times-good-diagnostics=0",
            "bad-times-diagnostics=1",
            "bad-times-message=repeat N times count must be int",
            "bad-times-help=got bool",
        ],
    },
    {
        "name": "MIR when statement lowering",
        "fixture": "mir_when_smoke.fk",
        "expect": [
            "when-body-blocks=7",
            "when-entry-term=If",
            "when-entry-cond=score == 100",
            "when-arm0-branch-kind=Branch",
            "when-arm0-branch-lhs=score == 100",
            "when-arm0-rvalue-kind=Binary",
            "when-arm0-rvalue-op=Eq",
            "when-arm0-rvalue-ty=bool",
            "when-arm1-branch-kind=Branch",
            "when-arm1-branch-lhs=score == 90",
            "when-arm1-rvalue-kind=Binary",
            "when-arm1-rvalue-op=Eq",
            "when-arm1-rvalue-ty=bool",
            "when-good-diagnostics=0",
            "bad-when-diagnostics=1",
            "bad-when-message=when arm pattern type mismatch",
            "bad-when-help=scrutinee is int but pattern is bool",
        ],
    },
    {
        "name": "MIR field and index places",
        "fixture": "mir_smoke.fk",
        "expect": [
            "main-stmts=13",
            "main-locals=6",
            "first-local=x",
            "first-local-ty=int",
            "stmt1-rvalue-kind=Binary",
            "stmt1-rvalue-op=Add",
            "stmt1-rvalue-ty=int",
            "field-place-kind=Field",
            "field-place-name=hp",
            "index-place-kind=Index",
            "body-count=2",
        ],
    },
    {
        "name": "MIR typed field and index access",
        "fixture": "mir_place_type_smoke.fk",
        "expect": [
            "shape-field-count=2",
            "shape-field0-name=hp",
            "shape-field0-type=int",
            "shape-field1-name=callsign",
            "shape-field1-type=word",
            "place-body-locals=4",
            "place-local0-name=ship",
            "place-local0-ty=Pilot",
            "place-local1-name=items",
            "place-local1-ty=List<int>",
            "hp-read-kind=UsePlace",
            "hp-read-ty=int",
            "first-read-kind=UsePlace",
            "first-read-ty=int",
            "assign-place-kind=Field",
            "assign-place-field=hp",
            "assign-place-ty=int",
            "assign-rvalue-kind=Binary",
            "assign-rvalue-op=Add",
            "assign-rvalue-ty=int",
            "return-place-kind=UsePlace",
            "return-place-ty=int",
            "place-good-diagnostics=0",
            "bad-field-diagnostics=1",
            "bad-field-message=unknown field access",
            "bad-field-help=Pilot has no field speed",
            "bad-index-target-diagnostics=1",
            "bad-index-target-message=index target not indexable",
            "bad-index-target-help=int is not indexable",
            "bad-index-expr-diagnostics=1",
            "bad-index-expr-message=index expression must be numeric",
            "bad-index-expr-help=got word",
        ],
    },
    {
        "name": "MIR field and index mutation",
        "fixture": "mir_place_mutation_smoke.fk",
        "expect": [
            "mutation-body-locals=2",
            "mutation-field-place-kind=Field",
            "mutation-field-place-field=hp",
            "mutation-field-place-ty=int",
            "mutation-field-rvalue-kind=Binary",
            "mutation-field-rvalue-op=Add",
            "mutation-field-rvalue-ty=int",
            "mutation-field-lhs-kind=UsePlace",
            "mutation-field-lhs-ty=int",
            "mutation-field-rhs-kind=ConstInt",
            "mutation-field-rhs-ty=int",
            "mutation-index-assign-place-kind=Index",
            "mutation-index-assign-place-ty=int",
            "mutation-index-assign-index-kind=ConstInt",
            "mutation-index-assign-index-ty=int",
            "mutation-index-assign-rvalue-kind=UsePlace",
            "mutation-index-assign-rvalue-ty=int",
            "mutation-index-update-place-kind=Index",
            "mutation-index-update-place-ty=int",
            "mutation-index-update-index-kind=ConstInt",
            "mutation-index-update-index-ty=int",
            "mutation-index-update-rvalue-kind=Binary",
            "mutation-index-update-rvalue-op=Add",
            "mutation-index-update-rvalue-ty=int",
            "mutation-index-update-lhs-kind=UsePlace",
            "mutation-index-update-lhs-ty=int",
            "mutation-index-update-rhs-kind=UsePlace",
            "mutation-index-update-rhs-ty=int",
            "mutation-good-diagnostics=0",
            "mutation-bad-field-type-diagnostics=1",
            "mutation-bad-field-type-message=field write type mismatch",
            "mutation-bad-field-type-help=hp on Pilot expects int but got word",
            "mutation-bad-index-type-diagnostics=1",
            "mutation-bad-index-type-message=indexed write type mismatch",
            "mutation-bad-index-type-help=element of List<int> expects int but got word",
            "mutation-bad-field-compound-diagnostics=1",
            "mutation-bad-field-compound-message=invalid binary operation",
            "mutation-bad-field-compound-help=Add between word and int",
            "mutation-bad-index-target-diagnostics=1",
            "mutation-bad-index-target-message=index target not indexable",
            "mutation-bad-index-target-help=int is not indexable",
            "mutation-bad-index-expr-diagnostics=1",
            "mutation-bad-index-expr-message=index expression must be numeric",
            "mutation-bad-index-expr-help=got word",
        ],
    },
    {
        "name": "MIR list literals",
        "fixture": "mir_list_literal_smoke.fk",
        "expect": [
            "list-body-locals=4",
            "list-local0-name=squad",
            "list-local0-ty=List<int>",
            "list-local1-name=mix",
            "list-local1-ty=List<num>",
            "list-local2-name=nested",
            "list-local2-ty=List<List<int>>",
            "list-local3-name=second",
            "list-local3-ty=int",
            "squad-rvalue-kind=List",
            "squad-rvalue-op=List",
            "squad-rvalue-ty=List<int>",
            "mix-rvalue-kind=List",
            "mix-rvalue-ty=List<num>",
            "nested-rvalue-kind=List",
            "nested-rvalue-ty=List<List<int>>",
            "second-rvalue-kind=UsePlace",
            "second-rvalue-ty=int",
            "list-good-diagnostics=0",
            "list-bad-mixed-diagnostics=1",
            "list-bad-mixed-message=list element drift",
            "list-bad-mixed-help=element 2 wants int but got word",
            "list-bad-empty-diagnostics=1",
            "list-bad-empty-message=empty list literal needs type context",
            "list-bad-empty-help=write a typed destination like pilot squad: List<int> = []",
        ],
    },
    {
        "name": "MIR fixed array literals",
        "fixture": "mir_array_literal_smoke.fk",
        "expect": [
            "array-take-locals=1",
            "array-take-local0-name=values",
            "array-take-local0-ty=[int;3]",
            "array-take-return-kind=UsePlace",
            "array-take-return-ty=int",
            "array-make-return-kind=Array",
            "array-make-return-ty=[int;2]",
            "array-main-locals=8",
            "array-main-local0-name=trio",
            "array-main-local0-ty=[int;3]",
            "array-main-local1-name=levels",
            "array-main-local1-ty=[num;3]",
            "array-main-local2-name=zeros",
            "array-main-local2-ty=[int;4]",
            "array-main-local3-name=grid",
            "array-main-local3-ty=[[num;2];2]",
            "array-main-local4-name=echoed",
            "array-main-local4-ty=int",
            "array-main-local5-name=made",
            "array-main-local5-ty=[int;2]",
            "array-main-local6-name=corner",
            "array-main-local6-ty=num",
            "array-main-local7-name=second",
            "array-main-local7-ty=int",
            "array-trio-element-ty=int",
            "array-trio-length=3",
            "array-grid-element-ty=[num;2]",
            "array-grid-length=2",
            "array-trio-rvalue-kind=Array",
            "array-trio-rvalue-ty=[int;3]",
            "array-levels-rvalue-kind=Array",
            "array-levels-rvalue-ty=[num;3]",
            "array-zeros-rvalue-kind=Array",
            "array-zeros-rvalue-ty=[int;4]",
            "array-grid-rvalue-kind=Array",
            "array-grid-rvalue-ty=[[num;2];2]",
            "array-made-rvalue-kind=Call",
            "array-made-rvalue-ty=[int;2]",
            "array-assign-place-kind=Local",
            "array-assign-place-ty=[int;3]",
            "array-assign-rvalue-kind=Array",
            "array-assign-rvalue-ty=[int;3]",
            "array-corner-rvalue-kind=UsePlace",
            "array-corner-rvalue-ty=num",
            "array-second-rvalue-kind=UsePlace",
            "array-second-rvalue-ty=int",
            "array-return-rvalue-kind=Binary",
            "array-return-rvalue-op=Add",
            "array-return-rvalue-ty=int",
            "array-good-diagnostics=0",
            "array-bad-length-diagnostics=1",
            "array-bad-length-message=array length mismatch",
            "array-bad-length-help=[int;3] expects 3 elements but got 2",
            "array-bad-element-diagnostics=1",
            "array-bad-element-message=array element drift",
            "array-bad-element-help=element 2 wants int but got word",
            "array-bad-repeat-type-diagnostics=1",
            "array-bad-repeat-type-message=array repeat count must be int",
            "array-bad-repeat-type-help=got bool",
            "array-bad-repeat-const-diagnostics=1",
            "array-bad-repeat-const-message=array repeat count must be constant",
            "array-bad-repeat-const-help=use a literal length like 4",
            "array-bad-repeat-negative-diagnostics=1",
            "array-bad-repeat-negative-message=array repeat count must be non-negative",
            "array-bad-repeat-negative-help=got -1",
        ],
    },
    {
        "name": "MIR tuple literals",
        "fixture": "mir_tuple_literal_smoke.fk",
        "expect": [
            "tuple-body-locals=3",
            "tuple-local0-name=pair",
            "tuple-local0-ty=(int,word)",
            "tuple-local1-name=trio",
            "tuple-local1-ty=(int,num,bool)",
            "tuple-local2-name=nested",
            "tuple-local2-ty=((int,int),word)",
            "pair-rvalue-kind=Tuple",
            "pair-rvalue-op=Tuple",
            "pair-rvalue-ty=(int,word)",
            "trio-rvalue-kind=Tuple",
            "trio-rvalue-ty=(int,num,bool)",
            "nested-rvalue-kind=Tuple",
            "nested-rvalue-ty=((int,int),word)",
            "tuple-good-diagnostics=0",
            "tuple-bad-mismatch-diagnostics=1",
            "tuple-bad-mismatch-message=local declaration type mismatch",
            "tuple-bad-mismatch-help=pair expects (int,word) but got (int,int)",
            "tuple-bad-slot-diagnostics=1",
            "tuple-bad-slot-message=tuple slot missing",
            "tuple-bad-slot-help=expected another element after ','",
        ],
    },
    {
        "name": "MIR tuple access and mutation",
        "fixture": "mir_tuple_access_smoke.fk",
        "expect": [
            "tuple-access-body-locals=5",
            "tuple-access-local0-name=pair",
            "tuple-access-local0-ty=(int,word)",
            "tuple-access-local1-name=left",
            "tuple-access-local1-ty=int",
            "tuple-access-local2-name=label",
            "tuple-access-local2-ty=word",
            "tuple-access-local3-name=nested",
            "tuple-access-local3-ty=((int,int),word)",
            "tuple-access-local4-name=inner",
            "tuple-access-local4-ty=int",
            "pair-slot-count=2",
            "pair-slot0-ty=int",
            "pair-slot1-ty=word",
            "nested-slot0-ty=(int,int)",
            "nested-slot1-ty=word",
            "tuple-access-pair-rvalue-kind=Tuple",
            "tuple-access-pair-rvalue-ty=(int,word)",
            "tuple-access-left-rvalue-kind=UsePlace",
            "tuple-access-left-rvalue-ty=int",
            "tuple-access-left-place-kind=Field",
            "tuple-access-left-place-field=0",
            "tuple-access-left-place-ty=int",
            "tuple-access-label-rvalue-kind=UsePlace",
            "tuple-access-label-rvalue-ty=word",
            "tuple-access-label-place-field=1",
            "tuple-access-label-place-ty=word",
            "tuple-access-nested-rvalue-kind=Tuple",
            "tuple-access-nested-rvalue-ty=((int,int),word)",
            "tuple-access-inner-rvalue-kind=UsePlace",
            "tuple-access-inner-rvalue-ty=int",
            "tuple-access-inner-place-field=1",
            "tuple-access-inner-place-ty=int",
            "tuple-access-inner-base-kind=Field",
            "tuple-access-inner-base-field=0",
            "tuple-access-inner-base-ty=(int,int)",
            "tuple-access-assign-place-kind=Field",
            "tuple-access-assign-place-field=0",
            "tuple-access-assign-place-ty=int",
            "tuple-access-assign-rvalue-kind=Binary",
            "tuple-access-assign-rvalue-op=Add",
            "tuple-access-assign-rvalue-ty=int",
            "tuple-access-return-rvalue-kind=UseLocal",
            "tuple-access-return-rvalue-ty=int",
            "tuple-access-good-diagnostics=0",
            "tuple-access-bad-range-diagnostics=1",
            "tuple-access-bad-range-message=tuple slot out of range",
            "tuple-access-bad-range-help=(int,word) has no slot 2",
            "tuple-access-bad-non-tuple-diagnostics=1",
            "tuple-access-bad-non-tuple-message=tuple slot access on non-tuple type",
            "tuple-access-bad-non-tuple-help=int has no tuple slots",
            "tuple-access-bad-named-slot-diagnostics=1",
            "tuple-access-bad-named-slot-message=tuple slot must be int literal",
            "tuple-access-bad-named-slot-help=use .0, .1, ... on (int,word)",
        ],
    },
    {
        "name": "MIR tuple destructuring",
        "fixture": "mir_tuple_destructure_smoke.fk",
        "expect": [
            "tuple-destructure-body-locals=7",
            "tuple-destructure-body-stmts=8",
            "tuple-destructure-local0-name=pair",
            "tuple-destructure-local0-ty=(int,word)",
            "tuple-destructure-local1-name=_tuple_unpack",
            "tuple-destructure-local1-ty=(int,word)",
            "tuple-destructure-local2-name=left",
            "tuple-destructure-local2-ty=int",
            "tuple-destructure-local3-name=label",
            "tuple-destructure-local3-ty=word",
            "tuple-destructure-local4-name=_tuple_unpack2",
            "tuple-destructure-local4-ty=((int,int),word)",
            "tuple-destructure-local5-name=x",
            "tuple-destructure-local5-ty=int",
            "tuple-destructure-local6-name=y",
            "tuple-destructure-local6-ty=int",
            "tuple-destructure-stmt1-kind=LocalInit",
            "tuple-destructure-stmt1-lhs=_tuple_unpack",
            "tuple-destructure-stmt4-kind=LocalInit",
            "tuple-destructure-stmt4-lhs=_tuple_unpack2",
            "tuple-destructure-pair-rvalue-kind=Tuple",
            "tuple-destructure-pair-rvalue-ty=(int,word)",
            "tuple-destructure-temp1-rvalue-kind=UseLocal",
            "tuple-destructure-temp1-rvalue-ty=(int,word)",
            "tuple-destructure-left-rvalue-kind=UsePlace",
            "tuple-destructure-left-rvalue-ty=int",
            "tuple-destructure-left-place-field=0",
            "tuple-destructure-left-place-ty=int",
            "tuple-destructure-label-rvalue-kind=UsePlace",
            "tuple-destructure-label-rvalue-ty=word",
            "tuple-destructure-label-place-field=1",
            "tuple-destructure-label-place-ty=word",
            "tuple-destructure-temp2-rvalue-kind=Tuple",
            "tuple-destructure-temp2-rvalue-ty=((int,int),word)",
            "tuple-destructure-x-rvalue-kind=UsePlace",
            "tuple-destructure-x-rvalue-ty=int",
            "tuple-destructure-x-place-field=0",
            "tuple-destructure-x-place-ty=int",
            "tuple-destructure-x-base-field=0",
            "tuple-destructure-x-base-ty=(int,int)",
            "tuple-destructure-y-rvalue-kind=UsePlace",
            "tuple-destructure-y-rvalue-ty=int",
            "tuple-destructure-y-place-field=1",
            "tuple-destructure-y-place-ty=int",
            "tuple-destructure-y-base-field=0",
            "tuple-destructure-y-base-ty=(int,int)",
            "tuple-destructure-return-rvalue-kind=Binary",
            "tuple-destructure-return-rvalue-op=Add",
            "tuple-destructure-return-rvalue-ty=int",
            "tuple-destructure-good-diagnostics=0",
            "tuple-destructure-bad-non-tuple-diagnostics=1",
            "tuple-destructure-bad-non-tuple-message=tuple destructure needs tuple source",
            "tuple-destructure-bad-non-tuple-help=got int",
            "tuple-destructure-bad-arity-diagnostics=1",
            "tuple-destructure-bad-arity-message=tuple destructure arity mismatch",
            "tuple-destructure-bad-arity-help=pattern wants 3 slots but source has 2",
            "tuple-destructure-bad-duplicate-diagnostics=1",
            "tuple-destructure-bad-duplicate-message=tuple destructure duplicate binding",
            "tuple-destructure-bad-duplicate-help=a already exists in this scope",
            "tuple-destructure-bad-type-diagnostics=1",
            "tuple-destructure-bad-type-message=tuple destructure type mismatch",
            "tuple-destructure-bad-type-help=pattern expects (int,word) but got (int,int)",
        ],
    },
    {
        "name": "MIR map literals",
        "fixture": "mir_map_literal_smoke.fk",
        "expect": [
            "map-body-locals=4",
            "map-local0-name=fleet",
            "map-local0-ty=Map<word,int>",
            "map-local1-name=scaled",
            "map-local1-ty=Map<int,num>",
            "map-local2-name=nested",
            "map-local2-ty=Map<word,Map<word,int>>",
            "map-local3-name=ship",
            "map-local3-ty=Pilot",
            "fleet-rvalue-kind=Map",
            "fleet-rvalue-op=Map",
            "fleet-rvalue-ty=Map<word,int>",
            "scaled-rvalue-kind=Map",
            "scaled-rvalue-ty=Map<int,num>",
            "nested-rvalue-kind=Map",
            "nested-rvalue-ty=Map<word,Map<word,int>>",
            "ship-rvalue-kind=Construct",
            "ship-rvalue-ty=Pilot",
            "map-good-diagnostics=0",
            "map-bad-key-diagnostics=1",
            "map-bad-key-message=map key drift",
            "map-bad-key-help=entry 2 wants key word but got int",
            "map-bad-value-diagnostics=1",
            "map-bad-value-message=map value drift",
            "map-bad-value-help=entry 2 wants value int but got word",
            "map-bad-empty-diagnostics=1",
            "map-bad-empty-message=empty map literal needs type context",
            "map-bad-empty-help=annotate the destination, for example pilot lookup: Map<word,int>",
        ],
    },
    {
        "name": "MIR map access and mutation",
        "fixture": "mir_map_access_smoke.fk",
        "expect": [
            "map-access-body-locals=4",
            "map-access-local0-name=lookup",
            "map-access-local0-ty=Map<word,int>",
            "map-access-local1-name=nested",
            "map-access-local1-ty=Map<word,Map<word,int>>",
            "map-access-local2-name=alpha",
            "map-access-local2-ty=int",
            "map-access-local3-name=front",
            "map-access-local3-ty=int",
            "map-access-lookup-rvalue-kind=Map",
            "map-access-lookup-rvalue-ty=Map<word,int>",
            "map-access-nested-rvalue-kind=Map",
            "map-access-nested-rvalue-ty=Map<word,Map<word,int>>",
            "map-access-lookup-key-ty=word",
            "map-access-lookup-value-ty=int",
            "map-access-nested-value-ty=Map<word,int>",
            "map-access-alpha-rvalue-kind=UsePlace",
            "map-access-alpha-rvalue-ty=int",
            "map-access-alpha-place-kind=Index",
            "map-access-alpha-place-ty=int",
            "map-access-alpha-key-kind=ConstWord",
            "map-access-alpha-key-ty=word",
            "map-access-front-rvalue-kind=UsePlace",
            "map-access-front-rvalue-ty=int",
            "map-access-front-place-kind=Index",
            "map-access-front-place-ty=int",
            "map-access-front-key-kind=ConstWord",
            "map-access-front-key-ty=word",
            "map-access-assign-place-kind=Index",
            "map-access-assign-place-ty=int",
            "map-access-assign-key-kind=ConstWord",
            "map-access-assign-key-ty=word",
            "map-access-assign-rvalue-kind=Binary",
            "map-access-assign-rvalue-op=Add",
            "map-access-assign-rvalue-ty=int",
            "map-access-return-rvalue-kind=UsePlace",
            "map-access-return-rvalue-ty=int",
            "map-access-good-diagnostics=0",
            "map-access-bad-key-read-diagnostics=1",
            "map-access-bad-key-read-message=map key type mismatch",
            "map-access-bad-key-read-help=Map<word,int> wants key word but got int",
            "map-access-bad-key-write-diagnostics=1",
            "map-access-bad-key-write-message=map key type mismatch",
            "map-access-bad-key-write-help=Map<word,int> wants key word but got bool",
            "map-access-bad-value-write-diagnostics=1",
            "map-access-bad-value-write-message=indexed write type mismatch",
            "map-access-bad-value-write-help=element of Map<word,int> expects int but got word",
        ],
    },
    {
        "name": "MIR shape construction",
        "fixture": "mir_shape_ctor_smoke.fk",
        "expect": [
            "shape-ctor-body-locals=2",
            "shape-ctor-local0-name=ship",
            "shape-ctor-local0-ty=Pilot",
            "shape-ctor-local1-name=power",
            "shape-ctor-local1-ty=int",
            "shape-ctor-rvalue-kind=Construct",
            "shape-ctor-rvalue-op=Pilot",
            "shape-ctor-rvalue-ty=Pilot",
            "shape-ctor-place-ty=Pilot",
            "shape-ctor-power-kind=UsePlace",
            "shape-ctor-power-ty=int",
            "shape-ctor-power-place-ty=int",
            "shape-ctor-return-kind=UseLocal",
            "shape-ctor-return-ty=int",
            "shape-ctor-good-diagnostics=0",
            "shape-ctor-bad-field-diagnostics=1",
            "shape-ctor-bad-field-message=unknown shape field",
            "shape-ctor-bad-field-help=Pilot has no field speed",
            "shape-ctor-missing-field-diagnostics=1",
            "shape-ctor-missing-field-message=missing shape field",
            "shape-ctor-missing-field-help=Pilot requires field callsign",
            "shape-ctor-duplicate-field-diagnostics=1",
            "shape-ctor-duplicate-field-message=duplicate shape field",
            "shape-ctor-duplicate-field-help=hp already set on Pilot",
            "shape-ctor-bad-type-diagnostics=1",
            "shape-ctor-bad-type-message=shape field type mismatch",
            "shape-ctor-bad-type-help=Pilot.hp expects int but got word",
            "shape-ctor-unknown-shape-diagnostics=1",
            "shape-ctor-unknown-shape-message=unknown shape constructor",
            "shape-ctor-unknown-shape-help=Ace is not a known shape",
        ],
    },
    {
        "name": "MIR impl and associated method calls",
        "fixture": "mir_method_call_smoke.fk",
        "expect": [
            "method-body-count=3",
            "boost-body-found=yes",
            "ace-body-found=yes",
            "boost-body-locals=2",
            "boost-local0-name=self",
            "boost-local0-ty=Pilot",
            "boost-local1-name=bonus",
            "boost-local1-ty=int",
            "boost-return-kind=Binary",
            "boost-return-op=Add",
            "boost-return-ty=int",
            "boost-return-lhs-kind=UsePlace",
            "boost-return-lhs-ty=int",
            "ace-body-locals=1",
            "ace-local0-name=callsign",
            "ace-local0-ty=word",
            "ace-return-kind=Construct",
            "ace-return-ty=Pilot",
            "method-main-locals=3",
            "method-main-local1-name=boosted",
            "method-main-local1-ty=int",
            "method-main-local2-name=ace",
            "method-main-local2-ty=Pilot",
            "instance-call-kind=Call",
            "instance-call-op=Pilot.boost",
            "instance-call-ty=int",
            "associated-call-kind=Call",
            "associated-call-op=Pilot::ace",
            "associated-call-ty=Pilot",
            "method-good-diagnostics=0",
            "bad-receiver-static-diagnostics=1",
            "bad-receiver-static-message=method wants associated syntax",
            "bad-receiver-static-help=Pilot::ace is static; call it with :: instead of a receiver",
            "bad-associated-instance-diagnostics=1",
            "bad-associated-instance-message=associated call needs a receiver",
            "bad-associated-instance-help=Pilot::boost is an instance method; call it through a value",
            "bad-missing-diagnostics=1",
            "bad-missing-message=receiver has no matching method",
            "bad-missing-help=Pilot offers no method evade",
            "bad-method-arity-diagnostics=1",
            "bad-method-arity-message=method call arity drift",
            "bad-method-arity-help=Pilot.boost takes 1 explicit arguments but got 0",
            "bad-method-arg-diagnostics=1",
            "bad-method-arg-message=method argument drift",
            "bad-method-arg-help=Pilot.boost argument 1 wants int, but word arrived",
            "bad-static-missing-diagnostics=1",
            "bad-static-missing-message=associated method lookup failed",
            "bad-static-missing-help=Pilot exposes no static method ghost",
        ],
    },
    {
        "name": "MIR snapshot and borrowck restore",
        "fixture": "mir_snapshot_smoke.fk",
        "expect": [
            "mir-snapshot-bytes=",
            "mir-snapshot-restore ok=1",
            "ok|workspace/mirSnapshotRestore",
            "borrowck-ok borrow=",
            "error|workspace/mirSnapshotRestore|-32602|",
        ],
    },
    {
        "name": "Meiya borrow-check scaffold",
        "fixture": "borrowck_smoke.fk",
        "expect": [
            "borrowck-ok borrow=0",
            "main-status=clean",
            "main-paths=25",
            "path0-kind=Write",
            "path0-text=x",
            "result-count=2",
        ],
    },
    {
        "name": "MIR else-if lowering",
        "fixture": "mir_else_if_smoke.fk",
        "expect": [
            "else-if-body-blocks=7",
            "else-if-outer-term=If",
            "else-if-outer-cond=power > 10",
            "else-if-outer-target=1",
            "else-if-outer-else=3",
            "else-if-outer-branch-kind=Branch",
            "else-if-outer-rvalue-kind=Binary",
            "else-if-outer-rvalue-op=Gt",
            "else-if-outer-rvalue-ty=bool",
            "else-if-nested-term=If",
            "else-if-nested-cond=ready",
            "else-if-nested-target=4",
            "else-if-nested-else=6",
            "else-if-nested-branch-kind=Branch",
            "else-if-nested-rvalue-kind=UseLocal",
            "else-if-nested-rvalue-ty=bool",
            "else-if-nested-after-term=Goto",
            "else-if-nested-after-target=2",
            "else-if-final-else-term=Goto",
            "else-if-good-diagnostics=0",
            "bad-else-if-diagnostics=1",
            "bad-else-if-message=if condition must be bool",
            "bad-else-if-help=got int",
        ],
    },
]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from freakc.__main__ import transpile  # noqa: E402
from freakc.parser import Parser  # noqa: E402
from freakc.type_checker import TypeChecker  # noqa: E402


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def crate_path(name: str) -> Path:
    return CRATES_ROOT / name / "src" / "lib.fk"


def crate_paths() -> list[Path]:
    return [crate_path(name) for name in CRATE_ORDER]


def fixture_paths() -> list[Path]:
    if not TESTS_ROOT.exists():
        return []
    return sorted(TESTS_ROOT.glob("*.fk"))


def check_exists(paths: list[Path]) -> None:
    missing = [path for path in paths if not path.exists()]
    if missing:
        for path in missing:
            print(f"missing: {rel(path)}")
        raise SystemExit(1)
    print(f"exists: {len(paths)} files")


def check_ascii(paths: list[Path]) -> None:
    bad: list[Path] = []
    for path in paths:
        try:
            path.read_text(encoding="ascii")
        except UnicodeDecodeError:
            bad.append(path)
    if bad:
        for path in bad:
            print(f"non-ascii: {rel(path)}")
        raise SystemExit(1)
    print(f"ascii: {len(paths)} files")


def parse_source(source: str, label: str):
    try:
        return Parser.from_source(source)
    except Exception as exc:
        print(f"parse failed: {label}")
        print(exc)
        raise SystemExit(1) from exc


def check_individual_parse(paths: list[Path]) -> None:
    for path in paths:
        parse_source(read_text(path), rel(path))
    print(f"parse individual: {len(paths)} files")


def flattened_crates() -> str:
    out: list[str] = []
    for path in crate_paths():
        out.append(f"-- flattened from {rel(path)}\n")
        out.append(read_text(path))
        out.append("\n")
    return "\n".join(out)


def check_typecheck(source: str, label: str) -> None:
    program = parse_source(source, label)
    diagnostics = TypeChecker().check(program)
    if diagnostics:
        print(f"typecheck failed: {label}")
        for diag in diagnostics[:80]:
            print(diag)
        if len(diagnostics) > 80:
            print(f"... {len(diagnostics) - 80} more diagnostics")
        raise SystemExit(1)


def check_flattened_crates() -> str:
    source = flattened_crates()
    program = parse_source(source, "flattened V4 crates")
    diagnostics = TypeChecker().check(program)
    if diagnostics:
        print("typecheck failed: flattened V4 crates")
        for diag in diagnostics[:80]:
            print(diag)
        if len(diagnostics) > 80:
            print(f"... {len(diagnostics) - 80} more diagnostics")
        raise SystemExit(1)
    print(f"flattened crates: statements={len(program.statements)}")
    return source


def check_fixture_transpile(base_source: str, fixtures: list[Path]) -> None:
    for fixture in fixtures:
        label = rel(fixture)
        source = base_source + "\n\n-- fixture\n" + read_text(fixture)
        check_typecheck(source, label)
        c_source, diagnostics, uses_ui = transpile(source, fixture.with_suffix(".flat.fk"))
        if diagnostics:
            print(f"transpile failed: {label}")
            for diag in diagnostics[:40]:
                print(diag)
            if len(diagnostics) > 40:
                print(f"... {len(diagnostics) - 40} more diagnostics")
            raise SystemExit(1)
        print(f"fixture transpile: {label} c_bytes={len(c_source)} uses_ui={uses_ui}")


def check_executable_smokes(base_source: str) -> None:
    clang = shutil.which("clang")
    if clang is None:
        print("runtime smoke failed: clang not found")
        raise SystemExit(1)

    RUNTIME_BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    runtime_c = RUNTIME_ROOT / "freak_runtime.c"
    runtime_smoke_c = RUNTIME_BUILD_ROOT / "freak_runtime_v4_smoke.c"
    runtime_source = read_text(runtime_c)
    runtime_source = runtime_source.replace("#define FREAK_MAX_ARRAYS 256", "#define FREAK_MAX_ARRAYS 8192")
    runtime_smoke_c.write_text(runtime_source, encoding="utf-8")
    include_arg = f"-I{RUNTIME_ROOT}"
    suffix = ".exe" if sys.platform.startswith("win") else ""

    for smoke in EXECUTABLE_SMOKES:
        fixture = TESTS_ROOT / smoke["fixture"]
        label = rel(fixture)
        source = base_source + "\n\n-- executable fixture\n" + read_text(fixture)
        c_source, diagnostics, uses_ui = transpile(source, fixture.with_suffix(".runtime.flat.fk"))
        if diagnostics:
            print(f"runtime transpile failed: {label}")
            for diag in diagnostics[:40]:
                print(diag)
            if len(diagnostics) > 40:
                print(f"... {len(diagnostics) - 40} more diagnostics")
            raise SystemExit(1)
        if uses_ui:
            print(f"runtime smoke failed: {label} unexpectedly requires UI")
            raise SystemExit(1)

        c_path = RUNTIME_BUILD_ROOT / f"{fixture.stem}.fk.c"
        exe_path = RUNTIME_BUILD_ROOT / f"{fixture.stem}{suffix}"
        c_path.write_text(c_source, encoding="utf-8")

        compile_cmd = [
            clang,
            "-o",
            str(exe_path),
            str(c_path),
            str(runtime_smoke_c),
            include_arg,
            "-w",
            "-O0",
        ]
        compiled = subprocess.run(compile_cmd, cwd=ROOT, text=True, capture_output=True)
        if compiled.returncode != 0:
            print(f"runtime compile failed: {label}")
            print(compiled.stdout)
            print(compiled.stderr)
            raise SystemExit(1)

        executed = subprocess.run([str(exe_path)], cwd=ROOT, text=True, capture_output=True, timeout=60)
        output = executed.stdout + executed.stderr
        if executed.returncode != 0:
            print(f"runtime execution failed: {label} exit={executed.returncode}")
            print(output[:4000])
            raise SystemExit(1)

        missing = [needle for needle in smoke["expect"] if needle not in output]
        if missing:
            print(f"runtime smoke failed: {label}")
            for needle in missing:
                print(f"missing output: {needle}")
            print(output[:4000])
            raise SystemExit(1)

        print(f"runtime smoke: {smoke['name']} fixture={label} output_bytes={len(output)}")


def main() -> int:
    crates = crate_paths()
    fixtures = fixture_paths()
    all_files = crates + fixtures + [V4_ROOT / "README.md"]

    print("Maverick (00-unit) checks")
    check_exists(crates)
    check_ascii(all_files)
    check_individual_parse(crates + fixtures)
    base_source = check_flattened_crates()
    check_fixture_transpile(base_source, fixtures)
    check_executable_smokes(base_source)
    print("Maverick checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
