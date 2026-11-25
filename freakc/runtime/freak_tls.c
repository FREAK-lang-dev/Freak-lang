/* ===================================================================
   FREAK runtime — std::tls (optional unit)
   ===================================================================
   TLS 1.2 / 1.3 for clients and servers over FREAK's own sockets, built on
   the vendored mbedTLS 3.6 LTS (third_party/mbedtls). The CLI compiles this
   file plus freak_tls_core.c and freak_tls_extra.c only for programs that
   `use std::tls`, so other programs never carry mbedTLS.

   Two faces over one implementation:
   - freak_tls_c_api (freak_runtime.h): plain C calls on a socket the caller
     owns, for runtime code such as the http_server event loop;
   - freak_tls_* int64 externs: the handle API that std/tls.fk wraps, where a
     session rides on a std TCP handle.

   Every call is single-threaded, like the rest of the V3.5 runtime tables.
   =================================================================== */

/* mbedTLS's TLS 1.3 key schedule, with the public headers this file uses.
   It comes first: it carries the FREAK mbedTLS configuration and opens the
   library's private fields to this file, which the write path reads. */
#ifdef _WIN32
/* winsock2.h must come before any windows.h the library pulls in. */
#include <winsock2.h>
#include <ws2tcpip.h>
#endif
#include "third_party/mbedtls/mbedtls_keys.inc"

#include "freak_runtime.h"

#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <wincrypt.h>
#else
#include <fcntl.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>
#endif



/* ------------------------------------------------------------------ */
/*  Shared state                                                       */
/* ------------------------------------------------------------------ */

static char freak_tls_global_error[256] = "";
static int freak_tls_ready = 0;          /* psa_crypto_init done */
static mbedtls_x509_crt freak_tls_system_roots;
static int freak_tls_system_roots_state = 0; /* 0 untried, 1 loaded, -1 none */
static char freak_tls_system_roots_error[160] = "";

static void freak_tls_set_global_error(const char *message) {
    snprintf(freak_tls_global_error, sizeof(freak_tls_global_error), "%s", message);
}

static void freak_tls_describe(char *out, size_t size, const char *what, int code) {
    char detail[160];
    mbedtls_strerror(code, detail, sizeof(detail));
    snprintf(out, size, "%s: %s (-0x%04x)", what, detail, (unsigned)(-code));
}

static int freak_tls_rng(void *context, unsigned char *out, size_t length) {
    (void)context;
    freak_tls_bridge_random(out, length);
    return 0;
}

/* mbedTLS's entropy source (MBEDTLS_ENTROPY_HARDWARE_ALT): the runtime's
   OS generator, which stops the program rather than return weak bytes. */
int mbedtls_hardware_poll(void *data, unsigned char *output, size_t length, size_t *olen) {
    (void)data;
    freak_tls_bridge_random(output, length);
    *olen = length;
    return 0;
}

static int freak_tls_init(void) {
    if (freak_tls_ready) return 1;
    psa_status_t status = psa_crypto_init();
    if (status != PSA_SUCCESS) {
        char message[96];
        snprintf(message, sizeof(message), "the TLS crypto layer failed to start (PSA status %d)", (int)status);
        freak_tls_set_global_error(message);
        return 0;
    }
    freak_tls_ready = 1;
    return 1;
}

/* ------------------------------------------------------------------ */
/*  System trust store                                                 */
/* ------------------------------------------------------------------ */

static int freak_tls_try_file(mbedtls_x509_crt *chain, const char *path) {
    if (!path || !*path) return 0;
    FILE *probe = fopen(path, "rb");
    if (!probe) return 0;
    fclose(probe);
    /* parse_file gives back how many certificates it skipped (>0) or an
       error (<0); a bundle with a few odd entries still loads the rest. */
    int before = 0;
    for (mbedtls_x509_crt *c = chain; c && c->raw.p; c = c->next) before++;
    mbedtls_x509_crt_parse_file(chain, path);
    int after = 0;
    for (mbedtls_x509_crt *c = chain; c && c->raw.p; c = c->next) after++;
    return after > before;
}

static int freak_tls_try_dir(mbedtls_x509_crt *chain, const char *path) {
    if (!path || !*path) return 0;
    int before = 0;
    for (mbedtls_x509_crt *c = chain; c && c->raw.p; c = c->next) before++;
    mbedtls_x509_crt_parse_path(chain, path);
    int after = 0;
    for (mbedtls_x509_crt *c = chain; c && c->raw.p; c = c->next) after++;
    return after > before;
}

/* The OS trust store, loaded once: SSL_CERT_FILE / SSL_CERT_DIR when set,
   else the Windows ROOT store, else the usual bundle paths of Linux, the
   BSDs and macOS (/etc/ssl/cert.pem), else /etc/ssl/certs. */
