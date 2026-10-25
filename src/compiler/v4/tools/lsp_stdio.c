/* See lsp_stdio.h. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "lsp_stdio.h"

#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#include <windows.h>
#include <psapi.h>
#else
#include <signal.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#endif
#ifdef __APPLE__
#include <mach/mach.h>
#endif

static bool lspio_eof = false;

static void* lspio_alloc(size_t size) {
    void* block = malloc(size ? size : 1);
    if (!block) {
        fputs("freak-lsp: out of memory\n", stderr);
        exit(1);
    }
    return block;
}

void lspio_init(void) {
#ifdef _WIN32
    /* Text mode would rewrite \n as \r\n and break Content-Length. */
    (void)_setmode(_fileno(stdin), _O_BINARY);
    (void)_setmode(_fileno(stdout), _O_BINARY);
#endif
}

bool lspio_at_eof(void) {
    return lspio_eof;
}

static freak_word lspio_stream_line(FILE* stream, bool* eof) {
    size_t cap = 128, len = 0;
    char* line = (char*)lspio_alloc(cap);
    int ch;
    while ((ch = fgetc(stream)) != EOF && ch != '\n') {
        if (len + 1 >= cap) {
            cap *= 2;
            char* grown = (char*)realloc(line, cap);
            if (!grown) { free(line); fputs("freak-lsp: out of memory\n", stderr); exit(1); }
            line = grown;
        }
        line[len++] = (char)ch;
    }
    if (ch == EOF && len == 0) *eof = true;
    if (len > 0 && line[len - 1] == '\r') len--;
    line[len] = '\0';
    return freak_word_own(line, len);
}

static freak_word lspio_stream_exact(FILE* stream, bool* eof, int64_t count) {
    if (count < 0) count = 0;
    char* body = (char*)lspio_alloc((size_t)count + 1);
    size_t got = fread(body, 1, (size_t)count, stream);
    if (got < (size_t)count) *eof = true;
    body[got] = '\0';
    return freak_word_own(body, got);
}

static void lspio_stream_send(FILE* stream, freak_word body) {
    fprintf(stream, "Content-Length: %zu\r\n\r\n", body.length);
    if (body.length) fwrite(body.data, 1, body.length, stream);
    fflush(stream);
}

freak_word lspio_read_line(void) {
    return lspio_stream_line(stdin, &lspio_eof);
}

freak_word lspio_read_exact(int64_t count) {
    return lspio_stream_exact(stdin, &lspio_eof, count);
}

void lspio_write_message(freak_word body) {
    lspio_stream_send(stdout, body);
}

void lspio_log(freak_word message) {
    fputs("[freak-lsp] ", stderr);
    if (message.length) fwrite(message.data, 1, message.length, stderr);
    fputc('\n', stderr);
    fflush(stderr);
}

int64_t lspio_byte_at(freak_word text, int64_t index) {
    if (index < 0 || (size_t)index >= text.length) return -1;
    return (int64_t)(unsigned char)text.data[index];
}

int64_t lspio_find_byte(freak_word text, int64_t byte_value, int64_t start) {
    if (start < 0) start = 0;
    if ((size_t)start >= text.length) return -1;
    const void* hit = memchr(text.data + start, (int)byte_value, text.length - (size_t)start);
    return hit ? (int64_t)((const char*)hit - text.data) : -1;
}

/* `start` indexes the opening quote; returns the index just past the closing quote. */
int64_t lspio_json_string_end(freak_word text, int64_t start) {
    size_t i = (size_t)start + 1;
    while (i < text.length) {
        char c = text.data[i];
        if (c == '\\') { i += 2; continue; }
        if (c == '"') return (int64_t)(i + 1);
        i++;
    }
    return (int64_t)text.length;
}

