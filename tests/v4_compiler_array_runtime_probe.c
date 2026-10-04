/* The real C registry is included unchanged. Only allocations/adoption in the
   additive compiler-array implementation are intercepted below. Probe-only
   injection does not replace allocators in the production runtime. */
#include "freak_runtime.c"
#include "freak_v4_word_runtime.h"
#include "freak_v4_compiler_array_runtime.h"
#include <assert.h>

static size_t probe_allocations, probe_adoptions;
static size_t probe_fail_allocation, probe_fail_adoption;
static void *probe_raw[4096];
static size_t probe_raw_count;

static void probe_untrack(void *pointer) {
    if (!pointer) return;
    size_t i = 0;
    while (i < probe_raw_count && probe_raw[i] != pointer) ++i;
    assert(i < probe_raw_count);
    probe_raw[i] = probe_raw[--probe_raw_count];
}
static void probe_track(void *pointer) {
    if (!pointer) return;
    assert(probe_raw_count < sizeof(probe_raw) / sizeof(probe_raw[0]));
    probe_raw[probe_raw_count++] = pointer;
}
static void *probe_malloc(size_t size) {
    ++probe_allocations;
    if (probe_fail_allocation && probe_allocations == probe_fail_allocation) return NULL;
    void *pointer = malloc(size);
    probe_track(pointer);
    return pointer;
}
static void *probe_realloc(void *pointer, size_t size) {
    ++probe_allocations;
    if (probe_fail_allocation && probe_allocations == probe_fail_allocation) return NULL;
    /* Keep only the tracking index across realloc; do not inspect its released
       pointer value after success. realloc failure retains the previous owner. */
    size_t index = 0;
    bool had_pointer = pointer != NULL;
    if (had_pointer) {
        while (index < probe_raw_count && probe_raw[index] != pointer) ++index;
        assert(index < probe_raw_count);
    }
    void *grown = realloc(pointer, size);
    if (grown) {
        if (had_pointer) probe_raw[index] = grown;
        else probe_track(grown);
    }
    return grown;
}
static void probe_free(void *pointer) {
    probe_untrack(pointer);
    free(pointer);
}
static int64_t probe_adopt(int64_t pointer, size_t size) {
    ++probe_adoptions;
    if (probe_fail_adoption && probe_adoptions == probe_fail_adoption) return 0;
    int64_t result = freak_llvm_word_try_adopt_sized(pointer, size);
    if (result) probe_untrack((void *)(uintptr_t)pointer);
    return result;
}
#define malloc probe_malloc
#define realloc probe_realloc
#define free probe_free
#define freak_llvm_word_try_adopt_sized probe_adopt
#include "freak_v4_compiler_array_runtime.c"
#undef malloc
#undef realloc
#undef free
#undef freak_llvm_word_try_adopt_sized

static void probe_fault(size_t allocation, size_t adoption) {
    probe_allocations = probe_adoptions = 0;
    probe_fail_allocation = allocation;
    probe_fail_adoption = adoption;
}
static int64_t probe_word(const void *bytes, size_t length) {
    size_t before = freak_llvm_owned_count;
    int64_t owner = freak_v4_word_from_bytes((int64_t)(uintptr_t)bytes, (int64_t)length);
    assert(owner && freak_llvm_owned_count == before + 1);
    return owner;
}
static void probe_bytes(int64_t word, const void *bytes, size_t length) {
    assert(freak_v4_word_bytes(word) == (int64_t)length);
    assert(!length || !memcmp((const void *)(uintptr_t)word, bytes, length));
    assert(((const char *)(uintptr_t)word)[length] == '\0');
}
static void probe_clean(void) {
    assert(v4_array_live == 0);
    assert(freak_llvm_owned_count == 0);
    assert(freak_c_owned_word_count == 0);
    /* Retained table and terminal generation history intentionally survive. */
    assert(probe_raw_count == (v4_arrays ? 1u : 0u));
}

