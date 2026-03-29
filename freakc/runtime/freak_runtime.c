#ifndef _WIN32
#define _POSIX_C_SOURCE 200809L
#endif

#include "freak_runtime.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <time.h>
#include <math.h>
#include <sys/stat.h>

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")
#include <windows.h>
#include <io.h>
#include <direct.h>
#else
#include <sys/time.h>
#include <unistd.h>
#include <dirent.h>
#define _strdup strdup
#endif

/* runtime bootstrap globals (set by generated main) */
int freak_argc = 0;
char** freak_argv = NULL;

int64_t freak_args_count(void) {
    return (int64_t)freak_argc;
}

freak_word freak_arg(int64_t index) {
    if (index < 0 || index >= freak_argc) {
        freak_panic(freak_word_lit("Argument index out of bounds"));
    }
    return freak_word_lit(freak_argv[index]);
}

/* ------------------------------------------------------------------ */
/*  word helpers                                                      */
/* ------------------------------------------------------------------ */

freak_word freak_word_lit(const char* s) {
    size_t len = strlen(s);
    freak_word w;
    w.data       = s;
    w.length     = len;
    w.char_count = len;   /* ASCII assumption for now */
    w.heap       = false;
    return w;
}

freak_word freak_word_own(char* s, size_t len) {
    freak_word w;
    w.data       = s;
    w.length     = len;
    w.char_count = len;
    w.heap       = true;
    return w;
}

freak_word freak_word_concat(freak_word a, freak_word b) {
    size_t total = a.length + b.length;
    char* buf = (char*)malloc(total + 1);
    if (!buf) { fprintf(stderr, "FREAK: out of memory\n"); exit(1); }
    memcpy(buf, a.data, a.length);
    memcpy(buf + a.length, b.data, b.length);
    buf[total] = '\0';
    return freak_word_own(buf, total);
}

bool freak_word_eq(freak_word a, freak_word b) {
    if (a.length != b.length) return false;
    return memcmp(a.data, b.data, a.length) == 0;
}

const char* freak_word_to_cstr(freak_word w) {
    /* Literals are NUL-terminated by the compiler; heap strings are
       NUL-terminated by freak_word_own / freak_interpolate. */
    return w.data;
}

/* ------------------------------------------------------------------ */
/*  Conversions to word                                               */
/* ------------------------------------------------------------------ */

freak_word freak_word_from_int(int64_t n) {
    char* buf = (char*)malloc(32);
    if (!buf) { fprintf(stderr, "FREAK: out of memory\n"); exit(1); }
    int len = snprintf(buf, 32, "%lld", (long long)n);
    if (len < 0) len = 0;
    return freak_word_own(buf, (size_t)len);
}

freak_word freak_word_from_double(double n) {
    char* buf = (char*)malloc(64);
    if (!buf) { fprintf(stderr, "FREAK: out of memory\n"); exit(1); }
    int len = snprintf(buf, 64, "%g", n);
    if (len < 0) len = 0;
    return freak_word_own(buf, (size_t)len);
}

freak_word freak_word_from_bool(bool b) {
    return freak_word_lit(b ? "true" : "false");
}

/* ------------------------------------------------------------------ */
/*  Interpolation                                                     */
/* ------------------------------------------------------------------ */

freak_word freak_interpolate(const char* fmt, ...) {
    va_list args, args_copy;
    va_start(args, fmt);
    va_copy(args_copy, args);

    /* First pass: determine required size. */
    int needed = vsnprintf(NULL, 0, fmt, args);
    va_end(args);

    if (needed < 0) {
        va_end(args_copy);
        return freak_word_lit("");
    }

    char* buf = (char*)malloc((size_t)needed + 1);
    if (!buf) { fprintf(stderr, "FREAK: out of memory\n"); exit(1); }

    vsnprintf(buf, (size_t)needed + 1, fmt, args_copy);
    va_end(args_copy);

    return freak_word_own(buf, (size_t)needed);
}

/* ------------------------------------------------------------------ */
/*  I/O                                                               */
/* ------------------------------------------------------------------ */

void freak_say(freak_word msg) {
    fwrite(msg.data, 1, msg.length, stdout);
    fputc('\n', stdout);
    fflush(stdout);
}

void freak_say_err(freak_word msg) {
    fwrite(msg.data, 1, msg.length, stderr);
    fputc('\n', stderr);
}

freak_word freak_ask(freak_word prompt) {
    /* Print the prompt (no newline). */
    fwrite(prompt.data, 1, prompt.length, stdout);
    fflush(stdout);

    char* line = NULL;
    size_t cap  = 0;
    size_t len  = 0;
    int    ch;
    while ((ch = fgetc(stdin)) != EOF && ch != '\n') {
        if (len + 1 >= cap) {
            cap = cap ? cap * 2 : 128;
            line = (char*)realloc(line, cap);
            if (!line) { fprintf(stderr, "FREAK: out of memory\n"); exit(1); }
        }
        line[len++] = (char)ch;
    }
    if (!line) {
        line = (char*)malloc(1);
        if (!line) { fprintf(stderr, "FREAK: out of memory\n"); exit(1); }
    }
    line[len] = '\0';
    return freak_word_own(line, len);
}

