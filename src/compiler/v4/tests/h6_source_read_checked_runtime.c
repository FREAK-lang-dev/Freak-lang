/* Checked bootstrap source I/O: exact contents and deterministic stdio faults.
   Compile this standalone file; it includes the runtime with local I/O wrappers.
   Run with args: empty regular file, readable regular file, missing path, directory.
   POSIX FIFO/unreadable paths may follow as extra expected failures. */
#ifdef __APPLE__
/* This fixture includes libc before the runtime, so select the same Darwin
   interfaces before those headers freeze their feature visibility. */
#define _DARWIN_C_SOURCE 1
#endif
#ifndef _WIN32
#define _POSIX_C_SOURCE 200809L
#endif
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/stat.h>
#ifdef _WIN32
#include <io.h>
#else
#include <unistd.h>
#endif
static int h6_fault = 0;
static int h6_allocations = 0;
static size_t h6_last_allocation = 0;
#ifdef _WIN32
/* UTF-8 source paths allocate their wide representation before contents. */
#define H6_CONTENTS_ALLOCATION 3
#else
#define H6_CONTENTS_ALLOCATION 2
#endif
static void* h6_malloc(size_t size) {
    ++h6_allocations;
    h6_last_allocation = size;
    if (h6_fault == 8 || ((h6_fault == 9 || h6_fault == 10) &&
                          h6_allocations == H6_CONTENTS_ALLOCATION)) return NULL;
    return malloc(size);
}
static int h6_seek(FILE* file, long offset, int whence) {
    if (h6_fault == 1) { errno = EIO; return -1; }
    return fseek(file, offset, whence);
}
static size_t h6_read(void* contents, size_t size, size_t count, FILE* file) {
    if (h6_fault == 4) { errno = EIO; return 0; }
    return fread(contents, size, count, file);
}
static int h6_close(FILE* file) {
    int status = fclose(file);
    if (h6_fault == 5) { errno = EIO; return EOF; }
    return status;
}
static int h6_getc(FILE* file) {
    if (h6_fault == 7) return 'x';
    return fgetc(file);
}
#ifdef _WIN32
static int h6_open(const wchar_t* name, int flags, ...) {
    if (h6_fault == 6) { errno = EACCES; return -1; }
    return _wopen(name, flags);
}
static int h6_stat(int descriptor, struct _stat64* metadata) {
    if (h6_fault == 3) { errno = EIO; return -1; }
    int status = _fstat64(descriptor, metadata);
    if (status == 0 && h6_fault == 2) metadata->st_size = -1;
    if (status == 0 && h6_fault == 10) metadata->st_size = (int64_t)INT32_MAX + 19;
    return status;
}
#define _wopen h6_open
#define _fstat64 h6_stat
#else
static int h6_open(const char* name, int flags, ...) {
    if (h6_fault == 6) { errno = EACCES; return -1; }
    return open(name, flags);
}
static int h6_stat(int descriptor, struct stat* metadata) {
    if (h6_fault == 3) { errno = EIO; return -1; }
    int status = fstat(descriptor, metadata);
    if (status == 0 && h6_fault == 2) metadata->st_size = -1;
    if (status == 0 && h6_fault == 10) metadata->st_size = (int64_t)INT32_MAX + 19;
    return status;
}
#define open h6_open
#define fstat h6_stat
#endif
#define malloc h6_malloc
#define fseek h6_seek
#define fread h6_read
#define fclose h6_close
#define fgetc h6_getc
#include "../../../../freakc/runtime/freak_runtime.c"
#undef malloc
#undef fseek
#undef fread
#undef fclose
#undef fgetc
#ifdef _WIN32
#undef _wopen
#undef _fstat64
#else
#undef open
#undef fstat
#endif
static int h6_ok(freak_result_word_word result, const char* expected) {
    if (!result.is_ok) return 0;
    int matches = result.data.ok_val.length == strlen(expected) &&
                  memcmp(result.data.ok_val.data, expected, strlen(expected)) == 0;
    freak_word_release_owned(&result.data.ok_val);
    return matches;
}
static int h6_err(freak_result_word_word result) {
    if (result.is_ok) {
        freak_word_release_owned(&result.data.ok_val);
        return 0;
    }
    return result.data.err_val.length != 0;
}
int main(int argc, char** argv) {
    if (argc < 5) return 2;
    int contents = h6_ok(freak_fs_read_checked(freak_word_lit(argv[1])), "") &&
                   h6_ok(freak_fs_read_checked(freak_word_lit(argv[2])), "task main() -> int {\n give back 7\n}\n");
    int errors = h6_err(freak_fs_read_checked(freak_word_lit(argv[3]))) &&
                 h6_err(freak_fs_read_checked(freak_word_lit(argv[4]))) &&
                 h6_err(freak_fs_read_checked(freak_word_lit("")));
    char nul_path[] = { 'a', '\0', 'b', '\0' };
    freak_word embedded = { .data = nul_path, .length = 3 };
    errors = errors && h6_err(freak_fs_read_checked(embedded));
    for (int index = 5; index < argc; ++index)
        errors = errors && h6_err(freak_fs_read_checked(freak_word_lit(argv[index])));
    int faults = 1;
    for (int fault = 1; fault <= 9; ++fault) {
        h6_fault = fault;
        h6_allocations = 0;
        if (!h6_err(freak_fs_read_checked(freak_word_lit(argv[2])))) faults = 0;
        if (fault == 9 && h6_allocations != H6_CONTENTS_ALLOCATION) faults = 0;
    }
    /* Exercise a size beyond Windows long without allocating gigabytes. */
    h6_fault = 10;
    h6_allocations = 0;
    int large_size = h6_err(freak_fs_read_checked(freak_word_lit(argv[2]))) &&
                     h6_allocations == H6_CONTENTS_ALLOCATION &&
                     h6_last_allocation == (size_t)INT32_MAX + 20;
    faults = faults && large_size;
    h6_fault = 0;
    int recovery = h6_ok(freak_fs_read_checked(freak_word_lit(argv[2])), "task main() -> int {\n give back 7\n}\n");
    printf("h6-runtime-source-read contents=%s errors=%s faults=%s recovery=%s\n",
           contents ? "true" : "false", errors ? "true" : "false",
           faults ? "true" : "false", recovery ? "true" : "false");
    return contents && errors && faults && recovery ? 0 : 1;
}
