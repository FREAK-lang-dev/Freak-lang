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

    duplicate_manifest = temporary / "duplicate-manifest"
    shutil.copytree(MANIFEST.parent, duplicate_manifest)
    duplicate_path = duplicate_manifest / "manifest.json"
    duplicate_text = duplicate_path.read_text(encoding="utf-8")
    duplicate_text = duplicate_text.replace(
        '"schema": "freak-v3-performance-manifest-v1"',
        '"schema": "freak-v3-performance-manifest-v1",\n  "schema": "freak-v3-performance-manifest-v1"',
        1,
    )
    duplicate_path.write_text(duplicate_text, encoding="utf-8")
    _expect_lab_error(lambda: LAB.load_manifest(duplicate_path), "duplicate manifest key was accepted")

    unbound = temporary / "unbound"
    shutil.copytree(MANIFEST.parent, unbound)
    (unbound / "unlisted.fk").write_text("task main() {}\n", encoding="utf-8")
    _expect_lab_error(lambda: LAB.load_manifest(unbound / "manifest.json"), "unbound source was accepted")

    malformed_output = temporary / "malformed-output.json"
    _write_json(malformed_output, {})
    _expect_lab_error(lambda: LAB.validate_output(malformed_output), "malformed output was accepted")
    help_text = LAB._parser().format_help()
    normalized_help = " ".join(help_text.split())
    assert "not digitally signed" in normalized_help
    assert "live compiler, Clang, and linker" in normalized_help
    posix_wrapper = LAB._recording_wrapper_bytes(
        "posix-sh",
        "/tmp/python with spaces",
        "/tmp/recorder with spaces.py",
        "ignored",
    ).decode("utf-8")
    assert posix_wrapper.startswith("#!/bin/sh\nexec ")
    assert "'/tmp/python with spaces'" in posix_wrapper
    assert "'/tmp/recorder with spaces.py'" in posix_wrapper
    _expect_lab_error(
        lambda: LAB._decode_bytes("QUFBQUFB", "bounded base64", maximum=2),
        "oversized base64 was decoded before rejection",
    )
    bounded_json = temporary / "bounded.json"
    bounded_json.write_text("{}\n", encoding="utf-8")
    _expect_lab_error(
        lambda: LAB._strict_json(bounded_json, maximum=1),
        "oversized JSON input was accepted",
    )

    observed_input = temporary / "invocation-input.c"
    observed_output = temporary / "invocation-output.o"
    observed_input.write_bytes(b"int x;\n")
    observed_output.write_bytes(b"object\n")
    raw_invocation = {
        "argv": ["-c", str(observed_input), "-o", str(observed_output)],
        "cwd": str(temporary),
        "exit_code": 0,
        "inputs": [
            {
                "argument_index": 1,
                "path": str(observed_input),
                "bytes": observed_input.stat().st_size,
                "sha256": LAB._sha256_file(observed_input),
            }
        ],
        "output": {
            "path": str(observed_output),
            "bytes": observed_output.stat().st_size,
            "sha256": LAB._sha256_file(observed_output),
        },
    }
    stored_invocation = LAB._invocation_record(raw_invocation, "static invocation")
    stored_invocation["output"]["sha256"] = "0" * 64
    _expect_lab_error(
        lambda: LAB._validate_invocation_record(stored_invocation, "mutated invocation"),
        "full invocation digest omitted output evidence",
    )

    old_capture_bound = LAB.MAX_CAPTURE_BYTES
    LAB.MAX_CAPTURE_BYTES = 32
    try:
        _expect_lab_error(
            lambda: LAB._run_bytes(
                [sys.executable, "-c", "import sys; sys.stdout.write('x' * 4096)"],
                cwd=temporary,
                environment=os.environ,
                timeout=10.0,
            ),
            "oversized subprocess output was accepted",
        )
    finally:
        LAB.MAX_CAPTURE_BYTES = old_capture_bound
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
        _refresh_invocation_record(invocation)
        changed = changed or "-O2" in invocation["argv"]
    assert changed
    observation["optimization_flags"] = ["-O2"]


def _replace_embedded_content(record: dict[str, Any], content: bytes) -> None:
    record["bytes"] = len(content)
    record["sha256"] = LAB._sha256_bytes(content)
    record["content_zlib_base64"] = LAB._encode_zlib_bytes(content)


def _refresh_invocation_record(invocation: dict[str, Any]) -> None:
    raw = {name: invocation[name] for name in LAB._RAW_INVOCATION_KEYS}
    invocation["record_sha256"] = LAB._json_sha256(raw)


