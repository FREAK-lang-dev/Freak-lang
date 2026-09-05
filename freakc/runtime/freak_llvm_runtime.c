#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <errno.h>
#include "freak_runtime.h"
extern int64_t freak_llvm_word_adopt(int64_t pointer);
extern void freak_llvm_word_release_replaced(int64_t previous, int64_t replacement);
/* ctype.h no longer needed — toupper/tolower/isspace moved to LLVM IR */
#ifdef _WIN32
#include <io.h>
__declspec(dllimport) unsigned long long __stdcall GetTickCount64(void);
#else
#include <unistd.h>
#include <sys/time.h>
#include <sys/wait.h>
#endif

static int64_t freak_llvm_normalize_process_status(int status) {
#ifdef _WIN32
    return (int64_t)status;
#else
    if (status == -1) return -1;
    if (WIFEXITED(status)) return (int64_t)WEXITSTATUS(status);
    if (WIFSIGNALED(status)) return (int64_t)(128 + WTERMSIG(status));
    return (int64_t)status;
#endif
}

/* ── Global args — no longer needed, moved to LLVM IR globals ── */

/* ── Word (string) primitives ───────────────────────── */
/* freak_word_from_int, from_bool, concat, eq, neq, length, char_at,
   starts_with, ends_with, to_int are now pure LLVM IR intrinsics. */

/* ── String methods ────────────────────────────────── */
/* All word/string functions are now pure LLVM IR intrinsics,
   including replace, contains, to_upper, to_lower, trim, etc. */

/* ── I/O ────────────────────────────────────────────── */
/* freak_llvm_say, print_str, print_int, print_newline are now
   defined as pure LLVM IR intrinsics in the emitted .ll file. */
/* freak_llvm_ask is defined in freak_runtime.c */

/* ── File I/O ───────────────────────────────────────── */
/* fs_read, fs_write, fs_append, fs_exists, fs_delete are now pure FREAK
   tasks in std/runtime.fk. They call the libc wrappers below. */

/* libc wrappers — take/return i64 (FREAK's universal ABI) */
static int64_t freak_llvm_copy_word_result(freak_word value) {
    if (value.length == SIZE_MAX) {
        freak_word_release_owned(&value);
        fprintf(stderr, "FREAK: word bridge size overflow\n");
        exit(1);
    }
    char* copy = (char*)malloc(value.length + 1);
    if (!copy) {
        freak_word_release_owned(&value);
        fprintf(stderr, "FREAK: out of memory\n");
        exit(1);
    }
    if (value.length > 0) memcpy(copy, value.data, value.length);
    copy[value.length] = '\0';
    freak_word_release_owned(&value);
    return freak_llvm_word_adopt((int64_t)copy);
}

int64_t freak_llvm_fs_list_dir(int64_t path) {
    return freak_llvm_copy_word_result(
        freak_fs_list_dir(freak_word_lit((const char*)path))
    );
}

void freak_llvm_fs_make_dir(int64_t path) {
    freak_fs_make_dir(freak_word_lit((const char*)path));
}

int64_t freak_llvm_process_env(int64_t name) {
    return freak_llvm_copy_word_result(
        freak_process_env(freak_word_lit((const char*)name))
    );
}

int64_t freak_llvm_process_input(void) {
    return freak_llvm_copy_word_result(freak_process_input());
}

int64_t freak_fopen(int64_t path, int64_t mode) {
    return (int64_t)fopen((const char*)path, (const char*)mode);
}
int64_t freak_fclose(int64_t file) {
    return (int64_t)fclose((FILE*)file);
}
int64_t freak_fseek(int64_t file, int64_t offset, int64_t whence) {
    return (int64_t)fseek((FILE*)file, (long)offset, (int)whence);
}
int64_t freak_ftell(int64_t file) {
    return (int64_t)ftell((FILE*)file);
}
int64_t freak_fread(int64_t buf, int64_t size, int64_t count, int64_t file) {
    return (int64_t)fread((void*)buf, (size_t)size, (size_t)count, (FILE*)file);
}
int64_t freak_fwrite(int64_t buf, int64_t size, int64_t count, int64_t file) {
    return (int64_t)fwrite((const void*)buf, (size_t)size, (size_t)count, (FILE*)file);
}
/**
 * Allocates zero-initialized memory for an array of elements.
 * @param count Number of elements to allocate.
 * @param size Size of each element in bytes.
 * @returns Address of the allocated memory, or zero if allocation fails.
 */
