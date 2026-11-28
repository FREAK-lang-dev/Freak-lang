/* FREAK's mbedTLS 3.6 build configuration.

   The upstream default (include/mbedtls/mbedtls_config.h) with everything a
   TLS 1.2 / 1.3 client and server over FREAK's own sockets doesn't use taken
   out: DTLS, the BSD socket and timing modules, self tests, debug output,
   PSK and static-RSA/DH key exchanges, legacy ciphers, X.509 writing and
   persistent PSA key storage. Hardware AES (AES-NI, Armv8 crypto), AES-GCM,
   ChaCha20-Poly1305, ECDHE over X25519/P-256/P-384/P-521, ECDSA and RSA
   certificates, SNI, ALPN and session tickets stay on. */
#include "mbedtls/mbedtls_config.h"

#undef MBEDTLS_SELF_TEST
#undef MBEDTLS_DEBUG_C
#undef MBEDTLS_NET_C
#undef MBEDTLS_TIMING_C
#undef MBEDTLS_SSL_PROTO_DTLS
#undef MBEDTLS_SSL_DTLS_ANTI_REPLAY
#undef MBEDTLS_SSL_DTLS_HELLO_VERIFY
#undef MBEDTLS_SSL_DTLS_SRTP
#undef MBEDTLS_SSL_DTLS_CLIENT_PORT_REUSE
#undef MBEDTLS_SSL_DTLS_CONNECTION_ID
#undef MBEDTLS_SSL_COOKIE_C
#undef MBEDTLS_SSL_CACHE_C
#undef MBEDTLS_SSL_CONTEXT_SERIALIZATION
#undef MBEDTLS_SSL_RENEGOTIATION
#undef MBEDTLS_SSL_EARLY_DATA
#undef MBEDTLS_CAMELLIA_C
#undef MBEDTLS_ARIA_C
#undef MBEDTLS_DES_C
#undef MBEDTLS_LMS_C
#undef MBEDTLS_NIST_KW_C
#undef MBEDTLS_CMAC_C
#undef MBEDTLS_CCM_C
#undef MBEDTLS_RIPEMD160_C
#undef MBEDTLS_PKCS7_C
#undef MBEDTLS_X509_CSR_PARSE_C
#undef MBEDTLS_X509_CSR_WRITE_C
#undef MBEDTLS_X509_CRT_WRITE_C
#undef MBEDTLS_X509_CREATE_C
#undef MBEDTLS_PEM_WRITE_C
#undef MBEDTLS_PSA_CRYPTO_STORAGE_C
#undef MBEDTLS_PSA_ITS_FILE_C
#undef MBEDTLS_PSA_CRYPTO_SE_C
#undef MBEDTLS_ECJPAKE_C
#undef MBEDTLS_DHM_C
#undef MBEDTLS_ECP_DP_SECP192R1_ENABLED
#undef MBEDTLS_ECP_DP_SECP224R1_ENABLED
#undef MBEDTLS_ECP_DP_SECP192K1_ENABLED
#undef MBEDTLS_ECP_DP_SECP224K1_ENABLED
#undef MBEDTLS_ECP_DP_SECP256K1_ENABLED
#undef MBEDTLS_ECP_DP_BP256R1_ENABLED
#undef MBEDTLS_ECP_DP_BP384R1_ENABLED
#undef MBEDTLS_ECP_DP_BP512R1_ENABLED
#undef MBEDTLS_ECP_DP_CURVE448_ENABLED
#undef MBEDTLS_KEY_EXCHANGE_PSK_ENABLED
#undef MBEDTLS_KEY_EXCHANGE_DHE_PSK_ENABLED
#undef MBEDTLS_KEY_EXCHANGE_ECDHE_PSK_ENABLED
#undef MBEDTLS_KEY_EXCHANGE_RSA_PSK_ENABLED
#undef MBEDTLS_KEY_EXCHANGE_DHE_RSA_ENABLED
#undef MBEDTLS_KEY_EXCHANGE_RSA_ENABLED
#undef MBEDTLS_KEY_EXCHANGE_ECDH_ECDSA_ENABLED
#undef MBEDTLS_KEY_EXCHANGE_ECDH_RSA_ENABLED
#undef MBEDTLS_KEY_EXCHANGE_ECJPAKE_ENABLED
#undef MBEDTLS_SSL_TLS1_3_KEY_EXCHANGE_MODE_PSK_ENABLED
#undef MBEDTLS_SSL_TLS1_3_KEY_EXCHANGE_MODE_PSK_EPHEMERAL_ENABLED

/* Armv8 SHA-256 instructions when the CPU has them (checked at run time). */
#define MBEDTLS_SHA256_USE_ARMV8_A_CRYPTO_IF_PRESENT

/* Buffers follow a negotiated maximum fragment length. Both directions keep
   the 16 KiB the TLS spec allows: a smaller outgoing buffer would break
   servers whose certificate chain doesn't fit in one record. */
#define MBEDTLS_SSL_VARIABLE_BUFFER_LENGTH

/* Entropy comes from the FREAK runtime's OS source (freak_tls.c supplies
   mbedtls_hardware_poll), so mbedTLS needs no bcrypt import library. */
#define MBEDTLS_NO_PLATFORM_ENTROPY
#define MBEDTLS_ENTROPY_HARDWARE_ALT

/* Clang on the MSVC runtime has no __udivti3 to link against, so bignum
   must not divide 128-bit values there (it uses its portable path). */
#if defined(_MSC_VER)
#define MBEDTLS_NO_UDBL_DIVISION
#endif
