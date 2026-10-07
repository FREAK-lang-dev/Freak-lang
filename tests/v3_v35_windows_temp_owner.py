#!/usr/bin/env python3
"""Verify effective-user ownership and private DACLs for Windows owned temps.

Portable controls execute production helper/creation code with modeled native
responses. SDK compilation and native Windows execution are separate evidence.
"""
from __future__ import annotations
import argparse
from contextlib import nullcontext
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
INCLUDE = ROOT/'freakc/runtime/freak_v35_fs.inc'

PREAMBLE = r'''
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
#include <limits.h>
#define WINAPI
#define NTAPI
#undef NULL
#define NULL 0
typedef int BOOL;
typedef uint32_t DWORD,ACCESS_MASK,ULONG;
typedef uint16_t USHORT;
typedef unsigned char BYTE,BOOLEAN;
typedef int32_t LONG;
typedef uintptr_t ULONG_PTR;
typedef intptr_t HANDLE,HMODULE;
typedef HANDLE *PHANDLE;
typedef void *PVOID,*LPVOID,*PSID,*PSECURITY_DESCRIPTOR;
typedef wchar_t *PWSTR;
typedef void *PLARGE_INTEGER;
typedef DWORD *PDWORD,*LPDWORD;
typedef USHORT SECURITY_DESCRIPTOR_CONTROL,*PSECURITY_DESCRIPTOR_CONTROL;
typedef void (*FARPROC)(void);
typedef int TOKEN_INFORMATION_CLASS,SE_OBJECT_TYPE,SECURITY_INFORMATION;
typedef struct {uint8_t Revision,SubAuthorityCount,IdentifierAuthority[6];DWORD SubAuthority[15];} SID;
typedef struct {BYTE AclRevision,Sbz1;USHORT AclSize,AceCount,Sbz2;} ACL,*PACL;
typedef struct {BYTE AceType,AceFlags;USHORT AceSize;} ACE_HEADER;
typedef struct {ACE_HEADER Header;ACCESS_MASK Mask;DWORD SidStart;} ACCESS_ALLOWED_ACE;
typedef struct {struct {PSID Sid;DWORD Attributes;} User;} TOKEN_USER;
typedef struct {DWORD dwFileAttributes;} BY_HANDLE_FILE_INFORMATION;
typedef struct {uint64_t VolumeSerialNumber;unsigned char Identifier[16];} FILE_ID_INFO;
typedef struct {DWORD Revision,Control;PSID Owner,Group;PACL Sacl,Dacl;} SECURITY_DESCRIPTOR;
typedef struct {BYTE Revision,Sbz1;USHORT Control;DWORD Owner,Group,Sacl,Dacl;} SECURITY_DESCRIPTOR_RELATIVE;
typedef BOOL (WINAPI *freak_fs_sid_valid_fn)(PSID);
typedef BOOL (WINAPI *freak_fs_sid_equal_fn)(PSID,PSID);
typedef BOOL (WINAPI *freak_fs_acl_valid_fn)(PACL);
typedef BOOL (WINAPI *freak_fs_ace_fn)(PACL,DWORD,PVOID *);
#define TRUE 1
#define FALSE 0
#define INVALID_HANDLE_VALUE ((HANDLE)-1)
#define ERROR_SUCCESS 0
#define ERROR_ACCESS_DENIED 5
#define ERROR_INVALID_DATA 13
#define ERROR_INSUFFICIENT_BUFFER 122
#define ERROR_PROC_NOT_FOUND 127
#define ERROR_ALREADY_EXISTS 183
#define ERROR_FILE_EXISTS 80
#define ERROR_NO_TOKEN 1008
#define ERROR_INVALID_SID 1337
#define ERROR_INVALID_OWNER 1307
#define ERROR_INVALID_ACL 1336
#define ERROR_INVALID_SECURITY_DESCR 1338
#define TOKEN_QUERY 8
#define TokenUser 1
#define SECURITY_DESCRIPTOR_REVISION 1
#define SID_MAX_SUB_AUTHORITIES 15
#define SECURITY_MAX_SID_SIZE 68
#define SECURITY_DESCRIPTOR_MIN_LENGTH 20
#define ACL_REVISION 2
#define ACCESS_ALLOWED_ACE_TYPE 0
#define OBJECT_INHERIT_ACE 1
#define CONTAINER_INHERIT_ACE 2
#define SE_DACL_PRESENT 4
#define SE_DACL_PROTECTED 0x1000
#define SE_SELF_RELATIVE 0x8000
#define FILE_ALL_ACCESS 0x1f01ff
#define READ_CONTROL 0x20000u
#define SYNCHRONIZE 0x100000u
#define FILE_READ_ATTRIBUTES 0x80u
#define FILE_LIST_DIRECTORY 1u
#define FILE_TRAVERSE 0x20u
#define FILE_ADD_FILE 2u
#define FILE_ADD_SUBDIRECTORY 4u
#define FILE_DELETE_CHILD 0x40u
#define DELETE 0x10000u
#define GENERIC_READ 0x80000000u
#define GENERIC_WRITE 0x40000000u
#define FILE_SHARE_READ 1
#define FILE_SHARE_WRITE 2
#define FILE_SHARE_DELETE 4
#define FILE_ATTRIBUTE_NORMAL 0x80u
#define FILE_ATTRIBUTE_DIRECTORY 0x10u
#define FILE_ATTRIBUTE_REPARSE_POINT 0x400u
#define FILE_TYPE_DISK 1
#define DUPLICATE_SAME_ACCESS 2
#define FileIdInfo 18
#define LOAD_LIBRARY_SEARCH_SYSTEM32 0x800u
#define SE_FILE_OBJECT 1
#define OWNER_SECURITY_INFORMATION 1
#define DACL_SECURITY_INFORMATION 4
static DWORD GetLastError(void);
static void SetLastError(DWORD);
static HANDLE GetCurrentProcess(void),GetCurrentThread(void);
static BOOL CloseHandle(HANDLE),FreeLibrary(HMODULE);
static BOOL DuplicateHandle(HANDLE,HANDLE,HANDLE,HANDLE *,DWORD,BOOL,DWORD);
static BOOL GetFileInformationByHandle(HANDLE,BY_HANDLE_FILE_INFORMATION *);
static BOOL GetFileInformationByHandleEx(HANDLE,int,void *,DWORD);
static DWORD GetFileType(HANDLE);
static HMODULE GetModuleHandleW(const wchar_t *),LoadLibraryExW(const wchar_t *,HANDLE,DWORD);
static FARPROC GetProcAddress(HMODULE,const char *);
static void *LocalFree(void *),*freak_command_allocate(size_t,size_t);
static wchar_t *freak_command_wide(const char *);
'''

