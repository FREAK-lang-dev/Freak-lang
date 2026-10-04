#include "freak_v4_c_integer_runtime.h"

#include <errno.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* These exact function-pointer types make a changed helper prototype a
 * compiler error under the driver's -Werror, before any native proof. */
static int32_t (*const signed_binary[])(int32_t, int32_t) = {
    freak_v4_i32_add, freak_v4_i32_sub, freak_v4_i32_mul,
    freak_v4_i32_div, freak_v4_i32_mod
};
static uint32_t (*const unsigned_binary[])(uint32_t, uint32_t) = {
    freak_v4_u32_add, freak_v4_u32_sub, freak_v4_u32_mul,
    freak_v4_u32_div, freak_v4_u32_mod
};
static int32_t (*const signed_negate)(int32_t) = freak_v4_i32_neg;
static uint32_t (*const unsigned_negate)(uint32_t) = freak_v4_u32_neg;
static int32_t (*const signed_from_int)(int64_t) = freak_v4_i32_from_int;
static int32_t (*const signed_from_uint)(uint64_t) = freak_v4_i32_from_uint;
static uint32_t (*const unsigned_from_int)(int64_t) = freak_v4_u32_from_int;
static uint32_t (*const unsigned_from_uint)(uint64_t) = freak_v4_u32_from_uint;
static const char *const operations[] = { "add", "sub", "mul", "div", "mod" };

static void input_error(void) {
    exit(2);
}

static void decimal(const char *text, int allow_minus) {
    const unsigned char *cursor = (const unsigned char *)text;
    if (allow_minus && *cursor == '-') {
        ++cursor;
    }
    if (*cursor == '\0') {
        input_error();
    }
    for (; *cursor; ++cursor) {
        if (*cursor < '0' || *cursor > '9') {
            input_error();
        }
    }
}

static int64_t signed_value(const char *text) {
    char *end = NULL;
    intmax_t result;
    decimal(text, 1);
    errno = 0;
    result = strtoimax(text, &end, 10);
    if (errno || !end || *end || result < INT64_MIN || result > INT64_MAX) {
        input_error();
    }
    return (int64_t)result;
}

static uint64_t unsigned_value(const char *text) {
    char *end = NULL;
    uintmax_t result;
    decimal(text, 0);
    errno = 0;
    result = strtoumax(text, &end, 10);
    if (errno || !end || *end || result > UINT64_MAX) {
        input_error();
    }
    return (uint64_t)result;
}

static int32_t signed32(const char *text) {
    int64_t result = signed_value(text);
    if (result < INT32_MIN || result > INT32_MAX) {
        input_error();
    }
    return (int32_t)result;
}

static uint32_t unsigned32(const char *text) {
    uint64_t result = unsigned_value(text);
    if (result > UINT32_MAX) {
        input_error();
    }
    return (uint32_t)result;
}

static int capability(const char *mode) {
    if (strcmp(mode, "--ubsan-overflow") == 0) {
        volatile int32_t left = INT32_MAX;
        volatile int32_t right = 1;
        volatile int32_t result = left + right;
        return result == 0 ? 0 : 2;
    }
    if (strcmp(mode, "--ubsan-division") == 0) {
        volatile int32_t left = INT32_MIN;
        volatile int32_t right = -1;
        volatile int32_t result = left / right;
        return result == 0 ? 0 : 2;
    }
    return 2;
}

int main(int argc, char **argv) {
    const char *operation;
    int is_signed;
    size_t index;
    if (argc == 2) {
        return capability(argv[1]);
    }
    if (argc != 3 && argc != 4) {
        return 2;
    }
    is_signed = strncmp(argv[1], "i32_", 4) == 0;
    if (!is_signed && strncmp(argv[1], "u32_", 4) != 0) {
        return 2;
    }
    operation = argv[1] + 4;
    if (strcmp(operation, "neg") == 0 && argc == 3) {
        if (is_signed) {
            printf("%" PRId32 "\n", signed_negate(signed32(argv[2])));
        } else {
            printf("%" PRIu32 "\n", unsigned_negate(unsigned32(argv[2])));
        }
        return 0;
    }
    if (strcmp(operation, "from_int") == 0 && argc == 3) {
        int64_t value = signed_value(argv[2]);
        if (is_signed) {
            printf("%" PRId32 "\n", signed_from_int(value));
        } else {
            printf("%" PRIu32 "\n", unsigned_from_int(value));
        }
        return 0;
    }
    if (strcmp(operation, "from_uint") == 0 && argc == 3) {
        uint64_t value = unsigned_value(argv[2]);
        if (is_signed) {
            printf("%" PRId32 "\n", signed_from_uint(value));
        } else {
            printf("%" PRIu32 "\n", unsigned_from_uint(value));
        }
        return 0;
    }
    if (argc != 4) {
        return 2;
    }
    for (index = 0; index < sizeof(operations) / sizeof(operations[0]); ++index) {
        if (strcmp(operation, operations[index]) == 0) {
            if (is_signed) {
                int32_t left = signed32(argv[2]);
                int32_t right = signed32(argv[3]);
                printf("%" PRId32 "\n", signed_binary[index](left, right));
            } else {
                uint32_t left = unsigned32(argv[2]);
                uint32_t right = unsigned32(argv[3]);
                printf("%" PRIu32 "\n", unsigned_binary[index](left, right));
            }
            return 0;
        }
    }
    return 2;
}
