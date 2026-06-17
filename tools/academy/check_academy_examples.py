#!/usr/bin/env python3
"""Run Academy lesson, reference, and Book examples through the V3 worker."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from freakc.academy import build_academy_book, build_academy_reference, iter_courses, iter_course_lessons, lesson_sections
from tools.academy.worker_host import handle_envelope


@dataclass(frozen=True)
class AcademyExample:
    source_name: str
    stable_id: str
    title: str
    source: str
    expected_output: str


def slug(value: str) -> str:
    chars: list[str] = []
    last_dash = False
    for char in value.lower():
        if "a" <= char <= "z" or "0" <= char <= "9":
            chars.append(char)
            last_dash = False
        elif not last_dash:
            chars.append("-")
            last_dash = True
    return "".join(chars).strip("-") or "example"


def iter_lesson_examples(root: Path = ROOT) -> Iterable[AcademyExample]:
    for course in iter_courses(root):
        for lesson in iter_course_lessons(course, root=root):
            for section in lesson_sections(lesson, "demonstration"):
                source = section.get("source")
                expected = section.get("expectedOutput")
                if isinstance(source, str) and isinstance(expected, str):
                    yield AcademyExample(
                        source_name="lesson",
                        stable_id=f"lesson:{lesson['id']}:{section['id']}",
                        title=str(section.get("title", section["id"])),
                        source=source,
                        expected_output=expected,
                    )


def iter_reference_examples(root: Path = ROOT) -> Iterable[AcademyExample]:
    reference = build_academy_reference(root)
    for entry in reference.get("entries", []):
        for index, example in enumerate(entry.get("examples", []), start=1):
            source = example.get("source")
            expected = example.get("expectedOutput")
            if isinstance(source, str) and isinstance(expected, str):
                yield AcademyExample(
                    source_name="reference",
                    stable_id=f"reference:{entry['id']}:{index}",
                    title=str(example.get("title", f"Example {index}")),
                    source=source,
                    expected_output=expected,
                )


def iter_book_examples(root: Path = ROOT) -> Iterable[AcademyExample]:
    book = build_academy_book(root)
    for part in book.get("parts", []):
        for chapter in part.get("chapters", []):
            for section in chapter.get("sections", []):
                for index, example in enumerate(section.get("examples", []), start=1):
                    source = example.get("source")
                    expected = example.get("expectedOutput")
                    if isinstance(source, str) and isinstance(expected, str):
                        yield AcademyExample(
                            source_name="book",
                            stable_id=f"book:{chapter['slug']}:{section['id']}:{index}",
                            title=str(example.get("title", f"Example {index}")),
                            source=source,
                            expected_output=expected,
                        )


def iter_academy_examples(root: Path = ROOT) -> list[AcademyExample]:
    return [
        *iter_lesson_examples(root),
        *iter_reference_examples(root),
        *iter_book_examples(root),
    ]


def check_example(example: AcademyExample) -> dict[str, Any]:
    request_id = f"check-{slug(example.stable_id)}"
    response = handle_envelope(
        {
            "protocolVersion": 1,
            "requestId": request_id,
            "method": "run",
            "params": {
                "fileId": f"{slug(example.stable_id)}.fk",
                "source": example.source,
            },
        }
    )

    result = response.get("result") if isinstance(response, dict) else None
    actual_output = ""
    ok = False
    message = ""
    if response.get("ok") is not True or not isinstance(result, dict):
        error = response.get("error", {})
        message = str(error.get("message", "worker request failed")) if isinstance(error, dict) else "worker request failed"
    else:
        actual_output = str(result.get("stdout", ""))
        run_ok = bool(result.get("ok"))
        output_ok = actual_output == example.expected_output
        ok = run_ok and output_ok
        if ok:
            message = "output matches"
        elif not run_ok:
            messages = result.get("messages", [])
            message = "\n".join(str(item) for item in messages) or str(result.get("stderr", "program failed"))
        else:
            message = f"expected output {example.expected_output!r}, got {actual_output!r}"

    return {
        "ok": ok,
        "source": example.source_name,
        "id": example.stable_id,
        "title": example.title,
        "expectedOutput": example.expected_output,
        "actualOutput": actual_output,
        "message": message,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Academy examples and verify expected output.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable check results.",
    )
    parser.add_argument(
        "--source",
        choices=["all", "lesson", "reference", "book"],
        default="all",
        help="Limit checks to one Academy source. Defaults to all.",
    )
    args = parser.parse_args(argv)

    examples = iter_academy_examples(ROOT)
    if args.source != "all":
        examples = [example for example in examples if example.source_name == args.source]

    results = [check_example(example) for example in examples]
    failed = [result for result in results if not result["ok"]]

    if args.json:
        print(json.dumps({"ok": not failed, "count": len(results), "results": results}, indent=2, sort_keys=True))
    else:
        for result in results:
            status = "OK" if result["ok"] else "FAIL"
            print(f"{result['source']} {result['id']}: {status}")
            if not result["ok"]:
                print(f"  {result['message']}")
        print(f"Academy example checks passed: {len(results) - len(failed)}/{len(results)} example(s).")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