/* ------------------------------------------------------------------ */
/*  Panic                                                             */
/* ------------------------------------------------------------------ */

_Noreturn void freak_panic(freak_word msg) {
    fprintf(stderr, "PANIC: ");
    fwrite(msg.data, 1, msg.length, stderr);
    fputc('\n', stderr);
    exit(1);
}

/* ------------------------------------------------------------------ */
/*  std::fs — file I/O                                                */
/* ------------------------------------------------------------------ */

freak_word freak_fs_read(freak_word path) {
    const char* p = freak_word_to_cstr(path);
    FILE* f = fopen(p, "rb");
    if (!f) {
        fprintf(stderr, "FREAK: cannot open file '%s': %s\n", p, strerror(errno));
        exit(1);
    }
    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);
    char* buf = (char*)malloc((size_t)size + 1);
    if (!buf) { fprintf(stderr, "FREAK: out of memory\n"); fclose(f); exit(1); }
    size_t read = fread(buf, 1, (size_t)size, f);
    fclose(f);
    buf[read] = '\0';
    return freak_word_own(buf, read);
}

void freak_fs_write(freak_word path, freak_word content) {
    const char* p = freak_word_to_cstr(path);
    FILE* f = fopen(p, "wb");
    if (!f) {
        fprintf(stderr, "FREAK: cannot write file '%s': %s\n", p, strerror(errno));
        exit(1);
    }
    fwrite(content.data, 1, content.length, f);
    fclose(f);
}

void freak_fs_append(freak_word path, freak_word content) {
    const char* p = freak_word_to_cstr(path);
    FILE* f = fopen(p, "ab");
    if (!f) {
        fprintf(stderr, "FREAK: cannot append file '%s': %s\n", p, strerror(errno));
        exit(1);
    }
    fwrite(content.data, 1, content.length, f);
    fclose(f);
}

bool freak_fs_exists(freak_word path) {
    const char* p = freak_word_to_cstr(path);
#ifdef _WIN32
    return _access(p, 0) == 0;
#else
    return access(p, F_OK) == 0;
#endif
}

void freak_fs_delete(freak_word path) {
    const char* p = freak_word_to_cstr(path);
    remove(p); /* ignore errors for now */
}

/* Aliases without freak_ prefix — the self-hosted compiler's generic
   call handler emits fs_append/fs_exists/fs_delete (no prefix) for
   builtins it doesn't explicitly know about. */
void fs_append(freak_word path, freak_word content) { freak_fs_append(path, content); }
bool fs_exists(freak_word path) { return freak_fs_exists(path); }
void fs_delete(freak_word path) { freak_fs_delete(path); }

void freak_fs_make_dir(freak_word path) {
    const char* p = freak_word_to_cstr(path);
#ifdef _WIN32
    _mkdir(p);
#else
    mkdir(p, 0777);
#endif
}

freak_word freak_fs_list_dir(freak_word path) {
    const char* p = freak_word_to_cstr(path);
    freak_word result = freak_word_lit("");
#ifdef _WIN32
    WIN32_FIND_DATAA fd;
    char search_path[1024];
    snprintf(search_path, sizeof(search_path), "%s\\*", p);
    HANDLE hFind = FindFirstFileA(search_path, &fd);
    if (hFind != INVALID_HANDLE_VALUE) {
        do {
            if (strcmp(fd.cFileName, ".") != 0 && strcmp(fd.cFileName, "..") != 0) {
                if (result.length > 0) result = freak_word_concat(result, freak_word_lit("|"));
                result = freak_word_concat(result, freak_word_lit(fd.cFileName));
            }
        } while (FindNextFileA(hFind, &fd));
        FindClose(hFind);
    }
#else
    DIR* dir = opendir(p);
    if (dir) {
        struct dirent* ent;
        while ((ent = readdir(dir)) != NULL) {
            if (strcmp(ent->d_name, ".") != 0 && strcmp(ent->d_name, "..") != 0) {
                if (result.length > 0) result = freak_word_concat(result, freak_word_lit("|"));
                result = freak_word_concat(result, freak_word_lit(ent->d_name));
            }
        }
        closedir(dir);
    }
#endif
    return result;
}

/* ------------------------------------------------------------------ */
/*  Numeric helpers                                                   */
/* ------------------------------------------------------------------ */

int64_t freak_abs_int(int64_t x) {
    return x < 0 ? -x : x;
}

double freak_abs_double(double x) {
    return x < 0.0 ? -x : x;
}

