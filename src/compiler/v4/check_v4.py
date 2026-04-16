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

    print("freakc_v4 checks")
    check_exists(crates)
    check_ascii(all_files)
    check_individual_parse(crates + fixtures)
    base_source = check_flattened_crates()
    check_fixture_transpile(base_source, fixtures)
    check_executable_smokes(base_source)
    print("V4 checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