static mbedtls_x509_crt *freak_tls_roots(void) {
    if (freak_tls_system_roots_state == 1) return &freak_tls_system_roots;
    if (freak_tls_system_roots_state == -1) return NULL;
    mbedtls_x509_crt_init(&freak_tls_system_roots);
    int loaded = 0;
    const char *env_file = getenv("SSL_CERT_FILE");
    const char *env_dir = getenv("SSL_CERT_DIR");
    if ((env_file && *env_file) || (env_dir && *env_dir)) {
        loaded |= freak_tls_try_file(&freak_tls_system_roots, env_file);
        loaded |= freak_tls_try_dir(&freak_tls_system_roots, env_dir);
    } else {
#ifdef _WIN32
        /* crypt32 is looked up at run time, so programs need no extra
           import library on MSVC or MinGW toolchains. */
        typedef HCERTSTORE (WINAPI *open_fn)(HCRYPTPROV_LEGACY, LPCWSTR);
        typedef PCCERT_CONTEXT (WINAPI *enum_fn)(HCERTSTORE, PCCERT_CONTEXT);
        typedef BOOL (WINAPI *close_fn)(HCERTSTORE, DWORD);
        HMODULE crypt32 = LoadLibraryW(L"crypt32.dll");
        open_fn open_store = crypt32 ? (open_fn)(void *)GetProcAddress(crypt32, "CertOpenSystemStoreW") : NULL;
        enum_fn next_cert = crypt32 ? (enum_fn)(void *)GetProcAddress(crypt32, "CertEnumCertificatesInStore") : NULL;
        close_fn close_store = crypt32 ? (close_fn)(void *)GetProcAddress(crypt32, "CertCloseStore") : NULL;
        HCERTSTORE store = open_store && next_cert && close_store ? open_store(0, L"ROOT") : NULL;
        if (store) {
            PCCERT_CONTEXT cert = NULL;
            while ((cert = next_cert(store, cert)) != NULL) {
                if (cert->dwCertEncodingType & X509_ASN_ENCODING) {
                    if (mbedtls_x509_crt_parse_der(&freak_tls_system_roots,
                            cert->pbCertEncoded, cert->cbCertEncoded) == 0) loaded = 1;
                }
            }
            close_store(store, 0);
        }
#else
        static const char *const bundles[] = {
            "/etc/ssl/certs/ca-certificates.crt",                 /* Debian, Ubuntu, Arch, Gentoo */
            "/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem",  /* Fedora, RHEL */
            "/etc/pki/tls/certs/ca-bundle.crt",                   /* older RHEL, CentOS */
            "/etc/ssl/ca-bundle.pem",                             /* openSUSE */
            "/etc/ssl/cert.pem",                                  /* macOS, Alpine, OpenBSD */
            "/usr/local/etc/ssl/cert.pem",                        /* FreeBSD */
            "/usr/local/share/certs/ca-root-nss.crt",             /* FreeBSD ports */
            NULL
        };
        for (int i = 0; bundles[i] && !loaded; i++) {
            loaded = freak_tls_try_file(&freak_tls_system_roots, bundles[i]);
        }
        if (!loaded) loaded = freak_tls_try_dir(&freak_tls_system_roots, "/etc/ssl/certs");
#endif
    }
    if (!loaded) {
        mbedtls_x509_crt_free(&freak_tls_system_roots);
        freak_tls_system_roots_state = -1;
        snprintf(freak_tls_system_roots_error, sizeof(freak_tls_system_roots_error),
                 "no trusted root certificates were found on this system (set SSL_CERT_FILE to a PEM bundle)");
        return NULL;
    }
    freak_tls_system_roots_state = 1;
    return &freak_tls_system_roots;
}

/* ------------------------------------------------------------------ */
/*  Configs                                                            */
/* ------------------------------------------------------------------ */

enum { FREAK_TLS_VERIFY_NONE = 0, FREAK_TLS_VERIFY_CHAIN = 1, FREAK_TLS_VERIFY_FULL = 2 };

struct freak_tls_config {
    mbedtls_ssl_config conf;
    mbedtls_x509_crt own_cert;
    mbedtls_pk_context own_key;
    mbedtls_x509_crt custom_ca;
    mbedtls_ssl_ticket_context ticket;
    int has_custom_ca;
    int has_ticket;
    int is_server;
    int verify_mode;
    int refs;          /* the handle (if any) + every live connection */
    int64_t handle;    /* 0 once the handle is released */
    char *alpn_text;   /* "h2\0http/1.1\0" */
    const char **alpn; /* NULL-terminated list into alpn_text */
};

static void freak_tls_config_unref(freak_tls_config *config) {
    if (!config || --config->refs > 0) return;
    mbedtls_ssl_config_free(&config->conf);
    mbedtls_x509_crt_free(&config->own_cert);
    mbedtls_pk_free(&config->own_key);
    mbedtls_x509_crt_free(&config->custom_ca);
    if (config->has_ticket) mbedtls_ssl_ticket_free(&config->ticket);
    free(config->alpn_text);
    free(config->alpn);
    free(config);
}

/* "h2,http/1.1" -> a NULL-terminated list mbedTLS can keep pointing at. */
static int freak_tls_config_set_alpn(freak_tls_config *config, const unsigned char *text, size_t length) {
    if (length == 0) return 1;
    size_t count = 1;
    for (size_t i = 0; i < length; i++) if (text[i] == ',') count++;
    config->alpn_text = (char *)malloc(length + 1);
    config->alpn = (const char **)calloc(count + 1, sizeof(char *));
    if (!config->alpn_text || !config->alpn) {
        freak_tls_set_global_error("out of memory reading the ALPN list");
        return 0;
    }
    memcpy(config->alpn_text, text, length);
    config->alpn_text[length] = 0;
    size_t n = 0;
    char *start = config->alpn_text;
    for (size_t i = 0; i <= length; i++) {
        if (i == length || config->alpn_text[i] == ',') {
            config->alpn_text[i] = 0;
            size_t name = strlen(start);
            if (name == 0 || name > 255) {
                freak_tls_set_global_error("each ALPN protocol name must be 1 to 255 bytes");
                return 0;
            }
            config->alpn[n++] = start;
            start = config->alpn_text + i + 1;
        }
    }
    config->alpn[n] = NULL;
    int code = mbedtls_ssl_conf_alpn_protocols(&config->conf, config->alpn);
    if (code != 0) {
        char message[200];
        freak_tls_describe(message, sizeof(message), "bad ALPN list", code);
        freak_tls_set_global_error(message);
        return 0;
    }
    return 1;
}

/* Verify the chain but not the name (verify-ca): the hostname still goes
   out as SNI, so only the name check is dropped, at the leaf. */
static int freak_tls_verify_chain_only(void *context, mbedtls_x509_crt *cert, int depth, uint32_t *flags) {
    (void)context; (void)cert;
    if (depth == 0) *flags &= ~(uint32_t)MBEDTLS_X509_BADCERT_CN_MISMATCH;
    return 0;
}

static freak_tls_config *freak_tls_config_alloc(int endpoint) {
    if (!freak_tls_init()) return NULL;
    freak_tls_config *config = (freak_tls_config *)calloc(1, sizeof(freak_tls_config));
    if (!config) { freak_tls_set_global_error("out of memory creating a TLS config"); return NULL; }
    mbedtls_ssl_config_init(&config->conf);
    mbedtls_x509_crt_init(&config->own_cert);
    mbedtls_pk_init(&config->own_key);
    mbedtls_x509_crt_init(&config->custom_ca);
    config->refs = 1;
    config->is_server = endpoint == MBEDTLS_SSL_IS_SERVER;
    int code = mbedtls_ssl_config_defaults(&config->conf, endpoint,
        MBEDTLS_SSL_TRANSPORT_STREAM, MBEDTLS_SSL_PRESET_DEFAULT);
    if (code != 0) {
        char message[200];
        freak_tls_describe(message, sizeof(message), "TLS config defaults failed", code);
        freak_tls_set_global_error(message);
        freak_tls_config_unref(config);
        return NULL;
    }
    /* AES-GCM first (hardware AES on x86 and Armv8), ChaCha20-Poly1305 for
       peers without it; forward-secret ECDHE only. */
    static const int suites[] = {
        MBEDTLS_TLS1_3_AES_128_GCM_SHA256,
        MBEDTLS_TLS1_3_AES_256_GCM_SHA384,
        MBEDTLS_TLS1_3_CHACHA20_POLY1305_SHA256,
        MBEDTLS_TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,
        MBEDTLS_TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,
        MBEDTLS_TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,
        MBEDTLS_TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
        MBEDTLS_TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256,
        MBEDTLS_TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256,
        0
    };
    mbedtls_ssl_conf_ciphersuites(&config->conf, suites);
    mbedtls_ssl_conf_rng(&config->conf, freak_tls_rng, NULL);
    mbedtls_ssl_conf_min_tls_version(&config->conf, MBEDTLS_SSL_VERSION_TLS1_2);
    mbedtls_ssl_conf_max_tls_version(&config->conf, MBEDTLS_SSL_VERSION_TLS1_3);
    return config;
}

