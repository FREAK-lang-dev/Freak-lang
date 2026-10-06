/* Real CRT argv / runtime argument API probe. Windows hooks inject failures
   into checked operations; successful paths use the actual UCRT and Win32 API. */
#ifdef _WIN32
#ifndef _WIN32_WINNT
#define _WIN32_WINNT 0x0602
#endif
#elif defined(__APPLE__)
#define _DARWIN_C_SOURCE 1
#define _POSIX_C_SOURCE 200809L
#else
#define _POSIX_C_SOURCE 200809L
#endif
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <errno.h>
#ifdef _WIN32
#include <winsock2.h>
#include <windows.h>
#include <corecrt_startup.h>
#endif

static int probe_fault, probe_raw_count;
static char **probe_raw_arguments;
static size_t probe_live, probe_allocations;
static int probe_tracking;

#ifdef _WIN32
static errno_t __cdecl probe_configure(_crt_argv_mode mode) {
    probe_tracking = 1;
    return probe_fault == 1 ? EINVAL : _configure_wide_argv(mode);
}
static void *probe_malloc(size_t size) {
    ++probe_allocations;
    if ((probe_fault == 3 && probe_allocations == 2) ||
        (probe_fault == 4 && probe_allocations == 4)) return NULL;
    void *result = malloc(size);
    if (result && probe_tracking) ++probe_live;
    return result;
}
static void *probe_calloc(size_t count, size_t size) {
    ++probe_allocations;
    if (probe_fault == 2) return NULL;
    void *result = calloc(count, size);
    if (result && probe_tracking) ++probe_live;
    return result;
}
static void probe_free(void *pointer) {
    if (pointer && probe_tracking) { assert(probe_live); --probe_live; }
    free(pointer);
}
static int WINAPI probe_encode(UINT page, DWORD flags, LPCWCH input, int length,
                               LPSTR output, int capacity, LPCCH default_char,
                               LPBOOL used_default) {
    if ((probe_fault == 5 && !output) || (probe_fault == 6 && output)) return 0;
    return WideCharToMultiByte(page, flags, input, length, output, capacity,
                               default_char, used_default);
}
static wchar_t **probe_wide_arguments(void) {
    wchar_t **wide = *__p___wargv();
    if (probe_fault == 7) return NULL;
    if (probe_fault == 8) {
        /* Own only this pointer vector and the malformed string. The real
           Win32 converter must reject it; leave CRT storage untouched. */
        static wchar_t malformed[] = {0xd800, 0};
        static wchar_t *copy[128];
        int count = *__p___argc();
        assert(count > 1 && count < 128);
        for (int i = 0; i <= count; ++i) copy[i] = wide[i];
        copy[1] = malformed;
        return copy;
    }
    return wide;
}
#define _configure_wide_argv probe_configure
#define malloc probe_malloc
#define calloc probe_calloc
#define free probe_free
#define WideCharToMultiByte probe_encode
#undef __wargv
#define __wargv probe_wide_arguments()
#endif
#include "../freakc/runtime/freak_runtime.c"
#ifdef _WIN32
#undef _configure_wide_argv
#undef malloc
#undef calloc
#undef free
#undef WideCharToMultiByte
#undef __wargv
#define __wargv (*__p___wargv())
#endif

static freak_word probe_retained;
static char probe_retained_bytes[1024];
static int probe_admitted;

static void probe_exit_before(void) {
    if (probe_fault) {
#ifdef _WIN32
        if (probe_live || freak_argv != probe_raw_arguments || freak_argc != probe_raw_count) {
            fputs("argv failure published or leaked a snapshot\n", stderr);
            fflush(stderr);
            _Exit(72);
        }
#endif
        assert(!probe_live);
        assert(freak_argv == probe_raw_arguments && freak_argc == probe_raw_count);
        puts("argv-failed-cleanly");
        return;
    }
    assert(probe_admitted);
    assert(!probe_retained.heap && !strcmp(probe_retained.data, probe_retained_bytes));
    assert(freak_args_count() == probe_raw_count);
    assert(!strcmp(freak_process_arg(3).data, probe_retained_bytes));
    puts("argv-exit-before-ok");
}

static void probe_exit_after(void) {
    assert(!strcmp(probe_retained.data, probe_retained_bytes));
    assert(freak_llvm_process_args_count() == probe_raw_count);
    puts("argv-exit-after-ok");
}

