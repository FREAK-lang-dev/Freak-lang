#include "freak_v4_compiler_array_runtime.h"
#include "freak_v4_word_runtime.h"
#include "freak_runtime.h"

#include <inttypes.h>
#include <limits.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Default follows the dynamic legacy compiler pool. Tests inject 1024; the
   process memory guard remains global. No fixed 1024 production admission. */
#ifndef FREAK_V4_COMPILER_ARRAY_LIVE_LIMIT
#define FREAK_V4_COMPILER_ARRAY_LIVE_LIMIT 0
#endif
#ifndef FREAK_V4_COMPILER_ARRAY_CAPACITY_LIMIT
#define FREAK_V4_COMPILER_ARRAY_CAPACITY_LIMIT 0
#endif
#ifndef FREAK_V4_COMPILER_ARRAY_GENERATION_MAX
#define FREAK_V4_COMPILER_ARRAY_GENERATION_MAX UINT32_C(0x1fffffff)
#endif
_Static_assert(FREAK_V4_COMPILER_ARRAY_LIVE_LIMIT >= 0, "negative live quota");
_Static_assert(FREAK_V4_COMPILER_ARRAY_CAPACITY_LIMIT >= 0, "negative capacity limit");
_Static_assert(FREAK_V4_COMPILER_ARRAY_GENERATION_MAX > 0 &&
               FREAK_V4_COMPILER_ARRAY_GENERATION_MAX <= UINT32_C(0x1fffffff),
               "generation must fit the private ticket");

#define V4_ARRAY_DOMAIN UINT64_C(0x4000000000000000)
#define V4_ARRAY_DOMAIN_MASK UINT64_C(0xe000000000000000)
/* The pinned legacy LLVM pool accepts only slots0..1023, even when its wider
   31-bit generation overlaps this domain. Revalidate before changing that pool. */
#define V4_ARRAY_SLOT_BIAS UINT32_C(1024)

typedef struct {
    int64_t *cells;
    int64_t length;
    size_t capacity;
    int64_t next_free;
    uint32_t generation;
    bool active;
} v4_compiler_array;

static v4_compiler_array *v4_arrays = NULL;
static size_t v4_array_count = 0, v4_array_capacity = 0;
static int64_t v4_array_free = -1;
static uint64_t v4_array_live = 0;

static _Noreturn void v4_array_fail(const char *reason) {
    fprintf(stderr, "FREAK: V4 compiler arrays: %s\n", reason);
    fflush(stderr);
    exit(1);
}

static int64_t v4_array_ticket(size_t slot, uint32_t generation) {
    return (int64_t)(V4_ARRAY_DOMAIN | ((uint64_t)generation << 32) |
                     ((uint32_t)slot + V4_ARRAY_SLOT_BIAS));
}

static int64_t v4_array_slot(int64_t ticket) {
    uint64_t raw = (uint64_t)ticket;
    if ((raw & V4_ARRAY_DOMAIN_MASK) != V4_ARRAY_DOMAIN) return -1;
    uint32_t generation = (uint32_t)(raw >> 32) & UINT32_C(0x1fffffff);
    uint32_t encoded_slot = (uint32_t)raw;
    if (encoded_slot < V4_ARRAY_SLOT_BIAS) return -1;
    size_t slot = encoded_slot - V4_ARRAY_SLOT_BIAS;
    if (!generation || slot >= v4_array_count || !v4_arrays[slot].active ||
            v4_arrays[slot].generation != generation) return -1;
    return (int64_t)slot;
}