int64_t freak_calloc(int64_t count, int64_t size) {
    return (int64_t)calloc((size_t)count, (size_t)size);
}
/**
 * Removes the file at the specified path.
 * @param path Null-terminated path to the file.
 * @returns 1 if removed or already absent; 0 on another removal error.
 */
int64_t freak_remove(int64_t path) {
#ifdef _WIN32
    int result = _unlink((const char*)path);
#else
    int result = unlink((const char*)path);
#endif
    return result == 0 || errno == ENOENT;
}

/* ── Process ────────────────────────────────────────── */
/* freak_llvm_process_args_count, process_arg, process_exit, process_exec
   are now pure LLVM IR intrinsics. */

int64_t freak_llvm_process_exec_capture(int64_t cmd_p) {
    const char* cmd = (const char*)cmd_p;
#ifdef _WIN32
    FILE* fp = _popen(cmd, "r");
#else
    FILE* fp = popen(cmd, "r");
#endif
    if (!fp) return (int64_t)"";
    size_t cap = 1024, len = 0;
    char* buf = (char*)malloc(cap);
    if (!buf) {
#ifdef _WIN32
        _pclose(fp);
#else
        pclose(fp);
#endif
        return (int64_t)"";
    }
    size_t n;
    while ((n = fread(buf + len, 1, cap - len - 1, fp)) > 0) {
        len += n;
        if (len + 1 >= cap) { cap *= 2; buf = (char*)realloc(buf, cap); }
    }
    buf[len] = '\0';
#ifdef _WIN32
    _pclose(fp);
#else
    pclose(fp);
#endif
    return freak_llvm_word_adopt((int64_t)buf);
}

/* ── Time ──────────────────────────────────────────── */
int64_t freak_llvm_time_now_ms(void) {
#ifdef _WIN32
    return (int64_t)GetTickCount64();
#else
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (int64_t)(tv.tv_sec * 1000LL + tv.tv_usec / 1000LL);
#endif
}

/* ── Panic ──────────────────────────────────────────── */
/* freak_llvm_panic is now a pure LLVM IR intrinsic. */

/* ── LLVM-compatible dynamic arrays (store int64_t) ─── */
/* The C backend arrays store freak_word structs (24 bytes each).
   The LLVM backend passes all values as int64_t (8 bytes), so we
   need a separate pool that stores int64_t. */
#define FREAK_LLVM_MAX_ARRAYS 1024
typedef struct {
    int64_t* data;
    int64_t  length;
    int64_t  capacity;
    int64_t  next_free;
    uint32_t generation;
    bool     in_use;
} freak_llvm_dyn_array;
static freak_llvm_dyn_array freak_llvm_arrays[FREAK_LLVM_MAX_ARRAYS];
static int64_t freak_llvm_array_count = 0;
static int64_t freak_llvm_array_free_head = -1;

#define FREAK_LLVM_ARRAY_GENERATION_MAX UINT32_C(0x7fffffff)

static int64_t freak_llvm_array_make_handle(int64_t slot, uint32_t generation) {
    return (int64_t)(((uint64_t)generation << 32) | (uint64_t)(uint32_t)slot);
}

static int64_t freak_llvm_array_slot_for_handle(int64_t handle) {
    if (handle < 0) return -1;
    uint64_t raw = (uint64_t)handle;
    int64_t slot = (int64_t)(uint32_t)(raw & UINT64_C(0xffffffff));
    uint32_t generation = (uint32_t)(raw >> 32);
    if (slot < 0 || slot >= freak_llvm_array_count) return -1;
    freak_llvm_dyn_array* array = &freak_llvm_arrays[slot];
    if (!array->in_use || array->generation != generation) return -1;
    return slot;
}

int64_t freak_llvm_array_new(void) {
    int64_t h = freak_llvm_array_free_head;
    if (h >= 0) {
        freak_llvm_array_free_head = freak_llvm_arrays[h].next_free;
        freak_llvm_arrays[h].generation += 1;
    } else {
        if (freak_llvm_array_count >= FREAK_LLVM_MAX_ARRAYS) {
            fprintf(stderr, "FREAK: too many live arrays (max %d)\n", FREAK_LLVM_MAX_ARRAYS);
            exit(1);
        }
        h = freak_llvm_array_count++;
        freak_llvm_arrays[h].generation = 1;
    }
    freak_llvm_arrays[h].length = 0;
    freak_llvm_arrays[h].capacity = 64;
    freak_llvm_arrays[h].next_free = -1;
    freak_llvm_arrays[h].in_use = true;
    freak_llvm_arrays[h].data = (int64_t*)malloc(64 * sizeof(int64_t));
    if (!freak_llvm_arrays[h].data) { fprintf(stderr, "FREAK: OOM\n"); exit(1); }
    return freak_llvm_array_make_handle(h, freak_llvm_arrays[h].generation);
}

