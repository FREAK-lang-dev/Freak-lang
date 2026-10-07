/* Shared V3.5 checked I/O substrate; included by the shipping C runtime. */
/* Some bootstrap fixtures include this runtime after feature-restricted libc
   headers. Their include guards cannot be reopened by a late feature macro.
   Declare these stable platform entry points with their actual libc ABI. */
#ifndef _WIN32
extern char *realpath(const char *restrict path,char *restrict resolved);
#endif
#ifndef _WIN32
#include <sys/file.h>
#else
#include <aclapi.h>
#endif
#ifdef __linux__
#include <sys/syscall.h>
extern long syscall(long number,...);
#endif
#ifdef __APPLE__
extern int renamex_np(const char *source,const char *destination,unsigned int flags);
#define FREAK_DARWIN_RENAME_EXCL 0x00000004u
#endif
#define FREAK_FS_RESULT_DOMAIN UINT64_C(0xe000000000000000)
#define FREAK_FS_READ_LIMIT ((size_t)64 * 1024 * 1024)
typedef struct {
    unsigned char *data;
    size_t length;
    char **entries;
    size_t entry_count;
    uint32_t generation;
    bool in_use, ok, source_text, completed, has_directory, owns_temp, temp_active, owns_lock, missing;
#ifdef _WIN32
    HANDLE directory, temp_parent;
#else
    int directory, temp_parent;
#endif
    char *temp_name;
    int64_t kind, size, mode;
    char error[256];
} freak_fs_ticket;
static freak_fs_ticket *freak_fs_tickets = NULL;
static size_t freak_fs_tickets_count = 0, freak_fs_tickets_capacity = 0, freak_fs_tickets_live = 0;
static bool freak_fs_ticket_audit_registered = false;

static void freak_fs_ticket_audit(void) {
#if defined(FREAK_RUNTIME_OWNERSHIP_AUDIT) || defined(FREAK_C_RUNTIME_OWNERSHIP_AUDIT)
    if (freak_fs_tickets_live) {
        fprintf(stderr,"FREAK: ownership audit found %llu live filesystem result(s)\n",(unsigned long long)freak_fs_tickets_live);
        _Exit(1);
    }
#endif
}
static int64_t freak_fs_ticket_new(void) {
    if (!freak_fs_ticket_audit_registered) {
        if (atexit(freak_fs_ticket_audit) != 0) freak_command_fail("cannot register filesystem result audit");
        freak_fs_ticket_audit_registered = true;
    }
    size_t slot = 0;
    while (slot < freak_fs_tickets_count && (freak_fs_tickets[slot].in_use ||
            freak_fs_tickets[slot].generation == FREAK_COMMAND_GENERATION_MAX)) slot++;
    if (slot == freak_fs_tickets_count) {
        if (slot >= UINT32_MAX - 1) freak_command_fail("filesystem ticket table exhausted");
        if (slot == freak_fs_tickets_capacity) {
            size_t capacity = freak_fs_tickets_capacity ? freak_fs_tickets_capacity * 2 : 16;
            if (capacity < freak_fs_tickets_capacity || capacity > SIZE_MAX / sizeof(*freak_fs_tickets))
                freak_command_fail("filesystem result table overflow");
            freak_fs_ticket *grown = realloc(freak_fs_tickets,capacity * sizeof(*grown));
            if (!grown) freak_command_fail("out of memory growing filesystem results");
            memset(grown + freak_fs_tickets_capacity,0,(capacity - freak_fs_tickets_capacity) * sizeof(*grown));
            freak_fs_tickets = grown; freak_fs_tickets_capacity = capacity;
        }
        freak_fs_tickets_count++;
    }
    freak_fs_ticket *result = &freak_fs_tickets[slot];
    uint32_t generation = result->generation + 1;
    memset(result,0,sizeof(*result));
#ifndef _WIN32
    result->directory = result->temp_parent = -1;
#endif
    result->generation = generation; result->in_use = true;
    freak_fs_tickets_live++;
    return (int64_t)(FREAK_FS_RESULT_DOMAIN | ((uint64_t)generation << 32) | (slot + 1));
}
static freak_fs_ticket *freak_fs_ticket_require(int64_t handle) {
    uint64_t raw = (uint64_t)handle;
    uint32_t slot = (uint32_t)raw, generation = (uint32_t)((raw >> 32) & FREAK_COMMAND_GENERATION_MAX);
    if ((raw & FREAK_COMMAND_DOMAIN_MASK) != FREAK_FS_RESULT_DOMAIN || !slot || slot > freak_fs_tickets_count ||
            !freak_fs_tickets[slot-1].in_use || freak_fs_tickets[slot-1].generation != generation)
        freak_command_fail("invalid or stale filesystem result ticket");
    return &freak_fs_tickets[slot-1];
}
static void freak_fs_ticket_error(freak_fs_ticket *result,const char *reason) {
    result->ok = false;
    snprintf(result->error,sizeof(result->error),"%s",reason);
}
static char *freak_fs_checked_path(freak_fs_ticket *result,freak_word path) {
    if (!path.data || !path.length || path.length >= SIZE_MAX || memchr(path.data,0,path.length)) {
        freak_fs_ticket_error(result,"filesystem path is empty or contains NUL"); return NULL;
    }
    if (!freak_system_utf8_valid(path.data,path.length)) {
        freak_fs_ticket_error(result,"filesystem path is not valid UTF-8"); return NULL;
    }
    return freak_command_copy(path,false);
}
static void freak_fs_ticket_data(freak_fs_ticket *result,const void *bytes,size_t length) {
    result->data = freak_command_allocate(length + 1,1);
    if (length) memcpy(result->data,bytes,length);
    result->length = length; result->ok = true;
}
static void freak_fs_close_descriptor(int descriptor) {
#ifdef _WIN32
    _close(descriptor);
#else
    close(descriptor);
#endif
}
static int freak_fs_open_read(const char *path) {
#ifdef _WIN32
    wchar_t *name = freak_command_wide(path);
    HANDLE file = CreateFileW(name,GENERIC_READ,FILE_SHARE_READ,NULL,OPEN_EXISTING,
            FILE_FLAG_OPEN_REPARSE_POINT,NULL);
    free(name);
    if (file == INVALID_HANDLE_VALUE) return -1;
    BY_HANDLE_FILE_INFORMATION metadata;
    if (!GetFileInformationByHandle(file,&metadata) ||
            (metadata.dwFileAttributes & (FILE_ATTRIBUTE_REPARSE_POINT | FILE_ATTRIBUTE_DIRECTORY)) ||
            GetFileType(file) != FILE_TYPE_DISK) {
        CloseHandle(file); SetLastError(ERROR_ACCESS_DENIED); return -1;
    }
    int descriptor = _open_osfhandle((intptr_t)file,_O_RDONLY | _O_BINARY);
    if (descriptor < 0) { CloseHandle(file); SetLastError(ERROR_TOO_MANY_OPEN_FILES); }
    return descriptor;
#else
    return open(path,O_RDONLY | O_NONBLOCK | O_NOFOLLOW | O_CLOEXEC);
#endif
}
static bool freak_fs_failure_missing(void) {
#ifdef _WIN32
    DWORD error=GetLastError(); return error == ERROR_FILE_NOT_FOUND || error == ERROR_PATH_NOT_FOUND;
#else
    return errno == ENOENT;
#endif
}
static int64_t freak_fs_read_mode(freak_word path,bool text) {
    int64_t handle = freak_fs_ticket_new(); freak_fs_ticket *result = freak_fs_ticket_require(handle);
    char *name = freak_fs_checked_path(result,path); if (!name) return handle;
    int descriptor = freak_fs_open_read(name);
    result->missing=descriptor < 0 && freak_fs_failure_missing(); free(name);
    if (descriptor < 0) { freak_fs_ticket_error(result,"could not open filesystem file"); return handle; }
#ifdef _WIN32
    struct _stat64 metadata;
    bool regular = _fstat64(descriptor,&metadata) == 0 && (metadata.st_mode & _S_IFMT) == _S_IFREG;
#else
    struct stat metadata;
    bool regular = fstat(descriptor,&metadata) == 0 && S_ISREG(metadata.st_mode);
#endif
    if (!regular || metadata.st_size < 0 || (uintmax_t)metadata.st_size > FREAK_FS_READ_LIMIT) {
        freak_fs_close_descriptor(descriptor);
        freak_fs_ticket_error(result,!regular ? "filesystem path is not a readable regular file" : "filesystem file exceeds 64 MiB read limit");
        return handle;
    }
#ifndef _WIN32
    result->mode=(int64_t)(metadata.st_mode & 07777);
#endif
#ifdef _WIN32
    FILE *file = _fdopen(descriptor,"rb");
#else
    FILE *file = fdopen(descriptor,"rb");
#endif
    if (!file) { freak_fs_close_descriptor(descriptor); freak_fs_ticket_error(result,"could not open filesystem stream"); return handle; }
    size_t length = (size_t)metadata.st_size;
    unsigned char *contents = freak_command_allocate(length + 1,1);
    size_t count = fread(contents,1,length,file);
    bool complete = count == length && !ferror(file);
    if (complete) complete = fgetc(file) == EOF && !ferror(file);
    if (fclose(file) != 0) complete = false;
    if (!complete) { free(contents); freak_fs_ticket_error(result,"could not read complete filesystem file"); return handle; }
    if (text && !freak_byte_buffer_utf8_valid(contents,length)) {
        free(contents); freak_fs_ticket_error(result,"filesystem text is not NUL-free UTF-8; use binary I/O"); return handle;
    }
    result->data = contents; result->length = length; result->ok = true; result->size = (int64_t)length;
    return handle;
}
int64_t freak_fs_read_ticket(freak_word path) { return freak_fs_read_mode(path,true); }
int64_t freak_fs_read_bytes_ticket(freak_word path) { return freak_fs_read_mode(path,false); }
int64_t freak_fs_read_source_ticket(freak_word path) {
    int64_t handle = freak_fs_ticket_new();
    freak_fs_ticket *result = freak_fs_ticket_require(handle);
    freak_result_word_word source = freak_fs_read_checked(path);
    if (source.is_ok) {
        freak_fs_ticket_data(result,source.data.ok_val.data,source.data.ok_val.length);
        result->source_text = true; result->size = (int64_t)source.data.ok_val.length;
        freak_word_release_owned(&source.data.ok_val);
    } else {
        snprintf(result->error,sizeof(result->error),"%.*s",(int)source.data.err_val.length,source.data.err_val.data);
        freak_word_release_owned(&source.data.err_val);
    }
    return handle;
}

static bool freak_fs_rename_native(const char *source,const char *destination) {
#ifdef _WIN32
    wchar_t *from = freak_command_wide(source), *to = freak_command_wide(destination);
    bool ok = MoveFileExW(from,to,MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH) != 0;
    free(from); free(to); return ok;
#else
    return rename(source,destination) == 0;
#endif
}
/* Synchronize namespace changes after the complete file is already durable.
   A post-rename synchronization error is reported; publication may have taken
   place, so callers must inspect/recover rather than assume rollback. */
