/* ================================================================== */
/*  FREAK UI — Win32/GDI Backend (Phase MA)                            */
/*                                                                     */
/*  Implements freak_ui_platform.h using Win32 APIs:                   */
/*    - CreateWindowEx for window management                           */
/*    - DIBSection pixel buffer for shapes/rects                       */
/*    - GDI for text rendering (TextOut with system fonts)             */
/*    - Win32 message loop for keyboard/mouse/resize events            */
/* ================================================================== */

#include "freak_ui_platform.h"

#ifdef _WIN32

#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

/* ------------------------------------------------------------------ */
/*  Internal state                                                     */
/* ------------------------------------------------------------------ */

typedef struct {
    HWND hwnd;
    HDC  mem_dc;        /* Off-screen DC for pixel buffer */
    HBITMAP hbm;        /* DIBSection bitmap */
    uint32_t* pixels;   /* Pointer to pixel data (BGRA, top-down) */
    int width;
    int height;
    int resizable;
    bool quit_requested;
    bool focused;

    /* GDI drawing state — we overlay GDI text on top of the pixel buffer */
    HDC gdi_dc;         /* Second off-screen DC for GDI drawing */
    HBITMAP gdi_hbm;

    /* Event buffer */
    freak_ui_event events[FREAK_UI_MAX_EVENTS];
    int event_count;
} freak_ui_window;

/* Single window for now (matches the plan's Phase A scope) */
static freak_ui_window* g_win = NULL;

/* ------------------------------------------------------------------ */
/*  Event buffering                                                    */
/* ------------------------------------------------------------------ */

static void push_event(freak_ui_window* w, freak_ui_event ev) {
    if (w->event_count < FREAK_UI_MAX_EVENTS) {
        w->events[w->event_count++] = ev;
    }
}

static int64_t vk_to_freak_key(WPARAM vk) {
    if (vk >= 'A' && vk <= 'Z') return FREAK_KEY_A + (vk - 'A');
    if (vk >= '0' && vk <= '9') return FREAK_KEY_0 + (vk - '0');
    if (vk >= VK_F1 && vk <= VK_F12) return FREAK_KEY_F1 + (vk - VK_F1);
    switch (vk) {
        case VK_RETURN:    return FREAK_KEY_ENTER;
        case VK_ESCAPE:    return FREAK_KEY_ESCAPE;
        case VK_SPACE:     return FREAK_KEY_SPACE;
        case VK_TAB:       return FREAK_KEY_TAB;
        case VK_BACK:      return FREAK_KEY_BACKSPACE;
        case VK_DELETE:    return FREAK_KEY_DELETE;
        case VK_UP:        return FREAK_KEY_UP;
        case VK_DOWN:      return FREAK_KEY_DOWN;
        case VK_LEFT:      return FREAK_KEY_LEFT;
        case VK_RIGHT:     return FREAK_KEY_RIGHT;
        case VK_SHIFT:
        case VK_LSHIFT:
        case VK_RSHIFT:    return FREAK_KEY_SHIFT;
        case VK_CONTROL:
        case VK_LCONTROL:
        case VK_RCONTROL:  return FREAK_KEY_CTRL;
        case VK_MENU:
        case VK_LMENU:
        case VK_RMENU:     return FREAK_KEY_ALT;
        default:           return FREAK_KEY_UNKNOWN;
    }
}

/* ------------------------------------------------------------------ */
/*  Window procedure                                                   */
/* ------------------------------------------------------------------ */