static void probe_ownership(void) {
    const unsigned char bytes[] = {'A', 0, 0xc3, 0xa9};
    int64_t input = probe_word(bytes, sizeof(bytes));
    int64_t array = freak_v4_compiler_array_new();
    assert(array != -1);
    assert(freak_v4_compiler_array_push_checked(array, input) == 1);
    int64_t stored = v4_arrays[v4_array_slot(array)].cells[0];
    assert(stored != input && freak_llvm_owned_count == 2);
    freak_v4_word_drop(input);
    int64_t first = freak_v4_compiler_array_get(array, 0);
    int64_t second = freak_v4_compiler_array_get(array, 0);
    assert(first != second && first != stored && second != stored);
    assert(freak_llvm_owned_count == 3);
    /* Borrowing this exact internal cell proves clone-before-replacement. */
    assert(freak_v4_compiler_array_set_checked(array, 0, stored) == 1);
    assert(v4_arrays[v4_array_slot(array)].cells[0] != stored);
    freak_v4_compiler_array_release(array);
    probe_bytes(first, bytes, sizeof(bytes));
    probe_bytes(second, bytes, sizeof(bytes));
    freak_v4_word_drop(first);
    freak_v4_word_drop(second);
    int64_t empty = freak_v4_compiler_array_get(-1, INT64_MAX);
    int64_t other = freak_v4_compiler_array_join(-1);
    assert(empty && other && empty != other);
    probe_bytes(empty, "", 0);
    probe_bytes(other, "", 0);
    freak_v4_word_drop(empty);
    freak_v4_word_drop(other);
    probe_clean();
    puts("compiler-array-ownership=ok");
}

static void probe_tickets(void) {
    int64_t array = freak_v4_compiler_array_new();
    /* Typed-V3 allows a numerically identical token. This is an explicit
       unsupported cross-ABI case, not a pretend decoder rejection. */
    uint32_t private_slot = (uint32_t)array;
    uint32_t private_generation = (uint32_t)((uint64_t)array >> 32);
    int64_t typed_v3_same_number = (int64_t)(((uint64_t)private_generation << 32) | private_slot);
    assert(typed_v3_same_number == array && private_slot >= 1024 &&
           private_generation <= UINT32_C(0x7fffffff));
    int64_t legacy = freak_array_new();
    int64_t builder = freak_word_builder_new();
    int64_t buffer = freak_byte_buffer_new();
    int64_t owner = probe_word("value", 5);
    int64_t foreign[] = {0, -1, 1, INT64_MIN, legacy, builder, buffer, owner,
                        (int64_t)UINT64_C(0x4000000100000000),
                        (int64_t)UINT64_C(0x7fffffff00000000)};
    for (size_t i = 0; i < sizeof(foreign) / sizeof(foreign[0]); ++i) {
        int64_t out = 117;
        assert(freak_v4_compiler_array_get_checked(foreign[i], 0, &out) == -1 && out == 0);
        assert(freak_v4_compiler_array_push_checked(foreign[i], 0) == -1);
        assert(freak_v4_compiler_array_set_checked(foreign[i], 0, 0) == -1);
        assert(freak_v4_compiler_array_len(foreign[i]) == 0);
        freak_v4_compiler_array_release(foreign[i]);
    }
    /* Legacy LLVM accepts31-bit generations but only1024 slots. Check every
       valid low-slot across the full-generation boundary families, including
       the exact formerly colliding0x40000001 generation. */
    const uint32_t generations[] = {1, UINT32_C(0x1fffffff), UINT32_C(0x20000001),
        UINT32_C(0x40000001), UINT32_C(0x60000001), UINT32_C(0x7fffffff)};
    for (size_t g = 0; g < sizeof(generations) / sizeof(generations[0]); ++g)
        for (uint32_t slot = 0; slot < 1024; ++slot) {
            int64_t legacy_full = (int64_t)(((uint64_t)generations[g] << 32) | slot);
            assert(v4_array_slot(legacy_full) < 0);
            assert(freak_v4_compiler_array_push_checked(legacy_full, 0) == -1);
        }
    freak_array_release(legacy);
    freak_word_builder_discard(builder);
    freak_byte_buffer_release(buffer);
    freak_v4_word_drop(owner);
    freak_v4_compiler_array_release(array);
    int64_t newer = freak_v4_compiler_array_new();
    assert(newer != -1 && newer != array);
    assert(freak_v4_compiler_array_push_checked(array, 0) == -1);
    freak_v4_compiler_array_release(array);
    assert(v4_array_live == 1);
    freak_v4_compiler_array_shutdown();
    int64_t after_shutdown = freak_v4_compiler_array_new();
    assert(after_shutdown != newer);
    assert(freak_v4_compiler_array_push_checked(newer, 0) == -1);
    freak_v4_compiler_array_release(after_shutdown);
    probe_clean();
    puts("compiler-array-tickets=ok");
}