static bool freak_fs_sync_parent(const char *path) {
#ifdef _WIN32
    /* MoveFileExW above requests WRITE_THROUGH; Windows does not expose a
       portable directory-fsync equivalent through this runtime contract. */
    (void)path; return true;
#else
    char *parent = freak_command_copy(freak_word_lit(path),false);
    char *slash = strrchr(parent,'/');
    if (!slash) { free(parent); parent = freak_command_copy(freak_word_lit("."),false); }
    else if (slash == parent) slash[1] = 0;
    else *slash = 0;
    int descriptor = open(parent,O_RDONLY | O_DIRECTORY | O_CLOEXEC);
    free(parent);
    if (descriptor < 0) return false;
    bool synced = fsync(descriptor) == 0;
    if (close(descriptor) != 0) synced = false;
    return synced;
#endif
}
static bool freak_fs_remove_native(const char *name) {
#ifdef _WIN32
    wchar_t *wide = freak_command_wide(name);
    bool removed = DeleteFileW(wide) != 0;
    DWORD error = GetLastError();
    bool ok = removed || error == ERROR_FILE_NOT_FOUND || error == ERROR_PATH_NOT_FOUND;
    free(wide); return ok;
#else
    return unlink(name) == 0 || errno == ENOENT;
#endif
}
static int freak_fs_exclusive_native(const char *name) {
#ifdef _WIN32
    wchar_t *wide = freak_command_wide(name);
    int descriptor = _wopen(wide,_O_WRONLY | _O_CREAT | _O_EXCL | _O_BINARY,_S_IREAD | _S_IWRITE);
    free(wide); return descriptor;
#else
    return open(name,O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC,0600);
#endif
}
static bool freak_fs_write_all(int descriptor,const unsigned char *bytes,size_t length) {
    size_t position = 0;
    while (position < length) {
        size_t remaining = length - position;
#ifdef _WIN32
        unsigned int wanted = remaining > INT_MAX ? INT_MAX : (unsigned int)remaining;
        int count = _write(descriptor,bytes + position,wanted);
#else
        size_t wanted = remaining > (size_t)SSIZE_MAX ? (size_t)SSIZE_MAX : remaining;
        ssize_t count = write(descriptor,bytes + position,wanted);
#endif
        if (count < 0 && errno == EINTR) continue;
        if (count <= 0) return false;
        position += (size_t)count;
    }
#ifdef _WIN32
    return _commit(descriptor) == 0;
#else
    return fsync(descriptor) == 0;
#endif
}
static bool freak_fs_close_write(int descriptor) {
#ifdef _WIN32
    return _close(descriptor) == 0;
#else
    return close(descriptor) == 0;
#endif
}
static uint64_t freak_fs_unique_counter = 0;
static char *freak_fs_temporary_name(const char *path) {
    size_t length = strlen(path);
    if (length > SIZE_MAX - 80) freak_command_fail("temporary path size overflow");
    char *name = freak_command_allocate(length + 80,1);
    snprintf(name,length + 80,"%s.freak-tmp-%llu-%llu-%llu",path,
            (unsigned long long)freak_process_pid(),(unsigned long long)freak_command_now_ms(),
            (unsigned long long)++freak_fs_unique_counter);
    return name;
}
static int64_t freak_fs_write_mode(freak_word path,const unsigned char *bytes,size_t length,int mode) {
    int64_t handle = freak_fs_ticket_new(); freak_fs_ticket *result = freak_fs_ticket_require(handle);
    char *name = freak_fs_checked_path(result,path); if (!name) return handle;
    char *temporary = NULL;
    int descriptor = -1;
    if (mode == 0) {
#ifdef _WIN32
        wchar_t *wide = freak_command_wide(name);
        DWORD attributes = GetFileAttributesW(wide);
        DWORD attribute_error = GetLastError();
        free(wide);
        bool safe = attributes == INVALID_FILE_ATTRIBUTES ? attribute_error == ERROR_FILE_NOT_FOUND :
            !(attributes & (FILE_ATTRIBUTE_DIRECTORY | FILE_ATTRIBUTE_REPARSE_POINT | FILE_ATTRIBUTE_DEVICE));
#else
        struct stat prior;
        bool existing = lstat(name,&prior) == 0;
        bool safe = existing ? S_ISREG(prior.st_mode) : errno == ENOENT;
#endif
        if (!safe) {
            free(name); freak_fs_ticket_error(result,"atomic write requires an absent or regular destination file"); return handle;
        }
        /* Keep the old artifact intact until a complete fsynced sibling is
           ready. Exclusive creation never follows an attacker-created link. */
        for (int attempt = 0; attempt < 128; attempt++) {
            free(temporary); temporary = freak_fs_temporary_name(name);
            descriptor = freak_fs_exclusive_native(temporary);
            if (descriptor >= 0 || errno != EEXIST) break;
        }
#ifndef _WIN32
        if (descriptor >= 0 && existing && fchmod(descriptor,prior.st_mode & 07777) != 0) {
            freak_fs_close_descriptor(descriptor); descriptor = -1;
        }
#endif
    } else if (mode == 2) descriptor = freak_fs_exclusive_native(name);
    else {
#ifdef _WIN32
        wchar_t *wide = freak_command_wide(name);
        HANDLE file = CreateFileW(wide,GENERIC_WRITE | FILE_APPEND_DATA,FILE_SHARE_READ,
                NULL,OPEN_ALWAYS,FILE_FLAG_OPEN_REPARSE_POINT,NULL);
        free(wide);
        BY_HANDLE_FILE_INFORMATION info;
        if (file != INVALID_HANDLE_VALUE) {
            if (GetFileInformationByHandle(file,&info) && GetFileType(file) == FILE_TYPE_DISK &&
                    !(info.dwFileAttributes & (FILE_ATTRIBUTE_REPARSE_POINT | FILE_ATTRIBUTE_DIRECTORY))) {
                descriptor = _open_osfhandle((intptr_t)file,_O_WRONLY | _O_APPEND | _O_BINARY);
                if (descriptor < 0) CloseHandle(file);
            } else CloseHandle(file);
        }
#else
        descriptor = open(name,O_WRONLY | O_APPEND | O_CREAT | O_NOFOLLOW | O_NONBLOCK | O_CLOEXEC,0600);
        struct stat append_info;
        if (descriptor >= 0 && (fstat(descriptor,&append_info) != 0 || !S_ISREG(append_info.st_mode))) {
            freak_fs_close_descriptor(descriptor); descriptor = -1;
        }
#endif
    }
    bool complete = descriptor >= 0 && freak_fs_write_all(descriptor,bytes,length);
    if (descriptor >= 0 && !freak_fs_close_write(descriptor)) complete = false;
    if (complete && temporary) complete = freak_fs_rename_native(temporary,name);
    bool published = complete; result->completed = published;
    if (complete) complete = freak_fs_sync_parent(name);
    if (!complete) {
        if (temporary) (void)freak_fs_remove_native(temporary);
        /* Remove only an incomplete exclusive file; a parent-sync failure
           happens after a complete artifact exists and must preserve it. */
        if (mode == 2 && descriptor >= 0 && !published) (void)freak_fs_remove_native(name);
        freak_fs_ticket_error(result,published ? "filesystem publication completed but directory synchronization failed" :
                "could not write and publish complete filesystem file");
    } else result->ok = true;
    free(temporary); free(name); return handle;
}
int64_t freak_fs_write_checked(freak_word path,freak_word contents) {
    if (!freak_byte_buffer_utf8_valid((const uint8_t *)contents.data,contents.length)) {
        int64_t handle = freak_fs_ticket_new();
        freak_fs_ticket_error(freak_fs_ticket_require(handle),"filesystem text is not NUL-free UTF-8; use binary I/O"); return handle;
    }
    return freak_fs_write_mode(path,(const unsigned char *)contents.data,contents.length,0);
}
int64_t freak_fs_write_bytes_checked(freak_word path,int64_t contents) {
    freak_byte_buffer_record *buffer = freak_byte_buffer_require(contents,"filesystem binary write");
    if (buffer->status != FREAK_BYTE_BUFFER_OK) {
        int64_t handle = freak_fs_ticket_new();
        freak_fs_ticket_error(freak_fs_ticket_require(handle),"binary buffer has a pending error"); return handle;
    }
    return freak_fs_write_mode(path,buffer->data,buffer->length,0);
}
int64_t freak_fs_append_checked(freak_word path,freak_word contents) {
    if (!freak_byte_buffer_utf8_valid((const uint8_t *)contents.data,contents.length)) {
        int64_t handle = freak_fs_ticket_new();
        freak_fs_ticket_error(freak_fs_ticket_require(handle),"filesystem text is not NUL-free UTF-8; use binary I/O"); return handle;
    }
    return freak_fs_write_mode(path,(const unsigned char *)contents.data,contents.length,1);
}
int64_t freak_fs_exclusive_create(freak_word path,freak_word contents) {
    return freak_fs_write_mode(path,(const unsigned char *)contents.data,contents.length,2);
}
int64_t freak_fs_rename_checked(freak_word source,freak_word destination) {
    int64_t handle = freak_fs_ticket_new(); freak_fs_ticket *result = freak_fs_ticket_require(handle);
    char *from = freak_fs_checked_path(result,source), *to = freak_fs_checked_path(result,destination);
    if (from && to) {
        if (freak_fs_rename_native(from,to)) {
            result->completed = true;
            if (freak_fs_sync_parent(to) && freak_fs_sync_parent(from)) result->ok = true;
            else freak_fs_ticket_error(result,"filesystem rename completed but directory synchronization failed");
        }
        else freak_fs_ticket_error(result,"could not atomically rename filesystem path");
    }
    free(from); free(to); return handle;
}
int64_t freak_fs_rename_new_checked(freak_word source,freak_word destination) {
    int64_t handle = freak_fs_ticket_new(); freak_fs_ticket *result = freak_fs_ticket_require(handle);
    char *from = freak_fs_checked_path(result,source), *to = freak_fs_checked_path(result,destination);
    if (from && to) {
        bool renamed = false, unavailable = false;
#ifdef _WIN32
        wchar_t *wide_from = freak_command_wide(from), *wide_to = freak_command_wide(to);
        renamed = MoveFileExW(wide_from,wide_to,MOVEFILE_WRITE_THROUGH) != 0;
        free(wide_from); free(wide_to);
#elif defined(__linux__) && defined(SYS_renameat2)
        renamed = syscall(SYS_renameat2,AT_FDCWD,from,AT_FDCWD,to,1 /* RENAME_NOREPLACE */) == 0;
        unavailable = !renamed && (errno == ENOSYS || errno == EINVAL || errno == EOPNOTSUPP);
#elif defined(__APPLE__)
        renamed = renamex_np(from,to,FREAK_DARWIN_RENAME_EXCL) == 0;
        unavailable = !renamed && (errno == ENOSYS || errno == ENOTSUP);
#else
        unavailable = true;
#endif
        if (renamed) {
            result->completed = true;
            if (freak_fs_sync_parent(to) && freak_fs_sync_parent(from)) result->ok = true;
            else freak_fs_ticket_error(result,"filesystem publication completed but directory synchronization failed");
        } else freak_fs_ticket_error(result,unavailable ? "atomic no-replace rename is unavailable on this host/filesystem" :
                "could not publish filesystem path without replacing destination");
    }
    free(from); free(to); return handle;
}
int64_t freak_fs_remove_checked(freak_word path) {
    int64_t handle = freak_fs_ticket_new(); freak_fs_ticket *result = freak_fs_ticket_require(handle);
    char *name = freak_fs_checked_path(result,path);
    if (name) {
        if (freak_fs_remove_native(name)) result->ok = result->completed = true;
        else freak_fs_ticket_error(result,"could not remove filesystem file");
    }
    free(name); return handle;
}
int64_t freak_fs_rmdir_checked(freak_word path) {
    int64_t handle = freak_fs_ticket_new(); freak_fs_ticket *result = freak_fs_ticket_require(handle);
    char *name = freak_fs_checked_path(result,path);
    if (name) {
#ifdef _WIN32
        wchar_t *wide = freak_command_wide(name);
        DWORD attributes = GetFileAttributesW(wide);
        bool ok = attributes != INVALID_FILE_ATTRIBUTES && !(attributes & FILE_ATTRIBUTE_REPARSE_POINT) &&
                  (attributes & FILE_ATTRIBUTE_DIRECTORY) && RemoveDirectoryW(wide);
        free(wide);
#else
        bool ok = rmdir(name) == 0;
#endif
        if (ok) result->ok = result->completed = true;
        else freak_fs_ticket_error(result,"could not remove empty filesystem directory");
    }
    free(name); return handle;
}
static bool freak_fs_mkdir_native(const char *name) {
#ifdef _WIN32
    wchar_t *wide = freak_command_wide(name);
    bool ok = CreateDirectoryW(wide,NULL) != 0;
    DWORD error = GetLastError();
    free(wide); SetLastError(error); return ok;
#else
    return mkdir(name,0700) == 0;
#endif
}
int64_t freak_fs_mkdir_checked(freak_word path) {
    int64_t handle = freak_fs_ticket_new(); freak_fs_ticket *result = freak_fs_ticket_require(handle);
    char *name = freak_fs_checked_path(result,path);
    if (name) {
        if (freak_fs_mkdir_native(name)) result->ok = result->completed = true;
        else freak_fs_ticket_error(result,"could not create filesystem directory");
    }
    free(name); return handle;
}
/* Package I/O uses directory identity, not a checked path followed by a second
   lookup. Each child is opened relative to its admitted parent with no links. */
#ifdef _WIN32
typedef HANDLE freak_fs_anchor;
#define FREAK_FS_INVALID_ANCHOR INVALID_HANDLE_VALUE
typedef struct { USHORT length, maximum; PWSTR buffer; } freak_fs_nt_string;
typedef struct { ULONG length; HANDLE root; freak_fs_nt_string *name; ULONG attributes; PVOID security, quality; } freak_fs_nt_object;
typedef struct { union { LONG status; PVOID pointer; } value; ULONG_PTR information; } freak_fs_nt_io;
typedef LONG (NTAPI *freak_fs_nt_create_fn)(PHANDLE,ACCESS_MASK,freak_fs_nt_object *,freak_fs_nt_io *,PLARGE_INTEGER,ULONG,ULONG,ULONG,ULONG,PVOID,ULONG);
static void freak_fs_anchor_close(freak_fs_anchor directory) { DWORD error=GetLastError(); if (directory != INVALID_HANDLE_VALUE) CloseHandle(directory); SetLastError(error); }
static freak_fs_anchor freak_fs_anchor_dup(freak_fs_anchor directory) {
    HANDLE copy = INVALID_HANDLE_VALUE;
    if (!DuplicateHandle(GetCurrentProcess(),directory,GetCurrentProcess(),&copy,0,FALSE,DUPLICATE_SAME_ACCESS)) return INVALID_HANDLE_VALUE;
    return copy;
}
static void freak_fs_sync_nonfinal(const char *operation);
static bool freak_fs_windows_discard_new_temp(HANDLE child);
static freak_fs_anchor freak_fs_anchor_child_mode_security(freak_fs_anchor parent,const char *name,bool directory,bool create,bool writable,bool allow_reparse,bool exclusive,PVOID security) {
    static freak_fs_nt_create_fn create_file = NULL;
    if (!create_file) create_file = (freak_fs_nt_create_fn)(void *)GetProcAddress(GetModuleHandleW(L"ntdll.dll"),"NtCreateFile");
    if (!create_file) return INVALID_HANDLE_VALUE;
    wchar_t *wide = freak_command_wide(name);
    size_t bytes = wcslen(wide) * sizeof(wchar_t);
    if (bytes > USHRT_MAX) { free(wide); return INVALID_HANDLE_VALUE; }
    freak_fs_nt_string string = {(USHORT)bytes,(USHORT)bytes,wide};
    freak_fs_nt_object object = {sizeof(object),parent,&string,0x40 /* OBJ_CASE_INSENSITIVE */,security,NULL};
    freak_fs_nt_io io={0}; io.value.status=0x103 /* STATUS_PENDING */;
    HANDLE child = INVALID_HANDLE_VALUE;
    ACCESS_MASK access = SYNCHRONIZE | FILE_READ_ATTRIBUTES | (directory ? FILE_LIST_DIRECTORY | FILE_TRAVERSE : GENERIC_READ);
    if (writable) access |= DELETE | (directory ? FILE_ADD_FILE | FILE_ADD_SUBDIRECTORY | FILE_DELETE_CHILD : GENERIC_WRITE);
    if (security) access |= READ_CONTROL;
    LONG status = create_file(&child,access,&object,&io,NULL,FILE_ATTRIBUTE_NORMAL,
        exclusive ? 0 : FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,create ? 2 /* FILE_CREATE */ : 1 /* FILE_OPEN */,
        (directory ? 1 /* FILE_DIRECTORY_FILE */ : 0x40 /* FILE_NON_DIRECTORY_FILE */) | 0x20 /* FILE_SYNCHRONOUS_IO_NONALERT */ | 0x200000 /* FILE_OPEN_REPARSE_POINT */,NULL,0);
    if (security && (status == 0x103 || (status == 0 && io.value.status == 0x103)))
        freak_fs_sync_nonfinal("owned temporary creation");
    free(wide);
    BY_HANDLE_FILE_INFORMATION info;
    if (status < 0) {
        typedef ULONG (WINAPI *convert_fn)(LONG);
        convert_fn convert=(convert_fn)(void *)GetProcAddress(GetModuleHandleW(L"ntdll.dll"),"RtlNtStatusToDosError");
        SetLastError(convert ? convert(status) : ERROR_ACCESS_DENIED); return INVALID_HANDLE_VALUE;
    }
    if (security && (status != 0 || io.value.status != 0 || io.information != 2 /* FILE_CREATED */)) {
        if (child != INVALID_HANDLE_VALUE) freak_fs_anchor_close(child);
        SetLastError(ERROR_ACCESS_DENIED); return INVALID_HANDLE_VALUE;
    }
    if (!GetFileInformationByHandle(child,&info) || GetFileType(child) != FILE_TYPE_DISK ||
        (!allow_reparse && (info.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT)) || !!(info.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) != directory) {
        if (child != INVALID_HANDLE_VALUE) {
            if (security) freak_fs_windows_discard_new_temp(child);
            CloseHandle(child);
        }
        SetLastError(ERROR_ACCESS_DENIED); return INVALID_HANDLE_VALUE;
    }
    return child;
}
static freak_fs_anchor freak_fs_anchor_child_mode(freak_fs_anchor parent,const char *name,bool directory,bool create,bool writable,bool allow_reparse,bool exclusive) {
    return freak_fs_anchor_child_mode_security(parent,name,directory,create,writable,allow_reparse,exclusive,NULL);
}
static freak_fs_anchor freak_fs_anchor_child(freak_fs_anchor parent,const char *name,bool directory,bool create,bool writable) {
    return freak_fs_anchor_child_mode(parent,name,directory,create,writable,false,false);
}
static bool freak_fs_anchor_same(freak_fs_anchor first,freak_fs_anchor second) {
    FILE_ID_INFO a,b;
    return GetFileInformationByHandleEx(first,FileIdInfo,&a,sizeof(a)) && GetFileInformationByHandleEx(second,FileIdInfo,&b,sizeof(b)) &&
        a.VolumeSerialNumber == b.VolumeSerialNumber && !memcmp(a.FileId.Identifier,b.FileId.Identifier,sizeof(a.FileId.Identifier));
}
typedef struct {
    const char *phase;
    DWORD native_error;
    int owner_match; /* -1: not examined, 0: different, 1: same */
} freak_fs_windows_parent_diagnostic;
static void freak_fs_windows_parent_note(freak_fs_windows_parent_diagnostic *diagnostic,const char *phase,DWORD error) {
    if (diagnostic) { diagnostic->phase=phase; diagnostic->native_error=error; }
}
static void freak_fs_nt_error(LONG status);
static void freak_fs_sync_nonfinal(const char *operation);
/* A READ_CONTROL ReOpenFile denial can occur on admitted directories. Limit
   this held full-ID alternative to positively identified local NTFS; it
   requests the same rights and never resolves a mutable path. */
