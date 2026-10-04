#ifndef FREAK_V4_C_INTEGER_RUNTIME_H
#define FREAK_V4_C_INTEGER_RUNTIME_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Compiler-private checked32 prerequisite. These C interfaces do not admit
 * c_int/c_long into V4 native source. Failure writes one fixed diagnostic to
 * stderr, produces no value, and exits with status 1 at every optimization. */
int32_t freak_v4_i32_add(int32_t lhs, int32_t rhs);
int32_t freak_v4_i32_sub(int32_t lhs, int32_t rhs);
int32_t freak_v4_i32_mul(int32_t lhs, int32_t rhs);
int32_t freak_v4_i32_neg(int32_t value);
int32_t freak_v4_i32_div(int32_t lhs, int32_t rhs);
int32_t freak_v4_i32_mod(int32_t lhs, int32_t rhs);

uint32_t freak_v4_u32_add(uint32_t lhs, uint32_t rhs);
uint32_t freak_v4_u32_sub(uint32_t lhs, uint32_t rhs);
uint32_t freak_v4_u32_mul(uint32_t lhs, uint32_t rhs);
uint32_t freak_v4_u32_neg(uint32_t value);
uint32_t freak_v4_u32_div(uint32_t lhs, uint32_t rhs);
uint32_t freak_v4_u32_mod(uint32_t lhs, uint32_t rhs);

/* Numerical value is preserved or the operation fails before narrowing. */
int32_t freak_v4_i32_from_int(int64_t value);
int32_t freak_v4_i32_from_uint(uint64_t value);
uint32_t freak_v4_u32_from_int(int64_t value);
uint32_t freak_v4_u32_from_uint(uint64_t value);

#ifdef __cplusplus
}
#endif

#endif
