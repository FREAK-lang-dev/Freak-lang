from __future__ import annotations

import io
import os
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from freakc.__main__ import main
from freakc.academy import (
    first_exercise,
    format_course_listing,
    format_progress,
    load_course,
    load_lesson,
    load_progress,
    mark_lesson_complete,
)


def test_seed_course_loads():
    course = load_course("freak-basics")

    assert course["compilerTrack"] == "v3"
    assert course["lessons"] == [
        "hello-freak",
        "variables",
        "primitive-types",
        "arithmetic",
        "conditions",
        "loops",
        "functions",
    ]


def test_seed_lesson_has_v3_exercise_contracts():
    lesson = load_lesson("hello-freak")
    exercise = first_exercise(lesson)

    assert lesson["supportLevel"] == "v3-mvp"
    assert exercise["id"] == "hello-exercise"
    assert [req["kind"] for req in exercise["requirements"]] == [
        "parses",
        "compiles",
        "expected_output",
    ]


def test_course_listing_mentions_seed_lesson():
    listing = format_course_listing()

    assert "freak-basics" in listing
    assert "hello-freak" in listing
    assert "functions" in listing
    assert "python -m freakc learn check <lesson-id> <file.fk>" in listing


def test_learn_list_cli_outputs_seed_course():
    out = io.StringIO()

    with redirect_stdout(out):
        code = main(["learn", "list"])

    assert code == 0
    assert "FREAK Academy" in out.getvalue()
    assert "hello-freak" in out.getvalue()


def test_learn_show_cli_outputs_lesson_outline():
    out = io.StringIO()

    with redirect_stdout(out):
        code = main(["learn", "show", "hello-freak"])

    assert code == 0
    assert "Hello, FREAK" in out.getvalue()
    assert "Compiler track: v3 / v3-mvp" in out.getvalue()


def test_progress_records_completed_lesson():
    lesson = load_lesson("hello-freak")

    with tempfile.TemporaryDirectory() as tmp:
        progress_path = Path(tmp) / "progress.json"

        assert mark_lesson_complete(lesson, path=progress_path) is True
        assert mark_lesson_complete(lesson, path=progress_path) is False

        progress = load_progress(progress_path)
        assert progress["completedLessons"] == ["freak-basics/hello-freak"]
        assert "[DONE] 1. hello-freak" in format_progress(path=progress_path)


def test_learn_status_cli_uses_progress_override():
    with tempfile.TemporaryDirectory() as tmp:
        progress_path = Path(tmp) / "progress.json"
        old_progress = os.environ.get("FREAK_ACADEMY_PROGRESS")
        os.environ["FREAK_ACADEMY_PROGRESS"] = str(progress_path)
        try:
            out = io.StringIO()
            with redirect_stdout(out):
                code = main(["learn", "status"])
        finally:
            if old_progress is None:
                os.environ.pop("FREAK_ACADEMY_PROGRESS", None)
            else:
                os.environ["FREAK_ACADEMY_PROGRESS"] = old_progress

    assert code == 0
    assert "FREAK Academy Progress" in out.getvalue()
    assert "[TODO] 1. hello-freak" in out.getvalue()


def test_learn_start_collects_submission_and_records_progress():
    captured: dict[str, str] = {}

    def fake_evaluate(exercise, path):
        captured["exercise"] = exercise["id"]
        captured["source"] = Path(path).read_text(encoding="utf-8")
        return [
            {
                "id": "parses",
                "kind": "parses",
                "passed": True,
                "message": "source parses",
            }
        ]

    with tempfile.TemporaryDirectory() as tmp:
        progress_path = Path(tmp) / "progress.json"
        old_progress = os.environ.get("FREAK_ACADEMY_PROGRESS")
        os.environ["FREAK_ACADEMY_PROGRESS"] = str(progress_path)
        try:
            out = io.StringIO()
            stdin = io.StringIO('\ufeffsay "Hello, FREAK Academy!"\n.submit\n')
            with (
                redirect_stdout(out),
                patch("sys.stdin", stdin),
                patch("freakc.__main__._academy_evaluate_submission", side_effect=fake_evaluate),
            ):
                code = main(["learn", "start", "hello-freak"])
        finally:
            if old_progress is None:
                os.environ.pop("FREAK_ACADEMY_PROGRESS", None)
            else:
                os.environ["FREAK_ACADEMY_PROGRESS"] = old_progress

        progress = load_progress(progress_path)

    assert code == 0
    assert captured["exercise"] == "hello-exercise"
    assert captured["source"] == 'say "Hello, FREAK Academy!"\n'
    assert progress["completedLessons"] == ["freak-basics/hello-freak"]
    assert "Starting: Hello, FREAK" in out.getvalue()
    assert "Progress saved." in out.getvalue()


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"{name}: OK")
