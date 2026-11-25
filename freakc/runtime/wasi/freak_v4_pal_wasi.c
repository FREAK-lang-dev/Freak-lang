/* FREAK V4 platform layer for wasm32-unknown-wasip1.
 *
 * The V4 core runtime needs a small C library: an allocator, the mem and str
 * functions, stdio output with a printf subset, exit/atexit and argument
 * access. This
 * file provides exactly that on WASI preview 1 imports, with no wasi-libc and
 * no host sysroot, so a FREAK program links into one self-contained module
 * that runs under any WASI host (Node, wasmtime, wasmer) and in browsers
 * through a small WASI shim.
 *
 * Behaviour follows glibc where programs can see it: stdout is buffered and
 * flushed by exit() and fflush(), stderr is unbuffered, _Exit() and abort()
 * drop buffered output, and %g prints the correctly rounded shortest form
 * (six significant digits, round-half-even on the exact binary value).
 *
 * Files are not wired to WASI preopens yet: every open fails, so fs::read
 * reports an error instead of trapping. The std host split (W4) adds them. */
#include <stddef.h>
#include <stdint.h>
#include <stdarg.h>
#include <stdbool.h>
#include "include/stdio.h"
#include "include/stdlib.h"
#include "include/string.h"
#include "include/fcntl.h"
#include "include/unistd.h"
#include "include/errno.h"
#include "include/sys/stat.h"

typedef struct { const void *buf; size_t len; } freak_pal_ciovec;
#define FREAK_WASI(name) __attribute__((import_module("wasi_snapshot_preview1"), import_name(#name)))
FREAK_WASI(fd_write) int freak_wasi_fd_write(int fd, const freak_pal_ciovec *iovs, size_t count, size_t *written);
FREAK_WASI(proc_exit) _Noreturn void freak_wasi_proc_exit(int code);
FREAK_WASI(args_sizes_get) int freak_wasi_args_sizes_get(size_t *argc, size_t *bytes);
FREAK_WASI(args_get) int freak_wasi_args_get(char **argv, char *buffer);

int freak_pal_errno;

/* ---- memory ------------------------------------------------------------ */

void *memcpy(void *dst, const void *src, size_t n) {
    unsigned char *d = dst;
    const unsigned char *s = src;
    while (n--) *d++ = *s++;
    return dst;
}

void *memmove(void *dst, const void *src, size_t n) {
    unsigned char *d = dst;
    const unsigned char *s = src;
    if (d < s) {
        while (n--) *d++ = *s++;
    } else {
        d += n;
        s += n;
        while (n--) *--d = *--s;
    }
    return dst;
}

void *memset(void *dst, int c, size_t n) {
    unsigned char *d = dst;
    while (n--) *d++ = (unsigned char)c;
    return dst;
}

int memcmp(const void *x, const void *y, size_t n) {
    const unsigned char *a = x, *b = y;
    for (; n; n--, a++, b++) {
        if (*a != *b) return *a - *b;
    }
    return 0;
}

void *memchr(const void *s, int c, size_t n) {
    const unsigned char *p = s;
    for (; n; n--, p++) {
        if (*p == (unsigned char)c) return (void *)p;
    }
    return NULL;
}

size_t strlen(const char *s) {
    const char *p = s;
    while (*p) p++;
    return (size_t)(p - s);
}

int strcmp(const char *a, const char *b) {
    while (*a && *a == *b) a++, b++;
    return (unsigned char)*a - (unsigned char)*b;
}

int strncmp(const char *a, const char *b, size_t n) {
    for (; n; n--, a++, b++) {
        if (*a != *b || !*a) return (unsigned char)*a - (unsigned char)*b;
    }
    return 0;
}

char *strerror(int code) {
    (void)code;
    return "WASI error";
}

/* Size-class allocator. Each block carries an 8-byte header holding its
   class; class c serves blocks of 16 << c bytes (header included) and keeps
   freed blocks on its own list. Linear memory only grows. */
