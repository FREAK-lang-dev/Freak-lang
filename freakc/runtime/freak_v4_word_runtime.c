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
    size_t length;
    if (!freak_llvm_word_owned_size(value, &length)) {
        freak_v4_word_panic("word value is not live owned storage");
    }
    if (length > (size_t)INT64_MAX) freak_v4_word_panic("byte length overflow");
    return length;
}

static const unsigned char* freak_v4_word_data(int64_t value) {
    return (const unsigned char*)(uintptr_t)value;
}

/* Set once by a bootstrap-mode entry. Only then are cached scalar counts
 * trusted; otherwise every observation revalidates UTF-8, so storage that
 * changed behind the runtime still reaches the named panic. */
static int freak_v4_word_cache_trusted = 0;

void freak_v4_word_v1_mode(void) {
    freak_v4_word_cache_trusted = 1;
}

static size_t freak_v4_word_scalar_count(int64_t value) {
    size_t length = freak_v4_word_size(value);
    size_t count;
    if (freak_v4_word_cache_trusted && freak_llvm_word_scalar_cache_get(value, &count)) return count;
    count = freak_v4_word_count(freak_v4_word_data(value), length);
    freak_llvm_word_scalar_cache_set(value, count);
    return count;
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
    size_t count = freak_v4_word_count(source, length);
    char* copy = (char*)malloc(length + 1);
    if (!copy) freak_v4_word_panic("out of memory copying owned storage");
    if (length) memcpy(copy, source, length);
    copy[length] = '\0';
    int64_t result = freak_v4_word_adopt(copy, length);
    freak_llvm_word_scalar_cache_set(result, count);
    return result;
}

/* Bootstrap-mode word copies share the immutable allocation, as V1 words
 * did; each owner still drops its own share. */
