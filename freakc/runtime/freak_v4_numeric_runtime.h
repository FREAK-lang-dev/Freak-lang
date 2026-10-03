#ifndef FREAK_V4_NUMERIC_RUNTIME_H
#define FREAK_V4_NUMERIC_RUNTIME_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* V4 operators are checked at every optimization level. A failed operation
 * writes one fixed diagnostic to stderr and exits with status 1. These entry
 * points do not change the legacy V3 arithmetic runtime. */
int64_t freak_v4_int_add(int64_t lhs, int64_t rhs);
int64_t freak_v4_int_sub(int64_t lhs, int64_t rhs);
int64_t freak_v4_int_mul(int64_t lhs, int64_t rhs);
int64_t freak_v4_int_neg(int64_t value);
int64_t freak_v4_int_div(int64_t lhs, int64_t rhs);
int64_t freak_v4_int_mod(int64_t lhs, int64_t rhs);

uint64_t freak_v4_uint_add(uint64_t lhs, uint64_t rhs);
uint64_t freak_v4_uint_sub(uint64_t lhs, uint64_t rhs);
uint64_t freak_v4_uint_mul(uint64_t lhs, uint64_t rhs);
uint64_t freak_v4_uint_neg(uint64_t value);
uint64_t freak_v4_uint_div(uint64_t lhs, uint64_t rhs);
uint64_t freak_v4_uint_mod(uint64_t lhs, uint64_t rhs);

/* The tiny ABI is an unsigned i8 carrier, including the C ABI zero-extension
 * attributes on LLVM declarations/calls. Callers must check wider conversions
 * before narrowing to this interface. */
uint8_t freak_v4_tiny_add(uint8_t lhs, uint8_t rhs);
uint8_t freak_v4_tiny_sub(uint8_t lhs, uint8_t rhs);
uint8_t freak_v4_tiny_mul(uint8_t lhs, uint8_t rhs);
uint8_t freak_v4_tiny_neg(uint8_t value);
uint8_t freak_v4_tiny_div(uint8_t lhs, uint8_t rhs);
uint8_t freak_v4_tiny_mod(uint8_t lhs, uint8_t rhs);

#ifdef __cplusplus
}
#endif

#endif
