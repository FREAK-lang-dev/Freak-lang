#!/usr/bin/env python3
"""Check exact Windows publication diagnostics with controlled API responses.

Portable extracted C models and SDK compilation are not native Windows runs.
The existing ACL, publication, durability and ownership gates remain required.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
INCLUDE = ROOT / 'freakc/runtime/freak_v35_fs.inc'

TYPES = r'''
#include <wchar.h>
#define _WIN32 1
typedef intptr_t HANDLE,HMODULE,freak_fs_anchor;
typedef HANDLE *PHANDLE;
typedef void *LPVOID;
typedef DWORD *PDWORD;
typedef unsigned char BYTE;
#undef NULL
#define NULL 0
#define TRUE 1
typedef void (*FARPROC)(void);
typedef void *PSECURITY_DESCRIPTOR;
typedef int TOKEN_INFORMATION_CLASS,SE_OBJECT_TYPE,SECURITY_INFORMATION,WELL_KNOWN_SID_TYPE;
typedef struct {struct {PSID Sid;} User;} TOKEN_USER;
typedef struct {uint64_t VolumeSerialNumber;struct {unsigned char Identifier[16];} FileId;} FILE_ID_INFO;
typedef struct {bool ok,completed;HANDLE directory;char error[256];} freak_fs_ticket;
typedef const char *freak_word;
#define INVALID_HANDLE_VALUE ((HANDLE)-1)
#define FREAK_FS_INVALID_ANCHOR INVALID_HANDLE_VALUE
#define ERROR_SUCCESS 0
#define ERROR_ACCESS_DENIED 5
#define ERROR_NO_TOKEN 1008
#define TOKEN_QUERY 8
#define TokenUser 1
#define SE_FILE_OBJECT 1
#define OWNER_SECURITY_INFORMATION 1
#define DACL_SECURITY_INFORMATION 4
#define WinLocalSystemSid 22
#define WinBuiltinAdministratorsSid 26
#define SECURITY_MAX_SID_SIZE 68
#define READ_CONTROL 0x20000u
#define FILE_READ_ATTRIBUTES 0x80u
#define SYNCHRONIZE 0x100000u
#define FILE_SHARE_READ 1
#define FILE_SHARE_WRITE 2
#define FILE_SHARE_DELETE 4
#define FILE_FLAG_BACKUP_SEMANTICS 0x02000000u
#define LOAD_LIBRARY_SEARCH_SYSTEM32 0x800u
#define FileIdInfo 18
static DWORD GetLastError(void);
static void SetLastError(DWORD);
static HANDLE GetCurrentProcess(void),GetCurrentThread(void);
static HANDLE ReOpenFile(HANDLE,DWORD,DWORD,DWORD);
static BOOL GetFileInformationByHandleEx(HANDLE,int,void *,DWORD);
static void freak_fs_anchor_close(HANDLE);
static bool freak_fs_anchor_same(HANDLE,HANDLE);
static HMODULE LoadLibraryExW(const wchar_t *,HANDLE,DWORD);
static FARPROC GetProcAddress(HMODULE,const char *);
static BOOL CloseHandle(HANDLE),FreeLibrary(HMODULE);
static void *LocalFree(void *);
static void *freak_command_allocate(size_t,size_t);
static void freak_fs_ticket_error(freak_fs_ticket *,const char *);
'''

API = r'''
static const char *scenario;static int target,current_side,loads[2],acquisitions[2],file_opens,renames,syncs;
static int module_live,reopened_live,token_live,descriptor_live;
static DWORD last_error;static char trace[16384];static size_t trace_used;
static SID caller,foreign,invalid,system_sid,admin_sid,everyone;static PACL effective_acl;
static void event(const char *name,int side) {int n=snprintf(trace+trace_used,sizeof(trace)-trace_used,"%s:%d,",name,side);require(n>=0 && (size_t)n<sizeof(trace)-trace_used,"trace bounds");trace_used+=(size_t)n;}
static bool fault(const char *name,int side) {return side==target && !strcmp(scenario,name);}
static DWORD GetLastError(void) {return last_error;}
static void SetLastError(DWORD error) {last_error=error;}
static HANDLE GetCurrentProcess(void) {return -2;}
static HANDLE GetCurrentThread(void) {return -3;}
static BOOL CloseHandle(HANDLE handle) {event("close",(int)handle);if(handle>=100 && handle<200)reopened_live--;if(handle>=200 && handle<300)token_live--;require(reopened_live>=0 && token_live>=0,"no duplicate native close");last_error=777;return 1;}
static void freak_fs_anchor_close(HANDLE handle) {DWORD saved=GetLastError();if(handle!=INVALID_HANDLE_VALUE)CloseHandle(handle);SetLastError(saved);}
static BOOL FreeLibrary(HMODULE module) {event("free-library",(int)module);require(module_live>0,"loaded library ownership");module_live--;last_error=778;return 1;}
static void *LocalFree(void *memory) {event("free-descriptor",current_side);require(memory && descriptor_live>0,"descriptor ownership");descriptor_live--;free(memory);last_error=779;return NULL;}
static void *freak_command_allocate(size_t count,size_t size) {void *p=calloc(count,size);require(p!=NULL,"allocation");return p;}
static void freak_fs_ticket_error(freak_fs_ticket *ticket,const char *reason) {ticket->ok=false;snprintf(ticket->error,sizeof(ticket->error),"%s",reason);}
static HMODULE LoadLibraryExW(const wchar_t *name,HANDLE unused,DWORD flags) {
    (void)name;(void)unused;require(flags==LOAD_LIBRARY_SEARCH_SYSTEM32,"security library scope");current_side=loads[0]?20:10;loads[current_side==20]++;event("load-library",current_side);
    if(fault("security-library",current_side)){last_error=101;return 0;}
    effective_acl=reset();caller=make_sid(1000);foreign=make_sid(1001);invalid=caller;invalid.Revision=2;system_sid=make_sid(18);admin_sid=make_sid(544);everyone=make_sid(0);
    if(fault("acl-write",current_side))append(effective_acl,ACCESS_ALLOWED_ACE_TYPE,0,GENERIC_WRITE,&everyone);
    if(fault("acl-unsupported",current_side))append(effective_acl,9,0,0,&caller);
    module_live++;return current_side+50;
}
static HANDLE ReOpenFile(HANDLE directory,DWORD access,DWORD share,DWORD flags) {
    event("reopen",(int)directory);require(access==(READ_CONTROL|FILE_READ_ATTRIBUTES|SYNCHRONIZE) && share==7 && flags==FILE_FLAG_BACKUP_SEMANTICS,"held minimum access");
    if(fault("read-control-reopen",(int)directory)){last_error=102;return INVALID_HANDLE_VALUE;}reopened_live++;return directory+100;
}
static BOOL GetFileInformationByHandleEx(HANDLE handle,int info,void *buffer,DWORD size) {
    event("identity",(int)handle);require(info==FileIdInfo && size==sizeof(FILE_ID_INFO),"full identity query");
    int side=handle>=100 ? (int)handle-100 : (int)handle;
    if(fault("held-identity",side) && handle<100){last_error=103;return 0;}
    if(fault("reopened-identity",side) && handle>=100){last_error=104;return 0;}
    FILE_ID_INFO *id=buffer;memset(id,0,sizeof(*id));id->VolumeSerialNumber=42;id->FileId.Identifier[0]=(unsigned char)(handle==30 || handle==40 ? 30 : side);
    if(fault("identity-mismatch",side) && handle>=100)id->FileId.Identifier[15]=1;
    return 1;
}
static bool freak_fs_anchor_same(HANDLE first,HANDLE second) {FILE_ID_INFO a,b;return GetFileInformationByHandleEx(first,FileIdInfo,&a,sizeof(a)) && GetFileInformationByHandleEx(second,FileIdInfo,&b,sizeof(b)) && a.VolumeSerialNumber==b.VolumeSerialNumber && !memcmp(a.FileId.Identifier,b.FileId.Identifier,sizeof(a.FileId.Identifier));}
static BOOL open_thread(HANDLE thread,DWORD access,BOOL itself,HANDLE *token) {
    (void)thread;(void)access;(void)itself;event("thread-token",current_side);
    if(fault("thread-token",current_side)){last_error=105;return 0;}
    if(fault("thread-present",current_side)){token_live++;*token=current_side+200;return 1;}
    last_error=ERROR_NO_TOKEN;return 0;
}
static BOOL open_process(HANDLE process,DWORD access,HANDLE *token) {(void)process;(void)access;event("process-token",current_side);if(fault("process-token",current_side)){last_error=106;return 0;}token_live++;*token=current_side+200;return 1;}
static BOOL token_info(HANDLE token,TOKEN_INFORMATION_CLASS info,void *buffer,DWORD size,DWORD *needed) {
    (void)token;(void)info;(void)size;event(buffer?"token-user":"token-size",current_side);
    if(!buffer){*needed=(DWORD)sizeof(TOKEN_USER);last_error=122;if(fault("token-size-failed",current_side)){*needed=0;last_error=107;return 0;}if(fault("token-size-success-invalid",current_side)){*needed=0;last_error=909;return 1;}return 0;}
    if(fault("token-user",current_side)){last_error=108;return 0;}((TOKEN_USER *)buffer)->User.Sid=fault("caller-null",current_side)?NULL:&caller;return 1;
}
static DWORD security_info(HANDLE handle,SE_OBJECT_TYPE type,SECURITY_INFORMATION requested,PSID *owner,PSID *group,PACL *acl,PACL *sacl,PSECURITY_DESCRIPTOR *descriptor) {
    (void)handle;(void)type;(void)requested;(void)group;(void)sacl;event("security-info",current_side);
    if(fault("security-info",current_side)){last_error=909;return 109;}
    *owner=fault("owner-null",current_side)?NULL:fault("owner-invalid",current_side)?&invalid:fault("owner-different",current_side)?&foreign:&caller;
    *acl=fault("acl-null",current_side)?NULL:effective_acl;*descriptor=malloc(1);require(*descriptor!=NULL,"descriptor allocation");descriptor_live++;return 0;
}
static BOOL well_known(WELL_KNOWN_SID_TYPE type,PSID domain,PSID sid,DWORD *size) {
    (void)domain;(void)size;event(type==WinLocalSystemSid?"system-sid":"administrators-sid",current_side);
    if(fault(type==WinLocalSystemSid?"system-sid":"administrators-sid",current_side)){last_error=type==WinLocalSystemSid?110:111;return 0;}
    memcpy(sid,type==WinLocalSystemSid?&system_sid:&admin_sid,sizeof(SID));return 1;
}
static BOOL api_valid_sid(PSID sid) {event("valid-sid",current_side);return valid_sid(sid);}
static BOOL api_equal_sid(PSID a,PSID b) {event("equal-sid",current_side);require(a && b && valid_sid(a) && valid_sid(b),"no unsafe SID comparison");return equal_sid(a,b);}
static BOOL api_valid_acl(PACL acl) {event("valid-acl",current_side);return valid_acl(acl);}
static BOOL api_get_ace(PACL acl,DWORD index,PVOID *value) {event("get-ace",current_side);return get_ace(acl,index,value);}
static FARPROC GetProcAddress(HMODULE module,const char *name) {
    (void)module;event(name,current_side);char missing[64];snprintf(missing,sizeof(missing),"api-%s",name);
    if(fault(missing,current_side)){last_error=112;return NULL;}
    last_error=909;
    if(!strcmp(name,"OpenProcessToken"))return (FARPROC)open_process;
    if(!strcmp(name,"OpenThreadToken"))return (FARPROC)open_thread;
    if(!strcmp(name,"GetTokenInformation"))return (FARPROC)token_info;
    if(!strcmp(name,"GetSecurityInfo"))return (FARPROC)security_info;
    if(!strcmp(name,"CreateWellKnownSid"))return (FARPROC)well_known;
    if(!strcmp(name,"IsValidAcl"))return (FARPROC)api_valid_acl;
    if(!strcmp(name,"GetAce"))return (FARPROC)api_get_ace;
    if(!strcmp(name,"IsValidSid"))return (FARPROC)api_valid_sid;
    if(!strcmp(name,"EqualSid"))return (FARPROC)api_equal_sid;
    require(0,"unknown security API");return NULL;
}
'''

FILESYSTEM = r'''
static freak_fs_ticket tickets[3];
static int64_t freak_fs_ticket_new(void) {memset(&tickets[2],0,sizeof(tickets[2]));return 3;}
static freak_fs_ticket *freak_fs_ticket_require(int64_t handle) {require(handle>=1 && handle<=3,"ticket bounds");return &tickets[handle-1];}
static freak_fs_ticket *freak_fs_directory_require(int64_t handle) {return freak_fs_ticket_require(handle);}
static char *freak_fs_checked_path(freak_fs_ticket *ticket,freak_word word) {(void)ticket;size_t n=strlen(word)+1;char *copy=malloc(n);require(copy!=NULL,"path allocation");memcpy(copy,word,n);return copy;}
static bool freak_fs_relative_valid(const char *name,bool single) {(void)single;return name && *name;}
static HANDLE freak_fs_anchor_parent(freak_fs_ticket *root,char *relative,char **leaf) {int side=(int)root->directory;acquisitions[side==20]++;event("acquire-parent",side);*leaf=relative;if(fault("parent-acquisition",side)){last_error=113;return INVALID_HANDLE_VALUE;}return side;}
static HANDLE freak_fs_anchor_child(HANDLE parent,const char *name,bool directory,bool create,bool writable) {(void)parent;(void)name;require(!directory && !create,"ordinary publication file");event("file-open",writable?30:40);file_opens++;return writable?30:40;}
static BOOL FlushFileBuffers(HANDLE file) {event("flush-file",(int)file);return 1;}
static bool freak_fs_anchor_rename_handle(HANDLE file,HANDLE destination,const char *name,bool replace) {(void)file;(void)destination;(void)name;require(!replace,"no replacement");event("rename",20);renames++;return true;}
static bool freak_fs_anchor_sync(HANDLE parent) {event("sync",(int)parent);syncs++;return true;}
'''

MAIN = r'''
int main(int argc,char **argv) {
    require(argc>=3,"arguments");scenario=argv[1];target=!strcmp(argv[2],"destination")?20:10;
    tickets[0].directory=10;tickets[1].directory=20;
    if(argc==4){
        freak_fs_windows_parent_diagnostic diagnostic={NULL,0,-1};
        bool accepted=freak_fs_windows_parent_private(10,!strcmp(argv[3],"null")?NULL:&diagnostic);
        require(!module_live && !reopened_live && !token_live && !descriptor_live,"all helper native owners released");
        printf("%d|%s|%lu|%d\n%s\n",accepted,diagnostic.phase?diagnostic.phase:"not-examined",(unsigned long)diagnostic.native_error,diagnostic.owner_match,trace);
        return 0;
    }
    int64_t result=freak_fs_rename_relative_new_checked(1,"module.ll",2,"emitted.ll");
    require(!module_live && !reopened_live && !token_live && !descriptor_live,"all publication native owners released");
    bool accepted=!strcmp(scenario,"success") || !strcmp(scenario,"thread-present");
    require(tickets[result-1].ok==accepted && tickets[result-1].completed==accepted,"unchanged publication outcome");
    require(acquisitions[0]==1 && acquisitions[1]==1,"both parent acquisitions retained");
    if(accepted){require(file_opens==2 && renames==1 && syncs==2 && loads[0]==1 && loads[1]==1,"success publication trace");}
    else {
        require(!file_opens && !renames && !syncs,"rejected guard precedes mutation");
        if(!strcmp(scenario,"parent-acquisition"))require(!loads[0] && !loads[1],"invalid acquisition skips both private checks");
        else if(target==10)require(loads[0]==1 && !loads[1],"source rejection skips destination");
        else require(loads[0]==1 && loads[1]==1,"destination examined after source passes");
    }
    printf("%d|%s\n%s\n",accepted,tickets[result-1].error,trace);return 0;
}
'''


def models(contents: str) -> str:
    spec = importlib.util.spec_from_file_location('windows_fs_existing', ROOT/'tests/v3_v35_windows_fs.py')
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    policy = module.POLICY_HARNESS
    preamble, support = policy.split('PRODUCTION_POLICY', 1)
    support = support[:support.index('int main(void)')]
    declaration = contents[contents.index('typedef struct {\n    const char *phase;'):contents.index('/* FREAK_WINDOWS_DIRECTORY_SYNC_BEGIN')]
    policy_begin = contents.index('typedef BOOL', contents.index('FREAK_WINDOWS_ACL_POLICY_BEGIN'))
    policy_end = contents.index('/* FREAK_WINDOWS_ACL_POLICY_END */')
    helper_begin = contents.index('static FARPROC freak_fs_windows_security_proc(')
    helper_end = contents.index('static int freak_fs_anchor_file_descriptor(', helper_begin)
    rename_begin = contents.index('int64_t freak_fs_rename_relative_new_checked(')
    rename_end = contents.index('int64_t freak_fs_set_mode_relative_checked(', rename_begin)
    return preamble + TYPES + declaration + contents[policy_begin:policy_end] + support + API + contents[helper_begin:helper_end] + FILESYSTEM + contents[rename_begin:rename_end] + MAIN


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clang', default=os.environ.get('FREAK_CLANG', 'clang'))
    parser.add_argument('--windows-sdk', type=Path)
    parser.add_argument('--sanitize', action='store_true')
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    clang = shutil.which(args.clang)
    assert clang, args.clang
    contents = INCLUDE.read_text()
    scenarios = {
        'security-library': ('security-library', 101, -1),
        **{'api-'+name: ('api-'+name, 112, -1) for name in ('OpenProcessToken','OpenThreadToken','GetTokenInformation','GetSecurityInfo','CreateWellKnownSid','IsValidAcl','GetAce','IsValidSid','EqualSid')},
        'read-control-reopen': ('read-control-reopen',102,-1),
        'held-identity': ('held-identity',103,-1),
        'reopened-identity': ('reopened-identity',104,-1),
        'identity-mismatch': ('identity-mismatch',0,-1),
        'thread-token': ('thread-token',105,-1),
        'process-token': ('process-token',106,-1),
        'token-size-failed': ('token-user-size',107,-1),
        'token-size-success-invalid': ('token-user-size',0,-1),
        'token-user': ('token-user',108,-1),
        'security-info': ('security-info',109,-1),
        'system-sid': ('system-sid',110,-1),
        'administrators-sid': ('administrators-sid',111,-1),
        'owner-different': ('acl-policy',0,0),
        'owner-null': ('acl-policy',0,-1),
        'owner-invalid': ('acl-policy',0,-1),
        'caller-null': ('acl-policy',0,-1),
        'acl-null': ('acl-policy',0,1),
        'acl-write': ('acl-policy',0,1),
        'acl-unsupported': ('acl-policy',0,1),
        'parent-acquisition': ('parent-acquisition',113,-1),
    }
    records = []
    commands = []
    environment = {**os.environ,'ASAN_OPTIONS':'detect_leaks=1:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1'}
    home_context = tempfile.TemporaryDirectory(prefix='freak-publication-diagnostic-') if not args.evidence else None
    home = Path(home_context.name) if home_context else args.evidence
    assert home is not None
    home.mkdir(parents=True, exist_ok=True)
    def run(label: str, command: list[str], *, expected: int = 0) -> subprocess.CompletedProcess:
        result = subprocess.run(command, cwd=home, env=environment, capture_output=True, timeout=60)
        (home/(label+'.stdout')).write_bytes(result.stdout)
        (home/(label+'.stderr')).write_bytes(result.stderr)
        commands.append({'label':label,'command':command,'returncode':result.returncode,'stdout_sha256':hashlib.sha256(result.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(result.stderr).hexdigest()})
        assert result.returncode == expected, (label,result.stdout,result.stderr)
        return result
    source = home/'publication-model.c'
    source.write_text(models(contents))
    binary = home/'publication-model'
    flags = ['-fsanitize=address,undefined','-fno-omit-frame-pointer'] if args.sanitize else []
    run('model-build',[clang,'-O2','-g','-Werror=implicit-function-declaration','-Werror=incompatible-pointer-types','-Werror=int-conversion','-Werror=return-type',*flags,str(source),'-o',str(binary)])
    for scenario, (phase,error,owner) in scenarios.items():
        for side in ('source','destination'):
            result = run(scenario+'-'+side,[str(binary),scenario,side])
            assert not result.stderr, result.stderr
            owner_text = 'unknown' if owner < 0 else 'same' if owner else 'different'
            suffix=f'{side}={phase},error={error},owner={owner_text}'
            assert suffix.encode() in result.stdout, result.stdout
            assert result.stdout.startswith(b'0|file publication requires safe owned destination and source parents ')
            if side=='source' and scenario!='parent-acquisition':
                assert b'destination=not-examined,error=0,owner=unknown' in result.stdout
            if side=='destination' and scenario!='parent-acquisition':
                assert b'source=passed,error=0,owner=same' in result.stdout
            assert len(result.stdout.splitlines()[0][2:]) < 256
            records.append({'scenario':scenario,'side':side,'phase':phase,'error':error,'owner_match':owner,'status':'pass'})
    for scenario in ('success','thread-present'):
        result = run(scenario,[str(binary),scenario,'source'])
        assert result.stdout.startswith(b'1|\n') and not result.stderr
        with_record = run(scenario+'-helper-record',[str(binary),scenario,'source','record'])
        without_record = run(scenario+'-helper-null',[str(binary),scenario,'source','null'])
        assert with_record.stdout.splitlines()[1:] == without_record.stdout.splitlines()[1:]
        assert with_record.stdout.startswith(b'1|passed|0|1\n') and without_record.stdout.startswith(b'1|not-examined|0|-1\n')
        records.append({'scenario':scenario,'success_API_trace_exact_with_or_without_diagnostic':True,'status':'pass'})
    # A cleanup-contaminated error or evaluation of an unexamined parent must fail.
    negative_controls = []
    for label, original, weakened, scenario in (
        ('stale-security-return','"security-info",security_error','"security-info",GetLastError()','security-info'),
        ('stale-logical-size','diagnostic && !sized ? GetLastError() : 0','diagnostic ? GetLastError() : 0','token-size-success-invalid'),
        ('destination-after-source-reject','private_parents && freak_fs_windows_parent_private(source_parent,&source_diagnostic) &&','private_parents && (freak_fs_windows_parent_private(source_parent,&source_diagnostic),true) &&','read-control-reopen'),
    ):
        mutated = source.read_text().replace(original,weakened)
        assert mutated != source.read_text()
        broken = home/(label+'.c');broken.write_text(mutated)
        bad = home/(label+'.model')
        run(label+'-build',[clang,'-O2',*flags,str(broken),'-o',str(bad)])
        result = subprocess.run([str(bad),scenario,'source'],cwd=home,env=environment,capture_output=True,timeout=15)
        (home/(label+'.stdout')).write_bytes(result.stdout);(home/(label+'.stderr')).write_bytes(result.stderr)
        expected = scenarios[scenario]
        oracle = f'source={expected[0]},error={expected[1]}'.encode()
        assert result.returncode != 0 or oracle not in result.stdout or b'destination=not-examined,error=0,owner=unknown' not in result.stdout
        negative_controls.append({'control':label,'status':'rejected','returncode':result.returncode})
    if args.windows_sdk:
        sdk = args.windows_sdk.resolve(strict=True)
        runtime = ROOT/'freakc/runtime'
        strict=['-Werror=implicit-function-declaration','-Werror=incompatible-pointer-types','-Werror=int-conversion','-Werror=return-type']
        run('GNU-runtime-syntax',[clang,'--target=x86_64-w64-windows-gnu','--sysroot='+str(sdk),*strict,'-fsyntax-only','-I'+str(runtime),str(runtime/'freak_runtime.c'),str(runtime/'freak_llvm_runtime.c')])
        run('GNU-runtime-object',[clang,'--target=x86_64-w64-windows-gnu','--sysroot='+str(sdk),*strict,'-O2','-c','-I'+str(runtime),str(runtime/'freak_runtime.c'),'-o',str(home/'runtime.obj')])
    report={'status':'pass','runtime_include_sha256':hashlib.sha256(INCLUDE.read_bytes()).hexdigest(),'test_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'cases':records,'negative_controls':negative_controls,'commands':commands,'native_Windows_execution':False,'scope':'Exact extracted helper/publication C with modeled Windows APIs; success API trace, failure phase/error before poisoned cleanup, source/destination order, safe owner observation and bounded prefix. SDK checks are compilation only.'}
    (home/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS Windows publication diagnostic: {len(records)} modeled controls, {len(negative_controls)} broken controls rejected',flush=True)
    if home_context:home_context.cleanup()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