static void probe_facts(void) {
    int64_t parent = freak_v4_compiler_array_new();
    int64_t child = freak_v4_compiler_array_new();
    freak_word encoded = freak_word_from_int(child);
    int64_t word = probe_word(encoded.data, encoded.length);
    freak_v4_compiler_array_push(parent, word);
    freak_v4_word_drop(word);
    freak_word_release_owned(&encoded);
    int64_t read = freak_v4_compiler_array_get(parent, 0);
    char *end = NULL;
    assert(strtoll((const char *)(uintptr_t)read, &end, 10) == child && end && !*end);
    freak_v4_word_drop(read);
    const int64_t facts[] = {-1, INT64_MIN, INT64_MAX};
    for (size_t i = 0; i < sizeof(facts) / sizeof(facts[0]); ++i) {
        encoded = freak_word_from_int(facts[i]);
        word = probe_word(encoded.data, encoded.length);
        freak_v4_compiler_array_push(parent, word);
        freak_v4_word_drop(word);
        freak_word_release_owned(&encoded);
        read = freak_v4_compiler_array_get(parent, (int64_t)i + 1);
        end = NULL;
        assert(strtoll((const char *)(uintptr_t)read, &end, 10) == facts[i] && end && !*end);
        freak_v4_word_drop(read);
    }
    freak_v4_compiler_array_release(parent);
    assert(v4_array_slot(child) >= 0 && v4_array_live == 1);
    freak_v4_compiler_array_release(child);
    probe_clean();
    puts("compiler-array-integer-facts=ok");
}

static void probe_snapshot_join(void) {
    const unsigned char bytes[] = {'a', '\r', '\n', '\n', 0, 0xc3, 0xa9, '\n'};
    int64_t source = probe_word(bytes, sizeof(bytes));
    int64_t array = freak_v4_compiler_array_snapshot_lines(source);
    assert(array != -1 && freak_v4_compiler_array_len(array) == 4);
    freak_v4_word_drop(source);
    const size_t offsets[] = {0, 3, 4, 8}, lengths[] = {2, 0, 3, 0};
    int64_t rebuilt = freak_v4_compiler_array_new();
    int64_t lf = probe_word("\n", 1);
    for (int64_t i = 0; i < 4; ++i) {
        int64_t word = freak_v4_compiler_array_get(array, i);
        probe_bytes(word, bytes + offsets[i], lengths[i]);
        freak_v4_compiler_array_push(rebuilt, word);
        if (i < 3) freak_v4_compiler_array_push(rebuilt, lf);
        freak_v4_word_drop(word);
    }
    freak_v4_word_drop(lf);
    int64_t roundtrip = freak_v4_compiler_array_join(rebuilt);
    probe_bytes(roundtrip, bytes, sizeof(bytes));
    freak_v4_word_drop(roundtrip);
    int64_t out = freak_v4_compiler_array_join(array);
    const unsigned char joined[] = {'a', '\r', 0, 0xc3, 0xa9};
    probe_bytes(out, joined, sizeof(joined));
    assert(v4_array_slot(array) < 0);
    freak_v4_word_drop(out);
    source = probe_word(NULL, 0);
    array = freak_v4_compiler_array_snapshot_lines(source);
    assert(array != -1 && freak_v4_compiler_array_len(array) == 0);
    out = freak_v4_compiler_array_join(array);
    assert(out != source && v4_array_slot(array) < 0);
    probe_bytes(out, "", 0);
    freak_v4_word_drop(out);
    freak_v4_word_drop(source);
    probe_clean();
    puts("compiler-array-snapshot-join=ok");
}