static freak_fs_anchor freak_fs_anchor_read_control_by_id(freak_fs_anchor directory,
        freak_fs_windows_parent_diagnostic *diagnostic) {
    typedef LONG (NTAPI *query_fn)(HANDLE,freak_fs_nt_io *,PVOID,ULONG,ULONG);
    struct { ULONG device_type, characteristics; } device={0};
    BY_HANDLE_FILE_INFORMATION attributes; FILE_ID_INFO identity,current;
    HANDLE candidate=INVALID_HANDLE_VALUE;
    const char *phase=NULL; DWORD error=0;
    if (!GetFileInformationByHandle(directory,&attributes)) {
        phase="read-control-held-attrs"; error=GetLastError(); goto rejected;
    }
    if (GetFileType(directory) != FILE_TYPE_DISK || !(attributes.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) ||
            (attributes.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT)) {
        phase="read-control-held-kind"; error=ERROR_ACCESS_DENIED; goto rejected;
    }
    if (!GetFileInformationByHandleEx(directory,FileIdInfo,&identity,sizeof(identity))) {
        phase="read-control-held-id"; error=GetLastError(); goto rejected;
    }
    wchar_t filesystem[32]={0};
    if (!GetVolumeInformationByHandleW(directory,NULL,0,NULL,NULL,NULL,filesystem,32)) {
        phase="read-control-filesystem"; error=GetLastError(); goto rejected;
    }
    if (wmemcmp(filesystem,L"NTFS",5)) {
        phase="read-control-provider"; error=ERROR_NOT_SUPPORTED; goto rejected;
    }
    HMODULE native=GetModuleHandleW(L"ntdll.dll");
    query_fn query=native ? (query_fn)(void *)GetProcAddress(native,"NtQueryVolumeInformationFile") : NULL;
    if (!query) { phase="read-control-api-query"; error=ERROR_PROC_NOT_FOUND; goto rejected; }
    freak_fs_nt_io io={0}; io.value.status=0x103 /* STATUS_PENDING */;
    LONG status=query(directory,&io,&device,sizeof(device),4 /* FileFsDeviceInformation */);
    if (status == 0x103 || (status == 0 && io.value.status == 0x103)) freak_fs_sync_nonfinal("security device query");
    if (status != 0) {
        freak_fs_nt_error(status); phase="read-control-device-query"; error=GetLastError(); goto rejected;
    }
    if (io.value.status != 0) {
        freak_fs_nt_error(io.value.status); phase="read-control-device-io"; error=GetLastError(); goto rejected;
    }
    if (io.information != sizeof(device) || device.device_type != 7 /* FILE_DEVICE_DISK */ ||
            (device.characteristics & 0x10 /* FILE_REMOTE_DEVICE */)) {
        phase="read-control-local-device"; error=ERROR_NOT_SUPPORTED; goto rejected;
    }
    FILE_ID_DESCRIPTOR descriptor={0}; descriptor.dwSize=sizeof(descriptor);
    descriptor.Type=ExtendedFileIdType; descriptor.ExtendedFileId=identity.FileId;
    candidate=OpenFileById(directory,&descriptor,READ_CONTROL | FILE_READ_ATTRIBUTES | SYNCHRONIZE,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,NULL,FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT);
    if (candidate == INVALID_HANDLE_VALUE) {
        phase="read-control-open-by-id"; error=GetLastError(); goto rejected;
    }
    if (!GetFileInformationByHandle(candidate,&attributes)) {
        phase="read-control-id-attrs"; error=GetLastError(); goto rejected;
    }
    if (GetFileType(candidate) != FILE_TYPE_DISK || !(attributes.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) ||
            (attributes.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT)) {
        phase="read-control-id-kind"; error=ERROR_ACCESS_DENIED; goto rejected;
    }
    if (!GetFileInformationByHandleEx(candidate,FileIdInfo,&current,sizeof(current))) {
        phase="read-control-id-query"; error=GetLastError(); goto rejected;
    }
    if (identity.VolumeSerialNumber != current.VolumeSerialNumber ||
            memcmp(identity.FileId.Identifier,current.FileId.Identifier,sizeof(identity.FileId.Identifier))) {
        phase="read-control-id-mismatch"; error=ERROR_ACCESS_DENIED; goto rejected;
    }
    return candidate;
rejected:
    freak_fs_windows_parent_note(diagnostic,phase,error);
    freak_fs_anchor_close(candidate); SetLastError(error); return INVALID_HANDLE_VALUE;
}
/* Reopen the held object, never its mutable path, and verify its identity. */
static freak_fs_anchor freak_fs_anchor_reopen(freak_fs_anchor directory,ACCESS_MASK access,
        freak_fs_windows_parent_diagnostic *diagnostic) {
    freak_fs_anchor reopened=ReOpenFile(directory,access | FILE_READ_ATTRIBUTES | SYNCHRONIZE,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,FILE_FLAG_BACKUP_SEMANTICS);
    if (reopened == INVALID_HANDLE_VALUE) {
        DWORD error=GetLastError();
        if (access == READ_CONTROL && error == ERROR_ACCESS_DENIED)
            return freak_fs_anchor_read_control_by_id(directory,diagnostic);
        freak_fs_windows_parent_note(diagnostic,"read-control-reopen",diagnostic ? error : 0);
        return reopened;
    }
    FILE_ID_INFO original,current;
    const char *phase=NULL; DWORD error=0;
    if (!GetFileInformationByHandleEx(directory,FileIdInfo,&original,sizeof(original))) {
        phase="held-identity"; if (diagnostic) error=GetLastError();
    } else if (!GetFileInformationByHandleEx(reopened,FileIdInfo,&current,sizeof(current))) {
        phase="reopened-identity"; if (diagnostic) error=GetLastError();
    } else if (original.VolumeSerialNumber != current.VolumeSerialNumber ||
            memcmp(original.FileId.Identifier,current.FileId.Identifier,sizeof(original.FileId.Identifier))) {
        phase="identity-mismatch";
    }
    if (phase) {
        freak_fs_windows_parent_note(diagnostic,phase,error);
        freak_fs_anchor_close(reopened); SetLastError(ERROR_ACCESS_DENIED); return INVALID_HANDLE_VALUE;
    }
    return reopened;
}
/* FREAK_WINDOWS_DIRECTORY_SYNC_BEGIN: normal native directory flush is only
   supported here on positively identified local NTFS. Other providers may
   report a successful directory flush without persisting its structure. */
typedef LONG (NTAPI *freak_fs_nt_flush_ex_fn)(HANDLE,ULONG,PVOID,ULONG,freak_fs_nt_io *);
typedef LONG (NTAPI *freak_fs_nt_query_volume_fn)(HANDLE,freak_fs_nt_io *,PVOID,ULONG,ULONG);
typedef struct { ULONG device_type, characteristics; } freak_fs_nt_device;
static void freak_fs_nt_error(LONG status) {
    typedef ULONG (WINAPI *convert_fn)(LONG);
    convert_fn convert=(convert_fn)(void *)GetProcAddress(GetModuleHandleW(L"ntdll.dll"),"RtlNtStatusToDosError");
    SetLastError(convert ? convert(status) : ERROR_IO_DEVICE);
}
static void freak_fs_sync_nonfinal(const char *operation) {
    /* These handles and APIs are synchronous. A nonfinal request must not
       escape its stack IOSB/output or close its handle before completion.
       Teardown keeps those objects alive and skips reentrant exit callbacks. */
    fprintf(stderr,"FREAK runtime: nonfinal synchronous directory %s; namespace changes may have completed\n",operation);
    fflush(NULL); _Exit(1);
}
static bool freak_fs_anchor_sync(freak_fs_anchor directory) {
    DWORD previous=GetLastError();
    HMODULE native=GetModuleHandleW(L"ntdll.dll");
    freak_fs_nt_query_volume_fn query=(freak_fs_nt_query_volume_fn)(void *)GetProcAddress(native,"NtQueryVolumeInformationFile");
    freak_fs_nt_flush_ex_fn flush=(freak_fs_nt_flush_ex_fn)(void *)GetProcAddress(native,"NtFlushBuffersFileEx");
    if (!query || !flush) { SetLastError(ERROR_PROC_NOT_FOUND); return false; }
    BY_HANDLE_FILE_INFORMATION attributes; FILE_ID_INFO identity;
    if (!GetFileInformationByHandle(directory,&attributes) ||
        !GetFileInformationByHandleEx(directory,FileIdInfo,&identity,sizeof(identity))) return false;
    if (GetFileType(directory) != FILE_TYPE_DISK || !(attributes.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) ||
        (attributes.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT)) { SetLastError(ERROR_ACCESS_DENIED); return false; }
    wchar_t filesystem[32]={0};
    if (!GetVolumeInformationByHandleW(directory,NULL,0,NULL,NULL,NULL,filesystem,32)) return false;
    if (wcscmp(filesystem,L"NTFS")) { SetLastError(ERROR_NOT_SUPPORTED); return false; }
    freak_fs_nt_device device={0}; freak_fs_nt_io io={0}; io.value.status=0x103 /* STATUS_PENDING */;
    LONG status=query(directory,&io,&device,sizeof(device),4 /* FileFsDeviceInformation */);
    if (status == 0x103 || (status == 0 && io.value.status == 0x103)) freak_fs_sync_nonfinal("device query");
    if (status != 0) { freak_fs_nt_error(status); return false; }
    if (io.value.status != 0) { freak_fs_nt_error(io.value.status); return false; }
    if (io.information < sizeof(device) || device.device_type != 7 /* FILE_DEVICE_DISK */ ||
        (device.characteristics & 0x10 /* FILE_REMOTE_DEVICE */)) { SetLastError(ERROR_NOT_SUPPORTED); return false; }
    /* Open the held identity with minimum directory append access. ReOpenFile
       cannot reliably change access on the NtCreateFile-held directories.
       ExtendedFileIdType preserves all 128 bits; no path or short-ID fallback. */
    FILE_ID_DESCRIPTOR descriptor={0}; descriptor.dwSize=sizeof(descriptor);
    descriptor.Type=ExtendedFileIdType; descriptor.ExtendedFileId=identity.FileId;
    HANDLE writable=OpenFileById(directory,&descriptor,FILE_APPEND_DATA | FILE_READ_ATTRIBUTES | SYNCHRONIZE,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,NULL,FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT);
    if (writable == INVALID_HANDLE_VALUE) return false;
    FILE_ID_INFO reopened; bool synchronized=false;
    if (!GetFileInformationByHandle(writable,&attributes) ||
        !GetFileInformationByHandleEx(writable,FileIdInfo,&reopened,sizeof(reopened))) goto finish;
    if (GetFileType(writable) != FILE_TYPE_DISK || !(attributes.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) ||
        (attributes.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT) || identity.VolumeSerialNumber != reopened.VolumeSerialNumber ||
        memcmp(identity.FileId.Identifier,reopened.FileId.Identifier,sizeof(identity.FileId.Identifier))) {
        SetLastError(ERROR_ACCESS_DENIED); goto finish;
    }
    io=(freak_fs_nt_io){0}; io.value.status=0x103;
    status=flush(writable,0,NULL,0,&io);
    if (status == 0x103 || (status == 0 && io.value.status == 0x103)) freak_fs_sync_nonfinal("flush");
    if (status != 0) freak_fs_nt_error(status);
    else if (io.value.status != 0) freak_fs_nt_error(io.value.status);
    else { synchronized=true; SetLastError(previous); }
finish:
    freak_fs_anchor_close(writable); return synchronized;
}
/* FREAK_WINDOWS_DIRECTORY_SYNC_END */
/* FREAK_WINDOWS_ACL_POLICY_BEGIN: tested policy uses the native ACL layout. */
typedef BOOL (WINAPI *freak_fs_acl_valid_fn)(PACL);
typedef BOOL (WINAPI *freak_fs_ace_fn)(PACL,DWORD,PVOID *);
typedef BOOL (WINAPI *freak_fs_sid_valid_fn)(PSID);
typedef BOOL (WINAPI *freak_fs_sid_equal_fn)(PSID,PSID);
static bool freak_fs_windows_acl_private(PACL acl,PSID owner,PSID caller,PSID system,PSID administrators,
        freak_fs_acl_valid_fn acl_valid,freak_fs_ace_fn get_ace,freak_fs_sid_valid_fn sid_valid,freak_fs_sid_equal_fn sid_equal) {
    if (!owner || !caller || !sid_valid(owner) || !sid_valid(caller) || !sid_equal(owner,caller) ||
        !acl || !acl_valid(acl) || acl->AceCount > 4096) return false;
    ACCESS_MASK writes=FILE_ADD_FILE | FILE_ADD_SUBDIRECTORY | FILE_DELETE_CHILD | FILE_WRITE_EA | FILE_WRITE_ATTRIBUTES |
        DELETE | WRITE_DAC | WRITE_OWNER | GENERIC_WRITE | GENERIC_ALL | MAXIMUM_ALLOWED;
    for (DWORD index=0;index<acl->AceCount;index++) {
        PVOID pointer=NULL; if (!get_ace(acl,index,&pointer)) return false;
        uintptr_t begin=(uintptr_t)acl,position=(uintptr_t)pointer;
        if (position < begin || position-begin > acl->AclSize || acl->AclSize-(position-begin) < sizeof(ACE_HEADER)) return false;
        ACE_HEADER *header=pointer;
        if (header->AceSize < sizeof(ACE_HEADER) || header->AceSize > acl->AclSize-(position-begin)) return false;
        /* Inherit-only ACEs grant no permissions on this held parent. */
        if (header->AceFlags & INHERIT_ONLY_ACE) continue;
        if (header->AceType == ACCESS_DENIED_ACE_TYPE) continue;
        /* Conditional, compound and object ACEs are conservatively unsupported. */
        if (header->AceType != ACCESS_ALLOWED_ACE_TYPE) return false;
        if (header->AceSize < offsetof(ACCESS_ALLOWED_ACE,SidStart)+8) return false;
        ACCESS_ALLOWED_ACE *allow=pointer;
        SID *sid=(SID *)&allow->SidStart;
        size_t sid_bytes=8+(size_t)sid->SubAuthorityCount*sizeof(DWORD);
        if (sid->SubAuthorityCount > SID_MAX_SUB_AUTHORITIES || sid_bytes > header->AceSize - offsetof(ACCESS_ALLOWED_ACE,SidStart) ||
            !sid_valid(sid)) return false;
        if ((allow->Mask & writes) && !sid_equal(sid,owner) && !sid_equal(sid,system) && !sid_equal(sid,administrators)) return false;
    }
    return true;
}
/* FREAK_WINDOWS_ACL_POLICY_END */
static FARPROC freak_fs_windows_security_proc(HMODULE security,const char *name,const char *phase,
        freak_fs_windows_parent_diagnostic *diagnostic) {
    FARPROC address=GetProcAddress(security,name);
    if (!address && diagnostic && !diagnostic->phase) freak_fs_windows_parent_note(diagnostic,phase,GetLastError());
    return address;
}
static bool freak_fs_windows_parent_private(freak_fs_anchor directory,freak_fs_windows_parent_diagnostic *diagnostic) {
    /* Resolve system security APIs without changing runtime linker libraries. */
    HMODULE security=LoadLibraryExW(L"advapi32.dll",NULL,LOAD_LIBRARY_SEARCH_SYSTEM32);
    HANDLE inspected=INVALID_HANDLE_VALUE,token=NULL;
    TOKEN_USER *user=NULL; PSECURITY_DESCRIPTOR descriptor=NULL; bool private=false;
    if (!security) {
        freak_fs_windows_parent_note(diagnostic,"security-library",diagnostic ? GetLastError() : 0);
        return false;
    }
    typedef BOOL (WINAPI *open_process_fn)(HANDLE,DWORD,PHANDLE);
    typedef BOOL (WINAPI *open_thread_fn)(HANDLE,DWORD,BOOL,PHANDLE);
    typedef BOOL (WINAPI *token_info_fn)(HANDLE,TOKEN_INFORMATION_CLASS,LPVOID,DWORD,PDWORD);
    typedef DWORD (WINAPI *security_info_fn)(HANDLE,SE_OBJECT_TYPE,SECURITY_INFORMATION,PSID *,PSID *,PACL *,PACL *,PSECURITY_DESCRIPTOR *);
    typedef BOOL (WINAPI *well_known_fn)(WELL_KNOWN_SID_TYPE,PSID,PSID,DWORD *);
#define FREAK_FS_SECURITY_PROC(name) freak_fs_windows_security_proc(security,name,"api-" name,diagnostic)
    open_process_fn open_process=(open_process_fn)(void *)FREAK_FS_SECURITY_PROC("OpenProcessToken");
    open_thread_fn open_thread=(open_thread_fn)(void *)FREAK_FS_SECURITY_PROC("OpenThreadToken");
    token_info_fn token_info=(token_info_fn)(void *)FREAK_FS_SECURITY_PROC("GetTokenInformation");
    security_info_fn security_info=(security_info_fn)(void *)FREAK_FS_SECURITY_PROC("GetSecurityInfo");
    well_known_fn well_known=(well_known_fn)(void *)FREAK_FS_SECURITY_PROC("CreateWellKnownSid");
    freak_fs_acl_valid_fn acl_valid=(freak_fs_acl_valid_fn)(void *)FREAK_FS_SECURITY_PROC("IsValidAcl");
    freak_fs_ace_fn get_ace=(freak_fs_ace_fn)(void *)FREAK_FS_SECURITY_PROC("GetAce");
    freak_fs_sid_valid_fn sid_valid=(freak_fs_sid_valid_fn)(void *)FREAK_FS_SECURITY_PROC("IsValidSid");
    freak_fs_sid_equal_fn sid_equal=(freak_fs_sid_equal_fn)(void *)FREAK_FS_SECURITY_PROC("EqualSid");
#undef FREAK_FS_SECURITY_PROC
    if (!open_process || !open_thread || !token_info || !security_info || !well_known || !acl_valid || !get_ace || !sid_valid || !sid_equal) goto cleanup;
    inspected=freak_fs_anchor_reopen(directory,READ_CONTROL,diagnostic);
    if (inspected == INVALID_HANDLE_VALUE) goto cleanup;
    if (!open_thread(GetCurrentThread(),TOKEN_QUERY,TRUE,&token)) {
        DWORD error=GetLastError();
        if (error != ERROR_NO_TOKEN) { freak_fs_windows_parent_note(diagnostic,"thread-token",error); goto cleanup; }
        if (!open_process(GetCurrentProcess(),TOKEN_QUERY,&token)) {
            freak_fs_windows_parent_note(diagnostic,"process-token",diagnostic ? GetLastError() : 0); goto cleanup;
        }
    }
    DWORD needed=0;
    BOOL sized=token_info(token,TokenUser,NULL,0,&needed);
    if (needed < sizeof(TOKEN_USER) || needed > 1048576) {
        freak_fs_windows_parent_note(diagnostic,"token-user-size",diagnostic && !sized ? GetLastError() : 0); goto cleanup;
    }
    user=freak_command_allocate(needed,1);
    if (!token_info(token,TokenUser,user,needed,&needed)) {
        freak_fs_windows_parent_note(diagnostic,"token-user",diagnostic ? GetLastError() : 0); goto cleanup;
    }
    PSID owner=NULL; PACL acl=NULL;
    DWORD security_error=security_info(inspected,SE_FILE_OBJECT,OWNER_SECURITY_INFORMATION | DACL_SECURITY_INFORMATION,&owner,NULL,&acl,NULL,&descriptor);
    if (security_error != ERROR_SUCCESS) { freak_fs_windows_parent_note(diagnostic,"security-info",security_error); goto cleanup; }
    union { DWORD aligned; BYTE bytes[SECURITY_MAX_SID_SIZE]; } system,administrators;
    DWORD system_size=sizeof(system.bytes),administrators_size=sizeof(administrators.bytes);
    if (!well_known(WinLocalSystemSid,NULL,system.bytes,&system_size)) {
        freak_fs_windows_parent_note(diagnostic,"system-sid",diagnostic ? GetLastError() : 0); goto cleanup;
    }
    if (!well_known(WinBuiltinAdministratorsSid,NULL,administrators.bytes,&administrators_size)) {
        freak_fs_windows_parent_note(diagnostic,"administrators-sid",diagnostic ? GetLastError() : 0); goto cleanup;
    }
    private=freak_fs_windows_acl_private(acl,owner,user->User.Sid,system.bytes,administrators.bytes,acl_valid,get_ace,sid_valid,sid_equal);
    if (diagnostic) {
        freak_fs_windows_parent_note(diagnostic,private ? "passed" : "acl-policy",0);
        if (private) diagnostic->owner_match=1;
        else if (owner && user->User.Sid && sid_valid(owner) && sid_valid(user->User.Sid)) {
            diagnostic->owner_match=sid_equal(owner,user->User.Sid) ? 1 : 0;
        }
    }
cleanup:
    if (descriptor) LocalFree(descriptor);
    free(user); if (token) CloseHandle(token);
    freak_fs_anchor_close(inspected); FreeLibrary(security); return private;
}
static void freak_fs_windows_publication_guard_error(freak_fs_ticket *result,
        const freak_fs_windows_parent_diagnostic *source,const freak_fs_windows_parent_diagnostic *destination) {
    char reason[256];
    snprintf(reason,sizeof(reason),"file publication requires safe owned destination and source parents [source=%s,error=%lu,owner=%s;destination=%s,error=%lu,owner=%s]",
        source->phase ? source->phase : "not-examined",(unsigned long)source->native_error,
        source->owner_match < 0 ? "unknown" : source->owner_match ? "same" : "different",
        destination->phase ? destination->phase : "not-examined",(unsigned long)destination->native_error,
        destination->owner_match < 0 ? "unknown" : destination->owner_match ? "same" : "different");
    freak_fs_ticket_error(result,reason);
}
static int freak_fs_anchor_file_descriptor(freak_fs_anchor file,bool writable) {
    int descriptor = _open_osfhandle((intptr_t)file,(writable ? _O_WRONLY : _O_RDONLY) | _O_BINARY);
    if (descriptor < 0) CloseHandle(file);
    return descriptor;
}
#else
typedef int freak_fs_anchor;
#define FREAK_FS_INVALID_ANCHOR (-1)
static void freak_fs_anchor_close(freak_fs_anchor directory) { int error=errno; if (directory >= 0) close(directory); errno=error; }
static freak_fs_anchor freak_fs_anchor_dup(freak_fs_anchor directory) { return fcntl(directory,F_DUPFD_CLOEXEC,0); }
static freak_fs_anchor freak_fs_anchor_child(freak_fs_anchor parent,const char *name,bool directory,bool create,bool writable) {
    int flags = O_CLOEXEC | O_NOFOLLOW | O_NONBLOCK | (directory ? O_RDONLY | O_DIRECTORY : writable ? O_WRONLY : O_RDONLY);
    if (create && directory) { if (mkdirat(parent,name,0700) != 0) return -1; }
    if (create && !directory) flags |= O_CREAT | O_EXCL;
    int child = openat(parent,name,flags,0600);
    struct stat info;
    if (child >= 0 && fstat(child,&info) != 0) { int error=errno; close(child); errno=error; return -1; }
    if (child >= 0 && (directory ? !S_ISDIR(info.st_mode) : !S_ISREG(info.st_mode))) { close(child); errno=EINVAL; return -1; }
    return child;
}
static bool freak_fs_anchor_same(freak_fs_anchor first,freak_fs_anchor second) {
    struct stat a,b; return fstat(first,&a) == 0 && fstat(second,&b) == 0 && a.st_dev == b.st_dev && a.st_ino == b.st_ino;
}
static bool freak_fs_anchor_sync(freak_fs_anchor directory) { return fsync(directory) == 0; }
static int freak_fs_anchor_file_descriptor(freak_fs_anchor file,bool writable) { (void)writable; return file; }
#endif
static bool freak_fs_relative_valid(const char *name,bool single) {
    size_t length = strlen(name);
    if (!length || length > 4096 || name[0] == '/' || name[length-1] == '/' || strpbrk(name,":\n\r\t")) return false;
#ifdef _WIN32
    if (strchr(name,'\\')) return false;
#endif
    const char *component = name;
    for (const char *cursor = name;;cursor++) {
        if (*cursor == '/' || !*cursor) {
            size_t count = (size_t)(cursor-component);
            if (!count || (count == 1 && component[0] == '.') || (count == 2 && component[0] == '.' && component[1] == '.')) return false;
            if (!*cursor) return true;
            if (single) return false;
            component = cursor+1;
        }
    }
}
static freak_fs_anchor freak_fs_anchor_root(const char *path) {
    if (strlen(path) > 4096) {
#ifdef _WIN32
        SetLastError(ERROR_FILENAME_EXCED_RANGE);
#else
        errno=ENAMETOOLONG;
#endif
        return FREAK_FS_INVALID_ANCHOR;
    }
#ifdef _WIN32
    wchar_t *input = freak_command_wide(path);
    DWORD count = GetFullPathNameW(input,0,NULL,NULL);
    wchar_t *absolute = count ? freak_command_allocate(count+1,sizeof(wchar_t)) : NULL;
    DWORD written=count ? GetFullPathNameW(input,count+1,absolute,NULL) : 0;
    bool resolved = written && written <= count;
    free(input);
    if (!resolved) { free(absolute); return INVALID_HANDLE_VALUE; }
    for (wchar_t *p=absolute;*p;p++) if (*p == L'/') *p = L'\\';
    size_t start=0;
    if (absolute[0] == L'\\' && absolute[1] == L'\\' && absolute[2] == L'?' && absolute[3] == L'\\') {
        if (wcsncmp(absolute+4,L"UNC\\",4) == 0) memmove(absolute+2,absolute+8,(wcslen(absolute+8)+1)*sizeof(wchar_t));
        else memmove(absolute,absolute+4,(wcslen(absolute+4)+1)*sizeof(wchar_t));
    }
    if (absolute[0] && absolute[1] == L':' && absolute[2] == L'\\') start=3;
    else if (absolute[0] == L'\\' && absolute[1] == L'\\') {
        wchar_t *server_end=wcschr(absolute+2,L'\\');
        wchar_t *share_end=server_end ? wcschr(server_end+1,L'\\') : NULL;
        if (share_end) start=(size_t)(share_end-absolute)+1;
        else if (server_end && server_end[1]) start=wcslen(absolute);
    }
    if (!start) { free(absolute); SetLastError(ERROR_INVALID_NAME); return INVALID_HANDLE_VALUE; }
    wchar_t saved=absolute[start]; absolute[start]=0;
    HANDLE current = CreateFileW(absolute,FILE_LIST_DIRECTORY | FILE_TRAVERSE | FILE_READ_ATTRIBUTES | SYNCHRONIZE,
        FILE_SHARE_READ | FILE_SHARE_WRITE,NULL,OPEN_EXISTING,FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT,NULL);
    absolute[start]=saved;
    BY_HANDLE_FILE_INFORMATION root_info;
    if (current != INVALID_HANDLE_VALUE && (!GetFileInformationByHandle(current,&root_info) ||
        !(root_info.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) || (root_info.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT))) {
        CloseHandle(current); current=INVALID_HANDLE_VALUE;
    }
    int utf8_size=WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,absolute+start,-1,NULL,0,NULL,NULL);
    char *tail=utf8_size > 0 ? freak_command_allocate((size_t)utf8_size,1) : NULL;
    if (tail) WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,absolute+start,-1,tail,utf8_size,NULL,NULL);
    free(absolute);
    if (!tail) { freak_fs_anchor_close(current); return INVALID_HANDLE_VALUE; }
    for (char *p=tail;*p;p++) if (*p == '\\') *p='/';
