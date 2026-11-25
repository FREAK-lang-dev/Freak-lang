/*
 * The pinned LLVM release libraries are built with zstd support, which LLVM
 * only uses for compressed debug sections and profiles. freak never asks for
 * either, so instead of shipping a libzstd dependency the release CLI links
 * these entry points, which report "unavailable" if anything ever calls them.
 */
#include <stddef.h>

typedef struct freak_zstd_unavailable ZSTD_CCtx;

#define FREAK_ZSTD_ERROR ((size_t)-1)

size_t ZSTD_compressBound(size_t size) { return size + (size >> 8) + 64; }
ZSTD_CCtx *ZSTD_createCCtx(void) { return NULL; }
size_t ZSTD_freeCCtx(ZSTD_CCtx *context) { (void)context; return 0; }
size_t ZSTD_CCtx_setParameter(ZSTD_CCtx *context, int parameter, int value) {
    (void)context; (void)parameter; (void)value; return FREAK_ZSTD_ERROR;
}
size_t ZSTD_compress2(ZSTD_CCtx *context, void *out, size_t out_size, const void *in, size_t in_size) {
    (void)context; (void)out; (void)out_size; (void)in; (void)in_size; return FREAK_ZSTD_ERROR;
}
size_t ZSTD_decompress(void *out, size_t out_size, const void *in, size_t in_size) {
    (void)out; (void)out_size; (void)in; (void)in_size; return FREAK_ZSTD_ERROR;
}
unsigned ZSTD_isError(size_t code) { return code == FREAK_ZSTD_ERROR; }
const char *ZSTD_getErrorName(size_t code) { (void)code; return "zstd is not available in this freak"; }
