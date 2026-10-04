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

/* Checked integer conversions preserve numerical value and reject narrowing
 * or sign changes outside the target range. Tiny parameters/results have the
 * same C zero-extension contract as the arithmetic helpers above. */
int64_t freak_v4_int_from_uint(uint64_t value);
uint64_t freak_v4_uint_from_int(int64_t value);
uint8_t freak_v4_tiny_from_int(int64_t value);
uint8_t freak_v4_tiny_from_uint(uint64_t value);
int64_t freak_v4_int_from_tiny(uint8_t value);
uint64_t freak_v4_uint_from_tiny(uint8_t value);

/* num and float use the same binary64 ABI. Integer conversion truncates toward
 * zero, then checks representability; NaN and infinities fail. A fractional
 * value strictly between -1 and 0 therefore converts to unsigned zero. A
 * float32 caller first extends its value to double. Integer-to-num conversion
 * may lose precision; the full integer domain remains finite in binary64. */
int64_t freak_v4_int_from_num(double value);
uint64_t freak_v4_uint_from_num(double value);
uint8_t freak_v4_tiny_from_num(double value);
double freak_v4_num_from_int(int64_t value);
double freak_v4_num_from_uint(uint64_t value);
double freak_v4_num_from_tiny(uint8_t value);

#ifdef __cplusplus
}
#endif

#endif