#else
    freak_fs_anchor current = open(path[0] == '/' ? "/" : ".",O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
    /* The checked external path is nonempty; '/' has an empty internal tail. */
    char *tail=freak_command_copy(freak_word_lit(path[0] == '/' ? path+1 : path),true);
#endif
    char *cursor=tail;
    while (*cursor && current != FREAK_FS_INVALID_ANCHOR) {
        while (*cursor == '/') cursor++;
        if (!*cursor) break;
        char *slash=strchr(cursor,'/'); if (slash) *slash=0;
        if (strcmp(cursor,".") != 0) {
            /* A physical POSIX host component is not a portable manifest path.
               The descriptor walk still refuses parent traversal and links. */
#ifdef _WIN32
            bool valid=freak_fs_relative_valid(cursor,true);
#else
            bool valid=strcmp(cursor,"..") != 0;
#endif
            if (!valid) {
                freak_fs_anchor_close(current); current=FREAK_FS_INVALID_ANCHOR;
#ifdef _WIN32
                SetLastError(ERROR_INVALID_NAME);
#else
                errno=EINVAL;
#endif
                break;
            }
            freak_fs_anchor next=freak_fs_anchor_child(current,cursor,true,false,false);
            freak_fs_anchor_close(current); current=next;
        }
        if (!slash) break;
        cursor=slash+1;
    }
    free(tail); return current;
}
static freak_fs_anchor freak_fs_anchor_parent(freak_fs_ticket *root,char *relative,char **leaf) {
    freak_fs_anchor current=freak_fs_anchor_dup(root->directory);
    char *cursor=relative,*slash;
    while (current != FREAK_FS_INVALID_ANCHOR && (slash=strchr(cursor,'/')) != NULL) {
        *slash=0;
        freak_fs_anchor next=freak_fs_anchor_child(current,cursor,true,false,false);
        freak_fs_anchor_close(current); current=next; cursor=slash+1;
    }
    *leaf=cursor; return current;
}
static freak_fs_ticket *freak_fs_directory_require(int64_t handle) {
    freak_fs_ticket *root=freak_fs_ticket_require(handle);
    if (!root->ok || !root->has_directory || root->kind != 2) freak_command_fail("filesystem operation requires a successful directory ticket");
    return root;
}
int64_t freak_fs_open_dir_ticket(freak_word path) {
    int64_t handle=freak_fs_ticket_new(); freak_fs_ticket *result=freak_fs_ticket_require(handle);
    char *name=freak_fs_checked_path(result,path); if (!name) return handle;
    freak_fs_anchor directory=freak_fs_anchor_root(name);
    if (directory == FREAK_FS_INVALID_ANCHOR) { result->missing=freak_fs_failure_missing(); freak_fs_ticket_error(result,"could not open anchored directory without following links"); }
    else { freak_fs_ticket_data(result,name,strlen(name)); result->directory=directory; result->has_directory=true; result->kind=2; }
    free(name); return handle;
}
/* The limit applies to the bytes actually read. A growth race gets at most one
   extra byte for detection and can never cause an unbounded allocation/read. */
static int64_t freak_fs_read_descriptor(int64_t handle,int descriptor,bool text,bool source,size_t limit) {
    freak_fs_ticket *result=freak_fs_ticket_require(handle);
#ifdef _WIN32
    struct _stat64 metadata;
    bool regular=_fstat64(descriptor,&metadata) == 0 && (metadata.st_mode & _S_IFMT) == _S_IFREG;
#else
    struct stat metadata;
    bool regular=fstat(descriptor,&metadata) == 0 && S_ISREG(metadata.st_mode);
#endif
    if (!regular || metadata.st_size < 0 || (uintmax_t)metadata.st_size > limit) {
        freak_fs_close_descriptor(descriptor); freak_fs_ticket_error(result,"filesystem file is not regular or exceeds bounded read limit"); return handle;
    }
#ifndef _WIN32
    /* Preserve permissions from the same admitted file, without a path lookup.
       Windows has no corresponding POSIX permission mode; its value stays 0. */
    result->mode=(int64_t)(metadata.st_mode & 07777);
#endif
    size_t capacity=(size_t)metadata.st_size+1, length=0;
    if (capacity > limit+1) capacity=limit+1;
    unsigned char *data=freak_command_allocate(capacity,1); bool complete=true;
    for (;;) {
        if (length == capacity) {
            size_t next=capacity < 4096 ? 4096 : capacity*2;
            if (next > limit+1) next=limit+1;
            if (next <= capacity) { complete=false; break; }
            unsigned char *grown=realloc(data,next); if (!grown) freak_command_fail("out of memory reading bounded filesystem file");
            data=grown; capacity=next;
        }
#ifdef _WIN32
        unsigned int wanted=capacity-length > INT_MAX ? INT_MAX : (unsigned int)(capacity-length);
        int count=_read(descriptor,data+length,wanted);
#else
        ssize_t count=read(descriptor,data+length,capacity-length);
#endif
        if (count < 0 && errno == EINTR) continue;
        if (count < 0) { complete=false; break; }
        if (!count) break;
        length+=(size_t)count;
        if (length > limit) { complete=false; break; }
    }
    if (!freak_fs_close_write(descriptor)) complete=false;
    if (!complete || (text && !freak_byte_buffer_utf8_valid(data,length))) {
        free(data); freak_fs_ticket_error(result,!complete ? "filesystem file exceeded limit or could not be read completely" : "filesystem text is not NUL-free UTF-8; use binary I/O"); return handle;
    }
    unsigned char *terminated=realloc(data,length+1); if (!terminated) freak_command_fail("out of memory completing filesystem read");
    terminated[length]=0; result->data=terminated; result->length=length; result->size=(int64_t)length; result->ok=true; result->source_text=source;
    return handle;
}
int64_t freak_fs_read_bytes_limit_ticket(freak_word path,int64_t limit) {
    int64_t handle=freak_fs_ticket_new(); freak_fs_ticket *result=freak_fs_ticket_require(handle);
    if (limit < 0 || (uint64_t)limit > FREAK_FS_READ_LIMIT) { freak_fs_ticket_error(result,"filesystem read limit must be 0..64 MiB"); return handle; }
    char *name=freak_fs_checked_path(result,path); if (!name) return handle;
    int descriptor=freak_fs_open_read(name); result->missing=descriptor < 0 && freak_fs_failure_missing(); free(name);
    if (descriptor < 0) { freak_fs_ticket_error(result,"could not open bounded filesystem file"); return handle; }
    return freak_fs_read_descriptor(handle,descriptor,false,false,(size_t)limit);
}
static int64_t freak_fs_read_relative_mode(int64_t root_handle,freak_word path,int64_t limit,bool text,bool source) {
    /* Allocate the result first: growing the ticket table may move root. */
    int64_t handle=freak_fs_ticket_new(); freak_fs_ticket *result=freak_fs_ticket_require(handle);
    freak_fs_ticket *root=freak_fs_directory_require(root_handle);
    if (limit < 0 || (uint64_t)limit > FREAK_FS_READ_LIMIT) { freak_fs_ticket_error(result,"filesystem read limit must be 0..64 MiB"); return handle; }
    char *name=freak_fs_checked_path(result,path); if (!name) return handle;
    if (!freak_fs_relative_valid(name,false)) { free(name); freak_fs_ticket_error(result,"filesystem relative path has unsafe components"); return handle; }
    char *leaf; freak_fs_anchor parent=freak_fs_anchor_parent(root,name,&leaf);
    freak_fs_anchor file=parent == FREAK_FS_INVALID_ANCHOR ? FREAK_FS_INVALID_ANCHOR : freak_fs_anchor_child(parent,leaf,false,false,false);
    result->missing=file == FREAK_FS_INVALID_ANCHOR && freak_fs_failure_missing();
    freak_fs_anchor_close(parent); free(name);
    if (file == FREAK_FS_INVALID_ANCHOR) { freak_fs_ticket_error(result,"could not read anchored regular file without following links"); return handle; }
    int descriptor=freak_fs_anchor_file_descriptor(file,false);
    if (descriptor < 0) { freak_fs_ticket_error(result,"could not open anchored filesystem stream"); return handle; }
    return freak_fs_read_descriptor(handle,descriptor,text,source,(size_t)limit);
}
int64_t freak_fs_read_relative_ticket(int64_t root,freak_word relative) { return freak_fs_read_relative_mode(root,relative,FREAK_FS_READ_LIMIT,true,false); }
int64_t freak_fs_read_source_relative_ticket(int64_t root,freak_word relative) { return freak_fs_read_relative_mode(root,relative,FREAK_FS_READ_LIMIT,false,true); }
int64_t freak_fs_read_relative_bytes_ticket(int64_t root,freak_word relative) { return freak_fs_read_relative_mode(root,relative,FREAK_FS_READ_LIMIT,false,false); }
int64_t freak_fs_read_relative_bytes_limit_ticket(int64_t root,freak_word relative,int64_t limit) { return freak_fs_read_relative_mode(root,relative,limit,false,false); }
#ifdef _WIN32
typedef LONG (NTAPI *freak_fs_nt_set_fn)(HANDLE,freak_fs_nt_io *,PVOID,ULONG,ULONG);
static bool freak_fs_anchor_set_information(HANDLE item,void *information,size_t length,ULONG kind) {
    freak_fs_nt_set_fn set_information=(freak_fs_nt_set_fn)(void *)GetProcAddress(GetModuleHandleW(L"ntdll.dll"),"NtSetInformationFile");
    if (!set_information || length > ULONG_MAX) return false;
    freak_fs_nt_io io;
    return set_information(item,&io,information,(ULONG)length,kind) >= 0;
}
static bool freak_fs_anchor_delete_handle(HANDLE item) {
    BOOLEAN dispose=TRUE;
    return freak_fs_anchor_set_information(item,&dispose,sizeof(dispose),13 /* FileDispositionInformation */);
}
/* Only a terminal FILE_CREATED response grants ownership of this new empty
   identity. Never unwind a pending request's IOSB or dispose it by its name. */
