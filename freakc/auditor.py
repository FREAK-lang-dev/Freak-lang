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

import ast
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


def _literal_executable_smokes(path: Path) -> Tuple[Dict[str, List[str]], List[str]]:
    """Read EXECUTABLE_SMOKES without importing or executing the harness."""
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        return {}, [f"check_v4.py could not be read: {exc}"]

    try:
        module = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        location = f"line {exc.lineno}" if exc.lineno is not None else "unknown line"
        return {}, [f"check_v4.py AST parse failed at {location}: {exc.msg}"]

    manifests: List[ast.expr] = []
    for node in module.body:
        if isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == "EXECUTABLE_SMOKES"
                for target in node.targets
            ):
                manifests.append(node.value)
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "EXECUTABLE_SMOKES"
            and node.value is not None
        ):
            manifests.append(node.value)

    if not manifests:
        return {}, ["check_v4.py: literal EXECUTABLE_SMOKES assignment missing"]
    if len(manifests) != 1:
        return {}, [
            f"check_v4.py: EXECUTABLE_SMOKES assigned {len(manifests)} times; expected once"
        ]

    try:
        manifest = ast.literal_eval(manifests[0])
    except (SyntaxError, TypeError, ValueError) as exc:
        return {}, [
            "check_v4.py: EXECUTABLE_SMOKES must be a literal manifest "
            f"({type(exc).__name__}: {exc})"
        ]

    if not isinstance(manifest, list):
        return {}, ["check_v4.py: EXECUTABLE_SMOKES must be a literal list"]

    smoke_expects: Dict[str, List[str]] = {}
    seen_fixtures: Dict[str, int] = {}
    errors: List[str] = []
    for index, entry in enumerate(manifest):
        if not isinstance(entry, dict):
            errors.append(f"EXECUTABLE_SMOKES[{index}]: entry must be a literal dict")
            continue

        fixture = entry.get("fixture")
        if not isinstance(fixture, str) or not fixture:
            errors.append(f"EXECUTABLE_SMOKES[{index}]: missing non-empty fixture name")
            continue
        if fixture in seen_fixtures:
            errors.append(
                f"EXECUTABLE_SMOKES: duplicate fixture entry {fixture} "
                f"at indexes {seen_fixtures[fixture]} and {index}"
            )
            continue
        seen_fixtures[fixture] = index

        expects = entry.get("expect")
        if not isinstance(expects, list):
            errors.append(f"EXECUTABLE_SMOKES: {fixture} missing literal expect list")
            continue
        if not expects:
            errors.append(f"EXECUTABLE_SMOKES: {fixture} has an empty expect list")
            continue
        if any(not isinstance(value, str) or not value for value in expects):
            errors.append(
                f"EXECUTABLE_SMOKES: {fixture} expect list contains a non-string or empty value"
            )
            continue

        smoke_expects[fixture] = expects

    return smoke_expects, errors


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
            "#RawPtrWrite",
            "raw-pointer method arity mismatch",
            "v4_mir_unary_ptr_offset",
            "v4_mir_unary_ptr_cast",
            "raw-pointer offset needs trust me block",
            "raw-pointer cast needs trust me block",
            "offset argument must be int or uint",
            "offset target type must not be void",
            "offset target type must be concrete",
            "offset target type must be scalar",
            "cast needs a target type parameter",
            "cast target type is invalid",
            "cast target syntax is invalid",
            "method takes no type arguments",
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
        if "raw-ptr-method-write-rvalue-op=#RawPtrWrite" not in harness_src:
            tm_missing.append("check_v4.py: raw pointer method write expectation")
        if "raw-ptr-method-good-call-count=3" not in harness_src:
            tm_missing.append("check_v4.py: raw pointer method call index expectation")
        if "raw-ptr-oc-offset-rvalue-op=PtrOffset" not in harness_src:
            tm_missing.append("check_v4.py: raw pointer offset expectation")
        if "raw-ptr-oc-cast-rvalue-op=PtrCast" not in harness_src:
            tm_missing.append("check_v4.py: raw pointer cast expectation")
        if "raw-ptr-oc-bad-diag1-help=raw-pointer offset requires .ace or higher; current honor is .pilot" not in harness_src:
            tm_missing.append("check_v4.py: low honor raw-pointer offset expectation")
        if "raw-ptr-method-collide-call-line=call ccc i64 @RawPtrWrite(i64 41)" not in harness_src:
            tm_missing.append("check_v4.py: RawPtrWrite user call collision expectation")
    else:
        tm_missing.append("check_v4.py harness missing")
    add(
        "V4 trust me block",
        not tm_missing,
        "parse + raw-pointer read/write/offset/cast gates + smokes wired" if not tm_missing else f"{len(tm_missing)} gap(s)",
    )
    if tm_missing:
        failures.append("V4 trust me block parsing regressed: " + "; ".join(tm_missing))

    # Check 7e: V4 semantic-core type/call carriers
    # The Phase-1 semantic core now carries named call-site arguments,
    # primitive carriers, tuple types, and fixed-array types through query
    # slices. Keep this guard narrow: it proves TY/MIR/editor/codegen smoke
    # carriage, plus scalar LLVM plans for primitive carriers; not final
    # runtime, tuple/fixed-array layout, or production backend completeness.
    semantic_core_missing: List[str] = []
    v4_ty_lib_sc = repo / "src" / "compiler" / "v4" / "crates" / "freak_ty" / "src" / "lib.fk"
    v4_mir_lib_sc = repo / "src" / "compiler" / "v4" / "crates" / "freak_mir" / "src" / "lib.fk"
    v4_editor_lib_sc = repo / "src" / "compiler" / "v4" / "crates" / "freak_editor" / "src" / "lib.fk"
    v4_codegen_lib_sc = repo / "src" / "compiler" / "v4" / "crates" / "freak_codegen_llvm" / "src" / "lib.fk"
    v4_check_harness_sc = repo / "src" / "compiler" / "v4" / "check_v4.py"
    v4_primitive_smoke = repo / "src" / "compiler" / "v4" / "tests" / "primitive_types_smoke.fk"
    v4_named_call_smoke = repo / "src" / "compiler" / "v4" / "tests" / "mir_named_call_smoke.fk"
    v4_named_call_editor_smoke = repo / "src" / "compiler" / "v4" / "tests" / "named_call_editor_smoke.fk"
    v4_method_call_smoke = repo / "src" / "compiler" / "v4" / "tests" / "mir_method_call_smoke.fk"
    v4_bound_associated_smoke = repo / "src" / "compiler" / "v4" / "tests" / "mir_bound_associated_smoke.fk"
    v4_bound_associated_editor_smoke = repo / "src" / "compiler" / "v4" / "tests" / "bound_associated_editor_smoke.fk"
    v4_tuple_smoke = repo / "src" / "compiler" / "v4" / "tests" / "mir_tuple_literal_smoke.fk"
    v4_array_smoke = repo / "src" / "compiler" / "v4" / "tests" / "mir_array_literal_smoke.fk"
    if v4_ty_lib_sc.exists():
        ty_src = v4_ty_lib_sc.read_text(encoding="utf-8")
        for needle in (
            'pilot v4_ty_uint = "uint"',
            'pilot v4_ty_tiny = "tiny"',
            'pilot v4_ty_float = "float"',
            'pilot v4_ty_float32 = "float32"',
            'pilot v4_ty_big = "big"',
            'pilot v4_ty_char = "char"',
            'pilot v4_ty_never = "never"',
            "v4_ty_int_literal_type",
            "v4_ty_float_literal_type",
            "v4_ty_is_tuple_type",
            "v4_ty_tuple_slot_type",
            "v4_ty_is_fixed_array_type",
            "v4_ty_fixed_array_length_normalized_text",
            "v4_ty_apply_self_and_doctrine_instance",
            "v4_ty_canonical_type_in_signature",
            "v4_ty_doctrine_method_param_surface_type",
            "v4_ty_doctrine_method_return_type_for_bound",
        ):
            if needle not in ty_src:
                semantic_core_missing.append(f"freak_ty: {needle}")
    else:
        semantic_core_missing.append("freak_ty/src/lib.fk missing")
    if v4_mir_lib_sc.exists():
        mir_src = v4_mir_lib_sc.read_text(encoding="utf-8")
        for needle in (
            "v4_mir_check_call_args",
            "v4_mir_check_callback_call_args",
            "unknown call argument",
            "duplicate call argument",
            "positional call argument after named",
            "unknown method argument",
            "duplicate method argument",
            "positional method argument after named",
            "v4_mir_check_ufcs_method_args",
            "v4_mir_check_bound_ufcs_method_args",
            "v4_mir_bound_method_ref_with_doctrine",
            "v4_mir_bound_method_ref_doctrine_instance",
            "v4_mir_bound_method_candidate_count",
            "ambiguous doctrine-bound method",
            "UFCS receiver type mismatch",
            "v4_mir_try_lower_tuple_literal",
            "v4_mir_check_fixed_array_literal",
            "v4_mir_fixed_array_slot_count",
        ):
            if needle not in mir_src:
                semantic_core_missing.append(f"freak_mir: {needle}")
    else:
        semantic_core_missing.append("freak_mir/src/lib.fk missing")
    if v4_editor_lib_sc.exists():
        editor_src = v4_editor_lib_sc.read_text(encoding="utf-8")
        for needle in (
            "v4_editor_doctrine_method_explicit_param_name_span",
            "v4_ty_doctrine_method_explicit_param_type_for_bound",
            "v4_mir_bound_method_ref_doctrine_instance",
        ):
            if needle not in editor_src:
                semantic_core_missing.append(f"freak_editor: {needle}")
    else:
        semantic_core_missing.append("freak_editor/src/lib.fk missing")
    if v4_codegen_lib_sc.exists():
        cg_src = v4_codegen_lib_sc.read_text(encoding="utf-8")
        for needle in (
            "ty_name == v4_ty_uint",
            "ty_name == v4_ty_tiny",
            "ty_name == v4_ty_float32",
            "ty_name == v4_ty_char",
            "ty_name == v4_ty_big",
            "ty_name == v4_ty_never",
        ):
            if needle not in cg_src:
                semantic_core_missing.append(f"freak_codegen_llvm: {needle}")
    else:
        semantic_core_missing.append("freak_codegen_llvm/src/lib.fk missing")
    for smoke_path, label in (
        (v4_primitive_smoke, "primitive_types_smoke.fk"),
        (v4_named_call_smoke, "mir_named_call_smoke.fk"),
        (v4_named_call_editor_smoke, "named_call_editor_smoke.fk"),
        (v4_method_call_smoke, "mir_method_call_smoke.fk"),
        (v4_bound_associated_smoke, "mir_bound_associated_smoke.fk"),
        (v4_bound_associated_editor_smoke, "bound_associated_editor_smoke.fk"),
        (v4_tuple_smoke, "mir_tuple_literal_smoke.fk"),
        (v4_array_smoke, "mir_array_literal_smoke.fk"),
    ):
        if not smoke_path.exists():
            semantic_core_missing.append(f"smoke fixture: {label}")
    if v4_bound_associated_smoke.exists():
        bound_associated_src = v4_bound_associated_smoke.read_text(encoding="utf-8")
        for needle in (
            'alias Value = word',
            'alias T = word',
            'Convert<int> + Convert<word>',
        ):
            if needle not in bound_associated_src:
                semantic_core_missing.append(f"mir_bound_associated_smoke.fk: {needle}")
    if v4_check_harness_sc.exists():
        harness_src = v4_check_harness_sc.read_text(encoding="utf-8")
        for needle in (
            "primitive_types_smoke.fk",
            "primitive-known-uint=true",
            "primitive-known-tiny=true",
            "primitive-known-float32=true",
            "primitive-known-char=true",
            "primitive-known-big=true",
            "primitive-known-never=true",
            "mir_named_call_smoke.fk",
            "named-compose-arg0-text=localhost",
            "named-unknown-message0=unknown call argument",
            "named-duplicate-message1=duplicate method argument",
            "named-positional-message0=positional call argument after named",
            "named_call_editor_smoke.fk",
            "named-call-editor-compose-timeout-found=true",
            "mir_method_call_smoke.fk",
            "ufcs-boost-call-op=Pilot::boost",
            "ufcs-take-call-op=Box<int>::take",
            "bad-ufcs-receiver-message=UFCS receiver type mismatch",
            "mir_bound_associated_smoke.fk",
            "bound-associated-ufcs-op=T::score",
            "bound-associated-static-op=T::baseline",
            "bound-associated-bad-diag0-message=UFCS receiver type mismatch",
            "bound-associated-bad-diag4-message=ambiguous doctrine-bound method",
            "bound_associated_editor_smoke.fk",
            "bound-associated-editor-ufcs-definition-matches=true",
            "bound-associated-editor-bonus-completion-detail=parameter bonus: int",
            "bound-associated-editor-ambiguous-completion-found=false",
            "mir_tuple_literal_smoke.fk",
            "tuple-local0-ty=(int,word)",
            "tuple-bad-mismatch-message=local declaration type mismatch",
            "mir_array_literal_smoke.fk",
            "array-trio-rvalue-ty=[int;3]",
            "array-bad-length-message=array length mismatch",
        ):
            if needle not in harness_src:
                semantic_core_missing.append(f"check_v4.py: {needle}")
    else:
        semantic_core_missing.append("check_v4.py harness missing")
    add(
        "V4 semantic core",
        not semantic_core_missing,
        "named calls + concrete/bound UFCS + primitive/tuple/fixed-array carriers wired" if not semantic_core_missing else f"{len(semantic_core_missing)} gap(s)",
    )
    if semantic_core_missing:
        failures.append("V4 semantic-core carrier surface regressed: " + "; ".join(semantic_core_missing))

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

    # ── Check 10: V4 contract-region source sets ──
    # Borrowed return signatures may select every parameter whose lifetime
    # outlives the return region. Require the set-valued TY/MIR/Meiya contract,
    # editor lifetime resolution, and executable source-set fixtures.
    v4_ty_lib_return = repo / "src" / "compiler" / "v4" / "crates" / "freak_ty" / "src" / "lib.fk"
    v4_mir_lib_return = repo / "src" / "compiler" / "v4" / "crates" / "freak_mir" / "src" / "lib.fk"
    v4_borrowck_lib_return = repo / "src" / "compiler" / "v4" / "crates" / "freak_borrowck" / "src" / "lib.fk"
    v4_editor_lib_return = repo / "src" / "compiler" / "v4" / "crates" / "freak_editor" / "src" / "lib.fk"
    v4_tests_return = repo / "src" / "compiler" / "v4" / "tests"
    v4_lend_return_smoke = v4_tests_return / "lend_return_smoke.fk"
    v4_lend_return_editor_smoke = v4_tests_return / "lend_return_editor_smoke.fk"
    v4_lend_return_invalidation_smoke = v4_tests_return / "lend_return_query_invalidation_smoke.fk"
    v4_named_lifetime_return_smoke = v4_tests_return / "named_lifetime_return_smoke.fk"
    v4_named_lifetime_diagnostics_smoke = v4_tests_return / "named_lifetime_diagnostics_smoke.fk"
    v4_named_lifetime_editor_smoke = v4_tests_return / "named_lifetime_editor_smoke.fk"
    v4_named_lifetime_invalidation_smoke = v4_tests_return / "named_lifetime_query_invalidation_smoke.fk"
    v4_check_harness_return = repo / "src" / "compiler" / "v4" / "check_v4.py"
    contract_region_missing: List[str] = []
    if v4_ty_lib_return.exists():
        ty_src = v4_ty_lib_return.read_text(encoding="utf-8")
        for needle in (
            "v4_ty_lend_type_with_lifetime",
            "v4_ty_lend_lifetime",
            "v4_ty_signature_param_lifetime",
            "v4_ty_type_text_suffix_is_keyword",
            "v4_ty_is_lend_type",
            "v4_ty_signature_generic_segment_start",
            "v4_ty_signature_generic_segment_end",
            "v4_ty_signature_generic_segment_span",
            "v4_ty_signature_generic_raw_bound_count",
            "v4_ty_signature_generic_raw_bound_name",
            "v4_ty_signature_generic_has_empty_bound_clause",
            "v4_ty_signature_lifetime_outlives_ids",
            "v4_ty_signature_lifetime_outlives",
            "v4_ty_signature_is_ordinary_static_task",
            "task v4_ty_signature_param_is_borrowed_return_source(",
            "task v4_ty_signature_borrowed_return_source_param_count(",
            "task v4_ty_signature_borrowed_return_source_param_at(",
            "v4_ty_signature_can_declare_generics",
            "v4_ty_validate_signature_generic_bounds",
            "v4_ty_type_contains_named_lend",
            "Meiya lifetime debt: empty generic bound on",
            "may only use lifetime bounds",
            "Meiya cannot store a named lend",
            "Meiya lifetime debt: lend type has no valid target",
        ):
            if needle not in ty_src:
                contract_region_missing.append(f"freak_ty: {needle}")
        # Frozen singular query retained only for compatibility. New policy and
        # implementation must use the count/at source-set API required above.
        ty_singular_wrapper = "v4_ty_signature_borrowed_return_source_param("
        if ty_src.count(ty_singular_wrapper) != 1:
            contract_region_missing.append(
                "freak_ty compatibility wrapper must be declaration-only: "
                "v4_ty_signature_borrowed_return_source_param"
            )
    else:
        contract_region_missing.append("freak_ty/src/lib.fk missing")
    if v4_mir_lib_return.exists():
        mir_src = v4_mir_lib_return.read_text(encoding="utf-8")
        for needle in (
            "v4_mir_rvalue_call_borrowed_source_signature_id",
            "v4_mir_rvalue_call_borrowed_source_arg_for_signature",
            "task v4_mir_rvalue_call_borrowed_source_arg_count(",
            "task v4_mir_rvalue_call_borrowed_source_arg_at(",
            "v4_mir_call_result_type",
            "v4_ty_signature_borrowed_return_source_param_count",
            "v4_ty_signature_borrowed_return_source_param_at",
            "task v4_mir_callback_type_contains_lend(",
            "task v4_mir_check_callback_call_args(",
            "Meiya cannot forward borrowed values through an FFI callback yet",
        ):
            if needle not in mir_src:
                contract_region_missing.append(f"freak_mir: {needle}")
        # Frozen singular query retained only for compatibility. Set-valued MIR
        # consumers must use the count/at API required above.
        mir_singular_wrapper = "v4_mir_rvalue_call_borrowed_source_arg("
        if mir_src.count(mir_singular_wrapper) != 1:
            contract_region_missing.append(
                "freak_mir compatibility wrapper must be declaration-only: "
                "v4_mir_rvalue_call_borrowed_source_arg"
            )
    else:
        contract_region_missing.append("freak_mir/src/lib.fk missing")
    if v4_borrowck_lib_return.exists():
        borrowck_src = v4_borrowck_lib_return.read_text(encoding="utf-8")
        for needle in (
            'v4_borrowck_provenance_known = "known"',
            'v4_borrowck_provenance_opaque = "opaque"',
            "v4_borrowck_provenance_new",
            "v4_borrowck_provenance_is_known",
            "v4_borrowck_provenance_mark_opaque",
            "task v4_borrowck_provenance_count(",
            "v4_borrowck_provenance_is_known_empty",
            "task v4_borrowck_provenance_source_row_at(",
            "task v4_borrowck_provenance_path_at(",
            "task v4_borrowck_provenance_origin_at(",
            "v4_borrowck_provenance_contains_path",
            "v4_borrowck_provenance_overlaps_path",
            "v4_borrowck_provenance_add_source",
            "v4_borrowck_provenance_union_into",
            "task v4_borrowck_provenance_union_borrow_capable_call_args(",
            "task v4_borrowck_fill_return_call_lend_provenance(",
            "v4_borrowck_provenance_scratch_reset",
            "v4_borrowck_provenance_state_active_count",
            "v4_borrowck_provenance_source_active_count",
            "v4_borrowck_provenance_memo_lookup",
            "v4_borrowck_provenance_memo_mark_ready",
            "v4_borrowck_provenance_memo_hit_count",
            "pilot v4_borrowck_source_provenance_ids = 0",
            "pilot v4_borrowck_source_paths = 0",
            "pilot v4_borrowck_source_origins = 0",
            "task v4_borrowck_return_call_lend_provenance(",
            "task v4_borrowck_return_lend_provenance(",
            "v4_borrowck_return_has_loop_carried_rebind",
            "v4_borrowck_check_returned_lends",
            "v4_borrowck_check_stored_call_lends",
            "v4_borrowck_stored_call_return_holder",
            "v4_borrowck_holder_alias_from_stmt",
            "v4_borrowck_rvalue_resolves_lend_source",
            "v4_borrowck_rvalue_returns_holder",
            "v4_borrowck_holder_state",
            "v4_borrowck_holder_reaches_stmt_without_rebind",
            "v4_borrowck_call_lends_source",
            "v4_borrowck_explicit_loan_holder",
            "v4_borrowck_holder_used_at_or_after_write",
            "v4_borrowck_explicit_loan_live_at_write",
            "v4_borrowck_explicit_loan_live_at_move",
            "v4_mir_rvalue_call_borrowed_source_arg_count",
            "v4_mir_rvalue_call_borrowed_source_arg_at",
            'v4_borrowck_path_return_loan = "ReturnLoan"',
            'v4_borrowck_path_return_loan_mut = "ReturnLoanMut"',
            "Meiya cannot establish the origin of this returned loan",
            "Meiya refuses to return a loan of an owned value",
            "Meiya refuses a mutable reloan from an immutable lend",
            "Meiya refuses a returned loan from the wrong lifetime",
            "Meiya cannot store this borrowed call result yet",
        ):
            if needle not in borrowck_src:
                contract_region_missing.append(f"freak_borrowck: {needle}")
        # Frozen singular origin query retained only for compatibility. The
        # provenance set is the authoritative borrowck contract.
        borrowck_singular_wrapper = "v4_borrowck_return_lend_origin("
        if borrowck_src.count(borrowck_singular_wrapper) != 1:
            contract_region_missing.append(
                "freak_borrowck compatibility wrapper must be declaration-only: "
                "v4_borrowck_return_lend_origin"
            )
        if "Meiya cannot choose one source for this returned loan" in borrowck_src:
            contract_region_missing.append(
                "freak_borrowck stale exact-one diagnostic: "
                "Meiya cannot choose one source for this returned loan"
            )
        if "v4_borrowck_return_ambiguous_help(" in borrowck_src:
            contract_region_missing.append(
                "freak_borrowck retains stale exact-one advice: "
                "v4_borrowck_return_ambiguous_help"
            )
    else:
        contract_region_missing.append("freak_borrowck/src/lib.fk missing")
    if v4_editor_lib_return.exists():
        editor_src = v4_editor_lib_return.read_text(encoding="utf-8")
        for needle in (
            'if kind == "Lifetime"',
            "v4_editor_lifetime_def",
            "v4_ty_signature_declares_lifetime_name",
            "v4_editor_lifetime_decl_span",
            "v4_ty_signature_generic_segment_start",
            "v4_ty_signature_generic_segment_end",
            "span = v4_editor_lifetime_decl_span",
        ):
            if needle not in editor_src:
                contract_region_missing.append(f"freak_editor: {needle}")
    else:
        contract_region_missing.append("freak_editor/src/lib.fk missing")
    if v4_lend_return_smoke.exists():
        return_smoke_src = v4_lend_return_smoke.read_text(encoding="utf-8")
        for needle in (
            'lend-return-forward-status=',
            'lend-return-forward-holder-status=',
            'lend-return-forward-branches-status=',
            'lend-return-forward-ambiguous-branches-status=',
            'lend-return-forward-ambiguous-call-status=',
            'lend-return-loop-carried-status=',
            'lend-return-restored-forward-region-source=',
        ):
            if needle not in return_smoke_src:
                contract_region_missing.append(f"lend_return_smoke: {needle}")
    else:
        contract_region_missing.append("smoke fixture: lend_return_smoke.fk")
    if not v4_lend_return_editor_smoke.exists():
        contract_region_missing.append("smoke fixture: lend_return_editor_smoke.fk")
    if not v4_lend_return_invalidation_smoke.exists():
        contract_region_missing.append("smoke fixture: lend_return_query_invalidation_smoke.fk")
    named_smoke_needles = (
        (
            v4_named_lifetime_return_smoke,
            (
                "named-lifetime-projection-source-param=",
                "named-lifetime-reordered-path-source=",
                "named-lifetime-wrong-holder-status=",
                "named-lifetime-wrong-call-status=",
                "named-lifetime-holder-move-status=",
                "named-lifetime-nested-move-status=",
                "named-lifetime-ambiguous-holder-move-status=",
                "named-lifetime-call-local-type=",
            ),
        ),
        (
            v4_named_lifetime_diagnostics_smoke,
            (
                "StoredLoan<'a>",
                "StoredRoute<'a>",
                "StoredAlias<'a>",
                "missing_target<'a>",
                "-span=",
            ),
        ),
        (
            v4_named_lifetime_editor_smoke,
            (
                "named-lifetime-editor-label-definition-matches=",
                "named-lifetime-editor-elided-definition=",
                "v4_semantic_snapshot_restore",
                "v4_hover_snapshot_restore",
                "v4_definition_snapshot_restore",
                "v4_diagnostics_snapshot_restore",
            ),
        ),
        (
            v4_named_lifetime_invalidation_smoke,
            (
                "named-lifetime-query-ty-invalidated=",
                "named-lifetime-query-after-hover=",
                "named-lifetime-query-after-definition-matches=",
            ),
        ),
    )
    for fixture_path, needles in named_smoke_needles:
        if fixture_path.exists():
            fixture_src = fixture_path.read_text(encoding="utf-8")
            for needle in needles:
                if needle not in fixture_src:
                    contract_region_missing.append(f"{fixture_path.name}: {needle}")
        else:
            contract_region_missing.append(f"smoke fixture: {fixture_path.name}")

    contract_region_smoke_needles = (
        (
            v4_tests_return / "contract_region_source_set_smoke.fk",
            (
                "task choose<'a>(lend 'a left: Ship, lend 'a right: Ship",
                "give back choose(lend first, lend second, take_first)",
                "contract-region-source-set-choose-status=",
                'v4_contract_region_source_set_emit_sources("contract-region-source-set-forward"',
                'v4_contract_region_source_set_emit_sources("contract-region-source-set-projection"',
            ),
        ),
        (
            v4_tests_return / "contract_region_mutability_smoke.fk",
            (
                "task shared_from_both<'a>(lend 'a observed: Ship, lend mut 'a writable: Ship",
                "task mutable_from_mutable<'a>(lend mut 'a left: Ship, lend mut 'a right: Ship",
                "give back lend mut observer",
                "contract-region-mutability-ineligible-status=",
                'v4_contract_region_mutability_emit_sources("contract-region-mutability-mut"',
            ),
        ),
        (
            v4_tests_return / "contract_region_outlives_smoke.fk",
            (
                "task direct<'short, 'long: 'short>",
                "task transitive<'short, 'middle: 'short, 'long: 'middle>",
                "task multiple<'short, 'middle, 'long: 'short + 'middle>",
                "task equivalent<'left: 'right, 'right: 'left>",
                "contract-region-outlives-direct-raw-bound-count=",
                "contract-region-outlives-transitive-long-outlives-short=",
                "contract-region-outlives-direct-short-reflexive=",
                "contract-region-outlives-equivalent-right-outlives-left=",
                'v4_contract_region_outlives_emit_sources("contract-region-outlives-transitive"',
            ),
        ),
        (
            v4_tests_return / "contract_region_relation_negative_smoke.fk",
            (
                "task reverse<'long, 'short: 'long>",
                "task missing<'short, 'long>",
                "contract-region-relation-negative-reverse-long-outlives-short=",
                "contract-region-relation-negative-missing-long-outlives-short=",
                "contract-region-relation-negative-missing-status=",
            ),
        ),
        (
            v4_tests_return / "contract_region_relation_stress_smoke.fk",
            (
                "repeat until generic_id >= 48",
                "v4_ty_signature_lifetime_outlives",
                "contract-region-relation-stress-fibonacci-transitive=",
                "contract-region-relation-stress-chain-reachable=",
                "contract-region-relation-stress-cycle-right-left=",
                "contract-region-relation-stress-extern-gated=",
            ),
        ),
        (
            v4_tests_return / "contract_region_bound_diagnostics_smoke.fk",
            (
                "task undeclared_bound<'a: 'ghost>",
                "task empty_bound<'a:>",
                "task lifetime_doctrine_bound<'a: Copy>",
                "task type_lifetime_bound<T: 'a, 'a>",
                "shape ShapeLifetimeDoctrine<'short, 'long: 'short, 'a: Copy>",
                "route RouteTypeLifetime<T: 'a, 'a>",
                "doctrine DoctrineEmptyType<T:>",
                "alias AliasMixedType<T: Copy + 'a, 'a>",
                "task extern_empty_type<'short, 'long: 'short, T:>",
                "contract-region-bound-diagnostics-empty-raw-bound-count=",
                "contract-region-bound-diagnostics-extern-ordinary-static=",
                "contract-region-bound-diagnostics-extern-source-count=",
                "contract-region-bound-diagnostics-diag",
            ),
        ),
        (
            v4_tests_return / "contract_region_loop_negative_smoke.fk",
            (
                "task loop_carried<'a>(lend 'a first: Ship, lend 'a second: Ship",
                "view = lend second",
                "contract-region-loop-negative-status=",
                "contract-region-loop-negative-borrow-diagnostics=",
                "contract-region-loop-negative-diag",
            ),
        ),
        (
            v4_tests_return / "contract_region_storage_negative_smoke.fk",
            (
                "pilot view = choose(lend first, lend second, take_first)",
                "pilot views = (choose(lend first, lend second, take_first), lend first)",
                "give back 7",
                "contract-region-storage-mir-diag0-message=",
                "contract-region-storage-local-holder-status=",
                "contract-region-storage-aggregate-status=",
                "contract-region-storage-diag",
            ),
        ),
        (
            v4_tests_return / "contract_region_boundary_negative_smoke.fk",
            (
                "doctrine Selector<'a>",
                "task callback_boundary<'a>(cb: task(left: lend 'a Ship, right: lend 'a Ship) -> lend 'a Ship)",
                "task static_boundary(lend 'static value: Ship) -> lend 'static Ship",
                "task v4_contract_region_boundary_negative_emit_diag(ty_id: int, diag_id: int) -> void {",
                'say "contract-region-boundary-negative-diagnostics-exact-four="',
                "v4_contract_region_boundary_negative_emit_diag(v4_contract_region_boundary_negative_ty, 3)",
            ),
        ),
        (
            v4_tests_return / "contract_region_forwarding_boundary_negative_smoke.fk",
            (
                "task v4_contract_region_forwarding_boundary_method_source() -> word {",
                "task v4_contract_region_forwarding_boundary_dynamic_source() -> word {",
                "task v4_contract_region_forwarding_boundary_callback_source() -> word {",
                "task v4_contract_region_forwarding_boundary_extern_source() -> word {",
                "task v4_contract_region_forwarding_boundary_ffi_source() -> word {",
                "task v4_contract_region_forwarding_boundary_mir_diag_span(",
                "task v4_contract_region_forwarding_boundary_borrow_diag_span(",
                'pilot v4_contract_region_forwarding_boundary_ffi_message = "Meiya cannot forward borrowed values through an FFI callback yet"',
                'v4_contract_region_forwarding_boundary_emit("contract-region-forwarding-ffi", v4_contract_region_forwarding_boundary_ffi_borrow, "ffi_forward", "mir", v4_contract_region_forwarding_boundary_ffi_message)',
                'say "contract-region-forwarding-closure-coverage=unsupported-no-v4-closure-syntax"',
            ),
        ),
        (
            v4_tests_return / "contract_region_editor_smoke.fk",
            (
                "task shorten<'long: 'out + 'out, 'out, 'wide: 'alt, 'alt>",
                "contract-region-editor-bound-semantic-def-matches-binder=",
                "contract-region-editor-bound-definition-matches-later-binder=",
                "contract-region-editor-repeated-definition-matches-later-binder=",
                "contract-region-editor-alt-definition-matches-alt-binder=",
                "v4_contract_region_editor_blocked_confirm = v4_driver_confirm_restored_key(",
                "v4_contract_region_editor_mismatch_confirm = v4_driver_confirm_restored_key(",
                "v4_contract_region_editor_promoted_confirm = v4_driver_confirm_restored_key(",
                "v4_contract_region_editor_document_confirm = v4_driver_confirm_restored_document(",
                "contract-region-editor-restored-alt-definition-query-nonempty=",
                "contract-region-editor-restored-definition-matches-later-binder=",
                "contract-region-editor-restored-alt-definition-matches-alt-binder=",
                "contract-region-editor-restored-definition-spans-distinct=",
            ),
        ),
        (
            v4_tests_return / "contract_region_query_invalidation_smoke.fk",
            (
                "task v4_contract_region_query_source(bound_name: word)",
                "v4_contract_region_query_before = v4_contract_region_query_source",
                "v4_contract_region_query_after = v4_contract_region_query_source",
                "contract-region-query-ty-invalidated=",
                "contract-region-query-after-source-count=",
                "contract-region-query-after-bound-definition-matches-alt-binder=",
            ),
        ),
        (
            v4_tests_return / "contract_region_liveness_smoke.fk",
            (
                "task move_first_before(first: Ship, second: Ship",
                "task move_second_before(first: Ship, second: Ship",
                "task nested_move_second_before(first: Ship, second: Ship",
                "contract-region-liveness-ordinary-call-source-count=",
                "contract-region-liveness-first-before-status=",
                "contract-region-liveness-second-before-status=",
                "contract-region-liveness-unrelated-before-status=",
                "contract-region-liveness-empty-union-known-empty=",
                "contract-region-liveness-opaque-overlaps-any-owner=",
                "contract-region-liveness-restored-forward-order-stable=",
            ),
        ),
        (
            v4_tests_return / "contract_region_elided_liveness_smoke.fk",
            (
                'src = src + "task choose(lend first: Ship, lend second: Ship) -> lend Ship {\\n"',
                "v4_ty_signature_borrowed_return_source_param_at(",
                "v4_mir_rvalue_call_borrowed_source_arg_at(",
                "contract-region-elided-liveness-signature-source-count=",
                "contract-region-elided-liveness-call-source-count=",
                "contract-region-elided-liveness-first-before-status=",
                "contract-region-elided-liveness-second-before-status=",
                "contract-region-elided-liveness-unrelated-before-status=",
                "contract-region-elided-liveness-first-after-status=",
                "contract-region-elided-liveness-second-after-status=",
            ),
        ),
        (
            v4_tests_return / "contract_region_elided_query_invalidation_smoke.fk",
            (
                "task v4_contract_region_elided_query_source(second_mode: word) -> word {",
                'src = src + "task choose(lend first: Ship, " + second_mode + "second: Ship) -> lend Ship {\\n"',
                'v4_lsp_handle_text_request("textDocument/didChange", v4_contract_region_elided_query_path, v4_contract_region_elided_query_after, 0)',
                "contract-region-elided-query-before-source-count=",
                "contract-region-elided-query-before-call-source-count=",
                "contract-region-elided-query-ty-invalidations-added=",
                "contract-region-elided-query-definition-recomputations-added=",
                "contract-region-elided-query-after-source-count=",
                "contract-region-elided-query-after-call-source-count=",
                "contract-region-elided-query-after-semantic=",
                "contract-region-elided-query-after-definition=",
            ),
        ),
        (
            v4_tests_return / "contract_region_resource_smoke.fk",
            (
                "repeat until level > 12",
                "v4_borrowck_check_mir(0, v4_contract_region_resource_mir)",
                "contract-region-resource-generation-sequence=",
                "contract-region-resource-memo-hits=",
                "contract-region-resource-capacities-reused=",
                "contract-region-resource-no-historical-growth=",
                "contract-region-resource-opaque-conservative=",
            ),
        ),
    )
    for fixture_path, needles in contract_region_smoke_needles:
        if fixture_path.exists():
            fixture_src = fixture_path.read_text(encoding="utf-8")
            for needle in needles:
                if needle not in fixture_src:
                    contract_region_missing.append(f"{fixture_path.name}: {needle}")
        else:
            contract_region_missing.append(f"smoke fixture: {fixture_path.name}")

    # These literal output oracles are the primary executable contract. The
    # source/API needles above remain useful secondary structural guards, but
    # cannot substitute for exact expectations in the harness manifest.
    required_harness_expects = {
        "lend_return_smoke.fk": (
            "lend-return-ambiguous-diagnostics=0",
        ),
        "lend_return_query_invalidation_smoke.fk": (
            "lend-return-query-before-message=none",
        ),
        "named_lifetime_diagnostics_smoke.fk": (
            "named-lifetime-diag-repeated-source=-2",
        ),
        "contract_region_source_set_smoke.fk": (
            "contract-region-source-set-ty-diagnostics=0",
            "contract-region-source-set-mir-diagnostics=0",
            "contract-region-source-set-borrow-diagnostics=0",
            "contract-region-source-set-choose-status=clean",
            "contract-region-source-set-forward-status=clean",
            "contract-region-source-set-projection-status=clean",
            "contract-region-source-set-choose-source0=right",
            "contract-region-source-set-choose-source1=left",
            "contract-region-source-set-choose-source-count=2",
            "contract-region-source-set-forward-source0=first",
            "contract-region-source-set-forward-source1=second",
            "contract-region-source-set-forward-source-count=2",
            "contract-region-source-set-projection-source0=fleet.lead",
            "contract-region-source-set-projection-source1=spare",
            "contract-region-source-set-projection-source-count=2",
        ),
        "contract_region_mutability_smoke.fk": (
            "contract-region-mutability-ty-diagnostics=0",
            "contract-region-mutability-mir-diagnostics=0",
            "contract-region-mutability-shared-status=clean",
            "contract-region-mutability-mut-status=clean",
            "contract-region-mutability-ineligible-status=blocked",
            "contract-region-mutability-shared-source0=observed",
            "contract-region-mutability-shared-source1=writable",
            "contract-region-mutability-shared-source-count=2",
            "contract-region-mutability-mut-source0=right",
            "contract-region-mutability-mut-source1=left",
            "contract-region-mutability-mut-source-count=2",
            "contract-region-mutability-borrow-diagnostics=1",
            "contract-region-mutability-diag0=Meiya refuses a mutable reloan from an immutable lend",
            "contract-region-mutability-diag0-span=0@",
        ),
        "contract_region_outlives_smoke.fk": (
            "contract-region-outlives-direct-raw-bound-count=1",
            "contract-region-outlives-direct-long-raw-bound='short",
            "contract-region-outlives-transitive-middle-raw-bound='short",
            "contract-region-outlives-transitive-long-raw-bound='middle",
            "contract-region-outlives-multiple-raw-bound-count=2",
            "contract-region-outlives-multiple-raw-bound0='short",
            "contract-region-outlives-multiple-raw-bound1='middle",
            "contract-region-outlives-direct-short-reflexive=true",
            "contract-region-outlives-direct-long-outlives-short=true",
            "contract-region-outlives-transitive-middle-outlives-short=true",
            "contract-region-outlives-transitive-long-outlives-middle=true",
            "contract-region-outlives-transitive-long-outlives-short=true",
            "contract-region-outlives-multiple-long-outlives-short=true",
            "contract-region-outlives-multiple-long-outlives-middle=true",
            "contract-region-outlives-equivalent-left-outlives-right=true",
            "contract-region-outlives-equivalent-right-outlives-left=true",
            "contract-region-outlives-ty-diagnostics=0",
            "contract-region-outlives-mir-diagnostics=0",
            "contract-region-outlives-borrow-diagnostics=0",
            "contract-region-outlives-direct-status=clean",
            "contract-region-outlives-transitive-status=clean",
            "contract-region-outlives-multiple-status=clean",
            "contract-region-outlives-equivalent-status=clean",
            "contract-region-outlives-direct-source-count=2",
            "contract-region-outlives-transitive-source-count=3",
            "contract-region-outlives-multiple-source-count=1",
            "contract-region-outlives-equivalent-source-count=1",
        ),
        "contract_region_relation_negative_smoke.fk": (
            "contract-region-relation-negative-reverse-raw-bound='long",
            "contract-region-relation-negative-reverse-long-outlives-short=false",
            "contract-region-relation-negative-reverse-short-outlives-long=true",
            "contract-region-relation-negative-missing-long-outlives-short=false",
            "contract-region-relation-negative-ty-diagnostics=0",
            "contract-region-relation-negative-mir-diagnostics=0",
            "contract-region-relation-negative-reverse-status=blocked",
            "contract-region-relation-negative-missing-status=blocked",
            "contract-region-relation-negative-borrow-diagnostics=2",
            "contract-region-relation-negative-diag0=Meiya refuses a returned loan from the wrong lifetime",
            "contract-region-relation-negative-diag1=Meiya refuses a returned loan from the wrong lifetime",
        ),
        "contract_region_relation_stress_smoke.fk": (
            "contract-region-relation-stress-parse-diagnostics=0",
            "contract-region-relation-stress-ty-diagnostics=0",
            "contract-region-relation-stress-fibonacci-lifetime-count=41",
            "contract-region-relation-stress-fibonacci-disconnected=false",
            "contract-region-relation-stress-fibonacci-transitive=true",
            "contract-region-relation-stress-fibonacci-plus-bound=true",
            "contract-region-relation-stress-chain-lifetime-count=48",
            "contract-region-relation-stress-chain-reachable=true",
            "contract-region-relation-stress-chain-reverse=false",
            "contract-region-relation-stress-cycle-left-right=true",
            "contract-region-relation-stress-cycle-right-left=true",
            "contract-region-relation-stress-declared-reflexive=true",
            "contract-region-relation-stress-undeclared-reflexive=false",
            "contract-region-relation-stress-static-reflexive=false",
            "contract-region-relation-stress-extern-gated=false",
        ),
        "contract_region_bound_diagnostics_smoke.fk": (
            "contract-region-bound-diagnostics-undeclared-raw-bound='ghost",
            "contract-region-bound-diagnostics-reserved-raw-bound='static",
            "contract-region-bound-diagnostics-elided-raw-bound='_",
            "contract-region-bound-diagnostics-empty-raw-bound-count=0",
            "contract-region-bound-diagnostics-lifetime-doctrine-raw-bound=Copy",
            "contract-region-bound-diagnostics-type-lifetime-raw-bound='a",
            "contract-region-bound-diagnostics-shape-kind=shape-signature",
            "contract-region-bound-diagnostics-shape-lifetime-doctrine-raw-bound=Copy",
            "contract-region-bound-diagnostics-shape-lifetime-doctrine-filtered-count=0",
            "contract-region-bound-diagnostics-shape-outlives=false",
            "contract-region-bound-diagnostics-route-kind=route-signature",
            "contract-region-bound-diagnostics-route-type-lifetime-raw-bound='a",
            "contract-region-bound-diagnostics-route-type-lifetime-filtered-count=0",
            "contract-region-bound-diagnostics-doctrine-kind=doctrine-signature",
            "contract-region-bound-diagnostics-doctrine-empty-type-raw-count=0",
            "contract-region-bound-diagnostics-doctrine-empty-type-clause=true",
            "contract-region-bound-diagnostics-alias-kind=alias-signature",
            "contract-region-bound-diagnostics-alias-mixed-raw-count=2",
            "contract-region-bound-diagnostics-alias-mixed-raw0=Copy",
            "contract-region-bound-diagnostics-alias-mixed-raw1='a",
            "contract-region-bound-diagnostics-alias-mixed-filtered-count=1",
            "contract-region-bound-diagnostics-alias-mixed-filtered0=Copy",
            "contract-region-bound-diagnostics-extern-kind=task-signature",
            "contract-region-bound-diagnostics-extern-member-id=0",
            "contract-region-bound-diagnostics-extern-generic-count=3",
            "contract-region-bound-diagnostics-extern-long-raw-bound='short",
            "contract-region-bound-diagnostics-extern-empty-type-raw-count=0",
            "contract-region-bound-diagnostics-extern-empty-type-clause=true",
            "contract-region-bound-diagnostics-extern-ordinary-static=false",
            "contract-region-bound-diagnostics-extern-outlives=false",
            "contract-region-bound-diagnostics-extern-source-count=0",
            "contract-region-bound-diagnostics-extern-source-at0=-1",
            "contract-region-bound-diagnostics-count=11",
            "Meiya lifetime debt: lifetime bound 'ghost on 'a is not declared on undeclared_bound",
            "Meiya lifetime debt: 'static is reserved and cannot be used as a lifetime bound on 'a",
            "Meiya lifetime debt: '_ is elided and cannot be used as a lifetime bound on 'a",
            "Meiya lifetime debt: empty generic bound on 'a in empty_bound",
            "Meiya lifetime debt: lifetime 'a may only use lifetime bounds, but found Copy",
            "Meiya lifetime debt: type generic T cannot use lifetime bound 'a",
            "contract-region-bound-diagnostics-diag6=Meiya lifetime debt: lifetime 'a may only use lifetime bounds, but found Copy",
            "contract-region-bound-diagnostics-diag6-span=0@",
            "contract-region-bound-diagnostics-diag7=Meiya lifetime debt: type generic T cannot use lifetime bound 'a",
            "contract-region-bound-diagnostics-diag7-span=0@",
            "contract-region-bound-diagnostics-diag8=Meiya lifetime debt: empty generic bound on T in DoctrineEmptyType",
            "contract-region-bound-diagnostics-diag8-span=0@",
            "contract-region-bound-diagnostics-diag9=Meiya lifetime debt: type generic T cannot use lifetime bound 'a",
            "contract-region-bound-diagnostics-diag9-span=0@",
            "contract-region-bound-diagnostics-diag10=Meiya lifetime debt: empty generic bound on T in extern_empty_type",
            "contract-region-bound-diagnostics-diag10-span=0@",
        ),
        "contract_region_loop_negative_smoke.fk": (
            "contract-region-loop-negative-ty-diagnostics=0",
            "contract-region-loop-negative-mir-diagnostics=0",
            "contract-region-loop-negative-status=blocked",
            "contract-region-loop-negative-borrow-diagnostics=1",
            "contract-region-loop-negative-diag0=Meiya cannot establish the origin of this returned loan",
            "contract-region-loop-negative-diag0-span=0@",
        ),
        "contract_region_storage_negative_smoke.fk": (
            "contract-region-storage-ty-diagnostics=0",
            "contract-region-storage-mir-diagnostics=1",
            "contract-region-storage-mir-diag0-message=Meiya cannot store a lend inside a tuple yet",
            "contract-region-storage-mir-diag0-help=aggregate_source_set constructs tuple element 1 with type lend Ship; keep this borrowed value in a scalar local holder until MIR can preserve aggregate child provenance",
            "contract-region-storage-mir-diag0-span=0@",
            "contract-region-storage-choose-status=clean",
            "contract-region-storage-local-holder-status=clean",
            "contract-region-storage-aggregate-status=clean",
            "contract-region-storage-borrow-diagnostics=1",
            "contract-region-storage-diag0=Meiya cannot store a lend inside a tuple yet",
            "contract-region-storage-diag0-span=0@",
        ),
        "contract_region_boundary_negative_smoke.fk": (
            "contract-region-boundary-negative-diagnostics=4",
            "contract-region-boundary-negative-diagnostics-exact-four=true",
            "contract-region-boundary-negative-diag0=Meiya cannot store a named lend in return type of Selector::choose yet",
            "contract-region-boundary-negative-diag0-span=0@117:129",
            "contract-region-boundary-negative-diag0-help=keep named lifetimes on ordinary task lend parameters and outer borrowed returns until aggregate provenance lands",
            "contract-region-boundary-negative-diag1=Meiya cannot store a named lend in parameter 0 of callback_boundary yet",
            "contract-region-boundary-negative-diag1-span=0@163:224",
            "contract-region-boundary-negative-diag1-help=keep named lifetimes on ordinary task lend parameters and outer borrowed returns until aggregate provenance lands",
            "contract-region-boundary-negative-diag2=Meiya cannot accept a static lend parameter yet",
            "contract-region-boundary-negative-diag2-span=0@279:286",
            "contract-region-boundary-negative-diag2-help='static needs source-storage classification before callers may promise an immortal loan",
            "contract-region-boundary-negative-diag3=Meiya cannot prove a static borrowed return yet",
            "contract-region-boundary-negative-diag3-span=0@303:320",
            "contract-region-boundary-negative-diag3-help='static returned loans need global-storage provenance before this contract can be sound",
        ),
        "contract_region_forwarding_boundary_negative_smoke.fk": (
            "contract-region-forwarding-method-ty-diagnostics=0",
            "contract-region-forwarding-method-mir-diagnostics=1",
            "contract-region-forwarding-method-borrow-diagnostics=2",
            "contract-region-forwarding-method-status=blocked",
            "contract-region-forwarding-method-invocation-diagnostic-count=1",
            "contract-region-forwarding-method-invocation-message=Meiya cannot establish the origin of this returned loan",
            "contract-region-forwarding-method-invocation-span=0@255:282",
            "contract-region-forwarding-method-rejected=true",
            "contract-region-forwarding-method-silently-accepted=false",
            "contract-region-forwarding-dynamic-ty-diagnostics=0",
            "contract-region-forwarding-dynamic-mir-diagnostics=1",
            "contract-region-forwarding-dynamic-borrow-diagnostics=2",
            "contract-region-forwarding-dynamic-status=blocked",
            "contract-region-forwarding-dynamic-invocation-diagnostic-count=1",
            "contract-region-forwarding-dynamic-invocation-message=Meiya cannot establish the origin of this returned loan",
            "contract-region-forwarding-dynamic-invocation-span=1@346:373",
            "contract-region-forwarding-dynamic-rejected=true",
            "contract-region-forwarding-dynamic-silently-accepted=false",
            "contract-region-forwarding-callback-ty-diagnostics=0",
            "contract-region-forwarding-callback-mir-diagnostics=1",
            "contract-region-forwarding-callback-borrow-diagnostics=1",
            "contract-region-forwarding-callback-status=clean",
            "contract-region-forwarding-callback-invocation-diagnostic-count=1",
            "contract-region-forwarding-callback-invocation-message=call target is not callable",
            "contract-region-forwarding-callback-invocation-span=2@136:150",
            "contract-region-forwarding-callback-rejected=true",
            "contract-region-forwarding-callback-silently-accepted=false",
            "contract-region-forwarding-extern-ty-diagnostics=2",
            "contract-region-forwarding-extern-mir-diagnostics=2",
            "contract-region-forwarding-extern-borrow-diagnostics=3",
            "contract-region-forwarding-extern-status=blocked",
            "contract-region-forwarding-extern-invocation-diagnostic-count=1",
            "contract-region-forwarding-extern-invocation-message=Meiya cannot establish the origin of this returned loan",
            "contract-region-forwarding-extern-invocation-span=3@162:187",
            "contract-region-forwarding-extern-rejected=true",
            "contract-region-forwarding-extern-silently-accepted=false",
            "contract-region-forwarding-ffi-ty-diagnostics=1",
            "contract-region-forwarding-ffi-mir-diagnostics=3",
            "contract-region-forwarding-ffi-borrow-diagnostics=3",
            "contract-region-forwarding-ffi-status=clean",
            "contract-region-forwarding-ffi-invocation-diagnostic-count=1",
            "contract-region-forwarding-ffi-invocation-message=Meiya cannot forward borrowed values through an FFI callback yet",
            "contract-region-forwarding-ffi-invocation-span=4@198:222",
            "contract-region-forwarding-ffi-rejected=true",
            "contract-region-forwarding-ffi-silently-accepted=false",
            "contract-region-forwarding-closure-coverage=unsupported-no-v4-closure-syntax",
        ),
        "contract_region_editor_smoke.fk": (
            "contract-region-editor-bound-semantic-name='out",
            "contract-region-editor-bound-semantic-kind=Lifetime",
            "contract-region-editor-bound-semantic-type=lifetime 'out on task shorten",
            "contract-region-editor-bound-semantic-def-matches-binder=true",
            "contract-region-editor-bound-hover-name='out",
            "contract-region-editor-bound-hover-kind=Lifetime",
            "contract-region-editor-bound-hover-type=lifetime 'out on task shorten",
            "contract-region-editor-bound-hover-name-matches-binder=true",
            "contract-region-editor-bound-hover-type-matches-binder=true",
            "contract-region-editor-bound-definition-found=1",
            "contract-region-editor-bound-definition-matches-later-binder=true",
            "contract-region-editor-bound-definition-not-long-binder=true",
            "contract-region-editor-bound-definition-not-bound-use=true",
            "contract-region-editor-repeated-definition-found=1",
            "contract-region-editor-repeated-definition-matches-later-binder=true",
            "contract-region-editor-alt-definition-found=1",
            "contract-region-editor-alt-definition-matches-alt-binder=true",
            "contract-region-editor-definition-records-distinct=true",
            "contract-region-editor-definition-binders-distinct=true",
            "ok|textDocument/hover",
            "**'out** `Lifetime`",
            "ok|textDocument/definition",
            "|'out|Lifetime",
            "semantic-snapshot-import ok=1",
            "hover-snapshot-import ok=1",
            "definition-snapshot-import ok=1",
            "semantic-snapshot-restore ok=1",
            "hover-snapshot-restore ok=1",
            "definition-snapshot-restore ok=1",
            "query-snapshot-restore ok=1",
            "contract-region-editor-blocked-confirm-promoted=0",
            "contract-region-editor-blocked-confirm-blocked=1",
            "contract-region-editor-blocked-confirm-mismatched=0",
            "contract-region-editor-mismatch-confirm-promoted=0",
            "contract-region-editor-mismatch-confirm-blocked=0",
            "contract-region-editor-mismatch-confirm-mismatched=1",
            "contract-region-editor-promoted-confirm-promoted=1",
            "contract-region-editor-promoted-confirm-blocked=0",
            "contract-region-editor-promoted-confirm-mismatched=0",
            "contract-region-editor-document-confirm-promoted=17",
            "contract-region-editor-document-confirm-blocked=0",
            "contract-region-editor-document-confirm-mismatched=0",
            "contract-region-editor-restored-semantic-query-nonempty=true",
            "contract-region-editor-restored-hover-query-nonempty=true",
            "contract-region-editor-restored-definition-query-nonempty=true",
            "contract-region-editor-restored-repeated-definition-query-nonempty=true",
            "contract-region-editor-restored-alt-definition-query-nonempty=true",
            "contract-region-editor-restored-semantic-kind=Lifetime",
            "contract-region-editor-restored-semantic-type=lifetime 'out on task shorten",
            "contract-region-editor-restored-semantic-def-stable=true",
            "contract-region-editor-restored-hover-kind=Lifetime",
            "contract-region-editor-restored-hover-type=lifetime 'out on task shorten",
            "contract-region-editor-restored-hover-type-stable=true",
            "contract-region-editor-restored-definition-found=1",
            "contract-region-editor-restored-definition-span-stable=true",
            "contract-region-editor-restored-definition-matches-later-binder=true",
            "contract-region-editor-restored-repeated-definition-matches-later-binder=true",
            "contract-region-editor-restored-alt-definition-matches-alt-binder=true",
            "contract-region-editor-restored-definition-records-distinct=true",
            "contract-region-editor-restored-definition-spans-distinct=true",
        ),
        "contract_region_query_invalidation_smoke.fk": (
            "contract-region-query-before-diagnostics=0",
            "contract-region-query-before-status=clean",
            "contract-region-query-before-source-count=2",
            "contract-region-query-before-long-outlives-out=true",
            "contract-region-query-before-long-outlives-alt=false",
            "contract-region-query-before-bound-semantic=lifetime 'out on task shorten",
            "contract-region-query-before-bound-hover=lifetime 'out on task shorten",
            "contract-region-query-before-bound-definition=1",
            "contract-region-query-before-bound-definition-matches-out-binder=true",
            "contract-region-query-bound-offset-stable=true",
            "ok|textDocument/didChange",
            "invalidation-contract|path=contract-region-query-invalidation.fk",
            "contract-region-query-ty-invalidated=true",
            "contract-region-query-mir-invalidated=true",
            "contract-region-query-borrowck-invalidated=true",
            "contract-region-query-diagnostics-invalidated=true",
            "contract-region-query-semantic-invalidated=true",
            "contract-region-query-hover-invalidated=true",
            "contract-region-query-definition-invalidated=true",
            "contract-region-query-ty-recomputed=true",
            "contract-region-query-mir-recomputed=true",
            "contract-region-query-borrowck-recomputed=true",
            "contract-region-query-diagnostics-recomputed=true",
            "contract-region-query-semantic-recomputed=true",
            "contract-region-query-hover-recomputed=true",
            "contract-region-query-definition-recomputed=true",
            "contract-region-query-after-diagnostics=1",
            "contract-region-query-after-message=Meiya refuses a returned loan from the wrong lifetime",
            "contract-region-query-after-status=blocked",
            "contract-region-query-after-source-count=1",
            "contract-region-query-after-long-outlives-out=false",
            "contract-region-query-after-long-outlives-alt=true",
            "contract-region-query-after-bound-semantic=lifetime 'alt on task shorten",
            "contract-region-query-after-bound-hover=lifetime 'alt on task shorten",
            "contract-region-query-after-bound-definition=1",
            "contract-region-query-after-bound-definition-matches-alt-binder=true",
            "contract-region-query-bound-definition-changed=true",
            "diagnostics|1",
        ),
        "contract_region_liveness_smoke.fk": (
            "contract-region-liveness-ty-diagnostics=0",
            "contract-region-liveness-mir-diagnostics=0",
            "contract-region-liveness-borrow-diagnostics=3",
            "contract-region-liveness-move-conflict-diagnostics=3",
            "contract-region-liveness-signature-source-count=2",
            "contract-region-liveness-ordinary-call-source-count=2",
            "contract-region-liveness-ordinary-call-source0=lend first",
            "contract-region-liveness-ordinary-call-source1=lend second",
            "contract-region-liveness-choose-status=clean",
            "contract-region-liveness-forward-status=clean",
            "contract-region-liveness-first-before-status=blocked",
            "contract-region-liveness-second-before-status=blocked",
            "contract-region-liveness-unrelated-before-status=clean",
            "contract-region-liveness-first-after-status=clean",
            "contract-region-liveness-second-after-status=clean",
            "contract-region-liveness-nested-second-before-status=blocked",
            "contract-region-liveness-choose-return-source-count=2",
            "contract-region-liveness-choose-return-source0=first",
            "contract-region-liveness-choose-return-source1=second",
            "contract-region-liveness-forward-return-source-count=2",
            "contract-region-liveness-forward-return-source0=first",
            "contract-region-liveness-forward-return-source1=second",
            "contract-region-liveness-empty-union-state=known",
            "contract-region-liveness-empty-union-count=0",
            "contract-region-liveness-empty-union-known-empty=true",
            "contract-region-liveness-opaque-overlaps-any-owner=true",
            "contract-region-liveness-snapshot-format=freak-borrowck-snapshot-v1",
            "borrowck-snapshot-import ok=1",
            "borrowck-snapshot-restore ok=1",
            "contract-region-liveness-restored-choose-return-source-count=2",
            "contract-region-liveness-restored-choose-return-source0=first",
            "contract-region-liveness-restored-choose-return-source1=second",
            "contract-region-liveness-restored-forward-return-source-count=2",
            "contract-region-liveness-restored-forward-return-source0=first",
            "contract-region-liveness-restored-forward-return-source1=second",
            "contract-region-liveness-restored-choose-order-stable=true",
            "contract-region-liveness-restored-forward-order-stable=true",
        ),
        "contract_region_elided_liveness_smoke.fk": (
            "contract-region-elided-liveness-ty-diagnostics=0",
            "contract-region-elided-liveness-mir-diagnostics=0",
            "contract-region-elided-liveness-borrow-diagnostics=2",
            "contract-region-elided-liveness-move-conflict-diagnostics=2",
            "contract-region-elided-liveness-signature-source-count=2",
            "contract-region-elided-liveness-signature-source0-index=0",
            "contract-region-elided-liveness-signature-source0-name=first",
            "contract-region-elided-liveness-signature-source1-index=1",
            "contract-region-elided-liveness-signature-source1-name=second",
            "contract-region-elided-liveness-call-source-count=2",
            "contract-region-elided-liveness-call-source0=lend first",
            "contract-region-elided-liveness-call-source1=lend second",
            "contract-region-elided-liveness-choose-status=clean",
            "contract-region-elided-liveness-first-before-status=blocked",
            "contract-region-elided-liveness-second-before-status=blocked",
            "contract-region-elided-liveness-unrelated-before-status=clean",
            "contract-region-elided-liveness-first-after-status=clean",
            "contract-region-elided-liveness-second-after-status=clean",
        ),
        "contract_region_elided_query_invalidation_smoke.fk": (
            "contract-region-elided-query-before-diagnostics=0",
            "contract-region-elided-query-before-message=none",
            "contract-region-elided-query-before-choose-status=clean",
            "contract-region-elided-query-before-observe-status=clean",
            "contract-region-elided-query-before-source-count=2",
            "contract-region-elided-query-before-source0=first",
            "contract-region-elided-query-before-source1=second",
            "contract-region-elided-query-before-call-source-count=2",
            "contract-region-elided-query-before-call-source0=lend first",
            "contract-region-elided-query-before-call-source1=lend second",
            "contract-region-elided-query-before-semantic=lend Ship",
            "contract-region-elided-query-before-hover=lend Ship",
            "contract-region-elided-query-before-definition=1",
            "contract-region-elided-query-editor-offset-stable=true",
            "contract-region-elided-query-ty-invalidations-added=1",
            "contract-region-elided-query-mir-invalidations-added=1",
            "contract-region-elided-query-borrowck-invalidations-added=1",
            "contract-region-elided-query-diagnostics-invalidations-added=1",
            "contract-region-elided-query-semantic-invalidations-added=1",
            "contract-region-elided-query-hover-invalidations-added=1",
            "contract-region-elided-query-definition-invalidations-added=1",
            "contract-region-elided-query-ty-recomputations-added=1",
            "contract-region-elided-query-mir-recomputations-added=1",
            "contract-region-elided-query-borrowck-recomputations-added=1",
            "contract-region-elided-query-diagnostics-recomputations-added=1",
            "contract-region-elided-query-semantic-recomputations-added=1",
            "contract-region-elided-query-hover-recomputations-added=1",
            "contract-region-elided-query-definition-recomputations-added=1",
            "contract-region-elided-query-after-diagnostics=0",
            "contract-region-elided-query-after-message=none",
            "contract-region-elided-query-after-choose-status=clean",
            "contract-region-elided-query-after-observe-status=clean",
            "contract-region-elided-query-after-source-count=1",
            "contract-region-elided-query-after-source0=first",
            "contract-region-elided-query-after-call-source-count=1",
            "contract-region-elided-query-after-call-source0=lend first",
            "contract-region-elided-query-after-semantic=Ship",
            "contract-region-elided-query-after-hover=Ship",
            "contract-region-elided-query-after-definition=1",
            "diagnostics|0",
        ),
        "contract_region_resource_smoke.fk": (
            "contract-region-resource-ty-diagnostics=0",
            "contract-region-resource-mir-diagnostics=0",
            "contract-region-resource-borrow-diagnostics=1",
            "contract-region-resource-diamond-status=clean",
            "contract-region-resource-opaque-status=blocked",
            "contract-region-resource-diamond-source-count=2",
            "contract-region-resource-diamond-source0=first",
            "contract-region-resource-diamond-source1=second",
            "contract-region-resource-recomputations=8",
            "contract-region-resource-generation-delta=8",
            "contract-region-resource-generation-sequence=true",
            "contract-region-resource-semantics-stable=true",
            "contract-region-resource-source-order-stable=true",
            "contract-region-resource-memo-hits=true",
            "contract-region-resource-one-state-per-memo=true",
            "contract-region-resource-active-counts-stable=true",
            "contract-region-resource-active-within-capacity=true",
            "contract-region-resource-capacities-reused=true",
            "contract-region-resource-no-historical-growth=true",
            "contract-region-resource-opaque-conservative=true",
            "contract-region-resource-bounds-opaque=true",
        ),
    }
    exact_harness_expect_fixtures = (
        "contract_region_boundary_negative_smoke.fk",
        "contract_region_forwarding_boundary_negative_smoke.fk",
        "contract_region_editor_smoke.fk",
        "contract_region_elided_liveness_smoke.fk",
        "contract_region_elided_query_invalidation_smoke.fk",
    )
    if v4_check_harness_return.exists():
        harness_expects, harness_errors = _literal_executable_smokes(v4_check_harness_return)
        contract_region_missing.extend(harness_errors)
        harness_fixtures = (
            "lend_return_smoke.fk",
            "lend_return_editor_smoke.fk",
            "lend_return_query_invalidation_smoke.fk",
            "named_lifetime_return_smoke.fk",
            "named_lifetime_diagnostics_smoke.fk",
            "named_lifetime_editor_smoke.fk",
            "named_lifetime_query_invalidation_smoke.fk",
        ) + tuple(fixture_path.name for fixture_path, _ in contract_region_smoke_needles)
        for fixture in harness_fixtures:
            if fixture not in harness_expects:
                contract_region_missing.append(f"EXECUTABLE_SMOKES: {fixture} entry missing")
        for fixture, required_expects in required_harness_expects.items():
            actual_expects = harness_expects.get(fixture)
            if actual_expects is None:
                continue
            if fixture in exact_harness_expect_fixtures:
                if tuple(actual_expects) != required_expects:
                    contract_region_missing.append(
                        f"EXECUTABLE_SMOKES: {fixture} expectation list does not exactly match the auditor oracle"
                    )
                continue
            for expected in required_expects:
                if expected not in actual_expects:
                    contract_region_missing.append(
                        f"EXECUTABLE_SMOKES: {fixture} missing expected value {expected!r}"
                    )

        stale_exact_one_expectations = (
            "Meiya cannot choose one source for this returned loan",
            "name one source before returning the loan",
        )
        for fixture, expects in harness_expects.items():
            for expected in expects:
                if any(stale in expected for stale in stale_exact_one_expectations):
                    contract_region_missing.append(
                        f"EXECUTABLE_SMOKES: {fixture} retains stale exact-one expectation {expected!r}"
                    )
                if (
                    fixture == "lend_return_smoke.fk"
                    and expected.startswith("lend-return-ambiguous-diagnostics=")
                    and expected != "lend-return-ambiguous-diagnostics=0"
                ):
                    contract_region_missing.append(
                        f"EXECUTABLE_SMOKES: {fixture} retains stale exact-one diagnostic count {expected!r}"
                    )
    else:
        contract_region_missing.append("check_v4.py harness missing")
    add(
        "V4 contract region source sets",
        not contract_region_missing,
        "TY/MIR source sets + Meiya provenance + editor/tooling smokes wired" if not contract_region_missing else f"{len(contract_region_missing)} gap(s)",
    )
    if contract_region_missing:
        failures.append("V4 contract-region source sets regressed: " + "; ".join(contract_region_missing))

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

    # Check 14: V4 training arc growth checks
    growth_missing: List[str] = []
    v4_growth_smoke = repo / "src" / "compiler" / "v4" / "tests" / "mir_loop_desugar_smoke.fk"
    v4_mir_lib_growth = repo / "src" / "compiler" / "v4" / "crates" / "freak_mir" / "src" / "lib.fk"
    v4_check_harness_growth = repo / "src" / "compiler" / "v4" / "check_v4.py"
    if v4_mir_lib_growth.exists():
        mir_src = v4_mir_lib_growth.read_text(encoding="utf-8")
        for needle in (
            "v4_mir_condition_subject_place",
            "v4_mir_condition_place_prefix_end",
            "v4_mir_body_mutates_place",
            "v4_mir_growth_place_base",
            "v4_mir_growth_place_prefix_matches",
            'or val == "->"',
            "v4_mir_growth_place_prefix_matches(lhs_text, wanted)",
        ):
            if needle not in mir_src:
                growth_missing.append(f"freak_mir: {needle}")
    else:
        growth_missing.append("freak_mir/src/lib.fk missing")
    if v4_growth_smoke.exists():
        smoke_src = v4_growth_smoke.read_text(encoding="utf-8")
        for needle in (
            "v4_mir_loop_make_field_growth_source",
            "v4_mir_loop_make_bad_field_growth_source",
            "v4_mir_loop_make_arm_growth_source",
            "v4_mir_loop_make_base_growth_source",
            "v4_mir_loop_make_expr_growth_source",
            "v4_mir_loop_make_paren_growth_source",
            "v4_mir_loop_make_prefix_growth_source",
            "bad-field-growth-help=",
        ):
            if needle not in smoke_src:
                growth_missing.append(f"mir_loop_desugar_smoke: {needle}")
    else:
        growth_missing.append("smoke fixture: mir_loop_desugar_smoke.fk")
    if v4_check_harness_growth.exists():
        harness_src = v4_check_harness_growth.read_text(encoding="utf-8")
        for needle in (
            "field-growth-diagnostics=0",
            "bad-field-growth-help=Yuuko found no progress for ship.power",
            "arm-growth-diagnostics=0",
            "base-growth-diagnostics=0",
            "expr-growth-diagnostics=0",
            "paren-growth-diagnostics=0",
            "prefix-growth-diagnostics=0",
        ):
            if needle not in harness_src:
                growth_missing.append(f"check_v4.py: {needle}")
    else:
        growth_missing.append("check_v4.py harness missing")
    add(
        "V4 growth checks",
        not growth_missing,
        "MIR projected/base/arm/expression growth smokes wired" if not growth_missing else f"{len(growth_missing)} gap(s)",
    )
    if growth_missing:
        failures.append("V4 training arc growth checks regressed: " + "; ".join(growth_missing))

    # Check 15: V4 alias nominality for doctrine impl targets
    # Aliases are compile-time substitutions. The V4 TY layer must reject
    # `impl Doctrine for Alias` instead of treating the alias as a fresh
    # nominal type. Keep the markers stable so the implementation lane can
    # satisfy this guard without broad alias-completeness overclaims.
    alias_nominality_missing: List[str] = []
    v4_ty_lib_alias_nominality = repo / "src" / "compiler" / "v4" / "crates" / "freak_ty" / "src" / "lib.fk"
    v4_alias_nominality_smoke = repo / "src" / "compiler" / "v4" / "tests" / "alias_nominality_smoke.fk"
    v4_check_harness_alias_nominality = repo / "src" / "compiler" / "v4" / "check_v4.py"
    if v4_ty_lib_alias_nominality.exists():
        ty_src = v4_ty_lib_alias_nominality.read_text(encoding="utf-8")
        for needle in (
            "v4_ty_alias_lookup_type_from_surface_type",
            "v4_resolve_symbol_target_name",
            "v4_ty_impl_doctrine_name_from_hir",
            "v4_ty_validate_alias_nominality",
            "alias nominality",
            "one-field shape",
        ):
            if needle not in ty_src:
                alias_nominality_missing.append(f"freak_ty: {needle}")
    else:
        alias_nominality_missing.append("freak_ty/src/lib.fk missing")
    if v4_alias_nominality_smoke.exists():
        smoke_src = v4_alias_nominality_smoke.read_text(encoding="utf-8")
        for needle in (
            "alias-nominality-diagnostics=1",
            "alias-nominality-bad-method-ref-empty=true",
            "alias-nominality-imported-ty-diagnostics=1",
            "alias-nominality-glob-ty-diagnostics=1",
            "alias-nominality-inherent-name-method-ref-present=true",
            "alias nominality",
        ):
            if needle not in smoke_src:
                alias_nominality_missing.append(f"alias_nominality_smoke: {needle}")
    else:
        alias_nominality_missing.append("smoke fixture: alias_nominality_smoke.fk")
    if v4_check_harness_alias_nominality.exists():
        harness_src = v4_check_harness_alias_nominality.read_text(encoding="utf-8")
        for needle in (
            "alias_nominality_smoke.fk",
            "alias-nominality-diagnostics=1",
            "alias-nominality-bad-method-ref-empty=true",
            "alias-nominality-imported-ty-diagnostics=1",
            "alias-nominality-glob-ty-diagnostics=1",
            "alias-nominality-inherent-name-method-ref-present=true",
            "alias nominality",
        ):
            if needle not in harness_src:
                alias_nominality_missing.append(f"check_v4.py: {needle}")
    else:
        alias_nominality_missing.append("check_v4.py harness missing")
    add(
        "V4 alias nominality",
        not alias_nominality_missing,
        "TY alias impl diagnostic + smoke wired" if not alias_nominality_missing else f"{len(alias_nominality_missing)} gap(s)",
    )
    if alias_nominality_missing:
        failures.append("V4 alias nominality doctrine-impl guard regressed: " + "; ".join(alias_nominality_missing))

    # Check 16: V4 dyn Doctrine semantic/editor surface
    # This is intentionally a semantic/query guard, not a vtable-codegen claim.
    dyn_doctrine_missing: List[str] = []
    v4_lex_dyn = repo / "src" / "compiler" / "v4" / "crates" / "freak_lex" / "src" / "lib.fk"
    v4_ty_dyn = repo / "src" / "compiler" / "v4" / "crates" / "freak_ty" / "src" / "lib.fk"
    v4_mir_dyn = repo / "src" / "compiler" / "v4" / "crates" / "freak_mir" / "src" / "lib.fk"
    v4_editor_dyn = repo / "src" / "compiler" / "v4" / "crates" / "freak_editor" / "src" / "lib.fk"
    v4_dyn_ty_smoke = repo / "src" / "compiler" / "v4" / "tests" / "dyn_doctrine_ty_smoke.fk"
    v4_dyn_mir_smoke = repo / "src" / "compiler" / "v4" / "tests" / "mir_dyn_doctrine_smoke.fk"
    v4_dyn_mir_generic_smoke = repo / "src" / "compiler" / "v4" / "tests" / "mir_dyn_doctrine_generic_smoke.fk"
    v4_dyn_mir_shared_smoke = repo / "src" / "compiler" / "v4" / "tests" / "mir_dyn_doctrine_shared_smoke.fk"
    v4_dyn_mir_diagnostics_smoke = repo / "src" / "compiler" / "v4" / "tests" / "mir_dyn_doctrine_diagnostics_smoke.fk"
    v4_dyn_editor_smoke = repo / "src" / "compiler" / "v4" / "tests" / "dyn_doctrine_editor_smoke.fk"
    v4_check_harness_dyn = repo / "src" / "compiler" / "v4" / "check_v4.py"
    if v4_lex_dyn.exists():
        lex_src = v4_lex_dyn.read_text(encoding="utf-8")
        if 'lower == "dyn"' not in lex_src:
            dyn_doctrine_missing.append('freak_lex: lower == "dyn"')
    else:
        dyn_doctrine_missing.append("freak_lex/src/lib.fk missing")
    if v4_ty_dyn.exists():
        ty_src = v4_ty_dyn.read_text(encoding="utf-8")
        for needle in (
            "task v4_ty_dyn_type",
            "task v4_ty_dyn_object_safety_issue",
            "task v4_ty_type_can_coerce_to_dyn_in_signature",
            "task v4_ty_types_compatible_with_context",
            "dyn doctrine is unknown",
            "dyn doctrine is not object safe",
        ):
            if needle not in ty_src:
                dyn_doctrine_missing.append(f"freak_ty: {needle}")
    else:
        dyn_doctrine_missing.append("freak_ty/src/lib.fk missing")
    if v4_mir_dyn.exists():
        mir_src = v4_mir_dyn.read_text(encoding="utf-8")
        for needle in (
            "task v4_mir_find_dyn_method_ref",
            "v4_ty_is_dyn_type(type_text)",
            "task v4_mir_type_has_dyn_keyword_at",
            "v4_mir_find_dyn_method_ref(mir_id, receiver_ty, method_name, true)",
        ):
            if needle not in mir_src:
                dyn_doctrine_missing.append(f"freak_mir: {needle}")
    else:
        dyn_doctrine_missing.append("freak_mir/src/lib.fk missing")
    if v4_editor_dyn.exists():
        editor_src = v4_editor_dyn.read_text(encoding="utf-8")
        for needle in (
            "v4_editor_document_symbols_add_doctrine_methods",
            "v4_mir_find_dyn_method_ref(mir_id, lookup_owner_ty, method_name",
            'v4_completion_add(completion_id, "dyn"',
            "v4_completion_add_bound_methods_for_owner",
        ):
            if needle not in editor_src:
                dyn_doctrine_missing.append(f"freak_editor: {needle}")
    else:
        dyn_doctrine_missing.append("freak_editor/src/lib.fk missing")
    if v4_dyn_ty_smoke.exists():
        smoke_src = v4_dyn_ty_smoke.read_text(encoding="utf-8")
        for needle in (
            "dyn-ty-param=",
            "dyn-ty-widget-object-safe=",
            "dyn-ty-button-coerces=",
            "dyn-ty-diag0-message=",
        ):
            if needle not in smoke_src:
                dyn_doctrine_missing.append(f"dyn_doctrine_ty_smoke: {needle}")
    else:
        dyn_doctrine_missing.append("smoke fixture: dyn_doctrine_ty_smoke.fk")
    if v4_dyn_mir_smoke.exists():
        smoke_src = v4_dyn_mir_smoke.read_text(encoding="utf-8")
        for needle in (
            "dyn-mir-return-op=",
            "dyn-mir-widget-local-type=",
        ):
            if needle not in smoke_src:
                dyn_doctrine_missing.append(f"mir_dyn_doctrine_smoke: {needle}")
    else:
        dyn_doctrine_missing.append("smoke fixture: mir_dyn_doctrine_smoke.fk")
    if v4_dyn_mir_generic_smoke.exists():
        smoke_src = v4_dyn_mir_generic_smoke.read_text(encoding="utf-8")
        if "dyn-mir-forward-accept-arg-ty=" not in smoke_src:
            dyn_doctrine_missing.append("mir_dyn_doctrine_generic_smoke: dyn-mir-forward-accept-arg-ty=")
    else:
        dyn_doctrine_missing.append("smoke fixture: mir_dyn_doctrine_generic_smoke.fk")
    if v4_dyn_mir_shared_smoke.exists():
        smoke_src = v4_dyn_mir_shared_smoke.read_text(encoding="utf-8")
        if "dyn-mir-forward-weak-arg-ty=" not in smoke_src:
            dyn_doctrine_missing.append("mir_dyn_doctrine_shared_smoke: dyn-mir-forward-weak-arg-ty=")
    else:
        dyn_doctrine_missing.append("smoke fixture: mir_dyn_doctrine_shared_smoke.fk")
    if v4_dyn_mir_diagnostics_smoke.exists():
        smoke_src = v4_dyn_mir_diagnostics_smoke.read_text(encoding="utf-8")
        if "dyn-mir-bad-message=" not in smoke_src:
            dyn_doctrine_missing.append("mir_dyn_doctrine_diagnostics_smoke: dyn-mir-bad-message=")
    else:
        dyn_doctrine_missing.append("smoke fixture: mir_dyn_doctrine_diagnostics_smoke.fk")
    if v4_dyn_editor_smoke.exists():
        smoke_src = v4_dyn_editor_smoke.read_text(encoding="utf-8")
        for needle in (
            "dyn-editor-call-kind=",
            "dyn-editor-definition-found=",
            "dyn-editor-completion-draw-found=",
            "dyn-editor-completion-dyn-kind=",
        ):
            if needle not in smoke_src:
                dyn_doctrine_missing.append(f"dyn_doctrine_editor_smoke: {needle}")
    else:
        dyn_doctrine_missing.append("smoke fixture: dyn_doctrine_editor_smoke.fk")
    if v4_check_harness_dyn.exists():
        harness_src = v4_check_harness_dyn.read_text(encoding="utf-8")
        for needle in (
            "dyn_doctrine_ty_smoke.fk",
            "mir_dyn_doctrine_smoke.fk",
            "mir_dyn_doctrine_generic_smoke.fk",
            "mir_dyn_doctrine_shared_smoke.fk",
            "mir_dyn_doctrine_diagnostics_smoke.fk",
            "dyn_doctrine_editor_smoke.fk",
            "dyn-editor-call-kind=Method",
        ):
            if needle not in harness_src:
                dyn_doctrine_missing.append(f"check_v4.py: {needle}")
    else:
        dyn_doctrine_missing.append("check_v4.py harness missing")
    add(
        "V4 dyn Doctrine",
        not dyn_doctrine_missing,
        "TY/MIR/editor dyn Doctrine smokes wired" if not dyn_doctrine_missing else f"{len(dyn_doctrine_missing)} gap(s)",
    )
    if dyn_doctrine_missing:
        failures.append("V4 dyn Doctrine semantic/editor surface regressed: " + "; ".join(dyn_doctrine_missing))

    # Check 17: V4 direct recursive shape/variant rejection
    # Owned recursion must not create infinite-size values. This guard checks
    # the semantic-core validator and smoke without claiming backend layout is complete.
    type_recursion_missing: List[str] = []
    v4_ty_type_recursion = repo / "src" / "compiler" / "v4" / "crates" / "freak_ty" / "src" / "lib.fk"
    v4_type_recursion_smoke = repo / "src" / "compiler" / "v4" / "tests" / "type_recursion_smoke.fk"
    v4_check_harness_type_recursion = repo / "src" / "compiler" / "v4" / "check_v4.py"
    if v4_ty_type_recursion.exists():
        ty_src = v4_ty_type_recursion.read_text(encoding="utf-8")
        for needle in (
            "v4_ty_validate_direct_type_recursion",
            "v4_ty_type_recursion_is_indirect_carrier",
            "v4_ty_type_recursion_expand_import_type",
            "v4_ty_type_recursion_seen_has_nominal",
            "v4_ty_type_recursion_path_in_nominal",
            "v4_ty_alias_lookup_type_from_surface_type",
            "generic \" + generic_name + \" shadows its owner",
            "Yuuko infinite shape",
            "Yuuko infinite variant",
            "Shared<T>, Weak<T>, List<T>, or a raw pointer",
        ):
            if needle not in ty_src:
                type_recursion_missing.append(f"freak_ty: {needle}")
    else:
        type_recursion_missing.append("freak_ty/src/lib.fk missing")
    if v4_type_recursion_smoke.exists():
        smoke_src = v4_type_recursion_smoke.read_text(encoding="utf-8")
        for needle in (
            "shape Direct",
            "shape Left",
            "shape Shared<T>",
            "shape InlineBox<T>",
            "alias AliasNode = AliasHolder",
            "alias DeepA10 = DeepNode",
            "alias BadAlias = Box<BadAlias>",
            "use util::ImportedNode as ImportedNode",
            "use util::Shared as Shared",
            "alias Ignore<T> = int",
            "shape Wrap<T>",
            "shape Node<Node>",
            "shape util::Node",
            "variant BadRoute",
            "variant GenericRoute",
            "type-recursion-safe-shared-path=",
            "type-recursion-shadow-ty-diagnostics=",
            "type-recursion-import-ty-diagnostics=",
            "type-recursion-alias-erased-ty-diagnostics=",
            "type-recursion-generic-growth-ty-diagnostics=",
            "type-recursion-generic-shadow-ty-diagnostics=",
            "type-recursion-import-local-ty-diagnostics=",
            "type-recursion-mir-diagnostics=",
        ):
            if needle not in smoke_src:
                type_recursion_missing.append(f"type_recursion_smoke: {needle}")
    else:
        type_recursion_missing.append("smoke fixture: type_recursion_smoke.fk")
    if v4_check_harness_type_recursion.exists():
        harness_src = v4_check_harness_type_recursion.read_text(encoding="utf-8")
        for needle in (
            "type_recursion_smoke.fk",
            "type-recursion-ty-diagnostics=10",
            "Yuuko alias loop: alias BadAlias expands forever via BadAlias -> BadAlias",
            "Yuuko infinite shape: GenericNode contains itself by value via GenericNode -> InlineBox<GenericNode> -> GenericNode",
            "Yuuko infinite shape: Node contains itself by value via Node -> Box<GenericAlias> -> GenericAlias -> Box<Node> -> Node",
            "Yuuko infinite shape: DeepNode contains itself by value via DeepNode -> DeepA1 -> DeepA2 -> DeepA3",
            "Yuuko infinite shape: ShadowNode contains itself by value via ShadowNode -> Shared<ShadowNode> -> ShadowNode",
            "Yuuko infinite shape: util::ImportedNode contains itself by value via util::ImportedNode -> util::ImportedNode",
            "Yuuko infinite shape: ImportShadowNode contains itself by value via ImportShadowNode -> util::Shared<ImportShadowNode> -> ImportShadowNode",
            "Yuuko infinite variant: GenericRoute contains itself by value via GenericRoute -> InlineBox<GenericRoute> -> GenericRoute",
            "type-recursion-import-ty-diagnostics=2",
            "type-recursion-alias-erased-ty-diagnostics=0",
            "type-recursion-generic-growth-diag0=Yuuko infinite shape: Wrap contains itself by value via Wrap -> Wrap",
            "type-recursion-generic-shadow-diag0=Meiya lifetime debt: generic Node shadows its owner Node; Yuuko needs one identity per timeline",
            "type-recursion-import-local-diag0=Yuuko infinite shape: Node contains itself by value via Node -> Node",
            "type-recursion-mir-diagnostics=10",
        ):
            if needle not in harness_src:
                type_recursion_missing.append(f"check_v4.py: {needle}")
    else:
        type_recursion_missing.append("check_v4.py harness missing")
    add(
        "V4 type recursion",
        not type_recursion_missing,
        "TY direct shape/variant recursion guard + smoke wired" if not type_recursion_missing else f"{len(type_recursion_missing)} gap(s)",
    )
    if type_recursion_missing:
        failures.append("V4 direct type-recursion guard regressed: " + "; ".join(type_recursion_missing))
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
