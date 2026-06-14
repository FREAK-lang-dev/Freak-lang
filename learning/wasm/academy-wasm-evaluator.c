// First FREAK Academy WASM-backed evaluator.
//
// Scope: the first six basics lessons. This module intentionally implements a
// tiny browser-safe evaluator for the first Academy basics exercises so the
// worker can use a real WASM artifact before the full compiler-owned evaluator
// exists.

#include <stdint.h>

#define ACADEMY_WORKER_PROTOCOL_VERSION 1
#define ACADEMY_WASM_EVALUATOR_VERSION 1
#define ACADEMY_SUPPORTED_LESSON_COUNT 6

#define STATUS_PARSES 1
#define STATUS_COMPILES 2
#define STATUS_RUNS 4
#define STATUS_OUTPUT_MATCHES 8

#define INPUT_CAPACITY 8192
#define STDOUT_CAPACITY 1024
#define MESSAGE_CAPACITY 256
#define IDENT_CAPACITY 64
#define VAR_CAPACITY 8
#define WORD_STORAGE_CAPACITY 2048
#define VALUE_INT 1
#define VALUE_WORD 2
#define CMP_EQ 1
#define CMP_NE 2
#define CMP_GT 3
#define CMP_GE 4
#define CMP_LT 5
#define CMP_LE 6

static unsigned char academy_input[INPUT_CAPACITY];
static unsigned char academy_stdout[STDOUT_CAPACITY];
static unsigned char academy_message[MESSAGE_CAPACITY];
static unsigned char academy_word_storage[WORD_STORAGE_CAPACITY];
static int academy_stdout_len = 0;
static int academy_message_len = 0;
static int academy_word_storage_len = 0;
static int academy_output_enabled = 1;
static int var_count = 0;
static unsigned char var_names[VAR_CAPACITY][IDENT_CAPACITY];
static int var_name_lens[VAR_CAPACITY];
static int var_types[VAR_CAPACITY];
static int var_int_values[VAR_CAPACITY];
static int var_word_offsets[VAR_CAPACITY];
static int var_word_lens[VAR_CAPACITY];

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

static void reset_eval_state(void) {
    academy_stdout_len = 0;
    academy_message_len = 0;
    academy_word_storage_len = 0;
    academy_output_enabled = 1;
    var_count = 0;
}

static int find_var(const unsigned char *name, int name_len) {
    for (int i = var_count - 1; i >= 0; i -= 1) {
        if (names_equal(name, name_len, var_names[i], var_name_lens[i])) {
            return i;
        }
    }
    return -1;
}

