#!/usr/bin/env python3
"""Local FREAK Academy worker-protocol host.

This is a native V3-backed adapter for the protocol the future browser/WASM
worker should implement. It is intentionally JSON-in/JSON-out so golden tests,
the website connector, and the WASM implementation can share fixtures.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from freakc.__main__ import (
    _academy_compile_submission,
    _academy_evaluate_submission,
    _academy_parse_submission,
)
from freakc.academy import AcademyError, first_exercise, load_lesson, section_by_id
from tools.academy.export_academy_package import build_package


PROTOCOL_VERSION = 1


class WorkerProtocolError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def response_ok(request_id: str, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "requestId": request_id,
        "ok": True,
        "result": result,
    }


def response_error(request_id: str, code: str, message: str) -> dict[str, Any]:
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "requestId": request_id,
        "ok": False,
        "error": {
            "code": code,
            "message": message,
        },
    }


def require_params(envelope: dict[str, Any]) -> dict[str, Any]:
    params = envelope.get("params")
    if not isinstance(params, dict):
        raise WorkerProtocolError("bad_request", "params must be an object")
    return params


def source_to_temp_file(source: str, file_id: str = "worker.fk") -> tuple[tempfile.TemporaryDirectory[str], Path]:
    tmp_ctx = tempfile.TemporaryDirectory(prefix="freak_academy_worker_")
    safe_name = Path(file_id).name or "worker.fk"
    if not safe_name.endswith(".fk"):
        safe_name += ".fk"
    source_path = Path(tmp_ctx.name) / safe_name
    source_path.write_text(source, encoding="utf-8")
    return tmp_ctx, source_path


def handle_package_info(_: dict[str, Any]) -> dict[str, Any]:
    package = build_package(ROOT)
    return {
        "packageId": package["packageId"],
        "languageVersion": package["languageVersion"],
        "compilerTrack": package["compilerTrack"],
        "workerProtocolVersion": package["workerProtocolVersion"],
        "courseCount": len(package["courses"]),
    }


def handle_check(params: dict[str, Any]) -> dict[str, Any]:
    source = params.get("source")
    if not isinstance(source, str):
        raise WorkerProtocolError("bad_request", "check requires string source")

    file_id = str(params.get("fileId", "worker.fk"))
    tmp_ctx, source_path = source_to_temp_file(source, file_id)
    with tmp_ctx:
        parsed, parse_messages = _academy_parse_submission(source_path)
        compiled = _academy_compile_submission(source_path, run_after=False) if parsed else {
            "ok": False,
            "messages": parse_messages,
        }
    return {
        "ok": bool(parsed and compiled["ok"]),
        "messages": [str(message) for message in compiled.get("messages", [])],
    }


def handle_run(params: dict[str, Any]) -> dict[str, Any]:
    source = params.get("source")
    if not isinstance(source, str):
        raise WorkerProtocolError("bad_request", "run requires string source")

    file_id = str(params.get("fileId", "worker.fk"))
    tmp_ctx, source_path = source_to_temp_file(source, file_id)
    with tmp_ctx:
        result = _academy_compile_submission(source_path, run_after=True)
    return {
        "ok": bool(result["ok"]),
        "stdout": str(result.get("stdout", "")),
        "stderr": str(result.get("stderr", "")),
        "returncode": int(result.get("returncode", 1 if not result["ok"] else 0)),
        "messages": [str(message) for message in result.get("messages", [])],
    }


def handle_evaluate_exercise(params: dict[str, Any]) -> dict[str, Any]:
    source = params.get("source")
    lesson_id = params.get("lessonId")
    if not isinstance(source, str):
        raise WorkerProtocolError("bad_request", "evaluateExercise requires string source")
    if not isinstance(lesson_id, str):
        raise WorkerProtocolError("bad_request", "evaluateExercise requires string lessonId")

    lesson = load_lesson(lesson_id)
    exercise_id = params.get("exerciseId")
    if isinstance(exercise_id, str) and exercise_id:
        exercise = section_by_id(lesson, exercise_id)
    else:
        exercise = first_exercise(lesson)

    file_id = str(params.get("fileId", f"{lesson_id}.fk"))
    tmp_ctx, source_path = source_to_temp_file(source, file_id)
    with tmp_ctx:
        requirements = _academy_evaluate_submission(exercise, source_path)

    return {
        "lessonId": lesson["id"],
        "exerciseId": exercise["id"],
        "passed": all(bool(item["passed"]) for item in requirements),
        "requirements": requirements,
    }


def handle_cancel(_: dict[str, Any]) -> dict[str, Any]:
    return {"cancelled": True}


HANDLERS = {
    "package.info": handle_package_info,
    "check": handle_check,
    "run": handle_run,
    "evaluateExercise": handle_evaluate_exercise,
    "cancel": handle_cancel,
}


def handle_envelope(envelope: dict[str, Any]) -> dict[str, Any]:
    request_id = str(envelope.get("requestId", ""))
    if envelope.get("protocolVersion") != PROTOCOL_VERSION:
        return response_error(request_id, "bad_protocol", "unsupported protocolVersion")
    if not request_id:
        return response_error("", "bad_request", "requestId is required")

    method = envelope.get("method")
    handler = HANDLERS.get(method)
    if handler is None:
        return response_error(request_id, "unknown_method", f"unknown method: {method}")

    try:
        result = handler(require_params(envelope))
        return response_ok(request_id, result)
    except WorkerProtocolError as exc:
        return response_error(request_id, exc.code, exc.message)
    except AcademyError as exc:
        return response_error(request_id, "academy_error", str(exc))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one FREAK Academy worker-protocol request.")
    parser.add_argument("request", nargs="?", help="Path to request JSON. Reads stdin when omitted.")
    args = parser.parse_args(argv)

    if args.request:
        raw = Path(args.request).read_text(encoding="utf-8")
    else:
        raw = sys.stdin.read()
    raw = raw.lstrip("\ufeff")
    if raw.startswith("\u00ef\u00bb\u00bf"):
        raw = raw[3:]

    try:
        envelope = json.loads(raw)
        if not isinstance(envelope, dict):
            raise ValueError("request JSON must be an object")
        response = handle_envelope(envelope)
    except Exception as exc:
        response = response_error("", "bad_json", str(exc))

    print(json.dumps(response, indent=2, sort_keys=True))
    return 0 if response.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
