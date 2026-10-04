/* Exact private fs void/outslot bridge proof. Production core, Word and system
   sources are included unchanged; only named OS/storage calls are intercepted.
   These hooks are private negative controls, never a public FREAK/foreign ABI. */
#include "freak_runtime.c"
#include "freak_v4_word_runtime.h"
#include "freak_v4_system_runtime.h"
#include <assert.h>

enum {
    P_PATH_ALLOC = 1u << 0, P_OPEN = 1u << 1, P_STAT = 1u << 2,
    P_NONREGULAR = 1u << 3, P_STREAM = 1u << 4, P_NEG_SIZE = 1u << 5,
    P_SEEK = 1u << 6, P_CONTENT_ALLOC = 1u << 7, P_SHORT = 1u << 8,
    P_READ_ERROR = 1u << 9, P_EXTRA = 1u << 10, P_EOF_ERROR = 1u << 11,
    P_CLOSE = 1u << 12, P_ADOPT = 1u << 13, P_LARGE_SIZE = 1u << 14,
    P_DESC_CLOSE = 1u << 15, P_ERROR_COPY = 1u << 16,
    P_ERROR_TRACK = 1u << 17, P_WIDE_FIRST = 1u << 18,
    P_WIDE_SECOND = 1u << 19
};
static unsigned probe_fault;
static bool probe_active, probe_error_copy, probe_forbid_touch;
static unsigned probe_allocations, probe_error_queries, probe_wide_calls;
static size_t probe_last_allocation, probe_path_scans;
static int probe_descriptors;
static void *probe_raw[8];
static size_t probe_raw_count;
static int64_t probe_path, probe_tag = 117, probe_payload = 118;
static unsigned char *probe_saved_path;
static size_t probe_storage_length, probe_metadata_length;
static bool probe_fatal_slots, probe_fatal_reset;
static bool probe_directory, probe_stat_nonregular;
static int probe_open_result;
static unsigned probe_stat_calls, probe_stream_calls, probe_read_calls;
static unsigned probe_adopt_calls, probe_descriptor_closes;
static _Noreturn void probe_word_abort(void);

static void probe_untrack(void *pointer) {
    if (!pointer) return;
    size_t index = 0;
    while (index < probe_raw_count && probe_raw[index] != pointer) ++index;
    assert(index < probe_raw_count);
    probe_raw[index] = probe_raw[--probe_raw_count];
}
static void *probe_word_malloc(size_t size) {
    if (probe_error_copy && (probe_fault & P_ERROR_COPY)) return NULL;
    return malloc(size);
}
static int64_t probe_word_adopt(int64_t value, size_t length) {
    if (probe_error_copy && (probe_fault & P_ERROR_TRACK)) return 0;
    return freak_llvm_word_try_adopt_sized(value, length);
}
#define malloc probe_word_malloc
#define freak_llvm_word_try_adopt_sized probe_word_adopt
#define abort probe_word_abort
#include "freak_v4_word_runtime.c"
#undef malloc
#undef freak_llvm_word_try_adopt_sized
#undef abort

