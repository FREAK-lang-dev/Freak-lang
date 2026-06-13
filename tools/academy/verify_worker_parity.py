#!/usr/bin/env python3
"""Verify native and browser-safe FREAK Academy workers produce the same responses."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.academy.generate_worker_fixtures import iter_fixtures
from tools.academy.worker_host import handle_envelope


def run_browser_worker(node: str, request: dict[str, Any]) -> dict[str, Any]:
    result = subprocess.run(
        [node, "tools/academy/browser_worker_host.mjs"],
        cwd=ROOT,
        input=json.dumps(request),
        text=True,
        capture_output=True,
        timeout=30,
    )
    try:
        response = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"browser worker returned invalid JSON: {result.stdout!r} {result.stderr!r}") from exc
    if result.returncode != (0 if response.get("ok") else 1):
        raise RuntimeError(
            f"browser worker exit mismatch: exit={result.returncode}, ok={response.get('ok')}, stderr={result.stderr!r}"
        )
    return response


def compare_json(actual: Any, expected: Any, trail: str = "$") -> str:
    if actual == expected:
        return ""
    if isinstance(actual, list) or isinstance(expected, list):
        if not isinstance(actual, list) or not isinstance(expected, list):
            return f"{trail}: expected {type_name(expected)}, got {type_name(actual)}"
        if len(actual) != len(expected):
            return f"{trail}: expected {len(expected)} item(s), got {len(actual)}"
        for index, (actual_item, expected_item) in enumerate(zip(actual, expected)):
            diff = compare_json(actual_item, expected_item, f"{trail}[{index}]")
            if diff:
                return diff
        return ""
    if isinstance(actual, dict) or isinstance(expected, dict):
        if not isinstance(actual, dict) or not isinstance(expected, dict):
            return f"{trail}: expected {type_name(expected)}, got {type_name(actual)}"
        actual_keys = sorted(actual)
        expected_keys = sorted(expected)
        if actual_keys != expected_keys:
            return f"{trail}: expected keys {', '.join(expected_keys)}, got {', '.join(actual_keys)}"
        for key in expected_keys:
            diff = compare_json(actual[key], expected[key], f"{trail}.{key}")
            if diff:
                return diff
        return ""
    return f"{trail}: expected {expected!r}, got {actual!r}"


def type_name(value: Any) -> str:
    if isinstance(value, list):
        return "array"
    if value is None:
        return "null"
    return type(value).__name__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify native/browser Academy worker parity.")
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Only check the first N generated requests. Defaults to all requests.",
    )
    args = parser.parse_args(argv)

    node = shutil.which("node")
    if node is None:
        print("Academy worker parity failed: Node.js is required for the browser-safe worker.", file=sys.stderr)
        return 1

    fixtures = iter_fixtures(ROOT)
    if args.limit > 0:
        fixtures = fixtures[: args.limit]

    failures: list[str] = []
    for name, request in fixtures:
        native_response = handle_envelope(request)
        try:
            browser_response = run_browser_worker(node, request)
        except RuntimeError as exc:
            failures.append(f"{name}: {exc}")
            continue

        diff = compare_json(browser_response, native_response)
        if diff:
            failures.append(f"{name}: {diff}")
            continue
        print(f"{name}: native/browser OK")

    if failures:
        print("Academy worker parity failed:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    print(f"Academy worker parity passed: {len(fixtures)} request(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
