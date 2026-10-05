#!/usr/bin/env python3
"""Exercise checked scalar runtime ABIs; language emitter checks are separate."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

PROGRAM = r'''
#include "freak_runtime.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
extern int64_t freak_llvm_num_to_int(int64_t);
extern void freak_llvm_word_release_replaced(int64_t, int64_t);
static int64_t convert(double value) {
#ifdef TEST_LLVM
    int64_t packed; memcpy(&packed, &value, sizeof packed);
    return freak_llvm_num_to_int(packed);
#else
    return freak_num_to_int_checked(value);
#endif
}
static void index_at(int64_t index) {
    if (index < 0 || index >= 3) {
        /* Fatal checks have no live owner whose normal cleanup is unreachable. */
#ifdef TEST_LLVM
        (void)freak_llvm_word_index_checked((int64_t)(intptr_t)"abc", index);
#else
        (void)freak_word_index_checked(freak_word_lit("abc"), index);
#endif
        return;
    }
    char *raw = malloc(4); assert(raw);
    raw[0] = 'a'; raw[1] = 0; raw[2] = (char)0x80; raw[3] = 0;
#ifdef TEST_LLVM
    int64_t owner = freak_llvm_word_adopt_sized((int64_t)(intptr_t)raw, 3);
    int64_t byte = freak_llvm_word_index_checked(owner, index);
    assert(freak_llvm_word_size(byte) == 1);
    assert((unsigned char)*(char *)(intptr_t)byte == (unsigned char)raw[index]);
    assert(byte != owner);
    freak_llvm_word_release_replaced(owner, 0);
    assert(freak_llvm_word_size(byte) == 1);
    freak_llvm_word_release_replaced(byte, 0);
#else
    freak_word owner = freak_word_own(raw, 3);
    freak_word byte = freak_word_index_checked(owner, index);
    assert(byte.heap && byte.length == 1 && byte.char_count == 1);
    assert((unsigned char)byte.data[0] == (unsigned char)raw[index]);
    assert(byte.data != raw);
    freak_word_release_owned(&owner);
    assert(byte.length == 1);
    freak_word_release_owned(&byte);
#endif
}
int main(int argc, char **argv) {
    assert(argc == 2);
    if (!strcmp(argv[1], "negative-index")) { index_at(-1); return 93; }
    if (!strcmp(argv[1], "high-index")) { index_at(3); return 93; }
    if (!strcmp(argv[1], "huge-index")) { index_at(INT64_MAX); return 93; }
    if (!strcmp(argv[1], "nan")) { convert(NAN); return 93; }
    if (!strcmp(argv[1], "infinity")) { convert(INFINITY); return 93; }
    if (!strcmp(argv[1], "negative-infinity")) { convert(-INFINITY); return 93; }
    if (!strcmp(argv[1], "upper-bound")) { convert(0x1p63); return 93; }
    if (!strcmp(argv[1], "below-lower")) { convert(nextafter(-0x1p63, -INFINITY)); return 93; }
    assert(!strcmp(argv[1], "valid"));
    assert(convert(-0.0) == 0 && convert(1.9) == 1 && convert(-1.9) == -1);
    assert(convert(-0x1p63) == INT64_MIN);
    assert(convert(nextafter(0x1p63, 0)) == INT64_MAX - 1023);
    for (int repeat = 0; repeat < 1000; repeat++)
        for (int64_t index = 0; index < 3; index++) index_at(index);
    freak_word path = freak_process_executable_path();
    assert(path.length && path.data[0]);
    FILE *image = fopen(freak_word_to_cstr(path), "rb"); assert(image);
    assert(fclose(image) == 0); freak_word_release_owned(&path);
    puts("bounds-and-image-ok");
}
'''

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG", "clang"))
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--optimization", type=int, choices=(0, 2, 3), action="append")
    parser.add_argument("--sanitize", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    runtime = (args.runtime_root or repo / "freakc/runtime").resolve()
    inputs = [p for p in runtime.rglob("*") if p.is_file()]
    vendor = runtime / "third_party/llhttp"
    if not vendor.exists():
        inputs += [p for p in (repo / "third_party/llhttp").rglob("*") if p.is_file()]
    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    evidence = {"runtime_input_hashes": before, "sanitized": args.sanitize, "matrices": []}
    with tempfile.TemporaryDirectory(prefix="freak-bounds-") as temporary:
        root = Path(temporary).resolve()
        source = root / "probe.c"; source.write_text(PROGRAM)
        if args.sanitize:
            control = root / "sanitizer-control.c"
            control.write_text("#include <stdlib.h>\nint main(void) { volatile char *p = malloc(1); free((void *)p); *p = 1; return 0; }\n")
            control_binary = root / ("sanitizer-control.exe" if os.name == "nt" else "sanitizer-control")
            subprocess.run([args.clang, "-O0", "-fsanitize=address,undefined", str(control), "-o", str(control_binary)], check=True, capture_output=True, timeout=90)
            failed = subprocess.run([str(control_binary)], capture_output=True, timeout=15)
            assert failed.returncode != 0 and b"heap-use-after-free" in failed.stderr, failed
            evidence["sanitizer_failing_control"] = True
        for opt in args.optimization or (0, 2, 3):
            for adapter in ("c", "llvm"):
                executable = root / (f"probe é & % {adapter}-O{opt}" + (".exe" if os.name == "nt" else ""))
                command = [args.clang, "-std=c11", f"-O{opt}", str(source),
                           str(runtime / "freak_runtime.c"), str(runtime / "freak_llvm_runtime.c"),
                           f"-I{runtime}", "-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1",
                           "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1", "-o", str(executable)]
                if adapter == "llvm": command += ["-DTEST_LLVM=1"]
                if args.sanitize: command += ["-fsanitize=address,undefined", "-fno-sanitize-recover=all", "-fno-omit-frame-pointer"]
                command += ["-lws2_32", "-lshell32"] if os.name == "nt" else ["-lm"]
                linked = subprocess.run(command, capture_output=True, timeout=90)
                assert linked.returncode == 0, linked.stderr.decode(errors="replace")
                cases = ["valid", "negative-index", "high-index", "huge-index", "nan",
                         "infinity", "negative-infinity", "upper-bound", "below-lower"]
                for case in cases:
                    env = {**os.environ, "PATH": "", "ASAN_OPTIONS": "detect_leaks=1"}
                    result = subprocess.run([str(executable), case], cwd=root, env=env,
                                            capture_output=True, timeout=15)
                    if case == "valid":
                        assert result.returncode == 0 and result.stdout == b"bounds-and-image-ok\n" and not result.stderr, (case, result)
                    else:
                        diagnostic = b"word index out of range" if "index" in case else b"num to int conversion out of range"
                        assert result.returncode == 1 and not result.stdout and diagnostic in result.stderr, (case, result)
                        assert b"runtime error:" not in result.stderr and b"Sanitizer" not in result.stderr, (case, result)
                evidence["matrices"].append({"adapter": adapter, "optimization": opt, "contracts": len(cases)})
                print(f"PASS checked bounds {adapter} O{opt}: {len(cases)} contracts", flush=True)
    evidence["inputs_unchanged"] = all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == sha for path, sha in before.items())
    assert evidence["inputs_unchanged"]
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(evidence, indent=2) + "\n")

if __name__ == "__main__":
    main()
