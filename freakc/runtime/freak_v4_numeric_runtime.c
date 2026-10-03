#include "freak_v4_numeric_runtime.h"

#include <float.h>
#include <stdio.h>
#include <stdlib.h>

_Static_assert(sizeof(double) == 8 && DBL_MANT_DIG == 53 && DBL_MAX_EXP == 1024,
               "V4 num requires IEEE 754 binary64 double");

#if defined(_MSC_VER)
#define FREAK_V4_NUMERIC_NORETURN __declspec(noreturn)
#else
#define FREAK_V4_NUMERIC_NORETURN _Noreturn
#endif

static FREAK_V4_NUMERIC_NORETURN void freak_v4_numeric_fail(const char *message) {
    fputs("FREAK V4: ", stderr);
    fputs(message, stderr);
    fputc('\n', stderr);
    exit(1);
}

int64_t freak_v4_int_add(int64_t lhs, int64_t rhs) {
    if ((rhs > 0 && lhs > INT64_MAX - rhs) ||
        (rhs < 0 && lhs < INT64_MIN - rhs)) {
        freak_v4_numeric_fail("int addition overflow");
    }
    return lhs + rhs;
}

int64_t freak_v4_int_sub(int64_t lhs, int64_t rhs) {
    if ((rhs > 0 && lhs < INT64_MIN + rhs) ||
        (rhs < 0 && lhs > INT64_MAX + rhs)) {
        freak_v4_numeric_fail("int subtraction overflow");
    }
    return lhs - rhs;
}

int64_t freak_v4_int_mul(int64_t lhs, int64_t rhs) {
    /* Partition by sign before division. Every bound calculation is defined:
     * INT64_MIN is divided only by a positive value, and negative divisors
     * divide INT64_MAX. In particular no guard evaluates INT64_MIN / -1. */
    if (lhs > 0) {
        if ((rhs > 0 && lhs > INT64_MAX / rhs) ||
            (rhs < 0 && rhs < INT64_MIN / lhs)) {
            freak_v4_numeric_fail("int multiplication overflow");
        }
    } else if (lhs < 0) {
        if ((rhs > 0 && lhs < INT64_MIN / rhs) ||
            (rhs < 0 && lhs < INT64_MAX / rhs)) {
            freak_v4_numeric_fail("int multiplication overflow");
        }
    }
    return lhs * rhs;
}

int64_t freak_v4_int_neg(int64_t value) {
    if (value == INT64_MIN) {
        freak_v4_numeric_fail("int negation overflow");
    }
    return -value;
}

int64_t freak_v4_int_div(int64_t lhs, int64_t rhs) {
    if (rhs == 0) {
        freak_v4_numeric_fail("int division by zero");
    }
    if (lhs == INT64_MIN && rhs == -1) {
        freak_v4_numeric_fail("int division overflow");
    }
    return lhs / rhs;
}

int64_t freak_v4_int_mod(int64_t lhs, int64_t rhs) {
    if (rhs == 0) {
        freak_v4_numeric_fail("int remainder by zero");
    }
    /* C's remainder operation shares division's unrepresentable-quotient
     * precondition, even though the mathematical remainder would be zero. */
    if (lhs == INT64_MIN && rhs == -1) {
        freak_v4_numeric_fail("int remainder overflow");
    }
    return lhs % rhs;
}

uint64_t freak_v4_uint_add(uint64_t lhs, uint64_t rhs) {
    if (lhs > UINT64_MAX - rhs) {
        freak_v4_numeric_fail("uint addition overflow");
    }
    return lhs + rhs;
}

uint64_t freak_v4_uint_sub(uint64_t lhs, uint64_t rhs) {
    if (lhs < rhs) {
        freak_v4_numeric_fail("uint subtraction underflow");
    }
    return lhs - rhs;
}

uint64_t freak_v4_uint_mul(uint64_t lhs, uint64_t rhs) {
    if (rhs != 0 && lhs > UINT64_MAX / rhs) {
        freak_v4_numeric_fail("uint multiplication overflow");
    }
    return lhs * rhs;
}

uint64_t freak_v4_uint_neg(uint64_t value) {
    if (value != 0) {
        freak_v4_numeric_fail("uint negation underflow");
    }
    return 0;
}

uint64_t freak_v4_uint_div(uint64_t lhs, uint64_t rhs) {
    if (rhs == 0) {
        freak_v4_numeric_fail("uint division by zero");
    }
    return lhs / rhs;
}

