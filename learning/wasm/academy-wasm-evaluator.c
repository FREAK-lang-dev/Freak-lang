// First FREAK Academy WASM-backed evaluator.
//
// Scope: the `hello-freak` lesson only. This module intentionally implements
// a tiny browser-safe evaluator for one `say "..."` program so the worker can
// use a real WASM artifact before the full compiler-owned evaluator exists.

#include <stdint.h>

#define ACADEMY_WORKER_PROTOCOL_VERSION 1
#define ACADEMY_WASM_EVALUATOR_VERSION 1
#define ACADEMY_SUPPORTED_LESSON_COUNT 1

#define STATUS_PARSES 1
#define STATUS_COMPILES 2
#define STATUS_RUNS 4
#define STATUS_OUTPUT_MATCHES 8

#define INPUT_CAPACITY 8192
#define STDOUT_CAPACITY 1024
#define MESSAGE_CAPACITY 256

static unsigned char academy_input[INPUT_CAPACITY];
static unsigned char academy_stdout[STDOUT_CAPACITY];
static unsigned char academy_message[MESSAGE_CAPACITY];
static int academy_stdout_len = 0;
static int academy_message_len = 0;

static int is_space(unsigned char ch) {
    return ch == ' ' || ch == '\t' || ch == '\r' || ch == '\n';
}

static int is_ident(unsigned char ch) {
    return (ch >= 'A' && ch <= 'Z') ||
           (ch >= 'a' && ch <= 'z') ||
           (ch >= '0' && ch <= '9') ||
           ch == '_';
}

static int bytes_equal(const unsigned char *left, const unsigned char *right, int len) {
    for (int i = 0; i < len; i += 1) {
        if (left[i] != right[i]) {
            return 0;
        }
    }
    return 1;
}

static void set_message(const char *message) {
    int i = 0;
    while (message[i] != 0 && i < MESSAGE_CAPACITY) {
        academy_message[i] = (unsigned char)message[i];
        i += 1;
    }
    academy_message_len = i;
}

static int skip_trivia(int index, int len) {
    while (index < len) {
        if (is_space(academy_input[index])) {
            index += 1;
            continue;
        }
        if (index + 1 < len && academy_input[index] == '-' && academy_input[index + 1] == '-') {
            index += 2;
            while (index < len && academy_input[index] != '\n') {
                index += 1;
            }
            continue;
        }
        break;
    }
    return index;
}

static int parse_say_string_program(int len) {
    int index = skip_trivia(0, len);
    academy_stdout_len = 0;
    academy_message_len = 0;

    if (index + 3 > len ||
        academy_input[index] != 's' ||
        academy_input[index + 1] != 'a' ||
        academy_input[index + 2] != 'y') {
        set_message("expected say statement");
        return 0;
    }
    if (index + 3 < len && is_ident(academy_input[index + 3])) {
        set_message("expected say keyword boundary");
        return 0;
    }
    index += 3;
    index = skip_trivia(index, len);

    if (index >= len || academy_input[index] != '"') {
        set_message("expected word literal after say");
        return 0;
    }
    index += 1;

    while (index < len) {
        unsigned char ch = academy_input[index];
        if (ch == '"') {
            index += 1;
            index = skip_trivia(index, len);
            if (index != len) {
                set_message("expected end of source after say statement");
                return 0;
            }
            if (academy_stdout_len + 1 > STDOUT_CAPACITY) {
                set_message("program output exceeds WASM stdout capacity");
                return 0;
            }
            academy_stdout[academy_stdout_len] = '\n';
            academy_stdout_len += 1;
            return 1;
        }
        if (ch == '\\') {
            index += 1;
            if (index >= len) {
                set_message("unterminated escape in word literal");
                return 0;
            }
            ch = academy_input[index];
            if (ch == 'n') {
                ch = '\n';
            } else if (ch == 'r') {
                ch = '\r';
            } else if (ch == 't') {
                ch = '\t';
            } else if (ch == '"' || ch == '\\') {
                // Keep the escaped character as-is.
            } else {
                // Match the current V3 MVP browser subset: unknown escapes
                // resolve to the escaped character.
            }
        }
        if (academy_stdout_len >= STDOUT_CAPACITY) {
            set_message("program output exceeds WASM stdout capacity");
            return 0;
        }
        academy_stdout[academy_stdout_len] = ch;
        academy_stdout_len += 1;
        index += 1;
    }

    set_message("unterminated word literal");
    return 0;
}

__attribute__((visibility("default")))
int academy_protocol_version(void) {
    return ACADEMY_WORKER_PROTOCOL_VERSION;
}

__attribute__((visibility("default")))
int academy_wasm_evaluator_version(void) {
    return ACADEMY_WASM_EVALUATOR_VERSION;
}

__attribute__((visibility("default")))
int academy_supported_lesson_count(void) {
    return ACADEMY_SUPPORTED_LESSON_COUNT;
}

__attribute__((visibility("default")))
int academy_input_offset(void) {
    return (int)(uintptr_t)academy_input;
}

__attribute__((visibility("default")))
int academy_input_capacity(void) {
    return INPUT_CAPACITY;
}

__attribute__((visibility("default")))
int academy_last_stdout_offset(void) {
    return (int)(uintptr_t)academy_stdout;
}

__attribute__((visibility("default")))
int academy_last_stdout_length(void) {
    return academy_stdout_len;
}

__attribute__((visibility("default")))
int academy_last_message_offset(void) {
    return (int)(uintptr_t)academy_message;
}

__attribute__((visibility("default")))
int academy_last_message_length(void) {
    return academy_message_len;
}

__attribute__((visibility("default")))
int academy_evaluate_hello_freak(int source_len) {
    static const unsigned char expected[] = "Hello, FREAK Academy!\n";
    int status = 0;

    academy_stdout_len = 0;
    academy_message_len = 0;

    if (source_len < 0 || source_len > INPUT_CAPACITY) {
        set_message("source exceeds WASM input capacity");
        return status;
    }

    if (!parse_say_string_program(source_len)) {
        return status;
    }

    status |= STATUS_PARSES;
    status |= STATUS_COMPILES;
    status |= STATUS_RUNS;

    if (academy_stdout_len == (int)(sizeof(expected) - 1) &&
        bytes_equal(academy_stdout, expected, academy_stdout_len)) {
        status |= STATUS_OUTPUT_MATCHES;
    }

    return status;
}
