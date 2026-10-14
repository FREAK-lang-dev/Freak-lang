#!/usr/bin/env python3
"""Execute native coded sites and immutable source facts without host re-reads."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from v3_checked_parsing import build_stage2, run, sanitizer_env
from v3_v35_language import require_ok

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
 args=parser.parse_args();assert args.clang
 repo=Path(__file__).resolve().parents[1];runtime=args.runtime.resolve(strict=True) if args.runtime else repo/'freakc/runtime'
 parts=[repo/'src/compiler/v3'/f'{part}.fk' for part in ('globals','helpers','lexer','parser','checker')]
 prefix=''.join(part.read_text() for part in parts)
 globals_text=parts[0].read_text()
 handles=sorted(set(re.findall(r'^pilot (\w+)\s*=\s*0\s*$',globals_text,re.M)) & set(re.findall(r'\b(\w+)\s*=\s*array_new\(\)',prefix)))
 cleanup='\n'.join(f'if {name} != 0 {{ array_release({name}); {name} = 0; }}' for name in handles)
 flags=['-O2','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1','-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1','-I',str(runtime)]
 links=['-lws2_32'] if sys.platform=='win32' else ['-lm']
 with tempfile.TemporaryDirectory(prefix='freak-v35-diagnostic-facts-') as directory:
  root=Path(directory);compiler=args.compiler.resolve(strict=True) if args.compiler else build_stage2(clang=args.clang,repo=repo,root=root)
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
   source=root/f'facts_{backend}.fk';source.write_text(harness)
   require_ok(run([str(compiler),str(source),'--'+backend],root),'fact component emission '+backend)
   objects=[]
   for unit in ('freak_runtime.c','freak_llvm_runtime.c'):
    if unit=='freak_llvm_runtime.c' and backend=='c':continue
    obj=root/f'{backend}_{unit}.o';require_ok(run([args.clang,*flags,'-c',str(runtime/unit),'-o',str(obj)],root),'fact runtime');objects.append(str(obj))
   binary=root/f'facts_{backend}';suffix='.c' if backend=='c' else '.ll'
   require_ok(run([args.clang,*flags,str(source)+suffix,*objects,*links,'-o',str(binary)],root),'fact native component link '+backend)
   for name in CASES:
    original_file.write_text('deliberately unrelated host bytes')
    result=run([str(binary),name],root,env=sanitizer_env())
    marker='valid-when-separators' if CASES[name][1] is None else 'native-fact-ok'
    assert result.returncode==0 and marker in result.stdout and not result.stderr,(backend,name,result)
   print(f'PASS {backend}: explicit codes, cloned source snapshots, hostile memory/disk mutation, reset and repeated when separators',flush=True)
 print(f'V3.5 diagnostic facts: PASS ({2*len(CASES)} native contracts)',flush=True)
 return 0

if __name__=='__main__':raise SystemExit(main())
