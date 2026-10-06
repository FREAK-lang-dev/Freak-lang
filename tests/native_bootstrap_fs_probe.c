/* Observational checked-FS probe. Every hook forwards the real OS operation;
   a failed production contract is reported as false, never made successful. */
#ifdef _WIN32
#ifndef _WIN32_WINNT
#define _WIN32_WINNT 0x0602
#endif
#elif defined(__APPLE__)
#define _DARWIN_C_SOURCE 1
#define _POSIX_C_SOURCE 200809L
#else
#define _POSIX_C_SOURCE 200809L
#endif
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <inttypes.h>
#include <string.h>
#ifdef _WIN32
#include <winsock2.h>
#include <windows.h>

typedef struct {
    const char *api, *phase;
    uint64_t handle, other, access, flags, share, disposition, options;
    int64_t result, io_status;
    uint64_t io_information, volume;
    DWORD error, attributes;
    unsigned char identity[16];
    int has_identity, has_io;
} probe_event;
static probe_event probe_events[512];
static size_t probe_event_count;
static int probe_overflow;
static const char *probe_phase = "startup";
static probe_event *probe_record(const char *api, int64_t result, DWORD error, HANDLE handle) {
    if (probe_event_count == sizeof(probe_events) / sizeof(*probe_events)) {
        probe_overflow = 1; return NULL;
    }
    probe_event *event = &probe_events[probe_event_count++];
    event->api = api; event->phase = probe_phase; event->result = result;
    event->error = error; event->handle = (uintptr_t)handle;
    return event;
}
static HANDLE WINAPI probe_create(LPCWSTR name, DWORD access, DWORD share,
        LPSECURITY_ATTRIBUTES security, DWORD disposition, DWORD flags, HANDLE template_file) {
    HANDLE result = CreateFileW(name, access, share, security, disposition, flags, template_file);
    DWORD error = GetLastError();
    probe_event *event = probe_record("CreateFileW", result != INVALID_HANDLE_VALUE, error, result);
    if (event) { event->access = access; event->share = share;
        event->disposition = disposition; event->flags = flags; }
    SetLastError(error); return result;
}
static HANDLE WINAPI probe_reopen(HANDLE original, DWORD access, DWORD share, DWORD flags) {
    HANDLE result = ReOpenFile(original, access, share, flags);
    DWORD error = GetLastError();
    probe_event *event = probe_record("ReOpenFile", result != INVALID_HANDLE_VALUE, error, original);
    if (event) { event->other = (uintptr_t)result; event->access = access;
        event->share = share; event->flags = flags; }
    SetLastError(error); return result;
}
static BOOL WINAPI probe_flush(HANDLE handle) {
    BOOL result = FlushFileBuffers(handle); DWORD error = GetLastError();
    probe_record("FlushFileBuffers", result, error, handle);
    SetLastError(error); return result;
}
static BOOL WINAPI probe_information(HANDLE handle, LPBY_HANDLE_FILE_INFORMATION information) {
    BOOL result = GetFileInformationByHandle(handle, information); DWORD error = GetLastError();
    probe_event *event = probe_record("GetFileInformationByHandle", result, error, handle);
    if (event && result) event->attributes = information->dwFileAttributes;
    SetLastError(error); return result;
}
static BOOL WINAPI probe_information_ex(HANDLE handle, FILE_INFO_BY_HANDLE_CLASS kind,
                                        LPVOID information, DWORD length) {
    BOOL result = GetFileInformationByHandleEx(handle, kind, information, length);
    DWORD error = GetLastError();
    probe_event *event = probe_record("GetFileInformationByHandleEx", result, error, handle);
    if (event) {
        event->flags = kind;
        if (result && kind == FileIdInfo && length >= sizeof(FILE_ID_INFO)) {
            FILE_ID_INFO *id = information; event->volume = id->VolumeSerialNumber;
            memcpy(event->identity, id->FileId.Identifier, sizeof(event->identity));
            event->has_identity = 1;
        }
    }
    SetLastError(error); return result;
}
static DWORD WINAPI probe_file_type(HANDLE handle) {
    DWORD result = GetFileType(handle), error = GetLastError();
    probe_record("GetFileType", result, error, handle);
    SetLastError(error); return result;
}
static BOOL WINAPI probe_close(HANDLE handle) {
    BOOL result = CloseHandle(handle); DWORD error = GetLastError();
    probe_record("CloseHandle", result, error, handle);
    SetLastError(error); return result;
}
static FARPROC WINAPI probe_address(HMODULE module, LPCSTR name);
#define CreateFileW probe_create
#define ReOpenFile probe_reopen
#define FlushFileBuffers probe_flush
#define GetFileInformationByHandle probe_information
#define GetFileInformationByHandleEx probe_information_ex
#define GetFileType probe_file_type
#define CloseHandle probe_close
#define GetProcAddress probe_address
#endif
#include "../freakc/runtime/freak_runtime.c"
#ifdef _WIN32
#undef CreateFileW
#undef ReOpenFile
#undef FlushFileBuffers
#undef GetFileInformationByHandle
#undef GetFileInformationByHandleEx
#undef GetFileType
#undef CloseHandle
#undef GetProcAddress

