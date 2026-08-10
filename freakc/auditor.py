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
from collections import Counter
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


def _bounded_text_section(source: str, start_marker: str, end_marker: str) -> Optional[str]:
    start = source.find(start_marker)
    if start < 0:
        return None
    end = source.find(end_marker, start + len(start_marker))
    if end < 0:
        return None
    return source[start:end]


@dataclass(frozen=True)
class _LiteralExecutableSmoke:
    expect: Tuple[str, ...]
    expect_exact: Tuple[str, ...]
    expect_mode: Optional[str]
    expect_unique: bool


_EXECUTABLE_SMOKE_MUTATORS = frozenset(
    {
        "__delitem__",
        "__iadd__",
        "__imul__",
        "__setitem__",
        "append",
        "clear",
        "extend",
        "insert",
        "pop",
        "remove",
        "reverse",
        "sort",
        "update",
    }
)
_EXECUTABLE_SMOKE_OPERATOR_MUTATORS = frozenset(
    {"delitem", "iadd", "imul", "setitem"}
)
_EXECUTABLE_SMOKE_READ_CALLS = frozenset(
    {
        "all",
        "any",
        "bool",
        "enumerate",
        "iter",
        "len",
        "list",
        "print",
        "repr",
        "reversed",
        "sorted",
        "str",
        "tuple",
    }
)
_EXECUTABLE_SMOKE_READ_METHODS = frozenset(
    {"__contains__", "copy", "count", "get", "index", "items", "keys", "values"}
)
_EXECUTABLE_SMOKE_SCALAR_FIELDS = frozenset(
    {"fixture", "name", "expect_mode", "expect_unique", "timeout"}
)
_MANIFEST_SEQUENCE_ALIAS = "sequence"
_MANIFEST_ENTRY_ALIAS = "entry"
_MANIFEST_MUTABLE_ALIAS = "mutable"
_UNIT_SNAPSHOT_INTEGRITY_CASES = (
    "current-snapshot-validated",
    "current-manifest-valid",
    "current-health-valid",
    "missing-section",
    "duplicate-section",
    "corrupt-inner-payload",
    "unknown-section",
    "current-diagnostics-valid",
    "changed-diagnostics-valid",
    "negative-source-id-atomic",
    "sparse-source-id-atomic",
    "duplicate-source-id-atomic",
    "duplicate-source-path-atomic",
    "forged-source-fingerprint-atomic",
    "invalid-restore-rejected",
    "preflight-preserves-source-text",
    "preflight-preserves-source-revision",
    "extras-visible-before-restore",
    "extra-cache-hit-before-restore",
    "valid-restore",
    "valid-restore-source-text",
    "valid-restore-source-revision",
    "extra-source-removed",
    "extra-semantic-removed",
    "extra-hover-removed",
    "extra-definition-removed",
    "extra-query-removed",
    "extra-cache-miss-after-restore",
    "wrong-format-restore-rejected",
)
_UNIT_SNAPSHOT_INTEGRITY_ORACLES = tuple(
    f"unit-snapshot-integrity|case={case_name}|ok=1"
    for case_name in _UNIT_SNAPSHOT_INTEGRITY_CASES
)
_UNIT_SNAPSHOT_INTEGRITY_STRUCTURAL_NEEDLES = (
    "task v4_unit_snapshot_integrity_assert(case_name: word, passed: bool) -> word {",
    'pilot out = "unit-snapshot-integrity|case=" + case_name',
) + tuple(
    f'v4_unit_snapshot_integrity_assert("{case_name}",'
    for case_name in _UNIT_SNAPSHOT_INTEGRITY_CASES
)
_UNIT_SNAPSHOT_MULTISOURCE_RESOURCE_ORACLES = (
    "snapshot-multisource-count=192",
    "snapshot-multisource-valid=true",
    "snapshot-multisource-manifest=true",
    "snapshot-multisource-diff=true",
    "snapshot-multisource-health=true",
    "snapshot-multisource-health-diff=true",
    "snapshot-multisource-duplicate-ids=true",
    "snapshot-multisource-duplicate-paths=true",
)
_MIR_SNAPSHOT_RESOURCE_ORACLES = (
    "mir-snapshot-resource-iterations=64",
    "mir-snapshot-resource-valid=true",
    "mir-snapshot-resource-array-probe=true",
)
_QUERY_INVALIDATION_RESOURCE_ORACLES = (
    "query-invalidation-resource-changes=96",
    "query-invalidation-resource-direct=600",
    "query-invalidation-resource-response=true",
    "query-invalidation-resource-dependents=true",
    "query-invalidation-resource-change-probe=true",
    "query-invalidation-resource-array-probe=true",
)
_EXPLICIT_STRICT_SMOKE_ORACLES: Dict[str, Tuple[str, ...]] = {
    "lend_return_query_invalidation_smoke.fk": (),
    "named_lifetime_editor_smoke.fk": (),
    "shared_weak_smoke.fk": (
        "shared-weak-ty-shared=1",
        "shared-weak-ty-weak=1",
        "shared-weak-ty-shared-mut=1",
        "shared-weak-root-ty=Shared<Ship>",
        "shared-weak-copy-ty=Shared<Ship>",
        "shared-weak-weak-ty=Weak<Ship>",
        "shared-weak-revived-ty=maybe<Shared<Ship>>",
        "shared-weak-guard-ty=result<SharedMut<Ship>,BorrowError>",
        "shared-weak-clone-args=1",
        "shared-weak-clone-arg-text=root",
        "shared-weak-downgrade-args=1",
        "shared-weak-downgrade-arg-text=root",
        "shared-weak-upgrade-args=1",
        "shared-weak-upgrade-arg-text=weak",
        "shared-weak-view-ty=lend Ship",
        "shared-weak-unique-ty=maybe<lend mut Ship>",
        "shared-weak-new-status=clean",
        "shared-weak-handles-status=clean",
        "shared-weak-borrow-status=clean",
        "shared-weak-mut-status=clean",
        "shared-weak-unique-status=clean",
        "shared-weak-direct-status=clean",
        "shared-weak-result-status=clean",
        "shared-weak-error-status=clean",
        "shared-weak-leak-status=blocked",
        "shared-weak-ty-diagnostics=0",
        "shared-weak-mir-diagnostics=1",
        "shared-weak-borrow-diagnostics=3",
        "shared-weak-direct-diagnostics=1",
        "shared-weak-guard-escape-diagnostics=1",
        "shared-weak-view-escape-status=blocked",
        "shared-weak-view-escape-diagnostics=1",
        "shared-alias-ty-diagnostics=0",
        "shared-alias-mir-diagnostics=0",
        "shared-alias-borrow-diagnostics=3",
        "shared-alias-borrow-diagnostics-exact-three=true",
        "shared-alias-get-mut-uncontended-status=clean",
        "shared-alias-get-mut-conflict-status=blocked",
        "shared-alias-get-mut-clone-first-status=clean",
        "shared-alias-stored-borrow-escape-status=blocked",
        "shared-alias-symbolic-index-status=blocked",
        "shared-alias-concrete-index-status=clean",
        "shared-alias-get-mut-conflict-diagnostics=1",
        "shared-alias-stored-borrow-escape-diagnostics=1",
        "shared-alias-symbolic-index-diagnostics=1",
        "shared-alias-symbolic-equal-possible-overlap=true",
        "shared-alias-symbolic-vs-literal-overlap=true",
        "shared-alias-concrete-distinct-overlap=false",
    ),
    "unit_snapshot_smoke.fk": _UNIT_SNAPSHOT_INTEGRITY_ORACLES,
    "unit_snapshot_multisource_resource_smoke.fk": _UNIT_SNAPSHOT_MULTISOURCE_RESOURCE_ORACLES,
    "mir_snapshot_resource_smoke.fk": _MIR_SNAPSHOT_RESOURCE_ORACLES,
    "query_invalidation_resource_smoke.fk": _QUERY_INVALIDATION_RESOURCE_ORACLES,
}


def _ast_contains_name(node: ast.AST, name: str) -> bool:
    return any(
        isinstance(child, ast.Name) and child.id == name
        for child in ast.walk(node)
    )


class _TopLevelManifestMutationVisitor(ast.NodeVisitor):
    """Find mutations and alias escapes after the literal manifest assignment."""

    def __init__(self) -> None:
        self.errors: List[str] = []
        self._alias_scopes: List[Dict[str, str]] = [{}]
        self._collector_scopes: List[set[str]] = [set()]

    def _record(self, node: ast.AST, action: str) -> None:
        line = getattr(node, "lineno", "unknown")
        self.errors.append(
            "check_v4.py: EXECUTABLE_SMOKES "
            f"{action} after its literal assignment at line {line}"
        )

    def _push_scope(self) -> None:
        self._alias_scopes.append({})
        self._collector_scopes.append(set())

    def _pop_scope(self) -> None:
        self._alias_scopes.pop()
        self._collector_scopes.pop()

    def _name_alias_kind(self, name: str) -> Optional[str]:
        if name == "EXECUTABLE_SMOKES":
            return _MANIFEST_SEQUENCE_ALIAS
        for scope in reversed(self._alias_scopes):
            alias_kind = scope.get(name)
            if alias_kind is not None:
                return alias_kind
        return None

    @staticmethod
    def _subscript_key(node: ast.Subscript) -> Optional[str]:
        if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
            return node.slice.value
        return None

    def _comprehension_carries_alias(
        self, generators: List[ast.comprehension], value: ast.AST
    ) -> bool:
        alias_targets: set[str] = set()
        for generator in generators:
            if self._iteration_alias_kind(generator.iter) is not None:
                alias_targets.update(self._target_names(generator.target))
        return self._expression_carries_target_alias(value, alias_targets)

    def _expression_carries_target_alias(
        self, value: ast.AST, alias_targets: set[str]
    ) -> bool:
        if isinstance(value, ast.Name):
            return value.id in alias_targets
        if isinstance(value, ast.Starred):
            return self._expression_carries_target_alias(value.value, alias_targets)
        if isinstance(value, (ast.List, ast.Tuple, ast.Set)):
            return any(
                self._expression_carries_target_alias(item, alias_targets)
                for item in value.elts
            )
        if isinstance(value, ast.Dict):
            return any(
                item is not None
                and self._expression_carries_target_alias(item, alias_targets)
                for item in [*value.keys, *value.values]
            )
        if isinstance(value, ast.Subscript) and isinstance(value.value, ast.Name):
            if value.value.id not in alias_targets:
                return False
            key = self._subscript_key(value)
            return key not in _EXECUTABLE_SMOKE_SCALAR_FIELDS
        if isinstance(value, ast.Attribute):
            return self._expression_carries_target_alias(value.value, alias_targets)
        if isinstance(value, ast.Call):
            if isinstance(value.func, ast.Name) and value.func.id == "dict":
                return any(
                    self._expression_carries_target_alias(argument, alias_targets)
                    for argument in value.args
                )
            if isinstance(value.func, ast.Attribute) and value.func.attr == "copy":
                return self._expression_carries_target_alias(
                    value.func.value, alias_targets
                )
        return False

    def _alias_kind(self, value: ast.AST) -> Optional[str]:
        if isinstance(value, ast.Name):
            return self._name_alias_kind(value.id)
        if isinstance(value, ast.Starred):
            return self._alias_kind(value.value)
        if isinstance(value, ast.NamedExpr):
            return self._alias_kind(value.value)
        if isinstance(value, ast.IfExp):
            return self._alias_kind(value.body) or self._alias_kind(value.orelse)
        if isinstance(value, (ast.List, ast.Tuple, ast.Set)):
            if any(self._alias_kind(item) is not None for item in value.elts):
                return _MANIFEST_SEQUENCE_ALIAS
            return None
        if isinstance(value, ast.Dict):
            if any(
                item is not None and self._alias_kind(item) is not None
                for item in [*value.keys, *value.values]
            ):
                return _MANIFEST_ENTRY_ALIAS
            return None
        if isinstance(value, ast.Subscript):
            container_kind = self._alias_kind(value.value)
            if container_kind == _MANIFEST_SEQUENCE_ALIAS:
                if isinstance(value.slice, ast.Slice):
                    return _MANIFEST_SEQUENCE_ALIAS
                return _MANIFEST_ENTRY_ALIAS
            if container_kind == _MANIFEST_ENTRY_ALIAS:
                key = self._subscript_key(value)
                if key in _EXECUTABLE_SMOKE_SCALAR_FIELDS:
                    return None
                return _MANIFEST_MUTABLE_ALIAS
            return None
        if isinstance(value, ast.Attribute):
            if self._alias_kind(value.value) is not None:
                return _MANIFEST_MUTABLE_ALIAS
            return None
        if isinstance(value, ast.Call):
            if isinstance(value.func, ast.Name) and value.args:
                argument_kind = self._alias_kind(value.args[0])
                if value.func.id in {"list", "tuple", "sorted"}:
                    if argument_kind == _MANIFEST_SEQUENCE_ALIAS:
                        return _MANIFEST_SEQUENCE_ALIAS
                if value.func.id in {"enumerate", "iter", "reversed"}:
                    if argument_kind == _MANIFEST_SEQUENCE_ALIAS:
                        return _MANIFEST_SEQUENCE_ALIAS
                if value.func.id == "dict" and argument_kind == _MANIFEST_ENTRY_ALIAS:
                    return _MANIFEST_ENTRY_ALIAS
            if isinstance(value.func, ast.Attribute):
                receiver_kind = self._alias_kind(value.func.value)
                if value.func.attr == "copy":
                    return receiver_kind
                if receiver_kind == _MANIFEST_ENTRY_ALIAS:
                    if value.func.attr == "get" and value.args:
                        key = value.args[0]
                        if (
                            isinstance(key, ast.Constant)
                            and key.value in _EXECUTABLE_SMOKE_SCALAR_FIELDS
                        ):
                            return None
                        return _MANIFEST_MUTABLE_ALIAS
                    if value.func.attr in {"items", "values"}:
                        return _MANIFEST_SEQUENCE_ALIAS
            return None
        if isinstance(value, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
            if self._comprehension_carries_alias(value.generators, value.elt):
                return _MANIFEST_SEQUENCE_ALIAS
            return None
        if isinstance(value, ast.DictComp):
            if self._comprehension_carries_alias(
                value.generators, value.key
            ) or self._comprehension_carries_alias(
                value.generators,
                value.value,
            ):
                return _MANIFEST_ENTRY_ALIAS
            return None
        if isinstance(value, ast.BinOp) and isinstance(value.op, (ast.Add, ast.Mult)):
            if self._alias_kind(value.left) == _MANIFEST_SEQUENCE_ALIAS or self._alias_kind(
                value.right
            ) == _MANIFEST_SEQUENCE_ALIAS:
                return _MANIFEST_SEQUENCE_ALIAS
        return None

    @staticmethod
    def _target_names(target: ast.AST) -> set[str]:
        if isinstance(target, ast.Name):
            return {target.id}
        if isinstance(target, (ast.List, ast.Tuple)):
            names: set[str] = set()
            for item in target.elts:
                names.update(_TopLevelManifestMutationVisitor._target_names(item))
            return names
        if isinstance(target, ast.Starred):
            return _TopLevelManifestMutationVisitor._target_names(target.value)
        return set()

    def _bind_alias(self, target: ast.AST, alias_kind: Optional[str]) -> None:
        if alias_kind is None:
            return
        if isinstance(target, ast.Name):
            if target.id != "EXECUTABLE_SMOKES":
                self._alias_scopes[-1][target.id] = alias_kind
            return
        if isinstance(target, (ast.List, ast.Tuple)):
            item_kind = (
                _MANIFEST_ENTRY_ALIAS
                if alias_kind == _MANIFEST_SEQUENCE_ALIAS
                else alias_kind
            )
            for item in target.elts:
                self._bind_alias(item, item_kind)
            return
        if isinstance(target, ast.Starred):
            self._bind_alias(target.value, _MANIFEST_SEQUENCE_ALIAS)

    def _mark_collector(self, target: ast.AST, value: Optional[ast.AST]) -> None:
        if not isinstance(target, ast.Name) or value is None:
            return
        if isinstance(value, (ast.List, ast.Dict, ast.Set)) and not any(
            self._alias_kind(child) is not None
            for child in ast.iter_child_nodes(value)
        ):
            self._collector_scopes[-1].add(target.id)

    def _is_local_collector(self, value: ast.AST) -> bool:
        return (
            isinstance(value, ast.Name)
            and value.id in self._collector_scopes[-1]
            and len(self._collector_scopes) > 1
        )

    def _target_mutates_manifest(
        self, target: ast.AST, *, include_alias_name: bool = False
    ) -> bool:
        if isinstance(target, ast.Name):
            return target.id == "EXECUTABLE_SMOKES" or (
                include_alias_name and self._name_alias_kind(target.id) is not None
            )
        if isinstance(target, (ast.Attribute, ast.Subscript)):
            return self._alias_kind(target.value) is not None or _ast_contains_name(
                target, "EXECUTABLE_SMOKES"
            )
        if isinstance(target, (ast.List, ast.Tuple)):
            return any(
                self._target_mutates_manifest(
                    item, include_alias_name=include_alias_name
                )
                for item in target.elts
            )
        if isinstance(target, ast.Starred):
            return self._target_mutates_manifest(
                target.value, include_alias_name=include_alias_name
            )
        return False

    @staticmethod
    def _is_direct_manifest_alias(value: ast.AST) -> bool:
        return isinstance(value, ast.Name) and value.id == "EXECUTABLE_SMOKES"

    def _visit_function_inputs(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda
    ) -> None:
        for default in [*node.args.defaults, *node.args.kw_defaults]:
            if default is not None:
                self.visit(default)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                self.visit(decorator)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function_inputs(node)
        self._push_scope()
        for statement in node.body:
            self.visit(statement)
        self._pop_scope()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function_inputs(node)
        self._push_scope()
        for statement in node.body:
            self.visit(statement)
        self._pop_scope()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for decorator in node.decorator_list:
            self.visit(decorator)
        for base in node.bases:
            self.visit(base)
        for keyword in node.keywords:
            self.visit(keyword.value)
        self._push_scope()
        for statement in node.body:
            self.visit(statement)
        self._pop_scope()

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self._visit_function_inputs(node)
        self._push_scope()
        self.visit(node.body)
        self._pop_scope()

    def visit_Assign(self, node: ast.Assign) -> None:
        if any(self._target_mutates_manifest(target) for target in node.targets):
            self._record(node, "is rebound or assigned through")
        elif self._is_direct_manifest_alias(node.value):
            self._record(node, "escapes through a direct alias")
        alias_kind = self._alias_kind(node.value)
        for target in node.targets:
            self._bind_alias(target, alias_kind)
            self._mark_collector(target, node.value)
        self.visit(node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if self._target_mutates_manifest(node.target):
            self._record(node, "is rebound or assigned through")
        elif node.value is not None and self._is_direct_manifest_alias(node.value):
            self._record(node, "escapes through a direct alias")
        if node.value is not None:
            self._bind_alias(node.target, self._alias_kind(node.value))
            self._mark_collector(node.target, node.value)
            self.visit(node.value)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        if self._target_mutates_manifest(node.target, include_alias_name=True):
            self._record(node, "is augmented")
        self.visit(node.value)

    def visit_Delete(self, node: ast.Delete) -> None:
        if any(self._target_mutates_manifest(target) for target in node.targets):
            self._record(node, "is deleted or deleted through")

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        if self._target_mutates_manifest(node.target):
            self._record(node, "is rebound by a named expression")
        elif self._is_direct_manifest_alias(node.value):
            self._record(node, "escapes through a direct alias")
        self._bind_alias(node.target, self._alias_kind(node.value))
        self.visit(node.value)

    def visit_For(self, node: ast.For) -> None:
        if self._target_mutates_manifest(node.target):
            self._record(node, "is rebound by a for target")
        self.visit(node.iter)
        self._bind_alias(node.target, self._iteration_alias_kind(node.iter))
        for statement in [*node.body, *node.orelse]:
            self.visit(statement)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        if self._target_mutates_manifest(node.target):
            self._record(node, "is rebound by an async-for target")
        self.visit(node.iter)
        self._bind_alias(node.target, self._iteration_alias_kind(node.iter))
        for statement in [*node.body, *node.orelse]:
            self.visit(statement)

    def _iteration_alias_kind(self, iterable: ast.AST) -> Optional[str]:
        iterable_kind = self._alias_kind(iterable)
        if iterable_kind == _MANIFEST_SEQUENCE_ALIAS:
            return _MANIFEST_ENTRY_ALIAS
        return None

    def _visit_comprehension(
        self,
        generators: List[ast.comprehension],
        values: List[ast.AST],
    ) -> None:
        self._push_scope()
        for generator in generators:
            self.visit(generator.iter)
            self._bind_alias(
                generator.target, self._iteration_alias_kind(generator.iter)
            )
            for condition in generator.ifs:
                self.visit(condition)
        for value in values:
            self.visit(value)
        self._pop_scope()

    def visit_ListComp(self, node: ast.ListComp) -> None:
        self._visit_comprehension(node.generators, [node.elt])

    def visit_SetComp(self, node: ast.SetComp) -> None:
        self._visit_comprehension(node.generators, [node.elt])

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        self._visit_comprehension(node.generators, [node.elt])

    def visit_DictComp(self, node: ast.DictComp) -> None:
        self._visit_comprehension(node.generators, [node.key, node.value])

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            if item.optional_vars is not None and self._target_mutates_manifest(
                item.optional_vars
            ):
                self._record(node, "is rebound by a with target")
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        for item in node.items:
            if item.optional_vars is not None and self._target_mutates_manifest(
                item.optional_vars
            ):
                self._record(node, "is rebound by an async-with target")
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name == "EXECUTABLE_SMOKES":
            self._record(node, "is rebound by an exception target")
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            bound_name = alias.asname or alias.name.split(".", 1)[0]
            if bound_name == "EXECUTABLE_SMOKES":
                self._record(node, "is rebound by an import")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            bound_name = alias.asname or alias.name
            if bound_name == "EXECUTABLE_SMOKES":
                self._record(node, "is rebound by an import")

    def visit_MatchAs(self, node: ast.MatchAs) -> None:
        if node.name == "EXECUTABLE_SMOKES":
            self._record(node, "is rebound by a match capture")
        self.generic_visit(node)

    def visit_MatchStar(self, node: ast.MatchStar) -> None:
        if node.name == "EXECUTABLE_SMOKES":
            self._record(node, "is rebound by a match capture")

    def visit_MatchMapping(self, node: ast.MatchMapping) -> None:
        if node.rest == "EXECUTABLE_SMOKES":
            self._record(node, "is rebound by a match capture")
        self.generic_visit(node)

    def visit_TypeAlias(self, node: ast.AST) -> None:
        target = getattr(node, "name", None)
        if isinstance(target, ast.AST) and self._target_mutates_manifest(target):
            self._record(node, "is rebound by a type alias")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        mutation_recorded = False
        if isinstance(node.func, ast.Attribute):
            receiver_kind = self._alias_kind(node.func.value)
            receiver_is_manifest = receiver_kind is not None or _ast_contains_name(
                node.func.value, "EXECUTABLE_SMOKES"
            )
            builtin_mutates_manifest = (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id in {"dict", "list"}
                and node.args
                and self._alias_kind(node.args[0]) is not None
            )
            operator_mutates_manifest = (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "operator"
                and node.func.attr in _EXECUTABLE_SMOKE_OPERATOR_MUTATORS
                and node.args
                and self._alias_kind(node.args[0]) is not None
            )
            if (
                node.func.attr in _EXECUTABLE_SMOKE_MUTATORS
                and (receiver_is_manifest or builtin_mutates_manifest)
            ) or operator_mutates_manifest:
                self._record(node, f"is mutated via {node.func.attr}()")
                mutation_recorded = True
            elif (
                receiver_kind is not None
                and node.func.attr not in _EXECUTABLE_SMOKE_READ_METHODS
            ):
                self._record(node, f"escapes through {node.func.attr}()")
                mutation_recorded = True
        elif (
            isinstance(node.func, ast.Name)
            and node.func.id in {"delattr", "setattr"}
            and node.args
            and self._alias_kind(node.args[0]) is not None
        ):
            self._record(node, f"is mutated via {node.func.id}()")
            mutation_recorded = True

        alias_arguments = [
            self._alias_kind(
                argument.value if isinstance(argument, ast.Starred) else argument
            )
            for argument in node.args
        ] + [self._alias_kind(keyword.value) for keyword in node.keywords]
        has_alias_argument = any(kind is not None for kind in alias_arguments)
        read_only_call = (
            isinstance(node.func, ast.Name)
            and node.func.id in _EXECUTABLE_SMOKE_READ_CALLS
        )
        local_collection = (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in {"append", "extend", "insert"}
            and self._is_local_collector(node.func.value)
        )
        if has_alias_argument and local_collection and not mutation_recorded:
            self._bind_alias(node.func.value, _MANIFEST_SEQUENCE_ALIAS)
        elif has_alias_argument and not read_only_call and not mutation_recorded:
            self._record(node, "escapes through an alias call argument")
        self.generic_visit(node)


_MANIFEST_GUARD_SELF_CHECKS = (
    (
        "shallow-list-nested-mutation",
        "copies = list(EXECUTABLE_SMOKES)\n"
        "copies[0]['expect'].append('forged')\n",
        "is mutated via append()",
    ),
    (
        "shallow-tuple-nested-assignment",
        "copies = tuple(EXECUTABLE_SMOKES)\n"
        "copies[0]['expect'][0] = 'forged'\n",
        "is rebound or assigned through",
    ),
    (
        "shallow-copy-helper-escape",
        "copies = list(EXECUTABLE_SMOKES)\n"
        "mutate_smoke(copies[0])\n",
        "escapes through an alias call argument",
    ),
    (
        "iteration-nested-mutation",
        "for smoke in EXECUTABLE_SMOKES:\n"
        "    smoke['expect'].append('forged')\n",
        "is mutated via append()",
    ),
    (
        "iteration-helper-escape",
        "for smoke in tuple(EXECUTABLE_SMOKES):\n"
        "    mutate_smoke(smoke)\n",
        "escapes through an alias call argument",
    ),
    (
        "pre-assignment-helper-mutation",
        "def mutate_manifest():\n"
        "    EXECUTABLE_SMOKES[0]['expect'].append('forged')\n"
        "mutate_manifest()\n",
        "is mutated via append()",
    ),
)
_MANIFEST_GUARD_READ_ONLY_SELF_CHECKS = (
    (
        "direct-read",
        "manifest_size = len(EXECUTABLE_SMOKES)\n",
    ),
    (
        "shallow-copy-read",
        "copies = list(EXECUTABLE_SMOKES)\n"
        "copy_size = len(copies)\n"
        "first_name = copies[0]['name']\n",
    ),
    (
        "iteration-read",
        "for smoke in tuple(EXECUTABLE_SMOKES):\n"
        "    print(smoke['fixture'])\n",
    ),
)


def _manifest_guard_self_check() -> List[str]:
    failures: List[str] = []
    for case_name, source, required_fragment in _MANIFEST_GUARD_SELF_CHECKS:
        module = ast.parse(source, filename=f"manifest-guard:{case_name}")
        visitor = _TopLevelManifestMutationVisitor()
        for node in module.body:
            visitor.visit(node)
        if not any(required_fragment in error for error in visitor.errors):
            failures.append(
                "auditor manifest guard self-check failed to reject "
                f"{case_name}: expected {required_fragment!r}, got {visitor.errors!r}"
            )

    for case_name, source in _MANIFEST_GUARD_READ_ONLY_SELF_CHECKS:
        module = ast.parse(source, filename=f"manifest-guard:{case_name}")
        visitor = _TopLevelManifestMutationVisitor()
        for node in module.body:
            visitor.visit(node)
        if visitor.errors:
            failures.append(
                "auditor manifest guard self-check rejected read-only case "
                f"{case_name}: {visitor.errors!r}"
            )
    return failures


def _literal_executable_smokes(
    path: Path,
) -> Tuple[Dict[str, _LiteralExecutableSmoke], List[str]]:
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

    manifests: List[Tuple[int, ast.expr]] = []
    for body_index, node in enumerate(module.body):
        if isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == "EXECUTABLE_SMOKES"
                for target in node.targets
            ):
                manifests.append((body_index, node.value))
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "EXECUTABLE_SMOKES"
            and node.value is not None
        ):
            manifests.append((body_index, node.value))

    if not manifests:
        return {}, ["check_v4.py: literal EXECUTABLE_SMOKES assignment missing"]
    if len(manifests) != 1:
        return {}, [
            f"check_v4.py: EXECUTABLE_SMOKES assigned {len(manifests)} times; expected once"
        ]

    try:
        manifest_index, manifest_expression = manifests[0]
        manifest = ast.literal_eval(manifest_expression)
    except (SyntaxError, TypeError, ValueError) as exc:
        return {}, [
            "check_v4.py: EXECUTABLE_SMOKES must be a literal manifest "
            f"({type(exc).__name__}: {exc})"
        ]

    if not isinstance(manifest, list):
        return {}, ["check_v4.py: EXECUTABLE_SMOKES must be a literal list"]

    mutation_visitor = _TopLevelManifestMutationVisitor()
    for body_index, node in enumerate(module.body):
        if body_index != manifest_index:
            mutation_visitor.visit(node)

    smokes: Dict[str, _LiteralExecutableSmoke] = {}
    seen_fixtures: Dict[str, int] = {}
    errors: List[str] = [
        *_manifest_guard_self_check(),
        *mutation_visitor.errors,
    ]
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
        if any(not isinstance(value, str) or not value for value in expects):
            errors.append(
                f"EXECUTABLE_SMOKES: {fixture} expect list contains a non-string or empty value"
            )
            continue

        exact_expects = entry.get("expect_exact", [])
        if not isinstance(exact_expects, list):
            errors.append(
                f"EXECUTABLE_SMOKES: {fixture} expect_exact must be a literal list"
            )
            continue
        if any(not isinstance(value, str) or not value for value in exact_expects):
            errors.append(
                f"EXECUTABLE_SMOKES: {fixture} expect_exact contains a non-string or empty value"
            )
            continue
        if not expects and not exact_expects:
            errors.append(f"EXECUTABLE_SMOKES: {fixture} has no expectations")
            continue

        expect_mode = entry.get("expect_mode")
        if expect_mode is not None and (
            not isinstance(expect_mode, str) or not expect_mode
        ):
            errors.append(
                f"EXECUTABLE_SMOKES: {fixture} expect_mode must be a non-empty string"
            )
            continue

        expect_unique = entry.get("expect_unique", False)
        if not isinstance(expect_unique, bool):
            errors.append(
                f"EXECUTABLE_SMOKES: {fixture} expect_unique must be a boolean"
            )
            continue
        if expect_unique and expect_mode != "line":
            errors.append(
                f"EXECUTABLE_SMOKES: {fixture} expect_unique requires expect_mode='line'"
            )
            continue
        if expect_unique:
            registered_counts = Counter([*expects, *exact_expects])
            duplicate_lines = [
                line for line, count in registered_counts.items() if count != 1
            ]
            if duplicate_lines:
                errors.append(
                    f"EXECUTABLE_SMOKES: {fixture} expect_unique registers duplicate lines "
                    + ", ".join(repr(line) for line in duplicate_lines)
                )
                continue

        smokes[fixture] = _LiteralExecutableSmoke(
            expect=tuple(expects),
            expect_exact=tuple(exact_expects),
            expect_mode=expect_mode,
            expect_unique=expect_unique,
        )

    return smokes, errors


