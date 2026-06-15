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
BOOK_PATH = ROOT / "learning" / "book" / "freak-academy-book.json"
REFERENCE_PATH = ROOT / "learning" / "reference" / "freak-academy-reference.json"

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
        "academy-book.schema.json",
        "academy-package.schema.json",
        "academy-reference.schema.json",
        "academy-wasm-evaluator.schema.json",
        "academy-wasm-probe.schema.json",
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


def collect_lesson_index() -> tuple[set[str], set[str]]:
    lesson_ids: set[str] = set()
    concept_ids: set[str] = set()
    for course_path in sorted(COURSES_DIR.glob("*/course.json")):
        course = load_json(course_path)
        lessons_dir = course_path.parent / "lessons"
        for lesson_id in course.get("lessons", []):
            lesson_path = lessons_dir / f"{lesson_id}.json"
            lesson = load_json(lesson_path)
            lesson_ids.add(str(lesson["id"]))
            for concept_id in lesson.get("conceptIds", []):
                concept_ids.add(str(concept_id))
    return lesson_ids, concept_ids


def validate_reference(lesson_ids: set[str], concept_ids: set[str]) -> tuple[int, set[str]]:
    expect(REFERENCE_PATH.exists(), REFERENCE_PATH, "reference artifact is missing")
    reference = load_json(REFERENCE_PATH)
    expect(reference.get("schemaVersion") == 1, REFERENCE_PATH, "`schemaVersion` must be 1")
    expect(reference.get("packageId") == "freak-academy-v3-mvp", REFERENCE_PATH, "`packageId` is invalid")
    expect_version(reference.get("languageVersion"), REFERENCE_PATH, "languageVersion")
    expect(reference.get("compilerTrack") in {"v3", "v4"}, REFERENCE_PATH, "`compilerTrack` must be `v3` or `v4`")
    expect(reference.get("repositoryPhase") in {"main-repo", "split-ready", "dedicated-repo"}, REFERENCE_PATH, "`repositoryPhase` is invalid")
    expect(reference.get("websiteConnector") == "freaklang.dev", REFERENCE_PATH, "`websiteConnector` must be freaklang.dev")
    expect_string(reference.get("title"), REFERENCE_PATH, "title")
    expect_string(reference.get("description"), REFERENCE_PATH, "description")

    entries = reference.get("entries")
    expect(isinstance(entries, list) and entries, REFERENCE_PATH, "`entries` must be a non-empty list")
    entry_ids: set[str] = set()
    covered_concepts: set[str] = set()
    for entry in entries:
        validate_reference_entry(entry, entry_ids, lesson_ids, covered_concepts)

    for entry in entries:
        for related_id in entry.get("related", []):
            expect(related_id in entry_ids, REFERENCE_PATH, f"unknown related reference `{related_id}`")

    missing_concepts = sorted(concept_ids - covered_concepts)
    expect(not missing_concepts, REFERENCE_PATH, f"reference missing lesson concepts: {', '.join(missing_concepts)}")
    return len(entries), entry_ids