int64_t freak_llvm_word_snapshot_lines(int64_t source) {
    if (freak_llvm_array_free_head < 0 && freak_llvm_array_count >= FREAK_LLVM_MAX_ARRAYS) return -1;
    const char* text = (const char*)source;
    /* The LLVM ABI is NUL-terminated: obtain its length exactly once, then
       scan/copy bounded ranges. Adoption also uses the known range length. */
    size_t length = text ? strlen(text) : 0;
    size_t count = length ? 1 : 0;
    for (size_t i = 0; i < length; ++i) {
        if (text[i] == '\n') {
            if (count == SIZE_MAX) return -1;
            ++count;
        }
    }
    size_t capacity = count ? count : 1;
    if (capacity > INT64_MAX || capacity > SIZE_MAX / sizeof(int64_t)) return -1;
    int64_t* lines = (int64_t*)malloc(capacity * sizeof(*lines));
    if (!lines) return -1;
    size_t used = 0, start = 0;
    for (size_t i = 0; count != 0; ++i) {
        if (i == length || text[i] == '\n') {
            size_t part_length = i - start;
            if (part_length == SIZE_MAX) goto fail;
            char* part = (char*)malloc(part_length + 1);
            if (!part) goto fail;
            if (part_length) memcpy(part, text + start, part_length);
            part[part_length] = '\0';
            int64_t adopted = freak_llvm_word_try_adopt_sized((int64_t)part, part_length);
            if (!adopted) { free(part); goto fail; }
            lines[used++] = adopted;
            if (i == length) break;
            start = i + 1;
        }
    }
    int64_t slot = freak_llvm_array_free_head;
    if (slot >= 0) {
        freak_llvm_array_free_head = freak_llvm_arrays[slot].next_free;
        freak_llvm_arrays[slot].generation += 1;
    } else {
        slot = freak_llvm_array_count++;
        freak_llvm_arrays[slot].generation = 1;
    }
    freak_llvm_arrays[slot].data = lines;
    freak_llvm_arrays[slot].length = (int64_t)used;
    freak_llvm_arrays[slot].capacity = (int64_t)capacity;
    freak_llvm_arrays[slot].next_free = -1;
    freak_llvm_arrays[slot].in_use = true;
    return freak_llvm_array_make_handle(slot, freak_llvm_arrays[slot].generation);
fail:
    for (size_t i = 0; i < used; ++i) freak_llvm_word_release_replaced(lines[i], 0);
    free(lines);
    return -1;
}

void freak_llvm_array_push(int64_t handle, int64_t item) {
    int64_t slot = freak_llvm_array_slot_for_handle(handle);
    if (slot < 0) return;
    freak_llvm_dyn_array* a = &freak_llvm_arrays[slot];
    if (a->length >= a->capacity) {
        a->capacity *= 2;
        a->data = (int64_t*)realloc(a->data, (size_t)a->capacity * sizeof(int64_t));
        if (!a->data) { fprintf(stderr, "FREAK: OOM growing array\n"); exit(1); }
    }
    a->data[a->length++] = item;
}
void freak_llvm_array_push_owned(int64_t handle, int64_t item) {
    if (freak_llvm_array_slot_for_handle(handle) < 0) {
        freak_llvm_word_release_replaced(item, 0);
        return;
    }
    freak_llvm_array_push(handle, item);
}
int64_t freak_llvm_array_get(int64_t handle, int64_t index) {
    int64_t slot = freak_llvm_array_slot_for_handle(handle);
    if (slot < 0) return 0;
    freak_llvm_dyn_array* a = &freak_llvm_arrays[slot];
    if (index < 0 || index >= a->length) return 0;
    return a->data[index];
}
int64_t freak_llvm_array_len(int64_t handle) {
    int64_t slot = freak_llvm_array_slot_for_handle(handle);
    if (slot < 0) return 0;
    return freak_llvm_arrays[slot].length;
}
void freak_llvm_array_set(int64_t handle, int64_t index, int64_t item) {
    int64_t slot = freak_llvm_array_slot_for_handle(handle);
    if (slot < 0) return;
    freak_llvm_dyn_array* a = &freak_llvm_arrays[slot];
    if (index < 0 || index >= a->length) {
        fprintf(stderr, "FREAK: array_set index %lld out of bounds (len %lld)\n",
                (long long)index, (long long)a->length);
        exit(1);
    }
    a->data[index] = item;
}

