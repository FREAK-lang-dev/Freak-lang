#!/usr/bin/env python3
"""Deterministic rejection-close controls extracted from the production source.

Both POSIX and Winsock branches use scripted socket/clock dependencies. These
are compiled logic models, not TCP delivery, Windows ABI, or elapsed-time proof.
The existing real HTTP corpus and native platform CI remain required.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import uuid
from v3_v35_acceptance import run_command


FUNCTIONS = ('freak_http_close_socket', 'freak_http_reason',
             'freak_http_finish_rejection', 'freak_http_reject')
CASES = ('send-failure', 'nonblocking-failure', 'missing-server', 'stopped-server',
         'shutdown-failure', 'eof', 'fatal-read', 'wait-timeout', 'wait-error',
         'wait-stop', 'stop-during-wait', 'stop-after-read', 'delayed-readiness',
         'at-deadline', 'retry-eof', 'retries-to-deadline', 'endless-byte-cap',
         'uneven-byte-cap', 'endless-time-cap', 'idle-short', 'idle-equal',
         'idle-zero', 'invalid-socket', 'head-eof', 'status500-get', 'status500-head')


def extract_function(source: str, name: str) -> str:
    matches = list(re.finditer(r'(?m)^static[^\n]*\b' + re.escape(name) +
                               r'\([^\n]*\)\s*\{', source))
    if len(matches) != 1:
        raise ValueError('expected exactly one production definition: ' + name)
    start = matches[0].start();opening = matches[0].end() - 1;depth = 0
    # Strings, character literals and comments cannot contribute brace tokens.
    tokens = r'/\*[\s\S]*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[{}]'
    for match in re.finditer(tokens, source[opening:]):
        if match.group() == '{':depth += 1
        elif match.group() == '}':
            depth -= 1
            if depth == 0:return source[start:opening + match.end()]
    raise ValueError('unterminated production definition: ' + name)


PREAMBLE = r'''
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdatomic.h>
#ifndef _WIN32
#include <sys/types.h>
#else
typedef intptr_t ssize_t;
#undef _WIN32
#endif
#ifdef MODEL_WINSOCK
#define _WIN32 1
#endif
#define SHUT_WR 731
#define SD_SEND 947
#define FREAK_INVALID_NATIVE_SOCKET (-1)
#define CHECK(test) do { if(!(test)) { fprintf(stderr,"CONTROL_ASSERTION:%d:%s\n",__LINE__,#test); exit(97); } } while(0)
typedef int freak_native_socket;
typedef struct { uint64_t idle_ms; } freak_http_limits;
/* Deliberately reduced fixture records, with no native layout/ABI claim. */
typedef struct { atomic_bool stopping; } freak_http_server;
typedef struct {
    int64_t server; freak_native_socket socket; int status; bool head_method;
    freak_http_limits limits; uint64_t header_deadline,body_deadline,idle_deadline;
    size_t line_wire,header_wire,raw_wire,chunk_wire,trailer_wire; char error[192];
} freak_http_request;
static freak_http_server owned_server;
static const char *fixture;
static uint64_t tick=1000,fixed_deadline,idle;
static size_t freak_http_socket_live,total_received,wire_size;
static unsigned sends,finds,shutdowns,waits,reads,closes;
static int last_error;
static char wire[512];
static bool is(const char *name) { return strcmp(fixture,name)==0; }
static uint64_t freak_command_now_ms(void) { return tick; }
static freak_http_server *freak_http_find_server(int64_t ticket) {
    CHECK(ticket==41);finds++;return is("missing-server")?NULL:&owned_server;
}
static bool freak_http_send_all(freak_http_request *request,const void *bytes,size_t size,uint64_t deadline) {
    CHECK(request->socket==23 && size<sizeof(wire) && deadline==1000+idle);
    CHECK(sends++==0);memcpy(wire,bytes,size);wire_size=size;return !is("send-failure");
}
static void freak_tcp_socket_native_close(freak_native_socket socket) {
    CHECK(socket==23 && closes++==0 && freak_http_socket_live==1);
}
static int model_shutdown(freak_native_socket socket,int direction) {
    CHECK(socket==23 && shutdowns++==0);
#ifdef MODEL_WINSOCK
    CHECK(direction==SD_SEND);
#else
    CHECK(direction==SHUT_WR);
#endif
    return is("shutdown-failure")?-1:0;
}
static int freak_http_wait_socket(freak_http_server *server,freak_native_socket socket,
                                  bool write_ready,uint64_t deadline,uint64_t idle_deadline) {
    CHECK(server==&owned_server && socket==23 && !write_ready);
    CHECK(deadline==fixed_deadline && idle_deadline==fixed_deadline && ++waits<=64);
    if(is("wait-timeout"))return 0;
    if(is("wait-error"))return -1;
    if(is("wait-stop") || atomic_load(&server->stopping))return -2;
    if(is("stop-during-wait")) { atomic_store(&server->stopping,true);tick++; }
    else if(is("delayed-readiness"))tick=fixed_deadline+1;
    else if(is("at-deadline"))tick=fixed_deadline;
    else if(is("endless-time-cap") || is("idle-equal") || is("retries-to-deadline"))tick+=10;
    else if(is("idle-short") || is("retry-eof"))tick++;
    return 1;
}
#ifdef MODEL_WINSOCK
static int model_recv(freak_native_socket socket,char *bytes,int size,int flags) {
#else
static ssize_t model_recv(freak_native_socket socket,void *bytes,size_t size,int flags) {
#endif
    CHECK(socket==23 && flags==0 && bytes && size>0 && (size_t)size<=4096);
    CHECK(tick<fixed_deadline && !atomic_load(&owned_server.stopping));
    CHECK((size_t)size<=65536-total_received && ++reads<=64);last_error=0;
    if(is("fatal-read")) { last_error=3;return -1; }
    if(is("retry-eof")) {
        if(reads<=2) { last_error=reads==1?1:2;return -1; }
        return 0;
    }
    if(is("retries-to-deadline")) { last_error=reads%2?1:2;return -1; }
    if(is("endless-byte-cap") || is("uneven-byte-cap") || is("endless-time-cap") ||
       is("idle-short") || is("idle-equal") || is("stop-after-read")) {
        size_t count=is("uneven-byte-cap") && reads==1?1:(size_t)size;
        memset(bytes,0xa5,count);total_received+=count;
        if(is("stop-after-read"))atomic_store(&owned_server.stopping,true);
        return (int)count;
    }
    return 0;
}
static bool freak_tcp_socket_error_is_interrupted(void) { return last_error==1; }
static bool freak_tcp_socket_error_is_timeout(void) { return last_error==2; }
#define shutdown model_shutdown
#define recv model_recv
'''

TRAILER = r'''
int main(int argc,char **argv) {
    CHECK(argc==2);fixture=argv[1];idle=is("idle-short")?7:is("idle-equal")?50:is("idle-zero")?0:120;
    fixed_deadline=1000+(idle<50?idle:50);atomic_init(&owned_server.stopping,is("stopped-server"));
    freak_http_request request;memset(&request,0,sizeof(request));
    request.server=41;request.socket=is("invalid-socket")?-1:23;
    request.status=is("status500-get") || is("status500-head") || is("nonblocking-failure")?500:408;
    request.head_method=is("head-eof") || is("status500-head");request.limits.idle_ms=idle;
    request.header_deadline=111;request.body_deadline=222;request.idle_deadline=333;
    request.line_wire=1;request.header_wire=2;request.raw_wire=3;request.chunk_wire=4;request.trailer_wire=5;
    memcpy(request.error,"retained first rejection cause",30);
    freak_http_request expected=request;expected.socket=FREAK_INVALID_NATIVE_SOCKET;
    freak_http_socket_live=is("invalid-socket")?0:1;
    freak_http_reject(&request,!is("nonblocking-failure"));
    CHECK(memcmp(&request,&expected,sizeof(request))==0 && freak_http_socket_live==0);
    CHECK(closes==(is("invalid-socket")?0:1));
    freak_http_reject(&request,true);freak_http_close_socket(&request.socket);
    CHECK(closes==(is("invalid-socket")?0:1) && sends==(is("invalid-socket")?0:1));
    if(!is("invalid-socket")) {
        const char *body=request.head_method?"":request.status==500?"Internal Server Error\n":"Request Timeout\n";
        char expected_wire[512];int length=snprintf(expected_wire,sizeof(expected_wire),
            "HTTP/1.1 %d %s\r\nContent-Length: %d\r\nContent-Type: text/plain; charset=utf-8\r\nConnection: close\r\n\r\n%s",
            request.status,request.status==500?"Internal Server Error":"Request Timeout",request.status==500?22:16,body);
        CHECK(length>0 && wire_size==(size_t)length && memcmp(wire,expected_wire,wire_size)==0);
    }
    unsigned expected_finds=1,expected_shutdowns=1,expected_waits=1,expected_reads=1;
    if(is("invalid-socket") || is("send-failure") || is("nonblocking-failure"))
        expected_finds=expected_shutdowns=expected_waits=expected_reads=0;
    else if(is("missing-server") || is("stopped-server"))expected_shutdowns=expected_waits=expected_reads=0;
    else if(is("shutdown-failure"))expected_waits=expected_reads=0;
    else if(is("wait-timeout") || is("wait-error") || is("wait-stop") || is("stop-during-wait") ||
            is("delayed-readiness") || is("at-deadline") || is("idle-zero"))expected_reads=0;
    else if(is("stop-after-read"))expected_waits=2;
    else if(is("retry-eof"))expected_waits=expected_reads=3;
    else if(is("endless-byte-cap")) { expected_waits=expected_reads=16;CHECK(total_received==65536); }
    else if(is("uneven-byte-cap")) { expected_waits=expected_reads=17;CHECK(total_received==65536); }
    else if(is("endless-time-cap") || is("idle-equal") || is("retries-to-deadline")) {
        expected_waits=5;expected_reads=4;CHECK(tick==fixed_deadline);
    } else if(is("idle-short")) { expected_waits=7;expected_reads=6;CHECK(tick==fixed_deadline); }
    CHECK(finds==expected_finds && shutdowns==expected_shutdowns && waits==expected_waits && reads==expected_reads);
#ifdef MODEL_WINSOCK
    const char *model="winsock-branch-logic-model";
#else
    const char *model="posix-branch-logic-model";
#endif
    printf("{\"case\":\"%s\",\"model\":\"%s\",\"status\":%d,\"head\":%s,\"idle_ms\":%llu,\"fixed_deadline_ms\":%llu,\"final_tick_ms\":%llu,\"received_bytes\":%zu,\"waits\":%u,\"reads\":%u,\"native_closes\":%u,\"response_bytes\":%zu}\n",
        fixture,model,request.status,request.head_method?"true":"false",(unsigned long long)idle,
        (unsigned long long)fixed_deadline,(unsigned long long)tick,total_received,waits,reads,closes,wire_size);
    return 0;
}
'''


MUTATIONS = (
    ('nonblocking-bypass', 'nonblocking-failure', 'sent && nonblocking', 'sent'),
    ('post-readiness-deadline-bypass', 'delayed-readiness',
     'freak_command_now_ms()>=deadline', 'false'),
    ('prior-uneven-byte-overrun', 'uneven-byte-cap',
     'size_t wanted=65536-drained; if(wanted>sizeof(discarded)) wanted=sizeof(discarded);',
     'size_t wanted=sizeof(discarded);'),
    ('progress-resets-deadline', 'endless-time-cap', 'drained+=(size_t)received;',
     'drained+=(size_t)received; deadline=freak_command_now_ms()+grace;'),
    ('close-omitted', 'eof', 'freak_http_close_socket(&request->socket);', '(void)request;'),
)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clang', default=os.environ.get('FREAK_CLANG', 'clang'))
    parser.add_argument('--runtime-root', type=Path,
                        default=Path(__file__).resolve().parents[1] / 'freakc/runtime')
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--optimization', type=int, choices=(0, 2, 3), default=0)
    parser.add_argument('--prepare-only', action='store_true')
    args=parser.parse_args();runtime=args.runtime_root.resolve(strict=True)
    source_path=runtime / 'freak_v35_http.inc';source=source_path.read_text()
    extracted={name:extract_function(source,name) for name in FUNCTIONS}
    production='\n\n'.join(extracted.values());harness=PREAMBLE+production+TRAILER
    for _, _, before, _ in MUTATIONS:
        if production.count(before)!=1:raise ValueError('mutation no longer uniquely targets production guard: '+before)
    report_path=args.report.absolute();report_path.parent.mkdir(parents=True,exist_ok=True)
    if report_path.exists():raise FileExistsError('use a fresh rejection-close report path: '+str(report_path))
    root=report_path.parent / (report_path.stem+'-raw');root.mkdir(exist_ok=False)
    pins=[source_path,Path(__file__).resolve(),Path(__file__).with_name('v3_v35_acceptance.py').resolve()]
    report={'status':'running','scope':'deterministic compiled branch logic; no TCP/Windows ABI/timing claim',
            'pinned_inputs':{str(path):sha(path) for path in pins},'commands':[],'cases':[],
            'failing_controls':[],'extracted_function_sha256':{name:hashlib.sha256(value.encode()).hexdigest()
                                                            for name,value in extracted.items()}}
    def save():
        temporary=report_path.with_name('.'+report_path.name+'-'+uuid.uuid4().hex)
        try:
            temporary.write_text(json.dumps(report,indent=2)+'\n');os.replace(temporary,report_path)
        finally:temporary.unlink(missing_ok=True)
    def run(command, label, expected=0):
        report['active']=label
        return run_command(list(map(str,command)),cwd=root,env=os.environ.copy(),label=label,
                           prefix=root/str(len(report['commands'])+1),records=report['commands'],
                           expected=expected,timeout=30 if label.startswith('compile') else 5,
                           on_record=lambda record:save())
    primary=None
    try:
        base_file=root/'production-rejection-controls.c';base_file.write_text(harness)
        report['generated_harness']={'path':str(base_file),'sha256':sha(base_file)}
        if args.prepare_only:
            report.update(status='prepared-only',prepared_cases=len(CASES)*2,prepared_failing_controls=len(MUTATIONS)*2)
        else:
            compiler=shutil.which(args.clang)
            if not compiler:raise FileNotFoundError('Clang not found: '+args.clang)
            compiler_path=Path(compiler).resolve(strict=True);pins.append(compiler_path)
            report['pinned_inputs'][str(compiler_path)]=sha(compiler_path)
            report['clang_version']=run([compiler,'--version'],'clang-version').stdout.decode().splitlines()[0]
            for branch in ('posix','winsock'):
                flags=['-std=c11','-Wall','-Wextra',f'-O{args.optimization}']
                if branch=='winsock':flags+=['-DMODEL_WINSOCK=1']
                binary=root/('rejection-'+branch+('.exe' if os.name=='nt' else ''))
                run([compiler,*flags,base_file,'-o',binary],'compile-'+branch)
                for case in CASES:
                    result=run([binary,case],branch+'-'+case)
                    if result.stderr:raise AssertionError('unexpected model stderr: '+repr(result.stderr))
                    record=json.loads(result.stdout)
                    if record['case']!=case or record['model']!=branch+'-branch-logic-model':
                        raise AssertionError('wrong control output identity')
                    report['cases'].append(record)
                for name, case, before, after in MUTATIONS:
                    mutant=root/(branch+'-'+name+'.c');mutant.write_text(PREAMBLE+production.replace(before,after)+TRAILER)
                    bad=root/(branch+'-'+name+('.exe' if os.name=='nt' else ''))
                    run([compiler,*flags,mutant,'-o',bad],'compile-failing-'+branch+'-'+name)
                    result=run([bad,case],'failing-'+branch+'-'+name,97)
                    if result.stdout or b'CONTROL_ASSERTION:' not in result.stderr:
                        raise AssertionError('failing control did not reach a guard assertion')
                    report['failing_controls'].append({'name':name,'branch':branch,'case':case,
                                                       'mutated_copy':str(mutant),'sha256':sha(mutant),'exit_code':97})
            report.update(status='passed',successful_cases=len(report['cases']),
                          successful_failing_controls=len(report['failing_controls']))
        if report['pinned_inputs']!={str(path):sha(path) for path in pins}:
            raise AssertionError('rejection control input changed during verification')
        report['pinned_inputs_unchanged']=True;report.pop('active',None)
    except BaseException as error:
        primary=error;report.update(status='failed',exception_type=type(error).__name__)
        raise
    finally:
        try:save()
        except BaseException as error:
            if primary is None:raise
            try:primary.add_note('rejection-close recording failed: '+repr(error))
            except BaseException:pass
    print(json.dumps({'status':report['status'],'report':str(report_path),
                      'cases':len(report['cases']),'failing_controls':len(report['failing_controls'])}))


if __name__=='__main__':main()