static void probe_failure_atomicity(void) {
    int64_t input = probe_word("word", 4);
    int64_t array = freak_v4_compiler_array_new();
    for (size_t allocation = 1; allocation <= 2; ++allocation) {
        size_t owners = freak_llvm_owned_count, raw = probe_raw_count;
        probe_fault(allocation, 0);
        assert(freak_v4_compiler_array_push_checked(array, input) == 0);
        assert(freak_v4_compiler_array_len(array) == 0 && freak_llvm_owned_count == owners);
        assert(probe_raw_count == raw && v4_array_live == 1);
    }
    probe_fault(0, 1);
    assert(freak_v4_compiler_array_push_checked(array, input) == 0);
    probe_fault(0, 0);
    freak_v4_compiler_array_push(array, input);
    int64_t stored = v4_arrays[v4_array_slot(array)].cells[0];
    assert(freak_v4_compiler_array_set_checked(array, -1, 0) == -2);
    int64_t index_out = 117;
    assert(freak_v4_compiler_array_get_checked(array, INT64_MAX, &index_out) == -2 && index_out == 0);
    /* Forged metadata on a genuine tiny owner must fail before any huge scan,
       allocation, input pointer read, or publication. Restore before drop. */
    freak_llvm_owned_word *metadata = freak_llvm_owned_find((void *)(uintptr_t)input, NULL);
    assert(metadata);
    size_t original_length = metadata->length;
    metadata->length = (size_t)PTRDIFF_MAX;
    assert(freak_v4_compiler_array_push_checked(array, input) == 0);
    assert(freak_v4_compiler_array_set_checked(array, 0, input) == 0);
    assert(freak_v4_compiler_array_snapshot_lines(input) == -1);
    metadata->length = original_length;
    metadata = freak_llvm_owned_find((void *)(uintptr_t)stored, NULL);
    original_length = metadata->length;
    metadata->length = (size_t)PTRDIFF_MAX;
    index_out = 117;
    assert(freak_v4_compiler_array_get_checked(array, 0, &index_out) == 0 && index_out == 0);
    index_out = 117;
    assert(freak_v4_compiler_array_join_checked(array, &index_out) == 0 && index_out == 0);
    assert(v4_arrays[v4_array_slot(array)].cells[0] == stored);
    metadata->length = original_length;
    for (int operation = 0; operation < 3; ++operation) {
        for (int failure = 0; failure < 2; ++failure) {
            int64_t out = 117;
            size_t owners = freak_llvm_owned_count, raw = probe_raw_count;
            probe_fault(failure ? 0 : 1, failure ? 1 : 0);
            int64_t status = operation == 0 ? freak_v4_compiler_array_set_checked(array, 0, input) :
                operation == 1 ? freak_v4_compiler_array_get_checked(array, 0, &out) :
                freak_v4_compiler_array_join_checked(array, &out);
            assert(status == 0 && (operation == 0 || out == 0));
            assert(v4_array_slot(array) >= 0 && freak_v4_compiler_array_len(array) == 1);
            assert(v4_arrays[v4_array_slot(array)].cells[0] == stored);
            assert(freak_llvm_owned_count == owners && probe_raw_count == raw);
        }
    }
    probe_fault(0, 0);
    for (int i = 1; i < 64; ++i) freak_v4_compiler_array_push(array, input);
    assert(freak_v4_compiler_array_len(array) == 64);
    size_t owners = freak_llvm_owned_count, raw = probe_raw_count;
    size_t capacity = v4_arrays[v4_array_slot(array)].capacity;
    probe_fault(2, 0);
    assert(freak_v4_compiler_array_push_checked(array, input) == 0);
    assert(freak_v4_compiler_array_len(array) == 64 && freak_llvm_owned_count == owners);
    assert(probe_raw_count == raw && v4_arrays[v4_array_slot(array)].capacity == capacity);
    probe_fault(0, 0);
    freak_v4_compiler_array_push(array, input);
    assert(freak_v4_compiler_array_len(array) == 65);
    freak_v4_compiler_array_release(array);
    int64_t lines = probe_word("a\nb\n", 4);
    for (int family = 0; family < 2; ++family) {
        for (size_t position = 1; position <= (family ? 3u : 4u); ++position) {
            owners = freak_llvm_owned_count; raw = probe_raw_count;
            probe_fault(family ? 0 : position, family ? position : 0);
            assert(freak_v4_compiler_array_snapshot_lines(lines) == -1);
            assert(v4_array_live == 0 && freak_llvm_owned_count == owners && probe_raw_count == raw);
            probe_fault(0, 0);
            int64_t recovered = freak_v4_compiler_array_snapshot_lines(lines);
            assert(recovered != -1 && freak_v4_compiler_array_len(recovered) == 3);
            freak_v4_compiler_array_release(recovered);
        }
    }
    freak_v4_word_drop(lines);
    freak_v4_word_drop(input);
    probe_clean();
    puts("compiler-array-rollback-recovery=ok");
}

