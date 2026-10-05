#!/usr/bin/env python3
"""Independent raw-socket HTTP corpus against production C and scalar LLVM APIs.

Builds only small runtime harnesses. No compiler bootstrap, network dependency,
Node generator, third-party Python module, or server outside numeric loopback.
The fixture application owns its routing; the runtime only parses and sends.
"""
from __future__ import annotations
import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path
import select
import shutil
import socket
import struct
import subprocess
import tempfile
import time

HARNESS = r'''
#include "freak_runtime.c"
#ifndef FREAK_V35_JSON_INCLUDED
#include "freak_v35_json.inc"
#endif
#include "freak_v35_http.inc"
#include <assert.h>
#ifndef _WIN32
#include <dirent.h>
#include <pthread.h>
#endif
#ifdef USE_LLVM_ADAPTER
#define H(name) freak_llvm_http_server_##name
#define J(name) freak_llvm_json_document_##name
#define W(s) ((int64_t)(intptr_t)(s))
static freak_word view(int64_t w) { return freak_llvm_word_view(w); }
static void drop(int64_t w) { freak_llvm_word_release_replaced(w,0); }
#else
#define H(name) freak_http_server_##name
#define J(name) freak_json_document_##name
#define W(s) freak_word_lit(s)
static freak_word view(freak_word w) { return w; }
static void drop(freak_word w) { freak_word_release_owned(&w); }
#endif
#define REQUIRE(c) do { if(!(c)) { fprintf(stderr,"FAIL at %d\n",__LINE__); exit(2); } } while(0)
static int64_t bytes(const void *data,size_t length) { int64_t b=freak_byte_buffer_with_capacity(length); freak_byte_buffer_record *r=freak_byte_buffer_require(b,"fixture"); if(length) memcpy(r->data,data,length);r->length=length;return b; }
static int fds(void) {
#ifdef __linux__
    DIR *d=opendir("/proc/self/fd"); REQUIRE(d);int n=0;struct dirent *e;while((e=readdir(d)))if(strcmp(e->d_name,".")&&strcmp(e->d_name,".."))n++;closedir(d);return n;
#else
    return -1;
#endif
}
static void base(void) {
    REQUIRE(H(live_servers)()==0&&H(live_requests)()==0&&H(live_sockets)()==0);
    REQUIRE(!freak_byte_buffer_live_count&&!freak_c_owned_word_count&&!freak_llvm_owned_count&&!freak_json_live_documents&&!freak_json_live_nodes);
}
static void bind_tests(void) {
    int64_t s=H(open)(0); REQUIRE(H(status)(s)==0&&H(local_port)(s)>0);
    int64_t occupied=H(open)(H(local_port)(s)); REQUIRE(H(status)(occupied)==2);__auto_type error=H(error)(occupied);REQUIRE(view(error).length);drop(error);H(close)(occupied);
    int port=H(local_port)(s);H(close)(s);s=H(open)(port);REQUIRE(H(status)(s)==0);H(close)(s);
    s=H(bind)(W("0.0.0.0"),0,0);REQUIRE(H(status)(s)==2);H(close)(s);
    s=H(bind)(W("0.0.0.0"),0,1);REQUIRE(H(status)(s)==0);H(close)(s);
    s=H(bind)(W("localhost"),0,0);REQUIRE(H(status)(s)==2);H(close)(s);
    s=H(open)(-1);REQUIRE(H(status)(s)==2);H(close)(s);
    s=H(bind)(W("::1"),0,0);if(H(status)(s)==0) REQUIRE(H(local_port)(s)>0);H(close)(s);
    base();
}
typedef struct { int64_t server,request; bool writing; atomic_bool ready; int sent; } stop_context;
static void stop_work(stop_context *c) {
    c->request=H(next_request)(c->server);
    if(c->writing) {
        REQUIRE(!H(request_status)(c->request));int amount=1024;freak_http_request *r=freak_http_require_request(c->request);setsockopt(r->socket,SOL_SOCKET,SO_SNDBUF,(const char *)&amount,sizeof(amount));
        int64_t b=freak_byte_buffer_with_capacity(8388608);freak_byte_buffer_record *buffer=freak_byte_buffer_require(b,"stop-write");memset(buffer->data,'x',8388608);buffer->length=8388608;
        atomic_store_explicit(&c->ready,true,memory_order_release);c->sent=H(send_bytes)(c->request,b);freak_byte_buffer_release(b);
    }
}
#ifdef _WIN32
static DWORD WINAPI accept_thread(LPVOID p) { stop_work(p);return 0; }
#else
static void *accept_thread(void *p) { stop_work(p);return NULL; }
#endif
static void stop_tests(void) {
    for(int reading=0;reading<3;reading++) {
        stop_context c={0};c.server=H(open)(0);c.writing=reading==2;atomic_init(&c.ready,false);REQUIRE(H(status)(c.server)==0);
        if(c.writing)H(set_limits)(c.server,8192,32768,100,8388608);
        freak_native_socket client=FREAK_INVALID_NATIVE_SOCKET;
        if(reading) { client=socket(AF_INET,SOCK_STREAM,IPPROTO_TCP);REQUIRE(client!=FREAK_INVALID_NATIVE_SOCKET);int receive=1024;setsockopt(client,SOL_SOCKET,SO_RCVBUF,(const char *)&receive,sizeof(receive));struct sockaddr_in a={0};a.sin_family=AF_INET;a.sin_port=htons(H(local_port)(c.server));a.sin_addr.s_addr=htonl(INADDR_LOOPBACK);REQUIRE(connect(client,(struct sockaddr *)&a,sizeof(a))==0);const char *wire=c.writing?"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n":"GET /";REQUIRE(send(client,wire,(int)strlen(wire),0)==(int)strlen(wire)); }
#ifdef _WIN32
        HANDLE thread=CreateThread(NULL,0,accept_thread,&c,0,NULL);REQUIRE(thread);Sleep(30);
#else
        pthread_t thread;REQUIRE(pthread_create(&thread,NULL,accept_thread,&c)==0);freak_time_sleep(30);
#endif
        if(c.writing) {uint64_t limit=freak_command_now_ms()+2000;while(!atomic_load_explicit(&c.ready,memory_order_acquire)){REQUIRE(freak_command_now_ms()<limit);freak_time_sleep(1);}freak_time_sleep(30);}
        uint64_t start=freak_command_now_ms();H(stop)(c.server);
#ifdef _WIN32
        REQUIRE(WaitForSingleObject(thread,1000)==WAIT_OBJECT_0);CloseHandle(thread);
#else
        REQUIRE(pthread_join(thread,NULL)==0);
#endif
        REQUIRE(freak_command_now_ms()-start<500&&H(request_status)(c.request)==(c.writing?0:503)&&H(status)(c.server)==1);if(c.writing)REQUIRE(!c.sent);
        if(client!=FREAK_INVALID_NATIVE_SOCKET) freak_tcp_socket_native_close(client);
        H(request_release)(c.request);H(close)(c.server);base();
    }
}
static size_t partial_sends,send_failures;
#if defined(__linux__)
ssize_t __real_send(int,const void *,size_t,int);
ssize_t __wrap_send(int fd,const void *p,size_t n,int flags) { ssize_t r=__real_send(fd,p,n,flags);if(r>0&&(size_t)r<n)partial_sends++;return r; }
#endif
static bool eq(freak_word word,const char *s) { return word.length==strlen(s)&&!memcmp(word.data,s,word.length); }
static void service(const char *profile) {
    int initial_fds=fds();int64_t server=H(open)(0);REQUIRE(H(status)(server)==0);
    bool tight=!strcmp(profile,"tight");
    if(tight) { H(set_limits)(server,128,512,8,64);H(set_chunk_limits)(server,64,64);H(set_timeouts)(server,220,260,120); }
    else H(set_timeouts)(server,1200,5000,1000);
    printf("PORT %lld\n",(long long)H(local_port)(server));fflush(stdout);
    size_t requests=0,baseline_retained=0;bool quit=false;int listener_fds=fds();
    while(!quit) {
        int64_t request=H(next_request)(server);
        if(!H(request_status)(request)) {
            __auto_type method=H(request_method)(request),path=H(request_path)(request),target=H(request_target)(request),query=H(request_query)(request);
            freak_word p=view(path),m=view(method);bool sent=true;
            if(eq(p,"/stop")) { quit=true;sent=H(send_text)(request,W("stopped")); }
            else if(eq(p,"/health")) {
                if(!eq(m,"GET")&&!eq(m,"HEAD")) { REQUIRE(H(response_status)(request,405));REQUIRE(H(response_header)(request,W("Allow"),W("GET, HEAD")));sent=H(send_text)(request,W("")); }
                else sent=H(send_text)(request,W("healthy"));
            } else if(p.length>7&&!memcmp(p.data,"/hello/",7)) {
                int64_t b=bytes(p.data+7,p.length-7);sent=H(send_bytes)(request,b);freak_byte_buffer_release(b);
            } else if(eq(p,"/echo")) {
                int64_t b=H(request_body)(request);sent=H(send_bytes)(request,b);freak_byte_buffer_release(b);
            } else if(eq(p,"/header-bytes")) {
                int64_t index=H(request_header_find)(request,W("X-Binary"),0);REQUIRE(index>=0);int64_t b=H(request_header_value_bytes)(request,index);sent=H(send_bytes)(request,b);freak_byte_buffer_release(b);
            } else if(eq(p,"/json")) {
                int64_t b=H(request_body)(request),d=J(parse_bytes)(b);freak_byte_buffer_release(b);
                if(!J(ok)(d)) { REQUIRE(H(response_status)(request,400));sent=H(send_text)(request,W("invalid JSON")); }
                else { int64_t root=J(root)(d),name=J(kind)(d,root)==6?J(object_get)(d,root,W("name")):0;
                    if(J(kind)(d,root)!=6||J(kind)(d,name)!=4) { REQUIRE(H(response_status)(request,422));sent=H(send_text)(request,W("name must be a string")); }
                    else { b=J(serialize_bytes)(d);REQUIRE(H(response_header)(request,W("Content-Type"),W("application/json")));sent=H(send_bytes)(request,b);freak_byte_buffer_release(b); }
                } J(release)(d);
            } else if(eq(p,"/inspect")) {
                char output[1024];size_t n=0;freak_word q=view(query);n+=(size_t)snprintf(output+n,sizeof(output)-n,"query=%.*s\n",(int)q.length,q.data);
                for(int64_t i=H(request_header_find)(request,W("X-Repeat"),0);i>=0;i=H(request_header_find)(request,W("x-repeat"),i+1)) {
                    __auto_type name=H(request_header_name)(request,i),value=H(request_header_value)(request,i);freak_word v=view(value);REQUIRE(eq(view(name),"x-repeat"));
                    n+=(size_t)snprintf(output+n,sizeof(output)-n,"%lld:%.*s\n",(long long)H(request_header_is_trailer)(request,i),(int)v.length,v.data);drop(name);drop(value);
                    int64_t raw=H(request_header_value_bytes)(request,i);REQUIRE(freak_byte_buffer_length(raw)==(int64_t)v.length);freak_byte_buffer_release(raw);
                } int64_t b=bytes(output,n);sent=H(send_bytes)(request,b);freak_byte_buffer_release(b);
            } else if(eq(p,"/unsafe")) {
                REQUIRE(!H(response_header)(request,W("bad\r\nname"),W("x")));REQUIRE(!H(response_header)(request,W("X"),W("a\r\nInjected: yes")));
                const char *framing[]={"Content-Length","Transfer-Encoding","Connection","Trailer","Upgrade","Keep-Alive","Proxy-Connection"};
                for(size_t i=0;i<sizeof(framing)/sizeof(*framing);i++) REQUIRE(!H(response_header)(request,W(framing[i]),W("x")));
                REQUIRE(!H(response_status)(request,100));REQUIRE(H(response_header)(request,W("X-Safe"),W("yes")));sent=H(send_text)(request,W("safe"));
            } else if(eq(p,"/large")) {
                freak_http_request *native=freak_http_require_request(request);int amount=1024;setsockopt(native->socket,SOL_SOCKET,SO_SNDBUF,(const char *)&amount,sizeof(amount));
                int64_t b=freak_byte_buffer_with_capacity(262144);freak_byte_buffer_record *r=freak_byte_buffer_require(b,"large fixture");for(size_t i=0;i<262144;i++)r->data[i]=(unsigned char)((i*17+3)&255);r->length=262144;sent=H(send_bytes)(request,b);freak_byte_buffer_release(b);
            } else if(eq(p,"/empty")) sent=H(send_text)(request,W(""));
            else if(eq(p,"/204")) { REQUIRE(H(response_status)(request,204));sent=H(send_text)(request,W("ignored")); }
            else if(eq(p,"/304")) { REQUIRE(H(response_status)(request,304));sent=H(send_text)(request,W("ignored")); }
            else { REQUIRE(H(response_status)(request,404));sent=H(send_text)(request,W("missing")); }
            if(!sent) send_failures++;
            /* Every getter is an independent owner and may outlive its request. */
            int64_t lease=H(request_body)(request);size_t length=freak_byte_buffer_require(lease,"lease")->length;
            H(request_release)(request);REQUIRE(freak_byte_buffer_length(lease)==(int64_t)length);freak_byte_buffer_release(lease);
            REQUIRE(view(path).length==p.length&&view(method).length==m.length);drop(method);drop(path);drop(target);drop(query);
        } else H(request_release)(request);
        requests++;
        REQUIRE(H(live_requests)()==0&&H(live_servers)()==1&&H(live_sockets)()==1);
        REQUIRE(!freak_byte_buffer_live_count&&!freak_c_owned_word_count&&!freak_llvm_owned_count&&!freak_json_live_documents&&!freak_json_live_nodes);
        REQUIRE(fds()==listener_fds);
        if(requests==20) baseline_retained=H(retained_bytes)();
        if(requests>20) REQUIRE((size_t)H(retained_bytes)()==baseline_retained);
    }
    H(stop)(server);H(close)(server);base();REQUIRE(fds()==initial_fds);
    printf("REPORT %zu %zu %zu %lld %d\n",requests,partial_sends,send_failures,(long long)H(retained_bytes)(),fds());fflush(stdout);
}
int main(int argc,char **argv) {
    REQUIRE(argc==2);
    if(!strcmp(argv[1],"bind")) {bind_tests();stop_tests();return 0;}
    if(!strcmp(argv[1],"normal")||!strcmp(argv[1],"tight")) {service(argv[1]);return 0;}
    int64_t s=H(open)(0);
    if(!strcmp(argv[1],"stale")) {H(close)(s);s=H(open)(0);H(status)(s-(INT64_C(1)<<32));return 8;}
    if(!strcmp(argv[1],"double")) {H(close)(s);H(close)(s);return 8;}
    if(!strcmp(argv[1],"foreign")) {H(status)(freak_byte_buffer_new());return 8;}
    if(!strcmp(argv[1],"wrong-domain")) {H(request_status)(s);return 8;}
    if(!strcmp(argv[1],"live-audit"))return 0;
    if(!strcmp(argv[1],"stale-request")) {H(stop)(s);int64_t r=H(next_request)(s);H(request_release)(r);r=H(next_request)(s);H(request_status)(r-(INT64_C(1)<<32));return 8;}
    if(!strcmp(argv[1],"double-request")) {H(stop)(s);int64_t r=H(next_request)(s);H(request_release)(r);H(request_release)(r);return 8;}
    if(!strcmp(argv[1],"invalid-limits")) {H(set_limits)(s,1,1,1,1);return 8;}
    return 9;
}
'''

