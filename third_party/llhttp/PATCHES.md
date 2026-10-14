# FREAK dependency delta

Upstream generated `src/llhttp.c` declares direct callbacks with
`const unsigned char *`, but its partial-span function-pointer typedef uses
`const char *`. Those types cross object boundaries in upstream builds. The
FREAK single-translation-unit shim defines explicit unsigned-byte wrappers.

Two generated-source lines are corrected: the span callback typedef takes
`const unsigned char *`, and the call casts its end pointer to the same type.
The generated state machine, grammar, constants, and protocol policy remain
unchanged. The wrappers then cast byte pointers to the native API's char
pointers explicitly. This prevents indirect incompatible-function-pointer UB.

`UPSTREAM.json` preserves original upstream digests. `SHA256SUMS` checks the
actual vendored files including the two-line correction and trusted shim.
The focused parser gate feeds request headers and a binary body one byte at a
time under UBSan function checks and verifies a deliberately failing control.

The FREAK-owned `src/llhttp.h` forwarding shim checks the public header's
`INCLUDE_LLHTTP_H_` guard before including `../include/llhttp.h`.
`freak_amalgamation.inc` loads the public header before including the upstream
sources, so this skips a redundant parent-directory lookup that can fail with
explicit extended Windows paths. Standalone translation units still use the
existing forwarding include when the public header has not been loaded. The
public API, generated parser, and callback bridges are unchanged.
