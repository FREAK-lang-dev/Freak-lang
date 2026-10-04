#include "freak_v4_c_integer_runtime.h"

#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

_Static_assert(CHAR_BIT == 8 && sizeof(int32_t) == 4 && sizeof(uint32_t) == 4,
               "V4 checked32 requires exact 32-bit carriers");
_Static_assert(sizeof(int64_t) == 8 && sizeof(uint64_t) == 8,
               "V4 checked32 requires exact 64-bit intermediates");
_Static_assert(INT32_MIN == (-INT32_C(2147483647) - 1) &&
               INT32_MAX == INT32_C(2147483647) &&
               UINT32_MAX == UINT32_C(4294967295), "V4 checked32 range");

#if defined(_MSC_VER)
#define FREAK_V4_C_INTEGER_NORETURN __declspec(noreturn)
#else
#define FREAK_V4_C_INTEGER_NORETURN _Noreturn
#endif

/* A separate private routine keeps the existing V3 and numeric runtime ABI
 * unchanged. Numeric failures exit; they do not unwind across a C boundary. */
static FREAK_V4_C_INTEGER_NORETURN void freak_v4_c_integer_fail(const char *message) {
    fputs("FREAK V4: ", stderr);
    fputs(message, stderr);
    fputc('\n', stderr);
    exit(1);
}

int32_t freak_v4_i32_add(int32_t lhs, int32_t rhs) {
    int64_t result = (int64_t)lhs + (int64_t)rhs;
    if (result < INT32_MIN || result > INT32_MAX) {
        freak_v4_c_integer_fail("i32 addition overflow");
    }
    return (int32_t)result;
}

int32_t freak_v4_i32_sub(int32_t lhs, int32_t rhs) {
    int64_t result = (int64_t)lhs - (int64_t)rhs;
    if (result < INT32_MIN || result > INT32_MAX) {
        freak_v4_c_integer_fail("i32 subtraction overflow");
    }
    return (int32_t)result;
}

int32_t freak_v4_i32_mul(int32_t lhs, int32_t rhs) {
    /* Every product of two signed32 inputs fits int64, including MIN32². */
    int64_t result = (int64_t)lhs * (int64_t)rhs;
    if (result < INT32_MIN || result > INT32_MAX) {
        freak_v4_c_integer_fail("i32 multiplication overflow");
    }
    return (int32_t)result;
}

int32_t freak_v4_i32_neg(int32_t value) {
    int64_t result = -(int64_t)value;
    if (result > INT32_MAX) {
        freak_v4_c_integer_fail("i32 negation overflow");
    }
    return (int32_t)result;
}

int32_t freak_v4_i32_div(int32_t lhs, int32_t rhs) {
    if (rhs == 0) {
        freak_v4_c_integer_fail("i32 division by zero");
    }
    if (lhs == INT32_MIN && rhs == -1) {
        freak_v4_c_integer_fail("i32 division overflow");
    }
    return (int32_t)((int64_t)lhs / (int64_t)rhs);
}

int32_t freak_v4_i32_mod(int32_t lhs, int32_t rhs) {
    if (rhs == 0) {
        freak_v4_c_integer_fail("i32 remainder by zero");
    }
    /* Preserve the unrepresentable-quotient failure, even though a widened
     * mathematical remainder for MIN32/-1 would otherwise be zero. */
    if (lhs == INT32_MIN && rhs == -1) {
        freak_v4_c_integer_fail("i32 remainder overflow");
    }
    return (int32_t)((int64_t)lhs % (int64_t)rhs);
}

uint32_t freak_v4_u32_add(uint32_t lhs, uint32_t rhs) {
    uint64_t result = (uint64_t)lhs + (uint64_t)rhs;
    if (result > UINT32_MAX) {
        freak_v4_c_integer_fail("u32 addition overflow");
    }
    return (uint32_t)result;
}

uint32_t freak_v4_u32_sub(uint32_t lhs, uint32_t rhs) {
    if (lhs < rhs) {
        freak_v4_c_integer_fail("u32 subtraction underflow");
    }
    return (uint32_t)((uint64_t)lhs - (uint64_t)rhs);
}

uint32_t freak_v4_u32_mul(uint32_t lhs, uint32_t rhs) {
    /* UINT32_MAX² is 18446744065119617025, below UINT64_MAX. */
    uint64_t result = (uint64_t)lhs * (uint64_t)rhs;
    if (result > UINT32_MAX) {
        freak_v4_c_integer_fail("u32 multiplication overflow");
    }
    return (uint32_t)result;
}

uint32_t freak_v4_u32_neg(uint32_t value) {
    if (value != 0) {
        freak_v4_c_integer_fail("u32 negation underflow");
    }
    return 0;
}

uint32_t freak_v4_u32_div(uint32_t lhs, uint32_t rhs) {
    if (rhs == 0) {
        freak_v4_c_integer_fail("u32 division by zero");
    }
    return (uint32_t)((uint64_t)lhs / (uint64_t)rhs);
}

uint32_t freak_v4_u32_mod(uint32_t lhs, uint32_t rhs) {
    if (rhs == 0) {
        freak_v4_c_integer_fail("u32 remainder by zero");
    }
    return (uint32_t)((uint64_t)lhs % (uint64_t)rhs);
}

int32_t freak_v4_i32_from_int(int64_t value) {
    if (value < INT32_MIN || value > INT32_MAX) {
        freak_v4_c_integer_fail("int to i32 conversion out of range");
    }
    return (int32_t)value;
}

int32_t freak_v4_i32_from_uint(uint64_t value) {
    if (value > (uint64_t)INT32_MAX) {
        freak_v4_c_integer_fail("uint to i32 conversion out of range");
    }
    return (int32_t)value;
}

uint32_t freak_v4_u32_from_int(int64_t value) {
    if (value < 0 || value > (int64_t)UINT32_MAX) {
        freak_v4_c_integer_fail("int to u32 conversion out of range");
    }
    return (uint32_t)value;
}

uint32_t freak_v4_u32_from_uint(uint64_t value) {
    if (value > UINT32_MAX) {
        freak_v4_c_integer_fail("uint to u32 conversion out of range");
    }
    return (uint32_t)value;
}
