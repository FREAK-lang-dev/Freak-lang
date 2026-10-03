/* The core/registry stays unchanged. Test-local observers check a borrowed
   owner's exact state and forbid allocations while the parser is active. */
#include "freak_runtime.c"
#include "freak_v4_word_runtime.h"

#include <assert.h>
#include <inttypes.h>
#include <limits.h>

static bool probe_active = false;
static int64_t probe_tag = 91, probe_value = 92;
static int64_t probe_word = 0;
static size_t probe_owners = 0, probe_c_owners = 0, probe_length = 0, probe_capacity = 0;
static freak_llvm_owned_word* probe_record = NULL;

static void probe_unchanged(void) {
    assert(freak_llvm_owned_count == probe_owners);
    assert(freak_c_owned_word_count == probe_c_owners);
    assert(freak_array_live_count == 0);
    if (probe_record) {
        assert(freak_llvm_owned_find((void*)(uintptr_t)probe_word, NULL) == probe_record);
        assert(probe_record->pointer == (void*)(uintptr_t)probe_word);
        assert(probe_record->length == probe_length);
        assert(probe_record->capacity == probe_capacity);
    }
}

#ifndef FREAK_V4_WORD_PARSE_DIRECT_LINK
static void probe_no_allocation(void) {
    if (probe_active) {
        fputs("word-parse-probe: parser allocated or freed storage\n", stderr);
        _Exit(90);
    }
}
static void* probe_malloc(size_t size) { probe_no_allocation(); return malloc(size); }
static void* probe_calloc(size_t count, size_t size) {
    probe_no_allocation(); return calloc(count, size);
}
static void* probe_realloc(void* pointer, size_t size) {
    probe_no_allocation(); return realloc(pointer, size);
}
static void probe_free(void* pointer) { probe_no_allocation(); free(pointer); }
static _Noreturn void probe_abort(void) {
    if (probe_active) {
        probe_unchanged();
        assert(probe_tag == 91 && probe_value == 92);
    }
    abort();
}
#define malloc probe_malloc
#define calloc probe_calloc
#define realloc probe_realloc
#define free probe_free
#define abort probe_abort
#include "freak_v4_word_runtime.c"
#undef malloc
#undef calloc
#undef realloc
#undef free
#undef abort
#endif

#ifdef FREAK_V4_WORD_PARSE_LEGACY_CONTROL
/* A deliberately wrong adapter calls the unchanged lenient API. Its complete
   ordinary output must be rejected by the checked-parser oracle, not a crash. */
static void probe_legacy_adapter(int64_t word, int64_t* tag, int64_t* value) {
    *value = freak_v4_word_to_int(word);
    *tag = 1;
}
#define freak_v4_word_parse_int_checked probe_legacy_adapter
#endif

static void probe_begin(int64_t word) {
    probe_word = word;
    probe_owners = freak_llvm_owned_count;
    probe_c_owners = freak_c_owned_word_count;
    probe_record = freak_llvm_owned_find((void*)(uintptr_t)word, NULL);
    probe_length = probe_record ? probe_record->length : 0;
    probe_capacity = probe_record ? probe_record->capacity : 0;
    probe_active = true;
}

static void probe_case(const char* label, const void* bytes, size_t length) {
    assert(length <= (size_t)INT64_MAX);
    int64_t word = freak_v4_word_from_bytes((int64_t)(uintptr_t)bytes, (int64_t)length);
    assert(word && freak_llvm_owned_count == 1 && freak_c_owned_word_count == 0);
    int64_t first_tag = -1, first_value = -1;
    for (int sticky = 0; sticky <= 2; sticky++) {
        freak_parse_clear_status();
        if (sticky == 1) (void)freak_word_parse_int(freak_word_lit("x"));
        if (sticky == 2) (void)freak_word_parse_int(freak_word_lit("9223372036854775808"));
        assert(freak_parse_status() == sticky);
        for (int repeat = 0; repeat < 3; repeat++) {
            probe_tag = 91;
            probe_value = 92;
            probe_begin(word);
            freak_v4_word_parse_int_checked(word, &probe_tag, &probe_value);
            probe_active = false;
            probe_unchanged();
            assert(freak_parse_status() == sticky);
            assert(!length || !memcmp((const void*)(uintptr_t)word, bytes, length));
            assert(((const char*)(uintptr_t)word)[length] == '\0');
            if (first_tag == -1) { first_tag = probe_tag; first_value = probe_value; }
            else assert(probe_tag == first_tag && probe_value == first_value);
        }
    }
    printf("parse-int:%s:%" PRId64 ":%" PRId64 "\n", label, first_tag, first_value);
    freak_v4_word_drop(word);
    assert(freak_llvm_owned_count == 0 && freak_c_owned_word_count == 0);
}

