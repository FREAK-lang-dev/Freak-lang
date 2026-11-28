#!/bin/bash
# wrk load run: http_server_wrk.sh <port> <label>  (CONCS="1 32 256", DUR=8,
# ROUTES="/ /assets/index.js /api/v1/hello/Ada" by default)
run() {
  local label=$1 url=$2 c=$3 t=2 out
  shift 3; [ "$c" -lt 2 ] && t=1
  if ! out=$(wrk -t"$t" -c"$c" -d"${DUR:-8}"s --latency "$@" "$url" 2>&1); then
    echo "wrk failed for $label c=$c:" >&2; echo "$out" >&2; return 1
  fi
  printf "%-28s c=%-4s %10s req/s  p50 %-9s p99 %-9s %s\n" "$label" "$c" \
    "$(echo "$out" | awk '/Requests\/sec/ {print $2}')" "$(echo "$out" | awk '$1=="50%" {print $2}')" \
    "$(echo "$out" | awk '$1=="99%" {print $2}')" "$(echo "$out" | grep -oE 'Socket errors.*|Non-2xx.*' | tr '\n' ' ')"
}
P=$1; L=$2
for c in ${CONCS:-1 32 256}; do
  for route in ${ROUTES:-/ /assets/index.js /api/v1/hello/Ada}; do
    run "$L $route" "http://127.0.0.1:$P$route" "$c" || exit 1
  done
done