def validate_reference_entry(
    entry: Any,
    entry_ids: set[str],
    lesson_ids: set[str],
    covered_concepts: set[str],
) -> None:
    expect(isinstance(entry, dict), REFERENCE_PATH, "each reference entry must be an object")
    expect_id(entry.get("id"), REFERENCE_PATH, "entries[].id")
    expect(entry["id"] not in entry_ids, REFERENCE_PATH, f"duplicate reference id `{entry['id']}`")
    entry_ids.add(entry["id"])
    expect_string(entry.get("title"), REFERENCE_PATH, "entries[].title")
    expect(entry.get("status") in {"v3-mvp", "v4-planned", "stable"}, REFERENCE_PATH, f"invalid reference status `{entry.get('status')}`")
    expect_version(entry.get("since"), REFERENCE_PATH, "entries[].since")
    expect_string(entry.get("summary"), REFERENCE_PATH, "entries[].summary")

    concepts = entry.get("conceptIds")
    expect(isinstance(concepts, list) and concepts, REFERENCE_PATH, f"reference `{entry['id']}` needs conceptIds")
    expect(len(concepts) == len(set(concepts)), REFERENCE_PATH, f"reference `{entry['id']}` has duplicate conceptIds")
    for concept_id in concepts:
        expect_id(concept_id, REFERENCE_PATH, "entries[].conceptIds[]")
        covered_concepts.add(concept_id)

    lessons = entry.get("lessonIds")
    expect(isinstance(lessons, list) and lessons, REFERENCE_PATH, f"reference `{entry['id']}` needs lessonIds")
    expect(len(lessons) == len(set(lessons)), REFERENCE_PATH, f"reference `{entry['id']}` has duplicate lessonIds")
    for lesson_id in lessons:
        expect_id(lesson_id, REFERENCE_PATH, "entries[].lessonIds[]")
        expect(lesson_id in lesson_ids, REFERENCE_PATH, f"reference `{entry['id']}` points to unknown lesson `{lesson_id}`")

    for list_field in ("grammar", "staticSemantics", "dynamicSemantics"):
        values = entry.get(list_field)
        expect(isinstance(values, list) and values, REFERENCE_PATH, f"reference `{entry['id']}` needs `{list_field}`")
        for value in values:
            expect_string(value, REFERENCE_PATH, f"entries[].{list_field}[]")

    related = entry.get("related")
    expect(isinstance(related, list), REFERENCE_PATH, f"reference `{entry['id']}` needs related list")
    expect(len(related) == len(set(related)), REFERENCE_PATH, f"reference `{entry['id']}` has duplicate related ids")
    for related_id in related:
        expect_id(related_id, REFERENCE_PATH, "entries[].related[]")

    examples = entry.get("examples")
    expect(isinstance(examples, list) and examples, REFERENCE_PATH, f"reference `{entry['id']}` needs examples")
    for example in examples:
        expect(isinstance(example, dict), REFERENCE_PATH, "each reference example must be an object")
        expect_string(example.get("title"), REFERENCE_PATH, "entries[].examples[].title")
        validate_freak_snippet(example.get("source"), REFERENCE_PATH, f"reference `{entry['id']}` example source")
        expect(isinstance(example.get("expectedOutput"), str), REFERENCE_PATH, "entries[].examples[].expectedOutput")


def validate_book(lesson_ids: set[str], concept_ids: set[str], reference_ids: set[str]) -> int:
    expect(BOOK_PATH.exists(), BOOK_PATH, "book artifact is missing")
    book = load_json(BOOK_PATH)
    expect(book.get("schemaVersion") == 1, BOOK_PATH, "`schemaVersion` must be 1")
    expect(book.get("packageId") == "freak-academy-v3-mvp", BOOK_PATH, "`packageId` is invalid")
    expect_version(book.get("languageVersion"), BOOK_PATH, "languageVersion")
    expect(book.get("compilerTrack") in {"v3", "v4"}, BOOK_PATH, "`compilerTrack` must be `v3` or `v4`")
    expect(book.get("repositoryPhase") in {"main-repo", "split-ready", "dedicated-repo"}, BOOK_PATH, "`repositoryPhase` is invalid")
    expect(book.get("websiteConnector") == "freaklang.dev", BOOK_PATH, "`websiteConnector` must be freaklang.dev")
    expect_string(book.get("title"), BOOK_PATH, "title")
    expect_string(book.get("description"), BOOK_PATH, "description")

    parts = book.get("parts")
    expect(isinstance(parts, list) and parts, BOOK_PATH, "`parts` must be a non-empty list")
    part_ids: set[str] = set()
    chapter_ids: set[str] = set()
    chapter_slugs: set[str] = set()
    chapter_count = 0
    for part in parts:
        expect(isinstance(part, dict), BOOK_PATH, "each part must be an object")
        expect_id(part.get("id"), BOOK_PATH, "parts[].id")
        expect(part["id"] not in part_ids, BOOK_PATH, f"duplicate part id `{part['id']}`")
        part_ids.add(part["id"])
        expect_string(part.get("title"), BOOK_PATH, "parts[].title")
        expect_string(part.get("summary"), BOOK_PATH, "parts[].summary")
        chapters = part.get("chapters")
        expect(isinstance(chapters, list) and chapters, BOOK_PATH, f"part `{part['id']}` needs chapters")
        for chapter in chapters:
            validate_book_chapter(chapter, chapter_ids, chapter_slugs, lesson_ids, concept_ids, reference_ids)
            chapter_count += 1

    return chapter_count


