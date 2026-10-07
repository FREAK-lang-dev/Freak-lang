#!/usr/bin/env python3
"""Execute original fs::read/write/append through trusted installed std assembly.

The LLVM backend must use the selected std/runtime.fk, rather than a test
substitute for its reserved wrappers. Runtime payloads are staged from the
production distribution manifest and fingerprinted before and after execution.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

PROGRAM = r'''
task main() {
    pilot operation = process::arg(1)
    pilot path = process::arg(2)
    if operation == "read-nul" or operation == "write-nul" or operation == "append-nul" {
        path = path + char_to_word(0) + "suffix"
        if operation == "read-nul" { operation = "read" }
        else if operation == "write-nul" { operation = "write" }
        else { operation = "append" }
    }
    if operation == "good" {
        pilot target = process::arg(3)
        pilot contents = fs::read(path)
        fs::write(target, contents)
        fs::append(target, "\nλ" + char_to_word(0) + "tail")
        repeat 100 times {
            pilot repeated = fs::read(path)
            if repeated != contents { panic("source bytes changed") }
        }
        say contents.length()
        say "LEGACY_FS_OK"
    } else if operation == "read" {
        pilot contents = fs::read(path)
        say contents.length()
        say "READ_OK"
    } else if operation == "write" {
        fs::write(path, "complete-output")
        say "SHOULD_NOT"
    } else if operation == "append" {
        fs::append(path, "complete-output")
        say "SHOULD_NOT"
    } else { panic("unknown fixture operation") }
}
'''

FAULTS = r'''
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
static FILE *tracked=NULL;
static int closes=0,registered=0;
static const char *fault(void) { const char *p=getenv("FREAK_FS_TEST_FAULT"); return p?p:""; }
static void audit_close(void) {
    if (tracked && closes!=1) { fprintf(stderr,"FAULT_CLOSE_MISSING:%d\n",closes); _Exit(72); }
    if (tracked) fprintf(stderr,"FAULT_CLOSED:%d\n",closes);
}
static void track(FILE *file,const char *path) {
    const char *p=strrchr(path,'/'); if(p)p++;else p=path;
    if(file && !strcmp(p,"fault.data") && *fault()) { tracked=file; closes=0; if(!registered) { atexit(audit_close);registered=1; } }
}
extern FILE *__real_fopen(const char *,const char *);
extern FILE *__real_fdopen(int,const char *);
extern int __real_fseek(FILE *,long,int);
extern size_t __real_fread(void *,size_t,size_t,FILE *);
extern size_t __real_fwrite(const void *,size_t,size_t,FILE *);
extern int __real_ferror(FILE *);
extern int __real_fclose(FILE *);
FILE *__wrap_fopen(const char *path,const char *mode) { FILE *f=__real_fopen(path,mode); track(f,path); return f; }
FILE *__wrap_fdopen(int fd,const char *mode) {
    FILE *f=__real_fdopen(fd,mode); char descriptor[64],path[4097]; snprintf(descriptor,sizeof(descriptor),"/proc/self/fd/%d",fd);
    ssize_t n=readlink(descriptor,path,sizeof(path)-1); if(n>0) { path[n]=0;track(f,path); } return f;
}
int __wrap_fseek(FILE *f,long offset,int whence) { if(f==tracked && !strcmp(fault(),"seek_error")) { errno=EIO; return -1; } return __real_fseek(f,offset,whence); }
size_t __wrap_fread(void *p,size_t size,size_t count,FILE *f) {
    if(f==tracked && !strcmp(fault(),"read_short") && count) return __real_fread(p,size,count-1,f);
    size_t n=__real_fread(p,size,count,f);
    if(f==tracked && !strcmp(fault(),"read_growth")) {
        char descriptor[64],path[4097]; snprintf(descriptor,sizeof(descriptor),"/proc/self/fd/%d",fileno(f)); ssize_t length=readlink(descriptor,path,sizeof(path)-1);
        if(length>0) { path[length]=0; FILE *out=__real_fopen(path,"ab"); if(!out || __real_fwrite("x",1,1,out)!=1 || __real_fclose(out)) _Exit(73); }
    }
    return n;
}
size_t __wrap_fwrite(const void *p,size_t size,size_t count,FILE *f) { if(f==tracked && !strcmp(fault(),"write_short") && count) return __real_fwrite(p,size,count-1,f); return __real_fwrite(p,size,count,f); }
int __wrap_ferror(FILE *f) { if(f==tracked && !strcmp(fault(),"stream_error")) return 1; return __real_ferror(f); }
int __wrap_fclose(FILE *f) { int mine=f==tracked; int result=__real_fclose(f); if(mine) { closes++; if(!strcmp(fault(),"close_error")) { errno=EIO;return EOF; } } return result; }
'''

AUDIT_CONTROL = r'''
#include "freak_runtime.h"
#include <stdlib.h>
#include <string.h>
int main(int count,char **arguments) {
    if (count!=2) return 70;
    if (!strcmp(arguments[1],"filesystem")) {
        (void)freak_fs_open_dir_ticket(freak_word_lit("."));
        return 0;
    }
    char *owner=malloc(2); if(!owner) return 71;
    owner[0]='x'; owner[1]=0;
    if(!strcmp(arguments[1],"c")) (void)freak_word_own(owner,1);
    else (void)freak_llvm_word_adopt_sized((int64_t)(intptr_t)owner,1);
    return 0;
}
'''


def fingerprint(root: Path) -> dict[str,str]:
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file()}


def legacy_filename_probe(compiler: Path, clang: Path, runtime: Path, root: Path) -> dict:
    """Keep native filename/byte witnesses separate from the original gate."""
    import v3_word_foundation as foundation

    root.mkdir(parents=True, exist_ok=False)
    report = {"host": os.name, "gate_passed": False, "processes": [],
              "windows_filesystem_execution_claimed": os.name == "nt",
              "unc_scope": "native Windows lexical conversion only; no network share is opened"}
    source = root / "filename-witness.c"
    source.write_text(r'''
#ifdef _WIN32
#define _WIN32_WINNT 0x0602
#endif
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#ifdef _WIN32
#include <winsock2.h>
#include <windows.h>
#include <wchar.h>
#include <io.h>
#include <fcntl.h>
static int tracking, allocation_count, fail_allocation, full_count, fail_full, live;
static void *owned[8];
static void *observe_malloc(size_t size) {
    if (tracking && ++allocation_count == fail_allocation) return NULL;
    void *value = malloc(size);
    if (tracking && value) { if (live == 8) abort(); owned[live++] = value; }
    return value;
}
static void observe_free(void *value) {
    if (tracking && value) {
        int found = 0;
        for (int index = 0; index < live; ++index) if (owned[index] == value) {
            owned[index] = owned[--live]; found = 1; break;
        }
        if (!found) abort();
    }
    free(value);
}
static DWORD WINAPI observe_full(LPCWSTR name, DWORD count, LPWSTR output, LPWSTR *leaf) {
    if (tracking && ++full_count == fail_full) { SetLastError(ERROR_INVALID_NAME); return 0; }
    return GetFullPathNameW(name, count, output, leaf);
}
#define malloc observe_malloc
#define free observe_free
#define GetFullPathNameW observe_full
#endif
#include "freak_runtime.c"
#ifdef _WIN32
#undef malloc
#undef free
#undef GetFullPathNameW
static wchar_t *decode(freak_word value) {
    int count = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, value.data,
        (int)value.length, NULL, 0);
    wchar_t *wide = count ? calloc((size_t)count + 1, sizeof(*wide)) : NULL;
    if (wide && MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, value.data,
            (int)value.length, wide, count) != count) { free(wide); return NULL; }
    return wide;
}
static void emit_wide(const char *kind, const wchar_t *value) {
    printf("%s:%zu:", kind, wcslen(value));
    for (; *value; ++value) printf("%04x", (unsigned)*value);
    putchar('\n');
}
static int failures(freak_word path) {
    for (int mode = 1; mode <= 4; ++mode) {
        wchar_t *input = decode(path); if (!input) return 61;
        live = 1; owned[0] = input; allocation_count = full_count = 0;
        fail_allocation = mode <= 2 ? mode : 0;
        fail_full = mode > 2 ? mode - 2 : 0; tracking = 1;
        wchar_t *result = freak_fs_windows_filename(input);
        tracking = 0;
        if (result || live) return 62;
    }
    puts("allocation-and-resolution-failures:4:released"); return 0;
}
#endif
int main(int count, char **arguments) {
    freak_argc = count; freak_argv = arguments;
    if (count < 3) return 63;
    freak_word mode = freak_arg(1), path = freak_arg(2);
#ifdef _WIN32
    if (freak_word_eq(mode, freak_word_lit("normalize"))) {
        wchar_t *input = decode(path); if (!input) return 64;
        wchar_t *normalized = freak_fs_windows_filename(input); if (!normalized) return 65;
        printf("same-pointer:%d\n", normalized == input); emit_wide("kernel-utf16", normalized);
        free(normalized); return 0;
    }
    if (freak_word_eq(mode, freak_word_lit("failures"))) return failures(path);
    if (freak_word_eq(mode, freak_word_lit("files-long-cwd"))) {
        if (count != 5) return 75;
        freak_word directory = freak_arg(4);
        if (!directory.length || directory.length > INT_MAX) return 76;
        wchar_t *wide = decode(directory); if (!wide) return 77;
        wchar_t *qualified = freak_fs_windows_filename(wide); if (!qualified) return 78;
        int entered = SetCurrentDirectoryW(qualified); free(qualified);
        if (!entered) return 79;
        DWORD capacity = GetCurrentDirectoryW(0, NULL);
        if (capacity <= MAX_PATH || capacity > 32767) return 80;
        wchar_t *current = calloc(capacity, sizeof(*current)); if (!current) return 81;
        DWORD written = GetCurrentDirectoryW(capacity, current);
        if (!written || written >= capacity) { free(current); return 82; }
        emit_wide("current-directory-utf16", current); free(current);
    }
    wchar_t *ordinary = decode(path); if (!ordinary) return 66;
    emit_wide("old-ordinary-utf16", ordinary);
    int old_descriptor = _wopen(ordinary, _O_RDONLY | _O_BINARY);
    int old_errno = errno;
    printf("old-ordinary-open:%d:errno:%d\n", old_descriptor, old_descriptor >= 0 ? 0 : old_errno);
    if (old_descriptor >= 0) _close(old_descriptor);
    wchar_t *normalized = freak_fs_windows_filename(ordinary); if (!normalized) return 67;
    emit_wide("kernel-utf16", normalized); free(normalized);
#endif
    if (count != 5) return 68;
    freak_word target = freak_arg(3), directory = freak_arg(4);
    const char expected[] = {'A', 0, (char)255, 'B', '\r', '\n'};
    freak_result_word_word read = freak_fs_read_checked(path);
    if (!read.is_ok || read.data.ok_val.length != sizeof(expected) ||
        memcmp(read.data.ok_val.data, expected, sizeof(expected))) return 69;
    puts("read-bytes:6:4100ff420d0a");
    freak_word_release_owned(&read.data.ok_val);
    freak_fs_write(target, (freak_word){expected, sizeof(expected), false});
    freak_fs_append(target, freak_word_lit("XY"));
    read = freak_fs_read_checked(target);
    if (!read.is_ok || read.data.ok_val.length != sizeof(expected) + 2 ||
        memcmp(read.data.ok_val.data, expected, sizeof(expected)) ||
        memcmp(read.data.ok_val.data + sizeof(expected), "XY", 2)) return 70;
    puts("copied-bytes:8:4100ff420d0a5859");
    freak_word_release_owned(&read.data.ok_val);
    if (!freak_fs_exists(target) || !freak_fs_delete(target) || freak_fs_exists(target) ||
        !freak_fs_delete(target) || freak_fs_delete(directory)) return 71;
    int64_t canonical = freak_fs_canonical_path(path);
    if (!freak_fs_result_ok(canonical)) return 72;
    freak_word resolved = freak_fs_result_word(canonical);
    printf("canonical-utf8:%zu:", resolved.length);
    for (size_t index = 0; index < resolved.length; ++index)
        printf("%02x", (unsigned char)resolved.data[index]);
    putchar('\n'); freak_word_release_owned(&resolved); freak_fs_result_release(canonical);
    const char nul[] = {'x', 0, 'y'};
    freak_word invalid = {nul, sizeof(nul), false};
    read = freak_fs_read_checked(invalid);
    if (read.is_ok || freak_fs_fopen_checked(invalid, freak_word_lit("wb")) ||
        freak_fs_exists(invalid) || freak_fs_delete(invalid)) return 73;
    freak_word_release_owned(&read.data.err_val);
#ifdef _WIN32
    const char bad_utf8[] = {'x', (char)255, 'y'};
    invalid = (freak_word){bad_utf8, sizeof(bad_utf8), false};
    read = freak_fs_read_checked(invalid);
    if (read.is_ok || freak_fs_fopen_checked(invalid, freak_word_lit("wb")) ||
        freak_fs_exists(invalid) || freak_fs_delete(invalid)) return 74;
    freak_word_release_owned(&read.data.err_val);
#endif
    puts("LEGACY_LONG_FILENAME_OK"); return 0;
}
''', encoding="ascii")
    binary = root / ("filename-witness.exe" if os.name == "nt" else "filename-witness")

    def execute(command: list[str], cwd: Path = root) -> subprocess.CompletedProcess:
        sequence = len(report["processes"]) + 1
        result = subprocess.run(command, cwd=cwd, capture_output=True, timeout=90)
        row = {"argv": command, "cwd": str(cwd), "returncode": result.returncode,
               "launcher_pid": os.getpid(), "image_sha256": hashlib.sha256(Path(command[0]).read_bytes()).hexdigest()}
        for name in ("stdout", "stderr"):
            data = getattr(result, name); destination = root / f"{sequence:02d}.{name}.raw"
            destination.write_bytes(data)
            row[name] = {"path": str(destination), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        report["processes"].append(row)
        (root / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        assert result.returncode == 0, (command, result.returncode, result.stdout, result.stderr)
        return result

    execute([str(clang), "-O0", "-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1", "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1",
             str(source), "-I", str(runtime), "-o", str(binary),
             *(["-lws2_32"] if os.name == "nt" else ["-lm"])])
    physical = root / "native-日本-Ω"
    physical.mkdir()
    for _ in range(12):
        physical /= "long-component-日本-Ω"; physical.mkdir()
    raw = physical / "raw.data"; raw.write_bytes(b"A\0\xffB\r\n")
    target = physical / "copy.data"
    paths = [(str(raw), str(target))]
    paths.append((str(raw.relative_to(root)), str(target.relative_to(root))))
    if os.name == "nt":
        def extended(path: Path) -> str:
            value = str(path)
            if value.startswith("\\\\?\\"): return value
            return "\\\\?\\UNC\\" + value[2:] if value.startswith("\\\\") else "\\\\?\\" + value
        paths += [(str(raw).replace("\\", "/"), str(target).replace("\\", "/")),
                  (extended(raw), extended(target))]
        if len(raw.drive) == 2:
            paths += [(str(raw)[2:], str(target)[2:]),
                      (raw.drive + str(raw.relative_to(root)), target.drive + str(target.relative_to(root)))]
    for path, output in paths:
        result = execute([str(binary), "files", path, output, str(physical)])
        assert result.stdout.replace(b"\r\n", b"\n").endswith(b"LEGACY_LONG_FILENAME_OK\n") and not result.stderr, result
        assert raw.read_bytes() == b"A\0\xffB\r\n" and physical.is_dir() and not target.exists()
    if os.name == "nt":
        def normalized(path: str, expected: str, same: bool) -> None:
            result = execute([str(binary), "normalize", path])
            units = expected.encode("utf-16-le")
            encoded = "".join(f"{int.from_bytes(units[index:index + 2], 'little'):04x}" for index in range(0, len(units), 2))
            assert result.stdout.replace(b"\r\n", b"\n") == f"same-pointer:{int(same)}\nkernel-utf16:{len(units) // 2}:{encoded}\n".encode(), result
        for path in ("relative.txt", "C:/short/../caller.txt", "\\\\?\\C:\\explicit\\..\\caller.txt",
                     "\\\\?\\UNC\\server\\share\\caller.txt", "\\\\.\\NUL"):
            normalized(path, path, True)
        long_unc = "\\\\server\\share\\" + "long-component\\" * 24 + "file"
        normalized(long_unc, "\\\\?\\UNC\\" + long_unc[2:], False)
        if not str(root).startswith("\\\\?\\"):
            normalized(str(root) + "\\." * 150 + "\\short.txt", extended(root / "short.txt"), False)
        # CreateProcessW rejects a long current directory. Enter it in the
        # native witness after launching from the ordinary short fixture root.
        relative = execute([str(binary), "files-long-cwd", "raw.data", "copy.data", extended(physical)])
        current_directories = []
        for directory in (str(physical), extended(physical)):
            units = directory.encode("utf-16-le")
            encoded = "".join(f"{int.from_bytes(units[index:index + 2], 'little'):04x}" for index in range(0, len(units), 2))
            current_directories.append(f"current-directory-utf16:{len(units) // 2}:{encoded}".encode())
        assert relative.stdout.replace(b"\r\n", b"\n").splitlines()[0] in current_directories, relative
        assert relative.stdout.replace(b"\r\n", b"\n").endswith(b"LEGACY_LONG_FILENAME_OK\n") and not relative.stderr, relative
        assert raw.read_bytes() == b"A\0\xffB\r\n" and physical.is_dir() and not target.exists()
        execute([str(binary), "failures", str(raw)])
    program = physical / "main.fk"
    program.write_text('task main() { say "LONG_EMIT" }\n', encoding="ascii")
    for backend in ("c", "llvm"):
        suffix = ".c" if backend == "c" else ".ll"
        generated = Path(str(program) + suffix); generated.write_bytes(b"OLD_STALE_BACKEND\n")
        execute([str(compiler), str(program), "--" + backend])
        assert generated.is_file() and b"OLD_STALE_BACKEND" not in generated.read_bytes()
        emitted = root / ("emitted-" + backend + (".exe" if os.name == "nt" else ""))
        foundation.compile_generated(clang=str(clang), repo=Path(__file__).resolve().parents[1],
                                     runtime_root=runtime, generated=generated, backend=backend, binary=emitted)
        result = execute([str(emitted)])
        assert result.stdout.replace(b"\r\n", b"\n") == b"LONG_EMIT\n", result
    report["gate_passed"] = True
    report["runtime_sha256"] = hashlib.sha256((runtime / "freak_runtime.c").read_bytes()).hexdigest()
    (root / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print("PASS legacy filename native bytes, read/write/append/exists/delete/canonical and C+LLVM sibling emissions", flush=True)
    return report


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cli',type=Path,required=True,help='fresh native full CLI with trusted std assembly')
    p.add_argument('--payload-repo',type=Path,help='repository whose current distribution manifest/runtime is staged')
    p.add_argument('--clang',default=os.environ.get('FREAK_CLANG','clang'))
    p.add_argument('--optimization',type=int,choices=(0,2,3),action='append')
    p.add_argument('--sanitize',action='store_true')
    p.add_argument('--report',type=Path)
    a=p.parse_args(); repo=Path(__file__).resolve().parents[1]; payload_repo=(a.payload_repo or repo).resolve(strict=True); cli=a.cli.resolve(strict=True)
    clang=shutil.which(a.clang); assert clang
    evidence={'cli_sha256':hashlib.sha256(cli.read_bytes()).hexdigest(),'stdlib_runtime_sha256':hashlib.sha256((repo/'std/runtime.fk').read_bytes()).hexdigest(),'host':sys.platform,'sanitizers':a.sanitize,'cases':[], 'ownership_audit_scope':'Successful empty/soak paths and intentional leak controls; fatal exits use normal native binaries because process termination does not promise lexical caller cleanup.'}
    env=dict(os.environ,ASAN_OPTIONS='detect_leaks=1:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1',FREAK_CLANG=clang)
    with tempfile.TemporaryDirectory(prefix='freak-legacy-fs-') as temporary:
        root=Path(temporary).resolve(); root.chmod(0o755); payload=root/'installed'; payload.mkdir()
        manifest=(payload_repo/'packaging/distribution-files.manifest').read_text(); selected=[]
        for line in manifest.splitlines():
            if not line or line.startswith('#'): continue
            source,target=line.split('|'); destination=payload/target; destination.parent.mkdir(parents=True,exist_ok=True)
            original=(repo/source) if source=='std/runtime.fk' else (payload_repo/source)
            selected.append((original,destination,hashlib.sha256(original.read_bytes()).hexdigest())); shutil.copyfile(original,destination)
        for original,destination,before in selected: assert hashlib.sha256(original.read_bytes()).hexdigest()==before,(original,'payload source changed during snapshot')
        before=fingerprint(payload); evidence['payload_sha256']=before; evidence['distribution_manifest_sha256']=hashlib.sha256(manifest.encode()).hexdigest();env['FREAK_HOME']=str(payload)
        runtime=payload/'runtime'; suffix='.exe' if os.name=='nt' else ''; flags=['-lws2_32','-lshell32'] if os.name=='nt' else ['-lm']
        if a.sanitize:
            flags+=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-g']
            control=root/'control.c'; control.write_text('#include <stdlib.h>\nint main(int n,char**v){volatile char*p=malloc(1);p[n+4]=1;free((void*)p);return 0;}\n'); binary=root/('control'+suffix)
            subprocess.run([clang,str(control),'-O0',*flags,'-o',str(binary)],check=True,capture_output=True)
            r=subprocess.run([str(binary)],env=env,capture_output=True,timeout=10);assert r.returncode!=0 and b'AddressSanitizer' in r.stderr
            control.write_text('#include <stdint.h>\nint main(int n,char**v){volatile int64_t a=INT64_MAX;volatile int64_t b=a+n;return (int)b;}\n')
            subprocess.run([clang,str(control),'-O0',*flags,'-o',str(binary)],check=True,capture_output=True)
            r=subprocess.run([str(binary)],env=env,capture_output=True,timeout=10);assert r.returncode!=0 and b'runtime error: signed integer overflow' in r.stderr
            evidence['failing_controls']=['asan_heap_oob','ubsan_signed_overflow']
        audit_control=root/'audit-control.c'; audit_control.write_text(AUDIT_CONTROL)
        audit_binary=root/('audit-control'+suffix)
        subprocess.run([clang,'-O0',str(audit_control),str(runtime/'freak_runtime.c'),f'-I{runtime}','-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1','-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1',*flags,'-o',str(audit_binary)],check=True,capture_output=True)
        for owner,status,diagnostic in (('c',87,b'C ownership audit found 1'),('llvm',86,b'LLVM ownership audit found 1'),('filesystem',1,b'1 live filesystem result')):
            r=subprocess.run([str(audit_binary),owner],cwd=root,env=env,capture_output=True,timeout=15)
            assert r.returncode==status and diagnostic in r.stderr,(owner,r.returncode,r.stderr)
        evidence['ownership_failing_controls']=['c_word','llvm_word','filesystem_ticket']
        fault_source=root/'faults.c'; fault_source.write_text(FAULTS)
        for backend in ('c','llvm'):
            source=root/f'legacy-{backend}.fk'; source.write_text(PROGRAM,encoding='utf8')
            assembled=subprocess.run([str(cli),'build',str(source),'--'+backend],cwd=root,env=env,capture_output=True,timeout=90)
            assert assembled.returncode==0,(backend,assembled.stdout,assembled.stderr)
            generated=Path(str(source)+('.c' if backend=='c' else '.ll')); code=generated.read_text()
            if backend=='llvm':
                assert 'define i64 @freak_llvm_fs_read' in code and 'call i64 @freak_llvm_fs_read_source_ticket' in code
                assert 'call i64 @freak_ferror' in code and 'define void @freak_llvm_fs_write' in code
            for opt in a.optimization or (0,2,3):
                binary=root/f'legacy-{backend}-O{opt}{suffix}'; audited_binary=root/f'legacy-{backend}-O{opt}-audit{suffix}'
                command=[clang,f'-O{opt}',str(generated),str(runtime/'freak_runtime.c'),f'-I{runtime}',*flags]
                if backend=='llvm':command.append(str(runtime/'freak_llvm_runtime.c'))
                if sys.platform.startswith('linux'):command+=[str(fault_source),*[f'-Wl,--wrap={name}' for name in ('fopen','fdopen','fseek','fread','fwrite','ferror','fclose')]]
                for executable,defines in ((binary,[]),(audited_binary,['-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1','-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1'])):
                    linked=subprocess.run([*command,*defines,'-o',str(executable)],capture_output=True,timeout=90); assert linked.returncode==0,linked.stderr.decode(errors='replace')
                cases=0
                def execute(name: str,operation: str,path: Path,*args: Path,expected: bytes|None=None,failed: bool=False,fault: str='',unprivileged: bool=False):
                    nonlocal cases
                    def drop_privileges():
                        os.setgroups([]); os.setgid(65534); os.setuid(65534)
                    executable=binary if failed else audited_binary
                    r=subprocess.run([str(executable),operation,str(path),*[str(arg) for arg in args]],cwd=root,env=dict(env,FREAK_FS_TEST_FAULT=fault),capture_output=True,timeout=15,preexec_fn=drop_privileges if unprivileged else None)
                    assert not any(marker in r.stderr for marker in (b'AddressSanitizer',b'LeakSanitizer',b'UndefinedBehaviorSanitizer',b'runtime error:',b'ownership audit found')),(name,r.returncode,r.stderr)
                    if failed:
                        assert r.returncode==1 and b'SHOULD_NOT' not in r.stdout and not r.stdout and b'FREAK:' in r.stderr and b'file' in r.stderr,(name,r.returncode,r.stdout,r.stderr)
                        if fault: assert b'FAULT_CLOSED:1' in r.stderr,(name,r.stderr)
                    else: assert r.returncode==0 and (expected is None or r.stdout.replace(b'\r\n',b'\n')==expected) and not r.stderr,(name,r.returncode,r.stdout,r.stderr)
                    evidence['cases'].append({'backend':backend,'optimization':opt,'case':name,'exit_code':r.returncode,'ownership_audit':not failed,'status':'pass'}); cases+=1
                empty=root/'empty'; empty.write_bytes(b''); execute('empty-valid','read',empty,expected=b'0\nREAD_OK\n')
                data='hello λ\n'.encode()+b'a\0\xffB'; raw=root/'unicode λ raw';raw.write_bytes(data); target=root/f'copy-{backend}-{opt}'
                execute('raw-source-owner-soak','good',raw,target,expected=str(len(data)).encode()+b'\nLEGACY_FS_OK\n');assert target.read_bytes()==data+'\nλ'.encode()+b'\0tail'
                execute('missing-read','read',root/'absent',failed=True);execute('directory-read','read',root,failed=True)
                nul_prefix=root/'nul-prefix.data'
                for op in ('read','write','append'):
                    nul_prefix.write_bytes(b'untouched-prefix');execute(f'nul-path-{op}',op+'-nul',nul_prefix,failed=True)
                    assert nul_prefix.read_bytes()==b'untouched-prefix',(op,'embedded-NUL path touched its prefix')
                for op in ('write','append'):
                    execute(f'directory-{op}',op,root,failed=True);execute(f'missing-parent-{op}',op,root/'absent-dir/file',failed=True)
                    if Path('/dev/full').exists(): execute(f'dev-full-{op}',op,Path('/dev/full'),failed=True)
                if os.name!='nt':
                    fifo=root/f'fifo-{backend}-{opt}';os.mkfifo(fifo);execute('fifo-read-nonblocking','read',fifo,failed=True)
                    denied=root/f'denied-{backend}-{opt}';denied.write_bytes(b'secret');denied.chmod(0o000)
                    try:execute('permission-read','read',denied,failed=True,unprivileged=os.geteuid()==0)
                    finally:denied.chmod(0o600)
                if sys.platform.startswith('linux'):
                    fault_file=root/'fault.data'
                    for name in ('seek_error','read_short','read_growth','stream_error','close_error'):
                        fault_file.write_bytes(b'complete-input');execute('read-'+name,'read',fault_file,failed=True,fault=name)
                    for op in ('write','append'):
                        for name in ('write_short','stream_error','close_error'):
                            fault_file.write_bytes(b'');execute(op+'-'+name,op,fault_file,failed=True,fault=name)
                print(f'PASS legacy fs {backend} O{opt}: {cases} native cases',flush=True)
        assert before==fingerprint(payload),'installed payload changed during verification'
    if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(evidence,indent=2)+'\n')
    return 0

if __name__=='__main__':raise SystemExit(main())