extern unsigned char __heap_base;
static uintptr_t freak_pal_heap_next, freak_pal_heap_end;
static void *freak_pal_free_lists[28];
#define FREAK_PAL_CLASSES 28 /* largest block: 16 << 27 = 2 GiB */

static void *freak_pal_grab(size_t n) {
    if (!freak_pal_heap_next) {
        freak_pal_heap_next = (uintptr_t)&__heap_base;
        freak_pal_heap_end = (uintptr_t)__builtin_wasm_memory_size(0) * 65536u;
    }
    freak_pal_heap_next = (freak_pal_heap_next + 15) & ~(uintptr_t)15;
    if (n > UINTPTR_MAX - freak_pal_heap_next) return NULL;
    while (freak_pal_heap_next + n > freak_pal_heap_end) {
        size_t pages = (freak_pal_heap_next + n - freak_pal_heap_end + 65535) / 65536;
        if (__builtin_wasm_memory_grow(0, pages) == (size_t)-1) return NULL;
        freak_pal_heap_end += pages * 65536u;
    }
    void *block = (void *)freak_pal_heap_next;
    freak_pal_heap_next += n;
    return block;
}

static int freak_pal_class_of(size_t n) {
    if (n > ((size_t)16 << (FREAK_PAL_CLASSES - 1)) - 8) return -1;
    int c = 0;
    size_t size = 16;
    while (size < n + 8) {
        size <<= 1;
        c++;
    }
    return c;
}

static size_t freak_pal_capacity(void *p) {
    return ((size_t)16 << *((uint64_t *)p - 1)) - 8;
}

void *malloc(size_t n) {
    int c = freak_pal_class_of(n);
    if (c < 0) return NULL;
    uint64_t *header = freak_pal_free_lists[c];
    if (header) {
        freak_pal_free_lists[c] = *(void **)(header + 1);
    } else {
        header = freak_pal_grab((size_t)16 << c);
        if (!header) return NULL;
    }
    *header = (uint64_t)c;
    return header + 1;
}

void free(void *p) {
    if (!p) return;
    uint64_t *header = (uint64_t *)p - 1;
    int c = (int)*header;
    *(void **)p = freak_pal_free_lists[c];
    freak_pal_free_lists[c] = header;
}

void *calloc(size_t count, size_t size) {
    if (size && count > SIZE_MAX / size) return NULL;
    size_t n = count * size;
    void *p = malloc(n);
    if (p) memset(p, 0, n);
    return p;
}

void *realloc(void *p, size_t n) {
    if (!p) return malloc(n);
    size_t capacity = freak_pal_capacity(p);
    if (n <= capacity) return p;
    void *grown = malloc(n);
    if (!grown) return NULL;
    memcpy(grown, p, capacity);
    free(p);
    return grown;
}

char *strdup(const char *s) {
    size_t n = strlen(s) + 1;
    char *copy = malloc(n);
    if (copy) memcpy(copy, s, n);
    return copy;
}

/* ---- output ------------------------------------------------------------ */

struct FILE {
    int fd;
    bool buffered;
    size_t used;
    char buffer[4096];
};
static FILE freak_pal_out_file = {1, true, 0, {0}};
static FILE freak_pal_err_file = {2, false, 0, {0}};
static FILE freak_pal_in_file = {0, false, 0, {0}};
FILE *freak_pal_stdout = &freak_pal_out_file;
FILE *freak_pal_stderr = &freak_pal_err_file;
FILE *freak_pal_stdin = &freak_pal_in_file;

static void freak_pal_write_fd(int fd, const char *s, size_t n) {
    freak_pal_ciovec vec = {s, n};
    while (n) {
        size_t written = 0;
        if (freak_wasi_fd_write(fd, &vec, 1, &written) != 0 || written == 0) return;
        vec.buf = (const char *)vec.buf + written;
        vec.len -= written;
        n -= written;
    }
}