def run(command, **kwargs):
    return subprocess.run(command, capture_output=True, timeout=60, **kwargs)

class Server:
    def __init__(self, exe: Path, profile: str, env: dict[str, str]):
        self.process=subprocess.Popen([str(exe),profile],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env)
        assert self.process.stdout is not None
        if os.name != 'nt':
            assert select.select([self.process.stdout],[],[],5)[0], 'server did not start'
        line=self.process.stdout.readline()
        assert line.startswith(b'PORT '),(line,self.process.poll())
        self.port=int(line.split()[1]);self.cases=0
    def connect(self):
        s=socket.create_connection(('127.0.0.1',self.port),timeout=4);s.settimeout(4);return s
    def exchange(self, data: bytes, *, split: int|None=None, eof=False, slow=False):
        with self.connect() as s:
            if split is None:s.sendall(data)
            else:
                s.sendall(data[:split]);time.sleep(.001);s.sendall(data[split:])
            if eof:s.shutdown(socket.SHUT_WR)
            chunks=[];read_count=0
            while True:
                try: chunk=s.recv(17 if slow else 65536)
                except ConnectionResetError:break
                if not chunk:break
                chunks.append(chunk);read_count+=len(chunk)
                if slow and read_count<4096:time.sleep(.0001)
        self.cases+=1
        return parse_response(b''.join(chunks))
    def stop(self):
        self.exchange(request('/stop'))
        out,err=self.process.communicate(timeout=5)
        assert self.process.returncode==0 and not err,(self.process.returncode,out,err)
        assert out.startswith(b'REPORT '),out
        return list(map(int,out.split()[1:]))
    def abort(self):
        if self.process.poll() is None:self.process.kill()
        self.process.communicate(timeout=5)

