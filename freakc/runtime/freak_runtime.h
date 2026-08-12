#pragma once

/*
 * FREAK Lite Runtime — C runtime support for the FREAK->C transpiler.
 *
 * Every emitted .c file includes this header.  The implementation lives in
 * freak_runtime.c which must be compiled and linked alongside the generated
 * code.
 */

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* ------------------------------------------------------------------ */
/*  Runtime bootstrap globals                                         */
/* ------------------------------------------------------------------ */

/* Populated by generated main() before freak_main() runs. */
extern int freak_argc;
extern char** freak_argv;

/* Enable ANSI escape sequences on Windows (no-op on other platforms). */
void freak_enable_ansi(void);

/* ------------------------------------------------------------------ */
/*  word type (UTF-8 string)                                          */
/* ------------------------------------------------------------------ */

typedef struct {
    const char* data;
    size_t length;       /* byte length   */
    size_t char_count;   /* codepoint count (== length for ASCII) */
    bool   heap;         /* runtime-owned; release only through word APIs */
} freak_word;

/* Command line arguments */
int64_t freak_args_count(void);
freak_word freak_arg(int64_t index);

#define FREAK_WORD_EMPTY { 0 }

/* Construct from a C string literal (no copy, points into rodata). */
freak_word freak_word_lit(const char* s);

/* Construct from a heap-allocated buffer (takes ownership). */
freak_word freak_word_own(char* s, size_t len);

/* Concatenate two words — allocates. */
freak_word freak_word_concat(freak_word a, freak_word b);
freak_word freak_word_concat_consuming(freak_word a, freak_word b, bool release_a, bool release_b);

/* Compiler-internal self-replacement fast path. Appends into a private
   geometrically grown buffer without changing freak_word's public layout. */
void freak_word_append_owned(freak_word* slot, freak_word suffix, bool release_suffix);

/* Copy an existing word binding. Heap words receive independent ownership;
   literals remain shared immutable storage. */
freak_word freak_word_clone(freak_word source);

/* Evaluate the replacement first, then release the previous owned buffer.
   Pointer equality keeps direct self-assignment safe. */
void freak_word_replace_owned(freak_word* slot, freak_word replacement);

/* Release a word binding at a task boundary and clear its slot. Runtime-owned
   data must use this/replacement APIs rather than direct free(), because the
   frozen runtime tracks private ownership and append-capacity metadata. */
void freak_word_release_owned(freak_word* slot);

/* Equality test (byte-wise). */
bool freak_word_eq(freak_word a, freak_word b);

/* Get a NUL-terminated C string.  For literals this is the original
   pointer; for heap strings the data is already NUL-terminated. */
const char* freak_word_to_cstr(freak_word w);

/* Conversions to word. */
freak_word freak_word_from_int(int64_t n);
freak_word freak_word_from_double(double n);
freak_word freak_word_from_bool(bool b);
freak_word freak_char_to_word(int64_t code);

/* printf-style interpolation — returns a heap-allocated word. */
freak_word freak_interpolate(const char* fmt, ...);

/* ------------------------------------------------------------------ */
/*  I/O                                                               */
/* ------------------------------------------------------------------ */

/* Print word to stdout with trailing newline. */
void freak_say(freak_word msg);

/* Print word to stderr with trailing newline. */
void freak_say_err(freak_word msg);

/* Prompt on stdout, read a line from stdin, return as word. */
freak_word freak_ask(freak_word prompt);

/* ------------------------------------------------------------------ */
/*  Panic                                                             */
/* ------------------------------------------------------------------ */

/* Print message to stderr and exit(1). */
_Noreturn void freak_panic(freak_word msg);

/* ------------------------------------------------------------------ */
/*  std::fs — file I/O                                                */
/* ------------------------------------------------------------------ */

/* Read entire file contents as a word. Panics on failure. */
freak_word freak_fs_read(freak_word path);

/* Write word contents to a file. Panics on failure. */
void freak_fs_write(freak_word path, freak_word content);

/* Append word contents to a file. Creates if not exists. Panics on failure. */
void freak_fs_append(freak_word path, freak_word content);

/* Aliases without freak_ prefix (self-hosted compiler compatibility) */
void fs_append(freak_word path, freak_word content);
bool fs_exists(freak_word path);
void fs_delete(freak_word path);

bool freak_fs_exists(freak_word path);
int64_t freak_path_exists(int64_t path);
bool freak_internal_delete_file_checked(freak_word path);
void freak_fs_delete(freak_word path);
void freak_fs_make_dir(freak_word path);
freak_word freak_fs_list_dir(freak_word path);

