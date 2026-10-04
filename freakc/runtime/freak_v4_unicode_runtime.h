#ifndef FREAK_V4_UNICODE_RUNTIME_H
#define FREAK_V4_UNICODE_RUNTIME_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Compiler-private owned-word ABI. Borrow a live runtime-owned UTF-8 word and
 * return fresh independent storage, even for empty/unchanged input. Preserve
 * embedded NULs. Unicode 17.0.0 default full lowercase includes expansions and
 * original-string Final_Sigma context; locale-specific tailoring is excluded.
 * Unknown/consumed inputs and allocation/size failures cause a named panic. */
int64_t freak_v4_word_to_lower(int64_t value);

#ifdef __cplusplus
}
#endif

#endif
