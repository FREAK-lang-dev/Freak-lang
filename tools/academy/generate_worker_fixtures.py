#!/usr/bin/env python3
"""Generate FREAK Academy worker protocol golden fixtures from lesson demos."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from freakc.academy import build_academy_package, first_exercise, lesson_sections
from tools.academy.worker_host import handle_envelope


DEFAULT_FIXTURE_DIR = ROOT / "learning" / "wasm" / "fixtures"


def normalized(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def fixture_stem(lesson_id: str) -> str:
    if lesson_id == "hello-freak":
        return "hello"
    return lesson_id.replace("-", "_")


def first_demo_source(lesson: dict[str, Any]) -> str:
    for section in lesson_sections(lesson, "demonstration"):
        source = section.get("source")
        if isinstance(source, str):
            return source
    raise ValueError(f"lesson `{lesson.get('id')}` has no demonstration source")


def request_fixture(name: str, method: str, request_id: str, params: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    return (
        name,
        {
            "protocolVersion": 1,
            "requestId": request_id,
            "method": method,
            "params": params,
        },
    )


def iter_fixtures(root: Path) -> list[tuple[str, dict[str, Any]]]:
    package = build_academy_package(root)
    fixtures: list[tuple[str, dict[str, Any]]] = [
        request_fixture("package_info", "package.info", "fixture-package-info", {}),
    ]

    for course in package["courses"]:
        for lesson in course["lessonData"]:
            lesson_id = str(lesson["id"])
            source = first_demo_source(lesson)
            stem = fixture_stem(lesson_id)
            file_id = f"{lesson_id}.fk"
            exercise = first_exercise(lesson)

            fixtures.extend(
                [
                    request_fixture(
                        f"check_{stem}",
                        "check",
                        f"fixture-check-{stem}",
                        {"fileId": file_id, "source": source},
                    ),
                    request_fixture(
                        f"run_{stem}",
                        "run",
                        f"fixture-run-{stem}",
                        {"fileId": file_id, "source": source},
                    ),
                    request_fixture(
                        f"evaluate_{stem}",
                        "evaluateExercise",
                        f"fixture-evaluate-{stem}",
                        {
                            "lessonId": lesson_id,
                            "exerciseId": exercise["id"],
                            "source": source,
                        },
                    ),
                ]
            )

    return fixtures


def write_fixtures(fixture_dir: Path, root: Path = ROOT) -> int:
    fixture_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for name, request in iter_fixtures(root):
        response = handle_envelope(request)
        (fixture_dir / f"{name}.request.json").write_text(normalized(request), encoding="utf-8")
        (fixture_dir / f"{name}.response.json").write_text(normalized(response), encoding="utf-8")
        count += 1
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Academy worker protocol golden fixtures.")
    parser.add_argument("--fixtures", default=str(DEFAULT_FIXTURE_DIR), help="Directory to write *.request/response.json fixtures.")
    args = parser.parse_args(argv)

    count = write_fixtures(Path(args.fixtures))
    print(f"Generated {count} worker fixture pair(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