void argv_probe_prepare(int argc, char **argv) {
    probe_raw_count = argc; probe_raw_arguments = argv;
    freak_argc = argc; freak_argv = argv;
    const char *fault = getenv("FREAK_BOOTSTRAP_ARGV_FAULT");
    probe_fault = fault ? atoi(fault) : 0;
    assert(atexit(probe_exit_before) == 0);
}

static void probe_hex(const char *label, int index, const char *text) {
    printf("%s %d ", label, index);
    for (const unsigned char *p = (const unsigned char *)text; *p; ++p)
        printf("%02x", (unsigned)*p);
    putchar('\n');
}

#ifdef _WIN32
static HANDLE probe_start;
static DWORD WINAPI probe_first_access(void *parameter) {
    (void)parameter;
    assert(WaitForSingleObject(probe_start, INFINITE) == WAIT_OBJECT_0);
    for (int i = 0; i < 50; ++i) assert(freak_process_args_count() == probe_raw_count);
    return 0;
}
#endif

int argv_probe_run(void) {
#ifdef _WIN32
    if (!probe_fault) {
        HANDLE threads[12];
        probe_start = CreateEventW(NULL, TRUE, FALSE, NULL); assert(probe_start);
        for (int i = 0; i < 12; ++i) {
            threads[i] = CreateThread(NULL, 0, probe_first_access, NULL, 0, NULL);
            assert(threads[i]);
        }
        assert(SetEvent(probe_start));
        assert(WaitForMultipleObjects(12, threads, TRUE, INFINITE) == WAIT_OBJECT_0);
        for (int i = 0; i < 12; ++i) assert(CloseHandle(threads[i]));
        assert(CloseHandle(probe_start));
    }
#endif
    assert(freak_args_count() == probe_raw_count);
#ifdef _WIN32
    assert(probe_live == (size_t)probe_raw_count + 1);
    probe_tracking = 0;
#endif
    char **arguments = freak_process_args();
    assert(arguments && arguments == freak_argv);
    assert(freak_process_args_count() == probe_raw_count);
    assert(freak_llvm_process_args_count() == probe_raw_count);
    for (int i = 0; i < probe_raw_count; ++i) {
        freak_word legacy = freak_arg(i), process = freak_process_arg(i);
        int64_t owned = freak_llvm_process_arg(i);
        assert(!legacy.heap && !process.heap);
        assert(legacy.data == arguments[i] && process.data == arguments[i]);
        assert(legacy.length == strlen(arguments[i]) && process.length == legacy.length);
        assert(owned && (char *)owned != arguments[i] && !strcmp((char *)owned, arguments[i]));
        assert(freak_llvm_word_view(owned).length == legacy.length);
        probe_hex("arg", i, arguments[i]);
        freak_llvm_word_release_replaced(owned, 0);
        probe_hex("crt-narrow", i, probe_raw_arguments[i]);
#ifdef _WIN32
        wchar_t **wide = __wargv;
        int size = WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, wide[i], -1,
                                       NULL, 0, NULL, NULL);
        assert(size > 0);
        char *converted = malloc((size_t)size); assert(converted);
        assert(WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, wide[i], -1,
                                  converted, size, NULL, NULL) == size);
        probe_hex("crt-wide", i, converted); free(converted);
#endif
    }
    assert(!freak_process_arg(-1).length && !freak_process_arg(probe_raw_count).length);
    int64_t empty = freak_llvm_process_arg(-1);
    assert(empty && !freak_llvm_word_view(empty).length);
    freak_llvm_word_release_replaced(empty, 0);
    probe_retained = freak_arg(3);
    assert(probe_retained.length < sizeof(probe_retained_bytes));
    memcpy(probe_retained_bytes, probe_retained.data, probe_retained.length + 1);
    probe_admitted = 1;
    assert(atexit(probe_exit_after) == 0);
    const char *mode = getenv("FREAK_BOOTSTRAP_ARGV_MODE");
    if (mode && !strcmp(mode, "bounds")) (void)freak_arg(probe_raw_count);
    if (mode && !strcmp(mode, "leak")) (void)freak_llvm_process_arg(1);
#ifdef _WIN32
    freak_llvm_setup_args(0, 0);
#else
    freak_llvm_setup_args(probe_raw_count, (int64_t)probe_raw_arguments);
#endif
    assert(freak_args_count() == probe_raw_count && freak_process_args() == arguments);
    assert(freak_arg(3).data == probe_retained.data);
    puts("argv-apis-ok");
    return 0;
}

#ifndef ARGV_LLVM_MAIN
int main(int argc, char **argv) {
    argv_probe_prepare(argc, argv);
    return argv_probe_run();
}
#endif