static bool v4_array_grow_table(void) {
    if (v4_array_count < v4_array_capacity) return true;
    uint64_t bound = UINT64_C(0x100000000) - V4_ARRAY_SLOT_BIAS;
    size_t allocation_bound = (size_t)PTRDIFF_MAX / sizeof(*v4_arrays);
    if (bound > allocation_bound) bound = allocation_bound;
    if (v4_array_capacity >= bound) return false;
    size_t next = v4_array_capacity == 0 ? 256 :
        v4_array_capacity > bound / 2 ? (size_t)bound : v4_array_capacity * 2;
    if (next > bound) next = (size_t)bound;
    if (next <= v4_array_capacity) return false;
    v4_compiler_array *staged = realloc(v4_arrays, next * sizeof(*staged));
    if (!staged) return false;
    memset(staged + v4_array_capacity, 0, (next - v4_array_capacity) * sizeof(*staged));
    v4_arrays = staged;
    v4_array_capacity = next;
    return true;
}

int64_t freak_v4_compiler_array_new(void) {
#if FREAK_V4_COMPILER_ARRAY_LIVE_LIMIT > 0
    if (v4_array_live >= (uint64_t)FREAK_V4_COMPILER_ARRAY_LIVE_LIMIT) return -1;
#endif
    size_t slot;
    if (v4_array_free >= 0) {
        slot = (size_t)v4_array_free;
        v4_array_free = v4_arrays[slot].next_free;
        ++v4_arrays[slot].generation;
    } else {
        if (!v4_array_grow_table()) return -1;
        slot = v4_array_count++;
        v4_arrays[slot].generation = 1;
    }
    v4_compiler_array *array = &v4_arrays[slot];
    array->cells = NULL;
    array->length = 0;
    array->capacity = 0;
    array->next_free = -1;
    array->active = true;
    ++v4_array_live;
    return v4_array_ticket(slot, array->generation);
}

static size_t v4_array_cell_bound(void) {
    size_t bound = (size_t)PTRDIFF_MAX / sizeof(int64_t);
    if ((uint64_t)bound > INT64_MAX) bound = (size_t)INT64_MAX;
#if FREAK_V4_COMPILER_ARRAY_CAPACITY_LIMIT > 0
    if ((uint64_t)FREAK_V4_COMPILER_ARRAY_CAPACITY_LIMIT < bound)
        bound = (size_t)FREAK_V4_COMPILER_ARRAY_CAPACITY_LIMIT;
#endif
    return bound;
}

static bool v4_array_reserve(v4_compiler_array *array) {
    if ((uint64_t)array->length < array->capacity) return true;
    size_t bound = v4_array_cell_bound();
    if ((uint64_t)array->length >= bound) return false;
    size_t next = array->capacity == 0 ? 64 :
        array->capacity > bound / 2 ? bound : array->capacity * 2;
    if (next > bound) next = bound;
    if (next <= array->capacity) return false;
    int64_t *staged = realloc(array->cells, next * sizeof(*staged));
    if (!staged) return false;
    array->cells = staged;
    array->capacity = next;
    return true;
}

/* Check raw registry metadata before word_bytes traverses UTF-8. Unknown
   owners still reach the existing Word panic without a pointer read. */
static bool v4_array_word_size(int64_t word, size_t *length) {
    size_t raw_bytes;
    if (freak_llvm_word_owned_size(word, &raw_bytes) &&
            (raw_bytes >= (size_t)PTRDIFF_MAX ||
             raw_bytes >= SIZE_MAX ||
             (uintptr_t)word > UINTPTR_MAX - raw_bytes)) return false;
    int64_t bytes = freak_v4_word_bytes(word);
    if ((uint64_t)bytes >= (uint64_t)PTRDIFF_MAX ||
            (uint64_t)bytes >= SIZE_MAX ||
            (uintptr_t)word > UINTPTR_MAX - (uint64_t)bytes) return false;
    (void)freak_v4_word_length(word);
    *length = (size_t)bytes;
    return true;
}

static int64_t v4_array_copy(const char *bytes, size_t length) {
    char *copy = malloc(length + 1);
    if (!copy) return 0;
    if (length) memcpy(copy, bytes, length);
    copy[length] = '\0';
    int64_t owner = freak_llvm_word_try_adopt_sized((int64_t)(uintptr_t)copy, length);
    if (!owner) free(copy);
    return owner;
}