/* ------------------------------------------------------------------ */
/*  Numeric helpers                                                   */
/* ------------------------------------------------------------------ */

int64_t freak_abs_int(int64_t x);
double  freak_abs_double(double x);
int64_t freak_clamp_int(int64_t x, int64_t lo, int64_t hi);
double  freak_clamp_double(double x, double lo, double hi);
int64_t freak_pow_int(int64_t base, int64_t exp);

/* ------------------------------------------------------------------ */
/*  std::time                                                         */
/* ------------------------------------------------------------------ */

int64_t freak_time_now_ms(void);
void    freak_time_sleep(int64_t ms);

/* ------------------------------------------------------------------ */
/*  std::math                                                         */
/* ------------------------------------------------------------------ */

double  freak_math_sin(double x);
double  freak_math_cos(double x);
double  freak_math_tan(double x);
double  freak_math_sqrt(double x);
double  freak_math_pow(double base, double exp);
double  freak_math_floor(double x);
double  freak_math_ceil(double x);
int64_t freak_math_random_int(int64_t min_val, int64_t max_val);
double  freak_math_random_float(void);

/* ------------------------------------------------------------------ */
/*  Closures                                                          */
/* ------------------------------------------------------------------ */

/* A closure is a function pointer + captured environment pointer.
   The emitter generates typed wrapper structs per closure signature,
   but the generic form is used for storage/passing. */
typedef struct {
    void* fn;    /* pointer to the generated static function */
    void* env;   /* pointer to the generated capture struct  */
} freak_closure;

/* ------------------------------------------------------------------ */
/*  Maybe<T> and Result<T,E> generator macros                         */
/* ------------------------------------------------------------------ */

/* Generate a maybe type for a given C type.
   Usage: FREAK_MAYBE_DECL(int64_t, int)
   Produces: typedef struct { bool has_value; int64_t value; } freak_maybe_int; */
#define FREAK_MAYBE_DECL(CType, Suffix) \
    typedef struct { \
        bool has_value; \
        CType value; \
    } freak_maybe_##Suffix

/* Generate a result type for given ok/err C types.
   Usage: FREAK_RESULT_DECL(int64_t, freak_word, int_word)
   Produces: typedef struct { bool is_ok; union { int64_t ok_val; freak_word err_val; } data; } freak_result_int_word; */
#define FREAK_RESULT_DECL(OkType, ErrType, Suffix) \
    typedef struct { \
        bool is_ok; \
        union { OkType ok_val; ErrType err_val; } data; \
    } freak_result_##Suffix

/* Pre-generated common maybe types */
FREAK_MAYBE_DECL(int64_t,    int);
FREAK_MAYBE_DECL(double,     num);
FREAK_MAYBE_DECL(freak_word, word);
FREAK_MAYBE_DECL(bool,       bool);

/* Pre-generated common result types (error is always freak_word) */
FREAK_RESULT_DECL(int64_t,    freak_word, int_word);
FREAK_RESULT_DECL(double,     freak_word, num_word);
FREAK_RESULT_DECL(freak_word, freak_word, word_word);
FREAK_RESULT_DECL(bool,       freak_word, bool_word);

/* ------------------------------------------------------------------ */
/*  String methods                                                    */
/* ------------------------------------------------------------------ */

/* Length in characters (codepoints). */
int64_t freak_word_length(freak_word w);

/* Case conversion — allocates new word. */
freak_word freak_word_to_upper(freak_word w);
freak_word freak_word_to_lower(freak_word w);

/* Substring tests. */
bool freak_word_contains(freak_word haystack, freak_word needle);
bool freak_word_starts_with(freak_word w, freak_word prefix);
bool freak_word_ends_with(freak_word w, freak_word suffix);

/* Trim whitespace from both ends — allocates. */
freak_word freak_word_trim(freak_word w);

/* Replace all occurrences of old with new — allocates. */
freak_word freak_word_replace(freak_word w, freak_word old_s, freak_word new_s);

/* Get character at index (0-based) as a single-char word. */
freak_word freak_word_char_at(freak_word w, int64_t index);

/* Stable, allocation-free FNV-1a checksum for persisted compiler data. */
int64_t freak_word_checksum(freak_word w);

/* Linear-time wire-format helpers used by compiler snapshots. Each returned
   word is produced with at most one allocation. */
freak_word freak_word_snapshot_escape(freak_word w);
freak_word freak_word_snapshot_unescape(freak_word w);
int64_t freak_word_snapshot_line_count(freak_word w);
freak_word freak_word_snapshot_line(freak_word w, int64_t wanted);
int64_t freak_word_snapshot_field_count(freak_word w);
freak_word freak_word_snapshot_field_raw(freak_word w, int64_t wanted);

