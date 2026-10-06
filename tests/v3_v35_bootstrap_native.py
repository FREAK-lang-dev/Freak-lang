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
        # Hostile paths are real arguments, including quotes, Unicode and metacharacters.
        payload = root / "installed é 日本 ' $ &"
        shutil.copytree(repo / 'freakc/runtime', payload / 'runtime')
        vendor = repo / 'third_party/llhttp'
        if vendor.exists():
            shutil.copytree(vendor, payload / 'runtime/third_party/llhttp', dirs_exist_ok=True)
        shutil.copytree(repo / 'std', payload / 'std')
        installed = payload / ('freak.exe' if os.name == 'nt' else 'freak')
        shutil.copy2(candidate, installed)
        stable_hash = digest(installed)
        tools = root / 'native-tools'
        tools.mkdir()
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
            forwarder=verify_windows_forwarder(clang,wrapper,wrapper_source,root,env,args.evidence)
            clang_paths=verify_windows_clang_paths(clang,wrapper,root,env,args.evidence,forwarder)
            env['FREAK_BOOTSTRAP_NATIVE_WITNESS']=str(root/'staged-clang-witnesses.txt')
        selected = root / "source é 日本 ' $ &"
        copy_source(source, selected, records)
        output_parent = root / ("preview é 日本 ' $ &" + ('\\' if os.name != 'nt' else ''))
        output_parent.mkdir()
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
            git_result = bootstrap(installed, checkout, git_output, env)
            assert git_result.returncode == 0, (git_result.returncode, git_result.stdout[-4000:], git_result.stderr[-4000:])
            git_report = json.loads((git_output / 'bootstrap-report.json').read_text())
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