static freak_tls_config *freak_tls_make_client_config(
        const unsigned char *alpn, size_t alpn_length, int mode,
        const unsigned char *ca, size_t ca_length) {
    if (mode < FREAK_TLS_VERIFY_NONE || mode > FREAK_TLS_VERIFY_FULL) {
        freak_tls_set_global_error("verify mode must be 0 (none), 1 (chain) or 2 (chain and hostname)");
        return NULL;
    }
    freak_tls_config *config = freak_tls_config_alloc(MBEDTLS_SSL_IS_CLIENT);
    if (!config) return NULL;
    config->verify_mode = mode;
    if (mode == FREAK_TLS_VERIFY_NONE) {
        mbedtls_ssl_conf_authmode(&config->conf, MBEDTLS_SSL_VERIFY_NONE);
    } else {
        mbedtls_x509_crt *roots = NULL;
        if (ca_length > 0) {
            /* PEM parsing needs the terminating NUL inside the length. */
            unsigned char *copy = (unsigned char *)malloc(ca_length + 1);
            if (!copy) { freak_tls_set_global_error("out of memory reading CA certificates"); freak_tls_config_unref(config); return NULL; }
            memcpy(copy, ca, ca_length);
            copy[ca_length] = 0;
            int code = mbedtls_x509_crt_parse(&config->custom_ca, copy, ca_length + 1);
            free(copy);
            if (code < 0 || !config->custom_ca.raw.p) {
                char message[200];
                freak_tls_describe(message, sizeof(message), "could not read the CA certificates", code < 0 ? code : MBEDTLS_ERR_X509_INVALID_FORMAT);
                freak_tls_set_global_error(message);
                freak_tls_config_unref(config);
                return NULL;
            }
            config->has_custom_ca = 1;
            roots = &config->custom_ca;
        } else {
            roots = freak_tls_roots();
            if (!roots) {
                freak_tls_set_global_error(freak_tls_system_roots_error);
                freak_tls_config_unref(config);
                return NULL;
            }
        }
        mbedtls_ssl_conf_authmode(&config->conf, MBEDTLS_SSL_VERIFY_REQUIRED);
        mbedtls_ssl_conf_ca_chain(&config->conf, roots, NULL);
        if (mode == FREAK_TLS_VERIFY_CHAIN) {
            mbedtls_ssl_conf_verify(&config->conf, freak_tls_verify_chain_only, NULL);
        }
    }
    if (!freak_tls_config_set_alpn(config, alpn, alpn_length)) { freak_tls_config_unref(config); return NULL; }
    return config;
}

static freak_tls_config *freak_tls_make_server_config(
        const unsigned char *cert, size_t cert_length,
        const unsigned char *key, size_t key_length,
        const unsigned char *alpn, size_t alpn_length) {
    freak_tls_config *config = freak_tls_config_alloc(MBEDTLS_SSL_IS_SERVER);
    if (!config) return NULL;
    char message[220];
    unsigned char *copy = (unsigned char *)malloc((cert_length > key_length ? cert_length : key_length) + 1);
    if (!copy) { freak_tls_set_global_error("out of memory reading the certificate"); freak_tls_config_unref(config); return NULL; }
    memcpy(copy, cert, cert_length);
    copy[cert_length] = 0;
    int code = mbedtls_x509_crt_parse(&config->own_cert, copy, cert_length + 1);
    if (code < 0 || !config->own_cert.raw.p) {
        free(copy);
        freak_tls_describe(message, sizeof(message), "could not read the server certificate", code < 0 ? code : MBEDTLS_ERR_X509_INVALID_FORMAT);
        freak_tls_set_global_error(message);
        freak_tls_config_unref(config);
        return NULL;
    }
    memcpy(copy, key, key_length);
    copy[key_length] = 0;
    code = mbedtls_pk_parse_key(&config->own_key, copy, key_length + 1, NULL, 0, freak_tls_rng, NULL);
    mbedtls_platform_zeroize(copy, key_length + 1);
    free(copy);
    if (code != 0) {
        freak_tls_describe(message, sizeof(message), "could not read the private key", code);
        freak_tls_set_global_error(message);
        freak_tls_config_unref(config);
        return NULL;
    }
    code = mbedtls_ssl_conf_own_cert(&config->conf, &config->own_cert, &config->own_key);
    if (code != 0) {
        freak_tls_describe(message, sizeof(message), "the certificate and key don't fit together", code);
        freak_tls_set_global_error(message);
        freak_tls_config_unref(config);
        return NULL;
    }
    if (mbedtls_pk_check_pair(&config->own_cert.pk, &config->own_key, freak_tls_rng, NULL) != 0) {
        freak_tls_set_global_error("the private key doesn't belong to the certificate");
        freak_tls_config_unref(config);
        return NULL;
    }
    mbedtls_ssl_conf_authmode(&config->conf, MBEDTLS_SSL_VERIFY_NONE);
#if defined(MBEDTLS_SSL_SESSION_TICKETS) && defined(MBEDTLS_SSL_TICKET_C)
    /* Session tickets so returning clients skip the full handshake. Keys
       live in memory only and rotate every 12 hours. */
    mbedtls_ssl_ticket_init(&config->ticket);
    if (mbedtls_ssl_ticket_setup(&config->ticket, freak_tls_rng, NULL,
            MBEDTLS_CIPHER_AES_256_GCM, 43200) == 0) {
        config->has_ticket = 1;
        mbedtls_ssl_conf_session_tickets_cb(&config->conf,
            mbedtls_ssl_ticket_write, mbedtls_ssl_ticket_parse, &config->ticket);
    } else {
        mbedtls_ssl_ticket_free(&config->ticket);
    }
#endif
    if (!freak_tls_config_set_alpn(config, alpn, alpn_length)) { freak_tls_config_unref(config); return NULL; }
    return config;
}

