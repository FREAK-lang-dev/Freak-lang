#!/usr/bin/env python3
"""Prove the source-only COCKPIT façade against an exact V3 compiler."""

from __future__ import annotations

import os
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import time
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

FAKE_UI = r'''
pilot fake_poll_count = 0
task fake_ui_create_window(title: word, width: int, height: int, resizable: int) -> int { give back 1 }
task fake_ui_destroy_window(handle: int) -> void {}
task fake_ui_poll_events(handle: int) -> int { give back fake_poll_count }
task fake_ui_event_kind(index: int) -> int { give back 0 }
task fake_ui_event_key(index: int) -> int { give back 0 }
task fake_ui_event_character(index: int) -> int { give back 0 }
task fake_ui_event_button(index: int) -> int { give back 0 }
task fake_ui_event_pressed(index: int) -> int { give back 0 }
task fake_ui_event_mouse_x(index: int) -> int { give back 0 }
task fake_ui_event_mouse_y(index: int) -> int { give back 0 }
task fake_ui_event_scroll_dy(index: int) -> int { give back 0 }
task fake_ui_event_gained(index: int) -> int { give back 0 }
task fake_ui_begin_frame(handle: int) -> void {}
task fake_ui_end_frame(handle: int) -> void {}
task fake_ui_get_width(handle: int) -> int { give back 320 }
task fake_ui_get_height(handle: int) -> int { give back 240 }
task fake_ui_set_clip(handle: int, x: int, y: int, width: int, height: int) -> void {}
task fake_ui_reset_clip(handle: int) -> void {}
task fake_ui_clear(handle: int, r: int, g: int, b: int, a: int) -> void {}
task fake_ui_fill_rect(handle: int, x: int, y: int, width: int, height: int, r: int, g: int, b: int, a: int) -> void {}
task fake_ui_stroke_rect(handle: int, x: int, y: int, width: int, height: int, r: int, g: int, b: int, a: int, thickness: int) -> void {}
task fake_ui_draw_text(handle: int, text: word, x: int, y: int, r: int, g: int, b: int, size: int, bold: bool, italic: bool) -> int { give back text.length() * 7 }
task fake_ui_measure_text(text: word, size: int, bold: int, italic: int) -> int { give back text.length() * 7 }
'''

