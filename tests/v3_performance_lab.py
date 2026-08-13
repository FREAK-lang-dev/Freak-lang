#!/usr/bin/env python3
"""Static and executable acceptance checks for the V3 performance lab."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "v3_performance_lab.py"
MANIFEST = ROOT / "benchmarks" / "v3" / "manifest.json"


def _load_tool() -> Any:
    specification = importlib.util.spec_from_file_location("freak_v3_performance_lab", TOOL)
    if specification is None or specification.loader is None:
        raise AssertionError(f"cannot import {TOOL}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


LAB = _load_tool()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _expect_lab_error(action: Callable[[], Any], message: str) -> None:
    try:
        action()
    except LAB.LabError:
        return
    raise AssertionError(message)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _static_checks(temporary: Path) -> dict[str, Any]:
    manifest = LAB.load_manifest(MANIFEST)
    assert manifest["schema"] == LAB.MANIFEST_SCHEMA
    assert [case["id"] for case in manifest["cases"]] == [
        "cpu_integer_10m",
        "word_dynamic_append",
        "startup_empty",
        "compile_hello",
    ]

    crlf = temporary / "crlf"
    shutil.copytree(MANIFEST.parent, crlf)
    for source in crlf.glob("*.fk"):
        normalized = source.read_bytes().decode("utf-8").replace("\r\n", "\n")
        source.write_bytes(normalized.replace("\n", "\r\n").encode("utf-8"))
    LAB.load_manifest(crlf / "manifest.json")

    cr_only = temporary / "cr-only"
    shutil.copytree(MANIFEST.parent, cr_only)
    cr_source = cr_only / "startup_empty.fk"
    cr_text = cr_source.read_bytes().decode("utf-8").replace("\r\n", "\n")
    cr_source.write_bytes(cr_text.replace("\n", "\r").encode("utf-8"))
    _expect_lab_error(
        lambda: LAB.load_manifest(cr_only / "manifest.json"),
        "lone-CR source mutation was canonicalized as LF",
    )

    snapshot = temporary / "snapshot"
    LAB._snapshot_sources(manifest, MANIFEST.parent, snapshot)
    snapshot_hashes = {
        case["source"]: LAB._sha256_source_file(snapshot / case["source"])
        for case in manifest["cases"]
    }
    assert snapshot_hashes == {
        case["source"]: case["source_sha256"] for case in manifest["cases"]
    }

    valid_stats = {
        "schema": LAB.RUNTIME_STATS_SCHEMA,
        "source": LAB.RUNTIME_STATS_SOURCE,
        "counters": {"allocations": 0, "copied_bytes": 42},
    }
    clean, record, failures = LAB._strip_runtime_stats(
        LAB.RUNTIME_STATS_PREFIX + json.dumps(valid_stats) + "\n"
    )
    assert clean == "" and record == valid_stats and failures == []
    invalid_stats = copy.deepcopy(valid_stats)
    invalid_stats["counters"]["allocations"] = -1
    _, record, failures = LAB._strip_runtime_stats(
        LAB.RUNTIME_STATS_PREFIX + json.dumps(invalid_stats) + "\n"
    )
    assert record is None and failures
    duplicate_stats = (
        '{"schema":"freak-v3-runtime-stats-v1","source":"freak-v3-runtime",'
        '"counters":{"allocations":0,"allocations":1}}'
    )
    _, record, failures = LAB._strip_runtime_stats(LAB.RUNTIME_STATS_PREFIX + duplicate_stats + "\n")
    assert record is None and failures

    stale = temporary / "stale"
    shutil.copytree(MANIFEST.parent, stale)
    with (stale / "cpu_integer_10m.fk").open("a", encoding="utf-8") as stream:
        stream.write("\n-- stale probe\n")
    _expect_lab_error(lambda: LAB.load_manifest(stale / "manifest.json"), "stale source hash was accepted")

    malformed = temporary / "malformed"
    shutil.copytree(MANIFEST.parent, malformed)
    malformed_value = json.loads((malformed / "manifest.json").read_text(encoding="utf-8"))
    del malformed_value["cases"][0]["modes"]["quick"]["expected_stdout_sha256"]
    _write_json(malformed / "manifest.json", malformed_value)
    _expect_lab_error(
        lambda: LAB.load_manifest(malformed / "manifest.json"),
        "malformed manifest mode was accepted",
    )

    unbound = temporary / "unbound"
    shutil.copytree(MANIFEST.parent, unbound)
    (unbound / "unlisted.fk").write_text("task main() {}\n", encoding="utf-8")
    _expect_lab_error(lambda: LAB.load_manifest(unbound / "manifest.json"), "unbound source was accepted")

    malformed_output = temporary / "malformed-output.json"
    _write_json(malformed_output, {})
    _expect_lab_error(lambda: LAB.validate_output(malformed_output), "malformed output was accepted")
    assert LAB._available_profiles("baseline help") == ["O0", "O1", "O2", "O3"]
    plus03_help = "profiles: \x1b[33m+03 — FINAL FORM\x1b[0m; LTO: --lto[=MODE]"
    assert LAB._available_profiles(plus03_help) == ["O0", "O1", "O2", "O3", "+03"]
    assert LAB._selected_profiles(None, LAB._available_profiles("baseline help")) == ["O0", "O1", "O2", "O3"]
    _expect_lab_error(
        lambda: LAB._selected_profiles(["+03"], LAB._available_profiles("baseline help")),
        "feature-unavailable +03 was accepted",
    )
    return manifest


def _mutate_and_reject(
    temporary: Path,
    document: dict[str, Any],
    name: str,
    mutation: Callable[[dict[str, Any]], None],
    cli: Path,
) -> None:
    candidate = copy.deepcopy(document)
    mutation(candidate)
    path = temporary / f"reject-{name}.json"
    _write_json(path, candidate)
    _expect_lab_error(
        lambda: LAB.validate_output(path, cli_override=str(cli)),
        f"malformed/stale result mutation was accepted: {name}",
    )


def _mutate_recorded_optimization(document: dict[str, Any]) -> None:
    observation = document["results"][0]["compile"]["observation"]
    changed = False
    for invocation in observation["invocations"]:
        invocation["argv"] = [
            "-O2" if argument == "-O0" else argument for argument in invocation["argv"]
        ]
        invocation["argv_sha256"] = LAB._json_sha256(invocation["argv"])
        changed = changed or "-O2" in invocation["argv"]
    assert changed
    observation["optimization_flags"] = ["-O2"]


def _live_checks(temporary: Path, manifest: dict[str, Any], cli: Path, clang: Path | None) -> None:
    before = {path.relative_to(MANIFEST.parent).as_posix(): _sha256(path) for path in MANIFEST.parent.rglob("*") if path.is_file()}
    output = temporary / "quick.json"
    command = [
        sys.executable,
        "-u",
        str(TOOL),
        "--cli",
        str(cli),
        "--manifest",
        str(MANIFEST),
        "--output",
        str(output),
        "--quick",
        "--profile",
        "O0",
        "--backend",
        "c",
        "--backend",
        "llvm",
        "--samples",
        "1",
        "--warmups",
        "0",
    ]
    if clang is not None:
        command.extend(["--clang", str(clang)])
    environment = os.environ.copy()
    environment["FREAK_HOME"] = str(temporary / "must-not-leak-freak-home")
    environment["FREAK_CLANG"] = str(temporary / "must-not-leak-fake-clang")
    environment["CFLAGS"] = "-Ofast must-not-leak"
    environment["LDFLAGS"] = "-fuse-ld=must-not-leak"
    environment["FREAK_UNRELATED_TEST_POISON"] = "must-not-leak"
    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        timeout=600,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"quick lab failed with {completed.returncode}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )

    document = LAB.validate_output(output, cli_override=str(cli))
    assert document["schema"] == "freak-v3-performance-lab-v1"
    assert document["compiler"]["path"] == str(cli)
    assert document["compiler"]["sha256"] == _sha256(cli)
    assert document["compiler"]["version"]
    assert document["configuration"]["mode"] == "quick"
    assert document["configuration"]["profiles"] == ["O0"]
    assert document["configuration"]["backends"] == ["c", "llvm"]
    assert len(document["results"]) == len(manifest["cases"]) * 2
    assert {result["backend"] for result in document["results"]} == {"c", "llvm"}
    assert all(result["profile"] == "O0" for result in document["results"])
    assert all(result["verification"] == {"passed": True, "failures": []} for result in document["results"])
    expected_quick = {case["id"]: case["modes"]["quick"] for case in manifest["cases"]}
    for result in document["results"]:
        mode = expected_quick[result["case"]]
        assert result["workload"]["parameters"] == mode["parameters"]
        assert result["workload"]["expected_stdout_sha256"] == mode["expected_stdout_sha256"]
        assert result["run"]["samples"][0]["stdout_sha256"] == mode["expected_stdout_sha256"]
        observation = result["compile"]["observation"]
        assert observation["schema"] == LAB.COMPILE_OBSERVATION_SCHEMA
        assert observation["optimization_flags"] == ["-O0"]
        assert observation["lto_flags"] == []
        assert observation["backend_artifact"]["suffix"] == (
            ".c" if result["backend"] == "c" else ".ll"
        )
        assert observation["runtime_plan"] in {"source", "bundle", "bundle-source-fallback"}
        assert result["peak_rss_bytes"] is None and result["peak_rss_reason"]
        assert result["runtime_counters"] is None and result["runtime_counters_reason"]
    assert "must-not-leak" not in output.read_text(encoding="utf-8")

    after = {path.relative_to(MANIFEST.parent).as_posix(): _sha256(path) for path in MANIFEST.parent.rglob("*") if path.is_file()}
    assert after == before, "the lab modified or generated files in the permanent benchmark tree"

    _mutate_and_reject(
        temporary,
        document,
        "schema",
        lambda value: value.__setitem__("schema", "freak-v3-performance-lab-v0"),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "compiler-hash",
        lambda value: value["compiler"].__setitem__("sha256", "0" * 64),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "extra-result-key",
        lambda value: value["results"][0].__setitem__("unknown", True),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "median",
        lambda value: value["results"][0]["run"].__setitem__(
            "median_ns", value["results"][0]["run"]["median_ns"] + 1
        ),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "checksum",
        lambda value: value["results"][0]["run"]["samples"][0].__setitem__("stdout_sha256", "0" * 64),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "raw-checksum",
        lambda value: value["results"][0]["run"]["samples"][0].__setitem__(
            "stdout_raw_sha256", "0" * 64
        ),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "toolchain-version",
        lambda value: value["toolchain"].__setitem__("version", "fabricated toolchain"),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "available-profiles",
        lambda value: value["configuration"]["available_profiles"].append("+03"),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "peak-rss",
        lambda value: value["results"][0].__setitem__("peak_rss_bytes", 123),
        cli,
    )

    def fabricate_counters(value: dict[str, Any]) -> None:
        result = value["results"][0]
        result["runtime_counters"] = {
            "samples": [
                {
                    "schema": LAB.RUNTIME_STATS_SCHEMA,
                    "source": LAB.RUNTIME_STATS_SOURCE,
                    "counters": {"allocations": 999},
                }
            ]
        }
        result["runtime_counters_reason"] = None

    _mutate_and_reject(temporary, document, "fabricated-counters", fabricate_counters, cli)
    _mutate_and_reject(
        temporary,
        document,
        "ignored-optimization",
        _mutate_recorded_optimization,
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "ignored-backend",
        lambda value: value["results"][0]["compile"]["observation"]["backend_artifact"].__setitem__(
            "suffix", ".ll"
        ),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "backend-artifact-hash",
        lambda value: value["results"][0]["compile"]["observation"]["backend_artifact"].__setitem__(
            "sha256", "0" * 64
        ),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "binary-hash",
        lambda value: value["results"][0]["binary"].__setitem__("sha256", "0" * 64),
        cli,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cli", nargs="?", help="exact fresh FREAK CLI for executable C/LLVM checks")
    parser.add_argument("--clang", help="exact Clang executable")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="freak-v3-performance-test-") as name:
        temporary = Path(name).resolve()
        manifest = _static_checks(temporary)
        if args.cli:
            cli = Path(args.cli).expanduser().resolve(strict=True)
            clang = Path(args.clang).expanduser().resolve(strict=True) if args.clang else None
            _live_checks(temporary, manifest, cli, clang)
    mode = "static + C/LLVM quick" if args.cli else "static only"
    print(f"v3 performance lab tests passed ({mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
