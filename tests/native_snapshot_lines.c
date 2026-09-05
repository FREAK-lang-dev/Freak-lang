/* Focused C and LLVM bridge test; no compiler rebuild required.
   clang -O1 tests/native_snapshot_lines.c -o native_snapshot_lines -lm
   Windows: replace -lm with -lws2_32. Includes runtime sources deliberately
   so allocation faults, scan calls and private handle state are observable. */
#ifndef _WIN32
#define _POSIX_C_SOURCE 200809L
#endif
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <io.h>
#include <direct.h>
#endif

static long fail_after = -1;
static size_t live_allocations, allocation_calls, strlen_calls, strlen_bytes, copied_bytes;
static int fail_allocation(void) {
    ++allocation_calls;
    if (fail_after < 0) return 0;
    if (fail_after == 0) return 1;
    --fail_after;
    return 0;
}
static void* probe_malloc(size_t size) {
    if (fail_allocation()) return NULL;
    void* p = malloc(size);
    if (p) ++live_allocations;
    return p;
}
static void* probe_calloc(size_t count, size_t size) {
    if (fail_allocation()) return NULL;
    void* p = calloc(count, size);
    if (p) ++live_allocations;
    return p;
}
static void* probe_realloc(void* previous, size_t size) {
    if (fail_allocation()) return NULL;
    int was_null = previous == NULL;
    void* p = realloc(previous, size);
    if (p && was_null) ++live_allocations;
    return p;
}
static void probe_free(void* p) {
    if (p) { assert(live_allocations); --live_allocations; }
    free(p);
}
static size_t probe_strlen(const char* p) {
    size_t length = strlen(p);
    ++strlen_calls;
    strlen_bytes += length;
    return length;
}
static void* probe_memcpy(void* dst, const void* src, size_t length) {
    copied_bytes += length;
    return memcpy(dst, src, length);
}
#define malloc probe_malloc
#define calloc probe_calloc
#define realloc probe_realloc
#define free probe_free
#define strlen probe_strlen
#define memcpy probe_memcpy
#define FREAK_ARRAY_LIVE_LIMIT 16
#define FREAK_C_RUNTIME_OWNERSHIP_AUDIT 1
#define FREAK_RUNTIME_OWNERSHIP_AUDIT 1
#include "../freakc/runtime/freak_runtime.c"
#define freak_wsa_inited probe_llvm_wsa_inited
#define freak_wsa_init probe_llvm_wsa_init
#include "../freakc/runtime/freak_llvm_runtime.c"
#undef freak_wsa_inited
#undef freak_wsa_init
#undef malloc
#undef calloc
#undef realloc
#undef free
#undef strlen
#undef memcpy

static int64_t split(const char* source, int llvm) {
    freak_word w = {source, strlen(source), strlen(source), false};
    strlen_calls = strlen_bytes = copied_bytes = allocation_calls = 0;
    int64_t handle = llvm ? freak_llvm_word_snapshot_lines((int64_t)source)
                          : freak_word_snapshot_lines(w);
    assert(strlen_calls == (size_t)llvm);
    assert(strlen_bytes == (llvm ? w.length : 0));
    assert(copied_bytes <= w.length);
    return handle;
}
static int64_t line_count(int64_t handle, int llvm) {
    return llvm ? freak_llvm_array_len(handle) : freak_array_len(handle);
}
static const char* line(int64_t handle, int64_t index, int llvm) {
    return llvm ? (const char*)freak_llvm_array_get(handle, index)
                : freak_array_get(handle, index).data;
}
static void release(int64_t handle, int llvm) {
    if (llvm) freak_llvm_array_release_owned(handle);
    else freak_array_release(handle); /* Actual Python bootstrap lowering. */
}
static void check_case(const char* source, const char** expected, size_t count, int llvm) {
    char* owned_source = malloc(strlen(source) + 1);
    assert(owned_source);
    strcpy(owned_source, source);
    int64_t handle = split(owned_source, llvm);
    free(owned_source); /* Every returned record must own an independent copy. */
    assert(handle >= 0 && line_count(handle, llvm) == (int64_t)count);
    for (size_t i = 0; i < count; ++i) assert(strcmp(line(handle, (int64_t)i, llvm), expected[i]) == 0);
    release(handle, llvm);
    assert(line_count(handle, llvm) == 0);
    const char* stale = line(handle, 0, llvm);
    assert(llvm ? stale == NULL : stale && stale[0] == 0);
    int64_t replacement = split("alive", llvm);
    assert(replacement >= 0 && replacement != handle);
    release(handle, llvm);
    assert(line_count(replacement, llvm) == 1 && strcmp(line(replacement, 0, llvm), "alive") == 0);
    release(replacement, llvm);
}

