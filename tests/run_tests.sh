#!/usr/bin/env bash
# FREAK Language — Test Runner
# Usage: ./tests/run_tests.sh [--llvm]
# Runs safe .fk tests through the v2 compiler and checks for crashes.

set -euo pipefail

BACKEND=""
if [[ "${1:-}" == "--llvm" ]]; then
    BACKEND="--llvm"
    echo "=== FREAK Test Runner (LLVM backend) ==="
else
    echo "=== FREAK Test Runner (C backend) ==="
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPILER="$ROOT/build/freakc_v2.exe"
RUNTIME_C="$ROOT/freakc/runtime/freak_runtime.c"
RUNTIME_LLVM="$ROOT/freakc/runtime/freak_llvm_runtime.c"
RUNTIME_INC="$ROOT/freakc/runtime"

if [[ ! -f "$COMPILER" ]]; then
    echo "ERROR: Compiler not found at $COMPILER"
    echo "Run the build first: cat src/compiler/*.fk > build/freakc_v2.fk && ..."
    exit 1
fi

PASS=0
FAIL=0
SKIP=0

# Tests that are safe to run (no stdin, no infinite loops, no filesystem writes)
SAFE_TESTS=(
    "hello.fk"
    "control_flow.fk"
    "operators.fk"
    "functions.fk"
    "break_continue.fk"
    "pipe_test.fk"
    "impl_test.fk"
    "llvm_comprehensive.fk"
)

run_test() {
    local fk_file="$1"
    local test_path="$SCRIPT_DIR/$fk_file"
    local test_name="${fk_file%.fk}"

    if [[ ! -f "$test_path" ]]; then
        echo "  SKIP  $fk_file (not found)"
        SKIP=$((SKIP + 1))
        return
    fi

    # Compile .fk to intermediate
    if [[ -n "$BACKEND" ]]; then
        # LLVM backend
        if ! "$COMPILER" "$test_path" --llvm > /dev/null 2>&1; then
            echo "  FAIL  $fk_file (compile to LLVM IR failed)"
            FAIL=$((FAIL + 1))
            return
        fi

        local ll_file="$test_path.ll"
        local exe_file="$SCRIPT_DIR/${test_name}_llvm_test"
        if [[ "$(uname -s)" == *MINGW* || "$(uname -s)" == *MSYS* || "$(uname -s)" == *CYGWIN* ]]; then
            exe_file="${exe_file}.exe"
        fi

        if ! clang -o "$exe_file" "$ll_file" "$RUNTIME_LLVM" -I"$RUNTIME_INC" -w -O2 -D_CRT_SECURE_NO_WARNINGS 2>/dev/null; then
            echo "  FAIL  $fk_file (clang link failed)"
            FAIL=$((FAIL + 1))
            return
        fi

        if timeout 5 "$exe_file" > /dev/null 2>&1; then
            echo "  PASS  $fk_file"
            PASS=$((PASS + 1))
        else
            echo "  FAIL  $fk_file (runtime error or timeout)"
            FAIL=$((FAIL + 1))
        fi
    else
        # C backend
        if ! "$COMPILER" "$test_path" > /dev/null 2>&1; then
            echo "  FAIL  $fk_file (compile to C failed)"
            FAIL=$((FAIL + 1))
            return
        fi

        local c_file="$test_path.c"
        local exe_file="$SCRIPT_DIR/${test_name}_ctest"
        if [[ "$(uname -s)" == *MINGW* || "$(uname -s)" == *MSYS* || "$(uname -s)" == *CYGWIN* ]]; then
            exe_file="${exe_file}.exe"
        fi

        if ! clang -o "$exe_file" "$c_file" "$RUNTIME_C" -I"$RUNTIME_INC" -w -O2 -D_CRT_SECURE_NO_WARNINGS 2>/dev/null; then
            echo "  FAIL  $fk_file (clang link failed)"
            FAIL=$((FAIL + 1))
            return
        fi

        if timeout 5 "$exe_file" > /dev/null 2>&1; then
            echo "  PASS  $fk_file"
            PASS=$((PASS + 1))
        else
            echo "  FAIL  $fk_file (runtime error or timeout)"
            FAIL=$((FAIL + 1))
        fi
    fi
}

echo ""
for test_file in "${SAFE_TESTS[@]}"; do
    run_test "$test_file"
done

echo ""
echo "Results: $PASS passed, $FAIL failed, $SKIP skipped"

if [[ $FAIL -gt 0 ]]; then
    exit 1
fi
