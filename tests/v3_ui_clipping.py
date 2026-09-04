#!/usr/bin/env python3
"""Verify V3 clipping lowering and Win32 software/GDI pixel behavior."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import v3_word_foundation as foundation

PROGRAM = '''task main() {
    pilot handle = ui::create_window("FREAK clipping lowering", 64, 64, 1)
    ui::set_clip(handle, 10, 10, 20, 20)
    ui::clear(handle, 255, 0, 0, 255)
    ui::reset_clip(handle)
    ui::destroy_window(handle)
    say "clip-ok"
}
'''

PROBE = r'''#include "ui/win32_backend.c"
#include <assert.h>

static HWND test_window;
static int64_t handle;
static int bridge;

static void expect(int value, const char* why) {
    if (!value) { fprintf(stderr, "clip probe: %s\n", why); exit(2); }
}
static BOOL CALLBACK find_own_window(HWND hwnd, LPARAM unused) {
    (void)unused;
    DWORD pid = 0;
    GetWindowThreadProcessId(hwnd, &pid);
    char name[64];
    GetClassNameA(hwnd, name, sizeof(name));
    if (pid == GetCurrentProcessId() && strcmp(name, "FreakUIClass") == 0) {
        test_window = hwnd;
        return FALSE;
    }
    return TRUE;
}
static void locate_window(void) {
    test_window = NULL;
    EnumWindows(find_own_window, 0);
    expect(test_window != NULL, "find window belonging to probe PID");
    /* A disabled private popup avoids desktop minimum-track dimensions and
       cannot take keyboard focus when begin_frame exercises its show path. */
    SetWindowLongPtrA(test_window, GWL_STYLE, WS_POPUP | WS_DISABLED);
    SetWindowPos(test_window, NULL, -32000, -32000, 0, 0,
                 SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED);
}
static void clip(int64_t h, int64_t x, int64_t y, int64_t w, int64_t height) {
    if (bridge) freak_llvm_ui_set_clip(h, x, y, w, height);
    else freak_ui_set_clip(h, x, y, w, height);
}
static void reset(int64_t h) {
    if (bridge) freak_llvm_ui_reset_clip(h);
    else freak_ui_reset_clip(h);
}
static void black(void) { reset(handle); freak_ui_clear(handle, 0, 0, 0, 255); }
static uint32_t pixel(int x, int y) {
    GdiFlush();
    return g_win->pixels[(size_t)y * g_win->width + x] & 0xffffff;
}
static void rect_pixels(int left, int top, int right, int bottom) {
    for (int y = 0; y < g_win->height; ++y) {
        for (int x = 0; x < g_win->width; ++x) {
            uint32_t wanted = x >= left && x < right && y >= top && y < bottom ? 0xffffff : 0;
            expect(pixel(x, y) == wanted, "exact rectangle pixels");
        }
    }
}
static void draw(int kind) {
    if (kind == 0) freak_ui_clear(handle, 255, 255, 255, 255);
    if (kind == 1) freak_ui_fill_rect(handle, -5, -5, 100, 100, 255, 255, 255, 255);
    if (kind == 2) freak_ui_stroke_rect(handle, 8, 8, 24, 24, 255, 255, 255, 255, 4);
    if (kind == 3) freak_ui_fill_circle(handle, 20, 20, 16, 255, 255, 255, 255);
    if (kind == 4) freak_ui_draw_line(handle, 0, 0, 60, 60, 255, 255, 255, 255, 3);
    if (kind == 5) freak_ui_draw_text(handle, "MMMMMMMM", 0, 5, 255, 255, 255, 30, 0, 0);
}
static void primitive_pixels(void) {
    uint32_t baseline[64 * 64];
    expect(g_win->width == 64 && g_win->height == 64, "initial client size");
    for (int kind = 0; kind < 6; ++kind) {
        black(); draw(kind); GdiFlush();
        memcpy(baseline, g_win->pixels, sizeof(baseline));
        black(); clip(handle, 10, 10, 20, 20); draw(kind);
        int inside_ink = 0, outside_ink = 0;
        for (int y = 0; y < 64; ++y) {
            for (int x = 0; x < 64; ++x) {
                int inside = x >= 10 && x < 30 && y >= 10 && y < 30;
                uint32_t original = baseline[y * 64 + x] & 0xffffff;
                expect(pixel(x, y) == (inside ? original : 0), "primitive clipped pixel parity");
                if (original) { if (inside) ++inside_ink; else ++outside_ink; }
            }
        }
        expect(inside_ink > 0 && outside_ink > 0, "clipping oracle has ink on both sides");
    }
}
static void resize_client(int width, int height) {
    RECT rect = {0, 0, width, height};
    expect(AdjustWindowRect(&rect, (DWORD)GetWindowLongPtrA(test_window, GWL_STYLE), FALSE),
           "adjust test client bounds");
    expect(SetWindowPos(test_window, NULL, 0, 0, rect.right - rect.left, rect.bottom - rect.top,
                        SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE), "resize test window");
    expect(freak_ui_get_width(handle) == width && freak_ui_get_height(handle) == height,
           "resized backing dimensions");
}
int main(int argc, char** argv) {
    bridge = argc > 1;
    (void)argv;
    handle = freak_ui_create_window("FREAK clipping probe", 64, 64, 1);
    expect(handle > 0, "create hidden native window");
    locate_window();
    resize_client(64, 64); /* OS creation may enforce its minimum track width. */
    expect(freak_ui_create_window("second", 64, 64, 1) == 0, "reject second live singleton");
    primitive_pixels();
    black(); clip(handle, -10, -10, 20, 20); draw(0); rect_pixels(0, 0, 10, 10);
    black(); clip(handle, INT64_MAX, INT64_MAX, INT64_MAX, INT64_MAX); draw(0); rect_pixels(0, 0, 0, 0);
    black(); clip(handle, INT64_MIN, INT64_MIN, INT64_MAX, INT64_MAX); draw(0); rect_pixels(0, 0, 0, 0);
    black(); clip(handle, -1, -1, INT64_MAX, INT64_MAX); draw(0); rect_pixels(0, 0, 64, 64);
    black(); clip(handle, 0, 0, 0, 20); draw(0); rect_pixels(0, 0, 0, 0);
    black(); clip(handle, 0, 0, 20, INT64_MIN); draw(0); rect_pixels(0, 0, 0, 0);
    black(); clip(handle, 10, 10, 20, 20);
    clip(-1, 0, 0, 64, 64); reset(0); freak_ui_begin_frame(INT64_MAX);
    draw(0); rect_pixels(10, 10, 30, 30);
    black(); clip(handle, 10, 10, 20, 20); clip(handle, 40, 40, 10, 10);
    draw(0); rect_pixels(40, 40, 50, 50); /* replacement, not implicit nesting */
    black(); clip(handle, 10, 10, 20, 20); reset(handle); draw(0); rect_pixels(0, 0, 64, 64);
    black(); clip(handle, 10, 10, 20, 20); freak_ui_begin_frame(handle);
    draw(0); rect_pixels(0, 0, 64, 64); ShowWindow(test_window, SW_HIDE);

    clip(handle, 8, 8, 32, 32);
    resize_client(16, 16);
    memset(g_win->pixels, 0, (size_t)g_win->width * g_win->height * 4);
    draw(0); rect_pixels(8, 8, 16, 16);
    resize_client(48, 48);
    memset(g_win->pixels, 0, (size_t)g_win->width * g_win->height * 4);
    draw(0); rect_pixels(8, 8, 40, 40);
    black(); clip(handle, 8, 8, 32, 32);
    freak_ui_draw_text(handle, "MMMMMMMM", 0, 5, 255, 255, 255, 30, 0, 0);
    int ink = 0;
    for (int y = 0; y < 48; ++y) for (int x = 0; x < 48; ++x) {
        if (x < 8 || x >= 40 || y < 8 || y >= 40) expect(pixel(x, y) == 0, "resized GDI clip");
        else if (pixel(x, y)) ++ink;
    }
    expect(ink > 0, "resized text still draws");
    DWORD objects = GetGuiResources(GetCurrentProcess(), GR_GDIOBJECTS);
    for (int i = 0; i < 40; ++i) { resize_client(32 + i % 2, 32); clip(handle, 1, 1, 10, 10); reset(handle); }
    expect(GetGuiResources(GetCurrentProcess(), GR_GDIOBJECTS) == objects, "resize/clip GDI objects do not grow");
    int64_t stale = handle;
    freak_ui_destroy_window(handle);
    clip(stale, 1, 1, 2, 2); reset(stale);
    handle = freak_ui_create_window("FREAK clipping replacement", 64, 64, 1);
    expect(handle > stale, "opaque handle never reused"); locate_window(); resize_client(64, 64);
    black(); clip(handle, 10, 10, 20, 20); reset(stale); clip(stale, 0, 0, 64, 64);
    freak_ui_destroy_window(stale); draw(0); rect_pixels(10, 10, 30, 30);
    expect(freak_ui_poll_events(handle) >= 0, "old window does not leave a quit for replacement");
    freak_ui_destroy_window(handle);
    g_last_handle = INT64_MAX;
    expect(freak_ui_create_window("exhausted", 64, 64, 1) == 0, "handle exhaustion fails without reuse");
    puts("clip-pixels-ok");
    return 0;
}
'''


def run(command: list[str], cwd: Path, timeout: int = 240) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("freak", type=Path, nargs="?")
    parser.add_argument("--runtime-root", type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    runtime = args.runtime_root.resolve() if args.runtime_root else repo / "freakc/runtime"
    clang = os.environ.get("FREAK_CLANG") or shutil.which("clang")
    assert clang, "Clang is required"
    with tempfile.TemporaryDirectory(prefix="freak-v3-clip-") as temporary:
        root = Path(temporary)
        freak = args.freak.resolve() if args.freak else foundation.build_fresh_cli(
            clang=clang, repo=repo, root=root, runtime_root=runtime)
        shutil.copytree(runtime, root / "runtime")
        shutil.copytree(repo / "std", root / "std")
        os.environ["FREAK_HOME"] = str(root)
        os.environ["FREAK_CLANG"] = clang
        print(f"UI clipping CLI: {freak}", flush=True)
        print(f"UI clipping runtime: {runtime}", flush=True)
        for backend in ("c", "llvm"):
            source = root / f"clip_{backend}.fk"
            source.write_text(PROGRAM, encoding="utf-8")
            generated, text = foundation.transpile(freak=freak, repo=repo, source=source, backend=backend)
            prefix = "freak_ui_" if backend == "c" else "@freak_llvm_ui_"
            for operation in ("set_clip", "reset_clip"):
                assert prefix + operation in text, (backend, operation)
            if sys.platform == "win32":
                binary = root / f"clip_{backend}.exe"
                command = [clang, "-O1", "-DFREAK_HAS_UI=1", str(generated),
                           str(runtime / "freak_runtime.c"), str(runtime / "ui/win32_backend.c"),
                           "-I", str(runtime), "-o", str(binary), "-lws2_32", "-lgdi32", "-luser32"]
                if backend == "llvm": command.append(str(runtime / "freak_llvm_runtime.c"))
                compiled = run(command, repo)
                assert compiled.returncode == 0, compiled.stdout + compiled.stderr
                executed = run([str(binary)], root, 20)
                assert executed.returncode == 0, executed.stdout + executed.stderr
                assert executed.stdout.strip() == "clip-ok", executed.stdout
        sys.path.insert(0, str(repo))
        from freakc.__main__ import transpile as bootstrap_transpile

        bootstrap_c, diagnostics, uses_ui, has_errors = bootstrap_transpile(
            PROGRAM, root / "bootstrap_clip.fk")
        assert bootstrap_c is not None and not has_errors and uses_ui, diagnostics
        assert "freak_ui_set_clip(" in bootstrap_c and "freak_ui_reset_clip(" in bootstrap_c
        if sys.platform == "win32":
            source = root / "bootstrap_clip.c"
            source.write_text(bootstrap_c, encoding="utf-8")
            binary = root / "bootstrap_clip.exe"
            compiled = run([clang, "-O1", str(source), str(runtime / "freak_runtime.c"),
                            str(runtime / "ui/win32_backend.c"), "-I", str(runtime),
                            "-o", str(binary), "-lws2_32", "-lgdi32", "-luser32"], repo)
            assert compiled.returncode == 0, compiled.stdout + compiled.stderr
            executed = run([str(binary)], root, 20)
            assert executed.returncode == 0 and executed.stdout.strip() == "clip-ok", (
                executed.stdout + executed.stderr)

        # With no UI backend linked, the new mechanisms must remain unavailable,
        # rather than silently succeeding through non-UI LLVM runtime stubs.
        unavailable_source = root / "unavailable_clip.c"
        unavailable_source.write_text('''#include "freak_runtime.h"
int main(void) {
    freak_ui_set_clip(0, 0, 0, 1, 1); freak_ui_reset_clip(0);
    freak_llvm_ui_set_clip(0, 0, 0, 1, 1); freak_llvm_ui_reset_clip(0);
    return 0;
}
''', encoding="utf-8")
        unavailable = run([clang, str(unavailable_source), str(runtime / "freak_runtime.c"),
                           str(runtime / "freak_llvm_runtime.c"), "-I", str(runtime),
                           "-o", str(root / "unavailable_clip"),
                           *( ["-lws2_32"] if sys.platform == "win32" else ["-lm"] )], repo)
        assert unavailable.returncode != 0, unavailable.stdout
        for symbol in ("freak_ui_set_clip", "freak_ui_reset_clip",
                       "freak_llvm_ui_set_clip", "freak_llvm_ui_reset_clip"):
            assert symbol in unavailable.stderr, unavailable.stderr
        for call, diagnostic in (
            ("ui::set_clip(0, 1, 2, 3)", "expects 5 argument(s), got 4"),
            ('ui::set_clip(0, 1, 2, "wide", 4)', "argument 4 expects int, got word"),
            ("ui::reset_clip(1.5)", "argument 1 expects int, got num"),
            ("ui::reset_clip()", "expects 1 argument(s), got 0"),
        ):
            source = root / "clip_negative.fk"
            source.write_text("task main() { " + call + " }\n", encoding="utf-8")
            for command in ([str(freak), "check", str(source)],
                            [str(freak), "build", str(source), "--c"],
                            [str(freak), "build", str(source), "--llvm"],
                            [sys.executable, "-m", "freakc", "check", str(source)],
                            [sys.executable, "-m", "freakc", "build", str(source)]):
                rejected = run(command, repo)
                assert rejected.returncode != 0, (command, rejected.stdout)
                assert diagnostic in rejected.stdout + rejected.stderr, (command, rejected.stdout, rejected.stderr)
                assert not source.with_suffix(".exe").exists()
                assert not source.with_suffix(".c").exists()
                assert not Path(str(source) + ".c").exists()
                assert not Path(str(source) + ".ll").exists()
        if sys.platform == "win32":
            source = root / "clip_probe.c"
            source.write_text(PROBE, encoding="utf-8")
            binary = root / "clip_probe.exe"
            compiled = run([clang, "-O1", "-DFREAK_HAS_UI=1", str(source),
                            str(runtime / "freak_runtime.c"), str(runtime / "freak_llvm_runtime.c"),
                            "-I", str(runtime), "-o", str(binary), "-lws2_32", "-lgdi32", "-luser32"], repo)
            assert compiled.returncode == 0, compiled.stdout + compiled.stderr
            for extra in ([], ["llvm"]):
                executed = run([str(binary), *extra], root, 30)
                assert executed.returncode == 0, executed.stdout + executed.stderr
                assert executed.stdout.strip() == "clip-pixels-ok", executed.stdout
        else:
            print("Win32 pixel execution not applicable on this host", flush=True)
    print("V3 UI clipping: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