int64_t freak_clamp_int(int64_t x, int64_t lo, int64_t hi) {
    if (x < lo) return lo;
    if (x > hi) return hi;
    return x;
}

double freak_clamp_double(double x, double lo, double hi) {
    if (x < lo) return lo;
    if (x > hi) return hi;
    return x;
}

int64_t freak_pow_int(int64_t base, int64_t exp) {
    int64_t result = 1;
    if (exp < 0) return 0;  /* integer pow with neg exp → 0 */
    while (exp > 0) {
        if (exp & 1) result *= base;
        base *= base;
        exp >>= 1;
    }
    return result;
}

/* ------------------------------------------------------------------ */
/*  std::time                                                         */
/* ------------------------------------------------------------------ */

int64_t freak_time_now_ms(void) {
#ifdef _WIN32
    FILETIME ft;
    GetSystemTimeAsFileTime(&ft);
    uint64_t time_100ns = ((uint64_t)ft.dwHighDateTime << 32) | ft.dwLowDateTime;
    /* Convert from 100ns intervals since Jan 1, 1601 to ms since Jan 1, 1970 */
    return (int64_t)((time_100ns - 116444736000000000ULL) / 10000);
#else
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (int64_t)(tv.tv_sec) * 1000 + (int64_t)(tv.tv_usec) / 1000;
#endif
}

void freak_time_sleep(int64_t ms) {
    if (ms <= 0) return;
#ifdef _WIN32
    Sleep((DWORD)ms);
#else
    struct timespec ts;
    ts.tv_sec = ms / 1000;
    ts.tv_nsec = (ms % 1000) * 1000000;
    nanosleep(&ts, NULL);
#endif
}

/* ------------------------------------------------------------------ */
/*  std::math                                                         */
/* ------------------------------------------------------------------ */

double freak_math_sin(double x) { return sin(x); }
double freak_math_cos(double x) { return cos(x); }
double freak_math_tan(double x) { return tan(x); }
double freak_math_sqrt(double x) { return sqrt(x); }
double freak_math_pow(double base, double exp) { return pow(base, exp); }
double freak_math_floor(double x) { return floor(x); }
double freak_math_ceil(double x) { return ceil(x); }

int64_t freak_math_random_int(int64_t min_val, int64_t max_val) {
    if (min_val >= max_val) return min_val;
    /* Basic rand() is not great, but sufficient for standard lib default */
    int64_t r = rand();
    return min_val + (r % (max_val - min_val));
}

double freak_math_random_float(void) {
    return (double)rand() / (double)RAND_MAX;
}

/* ------------------------------------------------------------------ */
/*  String methods                                                    */
/* ------------------------------------------------------------------ */

#include <ctype.h>

int64_t freak_word_length(freak_word w) {
    return (int64_t)w.char_count;
}

freak_word freak_word_to_upper(freak_word w) {
    char* buf = (char*)malloc(w.length + 1);
    if (!buf) { fprintf(stderr, "FREAK: out of memory\n"); exit(1); }
    for (size_t i = 0; i < w.length; i++) {
        buf[i] = (char)toupper((unsigned char)w.data[i]);
    }
    buf[w.length] = '\0';
    return freak_word_own(buf, w.length);
}

freak_word freak_word_to_lower(freak_word w) {
    char* buf = (char*)malloc(w.length + 1);
    if (!buf) { fprintf(stderr, "FREAK: out of memory\n"); exit(1); }
    for (size_t i = 0; i < w.length; i++) {
        buf[i] = (char)tolower((unsigned char)w.data[i]);
    }
    buf[w.length] = '\0';
    return freak_word_own(buf, w.length);
}

bool freak_word_contains(freak_word haystack, freak_word needle) {
    if (needle.length == 0) return true;
    if (needle.length > haystack.length) return false;
    for (size_t i = 0; i <= haystack.length - needle.length; i++) {
        if (memcmp(haystack.data + i, needle.data, needle.length) == 0) {
            return true;
        }
    }
    return false;
}

bool freak_word_starts_with(freak_word w, freak_word prefix) {
    if (prefix.length > w.length) return false;
    return memcmp(w.data, prefix.data, prefix.length) == 0;
}

bool freak_word_ends_with(freak_word w, freak_word suffix) {
    if (suffix.length > w.length) return false;
    return memcmp(w.data + w.length - suffix.length, suffix.data, suffix.length) == 0;
}

freak_word freak_word_trim(freak_word w) {
    size_t start = 0;
    while (start < w.length && isspace((unsigned char)w.data[start])) start++;
    size_t end = w.length;
    while (end > start && isspace((unsigned char)w.data[end - 1])) end--;
    size_t new_len = end - start;
    char* buf = (char*)malloc(new_len + 1);
    if (!buf) { fprintf(stderr, "FREAK: out of memory\n"); exit(1); }
    memcpy(buf, w.data + start, new_len);
    buf[new_len] = '\0';
    return freak_word_own(buf, new_len);
}