static void *probe_malloc(size_t size) {
    if (!probe_active) return malloc(size);
    assert(!probe_forbid_touch);
    ++probe_allocations;
    probe_last_allocation = size;
    if ((probe_allocations == 1 && (probe_fault & P_PATH_ALLOC)) ||
            (probe_allocations == 2 && (probe_fault & P_CONTENT_ALLOC))) return NULL;
    void *pointer = malloc(size);
    if (pointer) {
        assert(probe_raw_count < sizeof(probe_raw) / sizeof(probe_raw[0]));
        probe_raw[probe_raw_count++] = pointer;
    }
    return pointer;
}
static void probe_free(void *pointer) {
    if (probe_active) probe_untrack(pointer);
    free(pointer);
}
static void *probe_memchr(const void *bytes, int value, size_t length) {
    assert(!probe_forbid_touch);
    ++probe_path_scans;
    return memchr(bytes, value, length);
}
static int64_t probe_adopt(int64_t pointer, size_t length) {
    ++probe_adopt_calls;
    if (probe_fault & P_ADOPT) return 0;
    int64_t result = freak_llvm_word_try_adopt_sized(pointer, length);
    if (result) probe_untrack((void *)(uintptr_t)pointer);
    return result;
}
static int64_t probe_error_word(int64_t pointer, int64_t length) {
    probe_error_copy = true;
    int64_t owner = freak_v4_word_from_bytes(pointer, length);
    probe_error_copy = false;
    return owner;
}
static int probe_seek(FILE *file, long offset, int whence) {
    return probe_fault & P_SEEK ? -1 : fseek(file, offset, whence);
}
static size_t probe_read(void *data, size_t size, size_t count, FILE *file) {
    ++probe_read_calls;
    return probe_fault & P_SHORT ? (count ? fread(data, size, count - 1, file) : 0) :
        fread(data, size, count, file);
}
static int probe_getc(FILE *file) {
    return probe_fault & P_EXTRA ? 'x' : fgetc(file);
}
static int probe_error(FILE *file) {
    ++probe_error_queries;
    if ((probe_fault & P_READ_ERROR) && probe_error_queries == 1) return 1;
    if ((probe_fault & P_EOF_ERROR) && probe_error_queries == 2) return 1;
    return ferror(file);
}
static int probe_close_file(FILE *file) {
    int result = fclose(file);
    assert(probe_descriptors > 0);
    --probe_descriptors;
    return probe_fault & P_CLOSE ? EOF : result;
}
#ifdef _WIN32
static int probe_open(const wchar_t *name, int flags, ...) {
    assert(!probe_forbid_touch);
    assert((flags & _O_BINARY) != 0);
    if (probe_fault & P_OPEN) return -1;
    int descriptor = _wopen(name, flags);
    probe_open_result = descriptor;
    if (descriptor >= 0) ++probe_descriptors;
    return descriptor;
}
static int probe_stat(int descriptor, struct _stat64 *metadata) {
    ++probe_stat_calls;
    if (probe_fault & P_STAT) return -1;
    int result = _fstat64(descriptor, metadata);
    probe_stat_nonregular = !result && (metadata->st_mode & _S_IFMT) != _S_IFREG;
    if (!result && (probe_fault & P_NONREGULAR)) metadata->st_mode = 0;
    if (!result && (probe_fault & P_NEG_SIZE)) metadata->st_size = -1;
    if (!result && (probe_fault & P_LARGE_SIZE)) metadata->st_size = (int64_t)INT32_MAX + 19;
    return result;
}
static FILE *probe_fdopen(int descriptor, const char *mode) {
    ++probe_stream_calls;
    return probe_fault & P_STREAM ? NULL : _fdopen(descriptor, mode);
}
static int probe_close_descriptor(int descriptor) {
    ++probe_descriptor_closes;
    int result = _close(descriptor);
    assert(probe_descriptors > 0);
    --probe_descriptors;
    return probe_fault & P_DESC_CLOSE ? -1 : result;
}
static int probe_wide(UINT page, DWORD flags, LPCCH bytes, int count,
                      LPWSTR output, int capacity) {
    ++probe_wide_calls;
    if (((probe_fault & P_WIDE_FIRST) && probe_wide_calls == 1) ||
            ((probe_fault & P_WIDE_SECOND) && probe_wide_calls == 2)) return 0;
    return MultiByteToWideChar(page, flags, bytes, count, output, capacity);
}
#define _wopen probe_open
#define _fstat64 probe_stat
#define _fdopen probe_fdopen
#define _close probe_close_descriptor
#define MultiByteToWideChar probe_wide
#else
static int probe_open(const char *name, int flags, ...) {
    assert(!probe_forbid_touch);
    assert((flags & O_NONBLOCK) != 0);
    if (probe_fault & P_OPEN) return -1;
    int descriptor = open(name, flags);
    probe_open_result = descriptor;
    if (descriptor >= 0) ++probe_descriptors;
    return descriptor;
}
static int probe_stat(int descriptor, struct stat *metadata) {
    ++probe_stat_calls;
    if (probe_fault & P_STAT) return -1;
    int result = fstat(descriptor, metadata);
    probe_stat_nonregular = !result && !S_ISREG(metadata->st_mode);
    if (!result && (probe_fault & P_NONREGULAR)) metadata->st_mode = 0;
    if (!result && (probe_fault & P_NEG_SIZE)) metadata->st_size = -1;
    if (!result && (probe_fault & P_LARGE_SIZE)) metadata->st_size = (int64_t)INT32_MAX + 19;
    return result;
}
static FILE *probe_fdopen(int descriptor, const char *mode) {
    ++probe_stream_calls;
    return probe_fault & P_STREAM ? NULL : fdopen(descriptor, mode);
}
static int probe_close_descriptor(int descriptor) {
    ++probe_descriptor_closes;
    int result = close(descriptor);
    assert(probe_descriptors > 0);
    --probe_descriptors;
    return probe_fault & P_DESC_CLOSE ? -1 : result;
}
#define open probe_open
#define fstat probe_stat
#define fdopen probe_fdopen
#define close probe_close_descriptor
#endif
#define malloc probe_malloc
#define free probe_free
#define memchr probe_memchr
#define fread probe_read
#define fseek probe_seek
#define fgetc probe_getc
#define ferror probe_error
#define fclose probe_close_file
#define freak_llvm_word_try_adopt_sized probe_adopt
#define freak_v4_word_from_bytes probe_error_word
#include "freak_v4_system_runtime.c"
#undef malloc
#undef free
#undef memchr
#undef fread
#undef fseek
#undef fgetc
#undef ferror
#undef fclose
#undef freak_llvm_word_try_adopt_sized
#undef freak_v4_word_from_bytes
#ifdef _WIN32
#undef _wopen
#undef _fstat64
#undef _fdopen
#undef _close
#undef MultiByteToWideChar
#else
#undef open
#undef fstat
#undef fdopen
#undef close
#endif

