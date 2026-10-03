/* Include the unmodified core in this test translation unit so assertions can
   observe the actual private owner count rather than an approximate RSS proxy. */
#include "freak_runtime.c"
#include "freak_v4_word_runtime.h"

#include <assert.h>

static int64_t v4_probe_owner(const void* data, size_t length) {
    size_t before = freak_llvm_owned_count;
    int64_t result = freak_v4_word_from_bytes((int64_t)(uintptr_t)data, (int64_t)length);
    assert(result && freak_llvm_owned_count == before + 1);
    assert(freak_llvm_word_size(result) == length);
    return result;
}

static void v4_probe_bytes(int64_t value, const void* expected, size_t length) {
    assert(freak_v4_word_bytes(value) == (int64_t)length);
    assert(!length || !memcmp((const void*)(uintptr_t)value, expected, length));
    assert(((const char*)(uintptr_t)value)[length] == '\0');
}

static int v4_probe_failure(const char* mode) {
    static const unsigned char invalid[][4] = {
        {0x80}, {0xc0, 0x80}, {0xc1, 0xbf}, {0xc2}, {0xdf, 0x7f},
        {0xe0, 0x9f, 0xbf}, {0xe1, 0x80}, {0xed, 0xa0, 0x80},
        {0xf0, 0x8f, 0xbf, 0xbf}, {0xf0, 0x90, 0x80},
        {0xf4, 0x90, 0x80, 0x80}, {0xf5, 0x80, 0x80, 0x80}, {0xff}
    };
    static const size_t lengths[] = {1,2,2,1,2,3,2,3,4,3,4,4,1};
    if (!strncmp(mode, "utf8-", 5)) {
        unsigned index = (unsigned)strtoul(mode + 5, NULL, 10);
        assert(index < sizeof(lengths) / sizeof(lengths[0]));
        freak_v4_word_from_bytes((int64_t)(uintptr_t)invalid[index], (int64_t)lengths[index]);
        return 99;
    }
    if (!strcmp(mode, "negative-length")) { freak_v4_word_from_bytes(0, -1); return 99; }
    if (!strcmp(mode, "null-source")) { freak_v4_word_from_bytes(0, 1); return 99; }
    if (!strcmp(mode, "source-overflow")) { freak_v4_word_from_bytes(-1, 1); return 99; }
    if (!strcmp(mode, "consumed-word")) { freak_v4_word_length(0); return 99; }

    int64_t value = v4_probe_owner("A\xc3\xa9\xf0\x9f\x98\x80", 7);
    if (!strcmp(mode, "char-negative")) freak_v4_word_char_at(value, -1);
    else if (!strcmp(mode, "char-end")) freak_v4_word_char_at(value, 3);
    else if (!strcmp(mode, "char-overflow")) freak_v4_word_char_at(value, INT64_MAX);
    else if (!strcmp(mode, "slice-negative")) freak_v4_word_slice(value, -1, 2);
    else if (!strcmp(mode, "slice-reversed")) freak_v4_word_slice(value, 2, 1);
    else if (!strcmp(mode, "slice-end")) freak_v4_word_slice(value, 0, 4);
    else if (!strcmp(mode, "slice-overflow")) freak_v4_word_slice(value, 0, INT64_MAX);
    else if (!strcmp(mode, "substring-negative")) freak_v4_word_substring(value, 0, -1);
    else if (!strcmp(mode, "substring-start")) freak_v4_word_substring(value, 4, 0);
    else if (!strcmp(mode, "substring-count")) freak_v4_word_substring(value, 2, 2);
    else if (!strcmp(mode, "substring-overflow")) freak_v4_word_substring(value, 1, INT64_MAX);
    else return 98;
    return 99;
}