int fflush(FILE *f) {
    if (!f) f = freak_pal_stdout;
    if (f->used) {
        freak_pal_write_fd(f->fd, f->buffer, f->used);
        f->used = 0;
    }
    return 0;
}

static void freak_pal_put(FILE *f, const char *s, size_t n) {
    if (!f->buffered) {
        freak_pal_write_fd(f->fd, s, n);
        return;
    }
    if (f->used + n > sizeof f->buffer) {
        fflush(f);
        if (n > sizeof f->buffer) {
            freak_pal_write_fd(f->fd, s, n);
            return;
        }
    }
    memcpy(f->buffer + f->used, s, n);
    f->used += n;
}

size_t fwrite(const void *p, size_t size, size_t count, FILE *f) {
    if (size && count) freak_pal_put(f, p, size * count);
    return count;
}

int fputs(const char *s, FILE *f) {
    freak_pal_put(f, s, strlen(s));
    return 0;
}

int fputc(int c, FILE *f) {
    char ch = (char)c;
    freak_pal_put(f, &ch, 1);
    return (unsigned char)c;
}

int putchar(int c) { return fputc(c, freak_pal_stdout); }

int puts(const char *s) {
    fputs(s, freak_pal_stdout);
    return fputc('\n', freak_pal_stdout);
}

/* ---- formatting -------------------------------------------------------- */

typedef struct { char *buf; size_t cap, len; } freak_pal_sink;

static void freak_pal_emit(freak_pal_sink *k, const char *s, size_t n) {
    for (size_t i = 0; i < n; i++, k->len++) {
        if (k->len + 1 < k->cap) k->buf[k->len] = s[i];
    }
}

static void freak_pal_pad(freak_pal_sink *k, char c, int count) {
    while (count-- > 0) freak_pal_emit(k, &c, 1);
}

/* Exact decimal expansion of a finite positive double: digits[0..len) times
   10^exponent. A double is mant * 2^e; for e < 0 that is mant * 5^-e / 10^-e,
   so the digits of one big integer are exact. 90 limbs hold 5^1074 * 2^53. */
#define FREAK_PAL_LIMBS 90
typedef struct { uint32_t limb[FREAK_PAL_LIMBS]; int used; } freak_pal_big;

static void freak_pal_big_mul_small(freak_pal_big *b, uint32_t factor) {
    uint64_t carry = 0;
    for (int i = 0; i < b->used; i++) {
        uint64_t v = (uint64_t)b->limb[i] * factor + carry;
        b->limb[i] = (uint32_t)v;
        carry = v >> 32;
    }
    if (carry && b->used < FREAK_PAL_LIMBS) b->limb[b->used++] = (uint32_t)carry;
}

static uint32_t freak_pal_big_div_small(freak_pal_big *b, uint32_t divisor) {
    uint64_t rem = 0;
    for (int i = b->used - 1; i >= 0; i--) {
        uint64_t cur = (rem << 32) | b->limb[i];
        b->limb[i] = (uint32_t)(cur / divisor);
        rem = cur % divisor;
    }
    while (b->used > 0 && b->limb[b->used - 1] == 0) b->used--;
    return (uint32_t)rem;
}

