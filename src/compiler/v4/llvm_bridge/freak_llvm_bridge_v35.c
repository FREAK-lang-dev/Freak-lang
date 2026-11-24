/* V3.5 C-host adapter for the LLVM bridge.
 *
 * Tools built by v35_seed.py (V3.5 --c) pass words as freak_word. This file
 * turns those into the core's (bytes, length) pairs and turns error text
 * back into a word. Every other bridge call takes and returns int64 only, so
 * FREAK declares the core functions directly. A V4-native host needs its own
 * adapter over the V4 word handle ABI; the core does not change. */
#include "freak_llvm_bridge_v35.h"

#include <stdlib.h>
#include <string.h>

int64_t freak_lb35_session_new(freak_word triple, freak_word name, int64_t opt) {
    return freak_lb_session_new(triple.data, triple.length, name.data, name.length, opt);
}

freak_word freak_lb35_error(int64_t session) {
    size_t length = 0;
    const char* text = freak_lb_error_text(session, &length);
    char* copy = malloc(length + 1);
    if (!copy) return freak_word_lit("");
    memcpy(copy, text, length);
    copy[length] = 0;
    return freak_word_own(copy, length);
}

int64_t freak_lb35_struct_begin(int64_t session, freak_word name) {
    return freak_lb_struct_begin(session, name.data, name.length);
}

int64_t freak_lb35_function(int64_t session, freak_word name, int64_t fn_type, int64_t linkage) {
    return freak_lb_function(session, name.data, name.length, fn_type, linkage);
}

int64_t freak_lb35_global_bytes(int64_t session, freak_word name, freak_word bytes, int64_t linkage) {
    return freak_lb_global_bytes(session, name.data, name.length, bytes.data, bytes.length, linkage);
}

int64_t freak_lb35_block(int64_t session, int64_t function, freak_word name) {
    return freak_lb_block(session, function, name.data, name.length);
}

int64_t freak_lb35_attribute(int64_t session, int64_t function, int64_t index, freak_word name) {
    return freak_lb_attribute(session, function, index, name.data, name.length);
}

int64_t freak_lb35_attribute_int(int64_t session, int64_t target, int64_t index, freak_word name, int64_t value) {
    return freak_lb_attribute_int(session, target, index, name.data, name.length, value);
}

int64_t freak_lb35_attribute_type(int64_t session, int64_t target, int64_t index, freak_word name, int64_t type) {
    return freak_lb_attribute_type(session, target, index, name.data, name.length, type);
}

int64_t freak_lb35_debug_unit(int64_t session, freak_word file, freak_word directory, freak_word producer) {
    return freak_lb_debug_unit(session, file.data, file.length, directory.data, directory.length,
                               producer.data, producer.length);
}

int64_t freak_lb35_emit(int64_t session, int64_t format, freak_word path) {
    return freak_lb_emit(session, format, path.data, path.length);
}