static bool freak_fs_windows_discard_new_temp(HANDLE child) {
    freak_fs_nt_set_fn set=(freak_fs_nt_set_fn)(void *)GetProcAddress(GetModuleHandleW(L"ntdll.dll"),"NtSetInformationFile");
    if (!set) return false;
    BOOLEAN dispose=TRUE; freak_fs_nt_io io={0}; io.value.status=0x103;
    LONG status=set(child,&io,&dispose,sizeof(dispose),13 /* FileDispositionInformation */);
    if (status == 0x103 || (status == 0 && io.value.status == 0x103))
        freak_fs_sync_nonfinal("owned temporary cleanup");
    return status == 0 && io.value.status == 0;
}
/* Bound all returned descriptor components before validating their contents. */
static bool freak_fs_windows_temp_span(const void *base,size_t size,const void *pointer,size_t length) {
    uintptr_t begin=(uintptr_t)base,position=(uintptr_t)pointer;
    return pointer && position >= begin && position-begin <= size && length <= size-(position-begin);
}
static bool freak_fs_windows_temp_sid(const void *base,size_t size,PSID pointer,freak_fs_sid_valid_fn valid) {
    if (!freak_fs_windows_temp_span(base,size,pointer,8) || (uintptr_t)pointer % _Alignof(SID)) return false;
    SID *sid=pointer;
    size_t length=8+(size_t)sid->SubAuthorityCount*sizeof(DWORD);
    return sid->SubAuthorityCount <= SID_MAX_SUB_AUTHORITIES &&
        freak_fs_windows_temp_span(base,size,pointer,length) && valid(pointer);
}
/* Like Unix mkdir(0700), owned temps receive a private creation-time DACL.
   Explicit effective-user ownership also handles group-default tokens. Only
   this new object receives the descriptor; existing parents and token defaults
   stay intact. Its absolute SD references live bounded SID and ACL storage. */
static freak_fs_anchor freak_fs_windows_owned_temp(freak_fs_anchor parent,const char *name,bool *retryable) {
    *retryable=false;
    HANDLE child=INVALID_HANDLE_VALUE,token=NULL;
    TOKEN_USER *user=NULL; PSECURITY_DESCRIPTOR returned=NULL;
    DWORD error=ERROR_ACCESS_DENIED;
    HMODULE security=LoadLibraryExW(L"advapi32.dll",NULL,LOAD_LIBRARY_SEARCH_SYSTEM32);
    if (!security) return INVALID_HANDLE_VALUE;
    typedef BOOL (WINAPI *open_process_fn)(HANDLE,DWORD,PHANDLE);
    typedef BOOL (WINAPI *open_thread_fn)(HANDLE,DWORD,BOOL,PHANDLE);
    typedef BOOL (WINAPI *token_info_fn)(HANDLE,TOKEN_INFORMATION_CLASS,LPVOID,DWORD,PDWORD);
    typedef BOOL (WINAPI *init_fn)(PSECURITY_DESCRIPTOR,DWORD);
    typedef BOOL (WINAPI *owner_fn)(PSECURITY_DESCRIPTOR,PSID,BOOL);
    typedef BOOL (WINAPI *init_acl_fn)(PACL,DWORD,DWORD);
    typedef BOOL (WINAPI *add_ace_fn)(PACL,DWORD,DWORD,DWORD,PSID);
    typedef BOOL (WINAPI *dacl_fn)(PSECURITY_DESCRIPTOR,BOOL,PACL,BOOL);
    typedef BOOL (WINAPI *control_fn)(PSECURITY_DESCRIPTOR,SECURITY_DESCRIPTOR_CONTROL,SECURITY_DESCRIPTOR_CONTROL);
    typedef BOOL (WINAPI *get_control_fn)(PSECURITY_DESCRIPTOR,PSECURITY_DESCRIPTOR_CONTROL,LPDWORD);
    typedef DWORD (WINAPI *length_fn)(PSECURITY_DESCRIPTOR);
    typedef DWORD (WINAPI *info_fn)(HANDLE,SE_OBJECT_TYPE,SECURITY_INFORMATION,PSID *,PSID *,PACL *,PACL *,PSECURITY_DESCRIPTOR *);
    open_process_fn open_process=(open_process_fn)(void *)GetProcAddress(security,"OpenProcessToken");
    open_thread_fn open_thread=(open_thread_fn)(void *)GetProcAddress(security,"OpenThreadToken");
    token_info_fn token_info=(token_info_fn)(void *)GetProcAddress(security,"GetTokenInformation");
    init_fn initialize=(init_fn)(void *)GetProcAddress(security,"InitializeSecurityDescriptor");
    owner_fn set_owner=(owner_fn)(void *)GetProcAddress(security,"SetSecurityDescriptorOwner");
    init_acl_fn initialize_acl=(init_acl_fn)(void *)GetProcAddress(security,"InitializeAcl");
    add_ace_fn add_ace=(add_ace_fn)(void *)GetProcAddress(security,"AddAccessAllowedAceEx");
    dacl_fn set_dacl=(dacl_fn)(void *)GetProcAddress(security,"SetSecurityDescriptorDacl");
    control_fn set_control=(control_fn)(void *)GetProcAddress(security,"SetSecurityDescriptorControl");
    get_control_fn get_control=(get_control_fn)(void *)GetProcAddress(security,"GetSecurityDescriptorControl");
    length_fn get_length=(length_fn)(void *)GetProcAddress(security,"GetSecurityDescriptorLength");
    freak_fs_acl_valid_fn valid_acl=(freak_fs_acl_valid_fn)(void *)GetProcAddress(security,"IsValidAcl");
    freak_fs_ace_fn get_ace=(freak_fs_ace_fn)(void *)GetProcAddress(security,"GetAce");
    info_fn get_info=(info_fn)(void *)GetProcAddress(security,"GetSecurityInfo");
    freak_fs_sid_valid_fn valid=(freak_fs_sid_valid_fn)(void *)GetProcAddress(security,"IsValidSid");
    freak_fs_sid_equal_fn equal=(freak_fs_sid_equal_fn)(void *)GetProcAddress(security,"EqualSid");
    if (!open_process || !open_thread || !token_info || !initialize || !set_owner || !initialize_acl || !add_ace ||
        !set_dacl || !set_control || !get_control || !get_length || !valid_acl || !get_ace || !get_info || !valid || !equal) {
        error=ERROR_PROC_NOT_FOUND; goto cleanup;
    }
    HANDLE candidate=NULL;
    if (open_thread(GetCurrentThread(),TOKEN_QUERY,TRUE,&candidate)) token=candidate;
    else {
        error=GetLastError();
        if (error != ERROR_NO_TOKEN) goto cleanup;
        candidate=NULL;
        if (!open_process(GetCurrentProcess(),TOKEN_QUERY,&candidate)) { error=GetLastError(); goto cleanup; }
        token=candidate;
    }
    DWORD needed=0;
    BOOL sized=token_info(token,TokenUser,NULL,0,&needed);
    if (sized || GetLastError() != ERROR_INSUFFICIENT_BUFFER || needed < sizeof(TOKEN_USER) || needed > 1048576) {
        error=ERROR_INVALID_DATA; goto cleanup;
    }
    DWORD capacity=needed; user=freak_command_allocate(capacity,1);
    if (!token_info(token,TokenUser,user,capacity,&needed)) { error=GetLastError(); goto cleanup; }
    if (needed < sizeof(TOKEN_USER) || needed > capacity || !user->User.Sid) { error=ERROR_INVALID_SID; goto cleanup; }
    uintptr_t begin=(uintptr_t)user,position=(uintptr_t)user->User.Sid;
    if (position < begin || position-begin > needed || needed-(position-begin) < 8 || position % _Alignof(SID)) {
        error=ERROR_INVALID_SID; goto cleanup;
    }
    SID *sid=(SID *)user->User.Sid;
    size_t length=8+(size_t)sid->SubAuthorityCount*sizeof(DWORD);
    if (sid->SubAuthorityCount > SID_MAX_SUB_AUTHORITIES || length > needed-(position-begin) || !valid(sid)) {
        error=ERROR_INVALID_SID; goto cleanup;
    }
    SECURITY_DESCRIPTOR descriptor;
    union { DWORD aligned; BYTE bytes[sizeof(ACL)+offsetof(ACCESS_ALLOWED_ACE,SidStart)+SECURITY_MAX_SID_SIZE]; } acl_storage;
    PACL private_acl=(PACL)acl_storage.bytes;
    if (!initialize(&descriptor,SECURITY_DESCRIPTOR_REVISION) || !set_owner(&descriptor,sid,FALSE) ||
        !initialize_acl(private_acl,sizeof(acl_storage.bytes),ACL_REVISION) ||
        !add_ace(private_acl,ACL_REVISION,OBJECT_INHERIT_ACE | CONTAINER_INHERIT_ACE,FILE_ALL_ACCESS,sid) ||
        !set_dacl(&descriptor,TRUE,private_acl,FALSE) ||
        !set_control(&descriptor,SE_DACL_PROTECTED,SE_DACL_PROTECTED)) {
        error=GetLastError(); goto cleanup;
    }
    child=freak_fs_anchor_child_mode_security(parent,name,true,true,true,false,false,&descriptor);
    if (child == INVALID_HANDLE_VALUE) {
        error=GetLastError(); *retryable=error == ERROR_ALREADY_EXISTS || error == ERROR_FILE_EXISTS; goto cleanup;
    }
    PSID actual=NULL; PACL actual_acl=NULL;
    error=get_info(child,SE_FILE_OBJECT,OWNER_SECURITY_INFORMATION | DACL_SECURITY_INFORMATION,&actual,NULL,&actual_acl,NULL,&returned);
    if (error != ERROR_SUCCESS) goto reject;
    if (!returned) { error=ERROR_INVALID_SECURITY_DESCR; goto reject; }
    DWORD returned_size=get_length(returned),revision=0; SECURITY_DESCRIPTOR_CONTROL control=0;
    if (returned_size < sizeof(SECURITY_DESCRIPTOR_RELATIVE) || returned_size > 1048576) {
        error=ERROR_INVALID_SECURITY_DESCR; goto reject;
    }
    if (!get_control(returned,&control,&revision)) { error=GetLastError(); goto reject; }
    if (revision != SECURITY_DESCRIPTOR_REVISION ||
        (control & (SE_SELF_RELATIVE | SE_DACL_PRESENT | SE_DACL_PROTECTED)) != (SE_SELF_RELATIVE | SE_DACL_PRESENT | SE_DACL_PROTECTED)) {
        error=ERROR_INVALID_SECURITY_DESCR; goto reject;
    }
    if (!freak_fs_windows_temp_sid(returned,returned_size,actual,valid) || !equal(actual,sid)) {
        error=ERROR_INVALID_OWNER; goto reject;
    }
    if (!freak_fs_windows_temp_span(returned,returned_size,actual_acl,sizeof(ACL)) || (uintptr_t)actual_acl % _Alignof(ACL) ||
        actual_acl->AclRevision != ACL_REVISION || actual_acl->AceCount != 1 || actual_acl->AclSize < sizeof(ACL) ||
        !freak_fs_windows_temp_span(returned,returned_size,actual_acl,actual_acl->AclSize) || !valid_acl(actual_acl)) {
        error=ERROR_INVALID_ACL; goto reject;
    }
    PVOID pointer=NULL;
    if (!get_ace(actual_acl,0,&pointer)) { error=GetLastError(); goto reject; }
    if (!freak_fs_windows_temp_span(actual_acl,actual_acl->AclSize,pointer,offsetof(ACCESS_ALLOWED_ACE,SidStart)+8) ||
        (uintptr_t)pointer % _Alignof(ACCESS_ALLOWED_ACE)) {
        error=ERROR_INVALID_ACL; goto reject;
    }
    ACCESS_ALLOWED_ACE *allow=pointer; SID *granted=(SID *)&allow->SidStart;
    size_t granted_size=8+(size_t)granted->SubAuthorityCount*sizeof(DWORD);
    if (allow->Header.AceType != ACCESS_ALLOWED_ACE_TYPE ||
        allow->Header.AceFlags != (OBJECT_INHERIT_ACE | CONTAINER_INHERIT_ACE) ||
        allow->Header.AceSize != offsetof(ACCESS_ALLOWED_ACE,SidStart)+granted_size ||
        !freak_fs_windows_temp_span(actual_acl,actual_acl->AclSize,allow,allow->Header.AceSize) ||
        allow->Mask != FILE_ALL_ACCESS || !freak_fs_windows_temp_sid(allow,allow->Header.AceSize,granted,valid) || !equal(granted,sid)) {
        error=ERROR_INVALID_ACL; goto reject;
    }
    error=ERROR_SUCCESS;
    goto cleanup;
reject:
    freak_fs_windows_discard_new_temp(child); freak_fs_anchor_close(child); child=INVALID_HANDLE_VALUE;
cleanup:
    if (returned) LocalFree(returned);
    free(user); if (token) CloseHandle(token); FreeLibrary(security);
    SetLastError(error); return child;
}
#endif
static bool freak_fs_anchor_delete(freak_fs_anchor parent,const char *leaf,bool directory) {
#ifdef _WIN32
    HANDLE item=freak_fs_anchor_child(parent,leaf,directory,false,true);
    if (item == INVALID_HANDLE_VALUE) return false;
    bool ok=freak_fs_anchor_delete_handle(item);
    CloseHandle(item); return ok;
#else
    return unlinkat(parent,leaf,directory ? AT_REMOVEDIR : 0) == 0;
#endif
}
#ifdef _WIN32
static bool freak_fs_anchor_rename_handle(HANDLE item,HANDLE destination,const char *to,bool replace) {
    wchar_t *name=freak_command_wide(to); size_t bytes=wcslen(name)*sizeof(wchar_t);
    size_t size=offsetof(FILE_RENAME_INFO,FileName)+bytes;
    FILE_RENAME_INFO *rename_info=freak_command_allocate(size,1);
    rename_info->ReplaceIfExists=replace; rename_info->RootDirectory=destination; rename_info->FileNameLength=(DWORD)bytes;
    memcpy(rename_info->FileName,name,bytes);
    bool renamed=freak_fs_anchor_set_information(item,rename_info,size,10 /* FileRenameInformation */);
    free(name); free(rename_info); return renamed;
}
#endif
static bool freak_fs_anchor_rename(freak_fs_anchor source,const char *from,freak_fs_anchor destination,const char *to,bool replace) {
#ifdef _WIN32
    HANDLE item=freak_fs_anchor_child(source,from,false,false,true);
    if (item == INVALID_HANDLE_VALUE) item=freak_fs_anchor_child(source,from,true,false,true);
    if (item == INVALID_HANDLE_VALUE) return false;
    bool renamed=freak_fs_anchor_rename_handle(item,destination,to,replace);
    CloseHandle(item); return renamed;
#else
    if (replace) return renameat(source,from,destination,to) == 0;
#if defined(__linux__) && defined(SYS_renameat2)
    return syscall(SYS_renameat2,source,from,destination,to,1) == 0;
#elif defined(__APPLE__)
    extern int renameatx_np(int,const char *,int,const char *,unsigned int);
    return renameatx_np(source,from,destination,to,FREAK_DARWIN_RENAME_EXCL) == 0;
#else
    errno=ENOTSUP; return false;
#endif
#endif
}
/* Publish a compiler-created ordinary file through retained parent identities.
   POSIX entry exchange by the same effective user cannot be made conditional
   on an inode by renameat2: callers must control entries during the transaction.
   Reject parents writable by another uid/group; ordinary 0755 output folders
   remain usable. Windows callers retain the equivalent ACL/transaction control. */