API = r'''
static const char *scenario;
static DWORD error;
static int modules,tokens,children,descriptors,created,disposed,queries,processes,threads,defaults;
static SID caller;
typedef union {DWORD aligned;BYTE bytes[sizeof(ACL)+offsetof(ACCESS_ALLOWED_ACE,SidStart)+SECURITY_MAX_SID_SIZE];} ACL_STORAGE;
typedef struct {SECURITY_DESCRIPTOR descriptor;SID owner;ACL_STORAGE acl;} RETURNED_SECURITY;
static RETURNED_SECURITY *returned_security;
static void require(int ok,const char *why){if(!ok){fprintf(stderr,"FAIL %s\n",why);exit(2);}}
static int is(const char *name){return !strcmp(scenario,name);}
static DWORD GetLastError(void){return error;}
static void SetLastError(DWORD value){error=value;}
static HANDLE GetCurrentProcess(void){return -2;}
static HANDLE GetCurrentThread(void){return -3;}
static BOOL CloseHandle(HANDLE handle){if(handle==200){require(tokens==1,"token owned once");tokens--;}else if(handle==123){require(children==1,"new child owned once");children--;}else require(0,"only owned handles close");error=777;return TRUE;}
static BOOL FreeLibrary(HMODULE module){require(module==50 && modules==1,"module owned once");modules--;error=778;return TRUE;}
static BOOL DuplicateHandle(HANDLE a,HANDLE b,HANDLE c,HANDLE *d,DWORD e,BOOL f,DWORD g){(void)a;(void)b;(void)c;(void)d;(void)e;(void)f;(void)g;require(0,"no duplication");return FALSE;}
static void *LocalFree(void *memory){require(memory && descriptors==1,"descriptor owned once");free(memory);descriptors--;error=779;return NULL;}
static void *freak_command_allocate(size_t count,size_t size){void *memory=calloc(count,size);require(memory!=NULL,"allocation");return memory;}
static wchar_t *freak_command_wide(const char *name){size_t n=strlen(name)+1;wchar_t *wide=calloc(n,sizeof(*wide));require(wide!=NULL,"wide allocation");for(size_t i=0;i<n;i++)wide[i]=(unsigned char)name[i];return wide;}
static HMODULE LoadLibraryExW(const wchar_t *name,HANDLE unused,DWORD flags){require(!wcscmp(name,L"advapi32.dll") && !unused && flags==LOAD_LIBRARY_SEARCH_SYSTEM32,"only system security library");if(is("library")){error=101;return 0;}modules++;return 50;}
static HMODULE GetModuleHandleW(const wchar_t *name){require(!wcscmp(name,L"ntdll.dll"),"native module");return 1;}
static BOOL valid_sid(PSID raw){SID *sid=raw;return sid && sid->Revision==1 && sid->SubAuthorityCount<=15;}
static BOOL equal_sid(PSID first,PSID second){require(valid_sid(first) && valid_sid(second),"valid SID compare");SID *sid=first;return !memcmp(first,second,8+4*sid->SubAuthorityCount);}
static BOOL open_thread(HANDLE thread,DWORD access,BOOL itself,HANDLE *token){require(thread==-3 && access==TOKEN_QUERY && itself,"effective thread query");threads++;if(is("thread-error")){*token=999;error=102;return FALSE;}if(is("thread")){tokens++;*token=200;return TRUE;}*token=998;error=ERROR_NO_TOKEN;return FALSE;}
static BOOL open_process(HANDLE process,DWORD access,HANDLE *token){require(process==-2 && access==TOKEN_QUERY,"process fallback query only");processes++;if(is("process-error")){*token=997;error=103;return FALSE;}tokens++;*token=200;return TRUE;}
static BOOL token_info(HANDLE token,TOKEN_INFORMATION_CLASS kind,LPVOID buffer,DWORD capacity,PDWORD needed){require(token==200 && kind==TokenUser,"never query/change token default owner");queries++;
    if(!buffer){*needed=sizeof(TOKEN_USER)+sizeof(SID);error=ERROR_INSUFFICIENT_BUFFER;if(is("size-small"))*needed=1;if(is("size-large"))*needed=1048577;if(is("size-error"))error=104;if(is("size-success"))return TRUE;return FALSE;}
    if(is("user-error")){error=105;return FALSE;}require(capacity==sizeof(TOKEN_USER)+sizeof(SID),"bounded allocated buffer");
    TOKEN_USER *user=buffer;user->User.Sid=(BYTE *)buffer+sizeof(TOKEN_USER);memcpy(user->User.Sid,&caller,sizeof(caller));*needed=capacity;
    if(is("user-length-small"))*needed=1;if(is("user-length-large"))*needed=capacity+1;
    if(is("sid-null"))user->User.Sid=NULL;if(is("sid-before"))user->User.Sid=(BYTE *)buffer-1;if(is("sid-after"))user->User.Sid=(BYTE *)buffer+capacity;if(is("sid-short"))user->User.Sid=(BYTE *)buffer+capacity-7;if(is("sid-unaligned"))user->User.Sid=(BYTE *)user->User.Sid+1;
    if(is("sid-subauthorities"))((SID *)user->User.Sid)->SubAuthorityCount=16;if(is("sid-truncated")){((SID *)user->User.Sid)->SubAuthorityCount=15;*needed=sizeof(TOKEN_USER)+12;}if(is("sid-invalid"))((SID *)user->User.Sid)->Revision=2;
    return TRUE;
}
static BOOL init_descriptor(PSECURITY_DESCRIPTOR raw,DWORD revision){require(revision==1,"descriptor revision");if(is("init")){error=106;return FALSE;}memset(raw,0,sizeof(SECURITY_DESCRIPTOR));((SECURITY_DESCRIPTOR *)raw)->Revision=1;return TRUE;}
static BOOL set_owner(PSECURITY_DESCRIPTOR raw,PSID owner,BOOL defaulted){SECURITY_DESCRIPTOR *sd=raw;require(sd->Revision==1 && !sd->Control && !sd->Dacl && !sd->Sacl && !sd->Group && valid_sid(owner) && !defaulted,"explicit user owner before private ACL setup");if(is("set-owner")){error=107;return FALSE;}sd->Owner=owner;return TRUE;}
static BOOL initialize_acl(PACL acl,DWORD length,DWORD revision){require(length==sizeof(ACL_STORAGE) && revision==ACL_REVISION,"bounded maximum SID ACL storage");if(is("init-acl")){error=112;return FALSE;}memset(acl,0,length);acl->AclRevision=revision;acl->AclSize=length;return TRUE;}
static BOOL add_ace(PACL acl,DWORD revision,DWORD flags,DWORD mask,PSID sid){require(acl->AclRevision==revision && !acl->AceCount && flags==3 && mask==FILE_ALL_ACCESS && equal_sid(sid,&caller),"only inheritable caller full-access ACE");if(is("add-ace")){error=113;return FALSE;}
    ACCESS_ALLOWED_ACE *ace=(ACCESS_ALLOWED_ACE *)((BYTE *)acl+sizeof(ACL));size_t bytes=8+4*((SID *)sid)->SubAuthorityCount;ace->Header=(ACE_HEADER){0,flags,offsetof(ACCESS_ALLOWED_ACE,SidStart)+bytes};ace->Mask=mask;memcpy(&ace->SidStart,sid,bytes);acl->AceCount=1;return TRUE;
}
static BOOL set_dacl(PSECURITY_DESCRIPTOR raw,BOOL present,PACL acl,BOOL defaulted){SECURITY_DESCRIPTOR *sd=raw;require(present && !defaulted && acl && sd->Owner && !sd->Dacl && !sd->Control,"non-NULL explicit private DACL");if(is("set-dacl")){error=114;return FALSE;}sd->Dacl=acl;sd->Control|=SE_DACL_PRESENT;return TRUE;}
static BOOL set_control(PSECURITY_DESCRIPTOR raw,SECURITY_DESCRIPTOR_CONTROL bits,SECURITY_DESCRIPTOR_CONTROL selected){SECURITY_DESCRIPTOR *sd=raw;require(bits==SE_DACL_PROTECTED && selected==SE_DACL_PROTECTED && sd->Dacl,"exclude inherited parent permissions at creation");if(is("set-control")){error=115;return FALSE;}sd->Control=(sd->Control&~bits)|selected;return TRUE;}
static DWORD get_length(PSECURITY_DESCRIPTOR raw){require(raw==returned_security,"length of held returned descriptor");if(is("descriptor-size-small"))return 19;if(is("descriptor-size-large"))return 1048577;return sizeof(RETURNED_SECURITY);}
static BOOL get_control(PSECURITY_DESCRIPTOR raw,PSECURITY_DESCRIPTOR_CONTROL control,LPDWORD revision){require(raw==returned_security,"control of held returned descriptor");if(is("get-control")){error=116;return FALSE;}*control=((SECURITY_DESCRIPTOR *)raw)->Control;*revision=is("descriptor-revision")?2:1;return TRUE;}
static BOOL valid_acl(PACL acl){require(acl==(PACL)returned_security->acl.bytes,"validate bounded returned ACL");return !is("acl-invalid");}
static BOOL get_ace(PACL acl,DWORD index,PVOID *pointer){require(acl==(PACL)returned_security->acl.bytes && !index,"only bounded actual ACE query");if(is("get-ace")){error=117;return FALSE;}*pointer=(BYTE *)acl+sizeof(ACL);if(is("ace-null"))*pointer=NULL;if(is("ace-before"))*pointer=(BYTE *)acl-1;if(is("ace-after"))*pointer=(BYTE *)acl+acl->AclSize;if(is("ace-short"))*pointer=(BYTE *)acl+acl->AclSize-15;if(is("ace-unaligned"))*pointer=(BYTE *)acl+sizeof(ACL)+1;if(is("ace-outside-but-valid")){void *outside=(BYTE *)&returned_security->owner+16;memcpy(outside,*pointer,20);*pointer=outside;}return TRUE;}
static DWORD get_info(HANDLE child,SE_OBJECT_TYPE kind,SECURITY_INFORMATION selected,PSID *owner,PSID *group,PACL *acl,PACL *sacl,PSECURITY_DESCRIPTOR *descriptor){require(child==123 && children==1 && kind==SE_FILE_OBJECT && selected==(OWNER_SECURITY_INFORMATION|DACL_SECURITY_INFORMATION) && !group && acl && !sacl,"query held actual owner and DACL");
    if(is("descriptor-null")){*descriptor=NULL;*owner=NULL;*acl=NULL;return 0;}
    returned_security=calloc(1,sizeof(*returned_security));require(returned_security!=NULL,"descriptor allocation");RETURNED_SECURITY *r=returned_security;*descriptor=r;descriptors++;r->owner=caller;*owner=&r->owner;*acl=(PACL)r->acl.bytes;
    r->descriptor.Revision=1;r->descriptor.Control=SE_SELF_RELATIVE|SE_DACL_PRESENT|SE_DACL_PROTECTED;r->descriptor.Owner=*owner;r->descriptor.Dacl=*acl;
    (*acl)->AclRevision=ACL_REVISION;(*acl)->AclSize=sizeof(ACL_STORAGE);(*acl)->AceCount=1;
    size_t caller_size=8+4*caller.SubAuthorityCount;
    ACCESS_ALLOWED_ACE *ace=(ACCESS_ALLOWED_ACE *)(r->acl.bytes+sizeof(ACL));ace->Header=(ACE_HEADER){0,3,offsetof(ACCESS_ALLOWED_ACE,SidStart)+caller_size};ace->Mask=FILE_ALL_ACCESS;memcpy(&ace->SidStart,&caller,caller_size);
    if(is("owner-query"))return 108;if(is("owner-null"))*owner=NULL;if(is("owner-before"))*owner=(BYTE *)r-1;if(is("owner-after"))*owner=(BYTE *)r+sizeof(*r);if(is("owner-short"))*owner=(BYTE *)r+sizeof(*r)-7;if(is("owner-unaligned"))*owner=(BYTE *)&r->owner+1;
    if(is("owner-invalid"))r->owner.Revision=2;if(is("owner-subauthorities"))r->owner.SubAuthorityCount=16;
    if(is("owner-different") || strstr(scenario,"cleanup-") || is("api-NtSetInformationFile"))r->owner.SubAuthority[0]++;
    if(is("descriptor-unprotected"))r->descriptor.Control&=~SE_DACL_PROTECTED;if(is("descriptor-absolute"))r->descriptor.Control&=~SE_SELF_RELATIVE;if(is("descriptor-no-dacl"))r->descriptor.Control&=~SE_DACL_PRESENT;
    if(is("acl-null"))*acl=NULL;if(is("acl-before"))*acl=(PACL)((BYTE *)r-1);if(is("acl-after"))*acl=(PACL)((BYTE *)r+sizeof(*r));if(is("acl-short"))*acl=(PACL)((BYTE *)r+sizeof(*r)-7);if(is("acl-unaligned"))*acl=(PACL)(r->acl.bytes+1);
    PACL stored=(PACL)r->acl.bytes;
    if(is("acl-revision"))stored->AclRevision=4;if(is("acl-no-ace"))stored->AceCount=0;if(is("acl-extra-ace"))stored->AceCount=2;if(is("acl-small"))stored->AclSize=7;if(is("acl-large"))stored->AclSize=65535;
    if(is("ace-type"))ace->Header.AceType=5;if(is("ace-flags"))ace->Header.AceFlags|=8;if(is("ace-mask"))ace->Mask|=0x80000000;if(is("ace-size-small"))ace->Header.AceSize=19;if(is("ace-size-large"))ace->Header.AceSize=65535;
    SID *granted=(SID *)&ace->SidStart;if(is("ace-sid-invalid"))granted->Revision=2;if(is("ace-sid-subauthorities"))granted->SubAuthorityCount=16;if(is("ace-sid-truncated")){granted->SubAuthorityCount=15;ace->Header.AceSize=68;}if(is("ace-sid-different"))granted->SubAuthority[0]++;
    return 0;
}
static BOOL GetFileInformationByHandle(HANDLE handle,BY_HANDLE_FILE_INFORMATION *info){require(handle==123,"held new attributes");if(is("attributes")){error=109;return FALSE;}info->dwFileAttributes=is("not-directory")?0:FILE_ATTRIBUTE_DIRECTORY;if(is("reparse"))info->dwFileAttributes|=FILE_ATTRIBUTE_REPARSE_POINT;return TRUE;}
static DWORD GetFileType(HANDLE handle){require(handle==123,"held new kind");return is("not-disk")?2:FILE_TYPE_DISK;}
static BOOL GetFileInformationByHandleEx(HANDLE handle,int kind,void *data,DWORD length){(void)handle;(void)kind;(void)data;(void)length;require(0,"no path reopen or identity substitution");return FALSE;}
static LONG nt_create(PHANDLE child,ACCESS_MASK access,freak_fs_nt_object *object,freak_fs_nt_io *io,PLARGE_INTEGER size,ULONG attrs,ULONG share,ULONG disposition,ULONG options,PVOID ea,ULONG ea_length){
    SECURITY_DESCRIPTOR *sd=object->security;require(object->root==10 && object->attributes==0x40 && !object->quality && !wcscmp(object->name->buffer,L"fresh") && object->name->length==5*sizeof(wchar_t),"held relative exact create");
    ACCESS_MASK minimum=SYNCHRONIZE|FILE_READ_ATTRIBUTES|FILE_LIST_DIRECTORY|FILE_TRAVERSE|DELETE|FILE_ADD_FILE|FILE_ADD_SUBDIRECTORY|FILE_DELETE_CHILD;
    require(access==(minimum|(sd?READ_CONTROL:0)) && !size && attrs==FILE_ATTRIBUTE_NORMAL && share==7 && disposition==2 && options==0x200021 && !ea && !ea_length,"exact create rights/options");
    if(sd){require(sd->Owner && equal_sid(sd->Owner,&caller) && !sd->Group && !sd->Sacl && sd->Dacl && sd->Control==(SE_DACL_PRESENT|SE_DACL_PROTECTED),"live caller SID and protected private SD");
        PACL acl=sd->Dacl;require(acl->AclRevision==2 && acl->AceCount==1 && acl->AclSize==sizeof(ACL_STORAGE),"live bounded single ACE ACL");ACCESS_ALLOWED_ACE *ace=(ACCESS_ALLOWED_ACE *)((BYTE *)acl+sizeof(ACL));require(ace->Header.AceType==0 && ace->Header.AceFlags==3 && ace->Header.AceSize==16+4*caller.SubAuthorityCount && ace->Mask==FILE_ALL_ACCESS && equal_sid(&ace->SidStart,&caller),"caller-only inheritable creation rights");}
    else require(is("ordinary"),"only ordinary callers use default security");
    if(is("create-error") || is("collision") || is("file-collision")){error=110;return -1;}
    io->value.status=0;io->information=2;
    if(is("create-pending"))return 0x103;
    if(is("create-io-pending"))io->value.status=0x103;
    if(is("create-informational"))return 1;
    if(is("create-io-error"))io->value.status=-2;
    if(is("not-created"))io->information=1;
    children++;created++;*child=123;return 0;
}
static LONG nt_set(HANDLE child,freak_fs_nt_io *io,PVOID value,ULONG length,ULONG kind){require(child==123 && children==1 && length==sizeof(BOOLEAN) && kind==13 && *(BOOLEAN *)value,"dispose exact newly held identity");disposed++;
    io->value.status=0;io->information=0;
    if(is("cleanup-pending"))return 0x103;if(is("cleanup-io-pending"))io->value.status=0x103;if(is("cleanup-error"))return -3;if(is("cleanup-io-error"))io->value.status=-4;return 0;
}
static ULONG convert_status(LONG status){require(status==-1,"creation failure conversion");return is("collision")?ERROR_ALREADY_EXISTS:is("file-collision")?ERROR_FILE_EXISTS:110;}
static FARPROC GetProcAddress(HMODULE module,const char *name){char missing[96];snprintf(missing,sizeof(missing),"api-%s",name);if(is(missing)){error=111;return NULL;}
    if(module==1){if(!strcmp(name,"NtCreateFile"))return (FARPROC)nt_create;if(!strcmp(name,"NtSetInformationFile"))return (FARPROC)nt_set;if(!strcmp(name,"RtlNtStatusToDosError"))return (FARPROC)convert_status;require(0,"unexpected native API");}
    require(module==50,"security module");
    if(!strcmp(name,"OpenProcessToken"))return (FARPROC)open_process;if(!strcmp(name,"OpenThreadToken"))return (FARPROC)open_thread;if(!strcmp(name,"GetTokenInformation"))return (FARPROC)token_info;
    if(!strcmp(name,"InitializeSecurityDescriptor"))return (FARPROC)init_descriptor;if(!strcmp(name,"SetSecurityDescriptorOwner"))return (FARPROC)set_owner;if(!strcmp(name,"GetSecurityInfo"))return (FARPROC)get_info;
    if(!strcmp(name,"InitializeAcl"))return (FARPROC)initialize_acl;if(!strcmp(name,"AddAccessAllowedAceEx"))return (FARPROC)add_ace;if(!strcmp(name,"SetSecurityDescriptorDacl"))return (FARPROC)set_dacl;if(!strcmp(name,"SetSecurityDescriptorControl"))return (FARPROC)set_control;
    if(!strcmp(name,"GetSecurityDescriptorLength"))return (FARPROC)get_length;if(!strcmp(name,"GetSecurityDescriptorControl"))return (FARPROC)get_control;if(!strcmp(name,"IsValidAcl"))return (FARPROC)valid_acl;if(!strcmp(name,"GetAce"))return (FARPROC)get_ace;
    if(!strcmp(name,"IsValidSid"))return (FARPROC)valid_sid;if(!strcmp(name,"EqualSid"))return (FARPROC)equal_sid;
    require(0,"no token mutation, extra privilege or path APIs");return NULL;
}
'''

