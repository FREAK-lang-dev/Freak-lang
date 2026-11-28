# Mbed TLS in the FREAK runtime

`std::tls` runs on Mbed TLS 3.6 LTS. The library ships here as three generated
translation units, not as the upstream tree:

| File | Contents |
|---|---|
| `mbedtls_core.inc` | crypto, X.509 and the TLS client (compiled by `freak_tls_core.c`) |
| `mbedtls_extra.inc` | the TLS server and PSA operations (compiled by `freak_tls_extra.c`) |
| `mbedtls_keys.inc` | the TLS 1.3 key schedule and the public headers (included by `freak_tls.c`) |

Upstream's library files clash on file-local names, so they can't share one
translation unit. Each `.inc` inlines every Mbed TLS header it needs once,
with comments stripped and `#line` markers, so compiler messages still name
the upstream file and line.

There are no local patches: `PATCHES` in `tools/mbedtls_amalgamate.py` is
empty, so the `.inc` files are exactly upstream. A patch (source in
`tools/mbedtls_patches/`) goes in only after a security review.

The build configuration is `freak_mbedtls_config.h`, which is the upstream
default with DTLS, the BSD socket and timing modules, self tests, debug output,
PSK and static-RSA/DH key exchanges, legacy ciphers, X.509 writing and PSA key
storage removed. Entropy comes from the FREAK runtime's OS generator
(`mbedtls_hardware_poll` in `freak_tls.c`), so no bcrypt or crypt32 import
library is needed on Windows.

The CLI compiles these units only for programs that `use std::tls`. Other
programs don't carry Mbed TLS.

## Updating

1. Download the release archive and check its SHA-256 against the release notes.
2. Extract it to an empty directory and run (Clang must be on `PATH`, or
   pass its path with `--clang`; the generator needs it even without
   `--verify`):

   ```sh
   python -u tools/mbedtls_amalgamate.py "./mbedtls-3.6.8" --verify
   ```

   with your extraction path in place of `./mbedtls-3.6.8`. It applies
   `PATCHES` (if any) to a copy of the tree first, and stops if an anchor is
   no longer there exactly once. `--verify` preprocesses every unit for eight
   targets (Linux x86-64 and AArch64, Windows MSVC x64 and Arm64, MinGW,
   macOS x86-64 and Arm64, and FreeBSD), once from the patched upstream tree
   and once from the `.inc`, against empty stand-ins for the system headers,
   and fails unless both give the same preprocessing tokens and the same
   errors. Whitespace between tokens is ignored; string and character
   literals are compared whole. It doesn't compile the units against each
   target's real SDK.

   Each `.inc` banner keeps the copyright notices of the upstream files it
   was built from, since the generator strips their comments.
3. Update `UPSTREAM.json`, then run the TLS suite test (`tests/suite/13_tls`).
