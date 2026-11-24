# V3.5 HTTP transport and deployment profile

The HTTP floor is an HTTP/1 transport for native applications. The application
owns its routes, validation, authorization and response policy and handles one
request at a time; behind `next_request` an event loop serves every connection
concurrently, keeps HTTP/1.1 connections alive and can spread one listener
across worker processes (see "Concurrency, keep-alive and workers").
The `http` project template demonstrates health, a named UTF-8 parameter and
strict JSON POST roundtrip. It starts on `127.0.0.1:8080` and prints only its
startup address. Its tests are ordinary native `std::test` programs.

```sh
freak init service --template=http
cd service
freak build
freak test
freak run
```

`--c` selects the portability backend; LLVM is the default. The project uses
the matching installed `std::http_server` and `std::json_document` payload and
has no external package dependency, registry resolution or lifecycle hook.
The shared native runtime requires C11 or newer. Its pinned llhttp 9.4.3
generated parser is C99-compatible and ships as source with its MIT licenses,
provenance, local patch record and checksums. Normal builds require neither
Node nor a parser generator, package download or network access.

## Binding and exposure

`http_server::open(port)` binds numeric loopback 127.0.0.1. Port 0 chooses an
ephemeral port, available through `local_port`. The explicit
`bind(address, port, allow_non_loopback)` accepts a numeric IPv4/IPv6 address;
the last argument must be 1 to admit a non-loopback address. Failed bind,
invalid address and occupied-port outcomes retain an owned failed server
ticket with `status()==2` and an error word. Release it with `close`.

The generated application reads `FREAK_HTTP_BIND`, `FREAK_HTTP_PORT` and
`FREAK_HTTP_ALLOW_NON_LOOPBACK`. Empty values choose 127.0.0.1, 8080 and no
external exposure. An explicit non-loopback address additionally requires
`FREAK_HTTP_ALLOW_NON_LOOPBACK=1`. Address selection alone does not expose the
listener. `--once` serves one accepted request and closes cleanly for a local
smoke check. The service has no unauthenticated remote shutdown endpoint.

## Request and ownership contract

One server hands the application at most one active request. `next_request(server)`
returns an owned ticket for a complete request or a structured parse/socket/deadline
failure. Successful `request_status` is 0; failures carry an HTTP status and
an error word. The floor sends a bounded error response when the connection
permits it, then closes that connection. Release every request, including failed
requests, before accepting another. Releasing a parsed request without sending a
response closes its connection. Close every server, including a failed bind.

Words returned by getters are independent managed values. `request_body` and
`request_header_value_bytes` return independent owned ByteBuffers; release them
exactly once. They can survive request release. The namespace builtins borrow
ByteBuffer arguments. Ordinary facade `http_send_bytes` consumes its buffer
parameter and releases it after the send; a caller must not use or release that
moved owner. `http_send_json` borrows a scalar document ticket, serializes into
an owned temporary ByteBuffer and releases that buffer on success or failure.
The caller still releases the JSON document.

`http_send_file(request, path)` streams a regular file as the body, at any
size, outside the buffered-body cap: Linux hands it to the socket with
`sendfile`, macOS and Windows read it 64 KiB at a time, so memory stays flat.
Each loop turn moves at most 512 KiB of one download, so a fast reader shares
the worker with other connections instead of holding it until the file ends.
It sets `Content-Length` from the file size and `Content-Type:
application/octet-stream` unless the application set one. A file response has
no total write deadline; it is closed only when no progress is made for
`idle_ms`. If the file cannot be opened (missing, a directory, a FIFO), it
returns 0, `request_error` says why, and the request can still be answered.
Released, stale or foreign tickets
fail before accessing a reused socket or buffer. Copying a scalar ticket does
not preserve its lifetime after release or subsequent slot reuse.

HTTP/1.1 requires exactly one valid Host. HTTP/1.0 may omit Host. The parser
rejects malformed header names, obsolete folding, duplicate Host or
Content-Length/Transfer-Encoding, TE+CL in either order, invalid/overflowing
lengths and malformed chunk framing. Only `chunked` transfer coding and
`identity` content coding are supported. CONNECT, protocol upgrades, HTTP/2
and non-origin request targets fail. A valid `Expect: 100-continue` receives
its interim response only after complete header/framing/size admission;
unsupported expectations receive a final rejection without waiting for a body.

Header records preserve order, repetitions, values and trailer identity.
Header names are lowercase ASCII. Binary/invalid UTF-8 header values require
the bytes getter; the word getter requires NUL-free UTF-8. Framing, Host,
authorization/cookie and other sensitive trailer fields are rejected.
Bodies are decoded from Content-Length/chunk framing into ByteBuffers and may
contain NUL, arbitrary bytes and multibyte text. Content-Length counts encoded
bytes. Path/query getters retain percent encoding and duplicate query values;
the application must validate and decode them without silently collapsing
duplicates. The template decodes one named path component and rejects encoded
separators, NUL, controls and invalid UTF-8.

