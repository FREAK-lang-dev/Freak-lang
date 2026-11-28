/* C side of examples/c_words_native.fk (tier 3 C ABI: word bytes at a C
   boundary). A FREAK `lend s: word` extern parameter arrives as the pair
   (const char *bytes, size_t length). The bytes are borrowed for the call
   and are not NUL-terminated for C, so every helper here uses the length
   and none calls strlen. */
#include <stddef.h>

size_t cw_count_byte(const char *bytes, size_t length, int byte) {
    size_t count = 0;
    for (size_t i = 0; i < length; ++i) count += (unsigned char)bytes[i] == (unsigned char)byte;
    return count;
}

/* 32-bit FNV-1a over exactly the lent bytes. */
unsigned cw_checksum(const char *bytes, size_t length) {
    unsigned hash = 2166136261u;
    for (size_t i = 0; i < length; ++i) {
        hash ^= (unsigned char)bytes[i];
        hash *= 16777619u;
    }
    return hash;
}

_Bool cw_same(const char *left, size_t left_length, const char *right, size_t right_length) {
    if (left_length != right_length) return 0;
    for (size_t i = 0; i < left_length; ++i) if (left[i] != right[i]) return 0;
    return 1;
}

int cw_byte_at(const char *bytes, size_t length, size_t index) {
    return index < length ? (unsigned char)bytes[index] : -1;
}

long cw_lengths(long scale, const char *first, size_t first_length, const char *second, size_t second_length) {
    (void)first;
    (void)second;
    return (long)first_length * scale + (long)second_length;
}

/* The pointer C receives is the word's own storage, not a copy. */
static const char *cw_seen;
static size_t cw_seen_length;
void cw_remember(const char *bytes, size_t length) {
    cw_seen = bytes;
    cw_seen_length = length;
}
_Bool cw_is_remembered(const char *bytes, size_t length) {
    return bytes == cw_seen && length == cw_seen_length;
}

short cw_short_len(const char *bytes, size_t length) {
    (void)bytes;
    return (short)-(long)length;
}