static int64_t v4_array_clone(int64_t word) {
    size_t length;
    if (!v4_array_word_size(word, &length)) return 0;
    return v4_array_copy((const char *)(uintptr_t)word, length);
}

int64_t freak_v4_compiler_array_push_checked(int64_t ticket, int64_t word) {
    int64_t slot = v4_array_slot(ticket);
    if (slot < 0) return FREAK_V4_COMPILER_ARRAY_INVALID;
    v4_compiler_array *array = &v4_arrays[slot];
    if ((uint64_t)array->length >= v4_array_cell_bound()) return FREAK_V4_COMPILER_ARRAY_RESOURCE;
    int64_t copy = v4_array_clone(word);
    if (!copy) return FREAK_V4_COMPILER_ARRAY_RESOURCE;
    if (!v4_array_reserve(array)) {
        freak_v4_word_drop(copy);
        return FREAK_V4_COMPILER_ARRAY_RESOURCE;
    }
    array->cells[array->length++] = copy;
    return FREAK_V4_COMPILER_ARRAY_OK;
}

int64_t freak_v4_compiler_array_set_checked(int64_t ticket, int64_t index, int64_t word) {
    int64_t slot = v4_array_slot(ticket);
    if (slot < 0) return FREAK_V4_COMPILER_ARRAY_INVALID;
    v4_compiler_array *array = &v4_arrays[slot];
    if (index < 0 || index >= array->length) return FREAK_V4_COMPILER_ARRAY_INDEX;
    int64_t copy = v4_array_clone(word);
    if (!copy) return FREAK_V4_COMPILER_ARRAY_RESOURCE;
    int64_t replaced = array->cells[index];
    array->cells[index] = copy;
    freak_v4_word_drop(replaced);
    return FREAK_V4_COMPILER_ARRAY_OK;
}

int64_t freak_v4_compiler_array_get_checked(int64_t ticket, int64_t index, int64_t *out) {
    if (!out) v4_array_fail("invalid result slot");
    *out = 0;
    int64_t slot = v4_array_slot(ticket);
    if (slot < 0) return FREAK_V4_COMPILER_ARRAY_INVALID;
    v4_compiler_array *array = &v4_arrays[slot];
    if (index < 0 || index >= array->length) return FREAK_V4_COMPILER_ARRAY_INDEX;
    *out = v4_array_clone(array->cells[index]);
    return *out ? FREAK_V4_COMPILER_ARRAY_OK : FREAK_V4_COMPILER_ARRAY_RESOURCE;
}

int64_t freak_v4_compiler_array_len(int64_t ticket) {
    int64_t slot = v4_array_slot(ticket);
    return slot < 0 ? 0 : v4_arrays[slot].length;
}

void freak_v4_compiler_array_release(int64_t ticket) {
    int64_t slot = v4_array_slot(ticket);
    if (slot < 0) return;
    v4_compiler_array *array = &v4_arrays[slot];
    array->active = false;
    --v4_array_live;
    for (int64_t i = 0; i < array->length; ++i) freak_v4_word_drop(array->cells[i]);
    free(array->cells);
    array->cells = NULL;
    array->length = 0;
    array->capacity = 0;
    array->next_free = -1;
    if (array->generation < FREAK_V4_COMPILER_ARRAY_GENERATION_MAX) {
        array->next_free = v4_array_free;
        v4_array_free = slot;
    }
}

void freak_v4_compiler_array_shutdown(void) {
    for (size_t slot = 0; slot < v4_array_count; ++slot)
        if (v4_arrays[slot].active)
            freak_v4_compiler_array_release(v4_array_ticket(slot, v4_arrays[slot].generation));
}

