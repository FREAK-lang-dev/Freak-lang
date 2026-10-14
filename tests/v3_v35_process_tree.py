#!/usr/bin/env python3
"""Native nested FREAK command groups obey ancestor deadlines/cancellation.

The supplied compiler must be a recorded fresh native stage2; no Python compiler
or convenience binary substitutes. Both generated backends call actual native
process APIs. Separate root jobs and siblings must survive targeted cleanup.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time

FREAK = r'''
task child(mode: word, depth: int) -> int {
    pilot executable = process::env("FREAK_TREE_SELF")
    if depth < 0 { executable = process::env("FREAK_TREE_LEAF") }
    pilot job = process::command_new(executable)
    process::command_env(job, "FREAK_TREE_MODE", mode)
    process::command_env(job, "FREAK_TREE_DEPTH", word_from_int(depth))
    process::command_arg(job, mode)
    process::command_arg(job, process::env("FREAK_TREE_EVENT"))
    give back job
}
task main() {
    pilot mode = process::env("FREAK_TREE_MODE")
    if mode == "owner-death" {
        pilot target = child("slow", 1)
        process::command_spawn_inherit(target, 0)
        pilot pause = child("pause", 0 - 1)
        process::command_run_inherit(pause, 1000)
        process::command_release(pause)
        pilot killer = child("kill-parent", 0 - 1)
        process::command_run_inherit(killer, 0)
        process::exit(94)
    }
    if mode == "siblings" {
        pilot target = child("slow", 1)
        pilot survivor = child("survivor", 0 - 1)
        process::command_spawn_inherit(target, 0)
        process::command_spawn_inherit(survivor, 0)
        pilot pause = child("pause", 0 - 1)
        process::command_run_inherit(pause, 1000)
        process::command_release(pause)
        process::command_terminate(target)
        if process::command_status(target) != 7 { process::exit(91) }
        process::command_release(target)
        pilot state = process::command_wait(survivor)
        pilot code = process::command_exit_code(survivor)
        process::command_release(survivor)
        if state != 2 or code != 0 { process::exit(92) }
        say "SIBLING_OK"
        give back
    }
    pilot depth = word_to_int(process::env("FREAK_TREE_DEPTH"))
    pilot job = child(mode, depth - 1)
    pilot state = process::command_run_inherit(job, 0)
    pilot code = process::command_exit_code(job)
    process::command_release(job)
    if state != 2 { process::exit(93) }
    process::exit(code)
}
'''
LEAF = r'''#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <windows.h>
#include <process.h>
static long own_pid(void){return _getpid();}
static void delay(int ms){Sleep((DWORD)ms);}
#else
#include <unistd.h>
#include <signal.h>
#include <time.h>
static long own_pid(void){return (long)getpid();}
static void delay(int ms){struct timespec t={ms/1000,(ms%1000)*1000000L};while(nanosleep(&t,&t)!=0){}}
#endif
static void event(const char *path,const char *kind,const char *mode){FILE *f=fopen(path,"a");if(!f)exit(94);fprintf(f,"%s %s %ld\n",kind,mode,own_pid());fclose(f);}
int main(int argc,char **argv){if(argc!=3)return 95;event(argv[2],"start",argv[1]);printf("PID=%ld\n",own_pid());fflush(stdout);
#ifndef _WIN32
if(!strcmp(argv[1],"kill-parent")){kill(getppid(),SIGKILL);delay(20000);return 96;}
#endif
if(!strcmp(argv[1],"slow"))delay(20000);else if(!strcmp(argv[1],"pause"))delay(250);else delay(1200);event(argv[2],"done",argv[1]);return 0;}
'''
PARENT = r'''
#include "freak_runtime.c"
#ifdef _WIN32
static void delay(int ms){Sleep((DWORD)ms);}
#else
#include <time.h>
static void delay(int ms){struct timespec t={ms/1000,(ms%1000)*1000000L};while(nanosleep(&t,&t)!=0&&errno==EINTR){}}
#endif
#ifdef USE_LLVM_ADAPTER
#define J(name) freak_llvm_process_command_##name
#define W(s) ((int64_t)(intptr_t)(s))
#else
#define J(name) freak_process_command_##name
#define W(s) freak_word_lit(s)
#endif
#define REQUIRE(c) do{if(!(c)){fprintf(stderr,"FAIL line %d\n",__LINE__);exit(2);}}while(0)
static int open_fds(void){int count=0;
#ifndef _WIN32
for(int fd=0;fd<512;fd++)if(fcntl(fd,F_GETFD)>=0)count++;
#endif
return count;}
int main(int argc,char **argv){REQUIRE(argc==8);
#ifndef _WIN32
if(!strcmp(argv[6],"closed-stdio")){close(0);close(1);close(2);}
#endif
int before=open_fds();
int64_t unrelated=J(new)(W(argv[2]));J(arg)(unrelated,W("survivor"));J(arg)(unrelated,W(argv[7]));J(spawn)(unrelated,5000,4096,4096);
int64_t job=J(new)(W(argv[1]));J(env)(job,W("FREAK_TREE_SELF"),W(argv[1]));J(env)(job,W("FREAK_TREE_LEAF"),W(argv[2]));J(env)(job,W("FREAK_TREE_MODE"),W(argv[3]));J(env)(job,W("FREAK_TREE_EVENT"),W(argv[4]));J(env)(job,W("FREAK_TREE_DEPTH"),W(argv[5]));
uint64_t start=freak_command_now_ms();int timeout=(!strcmp(argv[6],"timeout")||!strcmp(argv[6],"closed-stdio"))?700:5000;
REQUIRE(J(spawn)(job,timeout,65536,65536)==1);
if(!strcmp(argv[6],"cancel")){delay(350);J(terminate)(job);REQUIRE(J(status)(job)==7);}
else if(!strcmp(argv[6],"race")){delay(3);J(terminate)(job);REQUIRE(J(status)(job)==7);}
else{int state;do{state=J(poll)(job);if(state==1)delay(1);}while(state==1);REQUIRE(state==((!strcmp(argv[6],"timeout")||!strcmp(argv[6],"closed-stdio"))?5:!strcmp(argv[6],"owner-death")?4:2));if(state==4)REQUIRE(J(signal)(job)==9);if(state==2)REQUIRE(J(exit_code)(job)==0);}
REQUIRE(freak_command_now_ms()-start<3500);J(release)(job);
REQUIRE(J(wait)(unrelated)==2&&J(exit_code)(unrelated)==0);J(release)(unrelated);
REQUIRE(freak_process_command_live()==0&&freak_process_command_children()==0&&freak_process_command_retained_bytes()==0);
REQUIRE(open_fds()==before);return 0;}
'''

def run(command, **kwargs):
    return subprocess.run(command,capture_output=True,timeout=45,**kwargs)

def alive(pid):
    if os.name=='nt':
        import ctypes
        k=ctypes.WinDLL('kernel32',use_last_error=True);k.OpenProcess.restype=ctypes.c_void_p;h=k.OpenProcess(0x1000,False,pid)
        if not h:return False
        status=ctypes.c_ulong()
        try:return bool(k.GetExitCodeProcess(ctypes.c_void_p(h),ctypes.byref(status))) and status.value==259
        finally:k.CloseHandle(ctypes.c_void_p(h))
    try:os.kill(pid,0)
    except ProcessLookupError:return False
    stat=Path(f'/proc/{pid}/stat')
    return not(stat.is_file() and stat.read_text().rsplit(') ',1)[1].startswith('Z '))

def events(path):
    return [line.split() for line in path.read_text().splitlines()] if path.exists() else []

def cleanup_recorded(paths):
    for path in paths:
        for row in events(path):
            pid=int(row[2])
            if alive(pid):
                if os.name=='nt':
                    import ctypes
                    k=ctypes.WinDLL('kernel32',use_last_error=True);k.OpenProcess.restype=ctypes.c_void_p;h=k.OpenProcess(1,False,pid)
                    if h:k.TerminateProcess(ctypes.c_void_p(h),137);k.CloseHandle(ctypes.c_void_p(h))
                else:
                    if hasattr(os,'pidfd_open') and hasattr(signal,'pidfd_send_signal'):
                        try:descriptor=os.pidfd_open(pid)
                        except ProcessLookupError:continue
                        try:
                            # Check this fixture's argv after acquiring its stable
                            # kernel identity; never kill a recycled numeric PID.
                            command=Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
                            if os.fsencode(path) in command:signal.pidfd_send_signal(descriptor,signal.SIGKILL)
                        except (ProcessLookupError,FileNotFoundError):pass
                        finally:os.close(descriptor)
                    else:os.kill(pid,signal.SIGKILL)

def main():
    p=argparse.ArgumentParser();p.add_argument('--compiler',type=Path,required=True);p.add_argument('--clang',default=os.environ.get('FREAK_CLANG','clang'));p.add_argument('--optimization',type=int,choices=(0,2,3),action='append');p.add_argument('--report',type=Path);p.add_argument('--runtime-root',type=Path);p.add_argument('--sanitize',action='store_true');args=p.parse_args()
    clang=shutil.which(args.clang);assert clang,args.clang
    repo=Path(__file__).resolve().parents[1];runtime=args.runtime_root or repo/'freakc/runtime';compiler=args.compiler.resolve(strict=True)
    report={'compiler_sha256':hashlib.sha256(compiler.read_bytes()).hexdigest(),'process_sha256':hashlib.sha256((runtime/'freak_v35_process.inc').read_bytes()).hexdigest(),'sanitize':args.sanitize,'matrices':[]}
    env=os.environ.copy();env['ASAN_OPTIONS']='detect_leaks=1:halt_on_error=1';env['UBSAN_OPTIONS']='halt_on_error=1'
    with tempfile.TemporaryDirectory(prefix='freak-process-tree-') as temporary:
        root=Path(temporary);suffix='.exe' if os.name=='nt' else '';leafsource=root/'leaf.c';leafsource.write_text(LEAF);leaf=root/f'leaf{suffix}'
        flags=['-lws2_32','-lshell32'] if os.name=='nt' else ['-lm']
        c=run([clang,str(leafsource),'-O2','-o',str(leaf)]);assert c.returncode==0,c.stderr.decode()
        if args.sanitize:
            flags += ['-fsanitize=address,undefined','-fno-omit-frame-pointer','-g']
            control=root/'control.c';control.write_text('#include <stdlib.h>\nint main(int n,char **v){volatile char *p=malloc(1);p[n+4]=3;free((void*)p);return 0;}\n')
            executable=root/'control';c=run([clang,str(control),'-O0',*flags,'-o',str(executable)]);assert c.returncode==0,c.stderr.decode()
            c=run([str(executable)],env=env);assert c.returncode!=0 and b'AddressSanitizer' in c.stderr,c.stderr
            report['sanitizer_failing_control']=True
        parentsource=root/'parent.c';parentsource.write_text(PARENT)
        for opt in args.optimization or (0,2,3):
            for backend in ('c','llvm'):
                fk=root/f'nested-{backend}.fk';fk.write_text(FREAK);c=run([str(compiler),str(fk),f'--{backend}']);assert c.returncode==0,(c.stdout,c.stderr)
                generated=Path(str(fk)+('.c' if backend=='c' else '.ll'));nested=root/f'nested-{backend}-O{opt}{suffix}'
                cmd=[clang,str(generated),str(runtime/'freak_runtime.c'),f'-I{runtime}',f'-O{opt}','-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1','-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1',*flags,'-o',str(nested)]
                if backend=='llvm':cmd.append(str(runtime/'freak_llvm_runtime.c'))
                c=run(cmd);assert c.returncode==0,c.stderr.decode()
                for adapter in ('c','llvm'):
                    parent=root/f'parent-{adapter}-O{opt}{suffix}'
                    cmd=[clang,str(parentsource),str(runtime/'freak_llvm_runtime.c'),f'-I{runtime}',f'-O{opt}','-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1','-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1',*flags,'-o',str(parent)]
                    if adapter=='llvm':cmd.insert(1,'-DUSE_LLVM_ADAPTER=1')
                    c=run(cmd);assert c.returncode==0,c.stderr.decode()
                    cases=[('slow',0,'timeout'),('slow',2,'timeout'),('slow',2,'cancel'),('siblings',0,'success')]
                    if os.name!='nt':cases += [('owner-death',0,'owner-death'),('slow',2,'closed-stdio')]
                    cases += [('slow',3,'race')]*3
                    for number,(mode,depth,operation) in enumerate(cases):
                        event=root/f'events-{backend}-{adapter}-{opt}-{number}';unrelated=root/f'unrelated-{backend}-{adapter}-{opt}-{number}'
                        try:
                            c=run([str(parent),str(nested),str(leaf),mode,str(event),str(depth),operation,str(unrelated)],env=env)
                            assert c.returncode==0 and not c.stdout and not c.stderr,(backend,adapter,opt,operation,c.returncode,c.stdout,c.stderr)
                            rows=events(event)
                            if operation!='race':assert any(row[:2]==['start','survivor' if mode=='siblings' else 'slow'] for row in rows),rows
                            for row in rows:
                                deadline=time.monotonic()+1
                                while alive(int(row[2])) and time.monotonic()<deadline:time.sleep(.01)
                                assert not alive(int(row[2])),('nested helper leaked',row,operation)
                            other=events(unrelated);assert [row[0] for row in other]==['start','done'],('unrelated job was killed',other)
                            if mode=='siblings':assert any(row[:2]==['done','survivor'] for row in rows),('sibling was killed',rows)
                        finally:cleanup_recorded([event,unrelated])
                    report['matrices'].append({'backend':backend,'adapter':adapter,'optimization':opt,'nested_timeout_cancel':True,'sibling_and_unrelated_survive':True,'registration_races':3,'abrupt_owner_death':os.name!='nt','closed_standard_descriptors':os.name!='nt','fd_child_capture_conservation':True})
                    print(f'PASS nested process tree {backend}/{adapter} O{opt}: ancestor timeout/cancel, siblings/unrelated survive, races, fd/child/capture conservation',flush=True)
    assert hashlib.sha256((runtime/'freak_v35_process.inc').read_bytes()).hexdigest()==report['process_sha256'],'runtime source changed during verification'
    if args.report:args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
