#!/usr/bin/env python3
"""Verify the native HTTP compiler ABI, owner disposal and hostile signatures.

HTTP framing and socket behavior have separate runtime and consumer execution
gates. This gate checks actual emitted calls for every frozen public operation.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import tempfile

from v3_checked_parsing import build_stage2, run
from v3_v35_language import require_ok

OPERATIONS = [
    "open",
    "bind",
    "status",
    "error",
    "local_port",
    "set_limits",
    "set_timeouts",
    "set_chunk_limits",
    "stop",
    "close",
    "next_request",
    "request_status",
    "request_error",
    "request_method",
    "request_target",
    "request_path",
    "request_query",
    "request_header_count",
    "request_header_name",
    "request_header_value",
    "request_header_value_bytes",
    "request_header_is_trailer",
    "request_header_find",
    "request_body",
    "response_status",
    "response_header",
    "send_bytes",
    "send_text",
    "request_release",
    "live_servers",
    "live_requests",
    "live_sockets",
    "retained_bytes"
]
PROGRAM = '''task main() {
    pilot server: int = 1
    pilot request: int = 2
    pilot bytes: ByteBuffer = ByteBuffer::new()
    pilot value_open: int = http_server::open(1)
    pilot value_bind: int = http_server::bind("127.0.0.1", 1, 1)
    pilot value_status: int = http_server::status(server)
    pilot value_error: word = http_server::error(server)
    pilot value_local_port: int = http_server::local_port(server)
    http_server::set_limits(server, 1, 1, 1, 1)
    http_server::set_timeouts(server, 1, 1, 1)
    http_server::set_chunk_limits(server, 1, 1)
    http_server::stop(server)
    pilot value_next_request: int = http_server::next_request(server)
    pilot value_request_status: int = http_server::request_status(request)
    pilot value_request_error: word = http_server::request_error(request)
    pilot value_request_method: word = http_server::request_method(request)
    pilot value_request_target: word = http_server::request_target(request)
    pilot value_request_path: word = http_server::request_path(request)
    pilot value_request_query: word = http_server::request_query(request)
    pilot value_request_header_count: int = http_server::request_header_count(request)
    pilot value_request_header_name: word = http_server::request_header_name(request, 1)
    pilot value_request_header_value: word = http_server::request_header_value(request, 1)
    pilot value_request_header_value_bytes: ByteBuffer = http_server::request_header_value_bytes(request, 1)
    pilot value_request_header_is_trailer: int = http_server::request_header_is_trailer(request, 1)
    pilot value_request_header_find: int = http_server::request_header_find(request, "X-Test", 1)
    pilot value_request_body: ByteBuffer = http_server::request_body(request)
    pilot value_response_status: int = http_server::response_status(request, 200)
    pilot value_response_header: int = http_server::response_header(request, "X-Test", "X-Test")
    pilot value_send_bytes: int = http_server::send_bytes(request, bytes)
    pilot value_send_text: int = http_server::send_text(request, "body")
    pilot value_live_servers: int = http_server::live_servers()
    pilot value_live_requests: int = http_server::live_requests()
    pilot value_live_sockets: int = http_server::live_sockets()
    pilot value_retained_bytes: int = http_server::retained_bytes()
    value_request_header_value_bytes.release()
    value_request_body.release()
    bytes.release()
    http_server::request_release(request)
    http_server::close(server)
}
'''
NEGATIVE = {
    'port_type': ('http_server::open("port")', 'argument 1 expects int, got word', False),
    'opt_in_type': ('http_server::bind("127.0.0.1", 1, true)', 'argument 3 expects int, got bool', False),
    'limits_arity': ('http_server::set_limits(1, 2, 3, 4)', 'expects 5 argument(s), got 4', False),
    'timeouts_type': ('http_server::set_timeouts(1, 2, "body", 4)', 'argument 3 expects int, got word', False),
    'header_index_type': ('http_server::request_header_name(1, "index")', 'argument 2 expects int, got word', False),
    'body_is_buffer': ('pilot body: int = http_server::request_body(1)', "cannot initialize int binding 'body' with ByteBuffer", False),
    'status_is_int': ('pilot status: bool = http_server::request_status(1)', "cannot initialize bool binding 'status' with int", False),
    'send_bytes_type': ('http_server::send_bytes(1, "bytes")', 'argument 2 expects ByteBuffer, got word', False),
    'header_value_type': ('http_server::response_header(1, "X-Test", 2)', 'argument 3 expects word, got int', False),
    'unknown_operation': ('http_server::request_magic(1)', "unknown callable 'http_server::request_magic'", False),
    'released_server': ('pilot server = http_server::open(0); http_server::close(server); http_server::status(server)', "You gave this away", True),
    'released_request': ('pilot request = http_server::next_request(1); http_server::request_release(request); http_server::request_status(request)', "You gave this away", True),
    'inferred_buffer_owner': ('pilot body = http_server::request_body(1); body.release(); body.length()', "You gave this away", True),
}
TOP_NEGATIVE = {
    'reserved_namespace': ('shape http_server { value: int } task main() {}', "shape name 'http_server' conflicts with a compiler builtin namespace"),
}


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler',type=Path)
    parser.add_argument('--clang',default=os.environ.get('FREAK_CLANG') or shutil.which('clang'))
    args=parser.parse_args()
    assert args.clang,'Clang required'
    repo=Path(__file__).resolve().parents[1]
    inventory=[]
    with tempfile.TemporaryDirectory(prefix='freak-v35-http-compiler-') as directory:
        root=Path(directory)
        compiler=args.compiler.resolve(strict=True) if args.compiler else build_stage2(clang=args.clang,repo=repo,root=root)
        for backend in ('c','llvm'):
            source=root/f'http_api_{backend}.fk'
            source.write_text(PROGRAM)
            require_ok(run([str(compiler),str(source),'--'+backend,'--strict-borrow'],root),'HTTP API '+backend)
            suffix='.c' if backend=='c' else '.ll'
            emitted=Path(str(source)+suffix).read_text()
            prefix='freak_http_server_' if backend=='c' else '@freak_llvm_http_server_'
            for operation in OPERATIONS:
                symbol=prefix+operation
                assert symbol+'(' in emitted,(backend,operation)
                if backend=='llvm':
                    assert any('call ' in line and symbol+'(' in line for line in emitted.splitlines()),(backend,operation)
            assert '__freak_user_http_server_' not in emitted,emitted
            inventory.append((backend,'positive'))
            print('PASS',backend,'HTTP 33-operation emission',flush=True)
            cases={name:('task main() { '+body+' }',diagnostic,strict) for name,(body,diagnostic,strict) in NEGATIVE.items()}
            cases.update({name:(program,diagnostic,False) for name,(program,diagnostic) in TOP_NEGATIVE.items()})
            for name,(program,diagnostic,strict) in cases.items():
                source=root/f'{backend}_{name}.fk'
                source.write_text(program)
                artifact=Path(str(source)+suffix)
                artifact.write_text('stale HTTP output')
                rejected=run([str(compiler),str(source),'--'+backend]+(['--strict-borrow'] if strict else []),root)
                assert rejected.returncode!=0 and diagnostic in rejected.stdout+rejected.stderr,(backend,name,diagnostic,rejected)
                assert not artifact.exists(),(backend,name,'stale artifact survived')
                inventory.append((backend,name))
                print('PASS',backend,name,flush=True)
    expected={(backend,name) for backend in ('c','llvm') for name in ('positive',*NEGATIVE,*TOP_NEGATIVE)}
    assert len(inventory)==len(expected) and set(inventory)==expected
    print(f'V3.5 HTTP compiler contracts: PASS ({len(inventory)} cases)',flush=True)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