void freak_llvm_array_set_owned(int64_t handle, int64_t index, int64_t item) {
    int64_t slot = freak_llvm_array_slot_for_handle(handle);
    if (slot < 0) {
        freak_llvm_word_release_replaced(item, 0);
        return;
    }
    freak_llvm_dyn_array* a = &freak_llvm_arrays[slot];
    if (index < 0 || index >= a->length) {
        fprintf(stderr, "FREAK: array_set index %lld out of bounds (len %lld)\n",
                (long long)index, (long long)a->length);
        exit(1);
    }
    freak_llvm_word_release_replaced(a->data[index], item);
    a->data[index] = item;
}

void freak_llvm_array_release(int64_t handle) {
    int64_t slot = freak_llvm_array_slot_for_handle(handle);
    if (slot < 0) return;
    freak_llvm_dyn_array* a = &freak_llvm_arrays[slot];
    free(a->data);
    a->data = NULL;
    a->length = 0;
    a->capacity = 0;
    a->in_use = false;
    if (a->generation >= FREAK_LLVM_ARRAY_GENERATION_MAX) {
        a->next_free = -1;
        return;
    }
    a->next_free = freak_llvm_array_free_head;
    freak_llvm_array_free_head = slot;
}

void freak_llvm_array_release_owned(int64_t handle) {
    int64_t slot = freak_llvm_array_slot_for_handle(handle);
    if (slot < 0) return;
    freak_llvm_dyn_array* a = &freak_llvm_arrays[slot];
    for (int64_t i = 0; i < a->length; ++i) {
        freak_llvm_word_release_replaced(a->data[i], 0);
    }
    freak_llvm_array_release(handle);
}

static int64_t freak_llvm_word_join_impl(int64_t handle, bool release_elements) {
    int64_t slot = freak_llvm_array_slot_for_handle(handle);
    if (slot < 0) return (int64_t)"";
    freak_llvm_dyn_array* a = &freak_llvm_arrays[slot];
    size_t total = 0;
    for (int64_t index = 0; index < a->length; index++) {
        const char* part = (const char*)a->data[index];
        size_t part_length = part ? strlen(part) : 0;
        if (part_length > SIZE_MAX - total - 1) {
            fprintf(stderr, "FREAK: joined word is too large\n");
            exit(1);
        }
        total += part_length;
    }

    char* joined = (char*)malloc(total + 1);
    if (!joined) {
        fprintf(stderr, "FREAK: out of memory joining words\n");
        exit(1);
    }
    size_t offset = 0;
    for (int64_t index = 0; index < a->length; index++) {
        const char* part = (const char*)a->data[index];
        size_t part_length = part ? strlen(part) : 0;
        if (part_length > 0) {
            memcpy(joined + offset, part, part_length);
            offset += part_length;
        }
    }
    joined[total] = '\0';
    if (release_elements) {
        freak_llvm_array_release_owned(handle);
    } else {
        freak_llvm_array_release(handle);
    }
    return freak_llvm_word_adopt((int64_t)joined);
}

int64_t freak_llvm_word_join(int64_t handle) {
    return freak_llvm_word_join_impl(handle, false);
}

int64_t freak_llvm_word_join_owned(int64_t handle) {
    return freak_llvm_word_join_impl(handle, true);
}

/* ── Shape (struct) helpers ─────────────────────────── */
/* freak_llvm_shape_alloc, shape_get, shape_set are now
   defined as pure LLVM IR intrinsics (calloc + GEP). */

/* ── LLVM wrapper aliases ───────────────────────────── */
/* All word function wrappers removed — now pure LLVM IR intrinsics. */

/* ── Bitcast helpers for double ↔ i64 ──────────────── */
static inline double i64_to_double(int64_t v) {
    double d; memcpy(&d, &v, sizeof(d)); return d;
}
static inline int64_t double_to_i64(double d) {
    int64_t v; memcpy(&v, &d, sizeof(v)); return v;
}

/* ── UI bridge (LLVM i64 → real freak_ui_* calls) ──── */
/* The LLVM backend passes everything as i64. These      */
/* bridge functions call the real UI runtime.             */
/* Only compiled when FREAK_HAS_UI is defined (i.e. when */
/* the UI backend .c file is included in the build).     */