static int freak_pal_exact_digits(double v, char *digits, int *exponent) {
    union { double d; uint64_t u; } bits = {v};
    int raw_exp = (int)((bits.u >> 52) & 0x7ff);
    uint64_t mant = bits.u & 0xfffffffffffffull;
    int e2;
    if (raw_exp == 0) {
        e2 = -1074;
    } else {
        mant |= 1ull << 52;
        e2 = raw_exp - 1075;
    }
    freak_pal_big big = {{0}, 0};
    big.limb[0] = (uint32_t)mant;
    big.limb[1] = (uint32_t)(mant >> 32);
    big.used = big.limb[1] ? 2 : 1;
    *exponent = 0;
    if (e2 >= 0) {
        for (int i = 0; i < e2; i++) freak_pal_big_mul_small(&big, 2);
    } else {
        for (int i = 0; i < -e2; i++) freak_pal_big_mul_small(&big, 5);
        *exponent = e2;
    }
    char reversed[800];
    int count = 0;
    while (big.used > 0) {
        uint32_t chunk = freak_pal_big_div_small(&big, 1000000000u);
        for (int i = 0; i < 9; i++) {
            reversed[count++] = (char)('0' + chunk % 10);
            chunk /= 10;
        }
    }
    while (count > 1 && reversed[count - 1] == '0') count--;
    for (int i = 0; i < count; i++) digits[i] = reversed[count - 1 - i];
    return count;
}

static void freak_pal_emit_g(freak_pal_sink *k, double v) {
    union { double d; uint64_t u; } bits = {v};
    bool negative = (bits.u >> 63) != 0;
    if (v != v) {
        freak_pal_emit(k, negative ? "-nan" : "nan", negative ? 4 : 3);
        return;
    }
    if (negative) {
        freak_pal_emit(k, "-", 1);
        v = -v;
    }
    if (v > 1.7976931348623157e308) {
        freak_pal_emit(k, "inf", 3);
        return;
    }
    if (v == 0) {
        freak_pal_emit(k, "0", 1);
        return;
    }
    enum { P = 6 };
    char digits[800];
    int exponent = 0;
    int count = freak_pal_exact_digits(v, digits, &exponent);
    int x = count - 1 + exponent; /* decimal exponent of the leading digit */
    char kept[P + 1];
    for (int i = 0; i < P; i++) kept[i] = i < count ? digits[i] : '0';
    if (count > P) {
        bool up = digits[P] > '5';
        if (digits[P] == '5') {
            bool rest = false;
            for (int i = P + 1; i < count; i++) {
                if (digits[i] != '0') rest = true;
            }
            up = rest || ((kept[P - 1] - '0') & 1);
        }
        if (up) {
            int i = P - 1;
            while (i >= 0 && kept[i] == '9') kept[i--] = '0';
            if (i < 0) {
                kept[0] = '1';
                x += 1;
            } else {
                kept[i] += 1;
            }
        }
    }
    int last = P - 1;
    while (last > 0 && kept[last] == '0') last--;
    if (x < -4 || x >= P) {
        freak_pal_emit(k, kept, 1);
        if (last > 0) {
            freak_pal_emit(k, ".", 1);
            freak_pal_emit(k, kept + 1, (size_t)last);
        }
        freak_pal_emit(k, x < 0 ? "e-" : "e+", 2);
        int ax = x < 0 ? -x : x;
        char exp_digits[4];
        int n = 0;
        do {
            exp_digits[n++] = (char)('0' + ax % 10);
            ax /= 10;
        } while (ax);
        if (n < 2) exp_digits[n++] = '0';
        while (n) freak_pal_emit(k, &exp_digits[--n], 1);
    } else if (x >= 0) {
        freak_pal_emit(k, kept, (size_t)x + 1);
        if (last > x) {
            freak_pal_emit(k, ".", 1);
            freak_pal_emit(k, kept + x + 1, (size_t)(last - x));
        }
    } else {
        freak_pal_emit(k, "0.", 2);
        for (int i = -1; i > x; i--) freak_pal_emit(k, "0", 1);
        freak_pal_emit(k, kept, (size_t)last + 1);
    }
}

/* printf subset used by the runtime: flags - 0, width, precision, length
   hh h l ll z j t, conversions d i u x X c s p g %. */
