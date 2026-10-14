#!/usr/bin/env python3
"""Verify anchored no-replace ordinary-file publication and native consumers."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
from v3_v35_process import WINDOWS_ARGV_WRAPPER

API = '''
int64_t freak_fs_rename_relative_new_checked(int64_t, freak_word, int64_t, freak_word);
int64_t freak_llvm_fs_rename_relative_new_checked(int64_t, int64_t, int64_t, int64_t);
'''

HARNESS = r'''
#include "freak_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#include <fcntl.h>
#include <dirent.h>
#include <sys/stat.h>
#include <stdarg.h>
#endif
API_DECLARATIONS
static void require(int ok,const char *reason) { if(!ok) { fprintf(stderr,"FAIL: %s\n",reason);exit(2); } }
#ifdef USE_LLVM_ADAPTER
#define W(s) ((int64_t)(intptr_t)(s))
#define F(n) freak_llvm_fs_##n
#else
#define W(s) freak_word_lit(s)
#define F(n) freak_fs_##n
#endif
static size_t resources(void) {
#ifdef _WIN32
    DWORD count=0; require(GetProcessHandleCount(GetCurrentProcess(),&count),"handle count"); return count;
#elif defined(__linux__)
    DIR *directory=opendir("/proc/self/fd"); require(directory!=NULL,"descriptor counter");
    size_t count=0; struct dirent *entry;
    while((entry=readdir(directory))) if(strcmp(entry->d_name,".") && strcmp(entry->d_name,"..")) count++;
    require(closedir(directory)==0,"close counter"); return count;
#else
    return 0;
#endif
}
static const char *mode="",*source_path="",*outside_path="";
static int changed=0,directory_syncs=0;
#ifdef TEST_INTERPOSE
extern int __real_openat(int,const char *,int,...);
extern int __real_fsync(int);
int __wrap_openat(int parent,const char *name,int flags,...) {
    mode_t permissions=0; if(flags&O_CREAT) { va_list ap; va_start(ap,flags);permissions=va_arg(ap,int);va_end(ap); }
    int file=__real_openat(parent,name,flags,permissions);
    if(file>=0 && !changed && (flags&O_DIRECTORY) && !strcmp(name,"pivot") &&
            (!strcmp(mode,"source-race") || !strcmp(mode,"destination-race"))) {
        require(renameat(parent,"pivot",parent,"retained")==0,"exchange fixture ancestor");
        require(symlinkat(outside_path,parent,"pivot")==0,"fixture ancestor link"); changed=1;
    }
    return file;
}
int __wrap_fsync(int file) {
    struct stat info; require(fstat(file,&info)==0,"sync fixture stat");
    int status=__real_fsync(file);
    if(S_ISDIR(info.st_mode)) {
        directory_syncs++;
        if(!strcmp(mode,"directory-sync-failure") && directory_syncs==1) { errno=EIO;return -1; }
    }
    if(S_ISREG(info.st_mode) && !strcmp(mode,"file-sync-failure")) { errno=EIO;return -1; }
    if(S_ISREG(info.st_mode) && !changed && !strcmp(mode,"source-exchange")) {
        char from[4097],retained[4097],secret[4097];
        require(snprintf(from,sizeof from,"%s/a",source_path)>0 && snprintf(retained,sizeof retained,"%s/retained-a",source_path)>0 &&
            snprintf(secret,sizeof secret,"%s/a",outside_path)>0,"exchange paths");
        require(rename(from,retained)==0 && symlink(secret,from)==0,"replace admitted source"); changed=1;
    }
    return status;
}
#endif
int main(int argc,char **argv) {
    require(argc==7,"arguments"); mode=argv[5];source_path=argv[1];outside_path=argv[6];
    size_t before=resources();
    int64_t source=F(open_dir_ticket)(W(argv[1])),destination=F(open_dir_ticket)(W(argv[3]));
    require(F(result_ok)(source) && F(result_ok)(destination),"root admission");
    int64_t publication=F(rename_relative_new_checked)(source,W(argv[2]),destination,W(argv[4]));
    printf("%d %d\n",(int)F(result_ok)(publication),(int)F(result_completed)(publication));
    if(!strcmp(mode,"directory-sync-failure")) require(directory_syncs==2,"both parents synchronized even after first failure");
    F(result_release)(publication);F(result_release)(source);F(result_release)(destination);
    require(freak_fs_result_live()==0,"no live results");require(resources()==before,"all descriptors/handles closed");
    return 0;
}
'''

CONSUMER = r'''
task main() {
    pilot source = fs::open_dir_ticket(process::arg(1))
    pilot destination = fs::open_dir_ticket(process::arg(3))
    if not fs::result_ok(source) or not fs::result_ok(destination) { panic("root admission") }
    pilot mut from_name = process::arg(2)
    pilot mut to_name = process::arg(4)
    if process::arg(5) == "nul-source" { from_name = from_name + char_to_word(0) + "suffix" }
    if process::arg(5) == "nul-destination" { to_name = to_name + char_to_word(0) + "suffix" }
    pilot publication = fs::rename_relative_new_checked(source, from_name, destination, to_name)
    say fs::result_ok(publication)
    say fs::result_completed(publication)
    fs::result_release(publication)
    fs::result_release(source)
    fs::result_release(destination)
}
'''

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clang',default=os.environ.get('FREAK_CLANG','clang'))
    parser.add_argument('--compiler',type=Path,help='fresh compiler exposing FS19 for actual C/LLVM consumer proof')
    parser.add_argument('--optimization',type=int,choices=(0,2,3),action='append')
    parser.add_argument('--sanitize',action='store_true')
    parser.add_argument('--report',type=Path)
    args=parser.parse_args();repo=Path(__file__).resolve().parents[1];runtime=repo/'freakc/runtime';clang=shutil.which(args.clang);assert clang
    flags=['-lws2_32','-lshell32'] if os.name=='nt' else ['-lm']
    if args.sanitize:flags+=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-g']
    env=dict(os.environ,ASAN_OPTIONS='detect_leaks=1:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1');records=[]
    evidence={'platform':sys.platform,'sanitizers':args.sanitize,'fs_include_sha256':hashlib.sha256((runtime/'freak_v35_fs.inc').read_bytes()).hexdigest(),'cases':records}
    with tempfile.TemporaryDirectory(prefix='freak-anchored-rename-') as temporary:
        home=Path(temporary);shim=home/'headers';shim.mkdir();shutil.copyfile(runtime/'freak_runtime.h',shim/'freak_runtime.h')
        with (shim/'freak_runtime.h').open('a') as header:header.write('\n/* Frozen FS19 ABI; production registration is integration-owned. */\n'+API)
        evidence['header_shim_sha256']=hashlib.sha256((shim/'freak_runtime.h').read_bytes()).hexdigest()
        harness=home/'harness.c';harness.write_text(HARNESS.replace('API_DECLARATIONS',API).replace('int main(','static int native_main(')+WINDOWS_ARGV_WRAPPER)
        if args.sanitize:
            controls=[('asan_heap_oob','#include <stdlib.h>\nint main(int n,char**v){volatile char*p=malloc(1);p[n+4]=1;free((void*)p);return 0;}\n',b'AddressSanitizer'),('ubsan_signed_overflow','#include <stdint.h>\nint main(int n,char**v){volatile int64_t a=INT64_MAX;volatile int64_t b=a+n;return (int)b;}\n',b'runtime error: signed integer overflow')]
            for name,code,marker in controls:
                source=home/'control.c';source.write_text(code);binary=home/'control'
                subprocess.run([clang,str(source),'-O0',*flags,'-o',str(binary)],check=True,capture_output=True)
                result=subprocess.run([str(binary)],env=env,capture_output=True,timeout=10);assert result.returncode and marker in result.stderr
            evidence['failing_controls']=[entry[0] for entry in controls]
        def fixture(name):
            case=home/name;case.mkdir();source=case/'source';destination=case/'destination';outside=case/'outside'
            for directory in (source,destination,outside):directory.mkdir(mode=0o700)
            (source/'a').write_bytes(b'compiler\0\xffoutput');(source/'a').chmod(0o751)
            (outside/'a').write_bytes(b'outside-secret');(outside/'result').write_bytes(b'outside-secret')
            return source,destination,outside
        def oracle(source,destination,outside,original,from_name,to_name,moved):
            assert (outside/'a').read_bytes()==b'outside-secret' and (outside/'result').read_bytes()==b'outside-secret'
            if moved:
                assert not (source/from_name).exists() and (destination/to_name).read_bytes()==b'compiler\0\xffoutput'
                if os.name!='nt':assert (destination/to_name).stat().st_ino==original.st_ino and (destination/to_name).stat().st_mode&0o7777==0o751
        for optimization in args.optimization or (0,2,3):
            for adapter in ('c','llvm'):
                binary=home/f'{adapter}-O{optimization}';command=[clang,str(harness),str(runtime/'freak_runtime.c'),str(runtime/'freak_llvm_runtime.c'),f'-I{shim}',f'-O{optimization}','-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1','-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1',*flags,'-o',str(binary)]
                if adapter=='llvm':command+=['-DUSE_LLVM_ADAPTER=1']
                if sys.platform.startswith('linux'):command+=['-DTEST_INTERPOSE=1','-Wl,--wrap=openat','-Wl,--wrap=fsync']
                result=subprocess.run(command,capture_output=True,timeout=90);assert result.returncode==0,result.stderr
                names=['success','nested','existing','destination-directory','source-directory','missing','unsafe-source','unsafe-destination']
                if os.name!='nt':names+=['destination-link','source-link','source-ancestor-link','destination-ancestor-link','fifo','group-writable-source','world-writable-destination','public-owned-parent']
                if sys.platform.startswith('linux'):names+=['source-race','destination-race','source-exchange','file-sync-failure','directory-sync-failure']
                for name in names:
                    source,destination,outside=fixture(f'{adapter}-{optimization}-{name}');from_name='a';to_name='result';mode=name;expected=b'0 0\n';moved=False;original=(source/'a').stat()
                    if name in ('success','public-owned-parent'):expected=b'1 1\n';moved=True
                    if name=='public-owned-parent':destination.chmod(0o755)
                    if name=='nested':
                        (source/'nested').mkdir();(destination/'nested').mkdir();(source/'a').rename(source/'nested/a');from_name='nested/a';to_name='nested/result';expected=b'1 1\n';moved=True
                    prior_destination=None
                    if name=='existing':(destination/'result').write_bytes(b'old-output');prior_destination=(destination/'result').stat()
                    if name=='destination-directory':(destination/'result').mkdir()
                    if name=='source-directory':(source/'a').unlink();(source/'a').mkdir()
                    if name=='missing':from_name='absent'
                    if name=='unsafe-source':from_name='../outside/a'
                    if name=='unsafe-destination':to_name='../outside/result'
                    if name=='destination-link':(destination/'result').symlink_to(outside/'result')
                    if name=='source-link':(source/'a').unlink();(source/'a').symlink_to(outside/'a')
                    if name.endswith('ancestor-link'):
                        root=source if name.startswith('source') else destination;(root/'pivot').symlink_to(outside,target_is_directory=True)
                        if root==source:from_name='pivot/a'
                        else:to_name='pivot/result'
                    if name=='fifo':(source/'a').unlink();os.mkfifo(source/'a')
                    if name=='group-writable-source':source.chmod(0o770)
                    if name=='world-writable-destination':destination.chmod(0o777)
                    if name in ('source-race','destination-race'):
                        root=source if name=='source-race' else destination;(root/'pivot').mkdir()
                        if root==source:(source/'a').rename(source/'pivot/a');from_name='pivot/a'
                        else:to_name='pivot/result'
                        expected=b'1 1\n';moved=True
                    if name=='directory-sync-failure':expected=b'0 1\n';moved=True
                    result=subprocess.run([str(binary),str(source),from_name,str(destination),to_name,mode,str(outside)],env=env,capture_output=True,timeout=15)
                    assert result.returncode==0 and result.stdout.replace(b'\r\n',b'\n')==expected and not result.stderr,(name,result.returncode,result.stdout,result.stderr)
                    actual_from='retained/a' if name=='source-race' else from_name;actual_to='retained/result' if name=='destination-race' else to_name
                    oracle(source,destination,outside,original,actual_from,actual_to,moved)
                    if name=='source-exchange':assert (source/'retained-a').read_bytes()==b'compiler\0\xffoutput' and not (destination/'result').exists()
                    elif not moved and name not in ('source-directory','source-link','fifo'):
                        assert (source/'a').read_bytes()==b'compiler\0\xffoutput' and (source/'a').stat().st_ino==original.st_ino
                    if name=='existing':assert (destination/'result').read_bytes()==b'old-output' and (destination/'result').stat().st_ino==prior_destination.st_ino
                    if name=='destination-link':assert (destination/'result').is_symlink() and os.readlink(destination/'result')==str(outside/'result')
                    if name=='destination-directory':assert (destination/'result').is_dir() and not list((destination/'result').iterdir())
                    if name=='source-directory':assert (source/'a').is_dir() and not list((source/'a').iterdir())
                    if name=='source-link':assert (source/'a').is_symlink() and os.readlink(source/'a')==str(outside/'a')
                    if name=='fifo':assert stat.S_ISFIFO((source/'a').stat().st_mode)
                    if not moved and name not in ('existing','destination-directory','destination-link'):assert not (destination/'result').exists()
                    records.append({'adapter':adapter,'optimization':optimization,'case':name,'status':'pass'})
                print(f'PASS anchored rename {adapter} O{optimization}: {len(names)} native cases',flush=True)
        if args.compiler:
            compiler=args.compiler.resolve(strict=True);evidence['compiler_sha256']=hashlib.sha256(compiler.read_bytes()).hexdigest()
            source=home/'consumer.fk';source.write_text(CONSUMER)
            for adapter in ('c','llvm'):
                generated=Path(str(source)+('.c' if adapter=='c' else '.ll'))
                built=subprocess.run([str(compiler),str(source),'--'+adapter,'--strict-borrow'],capture_output=True,timeout=90);assert built.returncode==0,(built.stdout,built.stderr)
                assert 'freak_'+('llvm_' if adapter=='llvm' else '')+'fs_rename_relative_new_checked' in generated.read_text()
                for optimization in args.optimization or (0,2,3):
                    binary=home/f'consumer-{adapter}-{optimization}';command=[clang,str(generated),str(runtime/'freak_runtime.c'),f'-I{shim}',f'-O{optimization}','-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1','-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1',*flags,'-o',str(binary)]
                    if adapter=='llvm':command+=[str(runtime/'freak_llvm_runtime.c')]
                    linked=subprocess.run(command,capture_output=True,timeout=90);assert linked.returncode==0,linked.stderr
                    for name,expected,moved in (('success',b'true\ntrue\n',True),('existing',b'false\nfalse\n',False),('nul-source',b'false\nfalse\n',False),('nul-destination',b'false\nfalse\n',False)):
                        source_root,destination,outside=fixture(f'consumer-{adapter}-{optimization}-{name}');original=(source_root/'a').stat()
                        if name=='existing':(destination/'result').write_bytes(b'old-output')
                        result=subprocess.run([str(binary),str(source_root),'a',str(destination),'result',name],env=env,capture_output=True,timeout=15)
                        assert result.returncode==0 and result.stdout.replace(b'\r\n',b'\n')==expected and not result.stderr,(adapter,optimization,name,result.returncode,result.stdout,result.stderr)
                        oracle(source_root,destination,outside,original,'a','result',moved)
                        if not moved:
                            assert (source_root/'a').read_bytes()==b'compiler\0\xffoutput'
                            if name=='existing':assert (destination/'result').read_bytes()==b'old-output'
                            else:assert not (destination/'result').exists()
                        records.append({'adapter':adapter,'optimization':optimization,'case':'language-'+name,'status':'pass'})
        assert evidence['fs_include_sha256']==hashlib.sha256((runtime/'freak_v35_fs.inc').read_bytes()).hexdigest(),'runtime changed during verification'
    if args.report:args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(evidence,indent=2)+'\n')
    return 0

if __name__=='__main__':raise SystemExit(main())
