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
/* freak_llvm_say, print_str, print_int, print_newline are now
   defined as pure LLVM IR intrinsics in the emitted .ll file. */

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
/* freak_llvm_process_args_count and process_arg are now
   defined as pure LLVM IR intrinsics reading @__freak_argc/@__freak_argv globals. */

void freak_llvm_process_exit(int64_t code) {
    exit((int)code);
}

int64_t freak_llvm_process_exec(int64_t cmd_p) {
    const char* cmd = (const char*)cmd_p;
    return (int64_t)system(cmd);
}

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
    return (int64_t)buf;
}

/* ── Panic ──────────────────────────────────────────── */

void freak_llvm_panic(int64_t msg_p) {
    fprintf(stderr, "PANIC: %s\n", (char*)msg_p);
    exit(1);
}

/* ── Shape (struct) helpers ─────────────────────────── */
/* freak_llvm_shape_alloc, shape_get, shape_set are now
   defined as pure LLVM IR intrinsics (calloc + GEP). */

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

/* freak_llvm_print_num, int_to_num, num_to_int are now
   defined as pure LLVM IR intrinsics (bitcast + sitofp/fptosi). */

/* ── String comparison ─────────────────────────────── */

int64_t freak_word_compare(int64_t ap, int64_t bp) {
    char* a = (char*)ap;
    char* b = (char*)bp;
    int r = strcmp(a, b);
    if (r < 0) return -1;
    if (r > 0) return 1;
    return 0;
}

/* ── Dynamic Arrays ────────────────────────────────── */
/* Same pool system as freak_runtime.c but with i64 interface */

typedef struct {
    int64_t* data;     /* stored as i64 (cast from char*) */
    int64_t length;
    int64_t capacity;
} freak_llvm_dyn_array;

#define FREAK_LLVM_MAX_ARRAYS 256
static freak_llvm_dyn_array freak_llvm_arrays[FREAK_LLVM_MAX_ARRAYS];
static int64_t freak_llvm_array_count = 0;

int64_t freak_array_new(void) {
    if (freak_llvm_array_count >= FREAK_LLVM_MAX_ARRAYS) {
        fprintf(stderr, "FREAK: too many arrays (max %d)\n", FREAK_LLVM_MAX_ARRAYS);
        exit(1);
    }
    int64_t h = freak_llvm_array_count++;
    freak_llvm_arrays[h].length = 0;
    freak_llvm_arrays[h].capacity = 64;
    freak_llvm_arrays[h].data = (int64_t*)malloc(64 * sizeof(int64_t));
    return h;
}

void freak_array_push(int64_t handle, int64_t item) {
    if (handle < 0 || handle >= freak_llvm_array_count) return;
    freak_llvm_dyn_array* a = &freak_llvm_arrays[handle];
    if (a->length >= a->capacity) {
        a->capacity *= 2;
        a->data = (int64_t*)realloc(a->data, (size_t)a->capacity * sizeof(int64_t));
    }
    a->data[a->length++] = item;
}

int64_t freak_array_get(int64_t handle, int64_t index) {
    if (handle < 0 || handle >= freak_llvm_array_count) return (int64_t)"";
    freak_llvm_dyn_array* a = &freak_llvm_arrays[handle];
    if (index < 0 || index >= a->length) return (int64_t)"";
    return a->data[index];
}

int64_t freak_array_len(int64_t handle) {
    if (handle < 0 || handle >= freak_llvm_array_count) return 0;
    return freak_llvm_arrays[handle].length;
}

void freak_array_set(int64_t handle, int64_t index, int64_t item) {
    if (handle < 0 || handle >= freak_llvm_array_count) return;
    freak_llvm_dyn_array* a = &freak_llvm_arrays[handle];
    if (index < 0 || index >= a->length) return;
    a->data[index] = item;
}

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
int64_t freak_tcp_connect(int64_t host_ptr, int64_t port) {
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
int64_t freak_tcp_send(int64_t fd, int64_t data_ptr) {
    char* data = (char*)data_ptr;
    int len = (int)strlen(data);
#ifdef _WIN32
    return (int64_t)send((SOCKET)fd, data, len, 0);
#else
    return (int64_t)send((int)fd, data, len, 0);
#endif
}

/* freak_tcp_recv(fd, max_bytes) -> string pointer (caller-owned) */
int64_t freak_tcp_recv(int64_t fd, int64_t max_bytes) {
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
    return (int64_t)buf;
}

/* freak_tcp_recv_all(fd, max_bytes) -> read until connection closes */
int64_t freak_tcp_recv_all(int64_t fd, int64_t max_bytes) {
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
    return (int64_t)buf;
}

/* freak_tcp_close(fd) -> void */
void freak_tcp_close(int64_t fd) {
#ifdef _WIN32
    closesocket((SOCKET)fd);
#else
    close((int)fd);
#endif
}

/* ── Entry point setup ──────────────────────────────── */
/* freak_llvm_setup_args is now defined as a pure LLVM IR intrinsic
   that stores argc/argv to @__freak_argc/@__freak_argv globals.
   The C-side process_exec/exit/exec_capture functions that need g_argc/g_argv
   are not affected — they still use the C globals below. However, these C globals
   are no longer populated by setup_args. Process functions that rely on them
   (exec, exit, exec_capture) don't use g_argc/g_argv so this is fine. */