/* Use the production resolver's exact existing native ABI type. This changes
   only the returned function pointer; all native calls and arguments remain. */
static freak_fs_nt_create_fn probe_nt_real;
static LONG NTAPI probe_nt_create(PHANDLE handle, ACCESS_MASK access,
        freak_fs_nt_object *object, freak_fs_nt_io *io, PLARGE_INTEGER allocation,
        ULONG attributes, ULONG share, ULONG disposition, ULONG options,
        PVOID ea, ULONG ea_length) {
    LONG status = probe_nt_real(handle, access, object, io, allocation, attributes,
                               share, disposition, options, ea, ea_length);
    DWORD error = GetLastError();
    probe_event *event = probe_record("NtCreateFile", status, error, object->root);
    if (event) {
        event->access = access; event->attributes = attributes; event->share = share;
        event->disposition = disposition; event->options = options;
        if (status >= 0) {
            event->other = (uintptr_t)*handle; event->has_io = 1;
            event->io_status = io->value.status; event->io_information = io->information;
        }
        /* A failure need not initialize IO_STATUS_BLOCK; never read indeterminate bytes. */
    }
    SetLastError(error); return status;
}
static FARPROC WINAPI probe_address(HMODULE module, LPCSTR name) {
    FARPROC result = GetProcAddress(module, name); DWORD error = GetLastError();
    if ((uintptr_t)name > UINT16_MAX && !strcmp(name, "NtCreateFile") && result) {
        probe_nt_real = (freak_fs_nt_create_fn)(void *)result;
        result = (FARPROC)(void *)probe_nt_create;
    }
    SetLastError(error); return result;
}
#endif

