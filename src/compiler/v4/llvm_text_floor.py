"""The oldest LLVM the V4 text backend supports, and a guard that keeps it so.

V4 writes textual LLVM IR and hands it to Clang. The text uses opaque `ptr`
types, which Clang 15 is the first release to accept by default, and
LLVM 17 and later accept nothing else. So the supported range starts at 15
and the module must never use typed pointers (`i8*`) or syntax that only a
newer LLVM parses. `freak doctor` checks the same floor
(CLI_DOCTOR_MINIMUM_CLANG_MAJOR in src/cli/doctor.fk).

Measured on 2026-11-23: all 50 modules V4 emits for src/compiler/v4/examples
compile with Clang 15.0.7, 16.0.6, 17.0.6, 18.1.3, 19.1.7 and 20.1.2, and
the 48 programs that link without extra C fixtures run with identical
stdout, stderr and exit status.
LLVM 14.0.6 rejects the modules (`ptr type is only supported in
-opaque-pointers mode`). Rerun with benchmarks/v4/llvm_major_matrix.py.
"""
from __future__ import annotations

import re

MIN_LLVM_MAJOR = 15

# Syntax newer than MIN_LLVM_MAJOR, as (pattern, first major, description).
# Patterns run on module text with string constants, quoted names and
# comments removed, so a word or name that spells one never matches.
NEWER_SYNTAX: tuple[tuple[str, int, str], ...] = (
    (r"\bmemory\(", 16, "memory(...) effects attribute"),
    (r"\bnofpclass\(", 16, "nofpclass attribute"),
    (r"\bzext\s+nneg\b", 18, "zext nneg"),
    (r"\bor\s+disjoint\b", 18, "or disjoint"),
    (r"\bwritable\b", 18, "writable attribute"),
    (r"\bdead_on_unwind\b", 18, "dead_on_unwind attribute"),
    (r"\buitofp\s+nneg\b", 19, "uitofp nneg"),
    (r"\btrunc\s+(?:nuw|nsw)\b", 19, "trunc nuw/nsw"),
    (r"\bgetelementptr\s+(?:inbounds\s+)?(?:nusw|nuw)\b", 19, "getelementptr nusw/nuw"),
    (r"\brange\(", 19, "range(...) attribute"),
    (r"\binitializes\(", 19, "initializes(...) attribute"),
    (r"\bsplat\s*\(", 19, "splat (...) constant"),
    (r"\bicmp\s+samesign\b", 20, "icmp samesign"),
    (r"\bcaptures\(", 21, "captures(...) attribute"),
)

# Typed pointers: a type followed by `*`. LLVM 17 removed them.
TYPED_POINTER = re.compile(r'(?:\bi\d+|\bvoid|\bdouble|\bfloat|\bhalf|\bptr|%[-\w.$]+|"|[)}\]>])\s*\*')

_STRING = re.compile(r'c?"[^"\n]*"')
_COMMENT = re.compile(r";[^\n]*")


def scrub(module: str) -> str:
    """Module text without string constants, quoted names or comments."""
    return _COMMENT.sub("", _STRING.sub('""', module))


def text_floor_problems(module: str) -> list[str]:
    """Every construct that would break a Clang at MIN_LLVM_MAJOR or newer."""
    text = scrub(module)
    problems: list[str] = []
    for pattern, major, description in NEWER_SYNTAX:
        if re.search(pattern, text):
            problems.append(f"{description} needs LLVM {major}, the floor is {MIN_LLVM_MAJOR}")
    if TYPED_POINTER.search(text):
        problems.append("typed pointer type; LLVM 17 and later accept only opaque ptr")
    return problems


def require_text_floor(module: str, label: str) -> None:
    problems = text_floor_problems(module)
    if problems:
        raise RuntimeError(f"{label}: LLVM module leaves the supported range:\n  " + "\n  ".join(problems))


_CLANG_VERSION = re.compile(r"^(?:Apple |Ubuntu |Debian |Homebrew |FreeBSD )?clang version (\d+)\.", re.MULTILINE)


def clang_major(version_output: str) -> int | None:
    """Major version from `clang --version`, or None when unrecognised.

    Apple Clang numbers its own releases; Apple Clang 15 is based on LLVM 16,
    so the same floor of 15 holds for it."""
    match = _CLANG_VERSION.search(version_output)
    return int(match.group(1)) if match else None