static int probe_profile(const char *mode) {
    if (!strcmp(mode, "quota") || !strcmp(mode, "dynamic")) {
        size_t count = !strcmp(mode, "quota") ? 1024u : 100000u;
        int64_t *tickets = malloc(count * sizeof(*tickets));
        assert(tickets);
        for (size_t i = 0; i < count; ++i) { tickets[i] = freak_v4_compiler_array_new(); assert(tickets[i] != -1); }
        if (!strcmp(mode, "quota")) {
            assert(FREAK_V4_COMPILER_ARRAY_LIVE_LIMIT == 1024);
            assert(freak_v4_compiler_array_new() == -1 && v4_array_live == count);
        } else assert(FREAK_V4_COMPILER_ARRAY_LIVE_LIMIT == 0 && v4_array_live == count);
        int64_t stale = tickets[count / 2];
        freak_v4_compiler_array_release(stale);
        int64_t recovered = freak_v4_compiler_array_new();
        assert(recovered != -1 && recovered != stale && v4_array_slot(stale) < 0);
        for (size_t i = 0; i < count; ++i) freak_v4_compiler_array_release(tickets[i]);
        freak_v4_compiler_array_release(recovered);
        free(tickets);
        probe_clean();
        puts(!strcmp(mode, "quota") ? "compiler-array-quota1024=ok" : "compiler-array-dynamic100000=ok");
        return 0;
    }
    if (!strcmp(mode, "retire")) {
        assert(FREAK_V4_COMPILER_ARRAY_GENERATION_MAX == 3);
        int64_t old[3];
        for (int i = 0; i < 3; ++i) {
            old[i] = freak_v4_compiler_array_new();
            assert(old[i] != -1 && (uint32_t)old[i] == V4_ARRAY_SLOT_BIAS);
            for (int j = 0; j < i; ++j) assert(v4_array_slot(old[j]) < 0);
            freak_v4_compiler_array_release(old[i]);
        }
        int64_t next = freak_v4_compiler_array_new();
        assert(next != -1 && (uint32_t)next == V4_ARRAY_SLOT_BIAS + 1);
        for (int i = 0; i < 3; ++i) assert(v4_array_slot(old[i]) < 0);
        freak_v4_compiler_array_release(next);
        probe_clean();
        puts("compiler-array-generation-retirement=ok");
        return 0;
    }
    if (!strcmp(mode, "capacity")) {
        assert(FREAK_V4_COMPILER_ARRAY_CAPACITY_LIMIT == 2);
        int64_t array = freak_v4_compiler_array_new(), word = probe_word("x", 1);
        freak_v4_compiler_array_push(array, word);
        freak_v4_compiler_array_push(array, word);
        size_t owners = freak_llvm_owned_count, raw = probe_raw_count;
        assert(freak_v4_compiler_array_push_checked(array, word) == 0);
        assert(freak_v4_compiler_array_len(array) == 2 && owners == freak_llvm_owned_count && raw == probe_raw_count);
        int64_t lines = probe_word("a\nb\nc", 5);
        owners = freak_llvm_owned_count; raw = probe_raw_count;
        assert(freak_v4_compiler_array_snapshot_lines(lines) == -1);
        assert(v4_array_live == 1 && owners == freak_llvm_owned_count && raw == probe_raw_count);
        freak_v4_word_drop(lines);
        freak_v4_word_drop(word);
        freak_v4_compiler_array_release(array);
        probe_clean();
        puts("compiler-array-capacity-rollback=ok");
        return 0;
    }
    if (!strcmp(mode, "table-failure")) {
        probe_fault(1, 0);
        assert(freak_v4_compiler_array_new() == -1);
        assert(!v4_arrays && v4_array_count == 0 && v4_array_capacity == 0 && v4_array_live == 0);
        assert(probe_raw_count == 0);
        probe_fault(0, 0);
        int64_t tickets[256];
        for (size_t i = 0; i < 256; ++i) { tickets[i] = freak_v4_compiler_array_new(); assert(tickets[i] != -1); }
        assert(v4_array_count == 256 && v4_array_capacity == 256);
        probe_fault(1, 0);
        assert(freak_v4_compiler_array_new() == -1);
        assert(v4_array_live == 256 && v4_array_count == 256 && v4_array_capacity == 256);
        probe_fault(0, 0);
        int64_t recovered = freak_v4_compiler_array_new();
        assert(recovered != -1 && v4_array_live == 257);
        for (size_t i = 0; i < 256; ++i) freak_v4_compiler_array_release(tickets[i]);
        freak_v4_compiler_array_release(recovered);
        probe_clean();
        puts("compiler-array-table-rollback=ok");
        return 0;
    }
    return 98;
}