#ifdef FREAK_HAS_UI
#include "freak_runtime.h"
int64_t freak_llvm_ui_create_window(int64_t title, int64_t w, int64_t h, int64_t flags) {
    freak_word t = freak_word_lit((const char*)title);
    return freak_ui_create_window_word(t, w, h, flags);
}
void freak_llvm_ui_destroy_window(int64_t handle) {
    freak_ui_destroy_window(handle);
}
int64_t freak_llvm_ui_poll_events(int64_t handle) {
    return freak_ui_poll_events(handle);
}
void freak_llvm_ui_begin_frame(int64_t handle) {
    freak_ui_begin_frame(handle);
}
void freak_llvm_ui_end_frame(int64_t handle) {
    freak_ui_end_frame(handle);
}
int64_t freak_llvm_ui_event_kind(int64_t idx)      { return freak_ui_event_kind(idx); }
int64_t freak_llvm_ui_event_key(int64_t idx)       { return freak_ui_event_key(idx); }
int64_t freak_llvm_ui_event_pressed(int64_t idx)   { return freak_ui_event_pressed(idx); }
int64_t freak_llvm_ui_event_character(int64_t idx)  { return freak_ui_event_character(idx); }
int64_t freak_llvm_ui_event_mouse_x(int64_t idx)   { return freak_ui_event_mouse_x(idx); }
int64_t freak_llvm_ui_event_mouse_y(int64_t idx)   { return freak_ui_event_mouse_y(idx); }
int64_t freak_llvm_ui_event_button(int64_t idx)    { return freak_ui_event_button(idx); }
int64_t freak_llvm_ui_event_repeat(int64_t idx)    { return freak_ui_event_repeat(idx); }
int64_t freak_llvm_ui_event_scroll_dy(int64_t idx) { return freak_ui_event_scroll_dy(idx); }
int64_t freak_llvm_ui_event_width(int64_t idx)     { return freak_ui_event_width(idx); }
int64_t freak_llvm_ui_event_height(int64_t idx)    { return freak_ui_event_height(idx); }
int64_t freak_llvm_ui_event_gained(int64_t idx)    { return freak_ui_event_gained(idx); }
int64_t freak_llvm_ui_get_width(int64_t handle)    { return freak_ui_get_width(handle); }
int64_t freak_llvm_ui_get_height(int64_t handle)   { return freak_ui_get_height(handle); }
void freak_llvm_ui_clear(int64_t h, int64_t r, int64_t g, int64_t b, int64_t a) {
    freak_ui_clear(h, r, g, b, a);
}
/**
 * Fills a rectangle in a UI window.
 * @param h Window handle.
 * @param x Horizontal position.
 * @param y Vertical position.
 * @param w Rectangle width.
 * @param hh Rectangle height.
 * @param r Red color component.
 * @param g Green color component.
 * @param b Blue color component.
 * @param a Alpha color component.
 */
void freak_llvm_ui_fill_rect(int64_t h, int64_t x, int64_t y, int64_t w, int64_t hh, int64_t r, int64_t g, int64_t b, int64_t a) {
    freak_ui_fill_rect(h, x, y, w, hh, r, g, b, a);
}
/**
 * Draws a rectangle outline with the specified color and stroke thickness.
 * @param h Window or rendering context handle.
 * @param x Horizontal position of the rectangle.
 * @param y Vertical position of the rectangle.
 * @param w Rectangle width.
 * @param hh Rectangle height.
 * @param r Red color component.
 * @param g Green color component.
 * @param b Blue color component.
 * @param a Alpha color component.
 * @param thickness Stroke thickness.
 */
void freak_llvm_ui_stroke_rect(int64_t h, int64_t x, int64_t y, int64_t w, int64_t hh, int64_t r, int64_t g, int64_t b, int64_t a, int64_t thickness) {
    freak_ui_stroke_rect(h, x, y, w, hh, r, g, b, a, thickness);
}
/**
 * Draws a filled circle in a UI window.
 * @param h UI window handle.
 * @param cx Circle center x-coordinate.
 * @param cy Circle center y-coordinate.
 * @param radius Circle radius.
 * @param r Red color component.
 * @param g Green color component.
 * @param b Blue color component.
 * @param a Alpha color component.
 */
void freak_llvm_ui_fill_circle(int64_t h, int64_t cx, int64_t cy, int64_t radius, int64_t r, int64_t g, int64_t b, int64_t a) {
    freak_ui_fill_circle(h, cx, cy, radius, r, g, b, a);
}
/**
 * Draws a colored line in a UI window.
 * @param h Window handle.
 * @param x1 Starting x-coordinate.
 * @param y1 Starting y-coordinate.
 * @param x2 Ending x-coordinate.
 * @param y2 Ending y-coordinate.
 * @param r Red color component.
 * @param g Green color component.
 * @param b Blue color component.
 * @param a Alpha color component.
 * @param thickness Line thickness.
 */
