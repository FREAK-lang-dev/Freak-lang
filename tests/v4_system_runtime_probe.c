/* The real core registry is included unchanged so the probe can assert exact
   live-owner counts. Only the new adapter's OS/allocator calls are intercepted;
   its production source is included byte-for-byte below. */
#include "freak_runtime.c"
#include "freak_v4_word_runtime.h"
#include "freak_v4_system_runtime.h"
#include <assert.h>

static int probe_fault = 0;
static int probe_allocations = 0;
static size_t probe_last_allocation = 0;
static int probe_descriptors = 0;
static void *probe_raw[8192];
static size_t probe_raw_count = 0;

static void probe_untrack(void *pointer) {
    if (!pointer) return;
    size_t index = 0;
    while (index < probe_raw_count && probe_raw[index] != pointer) ++index;
    assert(index < probe_raw_count);
    probe_raw[index] = probe_raw[--probe_raw_count];
}
static void *probe_malloc(size_t size) {
    ++probe_allocations;
    probe_last_allocation = size;
    if ((probe_fault == 1 && probe_allocations == 1) ||
            (probe_fault == 2 && probe_allocations == 2) ||
            (probe_fault == 12 && probe_allocations == 2)) return NULL;
    void *pointer = malloc(size);
    if (pointer) {
        assert(probe_raw_count < sizeof(probe_raw) / sizeof(probe_raw[0]));
        probe_raw[probe_raw_count++] = pointer;
    }
    return pointer;
}
static void probe_free(void *pointer) {
    probe_untrack(pointer);
    free(pointer);
}
static int64_t probe_adopt(int64_t pointer, size_t length) {
    if (probe_fault == 3) return 0;
    int64_t result = freak_llvm_word_try_adopt_sized(pointer, length);
    if (result) probe_untrack((void *)(uintptr_t)pointer);
    return result;
}
static int probe_seek(FILE *file, long offset, int whence) {
    if (probe_fault == 7) return -1;
    return fseek(file, offset, whence);
}
static size_t probe_read(void *data, size_t size, size_t count, FILE *file) {
    if (probe_fault == 8) return count ? fread(data, size, count - 1, file) : 0;
    return fread(data, size, count, file);
}
static int probe_getc(FILE *file) {
    if (probe_fault == 9) return 'x';
    return fgetc(file);
}
static int probe_error(FILE *file) {
    if (probe_fault == 13) return 1;
    return ferror(file);
}
static int probe_close_file(FILE *file) {
    int result = fclose(file);
    --probe_descriptors;
    assert(probe_descriptors >= 0);
    return probe_fault == 10 ? EOF : result;
}
#ifdef _WIN32
static int probe_open(const wchar_t *name, int flags, ...) {
    if (probe_fault == 4) return -1;
    int descriptor = _wopen(name, flags);
    if (descriptor >= 0) ++probe_descriptors;
    return descriptor;
}
static int probe_stat(int descriptor, struct _stat64 *metadata) {
    if (probe_fault == 5) return -1;
    int result = _fstat64(descriptor, metadata);
    if (!result && probe_fault == 11) metadata->st_size = -1;
    if (!result && probe_fault == 12) metadata->st_size = (int64_t)INT32_MAX + 19;
    return result;
}
static FILE *probe_fdopen(int descriptor, const char *mode) {
    return probe_fault == 6 ? NULL : _fdopen(descriptor, mode);
}
static int probe_close_descriptor(int descriptor) {
    int result = _close(descriptor);
    --probe_descriptors;
    assert(probe_descriptors >= 0);
    return result;
}
#define _wopen probe_open
#define _fstat64 probe_stat
#define _fdopen probe_fdopen
#define _close probe_close_descriptor
#else
static int probe_open(const char *name, int flags, ...) {
    if (probe_fault == 4) return -1;
    int descriptor = open(name, flags);
    if (descriptor >= 0) ++probe_descriptors;
    return descriptor;
}
static int probe_stat(int descriptor, struct stat *metadata) {
    if (probe_fault == 5) return -1;
    int result = fstat(descriptor, metadata);
    if (!result && probe_fault == 11) metadata->st_size = -1;
    if (!result && probe_fault == 12) metadata->st_size = (int64_t)INT32_MAX + 19;
    return result;
}
static FILE *probe_fdopen(int descriptor, const char *mode) {
    return probe_fault == 6 ? NULL : fdopen(descriptor, mode);
}
static int probe_close_descriptor(int descriptor) {
    int result = close(descriptor);
    --probe_descriptors;
    assert(probe_descriptors >= 0);
    return result;
}
#define open probe_open
#define fstat probe_stat
#define fdopen probe_fdopen
#define close probe_close_descriptor
#endif
#define malloc probe_malloc
#define free probe_free
#define fread probe_read
#define fseek probe_seek
#define fgetc probe_getc
#define ferror probe_error
#define fclose probe_close_file
#define freak_llvm_word_try_adopt_sized probe_adopt
#include "freak_v4_system_runtime.c"
#undef malloc
#undef free
#undef fread
#undef fseek
#undef fgetc
#undef ferror
#undef fclose
#undef freak_llvm_word_try_adopt_sized
#ifdef _WIN32
#undef _wopen
#undef _fstat64
#undef _fdopen
#undef _close
#else
#undef open
#undef fstat
#undef fdopen
#undef close
#endif

