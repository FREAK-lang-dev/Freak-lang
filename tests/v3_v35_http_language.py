#!/usr/bin/env python3
"""Ordinary FREAK HTTP consumer and semantic/ownership vertical gate.

Requires an explicitly supplied fresh native compiler with HTTP/JSON bindings.
The fixture owns its routes, named parameter, JSON validation and 404/405 policy.
The independent client/raw-socket driver uses the same floor corpus helpers.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from v3_v35_http import HttpProgress, Server, assert_response, invalid_corpus, request, reset_content_corpus, runtime_inputs

PROGRAM = r'''
task app_dispatch(request: int) -> bool {
    pilot path = http_request_path(request)
    pilot method = http_request_method(request)
    if path == "/stop" {
        pilot sent = http_send_text(request, "stopped")
        give back true
    }
    if path == "/health" {
        if method != "GET" and method != "HEAD" {
            pilot status = http_response_status(request, 405)
            pilot header = http_response_header(request, "Allow", "GET, HEAD")
            pilot sent = http_send_text(request, "")
        } else {
            pilot sent = http_send_text(request, "healthy")
        }
        give back false
    }
    if path.starts_with("/hello/") {
        pilot name = path.substring(7, path.length() - 7)
        pilot sent = http_send_text(request, name)
        give back false
    }
    if path == "/echo" {
        pilot body = http_request_body(request)
        pilot sent = http_send_bytes(request, body)
        give back false
    }
    if path == "/header-bytes" {
        pilot index = http_header_find(request, "X-Binary", 0)
        pilot body = http_header_value_bytes(request, index)
        pilot sent = http_send_bytes(request, body)
        give back false
    }
    if path == "/json" {
        pilot body = http_request_body(request)
        pilot document = json_document::parse_bytes(body)
        body.release()
        if json_document_ok(document) == 0 {
            pilot status = http_response_status(request, 400)
            pilot sent = http_send_text(request, "invalid JSON")
        } else {
            pilot root = json_document_root(document)
            pilot mut name = 0
            if json_document_kind(document, root) == 6 {
                name = json_document_object_get(document, root, "name")
            }
            if json_document_kind(document, root) != 6 or json_document_kind(document, name) != 4 {
                pilot status = http_response_status(request, 422)
                pilot sent = http_send_text(request, "name must be a string")
            } else {
                pilot sent = http_send_json(request, document)
            }
        }
        json_document_release(document)
        give back false
    }
    if path == "/inspect" {
        pilot mut output = "query=" + http_request_query(request) + "\n"
        pilot mut index = http_header_find(request, "X-Repeat", 0)
        repeat until index < 0 {
            output = output + word_from_int(http_header_is_trailer(request, index)) + ":" + http_header_value(request, index) + "\n"
            index = http_header_find(request, "x-repeat", index + 1)
        }
        pilot sent = http_send_text(request, output)
        give back false
    }
    if path == "/empty" {
        pilot sent = http_send_text(request, "")
        give back false
    }
    if path == "/204" {
        pilot status = http_response_status(request, 204)
        pilot sent = http_send_text(request, "ignored")
        give back false
    }
    if path == "/205" {
        pilot status = http_response_status(request, 205)
        if http_request_query(request) == "bytes" {
            pilot body = http_request_body(request)
            pilot sent = http_send_bytes(request, body)
        } else {
            pilot sent = http_send_text(request, "ignored")
        }
        give back false
    }
    if path == "/304" {
        pilot status = http_response_status(request, 304)
        pilot sent = http_send_text(request, "ignored")
        give back false
    }
    pilot status = http_response_status(request, 404)
    pilot sent = http_send_text(request, "missing")
    give back false
}
task main() {
    pilot server = http_open(0)
    if http_server_status(server) != 0 {
        say http_server_error(server)
        http_close(server)
        process::exit(2)
    }
    http_set_timeouts(server, 1200, 5000, 1000)
    say "PORT " + word_from_int(http_local_port(server))
    pilot mut finished = false
    repeat until finished {
        pilot request = http_next_request(server)
        if http_request_status(request) == 0 {
            finished = app_dispatch(request)
        }
        http_request_release(request)
    }
    http_stop(server)
    http_close(server)
    say "REPORT " + word_from_int(http_server::live_servers()) + " " + word_from_int(http_server::live_requests()) + " " + word_from_int(http_server::live_sockets()) + " " + word_from_int(http_server::retained_bytes()) + " 0"
}
'''

NEGATIVE = {
    'body_type':('task main() { pilot b = http_server::send_bytes(1, 2) }','ByteBuffer'),
    'return_type':('task main() { pilot b: int = http_server::request_body(1) }','ByteBuffer'),
    'word_type':('task main() { pilot s = http_server::bind(1, 0, 0) }','word'),
    'arity':('task main() { pilot s = http_server::open(0, 0) }','argument'),
}
CONTROLLED = {
    'stale_server':'task main() { pilot s = http_open(0); http_close(s); say http_server_status(s) }',
    'wrong_domain':'task main() { pilot s = http_open(0); say http_request_status(s) }',
    'invalid_limits':'task main() { pilot s = http_open(0); http_set_limits(s, 1, 1, 1, 1) }',
}

def run(command, *, cwd, env=None):
    return subprocess.run(command,cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8',timeout=90)

def consumer_corpus(server:Server,soak:int):
    server.checkpoint('language-consumer','routing-and-framing')
    assert_response(server.exchange(request('/health')),200,b'healthy')
    assert_response(server.exchange(request('/hello/Ada')),200,b'Ada')
    h=assert_response(server.exchange(request('/health','HEAD')),200,b'',head=True);assert h[b'content-length']==b'7'
    h=assert_response(server.exchange(request('/unknown','HEAD')),404,b'',head=True);assert h[b'content-length']==b'7'
    h=assert_response(server.exchange(request('/health','POST')),405,b'');assert h[b'allow']==b'GET, HEAD'
    for path,status in [('/empty',200),('/204',204)]:assert_response(server.exchange(request(path)),status,b'')
    assert_response(server.exchange(request('/204','HEAD')),204,b'',head=True)
    reset_content_corpus(server)
    server.checkpoint('language-consumer','bodyless-and-header-responses')
    for method in ('GET','HEAD'):
        h=assert_response(server.exchange(request('/304',method)),304,b'',head=method=='HEAD');assert h[b'content-length']==b'7'
    binary=b'A\0\xff\xc3\xa9\xf0\x9f\x9a\x80B'
    fixed=request('/echo','POST',binary)
    chunked=request('/echo','POST',b'b;ext="a\\\"b"\r\n'+binary+b'\r\n0\r\nX: trailer\r\n\r\n',headers=[('Transfer-Encoding','chunked')])
    # Body length below is checked independently rather than hard-coding framing.
    chunked=chunked.replace(b'\r\nb;ext=',f'\r\n{len(binary):x};ext='.encode())
    for wire in (fixed,chunked):
        server.checkpoint('language-consumer','binary-body-splits')
        for split in range(1,len(wire)):assert_response(server.exchange(wire,split=split),200,binary)
    assert_response(server.exchange(request('/header-bytes').replace(b'\r\n\r\n',b'\r\nX-Binary: \xff\x80\r\n\r\n')),200,b'\xff\x80')
    wire=request('/inspect?x=1&x=2%20z','POST',b'1\r\na\r\n0\r\nX-Repeat: third\r\n\r\n',headers=[('Transfer-Encoding','chunked'),('X-Repeat','first'),('X-Repeat','second')])
    assert_response(server.exchange(wire),200,b'query=x=1&x=2%20z\n0:first\n0:second\n1:third\n')
    doc={'name':'é猫🚀','escape':'"\\\n\t','nul':'a\0b','n':9007199254740993}
    source=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();wire=request('/json','POST',source)
    for split in range(1,len(wire)):
        if split%128==1:server.checkpoint('language-consumer','json-body-splits',case=split)
        result=server.exchange(wire,split=split);h=assert_response(result,200);assert h[b'content-type']==b'application/json' and json.loads(result[2])==doc
    for source,status in [(b'{',400),(b'null',422),(b'[]',422),(b'{"name":null}',422),(b'{"name":"x","name":"y"}',400),(b'{"name":"\\uD800"}',400)]:assert_response(server.exchange(request('/json','POST',source)),status)
    invalid_corpus(server)
    for i in range(soak):
        if i%128==0:server.checkpoint('language-consumer','ownership-soak',case=i)
        if i%3==0:assert_response(server.exchange(request('/echo','POST',binary)),200,binary)
        elif i%3==1:assert_response(server.exchange(request('/json','POST',b'{"name":"soak"}')),200)
        else:assert_response(server.exchange(request('/health')),200,b'healthy')

def main():
    p=argparse.ArgumentParser();p.add_argument('--compiler',type=Path,required=True);p.add_argument('--clang',default=os.environ.get('FREAK_CLANG','clang'));p.add_argument('--runtime-root',type=Path);p.add_argument('--std-root',type=Path);p.add_argument('--optimization',type=int,choices=(0,2,3),action='append');p.add_argument('--backend',choices=('c','llvm'),action='append');p.add_argument('--sanitize',action='store_true');p.add_argument('--soak',type=int,default=1000);p.add_argument('--report',type=Path);args=p.parse_args()
    evidence={'matrices':[]}
    with HttpProgress(args.report,evidence,len(args.optimization or (0,2,3))*len(args.backend or ('c','llvm'))) as progress:
        progress.stage('input-provenance')
        repo=Path(__file__).resolve().parents[1];runtime,vendor=runtime_inputs(args.runtime_root);compiler=args.compiler.resolve(strict=True)
        std=(args.std_root or repo/'std').resolve(strict=True)
        facade=(std/'json_document.fk').read_text()+'\n'+(std/'http_server.fk').read_text()
        pinned_paths=[compiler,std/'json_document.fk',std/'http_server.fk',*sorted(runtime.glob('*.c')),*sorted(runtime.glob('*.h')),*sorted(runtime.glob('*.inc'))]
        pinned_paths+=sorted(p for p in vendor.rglob('*') if p.is_file())
        before={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in pinned_paths}
        clang=shutil.which(args.clang);assert clang,args.clang
        env=os.environ.copy();env['ASAN_OPTIONS']='detect_leaks=1:halt_on_error=1';env['UBSAN_OPTIONS']='halt_on_error=1'
        evidence.update({'compiler_sha256':before[str(compiler)],'clang_path':str(Path(clang).resolve()),'clang_sha256':hashlib.sha256(Path(clang).read_bytes()).hexdigest(),'facade_sha256':hashlib.sha256(facade.encode()).hexdigest(),'pinned_input_sha256':before,'strict_borrow':True,'sanitize':args.sanitize,'matrices':[]})
        progress.stage('input-provenance-complete')
        with tempfile.TemporaryDirectory(prefix='freak-http-language-') as temporary:
            root=Path(temporary);suffix='.exe' if os.name=='nt' else ''
            if args.sanitize:
                progress.stage('sanitizer-control','compile')
                control=root/'control.c';control.write_text('#include <stdlib.h>\nint main(int n,char **v){volatile char *p=malloc(1);p[n+4]=3;free((void*)p);return 0;}\n');binary=root/'control'
                linked=run([clang,control,'-O0','-fsanitize=address,undefined','-o',binary],cwd=root);assert linked.returncode==0,(linked.stdout,linked.stderr)
                progress.stage('sanitizer-control','execute')
                failed=run([binary],cwd=root,env=env);assert failed.returncode!=0 and 'AddressSanitizer' in failed.stderr,failed.stderr;evidence['sanitizer_failing_control']=True
            for opt in args.optimization or (0,2,3):
                for backend in args.backend or ('c','llvm'):
                    progress.matrix_started('backend',backend,opt)
                    for name,program in [('consumer',PROGRAM),*CONTROLLED.items()]:
                        progress.stage('language-compile',name)
                        source=root/f'{name}-{backend}.fk';source.write_text(facade+'\n'+program)
                        compiled=run([str(compiler),str(source),f'--{backend}','--strict-borrow'],cwd=root);assert compiled.returncode==0,(name,compiled.stdout,compiled.stderr)
                        generated=Path(str(source)+('.c' if backend=='c' else '.ll'));binary=root/f'{name}-{backend}-O{opt}{suffix}'
                        cmd=[clang,f'-O{opt}',str(generated),str(runtime/'freak_runtime.c'),f'-I{runtime}','-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1','-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1','-o',str(binary)]
                        if args.sanitize:cmd+=['-fsanitize=address,undefined,function','-fno-omit-frame-pointer','-g']
                        if backend=='llvm':cmd.append(str(runtime/'freak_llvm_runtime.c'))
                        cmd+=['-lws2_32','-lshell32'] if os.name=='nt' else ['-lm']
                        progress.stage('native-link',name)
                        linked=run(cmd,cwd=root);assert linked.returncode==0,(name,linked.stdout,linked.stderr)
                        if name=='consumer':
                            server=Server(binary,'normal',env,progress)
                            try:
                                consumer_corpus(server,args.soak)
                                server.checkpoint('server-stop','consumer')
                                counts=server.stop();assert counts[:3]==[0,0,0],counts
                                cases=server.cases
                            finally:server.abort()
                        else:
                            progress.stage('controlled-error',name)
                            executed=run([str(binary)],cwd=root,env=env);assert executed.returncode!=0 and not executed.stdout and 'HTTP floor:' in executed.stderr,(name,backend,executed.returncode,executed.stdout,executed.stderr)
                    for name,(program,diagnostic) in NEGATIVE.items():
                        progress.stage('semantic-rejection',name)
                        source=root/f'{name}-{backend}.fk';source.write_text(program)
                        generated=Path(str(source)+('.c' if backend=='c' else '.ll'));generated.write_text('stale output')
                        failed=run([str(compiler),str(source),f'--{backend}','--strict-borrow'],cwd=root)
                        assert failed.returncode!=0 and diagnostic.lower() in (failed.stdout+failed.stderr).lower(),(name,failed.returncode,failed.stdout,failed.stderr)
                        assert not generated.exists(),(name,'stale generated artifact survived')
                    evidence['matrices'].append({'backend':backend,'optimization':opt,'ordinary_consumer_cases':cases,'controlled_errors':len(CONTROLLED),'semantic_rejections':len(NEGATIVE)})
                    progress.matrix_finished()
                    print(f'PASS HTTP facade {backend} O{opt}: {cases} ordinary-consumer requests,3 controlled errors,4 semantic rejections',flush=True)
        progress.stage('final-input-verification')
        after={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in pinned_paths};assert after==before,'pinned compiler/runtime/std/vendor inputs changed during gate';evidence['pinned_inputs_unchanged']=True
        progress.passed()
if __name__=='__main__':main()
