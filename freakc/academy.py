"""Shared FREAK Academy lesson loading helpers.

This module is intentionally small and file-based. The Academy internals are
being staged in this repo now, but should remain easy to move into a dedicated
Academy repository later.
"""

from __future__ import annotations

import json
import os
import hashlib
import shutil
import sys
from pathlib import Path
from typing import Any, Iterable


class AcademyError(Exception):
    """Raised when Academy content cannot be found or loaded."""


ACADEMY_PACKAGE_ID = "freak-academy-v3-mvp"
ACADEMY_LANGUAGE_VERSION = "0.13.3"
ACADEMY_COMPILER_TRACK = "v3"
ACADEMY_REPOSITORY_PHASE = "main-repo"
ACADEMY_WEBSITE_CONNECTOR = "freaklang.dev"
ACADEMY_WORKER_PROTOCOL_VERSION = 1


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


def build_academy_package(root: Path | None = None) -> dict[str, Any]:
    package_root = root or repository_root()
    courses: list[dict[str, Any]] = []
    for course in iter_courses(package_root):
        packaged_course = dict(course)
        packaged_course["lessonData"] = list(iter_course_lessons(course, root=package_root))
        courses.append(packaged_course)

    return {
        "schemaVersion": 1,
        "packageId": ACADEMY_PACKAGE_ID,
        "languageVersion": ACADEMY_LANGUAGE_VERSION,
        "compilerTrack": ACADEMY_COMPILER_TRACK,
        "repositoryPhase": ACADEMY_REPOSITORY_PHASE,
        "websiteConnector": ACADEMY_WEBSITE_CONNECTOR,
        "workerProtocolVersion": ACADEMY_WORKER_PROTOCOL_VERSION,
        "courses": courses,
    }


def export_academy_package(destination: Path, root: Path | None = None) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    package = build_academy_package(root=root)
    destination.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def academy_worker_path(root: Path | None = None) -> Path:
    return (root or repository_root()) / "learning" / "wasm" / "academy-worker.mjs"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _asset_record(path: Path, role: str, artifact_type: str) -> dict[str, Any]:
    return {
        "path": path.name,
        "role": role,
        "artifactType": artifact_type,
        "sha256": _sha256_file(path),
        "bytes": path.stat().st_size,
    }


