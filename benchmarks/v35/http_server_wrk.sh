#!/bin/bash
# wrk load run: http_server_wrk.sh <port> <label>  (CONCS="1 32 256", DUR=8 by default)
run() { local label=$1 url=$2 c=$3; shift 3; local t=2; [ "$c" -lt 2 ] && t=1
  local out=$(wrk -t$t -c$c -d${DUR:-8}s --latency "$@" "$url" 2>&1)
  printf "%-28s c=%-4s %10s req/s  p50 %-9s p99 %-9s %s\n" "$label" "$c" "$(echo "$out" | awk '/Requests\/sec/ {print $2}')" "$(echo "$out" | awk '$1=="50%" {print $2}')" "$(echo "$out" | awk '$1=="99%" {print $2}')" "$(echo "$out" | grep -oE 'Socket errors.*|Non-2xx.*' | tr '\n' ' ')"; }
P=$1; L=$2
for c in ${CONCS:-1 32 256}; do
  run "$L /" http://127.0.0.1:$P/ $c
  run "$L /assets/index.js" http://127.0.0.1:$P/assets/index.js $c
  run "$L /api/v1/hello/:name" http://127.0.0.1:$P/api/v1/hello/Ada $c
done