def _selected_link(document: dict[str, Any]) -> dict[str, Any]:
    observation = document["results"][0]["compile"]["observation"]
    selected = observation["link_invocation_sha256"]
    return next(item for item in observation["invocations"] if item["record_sha256"] == selected)


def _mutate_link_output(document: dict[str, Any]) -> None:
    observation = document["results"][0]["compile"]["observation"]
    invocation = _selected_link(document)
    output_index = invocation["argv"].index("-o")
    invocation["argv"][output_index + 1] = str(Path(invocation["cwd"]) / "detached-output.exe")
    _refresh_invocation_record(invocation)
    observation["link_invocation_sha256"] = invocation["record_sha256"]
    observation["linker"]["link_invocation_sha256"] = invocation["record_sha256"]


def _detach_link_runtime_input(document: dict[str, Any]) -> None:
    invocation = _selected_link(document)
    for index, input_record in enumerate(invocation["inputs"]):
        if Path(input_record["path"]).name in LAB._RUNTIME_INPUT_NAMES:
            del invocation["inputs"][index]
            return
    raise AssertionError("selected link invocation did not contain a runtime input")


def _mutate_canonical_recorder(document: dict[str, Any]) -> None:
    recording = document["recording"]
    content = b"#!/usr/bin/env python3\nraise SystemExit(0)\n"
    recording["recorder_content_base64"] = LAB._encode_bytes(content)
    recording["recorder_sha256"] = LAB._sha256_bytes(content)
    recording["combined_sha256"] = LAB._recording_identity_digest(recording)


def _coherently_replace_binary_fields(document: dict[str, Any]) -> None:
    result = document["results"][0]
    content = b"detached executable binary"
    _replace_embedded_content(result["binary"], content)
    invocation = _selected_link(document)
    invocation["output"]["bytes"] = len(content)
    invocation["output"]["sha256"] = LAB._sha256_bytes(content)
    # Each nested record is now self-consistent. The full invocation digest must
    # still reject the coherent replacement.


def _coherently_replace_artifact_fields(document: dict[str, Any]) -> None:
    observation = document["results"][0]["compile"]["observation"]
    artifact = observation["backend_artifact"]
    old_path = artifact["path"]
    content = b"detached backend artifact"
    _replace_embedded_content(artifact, content)
    for invocation in observation["invocations"]:
        for input_record in invocation["inputs"]:
            if input_record["path"] == old_path:
                input_record["bytes"] = len(content)
                input_record["sha256"] = LAB._sha256_bytes(content)


