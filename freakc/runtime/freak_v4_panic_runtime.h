#pragma once

#include <stdint.h>

/* Compiler-private explicit panic=abort prerequisite, not the default unwind
   implementation or a foreign C ABI for FREAK words. Message is borrowed live
   owned W2 storage. Writes exactly PANIC: , its sized UTF-8 bytes, and newline
   to stderr, flushes, then aborts the process. Empty and embedded NUL are valid.
   Does not drop/clone the message, unwind, run deferred work, or invoke atexit.
   Invalid private owners/metadata use the existing named word-panic contract. */
_Noreturn void freak_v4_panic_abort(int64_t message);

/* Default panic=unwind for programs with no catch, eventually, sorties or
   user destructors, where unwinding has nothing observable to run: writes the
   same PANIC: report, flushes every output stream, and ends the process with
   status 101 without atexit handlers. No frames are unwound, so no unwind
   crosses a foreign boundary. Landing pads replace this with those features. */
#define FREAK_V4_PANIC_EXIT_STATUS 101
_Noreturn void freak_v4_panic_unwind(int64_t message);