int vsnprintf(char *buf, size_t cap, const char *f, va_list ap) {
    freak_pal_sink k = {buf, cap, 0};
    for (; *f; f++) {
        if (*f != '%') {
            freak_pal_emit(&k, f, 1);
            continue;
        }
        f++;
        bool left = false, zero = false;
        for (;; f++) {
            if (*f == '-') left = true;
            else if (*f == '0') zero = true;
            else if (*f != '+' && *f != ' ' && *f != '#') break;
        }
        int width = 0;
        if (*f == '*') {
            width = va_arg(ap, int);
            f++;
        } else {
            while (*f >= '0' && *f <= '9') width = width * 10 + (*f++ - '0');
        }
        int precision = -1;
        if (*f == '.') {
            f++;
            precision = 0;
            if (*f == '*') {
                precision = va_arg(ap, int);
                f++;
            } else {
                while (*f >= '0' && *f <= '9') precision = precision * 10 + (*f++ - '0');
            }
        }
        int longs = 0;
        bool wide = false;
        while (*f == 'l') { longs++; f++; }
        while (*f == 'h') f++;
        /* size_t and ptrdiff_t are 32-bit here; intmax_t is 64-bit. */
        if (*f == 'j') { wide = true; f++; }
        else if (*f == 'z' || *f == 't') f++;
        char text[48];
        const char *out = text;
        size_t len = 0;
        bool numeric = false;
        switch (*f) {
        case 'd': case 'i': {
            long long value = (longs >= 2 || wide) ? va_arg(ap, long long) : longs ? va_arg(ap, long) : va_arg(ap, int);
            unsigned long long mag = value < 0 ? 0ull - (unsigned long long)value : (unsigned long long)value;
            char rev[24];
            int n = 0;
            do { rev[n++] = (char)('0' + mag % 10); mag /= 10; } while (mag);
            if (value < 0) text[len++] = '-';
            while (n) text[len++] = rev[--n];
            numeric = true;
            break;
        }
        case 'u': case 'x': case 'X': case 'p': {
            unsigned long long value;
            if (*f == 'p') value = (uintptr_t)va_arg(ap, void *);
            else value = (longs >= 2 || wide) ? va_arg(ap, unsigned long long) : longs ? va_arg(ap, unsigned long) : va_arg(ap, unsigned);
            unsigned base = *f == 'u' ? 10 : 16;
            const char *alphabet = *f == 'X' ? "0123456789ABCDEF" : "0123456789abcdef";
            char rev[24];
            int n = 0;
            do { rev[n++] = alphabet[value % base]; value /= base; } while (value);
            if (*f == 'p') { text[len++] = '0'; text[len++] = 'x'; }
            while (n) text[len++] = rev[--n];
            numeric = true;
            break;
        }
        case 'c':
            text[0] = (char)va_arg(ap, int);
            len = 1;
            break;
        case 's':
            out = va_arg(ap, const char *);
            if (!out) out = "(null)";
            len = strlen(out);
            if (precision >= 0 && (size_t)precision < len) len = (size_t)precision;
            break;
        case 'g': {
            freak_pal_sink inner = {text, sizeof text, 0};
            freak_pal_emit_g(&inner, va_arg(ap, double));
            len = inner.len < sizeof text ? inner.len : sizeof text - 1;
            break;
        }
        case '%':
            text[0] = '%';
            len = 1;
            break;
        default:
            text[0] = '%';
            text[1] = '?';
            len = 2;
            break;
        }
        int padding = width > (int)len ? width - (int)len : 0;
        if (!left) {
            if (zero && numeric && len && out[0] == '-') {
                freak_pal_emit(&k, "-", 1);
                freak_pal_pad(&k, '0', padding);
                freak_pal_emit(&k, out + 1, len - 1);
                continue;
            }
            freak_pal_pad(&k, zero && numeric ? '0' : ' ', padding);
        }
        freak_pal_emit(&k, out, len);
        if (left) freak_pal_pad(&k, ' ', padding);
        if (!*f) break;
    }
    if (cap) buf[k.len < cap ? k.len : cap - 1] = 0;
    return (int)k.len;
}