void freak_llvm_ui_draw_line(int64_t h, int64_t x1, int64_t y1, int64_t x2, int64_t y2, int64_t r, int64_t g, int64_t b, int64_t a, int64_t thickness) {
    freak_ui_draw_line(h, x1, y1, x2, y2, r, g, b, a, thickness);
}
/**
 * Draws text in a window using the specified position, color, size, and style.
 * @param h Window handle.
 * @param text Null-terminated text to draw.
 * @param x Horizontal position.
 * @param y Vertical position.
 * @param r Red color component.
 * @param g Green color component.
 * @param b Blue color component.
 * @param size Text size.
 * @param bold Nonzero to draw bold text.
 * @param italic Nonzero to draw italic text.
 * @returns Result of the text drawing operation.
 */
int64_t freak_llvm_ui_draw_text(int64_t h, int64_t text, int64_t x, int64_t y, int64_t r, int64_t g, int64_t b, int64_t size, int64_t bold, int64_t italic) {
    freak_word t = freak_word_lit((const char*)text);
    return freak_ui_draw_text_word(h, t, x, y, r, g, b, size, bold, italic);
}
int64_t freak_llvm_ui_measure_text(int64_t text, int64_t size, int64_t bold, int64_t italic) {
    freak_word t = freak_word_lit((const char*)text);
    return freak_ui_measure_text_word(t, size, bold, italic);
}
#else /* !FREAK_HAS_UI — no-op stubs so non-UI builds still link */
int64_t freak_llvm_ui_create_native(int64_t t, int64_t w, int64_t h) { return 0; }
int64_t freak_llvm_ui_poll_events(int64_t h)  { return 0; }
void    freak_llvm_ui_begin_frame(int64_t h)  { }
void    freak_llvm_ui_end_frame(int64_t h)    { }
void    freak_llvm_ui_clear(int64_t h, int64_t r, int64_t g, int64_t b, int64_t a) { }
/**
 * No-op when FREAK_HAS_UI is disabled. Fills a rectangle in a UI window.
 * @param h UI window handle.
 * @param x Horizontal position.
 * @param y Vertical position.
 * @param w Rectangle width.
 * @param hh Rectangle height.
 * @param r Red color component.
 * @param g Green color component.
 * @param b Blue color component.
 * @param a Alpha color component.
 */
void    freak_llvm_ui_fill_rect(int64_t h, int64_t x, int64_t y, int64_t w, int64_t hh, int64_t r, int64_t g, int64_t b, int64_t a) { }
/**
 * No-op when FREAK_HAS_UI is disabled. Draws a stroked rectangle in the specified color and line thickness.
 * @param h Window or drawing context handle.
 * @param x Horizontal position of the rectangle.
 * @param y Vertical position of the rectangle.
 * @param w Rectangle width.
 * @param hh Rectangle height.
 * @param r Red color component.
 * @param g Green color component.
 * @param b Blue color component.
 * @param a Alpha color component.
 * @param thickness Stroke thickness.
 */
void    freak_llvm_ui_stroke_rect(int64_t h, int64_t x, int64_t y, int64_t w, int64_t hh, int64_t r, int64_t g, int64_t b, int64_t a, int64_t thickness) { }
/**
 * No-op when FREAK_HAS_UI is disabled. Draws a colored line in a window.
 * @param h Window handle.
 * @param x1 Starting x-coordinate.
 * @param y1 Starting y-coordinate.
 * @param x2 Ending x-coordinate.
 * @param y2 Ending y-coordinate.
 * @param r Red color component.
 * @param g Green color component.
 * @param b Blue color component.
 * @param a Alpha color component.
 * @param thickness Line thickness.
 */
void    freak_llvm_ui_draw_line(int64_t h, int64_t x1, int64_t y1, int64_t x2, int64_t y2, int64_t r, int64_t g, int64_t b, int64_t a, int64_t thickness) { }
#endif /* FREAK_HAS_UI */

/* ── Numeric conversions (i64 ↔ bitcast double) ────── */
/* These were marked "pure LLVM IR intrinsics" in a comment but no IR
   definition was ever emitted, so any user-side `.to_num()` /
   `.to_int()` / `.to_word()` call became an unresolved extern.        */
int64_t freak_llvm_int_to_num(int64_t i) {
    return double_to_i64((double)i);
}
/**
 * Decodes a packed double and converts its numeric value to an integer.
 * @param n IEEE-754 double bits carried in the universal integer ABI.
 * @returns The numeric value truncated toward zero when representable.
 */