static void check_c_snapshot_array_ownership(void) {
    size_t baseline = live_allocations;
    for (int owned_release = 0; owned_release <= 1; ++owned_release) {
        int64_t h = split("a\nb", 0);
        assert(h >= 0 && freak_arrays[freak_array_slot_for_handle(h)].owns_elements);
        freak_array_set(h, 0, freak_array_get(h, 0)); /* self alias */
        freak_array_set(h, 1, freak_array_get(h, 0)); /* sibling alias */
        freak_array_push(h, freak_array_get(h, 0)); /* alias across capacity growth */
        assert(freak_array_len(h) == 3);
        for (int64_t i = 0; i < 3; ++i) {
            assert(strcmp(freak_array_get(h, i).data, "a") == 0);
            for (int64_t j = 0; j < i; ++j) {
                assert(freak_array_get(h, i).data != freak_array_get(h, j).data);
            }
        }
        freak_word external = freak_word_from_int(123);
        freak_array_push(h, external);
        freak_array_set(h, 0, external);
        freak_word_release_owned(&external);
        assert(strcmp(freak_array_get(h, 0).data, "123") == 0);
        assert(strcmp(freak_array_get(h, 3).data, "123") == 0);
        freak_array_push_owned(h, freak_word_from_int(7));
        freak_array_set_owned(h, 0, freak_word_from_int(8));
        assert(strcmp(freak_array_get(h, 0).data, "8") == 0);
        assert(strcmp(freak_array_get(h, 4).data, "7") == 0);
        if (owned_release) freak_array_release_owned(h);
        else freak_array_release(h);
        freak_array_release(h);
        freak_array_release_owned(h);
        assert(live_allocations == baseline);
    }
    for (int owned_join = 0; owned_join <= 1; ++owned_join) {
        int64_t h = split("a\n\nb\r\n", 0);
        freak_word joined = owned_join ? freak_word_join_owned(h) : freak_word_join(h);
        assert(strcmp(joined.data, "ab\r") == 0 && freak_array_len(h) == 0);
        freak_word_release_owned(&joined);
        assert(live_allocations == baseline);
    }
    int64_t empty = split("", 0);
    freak_array_push(empty, freak_word_lit("literal"));
    assert(strcmp(freak_array_get(empty, 0).data, "literal") == 0);
    int64_t old_slot = freak_array_slot_for_handle(empty);
    freak_array_release(empty);
    int64_t borrowed = freak_array_new();
    assert(freak_array_slot_for_handle(borrowed) == old_slot && borrowed != empty);
    assert(!freak_arrays[old_slot].owns_elements);
    freak_word external = freak_word_from_int(42);
    freak_array_push(borrowed, external);
    freak_array_set(borrowed, 0, external);
    assert(freak_array_get(borrowed, 0).data == external.data);
    freak_array_release(borrowed); /* Legacy borrowed words must remain alive. */
    assert(strcmp(external.data, "42") == 0);
    freak_word_release_owned(&external);
    int64_t transferred = freak_array_new();
    freak_array_push_owned(transferred, freak_word_from_int(99));
    freak_array_release_owned(transferred);
    assert(live_allocations == baseline);
    puts("snapshot_lines C ordinary/owned release, mutation, join and reuse PASS");
}

static void check_registered_binary_lines(void) {
    const char bytes[] = {'a', 0, 'b', '\n', 'c', '\n', 0};
    char* data = probe_malloc(sizeof(bytes));
    assert(data);
    memcpy(data, bytes, sizeof(bytes));
    int64_t source = freak_llvm_word_adopt_sized((int64_t)data, 6);
    size_t owned = freak_llvm_owned_count;
    size_t baseline = live_allocations;
    fail_after = 0;
    assert(freak_llvm_word_try_adopt_sized(source, 6) == source);
    assert(freak_llvm_word_try_adopt_sized(source, 1) == 0);
    fail_after = -1;
    assert(freak_llvm_owned_count == owned && freak_llvm_word_size(source) == 6);
    assert(freak_llvm_word_try_adopt_sized(0, 1) == 0);
    int64_t zero = freak_llvm_word_char_at(source, 1);
    strlen_calls = 0;
    int64_t lines = freak_llvm_word_snapshot_lines(source);
    assert(lines >= 0 && freak_llvm_array_len(lines) == 3);
    assert(strlen_calls == 0);
    freak_llvm_word_release_replaced(source, 0);
    int64_t first = freak_llvm_array_get(lines, 0);
    assert(freak_llvm_word_size(first) == 3 && memcmp((void*)first, bytes, 3) == 0);
    assert(freak_llvm_word_size(freak_llvm_array_get(lines, 1)) == 1);
    assert(freak_llvm_word_size(freak_llvm_array_get(lines, 2)) == 0);
    int64_t joined = freak_llvm_word_join_owned(lines);
    const char expected[] = {'a', 0, 'b', 'c'};
    assert(freak_llvm_word_size(joined) == sizeof(expected));
    assert(memcmp((void*)joined, expected, sizeof(expected)) == 0);
    freak_llvm_word_release_replaced(joined, 0);
    strlen_calls = 0;
    lines = freak_llvm_word_snapshot_lines(zero);
    assert(lines >= 0 && freak_llvm_array_len(lines) == 1 && strlen_calls == 0);
    first = freak_llvm_array_get(lines, 0);
    assert(freak_llvm_word_size(first) == 1 && *(char*)first == 0);
    freak_llvm_array_release_owned(lines);
    assert(freak_llvm_word_size(zero) == 1);
    assert(freak_llvm_owned_count == owned - 1 && live_allocations == baseline - 2);
    puts("snapshot_lines registered binary lengths and static NUL PASS");
}

