#!/usr/bin/env python3
"""Check Windows publication ACL policy and prepare real native durability gates.

Portable runs execute the exact production ACL decision with synthetic ACL
layout fixtures. They prove policy/bounds logic, not Windows OS semantics.
Native Windows runs additionally use real owner/DACL queries and checked flushes.
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

WINDOWS_HARNESS = r'''
#include "freak_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>
#include <aclapi.h>
extern int64_t freak_llvm_fs_rename_relative_new_checked(int64_t,int64_t,int64_t,int64_t);
static const char *scenario="";static int directory_flushes=0;
static void require(int ok,const char *why) {if(!ok) {fprintf(stderr,"FAIL: %s (Win32 %lu)\n",why,GetLastError());exit(2);}}
#ifdef USE_LLVM_ADAPTER
#define W(s) ((int64_t)(intptr_t)(s))
#define F(n) freak_llvm_fs_##n
#else
#define W(s) freak_word_lit(s)
#define F(n) freak_fs_##n
#endif
BOOL WINAPI freak_test_flush_buffers(HANDLE file) {
    BY_HANDLE_FILE_INFORMATION info;require(GetFileInformationByHandle(file,&info),"flush handle information");
    if(info.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) {
        directory_flushes++;
        if(!strcmp(scenario,"directory-fault") && directory_flushes==1) {SetLastError(ERROR_IO_DEVICE);return FALSE;}
    }
    return FlushFileBuffers(file);
}
FARPROC WINAPI freak_test_get_proc_address(HMODULE module,LPCSTR name) {
    if(!strcmp(scenario,"missing-security-api") && !strcmp(name,"GetSecurityInfo")) return NULL;
    return GetProcAddress(module,name);
}
static void private_acl(const char *name,int policy) {
    HANDLE token=NULL;require(OpenProcessToken(GetCurrentProcess(),TOKEN_QUERY,&token),"token query");DWORD count=0;
    GetTokenInformation(token,TokenUser,NULL,0,&count);TOKEN_USER *user=malloc(count);require(user!=NULL && GetTokenInformation(token,TokenUser,user,count,&count),"user SID");
    union {DWORD aligned;BYTE bytes[SECURITY_MAX_SID_SIZE];} everyone;DWORD size=sizeof everyone.bytes;
    require(CreateWellKnownSid(WinWorldSid,NULL,everyone.bytes,&size),"everyone SID");
    EXPLICIT_ACCESSW grants[2]={0};grants[0].grfAccessPermissions=FILE_ALL_ACCESS;grants[0].grfAccessMode=SET_ACCESS;
    grants[0].Trustee.TrusteeForm=TRUSTEE_IS_SID;grants[0].Trustee.ptstrName=user->User.Sid;
    grants[1].grfAccessPermissions=policy==1 ? FILE_GENERIC_READ | FILE_GENERIC_EXECUTE : policy==2 ? FILE_ADD_FILE : policy==3 ? WRITE_DAC : FILE_DELETE_CHILD;
    grants[1].grfAccessMode=SET_ACCESS;grants[1].Trustee.TrusteeForm=TRUSTEE_IS_SID;grants[1].Trustee.ptstrName=everyone.bytes;
    PACL acl=NULL;require(SetEntriesInAclW(policy ? 2 : 1,grants,NULL,&acl)==ERROR_SUCCESS,"construct private ACL");
    int characters=MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,name,-1,NULL,0);wchar_t *wide=malloc((size_t)characters*sizeof(wchar_t));
    require(wide && MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,name,-1,wide,characters)==characters,"path UTF8");
    DWORD status=SetNamedSecurityInfoW(wide,SE_FILE_OBJECT,OWNER_SECURITY_INFORMATION | DACL_SECURITY_INFORMATION | PROTECTED_DACL_SECURITY_INFORMATION,
        user->User.Sid,NULL,policy==5 ? NULL : acl,NULL);
    require(status==ERROR_SUCCESS,"set real owner/private DACL");LocalFree(acl);free(wide);free(user);CloseHandle(token);
}
int main(int argc,char **argv) {
    require(argc==4,"arguments");scenario=argv[3];
    int source_policy=!strcmp(scenario,"source-write") ? 2 : !strcmp(scenario,"null-dacl") ? 5 : 0;
    int destination_policy=!strcmp(scenario,"readonly-others") ? 1 : !strcmp(scenario,"destination-write") ? 2 : !strcmp(scenario,"write-dac") ? 3 : !strcmp(scenario,"delete-child") ? 4 : 0;
    private_acl(argv[1],source_policy);private_acl(argv[2],destination_policy);
    DWORD before=0,after=0;require(GetProcessHandleCount(GetCurrentProcess(),&before),"handle baseline");
    int64_t source=F(open_dir_ticket)(W(argv[1])),destination=F(open_dir_ticket)(W(argv[2]));require(F(result_ok)(source) && F(result_ok)(destination),"root admission");
    int64_t publication=F(rename_relative_new_checked)(source,W("a"),destination,W("result"));
    int accepted=!strcmp(scenario,"native") || !strcmp(scenario,"readonly-others");int completed=accepted || !strcmp(scenario,"directory-fault");
    require(!!F(result_completed)(publication)==completed,"publication completed classification");
    require(!!F(result_ok)(publication)==accepted,"native checked directory durability/ACL classification");
    if(completed) require(directory_flushes==2,"both held parent flushes attempted");
    F(result_release)(publication);F(result_release)(source);F(result_release)(destination);
    require(freak_fs_result_live()==0,"result ownership");require(GetProcessHandleCount(GetCurrentProcess(),&after) && before==after,"handle ownership");
    printf("WINDOWS_OK %d\n",directory_flushes);return 0;
}
'''

WINDOWS_RUNTIME_WRAPPER = '''#include <winsock2.h>
#include <windows.h>
BOOL WINAPI freak_test_flush_buffers(HANDLE);
FARPROC WINAPI freak_test_get_proc_address(HMODULE,LPCSTR);
#define FlushFileBuffers freak_test_flush_buffers
#define GetProcAddress freak_test_get_proc_address
#include "freak_runtime.c"
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
    hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in [include, runtime/'freak_runtime.c', runtime/'freak_runtime.h', runtime/'freak_llvm_runtime.c']}
    records = []
    report = {'runtime_sha256': hashes, 'cases': records, 'native_windows_verified': os.name == 'nt',
              'portable_scope': 'exact ACL policy with synthetic native-layout fixtures; not Windows syscall behavior',
              'native_windows_scope': 'real caller ownership, private/readonly/nonowner-write/null DACLs, real directory flush and first-flush fault'}
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
            assert '__imp_ReOpenFile' in symbols and not any(s.endswith(n) for s in symbols for n in security_names), symbols
            report['windows_sdk_object'] = {'command': command, 'status': 'pass', 'sha256': hashlib.sha256(object_path.read_bytes()).hexdigest(), 'undefined_symbols': symbols, 'no_new_security_library_imports': True, 'native_execution': False}
        if os.name == 'nt':
            for adapter in ('c', 'llvm'):
                for optimization in args.optimization or (0, 2, 3):
                    binary = home/f'{adapter}-{optimization}.exe'
                    command = [clang, str(harness), str(wrapper), f'-I{runtime}', f'-O{optimization}', *flags, '-lws2_32', '-lshell32', '-ladvapi32', '-o', str(binary)]
                    if adapter == 'llvm':command += ['-DUSE_LLVM_ADAPTER=1', str(runtime/'freak_llvm_runtime.c')]
                    built = subprocess.run(command, capture_output=True, timeout=90);assert built.returncode == 0, built.stderr
                    for name in ('native', 'readonly-others', 'source-write', 'destination-write', 'write-dac', 'delete-child', 'null-dacl', 'missing-security-api', 'directory-fault'):
                        case = home/f'{adapter}-{optimization}-{name}';case.mkdir();source_root, destination = case/'source', case/'destination'
                        source_root.mkdir();destination.mkdir();(source_root/'a').write_bytes(b'published\0\xff');(destination/'neighbor').write_bytes(b'unchanged')
                        result = subprocess.run([str(binary), str(source_root), str(destination), name], env=environment, capture_output=True, timeout=15)
                        assert result.returncode == 0 and not result.stderr, (adapter, optimization, name, result)
                        moved = name in ('native', 'readonly-others', 'directory-fault')
                        assert (destination/'neighbor').read_bytes() == b'unchanged'
                        assert not (source_root/'a').exists() if moved else (source_root/'a').read_bytes() == b'published\0\xff'
                        assert (destination/'result').read_bytes() == b'published\0\xff' if moved else not (destination/'result').exists()
                        records.append({'adapter': adapter, 'optimization': optimization, 'case': 'native-windows-'+name, 'status': 'pass'})
    assert hashes == {str(path): hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in hashes}, 'runtime changed during verification'
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True);args.report.write_text(json.dumps(report, indent=2)+'\n')
    return 0


if __name__ == '__main__':raise SystemExit(main())
