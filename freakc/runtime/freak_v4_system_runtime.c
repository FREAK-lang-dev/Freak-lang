#ifndef _WIN32
#define _POSIX_C_SOURCE 200809L
#endif

#include "freak_v4_system_runtime.h"
#include "freak_v4_word_runtime.h"
#include "freak_runtime.h"

#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <fcntl.h>
#ifdef _WIN32
#include <windows.h>
#include <shellapi.h>
#include <io.h>
#else
#include <unistd.h>
#endif

typedef struct {
    char *bytes;
    size_t length;
} freak_v4_argument;

static freak_v4_argument *freak_v4_arguments = NULL;
static size_t freak_v4_argument_count = 0;
static bool freak_v4_arguments_cleanup_registered = false;

static _Noreturn void freak_v4_system_fail(const char *reason) {
    fprintf(stderr, "FREAK: V4 system runtime: %s\n", reason);
    fflush(stderr);
    exit(1);
}

/* Strict UTF-8 scalar validation, including U+0000 as ordinary sized data.
   This adapter needs a boolean result so invalid files become Err, not panic. */
static bool freak_v4_system_utf8_valid(const char *bytes, size_t length) {
    const unsigned char *data = (const unsigned char *)bytes;
    size_t offset = 0;
    while (offset < length) {
        unsigned char first = data[offset++];
        if (first <= 0x7f) continue;
        if (first >= 0xc2 && first <= 0xdf) {
            if (length - offset < 1 || data[offset] < 0x80 ||
                    data[offset] > 0xbf) return false;
            offset += 1;
        } else if (first >= 0xe0 && first <= 0xef) {
            if (length - offset < 2) return false;
            unsigned char second = data[offset], third = data[offset + 1];
            if (third < 0x80 || third > 0xbf ||
                    (first == 0xe0 ? second < 0xa0 || second > 0xbf :
                     first == 0xed ? second < 0x80 || second > 0x9f :
                     second < 0x80 || second > 0xbf)) return false;
            offset += 2;
        } else if (first >= 0xf0 && first <= 0xf4) {
            if (length - offset < 3) return false;
            unsigned char second = data[offset], third = data[offset + 1];
            unsigned char fourth = data[offset + 2];
            if (third < 0x80 || third > 0xbf || fourth < 0x80 ||
                    fourth > 0xbf ||
                    (first == 0xf0 ? second < 0x90 || second > 0xbf :
                     first == 0xf4 ? second < 0x80 || second > 0x8f :
                     second < 0x80 || second > 0xbf)) return false;
            offset += 3;
        } else {
            return false;
        }
    }
    return true;
}

static void freak_v4_arguments_free(freak_v4_argument *arguments, size_t count) {
    for (size_t index = 0; index < count; ++index) free(arguments[index].bytes);
    free(arguments);
}

void freak_v4_process_shutdown_args(void) {
    freak_v4_arguments_free(freak_v4_arguments, freak_v4_argument_count);
    freak_v4_arguments = NULL;
    freak_v4_argument_count = 0;
}

void freak_v4_process_setup_args(int64_t argc, int64_t argv) {
    if (argc < 0 || argc > INT_MAX || (argc > 0 && !argv))
        freak_v4_system_fail("invalid argument vector");
    size_t count = (size_t)argc;
#ifdef _WIN32
    int wide_count = 0;
    LPWSTR *wide = CommandLineToArgvW(GetCommandLineW(), &wide_count);
    if (!wide || wide_count <= 0) {
        if (wide) LocalFree(wide);
        freak_v4_system_fail("could not decode Unicode argument vector");
    }
    count = (size_t)wide_count;
#endif
    if (count > SIZE_MAX / sizeof(freak_v4_argument)) {
#ifdef _WIN32
        LocalFree(wide);
#endif
        freak_v4_system_fail("argument vector size overflow");
    }
    freak_v4_argument *staged = count ?
        (freak_v4_argument *)malloc(count * sizeof(*staged)) : NULL;
    const char *failure = NULL;
    if (count && !staged) failure = "argument snapshot allocation failed";
    if (staged) memset(staged, 0, count * sizeof(*staged));
    size_t completed = 0;
    for (; completed < count && !failure; ++completed) {
#ifdef _WIN32
        int length = WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS,
                wide[completed], -1, NULL, 0, NULL, NULL);
        if (length <= 0) { failure = "argument is not valid Unicode"; break; }
        char *copy = (char *)malloc((size_t)length);
        if (!copy) { failure = "argument snapshot allocation failed"; break; }
        int written = WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS,
                wide[completed], -1, copy, length, NULL, NULL);
        if (written != length) {
            free(copy);
            failure = "could not convert Unicode argument";
            break;
        }
        staged[completed].bytes = copy;
        staged[completed].length = (size_t)length - 1;
