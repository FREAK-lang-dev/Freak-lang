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
#include <winternl.h>
#include <winioctl.h>

typedef struct {
    const char *api, *phase;
    uint64_t handle, other, access, flags, share, disposition, options;
    int64_t result, io_status;
    uint64_t io_information, volume, length;
    DWORD error, attributes, device_type, descriptor_type, descriptor_size;
    unsigned char identity[16], descriptor_id[16];
    int has_identity, has_io, has_device, has_descriptor;
} probe_event;
static probe_event probe_events[512];
static size_t probe_event_count;
static int probe_overflow;
static const char *probe_phase = "startup";
static _Noreturn void probe_nonfinal(const char *api,LONG status);
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
static HANDLE WINAPI probe_open_by_id(HANDLE volume, LPFILE_ID_DESCRIPTOR descriptor,
        DWORD access, DWORD share, LPSECURITY_ATTRIBUTES security, DWORD flags) {
    FILE_ID_DESCRIPTOR requested;
    int extended = descriptor && descriptor->dwSize >= sizeof(*descriptor) && descriptor->Type == ExtendedFileIdType;
    if (extended) requested = *descriptor;
    HANDLE result = OpenFileById(volume, descriptor, access, share, security, flags);
    DWORD error = GetLastError();
    probe_event *event = probe_record("OpenFileById", result != INVALID_HANDLE_VALUE, error, volume);
    if (event) {
        event->other = (uintptr_t)result; event->access = access;
        event->share = share; event->flags = flags;
        if (extended) {
            event->has_descriptor = 1; event->descriptor_type = requested.Type;
            event->descriptor_size = requested.dwSize;
            memcpy(event->descriptor_id, requested.ExtendedFileId.Identifier, sizeof(event->descriptor_id));
        }
    }
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
static BOOL WINAPI probe_duplicate(HANDLE source_process, HANDLE source,
        HANDLE target_process, LPHANDLE target, DWORD access, BOOL inherit, DWORD options) {
    BOOL result = DuplicateHandle(source_process,source,target_process,target,access,inherit,options);
    DWORD error = GetLastError();
    probe_event *event = probe_record("DuplicateHandle",result,error,source);
    if (event) { event->access=access; event->options=options;
        if (result) event->other=(uintptr_t)*target; }
    SetLastError(error); return result;
}
static FARPROC WINAPI probe_address(HMODULE module, LPCSTR name);
#define CreateFileW probe_create
#define ReOpenFile probe_reopen
#define OpenFileById probe_open_by_id
#define FlushFileBuffers probe_flush
#define GetFileInformationByHandle probe_information
#define GetFileInformationByHandleEx probe_information_ex
#define GetFileType probe_file_type
#define CloseHandle probe_close
#define DuplicateHandle probe_duplicate
#define GetProcAddress probe_address
#endif
#include "../freakc/runtime/freak_runtime.c"
#ifdef _WIN32
#undef CreateFileW
#undef ReOpenFile
#undef OpenFileById
#undef FlushFileBuffers
#undef GetFileInformationByHandle
#undef GetFileInformationByHandleEx
#undef GetFileType
#undef CloseHandle
#undef DuplicateHandle
#undef GetProcAddress

/* Use the production resolver's exact existing native ABI type. This changes
   only the returned function pointer; all native calls and arguments remain. */
static freak_fs_nt_create_fn probe_nt_real;
typedef LONG (NTAPI *probe_flush_ex_fn)(HANDLE,ULONG,PVOID,ULONG,freak_fs_nt_io *);
typedef LONG (NTAPI *probe_query_volume_fn)(HANDLE,freak_fs_nt_io *,PVOID,ULONG,ULONG);
static probe_flush_ex_fn probe_flush_ex_real;
static probe_query_volume_fn probe_query_volume_real;
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
        if (status == 0 && io->value.status == 0) {
            event->other = (uintptr_t)*handle; event->has_io = 1;
            event->io_status = io->value.status; event->io_information = io->information;
        }
        /* A failure/pending return need not complete IO_STATUS_BLOCK; never
           read indeterminate bytes or label a pending operation complete. */
    }
    if (status==0x103 || (status==0 &&
        (io->value.status==INT32_MIN || io->value.status==0x103)))
        probe_nonfinal("NtCreateFile",status);
    SetLastError(error); return status;
}
static LONG NTAPI probe_nt_flush_ex(HANDLE handle, ULONG flags, PVOID parameters,
        ULONG length, freak_fs_nt_io *io) {
    /* NTSTATUS and a successful completed IOSB are separate observations.
       Failure/pending returns do not authorize reading caller output. */
    LONG status = probe_flush_ex_real(handle, flags, parameters, length, io);
    DWORD error = GetLastError();
    probe_event *event = probe_record("NtFlushBuffersFileEx", status, error, handle);
    if (event) {
        event->flags = flags; event->length = length;
        if (status == 0 && io && io->value.status == 0) {
            event->has_io = 1; event->io_status = io->value.status;
            event->io_information = io->information;
        }
    }
    if (status == 0x103 || (status == 0 && io &&
        (io->value.status == INT32_MIN || io->value.status == 0x103)))
        probe_nonfinal("NtFlushBuffersFileEx", status);
    SetLastError(error); return status;
}
static LONG NTAPI probe_nt_query_volume(HANDLE handle, freak_fs_nt_io *io,
        PVOID information, ULONG length, ULONG kind) {
    LONG status = probe_query_volume_real(handle, io, information, length, kind);
    DWORD error = GetLastError();
    probe_event *event = probe_record("NtQueryVolumeInformationFile", status, error, handle);
    if (event) {
        event->flags = kind; event->length = length;
        if (status == 0 && io && io->value.status == 0) {
            event->has_io = 1; event->io_status = io->value.status;
            event->io_information = io->information;
            if (information && kind == FileFsDeviceInformation && length >= sizeof(FILE_FS_DEVICE_INFORMATION) &&
                io->information >= sizeof(FILE_FS_DEVICE_INFORMATION) && io->information <= length) {
                FILE_FS_DEVICE_INFORMATION device;
                memcpy(&device, information, sizeof(device));
                event->has_device = 1; event->device_type = device.DeviceType;
                event->attributes = device.Characteristics;
            }
        }
    }
    if (status == 0x103 || (status == 0 && io &&
        (io->value.status == INT32_MIN || io->value.status == 0x103)))
        probe_nonfinal("NtQueryVolumeInformationFile", status);
    SetLastError(error); return status;
}
static FARPROC WINAPI probe_address(HMODULE module, LPCSTR name) {
    FARPROC result = GetProcAddress(module, name); DWORD error = GetLastError();
    if ((uintptr_t)name > UINT16_MAX && result) {
        if (!strcmp(name, "NtCreateFile")) {
            probe_nt_real = (freak_fs_nt_create_fn)(void *)result;
            result = (FARPROC)(void *)probe_nt_create;
        } else if (!strcmp(name, "NtFlushBuffersFileEx")) {
            probe_flush_ex_real = (probe_flush_ex_fn)(void *)result;
            result = (FARPROC)(void *)probe_nt_flush_ex;
        } else if (!strcmp(name, "NtQueryVolumeInformationFile")) {
            probe_query_volume_real = (probe_query_volume_fn)(void *)result;
            result = (FARPROC)(void *)probe_nt_query_volume;
        }
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
static void probe_checkpoint(const char *name) {
    DWORD error = GetLastError();
    long count = probe_resources();
    printf("{\"type\":\"resource_checkpoint\",\"phase\":"); probe_string(name);
    printf(",\"process_handles\":%ld}\n",count);
    SetLastError(error);
}
/* Microsoft NtFlushBuffersFileEx: HANDLE, ULONG Flags, PVOID Parameters,
   ULONG ParametersSize, PIO_STATUS_BLOCK. Pinned ntdll also exports @20 on
   x86. Reuse the production IOSB only after verifying its SDK layout. */
_Static_assert(sizeof(freak_fs_nt_io)==sizeof(IO_STATUS_BLOCK),"native IOSB size");
_Static_assert(offsetof(freak_fs_nt_io,value)==offsetof(IO_STATUS_BLOCK,Status),"native IOSB status");
_Static_assert(offsetof(freak_fs_nt_io,information)==offsetof(IO_STATUS_BLOCK,Information),"native IOSB information");

static void probe_alternative_flush(const char *method,HANDLE reference,HANDLE candidate,
                                    ACCESS_MASK access,int open_attempted,DWORD open_error) {
    DWORD original_error=GetLastError();
    BY_HANDLE_FILE_INFORMATION metadata;
    int opened=candidate != INVALID_HANDLE_VALUE;
    int same=opened && probe_information(candidate,&metadata) &&
        probe_file_type(candidate)==FILE_TYPE_DISK &&
        (metadata.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) &&
        !(metadata.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT) &&
        freak_fs_anchor_same(reference,candidate);
    probe_flush_ex_fn flush=(probe_flush_ex_fn)(void *)GetProcAddress(GetModuleHandleW(L"ntdll.dll"),"NtFlushBuffersFileEx");
    freak_fs_nt_io io; memset(&io,0,sizeof(io));
    io.value.status=INT32_MIN; io.information=UINTPTR_MAX;
    int called=same && flush != NULL;
    LONG status=INT32_MIN; DWORD error=GetLastError();
    if (called) {
        status=flush(candidate,0,NULL,0,&io); error=GetLastError();
        probe_event *event=probe_record("NtFlushBuffersFileEx",status,error,candidate);
        if (event && status==0 && io.value.status==0 && io.information!=UINTPTR_MAX) {
            event->has_io=1; event->io_status=io.value.status;
            event->io_information=io.information;
        }
    }
    int pending=called && status==0x103; /* STATUS_PENDING is not completion. */
    int completed=called && status==0 && io.value.status==0;
    printf("{\"type\":\"alternative\",\"method\":"); probe_string(method);
    printf(",\"open_attempted\":%s,\"opened\":%s,\"open_error\":%lu,\"requested_access\":%lu,\"reference_handle\":%"PRIu64",\"candidate_handle\":%"PRIu64
        ",\"identity_matches\":%s,\"flush_api_available\":%s,\"flush_called\":%s,\"flush_flags\":0,\"parameters_size\":0,\"ntstatus\":",
        open_attempted?"true":"false",opened?"true":"false",(unsigned long)open_error,(unsigned long)access,
        (uint64_t)(uintptr_t)reference,(uint64_t)(uintptr_t)candidate,
        same?"true":"false",flush?"true":"false",called?"true":"false");
    if (called) printf("%ld",(long)status); else printf("null");
    printf(",\"status_pending\":%s,\"completion_valid\":%s,\"io_status\":",pending?"true":"false",completed?"true":"false");
    if (completed) printf("%ld",(long)io.value.status); else printf("null");
    printf(",\"io_information\":");
    if (completed && io.information!=UINTPTR_MAX) printf("%"PRIu64,(uint64_t)io.information); else printf("null");
    printf(",\"last_error\":%lu,\"durability_proven\":false}\n",(unsigned long)error);
    if (pending || (called && status==0 &&
        (io.value.status==INT32_MIN || io.value.status==0x103)))
        probe_nonfinal("NtFlushBuffersFileEx",status);
    SetLastError(original_error);
}
static void probe_alternatives(HANDLE parent,HANDLE temp) {
    probe_phase="alternative_held_temp";
    probe_alternative_flush("held_writable_temp",temp,temp,0,0,0);
    probe_phase="alternative_duplicate_temp";
    HANDLE copy=INVALID_HANDLE_VALUE;
    BOOL copied=probe_duplicate(GetCurrentProcess(),temp,GetCurrentProcess(),&copy,0,FALSE,DUPLICATE_SAME_ACCESS);
    DWORD error=GetLastError();
    if (!copied) copy=INVALID_HANDLE_VALUE;
    probe_alternative_flush("duplicate_same_access_temp",temp,copy,0,1,error);
    freak_fs_anchor_close(copy);
    if (parent==INVALID_HANDLE_VALUE) return;
    ACCESS_MASK rights[]={FILE_APPEND_DATA,FILE_WRITE_DATA};
    const char *reopens[]={"reopen_parent_append","reopen_parent_write"};
    const char *empties[]={"nt_empty_parent_append","nt_empty_parent_write"};
    const char *by_ids[]={"open_by_id_parent_append","open_by_id_parent_write"};
    for (size_t i=0;i<2;i++) {
        ACCESS_MASK access=rights[i]|FILE_READ_ATTRIBUTES|SYNCHRONIZE;
        probe_phase=reopens[i];
        HANDLE reopened=probe_reopen(parent,access,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,FILE_FLAG_BACKUP_SEMANTICS);
        error=GetLastError();
        probe_alternative_flush(reopens[i],parent,reopened,access,1,error);
        freak_fs_anchor_close(reopened);
        probe_phase=empties[i];
        /* Hypothesis only: an empty relative object name may reopen its held
           RootDirectory. FILE_OPEN never creates an entry; verify identity. */
        wchar_t empty[]=L"";
        freak_fs_nt_string name={0,sizeof(empty),empty};
        freak_fs_nt_object object={sizeof(object),parent,&name,0x40,NULL,NULL};
        freak_fs_nt_io io; memset(&io,0,sizeof(io));
        io.value.status=INT32_MIN; io.information=UINTPTR_MAX;
        HANDLE native=INVALID_HANDLE_VALUE; int attempted=probe_nt_real != NULL;
        LONG status=attempted ? probe_nt_create(&native,access,&object,&io,NULL,FILE_ATTRIBUTE_NORMAL,
            FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,1,1|0x20|0x200000,NULL,0) : INT32_MIN;
        error=GetLastError();
        if (status!=0) {
            if (native!=INVALID_HANDLE_VALUE) freak_fs_anchor_close(native);
            native=INVALID_HANDLE_VALUE;
        }
        probe_alternative_flush(empties[i],parent,native,access,attempted,error);
        freak_fs_anchor_close(native);
        probe_phase=by_ids[i];
        FILE_ID_INFO identity; FILE_ID_DESCRIPTOR descriptor;
        memset(&descriptor,0,sizeof(descriptor));
        descriptor.dwSize=sizeof(descriptor); descriptor.Type=ExtendedFileIdType;
        int identity_known=probe_information_ex(parent,FileIdInfo,&identity,sizeof(identity)) != 0;
        HANDLE by_id=INVALID_HANDLE_VALUE;
        if (identity_known) {
            descriptor.ExtendedFileId=identity.FileId;
            by_id=OpenFileById(parent,&descriptor,access,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,NULL,
                FILE_FLAG_BACKUP_SEMANTICS|FILE_FLAG_OPEN_REPARSE_POINT);
            error=GetLastError();
            probe_event *event=probe_record("OpenFileById",by_id!=INVALID_HANDLE_VALUE,error,parent);
            if (event) {
                event->other=(uintptr_t)by_id; event->access=access;
                event->flags=FILE_FLAG_BACKUP_SEMANTICS|FILE_FLAG_OPEN_REPARSE_POINT; event->share=7;
                event->has_identity=1; event->volume=identity.VolumeSerialNumber;
                memcpy(event->identity,descriptor.ExtendedFileId.Identifier,sizeof(event->identity));
            }
        } else error=GetLastError();
        probe_alternative_flush(by_ids[i],parent,by_id,access,identity_known,error);
        freak_fs_anchor_close(by_id);
    }
}
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
    /* Actual configured SDK query/structure. FILE_REMOTE_DEVICE=0x10 is the
       pinned SDK wdm.h characteristic; failure never means a local device. */
    _Static_assert(FileFsDeviceInformation==4,"native filesystem device class");
    _Static_assert(sizeof(FILE_FS_DEVICE_INFORMATION)==8,"native filesystem device size");
    typedef NTSTATUS (NTAPI *query_fn)(HANDLE,PIO_STATUS_BLOCK,PVOID,ULONG,FS_INFORMATION_CLASS);
    query_fn query=(query_fn)(void *)GetProcAddress(GetModuleHandleW(L"ntdll.dll"),"NtQueryVolumeInformationFile");
    IO_STATUS_BLOCK io; memset(&io,0,sizeof(io)); io.Status=INT32_MIN; io.Information=UINTPTR_MAX;
    FILE_FS_DEVICE_INFORMATION device; memset(&device,0xff,sizeof(device));
    NTSTATUS status=query ? query(directory,&io,&device,sizeof(device),FileFsDeviceInformation) : INT32_MIN;
    DWORD query_error=GetLastError();
    int completed=query && status==0 && io.Status==0 && io.Information>=sizeof(device) && io.Information!=UINTPTR_MAX;
    if (query) {
        probe_event *event=probe_record("NtQueryVolumeInformationFile",status,query_error,directory);
        if (event) { event->flags=FileFsDeviceInformation;
            if (completed) { event->has_io=1; event->io_status=io.Status; event->io_information=io.Information;
                event->attributes=device.Characteristics; } }
    }
    printf("{\"type\":\"device_profile\",\"query_available\":%s,\"information_class\":4,\"ntstatus\":",
        query?"true":"false");
    if (query) printf("%ld",(long)status); else printf("null");
    printf(",\"status_pending\":%s,\"completion_valid\":%s,\"io_status\":",
        query && status==0x103?"true":"false",completed?"true":"false");
    if (completed) printf("%ld",(long)io.Status); else printf("null");
    printf(",\"io_information\":");
    if (completed) printf("%"PRIu64,(uint64_t)io.Information); else printf("null");
    printf(",\"device_type\":");
    if (completed) printf("%lu",(unsigned long)device.DeviceType); else printf("null");
    printf(",\"characteristics\":");
    if (completed) printf("%lu",(unsigned long)device.Characteristics); else printf("null");
    printf(",\"remote\":");
    if (completed) printf("%s",device.Characteristics & 0x10?"true":"false"); else printf("null");
    printf(",\"local_disk\":");
    if (completed) printf("%s",device.DeviceType==FILE_DEVICE_DISK && !(device.Characteristics & 0x10)?"true":"false"); else printf("null");
    printf(",\"last_error\":%lu}\n",(unsigned long)query_error);
    if (query && (status==0x103 || (status==0 && (io.Status==INT32_MIN || io.Status==0x103))))
        probe_nonfinal("NtQueryVolumeInformationFile",status);
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
        printf("\",\"length\":%"PRIu64",\"device_valid\":%s,\"device_type\":%lu,\"descriptor_valid\":%s,\"descriptor_type\":%lu,\"descriptor_size\":%lu,\"descriptor_id\":\"",
            event->length,event->has_device?"true":"false",(unsigned long)event->device_type,
            event->has_descriptor?"true":"false",(unsigned long)event->descriptor_type,
            (unsigned long)event->descriptor_size);
        for (size_t j=0;j<sizeof(event->descriptor_id);j++) printf("%02x",event->descriptor_id[j]);
        puts("\"}");
    }
}
static _Noreturn void probe_nonfinal(const char *api,LONG status) {
    printf("{\"type\":\"incomplete\",\"api\":"); probe_string(api);
    printf(",\"ntstatus\":%ld,\"diagnostic_completed\":false,\"termination\":\"no_unwind\"}\n",(long)status);
    probe_dump_events(); fflush(stdout);
    fputs("checked FS diagnostic: pending or nonfinal native output; terminating without unwinding\n",stderr);
    fflush(stderr);
    /* Keep pending handles and output storage alive until process teardown.
       No callback, caller return, stack unwind, or premature close occurs. */
    _Exit(74);
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
    probe_checkpoint("after_open_parent");
    if (freak_fs_result_ok(root)) probe_profile(freak_fs_ticket_require(root)->directory);
    probe_checkpoint("after_profile");
#endif
    PROBE_PHASE("temp_dir");
    int64_t temp = freak_fs_temp_dir(parent,freak_word_lit("fs-probe"));
    probe_ticket("temp_dir",temp,probe_native_error());
    passed &= freak_fs_result_ok(temp);
#ifdef _WIN32
    probe_checkpoint("after_temp_dir");
#endif
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
        probe_checkpoint("after_mkdir");
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
        probe_checkpoint("before_alternatives");
        probe_alternatives(freak_fs_result_ok(root) ? freak_fs_ticket_require(root)->directory : INVALID_HANDLE_VALUE,
                           freak_fs_ticket_require(temp)->directory);
        probe_checkpoint("after_alternatives");
#endif
        PROBE_PHASE("cleanup_temp");
        int64_t removed = freak_fs_remove_temp_dir_checked(temp);
        probe_ticket("cleanup_temp",removed,probe_native_error());
        cleanup_completed = freak_fs_result_completed(removed);
        passed &= freak_fs_result_ok(removed) && cleanup_completed;
        freak_fs_result_release(removed);
#ifdef _WIN32
        probe_checkpoint("after_cleanup");
#endif
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