int64_t freak_fs_rename_relative_new_checked(int64_t source_handle,freak_word source_relative,
        int64_t destination_handle,freak_word destination_relative) {
    int64_t handle=freak_fs_ticket_new(); freak_fs_ticket *result=freak_fs_ticket_require(handle);
    freak_fs_ticket *source_root=freak_fs_directory_require(source_handle),*destination_root=freak_fs_directory_require(destination_handle);
    char *from=freak_fs_checked_path(result,source_relative),*to=freak_fs_checked_path(result,destination_relative);
    if (!from || !to) { free(from); free(to); return handle; }
    if (!freak_fs_relative_valid(from,false) || !freak_fs_relative_valid(to,false)) {
        free(from); free(to); freak_fs_ticket_error(result,"file publication relative path has unsafe components"); return handle;
    }
    char *source_leaf,*destination_leaf;
#ifdef _WIN32
    freak_fs_windows_parent_diagnostic source_diagnostic={NULL,0,-1},destination_diagnostic={NULL,0,-1};
#endif
    freak_fs_anchor source_parent=freak_fs_anchor_parent(source_root,from,&source_leaf);
#ifdef _WIN32
    if (source_parent == FREAK_FS_INVALID_ANCHOR) freak_fs_windows_parent_note(&source_diagnostic,"parent-acquisition",GetLastError());
#endif
    freak_fs_anchor destination_parent=freak_fs_anchor_parent(destination_root,to,&destination_leaf);
#ifdef _WIN32
    if (destination_parent == FREAK_FS_INVALID_ANCHOR) freak_fs_windows_parent_note(&destination_diagnostic,"parent-acquisition",GetLastError());
#endif
    freak_fs_anchor file=FREAK_FS_INVALID_ANCHOR;
    bool private_parents=source_parent != FREAK_FS_INVALID_ANCHOR && destination_parent != FREAK_FS_INVALID_ANCHOR;
#ifdef _WIN32
    private_parents=private_parents && freak_fs_windows_parent_private(source_parent,&source_diagnostic) &&
        freak_fs_windows_parent_private(destination_parent,&destination_diagnostic);
#else
    struct stat source_info,destination_info;
    private_parents=private_parents && fstat(source_parent,&source_info) == 0 && fstat(destination_parent,&destination_info) == 0 &&
        source_info.st_uid == geteuid() && destination_info.st_uid == geteuid() &&
        !(source_info.st_mode & 0022) && !(destination_info.st_mode & 0022);
#endif
    if (private_parents) file=freak_fs_anchor_child(source_parent,source_leaf,false,false,
#ifdef _WIN32
        true /* retained HANDLE needs DELETE and write access for flush */
#else
        false
#endif
    );
    bool complete=false;
    if (file != FREAK_FS_INVALID_ANCHOR) {
#ifdef _WIN32
        complete=FlushFileBuffers(file) && freak_fs_anchor_rename_handle(file,destination_parent,destination_leaf,false);
#else
        struct stat admitted,current;
        complete=fstat(file,&admitted) == 0 && fsync(file) == 0 &&
            fstatat(source_parent,source_leaf,&current,AT_SYMLINK_NOFOLLOW) == 0 &&
            S_ISREG(current.st_mode) && current.st_dev == admitted.st_dev && current.st_ino == admitted.st_ino &&
            freak_fs_anchor_rename(source_parent,source_leaf,destination_parent,destination_leaf,false);
#endif
    }
    result->completed=complete;
    if (complete) {
        freak_fs_anchor published=freak_fs_anchor_child(destination_parent,destination_leaf,false,false,false);
        bool same=published != FREAK_FS_INVALID_ANCHOR && freak_fs_anchor_same(file,published);
        freak_fs_anchor_close(published);
        bool source_synced=freak_fs_anchor_sync(source_parent),destination_synced=freak_fs_anchor_sync(destination_parent);
        if (same && source_synced && destination_synced) result->ok=true;
        else freak_fs_ticket_error(result,same ? "file publication completed but directory synchronization failed" :
            "file publication completed but destination identity changed during rename");
#ifdef _WIN32
    } else {
        if (!private_parents) freak_fs_windows_publication_guard_error(result,&source_diagnostic,&destination_diagnostic);
        else freak_fs_ticket_error(result,"could not synchronize and publish ordinary file without replacing destination");
    }
#else
    } else freak_fs_ticket_error(result,private_parents ? "could not synchronize and publish ordinary file without replacing destination" :
        "file publication requires safe owned destination and source parents");
#endif
    freak_fs_anchor_close(file); freak_fs_anchor_close(source_parent); freak_fs_anchor_close(destination_parent);
    free(from); free(to); return handle;
}
int64_t freak_fs_set_mode_relative_checked(int64_t root_handle,freak_word relative,int64_t mode) {
    int64_t handle=freak_fs_ticket_new(); freak_fs_ticket *result=freak_fs_ticket_require(handle);
    freak_fs_ticket *root=freak_fs_directory_require(root_handle);
    if (mode < 0 || mode > 0777) { freak_fs_ticket_error(result,"filesystem permission mode must be 0..0777 without privilege bits"); return handle; }
    char *name=freak_fs_checked_path(result,relative); if (!name) return handle;
    if (!freak_fs_relative_valid(name,false)) { free(name); freak_fs_ticket_error(result,"filesystem relative path has unsafe components"); return handle; }
#ifdef _WIN32
    free(name); freak_fs_ticket_error(result,"POSIX permission modes are not supported on Windows"); return handle;
#else
    char *leaf; freak_fs_anchor parent=freak_fs_anchor_parent(root,name,&leaf);
    struct stat parent_info,admitted,current;
    bool safe=parent >= 0 && fstat(parent,&parent_info) == 0 && parent_info.st_uid == geteuid() && !(parent_info.st_mode & 0022);
    freak_fs_anchor file=safe ? freak_fs_anchor_child(parent,leaf,false,false,false) : FREAK_FS_INVALID_ANCHOR;
    safe=file >= 0 && fstat(file,&admitted) == 0 && admitted.st_uid == geteuid() && admitted.st_nlink == 1 &&
        fstatat(parent,leaf,&current,AT_SYMLINK_NOFOLLOW) == 0 && S_ISREG(current.st_mode) &&
        current.st_dev == admitted.st_dev && current.st_ino == admitted.st_ino;
    bool changed=safe && fchmod(file,(mode_t)mode) == 0;
    result->completed=changed;
    bool synchronized=changed && fsync(file) == 0;
    bool same=changed && fstat(file,&current) == 0 && current.st_uid == geteuid() && current.st_nlink == 1 &&
        (current.st_mode & 07777) == (mode_t)mode &&
        fstatat(parent,leaf,&current,AT_SYMLINK_NOFOLLOW) == 0 && S_ISREG(current.st_mode) &&
        current.st_dev == admitted.st_dev && current.st_ino == admitted.st_ino;
    bool closed=file < 0 || freak_fs_close_write(file);
    if (changed && synchronized && same && closed) result->ok=true;
    else freak_fs_ticket_error(result,changed ? "permission mode changed but synchronization, close or identity verification failed" :
        "could not set permission mode on owned single-link ordinary file in safe parent");
    freak_fs_anchor_close(parent); free(name); return handle;
#endif
}
int64_t freak_fs_write_relative_bytes_checked(int64_t root_handle,freak_word relative,int64_t bytes_handle) {
    freak_byte_buffer_record *buffer=freak_byte_buffer_require(bytes_handle,"anchored filesystem binary write");
    int64_t handle=freak_fs_ticket_new(); freak_fs_ticket *result=freak_fs_ticket_require(handle);
    freak_fs_ticket *root=freak_fs_directory_require(root_handle);
    if (buffer->status != FREAK_BYTE_BUFFER_OK) { freak_fs_ticket_error(result,"binary buffer has a pending error"); return handle; }
    char *name=freak_fs_checked_path(result,relative); if (!name) return handle;
    if (!freak_fs_relative_valid(name,false)) { free(name); freak_fs_ticket_error(result,"filesystem relative path has unsafe components"); return handle; }
    char *leaf; freak_fs_anchor parent=freak_fs_anchor_parent(root,name,&leaf);
    if (parent == FREAK_FS_INVALID_ANCHOR) { free(name); freak_fs_ticket_error(result,"could not open anchored destination parent"); return handle; }
    bool safe=true;
#ifndef _WIN32
    struct stat prior; bool existing=fstatat(parent,leaf,&prior,AT_SYMLINK_NOFOLLOW) == 0;
    safe=existing ? S_ISREG(prior.st_mode) : errno == ENOENT;
#else
    HANDLE prior=freak_fs_anchor_child(parent,leaf,false,false,false);
    bool existing=prior != INVALID_HANDLE_VALUE;
    if (existing) CloseHandle(prior);
    else safe=GetLastError() == ERROR_FILE_NOT_FOUND;
#endif
    char *temporary=NULL; freak_fs_anchor file=FREAK_FS_INVALID_ANCHOR;
    if (safe) for (int i=0;i<128;i++) { free(temporary); temporary=freak_fs_temporary_name(".write"); file=freak_fs_anchor_child(parent,temporary,false,true,true); if (file != FREAK_FS_INVALID_ANCHOR) break; }
    int descriptor=file == FREAK_FS_INVALID_ANCHOR ? -1 : freak_fs_anchor_file_descriptor(file,true);
#ifndef _WIN32
    if (descriptor >= 0 && existing && fchmod(descriptor,prior.st_mode & 07777) != 0) { close(descriptor); descriptor=-1; }
#endif
    bool complete=descriptor >= 0 && freak_fs_write_all(descriptor,buffer->data,buffer->length);
    if (descriptor >= 0 && !freak_fs_close_write(descriptor)) complete=false;
    if (complete) complete=freak_fs_anchor_rename(parent,temporary,parent,leaf,true);
    result->completed=complete;
    if (complete && freak_fs_anchor_sync(parent)) result->ok=true;
    else { if (temporary && !result->completed) freak_fs_anchor_delete(parent,temporary,false); freak_fs_ticket_error(result,result->completed ? "filesystem publication completed but directory synchronization failed" : "could not write and publish anchored filesystem file"); }
    freak_fs_anchor_close(parent); free(temporary); free(name); return handle;
}
int64_t freak_fs_remove_relative_file_checked(int64_t root_handle,freak_word relative) {
    int64_t handle=freak_fs_ticket_new(); freak_fs_ticket *result=freak_fs_ticket_require(handle);
    freak_fs_ticket *root=freak_fs_directory_require(root_handle);
    char *name=freak_fs_checked_path(result,relative); if (!name) return handle;
    if (!freak_fs_relative_valid(name,false)) { free(name); freak_fs_ticket_error(result,"filesystem relative path has unsafe components"); return handle; }
    char *leaf; freak_fs_anchor parent=freak_fs_anchor_parent(root,name,&leaf); bool removed=false;
    if (parent != FREAK_FS_INVALID_ANCHOR) {
#ifdef _WIN32
        HANDLE file=freak_fs_anchor_child_mode(parent,leaf,false,false,true,true,false);
        if (file != INVALID_HANDLE_VALUE) { removed=freak_fs_anchor_delete_handle(file); CloseHandle(file); }
#else
        struct stat info;
        removed=fstatat(parent,leaf,&info,AT_SYMLINK_NOFOLLOW) == 0 && !S_ISDIR(info.st_mode) && unlinkat(parent,leaf,0) == 0;
#endif
    }
    result->completed=removed;
    if (removed && freak_fs_anchor_sync(parent)) result->ok=true;
    else freak_fs_ticket_error(result,removed ? "file removal completed but directory synchronization failed" : "could not remove anchored file entry");
    freak_fs_anchor_close(parent); free(name); return handle;
}
int64_t freak_fs_lock_dir_ticket(int64_t root_handle,freak_word lock_name) {
    int64_t handle=freak_fs_ticket_new(); freak_fs_ticket *result=freak_fs_ticket_require(handle);
    freak_fs_ticket *root=freak_fs_directory_require(root_handle);
    char *name=freak_fs_checked_path(result,lock_name); if (!name) return handle;
    if (!freak_fs_relative_valid(name,true)) { free(name); freak_fs_ticket_error(result,"directory lock name must be one safe component"); return handle; }
#ifdef _WIN32
    HANDLE lock=freak_fs_anchor_child_mode(root->directory,name,false,true,true,false,true);
    if (lock == INVALID_HANDLE_VALUE && (GetLastError() == ERROR_FILE_EXISTS || GetLastError() == ERROR_ALREADY_EXISTS))
        lock=freak_fs_anchor_child_mode(root->directory,name,false,false,true,false,true);
    bool locked=lock != INVALID_HANDLE_VALUE;
#else
    struct stat root_info;
    if (fstat(root->directory,&root_info) != 0 || root_info.st_uid != geteuid() || (root_info.st_mode & 0077)) {
        free(name); freak_fs_ticket_error(result,"directory transaction lock requires a private owned directory"); return handle;
    }
    int lock=openat(root->directory,name,O_RDWR | O_CREAT | O_NOFOLLOW | O_NONBLOCK | O_CLOEXEC,0600);
    struct stat info;
    bool locked=lock >= 0 && fstat(lock,&info) == 0 && S_ISREG(info.st_mode) && info.st_nlink == 1 &&
        info.st_uid == geteuid() && !(info.st_mode & 0077) && flock(lock,LOCK_EX | LOCK_NB) == 0;
#endif
    if (locked) { freak_fs_ticket_data(result,name,strlen(name)); result->directory=lock; result->owns_lock=true; result->kind=5; }
    else { freak_fs_anchor_close(lock); freak_fs_ticket_error(result,"directory transaction lock is held or not a private regular file"); }
    free(name); return handle;
}
static char *freak_fs_anchor_join(const char *parent,const char *name) {
    size_t length=strlen(parent)+strlen(name)+2;
    char *full=freak_command_allocate(length,1);
#ifdef _WIN32
    snprintf(full,length,"%s\\%s",parent,name);
    for (char *cursor=full;*cursor;cursor++) if (*cursor == '/') *cursor='\\';
#else
    snprintf(full,length,"%s/%s",parent,name);
#endif
    return full;
}
int64_t freak_fs_open_relative_dir_ticket(int64_t root_handle,freak_word relative) {
    int64_t handle=freak_fs_ticket_new(); freak_fs_ticket *result=freak_fs_ticket_require(handle);
    freak_fs_ticket *root=freak_fs_directory_require(root_handle);
    char *name=freak_fs_checked_path(result,relative); if (!name) return handle;
    if (!freak_fs_relative_valid(name,false)) { free(name); freak_fs_ticket_error(result,"filesystem relative path has unsafe components"); return handle; }
    char *logical=freak_command_copy(freak_word_lit(name),false),*leaf;
    freak_fs_anchor parent=freak_fs_anchor_parent(root,name,&leaf);
    freak_fs_anchor directory=parent == FREAK_FS_INVALID_ANCHOR ? FREAK_FS_INVALID_ANCHOR : freak_fs_anchor_child(parent,leaf,true,false,false);
    if (directory != FREAK_FS_INVALID_ANCHOR) {
        char *full=freak_fs_anchor_join((const char *)root->data,logical);
        freak_fs_ticket_data(result,full,strlen(full)); free(full);
        result->directory=directory; result->has_directory=true; result->kind=2;
#ifndef _WIN32
        struct stat info; if (fstat(directory,&info) == 0) result->mode=(int64_t)(info.st_mode & 07777);
#endif
    } else { result->missing=freak_fs_failure_missing(); freak_fs_ticket_error(result,"could not open anchored directory without following links"); }
    freak_fs_anchor_close(parent); free(logical); free(name); return handle;
}
int64_t freak_fs_mkdir_relative_checked(int64_t root_handle,freak_word relative) {
    int64_t handle=freak_fs_ticket_new(); freak_fs_ticket *result=freak_fs_ticket_require(handle);
    freak_fs_ticket *root=freak_fs_directory_require(root_handle);
    char *name=freak_fs_checked_path(result,relative); if (!name) return handle;
    if (!freak_fs_relative_valid(name,false)) { free(name); freak_fs_ticket_error(result,"filesystem relative path has unsafe components"); return handle; }
    char *logical=freak_command_copy(freak_word_lit(name),false),*leaf;
    freak_fs_anchor parent=freak_fs_anchor_parent(root,name,&leaf),directory=FREAK_FS_INVALID_ANCHOR;
    if (parent != FREAK_FS_INVALID_ANCHOR) {
#ifdef _WIN32
        directory=freak_fs_anchor_child(parent,leaf,true,true,true);
        result->completed=directory != FREAK_FS_INVALID_ANCHOR;
#else
        result->completed=mkdirat(parent,leaf,0700) == 0;
        if (result->completed) directory=freak_fs_anchor_child(parent,leaf,true,false,false);
#endif
    }
    if (directory != FREAK_FS_INVALID_ANCHOR) {
        char *full=freak_fs_anchor_join((const char *)root->data,logical);
        freak_fs_ticket_data(result,full,strlen(full)); free(full);
        result->directory=directory; result->has_directory=true; result->kind=2;
        if (!freak_fs_anchor_sync(parent)) freak_fs_ticket_error(result,"directory creation completed but directory synchronization failed");
    } else freak_fs_ticket_error(result,result->completed ? "directory creation completed but identity could not be opened" : "could not exclusively create anchored directory");
    freak_fs_anchor_close(parent); free(logical); free(name); return handle;
}
int64_t freak_fs_temp_dir(freak_word parent,freak_word prefix) {
    int64_t handle=freak_fs_ticket_new(); freak_fs_ticket *result=freak_fs_ticket_require(handle);
    char *directory=freak_fs_checked_path(result,parent),*name=freak_fs_checked_path(result,prefix);
    if (!directory || !name) { free(directory); free(name); return handle; }
    if (!freak_fs_relative_valid(name,true) || strlen(name) > 128) { freak_fs_ticket_error(result,"temporary prefix must be a simple filename"); free(directory); free(name); return handle; }
    freak_fs_anchor owner=freak_fs_anchor_root(directory),child=FREAK_FS_INVALID_ANCHOR;
    char *temporary=NULL;
    if (owner != FREAK_FS_INVALID_ANCHOR) for (int i=0;i<128;i++) {
        free(temporary); temporary=freak_fs_temporary_name(name);
#ifdef _WIN32
        bool retryable=false; child=freak_fs_windows_owned_temp(owner,temporary,&retryable);
        if (child != FREAK_FS_INVALID_ANCHOR || !retryable) break;
#else
        child=freak_fs_anchor_child(owner,temporary,true,true,true); if (child != FREAK_FS_INVALID_ANCHOR) break;
#endif
    }
    if (child == FREAK_FS_INVALID_ANCHOR) { freak_fs_anchor_close(owner); freak_fs_ticket_error(result,"could not exclusively create anchored temporary directory"); }
    else {
        char *full=freak_fs_anchor_join(directory,temporary);
        freak_fs_ticket_data(result,full,strlen(full)); free(full);
        result->directory=child; result->temp_parent=owner; result->temp_name=temporary; temporary=NULL;
        result->has_directory=result->owns_temp=result->temp_active=result->completed=true; result->kind=2;
    }
    free(directory); free(name); free(temporary); return handle;
}
/* Enumerate/decrement a bounded tree through admitted directory handles. A
   link is removed as an entry; its target is never opened or enumerated. */
