#include "freak_v4_unicode_runtime.h"
#include "freak_v4_unicode_lower_tables.h"
#include "freak_v4_word_runtime.h"
#include "freak_runtime.h"

#include <limits.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

static _Noreturn void freak_v4_unicode_panic(const char *reason) {
    fprintf(stderr, "FREAK: V4 Unicode panic: %s\n", reason);
    fflush(stderr);
    abort();
}

static int freak_v4_unicode_has_property(uint32_t scalar,
        const freak_v4_unicode_property_range *ranges, size_t count) {
    size_t first = 0, last = count;
    while (first < last) {
        size_t middle = first + (last - first) / 2;
        if (scalar < ranges[middle].first) last = middle;
        else if (scalar > ranges[middle].last) first = middle + 1;
        else return 1;
    }
    return 0;
}

static int freak_v4_unicode_is_cased(uint32_t scalar) {
    return freak_v4_unicode_has_property(scalar, freak_v4_unicode_cased,
        sizeof(freak_v4_unicode_cased) / sizeof(freak_v4_unicode_cased[0]));
}

static int freak_v4_unicode_is_ignorable(uint32_t scalar) {
    return freak_v4_unicode_has_property(scalar, freak_v4_unicode_case_ignorable,
        sizeof(freak_v4_unicode_case_ignorable) / sizeof(freak_v4_unicode_case_ignorable[0]));
}

/* The live owner and full UTF-8 validity are checked before this decoder runs.
 * Every continuation read therefore lies within the exact validated length. */
static uint32_t freak_v4_unicode_decode(const unsigned char *data, size_t *offset) {
    unsigned char first = data[(*offset)++];
    if (first <= 0x7f) return first;
    unsigned count = first <= 0xdf ? 1 : first <= 0xef ? 2 : 3;
    uint32_t value = first & (count == 1 ? 0x1fu : count == 2 ? 0x0fu : 0x07u);
    while (count--) value = (value << 6) | (data[(*offset)++] & 0x3fu);
    return value;
}

static const freak_v4_unicode_lower_mapping *freak_v4_unicode_mapping(uint32_t scalar) {
    size_t first = 0, last = sizeof(freak_v4_unicode_lower_mappings) / sizeof(freak_v4_unicode_lower_mappings[0]);
    while (first < last) {
        size_t middle = first + (last - first) / 2;
        const freak_v4_unicode_lower_mapping *entry = &freak_v4_unicode_lower_mappings[middle];
        if (scalar < entry->source) last = middle;
        else if (scalar > entry->source) first = middle + 1;
        else return entry;
    }
    return NULL;
}

static size_t freak_v4_unicode_width(uint32_t scalar) {
    return scalar <= 0x7fu ? 1 : scalar <= 0x7ffu ? 2 : scalar <= 0xffffu ? 3 : 4;
}

static size_t freak_v4_unicode_append_size(size_t size, size_t width) {
    if (size > (size_t)INT64_MAX || size >= SIZE_MAX ||
            width > (size_t)INT64_MAX - size || width >= SIZE_MAX - size) {
        freak_v4_unicode_panic("lowercase byte length overflow");
    }
    return size + width;
}

static size_t freak_v4_unicode_encode(unsigned char *data, size_t offset, uint32_t scalar) {
    if (scalar <= 0x7fu) data[offset++] = (unsigned char)scalar;
    else if (scalar <= 0x7ffu) {
        data[offset++] = (unsigned char)(0xc0u | (scalar >> 6));
        data[offset++] = (unsigned char)(0x80u | (scalar & 0x3fu));
    } else if (scalar <= 0xffffu) {
        data[offset++] = (unsigned char)(0xe0u | (scalar >> 12));
        data[offset++] = (unsigned char)(0x80u | ((scalar >> 6) & 0x3fu));
        data[offset++] = (unsigned char)(0x80u | (scalar & 0x3fu));
    } else {
        data[offset++] = (unsigned char)(0xf0u | (scalar >> 18));
        data[offset++] = (unsigned char)(0x80u | ((scalar >> 12) & 0x3fu));
        data[offset++] = (unsigned char)(0x80u | ((scalar >> 6) & 0x3fu));
        data[offset++] = (unsigned char)(0x80u | (scalar & 0x3fu));
    }
    return offset;
}

/* Only sigma examines following context. Sigma itself is non-ignorable, so
 * ignorable runs are examined at most twice per pass: linear input work. */
static int freak_v4_unicode_final_sigma(const unsigned char *data,
        size_t length, size_t next, int preceding_cased) {
    if (!preceding_cased) return 0;
    while (next < length) {
        uint32_t scalar = freak_v4_unicode_decode(data, &next);
        if (!freak_v4_unicode_is_ignorable(scalar)) return !freak_v4_unicode_is_cased(scalar);
    }
    return 1;
}

static size_t freak_v4_unicode_lower_pass(const unsigned char *data,
        size_t length, unsigned char *output) {
    size_t offset = 0, written = 0;
    int preceding_cased = 0;
    while (offset < length) {
        uint32_t scalar = freak_v4_unicode_decode(data, &offset);
        const freak_v4_unicode_lower_mapping *mapping = freak_v4_unicode_mapping(scalar);
        uint32_t first = mapping ? mapping->first : scalar;
        uint32_t second = mapping ? mapping->second : 0;
        unsigned count = mapping ? mapping->length : 1;
        if (scalar == 0x03a3u && freak_v4_unicode_final_sigma(data, length, offset, preceding_cased)) {
            first = 0x03c2u;
        }
        for (unsigned index = 0; index < count; index++) {
            uint32_t mapped = index == 0 ? first : second;
            size_t end = freak_v4_unicode_append_size(written, freak_v4_unicode_width(mapped));
            if (output) (void)freak_v4_unicode_encode(output, written, mapped);
            written = end;
        }
        /* Ignorable wins when a scalar has both properties. Context always
         * observes original scalars, never the newly lowercased expansion. */
        if (!freak_v4_unicode_is_ignorable(scalar)) preceding_cased = freak_v4_unicode_is_cased(scalar);
    }
    return written;
}

int64_t freak_v4_word_to_lower(int64_t value) {
    size_t length = 0;
    if (!value) freak_v4_unicode_panic("word value has been consumed");
    if (!freak_llvm_word_owned_size(value, &length)) freak_v4_unicode_panic("word value is not a live owner");
    (void)freak_v4_word_bytes(value);
    const unsigned char *data = (const unsigned char *)(uintptr_t)value;
    size_t size = freak_v4_unicode_lower_pass(data, length, NULL);
    unsigned char *lower = (unsigned char *)malloc(size + 1);
    if (!lower) freak_v4_unicode_panic("out of memory lowercasing word");
    (void)freak_v4_unicode_lower_pass(data, length, lower);
    lower[size] = 0;
    int64_t result = freak_v4_word_from_bytes((int64_t)(uintptr_t)lower, (int64_t)size);
    free(lower);
    return result;
}