freak_word freak_word_replace(freak_word w, freak_word old_s, freak_word new_s) {
    if (old_s.length == 0) return w;
    if (w.length < old_s.length) {
        char* buf = (char*)malloc(w.length + 1);
        if (!buf) { fprintf(stderr, "FREAK: out of memory\n"); exit(1); }
        memcpy(buf, w.data, w.length);
        buf[w.length] = '\0';
        return freak_word_own(buf, w.length);
    }
    /* Count occurrences */
    size_t count = 0;
    for (size_t i = 0; i <= w.length - old_s.length; i++) {
        if (memcmp(w.data + i, old_s.data, old_s.length) == 0) {
            count++;
            i += old_s.length - 1;
        }
    }
    if (count == 0) {
        char* buf = (char*)malloc(w.length + 1);
        if (!buf) { fprintf(stderr, "FREAK: out of memory\n"); exit(1); }
        memcpy(buf, w.data, w.length);
        buf[w.length] = '\0';
        return freak_word_own(buf, w.length);
    }
    size_t new_len = w.length + count * (new_s.length - old_s.length);
    char* buf = (char*)malloc(new_len + 1);
    if (!buf) { fprintf(stderr, "FREAK: out of memory\n"); exit(1); }
    size_t j = 0;
    for (size_t i = 0; i < w.length; ) {
        if (i + old_s.length <= w.length &&
            memcmp(w.data + i, old_s.data, old_s.length) == 0) {
            memcpy(buf + j, new_s.data, new_s.length);
            j += new_s.length;
            i += old_s.length;
        } else {
            buf[j++] = w.data[i++];
        }
    }
    buf[new_len] = '\0';
    return freak_word_own(buf, new_len);
}

freak_word freak_word_char_at(freak_word w, int64_t index) {
    if (index < 0 || (size_t)index >= w.length) {
        return freak_word_lit("");
    }
    char* buf = (char*)malloc(2);
    if (!buf) { fprintf(stderr, "FREAK: out of memory\n"); exit(1); }
    buf[0] = w.data[index];
    buf[1] = '\0';
    return freak_word_own(buf, 1);
}

freak_word freak_word_substring(freak_word w, int64_t start, int64_t len) {
    if (start < 0 || (size_t)start >= w.length || len <= 0) {
        return freak_word_lit("");
    }
    if ((size_t)(start + len) > w.length) {
        len = (int64_t)(w.length - (size_t)start);
    }
    char* buf = (char*)malloc((size_t)len + 1);
    if (!buf) { fprintf(stderr, "FREAK: out of memory\n"); exit(1); }
    memcpy(buf, w.data + start, (size_t)len);
    buf[len] = '\0';
    return freak_word_own(buf, (size_t)len);
}

int64_t freak_word_to_int(freak_word w) {
    return strtoll(w.data, NULL, 10);
}

int64_t freak_word_compare(freak_word a, freak_word b) {
    int r = strcmp(a.data, b.data);
    if (r < 0) return -1;
    if (r > 0) return 1;
    return 0;
}

double freak_word_to_num(freak_word w) {
    return strtod(w.data, NULL);
}

double freak_parse_num(freak_word w) {
    return strtod(w.data, NULL);
}

freak_word freak_format_num(double n) {
    static char buf[64];
    snprintf(buf, sizeof(buf), "%.10g", n);
    return freak_word_lit(buf);
}

/* ------------------------------------------------------------------ */
/*  std::process                                                      */
/* ------------------------------------------------------------------ */

freak_process_output freak_process_run(freak_word cmd, void* args) {
    (void)args;
    freak_process_output out;
    const char* cmd_str = freak_word_to_cstr(cmd);

    /* Capture stdout via popen */
    #ifdef _WIN32
    FILE* fp = _popen(cmd_str, "r");
    #else
    FILE* fp = popen(cmd_str, "r");
    #endif

    if (!fp) {
        out.out = freak_word_lit("");
        out.err = freak_word_lit("Failed to execute command");
        out.exit_code = -1;
        out.success = false;
        return out;
    }

    /* Read all output */
    size_t cap = 4096;
    size_t len = 0;
    char* buf = (char*)malloc(cap);
    size_t n;
    while ((n = fread(buf + len, 1, cap - len - 1, fp)) > 0) {
        len += n;
        if (len + 1 >= cap) {
            cap *= 2;
            buf = (char*)realloc(buf, cap);
        }
    }
    buf[len] = '\0';

    #ifdef _WIN32
    int status = _pclose(fp);
    #else
    int status = pclose(fp);
    #endif

    out.out = freak_word_own(buf, len);
    out.err = freak_word_lit("");
    out.exit_code = (int64_t)status;
    out.success = (status == 0);
    return out;
}

