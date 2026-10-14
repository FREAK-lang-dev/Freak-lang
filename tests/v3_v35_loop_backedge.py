#!/usr/bin/env python3
"""Reject repeated-route moves while executing safe per-iteration owners."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import shutil
import sys
import tempfile
from v3_checked_parsing import build_stage2, run, sanitizer_env
from v3_v35_language import require_ok

POSITIVE = {
 'conditional_break_is_not_continuing_move': ('task main() { pilot bytes: ByteBuffer = ByteBuffer::new(); repeat 3 times { if true { bytes.release(); break; } say bytes.length(); } }',''),
 'nested_block_break_stops_walk': ('task main() { pilot bytes: ByteBuffer = ByteBuffer::new(); repeat 3 times { { bytes.release(); break; } say bytes.length(); } }',''),
 'return_route_keeps_zero_iteration_owner': ('task main() { pilot bytes: ByteBuffer = ByteBuffer::new(); repeat 0 times { bytes.release(); give back; } say bytes.length(); bytes.release(); }','0\n'),
 'fresh_local_each_iteration': ('task main() { repeat 3 times { pilot bytes: ByteBuffer = ByteBuffer::new(); say bytes.length(); bytes.release(); } }','0\n0\n0\n'),
 'outer_reinitialize_at_end': ('task main() { pilot mut bytes: ByteBuffer = ByteBuffer::new(); repeat 3 times { say bytes.length(); bytes.release(); bytes = ByteBuffer::new(); } bytes.release(); }','0\n0\n0\n'),
 'outer_reinitialize_at_start': ('task main() { pilot mut bytes: ByteBuffer = ByteBuffer::new(); bytes.release(); repeat 3 times { bytes = ByteBuffer::new(); say bytes.length(); bytes.release(); } }','0\n0\n0\n'),
 'continue_after_reinitialize': ('task main() { pilot mut bytes: ByteBuffer = ByteBuffer::new(); repeat 3 times with i { say bytes.length(); bytes.release(); bytes = ByteBuffer::new(); if i == 1 { continue; } } bytes.release(); }','0\n0\n0\n'),
 'break_has_no_next_iteration': ('task main() { pilot bytes: ByteBuffer = ByteBuffer::new(); repeat 3 times { say bytes.length(); bytes.release(); break; } }','0\n'),
 'one_iteration_continue': ('task main() { pilot bytes: ByteBuffer = ByteBuffer::new(); repeat 1 times { say bytes.length(); bytes.release(); continue; } }','0\n'),
 'for_continue_after_reinitialize': ('task main() { pilot mut bytes: ByteBuffer = ByteBuffer::new(); for (pilot i = 0; i < 3; i += 1) { say bytes.length(); bytes.release(); bytes = ByteBuffer::new(); if i == 1 { continue; } } bytes.release(); }','0\n0\n0\n'),
 'while_borrows_live_condition': ('task main() { pilot mut bytes: ByteBuffer = ByteBuffer::new(); pilot mut count = 0; while bytes.length() == 0 and count < 2 { say bytes.length(); bytes.release(); bytes = ByteBuffer::new(); count += 1; } bytes.release(); }','0\n0\n'),
 'condition_consumes_then_body_restores': ('task test(bytes: ByteBuffer) -> bool { bytes.release(); give back true; } task main() { pilot mut bytes: ByteBuffer = ByteBuffer::new(); pilot mut count = 0; while test(bytes) { bytes = ByteBuffer::new(); count += 1; if count == 2 { bytes.release(); break; } } say count; }','2\n'),
 'single_training_condition_consumes': ('task test(bytes: ByteBuffer) -> bool { bytes.release(); give back false; } task main() { pilot bytes: ByteBuffer = ByteBuffer::new(); training arc until test(bytes) max 1 sessions { say 1; } }','1\n'),
 'word_clone_each_iteration': ('task take(text: word) { say text; } task main() { pilot text = "stable" + " owner"; repeat 3 times { take(text + ""); } say text; }','stable owner\nstable owner\nstable owner\nstable owner\n'),
 'nested_reinitialized_routes': ('task main() { pilot mut bytes: ByteBuffer = ByteBuffer::new(); repeat 2 times { repeat 2 times { say bytes.length(); bytes.release(); bytes = ByteBuffer::new(); } } bytes.release(); }','0\n0\n0\n0\n'),
 'when_continue_reinitialized': ('task main() { pilot mut bytes: ByteBuffer = ByteBuffer::new(); repeat 3 times with i { bytes.release(); bytes = ByteBuffer::new(); when i { 1 -> continue; _ -> say bytes.length(); }; } bytes.release(); }','0\n0\n'),
}
NEGATIVE = {
 'outer_next_iteration_after_single_inner': 'task main() { pilot bytes: ByteBuffer = ByteBuffer::new(); repeat 2 times { repeat 1 times { say bytes.length(); bytes.release(); } } }',
 'repeat_next_iteration_reads_released': 'task main() { pilot bytes: ByteBuffer = ByteBuffer::new(); repeat 2 times { say bytes.length(); bytes.release(); } }',
 'continue_next_iteration_reads_released': 'task main() { pilot bytes: ByteBuffer = ByteBuffer::new(); repeat 2 times { say bytes.length(); bytes.release(); continue; } }',
 'while_next_iteration_reads_released': 'task main() { pilot bytes: ByteBuffer = ByteBuffer::new(); pilot mut count = 0; while count < 2 { say bytes.length(); bytes.release(); count += 1; } }',
 'range_next_iteration_reads_released': 'task main() { pilot bytes: ByteBuffer = ByteBuffer::new(); for each i in 0..2 { say bytes.length(); bytes.release(); } }',
 'for_next_iteration_reads_released': 'task main() { pilot bytes: ByteBuffer = ByteBuffer::new(); for (pilot i = 0; i < 2; i += 1) { say bytes.length(); bytes.release(); } }',
 'foreach_next_iteration_reads_released': 'task main() { pilot bytes: ByteBuffer = ByteBuffer::new(); pilot values: List<int> = [1, 2]; for each i in values { say bytes.length(); bytes.release(); } }',
 'training_next_iteration_reads_released': 'task main() { pilot bytes: ByteBuffer = ByteBuffer::new(); training arc until false max 2 sessions { say bytes.length(); bytes.release(); } }',
 'nested_next_iteration_reads_released': 'task main() { pilot bytes: ByteBuffer = ByteBuffer::new(); repeat 2 times { repeat 2 times { say bytes.length(); bytes.release(); } } }',
 'word_next_iteration_consumes': 'task take(text: word) {} task main() { pilot text = "owner" + " word"; repeat 2 times { take(text); } }',
 'condition_next_iteration_consumes': 'task test(bytes: ByteBuffer) -> bool { bytes.release(); give back true; } task main() { pilot bytes: ByteBuffer = ByteBuffer::new(); while test(bytes) { say 1; } }',
 'condition_next_iteration_reads': 'task main() { pilot bytes: ByteBuffer = ByteBuffer::new(); while bytes.length() == 0 { bytes.release(); } }',
 'training_condition_next_iteration_consumes': 'task test(bytes: ByteBuffer) -> bool { bytes.release(); give back false; } task main() { pilot bytes: ByteBuffer = ByteBuffer::new(); training arc until test(bytes) max 2 sessions { say 1; } }',
 'foreach_collection_next_iteration': 'task take(values: List<int>) {} task main() { pilot values: List<int> = [1, 2]; for each i in values { take(values); } }',
 'when_continue_skips_reinitialize': 'task main() { pilot mut bytes: ByteBuffer = ByteBuffer::new(); repeat 3 times with i { say bytes.length(); bytes.release(); when i { 1 -> continue; _ -> { bytes = ByteBuffer::new(); } }; } }',
}


def main() -> int:
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--compiler',type=Path)
 parser.add_argument('--clang',default=os.environ.get('FREAK_CLANG') or shutil.which('clang'))
 args=parser.parse_args();assert args.clang
 repo=Path(__file__).resolve().parents[1];runtime=repo/'freakc/runtime'
 flags=['-O2','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1','-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1','-I',str(runtime)]
 links=['-lws2_32'] if sys.platform=='win32' else ['-lm']
 with tempfile.TemporaryDirectory(prefix='freak-v35-loop-backedge-') as directory:
  root=Path(directory);compiler=args.compiler.resolve(strict=True) if args.compiler else build_stage2(clang=args.clang,repo=repo,root=root)
  for backend in ('c','llvm'):
   suffix='.c' if backend=='c' else '.ll';objects=[]
   for unit in ('freak_runtime.c','freak_llvm_runtime.c'):
    if unit=='freak_llvm_runtime.c' and backend=='c':continue
    obj=root/f'{backend}_{unit}.o';require_ok(run([args.clang,*flags,'-c',str(runtime/unit),'-o',str(obj)],root),'backedge runtime');objects.append(str(obj))
   for name,(program,expected) in POSITIVE.items():
    source=root/f'{name}_{backend}.fk';source.write_text(program+'\n')
    require_ok(run([str(compiler),str(source),'--'+backend,'--strict-borrow'],root),'backedge positive '+name)
    binary=root/f'{name}_{backend}';require_ok(run([args.clang,*flags,str(source)+suffix,*objects,*links,'-o',str(binary)],root),'backedge link '+name)
    result=run([str(binary)],root,env=sanitizer_env());assert result.returncode==0 and result.stdout==expected and not result.stderr,(backend,name,result)
   for name,program in NEGATIVE.items():
    source=root/f'{name}_{backend}.fk';source.write_text(program+'\n');artifact=Path(str(source)+suffix);artifact.write_text('stale')
    result=run([str(compiler),str(source),'--'+backend,'--strict-borrow'],root)
    assert result.returncode!=0 and 'no longer belongs' in result.stdout and not artifact.exists(),(backend,name,result)
   print(f'PASS {backend}: {len(POSITIVE)} safe repeated-route owners, {len(NEGATIVE)} later-iteration move controls',flush=True)
 print(f'V3.5 loop repeated-route ownership: PASS ({2*(len(POSITIVE)+len(NEGATIVE))} contracts)',flush=True)
 return 0

if __name__=='__main__':raise SystemExit(main())
