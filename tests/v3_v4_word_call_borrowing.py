#!/usr/bin/env python3
"""Measure real heap-word copies and execute conservative C call ownership.

The linker's clone wrapper counts actual copied bytes, so the hot-reader test
detects a compiler that merely hides emitted clone text. ASan/UBSan and the
runtime owner audit verify borrowed inputs, independent results and rejected
escape/effect cases. An optional baseline compiler proves the same observable
semantics with the original owning path and its higher hot-reader copy count.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

from v3_checked_parsing import build_stage2, run, sanitizer_env
from v3_v35_language import require_ok

PREAMBLE = '''extern task v4_word_copy_reset() -> void
extern task v4_word_copy_calls() -> int
extern task v4_word_copy_bytes() -> int
extern task v4_word_opaque(text: word) -> int
'''
BYTE = '''task byte(text: word, pos: int) -> word {
    if pos < 0 { give back ""; }
    if pos >= text.length() { give back ""; }
    give back text.char_at(pos);
}
'''
WRAPPER = '''#include "freak_runtime.h"
static int64_t calls, copied;
freak_word __real_freak_word_clone(freak_word source);
freak_word __wrap_freak_word_clone(freak_word source) {
    if (source.heap && source.data) { calls++; copied += source.length; }
    return __real_freak_word_clone(source);
}
void v4_word_copy_reset(void) { calls = copied = 0; }
int64_t v4_word_copy_calls(void) { return calls; }
int64_t v4_word_copy_bytes(void) { return copied; }
int64_t v4_word_opaque(freak_word text) { return text.length; }
'''

# Final two stdout lines are measured clone calls and bytes. Word owners are
# retained/replaced after the call so a borrowed escape or early free is used.
CASES = {
    'deep_ast_fallback': ('task read(text: word) -> int {' + ' if true {' * 100 +
        ' give back text.length();' + ' }' * 100 + ' give back 0; }\n' + '''
    task main() { pilot owner = "original" + " owner"; v4_word_copy_reset();
        say read(owner); say owner; say v4_word_copy_calls(); say v4_word_copy_bytes(); }
    ''', '14\noriginal owner\n', 'retain'),
    'empty_heap_concat_result': ('''task append(text: word) -> word {
        give back text + ""; }
    task main() { pilot owner = "" + ""; v4_word_copy_reset();
        pilot kept = append(owner); owner = "new" + " owner";
        say kept.length(); say owner;
        say v4_word_copy_calls(); say v4_word_copy_bytes(); }
    ''', '0\nnew owner\n', 'elide_empty'),
    'pure_multihop_word_result': ('''task leaf(text: word) -> word {
        give back text + " suffix"; }
    task middle(text: word) -> word { give back leaf(text); }
    task outer(text: word) -> word { give back middle(text); }
    task main() { pilot owner = "original" + " owner"; v4_word_copy_reset();
        pilot kept = outer(owner); owner = "new" + " owner";
        say kept; say owner;
        say v4_word_copy_calls(); say v4_word_copy_bytes(); }
    ''', 'original owner suffix\nnew owner\n', 'elide'),
    'same_word_multiple_arguments': ('''task both(first: word, second: word) -> int {
        give back first.length() + second.length(); }
    task main() { pilot owner = "original" + " owner"; v4_word_copy_reset();
        say both(owner, owner); owner += " changed"; say owner;
        say v4_word_copy_calls(); say v4_word_copy_bytes(); }
    ''', '28\noriginal owner changed\n', 'elide'),
    'primitive_local_rebinding': ('''task read(text: word, n: int) -> int {
        pilot amount = n; amount += 1;
        pilot decimal: num = 1.5; decimal = decimal + 1.0;
        pilot enabled = false; enabled = true;
        if enabled and decimal == 2.5 { give back text.length() + amount; }
        give back 0; }
    task main() { pilot owner = "original" + " owner"; v4_word_copy_reset();
        say read(owner, 4); say owner;
        say v4_word_copy_calls(); say v4_word_copy_bytes(); }
    ''', '19\noriginal owner\n', 'elide'),
    'hot_nested_reader': (BYTE + '''task count(text: word) -> int {
        pilot index = 0; pilot total = 0;
        repeat until index >= text.length() {
            if byte(text, index) == "x" { total += 1; }
            index += 1;
        }
        give back total;
    }
    task main() { pilot owner = "x".repeated(4096); v4_word_copy_reset();
        say count(owner); say owner.length();
        say v4_word_copy_calls(); say v4_word_copy_bytes(); }
    ''', '4096\n4096\n', 'elide'),
    'stable_byte_result': (BYTE + '''task main() {
        pilot owner = "original" + " owner"; v4_word_copy_reset();
        pilot kept = byte(owner, 1); owner = "replacement" + " owner";
        say kept; say owner; say v4_word_copy_calls(); say v4_word_copy_bytes(); }
    ''', 'r\nreplacement owner\n', 'elide'),
    'independent_concat_result': ('''task append(text: word) -> word {
        if text.length() == 0 { give back "empty"; }
        give back text + " suffix";
    }
    task main() { pilot owner = "original" + " owner"; v4_word_copy_reset();
        pilot kept = append(owner); owner = "new" + " owner";
        say kept; say owner; say v4_word_copy_calls(); say v4_word_copy_bytes(); }
    ''', 'original owner suffix\nnew owner\n', 'elide'),
    'nonliteral_temporary': (BYTE + '''task main() { v4_word_copy_reset();
        say byte("heap" + " temporary", 1);
        say v4_word_copy_calls(); say v4_word_copy_bytes(); }
    ''', 'e\n', 'unconstrained'),
    'sized_nul_byte': (BYTE + '''task main() {
        pilot owner = "left" + char_to_word(0) + "right"; v4_word_copy_reset();
        pilot kept = byte(owner, 4); owner = "new" + " owner";
        say kept.length(); say kept == char_to_word(0);
        say v4_word_copy_calls(); say v4_word_copy_bytes(); }
    ''', '1\ntrue\n', 'elide'),
    'direct_return': ('''task identity(text: word) -> word { give back text; }
    task main() { pilot owner = "original" + " owner"; v4_word_copy_reset();
        pilot kept = identity(owner); owner = "new" + " owner";
        say kept; say owner; say v4_word_copy_calls(); say v4_word_copy_bytes(); }
    ''', 'original owner\nnew owner\n', 'retain'),
    'aliased_return': ('''task identity(text: word) -> word {
        pilot alias = text; give back alias; }
    task main() { pilot owner = "original" + " owner"; v4_word_copy_reset();
        pilot kept = identity(owner); owner = "new" + " owner";
        say kept; say v4_word_copy_calls(); say v4_word_copy_bytes(); }
    ''', 'original owner\n', 'retain'),
    'empty_replace_escape': ('''task identity(text: word) -> word {
        give back text.replace("", "ignored"); }
    task main() { pilot owner = "original" + " owner"; v4_word_copy_reset();
        pilot kept = identity(owner); owner = "new" + " owner";
        say kept; say v4_word_copy_calls(); say v4_word_copy_bytes(); }
    ''', 'original owner\n', 'retain'),
    'transitive_escape': ('''task inner(text: word) -> word { give back text; }
    task outer(text: word) -> word { give back inner(text); }
    task main() { pilot owner = "original" + " owner"; v4_word_copy_reset();
        pilot kept = outer(owner); owner = "new" + " owner";
        say kept; say v4_word_copy_calls(); say v4_word_copy_bytes(); }
    ''', 'original owner\n', 'retain'),
    'parameter_rebinding': ('''task change(text: word, enabled: bool) -> word {
        if enabled { text += " changed"; give back text; }
        give back text;
    }
    task main() { pilot owner = "original" + " owner"; v4_word_copy_reset();
        say change(owner, true); say change(owner, false); say owner;
        say v4_word_copy_calls(); say v4_word_copy_bytes(); }
    ''', 'original owner changed\noriginal owner\noriginal owner\n', 'retain'),
    'parameter_shadow': ('''task read(text: word) -> int {
        { pilot text = text + " extra"; give back text.length(); }
        give back text.length(); }
    task main() { pilot owner = "original" + " owner"; v4_word_copy_reset();
        say read(owner); say owner; say v4_word_copy_calls(); say v4_word_copy_bytes(); }
    ''', '20\noriginal owner\n', 'retain'),
    'global_store': ('''pilot saved = "initial" + " owner"
    task save(text: word) -> int { saved = text; give back text.length(); }
    task main() { pilot owner = "original" + " owner"; v4_word_copy_reset();
        say save(owner); owner = "new" + " owner"; say saved;
        say v4_word_copy_calls(); say v4_word_copy_bytes(); }
    ''', '14\noriginal owner\n', 'retain'),
    'later_argument_mutation': (BYTE + '''pilot global_word = "OLD" + " owner"
    task replace_global() -> int { global_word = "NEW" + " owner"; give back 0; }
    task main() { v4_word_copy_reset(); say byte(global_word, replace_global());
        say global_word; say v4_word_copy_calls(); say v4_word_copy_bytes(); }
    ''', 'O\nNEW owner\n', 'retain'),
    'later_argument_effect_on_local': (BYTE + '''pilot counter = 0
    task effect() -> int { counter += 1; give back 0; }
    task main() { pilot owner = "OLD" + " owner"; v4_word_copy_reset();
        say byte(owner, effect()); say counter; say owner;
        say v4_word_copy_calls(); say v4_word_copy_bytes(); }
    ''', 'O\n1\nOLD owner\n', 'retain'),
    'unknown_extern': ('''task read(text: word) -> int { give back v4_word_opaque(text); }
    task main() { pilot owner = "original" + " owner"; v4_word_copy_reset();
        say read(owner); say owner; say v4_word_copy_calls(); say v4_word_copy_bytes(); }
    ''', '14\noriginal owner\n', 'retain'),
    'recursive': ('''task read(text: word, n: int) -> int {
        if n == 0 { give back text.length(); }
        give back read(text, n - 1); }
    task main() { pilot owner = "original" + " owner"; v4_word_copy_reset();
        say read(owner, 5); say owner; say v4_word_copy_calls(); say v4_word_copy_bytes(); }
    ''', '14\noriginal owner\n', 'retain'),
    'mutually_recursive': ('''task first(text: word, n: int) -> int {
        if n == 0 { give back text.length(); } give back second(text, n - 1); }
    task second(text: word, n: int) -> int {
        if n == 0 { give back text.length(); } give back first(text, n - 1); }
    task main() { pilot owner = "original" + " owner"; v4_word_copy_reset();
        say first(owner, 5); say owner; say v4_word_copy_calls(); say v4_word_copy_bytes(); }
    ''', '14\noriginal owner\n', 'retain'),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', type=Path)
    parser.add_argument('--baseline-compiler', type=Path)
    parser.add_argument('--clang', default=os.environ.get('FREAK_CLANG') or shutil.which('clang'))
    parser.add_argument('--sanitize', action='store_true')
    parser.add_argument('--optimization', choices=('O0', 'O2', 'O3'), default='O2')
    parser.add_argument('--case', choices=tuple(CASES))
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    assert sys.platform.startswith('linux'), 'copy-byte oracle requires GNU linker --wrap'
    assert args.clang, 'Clang required'
    repo = Path(__file__).resolve().parents[1]
    runtime = repo / 'freakc/runtime'
    flags = ['-' + args.optimization, '-g', '-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1',
             '-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1', '-I', str(runtime)]
    if args.sanitize:
        flags += ['-fsanitize=address,undefined', '-fno-omit-frame-pointer']
    records = []
    with tempfile.TemporaryDirectory(prefix='freak-word-calls-') as temporary:
        root = Path(temporary)
        compiler = args.compiler.resolve(strict=True) if args.compiler else build_stage2(clang=args.clang, repo=repo, root=root)
        wrapper = root / 'clone_oracle.c'
        wrapper.write_text(WRAPPER)
        objects = []
        for source in (runtime / 'freak_runtime.c', wrapper):
            obj = root / (source.stem + '.o')
            require_ok(run([args.clang, *flags, '-c', str(source), '-o', str(obj)], root), 'word-call runtime')
            objects.append(str(obj))
        compilers = [('optimized', compiler)]
        if args.baseline_compiler:
            compilers.append(('baseline', args.baseline_compiler.resolve(strict=True)))
        for label, selected in compilers:
            for name, (program, expected, policy) in CASES.items():
                if args.case and name != args.case:
                    continue
                source = root / f'{label}_{name}.fk'
                source.write_text(PREAMBLE + program + '\n')
                require_ok(run([str(selected), str(source), '--c'], root), 'word-call emit ' + name)
                binary = root / f'{label}_{name}'
                require_ok(run([args.clang, *flags, str(source) + '.c', *objects,
                                '-Wl,--wrap=freak_word_clone', '-lm', '-o', str(binary)], root), 'word-call link ' + name)
                result = run([str(binary)], root, env=sanitizer_env())
                require_ok(result, 'word-call execute ' + name)
                lines = result.stdout.splitlines(keepends=True)
                assert ''.join(lines[:-2]) == expected and not result.stderr, (label, name, result)
                calls, copied = map(int, lines[-2:])
                if policy == 'retain' or (policy.startswith('elide') and label == 'baseline'):
                    assert calls > 0 and copied >= 0, (label, name, calls, copied)
                    if policy != 'elide_empty':
                        assert copied > 0, (label, name, calls, copied)
                elif policy.startswith('elide'):
                    assert calls == 0 and copied == 0, (label, name, calls, copied)
                records.append({'compiler': label, 'case': name, 'policy': policy,
                                'calls': calls, 'copied_bytes': copied,
                                'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                                'generated_c_sha256': hashlib.sha256(Path(str(source) + '.c').read_bytes()).hexdigest(),
                                'stdout': result.stdout, 'stderr': result.stderr, 'returncode': result.returncode})
                print('PASS', label, name, 'heap-clones', calls, 'copied-bytes', copied, flush=True)
    expected_count = (1 if args.case else len(CASES)) * (2 if args.baseline_compiler else 1)
    assert len(records) == expected_count
    report = {'status': 'pass', 'optimization': args.optimization, 'sanitizers': args.sanitize,
              'runtime_sha256': hashlib.sha256((runtime / 'freak_runtime.c').read_bytes()).hexdigest(),
              'cases': records}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    print('PASS native word-call ownership/copy-byte cases', len(records), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