static void (*const probe_fs_abi)(int64_t, int64_t *, int64_t *) = freak_v4_fs_read;
static void probe_check_path(void) {
    size_t length = SIZE_MAX;
    assert(probe_path && freak_llvm_word_owned_size(probe_path, &length));
    assert(length == probe_metadata_length);
    assert(!probe_storage_length || !memcmp((void *)(uintptr_t)probe_path,
                                            probe_saved_path, probe_storage_length));
}
static _Noreturn void probe_word_abort(void) {
    /* Word panic bypasses atexit. Observe the still-live borrow and rolled-back
       private storage immediately before calling the real abort; do not claim
       that process-abort runs ordinary caller cleanup. */
    assert(probe_active && probe_error_copy && probe_fatal_reset);
    probe_check_path();
    assert(probe_tag == 0 && probe_payload == 0);
    assert(freak_llvm_owned_count == 1 && freak_c_owned_word_count == 0);
    assert(probe_descriptors == 0 && probe_raw_count == 0);
    abort();
}
static void probe_drop_path(void) {
    if (!probe_path) return;
    probe_check_path();
    freak_llvm_owned_word *record = freak_llvm_owned_find((void *)(uintptr_t)probe_path, NULL);
    assert(record);
    record->length = probe_storage_length;
    freak_v4_word_drop(probe_path);
    probe_path = 0;
    free(probe_saved_path);
    probe_saved_path = NULL;
}
static void probe_cleanup(void) {
    probe_active = probe_error_copy = probe_forbid_touch = false;
    probe_fault = 0;
    if (probe_fatal_slots) assert(probe_tag == 117 && probe_payload == 118);
    if (probe_fatal_reset) assert(probe_tag == 0 && probe_payload == 0);
    probe_drop_path();
    freak_v4_process_shutdown_args();
    assert(probe_descriptors == 0 && probe_raw_count == 0);
    assert(freak_llvm_owned_count == 0 && freak_c_owned_word_count == 0);
}
static void probe_save_path(int64_t path) {
    probe_path = path;
    assert(freak_llvm_word_owned_size(path, &probe_storage_length));
    probe_metadata_length = probe_storage_length;
    probe_saved_path = malloc(probe_storage_length ? probe_storage_length : 1);
    assert(probe_saved_path);
    if (probe_storage_length) memcpy(probe_saved_path, (void *)(uintptr_t)path, probe_storage_length);
}
static int64_t probe_invoke(int64_t *tag) {
    size_t before = freak_llvm_owned_count, scans = probe_path_scans;
    assert(probe_descriptors == 0 && probe_raw_count == 0);
    probe_check_path();
    probe_allocations = probe_error_queries = probe_wide_calls = 0;
    probe_open_result = -2;
    probe_stat_nonregular = false;
    probe_stat_calls = probe_stream_calls = probe_read_calls = 0;
    probe_adopt_calls = probe_descriptor_closes = 0;
    int64_t payload = 0;
    *tag = -1;
    probe_active = true;
    probe_fs_abi(probe_path, tag, &payload);
    probe_active = false;
    assert((*tag == 0 || *tag == 1) && payload && payload != probe_path);
    assert(freak_llvm_owned_count == before + 1);
    size_t length;
    assert(freak_llvm_word_owned_size(payload, &length));
    if (!*tag) assert(length > 0);
    probe_check_path();
    assert(probe_descriptors == 0 && probe_raw_count == 0);
    if (probe_forbid_touch) assert(probe_path_scans == scans && probe_allocations == 0);
    if (probe_fault & P_LARGE_SIZE) assert(probe_last_allocation == (size_t)INT32_MAX + 20);
    if (probe_directory) {
        assert(!probe_fault && *tag == 0 && probe_open_result >= -1);
        assert(probe_stream_calls == 0 && probe_read_calls == 0 && probe_adopt_calls == 0);
        if (probe_open_result < 0) assert(probe_stat_calls == 0 && probe_descriptor_closes == 0);
        else assert(probe_stat_calls == 1 && probe_stat_nonregular && probe_descriptor_closes == 1);
#ifndef _WIN32
        assert(probe_open_result >= 0);
#endif
    }
    return payload;
}
static void probe_print_payload(int64_t tag, int64_t payload) {
    size_t length;
    assert(freak_llvm_word_owned_size(payload, &length));
    printf("fs-tag:%lld\nfs-bytes:", (long long)tag);
    const unsigned char *bytes = (const unsigned char *)(uintptr_t)payload;
    for (size_t index = 0; index < length; ++index) printf("%02x", bytes[index]);
    putchar('\n');
}
static void probe_summary(unsigned recovery) {
    assert(freak_llvm_owned_count == 0 && freak_c_owned_word_count == 0);
    assert(probe_descriptors == 0 && probe_raw_count == 0);
    printf("path:unchanged\npayloads:independent\nrecovery:%u\n"
           "owners:0\ndescriptors:0\nraw-allocations:0\n", recovery);
}
static void probe_two_results(bool path_first) {
    int64_t tag1, tag2, first = probe_invoke(&tag1);
    bool first_rejected = probe_open_result < 0;
    int64_t second = probe_invoke(&tag2);
    if (probe_directory) {
        assert(first_rejected == (probe_open_result < 0));
        printf("directory-open:%s;stat:%u;raw-close:%u;stream:0;read:0;adopt:0\n",
               first_rejected ? "rejected" : "admitted", probe_stat_calls, probe_descriptor_closes);
    }
    assert(first != second && tag1 == tag2 && freak_v4_word_equal(first, second));
    if (path_first) probe_drop_path();
    probe_print_payload(tag1, first);
    freak_v4_word_drop(first);
    assert(freak_llvm_owned_count == (path_first ? 1u : 2u));
    if (!path_first) { probe_check_path(); probe_drop_path(); }
    freak_v4_word_drop(second);
    probe_summary(0);
}
static unsigned probe_fault_named(const char *name) {
    static const struct { const char *name; unsigned value; } names[] = {
        {"path-allocation", P_PATH_ALLOC}, {"open", P_OPEN}, {"stat", P_STAT},
        {"nonregular", P_NONREGULAR}, {"stream", P_STREAM}, {"negative-size", P_NEG_SIZE},
        {"seek", P_SEEK}, {"contents-allocation", P_CONTENT_ALLOC}, {"short-read", P_SHORT},
        {"read-error", P_READ_ERROR}, {"extra-data", P_EXTRA}, {"eof-error", P_EOF_ERROR},
        {"close", P_CLOSE}, {"adopt", P_ADOPT}, {"large-allocation", P_LARGE_SIZE | P_CONTENT_ALLOC},
        {"seek-close", P_SEEK | P_CLOSE}, {"allocation-close", P_CONTENT_ALLOC | P_CLOSE},
        {"short-close", P_SHORT | P_CLOSE}, {"read-error-close", P_READ_ERROR | P_CLOSE},
        {"stat-descriptor-close", P_STAT | P_DESC_CLOSE},
        {"wide-first", P_WIDE_FIRST}, {"wide-second", P_WIDE_SECOND}
    };
    for (size_t index = 0; index < sizeof(names) / sizeof(names[0]); ++index)
        if (!strcmp(name, names[index].name)) return names[index].value;
    return 0;
}
static void probe_fault_recovery(unsigned fault) {
    probe_fault = fault;
    int64_t tag, first = probe_invoke(&tag);
    assert(tag == 0);
    probe_fault = 0;
    for (unsigned index = 0; index < 64; ++index) {
        int64_t recovered_tag, recovered = probe_invoke(&recovered_tag);
        assert(recovered_tag == 1 && recovered != first && recovered != probe_path);
        const unsigned char bytes[] = {'A', 0, 0xc3, 0xa9, 0xe4, 0xb8, 0xad, 0xf0, 0x9f, 0x98, 0x80};
        size_t length;
        assert(freak_llvm_word_owned_size(recovered, &length) && length == sizeof(bytes));
        assert(!memcmp((void *)(uintptr_t)recovered, bytes, sizeof(bytes)));
        freak_v4_word_drop(recovered);
        assert(freak_llvm_owned_count == 2);
    }
    probe_drop_path();
    probe_print_payload(tag, first);
    freak_v4_word_drop(first);
    probe_summary(64);
}
static int probe_path_case(const char *name) {
    if (!strcmp(name, "empty")) probe_save_path(freak_v4_word_from_bytes(0, 0));
    else if (!strcmp(name, "nul") || !strcmp(name, "nul-invalid")) {
        const char bytes[] = {'a', 0, 'b'};
        int64_t path = freak_v4_word_from_bytes((int64_t)(uintptr_t)bytes, sizeof(bytes));
        if (!strcmp(name, "nul-invalid")) ((unsigned char *)(uintptr_t)path)[0] = 0xff;
        probe_save_path(path);
    } else if (!strcmp(name, "invalid")) {
        int64_t path = freak_v4_word_from_bytes((int64_t)(uintptr_t)"abc", 3);
        ((unsigned char *)(uintptr_t)path)[0] = 0xff; /* malformed private storage control */
        probe_save_path(path);
    } else if (!strcmp(name, "size-max") || !strcmp(name, "windows-size")) {
        probe_save_path(freak_v4_word_from_bytes((int64_t)(uintptr_t)"p", 1));
        size_t forged = SIZE_MAX;
#ifdef _WIN32
        if (!strcmp(name, "windows-size")) forged = (size_t)INT_MAX + 1;
#else
        if (!strcmp(name, "windows-size")) return 2;
#endif
        freak_llvm_owned_word *record = freak_llvm_owned_find((void *)(uintptr_t)probe_path, NULL);
        assert(record);
        record->length = probe_metadata_length = forged;
        probe_forbid_touch = true;
    } else return 2;
    assert(atexit(probe_cleanup) == 0);
    probe_two_results(true);
    return 0;
}
static int probe_fatal(const char *name) {
    bool slot = !strcmp(name, "null-tag") || !strcmp(name, "null-payload") ||
        !strcmp(name, "null-both") || !strcmp(name, "alias");
    if (slot || !strcmp(name, "error-copy") || !strcmp(name, "error-track"))
        probe_save_path(freak_v4_process_arg(3));
    assert(atexit(probe_cleanup) == 0);
    if (slot) {
        probe_fatal_slots = true;
        if (!strcmp(name, "null-tag")) probe_fs_abi(probe_path, NULL, &probe_payload);
        else if (!strcmp(name, "null-payload")) probe_fs_abi(probe_path, &probe_tag, NULL);
        else if (!strcmp(name, "null-both")) probe_fs_abi(probe_path, NULL, NULL);
        else probe_fs_abi(probe_path, &probe_tag, &probe_tag);
    } else {
        probe_fatal_reset = true;
        if (!strcmp(name, "error-copy") || !strcmp(name, "error-track")) {
            probe_fault = P_OPEN | (!strcmp(name, "error-copy") ? P_ERROR_COPY : P_ERROR_TRACK);
            probe_active = true;
            probe_fs_abi(probe_path, &probe_tag, &probe_payload);
        } else if (!strcmp(name, "null")) probe_fs_abi(0, &probe_tag, &probe_payload);
        else if (!strcmp(name, "foreign")) probe_fs_abi((int64_t)(uintptr_t)"foreign", &probe_tag, &probe_payload);
        else if (!strcmp(name, "unknown")) probe_fs_abi(-1, &probe_tag, &probe_payload);
        else if (!strcmp(name, "stale")) {
            int64_t stale = freak_v4_word_from_bytes((int64_t)(uintptr_t)"old", 3);
            freak_v4_word_drop(stale);
            probe_fs_abi(stale, &probe_tag, &probe_payload);
        } else return 2;
    }
    return 99;
}
static int probe_capability(const char *name) {
    if (!strcmp(name, "--asan-heap")) {
        volatile char *bytes = malloc(8);
        if (!bytes) return 97;
        volatile size_t index = 8;
        bytes[index] = 'x';
        free((void *)bytes);
    } else if (!strcmp(name, "--ubsan-overflow")) {
        volatile int32_t left = INT32_MAX, right = 1, result = left + right;
        (void)result;
    } else if (!strcmp(name, "--ubsan-division")) {
        volatile int32_t left = INT32_MIN, right = -1, result = left / right;
        (void)result;
    } else if (!strcmp(name, "--llvm-owner-audit")) {
        (void)freak_v4_word_from_bytes((int64_t)(uintptr_t)"leak", 4);
        return 0;
    } else if (!strcmp(name, "--c-owner-audit")) {
        (void)freak_word_clone(freak_word_lit("leak"));
        return 0;
    } else return 2;
    return 99;
}
int main(int argc, char **argv) {
#ifdef _WIN32
    _set_abort_behavior(0, _WRITE_ABORT_MSG | _CALL_REPORTFAULT);
#endif
    if (argc < 2) return 2;
    if (argc == 2) return probe_capability(argv[1]);
    if (!strcmp(argv[1], "--path") && argc == 3) return probe_path_case(argv[2]);
    if (argc != 4) return 2;
    freak_v4_process_setup_args(argc, (int64_t)(uintptr_t)argv);
    if (!strcmp(argv[1], "--fatal")) return probe_fatal(argv[2]);
    if (!strcmp(argv[1], "--read")) {
        if (strcmp(argv[3], "path-first") && strcmp(argv[3], "payload-first") && strcmp(argv[3], "directory-boundary")) return 2;
        probe_directory = !strcmp(argv[3], "directory-boundary");
        probe_save_path(freak_v4_process_arg(2));
        assert(atexit(probe_cleanup) == 0);
        probe_two_results(!strcmp(argv[3], "path-first"));
        return 0;
    }
    if (!strcmp(argv[1], "--fault")) {
        unsigned fault = probe_fault_named(argv[2]);
        if (!fault) return 2;
        probe_save_path(freak_v4_process_arg(3));
        assert(atexit(probe_cleanup) == 0);
        probe_fault_recovery(fault);
        return 0;
    }
    return 2;
}
