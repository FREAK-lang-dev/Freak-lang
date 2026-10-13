#!/usr/bin/env python3
"""Execute native coded sites and immutable source facts without host re-reads."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from v3_checked_parsing import build_stage2, run, sanitizer_env
from v3_v35_acceptance import run_command


def file_sha(path: Path) -> str:
 with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def resource_context() -> dict:
 context={'python_pid':os.getpid(),'platform':sys.platform}
 try:
  import resource
  context['rss']={'unit':'bytes' if sys.platform=='darwin' else 'KiB',
   'self_max':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
   'children_max':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
   'scope':'cumulative host-process and reaped-child high-water marks, not this command alone'}
  context['limits']={}
  for name in ('RLIMIT_AS','RLIMIT_DATA','RLIMIT_RSS'):
   if hasattr(resource,name):context['limits'][name]=list(resource.getrlimit(getattr(resource,name)))
 except (ImportError,OSError,ValueError):context['resource_module']='unavailable'
 try:context['physical_memory_bytes']=os.sysconf('SC_PAGE_SIZE')*os.sysconf('SC_PHYS_PAGES')
 except (AttributeError,OSError,ValueError):pass
 return context


def require_ok(result: subprocess.CompletedProcess[str],label: str) -> None:
 if result.returncode:raise AssertionError(f'{label} failed ({result.returncode})\n{result.stdout[-4000:]}{result.stderr[-4000:]}')


def resolve_clang(selected: str) -> Path:
 found=shutil.which(selected)
 path=Path(found or selected).resolve(strict=True)
 if not path.is_file():raise ValueError('selected Clang is not a file')
 return path


def native_environment(clang: Path,evidence=None,*,platform: str|None=None) -> tuple[dict,list[Path]]:
 env=sanitizer_env()
 if (platform or sys.platform)!='win32':return env,[]
 command=[str(clang),'-print-resource-dir']
 result=evidence.run(command,clang.parent,timeout=10) if evidence is not None else run(command,clang.parent,timeout=10)
 require_ok(result,'selected Clang resource query')
 if not result.stdout.strip():raise ValueError('selected Clang resource query returned no directory')
 resource=Path(result.stdout.strip()).resolve(strict=True)
 if not resource.is_dir():raise ValueError('selected Clang resource is not a directory')
 files=set()
 for pattern in ('clang_rt.asan_dynamic-*.dll','libclang_rt.asan_dynamic-*.dll'):
  files.update(path for path in clang.parent.glob(pattern) if path.is_file())
  files.update(path for path in resource.rglob(pattern) if path.is_file())
 if not files:raise FileNotFoundError('selected Clang ASan DLL is absent from its bin and resource tree')
 ordered=sorted(files,key=lambda path:str(path))
 directories=[str(clang.parent.resolve())]
 directories+=sorted({str(path.parent.resolve()) for path in ordered}-set(directories))
 env['PATH']=os.pathsep.join(directories)+os.pathsep+env.get('PATH','')
 return env,ordered


class FactsEvidence:
 """Retain original command bytes and bounded source/phase/resource context."""
 MAX_REPORT_BYTES=1024*1024
 EMITTED_TAIL_BYTES=16*1024

 def __init__(self,path: Path|None,root: Path):
  self.path=path
  self.raw_dir=path.parent/(path.stem+'-raw') if path is not None else root/'command-evidence'
  self.report={'schema':1,'commands':[],'matrices':[],'source_snapshots':{},'emitted_outputs':{},'pinned_inputs':{},
   'progress':{'outcome':'running','sequence':0,'completed_contracts':0,'expected_contracts':26,'active':{'phase':'report-start'}}}
  self.identities={}

 def __enter__(self):
  self.raw_dir.mkdir(parents=True,exist_ok=True)
  self._write()
  return self

 @staticmethod
 def _note(original: BaseException,label: str,secondary: BaseException):
  try:original.add_note(label+type(secondary).__name__[:160])
  except BaseException:pass

 def __exit__(self,kind,error,traceback):
  if error is not None:
   self.report['progress'].update(outcome='failed',exception_type=kind.__name__[:160])
   try:self._write()
   except BaseException as recording:self._note(error,'Facts evidence recording failed: ',recording)
   return False
  if self.report['progress']['outcome']!='passed':
   error=RuntimeError('facts verification ended without a passing checkpoint')
   self.report['progress'].update(outcome='failed',exception_type=type(error).__name__)
   try:self._write()
   except BaseException as recording:self._note(error,'Facts evidence recording failed: ',recording)
   raise error
  return False

 def _write(self):
  if self.path is None:return
  self.report['progress']['sequence']+=1
  data=(json.dumps(self.report,indent=2)+'\n').encode('utf-8')
  if len(data)>self.MAX_REPORT_BYTES:raise ValueError('facts report exceeds bounded size')
  self.path.parent.mkdir(parents=True,exist_ok=True)
  temporary=None;original=None
  try:
   with tempfile.NamedTemporaryFile(dir=self.path.parent,prefix='.'+self.path.name+'-',delete=False) as stream:
    temporary=Path(stream.name);stream.write(data);stream.flush();os.fsync(stream.fileno())
   os.replace(temporary,self.path)
  except BaseException as error:
   original=error
   raise
  finally:
   if temporary is not None:
    try:temporary.unlink(missing_ok=True)
    except BaseException as cleanup_error:
     if original is None:raise
     self._note(original,'Facts staged-file cleanup failed: ',cleanup_error)

 @staticmethod
 def _print(label: str,context: dict):
  print(label+' '+json.dumps(context,sort_keys=True)[:4000],flush=True)

 def stage(self,phase: str,*,backend: str|None=None,fixture: str|None=None):
  if not phase or len(phase)>160:raise ValueError('invalid facts phase')
  active={'phase':phase,'resource':resource_context()}
  if backend is not None:active['backend']=backend
  if fixture is not None:active['fixture']=fixture
  self.report['progress']['active']=active
  self._write();self._print('FACTS_PHASE',active)

 def pin(self,path: Path):
  logical=str(path.absolute());resolved=path.resolve(strict=True)
  if not resolved.is_file():raise ValueError('facts input is not a file')
  identity=(str(resolved),file_sha(resolved))
  first=self.identities.setdefault(logical,identity)
  if first!=identity:raise AssertionError('facts input identity changed: '+logical)
  self.report['pinned_inputs'][logical]={'resolved_path':first[0],'sha256':first[1]}

 def verify_pins(self):
  for logical,identity in self.identities.items():
   resolved=Path(logical).resolve(strict=True)
   if (str(resolved),file_sha(resolved))!=identity:raise AssertionError('facts input identity changed: '+logical)

 def source_snapshot(self,source: Path,backend: str):
  data=source.read_bytes();retained=self.raw_dir/f'facts_{backend}.fk';retained.write_bytes(data)
  self.report['source_snapshots'][backend]={'path':str(source),'retained_path':str(retained),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
  self.pin(source);self.pin(retained)
  self._write()

 def _emitted(self,path: Path,record: dict):
  result={'path':str(path),'stable':False}
  if record.get('cleanup_failed') or record.get('returncode') is None:
   result['reason']='owned child cleanup or termination not confirmed'
  elif not path.is_file():result['reason']='no emitted output exists after terminal command'
  else:
   size=path.stat().st_size
   with path.open('rb') as stream:
    stream.seek(max(0,size-self.EMITTED_TAIL_BYTES));tail=stream.read(self.EMITTED_TAIL_BYTES)
   retained=self.raw_dir/(path.name+'.tail');retained.write_bytes(tail)
   result.update(stable=True,bytes=size,sha256=file_sha(path),tail_path=str(retained),tail_bytes=len(tail),tail_sha256=hashlib.sha256(tail).hexdigest(),tail_scope='at most final16KiB after owned command termination')
   self.pin(path);self.pin(retained)
  self.report['emitted_outputs'][str(path)]=result

 def run(self,command:list[str],cwd:Path,env:dict|None=None,timeout:int=180,*,emitted:Path|None=None) -> subprocess.CompletedProcess[str]:
  active=self.report['progress']['active'];label=active['phase']
  prefix=self.raw_dir/f'{len(self.report["commands"]):03d}-{label}'
  def checkpoint(record):
   active=self.report['progress']['active']
   active['command_index']=len(self.report['commands'])-1
   if 'pid' in record:active['pid']=record['pid']
   if 'elapsed_seconds' in record:
    active['returncode']=record['returncode'];active['resource_after']=resource_context()
    if emitted is not None:self._emitted(emitted,record)
   self._write()
  result=run_command(command,cwd=cwd,env=env if env is not None else os.environ.copy(),label=label,prefix=prefix,records=self.report['commands'],expected=None,timeout=timeout,on_record=checkpoint)
  text=lambda data:data.decode('utf-8',errors='replace').replace('\r\n','\n').replace('\r','\n')
  self._print('FACTS_COMMAND',{'phase':label,'returncode':result.returncode,'stdout_tail':text(result.stdout)[-1500:],'stderr_tail':text(result.stderr)[-1500:]})
  return subprocess.CompletedProcess(result.args,result.returncode,text(result.stdout),text(result.stderr))

 def matrix_started(self,backend:str):
  if backend not in ('c','llvm') or backend in [m['backend'] for m in self.report['matrices']]:raise ValueError('invalid facts matrix')
  self.report['matrices'].append({'backend':backend,'completed_cases':[],'outcome':'running'})

 def contract_completed(self,backend:str,name:str):
  matrix=self.report['matrices'][-1]
  if matrix['backend']!=backend or name not in CASES or name in matrix['completed_cases']:raise ValueError('invalid facts contract')
  matrix['completed_cases'].append(name)
  self.report['progress']['completed_contracts']+=1
  self._write()

 def matrix_finished(self,backend:str):
  matrix=self.report['matrices'][-1]
  if matrix['backend']!=backend or matrix['completed_cases']!=list(CASES):raise ValueError('incomplete facts matrix')
  matrix['outcome']='passed';self._write()

 def passed(self):
  matrices=self.report['matrices']
  if [m['backend'] for m in matrices]!=['c','llvm'] or any(m['outcome']!='passed' or m['completed_cases']!=list(CASES) for m in matrices) or self.report['progress']['completed_contracts']!=26:raise ValueError('incomplete facts contracts cannot pass')
  self.stage('final-input-verification');self.verify_pins()
  self.report['pinned_inputs_unchanged']=True
  self.report['progress'].update(outcome='passed',active={'phase':'complete'})
  self._write()

CASES = {
 'unbound': ('task main() { say missing; }\n', 'E0001'),
 'type': ('task main() { pilot x: int = "word"; }\n', 'E0002'),
 'move': ('task take(text: word) {} task main() { pilot text = "owner" + " word"; take(text); say text; }\n', 'E0003'),
 'immutable': ('task main() { fixed pilot x = 1; x = 2; }\n', 'E0004'),
 'call': ('task choose(value: int) {} task main() { choose(); }\n', 'E0005'),
 'numeric_parse': ('task main() { say 1.2.3; }\n', 'E0007'),
 'overflow': ('task main() { say 99999999999999999999999; }\n', 'E0008'),
 'generic_syntax': ('task main() { say "\\q"; }\n', ''),
 'empty_registered_source': ('', 'E0005'),
 'mapped_foreign_snapshot': ('task main() { say missing; }\n', 'E0001'),
 'unknown_snapshot': ('task main() {}\n', 'E0001'),
 'empty_unread_snapshot': ('task main() {}\n', 'E0001'),
 'repeated_when_semicolons': ('task main() { when 1 { ;;; 1 -> say "one";;; 2 -> say "two";;; }; }\n', None),
}


def quote(value: str) -> str:
 return '"'+value.replace('\\','\\\\').replace('"','\\"').replace('\n','\\n').replace('\r','\\r').replace('\t','\\t').replace('{','\\{').replace('}','\\}')+'"'


def main() -> int:
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--compiler',type=Path)
 parser.add_argument('--runtime',type=Path,help='immutable candidate runtime directory; defaults to this checkout')
 parser.add_argument('--clang',default=os.environ.get('FREAK_CLANG') or shutil.which('clang'))
 parser.add_argument('--report',type=Path,help='retain atomic phase and raw command evidence outside scratch')
 args=parser.parse_args();assert args.clang
 repo=Path(__file__).resolve().parents[1];runtime=args.runtime.resolve(strict=True) if args.runtime else repo/'freakc/runtime'
 parts=[repo/'src/compiler/v3'/f'{part}.fk' for part in ('globals','helpers','lexer','parser','checker')]
 prefix=''.join(part.read_text() for part in parts)
 globals_text=parts[0].read_text()
 handles=sorted(set(re.findall(r'^pilot (\w+)\s*=\s*0\s*$',globals_text,re.M)) & set(re.findall(r'\b(\w+)\s*=\s*array_new\(\)',prefix)))
 cleanup='\n'.join(f'if {name} != 0 {{ array_release({name}); {name} = 0; }}' for name in handles)
 flags=['-O2','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1','-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1','-I',str(runtime)]
 links=['-lws2_32'] if sys.platform=='win32' else ['-lm']
 with tempfile.TemporaryDirectory(prefix='freak-v35-diagnostic-facts-') as directory, FactsEvidence(args.report,Path(directory)) as evidence:
  root=Path(directory)
  evidence.stage('compiler-resolution')
  clang=resolve_clang(args.clang);evidence.pin(clang)
  compiler=args.compiler.resolve(strict=True) if args.compiler else build_stage2(clang=str(clang),repo=repo,root=root)
  evidence.pin(compiler)
  for pinned in [Path(__file__),repo/'tests/v3_checked_parsing.py',repo/'tests/v3_v35_acceptance.py',*parts,*sorted(path for path in runtime.rglob('*') if path.is_file() and path.suffix in ('.c','.h','.inc'))]:evidence.pin(pinned)
  evidence.stage('sanitizer-resource-query')
  native_env,dlls=native_environment(clang,evidence)
  for dll in dlls:evidence.pin(dll)
  evidence.report['host_runtime']={'clang_path':str(clang),'asan_dlls':[str(dll) for dll in dlls]}
  original_file=root/'original source.fk'
  choices='\n'.join('if selected == '+quote(name)+' { original = '+quote(source)+'; wanted = '+quote(code or '')+'; }' for name,(source,code) in CASES.items())
  harness=prefix+f'''
task main() {{
 pilot selected = process::arg(1)
 pilot original = ""
 pilot wanted = ""
 {choices}
 input_file = {quote(str(original_file))}
 init_arrays()
 diagnostic_source = original
 source_map_reset()
 pilot expected_file = input_file
 pilot loaded_source = original
 if selected == "mapped_foreign_snapshot" {{
   expected_file = input_file + " imported"
   pilot prefix_source = "task prefix() \\{{\\}}"
   source_map_register(input_file, prefix_source)
   source_map_register(expected_file, original)
   loaded_source = prefix_source + "\\n" + original
 }} else {{ source_map_register(input_file, original); }}
 tokenize(loaded_source)
 if error_count == 0 {{ parse_program(); strict_borrow = true; if error_count == 0 {{ check_program(); }} }}
 pilot snapshot_expected = wanted != ""
 if selected == "unknown_snapshot" {{
   expected_file = "/unregistered/provenance.fk"
   snapshot_expected = false
   diag_error_at_code("E0001", "unregistered source", "", expected_file, 1, 1)
 }}
 if selected == "empty_unread_snapshot" {{
   source_map_reset()
   diagnostic_source = ""
   snapshot_expected = false
   diag_error_at_code("E0001", "source never loaded", "", input_file, 1, 1)
 }}
 pilot selected_fact = 0 - 1
 pilot index = 0
 repeat diag_fact_count() times {{
   if diag_fact_code(index) == wanted {{ selected_fact = index; }}
   index += 1
 }}
 if selected == "repeated_when_semicolons" {{
   if error_count != 0 {{ panic("valid repeated semicolons rejected"); }}
   say "valid-when-separators"
 }} else {{
   if selected_fact < 0 {{ panic("missing explicit diagnostic site code"); }}
   if diag_fact_message(selected_fact) == "" {{ panic("missing message"); }}
   if diag_fact_file(selected_fact) != expected_file {{ panic("wrong original provenance"); }}
   if diag_fact_line(selected_fact) != 1 or diag_fact_column(selected_fact) < 1 {{ panic("wrong original position"); }}
   if snapshot_expected and not diag_fact_source_known(selected_fact) {{ panic("missing original source"); }}
   if not snapshot_expected and diag_fact_source_known(selected_fact) {{ panic("unavailable source fabricated for cast"); }}
   pilot saved_source = diag_fact_source(selected_fact)
   source_map_reset()
   diagnostic_source = "changed in memory"
   lex_source = "changed in memory"
   pilot changed = fs::write_checked(input_file, "changed on disk")
   if not fs::result_ok(changed) {{ panic("hostile source mutation fixture failed"); }}
   fs::result_release(changed)
   if snapshot_expected and diag_fact_source(selected_fact) != original {{ panic("fact re-read or aliased changed source"); }}
   reset_diagnostics()
   if snapshot_expected and saved_source != original {{ panic("getter did not clone independent source owner"); }}
   if diag_fact_count() != 0 or error_count != 0 or parse_error_count != 0 {{ panic("stale diagnostics after reset"); }}
   if diag_fact_source_known(0) or diag_fact_source_known(-1) or diag_fact_source(0) != "" {{ panic("invalid fact accessor"); }}
   say "native-fact-ok"
 }}
 reset_diagnostics()
 source_map_reset()
 {cleanup}
}}
'''
  for backend in ('c','llvm'):
   evidence.matrix_started(backend)
   source=root/f'facts_{backend}.fk';source.write_text(harness)
   evidence.source_snapshot(source,backend)
   evidence.stage('compiler-emission',backend=backend)
   require_ok(evidence.run([str(compiler),str(source),'--'+backend],root,emitted=Path(str(source)+('.c' if backend=='c' else '.ll'))),'fact component emission '+backend)
   objects=[]
   for unit in ('freak_runtime.c','freak_llvm_runtime.c'):
    if unit=='freak_llvm_runtime.c' and backend=='c':continue
    evidence.stage('runtime-compilation',backend=backend,fixture=unit)
    obj=root/f'{backend}_{unit}.o';require_ok(evidence.run([str(clang),*flags,'-c',str(runtime/unit),'-o',str(obj)],root),'fact runtime');objects.append(str(obj))
   binary=root/f'facts_{backend}';suffix='.c' if backend=='c' else '.ll'
   evidence.stage('native-link',backend=backend)
   require_ok(evidence.run([str(clang),*flags,str(source)+suffix,*objects,*links,'-o',str(binary)],root),'fact native component link '+backend)
   for name in CASES:
    original_file.write_text('deliberately unrelated host bytes')
    evidence.stage('native-contract',backend=backend,fixture=name)
    result=evidence.run([str(binary),name],root,env=native_env)
    marker='valid-when-separators' if CASES[name][1] is None else 'native-fact-ok'
    assert result.returncode==0 and marker in result.stdout and not result.stderr,(backend,name,result)
    evidence.contract_completed(backend,name)
   evidence.matrix_finished(backend)
   print(f'PASS {backend}: explicit codes, cloned source snapshots, hostile memory/disk mutation, reset and repeated when separators',flush=True)
  evidence.passed()
 print(f'V3.5 diagnostic facts: PASS ({2*len(CASES)} native contracts)',flush=True)
 return 0

if __name__=='__main__':raise SystemExit(main())