#define CASE(label, text) probe_case(label, text, sizeof(text) - 1)
static void probe_cases(void) {
    CASE("zero", "0");
    CASE("plus-zero", "+0");
    CASE("minus-zero", "-0");
    CASE("leading-zeros", "00042");
    CASE("plus", "+42");
    CASE("minus", "-42");
    CASE("maximum", "9223372036854775807");
    CASE("minimum", "-9223372036854775808");
    CASE("plus-maximum", "+9223372036854775807");
    CASE("zero-minimum", "-0009223372036854775808");
    CASE("empty", "");
    CASE("sign-plus", "+");
    CASE("sign-minus", "-");
    CASE("double-sign", "--1");
    CASE("mixed-sign", "+-1");
    CASE("leading-space", " 42");
    CASE("trailing-space", "42 ");
    CASE("tab", "\t42");
    CASE("newline", "42\n");
    CASE("decimal", "4.2");
    CASE("exponent", "1e2");
    CASE("hex", "0x10");
    CASE("separator", "1_000");
    CASE("prefix-junk", "x12");
    CASE("suffix-junk", "12junk");
    CASE("nul", "\0");
    CASE("nul-suffix", "12\0junk");
    CASE("nul-leading", "\00012");
    CASE("fullwidth-digits", "\xef\xbc\x91\xef\xbc\x92");
    CASE("arabic-digit", "\xd9\xa1");
    CASE("unicode-space", "\xc2\xa0" "42");
    CASE("unicode-suffix", "42\xf0\x9f\x98\x80");
    CASE("positive-overflow", "9223372036854775808");
    CASE("negative-overflow", "-9223372036854775809");
    CASE("huge-positive", "99999999999999999999999999999999999999");
    CASE("huge-negative", "-99999999999999999999999999999999999999");
    size_t length = 262144;
    char* large = (char*)malloc(length);
    assert(large);
    memset(large, '0', length);
    large[length - 1] = '7';
    probe_case("large-leading-zeros", large, length);
    large[length - 1] = 'x';
    probe_case("large-suffix", large, length);
    memset(large, '9', length);
    probe_case("large-overflow", large, length);
    free(large);
    freak_parse_clear_status();
    int64_t legacy = freak_v4_word_from_bytes((int64_t)(uintptr_t)"  -42junk", 9);
    assert(freak_v4_word_to_int(legacy) == -42 && freak_parse_status() == 0);
    freak_v4_word_drop(legacy);
    puts("borrow-and-status=ok");
    puts("legacy-lenient=ok");
    puts("v4-word-parse-runtime=ok");
}

