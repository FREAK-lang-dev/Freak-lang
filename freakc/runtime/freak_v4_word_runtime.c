#include "freak_v4_word_runtime.h"
#include "freak_runtime.h"

#include <inttypes.h>
#include <limits.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Existing ownership registry release; deliberately keep V3 code unchanged. */
extern void freak_llvm_word_release_replaced(int64_t previous, int64_t replacement);

static _Noreturn void freak_v4_word_panic(const char* reason) {
    fprintf(stderr, "FREAK: V4 word panic: %s\n", reason);
    fflush(stderr);
    abort();
}

/* Read one complete Unicode scalar, including scalar zero. No byte past the
   sized input is examined, and invalid encodings never become word values. */
static size_t freak_v4_word_scalar_width(
        const unsigned char* data, size_t length, size_t offset) {
    if (offset >= length) freak_v4_word_panic("invalid UTF-8");
    unsigned char first = data[offset];
    if (first <= 0x7f) return 1;
    if (first >= 0xc2 && first <= 0xdf) {
        if (length - offset < 2 || data[offset + 1] < 0x80 ||
                data[offset + 1] > 0xbf) freak_v4_word_panic("invalid UTF-8");
        return 2;
    }
    if (first >= 0xe0 && first <= 0xef) {
        if (length - offset < 3) freak_v4_word_panic("invalid UTF-8");
        unsigned char second = data[offset + 1];
        unsigned char third = data[offset + 2];
        if (third < 0x80 || third > 0xbf ||
                (first == 0xe0 ? second < 0xa0 || second > 0xbf :
                 first == 0xed ? second < 0x80 || second > 0x9f :
                 second < 0x80 || second > 0xbf)) {
            freak_v4_word_panic("invalid UTF-8");
        }
        return 3;
    }
    if (first >= 0xf0 && first <= 0xf4) {
        if (length - offset < 4) freak_v4_word_panic("invalid UTF-8");
        unsigned char second = data[offset + 1];
        unsigned char third = data[offset + 2];
        unsigned char fourth = data[offset + 3];
        if (third < 0x80 || third > 0xbf || fourth < 0x80 || fourth > 0xbf ||
                (first == 0xf0 ? second < 0x90 || second > 0xbf :
                 first == 0xf4 ? second < 0x80 || second > 0x8f :
                 second < 0x80 || second > 0xbf)) {
            freak_v4_word_panic("invalid UTF-8");
        }
        return 4;
    }
    freak_v4_word_panic("invalid UTF-8");
}

static size_t freak_v4_word_count(const unsigned char* data, size_t length) {
    size_t offset = 0, count = 0;
    while (offset < length) {
        offset += freak_v4_word_scalar_width(data, length, offset);
        count++;
    }
    return count;
}

static size_t freak_v4_word_size(int64_t value) {
    if (!value) freak_v4_word_panic("word value has been consumed");
    size_t length = freak_llvm_word_size(value);
    if (length > (size_t)INT64_MAX) freak_v4_word_panic("byte length overflow");
    return length;
}

static const unsigned char* freak_v4_word_data(int64_t value) {
    return (const unsigned char*)(uintptr_t)value;
}

static size_t freak_v4_word_scalar_count(int64_t value) {
    return freak_v4_word_count(freak_v4_word_data(value), freak_v4_word_size(value));
}

static int64_t freak_v4_word_adopt(char* data, size_t length) {
    int64_t result = freak_llvm_word_try_adopt_sized((int64_t)(uintptr_t)data, length);
    if (!result) {
        free(data);
        freak_v4_word_panic("out of memory tracking owned storage");
    }
    return result;
}

int64_t freak_v4_word_from_bytes(int64_t data, int64_t byte_length) {
    if (byte_length < 0) freak_v4_word_panic("negative byte length");
    uint64_t length64 = (uint64_t)byte_length;
    if (length64 >= (uint64_t)SIZE_MAX || length64 > (uint64_t)UINTPTR_MAX) {
        freak_v4_word_panic("byte length overflow");
    }
    size_t length = (size_t)length64;
    if (!data && length) freak_v4_word_panic("null byte source");
    if (length && (uintptr_t)data > UINTPTR_MAX - length) {
        freak_v4_word_panic("byte source range overflow");
    }
    const unsigned char* source = (const unsigned char*)(uintptr_t)data;
    (void)freak_v4_word_count(source, length);
    char* copy = (char*)malloc(length + 1);
    if (!copy) freak_v4_word_panic("out of memory copying owned storage");
    if (length) memcpy(copy, source, length);
    copy[length] = '\0';
    return freak_v4_word_adopt(copy, length);
}

int64_t freak_v4_word_clone(int64_t value) {
    return freak_v4_word_from_bytes(value, (int64_t)freak_v4_word_size(value));
}

int64_t freak_v4_word_concat(int64_t left, int64_t right) {
    size_t left_length = freak_v4_word_size(left);
    size_t right_length = freak_v4_word_size(right);
    if (right_length > (size_t)INT64_MAX - left_length ||
            right_length >= SIZE_MAX - left_length) {
        freak_v4_word_panic("concatenation length overflow");
    }
    (void)freak_v4_word_scalar_count(left);
    (void)freak_v4_word_scalar_count(right);
    size_t length = left_length + right_length;
    char* joined = (char*)malloc(length + 1);
    if (!joined) freak_v4_word_panic("out of memory concatenating words");
    if (left_length) memcpy(joined, freak_v4_word_data(left), left_length);
    if (right_length) memcpy(joined + left_length, freak_v4_word_data(right), right_length);
    joined[length] = '\0';
    return freak_v4_word_adopt(joined, length);
}

