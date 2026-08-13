#!/usr/bin/env python3
"""Deterministic, provenance-rich benchmark harness for the shipping V3 CLI."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
import platform
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import zlib
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


RESULT_SCHEMA = "freak-v3-performance-lab-v1"
MANIFEST_SCHEMA = "freak-v3-performance-manifest-v1"
COMPILE_OBSERVATION_SCHEMA = "freak-v3-compile-observation-v1"
RUNTIME_STATS_PREFIX = "FREAK_RUNTIME_STATS "
RUNTIME_STATS_SCHEMA = "freak-v3-runtime-stats-v1"
RUNTIME_STATS_SOURCE = "freak-v3-runtime"
RSS_UNAVAILABLE_REASON = "portable per-child peak RSS collection is unavailable in lab schema v1"
RUNTIME_COUNTERS_UNAVAILABLE_REASON = "runtime stats sentinel not emitted by this build"
DEFAULT_MANIFEST = Path(__file__).resolve().parents[1] / "benchmarks" / "v3" / "manifest.json"
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
MAX_CONTENT_BYTES = 64 * 1024 * 1024

_ROOT_MANIFEST_KEYS = {"schema", "cases"}
_CASE_KEYS = {"id", "category", "source", "source_sha256", "modes"}
_MODE_KEYS = {
    "arguments",
    "parameters",
    "expected_exit_code",
    "expected_stdout",
    "expected_stdout_sha256",
    "expected_stderr",
    "expected_stderr_sha256",
}
_RESULT_KEYS = {
    "case",
    "category",
    "source",
    "source_sha256",
    "backend",
    "profile",
    "profile_id",
    "profile_display",
    "target",
    "workload",
    "compile",
    "binary",
    "run",
    "peak_rss_bytes",
    "peak_rss_reason",
    "runtime_counters",
    "runtime_counters_reason",
    "verification",
}
_WORKLOAD_KEYS = {
    "mode",
    "arguments",
    "parameters",
    "expected_exit_code",
    "expected_stdout",
    "expected_stdout_sha256",
    "expected_stderr",
    "expected_stderr_sha256",
}
_SAMPLE_KEYS = {
    "index",
    "duration_ns",
    "exit_code",
    "stdout",
    "stdout_sha256",
    "stdout_raw_sha256",
    "stdout_raw_base64",
    "stderr",
    "stderr_sha256",
    "stderr_raw_sha256",
    "stderr_raw_base64",
}
_COMPILE_KEYS = {
    "duration_ns",
    "stdout_raw_base64",
    "stdout_sha256",
    "stderr_raw_base64",
    "stderr_sha256",
    "command",
    "command_sha256",
    "observation",
}
_COMPILE_OBSERVATION_KEYS = {
    "schema",
    "source_snapshot_sha256",
    "recording_wrapper_sha256",
    "probe_invocations",
    "invocations",
    "optimization_flags",
    "lto_flags",
    "target_flags",
    "linker_flags",
    "runtime_plan",
    "runtime_inputs",
    "backend_artifact",
    "linker",
}
_ARTIFACT_KEYS = {"suffix", "bytes", "sha256", "content_zlib_base64"}
_BINARY_KEYS = {"bytes", "sha256", "content_zlib_base64"}
_RUNTIME_STATS_KEYS = {"schema", "source", "counters"}
_RUNTIME_INPUT_NAMES = {
    "freak_runtime.c",
    "freak_llvm_runtime.c",
    "freak_runtime.o",
    "freak_llvm_runtime.o",
    "freak_ui_win32.o",
    "freak_runtime.obj",
    "freak_llvm_runtime.obj",
    "freak_ui_win32.obj",
    "win32_backend.c",
}
_SAFE_ENV_KEYS = {
    "APPDATA",
    "COMSPEC",
    "HOME",
    "LOCALAPPDATA",
    "NUMBER_OF_PROCESSORS",
    "OS",
    "PATH",
    "PATHEXT",
    "PROGRAMDATA",
    "SYSTEMDRIVE",
    "SYSTEMROOT",
    "TEMP",
    "TMP",
    "TMPDIR",
    "USERPROFILE",
    "WINDIR",
}
_PROFILE_SPECS = {
    "O0": {"id": "opt0", "display": "O0", "arguments": ["--opt=0"], "opt": "-O0", "lto": []},
    "O1": {"id": "opt1", "display": "O1", "arguments": ["--opt=1"], "opt": "-O1", "lto": []},
    "O2": {"id": "opt2", "display": "O2", "arguments": ["--opt=2"], "opt": "-O2", "lto": []},
    "O3": {"id": "opt3", "display": "O3", "arguments": ["--opt=3"], "opt": "-O3", "lto": []},
    "+03": {
        "id": "plus03",
        "display": "+03 — FINAL FORM",
        "arguments": ["+03"],
        "opt": "-O3",
        "lto": ["-flto=thin"],
    },
}
_BACKEND_SPECS = {"c": "--c", "llvm": "--llvm"}


class LabError(RuntimeError):
    """A deterministic input, provenance, build, or verification error."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_source_bytes(path: Path) -> bytes:
    try:
        text = path.read_bytes().decode("utf-8")
    except (OSError, UnicodeError) as error:
        raise LabError(f"cannot read FREAK source {path}: {error}") from error
    return text.replace("\r\n", "\n").encode("utf-8")


def _sha256_source_file(path: Path) -> str:
    """Hash FREAK source in its repository-canonical UTF-8/LF form."""

    return _sha256_bytes(_canonical_source_bytes(path))


def _json_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return _sha256_text(encoded)


