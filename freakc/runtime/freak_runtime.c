#ifndef _WIN32
#define _POSIX_C_SOURCE 200809L
#endif

#include "freak_runtime.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdatomic.h>
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
#include <sys/wait.h>
#include <unistd.h>
#include <dirent.h>
#define _strdup strdup
#endif

static int64_t freak_normalize_process_status(int status) {
#ifdef _WIN32
    return (int64_t)status;
#else
    if (status == -1) return -1;
    if (WIFEXITED(status)) return (int64_t)WEXITSTATUS(status);
    if (WIFSIGNALED(status)) return (int64_t)(128 + WTERMSIG(status));
    return (int64_t)status;
#endif
}

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

freak_word freak_word_concat_consuming(freak_word a, freak_word b, bool release_a, bool release_b) {
    freak_word result = freak_word_concat(a, b);
    bool same_input = a.data == b.data;
    if (release_a) freak_word_release_owned(&a);
    if (release_b && (!same_input || !release_a)) freak_word_release_owned(&b);
    return result;
}

freak_word freak_word_clone(freak_word source) {
    if (!source.heap || !source.data) return source;
    char* buf = (char*)malloc(source.length + 1);
    if (!buf) { fprintf(stderr, "FREAK: out of memory\n"); exit(1); }
    memcpy(buf, source.data, source.length);
    buf[source.length] = '\0';
    return freak_word_own(buf, source.length);
}

void freak_word_replace_owned(freak_word* slot, freak_word replacement) {
    if (!slot) return;
    if (slot->heap && slot->data && slot->data != replacement.data) {
        free((void*)slot->data);
    }
    *slot = replacement;
}