static LRESULT CALLBACK FreakWndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    if (!g_win) return DefWindowProcA(hwnd, msg, wParam, lParam);

    freak_ui_event ev = {0};

    switch (msg) {
        case WM_CLOSE:
            ev.kind = FREAK_UI_EVENT_QUIT;
            push_event(g_win, ev);
            g_win->quit_requested = true;
            return 0;

        case WM_DESTROY:
            PostQuitMessage(0);
            return 0;

        case WM_KEYDOWN:
        case WM_SYSKEYDOWN:
            ev.kind = FREAK_UI_EVENT_KEY;
            ev.key = vk_to_freak_key(wParam);
            ev.pressed = 1;
            ev.repeat = (lParam & 0x40000000) ? 1 : 0;
            push_event(g_win, ev);
            return 0;

        case WM_KEYUP:
        case WM_SYSKEYUP:
            ev.kind = FREAK_UI_EVENT_KEY;
            ev.key = vk_to_freak_key(wParam);
            ev.pressed = 0;
            ev.repeat = 0;
            push_event(g_win, ev);
            return 0;

        case WM_CHAR:
            if (wParam >= 32) { /* skip control chars */
                ev.kind = FREAK_UI_EVENT_CHAR;
                ev.character = (int64_t)wParam;
                push_event(g_win, ev);
            }
            return 0;

        case WM_LBUTTONDOWN:
        case WM_LBUTTONUP:
            ev.kind = FREAK_UI_EVENT_MOUSE;
            ev.mouse_x = (int64_t)LOWORD(lParam);
            ev.mouse_y = (int64_t)HIWORD(lParam);
            ev.button = FREAK_MOUSE_LEFT;
            ev.pressed = (msg == WM_LBUTTONDOWN) ? 1 : 0;
            push_event(g_win, ev);
            return 0;

        case WM_RBUTTONDOWN:
        case WM_RBUTTONUP:
            ev.kind = FREAK_UI_EVENT_MOUSE;
            ev.mouse_x = (int64_t)LOWORD(lParam);
            ev.mouse_y = (int64_t)HIWORD(lParam);
            ev.button = FREAK_MOUSE_RIGHT;
            ev.pressed = (msg == WM_RBUTTONDOWN) ? 1 : 0;
            push_event(g_win, ev);
            return 0;

        case WM_MBUTTONDOWN:
        case WM_MBUTTONUP:
            ev.kind = FREAK_UI_EVENT_MOUSE;
            ev.mouse_x = (int64_t)LOWORD(lParam);
            ev.mouse_y = (int64_t)HIWORD(lParam);
            ev.button = FREAK_MOUSE_MIDDLE;
            ev.pressed = (msg == WM_MBUTTONDOWN) ? 1 : 0;
            push_event(g_win, ev);
            return 0;

        case WM_MOUSEMOVE:
            ev.kind = FREAK_UI_EVENT_MOUSE;
            ev.mouse_x = (int64_t)LOWORD(lParam);
            ev.mouse_y = (int64_t)HIWORD(lParam);
            ev.button = FREAK_MOUSE_NONE;
            ev.pressed = 0;
            push_event(g_win, ev);
            return 0;

        case WM_MOUSEWHEEL:
            ev.kind = FREAK_UI_EVENT_SCROLL;
            {
                POINT pt;
                pt.x = (int)(short)LOWORD(lParam);
                pt.y = (int)(short)HIWORD(lParam);
                ScreenToClient(hwnd, &pt);
                ev.mouse_x = pt.x;
                ev.mouse_y = pt.y;
            }
            ev.scroll_dy = (int64_t)(GET_WHEEL_DELTA_WPARAM(wParam) / WHEEL_DELTA);
            ev.scroll_dx = 0;
            push_event(g_win, ev);
            return 0;

        case WM_SIZE:
            if (wParam != SIZE_MINIMIZED) {
                int new_w = LOWORD(lParam);
                int new_h = HIWORD(lParam);
                if (new_w > 0 && new_h > 0 && (new_w != g_win->width || new_h != g_win->height)) {
                    g_win->width = new_w;
                    g_win->height = new_h;

                    /* Recreate pixel buffer for new size */
                    HDC hdc = GetDC(hwnd);
                    if (g_win->hbm) DeleteObject(g_win->hbm);
                    if (g_win->mem_dc) DeleteDC(g_win->mem_dc);

                    g_win->mem_dc = CreateCompatibleDC(hdc);
                    BITMAPINFO bmi = {0};
                    bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
                    bmi.bmiHeader.biWidth = new_w;
                    bmi.bmiHeader.biHeight = -new_h; /* top-down */
                    bmi.bmiHeader.biPlanes = 1;
                    bmi.bmiHeader.biBitCount = 32;
                    bmi.bmiHeader.biCompression = BI_RGB;
                    g_win->hbm = CreateDIBSection(hdc, &bmi, DIB_RGB_COLORS,
                                                  (void**)&g_win->pixels, NULL, 0);
                    SelectObject(g_win->mem_dc, g_win->hbm);
                    ReleaseDC(hwnd, hdc);

                    ev.kind = FREAK_UI_EVENT_RESIZE;
                    ev.width = new_w;
                    ev.height = new_h;
                    push_event(g_win, ev);
                }
            }
            return 0;

        case WM_SETFOCUS:
            ev.kind = FREAK_UI_EVENT_FOCUS;
            ev.gained = 1;
            push_event(g_win, ev);
            g_win->focused = true;
            return 0;

        case WM_KILLFOCUS:
            ev.kind = FREAK_UI_EVENT_FOCUS;
            ev.gained = 0;
            push_event(g_win, ev);
            g_win->focused = false;
            return 0;

        default:
            break;
    }
    return DefWindowProcA(hwnd, msg, wParam, lParam);
}

