#ifndef FREAK_UI_PLATFORM_H
#define FREAK_UI_PLATFORM_H

#include <stdint.h>
#include <stdbool.h>

/* ================================================================== */
/*  FREAK UI Platform Abstraction Layer                                */
/*  Phase MA: Window + Drawing + Events on Windows (Win32/GDI)         */
/*                                                                     */
/*  Each platform (Win32, Cocoa, X11) implements this same interface.  */
/*  The FREAK std::ui layer calls these functions via extern.          */
/* ================================================================== */

/* ------------------------------------------------------------------ */
/*  Event types                                                        */
/* ------------------------------------------------------------------ */

/* Event kind tags — matches FREAK route Event { ... } */
#define FREAK_UI_EVENT_NONE      0
#define FREAK_UI_EVENT_QUIT      1
#define FREAK_UI_EVENT_KEY       2
#define FREAK_UI_EVENT_CHAR      3
#define FREAK_UI_EVENT_MOUSE     4
#define FREAK_UI_EVENT_SCROLL    5
#define FREAK_UI_EVENT_RESIZE    6
#define FREAK_UI_EVENT_FOCUS     7

/* Max events buffered per frame */
#define FREAK_UI_MAX_EVENTS 64

typedef struct {
    int64_t kind;       /* FREAK_UI_EVENT_* */
    /* Key events */
    int64_t key;        /* virtual key code (platform-normalized) */
    int64_t pressed;    /* 1 = down, 0 = up */
    int64_t repeat;     /* 1 = auto-repeat */
    /* Char events */
    int64_t character;  /* Unicode codepoint */
    /* Mouse events */
    int64_t mouse_x;
    int64_t mouse_y;
    int64_t button;     /* 0=none, 1=left, 2=right, 3=middle */
    /* Scroll events */
    int64_t scroll_dx;
    int64_t scroll_dy;
    /* Resize events */
    int64_t width;
    int64_t height;
    /* Focus events */
    int64_t gained;     /* 1 = gained, 0 = lost */
} freak_ui_event;

/* ------------------------------------------------------------------ */
/*  Key codes (platform-normalized subset)                             */
/* ------------------------------------------------------------------ */

#define FREAK_KEY_UNKNOWN   0
#define FREAK_KEY_A         1
#define FREAK_KEY_B         2
#define FREAK_KEY_C         3
#define FREAK_KEY_D         4
#define FREAK_KEY_E         5
#define FREAK_KEY_F         6
#define FREAK_KEY_G         7
#define FREAK_KEY_H         8
#define FREAK_KEY_I         9
#define FREAK_KEY_J         10
#define FREAK_KEY_K         11
#define FREAK_KEY_L         12
#define FREAK_KEY_M         13
#define FREAK_KEY_N         14
#define FREAK_KEY_O         15
#define FREAK_KEY_P         16
#define FREAK_KEY_Q         17
#define FREAK_KEY_R         18
#define FREAK_KEY_S         19
#define FREAK_KEY_T         20
#define FREAK_KEY_U         21
#define FREAK_KEY_V         22
#define FREAK_KEY_W         23
#define FREAK_KEY_X         24
#define FREAK_KEY_Y         25
#define FREAK_KEY_Z         26
#define FREAK_KEY_0         27
#define FREAK_KEY_1         28
#define FREAK_KEY_2         29
#define FREAK_KEY_3         30
#define FREAK_KEY_4         31
#define FREAK_KEY_5         32
#define FREAK_KEY_6         33
#define FREAK_KEY_7         34
#define FREAK_KEY_8         35
#define FREAK_KEY_9         36
#define FREAK_KEY_ENTER     37
#define FREAK_KEY_ESCAPE    38
#define FREAK_KEY_SPACE     39
#define FREAK_KEY_TAB       40
#define FREAK_KEY_BACKSPACE 41
#define FREAK_KEY_DELETE    42
#define FREAK_KEY_UP        43
#define FREAK_KEY_DOWN      44
#define FREAK_KEY_LEFT      45
#define FREAK_KEY_RIGHT     46
#define FREAK_KEY_SHIFT     47
#define FREAK_KEY_CTRL      48
#define FREAK_KEY_ALT       49
#define FREAK_KEY_F1        50
#define FREAK_KEY_F2        51
#define FREAK_KEY_F3        52
#define FREAK_KEY_F4        53
#define FREAK_KEY_F5        54
#define FREAK_KEY_F6        55
#define FREAK_KEY_F7        56
#define FREAK_KEY_F8        57
#define FREAK_KEY_F9        58
#define FREAK_KEY_F10       59
#define FREAK_KEY_F11       60
#define FREAK_KEY_F12       61

/* Mouse button codes */
#define FREAK_MOUSE_NONE    0
#define FREAK_MOUSE_LEFT    1
#define FREAK_MOUSE_RIGHT   2
#define FREAK_MOUSE_MIDDLE  3

/* ------------------------------------------------------------------ */
/*  Window lifecycle                                                   */
/* ------------------------------------------------------------------ */

/* Create a native window. Returns a nonreused opaque handle (0 on failure).
   The handle is not an OS window identifier. A second live window is rejected
   by the current singleton backend. */
