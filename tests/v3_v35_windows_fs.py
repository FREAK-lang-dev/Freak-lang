#!/usr/bin/env python3
"""Check Windows held-directory synchronization and publication ACL policy.

Portable runs execute the exact production ACL decision with synthetic ACL
layout fixtures. They prove policy/bounds logic, not Windows OS semantics.
Native Windows runs additionally execute actual held local-NTFS queries, full128
identity opens, normal native flushes and controlled failure responses. Successful
flushes are API evidence, not power-loss or unprivileged-profile proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile


POLICY_HARNESS = r'''
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define WINAPI
typedef int BOOL;
typedef uint32_t DWORD,ACCESS_MASK;
typedef void *PVOID,*PSID;
typedef struct {uint8_t AceType,AceFlags;uint16_t AceSize;} ACE_HEADER;
typedef struct {ACE_HEADER Header;ACCESS_MASK Mask;DWORD SidStart;} ACCESS_ALLOWED_ACE;
typedef struct {uint8_t Revision,SubAuthorityCount,IdentifierAuthority[6];DWORD SubAuthority[15];} SID;
typedef struct {uint8_t AclRevision,Sbz1;uint16_t AclSize,AceCount,Sbz2;} ACL,*PACL;
#define FILE_ADD_FILE 0x00000002u
#define FILE_ADD_SUBDIRECTORY 0x00000004u
#define FILE_WRITE_EA 0x00000010u
#define FILE_DELETE_CHILD 0x00000040u
#define FILE_WRITE_ATTRIBUTES 0x00000100u
#define DELETE 0x00010000u
#define WRITE_DAC 0x00040000u
#define WRITE_OWNER 0x00080000u
#define GENERIC_WRITE 0x40000000u
#define GENERIC_ALL 0x10000000u
#define MAXIMUM_ALLOWED 0x02000000u
#define ACCESS_ALLOWED_ACE_TYPE 0
#define ACCESS_DENIED_ACE_TYPE 1
#define INHERIT_ONLY_ACE 8
#define SID_MAX_SUB_AUTHORITIES 15
PRODUCTION_POLICY
static void require(int ok,const char *why) {if(!ok) {fprintf(stderr,"FAIL: %s\n",why);exit(2);}}
static union {uint64_t aligned;unsigned char bytes[8192];} storage;
static int invalid_acl=0,outside_ace=0,get_ace_calls=0,checks=0;
static SID make_sid(DWORD identifier) {SID s={0};s.Revision=1;s.SubAuthorityCount=1;s.IdentifierAuthority[5]=5;s.SubAuthority[0]=identifier;return s;}
static BOOL valid_sid(PSID raw) {SID *s=raw;return s && s->Revision==1 && s->SubAuthorityCount<=15;}
static BOOL equal_sid(PSID a,PSID b) {SID *first=a,*second=b;return valid_sid(a) && valid_sid(b) && first->SubAuthorityCount==second->SubAuthorityCount && !memcmp(a,b,8+4*first->SubAuthorityCount);}
static BOOL valid_acl(PACL acl) {return !invalid_acl && acl && acl->AclSize>=sizeof(ACL);}
static BOOL get_ace(PACL acl,DWORD index,PVOID *value) {
    get_ace_calls++;if(outside_ace) {*value=storage.bytes+sizeof(storage.bytes);return 1;}
    size_t offset=sizeof(ACL);
    for(DWORD i=0;i<=index;i++) {
        if(offset>acl->AclSize || acl->AclSize-offset<sizeof(ACE_HEADER)) return 0;
        ACE_HEADER *header=(ACE_HEADER *)((unsigned char *)acl+offset);
        if(i==index) {*value=header;return 1;}offset+=header->AceSize;
    }
    return 0;
}
static PACL reset(void) {memset(&storage,0,sizeof storage);PACL acl=(PACL)storage.bytes;acl->AclRevision=2;acl->AclSize=sizeof(ACL);invalid_acl=outside_ace=get_ace_calls=0;return acl;}
static void append(PACL acl,int type,int flags,ACCESS_MASK mask,SID *sid) {
    size_t size=8+8+4*sid->SubAuthorityCount;require(acl->AclSize+size<=sizeof storage.bytes,"fixture bounds");
    ACCESS_ALLOWED_ACE *entry=(ACCESS_ALLOWED_ACE *)(storage.bytes+acl->AclSize);
    entry->Header=(ACE_HEADER){(uint8_t)type,(uint8_t)flags,(uint16_t)size};entry->Mask=mask;memcpy(&entry->SidStart,sid,8+4*sid->SubAuthorityCount);
    acl->AclSize+=(uint16_t)size;acl->AceCount++;
}
static void check(PACL acl,SID *owner,SID *caller,SID *system,SID *admins,int expected,const char *why) {
    require(freak_fs_windows_acl_private(acl,owner,caller,system,admins,valid_acl,get_ace,valid_sid,equal_sid)==expected,why);checks++;
}
int main(void) {
    SID owner=make_sid(1000),other=make_sid(1001),system=make_sid(18),admins=make_sid(544),everyone=make_sid(0);
    PACL acl=reset();check(acl,&owner,&owner,&system,&admins,1,"empty DACL grants nobody write");
    check(NULL,&owner,&owner,&system,&admins,0,"null DACL grants everybody access");
    append(acl,0,0,GENERIC_ALL,&owner);append(acl,0,0,GENERIC_ALL,&system);append(acl,0,0,GENERIC_ALL,&admins);
    append(acl,0,0,0x001200a9u,&everyone);check(acl,&owner,&owner,&system,&admins,1,"owner and privileged writes; readonly others");
    check(acl,&other,&owner,&system,&admins,0,"foreign owner");
    SID invalid=owner;invalid.Revision=2;check(acl,&invalid,&owner,&system,&admins,0,"invalid owner SID");
    const ACCESS_MASK writes[]={FILE_ADD_FILE,FILE_ADD_SUBDIRECTORY,FILE_DELETE_CHILD,FILE_WRITE_EA,FILE_WRITE_ATTRIBUTES,DELETE,WRITE_DAC,WRITE_OWNER,GENERIC_WRITE,GENERIC_ALL,MAXIMUM_ALLOWED};
    for(size_t i=0;i<sizeof(writes)/sizeof(writes[0]);i++) {acl=reset();append(acl,0,0,writes[i],&everyone);check(acl,&owner,&owner,&system,&admins,0,"nonowner write capability");}
    acl=reset();append(acl,0,INHERIT_ONLY_ACE,GENERIC_ALL,&everyone);check(acl,&owner,&owner,&system,&admins,1,"inherit-only ACE does not apply to parent");
    acl=reset();append(acl,1,0,GENERIC_ALL,&everyone);append(acl,0,0,GENERIC_ALL,&everyone);check(acl,&owner,&owner,&system,&admins,0,"deny ACE cannot make ambiguous write grant acceptable");
    acl=reset();append(acl,9,0,0x001200a9u,&owner);check(acl,&owner,&owner,&system,&admins,0,"conditional ACE fails closed");
    acl=reset();append(acl,5,0,0x001200a9u,&owner);check(acl,&owner,&owner,&system,&admins,0,"object ACE fails closed");
    acl=reset();append(acl,0,0,GENERIC_ALL,&owner);invalid_acl=1;check(acl,&owner,&owner,&system,&admins,0,"invalid ACL fails closed");
    invalid_acl=0;outside_ace=1;check(acl,&owner,&owner,&system,&admins,0,"ACE pointer outside ACL");
    outside_ace=0;ACCESS_ALLOWED_ACE *entry=(ACCESS_ALLOWED_ACE *)(storage.bytes+sizeof(ACL));entry->Header.AceSize=12;
    check(acl,&owner,&owner,&system,&admins,0,"truncated SID bounds");
    entry->Header.AceSize=20;((SID *)&entry->SidStart)->SubAuthorityCount=255;check(acl,&owner,&owner,&system,&admins,0,"oversized SID bounds");
    acl=reset();acl->AceCount=4097;check(acl,&owner,&owner,&system,&admins,0,"ACL enumeration budget");require(get_ace_calls==0,"budget checked before enumeration");
    printf("POLICY_OK %d\n",checks);return 0;
}
'''

SYNC_MODEL = r'''
/* Exact production decision logic; API responses below are controlled models,
   not execution of Windows APIs or proof of provider durability. */
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
#define NTAPI
#define WINAPI
typedef int BOOL;typedef uint32_t DWORD,ULONG,ACCESS_MASK;typedef int32_t LONG;
typedef uintptr_t HANDLE,HMODULE,freak_fs_anchor;typedef void *PVOID;
typedef struct { union {LONG status;PVOID pointer;} value;uintptr_t information; } freak_fs_nt_io;
typedef struct {unsigned char Identifier[16];} FILE_ID_128;
typedef struct {uint64_t VolumeSerialNumber;FILE_ID_128 FileId;} FILE_ID_INFO;
typedef struct {DWORD dwFileAttributes;} BY_HANDLE_FILE_INFORMATION;
typedef struct {DWORD dwSize;int Type;FILE_ID_128 ExtendedFileId;} FILE_ID_DESCRIPTOR;
#define INVALID_HANDLE_VALUE UINTPTR_MAX
#define FILE_TYPE_DISK 1
#define FILE_ATTRIBUTE_DIRECTORY 16
#define FILE_ATTRIBUTE_REPARSE_POINT 1024
#define FILE_READ_ATTRIBUTES 128
#define FILE_APPEND_DATA 4
#define SYNCHRONIZE 0x100000
#define FILE_SHARE_READ 1
#define FILE_SHARE_WRITE 2
#define FILE_SHARE_DELETE 4
#define FILE_FLAG_BACKUP_SEMANTICS 0x02000000
#define FILE_FLAG_OPEN_REPARSE_POINT 0x00200000
#define FileIdInfo 18
#define ExtendedFileIdType 2
#define ERROR_ACCESS_DENIED 5
#define ERROR_IO_DEVICE 1117
#define ERROR_NOT_SUPPORTED 50
#define ERROR_PROC_NOT_FOUND 127
static const char *scenario;static DWORD error=777;static int opens=0,closes=0,flushes=0;
static int is(const char *s){return !strcmp(scenario,s);}
static void require(int ok){if(!ok){fputs("MODEL_ASSERTION\n",stderr);exit(70);}}
static DWORD GetLastError(void){return error;}static void SetLastError(DWORD value){error=value;}
static HMODULE GetModuleHandleW(const wchar_t *name){(void)name;return 1;}
static ULONG WINAPI convert(LONG status){(void)status;return ERROR_IO_DEVICE;}
static LONG NTAPI model_query(HANDLE file,freak_fs_nt_io *io,PVOID output,ULONG size,ULONG type){
    require(file==1 && size==8 && type==4);
    if(is("query-pending"))return 0x103;if(is("query-nonfinal"))return 0;
    if(is("query-error"))return -1;
    ULONG *device=output;device[0]=is("query-device")?0:7;device[1]=is("query-remote")?16:0;
    io->value.status=is("query-io-error")?-1:0;io->information=is("query-short")?7:8;return 0;
}
static LONG NTAPI model_flush(HANDLE file,ULONG flags,PVOID parameters,ULONG size,freak_fs_nt_io *io){
    require(file==2 && flags==0 && !parameters && !size);flushes++;
    if(is("flush-pending"))return 0x103;if(is("flush-nonfinal"))return 0;
    if(is("flush-error"))return -1;io->value.status=is("flush-io-error")?-1:0;io->information=0;return 0;
}
static void *GetProcAddress(HMODULE module,const char *name){
    require(module==1);
    if(!strcmp(name,"NtFlushBuffersFileEx"))return is("missing-flush")?NULL:(void *)model_flush;
    if(!strcmp(name,"NtQueryVolumeInformationFile"))return is("missing-query")?NULL:(void *)model_query;
    return (void *)convert;
}
static BOOL GetFileInformationByHandle(HANDLE file,BY_HANDLE_FILE_INFORMATION *info){
    if(is("attributes-error")){error=5;return 0;}
    info->dwFileAttributes=FILE_ATTRIBUTE_DIRECTORY;
    if((file==1 && is("root-reparse")) || (file==2 && is("candidate-reparse")))info->dwFileAttributes|=FILE_ATTRIBUTE_REPARSE_POINT;
    if((file==1 && is("root-file")) || (file==2 && is("candidate-file")))info->dwFileAttributes=0;return 1;
}
static BOOL GetFileInformationByHandleEx(HANDLE file,int type,PVOID raw,DWORD size){
    require(type==FileIdInfo && size==sizeof(FILE_ID_INFO));
    if(file==2 && is("identity-error")){error=5;return 0;}
    FILE_ID_INFO *id=raw;memset(id,0,sizeof(*id));id->VolumeSerialNumber=42;id->FileId.Identifier[15]=99;
    if(file==2 && is("identity-high"))id->FileId.Identifier[15]^=1;
    if(file==2 && is("identity-volume"))id->VolumeSerialNumber^=1;return 1;
}
static DWORD GetFileType(HANDLE file){return (file==1 && is("root-device")) || (file==2 && is("candidate-device"))?3:1;}
static BOOL GetVolumeInformationByHandleW(HANDLE file,wchar_t *name,DWORD count,DWORD *serial,DWORD *component,DWORD *flags,wchar_t *fs,DWORD fs_count){
    require(file==1 && !name && !count && !serial && !component && !flags && fs_count==32);
    if(is("filesystem-error")){error=5;return 0;}wcscpy(fs,is("filesystem-other")?L"ReFS":L"NTFS");return 1;
}
static HANDLE OpenFileById(HANDLE file,FILE_ID_DESCRIPTOR *id,DWORD access,DWORD share,PVOID security,DWORD flags){
    require(file==1 && id->Type==ExtendedFileIdType && id->dwSize==sizeof(*id) && id->ExtendedFileId.Identifier[15]==99 && access==(FILE_APPEND_DATA|FILE_READ_ATTRIBUTES|SYNCHRONIZE) && share==7 && !security && flags==(FILE_FLAG_BACKUP_SEMANTICS|FILE_FLAG_OPEN_REPARSE_POINT));
    if(is("open-error")){error=5;return INVALID_HANDLE_VALUE;}opens++;return 2;
}
static void freak_fs_anchor_close(HANDLE file){require(file==2);closes++;}
PRODUCTION_SYNC
static void callback(void){if(strstr(scenario,"pending") || strstr(scenario,"nonfinal"))fputs("UNSAFE_EXIT_CALLBACK\n",stderr);}
int main(int argc,char **argv){
    require(argc==2);scenario=argv[1];require(atexit(callback)==0);
    bool ok=freak_fs_anchor_sync(1);require(ok==is("native"));require(opens==closes);
    if(ok)require(error==777 && flushes==1 && opens==1);
    else require(error!=777);
    if(strstr(scenario,"identity") || strstr(scenario,"candidate"))require(opens==1 && flushes==0);
    if(strstr(scenario,"query") || strstr(scenario,"missing") || strstr(scenario,"filesystem") || strstr(scenario,"root"))require(!opens && !flushes);
    printf("SYNC_MODEL_OK %d %d %d\n",opens,closes,flushes);return 0;
}
'''

SYNC_CONTROLS = ('missing-flush', 'missing-query', 'filesystem-error', 'filesystem-other',
                 'query-error', 'query-short', 'query-device', 'query-remote',
                 'open-error', 'identity-high', 'identity-volume', 'candidate-reparse',
                 'candidate-file', 'candidate-device')
NONFINAL_CONTROLS = ('query-pending', 'query-nonfinal', 'flush-pending', 'flush-nonfinal')

WINDOWS_HARNESS = r'''
#ifndef _WIN32_WINNT
#define _WIN32_WINNT 0x0602
#endif
#include "freak_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>
#include <winternl.h>
#include <aclapi.h>
extern int64_t freak_llvm_fs_rename_relative_new_checked(int64_t,int64_t,int64_t,int64_t);
static const char *scenario="";static int active=0,directory_flushes=0,candidate_opens=0,candidate_closes=0,dispositions=0;
static HANDLE candidate=INVALID_HANDLE_VALUE,delete_marked=INVALID_HANDLE_VALUE;
static void require(int ok,const char *why) {if(!ok) {fprintf(stderr,"FAIL: %s (Win32 %lu)\n",why,GetLastError());exit(2);}}
#ifdef USE_LLVM_ADAPTER
#define W(s) ((int64_t)(intptr_t)(s))
#define F(n) freak_llvm_fs_##n
#else
#define W(s) freak_word_lit(s)
#define F(n) freak_fs_##n
#endif
static int is(const char *name){return active && !strcmp(scenario,name);}
static void unsafe_callback(void){if(strstr(scenario,"pending") || strstr(scenario,"nonfinal"))fputs("UNSAFE_EXIT_CALLBACK\n",stderr);}
/* These pointers address production-declared native records. Observe/edit
   their SDK-compatible fields through bytes, preserving the original pointer
   and storage lifetime when submitting real native operations. */
static NTSTATUS io_status(PIO_STATUS_BLOCK io){
    NTSTATUS status;memcpy(&status,(const unsigned char *)io+offsetof(IO_STATUS_BLOCK,Status),sizeof(status));return status;
}
static ULONG_PTR io_information(PIO_STATUS_BLOCK io){
    ULONG_PTR information;memcpy(&information,(const unsigned char *)io+offsetof(IO_STATUS_BLOCK,Information),sizeof(information));return information;
}
static void io_pending(PIO_STATUS_BLOCK io){
    NTSTATUS status=0x103;memcpy((unsigned char *)io+offsetof(IO_STATUS_BLOCK,Status),&status,sizeof(status));
}
static void io_short(PIO_STATUS_BLOCK io){
    ULONG_PTR information=sizeof(FILE_FS_DEVICE_INFORMATION)-1;
    memcpy((unsigned char *)io+offsetof(IO_STATUS_BLOCK,Information),&information,sizeof(information));
}
NTSTATUS NTAPI freak_test_flush_ex(HANDLE file,ULONG flags,PVOID parameters,ULONG size,PIO_STATUS_BLOCK io) {
    typedef NTSTATUS (NTAPI *fn)(HANDLE,ULONG,PVOID,ULONG,PIO_STATUS_BLOCK);
    fn real=(fn)(void *)GetProcAddress(GetModuleHandleW(L"ntdll.dll"),"NtFlushBuffersFileEx");
    require(real && flags==0 && !parameters && !size && file==candidate,"exact flush call");
    require(delete_marked==INVALID_HANDLE_VALUE,"delete handle closed before parent flush");
    directory_flushes++;
    if(is("flush-pending"))return 0x103;
    if(is("flush-nonfinal")){io_pending(io);return 0;}
    if(is("directory-fault") && directory_flushes==1)return (NTSTATUS)0xc0000185;
    return real(file,flags,parameters,size,io);
}
NTSTATUS NTAPI freak_test_query_volume(HANDLE file,PIO_STATUS_BLOCK io,PVOID out,ULONG size,FS_INFORMATION_CLASS type) {
    require(type==FileFsDeviceInformation && size==sizeof(FILE_FS_DEVICE_INFORMATION),"exact device query");
    if(is("query-pending"))return 0x103;
    if(is("query-nonfinal")){io_pending(io);return 0;}
    if(is("query-error"))return (NTSTATUS)0xc0000022;
    NTSTATUS status=NtQueryVolumeInformationFile(file,io,out,size,type);
    if(status==0 && io_status(io)==0){
        FILE_FS_DEVICE_INFORMATION device;
        if(io_information(io)>=sizeof(device)){
            memcpy(&device,out,sizeof(device));
            if(is("query-remote"))device.Characteristics|=0x10;
            if(is("query-device"))device.DeviceType=0;
            memcpy(out,&device,sizeof(device));
        }
        if(is("query-short"))io_short(io);
    }
    return status;
}
NTSTATUS NTAPI freak_test_set_information(HANDLE,PIO_STATUS_BLOCK,PVOID,ULONG,FILE_INFORMATION_CLASS);
FARPROC WINAPI freak_test_get_proc_address(HMODULE module,LPCSTR name) {
    if(is("missing-security-api") && !strcmp(name,"GetSecurityInfo")) return NULL;
    if(!strcmp(name,"NtSetInformationFile"))return (FARPROC)freak_test_set_information;
    if(!strcmp(name,"NtFlushBuffersFileEx"))return is("missing-flush") ? NULL : (FARPROC)freak_test_flush_ex;
    if(!strcmp(name,"NtQueryVolumeInformationFile"))return is("missing-query") ? NULL : (FARPROC)freak_test_query_volume;
    return GetProcAddress(module,name);
}
HANDLE WINAPI freak_test_open_by_id(HANDLE parent,LPFILE_ID_DESCRIPTOR id,DWORD access,DWORD share,LPSECURITY_ATTRIBUTES security,DWORD flags){
    require(id->Type==ExtendedFileIdType && id->dwSize==sizeof(*id) && access==(FILE_APPEND_DATA|FILE_READ_ATTRIBUTES|SYNCHRONIZE) && share==7 && !security && flags==(FILE_FLAG_BACKUP_SEMANTICS|FILE_FLAG_OPEN_REPARSE_POINT),"full identity/minimum access open");
    if(is("open-error")){SetLastError(ERROR_ACCESS_DENIED);return INVALID_HANDLE_VALUE;}
    candidate=OpenFileById(parent,id,access,share,security,flags);if(candidate!=INVALID_HANDLE_VALUE)candidate_opens++;return candidate;
}
BOOL WINAPI freak_test_information(HANDLE file,LPBY_HANDLE_FILE_INFORMATION info){
    BOOL ok=GetFileInformationByHandle(file,info);
    if(ok && file==candidate){if(is("candidate-reparse"))info->dwFileAttributes|=FILE_ATTRIBUTE_REPARSE_POINT;if(is("candidate-file"))info->dwFileAttributes&=~FILE_ATTRIBUTE_DIRECTORY;}return ok;
}
BOOL WINAPI freak_test_information_ex(HANDLE file,FILE_INFO_BY_HANDLE_CLASS type,LPVOID out,DWORD size){
    BOOL ok=GetFileInformationByHandleEx(file,type,out,size);
    if(ok && file==candidate && type==FileIdInfo){FILE_ID_INFO *id=out;if(is("identity-high"))id->FileId.Identifier[15]^=1;if(is("identity-volume"))id->VolumeSerialNumber^=1;}return ok;
}
DWORD WINAPI freak_test_file_type(HANDLE file){return file==candidate && is("candidate-device") ? FILE_TYPE_PIPE : GetFileType(file);}
BOOL WINAPI freak_test_volume(HANDLE file,LPWSTR name,DWORD count,LPDWORD serial,LPDWORD component,LPDWORD flags,LPWSTR fs,DWORD fs_count){
    BOOL ok=GetVolumeInformationByHandleW(file,name,count,serial,component,flags,fs,fs_count);
    if(is("filesystem-error")){SetLastError(ERROR_ACCESS_DENIED);return FALSE;}
    if(ok && is("filesystem-other")){require(fs_count>=5,"filesystem buffer");wcscpy(fs,L"ReFS");}return ok;
}
NTSTATUS NTAPI freak_test_set_information(HANDLE file,PIO_STATUS_BLOCK io,PVOID info,ULONG size,FILE_INFORMATION_CLASS type){
    typedef NTSTATUS (NTAPI *fn)(HANDLE,PIO_STATUS_BLOCK,PVOID,ULONG,FILE_INFORMATION_CLASS);
    fn real=(fn)(void *)GetProcAddress(GetModuleHandleW(L"ntdll.dll"),"NtSetInformationFile");
    require(real!=NULL,"real native set-information export");
    NTSTATUS status=real(file,io,info,size,type);DWORD error=GetLastError();
    if(status==0x103 || (status==0 && io_status(io)==0x103)){
        fputs("NONFINAL_NATIVE_DISPOSITION\n",stderr);fflush(NULL);_Exit(1);
    }
    if(status==0 && type==FileDispositionInformation && size==sizeof(BOOLEAN) && *(BOOLEAN *)info){
        require(delete_marked==INVALID_HANDLE_VALUE,"one live deletion disposition");delete_marked=file;dispositions++;
    }
    SetLastError(error);return status;
}
BOOL WINAPI freak_test_close(HANDLE file){
    DWORD error=GetLastError();BOOL ok=CloseHandle(file);
    if(ok && file==candidate){candidate_closes++;candidate=INVALID_HANDLE_VALUE;}
    if(ok && file==delete_marked)delete_marked=INVALID_HANDLE_VALUE;
    SetLastError(error);return ok;
}
static void private_acl(const char *name,int policy) {
    HANDLE token=NULL;require(OpenProcessToken(GetCurrentProcess(),TOKEN_QUERY,&token),"token query");DWORD count=0;
    GetTokenInformation(token,TokenUser,NULL,0,&count);TOKEN_USER *user=malloc(count);require(user!=NULL && GetTokenInformation(token,TokenUser,user,count,&count),"user SID");
    union {DWORD aligned;BYTE bytes[SECURITY_MAX_SID_SIZE];} everyone;DWORD size=sizeof everyone.bytes;
    require(CreateWellKnownSid(WinWorldSid,NULL,everyone.bytes,&size),"everyone SID");
    EXPLICIT_ACCESSW grants[2]={0};grants[0].grfAccessPermissions=FILE_ALL_ACCESS;grants[0].grfAccessMode=SET_ACCESS;
    /* Keep the owner's access on existing and newly created fixture children.
       The controlled nonowner grant below still applies only to the parent. */
    grants[0].grfInheritance=SUB_CONTAINERS_AND_OBJECTS_INHERIT;
    grants[0].Trustee.TrusteeForm=TRUSTEE_IS_SID;grants[0].Trustee.ptstrName=user->User.Sid;
    grants[1].grfAccessPermissions=policy==1 ? FILE_GENERIC_READ | FILE_GENERIC_EXECUTE : policy==2 ? FILE_ADD_FILE : policy==3 ? WRITE_DAC : FILE_DELETE_CHILD;
    grants[1].grfAccessMode=SET_ACCESS;grants[1].Trustee.TrusteeForm=TRUSTEE_IS_SID;grants[1].Trustee.ptstrName=(LPWSTR)(void *)everyone.bytes;
    PACL acl=NULL;require(SetEntriesInAclW(policy ? 2 : 1,grants,NULL,&acl)==ERROR_SUCCESS,"construct private ACL");
    int characters=MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,name,-1,NULL,0);wchar_t *wide=malloc((size_t)characters*sizeof(wchar_t));
    require(wide && MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,name,-1,wide,characters)==characters,"path UTF8");
    DWORD status=SetNamedSecurityInfoW(wide,SE_FILE_OBJECT,OWNER_SECURITY_INFORMATION | DACL_SECURITY_INFORMATION | PROTECTED_DACL_SECURITY_INFORMATION,
        user->User.Sid,NULL,policy==5 ? NULL : acl,NULL);
    require(status==ERROR_SUCCESS,"set real owner/private DACL");LocalFree(acl);free(wide);free(user);CloseHandle(token);
}
static void seed_owner_acl(const char *parent,const char *leaf){
    size_t length=strlen(parent)+strlen(leaf)+2;char *path=malloc(length);
    require(path!=NULL,"seeded child ACL path allocation");
    int written=snprintf(path,length,"%s/%s",parent,leaf);
    require(written>=0 && (size_t)written<length,"seeded child ACL path join");
    private_acl(path,0);free(path);
}
static void release(int64_t ticket,int expected,int completed){require(!!F(result_ok)(ticket)==expected,"checked result");require(!!F(result_completed)(ticket)==completed,"completed result");F(result_release)(ticket);}
int main(int argc,char **argv) {
    require(argc==4,"arguments");scenario=argv[3];require(atexit(unsafe_callback)==0,"callback registration");
    int source_policy=!strcmp(scenario,"source-write") ? 2 : !strcmp(scenario,"null-dacl") ? 5 : 0;
    int destination_policy=!strcmp(scenario,"readonly-others") ? 1 : !strcmp(scenario,"destination-write") ? 2 : !strcmp(scenario,"write-dac") ? 3 : !strcmp(scenario,"delete-child") ? 4 : 0;
    /* Preserve seeded byte-oracle access even for the NULL parent DACL case. */
    seed_owner_acl(argv[1],"a");seed_owner_acl(argv[1],"deletable");seed_owner_acl(argv[2],"neighbor");
    private_acl(argv[1],source_policy);private_acl(argv[2],destination_policy);
    /* Measure first-use cache effects explicitly, then require exact handle
       balance for the tested operation. Warmup is independent owned mutation. */
    DWORD cold=0,before=0,after=0;require(GetProcessHandleCount(GetCurrentProcess(),&cold),"cold handle baseline");
    int64_t warm=F(temp_dir)(W(argv[1]),W("warm"));require(F(result_ok)(warm),"warmup owned temp");
    release(F(mkdir_relative_checked)(warm,W("child")),1,1);release(F(remove_temp_dir_checked)(warm),1,1);F(result_release)(warm);
    require(freak_fs_result_live()==0,"warmup ticket balance");
    require(candidate_opens==candidate_closes && candidate==INVALID_HANDLE_VALUE && delete_marked==INVALID_HANDLE_VALUE,"warmup owned handle balance before reset");require(GetProcessHandleCount(GetCurrentProcess(),&before),"warm handle baseline");
    printf("WARMUP_HANDLES %ld\n",(long)before-(long)cold);
    int64_t source=F(open_dir_ticket)(W(argv[1])),destination=F(open_dir_ticket)(W(argv[2]));require(F(result_ok)(source) && F(result_ok)(destination),"root admission");
    directory_flushes=candidate_opens=candidate_closes=dispositions=0;active=1;
    int ordinary=!strcmp(scenario,"native") || !strcmp(scenario,"readonly-others") || !strcmp(scenario,"source-write") || !strcmp(scenario,"destination-write") || !strcmp(scenario,"write-dac") || !strcmp(scenario,"delete-child") || !strcmp(scenario,"null-dacl") || !strcmp(scenario,"missing-security-api") || !strcmp(scenario,"directory-fault");
    if(ordinary){
        int accepted=!strcmp(scenario,"native") || !strcmp(scenario,"readonly-others");int completed=accepted || !strcmp(scenario,"directory-fault");
        release(F(rename_relative_new_checked)(source,W("a"),destination,W("result")),accepted,completed);
        if(completed)require(directory_flushes==2,"both held parent flushes attempted");
    }else if(is("replace-delete")){
        int64_t buffer=freak_byte_buffer_new();freak_byte_buffer_write_byte(buffer,'N');freak_byte_buffer_write_byte(buffer,0);freak_byte_buffer_write_byte(buffer,255);
        release(F(write_relative_bytes_checked)(source,W("a"),buffer),1,1);freak_byte_buffer_release(buffer);
        release(F(remove_relative_file_checked)(source,W("deletable")),1,1);require(directory_flushes==2 && dispositions==1,"replace/delete both barriers and real disposition");
    }else if(is("temp-rollback")){
        active=0;int64_t temp=F(temp_dir)(W(argv[1]),W("owned"));require(F(result_ok)(temp),"owned staging");active=1;scenario="directory-fault";
        release(F(publish_temp_dir_checked)(temp,destination,W("published")),0,1);require(directory_flushes==2,"both temp parents attempted after first failure");
        scenario="temp-rollback";release(F(remove_temp_dir_checked)(temp),1,1);F(result_release)(temp);require(dispositions==1,"real owned temp disposition observed");
    }else{
        release(F(mkdir_relative_checked)(source,W("runtime")),0,1);
        require(directory_flushes==0,"rejected support/identity never flushed");
    }
    require(candidate_opens==candidate_closes && candidate==INVALID_HANDLE_VALUE,"every sync candidate closed");
    F(result_release)(source);F(result_release)(destination);require(freak_fs_result_live()==0,"result ownership");
    require(GetProcessHandleCount(GetCurrentProcess(),&after) && before==after,"tested-operation handle ownership");
    printf("WINDOWS_OK %d %d %d\n",directory_flushes,candidate_opens,candidate_closes);
    return 0;
}
'''

WINDOWS_RUNTIME_WRAPPER = r'''
#ifndef _WIN32_WINNT
#define _WIN32_WINNT 0x0602
#endif
#include <winsock2.h>
#include <windows.h>
#include <winternl.h>
FARPROC WINAPI freak_test_get_proc_address(HMODULE,LPCSTR);
HANDLE WINAPI freak_test_open_by_id(HANDLE,LPFILE_ID_DESCRIPTOR,DWORD,DWORD,LPSECURITY_ATTRIBUTES,DWORD);
BOOL WINAPI freak_test_information(HANDLE,LPBY_HANDLE_FILE_INFORMATION);
BOOL WINAPI freak_test_information_ex(HANDLE,FILE_INFO_BY_HANDLE_CLASS,LPVOID,DWORD);
DWORD WINAPI freak_test_file_type(HANDLE);
BOOL WINAPI freak_test_volume(HANDLE,LPWSTR,DWORD,LPDWORD,LPDWORD,LPDWORD,LPWSTR,DWORD);
BOOL WINAPI freak_test_close(HANDLE);
#define GetProcAddress freak_test_get_proc_address
#define OpenFileById freak_test_open_by_id
#define GetFileInformationByHandle freak_test_information
#define GetFileInformationByHandleEx freak_test_information_ex
#define GetFileType freak_test_file_type
#define GetVolumeInformationByHandleW freak_test_volume
#define CloseHandle freak_test_close
#include "freak_runtime.c"
_Static_assert(sizeof(freak_fs_nt_io)==sizeof(IO_STATUS_BLOCK),"native IOSB size");
_Static_assert(offsetof(freak_fs_nt_io,value)==offsetof(IO_STATUS_BLOCK,Status),"native IOSB status");
_Static_assert(offsetof(freak_fs_nt_io,information)==offsetof(IO_STATUS_BLOCK,Information),"native IOSB information");
_Static_assert(sizeof(freak_fs_nt_device)==sizeof(FILE_FS_DEVICE_INFORMATION),"device native size");
_Static_assert(offsetof(freak_fs_nt_device,characteristics)==offsetof(FILE_FS_DEVICE_INFORMATION,Characteristics),"device native layout");
'''

POSIX_TEMP_HARNESS = r'''
#define _POSIX_C_SOURCE 200809L
#include "freak_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <sys/stat.h>
#ifdef USE_LLVM_ADAPTER
#define W(s) ((int64_t)(intptr_t)(s))
#define F(n) freak_llvm_fs_##n
#else
#define W(s) freak_word_lit(s)
#define F(n) freak_fs_##n
#endif
static int inject=0,flushes=0;
extern int __real_fsync(int);
int __wrap_fsync(int file){
    struct stat info;if(fstat(file,&info)!=0)exit(70);
    if(inject && S_ISDIR(info.st_mode)){flushes++;if(flushes==1){errno=EIO;return -1;}}
    return __real_fsync(file);
}
static void require(int ok){if(!ok){fprintf(stderr,"temporary publication assertion\n");exit(71);}}
int main(int argc,char **argv){
    require(argc==3);int64_t directory=F(open_dir_ticket)(W(argv[2]));require(F(result_ok)(directory));
    int64_t temp=F(temp_dir)(W(argv[1]),W("owned"));require(F(result_ok)(temp));inject=1;
    int64_t publication=F(publish_temp_dir_checked)(temp,directory,W("published"));
    require(!F(result_ok)(publication)&&F(result_completed)(publication)&&flushes==2);inject=0;
    F(result_release)(publication);int64_t removal=F(remove_temp_dir_checked)(temp);require(F(result_ok)(removal));
    F(result_release)(removal);F(result_release)(temp);F(result_release)(directory);require(freak_fs_result_live()==0);
    puts("TEMP_PARENTS_SYNC_OK");return 0;
}
'''


def coff_undefined_symbols(path: Path) -> list[str]:
    data = path.read_bytes()
    machine, _, _, offset, count, _, _ = struct.unpack_from('<HHIIIHH', data)
    assert machine == 0x8664, 'expected actual x86_64 Windows COFF object'
    table = offset + count * 18
    assert table + 4 <= len(data)
    size = struct.unpack_from('<I', data, table)[0]
    assert table + size <= len(data)
    symbols = []
    index = 0
    while index < count:
        entry = offset + index * 18
        name, value, section, _, storage, auxiliaries = struct.unpack_from('<8sIhHBB', data, entry)
        if name[:4] == bytes(4):
            start = table + struct.unpack_from('<I', name, 4)[0]
            assert table + 4 <= start < table + size
            text = data[start:data.index(b'\0', start, table + size)].decode('utf8')
        else:
            text = name.rstrip(b'\0').decode('utf8')
        if section == 0 and value == 0 and storage == 2:
            symbols.append(text)
        index += 1 + auxiliaries
    return sorted(symbols)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clang', default=os.environ.get('FREAK_CLANG', 'clang'))
    parser.add_argument('--optimization', type=int, choices=(0, 2, 3), action='append')
    parser.add_argument('--sanitize', action='store_true')
    parser.add_argument('--windows-sdk', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    clang = shutil.which(args.clang);assert clang, args.clang
    runtime = Path(__file__).resolve().parents[1]/'freakc'/'runtime'
    include = runtime/'freak_v35_fs.inc'
    contents = include.read_text()
    begin = contents.index('typedef BOOL', contents.index('FREAK_WINDOWS_ACL_POLICY_BEGIN'))
    end = contents.index('/* FREAK_WINDOWS_ACL_POLICY_END */', begin)
    policy = contents[begin:end]
    sync_begin = contents.index('typedef LONG', contents.index('FREAK_WINDOWS_DIRECTORY_SYNC_BEGIN'))
    sync_end = contents.index('/* FREAK_WINDOWS_DIRECTORY_SYNC_END */', sync_begin)
    sync = contents[sync_begin:sync_end]
    hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in [include, runtime/'freak_runtime.c', runtime/'freak_runtime.h', runtime/'freak_llvm_runtime.c']}
    records = []
    report = {'runtime_sha256': hashes, 'test_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'cases': records, 'native_windows_verified': os.name == 'nt',
              'portable_scope': 'exact ACL policy with synthetic native-layout fixtures; not Windows syscall behavior',
              'native_windows_scope': 'real local NTFS/full128 identity opens, checked normal NtFlushEx, original ACL controls, both parents, partial completion, owned rollback, atomic replacement/deletion order; controlled rejection models labelled separately'}
    flags = ['-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-g'] if args.sanitize else []
    environment = dict(os.environ, ASAN_OPTIONS='detect_leaks=1:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1')
    with tempfile.TemporaryDirectory(prefix='freak-windows-fs-') as temporary:
        home = Path(temporary)
        source = home/'policy.c'
        source.write_text(POLICY_HARNESS.replace('PRODUCTION_POLICY', policy))
        if args.sanitize:
            control = home/'control.c';binary = home/'control';controls = []
            for name, body, diagnostic in (
                ('asan_heap_oob', '#include <stdlib.h>\nint main(int n,char**v){volatile char*p=malloc(1);p[n+4]=1;free((void*)p);return 0;}\n', b'AddressSanitizer'),
                ('ubsan_signed_overflow', '#include <stdint.h>\nint main(int n,char**v){volatile int64_t a=INT64_MAX;volatile int64_t b=a+n;return (int)b;}\n', b'runtime error: signed integer overflow')):
                control.write_text(body)
                built = subprocess.run([clang, str(control), '-O0', *flags, '-o', str(binary)], capture_output=True, timeout=60)
                assert built.returncode == 0, built.stderr
                result = subprocess.run([str(binary)], env=environment, capture_output=True, timeout=15)
                assert result.returncode != 0 and diagnostic in result.stderr, result
                controls.append(name)
            report['failing_controls'] = controls
        for optimization in args.optimization or (0, 2, 3):
            binary = home/f'policy-{optimization}'
            built = subprocess.run([clang, str(source), f'-O{optimization}', *flags, '-o', str(binary)], capture_output=True, timeout=60)
            assert built.returncode == 0, built.stderr
            result = subprocess.run([str(binary)], env=environment, capture_output=True, timeout=15)
            assert result.returncode == 0 and not result.stderr and result.stdout.startswith(b'POLICY_OK '), result
            records.append({'case': 'portable-acl-policy', 'optimization': optimization, 'checks': int(result.stdout.split()[1]), 'status': 'pass'})
            print(f'PASS portable Windows ACL policy O{optimization}: {result.stdout.strip().decode()}', flush=True)
        model_source = home/'sync-model.c';model_source.write_text(SYNC_MODEL.replace('PRODUCTION_SYNC',sync))
        model_cases = ('native', *SYNC_CONTROLS, 'attributes-error', 'root-reparse', 'root-file', 'root-device', 'identity-error', 'query-io-error', 'flush-error', 'flush-io-error', *NONFINAL_CONTROLS)
        for optimization in args.optimization or (0, 2, 3):
            binary = home/f'sync-model-{optimization}'
            built = subprocess.run([clang,str(model_source),f'-O{optimization}',*flags,'-o',str(binary)],capture_output=True,timeout=60);assert built.returncode==0,built.stderr
            for name in model_cases:
                result = subprocess.run([str(binary),name],env=environment,capture_output=True,timeout=15)
                if name in NONFINAL_CONTROLS:
                    assert result.returncode==1 and b'nonfinal synchronous directory' in result.stderr and b'UNSAFE_EXIT_CALLBACK' not in result.stderr and not result.stdout,(name,result)
                else:assert result.returncode==0 and not result.stderr and result.stdout.startswith(b'SYNC_MODEL_OK '),(name,result)
                records.append({'case':'controlled-sync-model-'+name,'optimization':optimization,'status':'pass','native_windows_execution':False})
            print(f'PASS exact production directory sync model O{optimization}: {len(model_cases)} controls',flush=True)
        negative_controls = []
        for name, weakened, case in (
                ('truncate-identity-to64',sync.replace('sizeof(identity.FileId.Identifier)', '8'),'identity-high'),
                ('ignore-provider-remote',sync.replace('(device.characteristics & 0x10 /* FILE_REMOTE_DEVICE */)', 'false'),'query-remote'),
                ('skip-real-flush',sync.replace('status=flush(writable,0,NULL,0,&io);', 'io.value.status=0; status=0;'),'native'),
                ('return-with-pending-iosb',sync.replace('freak_fs_sync_nonfinal("flush");', 'return false;'),'flush-pending')):
            assert weakened != sync
            model_source.write_text(SYNC_MODEL.replace('PRODUCTION_SYNC',weakened))
            binary=home/'broken-sync-model'
            built=subprocess.run([clang,str(model_source),'-O2',*flags,'-o',str(binary)],capture_output=True,timeout=60);assert built.returncode==0,built.stderr
            result=subprocess.run([str(binary),case],env=environment,capture_output=True,timeout=15)
            assert result.returncode!=0 and (b'MODEL_ASSERTION' in result.stderr or b'UNSAFE_EXIT_CALLBACK' in result.stderr),(name,result)
            assert b'nonfinal synchronous directory' not in result.stderr,(name,result)
            negative_controls.append({'case':name,'status':'rejected','returncode':result.returncode,'stderr':result.stderr.decode(errors='replace')})
        report['broken_implementation_controls']=negative_controls
        if os.name != 'nt' and os.uname().sysname == 'Linux':
            temp_source = home/'temp-parents.c';temp_source.write_text(POSIX_TEMP_HARNESS)
            for adapter in ('c', 'llvm'):
                for optimization in args.optimization or (0, 2, 3):
                    binary = home/f'temp-{adapter}-{optimization}'
                    command = [clang, str(temp_source), str(runtime/'freak_runtime.c'), f'-I{runtime}', f'-O{optimization}', *flags, '-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1', '-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1', '-Wl,--wrap=fsync', '-lm', '-o', str(binary)]
                    if adapter == 'llvm':command += ['-DUSE_LLVM_ADAPTER=1', str(runtime/'freak_llvm_runtime.c')]
                    built = subprocess.run(command, capture_output=True, timeout=90);assert built.returncode == 0, built.stderr
                    original, destination = home/f'original-{adapter}-{optimization}', home/f'destination-{adapter}-{optimization}'
                    original.mkdir();destination.mkdir();(destination/'neighbor').write_bytes(b'untouched')
                    result = subprocess.run([str(binary), str(original), str(destination)], env=environment, capture_output=True, timeout=15)
                    assert result.returncode == 0 and not result.stderr and result.stdout == b'TEMP_PARENTS_SYNC_OK\n', result
                    assert not list(original.iterdir()) and not (destination/'published').exists() and (destination/'neighbor').read_bytes() == b'untouched'
                    records.append({'adapter': adapter, 'optimization': optimization, 'case': 'posix-temp-publication-both-parent-sync-attempts', 'status': 'pass'})
        harness = home/'windows.c';harness.write_text(WINDOWS_HARNESS)
        wrapper = home/'runtime.c';wrapper.write_text(WINDOWS_RUNTIME_WRAPPER)
        if args.windows_sdk:
            sdk = args.windows_sdk.resolve(strict=True)
            command = [clang, '--target=x86_64-w64-windows-gnu', f'--sysroot={sdk}', '-fsyntax-only', '-Werror=implicit-function-declaration', f'-I{runtime}', str(runtime/'freak_runtime.c'), str(runtime/'freak_llvm_runtime.c')]
            result = subprocess.run(command, capture_output=True, timeout=90)
            assert result.returncode == 0, result.stderr
            report['windows_sdk_syntax'] = {'command': command, 'status': 'pass', 'native_execution': False}
            for adapter in ('c', 'llvm'):
                command = [clang, '--target=x86_64-w64-windows-gnu', f'--sysroot={sdk}', '-fsyntax-only', '-Werror=implicit-function-declaration', f'-I{runtime}', str(harness), str(wrapper)]
                if adapter == 'llvm':command += ['-DUSE_LLVM_ADAPTER=1', str(runtime/'freak_llvm_runtime.c')]
                result = subprocess.run(command, capture_output=True, timeout=90)
                assert result.returncode == 0, result.stderr
                records.append({'case': 'windows-sdk-native-harness-syntax', 'adapter': adapter, 'status': 'pass', 'native_execution': False})
            object_path = home/'runtime.obj'
            command = [clang, '--target=x86_64-w64-windows-gnu', f'--sysroot={sdk}', '-c', '-O2', f'-I{runtime}', str(runtime/'freak_runtime.c'), '-o', str(object_path)]
            result = subprocess.run(command, capture_output=True, timeout=90)
            assert result.returncode == 0, result.stderr
            symbols = coff_undefined_symbols(object_path)
            security_names = ('OpenProcessToken', 'OpenThreadToken', 'GetTokenInformation', 'GetSecurityInfo', 'CreateWellKnownSid', 'IsValidAcl', 'GetAce', 'IsValidSid', 'EqualSid')
            assert '__imp_OpenFileById' in symbols and '__imp_GetVolumeInformationByHandleW' in symbols and '__imp_ReOpenFile' in symbols and not any(s.endswith(n) for s in symbols for n in security_names), symbols
            report['windows_sdk_object'] = {'command': command, 'status': 'pass', 'sha256': hashlib.sha256(object_path.read_bytes()).hexdigest(), 'undefined_symbols': symbols, 'no_new_security_library_imports': True, 'native_execution': False}
        if os.name == 'nt':
            report['native_windows_observations'] = []
            report['native_windows_verified'] = False
            report['gate_passed'] = False
            for adapter in ('c', 'llvm'):
                for optimization in args.optimization or (0, 2, 3):
                    binary = home/f'{adapter}-{optimization}.exe'
                    command = [clang, str(harness), str(wrapper), f'-I{runtime}', f'-O{optimization}', *flags, '-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1', '-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1', '-lws2_32', '-lshell32', '-ladvapi32', '-lntdll', '-o', str(binary)]
                    if adapter == 'llvm':command += ['-DUSE_LLVM_ADAPTER=1', str(runtime/'freak_llvm_runtime.c')]
                    built = subprocess.run(command, capture_output=True, timeout=90);assert built.returncode == 0, built.stderr
                    for name in ('native', 'readonly-others', 'source-write', 'destination-write', 'write-dac', 'delete-child', 'null-dacl', 'missing-security-api', 'directory-fault', *SYNC_CONTROLS, *NONFINAL_CONTROLS, 'replace-delete', 'temp-rollback'):
                        case = home/f'{adapter}-{optimization}-{name}';case.mkdir();source_root, destination = case/'source', case/'destination'
                        source_root.mkdir();destination.mkdir();(source_root/'a').write_bytes(b'published\0\xff');(destination/'neighbor').write_bytes(b'unchanged');(source_root/'deletable').write_bytes(b'delete-me')
                        invocation = [str(binary), str(source_root), str(destination), name]
                        result = subprocess.run(invocation, env=environment, capture_output=True, timeout=15)
                        observation = {'adapter': adapter, 'optimization': optimization, 'case': name,
                                       'command': invocation, 'returncode': result.returncode,
                                       'controlled_api_response': name in (*SYNC_CONTROLS,*NONFINAL_CONTROLS,'directory-fault','missing-security-api','temp-rollback'),
                                       'stdout': result.stdout.decode(errors='replace'),
                                       'stderr': result.stderr.decode(errors='replace'),
                                       'stdout_hex': result.stdout.hex(), 'stderr_hex': result.stderr.hex(),
                                       'text_decoding': 'UTF8 with replacement; hex preserves original bytes',
                                       'oracles_passed': False}
                        report['native_windows_observations'].append(observation)
                        print('WINDOWS_OBSERVATION '+json.dumps(observation), flush=True)
                        if args.report:
                            args.report.parent.mkdir(parents=True, exist_ok=True)
                            args.report.write_text(json.dumps(report, indent=2)+'\n')
                        if name in NONFINAL_CONTROLS:
                            assert result.returncode==1 and b'nonfinal synchronous directory' in result.stderr and b'UNSAFE_EXIT_CALLBACK' not in result.stderr,(name,result)
                        else:
                            assert result.returncode==0 and not result.stderr,(adapter,optimization,name,result)
                            assert result.stdout.startswith(b'WARMUP_HANDLES ') and b'WINDOWS_OK ' in result.stdout,result.stdout
                        assert (destination/'neighbor').read_bytes() == b'unchanged'
                        assert not any(p.is_dir() and p.name.startswith('warm') for p in source_root.iterdir()), 'actual warmup owned directory must be absent'
                        if name in NONFINAL_CONTROLS:
                            assert (source_root/'runtime').is_dir(), 'namespace mutation remains completed on fatal contract violation'
                        else:
                            moved=name in ('native','readonly-others','directory-fault')
                            if name=='replace-delete':
                                assert (source_root/'a').read_bytes()==b'N\0\xff' and not (source_root/'deletable').exists()
                            else:assert not (source_root/'a').exists() if moved else (source_root/'a').read_bytes()==b'published\0\xff'
                            assert (destination/'result').read_bytes()==b'published\0\xff' if moved else not (destination/'result').exists()
                            if name in SYNC_CONTROLS:assert (source_root/'runtime').is_dir(), 'completed failed barrier must leave actual creation'
                            if name=='temp-rollback':assert not (destination/'published').exists() and sorted(p.name for p in source_root.iterdir())==['a','deletable']
                        observation['oracles_passed'] = True
                        records.append({'adapter':adapter,'optimization':optimization,'case':'native-windows-'+name,'status':'pass',
                                        'controlled_api_response':name in (*SYNC_CONTROLS,*NONFINAL_CONTROLS,'directory-fault','missing-security-api','temp-rollback'),
                                        'stdout':result.stdout.decode(errors='replace'),'stderr':result.stderr.decode(errors='replace')})
    assert hashes == {str(path): hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in hashes}, 'runtime changed during verification'
    if os.name == 'nt':report['gate_passed'] = report['native_windows_verified'] = True
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True);args.report.write_text(json.dumps(report, indent=2)+'\n')
    return 0


if __name__ == '__main__':raise SystemExit(main())
