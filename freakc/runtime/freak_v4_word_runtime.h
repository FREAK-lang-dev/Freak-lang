#pragma once

#include <stdint.h>

/* Compiler-private native V4 ABI. A word is an i64 data pointer whose exact
   byte length is recorded in the existing owned-word registry. This is not a
   public C ABI for FREAK word and never authorizes arbitrary foreign pointers.

   All word-returning operations allocate a fresh, independently owned value,
   including empty words and boolean conversions. Inputs are borrowed except
   drop, which consumes an owner. The compiler implements single-owner moves;
   clone is the only operation that duplicates ownership. Zero is a consumed
   cleanup sentinel: drop(0) is legal, but observations require a live word.

   Ordinary native word values are constructed through this API. Legacy V3
   byte operations and their borrowed C-string compatibility are unchanged. */

/* Copies exactly byte_length bytes, without reading a source terminator.
   UTF-8 must encode Unicode scalars; embedded U+0000 is valid. The source need
   only remain valid during the call. Null with zero length constructs empty.
   Invalid UTF-8, lengths, indexes, and ranges cause a named panic-abort. */
int64_t freak_v4_word_from_bytes(int64_t data, int64_t byte_length);
int64_t freak_v4_word_clone(int64_t value);
int64_t freak_v4_word_concat(int64_t left, int64_t right);
int64_t freak_v4_word_equal(int64_t left, int64_t right);
void freak_v4_word_say(int64_t value);
void freak_v4_word_say_err(int64_t value);
void freak_v4_word_drop(int64_t value);

int64_t freak_v4_word_from_int(int64_t value);
int64_t freak_v4_word_from_bool(int64_t value);
int64_t freak_v4_word_from_num(double value);
/* Legacy lenient word_to_int alias, not the bible maybe<int> method. */
int64_t freak_v4_word_to_int(int64_t value);

/* Count Unicode scalars, not grapheme clusters or UTF-8 bytes. */
int64_t freak_v4_word_length(int64_t value);
int64_t freak_v4_word_bytes(int64_t value);
int64_t freak_v4_word_char_at(int64_t value, int64_t scalar_index);
/* slice uses scalar [start,end); substring uses scalar (start,count). */
int64_t freak_v4_word_slice(int64_t value, int64_t start, int64_t end);
int64_t freak_v4_word_substring(int64_t value, int64_t start, int64_t count);
int64_t freak_v4_word_starts_with(int64_t value, int64_t prefix);
int64_t freak_v4_word_ends_with(int64_t value, int64_t suffix);
int64_t freak_v4_word_contains(int64_t value, int64_t needle);

/* Unicode casing requires pinned tables and contextual mappings. No to_lower
   entry is provided by this owned-storage slice. */