/* ------------------------------------------------------------------ */
/*  Window lifecycle                                                   */
/* ------------------------------------------------------------------ */

int64_t freak_ui_create_window(const char* title, int64_t width, int64_t height, int64_t resizable) {
    if (!title) title = "FREAK UI";

    g_win = (freak_ui_window*)calloc(1, sizeof(freak_ui_window));
    if (!g_win) return 0;

    g_win->width = (int)width;
    g_win->height = (int)height;
    g_win->resizable = (int)resizable;

    WNDCLASSA wc = {0};
    wc.style = CS_HREDRAW | CS_VREDRAW;
    wc.lpfnWndProc = FreakWndProc;
    wc.hInstance = GetModuleHandle(NULL);
    wc.lpszClassName = "FreakUIClass";
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    RegisterClassA(&wc);

    DWORD style = resizable ? WS_OVERLAPPEDWINDOW : (WS_OVERLAPPEDWINDOW & ~(WS_THICKFRAME | WS_MAXIMIZEBOX));
    RECT rect = {0, 0, g_win->width, g_win->height};
    AdjustWindowRect(&rect, style, FALSE);

    g_win->hwnd = CreateWindowExA(
        0,
        "FreakUIClass",
        title,
        style,
        CW_USEDEFAULT, CW_USEDEFAULT,
        rect.right - rect.left,
        rect.bottom - rect.top,
        NULL, NULL, wc.hInstance, NULL
    );

    if (!g_win->hwnd) {
        free(g_win);
        g_win = NULL;
        return 0;
    }

    /* Create off-screen pixel buffer (DIBSection) */
    HDC hdc = GetDC(g_win->hwnd);
    g_win->mem_dc = CreateCompatibleDC(hdc);

    BITMAPINFO bmi = {0};
    bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    bmi.bmiHeader.biWidth = g_win->width;
    bmi.bmiHeader.biHeight = -g_win->height; /* top-down */
    bmi.bmiHeader.biPlanes = 1;
    bmi.bmiHeader.biBitCount = 32;
    bmi.bmiHeader.biCompression = BI_RGB;

    g_win->hbm = CreateDIBSection(hdc, &bmi, DIB_RGB_COLORS,
                                  (void**)&g_win->pixels, NULL, 0);
    SelectObject(g_win->mem_dc, g_win->hbm);
    ReleaseDC(g_win->hwnd, hdc);

    /* Do NOT show the window yet — let the caller decide with show_window */
    g_win->focused = false;

    return (int64_t)(intptr_t)g_win->hwnd;
}

void freak_ui_destroy_window(int64_t handle) {
    if (!g_win) return;
    if (g_win->hbm) DeleteObject(g_win->hbm);
    if (g_win->mem_dc) DeleteDC(g_win->mem_dc);
    if (g_win->hwnd) DestroyWindow(g_win->hwnd);
    free(g_win);
    g_win = NULL;
}

void freak_ui_show_window(int64_t handle) {
    if (!g_win || !g_win->hwnd) return;
    ShowWindow(g_win->hwnd, SW_SHOW);
    UpdateWindow(g_win->hwnd);
    g_win->focused = true;
}

void freak_ui_set_title(int64_t handle, const char* title) {
    if (!g_win || !g_win->hwnd) return;
    if (!title) title = "";
    SetWindowTextA(g_win->hwnd, title);
}

int64_t freak_ui_window_should_close(int64_t handle) {
    if (!g_win) return 1;
    return g_win->quit_requested ? 1 : 0;
}

/* ------------------------------------------------------------------ */
/*  Event loop                                                         */
/* ------------------------------------------------------------------ */

