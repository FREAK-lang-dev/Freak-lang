#!/usr/bin/env python3
"""Exercise the typed V3 runtime directly, including ownership failure controls.

Run from a compiler developer shell on Windows. This supplements, and does not
replace, source-to-native backend tests.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

PROGRAM = r'''
#include "freak_runtime.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
int main(int argc, char **argv) {
 freak_v3_array_release(0); freak_v3_shape_release(0);
 int64_t a=freak_v3_array_new(FREAK_V3_INT);
 if(argc>1) {
  if(!strcmp(argv[1],"retain-c-word")) { freak_word source=freak_word_concat(freak_word_lit("re"),freak_word_lit("tained")); int64_t w=freak_v3_array_filled_word(1,source); freak_word_release_owned(&source); assert(freak_v3_live_words()==1); (void)w; return 0; }
  if(!strcmp(argv[1],"retain-llvm-word")) { int64_t w=freak_v3_array_filled(2,1,(int64_t)(intptr_t)"retained"); assert(freak_v3_live_words()==1); (void)w; return 0; }
  if(!strcmp(argv[1],"negative")) freak_v3_array_get(a,-1);
  if(!strcmp(argv[1],"equal")) freak_v3_array_set(a,0,4);
  if(!strcmp(argv[1],"huge")) freak_v3_array_filled(0,INT64_MAX,0);
  if(!strcmp(argv[1],"stale")) {freak_v3_array_release(a); int64_t b=freak_v3_array_new(0); (void)b; freak_v3_array_get(a,0);}
  if(!strcmp(argv[1],"cycle")) {int64_t s=freak_v3_shape_new(1); freak_v3_shape_init(s,0,3,s);}
  if(!strcmp(argv[1],"cycle2")) {int64_t s=freak_v3_shape_new(1),t=freak_v3_shape_new(1); freak_v3_shape_init(s,0,3,t); freak_v3_shape_init(t,0,3,s);}
  return 9;
 }
 for(int64_t i=0;i<1000000;i++) freak_v3_array_push(a,i);
 int64_t sum=0; for(int64_t i=0;i<1000000;i++){freak_v3_array_set(a,i,freak_v3_array_get(a,i)+1);sum+=freak_v3_array_get(a,i);}
 assert(sum==INT64_C(500000500000)); assert(freak_v3_array_len(a)==1000000);
 freak_v3_array_retain(a); freak_v3_array_release(a); assert(freak_v3_live_arrays()==1); freak_v3_array_release(a);
 a=freak_v3_array_filled(1,1000000,freak_v3_num_bits(1.25));
 assert(freak_v3_bits_num(freak_v3_array_get(a,999999))==1.25); freak_v3_array_release(a);
 int64_t handles[4096]; for(int i=0;i<4096;i++)handles[i]=freak_v3_array_new(0); for(int i=0;i<4096;i++)freak_v3_array_release(handles[i]);
 a=freak_v3_array_new(FREAK_V3_WORD); freak_v3_array_push(a,(int64_t)(intptr_t)"hi");
 freak_v3_array_set(a,0,freak_v3_array_get(a,0)); assert(!strcmp((char*)(intptr_t)freak_v3_array_get(a,0),"hi"));
 assert(freak_v3_live_words()==1); freak_v3_array_release(a);
 a=freak_v3_array_filled_word(8,freak_word_lit("hello"));
 freak_v3_array_set_word(a,0,freak_v3_array_get_word(a,1));
 assert(freak_v3_array_get_word(a,0).length==5); assert(freak_v3_live_words()==8); freak_v3_array_release(a);
 freak_word owned=freak_word_concat(freak_word_lit("own"),freak_word_lit("ed"));
 a=freak_v3_array_filled_word(2,owned); freak_word_release_owned(&owned);
 freak_v3_array_set_word(a,0,freak_v3_array_get_word(a,1));
 owned=freak_word_clone(freak_v3_array_get_word(a,0)); freak_v3_array_release(a);
 assert(owned.length==5 && !memcmp(owned.data,"owned",5)); freak_word_release_owned(&owned);
 int64_t s=freak_v3_shape_new(2); freak_v3_shape_init_word(s,0,freak_word_lit("shape")); freak_v3_shape_init(s,1,0,42);
 a=freak_v3_array_filled(3,256,s); freak_v3_shape_release(s); assert(freak_v3_live_shapes()==1); assert(freak_v3_live_words()==1);
 s=freak_v3_array_get(a,0); freak_v3_shape_set_word(s,0,freak_v3_shape_get_word(s,0));
 freak_v3_array_set(a,0,s); assert(freak_v3_shape_get(s,1)==42); freak_v3_array_release(a);
 s=freak_v3_shape_new(1); freak_v3_shape_init(s,0,2,(int64_t)(intptr_t)"take");
 int64_t v=freak_v3_shape_take(s,0); assert(freak_v3_live_words()==0); freak_v3_shape_set_owned(s,0,v); assert(freak_v3_live_words()==1); freak_v3_shape_release(s);
 s=freak_v3_shape_new(1); int64_t t=freak_v3_shape_new(1); freak_v3_shape_init(t,0,2,(int64_t)(intptr_t)"nested"); freak_v3_shape_init(s,0,3,t); freak_v3_shape_release(t); freak_v3_shape_release(s);
 /* Build a deep chain in linear time by attaching fresh leaves, then exercise
    full-depth cycle detection and iterative destruction. */
 int64_t root=freak_v3_shape_new(1), tail=root;
 for(int i=0;i<20000;i++) { int64_t child=freak_v3_shape_new(1); freak_v3_shape_init(tail,0,3,child); if(tail!=root) freak_v3_shape_release(tail); tail=child; }
 freak_v3_shape_init(tail,0,0,0); freak_v3_shape_release(tail);
 s=freak_v3_shape_new(1); freak_v3_shape_init(s,0,3,root); freak_v3_shape_release(root); freak_v3_shape_release(s);
 assert(freak_v3_live_arrays()==0); assert(freak_v3_live_shapes()==0); assert(freak_v3_live_words()==0);
 puts("typed-runtime-ok checksum=500000500000 arrays=0 shapes=0 words=0"); return 0;
}

'''

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sanitize", action="store_true")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    clang = os.environ.get("FREAK_CLANG") or shutil.which("clang")
    if not clang:
        raise SystemExit("clang is required")
    with tempfile.TemporaryDirectory(prefix="freak-v3-arrays-") as temporary:
        directory = Path(temporary)
        source = directory / "runtime_test.c"
        binary = directory / ("runtime_test.exe" if os.name == "nt" else "runtime_test")
        source.write_text(PROGRAM, encoding="utf-8")
        command = [clang, "-std=c11", "-O2", "-Werror", "-Wno-deprecated-declarations",
                   "-DFREAK_RUNTIME_OWNERSHIP_AUDIT", "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT",
                   "-I", str(repo / "freakc/runtime"), str(source),
                   str(repo / "freakc/runtime/freak_runtime.c"), "-o", str(binary)]
        if args.sanitize:
            command += ["-fsanitize=address", "-g"]
        command += ["-lws2_32"] if os.name == "nt" else ["-lm"]
        subprocess.run(command, check=True, timeout=120)
        runtime_env = os.environ.copy()
        if args.sanitize and os.name == "nt":
            resource = subprocess.run([clang, "-print-resource-dir"], check=True,
                                      capture_output=True, text=True, timeout=10)
            resource_dir = Path(resource.stdout.strip())
            # MSVC-target LLVM installs its ASan DLL below the resource dir;
            # LLVM-MinGW normally provides it beside clang. Use this compiler's
            # runtime, without depending on another LLVM installation on PATH.
            dll_dirs = {str(Path(clang).resolve().parent)}
            dll_dirs.update(str(path.parent) for path in resource_dir.rglob("clang_rt.asan_dynamic-*.dll"))
            runtime_env["PATH"] = os.pathsep.join(sorted(dll_dirs)) + os.pathsep + runtime_env.get("PATH", "")
        started = time.perf_counter()
        result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=60, env=runtime_env)
        assert result.returncode == 0, f"runtime exit {result.returncode}: {result.stdout}{result.stderr}"
        assert "typed-runtime-ok" in result.stdout, result.stdout
        print(result.stdout.strip(), f"elapsed={time.perf_counter()-started:.3f}s")
        expected = {"negative": "out of bounds", "equal": "out of bounds",
                    "huge": "too large", "stale": "released container",
                    "cycle": "cyclic owned shape", "cycle2": "cyclic owned shape"}
        for case, diagnostic in expected.items():
            result = subprocess.run([str(binary), case], capture_output=True, text=True, timeout=10, env=runtime_env)
            assert result.returncode == 1, (case, result.returncode, result.stderr)
            assert diagnostic in result.stderr, (case, result.stderr)
        for case, code in (("retain-c-word", 87), ("retain-llvm-word", 86)):
            result = subprocess.run([str(binary), case], capture_output=True, text=True, timeout=10, env=runtime_env)
            assert result.returncode == code, (case, result.returncode, result.stderr)
            assert "unreleased word allocation(s)" in result.stderr, result.stderr
        print("6 negative controls passed; both actual-allocation retention controls passed")

if __name__ == "__main__":
    main()