def request(path='/',method='GET',body=b'',headers=(),version='HTTP/1.1'):
    fields=[('Host','localhost'),*headers]
    if body and not any(k.lower() in ('content-length','transfer-encoding') for k,v in fields):fields.append(('Content-Length',str(len(body))))
    return f'{method} {path} {version}\r\n'.encode()+b''.join(f'{k}: {v}\r\n'.encode() for k,v in fields)+b'\r\n'+body

def parse_response(raw: bytes):
    assert b'\r\n\r\n' in raw,raw
    headers,body=raw.split(b'\r\n\r\n',1);lines=headers.split(b'\r\n');status=int(lines[0].split()[1]);fields={}
    for line in lines[1:]:
        k,v=line.split(b':',1);key=k.lower();assert key not in fields,(key,raw);fields[key]=v.strip()
    assert fields[b'connection']==b'close',fields
    assert b'transfer-encoding' not in fields,fields
    return status,fields,body

def assert_response(result,status,body=None,*,head=False):
    actual,headers,payload=result;assert actual==status,(status,result)
    if body is not None:assert payload==body,('body bytes differ',len(body),len(payload),hashlib.sha256(body).hexdigest(),hashlib.sha256(payload).hexdigest(),status)
    if status==204:assert b'content-length' not in headers and payload==b'',result
    elif head or status==304:assert not payload,result
    else:assert int(headers[b'content-length'])==len(payload),result
    return headers