static int lspio_hex(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

static long lspio_hex4(const char* p, size_t left) {
    if (left < 4) return -1;
    long v = 0;
    for (int k = 0; k < 4; k++) {
        int h = lspio_hex(p[k]);
        if (h < 0) return -1;
        v = (v << 4) | h;
    }
    return v;
}

static size_t lspio_put_utf8(char* out, unsigned long cp) {
    if (cp < 0x80) { out[0] = (char)cp; return 1; }
    if (cp < 0x800) { out[0] = (char)(0xC0 | (cp >> 6)); out[1] = (char)(0x80 | (cp & 0x3F)); return 2; }
    if (cp < 0x10000) {
        out[0] = (char)(0xE0 | (cp >> 12)); out[1] = (char)(0x80 | ((cp >> 6) & 0x3F));
        out[2] = (char)(0x80 | (cp & 0x3F)); return 3;
    }
    out[0] = (char)(0xF0 | (cp >> 18)); out[1] = (char)(0x80 | ((cp >> 12) & 0x3F));
    out[2] = (char)(0x80 | ((cp >> 6) & 0x3F)); out[3] = (char)(0x80 | (cp & 0x3F));
    return 4;
}

/* Decodes the JSON string whose opening quote is at `start`. */
freak_word lspio_json_unescape(freak_word text, int64_t start) {
    size_t end = (size_t)lspio_json_string_end(text, start);
    size_t i = (size_t)start + 1;
    char* out = (char*)lspio_alloc(end - i + 1);
    size_t n = 0;
    while (i < text.length) {
        char c = text.data[i];
        if (c == '"') break;
        if (c != '\\' || i + 1 >= text.length) { out[n++] = c; i++; continue; }
        char e = text.data[i + 1];
        i += 2;
        switch (e) {
            case 'n': out[n++] = '\n'; break;
            case 't': out[n++] = '\t'; break;
            case 'r': out[n++] = '\r'; break;
            case 'b': out[n++] = '\b'; break;
            case 'f': out[n++] = '\f'; break;
            case 'u': {
                long cp = lspio_hex4(text.data + i, text.length - i);
                if (cp < 0) { out[n++] = '?'; break; }
                i += 4;
                if (cp >= 0xD800 && cp <= 0xDBFF && i + 6 <= text.length &&
                    text.data[i] == '\\' && text.data[i + 1] == 'u') {
                    long lo = lspio_hex4(text.data + i + 2, text.length - i - 2);
                    if (lo >= 0xDC00 && lo <= 0xDFFF) {
                        cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                        i += 6;
                    }
                }
                /* A \u escape is six source bytes and at most four output bytes. */
                n += lspio_put_utf8(out + n, (unsigned long)cp);
                break;
            }
            default: out[n++] = e; break;
        }
    }
    out[n] = '\0';
    return freak_word_own(out, n);
}

freak_word lspio_json_escape(freak_word text) {
    char* out = (char*)lspio_alloc(text.length * 6 + 1);
    size_t n = 0;
    for (size_t i = 0; i < text.length; i++) {
        unsigned char c = (unsigned char)text.data[i];
        switch (c) {
            case '"': out[n++] = '\\'; out[n++] = '"'; break;
            case '\\': out[n++] = '\\'; out[n++] = '\\'; break;
            case '\n': out[n++] = '\\'; out[n++] = 'n'; break;
            case '\r': out[n++] = '\\'; out[n++] = 'r'; break;
            case '\t': out[n++] = '\\'; out[n++] = 't'; break;
            default:
                if (c < 0x20) n += (size_t)sprintf(out + n, "\\u%04x", c);
                else out[n++] = (char)c;
        }
    }
    out[n] = '\0';
    return freak_word_own(out, n);
}

bool lspio_is_windows(void) {
#ifdef _WIN32
    return true;
#else
    return false;
#endif
}

/* file:///home/a%20b/x.fk -> /home/a b/x.fk; file:///C:/x.fk -> C:/x.fk.
   Returns an empty word for non-file URIs. */
freak_word lspio_uri_to_path(freak_word uri) {
    const char* prefix = "file://";
    size_t plen = strlen(prefix);
    if (uri.length < plen || strncmp(uri.data, prefix, plen) != 0) {
        return freak_word_own((char*)lspio_alloc(1), 0);
    }
    size_t i = plen;
    char* out = (char*)lspio_alloc(uri.length + 3);
    size_t n = 0;
    if (i < uri.length && uri.data[i] != '/') {
        /* UNC authority: file://server/share -> //server/share */
        out[n++] = '/'; out[n++] = '/';
    }
    for (; i < uri.length; i++) {
        char c = uri.data[i];
        if (c == '%' && i + 2 < uri.length && lspio_hex(uri.data[i + 1]) >= 0 && lspio_hex(uri.data[i + 2]) >= 0) {
            out[n++] = (char)((lspio_hex(uri.data[i + 1]) << 4) | lspio_hex(uri.data[i + 2]));
            i += 2;
        } else {
            out[n++] = c;
        }
    }
    out[n] = '\0';
#ifdef _WIN32
    /* /C:/x -> C:/x */
    if (n >= 3 && out[0] == '/' && out[2] == ':') {
        memmove(out, out + 1, n);
        n--;
    }
    for (size_t k = 0; k < n; k++) if (out[k] == '/') out[k] = '\\';
#endif
    return freak_word_own(out, n);
}

bool lspio_file_exists(freak_word path) {
    const char* cpath = freak_word_to_cstr(path);
    FILE* f = fopen(cpath, "rb");
    if (!f) return false;
    fclose(f);
    return true;
}

/* Runs a shell command line and returns its combined output. The caller
   redirects stdin so the child never reads the LSP stream. */
freak_word lspio_run_capture(freak_word command) {
    const char* cmd = freak_word_to_cstr(command);
    fflush(stdout);
#ifdef _WIN32
    FILE* pipe = _popen(cmd, "rb");
#else
    FILE* pipe = popen(cmd, "r");
#endif
    if (!pipe) return freak_word_own((char*)lspio_alloc(1), 0);
    size_t cap = 4096, len = 0, got;
    char* buf = (char*)lspio_alloc(cap);
    while ((got = fread(buf + len, 1, cap - len - 1, pipe)) > 0) {
        len += got;
        if (len + 1 >= cap) {
            cap *= 2;
            char* grown = (char*)realloc(buf, cap);
            if (!grown) { free(buf); fputs("freak-lsp: out of memory\n", stderr); exit(1); }
            buf = grown;
        }
    }
#ifdef _WIN32
    _pclose(pipe);
#else
    pclose(pipe);
#endif
    buf[len] = '\0';
    return freak_word_own(buf, len);
}

/* ------------------------------------------------------------------ */
/* Supervisor <-> worker. The bootstrap runtime never frees words, so  */
/* the analysis runs in a worker process that the supervisor replaces  */
/* when it grows too large (or crashes), replaying open documents.     */
/* ------------------------------------------------------------------ */

static FILE* lspio_worker_in = NULL;   /* supervisor writes requests */
static FILE* lspio_worker_out = NULL;  /* supervisor reads replies   */
static bool lspio_worker_eof_flag = false;
#ifdef _WIN32
static HANDLE lspio_worker_process = NULL;
#else
static pid_t lspio_worker_pid = -1;
#endif

bool lspio_is_worker(void) {
    const char* flag = getenv("FREAK_LSP_WORKER");
    return flag && flag[0] == '1';
}

int64_t lspio_env_int(freak_word name, int64_t fallback) {
    const char* value = getenv(freak_word_to_cstr(name));
    if (!value || !*value) return fallback;
    char* end = NULL;
    long long parsed = strtoll(value, &end, 10);
    return (end && *end == '\0') ? (int64_t)parsed : fallback;
}

int64_t lspio_rss_mb(void) {
#if defined(_WIN32)
    PROCESS_MEMORY_COUNTERS counters;
    if (K32GetProcessMemoryInfo(GetCurrentProcess(), &counters, sizeof(counters)))
        return (int64_t)(counters.WorkingSetSize / (1024 * 1024));
    return 0;
#elif defined(__APPLE__)
    struct mach_task_basic_info info;
    mach_msg_type_number_t count = MACH_TASK_BASIC_INFO_COUNT;
    if (task_info(mach_task_self(), MACH_TASK_BASIC_INFO, (task_info_t)&info, &count) == KERN_SUCCESS)
        return (int64_t)(info.resident_size / (1024 * 1024));
    return 0;
#else
    FILE* statm = fopen("/proc/self/statm", "r");
    long pages = 0, resident = 0;
    if (!statm) return 0;
    if (fscanf(statm, "%ld %ld", &pages, &resident) != 2) resident = 0;
    fclose(statm);
    return (int64_t)resident * (int64_t)sysconf(_SC_PAGESIZE) / (1024 * 1024);
#endif
}

bool lspio_worker_spawn(void) {
    lspio_worker_eof_flag = false;
#ifdef _WIN32
    wchar_t self[32768];
    DWORD len = GetModuleFileNameW(NULL, self, 32768);
    if (len == 0 || len >= 32768) return false;
    SECURITY_ATTRIBUTES inherit = { sizeof(SECURITY_ATTRIBUTES), NULL, TRUE };
    HANDLE child_in_read, child_in_write, child_out_read, child_out_write;
    if (!CreatePipe(&child_in_read, &child_in_write, &inherit, 0)) return false;
    if (!CreatePipe(&child_out_read, &child_out_write, &inherit, 0)) {
        CloseHandle(child_in_read); CloseHandle(child_in_write); return false;
    }
    SetHandleInformation(child_in_write, HANDLE_FLAG_INHERIT, 0);
    SetHandleInformation(child_out_read, HANDLE_FLAG_INHERIT, 0);
    STARTUPINFOW startup;
    PROCESS_INFORMATION info;
    ZeroMemory(&startup, sizeof(startup));
    ZeroMemory(&info, sizeof(info));
    startup.cb = sizeof(startup);
    startup.dwFlags = STARTF_USESTDHANDLES;
    startup.hStdInput = child_in_read;
    startup.hStdOutput = child_out_write;
    startup.hStdError = GetStdHandle(STD_ERROR_HANDLE);
    wchar_t command[32800];
    _snwprintf(command, 32800, L"\"%ls\"", self);
    SetEnvironmentVariableW(L"FREAK_LSP_WORKER", L"1");
    BOOL started = CreateProcessW(self, command, NULL, NULL, TRUE, CREATE_NO_WINDOW,
                                  NULL, NULL, &startup, &info);
    SetEnvironmentVariableW(L"FREAK_LSP_WORKER", NULL);
    CloseHandle(child_in_read);
    CloseHandle(child_out_write);
    if (!started) {
        CloseHandle(child_in_write); CloseHandle(child_out_read); return false;
    }
    CloseHandle(info.hThread);
    lspio_worker_process = info.hProcess;
    lspio_worker_in = _fdopen(_open_osfhandle((intptr_t)child_in_write, _O_BINARY), "wb");
    lspio_worker_out = _fdopen(_open_osfhandle((intptr_t)child_out_read, _O_BINARY | _O_RDONLY), "rb");
#else
    int to_child[2], from_child[2];
    if (pipe(to_child) != 0) return false;
    if (pipe(from_child) != 0) { close(to_child[0]); close(to_child[1]); return false; }
    signal(SIGPIPE, SIG_IGN);
    char self[4096];
    ssize_t n = readlink("/proc/self/exe", self, sizeof(self) - 1);
    const char* program = NULL;
    if (n > 0) { self[n] = '\0'; program = self; }
    pid_t pid = fork();
    if (pid < 0) return false;
    if (pid == 0) {
        dup2(to_child[0], 0);
        dup2(from_child[1], 1);
        close(to_child[0]); close(to_child[1]); close(from_child[0]); close(from_child[1]);
        setenv("FREAK_LSP_WORKER", "1", 1);
        extern char** freak_argv;
        if (program) execv(program, freak_argv);
        execvp(freak_argv[0], freak_argv);
        _exit(127);
    }
    close(to_child[0]);
    close(from_child[1]);
    lspio_worker_pid = pid;
    lspio_worker_in = fdopen(to_child[1], "w");
    lspio_worker_out = fdopen(from_child[0], "r");
#endif
    return lspio_worker_in && lspio_worker_out;
}

void lspio_worker_send(freak_word body) {
    if (lspio_worker_in) lspio_stream_send(lspio_worker_in, body);
}

freak_word lspio_worker_read_line(void) {
    if (!lspio_worker_out) { lspio_worker_eof_flag = true; return freak_word_own((char*)lspio_alloc(1), 0); }
    return lspio_stream_line(lspio_worker_out, &lspio_worker_eof_flag);
}

freak_word lspio_worker_read_exact(int64_t count) {
    return lspio_stream_exact(lspio_worker_out, &lspio_worker_eof_flag, count);
}

bool lspio_worker_at_eof(void) {
    return lspio_worker_eof_flag;
}

/* Closes the pipes and returns the worker's exit code. */
int64_t lspio_worker_wait(void) {
    if (lspio_worker_in) { fclose(lspio_worker_in); lspio_worker_in = NULL; }
    if (lspio_worker_out) { fclose(lspio_worker_out); lspio_worker_out = NULL; }
#ifdef _WIN32
    DWORD code = 1;
    if (lspio_worker_process) {
        WaitForSingleObject(lspio_worker_process, INFINITE);
        GetExitCodeProcess(lspio_worker_process, &code);
        CloseHandle(lspio_worker_process);
        lspio_worker_process = NULL;
    }
    return (int64_t)code;
#else
    int status = 0;
    if (lspio_worker_pid > 0) {
        while (waitpid(lspio_worker_pid, &status, 0) < 0) {}
        lspio_worker_pid = -1;
    }
    return WIFEXITED(status) ? WEXITSTATUS(status) : 1;
#endif
}