int64_t freak_llvm_num_to_int(int64_t n) {
    return (int64_t)i64_to_double(n);
}
/**
 * Formats a packed double value as a runtime word.
 * @param n IEEE-754 double bits carried in the universal integer ABI.
 * @returns An owned runtime word containing the formatted value.
 */
int64_t freak_llvm_word_from_num(int64_t n) {
    char* buf = (char*)malloc(64);
    if (!buf) {
        fprintf(stderr, "FREAK: out of memory formatting a number\n");
        exit(1);
    }
    snprintf(buf, 64, "%.10g", i64_to_double(n));
    return freak_llvm_word_adopt((int64_t)buf);
}

/* ── char_to_word (UTF-8 encode a code point) ───────── */
int64_t freak_llvm_char_to_word(int64_t code) {
    char* buf = (char*)malloc(5);
    if (!buf) return (int64_t)"";
    size_t len = 0;
    uint32_t c = (uint32_t)code;
    if (c <= 0x7F) {
        buf[0] = (char)c; len = 1;
    } else if (c <= 0x7FF) {
        buf[0] = (char)(0xC0 | (c >> 6));
        buf[1] = (char)(0x80 | (c & 0x3F));
        len = 2;
    } else if (c <= 0xFFFF) {
        buf[0] = (char)(0xE0 | (c >> 12));
        buf[1] = (char)(0x80 | ((c >> 6) & 0x3F));
        buf[2] = (char)(0x80 | (c & 0x3F));
        len = 3;
    } else {
        buf[0] = (char)(0xF0 | (c >> 18));
        buf[1] = (char)(0x80 | ((c >> 12) & 0x3F));
        buf[2] = (char)(0x80 | ((c >> 6) & 0x3F));
        buf[3] = (char)(0x80 | (c & 0x3F));
        len = 4;
    }
    buf[len] = '\0';
    return freak_llvm_word_adopt((int64_t)buf);
}

/* ── Math bridge (LLVM i64-bitcast-double → real <math.h>) ─ */
#include <math.h>
int64_t freak_llvm_math_sqrt(int64_t x)  { return double_to_i64(sqrt(i64_to_double(x))); }
int64_t freak_llvm_math_pow(int64_t b, int64_t e) { return double_to_i64(pow(i64_to_double(b), i64_to_double(e))); }
int64_t freak_llvm_math_sin(int64_t x)   { return double_to_i64(sin(i64_to_double(x))); }
int64_t freak_llvm_math_cos(int64_t x)   { return double_to_i64(cos(i64_to_double(x))); }
int64_t freak_llvm_math_tan(int64_t x)   { return double_to_i64(tan(i64_to_double(x))); }
int64_t freak_llvm_math_floor(int64_t x) { return double_to_i64(floor(i64_to_double(x))); }
int64_t freak_llvm_math_ceil(int64_t x)  { return double_to_i64(ceil(i64_to_double(x))); }

/**
 * Parses a null-terminated numeric string as a double.
 * @param w Pointer to the null-terminated numeric string.
 * @returns Parsed double bits packed into the universal integer ABI.
 */
int64_t freak_llvm_parse_num(int64_t w) {
    return double_to_i64(strtod((const char*)w, NULL));
}
/**
 * Formats a packed double value as a decimal string.
 * @param n IEEE-754 double bits carried in the universal integer ABI.
 * @return Newly allocated, owned word containing the formatted number.
 */
int64_t freak_llvm_format_num(int64_t n) {
    char* buf = (char*)malloc(64);
    if (!buf) {
        fprintf(stderr, "FREAK: out of memory formatting a number\n");
        exit(1);
    }
    snprintf(buf, 64, "%.10g", i64_to_double(n));
    return freak_llvm_word_adopt((int64_t)buf);
}

/* ── Num (double) helpers ──────────────────────────── */
/* Doubles are stored as bitcast i64 in FREAK LLVM IR.  */
/* These helpers reinterpret the bits.                    */

/* freak_llvm_word_from_num, print_num, int_to_num, num_to_int, word_compare
   are now pure LLVM IR intrinsics. */

/* ── Dynamic Arrays ────────────────────────────────── */
/* freak_array_new, push, get, len, set are now pure LLVM IR intrinsics
   using a global pool defined in the emitted .ll file. */

