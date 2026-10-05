#!/usr/bin/env python3
"""Verify checked native filesystem carriers, publication and binary identity.

Both C and LLVM scalar adapters call the shipping runtime, with independent
Python file/metadata/hash oracles. This gate does not compile FREAK sources.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from v3_v35_process import WINDOWS_ARGV_WRAPPER


HARNESS = r'''
#include "freak_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#ifdef TEST_FSYNC_FAULT
#include <sys/stat.h>
#include <errno.h>
static int fail_directory_sync=0;
extern int __real_fsync(int descriptor);
int __wrap_fsync(int descriptor) {
    struct stat info;
    if(fail_directory_sync && fstat(descriptor,&info)==0 && S_ISDIR(info.st_mode)) { errno=EIO; return -1; }
    return __real_fsync(descriptor);
}
#endif
static void require(int ok,const char *why) { if (!ok) { fprintf(stderr,"FAIL: %s\n",why); exit(2); } }
#ifdef USE_LLVM_ADAPTER
#define W(s) ((int64_t)(intptr_t)(s))
#define F(name) freak_llvm_fs_##name
extern void freak_llvm_word_release_replaced(int64_t previous,int64_t replacement);
static freak_word word(int64_t h) { return freak_llvm_word_view(F(result_word)(h)); }
static freak_word error(int64_t h) { return freak_llvm_word_view(F(result_error)(h)); }
static freak_word entry(int64_t h,int64_t i) { return freak_llvm_word_view(F(result_entry)(h,i)); }
static freak_word hash(int64_t h) { return freak_llvm_word_view(F(sha256_bytes)(h)); }
static void drop(freak_word *w) { freak_llvm_word_release_replaced((int64_t)(intptr_t)w->data,0); *w=freak_word_lit(""); }
#else
#define W(s) freak_word_lit(s)
#define F(name) freak_fs_##name
#define word freak_fs_result_word
#define error freak_fs_result_error
#define entry freak_fs_result_entry
#define hash freak_fs_sha256_bytes
#define drop freak_word_release_owned
#endif
static void success(int64_t h) { if (!F(result_ok)(h)) { freak_word e=error(h); fwrite(e.data,1,e.length,stderr); drop(&e); require(0,"expected success"); } F(result_release)(h); }
static void failed(int64_t h) { require(!F(result_ok)(h),"expected ordinary I/O error"); freak_word e=error(h); require(e.length>0,"error has message"); drop(&e); F(result_release)(h); }
static void equal(freak_word w,const void *p,size_t n) { require(w.length==n && (n==0 || memcmp(w.data,p,n)==0),"exact owned result bytes"); }
int main(int argc,char **argv) {
    if (argc<2) return 90;
    const char *mode=argv[1];
#ifdef TEST_FSYNC_FAULT
    if (!strcmp(mode,"fault-create")) { fail_directory_sync=1; failed(F(exclusive_create)(W("fault.lock"),W("complete-owner"))); return 0; }
    if (!strcmp(mode,"fault-write")) { fail_directory_sync=1; failed(F(write_checked)(W("fault-output"),W("complete-new"))); return 0; }
    if (!strcmp(mode,"fault-rename")) { fail_directory_sync=1; failed(F(rename_checked)(W("fault-from"),W("fault-to"))); return 0; }
#endif
    if (!strcmp(mode,"hash")) {
        int64_t r=F(read_bytes_ticket)(W(argv[2])); require(F(result_ok)(r),"binary read");
        int64_t b=F(result_bytes)(r); F(result_release)(r);
        freak_byte_buffer_seek(b,freak_byte_buffer_length(b));
        freak_word w=hash(b); fwrite(w.data,1,w.length,stdout); drop(&w); freak_byte_buffer_release(b); return 0;
    }
    if (!strcmp(mode,"list")) {
        int64_t r=F(list_dir_checked)(W(argv[2])); require(F(result_ok)(r),"directory read");
        for(int64_t i=0;i<F(result_count)(r);i++) { freak_word w=entry(r,i); printf("%zu:",w.length); for(size_t j=0;j<w.length;j++) printf("%02x",(unsigned char)w.data[j]); putchar('\n'); drop(&w); }
        F(result_release)(r); return 0;
    }
    if (!strcmp(mode,"canonical")) { int64_t r=F(canonical_path)(W(argv[2])); require(F(result_ok)(r),"canonical identity"); freak_word w=word(r); fwrite(w.data,1,w.length,stdout); F(result_release)(r); drop(&w); return 0; }
    if (!strcmp(mode,"binary-copy")) { int64_t r=F(read_bytes_ticket)(W(argv[2])); require(F(result_ok)(r),"source binary"); int64_t b=F(result_bytes)(r); F(result_release)(r); success(F(write_bytes_checked)(W(argv[3]),b)); freak_byte_buffer_release(b); return 0; }
    if (!strcmp(mode,"read-fails")) { failed(F(read_ticket)(W(argv[2]))); return 0; }
    if (!strcmp(mode,"binary-fails")) { failed(F(read_bytes_ticket)(W(argv[2]))); return 0; }
    if (!strcmp(mode,"append-fails")) { failed(F(append_checked)(W(argv[2]),W("changed"))); return 0; }
    if (!strcmp(mode,"write-fails")) { failed(F(write_checked)(W(argv[2]),W("changed"))); return 0; }
    if (!strcmp(mode,"list-fails")) { failed(F(list_dir_checked)(W(argv[2]))); return 0; }
    if (!strcmp(mode,"rename-new")) { success(F(rename_new_checked)(W(argv[2]),W(argv[3]))); return 0; }
    if (!strcmp(mode,"rename-new-fails")) { failed(F(rename_new_checked)(W(argv[2]),W(argv[3]))); return 0; }
    if (!strcmp(mode,"write")) { success(F(write_checked)(W(argv[2]),W(argv[3]))); return 0; }
    if (!strcmp(mode,"stat")) { int64_t r=F(stat_checked)(W(argv[2])); require(F(result_ok)(r),"stat"); printf("%lld:%lld:%lld",(long long)F(result_kind)(r),(long long)F(result_size)(r),(long long)F(result_mode)(r)); F(result_release)(r); return 0; }
    if (!strcmp(mode,"source")) { int64_t r=F(read_source_ticket)(W(argv[2])); require(F(result_ok)(r),"preserved source read"); freak_word w=word(r); F(result_release)(r); for(size_t j=0;j<w.length;j++) printf("%02x",(unsigned char)w.data[j]); drop(&w); return 0; }
    if (!strcmp(mode,"legacy-write")) { freak_fs_write(freak_word_lit(argv[2]),freak_word_lit("completion")); return 0; }
    if (!strcmp(mode,"legacy-append")) { freak_fs_append(freak_word_lit(argv[2]),freak_word_lit("completion")); return 0; }
    if (!strcmp(mode,"legacy-read")) { freak_word w=freak_fs_read(freak_word_lit(argv[2])); freak_word_release_owned(&w); return 0; }
    if (!strcmp(mode,"foreign")) { F(result_ok)((int64_t)UINT64_C(0x8000000100000001)); return 99; }
    if (!strcmp(mode,"bad-result")) { word(F(read_ticket)(W("absent"))); return 99; }
    if (!strcmp(mode,"bad-entry")) { entry(F(list_dir_checked)(W(".")),-1); return 99; }
    if (!strcmp(mode,"binary-word")) { word(F(read_bytes_ticket)(W(argv[2]))); return 99; }
    if (!strcmp(mode,"leak")) { F(read_ticket)(W("absent")); return 0; }
    if (!strcmp(mode,"stale") || !strcmp(mode,"double")) { int64_t r=F(read_ticket)(W("absent")); F(result_release)(r); if(!strcmp(mode,"stale")) F(result_ok)(r); else F(result_release)(r); return 99; }
    if (!strcmp(mode,"smoke")) {
        success(F(write_checked)(W("text λ $.txt"),W("hello λ\n")));
        int64_t r=F(read_ticket)(W("text λ $.txt")); require(F(result_ok)(r),"unicode text"); freak_word a=word(r), b=word(r); F(result_release)(r);
        equal(a,"hello λ\n",strlen("hello λ\n")); equal(b,a.data,a.length); drop(&a); drop(&b);
        success(F(append_checked)(W("text λ $.txt"),W("tail")));
        success(F(write_checked)(W("empty"),W(""))); r=F(read_ticket)(W("empty")); require(F(result_ok)(r),"empty valid text"); a=word(r); equal(a,"",0); drop(&a); F(result_release)(r);
        failed(F(read_ticket)(W("absent"))); failed(F(read_ticket)(W(""))); failed(F(write_checked)(W("absent-dir/file"),W("new")));
        success(F(exclusive_create)(W("operation.lock"),W("owner"))); failed(F(exclusive_create)(W("operation.lock"),W("intruder")));
        r=F(read_ticket)(W("operation.lock")); require(F(result_ok)(r),"lock retained"); a=word(r); equal(a,"owner",5); drop(&a); F(result_release)(r);
        success(F(remove_checked)(W("operation.lock"))); success(F(remove_checked)(W("absent")));
        success(F(mkdir_checked)(W("owned-dir"))); failed(F(mkdir_checked)(W("owned-dir"))); failed(F(remove_checked)(W("owned-dir")));
        r=F(list_dir_checked)(W("owned-dir")); require(F(result_ok)(r)&&F(result_count)(r)==0,"empty inventory"); F(result_release)(r);
        success(F(write_checked)(W("owned-dir/item"),W("data"))); failed(F(rmdir_checked)(W("owned-dir"))); success(F(remove_checked)(W("owned-dir/item"))); success(F(rmdir_checked)(W("owned-dir")));
        r=F(temp_dir)(W("."),W("stage")); require(F(result_ok)(r),"exclusive stage"); a=word(r); F(result_release)(r);
        success(F(rename_checked)(W(a.data),W("published-dir"))); drop(&a); success(F(rmdir_checked)(W("published-dir")));
        failed(F(temp_dir)(W("."),W("../escape"))); failed(F(rename_checked)(W("absent"),W("empty")));
        for(int i=0;i<256;i++) { r=F(read_ticket)(W("empty")); require(F(result_ok)(r),"repeat carrier"); a=word(r); int64_t bb=F(result_bytes)(r); F(result_release)(r); drop(&a); freak_byte_buffer_release(bb); }
        require(freak_fs_result_live()==0,"all result owners released"); puts("FS_OK"); return 0;
    }
    return 91;
}
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG", "clang"))
    parser.add_argument("--optimization", type=int, choices=(0, 2, 3), action="append")
    parser.add_argument("--sanitize", action="store_true")
    args = parser.parse_args()
    compiler = shutil.which(args.clang)
    assert compiler, f"Clang not found: {args.clang}"
    runtime = Path(__file__).resolve().parents[1] / "freakc" / "runtime"
    env = dict(os.environ, ASAN_OPTIONS="detect_leaks=1:halt_on_error=1", UBSAN_OPTIONS="halt_on_error=1")
    flags = ["-lws2_32", "-lshell32"] if os.name == "nt" else ["-lm"]
    suffix = ".exe" if os.name == "nt" else ""
    if args.sanitize:
        flags += ["-fsanitize=address,undefined", "-fno-omit-frame-pointer", "-g"]
    with tempfile.TemporaryDirectory(prefix="freak-v35-fs λ $ ") as temporary:
        root = Path(temporary)
        source = root / "harness.c"
        source.write_text(HARNESS.replace("int main(", "static int native_main(") + WINDOWS_ARGV_WRAPPER, encoding="utf-8")
        if args.sanitize:
            control = root / "control.c"
            control.write_text("#include <stdlib.h>\nint main(int n,char **v){volatile char *p=malloc(1);p[n+4]=3;free((void*)p);return 0;}\n")
            exe = root / f"control{suffix}"
            subprocess.run([compiler, str(control), "-O0", *flags, "-o", str(exe)], check=True, capture_output=True)
            result = subprocess.run([str(exe)], capture_output=True, env=env, timeout=10)
            assert result.returncode != 0 and b"AddressSanitizer" in result.stderr, result.stderr
        for optimization in args.optimization or (0, 2, 3):
            for adapter in ("c", "llvm"):
                exe = root / f"filesystem-{adapter}-O{optimization}{suffix}"
                build = [compiler, str(source), str(runtime / "freak_runtime.c"), str(runtime / "freak_llvm_runtime.c"), f"-I{runtime}", f"-O{optimization}", "-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1", "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1", "-D_CRT_SECURE_NO_WARNINGS", *flags, "-o", str(exe)]
                if sys.platform.startswith("linux"):
                    build += ["-DTEST_FSYNC_FAULT=1", "-Wl,--wrap=fsync"]
                if adapter == "llvm":
                    build.insert(1, "-DUSE_LLVM_ADAPTER=1")
                compiled = subprocess.run(build, capture_output=True, timeout=90)
                assert compiled.returncode == 0, compiled.stderr.decode(errors="replace")
                cwd = root / f"case-{adapter}-{optimization}"
                cwd.mkdir()

                def run(*arguments: str, failure: bytes | None = None) -> bytes:
                    result = subprocess.run([str(exe), *arguments], cwd=cwd, env=env, capture_output=True, timeout=10)
                    if failure is None:
                        assert result.returncode == 0 and not result.stderr, (arguments, result.returncode, result.stdout, result.stderr)
                    else:
                        assert result.returncode == 1 and not result.stdout and failure in result.stderr, (arguments, result.returncode, result.stdout, result.stderr)
                    return result.stdout

                assert run("smoke") == b"FS_OK\n"
                assert (cwd / "text λ $.txt").read_bytes() == "hello λ\ntail".encode()
                assert sorted(p.name for p in cwd.iterdir()) == ["empty", "text λ $.txt"], list(cwd.iterdir())
                for length in (0, 1, 3, 55, 56, 63, 64, 65, 119, 120, 127, 128, 129, 4097, 65536):
                    data = bytes((i * 73 + 19) & 255 for i in range(length))
                    sample = cwd / "hash-input"
                    sample.write_bytes(data)
                    assert run("hash", str(sample)) == hashlib.sha256(data).hexdigest().encode()
                    run("binary-copy", str(sample), "hash-copy")
                    assert (cwd / "hash-copy").read_bytes() == data
                (cwd / "publish-source").write_bytes(b"source")
                (cwd / "publish-existing").write_bytes(b"existing")
                run("rename-new-fails", "publish-source", "publish-existing")
                assert (cwd / "publish-source").read_bytes() == b"source" and (cwd / "publish-existing").read_bytes() == b"existing"
                if os.name != "nt":
                    (cwd / "publish-broken").symlink_to("missing-target")
                    run("rename-new-fails", "publish-source", "publish-broken")
                    assert (cwd / "publish-broken").is_symlink() and (cwd / "publish-source").read_bytes() == b"source"
                run("rename-new", "publish-source", "published")
                assert not (cwd / "publish-source").exists() and (cwd / "published").read_bytes() == b"source"
                binary = cwd / "raw-source"
                binary.write_bytes(b"a\0\xffb")
                run("read-fails", str(binary))
                assert run("source", str(binary)) == b"6100ff62"
                run("binary-word", str(binary), failure=b"filesystem result is binary")
                too_big = cwd / "large"
                with too_big.open("wb") as file:
                    file.truncate(64 * 1024 * 1024 + 1)
                run("binary-fails", str(too_big))
                run("read-fails", str(cwd))
                inventory = cwd / "inventory"
                inventory.mkdir()
                names = ["λ.txt", "pipe|name", "spaces $ &", "line\nbreak"] if os.name != "nt" else ["λ.txt", "spaces $ &", "a.txt"]
                for name in names:
                    (inventory / name).write_bytes(b"")
                expected = b"".join(str(len(name.encode())).encode() + b":" + name.encode().hex().encode() + b"\n" for name in sorted(names, key=lambda x: x.encode()))
                assert run("list", str(inventory)) == expected
                path = (cwd / "text λ $.txt").resolve()
                canonical = run("canonical", str(path)).decode()
                assert os.path.normcase(canonical.removeprefix("\\\\?\\")) == os.path.normcase(str(path)), canonical
                if os.name != "nt":
                    path.chmod(0o755)
                    run("write", str(path), "replaced")
                    assert path.read_bytes() == b"replaced" and path.stat().st_mode & 0o7777 == 0o755
                    link = cwd / "link"
                    link.symlink_to(path)
                    assert run("stat", str(link)).split(b":")[0] == b"3"
                    run("read-fails", str(link)); run("write-fails", str(link)); run("append-fails", str(link))
                    assert path.read_bytes() == b"replaced"
                    directory_link = cwd / "directory-link"
                    directory_link.symlink_to(inventory, target_is_directory=True)
                    run("list-fails", str(directory_link))
                    run("list-fails", str(directory_link) + "/")
                    assert run("stat", str(directory_link) + "/").split(b":")[0] == b"3"
                    fifo = cwd / "fifo"
                    os.mkfifo(fifo)
                    run("read-fails", str(fifo)); run("append-fails", str(fifo))
                    if Path("/dev/full").exists():
                        run("write-fails", "/dev/full")
                        run("legacy-write", "/dev/full", failure=b"could not complete file write")
                        run("legacy-append", "/dev/full", failure=b"could not complete file write")
                if sys.platform.startswith("linux"):
                    run("fault-create")
                    assert (cwd / "fault.lock").read_bytes() == b"complete-owner"
                    (cwd / "fault-output").write_bytes(b"old")
                    run("fault-write")
                    assert (cwd / "fault-output").read_bytes() == b"complete-new"
                    (cwd / "fault-from").write_bytes(b"rename-data")
                    run("fault-rename")
                    assert not (cwd / "fault-from").exists() and (cwd / "fault-to").read_bytes() == b"rename-data"
                    assert not list(cwd.glob("*.freak-tmp-*"))
                run("legacy-read", "absent", failure=b"cannot read complete file")
                for mode, diagnostic in (("stale", b"stale filesystem"), ("double", b"stale filesystem"), ("foreign", b"stale filesystem"), ("bad-result", b"unsuccessful filesystem"), ("bad-entry", b"index out of bounds"), ("leak", b"live filesystem result")):
                    run(mode, failure=diagnostic)
                print(f"PASS checked filesystem {adapter} O{optimization}: complete I/O, binary hash, publication, metadata, owners", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