/* Get a substring from start (inclusive) with given length. */
freak_word freak_word_substring(freak_word w, int64_t start, int64_t len);

/* Conversions from word to number. */
int64_t freak_word_to_int(freak_word w);
int64_t freak_word_compare(freak_word a, freak_word b);
double  freak_word_to_num(freak_word w);
double  freak_parse_num(freak_word w);
freak_word freak_format_num(double n);

/* ------------------------------------------------------------------ */
/*  std::process                                                      */
/* ------------------------------------------------------------------ */

typedef struct {
    freak_word out;
    freak_word err;
    int64_t exit_code;
    bool success;
} freak_process_output;

typedef struct {
    uint64_t pid;
} freak_process_handle;

/* run/spawn/process metadata */
freak_process_output freak_process_run(freak_word cmd, void* args /* TODO: list<word> */);
freak_process_handle freak_process_spawn(freak_word cmd, void* args /* TODO: list<word> */);
uint64_t freak_process_pid(void);
void freak_process_exit(int64_t code);
freak_word freak_process_input(void);
freak_maybe_word freak_process_env_var(freak_word name);
void freak_process_set_env(freak_word name, freak_word val);
freak_word freak_process_env(freak_word name);
void* freak_process_args(void); /* TODO: list<word> */
int64_t freak_process_args_count(void);
freak_word freak_process_arg(int64_t index);

/* Simple command execution */
int64_t freak_process_exec(freak_word cmd);
freak_word freak_process_exec_capture(freak_word cmd);

/* process handle methods */
int64_t freak_process_wait(freak_process_handle p);
bool freak_process_kill(freak_process_handle p);

/* ------------------------------------------------------------------ */
/*  std::thread                                                       */
/* ------------------------------------------------------------------ */

typedef struct {
    uint64_t id;
    bool finished;
} freak_thread_handle;

/* raw thread primitives */
freak_thread_handle freak_thread_spawn(freak_closure f);
uint64_t freak_thread_current_id(void);
void freak_thread_yield_now(void);
uint64_t freak_thread_available_parallelism(void);

/* thread handle methods */
bool freak_thread_join(freak_thread_handle h);
uint64_t freak_thread_id(freak_thread_handle h);
bool freak_thread_is_finished(freak_thread_handle h);

/* simple atomics */
typedef struct { volatile int64_t value; } freak_atomic_int;
typedef struct { volatile bool value; } freak_atomic_bool;

int64_t freak_atomic_int_load(freak_atomic_int* a);
void freak_atomic_int_store(freak_atomic_int* a, int64_t v);
int64_t freak_atomic_int_fetch_add(freak_atomic_int* a, int64_t n);
bool freak_atomic_int_compare_swap(freak_atomic_int* a, int64_t old_v, int64_t new_v);

bool freak_atomic_bool_load(freak_atomic_bool* a);
void freak_atomic_bool_store(freak_atomic_bool* a, bool v);
bool freak_atomic_bool_flip(freak_atomic_bool* a);

/* ------------------------------------------------------------------ */
/*  std::bytes                                                        */
/* ------------------------------------------------------------------ */

typedef struct {
    uint8_t* data;
    size_t length;
    size_t capacity;
    size_t cursor;
} freak_byte_buffer;

freak_byte_buffer freak_bytes_new(void);
freak_byte_buffer freak_bytes_from(void* data /* TODO: list<tiny> */);

void freak_bytes_write_byte(freak_byte_buffer* b, uint8_t v);
void freak_bytes_write_int(freak_byte_buffer* b, int64_t v);
void freak_bytes_write_int_be(freak_byte_buffer* b, int64_t v);
void freak_bytes_write_word(freak_byte_buffer* b, freak_word s);
void freak_bytes_write_bytes(freak_byte_buffer* b, const uint8_t* data, size_t n);

freak_maybe_int freak_bytes_read_byte(freak_byte_buffer* b);
freak_maybe_int freak_bytes_read_int(freak_byte_buffer* b);
freak_maybe_word freak_bytes_read_word(freak_byte_buffer* b, uint64_t len);

void freak_bytes_seek(freak_byte_buffer* b, uint64_t pos);
uint64_t freak_bytes_position(const freak_byte_buffer* b);
uint64_t freak_bytes_length(const freak_byte_buffer* b);

void* freak_bytes_to_list(const freak_byte_buffer* b); /* TODO: list<tiny> */
freak_result_word_word freak_bytes_to_word(const freak_byte_buffer* b);

