#pragma once

#include <stdint.h>

/* Compiler-private owned-word storage prerequisite, not List<T> or a public C
   ABI. Tickets are copyable integer identities in a separate encoded domain.
   A valid cell owns one registered V4 word. Inputs borrow; stores copy; gets
   return a fresh owner. Release drops cells, never nested integer tickets.
   The pool is single-threaded and does not support reentrant allocator hooks.

   Checked operations return OK, RESOURCE, INVALID or INDEX. A required output
   pointer names unowned writable storage disjoint from runtime/input storage; failures
   write zero (a cleanup sentinel, not
   a word). No ticket/cell/length mutation is published on checked store failure.
   new/snapshot return -1 on allocation or optional live-quota exhaustion.

   Legacy-shaped wrappers preserve invalid-ticket no-op/len0 and live OOB-set
   exit1. get/join return owning empty on invalid input, deliberately replacing
   the legacy borrowed empty. Allocation failure is named exit1, not a usable
   zero word. join consumes its ticket only on success. */
enum {
    FREAK_V4_COMPILER_ARRAY_OK = 1,
    FREAK_V4_COMPILER_ARRAY_RESOURCE = 0,
    FREAK_V4_COMPILER_ARRAY_INVALID = -1,
    FREAK_V4_COMPILER_ARRAY_INDEX = -2
};

int64_t freak_v4_compiler_array_new(void);
int64_t freak_v4_compiler_array_len(int64_t ticket);
void freak_v4_compiler_array_release(int64_t ticket);
/* Drops all live cells without resetting generations or resurrecting tickets.
   The reusable table/retired-slot history remains until process exit. */
void freak_v4_compiler_array_shutdown(void);

int64_t freak_v4_compiler_array_push_checked(int64_t ticket, int64_t borrowed_word);
int64_t freak_v4_compiler_array_set_checked(int64_t ticket, int64_t index, int64_t borrowed_word);
int64_t freak_v4_compiler_array_get_checked(int64_t ticket, int64_t index, int64_t *out_word);
int64_t freak_v4_compiler_array_join_checked(int64_t ticket, int64_t *out_word);

void freak_v4_compiler_array_push(int64_t ticket, int64_t borrowed_word);
void freak_v4_compiler_array_set(int64_t ticket, int64_t index, int64_t borrowed_word);
int64_t freak_v4_compiler_array_get(int64_t ticket, int64_t index);
int64_t freak_v4_compiler_array_join(int64_t ticket);
/* LF split: empty input has zero rows; CR, NUL, blank/trailing rows survive.
   Borrows source; partial construction releases every staged owner/ticket. */
int64_t freak_v4_compiler_array_snapshot_lines(int64_t borrowed_word);
