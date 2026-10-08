#!/usr/bin/env python3
"""Verify real POSIX launch failures and deterministic private-handshake faults.

The fixture includes the shipping runtime and interposes syscall names only in
its own translation unit. It exercises both scalar ABIs without a language
compiler. Native macOS execution remains a separate gate when run on Linux.
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
import sys
import tempfile


CHILD = r'''
#define _POSIX_C_SOURCE 200809L
#include <string.h>
#include <time.h>
int main(int argc, char **argv) {
    if (argc > 1 && strcmp(argv[1], "sleep") == 0) {
        struct timespec delay = {3, 0}; nanosleep(&delay, 0);
    }
    return argc > 1 && strcmp(argv[1], "zero") == 0 ? 0 : 127;
}
'''

HARNESS = r'''
#ifdef __APPLE__
/* The fixture includes SDK headers before the runtime. Enable Darwin's
   no-follow and BSD interfaces before their include guards become fixed. */
#define _DARWIN_C_SOURCE 1
#endif
#define _GNU_SOURCE
#define _POSIX_C_SOURCE 200809L
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <stdarg.h>
#include <stdint.h>
#include <signal.h>
#include "freak_runtime.h"
enum fault_kind { CLEAN, GROUP, FAMILY_FD, TERMINAL, STDOUT_FD, STDERR_FD,
    EXEC_DENIED, PARTIAL, BAD_STAGE, ZERO_ERRNO, NEGATIVE_ERRNO, OVERSIZED,
    WRITE_EINTR, READ_ERROR, LAUNCH_DELAY, GUARDIAN,
    ORDERED_GROUP, ORDERED_FAST, ORDERED_ZERO, PRIMARY_FORK, PRIMARY_GROUP,
    GUARDIAN_FORK, READY_READ, READY_EOF, READY_BAD, READY_READ_EINTR,
    READY_WRITE, READY_SHORT, READY_WRITE_EINTR, PRIMARY_REAPED,
    GUARDIAN_GROUP_REAPED, GUARDIAN_REAPED };
static int fault;
static pid_t owner;
static int write_attempts;
static int read_attempts, fork_attempts, ready_write_attempts;
static int ordering[2] = {-1,-1};
static int ordering_sent;
static int primary_child;
static pid_t retired_primary;
static pid_t primary_group, retired_group, retired_guardian;
static int guardian_fork_failed, cancelled_before_eof;
static pid_t test_fork(void);
static int test_kill(pid_t pid, int signal);
static int test_close(int fd);
static int test_setpgid(pid_t pid, pid_t group);
static int test_fcntl(int fd, int operation, ...);
static int test_dup2(int oldfd, int newfd);
static int test_isatty(int fd);
static pid_t test_tcgetpgrp(int fd);
static int test_tcsetpgrp(int fd, pid_t group);
static int test_execve(const char *path, char *const argv[], char *const env[]);
static ssize_t test_write(int fd, const void *data, size_t size);
static ssize_t test_read(int fd, void *data, size_t size);
#define fork test_fork
#define kill test_kill
#define close test_close
#define setpgid test_setpgid
#define fcntl test_fcntl
#define dup2 test_dup2
#define isatty test_isatty
#define tcgetpgrp test_tcgetpgrp
#define tcsetpgrp test_tcsetpgrp
#define execve test_execve
#define write test_write
#define read test_read
#include "freak_runtime.c"
#undef fork
#undef kill
#undef close
#undef setpgid
#undef fcntl
#undef dup2
#undef isatty
#undef tcgetpgrp
#undef tcsetpgrp
#undef execve
#undef write
#undef read
static int ordered_fault(void) { return fault >= ORDERED_GROUP && fault <= ORDERED_ZERO; }
static void ordering_marker(unsigned char marker) {
    if (!ordered_fault() || !primary_child || ordering_sent) return;
    ssize_t sent;
    do { sent = write(ordering[1], &marker, 1); } while (sent < 0 && errno == EINTR);
    if (sent != 1) _exit(94);
    ordering_sent = 1;
}
static pid_t test_fork(void) {
    int attempt = ++fork_attempts;
    if ((fault == PRIMARY_FORK && attempt == 1) ||
        ((fault == GUARDIAN_FORK || fault == GUARDIAN_GROUP_REAPED) && attempt == 2)) {
        guardian_fork_failed = attempt == 2;
        errno = EAGAIN; return -1;
    }
    pid_t child = fork();
    if (child == 0) primary_child = attempt == 1;
    return child;
}
static int test_kill(pid_t pid, int signal) {
    if (fault == PRIMARY_REAPED && getpid() == owner && pid == retired_primary && pid > 0) _exit(97);
    if (fault == GUARDIAN_GROUP_REAPED && getpid() == owner && pid == -primary_group && primary_group > 0) {
        if (retired_group == primary_group) _exit(100);
        cancelled_before_eof = 1;
    }
    if (fault == GUARDIAN_REAPED && getpid() == owner && pid == retired_guardian && pid > 0) _exit(101);
    return kill(pid,signal);
}
static int test_close(int fd) {
    int saved = errno;
    int observe_eof = fault == GUARDIAN_GROUP_REAPED && getpid() == owner &&
        guardian_fork_failed && !cancelled_before_eof &&
        (fcntl(fd,F_GETFL) & O_ACCMODE) == O_WRONLY;
    errno = saved;
    int result = close(fd), error = errno;
    if (result == 0 && observe_eof) {
        /* If the failed-guardian path releases readiness before cancellation,
           consume the primary after its actual EOF abort. A later negative
           group signal is forbidden once this identity has been retired. */
        siginfo_t exited; int observed;
        uint64_t deadline = freak_command_now_ms() + 2000;
        do {
            memset(&exited,0,sizeof(exited));
            observed = waitid(P_PID,(id_t)primary_group,&exited,WEXITED|WNOWAIT|WNOHANG);
            if (observed < 0 || exited.si_pid == primary_group) break;
            (void)poll(NULL,0,1);
        } while (freak_command_now_ms() < deadline);
        if (observed != 0 || exited.si_pid != primary_group ||
                exited.si_code != CLD_EXITED || exited.si_status != 127) _exit(102);
        pid_t reaped; do { reaped = waitpid(primary_group,NULL,0); } while (reaped < 0 && errno == EINTR);
        if (reaped != primary_group) _exit(103);
        retired_group = primary_group;
    }
    errno = error; return result;
}
static int test_setpgid(pid_t pid, pid_t group) {
    if (getpid() == owner && pid > 0 && group == pid) primary_group = pid;
    if (fault == GUARDIAN_REAPED && !primary_child && getpid() != owner && pid == 0 && group > 0) {
        errno = EPERM; return -1;
    }
    if (fault == GUARDIAN_REAPED && getpid() == owner && pid > 0 && group != pid) {
        /* The guardian is forced to fail its own join. Retire its actual child
           identity before returning the parent's join error; signalling that
           numeric PID afterward must never be part of runtime cleanup. */
        siginfo_t exited; int observed;
        uint64_t deadline = freak_command_now_ms() + 2000;
        do {
            memset(&exited,0,sizeof(exited));
            observed = waitid(P_PID,(id_t)pid,&exited,WEXITED|WNOWAIT|WNOHANG);
            if (observed < 0 || exited.si_pid == pid) break;
            (void)poll(NULL,0,1);
        } while (freak_command_now_ms() < deadline);
        if (observed != 0 || exited.si_pid != pid ||
                exited.si_code != CLD_EXITED || exited.si_status != 127) _exit(104);
        pid_t reaped; do { reaped = waitpid(pid,NULL,0); } while (reaped < 0 && errno == EINTR);
        if (reaped != pid) _exit(105);
        retired_guardian = pid; errno = ESRCH; return -1;
    }
    if (fault == PRIMARY_REAPED && getpid() == owner && pid > 0 && group == pid) {
        /* The fixture still owns this blocked primary when it kills/reaps it.
           Thereafter the kill wrapper rejects any runtime signal of its now
           retired numeric PID; no actual PID recycling is needed. */
        if (kill(pid,SIGKILL) < 0) _exit(98);
        pid_t reaped; do { reaped = waitpid(pid,NULL,0); } while (reaped < 0 && errno == EINTR);
        if (reaped != pid) _exit(99);
        retired_primary = pid; errno = ESRCH; return -1;
    }
    if (ordered_fault() && getpid() == owner && pid > 0 && group == pid) {
        /* An independent fixture pipe observes either the primary waiting at
           the readiness gate (R), or its old ungated setup/exec path (E).
           Only a child actually observed exited can model an absent group.
           This deterministic fault is not a claim about macOS zombie groups. */
        struct pollfd event = {ordering[0],POLLIN,0};
        int available; do { available = poll(&event,1,2000); } while (available < 0 && errno == EINTR);
        unsigned char marker = 0;
        if (available <= 0 || read(ordering[0],&marker,1) != 1) _exit(95);
        if (marker != 'R') {
            siginfo_t exited; int observed;
            uint64_t deadline = freak_command_now_ms() + 2000;
            do {
                memset(&exited,0,sizeof(exited));
                observed = waitid(P_PID,(id_t)pid,&exited,WEXITED|WNOWAIT|WNOHANG);
                if (observed < 0 || exited.si_pid == pid) break;
                (void)poll(NULL,0,1);
            } while (freak_command_now_ms() < deadline);
            if (observed != 0 || exited.si_pid != pid || exited.si_code != CLD_EXITED ||
                    exited.si_status != (fault == ORDERED_ZERO ? 0 : 127)) _exit(96);
            errno = ESRCH; return -1;
        }
    }
    if ((fault == PRIMARY_GROUP && getpid() == owner && pid > 0 && group == pid) ||
        ((fault == GROUP || fault == ORDERED_GROUP) && primary_child && pid == 0 && group == 0) ||
        (fault == GUARDIAN && getpid() == owner && pid > 0 && group != pid)) {
        errno = fault == PRIMARY_GROUP ? ESRCH : EPERM; return -1;
    }
    /* Before the repair this models a fast child that never formed a group.
       With the readiness gate the parent's successful setpgid already did so. */
    if ((fault == ORDERED_FAST || fault == ORDERED_ZERO) && primary_child && pid == 0 && group == 0) return 0;
    return setpgid(pid, group);
}
static int test_fcntl(int fd, int operation, ...) {
    va_list values; va_start(values, operation);
    if (operation == F_GETFD || operation == F_GETFL) {
        va_end(values); return fcntl(fd, operation);
    }
    if (operation == F_SETLK || operation == F_SETLKW || operation == F_GETLK) {
        struct flock *argument = va_arg(values, struct flock *); va_end(values);
        return fcntl(fd, operation, argument);
    }
#ifdef F_GETPATH
    if (operation == F_GETPATH) {
        char *argument = va_arg(values, char *); va_end(values);
        return fcntl(fd, operation, argument);
    }
#endif
    int argument = va_arg(values, int); va_end(values);
    if (fault == FAMILY_FD && getpid() != owner && operation == F_SETFD && argument == 0) {
        errno = EBADF; return -1;
    }
    return fcntl(fd, operation, argument);
}
static int test_dup2(int oldfd, int newfd) {
    if (getpid() != owner && ((fault == STDOUT_FD && newfd == STDOUT_FILENO) ||
                             (fault == STDERR_FD && newfd == STDERR_FILENO))) {
        errno = newfd == STDOUT_FILENO ? EBADF : EIO; return -1;
    }
    return dup2(oldfd, newfd);
}
static int test_isatty(int fd) { return fault == TERMINAL ? 1 : isatty(fd); }
static pid_t test_tcgetpgrp(int fd) { return fault == TERMINAL ? getpgrp() : tcgetpgrp(fd); }
static int test_tcsetpgrp(int fd, pid_t group) {
    if (fault == TERMINAL) {
        if (getpid() != owner) { errno = EPERM; return -1; }
        return 0;
    }
    return tcsetpgrp(fd, group);
}
static int test_execve(const char *path, char *const argv[], char *const env[]) {
    if (fault == LAUNCH_DELAY) { struct timespec delay = {3, 0}; nanosleep(&delay, NULL); }
    if (fault == EXEC_DENIED || (fault >= PARTIAL && fault <= WRITE_EINTR)) {
        errno = EPERM; return -1;
    }
    ordering_marker('E');
    return execve(path, argv, env);
}
/* This independent wire oracle deliberately does not use the runtime's type. */
static ssize_t test_write(int fd, const void *data, size_t size) {
    if (getpid() == owner && size == 1) {
        if (fault == READY_WRITE) { errno = EIO; return -1; }
        if (fault == READY_SHORT) return 0;
        if (fault == READY_WRITE_EINTR && ready_write_attempts++ == 0) { errno = EINTR; return -1; }
    }
    if (getpid() != owner && size == 8) {
        struct { int32_t error; uint32_t stage; } wire;
        memcpy(&wire, data, sizeof(wire));
        if (fault == WRITE_EINTR && write_attempts++ == 0) { errno = EINTR; return -1; }
        if (fault == PARTIAL) return write(fd, data, 3);
        if (fault == BAD_STAGE) wire.stage = UINT32_MAX;
        if (fault == ZERO_ERRNO) wire.error = 0;
        if (fault == NEGATIVE_ERRNO) wire.error = -EPERM;
        if (fault == OVERSIZED) {
            unsigned char oversized[9]; memcpy(oversized, &wire, sizeof(wire)); oversized[8] = 1;
            return write(fd, oversized, sizeof(oversized));
        }
        ssize_t sent = write(fd, &wire, sizeof(wire));
        if (sent == sizeof(wire)) ordering_marker('E');
        return sent;
    }
    return write(fd, data, size);
}
static ssize_t test_read(int fd, void *data, size_t size) {
    if (primary_child && size == 1) {
        ordering_marker('R');
        if (fault == READY_READ_EINTR && read_attempts++ == 0) { errno = EINTR; return -1; }
        /* Admit rejection controls only after the real readiness token. The
           parent and guardian have formed the group before this child exits;
           these faults exercise validation, not an early artificial exit. */
        ssize_t received = read(fd,data,size);
        if (received == 1) {
            if (fault == READY_READ) { errno = EIO; return -1; }
            if (fault == READY_EOF) return 0;
            if (fault == READY_BAD) *(unsigned char *)data = 2;
        }
        return received;
    }
    if (fault == READ_ERROR && getpid() == owner && size == 9) { errno = EIO; return -1; }
    return read(fd, data, size);
}

#ifdef USE_LLVM_ADAPTER
extern void freak_llvm_word_release_replaced(int64_t previous, int64_t replacement);
#define command_new(s) freak_llvm_process_command_new((int64_t)(intptr_t)(s))
#define argument(h,s) freak_llvm_process_command_arg(h,(int64_t)(intptr_t)(s))
#define cwd(h,s) freak_llvm_process_command_cwd(h,(int64_t)(intptr_t)(s))
#define run freak_llvm_process_command_run
#define run_inherit freak_llvm_process_command_run_inherit
#define exit_code freak_llvm_process_command_exit_code
#define release freak_llvm_process_command_release
static freak_word error_word(int64_t h) { return freak_llvm_word_view(freak_llvm_process_command_error(h)); }
static void drop_word(freak_word *word) { freak_llvm_word_release_replaced((int64_t)(intptr_t)word->data, 0); *word = freak_word_lit(""); }
#else
#define command_new(s) freak_process_command_new(freak_word_lit(s))
#define argument(h,s) freak_process_command_arg(h,freak_word_lit(s))
#define cwd(h,s) freak_process_command_cwd(h,freak_word_lit(s))
#define run freak_process_command_run
#define run_inherit freak_process_command_run_inherit
#define exit_code freak_process_command_exit_code
#define release freak_process_command_release
#define error_word freak_process_command_error
#define drop_word freak_word_release_owned
#endif
static void require(int condition, const char *reason) {
    if (!condition) { fprintf(stderr,"FAIL: %s\n",reason); exit(2); }
}
static void zero_owners(void) {
    require(freak_process_command_live() == 0, "command tickets released");
    require(freak_process_command_children() == 0, "primary and guardian reaped");
    require(freak_process_command_retained_bytes() == 0, "command allocations released");
    require(freak_fs_result_live() == 0, "filesystem tickets conserved");
}
static size_t descriptors(void) {
    size_t count; int *open = freak_command_open_descriptors(&count);
    require(open != NULL,"enumerate descriptors"); free(open); return count;
}

static void case_require(int condition, const char *label, const char *field,
        int64_t command, int64_t status, int expected_status, freak_word *error) {
    if (condition) return;
    fprintf(stderr,"FAIL: %s field=%s status=%lld expected=%d exit=%lld error=",label,field,
            (long long)status,expected_status,(long long)exit_code(command));
    for (size_t i=0;i<error->length;i++) fprintf(stderr,"%02x",(unsigned char)error->data[i]);
    fputc('\n',stderr); drop_word(error); release(command); exit(2);
}
static void check(const char *label, const char *path, const char *directory,
        const char *mode, int injected, int expected_status, const char *stage, int expected_errno) {
    fault = injected; write_attempts = read_attempts = fork_attempts = ready_write_attempts = 0;
    primary_child = ordering_sent = 0; retired_primary = 0;
    primary_group = retired_group = retired_guardian = 0;
    guardian_fork_failed = cancelled_before_eof = 0;
    if (ordered_fault()) require(freak_command_pipe(ordering),"ordering witness pipe");
    int64_t command = command_new(path);
    if (directory) cwd(command,directory);
    if (mode) argument(command,mode);
    int64_t status = injected == TERMINAL ? run_inherit(command,1000) :
        run(command,expected_status == FREAK_COMMAND_TIMED_OUT ? 80 : 2000,128,128);
    freak_word error = error_word(command);
#define CASE_REQUIRE(condition,field) case_require((condition),label,(field),command,status,expected_status,&error)
    CASE_REQUIRE(status == expected_status,"status");
    if (stage) {
        char expected[128]; snprintf(expected,sizeof(expected),"(stage=%s, errno=%d)",stage,expected_errno);
        CASE_REQUIRE(strncmp(error.data,"could not launch executable: ",29) == 0,"prefix");
        CASE_REQUIRE(strstr(error.data,expected) != NULL,"stage/errno");
        CASE_REQUIRE(strstr(error.data,strerror(expected_errno)) != NULL,"strerror");
    } else if (expected_status == FREAK_COMMAND_SPAWN_FAILED) {
        const char *expected = (injected == GUARDIAN || injected == PRIMARY_FORK || injected == PRIMARY_GROUP ||
            injected == GUARDIAN_FORK || injected == READY_WRITE || injected == READY_SHORT ||
            injected == PRIMARY_REAPED || injected == GUARDIAN_GROUP_REAPED ||
            injected == GUARDIAN_REAPED) ? "could not create child process: " :
            "could not launch executable: exec status pipe failed";
        CASE_REQUIRE(strncmp(error.data,expected,strlen(expected)) == 0,"generic prefix");
        CASE_REQUIRE(strstr(error.data,"stage=") == NULL && strstr(error.data,"errno=") == NULL,"generic fields");
    } else if (expected_status == FREAK_COMMAND_EXITED) {
        CASE_REQUIRE(exit_code(command) == (injected == ORDERED_ZERO ? 0 : 127) && error.length == 0,"exit/error");
    } else CASE_REQUIRE(strstr(error.data,"stage=") == NULL,"timeout fields");
#undef CASE_REQUIRE
    printf("%s %s status=%lld error=",injected >= ORDERED_GROUP ? "SUPCASE" : "CASE",label,(long long)status);
    for (size_t i=0;i<error.length;i++) printf("%02x",(unsigned char)error.data[i]);
    putchar('\n'); drop_word(&error); release(command); zero_owners();
    freak_command_close_pipe(&ordering[0]); freak_command_close_pipe(&ordering[1]); fault = CLEAN;
}
int main(int argc, char **argv) {
    require(argc == 6,"child/missing/denied/script/missing-directory arguments"); owner = getpid();
    check("exit127",argv[1],NULL,NULL,CLEAN,FREAK_COMMAND_EXITED,NULL,0);
    size_t before = descriptors();
    check("missing",argv[2],NULL,NULL,CLEAN,FREAK_COMMAND_SPAWN_FAILED,"execve",ENOENT);
    check("denied",argv[3],NULL,NULL,CLEAN,FREAK_COMMAND_SPAWN_FAILED,"execve",EACCES);
    check("no-shell",argv[4],NULL,NULL,CLEAN,FREAK_COMMAND_SPAWN_FAILED,"execve",ENOEXEC);
    check("chdir",argv[1],argv[5],NULL,CLEAN,FREAK_COMMAND_SPAWN_FAILED,"chdir",ENOENT);
    check("setpgid",argv[1],NULL,NULL,GROUP,FREAK_COMMAND_SPAWN_FAILED,"setpgid",EPERM);
    check("family-fd",argv[1],NULL,NULL,FAMILY_FD,FREAK_COMMAND_SPAWN_FAILED,"family-fd",EBADF);
    check("terminal",argv[1],NULL,NULL,TERMINAL,FREAK_COMMAND_SPAWN_FAILED,"terminal",EPERM);
    check("stdout",argv[1],NULL,NULL,STDOUT_FD,FREAK_COMMAND_SPAWN_FAILED,"stdout",EBADF);
    check("stderr",argv[1],NULL,NULL,STDERR_FD,FREAK_COMMAND_SPAWN_FAILED,"stderr",EIO);
    check("execve-denied",argv[1],NULL,NULL,EXEC_DENIED,FREAK_COMMAND_SPAWN_FAILED,"execve",EPERM);
    check("partial",argv[1],NULL,NULL,PARTIAL,FREAK_COMMAND_SPAWN_FAILED,NULL,0);
    check("unknown-stage",argv[1],NULL,NULL,BAD_STAGE,FREAK_COMMAND_SPAWN_FAILED,NULL,0);
    check("zero-errno",argv[1],NULL,NULL,ZERO_ERRNO,FREAK_COMMAND_SPAWN_FAILED,NULL,0);
    check("negative-errno",argv[1],NULL,NULL,NEGATIVE_ERRNO,FREAK_COMMAND_SPAWN_FAILED,NULL,0);
    check("oversized",argv[1],NULL,NULL,OVERSIZED,FREAK_COMMAND_SPAWN_FAILED,NULL,0);
    check("write-eintr",argv[1],NULL,NULL,WRITE_EINTR,FREAK_COMMAND_SPAWN_FAILED,"execve",EPERM);
    check("read-error",argv[1],NULL,"sleep",READ_ERROR,FREAK_COMMAND_SPAWN_FAILED,NULL,0);
    check("launch-deadline",argv[1],NULL,NULL,LAUNCH_DELAY,FREAK_COMMAND_TIMED_OUT,NULL,0);
    check("run-deadline",argv[1],NULL,"sleep",CLEAN,FREAK_COMMAND_TIMED_OUT,NULL,0);
    check("guardian-setup",argv[1],NULL,"sleep",GUARDIAN,FREAK_COMMAND_SPAWN_FAILED,NULL,0);
    check("ordered-setpgid",argv[1],NULL,NULL,ORDERED_GROUP,FREAK_COMMAND_SPAWN_FAILED,"setpgid",EPERM);
    check("ordered-exit127",argv[1],NULL,NULL,ORDERED_FAST,FREAK_COMMAND_EXITED,NULL,0);
    check("ordered-exit0",argv[1],NULL,"zero",ORDERED_ZERO,FREAK_COMMAND_EXITED,NULL,0);
    check("primary-fork",argv[1],NULL,NULL,PRIMARY_FORK,FREAK_COMMAND_SPAWN_FAILED,NULL,0);
    check("primary-group",argv[1],NULL,NULL,PRIMARY_GROUP,FREAK_COMMAND_SPAWN_FAILED,NULL,0);
    check("guardian-fork",argv[1],NULL,NULL,GUARDIAN_FORK,FREAK_COMMAND_SPAWN_FAILED,NULL,0);
    check("ready-read",argv[1],NULL,NULL,READY_READ,FREAK_COMMAND_SPAWN_FAILED,"guardian-ready",EIO);
    check("ready-eof",argv[1],NULL,NULL,READY_EOF,FREAK_COMMAND_SPAWN_FAILED,"guardian-ready",EIO);
    check("ready-bad",argv[1],NULL,NULL,READY_BAD,FREAK_COMMAND_SPAWN_FAILED,"guardian-ready",EIO);
    check("ready-read-eintr",argv[1],NULL,NULL,READY_READ_EINTR,FREAK_COMMAND_EXITED,NULL,0);
    check("ready-write",argv[1],NULL,NULL,READY_WRITE,FREAK_COMMAND_SPAWN_FAILED,NULL,0);
    check("ready-short",argv[1],NULL,NULL,READY_SHORT,FREAK_COMMAND_SPAWN_FAILED,NULL,0);
    check("ready-write-eintr",argv[1],NULL,NULL,READY_WRITE_EINTR,FREAK_COMMAND_EXITED,NULL,0);
    check("primary-reaped",argv[1],NULL,NULL,PRIMARY_REAPED,FREAK_COMMAND_SPAWN_FAILED,NULL,0);
    check("guardian-group-reaped",argv[1],NULL,NULL,GUARDIAN_GROUP_REAPED,FREAK_COMMAND_SPAWN_FAILED,NULL,0);
    check("guardian-reaped",argv[1],NULL,NULL,GUARDIAN_REAPED,FREAK_COMMAND_SPAWN_FAILED,NULL,0);
    require(descriptors() == before,"kernel descriptor conservation");
    puts("POSIX_LAUNCH_DIAGNOSTIC_OK cases=21");
    puts("POSIX_LAUNCH_STARTUP_OK cases=16"); return 0;
}
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clang', default=os.environ.get('FREAK_CLANG', 'clang'))
    parser.add_argument('--optimization', type=int, choices=(0, 2, 3), action='append')
    parser.add_argument('--sanitize', action='store_true')
    parser.add_argument('--work-dir', type=Path, help='retain generated fixtures in this directory')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if os.name == 'nt':
        print('POSIX launch diagnostics require Linux or macOS; no Windows execution claimed.')
        return 0
    clang = shutil.which(args.clang)
    assert clang, args.clang
    repo = Path(__file__).resolve().parents[1]
    runtime = repo / 'freakc/runtime'
    inputs = sorted([Path(__file__).resolve(), *runtime.glob('*.c'), *runtime.glob('*.h'),
                     *runtime.glob('*.inc'), *(p for p in (repo/'third_party/llhttp').rglob('*') if p.is_file())])
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    before = {str(p.relative_to(repo)): digest(p) for p in inputs}
    records = []
    report = {'status': 'running', 'host': sys.platform, 'inputs': before, 'commands': records,
              'sanitizers_enabled': args.sanitize, 'optimization_profile': args.optimization or [0, 2, 3],
              'scalar_ABIs': ['c', 'llvm']}
    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=1:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1')
    def run(command: list[str], label: str) -> subprocess.CompletedProcess[bytes]:
        result = subprocess.run(command, capture_output=True, env=env, timeout=90)
        records.append({'label': label, 'argv': command, 'returncode': result.returncode,
                        'stdout_hex': result.stdout.hex(), 'stderr_hex': result.stderr.hex()})
        return result
    if args.work_dir:
        args.work_dir.mkdir(parents=True, exist_ok=True)
    workspace = nullcontext(str(args.work_dir.resolve())) if args.work_dir else tempfile.TemporaryDirectory(prefix='freak-posix-launch-')
    try:
        with workspace as directory:
            work = Path(directory)
            child_source, harness_source = work/'child.c', work/'harness.c'
            child_source.write_text(CHILD); harness_source.write_text(HARNESS)
            child = work/"child é 日本 ' $ &"
            result = run([clang, '-std=c11', '-O2', str(child_source), '-o', str(child)], 'child-build')
            assert result.returncode == 0, records[-1]
            denied = work/'denied'
            shutil.copy2(child, denied); denied.chmod(0o600)
            script = work/'no-shebang'; script.write_text('exit 0\n'); script.chmod(0o700)
            strict = ['-std=c11', '-Werror=implicit-function-declaration', '-Werror=incompatible-pointer-types',
                      '-Werror=int-conversion', '-Werror=return-type', f'-I{runtime}']
            sanitizer = ['-fsanitize=address,undefined', '-fno-sanitize-recover=all', '-fno-omit-frame-pointer', '-g'] if args.sanitize else []
            if args.sanitize:
                control_source = work/'sanitizer-control.c'
                control_source.write_text('int main(void) { volatile int a=2147483647; return a+1; }\n')
                control = work/'sanitizer-control'
                result = run([clang, '-O0', *sanitizer, str(control_source), '-o', str(control)], 'sanitizer-control-build')
                assert result.returncode == 0, records[-1]
                result = run([str(control)], 'sanitizer-control-run')
                assert result.returncode != 0 and b'runtime error' in result.stderr, records[-1]
            binaries = {}
            for optimization in args.optimization or (0, 2, 3):
                for abi in ('c', 'llvm'):
                    executable = work/f'launch-{abi}-O{optimization}'
                    command = [clang, *strict, f'-O{optimization}', *sanitizer,
                               '-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1', '-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1',
                               str(harness_source), str(runtime/'freak_llvm_runtime.c'), '-lm', '-o', str(executable)]
                    if abi == 'llvm': command.append('-DUSE_LLVM_ADAPTER=1')
                    result = run(command, f'build-{abi}-O{optimization}')
                    assert result.returncode == 0, records[-1]
                    binaries[executable.name] = digest(executable)
                    result = run([str(executable), str(child), str(work/'missing'), str(denied), str(script),
                                  str(work/'missing-directory')], f'run-{abi}-O{optimization}')
                    assert result.returncode == 0 and result.stderr == b'', records[-1]
                    assert sum(line.startswith(b'CASE ') for line in result.stdout.splitlines()) == 21, records[-1]
                    assert sum(line.startswith(b'SUPCASE ') for line in result.stdout.splitlines()) == 16, records[-1]
                    assert result.stdout.endswith(b'POSIX_LAUNCH_DIAGNOSTIC_OK cases=21\nPOSIX_LAUNCH_STARTUP_OK cases=16\n'), records[-1]
            report.update(status='pass', cases_per_ABI=21, supplemental_cases_per_ABI=16,
                          supplemental_case_contract='bounded native ordering witnesses and startup failure controls; original 21 unchanged', binaries=binaries,
                          fixture_hashes={'child': digest(child_source), 'harness': digest(harness_source)})
    finally:
        report['inputs_unchanged'] = before == {str(p.relative_to(repo)): digest(p) for p in inputs}
        if not report['inputs_unchanged']: report['status'] = 'fail'
        if report['status'] != 'pass': report['status'] = 'fail'
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, indent=2)+'\n')
    assert report['status'] == 'pass', report['status']
    print(f"POSIX launch diagnostics: original 21 + supplemental 16 cases per ABI passed on {sys.platform}; no foreign native execution claimed.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
