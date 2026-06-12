from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from freakc.__main__ import main
from freakc.academy import first_exercise, format_course_listing, load_course, load_lesson


def test_seed_course_loads():
    course = load_course("freak-basics")

    assert course["compilerTrack"] == "v3"
    assert course["lessons"] == ["hello-freak"]


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


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"{name}: OK")