int64_t freak_v4_compiler_array_join_checked(int64_t ticket, int64_t *out) {
    if (!out) v4_array_fail("invalid result slot");
    *out = 0;
    int64_t slot = v4_array_slot(ticket);
    if (slot < 0) return FREAK_V4_COMPILER_ARRAY_INVALID;
    v4_compiler_array *array = &v4_arrays[slot];
    size_t total = 0;
    for (int64_t i = 0; i < array->length; ++i) {
        size_t length;
        if (!v4_array_word_size(array->cells[i], &length) || length > (size_t)PTRDIFF_MAX - 1 - total)
            return FREAK_V4_COMPILER_ARRAY_RESOURCE;
        total += length;
    }
    char *joined = malloc(total + 1);
    if (!joined) return FREAK_V4_COMPILER_ARRAY_RESOURCE;
    size_t offset = 0;
    for (int64_t i = 0; i < array->length; ++i) {
        size_t length = (size_t)freak_v4_word_bytes(array->cells[i]);
        if (length) memcpy(joined + offset, (const void *)(uintptr_t)array->cells[i], length);
        offset += length;
    }
    joined[total] = '\0';
    int64_t owner = freak_llvm_word_try_adopt_sized((int64_t)(uintptr_t)joined, total);
    if (!owner) { free(joined); return FREAK_V4_COMPILER_ARRAY_RESOURCE; }
    freak_v4_compiler_array_release(ticket);
    *out = owner;
    return FREAK_V4_COMPILER_ARRAY_OK;
}

void freak_v4_compiler_array_push(int64_t ticket, int64_t word) {
    if (freak_v4_compiler_array_push_checked(ticket, word) == FREAK_V4_COMPILER_ARRAY_RESOURCE)
        v4_array_fail("out of memory growing array");
}

void freak_v4_compiler_array_set(int64_t ticket, int64_t index, int64_t word) {
    int64_t status = freak_v4_compiler_array_set_checked(ticket, index, word);
    if (status == FREAK_V4_COMPILER_ARRAY_RESOURCE) v4_array_fail("out of memory replacing array word");
    if (status == FREAK_V4_COMPILER_ARRAY_INDEX) {
        fprintf(stderr, "FREAK: array_set index %lld out of bounds (len %lld)\n",
                (long long)index, (long long)freak_v4_compiler_array_len(ticket));
        fflush(stderr);
        exit(1);
    }
}

int64_t freak_v4_compiler_array_get(int64_t ticket, int64_t index) {
    int64_t word;
    int64_t status = freak_v4_compiler_array_get_checked(ticket, index, &word);
    if (status == FREAK_V4_COMPILER_ARRAY_OK) return word;
    if (status == FREAK_V4_COMPILER_ARRAY_RESOURCE) v4_array_fail("out of memory copying array word");
    word = v4_array_copy("", 0);
    if (!word) v4_array_fail("out of memory copying array word");
    return word;
}

int64_t freak_v4_compiler_array_join(int64_t ticket) {
    int64_t word;
    int64_t status = freak_v4_compiler_array_join_checked(ticket, &word);
    if (status == FREAK_V4_COMPILER_ARRAY_OK) return word;
    if (status == FREAK_V4_COMPILER_ARRAY_RESOURCE) v4_array_fail("out of memory joining words");
    word = v4_array_copy("", 0);
    if (!word) v4_array_fail("out of memory joining words");
    return word;
}

int64_t freak_v4_compiler_array_snapshot_lines(int64_t word) {
    size_t length;
    if (!v4_array_word_size(word, &length)) return -1;
    int64_t ticket = freak_v4_compiler_array_new();
    if (ticket < 0) return -1;
    if (length == 0) return ticket;
    v4_compiler_array *array = &v4_arrays[v4_array_slot(ticket)];
    const char *bytes = (const char *)(uintptr_t)word;
    size_t start = 0;
    for (size_t i = 0;; ++i) {
        if (i == length || bytes[i] == '\n') {
            int64_t line = v4_array_copy(bytes + start, i - start);
            if (!line || !v4_array_reserve(array)) {
                freak_v4_word_drop(line);
                freak_v4_compiler_array_release(ticket);
                return -1;
            }
            array->cells[array->length++] = line;
            if (i == length) return ticket;
            start = i + 1;
        }
    }
}
