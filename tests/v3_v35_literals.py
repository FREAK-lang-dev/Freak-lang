#!/usr/bin/env python3
"""Verify strict escapes, bounded interpolation, fixed roots and when arms."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from v3_checked_parsing import build_stage2, run, sanitizer_env
from v3_v35_language import require_ok

POSITIVE = {
 'repeated_when_semicolons': ('''task main() { when 1 { ;;; 1 -> say "one";;; 2 -> say "two";;; }; }''', 'one\n'),
 'escapes': (r'''task main() { say "a\nb\tc\rd\"e\\f"; say "\x419"; say "\\x41"; }''', 'a\nb\tc\rd"e\\f\nA9\n\\x41\n'),
 'escaped_expression_braces': (r'''task main() { say "\{guess * 2\}"; say "\{f(x)\}"; say "\{missing\}"; }''', '{guess * 2}\n{f(x)}\n{missing}\n'),
 'json_literal': (r'''task main() { say "{\"guess\":2}"; say "{key: value}"; say "{}"; }''', '{"guess":2}\n{key: value}\n{}\n'),
 'backslash_before_interpolation': (r'''task main() { pilot number = 7; say "\\{number}"; say "\x7Bnumber\x7D"; }''', '\\7\n{number}\n'),
 'field_interpolation': ('''shape Person { age: int, name: word } task main() { pilot person = Person { age: 7, name: "owner" + " word" }; say "{person.age}:{person.name}"; }''', '7:owner word\n'),
 'grounded_context': ('task grounded() -> int { give back 7; } task main() { pilot grounded = 2; grounded += 1; say grounded; if true { grounded pilot x = 4; say x; } }', '3\n4\n'),
 'grounded_root': ('grounded pilot value = 4; task main() { say value; }', '4\n'),
 'default_mutability': ('task main() { pilot x = 1; x += 2; pilot mut y = 3; y = 4; pilot xs: List<int> = [1]; xs[0] = 2; say x + y + xs[0]; }', '9\n'),
 'fixed_read_and_shadow': ('''fixed pilot value = 4
shape Box { value: int }
fixed pilot box = Box { value: 7 }
task main() { say value; say box.value; if true { pilot mut value = 2; value += 3; say value; } say value; }''', '4\n7\n5\n4\n'),
 'fixed_nested_read': ('''shape Inner { value: int } shape Outer { inner: Inner }
task main() { fixed pilot outer = Outer { inner: Inner { value: 7 } }; say outer.inner.value; }''', '7\n'),
 'unique_when': ('''task main() { when 2 { 1 -> say "one"; 2 -> say "two"; _ -> say "other"; }; when true { false -> say "false"; true -> say "true"; }; when "B" { "A" -> say "a"; "B" -> say "b"; }; }''', 'two\ntrue\nb\n'),
 'distinct_large_integers': ('''task main() { when 9223372036854775807 { 9223372036854775806 -> say "lower"; 9223372036854775807 -> say "upper"; }; }''', 'upper\n'),
 'large_integer_then_float_bucket': ('''task main() { when 9223372036854775807 { 9223372036854775806 -> say "lower"; 9223372036854775807.0 -> say "bucket"; }; }''', 'bucket\n'),
}
NEGATIVE = {
 'unknown_escape': (r'''task main() {
    say "a\q"
}''', 'unknown string escape'),
 'unsupported_unicode_escape': (r'''task main() { say "\u0041"; }''', 'unknown string escape'),
 'unsupported_zero_escape': (r'''task main() { say "\0"; }''', 'unknown string escape'),
 'expression_interpolation': ('''task main() { pilot guess = 2; say "{guess * 2}"; }''', 'unsupported interpolation expression'),
 'call_interpolation': ('''task f(value: int) -> int { give back value; } task main() { pilot x = 2; say "{f(x)}"; }''', 'unsupported interpolation expression'),
 'spaced_interpolation': ('''task main() { pilot x = 2; say "{ x }"; }''', 'unsupported interpolation expression'),
 'unclosed_interpolation': ('''task main() { pilot x = 2; say "{x"; }''', 'unterminated interpolation expression'),
 'reserved_interpolation': ('''task main() { say "{true}"; }''', 'unsupported interpolation expression'),
 'fixed_scalar': ('''task main() { fixed pilot x = 1; x = 2; }''', 'fixed pilot cannot be modified'),
 'fixed_compound': ('''task main() { fixed pilot x = 1; x += 2; }''', 'fixed pilot cannot be modified'),
 'fixed_global': ('''fixed pilot x = 1
task main() { x += 2; }''', 'fixed pilot cannot be modified'),
 'fixed_field': ('''shape Box { value: int } task main() { fixed pilot box = Box { value: 1 }; box.value = 2; }''', 'fixed pilot cannot be modified'),
 'fixed_nested_field': ('''shape Inner { value: int } shape Outer { inner: Inner } task main() { fixed pilot box = Outer { inner: Inner { value: 1 } }; box.inner.value += 2; }''', 'fixed pilot cannot be modified'),
 'fixed_list': ('''task main() { fixed pilot values: List<int> = [1]; values[0] = 2; }''', 'fixed pilot cannot be modified'),
 'fixed_list_push': ('''task main() { fixed pilot values: List<int> = [1]; values.push(2); }''', 'fixed pilot cannot be modified'),
 'fixed_list_pop': ('''task main() { fixed pilot values: List<int> = [1]; say values.pop(); }''', 'fixed pilot cannot be modified'),
 'fixed_list_clear': ('''task main() { fixed pilot values: List<int> = [1]; values.clear(); }''', 'fixed pilot cannot be modified'),
 'fixed_list_reserve': ('''task main() { fixed pilot values: List<int> = [1]; values.reserve(8); }''', 'fixed pilot cannot be modified'),
 'when_integer_duplicate': ('''task main() { when 1 { 1 -> say "first"; 01 -> say "second"; }; }''', 'when arm duplicates'),
 'when_negative_zero': ('''task main() { when 0 { 0 -> say "first"; -0 -> say "second"; }; }''', 'when arm duplicates'),
 'when_bool_alias': ('''task main() { when true { true -> say "first"; HaI -> say "second"; }; }''', 'when arm duplicates'),
 'when_float_duplicate': ('''task main() { when 1.0 { 1.0 -> say "first"; 1.00 -> say "second"; }; }''', 'when arm duplicates'),
 'when_mixed_small_duplicate': ('''task main() { when 1 { 1 -> say "first"; 1.0 -> say "second"; }; }''', 'when arm duplicates'),
 'when_float_covers_int': ('''task main() { when 9223372036854775807 { 9223372036854775807.0 -> say "first"; 9223372036854775807 -> say "second"; }; }''', 'when arm duplicates'),
 'when_num_rounding_collision': ('''task main() { when 9223372036854775807.0 { 9223372036854775806 -> say "first"; 9223372036854775807 -> say "second"; }; }''', 'when arm duplicates'),
 'when_word_hex_alias': (r'''task main() { when "A" { "A" -> say "first"; "\x41" -> say "second"; }; }''', 'when arm duplicates'),
 'when_unicode_hex_alias': (r'''task main() { when "é" { "é" -> say "first"; "\xC3\xA9" -> say "second"; }; }''', 'when arm duplicates'),
 'when_raw_byte_hex_alias': (r'''task main() { when "\xFF" { "\xFF" -> say "first"; "\xff" -> say "second"; }; }''', 'when arm duplicates'),
 'when_escaped_brace_alias': (r'''task main() { when "\{x\}" { "\{x\}" -> say "first"; "\x7Bx\x7D" -> say "second"; }; }''', 'when arm duplicates'),
 'when_after_wildcard': ('''task main() { when 1 { _ -> say "first"; 1 -> say "second"; }; }''', "when arm is unreachable after '_'"),
 'when_repeated_wildcard': ('''task main() { when 1 { _ -> say "first"; _ -> say "second"; }; }''', "when arm is unreachable after '_'"),
}
# Both immutable spellings reject the same write forms in strict/default modes.
for name, (program, diagnostic) in tuple(NEGATIVE.items()):
 if name.startswith('fixed_'):
  NEGATIVE[name.replace('fixed_', 'grounded_', 1)] = (program.replace('fixed pilot', 'grounded pilot'), diagnostic.replace('fixed pilot', 'grounded pilot'))


def main() -> int:
 parser = argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--compiler', type=Path)
 parser.add_argument('--clang', default=os.environ.get('FREAK_CLANG') or shutil.which('clang'))
 parser.add_argument('--optimization', choices=('0','2','3'), default='2')
 parser.add_argument('--sanitize', action='store_true')
 args = parser.parse_args()
 assert args.clang
 repo = Path(__file__).resolve().parents[1]; runtime = repo / 'freakc/runtime'
 flags = ['-O'+args.optimization, '-g', '-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1', '-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1', '-I', str(runtime)]
 if args.sanitize: flags += ['-fsanitize=address,undefined', '-fno-omit-frame-pointer']
 link_flags = ['-lws2_32'] if sys.platform == 'win32' else ['-lm']
 with tempfile.TemporaryDirectory(prefix='freak-v35-literals-') as directory:
  root=Path(directory); compiler=args.compiler.resolve(strict=True) if args.compiler else build_stage2(clang=args.clang,repo=repo,root=root)
  for backend in ('c','llvm'):
   suffix='.c' if backend=='c' else '.ll'; objects=[]
   for unit in ('freak_runtime.c','freak_llvm_runtime.c'):
    if unit=='freak_llvm_runtime.c' and backend=='c': continue
    obj=root/f'{backend}_{unit}.o'; require_ok(run([args.clang,*flags,'-c',str(runtime/unit),'-o',str(obj)],root),'literal runtime'); objects.append(str(obj))
   for name,(program,expected) in POSITIVE.items():
    source=root/f'{name}_{backend}.fk';source.write_text(program+'\n')
    require_ok(run([str(compiler),str(source),'--'+backend,'--strict-borrow'],root),'literal emission '+name)
    binary=root/f'{name}_{backend}';require_ok(run([args.clang,*flags,str(source)+suffix,*objects,*link_flags,'-o',str(binary)],root),'literal link '+name)
    result=subprocess.run([str(binary)],cwd=root,env=sanitizer_env(),capture_output=True);assert result.returncode==0 and result.stdout==expected.encode() and not result.stderr,(backend,name,result)
   for strict in (False,True):
    for name,(program,diagnostic) in NEGATIVE.items():
     source=root/f'{name}_{backend}_{strict}.fk';source.write_text(program+'\n');artifact=Path(str(source)+suffix);artifact.write_text('stale artifact')
     command=[str(compiler),str(source),'--'+backend]
     if strict:command.append('--strict-borrow')
     result=run(command,root);assert result.returncode!=0 and diagnostic in result.stdout and not artifact.exists(),(backend,strict,name,result)
     if name=='unknown_escape':assert ':2:11' in result.stdout,result
   print(f'PASS {backend} O{args.optimization}: {len(POSITIVE)} native literal programs, {len(NEGATIVE)*2} strict/default rejection controls',flush=True)
 print(f'V3.5 literal contracts: PASS ({2*(len(POSITIVE)+2*len(NEGATIVE))} contracts)',flush=True)
 return 0

if __name__=='__main__':raise SystemExit(main())