static int declare_var(const unsigned char *name, int name_len) {
    if (name_len <= 0 || name_len >= IDENT_CAPACITY) {
        set_message("invalid variable name");
        return -1;
    }
    if (var_count >= VAR_CAPACITY) {
        set_message("too many variables for WASM evaluator");
        return -1;
    }
    if (find_var(name, name_len) >= 0) {
        set_message("duplicate variable in WASM evaluator");
        return -1;
    }

    int slot = var_count;
    for (int i = 0; i < name_len; i += 1) {
        var_names[slot][i] = name[i];
    }
    var_name_lens[slot] = name_len;
    var_types[slot] = 0;
    var_int_values[slot] = 0;
    var_word_offsets[slot] = 0;
    var_word_lens[slot] = 0;
    var_count += 1;
    return slot;
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

static int parse_int_primary(int *index, int len, int *value) {
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
    int slot = find_var(name, name_len);
    if (slot < 0) {
        set_message("unknown symbol in WASM evaluator");
        return 0;
    }
    if (var_types[slot] != VALUE_INT) {
        set_message("expected int value in WASM evaluator");
        return 0;
    }

    *value = var_int_values[slot];
    *index = current;
    return 1;
}

static int parse_int_term(int *index, int len, int *value) {
    if (!parse_int_primary(index, len, value)) {
        return 0;
    }

    while (1) {
        int current = skip_trivia(*index, len);
        unsigned char op = 0;
        int rhs = 0;
        if (current < len && (academy_input[current] == '*' || academy_input[current] == '/')) {
            op = academy_input[current];
            current += 1;
        } else {
            return 1;
        }
        if (!parse_int_primary(&current, len, &rhs)) {
            return 0;
        }
        if (op == '*') {
            *value *= rhs;
        } else {
            if (rhs == 0) {
                set_message("division by zero in WASM evaluator");
                return 0;
            }
            *value /= rhs;
        }
        *index = current;
    }
}

static int parse_int_expression(int *index, int len, int *value) {
    if (!parse_int_term(index, len, value)) {
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
        if (!parse_int_term(&current, len, &rhs)) {
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

static int parse_comparison_operator(int *index, int len, int *op) {
    int current = skip_trivia(*index, len);
    if (current + 1 < len && academy_input[current] == '=' && academy_input[current + 1] == '=') {
        *op = CMP_EQ;
        *index = current + 2;
        return 1;
    }
    if (current + 1 < len && academy_input[current] == '!' && academy_input[current + 1] == '=') {
        *op = CMP_NE;
        *index = current + 2;
        return 1;
    }
    if (current + 1 < len && academy_input[current] == '>' && academy_input[current + 1] == '=') {
        *op = CMP_GE;
        *index = current + 2;
        return 1;
    }
    if (current + 1 < len && academy_input[current] == '<' && academy_input[current + 1] == '=') {
        *op = CMP_LE;
        *index = current + 2;
        return 1;
    }
    if (current < len && academy_input[current] == '>') {
        *op = CMP_GT;
        *index = current + 1;
        return 1;
    }
    if (current < len && academy_input[current] == '<') {
        *op = CMP_LT;
        *index = current + 1;
        return 1;
    }

    set_message("expected comparison operator");
    return 0;
}

static int parse_bool_expression(int *index, int len, int *value) {
    int lhs = 0;
    int rhs = 0;
    int op = 0;

    if (!parse_int_expression(index, len, &lhs)) {
        return 0;
    }
    if (!parse_comparison_operator(index, len, &op)) {
        return 0;
    }
    if (!parse_int_expression(index, len, &rhs)) {
        return 0;
    }

    if (op == CMP_EQ) {
        *value = lhs == rhs;
    } else if (op == CMP_NE) {
        *value = lhs != rhs;
    } else if (op == CMP_GT) {
        *value = lhs > rhs;
    } else if (op == CMP_GE) {
        *value = lhs >= rhs;
    } else if (op == CMP_LT) {
        *value = lhs < rhs;
    } else {
        *value = lhs <= rhs;
    }
    return 1;
}

static int append_output_byte(unsigned char ch) {
    if (!academy_output_enabled) {
        return 1;
    }
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

static int parse_word_literal_to_storage(int *index, int len, int *offset, int *word_len) {
    int current = skip_trivia(*index, len);
    int start_offset = academy_word_storage_len;
    if (current >= len || academy_input[current] != '"') {
        set_message("expected word literal");
        return 0;
    }
    current += 1;

    while (current < len) {
        unsigned char ch = academy_input[current];
        if (ch == '"') {
            *offset = start_offset;
            *word_len = academy_word_storage_len - start_offset;
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
        if (academy_word_storage_len >= WORD_STORAGE_CAPACITY) {
            set_message("word storage exceeds WASM evaluator capacity");
            return 0;
        }
        academy_word_storage[academy_word_storage_len] = ch;
        academy_word_storage_len += 1;
        current += 1;
    }

    set_message("unterminated word literal");
    return 0;
}

static int append_output_word_var(int slot) {
    int offset = var_word_offsets[slot];
    int len = var_word_lens[slot];
    for (int i = 0; i < len; i += 1) {
        if (!append_output_byte(academy_word_storage[offset + i])) {
            return 0;
        }
    }
    return 1;
}

static int parse_say_value_statement(int *index, int len) {
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
        unsigned char name[IDENT_CAPACITY];
        int name_len = 0;
        int name_cursor = current;
        if (parse_identifier(&name_cursor, len, name, &name_len, "expected value after say")) {
            int after_name = skip_trivia(name_cursor, len);
            int slot = find_var(name, name_len);
            if (
                slot >= 0 &&
                var_types[slot] == VALUE_WORD &&
                (after_name >= len || (
                    academy_input[after_name] != '+' &&
                    academy_input[after_name] != '-' &&
                    academy_input[after_name] != '*' &&
                    academy_input[after_name] != '/'
                ))
            ) {
                if (!append_output_word_var(slot)) {
                    return 0;
                }
                current = name_cursor;
            } else {
                if (!parse_int_expression(&current, len, &int_value)) {
                    return 0;
                }
                if (!append_output_int(int_value)) {
                    return 0;
                }
            }
        } else {
            if (!parse_int_expression(&current, len, &int_value)) {
                return 0;
            }
            if (!append_output_int(int_value)) {
                return 0;
            }
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

static int type_name_is(const unsigned char *name, int name_len, const char *expected, int expected_len) {
    if (name_len != expected_len) {
        return 0;
    }
    for (int i = 0; i < expected_len; i += 1) {
        if (name[i] != (unsigned char)expected[i]) {
            return 0;
        }
    }
    return 1;
}

static int parse_pilot_statement(int *index, int len) {
    unsigned char name[IDENT_CAPACITY];
    unsigned char type_name[IDENT_CAPACITY];
    int name_len = 0;
    int type_name_len = 0;
    int int_value = 0;
    int word_offset = 0;
    int word_len = 0;
    int slot = -1;
    int current = skip_trivia(*index, len);

    if (!match_keyword(current, len, "pilot", 5)) {
        set_message("expected pilot declaration");
        return 0;
    }
    current += 5;
    if (!parse_identifier(&current, len, name, &name_len, "expected pilot name")) {
        return 0;
    }
    slot = declare_var(name, name_len);
    if (slot < 0) {
        return 0;
    }

    current = skip_trivia(current, len);
    if (current < len && academy_input[current] == ':') {
        current += 1;
        if (!parse_identifier(&current, len, type_name, &type_name_len, "expected type annotation")) {
            return 0;
        }
        current = skip_trivia(current, len);
    }

    if (current >= len || academy_input[current] != '=') {
        set_message("expected '=' in pilot declaration");
        return 0;
    }
    current += 1;
    current = skip_trivia(current, len);

    if (current < len && academy_input[current] == '"') {
        if (type_name_len > 0 && !type_name_is(type_name, type_name_len, "word", 4)) {
            set_message("word literal does not match type annotation");
            return 0;
        }
        if (!parse_word_literal_to_storage(&current, len, &word_offset, &word_len)) {
            return 0;
        }
        var_types[slot] = VALUE_WORD;
        var_word_offsets[slot] = word_offset;
        var_word_lens[slot] = word_len;
    } else {
        if (type_name_len > 0 && !type_name_is(type_name, type_name_len, "int", 3)) {
            set_message("int expression does not match type annotation");
            return 0;
        }
        if (!parse_int_expression(&current, len, &int_value)) {
            return 0;
        }
        var_types[slot] = VALUE_INT;
        var_int_values[slot] = int_value;
    }

    *index = current;
    return 1;
}

static int parse_basics_program(int len) {
    int index = skip_trivia(0, len);
    int say_count = 0;

    reset_eval_state();

    while (match_keyword(index, len, "pilot", 5)) {
        if (!parse_pilot_statement(&index, len)) {
            return 0;
        }
        index = skip_trivia(index, len);
    }

    while (match_keyword(index, len, "say", 3)) {
        if (!parse_say_value_statement(&index, len)) {
            return 0;
        }
        say_count += 1;
        index = skip_trivia(index, len);
    }

    if (say_count == 0) {
        set_message("expected say statement");
        return 0;
    }
    if (index != len) {
        set_message("expected end of source after basics lesson program");
        return 0;
    }
    return 1;
}

static int find_block_range(int *index, int len, int *body_start, int *body_end, int *after_block) {
    int current = skip_trivia(*index, len);
    int depth = 1;

    if (current >= len || academy_input[current] != '{') {
        set_message("expected block");
        return 0;
    }
    current += 1;
    *body_start = current;

    while (current < len) {
        unsigned char ch = academy_input[current];
        if (ch == '"') {
            current += 1;
            while (current < len) {
                if (academy_input[current] == '\\') {
                    current += 2;
                    continue;
                }
                if (academy_input[current] == '"') {
                    current += 1;
                    break;
                }
                current += 1;
            }
            continue;
        }
        if (current + 1 < len && academy_input[current] == '-' && academy_input[current + 1] == '-') {
            current += 2;
            while (current < len && academy_input[current] != '\n') {
                current += 1;
            }
            continue;
        }
        if (ch == '{') {
            depth += 1;
        } else if (ch == '}') {
            depth -= 1;
            if (depth == 0) {
                *body_end = current;
                *after_block = current + 1;
                *index = current + 1;
                return 1;
            }
        }
        current += 1;
    }

    set_message("unterminated block");
    return 0;
}

static int parse_say_statements_range(int start, int end) {
    int index = skip_trivia(start, end);
    int statement_count = 0;

    while (index < end) {
        if (!parse_say_value_statement(&index, end)) {
            return 0;
        }
        statement_count += 1;
        index = skip_trivia(index, end);
    }

    if (statement_count == 0) {
        set_message("expected say statement in block");
        return 0;
    }
    return 1;
}

static int validate_say_block(int start, int end) {
    int previous_output_enabled = academy_output_enabled;
    int ok = 0;

    academy_output_enabled = 0;
    ok = parse_say_statements_range(start, end);
    academy_output_enabled = previous_output_enabled;
    return ok;
}

static int parse_conditions_program(int len) {
    int index = skip_trivia(0, len);
    int condition_value = 0;
    int then_start = 0;
    int then_end = 0;
    int then_after = 0;
    int else_start = 0;
    int else_end = 0;
    int else_after = 0;

    reset_eval_state();

    while (match_keyword(index, len, "pilot", 5)) {
        if (!parse_pilot_statement(&index, len)) {
            return 0;
        }
        index = skip_trivia(index, len);
    }

    if (!match_keyword(index, len, "if", 2)) {
        set_message("expected if statement");
        return 0;
    }
    index += 2;

    if (!parse_bool_expression(&index, len, &condition_value)) {
        return 0;
    }
    if (!find_block_range(&index, len, &then_start, &then_end, &then_after)) {
        return 0;
    }

    index = skip_trivia(then_after, len);
    if (!match_keyword(index, len, "else", 4)) {
        set_message("expected else branch");
        return 0;
    }
    index += 4;
    if (!find_block_range(&index, len, &else_start, &else_end, &else_after)) {
        return 0;
    }

    index = skip_trivia(else_after, len);
    if (index != len) {
        set_message("expected end of source after condition lesson program");
        return 0;
    }

    if (!validate_say_block(then_start, then_end)) {
        return 0;
    }
    if (!validate_say_block(else_start, else_end)) {
        return 0;
    }

    if (condition_value) {
        return parse_say_statements_range(then_start, then_end);
    }
    return parse_say_statements_range(else_start, else_end);
}

static int parse_loops_program(int len) {
    int index = skip_trivia(0, len);
    int count = 0;
    int body_start = 0;
    int body_end = 0;
    int after_block = 0;

    reset_eval_state();

    while (match_keyword(index, len, "pilot", 5)) {
        if (!parse_pilot_statement(&index, len)) {
            return 0;
        }
        index = skip_trivia(index, len);
    }

    if (!match_keyword(index, len, "repeat", 6)) {
        set_message("expected repeat loop");
        return 0;
    }
    index += 6;

    if (!parse_int_expression(&index, len, &count)) {
        return 0;
    }
    if (count < 0) {
        set_message("repeat count cannot be negative");
        return 0;
    }
    index = skip_trivia(index, len);
    if (!match_keyword(index, len, "times", 5)) {
        set_message("expected times keyword");
        return 0;
    }
    index += 5;

    if (!find_block_range(&index, len, &body_start, &body_end, &after_block)) {
        return 0;
    }
    index = skip_trivia(after_block, len);
    if (index != len) {
        set_message("expected end of source after loop lesson program");
        return 0;
    }

    if (!validate_say_block(body_start, body_end)) {
        return 0;
    }

    for (int i = 0; i < count; i += 1) {
        if (!parse_say_statements_range(body_start, body_end)) {
            return 0;
        }
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

    if (!parse_basics_program(source_len)) {
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
int academy_evaluate_primitive_types(int source_len) {
    static const unsigned char expected[] = "Shiranui\n9001\n";
    int status = 0;

    reset_eval_state();

    if (source_len < 0 || source_len > INPUT_CAPACITY) {
        set_message("source exceeds WASM input capacity");
        return status;
    }

    if (!parse_basics_program(source_len)) {
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
int academy_evaluate_arithmetic(int source_len) {
    static const unsigned char expected[] = "32\n";
    int status = 0;

    reset_eval_state();

    if (source_len < 0 || source_len > INPUT_CAPACITY) {
        set_message("source exceeds WASM input capacity");
        return status;
    }

    if (!parse_basics_program(source_len)) {
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
int academy_evaluate_conditions(int source_len) {
    static const unsigned char expected[] = "over\n";
    int status = 0;

    reset_eval_state();

    if (source_len < 0 || source_len > INPUT_CAPACITY) {
        set_message("source exceeds WASM input capacity");
        return status;
    }

    if (!parse_conditions_program(source_len)) {
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
int academy_evaluate_loops(int source_len) {
    static const unsigned char expected[] = "FREAK\nFREAK\nFREAK\n";
    int status = 0;

    reset_eval_state();

    if (source_len < 0 || source_len > INPUT_CAPACITY) {
        set_message("source exceeds WASM input capacity");
        return status;
    }

    if (!parse_loops_program(source_len)) {
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
