# Vendored llhttp for the FREAK HTTP floor

Pinned maintained generated release: `release/v9.4.3`, commit
`0e815792b167a9bd8ace259b95b7da953776c288` from
<https://github.com/nodejs/llhttp>. Upstream is MIT licensed; both upstream
license files are retained. `UPSTREAM.json` records the archive digest and
`SHA256SUMS` verifies the actual vendored source/header/license/shim. `UPSTREAM.json`
preserves original upstream digests and `PATCHES.md` records the reviewed
two-line generated span callback correction.

The generated C99 parser, native API, protocol helpers, and header total
371,863 bytes. Clang 19 on Linux compiled the single translation unit at O2 to
116,016 bytes in under a second. This evaluation establishes the available
Linux toolchain; Windows/macOS compilation and execution require their gates.

Normal FREAK builds need no Node, npm, generator, CMake, network, or package
build script. `freak_amalgamation.inc` provides explicit typed byte-pointer
bridges for upstream callbacks normally compiled in separate translation
units. `src/llhttp.h` is a local include-path shim. Only the documented span callback type/cast correction changes generated
upstream source; the adapter is part of the trusted compiler
runtime, rather than native FFI exposed to packages.

The HTTP adapter uses strict defaults and never enables a leniency flag.
Lenient parsing can permit request smuggling or poisoning; see upstream
<https://github.com/nodejs/llhttp#api> and RFC 9112. The FREAK adapter applies its
stricter Host, duplicate framing, supported coding, limits, and lifetime policy
around parser events. The dependency does not supply routing, TLS, CORS,
authentication, cookies, forwarded-header trust, or application isolation.
