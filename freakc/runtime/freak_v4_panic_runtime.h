#pragma once

#include <stdint.h>

/* Compiler-private explicit panic=abort prerequisite, not the default unwind
   implementation or a foreign C ABI for FREAK words. Message is borrowed live
   owned W2 storage. Writes exactly PANIC: , its sized UTF-8 bytes, and newline
   to stderr, flushes, then aborts the process. Empty and embedded NUL are valid.
   Does not drop/clone the message, unwind, run deferred work, or invoke atexit.
   Invalid private owners/metadata use the existing named word-panic contract. */
_Noreturn void freak_v4_panic_abort(int64_t message);