/* ------------------------------------------------------------------ */
/*  Connections                                                        */
/* ------------------------------------------------------------------ */

struct freak_tls_conn {
    mbedtls_ssl_context ssl;
    freak_tls_config *config;
    uintptr_t native;     /* the socket when tcp == 0 */
    int64_t tcp;          /* FREAK TCP handle, looked up on every I/O */
    int nonblocking;
    int status;           /* last result code (0 ok, FREAK_TLS_*) */
    int handshake_done;
    int close_sent;       /* our close_notify went out */
    int peer_notified;    /* the peer's close_notify arrived */
    int read_closed;      /* the peer finished: close_notify, EOF or reset */
    size_t pending_write; /* bytes queued by a write that hit WANT_WRITE */
    char message[256];
};

static int freak_tls_conn_socket(freak_tls_conn *conn, uintptr_t *native) {
    if (conn->tcp == 0) { *native = conn->native; return 1; }
    return freak_tls_bridge_socket(conn->tcp, native) ? 1 : 0;
}

static int freak_tls_socket_would_block(void) {
#ifdef _WIN32
    return WSAGetLastError() == WSAEWOULDBLOCK;
#else
    return errno == EAGAIN || errno == EWOULDBLOCK;
#endif
}

static int freak_tls_socket_interrupted(void) {
#ifdef _WIN32
    return WSAGetLastError() == WSAEINTR;
#else
    return errno == EINTR;
#endif
}

static int freak_tls_socket_timed_out(void) {
#ifdef _WIN32
    return WSAGetLastError() == WSAETIMEDOUT;
#else
    return 0;
#endif
}

static int freak_tls_socket_reset(void) {
#ifdef _WIN32
    int e = WSAGetLastError();
    return e == WSAECONNRESET || e == WSAECONNABORTED;
#else
    return errno == ECONNRESET || errno == EPIPE;
#endif
}

static int freak_tls_native_set_nonblocking(uintptr_t native, int on) {
#ifdef _WIN32
    u_long mode = on ? 1 : 0;
    return ioctlsocket((SOCKET)native, FIONBIO, &mode) == 0;
#else
    int flags = fcntl((int)native, F_GETFL, 0);
    if (flags < 0) return 0;
    flags = on ? (flags | O_NONBLOCK) : (flags & ~O_NONBLOCK);
    return fcntl((int)native, F_SETFL, flags) == 0;
#endif
}

static int freak_tls_bio_send(void *context, const unsigned char *data, size_t length) {
    freak_tls_conn *conn = (freak_tls_conn *)context;
    uintptr_t native;
    if (!freak_tls_conn_socket(conn, &native)) return MBEDTLS_ERR_NET_INVALID_CONTEXT;
    int chunk = length > (size_t)INT_MAX ? INT_MAX : (int)length;
    for (;;) {
#ifdef _WIN32
        int sent = send((SOCKET)native, (const char *)data, chunk, 0);
#elif defined(MSG_NOSIGNAL)
        ssize_t sent = send((int)native, data, (size_t)chunk, MSG_NOSIGNAL);
#else
        ssize_t sent = send((int)native, data, (size_t)chunk, 0);
#endif
        if (sent >= 0) return (int)sent;
        if (freak_tls_socket_interrupted()) continue;
        if (freak_tls_socket_would_block()) return conn->nonblocking ? MBEDTLS_ERR_SSL_WANT_WRITE : MBEDTLS_ERR_SSL_TIMEOUT;
        if (freak_tls_socket_timed_out()) return MBEDTLS_ERR_SSL_TIMEOUT;
        if (freak_tls_socket_reset()) return MBEDTLS_ERR_NET_CONN_RESET;
        return MBEDTLS_ERR_NET_SEND_FAILED;
    }
}

static int freak_tls_bio_recv(void *context, unsigned char *out, size_t length) {
    freak_tls_conn *conn = (freak_tls_conn *)context;
    uintptr_t native;
    if (!freak_tls_conn_socket(conn, &native)) return MBEDTLS_ERR_NET_INVALID_CONTEXT;
    int chunk = length > (size_t)INT_MAX ? INT_MAX : (int)length;
    for (;;) {
#ifdef _WIN32
        int got = recv((SOCKET)native, (char *)out, chunk, 0);
#else
        ssize_t got = recv((int)native, out, (size_t)chunk, 0);
#endif
        if (got >= 0) return (int)got;
        if (freak_tls_socket_interrupted()) continue;
        if (freak_tls_socket_would_block()) return conn->nonblocking ? MBEDTLS_ERR_SSL_WANT_READ : MBEDTLS_ERR_SSL_TIMEOUT;
        if (freak_tls_socket_timed_out()) return MBEDTLS_ERR_SSL_TIMEOUT;
        if (freak_tls_socket_reset()) return MBEDTLS_ERR_NET_CONN_RESET;
        return MBEDTLS_ERR_NET_RECV_FAILED;
    }
}

static freak_tls_conn *freak_tls_conn_make(freak_tls_config *config, int64_t tcp, uintptr_t native) {
    freak_tls_conn *conn = (freak_tls_conn *)calloc(1, sizeof(freak_tls_conn));
    if (!conn) { freak_tls_set_global_error("out of memory creating a TLS connection"); return NULL; }
    mbedtls_ssl_init(&conn->ssl);
    int code = mbedtls_ssl_setup(&conn->ssl, &config->conf);
    if (code != 0) {
        char message[200];
        freak_tls_describe(message, sizeof(message), "TLS connection setup failed", code);
        freak_tls_set_global_error(message);
        mbedtls_ssl_free(&conn->ssl);
        free(conn);
        return NULL;
    }
    config->refs++;
    conn->config = config;
    conn->tcp = tcp;
    conn->native = native;
    mbedtls_ssl_set_bio(&conn->ssl, conn, freak_tls_bio_send, freak_tls_bio_recv, NULL);
    return conn;
}

static void freak_tls_conn_destroy(freak_tls_conn *conn) {
    if (!conn) return;
    mbedtls_ssl_free(&conn->ssl);
    freak_tls_config_unref(conn->config);
    free(conn);
}