/* Simple exec: run command, return exit code */
int64_t freak_process_exec(freak_word cmd) {
    const char* cmd_str = freak_word_to_cstr(cmd);
    return (int64_t)system(cmd_str);
}

/* Exec and capture stdout */
freak_word freak_process_exec_capture(freak_word cmd) {
    freak_process_output r = freak_process_run(cmd, NULL);
    return r.out;
}

freak_process_handle freak_process_spawn(freak_word cmd, void* args) {
    (void)cmd;
    (void)args;
    freak_process_handle h;
    h.pid = 0;
    return h;
}

uint64_t freak_process_pid(void) {
#if defined(_WIN32)
    return 0;
#else
    return (uint64_t)0;
#endif
}

void freak_process_exit(int64_t code) {
    exit((int)code);
}

freak_word freak_process_input(void) {
    return freak_ask(freak_word_lit(""));
}

freak_maybe_word freak_process_env_var(freak_word name) {
    freak_maybe_word r;
    const char* key = freak_word_to_cstr(name);
    const char* val = key ? getenv(key) : NULL;
    if (val) {
        r.has_value = true;
        r.value = freak_word_lit(val);
    } else {
        r.has_value = false;
        r.value = freak_word_lit("");
    }
    return r;
}

void freak_process_set_env(freak_word name, freak_word val) {
    (void)name;
    (void)val;
    /* Minimal cross-platform stub: no-op for now. */
}

freak_word freak_process_env(freak_word name) {
    const char* key = freak_word_to_cstr(name);
    const char* val = key ? getenv(key) : NULL;
    if (val) return freak_word_lit(val);
    return freak_word_lit("");
}

void* freak_process_args(void) {
    return (void*)freak_argv;
}

int64_t freak_process_wait(freak_process_handle p) {
    (void)p;
    return -1;
}

bool freak_process_kill(freak_process_handle p) {
    (void)p;
    return false;
}

/* ------------------------------------------------------------------ */
/*  std::thread                                                       */
/* ------------------------------------------------------------------ */

freak_thread_handle freak_thread_spawn(freak_closure f) {
    (void)f;
    freak_thread_handle h;
    h.id = 0;
    h.finished = true;
    return h;
}

uint64_t freak_thread_current_id(void) {
    return 0;
}

void freak_thread_yield_now(void) {
    /* Minimal stub: no scheduler hint available without platform APIs. */
}

uint64_t freak_thread_available_parallelism(void) {
    return 1;
}

bool freak_thread_join(freak_thread_handle h) {
    (void)h;
    return true;
}

uint64_t freak_thread_id(freak_thread_handle h) {
    return h.id;
}

bool freak_thread_is_finished(freak_thread_handle h) {
    return h.finished;
}

int64_t freak_atomic_int_load(freak_atomic_int* a) {
    return a ? a->value : 0;
}

void freak_atomic_int_store(freak_atomic_int* a, int64_t v) {
    if (a) a->value = v;
}

int64_t freak_atomic_int_fetch_add(freak_atomic_int* a, int64_t n) {
    if (!a) return 0;
    int64_t old = a->value;
    a->value += n;
    return old;
}

bool freak_atomic_int_compare_swap(freak_atomic_int* a, int64_t old_v, int64_t new_v) {
    if (!a) return false;
    if (a->value == old_v) {
        a->value = new_v;
        return true;
    }
    return false;
}

bool freak_atomic_bool_load(freak_atomic_bool* a) {
    return a ? a->value : false;
}

void freak_atomic_bool_store(freak_atomic_bool* a, bool v) {
    if (a) a->value = v;
}

bool freak_atomic_bool_flip(freak_atomic_bool* a) {
    if (!a) return false;
    a->value = !a->value;
    return a->value;
}

/* ------------------------------------------------------------------ */
/*  std::bytes                                                        */
/* ------------------------------------------------------------------ */

static void freak_bytes_ensure_capacity(freak_byte_buffer* b, size_t needed) {
    if (!b) return;
    if (b->capacity >= needed) return;
    size_t new_cap = b->capacity ? b->capacity : 16;
    while (new_cap < needed) new_cap *= 2;
    uint8_t* n = (uint8_t*)realloc(b->data, new_cap);
    if (!n) {
        fprintf(stderr, "FREAK: out of memory\n");
        exit(1);
    }
    b->data = n;
    b->capacity = new_cap;
}

freak_byte_buffer freak_bytes_new(void) {
    freak_byte_buffer b;
    b.data = NULL;
    b.length = 0;
    b.capacity = 0;
    b.cursor = 0;
    return b;
}

freak_byte_buffer freak_bytes_from(void* data) {
    (void)data;
    return freak_bytes_new();
}

void freak_bytes_write_byte(freak_byte_buffer* b, uint8_t v) {
    if (!b) return;
    freak_bytes_ensure_capacity(b, b->length + 1);
    b->data[b->length++] = v;
}

