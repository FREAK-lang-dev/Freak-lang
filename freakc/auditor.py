"""
FREAK Auditor — static analysis commands for Phase 8.

Commands:
    freak audit-science     list every 'for science,' call site
    freak audit-trust       list every 'trust me' block (file, line, level, reason)
    freak audit-miracles    list every 'deus_ex_machina' block with monologue preview
    freak foreshadow-audit  show all foreshadow/payoff pairs and any unpaid ones

All commands accept one or more .fk file paths (or scan recursively if a
directory is given).  They return a non-zero exit code if any warnings/errors
are found (unpaid foreshadows, too many miracles, under-word-count monologues).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .lexer import Lexer, TokenType
from .parser import (
    Annotation,
    Assign,
    Block,
    CheckMaybe,
    CheckResult,
    DeusExMachina,
    DoctrineDecl,
    EventuallyBlock,
    ExprStmt,
    ForEach,
    ForeshadowDecl,
    GiveBack,
    IfExpr,
    ImplBlock,
    IsekaiBlock,
    ParseError,
    Parser,
    PayoffStmt,
    PilotDecl,
    Program,
    RepeatTimes,
    RepeatUntil,
    SayStmt,
    ShapeDecl,
    TaskDecl,
    TrainingArc,
    TrustMeBlock,
    UseImport,
    WhenExpr,
)

# ---------------------------------------------------------------------------
#  Data classes for audit results
# ---------------------------------------------------------------------------


@dataclass
class ScienceCallSite:
    file: str
    line: int

    def __str__(self) -> str:
        return f"  {self.file}:{self.line}: for science"


@dataclass
class TrustMeEntry:
    file: str
    line: int
    honor_level: str
    reason: str

    def __str__(self) -> str:
        return (
            f"  {self.file}:{self.line}: "
            f'trust me (honor: .{self.honor_level}) — "{self.reason}"'
        )


@dataclass
class MiracleEntry:
    file: str
    line: int
    word_count: int
    monologue_preview: str  # first 60 chars

    def __str__(self) -> str:
        wc = f"{self.word_count} words"
        preview = self.monologue_preview
        return f'  {self.file}:{self.line}: deus_ex_machina ({wc}) — "{preview}"'


@dataclass
class ForeshadowEntry:
    file: str
    line: int
    name: str
    paid_off: bool = False
    payoff_line: Optional[int] = None

    def __str__(self) -> str:
        if self.paid_off:
            return (
                f"  {self.file}:{self.line}: foreshadow '{self.name}'"
                f" → paid off at line {self.payoff_line}"
            )
        return f"  {self.file}:{self.line}: foreshadow '{self.name}' ← UNPAID ✗"


# ---------------------------------------------------------------------------
#  Token-level scanner (gives us line numbers)
# ---------------------------------------------------------------------------


def _scan_tokens_for_science(source: str, file: str) -> List[ScienceCallSite]:
    """Scan the token stream for FOR_SCIENCE tokens."""
    results: List[ScienceCallSite] = []
    try:
        tokens = Lexer(source).tokenize()
    except Exception:
        return results
    for tok in tokens:
        if tok.type == TokenType.FOR_SCIENCE:
            results.append(ScienceCallSite(file=file, line=tok.line))
    return results


def _scan_tokens_line_map(source: str) -> Dict[str, int]:
    """
    Build a map of {lexeme_lower → first line} by scanning every token.
    Used to correlate AST nodes (which lack line numbers) back to their
    approximate source location.
    """
    mapping: Dict[str, int] = {}
    try:
        tokens = Lexer(source).tokenize()
    except Exception:
        return mapping
    for tok in tokens:
        key = tok.lexeme.lower()
        if key not in mapping:
            mapping[key] = tok.line
    return mapping


def _find_trust_me_lines(source: str) -> List[int]:
    """Return line numbers of every TRUST_ME token."""
    lines: List[int] = []
    try:
        tokens = Lexer(source).tokenize()
    except Exception:
        return lines
    for tok in tokens:
        if tok.type == TokenType.TRUST_ME:
            lines.append(tok.line)
    return lines


def _find_deus_ex_lines(source: str) -> List[int]:
    """Return line numbers of every DEUS_EX_MACHINA token."""
    lines: List[int] = []
    try:
        tokens = Lexer(source).tokenize()
    except Exception:
        return lines
    for tok in tokens:
        if tok.type == TokenType.DEUS_EX_MACHINA:
            lines.append(tok.line)
    return lines


def _find_foreshadow_payoff_lines(source: str) -> Tuple[List[int], List[int]]:
    """Return (foreshadow_lines, payoff_lines)."""
    fshadow: List[int] = []
    payoff: List[int] = []
    try:
        tokens = Lexer(source).tokenize()
    except Exception:
        return fshadow, payoff
    for tok in tokens:
        if tok.type == TokenType.FORESHADOW:
            fshadow.append(tok.line)
        elif tok.type == TokenType.PAYOFF:
            payoff.append(tok.line)
    return fshadow, payoff


# ---------------------------------------------------------------------------
#  AST walker helpers
# ---------------------------------------------------------------------------


def _walk_statements(stmts, visitor) -> None:
    """Recursively walk all statements in a program/block, calling visitor."""
    for stmt in stmts:
        visitor(stmt)
        # Recurse into nested blocks
        if isinstance(stmt, (TaskDecl,)):
            if isinstance(stmt.body, Block):
                _walk_statements(stmt.body.statements, visitor)
        elif isinstance(stmt, (IfExpr,)):
            _walk_statements(stmt.then_block.statements, visitor)
            for _, blk in stmt.elif_branches:
                _walk_statements(blk.statements, visitor)
            if stmt.else_block:
                _walk_statements(stmt.else_block.statements, visitor)
        elif isinstance(stmt, (WhenExpr,)):
            for arm in stmt.arms:
                if isinstance(arm.body, Block):
                    _walk_statements(arm.body.statements, visitor)
        elif isinstance(stmt, (ForEach, RepeatTimes, RepeatUntil, TrainingArc)):
            _walk_statements(stmt.body.statements, visitor)
        elif isinstance(stmt, (CheckMaybe,)):
            _walk_statements(stmt.got_body.statements, visitor)
            _walk_statements(stmt.nobody_body.statements, visitor)
        elif isinstance(stmt, (CheckResult,)):
            _walk_statements(stmt.ok_body.statements, visitor)
            _walk_statements(stmt.err_body.statements, visitor)
        elif isinstance(stmt, (TrustMeBlock,)):
            _walk_statements(stmt.body.statements, visitor)
        elif isinstance(stmt, (DeusExMachina,)):
            _walk_statements(stmt.body.statements, visitor)
        elif isinstance(stmt, (IsekaiBlock,)):
            _walk_statements(stmt.body.statements, visitor)
        elif isinstance(stmt, (EventuallyBlock,)):
            _walk_statements(stmt.body.statements, visitor)
        elif isinstance(stmt, (Annotation,)):
            if stmt.target:
                visitor(stmt.target)
                _walk_statements([stmt.target], lambda s: None)  # recurse
        elif isinstance(stmt, (ImplBlock,)):
            for m in stmt.methods:
                visitor(m)
                if isinstance(m.body, Block):
                    _walk_statements(m.body.statements, visitor)
        elif isinstance(stmt, ForeshadowDecl):
            pass  # handled by visitor directly
        elif isinstance(stmt, ExprStmt):
            pass


def _collect_trust_me(program: Program, source: str, file: str) -> List[TrustMeEntry]:
    """Walk AST to find all TrustMeBlock nodes, correlate with token line numbers."""
    trust_lines = _find_trust_me_lines(source)
    results: List[TrustMeEntry] = []
    idx = [0]  # mutable counter for matching line numbers

    def visitor(stmt):
        if isinstance(stmt, TrustMeBlock):
            line = trust_lines[idx[0]] if idx[0] < len(trust_lines) else 0
            idx[0] += 1
            preview = stmt.reason[:80] if stmt.reason else "(no reason given)"
            results.append(
                TrustMeEntry(
                    file=file,
                    line=line,
                    honor_level=stmt.honor_level,
                    reason=preview,
                )
            )

    _walk_statements(program.statements, visitor)
    return results


def _collect_miracles(program: Program, source: str, file: str) -> List[MiracleEntry]:
    """Walk AST to find all DeusExMachina nodes."""
    deus_lines = _find_deus_ex_lines(source)
    results: List[MiracleEntry] = []
    idx = [0]

    def visitor(stmt):
        if isinstance(stmt, DeusExMachina):
            line = deus_lines[idx[0]] if idx[0] < len(deus_lines) else 0
            idx[0] += 1
            word_count = len(stmt.monologue.split())
            preview = stmt.monologue[:60].replace("\n", " ").strip()
            if len(stmt.monologue) > 60:
                preview += "..."
            results.append(
                MiracleEntry(
                    file=file,
                    line=line,
                    word_count=word_count,
                    monologue_preview=preview,
                )
            )

    _walk_statements(program.statements, visitor)
    return results


def _collect_foreshadows(
    program: Program, source: str, file: str
) -> List[ForeshadowEntry]:
    """Walk AST and collect foreshadow/payoff pairs."""
    fs_lines, po_lines = _find_foreshadow_payoff_lines(source)
    fs_idx = [0]
    po_idx = [0]

    # First pass: collect all foreshadow decls
    foreshadows: Dict[str, ForeshadowEntry] = {}
    ordered: List[ForeshadowEntry] = []

    def visit_foreshadow(stmt):
        if isinstance(stmt, ForeshadowDecl):
            line = fs_lines[fs_idx[0]] if fs_idx[0] < len(fs_lines) else 0
            fs_idx[0] += 1
            entry = ForeshadowEntry(file=file, line=line, name=stmt.decl.name)
            foreshadows[stmt.decl.name] = entry
            ordered.append(entry)

    _walk_statements(program.statements, visit_foreshadow)

    # Second pass: collect payoffs and mark
    def visit_payoff(stmt):
        if isinstance(stmt, PayoffStmt):
            line = po_lines[po_idx[0]] if po_idx[0] < len(po_lines) else 0
            po_idx[0] += 1
            if stmt.name in foreshadows:
                foreshadows[stmt.name].paid_off = True
                foreshadows[stmt.name].payoff_line = line

    _walk_statements(program.statements, visit_payoff)

    return ordered


# ---------------------------------------------------------------------------
#  High-level per-file analysis
# ---------------------------------------------------------------------------


def _analyse_file(
    path: Path,
) -> Tuple[
    List[ScienceCallSite],
    List[TrustMeEntry],
    List[MiracleEntry],
    List[ForeshadowEntry],
    Optional[str],  # parse error message, or None
]:
    source = path.read_text(encoding="utf-8")
    file_str = str(path)

    science = _scan_tokens_for_science(source, file_str)

    try:
        program = Parser.from_source(source)
    except ParseError as e:
        return science, [], [], [], str(e)

    trust = _collect_trust_me(program, source, file_str)
    miracles = _collect_miracles(program, source, file_str)
    foreshadows = _collect_foreshadows(program, source, file_str)
    return science, trust, miracles, foreshadows, None


def _gather_fk_files(paths: List[Path]) -> List[Path]:
    """Expand directories recursively; keep .fk files."""
    result: List[Path] = []
    for p in paths:
        if p.is_dir():
            result.extend(sorted(p.rglob("*.fk")))
        elif p.suffix == ".fk":
            result.append(p)
    return result


# ---------------------------------------------------------------------------
#  Public command functions
# ---------------------------------------------------------------------------


def audit_science(paths: List[Path]) -> int:
    """
    List every 'for science,' call site in the given files/directories.
    Returns 0 (always informational).
    """
    fk_files = _gather_fk_files(paths)
    if not fk_files:
        print("No .fk files found.")
        return 1

    all_sites: List[ScienceCallSite] = []
    for path in fk_files:
        source = path.read_text(encoding="utf-8")
        all_sites.extend(_scan_tokens_for_science(source, str(path)))

    if not all_sites:
        print("No 'for science' call sites found.")
        return 0

    print(f"Found {len(all_sites)} 'for science' call site(s):\n")
    for site in all_sites:
        print(site)
    return 0


def audit_trust(paths: List[Path]) -> int:
    """
    List every 'trust me' block with file, line, honor level, and reason.
    Returns 0 (always informational).
    """
    fk_files = _gather_fk_files(paths)
    if not fk_files:
        print("No .fk files found.")
        return 1

    all_entries: List[TrustMeEntry] = []
    for path in fk_files:
        source = path.read_text(encoding="utf-8")
        file_str = str(path)
        trust_lines = _find_trust_me_lines(source)
        try:
            program = Parser.from_source(source)
        except ParseError:
            continue
        all_entries.extend(_collect_trust_me(program, source, file_str))

    if not all_entries:
        print("No 'trust me' blocks found.")
        return 0

    print(f"Found {len(all_entries)} 'trust me' block(s):\n")
    for entry in all_entries:
        print(entry)
    return 0


def audit_miracles(paths: List[Path]) -> int:
    """
    List every 'deus_ex_machina' block with file, line, word count, and monologue preview.
    Warns if > 3, errors if > 10 in the scanned codebase.
    """
    fk_files = _gather_fk_files(paths)
    if not fk_files:
        print("No .fk files found.")
        return 1

    all_miracles: List[MiracleEntry] = []
    for path in fk_files:
        source = path.read_text(encoding="utf-8")
        file_str = str(path)
        deus_lines = _find_deus_ex_lines(source)
        try:
            program = Parser.from_source(source)
        except ParseError:
            continue
        all_miracles.extend(_collect_miracles(program, source, file_str))

    if not all_miracles:
        print("No deus_ex_machina blocks found. The laws of physics remain intact.")
        return 0

    print(f"Found {len(all_miracles)} deus_ex_machina block(s):\n")
    for entry in all_miracles:
        print(entry)
        if entry.word_count < 20:
            print(f"    ✗ Monologue too short ({entry.word_count} words, need 20)")

    exit_code = 0
    if len(all_miracles) > 10:
        print(
            f"\n✗ ERROR: {len(all_miracles)} miracles is too many. "
            f"(Yuuko voice: \"At this point you're not bending the rules,"
            f" you're snapping them in half.\")"
        )
        exit_code = 1
    elif len(all_miracles) > 3:
        print(
            f"\n⚠ WARNING: {len(all_miracles)} miracles found. "
            f'(Sagiri voice: "Three is a coincidence. Four is a habit.")'
        )

    return exit_code


def foreshadow_audit(paths: List[Path]) -> int:
    """
    Show all foreshadow/payoff pairs and highlight any unpaid foreshadows.
    Returns 1 if any foreshadow is unpaid.
    """
    fk_files = _gather_fk_files(paths)
    if not fk_files:
        print("No .fk files found.")
        return 1

    all_entries: List[ForeshadowEntry] = []
    parse_errors: List[str] = []

    for path in fk_files:
        science, trust, miracles, foreshadows, err = _analyse_file(path)
        all_entries.extend(foreshadows)
        if err:
            parse_errors.append(f"  {path}: {err}")

    if parse_errors:
        print("Parse errors encountered:")
        for e in parse_errors:
            print(e)
        print()

    if not all_entries:
        print("No foreshadow declarations found.")
        return 0

    unpaid = [e for e in all_entries if not e.paid_off]
    paid = [e for e in all_entries if e.paid_off]

    print(
        f"Foreshadow audit: {len(all_entries)} total, "
        f"{len(paid)} paid, {len(unpaid)} unpaid\n"
    )

    for entry in all_entries:
        print(entry)

    if unpaid:
        print(
            f"\n✗ {len(unpaid)} unpaid foreshadow(s). "
            f'(Takeru voice: "Every promise you make, you keep. '
            f"That's what it means to be a pilot.\")"
        )
        return 1

    print(
        "\n✓ All foreshadows paid off. "
        '(Yuuko voice: "Good. Loose ends are for lesser writers.")'
    )
    return 0


# ---------------------------------------------------------------------------
#  audit_conformance — verify v0.13.x bible-vs-implementation conformance
# ---------------------------------------------------------------------------


def _find_repo_root(start: Path) -> Optional[Path]:
    """Walk upward looking for freak-full-bible.md to locate repo root."""
    p = start.resolve()
    if p.is_file():
        p = p.parent
    while True:
        if (p / "freak-full-bible.md").exists():
            return p
        if p.parent == p:
            return None
        p = p.parent


def audit_conformance(paths: List[Path]) -> int:
    """
    Verify v0.13.x implementation conforms to the contracts the bible
    promises for this release. Checks every "✅ aligned" claim from
    freak-conformance-audit.md is still backed by code or files.

    Returns 1 if any v0.13.x contract is broken, 0 otherwise.

    The check set is hardcoded to the v0.13.x baseline. V4-tagged contracts
    are intentionally not checked — once Phase D bible amendments add
    Status tags, this function can be extended to read them directly.
    """
    import sys as _sys

    start = paths[0] if paths else Path(".")
    repo = _find_repo_root(start)
    if repo is None:
        print("✗ Cannot locate repo root (freak-full-bible.md not found).")
        return 1

    failures: List[str] = []
    warnings: List[str] = []
    summary: List[Tuple[str, bool, str]] = []

    def add(label: str, ok: bool, detail: str = "") -> None:
        summary.append((label, ok, detail))

    # ── Check 1: bible + audit doc present ─────────────────────
    bible = repo / "freak-full-bible.md"
    audit_doc = repo / "freak-conformance-audit.md"
    bible_size = bible.stat().st_size if bible.exists() else 0
    add("Bible", bible.exists() and bible_size > 10_000, f"{bible_size} bytes")
    if not bible.exists():
        failures.append(f"Missing: {bible}")
    elif bible_size < 10_000:
        warnings.append(f"Bible suspiciously small: {bible_size} bytes")

    add("Audit doc", audit_doc.exists(),
        "freak-conformance-audit.md" if audit_doc.exists() else "missing (run audit first)")
    if not audit_doc.exists():
        warnings.append("freak-conformance-audit.md missing — run conformance audit first.")

    # ── Check 2: native CLI binary present ─────────────────────
    freak_exe_name = "freak.exe" if _sys.platform == "win32" else "freak"
    freak_exe = repo / "build" / freak_exe_name
    add("Native CLI", freak_exe.exists(), str(freak_exe.relative_to(repo)) if freak_exe.exists() else "not built")
    if not freak_exe.exists():
        warnings.append(f"Native CLI not built ({freak_exe}). Run build_cli.bat or CI.")

    # ── Check 3: lexer has v0.13.x keywords ───────────────────
    lexer_path = repo / "freakc" / "lexer.py"
    required_keywords = [
        # Core
        "PILOT", "TASK", "GIVE_BACK", "SAY", "SHAPE", "IMPL", "DOCTRINE",
        "LAUNCH", "USE",
        # Control flow
        "IF", "ELSE", "WHEN", "REPEAT", "TIMES", "UNTIL", "DONE",
        "BREAK", "CONTINUE",
        # Error handling
        "CHECK", "RESULT_KW", "GOT", "NOBODY", "SOME", "OK", "ERR", "OR_ELSE",
        # Memory
        "LEND", "MUT", "MOVE", "COPY", "TRUST_ME",
        # Anime
        "TRAINING_ARC", "FORESHADOW", "PAYOFF", "DEUS_EX_MACHINA",
        "ISEKAI", "EVENTUALLY", "BRINGING_BACK", "ON_MY_HONOR",
        "FOR_SCIENCE", "KNOWING", "SADLY", "ROUTE_KW",
        # Operators
        "PIPE", "FAT_ARROW", "ARROW", "QUESTION",
        "PLUS_ULTRA", "NAKAMA", "FINAL_FORM", "TSUNDERE",
    ]
    missing_kw: List[str] = []
    if lexer_path.exists():
        lexer_src = lexer_path.read_text(encoding="utf-8")
        missing_kw = [kw for kw in required_keywords if kw not in lexer_src]
    else:
        failures.append(f"Lexer source not found: {lexer_path}")
    add("Lexer keywords",
        bool(lexer_path.exists()) and not missing_kw,
        f"{len(required_keywords) - len(missing_kw)}/{len(required_keywords)} keywords"
        if lexer_path.exists() else "lexer missing")
    if missing_kw:
        failures.append(f"Lexer missing keywords: {', '.join(missing_kw)}")

    # ── Check 4: audit dispatch consistency (Python + native) ──
    audit_subs = [
        "audit-science",
        "audit-trust",
        "audit-miracles",
        "foreshadow-audit",
        "audit-conformance",
    ]

    main_py = repo / "freakc" / "__main__.py"
    py_missing: List[str] = []
    if main_py.exists():
        py_src = main_py.read_text(encoding="utf-8")
        py_missing = [s for s in audit_subs if s not in py_src]
    else:
        failures.append("freakc/__main__.py missing")
    add("Python CLI audits",
        main_py.exists() and not py_missing,
        f"{len(audit_subs) - len(py_missing)}/{len(audit_subs)} dispatched")
    if py_missing:
        failures.append(f"Python CLI missing dispatch: {', '.join(py_missing)}")

    cli_main = repo / "src" / "cli" / "main.fk"
    cli_missing: List[str] = []
    if cli_main.exists():
        cli_src = cli_main.read_text(encoding="utf-8")
        cli_missing = [s for s in audit_subs if s not in cli_src]
    else:
        warnings.append("src/cli/main.fk missing — native CLI source not present")
    add("Native CLI audits",
        cli_main.exists() and not cli_missing,
        f"{len(audit_subs) - len(cli_missing)}/{len(audit_subs)} dispatched")
    if cli_missing and cli_main.exists():
        # Downgrade audit-conformance-only gap to warning until rebuild
        non_self = [s for s in cli_missing if s != "audit-conformance"]
        if non_self:
            failures.append(f"Native CLI missing dispatch: {', '.join(non_self)}")
        else:
            warnings.append("Native CLI missing audit-conformance dispatch — rebuild via build_cli.bat.")

    # ── Check 5: stdlib modules present ────────────────────────
    expected_fk = {
        "std::math": "std/math.fk",
        "std::string": "std/string.fk",
        "std::convert": "std/convert.fk",
        "std::algorithm": "std/algorithm.fk",
        "std::json": "std/json.fk",
        "std::http": "std/http.fk",
        "std::math3d": "std/math3d.fk",
        "std::version": "std/version.fk",
        "std::zip": "std/zip.fk",
    }
    runtime_c = repo / "freakc" / "runtime" / "freak_runtime.c"
    runtime_src = runtime_c.read_text(encoding="utf-8") if runtime_c.exists() else ""
    expected_runtime = {
        "std::fs": ("freak_fs_read", "freak_runtime_fs_read"),
        "std::process": ("freak_process_exec", "freak_runtime_process_exec"),
        "std::time": ("freak_time_now_ms", "freak_runtime_time_now_ms"),
    }

    missing_stdlib: List[str] = []
    for mod, fk_path in expected_fk.items():
        if not (repo / fk_path).exists():
            missing_stdlib.append(f"{mod} -> {fk_path}")
    for mod, syms in expected_runtime.items():
        if not any(s in runtime_src for s in syms):
            missing_stdlib.append(f"{mod} -> runtime symbol")

    add("Stdlib modules",
        not missing_stdlib,
        f"{len(expected_fk) + len(expected_runtime) - len(missing_stdlib)}/"
        f"{len(expected_fk) + len(expected_runtime)} present")
    if missing_stdlib:
        failures.append(f"Stdlib missing: {'; '.join(missing_stdlib)}")

    # ── Check 6: borrow checker --strict-borrow flag ──────────
    cli_src = cli_main.read_text(encoding="utf-8") if cli_main.exists() else ""
    bc_ok = "--strict-borrow" in cli_src
    add("Borrow checker", bc_ok, "--strict-borrow flag handled" if bc_ok else "flag missing")
    if not bc_ok:
        failures.append("--strict-borrow not handled in src/cli/main.fk")

    # ── Check 7: deus_ex_machina 20-word rule still enforced ──
    parser_path = repo / "freakc" / "parser.py"
    dem_ok = False
    if parser_path.exists():
        parser_src = parser_path.read_text(encoding="utf-8")
        # Look for any reference to the 20-word minimum near deus_ex_machina
        dem_ok = "20" in parser_src and "deus_ex_machina" in parser_src.lower()
    add("deus_ex_machina ≥20", dem_ok, "monologue word count enforced" if dem_ok else "rule missing")
    if not dem_ok:
        warnings.append("deus_ex_machina 20-word rule not visibly enforced in parser.py")

    # ── Check 7c: V4 raw-pointer .is_null() lowering (regression guard) ──
    # Bible §16.4 permits .is_null() checks outside trust-me; V4 lowers them
    # to LLVM icmp eq ptr %p, null. Lock in the MIR opcode + codegen path +
    # smoke fixture so regressions surface immediately.
    v4_mir_lib_isn = repo / "src" / "compiler" / "v4" / "crates" / "freak_mir" / "src" / "lib.fk"
    v4_codegen_lib_isn = repo / "src" / "compiler" / "v4" / "crates" / "freak_codegen_llvm" / "src" / "lib.fk"
    v4_isn_smoke = repo / "src" / "compiler" / "v4" / "tests" / "raw_pointer_is_null_smoke.fk"
    v4_check_harness_isn = repo / "src" / "compiler" / "v4" / "check_v4.py"
    isn_missing: List[str] = []
    if v4_mir_lib_isn.exists():
        mir_src = v4_mir_lib_isn.read_text(encoding="utf-8")
        for needle in (
            "v4_mir_unary_ptr_is_null",
            "is_null takes no arguments",
        ):
            if needle not in mir_src:
                isn_missing.append(f"freak_mir: {needle}")
    else:
        isn_missing.append("freak_mir/src/lib.fk missing")
    if v4_codegen_lib_isn.exists():
        cg_src = v4_codegen_lib_isn.read_text(encoding="utf-8")
        if "icmp eq ptr" not in cg_src:
            isn_missing.append("freak_codegen_llvm: icmp eq ptr lowering")
    else:
        isn_missing.append("freak_codegen_llvm/src/lib.fk missing")
    if not v4_isn_smoke.exists():
        isn_missing.append("smoke fixture: raw_pointer_is_null_smoke.fk")
    if v4_check_harness_isn.exists():
        harness_src = v4_check_harness_isn.read_text(encoding="utf-8")
        if "raw_pointer_is_null_smoke.fk" not in harness_src:
            isn_missing.append("EXECUTABLE_SMOKES: raw_pointer_is_null_smoke entry")
    else:
        isn_missing.append("check_v4.py harness missing")
    add(
        "V4 raw-ptr is_null",
        not isn_missing,
        "MIR opcode + LLVM lowering + smoke wired" if not isn_missing else f"{len(isn_missing)} gap(s)",
    )
    if isn_missing:
        failures.append("V4 raw-pointer is_null lowering regressed: " + "; ".join(isn_missing))

    # ── Check 7d: V4 trust me block parsing (regression guard) ──
    # Bible §16.4 gates raw-pointer dereferencing on `trust me` blocks. V4 now
    # parses the honor ladder, validates known ranks, and uses that rank for
    # first-pass raw-pointer read/write/offset/cast gates.
    v4_mir_lib_tm = repo / "src" / "compiler" / "v4" / "crates" / "freak_mir" / "src" / "lib.fk"
    v4_codegen_lib_tm = repo / "src" / "compiler" / "v4" / "crates" / "freak_codegen_llvm" / "src" / "lib.fk"
    v4_ty_lib_tm = repo / "src" / "compiler" / "v4" / "crates" / "freak_ty" / "src" / "lib.fk"
    v4_trust_me_smoke = repo / "src" / "compiler" / "v4" / "tests" / "trust_me_block_smoke.fk"
    v4_deref_smoke = repo / "src" / "compiler" / "v4" / "tests" / "raw_pointer_deref_smoke.fk"
    v4_deref_write_smoke = repo / "src" / "compiler" / "v4" / "tests" / "raw_pointer_deref_write_smoke.fk"
    v4_raw_methods_smoke = repo / "src" / "compiler" / "v4" / "tests" / "raw_pointer_methods_smoke.fk"
    v4_raw_offset_cast_smoke = repo / "src" / "compiler" / "v4" / "tests" / "raw_pointer_offset_cast_smoke.fk"
    v4_check_harness_tm = repo / "src" / "compiler" / "v4" / "check_v4.py"
    tm_missing: List[str] = []
    if v4_mir_lib_tm.exists():
        mir_src = v4_mir_lib_tm.read_text(encoding="utf-8")
        for needle in (
            "v4_mir_lower_trust_me_stmt",
            "trust me block needs me keyword",
            "trust me block needs body",
            "v4_mir_push_trust_me",
            "v4_mir_push_trust_me_honor",
            "v4_mir_inside_trust_me",
            "v4_mir_honor_rank",
            "trust me honor level unknown",
            "trust me honor level too low",
            "v4_mir_unary_deref",
            "raw-pointer deref needs trust me block",
            "v4_mir_place_deref",
            "raw-pointer write needs *mut T",
            "v4_mir_trust_honor_help",
            "v4_mir_try_lower_builtin_raw_pointer_instance_method",
            "v4_mir_call_raw_ptr_write",
            "raw-pointer method arity mismatch",
            "v4_mir_unary_ptr_offset",
            "v4_mir_unary_ptr_cast",
            "raw-pointer offset needs trust me block",
            "raw-pointer cast needs trust me block",
            "offset argument must be int or uint",
            "cast needs a target type parameter",
            "cast target type is invalid",
            "v4_mir_generic_method_type_arg_open_for_close",
            "v4_mir_is_generic_instance_method_call_shape",
        ):
            if needle not in mir_src:
                tm_missing.append(f"freak_mir: {needle}")
    else:
        tm_missing.append("freak_mir/src/lib.fk missing")
    if v4_ty_lib_tm.exists():
        ty_src = v4_ty_lib_tm.read_text(encoding="utf-8")
        if "v4_ty_is_mutable_raw_pointer_type" not in ty_src:
            tm_missing.append("freak_ty: v4_ty_is_mutable_raw_pointer_type")
        if "v4_ty_raw_pointer_with_target_type" not in ty_src:
            tm_missing.append("freak_ty: v4_ty_raw_pointer_with_target_type")
    else:
        tm_missing.append("freak_ty/src/lib.fk missing")
    if v4_codegen_lib_tm.exists():
        cg_src = v4_codegen_lib_tm.read_text(encoding="utf-8")
        if "v4_mir_unary_deref" not in cg_src:
            tm_missing.append("freak_codegen_llvm: deref load lowering")
        if "v4_mir_place_deref" not in cg_src:
            tm_missing.append("freak_codegen_llvm: deref store lowering")
        if "v4_mir_call_raw_ptr_write" not in cg_src:
            tm_missing.append("freak_codegen_llvm: raw pointer method write store lowering")
        if "v4_mir_unary_ptr_offset" not in cg_src:
            tm_missing.append("freak_codegen_llvm: raw pointer offset gep lowering")
        if "v4_mir_unary_ptr_cast" not in cg_src:
            tm_missing.append("freak_codegen_llvm: raw pointer cast gep lowering")
    else:
        tm_missing.append("freak_codegen_llvm/src/lib.fk missing")
    if not v4_trust_me_smoke.exists():
        tm_missing.append("smoke fixture: trust_me_block_smoke.fk")
    if not v4_deref_smoke.exists():
        tm_missing.append("smoke fixture: raw_pointer_deref_smoke.fk")
    if not v4_deref_write_smoke.exists():
        tm_missing.append("smoke fixture: raw_pointer_deref_write_smoke.fk")
    if not v4_raw_methods_smoke.exists():
        tm_missing.append("smoke fixture: raw_pointer_methods_smoke.fk")
    if not v4_raw_offset_cast_smoke.exists():
        tm_missing.append("smoke fixture: raw_pointer_offset_cast_smoke.fk")
    if v4_check_harness_tm.exists():
        harness_src = v4_check_harness_tm.read_text(encoding="utf-8")
        if "trust_me_block_smoke.fk" not in harness_src:
            tm_missing.append("EXECUTABLE_SMOKES: trust_me_block_smoke entry")
        if "raw_pointer_deref_smoke.fk" not in harness_src:
            tm_missing.append("EXECUTABLE_SMOKES: raw_pointer_deref_smoke entry")
        if "raw_pointer_deref_write_smoke.fk" not in harness_src:
            tm_missing.append("EXECUTABLE_SMOKES: raw_pointer_deref_write_smoke entry")
        if "raw_pointer_methods_smoke.fk" not in harness_src:
            tm_missing.append("EXECUTABLE_SMOKES: raw_pointer_methods_smoke entry")
        if "raw_pointer_offset_cast_smoke.fk" not in harness_src:
            tm_missing.append("EXECUTABLE_SMOKES: raw_pointer_offset_cast_smoke entry")
        if "trust-me-honor-rank-humanity=5" not in harness_src:
            tm_missing.append("check_v4.py: trust-me honor rank expectations")
        if "trust-me-unknown-level-mir-diag0-message=trust me honor level unknown" not in harness_src:
            tm_missing.append("check_v4.py: unknown honor expectation")
        if "raw-ptr-write-cadet-mir-diag0-message=trust me honor level too low" not in harness_src:
            tm_missing.append("check_v4.py: low honor raw-pointer write expectation")
        if "raw-ptr-method-write-rvalue-op=RawPtrWrite" not in harness_src:
            tm_missing.append("check_v4.py: raw pointer method write expectation")
        if "raw-ptr-method-good-call-count=2" not in harness_src:
            tm_missing.append("check_v4.py: raw pointer method call index expectation")
        if "raw-ptr-oc-offset-rvalue-op=PtrOffset" not in harness_src:
            tm_missing.append("check_v4.py: raw pointer offset expectation")
        if "raw-ptr-oc-cast-rvalue-op=PtrCast" not in harness_src:
            tm_missing.append("check_v4.py: raw pointer cast expectation")
        if "raw-ptr-oc-bad-diag1-help=raw-pointer offset requires .ace or higher; current honor is .pilot" not in harness_src:
            tm_missing.append("check_v4.py: low honor raw-pointer offset expectation")
    else:
        tm_missing.append("check_v4.py harness missing")
    add(
        "V4 trust me block",
        not tm_missing,
        "parse + raw-pointer read/write/offset/cast gates + smokes wired" if not tm_missing else f"{len(tm_missing)} gap(s)",
    )
    if tm_missing:
        failures.append("V4 trust me block parsing regressed: " + "; ".join(tm_missing))

    # ── Check 8: V4 @extern_callback FFI surface (regression guard) ──
    # Once a 🔜 V4 row promotes to ⚠️/✅ in bible §0.2, audit_conformance
    # grows a check so the contract cannot silently regress. The
    # @extern_callback("ABI") inbound callback surface landed in V4 with
    # validators in freak_ty, LLVM trampolines in freak_codegen_llvm, a
    # smoke fixture, and an EXECUTABLE_SMOKES entry.
    v4_ty_lib = repo / "src" / "compiler" / "v4" / "crates" / "freak_ty" / "src" / "lib.fk"
    v4_codegen_lib = repo / "src" / "compiler" / "v4" / "crates" / "freak_codegen_llvm" / "src" / "lib.fk"
    v4_smoke = repo / "src" / "compiler" / "v4" / "tests" / "extern_callback_export_smoke.fk"
    v4_check_harness = repo / "src" / "compiler" / "v4" / "check_v4.py"
    ec_missing: List[str] = []
    if v4_ty_lib.exists():
        ty_src = v4_ty_lib.read_text(encoding="utf-8")
        for needle in (
            "v4_ty_signature_has_extern_callback",
            "v4_ty_extern_callback_trampoline_name",
            "v4_ty_task_callback_value_type",
        ):
            if needle not in ty_src:
                ec_missing.append(f"freak_ty: {needle}")
    else:
        ec_missing.append("freak_ty/src/lib.fk missing")
    if v4_codegen_lib.exists():
        cg_src = v4_codegen_lib.read_text(encoding="utf-8")
        for needle in (
            "v4_codegen_llvm_callback_trampoline_name",
            "v4_codegen_llvm_lower_callback_trampolines",
            "v4_codegen_llvm_use_symbol_value",
        ):
            if needle not in cg_src:
                ec_missing.append(f"freak_codegen_llvm: {needle}")
    else:
        ec_missing.append("freak_codegen_llvm/src/lib.fk missing")
    if not v4_smoke.exists():
        ec_missing.append("smoke fixture: extern_callback_export_smoke.fk")
    if v4_check_harness.exists():
        harness_src = v4_check_harness.read_text(encoding="utf-8")
        if "extern_callback_export_smoke.fk" not in harness_src:
            ec_missing.append("EXECUTABLE_SMOKES: extern_callback_export_smoke entry")
    else:
        ec_missing.append("check_v4.py harness missing")
    add(
        "V4 @extern_callback",
        not ec_missing,
        "TY validators, LLVM trampoline, smoke wired" if not ec_missing else f"{len(ec_missing)} gap(s)",
    )
    if ec_missing:
        failures.append("V4 @extern_callback surface regressed: " + "; ".join(ec_missing))

    # ── Check 9: V4 stack-unwinder extern-import diagnostic ──
    # Bible §16.5 promises panics never cross extern boundaries; V4 enforces
    # the inbound side by warning on known C unwinder primitives declared
    # in extern blocks. Lock in the validator + smoke fixture + EXECUTABLE_SMOKES
    # entry so the surface cannot silently regress.
    v4_ty_lib_unw = repo / "src" / "compiler" / "v4" / "crates" / "freak_ty" / "src" / "lib.fk"
    v4_mir_lib_unw = repo / "src" / "compiler" / "v4" / "crates" / "freak_mir" / "src" / "lib.fk"
    v4_unwinder_smoke = repo / "src" / "compiler" / "v4" / "tests" / "extern_unwinder_smoke.fk"
    v4_allow_unwinder_smoke = repo / "src" / "compiler" / "v4" / "tests" / "extern_allow_unwinder_smoke.fk"
    v4_unwinder_call_site_smoke = repo / "src" / "compiler" / "v4" / "tests" / "extern_unwinder_call_site_smoke.fk"
    v4_check_harness_unw = repo / "src" / "compiler" / "v4" / "check_v4.py"
    unw_missing: List[str] = []
    if v4_ty_lib_unw.exists():
        ty_src = v4_ty_lib_unw.read_text(encoding="utf-8")
        for needle in (
            "v4_ty_is_known_unwinder_symbol",
            "v4_ty_validate_extern_member_unwinder_contract",
            "v4_ty_add_warning_diag",
            "v4_ty_extern_member_has_allow_unwinder",
            "v4_ty_extern_block_has_allow_unwinder",
            "v4_ty_signature_is_warned_unwinder",
        ):
            if needle not in ty_src:
                unw_missing.append(f"freak_ty: {needle}")
    else:
        unw_missing.append("freak_ty/src/lib.fk missing")
    if v4_mir_lib_unw.exists():
        mir_src = v4_mir_lib_unw.read_text(encoding="utf-8")
        for needle in (
            "v4_mir_warn_unwinder_call_site",
            "v4_mir_add_type_warning",
        ):
            if needle not in mir_src:
                unw_missing.append(f"freak_mir: {needle}")
    else:
        unw_missing.append("freak_mir/src/lib.fk missing")
    if not v4_unwinder_smoke.exists():
        unw_missing.append("smoke fixture: extern_unwinder_smoke.fk")
    if not v4_allow_unwinder_smoke.exists():
        unw_missing.append("smoke fixture: extern_allow_unwinder_smoke.fk")
    if not v4_unwinder_call_site_smoke.exists():
        unw_missing.append("smoke fixture: extern_unwinder_call_site_smoke.fk")
    if v4_check_harness_unw.exists():
        harness_src = v4_check_harness_unw.read_text(encoding="utf-8")
        if "extern_unwinder_smoke.fk" not in harness_src:
            unw_missing.append("EXECUTABLE_SMOKES: extern_unwinder_smoke entry")
        if "extern_allow_unwinder_smoke.fk" not in harness_src:
            unw_missing.append("EXECUTABLE_SMOKES: extern_allow_unwinder_smoke entry")
        if "extern_unwinder_call_site_smoke.fk" not in harness_src:
            unw_missing.append("EXECUTABLE_SMOKES: extern_unwinder_call_site_smoke entry")
    else:
        unw_missing.append("check_v4.py harness missing")
    add(
        "V4 unwinder diag",
        not unw_missing,
        "decl + call-site + opt-out + smokes wired" if not unw_missing else f"{len(unw_missing)} gap(s)",
    )
    if unw_missing:
        failures.append("V4 unwinder-import diagnostic regressed: " + "; ".join(unw_missing))

    # ── Check 10: V4 borrowed-return provenance ──
    # Borrowed return signatures and the first elision slice are now a
    # promoted V4 contract. Require TY surface carriage, Meiya's return
    # validation, and its executable smoke whenever conformance is audited.
    v4_ty_lib_return = repo / "src" / "compiler" / "v4" / "crates" / "freak_ty" / "src" / "lib.fk"
    v4_borrowck_lib_return = repo / "src" / "compiler" / "v4" / "crates" / "freak_borrowck" / "src" / "lib.fk"
    v4_lend_return_smoke = repo / "src" / "compiler" / "v4" / "tests" / "lend_return_smoke.fk"
    v4_check_harness_return = repo / "src" / "compiler" / "v4" / "check_v4.py"
    return_missing: List[str] = []
    if v4_ty_lib_return.exists():
        ty_src = v4_ty_lib_return.read_text(encoding="utf-8")
        for needle in (
            "v4_ty_lend_type",
            'out == "lend" and value == "mut"',
            "v4_ty_is_lend_type",
        ):
            if needle not in ty_src:
                return_missing.append(f"freak_ty: {needle}")
    else:
        return_missing.append("freak_ty/src/lib.fk missing")
    if v4_borrowck_lib_return.exists():
        borrowck_src = v4_borrowck_lib_return.read_text(encoding="utf-8")
        for needle in (
            "v4_borrowck_return_lend_origin",
            "v4_borrowck_check_returned_lends",
            "v4_borrowck_check_stored_call_lends",
            "v4_borrowck_stored_call_return_holder",
            "v4_borrowck_holder_alias_from_stmt",
            "v4_borrowck_holder_state",
            "v4_borrowck_holder_reaches_stmt_without_rebind",
            "v4_borrowck_path_canon(v4_mir_rvalue_text(mir_id, body_id, rvalue_id)) == holder_canon",
            "Meiya refuses to return a loan of an owned value",
            "Meiya refuses a mutable reloan from an immutable lend",
            "Meiya cannot store this borrowed call result yet",
        ):
            if needle not in borrowck_src:
                return_missing.append(f"freak_borrowck: {needle}")
    else:
        return_missing.append("freak_borrowck/src/lib.fk missing")
    if not v4_lend_return_smoke.exists():
        return_missing.append("smoke fixture: lend_return_smoke.fk")
    if v4_check_harness_return.exists():
        harness_src = v4_check_harness_return.read_text(encoding="utf-8")
        if "lend_return_smoke.fk" not in harness_src:
            return_missing.append("EXECUTABLE_SMOKES: lend_return_smoke entry")
    else:
        return_missing.append("check_v4.py harness missing")
    add(
        "V4 lend returns",
        not return_missing,
        "TY surface + provenance + smoke wired" if not return_missing else f"{len(return_missing)} gap(s)",
    )
    if return_missing:
        failures.append("V4 borrowed-return provenance regressed: " + "; ".join(return_missing))

    # Check 11: V4 partial-move CFG repairs
    partial_move_missing: List[str] = []
    v4_partial_move_smoke = repo / "src" / "compiler" / "v4" / "tests" / "borrowck_partial_move_smoke.fk"
    if v4_borrowck_lib_return.exists():
        borrowck_src = v4_borrowck_lib_return.read_text(encoding="utf-8")
        for needle in (
            "v4_borrowck_move_repaired_on_all_paths_seen",
            "v4_borrowck_stmt_repairs_move",
            "v4_borrowck_repair_state_key",
        ):
            if needle not in borrowck_src:
                partial_move_missing.append(f"freak_borrowck: {needle}")
    else:
        partial_move_missing.append("freak_borrowck/src/lib.fk missing")
    if v4_partial_move_smoke.exists():
        smoke_src = v4_partial_move_smoke.read_text(encoding="utf-8")
        for needle in (
            "cross_repaired",
            "partial-move-cross-unrepaired-status=",
            "partial-move-cross-message=",
        ):
            if needle not in smoke_src:
                partial_move_missing.append(f"borrowck_partial_move_smoke: {needle}")
    else:
        partial_move_missing.append("smoke fixture: borrowck_partial_move_smoke.fk")
    if v4_check_harness_return.exists():
        harness_src = v4_check_harness_return.read_text(encoding="utf-8")
        if "partial-move-cross-unrepaired-status=blocked" not in harness_src:
            partial_move_missing.append("check_v4.py: partial-move cross-block expectation")
    else:
        partial_move_missing.append("check_v4.py harness missing")
    add(
        "V4 partial moves",
        not partial_move_missing,
        "CFG repair proof + smoke wired" if not partial_move_missing else f"{len(partial_move_missing)} gap(s)",
    )
    if partial_move_missing:
        failures.append("V4 partial-move CFG repair regressed: " + "; ".join(partial_move_missing))

    # Check 12: V4 moved-local drop flags
    drop_flag_missing: List[str] = []
    v4_drop_order_smoke = repo / "src" / "compiler" / "v4" / "tests" / "borrowck_drop_order_smoke.fk"
    v4_borrowck_snapshot_smoke = repo / "src" / "compiler" / "v4" / "tests" / "borrowck_snapshot_smoke.fk"
    if v4_borrowck_lib_return.exists():
        borrowck_src = v4_borrowck_lib_return.read_text(encoding="utf-8")
        for needle in (
            "v4_borrowck_local_moved_without_reinit_linear",
            "v4_borrowck_local_moved_on_all_exits_seen",
            "v4_borrowck_local_moved_on_any_exit",
            "v4_borrowck_local_has_exit_state_seen",
            "v4_borrowck_path_drop_if",
            "v4_borrowck_drop_seen_block",
            "v4_borrowck_drop_state_key",
            "terminator == v4_mir_term_unreachable",
            "v4_borrowck_path_exact_local",
            "v4_borrowck_stmt_has_exact_local_path",
        ):
            if needle not in borrowck_src:
                drop_flag_missing.append(f"freak_borrowck: {needle}")
    else:
        drop_flag_missing.append("freak_borrowck/src/lib.fk missing")
    if v4_drop_order_smoke.exists():
        smoke_src = v4_drop_order_smoke.read_text(encoding="utf-8")
        for needle in (
            "moved_local",
            "move_reassign",
            "branch_moved",
            "branch_partial",
            "branch_reinit",
            "loop_before_move",
            "loop_moves_inside",
            "route_branch_moved",
            "drop-moved-count=",
            "drop-reinit-count=",
            "drop-move-reassign-count=",
            "drop-branch-moved-count=",
            "drop-branch-partial-count=",
            "drop-branch-partial-if-count=",
            "drop-branch-reinit-if-count=",
            "drop-loop-before-move-count=",
            "drop-loop-moves-inside-if-count=",
            "drop-route-branch-moved-count=",
        ):
            if needle not in smoke_src:
                drop_flag_missing.append(f"borrowck_drop_order_smoke: {needle}")
    else:
        drop_flag_missing.append("smoke fixture: borrowck_drop_order_smoke.fk")
    if v4_borrowck_snapshot_smoke.exists():
        snapshot_src = v4_borrowck_snapshot_smoke.read_text(encoding="utf-8")
        for needle in (
            "v4_borrowck_snapshot_dropif_source",
            "borrowck-snapshot-dropif-count=",
            "borrowck-snapshot-dropif-kind=",
            "borrowck-snapshot-dropif-line=",
            "restored-dropif-count=",
            "restored-dropif-kind=",
        ):
            if needle not in snapshot_src:
                drop_flag_missing.append(f"borrowck_snapshot_smoke: {needle}")
    else:
        drop_flag_missing.append("smoke fixture: borrowck_snapshot_smoke.fk")
    if v4_check_harness_return.exists():
        harness_src = v4_check_harness_return.read_text(encoding="utf-8")
        if "drop-branch-partial-count=2" not in harness_src:
            drop_flag_missing.append("check_v4.py: moved-local drop expectation")
        if "drop-branch-partial-if-count=1" not in harness_src:
            drop_flag_missing.append("check_v4.py: conditional branch drop expectation")
        if "drop-branch-reinit-if-count=0" not in harness_src:
            drop_flag_missing.append("check_v4.py: branch reinit drop expectation")
        if "drop-loop-before-move-count=1" not in harness_src:
            drop_flag_missing.append("check_v4.py: loop-backedge drop expectation")
        if "drop-loop-moves-inside-if-count=1" not in harness_src:
            drop_flag_missing.append("check_v4.py: loop move DropIf expectation")
        if "drop-route-branch-moved-count=1" not in harness_src:
            drop_flag_missing.append("check_v4.py: unreachable-tail drop expectation")
        if "borrowck-snapshot-dropif-count=1" not in harness_src:
            drop_flag_missing.append("check_v4.py: DropIf snapshot expectation")
        if "restored-dropif-count=1" not in harness_src:
            drop_flag_missing.append("check_v4.py: restored DropIf snapshot expectation")
    else:
        drop_flag_missing.append("check_v4.py harness missing")
    add(
        "V4 drop flags",
        not drop_flag_missing,
        "linear + all-exit moved-local suppression wired, DropIf survives mixed exits, loop backedges, and snapshots" if not drop_flag_missing else f"{len(drop_flag_missing)} gap(s)",
    )
    if drop_flag_missing:
        failures.append("V4 moved-local drop flags regressed: " + "; ".join(drop_flag_missing))

    # Check 13: V4 Shared/Weak ownership surface
    shared_weak_missing: List[str] = []
    v4_shared_smoke = repo / "src" / "compiler" / "v4" / "tests" / "shared_weak_smoke.fk"
    v4_mir_lib_shared = repo / "src" / "compiler" / "v4" / "crates" / "freak_mir" / "src" / "lib.fk"
    if v4_borrowck_lib_return.exists():
        borrowck_src = v4_borrowck_lib_return.read_text(encoding="utf-8")
        for needle in (
            "v4_borrowck_check_shared_guard_escapes",
            "v4_borrowck_rvalue_returns_shared_mut_guard",
            "Meiya refuses to let a SharedMut guard escape",
        ):
            if needle not in borrowck_src:
                shared_weak_missing.append(f"freak_borrowck: {needle}")
    else:
        shared_weak_missing.append("freak_borrowck/src/lib.fk missing")
    if v4_mir_lib_shared.exists():
        mir_src = v4_mir_lib_shared.read_text(encoding="utf-8")
        for needle in (
            "v4_mir_try_lower_builtin_shared_instance_method",
            "v4_mir_try_lower_builtin_shared_associated_method",
            "v4_mir_builtin_shared_receiver_loan_payload",
            "Weak must upgrade before borrow",
            "v4_ty_shared_mut_type",
        ):
            if needle not in mir_src:
                shared_weak_missing.append(f"freak_mir: {needle}")
    else:
        shared_weak_missing.append("freak_mir/src/lib.fk missing")
    if v4_shared_smoke.exists():
        smoke_src = v4_shared_smoke.read_text(encoding="utf-8")
        for needle in (
            "Shared<Ship>::new",
            "root.borrow()",
            "root.borrow_mut()",
            "weak.upgrade()",
            "weak.borrow()",
            "return_borrow_error",
            "leak_actual_guard",
            "shared-weak-guard-escape-diagnostics=",
        ):
            if needle not in smoke_src:
                shared_weak_missing.append(f"shared_weak_smoke: {needle}")
    else:
        shared_weak_missing.append("smoke fixture: shared_weak_smoke.fk")
    if v4_check_harness_return.exists():
        harness_src = v4_check_harness_return.read_text(encoding="utf-8")
        if "shared-weak-guard-ty=result<SharedMut<Ship>,BorrowError>" not in harness_src:
            shared_weak_missing.append("check_v4.py: SharedMut type expectation")
        if "shared-weak-direct-diagnostics=1" not in harness_src:
            shared_weak_missing.append("check_v4.py: weak direct borrow expectation")
        if "shared-weak-error-status=clean" not in harness_src:
            shared_weak_missing.append("check_v4.py: SharedMut result error expectation")
        if "shared-weak-clone-args=1" not in harness_src:
            shared_weak_missing.append("check_v4.py: Shared clone receiver argument expectation")
        if "shared-weak-upgrade-args=1" not in harness_src:
            shared_weak_missing.append("check_v4.py: Weak upgrade receiver argument expectation")
        if "shared-weak-guard-escape-diagnostics=1" not in harness_src:
            shared_weak_missing.append("check_v4.py: guard escape expectation")
    else:
        shared_weak_missing.append("check_v4.py harness missing")
    add(
        "V4 Shared/Weak",
        not shared_weak_missing,
        "TY/MIR Shared/Weak method surface plus weak-borrow and guard-escape diagnostics wired" if not shared_weak_missing else f"{len(shared_weak_missing)} gap(s)",
    )
    if shared_weak_missing:
        failures.append("V4 Shared/Weak ownership surface regressed: " + "; ".join(shared_weak_missing))

    # ── Print summary ────────────────────────────────────────
    print()
    print("FREAK Conformance Audit (v0.13.x baseline)")
    print("=" * 56)
    for label, ok, detail in summary:
        marker = "✓" if ok else "✗"
        print(f"  {marker}  {label:<20} {detail}")
    print("=" * 56)

    if warnings:
        print()
        print("Warnings:")
        for w in warnings:
            print(f"  ⚠  {w}")

    if failures:
        print()
        print("Failures:")
        for f in failures:
            print(f"  ✗  {f}")
        print()
        print(
            f"✗ {len(failures)} divergence(s) found. v0.13.x conformance NOT clean. "
            '(Sagiri voice: "I told you the bible was overpromising.")'
        )
        return 1

    print()
    if warnings:
        print(
            f"⚠  {len(warnings)} warning(s); no failures. Conformance clean with caveats. "
            '(Yuuko voice: "Acceptable. Barely.")'
        )
    else:
        print(
            "✓ All v0.13.x conformance checks passed. "
            '(Meiya voice: "I knew you would not disappoint.")'
        )
    return 0


__all__ = [
    "audit_science",
    "audit_trust",
    "audit_miracles",
    "foreshadow_audit",
    "audit_conformance",
    "ScienceCallSite",
    "TrustMeEntry",
    "MiracleEntry",
    "ForeshadowEntry",
]