int main(void) {
    /* The first C table allocation must fail without publishing a handle. */
    fail_after = 0;
    assert(split("x", 0) == -1 && freak_array_count == 0);
    assert(split("x", 1) == -1 && freak_llvm_array_count == 0);
    /* Fresh LLVM ownership-registry allocation failure releases both buffers. */
    fail_after = 2;
    assert(split("x", 1) == -1 && freak_llvm_owned_bucket_count == 0);
    assert(live_allocations == 0);
    fail_after = -1;
    const char* singleton[] = {"x"};
    const char* blanks[] = {"", ""};
    const char* mixed[] = {"first\r", "", "third\r", ""};
    /* C words retain their explicit byte-length contract, including NUL bytes. */
    const char binary_source[] = {'a', 0, 'b', '\n', 'c'};
    freak_word binary_word = {binary_source, sizeof(binary_source), sizeof(binary_source), false};
    int64_t binary_handle = freak_word_snapshot_lines(binary_word);
    assert(binary_handle >= 0 && freak_array_len(binary_handle) == 2);
    freak_word binary_line = freak_array_get(binary_handle, 0);
    assert(binary_line.length == 3 && memcmp(binary_line.data, binary_source, 3) == 0);
    freak_array_release_owned(binary_handle);
    int64_t null_c = freak_word_snapshot_lines((freak_word)FREAK_WORD_EMPTY);
    int64_t null_llvm = freak_llvm_word_snapshot_lines(0);
    assert(null_c >= 0 && freak_array_len(null_c) == 0);
    assert(null_llvm >= 0 && freak_llvm_array_len(null_llvm) == 0);
    freak_array_release_owned(null_c);
    freak_llvm_array_release_owned(null_llvm);
    check_c_snapshot_array_ownership();
    check_registered_binary_lines();
    for (int llvm = 0; llvm <= 1; ++llvm) {
        check_case("", NULL, 0, llvm);
        check_case("x", singleton, 1, llvm);
        check_case("\n", blanks, 2, llvm);
        check_case("first\r\n\nthird\r\n", mixed, 4, llvm);
        size_t baseline = live_allocations;
        for (int repeat = 0; repeat < 2000; ++repeat) {
            int64_t h = split("a\n\nb\r\n", llvm);
            assert(h >= 0 && line_count(h, llvm) == 4);
            release(h, llvm);
        }
        assert(live_allocations == baseline);
        /* Fault every allocation position, including after partial adoption. */
        char fault_input[257];
        memset(fault_input, '\n', sizeof(fault_input) - 1);
        fault_input[sizeof(fault_input) - 1] = 0;
        int completed = 0;
        for (long fault = 0; fault < 600; ++fault) {
            fail_after = fault;
            int64_t h = split(fault_input, llvm);
            fail_after = -1;
            if (h >= 0) { assert(line_count(h, llvm) == 257); release(h, llvm); completed = 1; }
            assert(live_allocations == baseline);
            assert(freak_llvm_owned_count == 0 && freak_array_live_count == 0);
            if (completed) break;
        }
        assert(completed);
        size_t records = 32768, width = 64, length = records * width;
        char* large = malloc(length + 1);
        assert(large);
        memset(large, 'x', length);
        for (size_t i = width - 1; i < length; i += width) large[i] = '\n';
        large[length] = 0;
        int64_t h = split(large, llvm);
        assert(h >= 0 && line_count(h, llvm) == (int64_t)records + 1);
        assert(allocation_calls <= records * 2 + 32);
        assert(copied_bytes == length - records);
        assert(strcmp(line(h, (int64_t)records, llvm), "") == 0);
        release(h, llvm);
        free(large);
        assert(live_allocations == baseline);
        printf("snapshot_lines %s: bytes=%zu records=%zu strlen_calls=%zu copied_bytes=%zu\n",
               llvm ? "LLVM" : "C", length, records + 1, strlen_calls, copied_bytes);
        int64_t handles[FREAK_LLVM_MAX_ARRAYS];
        size_t limit = llvm ? FREAK_LLVM_MAX_ARRAYS : FREAK_ARRAY_LIVE_LIMIT;
        for (size_t i = 0; i < limit; ++i) {
            handles[i] = split("", llvm);
            assert(handles[i] >= 0);
        }
        /* Exhaustion is checked before source scanning. */
        assert((llvm ? freak_llvm_word_snapshot_lines((int64_t)"x")
                     : freak_word_snapshot_lines(freak_word_lit("x"))) == -1);
        for (size_t i = 0; i < limit; ++i) release(handles[i], llvm);
        assert(live_allocations == baseline);
    }
    assert(freak_llvm_owned_count == 0 && freak_array_live_count == 0);
    puts("native_snapshot_lines PASS");
    return 0;
}
