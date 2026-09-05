#!/usr/bin/env python3
"""Deterministic, provenance-rich benchmark harness for the shipping V3 CLI.

``--validate-output`` checks schema closure, evidence consistency, and the live
compiler/Clang/linker identities. Result JSON is intentionally not a digital
signature and cannot authenticate a report that an attacker coherently
reauthored in full. POSIX process containment is cooperative: compiler
toolchains must remain in the isolated session/process group created for them.
Detached descendants that also close inherited capture handles cannot be
identified portably.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
import platform
import re
import shlex
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import zlib
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


RESULT_SCHEMA = "freak-v3-performance-lab-v2"
MANIFEST_SCHEMA = "freak-v3-performance-manifest-v1"
COMPILE_OBSERVATION_SCHEMA = "freak-v3-compile-observation-v2"
RECORDING_SCHEMA = "freak-v3-recording-wrapper-v2"
TRUST_MODEL_SCHEMA = "freak-v3-performance-trust-model-v1"
TRUST_MODEL_SCOPE = "internal-consistency-and-live-toolchain-revalidation"
TRUST_MODEL_LIMITATION = (
    "detects malformed evidence, internal inconsistency, and live environment drift; "
    "it is not a digital signature and cannot authenticate a report maliciously reauthored in full"
)
TRUST_MODEL_HELP = (
    "Validation checks internal consistency and revalidates the live compiler, Clang, and linker. "
    "Result JSON is not digitally signed and cannot prove historical execution after malicious "
    "coherent reauthoring."
)
PROCESS_CONTAINMENT_HELP = (
    "On POSIX, process containment is cooperative: compiler toolchains must not detach from "
    "the isolated session/process group. Detached descendants that close inherited capture "
    "handles cannot be identified portably."
)
RUNTIME_STATS_PREFIX = "FREAK_RUNTIME_STATS "
RUNTIME_STATS_SCHEMA = "freak-v3-runtime-stats-v1"
RUNTIME_STATS_SOURCE = "freak-v3-runtime"
RSS_UNAVAILABLE_REASON = "portable per-child peak RSS collection is unavailable in lab schema v1"
RUNTIME_COUNTERS_UNAVAILABLE_REASON = "runtime stats sentinel not emitted by this build"
DEFAULT_MANIFEST = Path(__file__).resolve().parents[1] / "benchmarks" / "v3" / "manifest.json"
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
MAX_CONTENT_BYTES = 64 * 1024 * 1024
MAX_COMPRESSED_CONTENT_BYTES = MAX_CONTENT_BYTES + 1024 * 1024
MAX_CAPTURE_BYTES = 16 * 1024 * 1024
MAX_RECORDING_LOG_BYTES = 16 * 1024 * 1024
MAX_MANIFEST_JSON_BYTES = 4 * 1024 * 1024
MAX_RESULT_JSON_BYTES = 256 * 1024 * 1024
MAX_RECORDER_SOURCE_BYTES = 1024 * 1024
MAX_SOURCE_BYTES = 4 * 1024 * 1024

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
    "command",
    "command_sha256",
    "executable_bytes",
    "executable_sha256_before",
    "executable_sha256_after",
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
    "recording_identity_sha256",
    "recording_before_sha256",
    "recording_after_sha256",
    "probe_invocations",
    "invocations",
    "link_invocation_sha256",
    "optimization_flags",
    "lto_flags",
    "target_flags",
    "linker_flags",
    "runtime_plan",
    "runtime_attempt_plan",
    "runtime_inputs",
    "linked_runtime_inputs",
    "backend_artifact",
    "linker",
}
_ARTIFACT_KEYS = {"path", "suffix", "bytes", "sha256", "content_zlib_base64"}
_BINARY_KEYS = {"path", "bytes", "sha256", "content_zlib_base64"}
_RUNTIME_STATS_KEYS = {"schema", "source", "counters"}
_RECORDING_IDENTITY_KEYS = {
    "schema",
    "kind",
    "python_executable",
    "python_sha256",
    "python_bytes",
    "recorder_path",
    "wrapper_path",
    "recorder_content_base64",
    "recorder_sha256",
    "wrapper_content_base64",
    "wrapper_sha256",
    "combined_sha256",
}
_RAW_INVOCATION_KEYS = {"argv", "cwd", "exit_code", "inputs", "output"}
_INVOCATION_KEYS = _RAW_INVOCATION_KEYS | {"record_sha256"}
_OBSERVED_INPUT_KEYS = {"argument_index", "path", "bytes", "sha256"}
_OBSERVED_OUTPUT_KEYS = {"path", "bytes", "sha256"}
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


def _read_bounded_file(path: Path, maximum: int, context: str) -> bytes:
    try:
        with path.open("rb") as stream:
            value = stream.read(maximum + 1)
    except (OSError, MemoryError) as error:
        raise LabError(f"cannot read {context} {path}: {error}") from error
    if len(value) > maximum:
        raise LabError(f"{context} exceeds the {maximum}-byte bound: {path}")
    return value


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
        text = _read_bounded_file(path, MAX_SOURCE_BYTES, "FREAK source").decode("utf-8")
    except UnicodeError as error:
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


def _decode_bytes(
    value: Any,
    context: str,
    *,
    maximum: int = MAX_CAPTURE_BYTES,
) -> bytes:
    text = _require_string(value, context)
    maximum_encoded = 4 * ((maximum + 2) // 3)
    if len(text) > maximum_encoded:
        raise LabError(f"{context} exceeds the decoded-size bound")
    try:
        decoded = base64.b64decode(text, validate=True)
    except (ValueError, binascii.Error) as error:
        raise LabError(f"{context} is not canonical base64") from error
    if _encode_bytes(decoded) != text:
        raise LabError(f"{context} is not canonical base64")
    if len(decoded) > maximum:
        raise LabError(f"{context} exceeds the decoded-size bound")
    return decoded


def _encode_zlib_bytes(value: bytes) -> str:
    return _encode_bytes(zlib.compress(value, level=9))


def _decode_zlib_bytes(value: Any, expected_size: int, context: str) -> bytes:
    if expected_size < 1 or expected_size > MAX_CONTENT_BYTES:
        raise LabError(f"{context} uncompressed size is outside the lab bound")
    compressed = _decode_bytes(value, context, maximum=MAX_COMPRESSED_CONTENT_BYTES)
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


def _strict_json(path: Path, *, maximum: int) -> Any:
    try:
        text = _read_bounded_file(path, maximum, "JSON input").decode("utf-8")
        return json.loads(
            text,
            object_pairs_hook=_reject_duplicate_json_keys,
            parse_constant=_reject_nonfinite_json_constant,
        )
    except LabError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, RecursionError) as error:
        raise LabError(f"cannot read JSON {path}: {error}") from error


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise ValueError(f"duplicate JSON key: {name}")
        result[name] = value
    return result


def _reject_nonfinite_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


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
    root = _require_dict(_strict_json(path, maximum=MAX_MANIFEST_JSON_BYTES), "manifest")
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


def _recording_recorder_text() -> str:
    return """#!/usr/bin/env python3
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def observed_file(path, argument_index=None):
    record = {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }
    if argument_index is not None:
        record["argument_index"] = argument_index
    return record


arguments = sys.argv[1:]
cwd = Path.cwd().resolve()
output_indexes = [index for index, argument in enumerate(arguments) if argument == "-o"]
output_index = output_indexes[0] if len(output_indexes) == 1 and output_indexes[0] + 1 < len(arguments) else None
inputs = []
for index, argument in enumerate(arguments):
    if output_index is not None and index == output_index + 1:
        continue
    candidate = Path(argument)
    if not candidate.is_absolute():
        candidate = cwd / candidate
    try:
        candidate = candidate.resolve(strict=True)
    except OSError:
        continue
    if candidate.is_file():
        inputs.append(observed_file(candidate, index))

completed = subprocess.run([os.environ["FREAK_PERF_REAL_CLANG"], *arguments])
output = None
if output_index is not None:
    candidate = Path(arguments[output_index + 1])
    if not candidate.is_absolute():
        candidate = cwd / candidate
    try:
        candidate = candidate.resolve(strict=True)
    except OSError:
        candidate = None
    if candidate is not None and candidate.is_file():
        output = observed_file(candidate)

record = {
    "argv": arguments,
    "cwd": str(cwd),
    "exit_code": completed.returncode,
    "inputs": inputs,
    "output": output,
}
with Path(os.environ["FREAK_PERF_CLANG_LOG"]).open("a", encoding="utf-8") as stream:
    stream.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\\n")