#else
        const char *argument = ((char **)(uintptr_t)argv)[completed];
        if (!argument) { failure = "invalid argument vector"; break; }
        size_t length = strlen(argument);
        if (length >= SIZE_MAX || length > (size_t)INT64_MAX) {
            failure = "argument size overflow"; break;
        }
        if (!freak_v4_system_utf8_valid(argument, length)) {
            failure = "argument is not valid UTF-8"; break;
        }
        char *copy = (char *)malloc(length + 1);
        if (!copy) { failure = "argument snapshot allocation failed"; break; }
        memcpy(copy, argument, length + 1);
        staged[completed].bytes = copy;
        staged[completed].length = length;
#endif
    }
#ifdef _WIN32
    LocalFree(wide);
#endif
    if (failure) {
        freak_v4_arguments_free(staged, completed);
        freak_v4_system_fail(failure);
    }
    if (!freak_v4_arguments_cleanup_registered) {
        if (atexit(freak_v4_process_shutdown_args) != 0) {
            freak_v4_arguments_free(staged, count);
            freak_v4_system_fail("could not register argument cleanup");
        }
        freak_v4_arguments_cleanup_registered = true;
    }
    freak_v4_process_shutdown_args();
    freak_v4_arguments = staged;
    freak_v4_argument_count = count;
}

int64_t freak_v4_process_args_count(void) {
    return (int64_t)freak_v4_argument_count;
}

int64_t freak_v4_process_arg(int64_t index) {
    if (index < 0 || (uint64_t)index >= freak_v4_argument_count)
        return freak_v4_word_from_bytes(0, 0);
    const freak_v4_argument *argument = &freak_v4_arguments[(size_t)index];
    return freak_v4_word_from_bytes((int64_t)(uintptr_t)argument->bytes,
                                   (int64_t)argument->length);
}

static void freak_v4_fs_error(int64_t *tag, int64_t *payload, const char *message) {
    int64_t owner = freak_v4_word_from_bytes((int64_t)(uintptr_t)message,
                                           (int64_t)strlen(message));
    *payload = owner;
    *tag = 0;
}

static void freak_v4_fs_close_descriptor(int descriptor) {
#ifdef _WIN32
    _close(descriptor);
#else
    close(descriptor);
#endif
}

