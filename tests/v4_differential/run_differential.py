#!/usr/bin/env python3
"""Run manifest-driven V3/V4 compile-phase differential checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA = "freak.v4.differential.v1"
FIXTURE_CATEGORIES = frozenset(
    {"compatible_positive", "syntax_negative", "type_negative", "intentional_difference"}
)
REQUIRED_FIXTURE_CATEGORIES = tuple(sorted(FIXTURE_CATEGORIES))
RELATIONSHIPS = frozenset({"equal", "v3_only", "v4_extension", "intentional_divergence"})
DIAGNOSTIC_CLASSES = frozenset(
    {"none", "lexical", "syntax", "hir", "resolve", "type", "ownership", "tool"}
)
RUNTIME_FIELDS = frozenset(
    {"runtime", "stdout", "stderr", "exit", "filesystem", "ownership", "values"}
)
V4_NATIVE_AVAILABLE = False
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
V4_PROBE_SCHEMA = "freak.v4.campaign-probe.v1"
V4_PROBE_DIAGNOSTICS = frozenset({"none", "lexical", "syntax", "hir", "resolve", "type"})
V4_PHASE_RE = re.compile(
    r"V4_PHASE\|tokens=\d+\|lex-diags=\d+\|parse-nodes=\d+"
    r"\|parse-diags=\d+\|hir-items=\d+\|hir-diags=\d+\|symbols=\d+"
    r"\|resolve-diags=\d+\|signatures=\d+\|ty-diags=\d+"
)

if not __debug__:
    raise SystemExit("run_differential.py requires assertions; do not run with python -O")


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "freakc").is_dir() and (parent / "src/compiler/v4").is_dir():
            return parent
    raise RuntimeError("could not locate repository root")


ROOT = repo_root()
HERE = Path(__file__).resolve().parent
CASES_ROOT = HERE / "cases"
PROBE = ROOT / "src/compiler/v4/tools/campaign_probe.py"
if str(PROBE.parent) not in sys.path:
    sys.path.insert(0, str(PROBE.parent))
from campaign_probe import (  # noqa: E402
    BoundedResult,
    run_bounded,
    stable_word_checksum,
    v4_host_mutex,
)


class ManifestError(ValueError):
    pass


@dataclass(frozen=True)
class CompilerObservation:
    accepted: bool
    diagnostic_class: str
    phase_summary: str
    deterministic: bool


def _expect_keys(value: dict[str, Any], expected: set[str], context: str) -> None:
    actual = set(value)
    if actual != expected:
        raise ManifestError(
            f"{context}: keys differ: missing={sorted(expected - actual)} "
            f"extra={sorted(actual - expected)}"
        )


def _validate_side(value: object, context: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ManifestError(f"{context}: expected object")
    _expect_keys(value, {"accepted", "diagnostic_class"}, context)
    if not isinstance(value["accepted"], bool):
        raise ManifestError(f"{context}.accepted: expected boolean")
    if (
        not isinstance(value["diagnostic_class"], str)
        or value["diagnostic_class"] not in DIAGNOSTIC_CLASSES
    ):
        raise ManifestError(f"{context}.diagnostic_class: unknown class")
    if value["accepted"] != (value["diagnostic_class"] == "none"):
        raise ManifestError(f"{context}: accepted must agree with diagnostic_class")
    return value


def load_manifest(path: Path) -> dict[str, object]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"could not read manifest: {exc}") from exc
    if not isinstance(document, dict):
        raise ManifestError("manifest root must be an object")
    _expect_keys(
        document, {"schema", "capabilities", "required_fixture_categories", "cases"}, "manifest"
    )
    if document["schema"] != SCHEMA:
        raise ManifestError(f"manifest schema must be {SCHEMA!r}")
    capabilities = document["capabilities"]
    if not isinstance(capabilities, dict):
        raise ManifestError("capabilities must be an object")
    _expect_keys(capabilities, {"v4_native"}, "capabilities")
    if not isinstance(capabilities["v4_native"], bool):
        raise ManifestError("capabilities.v4_native must be boolean")
    if capabilities["v4_native"] and not V4_NATIVE_AVAILABLE:
        raise ManifestError("v4_native was declared but this harness has no native V4 adapter")
    required_categories = document["required_fixture_categories"]
    if required_categories != list(REQUIRED_FIXTURE_CATEGORIES):
        raise ManifestError(
            "required_fixture_categories must be the canonical complete list "
            f"{list(REQUIRED_FIXTURE_CATEGORIES)!r}"
        )
    raw_cases = document["cases"]
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ManifestError("cases must be a non-empty list")
    seen_ids: set[str] = set()
    seen_sources: set[str] = set()
    normalized_cases: list[dict[str, object]] = []
    for index, raw_case in enumerate(raw_cases):
        context = f"cases[{index}]"
        if not isinstance(raw_case, dict):
            raise ManifestError(f"{context}: expected object")
        _expect_keys(
            raw_case,
            {
                "id",
                "fixture_category",
                "relationship",
                "source",
                "intentional_difference_reason",
                "requires_v4_native",
                "compare",
                "expect",
            },
            context,
        )
        case_id = raw_case["id"]
        source_name = raw_case["source"]
        fixture_category = raw_case["fixture_category"]
        relationship = raw_case["relationship"]
        if not isinstance(case_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", case_id):
            raise ManifestError(f"{context}.id: expected stable lowercase identifier")
        if case_id in seen_ids:
            raise ManifestError(f"{context}.id: duplicate {case_id!r}")
        seen_ids.add(case_id)
        if not isinstance(fixture_category, str) or fixture_category not in FIXTURE_CATEGORIES:
            raise ManifestError(f"{context}.fixture_category: unknown category")
        if not isinstance(relationship, str) or relationship not in RELATIONSHIPS:
            raise ManifestError(f"{context}.relationship: unknown relationship")
        reason = raw_case["intentional_difference_reason"]
        needs_reason = relationship != "equal"
        if not isinstance(reason, str) or bool(reason.strip()) != needs_reason:
            requirement = "non-empty" if needs_reason else "empty"
            raise ManifestError(f"{context}.intentional_difference_reason must be {requirement}")
        if not isinstance(source_name, str) or not source_name.endswith(".fk"):
            raise ManifestError(f"{context}.source: expected relative .fk path")
        source_path = (CASES_ROOT / source_name).resolve()
        try:
            source_path.relative_to(CASES_ROOT.resolve())
        except ValueError as exc:
            raise ManifestError(f"{context}.source escapes cases root") from exc
        if not source_path.is_file() or source_path.is_symlink():
            raise ManifestError(f"{context}.source must be a regular file")
        if source_name in seen_sources:
            raise ManifestError(f"{context}.source: duplicate {source_name!r}")
        seen_sources.add(source_name)
        requires_native = raw_case["requires_v4_native"]
        if not isinstance(requires_native, bool):
            raise ManifestError(f"{context}.requires_v4_native must be boolean")
        compare = raw_case["compare"]
        if not isinstance(compare, list) or compare != [
            "compile_acceptance",
            "diagnostic_class",
            "deterministic_phase_summary",
        ]:
            raise ManifestError(f"{context}.compare: unsupported comparison contract")
        runtime_requested = requires_native or bool(set(compare) & RUNTIME_FIELDS) or bool(
            set(raw_case) & RUNTIME_FIELDS
        )
        if runtime_requested and not capabilities["v4_native"]:
            raise ManifestError(f"{context}: runtime schema requires capabilities.v4_native=true")
        expect = raw_case["expect"]
        if not isinstance(expect, dict):
            raise ManifestError(f"{context}.expect: expected object")
        _expect_keys(expect, {"v3", "v4"}, f"{context}.expect")
        v3 = _validate_side(expect["v3"], f"{context}.expect.v3")
        v4 = _validate_side(expect["v4"], f"{context}.expect.v4")
        if relationship == "equal" and v3 != v4:
            raise ManifestError(f"{context}: equal relationship must expect equal observations")
        if relationship == "v3_only" and not (v3["accepted"] and not v4["accepted"]):
            raise ManifestError(f"{context}: v3_only expectations are inconsistent")
        if relationship == "v4_extension" and not (not v3["accepted"] and v4["accepted"]):
            raise ManifestError(f"{context}: v4_extension expectations are inconsistent")
        if relationship == "intentional_divergence" and v3 == v4:
            raise ManifestError(f"{context}: intentional_divergence must differ")
        if fixture_category == "compatible_positive" and not (
            relationship == "equal" and v3["accepted"] and v4["accepted"]
        ):
            raise ManifestError(f"{context}: compatible_positive must be equal and accepted")
        if fixture_category == "syntax_negative" and not (
            relationship == "equal"
            and not v3["accepted"]
            and v3["diagnostic_class"] == "syntax"
        ):
            raise ManifestError(f"{context}: syntax_negative must equally reject as syntax")
        if fixture_category == "type_negative" and not (
            relationship == "equal"
            and not v3["accepted"]
            and v3["diagnostic_class"] == "type"
        ):
            raise ManifestError(f"{context}: type_negative must equally reject as type")
        if fixture_category == "intentional_difference" and relationship == "equal":
            raise ManifestError(f"{context}: intentional_difference requires a differing relationship")
        normalized = dict(raw_case)
        normalized["source_path"] = source_path
        normalized_cases.append(normalized)
    observed_categories = {str(case["fixture_category"]) for case in normalized_cases}
    missing_categories = set(REQUIRED_FIXTURE_CATEGORIES) - observed_categories
    if missing_categories:
        raise ManifestError(
            f"required fixture categories have no cases: {sorted(missing_categories)}"
        )
    discovered = {
        path.relative_to(CASES_ROOT).as_posix()
        for path in CASES_ROOT.rglob("*.fk")
        if path.is_file()
    }
    if discovered != seen_sources:
        raise ManifestError(
            f"source inventory differs: missing={sorted(seen_sources - discovered)} "
            f"extra={sorted(discovered - seen_sources)}"
        )
    return {**document, "cases": normalized_cases}


def copy_adjacent_distribution(freak: Path, install: Path) -> Path:
    bin_dir = install / "bin"
    bin_dir.mkdir(parents=True)
    installed = bin_dir / freak.name
    shutil.copy2(freak, installed)
    manifest = ROOT / "packaging/distribution-files.manifest"
    for raw_line in manifest.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("|")
        if len(parts) != 2:
            raise RuntimeError(f"invalid distribution manifest row: {raw_line!r}")
        source = (ROOT / parts[0]).resolve()
        destination = (install / parts[1]).resolve()
        source.relative_to(ROOT.resolve())
        destination.relative_to(install.resolve())
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return installed


def _strip_ansi(value: str) -> str:
    return ANSI_RE.sub("", value).replace("\r\n", "\n").replace("\r", "\n")


def _strict_json_object(value: str) -> dict[str, object]:
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, item in pairs:
            if key in result:
                raise RuntimeError(f"V4 probe JSON duplicates key {key!r}")
            result[key] = item
        return result

    def reject_constant(constant: str) -> object:
        raise RuntimeError(f"V4 probe JSON contains non-finite number {constant}")

    try:
        payload = json.loads(
            value,
            object_pairs_hook=reject_duplicates,
            parse_constant=reject_constant,
        )
    except (json.JSONDecodeError, RuntimeError) as exc:
        raise RuntimeError(f"V4 probe returned invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("V4 probe JSON root must be an object")
    return payload


def _validate_v4_probe_payload(payload: dict[str, object], source_path: Path) -> None:
    expected_keys = {
        "schema",
        "adapter",
        "accepted",
        "diagnostic_class",
        "phase_summary",
        "deterministic",
        "source_sha256",
        "source_bytes",
        "source_checksum",
        "native_program_executed",
        "peak_memory_bytes",
    }
    if set(payload) != expected_keys:
        raise RuntimeError(
            f"V4 probe JSON keys differ: missing={sorted(expected_keys - set(payload))} "
            f"extra={sorted(set(payload) - expected_keys)}"
        )
    source_bytes = source_path.read_bytes()
    expected_digest = hashlib.sha256(source_bytes).hexdigest()
    if not isinstance(payload["schema"], str) or payload["schema"] != V4_PROBE_SCHEMA:
        raise RuntimeError("V4 probe schema is not the required version")
    if (
        not isinstance(payload["adapter"], str)
        or payload["adapter"] != "embedded-v4-frontend-through-ty"
    ):
        raise RuntimeError("V4 probe adapter is not the frontend-through-TY adapter")
    if type(payload["accepted"]) is not bool:
        raise RuntimeError("V4 probe accepted must be boolean")
    if (
        not isinstance(payload["diagnostic_class"], str)
        or payload["diagnostic_class"] not in V4_PROBE_DIAGNOSTICS
    ):
        raise RuntimeError("V4 probe diagnostic class is outside the compile-phase vocabulary")
    if payload["accepted"] != (payload["diagnostic_class"] == "none"):
        raise RuntimeError("V4 probe acceptance and diagnostic class disagree")
    if type(payload["deterministic"]) is not bool:
        raise RuntimeError("V4 probe deterministic must be boolean")
    if not isinstance(payload["phase_summary"], str) or V4_PHASE_RE.fullmatch(
        payload["phase_summary"]
    ) is None:
        raise RuntimeError("V4 probe phase summary is malformed")
    if not isinstance(payload["source_sha256"], str) or payload["source_sha256"] != expected_digest:
        raise RuntimeError("V4 probe source digest does not match the requested fixture")
    if type(payload["source_bytes"]) is not int or payload["source_bytes"] != len(source_bytes):
        raise RuntimeError("V4 probe source byte count does not match the requested fixture")
    if (
        type(payload["source_checksum"]) is not int
        or payload["source_checksum"] != stable_word_checksum(source_bytes)
    ):
        raise RuntimeError("V4 probe source checksum does not match the requested fixture")
    if payload["native_program_executed"] is not False:
        raise RuntimeError("V4 probe violated compile-phase-only contract")
    if type(payload["peak_memory_bytes"]) is not int or payload["peak_memory_bytes"] < 0:
        raise RuntimeError("V4 probe peak memory must be a nonnegative integer")


def _classify_v3(result: BoundedResult) -> CompilerObservation:
    output = _strip_ansi(result.stdout + result.stderr)
    lowered = output.lower()
    error_lines = sum(
        1 for line in output.splitlines() if line.strip().lower().startswith(("error:", "fatal:"))
    )
    if "type/borrow errors found" in lowered:
        diagnostic_class = "type"
    elif "syntax errors found" in lowered or error_lines > 0:
        diagnostic_class = "syntax"
    elif result.returncode != 0:
        diagnostic_class = "tool"
    else:
        diagnostic_class = "none"
    phases = []
    for marker in ("Lexing", "Parsing", "Type checking"):
        phases.append(f"{marker.lower().replace(' ', '-')}={'seen' if marker in output else 'missing'}")
    summary = "V3_PHASE|" + "|".join(phases) + f"|diagnostic-class={diagnostic_class}"
    return CompilerObservation(
        accepted=diagnostic_class == "none",
        diagnostic_class=diagnostic_class,
        phase_summary=summary,
        deterministic=True,
    )


def observe_v3(
    installed_freak: Path,
    source_path: Path,
    case_root: Path,
    *,
    timeout: int,
    memory_limit_mb: int,
    output_limit_mb: int,
) -> CompilerObservation:
    case_root.mkdir(parents=True)
    source = case_root / "input.fk"
    source.write_bytes(source_path.read_bytes())
    environment = os.environ.copy()
    environment.pop("FREAK_HOME", None)
    environment["NO_COLOR"] = "1"
    observations: list[CompilerObservation] = []
    for _ in range(2):
        result = run_bounded(
            [str(installed_freak), "check", str(source)],
            cwd=case_root,
            env=environment,
            timeout_seconds=timeout,
            memory_limit_mb=memory_limit_mb,
            output_limit_mb=output_limit_mb,
        )
        observations.append(_classify_v3(result))
    deterministic = observations[0] == observations[1]
    return CompilerObservation(**{**observations[0].__dict__, "deterministic": deterministic})


def observe_v4(
    source_path: Path,
    *,
    timeout: int,
    memory_limit_mb: int,
    output_limit_mb: int,
    clang: str | None,
) -> CompilerObservation:
    command = [
        sys.executable,
        "-u",
        str(PROBE),
        "--source",
        str(source_path),
        "--timeout",
        str(timeout),
        "--memory-limit-mb",
        str(memory_limit_mb),
        "--output-limit-mb",
        str(output_limit_mb),
    ]
    if clang:
        command.extend(["--clang", clang])
    environment = os.environ.copy()
    environment["FREAK_CAMPAIGN_MUTEX_HELD"] = "1"
    with v4_host_mutex(timeout_seconds=timeout):
        result = run_bounded(
            command,
            cwd=ROOT,
            env=environment,
            timeout_seconds=timeout * 3 + 30,
            memory_limit_mb=memory_limit_mb,
            output_limit_mb=output_limit_mb,
        )
    output_lines = result.stdout.splitlines()
    if len(output_lines) != 1:
        raise RuntimeError(
            f"V4 probe must return exactly one JSON line:\n{result.stdout}\n{result.stderr}"
        )
    payload = _strict_json_object(output_lines[0])
    if result.returncode != 0:
        if (
            set(payload) != {"schema", "adapter_error"}
            or payload.get("schema") != V4_PROBE_SCHEMA
            or not isinstance(payload.get("adapter_error"), str)
            or not payload["adapter_error"]
        ):
            raise RuntimeError("V4 probe failure payload is malformed")
        raise RuntimeError(f"V4 probe unavailable: {payload['adapter_error']}")
    if result.stderr:
        raise RuntimeError(f"V4 probe emitted unexpected stderr: {result.stderr[-2000:]}")
    _validate_v4_probe_payload(payload, source_path)
    return CompilerObservation(
        accepted=payload["accepted"],
        diagnostic_class=payload["diagnostic_class"],
        phase_summary=payload["phase_summary"],
        deterministic=payload["deterministic"],
    )


def _matches_expectation(observation: CompilerObservation, expected: dict[str, object]) -> bool:
    return (
        observation.accepted == expected["accepted"]
        and observation.diagnostic_class == expected["diagnostic_class"]
        and observation.deterministic
    )


def self_test(manifest_path: Path) -> None:
    document = load_manifest(manifest_path)
    assert len(document["cases"]) >= 4
    original = json.loads(manifest_path.read_text(encoding="utf-8"))

    def expect_manifest_rejection(rejected: dict[str, object], needle: str) -> None:
        path = schema_root / "cases.json"
        path.write_text(json.dumps(rejected), encoding="utf-8")
        try:
            load_manifest(path)
        except ManifestError as exc:
            assert needle in str(exc), (needle, str(exc))
        else:
            raise AssertionError(f"invalid manifest was accepted: {needle}")

    with tempfile.TemporaryDirectory(prefix="freak-differential-schema-") as temporary:
        schema_root = Path(temporary)
        rejected = json.loads(json.dumps(original))
        rejected["cases"][0]["requires_v4_native"] = True
        expect_manifest_rejection(rejected, "runtime schema requires")

        rejected = json.loads(json.dumps(original))
        rejected["required_fixture_categories"] = []
        expect_manifest_rejection(rejected, "canonical complete list")

        rejected = json.loads(json.dumps(original))
        rejected["cases"] = [
            case for case in rejected["cases"] if case["fixture_category"] != "type_negative"
        ]
        expect_manifest_rejection(rejected, "required fixture categories have no cases")

        rejected = json.loads(json.dumps(original))
        rejected["cases"][0]["relationship"] = "negative"
        expect_manifest_rejection(rejected, "unknown relationship")

        source = schema_root / "payload.fk"
        source.write_bytes(b"task main() {}\r\n")
        payload: dict[str, object] = {
            "schema": V4_PROBE_SCHEMA,
            "adapter": "embedded-v4-frontend-through-ty",
            "accepted": True,
            "diagnostic_class": "none",
            "phase_summary": (
                "V4_PHASE|tokens=6|lex-diags=0|parse-nodes=2|parse-diags=0|"
                "hir-items=1|hir-diags=0|symbols=1|resolve-diags=0|"
                "signatures=1|ty-diags=0"
            ),
            "deterministic": True,
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "source_bytes": len(source.read_bytes()),
            "source_checksum": stable_word_checksum(source.read_bytes()),
            "native_program_executed": False,
            "peak_memory_bytes": 1,
        }
        _validate_v4_probe_payload(payload, source)
        try:
            _strict_json_object('{"schema":1,"schema":2}')
        except RuntimeError as exc:
            assert "duplicates key" in str(exc)
        else:
            raise AssertionError("duplicate probe JSON key was accepted")
        payload["source_sha256"] = "0" * 64
        try:
            _validate_v4_probe_payload(payload, source)
        except RuntimeError as exc:
            assert "digest" in str(exc)
        else:
            raise AssertionError("forged probe source digest was accepted")
    assert _classify_v3(BoundedResult(("probe",), 0, "Lexing\nParsing\nType checking\n", "", 0)).accepted
    assert _classify_v3(BoundedResult(("probe",), 1, "FAILED -- syntax errors found\n", "", 0)).diagnostic_class == "syntax"
    print(
        f"differential manifest self-test: PASS cases={len(document['cases'])} "
        f"required-categories={len(REQUIRED_FIXTURE_CATEGORIES)}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("freak", nargs="?", type=Path, help="path to a V3 freak executable")
    parser.add_argument("--manifest", type=Path, default=HERE / "cases.json")
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--clang")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--memory-limit-mb", type=int, default=768)
    parser.add_argument("--output-limit-mb", type=int, default=4)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.timeout <= 0 or args.memory_limit_mb <= 0 or args.output_limit_mb <= 0:
        parser.error("time, memory, and output limits must all be positive")
    try:
        document = load_manifest(args.manifest.resolve())
        if args.self_test:
            self_test(args.manifest.resolve())
            return 0
        if args.freak is None or not args.freak.resolve().is_file():
            parser.error("freak must name an existing V3 executable")
        cases = document["cases"]
        selected_ids = set(args.case)
        if selected_ids:
            known_ids = {str(case["id"]) for case in cases}
            unknown = selected_ids - known_ids
            if unknown:
                raise ManifestError(f"unknown case filters: {sorted(unknown)}")
            cases = [case for case in cases if case["id"] in selected_ids]
        failures = 0
        with tempfile.TemporaryDirectory(prefix="freak-v3-v4-differential-") as temporary:
            root = Path(temporary)
            installed_freak = copy_adjacent_distribution(args.freak.resolve(), root / "v3-install")
            for index, case in enumerate(cases):
                v3 = observe_v3(
                    installed_freak,
                    case["source_path"],
                    root / "cases" / f"{index:03d}-{case['id']}" / "v3",
                    timeout=args.timeout,
                    memory_limit_mb=args.memory_limit_mb,
                    output_limit_mb=args.output_limit_mb,
                )
                v4 = observe_v4(
                    case["source_path"],
                    timeout=args.timeout,
                    memory_limit_mb=args.memory_limit_mb,
                    output_limit_mb=args.output_limit_mb,
                    clang=args.clang,
                )
                expected = case["expect"]
                ok = _matches_expectation(v3, expected["v3"]) and _matches_expectation(
                    v4, expected["v4"]
                )
                status = "PASS" if ok else "MISMATCH"
                reason = case["intentional_difference_reason"]
                print(
                    f"{status} {case['id']} category={case['fixture_category']} "
                    f"relationship={case['relationship']} "
                    f"v3={'accept' if v3.accepted else 'reject'}/{v3.diagnostic_class} "
                    f"v4={'accept' if v4.accepted else 'reject'}/{v4.diagnostic_class} "
                    f"phases=v3:{'stable' if v3.deterministic else 'drift'},"
                    f"v4:{'stable' if v4.deterministic else 'drift'}"
                    + (f" reason={reason}" if reason else "")
                )
                if not ok:
                    failures += 1
                    print(
                        "  expected="
                        + json.dumps(expected, sort_keys=True)
                        + " actual="
                        + json.dumps({"v3": v3.__dict__, "v4": v4.__dict__}, sort_keys=True)
                    )
        print(
            f"differential compile-phase summary: cases={len(cases)} "
            f"passed={len(cases) - failures} mismatches={failures} v4-native=0"
        )
        return 1 if failures else 0
    except (ManifestError, RuntimeError, OSError) as exc:
        print(f"differential harness failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