int64_t freak_ui_poll_events(int64_t handle) {
    if (!g_win) return -1;

    g_win->event_count = 0;

    MSG msg;
    while (PeekMessageA(&msg, NULL, 0, 0, PM_REMOVE)) {
        if (msg.message == WM_QUIT) {
            g_win->quit_requested = true;
            freak_ui_event ev = {0};
            ev.kind = FREAK_UI_EVENT_QUIT;
            push_event(g_win, ev);
            return -1;
        }
        TranslateMessage(&msg);
        DispatchMessageA(&msg);
    }

    if (g_win->quit_requested) return -1;
    return (int64_t)g_win->event_count;
}

/* Event accessors — index into the per-frame event buffer */
int64_t freak_ui_event_kind(int64_t index) {
    if (!g_win || index < 0 || index >= g_win->event_count) return FREAK_UI_EVENT_NONE;
    return g_win->events[index].kind;
}
int64_t freak_ui_event_key(int64_t index) {
    if (!g_win || index < 0 || index >= g_win->event_count) return 0;
    return g_win->events[index].key;
}
int64_t freak_ui_event_pressed(int64_t index) {
    if (!g_win || index < 0 || index >= g_win->event_count) return 0;
    return g_win->events[index].pressed;
}
int64_t freak_ui_event_repeat(int64_t index) {
    if (!g_win || index < 0 || index >= g_win->event_count) return 0;
    return g_win->events[index].repeat;
}
int64_t freak_ui_event_character(int64_t index) {
    if (!g_win || index < 0 || index >= g_win->event_count) return 0;
    return g_win->events[index].character;
}
int64_t freak_ui_event_mouse_x(int64_t index) {
    if (!g_win || index < 0 || index >= g_win->event_count) return 0;
    return g_win->events[index].mouse_x;
}
int64_t freak_ui_event_mouse_y(int64_t index) {
    if (!g_win || index < 0 || index >= g_win->event_count) return 0;
    return g_win->events[index].mouse_y;
}
int64_t freak_ui_event_button(int64_t index) {
    if (!g_win || index < 0 || index >= g_win->event_count) return 0;
    return g_win->events[index].button;
}
int64_t freak_ui_event_scroll_dy(int64_t index) {
    if (!g_win || index < 0 || index >= g_win->event_count) return 0;
    return g_win->events[index].scroll_dy;
}
int64_t freak_ui_event_width(int64_t index) {
    if (!g_win || index < 0 || index >= g_win->event_count) return 0;
    return g_win->events[index].width;
}
int64_t freak_ui_event_height(int64_t index) {
    if (!g_win || index < 0 || index >= g_win->event_count) return 0;
    return g_win->events[index].height;
}
int64_t freak_ui_event_gained(int64_t index) {
    if (!g_win || index < 0 || index >= g_win->event_count) return 0;
    return g_win->events[index].gained;
}

/* ------------------------------------------------------------------ */
/*  Frame control                                                      */
/* ------------------------------------------------------------------ */

void freak_ui_begin_frame(int64_t handle) {
    /* Nothing needed — drawing goes to pixel buffer directly */
}

void freak_ui_end_frame(int64_t handle) {
    if (!g_win || !g_win->hwnd || !g_win->mem_dc) return;

    HDC hdc = GetDC(g_win->hwnd);
    BitBlt(hdc, 0, 0, g_win->width, g_win->height, g_win->mem_dc, 0, 0, SRCCOPY);
    ReleaseDC(g_win->hwnd, hdc);

    /* ~60 FPS frame cap (naive but functional for Phase MA) */
    Sleep(16);
}

/* ------------------------------------------------------------------ */
/*  Drawing — pixel buffer operations                                  */
/* ------------------------------------------------------------------ */

static inline void set_pixel(int x, int y, uint32_t color) {
    if (!g_win || !g_win->pixels) return;
    if (x < 0 || x >= g_win->width || y < 0 || y >= g_win->height) return;
    g_win->pixels[y * g_win->width + x] = color;
}

static inline uint32_t make_bgr(int64_t r, int64_t g, int64_t b) {
    return ((uint32_t)(r & 0xFF) << 16) | ((uint32_t)(g & 0xFF) << 8) | (uint32_t)(b & 0xFF);
}