static int probe_failure(const char* mode) {
    int64_t word = 0;
    if (strstr(mode, "-poison")) word = 1;
    else if (!strcmp(mode, "foreign")) word = (int64_t)(uintptr_t)"123";
    else if (!strcmp(mode, "unknown")) word = 1;
    else if (!strcmp(mode, "negative")) word = -1;
    else if (!strcmp(mode, "null")) word = 0;
    else {
        word = freak_v4_word_from_bytes((int64_t)(uintptr_t)"7", 1);
        if (!strcmp(mode, "stale")) freak_v4_word_drop(word);
        else if (!strcmp(mode, "size-max")) {
            freak_llvm_owned_find((void*)(uintptr_t)word, NULL)->length = SIZE_MAX;
        } else if (!strcmp(mode, "signed-overflow")) {
            assert(sizeof(size_t) > 4);
            freak_llvm_owned_find((void*)(uintptr_t)word, NULL)->length = (size_t)INT64_MAX + (size_t)1;
        } else if (!strcmp(mode, "utf8-after-overflow") || !strcmp(mode, "utf8-after-junk")) {
            const char* text = !strcmp(mode, "utf8-after-overflow") ? "999999999999999999999999999999X" : "xX";
            size_t length = strlen(text);
            freak_v4_word_drop(word);
            word = freak_v4_word_from_bytes((int64_t)(uintptr_t)text, (int64_t)length);
            ((unsigned char*)(uintptr_t)word)[length - 1] = 0xff;
        } else if (!strncmp(mode, "utf8-", 5)) {
            static const unsigned char invalid[][4] = {
                {0x80}, {0xc0,0x80}, {0xc1,0xbf}, {0xc2}, {0xdf,0x7f},
                {0xe0,0x9f,0xbf}, {0xe1,0x80}, {0xed,0xa0,0x80},
                {0xf0,0x8f,0xbf,0xbf}, {0xf0,0x90,0x80},
                {0xf4,0x90,0x80,0x80}, {0xf5,0x80,0x80,0x80}, {0xff}
            };
            static const size_t lengths[] = {1,2,2,1,2,3,2,3,4,3,4,4,1};
            unsigned index = (unsigned)strtoul(mode + 5, NULL, 10);
            assert(index < sizeof(lengths) / sizeof(lengths[0]));
            freak_v4_word_drop(word);
            unsigned char valid[4] = {'0','0','0','0'};
            word = freak_v4_word_from_bytes((int64_t)(uintptr_t)valid, (int64_t)lengths[index]);
            memcpy((void*)(uintptr_t)word, invalid[index], lengths[index]);
        } else if (strcmp(mode, "null-tag") && strcmp(mode, "null-value") &&
                   strcmp(mode, "null-both") && strcmp(mode, "alias-slots")) {
            return 98;
        }
    }
    probe_begin(word);
    if (!strncmp(mode, "null-tag", 8)) freak_v4_word_parse_int_checked(word, NULL, &probe_value);
    else if (!strncmp(mode, "null-value", 10)) freak_v4_word_parse_int_checked(word, &probe_tag, NULL);
    else if (!strncmp(mode, "null-both", 9)) freak_v4_word_parse_int_checked(word, NULL, NULL);
    else if (!strncmp(mode, "alias-slots", 11)) freak_v4_word_parse_int_checked(word, &probe_tag, &probe_tag);
    else freak_v4_word_parse_int_checked(word, &probe_tag, &probe_value);
    return 99;
}

int main(int argc, char** argv) {
#ifdef _WIN32
    _set_abort_behavior(0, _WRITE_ABORT_MSG | _CALL_REPORTFAULT);
#endif
    if (argc == 1) { probe_cases(); return 0; }
    assert(argc == 2);
    if (!strcmp(argv[1], "audit-LLVM")) {
        volatile int64_t leaked = freak_v4_word_from_int(7); (void)leaked; return 0;
    }
    if (!strcmp(argv[1], "audit-C")) {
        volatile freak_word leaked = freak_word_from_int(7); (void)leaked; return 0;
    }
    if (!strcmp(argv[1], "cap-address")) {
        volatile char* pointer = (char*)malloc(1);
        free((void*)pointer);
        return pointer[0];
    }
    if (!strcmp(argv[1], "cap-undefined")) {
        volatile int value = INT_MAX, one = 1; return value + one;
    }
#ifndef FREAK_V4_WORD_PARSE_DIRECT_LINK
    (void)probe_calloc;
    (void)probe_realloc;
    if (!strcmp(argv[1], "cap-observer")) { probe_active = true; probe_free(NULL); return 99; }
#endif
    return probe_failure(argv[1]);
}
