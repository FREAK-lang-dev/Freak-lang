# @@NAME@@

A small native HTTP/1 service with `/health`, the named `/hello/Ada` route,
and strict JSON POST roundtrip at `/json`. The JSON root must be an object
with a string `name`; invalid JSON returns 400 and field-type errors return 422.
Names decode percent-encoded UTF-8 and reject hidden separators, NUL and controls.
The manifest declares entry/module/export/tests. There are no external dependencies.

From this directory:

```sh
freak build
freak test
freak run
```

Visit `http://127.0.0.1:8080/health`. `freak run -- --once` serves one request
and exits, which is useful for a local smoke check. Use `--c` for the C backend.
The service binds 127.0.0.1 by default. `FREAK_HTTP_PORT` selects a decimal port;
zero requests an ephemeral port. `FREAK_HTTP_BIND` accepts a numeric address.
A non-loopback address additionally requires `FREAK_HTTP_ALLOW_NON_LOOPBACK=1`.
Selecting a public address alone does not enable external access.

This service speaks plaintext HTTP. Put an existing TLS reverse proxy in front
of its loopback/private listener for remote HTTPS. Port 443 does not turn HTTP
into TLS. The application ignores Forwarded/X-Forwarded-* headers and makes no
client-identity or origin decisions from them. Add a reviewed trusted-proxy
allowlist and reject direct ingress before using such headers.

There are no CORS headers, authentication scheme, access logs, or request/body
logs by default. Browser access needs an explicit allowed-origin/method/header
policy, and private routes need authentication. Never log Authorization,
cookies, tokens, or request-body secrets merely to debug a route.

One request runs at a time and each connection closes after its response.
Default limits are 8KiB request line, 32KiB headers/100 fields, 1MiB body,
5s absolute headers, 15s absolute body and 2s idle. Aggregate chunk metadata
is 4KiB and trailers 8KiB. Trickle input cannot keep resetting absolute deadlines.
An arbitrary slow handler blocks later clients; the library cannot preempt
handler code. This example has passed focused tests and is not a claim of
production hardening, TLS, streaming, keepalive, WebSocket, or concurrency support.

Requirements: matching V3.5 compiler/runtime/std/template payload, Clang and
host SDK, checked byte/filesystem, strict JSON and owned HTTP capabilities.
The shared native runtime requires C11 or newer; vendored llhttp's generated
parser is C99-compatible and needs no Node/generator/network at normal build.
No Git, registry, Python or lifecycle hook is required by this project.

Stop a running local service before removing its generated directory. The CLI
owns build/test output; cleanup never needs deleting dependency source or an
unrelated existing destination. Review the license before publishing.