static void probe_exit_clean(void) {
    assert(probe_descriptors == 0);
    assert(probe_raw_count == 0);
    assert(freak_llvm_owned_count == 0);
    assert(freak_c_owned_word_count == 0);
}
static int64_t probe_word(const void *bytes, size_t length) {
    size_t before = freak_llvm_owned_count;
    int64_t word = freak_v4_word_from_bytes((int64_t)(uintptr_t)bytes, (int64_t)length);
    size_t actual = SIZE_MAX;
    assert(word);
    assert(freak_llvm_word_owned_size(word, &actual) && actual == length);
    assert(freak_llvm_owned_count == before + 1);
    return word;
}
static void probe_bytes(int64_t word, const void *bytes, size_t length) {
    size_t actual = SIZE_MAX;
    assert(freak_llvm_word_owned_size(word, &actual) && actual == length);
    assert(!length || !memcmp((void *)(uintptr_t)word, bytes, length));
}
static void probe_result(int64_t path, int64_t expected_tag,
                         const void *expected_bytes, size_t expected_length) {
    size_t before = freak_llvm_owned_count, path_length = SIZE_MAX;
    assert(freak_llvm_word_owned_size(path, &path_length));
    int64_t tag = -1, payload = 0;
    freak_v4_fs_read(path, &tag, &payload);
    assert(tag == expected_tag && payload && payload != path);
    assert(freak_llvm_owned_count == before + 1);
    size_t still_length = SIZE_MAX;
    assert(freak_llvm_word_owned_size(path, &still_length) && still_length == path_length);
    if (tag) probe_bytes(payload, expected_bytes, expected_length);
    else assert(freak_v4_word_bytes(payload) > 0);
    freak_v4_word_drop(payload);
    assert(freak_llvm_owned_count == before && probe_descriptors == 0);
}
static void probe_arguments(int argc, char **argv, bool print) {
    freak_v4_process_setup_args(argc, (int64_t)(uintptr_t)argv);
    assert(freak_v4_process_args_count() == argc);
    for (int64_t index = 0; index < argc; ++index) {
        size_t before = freak_llvm_owned_count;
        int64_t first = freak_v4_process_arg(index), second = freak_v4_process_arg(index);
        assert(first && second && first != second && freak_v4_word_equal(first, second));
        assert(freak_llvm_owned_count == before + 2);
        if (print) {
            printf("arg:%lld:", (long long)index);
            size_t length = freak_llvm_word_size(first);
            const unsigned char *data = (const unsigned char *)(uintptr_t)first;
            for (size_t offset = 0; offset < length; ++offset) printf("%02x", data[offset]);
            putchar('\n');
        }
        freak_v4_word_drop(first);
        /* A returned copy survives replacing the entire private argument table. */
        freak_v4_process_setup_args(argc, (int64_t)(uintptr_t)argv);
        assert(freak_v4_word_bytes(second) >= 0);
        freak_v4_word_drop(second);
        assert(freak_llvm_owned_count == before);
    }
    int64_t low = freak_v4_process_arg(-1), end = freak_v4_process_arg(argc);
    int64_t huge = freak_v4_process_arg(INT64_MAX);
    assert(low != end && low != huge && end != huge);
    probe_bytes(low, "", 0); probe_bytes(end, "", 0); probe_bytes(huge, "", 0);
    freak_v4_word_drop(low); freak_v4_word_drop(end); freak_v4_word_drop(huge);
#ifndef _WIN32
    char program[] = "program", text[] = "A\xc3\xa9";
    char *injected[] = {program, text, ""};
    freak_v4_process_setup_args(3, (int64_t)(uintptr_t)injected);
    memset(text, 'x', sizeof(text) - 1);
    int64_t copy = freak_v4_process_arg(1);
    probe_bytes(copy, "A\xc3\xa9", 3);
    freak_v4_process_shutdown_args();
    probe_bytes(copy, "A\xc3\xa9", 3);
    freak_v4_word_drop(copy);
    freak_v4_process_setup_args(0, 0);
    assert(freak_v4_process_args_count() == 0);
#endif
    freak_v4_process_shutdown_args();
    assert(freak_v4_process_args_count() == 0 && probe_raw_count == 0);
    int64_t empty = freak_v4_process_arg(0);
    probe_bytes(empty, "", 0);
    freak_v4_word_drop(empty);
}
static int probe_failure(const char *mode, int argc, char **argv) {
    if (!strcmp(mode, "--negative-argc")) freak_v4_process_setup_args(-1, 0);
    else if (!strcmp(mode, "--huge-argc")) freak_v4_process_setup_args(INT64_MAX, 0);
    else if (!strcmp(mode, "--null-argv")) freak_v4_process_setup_args(1, 0);
    else if (!strcmp(mode, "--snapshot-allocation")) {
        probe_fault = 1; probe_allocations = 0;
        freak_v4_process_setup_args(argc, (int64_t)(uintptr_t)argv);
    } else if (!strcmp(mode, "--argument-allocation")) {
        probe_fault = 2; probe_allocations = 0;
        freak_v4_process_setup_args(argc, (int64_t)(uintptr_t)argv);
    } else if (!strcmp(mode, "--invalid-wide-argument")) {
        freak_v4_process_setup_args(argc, (int64_t)(uintptr_t)argv);
    } else if (!strcmp(mode, "--invalid-result-slots")) {
        freak_v4_fs_read(0, NULL, NULL);
    } else if (!strcmp(mode, "--aliased-result-slots")) {
        int64_t slot;
        freak_v4_fs_read(0, &slot, &slot);
    } else if (!strcmp(mode, "--foreign-path")) {
        int64_t tag, payload;
        freak_v4_fs_read((int64_t)(uintptr_t)"foreign", &tag, &payload);
    } else if (!strcmp(mode, "--unknown-path")) {
        int64_t tag, payload;
        freak_v4_fs_read(-1, &tag, &payload);
    } else if (!strcmp(mode, "--stale-path")) {
        int64_t stale = probe_word("old", 3), tag, payload;
        freak_v4_word_drop(stale);
        freak_v4_fs_read(stale, &tag, &payload);
    }
#ifndef _WIN32
    else if (!strcmp(mode, "--null-argument")) {
        char *injected[] = {NULL};
        freak_v4_process_setup_args(1, (int64_t)(uintptr_t)injected);
    } else if (!strcmp(mode, "--invalid-argument")) {
        char invalid[] = {(char)0xff, 0};
        char *injected[] = {"program", invalid};
        freak_v4_process_setup_args(2, (int64_t)(uintptr_t)injected);
    }
#endif
    else return 98;
    return 99;
}
int main(int argc, char **argv) {
    assert(atexit(probe_exit_clean) == 0);
    if (argc < 2 || strcmp(argv[1], "--accepted") != 0)
        return argc < 2 ? 2 : probe_failure(argv[1], argc, argv);
    assert(argc >= 7);
    /* Use returned V4 arguments for every path: Windows CRT narrow argv may
       lose the Unicode filename even while the real wide command line is exact. */
    freak_v4_process_setup_args(argc, (int64_t)(uintptr_t)argv);
    int64_t paths[5];
    for (int index = 0; index < 5; ++index) paths[index] = freak_v4_process_arg(index + 2);
    const unsigned char content[] = {'A', 0, 0xc3, 0xa9, 0xe4, 0xb8, 0xad, 0xf0, 0x9f, 0x98, 0x80};
    probe_result(paths[0], 1, "", 0);
    probe_result(paths[1], 1, content, sizeof(content));
    probe_result(paths[2], 0, NULL, 0);
    probe_result(paths[3], 0, NULL, 0);
    probe_result(paths[4], 0, NULL, 0);
    int64_t empty_path = probe_word("", 0);
    const char nul_bytes[] = {'a', 0, 'b'};
    int64_t nul_path = probe_word(nul_bytes, sizeof(nul_bytes));
    probe_result(empty_path, 0, NULL, 0);
    probe_result(nul_path, 0, NULL, 0);
    freak_v4_word_drop(empty_path); freak_v4_word_drop(nul_path);
    int64_t invalid_path = argc > 7 ? freak_v4_process_arg(7) : 0;
    assert(invalid_path);
    probe_result(invalid_path, 0, NULL, 0);
    freak_v4_word_drop(invalid_path);
    size_t baseline_raw = probe_raw_count;
    for (int fault = 1; fault <= 13; ++fault) {
        probe_fault = fault; probe_allocations = 0;
        probe_result(paths[1], 0, NULL, 0);
        if (fault == 12) assert(probe_last_allocation == (size_t)INT32_MAX + 20);
        assert(probe_raw_count == baseline_raw);
    }
    probe_fault = 0;
    for (int iteration = 0; iteration < 64; ++iteration) {
        probe_result(paths[1], 1, content, sizeof(content));
        probe_result(paths[0], 1, "", 0);
        probe_result(paths[2], 0, NULL, 0);
    }
    for (int index = 0; index < 5; ++index) freak_v4_word_drop(paths[index]);
    assert(freak_llvm_owned_count == 0);
    probe_arguments(argc, argv, true);
    /* Leave a private snapshot alive to prove process-lifetime cleanup too. */
    freak_v4_process_setup_args(argc, (int64_t)(uintptr_t)argv);
    assert(freak_llvm_owned_count == 0 && probe_descriptors == 0);
    puts("v4-system-runtime=ok");
    return 0;
}