raise SystemExit(completed.returncode)
"""


def _recording_wrapper_bytes(kind: str, python_executable: str, recorder_path: str, recorder_text: str) -> bytes:
    if kind == "windows-cmd":
        return f'@"{python_executable}" "{recorder_path}" %*\r\n'.encode("utf-8")
    if kind == "posix-sh":
        return (
            "#!/bin/sh\nexec "
            + shlex.quote(python_executable)
            + " "
            + shlex.quote(recorder_path)
            + ' "$@"\n'
        ).encode("utf-8")
    raise LabError(f"unknown recording wrapper kind: {kind}")


def _recording_identity_digest(identity: Mapping[str, Any]) -> str:
    material = {name: identity[name] for name in sorted(identity) if name != "combined_sha256"}
    return _json_sha256(material)


def _write_recording_clang(work_dir: Path, real_clang: Path) -> tuple[Path, Path, dict[str, Any]]:
    recorder = work_dir / "record_clang.py"
    log = work_dir / "clang-invocations.jsonl"
    recorder_text = _recording_recorder_text()
    recorder_bytes = recorder_text.encode("utf-8")
    recorder.write_bytes(recorder_bytes)
    python_executable = str(Path(sys.executable).resolve(strict=True))
    if sys.platform == "win32":
        kind = "windows-cmd"
        wrapper = work_dir / "record-clang.cmd"
    else:
        kind = "posix-sh"
        wrapper = work_dir / "record-clang"
    wrapper_bytes = _recording_wrapper_bytes(kind, python_executable, str(recorder.resolve()), recorder_text)
    wrapper.write_bytes(wrapper_bytes)
    if kind == "posix-sh":
        wrapper.chmod(0o755)
    identity = {
        "schema": RECORDING_SCHEMA,
        "kind": kind,
        "python_executable": python_executable,
        "python_sha256": _sha256_file(Path(python_executable)),
        "python_bytes": Path(python_executable).stat().st_size,
        "recorder_path": str(recorder.resolve()),
        "wrapper_path": str(wrapper.resolve()),
        "recorder_content_base64": _encode_bytes(recorder_bytes),
        "recorder_sha256": _sha256_bytes(recorder_bytes),
        "wrapper_content_base64": _encode_bytes(wrapper_bytes),
        "wrapper_sha256": _sha256_bytes(wrapper_bytes),
    }
    identity["combined_sha256"] = _recording_identity_digest(identity)
    return wrapper.resolve(), log.resolve(), identity


def _rehash_recording_files(identity: Mapping[str, Any], context: str) -> str:
    recorder = Path(str(identity["recorder_path"]))
    wrapper = Path(str(identity["wrapper_path"]))
    python_executable = Path(str(identity["python_executable"]))
    try:
        recorder_bytes = _read_bounded_file(recorder, MAX_RECORDER_SOURCE_BYTES, f"{context} recorder")
        wrapper_bytes = _read_bounded_file(wrapper, MAX_RECORDER_SOURCE_BYTES, f"{context} wrapper")
        python_sha256 = _sha256_file(python_executable)
        python_bytes = python_executable.stat().st_size
    except LabError:
        raise
    except OSError as error:
        raise LabError(f"{context} recorder source is unavailable: {error}") from error
    if (
        identity["recorder_sha256"] != _sha256_bytes(recorder_bytes)
        or identity["wrapper_sha256"] != _sha256_bytes(wrapper_bytes)
        or identity["python_sha256"] != python_sha256
        or identity["python_bytes"] != python_bytes
        or identity["recorder_content_base64"] != _encode_bytes(recorder_bytes)
        or identity["wrapper_content_base64"] != _encode_bytes(wrapper_bytes)
    ):
        raise LabError(f"{context} recorder source changed")
    return _recording_identity_digest(identity)


def _read_recording_log(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise LabError("recording Clang did not produce an invocation log")
    invocations: list[dict[str, Any]] = []
    try:
        text = _read_bounded_file(path, MAX_RECORDING_LOG_BYTES, "recording Clang invocation log").decode("utf-8")
        for index, line in enumerate(text.splitlines()):
            value = json.loads(
                line,
                object_pairs_hook=_reject_duplicate_json_keys,
                parse_constant=_reject_nonfinite_json_constant,
            )
            if not isinstance(value, dict) or set(value) != _RAW_INVOCATION_KEYS:
                raise LabError(f"recording Clang invocation {index} is malformed")
            invocations.append(value)
    except LabError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
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


_WINDOWS_API: Any | None = None


def _windows_api() -> Any:
    """Load the narrowly scoped Win32 API used for suspended process launch."""

    global _WINDOWS_API
    if _WINDOWS_API is not None:
        return _WINDOWS_API
    import ctypes
    from ctypes import wintypes

    class StartupInfo(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("lp_reserved", wintypes.LPWSTR),
            ("lp_desktop", wintypes.LPWSTR),
            ("lp_title", wintypes.LPWSTR),
            ("dw_x", wintypes.DWORD),
            ("dw_y", wintypes.DWORD),
            ("dw_x_size", wintypes.DWORD),
            ("dw_y_size", wintypes.DWORD),
            ("dw_x_count_chars", wintypes.DWORD),
            ("dw_y_count_chars", wintypes.DWORD),
            ("dw_fill_attribute", wintypes.DWORD),
            ("dw_flags", wintypes.DWORD),
            ("w_show_window", wintypes.WORD),
            ("cb_reserved2", wintypes.WORD),
            ("lp_reserved2", ctypes.POINTER(ctypes.c_ubyte)),
            ("h_std_input", wintypes.HANDLE),
            ("h_std_output", wintypes.HANDLE),
            ("h_std_error", wintypes.HANDLE),
        ]

    class StartupInfoEx(ctypes.Structure):
        _fields_ = [("startup_info", StartupInfo), ("attribute_list", ctypes.c_void_p)]

    class ProcessInformation(ctypes.Structure):
        _fields_ = [
            ("process", wintypes.HANDLE),
            ("thread", wintypes.HANDLE),
            ("process_id", wintypes.DWORD),
            ("thread_id", wintypes.DWORD),
        ]

    class IoCounters(ctypes.Structure):
        _fields_ = [
            ("read_operations", ctypes.c_ulonglong),
            ("write_operations", ctypes.c_ulonglong),
            ("other_operations", ctypes.c_ulonglong),
            ("read_bytes", ctypes.c_ulonglong),
            ("write_bytes", ctypes.c_ulonglong),
            ("other_bytes", ctypes.c_ulonglong),
        ]

    class BasicLimits(ctypes.Structure):
        _fields_ = [
            ("per_process_user_time", ctypes.c_longlong),
            ("per_job_user_time", ctypes.c_longlong),
            ("limit_flags", wintypes.DWORD),
            ("minimum_working_set", ctypes.c_size_t),
            ("maximum_working_set", ctypes.c_size_t),
            ("active_process_limit", wintypes.DWORD),
            ("affinity", ctypes.c_size_t),
            ("priority_class", wintypes.DWORD),
            ("scheduling_class", wintypes.DWORD),
        ]

    class ExtendedLimits(ctypes.Structure):
        _fields_ = [
            ("basic_limits", BasicLimits),
            ("io_counters", IoCounters),
            ("process_memory_limit", ctypes.c_size_t),
            ("job_memory_limit", ctypes.c_size_t),
            ("peak_process_memory", ctypes.c_size_t),
            ("peak_job_memory", ctypes.c_size_t),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.SetInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    kernel32.SetInformationJobObject.restype = wintypes.BOOL
    kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
    kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel32.TerminateJobObject.restype = wintypes.BOOL
    kernel32.InitializeProcThreadAttributeList.argtypes = [
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    kernel32.InitializeProcThreadAttributeList.restype = wintypes.BOOL
    kernel32.UpdateProcThreadAttribute.argtypes = [
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.c_size_t,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]
    kernel32.UpdateProcThreadAttribute.restype = wintypes.BOOL
    kernel32.DeleteProcThreadAttributeList.argtypes = [ctypes.c_void_p]
    kernel32.DeleteProcThreadAttributeList.restype = None
    kernel32.CreateProcessW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.LPWSTR,
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.BOOL,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.LPCWSTR,
        ctypes.POINTER(StartupInfo),
        ctypes.POINTER(ProcessInformation),
    ]
    kernel32.CreateProcessW.restype = wintypes.BOOL
    kernel32.ResumeThread.argtypes = [wintypes.HANDLE]
    kernel32.ResumeThread.restype = wintypes.DWORD
    kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel32.GetExitCodeProcess.restype = wintypes.BOOL
    kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel32.TerminateProcess.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    class Api:
        pass

    api = Api()
    api.ctypes = ctypes
    api.wintypes = wintypes
    api.kernel32 = kernel32
    api.StartupInfoEx = StartupInfoEx
    api.ProcessInformation = ProcessInformation
    api.ExtendedLimits = ExtendedLimits
    _WINDOWS_API = api
    return api


class _WindowsProcess:
    """Minimal Popen-compatible wrapper retaining the suspended primary thread."""

    def __init__(
        self,
        command: Sequence[str],
        process_handle: Any,
        thread_handle: Any,
        pid: int,
        stdout: Any,
        stderr: Any,
    ) -> None:
        self.args = list(command)
        self.pid = pid
        self.stdout = stdout
        self.stderr = stderr
        self.returncode: int | None = None
        self._api = _windows_api()
        self._process_handle = process_handle
        self._thread_handle = thread_handle

    @classmethod
    def create_suspended(
        cls,
        command: Sequence[str],
        cwd: Path,
        environment: Mapping[str, str],
    ) -> _WindowsProcess:
        """Create a suspended process with only its three standard handles inherited."""

        if not command:
            raise OSError("cannot launch an empty command")
        import ctypes
        import msvcrt

        api = _windows_api()
        read_fds: list[int] = []
        child_fds: list[int] = []
        opened_streams: list[Any] = []
        attribute_buffer: Any | None = None
        attribute_list: Any | None = None
        process_information = api.ProcessInformation()
        created = False
        try:
            stdin_fd = os.open(os.devnull, os.O_RDONLY | os.O_BINARY)
            child_fds.append(stdin_fd)
            stdout_read, stdout_write = os.pipe()
            read_fds.append(stdout_read)
            child_fds.append(stdout_write)
            stderr_read, stderr_write = os.pipe()
            read_fds.append(stderr_read)
            child_fds.append(stderr_write)
            for fd in child_fds:
                os.set_inheritable(fd, True)
            for fd in read_fds:
                os.set_inheritable(fd, False)
            inherited_handles = (api.wintypes.HANDLE * len(child_fds))(
                *(msvcrt.get_osfhandle(fd) for fd in child_fds)
            )
            attribute_size = ctypes.c_size_t()
            api.kernel32.InitializeProcThreadAttributeList(
                None, 1, 0, ctypes.byref(attribute_size)
            )
            attribute_buffer = ctypes.create_string_buffer(attribute_size.value)
            attribute_list = ctypes.cast(attribute_buffer, ctypes.c_void_p)
            if not api.kernel32.InitializeProcThreadAttributeList(
                attribute_list, 1, 0, ctypes.byref(attribute_size)
            ):
                raise ctypes.WinError(ctypes.get_last_error())
            # PROC_THREAD_ATTRIBUTE_HANDLE_LIST restricts inheritance even though
            # CreateProcessW must receive bInheritHandles=TRUE for stdio.
            if not api.kernel32.UpdateProcThreadAttribute(
                attribute_list,
                0,
                0x00020002,
                ctypes.cast(inherited_handles, ctypes.c_void_p),
                ctypes.sizeof(inherited_handles),
                None,
                None,
            ):
                raise ctypes.WinError(ctypes.get_last_error())
            startup = api.StartupInfoEx()
            startup.startup_info.cb = ctypes.sizeof(startup)
            startup.startup_info.dw_flags = 0x00000100  # STARTF_USESTDHANDLES
            startup.startup_info.h_std_input = inherited_handles[0]
            startup.startup_info.h_std_output = inherited_handles[1]
            startup.startup_info.h_std_error = inherited_handles[2]
            startup.attribute_list = attribute_list
            command_line = ctypes.create_unicode_buffer(
                subprocess.list2cmdline([os.fsdecode(argument) for argument in command])
            )
            entries = [f"{name}={value}" for name, value in environment.items()]
            if any("\0" in entry for entry in entries):
                raise OSError("Windows process environment contains NUL")
            entries.sort(key=str.upper)
            environment_block = ctypes.create_unicode_buffer("\0".join(entries) + "\0\0")
            creation_flags = (
                0x00000004  # CREATE_SUSPENDED
                | 0x00000200  # CREATE_NEW_PROCESS_GROUP
                | 0x00000400  # CREATE_UNICODE_ENVIRONMENT
                | 0x00080000  # EXTENDED_STARTUPINFO_PRESENT
            )
            if not api.kernel32.CreateProcessW(
                os.fsdecode(command[0]),
                command_line,
                None,
                None,
                True,
                creation_flags,
                ctypes.cast(environment_block, ctypes.c_void_p),
                str(cwd),
                ctypes.byref(startup.startup_info),
                ctypes.byref(process_information),
            ):
                raise ctypes.WinError(ctypes.get_last_error())
            created = True
            for fd in child_fds:
                os.close(fd)
            child_fds.clear()
            stdout = os.fdopen(stdout_read, "rb", buffering=0)
            opened_streams.append(stdout)
            read_fds.remove(stdout_read)
            stderr = os.fdopen(stderr_read, "rb", buffering=0)
            opened_streams.append(stderr)
            read_fds.remove(stderr_read)
            process = cls(
                command,
                process_information.process,
                process_information.thread,
                int(process_information.process_id),
                stdout,
                stderr,
            )
            opened_streams.clear()
            return process
        except BaseException as error:
            for stream in opened_streams:
                try:
                    stream.close()
                except OSError:
                    pass
            cleanup_errors: list[str] = []
            if created:
                if not api.kernel32.TerminateProcess(process_information.process, 1):
                    cleanup_errors.append(
                        f"cannot terminate suspended Windows process: "
                        f"{api.ctypes.WinError(api.ctypes.get_last_error())}"
                    )
                wait_result = api.kernel32.WaitForSingleObject(process_information.process, 2000)
                if wait_result != 0:
                    cleanup_errors.append(
                        f"cannot verify suspended Windows process termination: wait result {wait_result}"
                    )
                if not api.kernel32.CloseHandle(process_information.thread):
                    cleanup_errors.append(
                        f"cannot close suspended Windows thread handle: "
                        f"{api.ctypes.WinError(api.ctypes.get_last_error())}"
                    )
                if not api.kernel32.CloseHandle(process_information.process):
                    cleanup_errors.append(
                        f"cannot close suspended Windows process handle: "
                        f"{api.ctypes.WinError(api.ctypes.get_last_error())}"
                    )
            if cleanup_errors:
                raise OSError(f"{error}; cleanup failed: {'; '.join(cleanup_errors)}") from error
            raise
        finally:
            if attribute_list is not None:
                api.kernel32.DeleteProcThreadAttributeList(attribute_list)
            for fd in child_fds + read_fds:
                try:
                    os.close(fd)
                except OSError:
                    pass

    def resume(self) -> None:
        if not self._thread_handle:
            raise OSError("Windows primary thread handle is unavailable")
        previous_count = self._api.kernel32.ResumeThread(self._thread_handle)
        if previous_count == 0xFFFFFFFF:
            raise self._api.ctypes.WinError(self._api.ctypes.get_last_error())
        if previous_count != 1:
            raise OSError(f"unexpected Windows primary thread suspend count {previous_count}")
        if not self._api.kernel32.CloseHandle(self._thread_handle):
            raise self._api.ctypes.WinError(self._api.ctypes.get_last_error())
        self._thread_handle = None

    def poll(self) -> int | None:
        if self.returncode is not None:
            return self.returncode
        result = self._api.kernel32.WaitForSingleObject(self._process_handle, 0)
        if result == 0x00000102:  # WAIT_TIMEOUT
            return None
        if result != 0:  # WAIT_OBJECT_0
            raise self._api.ctypes.WinError(self._api.ctypes.get_last_error())
        code = self._api.wintypes.DWORD()
        if not self._api.kernel32.GetExitCodeProcess(self._process_handle, self._api.ctypes.byref(code)):
            raise self._api.ctypes.WinError(self._api.ctypes.get_last_error())
        self.returncode = int(code.value)
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        milliseconds = 0xFFFFFFFF if timeout is None else min(0xFFFFFFFE, max(0, int(timeout * 1000 + 0.999)))
        result = self._api.kernel32.WaitForSingleObject(self._process_handle, milliseconds)
        if result == 0x00000102:
            raise subprocess.TimeoutExpired(self.args, timeout)
        if result != 0:
            raise self._api.ctypes.WinError(self._api.ctypes.get_last_error())
        returncode = self.poll()
        assert returncode is not None
        return returncode

    def kill(self) -> None:
        if self.poll() is None and not self._api.kernel32.TerminateProcess(self._process_handle, 1):
            raise self._api.ctypes.WinError(self._api.ctypes.get_last_error())

    def close(self) -> None:
        errors: list[OSError] = []
        if self._thread_handle:
            if not self._api.kernel32.CloseHandle(self._thread_handle):
                errors.append(self._api.ctypes.WinError(self._api.ctypes.get_last_error()))
            else:
                self._thread_handle = None
        if self._process_handle:
            if not self._api.kernel32.CloseHandle(self._process_handle):
                errors.append(self._api.ctypes.WinError(self._api.ctypes.get_last_error()))
            else:
                self._process_handle = None
        if errors:
            raise errors[0]


class _WindowsJob:
    """Own one Windows process tree and kill it when the job is closed."""

    def __init__(self) -> None:
        api = _windows_api()
        handle = api.kernel32.CreateJobObjectW(None, None)
        if not handle:
            raise api.ctypes.WinError(api.ctypes.get_last_error())
        limits = api.ExtendedLimits()
        limits.basic_limits.limit_flags = 0x00002000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not api.kernel32.SetInformationJobObject(
            handle, 9, api.ctypes.byref(limits), api.ctypes.sizeof(limits)
        ):
            error = api.ctypes.WinError(api.ctypes.get_last_error())
            api.kernel32.CloseHandle(handle)
            raise error
        self._api = api
        self._handle = handle
        self._assigned = False

    def assign(self, process: _WindowsProcess) -> None:
        if not self._api.kernel32.AssignProcessToJobObject(self._handle, process._process_handle):
            raise self._api.ctypes.WinError(self._api.ctypes.get_last_error())
        self._assigned = True

    def terminate(self) -> None:
        if self._handle and not self._api.kernel32.TerminateJobObject(self._handle, 1):
            raise self._api.ctypes.WinError(self._api.ctypes.get_last_error())

    def close(self) -> None:
        if self._handle:
            if not self._api.kernel32.CloseHandle(self._handle):
                raise self._api.ctypes.WinError(self._api.ctypes.get_last_error())
            self._handle = None


def _direct_process_exited_without_reaping(process: Any) -> bool:
    """Observe direct-child exit while preserving the POSIX group leader PID."""

    if sys.platform == "win32":
        return process.poll() is not None
    if not all(hasattr(os, name) for name in ("waitid", "P_PID", "WEXITED", "WNOHANG", "WNOWAIT")):
        raise LabError("POSIX platform lacks waitid(WNOWAIT) required for safe process-group containment")
    try:
        status = os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
    except ChildProcessError as error:
        raise LabError("direct process was reaped before process-group cleanup") from error
    return status is not None and status.si_pid != 0


def _darwin_exited_group_is_singleton(process: Any) -> bool:
    """Prove that a pinned, exited leader is the group's only remaining PID.

    Darwin killpg returns EPERM for a zombie-only group. Never infer this from
    direct-child exit alone: a live descendant may instead be unkillable.
    libproc includes zombies and returns a PID count. Two slots distinguish a
    complete singleton from a full/truncated result, without unbounded storage.
    Any uncertainty retains the original containment error.
    """
    if sys.platform != "darwin":
        return False
    try:
        if not _direct_process_exited_without_reaping(process):
            return False
        import ctypes

        library = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
        query = library.proc_listpgrppids
        query.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
        query.restype = ctypes.c_int
        members = (ctypes.c_int * 2)()
        count = query(process.pid, members, ctypes.sizeof(members))
        return count == 1 and members[0] == process.pid
    except (OSError, AttributeError, LabError):
        return False


def _terminate_process_tree(process: Any, windows_job: _WindowsJob | None) -> list[str]:
    """Terminate the launched Windows job or cooperative POSIX process group."""

    errors: list[str] = []
    job_termination_requested = False
    if sys.platform == "win32":
        if windows_job is not None and windows_job._assigned:
            try:
                windows_job.terminate()
                job_termination_requested = True
            except OSError as error:
                errors.append(f"cannot terminate Windows process job: {error}")
    else:
        # The leader is deliberately unreaped until after this signal so its
        # numeric PID cannot be recycled as an unrelated process-group ID.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except PermissionError as error:
            if not _darwin_exited_group_is_singleton(process):
                errors.append(f"cannot terminate POSIX process group {process.pid}: {error}")
        except OSError as error:
            errors.append(f"cannot terminate POSIX process group {process.pid}: {error}")
    if job_termination_requested:
        try:
            process.wait(timeout=2.0)
            return errors
        except (OSError, subprocess.TimeoutExpired) as error:
            errors.append(f"cannot await Windows process job termination for {process.pid}: {error}")
    if process.poll() is None:
        try:
            process.kill()
        except OSError as error:
            errors.append(f"cannot terminate direct process {process.pid}: {error}")
    try:
        process.wait(timeout=2.0)
    except (OSError, subprocess.TimeoutExpired) as error:
        errors.append(f"cannot reap direct process {process.pid}: {error}")
    return errors


def _join_capture_threads(
    readers: Sequence[threading.Thread],
    streams: Sequence[Any],
    shutdown: threading.Event,
) -> list[str]:
    """Bound natural pipe drain, then close every stream and bound shutdown."""

    errors: list[str] = []
    drain_deadline = time.monotonic() + 2.0
    for index, reader in enumerate(readers):
        if reader.ident is None:
            continue
        try:
            reader.join(timeout=max(0.0, drain_deadline - time.monotonic()))
        except BaseException as error:
            errors.append(f"cannot join capture reader {index}: {error}")
    readers_without_eof = [
        index for index, reader in enumerate(readers) if reader.ident is not None and reader.is_alive()
    ]
    shutdown.set()
    for index, stream in enumerate(streams):
        try:
            stream.close()
        except BaseException as error:
            errors.append(f"cannot close capture pipe {index}: {error}")
    deadline = time.monotonic() + 2.0
    for index, reader in enumerate(readers):
        if reader.ident is None or not reader.is_alive():
            continue
        try:
            reader.join(timeout=max(0.0, deadline - time.monotonic()))
        except BaseException as error:
            errors.append(f"cannot finish joining capture reader {index}: {error}")
    for index in readers_without_eof:
        detail = f"capture reader {index} did not reach EOF after process containment cleanup"
        if sys.platform != "win32":
            detail += "; POSIX toolchain descendants must not detach from the launched session/process group"
        errors.append(detail)
    errors.extend(
        f"capture reader {index} did not stop after its capture pipe was closed"
        for index, reader in enumerate(readers)
        if reader.is_alive()
    )
    return errors


def _run_bytes(
    command: Sequence[str],
    *,
    cwd: Path,
    environment: Mapping[str, str],
    timeout: float,
) -> subprocess.CompletedProcess[bytes]:
    process: Any | None = None
    windows_job: _WindowsJob | None = None
    readers: list[threading.Thread] = []
    streams: list[Any] = []
    stdout_buffer = bytearray()
    stderr_buffer = bytearray()
    overflow = threading.Event()
    capture_shutdown = threading.Event()
    reader_errors: list[BaseException] = []
    primary_error: BaseException | None = None
    cleanup_errors: list[str] = []

    def capture(stream: Any, destination: bytearray) -> None:
        try:
            read_block = getattr(stream, "read1", stream.read)
            while True:
                block = read_block(64 * 1024)
                if not block:
                    return
                remaining = MAX_CAPTURE_BYTES - len(destination)
                if remaining > 0:
                    destination.extend(block[:remaining])
                if len(block) > remaining:
                    overflow.set()
        except BaseException as error:  # surfaced deterministically on the launcher thread
            if not capture_shutdown.is_set():
                reader_errors.append(error)

    try:
        if sys.platform == "win32":
            windows_job = _WindowsJob()
            process = _WindowsProcess.create_suspended(command, cwd, environment)
            streams = [process.stdout, process.stderr]
            try:
                windows_job.assign(process)
                process.resume()
            except OSError as error:
                raise LabError(
                    f"cannot atomically enroll and resume Windows process {process.pid}: {error}"
                ) from error
        else:
            process = subprocess.Popen(
                list(command),
                cwd=str(cwd),
                env=dict(environment),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
                start_new_session=True,
            )
            assert process.stdout is not None and process.stderr is not None
            streams = [process.stdout, process.stderr]
        reader_candidates = [
            threading.Thread(
                target=capture,
                args=(streams[0], stdout_buffer),
                daemon=True,
                name="freak-v3-capture-stdout",
            ),
            threading.Thread(
                target=capture,
                args=(streams[1], stderr_buffer),
                daemon=True,
                name="freak-v3-capture-stderr",
            ),
        ]
        for index, reader in enumerate(reader_candidates):
            try:
                reader.start()
            except (OSError, RuntimeError) as error:
                raise LabError(f"cannot start capture reader {index}: {error}") from error
            readers.append(reader)
        deadline = time.monotonic() + timeout
        while not _direct_process_exited_without_reaping(process):
            if overflow.is_set():
                primary_error = LabError(
                    f"command output exceeds the {MAX_CAPTURE_BYTES}-byte per-channel bound: {command!r}"
                )
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                primary_error = subprocess.TimeoutExpired(list(command), timeout)
                break
            time.sleep(min(0.05, remaining))
    except BaseException as error:
        primary_error = error
    finally:
        if process is not None:
            try:
                cleanup_errors.extend(_terminate_process_tree(process, windows_job))
            except BaseException as error:
                cleanup_errors.append(f"unexpected process containment cleanup failure: {error}")
        try:
            cleanup_errors.extend(_join_capture_threads(readers, streams, capture_shutdown))
        except BaseException as error:
            cleanup_errors.append(f"unexpected capture cleanup failure: {error}")
            capture_shutdown.set()
            for index, stream in enumerate(streams):
                try:
                    stream.close()
                except BaseException as close_error:
                    cleanup_errors.append(f"cannot close capture pipe {index}: {close_error}")
        if windows_job is not None:
            try:
                windows_job.close()
            except BaseException as error:
                cleanup_errors.append(f"cannot close Windows process job: {error}")
        if isinstance(process, _WindowsProcess):
            try:
                process.close()
            except BaseException as error:
                cleanup_errors.append(f"cannot close Windows process handles: {error}")

    if primary_error is not None:
        if cleanup_errors:
            raise LabError(f"{primary_error}; cleanup failed: {'; '.join(cleanup_errors)}") from primary_error
        if isinstance(primary_error, LabError):
            raise primary_error
        if isinstance(primary_error, (OSError, subprocess.TimeoutExpired)):
            raise LabError(f"command failed to execute: {command!r}: {primary_error}") from primary_error
        raise primary_error
    if cleanup_errors:
        raise LabError(f"command process containment cleanup failed: {'; '.join(cleanup_errors)}")
    if overflow.is_set():
        raise LabError(f"command output exceeds the {MAX_CAPTURE_BYTES}-byte per-channel bound: {command!r}")
    if reader_errors:
        raise LabError(f"command output capture failed: {command!r}: {reader_errors[0]}")
    assert process is not None and process.returncode is not None
    return subprocess.CompletedProcess(
        list(command),
        process.returncode,
        bytes(stdout_buffer),
        bytes(stderr_buffer),
    )


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


def _normalized_recorded_path(value: str, cwd: str) -> str:
    path = Path(value)
    if not path.is_absolute():
        path = Path(cwd) / path
    return str(path.resolve(strict=False))


def _path_identity(value: str) -> str:
    return os.path.normcase(os.path.normpath(value))


def _validate_observed_file_record(
    value: Any,
    context: str,
    *,
    input_record: bool,
) -> dict[str, Any]:
    record = _require_dict(value, context)
    _exact_keys(record, _OBSERVED_INPUT_KEYS if input_record else _OBSERVED_OUTPUT_KEYS, context)
    path = _require_string(record.get("path"), f"{context}.path", nonempty=True)
    if not Path(path).is_absolute():
        raise LabError(f"{context}.path must be absolute")
    _require_int(record.get("bytes"), f"{context}.bytes", minimum=0)
    sha256 = _require_string(record.get("sha256"), f"{context}.sha256")
    if not re.fullmatch(r"[0-9a-f]{64}", sha256):
        raise LabError(f"{context}.sha256 is invalid")
    if input_record:
        _require_int(record.get("argument_index"), f"{context}.argument_index", minimum=0)
    return record


def _validate_invocation_payload(value: Any, context: str, *, stored: bool) -> dict[str, Any]:
    record = _require_dict(value, context)
    _exact_keys(record, _INVOCATION_KEYS if stored else _RAW_INVOCATION_KEYS, context)
    arguments = _require_string_list(record.get("argv"), f"{context}.argv")
    if stored:
        raw_record = {name: record[name] for name in _RAW_INVOCATION_KEYS}
        if record.get("record_sha256") != _json_sha256(raw_record):
            raise LabError(f"{context} full-record checksum is invalid")
    cwd = _require_string(record.get("cwd"), f"{context}.cwd", nonempty=True)
    if not Path(cwd).is_absolute():
        raise LabError(f"{context}.cwd must be absolute")
    _require_int(record.get("exit_code"), f"{context}.exit_code")
    raw_inputs = _require_list(record.get("inputs"), f"{context}.inputs")
    inputs: list[dict[str, Any]] = []
    seen_indexes: set[int] = set()
    seen_paths: set[str] = set()
    for index, raw_input in enumerate(raw_inputs):
        input_context = f"{context}.inputs[{index}]"
        observed = _validate_observed_file_record(raw_input, input_context, input_record=True)
        argument_index = observed["argument_index"]
        if argument_index >= len(arguments):
            raise LabError(f"{input_context}.argument_index is outside argv")
        expected_path = _normalized_recorded_path(arguments[argument_index], cwd)
        if _path_identity(expected_path) != _path_identity(observed["path"]):
            raise LabError(f"{input_context}.path differs from argv")
        path_key = _path_identity(observed["path"])
        if argument_index in seen_indexes or path_key in seen_paths:
            raise LabError(f"{context}.inputs contains a duplicate")
        seen_indexes.add(argument_index)
        seen_paths.add(path_key)
        inputs.append(observed)
    if [item["argument_index"] for item in inputs] != sorted(item["argument_index"] for item in inputs):
        raise LabError(f"{context}.inputs are not ordered by argv position")

    output_indexes = [index for index, argument in enumerate(arguments) if argument == "-o"]
    output = record.get("output")
    if output is None:
        if record.get("exit_code") == 0 and len(output_indexes) == 1:
            raise LabError(f"{context} successful output invocation lacks output evidence")
    else:
        observed_output = _validate_observed_file_record(output, f"{context}.output", input_record=False)
        if len(output_indexes) != 1 or output_indexes[0] + 1 >= len(arguments):
            raise LabError(f"{context} output evidence lacks one canonical -o argument")
        expected_path = _normalized_recorded_path(arguments[output_indexes[0] + 1], cwd)
        if _path_identity(expected_path) != _path_identity(observed_output["path"]):
            raise LabError(f"{context}.output.path differs from -o")
    return record


def _invocation_record(value: Mapping[str, Any], context: str) -> dict[str, Any]:
    raw = _validate_invocation_payload(value, context, stored=False)
    return {**raw, "record_sha256": _json_sha256(raw)}


def _same_observed_file(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return (
        _path_identity(str(left["path"])) == _path_identity(str(right["path"]))
        and left["bytes"] == right["bytes"]
        and left["sha256"] == right["sha256"]
    )


def _pipeline_reaches(
    invocations: Sequence[Mapping[str, Any]],
    source: Mapping[str, Any],
    destination: Mapping[str, Any],
) -> bool:
    reached: list[Mapping[str, Any]] = [source]
    pending = [invocation for invocation in invocations if invocation["exit_code"] == 0 and invocation["output"]]
    changed = True
    while changed:
        changed = False
        remaining: list[Mapping[str, Any]] = []
        for invocation in pending:
            if any(
                _same_observed_file(input_record, known)
                for input_record in invocation["inputs"]
                for known in reached
            ):
                output = invocation["output"]
                if not any(_same_observed_file(output, known) for known in reached):
                    reached.append(output)
                    changed = True
            else:
                remaining.append(invocation)
        pending = remaining
    return any(_same_observed_file(destination, known) for known in reached)


def _runtime_input_records(invocations: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_path: dict[str, dict[str, Any]] = {}
    for invocation in invocations:
        for observed in invocation["inputs"]:
            name = Path(observed["path"]).name
            if name not in _RUNTIME_INPUT_NAMES:
                continue
            item = {
                "name": name,
                "path": observed["path"],
                "bytes": observed["bytes"],
                "sha256": observed["sha256"],
            }
            key = _path_identity(observed["path"])
            if key in by_path and by_path[key] != item:
                raise LabError(f"recorded runtime input changed during build: {observed['path']}")
            by_path[key] = item
    return sorted(by_path.values(), key=lambda item: (item["name"], item["path"]))


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


def _resolve_observed_linker(value: str, environment: Mapping[str, str]) -> Path:
    """Use the same alias resolution for recorded and revalidated linkers."""
    linker = Path(value)
    if not linker.is_absolute():
        found = shutil.which(value, path=environment.get("PATH"))
        if not found:
            raise LabError(f"observed linker is not resolvable: {value}")
        linker = Path(found)
    elif sys.platform == "win32" and not linker.is_file() and not str(linker).lower().endswith(".exe"):
        executable = Path(str(linker) + ".exe")
        if executable.is_file():
            linker = executable
    return _resolve_exact_executable(str(linker), "observed linker")


def _linker_identity_from_trace(
    clang: Path,
    link_arguments: Sequence[str],
    link_invocation_sha256: str,
    cwd: Path,
    environment: Mapping[str, str],
    timeout: float,
) -> dict[str, Any]:
    output_indexes = [index for index, argument in enumerate(link_arguments) if argument == "-o"]
    if len(output_indexes) != 1 or output_indexes[0] + 1 >= len(link_arguments):
        raise LabError("recorded link invocation lacks one canonical -o argument")
    trace_arguments = list(link_arguments)
    original_output = Path(trace_arguments[output_indexes[0] + 1])
    suffix = original_output.suffix or (".exe" if sys.platform == "win32" else ".out")
    trace_arguments[output_indexes[0] + 1] = f"freak-link-trace-output{suffix}"
    trace = _run_bytes([str(clang), "-###", *trace_arguments], cwd=cwd, environment=environment, timeout=timeout)
    trace_bytes = trace.stdout + trace.stderr
    trace_text = _decode(trace_bytes, "Clang linker trace")
    candidates: list[str] = []
    for line in trace_text.splitlines():
        match = re.match(r'^\s*"([^"]+)"', line)
        first = match.group(1) if match else (line.strip().split(" ", 1)[0] if line.strip() else "")
        if first and _is_linker_name(first):
            candidates.append(first)
    if not candidates:
        raise LabError(
            f"Clang did not expose a linker for recorded invocation (exit={trace.returncode})\n{trace_text}"
        )
    linker_value = candidates[-1]
    linker = _resolve_observed_linker(linker_value, environment)
    version = _run_bytes([str(linker), "--version"], cwd=cwd, environment=environment, timeout=timeout)
    return {
        "link_invocation_sha256": link_invocation_sha256,
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


def _expected_linker_flags(profile: str) -> list[str]:
    if profile != "+03":
        return []
    return ["-fuse-ld=ld"] if sys.platform == "darwin" else ["-fuse-ld=lld"]


def _compile_observation(
    *,
    recording_log: Path,
    recording_identity_sha256: str,
    recording_before_sha256: str,
    recording_after_sha256: str,
    source_snapshot_sha256: str,
    real_clang: Path,
    lane_dir: Path,
    environment: Mapping[str, str],
    backend: str,
    profile: str,
    target_argument: str | None,
    backend_artifact: Path,
    binary: Path,
    timeout: float,
) -> dict[str, Any]:
    raw_invocations = _read_recording_log(recording_log)
    invocations = [
        _invocation_record(value, f"recorded Clang invocation {index}")
        for index, value in enumerate(raw_invocations)
    ]
    build_invocations = [invocation for invocation in invocations if "-o" in invocation["argv"]]
    probe_invocations = [invocation for invocation in invocations if "-o" not in invocation["argv"]]
    if not build_invocations:
        raise LabError("recording Clang observed no build invocation")
    successful_links = [
        invocation
        for invocation in build_invocations
        if invocation["exit_code"] == 0 and "-c" not in invocation["argv"]
    ]
    if len(successful_links) != 1:
        raise LabError(f"recording Clang observed {len(successful_links)} successful link invocations")
    successful_link = successful_links[0]
    flattened = [argument for invocation in build_invocations for argument in invocation["argv"]]
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
    link_arguments = successful_link["argv"]
    actual_linker_flags = sorted(set(argument for argument in link_arguments if argument.startswith("-fuse-ld=")))
    if actual_linker_flags != _expected_linker_flags(profile):
        raise LabError(f"successful link flags {actual_linker_flags} do not implement requested profile {profile}")
    if profile == "+03" and "-flto=thin" not in link_arguments:
        raise LabError("+03 successful link invocation omits ThinLTO")

    artifact_path = backend_artifact.resolve(strict=True)
    artifact_bytes = _read_bounded_file(backend_artifact, MAX_CONTENT_BYTES, "backend artifact")
    artifact_observation = {
        "path": str(artifact_path),
        "bytes": len(artifact_bytes),
        "sha256": _sha256_bytes(artifact_bytes),
    }
    artifact_consumers = [
        invocation
        for invocation in build_invocations
        if invocation["exit_code"] == 0
        and any(_same_observed_file(observed, artifact_observation) for observed in invocation["inputs"])
    ]
    if not artifact_consumers:
        raise LabError("no successful recorded Clang invocation consumed the generated backend artifact")
    for invocation in artifact_consumers:
        invocation_opt = sorted(set(argument for argument in invocation["argv"] if re.fullmatch(r"-O[^/\\]*", argument)))
        if invocation_opt != [profile_spec["opt"]]:
            raise LabError("backend artifact consumer does not implement the requested optimization")
        if profile == "+03" and "-flto=thin" not in invocation["argv"]:
            raise LabError("+03 backend artifact consumer omits ThinLTO")

    binary_path = binary.resolve(strict=True)
    binary_observation = {
        "path": str(binary_path),
        "bytes": binary.stat().st_size,
        "sha256": _sha256_file(binary),
    }
    if successful_link["output"] is None or not _same_observed_file(successful_link["output"], binary_observation):
        raise LabError("successful recorded link output differs from the executable binary")
    if not _pipeline_reaches(build_invocations, artifact_observation, binary_observation):
        raise LabError("generated backend artifact is not connected to the executable binary")

    runtime_inputs = _runtime_input_records(build_invocations)
    linked_runtime_inputs = _runtime_input_records([successful_link])
    for item in runtime_inputs:
        runtime_path = _resolve_exact_executable(item["path"], "recorded runtime input")
        if item["bytes"] != runtime_path.stat().st_size or item["sha256"] != _sha256_file(runtime_path):
            raise LabError(f"recorded runtime input changed during build: {runtime_path}")
    runtime_names = {value["name"] for value in linked_runtime_inputs}
    attempted_runtime_names = {value["name"] for value in runtime_inputs}
    plan = _runtime_plan(runtime_names)
    attempt_plan = _runtime_plan(attempted_runtime_names)
    if plan == "missing" or attempt_plan == "missing":
        raise LabError("recorded build has no runtime source or object inputs")
    if profile == "+03" and (plan != "source" or attempt_plan != "source"):
        raise LabError("+03 must link runtime sources in the LTO unit")
    required_runtime = {"freak_runtime.c"} if plan == "source" else {"freak_runtime.obj", "freak_runtime.o"}
    if not (runtime_names & required_runtime):
        raise LabError("recorded build omits the base runtime")
    llvm_names = {"freak_llvm_runtime.c", "freak_llvm_runtime.o", "freak_llvm_runtime.obj"}
    if backend == "llvm":
        if not (runtime_names & llvm_names):
            raise LabError("recorded LLVM build omits the LLVM runtime")
    elif runtime_names & llvm_names:
        raise LabError("recorded C build unexpectedly links the LLVM runtime")

    linker = _linker_identity_from_trace(
        real_clang,
        link_arguments,
        successful_link["record_sha256"],
        lane_dir,
        environment,
        timeout,
    )
    return {
        "schema": COMPILE_OBSERVATION_SCHEMA,
        "source_snapshot_sha256": source_snapshot_sha256,
        "recording_identity_sha256": recording_identity_sha256,
        "recording_before_sha256": recording_before_sha256,
        "recording_after_sha256": recording_after_sha256,
        "probe_invocations": probe_invocations,
        "invocations": build_invocations,
        "link_invocation_sha256": successful_link["record_sha256"],
        "optimization_flags": optimization_flags,
        "lto_flags": lto_flags,
        "target_flags": target_flags,
        "linker_flags": linker_flags,
        "runtime_plan": plan,
        "runtime_attempt_plan": attempt_plan,
        "runtime_inputs": runtime_inputs,
        "linked_runtime_inputs": linked_runtime_inputs,
        "backend_artifact": {
            "path": str(artifact_path),
            "suffix": backend_artifact.suffix,
            "bytes": len(artifact_bytes),
            "sha256": _sha256_bytes(artifact_bytes),
            "content_zlib_base64": _encode_zlib_bytes(artifact_bytes),
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
    recording_identity: Mapping[str, Any],
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
    recording_before_sha256 = _rehash_recording_files(recording_identity, "before build")
    recording_log.unlink(missing_ok=True)
    compile_start = time.perf_counter_ns()
    compiled = _run_bytes(compile_command, cwd=lane_dir, environment=environment, timeout=timeout)
    compile_ns = time.perf_counter_ns() - compile_start
    recording_after_sha256 = _rehash_recording_files(recording_identity, "after build")
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
    binary = _binary_path(copied_source)
    compile_observation = _compile_observation(
        recording_log=recording_log,
        recording_identity_sha256=recording_identity["combined_sha256"],
        recording_before_sha256=recording_before_sha256,
        recording_after_sha256=recording_after_sha256,
        source_snapshot_sha256=case["source_sha256"],
        real_clang=real_clang,
        lane_dir=lane_dir,
        environment=environment,
        backend=backend,
        profile=profile,
        target_argument=target_argument,
        backend_artifact=backend_artifact,
        binary=binary,
        timeout=timeout,
    )

    run_command = [str(binary), *mode["arguments"]]
    linked_output = next(
        invocation["output"]
        for invocation in compile_observation["invocations"]
        if invocation["record_sha256"] == compile_observation["link_invocation_sha256"]
    )
    if linked_output is None:
        raise LabError(f"successful link lacks output evidence for {case['id']}/{backend}/{profile}")

    def verify_executable(stage: str) -> tuple[int, str]:
        try:
            size = binary.stat().st_size
        except OSError as error:
            raise LabError(f"executable is unavailable {stage}: {error}") from error
        if size > MAX_CONTENT_BYTES:
            raise LabError(f"executable exceeds the {MAX_CONTENT_BYTES}-byte lab bound {stage}")
        digest = _sha256_file(binary)
        if size != linked_output["bytes"] or digest != linked_output["sha256"]:
            raise LabError(f"executable differs from the recorded link output {stage}")
        return size, digest

    warmup_records: list[dict[str, Any]] = []
    for warmup_index in range(warmups):
        executable_bytes, executable_before = verify_executable(f"before warmup {warmup_index}")
        warmup_start = time.perf_counter_ns()
        warmed = _run_bytes(run_command, cwd=lane_dir, environment=environment, timeout=timeout)
        warmup_ns = time.perf_counter_ns() - warmup_start
        _, executable_after = verify_executable(f"after warmup {warmup_index}")
        warmup_stdout, warmup_stderr, _, warmup_failures = _verify_completed(
            warmed,
            mode,
            f"warmup {warmup_index} for {case['id']}/{backend}/{profile}",
        )
        warmup_records.append(
            {
                "index": warmup_index,
                "duration_ns": warmup_ns,
                "exit_code": warmed.returncode,
                "stdout": warmup_stdout,
                "stdout_sha256": _sha256_text(warmup_stdout),
                "stdout_raw_sha256": _sha256_bytes(warmed.stdout),
                "stdout_raw_base64": _encode_bytes(warmed.stdout),
                "stderr": warmup_stderr,
                "stderr_sha256": _sha256_text(warmup_stderr),
                "stderr_raw_sha256": _sha256_bytes(warmed.stderr),
                "stderr_raw_base64": _encode_bytes(warmed.stderr),
                "command": run_command,
                "command_sha256": _json_sha256(run_command),
                "executable_bytes": executable_bytes,
                "executable_sha256_before": executable_before,
                "executable_sha256_after": executable_after,
            }
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
        executable_bytes, executable_before = verify_executable(f"before sample {sample_index}")
        run_start = time.perf_counter_ns()
        completed = _run_bytes(run_command, cwd=lane_dir, environment=environment, timeout=timeout)
        duration_ns = time.perf_counter_ns() - run_start
        _, executable_after = verify_executable(f"after sample {sample_index}")
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
                "command": run_command,
                "command_sha256": _json_sha256(run_command),
                "executable_bytes": executable_bytes,
                "executable_sha256_before": executable_before,
                "executable_sha256_after": executable_after,
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

    verify_executable("after all samples")
    binary_bytes = _read_bounded_file(binary, MAX_CONTENT_BYTES, "binary")
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
            "path": str(binary.resolve(strict=True)),
            "bytes": len(binary_bytes),
            "sha256": _sha256_bytes(binary_bytes),
            "content_zlib_base64": _encode_zlib_bytes(binary_bytes),
        },
        "run": {
            "warmups": warmup_records,
            "samples": run_samples,
            "median_ns": int(statistics.median(durations)),
        },
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
        wrapper, recording_log, recording_identity = _write_recording_clang(work_dir, clang)
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
                            recording_identity=recording_identity,
                        )
                    )

    document = {
        "schema": RESULT_SCHEMA,
        "trust_model": {
            "schema": TRUST_MODEL_SCHEMA,
            "scope": TRUST_MODEL_SCOPE,
            "limitation": TRUST_MODEL_LIMITATION,
        },
        "lab": {
            "path": str(Path(__file__).resolve()),
            "sha256": _sha256_file(Path(__file__).resolve()),
        },
        "manifest": {
            "path": str(manifest_path),
            "schema": manifest["schema"],
            "sha256": _sha256_file(manifest_path),
        },
        "recording": recording_identity,
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


def _validate_invocation_record(value: Any, context: str) -> dict[str, Any]:
    return _validate_invocation_payload(value, context, stored=True)


def _validate_recording_identity(value: Any, context: str) -> dict[str, Any]:
    identity = _require_dict(value, context)
    _exact_keys(identity, _RECORDING_IDENTITY_KEYS, context)
    if identity.get("schema") != RECORDING_SCHEMA:
        raise LabError(f"{context}.schema is unsupported")
    expected_kind = "windows-cmd" if sys.platform == "win32" else "posix-sh"
    if identity.get("kind") != expected_kind:
        raise LabError(f"{context}.kind differs from the validation platform")
    python_executable = _require_string(
        identity.get("python_executable"),
        f"{context}.python_executable",
        nonempty=True,
    )
    if python_executable != str(Path(sys.executable).resolve(strict=True)):
        raise LabError(f"{context}.python_executable differs from the validator")
    python_path = Path(python_executable)
    if (
        identity.get("python_sha256") != _sha256_file(python_path)
        or identity.get("python_bytes") != python_path.stat().st_size
    ):
        raise LabError(f"{context} Python executable identity is stale")
    recorder_path = _require_string(identity.get("recorder_path"), f"{context}.recorder_path", nonempty=True)
    wrapper_path = _require_string(identity.get("wrapper_path"), f"{context}.wrapper_path", nonempty=True)
    if not Path(recorder_path).is_absolute() or not Path(wrapper_path).is_absolute():
        raise LabError(f"{context} paths must be absolute")
    if Path(recorder_path).name != "record_clang.py":
        raise LabError(f"{context}.recorder_path is not canonical")
    expected_wrapper_name = "record-clang.cmd" if expected_kind == "windows-cmd" else "record-clang"
    if Path(wrapper_path).name != expected_wrapper_name:
        raise LabError(f"{context}.wrapper_path is not canonical")

    recorder_bytes = _decode_bytes(
        identity.get("recorder_content_base64"),
        f"{context}.recorder_content_base64",
        maximum=MAX_RECORDER_SOURCE_BYTES,
    )
    wrapper_bytes = _decode_bytes(
        identity.get("wrapper_content_base64"),
        f"{context}.wrapper_content_base64",
        maximum=MAX_RECORDER_SOURCE_BYTES,
    )
    expected_recorder = _recording_recorder_text().encode("utf-8")
    expected_wrapper = _recording_wrapper_bytes(
        expected_kind,
        python_executable,
        recorder_path,
        _recording_recorder_text(),
    )
    if recorder_bytes != expected_recorder or identity.get("recorder_sha256") != _sha256_bytes(recorder_bytes):
        raise LabError(f"{context} recorder content is not canonical")
    if wrapper_bytes != expected_wrapper or identity.get("wrapper_sha256") != _sha256_bytes(wrapper_bytes):
        raise LabError(f"{context} wrapper content is not canonical")
    if identity.get("combined_sha256") != _recording_identity_digest(identity):
        raise LabError(f"{context}.combined_sha256 is invalid")
    return identity


def _validate_linker_identity(
    value: Any,
    context: str,
    clang: Path,
    link_arguments: Sequence[str],
    environment: Mapping[str, str],
    timeout: float,
    expected_link_invocation_sha256: str,
) -> dict[str, Any]:
    linker = _require_dict(value, context)
    expected_keys = {
        "link_invocation_sha256",
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
    if linker.get("link_invocation_sha256") != expected_link_invocation_sha256:
        raise LabError(f"{context} trace is detached from the successful link invocation")
    observed_path = _require_string(linker.get("observed_path"), f"{context}.observed_path", nonempty=True)
    path = _resolve_exact_executable(_require_string(linker.get("path"), f"{context}.path"), "result linker")
    if linker.get("sha256") != _sha256_file(path) or linker.get("bytes") != path.stat().st_size:
        raise LabError(f"{context} provenance is stale")
    stdout = _decode_bytes(linker.get("version_stdout_base64"), f"{context}.version_stdout_base64")
    stderr = _decode_bytes(linker.get("version_stderr_base64"), f"{context}.version_stderr_base64")
    trace = _decode_bytes(linker.get("trace_raw_base64"), f"{context}.trace_raw_base64")
    if linker.get("trace_sha256") != _sha256_bytes(trace):
        raise LabError(f"{context} trace checksum is invalid")
    if observed_path.encode("utf-8") not in trace and Path(observed_path).name.encode("utf-8") not in trace:
        raise LabError(f"{context} trace does not name the recorded linker")
    observed = _resolve_observed_linker(observed_path, environment)
    if _path_identity(str(observed)) != _path_identity(str(path)):
        raise LabError(f"{context} observed and resolved linker paths differ")
    with tempfile.TemporaryDirectory(prefix="freak-v3-linker-revalidate-") as temporary:
        live = _linker_identity_from_trace(
            clang,
            link_arguments,
            expected_link_invocation_sha256,
            Path(temporary).resolve(),
            environment,
            timeout,
        )
    if (
        _path_identity(str(path)) != _path_identity(live["path"])
        or linker.get("sha256") != live["sha256"]
        or linker.get("bytes") != live["bytes"]
        or linker.get("version_exit_code") != live["version_exit_code"]
        or stdout != _decode_bytes(live["version_stdout_base64"], f"{context} live version stdout")
        or stderr != _decode_bytes(live["version_stderr_base64"], f"{context} live version stderr")
    ):
        raise LabError(f"{context} differs from the linker derived by live Clang -###")
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
    compile_source_path: str,
    binary: Mapping[str, Any],
    recording_identity_sha256: str,
    clang: Path,
    environment: Mapping[str, str],
    timeout: float,
) -> None:
    observation = _require_dict(value, context)
    _exact_keys(observation, _COMPILE_OBSERVATION_KEYS, context)
    if observation.get("schema") != COMPILE_OBSERVATION_SCHEMA:
        raise LabError(f"{context}.schema is invalid")
    if observation.get("source_snapshot_sha256") != source_sha256:
        raise LabError(f"{context}.source_snapshot_sha256 differs from the compiled source")
    if observation.get("recording_identity_sha256") != recording_identity_sha256:
        raise LabError(f"{context}.recording_identity_sha256 differs from the root recorder")
    if (
        observation.get("recording_before_sha256") != recording_identity_sha256
        or observation.get("recording_after_sha256") != recording_identity_sha256
    ):
        raise LabError(f"{context} recorder source changed around the build")
    probes = _require_list(observation.get("probe_invocations"), f"{context}.probe_invocations")
    probe_invocations = [
        _validate_invocation_record(value, f"{context}.probe_invocations[{index}]")
        for index, value in enumerate(probes)
    ]
    if not any("--version" in invocation["argv"] and invocation["exit_code"] == 0 for invocation in probe_invocations):
        raise LabError(f"{context} lacks the CLI's Clang identity probe")
    raw_invocations = _require_list(observation.get("invocations"), f"{context}.invocations")
    invocations = [
        _validate_invocation_record(value, f"{context}.invocations[{index}]")
        for index, value in enumerate(raw_invocations)
    ]
    if not invocations:
        raise LabError(f"{context} has no build invocations")
    successful_links = [
        invocation
        for invocation in invocations
        if invocation["exit_code"] == 0 and "-c" not in invocation["argv"]
    ]
    if len(successful_links) != 1:
        raise LabError(f"{context} must contain exactly one successful link invocation")
    successful_link = successful_links[0]
    if observation.get("link_invocation_sha256") != successful_link["record_sha256"]:
        raise LabError(f"{context}.link_invocation_sha256 does not select the successful link")
    link_output = successful_link.get("output")
    if link_output is None or not _same_observed_file(link_output, binary):
        raise LabError(f"{context} successful link output differs from the executed binary")

    source_path = Path(compile_source_path)
    if not source_path.is_absolute() or source_path.name != Path(source_name).name:
        raise LabError(f"{context} compile source path is not canonical")
    expected_binary_paths = {
        _path_identity(str(source_path.with_suffix(".exe").resolve(strict=False))),
        _path_identity(str(source_path.with_suffix("").resolve(strict=False))),
    }
    if _path_identity(str(binary["path"])) not in expected_binary_paths:
        raise LabError(f"{context} binary path is detached from the compile source")

    flattened = [argument for invocation in invocations for argument in invocation["argv"]]
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
    link_arguments = successful_link["argv"]
    if sorted(set(argument for argument in link_arguments if argument.startswith("-fuse-ld="))) != _expected_linker_flags(profile):
        raise LabError(f"{context} successful linker flags do not implement {profile}")
    if profile == "+03" and "-flto=thin" not in link_arguments:
        raise LabError(f"{context} successful link omits ThinLTO")

    expected_suffix = ".c" if backend == "c" else ".ll"
    artifact = _require_dict(observation.get("backend_artifact"), f"{context}.backend_artifact")
    _exact_keys(artifact, _ARTIFACT_KEYS, f"{context}.backend_artifact")
    expected_artifact_path = str(Path(compile_source_path + expected_suffix).resolve(strict=False))
    artifact_path = _require_string(artifact.get("path"), f"{context}.backend_artifact.path", nonempty=True)
    if _path_identity(artifact_path) != _path_identity(expected_artifact_path):
        raise LabError(f"{context} backend artifact path is detached from the compile source")
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
    artifact_observation = {
        "path": artifact_path,
        "bytes": artifact_size,
        "sha256": artifact["sha256"],
    }
    artifact_consumers = [
        invocation
        for invocation in invocations
        if invocation["exit_code"] == 0
        and any(_same_observed_file(observed, artifact_observation) for observed in invocation["inputs"])
    ]
    if not artifact_consumers:
        raise LabError(f"{context} has no successful backend artifact consumer")
    for invocation in artifact_consumers:
        invocation_opt = sorted(set(argument for argument in invocation["argv"] if re.fullmatch(r"-O[^/\\]*", argument)))
        if invocation_opt != [profile_spec["opt"]]:
            raise LabError(f"{context} backend artifact consumer has the wrong optimization")
        if profile == "+03" and "-flto=thin" not in invocation["argv"]:
            raise LabError(f"{context} +03 backend artifact consumer omits ThinLTO")
    if not _pipeline_reaches(invocations, artifact_observation, binary):
        raise LabError(f"{context} backend artifact does not reach the executable binary")

    def validate_runtime_items(raw_value: Any, item_context: str) -> list[dict[str, Any]]:
        raw_items = _require_list(raw_value, item_context)
        items: list[dict[str, Any]] = []
        seen: set[str] = set()
        for index, raw_item in enumerate(raw_items):
            current = f"{item_context}[{index}]"
            item = _require_dict(raw_item, current)
            _exact_keys(item, {"name", "path", "bytes", "sha256"}, current)
            path = _resolve_exact_executable(_require_string(item.get("path"), f"{current}.path"), "runtime input")
            if item.get("name") != path.name or path.name not in _RUNTIME_INPUT_NAMES:
                raise LabError(f"{current} name is invalid")
            key = _path_identity(str(path))
            if key in seen:
                raise LabError(f"{item_context} repeats a runtime input")
            seen.add(key)
            if item.get("bytes") != path.stat().st_size or item.get("sha256") != _sha256_file(path):
                raise LabError(f"{current} provenance is stale")
            items.append(item)
        if items != sorted(items, key=lambda item: (item["name"], item["path"])):
            raise LabError(f"{item_context} is not canonically ordered")
        return items

    runtime_inputs = validate_runtime_items(observation.get("runtime_inputs"), f"{context}.runtime_inputs")
    linked_runtime_inputs = validate_runtime_items(
        observation.get("linked_runtime_inputs"),
        f"{context}.linked_runtime_inputs",
    )
    if runtime_inputs != _runtime_input_records(invocations):
        raise LabError(f"{context}.runtime_inputs are detached from invocation inputs")
    if linked_runtime_inputs != _runtime_input_records([successful_link]):
        raise LabError(f"{context}.linked_runtime_inputs are detached from the successful link")
    runtime_names = {item["name"] for item in linked_runtime_inputs}
    attempted_names = {item["name"] for item in runtime_inputs}
    derived_plan = _runtime_plan(runtime_names)
    derived_attempt_plan = _runtime_plan(attempted_names)
    if observation.get("runtime_plan") != derived_plan or derived_plan not in {"source", "bundle"}:
        raise LabError(f"{context} runtime plan is invalid")
    if observation.get("runtime_attempt_plan") != derived_attempt_plan or derived_attempt_plan == "missing":
        raise LabError(f"{context} runtime attempt plan is invalid")
    if profile == "+03" and (derived_plan != "source" or derived_attempt_plan != "source"):
        raise LabError(f"{context} +03 runtime plan is not source-linked")
    required_base = {"freak_runtime.c"} if derived_plan == "source" else {"freak_runtime.o", "freak_runtime.obj"}
    if not (runtime_names & required_base):
        raise LabError(f"{context} omits the base runtime")
    llvm_names = {"freak_llvm_runtime.c", "freak_llvm_runtime.o", "freak_llvm_runtime.obj"}
    if backend == "llvm" and not (runtime_names & llvm_names):
        raise LabError(f"{context} omits the LLVM runtime")
    if backend == "c" and runtime_names & llvm_names:
        raise LabError(f"{context} C backend unexpectedly links the LLVM runtime")

    _validate_linker_identity(
        observation.get("linker"),
        f"{context}.linker",
        clang,
        successful_link["argv"],
        environment,
        timeout,
        successful_link["record_sha256"],
    )


def _validate_execution_record(
    value: Any,
    context: str,
    index: int,
    mode: Mapping[str, Any],
    binary: Mapping[str, Any],
) -> tuple[int, dict[str, Any] | None]:
    record = _require_dict(value, context)
    _exact_keys(record, _SAMPLE_KEYS, context)
    if record.get("index") != index:
        raise LabError(f"{context} index is not canonical")
    duration = _require_int(record.get("duration_ns"), f"{context}.duration_ns", minimum=0)
    if record.get("exit_code") != mode["expected_exit_code"]:
        raise LabError(f"{context} exit code differs from manifest")
    command = _require_string_list(record.get("command"), f"{context}.command")
    expected_command = [binary["path"], *mode["arguments"]]
    if command != expected_command or record.get("command_sha256") != _json_sha256(command):
        raise LabError(f"{context} execution command differs from the workload")
    if (
        record.get("executable_bytes") != binary["bytes"]
        or record.get("executable_sha256_before") != binary["sha256"]
        or record.get("executable_sha256_after") != binary["sha256"]
    ):
        raise LabError(f"{context} executable identity differs around execution")
    raw_stdout = _decode_bytes(record.get("stdout_raw_base64"), f"{context}.stdout_raw_base64")
    raw_stderr = _decode_bytes(record.get("stderr_raw_base64"), f"{context}.stderr_raw_base64")
    if record.get("stdout_raw_sha256") != _sha256_bytes(raw_stdout):
        raise LabError(f"{context} raw stdout checksum is invalid")
    if record.get("stderr_raw_sha256") != _sha256_bytes(raw_stderr):
        raise LabError(f"{context} raw stderr checksum is invalid")
    canonical_stdout = _canonical_output(raw_stdout, f"{context} stdout")
    canonical_raw_stderr = _canonical_output(raw_stderr, f"{context} stderr")
    canonical_stderr, counter, counter_failures = _strip_runtime_stats(canonical_raw_stderr)
    if counter_failures:
        raise LabError(f"{context} runtime stats are invalid: {counter_failures}")
    for channel, text in (("stdout", canonical_stdout), ("stderr", canonical_stderr)):
        checksum = record.get(f"{channel}_sha256")
        if record.get(channel) != text:
            raise LabError(f"{context} stored {channel} differs from raw bytes")
        if text != mode[f"expected_{channel}"] or checksum != mode[f"expected_{channel}_sha256"]:
            raise LabError(f"{context} {channel} differs from manifest")
        if checksum != _sha256_text(text):
            raise LabError(f"{context} {channel} checksum is invalid")
    return duration, counter


def validate_output(path: Path, *, cli_override: str | None = None) -> dict[str, Any]:
    """Reject malformed, internally inconsistent, or stale lab output."""

    document = _require_dict(
        _strict_json(path.resolve(strict=True), maximum=MAX_RESULT_JSON_BYTES),
        "result",
    )
    required_root = {
        "schema",
        "trust_model",
        "lab",
        "manifest",
        "recording",
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
    trust_model = _require_dict(document["trust_model"], "result.trust_model")
    _exact_keys(trust_model, {"schema", "scope", "limitation"}, "result.trust_model")
    if trust_model != {
        "schema": TRUST_MODEL_SCHEMA,
        "scope": TRUST_MODEL_SCOPE,
        "limitation": TRUST_MODEL_LIMITATION,
    }:
        raise LabError("result trust model is invalid")

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
    recording_identity = _validate_recording_identity(document["recording"], "result.recording")

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
    warmups = _require_int(configuration.get("warmups"), "result.configuration.warmups", minimum=0)
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
        binary = _require_dict(result.get("binary"), f"{context}.binary")
        _exact_keys(binary, _BINARY_KEYS, f"{context}.binary")
        binary_path = _require_string(binary.get("path"), f"{context}.binary.path", nonempty=True)
        if not Path(binary_path).is_absolute():
            raise LabError(f"{context}.binary.path must be absolute")
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
        _validate_compile_observation(
            compile_info.get("observation"),
            context=f"{context}.compile.observation",
            backend=combination[1],
            profile=combination[2],
            target_requested=requested_target,
            source_name=case["source"],
            source_sha256=case["source_sha256"],
            compile_source_path=compile_command[2],
            binary=binary,
            recording_identity_sha256=recording_identity["combined_sha256"],
            clang=clang_path,
            environment=validation_environment,
            timeout=validation_timeout,
        )
        run = _require_dict(result.get("run"), f"{context}.run")
        _exact_keys(run, {"warmups", "samples", "median_ns"}, f"{context}.run")
        raw_warmups = _require_list(run.get("warmups"), f"{context}.run.warmups")
        if len(raw_warmups) != warmups:
            raise LabError(f"{context} has the wrong warmup count")
        for warmup_index, raw_warmup in enumerate(raw_warmups):
            _validate_execution_record(
                raw_warmup,
                f"{context}.run.warmups[{warmup_index}]",
                warmup_index,
                mode,
                binary,
            )
        raw_samples = _require_list(run.get("samples"), f"{context}.run.samples")
        if len(raw_samples) != samples:
            raise LabError(f"{context} has the wrong sample count")
        durations: list[int] = []
        observed_counters: list[dict[str, Any] | None] = []
        for sample_index, raw_sample in enumerate(raw_samples):
            duration, counter = _validate_execution_record(
                raw_sample,
                f"{context}.run.samples[{sample_index}]",
                sample_index,
                mode,
                binary,
            )
            durations.append(duration)
            observed_counters.append(counter)
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
    if len(encoded.encode("utf-8")) > MAX_RESULT_JSON_BYTES:
        raise LabError(f"result JSON exceeds the {MAX_RESULT_JSON_BYTES}-byte bound")
    if output == "-":
        sys.stdout.write(encoded)
        return
    destination = Path(output).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(encoded, encoding="utf-8", newline="\n")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=f"{TRUST_MODEL_HELP} {PROCESS_CONTAINMENT_HELP}",
    )
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