uint64_t freak_v4_uint_mod(uint64_t lhs, uint64_t rhs) {
    if (rhs == 0) {
        freak_v4_numeric_fail("uint remainder by zero");
    }
    return lhs % rhs;
}

uint8_t freak_v4_tiny_add(uint8_t lhs, uint8_t rhs) {
    uint32_t result = (uint32_t)lhs + (uint32_t)rhs;
    if (result > UINT8_MAX) {
        freak_v4_numeric_fail("tiny addition overflow");
    }
    return (uint8_t)result;
}

uint8_t freak_v4_tiny_sub(uint8_t lhs, uint8_t rhs) {
    if (lhs < rhs) {
        freak_v4_numeric_fail("tiny subtraction underflow");
    }
    return (uint8_t)((uint32_t)lhs - (uint32_t)rhs);
}

uint8_t freak_v4_tiny_mul(uint8_t lhs, uint8_t rhs) {
    uint32_t result = (uint32_t)lhs * (uint32_t)rhs;
    if (result > UINT8_MAX) {
        freak_v4_numeric_fail("tiny multiplication overflow");
    }
    return (uint8_t)result;
}

uint8_t freak_v4_tiny_neg(uint8_t value) {
    if (value != 0) {
        freak_v4_numeric_fail("tiny negation underflow");
    }
    return 0;
}

uint8_t freak_v4_tiny_div(uint8_t lhs, uint8_t rhs) {
    if (rhs == 0) {
        freak_v4_numeric_fail("tiny division by zero");
    }
    return (uint8_t)((uint32_t)lhs / (uint32_t)rhs);
}

uint8_t freak_v4_tiny_mod(uint8_t lhs, uint8_t rhs) {
    if (rhs == 0) {
        freak_v4_numeric_fail("tiny remainder by zero");
    }
    return (uint8_t)((uint32_t)lhs % (uint32_t)rhs);
}

int64_t freak_v4_int_from_uint(uint64_t value) {
    if (value > (uint64_t)INT64_MAX) {
        freak_v4_numeric_fail("uint to int conversion out of range");
    }
    return (int64_t)value;
}

uint64_t freak_v4_uint_from_int(int64_t value) {
    if (value < 0) {
        freak_v4_numeric_fail("int to uint conversion out of range");
    }
    return (uint64_t)value;
}

uint8_t freak_v4_tiny_from_int(int64_t value) {
    if (value < 0 || value > UINT8_MAX) {
        freak_v4_numeric_fail("int to tiny conversion out of range");
    }
    return (uint8_t)value;
}

uint8_t freak_v4_tiny_from_uint(uint64_t value) {
    if (value > UINT8_MAX) {
        freak_v4_numeric_fail("uint to tiny conversion out of range");
    }
    return (uint8_t)value;
}

int64_t freak_v4_int_from_tiny(uint8_t value) {
    return (int64_t)value;
}

uint64_t freak_v4_uint_from_tiny(uint8_t value) {
    return (uint64_t)value;
}

int64_t freak_v4_int_from_num(double value) {
    /* Both power-of-two bounds are exactly representable. Converting
     * INT64_MAX to double would round up and accept an undefined C cast. */
    if (value != value || value < -9223372036854775808.0 ||
        value >= 9223372036854775808.0) {
        freak_v4_numeric_fail("num to int conversion out of range");
    }
    return (int64_t)value;
}

uint64_t freak_v4_uint_from_num(double value) {
    /* Check the range of the truncated result: (-1, 0) truncates to zero.
     * NaN fails explicitly; both infinities fail the ordered bound checks. */
    if (value != value || value <= -1.0 || value >= 18446744073709551616.0) {
        freak_v4_numeric_fail("num to uint conversion out of range");
    }
    return (uint64_t)value;
}

uint8_t freak_v4_tiny_from_num(double value) {
    if (value != value || value <= -1.0 || value >= 256.0) {
        freak_v4_numeric_fail("num to tiny conversion out of range");
    }
    return (uint8_t)value;
}

double freak_v4_num_from_int(int64_t value) {
    return (double)value;
}

double freak_v4_num_from_uint(uint64_t value) {
    return (double)value;
}

double freak_v4_num_from_tiny(uint8_t value) {
    return (double)value;
}