void freak_ui_clear(int64_t handle, int64_t r, int64_t g, int64_t b, int64_t a) {
    if (!g_win || !g_win->pixels) return;
    uint32_t color = make_bgr(r, g, b);
    int total = g_win->width * g_win->height;
    uint32_t* p = g_win->pixels;
    for (int i = 0; i < total; i++) {
        p[i] = color;
    }
}

void freak_ui_fill_rect(int64_t handle, int64_t x, int64_t y, int64_t w, int64_t h,
                        int64_t r, int64_t g, int64_t b, int64_t a) {
    if (!g_win || !g_win->pixels) return;

    int ix = (int)x, iy = (int)y, iw = (int)w, ih = (int)h;
    if (ix < 0) { iw += ix; ix = 0; }
    if (iy < 0) { ih += iy; iy = 0; }
    if (ix + iw > g_win->width) iw = g_win->width - ix;
    if (iy + ih > g_win->height) ih = g_win->height - iy;
    if (iw <= 0 || ih <= 0) return;

    uint32_t color = make_bgr(r, g, b);
    uint32_t* p = g_win->pixels;
    for (int row = iy; row < iy + ih; row++) {
        for (int col = ix; col < ix + iw; col++) {
            p[row * g_win->width + col] = color;
        }
    }
}

void freak_ui_stroke_rect(int64_t handle, int64_t x, int64_t y, int64_t w, int64_t h,
                          int64_t r, int64_t g, int64_t b, int64_t a, int64_t thickness) {
    int t = (int)thickness;
    if (t < 1) t = 1;
    /* Top */
    freak_ui_fill_rect(handle, x, y, w, t, r, g, b, a);
    /* Bottom */
    freak_ui_fill_rect(handle, x, y + h - t, w, t, r, g, b, a);
    /* Left */
    freak_ui_fill_rect(handle, x, y, t, h, r, g, b, a);
    /* Right */
    freak_ui_fill_rect(handle, x + w - t, y, t, h, r, g, b, a);
}

void freak_ui_fill_circle(int64_t handle, int64_t cx, int64_t cy, int64_t radius,
                          int64_t r, int64_t g, int64_t b, int64_t a) {
    if (!g_win || !g_win->pixels) return;

    int rad = (int)radius;
    uint32_t color = make_bgr(r, g, b);
    int rad_sq = rad * rad;

    for (int dy = -rad; dy <= rad; dy++) {
        for (int dx = -rad; dx <= rad; dx++) {
            if (dx * dx + dy * dy <= rad_sq) {
                set_pixel((int)cx + dx, (int)cy + dy, color);
            }
        }
    }
}

void freak_ui_draw_line(int64_t handle, int64_t x1, int64_t y1, int64_t x2, int64_t y2,
                        int64_t r, int64_t g, int64_t b, int64_t a, int64_t thickness) {
    if (!g_win || !g_win->pixels) return;

    /* Bresenham's line algorithm */
    int ix1 = (int)x1, iy1 = (int)y1, ix2 = (int)x2, iy2 = (int)y2;
    uint32_t color = make_bgr(r, g, b);
    int t = (int)thickness;
    if (t < 1) t = 1;
    int half_t = t / 2;

    int dx = abs(ix2 - ix1);
    int dy = -abs(iy2 - iy1);
    int sx = ix1 < ix2 ? 1 : -1;
    int sy = iy1 < iy2 ? 1 : -1;
    int err = dx + dy;

    while (1) {
        /* Draw a square of pixels for thickness */
        for (int ty = -half_t; ty <= half_t; ty++) {
            for (int tx = -half_t; tx <= half_t; tx++) {
                set_pixel(ix1 + tx, iy1 + ty, color);
            }
        }
        if (ix1 == ix2 && iy1 == iy2) break;
        int e2 = 2 * err;
        if (e2 >= dy) { err += dy; ix1 += sx; }
        if (e2 <= dx) { err += dx; iy1 += sy; }
    }
}

/* ------------------------------------------------------------------ */
/*  Drawing — GDI text rendering                                       */
/* ------------------------------------------------------------------ */

static HFONT create_font(int64_t font_size, int64_t bold, int64_t italic) {
    return CreateFontA(
        -(int)font_size,         /* height (negative = character height) */
        0,                       /* width (0 = auto) */
        0, 0,                    /* escapement, orientation */
        bold ? FW_BOLD : FW_NORMAL,
        italic ? TRUE : FALSE,
        FALSE, FALSE,            /* underline, strikeout */
        DEFAULT_CHARSET,
        OUT_TT_PRECIS,
        CLIP_DEFAULT_PRECIS,
        CLEARTYPE_QUALITY,       /* ClearType for smooth text */
        DEFAULT_PITCH | FF_DONTCARE,
        "Segoe UI"               /* Default Windows UI font */
    );
}