def _explicit_strict_smoke_errors(
    smokes: Dict[str, _LiteralExecutableSmoke], fixtures: Tuple[str, ...]
) -> List[str]:
    errors: List[str] = []
    for fixture in fixtures:
        smoke = smokes.get(fixture)
        if smoke is None:
            errors.append(f"EXECUTABLE_SMOKES: {fixture} entry missing")
            continue
        if smoke.expect_mode != "line":
            errors.append(
                f"EXECUTABLE_SMOKES: {fixture} expect_mode must be 'line'"
            )
        if smoke.expect_unique is not True:
            errors.append(
                f"EXECUTABLE_SMOKES: {fixture} expect_unique must be true"
            )
        if smoke.expect_exact:
            errors.append(
                f"EXECUTABLE_SMOKES: {fixture} must keep every exact line in expect"
            )
        for expected in _EXPLICIT_STRICT_SMOKE_ORACLES[fixture]:
            if expected not in smoke.expect:
                errors.append(
                    f"EXECUTABLE_SMOKES: {fixture} missing expected value {expected!r}"
                )
    return errors


def audit_conformance(paths: List[Path]) -> int:
    """
    Verify the v0.13.x baseline and promoted V4 implementation contracts.
    Checks every audited claim is still backed by code, files, or executable
    smoke oracles.

    Returns 1 if any audited contract is broken, 0 otherwise.

    The check set remains explicit: baseline contracts and selected V4 slices
    are guarded here while unpromoted V4 contracts remain outside the gate.
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

    # Check 6b: V3 run freshness and distribution replacement contracts.
    run_freshness_missing: List[str] = []
    freshness_sources = {
        "run pipeline": (
            repo / "src" / "cli" / "run.fk",
            (
                'CLI_RUN_CACHE_SCHEMA = "freak-run-cache-v2"',
                "task cli_run_fingerprint",
                "task cli_run_cache_record",
                "fs::delete(cache_file)",
                "confirmed != fingerprint",
                "launch_fingerprint != fingerprint",
                'run_path = "./" + run_path',
                "run cache hit",
            ),
        ),
        "build invalidation": (
            repo / "src" / "cli" / "build.fk",
            (
                'pilot run_cache_file = cli_binary_path(src_file) + ".freak-run-cache"',
                "fs::delete(run_cache_file)",
                "task cli_cross_target_is_safe",
                "invalid target triple",
                'pilot use_bundle = is_win and cross == "" and runtime_obj_ext != ""',
                "Linking packaged Windows runtime objects",
                "POSIX double quotes still expand",
            ),
        ),
        "main dispatch": (
            cli_main,
            ("pilot run_exit = cli_run", "process::exit(run_exit)"),
        ),
        "diagnostic origins": (
            repo / "src" / "compiler" / "v3" / "helpers.fk",
            (
                "tok_origin_files",
                "source_map_register",
                "source_location_files",
                "get_file_source_line",
            ),
        ),
        "nominal hard gate": (
            repo / "src" / "compiler" / "v3" / "checker.fk",
            (
                "tc_builtin_method_allowed",
                "tc_builtin_method_arity",
                "tc_expr_type",
                "ast_expr_files",
            ),
        ),
        "codegen gate regression": (
            repo / "tests" / "v3_codegen_error_gate.py",
            (
                "assert_builtin_signature_parity",
                "classified builtin has no backend lowering",
                "builtin task collision",
                "malformed-stdlib-home/std/math.fk:2:",
                "unclosed installed std block origin",
                "PrimitiveNamed",
                "primitive_methods_ok.fk",
                "missing_multiline",
            ),
        ),
        "regression": (
            repo / "tests" / "v3_run_freshness.py",
            (
                "CACHE_A",
                "CACHE_B",
                "externally replaced artifact",
                'for backend in ("--c", "--llvm")',
                "FREAK_PATH_INJECTED",
                "stale object",
                "runtime_objects",
                "Linking packaged Windows runtime objects",
                "failed rebuild left stale freshness proof",
            ),
        ),
        "process runtime": (
            repo / "freakc" / "runtime" / "freak_runtime.c",
            ("freak_normalize_process_status", "WIFEXITED"),
        ),
        "LLVM process runtime": (
            repo / "freakc" / "runtime" / "freak_llvm_runtime.c",
            ("freak_llvm_normalize_process_status", "WIFEXITED"),
        ),
        "word ownership runtime": (
            repo / "freakc" / "runtime" / "freak_runtime.c",
            (
                "freak_word_replace_owned",
                "freak_llvm_word_release_replaced",
                "freak_llvm_word_adopt",
                "FREAK_RUNTIME_OWNERSHIP_AUDIT",
                "freak_array_set_owned",
                "freak_array_release_owned",
                "freak_word_join_owned",
            ),
        ),
        "word ownership regression": (
            repo / "tests" / "v3_word_ownership.py",
            (
                "repeat 512 times",
                "-fsanitize=address",
                "LeakSanitizer",
                "text = text",
                "ownership audit found 1 unreleased word allocation",
                "literal_items",
                "message.observe(message.value)",
            ),
        ),
        "POSIX installer": (
            repo / "install.sh",
            (
                'STAGE_DIR="$TMPDIR_INSTALL/stage"',
                "restore_previous_payload",
                "TRANSACTION_ACTIVE",
                "reconcile_orphaned_transaction",
                "FREAK_INSTALL_TEST_FAIL_RESTORE",
                ".freak-backup-",
                "distribution-files.manifest",
            ),
        ),
        "Windows installer": (
            repo / "install.ps1",
            (
                '$StageDir = Join-Path $TmpDir "stage"',
                ".freak-backup-",
                ".freak-upgrade-pending",
                ".freak-binary-backup",
                "Get-FileHash",
                "previous payload was restored",
                "distribution-files.manifest",
            ),
        ),
        "release payload": (
            repo / ".github" / "workflows" / "release.yml",
            (
                "packaging/distribution-files.manifest",
                "dist/freak/distribution-files.manifest",
                "required WinGet manifest missing",
            ),
        ),
    }
    for label, (source_path, needles) in freshness_sources.items():
        if not source_path.exists():
            run_freshness_missing.append(f"{label}: {source_path.name} missing")
            continue
        source_text = source_path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in source_text:
                run_freshness_missing.append(f"{label}: {needle}")
        if label == "release payload" and (
            "Pre-compile runtime to .o" in source_text
            or "dist/freak/runtime/freak_runtime.o" in source_text
        ):
            run_freshness_missing.append(
                "release payload: unsafe precompiled POSIX runtime objects"
            )
    bible_text = bible.read_text(encoding="utf-8") if bible.exists() else ""
    audit_text = audit_doc.read_text(encoding="utf-8") if audit_doc.exists() else ""
    for label, text in (("bible", bible_text), ("audit", audit_text)):
        if "output artifact" not in text or "not serialized" not in text:
            run_freshness_missing.append(f"{label}: honest freshness boundary")
    add(
        "V3 run freshness",
        not run_freshness_missing,
        "content cache + stale-run gate + staged installers wired"
        if not run_freshness_missing
        else f"{len(run_freshness_missing)} gap(s)",
    )
    if run_freshness_missing:
        failures.append(
            "V3 run freshness/install cleanup regressed: "
            + "; ".join(run_freshness_missing)
        )

    # Check 6c: one complete distribution manifest drives release/install,
    # doctor proves the usable toolchain, and `freak upgrade` stays live with
    # the immutable v0.14.0 migration boundary documented honestly.
    distribution_missing: List[str] = []
    dist_manifest = repo / "packaging" / "distribution-files.manifest"
    manifest_sources: set[str] = set()
    manifest_destinations: set[str] = set()
    if not dist_manifest.exists():
        distribution_missing.append("distribution manifest missing")
    else:
        for raw_line in dist_manifest.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            source, separator, destination = line.partition("|")
            if not separator or not source or not destination:
                distribution_missing.append(f"malformed manifest entry: {line}")
                continue
            if source in manifest_sources:
                distribution_missing.append(f"duplicate manifest source: {source}")
            if destination in manifest_destinations:
                distribution_missing.append(
                    f"duplicate manifest destination: {destination}"
                )
            if ".." in Path(source).parts or ".." in Path(destination).parts:
                distribution_missing.append(f"unsafe manifest entry: {line}")
            manifest_sources.add(source)
            manifest_destinations.add(destination)
            if not (repo / source).is_file():
                distribution_missing.append(f"manifest source missing: {source}")

        expected_sources = {
            path.relative_to(repo).as_posix()
            for path in (repo / "std").rglob("*.fk")
        }
        expected_sources.update(
            {
                "freakc/runtime/freak_runtime.c",
                "freakc/runtime/freak_runtime.h",
                "freakc/runtime/freak_llvm_runtime.c",
                "freakc/runtime/ui/win32_backend.c",
                "freakc/runtime/ui/freak_ui_platform.h",
                "freakc/runtime/freak_abi",
                "std/freak_abi",
            }
        )
        for missing_source in sorted(expected_sources - manifest_sources):
            distribution_missing.append(
                f"required file absent from manifest: {missing_source}"
            )
        for extra_source in sorted(manifest_sources - expected_sources):
            distribution_missing.append(
                f"unexpected manifest source: {extra_source}"
            )

    distribution_sources = {
        "POSIX dependency installer": (
            repo / "install.sh",
            (
                "--with-deps",
                "FREAK_INSTALL_ARCHIVE",
                "FREAK_INSTALL_TEST_FAIL_RESTORE",
                "reconcile_orphaned_transaction",
                "distribution-files.manifest",
                "verify_downloaded_archive",
                "SHA256SUMS",
            ),
        ),
        "Windows dependency installer": (
            repo / "install.ps1",
            (
                "Test-ClangToolchain",
                "MartinStorsjo.LLVM-MinGW.UCRT",
                "Start-DeferredBinaryReplacement",
                ".freak-upgrade-pending",
                "Get-Process -Id",
                "Assert-DownloadedArchiveChecksum",
                "SHA256SUMS",
            ),
        ),
        "doctor": (
            repo / "src" / "cli" / "doctor.fk",
            (
                "modules_expected\\\": 11",
                "files_expected\\\": 6",
                "FREAK_V3_ABI",
                "ABI mismatch",
                "upgrade_pending",
                "ui/window.fk",
                'process::env("TMPDIR")',
                "probe_run_exit == 0",
                "compile, link, and execution work",
                "-> int",
            ),
        ),
        "upgrade": (
            repo / "src" / "cli" / "hangar.fk",
            ("FREAK_UPGRADE_SCRIPT", "tagged installer", "migration limitations"),
        ),
        "CLI exit propagation": (
            cli_main,
            ("process::exit(upgrade_res)", "process::exit(doctor_exit)"),
        ),
        "regression": (
            repo / "tests" / "v3_install_doctor_upgrade.py",
            (
                "check_offline_installer",
                "FREAK_INSTALL_TEST_FAIL_APPLY",
                "FREAK_INSTALL_TEST_FAIL_RESTORE",
                ".freak-upgrade-pending",
                "check_doctor",
                "FREAK_DOCTOR_INSTALL_COMMAND",
                "check_upgrade",
            ),
        ),
        "CI": (
            repo / ".github" / "workflows" / "ci.yml",
            ("tests/v3_install_doctor_upgrade.py", "Pre-compile Windows runtime objects"),
        ),
        "release": (
            repo / ".github" / "workflows" / "release.yml",
            (
                "LLVM_MINGW_SHA256",
                "Pre-compile Windows runtime objects",
                "freak_runtime.obj dist/freak/runtime/",
                "freak_llvm_runtime.obj dist/freak/runtime/",
                "freak_ui_win32.obj dist/freak/runtime/",
            ),
        ),
        "release-shaped regression": (
            repo / "tests" / "v3_release_install_smoke.py",
            (
                "distribution-files.manifest",
                "compile, link, and execution work",
                "Linking packaged Windows runtime objects",
                'installed_hangar), "--version"',
            ),
        ),
        "release version invariant": (
            repo / "tools" / "release_version.py",
            (
                "FREAK_VERSION",
                "CLI_VERSION = FREAK_VERSION",
                "FREAKC_VERSION = FREAK_VERSION",
                "Git tag",
                "WinGet",
            ),
        ),
    }
    for label, (source_path, needles) in distribution_sources.items():
        if not source_path.exists():
            distribution_missing.append(f"{label}: {source_path.name} missing")
            continue
        source_text = source_path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in source_text:
                distribution_missing.append(f"{label}: {needle}")
    add(
        "V3 distribution/doctor/upgrade",
        not distribution_missing,
        "complete manifest + usable toolchain + Windows object bundle + staged upgrade boundary"
        if not distribution_missing
        else f"{len(distribution_missing)} gap(s)",
    )
    if distribution_missing:
        failures.append(
            "V3 distribution/doctor/upgrade regressed: "
            + "; ".join(distribution_missing)
        )

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

    # Check 7f: V4 closure capture frontend/query and Meiya surface
    # This guards the promoted §1.8 checkpoint without claiming backend closure
    # environments, nested closure inference, borrowed-return contracts, or
    # Send/Sync proof.
    closure_capture_missing: List[str] = []
    closure_capture_files = (
        (
            repo / "src" / "compiler" / "v4" / "crates" / "freak_parse" / "src" / "lib.fk",
            "freak_parse",
            (
                'pilot v4_node_closure = "ClosureExpr"',
                "task v4_parse_parse_closures_in_item(",
                'token_value == "\\n" and depth == 0',
                "expected | after closure parameters",
                "expected expression after closure =>",
            ),
        ),
        (
            repo / "src" / "compiler" / "v4" / "crates" / "freak_hir" / "src" / "lib.fk",
            "freak_hir",
            (
                "task v4_hir_closure_count(",
                "task v4_hir_closure_at_offset(",
            ),
        ),
        (
            repo / "src" / "compiler" / "v4" / "crates" / "freak_ty" / "src" / "lib.fk",
            "freak_ty",
            (
                'pilot v4_ty_closure_one_shot = "OneShot"',
                "task v4_ty_closure_type_at(",
                "task v4_ty_closure_as_task_type(",
                "task v4_ty_infer_closure_block_return(",
                "task v4_ty_validate_closure_params(",
                "give back v4_ty_closure_doctrine(ty_name) == v4_ty_closure_callable",
                "task v4_ty_doctrine_method_param_mode(",
            ),
        ),
        (
            repo / "src" / "compiler" / "v4" / "crates" / "freak_mir" / "src" / "lib.fk",
            "freak_mir",
            (
                'pilot v4_mir_rvalue_closure = "Closure"',
                'pilot v4_mir_rvalue_capture_borrow = "CaptureBorrow"',
                'pilot v4_mir_rvalue_capture_borrow_mut = "CaptureBorrowMut"',
                'pilot v4_mir_rvalue_capture_copy = "CaptureCopy"',
                'pilot v4_mir_rvalue_capture_move = "CaptureMove"',
                "task v4_mir_try_lower_closure_expr(",
                "task v4_mir_closure_local_decl_name_token(",
                "task v4_mir_closure_identifier_is_member_name(",
                "task v4_mir_closure_scope_pop(",
                "task v4_mir_closure_receiver_call_is_mutating(",
                "Yuuko cannot copy this closure capture",
                "Meiya keeps this closure capture immutable",
            ),
        ),
        (
            repo / "src" / "compiler" / "v4" / "crates" / "freak_borrowck" / "src" / "lib.fk",
            "freak_borrowck",
            (
                "task v4_borrowck_stored_closure_holder(",
                "task v4_borrowck_holder_alias_from_stmt(",
                "task v4_borrowck_collect_call_callee_paths(",
                "v4_ty_closure_one_shot",
                "v4_ty_closure_mut_callable",
            ),
        ),
        (
            repo / "src" / "compiler" / "v4" / "crates" / "freak_editor" / "src" / "lib.fk",
            "freak_editor",
            (
                "task v4_editor_local_type_display_at(",
                "task v4_editor_closure_param_detail(",
                "task v4_editor_identifier_is_member_name(",
                'give back "capture " + capture_mode + " " + display',
            ),
        ),
    )
    for closure_path, closure_label, needles in closure_capture_files:
        if not closure_path.exists():
            closure_capture_missing.append(f"{closure_label}/src/lib.fk missing")
            continue
        closure_src = closure_path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in closure_src:
                closure_capture_missing.append(f"{closure_label}: {needle}")

    closure_smoke_needles = (
        (
            repo / "src" / "compiler" / "v4" / "tests" / "closure_capture_smoke.fk",
            ("closure-capture-block-ty=", "closure-capture-shadow-count=", "closure-capture-member-name=", "closure-capture-scoped-name1=", "closure-capture-callable-copy-type=", "closure-capture-status="),
        ),
        (
            repo / "src" / "compiler" / "v4" / "tests" / "closure_capture_negative_smoke.fk",
            ("closure-negative-borrow-alias-status=", "closure-negative-mut-transfer-status=", "closure-negative-duplicate-param-message=", "closure-negative-immutable-message-count="),
        ),
        (
            repo / "src" / "compiler" / "v4" / "tests" / "closure_recovery_smoke.fk",
            ("closure-recovery-all-malformed-recorded=", "closure-recovery-following-closure-preserved=", "closure-recovery-survivor-present="),
        ),
        (
            repo / "src" / "compiler" / "v4" / "tests" / "closure_capture_editor_smoke.fk",
            ("closure-editor-param-semantic=", "closure-editor-param-definition-matches=", "closure-editor-param-lsp-completion=", "closure-editor-member-resolution=", "closure-editor-invalidation-matches-diff="),
        ),
    )
    for smoke_path, needles in closure_smoke_needles:
        if not smoke_path.exists():
            closure_capture_missing.append(f"smoke fixture: {smoke_path.name}")
            continue
        smoke_src = smoke_path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in smoke_src:
                closure_capture_missing.append(f"{smoke_path.name}: {needle}")

    closure_harness = repo / "src" / "compiler" / "v4" / "check_v4.py"
    if closure_harness.exists():
        closure_harness_src = closure_harness.read_text(encoding="utf-8")
        for needle in (
            '"fixture": "closure_capture_smoke.fk"',
            '"fixture": "closure_capture_negative_smoke.fk"',
            '"fixture": "closure_recovery_smoke.fk"',
            '"fixture": "closure_capture_editor_smoke.fk"',
            '"closure-negative-borrow-diagnostics=9"',
            '"closure-capture-block-ty=closure[Callable,borrow](value:int)->int"',
            '"closure-capture-scoped-name1=count"',
            '"closure-capture-callable-copy-type=true"',
            '"closure-negative-immutable-message-count=2"',
            '"closure-recovery-following-closure-preserved=true"',
            '"closure-editor-param-definition-matches=true"',
            '"closure-editor-member-resolution=true"',
            '"closure-editor-invalidation-matches-diff=true"',
        ):
            if needle not in closure_harness_src:
                closure_capture_missing.append(f"check_v4.py: {needle}")
    else:
        closure_capture_missing.append("check_v4.py harness missing")

    closure_docs = (
        (bible, "Yuuko found the environment, Meiya guards the door"),
        (audit_doc, "V4 closure checkpoint"),
        (repo / "src" / "compiler" / "v4" / "README.md", "Closures now form a complete first-pass frontend/query slice"),
    )
    for doc_path, needle in closure_docs:
        if not doc_path.exists() or needle not in doc_path.read_text(encoding="utf-8"):
            closure_capture_missing.append(f"closure documentation: {doc_path.name}: {needle}")

    add(
        "V4 closure captures",
        not closure_capture_missing,
        "parse/HIR/TY/MIR/Meiya/editor/snapshot/invalidation smokes wired"
        if not closure_capture_missing
        else f"{len(closure_capture_missing)} gap(s)",
    )
    if closure_capture_missing:
        failures.append("V4 closure capture surface regressed: " + "; ".join(closure_capture_missing))

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
    v4_runtime_c_return = repo / "freakc" / "runtime" / "freak_runtime.c"
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
    contract_region_docs = (
        (
            bible,
            "> **⚠️ V4 partial — Meiya is waking up:**",
            "\n### 4.1 Ownership Rules",
            (
                "Borrowed return types now flow through TY/MIR.",
                "all 18\n> invalidation report fields",
                "15 concrete query families",
                "three aggregate\n> totals",
                "`some(...)`, `ok(...)`",
                "Task-local tuples, fixed arrays, shapes, and route payloads",
                "normalized into declaration order",
                "field-sensitive final-use liveness",
                "`LoanMut` remains exclusive",
                "existing MIR/borrowck snapshots",
                "non-ordinary aggregate task boundaries",
                "runtime\n> aggregate-loan ABI",
                "bounded rings",
                "iterative\n> memo worklist",
                "reverse dependency edges",
                "4,096 memo entries",
                "65,536 work items",
                "solved-memo frontier",
                "snapshot v2 restore",
                "legacy v1 snapshots import",
                "truncated v2 records are rejected",
                "64-diamond fixture",
                "not full region inference",
            ),
        ),
        (
            audit_doc,
            "Contract-region checkpoint (",
            "\n---",
            (
                "Contract-region checkpoint (**⚠️ V4 partial**)",
                "(ty_id, sig_id)",
                "all 18 report fields",
                "15 concrete query families",
                "three aggregate totals",
                "`some(...)`, `ok(...)`",
                "complete fixed-layout storage",
                "declaration order",
                "selected field's loan",
                "`LoanMut` exclusivity",
                "existing MIR/borrowck component snapshots",
                "non-ordinary aggregate task parameters and returns",
                "runtime aggregate-loan ABI",
                "canonical-value",
                "arena reclamation remains open",
                "iterative\ndependency discovery",
                "per-memo reverse dependency adjacency lists",
                "memo/dependency/work/source-fact/path-byte\nbudget exhaustion",
                "64-diamond stress fixture",
                "v2 borrowck snapshot",
                "Legacy v1 imports",
                "solved-memo frontier",
            ),
        ),
        (
            repo / "freakc-v4-00-unit-architecture.md",
            "### Implemented Contract-Region Checkpoint (V4 Partial)",
            "\n### Why MIR is Required",
            (
                "Implemented Contract-Region Checkpoint (V4 Partial)",
                "(ty_id, sig_id)",
                "18 invalidation report fields",
                "15 concrete query families",
                "three aggregate totals",
                "`some(...)`, `ok(...)`",
                "task-local fixed-layout vocabulary",
                "declaration-keyed aggregate children",
                "field-sensitive final-use liveness",
                "existing tooling protocols",
                "non-ordinary aggregate task parameters or returns do not carry fixed-layout provenance",
                "non-ordinary aggregate task boundaries",
                "backend lowering remain future Meiya work",
                "bounded ring",
                "iterative worklist",
                "reverse dependency edge",
                "4,096 memo",
                "65,536 processed work items",
                "solved-memo frontier",
                "borrowck snapshot v2",
                "Legacy v1 snapshots remain importable",
                "64-diamond fixture",
                "not completed",
            ),
        ),
        (
            repo / "src" / "compiler" / "v4" / "README.md",
            "Borrowed return types now carry through TY/MIR.",
            "\nThe first `Shared<T>` / `Weak<T>` ownership surface",
            (
                "all 18 report fields: 15",
                "three refreshed aggregate totals",
                "`some(...)`, `ok(...)`",
                "task-local fixed-layout aggregates",
                "declaration order",
                "unrelated siblings live",
                "`LoanMut` remains exclusive",
                "existing query families and 00-Unit",
                "non-ordinary aggregate task parameters or returns remain outside fixed-layout provenance",
                "runtime aggregate-loan ABI",
                "bounded rings",
                "iterative memo worklist",
                "reverse dependency edges",
                "4,096 memo",
                "65,536 work items",
                "solved-memo frontier",
                "borrowck snapshot v2",
                "Legacy v1 snapshots remain importable",
                "64-diamond CFG\nsmoke",
                "not full region inference",
            ),
        ),
    )
    for doc_path, start_marker, end_marker, needles in contract_region_docs:
        if not doc_path.exists():
            contract_region_missing.append(f"contract-region documentation missing: {doc_path.name}")
            continue
        doc_source = doc_path.read_text(encoding="utf-8")
        checkpoint = _bounded_text_section(doc_source, start_marker, end_marker)
        if checkpoint is None:
            contract_region_missing.append(
                f"{doc_path.name}: contract-region checkpoint boundaries missing"
            )
            continue
        for needle in needles:
            if needle not in checkpoint:
                contract_region_missing.append(
                    f"{doc_path.name}: contract-region checkpoint missing {needle!r}"
                )
    contract_region_status_docs = (
        (
            bible,
            (
                (
                    "Borrowed return types now flow through TY/MIR.",
                    "\n### 4.1 Ownership Rules",
                    (
                        "Body-derived provenance/source discovery is implemented in this slice",
                    ),
                ),
                (
                    "the current 00-Unit slice supports",
                    "\n> Scalar holders",
                    (
                        "Lifetime eligibility remains signature-derived from declared ordinary-task contracts",
                    ),
                ),
            ),
            (
                "body-derived/general lexical inference",
                "not body-derived or general lexical",
            ),
        ),
        (
            audit_doc,
            (
                (
                    "| Borrowed returns `-> lend T` / `-> lend mut T` |",
                    "\nContract-region checkpoint (",
                    ("Lifetime eligibility remains signature-derived",),
                ),
                (
                    "Contract-region checkpoint (",
                    "\nClosure-capture checkpoint (",
                    (
                        "Body-derived provenance/source discovery through reaching definitions is\nimplemented",
                    ),
                ),
            ),
            (
                "Body-derived/general lexical inference",
                "body-derived/general lexical solving",
                "not body-derived/general lexical inference",
                "does not claim body-derived/general lexical inference",
                "Remaining gaps include body-derived/general lexical inference",
            ),
        ),
        (
            repo / "src" / "compiler" / "v4" / "README.md",
            (
                (
                    "Borrowed return types now carry through TY/MIR.",
                    "\nThe first `Shared<T>` / `Weak<T>` ownership surface",
                    (
                        "Body-derived provenance/source discovery through reaching definitions is\nimplemented",
                        "Lifetime\neligibility remains signature-derived from declared ordinary-task contracts",
                    ),
                ),
            ),
            (
                "body-derived source discovery and general lexical lifetime inference\nremain open",
            ),
        ),
    )
    for (
        doc_path,
        status_sections,
        stale_statuses,
    ) in contract_region_status_docs:
        if not doc_path.exists():
            contract_region_missing.append(
                f"contract-region status documentation missing: {doc_path.name}"
            )
            continue
        doc_source = doc_path.read_text(encoding="utf-8")
        for start_marker, end_marker, required_statuses in status_sections:
            checkpoint = _bounded_text_section(doc_source, start_marker, end_marker)
            if checkpoint is None:
                contract_region_missing.append(
                    f"{doc_path.name}: contract-region status boundaries missing"
                )
                continue
            for required_status in required_statuses:
                if required_status not in checkpoint:
                    contract_region_missing.append(
                        f"{doc_path.name}: contract-region checkpoint status missing {required_status!r}"
                    )
        for stale_status in stale_statuses:
            if stale_status in doc_source:
                contract_region_missing.append(
                    f"{doc_path.name}: stale contract-region status {stale_status!r}"
                )
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
            "pilot v4_ty_borrowed_return_source_cache_capacity_value = 32",
            "pilot v4_ty_borrowed_return_source_cache_entry_count_value = 0",
            "task v4_ty_borrowed_return_source_cache_store(",
            "task v4_ty_borrowed_return_source_cache_invalidate_file(",
            "task v4_ty_borrowed_return_source_cache_invalidate_signature(",
            "task v4_ty_borrowed_return_source_cache_capacity(",
            "task v4_ty_borrowed_return_source_cache_entry_count(",
            "task v4_ty_signature_borrowed_return_source_cache(",
            "task v4_ty_borrowed_return_source_cache_build_count(",
            "task v4_ty_signature_borrowed_return_source_param_count(",
            "task v4_ty_signature_borrowed_return_source_param_at(",
            "v4_ty_signature_can_declare_generics",
            "v4_ty_validate_signature_generic_bounds",
            "v4_ty_type_contains_named_lend",
            "task v4_ty_type_contains_lend(",
            "task v4_ty_type_is_array_repeatable(",
            "task v4_ty_is_bare_type_pattern_binding(",
            "task v4_ty_validate_no_lend_storage(",
            "task v4_ty_fixed_lend_leaf_count(",
            "pilot v4_ty_fixed_lend_leaf_limit = 256",
            "pilot v4_ty_return_lend_source_limit = 256",
            "v4_ty_return_lend_source_opaque",
            "task v4_ty_fixed_lend_leaf_type_at(",
            "task v4_ty_fixed_lend_leaf_projection_at(",
            "task v4_ty_fixed_lend_leaf_route_guard_at(",
            "task v4_ty_signature_return_lend_source_count(",
            "task v4_ty_return_lend_source_payload_append_bounded(",
            "task v4_ty_return_lend_source_payload_count(",
            "task v4_ty_return_lend_source_payload_at(",
            "task v4_ty_signature_return_lend_source_payload(",
            "task v4_ty_signature_return_lend_source_param_at(",
            "task v4_ty_signature_return_lend_source_projection_at(",
            "task v4_ty_signature_return_lend_source_route_guard_at(",
            "task v4_ty_signature_lend_leaf_contract_matches(",
            "task v4_ty_types_same_in_signature(",
            "task v4_ty_validate_aggregate_return_lend_contracts(",
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
            "task v4_mir_rvalue_call_return_lend_leaf_count(",
            "task v4_mir_rvalue_call_return_lend_leaf_projection_at(",
            "task v4_mir_rvalue_call_return_lend_leaf_route_guard_at(",
            "task v4_mir_rvalue_call_borrowed_source_arg_count_for_leaf(",
            "task v4_mir_rvalue_call_borrowed_source_payload_for_leaf(",
            "task v4_mir_rvalue_call_borrowed_source_arg_at_for_leaf(",
            "task v4_mir_rvalue_call_borrowed_source_projection_at_for_leaf(",
            "task v4_mir_rvalue_call_borrowed_source_route_guard_at_for_leaf(",
            "task v4_mir_callback_type_contains_lend(",
            "task v4_mir_check_callback_call_args(",
            "task v4_mir_reject_aggregate_lend_child(",
            "task v4_mir_reject_lend_bearing_call_generics(",
            "task v4_mir_check_fixed_array_repeated_literal(",
            "fixed-array repeat value must be Copy or Cloneable",
            "Meiya cannot substitute a lend-bearing type for a generic call yet",
            'v4_mir_reject_aggregate_lend_child(mir_id, body_id, "a maybe some()",',
            'v4_mir_reject_aggregate_lend_child(mir_id, body_id, "a result ok()",',
            'v4_mir_reject_aggregate_lend_child(mir_id, body_id, "a result err()",',
            '"a map", "map entry " + word_from_int(pair_idx) + " key"',
            '"a map", "map entry " + word_from_int(pair_idx) + " value"',
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
            "v4_borrowck_provenance_known_empty",
            'v4_borrowck_provenance_opaque = "opaque"',
            "v4_borrowck_provenance_new",
            "v4_borrowck_provenance_is_known",
            "v4_borrowck_provenance_mark_opaque",
            "task v4_borrowck_provenance_count(",
            "v4_borrowck_provenance_is_known_empty",
            "task v4_borrowck_provenance_source_row_at(",
            "task v4_borrowck_provenance_path_at(",
            "task v4_borrowck_provenance_route_guard_at(",
            "task v4_borrowck_provenance_contains_source(",
            "task v4_borrowck_provenance_origin_at(",
            "v4_borrowck_provenance_contains_path",
            "v4_borrowck_provenance_overlaps_path",
            "v4_borrowck_provenance_add_source",
            "task v4_borrowck_provenance_add_source_guarded(",
            "task v4_borrowck_provenance_union_into(",
            "task v4_borrowck_provenance_union_borrow_capable_call_args(",
            "task v4_borrowck_fill_return_call_lend_provenance(",
            "task v4_borrowck_rvalue_matches_route_guard_projected_at(",
            "task v4_borrowck_provenance_mark_known_empty(",
            "task v4_borrowck_call_has_known_lend_provenance(",
            "task v4_borrowck_projection_match_tail(",
            "task v4_borrowck_fill_param_lend_provenance(",
            "task v4_borrowck_return_source_contract_count(",
            "task v4_borrowck_rvalue_unique_holder_projection(",
            "Meiya cannot establish the origin of this returned aggregate loan",
            "Meiya refuses to return an aggregate loan of an owned value",
            "v4_borrowck_provenance_scratch_reset",
            "v4_borrowck_provenance_state_active_count",
            "v4_borrowck_provenance_source_active_count",
            "task v4_borrowck_provenance_integer_word(",
            "task v4_borrowck_provenance_integer_intern_count(",
            "task v4_borrowck_provenance_integer_intern_capacity(",
            "task v4_borrowck_path_canon_cache_count(",
            "task v4_borrowck_path_canon_cache_capacity(",
            "task v4_borrowck_path_canon_value_cache_count(",
            "task v4_borrowck_fill_holder_lend_provenance(",
            "task v4_borrowck_provenance_union_projected_into(",
            "v4_borrowck_provenance_memo_lookup",
            "v4_borrowck_provenance_memo_mark_ready",
            "v4_borrowck_provenance_memo_hit_count",
            "v4_borrowck_provenance_solver_dirty",
            "v4_borrowck_provenance_revision_value",
            "pilot v4_borrowck_fixed_point_rounds_by_file = 0",
            "pilot v4_borrowck_fixed_point_work_items_by_file = 0",
            "pilot v4_borrowck_provenance_solved_memo_active = 0",
            "pilot v4_borrowck_provenance_memo_body_heads = 0",
            "task v4_borrowck_provenance_memo_body_head(",
            "task v4_borrowck_provenance_memo_index_insert(",
            "v4_borrowck_provenance_scratch_store(v4_borrowck_provenance_worklist_queued, memo_id, \"false\")",
            "pilot v4_borrowck_provenance_dependency_sources = 0",
            "pilot v4_borrowck_provenance_dependency_dependents = 0",
            "pilot v4_borrowck_provenance_dependency_next = 0",
            "pilot v4_borrowck_provenance_dependency_heads = 0",
            "pilot v4_borrowck_provenance_dependency_tails = 0",
            "pilot v4_borrowck_provenance_worklist_memos = 0",
            "pilot v4_borrowck_provenance_source_fact_limit_value = 1024",
            "pilot v4_borrowck_provenance_path_byte_limit_value = 1024",
            "pilot v4_borrowck_provenance_memo_limit_value = 4096",
            "pilot v4_borrowck_provenance_dependency_limit_value = 16384",
            "pilot v4_borrowck_provenance_work_item_limit_value = 65536",
            "task v4_borrowck_provenance_discover_memos(",
            "task v4_borrowck_provenance_dependency_add(",
            "task v4_borrowck_provenance_worklist_enqueue(",
            "task v4_borrowck_provenance_worklist_enqueue_dependents(",
            "task v4_borrowck_provenance_run_fixed_point_phase(",
            "task v4_borrowck_provenance_solve_fixed_point(",
            "task v4_borrowck_provenance_mark_all_opaque(",
            "task v4_borrowck_provenance_trip_resource_limit(",
            "task v4_borrowck_store_provenance_telemetry(borrow_id: int)",
            "task v4_borrowck_provenance_fixed_point_rounds(borrow_id: int)",
            "task v4_borrowck_provenance_fixed_point_limit(borrow_id: int)",
            "task v4_borrowck_provenance_fixed_point_solve_count(borrow_id: int)",
            "task v4_borrowck_provenance_fixed_point_converged(borrow_id: int)",
            "task v4_borrowck_provenance_resource_exhausted(borrow_id: int)",
            "task v4_borrowck_provenance_fixed_point_work_items(borrow_id: int)",
            "task v4_borrowck_provenance_dependency_limit(",
            "task v4_borrowck_provenance_work_item_limit(",
            "task v4_borrowck_provenance_source_fact_limit(",
            "task v4_borrowck_provenance_path_byte_limit(",
            "task v4_borrowck_provenance_memo_limit(",
            "task v4_borrowck_restore_telemetry_slot(",
            "pilot v4_borrowck_source_provenance_ids = 0",
            "pilot v4_borrowck_source_paths = 0",
            "pilot v4_borrowck_source_origins = 0",
            "task v4_borrowck_return_call_lend_provenance(",
            "task v4_borrowck_return_lend_provenance(",
            "v4_borrowck_check_returned_lends",
            "v4_borrowck_check_stored_call_lends",
            "v4_borrowck_stored_call_return_holder",
            "v4_borrowck_holder_alias_from_stmt",
            "task v4_borrowck_collect_rvalue_holder_projections(",
            "v4_borrowck_rvalue_resolves_lend_source",
            "v4_borrowck_rvalue_returns_holder",
            "v4_ty_type_is_structurally_copy",
            "task v4_borrowck_repeat_path_slot_index(",
            "task v4_borrowck_repeat_projection_candidates(",
            "v4_mir_rvalue_capture_borrow_mut",
            "v4_borrowck_projected_alias_ambiguous",
            "task v4_borrowck_repeat_projection_scan_help(",
            "v4_borrowck_holder_state",
            "v4_borrowck_projected_alias_ambiguous",
            "task v4_borrowck_block_reaches(",
            "v4_borrowck_holder_reaches_stmt_without_rebind",
            "v4_borrowck_holder_worklist_contains",
            "v4_borrowck_call_lends_source",
            "v4_borrowck_explicit_loan_holder",
            "v4_borrowck_holder_used_at_or_after_write",
            "v4_borrowck_explicit_loan_live_at_write",
            "v4_borrowck_explicit_loan_live_at_move",
            "v4_mir_rvalue_call_borrowed_source_arg_count",
            "v4_mir_rvalue_call_borrowed_source_arg_at",
            'v4_borrowck_path_return_loan = "ReturnLoan"',
            'v4_borrowck_path_return_loan_mut = "ReturnLoanMut"',
            'pilot v4_borrowck_snapshot_legacy_format = "freak-borrowck-snapshot-v1"',
            'pilot v4_borrowck_snapshot_format = "freak-borrowck-snapshot-v2"',
            "task v4_borrowck_snapshot_format_supported(",
            "task v4_borrowck_repeat_fill_loan_live_at_write(",
            "task v4_borrowck_snapshot_payload_format(",
            "format == v4_borrowck_snapshot_format and v4_borrowck_snapshot_field_count(line) < 12",
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
        if "v4_borrowck_return_has_loop_carried_rebind" in borrowck_src:
            contract_region_missing.append(
                "freak_borrowck retains stale blanket loop rejection: "
                "v4_borrowck_return_has_loop_carried_rebind"
            )
        for stale_recursive_helper in (
            "v4_borrowck_block_reaches_seen",
            "v4_borrowck_holder_reaches_stmt_without_rebind_seen",
            "v4_borrowck_hidden_holder_reaches_access_seen",
            "v4_borrowck_holder_used_at_or_after_write_seen",
        ):
            if stale_recursive_helper in borrowck_src:
                contract_region_missing.append(
                    "freak_borrowck retains recursive CFG/holder traversal: "
                    + stale_recursive_helper
                )
    else:
        contract_region_missing.append("freak_borrowck/src/lib.fk missing")
    if v4_runtime_c_return.exists():
        runtime_src = v4_runtime_c_return.read_text(encoding="utf-8")
        for needle in (
            "freak_array_reserve_handle",
            "freak_dyn_array*)realloc(",
            "static void freak_array_reserve_elements(",
            "old_capacity > INT64_MAX / 2",
            "(uint64_t)new_capacity > SIZE_MAX / sizeof(freak_word)",
        ):
            if needle not in runtime_src:
                contract_region_missing.append(f"freak_runtime.c: {needle}")
        if "#define FREAK_MAX_ARRAYS 256" in runtime_src:
            contract_region_missing.append("freak_runtime.c retains fixed 256-array handle ceiling")
    else:
        contract_region_missing.append("freakc/runtime/freak_runtime.c missing")
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
            v4_tests_return / "contract_region_body_derived_probe_smoke.fk",
            (
                "task field_rebind_agg<'a>(lend 'a fleet: Fleet, view: View<'a>)",
                "view.lead = lend fleet.ship",
                "task conditional_field_rebind<'a>(lend 'a fleet: Fleet, view: View<'a>",
                "task loop_param_rebind<'a>(lend 'a fleet: Fleet, view: View<'a>",
                "task branch_join<'a>(lend 'a fleet: Fleet, lend 'a other: Ship",
                'v4_body_probe_emit_sources("body-probe-field-rebind"',
                'v4_body_probe_emit_sources("body-probe-inner-rebind"',
                'v4_body_probe_emit_sources("body-probe-branch-join"',
                'v4_body_probe_emit_sources("body-probe-conditional-field-rebind"',
                'v4_body_probe_emit_sources("body-probe-loop-param-rebind"',
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
                "repeat until generic_id >= 20",
                "repeat until generic_id >= 28",
                "v4_ty_signature_lifetime_outlives",
                "v4_ty_borrowed_return_source_cache_build_count()",
                "contract-region-relation-stress-fibonacci-transitive=",
                "contract-region-relation-stress-chain-reachable=",
                "contract-region-relation-stress-cycle-right-left=",
                "contract-region-relation-stress-extern-gated=",
                "contract-region-relation-stress-source-cache-stable=",
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
            v4_tests_return / "contract_region_loop_fixed_point_smoke.fk",
            (
                "task direct_loop<'a>(lend 'a first: Ship, lend 'a second: Ship",
                "task alias_cycle<'a>(lend 'a first: Ship, lend 'a second: Ship",
                "task dedup_loop<'a>(lend 'a source: Ship",
                "task long_alias_ring<'a>(",
                "repeat until ring_id >= 12",
                "view = lend second",
                "view = relay",
                "relay = view",
                "v4_borrowck_provenance_fixed_point_converged(v4_contract_region_loop_fixed_point_borrow)",
                "v4_borrowck_snapshot_restore(",
                "contract-region-loop-fixed-point-direct-status=",
                "contract-region-loop-fixed-point-alias-source-count=",
                "contract-region-loop-fixed-point-dedup-source-count=",
                "contract-region-loop-fixed-point-restored-alias-source-count=",
            ),
        ),
        (
            v4_tests_return / "contract_region_many_root_smoke.fk",
            (
                "pilot v4_contract_region_many_root_count = 256",
                "v4_borrowck_provenance_fixed_point_solve_count(",
                "v4_borrowck_provenance_fixed_point_work_items(",
                "v4_borrowck_return_lend_provenance(",
                "v4_borrowck_store_provenance_telemetry(",
                "contract-region-many-root-results-clean=",
                "contract-region-many-root-resource-exhausted=",
                "contract-region-many-root-linear-work=",
                "contract-region-many-root-work-bounded=",
            ),
        ),
        (
            v4_tests_return / "contract_region_loop_fail_closed_smoke.fk",
            (
                "v4_borrowck_provenance_round_limit_test_override = 1",
                "v4_borrowck_provenance_source_fact_limit_value = 1",
                "v4_borrowck_provenance_path_byte_limit_value = 8",
                "v4_borrowck_provenance_dependency_limit_value = 1",
                "v4_borrowck_provenance_work_item_limit_value = 1",
                "v4_borrowck_provenance_resource_exhausted(v4_contract_region_loop_fail_closed_round_borrow)",
                "v4_borrowck_provenance_scratch_reset()",
                "v4_borrowck_snapshot_restore(",
                "contract-region-loop-fail-closed-snapshot-poisoned=",
                "contract-region-loop-fail-closed-round-cap-hit=",
                "contract-region-loop-fail-closed-budget-resource-exhausted=",
                "contract-region-loop-fail-closed-path-resource-exhausted=",
                "contract-region-loop-fail-closed-dependency-resource-exhausted=",
                "contract-region-loop-fail-closed-dependency-edges-bounded=",
                "contract-region-loop-fail-closed-work-resource-exhausted=",
                "contract-region-loop-fail-closed-work-queue-bounded=",
                "contract-region-loop-fail-closed-restored-round-status=",
                "contract-region-loop-fail-closed-restored-round-converged=",
                "contract-region-loop-fail-closed-restored-budget-resource-exhausted=",
                "freak-borrowck-snapshot-v2|files=1|results=0|paths=0|diagnostics=0",
                "freak-borrowck-snapshot-v1|files=1|results=0|paths=0|diagnostics=0",
                "contract-region-loop-fail-closed-truncated-v2-rejected=",
                "contract-region-loop-fail-closed-legacy-v1-imported=",
                "contract-region-loop-fail-closed-legacy-v1-restored=",
                "contract-region-loop-fail-closed-legacy-v1-converged=",
            ),
        ),
        (
            v4_tests_return / "contract_region_loop_dependency_stress_smoke.fk",
            (
                "task long_holder_chain<'a>(lend 'a source: Ship)",
                "repeat until link_id > 48",
                'src = src + "    give back view48\\n"',
                "v4_borrowck_provenance_memo_active_count()",
                "v4_borrowck_provenance_fixed_point_rounds(v4_contract_region_loop_dependency_stress_borrow)",
                "v4_borrowck_provenance_resource_exhausted(v4_contract_region_loop_dependency_stress_borrow)",
                "v4_borrowck_provenance_fixed_point_work_items(v4_contract_region_loop_dependency_stress_borrow)",
                "contract-region-loop-dependency-stress-memo-depth-proven=",
                "contract-region-loop-dependency-stress-rounds-bounded=",
                "contract-region-loop-dependency-stress-work-bounded=",
            ),
        ),
        (
            v4_tests_return / "contract_region_cfg_worklist_stress_smoke.fk",
            (
                "repeat until branch_id >= 64",
                "v4_borrowck_block_reaches(",
                "v4_borrowck_block_can_cycle(",
                "v4_borrowck_provenance_fixed_point_work_items(",
                "contract-region-cfg-worklist-stress-forward-reachable=",
                "contract-region-cfg-worklist-stress-reverse-unreachable=",
                "contract-region-cfg-worklist-stress-entry-acyclic=",
                "contract-region-cfg-worklist-stress-work-bounded=",
            ),
        ),
        (
            v4_tests_return / "contract_region_loop_query_invalidation_smoke.fk",
            (
                'v4_contract_region_loop_query_source("second")',
                'v4_contract_region_loop_query_source("first ")',
                'v4_lsp_handle_text_request("textDocument/didChange"',
                "v4_unit_snapshot_diff(",
                "v4_unit_snapshot_health_append_diff(",
                "v4_unit_snapshot_restore(",
                "contract-region-loop-query-all-18-invalidations-positive=",
                "contract-region-loop-query-invalidation-matches-diff=",
                "contract-region-loop-query-signature-stable=",
                "contract-region-loop-query-all-18-recomputations-positive=",
                "contract-region-loop-query-restored-source-count=",
                "contract-region-loop-query-restored-editor-coherent=",
            ),
        ),
        (
            v4_tests_return / "contract_region_aggregate_boundary_smoke.fk",
            (
                "task tuple_pass<'a,'b>",
                "task same_lifetime_pass<'a>",
                "task aggregate_outlives<'short,'long: 'short>",
                "task projected_tuple<'a>(lend 'a fleet: Fleet)",
                "task same_lifetime_first_live(first: Ship, second: Ship)",
                "task array_sibling_live(first: Ship, second: Ship)",
                "task empty_array_pass<'a>",
                "task empty_array_call(first: Ship)",
                "aggregate-boundary-empty-call-provenance-known-empty=",
                "v4_borrowck_provenance_is_known_empty(",
                "task array_pass<'a>",
                "task shape_pass<'a,'b>",
                "v4_ty_signature_return_lend_leaf_count(",
                "v4_ty_signature_return_lend_source_count(",
                "v4_ty_signature_return_lend_source_projection_at(",
                "v4_mir_rvalue_call_borrowed_source_projection_at_for_leaf(",
                "aggregate-boundary-tuple-sibling-dead=",
                "aggregate-boundary-shape-sibling-dead=",
                "aggregate-boundary-array-owner-live=",
                "aggregate-boundary-same-source0-count=",
                "aggregate-boundary-projected-tuple-source-count=",
            ),
        ),
        (
            v4_tests_return / "contract_region_aggregate_route_boundary_smoke.fk",
            (
                "task route_owner_live(first: Ship)",
                "task route_empty_clean(first: Ship)",
                "task shape_to_route<'a>(views: SingleView<'a>)",
                "task shape_to_route_forward<'a>(views: SingleView<'a>)",
                "task shape_to_route_roundtrip(first: Ship)",
                "task nested_empty<'a>",
                "task route_pass<'a>",
                "task nested_owned_escape<'a>",
                "task aggregate_owned_escape<'a>",
                "v4_ty_signature_return_lend_source_route_guard_at(",
                "aggregate-boundary-owned-escape=",
                "aggregate-boundary-nested-owned-escape=",
                "aggregate-boundary-route-source-guard=",
                "aggregate-boundary-nested-route-guard=",
            ),
        ),
        (
            v4_tests_return / "contract_region_aggregate_edge_smoke.fk",
            (
                "task nested_array_pass<'a>",
                "BASE + WIDTH",
                "task nested_const_roundtrip(first: Ship)",
                "aggregate-edge-nested-const-source-projection=",
                "task empty_array_generic_call(first: Ship)",
                "aggregate-edge-empty-generic-type=",
                "aggregate-edge-empty-array-stores-lend=",
                "aggregate-edge-empty-generic-diagnostic=",
                "task select_ship<'a>",
                "task different_target_sibling_dead(first: Ship, other: Cat)",
                "task generic_select<'a,T,U>",
                "task generic_target_sibling_dead(first: Ship, other: Cat)",
                "task projected_call_sibling_dead(first: Ship, second: Ship, other: Cat)",
                "task projected_call_owner_live(first: Ship, second: Ship, other: Cat)",
                "task tuple_scalar_pass<'a>",
                "task returned_call_leaf_rebind(first: Ship, second: Ship)",
                "task projected_holder<'a>",
                "task projected_scalar_roundtrip(fleet: Fleet)",
                "aggregate-edge-returned-call-leaf-holder=",
                "aggregate-edge-projected-scalar-source-count=",
                "aggregate-edge-generic-target-source-count=",
                "aggregate-edge-projected-call-sibling-dead=",
                "aggregate-edge-different-target-source-count=",
                "task duplicate_rebind_all(first: Ship, second: Ship)",
                "task duplicate_rebind_one(first: Ship, second: Ship)",
                "task duplicate_pass<'a>",
                "task duplicate_call_rebind_all(first: Ship, second: Ship)",
                "task duplicate_projected_pass<'a>",
                "task duplicate_call_rebind_one(first: Ship, second: Ship)",
                "task duplicate_projected_call_rebind_all(first: Ship, second: Ship)",
                "task nested_duplicate_call_rebind_all(first: Ship, second: Ship)",
                "aggregate-edge-duplicate-projection-count=",
                "aggregate-edge-duplicate-rebind-all=",
                "aggregate-edge-duplicate-call-projection-count=",
                "aggregate-edge-duplicate-call-rebind-all=",
                "aggregate-edge-call-projection-relation-limit=",
                "v4_ty_type_stores_lend(",
                "Meiya cannot substitute a lend-bearing type for a generic call yet",
            ),
        ),
        (
            v4_tests_return / "contract_region_aggregate_budget_smoke.fk",
            (
                "repeat until v4_aggregate_budget_depth >= 9",
                "repeat until v4_aggregate_budget_relation >= 257",
                "shape Recursive<'a>",
                "v4_ty_signature_return_lend_leaf_count(",
                "v4_ty_return_lend_source_payload_append_bounded(",
                "aggregate-budget-fanout-opaque=",
                "aggregate-budget-source-cutoff-atomic=",
            ),
        ),
        (
            v4_tests_return / "contract_region_aggregate_negative_smoke.fk",
            (
                "task mutable_upgrade<'a>",
                "task mismatched_carrier(first: Ship)",
                "v4_mir_rvalue_call_borrowed_source_arg_count_for_leaf(",
                "aggregate-negative-upgrade-source-count=",
                "aggregate-negative-mismatch-map-count=",
                "aggregate-negative-mismatch-diagnostic=",
            ),
        ),
        (
            v4_tests_return / "contract_region_fixed_aggregate_smoke.fk",
            (
                "task tuple_sibling_dead(first: Ship, second: Ship)",
                "task tuple_left_live(first: Ship, second: Ship)",
                "pilot views: [lend mut Ship;2] = [lend mut first, lend mut second]",
                "Pair<lend mut Ship,lend mut Ship>",
                "task explicit_mut_alias(first: Ship)",
                "task direct_local<'a>(lend 'a first: Ship)",
                "task repeat_mut_one(first: Ship)",
                "task repeat_immutable_outer(first: Ship)",
                "pilot copies = [shared; 2]",
                "task repeat_owned_sibling(first: Ship, owned: Owned)",
                "task repeat_cloneable(value: CloneOwned)",
                "task repeat_nominal_copy(value: NominalCopy)",
                "impl Copy for NominalCopy",
                "impl Cloneable for CloneOwned",
                "task repeat_shared_rebind_all(first: Ship, second: Ship)",
                "task repeat_shared_rebind_one(first: Ship, second: Ship)",
                "task repeat_nested_sibling_dead(first: Ship, second: Ship)",
                "task repeat_nested_container_rebind(first: Ship, second: Ship)",
                "holder.0[0] = lend second",
                "task repeat_structural_copy(first: Ship, second: Ship)",
                "task repeat_shared_partial_rebind_257(first: Ship, second: Ship)",
                "task repeat_shared_dead_256(first: Ship)",
                "task repeat_shared_dead_257(first: Ship)",
                "task empty_array_generic_call(first: Ship)",
                "task empty_array_stored_call(first: Ship)",
                "pilot copied: [lend Ship;0] = identity(empty)",
                "fixed-aggregate-empty-array-stores-lend=",
                "fixed-aggregate-empty-array-generic-diagnostic=",
                "fixed-aggregate-empty-array-stored-call=",
                "v4_ty_type_stores_lend(",
                "Meiya cannot substitute a lend-bearing type for a generic call yet",
                "fixed-aggregate-repeat-copy-diagnostic=",
                "fixed-aggregate-repeat-copy-diagnostic-count=",
                "right: lend mut second, left: lend mut first",
                "Stored<lend Ship,lend Ship>::Hold",
                "task route_pattern_capture_keeps_loan(first: Ship)",
                "Stored<lend mut Ship,int>::Hold",
                "pilot views: [lend Ship;2] = [lend first; 2]",
                "pilot views: [lend mut Ship;2] = [lend mut first; 2]",
                "task duplicate_shared_rebind_releases(first: Ship, second: Ship)",
                "views.1 = lend mut third",
                "views.0 = lend mut third",
                'v4_borrowck_text_cached("contract-region-fixed-aggregate.fk"',
                "task loop_rebind_before_backedge(first: Ship, second: Ship, sibling: Ship)",
                "holder.0 = lend mut first",
                "task loop_sibling_survives(first: Ship, second: Ship, third: Ship)",
                "task dynamic_index_rebind<'a,'b>",
                "slots[index] = lend second",
                "task dynamic_index_preserves_old(",
                "task dynamic_index_includes_new(",
                "task repeat_mut_zero(",
                "pilot slots: [lend mut Ship;0] = [lend mut first; 0]",
                "task mutate_through_stored(first: Ship)",
                "views.0.hp = 19",
                "task immutable_outer_lend(first: Ship)",
                "shared.left.hp = 20",
                "copy.left.hp = 21",
                "task closure_capture_keeps_loan(first: Ship)",
                "task wrapped_closure_call_rejected(first: Ship)",
                "task empty_closure_repeat_clean(first: Ship)",
                "task zero_length_closure_call_clean(first: Ship)",
                "task dynamic_closure_call_storage_rejected(first: Ship)",
                "task wrap<C>(value: C) -> (C,int)",
                "task empty_wrap<C>(value: C) -> [C;0]",
                "task list_wrap<C>(value: C) -> List<C>",
                "pilot wrapped = wrap(reader)",
                "pilot readers = [reader; 0]",
                "pilot reader = |_| => holder.0.hp",
                "task closure_forwarded_capture_keeps_loan(first: Ship)",
                "pilot forwarded = identity(reader)",
                "task dynamic_closure_storage_rejected(first: Ship)",
                "pilot readers = [reader]",
                "pilot extracted = readers[0]",
                "task dynamic_forwarded_closure_storage_rejected(first: Ship)",
                "task projected_closure_assignment_storage_rejected(first: Ship)",
                "task forwarded_closure_rebind_storage_rejected(first: Ship)",
                "task mixed_lend_closure_storage_rejected(first: Ship, second: Ship)",
                "task plain_local_cycle_clean()",
                "task dynamic_closure_conditional_rebind(first: Ship, flag: bool)",
                "reader = |_| => 0",
                "task fixed_closure_tuple_storage_rejected(first: Ship)",
                "task fixed_closure_repeat_storage_rejected(first: Ship)",
                "task dynamic_wrapped_closure_storage_rejected(first: Ship)",
                "task dynamic_nested_move_closure_storage_rejected(first: Ship)",
                "Meiya cannot store a loan-capturing closure inside fixed aggregate storage yet",
                "task mutable_lend_projection_protects_replacement(first: Ship, second: Ship)",
                "task mutable_lend_projection_releases_replaced(first: Ship, second: Ship)",
                "access.0 = lend mut second",
                "fixed-aggregate-mutable-lend-projection-releases-replaced=",
                "task returned_call_owner_live(first: Ship)",
                "task returned_call_duplicate_mut(first: Ship)",
                "relay_mut(lend mut first)",
                "fixed-aggregate-closure-capture-keeps-loan=",
                "fixed-aggregate-wrapped-closure-call-rejected=",
                "fixed-aggregate-empty-closure-repeat-clean=",
                "fixed-aggregate-zero-length-closure-call-clean=",
                "fixed-aggregate-dynamic-closure-call-storage-rejected=",
                "fixed-aggregate-dynamic-closure-storage-diagnostic=",
                "fixed-aggregate-repeat-nominal-copy=",
                "fixed-aggregate-repeat-shared-partial-rebind-257=",
                "fixed-aggregate-duplicate-shared-rebind-releases=",
                "fixed-aggregate-projected-closure-assignment-storage-rejected=",
                "fixed-aggregate-dynamic-closure-storage-diagnostic-count=",
                "fixed-aggregate-fixed-closure-storage-diagnostic-count=",
                "fixed-aggregate-dynamic-forwarded-closure-storage-rejected=",
                "fixed-aggregate-forwarded-closure-rebind-storage-rejected=",
                "fixed-aggregate-mixed-lend-closure-storage-rejected=",
                "fixed-aggregate-plain-local-cycle=",
                "fixed-aggregate-loop-sibling-survives=",
                "fixed-aggregate-dynamic-index-rebind=",
                "fixed-aggregate-dynamic-index-preserves-old=",
                "fixed-aggregate-dynamic-index-includes-new=",
                "fixed-aggregate-repeat-mut-zero=",
                "v4_borrowck_path_write_definitely_covers(",
                "v4_borrowck_path_write_may_bind(",
                "fixed-aggregate-descendant-write-may-bind=",
                "fixed-aggregate-immutable-outer-lend=",
                "fixed-aggregate-repeat-mut-zero-holder=",
                "v4_mir_rvalue_aggregate_child_projection(",
                "v4_mir_rvalue_aggregate_child_for_projection(",
                "v4_ty_type_lend_storage_class(",
                "v4_borrowck_explicit_loan_holder(",
                "fixed-aggregate-tuple-sibling-dead=",
                "fixed-aggregate-shape-child0-projection=",
                "fixed-aggregate-route-child0-projection=",
                "fixed-aggregate-route-left-holder=",
                "fixed-aggregate-route-pattern-left-type=",
                "fixed-aggregate-direct-holder=",
                "fixed-aggregate-class-list=",
                "fixed-aggregate-compact-lend-mut=",
                "fixed-aggregate-compact-lend-lifetime=",
            ),
        ),
        (
            v4_tests_return / "contract_region_repeat_projection_smoke.fk",
            (
                "task repeat_shared_rebind_257(first: Ship, second: Ship)",
                "task repeat_shared_partial_rebind_1025(first: Ship, second: Ship)",
                "task repeat_shared_extracted_alias_rebind_256(first: Ship, second: Ship)",
                "task repeat_shared_capture_live(first: Ship)",
                "pilot replacement = lend second",
                "pilot reader = |_| => views[0].hp",
                "repeat-projection-rebind-257=",
                "repeat-projection-partial-rebind-1025=",
                "repeat-projection-extracted-alias-rebind-256=",
                "repeat-projection-capture-live=",
            ),
        ),
        (
            v4_tests_return / "contract_region_recursive_wrapper_smoke.fk",
            (
                "shape Node<'a>",
                "next: List<Node<'a>>",
                "v4_ty_type_lend_storage_class(",
                "recursive-wrapper-storage-class=",
                "recursive-wrapper-diagnostic=",
            ),
        ),
        (
            v4_tests_return / "contract_region_conditional_alias_smoke.fk",
            (
                "task conditional_alias_targets(first: Ship, second: Ship, third: Ship, choose_right: bool)",
                "access = lend mut right",
                "access.0 = lend mut third",
                "pilot forwarded = access",
                "forwarded.0 = lend mut second",
                "task transferred_alias_long_release(first: Ship, second: Ship)",
                "relay19.0 = lend mut second",
                "task transferred_alias_source_rebind(first: Ship, second: Ship, third: Ship)",
                "access = lend mut other",
                "forwarded.0 = lend mut third",
                "conditional-alias-borrow-diagnostics=",
                "conditional-alias-status=",
                "transferred-alias-status=",
                "transferred-alias-long-release-status=",
                "transferred-alias-source-rebind-status=",
            ),
        ),
        (
            v4_tests_return / "contract_region_fixed_aggregate_query_smoke.fk",
            (
                'v4_fixed_aggregate_query_source("left")',
                'v4_fixed_aggregate_query_source("rght")',
                "v4_fixed_aggregate_query_report_positive(",
                "v4_fixed_aggregate_query_reports_match(",
                "v4_fixed_aggregate_query_shape_facts(",
                '"views.left"',
                '"views.rght"',
                "v4_semantic_at_text_cached(",
                "v4_hover_text_cached(",
                "v4_definition_at_text_cached(",
                "v4_document_symbols_text_cached(",
                "v4_completion_text_cached(",
                'v4_lsp_handle_text_request("textDocument/didChange"',
                "v4_unit_snapshot_diff(",
                "v4_unit_snapshot_health_append_diff(",
                "v4_unit_snapshot_restore(",
                "fixed-aggregate-query-all-18-invalidations-positive=",
                "fixed-aggregate-query-invalidation-matches-diff=",
                "fixed-aggregate-query-after-shape-facts=",
                "fixed-aggregate-query-snapshot-restored=",
                "fixed-aggregate-query-restored-editor-coherent=",
            ),
        ),
        (
            v4_tests_return / "contract_region_storage_negative_smoke.fk",
            (
                "pilot view = choose(lend first, lend second, take_first)",
                "pilot views = (choose(lend first, lend second, take_first), 7)",
                "pilot views: [lend Ship; 1] = [choose(lend first, lend second, take_first)]",
                "pilot views = [choose(lend first, lend second, take_first); 2]",
                "pilot views = [choose(lend first, lend second, take_first)]",
                "pilot view = Box ",
                "pilot view = Stored::Hold ",
                "pilot view: maybe<lend Ship> = some(choose(",
                "pilot view: result<lend Ship,word> = ok(choose(",
                "pilot view: result<int,lend Ship> = err(choose(",
                "pilot views: Map<lend Ship,int>",
                "pilot views: Map<word,lend Ship>",
                "task named_signature_escape<'a>(value: maybe<result<Map<word,lend 'a Ship>,int>>)",
                "task elided_signature_escape(value: maybe<result<Map<word,lend Ship>,int>>)",
                "contract-region-storage-ty-diagnostics-exact-four=",
                "contract-region-storage-mir-diagnostics-exact-ten=",
                "contract-region-storage-local-holder-status=",
                "contract-region-storage-fixed-array-literal-status=",
                "contract-region-storage-fixed-array-repeat-status=",
                "contract-region-storage-list-literal-status=",
                "contract-region-storage-shape-value-status=",
                "contract-region-storage-route-payload-status=",
                "contract-region-storage-some-status=",
                "contract-region-storage-ok-status=",
                "contract-region-storage-err-status=",
                "contract-region-storage-map-key-status=",
                "contract-region-storage-map-value-status=",
                "contract-region-storage-borrow-diagnostics-exact-ten=",
                "contract-region-storage-borrow-diags-match-mir=",
                "v4_contract_region_storage_negative_deep_lend_free_type()",
                "v4_contract_region_storage_negative_deep_wrapper_type()",
                "v4_ty_type_may_store_lend(ty_id, type_text)",
                "contract-region-storage-deep-class=",
                "contract-region-storage-deep-confirmed-lend=",
                "contract-region-storage-deep-wrapper-class=",
                "contract-region-storage-deep-wrapper-confirmed-lend=",
                "contract-region-storage-deep-wrapper-may-store-lend=",
                "contract-region-storage-deep-diagnostic=",
            ),
        ),
        (
            v4_tests_return / "contract_region_generic_lend_escape_smoke.fk",
            (
                "task wrap<T>(value: T) -> maybe<T>",
                "pilot wrapped = wrap(lend value)",
                "pilot direct = identity(lend value)",
                "Meiya cannot substitute a lend-bearing type for a generic call yet",
                "contract-region-generic-lend-escape-meiya-count=",
                "impl Direct<'a>",
                "impl Add for Box<T>",
                "pilot hidden_direct_instance = stored.keep()",
                "pilot hidden_operator = wrapped + wrapped",
                "contract-region-owner-generic-negative-method-boundary-count=",
                "Meiya cannot carry a lend-bearing aggregate across a method call yet",
            ),
        ),
        (
            v4_tests_return / "mir_snapshot_smoke.fk",
            (
                "v4_mir_snapshot_direct_restore_generation_before",
                "mir-snapshot-direct-restore-generation-advanced=",
                "v4_mir_snapshot_lsp_restore_generation_before",
                "v4_borrowck_provenance_scratch_generation()",
                "mir-snapshot-lsp-restore-generation-advanced=",
            ),
        ),
        (
            v4_tests_return / "contract_region_source_cache_churn_smoke.fk",
            (
                "v4_ty_borrowed_return_source_cache_capacity()",
                "v4_ty_borrowed_return_source_cache_entry_count()",
                "v4_ty_borrowed_return_source_cache_store(",
                "contract-region-source-cache-churn-evicted-first-rebuild-delta=",
                "contract-region-source-cache-churn-known-empty-cached=",
                "contract-region-source-cache-churn-signature-restore-rebuild-delta=",
                "contract-region-source-cache-churn-file-restore-rebuild-delta=",
            ),
        ),
        (
            v4_tests_return / "contract_region_boundary_negative_smoke.fk",
            (
                "doctrine Selector<'a>",
                "task callback_boundary<'a>(cb: task(left: lend 'a Ship, right: lend 'a Ship) -> lend 'a Ship)",
                "task static_boundary(lend 'static value: Ship) -> lend 'static Ship",
                "task v4_contract_region_boundary_negative_emit_diag(ty_id: int, diag_id: int) -> void {",
                'say "contract-region-boundary-negative-diagnostics-exact-three="',
                "v4_contract_region_boundary_negative_emit_diag(v4_contract_region_boundary_negative_ty, 2)",
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
                'say "contract-region-forwarding-closure-coverage=unsupported-no-borrowed-closure-contract"',
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
                "v4_semantic_restore_fact_slot(",
                "v4_hover_restore_slot(",
                "v4_definition_restore_slot(",
                "contract-region-editor-poison-before-restore-all=",
                "contract-region-editor-restored-semantic-facts-exact=",
                "contract-region-editor-document-query-family-valid=",
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
                "contract-region-query-query-invalidated=",
                "contract-region-query-core-invalidated=",
                "contract-region-query-editor-invalidated=",
                "contract-region-query-all-18-invalidations-positive=",
                "contract-region-query-document-symbols-invalidated=",
                "contract-region-query-completion-invalidated=",
                "contract-region-query-document-symbols-recomputed=",
                "contract-region-query-completion-recomputed=",
                "contract-region-query-all-18-recomputations-positive=",
                "contract-region-query-after-source-count=",
                "contract-region-query-after-bound-definition-matches-alt-binder=",
            ),
        ),
        (
            v4_tests_return / "contract_region_projected_holder_smoke.fk",
            (
                "give back lend view.ship",
                "pilot second = first",
                "give back lend second.ship",
                "contract-region-projected-holder-source=",
                "contract-region-projected-holder-chain-source=",
                "contract-region-projected-holder-cycle-source-count=",
                "contract-region-projected-holder-cycle-source=",
                "task tuple_holder_reborrow<'a>",
                "task array_holder_reborrow<'a>",
                "task shape_holder_reborrow<'a>",
                "give back lend slots.0.ship",
                "give back lend slots[0].ship",
                "give back lend stored.view.ship",
                "contract-region-projected-holder-tuple-source=",
                "contract-region-projected-holder-array-source=",
                "contract-region-projected-holder-shape-source=",
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
                "contract-region-liveness-snapshot-poisoned-before-restore=",
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
                "task v4_contract_region_elided_query_source(second_mode: word, loop_source: word) -> word {",
                'src = src + "task choose(lend first: Ship, " + second_mode + "second: Ship) -> lend Ship {\\n"',
                'src = src + "task loop_choose(lend first: Ship, " + second_mode + "second: Ship, ready: bool) -> lend Ship {\\n"',
                'src = src + "        view = lend " + loop_source + "\\n"',
                'v4_lsp_handle_text_request("textDocument/didChange", v4_contract_region_elided_query_path, v4_contract_region_elided_query_after, 0)',
                "contract-region-elided-query-before-loop-source-count=",
                "contract-region-elided-query-before-loop-converged=",
                "contract-region-elided-query-before-source-count=",
                "contract-region-elided-query-before-call-source-count=",
                "contract-region-elided-query-ty-restore-poisoned=",
                "contract-region-elided-query-ty-restore-cache-builds-added=",
                "contract-region-elided-query-query-invalidations-added=",
                "contract-region-elided-query-core-invalidations-added=",
                "contract-region-elided-query-editor-invalidations-added=",
                "contract-region-elided-query-all-18-invalidations-positive=",
                "contract-region-elided-query-ty-invalidations-added=",
                "contract-region-elided-query-document-symbols-invalidations-added=",
                "contract-region-elided-query-completion-invalidations-added=",
                "contract-region-elided-query-definition-recomputations-added=",
                "contract-region-elided-query-document-symbols-recomputations-added=",
                "contract-region-elided-query-completion-recomputations-added=",
                "contract-region-elided-query-all-18-recomputations-positive=",
                "contract-region-elided-query-after-source-count=",
                "contract-region-elided-query-after-call-source-count=",
                "contract-region-elided-query-after-loop-source-count=",
                "contract-region-elided-query-after-loop-converged=",
                "contract-region-elided-query-after-semantic=",
                "contract-region-elided-query-after-definition=",
            ),
        ),
        (
            v4_tests_return / "contract_region_resource_smoke.fk",
            (
                "repeat until level > 12",
                "v4_borrowck_check_mir(0, v4_contract_region_resource_mir)",
                "v4_borrowck_provenance_integer_intern_count()",
                "v4_borrowck_path_canon_cache_count()",
                "v4_borrowck_provenance_integer_intern_capacity()",
                "v4_borrowck_path_canon_value_cache_count()",
                "contract-region-resource-cache-evictions-observed=",
                "contract-region-resource-steady-state-evictions-stable=",
                "contract-region-resource-hot-reuse-stable=",
                "contract-region-resource-runtime-array-growth=",
                "contract-region-resource-generation-sequence=",
                "contract-region-resource-memo-hits=",
                "contract-region-resource-capacities-reused=",
                "contract-region-resource-integer-intern-count-stable=",
                "contract-region-resource-canonical-path-cache-count-stable=",
                "contract-region-resource-no-historical-growth=",
                "contract-region-resource-loop-semantics-stable=",
                "contract-region-resource-fixed-point-rounds-bounded=",
                "contract-region-resource-fixed-point-work-bounded=",
                "contract-region-resource-fixed-point-telemetry-stable=",
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
        "mir_snapshot_smoke.fk": (
            "mir-snapshot-direct-restore-generation-advanced=true",
            "mir-snapshot-lsp-restore-generation-advanced=true",
        ),
        "ty_snapshot_smoke.fk": (
            "ty-restore-malformed-rejected=true",
            "ty-restore-malformed-atomic=true",
            "ty-restore-extra-visible-before=true",
            "ty-restore-active-files-exact=true",
            "ty-restore-extra-file-hidden=true",
            "ty-restore-extra-children-hidden=true",
            "ty-restore-retained-handles-reused=true",
            "ty-restore-retained-capacity-stable=true",
            "ty-restore-top-slot-reused=true",
            "ty-restore-top-capacity-stable=true",
            "ty-restore-repeat-no-growth=true",
        ),
        "dyn_doctrine_ty_smoke.fk": (
            "dyn-ty-prelude-shared-carrier=true",
            "dyn-ty-prelude-weak-carrier=true",
            "dyn-ty-shadowed-shared-carrier=false",
            "dyn-ty-shadowed-weak-carrier=false",
            "dyn-ty-shadowed-shared-coerces=false",
            "dyn-ty-shadowed-weak-coerces=false",
        ),
        "query_snapshot_confirm_smoke.fk": (
            "query-confirm-contract|case=two-source-core-ids-blocked|ok=1",
        ),
        "document_symbols_snapshot_smoke.fk": (
            "document-symbols-snapshot-exact-restore=true",
            "document-symbols-snapshot-stale-child-hidden=true",
            "document-symbols-snapshot-child-first-atomic=true",
            "document-symbols-snapshot-duplicate-child-atomic=true",
            "document-symbols-snapshot-declared-count-atomic=true",
        ),
        "completion_snapshot_smoke.fk": (
            "completion-snapshot-exact-restore=true",
            "completion-snapshot-stale-child-hidden=true",
            "completion-snapshot-child-first-atomic=true",
            "completion-snapshot-duplicate-child-atomic=true",
            "completion-snapshot-declared-count-atomic=true",
        ),
        "contract_region_aggregate_smoke.fk": (
            "contract-region-aggregate-branch-status=blocked",
            "contract-region-aggregate-branch-tuple-child-count=2",
            "contract-region-aggregate-branch-mutation-conflicts=1",
            "contract-region-aggregate-branch-final-use-visible=true",
            "contract-region-aggregate-get-mut-status=blocked",
            "contract-region-aggregate-get-mut-list-child-count=1",
            "contract-region-aggregate-get-mut-storage-rejections=1",
            "contract-region-aggregate-get-mut-storage-rejected=true",
            "contract-region-aggregate-get-mut-loan-mut-paths=1",
            "contract-region-aggregate-get-mut-transfer-visible=true",
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
            "contract-region-mutability-diag0-span=0@615:633",
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
            "contract-region-relation-stress-fibonacci-lifetime-count=21",
            "contract-region-relation-stress-fibonacci-disconnected=false",
            "contract-region-relation-stress-fibonacci-transitive=true",
            "contract-region-relation-stress-fibonacci-plus-bound=true",
            "contract-region-relation-stress-chain-lifetime-count=28",
            "contract-region-relation-stress-chain-reachable=true",
            "contract-region-relation-stress-chain-reverse=false",
            "contract-region-relation-stress-cycle-left-right=true",
            "contract-region-relation-stress-cycle-right-left=true",
            "contract-region-relation-stress-declared-reflexive=true",
            "contract-region-relation-stress-undeclared-reflexive=false",
            "contract-region-relation-stress-static-reflexive=false",
            "contract-region-relation-stress-extern-gated=false",
            "contract-region-relation-stress-source-set-count=2",
            "contract-region-relation-stress-repetitions=3",
            "contract-region-relation-stress-scratch-active=2",
            "contract-region-relation-stress-scratch-capacity=28",
            "contract-region-relation-stress-scratch-generation-delta=6",
            "contract-region-relation-stress-scratch-generation-sequence=true",
            "contract-region-relation-stress-semantics-stable=true",
            "contract-region-relation-stress-scratch-active-stable=true",
            "contract-region-relation-stress-scratch-active-within-capacity=true",
            "contract-region-relation-stress-scratch-capacity-stable=true",
            "contract-region-relation-stress-source-cache-build-delta=0",
            "contract-region-relation-stress-source-cache-stable=true",
            "contract-region-relation-stress-no-historical-growth=true",
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
            "contract-region-bound-diagnostics-diag0=Meiya lifetime debt: lifetime bound 'ghost on 'a is not declared on undeclared_bound",
            "contract-region-bound-diagnostics-diag1=Meiya lifetime debt: 'static is reserved and cannot be used as a lifetime bound on 'a",
            "contract-region-bound-diagnostics-diag2=Meiya lifetime debt: '_ is elided and cannot be used as a lifetime bound on 'a",
            "contract-region-bound-diagnostics-diag3=Meiya lifetime debt: empty generic bound on 'a in empty_bound",
            "contract-region-bound-diagnostics-diag4=Meiya lifetime debt: lifetime 'a may only use lifetime bounds, but found Copy",
            "contract-region-bound-diagnostics-diag5=Meiya lifetime debt: type generic T cannot use lifetime bound 'a",
            "contract-region-bound-diagnostics-diag6=Meiya lifetime debt: lifetime 'a may only use lifetime bounds, but found Copy",
            "contract-region-bound-diagnostics-diag6-span=0@495:503",
            "contract-region-bound-diagnostics-diag7=Meiya lifetime debt: type generic T cannot use lifetime bound 'a",
            "contract-region-bound-diagnostics-diag7-span=0@548:553",
            "contract-region-bound-diagnostics-diag8=Meiya lifetime debt: empty generic bound on T in DoctrineEmptyType",
            "contract-region-bound-diagnostics-diag8-span=0@600:602",
            "contract-region-bound-diagnostics-diag9=Meiya lifetime debt: type generic T cannot use lifetime bound 'a",
            "contract-region-bound-diagnostics-diag9-span=0@658:670",
            "contract-region-bound-diagnostics-diag10=Meiya lifetime debt: empty generic bound on T in extern_empty_type",
            "contract-region-bound-diagnostics-diag10-span=0@743:745",
        ),
        "contract_region_loop_fixed_point_smoke.fk": (
            "contract-region-loop-fixed-point-ty-diagnostics=0",
            "contract-region-loop-fixed-point-mir-diagnostics=0",
            "contract-region-loop-fixed-point-borrow-diagnostics=0",
            "contract-region-loop-fixed-point-direct-status=clean",
            "contract-region-loop-fixed-point-direct-source-count=2",
            "contract-region-loop-fixed-point-direct-source0=first",
            "contract-region-loop-fixed-point-direct-source1=second",
            "contract-region-loop-fixed-point-alias-status=clean",
            "contract-region-loop-fixed-point-alias-source-count=2",
            "contract-region-loop-fixed-point-alias-has-first=true",
            "contract-region-loop-fixed-point-alias-has-second=true",
            "contract-region-loop-fixed-point-dedup-status=clean",
            "contract-region-loop-fixed-point-dedup-source-count=1",
            "contract-region-loop-fixed-point-dedup-source0=source",
            "contract-region-loop-fixed-point-ring-status=clean",
            "contract-region-loop-fixed-point-ring-source-count=12",
            "contract-region-loop-fixed-point-ring-source0=source0",
            "contract-region-loop-fixed-point-ring-source11=source11",
            "contract-region-loop-fixed-point-converged=true",
            "contract-region-loop-fixed-point-solved=true",
            "contract-region-loop-fixed-point-rounds-positive=true",
            "contract-region-loop-fixed-point-rounds-bounded=true",
            "contract-region-loop-fixed-point-multi-round=true",
            "contract-region-loop-fixed-point-memo-cycle-observed=true",
            "borrowck-snapshot-import ok=1 format=freak-borrowck-snapshot-v2 lines=120 files=1 results=4 paths=113 diagnostics=0 malformed=0 headers=1 ends=1",
            "borrowck-snapshot-restore ok=1 files=1 results=4 paths=113 diagnostics=0 skipped-other=0 arena-files=1",
            "contract-region-loop-fixed-point-restored-alias-status=clean",
            "contract-region-loop-fixed-point-restored-alias-source-count=2",
            "contract-region-loop-fixed-point-restored-alias-has-first=true",
            "contract-region-loop-fixed-point-restored-alias-has-second=true",
            "contract-region-loop-fixed-point-restored-ring-source-count=12",
            "contract-region-loop-fixed-point-restored-ring-source11=source11",
        ),
        "contract_region_many_root_smoke.fk": (
            "contract-region-many-root-ty-diagnostics=0",
            "contract-region-many-root-mir-diagnostics=0",
            "contract-region-many-root-borrow-diagnostics=0",
            "contract-region-many-root-results=1",
            "contract-region-many-root-memos=256",
            "contract-region-many-root-solves=256",
            "contract-region-many-root-work-items=512",
            "contract-region-many-root-results-clean=true",
            "contract-region-many-root-converged=true",
            "contract-region-many-root-resource-exhausted=false",
            "contract-region-many-root-linear-work=true",
            "contract-region-many-root-work-bounded=true",
        ),
        "contract_region_loop_fail_closed_smoke.fk": (
            "contract-region-loop-fail-closed-round-status=blocked",
            "contract-region-loop-fail-closed-round-diagnostics=1",
            "contract-region-loop-fail-closed-round-message=Meiya cannot establish the origin of this returned loan",
            "contract-region-loop-fail-closed-round-source-count=0",
            "contract-region-loop-fail-closed-round-converged=false",
            "contract-region-loop-fail-closed-round-resource-exhausted=false",
            "contract-region-loop-fail-closed-round-cap-hit=true",
            "contract-region-loop-fail-closed-budget-status=blocked",
            "contract-region-loop-fail-closed-budget-diagnostics=1",
            "contract-region-loop-fail-closed-budget-message=Meiya cannot establish the origin of this returned loan",
            "contract-region-loop-fail-closed-budget-source-count=0",
            "contract-region-loop-fail-closed-budget-converged=false",
            "contract-region-loop-fail-closed-budget-resource-exhausted=true",
            "contract-region-loop-fail-closed-budget-facts-bounded=true",
            "contract-region-loop-fail-closed-path-resource-exhausted=true",
            "contract-region-loop-fail-closed-path-facts-bounded=true",
            "contract-region-loop-fail-closed-path-opaque=true",
            "contract-region-loop-fail-closed-dependency-resource-exhausted=true",
            "contract-region-loop-fail-closed-dependency-edges-bounded=true",
            "contract-region-loop-fail-closed-dependency-opaque=true",
            "contract-region-loop-fail-closed-work-resource-exhausted=true",
            "contract-region-loop-fail-closed-work-queue-bounded=true",
            "contract-region-loop-fail-closed-work-opaque=true",
            "borrowck-snapshot-import ok=1 format=freak-borrowck-snapshot-v2 lines=76 files=2 results=2 paths=68 diagnostics=2 malformed=0 headers=1 ends=1",
            "contract-region-loop-fail-closed-snapshot-poisoned=true",
            "borrowck-snapshot-restore ok=1 files=2 results=2 paths=68 diagnostics=2 skipped-other=0 arena-files=2",
            "contract-region-loop-fail-closed-restored-round-status=blocked",
            "contract-region-loop-fail-closed-restored-budget-status=blocked",
            "contract-region-loop-fail-closed-restored-round-converged=false",
            "contract-region-loop-fail-closed-restored-budget-resource-exhausted=true",
            "contract-region-loop-fail-closed-truncated-v2-rejected=true",
            "contract-region-loop-fail-closed-legacy-v1-imported=true",
            "contract-region-loop-fail-closed-legacy-v1-restored=true",
            "contract-region-loop-fail-closed-legacy-v1-rounds=0",
            "contract-region-loop-fail-closed-legacy-v1-limit=0",
            "contract-region-loop-fail-closed-legacy-v1-solves=0",
            "contract-region-loop-fail-closed-legacy-v1-converged=true",
            "contract-region-loop-fail-closed-legacy-v1-resource-exhausted=false",
            "contract-region-loop-fail-closed-legacy-v1-work-items=0",
        ),
        "contract_region_loop_dependency_stress_smoke.fk": (
            "contract-region-loop-dependency-stress-ty-diagnostics=0",
            "contract-region-loop-dependency-stress-mir-diagnostics=0",
            "contract-region-loop-dependency-stress-borrow-diagnostics=0",
            "contract-region-loop-dependency-stress-status=clean",
            "contract-region-loop-dependency-stress-source-count=1",
            "contract-region-loop-dependency-stress-source=source",
            "contract-region-loop-dependency-stress-memos=50",
            "contract-region-loop-dependency-stress-memo-depth-proven=true",
            "contract-region-loop-dependency-stress-multi-round=true",
            "contract-region-loop-dependency-stress-rounds-bounded=true",
            "contract-region-loop-dependency-stress-converged=true",
            "contract-region-loop-dependency-stress-resource-exhausted=false",
            "contract-region-loop-dependency-stress-work-bounded=true",
        ),
        "contract_region_cfg_worklist_stress_smoke.fk": (
            "contract-region-cfg-worklist-stress-ty-diagnostics=0",
            "contract-region-cfg-worklist-stress-mir-diagnostics=0",
            "contract-region-cfg-worklist-stress-borrow-diagnostics=0",
            "contract-region-cfg-worklist-stress-block-count-bounded=true",
            "contract-region-cfg-worklist-stress-return-block-valid=true",
            "contract-region-cfg-worklist-stress-forward-reachable=true",
            "contract-region-cfg-worklist-stress-reverse-unreachable=true",
            "contract-region-cfg-worklist-stress-entry-acyclic=true",
            "contract-region-cfg-worklist-stress-status=clean",
            "contract-region-cfg-worklist-stress-source-count=1",
            "contract-region-cfg-worklist-stress-source=source",
            "contract-region-cfg-worklist-stress-converged=true",
            "contract-region-cfg-worklist-stress-work-bounded=true",
        ),
        "contract_region_loop_query_invalidation_smoke.fk": (
            "contract-region-loop-query-byte-length-stable=true",
            "contract-region-loop-query-offset-stable=true",
            "contract-region-loop-query-before-status=clean",
            "contract-region-loop-query-before-source-count=2",
            "contract-region-loop-query-before-source0=first",
            "contract-region-loop-query-before-source1=second",
            "contract-region-loop-query-before-signature-sources=2",
            "contract-region-loop-query-before-editor-coherent=true",
            "contract-region-loop-query-all-18-invalidations-positive=true",
            "contract-region-loop-query-invalidation-matches-diff=true",
            "contract-region-loop-query-health-ok=true",
            "contract-region-loop-query-after-status=clean",
            "contract-region-loop-query-after-source-count=1",
            "contract-region-loop-query-after-source0=first",
            "contract-region-loop-query-after-converged=true",
            "contract-region-loop-query-signature-stable=true",
            "contract-region-loop-query-after-diagnostics=0",
            "contract-region-loop-query-after-editor-coherent=true",
            "contract-region-loop-query-all-18-recomputations-positive=true",
            "contract-region-loop-query-snapshot-restored=true",
            "contract-region-loop-query-restored-status=clean",
            "contract-region-loop-query-restored-source-count=1",
            "contract-region-loop-query-restored-editor-coherent=true",
        ),
        "contract_region_aggregate_boundary_smoke.fk": (
            "aggregate-boundary-core-parse-diagnostics=0",
            "aggregate-boundary-core-ty-diagnostics=0",
            "aggregate-boundary-core-mir-diagnostics=0",
            "aggregate-boundary-core-borrow-diagnostics=7",
            "aggregate-boundary-tuple-owner-live=blocked",
            "aggregate-boundary-tuple-sibling-dead=clean",
            "aggregate-boundary-same-lifetime-first-live=blocked",
            "aggregate-boundary-same-lifetime-second-live=blocked",
            "aggregate-boundary-array-owner-live=blocked",
            "aggregate-boundary-array-sibling-live=blocked",
            "aggregate-boundary-shape-owner-live=blocked",
            "aggregate-boundary-shape-sibling-dead=clean",
            "aggregate-boundary-empty-array-call=clean",
            "aggregate-boundary-outlives-owner-live=blocked",
            "aggregate-boundary-tuple-leaves=2",
            "aggregate-boundary-tuple-leaf0=.0",
            "aggregate-boundary-tuple-leaf1=.1",
            "aggregate-boundary-tuple-source0-count=1",
            "aggregate-boundary-tuple-source0-projection=.0",
            "aggregate-boundary-tuple-source1-count=1",
            "aggregate-boundary-tuple-source1-projection=.1",
            "aggregate-boundary-same-source0-count=2",
            "aggregate-boundary-same-source1-count=2",
            "aggregate-boundary-same-source0-projection0=.0",
            "aggregate-boundary-same-source0-projection1=.1",
            "aggregate-boundary-outlives-source-count=1",
            "aggregate-boundary-outlives-source-projection=.0",
            "aggregate-boundary-projected-tuple-source-count=1",
            "aggregate-boundary-array-leaves=1",
            "aggregate-boundary-array-projection=[*]",
            "aggregate-boundary-empty-array-leaves=0",
            "aggregate-boundary-shape-leaves=2",
            "aggregate-boundary-shape-leaf0=.left",
            "aggregate-boundary-shape-leaf1=.right",
            "aggregate-boundary-mir-call-leaves=2",
            "aggregate-boundary-mir-call-source0-projection=.0",
            "aggregate-boundary-mir-call-source1-projection=.1",
            "aggregate-boundary-mir-empty-call-leaves=0",
            "aggregate-boundary-empty-call-provenance-known-empty=true",
            "aggregate-boundary-empty-call-provenance-count=0",
            "aggregate-boundary-rewrite-diagnostic=true",
        ),
        "contract_region_aggregate_route_boundary_smoke.fk": (
            "aggregate-boundary-route-parse-diagnostics=0",
            "aggregate-boundary-route-ty-diagnostics=1",
            "aggregate-boundary-route-mir-diagnostics=1",
            "aggregate-boundary-route-borrow-diagnostics=4",
            "aggregate-boundary-route-roundtrip=clean",
            "aggregate-boundary-route-owner-live=blocked",
            "aggregate-boundary-route-empty-clean=clean",
            "aggregate-boundary-shape-to-route=clean",
            "aggregate-boundary-shape-to-route-forward=clean",
            "aggregate-boundary-shape-to-route-roundtrip=clean",
            "aggregate-boundary-nested-empty=clean",
            "aggregate-boundary-owned-escape=blocked",
            "aggregate-boundary-nested-owned-escape=blocked",
            "aggregate-boundary-route-ty-diag0=Meiya cannot find a source for returned lifetime 'a at .0",
            "aggregate-boundary-route-ty-diag0-help=add a compatible lend parameter leaf whose declared lifetime outlives this returned projection",
            "aggregate-boundary-route-leaves=1",
            "aggregate-boundary-route-guard=RoutedView<'a>::Hold",
            "aggregate-boundary-route-source-guard=RoutedView<'a>::Hold",
            "aggregate-boundary-nested-route-guard=OuterView<'a>::Wrap/InnerView<'a>::Hold",
            "aggregate-boundary-owned-diagnostic=true",
        ),
        "contract_region_aggregate_edge_smoke.fk": (
            "aggregate-edge-parse-diagnostics=0",
            "aggregate-edge-ty-diagnostics=0",
            "aggregate-edge-mir-diagnostics=0",
            "aggregate-edge-borrow-diagnostics=3",
            "aggregate-edge-nested-const-roundtrip=clean",
            "aggregate-edge-nested-const-call-leaves=1",
            "aggregate-edge-nested-const-source-projection=.0[*]",
            "aggregate-edge-empty-generic-call=clean",
            "aggregate-edge-empty-generic-type=[lend mut Ship;0]",
            "aggregate-edge-empty-array-stores-lend=false",
            "aggregate-edge-empty-generic-diagnostic=false",
            "aggregate-edge-different-target-source-count=1",
            "aggregate-edge-different-target-sibling-dead=clean",
            "aggregate-edge-generic-target-source-count=1",
            "aggregate-edge-generic-target-sibling-dead=clean",
            "aggregate-edge-projected-call-sibling-dead=clean",
            "aggregate-edge-projected-call-owner-live=blocked",
            "aggregate-edge-returned-call-leaf-rebind=clean",
            "aggregate-edge-returned-call-leaf-holder=returned.0",
            "aggregate-edge-projected-scalar-source-count=1",
            "aggregate-edge-projected-scalar-roundtrip=clean",
            "aggregate-edge-duplicate-projection-count=2",
            "aggregate-edge-duplicate-projection0=.0",
            "aggregate-edge-duplicate-projection1=.1",
            "aggregate-edge-duplicate-rebind-all=clean",
            "aggregate-edge-duplicate-rebind-one=blocked",
            "aggregate-edge-call-projection-relation-limit=1024",
            "aggregate-edge-duplicate-call-projection-count=2",
            "aggregate-edge-duplicate-call-projection0=.0",
            "aggregate-edge-duplicate-call-projection1=.1",
            "aggregate-edge-duplicate-call-rebind-all=clean",
            "aggregate-edge-duplicate-call-rebind-one=blocked",
            "aggregate-edge-duplicate-projected-call-rebind-all=clean",
            "aggregate-edge-nested-duplicate-call-rebind-all=clean",
        ),
        "contract_region_aggregate_budget_smoke.fk": (
            "aggregate-budget-leaf-limit=256",
            "aggregate-budget-source-limit=256",
            "aggregate-budget-wide-leaves=-1",
            "aggregate-budget-recursive-leaves=-1",
            "aggregate-budget-fanout-sources=-1",
            "aggregate-budget-fanout-opaque=true",
            "aggregate-budget-leaf-diagnostic=true",
            "aggregate-budget-source-cutoff-atomic=true",
        ),
        "contract_region_aggregate_negative_smoke.fk": (
            "aggregate-negative-upgrade-source-count=0",
            "aggregate-negative-upgrade-diagnostic=true",
            "aggregate-negative-mismatch-map-count=-1",
            "aggregate-negative-mismatch-status=blocked",
            "aggregate-negative-mismatch-diagnostic=true",
        ),
        "contract_region_fixed_aggregate_smoke.fk": (
            "fixed-aggregate-parse-diagnostics=0",
            "fixed-aggregate-ty-diagnostics=0",
            "fixed-aggregate-mir-diagnostics=8",
            "fixed-aggregate-borrow-diagnostics=45",
            "fixed-aggregate-tuple-sibling-dead=clean",
            "fixed-aggregate-tuple-left-live=blocked",
            "fixed-aggregate-array-sibling-dead=clean",
            "fixed-aggregate-array-left-live=blocked",
            "fixed-aggregate-shape-sibling-dead=clean",
            "fixed-aggregate-shape-left-live=blocked",
            "fixed-aggregate-explicit-mut-alias=blocked",
            "fixed-aggregate-route-local=clean",
            "fixed-aggregate-route-pattern-capture-keeps-loan=blocked",
            "fixed-aggregate-direct-local=clean",
            "fixed-aggregate-nested-local=clean",
            "fixed-aggregate-repeat-shared=clean",
            "fixed-aggregate-repeat-immutable-outer=clean",
            "fixed-aggregate-repeat-owned-sibling=clean",
            "fixed-aggregate-repeat-cloneable=clean",
            "fixed-aggregate-repeat-nominal-copy=clean",
            "fixed-aggregate-repeat-copy-diagnostic=true",
            "fixed-aggregate-repeat-copy-diagnostic-count=2",
            "fixed-aggregate-repeat-shared-rebind-all=clean",
            "fixed-aggregate-repeat-shared-rebind-one=blocked",
            "fixed-aggregate-repeat-nested-sibling-dead=clean",
            "fixed-aggregate-repeat-nested-container-rebind=clean",
            "fixed-aggregate-repeat-structural-copy=clean",
            "fixed-aggregate-repeat-shared-dead-256=clean",
            "fixed-aggregate-repeat-shared-partial-rebind-257=clean",
            "fixed-aggregate-repeat-shared-dead-257=clean",
            "fixed-aggregate-empty-array-generic-call=clean",
            "fixed-aggregate-empty-array-stored-call=clean",
            "fixed-aggregate-empty-array-stores-lend=false",
            "fixed-aggregate-empty-array-generic-diagnostic=false",
            "fixed-aggregate-repeat-mut=blocked",
            "fixed-aggregate-repeat-mut-one=clean",
            "fixed-aggregate-repeat-mut-aggregate=blocked",
            "fixed-aggregate-move=blocked",
            "fixed-aggregate-sibling-rebind=blocked",
            "fixed-aggregate-left-rebind=clean",
            "fixed-aggregate-duplicate-shared-rebind-releases=clean",
            "fixed-aggregate-left-rebind-protects-new=blocked",
            "fixed-aggregate-immutable-holder-rebind=clean",
            "fixed-aggregate-scoped-argument-shape-live=blocked",
            "fixed-aggregate-projection-destination-alias=blocked",
            "fixed-aggregate-loop-rebind-before-backedge=clean",
            "fixed-aggregate-shape-child0-projection=.left",
            "fixed-aggregate-loop-sibling-survives=blocked",
            "fixed-aggregate-dynamic-index-rebind=blocked",
            "fixed-aggregate-dynamic-index-preserves-old=blocked",
            "fixed-aggregate-dynamic-index-includes-new=blocked",
            "fixed-aggregate-repeat-mut-zero=clean",
            "fixed-aggregate-mutate-through-stored=clean",
            "fixed-aggregate-immutable-outer-lend=blocked",
            "fixed-aggregate-closure-capture-keeps-loan=blocked",
            "fixed-aggregate-closure-forwarded-capture-keeps-loan=blocked",
            "fixed-aggregate-wrapped-closure-call-rejected=blocked",
            "fixed-aggregate-empty-closure-repeat-clean=clean",
            "fixed-aggregate-zero-length-closure-call-clean=clean",
            "fixed-aggregate-dynamic-closure-call-storage-rejected=blocked",
            "fixed-aggregate-dynamic-closure-storage-rejected=blocked",
            "fixed-aggregate-dynamic-closure-storage-diagnostic=true",
            "fixed-aggregate-dynamic-closure-storage-diagnostic-count=8",
            "fixed-aggregate-fixed-closure-storage-diagnostic-count=5",
            "fixed-aggregate-dynamic-forwarded-closure-storage-rejected=blocked",
            "fixed-aggregate-forwarded-closure-rebind-storage-rejected=blocked",
            "fixed-aggregate-mixed-lend-closure-storage-rejected=blocked",
            "fixed-aggregate-projected-closure-assignment-storage-rejected=blocked",
            "fixed-aggregate-plain-local-cycle=clean",
            "fixed-aggregate-dynamic-closure-conditional-rebind=blocked",
            "fixed-aggregate-fixed-closure-tuple-storage-rejected=blocked",
            "fixed-aggregate-fixed-closure-repeat-storage-rejected=blocked",
            "fixed-aggregate-dynamic-wrapped-closure-storage-rejected=blocked",
            "fixed-aggregate-dynamic-nested-move-closure-storage-rejected=blocked",
            "fixed-aggregate-fixed-closure-storage-diagnostic=true",
            "fixed-aggregate-mutable-lend-projection-protects-replacement=blocked",
            "fixed-aggregate-mutable-lend-projection-releases-replaced=clean",
            "fixed-aggregate-returned-call-owner-live=blocked",
            "fixed-aggregate-returned-call-duplicate-mut=blocked",
            "fixed-aggregate-descendant-write-may-bind=false",
            "fixed-aggregate-symbolic-write-may-bind=true",
            "fixed-aggregate-parent-write-may-bind=true",
            "fixed-aggregate-dynamic-write-definite-slot0=false",
            "fixed-aggregate-concrete-write-definite-slot0=true",
            "fixed-aggregate-whole-write-definite-slot0=true",
            "fixed-aggregate-repeat-mut-zero-holder=@temporary",
            "fixed-aggregate-shape-child1-projection=.right",
            "fixed-aggregate-shape-left-child-found=true",
            "fixed-aggregate-shape-right-child-found=true",
            "fixed-aggregate-route-child0-projection=.left",
            "fixed-aggregate-route-child1-projection=.right",
            "fixed-aggregate-route-left-child-found=true",
            "fixed-aggregate-route-right-child-found=true",
            "fixed-aggregate-route-left-holder=stored.left",
            "fixed-aggregate-route-right-holder=stored.right",
            "fixed-aggregate-route-pattern-left-type=lend mut Ship",
            "fixed-aggregate-direct-holder=stored.view",
            "fixed-aggregate-class-tuple=fixed",
            "fixed-aggregate-class-array=fixed",
            "fixed-aggregate-class-shape=fixed",
            "fixed-aggregate-class-route=fixed",
            "fixed-aggregate-class-direct-lifetime=fixed",
            "fixed-aggregate-class-list=unsupported",
            "fixed-aggregate-compact-lend-mut=Stored<lend mut Ship,int>",
            "fixed-aggregate-compact-lend-lifetime=Stored<lend 'a Ship,int>",
        ),
        "contract_region_repeat_projection_smoke.fk": (
            "repeat-projection-parse-diagnostics=0",
            "repeat-projection-ty-diagnostics=0",
            "repeat-projection-mir-diagnostics=0",
            "repeat-projection-borrow-diagnostics=2",
            "repeat-projection-rebind-257=clean",
            "repeat-projection-partial-rebind-1025=clean",
            "repeat-projection-extracted-alias-rebind-256=blocked",
            "repeat-projection-capture-live=blocked",
        ),
        "contract_region_recursive_wrapper_smoke.fk": (
            "recursive-wrapper-parse-diagnostics=0",
            "recursive-wrapper-ty-diagnostics=3",
            "recursive-wrapper-mir-diagnostics=3",
            "recursive-wrapper-storage-class=unsupported",
            "recursive-wrapper-fixed-storage=false",
            "recursive-wrapper-leaf-count=-1",
            "recursive-wrapper-diagnostic=true",
        ),
        "contract_region_conditional_alias_smoke.fk": (
            "conditional-alias-parse-diagnostics=0",
            "conditional-alias-ty-diagnostics=0",
            "conditional-alias-mir-diagnostics=0",
            "conditional-alias-borrow-diagnostics=3",
            "conditional-alias-status=blocked",
            "transferred-alias-status=blocked",
            "transferred-alias-long-release-status=clean",
            "transferred-alias-source-rebind-status=blocked",
            "closure-aggregate-write-parse-diagnostics=0",
            "closure-aggregate-write-ty-diagnostics=0",
            "closure-aggregate-write-mir-diagnostics=1",
            "closure-aggregate-write-rejected=true",
            "nested-lend-projection-parse-diagnostics=0",
            "nested-lend-projection-ty-diagnostics=0",
            "nested-lend-projection-mir-diagnostics=0",
            "nested-lend-projection-borrow-diagnostics=1",
            "nested-lend-projection-status=blocked",
            "indexed-nested-lend-projection-parse-diagnostics=0",
            "indexed-nested-lend-projection-ty-diagnostics=0",
            "indexed-nested-lend-projection-mir-diagnostics=0",
            "indexed-nested-lend-projection-borrow-diagnostics=1",
            "indexed-nested-lend-projection-status=blocked",
            "shadowed-alias-parse-diagnostics=0",
            "shadowed-alias-ty-diagnostics=0",
            "shadowed-alias-mir-diagnostics=0",
            "shadowed-alias-borrow-diagnostics=1",
            "shadowed-alias-status=blocked",
        ),
        "contract_region_fixed_aggregate_query_smoke.fk": (
            "fixed-aggregate-query-byte-length-stable=true",
            "fixed-aggregate-query-offset-stable=true",
            "fixed-aggregate-query-before-status=blocked",
            "fixed-aggregate-query-before-shape-facts=true",
            "fixed-aggregate-query-before-editor-coherent=true",
            "fixed-aggregate-query-all-18-invalidations-positive=true",
            "fixed-aggregate-query-invalidation-matches-diff=true",
            "fixed-aggregate-query-health-ok=true",
            "fixed-aggregate-query-after-status=clean",
            "fixed-aggregate-query-after-diagnostics=0",
            "fixed-aggregate-query-after-shape-facts=true",
            "fixed-aggregate-query-after-editor-coherent=true",
            "fixed-aggregate-query-snapshot-restored=true",
            "fixed-aggregate-query-restore-generation-advanced=true",
            "fixed-aggregate-query-restored-status=blocked",
            "fixed-aggregate-query-restored-diagnostics=1",
            "fixed-aggregate-query-restored-shape-facts=true",
            "fixed-aggregate-query-restored-editor-coherent=true",
        ),
        "contract_region_storage_negative_smoke.fk": (
            "contract-region-storage-ty-diagnostics=4",
            "contract-region-storage-ty-diagnostics-exact-four=true",
            "contract-region-storage-ty-diag0=Meiya cannot store a named lend in parameter 0 of named_signature_escape yet",
            "contract-region-storage-ty-diag0-help=use a direct lend, tuple, fixed array, shape, or route payload; dynamic containers, callbacks, aliases, and doctrines remain outside fixed aggregate provenance",
            "contract-region-storage-ty-diag1=Meiya cannot store a named lend in return type of named_signature_escape yet",
            "contract-region-storage-ty-diag1-help=use a direct lend, tuple, fixed array, shape, or route payload; dynamic containers, callbacks, aliases, and doctrines remain outside fixed aggregate provenance",
            "contract-region-storage-ty-diag2=Meiya cannot store a lend in parameter 0 of elided_signature_escape yet",
            "contract-region-storage-ty-diag2-help=use a direct lend, tuple, fixed array, shape, or route payload; dynamic containers, callbacks, aliases, and doctrines remain outside fixed aggregate provenance",
            "contract-region-storage-ty-diag3=Meiya cannot store a lend in return type of elided_signature_escape yet",
            "contract-region-storage-ty-diag3-help=use a direct lend, tuple, fixed array, shape, or route payload; dynamic containers, callbacks, aliases, and doctrines remain outside fixed aggregate provenance",
            "contract-region-storage-mir-diagnostics=10",
            "contract-region-storage-mir-diagnostics-exact-ten=true",
            "contract-region-storage-mir-diag0=Meiya cannot store a named lend in parameter 0 of named_signature_escape yet",
            "contract-region-storage-mir-diag0-help=use a direct lend, tuple, fixed array, shape, or route payload; dynamic containers, callbacks, aliases, and doctrines remain outside fixed aggregate provenance",
            "contract-region-storage-mir-diag1=Meiya cannot store a named lend in return type of named_signature_escape yet",
            "contract-region-storage-mir-diag1-help=use a direct lend, tuple, fixed array, shape, or route payload; dynamic containers, callbacks, aliases, and doctrines remain outside fixed aggregate provenance",
            "contract-region-storage-mir-diag2=Meiya cannot store a lend in parameter 0 of elided_signature_escape yet",
            "contract-region-storage-mir-diag2-help=use a direct lend, tuple, fixed array, shape, or route payload; dynamic containers, callbacks, aliases, and doctrines remain outside fixed aggregate provenance",
            "contract-region-storage-mir-diag3=Meiya cannot store a lend in return type of elided_signature_escape yet",
            "contract-region-storage-mir-diag3-help=use a direct lend, tuple, fixed array, shape, or route payload; dynamic containers, callbacks, aliases, and doctrines remain outside fixed aggregate provenance",
            "contract-region-storage-list-literal-diag=Meiya cannot store a lend inside a list yet",
            "contract-region-storage-list-literal-detail=list_literal_source_set constructs list element 1 with type lend Ship; keep this borrowed value in a scalar local holder until MIR can preserve aggregate child provenance",
            "contract-region-storage-some-diag=Meiya cannot store a lend inside a maybe some() yet",
            "contract-region-storage-some-detail=maybe_source_set constructs the some() payload with type lend Ship; keep this borrowed value in a scalar local holder until MIR can preserve aggregate child provenance",
            "contract-region-storage-ok-diag=Meiya cannot store a lend inside a result ok() yet",
            "contract-region-storage-ok-detail=result_ok_source_set constructs the ok() payload with type lend Ship; keep this borrowed value in a scalar local holder until MIR can preserve aggregate child provenance",
            "contract-region-storage-err-diag=Meiya cannot store a lend inside a result err() yet",
            "contract-region-storage-err-detail=result_err_source_set constructs the err() payload with type lend Ship; keep this borrowed value in a scalar local holder until MIR can preserve aggregate child provenance",
            "contract-region-storage-map-key-diag=Meiya cannot store a lend inside a map yet",
            "contract-region-storage-map-key-detail=map_key_source_set constructs map entry 1 key with type lend Ship; keep this borrowed value in a scalar local holder until MIR can preserve aggregate child provenance",
            "contract-region-storage-map-value-diag=Meiya cannot store a lend inside a map yet",
            "contract-region-storage-map-value-detail=map_value_source_set constructs map entry 1 value with type lend Ship; keep this borrowed value in a scalar local holder until MIR can preserve aggregate child provenance",
            "contract-region-storage-choose-status=clean",
            "contract-region-storage-local-holder-status=clean",
            "contract-region-storage-elided-holder-status=clean",
            "contract-region-storage-tuple-status=clean",
            "contract-region-storage-fixed-array-literal-status=clean",
            "contract-region-storage-fixed-array-repeat-status=clean",
            "contract-region-storage-list-literal-status=blocked",
            "contract-region-storage-shape-value-status=clean",
            "contract-region-storage-route-payload-status=clean",
            "contract-region-storage-some-status=blocked",
            "contract-region-storage-ok-status=blocked",
            "contract-region-storage-err-status=blocked",
            "contract-region-storage-map-key-status=blocked",
            "contract-region-storage-map-value-status=blocked",
            "contract-region-storage-named-signature-status=clean",
            "contract-region-storage-elided-signature-status=clean",
            "contract-region-storage-borrow-diagnostics=10",
            "contract-region-storage-borrow-diagnostics-exact-ten=true",
            "contract-region-storage-borrow-diags-match-mir=true",
            "contract-region-storage-deep-class=exhausted",
            "contract-region-storage-deep-confirmed-lend=false",
            "contract-region-storage-deep-may-store-lend=true",
            "contract-region-storage-deep-wrapper-class=exhausted",
            "contract-region-storage-deep-wrapper-confirmed-lend=false",
            "contract-region-storage-deep-wrapper-may-store-lend=true",
            "contract-region-storage-deep-diagnostic-added=true",
            "contract-region-storage-deep-diagnostic=Meiya's lend-storage analysis exhausted its depth budget",
        ),
        "contract_region_generic_lend_escape_smoke.fk": (
            "contract-region-generic-lend-escape-parse-diagnostics=0",
            "contract-region-generic-lend-escape-ty-diagnostics=0",
            "contract-region-generic-lend-escape-mir-diagnostics=3",
            "contract-region-generic-lend-escape-meiya-count=3",
            "contract-region-generic-lend-escape-wrap-type=maybe<T>",
            "contract-region-generic-lend-escape-wrap-hidden-loan=false",
            "contract-region-generic-lend-escape-identity-type=T",
            "contract-region-generic-lend-escape-identity-outer-loan=false",
            "contract-region-generic-lend-escape-diag0-message=Meiya cannot substitute a lend-bearing type for a generic call yet",
            "contract-region-generic-lend-escape-diag0-help=wrap infers T as lend Ship; keep lends on explicit lend parameters and outer borrowed returns until generic provenance exists",
            "contract-region-generic-lend-escape-diag1-message=Meiya cannot substitute a lend-bearing type for a generic call yet",
           "contract-region-generic-lend-escape-diag1-help=identity infers T as lend Ship; keep lends on explicit lend parameters and outer borrowed returns until generic provenance exists",
            "contract-region-generic-lend-escape-nominal-type=T",
            "contract-region-generic-lend-escape-diag2-message=Meiya cannot substitute a lend-bearing type for a generic call yet",
            "contract-region-generic-lend-escape-diag2-help=identity infers T as Direct<'a>; keep lends on explicit lend parameters and outer borrowed returns until generic provenance exists",
            "contract-region-owner-generic-happy-parse-diagnostics=0",
            "contract-region-owner-generic-happy-ty-diagnostics=0",
            "contract-region-owner-generic-happy-mir-diagnostics=0",
            "contract-region-owner-generic-happy-instance-type=Box<Ship>",
            "contract-region-owner-generic-happy-associated-type=Box<Ship>",
            "contract-region-owner-generic-happy-shared-type=Shared<Ship>",
            "contract-region-owner-generic-happy-borrow-type=lend Ship",
            "contract-region-owner-generic-happy-new-identity=builtin::Shared::new",
            "contract-region-owner-generic-happy-new-builtin=true",
            "contract-region-owner-generic-happy-borrow-identity=builtin::Shared::borrow",
            "contract-region-owner-generic-happy-borrow-builtin=true",
            "contract-region-owner-generic-happy-forged-identity-empty=true",
            "contract-region-owner-generic-happy-forged-builtin=false",
            "contract-region-owner-generic-happy-alpha-param=Direct<'b>",
            "contract-region-owner-generic-happy-alpha-return=Direct<'b>",
            "contract-region-owner-generic-negative-parse-diagnostics=0",
            "contract-region-owner-generic-negative-ty-diagnostics=0",
            "contract-region-owner-generic-negative-mir-diagnostics=8",
            "contract-region-owner-generic-negative-meiya-count=7",
            "contract-region-owner-generic-negative-instance-type=unknown",
            "contract-region-owner-generic-negative-associated-type=unknown",
            "contract-region-owner-generic-negative-shared-type=unknown",
            "contract-region-owner-generic-negative-shared-identity-empty=true",
            "contract-region-owner-generic-negative-shared-builtin=false",
            "contract-region-owner-generic-negative-method-boundary-count=1",
            "contract-region-owner-generic-negative-nominal-associated-type=unknown",
            "contract-region-owner-generic-negative-nominal-instance-type=unknown",
            "contract-region-owner-generic-negative-nominal-shared-type=unknown",
            "contract-region-owner-generic-negative-nominal-associated-identity-empty=true",
            "contract-region-owner-generic-negative-nominal-instance-identity-empty=true",
            "contract-region-owner-generic-negative-nominal-shared-identity-empty=true",
            "contract-region-owner-generic-negative-nominal-shared-builtin=false",
            "contract-region-owner-generic-negative-direct-instance-type=unknown",
            "contract-region-owner-generic-negative-operator-type=unknown",
            "contract-region-owner-generic-negative-diag6-message=Meiya cannot carry a lend-bearing aggregate across a method call yet",
            "contract-region-owner-generic-negative-diag7-message=Meiya cannot substitute a lend-bearing type for a generic call yet",
            "contract-region-owner-generic-negative-diag0-message=Meiya cannot substitute a lend-bearing type for a generic call yet",
            "contract-region-owner-generic-negative-diag0-help=Box<lend Ship>.keep derives owner generic T as lend Ship; keep lends on explicit lend parameters and outer borrowed returns until generic provenance exists",
            "contract-region-owner-generic-negative-diag1-message=Meiya cannot substitute a lend-bearing type for a generic call yet",
            "contract-region-owner-generic-negative-diag1-help=Box<lend Ship>::pack derives owner generic T as lend Ship; keep lends on explicit lend parameters and outer borrowed returns until generic provenance exists",
            "contract-region-owner-generic-negative-diag2-message=Meiya cannot substitute a lend-bearing type for a generic call yet",
            "contract-region-owner-generic-negative-diag2-help=Shared<lend Ship>::new derives owner generic T as lend Ship; keep lends on explicit lend parameters and outer borrowed returns until generic provenance exists",
            "contract-region-owner-generic-negative-diag3-message=Meiya cannot substitute a lend-bearing type for a generic call yet",
            "contract-region-owner-generic-negative-diag3-help=Box<Direct<'a>>::pack derives owner generic T as Direct<'a>; keep lends on explicit lend parameters and outer borrowed returns until generic provenance exists",
            "contract-region-owner-generic-negative-diag4-message=Meiya cannot substitute a lend-bearing type for a generic call yet",
            "contract-region-owner-generic-negative-diag4-help=Box<Direct<'a>>.keep derives owner generic T as Direct<'a>; keep lends on explicit lend parameters and outer borrowed returns until generic provenance exists",
            "contract-region-owner-generic-negative-diag5-message=Meiya cannot substitute a lend-bearing type for a generic call yet",
            "contract-region-owner-generic-negative-diag5-help=Shared<Direct<'a>>::new derives owner generic T as Direct<'a>; keep lends on explicit lend parameters and outer borrowed returns until generic provenance exists",
            "contract-region-shadowed-shared-parse-diagnostics=0",
            "contract-region-shadowed-shared-ty-diagnostics=0",
            "contract-region-shadowed-shared-mir-diagnostics=0",
            "contract-region-shadowed-shared-borrow-type=Ship",
            "contract-region-shadowed-shared-new-type=Shared<Ship>",
            "contract-region-shadowed-shared-borrow-identity-empty=true",
            "contract-region-shadowed-shared-borrow-builtin=false",
            "contract-region-shadowed-shared-new-identity-empty=true",
            "contract-region-shadowed-shared-new-builtin=false",
            "contract-region-builtin-identity-poisoned-before-restore=true",
            "contract-region-mir-snapshot-missing-field-validation-rejected=true",
            "contract-region-mir-snapshot-missing-field-restore-rejected=true",
            "contract-region-mir-snapshot-v4-validation-rejected=true",
            "contract-region-mir-snapshot-v4-restore-rejected=true",
            "contract-region-mir-snapshot-child-before-parent-validation-rejected=true",
            "contract-region-mir-snapshot-child-before-parent-restore-rejected=true",
            "contract-region-mir-snapshot-invalid-restore-state-stable=true",
            "contract-region-builtin-identity-restore-ok=true",
            "contract-region-builtin-identity-borrow-after-restore=true",
            "contract-region-builtin-identity-forged-after-restore=false",
            "contract-region-builtin-identity-shadow-after-restore=false",
        ),
        "contract_region_source_cache_churn_smoke.fk": (
            "contract-region-source-cache-churn-parse-diagnostics=0",
            "contract-region-source-cache-churn-ty-diagnostics=0",
            "contract-region-source-cache-churn-capacity=32",
            "contract-region-source-cache-churn-source-signatures=1",
            "contract-region-source-cache-churn-churn-rows=35",
            "contract-region-source-cache-churn-initial-build-delta=1",
            "contract-region-source-cache-churn-initial-entry-count=1",
            "contract-region-source-cache-churn-bounded-after-fill=true",
            "contract-region-source-cache-churn-evicted-first-rebuild-delta=1",
            "contract-region-source-cache-churn-evicted-first-count=2",
            "contract-region-source-cache-churn-evicted-first-order=true",
            "contract-region-source-cache-churn-entry-count-after-rebuild=32",
            "contract-region-source-cache-churn-known-empty-first-build-delta=1",
            "contract-region-source-cache-churn-known-empty-second-build-delta=0",
            "contract-region-source-cache-churn-known-empty-count=0",
            "contract-region-source-cache-churn-known-empty-count-again=0",
            "contract-region-source-cache-churn-known-empty-cached=true",
            "contract-region-source-cache-churn-signature-restore-ok=1",
            "contract-region-source-cache-churn-signature-restore-entry-count-after-invalidate=31",
            "contract-region-source-cache-churn-signature-restore-rebuild-delta=1",
            "contract-region-source-cache-churn-signature-restore-order=true",
            "contract-region-source-cache-churn-file-restore-ok=true",
            "contract-region-source-cache-churn-file-restore-child-handles-reused=true",
            "contract-region-source-cache-churn-file-restore-cleared-signatures=true",
            "contract-region-source-cache-churn-file-restore-cleared-diagnostics=true",
            "contract-region-source-cache-churn-file-restore-entry-count-after-invalidate=0",
            "contract-region-source-cache-churn-file-signature-restore-ok=1",
            "contract-region-source-cache-churn-file-restore-rebuild-delta=1",
            "contract-region-source-cache-churn-file-restore-entry-count-after-rebuild=1",
            "contract-region-source-cache-churn-file-restore-order=true",
            "contract-region-source-cache-churn-repeated-file-restore-ok=true",
            "contract-region-source-cache-churn-repeated-file-restore-child-handles-reused=true",
            "contract-region-source-cache-churn-repeated-file-restore-cleared-signatures=true",
            "contract-region-source-cache-churn-repeated-file-restore-cleared-diagnostics=true",
            "contract-region-source-cache-churn-repeated-file-restore-entry-count-after-invalidate=0",
            "contract-region-source-cache-churn-repeated-file-signature-restore-ok=1",
            "contract-region-source-cache-churn-repeated-file-restore-rebuild-delta=1",
            "contract-region-source-cache-churn-repeated-file-restore-entry-count-after-rebuild=1",
            "contract-region-source-cache-churn-repeated-file-restore-order=true",
            "contract-region-source-cache-churn-snapshot-bad-declared-validation-rejected=true",
            "contract-region-source-cache-churn-snapshot-child-before-parent-validation-rejected=true",
            "contract-region-source-cache-churn-snapshot-bad-declared-restore-rejected=true",
            "contract-region-source-cache-churn-snapshot-child-before-parent-restore-rejected=true",
            "contract-region-source-cache-churn-snapshot-invalid-restore-state-stable=true",
            "contract-region-source-cache-churn-bounded-final=true",
        ),
        "contract_region_boundary_negative_smoke.fk": (
            "contract-region-boundary-negative-diagnostics=3",
            "contract-region-boundary-negative-diagnostics-exact-three=true",
            "contract-region-boundary-negative-diag0=Meiya cannot store a named lend in parameter 0 of callback_boundary yet",
            "contract-region-boundary-negative-diag0-source-path=contract-region-boundary-negative.fk",
            "contract-region-boundary-negative-diag0-range=163:224",
            "contract-region-boundary-negative-diag0-help=use a direct lend, tuple, fixed array, shape, or route payload; dynamic containers, callbacks, aliases, and doctrines remain outside fixed aggregate provenance",
            "contract-region-boundary-negative-diag1=Meiya cannot accept a static lend parameter yet",
            "contract-region-boundary-negative-diag1-source-path=contract-region-boundary-negative.fk",
            "contract-region-boundary-negative-diag1-range=279:286",
            "contract-region-boundary-negative-diag1-help='static needs source-storage classification before callers may promise an immortal loan",
            "contract-region-boundary-negative-diag2=Meiya cannot prove a static borrowed return yet",
            "contract-region-boundary-negative-diag2-source-path=contract-region-boundary-negative.fk",
            "contract-region-boundary-negative-diag2-range=303:320",
            "contract-region-boundary-negative-diag2-help='static returned loans need global-storage provenance before this contract can be sound",
        ),
        "contract_region_forwarding_boundary_negative_smoke.fk": (
            "contract-region-forwarding-method-ty-diagnostics=0",
            "contract-region-forwarding-method-mir-diagnostics=1",
            "contract-region-forwarding-method-borrow-diagnostics=2",
            "contract-region-forwarding-method-status=blocked",
            "contract-region-forwarding-method-invocation-diagnostic-count=1",
            "contract-region-forwarding-method-invocation-message=Meiya cannot establish the origin of this returned loan",
            "contract-region-forwarding-method-invocation-source-path=contract-region-forwarding-method.fk",
            "contract-region-forwarding-method-invocation-range=255:282",
            "contract-region-forwarding-method-rejected=true",
            "contract-region-forwarding-method-silently-accepted=false",
            "contract-region-forwarding-dynamic-ty-diagnostics=0",
            "contract-region-forwarding-dynamic-mir-diagnostics=1",
            "contract-region-forwarding-dynamic-borrow-diagnostics=2",
            "contract-region-forwarding-dynamic-status=blocked",
            "contract-region-forwarding-dynamic-invocation-diagnostic-count=1",
            "contract-region-forwarding-dynamic-invocation-message=Meiya cannot establish the origin of this returned loan",
            "contract-region-forwarding-dynamic-invocation-source-path=contract-region-forwarding-dynamic.fk",
            "contract-region-forwarding-dynamic-invocation-range=346:373",
            "contract-region-forwarding-dynamic-rejected=true",
            "contract-region-forwarding-dynamic-silently-accepted=false",
            "contract-region-forwarding-callback-ty-diagnostics=1",
            "contract-region-forwarding-callback-mir-diagnostics=2",
            "contract-region-forwarding-callback-borrow-diagnostics=2",
            "contract-region-forwarding-callback-status=clean",
            "contract-region-forwarding-callback-invocation-diagnostic-count=1",
            "contract-region-forwarding-callback-invocation-message=call target is not callable",
            "contract-region-forwarding-callback-invocation-source-path=contract-region-forwarding-callback.fk",
            "contract-region-forwarding-callback-invocation-range=136:150",
            "contract-region-forwarding-callback-rejected=true",
            "contract-region-forwarding-callback-silently-accepted=false",
            "contract-region-forwarding-extern-ty-diagnostics=4",
            "contract-region-forwarding-extern-mir-diagnostics=4",
            "contract-region-forwarding-extern-borrow-diagnostics=5",
            "contract-region-forwarding-extern-status=blocked",
            "contract-region-forwarding-extern-invocation-diagnostic-count=1",
            "contract-region-forwarding-extern-invocation-message=Meiya cannot establish the origin of this returned loan",
            "contract-region-forwarding-extern-invocation-source-path=contract-region-forwarding-extern.fk",
            "contract-region-forwarding-extern-invocation-range=162:187",
            "contract-region-forwarding-extern-rejected=true",
            "contract-region-forwarding-extern-silently-accepted=false",
            "contract-region-forwarding-ffi-ty-diagnostics=3",
            "contract-region-forwarding-ffi-mir-diagnostics=5",
            "contract-region-forwarding-ffi-borrow-diagnostics=5",
            "contract-region-forwarding-ffi-ty-diag0=Meiya cannot store a lend in field choose of HookTable yet",
            "contract-region-forwarding-ffi-mir-diag0=Meiya cannot store a lend in field choose of HookTable yet",
            "contract-region-forwarding-ffi-borrow-diag0=Meiya cannot store a lend in field choose of HookTable yet",
            "contract-region-forwarding-ffi-status=clean",
            "contract-region-forwarding-ffi-invocation-diagnostic-count=1",
            "contract-region-forwarding-ffi-invocation-message=Meiya cannot forward borrowed values through an FFI callback yet",
            "contract-region-forwarding-ffi-invocation-source-path=contract-region-forwarding-ffi.fk",
            "contract-region-forwarding-ffi-invocation-range=198:222",
            "contract-region-forwarding-ffi-rejected=true",
            "contract-region-forwarding-ffi-silently-accepted=false",
            "contract-region-forwarding-closure-coverage=unsupported-no-borrowed-closure-contract",
        ),
        "contract_region_editor_smoke.fk": (
            "contract-region-editor-bound-semantic-name='out",
            "contract-region-editor-bound-semantic-kind=Lifetime",
            "contract-region-editor-bound-semantic-type=lifetime 'out on task shorten<'long:'out+'out,'out,'wide:'alt,'alt>(...) -> lend 'out Ship",
            "contract-region-editor-bound-semantic-def-matches-binder=true",
            "contract-region-editor-bound-hover-name='out",
            "contract-region-editor-bound-hover-kind=Lifetime",
            "contract-region-editor-bound-hover-type=lifetime 'out on task shorten<'long:'out+'out,'out,'wide:'alt,'alt>(...) -> lend 'out Ship",
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
            "location|contract-region-editor.fk|3|33|3|37|'out|Lifetime",
            "contract-region-editor-poison-before-restore-semantic=true",
            "contract-region-editor-poison-before-restore-hover=true",
            "contract-region-editor-poison-before-restore-definition=true",
            "contract-region-editor-poison-before-restore-all=true",
            "contract-region-editor-restored-semantic-facts-exact=true",
            "contract-region-editor-restored-hover-facts-exact=true",
            "contract-region-editor-restored-definition-facts-exact=true",
            "contract-region-editor-blocked-key-confirmed=true",
            "contract-region-editor-mismatched-key-confirmed=true",
            "contract-region-editor-syntax-key-promoted=true",
            "contract-region-editor-document-confirm-clean=true",
            "contract-region-editor-document-query-family-valid=true",
            "contract-region-editor-document-core-family-valid=true",
            "contract-region-editor-document-editor-family-valid=true",
            "contract-region-editor-document-semantic-family-valid=true",
            "contract-region-editor-document-hover-family-valid=true",
            "contract-region-editor-document-definition-family-valid=true",
            "contract-region-editor-restored-semantic-query-nonempty=true",
            "contract-region-editor-restored-hover-query-nonempty=true",
            "contract-region-editor-restored-definition-query-nonempty=true",
            "contract-region-editor-restored-repeated-definition-query-nonempty=true",
            "contract-region-editor-restored-alt-definition-query-nonempty=true",
            "contract-region-editor-restored-semantic-kind=Lifetime",
            "contract-region-editor-restored-semantic-type=lifetime 'out on task shorten<'long:'out+'out,'out,'wide:'alt,'alt>(...) -> lend 'out Ship",
            "contract-region-editor-restored-semantic-def-stable=true",
            "contract-region-editor-restored-semantic-value-stable=true",
            "contract-region-editor-restored-semantic-span-stable=true",
            "contract-region-editor-restored-hover-kind=Lifetime",
            "contract-region-editor-restored-hover-type=lifetime 'out on task shorten<'long:'out+'out,'out,'wide:'alt,'alt>(...) -> lend 'out Ship",
            "contract-region-editor-restored-hover-type-stable=true",
            "contract-region-editor-restored-hover-value-stable=true",
            "contract-region-editor-restored-definition-found=1",
            "contract-region-editor-restored-definition-span-stable=true",
            "contract-region-editor-restored-definition-value-stable=true",
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
            "contract-region-query-before-bound-definition=1",
           "contract-region-query-before-bound-definition-matches-out-binder=true",
            "contract-region-query-before-bound-semantic=lifetime 'out on task shorten<'long:'out,'out,'alt>(...) -> lend 'out Ship",
            "contract-region-query-before-bound-hover=lifetime 'out on task shorten<'long:'out,'out,'alt>(...) -> lend 'out Ship",
            "contract-region-query-bound-offset-stable=true",
            "ok|textDocument/didChange",
            "contract-region-query-query-invalidated=true",
            "contract-region-query-core-invalidated=true",
            "contract-region-query-syntax-invalidated=true",
            "contract-region-query-lex-invalidated=true",
            "contract-region-query-parse-invalidated=true",
            "contract-region-query-expand-invalidated=true",
            "contract-region-query-hir-invalidated=true",
            "contract-region-query-resolve-invalidated=true",
            "contract-region-query-ty-invalidated=true",
            "contract-region-query-mir-invalidated=true",
            "contract-region-query-borrowck-invalidated=true",
            "contract-region-query-diagnostics-invalidated=true",
            "contract-region-query-editor-invalidated=true",
            "contract-region-query-semantic-invalidated=true",
            "contract-region-query-hover-invalidated=true",
            "contract-region-query-definition-invalidated=true",
            "contract-region-query-document-symbols-invalidated=true",
            "contract-region-query-completion-invalidated=true",
            "contract-region-query-all-18-invalidations-positive=true",
            "contract-region-query-query-recomputed=true",
            "contract-region-query-core-recomputed=true",
            "contract-region-query-syntax-recomputed=true",
            "contract-region-query-lex-recomputed=true",
            "contract-region-query-parse-recomputed=true",
            "contract-region-query-expand-recomputed=true",
            "contract-region-query-hir-recomputed=true",
            "contract-region-query-resolve-recomputed=true",
            "contract-region-query-ty-recomputed=true",
            "contract-region-query-mir-recomputed=true",
            "contract-region-query-borrowck-recomputed=true",
            "contract-region-query-diagnostics-recomputed=true",
            "contract-region-query-editor-recomputed=true",
            "contract-region-query-semantic-recomputed=true",
            "contract-region-query-hover-recomputed=true",
            "contract-region-query-definition-recomputed=true",
            "contract-region-query-document-symbols-recomputed=true",
            "contract-region-query-completion-recomputed=true",
            "contract-region-query-all-18-recomputations-positive=true",
            "contract-region-query-after-diagnostics=1",
            "contract-region-query-after-message=Meiya refuses a returned loan from the wrong lifetime",
            "contract-region-query-after-status=blocked",
            "contract-region-query-after-source-count=1",
            "contract-region-query-after-long-outlives-out=false",
            "contract-region-query-after-long-outlives-alt=true",
            "contract-region-query-after-bound-definition=1",
           "contract-region-query-after-bound-definition-matches-alt-binder=true",
            "contract-region-query-after-bound-semantic=lifetime 'alt on task shorten<'long:'alt,'out,'alt>(...) -> lend 'out Ship",
            "contract-region-query-after-bound-hover=lifetime 'alt on task shorten<'long:'alt,'out,'alt>(...) -> lend 'out Ship",
            "contract-region-query-bound-definition-changed=true",
            "diagnostics|1",
        ),
        "contract_region_projected_holder_smoke.fk": (
            "contract-region-projected-holder-ty-diagnostics=0",
            "contract-region-projected-holder-mir-diagnostics=0",
            "contract-region-projected-holder-borrow-diagnostics=2",
            "contract-region-projected-holder-status=clean",
            "contract-region-projected-holder-chain-status=clean",
            "contract-region-projected-holder-owned-status=blocked",
            "contract-region-projected-holder-control-status=blocked",
            "contract-region-projected-holder-cycle-status=clean",
            "contract-region-projected-holder-source=fleet.ship",
            "contract-region-projected-holder-chain-source=fleet.ship",
            "contract-region-projected-holder-owned-diagnostics=2",
            "contract-region-projected-holder-opaque-diagnostics=0",
            "contract-region-projected-holder-cycle-source-count=1",
            "contract-region-projected-holder-cycle-source=fleet.ship",
            "contract-region-projected-holder-tuple-status=clean",
            "contract-region-projected-holder-array-status=clean",
            "contract-region-projected-holder-shape-status=clean",
            "contract-region-projected-holder-tuple-source=fleet.ship",
            "contract-region-projected-holder-array-source=fleet.ship",
            "contract-region-projected-holder-shape-source=fleet.ship",
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
            "contract-region-liveness-snapshot-format=freak-borrowck-snapshot-v2",
            "contract-region-liveness-snapshot-poisoned-before-restore=true",
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
            "contract-region-elided-query-before-loop-status=clean",
            "contract-region-elided-query-before-loop-source-count=2",
            "contract-region-elided-query-before-loop-source0=first",
            "contract-region-elided-query-before-loop-source1=second",
            "contract-region-elided-query-before-loop-converged=true",
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
            "contract-region-elided-query-ty-restore-poisoned=true",
            "contract-region-elided-query-ty-restore-slot-applied=true",
            "contract-region-elided-query-ty-restored-source-count=2",
            "contract-region-elided-query-ty-restored-source0=first",
            "contract-region-elided-query-ty-restored-source1=second",
            "contract-region-elided-query-ty-restored-source-order-stable=true",
            "contract-region-elided-query-ty-restore-cache-builds-added=1",
            "contract-region-elided-query-query-invalidations-added=15",
            "contract-region-elided-query-core-invalidations-added=10",
            "contract-region-elided-query-syntax-invalidations-added=1",
            "contract-region-elided-query-lex-invalidations-added=1",
            "contract-region-elided-query-parse-invalidations-added=1",
            "contract-region-elided-query-expand-invalidations-added=1",
            "contract-region-elided-query-hir-invalidations-added=1",
            "contract-region-elided-query-resolve-invalidations-added=1",
            "contract-region-elided-query-ty-invalidations-added=1",
            "contract-region-elided-query-mir-invalidations-added=1",
            "contract-region-elided-query-borrowck-invalidations-added=1",
            "contract-region-elided-query-diagnostics-invalidations-added=1",
            "contract-region-elided-query-editor-invalidations-added=5",
            "contract-region-elided-query-semantic-invalidations-added=1",
            "contract-region-elided-query-hover-invalidations-added=1",
            "contract-region-elided-query-definition-invalidations-added=1",
            "contract-region-elided-query-document-symbols-invalidations-added=1",
            "contract-region-elided-query-completion-invalidations-added=1",
            "contract-region-elided-query-all-18-invalidations-positive=true",
            "contract-region-elided-query-query-recomputations-added=15",
            "contract-region-elided-query-core-recomputations-added=10",
            "contract-region-elided-query-syntax-recomputations-added=1",
            "contract-region-elided-query-lex-recomputations-added=1",
            "contract-region-elided-query-parse-recomputations-added=1",
            "contract-region-elided-query-expand-recomputations-added=1",
            "contract-region-elided-query-hir-recomputations-added=1",
            "contract-region-elided-query-resolve-recomputations-added=1",
            "contract-region-elided-query-ty-recomputations-added=1",
            "contract-region-elided-query-mir-recomputations-added=1",
            "contract-region-elided-query-borrowck-recomputations-added=1",
            "contract-region-elided-query-diagnostics-recomputations-added=1",
            "contract-region-elided-query-editor-recomputations-added=5",
            "contract-region-elided-query-semantic-recomputations-added=1",
            "contract-region-elided-query-hover-recomputations-added=1",
            "contract-region-elided-query-definition-recomputations-added=1",
            "contract-region-elided-query-document-symbols-recomputations-added=1",
            "contract-region-elided-query-completion-recomputations-added=1",
            "contract-region-elided-query-all-18-recomputations-positive=true",
            "contract-region-elided-query-after-diagnostics=0",
            "contract-region-elided-query-after-message=none",
            "contract-region-elided-query-after-choose-status=clean",
            "contract-region-elided-query-after-loop-status=clean",
            "contract-region-elided-query-after-loop-source-count=1",
            "contract-region-elided-query-after-loop-source0=first",
            "contract-region-elided-query-after-loop-converged=true",
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
            "contract-region-resource-borrow-diagnostics=0",
            "contract-region-resource-diamond-status=clean",
            "contract-region-resource-loop-status=clean",
            "contract-region-resource-diamond-source-count=2",
            "contract-region-resource-diamond-source0=first",
            "contract-region-resource-diamond-source1=second",
            "contract-region-resource-loop-source-count=1",
            "contract-region-resource-loop-source0=source",
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
            "contract-region-resource-integer-intern-count=128",
            "contract-region-resource-integer-intern-capacity=128",
            "contract-region-resource-integer-intern-count-stable=true",
            "contract-region-resource-integer-cache-bounded=true",
            "contract-region-resource-integer-rebuild-correct=true",
            "contract-region-resource-canonical-path-cache-count=128",
            "contract-region-resource-canonical-path-cache-capacity=128",
            "contract-region-resource-canonical-path-cache-count-stable=true",
            "contract-region-resource-canonical-value-cache-count=128",
            "contract-region-resource-canonical-value-cache-capacity=128",
            "contract-region-resource-canonical-value-cache-count-stable=true",
            "contract-region-resource-canonical-path-cache-bounded=true",
            "contract-region-resource-canonical-path-rebuild-correct=true",
            "contract-region-resource-cache-evictions-observed=true",
            "contract-region-resource-hot-reuse-stable=true",
            "contract-region-resource-steady-integer-eviction-delta=0",
            "contract-region-resource-steady-path-eviction-delta=0",
            "contract-region-resource-steady-path-value-eviction-delta=0",
            "contract-region-resource-steady-state-evictions-stable=true",
            "contract-region-resource-no-historical-growth=true",
            "contract-region-resource-runtime-array-growth=true",
            "contract-region-resource-loop-semantics-stable=true",
            "contract-region-resource-fixed-point-converged=true",
            "contract-region-resource-fixed-point-rounds-bounded=true",
            "contract-region-resource-fixed-point-solves-positive=true",
            "contract-region-resource-fixed-point-work-bounded=true",
            "contract-region-resource-fixed-point-telemetry-stable=true",
            "contract-region-resource-bounds-opaque=true",
        ),
        "contract_region_body_derived_probe_smoke.fk": (
            "body-probe-parse-diagnostics=0",
            "body-probe-ty-diagnostics=0",
            "body-probe-mir-diagnostics=0",
            "body-probe-borrow-diagnostics=2",
            "body-probe-chain-two-hop=clean",
            "body-probe-holder-build-chain=clean",
            "body-probe-call-store-agg=clean",
            "body-probe-call-store-scalar-agg=clean",
            "body-probe-call-store-scalar=clean",
            "body-probe-call-in-ctor=clean",
            "body-probe-field-rebind-agg=clean",
            "body-probe-conditional-field-rebind=clean",
            "body-probe-nested-build=clean",
            "body-probe-inner-rebind=clean",
            "body-probe-chain-projected-agg=clean",
            "body-probe-branch-join=clean",
            "body-probe-loop-carried-local=clean",
            "body-probe-loop-param-rebind=clean",
            "body-probe-mixed-owned-leaf=blocked",
            "body-probe-branch-single-source=blocked",
            "body-probe-field-rebind-source0=fleet.ship",
            "body-probe-field-rebind-source-count=1",
            "body-probe-inner-rebind-source0=fleet.ship",
            "body-probe-inner-rebind-source-count=1",
            "body-probe-branch-join-source0=other",
            "body-probe-branch-join-source1=fleet.ship",
            "body-probe-branch-join-source-count=2",
            "body-probe-conditional-field-rebind-source0=view.lead",
            "body-probe-conditional-field-rebind-source1=fleet.ship",
            "body-probe-conditional-field-rebind-source-count=2",
            "body-probe-loop-param-rebind-source0=view.lead",
            "body-probe-loop-param-rebind-source1=fleet.ship",
            "body-probe-loop-param-rebind-source-count=2",
            "body-probe-owned-diagnostics=1",
            "body-probe-unproven-diagnostics=1",
        ),
    }
    if v4_check_harness_return.exists():
        harness_smokes, harness_errors = _literal_executable_smokes(v4_check_harness_return)
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
            if fixture not in harness_smokes:
                contract_region_missing.append(f"EXECUTABLE_SMOKES: {fixture} entry missing")
        for fixture in harness_smokes:
            if fixture.startswith("contract_region_") and fixture not in required_harness_expects:
                contract_region_missing.append(
                    f"EXECUTABLE_SMOKES: {fixture} has no literal contract-region oracle"
                )
        contract_region_explicit_strict = (
            "lend_return_query_invalidation_smoke.fk",
            "named_lifetime_editor_smoke.fk",
        )
        contract_region_missing.extend(
            _explicit_strict_smoke_errors(
                harness_smokes, contract_region_explicit_strict
            )
        )
        for fixture, smoke in harness_smokes.items():
            if not fixture.startswith("contract_region_"):
                continue
            if smoke.expect_mode != "line":
                contract_region_missing.append(
                    f"EXECUTABLE_SMOKES: {fixture} expect_mode must be 'line'"
                )
            if smoke.expect_unique is not True:
                contract_region_missing.append(
                    f"EXECUTABLE_SMOKES: {fixture} expect_unique must be true"
                )
            if smoke.expect_exact:
                contract_region_missing.append(
                    f"EXECUTABLE_SMOKES: {fixture} must keep every exact line in expect"
                )
        for fixture, required_expects in required_harness_expects.items():
            smoke = harness_smokes.get(fixture)
            if smoke is None:
                continue
            if fixture.startswith("contract_region_"):
                if smoke.expect != required_expects:
                    contract_region_missing.append(
                        f"EXECUTABLE_SMOKES: {fixture} expectation list does not exactly match the auditor oracle"
                    )
                continue
            for expected in required_expects:
                if expected not in smoke.expect and expected not in smoke.expect_exact:
                    contract_region_missing.append(
                        f"EXECUTABLE_SMOKES: {fixture} missing expected value {expected!r}"
                    )

        stale_exact_one_expectations = (
            "Meiya cannot choose one source for this returned loan",
            "name one source before returning the loan",
        )
        for fixture, smoke in harness_smokes.items():
            for expected in smoke.expect + smoke.expect_exact:
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
        "V4 contract regions",
        not contract_region_missing,
        "source sets + local fixed aggregates + Meiya/editor/tooling smokes wired" if not contract_region_missing else f"{len(contract_region_missing)} gap(s)",
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
            "v4_borrowck_local_initially_initialized",
            "v4_borrowck_local_state_after_block",
            "v4_borrowck_local_moved_on_any_exit",
            "v4_borrowck_local_has_exit_state",
            "v4_borrowck_enqueue_drop_state",
            "v4_borrowck_path_drop_if",
            "v4_borrowck_drop_state_index",
            "v4_borrowck_mark_seen_index",
            "array_release(seen)",
            "terminator != v4_mir_term_unreachable",
            "v4_borrowck_path_exact_local",
            "v4_borrowck_stmt_has_exact_local_path",
        ):
            if needle not in borrowck_src:
                drop_flag_missing.append(f"freak_borrowck: {needle}")
    else:
        drop_flag_missing.append("freak_borrowck/src/lib.fk missing")
    if v4_mir_lib_return.exists():
        mir_src = v4_mir_lib_return.read_text(encoding="utf-8")
        if mir_src.count("pilot loop_entry_block = v4_mir_add_block") < 2:
            drop_flag_missing.append("freak_mir: repeat/training loop preheaders")
        for needle in (
            "count_block, condition_block",
            "body_tail, condition_block",
            "iterable_block, loop_header",
            "body_tail, loop_header",
        ):
            if needle not in mir_src:
                drop_flag_missing.append(f"freak_mir: loop split {needle}")
    else:
        drop_flag_missing.append("freak_mir/src/lib.fk missing")
    if v4_drop_order_smoke.exists():
        smoke_src = v4_drop_order_smoke.read_text(encoding="utf-8")
        for needle in (
            "moved_local",
            "move_reassign",
            "branch_moved",
            "branch_partial",
            "branch_reinit",
            "branch_merge_reinit",
            "branch_declared_local",
            "loop_before_move",
            "loop_moves_inside",
            "loop_reinit_after_move",
            "loop_declared_local",
            "route_branch_moved",
            "drop-moved-count=",
            "drop-reinit-count=",
            "drop-move-reassign-count=",
            "drop-branch-moved-count=",
            "drop-branch-partial-count=",
            "drop-branch-partial-if-count=",
            "drop-branch-reinit-if-count=",
            "drop-branch-declared-local-if-count=",
            "drop-loop-before-move-count=",
            "drop-loop-moves-inside-if-count=",
            "drop-loop-declared-local-if-count=",
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
        if "drop-branch-merge-reinit-if-count=0" not in harness_src:
            drop_flag_missing.append("check_v4.py: branch merge reinit drop expectation")
        if "drop-branch-declared-local-if-count=1" not in harness_src:
            drop_flag_missing.append("check_v4.py: branch-local initialization expectation")
        if "drop-loop-before-move-count=1" not in harness_src:
            drop_flag_missing.append("check_v4.py: loop-backedge drop expectation")
        if "drop-loop-moves-inside-if-count=1" not in harness_src:
            drop_flag_missing.append("check_v4.py: loop move DropIf expectation")
        if "drop-loop-reinit-after-move-if-count=1" not in harness_src:
            drop_flag_missing.append("check_v4.py: loop reinit DropIf expectation")
        if "drop-loop-declared-local-if-count=1" not in harness_src:
            drop_flag_missing.append("check_v4.py: loop-local initialization expectation")
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
            "v4_borrowck_call_is_shared_borrow_with_receiver",
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
            "return_borrow_view",
            "shared-weak-guard-escape-diagnostics=",
            "shared-weak-view-escape-diagnostics=",
        ):
            if needle not in smoke_src:
                shared_weak_missing.append(f"shared_weak_smoke: {needle}")
    else:
        shared_weak_missing.append("smoke fixture: shared_weak_smoke.fk")
    if v4_check_harness_return.exists():
        shared_smokes, shared_manifest_errors = _literal_executable_smokes(
            v4_check_harness_return
        )
        shared_weak_missing.extend(shared_manifest_errors)
        shared_weak_missing.extend(
            _explicit_strict_smoke_errors(
                shared_smokes, ("shared_weak_smoke.fk",)
            )
        )
    else:
        shared_weak_missing.append("check_v4.py harness missing")
    add(
        "V4 Shared/Weak",
        not shared_weak_missing,
        "TY/MIR Shared/Weak method surface plus weak-borrow and guard-escape diagnostics wired" if not shared_weak_missing else f"{len(shared_weak_missing)} gap(s)",
    )
    if shared_weak_missing:
        failures.append("V4 Shared/Weak ownership surface regressed: " + "; ".join(shared_weak_missing))

    # Check 14: V4 unit snapshot restore integrity
    unit_snapshot_integrity_missing: List[str] = []
    v4_unit_snapshot_smoke = (
        repo / "src" / "compiler" / "v4" / "tests" / "unit_snapshot_smoke.fk"
    )
    v4_unit_snapshot_resource_smoke = (
        repo
        / "src"
        / "compiler"
        / "v4"
        / "tests"
        / "unit_snapshot_multisource_resource_smoke.fk"
    )
    v4_snapshot_lib = (
        repo
        / "src"
        / "compiler"
        / "v4"
        / "crates"
        / "freak_snapshot"
        / "src"
        / "lib.fk"
    )
    v4_mir_snapshot_resource_smoke = (
        repo / "src" / "compiler" / "v4" / "tests" / "mir_snapshot_resource_smoke.fk"
    )
    v4_query_invalidation_resource_smoke = (
        repo
        / "src"
        / "compiler"
        / "v4"
        / "tests"
        / "query_invalidation_resource_smoke.fk"
    )
    v4_mir_snapshot_lib = (
        repo / "src" / "compiler" / "v4" / "crates" / "freak_mir" / "src" / "lib.fk"
    )
    v4_query_resource_lib = (
        repo / "src" / "compiler" / "v4" / "crates" / "freak_query" / "src" / "lib.fk"
    )
    if v4_unit_snapshot_smoke.exists():
        unit_snapshot_src = v4_unit_snapshot_smoke.read_text(encoding="utf-8")
        for needle in _UNIT_SNAPSHOT_INTEGRITY_STRUCTURAL_NEEDLES:
            if needle not in unit_snapshot_src:
                unit_snapshot_integrity_missing.append(
                    f"unit_snapshot_smoke: {needle}"
                )
    else:
        unit_snapshot_integrity_missing.append(
            "smoke fixture: unit_snapshot_smoke.fk"
        )
    if v4_unit_snapshot_resource_smoke.exists():
        resource_src = v4_unit_snapshot_resource_smoke.read_text(encoding="utf-8")
        for needle in (
            "v4_unit_snapshot_multisource_expected = 192",
            "v4_unit_snapshot_validate",
            "v4_unit_snapshot_manifest",
            "v4_unit_snapshot_diff",
            "v4_unit_snapshot_health",
        ):
            if needle not in resource_src:
                unit_snapshot_integrity_missing.append(
                    f"unit_snapshot_multisource_resource_smoke: {needle}"
                )
    else:
        unit_snapshot_integrity_missing.append(
            "smoke fixture: unit_snapshot_multisource_resource_smoke.fk"
        )
    if v4_snapshot_lib.exists():
        snapshot_src = v4_snapshot_lib.read_text(encoding="utf-8")
        for needle in (
            "v4_unit_snapshot_word_array_count",
            "v4_unit_snapshot_collect_source_index",
            "v4_unit_snapshot_source_index_line_by_path",
        ):
            if needle not in snapshot_src:
                unit_snapshot_integrity_missing.append(f"freak_snapshot: {needle}")
        if "pilot earlier_line_id" in snapshot_src:
            unit_snapshot_integrity_missing.append(
                "freak_snapshot: quadratic prior-source rescan"
            )
    else:
        unit_snapshot_integrity_missing.append("freak_snapshot/src/lib.fk missing")
    for fixture_path, fixture_name, needles in (
        (
            v4_mir_snapshot_resource_smoke,
            "mir_snapshot_resource_smoke",
            (
                "v4_mir_snapshot_resource_iterations >= 64",
                "v4_mir_snapshot_validate",
                "v4_mir_snapshot_resource_cycle_iterations >= 64",
                "mir-snapshot-resource-cycles-rejected=",
                "mir-snapshot-resource-array-probe=",
                "mir-snapshot-resource-handle-capacity-bounded=",
                "mir-snapshot-resource-handle-capacity-stable=",
            ),
        ),
        (
            v4_query_invalidation_resource_smoke,
            "query_invalidation_resource_smoke",
            (
                "v4_query_invalidation_resource_changes >= 96",
                "v4_query_invalidation_resource_direct >= 600",
                "query-invalidation-resource-array-probe=",
                "query-invalidation-resource-handle-capacity-bounded=",
                "query-invalidation-resource-handle-capacity-stable=",
            ),
        ),
    ):
        if fixture_path.exists():
            fixture_src = fixture_path.read_text(encoding="utf-8")
            for needle in needles:
                if needle not in fixture_src:
                    unit_snapshot_integrity_missing.append(
                        f"{fixture_name}: {needle}"
                    )
        else:
            unit_snapshot_integrity_missing.append(
                f"smoke fixture: {fixture_path.name}"
            )
    if v4_mir_snapshot_lib.exists():
        mir_snapshot_src = v4_mir_snapshot_lib.read_text(encoding="utf-8")
        for needle in (
            "v4_mir_snapshot_release_body_graph_arrays",
            "array_release(states)",
            "array_release(v4_mir_loop_break_targets)",
            "array_release(v4_mir_scope_spans)",
        ):
            if needle not in mir_snapshot_src:
                unit_snapshot_integrity_missing.append(f"freak_mir: {needle}")
    else:
        unit_snapshot_integrity_missing.append("freak_mir/src/lib.fk missing")
    if v4_query_resource_lib.exists():
        query_resource_src = v4_query_resource_lib.read_text(encoding="utf-8")
        for needle in ("array_release(seen)", "array_release(work)"):
            if needle not in query_resource_src:
                unit_snapshot_integrity_missing.append(f"freak_query: {needle}")
    else:
        unit_snapshot_integrity_missing.append("freak_query/src/lib.fk missing")
    if v4_check_harness_return.exists():
        check_harness_src = v4_check_harness_return.read_text(encoding="utf-8")
        for needle in (
            "C_ARRAY_HANDLE_RESOURCE_LIMIT = 1024",
            "-DFREAK_ARRAY_LIVE_LIMIT=",
            "mir_snapshot_resource_smoke.fk",
            "query_invalidation_resource_smoke.fk",
        ):
            if needle not in check_harness_src:
                unit_snapshot_integrity_missing.append(f"check_v4.py: {needle}")
        runtime_resource_path = repo / "freakc" / "runtime" / "freak_runtime.c"
        if runtime_resource_path.exists():
            runtime_resource_src = runtime_resource_path.read_text(encoding="utf-8")
            if "FREAK_ARRAY_LIVE_LIMIT" not in runtime_resource_src:
                unit_snapshot_integrity_missing.append(
                    "freak_runtime.c: FREAK_ARRAY_LIVE_LIMIT"
                )
        else:
            unit_snapshot_integrity_missing.append("freak_runtime.c missing")
        snapshot_smokes, snapshot_manifest_errors = _literal_executable_smokes(
            v4_check_harness_return
        )
        unit_snapshot_integrity_missing.extend(snapshot_manifest_errors)
        unit_snapshot_integrity_missing.extend(
            _explicit_strict_smoke_errors(
                snapshot_smokes,
                (
                    "unit_snapshot_smoke.fk",
                    "unit_snapshot_multisource_resource_smoke.fk",
                    "mir_snapshot_resource_smoke.fk",
                    "query_invalidation_resource_smoke.fk",
                ),
            )
        )
    else:
        unit_snapshot_integrity_missing.append("check_v4.py harness missing")
    add(
        "V4 unit snapshot integrity",
        not unit_snapshot_integrity_missing,
        "atomic restore plus bounded snapshot and invalidation scratch resources wired"
        if not unit_snapshot_integrity_missing
        else f"{len(unit_snapshot_integrity_missing)} gap(s)",
    )
    if unit_snapshot_integrity_missing:
        failures.append(
            "V4 unit snapshot integrity regressed: "
            + "; ".join(unit_snapshot_integrity_missing)
        )

    # Check 15: V4 training arc growth checks
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

    # Check 16: V4 alias nominality for doctrine impl targets
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

    # Check 17: V4 dyn Doctrine semantic/editor surface
    # This is intentionally a semantic/query guard, not a vtable-codegen claim.
    dyn_doctrine_missing: List[str] = []
    v4_lex_dyn = repo / "src" / "compiler" / "v4" / "crates" / "freak_lex" / "src" / "lib.fk"
    v4_ty_dyn = repo / "src" / "compiler" / "v4" / "crates" / "freak_ty" / "src" / "lib.fk"
    v4_mir_dyn = repo / "src" / "compiler" / "v4" / "crates" / "freak_mir" / "src" / "lib.fk"
    v4_borrowck_dyn = repo / "src" / "compiler" / "v4" / "crates" / "freak_borrowck" / "src" / "lib.fk"
    v4_editor_dyn = repo / "src" / "compiler" / "v4" / "crates" / "freak_editor" / "src" / "lib.fk"
    v4_dyn_ty_smoke = repo / "src" / "compiler" / "v4" / "tests" / "dyn_doctrine_ty_smoke.fk"
    v4_dyn_mir_smoke = repo / "src" / "compiler" / "v4" / "tests" / "mir_dyn_doctrine_smoke.fk"
    v4_dyn_mir_generic_smoke = repo / "src" / "compiler" / "v4" / "tests" / "mir_dyn_doctrine_generic_smoke.fk"
    v4_dyn_mir_shared_smoke = repo / "src" / "compiler" / "v4" / "tests" / "mir_dyn_doctrine_shared_smoke.fk"
    v4_dyn_mir_diagnostics_smoke = repo / "src" / "compiler" / "v4" / "tests" / "mir_dyn_doctrine_diagnostics_smoke.fk"
    v4_dyn_lend_erasure_smoke = repo / "src" / "compiler" / "v4" / "tests" / "dyn_doctrine_lend_erasure_smoke.fk"
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
    if v4_borrowck_dyn.exists():
        borrowck_src = v4_borrowck_dyn.read_text(encoding="utf-8")
        for needle in (
            "task v4_borrowck_check_dyn_lend_erasure",
            "Meiya cannot erase a lend-bearing value into a dyn doctrine yet",
        ):
            if needle not in borrowck_src:
                dyn_doctrine_missing.append(f"freak_borrowck: {needle}")
    else:
        dyn_doctrine_missing.append("freak_borrowck/src/lib.fk missing")
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
    if v4_dyn_lend_erasure_smoke.exists():
        smoke_src = v4_dyn_lend_erasure_smoke.read_text(encoding="utf-8")
        for needle in (
            "pilot erased: dyn Widget = view",
            "dyn-lend-erasure-mir-rejected=",
            "dyn-lend-erasure-borrow-rejected=",
        ):
            if needle not in smoke_src:
                dyn_doctrine_missing.append(f"dyn_doctrine_lend_erasure_smoke: {needle}")
    else:
        dyn_doctrine_missing.append("smoke fixture: dyn_doctrine_lend_erasure_smoke.fk")
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
            "dyn_doctrine_lend_erasure_smoke.fk",
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

    # Check 18: V4 direct recursive shape/variant rejection
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
            "type-recursion-generic-growth-ty-diagnostics=3",
            "type-recursion-generic-growth-diag0=Meiya's lend-storage analysis exhausted its depth budget",
            "type-recursion-generic-growth-diag0-span=4@26:39",
            "type-recursion-generic-growth-diag1=Meiya's lend-storage analysis exhausted its depth budget",
            "type-recursion-generic-growth-diag1-span=4@64:76",
            "type-recursion-generic-growth-diag2=Yuuko infinite shape: Wrap contains itself by value via Wrap -> Wrap",
            "type-recursion-generic-growth-diag2-span=4@26:39",
            "type-recursion-generic-growth-mir-diagnostics=3",
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
