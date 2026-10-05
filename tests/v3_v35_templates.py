#!/usr/bin/env python3
"""Native template generation and installed project build/run/test acceptance.

The small creator harness supplies only the existing payload/platform selector
interfaces. Its generation code and checked FS operations are production code.
Passing --cli additionally exercises real init dispatch, package imports,
native build/run/test and default HTTP exposure from the installed payload.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import select
import shutil
import subprocess
import tempfile
import time
from v3_v35_http import assert_response, parse_response, request

SELECTORS=r'''
task cli_find_runtime_dir() -> word { give back process::env("TEMPLATE_RUNTIME") }
task cli_is_windows() -> bool { give back process::env("OS") == "Windows_NT" }
task cli_payload_is_resolution_error(value: word) -> bool { give back value.starts_with("!freak-payload-resolution-error!") }
'''
MAIN=r'''
task main() {
    pilot success = cli_create_template(process::arg(1), process::arg(2))
    if success { say "OK" } else { say "ERROR " + cli_template_error }
    cli_template_error = ""
}
'''

def run(command,*,cwd,env=None,timeout=90):
    return subprocess.run(list(map(str,command)),cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8',timeout=timeout)

def tree(path:Path):
    return {str(p.relative_to(path)).replace(os.sep,'/'):p.read_bytes() for p in path.rglob('*') if p.is_file()}

def expected(canonical:Path,kind:str,name:str):
    consumer='template-consumer-app' if name=='template-consumer' else 'template-consumer'
    return {k:v.replace(b'@@NAME@@',name.encode()).replace(b'@@CONSUMER_NAME@@',consumer.encode()) for k,v in tree(canonical/kind).items()}

def creator_case(binary:Path,kind:str,destination:Path,env,*,success:bool):
    r=run([binary,kind,destination],cwd=destination.parent if destination.parent.exists() else destination.parents[1],env=env)
    assert r.returncode==0 and not r.stderr,(kind,destination,r.returncode,r.stdout,r.stderr)
    assert r.stdout.startswith('OK\n' if success else 'ERROR '),(kind,destination,success,r.stdout)
    return r

def creator_corpus(binary:Path,canonical:Path,root:Path,env):
    parent=root/'parent space🚀';parent.mkdir();env=env.copy()
    # Selector points at the existing repo payload; CWD contains no templates.
    env['TEMPLATE_RUNTIME']=str(canonical.parents[1]/'freakc/runtime')
    for kind in ('cli','lib','http'):
        name=kind+'-demo';destination=parent/name;creator_case(binary,kind,destination,env,success=True)
        assert tree(destination)==expected(canonical,kind,name),kind
        original=tree(destination);creator_case(binary,kind,destination,env,success=False);assert tree(destination)==original
    destination=parent/('a'*64);creator_case(binary,'lib',destination,env,success=True);assert tree(destination)==expected(canonical,'lib','a'*64)
    destination=parent/'template-consumer';creator_case(binary,'lib',destination,env,success=True);assert tree(destination)==expected(canonical,'lib','template-consumer')
    sentinel=parent/'sentinel';sentinel.mkdir();(sentinel/'keep').write_bytes(b'unknown existing work\0')
    creator_case(binary,'cli',sentinel,env,success=False);assert (sentinel/'keep').read_bytes()==b'unknown existing work\0'
    empty=parent/'empty';empty.mkdir();creator_case(binary,'cli',empty,env,success=False);assert list(empty.iterdir())==[]
    regular=parent/'regular';regular.write_bytes(b'preserve');creator_case(binary,'cli',regular,env,success=False);assert regular.read_bytes()==b'preserve'
    for name in ('bad name','bad"name','bad$name','bad&name','é','9start','CON','nul','LPT9','COM1','x'*65):
        destination=parent/name;creator_case(binary,'cli',destination,env,success=False);assert not destination.exists(),name
    creator_case(binary,'unknown',parent/'unknown',env,success=False);assert not (parent/'unknown').exists()
    creator_case(binary,'cli',parent/'missing-parent'/'child',env,success=False);assert not (parent/'missing-parent').exists()
    if os.name!='nt':
        for name,target in [('linked',sentinel),('broken',parent/'absent')]:
            linked=parent/name;linked.symlink_to(target,target_is_directory=True);creator_case(binary,'cli',linked,env,success=False);assert linked.is_symlink()
        linkparent=root/'linkparent';linkparent.symlink_to(parent,target_is_directory=True)
        creator_case(binary,'cli',linkparent/'escape',env,success=False);assert not (parent/'escape').exists()
    # Two real creators race for one name. Publication must preserve one whole
    # generation and both creators must clean only their own staging tickets.
    destination=parent/'race';processes=[subprocess.Popen([str(binary),'cli',str(destination)],cwd=parent,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE) for _ in range(2)]
    results=[p.communicate(timeout=10) for p in processes];assert sorted(out.startswith(b'OK\n') for out,err in results)==[False,True],results
    assert all(p.returncode==0 and not err for p,(out,err) in zip(processes,results)),results
    assert tree(destination)==expected(canonical,'cli','race')
    # The authoritative selector error cannot fall back to an ambient tree.
    failure_env=env.copy();failure_env['TEMPLATE_RUNTIME']='!freak-payload-resolution-error!ambiguous|root'
    creator_case(binary,'cli',parent/'resolution',failure_env,success=False);assert not (parent/'resolution').exists()
    variants=['missing','oversized','invalid-utf8','embedded-nul']
    if os.name!='nt':variants+=['linked-file','linked-template-root']
    for variant in variants:
        payload=root/variant;source=payload/'templates/v35/cli';shutil.copytree(canonical/'cli',source);(payload/'runtime').mkdir()
        readme=source/'README.md'
        if variant=='missing':readme.unlink()
        elif variant=='oversized':readme.write_bytes(b'x'*131073)
        elif variant=='invalid-utf8':readme.write_bytes(b'\xff')
        elif variant=='embedded-nul':readme.write_bytes(b'a\0b')
        elif variant=='linked-file':readme.unlink();readme.symlink_to(sentinel/'keep')
        else:shutil.rmtree(source);source.symlink_to(canonical/'cli',target_is_directory=True)
        failure_env=env.copy();failure_env['TEMPLATE_RUNTIME']=str(payload/'runtime')
        before=sorted(p.name for p in parent.iterdir());creator_case(binary,'cli',parent/('fail-'+variant),failure_env,success=False)
        assert sorted(p.name for p in parent.iterdir())==before,variant
        assert (sentinel/'keep').read_bytes()==b'unknown existing work\0'
    assert not any(p.name.startswith('freak-template-') for p in parent.iterdir()),list(parent.iterdir())
    return {'canonical_kinds':3,'no_clobber_and_race':True,'bounded_partial_failure_variants':len(variants),'unicode_parent':True,'library_max_name_and_consumer_identity':True,'source_template_sha256':{f'{kind}/{path}':hashlib.sha256(data).hexdigest() for kind in ('cli','lib','http') for path,data in tree(canonical/kind).items()}}

def http_once(cli:Path,project:Path,backend:str,env):
    import socket
    child_env=env.copy();child_env['FREAK_HTTP_PORT']='0';child_env.pop('FREAK_HTTP_BIND',None);child_env.pop('FREAK_HTTP_ALLOW_NON_LOOPBACK',None)
    child=subprocess.Popen([str(cli),'run','--'+backend,'--','--once'],cwd=project,env=child_env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8')
    try:
        assert child.stdout is not None;deadline=time.monotonic()+30;lines=[];port=None
        while time.monotonic()<deadline:
            if os.name!='nt' and not select.select([child.stdout],[],[],min(1,max(0,deadline-time.monotonic())))[0]:continue
            line=child.stdout.readline();lines.append(line)
            if line.startswith('HTTP http://127.0.0.1:'):port=int(line.rstrip().rsplit(':',1)[1]);break
            if not line and child.poll() is not None:break
        assert port,lines
        with socket.create_connection(('127.0.0.1',port),timeout=4) as client:
            client.sendall(request('/health'));wire=b''
            while data:=client.recv(4096):wire+=data
        assert_response(parse_response(wire),200,b'healthy')
        out,err=child.communicate(timeout=10);assert child.returncode==0,(lines,out,err)
        assert not err,(lines,out,err)
    finally:
        if child.poll() is None:child.kill();child.communicate(timeout=5)

def installed_corpus(cli:Path,canonical:Path,root:Path,env,backends):
    report=[]
    for kind in ('cli','lib','http'):
        name=kind+'-installed';project=root/name
        created=run([cli,'init',name,'--template='+kind],cwd=root,env=env);assert created.returncode==0,(created.stdout,created.stderr)
        assert tree(project)==expected(canonical,kind,name),(kind,tree(project).keys())
        preserved=tree(project);duplicate=run([cli,'init',name,'--template='+kind],cwd=root,env=env);assert duplicate.returncode!=0,(kind,duplicate.stdout,duplicate.stderr);assert tree(project)==preserved
        for backend in backends:
            tested=run([cli,'test','--'+backend],cwd=project,env=env);assert tested.returncode==0,(kind,backend,tested.stdout,tested.stderr)
            # Break the actual function and prove the generated named test fails.
            module=project/('src/routes.fk' if kind=='http' else 'src/greet.fk');original=module.read_text();module.write_text(original.replace('"Hello, "','"Broken, "'))
            failed=run([cli,'test','--'+backend],cwd=project,env=env);assert failed.returncode!=0,(kind,backend,failed.stdout,failed.stderr);module.write_text(original)
            app=project/'examples/consumer' if kind=='lib' else project
            built=run([cli,'build','--'+backend],cwd=app,env=env);assert built.returncode==0,(kind,backend,built.stdout,built.stderr)
            if kind=='http':http_once(cli,app,backend,env)
            else:
                command=[cli,'run','--'+backend]
                if kind=='cli':command+=['--','Ada $ & % \\']
                executed=run(command,cwd=app,env=env);assert executed.returncode==0,(kind,backend,executed.stdout,executed.stderr)
                expected_line='Hello, consumer!' if kind=='lib' else 'Hello, Ada $ & % \\!'
                assert expected_line in executed.stdout.splitlines(),executed.stdout
                if kind=='lib':assert executed.stdout.splitlines().count('Hello, consumer!')==1,executed.stdout
            if kind=='lib':
                tested=run([cli,'test','--'+backend],cwd=app,env=env);assert tested.returncode==0,(kind,backend,tested.stdout,tested.stderr)
            report.append({'template':kind,'backend':backend,'build_run_test':True,'failing_test_control':True})
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--compiler',type=Path,required=True);p.add_argument('--clang',default=os.environ.get('FREAK_CLANG','clang'));p.add_argument('--runtime-root',type=Path,required=True);p.add_argument('--templates-root',type=Path);p.add_argument('--optimization',type=int,choices=(0,2,3),action='append');p.add_argument('--backend',choices=('c','llvm'),action='append');p.add_argument('--sanitize',action='store_true');p.add_argument('--cli',type=Path);p.add_argument('--payload-home',type=Path);p.add_argument('--report',type=Path);args=p.parse_args()
    repo=Path(__file__).resolve().parents[1];canonical=(args.templates_root or repo/'templates/v35').resolve(strict=True);compiler=args.compiler.resolve(strict=True);runtime=args.runtime_root.resolve(strict=True)
    generator=(repo/'src/cli/templates.fk').read_text();backends=args.backend or ('c','llvm');env=os.environ.copy();env['ASAN_OPTIONS']='detect_leaks=1:halt_on_error=1';env['UBSAN_OPTIONS']='halt_on_error=1'
    vendor=runtime/'third_party/llhttp'
    if not vendor.exists():vendor=runtime.parents[1]/'third_party/llhttp'
    pinned=[compiler,repo/'src/cli/templates.fk',*sorted(p for p in canonical.rglob('*') if p.is_file()),*sorted(runtime.glob('*.c')),*sorted(runtime.glob('*.h')),*sorted(runtime.glob('*.inc')),*sorted(p for p in vendor.rglob('*') if p.is_file())]
    before={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in pinned}
    evidence={'compiler_sha256':before[str(compiler)],'generator_sha256':hashlib.sha256(generator.encode()).hexdigest(),'pinned_input_sha256':before,'strict_borrow':True,'sanitize':args.sanitize,'creator_matrices':[],'installed_cli_matrices':[],'installed_cli_verified':False}
    with tempfile.TemporaryDirectory(prefix='freak-native-templates-') as temporary:
        root=Path(temporary);source=root/'creator.fk';source.write_text(SELECTORS+'\n'+generator+'\n'+MAIN)
        if args.sanitize:
            control=root/'control.c';control.write_text('#include <stdlib.h>\nint main(int n,char **v){volatile char *p=malloc(1);p[n+4]=3;free((void*)p);return 0;}\n');binary=root/'control'
            linked=run([args.clang,control,'-O0','-fsanitize=address,undefined','-o',binary],cwd=root);assert linked.returncode==0,(linked.stdout,linked.stderr)
            failed=run([binary],cwd=root,env=env);assert failed.returncode!=0 and 'AddressSanitizer' in failed.stderr,failed.stderr;evidence['sanitizer_failing_control']=True
        for backend in backends:
            compiled=run([compiler,source,'--'+backend,'--strict-borrow'],cwd=root);assert compiled.returncode==0,(compiled.stdout,compiled.stderr)
            generated=Path(str(source)+('.c' if backend=='c' else '.ll'))
            for opt in args.optimization or (0,2,3):
                binary=root/f'creator-{backend}-O{opt}';command=[args.clang,'-O'+str(opt),generated,runtime/'freak_runtime.c','-I'+str(runtime),'-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1','-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1','-o',binary]
                if args.sanitize:command+=['-fsanitize=address,undefined,function','-fno-omit-frame-pointer','-g']
                if backend=='llvm':command.append(runtime/'freak_llvm_runtime.c')
                command+=['-lws2_32','-lshell32'] if os.name=='nt' else ['-lm']
                linked=run(command,cwd=root);assert linked.returncode==0,(linked.stdout,linked.stderr)
                scratch=root/f'cases-{backend}-O{opt}';scratch.mkdir();corpus=creator_corpus(binary,canonical,scratch,env)
                evidence['creator_matrices'].append({'backend':backend,'optimization':opt,'corpus':corpus});print(f'PASS native template creator {backend} O{opt}: fixed canonical bytes,owned staging,no-clobber,race,links,bounded failures',flush=True)
        if args.cli:
            cli=args.cli.resolve(strict=True);cli_env=env.copy()
            if args.payload_home:cli_env['FREAK_HOME']=str(args.payload_home.resolve(strict=True))
            projects=root/'installed-projects';projects.mkdir();evidence['installed_cli_matrices']=installed_corpus(cli,canonical,projects,cli_env,backends);evidence['installed_cli_verified']=True;evidence['cli_sha256']=hashlib.sha256(cli.read_bytes()).hexdigest()
    after={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in pinned};assert before==after,'pinned compiler/runtime/templates changed during gate';evidence['pinned_inputs_unchanged']=True
    if args.report:args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(evidence,indent=2)+'\n')
if __name__=='__main__':main()