def validate_book_chapter(
    chapter: Any,
    chapter_ids: set[str],
    chapter_slugs: set[str],
    lesson_ids: set[str],
    concept_ids: set[str],
    reference_ids: set[str],
) -> None:
    expect(isinstance(chapter, dict), BOOK_PATH, "each book chapter must be an object")
    expect_id(chapter.get("id"), BOOK_PATH, "chapters[].id")
    expect(chapter["id"] not in chapter_ids, BOOK_PATH, f"duplicate chapter id `{chapter['id']}`")
    chapter_ids.add(chapter["id"])
    expect_string(chapter.get("title"), BOOK_PATH, "chapters[].title")
    expect_string(chapter.get("slug"), BOOK_PATH, "chapters[].slug")
    expect(chapter["slug"] not in chapter_slugs, BOOK_PATH, f"duplicate chapter slug `{chapter['slug']}`")
    chapter_slugs.add(chapter["slug"])
    expect(chapter.get("status") in {"v3-mvp", "v4-placeholder", "stable"}, BOOK_PATH, f"invalid chapter status `{chapter.get('status')}`")
    expect_version(chapter.get("since"), BOOK_PATH, "chapters[].since")
    expect_string(chapter.get("summary"), BOOK_PATH, "chapters[].summary")

    for field, known_ids in (
        ("conceptIds", concept_ids),
        ("lessonIds", lesson_ids),
        ("referenceIds", reference_ids),
    ):
        values = chapter.get(field)
        expect(isinstance(values, list) and values, BOOK_PATH, f"chapter `{chapter['id']}` needs {field}")
        expect(len(values) == len(set(values)), BOOK_PATH, f"chapter `{chapter['id']}` has duplicate {field}")
        for value in values:
            expect_id(value, BOOK_PATH, f"chapters[].{field}[]")
            expect(value in known_ids, BOOK_PATH, f"chapter `{chapter['id']}` points to unknown {field} `{value}`")

    sections = chapter.get("sections")
    expect(isinstance(sections, list) and sections, BOOK_PATH, f"chapter `{chapter['id']}` needs sections")
    section_ids: set[str] = set()
    for section in sections:
        expect(isinstance(section, dict), BOOK_PATH, "each book section must be an object")
        expect_id(section.get("id"), BOOK_PATH, "chapters[].sections[].id")
        expect(section["id"] not in section_ids, BOOK_PATH, f"chapter `{chapter['id']}` has duplicate section id `{section['id']}`")
        section_ids.add(section["id"])
        expect_string(section.get("title"), BOOK_PATH, "chapters[].sections[].title")
        expect_string(section.get("body"), BOOK_PATH, "chapters[].sections[].body")
        examples = section.get("examples", [])
        expect(isinstance(examples, list), BOOK_PATH, "chapters[].sections[].examples must be a list")
        for example in examples:
            expect(isinstance(example, dict), BOOK_PATH, "each book example must be an object")
            expect_string(example.get("title"), BOOK_PATH, "chapters[].sections[].examples[].title")
            validate_freak_snippet(example.get("source"), BOOK_PATH, f"chapter `{chapter['id']}` example source")
            expect(isinstance(example.get("expectedOutput"), str), BOOK_PATH, "chapters[].sections[].examples[].expectedOutput")


def main() -> int:
    try:
        validate_schema_files()
        course_count, lesson_count = validate_courses()
        lesson_ids, concept_ids = collect_lesson_index()
        reference_count, reference_ids = validate_reference(lesson_ids, concept_ids)
        chapter_count = validate_book(lesson_ids, concept_ids, reference_ids)
    except ValidationError as exc:
        print(f"Academy validation failed: {exc}", file=sys.stderr)
        return 1

    print(
        f"Academy validation passed: {course_count} course(s), "
        f"{lesson_count} lesson(s), {reference_count} reference entry(s), "
        f"{chapter_count} book chapter(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