/* ------------------------------------------------------------------ */
/*  Dynamic arrays (replaces pipe-delimited string "arrays")          */
/* ------------------------------------------------------------------ */

/* Creates a new dynamic array, returns a handle (int64_t). */
int64_t freak_array_new(void);

/* Push a word onto the array. */
void freak_array_push(int64_t handle, freak_word item);
void freak_array_push_owned(int64_t handle, freak_word item);

/* Get item at index (0-based). Returns empty word if out of bounds. */
freak_word freak_array_get(int64_t handle, int64_t index);

/* Get current length of the array. */
int64_t freak_array_len(int64_t handle);

/* Set item at index. Panics if out of bounds. */
void freak_array_set(int64_t handle, int64_t index, freak_word item);
void freak_array_set_owned(int64_t handle, int64_t index, freak_word item);

/* Release an array slot so a later array_new call can reuse it with a new
   generation-tagged handle. Stale handles remain invalid. */
void freak_array_release(int64_t handle);
void freak_array_release_owned(int64_t handle);

/* Join every word in an array with one allocation and release the handle. */
freak_word freak_word_join(int64_t handle);
freak_word freak_word_join_owned(int64_t handle);

/* ------------------------------------------------------------------ */
/*  TCP Socket primitives                                             */
/* ------------------------------------------------------------------ */

int64_t freak_tcp_connect(freak_word host, int64_t port);
int64_t freak_tcp_send(int64_t fd, freak_word data);
freak_word freak_tcp_recv(int64_t fd, int64_t max_bytes);
freak_word freak_tcp_recv_all(int64_t fd, int64_t max_bytes);
void freak_tcp_close(int64_t fd);

/* ------------------------------------------------------------------ */
/*  UI Runtime Subsystem (std::ui)                                    */
/*  Implemented in freakc/runtime/ui/win32_backend.c (Windows)        */
/* ------------------------------------------------------------------ */

/* Legacy LLVM backend aliases — only declare when not already defined as macros */
#ifndef freak_llvm_ui_create_native
int64_t freak_llvm_ui_create_native(int64_t title_word, int64_t width, int64_t height);
int64_t freak_llvm_ui_poll_events(int64_t handle);
void freak_llvm_ui_begin_frame(int64_t handle);
void freak_llvm_ui_end_frame(int64_t handle);
void freak_llvm_ui_clear(int64_t handle, int64_t r, int64_t g, int64_t b, int64_t a);
void freak_llvm_ui_fill_rect(int64_t handle, int64_t x, int64_t y, int64_t w, int64_t h, int64_t r, int64_t g, int64_t b, int64_t a);
#endif

/* Phase MA: Window lifecycle (accept freak_word for string params) */
int64_t freak_ui_create_window_word(freak_word title, int64_t width, int64_t height, int64_t resizable);
void    freak_ui_show_window(int64_t handle);
void    freak_ui_set_title_word(int64_t handle, freak_word title);
int64_t freak_ui_window_should_close(int64_t handle);
void    freak_ui_destroy_window(int64_t handle);

/* Phase MA: Event loop */
int64_t freak_ui_poll_events(int64_t handle);
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

/* Phase MA: Frame control */
void freak_ui_begin_frame(int64_t handle);
void freak_ui_end_frame(int64_t handle);

/* Phase MA: Drawing */
void freak_ui_clear(int64_t handle, int64_t r, int64_t g, int64_t b, int64_t a);
void freak_ui_fill_rect(int64_t handle, int64_t x, int64_t y, int64_t w, int64_t h,
                        int64_t r, int64_t g, int64_t b, int64_t a);
void freak_ui_stroke_rect(int64_t handle, int64_t x, int64_t y, int64_t w, int64_t h,
                          int64_t r, int64_t g, int64_t b, int64_t a, int64_t thickness);
void freak_ui_fill_circle(int64_t handle, int64_t cx, int64_t cy, int64_t radius,
                          int64_t r, int64_t g, int64_t b, int64_t a);
void freak_ui_draw_line(int64_t handle, int64_t x1, int64_t y1, int64_t x2, int64_t y2,
                        int64_t r, int64_t g, int64_t b, int64_t a, int64_t thickness);
int64_t freak_ui_draw_text_word(int64_t handle, freak_word text, int64_t x, int64_t y,
                                int64_t r, int64_t g, int64_t b, int64_t font_size,
                                int64_t bold, int64_t italic);
int64_t freak_ui_get_width(int64_t handle);
int64_t freak_ui_get_height(int64_t handle);
int64_t freak_ui_measure_text_word(freak_word text, int64_t font_size, int64_t bold, int64_t italic);