/* ── TCP Socket primitives ─────────────────────────── */

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
static int freak_wsa_inited = 0;
static void freak_wsa_init(void) {
    if (!freak_wsa_inited) {
        WSADATA wsa;
        WSAStartup(MAKEWORD(2,2), &wsa);
        freak_wsa_inited = 1;
    }
}
#else
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#endif

/* freak_tcp_connect(host_ptr, port) -> socket fd (or -1 on error) */
int64_t freak_llvm_tcp_connect(int64_t host_ptr, int64_t port) {
    char* host = (char*)host_ptr;
#ifdef _WIN32
    freak_wsa_init();
    SOCKET sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (sock == INVALID_SOCKET) return -1;
#else
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) return -1;
#endif

    struct addrinfo hints, *res;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;
    char port_str[16];
    snprintf(port_str, 16, "%lld", (long long)port);
    if (getaddrinfo(host, port_str, &hints, &res) != 0) {
#ifdef _WIN32
        closesocket(sock);
#else
        close(sock);
#endif
        return -1;
    }
    int rc = connect((int)sock, res->ai_addr, (int)res->ai_addrlen);
    freeaddrinfo(res);
    if (rc != 0) {
#ifdef _WIN32
        closesocket(sock);
#else
        close(sock);
#endif
        return -1;
    }
    return (int64_t)sock;
}

/* freak_tcp_send(fd, data_ptr) -> bytes sent (or -1) */
int64_t freak_llvm_tcp_send(int64_t fd, int64_t data_ptr) {
    char* data = (char*)data_ptr;
    int len = (int)strlen(data);
#ifdef _WIN32
    return (int64_t)send((SOCKET)fd, data, len, 0);
#else
    return (int64_t)send((int)fd, data, len, 0);
#endif
}

/* freak_tcp_recv(fd, max_bytes) -> string pointer (caller-owned) */
int64_t freak_llvm_tcp_recv(int64_t fd, int64_t max_bytes) {
    int bufsz = (int)max_bytes;
    if (bufsz <= 0) bufsz = 4096;
    char* buf = malloc(bufsz + 1);
    if (!buf) return (int64_t)"";
#ifdef _WIN32
    int n = recv((SOCKET)fd, buf, bufsz, 0);
#else
    int n = recv((int)fd, buf, bufsz, 0);
#endif
    if (n <= 0) { free(buf); return (int64_t)""; }
    buf[n] = '\0';
    return freak_llvm_word_adopt((int64_t)buf);
}

/* freak_tcp_recv_all(fd, max_bytes) -> read until connection closes */
int64_t freak_llvm_tcp_recv_all(int64_t fd, int64_t max_bytes) {
    int bufsz = (int)max_bytes;
    if (bufsz <= 0) bufsz = 65536;
    char* buf = malloc(bufsz + 1);
    if (!buf) return (int64_t)"";
    int total = 0;
    while (total < bufsz) {
#ifdef _WIN32
        int n = recv((SOCKET)fd, buf + total, bufsz - total, 0);
#else
        int n = recv((int)fd, buf + total, bufsz - total, 0);
#endif
        if (n <= 0) break;
        total += n;
    }
    buf[total] = '\0';
    return freak_llvm_word_adopt((int64_t)buf);
}

/* freak_tcp_close(fd) -> void */
void freak_llvm_tcp_close(int64_t fd) {
#ifdef _WIN32
    closesocket((SOCKET)fd);
#else
    close((int)fd);
#endif
}

int64_t freak_llvm_shape_alloc(int64_t field_count) {
    if (field_count <= 0) {
        field_count = 1;
    }
    int64_t* fields = (int64_t*)calloc((size_t)field_count, sizeof(int64_t));
    if (!fields) {
        fprintf(stderr, "FREAK: OOM allocating shape\n");
        exit(1);
    }
    return (int64_t)fields;
}

int64_t freak_llvm_shape_get(int64_t shape_handle, int64_t field_index) {
    int64_t* fields = (int64_t*)shape_handle;
    if (!fields || field_index < 0) {
        return 0;
    }
    return fields[field_index];
}

void freak_llvm_shape_set(int64_t shape_handle, int64_t field_index, int64_t value) {
    int64_t* fields = (int64_t*)shape_handle;
    if (!fields || field_index < 0) {
        return;
    }
    fields[field_index] = value;
}

int64_t freak_llvm_process_exec(int64_t cmd_p) {
    const char* cmd = (const char*)cmd_p;
    if (!cmd) {
        return -1;
    }
    return freak_llvm_normalize_process_status(system(cmd));
}

/* ── Entry point setup ──────────────────────────────── */
/* freak_llvm_setup_args is now a pure LLVM IR intrinsic. */
