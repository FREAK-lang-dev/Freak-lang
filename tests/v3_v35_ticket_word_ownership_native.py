#!/usr/bin/env python3
"""Verify ticket word getters retain owned bytes across owner lifecycles.

Runs the shipping C runtime and its LLVM scalar adapters directly. Real public
failure/listing paths are complemented by bounded Unicode/empty error injection
and public ticket-table growth. No language compiler reconstruction is needed.
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
import time

HARNESS = r'''
#ifdef _WIN32
#ifndef _WIN32_WINNT
#define _WIN32_WINNT 0x0602
#endif
#endif
#ifdef __APPLE__
#define _DARWIN_C_SOURCE 1
#endif
#ifndef _WIN32
#define _POSIX_C_SOURCE 200809L
#endif
#include "freak_runtime.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
static int fail_next_malloc;
static int move_ticket_table;
static void *fixture_malloc(size_t size);
static void *fixture_realloc(void *pointer, size_t size);
#define malloc fixture_malloc
#define realloc fixture_realloc
#include "freak_runtime.c"
#undef malloc
#undef realloc
static void *fixture_malloc(size_t size) {
    if (fail_next_malloc) { fail_next_malloc = 0; return NULL; }
    return malloc(size);
}
static void *fixture_realloc(void *pointer, size_t size) {
    size_t old_size = 0;
    if (move_ticket_table && pointer) {
        if (pointer == freak_fs_tickets) old_size = freak_fs_tickets_capacity * sizeof(*freak_fs_tickets);
        else if (pointer == freak_json_documents) old_size = freak_json_document_capacity * sizeof(*freak_json_documents);
        else if (pointer == freak_commands) old_size = freak_commands_capacity * sizeof(*freak_commands);
    }
    if (!old_size) return realloc(pointer, size);
    if (size < old_size) { fprintf(stderr, "FAIL: unexpected ticket shrink\n"); exit(2); }
    void *replacement = malloc(size);
    if (!replacement) return NULL;
    memcpy(replacement, pointer, old_size); free(pointer); return replacement;
}
extern void freak_llvm_word_release_replaced(int64_t, int64_t);
#ifdef USE_LLVM_ADAPTER
#define FS(name) freak_llvm_fs_##name
#define CMD(name) freak_llvm_process_command_##name
#define HTTP(name) freak_llvm_http_server_##name
#define JSON(name) freak_llvm_json_document_##name
#define WORD(text) ((int64_t)(intptr_t)(text))
#define GET(call) freak_llvm_word_view(call)
static void drop(freak_word *word) {
    freak_llvm_word_release_replaced((int64_t)(intptr_t)word->data, 0);
    *word = freak_word_lit("");
}
#else
#define FS(name) freak_fs_##name
#define CMD(name) freak_process_command_##name
#define HTTP(name) freak_http_server_##name
#define JSON(name) freak_json_document_##name
#define WORD(text) freak_word_lit(text)
#define GET(call) (call)
#define drop freak_word_release_owned
#endif
static void require(int condition, const char *reason) {
    if (!condition) { fprintf(stderr, "FAIL: %s\n", reason); exit(2); }
}
enum kind { FS_ERROR, JSON_ERROR, COMMAND_ERROR, SERVER_ERROR, REQUEST_ERROR, FS_ENTRY };
typedef struct { int64_t ticket, server; } owner;
static owner make_owner(int kind, const char *directory, const char *missing) {
    owner result = {0, 0};
    switch (kind) {
        case FS_ERROR: result.ticket = FS(read_ticket)(WORD(missing)); break;
        case JSON_ERROR: result.ticket = JSON(new)(); JSON(make_bool)(result.ticket, 2); break;
        case COMMAND_ERROR:
            result.ticket = CMD(new)(WORD(missing)); CMD(run)(result.ticket, 2000, 128, 128); break;
        case SERVER_ERROR: result.ticket = HTTP(bind)(WORD("not-an-ip"), 0, 0); break;
        case REQUEST_ERROR:
            result.server = HTTP(bind)(WORD("not-an-ip"), 0, 0);
            result.ticket = HTTP(next_request)(result.server); break;
        case FS_ENTRY:
            result.ticket = FS(list_dir_checked)(WORD(directory));
            require(FS(result_ok)(result.ticket) && FS(result_count)(result.ticket) == 1, "single real Unicode entry"); break;
    }
    return result;
}
static freak_word get_word(int kind, owner value) {
    switch (kind) {
        case FS_ERROR: return GET(FS(result_error)(value.ticket));
        case JSON_ERROR: return GET(JSON(error)(value.ticket));
        case COMMAND_ERROR: return GET(CMD(error)(value.ticket));
        case SERVER_ERROR: return GET(HTTP(error)(value.ticket));
        case REQUEST_ERROR: return GET(HTTP(request_error)(value.ticket));
        default: return GET(FS(result_entry)(value.ticket, 0));
    }
}
static void overwrite_error(int kind, owner value, const char *text) {
    char *destination = NULL;
    switch (kind) {
        case FS_ERROR: destination = freak_fs_ticket_require(value.ticket)->error; break;
        case JSON_ERROR: destination = freak_json_require(value.ticket)->error; break;
        case COMMAND_ERROR: destination = freak_command_require(value.ticket)->error; break;
        case SERVER_ERROR: destination = freak_http_require_server(value.ticket)->error; break;
        case REQUEST_ERROR: destination = freak_http_require_request(value.ticket)->error; break;
    }
    require(destination != NULL && strlen(text) < 160, "bounded error injection");
    strcpy(destination, text);
}
static void release_owner(int kind, owner value) {
    switch (kind) {
        case FS_ERROR: case FS_ENTRY: FS(result_release)(value.ticket); break;
        case JSON_ERROR: JSON(release)(value.ticket); break;
        case COMMAND_ERROR: CMD(release)(value.ticket); break;
        case SERVER_ERROR: HTTP(close)(value.ticket); break;
        case REQUEST_ERROR: HTTP(request_release)(value.ticket); HTTP(close)(value.server); break;
    }
}
static int oom_kind;
static owner oom_owner;
/* The fixture releases its setup owner before audit callbacks, so the forced
   allocation failure observes the production word diagnostic/exit policy. */
static void cleanup_oom_owner(void) { release_owner(oom_kind, oom_owner); }
static void owned(freak_word word) {
#ifdef USE_LLVM_ADAPTER
    size_t length = SIZE_MAX;
    require(freak_llvm_word_owned_size((int64_t)(intptr_t)word.data, &length) && length == word.length,
            "getter transferred exactly one owned LLVM word");
    require(freak_c_owned_word_count == 0, "C bookkeeping transferred to LLVM");
#else
    require(word.heap && word.data, "getter returned an owned C word");
#endif
}
static void equal(freak_word word, const char *bytes, size_t length) {
    require(word.length == length && memcmp(word.data, bytes, length) == 0 && word.data[length] == 0,
            "returned bytes survive owner mutation/release/reuse/growth");
}
static void zero_owners(void) {
    require(freak_fs_result_live() == 0 && freak_json_live_documents == 0 && freak_json_live_nodes == 0,
            "FS and JSON owners released");
    require(freak_process_command_live() == 0 && freak_process_command_children() == 0 &&
            freak_process_command_retained_bytes() == 0, "process owners and children released");
    require(freak_http_server_live_servers() == 0 && freak_http_server_live_requests() == 0 &&
            freak_http_server_live_sockets() == 0, "HTTP owners and sockets released");
    require(freak_c_owned_word_count == 0 && freak_llvm_owned_count == 0, "both word registries empty");
}
static void lifecycle(int kind, const char *directory, const char *missing, const char *seed) {
    owner initial = make_owner(kind, directory, missing);
    if (seed) overwrite_error(kind, initial, seed);
    freak_word first = get_word(kind, initial); owned(first);
    char expected[1024]; size_t length = first.length;
    require(length < sizeof(expected), "bounded expected bytes"); memcpy(expected, first.data, length);
    if (!seed) require(length > 0, "real public failure or entry is nonempty");
    freak_word second = freak_word_lit("");
    if (seed) {
        overwrite_error(kind, initial, "new owner message"); second = get_word(kind, initial); owned(second);
        require(first.data != second.data, "each getter owns a separate allocation");
    }
    release_owner(kind, initial);
    owner replacement = make_owner(kind, directory, missing);
    require((uint32_t)replacement.ticket == (uint32_t)initial.ticket && replacement.ticket != initial.ticket,
            "real slot reused with a fresh generation");
    equal(first, expected, length);
    if (seed) equal(second, "new owner message", 17);
    release_owner(kind, replacement); drop(&first); if (seed) drop(&second);
    zero_owners(); printf("CASE lifecycle kind=%d seed=%s\n", kind, seed ? (*seed ? "unicode" : "empty") : "public");
}
static size_t table_capacity(int kind) {
    return kind == FS_ERROR ? freak_fs_tickets_capacity : kind == JSON_ERROR ? freak_json_document_capacity : freak_commands_capacity;
}
static void *table_address(int kind) {
    return kind == FS_ERROR ? (void *)freak_fs_tickets : kind == JSON_ERROR ? (void *)freak_json_documents : (void *)freak_commands;
}
static owner quiet_owner(int kind, const char *directory) {
    owner value = {0, 0};
    if (kind == FS_ERROR) value.ticket = FS(stat_checked)(WORD(directory));
    else if (kind == JSON_ERROR) value.ticket = JSON(new)();
    else value.ticket = CMD(new)(WORD("not-launched"));
    return value;
}
static void successful_empty(int kind, const char *directory) {
    owner initial = kind == SERVER_ERROR ? (owner){HTTP(bind)(WORD("127.0.0.1"), 0, 0), 0} : quiet_owner(kind, directory);
    if (kind == FS_ERROR) require(FS(result_ok)(initial.ticket), "successful FS result");
    else if (kind == JSON_ERROR) require(JSON(ok)(initial.ticket), "healthy JSON document");
    else if (kind == COMMAND_ERROR) require(CMD(status)(initial.ticket) == FREAK_COMMAND_READY, "ready process command");
    else require(HTTP(status)(initial.ticket) == 0, "healthy HTTP server");
    freak_word saved = get_word(kind, initial); owned(saved); equal(saved, "", 0);
    release_owner(kind, initial); equal(saved, "", 0); drop(&saved); zero_owners();
    printf("CASE successful-empty kind=%d\n", kind);
}
static void growth(int kind, const char *directory) {
    owner initial = quiet_owner(kind, directory); overwrite_error(kind, initial, "grow \xce\xbb \xe6\x97\xa5\xe6\x9c\xac");
    freak_word saved = get_word(kind, initial); owned(saved);
    size_t previous_capacity = table_capacity(kind); require(previous_capacity < 128, "bounded table fixture");
    void *previous_address = table_address(kind); move_ticket_table = 1;
    owner owners[128]; size_t count = 0;
    do { owners[count++] = quiet_owner(kind, directory); } while (table_capacity(kind) == previous_capacity && count < 128);
    move_ticket_table = 0;
    require(table_capacity(kind) > previous_capacity, "real public constructors grew the ticket table");
    require(table_address(kind) != previous_address, "fixture realloc moved the actual ticket table");
    overwrite_error(kind, initial, "overwritten after growth");
    equal(saved, "grow \xce\xbb \xe6\x97\xa5\xe6\x9c\xac", 14);
    release_owner(kind, initial);
    for (size_t i = 0; i < count; i++) release_owner(kind, owners[i]);
    equal(saved, "grow \xce\xbb \xe6\x97\xa5\xe6\x9c\xac", 14); drop(&saved); zero_owners();
    printf("CASE table-growth kind=%d\n", kind);
}
int main(int argc, char **argv) {
    require(argc == 4, "mode, directory, missing path");
    if (!strcmp(argv[1], "leak")) {
        owner value = make_owner(FS_ERROR, argv[2], argv[3]);
        freak_word saved = get_word(FS_ERROR, value); owned(saved); release_owner(FS_ERROR, value);
        puts("INTENTIONAL_OWNED_WORD_LEAK"); return 0;
    }
    if (!strncmp(argv[1], "oom-", 4)) {
        int kind = atoi(argv[1] + 4); require(kind >= 0 && kind <= FS_ENTRY, "OOM getter kind");
        owner value = make_owner(kind, argv[2], argv[3]);
        oom_kind = kind; oom_owner = value; require(atexit(cleanup_oom_owner) == 0, "OOM fixture cleanup");
        fail_next_malloc = 1;
        (void)get_word(kind, value); puts("UNREACHABLE_AFTER_ALLOCATION_FAILURE"); return 3;
    }
    require(!strcmp(argv[1], "all"), "known mode");
    for (int kind = FS_ERROR; kind <= FS_ENTRY; kind++) lifecycle(kind, argv[2], argv[3], NULL);
    for (int kind = FS_ERROR; kind <= REQUEST_ERROR; kind++) {
        lifecycle(kind, argv[2], argv[3], "");
        lifecycle(kind, argv[2], argv[3], "error \xce\xbb \xe6\x97\xa5\xe6\x9c\xac");
    }
    for (int kind = FS_ERROR; kind <= SERVER_ERROR; kind++) successful_empty(kind, argv[2]);
    for (int kind = FS_ERROR; kind <= COMMAND_ERROR; kind++) growth(kind, argv[2]);
    freak_word literal = freak_word_lit("literal \xce\xbb");
    freak_word unchanged = freak_word_clone(literal);
    require(unchanged.data == literal.data && !unchanged.heap, "generic literal clone still borrows safely");
    drop(&unchanged); zero_owners(); puts("CASE generic-clone-contract");
    puts("TICKET_WORD_OWNERSHIP_OK cases=24"); return 0;
}
'''


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clang', default=os.environ.get('FREAK_CLANG', 'clang'))
    parser.add_argument('--runtime', type=Path)
    parser.add_argument('--optimization', type=int, choices=(0, 2, 3), action='append')
    parser.add_argument('--sanitize', action='store_true')
    parser.add_argument('--work-dir', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    clang = shutil.which(args.clang)
    assert clang, args.clang
    repo = Path(__file__).resolve().parents[1]
    runtime = (args.runtime or repo/'freakc/runtime').resolve(strict=True)
    executable_suffix = '.exe' if os.name == 'nt' else ''
    native_eol = b'\r\n' if os.name == 'nt' else b'\n'
    vendor = runtime.parents[1]/'third_party/llhttp'
    inputs = sorted(set([Path(__file__).resolve(), *(p for p in runtime.iterdir() if p.is_file()),
                         *(p for p in vendor.rglob('*') if p.is_file())]))
    before = {str(p): digest(p) for p in inputs}
    records = []
    report = {'status': 'running', 'host': sys.platform, 'inputs': before, 'commands': records,
              'sanitizers_enabled': args.sanitize, 'optimization_profile': args.optimization or [0, 2, 3],
              'scalar_ABIs': ['c', 'llvm'], 'cases_per_ABI': 24}
    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=1:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1')

    def run(command: list[str], label: str) -> subprocess.CompletedProcess[bytes]:
        started = time.monotonic()
        result = subprocess.run(command, capture_output=True, env=env, timeout=90)
        records.append({'label': label, 'argv': command, 'returncode': result.returncode,
                        'elapsed_seconds': time.monotonic()-started,
                        'stdout_hex': result.stdout.hex(), 'stderr_hex': result.stderr.hex()})
        print(label, result.returncode, flush=True)
        return result

    if args.work_dir:
        args.work_dir.mkdir(parents=True, exist_ok=True)
    workspace = nullcontext(str(args.work_dir.resolve())) if args.work_dir else tempfile.TemporaryDirectory(prefix='freak-ticket-word-')
    try:
        with workspace as directory:
            work = Path(directory)
            source = work/'owner-lifecycle.c'
            source.write_text(HARNESS)
            fixture = work/'inventory'
            fixture.mkdir(exist_ok=True)
            (fixture/'entry λ 日本').write_bytes(b'fixture')
            strict = ['-std=c11', '-Werror=implicit-function-declaration', '-Werror=incompatible-pointer-types',
                      '-Werror=int-conversion', '-Werror=return-type', f'-I{runtime}']
            sanitize = ['-fsanitize=address,undefined', '-fno-sanitize-recover=all', '-fno-omit-frame-pointer', '-g'] if args.sanitize else []
            libraries = ['-lws2_32', '-lshell32'] if os.name == 'nt' else ['-lm']
            if args.sanitize:
                control_source = work/'sanitizer-control.c'
                control_source.write_text('int main(void) { volatile int a=2147483647; return a+1; }\n')
                control = work/f'sanitizer-control{executable_suffix}'
                result = run([clang, '-O0', *sanitize, str(control_source), '-o', str(control)], 'sanitizer-control-build')
                assert result.returncode == 0, records[-1]
                result = run([str(control)], 'sanitizer-control-run')
                assert result.returncode != 0 and b'runtime error' in result.stderr, records[-1]
                address_source = work/'address-control.c'
                address_source.write_text('#include <stdlib.h>\nint main(void) { char *p=malloc(1); free(p); return *(volatile char *)p; }\n')
                address = work/f'address-control{executable_suffix}'
                result = run([clang, '-O0', *sanitize, str(address_source), '-o', str(address)], 'address-control-build')
                assert result.returncode == 0, records[-1]
                result = run([str(address)], 'address-control-run')
                assert result.returncode != 0 and b'AddressSanitizer' in result.stderr and b'heap-use-after-free' in result.stderr, records[-1]
            binaries = {}
            for optimization in args.optimization or (0, 2, 3):
                for abi in ('c', 'llvm'):
                    executable = work/f'owner-{abi}-O{optimization}{executable_suffix}'
                    command = [clang, *strict, f'-O{optimization}', *sanitize,
                               '-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1', '-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1',
                               str(source), str(runtime/'freak_llvm_runtime.c'), *libraries, '-o', str(executable)]
                    if abi == 'llvm': command.append('-DUSE_LLVM_ADAPTER=1')
                    result = run(command, f'build-{abi}-O{optimization}')
                    assert result.returncode == 0, records[-1]
                    binaries[executable.name] = digest(executable)
                    arguments = [str(fixture), str(work/'missing')]
                    result = run([str(executable), 'all', *arguments], f'run-{abi}-O{optimization}')
                    assert result.returncode == 0 and result.stderr == b'', records[-1]
                    assert result.stdout.count(b'CASE ') == 24 and result.stdout.endswith(b'TICKET_WORD_OWNERSHIP_OK cases=24' + native_eol), records[-1]
                    result = run([str(executable), 'leak', *arguments], f'leak-control-{abi}-O{optimization}')
                    assert result.returncode == (87 if abi == 'c' else 86), records[-1]
                    assert b'ownership audit found' in result.stderr and b'unreleased word allocation' in result.stderr, records[-1]
                    for kind in range(6):
                        result = run([str(executable), f'oom-{kind}', *arguments], f'oom-{kind}-{abi}-O{optimization}')
                        assert result.returncode == 1 and b'FREAK: out of memory' + native_eol in result.stderr, records[-1]
                        assert b'UNREACHABLE' not in result.stdout, records[-1]
            report.update(status='pass', binaries=binaries, fixture_sha256=digest(source))
    finally:
        report['inputs_unchanged'] = before == {str(p): digest(p) for p in inputs}
        if not report['inputs_unchanged'] or report['status'] != 'pass': report['status'] = 'fail'
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, indent=2)+'\n')
    assert report['status'] == 'pass', report['status']
    print(f"Ticket word ownership: 24 lifecycle cases per ABI passed on {sys.platform}; no foreign native execution claimed.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