Response APIs reject CR/LF, invalid header tokens and caller-supplied framing
headers. The floor supplies encoded-byte Content-Length and the Connection
header (`keep-alive` or `close`).
HEAD emits the corresponding length without the body, including parser,
size and deadline rejections once `HEAD ` has been accepted. An incomplete
`HEAD` token or malformed method delimiter remains an ordinary parse error.
A 204 response has no Content-Length or body; 205 emits Content-Length: 0
without a body, and 304 has no body. A send writes what the socket takes at
once and queues the rest; the event loop finishes it (bounded by the body
deadline and idle gap) while the application serves later requests. The send
return value reports that the complete response was accepted for delivery; a
later network failure only closes that connection.

## Limits and shutdown

| Resource | Default |
|---|---:|
| Request line |8192 bytes |
| Initial headers |32768 wire bytes |
| Header/trailer records |100 total |
| Decoded request/response body |1048576 bytes |
| Aggregate chunk-size/extension lines |4096 wire bytes |
| Trailers |8192 wire bytes |
| Absolute header deadline |5000ms |
| Absolute body deadline |15000ms |
| Idle deadline |2000ms |
| Keep-alive idle / requests per connection |5000ms / 1000 |
| Open connections per worker |4096 |
| Listen backlog |SOMAXCONN (Windows: `SOMAXCONN_HINT(65535)`) |
| Worker processes |1 (`FREAK_HTTP_WORKERS` overrides) |
| Active handlers per worker |1 |

`set_limits`, `set_chunk_limits`, `set_timeouts`, `set_keep_alive`,
`set_max_connections` and `set_workers` configure a server before
it owns an active request. Values are checked; negative/oversized values fail.
Absolute header/body deadlines do not reset when trickle bytes arrive. Idle
deadlines track positive socket progress. Raw framing, decoded body, header
metadata and response allocation have separate bounded admission.

`stop` sets the server's atomic stop flag. A blocked `next_request` checks it
between polls of at most 50ms, subject to host scheduling and bounded work in
that poll. Queued response bytes are dropped on stop. Wait for the blocked operation to return, release its request and
then close the server. Concurrent `close`, release, configuration and arbitrary
other runtime operations are not a supported thread-safety contract.
The acceptance gate measures stop during blocked accept, read and a queued write.

## Concurrency, keep-alive and workers

Each worker process runs one event loop: epoll (edge-triggered) on Linux,
kqueue on macOS and the BSDs, WSAPoll on Windows. The loop accepts, reads,
parses and writes every open connection without blocking on any of them, and
hands complete requests to the application in arrival order. A client that
stalls mid-headers, trickles a body or stops reading its response only holds
its own connection until its deadline; everyone else keeps being served.
Handlers still run one at a time per worker, so a slow handler delays that
worker's queue. Socket deadlines cannot safely preempt arbitrary application
code; a hard handler CPU limit needs process isolation.

HTTP/1.1 connections persist unless the client sends `Connection: close`;
HTTP/1.0 persists only with `Connection: keep-alive`. Pipelined requests are
answered in order. `set_keep_alive(server, idle_ms, max_requests)` sets how long
an idle connection waits for its next request and how many requests one
connection serves (`max_requests` 0 turns keep-alive off). Errors the
transport generates itself (400, 408, 413, 414, 431, 503 and similar) always
close; an application response keeps the connection whatever its status.
The first request's header deadline counts from acceptance; later requests'
count from their first byte, and they use the limits current at that byte.
`set_max_connections(server, n)` caps open connections per worker;
beyond it new connections wait in the kernel backlog. Rejected requests still
waiting for the application count against the cap too. On POSIX the runtime
raises the soft open-file limit toward that cap.

`set_workers(server, n)` (or `FREAK_HTTP_WORKERS=n` when the application never
calls it) starts `n` processes that share the listener at the first
`next_request`; 0 means one per CPU. On Linux and macOS the extra workers are
forked there and continue from that call; on Windows they are started as new
copies of the program, inheriting the listening socket, and adopt it at their
own matching `bind`/`open` call. Every worker runs the same request loop with
its own memory: in-process state such as counters, caches or rate limits is per
worker. `worker_index(server)` is 0 in the first process. The first process
restarts a worker that exits (at most once a second per slot) and stops every
worker in `close`; workers also stop when the first process dies (Linux parent
death signal, a parent check on macOS, a job object on Windows). Use workers
with one server per program.
Open database connections and other sockets lazily, after the first
`next_request` (or per worker): on Linux and macOS a socket opened before the
fork is shared by every worker.

The floor does not provide streaming bodies, WebSocket, upgrades, HTTP/2 or
TLS.

### Longer-run path

