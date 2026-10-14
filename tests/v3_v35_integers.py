#!/usr/bin/env python3
"""Verify defined signed arithmetic through native C and emitted LLVM ABI calls."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import random
import shutil
import subprocess
import tempfile


HARNESS = r'''
#include "freak_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef USE_LLVM
extern int64_t test_llvm_add(int64_t,int64_t),test_llvm_sub(int64_t,int64_t),test_llvm_mul(int64_t,int64_t),test_llvm_div(int64_t,int64_t),test_llvm_rem(int64_t,int64_t),test_llvm_neg(int64_t);
#define OP(name) test_llvm_##name
#else
#define OP(name) freak_int_##name##_checked
#endif
static int64_t calculate(const char *op,int64_t a,int64_t b) {
    if(!strcmp(op,"add")) return OP(add)(a,b);
    if(!strcmp(op,"sub")) return OP(sub)(a,b);
    if(!strcmp(op,"mul")) return OP(mul)(a,b);
    if(!strcmp(op,"div")) return OP(div)(a,b);
    if(!strcmp(op,"rem")) return OP(rem)(a,b);
    if(!strcmp(op,"neg")) return OP(neg)(a);
    exit(93);
}
int main(int argc,char **argv) {
    if(argc==2 && !strcmp(argv[1],"batch")) {
        char op[16]; long long a,b;
        while(scanf("%15s %lld %lld",op,&a,&b)==3) printf("%lld\n",(long long)calculate(op,(int64_t)a,(int64_t)b));
        return ferror(stdin) ? 92 : 0;
    }
    if(argc!=4) return 91;
    printf("%lld\n",(long long)calculate(argv[1],strtoll(argv[2],NULL,10),strtoll(argv[3],NULL,10)));
    return 0;
}
'''


def oracle(op: str, a: int, b: int) -> int | None:
    low, high = -(1 << 63), (1 << 63) - 1
    if op in ("div", "rem") and (b == 0 or (a == low and b == -1)):
        return None
    if op == "add":
        result = a + b
    elif op == "sub":
        result = a - b
    elif op == "mul":
        result = a * b
    elif op == "neg":
        result = -a
    else:
        quotient = abs(a) // abs(b) * (-1 if (a < 0) != (b < 0) else 1)
        result = quotient if op == "div" else a - quotient * b
    return result if low <= result <= high else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG", "clang"))
    parser.add_argument("--optimization", type=int, choices=(0, 2, 3), action="append")
    parser.add_argument("--sanitize", action="store_true")
    args = parser.parse_args()
    compiler = shutil.which(args.clang)
    assert compiler, args.clang
    runtime = Path(__file__).resolve().parents[1] / "freakc" / "runtime"
    low, high = -(1 << 63), (1 << 63) - 1
    boundaries = [low, low + 1, -(1 << 32), -3, -2, -1, 0, 1, 2, 3, 1 << 32, high - 1, high]
    generator = random.Random(35004)
    pairs = [(a, b) for a in boundaries for b in boundaries]
    pairs += [(generator.randrange(low, high + 1), generator.randrange(low, high + 1)) for _ in range(192)]
    legal = [(op, a, b, expected) for op in ("add", "sub", "mul", "div", "rem", "neg") for a, b in pairs if (expected := oracle(op, a, b)) is not None]
    adverse = [("add", high, 1), ("add", low, -1), ("sub", low, 1), ("sub", high, -1), ("sub", 0, low), ("mul", high, 2), ("mul", low, 2), ("mul", low, -1), ("mul", -1, low), ("mul", low, low), ("div", 1, 0), ("div", low, -1), ("rem", 1, 0), ("rem", low, -1), ("neg", low, 0)]
    flags = ["-lws2_32"] if os.name == "nt" else ["-lm"]
    env = dict(os.environ, UBSAN_OPTIONS="halt_on_error=1", ASAN_OPTIONS="detect_leaks=1:halt_on_error=1")
    if args.sanitize:
        flags += ["-fsanitize=address,undefined", "-fno-omit-frame-pointer", "-g"]
    suffix = ".exe" if os.name == "nt" else ""
    with tempfile.TemporaryDirectory(prefix="freak-v35-int-") as temporary:
        root = Path(temporary)
        source = root / "harness.c"
        source.write_text(HARNESS)
        bridge = root / "bridge.ll"
        fragments = []
        for op in ("add", "sub", "mul", "div", "rem", "neg"):
            arguments = "i64 %a" if op == "neg" else "i64 %a, i64 %b"
            types = "i64" if op == "neg" else "i64, i64"
            fragments.append(f"declare i64 @freak_int_{op}_checked({types})\ndefine i64 @test_llvm_{op}({arguments}) {{\nentry:\n  %result = call i64 @freak_int_{op}_checked({arguments})\n  ret i64 %result\n}}\n")
        bridge.write_text("\n".join(fragments))
        if args.sanitize:
            control = root / "control.c"
            control.write_text("#include <stdint.h>\nint main(int n,char **v){volatile int64_t a=INT64_MAX,b=n;return (int)(a+b);}\n")
            exe = root / f"control{suffix}"
            subprocess.run([compiler, str(control), "-O2", *flags, "-o", str(exe)], check=True, capture_output=True)
            result = subprocess.run([str(exe)], capture_output=True, env=env, timeout=10)
            assert result.returncode != 0 and b"signed integer overflow" in result.stderr, result.stderr
        for optimization in args.optimization or (0, 2, 3):
            for adapter in ("c", "llvm"):
                exe = root / f"integer-{adapter}-O{optimization}{suffix}"
                build = [compiler, str(source), str(runtime / "freak_runtime.c"), f"-I{runtime}", f"-O{optimization}", *flags, "-o", str(exe)]
                if adapter == "llvm":
                    build += ["-DUSE_LLVM=1", str(bridge)]
                compiled = subprocess.run(build, capture_output=True, timeout=90)
                assert compiled.returncode == 0, compiled.stderr.decode(errors="replace")
                batch = "".join(f"{op} {a} {b}\n" for op, a, b, _ in legal)
                result = subprocess.run([str(exe), "batch"], input=batch.encode(), capture_output=True, env=env, timeout=10)
                expected = "".join(f"{value}\n" for _, _, _, value in legal).encode()
                assert result.returncode == 0 and result.stdout == expected and not result.stderr, (result.returncode, result.stderr)
                for op, a, b in adverse:
                    result = subprocess.run([str(exe), op, str(a), str(b)], capture_output=True, env=env, timeout=10)
                    diagnostic = b"division by zero" if op in ("div", "rem") and b == 0 else b"overflow"
                    assert result.returncode == 1 and not result.stdout and b"FREAK: integer " + diagnostic in result.stderr, (op, a, b, result.returncode, result.stdout, result.stderr)
                    assert b"runtime error:" not in result.stderr and b"AddressSanitizer" not in result.stderr, result.stderr
                print(f"PASS checked integer {adapter} O{optimization}: {len(legal)} legal oracle cases, {len(adverse)} controlled failures", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