def build_browser_assets(
    destination: Path,
    root: Path | None = None,
    *,
    include_wasm_evaluator: bool = False,
    wasm_compiler: str = "clang",
) -> dict[str, Any]:
    """Export the browser-consumable Academy package, worker, and manifest."""

    package_root = root or repository_root()
    destination.mkdir(parents=True, exist_ok=True)

    package_path = destination / "freak-academy-package.json"
    worker_source = academy_worker_path(package_root)
    worker_path = destination / "academy-worker.mjs"
    manifest_path = destination / "academy-assets-manifest.json"

    if not worker_source.exists():
        raise AcademyError(f"Academy browser worker not found: {worker_source}")

    export_academy_package(package_path, root=package_root)
    shutil.copyfile(worker_source, worker_path)

    assets = [
        _asset_record(package_path, "academy-package", "json"),
        _asset_record(worker_path, "worker-entrypoint", "browser-safe-js-reference"),
    ]
    wasm_evaluator_manifest: dict[str, Any] | None = None
    if include_wasm_evaluator:
        from tools.academy.build_wasm_evaluator import MANIFEST_NAME, WASM_NAME, build_wasm_evaluator

        wasm_evaluator_manifest = build_wasm_evaluator(destination, compiler=wasm_compiler)
        assets.append(_asset_record(destination / WASM_NAME, "wasm-evaluator", "wasm"))
        assets.append(_asset_record(destination / MANIFEST_NAME, "wasm-evaluator-manifest", "json"))

    manifest = {
        "schemaVersion": 1,
        "packageId": ACADEMY_PACKAGE_ID,
        "languageVersion": ACADEMY_LANGUAGE_VERSION,
        "compilerTrack": ACADEMY_COMPILER_TRACK,
        "repositoryPhase": ACADEMY_REPOSITORY_PHASE,
        "websiteConnector": ACADEMY_WEBSITE_CONNECTOR,
        "workerProtocolVersion": ACADEMY_WORKER_PROTOCOL_VERSION,
        "artifactStatus": "wasm-preview" if include_wasm_evaluator else "browser-safe-js-reference",
        "wasmStatus": "preview" if include_wasm_evaluator else "pending-v4-compiler-owned-artifact",
        "packagePath": package_path.name,
        "workerPath": worker_path.name,
        "assets": assets,
    }
    if wasm_evaluator_manifest is not None:
        manifest["wasmEvaluatorPath"] = wasm_evaluator_manifest["wasmPath"]
        manifest["wasmEvaluatorManifestPath"] = "academy-wasm-evaluator-manifest.json"
        manifest["wasmEvaluator"] = {
            "artifactStatus": wasm_evaluator_manifest["artifactStatus"],
            "supportedLessons": wasm_evaluator_manifest["supportedLessons"],
            "sha256": wasm_evaluator_manifest["sha256"],
            "bytes": wasm_evaluator_manifest["bytes"],
            "target": wasm_evaluator_manifest["target"],
        }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


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
            "  freak learn list",
            "  freak learn show <lesson-id>",
            "  freak learn demo <lesson-id>",
            "  freak learn start <lesson-id>",
            "  freak learn check <lesson-id> <file.fk>",
            "  freak learn status",
            "  freak learn export <path>",
            "  freak learn import <path>",
            "  freak learn reset [all|course-id|lesson-id]",
            "  freak learn package <path>",
            "  freak learn web-assets <dir> [--with-wasm-evaluator]",
            "  freak learn wasm-status [dir]",
            "  freak learn wasm-evaluator [dir]",
            "  freak learn worker [request.json]",
            "  freak learn worker-parity",
            "",
            "Bootstrap fallback: python -m freakc learn <cmd>",
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
    try:
        return normalize_progress(_load_json(target))
    except AcademyError as exc:
        raise AcademyError(f"{target}: {exc}") from exc


def save_progress(progress: dict[str, Any], path: Path | None = None) -> None:
    target = path or progress_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(normalize_progress(progress), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def normalize_progress(progress: dict[str, Any]) -> dict[str, Any]:
    if progress.get("schemaVersion") != 1:
        raise AcademyError("unsupported Academy progress schema")
    completed = progress.get("completedLessons", [])
    if not isinstance(completed, list):
        raise AcademyError("completedLessons must be a list")

    normalized: list[str] = []
    for item in completed:
        if not isinstance(item, str) or "/" not in item:
            raise AcademyError("completed lesson entries must be course/lesson strings")
        if item not in normalized:
            normalized.append(item)

    return {
        "schemaVersion": 1,
        "completedLessons": sorted(normalized),
    }


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


def export_progress(destination: Path, path: Path | None = None) -> None:
    progress = load_progress(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(progress, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def import_progress(source: Path, path: Path | None = None) -> None:
    progress = normalize_progress(_load_json(source))
    save_progress(progress, path)


def reset_progress(scope: str = "all", root: Path | None = None, path: Path | None = None) -> int:
    progress = load_progress(path)
    completed = set(str(item) for item in progress.get("completedLessons", []))

    if scope in ("", "all"):
        removed = len(completed)
        save_progress(default_progress(), path)
        return removed

    removed_keys: set[str] = set()
    course_ids = {str(course["id"]) for course in iter_courses(root)}
    if scope in course_ids:
        removed_keys = {key for key in completed if key.startswith(f"{scope}/")}
    else:
        for course in iter_courses(root):
            for lesson in iter_course_lessons(course, root=root):
                if lesson["id"] == scope:
                    removed_keys.add(progress_key(str(course["id"]), str(lesson["id"])))

    if not removed_keys:
        raise AcademyError(f"No progress entries match `{scope}`")

    progress["completedLessons"] = sorted(completed - removed_keys)
    save_progress(progress, path)
    return len(removed_keys)


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