void freak_bytes_write_int(freak_byte_buffer* b, int64_t v) {
    if (!b) return;
    for (int i = 0; i < 8; i++) {
        freak_bytes_write_byte(b, (uint8_t)((uint64_t)v >> (i * 8)));
    }
}

void freak_bytes_write_int_be(freak_byte_buffer* b, int64_t v) {
    if (!b) return;
    for (int i = 7; i >= 0; i--) {
        freak_bytes_write_byte(b, (uint8_t)((uint64_t)v >> (i * 8)));
    }
}

void freak_bytes_write_word(freak_byte_buffer* b, freak_word s) {
    if (!b) return;
    freak_bytes_write_bytes(b, (const uint8_t*)s.data, s.length);
}

void freak_bytes_write_bytes(freak_byte_buffer* b, const uint8_t* data, size_t n) {
    if (!b || !data || n == 0) return;
    freak_bytes_ensure_capacity(b, b->length + n);
    memcpy(b->data + b->length, data, n);
    b->length += n;
}

freak_maybe_int freak_bytes_read_byte(freak_byte_buffer* b) {
    freak_maybe_int r;
    if (!b || b->cursor >= b->length) {
        r.has_value = false;
        r.value = 0;
        return r;
    }
    r.has_value = true;
    r.value = (int64_t)b->data[b->cursor++];
    return r;
}

freak_maybe_int freak_bytes_read_int(freak_byte_buffer* b) {
    freak_maybe_int r;
    if (!b || b->cursor + 8 > b->length) {
        r.has_value = false;
        r.value = 0;
        return r;
    }
    uint64_t acc = 0;
    for (int i = 0; i < 8; i++) {
        acc |= ((uint64_t)b->data[b->cursor++]) << (i * 8);
    }
    r.has_value = true;
    r.value = (int64_t)acc;
    return r;
}

freak_maybe_word freak_bytes_read_word(freak_byte_buffer* b, uint64_t len) {
    freak_maybe_word r;
    if (!b || b->cursor + (size_t)len > b->length) {
        r.has_value = false;
        r.value = freak_word_lit("");
        return r;
    }
    char* s = (char*)malloc((size_t)len + 1);
    if (!s) {
        fprintf(stderr, "FREAK: out of memory\n");
        exit(1);
    }
    memcpy(s, b->data + b->cursor, (size_t)len);
    s[len] = '\0';
    b->cursor += (size_t)len;
    r.has_value = true;
    r.value = freak_word_own(s, (size_t)len);
    return r;
}

void freak_bytes_seek(freak_byte_buffer* b, uint64_t pos) {
    if (!b) return;
    if (pos > b->length) pos = b->length;
    b->cursor = (size_t)pos;
}

uint64_t freak_bytes_position(const freak_byte_buffer* b) {
    return b ? (uint64_t)b->cursor : 0;
}

uint64_t freak_bytes_length(const freak_byte_buffer* b) {
    return b ? (uint64_t)b->length : 0;
}

void* freak_bytes_to_list(const freak_byte_buffer* b) {
    (void)b;
    return NULL;
}

freak_result_word_word freak_bytes_to_word(const freak_byte_buffer* b) {
    freak_result_word_word r;
    if (!b) {
        r.is_ok = false;
        r.data.err_val = freak_word_lit("null byte buffer");
        return r;
    }
    char* s = (char*)malloc(b->length + 1);
    if (!s) {
        fprintf(stderr, "FREAK: out of memory\n");
        exit(1);
    }
    memcpy(s, b->data, b->length);
    s[b->length] = '\0';
    r.is_ok = true;
    r.data.ok_val = freak_word_own(s, b->length);
    return r;
}

void freak_llvm_setup_args(int64_t argc, int64_t argv) {
    freak_argc = (int)argc;
    freak_argv = (char**)argv;
}

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int64_t freak_llvm_word_from_int(int64_t n) {
    char* buf = (char*)malloc(32);
    snprintf(buf, 32, "%lld", (long long)n);
    return (int64_t)buf;
}

int64_t freak_llvm_word_from_bool(int64_t b) {
    return (int64_t)(b ? "true" : "false");
}

int64_t freak_llvm_word_concat(int64_t a, int64_t b) {
    const char* sa = (const char*)a;
    const char* sb = (const char*)b;
    if (!sa) sa = "";
    if (!sb) sb = "";
    size_t len = strlen(sa) + strlen(sb) + 1;
    char* buf = (char*)malloc(len);
    strcpy(buf, sa);
    strcat(buf, sb);
    return (int64_t)buf;
}

int64_t freak_llvm_word_eq(int64_t a, int64_t b) {
    const char* sa = (const char*)a;
    const char* sb = (const char*)b;
    if (!sa) sa = "";
    if (!sb) sb = "";
    return strcmp(sa, sb) == 0 ? 1 : 0;
}

