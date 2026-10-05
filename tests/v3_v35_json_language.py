#!/usr/bin/env python3
"""Execute the strict JSON facade using an explicitly fresh native V3 compiler.

This is the vertical language/ABI gate; direct-runtime corpus verification is
separate in v3_v35_json.py. Both are required for the JSON slice.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

PROGRAM = r'''
task main() {
    pilot doc = json_document_parse("{\"x\":null,\"n\":9007199254740993,\"b\":true,\"a\":[\"hé\",\"a\\u0000b\"]}")
    say json_document_ok(doc)
    pilot root = json_document_root(doc)
    say json_document_kind(doc, json_document_object_get(doc, root, "missing"))
    say json_document_kind(doc, json_document_object_get(doc, root, "x"))
    say json_document_count(doc, root)
    say json_document_number_text(doc, json_document_object_get(doc, root, "n"))
    say json_document_bool_value(doc, json_document_object_get(doc, root, "b"))
    pilot array = json_document_object_get(doc, root, "a")
    say json_document_string_word(doc, json_document_array_get(doc, array, 0))
    pilot binary = json_document_string_bytes(doc, json_document_array_get(doc, array, 1))
    say binary.length()
    pilot key = json_document_object_key_bytes(doc, root, 0)
    say key.to_word()
    key.release()
    pilot serialized = json_document_serialize_bytes(doc)
    pilot second = json_document_parse_bytes(serialized)
    say json_document_ok(second)
    json_document_release(second)
    serialized.release()
    json_document_release(doc)
    say binary.read_byte()
    say binary.read_byte()
    say binary.read_byte()
    binary.release()
    pilot bad = json_document_parse("[1,]")
    say json_document_ok(bad)
    say json_document_error_position(bad)
    say json_document_error(bad)
    json_document_release(bad)
    pilot made = json_document_new()
    pilot object = json_document_make_object(made)
    pilot items = json_document_make_array(made)
    say json_document_array_append(made, items, json_document_make_null(made))
    say json_document_array_append(made, items, json_document_make_bool(made, 0))
    say json_document_array_append(made, items, json_document_make_number(made, "-0.0100E+999"))
    say json_document_array_append(made, items, json_document_make_string(made, "quote\"\n"))
    say json_document_object_insert(made, object, "items", items)
    pilot zero = ByteBuffer::new()
    zero.write_byte(0)
    pilot nul = json_document_make_string_bytes(made, zero)
    say json_document_object_insert_bytes(made, object, zero, nul)
    say json_document_kind(made, json_document_object_get_bytes(made, object, zero))
    zero.release()
    say json_document_set_root(made, object)
    say json_document_serialize_word(made)
    json_document_release(made)
}
'''
EXPECTED = ('1\n0\n1\n4\n9007199254740993\n1\nhé\n3\nx\n1\n97\n0\n98\n0\n3\nexpected JSON value\n'
            '1\n1\n1\n1\n1\n1\n4\n1\n{"items":[null,false,-0.0100E+999,"quote\\\"\\u000a"],"\\u0000":"\\u0000"}\n')
NEGATIVE = {
    'input_type':('task main() { pilot d = json_document::parse_bytes(1) }','ByteBuffer'),
    'return_type':('task main() { pilot d = json_document::new(); pilot x: int = json_document::serialize_bytes(d) }','ByteBuffer'),
    'word_type':('task main() { pilot d = json_document::parse(1) }','word'),
    'arity':('task main() { pilot d = json_document::new(); json_document::release(d, d) }','argument'),
}
CONTROLLED = {
    'stale_doc':'task main() { pilot d = json_document_parse("null"); json_document_release(d); say json_document_ok(d) }',
    'stale_view':'task main() { pilot d = json_document_parse("null"); pilot node = json_document_root(d); json_document_release(d); pilot second = json_document_parse("null"); say json_document_kind(second, node) }',
    'wrong_type':'task main() { pilot d = json_document_parse("null"); say json_document_number_text(d, json_document_root(d)) }',
    'nul_text':'task main() { pilot d = json_document_parse("\"a\\u0000b\""); say json_document_string_word(d, json_document_root(d)) }',
}

def run(command, *, cwd, env=None):
    return subprocess.run(command,cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8',timeout=90)

def main():
    p=argparse.ArgumentParser();p.add_argument('--compiler',type=Path,required=True);p.add_argument('--clang',default=os.environ.get('FREAK_CLANG','clang'));p.add_argument('--runtime-root',type=Path);p.add_argument('--optimization',type=int,choices=(0,2,3),action='append');p.add_argument('--report',type=Path);args=p.parse_args()
    repo=Path(__file__).resolve().parents[1];runtime=args.runtime_root or repo/'freakc/runtime';compiler=args.compiler.resolve(strict=True)
    facade=(repo/'std/json_document.fk').read_text();evidence={'compiler_sha256':hashlib.sha256(compiler.read_bytes()).hexdigest(),'facade_sha256':hashlib.sha256(facade.encode()).hexdigest(),'matrices':[]}
    with tempfile.TemporaryDirectory(prefix='freak-json-language-') as temporary:
        root=Path(temporary);suffix='.exe' if os.name=='nt' else ''
        for opt in args.optimization or (0,2,3):
            for backend in ('c','llvm'):
                for name,program in [('facade',PROGRAM),*CONTROLLED.items()]:
                    source=root/f'{name}-{backend}.fk';source.write_text(facade+'\n'+program)
                    compiled=run([str(compiler),str(source),f'--{backend}'],cwd=root);assert compiled.returncode==0,(name,compiled.stdout,compiled.stderr)
                    generated=Path(str(source)+('.c' if backend=='c' else '.ll'));binary=root/f'{name}-{backend}-O{opt}{suffix}'
                    cmd=[args.clang,f'-O{opt}',str(generated),str(runtime/'freak_runtime.c'),f'-I{runtime}','-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1','-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1','-o',str(binary)]
                    if backend=='llvm':cmd.append(str(runtime/'freak_llvm_runtime.c'))
                    cmd+=['-lws2_32','-lshell32'] if os.name=='nt' else ['-lm']
                    linked=run(cmd,cwd=root);assert linked.returncode==0,(name,linked.stdout,linked.stderr)
                    executed=run([str(binary)],cwd=root)
                    if name=='facade':assert executed.returncode==0 and executed.stdout==EXPECTED and not executed.stderr,(backend,opt,executed.returncode,executed.stdout,executed.stderr)
                    else:assert executed.returncode!=0 and not executed.stdout and 'JSON document:' in executed.stderr,(name,backend,executed.returncode,executed.stdout,executed.stderr)
                for name,(program,diagnostic) in NEGATIVE.items():
                    source=root/f'{name}-{backend}.fk';source.write_text(program)
                    generated=Path(str(source)+('.c' if backend=='c' else '.ll'));generated.write_text('stale output')
                    failed=run([str(compiler),str(source),f'--{backend}'],cwd=root)
                    assert failed.returncode!=0 and diagnostic.lower() in (failed.stdout+failed.stderr).lower(),(name,failed.returncode,failed.stdout,failed.stderr)
                    assert not generated.exists(),(name,'stale generated artifact survived')
                evidence['matrices'].append({'backend':backend,'optimization':opt,'facade':True,'controlled_errors':len(CONTROLLED),'semantic_rejections':len(NEGATIVE)})
                print(f'PASS strict JSON facade {backend} O{opt}: native execution,4controlled errors,4semantic rejections',flush=True)
    if args.report:args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(evidence,indent=2)+'\n')
if __name__=='__main__':main()
