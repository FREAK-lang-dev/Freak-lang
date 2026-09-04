# FREAK V3 HTTP acceptance server

This package is a deliberately small, direct-compile acceptance application
for the managed V3 TCP socket and `ByteBuffer` APIs. It listens only on
`127.0.0.1`, accepts a fixed number of sequential connections, and implements
one HTTP/1.1 route:

```text
GET /hello HTTP/1.1
```

The success response is JSON: `{"message":"FREAKING WORKS"}`. Malformed,
unsupported, or over-64-KiB request headers receive a deterministic 400
response. TLS, keep-alive, routing, and request bodies are intentionally out of
scope for this runtime-floor example.

Compile `src/main.fk` directly with the V3 CLI. The first optional argument is
the port (`0` selects an ephemeral port); the second is the number of
connections to accept. The server prints `ORDNANCE_READY <port>` before it
starts accepting clients.

Each client has a 250-ms send/receive idle timeout and a two-second total
header budget measured with the monotonic clock. An idle receive timeout closes
the connection; a header that exceeds the total budget receives 400 if the
socket is still writable. The server then continues to the next connection. This bounded
sequential example is an acceptance fixture, not a concurrent production server.