MAIN = r'''
static void unsafe_callback(void){fputs("UNSAFE_CALLBACK\n",stderr);}
int main(int argc,char **argv){require(argc==2,"scenario");scenario=argv[1];caller.Revision=1;caller.SubAuthorityCount=1;caller.IdentifierAuthority[5]=5;caller.SubAuthority[0]=1000;
    if(is("max-sid"))caller.SubAuthorityCount=15;if(is("short-sid"))caller.SubAuthorityCount=0;
    bool retry=false;HANDLE result;
    if(strstr(argv[1],"pending"))require(!atexit(unsafe_callback),"register pending callback control");
    if(is("ordinary")){result=freak_fs_anchor_child_mode(10,"fresh",true,true,true,false,false);require(result==123 && !modules && !tokens && !descriptors,"ordinary creator unchanged");}
    else result=freak_fs_windows_owned_temp(10,"fresh",&retry);
    int accepted=is("success") || is("thread") || is("ordinary") || is("max-sid") || is("short-sid");
    require((result!=INVALID_HANDLE_VALUE)==accepted,"expected admission");
    if(result!=INVALID_HANDLE_VALUE)freak_fs_anchor_close(result);
    require(!modules && !tokens && !children && !descriptors && !defaults,"all owners balanced, token defaults untouched");
    if(is("thread"))require(!processes,"thread identity never falls back");
    if(is("thread-error"))require(!processes,"thread failure never falls back");
    require(retry==(is("collision")||is("file-collision")),"only collision retry");
    if(strstr(scenario,"owner-") || strstr(scenario,"cleanup-") || !strncmp(scenario,"descriptor-",11) || !strncmp(scenario,"acl-",4) || !strncmp(scenario,"ace-",4) || is("get-control") || is("get-ace") || is("attributes") || is("not-directory") || is("reparse") || is("not-disk"))require(disposed==1,"held new identity cleanup attempted");
    printf("TEMP_OWNER_OK %d %d %d %d %u\n",accepted,created,disposed,retry,error);return 0;
}
'''