int snprintf(char *b, size_t n, const char *f, ...) {
    va_list ap;
    va_start(ap, f);
    int r = vsnprintf(b, n, f, ap);
    va_end(ap);
    return r;
}

int vfprintf(FILE *fp, const char *f, va_list ap) {
    char small[1024];
    va_list copy;
    va_copy(copy, ap);
    int n = vsnprintf(small, sizeof small, f, copy);
    va_end(copy);
    if (n < 0) return n;
    if ((size_t)n < sizeof small) {
        freak_pal_put(fp, small, (size_t)n);
        return n;
    }
    char *large = malloc((size_t)n + 1);
    if (!large) {
        freak_pal_put(fp, small, sizeof small - 1);
        return n;
    }
    vsnprintf(large, (size_t)n + 1, f, ap);
    freak_pal_put(fp, large, (size_t)n);
    free(large);
    return n;
}

int fprintf(FILE *fp, const char *f, ...) {
    va_list ap;
    va_start(ap, f);
    int r = vfprintf(fp, f, ap);
    va_end(ap);
    return r;
}

int printf(const char *f, ...) {
    va_list ap;
    va_start(ap, f);
    int r = vfprintf(freak_pal_stdout, f, ap);
    va_end(ap);
    return r;
}

/* ---- numbers ----------------------------------------------------------- */

long long strtoll(const char *s, char **end, int base) {
    (void)base;
    const char *p = s;
    while (*p == ' ' || *p == '\t' || *p == '\n' || *p == '\r' || *p == '\f' || *p == '\v') p++;
    bool negative = false;
    if (*p == '-' || *p == '+') negative = *p++ == '-';
    const char *digits = p;
    unsigned long long value = 0;
    bool overflow = false;
    unsigned long long limit = negative ? (unsigned long long)INT64_MAX + 1u : (unsigned long long)INT64_MAX;
    while (*p >= '0' && *p <= '9') {
        unsigned digit = (unsigned)(*p++ - '0');
        if (value > (limit - digit) / 10) overflow = true;
        else value = value * 10 + digit;
    }
    if (end) *end = (char *)(p == digits ? s : p);
    if (p == digits) return 0;
    if (overflow) {
        freak_pal_errno = 68; /* ERANGE */
        return negative ? INT64_MIN : INT64_MAX;
    }
    return negative ? (long long)(0ull - value) : (long long)value;
}

long long atoll(const char *s) { return strtoll(s, NULL, 10); }

/* Decimal-only strtod for the bootstrap word_to_num path. Strict V4 code
   parses numbers itself; this keeps the symbol defined and close to libc. */
double strtod(const char *s, char **end) {
    const char *p = s;
    while (*p == ' ' || *p == '\t' || *p == '\n' || *p == '\r') p++;
    bool negative = false;
    if (*p == '-' || *p == '+') negative = *p++ == '-';
    double value = 0;
    bool any = false;
    while (*p >= '0' && *p <= '9') { value = value * 10 + (*p++ - '0'); any = true; }
    if (*p == '.') {
        p++;
        double scale = 0.1;
        while (*p >= '0' && *p <= '9') { value += (*p++ - '0') * scale; scale /= 10; any = true; }
    }
    if (any && (*p == 'e' || *p == 'E')) {
        const char *mark = p++;
        bool minus = false;
        if (*p == '-' || *p == '+') minus = *p++ == '-';
        if (*p >= '0' && *p <= '9') {
            int e = 0;
            while (*p >= '0' && *p <= '9') { if (e < 4000) e = e * 10 + (*p - '0'); p++; }
            while (e--) value = minus ? value / 10 : value * 10;
        } else {
            p = mark;
        }
    }
    if (end) *end = (char *)(any ? p : s);
    return negative ? -value : value;
}

char *getenv(const char *name) {
    (void)name;
    return NULL;
}

/* ---- process ----------------------------------------------------------- */

