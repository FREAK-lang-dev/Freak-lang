#!/usr/bin/env bash
# FREAK Compiler Test Suite Runner
# Usage: ./tests/suite/run_tests.sh [freak_binary]
# Default freak binary: build/freak (relative to repo root)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SUITE_DIR="$REPO_ROOT/tests/suite"
FREAK="${1:-$REPO_ROOT/build/freak}"

if [ ! -f "$FREAK" ]; then
    echo "ERROR: freak binary not found at $FREAK"
    echo "Usage: $0 [path/to/freak]"
    exit 1
fi

PASS=0
FAIL=0
SKIP=0

echo ""
echo "  FREAK Compiler Test Suite"
echo "  freak: $FREAK"
echo "  suite: $SUITE_DIR"
echo ""

for fk_file in "$SUITE_DIR"/[0-9]*.fk; do
    name=$(basename "${fk_file%.fk}")
    expected_file="$SUITE_DIR/$name.expected"

    if [ ! -f "$expected_file" ]; then
        echo "  SKIP  $name  (no .expected file)"
        SKIP=$((SKIP + 1))
        continue
    fi

    # Compile
    build_out=$("$FREAK" build "$fk_file" 2>&1)
    bin="${fk_file%.fk}"
    if [[ "$OSTYPE" == "msys"* ]] || [[ "$OSTYPE" == "cygwin"* ]]; then
        bin="${bin}.exe"
    fi

    if [ ! -f "$bin" ]; then
        echo "  FAIL  $name  (build failed)"
        FAIL=$((FAIL + 1))
        continue
    fi

    # Run and compare
    actual=$("$bin" 2>&1)
    expected=$(cat "$expected_file")

    if [ "$actual" = "$expected" ]; then
        echo "  PASS  $name"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  $name"
        echo "        expected:"
        echo "$expected" | sed 's/^/          /'
        echo "        actual:"
        echo "$actual" | sed 's/^/          /'
        FAIL=$((FAIL + 1))
    fi
done

echo ""
echo "  Results: $PASS passed, $FAIL failed, $SKIP skipped"
echo ""

if [ $FAIL -gt 0 ]; then
    exit 1
fi