int64_t freak_ui_create_window(const char* title, int64_t width, int64_t height, int64_t resizable);

/* Destroy the window and free resources. */
void freak_ui_destroy_window(int64_t handle);

/* Show the window (make it visible and bring to front). */
void freak_ui_show_window(int64_t handle);

/* Update the window title bar text. */
void freak_ui_set_title(int64_t handle, const char* title);

/* Returns 1 if the window close was requested (X button, WM_CLOSE), 0 otherwise. */
int64_t freak_ui_window_should_close(int64_t handle);

/* ------------------------------------------------------------------ */
/*  Event loop                                                         */
/* ------------------------------------------------------------------ */

/* Poll OS events. Returns number of events buffered.
   Returns -1 if quit was requested. */
int64_t freak_ui_poll_events(int64_t handle);

/* Get a buffered event by index (0..count-1). Returns event struct fields
   packed into a flat array for easy FFI. */
int64_t freak_ui_event_kind(int64_t index);
int64_t freak_ui_event_key(int64_t index);
int64_t freak_ui_event_pressed(int64_t index);
int64_t freak_ui_event_repeat(int64_t index);
int64_t freak_ui_event_character(int64_t index);
int64_t freak_ui_event_mouse_x(int64_t index);
int64_t freak_ui_event_mouse_y(int64_t index);
int64_t freak_ui_event_button(int64_t index);
int64_t freak_ui_event_scroll_dy(int64_t index);
int64_t freak_ui_event_width(int64_t index);
int64_t freak_ui_event_height(int64_t index);
int64_t freak_ui_event_gained(int64_t index);

/* ------------------------------------------------------------------ */
/*  Frame control                                                      */
/* ------------------------------------------------------------------ */

void freak_ui_begin_frame(int64_t handle);
void freak_ui_end_frame(int64_t handle);
/* Replace the current half-open drawing clip, intersected with client bounds.
   Nonpositive extents are empty. Invalid/stale handles are ignored.
   reset_clip and begin_frame restore full client bounds; nesting is caller-owned. */
void freak_ui_set_clip(int64_t handle, int64_t x, int64_t y, int64_t width, int64_t height);
void freak_ui_reset_clip(int64_t handle);

/* ------------------------------------------------------------------ */
/*  Drawing — pixel buffer operations                                  */
/* ------------------------------------------------------------------ */

void freak_ui_clear(int64_t handle, int64_t r, int64_t g, int64_t b, int64_t a);
void freak_ui_fill_rect(int64_t handle, int64_t x, int64_t y, int64_t w, int64_t h,
                        int64_t r, int64_t g, int64_t b, int64_t a);
void freak_ui_stroke_rect(int64_t handle, int64_t x, int64_t y, int64_t w, int64_t h,
                          int64_t r, int64_t g, int64_t b, int64_t a, int64_t thickness);
void freak_ui_fill_circle(int64_t handle, int64_t cx, int64_t cy, int64_t radius,
                          int64_t r, int64_t g, int64_t b, int64_t a);
void freak_ui_draw_line(int64_t handle, int64_t x1, int64_t y1, int64_t x2, int64_t y2,
                        int64_t r, int64_t g, int64_t b, int64_t a, int64_t thickness);

/* ------------------------------------------------------------------ */
/*  Drawing — GDI text rendering (Windows)                             */
/* ------------------------------------------------------------------ */

/* Draw text at (x, y) with given color and font size.
   Returns the width of the rendered text in pixels. */
int64_t freak_ui_draw_text(int64_t handle, const char* text, int64_t x, int64_t y,
                           int64_t r, int64_t g, int64_t b, int64_t font_size,
                           int64_t bold, int64_t italic);

/* Measure text dimensions without drawing. Returns width. Height via out param. */
int64_t freak_ui_measure_text(const char* text, int64_t font_size, int64_t bold,
                              int64_t italic, int64_t* out_height);

/* ------------------------------------------------------------------ */
/*  Window state queries                                               */
/* ------------------------------------------------------------------ */

int64_t freak_ui_get_width(int64_t handle);
int64_t freak_ui_get_height(int64_t handle);

/* ------------------------------------------------------------------ */
/*  Legacy aliases (for backward compatibility with existing code)     */
/* ------------------------------------------------------------------ */

#define freak_llvm_ui_create_native(t,w,h) freak_ui_create_window((const char*)(intptr_t)(t),(w),(h),1)
#define freak_llvm_ui_poll_events(h)       (freak_ui_poll_events(h) >= 0 ? 1 : 0)
#define freak_llvm_ui_begin_frame(h)       freak_ui_begin_frame(h)
#define freak_llvm_ui_end_frame(h)         freak_ui_end_frame(h)
#define freak_llvm_ui_clear(h,r,g,b,a)     freak_ui_clear((h),(r),(g),(b),(a))
#define freak_llvm_ui_fill_rect(h,x,y,w,hh,r,g,b,a) freak_ui_fill_rect((h),(x),(y),(w),(hh),(r),(g),(b),(a))

#endif /* FREAK_UI_PLATFORM_H */
