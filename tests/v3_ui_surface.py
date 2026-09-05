#!/usr/bin/env python3
"""Prove the deliberately narrow frozen-V3 std::ui surface."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


PROGRAM = """task main() {
    pilot window = Window { handle: 0, width: 0, height: 0 }
    pilot canvas = Canvas::from_window(window)
    pilot rect = Rect { x: 1.5, y: 2.5, w: 3.5, h: 4.5 }
    pilot from = Vec2 { x: 1.5, y: 2.5 }
    pilot to = Vec2 { x: 3.5, y: 4.5 }
    pilot color = Color::rgba(1, 2, 3, 4)
    canvas.fill_rect(rect, color)
    canvas.stroke_rect(rect, color, 2)
    canvas.fill_circle(from, 3, color)
    canvas.draw_line(from, to, color, 2)
    ui::poll_events(0)
    say "ui floor"
}
"""


def run(command: list[str], cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """
    Execute a command and capture its standard output and error streams.

    Parameters:
        command (list[str]): Command and arguments to execute.
        cwd (Path): Working directory for the subprocess.
        env (dict[str, str]): Environment variables for the subprocess.

    Returns:
        subprocess.CompletedProcess[str]: The completed process result, including its exit status and captured text streams.
    """
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        check=False,
    )


def output(result: subprocess.CompletedProcess[str]) -> str:
    """Combine a completed subprocess's standard output and standard error.

    Parameters:
        result (subprocess.CompletedProcess[str]): The completed subprocess result.

    Returns:
        str: The concatenated standard output and standard error.
    """
    return result.stdout + result.stderr


def main() -> int:
    """
    Validate the frozen V3 `std::ui` surface and generated backend output for a Freak executable.

    Returns:
        int: Zero after all validations pass.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("freak", type=Path)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parent.parent
    freak = args.freak.resolve()
    assert freak.is_file(), freak
    std_ui_path = repo / "std" / "ui" / "window.fk"
    std_ui = std_ui_path.read_text(encoding="utf-8")
    assert "task poll(self)" not in std_ui
    assert "Squad" not in std_ui
    assert "ui::poll_events(handle)" in std_ui
    assert "Win32/GDI" in std_ui
    for lowered in (
        "rect.x.to_int()",
        "rect.y.to_int()",
        "rect.w.to_int()",
        "rect.h.to_int()",
        "center.x.to_int()",
        "center.y.to_int()",
        "from.x.to_int()",
        "from.y.to_int()",
        "to.x.to_int()",
        "to.y.to_int()",
    ):
        assert lowered in std_ui, lowered

    readme = (repo / "README.md").read_text(encoding="utf-8")
    cockpit_readme = (repo / "packages" / "cockpit" / "README.md").read_text(
        encoding="utf-8"
    )
    assert "COCKPIT — Maverick Source Preview" in readme
    assert "not a supported package on the frozen V3 compiler" in readme
    assert "not a V3 release package" in cockpit_readme

    env = os.environ.copy()
    env.pop("FREAK_HOME", None)
    env["NO_COLOR"] = "1"
    executable_suffix = ".exe" if sys.platform == "win32" else ""

    with tempfile.TemporaryDirectory(prefix="freak-v3-ui-surface-") as temporary:
        root = Path(temporary)
        source = root / "ui_floor_combined.fk"
        source.write_text(std_ui + "\n" + PROGRAM, encoding="utf-8")

        checked = run([str(freak), "check", str(source)], root, env)
        assert checked.returncode == 0, output(checked)

        generated_by_backend: dict[str, str] = {}
        for backend, flag, suffix in (
            ("c", "--c", ".c"),
            ("llvm", "--llvm", ".ll"),
        ):
            emitted = run([str(freak), "transpile", str(source), flag], root, env)
            assert emitted.returncode == 0, f"{backend} std::ui transpile failed\n{output(emitted)}"
            generated_path = Path(str(source) + suffix)
            assert generated_path.is_file(), generated_path
            generated_by_backend[backend] = generated_path.read_text(encoding="utf-8")

        generated_c = generated_by_backend["c"]
        assert generated_c.count("((int64_t)(") >= 10
        for call in ("fill_rect", "stroke_rect", "fill_circle", "draw_line"):
            assert f"freak_ui_{call}" in generated_c

        generated_llvm = generated_by_backend["llvm"]
        assert generated_llvm.count("call i64 @freak_llvm_num_to_int") >= 10
        ten_i64 = r"i64 [^,\)]+(?:, i64 [^,\)]+){9}"
        assert re.search(
            r"call void @freak_llvm_ui_stroke_rect\(" + ten_i64 + r"\)",
            generated_llvm,
        )
        assert re.search(
            r"call void @freak_llvm_ui_draw_line\(" + ten_i64 + r"\)",
            generated_llvm,
        )

        if sys.platform == "win32":
            imported_source = root / "ui_floor.fk"
            imported_source.write_text(
                "use std::ui::{Window, Canvas, Rect, Vec2, Color}\n\n" + PROGRAM,
                encoding="utf-8",
            )
            built = run(
                [str(freak), "build", str(imported_source), "--llvm"], root, env
            )
            assert built.returncode == 0, output(built)
            binary = imported_source.with_suffix(executable_suffix)
            assert binary.is_file(), binary
            executed = run([str(binary)], root, env)
            assert executed.returncode == 0, output(executed)
            assert executed.stderr == "", executed.stderr
            assert executed.stdout.replace("\r\n", "\n") == "ui floor\n", executed.stdout

    print("V3 std::ui truthful surface: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
