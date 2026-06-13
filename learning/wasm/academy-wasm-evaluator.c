// First FREAK Academy WASM-backed evaluator.
//
// Scope: the `hello-freak` and `variables` lessons. This module intentionally
// implements a tiny browser-safe evaluator for the first Academy basics
// exercises so the worker can use a real WASM artifact before the full
// compiler-owned evaluator exists.

#include <stdint.h>

#define ACADEMY_WORKER_PROTOCOL_VERSION 1
#define ACADEMY_WASM_EVALUATOR_VERSION 1
#define ACADEMY_SUPPORTED_LESSON_COUNT 2

#define STATUS_PARSES 1
#define STATUS_COMPILES 2
#define STATUS_RUNS 4
#define STATUS_OUTPUT_MATCHES 8

#define INPUT_CAPACITY 8192
#define STDOUT_CAPACITY 1024
#define MESSAGE_CAPACITY 256
#define IDENT_CAPACITY 64

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

static int is_ident_start(unsigned char ch) {
    return (ch >= 'A' && ch <= 'Z') ||
           (ch >= 'a' && ch <= 'z') ||
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

static int names_equal(const unsigned char *left, int left_len, const unsigned char *right, int right_len) {
    if (left_len != right_len) {
        return 0;
    }
    return bytes_equal(left, right, left_len);
}

static int match_keyword(int index, int len, const char *keyword, int keyword_len) {
    if (index + keyword_len > len) {
        return 0;
    }
    for (int i = 0; i < keyword_len; i += 1) {
        if (academy_input[index + i] != (unsigned char)keyword[i]) {
            return 0;
        }
    }
    if (index + keyword_len < len && is_ident(academy_input[index + keyword_len])) {
        return 0;
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

static int parse_identifier(int *index, int len, unsigned char *name, int *name_len, const char *label) {
    int current = skip_trivia(*index, len);
    int start = current;

    if (current >= len || !is_ident_start(academy_input[current])) {
        set_message(label);
        return 0;
    }

    current += 1;
    while (current < len && is_ident(academy_input[current])) {
        current += 1;
    }

    *name_len = current - start;
    if (*name_len >= IDENT_CAPACITY) {
        set_message("identifier exceeds WASM evaluator capacity");
        return 0;
    }
    for (int i = 0; i < *name_len; i += 1) {
        name[i] = academy_input[start + i];
    }

    *index = current;
    return 1;
}

static int parse_int_literal(int *index, int len, int *value) {
    int current = skip_trivia(*index, len);
    int parsed = 0;
    int sign = 1;
    int result = 0;

    if (current < len && academy_input[current] == '-') {
        sign = -1;
        current += 1;
    }

    while (current < len && academy_input[current] >= '0' && academy_input[current] <= '9') {
        parsed = 1;
        result = result * 10 + (academy_input[current] - '0');
        current += 1;
    }

    if (!parsed) {
        return 0;
    }

    *value = result * sign;
    *index = current;
    return 1;
}

static int parse_int_primary(
    int *index,
    int len,
    int has_var,
    const unsigned char *var_name,
    int var_name_len,
    int var_value,
    int *value
) {
    int current = skip_trivia(*index, len);
    if (parse_int_literal(&current, len, value)) {
        *index = current;
        return 1;
    }

    unsigned char name[IDENT_CAPACITY];
    int name_len = 0;
    current = *index;
    if (!parse_identifier(&current, len, name, &name_len, "expected int expression")) {
        return 0;
    }
    if (!has_var || !names_equal(name, name_len, var_name, var_name_len)) {
        set_message("unknown symbol in WASM evaluator");
        return 0;
    }

    *value = var_value;
    *index = current;
    return 1;
}

static int parse_int_expression(
    int *index,
    int len,
    int has_var,
    const unsigned char *var_name,
    int var_name_len,
    int var_value,
    int *value
) {
    if (!parse_int_primary(index, len, has_var, var_name, var_name_len, var_value, value)) {
        return 0;
    }

    while (1) {
        int current = skip_trivia(*index, len);
        unsigned char op = 0;
        int rhs = 0;
        if (current < len && (academy_input[current] == '+' || academy_input[current] == '-')) {
            op = academy_input[current];
            current += 1;
        } else {
            return 1;
        }
        if (!parse_int_primary(&current, len, has_var, var_name, var_name_len, var_value, &rhs)) {
            return 0;
        }
        if (op == '+') {
            *value += rhs;
        } else {
            *value -= rhs;
        }
        *index = current;
    }
}

static int append_output_byte(unsigned char ch) {
    if (academy_stdout_len >= STDOUT_CAPACITY) {
        set_message("program output exceeds WASM stdout capacity");
        return 0;
    }
    academy_stdout[academy_stdout_len] = ch;
    academy_stdout_len += 1;
    return 1;
}

static int append_output_newline(void) {
    return append_output_byte('\n');
}

static int append_output_int(int value) {
    unsigned char digits[16];
    int digit_count = 0;
    int current = value;

    if (value == 0) {
        return append_output_byte('0');
    }
    if (value < 0) {
        if (!append_output_byte('-')) {
            return 0;
        }
        current = -current;
    }

    while (current > 0 && digit_count < 16) {
        digits[digit_count] = (unsigned char)('0' + (current % 10));
        current /= 10;
        digit_count += 1;
    }
    for (int i = digit_count - 1; i >= 0; i -= 1) {
        if (!append_output_byte(digits[i])) {
            return 0;
        }
    }
    return 1;
}

static int parse_word_literal_to_stdout(int *index, int len) {
    int current = skip_trivia(*index, len);
    if (current >= len || academy_input[current] != '"') {
        set_message("expected word literal");
        return 0;
    }
    current += 1;

    while (current < len) {
        unsigned char ch = academy_input[current];
        if (ch == '"') {
            *index = current + 1;
            return 1;
        }
        if (ch == '\\') {
            current += 1;
            if (current >= len) {
                set_message("unterminated escape in word literal");
                return 0;
            }
            ch = academy_input[current];
            if (ch == 'n') {
                ch = '\n';
            } else if (ch == 'r') {
                ch = '\r';
            } else if (ch == 't') {
                ch = '\t';
            }
        }
        if (!append_output_byte(ch)) {
            return 0;
        }
        current += 1;
    }

    set_message("unterminated word literal");
    return 0;
}

static int parse_say_value_statement(
    int *index,
    int len,
    int has_var,
    const unsigned char *var_name,
    int var_name_len,
    int var_value
) {
    int current = skip_trivia(*index, len);
    int int_value = 0;

    if (!match_keyword(current, len, "say", 3)) {
        set_message("expected say statement");
        return 0;
    }
    current += 3;
    current = skip_trivia(current, len);

    if (current < len && academy_input[current] == '"') {
        if (!parse_word_literal_to_stdout(&current, len)) {
            return 0;
        }
    } else {
        if (!parse_int_expression(&current, len, has_var, var_name, var_name_len, var_value, &int_value)) {
            return 0;
        }
        if (!append_output_int(int_value)) {
            return 0;
        }
    }

    if (!append_output_newline()) {
        return 0;
    }
    *index = current;
    return 1;
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

static int parse_variables_program(int len) {
    unsigned char var_name[IDENT_CAPACITY];
    unsigned char type_name[IDENT_CAPACITY];
    int var_name_len = 0;
    int type_name_len = 0;
    int var_value = 0;
    int has_var = 0;
    int index = skip_trivia(0, len);

    academy_stdout_len = 0;
    academy_message_len = 0;

    if (match_keyword(index, len, "pilot", 5)) {
        index += 5;
        if (!parse_identifier(&index, len, var_name, &var_name_len, "expected pilot name")) {
            return 0;
        }
        index = skip_trivia(index, len);
        if (index < len && academy_input[index] == ':') {
            index += 1;
            if (!parse_identifier(&index, len, type_name, &type_name_len, "expected type annotation")) {
                return 0;
            }
            (void)type_name;
            (void)type_name_len;
            index = skip_trivia(index, len);
        }
        if (index >= len || academy_input[index] != '=') {
            set_message("expected '=' in pilot declaration");
            return 0;
        }
        index += 1;
        if (!parse_int_expression(&index, len, 0, var_name, var_name_len, 0, &var_value)) {
            return 0;
        }
        has_var = 1;
    }

    if (!parse_say_value_statement(&index, len, has_var, var_name, var_name_len, var_value)) {
        return 0;
    }
    index = skip_trivia(index, len);
    if (index != len) {
        set_message("expected end of source after variables lesson program");
        return 0;
    }
    return 1;
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

__attribute__((visibility("default")))
int academy_evaluate_variables(int source_len) {
    static const unsigned char expected[] = "100\n";
    int status = 0;

    academy_stdout_len = 0;
    academy_message_len = 0;

    if (source_len < 0 || source_len > INPUT_CAPACITY) {
        set_message("source exceeds WASM input capacity");
        return status;
    }

    if (!parse_variables_program(source_len)) {
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
