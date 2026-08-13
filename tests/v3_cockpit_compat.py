#!/usr/bin/env python3
"""Prove the source-only COCKPIT façade against an exact V3 compiler."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import v3_byte_buffer_foundation as byte_foundation
import v3_word_foundation as foundation


SOURCE_ORDER = (
    "containers.fk",
    "layout.fk",
    "theme.fk",
    "widgets.fk",
    "ui.fk",
)

PURE_PROGRAM = r'''
task main() {
    pilot values = cockpit_values_new()
    cockpit_values_push_int(values, 7)
    cockpit_values_push_int(values, 0 - 2)
    cockpit_values_push_bool(values, true)
    say cockpit_values_length(values)
    say cockpit_values_get_int(values, 0)
    say cockpit_values_get_int(values, 1)
    say cockpit_values_get_bool(values, 2)

    pilot theme = cockpit_theme_dark()
    say cockpit_theme_get(theme, cockpit_theme_font_size)
    say cockpit_color_r(cockpit_theme_get(theme, cockpit_theme_bg))

    pilot layout: ByteBuffer = ByteBuffer::with_capacity(cockpit_layout_capacity())
    say layout.capacity()
    cockpit_layout_begin_frame(layout, 300, 200, 10, 5)
    cockpit_layout_allocate(layout, 50, 20)
    say cockpit_layout_last_x()
    say cockpit_layout_last_y()
    cockpit_layout_begin_row(layout, 30, 3)
    cockpit_layout_allocate(layout, 40, 10)
    say cockpit_layout_last_x()
    cockpit_layout_allocate(layout, 20, 12)
    say cockpit_layout_last_x()
    cockpit_layout_end(layout)
    cockpit_layout_allocate(layout, 60, 15)
    say cockpit_layout_last_x()
    say cockpit_layout_last_y()
    say cockpit_layout_depth(layout)
    say cockpit_layout_status(layout)
    say layout.capacity()

    cockpit_layout_release(layout)
    cockpit_theme_release(theme)
    cockpit_values_release(values)
}
'''

PURE_STDOUT = ["3", "7", "-2", "true", "14", "22", "2560", "10", "10", "10", "53", "10", "52", "1", "0", "2560"]


def run(
    command: list[str], cwd: Path, *, timeout: int = 300
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def aggregate(paths: list[Path], destination: Path, suffix: str = "") -> Path:
    payload = b"\n".join(path.read_bytes() for path in paths)
    if suffix:
        payload += b"\n" + suffix.encode("utf-8")
    destination.write_bytes(payload)
    return destination


def package_artifacts(package: Path) -> set[Path]:
    return {
        path
        for path in package.rglob("*")
        if path.is_file() and path.suffix in {".c", ".ll", ".obj", ".exe"}
    }


def assert_static_contract(package: Path) -> None:
    source_paths = [package / "src" / name for name in SOURCE_ORDER]
    example_paths = sorted((package / "examples").glob("*.fk"))
    joined = "\n".join(
        path.read_text(encoding="utf-8") for path in source_paths + example_paths
    )
    assert "Squad" not in joined
    assert "Window::" not in joined
    assert "Window.poll" not in joined
    assert not re.search(r"\bshape\s+[A-Za-z_]", joined)
    assert "ui::poll_events" in joined
    assert "ui::event_kind" in joined
    assert "ui::event_mouse_x" in joined
    assert "ui::event_character" in joined
    assert joined.count("ByteBuffer::with_capacity") == len(example_paths)
    begin_frame = (package / "src" / "ui.fk").read_text(encoding="utf-8")
    assert "ByteBuffer::" not in begin_frame
    assert "array_new(" not in begin_frame
    for example in example_paths:
        text = example.read_text(encoding="utf-8")
        assert re.search(r"repeat\s+[0-9]+\s+times", text), example
        first_frame_loop = re.search(r"repeat\s+[0-9]+\s+times", text)
        assert first_frame_loop is not None
        assert text.count("cockpit_ui_open(") == 1, example
        assert text.index("cockpit_ui_open(") < first_frame_loop.start(), example
        assert text.index("ByteBuffer::with_capacity") < first_frame_loop.start(), example
        assert "cockpit_ui_close(window)" in text, example
        assert "cockpit_layout_release(layout)" in text, example
        assert "cockpit_theme_release(theme)" in text, example
    manifest = (package / "hangar.toml").read_text(encoding="utf-8")
    assert 'edition = "alternative-3"' in manifest
    assert "source-only" in manifest.lower()


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    package = repo / "packages" / "cockpit"
    runtime = repo / "freakc" / "runtime"
    compiler = (
        os.environ.get("FREAK_CLANG")
        or shutil.which("gcc")
        or shutil.which("clang")
        or shutil.which("cc")
    )
    assert compiler, "a C/LLVM compiler is required"
    assert_static_contract(package)
    artifacts_before = package_artifacts(package)
    source_paths = [package / "src" / name for name in SOURCE_ORDER]

    with tempfile.TemporaryDirectory(prefix="freak-v3-cockpit-") as temporary:
        root = Path(temporary)
        freak = foundation.build_fresh_cli(
            clang=compiler, repo=repo, root=root, runtime_root=runtime
        )

        pure_source = aggregate(
            source_paths[:3], root / "cockpit_pure.fk", PURE_PROGRAM
        )
        for backend in ("c", "llvm"):
            generated, generated_text = foundation.transpile(
                freak=freak, repo=repo, source=pure_source, backend=backend
            )
            assert "freak_byte_buffer_" in generated_text or "@freak_llvm_byte_buffer_" in generated_text
            binary = root / f"cockpit_pure_{backend}{'.exe' if sys.platform == 'win32' else ''}"
            byte_foundation.compile_generated(
                compiler, repo, runtime, generated, binary, backend
            )
            executed = run([str(binary)], root)
            assert executed.returncode == 0, executed.stdout + executed.stderr
            assert executed.stdout.strip().splitlines() == PURE_STDOUT, (
                backend,
                executed.stdout,
            )
            assert "ownership audit found" not in executed.stderr, executed.stderr
            stats = foundation.parse_runtime_stats(executed.stderr)["counters"]
            assert stats["byte_buffer_creations"] == 1, stats
            assert stats["byte_buffer_allocations"] == 1, stats
            assert stats["byte_buffer_growths"] == 0, stats
            assert stats["byte_buffer_releases"] == 1, stats

        for example in ("smoke.fk", "showcase.fk", "calculator.fk"):
            aggregate_source = aggregate(
                source_paths + [package / "examples" / example],
                root / f"cockpit_{example}",
            )
            checked = run([str(freak), "check", str(aggregate_source)], repo)
            assert checked.returncode == 0, checked.stdout + checked.stderr
            for backend in ("c", "llvm"):
                generated, generated_text = foundation.transpile(
                    freak=freak,
                    repo=repo,
                    source=aggregate_source,
                    backend=backend,
                )
                prefix = "freak_ui_" if backend == "c" else "@freak_llvm_ui_"
                for operation in (
                    "create_window",
                    "poll_events",
                    "event_kind",
                    "begin_frame",
                    "clear",
                    "fill_rect",
                    "draw_text",
                    "end_frame",
                    "destroy_window",
                ):
                    assert prefix + operation in generated_text, (example, backend, operation)
                assert generated.is_file()

    assert package_artifacts(package) == artifacts_before
    print("v3 COCKPIT compatibility tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