REPLAY_PROGRAM = r'''
task replay_focus_order(window: int, layout: ByteBuffer, theme: int) -> void {
    pilot previous = 0
    repeat 2 times {
        cockpit_ui_focus_input(previous)
        cockpit_ui_begin_events()
        cockpit_layout_begin_frame(layout, 200, 200, 0, 0)
        cockpit_ui_feed_event(3, 0, 120, 0, 0, 0, 0, 0)
        pilot target_y = 45
        if previous == 1 { target_y = 10 }
        replay_click(10, target_y)
        cockpit_ui_feed_event(3, 0, 121, 0, 0, 0, 0, 0)
        pilot first = cockpit_widget_input(window, layout, theme, "A", 100)
        pilot second = cockpit_widget_input(window, layout, theme, "B", 100)
        if previous == 0 {
            if first != "Ax" or second != "By" { cockpit_fail("focus first to second ordering") }
        } else {
            if first != "Ay" or second != "Bx" { cockpit_fail("focus second to first ordering") }
        }
        if cockpit_ui_focused_input != 1 - previous { cockpit_fail("final focus order") }
        cockpit_ui_begin_events()
        cockpit_layout_begin_frame(layout, 200, 200, 0, 0)
        cockpit_ui_feed_event(2, 41, 0, 0, 1, 0, 0, 0)
        first = cockpit_widget_input(window, layout, theme, first, 100)
        second = cockpit_widget_input(window, layout, theme, second, 100)
        if previous == 0 {
            if first != "Ax" or second != "B" { cockpit_fail("persisted second focus") }
        } else {
            if first != "A" or second != "Bx" { cockpit_fail("persisted first focus") }
        }
        previous += 1
    }
    cockpit_ui_focus_input(0)
    cockpit_ui_begin_events()
    cockpit_layout_begin_frame(layout, 200, 200, 0, 0)
    replay_click(10, 45)
    cockpit_ui_feed_event(3, 0, 120, 0, 0, 0, 0, 0)
    replay_click(10, 10)
    cockpit_ui_feed_event(3, 0, 121, 0, 0, 0, 0, 0)
    replay_click(150, 150)
    cockpit_ui_feed_event(3, 0, 122, 0, 0, 0, 0, 0)
    if cockpit_widget_input(window, layout, theme, "A", 100) != "Ay" { cockpit_fail("multiple focus clicks first") }
    if cockpit_widget_input(window, layout, theme, "B", 100) != "Bx" { cockpit_fail("multiple focus clicks second") }
    if cockpit_ui_focused_input != 0 - 1 { cockpit_fail("outside click clears focus") }
    cockpit_ui_focus_input(0)
    cockpit_ui_begin_events()
    cockpit_layout_begin_frame(layout, 200, 200, 0, 0)
    replay_click(10, 45)
    cockpit_ui_feed_event(3, 0, 120, 0, 0, 0, 0, 0)
    cockpit_clip_push(window, 0, 0, 100, 32)
    if cockpit_widget_input(window, layout, theme, "A", 100) != "A" { cockpit_fail("clipped click retained old focus") }
    if cockpit_widget_input(window, layout, theme, "B", 100) != "B" { cockpit_fail("clipped input received text") }
    cockpit_clip_pop(window)
    cockpit_ui_focus_input(0)
    cockpit_ui_begin_events()
    cockpit_layout_begin_frame(layout, 200, 200, 0, 0)
    replay_click(10, 10)
    cockpit_ui_feed_event(3, 0, 120, 0, 0, 0, 0, 0)
    cockpit_modal_open()
    if not cockpit_modal_begin(window, layout, theme, 320, 240) { cockpit_fail("modal begin failed") }
    if cockpit_widget_input(window, layout, theme, "M", 100) != "M" { cockpit_fail("modal inherited opening edits") }
    cockpit_modal_end(window, layout)
    cockpit_modal_close()
}

task replay_failed_panels(window: int, layout: ByteBuffer, theme: int) -> void {
    pilot wrapper = 0
    repeat 3 times {
        cockpit_layout_begin_frame(layout, 200, 200, 0, 0)
        repeat 31 times { cockpit_layout_append_context(layout, 1, 2, 100, 100, 0, 3) }
        pilot snapshot = layout.slice(0, layout.length())
        cockpit_clip_push(window, 2, 3, 120, 130)
        pilot clip_depth = cockpit_ui_clip_depth
        if wrapper == 0 {
            cockpit_panel_begin(window, layout, theme, 90, 80)
            cockpit_panel_end(window, layout)
        } else if wrapper == 1 {
            if cockpit_scroll_begin(window, layout, theme, 90, 80, 400, 17) != 17 { cockpit_fail("failed scroll changed offset") }
            cockpit_scroll_end(window, layout)
        } else {
            cockpit_modal_open()
            if cockpit_modal_begin(window, layout, theme, 90, 80) { cockpit_fail("failed modal reported success") }
            cockpit_modal_end(window, layout)
            if cockpit_ui_modal_scope { cockpit_fail("failed modal changed scope") }
            cockpit_modal_close()
        }
        if cockpit_layout_depth(layout) != 32 or cockpit_layout_status(layout) != 2 { cockpit_fail("failed panel unwound parent") }
        if cockpit_ui_clip_depth != clip_depth { cockpit_fail("failed panel changed clip") }
        layout.seek(0)
        repeat snapshot.length() times {
            if layout.read_byte() != snapshot.read_byte() { cockpit_fail("failed panel mutated parent") }
        }
        snapshot.release()
        cockpit_clip_pop(window)
        wrapper += 1
    }
    cockpit_layout_begin_frame(layout, 200, 200, 0, 0)
}

task replay_click(x: int, y: int) -> void {
    cockpit_ui_feed_event(4, 0, 0, 1, 0, x, y, 0)
    cockpit_ui_feed_event(4, 0, 0, 1, 1, x, y, 0)
}
task main() {
    pilot window = cockpit_ui_open("Replay", 320, 240, true)
    pilot theme = cockpit_theme_dark()
    pilot layout = ByteBuffer::with_capacity(cockpit_layout_capacity())
    replay_focus_order(window, layout, theme)
    replay_failed_panels(window, layout, theme)
    cockpit_ui_focus_input(0 - 1)
    fake_poll_count = 0 - 1
    cockpit_ui_begin_frame(window, layout, theme)
    say cockpit_ui_should_close()
    fake_poll_count = 0
    cockpit_ui_begin_events()
    cockpit_ui_feed_event(3, 0, 97, 0, 0, 0, 0, 0)
    cockpit_ui_feed_event(3, 0, 98, 0, 0, 0, 0, 0)
    say cockpit_ui_edit_text("x")
    cockpit_ui_begin_events()
    cockpit_ui_feed_event(3, 0, 97, 0, 0, 0, 0, 0)
    cockpit_ui_feed_event(2, 41, 0, 0, 1, 0, 0, 0)
    say cockpit_ui_edit_text("x")
    say cockpit_ui_delete_scalar("é🙂")
    say cockpit_ui_delete_scalar("é").length()
    cockpit_ui_begin_events()
    cockpit_layout_begin_frame(layout, 200, 200, 0, 0)
    replay_click(10, 10)
    cockpit_ui_feed_event(3, 0, 120, 0, 0, 0, 0, 0)
    cockpit_ui_feed_event(3, 0, 121, 0, 0, 0, 0, 0)
    say cockpit_widget_input(window, layout, theme, "", 100)
    say cockpit_widget_input(window, layout, theme, "unfocused", 100)

    cockpit_layout_begin_frame(layout, 300, 200, 10, 5)
    cockpit_layout_allocate(layout, 50, 20)
    cockpit_layout_begin_row(layout, 30, 3)
    cockpit_layout_allocate(layout, 40, 10)
    say cockpit_layout_last_y()
    cockpit_layout_end(layout)
    cockpit_layout_begin_frame(layout, 50, 80, 0, 0)
    cockpit_ui_begin_events()
    replay_click(75, 10)
    say cockpit_widget_button(window, layout, theme, "Wide", 100)
    say cockpit_layout_last_width()

    cockpit_layout_begin_frame(layout, 200, 100, 0, 0)
    cockpit_ui_begin_events()
    replay_click(99, 10)
    cockpit_ui_feed_event(4, 0, 0, 1, 0, 99, 10, 0)
    say cockpit_widget_slider(window, layout, theme, 0, 0, 100, 100)
    cockpit_ui_begin_events()
    cockpit_layout_begin_frame(layout, 200, 200, 0, 0)
    cockpit_ui_feed_event(4, 0, 0, 0, 0, 20, 20, 0)
    cockpit_ui_feed_event(5, 0, 0, 0, 0, 20, 20, 0 - 1)
    say cockpit_scroll_begin(window, layout, theme, 100, 80, 300, 0)
    cockpit_widget_label(window, layout, theme, "scrolled")
    cockpit_scroll_end(window, layout)
    say cockpit_ui_clip_depth
    cockpit_clip_push(window, 10, 10, 100, 100)
    cockpit_clip_push(window, 50, 0, 100, 100)
    say cockpit_clip_contains(20, 20)
    say cockpit_clip_contains(60, 20)
    cockpit_clip_pop(window)
    say cockpit_clip_contains(20, 20)
    cockpit_clip_pop(window)

    cockpit_modal_open()
    cockpit_ui_begin_events()
    cockpit_layout_begin_frame(layout, 200, 200, 0, 0)
    replay_click(10, 10)
    say cockpit_widget_button(window, layout, theme, "Blocked", 100)
    say cockpit_modal_begin(window, layout, theme, 200, 100)
    cockpit_widget_label(window, layout, theme, "Modal")
    cockpit_modal_end(window, layout)
    cockpit_modal_close()
    say cockpit_ui_clip_depth
    cockpit_layout_begin_frame(layout, 100, 100, 0, 0)
    repeat 32 times { cockpit_layout_begin_row(layout, 1, 0) }
    say cockpit_layout_depth(layout)
    say cockpit_layout_status(layout)
    cockpit_layout_end(layout)
    say cockpit_layout_depth(layout)
    cockpit_layout_begin_frame(layout, 100, 100, 0, 0)
    say cockpit_layout_status(layout)

    pilot choices = cockpit_words_new()
    cockpit_words_push(choices, "First")
    cockpit_words_push(choices, "Second")
    cockpit_ui_begin_events()
    cockpit_layout_begin_frame(layout, 200, 200, 0, 0)
    replay_click(10, 10)
    say cockpit_widget_dropdown(window, layout, theme, 0, choices)
    cockpit_popup_draw(window)
    cockpit_ui_begin_events()
    replay_click(10, 75)
    cockpit_popup_draw(window)
    cockpit_ui_begin_events()
    cockpit_layout_begin_frame(layout, 200, 200, 0, 0)
    say cockpit_widget_dropdown(window, layout, theme, 0, choices)
    cockpit_widget_tooltip(window, theme, "Tip", 0, 0, 200, 200)
    say cockpit_ui_clip_depth
    repeat 20 times { cockpit_words_push(choices, "More") }
    cockpit_ui_begin_events()
    cockpit_layout_begin_frame(layout, 200, 200, 0, 0)
    replay_click(10, 10)
    cockpit_widget_dropdown(window, layout, theme, 0, choices)
    cockpit_popup_draw(window)
    cockpit_ui_begin_events()
    cockpit_ui_feed_event(5, 0, 0, 0, 0, 10, 25, 0 - 100)
    replay_click(10, 25)
    cockpit_popup_draw(window)
    cockpit_ui_begin_events()
    cockpit_layout_begin_frame(layout, 200, 200, 0, 0)
    say cockpit_widget_dropdown(window, layout, theme, 0, choices)
    cockpit_words_release(choices)
    cockpit_layout_release(layout)
    cockpit_theme_release(theme)
    cockpit_ui_close(window)
}
'''