/* An mbedTLS result as a FREAK_TLS_* code, keeping the reason. */
static int freak_tls_conn_fail(freak_tls_conn *conn, int code, const char *what) {
    switch (code) {
    case MBEDTLS_ERR_SSL_WANT_READ: conn->status = FREAK_TLS_WANT_READ; return FREAK_TLS_WANT_READ;
    case MBEDTLS_ERR_SSL_WANT_WRITE: conn->status = FREAK_TLS_WANT_WRITE; return FREAK_TLS_WANT_WRITE;
    case MBEDTLS_ERR_SSL_TIMEOUT:
        conn->status = FREAK_TLS_TIMED_OUT;
        snprintf(conn->message, sizeof(conn->message), "%s: timed out", what);
        return FREAK_TLS_TIMED_OUT;
    case MBEDTLS_ERR_SSL_PEER_CLOSE_NOTIFY:
        conn->peer_notified = 1;
        /* fall through */
    case MBEDTLS_ERR_SSL_CONN_EOF:
    case MBEDTLS_ERR_NET_CONN_RESET:
        conn->read_closed = 1;
        conn->status = FREAK_TLS_CLOSED;
        snprintf(conn->message, sizeof(conn->message), "%s: the peer closed the connection", what);
        return FREAK_TLS_CLOSED;
    default:
        break;
    }
    conn->status = FREAK_TLS_FAILED;
    if (code == MBEDTLS_ERR_X509_CERT_VERIFY_FAILED) {
        char info[200];
        uint32_t flags = mbedtls_ssl_get_verify_result(&conn->ssl);
        int n = mbedtls_x509_crt_verify_info(info, sizeof(info), "", flags);
        while (n > 0 && (info[n - 1] == '\n' || info[n - 1] == ' ')) info[--n] = 0;
        for (int i = 0; i < n; i++) if (info[i] == '\n') info[i] = ';';
        snprintf(conn->message, sizeof(conn->message), "%s: certificate verify failed: %s", what, n > 0 ? info : "untrusted");
    } else if (code == MBEDTLS_ERR_NET_INVALID_CONTEXT) {
        snprintf(conn->message, sizeof(conn->message), "%s: the TCP socket is closed or failed", what);
    } else {
        freak_tls_describe(conn->message, sizeof(conn->message), what, code);
    }
    return FREAK_TLS_FAILED;
}

/* A send that timed out may have put part of a record on the wire, and the
   API has no way to retry that exact record, so the session ends there. */
static int freak_tls_conn_write_fail(freak_tls_conn *conn, int code, const char *what) {
    int result = freak_tls_conn_fail(conn, code, what);
    if (result == FREAK_TLS_TIMED_OUT && conn->ssl.MBEDTLS_PRIVATE(out_left) > 0) {
        conn->status = FREAK_TLS_FAILED;
        snprintf(conn->message, sizeof(conn->message), "%s: timed out partway through a record; the session can't continue", what);
    }
    return result;
}

static int freak_tls_conn_handshake(freak_tls_conn *conn) {
    if (conn->handshake_done) return 0;
    if (conn->status == FREAK_TLS_FAILED) return FREAK_TLS_FAILED;
    if (conn->read_closed) return FREAK_TLS_CLOSED;
    for (;;) {
        int code = mbedtls_ssl_handshake(&conn->ssl);
        if (code == 0) { conn->handshake_done = 1; conn->status = 0; return 0; }
#if defined(MBEDTLS_SSL_PROTO_TLS1_3) && defined(MBEDTLS_SSL_SESSION_TICKETS)
        if (code == MBEDTLS_ERR_SSL_RECEIVED_NEW_SESSION_TICKET) continue;
#endif
        return freak_tls_conn_fail(conn, code, "TLS handshake failed");
    }
}

static int freak_tls_conn_read(freak_tls_conn *conn, unsigned char *out, size_t count) {
    if (conn->status == FREAK_TLS_FAILED) return FREAK_TLS_FAILED;
    if (conn->read_closed) return 0;
    if (count == 0) return 0;
    if (count > (size_t)INT_MAX) count = (size_t)INT_MAX;
    for (;;) {
        int code = mbedtls_ssl_read(&conn->ssl, out, count);
        if (code > 0) { conn->status = 0; if (!conn->handshake_done) conn->handshake_done = mbedtls_ssl_is_handshake_over(&conn->ssl); return code; }
        if (code == 0) { conn->read_closed = 1; conn->status = FREAK_TLS_CLOSED; return 0; }
#if defined(MBEDTLS_SSL_PROTO_TLS1_3) && defined(MBEDTLS_SSL_SESSION_TICKETS)
        if (code == MBEDTLS_ERR_SSL_RECEIVED_NEW_SESSION_TICKET) continue;
#endif
        int result = freak_tls_conn_fail(conn, code, "TLS read failed");
        return result == FREAK_TLS_CLOSED ? 0 : result;
    }
}

static int freak_tls_conn_flush(freak_tls_conn *conn) {
    if (conn->pending_write == 0) return 0;
    /* With output still queued, mbedtls_ssl_write only flushes it and
       reports the queued length; it never reads the data argument. */
    int code = mbedtls_ssl_write(&conn->ssl, (const unsigned char *)"", conn->pending_write);
    if (code >= 0) {
        conn->pending_write = 0;
        if (conn->status == FREAK_TLS_WANT_READ || conn->status == FREAK_TLS_WANT_WRITE) conn->status = 0;
        return 0;
    }
    return freak_tls_conn_write_fail(conn, code, "TLS write failed");
}