int main(int argc, char** argv) {
    if (argc > 1) return v4_probe_failure(argv[1]);
    assert(freak_llvm_owned_count == 0);
    int64_t owners[128];
    size_t used = 0;
#define OWN(expression) (owners[used++] = (expression))
    unsigned char source[] = {'A',0,0xc3,0xa9,0xe4,0xb8,0xad,0xf0,0x9f,0x98,0x80};
    int64_t value = OWN(v4_probe_owner(source, sizeof(source)));
    memset(source, 'x', sizeof(source));
    const unsigned char expected[] = {'A',0,0xc3,0xa9,0xe4,0xb8,0xad,0xf0,0x9f,0x98,0x80};
    v4_probe_bytes(value, expected, sizeof(expected));
    assert(freak_v4_word_length(value) == 5);
    int64_t clone = OWN(freak_v4_word_clone(value));
    assert(clone != value && freak_v4_word_equal(clone, value));
    /* Exercise clone after its original owner has actually been released. */
    size_t before_detached = freak_llvm_owned_count;
    int64_t original = v4_probe_owner(expected, sizeof(expected));
    int64_t detached = freak_v4_word_clone(original);
    freak_v4_word_drop(original);
    assert(freak_llvm_owned_count == before_detached + 1);
    v4_probe_bytes(detached, expected, sizeof(expected));
    freak_v4_word_drop(detached);
    assert(freak_llvm_owned_count == before_detached);
    int64_t empty = OWN(v4_probe_owner(NULL, 0));
    assert(freak_v4_word_length(empty) == 0);
    int64_t other_empty = OWN(freak_v4_word_clone(empty));
    assert(other_empty != empty && freak_v4_word_equal(empty, other_empty));

    static const size_t offsets[] = {0,1,2,4,7,11};
    for (int64_t index = 0; index < 5; index++) {
        int64_t scalar = OWN(freak_v4_word_char_at(value, index));
        v4_probe_bytes(scalar, expected + offsets[index], offsets[index+1] - offsets[index]);
        assert(freak_v4_word_length(scalar) == 1);
    }
    int64_t middle = OWN(freak_v4_word_slice(value, 1, 4));
    v4_probe_bytes(middle, expected + 1, 6);
    int64_t substring = OWN(freak_v4_word_substring(value, 1, 3));
    assert(freak_v4_word_equal(middle, substring));
    int64_t end_empty = OWN(freak_v4_word_slice(value, 5, 5));
    int64_t sub_empty = OWN(freak_v4_word_substring(value, 5, 0));
    assert(freak_v4_word_equal(end_empty, empty) && freak_v4_word_equal(sub_empty, empty));
    int64_t prefix = OWN(freak_v4_word_slice(value, 0, 2));
    int64_t suffix = OWN(freak_v4_word_substring(value, 3, 2));
    size_t before_observation = freak_llvm_owned_count;
    assert(freak_v4_word_starts_with(value, prefix));
    assert(freak_v4_word_ends_with(value, suffix));
    assert(freak_v4_word_contains(value, middle));
    assert(freak_v4_word_contains(value, empty));
    assert(freak_v4_word_starts_with(value, empty));
    assert(freak_v4_word_ends_with(value, empty));
    assert(!freak_v4_word_contains(prefix, value));
    assert(!freak_v4_word_starts_with(prefix, value));
    assert(!freak_v4_word_ends_with(prefix, value));
    assert(!freak_v4_word_equal(prefix, value));
    assert(freak_llvm_owned_count == before_observation);
    int64_t joined = OWN(freak_v4_word_concat(prefix, suffix));
    assert(freak_v4_word_length(joined) == 4 && freak_v4_word_bytes(joined) == 9);
    int64_t self_joined = OWN(freak_v4_word_concat(value, value));
    assert(freak_v4_word_length(self_joined) == 10 && freak_v4_word_bytes(self_joined) == 22);
    assert(freak_v4_word_equal(clone, value));

    /* The joined owner also survives dropping both borrowed inputs. */
    size_t before_joined = freak_llvm_owned_count;
    int64_t first = v4_probe_owner(expected, 2);
    int64_t second = v4_probe_owner(expected + 2, sizeof(expected) - 2);
    int64_t independent_join = freak_v4_word_concat(first, second);
    freak_v4_word_drop(first);
    freak_v4_word_drop(second);
    v4_probe_bytes(independent_join, expected, sizeof(expected));
    assert(freak_llvm_owned_count == before_joined + 1);
    freak_v4_word_drop(independent_join);
    assert(freak_llvm_owned_count == before_joined);

    const unsigned char combining[] = {'e',0xcc,0x81};
    int64_t combined = OWN(v4_probe_owner(combining, sizeof(combining)));
    assert(freak_v4_word_length(combined) == 2);
    const unsigned char boundaries[] = {
        0x7f, 0xc2,0x80, 0xdf,0xbf, 0xe0,0xa0,0x80, 0xed,0x9f,0xbf,
        0xee,0x80,0x80, 0xef,0xbf,0xbf, 0xf0,0x90,0x80,0x80, 0xf4,0x8f,0xbf,0xbf
    };
    int64_t limits = OWN(v4_probe_owner(boundaries, sizeof(boundaries)));
    assert(freak_v4_word_length(limits) == 9);
    int64_t minimum = OWN(freak_v4_word_from_int(INT64_MIN));
    int64_t maximum = OWN(freak_v4_word_from_int(INT64_MAX));
    v4_probe_bytes(minimum, "-9223372036854775808", 20);
    v4_probe_bytes(maximum, "9223372036854775807", 19);
    assert(freak_v4_word_to_int(minimum) == INT64_MIN);
    assert(freak_v4_word_to_int(maximum) == INT64_MAX);
    int64_t yes = OWN(freak_v4_word_from_bool(1));
    int64_t no = OWN(freak_v4_word_from_bool(0));
    int64_t also_yes = OWN(freak_v4_word_from_bool(-1));
    v4_probe_bytes(yes, "true", 4);
    v4_probe_bytes(no, "false", 5);
    assert(yes != also_yes && freak_v4_word_equal(yes, also_yes));
    int64_t number = OWN(freak_v4_word_from_num(-3.5));
    v4_probe_bytes(number, "-3.5", 4);
    int64_t lenient = OWN(v4_probe_owner("  -42junk", 9));
    assert(freak_v4_word_to_int(lenient) == -42);

    /* A move changes the compiler binding, not allocation ownership. */
    int64_t moved_from = OWN(v4_probe_owner("moved", 5));
    size_t moved_slot = used - 1;
    int64_t moved_to = moved_from;
    moved_from = 0;
    owners[moved_slot] = moved_from;
    assert(freak_llvm_owned_count == used);
    freak_v4_word_drop(moved_from);
    assert(freak_llvm_owned_count == used);
    v4_probe_bytes(moved_to, "moved", 5);
    freak_v4_word_drop(moved_to);
    assert(freak_llvm_owned_count == used - 1);

    before_observation = freak_llvm_owned_count;
    freak_v4_word_say(value);
    freak_v4_word_say_err(value);
    freak_v4_word_say(empty);
    assert(freak_llvm_owned_count == before_observation);
    while (used) freak_v4_word_drop(owners[--used]);
    assert(freak_llvm_owned_count == 0);
    freak_v4_word_drop(0);
    /* Repeated replacements stress actual owner registration and release. */
    for (int index = 0; index < 512; index++) {
        int64_t current = v4_probe_owner("a", 1);
        int64_t next = freak_v4_word_concat(current, current);
        freak_v4_word_drop(current);
        assert(freak_llvm_owned_count == 1);
        freak_v4_word_drop(next);
        assert(freak_llvm_owned_count == 0);
    }
    fputs("v4-word-runtime=ok\n", stdout);
    return 0;
}