REPLAY_STDOUT = ["true", "xab", "x", "é", "0", "xy", "unfocused", "35", "false", "50", "100", "24", "0", "false", "true", "true", "false", "true", "0", "32", "2", "32", "0", "0", "1", "0", "15"]

CALCULATOR_HARNESS = r'''
pilot calculator_test_frame = 0
task cockpit_ui_begin_frame(window: int, layout: ByteBuffer, theme: int) -> void {
    calculator_test_frame += 1
    calculator_actual_begin_frame(window, layout, theme)
}
task cockpit_widget_heading(window: int, layout: ByteBuffer, theme: int, text: word) -> void {
    say text
    calculator_actual_heading(window, layout, theme, text)
}
task cockpit_widget_button(window: int, layout: ByteBuffer, theme: int, text: word, width: int) -> bool {
    pilot ignored = calculator_actual_button(window, layout, theme, text, width)
    if calculator_test_frame == 1 { give back text == "8" }
    if calculator_test_frame == 2 { give back text == "/" }
    if calculator_test_frame == 3 { give back text == "0" }
    if calculator_test_frame == 4 or calculator_test_frame == 6 or calculator_test_frame == 11 { give back text == "=" }
    if calculator_test_frame == 5 or calculator_test_frame == 9 { give back text == "+" }
    if calculator_test_frame == 7 { give back text == "C" }
    if calculator_test_frame == 8 { give back text == "2" }
    if calculator_test_frame == 10 { give back text == "3" }
    give back false
}
task cockpit_ui_end_frame(window: int) -> void {
    calculator_actual_end_frame(window)
    if calculator_test_frame >= 12 { cockpit_ui_request_close() }
}
'''


