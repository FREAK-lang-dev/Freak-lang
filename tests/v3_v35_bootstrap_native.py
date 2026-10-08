#!/usr/bin/env python3
"""Verify a supplied installed native V3.5 bootstrap and its separate V4 preview.

The candidate is never rebuilt here. Python is the independent test driver;
compiled traps prove the successful installed route cannot invoke Python.
--source must contain the final frozen bootstrap.toml and byte inventory.
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

NATIVE_PROGRAM_STDOUT = b'native-v4\r\n' if os.name == 'nt' else b'native-v4\n'
# The required negative control is bound to the workflow's immutable UCRT SDK,
# not a claim about every Windows Clang configuration.
PINNED_WINDOWS_CLANG_SHA256 = 'a8b7a614eeadd9105f814be3701a7f312cda4cea51751b75b408c16100c94e85'
PINNED_WINDOWS_SDK_SHA256 = 'b9b68a4d276e16fa25802aaba458e4638f64b3884c290aaccdc2d87083b6ca35'

WRAPPER = r'''#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <windows.h>
#include <shellapi.h>
#include <process.h>
#include <stdint.h>
#include <wchar.h>
/* CRT spawn joins argv strings with spaces; quote each string for the
   receiving CRT, including empty arguments and trailing backslashes. */
static wchar_t *quote_spawn_argument(const wchar_t *argument) {
    size_t length=wcslen(argument);
    if(length>(SIZE_MAX/sizeof(wchar_t)-3)/2)return NULL;
    wchar_t *quoted=calloc(length*2+3,sizeof(wchar_t));
    if(!quoted)return NULL;
    size_t used=0; quoted[used++]=L'"';
    const wchar_t *cursor=argument;
    while(*cursor) {
        size_t slashes=0;
        while(*cursor==L'\\'){slashes++;cursor++;}
        size_t escaped=(*cursor==L'"'||!*cursor)?slashes*2:slashes;
        for(size_t i=0;i<escaped;i++)quoted[used++]=L'\\';
        if(*cursor==L'"')quoted[used++]=L'\\';
        if(*cursor)quoted[used++]=*cursor++;
    }
    quoted[used++]=L'"';
    return quoted;
}
static int forward_spawn(const wchar_t *compiler,int count,wchar_t **arguments) {
#ifdef FREAK_BOOTSTRAP_TEST_UNQUOTED_FORWARD
    /* Deliberately preserve the old broken second hop for its native oracle. */
    return (int)_wspawnv(_P_WAIT,compiler,(const wchar_t *const *)arguments);
#else
    if(count<1||(size_t)count>SIZE_MAX/sizeof(wchar_t *)-1)return 96;
    wchar_t **quoted=calloc((size_t)count+1,sizeof(wchar_t *));
    if(!quoted)return 96;
    size_t command_length=0;
    int result=96;
    for(int i=0;i<count;i++) {
        if(!arguments[i]||!(quoted[i]=quote_spawn_argument(arguments[i])))goto done;
        size_t length=wcslen(quoted[i]);
        size_t separator=i?1:0;
        if(length>32766-separator||command_length>32766-separator-length)goto done;
        command_length+=length+separator;
    }
    result=(int)_wspawnv(_P_WAIT,compiler,(const wchar_t *const *)quoted);
done:
    for(int i=0;i<count;i++)free(quoted[i]);
    free(quoted);
    return result;
#endif
}
/* Observe the actual parsed first-hop argv and staged header before Clang runs.
   The incoming tool spelling is separate from the backslash kernel spelling.
   Collection never changes compiler arguments or its return status. */
static int observe_utf8(FILE *file,const wchar_t *value) {
    int size=WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,value,-1,NULL,0,NULL,NULL);
    if(size<1)return 0;
    unsigned char *bytes=malloc((size_t)size);
    if(!bytes)return 0;
    int valid=WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,value,-1,(char *)bytes,size,NULL,NULL)==size;
    if(valid)for(int i=0;i<size-1;i++)fprintf(file,"%02x",bytes[i]);
    free(bytes);return valid;
}
/* Give ordinary/relative diagnostic inputs the same explicit long-path kernel
   admission. This changes only the witness path, never the forwarded argv. */
static wchar_t *observe_absolute_kernel(wchar_t *path,FILE *file) {
    if(wcsncmp(path,L"\\\\?\\",4)==0)return path;
    DWORD capacity=GetFullPathNameW(path,0,NULL,NULL);
    DWORD error=capacity?0:GetLastError();
    if(!capacity||capacity>32768) {
        fprintf(file,"full_path 0 %lu %lu\n",(unsigned long)capacity,(unsigned long)error);
        fputs("collection_error absolute-kernel-path-size\n",file);free(path);return NULL;
    }
    wchar_t *absolute=calloc(capacity,sizeof(wchar_t));
    if(!absolute){fputs("collection_error absolute-kernel-path-allocation\n",file);free(path);return NULL;}
    DWORD copied=GetFullPathNameW(path,capacity,absolute,NULL);
    error=copied?0:GetLastError();free(path);
    fprintf(file,"full_path %d %lu %lu\n",copied&&copied<capacity,(unsigned long)copied,(unsigned long)error);
    if(!copied||copied>=capacity){fputs("collection_error absolute-kernel-path-resolution\n",file);free(absolute);return NULL;}
    /* Resolution may already supply an extended DOS/UNC path. Keep that
       qualified spelling instead of treating its leading slashes as UNC. */
    if(wcsncmp(absolute,L"\\\\?\\",4)==0)return absolute;
    const wchar_t *tail=absolute;
    const wchar_t *prefix=L"\\\\?\\";
    if(absolute[0]==L'\\'&&absolute[1]==L'\\'){prefix=L"\\\\?\\UNC\\";tail+=2;}
    size_t prefix_length=wcslen(prefix),length=wcslen(tail);
    if(length>32766-prefix_length){fputs("collection_error absolute-kernel-path-limit\n",file);free(absolute);return NULL;}
    wchar_t *extended=calloc(prefix_length+length+1,sizeof(wchar_t));
    if(!extended){fputs("collection_error extended-kernel-path-allocation\n",file);free(absolute);return NULL;}
    memcpy(extended,prefix,prefix_length*sizeof(wchar_t));
    memcpy(extended+prefix_length,tail,(length+1)*sizeof(wchar_t));
    free(absolute);return extended;
}
static void observe_clang_arguments(int count,wchar_t **arguments,const wchar_t *compiler) {
    const wchar_t *include=NULL;
    for(int i=1;i+1<count;i++)if(wcscmp(arguments[i],L"-I")==0){include=arguments[i+1];break;}
    if(!include)return;
    DWORD capacity=GetEnvironmentVariableW(L"FREAK_BOOTSTRAP_NATIVE_WITNESS",NULL,0);
    if(!capacity||capacity>32768)return;
    wchar_t *channel=calloc(capacity,sizeof(wchar_t));
    if(!channel)return;
    DWORD copied=GetEnvironmentVariableW(L"FREAK_BOOTSTRAP_NATIVE_WITNESS",channel,capacity);
    FILE *file=copied&&copied<capacity?_wfopen(channel,L"ab"):NULL;
    free(channel);if(!file)return;
    fprintf(file,"FREAK-BOOTSTRAP-CLANG-1 %d\n",count);
    int encoded=1;
    for(int i=0;i<count;i++){fputs("arg ",file);encoded&=observe_utf8(file,arguments[i]);fputc('\n',file);}
    fputs("compiler ",file);encoded&=observe_utf8(file,compiler);fputc('\n',file);
    fputs("include ",file);encoded&=observe_utf8(file,include);fputc('\n',file);
    size_t length=wcslen(include);
    const wchar_t suffix[]=L"\\freak_runtime.h";
    wchar_t *kernel=length<=32700?calloc(length+sizeof(suffix)/sizeof(wchar_t),sizeof(wchar_t)):NULL;
    if(!kernel){fputs("collection_error path-allocation\nend\n",file);fclose(file);return;}
    for(size_t i=0;i<length;i++)kernel[i]=include[i]==L'/'?L'\\':include[i];
    memcpy(kernel+length,suffix,sizeof(suffix));
    kernel=observe_absolute_kernel(kernel,file);
    if(!kernel){fputs("end\n",file);fclose(file);return;}
    fputs("kernel_header ",file);encoded&=observe_utf8(file,kernel);fputc('\n',file);
    HANDLE header=CreateFileW(kernel,GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,
                             NULL,OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,NULL);
    DWORD error=header==INVALID_HANDLE_VALUE?GetLastError():0;
    fprintf(file,"open %d %lu\n",header!=INVALID_HANDLE_VALUE,(unsigned long)error);
    free(kernel);
    if(header!=INVALID_HANDLE_VALUE) {
        FILE_ATTRIBUTE_TAG_INFO attributes={0};
        BOOL attributes_ok=GetFileInformationByHandleEx(header,FileAttributeTagInfo,&attributes,sizeof(attributes));
        error=attributes_ok?0:GetLastError();
        fprintf(file,"attributes %d %lu %lu %lu\n",attributes_ok!=0,(unsigned long)attributes.FileAttributes,
                (unsigned long)attributes.ReparseTag,(unsigned long)error);
        SetLastError(0);DWORD type=GetFileType(header);
        error=type==FILE_TYPE_UNKNOWN?GetLastError():0;
        fprintf(file,"type %lu %lu\n",(unsigned long)type,(unsigned long)error);
        LARGE_INTEGER size={0};
        BOOL size_ok=GetFileSizeEx(header,&size);
        error=size_ok?0:GetLastError();
        fprintf(file,"size %d %lld %lu\n",size_ok!=0,(long long)size.QuadPart,(unsigned long)error);
        if(attributes_ok&&!(attributes.FileAttributes&(FILE_ATTRIBUTE_DIRECTORY|FILE_ATTRIBUTE_REPARSE_POINT))&&
           type==FILE_TYPE_DISK&&size_ok&&size.QuadPart>=0&&size.QuadPart<=1048576) {
            size_t expected=(size_t)size.QuadPart,used=0;
            unsigned char *bytes=malloc(expected+1);
            if(!bytes)fputs("collection_error header-buffer-allocation\n",file);
            BOOL valid=bytes!=NULL;DWORD read_error=0;
            while(valid&&used<expected) {
                DWORD amount=0;
                valid=ReadFile(header,bytes+used,(DWORD)(expected-used),&amount,NULL);
                if(!valid){read_error=GetLastError();break;}
                if(!amount){valid=FALSE;break;}
                used+=amount;
            }
            DWORD extra=0;unsigned char tail;
            if(valid){valid=ReadFile(header,&tail,1,&extra,NULL);if(!valid)read_error=GetLastError();}
            fprintf(file,"read %d %zu %lu %lu\n",valid!=0,used,(unsigned long)read_error,(unsigned long)extra);
            fputs("bytes ",file);
            if(bytes)for(size_t i=0;i<used;i++)fprintf(file,"%02x",bytes[i]);
            fputc('\n',file);free(bytes);
        } else fputs("collection_error header-not-bounded-ordinary-file\n",file);
        BOOL closed=CloseHandle(header);error=closed?0:GetLastError();
        fprintf(file,"close %d %lu\n",closed!=0,(unsigned long)error);
    }
    if(!encoded)fputs("collection_error utf8-conversion\n",file);
    fputs("end\n",file);fclose(file);
}
#else
#include <unistd.h>
#endif
int main(int argc, char **argv) {
#ifdef _WIN32
    int count; wchar_t **wide = CommandLineToArgvW(GetCommandLineW(), &count);
    if (!wide) return 90;
    argc=count; argv=calloc((size_t)argc+1,sizeof(char*));
    for(int i=0;i<argc;i++) { int n=WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,wide[i],-1,NULL,0,NULL,NULL);
        argv[i]=malloc((size_t)n); if(!argv[i] || !WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,wide[i],-1,argv[i],n,NULL,NULL))return 91; }
#endif
    const char *log=getenv("FREAK_BOOTSTRAP_NATIVE_LOG");
    if(!log)return 92;
    FILE *file=fopen(log,"ab"); if(!file)return 93;
    fprintf(file,"%s\n",argv[0]); fclose(file);
    if(strstr(argv[0],"python")) return 97;
    const char *mode=getenv("FREAK_BOOTSTRAP_NATIVE_MODE");
    if(argc>2 && mode && strcmp(mode,"fail-link")==0) { fputc(0,stderr);fputc(255,stderr);return 43; }
    if(argc>2 && mode && strcmp(mode,"slow-link")==0) {
        const char *ready=getenv("FREAK_BOOTSTRAP_NATIVE_READY");
        if(ready){file=fopen(ready,"wb");if(file){fputs("ready",file);fclose(file);}}
#ifdef _WIN32
        Sleep(60000);
#else
        sleep(60);
#endif
    }
#ifdef _WIN32
    DWORD size=GetEnvironmentVariableW(L"FREAK_BOOTSTRAP_NATIVE_CLANG",NULL,0);
    wchar_t *compiler=calloc(size,sizeof(wchar_t));
    if(!size||!compiler||!GetEnvironmentVariableW(L"FREAK_BOOTSTRAP_NATIVE_CLANG",compiler,size))return 94;
    observe_clang_arguments(argc,wide,compiler);
    wide[0]=compiler;
    int result=forward_spawn(compiler,argc,wide);
    for(int i=0;i<argc;i++)free(argv[i]);
    free(argv);free(compiler);LocalFree(wide);
    return result;
#else
    const char *compiler=getenv("FREAK_BOOTSTRAP_NATIVE_CLANG");if(!compiler)return 94;
    argv[0]=(char*)compiler;execv(compiler,argv);return 95;
#endif
}
'''

FORWARD_RECEIVER = r'''#include <stdio.h>
#include <stdlib.h>
#include <corecrt_startup.h>
#include <windows.h>
int main(void) {
    if(_configure_wide_argv(_crt_argv_unexpanded_arguments)!=0)return 90;
    int count=*__p___argc(); wchar_t **arguments=*__p___wargv();
    if(count<1||!arguments)return 91;
    puts("FREAK-BOOTSTRAP-FORWARD-ARGV-1");printf("%d\n",count);
    for(int i=0;i<count;i++) {
        if(!arguments[i])return 92;
        int size=WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,arguments[i],-1,NULL,0,NULL,NULL);
        if(size<1)return 93;
        unsigned char *bytes=malloc((size_t)size);
        if(!bytes)return 94;
        if(WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,arguments[i],-1,(char *)bytes,size,NULL,NULL)!=size){free(bytes);return 93;}
        printf("%d:",size-1);
        for(int j=0;j<size-1;j++)printf("%02x",bytes[j]);
        putchar('\n');free(bytes);
    }
    if(fflush(stdout)!=0)return 95;
    return 23;
}
'''

FORWARD_ARGUMENTS = ('', 'a b', 'tab\tvalue', 'é日本🙂', '"quoted"', 'tail\\',
                     'two\\\\', 'slash\\"quote', "' $ & %PATH% ; |", '*?literal')


def forward_arguments(stdout: bytes) -> list[bytes]:
    lines=stdout.splitlines()
    assert len(lines)>=2 and lines[0]==b'FREAK-BOOTSTRAP-FORWARD-ARGV-1', stdout
    count=int(lines[1])
    assert count>=0 and len(lines)==count+2, stdout
    arguments=[]
    for line in lines[2:]:
        length, encoded=line.split(b':',1)
        assert len(encoded)==int(length)*2, line
        argument=bytes.fromhex(encoded.decode('ascii'))
        assert len(argument)==int(length), line
        arguments.append(argument)
    return arguments


def verify_windows_forwarder(clang: Path, wrapper: Path, wrapper_source: Path,
                             root: Path, env: dict[str,str], evidence: Path | None) -> dict:
    """Observe the real wrapper→UCRT child hop, including the old defect."""
    receiver_source=root/'forward-receiver.c'
    receiver_source.write_text(FORWARD_RECEIVER,encoding='utf-8')
    receiver=root/"receiver é 日本 ' $ &.exe"
    broken=root/'old-unquoted-forwarder.exe'
    report={'status':'running','scope':'native test-wrapper second-hop argv only',
            'expected_arguments_hex':[value.encode('utf-8').hex() for value in (str(receiver),*FORWARD_ARGUMENTS)],
            'argv0_included':True,
            'fixed_matched':False,'old_control_exercised':False,
            'sources_sha256':{'wrapper':digest(wrapper_source),'receiver':digest(receiver_source)},
            'binaries_sha256':{'clang':digest(clang),'fixed_wrapper':digest(wrapper)},
            'commands':[]}

    def save() -> None:
        if evidence:
            evidence.parent.mkdir(parents=True,exist_ok=True)
            evidence.write_text(json.dumps({'status':'fail' if report['status']=='fail' else 'running','phase':'test forwarder argv',
                                            'forwarder':report},indent=2)+'\n')

    def run(command: list[str], selected: dict[str,str]) -> subprocess.CompletedProcess[bytes]:
        result=subprocess.run(command,env=selected,capture_output=True,timeout=60)
        report['commands'].append({'argv':command,'returncode':result.returncode,
                                    'stdout_hex':result.stdout.hex(),'stderr_hex':result.stderr.hex()})
        save()
        return result

    try:
        for command in ([str(clang),'-O0',str(receiver_source),'-o',str(receiver)],
                        [str(clang),'-O0','-DFREAK_BOOTSTRAP_TEST_UNQUOTED_FORWARD=1',
                         str(wrapper_source),'-o',str(broken),'-lshell32']):
            result=run(command,env)
            assert result.returncode==0, result.stderr
        report['binaries_sha256'].update({'old_control_wrapper':digest(broken),'receiver':digest(receiver)})
        selected={**env,'FREAK_BOOTSTRAP_NATIVE_CLANG':str(receiver)}
        selected.pop('FREAK_BOOTSTRAP_NATIVE_MODE',None)
        expected=[value.encode('utf-8') for value in (str(receiver),*FORWARD_ARGUMENTS)]
        result=run([str(wrapper),*FORWARD_ARGUMENTS],selected)
        assert result.returncode==23 and result.stderr==b'', result
        actual=forward_arguments(result.stdout)
        report['fixed_arguments_hex']=[value.hex() for value in actual]
        assert actual==expected, (actual,expected)
        report['fixed_matched']=True
        result=run([str(broken),*FORWARD_ARGUMENTS],selected)
        assert result.returncode==23 and result.stderr==b'', result
        actual=forward_arguments(result.stdout)
        report['old_arguments_hex']=[value.hex() for value in actual]
        assert actual!=expected, 'old unquoted spawn unexpectedly preserved every argument'
        report['old_control_exercised']=True
        report['status']='pass'
    except BaseException:
        report['status']='fail'
        raise
    finally:
        save()
    return report

PROGRAM = 'task main() -> int {\n    say "native-v4"\n    give back 42\n}\n'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_git_build_capture(evidence: Path | None, process: subprocess.CompletedProcess[bytes] | None,
                           images: dict[str, Path], before_images: dict | None = None) -> dict | None:
    if evidence is None:
        return
    identities = {}
    for name, path in images.items():
        try:
            before = path.stat()
            sha256 = digest(path)
            after = path.stat()
            identities[name] = {
                'path': str(path), 'sha256': sha256,
                'mode': after.st_mode, 'size': after.st_size,
                'device': after.st_dev, 'inode': after.st_ino, 'mtime_ns': after.st_mtime_ns,
                'stat_unchanged_while_hashing':
                    (before.st_dev, before.st_ino, before.st_mode, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                    (after.st_dev, after.st_ino, after.st_mode, after.st_size, after.st_mtime_ns, after.st_ctime_ns),
            }
        except OSError as error:
            identities[name] = {'path': str(path), 'sha256': None,
                                'observation_error': {'type': type(error).__name__,
                                                      'errno': error.errno, 'message': str(error)}}
    report = {
        'phase': 'second local Git checkout bootstrap',
        'state': 'pending' if process is None else 'completed',
        'returncode': None if process is None else process.returncode,
        'stdout_hex': None if process is None else process.stdout.hex(),
        'stderr_hex': None if process is None else process.stderr.hex(),
        'images_before': identities if process is None else before_images,
        'images_after': None if process is None else identities,
    }
    destination = evidence.with_suffix('.git-build.json')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return identities


def clang_witnesses(path: Path, expected_header: bytes) -> list[dict]:
    """Decode bounded ASCII frames from real wide-argv/kernel observations."""
    data=path.read_bytes()
    assert len(data)<=67108864, 'Clang witness collection exceeds 64 MiB'
    lines=data.splitlines()
    records=[]
    index=0
    while index<len(lines):
        magic,count=lines[index].split(b' ',1)
        assert magic==b'FREAK-BOOTSTRAP-CLANG-1'
        count=int(count)
        assert 1<=count<=256 and len(records)<128
        index+=1
        record={'arguments_hex':[],'collection_errors':[]}
        for _ in range(count):
            key,value=lines[index].split(b' ',1)
            assert key==b'arg'
            bytes.fromhex(value.decode('ascii')).decode('utf-8')
            record['arguments_hex'].append(value.decode('ascii'))
            index+=1
        while lines[index]!=b'end':
            key,value=lines[index].split(b' ',1)
            name=key.decode('ascii')
            if name=='collection_error':
                record['collection_errors'].append(value.decode('ascii'))
            elif name in ('compiler','include','kernel_header','bytes'):
                assert name+'_hex' not in record
                raw=bytes.fromhex(value.decode('ascii'))
                if name!='bytes':
                    raw.decode('utf-8')
                record[name+'_hex']=value.decode('ascii')
            else:
                assert name not in record and name in ('full_path','open','attributes','type','size','read','close')
                record[name]=[int(part) for part in value.split()]
            index+=1
        index+=1
        raw=bytes.fromhex(record.get('bytes_hex',''))
        record['header_sha256']=hashlib.sha256(raw).hexdigest()
        record['kernel_header_verified']=(
            not record['collection_errors'] and record.get('open')==[1,0] and
            len(record.get('attributes',[]))==4 and record['attributes'][0]==1 and
            record['attributes'][1]&(0x10|0x400)==0 and record['attributes'][2:]==[0,0] and
            record.get('type')==[1,0] and record.get('size')==[1,len(expected_header),0] and
            record.get('read')==[1,len(expected_header),0,0] and record.get('close')==[1,0] and
            raw==expected_header)
        arguments=[bytes.fromhex(value).decode('utf-8') for value in record['arguments_hex']]
        include=bytes.fromhex(record['include_hex']).decode('utf-8')
        assert arguments[arguments.index('-I')+1]==include, record
        record['include_argument']=include
        record['kernel_header_path']=bytes.fromhex(record['kernel_header_hex']).decode('utf-8')
        records.append(record)
    return records


def windows_extended(path: Path) -> str:
    text=str(path)
    assert len(text)>=3 and text[1:3]==':\\', text
    return '\\\\?\\'+text


def save_clang_observations(evidence: Path | None, forwarder: dict | None,
                            paths: dict | None, witnesses: list[dict], *, failed: bool = False,
                            native: dict | None = None) -> None:
    if evidence:
        evidence.parent.mkdir(parents=True,exist_ok=True)
        evidence.write_text(json.dumps({'status':'fail' if failed else 'running',
            'phase':'native Clang path/header observations','public_bootstrap_verified':False,
            'forwarder':forwarder,'clang_paths':paths,'staged_clang_witnesses':witnesses,
            'native_bootstrap_observation':native},indent=2)+'\n')


def verify_windows_clang_paths(clang: Path, wrapper: Path, root: Path, env: dict[str,str],
                               evidence: Path | None, forwarder: dict | None) -> dict:
    """Compare only Clang path spellings over exactly the same native files."""
    header=b'#define FREAK_PATH_PROBE_RESULT 23\n'
    source=b'#include "freak_runtime.h"\nint main(void) { return FREAK_PATH_PROBE_RESULT; }\n'
    witness=root/'path-probe-witnesses.txt'
    report={'status':'running','scope':'native wrapper to pinned Clang path spelling',
            'negative_control_profile':'llvm-mingw-20260616-ucrt, Clang 22.1.8',
            'public_bootstrap_verified':False,'clang_sha256':digest(clang),
            'header_sha256':hashlib.sha256(header).hexdigest(),'source_sha256':hashlib.sha256(source).hexdigest(),
            'source_bytes_hex':source.hex(),'header_bytes_hex':header.hex(),'cases':[],
            'kernel_witnesses':[]}
    pinned=report['clang_sha256']==PINNED_WINDOWS_CLANG_SHA256
    report['pinned_negative_control_required']=pinned
    report['pinned_sdk_archive_sha256']=PINNED_WINDOWS_SDK_SHA256 if pinned else None
    selected={**env,'FREAK_BOOTSTRAP_NATIVE_WITNESS':str(witness)}
    # Keep the process CWD short while file arguments retain extended paths.
    # Relative controls still name the same fixture files.
    launch_cwd=str(root)
    cwd_length=len(launch_cwd.encode('utf-16-le'))//2
    assert root.is_absolute() and not launch_cwd.startswith(('\\\\?\\','//?/')) and cwd_length<260, launch_cwd
    report['launch_cwd']=launch_cwd
    report['launch_cwd_utf16_code_units']=cwd_length
    report['pending_launch']=None

    def save(failed: bool = False) -> None:
        if witness.exists():
            report['witness_frames_hex']=witness.read_bytes().hex()
        save_clang_observations(evidence,forwarder,report,[],failed=failed)

    try:
        report['tool_identity']=[]
        for option in ('--version','-dumpmachine'):
            command=[str(wrapper),option]
            result=subprocess.run(command,env=selected,capture_output=True,timeout=30)
            report['tool_identity'].append({'argv':command,'returncode':result.returncode,
                                           'stdout_hex':result.stdout.hex(),'stderr_hex':result.stderr.hex()})
            save()
            assert result.returncode==0, report['tool_identity'][-1]
        if pinned:
            assert b'clang version 22.1.8' in bytes.fromhex(report['tool_identity'][0]['stdout_hex'])
            assert b'x86_64-w64-windows-gnu' in bytes.fromhex(report['tool_identity'][1]['stdout_hex'])
        for profile in ('short','long'):
            fixture=root/"include é 日本 ' $ &"/profile
            if profile=='long':
                fixture=fixture/('a'*80)/('b'*80)/('c'*80)
            kernel=Path(windows_extended(fixture))
            (kernel/'src').mkdir(parents=True)
            (kernel/'include').mkdir()
            (kernel/'include/freak_runtime.h').write_bytes(header)
            (kernel/'src/probe.c').write_bytes(source)
            assert (kernel/'include/freak_runtime.h').read_bytes()==header
            assert (kernel/'src/probe.c').read_bytes()==source
            source_path=fixture/'src/probe.c'
            include_path=fixture/'include'
            length=len(str(fixture/'include/freak_runtime.h').encode('utf-16-le'))//2
            parent_length=len(str(fixture).encode('utf-16-le'))//2
            assert (length<260 if profile=='short' else parent_length>260), (length,parent_length)
            assert all(len(part.encode('utf-16-le'))//2<255 for part in fixture.parts[1:])
            extended_source=windows_extended(source_path)
            extended_include=windows_extended(include_path)
            cases=(
                ('ordinary',str(source_path),str(include_path),False,True),
                ('extended-backslash',extended_source,extended_include,False,False),
                ('extended-forward',extended_source.replace('\\','/'),extended_include.replace('\\','/'),True,True),
                ('backslash-source-forward-include',extended_source,extended_include.replace('\\','/'),True,True),
                ('forward-source-backslash-include',extended_source.replace('\\','/'),extended_include,True,False),
                ('relative-cwd',os.path.relpath(source_path,root),os.path.relpath(include_path,root),False,True))
            for label,rendered_source,rendered_include,forward_output,should_pass in cases:
                if label=='relative-cwd' or (profile=='long' and label=='ordinary'):
                    should_pass=None
                if not should_pass and not pinned:
                    should_pass=None
                output=fixture/('program-'+label+'.exe')
                if label=='relative-cwd':
                    rendered_output=os.path.relpath(output,root)
                elif label=='ordinary':
                    rendered_output=str(output)
                else:
                    rendered_output=windows_extended(output)
                    if forward_output:
                        rendered_output=rendered_output.replace('\\','/')
                command=[str(wrapper),'-O0',rendered_source,'-I',rendered_include,'-o',rendered_output]
                report['pending_launch']={'phase':'compile','profile':profile,'case':label,
                                          'argv':command,'cwd':launch_cwd,'child_status_unknown':True}
                save()
                result=subprocess.run(command,cwd=root,env=selected,capture_output=True,timeout=60)
                record={'profile':profile,'case':label,'path_characters':length,
                        'parent_utf16_code_units':parent_length,
                        'argv':command,'cwd':launch_cwd,'returncode':result.returncode,
                        'stdout_hex':result.stdout.hex(),'stderr_hex':result.stderr.hex(),
                        'expected_compile_success':should_pass,
                        'expectation_kind':('observational-baseline' if should_pass is None else
                                            'required-success' if should_pass else 'required-pinned-missing-header'),
                        'verified':False}
                report['cases'].append(record)
                report['pending_launch']=None
                save()
                if should_pass is True or (should_pass is None and result.returncode==0):
                    assert result.returncode==0, record
                    physical=Path(windows_extended(output))
                    record['output_sha256']=digest(physical)
                    report['pending_launch']={'phase':'execute','profile':profile,'case':label,
                                              'argv':[str(physical)],'executable':str(physical),
                                              'cwd':launch_cwd,'child_status_unknown':True}
                    save()
                    executed=subprocess.run([str(physical)],executable=str(physical),cwd=root,
                                            env=selected,capture_output=True,timeout=30)
                    record['executed']={'argv':[str(physical)],'executable':str(physical),
                                        'cwd':launch_cwd,'returncode':executed.returncode,
                                        'stdout_hex':executed.stdout.hex(),'stderr_hex':executed.stderr.hex()}
                    report['pending_launch']=None
                    save()
                    assert executed.returncode==23 and executed.stdout==executed.stderr==b'', record
                elif should_pass is False:
                    assert result.returncode==1 and b"'freak_runtime.h' file not found" in result.stderr, record
                    assert not Path(windows_extended(output)).exists(), record
                else:
                    record['baseline_only_observed']=True
                record['verified']=True
                save()
        report['kernel_witnesses']=clang_witnesses(witness,header)
        save()
        assert len(report['kernel_witnesses'])==len(report['cases'])==12
        assert all(record['kernel_header_verified'] for record in report['kernel_witnesses'])
        report['status']='pass'
    except BaseException:
        report['status']='fail'
        save(True)
        raise
    save()
    return report


def inventory(source: Path) -> list[tuple[str, str, str]]:
    lines = (source / 'bootstrap.lock').read_text(encoding='utf-8').splitlines()
    assert lines[0] == 'FREAK-V4-BOOTSTRAP-LOCK-1' and len(lines[1].split()[1]) == 40, 'source has no frozen bootstrap lock'
    records = [tuple(line.split(' ', 2)) for line in lines[2:] if line]
    assert len(records) == 28, records
    for role, expected, relative in records:
        assert role in ('source_order', 'source', 'entry', 'metadata') and digest(source / relative) == expected, relative
    return records


def copy_source(original: Path, destination: Path, records: list[tuple[str, str, str]]) -> None:
    for _, _, relative in records:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original / relative, target)
    shutil.copy2(original / 'bootstrap.lock', destination / 'bootstrap.lock')


def rewrite_lock(source: Path, relative: str) -> None:
    lock = source / 'bootstrap.lock'
    lines = lock.read_text(encoding='utf-8').splitlines()
    for index, line in enumerate(lines[2:], 2):
        role, _, path = line.split(' ', 2)
        if path == relative:
            lines[index] = f'{role} {digest(source / path)} {path}'
    lock.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def bootstrap(candidate: Path, source: Path, output: Path, env: dict[str, str], *, locked: bool = True,
              output_spelling: str | None = None) -> subprocess.CompletedProcess[bytes]:
    command = [str(candidate), 'bootstrap', '--v4', '--source=' + str(source), '--output=' + (output_spelling or str(output))]
    if locked:
        command.append('--locked')
    return subprocess.run(command, cwd=source.parent, env=env, capture_output=True, timeout=360)


def failed(process: subprocess.CompletedProcess[bytes], output: Path, parent: Path, *, stage_cleanup: bool = True) -> None:
    assert process.returncode != 0 and (process.stdout or process.stderr), process
    assert not output.exists(), (output, process.stdout, process.stderr)
    if stage_cleanup:
        assert not list(parent.glob('.freak-v4-bootstrap*')), list(parent.iterdir())


def windows_owner_require(condition: bool, phase: str, detail: object = None) -> None:
    if not condition:
        raise AssertionError(('Windows private-root ownership', phase, detail))


def windows_private_root(root: Path, evidence: Path | None, report: dict | None = None,
                         directory: Path | None = None) -> dict:
    """Change only the newly exclusive fixture root, through one held handle.

    Keep token defaults intact: an elevated token can name Administrators as
    TokenOwner while the checked publication policy requires TokenUser.
    """
    import ctypes as c

    kernel = c.WinDLL('kernel32.dll', use_last_error=True, winmode=0x800)
    security = c.WinDLL('advapi32.dll', use_last_error=True, winmode=0x800)
    pointer, dword, boolean = c.c_void_p, c.c_uint32, c.c_int
    word = c.c_uint16
    def api(library, name, result, *arguments):
        function = getattr(library, name)
        function.restype, function.argtypes = result, arguments
        return function
    close = api(kernel, 'CloseHandle', boolean, pointer)
    current_process = api(kernel, 'GetCurrentProcess', pointer)
    current_thread = api(kernel, 'GetCurrentThread', pointer)
    local_free = api(kernel, 'LocalFree', pointer, pointer)
    create_file = api(kernel, 'CreateFileW', pointer, c.c_wchar_p, dword, dword,
                      pointer, dword, dword, pointer)
    file_type = api(kernel, 'GetFileType', dword, pointer)
    file_info = api(kernel, 'GetFileInformationByHandleEx', boolean,
                    pointer, c.c_int, pointer, dword)
    open_process = api(security, 'OpenProcessToken', boolean, pointer, dword, c.POINTER(pointer))
    open_thread = api(security, 'OpenThreadToken', boolean, pointer, dword, boolean, c.POINTER(pointer))
    token_info = api(security, 'GetTokenInformation', boolean,
                     pointer, c.c_int, pointer, dword, c.POINTER(dword))
    valid_sid = api(security, 'IsValidSid', boolean, pointer)
    valid_acl = api(security, 'IsValidAcl', boolean, pointer)
    initialize_acl = api(security, 'InitializeAcl', boolean, pointer, dword, dword)
    add_ace = api(security, 'AddAccessAllowedAceEx', boolean, pointer, dword, dword, dword, pointer)
    get_ace = api(security, 'GetAce', boolean, pointer, dword, c.POINTER(pointer))
    get_security = api(security, 'GetSecurityInfo', dword, pointer, c.c_int, dword,
                       c.POINTER(pointer), pointer, c.POINTER(pointer), pointer, c.POINTER(pointer))
    set_security = api(security, 'SetSecurityInfo', dword, pointer, c.c_int, dword,
                       pointer, pointer, pointer, pointer)
    sd_length = api(security, 'GetSecurityDescriptorLength', dword, pointer)
    sd_control = api(security, 'GetSecurityDescriptorControl', boolean,
                     pointer, c.POINTER(word), c.POINTER(dword))
    class FileId(c.Structure):
        _fields_ = [('volume', c.c_uint64), ('identifier', c.c_ubyte * 16)]
    class Attributes(c.Structure):
        _fields_ = [('attributes', dword), ('reparse_tag', dword)]
    class Acl(c.Structure):
        _fields_ = [('revision', c.c_ubyte), ('reserved', c.c_ubyte),
                    ('size', word), ('count', word), ('reserved2', word)]
    class NativeString(c.Structure):
        _fields_ = [('length', word), ('capacity', word), ('buffer', pointer)]
    class NativeObject(c.Structure):
        _fields_ = [('length', dword), ('root', pointer), ('name', c.POINTER(NativeString)),
                    ('attributes', dword), ('security', pointer), ('quality', pointer)]
    class NativeStatus(c.Union):
        _fields_ = [('status', c.c_int32), ('pointer', pointer)]
    class NativeIo(c.Structure):
        _fields_ = [('value', NativeStatus), ('information', c.c_size_t)]
    native_create = api(c.WinDLL('ntdll.dll', use_last_error=True, winmode=0x800), 'NtCreateFile', c.c_int32,
                        c.POINTER(pointer), dword, c.POINTER(NativeObject), c.POINTER(NativeIo),
                        pointer, dword, dword, dword, dword, pointer, dword)
    initial = report is None
    if initial:
        report = {'status': 'running', 'scope': 'new exclusive fixture directories and native runtime temporary ownership',
                  'token_defaults_modified': False, 'native_runtime_verified': False,
                  'root': str(root), 'configured_directories': []}
    def save():
        if evidence:
            evidence.parent.mkdir(parents=True, exist_ok=True)
            evidence.with_suffix('.windows-owner.json').write_text(json.dumps(report, indent=2)+'\n')
    def checked(ok, phase):
        windows_owner_require(bool(ok), phase, c.get_last_error())
    def sid_bytes(address, begin, length, phase):
        windows_owner_require(address is not None and begin <= address <= begin+length-8, phase+' bounds')
        count = c.string_at(address, 2)[1]
        size = 8+4*count
        windows_owner_require(count <= 15 and size <= begin+length-address, phase+' length')
        checked(valid_sid(address), phase+' validity')
        return c.string_at(address, size)
    def token_sid(handle, information):
        needed = dword()
        minimum = c.sizeof(pointer)*(2 if information == 1 else 1)
        c.set_last_error(0)
        sized = token_info(handle, information, None, 0, c.byref(needed))
        windows_owner_require(not sized and c.get_last_error() == 122 and
                              minimum <= needed.value <= 1048576, 'token size',
                              (information, sized, needed.value, c.get_last_error()))
        capacity = needed.value
        buffer = c.create_string_buffer(capacity)
        checked(token_info(handle, information, buffer, capacity, c.byref(needed)), 'token query')
        windows_owner_require(minimum <= needed.value <= capacity, 'token returned size')
        address = pointer.from_buffer(buffer).value
        windows_owner_require(address is not None and address >= c.addressof(buffer)+minimum, 'token SID after header')
        return sid_bytes(address, c.addressof(buffer), needed.value, 'token SID')
    def identity(handle):
        attributes, identifier = Attributes(), FileId()
        checked(file_info(handle, 9, c.byref(attributes), c.sizeof(attributes)), 'held attributes')
        windows_owner_require(file_type(handle) == 1 and attributes.attributes & 0x10 and
                              not attributes.attributes & 0x400, 'ordinary disk directory',
                              (attributes.attributes, attributes.reparse_tag))
        checked(file_info(handle, 18, c.byref(identifier), c.sizeof(identifier)), 'full held identity')
        return {'volume': identifier.volume, 'file_id_hex': bytes(identifier.identifier).hex()}
    def ownership(handle, expected_user=None):
        owner, acl, descriptor = pointer(), pointer(), pointer()
        error = get_security(handle, 1, 5, c.byref(owner), None, c.byref(acl), None, c.byref(descriptor))
        windows_owner_require(error == 0 and descriptor.value is not None, 'held security query', error)
        try:
            size = sd_length(descriptor)
            windows_owner_require(20 <= size <= 1048576, 'security descriptor size', size)
            raw_owner = sid_bytes(owner.value, descriptor.value, size, 'root owner SID')
            result = {'owner_sid_hex': raw_owner.hex()}
            if expected_user is not None:
                windows_owner_require(raw_owner == expected_user, 'root effective owner', result)
                windows_owner_require(acl.value is not None and descriptor.value <= acl.value <= descriptor.value+size-8,
                                      'DACL bounds')
                header = Acl.from_address(acl.value)
                windows_owner_require(8 <= header.size <= descriptor.value+size-acl.value and
                                      header.revision == 2 and header.count == 1, 'one-user DACL header')
                checked(valid_acl(acl), 'DACL validity')
                ace = pointer()
                checked(get_ace(acl, 0, c.byref(ace)), 'one-user ACE')
                windows_owner_require(ace.value is not None and acl.value+8 <= ace.value <= acl.value+header.size-8,
                                      'ACE bounds')
                entry = c.string_at(ace.value, 8)
                ace_size = int.from_bytes(entry[2:4], 'little')
                windows_owner_require(entry[:2] == b'\x00\x03' and 16 <= ace_size <= acl.value+header.size-ace.value and
                                      int.from_bytes(entry[4:8], 'little') == 0x1f01ff, 'inheritable user full-control ACE')
                windows_owner_require(sid_bytes(ace.value+8, ace.value, ace_size, 'ACE SID') == expected_user,
                                      'DACL effective user')
                control, revision = word(), dword()
                checked(sd_control(descriptor, c.byref(control), c.byref(revision)), 'DACL control')
                windows_owner_require(control.value & 0x1000 and control.value & 4, 'protected present DACL', control.value)
                result.update({'dacl_hex': c.string_at(acl, header.size).hex(), 'control': control.value,
                               'protected_user_only_inheritable_dacl': True})
            return result
        finally:
            windows_owner_require(local_free(descriptor) is None, 'security descriptor release')
    process, effective = pointer(), pointer()
    held = root_handle = None
    directory_handles = []
    try:
        candidate = pointer()
        checked(open_process(current_process(), 8, c.byref(candidate)), 'process token query handle')
        windows_owner_require(candidate.value not in (None, pointer(-1).value), 'returned process token handle')
        process = candidate
        candidate = pointer()
        if open_thread(current_thread(), 8, True, c.byref(candidate)):
            windows_owner_require(candidate.value not in (None, pointer(-1).value), 'returned effective token handle')
            effective = candidate
        else:
            windows_owner_require(c.get_last_error() == 1008, 'effective thread token', c.get_last_error())
            effective = process
        original = {'effective_user_sid_hex': token_sid(effective, 1).hex(),
                    'effective_owner_sid_hex': token_sid(effective, 4).hex(),
                    'process_owner_sid_hex': token_sid(process, 4).hex()}
        if initial:
            report['original_tokens'] = original
        else:
            windows_owner_require(original == report['original_tokens'], 'fixture token defaults remain original', original)
        user = bytes.fromhex(original['effective_user_sid_hex'])
        # TemporaryDirectory created this empty name exclusively. Adopt its
        # ordinary directory once; all security changes use the held object.
        held = create_file(str(root), 0xe0000 | 0xa0, 7, None, 3, 0x02000000 | 0x00200000, None)
        root_handle = held
        windows_owner_require(held not in (None, pointer(-1).value), 'open exclusive fixture root', c.get_last_error())
        if not initial:
            windows_owner_require(identity(held) == {key: report['root_after'][key] for key in ('volume', 'file_id_hex')},
                                  'held fixture root identity continuity')
            ownership(held, user)
            if directory is None:
                report['parent_tokens_after_native'] = original
                return report
            relative = directory.relative_to(root)
            windows_owner_require(relative.parts and all(part not in ('', '.', '..') for part in relative.parts),
                                  'new fixture directory within held root', str(relative))
            for part in relative.parts:
                raw = part.encode('utf-16-le')
                windows_owner_require(0 < len(raw) <= 65532 and '\x00' not in part and '\\' not in part and '/' not in part,
                                      'one native directory component', part)
                buffer = c.create_string_buffer(raw+b'\x00\x00')
                name = NativeString(len(raw), len(raw)+2, c.addressof(buffer))
                objects = NativeObject(c.sizeof(NativeObject), held, c.pointer(name), 0x1040, None, None)
                io, child = NativeIo(), pointer()
                io.value.status = 0x103
                status = native_create(c.byref(child), 0x1e00a0, c.byref(objects), c.byref(io), None,
                                       0, 7, 1, 0x200021, None, 0)
                if status == 0x103 or (status == 0 and io.value.status == 0x103):
                    try:
                        report['status'] = 'fail'
                        report['nonfinal_native_directory_open'] = str(relative)
                        save()
                    finally:
                        # Evidence failure must not unwind a pending native
                        # request's IOSB, name, or handle storage either.
                        os._exit(1)
                if status == 0 and child.value not in (None, pointer(-1).value):
                    directory_handles.append(child.value)
                windows_owner_require(status == 0 and io.value.status == 0 and io.information == 1 and
                                      child.value not in (None, pointer(-1).value),
                                      'held no-reparse directory walk', (part, status, io.value.status, io.information))
                held = child.value
                identity(held)
        before = identity(held)
        record = {'relative': '.' if initial else str(relative), 'before': {**before, **ownership(held)}}
        if initial:
            report['root_before'] = record['before']
        report['configured_directories'].append(record)
        save()
        sid = c.create_string_buffer(user)
        acl = c.create_string_buffer(16+len(user))
        checked(initialize_acl(acl, len(acl), 2), 'initialize user DACL')
        checked(add_ace(acl, 2, 3, 0x1f01ff, sid), 'add inheritable user ACE')
        error = set_security(held, 1, 0x80000005, sid, None, acl, None)
        windows_owner_require(error == 0, 'set held root owner and protected DACL', error)
        after = identity(held)
        windows_owner_require(before == after, 'root identity after security assignment', (before, after))
        record['after'] = {**after, **ownership(held, user)}
        if initial:
            report['root_after'] = record['after']
        observed = {'effective_user_sid_hex': token_sid(effective, 1).hex(),
                    'effective_owner_sid_hex': token_sid(effective, 4).hex(),
                    'process_owner_sid_hex': token_sid(process, 4).hex()}
        windows_owner_require(original == observed, 'unchanged original token defaults', observed)
        record['token_defaults_unchanged'] = True
        report['tokens_after_root_setup'] = observed
        report['root_setup_verified'] = True
        report['status'] = 'pass' if report['native_runtime_verified'] else 'root-ready'
    except BaseException as error:
        report['status'] = 'fail'
        report['root_setup_failure'] = repr(error)
        raise
    finally:
        cleanup_errors = []
        for handle in reversed(directory_handles):
            if not close(handle):
                cleanup_errors.append(('fixture directory handle release', c.get_last_error()))
        if root_handle not in (None, pointer(-1).value):
            if not close(root_handle):
                cleanup_errors.append(('root handle release', c.get_last_error()))
        if effective.value and effective.value != process.value:
            if not close(effective):
                cleanup_errors.append(('effective token handle release', c.get_last_error()))
        if process.value:
            if not close(process):
                cleanup_errors.append(('process token handle release', c.get_last_error()))
        if cleanup_errors:
            report['status'] = 'fail'
            report['root_setup_cleanup_errors'] = cleanup_errors
        save()
        windows_owner_require(not cleanup_errors, 'all root setup handles released', cleanup_errors)
    return report


def windows_claim_fixture_directories(root: Path, directories: set[Path], evidence: Path | None, report: dict) -> None:
    """Only explicitly new Python fixture directories, before public use.

    Runtime-created directories are never normalized by this helper. The
    native runtime ownership preflight must accept their actual ownership.
    Names come from the copy inputs/lock, never a walk of mutable output names.
    """
    for current in sorted(directories, key=lambda path: (len(path.parts), str(path))):
        windows_private_root(root, evidence, report, current)


def windows_copied_fixture_directories(root: Path, copies: list[tuple[Path, Path]]) -> set[Path]:
    directories = set()
    for borrowed, destination in copies:
        for source in (borrowed, *borrowed.rglob('*')):
            if source.is_dir():
                target = destination/source.relative_to(borrowed)
                while target != root:
                    target.relative_to(root)
                    directories.add(target)
                    target = target.parent
    return directories


WINDOWS_OWNER_PROBE = r'''
/* Native child evidence over the exact installed runtime; no API interposition,
   token mutation, privilege adjustment, or alternate ACL policy. */
#define FREAK_RUNTIME_OWNERSHIP_AUDIT 1
#define FREAK_C_RUNTIME_OWNERSHIP_AUDIT 1
#include "freak_runtime.c"
static void owner_require(bool ok,const char *phase) {
    if (!ok) { fprintf(stderr,"WINDOWS_OWNER_FAIL %s error=%lu\n",phase,(unsigned long)GetLastError()); exit(2); }
}
typedef struct { DWORD size; union { DWORD aligned; BYTE bytes[SECURITY_MAX_SID_SIZE]; } sid; } owner_sid;
typedef struct { owner_sid user,effective_owner,process_owner; } owner_tokens;
static owner_sid owner_token_sid(HANDLE token,TOKEN_INFORMATION_CLASS information) {
    DWORD size=0; SetLastError(0);
    BOOL sized=GetTokenInformation(token,information,NULL,0,&size);
    size_t minimum=information == TokenUser ? sizeof(TOKEN_USER) : sizeof(TOKEN_OWNER);
    owner_require(!sized && GetLastError() == ERROR_INSUFFICIENT_BUFFER && size >= minimum && size <= 1048576,"token-size");
    DWORD capacity=size; BYTE *buffer=malloc(capacity); owner_require(buffer != NULL,"token-allocation");
    owner_require(GetTokenInformation(token,information,buffer,capacity,&size) && size >= minimum && size <= capacity,"token-query");
    PSID pointer=information == TokenUser ? ((TOKEN_USER *)buffer)->User.Sid : ((TOKEN_OWNER *)buffer)->Owner;
    uintptr_t begin=(uintptr_t)buffer,position=(uintptr_t)pointer;
    owner_require(position >= begin+minimum && position-begin <= size && size-(position-begin) >= 8,"token-sid-bounds");
    SID *sid=pointer; DWORD length=8+(DWORD)sid->SubAuthorityCount*4;
    owner_require(sid->SubAuthorityCount <= SID_MAX_SUB_AUTHORITIES && length <= size-(position-begin) &&
                  length <= SECURITY_MAX_SID_SIZE && IsValidSid(pointer),"token-sid-valid");
    owner_sid result={0}; result.size=length; memcpy(result.sid.bytes,pointer,length); free(buffer); return result;
}
static owner_tokens owner_token_snapshot(void) {
    HANDLE process=NULL,effective=NULL;
    owner_require(OpenProcessToken(GetCurrentProcess(),TOKEN_QUERY,&process),"process-token");
    if (!OpenThreadToken(GetCurrentThread(),TOKEN_QUERY,TRUE,&effective)) {
        owner_require(GetLastError() == ERROR_NO_TOKEN,"thread-token"); effective=process;
    }
    owner_tokens result={owner_token_sid(effective,TokenUser),owner_token_sid(effective,TokenOwner),owner_token_sid(process,TokenOwner)};
    if (effective != process) owner_require(CloseHandle(effective),"thread-token-close");
    owner_require(CloseHandle(process),"process-token-close"); return result;
}
static bool owner_same_sid(const owner_sid *a,const owner_sid *b) {
    return a->size == b->size && !memcmp(a->sid.bytes,b->sid.bytes,a->size);
}
static void owner_unchanged(const owner_tokens *original) {
    owner_tokens current=owner_token_snapshot();
    owner_require(owner_same_sid(&original->user,&current.user) && owner_same_sid(&original->effective_owner,&current.effective_owner) &&
                  owner_same_sid(&original->process_owner,&current.process_owner),"original-token-defaults-unchanged");
}
static bool owner_same_id(const FILE_ID_INFO *a,const FILE_ID_INFO *b) {
    return a->VolumeSerialNumber == b->VolumeSerialNumber && !memcmp(a->FileId.Identifier,b->FileId.Identifier,16);
}
static FILE_ID_INFO owner_identity(HANDLE directory) {
    FILE_ID_INFO identity; BY_HANDLE_FILE_INFORMATION attributes;
    owner_require(GetFileInformationByHandle(directory,&attributes) && GetFileType(directory) == FILE_TYPE_DISK &&
                  (attributes.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) && !(attributes.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT),"ordinary-held-directory");
    owner_require(GetFileInformationByHandleEx(directory,FileIdInfo,&identity,sizeof(identity)),"full128-held-identity"); return identity;
}
static owner_sid owner_held_user(HANDLE directory,const owner_sid *user) {
    FILE_ID_INFO before=owner_identity(directory);
    freak_fs_windows_parent_diagnostic diagnostic={NULL,0,-1};
    HANDLE inspected=freak_fs_anchor_reopen(directory,READ_CONTROL,&diagnostic);
    owner_require(inspected != INVALID_HANDLE_VALUE,"held-owner-reopen");
    FILE_ID_INFO reopened=owner_identity(inspected); owner_require(owner_same_id(&before,&reopened),"owner-inspection-full128-identity");
    PSID owner=NULL; PSECURITY_DESCRIPTOR descriptor=NULL;
    DWORD error=GetSecurityInfo(inspected,SE_FILE_OBJECT,OWNER_SECURITY_INFORMATION,&owner,NULL,NULL,NULL,&descriptor);
    owner_require(error == ERROR_SUCCESS && descriptor != NULL && owner != NULL,"actual-held-owner-query");
    DWORD size=GetSecurityDescriptorLength(descriptor); uintptr_t begin=(uintptr_t)descriptor,position=(uintptr_t)owner;
    owner_require(size >= 20 && size <= 1048576 && position >= begin && position-begin <= size && size-(position-begin) >= 8,"actual-owner-bounds");
    SID *sid=owner; DWORD length=8+(DWORD)sid->SubAuthorityCount*4;
    owner_require(sid->SubAuthorityCount <= SID_MAX_SUB_AUTHORITIES && length <= size-(position-begin) &&
                  IsValidSid(owner) && length == user->size && !memcmp(owner,user->sid.bytes,length),"actual-owner-is-effective-user");
    owner_sid actual={0}; actual.size=length; memcpy(actual.sid.bytes,owner,length);
    owner_require(LocalFree(descriptor) == NULL,"actual-owner-descriptor-release");
    owner_require(CloseHandle(inspected),"owner-inspection-close");
    FILE_ID_INFO after=owner_identity(directory); owner_require(owner_same_id(&before,&after),"actual-owner-held-identity-stable");
    diagnostic=(freak_fs_windows_parent_diagnostic){NULL,0,-1};
    owner_require(freak_fs_windows_parent_private(directory,&diagnostic) && diagnostic.owner_match == 1 &&
                  diagnostic.phase && !strcmp(diagnostic.phase,"passed") && diagnostic.native_error == 0,"original-strict-parent-private");
    return actual;
}
static void owner_hex(const BYTE *bytes,DWORD size) { for (DWORD i=0;i<size;i++) printf("%02x",bytes[i]); }
static void owner_id_json(const FILE_ID_INFO *identity) {
    printf("{\"volume\":%llu,\"file_id_hex\":\"",(unsigned long long)identity->VolumeSerialNumber);
    owner_hex(identity->FileId.Identifier,16); printf("\"}");
}
static void owner_temp(const char *parent,const owner_tokens *original,bool llvm,bool emit) {
    int64_t temp=llvm ? freak_llvm_fs_temp_dir((int64_t)(intptr_t)parent,(int64_t)(intptr_t)"native-owner-probe") :
        freak_fs_temp_dir(freak_word_lit(parent),freak_word_lit("native-owner-probe"));
    owner_require(freak_fs_result_ok(temp) && freak_fs_result_completed(temp),"native-temp-created");
    freak_fs_ticket *ticket=freak_fs_ticket_require(temp);
    owner_require(ticket->owns_temp && ticket->temp_active && ticket->has_directory,"native-owned-ticket");
    FILE_ID_INFO before=owner_identity(ticket->directory); owner_sid actual=owner_held_user(ticket->directory,&original->user);
    FILE_ID_INFO after=owner_identity(ticket->directory); owner_require(owner_same_id(&before,&after),"temp-full128-before-after");
    owner_unchanged(original);
    int64_t cleanup=llvm ? freak_llvm_fs_remove_temp_dir_checked(temp) : freak_fs_remove_temp_dir_checked(temp);
    ticket=freak_fs_ticket_require(temp);
    owner_require(freak_fs_result_ok(cleanup) && freak_fs_result_completed(cleanup) &&
                  !ticket->temp_active && !ticket->has_directory,"native-owned-temp-checked-cleanup");
    freak_fs_result_release(cleanup); freak_fs_result_release(temp);
    owner_require(freak_fs_result_live() == 0,"native-temp-ticket-balance"); owner_unchanged(original);
    if (emit) { printf("{\"adapter\":\"%s\",\"held_identity\":",llvm ? "llvm" : "c"); owner_id_json(&before);
        printf(",\"held_identity_after\":"); owner_id_json(&after); printf(",\"owner_sid_hex\":\""); owner_hex(actual.sid.bytes,actual.size);
        printf("\",\"held_owner_matches_effective_user\":true,\"strict_parent_private\":true,\"cleanup_completed\":true,\"live_tickets\":0}"); }
}
int main(void) {
    freak_args_windows_prepare(); owner_require(freak_argc == 2,"arguments");
    const char *parent=freak_argv[1]; owner_tokens original=owner_token_snapshot();
    HANDLE root=freak_fs_anchor_root(parent); owner_require(root != INVALID_HANDLE_VALUE,"root-admission");
    FILE_ID_INFO identity=owner_identity(root); owner_held_user(root,&original.user);
    DWORD cold=0,warm=0,after=0;
    owner_require(GetProcessHandleCount(GetCurrentProcess(),&cold),"cold-handle-count");
    owner_temp(parent,&original,false,false); owner_temp(parent,&original,true,false);
    owner_require(GetProcessHandleCount(GetCurrentProcess(),&warm),"warm-handle-count");
    printf("{\"effective_user_sid_hex\":\""); owner_hex(original.user.sid.bytes,original.user.size);
    printf("\",\"effective_owner_sid_hex\":\""); owner_hex(original.effective_owner.sid.bytes,original.effective_owner.size);
    printf("\",\"process_owner_sid_hex\":\""); owner_hex(original.process_owner.sid.bytes,original.process_owner.size);
    printf("\",\"default_owner_differs_from_user\":%s,\"root_identity\":",owner_same_sid(&original.user,&original.effective_owner) ? "false" : "true");
    owner_id_json(&identity); printf(",\"cases\":["); owner_temp(parent,&original,false,true); printf(","); owner_temp(parent,&original,true,true);
    owner_require(GetProcessHandleCount(GetCurrentProcess(),&after) && warm == after,"native-tested-handle-balance");
    owner_unchanged(&original); FILE_ID_INFO final=owner_identity(root); owner_require(owner_same_id(&identity,&final),"root-full128-final-identity");
    owner_require(CloseHandle(root),"root-close");
    printf("],\"cold_handles\":%lu,\"warm_handles\":%lu,\"after_handles\":%lu,\"token_defaults_unchanged\":true,\"live_tickets\":0}\n",
        (unsigned long)cold,(unsigned long)warm,(unsigned long)after); return 0;
}
'''


def verify_windows_temp_owner(clang: Path, runtime: Path, root: Path, evidence: Path | None, report: dict) -> None:
    """Bounded child proof; retain partial native output on any failure."""
    source, image = root/'windows-owner-probe.c', root/'windows-owner-probe.exe'
    source.write_text(WINDOWS_OWNER_PROBE, encoding='utf-8')
    runtime_before = {path.relative_to(runtime).as_posix(): digest(path)
                      for path in sorted(runtime.rglob('*')) if path.is_file()}
    command = [str(clang), '-O0', str(source), str(runtime/'freak_llvm_runtime.c'),
               '-I', str(runtime), '-lws2_32', '-ladvapi32', '-o', str(image)]
    def save():
        if evidence:
            evidence.with_suffix('.windows-owner.json').write_text(json.dumps(report, indent=2)+'\n')
    report['runtime_inventory'] = runtime_before
    report['probe_source_sha256'] = digest(source)
    report['clang_sha256'] = digest(clang)
    report['pending_launch'] = {'phase': 'compile', 'argv': command, 'child_status_unknown': True}
    save()
    try:
        built = subprocess.run(command, capture_output=True, timeout=90)
        report['build'] = {'argv': command, 'returncode': built.returncode,
                           'stdout_hex': built.stdout.hex(), 'stderr_hex': built.stderr.hex()}
        report['pending_launch'] = None
        save()
        windows_owner_require(built.returncode == 0, 'native ownership probe build', report['build'])
        invocation = [str(image), str(root)]
        report['probe_image_sha256'] = digest(image)
        report['pending_launch'] = {'phase': 'execute', 'argv': invocation, 'child_status_unknown': True}
        save()
        executed = subprocess.run(invocation, capture_output=True, timeout=30)
        report['execution'] = {'argv': invocation, 'returncode': executed.returncode,
                               'stdout_hex': executed.stdout.hex(), 'stderr_hex': executed.stderr.hex()}
        report['pending_launch'] = None
        save()
        windows_owner_require(executed.returncode == 0 and not executed.stderr, 'native ownership probe execution', report['execution'])
        native = json.loads(executed.stdout)
        windows_owner_require({key: native[key] for key in report['original_tokens']} == report['original_tokens'],
                              'native child retains original effective identity/default owner', native)
        windows_owner_require(native['root_identity'] == {key: report['root_after'][key] for key in ('volume', 'file_id_hex')},
                              'native child actual root identity', native)
        windows_owner_require(native['token_defaults_unchanged'] and native['live_tickets'] == 0 and
                              native['default_owner_differs_from_user'] ==
                              (native['effective_user_sid_hex'] != native['effective_owner_sid_hex']) and
                              native['warm_handles'] == native['after_handles'] and
                              [case['adapter'] for case in native['cases']] == ['c', 'llvm'] and
                              all(case['held_owner_matches_effective_user'] and case['strict_parent_private'] and
                                  case['cleanup_completed'] and case['live_tickets'] == 0 and
                                  case['held_identity'] == case['held_identity_after'] and
                                  case['owner_sid_hex'] == native['effective_user_sid_hex'] for case in native['cases']),
                              'native ownership and cleanup oracle', native)
        windows_owner_require(not list(root.glob('native-owner-probe.freak-tmp-*')), 'native owned temp namespace cleanup')
        windows_owner_require(runtime_before == {path.relative_to(runtime).as_posix(): digest(path)
                                                for path in sorted(runtime.rglob('*')) if path.is_file()},
                              'exact installed runtime remains unchanged')
        windows_private_root(root, evidence, report)
        report['native'] = native
        report['native_runtime_verified'] = True
        report['status'] = 'pass'
    except BaseException as error:
        report['status'] = 'fail'
        if isinstance(error, subprocess.TimeoutExpired):
            report['timed_out_launch'] = {'argv': error.cmd, 'timeout': error.timeout,
                                          'stdout_hex': (error.stdout or b'').hex(),
                                          'stderr_hex': (error.stderr or b'').hex()}
        report['native_preflight_failure'] = repr(error)
        raise
    finally:
        save()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--clang', required=True, type=Path)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--source', type=Path)
    parser.add_argument('--git-checkout', type=Path, help='also prove exact local Git commit/source bytes using this frozen V4 root')
    parser.add_argument('--entry-probe', action='store_true', help='mark focused native entry scope; does not establish production CLI parser')
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    candidate, clang, repo = args.candidate.resolve(strict=True), args.clang.resolve(strict=True), args.repo.resolve(strict=True)
    source = (args.source or repo / 'src/compiler/v4').resolve(strict=True)
    records = inventory(source)
    checks: list[str] = []
    limitations: list[str] = []
    forwarder: dict | None = None
    clang_paths: dict | None = None
    staged_witnesses: list[dict] = []
    native_observation: dict | None = None
    with tempfile.TemporaryDirectory(prefix='freak-v35-bootstrap-') as temporary:
        root = Path(temporary).resolve()
        if os.name == 'nt':
            windows_owner = windows_private_root(root, args.evidence)
        # Hostile paths are real arguments, including quotes, Unicode and metacharacters.
        payload = root / "installed é 日本 ' $ &"
        shutil.copytree(repo / 'freakc/runtime', payload / 'runtime')
        vendor = repo / 'third_party/llhttp'
        if vendor.exists():
            shutil.copytree(vendor, payload / 'runtime/third_party/llhttp', dirs_exist_ok=True)
        shutil.copytree(repo / 'std', payload / 'std')
        if os.name == 'nt':
            copied = [(repo/'freakc/runtime', payload/'runtime'), (repo/'std', payload/'std')]
            if vendor.exists():
                copied.append((vendor, payload/'runtime/third_party/llhttp'))
            windows_claim_fixture_directories(root, windows_copied_fixture_directories(root, copied), args.evidence, windows_owner)
        installed = payload / ('freak.exe' if os.name == 'nt' else 'freak')
        shutil.copy2(candidate, installed)
        stable_hash = digest(installed)
        tools = root / 'native-tools'
        tools.mkdir()
        if os.name == 'nt':
            windows_claim_fixture_directories(root, {tools}, args.evidence, windows_owner)
        wrapper_source = root / 'native-wrapper.c'
        wrapper_source.write_text(WRAPPER, encoding='utf-8')
        wrapper = tools / ('clang-wrapper.exe' if os.name == 'nt' else "clang-wrapper é ' $ &")
        command = [str(clang), '-O0', str(wrapper_source), '-o', str(wrapper)]
        if os.name == 'nt':
            command.append('-lshell32')
        built = subprocess.run(command, capture_output=True, timeout=60)
        assert built.returncode == 0, built.stderr
        for name in ('python', 'python3'):
            shutil.copy2(wrapper, tools / (name + '.exe' if os.name == 'nt' else name))
        env = {**os.environ, 'FREAK_HOME': str(payload), 'FREAK_CLANG': str(wrapper),
               'FREAK_BOOTSTRAP_NATIVE_CLANG': str(clang), 'FREAK_BOOTSTRAP_NATIVE_LOG': str(root / 'native.log')}
        # Keep SDK/system executable discovery but intercept every Python basename.
        env['PATH'] = str(tools) + os.pathsep + env.get('PATH', '')
        if os.name == 'nt':
            verify_windows_temp_owner(clang, payload/'runtime', root, args.evidence, windows_owner)
            forwarder=verify_windows_forwarder(clang,wrapper,wrapper_source,root,env,args.evidence)
            clang_paths=verify_windows_clang_paths(clang,wrapper,root,env,args.evidence,forwarder)
            env['FREAK_BOOTSTRAP_NATIVE_WITNESS']=str(root/'staged-clang-witnesses.txt')
        selected = root / "source é 日本 ' $ &"
        copy_source(source, selected, records)
        if os.name == 'nt':
            source_directories = {selected}
            for _, _, relative in records:
                windows_owner_require(not Path(relative).is_absolute() and '..' not in Path(relative).parts,
                                      'new copied source relative directory', relative)
                parent = (selected/relative).parent
                while parent != selected:
                    source_directories.add(parent)
                    parent = parent.parent
            windows_claim_fixture_directories(root, source_directories, args.evidence, windows_owner)
        output_parent = root / ("preview é 日本 ' $ &" + ('\\' if os.name != 'nt' else ''))
        output_parent.mkdir()
        if os.name == 'nt':
            windows_claim_fixture_directories(root, {output_parent}, args.evidence, windows_owner)
        output = output_parent / 'bundle'
        result = bootstrap(installed, selected, output, env,
                           output_spelling=str(output_parent) + '//bundle' if os.name != 'nt' else None)
        if os.name == 'nt':
            witness=Path(env['FREAK_BOOTSTRAP_NATIVE_WITNESS'])
            raw=witness.read_bytes() if witness.exists() else b''
            native_observation={'returncode':result.returncode,'stdout_hex':result.stdout.hex(),
                                'stderr_hex':result.stderr.hex(),'witness_frames_hex':raw.hex(),
                                'witness_phase':'first installed public bootstrap',
                                'expected_header_sha256':digest(payload/'runtime/freak_runtime.h'),
                                'collection_error':None}
            try:
                staged_witnesses=clang_witnesses(witness,(payload/'runtime/freak_runtime.h').read_bytes())
            except Exception as error:
                native_observation['collection_error']=str(error)
            save_clang_observations(args.evidence,forwarder,clang_paths,staged_witnesses,
                                    failed=result.returncode!=0,native=native_observation)
        if result.returncode != 0:
            if args.evidence:
                args.evidence.parent.mkdir(parents=True, exist_ok=True)
                args.evidence.with_suffix('.stdout').write_bytes(result.stdout)
                args.evidence.with_suffix('.stderr').write_bytes(result.stderr)
            raise AssertionError((result.returncode, result.stdout[-4000:], result.stderr[-4000:]))
        if os.name == 'nt':
            assert native_observation['collection_error'] is None, native_observation
            assert staged_witnesses and all(record['kernel_header_verified'] for record in staged_witnesses)
            assert all(record['include_argument'].startswith('//?/') and
                       '\\' not in record['include_argument'] for record in staged_witnesses)
        assert output.is_dir(), output
        assert not list(output_parent.glob('.freak-v4-bootstrap*'))
        report = json.loads((output / 'bootstrap-report.json').read_text(encoding='utf-8'))
        assert report['status'] == 'verified' and report['builder_sha256'] == stable_hash
        assert report['source_inventory'] == 'byte-verified'
        assert report['source_commit'] == (selected / 'bootstrap.lock').read_text().splitlines()[1].split()[1]
        assert report['source_input_sha256'] and report['runtime_inventory_sha256']
        assert report['verification'] == ['native-identity', 'query-store-invalidation', 'scalar-stdio', 'task-arithmetic-branch', 'preview-version', 'preview-check']
        assert digest(installed) == stable_hash, 'stable compiler was replaced'
        preview = output / ('freak-v4.exe' if os.name == 'nt' else 'freak-v4')
        engine = output / ('freak-v4-engine.exe' if os.name == 'nt' else 'freak-v4-engine')
        assert digest(preview) == report['launcher_sha256'] and digest(engine) == report['engine_sha256']
        checks.append('installed native bootstrap, private runtime, identity/query/corpus, stable binary preservation')
        if args.git_checkout:
            checkout = args.git_checkout.resolve(strict=True)
            checkout_records = inventory(checkout)
            before = {relative: digest(checkout / relative) for _, _, relative in checkout_records}
            git_output = output_parent / 'git-bundle'
            images = {'installed': installed, 'selected_clang_wrapper': wrapper, 'underlying_clang': clang}
            image_identities = save_git_build_capture(args.evidence, None, images)
            git_result = bootstrap(installed, checkout, git_output, env)
            save_git_build_capture(args.evidence, git_result, images, image_identities)
            if os.name == 'nt':
                raw=witness.read_bytes() if witness.exists() else b''
                native_observation['git_checkout_bootstrap']={
                    'returncode':git_result.returncode,'stdout_hex':git_result.stdout.hex(),
                    'stderr_hex':git_result.stderr.hex(),'cumulative_witness_frames_hex':raw.hex(),
                    'witness_phase':'second local Git checkout bootstrap'}
                save_clang_observations(args.evidence,forwarder,clang_paths,staged_witnesses,
                                        failed=git_result.returncode!=0,native=native_observation)
            assert git_result.returncode == 0, (git_result.returncode, git_result.stdout[-4000:], git_result.stderr[-4000:])
            git_report = json.loads((git_output / 'bootstrap-report.json').read_text())
            if os.name == 'nt':
                native_observation['git_checkout_bootstrap']['report']=git_report
                save_clang_observations(args.evidence,forwarder,clang_paths,staged_witnesses,
                                        failed=git_report['git_verification']!='commit-source-bytes-verified',
                                        native=native_observation)
            assert git_report['git_verification'] == 'commit-source-bytes-verified', git_report
            assert {relative: digest(checkout / relative) for _, _, relative in checkout_records} == before
            checks.append('exact local Git object/source-byte verification and unchanged checkout')
        # Relocation and a contradictory FREAK_HOME cannot redirect the private payload.
        relocated = root / ("relocated é 日本 ' $ &" + ('\\' if os.name != 'nt' else ''))
        output.rename(relocated)
        preview = relocated / preview.name
        engine = relocated / engine.name
        contradictory = {**env, 'FREAK_HOME': str(root / 'absent-payload')}
        version = subprocess.run([preview, '--version'], cwd=root, env=contradictory, capture_output=True, timeout=30)
        assert version.returncode == 0 and stable_hash.encode() in version.stdout and report['source_input_sha256'].encode() in version.stdout, version
        program = root / "program é 日本 ' $ &.fk"
        program.write_text(PROGRAM, encoding='utf-8')
        for action in ('check', 'emit', 'build'):
            destination = root / ('compiled.exe' if os.name == 'nt' else 'compiled') if action == 'build' else root / 'emitted.ll'
            command = [str(preview), action, str(program)]
            if action != 'check':
                command.append('--output=' + str(destination))
            process = subprocess.run(command, cwd=root, env=contradictory, capture_output=True, timeout=180)
            assert process.returncode == 0, (action, process.stdout, process.stderr)
            if action == 'emit':
                module = destination.read_bytes()
                assert b'define i32 @main' in module and b'@@V4-MODULE' not in module
            if action == 'build':
                executed = subprocess.run([destination], cwd=root, env=contradictory, capture_output=True, timeout=30)
                assert executed.returncode == 42 and executed.stdout == NATIVE_PROGRAM_STDOUT and not executed.stderr, executed
        checks.append('relocated preview version/check/emit/build and actual native program execution')
        if os.name != 'nt':
            # Backslashes are literal POSIX bytes. Guard the different slash path
            # against the exact data-loss bug reproduced by independent review.
            unrelated_parent = root / 'ordinary'
            unrelated_parent.mkdir()
            for action, name in (('emit', 'result.ll'), ('build', 'program')):
                requested = root / ('ordinary\\' + name)
                unrelated = unrelated_parent / name
                requested.write_bytes(b'prior literal output')
                unrelated.write_bytes(b'unrelated slash-path bytes')
                process = subprocess.run([preview, action, program, '--output=' + str(requested)],
                                         cwd=root, env=contradictory, capture_output=True, timeout=180)
                assert process.returncode == 0, (action, process.stdout, process.stderr)
                assert unrelated.read_bytes() == b'unrelated slash-path bytes'
                if action == 'emit':
                    assert b'define i32 @main' in requested.read_bytes()
                else:
                    executed = subprocess.run([requested], cwd=root, env=contradictory, capture_output=True, timeout=30)
                    assert executed.returncode == 42 and executed.stdout == NATIVE_PROGRAM_STDOUT and not executed.stderr, executed
            checks.append('POSIX trailing-backslash parents, repeated separators and literal output leaves preserve unrelated slash-path bytes')
        # Public preview error contracts include stale-output invalidation and aliases.
        program.write_text('task main() -> int { pilot broken = }\n', encoding='utf-8')
        stale = root / 'stale.ll'
        stale.write_text('prior-success')
        rejected = subprocess.run([preview, 'emit', program, '--output=' + str(stale)], cwd=root, env=contradictory, capture_output=True, timeout=120)
        assert rejected.returncode != 0 and not stale.exists(), rejected
        before = program.read_bytes()
        alias = subprocess.run([preview, 'emit', program, '--output=' + str(program)], cwd=root, env=contradictory, capture_output=True, timeout=30)
        assert alias.returncode != 0 and program.read_bytes() == before
        if os.name != 'nt':
            literal_stale = root / 'ordinary\\result.ll'
            literal_stale.write_bytes(b'prior literal success')
            rejected = subprocess.run([preview, 'emit', program, '--output=' + str(literal_stale)],
                                      cwd=root, env=contradictory, capture_output=True, timeout=120)
            assert rejected.returncode != 0 and not literal_stale.exists(), rejected
            assert (unrelated_parent / 'result.ll').read_bytes() == b'unrelated slash-path bytes'
        checks.append('preview diagnostics, nonzero status, stale invalidation, source alias protection')
        # Corrupted private payload is refused before a source can execute.
        runtime_file = relocated / 'runtime/freak_v4_word_runtime.c'
        prior = runtime_file.read_bytes()
        runtime_file.write_bytes(prior + b'\ncorrupt\n')
        corrupt = subprocess.run([preview, '--version'], env=contradictory, capture_output=True, timeout=30)
        assert corrupt.returncode != 0 and b'hash mismatch' in corrupt.stdout, corrupt
        runtime_file.write_bytes(prior)
        prior = engine.read_bytes()
        engine.write_bytes(prior + b'corrupt')
        corrupt = subprocess.run([preview, '--version'], env=contradictory, capture_output=True, timeout=30)
        assert corrupt.returncode != 0 and b'hash mismatch' in corrupt.stdout, corrupt
        engine.write_bytes(prior)
        checks.append('corrupted engine and private runtime byte inventory refused')
        # Frozen source mutations fail before creating an owned stage.
        crate = next(path for role, _, path in records if role == 'source')
        original = (selected / crate).read_bytes()
        (selected / crate).write_bytes(original + b'\n-- edited\n')
        rejected = bootstrap(installed, selected, output_parent / 'edited', env)
        failed(rejected, output_parent / 'edited', output_parent)
        assert b'byte inventory mismatch' in rejected.stdout
        (selected / crate).write_bytes(original)
        # A development syntax failure must preserve its original source location.
        (selected / crate).write_bytes(original + b'\ntask bad_bootstrap( {\n')
        rejected = bootstrap(installed, selected, output_parent / 'syntax', env, locked=False)
        failed(rejected, output_parent / 'syntax', output_parent)
        assert (str(selected / crate).encode() in rejected.stdout or str(selected / crate).encode() in rejected.stderr), rejected
        (selected / crate).write_bytes(original)
        checks.append('frozen source mutation and original-file syntax diagnostics with owned cleanup')
        for mode in ('fail-link',):
            rejected = bootstrap(installed, selected, output_parent / mode, {**env, 'FREAK_BOOTSTRAP_NATIVE_MODE': mode})
            failed(rejected, output_parent / mode, output_parent)
        missing = bootstrap(installed, selected, output_parent / 'missing-tool', {**env, 'FREAK_CLANG': str(root / 'not-a-tool')})
        failed(missing, output_parent / 'missing-tool', output_parent)
        marker = payload / 'runtime/freak_abi'
        prior = marker.read_bytes()
        marker.write_text('wrong-abi\n')
        rejected = bootstrap(installed, selected, output_parent / 'bad-runtime', env)
        failed(rejected, output_parent / 'bad-runtime', output_parent)
        marker.write_bytes(prior)
        checks.append('binary failed link, authoritative missing tool, bad runtime marker; no published output')
        prior_manifest = (selected / 'bootstrap.toml').read_bytes()
        (selected / 'bootstrap.toml').write_bytes(prior_manifest.replace(b'v4-host-bootstrap-v1', b'implicit-profile'))
        rewrite_lock(selected, 'bootstrap.toml')
        rejected = bootstrap(installed, selected, output_parent / 'profile', env)
        failed(rejected, output_parent / 'profile', output_parent)
        (selected / 'bootstrap.toml').write_bytes(prior_manifest)
        shutil.copy2(source / 'bootstrap.lock', selected / 'bootstrap.lock')
        source_hashes = {relative: digest(selected / relative) for _, _, relative in records}
        rejected = bootstrap(installed, selected, selected, env)
        assert rejected.returncode != 0 and {relative: digest(selected / relative) for _, _, relative in records} == source_hashes
        existing = output_parent / 'existing'
        existing.mkdir()
        (existing / 'prior').write_text('prior')
        rejected = bootstrap(installed, selected, existing, env)
        assert rejected.returncode != 0 and (existing / 'prior').read_text() == 'prior'
        checks.append('explicit compatibility required and source/existing-output aliases preserve bytes')
        # Hidden emission is not a second general-purpose write command.
        nonce_env = dict(env)
        nonce_env.pop('FREAK_BOOTSTRAP_STAGE_NONCE', None)
        private = subprocess.run([installed, '__bootstrap-stage', selected, '0' * 64],
                                 cwd=root, env=nonce_env, capture_output=True, timeout=30)
        assert private.returncode != 0 and b'nonce' in private.stdout, private
        assert {relative: digest(selected / relative) for _, _, relative in records} == source_hashes
        checks.append('private emission refuses a caller without its parent invocation nonce')
        # Normal SIGTERM is a failed attempt; a killed owner cannot publish success.
        ready = root / 'slow-ready'
        interrupted_output = output_parent / 'interrupted'
        interrupted_env = {**env, 'FREAK_BOOTSTRAP_NATIVE_MODE': 'slow-link', 'FREAK_BOOTSTRAP_NATIVE_READY': str(ready)}
        command = [str(installed), 'bootstrap', '--v4', '--source=' + str(selected), '--output=' + str(interrupted_output), '--locked']
        process = subprocess.Popen(command, cwd=root, env=interrupted_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        deadline = time.monotonic() + 120
        while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(.02)
        assert ready.exists(), process.communicate(timeout=5)
        process.terminate()
        stdout, stderr = process.communicate(timeout=30)
        assert process.returncode != 0 and not interrupted_output.exists()
        retained = list(output_parent.glob('.freak-v4-bootstrap*'))
        assert all(not (path / 'bootstrap-report.json').exists() for path in retained), retained
        if retained:
            limitations.append('Abrupt owner termination leaves an unpublished private stage; its success report is absent and it is never reused.')
        checks.append('interrupted native link exits nonzero and publishes no output/success report')
        log = (root / 'native.log').read_text(encoding='utf-8')
        assert 'python' not in log.lower(), log
        assert digest(installed) == stable_hash
        checks.append('compiled Python traps unused; stable V3 binary unchanged')
        if os.name == 'nt':
            witness=Path(env['FREAK_BOOTSTRAP_NATIVE_WITNESS'])
            native_observation['cumulative_witness_frames_hex']=witness.read_bytes().hex()
            native_observation['cumulative_witness_phase']='all bootstrap/preview attempts before final collection'
            save_clang_observations(args.evidence,forwarder,clang_paths,staged_witnesses,native=native_observation)
            staged_witnesses=clang_witnesses(witness,
                                            (payload/'runtime/freak_runtime.h').read_bytes())
            save_clang_observations(args.evidence,forwarder,clang_paths,staged_witnesses,native=native_observation)
            assert staged_witnesses and all(record['kernel_header_verified'] for record in staged_witnesses)
            assert all(record['include_argument'].startswith('//?/') and
                       '\\' not in record['include_argument'] for record in staged_witnesses)
    report = {'status': 'pass', 'candidate_sha256': digest(candidate), 'clang_sha256': digest(clang),
              'scope': 'focused native orchestration entry' if args.entry_probe else 'installed public native CLI',
              'checks': checks, 'limitations': limitations, 'forwarder': forwarder,
              'clang_paths':clang_paths,'staged_clang_witnesses':staged_witnesses,
              'native_bootstrap_observation':native_observation,'public_bootstrap_verified':True}
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(report, indent=2) + '\n')
    print(f'PASS native bootstrap/preview {len(checks)} contract groups')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
