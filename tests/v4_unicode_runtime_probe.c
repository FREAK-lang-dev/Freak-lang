/* Observe real owner counts and exercise production Unicode code, including
 * its checked size/allocation paths, without altering production C sources. */
#include "freak_runtime.c"
#include "freak_v4_word_runtime.h"

#include <assert.h>
#include <inttypes.h>

static int v4_unicode_allocation_failure = 0;
static void *v4_unicode_probe_malloc(size_t size) {
    if (v4_unicode_allocation_failure) return NULL;
    return malloc(size);
}
#define malloc v4_unicode_probe_malloc
#include "freak_v4_unicode_runtime.c"
#undef malloc

static int64_t v4_unicode_owner(const void *data, size_t length) {
    size_t before = freak_llvm_owned_count;
    int64_t value = freak_v4_word_from_bytes((int64_t)(uintptr_t)data, (int64_t)length);
    assert(value && freak_llvm_owned_count == before + 1);
    return value;
}

static void v4_unicode_owner_bytes(int64_t value, const void *expected, size_t length) {
    size_t stored = SIZE_MAX;
    assert(freak_llvm_word_owned_size(value, &stored) && stored == length);
    assert(freak_v4_word_bytes(value) == (int64_t)length);
    assert(!length || !memcmp((const void *)(uintptr_t)value, expected, length));
    assert(((const unsigned char *)(uintptr_t)value)[length] == 0);
}

static int v4_unicode_failure(const char *mode) {
    if (!strcmp(mode, "consumed")) (void)freak_v4_word_to_lower(0);
    else if (!strcmp(mode, "foreign")) (void)freak_v4_word_to_lower((int64_t)(uintptr_t)"ASCII");
    else if (!strcmp(mode, "foreign-invalid-pointer")) (void)freak_v4_word_to_lower(1);
    else if (!strcmp(mode, "size-overflow")) (void)freak_v4_unicode_append_size((size_t)INT64_MAX, 1);
    else if (!strcmp(mode, "size-max")) (void)freak_v4_unicode_append_size(SIZE_MAX, 1);
    else {
        int64_t value = v4_unicode_owner("AB", 2);
        if (!strcmp(mode, "stale")) {
            freak_v4_word_drop(value);
            (void)freak_v4_word_to_lower(value);
        } else if (!strcmp(mode, "allocation")) {
            v4_unicode_allocation_failure = 1;
            (void)freak_v4_word_to_lower(value);
        } else if (!strcmp(mode, "mutated-utf8")) {
            ((unsigned char *)(uintptr_t)value)[0] = 0xff;
            (void)freak_v4_word_to_lower(value);
        } else return 98;
    }
    return 99;
}