def check_calculator_example(freak: Path, compiler: str, repo: Path, runtime: Path,
                             root: Path, source_paths: list[Path], package: Path) -> None:
    # Drive the actual example's main loop. Only buttons/frame timing and the
    # rendered heading are instrumented; arithmetic/state logic is not copied.
    text = "\n".join(path.read_text(encoding="utf-8") for path in source_paths)
    for original, replacement in (
        ("cockpit_ui_begin_frame", "calculator_actual_begin_frame"),
        ("cockpit_widget_heading", "calculator_actual_heading"),
        ("cockpit_widget_button", "calculator_actual_button"),
        ("cockpit_ui_end_frame", "calculator_actual_end_frame"),
    ):
        assert text.count("task " + original + "(") == 1
        text = text.replace("task " + original + "(", "task " + replacement + "(")
    example = (package / "examples/calculator.fk").read_text(encoding="utf-8")
    source = root / "calculator_interaction.fk"
    source.write_text(FAKE_UI + "\n" + text.replace("ui::", "fake_ui_") + example + CALCULATOR_HARNESS,
                      encoding="utf-8")
    expected = ["0", "8", "8", "0", "Error", "Error", "Error", "0", "2", "2", "3", "5"]
    for backend in ("c", "llvm"):
        generated, _ = foundation.transpile(freak=freak, repo=repo, source=source, backend=backend)
        binary = root / f"calculator_interaction_{backend}{'.exe' if sys.platform == 'win32' else ''}"
        byte_foundation.compile_generated(compiler, repo, runtime, generated, binary, backend)
        executed = run([str(binary)], root, timeout=20)
        assert executed.returncode == 0, (backend, executed.stdout, executed.stderr)
        assert executed.stdout.strip().splitlines() == expected, (backend, executed.stdout)
        assert "ownership audit found" not in executed.stderr, executed.stderr


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