int64_t freak_llvm_word_neq(int64_t a, int64_t b) {
    return 1 - freak_llvm_word_eq(a, b);
}

int64_t freak_llvm_word_length(int64_t a) {
    const char* sa = (const char*)a;
    if (!sa) return 0;
    return strlen(sa);
}

int64_t freak_llvm_word_char_at(int64_t a, int64_t idx) {
    const char* sa = (const char*)a;
    if (!sa) return (int64_t)"";
    size_t len = strlen(sa);
    if (idx < 0 || idx >= (int64_t)len) return (int64_t)"";
    char* buf = (char*)malloc(2);
    buf[0] = sa[idx];
    buf[1] = '\0';
    return (int64_t)buf;
}

int64_t freak_llvm_word_contains(int64_t a, int64_t b) {
    const char* sa = (const char*)a;
    const char* sb = (const char*)b;
    if (!sa || !sb) return 0;
    return strstr(sa, sb) != NULL ? 1 : 0;
}

int64_t freak_llvm_word_starts_with(int64_t a, int64_t b) {
    const char* sa = (const char*)a;
    const char* sb = (const char*)b;
    if (!sa || !sb) return 0;
    return strncmp(sa, sb, strlen(sb)) == 0 ? 1 : 0;
}

int64_t freak_llvm_word_ends_with(int64_t a, int64_t b) {
    const char* sa = (const char*)a;
    const char* sb = (const char*)b;
    if (!sa || !sb) return 0;
    size_t la = strlen(sa);
    size_t lb = strlen(sb);
    if (lb > la) return 0;
    return strcmp(sa + la - lb, sb) == 0 ? 1 : 0;
}

int64_t freak_llvm_word_to_upper(int64_t a) {
    const char* sa = (const char*)a;
    if (!sa) return (int64_t)"";
    char* buf = _strdup(sa);
    for (char* p = buf; *p; p++) {
        if (*p >= 'a' && *p <= 'z') *p -= 32;
    }
    return (int64_t)buf;
}

int64_t freak_llvm_word_to_lower(int64_t a) {
    const char* sa = (const char*)a;
    if (!sa) return (int64_t)"";
    char* buf = _strdup(sa);
    for (char* p = buf; *p; p++) {
        if (*p >= 'A' && *p <= 'Z') *p += 32;
    }
    return (int64_t)buf;
}

int64_t freak_llvm_word_trim(int64_t a) {
    const char* sa = (const char*)a;
    if (!sa) return (int64_t)"";
    return (int64_t)sa; // Stub implementation
}

int64_t freak_llvm_word_replace(int64_t a, int64_t b, int64_t c) {
    const char* sa = (const char*)a;
    if (!sa) return (int64_t)"";
    return (int64_t)sa; // Stub implementation
}

int64_t freak_llvm_word_to_int(int64_t a) {
    const char* sa = (const char*)a;
    if (!sa) return 0;
    return (int64_t)atoll(sa);
}

void freak_llvm_say(int64_t msg) {
    const char* s = (const char*)msg;
    if (s) puts(s);
}

void freak_llvm_print_str(int64_t msg) {
    const char* s = (const char*)msg;
    if (s) fputs(s, stdout);
}

void freak_llvm_print_int(int64_t n) {
    printf("%lld", (long long)n);
}

void freak_llvm_print_newline(void) {
    puts("");
}

int64_t freak_llvm_ask(int64_t prompt) {
    const char* p = (const char*)prompt;
    if (p) {
        fputs(p, stdout);
        fflush(stdout);
    }
    char buf[1024];
    if (fgets(buf, sizeof(buf), stdin)) {
        size_t len = strlen(buf);
        if (len > 0 && buf[len - 1] == '\n') {
            buf[len - 1] = '\0';
        }
        return (int64_t)_strdup(buf);
    }
    return (int64_t)_strdup("");
}

int64_t freak_llvm_fs_read(int64_t path) {
    const char* p = (const char*)path;
    if (!p) return (int64_t)_strdup("");
    FILE* f = fopen(p, "rb");
    if (!f) return (int64_t)_strdup("");
    fseek(f, 0, SEEK_END);
    long fsize = ftell(f);
    fseek(f, 0, SEEK_SET);
    char* string = (char*)malloc(fsize + 1);
    fread(string, 1, fsize, f);
    fclose(f);
    string[fsize] = 0;
    return (int64_t)string;
}

void freak_llvm_fs_write(int64_t path, int64_t content) {
    const char* p = (const char*)path;
    const char* c = (const char*)content;
    if (!p || !c) return;
    FILE* f = fopen(p, "wb");
    if (!f) return;
    fwrite(c, 1, strlen(c), f);
    fclose(f);
}

int64_t freak_process_args_count(void) {
    return (int64_t)freak_argc;
}