def normal_corpus(s:Server,soak:int):
    # http.client provides an independent ordinary-client response parser.
    c=http.client.HTTPConnection('127.0.0.1',s.port,timeout=4);c.request('GET','/health');r=c.getresponse();assert r.status==200 and r.read()==b'healthy' and r.getheader('Connection')=='close';c.close();s.cases+=1
    assert_response(s.exchange(request('/hello/Ada')),200,b'Ada')
    assert_response(s.exchange(request('/health',version='HTTP/1.0').replace(b'Host: localhost\r\n',b'')),200,b'healthy')
    assert_response(s.exchange(request('/health',headers=[('Host','duplicate')])),400)
    for host in ('example.com','127.0.0.1:8080','[::1]','[::1]:8080'):
        assert_response(s.exchange(request('/health').replace(b'localhost',host.encode())),200,b'healthy')
    assert_response(s.exchange(request('/health','HEAD')),200,b'',head=True)
    assert_response(s.exchange(request('/unknown','HEAD')),404,b'',head=True)
    h=assert_response(s.exchange(request('/health','POST')),405,b'');assert h[b'allow']==b'GET, HEAD'
    assert_response(s.exchange(request('/empty')),200,b'')
    assert_response(s.exchange(request('/204')),204,b'')
    assert_response(s.exchange(request('/304')),304,b'')
    h=assert_response(s.exchange(request('/unsafe')),200,b'safe');assert h[b'x-safe']==b'yes' and b'injected' not in h
    binary=b'A\0\xff\xc3\xa9\xf0\x9f\x9a\x80B'
    assert_response(s.exchange(request('/header-bytes').replace(b'\r\n\r\n',b'\r\nX-Binary: \xff\x80\r\n\r\n')),200,b'\xff\x80')
    fixed=request('/echo','POST',binary)
    chunked=request('/echo','POST',b'5;foo="a\\\"b"\r\n'+binary[:5]+b'\r\n'+f'{len(binary)-5:x}'.encode()+b'\r\n'+binary[5:]+b'\r\n0\r\nX-End: yes\r\n\r\n',headers=[('Transfer-Encoding','chunked')])
    for wire in (fixed,chunked):
        for split in range(1,len(wire)):assert_response(s.exchange(wire,split=split),200,binary)
    wire=request('/inspect?x=1&x=2%20z','POST',b'1\r\na\r\n0\r\nX-Repeat: third\r\n\r\n',headers=[('Transfer-Encoding','chunked'),('X-Repeat','first'),('X-Repeat','second')])
    assert_response(s.exchange(wire),200,b'query=x=1&x=2%20z\n0:first\n0:second\n1:third\n')
    doc={'name':'é猫🚀','escape':'"\\\n\t','nul':'a\0b','n':9007199254740993}
    body=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();wire=request('/json','POST',body,headers=[('Content-Type','application/json')])
    for split in range(1,len(wire)):
        response=s.exchange(wire,split=split);h=assert_response(response,200);assert h[b'content-type']==b'application/json';assert json.loads(response[2])==doc
    for body,status in [(b'{',400),(b'[]',422),(b'null',422),(b'{"name":null}',422),(b'{"name":"x","name":"y"}',400),(b'{"name":"\\uD800"}',400),(b'{"name":"a\x00b"}',400),(b'{"name":"\xff"}',400)]:assert_response(s.exchange(request('/json','POST',body)),status)
    # Exactly one message is exposed even when a second request shares the recv.
    response=s.exchange(request('/health')+request('/hello/second'));assert_response(response,200,b'healthy')
    with s.connect() as client:
        client.sendall(request('/echo','POST',headers=[('Content-Length','3'),('Expect','100-continue')]))
        interim=b''
        while not interim.endswith(b'\r\n\r\n'):interim+=client.recv(1)
        assert interim==b'HTTP/1.1 100 Continue\r\n\r\n',interim
        client.sendall(b'a\0b');out=b''
        while chunk:=client.recv(4096):out+=chunk
        assert_response(parse_response(out),200,b'a\0b');s.cases+=1
    large=s.exchange(request('/large'),slow=True);assert_response(large,200,bytes((i*17+3)&255 for i in range(262144)))
    # Peer reset while sending must not kill the listener or retain its socket.
    with s.connect() as client:
        client.sendall(request('/large'));client.setsockopt(socket.SOL_SOCKET,socket.SO_LINGER,struct.pack('ii',1,0))
    time.sleep(.01);assert_response(s.exchange(request('/health')),200,b'healthy')
    for i in range(soak):
        if i%4==0:assert_response(s.exchange(request('/echo','POST',binary)),200,binary)
        elif i%4==1:assert_response(s.exchange(request('/json','POST',b'{"name":"soak"}')),200)
        elif i%4==2:assert_response(s.exchange(request('/health')),200,b'healthy')
        else:assert_response(s.exchange(request('/health').replace(b'Host: localhost\r\n',b'')),400)