def compile_native_ui(compiler: str, runtime: Path, generated: Path, binary: Path, backend: str) -> None:
    command = [compiler, "-O1", "-DFREAK_HAS_UI", "-DFREAK_WORD_FOUNDATION_AUDIT=1", "-I", str(runtime), str(generated), str(runtime / "freak_runtime.c"), str(runtime / "ui" / "win32_backend.c")]
    if backend == "llvm":
        command.extend(["-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1", str(runtime / "freak_llvm_runtime.c")])
    else:
        command.append("-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1")
    command.extend(["-lws2_32", "-luser32", "-lgdi32", "-lmsimg32", "-o", str(binary)])
    compiled = run(command, binary.parent)
    assert compiled.returncode == 0, compiled.stdout + compiled.stderr


def native_window_close(binary: Path) -> None:
    """Exercise only the visible window owned by this exact child process."""
    import ctypes.wintypes

    wintypes = ctypes.wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.PostMessageW.restype = wintypes.BOOL
    child = subprocess.Popen([str(binary)], cwd=binary.parent, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
    try:
        found = []
        @callback_type
        def inspect_window(hwnd, unused):
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == child.pid and user32.IsWindowVisible(hwnd):
                found.append(hwnd)
            return True
        deadline = time.monotonic() + 10
        while child.poll() is None and not found and time.monotonic() < deadline:
            user32.EnumWindows(inspect_window, 0)
            if not found:
                time.sleep(0.05)
        assert found, f"child {child.pid} never presented a native window"
        # Recheck ownership immediately before sending the close request.
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(found[0], ctypes.byref(pid))
        assert pid.value == child.pid
        assert user32.PostMessageW(found[0], 0x0010, 0, 0), ctypes.get_last_error()
        stdout, stderr = child.communicate(timeout=5)
        assert child.returncode == 0, (child.returncode, stdout, stderr)
        assert "ownership audit found" not in stderr, stderr
    finally:
        if child.poll() is None:
            child.terminate()
            child.communicate(timeout=5)


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
    for example in example_paths:
        text = example.read_text(encoding="utf-8")
        first_frame_loop = re.search(r"repeat\s+(?:[0-9]+\s+times|until\s+cockpit_ui_should_close\(\))", text)
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
    parser = argparse.ArgumentParser()
    parser.add_argument("freak", nargs="?", type=Path)
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--replay-only", action="store_true", help="run package event/layout logic with injected platform calls")
    parser.add_argument("--calculator-only", action="store_true", help="drive the actual calculator example through division error and clear recovery")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    package = repo / "packages" / "cockpit"
    runtime = args.runtime_root.resolve() if args.runtime_root else repo / "freakc" / "runtime"
    compiler = (
        os.environ.get("FREAK_CLANG")
        or shutil.which("clang")
    )
    assert compiler, "a C/LLVM compiler is required"
    assert_static_contract(package)
    artifacts_before = package_artifacts(package)
    source_paths = [package / "src" / name for name in SOURCE_ORDER]

    with tempfile.TemporaryDirectory(prefix="freak-v3-cockpit-") as temporary:
        root = Path(temporary)
        freak = args.freak.resolve() if args.freak else foundation.build_fresh_cli(
            clang=compiler, repo=repo, root=root, runtime_root=runtime
        )

        check_calculator_example(freak, compiler, repo, runtime, root, source_paths, package)
        if args.calculator_only:
            assert package_artifacts(package) == artifacts_before
            print("PASS actual calculator C/LLVM: visible division Error, stable error controls, clear and addition recovery")
            return 0

        replay_source = root / "cockpit_replay.fk"
        replay_source.write_text(FAKE_UI + "\n" + "\n".join(path.read_text(encoding="utf-8").replace("ui::", "fake_ui_") for path in source_paths) + REPLAY_PROGRAM, encoding="utf-8")
        for backend in ("c", "llvm"):
            generated, _ = foundation.transpile(freak=freak, repo=repo, source=replay_source, backend=backend)
            binary = root / f"cockpit_replay_{backend}{'.exe' if sys.platform == 'win32' else ''}"
            byte_foundation.compile_generated(compiler, repo, runtime, generated, binary, backend)
            executed = run([str(binary)], root)
            assert executed.returncode == 0, (backend, executed.stdout, executed.stderr)
            assert executed.stdout.strip().splitlines() == REPLAY_STDOUT, (backend, executed.stdout, executed.stderr)
            assert "ownership audit found" not in executed.stderr, executed.stderr

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

        for example in ("smoke.fk", "showcase.fk", "calculator.fk", "settings.fk"):
            aggregate_source = aggregate(
                source_paths + [package / "examples" / example],
                root / f"cockpit_{example}",
            )
            if args.replay_only:
                aggregate_source.write_text(FAKE_UI + "\n" + aggregate_source.read_text(encoding="utf-8").replace("ui::", "fake_ui_"), encoding="utf-8")
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
                    if not args.replay_only:
                        assert prefix + operation in generated_text, (example, backend, operation)
                assert generated.is_file()
                binary = root / f"{example}_{backend}{'.exe' if sys.platform == 'win32' else ''}"
                if args.replay_only:
                    byte_foundation.compile_generated(compiler, repo, runtime, generated, binary, backend)
                elif sys.platform == "win32":
                    compile_native_ui(compiler, runtime, generated, binary, backend)
                    native_window_close(binary)

    assert package_artifacts(package) == artifacts_before
    print("v3 COCKPIT injected C/LLVM replay and example linking passed (native UI not requested)" if args.replay_only else "v3 COCKPIT compatibility tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