static int freak_tls_conn_write(freak_tls_conn *conn, const unsigned char *data, size_t count) {
    if (conn->status == FREAK_TLS_FAILED) return FREAK_TLS_FAILED;
    if (conn->read_closed || conn->status == FREAK_TLS_CLOSED) return FREAK_TLS_CLOSED;
    if (conn->close_sent) {
        snprintf(conn->message, sizeof(conn->message), "TLS write failed: the session was closed");
        return FREAK_TLS_CLOSED;
    }
    /* Finish the handshake first. A write that runs it implicitly can hit
       WANT_WRITE with handshake records queued, and those must not be
       counted as accepted application bytes. */
    if (!conn->handshake_done) {
        int shaken = freak_tls_conn_handshake(conn);
        if (shaken != 0) return shaken;
    }
    if (conn->pending_write) {
        int flushed = freak_tls_conn_flush(conn);
        if (flushed != 0) return flushed;
    }
    if (count > (size_t)INT_MAX) count = (size_t)INT_MAX;
    size_t total = 0;
    while (total < count) {
        int code = mbedtls_ssl_write(&conn->ssl, data + total, count - total);
        if (code > 0) { total += (size_t)code; continue; }
        if (code == MBEDTLS_ERR_SSL_WANT_WRITE && conn->ssl.MBEDTLS_PRIVATE(out_left) > 0) {
            /* The record is encrypted and queued; only the socket is full.
               Those bytes count as accepted; conn_flush sends them later. */
            size_t queued = count - total;
            int limit = mbedtls_ssl_get_max_out_record_payload(&conn->ssl);
            if (limit > 0 && queued > (size_t)limit) queued = (size_t)limit;
            conn->pending_write = queued;
            total += queued;
            conn->status = FREAK_TLS_WANT_WRITE;
            break;
        }
        if (total > 0) {
            /* Report what went out; the error comes back on the next call. */
            freak_tls_conn_write_fail(conn, code, "TLS write failed");
            if (conn->status == FREAK_TLS_WANT_READ || conn->status == FREAK_TLS_WANT_WRITE) conn->status = 0;
            break;
        }
        return freak_tls_conn_write_fail(conn, code, "TLS write failed");
    }
    if (!conn->handshake_done) conn->handshake_done = mbedtls_ssl_is_handshake_over(&conn->ssl);
    /* Nothing left queued: an earlier WANT_* no longer describes the session. */
    if (conn->pending_write == 0 && (conn->status == FREAK_TLS_WANT_READ || conn->status == FREAK_TLS_WANT_WRITE)) conn->status = 0;
    return (int)total;
}

static bool freak_tls_conn_wants_write(freak_tls_conn *conn) {
    return conn->pending_write > 0 || conn->ssl.MBEDTLS_PRIVATE(out_left) > 0;
}

static size_t freak_tls_conn_pending(freak_tls_conn *conn) {
    return mbedtls_ssl_get_bytes_avail(&conn->ssl);
}

static int freak_tls_conn_close(freak_tls_conn *conn) {
    if (conn->status == FREAK_TLS_FAILED || conn->close_sent) return 0;
    /* A peer that sent close_notify still waits for ours; a peer that just
       dropped the connection (EOF or reset) can't receive it. */
    if (conn->read_closed && !conn->peer_notified) return 0;
    if (conn->pending_write) {
        int flushed = freak_tls_conn_flush(conn);
        if (flushed != 0) return flushed == FREAK_TLS_CLOSED ? 0 : flushed;
    }
    int code = mbedtls_ssl_close_notify(&conn->ssl);
    if (code == 0) {
        /* Reads stay open so the caller can wait for the peer's close_notify. */
        conn->close_sent = 1;
        conn->status = conn->read_closed ? FREAK_TLS_CLOSED : 0;
        return 0;
    }
    int result = freak_tls_conn_write_fail(conn, code, "TLS close failed");
    return result == FREAK_TLS_CLOSED ? 0 : result;
}

static const char *freak_tls_conn_error(freak_tls_conn *conn) {
    return conn->message;
}

static const char *freak_tls_conn_alpn(freak_tls_conn *conn) {
    const char *protocol = mbedtls_ssl_get_alpn_protocol(&conn->ssl);
    return protocol ? protocol : "";
}

/* ------------------------------------------------------------------ */
/*  C API (for runtime code such as the http_server event loop)        */
/* ------------------------------------------------------------------ */

static freak_tls_config *freak_tls_config_lookup(int64_t handle);

static freak_tls_config *freak_tls_c_server_config(int64_t handle) {
    freak_tls_config *config = freak_tls_config_lookup(handle);
    return config && config->is_server ? config : NULL;
}

static freak_tls_conn *freak_tls_c_conn_new(freak_tls_config *config, uintptr_t native_socket) {
    if (!config) return NULL;
#if defined(__APPLE__) && defined(SO_NOSIGPIPE)
    int one = 1;
    setsockopt((int)native_socket, SOL_SOCKET, SO_NOSIGPIPE, &one, sizeof(one));
#endif
    freak_tls_conn *conn = freak_tls_conn_make(config, 0, native_socket);
    if (conn) conn->nonblocking = 1;
    return conn;
}

static const freak_tls_c_api freak_tls_c_api_table = {
    1,
    freak_tls_c_server_config,
    freak_tls_c_conn_new,
    freak_tls_conn_handshake,
    freak_tls_conn_read,
    freak_tls_conn_write,
    freak_tls_conn_flush,
    freak_tls_conn_wants_write,
    freak_tls_conn_pending,
    freak_tls_conn_close,
    freak_tls_conn_destroy,
    freak_tls_conn_error,
    freak_tls_conn_alpn,
};

__attribute__((constructor)) static void freak_tls_register(void) {
    freak_tls_api = &freak_tls_c_api_table;
}

/* ------------------------------------------------------------------ */
/*  Handles (std/tls.fk)                                               */
/* ------------------------------------------------------------------ */

#define FREAK_TLS_DOMAIN_MASK      UINT64_C(0xf000000000000000)
#define FREAK_TLS_SESSION_DOMAIN   UINT64_C(0xd000000000000000)
#define FREAK_TLS_CONFIG_DOMAIN    UINT64_C(0x7000000000000000)
#define FREAK_TLS_GENERATION_MAX   UINT32_C(0x0fffffff)

typedef struct {
    void *item;
    uint32_t generation;
} freak_tls_slot;

typedef struct {
    freak_tls_slot *slots;
    int64_t count;
    int64_t capacity;
    int64_t live;
    uint64_t domain;
} freak_tls_table;

static freak_tls_table freak_tls_sessions = { NULL, 0, 0, 0, FREAK_TLS_SESSION_DOMAIN };
static freak_tls_table freak_tls_configs = { NULL, 0, 0, 0, FREAK_TLS_CONFIG_DOMAIN };

static int64_t freak_tls_table_add(freak_tls_table *table, void *item) {
    int64_t slot = -1;
    for (int64_t i = 0; i < table->count; i++) {
        if (!table->slots[i].item && table->slots[i].generation < FREAK_TLS_GENERATION_MAX) { slot = i; break; }
    }
    if (slot < 0) {
        if (table->count == table->capacity) {
            int64_t capacity = table->capacity ? table->capacity * 2 : 16;
            if (capacity > (int64_t)UINT32_MAX) { fprintf(stderr, "FREAK: TLS handle table exhausted\n"); exit(1); }
            freak_tls_slot *grown = (freak_tls_slot *)realloc(table->slots, (size_t)capacity * sizeof(freak_tls_slot));
            if (!grown) { fprintf(stderr, "FREAK: out of memory growing the TLS handle table\n"); exit(1); }
            memset(grown + table->capacity, 0, (size_t)(capacity - table->capacity) * sizeof(freak_tls_slot));
            table->slots = grown;
            table->capacity = capacity;
        }
        slot = table->count++;
    }
    table->slots[slot].item = item;
    table->slots[slot].generation += 1;
    table->live += 1;
    return (int64_t)(table->domain | ((uint64_t)table->slots[slot].generation << 32) | (uint64_t)(uint32_t)slot);
}

