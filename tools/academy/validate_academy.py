#!/usr/bin/env python3
"""Validate FREAK Academy schemas and seed course data.

This is a deliberately small stdlib-only validator for the V3-first phase.
It checks the contracts that matter before a full schema-validation toolchain
exists in FREAK itself.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schemas"
COURSES_DIR = ROOT / "learning" / "courses"

ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")

SECTION_TYPES = {
    "introduction",
    "demonstration",
    "explanation",
    "exercise",
    "quiz",
    "summary",
}

REQUIREMENT_KINDS = {
    "parses",
    "compiles",
    "symbol_exists",
    "symbol_type",
    "constant_value",
    "function_exists",
    "function_signature",
    "calls_function",
    "printed_symbol",
    "construct_used",
    "operator_used",
    "expected_output",
    "tests_pass",
    "diagnostic_expected",
    "diagnostic_absent",
}

FREAK_SOURCE_FIELDS = ("source", "starter")
LEGACY_SYNTAX_MARKERS = ("let ", "print(")


class ValidationError(Exception):
    pass


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"{path}: invalid JSON: {exc}") from exc


def expect(condition: bool, path: Path, message: str) -> None:
    if not condition:
        raise ValidationError(f"{path}: {message}")


def expect_id(value: Any, path: Path, field: str) -> None:
    expect(isinstance(value, str) and bool(ID_RE.match(value)), path, f"`{field}` must be a stable lowercase id")


def expect_version(value: Any, path: Path, field: str) -> None:
    expect(isinstance(value, str) and bool(VERSION_RE.match(value)), path, f"`{field}` must be semver-like")


def expect_string(value: Any, path: Path, field: str) -> None:
    expect(isinstance(value, str) and bool(value.strip()), path, f"`{field}` must be a non-empty string")


def validate_schema_files() -> None:
    required = [
        "academy-browser-assets.schema.json",
        "academy-package.schema.json",
        "academy-worker-protocol.schema.json",
        "academy-worker-response.schema.json",
        "course.schema.json",
        "lesson.schema.json",
    ]
    for name in required:
        path = SCHEMA_DIR / name
        expect(path.exists(), path, "schema file is missing")
        data = load_json(path)
        expect(data.get("$schema") == "https://json-schema.org/draft/2020-12/schema", path, "schema draft must be 2020-12")
        expect_string(data.get("$id"), path, "$id")
        expect_string(data.get("title"), path, "title")


def validate_course(path: Path) -> dict[str, Any]:
    course = load_json(path)
    expect(course.get("schemaVersion") == 1, path, "`schemaVersion` must be 1")
    expect_id(course.get("id"), path, "id")
    expect_string(course.get("title"), path, "title")
    expect_string(course.get("description"), path, "description")
    expect_version(course.get("languageVersion"), path, "languageVersion")
    expect(course.get("compilerTrack") in {"v3", "v4"}, path, "`compilerTrack` must be `v3` or `v4`")
    expect(course.get("repositoryPhase") in {"main-repo", "split-ready", "dedicated-repo"}, path, "`repositoryPhase` is invalid")
    expect_string(course.get("websitePath"), path, "websitePath")
    expect(course["websitePath"].startswith("/"), path, "`websitePath` must be absolute")

    lessons = course.get("lessons")
    expect(isinstance(lessons, list) and lessons, path, "`lessons` must be a non-empty list")
    expect(len(lessons) == len(set(lessons)), path, "`lessons` must not contain duplicates")
    for lesson_id in lessons:
        expect_id(lesson_id, path, "lessons[]")
    return course


def validate_lesson(path: Path, course: dict[str, Any], expected_order: int) -> dict[str, Any]:
    lesson = load_json(path)
    expect(lesson.get("schemaVersion") == 1, path, "`schemaVersion` must be 1")
    expect_id(lesson.get("id"), path, "id")
    expect(lesson.get("courseId") == course["id"], path, "`courseId` must match the course")
    expect_string(lesson.get("title"), path, "title")
    expect(lesson.get("order") == expected_order, path, "`order` must match course lesson order")
    expect_version(lesson.get("languageVersion"), path, "languageVersion")
    expect(lesson.get("compilerTrack") == course["compilerTrack"], path, "`compilerTrack` must match the course")
    expect(lesson.get("supportLevel") in {"v3-mvp", "v4-planned", "stable"}, path, "`supportLevel` is invalid")

    objectives = lesson.get("objectives")
    expect(isinstance(objectives, list) and objectives, path, "`objectives` must be a non-empty list")
    for objective in objectives:
        expect_string(objective, path, "objectives[]")

    sections = lesson.get("sections")
    expect(isinstance(sections, list) and sections, path, "`sections` must be a non-empty list")
    section_ids: set[str] = set()
    has_exercise = False
    has_quiz = False

    for section in sections:
        expect(isinstance(section, dict), path, "each section must be an object")
        expect_id(section.get("id"), path, "sections[].id")
        expect(section["id"] not in section_ids, path, f"duplicate section id `{section['id']}`")
        section_ids.add(section["id"])
        expect(section.get("type") in SECTION_TYPES, path, f"invalid section type `{section.get('type')}`")
        expect_string(section.get("title"), path, "sections[].title")

        for field in FREAK_SOURCE_FIELDS:
            if field in section:
                validate_freak_snippet(section[field], path, f"section `{section['id']}` `{field}`")

        if section["type"] == "demonstration":
            expect_string(section.get("source"), path, f"demonstration `{section['id']}` needs source")
            expect(isinstance(section.get("expectedOutput"), str), path, f"demonstration `{section['id']}` needs expectedOutput")

        if section["type"] == "exercise":
            has_exercise = True
            expect_string(section.get("prompt"), path, f"exercise `{section['id']}` needs prompt")
            expect_string(section.get("starter"), path, f"exercise `{section['id']}` needs starter")
            requirements = section.get("requirements")
            expect(isinstance(requirements, list) and requirements, path, f"exercise `{section['id']}` needs requirements")
            for requirement in requirements:
                validate_requirement(requirement, path)

        if section["type"] == "quiz":
            has_quiz = True
            questions = section.get("questions")
            expect(isinstance(questions, list) and questions, path, f"quiz `{section['id']}` needs questions")
            for question in questions:
                validate_question(question, path)

    expect(has_exercise, path, "lesson needs at least one exercise section")
    expect(has_quiz, path, "lesson needs at least one quiz section")
    return lesson


def validate_freak_snippet(source: Any, path: Path, label: str) -> None:
    expect(isinstance(source, str), path, f"{label} must be a string")
    for marker in LEGACY_SYNTAX_MARKERS:
        expect(marker not in source, path, f"{label} contains legacy syntax marker `{marker}`")


def validate_requirement(requirement: Any, path: Path) -> None:
    expect(isinstance(requirement, dict), path, "each requirement must be an object")
    expect_id(requirement.get("id"), path, "requirements[].id")
    kind = requirement.get("kind")
    expect(kind in REQUIREMENT_KINDS, path, f"unknown requirement kind `{kind}`")
    if kind == "expected_output":
        expect(isinstance(requirement.get("expected"), str), path, "`expected_output` requires string `expected`")


def validate_question(question: Any, path: Path) -> None:
    expect(isinstance(question, dict), path, "each quiz question must be an object")
    expect_id(question.get("id"), path, "questions[].id")
    expect_string(question.get("prompt"), path, "questions[].prompt")
    choices = question.get("choices")
    expect(isinstance(choices, list) and len(choices) >= 2, path, "`choices` needs at least two answers")
    for choice in choices:
        expect_string(choice, path, "choices[]")
    answer = question.get("answer")
    expect(isinstance(answer, int) and 0 <= answer < len(choices), path, "`answer` must point at a choice")


def validate_courses() -> tuple[int, int]:
    expect(COURSES_DIR.exists(), COURSES_DIR, "courses directory is missing")
    courses = sorted(COURSES_DIR.glob("*/course.json"))
    expect(bool(courses), COURSES_DIR, "no courses found")

    lesson_count = 0
    for course_path in courses:
        course = validate_course(course_path)
        lessons_dir = course_path.parent / "lessons"
        expect(lessons_dir.exists(), lessons_dir, "lessons directory is missing")
        for index, lesson_id in enumerate(course["lessons"], start=1):
            lesson_path = lessons_dir / f"{lesson_id}.json"
            expect(lesson_path.exists(), lesson_path, "listed lesson file is missing")
            lesson = validate_lesson(lesson_path, course, index)
            expect(lesson["id"] == lesson_id, lesson_path, "lesson id must match file name and course list")
            lesson_count += 1
    return len(courses), lesson_count


def main() -> int:
    try:
        validate_schema_files()
        course_count, lesson_count = validate_courses()
    except ValidationError as exc:
        print(f"Academy validation failed: {exc}", file=sys.stderr)
        return 1

    print(f"Academy validation passed: {course_count} course(s), {lesson_count} lesson(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
