#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <ctype.h>
#ifdef _WIN32
#include <io.h>
#else
#include <unistd.h>
#endif

/* ── Global args (set by main) ──────────────────────── */
static int g_argc = 0;
static char** g_argv = NULL;

/* ── Word (string) primitives ───────────────────────── */

int64_t freak_word_from_int(int64_t n) {
    char* buf = malloc(32);
    snprintf(buf, 32, "%lld", (long long)n);
    return (int64_t)buf;
}

int64_t freak_word_from_bool(int64_t b) {
    return b ? (int64_t)"true" : (int64_t)"false";
}

int64_t freak_word_concat(int64_t ap, int64_t bp) {
    char* a = (char*)ap;
    char* b = (char*)bp;
    size_t la = strlen(a);
    size_t lb = strlen(b);
    char* res = malloc(la + lb + 1);
    memcpy(res, a, la);
    memcpy(res + la, b, lb);
    res[la + lb] = '\0';
    return (int64_t)res;
}

int64_t freak_word_eq(int64_t ap, int64_t bp) {
    return strcmp((char*)ap, (char*)bp) == 0 ? 1 : 0;
}

int64_t freak_word_neq(int64_t ap, int64_t bp) {
    return strcmp((char*)ap, (char*)bp) != 0 ? 1 : 0;
}

/* ── String methods ─────────────────────────────────── */

int64_t freak_word_length(int64_t sp) {
    return (int64_t)strlen((char*)sp);
}

int64_t freak_word_char_at(int64_t sp, int64_t idx) {
    char* s = (char*)sp;
    size_t len = strlen(s);
    if ((size_t)idx >= len) return (int64_t)"";
    char* buf = malloc(2);
    buf[0] = s[idx];
    buf[1] = '\0';
    return (int64_t)buf;
}

int64_t freak_word_contains(int64_t sp, int64_t np) {
    return strstr((char*)sp, (char*)np) != NULL ? 1 : 0;
}

int64_t freak_word_starts_with(int64_t sp, int64_t pp) {
    char* s = (char*)sp;
    char* p = (char*)pp;
    size_t pl = strlen(p);
    return strncmp(s, p, pl) == 0 ? 1 : 0;
}

int64_t freak_word_ends_with(int64_t sp, int64_t pp) {
    char* s = (char*)sp;
    char* p = (char*)pp;
    size_t sl = strlen(s);
    size_t pl = strlen(p);
    if (pl > sl) return 0;
    return strcmp(s + sl - pl, p) == 0 ? 1 : 0;
}

int64_t freak_word_to_upper(int64_t sp) {
    char* s = (char*)sp;
    size_t len = strlen(s);
    char* buf = malloc(len + 1);
    for (size_t i = 0; i < len; i++) buf[i] = (char)toupper((unsigned char)s[i]);
    buf[len] = '\0';
    return (int64_t)buf;
}

int64_t freak_word_to_lower(int64_t sp) {
    char* s = (char*)sp;
    size_t len = strlen(s);
    char* buf = malloc(len + 1);
    for (size_t i = 0; i < len; i++) buf[i] = (char)tolower((unsigned char)s[i]);
    buf[len] = '\0';
    return (int64_t)buf;
}

int64_t freak_word_trim(int64_t sp) {
    char* s = (char*)sp;
    while (*s && isspace((unsigned char)*s)) s++;
    size_t len = strlen(s);
    while (len > 0 && isspace((unsigned char)s[len - 1])) len--;
    char* buf = malloc(len + 1);
    memcpy(buf, s, len);
    buf[len] = '\0';
    return (int64_t)buf;
}

