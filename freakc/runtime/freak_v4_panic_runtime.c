#include "freak_v4_panic_runtime.h"
#include "freak_v4_word_runtime.h"
#include "freak_runtime.h"

#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif

static _Noreturn void freak_v4_panic_word_fail(const char *reason) {
    fprintf(stderr, "FREAK: V4 word panic: %s\n", reason);
    fflush(stderr);
    abort();
}

static void freak_v4_panic_report(int64_t message) {
#ifdef _WIN32
    /* Binary mode preserves the sized payload instead of translating its
       newline bytes. */
    (void)_setmode(_fileno(stderr), _O_BINARY);
#endif
    if (!message) freak_v4_panic_word_fail("word value has been consumed");
    size_t length = 0;
    if (!freak_llvm_word_owned_size(message, &length))
        freak_v4_panic_word_fail("word value is not live owned storage");
    /* Registry membership never permits impossible sizes or the legacy
       unknown-pointer/strlen fallback. Check metadata before a pointer read. */
    if (length >= SIZE_MAX || (uintmax_t)length > (uintmax_t)INT64_MAX)
        freak_v4_panic_word_fail("byte length overflow");
    /* Keep the established strict UTF-8 scalar contract, including U+0000.
       Validation borrows the word and performs no ownership transfer. */
    (void)freak_v4_word_length(message);
    (void)fwrite("PANIC: ", 1, 7, stderr);
    if (length) (void)fwrite((const void *)(uintptr_t)message, 1, length, stderr);
    (void)fputc('\n', stderr);
    (void)fflush(stderr);
}

_Noreturn void freak_v4_panic_abort(int64_t message) {
#ifdef _WIN32
    /* Abort is intentional, deterministic and noninteractive. */
    _set_abort_behavior(0, _WRITE_ABORT_MSG | _CALL_REPORTFAULT);
#endif
    freak_v4_panic_report(message);
    abort();
}

_Noreturn void freak_v4_panic_unwind(int64_t message) {
    freak_v4_panic_report(message);
    /* The main sortie ends as panicked. Output written before the panic is
       kept; atexit handlers and leak checks do not run, as with abort. */
    (void)fflush(NULL);
    _Exit(FREAK_V4_PANIC_EXIT_STATUS);
}