static bool freak_fs_anchor_clear(freak_fs_anchor directory,size_t depth,size_t *remaining) {
    if (depth > 128) return false;
#ifdef _WIN32
    const size_t capacity=64*1024; unsigned char *batch=freak_command_allocate(capacity,1);
    FILE_INFO_BY_HANDLE_CLASS operation=FileIdBothDirectoryRestartInfo; bool ok=true;
    for (;;) {
        if (!GetFileInformationByHandleEx(directory,operation,batch,(DWORD)capacity)) { ok=GetLastError() == ERROR_NO_MORE_FILES; break; }
        operation=FileIdBothDirectoryInfo; size_t position=0;
        for (;;) {
            FILE_ID_BOTH_DIR_INFO *item=(FILE_ID_BOTH_DIR_INFO *)(batch+position);
            size_t prefix=offsetof(FILE_ID_BOTH_DIR_INFO,FileName);
            if (position > capacity-prefix || item->FileNameLength % sizeof(wchar_t) || item->FileNameLength > capacity-position-prefix) { ok=false; break; }
            int characters=(int)(item->FileNameLength/sizeof(wchar_t));
            int bytes=WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,item->FileName,characters,NULL,0,NULL,NULL);
            char *name=bytes > 0 ? freak_command_allocate((size_t)bytes+1,1) : NULL;
            if (!name || WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,item->FileName,characters,name,bytes,NULL,NULL) != bytes) { free(name); ok=false; break; }
            if (strcmp(name,".") && strcmp(name,"..")) {
                if (!*remaining) { free(name); ok=false; break; } --*remaining;
                bool folder=(item->FileAttributes & FILE_ATTRIBUTE_DIRECTORY) != 0;
                if (item->FileAttributes & FILE_ATTRIBUTE_REPARSE_POINT) {
                    HANDLE link=freak_fs_anchor_child_mode(directory,name,folder,false,true,true,false);
                    ok=link != INVALID_HANDLE_VALUE && freak_fs_anchor_delete_handle(link); freak_fs_anchor_close(link);
                }
                else if (folder) {
                    HANDLE child=freak_fs_anchor_child(directory,name,true,false,true);
                    ok=child != INVALID_HANDLE_VALUE && freak_fs_anchor_clear(child,depth+1,remaining) && freak_fs_anchor_delete_handle(child);
                    freak_fs_anchor_close(child);
                }
                else ok=freak_fs_anchor_delete(directory,name,false);
            }
            free(name); if (!ok || !item->NextEntryOffset) break;
            if (item->NextEntryOffset < prefix || item->NextEntryOffset > capacity-position-prefix) { ok=false; break; } position+=item->NextEntryOffset;
        }
        if (!ok) break;
    }
    free(batch); return ok;
#else
    int copy=freak_fs_anchor_dup(directory); DIR *scan=copy >= 0 ? fdopendir(copy) : NULL;
    if (!scan) { if (copy >= 0) close(copy); return false; }
    bool ok=true; struct dirent *entry;
    rewinddir(scan); errno=0;
    while ((entry=readdir(scan)) != NULL) {
        if (!strcmp(entry->d_name,".") || !strcmp(entry->d_name,"..")) continue;
        if (!*remaining) { ok=false; break; } --*remaining;
        struct stat info;
        if (fstatat(directory,entry->d_name,&info,AT_SYMLINK_NOFOLLOW) != 0) { ok=false; break; }
        if (S_ISDIR(info.st_mode)) {
            int child=freak_fs_anchor_child(directory,entry->d_name,true,false,false);
            struct stat opened; bool same=child >= 0 && fstat(child,&opened) == 0 && opened.st_dev == info.st_dev && opened.st_ino == info.st_ino;
            ok=same && freak_fs_anchor_clear(child,depth+1,remaining);
            struct stat current; if (ok) ok=fstatat(directory,entry->d_name,&current,AT_SYMLINK_NOFOLLOW) == 0 && current.st_dev == opened.st_dev && current.st_ino == opened.st_ino;
            freak_fs_anchor_close(child);
            if (ok) ok=unlinkat(directory,entry->d_name,AT_REMOVEDIR) == 0;
        } else ok=unlinkat(directory,entry->d_name,0) == 0;
        if (!ok) break;
        errno=0;
    }
    if (ok && errno) ok=false;
    if (closedir(scan) != 0) ok=false;
    return ok;
#endif
}
static bool freak_fs_temp_identity(freak_fs_ticket *temp) {
    if (!temp->owns_temp || !temp->temp_active || !temp->has_directory) return false;
    freak_fs_anchor current=freak_fs_anchor_child(temp->temp_parent,temp->temp_name,true,false,false);
    bool same=current != FREAK_FS_INVALID_ANCHOR && freak_fs_anchor_same(current,temp->directory);
    freak_fs_anchor_close(current); return same;
}
int64_t freak_fs_remove_temp_dir_checked(int64_t temp_handle) {
    int64_t handle=freak_fs_ticket_new(); freak_fs_ticket *result=freak_fs_ticket_require(handle);
    freak_fs_ticket *temp=freak_fs_ticket_require(temp_handle);
    if (!freak_fs_temp_identity(temp)) { freak_fs_ticket_error(result,"temporary directory ownership identity is absent or changed"); return handle; }
    size_t remaining=65535;
    bool cleared=freak_fs_anchor_clear(temp->directory,0,&remaining) && freak_fs_temp_identity(temp);
#ifdef _WIN32
    bool removed=cleared && freak_fs_anchor_delete_handle(temp->directory);
#else
    bool removed=cleared && freak_fs_anchor_delete(temp->temp_parent,temp->temp_name,true);
#endif
    if (removed) { freak_fs_anchor_close(temp->directory); temp->has_directory=false; }
    if (removed) { result->completed=true; temp->temp_active=false; if (freak_fs_anchor_sync(temp->temp_parent)) result->ok=true; }
    if (!result->ok) freak_fs_ticket_error(result,result->completed ? "temporary removal completed but directory synchronization failed" : "could not safely remove complete owned temporary directory");
    return handle;
}
int64_t freak_fs_publish_temp_dir_checked(int64_t temp_handle,int64_t parent_handle,freak_word destination) {
    int64_t handle=freak_fs_ticket_new(); freak_fs_ticket *result=freak_fs_ticket_require(handle);
    freak_fs_ticket *temp=freak_fs_ticket_require(temp_handle),*parent=freak_fs_directory_require(parent_handle);
    char *name=freak_fs_checked_path(result,destination); if (!name) return handle;
    if (!freak_fs_relative_valid(name,true) || !freak_fs_temp_identity(temp)) { free(name); freak_fs_ticket_error(result,"publication requires owned temporary identity and simple destination name"); return handle; }
    freak_fs_anchor old_parent=temp->temp_parent,new_parent=freak_fs_anchor_dup(parent->directory);
    if (new_parent == FREAK_FS_INVALID_ANCHOR) { free(name); freak_fs_ticket_error(result,"could not retain publication parent identity"); return handle; }
#ifdef _WIN32
    bool renamed=freak_fs_anchor_rename_handle(temp->directory,parent->directory,name,false);
#else
    bool renamed=freak_fs_anchor_rename(old_parent,temp->temp_name,parent->directory,name,false);
#endif
    if (renamed) {
        result->completed=true;
        /* Retain ownership of the published identity, including an unsynced
           publication: the transaction may safely roll back its own new tree. */
        temp->temp_parent=new_parent; new_parent=FREAK_FS_INVALID_ANCHOR;
        free(temp->temp_name); temp->temp_name=name; name=NULL;
        char *full=freak_fs_anchor_join((const char *)parent->data,temp->temp_name);
        free(temp->data); temp->data=(unsigned char *)full; temp->length=strlen(full);
        bool parent_synced=freak_fs_anchor_sync(parent->directory),old_parent_synced=freak_fs_anchor_sync(old_parent);
        bool synced=parent_synced && old_parent_synced;
        freak_fs_anchor_close(old_parent);
        if (!freak_fs_temp_identity(temp)) freak_fs_ticket_error(result,"publication completed but owned directory identity changed during rename");
        else if (synced) result->ok=true;
        else freak_fs_ticket_error(result,"temporary publication completed but directory synchronization failed");
    } else freak_fs_ticket_error(result,"could not publish owned temporary directory without replacing destination");
    freak_fs_anchor_close(new_parent); free(name); return handle;
}

int64_t freak_fs_canonical_path(freak_word path) {
    int64_t handle = freak_fs_ticket_new(); freak_fs_ticket *result = freak_fs_ticket_require(handle);
    char *name = freak_fs_checked_path(result,path); if (!name) return handle;
#ifdef _WIN32
    wchar_t *wide = freak_command_wide(name);
    HANDLE file = CreateFileW(wide,0,FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,NULL,OPEN_EXISTING,FILE_FLAG_BACKUP_SEMANTICS,NULL);
    free(wide);
    if (file != INVALID_HANDLE_VALUE) {
        DWORD count = GetFinalPathNameByHandleW(file,NULL,0,FILE_NAME_NORMALIZED | VOLUME_NAME_DOS);
        wchar_t *canonical = freak_command_allocate((size_t)count + 1,sizeof(wchar_t));
        DWORD read = GetFinalPathNameByHandleW(file,canonical,count + 1,FILE_NAME_NORMALIZED | VOLUME_NAME_DOS);
        if (count && read && read <= count) {
            int bytes = WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,canonical,-1,NULL,0,NULL,NULL);
            if (bytes > 0) {
                result->data = freak_command_allocate((size_t)bytes,1);
                if (WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,canonical,-1,(char *)result->data,bytes,NULL,NULL) == bytes) {
                    result->length = (size_t)bytes - 1; result->ok = true;
                }
            }
        }
        free(canonical); CloseHandle(file);
    }
#else
    char *canonical = realpath(name,NULL);
    if (canonical) {
        if (freak_system_utf8_valid(canonical,strlen(canonical))) freak_fs_ticket_data(result,canonical,strlen(canonical));
        free(canonical);
    }
#endif
    if (!result->ok) freak_fs_ticket_error(result,"could not resolve canonical filesystem identity");
    free(name); return handle;
}
/* A trailing separator must not cause the host to follow a final symlink
   before lstat/O_NOFOLLOW/GetFileAttributes sees it. Preserve filesystem roots. */
static char *freak_fs_nofollow_path(freak_fs_ticket *result,freak_word path) {
    char *name = freak_fs_checked_path(result,path);
    if (!name) return NULL;
    size_t length = strlen(name);
    while (length > 1) {
#ifdef _WIN32
        if (length == 3 && name[1] == ':') break;
        if (name[length-1] != '/' && name[length-1] != '\\') break;
#else
        if (name[length-1] != '/') break;
#endif
        name[--length] = 0;
    }
    return name;
}
/* An absent leaf reached through a broken ancestor link is not a safe missing
   path. Recheck native not-found failures through nofollow directory handles;
   unreadable, non-directory and reparse ancestors remain ordinary errors. */
static bool freak_fs_stat_known_missing(const char *name) {
#ifdef _WIN32
    DWORD saved=GetLastError();
    freak_fs_anchor directory=freak_fs_anchor_root(name);
    bool missing=directory == FREAK_FS_INVALID_ANCHOR && freak_fs_failure_missing();
    freak_fs_anchor_close(directory); SetLastError(saved); return missing;
#else
    int saved=errno;
    freak_fs_anchor current=open(name[0] == '/' ? "/" : ".",O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
    char *tail=freak_command_copy(freak_word_lit(name[0] == '/' ? name+1 : name),false);
    char *cursor=tail; bool missing=current < 0 && errno == ENOENT;
    while (*cursor && current >= 0) {
        while (*cursor == '/') cursor++;
        if (!*cursor) break;
        char *slash=strchr(cursor,'/'); if (slash) *slash=0;
        /* Unlike contained relative operations, general stat accepts ../. */
        freak_fs_anchor next=openat(current,cursor,O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC | O_NONBLOCK);
        if (next < 0) missing=errno == ENOENT;
        freak_fs_anchor_close(current); current=next;
        if (!slash) break;
        cursor=slash+1;
    }
    freak_fs_anchor_close(current); free(tail); errno=saved; return missing;
#endif
}
int64_t freak_fs_stat_checked(freak_word path) {
    int64_t handle = freak_fs_ticket_new(); freak_fs_ticket *result = freak_fs_ticket_require(handle);
    char *name = freak_fs_nofollow_path(result,path); if (!name) return handle;
#ifdef _WIN32
    wchar_t *wide = freak_command_wide(name);
    WIN32_FILE_ATTRIBUTE_DATA info;
    if (GetFileAttributesExW(wide,GetFileExInfoStandard,&info)) {
        result->kind = (info.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT) ? 3 :
                       (info.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) ? 2 : 1;
        uint64_t size = ((uint64_t)info.nFileSizeHigh << 32) | info.nFileSizeLow;
        if (size <= INT64_MAX) {
            result->size = (int64_t)size; result->mode = (int64_t)info.dwFileAttributes; result->ok = true;
        }
    } else if (freak_fs_failure_missing()) result->missing=freak_fs_stat_known_missing(name);
    free(wide);
#else
    struct stat info;
    if (lstat(name,&info) == 0) {
        if (info.st_size >= 0 && (uintmax_t)info.st_size <= INT64_MAX) {
            result->kind = S_ISREG(info.st_mode) ? 1 : S_ISDIR(info.st_mode) ? 2 : S_ISLNK(info.st_mode) ? 3 : 4;
            result->size = (int64_t)info.st_size; result->mode = (int64_t)(info.st_mode & 07777); result->ok = true;
        }
    } else if (errno == ENOENT) result->missing=freak_fs_stat_known_missing(name);
#endif
    if (!result->ok) freak_fs_ticket_error(result,"could not inspect filesystem path without following links");
    free(name); return handle;
}
static void freak_fs_add_entry(freak_fs_ticket *result,const char *entry) {
    if (strcmp(entry,".") == 0 || strcmp(entry,"..") == 0) return;
    if (!freak_system_utf8_valid(entry,strlen(entry))) { freak_fs_ticket_error(result,"directory entry is not valid UTF-8"); return; }
    if (result->entry_count >= 65535) { freak_fs_ticket_error(result,"directory exceeds 65535-entry limit"); return; }
    char **grown = realloc(result->entries,(result->entry_count + 1) * sizeof(char *));
    if (!grown) freak_command_fail("out of memory collecting directory inventory");
    result->entries = grown; result->entries[result->entry_count++] = freak_command_copy(freak_word_lit(entry),false);
}
static int freak_fs_entry_compare(const void *a,const void *b) { return strcmp(*(char *const *)a,*(char *const *)b); }
static void freak_fs_list_anchor(freak_fs_ticket *result,freak_fs_anchor directory) {
#ifdef _WIN32
    BY_HANDLE_FILE_INFORMATION identity;
    result->ok = directory != INVALID_HANDLE_VALUE &&
        GetFileInformationByHandle(directory,&identity) &&
        (identity.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) &&
        !(identity.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT);
    if (result->ok) {
        const size_t capacity = 64 * 1024;
        unsigned char *batch = freak_command_allocate(capacity,1);
        FILE_INFO_BY_HANDLE_CLASS operation = FileIdBothDirectoryRestartInfo;
        for (;;) {
            if (!GetFileInformationByHandleEx(directory,operation,batch,(DWORD)capacity)) {
                if (GetLastError() != ERROR_NO_MORE_FILES) freak_fs_ticket_error(result,"could not read complete directory inventory");
                break;
            }
            operation = FileIdBothDirectoryInfo;
            size_t position = 0;
            for (;;) {
                FILE_ID_BOTH_DIR_INFO *item = (FILE_ID_BOTH_DIR_INFO *)(batch + position);
                size_t prefix = offsetof(FILE_ID_BOTH_DIR_INFO,FileName);
                if (position > capacity - prefix || item->FileNameLength % sizeof(wchar_t) ||
                        item->FileNameLength > capacity - position - prefix) {
                    freak_fs_ticket_error(result,"invalid directory inventory record"); break;
                }
                int characters = (int)(item->FileNameLength / sizeof(wchar_t));
                int bytes = WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,item->FileName,characters,NULL,0,NULL,NULL);
                if (bytes <= 0) { freak_fs_ticket_error(result,"directory entry is not valid Unicode"); break; }
                char *entry = freak_command_allocate((size_t)bytes + 1,1);
                if (WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,item->FileName,characters,entry,bytes,NULL,NULL) != bytes)
                    freak_fs_ticket_error(result,"could not decode directory inventory entry");
                else freak_fs_add_entry(result,entry);
                free(entry);
                if (!result->ok || !item->NextEntryOffset) break;
                if (item->NextEntryOffset < prefix || item->NextEntryOffset > capacity - position - prefix) {
                    freak_fs_ticket_error(result,"invalid directory inventory offset"); break;
                }
                position += item->NextEntryOffset;
            }
            if (!result->ok) break;
        }
        free(batch);
    }