On loopback the 0.16 floor serves small responses within about 20% of nginx
per worker (92k vs 110k requests/s on one worker, 245k vs 308k on four; see
`benchmarks/v35/http_server_load.md`). The remaining steps, roughly in order:

1. Peer address on a request (`X-Real-IP`, per-IP limits).
2. Streaming request bodies and generated response bodies (chunked). File
   responses already stream (`http_send_file`, with `sendfile` on Linux);
   `TransmitFile` on Windows and Range requests would follow.
3. IOCP on Windows instead of WSAPoll, and optionally io_uring on Linux.
4. Response compression in the floor (gzip/brotli, plus precompressed files).
5. With V4's threads and task values: worker threads sharing one process (and
   its caches) instead of worker processes, and handlers that can await I/O so
   one slow handler no longer delays its worker's queue.
6. HTTP/2 and WebSocket upgrades once streaming exists.

## HTTPS and reverse proxies

The listener speaks plaintext HTTP, including if someone chooses port 443.
Terminate TLS at an existing maintained reverse proxy with valid certificates.
Keep the application on loopback, or on a private interface with ingress
restricted to the proxy. The following Nginx fragment illustrates that boundary;
use your existing certificate and reviewed proxy configuration.

```nginx
server {
    listen 443 ssl;
    server_name service.example;
    ssl_certificate /etc/ssl/service/fullchain.pem;
    ssl_certificate_key /etc/ssl/service/private-key.pem;
    access_log off;
    client_max_body_size 1m;
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header Connection close;
        proxy_set_header Forwarded "";
        proxy_set_header X-Forwarded-For "";
        proxy_set_header X-Forwarded-Host "";
        proxy_set_header X-Forwarded-Proto "";
        proxy_set_header X-Real-IP "";
        proxy_connect_timeout 2s;
        proxy_send_timeout 20s;
        proxy_read_timeout 20s;
    }
}
```

The template ignores Forwarded and X-Forwarded-* values. It has no built-in
trusted-proxy identity policy and must keep ignoring those headers until one
is deliberately implemented. A later policy must authenticate the immediate
proxy peer, restrict direct ingress, discard client-supplied values and parse
one defined chain with a documented allowlist. A header supplied by an
arbitrary client is not evidence of its original identity, scheme or origin.

## Browser policy and logging

No CORS headers are sent by default. If browser sharing is required, define
specific allowed origins, methods and request headers; check the actual origin
and preflight request against that list. Credentialed requests require an
explicit origin rather than wildcard approval. CORS does not replace
authentication, authorization or CSRF protection for state changes.

The generated service logs only its configured startup address. Keep
Authorization, cookies, tokens, body secrets and sensitive query values out of
application and proxy logs by default. The proxy example disables access logs;
enable a reviewed log format only when needed. Do not echo raw client input
into diagnostics merely to investigate a route.

## Verification and practical scope

`tests/v3_v35_llhttp.py` checks pinned local checksums, incremental binary input
and the maintained parser's callback ABI with function/undefined/address
sanitizers and a failing control. `tests/v3_v35_http.py` drives the production
transport with independent HTTP clients and a hostile raw-socket corpus on
both scalar runtime interfaces at O0/O2/O3. It forces real partial sends,
tests strict framing/Host/Expect/chunks/trailers, exact size boundaries,
absolute/idle deadlines, resets, bind/restart and stop during network waits.
The same-process mixed request soak conserves live HTTP/socket/buffer/word/JSON
owners, kernel descriptors and retained HTTP metadata after warmup. It also
checks that shared ByteBuffer/JSON ticket tables and LLVM word buckets stop
growing after their exercised paths have warmed up.

`tests/v3_v35_http_language.py` compiles an ordinary FREAK consumer using the
fresh V3.5 compiler, strict borrow checking, both native backends and ownership
audits. It verifies the facade, JSON roundtrip, named route, HEAD/204/205/304,
rejected HEAD framing, 404/405,
binary bodies, split framing and semantic type failures. The template gate
also generates the installed examples, builds/runs/tests them and checks
existing destinations, links, malformed names, partial failures and cleanup.

The final release gate retains the Ordnance consumer checks and additionally
runs the raw transport and ordinary-language matrices against the extracted
archive's runtime, bundled parser and standard library. It exercises the
installed CLI's template build/run/test paths. The compiler ABI and parser
checksum checks use the explicit current compiler and pinned source checkout;
archive payload verification separately checks every installed parser byte.
Parser selection matches the runtime's include priority, and an explicitly
supplied runtime cannot borrow an external parser when its bundle is missing.
CI preserves the native HTTP and template JSON reports as artifacts.

These focused checks establish the stated floor. They do not make the example
production-hardened. Native Windows/macOS execution and final archive/CI
acceptance remain separate release requirements; a Linux run does not establish
those hosts. Review application policy, proxy setup, dependency pinning and
operational limits for the actual deployment before exposing a service.
