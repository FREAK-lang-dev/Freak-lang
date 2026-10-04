/* Use the real registry unchanged to verify that panic keeps its borrowed
   message alive until the actual abort, without relying on RSS estimates. */
#include "freak_runtime.c"
#include "freak_v4_word_runtime.h"
#include "freak_v4_panic_runtime.h"

#include <assert.h>

static int64_t probe_message = 0;
static size_t probe_message_length = 0;
static size_t probe_owner_count = 0;

#ifndef FREAK_V4_PANIC_DIRECT_LINK
static void probe_borrow_is_live(void) {
    if (!probe_message) return;
    size_t length = SIZE_MAX;
    assert(freak_llvm_word_owned_size(probe_message, &length));
    assert(length == probe_message_length);
    assert(freak_llvm_owned_count == probe_owner_count);
}
static size_t probe_fwrite(const void *bytes, size_t size, size_t count, FILE *stream) {
    probe_borrow_is_live();
    return fwrite(bytes, size, count, stream);
}
static int probe_fflush(FILE *stream) {
    probe_borrow_is_live();
    return fflush(stream);
}
static _Noreturn void probe_abort(void) {
    probe_borrow_is_live();
    abort();
}
#define fwrite probe_fwrite
#define fflush probe_fflush
#define abort probe_abort
/* The production helper is included unchanged; the wrappers only assert the
   loan contract and ultimately perform the real libc writes/flush/abort. */
#include "freak_v4_panic_runtime.c"
#undef fwrite
#undef fflush
#undef abort
#endif

static int64_t probe_owner(const void *bytes, size_t length) {
    size_t before = freak_llvm_owned_count;
    int64_t word = freak_v4_word_from_bytes((int64_t)(uintptr_t)bytes, (int64_t)length);
    size_t actual = SIZE_MAX;
    assert(word && freak_llvm_word_owned_size(word, &actual) && actual == length);
    assert(freak_llvm_owned_count == before + 1);
    return word;
}
static void probe_deferred_marker(void) {
    fputs("panic-atexit-ran\n", stderr);
}
static void probe_success_cleanup(void) {
    assert(freak_llvm_owned_count == 0);
    assert(freak_c_owned_word_count == 0);
}
static _Noreturn void probe_panic_message(const void *bytes, size_t length) {
    probe_message = probe_owner(bytes, length);
    probe_message_length = length;
    probe_owner_count = freak_llvm_owned_count;
    freak_v4_panic_abort(probe_message);
}

int main(int argc, char **argv) {
    if (argc == 1) {
        assert(atexit(probe_success_cleanup) == 0);
        const unsigned char data[] = {'A', 0, 0xc3, 0xa9, 0xe4, 0xb8, 0xad, 0xf0, 0x9f, 0x98, 0x80};
        /* This models a successful assertion: no panic, normal owner cleanup. */
        for (int iteration = 0; iteration < 64; ++iteration) {
            int64_t word = probe_owner(data, sizeof(data));
            assert(freak_v4_word_length(word) == 5);
            freak_v4_word_drop(word);
            assert(freak_llvm_owned_count == 0);
        }
        int64_t empty = probe_owner(NULL, 0);
        freak_v4_word_drop(empty);
        puts("v4-panic-runtime-success=ok");
        return 0;
    }
    assert(argc == 2);
    assert(atexit(probe_deferred_marker) == 0);
    const char *mode = argv[1];
    if (!strcmp(mode, "empty")) probe_panic_message(NULL, 0);
    if (!strcmp(mode, "ascii")) probe_panic_message("invariant failed", 16);
    if (!strcmp(mode, "unicode")) {
        const unsigned char text[] = {0x63, 0x61, 0x66, 0xc3, 0xa9, 0x20, 0xe4, 0xb8, 0xad, 0x20, 0xf0, 0x9f, 0x98, 0x80};
        probe_panic_message(text, sizeof(text));
    }
    if (!strcmp(mode, "nul")) {
        const unsigned char text[] = {'A', 0, 'B'};
        probe_panic_message(text, sizeof(text));
    }
    if (!strcmp(mode, "multiline")) probe_panic_message("first\nsecond\n", 13);
    if (!strcmp(mode, "crlf")) probe_panic_message("first\r\nsecond", 13);
    if (!strcmp(mode, "large")) {
        const size_t count = 262144;
        unsigned char *text = (unsigned char *)malloc(count);
        assert(text);
        memset(text, 'x', count);
        text[0] = 'A'; text[1] = 0; text[count - 1] = 'Z';
        probe_message = probe_owner(text, count);
        free(text);
        probe_message_length = count;
        probe_owner_count = freak_llvm_owned_count;
        freak_v4_panic_abort(probe_message);
    }
    if (!strcmp(mode, "null")) freak_v4_panic_abort(0);
    if (!strcmp(mode, "unknown")) freak_v4_panic_abort(1);
    if (!strcmp(mode, "negative")) freak_v4_panic_abort(-1);
    if (!strcmp(mode, "foreign")) freak_v4_panic_abort((int64_t)(uintptr_t)"foreign");
    if (!strcmp(mode, "stale")) {
        int64_t stale = probe_owner("old", 3);
        freak_v4_word_drop(stale);
        freak_v4_panic_abort(stale);
    }
    if (!strcmp(mode, "size-max") || !strcmp(mode, "signed-overflow")) {
        int64_t word = probe_owner("p", 1);
        freak_llvm_owned_word *owned = freak_llvm_owned_find((void *)(uintptr_t)word, NULL);
        assert(owned);
        if (!strcmp(mode, "size-max")) owned->length = SIZE_MAX;
        else {
#if SIZE_MAX > INT64_MAX
            owned->length = (size_t)INT64_MAX + 1;
#else
            return 98;
#endif
        }
        freak_v4_panic_abort(word);
    }
    if (!strcmp(mode, "invalid-utf8")) {
        int64_t word = probe_owner("x", 1);
        *(unsigned char *)(uintptr_t)word = 0xff;
        freak_v4_panic_abort(word);
    }
    fputs("panic-returned-or-case-unknown\n", stdout);
    return 99;
}
