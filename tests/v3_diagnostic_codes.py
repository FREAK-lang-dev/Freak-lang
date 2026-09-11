#!/usr/bin/env python3
"""V3 diagnostic codes foundation: stability, determinism, modes, eggs, data.

Pure-data suite: stdlib only, no Clang, no linker, no compiler build.
Run from the repo root: ``python -u tests/v3_diagnostic_codes.py``.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIAG_DIR = REPO_ROOT / "src" / "diagnostics"
PACKS_DIR = DIAG_DIR / "packs"

EXPECTED_CODES = (
    ("E0001", "unknown-binding", "Unknown binding"),
    ("E0002", "type-mismatch", "Type mismatch"),
    ("E0003", "use-after-move", "Use after move"),
    ("E0004", "immutable-reassignment", "Immutable reassignment"),
    ("E0005", "invalid-call", "Invalid call"),
    ("E0006", "index-out-of-bounds", "Index out of bounds"),
    ("E0007", "numeric-parse-failure", "Numeric parse failure"),
    ("E0008", "numeric-overflow", "Numeric overflow"),
    ("E0009", "allocation-failure", "Allocation failure"),
    ("E0010", "unsupported-target", "Unsupported target"),
)

EXPECTED_SPEAKERS = (
    "freak", "yuuko", "meiya", "hangar", "cockpit",
    "ministry", "llvm", "linker", "platform",
)

VALID_SOURCES = (
    "pilot x = 1",
    "task main() { say 42 }",
    "pilot name: word = \"ok\"",
)

_EXEC_MARKERS = ("__import__", "eval(", "exec(", "os.system", "subprocess", "compile(")


def _load_selector():
    spec = importlib.util.spec_from_file_location(
        "v3_diagnostic_selector", DIAG_DIR / "selector.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


selector = _load_selector()


class CodeStability(unittest.TestCase):
    def test_exact_code_table(self):
        payload = json.loads((DIAG_DIR / "codes.json").read_text(encoding="utf-8"))
        codes = payload["codes"]
        self.assertEqual(
            [(c["code"], c["slug"], c["title"]) for c in codes],
            list(EXPECTED_CODES),
        )
        self.assertEqual(selector.code_order(), [c for c, _, _ in EXPECTED_CODES])
        for entry in codes:
            self.assertTrue(selector.is_known_code(entry["code"]))
        self.assertFalse(selector.is_known_code("E9999"))

    def test_table_reload_is_stable(self):
        first = (DIAG_DIR / "codes.json").read_bytes()
        second = (DIAG_DIR / "codes.json").read_bytes()
        self.assertEqual(first, second)
        self.assertEqual(selector.load_codes(), selector.load_codes())


class Determinism(unittest.TestCase):
    KWARGS = dict(
        version="0.14.1", code="E0002", file="main.fk",
        line=7, column=3, source="pilot x: num = \"nope\"", speaker="YUUKO",
    )

    def test_same_input_same_line(self):
        first = selector.select_line(**self.KWARGS)
        for _ in range(100):
            self.assertEqual(selector.select_line(**self.KWARGS), first)

    def test_every_key_field_participates(self):
        base = selector.digest_hex(**self.KWARGS)
        mutations = dict(
            version="0.14.2", code="E0003", file="other.fk",
            line=8, column=4, source="pilot x = 1", speaker="MEIYA",
        )
        seen = {base}
        for field, value in mutations.items():
            probing = dict(self.KWARGS)
            probing[field] = value
            digest = selector.digest_hex(**probing)
            self.assertNotEqual(digest, base, field)
            seen.add(digest)
        self.assertEqual(len(seen), len(mutations) + 1)

    def test_index_matches_digest_mod_count(self):
        pack = selector.load_pack("YUUKO")
        digest = selector.digest_hex(**self.KWARGS)
        self.assertEqual(
            selector.select_index(**self.KWARGS),
            int(digest, 16) % len(pack["lines"]),
        )


class PresentationModes(unittest.TestCase):
    CANONICALS = (
        "type error: expected num, got word (line 7)",
        "",
        "borrowck: Shirogane. You gave this away. (line 3)\n --> main.fk:3:1",
        "日本語と絵文字 🎌 line",
        "trailing newline\n",
    )

    def test_off_leaves_canonical_byte_identical(self):
        for canonical in self.CANONICALS:
            out = selector.render(
                canonical, mode="off", version="0.14.1", code="E0002",
                file="main.fk", line=7, column=3,
                source="pilot x: num = \"nope\"", speaker="YUUKO",
            )
            self.assertEqual(out, canonical)
            self.assertEqual(out.encode("utf-8"), canonical.encode("utf-8"))

    def test_minimal_and_normal_keep_canonical_verbatim(self):
        canonical = "type error: expected num, got word (line 7)"
        minimal = selector.render(canonical, mode="minimal", **Determinism.KWARGS)
        normal = selector.render(canonical, mode="normal", **Determinism.KWARGS)
        for out, tag in ((minimal, "[E0002]"), (normal, "[E0002 YUUKO]")):
            self.assertTrue(out.startswith(canonical + "\n" + tag + " "))

    def test_bad_mode_rejected(self):
        with self.assertRaises(ValueError):
            selector.render("x", mode="verbose")

    def test_off_mode_performs_no_data_lookups(self):
        real_egg = selector.select_easter_egg
        real_line = selector.select_line
        real_resource = selector.select_resource

        def unexpected(*_args, **_kwargs):
            raise AssertionError("off mode must not consult presentation data")

        selector.select_easter_egg = unexpected
        selector.select_line = unexpected
        selector.select_resource = unexpected
        try:
            self.assertEqual(
                selector.render("canonical\nbytes", mode="off", code="E0009"),
                "canonical\nbytes",
            )
        finally:
            selector.select_easter_egg = real_egg
            selector.select_line = real_line
            selector.select_resource = real_resource

    def test_resource_line_is_normal_mode_only_for_allocation_failure(self):
        kwargs = dict(
            version="0.14.1", file="alloc.fk", line=4, column=2,
            source="reserve too much", speaker="FREAK",
        )
        minimal = selector.render("oom", mode="minimal", code="E0009", **kwargs)
        normal = selector.render("oom", mode="normal", code="E0009", **kwargs)
        other = selector.render("bounds", mode="normal", code="E0006", **kwargs)
        self.assertNotIn("[resource]", minimal)
        self.assertEqual(normal.count("[resource]"), 1)
        self.assertNotIn("[resource]", other)
        self.assertIn(normal.split("[resource] ", 1)[1], selector.load_resources())


class EasterEggs(unittest.TestCase):
    def test_eggs_fire_only_on_exact_invalid_source(self):
        eggs = selector.load_easter_eggs()
        self.assertGreaterEqual(len(eggs), 3)
        for egg in eggs:
            exact = egg["exact_source"]
            self.assertEqual(selector.select_easter_egg(exact, egg.get("code")), egg["line"])
            # Near-misses: never fire.
            for near in (exact + " ", " " + exact, exact.upper(), exact + "\n"):
                if near == exact:
                    continue
                self.assertIsNone(selector.select_easter_egg(near, egg.get("code")))

    def test_no_egg_for_valid_sources(self):
        eggs = selector.load_easter_eggs()
        egg_lines = {egg["line"] for egg in eggs}
        for source in VALID_SOURCES:
            self.assertIsNone(selector.select_easter_egg(source, "E0001"))
            self.assertIsNone(selector.select_easter_egg(source))
            for speaker in ("FREAK", "YUUKO", "MEIYA"):
                line = selector.select_line(
                    "0.14.1", "E0001", "main.fk", 1, 1, source, speaker
                )
                self.assertNotIn(line, egg_lines)
                rendered = selector.render(
                    "canonical", mode="normal", version="0.14.1",
                    code="E0001", file="main.fk", line=1, column=1,
                    source=source, speaker=speaker,
                )
                for egg_line in egg_lines:
                    self.assertNotIn(egg_line, rendered)

    def test_code_specific_egg_rejects_a_different_diagnostic_code(self):
        egg = next(item for item in selector.load_easter_eggs() if item["code"])
        different = next(code for code, _, _ in EXPECTED_CODES if code != egg["code"])
        self.assertIsNone(selector.select_easter_egg(egg["exact_source"], different))

    def test_code_agnostic_egg_accepts_any_failed_check(self):
        egg = next(item for item in selector.load_easter_eggs() if item["code"] is None)
        for code, _, _ in EXPECTED_CODES:
            self.assertEqual(
                selector.select_easter_egg(egg["exact_source"], code), egg["line"]
            )


class PacksAreData(unittest.TestCase):
    def test_all_json_parse_and_hold_data_only(self):
        files = [DIAG_DIR / "codes.json", DIAG_DIR / "easter_eggs.json", DIAG_DIR / "resources.json"]
        files += sorted(PACKS_DIR.glob("*.json"))
        self.assertGreaterEqual(len(files), 10)
        for path in files:
            with self.subTest(pack=path.name):
                payload = json.loads(path.read_text(encoding="utf-8"))
                self.assertIsInstance(payload, dict)
                self._assert_data_only(payload)
                text = path.read_text(encoding="utf-8")
                for marker in _EXEC_MARKERS:
                    self.assertNotIn(marker, text)

    def _assert_data_only(self, value, depth=0):
        self.assertLess(depth, 10)
        if isinstance(value, dict):
            for key, item in value.items():
                self.assertIsInstance(key, str)
                self._assert_data_only(item, depth + 1)
        elif isinstance(value, list):
            self.assertGreater(len(value), 0)
            for item in value:
                self._assert_data_only(item, depth + 1)
        elif isinstance(value, str):
            self.assertTrue(value.strip())
        elif isinstance(value, (int, float)) or value is None:
            pass
        else:
            self.fail("non-data value %r (%s)" % (value, type(value).__name__))

    def test_expected_speakers_and_nonempty_lines(self):
        stems = sorted(p.stem for p in PACKS_DIR.glob("*.json"))
        self.assertEqual(stems, sorted(EXPECTED_SPEAKERS))
        speakers = [s.lower() for s in selector.list_speakers()]
        self.assertEqual(sorted(speakers), sorted(EXPECTED_SPEAKERS))
        for stem in EXPECTED_SPEAKERS:
            pack = selector.load_pack(stem)
            self.assertGreaterEqual(len(pack["lines"]), 2)

    def test_no_existing_canonical_message_reused(self):
        canonical_fragments = (
            "You gave this away. It no longer belongs to you.",
            "This binding was sworn to silence. It cannot be reassigned.",
        )
        for path in PACKS_DIR.glob("*.json"):
            text = path.read_text(encoding="utf-8")
            for fragment in canonical_fragments:
                self.assertNotIn(fragment, text)

    def test_unknown_and_empty_speakers_fall_back_to_freak_pack(self):
        expected = selector.load_pack("FREAK")
        for speaker in ("DOES_NOT_EXIST", "", None):
            with self.subTest(speaker=speaker):
                self.assertEqual(selector.load_pack(speaker), expected)


class PlatformVoices(unittest.TestCase):
    KWARGS = dict(
        version="0.14.1", code="E0010", file="main.fk",
        line=1, column=1, source="pilot x = 1", speaker="PLATFORM",
    )

    def test_platform_subset_is_deterministic(self):
        first = selector.select_line(**self.KWARGS, platform="linux")
        for _ in range(50):
            self.assertEqual(selector.select_line(**self.KWARGS, platform="linux"), first)

    def test_platform_line_comes_from_subset(self):
        payload = json.loads((PACKS_DIR / "platform.json").read_text(encoding="utf-8"))
        for platform in ("linux", "macos", "windows"):
            line = selector.select_line(**self.KWARGS, platform=platform)
            self.assertIn(line, payload["platforms"][platform])

    def test_unknown_platform_falls_back_to_top_level(self):
        pack = selector.load_pack("PLATFORM")
        line = selector.select_line(**self.KWARGS, platform="plan9")
        self.assertIn(line, pack["lines"])

    def test_render_passes_platform_through(self):
        out = selector.render("boom", mode="normal", platform="linux", **self.KWARGS)
        payload = json.loads((PACKS_DIR / "platform.json").read_text(encoding="utf-8"))
        self.assertTrue(
            any(owned in out for owned in payload["platforms"]["linux"])
            or "[E0010 PLATFORM]" in out,
            out,
        )

    def test_empty_resources_raise(self):
        real = selector.load_resources
        selector.load_resources = lambda: []
        try:
            with self.assertRaises(ValueError):
                selector.select_resource("0.14.1", "E0009", "a.fk", 1, 1, "x")
        finally:
            selector.load_resources = real


if __name__ == "__main__":
    unittest.main(verbosity=2)
