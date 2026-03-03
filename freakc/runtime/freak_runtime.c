#include "freak_runtime.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

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

int64_t freak_word_to_int(freak_word w) {
    return strtoll(w.data, NULL, 10);
}

double freak_word_to_num(freak_word w) {
    return strtod(w.data, NULL);
}
