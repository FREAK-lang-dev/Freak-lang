"""V3 diagnostic codes: deterministic cast selector (presentation only).

Data lives in JSON next to this module; this file only *selects* lines.
It never changes a canonical diagnostic: mode "off" returns the input
byte-identical, and the checker/emitter lanes keep owning canonical text.

Selection key (all fields, in order, NUL-joined, SHA-256):
    compiler_version + code + file + line + column + source + speaker
index = int(digest, 16) % len(pack lines). Same input -> same line.

Easter eggs fire ONLY on byte-exact match of the full source text against
a registered invalid source (see easter_eggs.json), and only as a
replacement cast line in minimal/normal mode. They are never consulted
in "off" mode and never fire for any other source.

Integration hook (deferred, owned by the lead): wire an opt-in
``--diagnostic-cast=<off|minimal|normal>`` CLI flag (default ``off``) at
the CLI dispatch boundary; keep checker/parser/emitter output canonical
and call ``render()`` as a post-pass presentation step only, passing the
compiler version plus the diagnostic code, file, line, column, source
text, and speaker. No checker/CLI flag parsing changes ship from this
lane.
"""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent
CODES_PATH = BASE_DIR / "codes.json"
PACKS_DIR = BASE_DIR / "packs"
EASTER_EGGS_PATH = BASE_DIR / "easter_eggs.json"
RESOURCES_PATH = BASE_DIR / "resources.json"

MODES = ("off", "minimal", "normal")

_FALLBACK_SPEAKER = "FREAK"


def _read_json(path: Path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def load_codes() -> Dict[str, dict]:
    """Return {code: entry} for E0001..E0010 in file order (stable)."""
    payload = _read_json(CODES_PATH)
    return {entry["code"]: entry for entry in payload["codes"]}


def code_order() -> List[str]:
    payload = _read_json(CODES_PATH)
    return [entry["code"] for entry in payload["codes"]]


def is_known_code(code: str) -> bool:
    return str(code).upper() in load_codes()


def list_speakers() -> List[str]:
    names = []
    for path in sorted(PACKS_DIR.glob("*.json")):
        names.append(path.stem.upper())
    return names


@lru_cache(maxsize=64)
def load_pack(speaker: str) -> Dict[str, list]:
    """Load one speaker pack; unknown speakers fall back to FREAK."""
    key = str(speaker or _FALLBACK_SPEAKER).upper()
    path = PACKS_DIR / (key.lower() + ".json")
    if not path.exists():
        path = PACKS_DIR / (_FALLBACK_SPEAKER.lower() + ".json")
        key = _FALLBACK_SPEAKER
    payload = _read_json(path)
    return {"speaker": payload.get("speaker", key), "lines": list(payload.get("lines", []))}


@lru_cache(maxsize=1)
def load_easter_eggs() -> List[dict]:
    return list(_read_json(EASTER_EGGS_PATH).get("eggs", []))


@lru_cache(maxsize=1)
def load_resources() -> List[str]:
    return list(_read_json(RESOURCES_PATH).get("lines", []))


def digest_hex(
    version: str,
    code: str,
    file: str,
    line: int,
    column: int,
    source: str,
    speaker: str,
) -> str:
    key = "\0".join(
        [str(version), str(code).upper(), str(file), str(int(line)), str(int(column)), str(source), str(speaker).upper()]
    )
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def select_index(version: str, code: str, file: str, line: int, column: int, source: str, speaker: str) -> int:
    pack = load_pack(speaker)
    count = len(pack["lines"])
    if count == 0:
        raise ValueError("speaker pack %r has no lines" % (speaker,))
    return int(digest_hex(version, code, file, line, column, source, speaker), 16) % count


def select_line(version: str, code: str, file: str, line: int, column: int, source: str, speaker: str) -> str:
    """Deterministically pick one cast line from the speaker pack."""
    pack = load_pack(speaker)
    return pack["lines"][select_index(version, code, file, line, column, source, speaker)]


def select_easter_egg(source: str, code: Optional[str] = None) -> Optional[str]:
    """Return the egg line only for a byte-exact invalid-source match.

    ``code`` narrows the match when the egg names one; eggs with a null
    code match any failed check. Every other source returns None —
    including near-misses that differ by whitespace or case.
    """
    for egg in load_easter_eggs():
        if source != egg.get("exact_source"):
            continue
        wanted = egg.get("code")
        if wanted is not None and code is not None and str(code).upper() != str(wanted).upper():
            continue
        return egg.get("line")
    return None


def select_resource(version: str, code: str, file: str, line: int, column: int, source: str) -> str:
    lines = load_resources()
    key = "\0".join([str(version), str(code).upper(), str(file), str(int(line)), str(int(column)), str(source), "RESOURCES"])
    return lines[int(hashlib.sha256(key.encode("utf-8")).hexdigest(), 16) % len(lines)]


def validate_mode(mode: str) -> str:
    normalized = str(mode).lower()
    if normalized not in MODES:
        raise ValueError("mode must be one of %r, got %r" % (MODES, mode))
    return normalized


def render(
    canonical: str,
    *,
    mode: str = "off",
    version: str = "0.0.0",
    code: str = "E0001",
    file: str = "<unknown>",
    line: int = 0,
    column: int = 0,
    source: str = "",
    speaker: str = "FREAK",
) -> str:
    """Present a canonical diagnostic with an optional cast line.

    - ``off``: return ``canonical`` byte-identical (no lookup side effects
      leak into the output).
    - ``minimal``: ``canonical`` + ``\\n[<CODE>] <cast line>``.
    - ``normal``: ``canonical`` + ``\\n[<CODE> <SPEAKER>] <cast line>`` and,
      for E0009 only, a second deterministic resource line.
    An exact-invalid-source easter egg replaces the pack line in
    minimal/normal mode; it never appears in ``off`` mode.
    """
    mode = validate_mode(mode)
    if mode == "off":
        return canonical
    code = str(code).upper()
    egg = select_easter_egg(source, code)
    cast = egg if egg is not None else select_line(version, code, file, line, column, source, speaker)
    tag = code if mode == "minimal" else "%s %s" % (code, str(speaker).upper())
    out = "%s\n[%s] %s" % (canonical, tag, cast)
    if mode == "normal" and code == "E0009":
        out += "\n[resource] %s" % select_resource(version, code, file, line, column, source)
    return out


__all__ = [
    "MODES",
    "load_codes",
    "code_order",
    "is_known_code",
    "list_speakers",
    "load_pack",
    "load_easter_eggs",
    "load_resources",
    "digest_hex",
    "select_index",
    "select_line",
    "select_easter_egg",
    "select_resource",
    "validate_mode",
    "render",
]
