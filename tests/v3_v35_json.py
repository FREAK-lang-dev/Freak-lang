#!/usr/bin/env python3
"""Strict JSON corpus, construction, ownership and scalar C/LLVM ABI gate.

Direct Clang harnesses use production runtime source, never a Python compiler.
Python's JSON decoder supplies an independent value/Unicode roundtrip oracle;
number-lexeme and duplicate-key policy have separate assertions.
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

HARNESS = r'''
#include "freak_runtime.c"
#ifndef FREAK_V35_JSON_INCLUDED
#include "freak_v35_json.inc"
#endif
#include <assert.h>
#ifdef USE_LLVM_ADAPTER
#define J(name) freak_llvm_json_document_##name
#define W(s) ((int64_t)(intptr_t)(s))
static freak_word view(int64_t word) { return freak_llvm_word_view(word); }
static void drop(int64_t word) { freak_llvm_word_release_replaced(word,0); }
#else
#define J(name) freak_json_document_##name
#define W(s) freak_word_lit(s)
static freak_word view(freak_word word) { return word; }
static void drop(freak_word word) { freak_word_release_owned(&word); }
#endif
#define REQUIRE(c) do { if (!(c)) { fprintf(stderr,"FAIL at line %d\n",__LINE__); exit(2); } } while (0)
static void check_word(freak_word w, const char *s) { REQUIRE(w.length==strlen(s)&&!memcmp(w.data,s,w.length)); }
static int64_t parse_data(const unsigned char *data,size_t length) {
    int64_t b=freak_byte_buffer_with_capacity((int64_t)length);
    freak_byte_buffer_record *r=freak_byte_buffer_require(b,"test");
    if(length) memcpy(r->data,data,length); r->length=length;
    int64_t d=J(parse_bytes)(b); freak_byte_buffer_release(b); return d;
}
static void normal(void) {
    int64_t words=freak_v3_live_words();
    size_t c_words=freak_c_owned_word_count, llvm_words=freak_llvm_owned_count, buffers=freak_byte_buffer_live_count;
    int64_t d=J(parse)(W("{\"null\":null,\"big\":9007199254740993,\"n\":-0.0100E+999,\"b\":false,\"a\":[\"\\uD83D\\uDE80\",\"a\\u0000b\"]}"));
    REQUIRE(J(ok)(d)); int64_t root=J(root)(d);
    REQUIRE(J(kind)(d,root)==6&&J(count)(d,root)==5);
    REQUIRE(J(kind)(d,J(object_get)(d,root,W("missing")))==0);
    REQUIRE(J(kind)(d,J(object_get)(d,root,W("null")))==1);
    int64_t big=J(object_get)(d,root,W("big"));
    __auto_type num=J(number_text)(d,big); check_word(view(num),"9007199254740993"); drop(num);
    __auto_type fraction=J(number_text)(d,J(object_get)(d,root,W("n"))); check_word(view(fraction),"-0.0100E+999"); drop(fraction);
    REQUIRE(J(bool_value)(d,J(object_get)(d,root,W("b")))==0);
    int64_t arr=J(object_get)(d,root,W("a")); REQUIRE(J(count)(d,arr)==2);
    REQUIRE(J(array_get)(d,arr,-1)==0&&J(array_get)(d,arr,2)==0);
    __auto_type rocket=J(string_word)(d,J(array_get)(d,arr,0)); check_word(view(rocket),"\xf0\x9f\x9a\x80"); drop(rocket);
    int64_t nul=J(string_bytes)(d,J(array_get)(d,arr,1));
    freak_byte_buffer_record *b=freak_byte_buffer_require(nul,"test"); REQUIRE(b->length==3&&!memcmp(b->data,"a\0b",3));
    int64_t keys=J(object_key_bytes)(d,root,0); REQUIRE(freak_byte_buffer_length(keys)==4); freak_byte_buffer_release(keys);
    __auto_type serialized=J(serialize_word)(d); freak_word text=view(serialized);
    REQUIRE(strstr(text.data,"9007199254740993")&&strstr(text.data,"-0.0100E+999")&&strstr(text.data,"\\u0000"));
    int64_t d2=J(parse)(serialized); REQUIRE(J(ok)(d2)); J(release)(d); J(release)(d2);
    REQUIRE(freak_byte_buffer_length(nul)==3); freak_byte_buffer_release(nul); drop(serialized);
    d=J(new)(); root=J(make_object)(d);
    int64_t a=J(make_array)(d), s=J(make_string)(d,W("quote\" slash\\\n\t\x01 \xc3\xa9"));
    REQUIRE(J(array_append)(d,a,s)); REQUIRE(J(array_append)(d,a,J(make_null)(d)));
    REQUIRE(J(array_append)(d,a,J(make_bool)(d,1))); REQUIRE(J(array_append)(d,a,J(make_number)(d,W("123456789012345678901234567890"))));
    REQUIRE(J(object_insert)(d,root,W("key\"\n"),a));
    int64_t kb=freak_byte_buffer_new(); freak_byte_buffer_write_byte(kb,0);
    int64_t value=J(make_string_bytes)(d,kb); REQUIRE(J(object_insert_bytes)(d,root,kb,value)); REQUIRE(J(object_get_bytes)(d,root,kb)==value); freak_byte_buffer_release(kb);
    REQUIRE(J(set_root)(d,root)); int64_t output=J(serialize_bytes)(d);
    d2=J(parse_bytes)(output); REQUIRE(J(ok)(d2)&&J(count)(d2,J(root)(d2))==2);
    J(release)(d); J(release)(d2); freak_byte_buffer_release(output);
    /* Independent documents retain distinct state; generations never reuse views. */
    for(int i=0;i<300;i++) { d=J(parse)(W("true")); d2=J(parse)(W("[null]")); REQUIRE(J(kind)(d,J(root)(d))==2); REQUIRE(J(kind)(d2,J(root)(d2))==5); J(release)(d); J(release)(d2); }
    REQUIRE(freak_json_live_documents==0&&freak_json_live_nodes==0&&freak_v3_live_words()==words);
    REQUIRE(freak_c_owned_word_count==c_words&&freak_llvm_owned_count==llvm_words&&freak_byte_buffer_live_count==buffers);
}
static void limits(void) {
    size_t n=FREAK_JSON_INPUT_LIMIT+1; unsigned char *text=malloc(n); memset(text,' ',n);
    int64_t d=parse_data(text,n); REQUIRE(!J(ok)(d)); J(release)(d);
    memcpy(text,"null",4); d=parse_data(text,FREAK_JSON_INPUT_LIMIT); REQUIRE(J(ok)(d)); J(release)(d); free(text);
    n=FREAK_JSON_STRING_LIMIT+3; text=malloc(n); text[0]='"'; memset(text+1,'a',n-2); text[n-1]='"';
    d=parse_data(text,n); REQUIRE(!J(ok)(d)); J(release)(d);
    text[n-2]='"'; d=parse_data(text,n-1); REQUIRE(J(ok)(d)); J(release)(d); free(text);
    n=FREAK_JSON_NUMBER_LIMIT+1; text=malloc(n); memset(text,'1',n);
    d=parse_data(text,n); REQUIRE(!J(ok)(d)); J(release)(d);
    d=parse_data(text,n-1); REQUIRE(J(ok)(d)); J(release)(d); free(text);
    text=malloc(259); memset(text,'[',129); text[129]='0'; memset(text+130,']',129);
    d=parse_data(text,259); REQUIRE(!J(ok)(d)); J(release)(d);
    memset(text,'[',127); text[127]='0'; memset(text+128,']',127);
    d=parse_data(text,255); REQUIRE(J(ok)(d)); J(release)(d); free(text);
    n=2*FREAK_JSON_NODE_LIMIT+1; text=malloc(n); text[0]='[';
    for(size_t i=0;i<FREAK_JSON_NODE_LIMIT;i++){text[2*i+1]='0';text[2*i+2]=',';} text[n-1]=']';
    d=parse_data(text,n); REQUIRE(!J(ok)(d)); J(release)(d);
    text[n-3]=']'; d=parse_data(text,n-2); REQUIRE(J(ok)(d)); J(release)(d); free(text);
    d=J(new)(); int64_t a=J(make_array)(d), b=J(make_array)(d);
    REQUIRE(J(array_append)(d,a,b)); REQUIRE(!J(array_append)(d,b,a)&&!J(ok)(d)); J(release)(d);
    d=J(new)(); a=J(make_object)(d); REQUIRE(J(object_insert)(d,a,W("x"),J(make_null)(d)));
    REQUIRE(!J(object_insert)(d,a,W("x"),J(make_null)(d))&&!J(ok)(d)); J(release)(d);
    d=J(new)(); REQUIRE(J(make_number)(d,W("01"))==0&&!J(ok)(d)); J(release)(d);
    d=J(new)(); REQUIRE(J(make_bool)(d,2)==0&&!J(ok)(d)); J(release)(d);
    d=J(new)(); a=J(make_array)(d); b=J(make_null)(d);
    REQUIRE(J(array_append)(d,a,b)); REQUIRE(!J(array_append)(d,a,b)); J(release)(d);
    d=J(new)(); a=J(make_array)(d);
    for(unsigned i=1;i<FREAK_JSON_DEPTH_LIMIT;i++){b=J(make_array)(d);REQUIRE(J(array_append)(d,b,a));a=b;}
    b=J(make_array)(d); REQUIRE(!J(array_append)(d,b,a)); J(release)(d);
    d=J(new)();
    for(unsigned i=0;i<FREAK_JSON_NODE_LIMIT;i++) REQUIRE(J(make_null)(d));
    REQUIRE(J(make_null)(d)==0&&!J(ok)(d)); J(release)(d);
    d=J(new)(); int64_t bytes=freak_byte_buffer_with_capacity(FREAK_JSON_STRING_LIMIT);
    freak_byte_buffer_record *buffer=freak_byte_buffer_require(bytes,"text budget");
    memset(buffer->data,'x',FREAK_JSON_STRING_LIMIT); buffer->length=FREAK_JSON_STRING_LIMIT;
    for(int i=0;i<4;i++) REQUIRE(J(make_string_bytes)(d,bytes));
    REQUIRE(J(make_string)(d,W("x"))==0&&!J(ok)(d));
    freak_byte_buffer_release(bytes); J(release)(d);
    REQUIRE(!freak_json_live_documents&&!freak_json_live_nodes);
}
int main(int argc,char **argv) {
    REQUIRE(argc>=2);
    if(!strcmp(argv[1],"normal")){normal();limits();return 0;}
    int64_t d=J(parse)(W("{\"s\":\"a\\u0000b\"}")), root=J(root)(d);
    if(!strcmp(argv[1],"stale")){int64_t node=root;J(release)(d);d=J(parse)(W("null"));J(kind)(d,node);return 8;}
    if(!strcmp(argv[1],"double")){J(release)(d);J(release)(d);return 8;}
    if(!strcmp(argv[1],"foreign")){int64_t other=J(parse)(W("null"));J(kind)(other,root);return 8;}
    if(!strcmp(argv[1],"wrong-type")){J(number_text)(d,root);return 8;}
    if(!strcmp(argv[1],"nul-word")){J(string_word)(d,J(object_get)(d,root,W("s")));return 8;}
    if(!strcmp(argv[1],"live-audit")) return 0;
    J(release)(d);
    REQUIRE(argc==3);FILE *f=fopen(argv[2],"rb");REQUIRE(f);fseek(f,0,SEEK_END);long size=ftell(f);REQUIRE(size>=0);rewind(f);
    unsigned char *data=malloc((size_t)size+1);REQUIRE(data);REQUIRE(fread(data,1,(size_t)size,f)==(size_t)size);fclose(f);
    d=parse_data(data,(size_t)size);free(data);
    if(!J(ok)(d)){__auto_type e=J(error)(d);freak_word w=view(e);fprintf(stderr,"JSON_ERROR:%lld:%.*s\n",(long long)J(error_position)(d),(int)w.length,w.data);drop(e);J(release)(d);return 3;}
    __auto_type output=J(serialize_word)(d);freak_word w=view(output);fwrite(w.data,1,w.length,stdout);drop(output);J(release)(d);return 0;
}
'''
VALID = [b"null",b"true",b"false",b"0",b"-0",b"-0.0",b"1e+10",b"1E-999",b"9007199254740993",b"123456789012345678901234567890", b"[]",b"{}",b'[null,true,false,0,"x"]',b'{"a":null,"b":[],"c":{}}',b'"\\\"\\\\\\/\\b\\f\\n\\r\\t"',b'"\\u0000"',b'"\\uD800\\uDC00"',b'"\\udbff\\udfff"',b'"\\u20ac"', '"é猫🚀"'.encode(),b' \r\n\t{"a":"z"}\r\n',b'{"":0,"\\u0000":1}', b'"'+bytes(range(0x20,0x7f)).replace(b'"',b'\\"').replace(b'\\',b'\\\\')+b'"']
# Last string gets separately corrected escaping by the independent generator.
VALID[-1] = json.dumps(''.join(map(chr,range(0x20,0x7f))),ensure_ascii=False).encode()
INVALID = [b"",b" ",b"NaN",b"Infinity",b"-Infinity",b"+1",b"01",b"-01",b".1",b"1.",b"1e",b"1e+",b"1e-",b"--1",b"0x10",b"true false",b"nullx",b"[]x",b"{}{}",b"[1,]",b"[,1]",b"[1 2]",b"{a:1}",b'{"a" 1}',b'{"a":}',b'{"a":1,}',b'{"a":1 "b":2}',b'{"a":1,"a":2}',b'{"a":1,"\\u0061":2}',b'{"\\u0000":1,"\\u0000":2}',b"[",b"{",b'"',b'"\\"',b'"\\x00"',b'"\\u123"',b'"\\uXXXX"',b'"\\uD800"',b'"\\uDC00"',b'"\\uD800\\u0000"',b'"\\uD800x"',b'"\\uDBFF\\uD800"',b'"a\nb"',b'"a\x00b"',b'"\xc0\x80"',b'"\xed\xa0\x80"',b'"\xf4\x90\x80\x80"',b'"\xf5\x80\x80\x80"',b'"\x80"',b'"\xe2\x82"',b'"\xff"',b"\xef\xbb\xbfnull",b"\x0bnull",b"null\x00",b"True",b"FALSE",b'"\\v"']

def run(command, **kwargs):
    return subprocess.run(command, capture_output=True, timeout=35, **kwargs)

def main():
    p=argparse.ArgumentParser();p.add_argument('--clang',default=os.environ.get('FREAK_CLANG','clang'));p.add_argument('--optimization',type=int,choices=(0,2,3),action='append');p.add_argument('--sanitize',action='store_true');p.add_argument('--report',type=Path);args=p.parse_args()
    clang=shutil.which(args.clang);assert clang, args.clang
    repo=Path(__file__).resolve().parents[1];runtime=repo/'freakc/runtime'
    env=os.environ.copy();env['ASAN_OPTIONS']='detect_leaks=1:halt_on_error=1';env['UBSAN_OPTIONS']='halt_on_error=1'
    report={'runtime_sha256':hashlib.sha256((runtime/'freak_runtime.c').read_bytes()).hexdigest(),'json_sha256':hashlib.sha256((runtime/'freak_v35_json.inc').read_bytes()).hexdigest(),'clang':str(Path(clang).resolve()),'clang_sha256':hashlib.sha256(Path(clang).read_bytes()).hexdigest(),'clang_version':run([clang,'--version']).stdout.decode().splitlines()[0],'sanitize':args.sanitize,'matrices':[]}
    with tempfile.TemporaryDirectory(prefix='freak-strict-json-') as temporary:
        root=Path(temporary);h=root/'json.c';h.write_text(HARNESS)
        flags=['-lws2_32','-lshell32'] if os.name=='nt' else ['-lm']
        if args.sanitize:
            flags+=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-g']
            control=root/'control.c';control.write_text('#include <stdlib.h>\nint main(int n,char **v){volatile char *p=malloc(1);p[n+4]=3;free((void*)p);return 0;}\n')
            exe=root/'control';c=run([clang,str(control),'-O0',*flags,'-o',str(exe)]);assert c.returncode==0,c.stderr.decode()
            c=run([str(exe)],env=env);assert c.returncode!=0 and b'AddressSanitizer' in c.stderr,c.stderr.decode();report['sanitizer_failing_control']=True
        for opt in args.optimization or (0,2,3):
            for adapter in ('c','llvm'):
                exe=root/f'json-{adapter}-O{opt}'
                command=[clang,str(h),str(runtime/'freak_llvm_runtime.c'),f'-I{runtime}',f'-O{opt}','-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1','-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1',*flags,'-o',str(exe)]
                if adapter=='llvm':command.insert(1,'-DUSE_LLVM_ADAPTER=1')
                c=run(command);assert c.returncode==0,c.stderr.decode()
                c=run([str(exe),'normal'],env=env);assert c.returncode==0 and not c.stdout and not c.stderr,(c.returncode,c.stdout,c.stderr)
                for case,message in [('stale',b'stale node view'),('double',b'stale document ticket'),('foreign',b'foreign'),('wrong-type',b'wrong type'),('nul-word',b'string_bytes'),('live-audit',b'live JSON document')]:
                    c=run([str(exe),case],env=env);assert c.returncode!=0 and not c.stdout and message in c.stderr,(case,c.returncode,c.stdout,c.stderr)
                for i,source in enumerate(VALID+INVALID):
                    f=root/'input.json';f.write_bytes(source);c=run([str(exe),'corpus',str(f)],env=env)
                    if i<len(VALID):
                        assert c.returncode==0 and not c.stderr,(source,c.returncode,c.stderr)
                        assert json.loads(c.stdout)==json.loads(source),(source,c.stdout)
                    else:
                        assert c.returncode==3 and not c.stdout and c.stderr.startswith(b'JSON_ERROR:'),(source,c.returncode,c.stdout,c.stderr)
                        position=int(c.stderr.split(b':')[1]);assert 0<=position<=len(source),(source,position)
                report['matrices'].append({'adapter':adapter,'optimization':opt,'valid':len(VALID),'invalid':len(INVALID),'limits_construction_ownership':True,'controlled_errors':6})
                print(f'PASS strict JSON {adapter} O{opt}: {len(VALID)} valid, {len(INVALID)} invalid, limits/construction/owners, 6 controlled errors',flush=True)
    if args.report:args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