int64_t freak_word_replace(int64_t sp, int64_t old_p, int64_t new_p) {
    char* s = (char*)sp;
    char* old_s = (char*)old_p;
    char* new_s = (char*)new_p;
    size_t old_len = strlen(old_s);
    size_t new_len = strlen(new_s);
    if (old_len == 0) return sp;

    /* Count occurrences */
    int count = 0;
    char* p = s;
    while ((p = strstr(p, old_s)) != NULL) { count++; p += old_len; }

    size_t result_len = strlen(s) + count * ((int64_t)new_len - (int64_t)old_len);
    char* buf = malloc(result_len + 1);
    char* dst = buf;
    p = s;
    while (*p) {
        if (strncmp(p, old_s, old_len) == 0) {
            memcpy(dst, new_s, new_len);
            dst += new_len;
            p += old_len;
        } else {
            *dst++ = *p++;
        }
    }
    *dst = '\0';
    return (int64_t)buf;
}

int64_t freak_word_to_int(int64_t sp) {
    return (int64_t)atoll((char*)sp);
}

/* ── I/O ────────────────────────────────────────────── */

void freak_llvm_say(int64_t sp) {
    puts((char*)sp);
}

void freak_llvm_print_str(int64_t sp) {
    printf("%s", (char*)sp);
}

void freak_llvm_print_int(int64_t n) {
    printf("%lld", (long long)n);
}

void freak_llvm_print_newline(void) {
    printf("\n");
}

int64_t freak_llvm_ask(int64_t prompt_p) {
    printf("%s", (char*)prompt_p);
    fflush(stdout);
    char buf[1024];
    if (fgets(buf, sizeof(buf), stdin)) {
        size_t len = strlen(buf);
        if (len > 0 && buf[len-1] == '\n') buf[--len] = '\0';
        char* res = malloc(len + 1);
        memcpy(res, buf, len + 1);
        return (int64_t)res;
    }
    return (int64_t)"";
}

/* ── File I/O ───────────────────────────────────────── */

int64_t freak_llvm_fs_read(int64_t path_p) {
    FILE* f = fopen((char*)path_p, "rb");
    if (!f) { fprintf(stderr, "PANIC: cannot read file: %s\n", (char*)path_p); exit(1); }
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    char* buf = malloc(sz + 1);
    fread(buf, 1, sz, f);
    buf[sz] = '\0';
    fclose(f);
    return (int64_t)buf;
}

void freak_llvm_fs_write(int64_t path_p, int64_t content_p) {
    FILE* f = fopen((char*)path_p, "wb");
    if (!f) { fprintf(stderr, "PANIC: cannot write file: %s\n", (char*)path_p); exit(1); }
    char* content = (char*)content_p;
    fwrite(content, 1, strlen(content), f);
    fclose(f);
}

void freak_llvm_fs_append(int64_t path_p, int64_t content_p) {
    FILE* f = fopen((char*)path_p, "ab");
    if (!f) { fprintf(stderr, "PANIC: cannot append file: %s\n", (char*)path_p); exit(1); }
    char* content = (char*)content_p;
    fwrite(content, 1, strlen(content), f);
    fclose(f);
}

int64_t freak_llvm_fs_exists(int64_t path_p) {
    char* path = (char*)path_p;
#ifdef _WIN32
    return _access(path, 0) == 0 ? 1 : 0;
#else
    return access(path, F_OK) == 0 ? 1 : 0;
#endif
}

void freak_llvm_fs_delete(int64_t path_p) {
    remove((char*)path_p);
}

/* ── Process ────────────────────────────────────────── */

int64_t freak_llvm_process_args_count(void) {
    return (int64_t)g_argc;
}

int64_t freak_llvm_process_arg(int64_t idx) {
    if (idx < 0 || idx >= g_argc) return (int64_t)"";
    return (int64_t)g_argv[idx];
}

void freak_llvm_process_exit(int64_t code) {
    exit((int)code);
}

/* ── Panic ──────────────────────────────────────────── */

void freak_llvm_panic(int64_t msg_p) {
    fprintf(stderr, "PANIC: %s\n", (char*)msg_p);
    exit(1);
}

/* ── Shape (struct) helpers ─────────────────────────── */

int64_t freak_llvm_shape_alloc(int64_t field_count) {
    int64_t* fields = (int64_t*)calloc((size_t)field_count, sizeof(int64_t));
    return (int64_t)fields;
}

