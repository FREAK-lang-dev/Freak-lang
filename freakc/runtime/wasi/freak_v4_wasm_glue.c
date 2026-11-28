/* FREAK V4 wasm glue: the few V3-runtime entry points native V4 code calls
 * that are host-specific in freak_runtime.c (console setup, argument capture,
 * say). The owned-word registry, freak_word_to_int/_to_num, the byte-word table and
 * the Shared<T> boxes are not copied here: src/compiler/v4/wasm_target.py
 * extracts them from freak_runtime.c and freak_llvm_runtime.c into one
 * translation unit that starts by including this file, so both targets
 * always run the same code. This file is not compiled on its own. */
#include "freak_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>

int freak_argc;
char **freak_argv;

void freak_enable_ansi(void) {}

/* Hooks the extracted registry calls; the C-backend ownership audit does
   not exist on this target. */
static void freak_c_append_untrack(void *pointer) { (void)pointer; }
static void freak_c_ownership_audit_release(void) {}
static void freak_word_foundation_audit_emit(void) {}

/* Like the native runtime, say flushes each line, so output written before
   an abort survives it. */
void freak_say(freak_word message) {
    fwrite(message.data, 1, message.length, stdout);
    fputc('\n', stdout);
    fflush(stdout);
}

void freak_say_err(freak_word message) {
    fwrite(message.data, 1, message.length, stderr);
    fputc('\n', stderr);
}

size_t freak_llvm_word_size(int64_t pointer);

void freak_llvm_say(int64_t message) {
    const char *text = (const char *)(uintptr_t)message;
    if (!text) return;
    fwrite(text, 1, freak_llvm_word_size(message), stdout);
    fputc('\n', stdout);
    fflush(stdout);
}

int64_t freak_llvm_process_args_count(void) { return freak_argc; }

void freak_llvm_setup_args(int64_t argc, int64_t argv) {
    freak_argc = (int)argc;
    freak_argv = (char **)(uintptr_t)argv;
}
