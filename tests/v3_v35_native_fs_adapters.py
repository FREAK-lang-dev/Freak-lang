#!/usr/bin/env python3
"""Exercise the real C and dedicated scalar FS adapters, including close faults.

Compiler-emitted namespace routing is verified separately by
v3_v35_runtime_aliases.py. These native ABI fixtures exercise both carriers at
O0/O2/O3 and preserve historical strcmp/NUL-prefix comparison semantics.
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

from v3_v35_legacy_fs import AUDIT_CONTROL, FAULTS

HARNESS = r'''
#include "freak_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
extern void freak_llvm_word_release_replaced(int64_t,int64_t);
#ifdef USE_LLVM_ADAPTER
typedef int64_t word;
static word literal(const char *v){return (int64_t)(intptr_t)v;}
static word owned(const char *v,size_t n){char *p=malloc(n+1);if(!p)exit(70);memcpy(p,v,n);p[n]=0;return freak_llvm_word_adopt_sized((int64_t)(intptr_t)p,n);}
static freak_word view(word v){return freak_llvm_word_view(v);}
static void drop(word v){freak_llvm_word_release_replaced(v,0);}
#define read_file freak_llvm_fs_read_native
#define write_file freak_llvm_fs_write_native
#define append_file freak_llvm_fs_append_native
#define exists_file freak_llvm_fs_exists_native
#define delete_file freak_llvm_fs_delete_native
#define compare freak_llvm_word_compare
#else
typedef freak_word word;
static word literal(const char *v){return freak_word_lit(v);}
static word owned(const char *v,size_t n){char *p=malloc(n+1);if(!p)exit(70);memcpy(p,v,n);p[n]=0;return freak_word_own(p,n);}
static freak_word view(word v){return v;}
static void drop(word v){freak_word_release_owned(&v);}
#define read_file freak_fs_read
#define write_file freak_fs_write
#define append_file freak_fs_append
#define exists_file freak_fs_exists
#define delete_file freak_fs_delete
#define compare freak_word_compare
#endif
#define REQUIRE(v) do{if(!(v)){fprintf(stderr,"fixture assertion %d\n",__LINE__);return 71;}}while(0)
int main(int argc,char **argv){
    if(argc<3)return 70;
    const char *operation=argv[1]; word path=literal(argv[2]);
    if(strstr(operation,"-nul")){
        size_t n=strlen(argv[2]);char *data=malloc(n+8);if(!data)return 70;
        memcpy(data,argv[2],n);memcpy(data+n,"\0suffix",7);path=owned(data,n+7);free(data);
        if(!strcmp(operation,"read-nul"))operation="read";
        else if(!strcmp(operation,"write-nul"))operation="write";
        else operation="append";
    }
    if(!strcmp(operation,"good")){
        REQUIRE(argc==4);word target=literal(argv[3]);word contents=read_file(path);
        write_file(target,contents);word tail=owned("\n\xce\xbb\0tail",8);append_file(target,tail);drop(tail);
        for(int i=0;i<100;i++){word repeated=read_file(path);freak_word a=view(contents),b=view(repeated);REQUIRE(a.length==b.length&&!memcmp(a.data,b.data,a.length));drop(repeated);}
        printf("%zu\nLEGACY_FS_OK\n",view(contents).length);drop(contents);
    }else if(!strcmp(operation,"read")){
        word contents=read_file(path);printf("%zu\nREAD_OK\n",view(contents).length);drop(contents);
    }else if(!strcmp(operation,"write")){write_file(path,literal("complete-output"));puts("SHOULD_NOT");}
    else if(!strcmp(operation,"append")){append_file(path,literal("complete-output"));puts("SHOULD_NOT");}
    else if(!strcmp(operation,"facts")){
        REQUIRE(argc==4);word directory=literal(argv[3]);REQUIRE(exists_file(path)&&exists_file(directory));
        size_t n=strlen(argv[2]);char *data=malloc(n+8);if(!data)return 70;memcpy(data,argv[2],n);memcpy(data+n,"\0suffix",7);
        word invalid=owned(data,n+7);free(data);REQUIRE(!exists_file(invalid)&&!delete_file(invalid));
#ifdef USE_LLVM_ADAPTER
        REQUIRE(!freak_path_exists(invalid));
#endif
        drop(invalid);REQUIRE(exists_file(path));
        REQUIRE(!exists_file(literal(""))&&!delete_file(literal("")));
        word utf8=owned("\xff",1);REQUIRE(!exists_file(utf8)&&!delete_file(utf8));drop(utf8);
        REQUIRE(!delete_file(directory)&&exists_file(directory));
        REQUIRE(delete_file(path)&&!exists_file(path)&&delete_file(path));
        puts("NATIVE_FS_FACTS_OK");
    }else if(!strcmp(operation,"compare")){
        for(int i=0;i<1024;i++){
            word a=owned("a\0z",3),b=owned("a\0x",3);
            REQUIRE(compare(a,b)==0);drop(a);drop(b);
            REQUIRE(compare(literal(""),literal("a"))==-1&&compare(literal("z"),literal("a"))==1&&compare(literal("equal"),literal("equal"))==0);
            REQUIRE(compare(literal("\xce\xbb"),literal("\xce\xbb"))==0);
        }puts("NATIVE_COMPARE_OK");
    }else return 70;
    return 0;
}
'''


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime',type=Path,help='directory containing actual freak_runtime.c')
    parser.add_argument('--clang',default=os.environ.get('FREAK_CLANG','clang'))
    parser.add_argument('--optimization',type=int,choices=(0,2,3),action='append')
    parser.add_argument('--sanitize',action='store_true')
    parser.add_argument('--report',type=Path)
    args=parser.parse_args();runtime=(args.runtime or Path(__file__).resolve().parents[1]/'freakc/runtime').resolve(strict=True)
    clang=shutil.which(args.clang);assert clang
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in runtime.iterdir() if p.is_file()}
    flags=['-lws2_32','-lshell32'] if os.name=='nt' else ['-lm']
    environment=dict(os.environ,ASAN_OPTIONS='detect_leaks=1:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
    cases=[];controls=[]
    with tempfile.TemporaryDirectory(prefix='freak-native-fs-adapters-') as temporary:
        root=Path(temporary);source=root/'harness.c';source.write_text(HARNESS)
        faults=root/'faults.c';faults.write_text(FAULTS)
        def build(path:Path,inputs:list[str],extra:list[str]):
            result=subprocess.run([clang,*inputs,f'-I{runtime}',*extra,*flags,'-o',str(path)],capture_output=True,timeout=90)
            assert result.returncode==0,result.stderr
        sanitizer=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-g'] if args.sanitize else []
        if args.sanitize:
            control=root/'control.c';binary=root/'control'
            for name,body,diagnostic in [('asan_heap_oob','#include <stdlib.h>\nint main(int n,char**v){volatile char*p=malloc(1);p[n+4]=1;free((void*)p);return 0;}\n',b'AddressSanitizer'),('ubsan_signed_overflow','#include <stdint.h>\nint main(int n,char**v){volatile int64_t a=INT64_MAX;volatile int64_t b=a+n;return (int)b;}\n',b'runtime error: signed integer overflow')]:
                control.write_text(body);build(binary,[str(control)],['-O0',*sanitizer]);result=subprocess.run([str(binary)],env=environment,capture_output=True,timeout=15)
                assert result.returncode!=0 and diagnostic in result.stderr,result;controls.append(name)
        audit_source=root/'audit.c';audit_source.write_text(AUDIT_CONTROL);audit_binary=root/'audit'
        build(audit_binary,[str(audit_source),str(runtime/'freak_runtime.c')],['-O0','-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1','-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1',*sanitizer])
        for name,code,diagnostic in [('c',87,b'C ownership audit found 1'),('llvm',86,b'LLVM ownership audit found 1'),('filesystem',1,b'1 live filesystem result')]:
            result=subprocess.run([str(audit_binary),name],cwd=root,env=environment,capture_output=True,timeout=15)
            assert result.returncode==code and diagnostic in result.stderr,result;controls.append('ownership_'+name)
        for adapter in ('c','llvm'):
            for opt in args.optimization or (0,2,3):
                binary=root/f'{adapter}-{opt}';audited=root/f'{adapter}-{opt}-audit'
                inputs=[str(source),str(runtime/'freak_runtime.c')];extra=[f'-O{opt}',*sanitizer]
                if adapter=='llvm':inputs.append(str(runtime/'freak_llvm_runtime.c'));extra.append('-DUSE_LLVM_ADAPTER=1')
                if sys.platform.startswith('linux'):inputs.append(str(faults));extra += [f'-Wl,--wrap={n}' for n in ('fopen','fdopen','fseek','fread','fwrite','ferror','fclose')]
                build(binary,inputs,extra);build(audited,inputs,[*extra,'-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1','-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1'])
                def execute(name:str,operation:str,path:Path,*more:Path,expected:bytes|None=None,failed:bool=False,fault:str=''):
                    result=subprocess.run([str(binary if failed else audited),operation,str(path),*[str(v) for v in more]],cwd=root,env=dict(environment,FREAK_FS_TEST_FAULT=fault),capture_output=True,timeout=15)
                    assert not any(v in result.stderr for v in (b'AddressSanitizer',b'LeakSanitizer',b'runtime error:',b'ownership audit found')),(name,result)
                    if failed:
                        assert result.returncode==1 and not result.stdout and b'FREAK:' in result.stderr and b'file' in result.stderr,(name,result)
                        if fault:assert b'FAULT_CLOSED:1' in result.stderr,(name,result)
                    else:assert result.returncode==0 and not result.stderr and (expected is None or result.stdout.replace(b'\r\n',b'\n')==expected),(name,result)
                    cases.append({'adapter':adapter,'optimization':opt,'case':name,'ownership_audit':not failed,'status':'pass'})
                empty=root/'empty';empty.write_bytes(b'');execute('empty-read','read',empty,expected=b'0\nREAD_OK\n')
                data='hello λ\n'.encode()+b'a\0\xffB';raw=root/'unicode λ raw';raw.write_bytes(data);target=root/'target λ'
                execute('raw-source-soak','good',raw,target,expected=str(len(data)).encode()+b'\nLEGACY_FS_OK\n');assert target.read_bytes()==data+b'\n\xce\xbb\0tail'
                execute('missing-read','read',root/'missing',failed=True);execute('directory-read','read',root,failed=True)
                for operation in ('read','write','append'):
                    prefix=root/'prefix';prefix.write_bytes(b'untouched');execute('nul-path-'+operation,operation+'-nul',prefix,failed=True);assert prefix.read_bytes()==b'untouched'
                for operation in ('write','append'):
                    execute('directory-'+operation,operation,root,failed=True);execute('missing-parent-'+operation,operation,root/'missing-parent/file',failed=True)
                    if Path('/dev/full').exists():execute('dev-full-'+operation,operation,Path('/dev/full'),failed=True)
                if os.name!='nt':
                    fifo=root/f'fifo-{adapter}-{opt}';os.mkfifo(fifo);execute('fifo-read','read',fifo,failed=True)
                    denied=root/'denied';denied.write_bytes(b'secret');denied.chmod(0)
                    try:
                        if os.geteuid()!=0:execute('permission-read','read',denied,failed=True)
                    finally:denied.chmod(0o600)
                if sys.platform.startswith('linux'):
                    path=root/'fault.data'
                    for fault in ('seek_error','read_short','read_growth','stream_error','close_error'):
                        path.write_bytes(b'complete-input');execute('read-'+fault,'read',path,failed=True,fault=fault)
                    for operation in ('write','append'):
                        for fault in ('write_short','stream_error','close_error'):
                            path.write_bytes(b'');execute(operation+'-'+fault,operation,path,failed=True,fault=fault)
                file=root/'delete λ';file.write_bytes(b'owned');directory=root/'directory λ';directory.mkdir(exist_ok=True)
                invalid_name=os.fsencode(root)+b'/\xff'
                if os.name!='nt':
                    descriptor=os.open(invalid_name,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600);os.write(descriptor,b'preserved-invalid-utf8');os.close(descriptor)
                execute('exists-delete-sized-paths','facts',file,directory,expected=b'NATIVE_FS_FACTS_OK\n');assert directory.is_dir() and not file.exists()
                if os.name!='nt':
                    with open(invalid_name,'rb') as stream:assert stream.read()==b'preserved-invalid-utf8'
                execute('compare-nul-prefix-and-order','compare',root,expected=b'NATIVE_COMPARE_OK\n')
                print(f'PASS native FS adapters {adapter} O{opt}',flush=True)
    assert hashes=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in runtime.iterdir() if p.is_file()},'runtime changed during gate'
    evidence={'host':sys.platform,'runtime_sha256':hashes,'cases':cases,'failing_controls':controls,'sanitizers':args.sanitize,'scope':'Real native C/scalar adapter calls; compiler namespace routing tested separately. Fatal exits use normal ownership mode; successful/soak paths use ownership audits. Native Windows execution pending on Linux.'}
    if args.report:args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(evidence,indent=2)+'\n')
    print(f'PASS native FS adapters: {len(cases)} cases',flush=True);return 0


if __name__=='__main__':raise SystemExit(main())