static int64_t freak_tls_table_slot(freak_tls_table *table, int64_t handle) {
    uint64_t raw = (uint64_t)handle;
    if ((raw & FREAK_TLS_DOMAIN_MASK) != table->domain) return -1;
    int64_t slot = (int64_t)(uint32_t)(raw & UINT64_C(0xffffffff));
    uint32_t generation = (uint32_t)(raw >> 32) & FREAK_TLS_GENERATION_MAX;
    if (slot < 0 || slot >= table->count) return -1;
    if (!table->slots[slot].item || table->slots[slot].generation != generation) return -1;
    return slot;
}

static void *freak_tls_table_take(freak_tls_table *table, int64_t handle) {
    int64_t slot = freak_tls_table_slot(table, handle);
    if (slot < 0) return NULL;
    void *item = table->slots[slot].item;
    table->slots[slot].item = NULL;
    table->live -= 1;
    return item;
}

static freak_tls_config *freak_tls_config_lookup(int64_t handle) {
    int64_t slot = freak_tls_table_slot(&freak_tls_configs, handle);
    return slot < 0 ? NULL : (freak_tls_config *)freak_tls_configs.slots[slot].item;
}

static freak_tls_conn *freak_tls_session_require(int64_t handle, const char *operation) {
    int64_t slot = freak_tls_table_slot(&freak_tls_sessions, handle);
    if (slot < 0) {
        fprintf(stderr, "FREAK: invalid or stale TLS session handle in %s\n", operation);
        exit(1);
    }
    return (freak_tls_conn *)freak_tls_sessions.slots[slot].item;
}

static const unsigned char *freak_tls_view(int64_t buffer, size_t *length) {
    if (buffer == 0) { *length = 0; return (const unsigned char *)""; }
    return freak_tls_bridge_bytes(buffer, length);
}

static int64_t freak_tls_register_config(freak_tls_config *config) {
    if (!config) return 0;
    config->handle = freak_tls_table_add(&freak_tls_configs, config);
    return config->handle;
}

int64_t freak_tls_client_config_new(int64_t alpn, int64_t verify_mode, int64_t ca_pem) {
    size_t alpn_length = 0, ca_length = 0;
    const unsigned char *alpn_bytes = freak_tls_view(alpn, &alpn_length);
    const unsigned char *ca_bytes = freak_tls_view(ca_pem, &ca_length);
    if (!alpn_bytes || !ca_bytes) { freak_tls_set_global_error("a TLS config argument buffer has a failed status"); return 0; }
    return freak_tls_register_config(freak_tls_make_client_config(alpn_bytes, alpn_length, (int)verify_mode, ca_bytes, ca_length));
}

int64_t freak_tls_server_config_new(int64_t cert_pem, int64_t key_pem, int64_t alpn) {
    size_t cert_length = 0, key_length = 0, alpn_length = 0;
    const unsigned char *cert = freak_tls_view(cert_pem, &cert_length);
    const unsigned char *key = freak_tls_view(key_pem, &key_length);
    const unsigned char *alpn_bytes = freak_tls_view(alpn, &alpn_length);
    if (!cert || !key || !alpn_bytes) { freak_tls_set_global_error("a TLS config argument buffer has a failed status"); return 0; }
    if (cert_length == 0 || key_length == 0) { freak_tls_set_global_error("a TLS server needs a certificate and a private key"); return 0; }
    return freak_tls_register_config(freak_tls_make_server_config(cert, cert_length, key, key_length, alpn_bytes, alpn_length));
}

void freak_tls_config_release(int64_t handle) {
    freak_tls_config *config = (freak_tls_config *)freak_tls_table_take(&freak_tls_configs, handle);
    if (!config) return;
    config->handle = 0;
    freak_tls_config_unref(config);
}

static int64_t freak_tls_session_open(int64_t config_handle, int64_t tcp, int server,
                                      const unsigned char *host, size_t host_length) {
    freak_tls_config *config = freak_tls_config_lookup(config_handle);
    if (!config) { freak_tls_set_global_error("invalid or released TLS config"); return 0; }
    if (config->is_server != server) {
        freak_tls_set_global_error(server ? "tls_server needs a server config" : "tls_client needs a client config");
        return 0;
    }
    uintptr_t native;
    if (!freak_tls_bridge_socket(tcp, &native)) { freak_tls_set_global_error("the TCP socket is not an open connection"); return 0; }
    freak_tls_conn *conn = freak_tls_conn_make(config, tcp, native);
    if (!conn) return 0;
    if (!server) {
        if (host_length > 253 || memchr(host, 0, host_length)) {
            freak_tls_set_global_error("the TLS host name is too long or contains a NUL byte");
            freak_tls_conn_destroy(conn);
            return 0;
        }
        char name[256];
        memcpy(name, host, host_length);
        name[host_length] = 0;
        /* Mode 0 still sends the name as SNI; modes 1 and 2 also verify the
           certificate against it (mode 1 drops only the name match). */
        int code = 0;
        if (host_length > 0) code = mbedtls_ssl_set_hostname(&conn->ssl, name);
        else if (config->verify_mode == FREAK_TLS_VERIFY_FULL) {
            freak_tls_set_global_error("verify mode 2 needs the server's host name");
            freak_tls_conn_destroy(conn);
            return 0;
        } else code = mbedtls_ssl_set_hostname(&conn->ssl, NULL);
        if (code != 0) {
            char message[200];
            freak_tls_describe(message, sizeof(message), "bad TLS host name", code);
            freak_tls_set_global_error(message);
            freak_tls_conn_destroy(conn);
            return 0;
        }
    }
    return freak_tls_table_add(&freak_tls_sessions, conn);
}

int64_t freak_tls_client_new(int64_t config, int64_t tcp, int64_t host) {
    size_t host_length = 0;
    const unsigned char *host_bytes = freak_tls_view(host, &host_length);
    if (!host_bytes) { freak_tls_set_global_error("the host name buffer has a failed status"); return 0; }
    return freak_tls_session_open(config, tcp, 0, host_bytes, host_length);
}

