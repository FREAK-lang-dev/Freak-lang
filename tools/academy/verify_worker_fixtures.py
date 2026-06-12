#!/usr/bin/env python3
"""Verify Academy worker protocol golden fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.academy.worker_host import handle_envelope


DEFAULT_FIXTURE_DIR = ROOT / "learning" / "wasm" / "fixtures"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def normalized(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def verify_fixture(request_path: Path) -> tuple[bool, str]:
    response_path = request_path.with_name(request_path.name.replace(".request.json", ".response.json"))
    if not response_path.exists():
        return False, f"missing response fixture: {response_path}"

    request = load_json(request_path)
    expected = load_json(response_path)
    actual = handle_envelope(request)

    if actual == expected:
        return True, f"{request_path.name}: OK"

    return (
        False,
        "\n".join([
            f"{request_path.name}: mismatch",
            "expected:",
            normalized(expected).rstrip(),
            "actual:",
            normalized(actual).rstrip(),
        ]),
    )


def verify_all(fixture_dir: Path = DEFAULT_FIXTURE_DIR) -> int:
    request_paths = sorted(fixture_dir.glob("*.request.json"))
    if not request_paths:
        print(f"No worker fixtures found in {fixture_dir}", file=sys.stderr)
        return 1

    failures = 0
    for request_path in request_paths:
        ok, message = verify_fixture(request_path)
        print(message)
        if not ok:
            failures += 1

    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify Academy worker protocol fixtures.")
    parser.add_argument("--fixtures", default=str(DEFAULT_FIXTURE_DIR), help="Directory containing *.request.json fixtures.")
    args = parser.parse_args(argv)

    return verify_all(Path(args.fixtures))


if __name__ == "__main__":
    raise SystemExit(main())