void freak_v4_fs_read(int64_t path, int64_t *out_is_ok, int64_t *out_payload) {
    if (!out_is_ok || !out_payload || out_is_ok == out_payload)
        freak_v4_system_fail("invalid filesystem result slots");
    *out_is_ok = 0;
    *out_payload = 0;
    /* Validate registry ownership before touching input bytes. The legacy size
       fallback accepts foreign C strings and must not authorize this ABI. */
    size_t length = 0;
    if (!freak_llvm_word_owned_size(path, &length))
        freak_v4_system_fail("filesystem path is not a live owned word");
    /* Registry membership alone does not make impossible byte counts safe to
       inspect. Admit the byte count before scanning or allocating a pathname. */
    if (length >= SIZE_MAX || (uintmax_t)length > (uintmax_t)INT64_MAX
#ifdef _WIN32
            || length > (size_t)INT_MAX
#endif
            ) {
        freak_v4_fs_error(out_is_ok, out_payload, "filesystem path size overflow");
        return;
    }
    const char *bytes = (const char *)(uintptr_t)path;
    const char *error = NULL;
    if (!length) error = "filesystem path is empty";
    else if (memchr(bytes, 0, length)) error = "filesystem path contains NUL";
    else if (!freak_v4_system_utf8_valid(bytes, length))
        error = "filesystem path is not valid UTF-8";
    int descriptor = -1;
    if (!error) {
#ifdef _WIN32
        int wide_length = !error ? MultiByteToWideChar(CP_UTF8,
                MB_ERR_INVALID_CHARS, bytes, (int)length, NULL, 0) : 0;
        if (!error && wide_length <= 0) error = "could not convert filesystem path";
        wchar_t *name = NULL;
        if (!error) {
            if ((size_t)wide_length > SIZE_MAX / sizeof(wchar_t) - 1)
                error = "filesystem path size overflow";
            else name = (wchar_t *)malloc(((size_t)wide_length + 1) * sizeof(wchar_t));
            if (!error && !name) error = "filesystem path allocation failed";
        }
        if (!error) {
            if (MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, bytes,
                    (int)length, name, wide_length) != wide_length) {
                error = "could not convert filesystem path";
            } else {
                name[wide_length] = 0;
                descriptor = _wopen(name, _O_RDONLY | _O_BINARY);
            }
        }
#else
        char *name = (char *)malloc(length + 1);
        if (!name) error = "filesystem path allocation failed";
        if (!error) {
            memcpy(name, bytes, length);
            name[length] = 0;
            descriptor = open(name, O_RDONLY | O_NONBLOCK);
        }
#endif
        free(name);
        if (!error && descriptor < 0) error = "could not open filesystem file";
    }
    if (error) {
        freak_v4_fs_error(out_is_ok, out_payload, error);
        return;
    }
#ifdef _WIN32
    struct _stat64 metadata;
    bool regular = _fstat64(descriptor, &metadata) == 0 &&
        (metadata.st_mode & _S_IFMT) == _S_IFREG;
#else
    struct stat metadata;
    bool regular = fstat(descriptor, &metadata) == 0 && S_ISREG(metadata.st_mode);
#endif
    if (!regular) {
        freak_v4_fs_close_descriptor(descriptor);
        freak_v4_fs_error(out_is_ok, out_payload,
                         "filesystem path is not a readable regular file");
        return;
    }
#ifdef _WIN32
    FILE *file = _fdopen(descriptor, "rb");
#else
    FILE *file = fdopen(descriptor, "rb");
#endif
    if (!file) {
        freak_v4_fs_close_descriptor(descriptor);
        freak_v4_fs_error(out_is_ok, out_payload, "could not open filesystem stream");
        return;
    }
    if (metadata.st_size < 0 ||
            (uintmax_t)metadata.st_size >= (uintmax_t)SIZE_MAX ||
            (uintmax_t)metadata.st_size > (uintmax_t)INT64_MAX) {
        error = "filesystem file size overflow";
    } else if (fseek(file, 0, SEEK_SET) != 0) {
        error = "could not seek filesystem file";
    }
    char *contents = NULL;
    size_t file_length = !error ? (size_t)metadata.st_size : 0;
    if (!error) {
        contents = (char *)malloc(file_length + 1);
        if (!contents) error = "filesystem contents allocation failed";
    }
    if (!error) {
        size_t count = fread(contents, 1, file_length, file);
        bool complete = count == file_length && !ferror(file);
        if (complete) complete = fgetc(file) == EOF && !ferror(file);
        if (!complete) error = "could not read complete filesystem file";
    }
    if (fclose(file) != 0 && !error) error = "could not close filesystem file";
    if (!error && !freak_v4_system_utf8_valid(contents, file_length))
        error = "filesystem file is not valid UTF-8";
    int64_t owner = 0;
    if (!error) {
        contents[file_length] = 0;
        owner = freak_llvm_word_try_adopt_sized((int64_t)(uintptr_t)contents, file_length);
        if (!owner) error = "filesystem contents ownership allocation failed";
    }
    if (error) {
        free(contents);
        freak_v4_fs_error(out_is_ok, out_payload, error);
        return;
    }
    *out_payload = owner;
    *out_is_ok = 1;
}