static void v4_unicode_storage(void) {
    assert(freak_llvm_owned_count == 0 && freak_c_owned_word_count == 0);
    size_t unchanged = 12345;
    assert(!freak_llvm_word_owned_size(0, &unchanged) && unchanged == 12345);
    assert(!freak_llvm_word_owned_size(1, &unchanged) && unchanged == 12345);
    assert(!freak_llvm_word_owned_size((int64_t)(uintptr_t)"foreign", &unchanged) && unchanged == 12345);
    assert(freak_llvm_word_size((int64_t)(uintptr_t)"legacy") == 6);
    const unsigned char sized[] = {'A', 0, 'B'};
    int64_t input = v4_unicode_owner(sized, sizeof(sized));
    size_t stored = 0;
    assert(freak_llvm_word_owned_size(input, &stored) && stored == sizeof(sized));
    assert(!freak_llvm_word_owned_size(input, NULL));
    int64_t lower = freak_v4_word_to_lower(input);
    assert(lower != input && freak_llvm_owned_count == 2);
    v4_unicode_owner_bytes(input, sized, sizeof(sized));
    freak_v4_word_drop(input);
    unchanged = 12345;
    assert(!freak_llvm_word_owned_size(input, &unchanged) && unchanged == 12345);
    v4_unicode_owner_bytes(lower, "a\0b", 3);
    freak_v4_word_drop(lower);
    assert(freak_llvm_owned_count == 0);
    input = v4_unicode_owner(NULL, 0);
    assert(freak_llvm_word_owned_size(input, &stored) && stored == 0);
    lower = freak_v4_word_to_lower(input);
    assert(lower != input && freak_llvm_owned_count == 2);
    freak_v4_word_drop(input);
    v4_unicode_owner_bytes(lower, NULL, 0);
    freak_v4_word_drop(lower);

    static const unsigned char pattern[] = {
        0xc8,0xba, 0xe2,0x84,0xaa, 0xc4,0xb0,
        0xf0,0x96,0xba,0xa0, 0xce,0xa3, 0
    };
    static const unsigned char lowered[] = {
        0xe2,0xb1,0xa5, 'k', 'i',0xcc,0x87,
        0xf0,0x96,0xba,0xbb, 0xcf,0x82, 0
    };
    const size_t repeats = 4096;
    unsigned char *large = malloc(sizeof(pattern) * repeats);
    assert(large);
    for (size_t index = 0; index < repeats; index++) memcpy(large + index * sizeof(pattern), pattern, sizeof(pattern));
    for (unsigned iteration = 0; iteration < 32; iteration++) {
        input = v4_unicode_owner(large, sizeof(pattern) * repeats);
        lower = freak_v4_word_to_lower(input);
        assert(lower != input && freak_llvm_owned_count == 2);
        freak_v4_word_drop(input);
        assert(freak_v4_word_bytes(lower) == (int64_t)(sizeof(lowered) * repeats));
        assert(freak_v4_word_length(lower) == (int64_t)(7 * repeats));
        for (size_t index = 0; index < repeats; index++) {
            assert(!memcmp((const unsigned char *)(uintptr_t)lower + index * sizeof(lowered), lowered, sizeof(lowered)));
        }
        freak_v4_word_drop(lower);
        assert(freak_llvm_owned_count == 0 && freak_c_owned_word_count == 0);
    }
    free(large);
    assert(freak_llvm_owned_count == 0 && freak_c_owned_word_count == 0);
    puts("v4-unicode-storage=ok");
}

static unsigned v4_unicode_hex(char value) {
    if (value >= '0' && value <= '9') return (unsigned)(value - '0');
    if (value >= 'a' && value <= 'f') return (unsigned)(value - 'a' + 10);
    assert(0 && "invalid batch hexadecimal byte");
    return 0;
}

static void v4_unicode_batch(void) {
    char line[131072];
    unsigned char bytes[65536];
    while (fgets(line, sizeof(line), stdin)) {
        size_t length = strlen(line);
        assert(length && line[length - 1] == '\n');
        length--;
        assert(!(length % 2) && length / 2 <= sizeof(bytes));
        for (size_t index = 0; index < length / 2; index++) {
            bytes[index] = (unsigned char)((v4_unicode_hex(line[index * 2]) << 4) | v4_unicode_hex(line[index * 2 + 1]));
        }
        assert(freak_llvm_owned_count == 0 && freak_c_owned_word_count == 0);
        int64_t input = v4_unicode_owner(bytes, length / 2);
        int64_t result = freak_v4_word_to_lower(input);
        assert(result != input && freak_llvm_owned_count == 2);
        v4_unicode_owner_bytes(input, bytes, length / 2);
        freak_v4_word_drop(input);
        int64_t result_length = freak_v4_word_bytes(result);
        const unsigned char *output = (const unsigned char *)(uintptr_t)result;
        for (int64_t index = 0; index < result_length; index++) printf("%02x", output[index]);
        printf(" %" PRId64 " %" PRId64 "\n", result_length, freak_v4_word_length(result));
        freak_v4_word_drop(result);
        assert(freak_llvm_owned_count == 0 && freak_c_owned_word_count == 0);
    }
    assert(!ferror(stdin));
}

int main(int argc, char **argv) {
#ifdef _WIN32
    /* Keep deliberate abort tests noninteractive with one exact diagnostic. */
    _set_abort_behavior(0, _WRITE_ABORT_MSG | _CALL_REPORTFAULT);
#endif
    if (argc > 1 && !strcmp(argv[1], "--batch")) {
        v4_unicode_batch();
        return 0;
    }
    if (argc > 1) return v4_unicode_failure(argv[1]);
    v4_unicode_storage();
    return 0;
}