freak_word freak_process_arg(int64_t index) {
    if (index < 0 || index >= freak_argc) {
        return freak_word_lit("");
    }
    return freak_word_lit(freak_argv[index]);
}

int64_t freak_llvm_process_args_count(void) {
    return (int64_t)freak_argc;
}

int64_t freak_llvm_process_arg(int64_t index) {
    if (index < 0 || index >= freak_argc) {
        return (int64_t)_strdup("");
    }
    return (int64_t)_strdup(freak_argv[index]);
}

void freak_llvm_process_exit(int64_t code) {
    exit((int)code);
}

/* ------------------------------------------------------------------ */
/*  Dynamic arrays (replaces pipe-delimited string "arrays")          */
/* ------------------------------------------------------------------ */

typedef struct {
    freak_word* data;
    int64_t length;
    int64_t capacity;
} freak_dyn_array;

#define FREAK_MAX_ARRAYS 256
static freak_dyn_array freak_arrays[FREAK_MAX_ARRAYS];
static int64_t freak_array_count = 0;

int64_t freak_array_new(void) {
    if (freak_array_count >= FREAK_MAX_ARRAYS) {
        fprintf(stderr, "FREAK: too many arrays (max %d)\n", FREAK_MAX_ARRAYS);
        exit(1);
    }
    int64_t h = freak_array_count++;
    freak_arrays[h].length = 0;
    freak_arrays[h].capacity = 64;
    freak_arrays[h].data = (freak_word*)malloc(64 * sizeof(freak_word));
    if (!freak_arrays[h].data) {
        fprintf(stderr, "FREAK: out of memory for array\n");
        exit(1);
    }
    return h;
}

void freak_array_push(int64_t handle, freak_word item) {
    if (handle < 0 || handle >= freak_array_count) return;
    freak_dyn_array* a = &freak_arrays[handle];
    if (a->length >= a->capacity) {
        a->capacity *= 2;
        a->data = (freak_word*)realloc(a->data, (size_t)a->capacity * sizeof(freak_word));
        if (!a->data) {
            fprintf(stderr, "FREAK: out of memory growing array\n");
            exit(1);
        }
    }
    a->data[a->length++] = item;
}

freak_word freak_array_get(int64_t handle, int64_t index) {
    if (handle < 0 || handle >= freak_array_count) return freak_word_lit("");
    freak_dyn_array* a = &freak_arrays[handle];
    if (index < 0 || index >= a->length) return freak_word_lit("");
    return a->data[index];
}

int64_t freak_array_len(int64_t handle) {
    if (handle < 0 || handle >= freak_array_count) return 0;
    return freak_arrays[handle].length;
}

void freak_array_set(int64_t handle, int64_t index, freak_word item) {
    if (handle < 0 || handle >= freak_array_count) return;
    freak_dyn_array* a = &freak_arrays[handle];
    if (index < 0 || index >= a->length) {
        fprintf(stderr, "FREAK: array_set index %lld out of bounds (len %lld)\n",
                (long long)index, (long long)a->length);
        exit(1);
    }
    a->data[index] = item;
}

/* ── TCP Socket primitives ─────────────────────────── */

#ifdef _WIN32
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

int64_t freak_tcp_connect(freak_word host, int64_t port) {
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
    if (getaddrinfo(host.data, port_str, &hints, &res) != 0) {
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

int64_t freak_tcp_send(int64_t fd, freak_word data) {
    int len = (int)data.length;
#ifdef _WIN32
    return (int64_t)send((SOCKET)fd, data.data, len, 0);
#else
    return (int64_t)send((int)fd, data.data, len, 0);
#endif
}

freak_word freak_tcp_recv(int64_t fd, int64_t max_bytes) {
    int bufsz = (int)max_bytes;
    if (bufsz <= 0) bufsz = 4096;
    char* buf = malloc(bufsz + 1);
    if (!buf) return freak_word_lit("");
#ifdef _WIN32
    int n = recv((SOCKET)fd, buf, bufsz, 0);
#else
    int n = recv((int)fd, buf, bufsz, 0);
#endif
    if (n <= 0) { free(buf); return freak_word_lit(""); }
    buf[n] = '\0';
    freak_word w;
    w.data = buf;
    w.length = n;
    w.char_count = n;
    return w;
}

freak_word freak_tcp_recv_all(int64_t fd, int64_t max_bytes) {
    int bufsz = (int)max_bytes;
    if (bufsz <= 0) bufsz = 65536;
    char* buf = malloc(bufsz + 1);
    if (!buf) return freak_word_lit("");
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
    freak_word w;
    w.data = buf;
    w.length = total;
    w.char_count = total;
    return w;
}

void freak_tcp_close(int64_t fd) {
#ifdef _WIN32
    closesocket((SOCKET)fd);
#else
    close((int)fd);
#endif
}