#else
    int descriptor=freak_fs_anchor_dup(directory);
    DIR *scan = descriptor >= 0 ? fdopendir(descriptor) : NULL;
    if (!scan && descriptor >= 0) close(descriptor);
    result->ok = scan != NULL;
    if (scan) {
        rewinddir(scan);
        struct dirent *entry;
        errno = 0;
        while ((entry = readdir(scan)) != NULL) {
            freak_fs_add_entry(result,entry->d_name);
            if (!result->ok) break;
            errno = 0;
        }
        if (result->ok && errno) freak_fs_ticket_error(result,"could not read complete directory inventory");
        if (closedir(scan) != 0) freak_fs_ticket_error(result,"could not close directory inventory");
    }
#endif
    if (!result->ok && !result->error[0]) freak_fs_ticket_error(result,"could not open directory inventory");
    if (result->ok && result->entry_count > 1) qsort(result->entries,result->entry_count,sizeof(char *),freak_fs_entry_compare);
}
int64_t freak_fs_list_dir_ticket(int64_t root_handle) {
    int64_t handle=freak_fs_ticket_new(); freak_fs_ticket *result=freak_fs_ticket_require(handle);
    freak_fs_ticket *root=freak_fs_directory_require(root_handle);
    freak_fs_list_anchor(result,root->directory); return handle;
}
int64_t freak_fs_list_dir_checked(freak_word path) {
    int64_t handle=freak_fs_ticket_new(); freak_fs_ticket *result=freak_fs_ticket_require(handle);
    char *name=freak_fs_nofollow_path(result,path); if (!name) return handle;
#ifdef _WIN32
    wchar_t *wide=freak_command_wide(name);
    HANDLE directory=CreateFileW(wide,FILE_LIST_DIRECTORY,FILE_SHARE_READ | FILE_SHARE_WRITE,NULL,OPEN_EXISTING,
        FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT,NULL);
    free(wide);
#else
    int directory=open(name,O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
#endif
    if (directory == FREAK_FS_INVALID_ANCHOR) { result->missing=freak_fs_failure_missing(); freak_fs_ticket_error(result,"could not open directory inventory"); }
    else freak_fs_list_anchor(result,directory);
    freak_fs_anchor_close(directory); free(name); return handle;
}
int64_t freak_fs_directory_identity_ticket(int64_t root_handle) {
    int64_t handle=freak_fs_ticket_new(); freak_fs_ticket *result=freak_fs_ticket_require(handle);
    freak_fs_ticket *root=freak_fs_directory_require(root_handle);
    char identity[128]; bool found=false;
#ifdef _WIN32
    FILE_ID_INFO info;
    if (GetFileInformationByHandleEx(root->directory,FileIdInfo,&info,sizeof(info))) {
        int count=snprintf(identity,sizeof(identity),"windows:%016llx:",(unsigned long long)info.VolumeSerialNumber);
        for (size_t i=0;i<sizeof(info.FileId.Identifier);i++) snprintf(identity+count+i*2,3,"%02x",info.FileId.Identifier[i]);
        found=true;
    }
#else
    struct stat info;
    if (fstat(root->directory,&info) == 0) {
        snprintf(identity,sizeof(identity),"posix:%ju:%ju",(uintmax_t)info.st_dev,(uintmax_t)info.st_ino); found=true;
    }
#endif
    /* Physical IDs are transient resolver keys while the anchor is live. They
       must never enter a reproducible content hash or persisted package lock. */
    if (found) freak_fs_ticket_data(result,identity,strlen(identity));
    else freak_fs_ticket_error(result,"could not inspect held directory identity");
    return handle;
}
int64_t freak_fs_directory_path_ticket(int64_t root_handle) {
    int64_t handle=freak_fs_ticket_new(); freak_fs_ticket *result=freak_fs_ticket_require(handle);
    freak_fs_ticket *root=freak_fs_directory_require(root_handle);
#ifdef _WIN32
    DWORD count=GetFinalPathNameByHandleW(root->directory,NULL,0,FILE_NAME_NORMALIZED | VOLUME_NAME_DOS);
    if (count && count <= 32768) {
        wchar_t *wide=freak_command_allocate((size_t)count+1,sizeof(wchar_t));
        DWORD read=GetFinalPathNameByHandleW(root->directory,wide,count+1,FILE_NAME_NORMALIZED | VOLUME_NAME_DOS);
        int bytes=read && read <= count ? WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,wide,(int)read,NULL,0,NULL,NULL) : 0;
        if (bytes > 0) {
            char *name=freak_command_allocate((size_t)bytes+1,1);
            if (WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,wide,(int)read,name,bytes,NULL,NULL) == bytes) freak_fs_ticket_data(result,name,(size_t)bytes);
            free(name);
        }
        free(wide);
    }
#else
    char path[4097]; bool found=false;
#ifdef __APPLE__
    found=fcntl(root->directory,F_GETPATH,path) == 0;
#elif defined(__linux__)
    char descriptor_name[64]; snprintf(descriptor_name,sizeof(descriptor_name),"/proc/self/fd/%d",root->directory);
    ssize_t count=readlink(descriptor_name,path,sizeof(path)-1);
    if (count > 0 && count < (ssize_t)sizeof(path)-1) { path[count]=0; found=true; }
#endif
    if (!found) {
        char *canonical=realpath((const char *)root->data,NULL);
        if (canonical && strlen(canonical) < sizeof(path)) { memcpy(path,canonical,strlen(canonical)+1); found=true; }
        free(canonical);
    }
    /* A kernel path is a name snapshot. Verify it still names the held inode;
       deleted/replaced paths and the realpath fallback cannot substitute a
       different directory identity into the package graph. */
    if (found) {
        freak_fs_anchor current=freak_fs_anchor_root(path);
        bool same=current != FREAK_FS_INVALID_ANCHOR && freak_fs_anchor_same(current,root->directory);
        freak_fs_anchor_close(current);
        if (same && freak_system_utf8_valid(path,strlen(path))) freak_fs_ticket_data(result,path,strlen(path));
    }
#endif
    if (!result->ok) freak_fs_ticket_error(result,"could not resolve current path of held directory identity");
    return handle;
}
bool freak_fs_result_missing(int64_t ticket) { return freak_fs_ticket_require(ticket)->missing; }
bool freak_fs_result_completed(int64_t ticket) { return freak_fs_ticket_require(ticket)->completed; }
bool freak_fs_result_ok(int64_t ticket) { return freak_fs_ticket_require(ticket)->ok; }
static freak_fs_ticket *freak_fs_result_success(int64_t ticket) {
    freak_fs_ticket *result = freak_fs_ticket_require(ticket);
    if (!result->ok) freak_command_fail("accessed unsuccessful filesystem result");
    return result;
}
freak_word freak_fs_result_word(int64_t ticket) {
    freak_fs_ticket *result = freak_fs_result_success(ticket);
    if (!result->source_text && !freak_byte_buffer_utf8_valid(result->data,result->length)) freak_command_fail("filesystem result is binary; use bytes getter");
    char *copy = freak_command_allocate(result->length + 1,1);
    if (result->length) memcpy(copy,result->data,result->length);
    return freak_word_own(copy,result->length);
}
freak_word freak_fs_result_error(int64_t ticket) { return freak_word_copy_cstr(freak_fs_ticket_require(ticket)->error); }
int64_t freak_fs_result_bytes(int64_t ticket) {
    freak_fs_ticket *result = freak_fs_result_success(ticket);
    int64_t handle = freak_byte_buffer_with_capacity((int64_t)result->length);
    freak_byte_buffer_record *buffer = freak_byte_buffer_require(handle,"filesystem result");
    if (result->length) memcpy(buffer->data,result->data,result->length);
    buffer->length = result->length; return handle;
}
int64_t freak_fs_result_kind(int64_t ticket) { return freak_fs_result_success(ticket)->kind; }
int64_t freak_fs_result_size(int64_t ticket) { return freak_fs_result_success(ticket)->size; }
int64_t freak_fs_result_mode(int64_t ticket) { return freak_fs_result_success(ticket)->mode; }
int64_t freak_fs_result_count(int64_t ticket) { return (int64_t)freak_fs_result_success(ticket)->entry_count; }
freak_word freak_fs_result_entry(int64_t ticket,int64_t index) {
    freak_fs_ticket *result = freak_fs_result_success(ticket);
    if (index < 0 || (uint64_t)index >= result->entry_count) freak_command_fail("directory inventory index out of bounds");
    return freak_word_copy_cstr(result->entries[index]);
}
void freak_fs_result_release(int64_t ticket) {
    freak_fs_ticket *result = freak_fs_ticket_require(ticket);
    if (result->has_directory || result->owns_lock) freak_fs_anchor_close(result->directory);
    if (result->owns_temp) freak_fs_anchor_close(result->temp_parent);
    free(result->temp_name); result->temp_name = NULL;
    result->has_directory = result->owns_temp = result->owns_lock = false;
    free(result->data);
    for (size_t index = 0; index < result->entry_count; index++) free(result->entries[index]);
    free(result->entries); result->data = NULL; result->entries = NULL;
    result->in_use = false; freak_fs_tickets_live--;
}
int64_t freak_fs_result_live(void) { return (int64_t)freak_fs_tickets_live; }

/* SHA-256 is a content identity primitive, not a package signature/trust API.
   Unsigned fixed-width operations implement FIPS 180-4. */
static uint32_t freak_fs_sha_rotate(uint32_t value,unsigned count) { return (value >> count) | (value << (32-count)); }
static void freak_fs_sha_block(uint32_t state[8],const unsigned char bytes[64]) {
    static const uint32_t k[64] = {
        0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
        0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
        0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
        0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
        0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
        0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
        0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
        0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
    };
    uint32_t words[64];
    for (unsigned i=0;i<16;i++) words[i]=((uint32_t)bytes[i*4]<<24)|((uint32_t)bytes[i*4+1]<<16)|((uint32_t)bytes[i*4+2]<<8)|bytes[i*4+3];
    for (unsigned i=16;i<64;i++) {
        uint32_t a=words[i-15],b=words[i-2];
        uint32_t s0=freak_fs_sha_rotate(a,7)^freak_fs_sha_rotate(a,18)^(a>>3);
        uint32_t s1=freak_fs_sha_rotate(b,17)^freak_fs_sha_rotate(b,19)^(b>>10);
        words[i]=words[i-16]+s0+words[i-7]+s1;
    }
    uint32_t a=state[0],b=state[1],c=state[2],d=state[3],e=state[4],f=state[5],g=state[6],h=state[7];
    for (unsigned i=0;i<64;i++) {
        uint32_t s1=freak_fs_sha_rotate(e,6)^freak_fs_sha_rotate(e,11)^freak_fs_sha_rotate(e,25);
        uint32_t t1=h+s1+((e&f)^((~e)&g))+k[i]+words[i];
        uint32_t s0=freak_fs_sha_rotate(a,2)^freak_fs_sha_rotate(a,13)^freak_fs_sha_rotate(a,22);
        uint32_t t2=s0+((a&b)^(a&c)^(b&c));
        h=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2;
    }
    state[0]+=a;state[1]+=b;state[2]+=c;state[3]+=d;state[4]+=e;state[5]+=f;state[6]+=g;state[7]+=h;
}
freak_word freak_fs_sha256_bytes(int64_t handle) {
    freak_byte_buffer_record *buffer = freak_byte_buffer_require(handle,"SHA-256 content identity");
    if (buffer->status != FREAK_BYTE_BUFFER_OK || (uintmax_t)buffer->length > UINT64_MAX/8)
        freak_command_fail("invalid buffer or SHA-256 input length");
    uint32_t state[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
    size_t offset=0;
    while (buffer->length-offset>=64) { freak_fs_sha_block(state,buffer->data+offset); offset+=64; }
    unsigned char tail[128]={0};
    size_t remainder=buffer->length-offset;
    if (remainder) memcpy(tail,buffer->data+offset,remainder);
    tail[remainder]=0x80;
    size_t padded=remainder<56?64:128;
    uint64_t bits=(uint64_t)buffer->length*8;
    for (unsigned i=0;i<8;i++) tail[padded-1-i]=(unsigned char)(bits>>(i*8));
    freak_fs_sha_block(state,tail);
    if (padded==128) freak_fs_sha_block(state,tail+64);
    char *hex=freak_command_allocate(65,1);
    for (unsigned i=0;i<8;i++) snprintf(hex+i*8,9,"%08x",state[i]);
    return freak_word_own(hex,64);
}

/* Scalar adapters preserve the LLVM word view and the same ticket domains. */
int64_t freak_llvm_fs_open_dir_ticket(int64_t path) { return freak_fs_open_dir_ticket(freak_llvm_word_view(path)); }
int64_t freak_llvm_fs_read_bytes_limit_ticket(int64_t path,int64_t limit) { return freak_fs_read_bytes_limit_ticket(freak_llvm_word_view(path),limit); }
int64_t freak_llvm_fs_read_relative_ticket(int64_t root,int64_t path) { return freak_fs_read_relative_ticket(root,freak_llvm_word_view(path)); }
int64_t freak_llvm_fs_read_source_relative_ticket(int64_t root,int64_t path) { return freak_fs_read_source_relative_ticket(root,freak_llvm_word_view(path)); }
int64_t freak_llvm_fs_read_relative_bytes_ticket(int64_t root,int64_t path) { return freak_fs_read_relative_bytes_ticket(root,freak_llvm_word_view(path)); }
int64_t freak_llvm_fs_read_relative_bytes_limit_ticket(int64_t root,int64_t path,int64_t limit) { return freak_fs_read_relative_bytes_limit_ticket(root,freak_llvm_word_view(path),limit); }
int64_t freak_llvm_fs_write_relative_bytes_checked(int64_t root,int64_t path,int64_t bytes) { return freak_fs_write_relative_bytes_checked(root,freak_llvm_word_view(path),bytes); }
int64_t freak_llvm_fs_set_mode_relative_checked(int64_t root,int64_t path,int64_t mode) { return freak_fs_set_mode_relative_checked(root,freak_llvm_word_view(path),mode); }
int64_t freak_llvm_fs_remove_temp_dir_checked(int64_t temp) { return freak_fs_remove_temp_dir_checked(temp); }
int64_t freak_llvm_fs_publish_temp_dir_checked(int64_t temp,int64_t parent,int64_t path) { return freak_fs_publish_temp_dir_checked(temp,parent,freak_llvm_word_view(path)); }
int64_t freak_llvm_fs_result_completed(int64_t result) { return freak_fs_result_completed(result) ? 1 : 0; }
int64_t freak_llvm_fs_lock_dir_ticket(int64_t root,int64_t name) { return freak_fs_lock_dir_ticket(root,freak_llvm_word_view(name)); }
int64_t freak_llvm_fs_remove_relative_file_checked(int64_t root,int64_t path) { return freak_fs_remove_relative_file_checked(root,freak_llvm_word_view(path)); }
int64_t freak_llvm_fs_mkdir_relative_checked(int64_t root,int64_t relative) { return freak_fs_mkdir_relative_checked(root,freak_llvm_word_view(relative)); }
int64_t freak_llvm_fs_open_relative_dir_ticket(int64_t root,int64_t relative) { return freak_fs_open_relative_dir_ticket(root,freak_llvm_word_view(relative)); }
int64_t freak_llvm_fs_list_dir_ticket(int64_t root) { return freak_fs_list_dir_ticket(root); }
int64_t freak_llvm_fs_result_missing(int64_t result) { return freak_fs_result_missing(result) ? 1 : 0; }
int64_t freak_llvm_fs_directory_path_ticket(int64_t root) { return freak_fs_directory_path_ticket(root); }
int64_t freak_llvm_fs_directory_identity_ticket(int64_t root) { return freak_fs_directory_identity_ticket(root); }
int64_t freak_llvm_fs_rename_relative_new_checked(int64_t source,int64_t from,int64_t destination,int64_t to) {
    return freak_fs_rename_relative_new_checked(source,freak_llvm_word_view(from),destination,freak_llvm_word_view(to));
}
