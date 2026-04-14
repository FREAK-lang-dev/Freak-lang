from __future__ import annotations

import sys
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
    print("V4 checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
