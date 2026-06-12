"""Shared FREAK Academy lesson loading helpers.

This module is intentionally small and file-based. The Academy internals are
being staged in this repo now, but should remain easy to move into a dedicated
Academy repository later.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable


class AcademyError(Exception):
    """Raised when Academy content cannot be found or loaded."""


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def courses_root(root: Path | None = None) -> Path:
    return (root or repository_root()) / "learning" / "courses"


def progress_path() -> Path:
    override = os.environ.get("FREAK_ACADEMY_PROGRESS")
    if override:
        return Path(override).expanduser()
    if sys.platform == "win32" and os.environ.get("APPDATA"):
        return Path(os.environ["APPDATA"]) / "FREAK" / "Academy" / "progress.json"
    return Path.home() / ".freak" / "academy" / "progress.json"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise AcademyError(f"Academy file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AcademyError(f"Invalid Academy JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise AcademyError(f"Academy file must contain a JSON object: {path}")
    return data


def iter_courses(root: Path | None = None) -> list[dict[str, Any]]:
    base = courses_root(root)
    if not base.exists():
        raise AcademyError(f"Academy courses directory not found: {base}")
    courses = [_load_json(path) for path in sorted(base.glob("*/course.json"))]
    if not courses:
        raise AcademyError(f"No Academy courses found under {base}")
    return courses


def load_course(course_id: str, root: Path | None = None) -> dict[str, Any]:
    return _load_json(courses_root(root) / course_id / "course.json")


def load_lesson(
    lesson_id: str,
    course_id: str | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    if course_id:
        return _load_json(courses_root(root) / course_id / "lessons" / f"{lesson_id}.json")

    matches: list[Path] = []
    for course in iter_courses(root):
        course_path = courses_root(root) / str(course["id"]) / "lessons" / f"{lesson_id}.json"
        if course_path.exists():
            matches.append(course_path)

    if not matches:
        raise AcademyError(f"Unknown Academy lesson: {lesson_id}")
    if len(matches) > 1:
        raise AcademyError(f"Lesson id is ambiguous across courses: {lesson_id}")
    return _load_json(matches[0])


def lesson_sections(lesson: dict[str, Any], section_type: str | None = None) -> list[dict[str, Any]]:
    sections = lesson.get("sections", [])
    if not isinstance(sections, list):
        raise AcademyError(f"Lesson {lesson.get('id', '<unknown>')} has invalid sections")
    if section_type is None:
        return [section for section in sections if isinstance(section, dict)]
    return [
        section
        for section in sections
        if isinstance(section, dict) and section.get("type") == section_type
    ]


def section_by_id(lesson: dict[str, Any], section_id: str) -> dict[str, Any]:
    for section in lesson_sections(lesson):
        if section.get("id") == section_id:
            return section
    raise AcademyError(f"Unknown section `{section_id}` in lesson `{lesson.get('id')}`")


def first_exercise(lesson: dict[str, Any]) -> dict[str, Any]:
    exercises = lesson_sections(lesson, "exercise")
    if not exercises:
        raise AcademyError(f"Lesson `{lesson.get('id')}` has no exercise section")
    return exercises[0]


def iter_course_lessons(course: dict[str, Any], root: Path | None = None) -> Iterable[dict[str, Any]]:
    course_id = str(course["id"])
    for lesson_id in course.get("lessons", []):
        yield load_lesson(str(lesson_id), course_id=course_id, root=root)


def format_course_listing(root: Path | None = None) -> str:
    lines = ["FREAK Academy", "", "Courses:"]
    for course in iter_courses(root):
        lessons = list(iter_course_lessons(course, root=root))
        lesson_word = "lesson" if len(lessons) == 1 else "lessons"
        lines.append(f"  {course['id']} - {course['title']} ({len(lessons)} {lesson_word})")
        for lesson in lessons:
            lines.append(f"    {lesson['order']}. {lesson['id']} - {lesson['title']}")
    lines.extend(
        [
            "",
            "Commands:",
            "  python -m freakc learn list",
            "  python -m freakc learn show <lesson-id>",
            "  python -m freakc learn demo <lesson-id>",
            "  python -m freakc learn check <lesson-id> <file.fk>",
            "  python -m freakc learn status",
        ]
    )
    return "\n".join(lines)


def format_lesson(lesson: dict[str, Any]) -> str:
    lines = [
        f"{lesson['title']} ({lesson['id']})",
        f"Course: {lesson['courseId']}",
        f"Compiler track: {lesson['compilerTrack']} / {lesson.get('supportLevel', 'unknown')}",
        "",
        "Objectives:",
    ]
    for objective in lesson.get("objectives", []):
        lines.append(f"  - {objective}")

    lines.extend(["", "Sections:"])
    for section in lesson_sections(lesson):
        lines.append(f"  - {section['id']} [{section['type']}] {section['title']}")
        if section.get("type") == "exercise" and "starter" in section:
            lines.append("    Starter:")
            for source_line in str(section["starter"]).splitlines():
                lines.append(f"      {source_line}")
    return "\n".join(lines)


def default_progress() -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "completedLessons": [],
    }


def load_progress(path: Path | None = None) -> dict[str, Any]:
    target = path or progress_path()
    if not target.exists():
        return default_progress()
    data = _load_json(target)
    if data.get("schemaVersion") != 1:
        raise AcademyError(f"Unsupported Academy progress schema in {target}")
    completed = data.get("completedLessons", [])
    if not isinstance(completed, list):
        raise AcademyError(f"Invalid completedLessons in {target}")
    return data


def save_progress(progress: dict[str, Any], path: Path | None = None) -> None:
    target = path or progress_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(progress, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def progress_key(course_id: str, lesson_id: str) -> str:
    return f"{course_id}/{lesson_id}"


def mark_lesson_complete(lesson: dict[str, Any], path: Path | None = None) -> bool:
    progress = load_progress(path)
    key = progress_key(str(lesson["courseId"]), str(lesson["id"]))
    completed = progress.setdefault("completedLessons", [])
    if key in completed:
        return False
    completed.append(key)
    completed.sort()
    save_progress(progress, path)
    return True


def format_progress(root: Path | None = None, path: Path | None = None) -> str:
    progress = load_progress(path)
    completed = set(str(item) for item in progress.get("completedLessons", []))

    lines = ["FREAK Academy Progress", ""]
    for course in iter_courses(root):
        lessons = list(iter_course_lessons(course, root=root))
        done_count = 0
        lines.append(f"{course['title']} ({course['id']})")
        for lesson in lessons:
            key = progress_key(str(course["id"]), str(lesson["id"]))
            done = key in completed
            done_count += 1 if done else 0
            status = "DONE" if done else "TODO"
            lines.append(f"  [{status}] {lesson['order']}. {lesson['id']} - {lesson['title']}")
        lines.append(f"  Progress: {done_count}/{len(lessons)} lessons")
        lines.append("")

    lines.append(f"Progress file: {progress_path() if path is None else path}")
    return "\n".join(lines).rstrip()