def _encode_bytes(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _decode_bytes(value: Any, context: str) -> bytes:
    text = _require_string(value, context)
    try:
        decoded = base64.b64decode(text, validate=True)
    except (ValueError, binascii.Error) as error:
        raise LabError(f"{context} is not canonical base64") from error
    if _encode_bytes(decoded) != text:
        raise LabError(f"{context} is not canonical base64")
    return decoded


def _encode_zlib_bytes(value: bytes) -> str:
    return _encode_bytes(zlib.compress(value, level=9))


def _decode_zlib_bytes(value: Any, expected_size: int, context: str) -> bytes:
    if expected_size < 1 or expected_size > MAX_CONTENT_BYTES:
        raise LabError(f"{context} uncompressed size is outside the lab bound")
    compressed = _decode_bytes(value, context)
    decompressor = zlib.decompressobj()
    try:
        decoded = decompressor.decompress(compressed, expected_size + 1)
        if len(decoded) > expected_size or decompressor.unconsumed_tail:
            raise LabError(f"{context} expands beyond its declared size")
        decoded += decompressor.flush()
    except zlib.error as error:
        raise LabError(f"{context} is not canonical zlib data") from error
    if (
        len(decoded) != expected_size
        or not decompressor.eof
        or decompressor.unused_data
    ):
        raise LabError(f"{context} zlib content is malformed")
    return decoded


def _strict_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as stream:
            return json.load(stream)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise LabError(f"cannot read JSON {path}: {error}") from error


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise ValueError(f"duplicate JSON key: {name}")
        result[name] = value
    return result


def _exact_keys(value: Mapping[str, Any], expected: set[str], context: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise LabError(f"{context} keys differ (missing={missing}, extra={extra})")


def _require_dict(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise LabError(f"{context} must be an object")
    return value


def _require_list(value: Any, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise LabError(f"{context} must be an array")
    return value


def _require_string_list(value: Any, context: str) -> list[str]:
    values = _require_list(value, context)
    if not all(isinstance(item, str) for item in values):
        raise LabError(f"{context} must contain only strings")
    return values


def _require_string(value: Any, context: str, *, nonempty: bool = False) -> str:
    if not isinstance(value, str) or (nonempty and not value):
        suffix = " non-empty" if nonempty else ""
        raise LabError(f"{context} must be a{suffix} string")
    return value


def _require_int(value: Any, context: str, *, minimum: int | None = None) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise LabError(f"{context} must be an integer")
    if minimum is not None and value < minimum:
        raise LabError(f"{context} must be >= {minimum}")
    return value


def load_manifest(path: Path) -> dict[str, Any]:
    """Load and fully validate a manifest and its source-tree closure."""

    path = path.resolve(strict=True)
    root = _require_dict(_strict_json(path), "manifest")
    _exact_keys(root, _ROOT_MANIFEST_KEYS, "manifest")
    if root["schema"] != MANIFEST_SCHEMA:
        raise LabError(f"unsupported manifest schema: {root['schema']!r}")

    cases = _require_list(root["cases"], "manifest.cases")
    if not cases:
        raise LabError("manifest.cases must not be empty")
    seen_ids: set[str] = set()
    seen_sources: set[str] = set()
    base = path.parent.resolve()

    for index, raw_case in enumerate(cases):
        context = f"manifest.cases[{index}]"
        case = _require_dict(raw_case, context)
        _exact_keys(case, _CASE_KEYS, context)
        case_id = _require_string(case["id"], f"{context}.id", nonempty=True)
        if not all(char.islower() or char.isdigit() or char == "_" for char in case_id):
            raise LabError(f"{context}.id must use lowercase letters, digits, and underscores")
        if case_id in seen_ids:
            raise LabError(f"duplicate case id: {case_id}")
        seen_ids.add(case_id)
        _require_string(case["category"], f"{context}.category", nonempty=True)

        source_name = _require_string(case["source"], f"{context}.source", nonempty=True)
        source_relative = Path(source_name)
        if source_relative.is_absolute() or source_relative.as_posix() != source_name:
            raise LabError(f"{context}.source must be a normalized relative POSIX path")
        if source_relative.suffix != ".fk" or ".." in source_relative.parts:
            raise LabError(f"{context}.source must identify a contained .fk file")
        source = (base / source_relative).resolve(strict=True)
        if source != base and base not in source.parents:
            raise LabError(f"{context}.source escapes the manifest directory")
        if source_name in seen_sources:
            raise LabError(f"duplicate manifest source: {source_name}")
        seen_sources.add(source_name)
        source_hash = _require_string(case["source_sha256"], f"{context}.source_sha256")
        if source_hash != _sha256_source_file(source):
            raise LabError(f"stale source hash for {source_name}")

        modes = _require_dict(case["modes"], f"{context}.modes")
        if set(modes) != {"default", "quick"}:
            raise LabError(f"{context}.modes must contain exactly default and quick")
        for mode_name in ("default", "quick"):
            mode_context = f"{context}.modes.{mode_name}"
            mode = _require_dict(modes[mode_name], mode_context)
            _exact_keys(mode, _MODE_KEYS, mode_context)
            _require_string_list(mode["arguments"], f"{mode_context}.arguments")
            parameters = _require_dict(mode["parameters"], f"{mode_context}.parameters")
            for name, parameter in parameters.items():
                if not isinstance(name, str) or not name:
                    raise LabError(f"{mode_context}.parameters keys must be non-empty strings")
                if isinstance(parameter, (dict, list, float)) or parameter is None:
                    raise LabError(f"{mode_context}.parameters.{name} must be a JSON scalar")
            _require_int(mode["expected_exit_code"], f"{mode_context}.expected_exit_code")
            for channel in ("stdout", "stderr"):
                text = _require_string(mode[f"expected_{channel}"], f"{mode_context}.expected_{channel}")
                declared = _require_string(
                    mode[f"expected_{channel}_sha256"],
                    f"{mode_context}.expected_{channel}_sha256",
                )
                if declared != _sha256_text(text):
                    raise LabError(f"{mode_context}.expected_{channel}_sha256 is stale")

    actual_sources = {
        source.relative_to(base).as_posix()
        for source in base.rglob("*.fk")
        if source.is_file()
    }
    if actual_sources != seen_sources:
        missing = sorted(seen_sources - actual_sources)
        unbound = sorted(actual_sources - seen_sources)
        raise LabError(f"manifest source closure differs (missing={missing}, unbound={unbound})")
    return root


def _snapshot_sources(manifest: Mapping[str, Any], manifest_dir: Path, destination: Path) -> None:
    """Create one canonical immutable-ish source snapshot for the whole run."""

    destination.mkdir(parents=True, exist_ok=False)
    for case in manifest["cases"]:
        source = (manifest_dir / case["source"]).resolve(strict=True)
        before = _sha256_source_file(source)
        if before != case["source_sha256"]:
            raise LabError(f"source changed after manifest validation: {case['source']}")
        canonical = _canonical_source_bytes(source)
        snapshot = destination / case["source"]
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes(canonical)
        after = _sha256_source_file(source)
        snapshot_hash = _sha256_source_file(snapshot)
        if before != after or snapshot_hash != case["source_sha256"]:
            raise LabError(f"source changed while snapshotting: {case['source']}")
        snapshot.chmod(0o444)


def _clean_environment(clang: Path | None = None) -> dict[str, str]:
    environment: dict[str, str] = {}
    for name, value in os.environ.items():
        upper = name.upper()
        if upper in _SAFE_ENV_KEYS:
            environment[name] = value
    environment["NO_COLOR"] = "1"
    environment["PYTHONUTF8"] = "1"
    if clang is not None:
        environment["FREAK_CLANG"] = str(clang)
    return environment


def _write_recording_clang(work_dir: Path, real_clang: Path) -> tuple[Path, Path, str]:
    recorder = work_dir / "record_clang.py"
    log = work_dir / "clang-invocations.jsonl"
    recorder_text = """#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from pathlib import Path

arguments = sys.argv[1:]
with Path(os.environ["FREAK_PERF_CLANG_LOG"]).open("a", encoding="utf-8") as stream:
    stream.write(json.dumps(arguments, ensure_ascii=False) + "\\n")
raise SystemExit(subprocess.run([os.environ["FREAK_PERF_REAL_CLANG"], *arguments]).returncode)
"""
    recorder.write_text(recorder_text, encoding="utf-8", newline="\n")
    if sys.platform == "win32":
        wrapper = work_dir / "record-clang.cmd"
        wrapper.write_text(
            f'@"{sys.executable}" "{recorder}" %*\n',
            encoding="utf-8",
            newline="\r\n",
        )
    else:
        wrapper = work_dir / "record-clang"
        wrapper.write_text(
            f'#!{sys.executable}\n{recorder_text.split(chr(10), 1)[1]}',
            encoding="utf-8",
            newline="\n",
        )
        wrapper.chmod(0o755)
    return wrapper.resolve(), log.resolve(), _sha256_file(wrapper)


def _read_recording_log(path: Path) -> list[list[str]]:
    if not path.is_file():
        raise LabError("recording Clang did not produce an invocation log")
    invocations: list[list[str]] = []
    try:
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
            value = json.loads(line)
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                raise LabError(f"recording Clang invocation {index} is malformed")
            invocations.append(value)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise LabError(f"cannot read recording Clang log: {error}") from error
    return invocations


def _resolve_exact_executable(value: str, description: str) -> Path:
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    try:
        candidate = candidate.resolve(strict=True)
    except OSError as error:
        raise LabError(f"{description} does not exist: {value}") from error
    if not candidate.is_file():
        raise LabError(f"{description} is not a file: {candidate}")
    return candidate


def _resolve_clang(value: str | None) -> Path:
    if value:
        return _resolve_exact_executable(value, "Clang")
    found = shutil.which("clang", path=_clean_environment().get("PATH"))
    if not found:
        raise LabError("Clang was not passed with --clang and is not on the clean PATH")
    return Path(found).resolve(strict=True)


def _run_bytes(
    command: Sequence[str],
    *,
    cwd: Path,
    environment: Mapping[str, str],
    timeout: float,
) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            list(command),
            cwd=str(cwd),
            env=dict(environment),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise LabError(f"command failed to execute: {command!r}: {error}") from error


def _decode(value: bytes, context: str) -> str:
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError as error:
        raise LabError(f"{context} is not valid UTF-8") from error


def _canonical_output(value: bytes, context: str) -> str:
    """Decode UTF-8 and make line-oriented workload contracts platform-neutral."""

    return _decode(value, context).replace("\r\n", "\n")


def _tool_identity(path: Path, environment: Mapping[str, str], cwd: Path, timeout: float) -> dict[str, Any]:
    version = _run_bytes([str(path), "--version"], cwd=cwd, environment=environment, timeout=timeout)
    if version.returncode != 0:
        raise LabError(f"Clang --version failed with exit code {version.returncode}")
    triple = _run_bytes([str(path), "-dumpmachine"], cwd=cwd, environment=environment, timeout=timeout)
    if triple.returncode != 0:
        raise LabError(f"Clang -dumpmachine failed with exit code {triple.returncode}")
    version_text = _decode(version.stdout, "Clang version output").strip()
    target_triple = _decode(triple.stdout, "Clang target output").strip()
    if not version_text or not target_triple:
        raise LabError("Clang identity output is empty")
    return {
        "path": str(path),
        "sha256": _sha256_file(path),
        "bytes": path.stat().st_size,
        "version": version_text,
        "target_triple": target_triple,
    }


def _compiler_identity(
    cli: Path,
    environment: Mapping[str, str],
    cwd: Path,
    timeout: float,
) -> tuple[dict[str, Any], str]:
    version = _run_bytes([str(cli), "version"], cwd=cwd, environment=environment, timeout=timeout)
    if version.returncode != 0:
        raise LabError(f"FREAK CLI version failed with exit code {version.returncode}")
    version_stdout = _decode(version.stdout, "compiler version stdout")
    version_stderr = _decode(version.stderr, "compiler version stderr")
    version_text = version_stdout.strip() or version_stderr.strip()
    if not version_text:
        raise LabError("FREAK CLI version output is empty")
    help_result = _run_bytes([str(cli), "help"], cwd=cwd, environment=environment, timeout=timeout)
    if help_result.returncode != 0:
        raise LabError(f"FREAK CLI help failed with exit code {help_result.returncode}")
    help_text = _decode(help_result.stdout + help_result.stderr, "compiler help output")
    identity = {
        "path": str(cli),
        "sha256": _sha256_file(cli),
        "bytes": cli.stat().st_size,
        "version": version_text,
        "version_stdout": version_stdout,
        "version_stderr": version_stderr,
        "version_output_sha256": _sha256_bytes(version.stdout + version.stderr),
        "help_stdout": _decode(help_result.stdout, "compiler help stdout"),
        "help_stderr": _decode(help_result.stderr, "compiler help stderr"),
        "help_output_sha256": _sha256_bytes(help_result.stdout + help_result.stderr),
    }
    return identity, help_text


def _available_profiles(help_text: str) -> list[str]:
    profiles = ["O0", "O1", "O2", "O3"]
    plain_help = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", help_text)
    if "+03 — FINAL FORM" in plain_help and "--lto[=MODE]" in plain_help:
        profiles.append("+03")
    return profiles


def _selected_profiles(requested: Sequence[str] | None, available: Sequence[str]) -> list[str]:
    profiles = list(requested) if requested else list(available)
    if not profiles:
        raise LabError("at least one profile is required")
    unknown = [profile for profile in profiles if profile not in _PROFILE_SPECS]
    if unknown:
        raise LabError(f"unknown profiles: {unknown}; expected O0, O1, O2, O3, or +03")
    unsupported = [profile for profile in profiles if profile not in available]
    if unsupported:
        raise LabError(f"profiles are unsupported by the exact CLI: {unsupported}")
    if len(set(profiles)) != len(profiles):
        raise LabError("profiles must not be repeated")
    return profiles


def _selected_values(requested: Sequence[str] | None, allowed: Iterable[str], description: str) -> list[str]:
    values = list(requested) if requested else list(allowed)
    unknown = [value for value in values if value not in allowed]
    if unknown:
        raise LabError(f"unknown {description}: {unknown}")
    if not values or len(set(values)) != len(values):
        raise LabError(f"{description} must be non-empty and unique")
    return values


def _validate_runtime_stats_record(value: Any, context: str) -> dict[str, Any]:
    record = _require_dict(value, context)
    _exact_keys(record, _RUNTIME_STATS_KEYS, context)
    if record.get("schema") != RUNTIME_STATS_SCHEMA:
        raise LabError(f"{context}.schema is unsupported")
    if record.get("source") != RUNTIME_STATS_SOURCE:
        raise LabError(f"{context}.source is unsupported")
    counters = _require_dict(record.get("counters"), f"{context}.counters")
    if not counters:
        raise LabError(f"{context}.counters must not be empty")
    for name, value in counters.items():
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", name):
            raise LabError(f"{context}.counters has a non-canonical name")
        _require_int(value, f"{context}.counters.{name}", minimum=0)
    return {"schema": RUNTIME_STATS_SCHEMA, "source": RUNTIME_STATS_SOURCE, "counters": counters}


def _strip_runtime_stats(stderr: str) -> tuple[str, dict[str, Any] | None, list[str]]:
    clean: list[str] = []
    records: list[dict[str, Any]] = []
    failures: list[str] = []
    for line in stderr.splitlines(keepends=True):
        candidate = line.rstrip("\r\n")
        if not candidate.startswith(RUNTIME_STATS_PREFIX):
            clean.append(line)
            continue
        payload = candidate[len(RUNTIME_STATS_PREFIX) :]
        try:
            record = json.loads(payload, object_pairs_hook=_reject_duplicate_json_keys)
        except (json.JSONDecodeError, ValueError) as error:
            failures.append(f"malformed runtime stats sentinel: {error}")
            continue
        try:
            records.append(_validate_runtime_stats_record(record, "runtime stats sentinel"))
        except LabError as error:
            failures.append(str(error))
    if len(records) > 1:
        failures.append("a run emitted more than one runtime stats sentinel")
    return "".join(clean), records[0] if len(records) == 1 else None, failures


def _host_identity() -> dict[str, Any]:
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "logical_cpu_count": os.cpu_count(),
        "python": platform.python_version(),
    }


def _binary_path(source: Path) -> Path:
    candidates = [source.with_suffix(".exe"), source.with_suffix("")]
    existing = [candidate for candidate in candidates if candidate.is_file()]
    if len(existing) != 1:
        raise LabError(f"expected exactly one output binary for {source}, found {existing}")
    return existing[0]


def _invocation_record(arguments: Sequence[str]) -> dict[str, Any]:
    values = list(arguments)
    return {"argv": values, "argv_sha256": _json_sha256(values)}


def _runtime_plan(runtime_names: set[str]) -> str:
    has_sources = any(name.endswith(".c") for name in runtime_names)
    has_objects = any(name.endswith((".o", ".obj")) for name in runtime_names)
    if has_sources and has_objects:
        return "bundle-source-fallback"
    if has_sources:
        return "source"
    if has_objects:
        return "bundle"
    return "missing"


def _resolve_recorded_path(value: str, cwd: Path, context: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = cwd / path
    try:
        return path.resolve(strict=True)
    except OSError as error:
        raise LabError(f"{context} does not exist: {value}") from error


def _is_linker_name(value: str) -> bool:
    name = Path(value).name.lower()
    return (
        name in {"ld", "ld.exe", "ld.lld", "ld.lld.exe", "lld-link", "lld-link.exe", "link", "link.exe"}
        or name.endswith("-ld")
        or name.endswith("-ld.exe")
    )


def _linker_identity_from_trace(
    clang: Path,
    link_arguments: Sequence[str],
    cwd: Path,
    environment: Mapping[str, str],
    timeout: float,
) -> dict[str, Any]:
    trace = _run_bytes([str(clang), "-###", *link_arguments], cwd=cwd, environment=environment, timeout=timeout)
    trace_bytes = trace.stdout + trace.stderr
    trace_text = _decode(trace_bytes, "Clang linker trace")
    candidates: list[str] = []
    for line in trace_text.splitlines():
        match = re.match(r'^\s*"([^"]+)"', line)
        first = match.group(1) if match else (line.strip().split(" ", 1)[0] if line.strip() else "")
        if first and _is_linker_name(first):
            candidates.append(first)
    if trace.returncode != 0 or not candidates:
        raise LabError(
            f"Clang did not expose a linker for recorded invocation (exit={trace.returncode})\n{trace_text}"
        )
    linker_value = candidates[-1]
    linker = Path(linker_value)
    if not linker.is_absolute():
        found = shutil.which(linker_value, path=environment.get("PATH"))
        if not found:
            raise LabError(f"observed linker is not resolvable: {linker_value}")
        linker = Path(found)
    elif sys.platform == "win32" and not linker.is_file() and not str(linker).lower().endswith(".exe"):
        executable = Path(str(linker) + ".exe")
        if executable.is_file():
            linker = executable
    linker = linker.resolve(strict=True)
    version = _run_bytes([str(linker), "--version"], cwd=cwd, environment=environment, timeout=timeout)
    return {
        "observed_path": linker_value,
        "path": str(linker),
        "sha256": _sha256_file(linker),
        "bytes": linker.stat().st_size,
        "version_exit_code": version.returncode,
        "version_stdout_base64": _encode_bytes(version.stdout),
        "version_stderr_base64": _encode_bytes(version.stderr),
        "trace_raw_base64": _encode_bytes(trace_bytes),
        "trace_sha256": _sha256_bytes(trace_bytes),
    }


def _compile_observation(
    *,
    recording_log: Path,
    recording_wrapper_sha256: str,
    source_snapshot_sha256: str,
    real_clang: Path,
    lane_dir: Path,
    environment: Mapping[str, str],
    backend: str,
    profile: str,
    target_argument: str | None,
    backend_artifact: Path,
    timeout: float,
) -> dict[str, Any]:
    raw_invocations = _read_recording_log(recording_log)
    build_invocations = [arguments for arguments in raw_invocations if "-o" in arguments]
    probe_invocations = [arguments for arguments in raw_invocations if "-o" not in arguments]
    if not build_invocations:
        raise LabError("recording Clang observed no build invocation")
    flattened = [argument for invocation in build_invocations for argument in invocation]
    optimization_flags = sorted(set(argument for argument in flattened if re.fullmatch(r"-O[^/\\]*", argument)))
    lto_flags = sorted(set(argument for argument in flattened if argument.startswith("-flto")))
    target_flags = sorted(set(argument for argument in flattened if argument.startswith("--target=")))
    linker_flags = sorted(set(argument for argument in flattened if argument.startswith("-fuse-ld=")))
    profile_spec = _PROFILE_SPECS[profile]
    if optimization_flags != [profile_spec["opt"]]:
        raise LabError(
            f"recorded optimization flags {optimization_flags} do not implement requested profile {profile}"
        )
    if lto_flags != profile_spec["lto"]:
        raise LabError(f"recorded LTO flags {lto_flags} do not implement requested profile {profile}")
    expected_targets = [f"--target={target_argument}"] if target_argument else []
    if target_flags != expected_targets:
        raise LabError(f"recorded target flags {target_flags} differ from request {expected_targets}")
    if any(argument in {"-Ofast", "-ffast-math", "-march=native"} for argument in flattened):
        raise LabError("recorded build used a forbidden unsafe optimization flag")

    artifact_path = backend_artifact.resolve(strict=True)
    recorded_paths: set[Path] = set()
    for argument in flattened:
        if argument.endswith((".c", ".ll")):
            try:
                recorded_paths.add(_resolve_recorded_path(argument, lane_dir, "recorded compiler input"))
            except LabError:
                continue
    if artifact_path not in recorded_paths:
        raise LabError("recorded Clang did not consume the generated backend artifact")

    runtime_inputs: list[dict[str, Any]] = []
    seen_runtime_paths: set[Path] = set()
    for argument in flattened:
        if Path(argument).name not in _RUNTIME_INPUT_NAMES:
            continue
        runtime_path = _resolve_recorded_path(argument, lane_dir, "recorded runtime input")
        if runtime_path in seen_runtime_paths:
            continue
        seen_runtime_paths.add(runtime_path)
        runtime_inputs.append(
            {
                "name": runtime_path.name,
                "path": str(runtime_path),
                "bytes": runtime_path.stat().st_size,
                "sha256": _sha256_file(runtime_path),
            }
        )
    runtime_inputs.sort(key=lambda value: (value["name"], value["path"]))
    runtime_names = {value["name"] for value in runtime_inputs}
    plan = _runtime_plan(runtime_names)
    if plan == "missing":
        raise LabError("recorded build has no runtime source or object inputs")
    if profile == "+03" and plan != "source":
        raise LabError("+03 must link runtime sources in the LTO unit")
    required_runtime = {"freak_runtime.c"} if plan in {"source", "bundle-source-fallback"} else {"freak_runtime.obj", "freak_runtime.o"}
    if not (runtime_names & required_runtime):
        raise LabError("recorded build omits the base runtime")
    if backend == "llvm":
        llvm_names = {"freak_llvm_runtime.c", "freak_llvm_runtime.o", "freak_llvm_runtime.obj"}
        if not (runtime_names & llvm_names):
            raise LabError("recorded LLVM build omits the LLVM runtime")

    link_invocations = [arguments for arguments in build_invocations if "-c" not in arguments]
    if not link_invocations:
        raise LabError("recording Clang observed no link invocation")
    linker = _linker_identity_from_trace(
        real_clang,
        link_invocations[-1],
        lane_dir,
        environment,
        timeout,
    )
    return {
        "schema": COMPILE_OBSERVATION_SCHEMA,
        "source_snapshot_sha256": source_snapshot_sha256,
        "recording_wrapper_sha256": recording_wrapper_sha256,
        "probe_invocations": [_invocation_record(arguments) for arguments in probe_invocations],
        "invocations": [_invocation_record(arguments) for arguments in build_invocations],
        "optimization_flags": optimization_flags,
        "lto_flags": lto_flags,
        "target_flags": target_flags,
        "linker_flags": linker_flags,
        "runtime_plan": plan,
        "runtime_inputs": runtime_inputs,
        "backend_artifact": {
            "suffix": backend_artifact.suffix,
            "bytes": backend_artifact.stat().st_size,
            "sha256": _sha256_file(backend_artifact),
            "content_zlib_base64": _encode_zlib_bytes(backend_artifact.read_bytes()),
        },
        "linker": linker,
    }


def _verify_completed(
    completed: subprocess.CompletedProcess[bytes],
    mode: Mapping[str, Any],
    context: str,
) -> tuple[str, str, dict[str, Any] | None, list[str]]:
    stdout = _canonical_output(completed.stdout, f"{context} stdout")
    raw_stderr = _canonical_output(completed.stderr, f"{context} stderr")
    stderr, counter, failures = _strip_runtime_stats(raw_stderr)
    failures = list(failures)
    if completed.returncode != mode["expected_exit_code"]:
        failures.append(f"exit code {completed.returncode}, expected {mode['expected_exit_code']}")
    if stdout != mode["expected_stdout"]:
        failures.append("stdout differs from manifest")
    if stderr != mode["expected_stderr"]:
        failures.append("stderr differs from manifest after stats removal")
    if _sha256_text(stdout) != mode["expected_stdout_sha256"]:
        failures.append("stdout checksum differs from manifest")
    if _sha256_text(stderr) != mode["expected_stderr_sha256"]:
        failures.append("stderr checksum differs from manifest")
    return stdout, stderr, counter, failures


def _one_result(
    *,
    cli: Path,
    environment: Mapping[str, str],
    case: Mapping[str, Any],
    mode_name: str,
    manifest_dir: Path,
    work_dir: Path,
    backend: str,
    profile: str,
    target_argument: str | None,
    resolved_target: str,
    samples: int,
    warmups: int,
    timeout: float,
    real_clang: Path,
    recording_log: Path,
    recording_wrapper_sha256: str,
) -> dict[str, Any]:
    mode = case["modes"][mode_name]
    source = manifest_dir / case["source"]
    lane_dir = work_dir / case["id"] / backend / _PROFILE_SPECS[profile]["id"]
    lane_dir.mkdir(parents=True)
    copied_source = lane_dir / source.name
    shutil.copyfile(source, copied_source)
    if _sha256_source_file(copied_source) != case["source_sha256"]:
        raise LabError(f"copied source differs from manifest snapshot: {case['source']}")

    compile_command = [
        str(cli),
        "build",
        str(copied_source),
        _BACKEND_SPECS[backend],
        *_PROFILE_SPECS[profile]["arguments"],
    ]
    if target_argument:
        compile_command.append(f"--target={target_argument}")
    recording_log.unlink(missing_ok=True)
    compile_start = time.perf_counter_ns()
    compiled = _run_bytes(compile_command, cwd=lane_dir, environment=environment, timeout=timeout)
    compile_ns = time.perf_counter_ns() - compile_start
    if compiled.returncode != 0:
        stdout = _decode(compiled.stdout, "compiler stdout")
        stderr = _decode(compiled.stderr, "compiler stderr")
        raise LabError(
            f"build failed for {case['id']}/{backend}/{profile} with exit code "
            f"{compiled.returncode}\nstdout:\n{stdout}\nstderr:\n{stderr}"
        )
    if _sha256_source_file(copied_source) != case["source_sha256"]:
        raise LabError(f"compiled source changed during build: {case['source']}")
    backend_artifact = Path(str(copied_source) + (".c" if backend == "c" else ".ll"))
    unexpected_artifact = Path(str(copied_source) + (".ll" if backend == "c" else ".c"))
    if not backend_artifact.is_file() or unexpected_artifact.exists():
        raise LabError(
            f"build did not produce exactly the requested {backend} artifact for {case['id']}"
        )
    compile_observation = _compile_observation(
        recording_log=recording_log,
        recording_wrapper_sha256=recording_wrapper_sha256,
        source_snapshot_sha256=case["source_sha256"],
        real_clang=real_clang,
        lane_dir=lane_dir,
        environment=environment,
        backend=backend,
        profile=profile,
        target_argument=target_argument,
        backend_artifact=backend_artifact,
        timeout=timeout,
    )
    binary = _binary_path(copied_source)

    run_command = [str(binary), *mode["arguments"]]
    for warmup_index in range(warmups):
        warmed = _run_bytes(run_command, cwd=lane_dir, environment=environment, timeout=timeout)
        _, _, _, warmup_failures = _verify_completed(
            warmed,
            mode,
            f"warmup {warmup_index} for {case['id']}/{backend}/{profile}",
        )
        if warmup_failures:
            raise LabError(
                f"warmup failed for {case['id']}/{backend}/{profile}: {warmup_failures}"
            )

    run_samples: list[dict[str, Any]] = []
    durations: list[int] = []
    counters: list[dict[str, Any] | None] = []
    failures: list[str] = []
    for sample_index in range(samples):
        run_start = time.perf_counter_ns()
        completed = _run_bytes(run_command, cwd=lane_dir, environment=environment, timeout=timeout)
        duration_ns = time.perf_counter_ns() - run_start
        stdout, stderr, counter, sample_failures = _verify_completed(
            completed,
            mode,
            f"sample {sample_index} for {case['id']}/{backend}/{profile}",
        )
        failures.extend(f"sample {sample_index}: {failure}" for failure in sample_failures)
        durations.append(duration_ns)
        counters.append(counter)
        run_samples.append(
            {
                "index": sample_index,
                "duration_ns": duration_ns,
                "exit_code": completed.returncode,
                "stdout": stdout,
                "stdout_sha256": _sha256_text(stdout),
                "stdout_raw_sha256": _sha256_bytes(completed.stdout),
                "stdout_raw_base64": _encode_bytes(completed.stdout),
                "stderr": stderr,
                "stderr_sha256": _sha256_text(stderr),
                "stderr_raw_sha256": _sha256_bytes(completed.stderr),
                "stderr_raw_base64": _encode_bytes(completed.stderr),
            }
        )

    present_counters = [counter for counter in counters if counter is not None]
    if present_counters and len(present_counters) != len(counters):
        failures.append("runtime stats sentinel was emitted for only some samples")
    runtime_counters: dict[str, Any] | None
    runtime_counters_reason: str | None
    if len(present_counters) == len(counters):
        runtime_counters = {"samples": present_counters}
        runtime_counters_reason = None
    else:
        runtime_counters = None
        runtime_counters_reason = (
            "runtime stats sentinel was emitted for only some samples"
            if present_counters
            else RUNTIME_COUNTERS_UNAVAILABLE_REASON
        )

    profile_spec = _PROFILE_SPECS[profile]
    return {
        "case": case["id"],
        "category": case["category"],
        "source": case["source"],
        "source_sha256": case["source_sha256"],
        "backend": backend,
        "profile": profile,
        "profile_id": profile_spec["id"],
        "profile_display": profile_spec["display"],
        "target": resolved_target,
        "workload": {
            "mode": mode_name,
            "arguments": mode["arguments"],
            "parameters": mode["parameters"],
            "expected_exit_code": mode["expected_exit_code"],
            "expected_stdout": mode["expected_stdout"],
            "expected_stdout_sha256": mode["expected_stdout_sha256"],
            "expected_stderr": mode["expected_stderr"],
            "expected_stderr_sha256": mode["expected_stderr_sha256"],
        },
        "compile": {
            "duration_ns": compile_ns,
            "stdout_raw_base64": _encode_bytes(compiled.stdout),
            "stdout_sha256": _sha256_bytes(compiled.stdout),
            "stderr_raw_base64": _encode_bytes(compiled.stderr),
            "stderr_sha256": _sha256_bytes(compiled.stderr),
            "command": compile_command,
            "command_sha256": _json_sha256(compile_command),
            "observation": compile_observation,
        },
        "binary": {
            "bytes": binary.stat().st_size,
            "sha256": _sha256_file(binary),
            "content_zlib_base64": _encode_zlib_bytes(binary.read_bytes()),
        },
        "run": {"samples": run_samples, "median_ns": int(statistics.median(durations))},
        "peak_rss_bytes": None,
        "peak_rss_reason": RSS_UNAVAILABLE_REASON,
        "runtime_counters": runtime_counters,
        "runtime_counters_reason": runtime_counters_reason,
        "verification": {"passed": not failures, "failures": failures},
    }


def run_lab(args: argparse.Namespace) -> dict[str, Any]:
    manifest_path = Path(args.manifest).expanduser().resolve(strict=True)
    manifest = load_manifest(manifest_path)
    cli = _resolve_exact_executable(args.cli, "FREAK CLI")
    clang = _resolve_clang(args.clang)
    identity_environment = _clean_environment(clang)

    with tempfile.TemporaryDirectory(prefix="freak-v3-performance-lab-") as temporary:
        work_dir = Path(temporary).resolve()
        snapshot_dir = work_dir / "source-snapshot"
        _snapshot_sources(manifest, manifest_path.parent, snapshot_dir)
        wrapper, recording_log, recording_wrapper_sha256 = _write_recording_clang(work_dir, clang)
        environment = dict(identity_environment)
        environment["FREAK_CLANG"] = str(wrapper)
        environment["FREAK_PERF_REAL_CLANG"] = str(clang)
        environment["FREAK_PERF_CLANG_LOG"] = str(recording_log)
        compiler, help_text = _compiler_identity(cli, identity_environment, work_dir, args.timeout)
        toolchain = _tool_identity(clang, identity_environment, work_dir, args.timeout)
        available_profiles = _available_profiles(help_text)
        profiles = _selected_profiles(args.profile, available_profiles)
        backends = _selected_values(args.backend, _BACKEND_SPECS, "backends")
        available_cases = [case["id"] for case in manifest["cases"]]
        cases = _selected_values(args.case, available_cases, "cases")
        selected_cases = {case["id"]: case for case in manifest["cases"] if case["id"] in cases}

        mode_name = "quick" if args.quick else "default"
        samples = args.samples if args.samples is not None else (1 if args.quick else 5)
        warmups = args.warmups if args.warmups is not None else (0 if args.quick else 1)
        if samples < 1 or samples % 2 == 0:
            raise LabError("--samples must be a positive odd integer")
        if warmups < 0:
            raise LabError("--warmups must be non-negative")
        resolved_target = args.target or toolchain["target_triple"]

        results: list[dict[str, Any]] = []
        for case_id in cases:
            for backend in backends:
                for profile in profiles:
                    results.append(
                        _one_result(
                            cli=cli,
                            environment=environment,
                            case=selected_cases[case_id],
                            mode_name=mode_name,
                            manifest_dir=snapshot_dir,
                            work_dir=work_dir,
                            backend=backend,
                            profile=profile,
                            target_argument=args.target,
                            resolved_target=resolved_target,
                            samples=samples,
                            warmups=warmups,
                            timeout=args.timeout,
                            real_clang=clang,
                            recording_log=recording_log,
                            recording_wrapper_sha256=recording_wrapper_sha256,
                        )
                    )

    document = {
        "schema": RESULT_SCHEMA,
        "lab": {
            "path": str(Path(__file__).resolve()),
            "sha256": _sha256_file(Path(__file__).resolve()),
        },
        "manifest": {
            "path": str(manifest_path),
            "schema": manifest["schema"],
            "sha256": _sha256_file(manifest_path),
        },
        "compiler": compiler,
        "toolchain": toolchain,
        "host": _host_identity(),
        "target": {"requested": args.target or "host", "resolved": resolved_target},
        "configuration": {
            "mode": mode_name,
            "cases": cases,
            "backends": backends,
            "profiles": profiles,
            "available_profiles": available_profiles,
            "samples": samples,
            "warmups": warmups,
        },
        "results": results,
        "verification": {
            "passed": all(result["verification"]["passed"] for result in results),
            "failed_results": [
                f"{result['case']}/{result['backend']}/{result['profile']}"
                for result in results
                if not result["verification"]["passed"]
            ],
        },
    }
    return document


def _validate_invocation_record(value: Any, context: str) -> list[str]:
    record = _require_dict(value, context)
    _exact_keys(record, {"argv", "argv_sha256"}, context)
    arguments = _require_string_list(record.get("argv"), f"{context}.argv")
    if record.get("argv_sha256") != _json_sha256(arguments):
        raise LabError(f"{context}.argv checksum is invalid")
    return arguments


def _validate_linker_identity(
    value: Any,
    context: str,
    environment: Mapping[str, str],
    timeout: float,
) -> dict[str, Any]:
    linker = _require_dict(value, context)
    expected_keys = {
        "observed_path",
        "path",
        "sha256",
        "bytes",
        "version_exit_code",
        "version_stdout_base64",
        "version_stderr_base64",
        "trace_raw_base64",
        "trace_sha256",
    }
    _exact_keys(linker, expected_keys, context)
    observed_path = _require_string(linker.get("observed_path"), f"{context}.observed_path", nonempty=True)
    path = _resolve_exact_executable(_require_string(linker.get("path"), f"{context}.path"), "result linker")
    if linker.get("sha256") != _sha256_file(path) or linker.get("bytes") != path.stat().st_size:
        raise LabError(f"{context} provenance is stale")
    stdout = _decode_bytes(linker.get("version_stdout_base64"), f"{context}.version_stdout_base64")
    stderr = _decode_bytes(linker.get("version_stderr_base64"), f"{context}.version_stderr_base64")
    version = _run_bytes([str(path), "--version"], cwd=path.parent, environment=environment, timeout=timeout)
    if (
        linker.get("version_exit_code") != version.returncode
        or stdout != version.stdout
        or stderr != version.stderr
    ):
        raise LabError(f"{context} live version identity differs")
    trace = _decode_bytes(linker.get("trace_raw_base64"), f"{context}.trace_raw_base64")
    if linker.get("trace_sha256") != _sha256_bytes(trace):
        raise LabError(f"{context} trace checksum is invalid")
    if observed_path.encode("utf-8") not in trace and Path(observed_path).name.encode("utf-8") not in trace:
        raise LabError(f"{context} trace does not name the recorded linker")
    observed = Path(observed_path)
    if observed.is_absolute():
        normalized = str(observed)
        if sys.platform == "win32" and not normalized.lower().endswith(".exe"):
            normalized += ".exe"
        if os.path.normcase(os.path.normpath(normalized)) != os.path.normcase(os.path.normpath(str(path))):
            raise LabError(f"{context} observed and resolved linker paths differ")
    elif Path(observed_path).name.lower().removesuffix(".exe") != path.name.lower().removesuffix(".exe"):
        raise LabError(f"{context} observed and resolved linker names differ")
    return linker


def _validate_compile_observation(
    value: Any,
    *,
    context: str,
    backend: str,
    profile: str,
    target_requested: str,
    source_name: str,
    source_sha256: str,
    environment: Mapping[str, str],
    timeout: float,
) -> None:
    observation = _require_dict(value, context)
    _exact_keys(observation, _COMPILE_OBSERVATION_KEYS, context)
    if observation.get("schema") != COMPILE_OBSERVATION_SCHEMA:
        raise LabError(f"{context}.schema is invalid")
    if observation.get("source_snapshot_sha256") != source_sha256:
        raise LabError(f"{context}.source_snapshot_sha256 differs from the compiled source")
    if not re.fullmatch(r"[0-9a-f]{64}", str(observation.get("recording_wrapper_sha256", ""))):
        raise LabError(f"{context}.recording_wrapper_sha256 is invalid")
    probes = _require_list(observation.get("probe_invocations"), f"{context}.probe_invocations")
    probe_arguments = [
        _validate_invocation_record(value, f"{context}.probe_invocations[{index}]")
        for index, value in enumerate(probes)
    ]
    if not any("--version" in arguments for arguments in probe_arguments):
        raise LabError(f"{context} lacks the CLI's Clang identity probe")
    raw_invocations = _require_list(observation.get("invocations"), f"{context}.invocations")
    invocations = [
        _validate_invocation_record(value, f"{context}.invocations[{index}]")
        for index, value in enumerate(raw_invocations)
    ]
    if not invocations:
        raise LabError(f"{context} has no build invocations")
    flattened = [argument for invocation in invocations for argument in invocation]
    derived_opt = sorted(set(argument for argument in flattened if re.fullmatch(r"-O[^/\\]*", argument)))
    derived_lto = sorted(set(argument for argument in flattened if argument.startswith("-flto")))
    derived_target = sorted(set(argument for argument in flattened if argument.startswith("--target=")))
    derived_linker = sorted(set(argument for argument in flattened if argument.startswith("-fuse-ld=")))
    profile_spec = _PROFILE_SPECS[profile]
    expected_target = [] if target_requested == "host" else [f"--target={target_requested}"]
    if observation.get("optimization_flags") != derived_opt or derived_opt != [profile_spec["opt"]]:
        raise LabError(f"{context} optimization flags do not implement {profile}")
    if observation.get("lto_flags") != derived_lto or derived_lto != profile_spec["lto"]:
        raise LabError(f"{context} LTO flags do not implement {profile}")
    if observation.get("target_flags") != derived_target or derived_target != expected_target:
        raise LabError(f"{context} target flags differ from the request")
    if observation.get("linker_flags") != derived_linker:
        raise LabError(f"{context} linker flags are inconsistent")
    if any(argument in {"-Ofast", "-ffast-math", "-march=native"} for argument in flattened):
        raise LabError(f"{context} contains an unsafe optimization flag")
    expected_suffix = ".c" if backend == "c" else ".ll"
    expected_artifact_name = source_name + expected_suffix
    if not any(Path(argument).name == Path(expected_artifact_name).name for argument in flattened):
        raise LabError(f"{context} does not consume the requested backend artifact")

    raw_inputs = _require_list(observation.get("runtime_inputs"), f"{context}.runtime_inputs")
    runtime_names: set[str] = set()
    paths_seen: set[str] = set()
    for index, raw_input in enumerate(raw_inputs):
        item_context = f"{context}.runtime_inputs[{index}]"
        item = _require_dict(raw_input, item_context)
        _exact_keys(item, {"name", "path", "bytes", "sha256"}, item_context)
        path = _resolve_exact_executable(_require_string(item.get("path"), f"{item_context}.path"), "runtime input")
        if item.get("name") != path.name or path.name not in _RUNTIME_INPUT_NAMES:
            raise LabError(f"{item_context} name is invalid")
        if str(path) in paths_seen:
            raise LabError(f"{context} repeats a runtime input")
        paths_seen.add(str(path))
        runtime_names.add(path.name)
        if item.get("bytes") != path.stat().st_size or item.get("sha256") != _sha256_file(path):
            raise LabError(f"{item_context} provenance is stale")
    derived_plan = _runtime_plan(runtime_names)
    if observation.get("runtime_plan") != derived_plan or derived_plan == "missing":
        raise LabError(f"{context} runtime plan is invalid")
    if profile == "+03" and derived_plan != "source":
        raise LabError(f"{context} +03 runtime plan is not source-linked")
    if not (runtime_names & {"freak_runtime.c", "freak_runtime.o", "freak_runtime.obj"}):
        raise LabError(f"{context} omits the base runtime")
    if backend == "llvm" and not (
        runtime_names & {"freak_llvm_runtime.c", "freak_llvm_runtime.o", "freak_llvm_runtime.obj"}
    ):
        raise LabError(f"{context} omits the LLVM runtime")

    artifact = _require_dict(observation.get("backend_artifact"), f"{context}.backend_artifact")
    _exact_keys(artifact, _ARTIFACT_KEYS, f"{context}.backend_artifact")
    if artifact.get("suffix") != expected_suffix:
        raise LabError(f"{context} backend artifact suffix is invalid")
    artifact_size = _require_int(
        artifact.get("bytes"),
        f"{context}.backend_artifact.bytes",
        minimum=1,
    )
    artifact_bytes = _decode_zlib_bytes(
        artifact.get("content_zlib_base64"),
        artifact_size,
        f"{context}.backend_artifact.content_zlib_base64",
    )
    if (
        not artifact_bytes
        or artifact.get("bytes") != len(artifact_bytes)
        or artifact.get("sha256") != _sha256_bytes(artifact_bytes)
    ):
        raise LabError(f"{context} backend artifact provenance is invalid")
    _validate_linker_identity(observation.get("linker"), f"{context}.linker", environment, timeout)


def validate_output(path: Path, *, cli_override: str | None = None) -> dict[str, Any]:
    """Reject malformed, internally inconsistent, or stale lab output."""

    document = _require_dict(_strict_json(path.resolve(strict=True)), "result")
    required_root = {
        "schema",
        "lab",
        "manifest",
        "compiler",
        "toolchain",
        "host",
        "target",
        "configuration",
        "results",
        "verification",
    }
    _exact_keys(document, required_root, "result")
    if document["schema"] != RESULT_SCHEMA:
        raise LabError(f"unsupported result schema: {document['schema']!r}")

    manifest_info = _require_dict(document["manifest"], "result.manifest")
    _exact_keys(manifest_info, {"path", "schema", "sha256"}, "result.manifest")
    manifest_path = Path(_require_string(manifest_info.get("path"), "result.manifest.path")).resolve(strict=True)
    if manifest_info.get("schema") != MANIFEST_SCHEMA:
        raise LabError("result manifest schema is invalid")
    if manifest_info.get("sha256") != _sha256_file(manifest_path):
        raise LabError("result manifest hash is stale")
    manifest = load_manifest(manifest_path)

    lab_info = _require_dict(document["lab"], "result.lab")
    _exact_keys(lab_info, {"path", "sha256"}, "result.lab")
    lab_path = Path(_require_string(lab_info.get("path"), "result.lab.path")).resolve(strict=True)
    if lab_info.get("sha256") != _sha256_file(lab_path):
        raise LabError("result lab hash is stale")

    compiler = _require_dict(document["compiler"], "result.compiler")
    compiler_keys = {
        "path",
        "sha256",
        "bytes",
        "version",
        "version_stdout",
        "version_stderr",
        "version_output_sha256",
        "help_stdout",
        "help_stderr",
        "help_output_sha256",
    }
    _exact_keys(
        compiler,
        compiler_keys,
        "result.compiler",
    )
    stored_compiler_path = _require_string(compiler.get("path"), "result.compiler.path", nonempty=True)
    compiler_path = _resolve_exact_executable(cli_override or stored_compiler_path, "result compiler")
    if compiler.get("path") != str(compiler_path) or compiler.get("sha256") != _sha256_file(compiler_path):
        raise LabError("result compiler provenance is stale")
    if compiler.get("bytes") != compiler_path.stat().st_size:
        raise LabError("result compiler size is stale")
    version_stdout = _require_string(compiler.get("version_stdout"), "result.compiler.version_stdout")
    version_stderr = _require_string(compiler.get("version_stderr"), "result.compiler.version_stderr")
    if compiler.get("version_output_sha256") != _sha256_text(version_stdout + version_stderr):
        raise LabError("result compiler version checksum is invalid")
    if compiler.get("version") != (version_stdout.strip() or version_stderr.strip()):
        raise LabError("result compiler version text is inconsistent")
    help_stdout = _require_string(compiler.get("help_stdout"), "result.compiler.help_stdout")
    help_stderr = _require_string(compiler.get("help_stderr"), "result.compiler.help_stderr")
    if compiler.get("help_output_sha256") != _sha256_text(help_stdout + help_stderr):
        raise LabError("result compiler help checksum is invalid")

    toolchain = _require_dict(document["toolchain"], "result.toolchain")
    _exact_keys(toolchain, {"path", "sha256", "bytes", "version", "target_triple"}, "result.toolchain")
    clang_path = _resolve_exact_executable(
        _require_string(toolchain.get("path"), "result.toolchain.path", nonempty=True),
        "result Clang",
    )
    if toolchain.get("sha256") != _sha256_file(clang_path) or toolchain.get("bytes") != clang_path.stat().st_size:
        raise LabError("result toolchain provenance is stale")
    validation_environment = _clean_environment(clang_path)
    validation_timeout = 30.0
    with tempfile.TemporaryDirectory(prefix="freak-v3-performance-validate-") as temporary:
        validation_cwd = Path(temporary).resolve()
        live_compiler, live_help = _compiler_identity(
            compiler_path,
            validation_environment,
            validation_cwd,
            validation_timeout,
        )
        live_toolchain = _tool_identity(
            clang_path,
            validation_environment,
            validation_cwd,
            validation_timeout,
        )
    if compiler != live_compiler:
        raise LabError("result compiler version/help identity differs from the live executable")
    if toolchain != live_toolchain:
        raise LabError("result toolchain version/target identity differs from the live executable")
    detected_profiles = _available_profiles(live_help)

    configuration = _require_dict(document["configuration"], "result.configuration")
    _exact_keys(
        configuration,
        {"mode", "cases", "backends", "profiles", "available_profiles", "samples", "warmups"},
        "result.configuration",
    )
    mode_name = configuration.get("mode")
    if mode_name not in {"default", "quick"}:
        raise LabError("result configuration mode is invalid")
    cases = _require_string_list(configuration.get("cases"), "result.configuration.cases")
    backends = _require_string_list(configuration.get("backends"), "result.configuration.backends")
    profiles = _require_string_list(configuration.get("profiles"), "result.configuration.profiles")
    available_profiles = _require_string_list(
        configuration.get("available_profiles"),
        "result.configuration.available_profiles",
    )
    samples = _require_int(configuration.get("samples"), "result.configuration.samples", minimum=1)
    _require_int(configuration.get("warmups"), "result.configuration.warmups", minimum=0)
    if samples % 2 == 0:
        raise LabError("result sample count must be odd")
    if not cases or not backends or not profiles:
        raise LabError("result configuration dimensions must be non-empty")
    if len(set(cases)) != len(cases) or len(set(backends)) != len(backends) or len(set(profiles)) != len(profiles):
        raise LabError("result configuration dimensions must be unique")

    manifest_cases = {case["id"]: case for case in manifest["cases"]}
    if any(case not in manifest_cases for case in cases):
        raise LabError("result contains an unknown case")
    if any(backend not in _BACKEND_SPECS for backend in backends):
        raise LabError("result contains an unknown backend")
    if any(profile not in _PROFILE_SPECS for profile in profiles):
        raise LabError("result contains an unknown profile")
    if available_profiles != detected_profiles or not set(profiles) <= set(available_profiles):
        raise LabError("result available profile inventory is invalid")
    host = _require_dict(document["host"], "result.host")
    _exact_keys(
        host,
        {"system", "release", "version", "machine", "processor", "logical_cpu_count", "python"},
        "result.host",
    )
    if host != _host_identity():
        raise LabError("result host identity differs from the validation host")
    target = _require_dict(document["target"], "result.target")
    _exact_keys(target, {"requested", "resolved"}, "result.target")
    requested_target = _require_string(target.get("requested"), "result.target.requested", nonempty=True)
    resolved_target = _require_string(target.get("resolved"), "result.target.resolved", nonempty=True)
    if (requested_target == "host" and resolved_target != toolchain["target_triple"]) or (
        requested_target != "host" and resolved_target != requested_target
    ):
        raise LabError("result target resolution is inconsistent")
    expected_combinations = {(case, backend, profile) for case in cases for backend in backends for profile in profiles}

    results = _require_list(document["results"], "result.results")
    actual_combinations: set[tuple[str, str, str]] = set()
    for index, raw_result in enumerate(results):
        context = f"result.results[{index}]"
        result = _require_dict(raw_result, context)
        _exact_keys(result, _RESULT_KEYS, context)
        combination = (
            _require_string(result.get("case"), f"{context}.case", nonempty=True),
            _require_string(result.get("backend"), f"{context}.backend", nonempty=True),
            _require_string(result.get("profile"), f"{context}.profile", nonempty=True),
        )
        if combination in actual_combinations:
            raise LabError(f"duplicate result combination: {combination}")
        actual_combinations.add(combination)
        if combination not in expected_combinations:
            raise LabError(f"unexpected result combination: {combination}")
        case = manifest_cases[combination[0]]
        mode = case["modes"][mode_name]
        if result.get("category") != case["category"]:
            raise LabError(f"{context} category differs from manifest")
        if result.get("source") != case["source"] or result.get("source_sha256") != case["source_sha256"]:
            raise LabError(f"{context} source provenance differs from manifest")
        profile_spec = _PROFILE_SPECS[combination[2]]
        if result.get("profile_id") != profile_spec["id"] or result.get("profile_display") != profile_spec["display"]:
            raise LabError(f"{context} profile spelling is not canonical")
        if result.get("target") != resolved_target:
            raise LabError(f"{context} target differs from root provenance")
        workload = _require_dict(result.get("workload"), f"{context}.workload")
        _exact_keys(workload, _WORKLOAD_KEYS, f"{context}.workload")
        expected_workload = {
            "mode": mode_name,
            "arguments": mode["arguments"],
            "parameters": mode["parameters"],
            "expected_exit_code": mode["expected_exit_code"],
            "expected_stdout": mode["expected_stdout"],
            "expected_stdout_sha256": mode["expected_stdout_sha256"],
            "expected_stderr": mode["expected_stderr"],
            "expected_stderr_sha256": mode["expected_stderr_sha256"],
        }
        if workload != expected_workload:
            raise LabError(f"{context} workload differs from manifest")
        compile_info = _require_dict(result.get("compile"), f"{context}.compile")
        _exact_keys(compile_info, _COMPILE_KEYS, f"{context}.compile")
        _require_int(compile_info.get("duration_ns"), f"{context}.compile.duration_ns", minimum=0)
        for channel in ("stdout", "stderr"):
            raw = _decode_bytes(
                compile_info.get(f"{channel}_raw_base64"),
                f"{context}.compile.{channel}_raw_base64",
            )
            if compile_info.get(f"{channel}_sha256") != _sha256_bytes(raw):
                raise LabError(f"{context} compiler {channel} checksum is invalid")
        compile_command = _require_string_list(
            compile_info.get("command"),
            f"{context}.compile.command",
        )
        if compile_info.get("command_sha256") != _json_sha256(compile_command):
            raise LabError(f"{context} compile command checksum is invalid")
        expected_tail = [_BACKEND_SPECS[combination[1]], *_PROFILE_SPECS[combination[2]]["arguments"]]
        if requested_target != "host":
            expected_tail.append(f"--target={requested_target}")
        if (
            len(compile_command) != 3 + len(expected_tail)
            or compile_command[0] != str(compiler_path)
            or compile_command[1] != "build"
            or Path(compile_command[2]).name != Path(case["source"]).name
            or compile_command[3:] != expected_tail
        ):
            raise LabError(f"{context} compile command differs from its result dimensions")
        _validate_compile_observation(
            compile_info.get("observation"),
            context=f"{context}.compile.observation",
            backend=combination[1],
            profile=combination[2],
            target_requested=requested_target,
            source_name=case["source"],
            source_sha256=case["source_sha256"],
            environment=validation_environment,
            timeout=validation_timeout,
        )
        binary = _require_dict(result.get("binary"), f"{context}.binary")
        _exact_keys(binary, _BINARY_KEYS, f"{context}.binary")
        binary_size = _require_int(binary.get("bytes"), f"{context}.binary.bytes", minimum=1)
        binary_bytes = _decode_zlib_bytes(
            binary.get("content_zlib_base64"),
            binary_size,
            f"{context}.binary.content_zlib_base64",
        )
        if (
            not binary_bytes
            or binary.get("bytes") != len(binary_bytes)
            or binary.get("sha256") != _sha256_bytes(binary_bytes)
        ):
            raise LabError(f"{context} binary provenance is invalid")
        run = _require_dict(result.get("run"), f"{context}.run")
        _exact_keys(run, {"samples", "median_ns"}, f"{context}.run")
        raw_samples = _require_list(run.get("samples"), f"{context}.run.samples")
        if len(raw_samples) != samples:
            raise LabError(f"{context} has the wrong sample count")
        durations: list[int] = []
        observed_counters: list[dict[str, Any] | None] = []
        for sample_index, raw_sample in enumerate(raw_samples):
            sample = _require_dict(raw_sample, f"{context}.run.samples[{sample_index}]")
            _exact_keys(sample, _SAMPLE_KEYS, f"{context}.run.samples[{sample_index}]")
            if sample.get("index") != sample_index:
                raise LabError(f"{context} sample indexes are not canonical")
            duration = _require_int(sample.get("duration_ns"), f"{context} sample duration", minimum=0)
            durations.append(duration)
            if sample.get("exit_code") != mode["expected_exit_code"]:
                raise LabError(f"{context} sample exit code differs from manifest")
            raw_stdout = _decode_bytes(
                sample.get("stdout_raw_base64"),
                f"{context}.run.samples[{sample_index}].stdout_raw_base64",
            )
            raw_stderr = _decode_bytes(
                sample.get("stderr_raw_base64"),
                f"{context}.run.samples[{sample_index}].stderr_raw_base64",
            )
            if sample.get("stdout_raw_sha256") != _sha256_bytes(raw_stdout):
                raise LabError(f"{context} sample raw stdout checksum is invalid")
            if sample.get("stderr_raw_sha256") != _sha256_bytes(raw_stderr):
                raise LabError(f"{context} sample raw stderr checksum is invalid")
            canonical_stdout = _canonical_output(raw_stdout, f"{context} sample stdout")
            canonical_raw_stderr = _canonical_output(raw_stderr, f"{context} sample stderr")
            canonical_stderr, counter, counter_failures = _strip_runtime_stats(canonical_raw_stderr)
            if counter_failures:
                raise LabError(f"{context} sample runtime stats are invalid: {counter_failures}")
            observed_counters.append(counter)
            for channel, text in (("stdout", canonical_stdout), ("stderr", canonical_stderr)):
                checksum = sample.get(f"{channel}_sha256")
                if sample.get(channel) != text:
                    raise LabError(f"{context} sample stored {channel} differs from raw bytes")
                if text != mode[f"expected_{channel}"] or checksum != mode[f"expected_{channel}_sha256"]:
                    raise LabError(f"{context} sample {channel} differs from manifest")
                if checksum != _sha256_text(text):
                    raise LabError(f"{context} sample {channel} checksum is invalid")
        if run.get("median_ns") != int(statistics.median(durations)):
            raise LabError(f"{context} median does not match raw samples")
        if result.get("peak_rss_bytes") is not None or result.get("peak_rss_reason") != RSS_UNAVAILABLE_REASON:
            raise LabError(f"{context} peak RSS must remain unavailable in schema v1")
        present_counters = [counter for counter in observed_counters if counter is not None]
        if present_counters and len(present_counters) != samples:
            raise LabError(f"{context} runtime stats are present for only some samples")
        if len(present_counters) == samples:
            expected_counters: dict[str, Any] | None = {"samples": present_counters}
            expected_counter_reason = None
        else:
            expected_counters = None
            expected_counter_reason = RUNTIME_COUNTERS_UNAVAILABLE_REASON
        if (
            result.get("runtime_counters") != expected_counters
            or result.get("runtime_counters_reason") != expected_counter_reason
        ):
            raise LabError(f"{context} runtime counter value/reason differs from raw samples")
        verification = _require_dict(result.get("verification"), f"{context}.verification")
        _exact_keys(verification, {"passed", "failures"}, f"{context}.verification")
        if verification.get("passed") is not True or verification.get("failures") != []:
            raise LabError(f"{context} is not verified")

    if actual_combinations != expected_combinations:
        missing = sorted(expected_combinations - actual_combinations)
        raise LabError(f"result combination matrix is incomplete: {missing}")
    verification = _require_dict(document["verification"], "result.verification")
    _exact_keys(verification, {"passed", "failed_results"}, "result.verification")
    if verification.get("passed") is not True or verification.get("failed_results") != []:
        raise LabError("result root verification did not pass")
    return document


def _write_document(document: Mapping[str, Any], output: str) -> None:
    encoded = json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if output == "-":
        sys.stdout.write(encoded)
        return
    destination = Path(output).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(encoded, encoding="utf-8", newline="\n")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", help="exact FREAK CLI executable (required for benchmark runs)")
    parser.add_argument("--clang", help="exact Clang executable; defaults to clean PATH lookup")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--output", default="-", help="result JSON path, or - for stdout")
    parser.add_argument("--quick", action="store_true", help="use quick manifest parameters")
    parser.add_argument("--case", action="append", help="case id; repeat to select several")
    parser.add_argument("--backend", action="append", help="c or llvm; repeat to select several")
    parser.add_argument("--profile", action="append", help="O0, O1, O2, O3, or feature-detected +03")
    parser.add_argument("--samples", type=int, help="positive odd measured sample count")
    parser.add_argument("--warmups", type=int, help="warmup count")
    parser.add_argument("--target", help="explicit target triple; omitted means exact Clang host target")
    parser.add_argument("--timeout", type=float, default=120.0, help="per-command timeout seconds")
    parser.add_argument("--validate-manifest", action="store_true", help="validate manifest and exit")
    parser.add_argument("--validate-output", help="validate an existing result JSON and exit")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.timeout <= 0:
            raise LabError("--timeout must be positive")
        if args.validate_output:
            validate_output(Path(args.validate_output), cli_override=args.cli)
            return 0
        if args.validate_manifest:
            load_manifest(Path(args.manifest).expanduser())
            return 0
        if not args.cli:
            parser.error("--cli is required unless validation-only mode is selected")
        document = run_lab(args)
        _write_document(document, args.output)
        return 0 if document["verification"]["passed"] else 1
    except LabError as error:
        print(f"v3 performance lab: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
