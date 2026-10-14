# Sequence HTTP/JSON service

Copy this directory and its sibling `freak-sequences` outside the checkout.
Build and test with the installed compiler:

```sh
freak build --c --strict-borrow
freak test --c --jobs=2
freak build --llvm --strict-borrow --frozen
freak test --llvm --jobs=2 --frozen
FREAK_HTTP_PORT=0 freak run --llvm --strict-borrow --frozen -- --requests 1000
```

Startup prints the actual loopback port. The optional request limit allows a
bounded acceptance soak and clean shutdown; omit it to serve until stopped.
The default port is 8080. This synchronous service handles one request per
connection and binds only `127.0.0.1`. Request bodies are limited to 8192 bytes;
absolute header/body deadlines are one second and the idle deadline is 250ms.
These bound slow-peer blocking, not arbitrary handler CPU time.

- `GET /health` returns `healthy`; HEAD sends no body.
- `GET /sequences/arithmetic?start=2&step=3&count=5` returns
  `{"values":[2,5,8,11,14]}`.
- POST to the same sequence path accepts a strict JSON object containing
  integer `start`, `step`, and `count` fields.
- `POST /echo` returns the exact request bytes, including NUL and non-text bytes,
  with `application/octet-stream`.
- Malformed JSON returns 400, invalid fields/ranges return 422, unsupported
  methods return 405 with Allow, and unknown paths return 404.

Start and step must be decimal integers in [-1000000,1000000]; count is
1..256. Duplicate JSON keys and malformed Unicode are rejected by the strict
document API. Response serialization uses JSON constructors, without manual
escaping. Each request, body, document, server, and child process has an
explicit owner and cleanup path. Request headers and bodies are never logged.

The application imports a real locked source library through its public
export and uses the public HTTP/JSON APIs. It does not use compiler arrays,
FFI, handwritten LLVM, or generated layout assumptions. Current capability
requirements are the V3.5 package binding, HTTP server and JSON document
profiles; this fixture does not claim immediate V4 source compatibility.