static void (*freak_pal_exit_fns[32])(void);
static int freak_pal_exit_count;

int atexit(void (*fn)(void)) {
    if (freak_pal_exit_count == 32) return -1;
    freak_pal_exit_fns[freak_pal_exit_count++] = fn;
    return 0;
}

_Noreturn void _Exit(int code) { freak_wasi_proc_exit(code); }

_Noreturn void exit(int code) {
    while (freak_pal_exit_count) freak_pal_exit_fns[--freak_pal_exit_count]();
    fflush(freak_pal_stdout);
    freak_wasi_proc_exit(code);
}

/* A trap, like SIGABRT: buffered stdout is dropped and the host reports it. */
_Noreturn void abort(void) { __builtin_trap(); }

extern int freak_pal_user_main(int, char **) __asm__("main");

__attribute__((export_name("_start"))) void _start(void) {
    size_t argc = 0, bytes = 0;
    if (freak_wasi_args_sizes_get(&argc, &bytes) != 0) argc = bytes = 0;
    char **argv = malloc((argc + 1) * sizeof(char *));
    char *strings = malloc(bytes ? bytes : 1);
    if (!argv || !strings) _Exit(70);
    if (argc && freak_wasi_args_get(argv, strings) != 0) argc = 0;
    argv[argc] = NULL;
    exit(freak_pal_user_main((int)argc, argv));
}

/* ---- files: no preopens yet, so every open fails cleanly --------------- */

int open(const char *path, int flags, ...) {
    (void)path;
    (void)flags;
    freak_pal_errno = ENOENT;
    return -1;
}

ssize_t read(int fd, void *buf, size_t n) {
    (void)fd;
    (void)buf;
    (void)n;
    freak_pal_errno = EIO;
    return -1;
}

int close(int fd) {
    (void)fd;
    return 0;
}

int fstat(int fd, struct stat *st) {
    (void)fd;
    (void)st;
    freak_pal_errno = EIO;
    return -1;
}

FILE *fdopen(int fd, const char *mode) { (void)fd; (void)mode; return NULL; }
FILE *fopen(const char *path, const char *mode) { (void)path; (void)mode; freak_pal_errno = ENOENT; return NULL; }
size_t fread(void *b, size_t s, size_t n, FILE *f) { (void)b; (void)s; (void)n; (void)f; return 0; }
int fclose(FILE *f) { (void)f; return 0; }
int ferror(FILE *f) { (void)f; return 1; }
int feof(FILE *f) { (void)f; return 1; }
int fseek(FILE *f, long offset, int whence) { (void)f; (void)offset; (void)whence; return -1; }
long ftell(FILE *f) { (void)f; return -1; }
int fgetc(FILE *f) { (void)f; return EOF; }

/* ---- compiler-rt ------------------------------------------------------- */

/* i64 overflow checks lower to a 128-bit multiply on wasm32. */
typedef __int128 freak_pal_ti;
freak_pal_ti __multi3(freak_pal_ti a, freak_pal_ti b) {
    uint64_t al = (uint64_t)a, ah = (uint64_t)(a >> 64), bl = (uint64_t)b, bh = (uint64_t)(b >> 64);
    uint64_t a0 = al & 0xffffffffu, a1 = al >> 32, b0 = bl & 0xffffffffu, b1 = bl >> 32;
    uint64_t p00 = a0 * b0, p01 = a0 * b1, p10 = a1 * b0, p11 = a1 * b1;
    uint64_t mid = (p00 >> 32) + (p01 & 0xffffffffu) + (p10 & 0xffffffffu);
    uint64_t lo = (p00 & 0xffffffffu) | (mid << 32);
    uint64_t hi = p11 + (p01 >> 32) + (p10 >> 32) + (mid >> 32) + al * bh + ah * bl;
    return (freak_pal_ti)(((unsigned __int128)hi << 64) | lo);
}