int64_t freak_v4_word_equal(int64_t left, int64_t right) {
    size_t left_length = freak_v4_word_size(left);
    size_t right_length = freak_v4_word_size(right);
    (void)freak_v4_word_scalar_count(left);
    (void)freak_v4_word_scalar_count(right);
    return left_length == right_length &&
        (!left_length || !memcmp(freak_v4_word_data(left), freak_v4_word_data(right), left_length));
}

void freak_v4_word_say(int64_t value) {
    (void)freak_v4_word_scalar_count(value);
    freak_say(freak_llvm_word_view(value));
}

void freak_v4_word_say_err(int64_t value) {
    (void)freak_v4_word_scalar_count(value);
    freak_say_err(freak_llvm_word_view(value));
}

void freak_v4_word_drop(int64_t value) {
    freak_llvm_word_release_replaced(value, 0);
}

int64_t freak_v4_word_from_int(int64_t value) {
    char buffer[32];
    int length = snprintf(buffer, sizeof(buffer), "%" PRId64, value);
    if (length < 0 || (size_t)length >= sizeof(buffer)) freak_v4_word_panic("integer formatting failed");
    return freak_v4_word_from_bytes((int64_t)(uintptr_t)buffer, length);
}

int64_t freak_v4_word_from_bool(int64_t value) {
    return freak_v4_word_from_bytes((int64_t)(uintptr_t)(value ? "true" : "false"), value ? 4 : 5);
}

int64_t freak_v4_word_from_num(double value) {
    char buffer[128];
    int length = snprintf(buffer, sizeof(buffer), "%g", value);
    if (length < 0 || (size_t)length >= sizeof(buffer)) freak_v4_word_panic("number formatting failed");
    return freak_v4_word_from_bytes((int64_t)(uintptr_t)buffer, length);
}

int64_t freak_v4_word_to_int(int64_t value) {
    (void)freak_v4_word_scalar_count(value);
    return freak_word_to_int(freak_llvm_word_view(value));
}

int64_t freak_v4_word_length(int64_t value) {
    return (int64_t)freak_v4_word_scalar_count(value);
}

int64_t freak_v4_word_bytes(int64_t value) {
    (void)freak_v4_word_scalar_count(value);
    return (int64_t)freak_v4_word_size(value);
}

static int64_t freak_v4_word_copy_scalar_range(
        int64_t value, size_t start, size_t end) {
    size_t length = freak_v4_word_size(value);
    const unsigned char* data = freak_v4_word_data(value);
    size_t offset = 0, scalar = 0, byte_start = 0, byte_end = 0;
    while (scalar < end) {
        if (scalar == start) byte_start = offset;
        offset += freak_v4_word_scalar_width(data, length, offset);
        scalar++;
    }
    if (start == end) byte_start = offset;
    byte_end = offset;
    return freak_v4_word_from_bytes((int64_t)(uintptr_t)(data + byte_start), (int64_t)(byte_end - byte_start));
}

int64_t freak_v4_word_char_at(int64_t value, int64_t scalar_index) {
    size_t count = freak_v4_word_scalar_count(value);
    if (scalar_index < 0 || (uint64_t)scalar_index >= (uint64_t)count) {
        freak_v4_word_panic("character index out of bounds");
    }
    size_t index = (size_t)scalar_index;
    return freak_v4_word_copy_scalar_range(value, index, index + 1);
}

int64_t freak_v4_word_slice(int64_t value, int64_t start, int64_t end) {
    size_t count = freak_v4_word_scalar_count(value);
    if (start < 0 || end < start || (uint64_t)end > (uint64_t)count) {
        freak_v4_word_panic("slice range out of bounds");
    }
    return freak_v4_word_copy_scalar_range(value, (size_t)start, (size_t)end);
}

int64_t freak_v4_word_substring(int64_t value, int64_t start, int64_t count) {
    size_t length = freak_v4_word_scalar_count(value);
    if (start < 0 || count < 0 || (uint64_t)start > (uint64_t)length ||
            (uint64_t)count > (uint64_t)length - (uint64_t)start) {
        freak_v4_word_panic("substring range out of bounds");
    }
    return freak_v4_word_copy_scalar_range(value, (size_t)start, (size_t)start + (size_t)count);
}

int64_t freak_v4_word_starts_with(int64_t value, int64_t prefix) {
    size_t length = freak_v4_word_size(value), prefix_length = freak_v4_word_size(prefix);
    (void)freak_v4_word_scalar_count(value);
    (void)freak_v4_word_scalar_count(prefix);
    return prefix_length <= length &&
        (!prefix_length || !memcmp(freak_v4_word_data(value), freak_v4_word_data(prefix), prefix_length));
}

int64_t freak_v4_word_ends_with(int64_t value, int64_t suffix) {
    size_t length = freak_v4_word_size(value), suffix_length = freak_v4_word_size(suffix);
    (void)freak_v4_word_scalar_count(value);
    (void)freak_v4_word_scalar_count(suffix);
    return suffix_length <= length &&
        (!suffix_length || !memcmp(freak_v4_word_data(value) + length - suffix_length, freak_v4_word_data(suffix), suffix_length));
}

int64_t freak_v4_word_contains(int64_t value, int64_t needle) {
    size_t length = freak_v4_word_size(value), needle_length = freak_v4_word_size(needle);
    (void)freak_v4_word_scalar_count(value);
    (void)freak_v4_word_scalar_count(needle);
    if (!needle_length) return 1;
    if (needle_length > length) return 0;
    const unsigned char* data = freak_v4_word_data(value);
    for (size_t offset = 0; offset <= length - needle_length; offset++) {
        if (!memcmp(data + offset, freak_v4_word_data(needle), needle_length)) return 1;
    }
    return 0;
}
