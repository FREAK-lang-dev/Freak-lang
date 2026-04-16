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
            "result-count=1",
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
