#!/usr/bin/env python3
"""Native descriptor/HANDLE containment and owned-stage I/O adversarial gate.

C and LLVM scalar-adapter tests use independent filesystem oracles. Linux
interposition exchanges an ancestor after it is opened and grows a bounded
file after fstat. Other hosts run the portable API checks; native platform
execution is reported only when this gate actually runs on that platform.
"""
from __future__ import annotations
import argparse
import json
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
#include <errno.h>
#ifdef _WIN32
#include <windows.h>
#else
#include <dirent.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#endif
/* Header registration belongs to the integration owner. */
extern int64_t freak_fs_open_dir_ticket(freak_word);
extern int64_t freak_fs_read_bytes_limit_ticket(freak_word,int64_t);
extern int64_t freak_fs_read_relative_ticket(int64_t,freak_word);
extern int64_t freak_fs_read_source_relative_ticket(int64_t,freak_word);
extern int64_t freak_fs_read_relative_bytes_ticket(int64_t,freak_word);
extern int64_t freak_fs_read_relative_bytes_limit_ticket(int64_t,freak_word,int64_t);
extern int64_t freak_fs_write_relative_bytes_checked(int64_t,freak_word,int64_t);
extern int64_t freak_fs_remove_temp_dir_checked(int64_t);
extern int64_t freak_fs_publish_temp_dir_checked(int64_t,int64_t,freak_word);
extern bool freak_fs_result_completed(int64_t);
extern int64_t freak_fs_lock_dir_ticket(int64_t,freak_word);
extern int64_t freak_fs_remove_relative_file_checked(int64_t,freak_word);
extern int64_t freak_fs_mkdir_relative_checked(int64_t,freak_word);
extern int64_t freak_fs_open_relative_dir_ticket(int64_t,freak_word);
extern int64_t freak_llvm_fs_open_dir_ticket(int64_t);
extern int64_t freak_llvm_fs_read_bytes_limit_ticket(int64_t,int64_t);
extern int64_t freak_llvm_fs_read_relative_ticket(int64_t,int64_t);
extern int64_t freak_llvm_fs_read_source_relative_ticket(int64_t,int64_t);
extern int64_t freak_llvm_fs_read_relative_bytes_ticket(int64_t,int64_t);
extern int64_t freak_llvm_fs_read_relative_bytes_limit_ticket(int64_t,int64_t,int64_t);
extern int64_t freak_llvm_fs_write_relative_bytes_checked(int64_t,int64_t,int64_t);
extern int64_t freak_llvm_fs_remove_temp_dir_checked(int64_t);
extern int64_t freak_llvm_fs_publish_temp_dir_checked(int64_t,int64_t,int64_t);
extern int64_t freak_llvm_fs_result_completed(int64_t);
extern int64_t freak_llvm_fs_lock_dir_ticket(int64_t,int64_t);
extern int64_t freak_llvm_fs_remove_relative_file_checked(int64_t,int64_t);
extern int64_t freak_llvm_fs_mkdir_relative_checked(int64_t,int64_t);
extern int64_t freak_llvm_fs_open_relative_dir_ticket(int64_t,int64_t);
static void require(int ok,const char *why) { if (!ok) { fprintf(stderr,"FAIL: %s\n",why); exit(2); } }
#ifdef USE_LLVM_ADAPTER
#define W(s) ((int64_t)(intptr_t)(s))
#define F(n) freak_llvm_fs_##n
extern void freak_llvm_word_release_replaced(int64_t,int64_t);
static freak_word word(int64_t h) { return freak_llvm_word_view(F(result_word)(h)); }
static void drop(freak_word *w) { freak_llvm_word_release_replaced((int64_t)(intptr_t)w->data,0); }
#else
#define W(s) freak_word_lit(s)
#define F(n) freak_fs_##n
#define word freak_fs_result_word
#define drop freak_word_release_owned
#endif
static void success(int64_t h) { require(F(result_ok)(h),"expected successful operation"); F(result_release)(h); }
static void failed(int64_t h) { require(!F(result_ok)(h),"expected refused operation"); F(result_release)(h); }
static void exact(int64_t h,const char *bytes,size_t n) { require(F(result_ok)(h),"successful anchored read"); freak_word w=word(h); require(w.length==n && !memcmp(w.data,bytes,n),"anchored bytes preserved"); drop(&w); F(result_release)(h); }
static int64_t buffer(const char *s) { int64_t b=freak_byte_buffer_new(); freak_byte_buffer_write_word(b,freak_word_lit(s)); require(b!=0,"buffer"); return b; }
#ifdef TEST_INTERPOSE
#include <stdarg.h>
extern int __real_openat(int,const char *,int,...);
extern ssize_t __real_read(int,void *,size_t);
extern int __real_fsync(int);
static int exchange=0,grow=0,sync_fault=0; static size_t read_total=0,read_max=0;
static char swap_path[8192],old_path[8192],outside_path[8192],grow_path[8192];
int __wrap_openat(int parent,const char *name,int flags,...) {
    va_list args; va_start(args,flags); mode_t mode=(flags&O_CREAT)?(mode_t)va_arg(args,int):0; va_end(args);
    int fd=__real_openat(parent,name,flags,mode);
    if (exchange && fd>=0 && !strcmp(name,"sub") && (flags&O_DIRECTORY)) {
        exchange=0; require(rename(swap_path,old_path)==0,"exchange admitted ancestor"); require(symlink(outside_path,swap_path)==0,"replace ancestor with outside link");
    }
    return fd;
}
ssize_t __wrap_read(int fd,void *bytes,size_t count) {
    if (grow) { grow=0; int file=open(grow_path,O_WRONLY|O_APPEND); require(file>=0,"growth file"); char chunk[8192]; memset(chunk,'x',sizeof(chunk)); for(int i=0;i<16;i++) require(write(file,chunk,sizeof(chunk))==sizeof(chunk),"append growth"); close(file); }
    if (count>read_max) read_max=count;
    ssize_t n=__real_read(fd,bytes,count); if(n>0) read_total+=(size_t)n; return n;
}
int __wrap_fsync(int fd) { struct stat info; if(sync_fault && fstat(fd,&info)==0 && S_ISDIR(info.st_mode)) { errno=EIO; return -1; } return __real_fsync(fd); }
static void paths(const char *root,const char *outside) { snprintf(swap_path,sizeof(swap_path),"%s/sub",root); snprintf(old_path,sizeof(old_path),"%s/old-sub",root); snprintf(outside_path,sizeof(outside_path),"%s",outside); }
#endif
#ifndef _WIN32
static int descriptors(void) { DIR *d=opendir("/proc/self/fd"); if(!d)return -1; int n=0; while(readdir(d))n++; closedir(d);return n; }
#endif
int main(int argc,char **argv) {
    if(argc<3)return 90; const char *mode=argv[1],*path=argv[2];
    if(!strcmp(mode,"foreign")) { F(read_relative_ticket)((int64_t)UINT64_C(0x8000000100000001),W("x")); return 99; }
    if(!strcmp(mode,"stale")) { int64_t d=F(open_dir_ticket)(W(path)); F(result_release)(d); F(read_relative_ticket)(d,W("x")); return 99; }
    if(!strcmp(mode,"wrong-kind")) { int64_t d=F(read_ticket)(W(path)); F(read_relative_ticket)(d,W("x")); return 99; }
    if(!strcmp(mode,"open-long-fails")) {
        size_t length=strlen(path); char *long_path=calloc(length+5001,1); require(long_path!=NULL,"long path allocation"); memcpy(long_path,path,length);
        for(size_t i=0;i<2500;i++) memcpy(long_path+length+i*2,"/.",2);
        failed(F(open_dir_ticket)(W(long_path))); free(long_path); return 0;
    }
    if(!strcmp(mode,"open-fails")) { failed(F(open_dir_ticket)(W(path))); return 0; }
    if(!strcmp(mode,"limit")) { failed(F(read_bytes_limit_ticket)(W(path),4096)); return 0; }
    int64_t d=F(open_dir_ticket)(W(path)); require(F(result_ok)(d),"anchor root");
    if(!strcmp(mode,"lock-hold")) {
        int64_t lock=F(lock_dir_ticket)(d,W("transaction.lock")); require(F(result_ok)(lock),"holder acquired"); puts("LOCKED"); fflush(stdout);
#ifdef _WIN32
        Sleep(60000);
#else
        pause();
#endif
        F(result_release)(lock); F(result_release)(d); return 0;
    }
    if(!strcmp(mode,"lock-fails")) { failed(F(lock_dir_ticket)(d,W("transaction.lock"))); F(result_release)(d); return 0; }
    if(!strcmp(mode,"lock-once")) { success(F(lock_dir_ticket)(d,W("transaction.lock"))); F(result_release)(d); return 0; }
    if(!strcmp(mode,"smoke")) {
        exact(F(read_relative_ticket)(d,W("sub/value")),"owned",5);
        exact(F(read_source_relative_ticket)(d,W("raw")),"a\0\xff" "b",4);
        failed(F(read_relative_ticket)(d,W("raw")));
        failed(F(read_relative_bytes_limit_ticket)(d,W("raw"),-1)); failed(F(read_relative_bytes_limit_ticket)(d,W("raw"),67108865));
        const char *unsafe[]={"../secret","sub/../value","/secret","sub//value","sub/./value","sub/","sub\\value","C:secret",".",".."};
        for(size_t i=0;i<sizeof(unsafe)/sizeof(*unsafe);i++) failed(F(read_relative_ticket)(d,W(unsafe[i])));
#ifndef _WIN32
        failed(F(read_relative_ticket)(d,W("link/secret"))); failed(F(read_relative_ticket)(d,W("file-link")));
        int64_t b=buffer("changed"); failed(F(write_relative_bytes_checked)(d,W("link/secret"),b)); failed(F(write_relative_bytes_checked)(d,W("file-link"),b)); failed(F(mkdir_relative_checked)(d,W("link/new-dir"))); failed(F(open_relative_dir_ticket)(d,W("link")));
#else
        int64_t b=buffer("changed");
#endif
        success(F(mkdir_relative_checked)(d,W("new-dir"))); failed(F(mkdir_relative_checked)(d,W("new-dir")));
        success(F(mkdir_relative_checked)(d,W("new-dir/nested"))); success(F(open_relative_dir_ticket)(d,W("new-dir/nested"))); failed(F(open_relative_dir_ticket)(d,W("raw"))); failed(F(mkdir_relative_checked)(d,W("missing-dir/nested")));
        success(F(write_relative_bytes_checked)(d,W("new-dir/nested/output"),b));
        success(F(write_relative_bytes_checked)(d,W("sub/output"),b)); freak_byte_buffer_release(b);
        exact(F(read_relative_ticket)(d,W("sub/output")),"changed",7);
        failed(F(remove_temp_dir_checked)(d));
        int64_t lock=F(lock_dir_ticket)(d,W("transaction.lock")); require(F(result_ok)(lock),"transaction lock acquired");
        failed(F(lock_dir_ticket)(d,W("transaction.lock"))); F(result_release)(lock);
        success(F(lock_dir_ticket)(d,W("transaction.lock"))); failed(F(lock_dir_ticket)(d,W("../escape")));
#ifndef _WIN32
        require(chmod(path,0755)==0,"expose parent fixture"); failed(F(lock_dir_ticket)(d,W("transaction.lock"))); require(chmod(path,0700)==0,"restore private parent");
#endif
        success(F(remove_relative_file_checked)(d,W("sub/output"))); failed(F(remove_relative_file_checked)(d,W("sub")));
#ifndef _WIN32
        success(F(remove_relative_file_checked)(d,W("file-link")));
#endif
        int64_t temp=F(temp_dir)(W(path),W("owned")); require(F(result_ok)(temp),"owned stage");
        b=buffer("stage"); success(F(write_relative_bytes_checked)(temp,W("value"),b)); freak_byte_buffer_release(b);
        int64_t published=F(publish_temp_dir_checked)(temp,d,W("published")); require(F(result_ok)(published)&&F(result_completed)(published),"anchored publication"); F(result_release)(published);
        exact(F(read_relative_ticket)(temp,W("value")),"stage",5); success(F(remove_temp_dir_checked)(temp)); F(result_release)(temp);
        temp=F(temp_dir)(W(path),W("owned")); failed(F(publish_temp_dir_checked)(temp,d,W("sub"))); success(F(remove_temp_dir_checked)(temp)); F(result_release)(temp);
#ifndef _WIN32
        int before=descriptors();
#endif
        for(int i=0;i<300;i++) { int64_t a=F(open_dir_ticket)(W(path)); require(F(result_ok)(a),"repeat anchor"); exact(F(read_relative_ticket)(a,W("sub/value")),"owned",5); F(result_release)(a); }
#ifndef _WIN32
        require(before==descriptors(),"directory descriptors released");
#endif
        for(int i=0;i<80;i++) { int64_t t=F(temp_dir)(W(path),W("soak")); require(F(result_ok)(t),"repeat stage"); success(F(remove_temp_dir_checked)(t)); F(result_release)(t); success(F(lock_dir_ticket)(d,W("transaction.lock"))); }
#ifndef _WIN32
        require(before==descriptors(),"stage and lock descriptors released");
#endif
        F(result_release)(d); require(freak_fs_result_live()==0,"all tickets released"); puts("ANCHORED_OK"); return 0;
    }
#ifdef TEST_INTERPOSE
    if(!strcmp(mode,"read-race") || !strcmp(mode,"write-race")) {
        require(argc==4,"outside argument"); paths(path,argv[3]); exchange=1;
        if(!strcmp(mode,"read-race")) exact(F(read_relative_ticket)(d,W("sub/value")),"owned",5);
        else { int64_t b=buffer("changed"); success(F(write_relative_bytes_checked)(d,W("sub/value"),b)); freak_byte_buffer_release(b); }
    } else if(!strcmp(mode,"growth")) {
        snprintf(grow_path,sizeof(grow_path),"%s/marker",path); grow=1; read_total=read_max=0;
        failed(F(read_relative_bytes_limit_ticket)(d,W("marker"),4096)); require(read_total<=4097 && read_max<=4097,"growth bounded by budget plus detection byte");
    } else if(!strcmp(mode,"fault-rename")) {
        char from[8192],to[8192]; snprintf(from,sizeof(from),"%s/from",path); snprintf(to,sizeof(to),"%s/to",path);
        success(F(write_checked)(W(from),W("complete"))); sync_fault=1;
        int64_t r=F(rename_checked)(W(from),W(to)); require(!F(result_ok)(r)&&F(result_completed)(r),"legacy rename completed sync failure distinguished"); F(result_release)(r);
    } else if(!strcmp(mode,"cleanup-descendant-race")) {
        int64_t temp=F(temp_dir)(W(path),W("owned")); freak_word p=word(temp); char sub[8192]; snprintf(sub,sizeof(sub),"%s/sub",p.data); success(F(mkdir_checked)(W(sub)));
        paths(p.data,argv[3]); drop(&p); int64_t b=buffer("owned"); success(F(write_relative_bytes_checked)(temp,W("sub/value"),b)); freak_byte_buffer_release(b);
        exchange=1; failed(F(remove_temp_dir_checked)(temp)); F(result_release)(temp);
    } else if(!strcmp(mode,"fault-publish")) {
        int64_t temp=F(temp_dir)(W(path),W("owned")); require(F(result_ok)(temp),"owned fault stage"); sync_fault=1;
        int64_t r=F(publish_temp_dir_checked)(temp,d,W("published")); require(!F(result_ok)(r)&&F(result_completed)(r),"completed sync failure distinguished"); F(result_release)(r);
        sync_fault=0; success(F(remove_temp_dir_checked)(temp)); F(result_release)(temp);
    } else
#endif
    if(!strcmp(mode,"temp-swap")) {
#ifndef _WIN32
        int64_t temp=F(temp_dir)(W(path),W("owned")); freak_word p=word(temp); char old[8192]; snprintf(old,sizeof(old),"%s-old",p.data); require(rename(p.data,old)==0 && mkdir(p.data,0700)==0,"substitute stage identity");
        failed(F(remove_temp_dir_checked)(temp)); failed(F(publish_temp_dir_checked)(temp,d,W("published"))); drop(&p); F(result_release)(temp);
#endif
    } else if(!strcmp(mode,"cleanup-parent-race")) {
#ifndef _WIN32
        require(argc==4,"outside argument"); int64_t temp=F(temp_dir)(W(path),W("owned")); int64_t b=buffer("owned"); success(F(write_relative_bytes_checked)(temp,W("value"),b)); freak_byte_buffer_release(b);
        char old[8192]; snprintf(old,sizeof(old),"%s-old",path); require(rename(path,old)==0 && symlink(argv[3],path)==0,"exchange stage ancestor"); success(F(remove_temp_dir_checked)(temp)); F(result_release)(temp);
#endif
    } else if(!strcmp(mode,"cleanup-link")) {
#ifndef _WIN32
        require(argc==4,"outside argument"); int64_t temp=F(temp_dir)(W(path),W("owned")); freak_word p=word(temp); char link[8192]; snprintf(link,sizeof(link),"%s/link",p.data); require(symlink(argv[3],link)==0,"stage link"); drop(&p); success(F(remove_temp_dir_checked)(temp)); F(result_release)(temp);
#endif
    } else if(!strcmp(mode,"cleanup-depth")) {
        int64_t temp=F(temp_dir)(W(path),W("deep")); require(F(result_ok)(temp),"depth stage"); freak_word p=word(temp);
        char nested[8192];
#ifdef _WIN32
        snprintf(nested,sizeof(nested),strncmp(p.data,"\\\\?\\",4) ? "\\\\?\\%s" : "%s",p.data);
        for(char *cursor=nested;*cursor;cursor++) if(*cursor=='/')*cursor='\\';
#else
        snprintf(nested,sizeof(nested),"%s",p.data);
#endif
        drop(&p);
        for(int i=0;i<129;i++) {
#ifdef _WIN32
            strcat(nested,"\\d");
#else
            strcat(nested,"/d");
#endif
            success(F(mkdir_checked)(W(nested)));
        }
        failed(F(remove_temp_dir_checked)(temp)); F(result_release)(temp);
    } else if(!strcmp(mode,"binary")) {
        int64_t r=F(read_relative_bytes_ticket)(d,W("raw")); require(F(result_ok)(r),"binary relative"); int64_t b=F(result_bytes)(r); require(freak_byte_buffer_length(b)==4,"binary length"); F(result_release)(r); freak_byte_buffer_release(b);
    } else { F(result_release)(d); return 91; }
    F(result_release)(d); require(freak_fs_result_live()==0,"all tickets released"); return 0;
}
'''


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clang',default=os.environ.get('FREAK_CLANG','clang'))
    parser.add_argument('--optimization',type=int,choices=(0,2,3),action='append')
    parser.add_argument('--sanitize',action='store_true')
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    compiler=shutil.which(args.clang); assert compiler
    runtime=Path(__file__).resolve().parents[1]/'freakc/runtime'
    flags=['-lws2_32','-lshell32'] if os.name=='nt' else ['-lm']
    if args.sanitize: flags+=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-g']
    env=dict(os.environ,ASAN_OPTIONS='detect_leaks=1:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
    records=[]
    with tempfile.TemporaryDirectory(prefix='freak-anchor λ $ ') as tmp:
        home=Path(tmp).resolve(); source=home/'harness.c'; source.write_text(HARNESS.replace('int main(', 'static int native_main(')+WINDOWS_ARGV_WRAPPER,encoding='utf8')
        if args.sanitize:
            control=home/'control.c'; control.write_text('#include <stdlib.h>\nint main(int n,char**v){volatile char*p=malloc(1);p[n+4]=1;free((void*)p);return 0;}\n')
            exe=home/'control'; subprocess.run([compiler,str(control),'-O0',*flags,'-o',str(exe)],check=True,capture_output=True)
            result=subprocess.run([str(exe)],capture_output=True,env=env,timeout=10)
            assert result.returncode and b'AddressSanitizer' in result.stderr
            control.write_text('#include <stdint.h>\nint main(int n,char**v){volatile int64_t a=INT64_MAX;volatile int64_t b=a+n;return (int)b;}\n')
            subprocess.run([compiler,str(control),'-O0',*flags,'-o',str(exe)],check=True,capture_output=True)
            result=subprocess.run([str(exe)],capture_output=True,env=env,timeout=10)
            assert result.returncode and b'runtime error: signed integer overflow' in result.stderr
        for opt in args.optimization or (0,2,3):
            for adapter in ('c','llvm'):
                exe=home/f'{adapter}-O{opt}{".exe" if os.name=="nt" else ""}'; command=[compiler,str(source),str(runtime/'freak_runtime.c'),str(runtime/'freak_llvm_runtime.c'),f'-I{runtime}',f'-O{opt}','-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1',*flags,'-o',str(exe)]
                if adapter=='llvm': command+=['-DUSE_LLVM_ADAPTER=1']
                if sys.platform.startswith('linux'): command+=['-DTEST_INTERPOSE=1','-Wl,--wrap=openat','-Wl,--wrap=read','-Wl,--wrap=fsync']
                built=subprocess.run(command,capture_output=True,timeout=90); assert built.returncode==0,built.stderr.decode(errors='replace')
                modes=['smoke','binary','limit','cleanup-depth','open-long-fails','temp-swap','cleanup-parent-race','cleanup-link'] if os.name!='nt' else ['smoke','binary','limit','cleanup-depth','open-long-fails']
                if sys.platform.startswith('linux'): modes+=['read-race','write-race','growth','fault-publish','fault-rename','cleanup-descendant-race']
                for mode in modes+['foreign','stale','wrong-kind','open-fails']:
                    case=home/f'{adapter}-{opt}-{mode}'; case.mkdir(); root=case/'root'; root.mkdir(mode=0o700); (root/'sub').mkdir(); (root/'sub/value').write_bytes(b'owned'); (root/'raw').write_bytes(b'a\0\xffb'); (root/'marker').write_bytes(b'small')
                    outside=case/'outside'; outside.mkdir(); (outside/'value').write_bytes(b'outside-secret'); (outside/'secret').write_bytes(b'outside-secret')
                    if os.name!='nt': (root/'link').symlink_to(outside,target_is_directory=True); (root/'file-link').symlink_to(outside/'secret')
                    input_path=root
                    if mode=='limit': input_path=root/'large'; input_path.write_bytes(b'x'*4097)
                    if mode=='wrong-kind': input_path=root/'sub/value'
                    if mode=='open-fails': input_path=root/'link' if os.name!='nt' else root/'raw'
                    result=subprocess.run([str(exe),mode,str(input_path),str(outside)],capture_output=True,timeout=20,env=env)
                    if mode in ('foreign','stale'): assert result.returncode!=0 and b'stale filesystem' in result.stderr,(mode,result.stderr)
                    elif mode=='wrong-kind': assert result.returncode!=0 and b'directory ticket' in result.stderr,(mode,result.stderr)
                    else: assert result.returncode==0,(mode,result.stdout,result.stderr)
                    assert (outside/'value').read_bytes()==b'outside-secret' and (outside/'secret').read_bytes()==b'outside-secret'
                    if mode=='write-race': assert (root/'old-sub/value').read_bytes()==b'changed'
                    if mode=='fault-publish': assert not (root/'published').exists()
                    if mode=='fault-rename': assert not (root/'from').exists() and (root/'to').read_bytes()==b'complete'
                    if mode=='temp-swap': assert len(list(root.glob('owned*')))==2
                    records.append({'adapter':adapter,'optimization':opt,'case':mode,'status':'pass'})
                locked=home/f'{adapter}-{opt}-lock'; locked.mkdir(mode=0o700)
                holder=subprocess.Popen([str(exe),'lock-hold',str(locked)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env)
                try:
                    assert holder.stdout and holder.stdout.readline()==b'LOCKED\n'
                    contender=subprocess.run([str(exe),'lock-fails',str(locked)],capture_output=True,env=env,timeout=10)
                    assert contender.returncode==0,contender.stderr
                    holder.kill(); holder.communicate(timeout=10)
                    retry=subprocess.run([str(exe),'lock-once',str(locked)],capture_output=True,env=env,timeout=10)
                    assert retry.returncode==0,retry.stderr
                    assert (locked/'transaction.lock').is_file()
                    records.append({'adapter':adapter,'optimization':opt,'case':'killed-lock-holder-retry','status':'pass'})
                finally:
                    if holder.poll() is None: holder.kill(); holder.communicate(timeout=10)
                print(f'PASS anchored filesystem {adapter} O{opt}: {len(modes)+5} cases',flush=True)
    if args.report: args.report.parent.mkdir(parents=True,exist_ok=True); args.report.write_text(json.dumps({'platform':sys.platform,'machine':os.uname().machine if hasattr(os,'uname') else os.environ.get('PROCESSOR_ARCHITECTURE'),'sanitizers':args.sanitize,'failing_controls':['asan_heap_oob','ubsan_signed_overflow'] if args.sanitize else [],'cases':records},indent=2)+'\n')
    return 0

if __name__=='__main__': raise SystemExit(main())