int64_t freak_ui_draw_text(int64_t handle, const char* text, int64_t x, int64_t y,
                           int64_t r, int64_t g, int64_t b, int64_t font_size,
                           int64_t bold, int64_t italic) {
    if (!g_win || !g_win->mem_dc || !text) return 0;

    HFONT font = create_font(font_size, bold, italic);
    HFONT old_font = (HFONT)SelectObject(g_win->mem_dc, font);

    SetTextColor(g_win->mem_dc, RGB((int)r, (int)g, (int)b));
    SetBkMode(g_win->mem_dc, TRANSPARENT);

    int len = (int)strlen(text);
    SIZE sz;
    GetTextExtentPoint32A(g_win->mem_dc, text, len, &sz);
    TextOutA(g_win->mem_dc, (int)x, (int)y, text, len);

    SelectObject(g_win->mem_dc, old_font);
    DeleteObject(font);

    return (int64_t)sz.cx;
}

int64_t freak_ui_measure_text(const char* text, int64_t font_size, int64_t bold,
                              int64_t italic, int64_t* out_height) {
    if (!g_win || !g_win->mem_dc || !text) {
        if (out_height) *out_height = 0;
        return 0;
    }

    HFONT font = create_font(font_size, bold, italic);
    HFONT old_font = (HFONT)SelectObject(g_win->mem_dc, font);

    int len = (int)strlen(text);
    SIZE sz;
    GetTextExtentPoint32A(g_win->mem_dc, text, len, &sz);

    SelectObject(g_win->mem_dc, old_font);
    DeleteObject(font);

    if (out_height) *out_height = (int64_t)sz.cy;
    return (int64_t)sz.cx;
}

/* ------------------------------------------------------------------ */
/*  Window state queries                                               */
/* ------------------------------------------------------------------ */

int64_t freak_ui_get_width(int64_t handle) {
    return g_win ? (int64_t)g_win->width : 0;
}

int64_t freak_ui_get_height(int64_t handle) {
    return g_win ? (int64_t)g_win->height : 0;
}

/* ------------------------------------------------------------------ */
/*  freak_word wrapper functions                                       */
/*  These accept freak_word (fat string) and extract .data for the     */
/*  underlying const char* functions.                                  */
/* ------------------------------------------------------------------ */

#include "../freak_runtime.h"

int64_t freak_ui_create_window_word(freak_word title, int64_t width, int64_t height, int64_t resizable) {
    return freak_ui_create_window(title.data ? title.data : "FREAK UI", width, height, resizable);
}

void freak_ui_set_title_word(int64_t handle, freak_word title) {
    freak_ui_set_title(handle, title.data ? title.data : "");
}

int64_t freak_ui_draw_text_word(int64_t handle, freak_word text, int64_t x, int64_t y,
                                int64_t r, int64_t g, int64_t b, int64_t font_size,
                                int64_t bold, int64_t italic) {
    return freak_ui_draw_text(handle, text.data ? text.data : "", x, y, r, g, b, font_size, bold, italic);
}

int64_t freak_ui_measure_text_word(freak_word text, int64_t font_size, int64_t bold, int64_t italic) {
    if (!g_win || !text.data) return 0;
    HDC hdc = GetDC(g_win->hwnd);
    int weight = bold ? FW_BOLD : FW_NORMAL;
    HFONT hfont = CreateFontA(-(int)font_size, 0, 0, 0, weight, (DWORD)italic, 0, 0,
                              DEFAULT_CHARSET, 0, 0, CLEARTYPE_QUALITY, DEFAULT_PITCH, "Segoe UI");
    HFONT old = (HFONT)SelectObject(hdc, hfont);
    SIZE sz;
    GetTextExtentPoint32A(hdc, text.data, (int)text.length, &sz);
    SelectObject(hdc, old);
    DeleteObject(hfont);
    ReleaseDC(g_win->hwnd, hdc);
    return (int64_t)sz.cx;
}

#endif /* _WIN32 */