def _substitute_linker_identity(document: dict[str, Any]) -> None:
    observation = document["results"][0]["compile"]["observation"]
    linker = observation["linker"]
    clang = Path(document["toolchain"]["path"])
    completed = subprocess.run(
        [str(clang), "--version"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    trace = f'"{clang}" fabricated linker trace\n'.encode("utf-8")
    linker.update(
        {
            "observed_path": str(clang),
            "path": str(clang),
            "sha256": LAB._sha256_file(clang),
            "bytes": clang.stat().st_size,
            "version_exit_code": completed.returncode,
            "version_stdout_base64": LAB._encode_bytes(completed.stdout),
            "version_stderr_base64": LAB._encode_bytes(completed.stderr),
            "trace_raw_base64": LAB._encode_bytes(trace),
            "trace_sha256": LAB._sha256_bytes(trace),
        }
    )


def _profile_matrix_checks(temporary: Path, cli: Path, clang: Path | None) -> None:
    output = temporary / "profile-matrix.json"
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
        "--case",
        "startup_empty",
        "--backend",
        "c",
        "--backend",
        "llvm",
        "--samples",
        "1",
        "--warmups",
        "1",
    ]
    if clang is not None:
        command.extend(["--clang", str(clang)])
    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        env=os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=600,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"profile matrix failed with {completed.returncode}\n"
            f"stdout:\n{completed.stdout.decode('utf-8', errors='replace')}\n"
            f"stderr:\n{completed.stderr.decode('utf-8', errors='replace')}"
        )
    document = LAB.validate_output(output, cli_override=str(cli))
    profiles = document["configuration"]["profiles"]
    assert profiles == document["configuration"]["available_profiles"]
    assert profiles[:4] == ["O0", "O1", "O2", "O3"]
    assert {result["profile"] for result in document["results"]} == set(profiles)
    assert {result["backend"] for result in document["results"]} == {"c", "llvm"}
    assert len(document["results"]) == len(profiles) * 2
    for result in document["results"]:
        observation = result["compile"]["observation"]
        spec = LAB._PROFILE_SPECS[result["profile"]]
        assert observation["optimization_flags"] == [spec["opt"]]
        assert observation["lto_flags"] == spec["lto"]
        assert observation["linker_flags"] == LAB._expected_linker_flags(result["profile"])
        assert len(result["run"]["warmups"]) == 1
        if result["profile"] == "+03":
            assert observation["runtime_plan"] == "source"
            assert observation["runtime_attempt_plan"] == "source"
    _mutate_and_reject(
        temporary,
        document,
        "warmup-executable-provenance",
        lambda value: value["results"][0]["run"]["warmups"][0].__setitem__(
            "executable_sha256_before", "0" * 64
        ),
        cli,
    )


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
        timeout=600,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"quick lab failed with {completed.returncode}\n"
            f"stdout:\n{completed.stdout.decode('utf-8', errors='replace')}\n"
            f"stderr:\n{completed.stderr.decode('utf-8', errors='replace')}"
        )

    document = LAB.validate_output(output, cli_override=str(cli))
    assert document["schema"] == LAB.RESULT_SCHEMA
    assert document["trust_model"] == {
        "schema": LAB.TRUST_MODEL_SCHEMA,
        "scope": LAB.TRUST_MODEL_SCOPE,
        "limitation": LAB.TRUST_MODEL_LIMITATION,
    }
    assert document["compiler"]["path"] == str(cli)
    assert document["compiler"]["sha256"] == _sha256(cli)
    assert document["compiler"]["version"]
    assert document["recording"]["schema"] == LAB.RECORDING_SCHEMA
    assert document["recording"]["combined_sha256"] == LAB._recording_identity_digest(document["recording"])
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
        assert observation["recording_identity_sha256"] == document["recording"]["combined_sha256"]
        assert observation["recording_before_sha256"] == document["recording"]["combined_sha256"]
        assert observation["recording_after_sha256"] == document["recording"]["combined_sha256"]
        assert observation["runtime_plan"] in {"source", "bundle"}
        assert observation["runtime_attempt_plan"] in {"source", "bundle", "bundle-source-fallback"}
        assert observation["linked_runtime_inputs"]
        link = next(
            invocation
            for invocation in observation["invocations"]
            if invocation["record_sha256"] == observation["link_invocation_sha256"]
        )
        assert link["exit_code"] == 0 and link["output"]["sha256"] == result["binary"]["sha256"]
        sample = result["run"]["samples"][0]
        assert sample["command"][0] == result["binary"]["path"]
        assert sample["executable_sha256_before"] == result["binary"]["sha256"]
        assert sample["executable_sha256_after"] == result["binary"]["sha256"]
        assert result["run"]["warmups"] == []
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
        "trust-model",
        lambda value: value["trust_model"].__setitem__(
            "limitation", "fabricated authentication claim"
        ),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "recording-identity-hash",
        lambda value: value["recording"].__setitem__("combined_sha256", "0" * 64),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "recording-canonical-content",
        _mutate_canonical_recorder,
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "recording-before-build",
        lambda value: value["results"][0]["compile"]["observation"].__setitem__(
            "recording_before_sha256", "0" * 64
        ),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "warmup-count",
        lambda value: value["configuration"].__setitem__("warmups", 999),
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
        "backend-artifact-recomputed",
        lambda value: _replace_embedded_content(
            value["results"][0]["compile"]["observation"]["backend_artifact"],
            b"detached backend artifact",
        ),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "backend-artifact-coherent-fields",
        _coherently_replace_artifact_fields,
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
        "binary-recomputed",
        lambda value: _replace_embedded_content(
            value["results"][0]["binary"],
            b"detached executable binary",
        ),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "binary-link-output-coherent-fields",
        _coherently_replace_binary_fields,
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "exact-linker-substitution",
        _substitute_linker_identity,
        cli,
    )
    _mutate_and_reject(temporary, document, "link-output", _mutate_link_output, cli)
    _mutate_and_reject(temporary, document, "detached-link-runtime", _detach_link_runtime_input, cli)

    duplicate_output = temporary / "reject-duplicate-nested-key.json"
    duplicate_text = output.read_text(encoding="utf-8")
    binary_path_text = json.dumps(document["results"][0]["binary"]["path"])
    binary_start = duplicate_text.index('"binary": {')
    path_start = duplicate_text.index(f'"path": {binary_path_text}', binary_start)
    needle = f'"path": {binary_path_text}'
    duplicate_text = duplicate_text[:path_start] + needle + ",\n        " + duplicate_text[path_start:]
    duplicate_output.write_text(duplicate_text, encoding="utf-8")
    _expect_lab_error(
        lambda: LAB.validate_output(duplicate_output, cli_override=str(cli)),
        "duplicate nested artifact key was accepted",
    )

    _profile_matrix_checks(temporary, cli, clang)
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