def invalid_corpus(s:Server):
    bad=[]
    for host in ('','a,b','a b','user@host','host/path','[::1','[broken]','[::1]:','a:','a:bad','a:65536','-host','a..b','a:0'):
        bad.append((request('/health').replace(b'localhost',host.encode()),400,'Host '+host))
    bad += [(request('/health').replace(b'Host: localhost\r\n',b''),400,'missing Host'),(request('/health',headers=[('host','localhost')]),400,'duplicate equal Host')]
    for wire in (b'GET /health HTTP/1.1\nHost: localhost\n\n',b'GET /health HTTP/1.1\r\nHost: localhost\r\nX: a\r\n folded\r\n\r\n',b'GET /health HTTP/1.1\r\nHost: localhost\r\nX : a\r\n\r\n',b'GET /health HTTP/1.1\r\nHost: localhost\r\nBad(Name: a\r\n\r\n'):
        bad.append((wire,400,'strict header line'))
    for fields in ([('Content-Length','0'),('Content-Length','0')],[('Content-Length','1'),('Content-Length','2')],[('Content-Length','0, 0')],[('Content-Length','+1')],[('Content-Length','-1')],[('Content-Length','18446744073709551616')],[('Content-Length','0'),('Transfer-Encoding','chunked')],[('Transfer-Encoding','chunked'),('Content-Length','0')],[('Transfer-Encoding','chunked'),('Transfer-Encoding','chunked')]):bad.append((request('/echo','POST',headers=fields),400,'ambiguous CL/TE'))
    for te in ('gzip','gzip, chunked','chunked, gzip','chunked, chunked'):bad.append((request('/echo','POST',headers=[('Transfer-Encoding',te)]),None,'unsupported TE'))
    bad += [(request('/echo','POST',headers=[('Content-Encoding','gzip')]),501,'CE'),(request('/health',headers=[('Upgrade','websocket'),('Connection','Upgrade')]),501,'upgrade'),(request('localhost:80','CONNECT'),501,'CONNECT'),(request('*','OPTIONS'),400,'asterisk target'),(request('http://localhost/health'),400,'absolute target'),(request('/bad%zz'),400,'percent'),(request('/bad#x'),400,'fragment'),(b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n',None,'HTTP2 preface'),(request('/health',version='HTTP/2.0'),505,'version'),(request('/health',headers=[('Expect','unrecognized')]),417,'expect'),(request('/health',headers=[('Expect','100-continue'),('Expect','100-continue')]),417,'duplicate expect')]
    for wire,status,label in bad:
        response=s.exchange(wire,eof=True)
        if status is None:assert response[0] in (400,501,505),(label,response)
        else:assert_response(response,status)
    for malformed in (b'Z\r\na\r\n0\r\n\r\n',b'1\r\naXX0\r\n\r\n',b'1\r\n',b'1\r\na\r\n',b'0\r\nX: y\r\n',b'10000000000000000\r\n',b'1;foo="unterminated\r\na\r\n0\r\n\r\n'):
        response=s.exchange(request('/echo','POST',malformed,headers=[('Transfer-Encoding','chunked')]),eof=True);assert response[0] in (400,413),(malformed,response)
    for name in ('Host','Content-Length','Transfer-Encoding','Authorization','Cookie','Connection'):
        wire=request('/echo','POST',f'0\r\n{name}: x\r\n\r\n'.encode(),headers=[('Transfer-Encoding','chunked')]);assert_response(s.exchange(wire),400)
    # Expect is admitted only after the complete header/framing/limit policy.
    for fields,status in [([('Host','duplicate'),('Content-Length','1'),('Expect','100-continue')],400),([('Content-Length','1048577'),('Expect','100-continue')],413)]:assert_response(s.exchange(request('/echo','POST',headers=fields)),status)

def tight_corpus(s:Server):
    assert_response(s.exchange(request('/health')),200,b'healthy')
    assert_response(s.exchange(request('/'+'x'*128)),414)
    assert_response(s.exchange(request('/health',headers=[('X','x'*512)])),431)
    assert_response(s.exchange(request('/health',headers=[('X'+str(i),'x') for i in range(8)])),431)
    assert_response(s.exchange(request('/echo','POST',headers=[('Content-Length','65')])),413)
    assert_response(s.exchange(request('/echo','POST',b'x'*64)),200,b'x'*64)
    # Exact admitted boundaries also pass, preventing limits from overrejecting.
    line=request('/'+'x'*112);assert len(line.split(b'\r\n')[0])+2==128;assert_response(s.exchange(line),404)
    headers=request('/health',headers=[('X','x'*488)]);assert len(headers.split(b'\r\n',1)[1])==512;assert_response(s.exchange(headers),200,b'healthy')
    assert_response(s.exchange(request('/health',headers=[('X'+str(i),'x') for i in range(7)])),200,b'healthy')
    assert_response(s.exchange(request('/echo','POST',b'1\r\na\r\n'*20+b'0\r\n\r\n',headers=[('Transfer-Encoding','chunked')])),200,b'a'*20)
    assert_response(s.exchange(request('/echo','POST',b'0\r\nX: '+b'a'*57+b'\r\n\r\n',headers=[('Transfer-Encoding','chunked')])),200,b'')
    assert_response(s.exchange(request('/echo','POST',b'41\r\n',headers=[('Transfer-Encoding','chunked')])),413)
    assert_response(s.exchange(request('/echo','POST',b'1;'+b'x'*64+b'=v\r\na\r\n0\r\n\r\n',headers=[('Transfer-Encoding','chunked')])),413)
    # Many tiny chunks are bounded by aggregate wire metadata, not decoded body.
    assert_response(s.exchange(request('/echo','POST',b'1\r\na\r\n'*24+b'0\r\n\r\n',headers=[('Transfer-Encoding','chunked')])),413)
    assert_response(s.exchange(request('/echo','POST',b'0\r\nX: '+b'a'*64+b'\r\n\r\n',headers=[('Transfer-Encoding','chunked')])),431)
    assert_response(s.exchange(request('/echo','POST',b'0\r\n'+b'X: a\r\n'*8+b'\r\n',headers=[('Transfer-Encoding','chunked')])),431)
    for wire in (b'GET /health HTTP/1.1\r\nHost:',request('/echo','POST',headers=[('Content-Length','2')])+b'a'):
        started=time.monotonic();assert_response(s.exchange(wire),408);assert time.monotonic()-started<1
    # Progress beats idle but cannot reset the absolute header/body deadline.
    for body in (False,True):
        with s.connect() as client:
            if body:client.sendall(request('/echo','POST',headers=[('Content-Length','20')]))
            else:client.sendall(b'GET /health HTTP/1.1\r\nX: ')
            started=time.monotonic()
            for i in range(10):
                try:client.sendall(b'a')
                except (BrokenPipeError,ConnectionResetError):break
                time.sleep(.05)
            out=b''
            while True:
                try:chunk=client.recv(4096)
                except ConnectionResetError:break
                if not chunk:break
                out+=chunk
            assert_response(parse_response(out),408);assert time.monotonic()-started<.8;s.cases+=1
    # Premature fixed-length EOF also rejects without retaining a handler.
    assert_response(s.exchange(request('/echo','POST',headers=[('Content-Length','2')])+b'a',eof=True),400)

def exercise(exe:Path,env,soak:int):
    c=run([str(exe),'bind'],env=env);assert c.returncode==0 and not c.stdout and not c.stderr,(c.returncode,c.stdout,c.stderr)
    for mode,message in [('stale',b'stale server'),('double',b'stale server'),('foreign',b'stale server'),('wrong-domain',b'stale request'),('stale-request',b'stale request'),('double-request',b'stale request'),('invalid-limits',b'invalid HTTP size'),('live-audit',b'live HTTP server')]:
        c=run([str(exe),mode],env=env);assert c.returncode!=0 and not c.stdout and message in c.stderr,(mode,c.returncode,c.stdout,c.stderr)
    report={}
    for profile in ('normal','tight'):
        s=Server(exe,profile,env)
        try:
            if profile=='normal':normal_corpus(s,soak);invalid_corpus(s)
            else:tight_corpus(s)
            counts=s.stop();report[profile]={'requests':counts[0],'partial_sends':counts[1],'send_failures':counts[2],'retained_bytes':counts[3],'kernel_fds':counts[4],'oracle_cases':s.cases}
            if profile=='normal' and os.sys.platform.startswith('linux'):assert counts[1]>0 and counts[2]>0,counts
        finally:s.abort()
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--clang',default=os.environ.get('FREAK_CLANG','clang'));p.add_argument('--optimization',type=int,choices=(0,2,3),action='append');p.add_argument('--adapter',choices=('c','llvm'),action='append');p.add_argument('--sanitize',action='store_true');p.add_argument('--soak',type=int,default=1000);p.add_argument('--report',type=Path);args=p.parse_args()
    assert args.soak>=0
    clang=shutil.which(args.clang);assert clang,args.clang
    repo=Path(__file__).resolve().parents[1];runtime=repo/'freakc/runtime'
    env=os.environ.copy();env['ASAN_OPTIONS']='detect_leaks=1:halt_on_error=1';env['UBSAN_OPTIONS']='halt_on_error=1'
    report={'runtime_sha256':hashlib.sha256((runtime/'freak_runtime.c').read_bytes()).hexdigest(),'http_sha256':hashlib.sha256((runtime/'freak_v35_http.inc').read_bytes()).hexdigest(),'clang':str(Path(clang).resolve()),'clang_sha256':hashlib.sha256(Path(clang).read_bytes()).hexdigest(),'clang_version':run([clang,'--version']).stdout.decode().splitlines()[0],'sanitize':args.sanitize,'matrices':[]}
    with tempfile.TemporaryDirectory(prefix='freak-http-floor-') as temporary:
        root=Path(temporary);h=root/'http.c';h.write_text(HARNESS)
        flags=['-lws2_32','-lshell32'] if os.name=='nt' else ['-lm','-pthread']
        if os.sys.platform.startswith('linux'):flags+=['-Wl,--wrap=send']
        if args.sanitize:
            flags+=['-fsanitize=address,undefined,function','-fno-omit-frame-pointer','-g']
            control=root/'control.c';control.write_text('#include <stdlib.h>\nint main(int n,char **v){volatile char *p=malloc(1);p[n+4]=3;free((void*)p);return 0;}\n')
            exe=root/'control';c=run([clang,str(control),'-O0',*flags,'-o',str(exe)]);assert c.returncode==0,c.stderr.decode()
            c=run([str(exe)],env=env);assert c.returncode!=0 and b'AddressSanitizer' in c.stderr,c.stderr.decode();report['sanitizer_failing_control']=True
        for opt in args.optimization or (0,2,3):
            for adapter in args.adapter or ('c','llvm'):
                exe=root/f'http-{adapter}-O{opt}'
                command=[clang,str(h),str(runtime/'freak_llvm_runtime.c'),f'-I{runtime}',f'-O{opt}','-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1','-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1',*flags,'-o',str(exe)]
                if adapter=='llvm':command.insert(1,'-DUSE_LLVM_ADAPTER=1')
                c=run(command);assert c.returncode==0,c.stderr.decode()
                corpus=exercise(exe,env,args.soak);report['matrices'].append({'adapter':adapter,'optimization':opt,'corpus':corpus,'bind_stop_ownership':True,'controlled_errors':8})
                print(f'PASS HTTP {adapter} O{opt}: {corpus}',flush=True)
    if args.report:args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
