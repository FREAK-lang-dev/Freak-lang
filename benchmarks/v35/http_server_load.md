# std::http_server load benchmark (0.15.2 vs 0.16 event loop)

Loopback, one 4-vCPU Linux container, `wrk` on the same machine (2 threads,
so client and server compete for the same 4 cores). 8-second runs. Numbers
are requests per second with p99 latency; "timeouts" are wrk's 2-second
socket timeouts. Absolute numbers will differ on real hardware; the ratios
are the point.

## akuma app (the "yashiro" experiment's routes)

`http_server_akuma_app.fk`: akuma 0.6 with `secure_headers`, a health route,
`/api/v1/hello/:name` (JSON) and an SPA/static mount with `AKUMA_STATIC_CACHE=1`.
The same compiled module (`.ll` from 0.15.2) is linked against each runtime.

| Server | `/` c=32 | `/api/...` c=32 | `/api/...` c=256 | `/api/...` c=32 + 16 stalled clients | 557 KB bundle c=32 |
|---|---|---|---|---|---|
| 0.15.2 runtime | 12.9k, p99 634 ms, timeouts | 8.9k, p99 386 ms, 20 timeouts | 9.2k, p99 501 ms, timeouts | 8.2k, p99 563 ms, 18 timeouts | 1.4k, timeouts |
| 0.16, 1 worker | 17.7k, p99 2.6 ms | 15.3k, p99 3.1 ms | 14.6k, p99 27 ms | 14.6k, p99 3.1 ms (14.7k without) | 2.0k |
| 0.16, 4 workers | 69.8k, p99 4.3 ms | 58.9k, p99 4.8 ms | 60.4k, p99 11.8 ms | 52.4k, p99 3.0 ms (50.7k without) | 6.2k |
| nginx, 4 workers | 186k (static) | 262k (`return 200`) | 310k | 265k | 15.9k (11.5k with `sendfile on`) |

No 0.16 run had a socket error or timeout. Stalled clients (half a request
header, never finished) no longer slow anyone else down. In the stalled
column 16 such clients stay open for the whole run: the server evicts each at
its deadline and the helper replaces it at once (96 connections over 12 s).
That column was measured in a separate session with its own unstalled
baseline, shown in parentheses; run-to-run spread on this box is about 10%.

## Raw floor (template app, no framework)

The `http` template's `/health` route, `wrk -t2 -c64`:

| Server | 1 worker | 2 workers | 4 workers |
|---|---|---|---|
| 0.16 std::http_server | 92k | 235k | ~245k |
| nginx `return 200` | 110k | | 308k |

The floor itself is within about 20% of nginx per worker. The akuma numbers
are lower because each request runs akuma's FREAK routing and header code
(V3.5 copies `word` arguments into every task call); that is framework and
compiler work, not socket handling. Large static files are the other gap:
akuma copies each cached file into a response buffer per request. 0.16's
`http_send_file` streams a file without that copy (and without the 1 MiB
buffered cap); akuma can switch to it. On this loopback setup nginx itself is
slower with `sendfile on`, so the table's nginx figure is with it off. See
"Longer-run path" in `docs/v35-http-floor.md`.

## Reproduce

```sh
FREAK_HTTP_PORT=9503 FREAK_HTTP_WORKERS=4 AKUMA_STATIC_CACHE=1 ./app &
./http_server_wrk.sh 9503 "akuma-4w"
# 16 clients stay stalled mid-header for the whole 8 s run (evicted ones are replaced)
python3 http_server_stall.py 9503 16 12 > stall.log & until grep -q stalled stall.log; do sleep 0.1; done
CONCS=32 ROUTES=/api/v1/hello/Ada ./http_server_wrk.sh 9503 "akuma-4w +16 stalled"; wait
nginx -c "$PWD/http_server_nginx.conf" -p "$PWD"; ./http_server_wrk.sh 9400 nginx
```