int64_t freak_v4_word_v1_share(int64_t value) {
    (void)freak_v4_word_size(value);
    int64_t shared = freak_llvm_word_share(value);
    return shared ? shared : freak_v4_word_clone(value);
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
    if (!value) return;
    (void)freak_v4_word_size(value);
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

void freak_v4_word_parse_int_checked(int64_t value, int64_t* out_is_some,
                                     int64_t* out_value) {
    if (!out_is_some || !out_value || out_is_some == out_value) {
        freak_v4_word_panic("invalid checked integer result slots");
    }
    size_t length = freak_v4_word_size(value);
    if (length == SIZE_MAX) freak_v4_word_panic("byte length overflow");
    const unsigned char* data = freak_v4_word_data(value);
    (void)freak_v4_word_count(data, length);

    size_t offset = 0;
    bool negative = false;
    if (offset < length && (data[offset] == '+' || data[offset] == '-')) {
        negative = data[offset] == '-';
        offset++;
    }
    uint64_t magnitude = 0;
    uint64_t limit = negative ? (uint64_t)INT64_MAX + 1u : (uint64_t)INT64_MAX;
    bool valid = offset < length;
    while (valid && offset < length) {
        unsigned char byte = data[offset++];
        if (byte < '0' || byte > '9') {
            valid = false;
        } else {
            unsigned digit = (unsigned)(byte - '0');
            if (magnitude > (limit - digit) / 10u) valid = false;
            else magnitude = magnitude * 10u + digit;
        }
    }
    int64_t result = 0;
    if (valid) {
        if (!negative) result = (int64_t)magnitude;
        else if (magnitude == (uint64_t)INT64_MAX + 1u) result = INT64_MIN;
        else result = -(int64_t)magnitude;
    }
    *out_value = result;
    *out_is_some = valid ? 1 : 0;
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
    /* An all-ASCII word has one byte per scalar. */
    if (freak_v4_word_scalar_count(value) == length) {
        return freak_v4_word_from_bytes((int64_t)(uintptr_t)(data + start), (int64_t)(end - start));
    }
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

/* Bootstrap mode keeps V1's lenient indexing, which the V4 crates were
 * written against: an index outside the word gives "", and a substring
 * count past the end is clamped. Indexes stay scalar, matching length(). */
int64_t freak_v4_word_v1_char_at(int64_t value, int64_t scalar_index) {
    size_t count = freak_v4_word_scalar_count(value);
    if (scalar_index < 0 || (uint64_t)scalar_index >= (uint64_t)count) {
        return freak_v4_word_from_bytes((int64_t)(uintptr_t)"", 0);
    }
    size_t index = (size_t)scalar_index;
    return freak_v4_word_copy_scalar_range(value, index, index + 1);
}

int64_t freak_v4_word_v1_substring(int64_t value, int64_t start, int64_t count) {
    size_t length = freak_v4_word_scalar_count(value);
    if (start < 0 || count <= 0 || (uint64_t)start >= (uint64_t)length) {
        return freak_v4_word_from_bytes((int64_t)(uintptr_t)"", 0);
    }
    size_t first = (size_t)start;
    size_t end = (uint64_t)count > (uint64_t)(length - first) ? length : first + (size_t)count;
    return freak_v4_word_copy_scalar_range(value, first, end);
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

static int64_t freak_v4_word_copy_bytes(const unsigned char* data, size_t length) {
    char* copy = (char*)malloc(length + 1);
    if (!copy) freak_v4_word_panic("out of memory copying owned storage");
    if (length) memcpy(copy, data, length);
    copy[length] = '\0';
    return freak_v4_word_adopt(copy, length);
}

int64_t freak_v4_word_snapshot_escape(int64_t value) {
    size_t length = freak_v4_word_size(value);
    const unsigned char* data = freak_v4_word_data(value);
    (void)freak_v4_word_count(data, length);
    size_t escaped = length;
    for (size_t i = 0; i < length; i++) {
        unsigned char ch = data[i];
        if (ch == '%' || ch == '|' || ch == '\n' || ch == '\r') {
            if (escaped > SIZE_MAX - 3) freak_v4_word_panic("snapshot escape overflow");
            escaped += 2;
        }
    }
    char* out = (char*)malloc(escaped + 1);
    if (!out) freak_v4_word_panic("out of memory copying owned storage");
    size_t at = 0;
    for (size_t i = 0; i < length; i++) {
        const char* code = NULL;
        switch (data[i]) {
            case '%': code = "%25"; break;
            case '|': code = "%7C"; break;
            case '\n': code = "%0A"; break;
            case '\r': code = "%0D"; break;
            default: break;
        }
        if (code) { memcpy(out + at, code, 3); at += 3; }
        else out[at++] = (char)data[i];
    }
    out[at] = '\0';
    return freak_v4_word_adopt(out, at);
}

int64_t freak_v4_word_snapshot_unescape(int64_t value) {
    size_t length = freak_v4_word_size(value);
    const unsigned char* data = freak_v4_word_data(value);
    (void)freak_v4_word_count(data, length);
    char* out = (char*)malloc(length + 1);
    if (!out) freak_v4_word_panic("out of memory copying owned storage");
    size_t at = 0, i = 0;
    while (i < length) {
        if (data[i] == '%' && length - i > 2) {
            char decoded = 0;
            if (data[i + 1] == '2' && data[i + 2] == '5') decoded = '%';
            else if (data[i + 1] == '7' && data[i + 2] == 'C') decoded = '|';
            else if (data[i + 1] == '0' && data[i + 2] == 'A') decoded = '\n';
            else if (data[i + 1] == '0' && data[i + 2] == 'D') decoded = '\r';
            if (decoded) { out[at++] = decoded; i += 3; continue; }
        }
        out[at++] = (char)data[i++];
    }
    out[at] = '\0';
    return freak_v4_word_adopt(out, at);
}

static int64_t freak_v4_word_snapshot_count(int64_t value, unsigned char separator) {
    size_t length = freak_v4_word_size(value);
    const unsigned char* data = freak_v4_word_data(value);
    (void)freak_v4_word_count(data, length);
    if (!length) return 0;
    int64_t count = 1;
    for (size_t i = 0; i < length; i++) {
        if (data[i] == separator) count++;
    }
    return count;
}

static int64_t freak_v4_word_snapshot_piece(int64_t value, int64_t wanted, unsigned char separator) {
    size_t length = freak_v4_word_size(value);
    const unsigned char* data = freak_v4_word_data(value);
    (void)freak_v4_word_count(data, length);
    if (wanted < 0) return freak_v4_word_copy_bytes(data, 0);
    int64_t piece = 0;
    size_t start = 0;
    for (size_t i = 0; i < length; i++) {
        if (data[i] == separator) {
            if (piece == wanted) return freak_v4_word_copy_bytes(data + start, i - start);
            piece++;
            start = i + 1;
        }
    }
    if (piece == wanted) return freak_v4_word_copy_bytes(data + start, length - start);
    return freak_v4_word_copy_bytes(data, 0);
}

int64_t freak_v4_word_snapshot_line_count(int64_t value) {
    return freak_v4_word_snapshot_count(value, '\n');
}

int64_t freak_v4_word_snapshot_line(int64_t value, int64_t wanted) {
    return freak_v4_word_snapshot_piece(value, wanted, '\n');
}

int64_t freak_v4_word_snapshot_field_count(int64_t value) {
    return freak_v4_word_snapshot_count(value, '|');
}

int64_t freak_v4_word_snapshot_field_raw(int64_t value, int64_t wanted) {
    return freak_v4_word_snapshot_piece(value, wanted, '|');
}

/* Bootstrap word.checksum(): the same stable 63-bit FNV-1a as V1's
   freak_word_checksum, so hash tables in the compiler crates keep their
   layout when V4 builds them. */
int64_t freak_v4_word_checksum(int64_t value) {
    size_t length = freak_v4_word_size(value);
    const unsigned char* data = freak_v4_word_data(value);
    uint64_t hash = UINT64_C(14695981039346656037);
    for (size_t i = 0; i < length; i++) {
        hash ^= (uint64_t)data[i];
        hash *= UINT64_C(1099511628211);
    }
    return (int64_t)(hash & UINT64_C(0x7fffffffffffffff));
}

/* Bootstrap chr(code): the one-scalar word for a Unicode code point, as V1's
   freak_char_to_word. Surrogates and values past U+10FFFF are rejected. */
int64_t freak_v4_word_chr(int64_t code) {
    if (code < 0 || code > 0x10FFFF || (code >= 0xD800 && code <= 0xDFFF)) {
        freak_v4_word_panic("chr code point is not a Unicode scalar value");
    }
    unsigned char buf[4];
    size_t len = 0;
    uint32_t c = (uint32_t)code;
    if (c <= 0x7F) {
        buf[0] = (unsigned char)c; len = 1;
    } else if (c <= 0x7FF) {
        buf[0] = (unsigned char)(0xC0 | (c >> 6));
        buf[1] = (unsigned char)(0x80 | (c & 0x3F));
        len = 2;
    } else if (c <= 0xFFFF) {
        buf[0] = (unsigned char)(0xE0 | (c >> 12));
        buf[1] = (unsigned char)(0x80 | ((c >> 6) & 0x3F));
        buf[2] = (unsigned char)(0x80 | (c & 0x3F));
        len = 3;
    } else {
        buf[0] = (unsigned char)(0xF0 | (c >> 18));
        buf[1] = (unsigned char)(0x80 | ((c >> 12) & 0x3F));
        buf[2] = (unsigned char)(0x80 | ((c >> 6) & 0x3F));
        buf[3] = (unsigned char)(0x80 | (c & 0x3F));
        len = 4;
    }
    return freak_v4_word_from_bytes((int64_t)(uintptr_t)buf, (int64_t)len);
}

/* Bootstrap word_to_num(text): strtod over the owned bytes, as V1. */
double freak_v4_word_to_num(int64_t value) {
    (void)freak_v4_word_scalar_count(value);
    return freak_word_to_num(freak_llvm_word_view(value));
}