/* exit1 compatibility errors run actual cleanup before both registered owner
   audits. abort paths must skip this atexit hook, including its marker. */
static int64_t probe_exit_word;
static void probe_exit_cleanup(void) {
    probe_fault(0, 0);
    freak_v4_compiler_array_shutdown();
    freak_v4_word_drop(probe_exit_word);
    probe_clean();
}
static void probe_abort_marker(void) { fputs("unexpected-atexit\n", stderr); }
static int probe_fatal(const char *mode) {
    if (!strcmp(mode, "audit-word")) { (void)probe_word("leak", 4); return 0; }
    if (!strcmp(mode, "audit-c-word")) { (void)freak_word_from_int(117); return 0; }
    if (!strcmp(mode, "sanitizer-address")) {
        char *pointer = malloc(1);
        assert(pointer);
        free(pointer);
        return *(volatile unsigned char *)pointer;
    }
    if (!strcmp(mode, "sanitizer-undefined")) {
        volatile int64_t max = INT64_MAX;
        volatile int64_t one = 1;
        return (int)(max + one);
    }
    if (!strcmp(mode, "fatal-null-out")) { freak_v4_compiler_array_get_checked(-1, 0, NULL); return 99; }
    int64_t array = freak_v4_compiler_array_new();
    assert(array != -1);
    if (!strncmp(mode, "fatal-word-", 11)) {
        int64_t word = 0;
        if (!strcmp(mode, "fatal-word-foreign")) word = (int64_t)(uintptr_t)"foreign";
        if (!strcmp(mode, "fatal-word-released")) { word = probe_word("released", 8); freak_v4_word_drop(word); }
        if (!strcmp(mode, "fatal-word-utf8")) {
            word = probe_word("a", 1);
            *(unsigned char *)(uintptr_t)word = 0x80;
        }
        assert(atexit(probe_abort_marker) == 0);
        freak_v4_compiler_array_push(array, word);
        return 99;
    }
    probe_exit_word = probe_word("word", 4);
    assert(atexit(probe_exit_cleanup) == 0);
    if (!strcmp(mode, "fatal-index-negative")) freak_v4_compiler_array_set(array, -1, probe_exit_word);
    else if (!strcmp(mode, "fatal-index-end")) freak_v4_compiler_array_set(array, 0, probe_exit_word);
    else if (!strcmp(mode, "fatal-push-resource")) { probe_fault(1, 0); freak_v4_compiler_array_push(array, probe_exit_word); }
    else {
        freak_v4_compiler_array_push(array, probe_exit_word);
        probe_fault(1, 0);
        if (!strcmp(mode, "fatal-set-resource")) freak_v4_compiler_array_set(array, 0, probe_exit_word);
        else if (!strcmp(mode, "fatal-get-resource")) (void)freak_v4_compiler_array_get(array, 0);
        else if (!strcmp(mode, "fatal-join-resource")) (void)freak_v4_compiler_array_join(array);
        else return 98;
    }
    return 99;
}

int main(int argc, char **argv) {
#ifdef _WIN32
    _set_abort_behavior(0, _WRITE_ABORT_MSG | _CALL_REPORTFAULT);
#endif
    const char *mode = argc > 1 ? argv[1] : "normal";
    if (!strncmp(mode, "fatal-", 6) || !strncmp(mode, "audit-", 6) || !strncmp(mode, "sanitizer-", 10))
        return probe_fatal(mode);
    if (strcmp(mode, "normal")) return probe_profile(mode);
    probe_ownership();
    probe_tickets();
    probe_facts();
    probe_snapshot_join();
    probe_failure_atomicity();
    probe_clean();
    return 0;
}
