#!/usr/bin/env python3
"""Export FREAK Academy lessons as one browser-consumable JSON package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from freakc.academy import iter_course_lessons, iter_courses


def build_package(root: Path = ROOT) -> dict[str, Any]:
    courses: list[dict[str, Any]] = []
    for course in iter_courses(root):
        packaged_course = dict(course)
        packaged_course["lessonData"] = list(iter_course_lessons(course, root=root))
        courses.append(packaged_course)

    return {
        "schemaVersion": 1,
        "packageId": "freak-academy-v3-mvp",
        "languageVersion": "0.13.3",
        "compilerTrack": "v3",
        "repositoryPhase": "main-repo",
        "websiteConnector": "freaklang.dev",
        "workerProtocolVersion": 1,
        "courses": courses,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export FREAK Academy lesson package JSON.")
    parser.add_argument("--output", "-o", help="Write package JSON to this path instead of stdout.")
    args = parser.parse_args(argv)

    package = build_package()
    payload = json.dumps(package, indent=2, sort_keys=True) + "\n"

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