int64_t freak_llvm_shape_get(int64_t ptr, int64_t index) {
    int64_t* fields = (int64_t*)ptr;
    return fields[index];
}

void freak_llvm_shape_set(int64_t ptr, int64_t index, int64_t value) {
    int64_t* fields = (int64_t*)ptr;
    fields[index] = value;
}

/* ── LLVM wrapper aliases ───────────────────────────── */
/* The LLVM IR declares @freak_llvm_word_* but this file defines  */
/* freak_word_*. Add thin wrappers so the linker can resolve them. */

int64_t freak_llvm_word_from_int(int64_t n)   { return freak_word_from_int(n); }
int64_t freak_llvm_word_from_bool(int64_t b)  { return freak_word_from_bool(b); }
int64_t freak_llvm_word_concat(int64_t a, int64_t b) { return freak_word_concat(a, b); }
int64_t freak_llvm_word_eq(int64_t a, int64_t b)     { return freak_word_eq(a, b); }
int64_t freak_llvm_word_neq(int64_t a, int64_t b)    { return freak_word_neq(a, b); }
int64_t freak_llvm_word_length(int64_t s)     { return freak_word_length(s); }
int64_t freak_llvm_word_char_at(int64_t s, int64_t i) { return freak_word_char_at(s, i); }
int64_t freak_llvm_word_contains(int64_t s, int64_t n) { return freak_word_contains(s, n); }
int64_t freak_llvm_word_starts_with(int64_t s, int64_t p) { return freak_word_starts_with(s, p); }
int64_t freak_llvm_word_ends_with(int64_t s, int64_t p) { return freak_word_ends_with(s, p); }
int64_t freak_llvm_word_to_upper(int64_t s)   { return freak_word_to_upper(s); }
int64_t freak_llvm_word_to_lower(int64_t s)   { return freak_word_to_lower(s); }
int64_t freak_llvm_word_trim(int64_t s)       { return freak_word_trim(s); }
int64_t freak_llvm_word_replace(int64_t s, int64_t o, int64_t n) { return freak_word_replace(s, o, n); }
int64_t freak_llvm_word_to_int(int64_t s)     { return freak_word_to_int(s); }

/* ── UI stubs (for LLVM backend) ───────────────────── */
int64_t freak_llvm_ui_create_native(int64_t t, int64_t w, int64_t h) { return 0; }
int64_t freak_llvm_ui_poll_events(int64_t w)  { return 0; }
void    freak_llvm_ui_begin_frame(int64_t w)  { }
void    freak_llvm_ui_end_frame(int64_t w)    { }
void    freak_llvm_ui_clear(int64_t w, int64_t r, int64_t g, int64_t b, int64_t a) { }
void    freak_llvm_ui_fill_rect(int64_t w, int64_t x, int64_t y, int64_t ww, int64_t hh, int64_t r, int64_t g, int64_t b, int64_t a) { }

/* ── Num (double) helpers ──────────────────────────── */
/* Doubles are stored as bitcast i64 in FREAK LLVM IR.  */
/* These helpers reinterpret the bits.                    */

int64_t freak_llvm_word_from_num(int64_t bits) {
    double d;
    memcpy(&d, &bits, sizeof(d));
    char* buf = (char*)malloc(32);
    snprintf(buf, 32, "%g", d);
    return (int64_t)buf;
}

void freak_llvm_print_num(int64_t bits) {
    double d;
    memcpy(&d, &bits, sizeof(d));
    printf("%g", d);
}

int64_t freak_llvm_int_to_num(int64_t n) {
    double d = (double)n;
    int64_t bits;
    memcpy(&bits, &d, sizeof(bits));
    return bits;
}

int64_t freak_llvm_num_to_int(int64_t bits) {
    double d;
    memcpy(&d, &bits, sizeof(d));
    return (int64_t)d;
}

/* ── Entry point setup ──────────────────────────────── */
/* The LLVM IR main calls freak_llvm_setup_args then freak_main */

void freak_llvm_setup_args(int64_t argc, int64_t argv) {
    g_argc = (int)argc;
    g_argv = (char**)argv;
}

