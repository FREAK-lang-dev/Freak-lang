#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
/* ctype.h no longer needed — toupper/tolower/isspace moved to LLVM IR */
#ifndef _WIN32
#include <unistd.h>
#endif

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
/* fs_read, fs_write, fs_append, fs_exists, fs_delete are now pure FREAK
   tasks in std/runtime.fk. They call libc via i64 IR wrappers. */

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
    return (int64_t)buf;
}

/* ── Panic ──────────────────────────────────────────── */
/* freak_llvm_panic is now a pure LLVM IR intrinsic. */

/* ── Shape (struct) helpers ─────────────────────────── */
/* freak_llvm_shape_alloc, shape_get, shape_set are now
   defined as pure LLVM IR intrinsics (calloc + GEP). */

/* ── LLVM wrapper aliases ───────────────────────────── */
/* All word function wrappers removed — now pure LLVM IR intrinsics. */

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

/* freak_llvm_word_from_num, print_num, int_to_num, num_to_int, word_compare
   are now pure LLVM IR intrinsics. */

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
/* freak_llvm_setup_args is now a pure LLVM IR intrinsic. */
