#!/usr/bin/env python3
"""Verify the pinned C99 parser/shim and fragmented callback ABI without generators."""
from __future__ import annotations
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

PROBE = r'''
#include "freak_amalgamation.inc"
static unsigned char body[4];
static size_t used;
static int complete;
static int on_body(llhttp_t *p,const char *bytes,size_t length) {
    (void)p;
    if(length>sizeof(body)-used) return -1;
    memcpy(body+used,bytes,length); used+=length; return 0;
}
static int on_complete(llhttp_t *p) { (void)p; complete=1; return HPE_PAUSED; }
int main(void) {
    const char request[]="POST /part?key=value HTTP/1.1\r\nHost: localhost\r\nX-Test: abcdef\r\nContent-Length: 4\r\n\r\nA\0\xff" "B";
    llhttp_settings_t settings; llhttp_settings_init(&settings);
    settings.on_body=on_body; settings.on_message_complete=on_complete;
    llhttp_t parser; llhttp_init(&parser,HTTP_REQUEST,&settings);
    for(size_t i=0;i<sizeof(request)-1;i++) {
        llhttp_errno_t result=llhttp_execute(&parser,request+i,1);
        if(result!=HPE_OK && result!=HPE_PAUSED) return 2;
    }
    return !complete || used!=4 || memcmp(body,"A\0\xff" "B",4) || parser.lenient_flags;
}
'''

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clang",default=os.environ.get("FREAK_CLANG","clang"))
    parser.add_argument("--sanitize",action="store_true")
    args=parser.parse_args()
    compiler=shutil.which(args.clang)
    assert compiler,args.clang
    dependency=Path(__file__).resolve().parents[1]/"third_party"/"llhttp"
    for line in (dependency/"SHA256SUMS").read_text().splitlines():
        digest,name=line.split("  ",1)
        assert hashlib.sha256((dependency/name).read_bytes()).hexdigest()==digest,name
    flags=["-fsanitize=address,undefined,function","-fno-omit-frame-pointer","-g"] if args.sanitize else []
    env=dict(os.environ,ASAN_OPTIONS="detect_leaks=1:halt_on_error=1",UBSAN_OPTIONS="halt_on_error=1")
    with tempfile.TemporaryDirectory(prefix="freak-llhttp-") as temporary:
        root=Path(temporary);source=root/"probe.c";source.write_text(PROBE)
        if args.sanitize:
            control=root/"control.c"
            control.write_text('#include <stdint.h>\nint f(int n){return n+1;}\nint main(void){long(*bad)(long)=(long(*)(long))(uintptr_t)f;return (int)bad(1);}\n')
            executable=root/"control"
            subprocess.run([compiler,str(control),"-O0",*flags,"-o",str(executable)],check=True,capture_output=True)
            failed=subprocess.run([str(executable)],capture_output=True,env=env,timeout=10)
            assert failed.returncode!=0 and b"incorrect function type" in failed.stderr,failed.stderr
        for optimization in (0,2,3):
            executable=root/f"probe-O{optimization}"
            built=subprocess.run([compiler,str(source),f"-I{dependency}","-std=c99",f"-O{optimization}","-Werror=incompatible-pointer-types","-Werror=incompatible-function-pointer-types",*flags,"-o",str(executable)],capture_output=True,timeout=30)
            assert built.returncode==0,built.stderr.decode(errors="replace")
            result=subprocess.run([str(executable)],capture_output=True,env=env,timeout=10)
            assert result.returncode==0 and not result.stdout and not result.stderr,(result.returncode,result.stderr)
            print(f"PASS llhttp pin/checksums/C99 fragmented callback ABI O{optimization}",flush=True)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