static void probe_string(const char *text) {
    putchar('"');
    for (const unsigned char *p = (const unsigned char *)text; *p; ++p) {
        if (*p == '"' || *p == '\\') printf("\\%c", *p);
        else if (*p < 32 || *p >= 127) printf("\\u%04x", *p);
        else putchar(*p);
    }
    putchar('"');
}
static void probe_ticket(const char *phase, int64_t ticket, unsigned long native_error) {
    freak_word error = freak_fs_result_error(ticket);
    printf("{\"type\":\"ticket\",\"phase\":"); probe_string(phase);
    printf(",\"ok\":%s,\"completed\":%s,\"missing\":%s,\"native_error\":%lu,\"error\":",
        freak_fs_result_ok(ticket) ? "true" : "false",
        freak_fs_result_completed(ticket) ? "true" : "false",
        freak_fs_result_missing(ticket) ? "true" : "false", native_error);
    probe_string(error.data); puts("}"); freak_word_release_owned(&error);
}
static unsigned long probe_native_error(void) {
#ifdef _WIN32
    return GetLastError();
#else
    return (unsigned long)errno;
#endif
}
static long probe_resources(void) {
#ifdef _WIN32
    DWORD count = 0;
    return GetProcessHandleCount(GetCurrentProcess(), &count) ? (long)count : -1;
#else
    DIR *scan = opendir("/dev/fd"); if (!scan) return -1;
    long count = -1; struct dirent *entry;
    while ((entry = readdir(scan))) if (strcmp(entry->d_name, ".") && strcmp(entry->d_name, "..")) ++count;
    closedir(scan); return count;
#endif
}
#ifdef _WIN32
static void probe_profile(HANDLE directory) {
    WCHAR filesystem[128] = {0}; DWORD serial = 0, maximum = 0, flags = 0;
    BOOL volume_ok = GetVolumeInformationByHandleW(directory, NULL, 0, &serial,
        &maximum, &flags, filesystem, 128); DWORD volume_error = GetLastError();
    char name[512] = {0};
    if (volume_ok) WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, filesystem, -1,
                                     name, sizeof(name), NULL, NULL);
    printf("{\"type\":\"filesystem\",\"ok\":%s,\"native_error\":%lu,\"name\":",
           volume_ok ? "true" : "false", (unsigned long)volume_error);
    probe_string(name); printf(",\"volume_serial\":%lu,\"flags\":%lu}\n",
        (unsigned long)serial, (unsigned long)flags);
    /* Public SDK types/declarations, resolved from the actual system module;
       this observational profile does not add a product linker dependency. */
    HMODULE security = LoadLibraryExW(L"advapi32.dll", NULL, LOAD_LIBRARY_SEARCH_SYSTEM32);
    typedef BOOL (WINAPI *open_fn)(HANDLE,DWORD,PHANDLE);
    typedef BOOL (WINAPI *info_fn)(HANDLE,TOKEN_INFORMATION_CLASS,LPVOID,DWORD,PDWORD);
    typedef BOOL (WINAPI *lookup_fn)(LPCWSTR,LPCWSTR,PLUID);
    open_fn open_token = security ? (open_fn)(void *)GetProcAddress(security,"OpenProcessToken") : NULL;
    info_fn info = security ? (info_fn)(void *)GetProcAddress(security,"GetTokenInformation") : NULL;
    lookup_fn lookup = security ? (lookup_fn)(void *)GetProcAddress(security,"LookupPrivilegeValueW") : NULL;
    HANDLE token = NULL; TOKEN_ELEVATION elevation = {0}; DWORD needed = 0;
    int elevation_known = 0, privileges_known = 0, backup = 0, restore = 0;
    unsigned long error = GetLastError();
    if (open_token && info && lookup && open_token(GetCurrentProcess(),TOKEN_QUERY,&token)) {
        elevation_known = info(token,TokenElevation,&elevation,sizeof(elevation),&needed) != 0;
        union { TOKEN_PRIVILEGES aligned; unsigned char bytes[4096]; } storage;
        privileges_known = info(token,TokenPrivileges,storage.bytes,sizeof(storage.bytes),&needed) != 0;
        error = GetLastError();
        LUID backup_id, restore_id;
        if (privileges_known && lookup(NULL,L"SeBackupPrivilege",&backup_id) && lookup(NULL,L"SeRestorePrivilege",&restore_id)) {
            TOKEN_PRIVILEGES *privileges = (TOKEN_PRIVILEGES *)storage.bytes;
            if (privileges->PrivilegeCount <= (sizeof(storage.bytes)-offsetof(TOKEN_PRIVILEGES,Privileges))/sizeof(LUID_AND_ATTRIBUTES))
                for (DWORD i=0;i<privileges->PrivilegeCount;i++) {
                    LUID_AND_ATTRIBUTES *item = &privileges->Privileges[i];
                    if (item->Luid.HighPart==backup_id.HighPart && item->Luid.LowPart==backup_id.LowPart)
                        backup = (item->Attributes & SE_PRIVILEGE_ENABLED) != 0;
                    if (item->Luid.HighPart==restore_id.HighPart && item->Luid.LowPart==restore_id.LowPart)
                        restore = (item->Attributes & SE_PRIVILEGE_ENABLED) != 0;
                }
            else privileges_known = 0;
        } else privileges_known = 0;
    } else error = GetLastError();
    printf("{\"type\":\"token\",\"elevation_known\":%s,\"elevated\":%s,\"privileges_known\":%s,\"backup_enabled\":%s,\"restore_enabled\":%s,\"native_error\":%lu}\n",
        elevation_known?"true":"false",elevation.TokenIsElevated?"true":"false",
        privileges_known?"true":"false",backup?"true":"false",restore?"true":"false",error);
    if (token) CloseHandle(token); if (security) FreeLibrary(security);
}
static void probe_dump_events(void) {
    for (size_t i=0;i<probe_event_count;i++) {
        probe_event *event = &probe_events[i];
        printf("{\"type\":\"native\",\"api\":"); probe_string(event->api);
        printf(",\"phase\":"); probe_string(event->phase);
        printf(",\"result\":%"PRId64",\"last_error\":%lu,\"handle\":%"PRIu64",\"other_handle\":%"PRIu64
            ",\"access\":%"PRIu64",\"flags\":%"PRIu64",\"share\":%"PRIu64",\"disposition\":%"PRIu64
            ",\"options\":%"PRIu64",\"attributes\":%lu,\"io_valid\":%s,\"io_status\":%"PRId64
            ",\"io_information\":%"PRIu64",\"identity_valid\":%s,\"volume\":%"PRIu64",\"file_id\":\"",
            event->result,(unsigned long)event->error,event->handle,event->other,event->access,
            event->flags,event->share,event->disposition,event->options,(unsigned long)event->attributes,
            event->has_io?"true":"false",event->io_status,event->io_information,
            event->has_identity?"true":"false",event->volume);
        for (size_t j=0;j<sizeof(event->identity);j++) printf("%02x",event->identity[j]);
        puts("\"}");
    }
}
#define PROBE_PHASE(name) (probe_phase = (name))
#else
#define PROBE_PHASE(name) ((void)0)
#endif