int64_t freak_tls_server_new(int64_t config, int64_t tcp) {
    return freak_tls_session_open(config, tcp, 1, NULL, 0);
}

void freak_tls_set_nonblocking(int64_t session, int64_t on) {
    freak_tls_conn *conn = freak_tls_session_require(session, "tls_set_nonblocking");
    uintptr_t native;
    /* Switch the socket itself, so send/recv return instead of waiting. */
    if (!freak_tls_conn_socket(conn, &native) || !freak_tls_native_set_nonblocking(native, on != 0)) {
        snprintf(conn->message, sizeof(conn->message), "tls_set_nonblocking: could not change the socket's blocking mode");
        return;
    }
    conn->nonblocking = on != 0;
}

int64_t freak_tls_handshake(int64_t session) {
    return freak_tls_conn_handshake(freak_tls_session_require(session, "tls_handshake"));
}

int64_t freak_tls_send(int64_t session, int64_t data, int64_t offset, int64_t count) {
    freak_tls_conn *conn = freak_tls_session_require(session, "tls_send");
    size_t length = 0;
    const unsigned char *bytes = freak_tls_bridge_bytes(data, &length);
    if (!bytes || offset < 0 || count < 0 || (uint64_t)offset > length || (uint64_t)count > length - (uint64_t)offset) {
        snprintf(conn->message, sizeof(conn->message), "tls_send: bad buffer, offset or count");
        return FREAK_TLS_FAILED;
    }
    if (count == 0) return 0;
    return freak_tls_conn_write(conn, bytes + offset, (size_t)count);
}

int64_t freak_tls_flush(int64_t session) {
    return freak_tls_conn_flush(freak_tls_session_require(session, "tls_flush"));
}

int64_t freak_tls_receive(int64_t session, int64_t out, int64_t max_bytes) {
    freak_tls_conn *conn = freak_tls_session_require(session, "tls_receive");
    if (max_bytes <= 0) return 0;
    size_t want = (uint64_t)max_bytes > (uint64_t)INT_MAX ? (size_t)INT_MAX : (size_t)max_bytes;
    size_t avail = mbedtls_ssl_get_bytes_avail(&conn->ssl);
    /* Reserve what is already decrypted, or one record, not max_bytes. */
    size_t room = avail ? avail : MBEDTLS_SSL_IN_CONTENT_LEN;
    if (room > want) room = want;
    unsigned char *space = freak_tls_bridge_reserve(out, room);
    if (!space) {
        snprintf(conn->message, sizeof(conn->message), "tls_receive: the destination buffer can't grow");
        return FREAK_TLS_FAILED;
    }
    int got = freak_tls_conn_read(conn, space, room);
    if (got > 0) freak_tls_bridge_commit(out, (size_t)got);
    return got;
}

int64_t freak_tls_pending(int64_t session) {
    return (int64_t)freak_tls_conn_pending(freak_tls_session_require(session, "tls_pending"));
}

int64_t freak_tls_close_notify(int64_t session) {
    return freak_tls_conn_close(freak_tls_session_require(session, "tls_close"));
}

void freak_tls_release(int64_t session) {
    freak_tls_conn_destroy((freak_tls_conn *)freak_tls_table_take(&freak_tls_sessions, session));
}

int64_t freak_tls_status(int64_t session) {
    return freak_tls_session_require(session, "tls_status")->status;
}

int64_t freak_tls_verified(int64_t session) {
    freak_tls_conn *conn = freak_tls_session_require(session, "tls_verified");
    if (conn->config->is_server || conn->config->verify_mode == FREAK_TLS_VERIFY_NONE) return 0;
    if (!conn->handshake_done) return 0;
    return mbedtls_ssl_get_verify_result(&conn->ssl) == 0 ? 1 : 0;
}

static int64_t freak_tls_append_text(int64_t out, const char *text) {
    return freak_tls_bridge_append(out, (const unsigned char *)text, strlen(text)) ? 1 : 0;
}

/* 0 error message, 1 negotiated ALPN protocol, 2 TLS version,
   3 cipher suite, 4 the peer's certificate (DER). */
int64_t freak_tls_info(int64_t session, int64_t what, int64_t out) {
    freak_tls_conn *conn = freak_tls_session_require(session, "tls_info");
    switch (what) {
    case 0: return freak_tls_append_text(out, conn->message);
    case 1: return freak_tls_append_text(out, freak_tls_conn_alpn(conn));
    case 2: return freak_tls_append_text(out, conn->handshake_done ? mbedtls_ssl_get_version(&conn->ssl) : "");
    case 3: return freak_tls_append_text(out, conn->handshake_done ? mbedtls_ssl_get_ciphersuite(&conn->ssl) : "");
    case 4: {
        const mbedtls_x509_crt *peer = conn->handshake_done ? mbedtls_ssl_get_peer_cert(&conn->ssl) : NULL;
        if (!peer) return 0;
        return freak_tls_bridge_append(out, peer->raw.p, peer->raw.len) ? 1 : 0;
    }
    case 5: {
        /* RFC 5929 tls-server-end-point: the peer certificate hashed with its
           signature hash, where MD5 and SHA-1 become SHA-256. */
        const mbedtls_x509_crt *peer = conn->handshake_done ? mbedtls_ssl_get_peer_cert(&conn->ssl) : NULL;
        if (!peer) return 0;
        mbedtls_md_type_t md = peer->MBEDTLS_PRIVATE(sig_md);
        if (md == MBEDTLS_MD_MD5 || md == MBEDTLS_MD_SHA1) md = MBEDTLS_MD_SHA256;
        if (md != MBEDTLS_MD_SHA256 && md != MBEDTLS_MD_SHA384 && md != MBEDTLS_MD_SHA512) return 0;
        const mbedtls_md_info_t *info = mbedtls_md_info_from_type(md);
        unsigned char digest[64];
        if (!info || mbedtls_md(info, peer->raw.p, peer->raw.len, digest) != 0) return 0;
        return freak_tls_bridge_append(out, digest, mbedtls_md_get_size(info)) ? 1 : 0;
    }
    default: return 0;
    }
}

int64_t freak_tls_last_error(int64_t out) {
    return freak_tls_append_text(out, freak_tls_global_error);
}

int64_t freak_tls_live_sessions(void) {
    return freak_tls_sessions.live;
}
