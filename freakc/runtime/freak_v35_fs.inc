/* Shared V3.5 checked I/O substrate; included by the shipping C runtime. */
/* Some bootstrap fixtures include this runtime after feature-restricted libc
   headers. Their include guards cannot be reopened by a late feature macro.
   Declare these stable platform entry points with their actual libc ABI. */
#ifndef _WIN32
extern char *realpath(const char *restrict path,char *restrict resolved);
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
    bool in_use, ok, source_text;
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
    memset(result,0,sizeof(*result)); result->generation = generation; result->in_use = true;
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
        CloseHandle(file); return -1;
    }
    int descriptor = _open_osfhandle((intptr_t)file,_O_RDONLY | _O_BINARY);
    if (descriptor < 0) CloseHandle(file);
    return descriptor;
#else
    return open(path,O_RDONLY | O_NONBLOCK | O_NOFOLLOW | O_CLOEXEC);
#endif
}
static int64_t freak_fs_read_mode(freak_word path,bool text) {
    int64_t handle = freak_fs_ticket_new(); freak_fs_ticket *result = freak_fs_ticket_require(handle);
    char *name = freak_fs_checked_path(result,path); if (!name) return handle;
    int descriptor = freak_fs_open_read(name); free(name);
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
    bool published = complete;
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
        if (freak_fs_remove_native(name)) result->ok = true;
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
        if (ok) result->ok = true;
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
        if (freak_fs_mkdir_native(name)) result->ok = true;
        else freak_fs_ticket_error(result,"could not create filesystem directory");
    }
    free(name); return handle;
}
int64_t freak_fs_temp_dir(freak_word parent,freak_word prefix) {
    int64_t handle = freak_fs_ticket_new(); freak_fs_ticket *result = freak_fs_ticket_require(handle);
    char *directory = freak_fs_checked_path(result,parent), *name = freak_fs_checked_path(result,prefix);
    if (!directory || !name) { free(directory); free(name); return handle; }
    if (strpbrk(name,"/\\:") || strcmp(name,".") == 0 || strcmp(name,"..") == 0 || strlen(name) > 128) {
        free(directory); free(name); freak_fs_ticket_error(result,"temporary prefix must be a simple filename"); return handle;
    }
    size_t size = strlen(directory) + strlen(name) + 2;
    char *base = freak_command_allocate(size,1); snprintf(base,size,"%s/%s",directory,name);
    char *temporary = NULL;
    for (int attempt = 0; attempt < 128; attempt++) {
        free(temporary); temporary = freak_fs_temporary_name(base);
        if (freak_fs_mkdir_native(temporary)) { freak_fs_ticket_data(result,temporary,strlen(temporary)); break; }
#ifdef _WIN32
        if (GetLastError() != ERROR_ALREADY_EXISTS) break;
#else
        if (errno != EEXIST) break;
#endif
    }
    if (!result->ok) freak_fs_ticket_error(result,"could not exclusively create temporary directory");
    free(directory); free(name); free(base); free(temporary); return handle;
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
    }
    free(wide);
#else
    struct stat info;
    if (lstat(name,&info) == 0 && info.st_size >= 0 && (uintmax_t)info.st_size <= INT64_MAX) {
        result->kind = S_ISREG(info.st_mode) ? 1 : S_ISDIR(info.st_mode) ? 2 : S_ISLNK(info.st_mode) ? 3 : 4;
        result->size = (int64_t)info.st_size; result->mode = (int64_t)(info.st_mode & 07777); result->ok = true;
    }
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
int64_t freak_fs_list_dir_checked(freak_word path) {
    int64_t handle = freak_fs_ticket_new(); freak_fs_ticket *result = freak_fs_ticket_require(handle);
    char *name = freak_fs_nofollow_path(result,path); if (!name) return handle;
#ifdef _WIN32
    /* Enumerate the admitted directory handle, never a second path lookup that
       can race a junction replacement after the reparse-point check. */
    wchar_t *wide = freak_command_wide(name);
    HANDLE directory = CreateFileW(wide,FILE_LIST_DIRECTORY,
            FILE_SHARE_READ | FILE_SHARE_WRITE,NULL,OPEN_EXISTING,
            FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT,NULL);
    free(wide);
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
    if (directory != INVALID_HANDLE_VALUE) CloseHandle(directory);
#else
    int descriptor = open(name,O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
    DIR *scan = descriptor >= 0 ? fdopendir(descriptor) : NULL;
    if (!scan && descriptor >= 0) close(descriptor);
    result->ok = scan != NULL;
    if (scan) {
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
    free(name); return handle;
}
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
freak_word freak_fs_result_error(int64_t ticket) { return freak_word_clone(freak_word_lit(freak_fs_ticket_require(ticket)->error)); }
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
    return freak_word_clone(freak_word_lit(result->entries[index]));
}
void freak_fs_result_release(int64_t ticket) {
    freak_fs_ticket *result = freak_fs_ticket_require(ticket);
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