void freak_word_release_owned(freak_word* slot) {
    if (!slot) return;
    if (slot->heap && slot->data) free((void*)slot->data);
    *slot = (freak_word)FREAK_WORD_EMPTY;
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

freak_word freak_char_to_word(int64_t code) {
    char* buf = (char*)malloc(5);
    if (!buf) { fprintf(stderr, "FREAK: out of memory\n"); exit(1); }
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
    return freak_word_own(buf, len);
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

#ifdef _WIN32
static void freak_write_stream_utf8(FILE* stream, HANDLE handle, const char* data, size_t len, bool newline) {
    DWORD mode = 0;
    if (!handle || handle == INVALID_HANDLE_VALUE || !GetConsoleMode(handle, &mode)) {
        if (len > 0) {
            fwrite(data, 1, len, stream);
        }
        if (newline) {
            fputc('\n', stream);
        }
        fflush(stream);
        return;
    }

    int src_len = (int)len;
    int wide_len = MultiByteToWideChar(CP_UTF8, 0, data, src_len, NULL, 0);
    if (wide_len <= 0) {
        if (len > 0) {
            fwrite(data, 1, len, stream);
        }
        if (newline) {
            fputc('\n', stream);
        }
        fflush(stream);
        return;
    }

    int total_wide_len = wide_len + (newline ? 1 : 0);
    wchar_t* wide_buf = (wchar_t*)malloc((size_t)total_wide_len * sizeof(wchar_t));
    if (!wide_buf) {
        fprintf(stderr, "FREAK: out of memory\n");
        exit(1);
    }

    MultiByteToWideChar(CP_UTF8, 0, data, src_len, wide_buf, wide_len);
    if (newline) {
        wide_buf[wide_len] = L'\n';
    }

    DWORD written = 0;
    WriteConsoleW(handle, wide_buf, (DWORD)total_wide_len, &written, NULL);
    free(wide_buf);
    fflush(stream);
}
#else
static void freak_write_stream_utf8(FILE* stream, const char* data, size_t len, bool newline) {
    if (len > 0) {
        fwrite(data, 1, len, stream);
    }
    if (newline) {
        fputc('\n', stream);
    }
    fflush(stream);
}
#endif

void freak_say(freak_word msg) {
#ifdef _WIN32
    freak_write_stream_utf8(stdout, GetStdHandle(STD_OUTPUT_HANDLE), msg.data, msg.length, true);
#else
    freak_write_stream_utf8(stdout, msg.data, msg.length, true);
#endif
}

void freak_say_err(freak_word msg) {
#ifdef _WIN32
    freak_write_stream_utf8(stderr, GetStdHandle(STD_ERROR_HANDLE), msg.data, msg.length, true);
#else
    freak_write_stream_utf8(stderr, msg.data, msg.length, true);
#endif
}

freak_word freak_ask(freak_word prompt) {
    /* Print the prompt (no newline). */
#ifdef _WIN32
    freak_write_stream_utf8(stdout, GetStdHandle(STD_OUTPUT_HANDLE), prompt.data, prompt.length, false);
#else
    freak_write_stream_utf8(stdout, prompt.data, prompt.length, false);
#endif

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
                if (result.length > 0) freak_word_replace_owned(&result, freak_word_concat(result, freak_word_lit("|")));
                freak_word_replace_owned(&result, freak_word_concat(result, freak_word_lit(fd.cFileName)));
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
                if (result.length > 0) freak_word_replace_owned(&result, freak_word_concat(result, freak_word_lit("|")));
                freak_word_replace_owned(&result, freak_word_concat(result, freak_word_lit(ent->d_name)));
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
    /* Method results are owned values. Even an identity replacement must not
       alias a parameter which the generated callee epilogue will release. */
    if (old_s.length == 0) return freak_word_clone(w);
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
    size_t new_len = w.length;
    if (new_s.length >= old_s.length) {
        size_t growth = new_s.length - old_s.length;
        if (growth > 0 && count > (SIZE_MAX - w.length) / growth) {
            fprintf(stderr, "FREAK: word replacement size overflow\n");
            exit(1);
        }
        new_len = w.length + count * growth;
    } else {
        size_t shrink = old_s.length - new_s.length;
        new_len = w.length - count * shrink;
    }
    if (new_len == SIZE_MAX) {
        fprintf(stderr, "FREAK: word replacement size overflow\n");
        exit(1);
    }
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

static const char* freak_word_byte_literal(unsigned char value) {
    static char byte_words[256][2];
    static atomic_bool ready = ATOMIC_VAR_INIT(false);
    static atomic_flag init_lock = ATOMIC_FLAG_INIT;
    if (!atomic_load_explicit(&ready, memory_order_acquire)) {
        while (atomic_flag_test_and_set_explicit(&init_lock, memory_order_acquire)) {
        }
        if (!atomic_load_explicit(&ready, memory_order_relaxed)) {
            for (size_t i = 0; i < 256; i++) {
                byte_words[i][0] = (char)i;
                byte_words[i][1] = '\0';
            }
            atomic_store_explicit(&ready, true, memory_order_release);
        }
        atomic_flag_clear_explicit(&init_lock, memory_order_release);
    }
    return byte_words[value];
}

freak_word freak_word_char_at(freak_word w, int64_t index) {
    if (index < 0 || (size_t)index >= w.length) {
        return freak_word_lit("");
    }
    freak_word out;
    out.data = freak_word_byte_literal((unsigned char)w.data[index]);
    out.length = 1;
    out.char_count = 1;
    out.heap = false;
    return out;
}

static int64_t freak_stable_checksum_bytes(const unsigned char* data, size_t len) {
    uint64_t hash = UINT64_C(14695981039346656037);
    for (size_t i = 0; i < len; i++) {
        hash ^= (uint64_t)data[i];
        hash *= UINT64_C(1099511628211);
    }
    return (int64_t)(hash & UINT64_C(0x7fffffffffffffff));
}

int64_t freak_word_checksum(freak_word w) {
    if (!w.data || w.length == 0) {
        return freak_stable_checksum_bytes((const unsigned char*)"", 0);
    }
    return freak_stable_checksum_bytes((const unsigned char*)w.data, w.length);
}

static freak_word freak_word_copy_range(freak_word w, size_t start, size_t end) {
    if (!w.data || start >= end || start >= w.length) {
        return freak_word_lit("");
    }
    if (end > w.length) end = w.length;
    size_t len = end - start;
    char* buf = (char*)malloc(len + 1);
    if (!buf) { fprintf(stderr, "FREAK: out of memory\n"); exit(1); }
    memcpy(buf, w.data + start, len);
    buf[len] = '\0';
    return freak_word_own(buf, len);
}

freak_word freak_word_snapshot_escape(freak_word w) {
    if (!w.data || w.length == 0) return freak_word_lit("");

    size_t escaped_len = w.length;
    for (size_t i = 0; i < w.length; i++) {
        char ch = w.data[i];
        if (ch == '%' || ch == '|' || ch == '\n' || ch == '\r') {
            if (escaped_len > SIZE_MAX - 2) {
                fprintf(stderr, "FREAK: snapshot escape overflow\n");
                exit(1);
            }
            escaped_len += 2;
        }
    }

    char* buf = (char*)malloc(escaped_len + 1);
    if (!buf) { fprintf(stderr, "FREAK: out of memory\n"); exit(1); }
    size_t out = 0;
    for (size_t i = 0; i < w.length; i++) {
        const char* encoded = NULL;
        switch (w.data[i]) {
            case '%': encoded = "%25"; break;
            case '|': encoded = "%7C"; break;
            case '\n': encoded = "%0A"; break;
            case '\r': encoded = "%0D"; break;
            default: break;
        }
        if (encoded) {
            memcpy(buf + out, encoded, 3);
            out += 3;
        } else {
            buf[out++] = w.data[i];
        }
    }
    buf[out] = '\0';
    return freak_word_own(buf, out);
}

freak_word freak_word_snapshot_unescape(freak_word w) {
    if (!w.data || w.length == 0) return freak_word_lit("");

    char* buf = (char*)malloc(w.length + 1);
    if (!buf) { fprintf(stderr, "FREAK: out of memory\n"); exit(1); }
    size_t out = 0;
    size_t i = 0;
    while (i < w.length) {
        if (w.data[i] == '%' && i + 2 < w.length) {
            const char* code = w.data + i;
            if (code[1] == '2' && code[2] == '5') {
                buf[out++] = '%';
                i += 3;
                continue;
            }
            if (code[1] == '7' && code[2] == 'C') {
                buf[out++] = '|';
                i += 3;
                continue;
            }
            if (code[1] == '0' && code[2] == 'A') {
                buf[out++] = '\n';
                i += 3;
                continue;
            }
            if (code[1] == '0' && code[2] == 'D') {
                buf[out++] = '\r';
                i += 3;
                continue;
            }
        }
        buf[out++] = w.data[i++];
    }
    buf[out] = '\0';
    return freak_word_own(buf, out);
}

int64_t freak_word_snapshot_line_count(freak_word w) {
    if (!w.data || w.length == 0) return 0;
    int64_t count = 1;
    for (size_t i = 0; i < w.length; i++) {
        if (w.data[i] == '\n') count++;
    }
    return count;
}

freak_word freak_word_snapshot_line(freak_word w, int64_t wanted) {
    if (!w.data || wanted < 0) return freak_word_lit("");
    int64_t line = 0;
    size_t start = 0;
    for (size_t i = 0; i < w.length; i++) {
        if (w.data[i] == '\n') {
            if (line == wanted) return freak_word_copy_range(w, start, i);
            line++;
            start = i + 1;
        }
    }
    if (line == wanted) return freak_word_copy_range(w, start, w.length);
    return freak_word_lit("");
}

int64_t freak_word_snapshot_field_count(freak_word w) {
    if (!w.data || w.length == 0) return 0;
    int64_t count = 1;
    for (size_t i = 0; i < w.length; i++) {
        if (w.data[i] == '|') count++;
    }
    return count;
}

freak_word freak_word_snapshot_field_raw(freak_word w, int64_t wanted) {
    if (!w.data || wanted < 0) return freak_word_lit("");
    int64_t field = 0;
    size_t start = 0;
    for (size_t i = 0; i < w.length; i++) {
        if (w.data[i] == '|') {
            if (field == wanted) return freak_word_copy_range(w, start, i);
            field++;
            start = i + 1;
        }
    }
    if (field == wanted) return freak_word_copy_range(w, start, w.length);
    return freak_word_lit("");
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
    out.exit_code = freak_normalize_process_status(status);
    out.success = (out.exit_code == 0);
    return out;
}

/* Simple exec: run command, return exit code */
int64_t freak_process_exec(freak_word cmd) {
    const char* cmd_str = freak_word_to_cstr(cmd);
    return freak_normalize_process_status(system(cmd_str));
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

void freak_enable_ansi(void) {
#ifdef _WIN32
    /* Match the console code page to our UTF-8 string literals before writing banner art. */
    SetConsoleOutputCP(CP_UTF8);
    SetConsoleCP(CP_UTF8);

    HANDLE handles[2];
    handles[0] = GetStdHandle(STD_OUTPUT_HANDLE);
    handles[1] = GetStdHandle(STD_ERROR_HANDLE);

    for (int i = 0; i < 2; i++) {
        HANDLE h = handles[i];
        if (!h || h == INVALID_HANDLE_VALUE) {
            continue;
        }

        DWORD mode = 0;
        if (!GetConsoleMode(h, &mode)) {
            continue;
        }

        mode |= ENABLE_VIRTUAL_TERMINAL_PROCESSING;
        SetConsoleMode(h, mode);
    }
#endif
}

void freak_llvm_setup_args(int64_t argc, int64_t argv) {
    freak_enable_ansi();
    freak_argc = (int)argc;
    freak_argv = (char**)argv;
}

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct freak_llvm_owned_word {
    void* pointer;
    struct freak_llvm_owned_word* next;
} freak_llvm_owned_word;

static freak_llvm_owned_word** freak_llvm_owned_buckets = NULL;
static size_t freak_llvm_owned_bucket_count = 0;
static size_t freak_llvm_owned_count = 0;

static size_t freak_llvm_owned_bucket(void* pointer, size_t bucket_count) {
    uint64_t value = (uint64_t)(uintptr_t)pointer;
    value ^= value >> 33;
    value *= UINT64_C(0xff51afd7ed558ccd);
    value ^= value >> 33;
    return (size_t)(value & (uint64_t)(bucket_count - 1));
}

static void freak_llvm_owned_resize(size_t new_bucket_count) {
    freak_llvm_owned_word** resized = (freak_llvm_owned_word**)calloc(
        new_bucket_count, sizeof(*resized));
    if (!resized) {
        fprintf(stderr, "FREAK: out of memory growing the owned-word registry\n");
        exit(1);
    }
    for (size_t bucket = 0; bucket < freak_llvm_owned_bucket_count; bucket++) {
        freak_llvm_owned_word* current = freak_llvm_owned_buckets[bucket];
        while (current) {
            freak_llvm_owned_word* next = current->next;
            size_t target = freak_llvm_owned_bucket(current->pointer, new_bucket_count);
            current->next = resized[target];
            resized[target] = current;
            current = next;
        }
    }
    free(freak_llvm_owned_buckets);
    freak_llvm_owned_buckets = resized;
    freak_llvm_owned_bucket_count = new_bucket_count;
}

static void freak_llvm_owned_ensure_capacity(void) {
    if (freak_llvm_owned_bucket_count == 0) {
        freak_llvm_owned_resize(64);
    } else if ((freak_llvm_owned_count + 1) * 4 >= freak_llvm_owned_bucket_count * 3) {
        freak_llvm_owned_resize(freak_llvm_owned_bucket_count * 2);
    }
}

#ifdef FREAK_RUNTIME_OWNERSHIP_AUDIT
static bool freak_llvm_ownership_audit_registered = false;

static void freak_llvm_ownership_audit_at_exit(void) {
    if (freak_llvm_owned_count != 0) {
        fprintf(stderr,
                "FREAK: LLVM ownership audit found %llu unreleased word allocation(s)\n",
                (unsigned long long)freak_llvm_owned_count);
        _Exit(86);
    }
}
#endif

int64_t freak_llvm_word_adopt(int64_t pointer) {
    if (!pointer) return pointer;
#ifdef FREAK_RUNTIME_OWNERSHIP_AUDIT
    if (!freak_llvm_ownership_audit_registered) {
        if (atexit(freak_llvm_ownership_audit_at_exit) != 0) {
            fprintf(stderr, "FREAK: could not register LLVM ownership audit\n");
            exit(1);
        }
        freak_llvm_ownership_audit_registered = true;
    }
#endif
    freak_llvm_owned_ensure_capacity();
    size_t bucket = freak_llvm_owned_bucket((void*)pointer, freak_llvm_owned_bucket_count);
    freak_llvm_owned_word* current = freak_llvm_owned_buckets[bucket];
    while (current) {
        if (current->pointer == (void*)pointer) return pointer;
        current = current->next;
    }
    freak_llvm_owned_word* owned = (freak_llvm_owned_word*)malloc(sizeof(*owned));
    if (!owned) {
        fprintf(stderr, "FREAK: out of memory tracking an owned word\n");
        exit(1);
    }
    owned->pointer = (void*)pointer;
    owned->next = freak_llvm_owned_buckets[bucket];
    freak_llvm_owned_buckets[bucket] = owned;
    freak_llvm_owned_count += 1;
    return pointer;
}

int64_t freak_llvm_word_clone(int64_t source) {
    const char* text = (const char*)source;
    if (!text) return 0;
    size_t length = strlen(text);
    char* clone = (char*)malloc(length + 1);
    if (!clone) {
        fprintf(stderr, "FREAK: out of memory cloning a word\n");
        exit(1);
    }
    memcpy(clone, text, length + 1);
    return freak_llvm_word_adopt((int64_t)clone);
}

void freak_llvm_word_release_replaced(int64_t previous, int64_t replacement) {
    if (!previous || previous == replacement) return;
    /* Literal/static/foreign pointers are deliberately absent from this
       registry and therefore ignored. Only adopted allocations are freed. */
    if (freak_llvm_owned_bucket_count == 0) return;
    size_t bucket = freak_llvm_owned_bucket((void*)previous, freak_llvm_owned_bucket_count);
    freak_llvm_owned_word** link = &freak_llvm_owned_buckets[bucket];
    while (*link) {
        freak_llvm_owned_word* owned = *link;
        if (owned->pointer == (void*)previous) {
            *link = owned->next;
            free(owned->pointer);
            free(owned);
            freak_llvm_owned_count -= 1;
            return;
        }
        link = &owned->next;
    }
}

int64_t freak_llvm_word_from_int(int64_t n) {
    char* buf = (char*)malloc(32);
    snprintf(buf, 32, "%lld", (long long)n);
    return freak_llvm_word_adopt((int64_t)buf);
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
    return freak_llvm_word_adopt((int64_t)buf);
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

int64_t freak_llvm_word_checksum(int64_t a) {
    const char* sa = (const char*)a;
    if (!sa) sa = "";
    return freak_stable_checksum_bytes((const unsigned char*)sa, strlen(sa));
}

int64_t freak_llvm_word_snapshot_escape(int64_t a) {
    const char* sa = (const char*)a;
    freak_word out = freak_word_snapshot_escape(freak_word_lit(sa ? sa : ""));
    if (out.heap) return freak_llvm_word_adopt((int64_t)out.data);
    return (int64_t)out.data;
}

int64_t freak_llvm_word_snapshot_unescape(int64_t a) {
    const char* sa = (const char*)a;
    freak_word out = freak_word_snapshot_unescape(freak_word_lit(sa ? sa : ""));
    if (out.heap) return freak_llvm_word_adopt((int64_t)out.data);
    return (int64_t)out.data;
}

int64_t freak_llvm_word_snapshot_line_count(int64_t a) {
    const char* sa = (const char*)a;
    return freak_word_snapshot_line_count(freak_word_lit(sa ? sa : ""));
}

int64_t freak_llvm_word_snapshot_line(int64_t a, int64_t wanted) {
    const char* sa = (const char*)a;
    freak_word out = freak_word_snapshot_line(freak_word_lit(sa ? sa : ""), wanted);
    if (out.heap) return freak_llvm_word_adopt((int64_t)out.data);
    return (int64_t)out.data;
}

int64_t freak_llvm_word_snapshot_field_count(int64_t a) {
    const char* sa = (const char*)a;
    return freak_word_snapshot_field_count(freak_word_lit(sa ? sa : ""));
}

int64_t freak_llvm_word_snapshot_field_raw(int64_t a, int64_t wanted) {
    const char* sa = (const char*)a;
    freak_word out = freak_word_snapshot_field_raw(freak_word_lit(sa ? sa : ""), wanted);
    if (out.heap) return freak_llvm_word_adopt((int64_t)out.data);
    return (int64_t)out.data;
}

int64_t freak_llvm_word_char_at(int64_t a, int64_t idx) {
    const char* sa = (const char*)a;
    if (!sa) return (int64_t)"";
    size_t len = strlen(sa);
    if (idx < 0 || idx >= (int64_t)len) return (int64_t)"";
    return (int64_t)freak_word_byte_literal((unsigned char)sa[idx]);
}

int64_t freak_llvm_word_substring(int64_t a, int64_t start, int64_t len) {
    const char* sa = (const char*)a;
    freak_word out = freak_word_substring(freak_word_lit(sa ? sa : ""), start, len);
    if (out.heap) return freak_llvm_word_adopt((int64_t)out.data);
    return (int64_t)out.data;
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
    return freak_llvm_word_adopt((int64_t)buf);
}

int64_t freak_llvm_word_to_lower(int64_t a) {
    const char* sa = (const char*)a;
    if (!sa) return (int64_t)"";
    char* buf = _strdup(sa);
    for (char* p = buf; *p; p++) {
        if (*p >= 'A' && *p <= 'Z') *p += 32;
    }
    return freak_llvm_word_adopt((int64_t)buf);
}

int64_t freak_llvm_word_trim(int64_t a) {
    const char* sa = (const char*)a;
    if (!sa) sa = "";
    const char* start = sa;
    while (*start && isspace((unsigned char)*start)) start++;
    const char* end = sa + strlen(sa);
    while (end > start && isspace((unsigned char)end[-1])) end--;
    size_t length = (size_t)(end - start);
    char* output = (char*)malloc(length + 1);
    if (!output) { fprintf(stderr, "FREAK: out of memory\n"); exit(1); }
    memcpy(output, start, length);
    output[length] = '\0';
    return freak_llvm_word_adopt((int64_t)output);
}

int64_t freak_llvm_word_replace(int64_t a, int64_t b, int64_t c) {
    const char* sa = (const char*)a;
    const char* old_s = (const char*)b;
    const char* new_s = (const char*)c;
    if (!sa) sa = "";
    if (!old_s) old_s = "";
    if (!new_s) new_s = "";
    size_t source_len = strlen(sa);
    size_t old_len = strlen(old_s);
    size_t replacement_len = strlen(new_s);
    size_t count = 0;
    if (old_len > 0 && source_len >= old_len) {
        for (size_t i = 0; i <= source_len - old_len; ) {
            if (memcmp(sa + i, old_s, old_len) == 0) {
                count++;
                i += old_len;
            } else {
                i++;
            }
        }
    }
    size_t output_len = source_len;
    if (replacement_len >= old_len) {
        size_t growth = replacement_len - old_len;
        if (growth > 0 && count > (SIZE_MAX - source_len) / growth) {
            fprintf(stderr, "FREAK: word replacement size overflow\n");
            exit(1);
        }
        output_len = source_len + count * growth;
    } else {
        size_t shrink = old_len - replacement_len;
        output_len = source_len - count * shrink;
    }
    if (output_len == SIZE_MAX) {
        fprintf(stderr, "FREAK: word replacement size overflow\n");
        exit(1);
    }
    char* output = (char*)malloc(output_len + 1);
    if (!output) { fprintf(stderr, "FREAK: out of memory\n"); exit(1); }
    size_t src = 0;
    size_t dst = 0;
    while (src < source_len) {
        if (old_len > 0 && src + old_len <= source_len && memcmp(sa + src, old_s, old_len) == 0) {
            memcpy(output + dst, new_s, replacement_len);
            dst += replacement_len;
            src += old_len;
        } else {
            output[dst++] = sa[src++];
        }
    }
    output[dst] = '\0';
    return freak_llvm_word_adopt((int64_t)output);
}

int64_t freak_llvm_word_to_int(int64_t a) {
    const char* sa = (const char*)a;
    if (!sa) return 0;
    return (int64_t)atoll(sa);
}

void freak_llvm_say(int64_t msg) {
    const char* s = (const char*)msg;
    if (!s) return;
#ifdef _WIN32
    freak_write_stream_utf8(stdout, GetStdHandle(STD_OUTPUT_HANDLE), s, strlen(s), true);
#else
    freak_write_stream_utf8(stdout, s, strlen(s), true);
#endif
}

void freak_llvm_print_str(int64_t msg) {
    const char* s = (const char*)msg;
    if (!s) return;
#ifdef _WIN32
    freak_write_stream_utf8(stdout, GetStdHandle(STD_OUTPUT_HANDLE), s, strlen(s), false);
#else
    freak_write_stream_utf8(stdout, s, strlen(s), false);
#endif
}

void freak_llvm_print_int(int64_t n) {
    char buf[32];
    int len = snprintf(buf, sizeof(buf), "%lld", (long long)n);
    if (len < 0) {
        return;
    }
#ifdef _WIN32
    freak_write_stream_utf8(stdout, GetStdHandle(STD_OUTPUT_HANDLE), buf, (size_t)len, false);
#else
    freak_write_stream_utf8(stdout, buf, (size_t)len, false);
#endif
}

void freak_llvm_print_newline(void) {
#ifdef _WIN32
    freak_write_stream_utf8(stdout, GetStdHandle(STD_OUTPUT_HANDLE), "", 0, true);
#else
    freak_write_stream_utf8(stdout, "", 0, true);
#endif
}

int64_t freak_llvm_ask(int64_t prompt) {
    const char* p = (const char*)prompt;
    if (p) {
#ifdef _WIN32
        freak_write_stream_utf8(stdout, GetStdHandle(STD_OUTPUT_HANDLE), p, strlen(p), false);
#else
        freak_write_stream_utf8(stdout, p, strlen(p), false);
#endif
    }
    char buf[1024];
    if (fgets(buf, sizeof(buf), stdin)) {
        size_t len = strlen(buf);
        if (len > 0 && buf[len - 1] == '\n') {
            buf[len - 1] = '\0';
        }
        return freak_llvm_word_adopt((int64_t)_strdup(buf));
    }
    return freak_llvm_word_adopt((int64_t)_strdup(""));
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
        return freak_llvm_word_adopt((int64_t)_strdup(""));
    }
    return freak_llvm_word_adopt((int64_t)_strdup(freak_argv[index]));
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
    int64_t next_free;
    uint32_t generation;
    bool in_use;
} freak_dyn_array;

static freak_dyn_array* freak_arrays = NULL;
static int64_t freak_array_count = 0;
static int64_t freak_array_capacity = 0;
static int64_t freak_array_free_head = -1;
static int64_t freak_array_live_count = 0;

#ifndef FREAK_ARRAY_LIVE_LIMIT
#define FREAK_ARRAY_LIVE_LIMIT 0
#endif

#define FREAK_ARRAY_GENERATION_MAX UINT32_C(0x7fffffff)

static int64_t freak_array_make_handle(int64_t slot, uint32_t generation) {
    return (int64_t)(((uint64_t)generation << 32) | (uint64_t)(uint32_t)slot);
}

static int64_t freak_array_slot_for_handle(int64_t handle) {
    if (handle < 0) return -1;
    uint64_t raw = (uint64_t)handle;
    int64_t slot = (int64_t)(uint32_t)(raw & UINT64_C(0xffffffff));
    uint32_t generation = (uint32_t)(raw >> 32);
    if (slot < 0 || slot >= freak_array_count) return -1;
    freak_dyn_array* array = &freak_arrays[slot];
    if (!array->in_use || array->generation != generation) return -1;
    return slot;
}

static void freak_array_reserve_handle(void) {
    if (freak_array_count < freak_array_capacity) {
        return;
    }

    int64_t old_capacity = freak_array_capacity;
    if (old_capacity > INT64_MAX / 2) {
        fprintf(stderr, "FREAK: array handle table is too large\n");
        exit(1);
    }
    int64_t new_capacity = old_capacity == 0 ? 256 : old_capacity * 2;
    if (new_capacity <= old_capacity || (uint64_t)new_capacity > SIZE_MAX / sizeof(freak_dyn_array)) {
        fprintf(stderr, "FREAK: array handle table is too large\n");
        exit(1);
    }

    freak_dyn_array* grown = (freak_dyn_array*)realloc(
        freak_arrays,
        (size_t)new_capacity * sizeof(freak_dyn_array)
    );
    if (!grown) {
        fprintf(stderr, "FREAK: out of memory growing array handle table\n");
        exit(1);
    }

    memset(
        grown + old_capacity,
        0,
        (size_t)(new_capacity - old_capacity) * sizeof(freak_dyn_array)
    );
    freak_arrays = grown;
    freak_array_capacity = new_capacity;
}

int64_t freak_array_new(void) {
    if (FREAK_ARRAY_LIVE_LIMIT > 0 && freak_array_live_count >= FREAK_ARRAY_LIVE_LIMIT) {
        return -1;
    }

    int64_t h = freak_array_free_head;
    if (h >= 0) {
        freak_array_free_head = freak_arrays[h].next_free;
        freak_arrays[h].generation += 1;
    } else {
        freak_array_reserve_handle();
        h = freak_array_count++;
        if ((uint64_t)h > UINT32_MAX) {
            fprintf(stderr, "FREAK: array handle table exhausted\n");
            exit(1);
        }
        freak_arrays[h].generation = 1;
    }
    freak_arrays[h].length = 0;
    freak_arrays[h].capacity = 64;
    freak_arrays[h].next_free = -1;
    freak_arrays[h].in_use = true;
    freak_arrays[h].data = (freak_word*)malloc(64 * sizeof(freak_word));
    if (!freak_arrays[h].data) {
        fprintf(stderr, "FREAK: out of memory for array\n");
        exit(1);
    }
    freak_array_live_count += 1;
    return freak_array_make_handle(h, freak_arrays[h].generation);
}

static void freak_array_reserve_elements(freak_dyn_array* array) {
    int64_t old_capacity = array->capacity;
    if (old_capacity <= 0 || old_capacity > INT64_MAX / 2) {
        fprintf(stderr, "FREAK: array element capacity is too large\n");
        exit(1);
    }

    int64_t new_capacity = old_capacity * 2;
    if (new_capacity <= old_capacity || (uint64_t)new_capacity > SIZE_MAX / sizeof(freak_word)) {
        fprintf(stderr, "FREAK: array element capacity is too large\n");
        exit(1);
    }

    freak_word* grown = (freak_word*)realloc(
        array->data,
        (size_t)new_capacity * sizeof(freak_word)
    );
    if (!grown) {
        fprintf(stderr, "FREAK: out of memory growing array\n");
        exit(1);
    }

    array->data = grown;
    array->capacity = new_capacity;
}

void freak_array_push(int64_t handle, freak_word item) {
    int64_t slot = freak_array_slot_for_handle(handle);
    if (slot < 0) return;
    freak_dyn_array* a = &freak_arrays[slot];
    if (a->length >= a->capacity) {
        freak_array_reserve_elements(a);
    }
    a->data[a->length++] = item;
}

void freak_array_push_owned(int64_t handle, freak_word item) {
    if (freak_array_slot_for_handle(handle) < 0) {
        freak_word_release_owned(&item);
        return;
    }
    freak_array_push(handle, item);
}

freak_word freak_array_get(int64_t handle, int64_t index) {
    int64_t slot = freak_array_slot_for_handle(handle);
    if (slot < 0) return freak_word_lit("");
    freak_dyn_array* a = &freak_arrays[slot];
    if (index < 0 || index >= a->length) return freak_word_lit("");
    return a->data[index];
}

int64_t freak_array_len(int64_t handle) {
    int64_t slot = freak_array_slot_for_handle(handle);
    if (slot < 0) return 0;
    return freak_arrays[slot].length;
}

void freak_array_set(int64_t handle, int64_t index, freak_word item) {
    int64_t slot = freak_array_slot_for_handle(handle);
    if (slot < 0) return;
    freak_dyn_array* a = &freak_arrays[slot];
    if (index < 0 || index >= a->length) {
        fprintf(stderr, "FREAK: array_set index %lld out of bounds (len %lld)\n",
                (long long)index, (long long)a->length);
        exit(1);
    }
    a->data[index] = item;
}

void freak_array_set_owned(int64_t handle, int64_t index, freak_word item) {
    int64_t slot = freak_array_slot_for_handle(handle);
    if (slot < 0) {
        freak_word_release_owned(&item);
        return;
    }
    freak_dyn_array* a = &freak_arrays[slot];
    if (index < 0 || index >= a->length) {
        fprintf(stderr, "FREAK: array_set index %lld out of bounds (len %lld)\n",
                (long long)index, (long long)a->length);
        exit(1);
    }
    freak_word_replace_owned(&a->data[index], item);
}

void freak_array_release(int64_t handle) {
    int64_t slot = freak_array_slot_for_handle(handle);
    if (slot < 0) return;
    freak_dyn_array* a = &freak_arrays[slot];
    free(a->data);
    a->data = NULL;
    a->length = 0;
    a->capacity = 0;
    a->in_use = false;
    freak_array_live_count -= 1;
    if (a->generation >= FREAK_ARRAY_GENERATION_MAX) {
        a->next_free = -1;
        return;
    }
    a->next_free = freak_array_free_head;
    freak_array_free_head = slot;
}

void freak_array_release_owned(int64_t handle) {
    int64_t slot = freak_array_slot_for_handle(handle);
    if (slot < 0) return;
    freak_dyn_array* a = &freak_arrays[slot];
    for (int64_t i = 0; i < a->length; ++i) {
        freak_word_release_owned(&a->data[i]);
    }
    freak_array_release(handle);
}

static freak_word freak_word_join_impl(int64_t handle, bool release_elements) {
    int64_t slot = freak_array_slot_for_handle(handle);
    if (slot < 0) {
        return freak_word_lit("");
    }

    freak_dyn_array* a = &freak_arrays[slot];
    size_t total = 0;
    for (int64_t index = 0; index < a->length; index++) {
        size_t part_length = a->data[index].length;
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
        freak_word part = a->data[index];
        if (part.length > 0) {
            memcpy(joined + offset, part.data, part.length);
            offset += part.length;
        }
    }
    joined[total] = '\0';
    freak_word result = freak_word_own(joined, total);
    if (release_elements) {
        freak_array_release_owned(handle);
    } else {
        freak_array_release(handle);
    }
    return result;
}

freak_word freak_word_join(int64_t handle) {
    return freak_word_join_impl(handle, false);
}

freak_word freak_word_join_owned(int64_t handle) {
    return freak_word_join_impl(handle, true);
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
    return freak_word_own(buf, (size_t)n);
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
    return freak_word_own(buf, (size_t)total);
}

void freak_tcp_close(int64_t fd) {
#ifdef _WIN32
    closesocket((SOCKET)fd);
#else
    close((int)fd);
#endif
}