def model(contents: str) -> str:
    begin=contents.index('typedef HANDLE freak_fs_anchor;')
    end=contents.index('static bool freak_fs_anchor_same(',begin)
    declarations=contents[begin:end]
    cleanup_begin=contents.index('/* Only a terminal FILE_CREATED response')
    cleanup_end=contents.index('\n#endif',cleanup_begin)
    aliases='typedef LONG (NTAPI *freak_fs_nt_set_fn)(HANDLE,freak_fs_nt_io *,PVOID,ULONG,ULONG);\n'
    nonfinal_begin=contents.index('static void freak_fs_sync_nonfinal(const char *operation) {')
    nonfinal_end=contents.index('static bool freak_fs_anchor_sync(',nonfinal_begin)
    return PREAMBLE+declarations+API+contents[nonfinal_begin:nonfinal_end]+aliases+contents[cleanup_begin:cleanup_end]+MAIN


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clang',default=os.environ.get('FREAK_CLANG','clang'))
    parser.add_argument('--sanitize',action='store_true')
    parser.add_argument('--windows-sdk',type=Path)
    parser.add_argument('--evidence',type=Path)
    parser.add_argument('--work-dir',type=Path)
    args=parser.parse_args()
    clang=shutil.which(args.clang);assert clang,args.clang
    before=INCLUDE.read_bytes();contents=before.decode()
    cases=['success','thread','ordinary','library','thread-error','process-error','size-small','size-large','size-error','size-success','user-error','user-length-small','user-length-large','sid-null','sid-before','sid-after','sid-short','sid-subauthorities','sid-truncated','sid-invalid','init','set-owner','create-error','collision','file-collision','create-informational','create-io-error','not-created','attributes','not-directory','reparse','not-disk','owner-query','owner-null','owner-invalid','owner-different','cleanup-error','cleanup-io-error','api-NtSetInformationFile']
    cases+=['max-sid','short-sid','sid-unaligned','init-acl','add-ace','set-dacl','set-control','get-control','get-ace','owner-before','owner-after','owner-short','owner-unaligned','owner-subauthorities','descriptor-null','descriptor-size-small','descriptor-size-large','descriptor-revision','descriptor-unprotected','descriptor-absolute','descriptor-no-dacl','acl-null','acl-before','acl-after','acl-short','acl-unaligned','acl-revision','acl-no-ace','acl-extra-ace','acl-small','acl-large','acl-invalid','ace-null','ace-before','ace-after','ace-short','ace-unaligned','ace-outside-but-valid','ace-type','ace-flags','ace-mask','ace-size-small','ace-size-large','ace-sid-invalid','ace-sid-subauthorities','ace-sid-truncated','ace-sid-different']
    cases+=['api-'+name for name in ('OpenProcessToken','OpenThreadToken','GetTokenInformation','InitializeSecurityDescriptor','SetSecurityDescriptorOwner','GetSecurityInfo','IsValidSid','EqualSid','NtCreateFile','InitializeAcl','AddAccessAllowedAceEx','SetSecurityDescriptorDacl','SetSecurityDescriptorControl','GetSecurityDescriptorLength','GetSecurityDescriptorControl','IsValidAcl','GetAce')]
    pending=['create-pending','create-io-pending','cleanup-pending','cleanup-io-pending']
    causal_errors={'sid-unaligned':1337,'init-acl':112,'add-ace':113,'set-dacl':114,'set-control':115,'get-control':116,'get-ace':117,
                   'owner-query':108,'owner-null':1307,'owner-invalid':1307,'owner-different':1307,
                   'owner-before':1307,'owner-after':1307,'owner-short':1307,'owner-unaligned':1307,'owner-subauthorities':1307,
                   'cleanup-error':1307,'cleanup-io-error':1307,'api-NtSetInformationFile':1307}
    causal_errors.update({case:1338 for case in cases if case.startswith('descriptor-')})
    causal_errors.update({case:1336 for case in cases if case.startswith(('acl-','ace-'))})
    causal_errors.update({case:127 for case in cases if case.startswith('api-') and case not in ('api-NtCreateFile','api-NtSetInformationFile')})
    records=[]
    flags=['-fsanitize=address,undefined','-fno-omit-frame-pointer'] if args.sanitize else []
    if args.work_dir:args.work_dir.mkdir(parents=True,exist_ok=False)
    with nullcontext(str(args.work_dir)) if args.work_dir else tempfile.TemporaryDirectory(prefix='freak-windows-temp-owner-') as temporary:
        home=Path(temporary);source=home/'model.c';source.write_text(model(contents));binary=home/('model.exe' if os.name=='nt' else 'model')
        built=subprocess.run([clang,'-O1','-Werror=implicit-function-declaration',*flags,str(source),'-o',str(binary)],capture_output=True,timeout=60)
        assert built.returncode==0,built.stderr.decode(errors='replace')
        for case in cases+pending:
            result=subprocess.run([str(binary),case],capture_output=True,timeout=15)
            if case in pending:
                assert result.returncode==1 and b'nonfinal synchronous directory owned temporary' in result.stderr and b'UNSAFE_CALLBACK' not in result.stderr,(case,result)
            else:
                assert result.returncode==0 and result.stdout.startswith(b'TEMP_OWNER_OK '),(case,result)
                if case in causal_errors:assert int(result.stdout.split()[-1])==causal_errors[case],(case,result)
            records.append({'scenario':case,'returncode':result.returncode,'stdout_hex':result.stdout.hex(),'stderr_hex':result.stderr.hex(),'status':'pass'})
        controls=[
            ('creation-sd','false,false,&descriptor);','false,false,NULL);','success'),
            ('read-control','if (security) access |= READ_CONTROL;','/* omitted */','success'),
            ('thread-error-fallback','if (error != ERROR_NO_TOKEN) goto cleanup;','/* ignored */','thread-error'),
            ('sid-bound','length > needed-(position-begin)','false','sid-truncated'),
            ('created-proof','io.information != 2 /* FILE_CREATED */','false','not-created'),
            ('owner-verification','!equal(actual,sid)','false','owner-different'),
            ('pending-lifetime','if (security && (status == 0x103 || (status == 0 && io.value.status == 0x103)))','if (false)','create-pending'),
            ('held-cleanup','status=set(child,&io,&dispose','status=set(10,&io,&dispose','owner-different'),
            ('private-dacl','!set_dacl(&descriptor,TRUE,private_acl,FALSE)','false','success'),
            ('protected-dacl','!set_control(&descriptor,SE_DACL_PROTECTED,SE_DACL_PROTECTED)','false','success'),
            ('held-protection','(control & (SE_SELF_RELATIVE | SE_DACL_PRESENT | SE_DACL_PROTECTED)) != (SE_SELF_RELATIVE | SE_DACL_PRESENT | SE_DACL_PROTECTED)','false','descriptor-unprotected'),
            ('held-acl-count','actual_acl->AceCount != 1','false','acl-extra-ace'),
            ('held-acl-range','!freak_fs_windows_temp_span(returned,returned_size,actual_acl,actual_acl->AclSize)','false','acl-large'),
            ('held-ace-range','return pointer && position >= begin && position-begin <= size && length <= size-(position-begin);','return pointer != NULL;','ace-outside-but-valid'),
            ('held-ace-type','allow->Header.AceType != ACCESS_ALLOWED_ACE_TYPE','false','ace-type'),
            ('held-ace-mask','allow->Mask != FILE_ALL_ACCESS','false','ace-mask'),
            ('held-ace-flags','allow->Header.AceFlags != (OBJECT_INHERIT_ACE | CONTAINER_INHERIT_ACE)','false','ace-flags'),
            ('held-ace-sid','!equal(granted,sid)','false','ace-sid-different'),
        ]
        for name,original,replacement,case in controls:
            assert contents.count(original)==1,(name,contents.count(original))
            broken=home/(name+'.c');broken.write_text(model(contents.replace(original,replacement,1)))
            executable=home/(name+('.exe' if os.name=='nt' else ''))
            compiled=subprocess.run([clang,'-O1','-Werror=implicit-function-declaration',*flags,str(broken),'-o',str(executable)],capture_output=True,timeout=60)
            assert compiled.returncode==0,(name,compiled.stderr)
            result=subprocess.run([str(executable),case],capture_output=True,timeout=15)
            expected_pending=case in pending and result.returncode==1 and b'nonfinal synchronous directory owned temporary' in result.stderr and b'UNSAFE_CALLBACK' not in result.stderr
            expected_regular=case not in pending and result.returncode==0 and result.stdout.startswith(b'TEMP_OWNER_OK ')
            assert not expected_pending and not expected_regular,(name,result)
            records.append({'scenario':'broken-'+name,'returncode':result.returncode,'stdout_hex':result.stdout.hex(),'stderr_hex':result.stderr.hex(),'status':'pass','scope':'required oracle rejected broken production decision'})
        model_sha=hashlib.sha256(source.read_bytes()).hexdigest()
        binary_sha=hashlib.sha256(binary.read_bytes()).hexdigest()
        if args.windows_sdk:
            runtime=ROOT/'freakc/runtime'
            result=subprocess.run([clang,'--target=x86_64-w64-windows-gnu',f'--sysroot={args.windows_sdk}','-fsyntax-only','-Werror=implicit-function-declaration',f'-I{runtime}',str(runtime/'freak_runtime.c'),str(runtime/'freak_llvm_runtime.c')],capture_output=True,timeout=60)
            assert result.returncode==0,result.stderr
            records.append({'scenario':'actual-windows-sdk-runtime-syntax','returncode':result.returncode,'stdout_hex':result.stdout.hex(),'stderr_hex':result.stderr.hex(),'status':'pass'})
    assert INCLUDE.read_bytes()==before,'source changed during verification'
    report={'status':'pass','scope':'production creation/owner/private-DACL helper with modeled native responses; SDK compile separate; actual native ownership/DACL requires bootstrap witness','retained_owner_model_oracles':'All 52 original responses remain, plus all 8 original broken controls; the owner-only SD control now requires the stronger private creation SD.','source_sha256':hashlib.sha256(before).hexdigest(),'test_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'model_sha256':model_sha,'model_binary_sha256':binary_sha,'clang':str(Path(clang).resolve()),'clang_sha256':hashlib.sha256(Path(clang).read_bytes()).hexdigest(),'cases':records}
    if args.evidence:args.evidence.parent.mkdir(parents=True,exist_ok=True);args.evidence.write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS Windows owned-temp {len(records)} modeled/native-compile controls')
    return 0

if __name__=='__main__':raise SystemExit(main())
