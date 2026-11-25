/* FREAK wasm32 platform layer: the libc subset the V4 core runtime uses.
 *
 * The wasm runtime is built freestanding against these headers instead of a
 * C library. Everything except the allocator and the mem* functions (which
 * LLVM and generated code call by their C names) is spelled freak_pal_* at
 * link level, so a FREAK `task open` or `task read` cannot replace the
 * runtime's own file calls on this target. */
#pragma once
#include <stddef.h>
#include <stdint.h>
#include <stdarg.h>

#define FREAK_PAL(name) freak_pal_##name