int main(int argc, char **argv) {
    freak_argc = argc; freak_argv = argv;
    if (freak_process_args_count() != 2) return 2;
    freak_word parent = freak_process_arg(1);
    int passed = 1, cleanup_completed = 0;
    int64_t initial_tickets = freak_fs_result_live();
    long before = probe_resources();
    PROBE_PHASE("open_parent");
    int64_t root = freak_fs_open_dir_ticket(parent);
    probe_ticket("open_parent",root,probe_native_error());
    passed &= freak_fs_result_ok(root);
#ifdef _WIN32
    if (freak_fs_result_ok(root)) probe_profile(freak_fs_ticket_require(root)->directory);
#endif
    PROBE_PHASE("temp_dir");
    int64_t temp = freak_fs_temp_dir(parent,freak_word_lit("fs-probe"));
    probe_ticket("temp_dir",temp,probe_native_error());
    passed &= freak_fs_result_ok(temp);
    if (freak_fs_result_ok(temp)) {
        /* A real existing-directory control proves reporting does not turn
           rejected creation or a false missing fact into successful proof. */
        if (getenv("FREAK_FS_PROBE_CONTROL")) {
            PROBE_PHASE("control_existing_runtime");
            int64_t prior = freak_fs_mkdir_relative_checked(temp,freak_word_lit("runtime"));
            probe_ticket("control_existing_runtime",prior,probe_native_error());
            freak_fs_result_release(prior);
        }
        PROBE_PHASE("open_missing_runtime");
        int64_t existing = freak_fs_open_relative_dir_ticket(temp,freak_word_lit("runtime"));
        probe_ticket("open_missing_runtime",existing,probe_native_error());
        passed &= !freak_fs_result_ok(existing) && freak_fs_result_missing(existing);
        freak_fs_result_release(existing);
        PROBE_PHASE("mkdir_runtime");
        int64_t made = freak_fs_mkdir_relative_checked(temp,freak_word_lit("runtime"));
        probe_ticket("mkdir_runtime",made,probe_native_error());
        passed &= freak_fs_result_ok(made) && freak_fs_result_completed(made);
        freak_fs_result_release(made);
#ifdef _WIN32
        /* The admitted parent itself came through NtCreateFile component
           walks. Compare an actual CreateFileW handle of the same identity;
           these observations never decide or repair the production contract. */
        if (freak_fs_result_ok(root)) {
            PROBE_PHASE("observe_NtCreateFile_parent_sync");
            int synchronized = freak_fs_anchor_sync(freak_fs_ticket_require(root)->directory);
            unsigned long native_error = probe_native_error();
            printf("{\"type\":\"sync_observation\",\"origin\":\"NtCreateFile_admitted_parent\",\"synchronized\":%s,\"native_error\":%lu}\n",
                synchronized?"true":"false",native_error);
            PROBE_PHASE("observe_CreateFile_same_parent_sync");
            wchar_t *wide = freak_command_wide(parent.data);
            HANDLE direct = probe_create(wide,FILE_LIST_DIRECTORY|FILE_TRAVERSE|FILE_READ_ATTRIBUTES|SYNCHRONIZE,
                FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,NULL,OPEN_EXISTING,
                FILE_FLAG_BACKUP_SEMANTICS|FILE_FLAG_OPEN_REPARSE_POINT,NULL);
            free(wide);
            int same = direct != INVALID_HANDLE_VALUE && freak_fs_anchor_same(direct,freak_fs_ticket_require(root)->directory);
            synchronized = same && freak_fs_anchor_sync(direct);
            native_error = probe_native_error();
            printf("{\"type\":\"sync_observation\",\"origin\":\"CreateFile_same_parent\",\"identity_matches_admitted_parent\":%s,\"synchronized\":%s,\"native_error\":%lu}\n",
                same?"true":"false",synchronized?"true":"false",native_error);
            freak_fs_anchor_close(direct);
        }
        PROBE_PHASE("observe_NtCreateFile_temp_sync");
        int synchronized = freak_fs_anchor_sync(freak_fs_ticket_require(temp)->directory);
        unsigned long native_error = probe_native_error();
        printf("{\"type\":\"sync_observation\",\"origin\":\"NtCreateFile_temp\",\"synchronized\":%s,\"native_error\":%lu}\n",
            synchronized?"true":"false",native_error);
#endif
        PROBE_PHASE("cleanup_temp");
        int64_t removed = freak_fs_remove_temp_dir_checked(temp);
        probe_ticket("cleanup_temp",removed,probe_native_error());
        cleanup_completed = freak_fs_result_completed(removed);
        passed &= freak_fs_result_ok(removed) && cleanup_completed;
        freak_fs_result_release(removed);
    }
    PROBE_PHASE("release_tickets");
    freak_fs_result_release(temp); freak_fs_result_release(root);
    int64_t after_tickets = freak_fs_result_live();
    long after = probe_resources();
#ifdef _WIN32
    probe_dump_events();
    passed &= !probe_overflow;
    int overflow = probe_overflow;
#else
    int overflow = 0;
#endif
    int resources_ok = before >= 0 && after == before && after_tickets == initial_tickets;
    passed &= resources_ok;
    printf("{\"type\":\"summary\",\"diagnostic_completed\":true,\"production_contract_passed\":%s,\"cleanup_completed\":%s,\"trace_overflow\":%s,\"tickets_before\":%"PRId64",\"tickets_after\":%"PRId64",\"resources_before\":%ld,\"resources_after\":%ld,\"resources_balanced\":%s}\n",
        passed?"true":"false",cleanup_completed?"true":"false",overflow?"true":"false",
        initial_tickets,after_tickets,before,after,resources_ok?"true":"false");
    return overflow ? 3 : 0;
}
