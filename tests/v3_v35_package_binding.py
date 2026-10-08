#!/usr/bin/env python3
"""Native package binding component gate; full CLI/source-store gates run separately.

The probe compiles production lexer/parser/checker/emitters, TOML/graph and binder
with a supplied, reconstructed native stage2. Its test-only adapter snapshots
declared local source bytes into native arrays before binding. It does not claim
source-store, Git/cache/lock or public CLI integration verification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


ADAPTER = r'''
pilot package_source_roots = 0
pilot package_source_original_roots = 0
pilot probe_source_nodes = 0
pilot probe_source_paths = 0
pilot probe_source_text = 0
pilot package_input_paths = 0
pilot package_input_nodes = 0
pilot package_input_roles = 0
task package_join_host(root: word, relative: word) -> word {
    give back root + "/" + relative
}
task package_read_graph_source(node: int, relative: word) -> word {
    pilot i = 0
    repeat until i >= array_len(probe_source_nodes) {
        if word_to_int(array_get(probe_source_nodes, i)) == node and array_get(probe_source_paths, i) == relative { give back array_get(probe_source_text, i) }
        i += 1
    }
    hangar_graph_fail("probe rejects undeclared source '" + relative + "'")
    give back ""
}
task probe_canonical(path: word) -> word {
    pilot probe_result = fs::canonical_path(path)
    if not fs::result_ok(probe_result) { say fs::result_error(probe_result) fs::result_release(probe_result) process::exit(80) }
    pilot value = fs::result_word(probe_result) fs::result_release(probe_result) give back value
}
task probe_add(root: word) -> int {
    pilot canonical = probe_canonical(root)
    pilot manifest = fs::read(canonical + "/hangar.toml")
    if not toml_parse(manifest) { say toml_error process::exit(81) }
    pilot material: ByteBuffer = ByteBuffer::new()
    material.write_word(manifest)
    pilot i = 0
    repeat until i >= toml_count {
        pilot key = array_get(toml_keys_arr, i)
        if key == "project.entry" or key.starts_with("modules.") or key.starts_with("tests.") {
            pilot relative = array_get(toml_vals_arr, i)
            material.write_word(relative) material.write_word(fs::read(canonical + "/" + relative))
        }
        i += 1
    }
    pilot identity = fs::sha256_bytes(material) material.release()
    pilot existing = hangar_graph_find_identity(identity)
    if existing >= 0 { give back existing }
    pilot node = hangar_graph_add_manifest(identity, canonical + "/hangar.toml", manifest, canonical)
    if node < 0 { say hangar_graph_error process::exit(82) }
    array_push(package_source_roots, canonical) array_push(package_source_original_roots, canonical)
    i = 0
    repeat until i >= array_len(hangar_graph_fact_keys) {
        if word_to_int(array_get(hangar_graph_fact_nodes, i)) == node {
            pilot key = array_get(hangar_graph_fact_keys, i)
            if key == "project.entry" or key.starts_with("modules.") or key.starts_with("tests.") {
                pilot relative = array_get(hangar_graph_fact_values, i)
                array_push(probe_source_nodes, word_from_int(node)) array_push(probe_source_paths, relative)
                array_push(probe_source_text, fs::read(canonical + "/" + relative))
            }
        }
        i += 1
    }
    give back node
}
task probe_prepare(root: word) -> void {
    hangar_graph_clear()
    package_source_roots = array_new() package_source_original_roots = array_new()
    probe_source_nodes = array_new() probe_source_paths = array_new() probe_source_text = array_new()
    package_input_paths = array_new() package_input_nodes = array_new() package_input_roles = array_new()
    probe_add(root)
    pilot edge = 0
    repeat until edge >= hangar_graph_edge_count {
        pilot parent = word_to_int(array_get(hangar_graph_edge_parents, edge))
        pilot root_path = array_get(package_source_original_roots, parent)
        pilot target = probe_add(root_path + "/" + array_get(hangar_graph_edge_sources, edge))
        if not hangar_graph_link(edge, target) { say hangar_graph_error process::exit(83) }
        edge += 1
    }
    if not hangar_graph_complete(0) { say hangar_graph_error process::exit(84) }
}
task probe_append(current: word, path: word) -> word {
    pilot source = fs::read(path)
    source_map_register(path, source)
    give back current + source + "\n"
}
task cli_load_std(source: word, target: word) -> word {
    pilot root = process::env("FREAK_BINDING_TEST_STD")
    pilot probe_result = ""
    if target == "llvm" {
        trusted_internal_runtime_source_file = root + "/runtime.fk"
        probe_result = probe_append(probe_result, root + "/runtime.fk")
    }
    probe_result = probe_append(probe_result, root + "/math.fk")
    probe_result = probe_append(probe_result, root + "/string.fk")
    probe_result = probe_append(probe_result, root + "/convert.fk")
    probe_result = probe_append(probe_result, root + "/algorithm.fk")
    probe_result = probe_append(probe_result, root + "/version.fk")
    give back probe_result
}
task main() -> void {
    init_arrays()
    if process::arg(5) != "" and not v35_set_bootstrap_compat(process::arg(5)) { process::exit(80) }
    pilot root = process::arg(1)
    if root != "standalone" { probe_prepare(root) } else { hangar_graph_clear() }
    input_file = process::arg(2)
    emit_target = process::arg(3)
    pilot source = cli_load_project_source(input_file, fs::read(input_file), emit_target)
    if cli_project_source_error != "" { say cli_project_source_error process::exit(85) }
    init_arrays()
    next_expr_id = 0 next_stmt_id = 0 shape_registry_count = 0
    tokenize(source)
    if not cli_project_bind_tokens() { process::exit(86) }
    parse_program()
    if error_count > 0 { process::exit(87) }
    if not cli_project_bind_ast() { process::exit(88) }
    check_program()
    if error_count > 0 { process::exit(89) }
    out_file = process::arg(4)
    if emit_target == "c" { fs::write(out_file, "") emit_c_program() }
    else { emit_llvm_program() }
    say "BINDING_OK units=" + word_from_int(array_len(pb_order))
    say "BINDING_SOURCE_SHA=" + PROBE_BINDING_SHA
    cli_project_binding_release()
}
'''


def run(command: list[str], *, cwd: Path, env: dict[str, str], timeout: int = 180) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(command, cwd=cwd, env=env, capture_output=True, timeout=timeout, check=False)


def task(source: str, name: str) -> str:
    start = source.index(f'task {name}(')
    end = source.find('\ntask ', start + 1)
    return source[start:end if end >= 0 else None]


def probe_source(repo: Path) -> str:
    files = [repo / 'src/compiler/v3' / f'{name}.fk' for name in
             ('globals', 'helpers', 'lexer', 'parser', 'checker', 'emit_c', 'emit_llvm')]
    text = '\n'.join(p.read_text() for p in files)
    text += '\n' + (repo / 'std/version.fk').read_text()
    text += '\n' + (repo / 'src/cli/toml.fk').read_text()
    text += '\n' + task((repo / 'src/cli/hangar.fk').read_text(), 'hangar_valid_package_name')
    text += '\n' + (repo / 'src/cli/package_graph.fk').read_text()
    text += '\n' + (repo / 'src/cli/package_binding.fk').read_text()
    digest = hashlib.sha256((repo / 'src/cli/package_binding.fk').read_bytes()).hexdigest()
    return text + '\npilot PROBE_BINDING_SHA = ' + json.dumps(digest) + '\n' + ADAPTER


def write_project(root: Path, name: str, sources: dict[str, str], *, entry: str = '',
                  modules: dict[str, str] | None = None, exports: dict[str, str] | None = None,
                  dependencies: dict[str, str] | None = None) -> None:
    root.mkdir(parents=True, exist_ok=True)
    manifest = f'[project]\nname = {json.dumps(name)}\nversion = "1.0.0"\nkind = "{"app" if entry else "lib"}"\n'
    if entry:
        manifest += f'entry = {json.dumps(entry)}\n'
    for section, facts in [('modules', modules), ('exports', exports)]:
        if facts:
            manifest += f'[{section}]\n' + ''.join(f'{key} = {json.dumps(value)}\n' for key, value in facts.items())
    if dependencies:
        manifest += '[dependencies]\n' + ''.join(f'{key} = {{ path = {json.dumps(value)} }}\n' for key, value in dependencies.items())
    (root / 'hangar.toml').write_text(manifest)
    for relative, source in sources.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)


def fixture(root: Path) -> tuple[Path, str]:
    write_project(root / 'base', 'base', {'src/core.fk': 'fixed pilot seed: int = 3\ntask helper() -> int { give back seed }\ntask api() -> int { give back helper() }\n'},
                  modules={'core': 'src/core.fk'}, exports={'api': 'core::api'})
    left = '''use base::{api as base_api}
fixed pilot seed: int = 11
shape Point { value: int }
impl Point { task read(self) -> int { give back self.value } }
task helper() -> int { give back seed + base_api() }
task api() -> int { pilot p: Point = Point { value: helper() } give back p.read() }
task make() -> Point { give back Point { value: seed } }
'''
    right = '''use base::{api as base_api}
fixed pilot seed: int = 21
shape Point { title: word, value: int }
impl Point { task read(self) -> int { give back self.value } }
task helper() -> int { give back seed + base_api() }
task api() -> int { pilot p = Point { title: "right", value: helper() } give back p.read() }
task make() -> Point { give back Point { title: "right", value: seed } }
'''
    for name, source in [('left', left), ('right', right)]:
        write_project(root / name, name, {'src/core.fk': source}, modules={'core': 'src/core.fk'},
                      exports={'api': 'core::api', 'Point': 'core::Point', 'make': 'core::make', 'seed': 'core::seed'},
                      dependencies={'base': '../base'})
    app = '''-- use rogue::{helper}, Point seed strings must stay untouched.
use left::{api as left_api, Point as LeftPoint, seed as left_seed}
use right as rhs
use self::extra::{extra}
fixed pilot helper: int = 100
task local(helper: int) -> int { pilot mut value: int = helper { pilot helper = 7 value += helper } give back value + helper }
task main() {
    pilot left: LeftPoint = LeftPoint { value: left_seed }
    pilot right = rhs::make()
    say left_api() + rhs::api() + extra()
    say "literal helper seed Point use ghost::\\{x, y\\}"
    say "bound={helper}, left={left.value}, right={right.title}"
    say local(5)
    pilot mut value = 0
    for (pilot helper = 0; helper < 2; helper += 1) { value += helper }
    repeat 2 times with helper { value += helper }
    for each helper in 1..3 { value += helper }
    say value
    check result fs::read_checked("missing-binding-fixture.txt") {
        ok(helper) -> { say helper }
        err(helper) -> { say "handled" }
    }
    say helper
}
'''
    write_project(root / 'app', 'consumer', {'src/main.fk': app, 'src/extra.fk': 'task extra() -> int { give back 2 }\n',
                  'src/unused.fk': 'THIS UNUSED SOURCE MUST NOT PARSE\n'}, entry='src/main.fk',
                  modules={'extra': 'src/extra.fk', 'unused': 'src/unused.fk'},
                  dependencies={'left': '../left', 'right': '../right'})
    return root / 'app', '40\nliteral helper seed Point use ghost::{x, y}\nbound=100, left=11, right=right\n17\n5\nhandled\n100\n'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--compiler', type=Path, required=True)
    parser.add_argument('--clang', required=True)
    parser.add_argument('--probe', type=Path)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--keep', type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    temporary = tempfile.TemporaryDirectory(prefix='v35-package-binding-') if not args.keep else None
    work = args.keep.resolve() if args.keep else Path(temporary.name)
    work.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env['FREAK_BINDING_TEST_STD'] = str(repo / 'std')
    runtime = repo / 'freakc/runtime'
    records: list[dict] = []
    probe = args.probe.resolve() if args.probe else work / 'binding_probe'
    if not args.probe:
        source = work / 'binding_probe.fk'
        source.write_text(probe_source(repo))
        result = run([str(args.compiler.resolve()), str(source), '--c'], cwd=work, env=env)
        (work / 'probe-compile.log').write_bytes(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(f'native probe source did not compile: {work / "probe-compile.log"}')
        result = run([args.clang, '-O0', '-I', str(runtime), str(source) + '.c',
                      str(runtime / 'freak_runtime.c'), str(runtime / 'freak_llvm_runtime.c'), '-lm', '-o', str(probe)],
                     cwd=work, env=env)
        (work / 'probe-link.log').write_bytes(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(f'native probe link failed: {work / "probe-link.log"}')
    unrelated = work / 'unrelated-cwd'
    unrelated.mkdir(exist_ok=True)
    app, expected = fixture(work / 'positive')
    for backend in ('c', 'llvm'):
        generated = work / f'consumer.{"c" if backend == "c" else "ll"}'
        result = run([str(probe), str(app), str(app / 'src/main.fk'), backend, str(generated)], cwd=unrelated, env=env)
        (work / f'bind-{backend}.log').write_bytes(result.stdout + result.stderr)
        binding_digest = hashlib.sha256((repo / 'src/cli/package_binding.fk').read_bytes()).hexdigest()
        expected_digest = f'BINDING_SOURCE_SHA={binding_digest}'.encode()
        if result.returncode or b'BINDING_OK units=5' not in result.stdout or expected_digest not in result.stdout:
            raise RuntimeError(f'{backend} positive binding/diamond failed: {work / f"bind-{backend}.log"}')
        for opt in (0, 2, 3):
            binary = work / f'consumer-{backend}-O{opt}'
            command = [args.clang, f'-O{opt}', '-I', str(runtime), str(generated),
                       str(runtime / 'freak_runtime.c'), str(runtime / 'freak_llvm_runtime.c'), '-lm', '-o', str(binary)]
            linked = run(command, cwd=unrelated, env=env)
            (work / f'link-{backend}-O{opt}.log').write_bytes(linked.stdout + linked.stderr)
            if linked.returncode:
                raise RuntimeError(f'{backend} O{opt} failed to link')
            executed = run([str(binary)], cwd=unrelated, env=env)
            if executed.returncode or executed.stdout.decode() != expected:
                raise RuntimeError(f'{backend} O{opt} unexpected output {executed.stdout!r}, expected {expected!r}')
            records.append({'case': 'external-diamond-private-shapes-scope-interpolation', 'backend': backend,
                            'opt': opt, 'output': executed.stdout.decode(), 'generated_sha256': hashlib.sha256(generated.read_bytes()).hexdigest()})
    # Declaration kinds must drive value, call, type and impl-owner binding.
    # Type/value aliases may share spelling without weakening value collisions.
    namespace_cases = {
        'forward-shape-constructor': (
            'task make() -> Later { give back Later { value: 1 } }\n'
            'shape Later { value: int }\ntask main() { say make().value }\n', '1\n'),
        'ordinary-source-helper': (
            'shape pkg_' + '0' * 64 + '_math { value: int }\n'
            'task chr(value: int) -> int { give back value }\ntask main() { say chr(7) }\n', '7\n'),
        'bootstrap-source-helper': (
            'shape pkg_' + '0' * 64 + '_math { value: int }\n'
            'task chr(value: int) -> int { give back value }\ntask main() { say chr(7) }\n', '7\n'),
        'legacy-ordinary-global-and-call': (
            'pilot Shared: int = 7\ntask Shared() -> int { give back 8 }\n'
            'task main() { say Shared say Shared() }\n', '7\n8\n'),
        'fixed-global-and-impl-member': (
            'shape Shared { value: int }\n'
            'fixed pilot Shared_read: int = 19\n'
            'impl Shared { task read(self) -> int { give back self.value } }\n'
            'task main() { pilot item = Shared { value: 7 } say item.read() say Shared_read }\n', '7\n19\n'),
        'shape-and-task': (
            'shape Shared { value: int }\n'
            'impl Shared { task read(self) -> int { give back self.value } '
            'task make(value: int) -> Shared { give back Shared { value: value } } }\n'
            'task Shared() -> int { give back 8 }\n'
            'task main() { pilot item: Shared = Shared { value: 7 } '
            'say item.read() say Shared() say Shared::make(9).read() }\n', '7\n8\n9\n'),
        'shape-and-global': (
            'shape Shared { value: int }\nfixed pilot Shared: int = 11\n'
            'task main() { pilot item: Shared = Shared { value: Shared } say item.value say Shared }\n', '11\n11\n'),
        'import-type-and-call': (
            'use left::{Point as Shared, api as Shared}\n'
            'task main() { pilot item: Shared = Shared { value: 7 } say item.read() say Shared() }\n', '7\n14\n'),
        'import-type-and-local-call': (
            'use left::{Point as Shared}\ntask Shared() -> int { give back 8 }\n'
            'task main() { pilot item: Shared = Shared { value: 7 } say item.read() say Shared() }\n', '7\n8\n'),
        'import-call-and-local-type': (
            'use left::{api as Shared}\nshape Shared { value: int }\n'
            'task main() { pilot item: Shared = Shared { value: 7 } say item.value say Shared() }\n', '7\n14\n'),
        'import-type-with-ambient-value': (
            'use left::{Point as std_abs}\n'
            'task main() { pilot item: std_abs = std_abs { value: 7 } say item.read() say std_abs(-2) }\n', '7\n2\n'),
        'import-call-after-scope-exit': (
            'use left::{api as measure}\n'
            'task main() { { pilot measure: int = 7 say measure } say measure() }\n', '7\n14\n'),
        'type-constructor-with-local-value': (
            'shape Shared { value: int }\n'
            'task main() { pilot Shared: int = 7 pilot item: Shared = Shared { value: Shared } say item.value }\n', '7\n'),
        'module-call-with-local-value': (
            'use left as measure\n'
            'task main() { pilot measure: int = 7 say measure::api() }\n', '14\n'),
        'associated-type-call-with-local-value': (
            'shape Shared { value: int }\n'
            'impl Shared { task make() -> Shared { give back Shared { value: 9 } } }\n'
            'task main() { pilot Shared: int = 7 pilot item = Shared::make() say item.value }\n', '9\n'),
        'module-and-value-alias': (
            'use left as Shared\nuse right::{api as Shared}\n'
            'task main() { say Shared::api() say Shared() }\n', '14\n24\n'),
    }
    for case, (source, expected) in namespace_cases.items():
        root = work / f'namespace-{case}'
        source_app, _ = fixture(root)
        file = source_app / 'src/main.fk'
        file.write_text(source)
        for backend in ('c', 'llvm'):
            generated = work / f'namespace-{case}.{backend if backend == "c" else "ll"}'
            profile = ['v4-host-bootstrap-v1'] if case == 'bootstrap-source-helper' else []
            result = run([str(probe), str(source_app), str(file), backend, str(generated), *profile], cwd=unrelated, env=env)
            (work / f'namespace-{case}-{backend}.log').write_bytes(result.stdout + result.stderr)
            if result.returncode:
                raise RuntimeError(f'{case}/{backend} binding failed: {result.stdout + result.stderr!r}')
            binary = work / f'namespace-{case}-{backend}'
            command = [args.clang, '-O2', '-I', str(runtime), str(generated),
                       str(runtime / 'freak_runtime.c'), str(runtime / 'freak_llvm_runtime.c'), '-lm', '-o', str(binary)]
            linked = run(command, cwd=unrelated, env=env)
            (work / f'namespace-link-{case}-{backend}.log').write_bytes(linked.stdout + linked.stderr)
            if linked.returncode:
                raise RuntimeError(f'{case}/{backend} link failed')
            executed = run([str(binary)], cwd=unrelated, env=env)
            if executed.returncode or executed.stdout.decode() != expected or executed.stderr:
                raise RuntimeError(f'{case}/{backend} output {executed.stdout!r}/{executed.stderr!r}, expected {expected!r}')
            records.append({'case': case, 'backend': backend, 'status': 'executed', 'output': expected,
                            'generated_sha256': hashlib.sha256(generated.read_bytes()).hexdigest()})
    negatives = {
        'transitive': ('use base::{api}\ntask main() {}\n', 'undeclared direct dependency', 1, 5),
        'missing-public': ('use left::{missing}\ntask main() {}\n', 'missing public export', 1, 12),
        'private': ('use left::{helper}\ntask main() {}\n', 'missing public export', 1, 12),
        'duplicate-alias': ('use left::{api as value, seed as value}\ntask main() {}\n', 'duplicate import alias', 1, 26),
        'malformed': ('use left::{api as}\ntask main() {}\n', 'import alias must be an identifier', 1, 18),
        'unimported-namespace': ('task main() { say left::api() }\n', 'missing or unimported public export', 1, 19),
        'unknown-standard': ('use std::madeup::{thing}\ntask main() {}\n', 'unsupported standard module', 1, 1),
        'wrong-standard-owner': ('use std::math::{ver_parse}\ntask main() {}\n', 'selected standard module', 1, 17),
        'nominal-type-isolation': ('use left::{Point as Left}\nuse right::{Point as Right}\ntask main() { pilot bad: Left = Right { title: "other", value: 1 } }\n', 'cannot initialize Point binding', 3, 1),
        'call-only-is-not-value': ('use left::{api as Only}\ntask main() { say Only }\n', "unknown binding 'Only'", 2, 19),
        'fixed-import-cannot-use-ambient-call': ('use left::{seed as std_abs}\ntask main() { say std_abs(-2) }\n', "unknown callable 'std_abs'", 2, 19),
        'fixed-local-cannot-use-ambient-call': ('fixed pilot std_abs: int = 7\ntask main() { say std_abs(-2) }\n', "unknown callable 'std_abs'", 2, 19),
        'local-shadows-selected-call': ('use left::{api as measure}\ntask main() { pilot measure: int = 7 say measure() }\n', "unknown callable 'measure': local value shadows this name", 2, 42),
        'fixed-local-shadows-selected-call': ('use left::{api as measure}\ntask main() { fixed pilot measure: int = 7 say measure() }\n', "unknown callable 'measure': local value shadows this name", 2, 48),
        'parameter-shadows-selected-call': ('use left::{api as measure}\ntask consume(measure: int) { say measure() }\ntask main() {}\n', "unknown callable 'measure': local value shadows this name", 2, 34),
        'outer-local-shadows-selected-call': ('use left::{api as measure}\ntask main() { pilot measure: int = 7 { say measure() } }\n', "unknown callable 'measure': local value shadows this name", 2, 44),
        'multiple-shadowed-calls': ('use left::{api as measure}\ntask main() { pilot measure: int = 7 say measure() say measure() }\n', "unknown callable 'measure': local value shadows this name", 2, 1),
        'range-binder-shadows-call': ('use left::{api as measure}\ntask main() { for each measure in 0..1 { say measure() } }\n', "unknown callable 'measure': local value shadows this name", 2, 46),
        'repeat-binder-shadows-call': ('use left::{api as measure}\ntask main() { repeat 1 times with measure { say measure() } }\n', "unknown callable 'measure': local value shadows this name", 2, 49),
        'type-only-is-not-call': ('use left::{Point as Only}\ntask main() { say Only() }\n', "unknown callable 'Only'", 2, 1),
        'alias-declaration-conflict': ('use left::{api as helper}\nfixed pilot helper: int = 1\ntask main() {}\n', 'import alias conflicts', 1, 12),
        'nested-import': ('task main() {\n    use left::{api}\n}\n', 'valid only at module scope', 2, 5),
        'builtin-namespace-shadow': ('use left as process\ntask main() { say process::args_count() }\n', 'missing or unimported public export', 2, 19),
        'reserved-shape-owner': ('shape math { value: num }\ntask main() {}\n', "shape name 'math' conflicts with a compiler builtin namespace", 1, 7),
        'reserved-shape-type': ('shape CheckedReadResult { value: int }\ntask main() {}\n', "shape name 'CheckedReadResult' conflicts with a built-in type", 1, 7),
        'reserved-task': ('task word_to_int(value: word) -> int { give back 99 }\ntask main() {}\n', "callable 'word_to_int' conflicts with a compiler builtin", 1, 6),
        'reserved-runtime-task': ('task llvm_fs_read(value: word) -> int { give back 99 }\ntask main() {}\n', "callable 'llvm_fs_read' conflicts with a compiler builtin", 1, 6),
    }
    for case, (source, message, line, column) in negatives.items():
        root = work / f'negative-{case}'
        source_app, _ = fixture(root)
        file = source_app / 'src/main.fk'
        file.write_text(source)
        for backend in ('c', 'llvm'):
            result = run([str(probe), str(source_app), str(file), backend, str(work / f'negative-{case}-{backend}')], cwd=unrelated, env=env)
            log = result.stdout + result.stderr
            (work / f'negative-{case}-{backend}.log').write_bytes(log)
            location = f'{file}:{line}:{column}'.encode()
            if result.returncode == 0 or message.encode() not in log or location not in log:
                raise RuntimeError(f'{case}/{backend} missing precise rejection {location!r}: {log!r}')
            records.append({'case': case, 'backend': backend, 'status': 'rejected', 'file': str(file), 'line': line, 'column': column})
    mutations = {
        'missing-export-declaration': ('task wrong() -> int { give back 4 }\n', 'use left::{api}\ntask main() {}\n', 'unsupported exported declaration', 'app/src/main.fk', 1, 12),
        'mutable-export': ('pilot seed: int = 4\ntask api() -> int { give back seed }\n', 'use left::{seed}\ntask main() {}\n', 'unsupported exported declaration', 'app/src/main.fk', 1, 12),
        'duplicate-private-shape': ('shape Point { value: int }\nshape Point { value: int }\ntask api() -> int { give back 4 }\n', 'use left::{api}\ntask main() {}\n', 'duplicate module declaration', 'left/src/core.fk', 2, 7),
        'duplicate-private-global': ('fixed pilot seed: int = 4\nfixed pilot seed: int = 5\nshape Point { value: int }\ntask api() -> int { give back 4 }\n', 'use left::{api}\ntask main() {}\n', 'duplicate module declaration', 'left/src/core.fk', 2, 13),
        'fixed-before-call': ('fixed pilot api: int = 4\ntask api() -> int { give back 5 }\n', 'use left::{api}\ntask main() {}\n', 'duplicate module declaration', 'left/src/core.fk', 2, 6),
        'call-before-fixed': ('task api() -> int { give back 5 }\nfixed pilot api: int = 4\n', 'use left::{api}\ntask main() {}\n', 'duplicate module declaration', 'left/src/core.fk', 2, 13),
        'duplicate-private-task': ('task api() -> int { give back 4 }\ntask api() -> int { give back 5 }\n', 'use left::{api}\ntask main() {}\n', 'duplicate module declaration', 'left/src/core.fk', 2, 6),
        'dependency-source-import': ('\n\nuse rogue::{helper}\ntask api() -> int { give back 4 }\n', 'use left::{api}\ntask main() {}\n', 'undeclared direct dependency', 'left/src/core.fk', 3, 5),
        'extern-export': ('extern task api() -> int\n', 'use left::{api}\ntask main() {}\n', 'extern declarations are unsupported', 'left/src/core.fk', 1, 13),
        'fixed-before-extern': ('fixed pilot api: int = 4\nextern task api() -> int\n', 'use left::{api}\ntask main() {}\n', 'duplicate module declaration', 'left/src/core.fk', 2, 13),
        'extern-before-fixed': ('extern task api() -> int\nfixed pilot api: int = 4\n', 'use left::{api}\ntask main() {}\n', 'duplicate module declaration', 'left/src/core.fk', 2, 13),
    }
    for case, (library, source, message, relative, line, column) in mutations.items():
        root = work / f'negative-{case}'
        source_app, _ = fixture(root)
        (root / 'left/src/core.fk').write_text(library)
        file = source_app / 'src/main.fk'
        file.write_text(source)
        for backend in ('c', 'llvm'):
            result = run([str(probe), str(source_app), str(file), backend, str(work / f'negative-{case}-{backend}')], cwd=unrelated, env=env)
            log = result.stdout + result.stderr
            (work / f'negative-{case}-{backend}.log').write_bytes(log)
            location = f'{root / relative}:{line}:{column}'.encode()
            if result.returncode == 0 or message.encode() not in log or location not in log:
                raise RuntimeError(f'{case}/{backend} missing original source rejection {location!r}: {log!r}')
            if case in ('fixed-before-extern', 'extern-before-fixed'):
                if b'extern declarations are unsupported' not in log or (work / f'negative-{case}-{backend}').exists():
                    raise RuntimeError(f'{case}/{backend} weakened active extern rejection or emitted output: {log!r}')
            records.append({'case': case, 'backend': backend, 'status': 'rejected', 'file': str(root / relative), 'line': line, 'column': column})
    # A dependency export can admit a callable without accidentally exposing
    # its same-spelled legacy ordinary global as an imported value.
    legacy_root = work / 'legacy-export-surface'
    legacy_app, _ = fixture(legacy_root)
    (legacy_root / 'left/src/core.fk').write_text(
        'pilot api: int = 4\nshape Point { value: int }\n'
        'fixed pilot seed: int = 1\ntask api() -> int { give back 5 }\n'
        'task make() -> Point { give back Point { value: 1 } }\n')
    legacy_file = legacy_app / 'src/main.fk'
    for source, accepted in (('use left::{api}\ntask main() { say api() }\n', True),
                             ('use left::{api}\ntask main() { say api }\n', False)):
        legacy_file.write_text(source)
        for backend in ('c', 'llvm'):
            result = run([str(probe), str(legacy_app), str(legacy_file), backend, str(work / f'legacy-export-{accepted}-{backend}')], cwd=unrelated, env=env)
            log = result.stdout + result.stderr
            (work / f'legacy-export-{accepted}-{backend}.log').write_bytes(log)
            if accepted:
                if result.returncode or b'BINDING_OK' not in result.stdout:
                    raise RuntimeError(f'{backend} admitted callable sibling failed: {log!r}')
            elif result.returncode == 0 or b"unknown binding 'api'" not in log:
                raise RuntimeError(f'{backend} ordinary sibling leaked through public export: {log!r}')
            records.append({'case': 'legacy-export-call' if accepted else 'legacy-export-value-rejected', 'backend': backend, 'status': 'accepted' if accepted else 'rejected'})
    # Source references cannot admit declarations through their flattened
    # identities. Exact source-authored lookalikes remain legal bindings.
    identity_root = work / 'generated-identity-access'
    identity_lib = identity_root / 'lib'
    identity_app = identity_root / 'app'
    write_project(identity_lib, 'identity-library', {'core.fk':
        'fixed pilot secret: int = 4\nshape Hidden { value: int }\n'
        'impl Hidden { task make() -> Hidden { give back Hidden { value: 6 } } }\n'
        'task helper() -> int { give back secret }\n'
        'task api() -> int { pilot item = Hidden::make() give back helper() + item.value }\n'
        'task other() -> int { give back 9 }\n'}, modules={'core': 'core.fk'},
        exports={'api': 'core::api', 'other': 'core::other'})
    write_project(identity_app, 'identity-app', {'main.fk':
        'use lib::{api}\ntask main() { say api() }\n'}, entry='main.fk', dependencies={'lib': '../lib'})
    identity_file = identity_app / 'main.fk'
    identity_c = work / 'identity-admitted.c'
    admitted = run([str(probe), str(identity_app), str(identity_file), 'c', str(identity_c)], cwd=unrelated, env=env)
    if admitted.returncode:
        raise RuntimeError(f'identity admission failed: {admitted.stdout + admitted.stderr!r}')
    prefixes = re.findall(r'__freak_user_(pkg_[0-9a-f]{64}_)helper\(', identity_c.read_text())
    if len(set(prefixes)) != 1:
        raise RuntimeError('missing unique emitted private helper identity')
    prefix = prefixes[0]
    for case, body in {
        'private-call': f'say {prefix}helper()',
        'private-value': f'say {prefix}secret',
        'private-annotation': f'task consume(item: {prefix}Hidden) {{}}\ntask main() {{}}',
        'private-list-annotation': f'task consume(item: List<{prefix}Hidden>) {{}}\ntask main() {{}}',
        'private-associated': f'pilot item = {prefix}Hidden::make() say item.value',
        'unimported-public-call': f'say {prefix}other()',
    }.items():
        declaration = body if 'annotation' in case else f'task main() {{ {body} }}'
        identity_file.write_text(f'use lib::{{api}}\n{declaration}\n')
        for backend in ('c', 'llvm'):
            generated = work / f'identity-{case}-{backend}'
            result = run([str(probe), str(identity_app), str(identity_file), backend, str(generated)], cwd=unrelated, env=env)
            log = result.stdout + result.stderr
            (work / f'identity-{case}-{backend}.log').write_bytes(log)
            if result.returncode == 0 or b'missing or unimported' not in log or str(identity_file).encode() not in log or generated.exists():
                raise RuntimeError(f'{case}/{backend} generated identity admitted: {log!r}')
            records.append({'case': case, 'backend': backend, 'status': 'rejected'})
    identity_controls = {
        'source-exact-lookalikes': (
            'use lib::{api}\n'
            f'task {prefix}helper() -> int {{ give back 7 }}\n'
            f'fixed pilot {prefix}secret: int = 8\n'
            f'shape {prefix}Hidden {{ value: int }}\n'
            f'task main() {{ {{ pilot {prefix}helper: int = 1 say {prefix}helper }} '
            f'say {prefix}helper() say {prefix}secret '
            f'pilot item: {prefix}Hidden = {prefix}Hidden {{ value: 2 }} say item.value say api() }}\n',
            '1\n7\n8\n2\n10\n'),
        'explicit-exact-alias': (
            f'use lib::{{api as {prefix}helper}}\n'
            f'task main() {{ say {prefix}helper() }}\n', '10\n'),
    }
    for case, (source, expected) in identity_controls.items():
        identity_file.write_text(source)
        for backend in ('c', 'llvm'):
            generated = work / f'identity-{case}.{"c" if backend == "c" else "ll"}'
            result = run([str(probe), str(identity_app), str(identity_file), backend, str(generated)], cwd=unrelated, env=env)
            if result.returncode:
                raise RuntimeError(f'{case}/{backend} legal lookalike rejected: {result.stdout + result.stderr!r}')
            binary = work / f'identity-{case}-{backend}'
            linked = run([args.clang, '-O2', '-I', str(runtime), str(generated), str(runtime / 'freak_runtime.c'),
                          str(runtime / 'freak_llvm_runtime.c'), '-lm', '-o', str(binary)], cwd=unrelated, env=env)
            if linked.returncode:
                raise RuntimeError(f'{case}/{backend} link failed: {linked.stdout + linked.stderr!r}')
            executed = run([str(binary)], cwd=unrelated, env=env)
            if executed.returncode or executed.stdout.decode() != expected or executed.stderr:
                raise RuntimeError(f'{case}/{backend} wrong binding output: {executed.stdout!r}/{executed.stderr!r}')
            records.append({'case': case, 'backend': backend, 'status': 'executed', 'output': expected})
    standalone = work / 'standalone-extern-identity.fk'
    standalone.write_text('shape Hidden { value: int }\n'
                          'task identity_probe() -> int { give back 1 }\n'
                          'task main() { say identity_probe() }\n')
    generated = work / 'standalone-identity.c'
    result = run([str(probe), 'standalone', str(standalone), 'c', str(generated)], cwd=unrelated, env=env)
    if result.returncode:
        raise RuntimeError(f'standalone admission failed: {result.stdout + result.stderr!r}')
    prefixes = re.findall(r'__freak_user_(pkg_[0-9a-f]{64}_)identity_probe\(', generated.read_text())
    if len(set(prefixes)) != 1:
        raise RuntimeError('missing unique standalone emitted identity')
    own = prefixes[0] + 'Hidden'
    for case, signature in (
        ('parameter', f'extern task consume(item: {own}) -> void'),
        ('list-parameter', f'extern task consume(item: List<{own}>) -> void'),
        ('return', f'extern task consume() -> {own}'),
    ):
        standalone.write_text(f'shape Hidden {{ value: int }}\n{signature}\ntask main() {{}}\n')
        for backend in ('c', 'llvm'):
            generated = work / f'standalone-extern-{case}-{backend}'
            result = run([str(probe), 'standalone', str(standalone), backend, str(generated)], cwd=unrelated, env=env)
            log = result.stdout + result.stderr
            if result.returncode == 0 or ("missing or unimported type '" + own + "'").encode() not in log or str(standalone).encode() not in log or generated.exists():
                raise RuntimeError(f'extern {case}/{backend} leaked nominal type: {log!r}')
            records.append({'case': 'extern-generated-' + case, 'backend': backend, 'status': 'rejected'})
    for case, declarations in (
        ('source-nominal', 'shape Hidden { value: int }\nextern task consume(item: Hidden) -> Hidden\n'),
        ('scalar', 'extern task consume(item: int) -> int\n'),
        ('source-exact-lookalike', f'shape {own} {{ value: int }}\nextern task consume(item: {own}) -> {own}\n'),
    ):
        standalone.write_text(declarations + 'task main() {}\n')
        for backend in ('c', 'llvm'):
            generated = work / f'standalone-extern-{case}-admitted-{backend}'
            result = run([str(probe), 'standalone', str(standalone), backend, str(generated)], cwd=unrelated, env=env)
            if result.returncode:
                raise RuntimeError(f'extern {case}/{backend} source type rejected: {result.stdout + result.stderr!r}')
            records.append({'case': 'extern-' + case, 'backend': backend, 'status': 'accepted'})
    # Unused export headers collect extern value names only for collisions;
    # externs are never exports and unused bodies stay outside parsing/emission.
    for case, declarations, accepted, message, line, column in (
        ('type-value-export', 'shape Shared { value: int }\ntask Shared() -> int { give back 5 }\n', True, '', 0, 0),
        ('fixed-callable-collision', 'fixed pilot Shared: int = 4\ntask Shared() -> int { give back 5 }\n', False, 'duplicate module declaration', 2, 6),
        ('callable-fixed-collision', 'task Shared() -> int { give back 5 }\nfixed pilot Shared: int = 4\n', False, 'duplicate module declaration', 2, 13),
        ('fixed-extern-collision', 'fixed pilot Shared: int = 4\nextern task Shared() -> int\n', False, 'duplicate module declaration', 2, 13),
        ('extern-fixed-collision', 'extern task Shared() -> int\nfixed pilot Shared: int = 4\n', False, 'duplicate module declaration', 2, 13),
        ('unsupported-extern-export', 'extern task Shared() -> int\n', False, 'missing or unsupported manifest export', 1, 1),
        ('type-extern-export', 'shape Shared { value: int }\nextern task Shared() -> int\n', True, '', 0, 0),
        ('private-body', 'fixed pilot Shared: int = 4\nextern task unused_private_extern_should_not_emit() -> int\n'
                         'task unused_private_body_should_not_emit() { pilot = }\n', True, '', 0, 0),
    ):
        root = work / f'unused-namespace-{case}'
        source_app, _ = fixture(root)
        manifest = root / 'left/hangar.toml'
        manifest.write_text(manifest.read_text().replace('[modules]\n', '[modules]\nother = "src/other.fk"\n').replace('[exports]\n', '[exports]\nshared = "other::Shared"\n'))
        (root / 'left/src/other.fk').write_text(declarations)
        for backend in ('c', 'llvm'):
            generated = work / f'unused-namespace-{case}-{backend}'
            result = run([str(probe), str(source_app), str(source_app / 'src/main.fk'), backend, str(generated)], cwd=unrelated, env=env)
            log = result.stdout + result.stderr
            (work / f'unused-namespace-{case}-{backend}.log').write_bytes(log)
            if accepted:
                if result.returncode or b'BINDING_OK' not in result.stdout:
                    raise RuntimeError(f'{backend} unused {case} incorrectly rejected: {log!r}')
                if case == 'private-body' and b'unused_private_' in generated.read_bytes():
                    raise RuntimeError(f'{backend} emitted an unused private body or extern')
            else:
                location = f'{root / "left/src/other.fk"}:{line}:{column}'.encode()
                if result.returncode == 0 or message.encode() not in log or location not in log or generated.exists():
                    raise RuntimeError(f'{backend} unused {case} missing original source rejection {location!r}: {log!r}')
            records.append({'case': 'unused-' + case, 'backend': backend, 'status': 'accepted' if accepted else 'rejected'})
    for count in (1, 2):
        invalid = 'task lexical_probe() { say "' + 'before\\x00after' * count + '" }\n'
        loaded = work / f'lexical-count-{count}.fk'
        loaded.write_text(invalid + 'task main() {}\n')
        root = work / f'unused-lexical-count-{count}'
        source_app, _ = fixture(root)
        manifest = root / 'left/hangar.toml'
        manifest.write_text(manifest.read_text().replace('[modules]\n', '[modules]\nother = "src/other.fk"\n').replace('[exports]\n', '[exports]\nexposed = "other::exposed"\n'))
        unloaded = root / 'left/src/other.fk'
        unloaded.write_text('task exposed() -> int { give back 4 }\n' + invalid)
        for phase, project_root, source in (
            ('loaded', 'standalone', loaded), ('unloaded-export', str(source_app), source_app / 'src/main.fk')
        ):
            for backend in ('c', 'llvm'):
                generated = work / f'lexical-count-{count}-{phase}-{backend}'
                result = run([str(probe), project_root, str(source), backend, str(generated)], cwd=unrelated, env=env)
                log = result.stdout + result.stderr
                (work / f'lexical-count-{count}-{phase}-{backend}.log').write_bytes(log)
                if result.returncode == 0 or f'{count} syntax error(s)'.encode() not in log or log.count(b'embedded NUL escape is not supported') != count or generated.exists():
                    raise RuntimeError(f'{backend} {phase} lexical count {count} not preserved: {log!r}')
                expected_phase = b'lexically invalid source module:' if phase == 'loaded' else b'lexically invalid exported source module:'
                if expected_phase not in log:
                    raise RuntimeError(f'{backend} wrong lexical admission phase: {log!r}')
                records.append({'case': f'{phase}-lexical-count-{count}', 'backend': backend, 'status': 'rejected'})
    # Missing exports in an unused public module are validated as declaration
    # metadata, while unused private modules stay outside the emitted program.
    unused = work / 'negative-unused-export'
    unused_app, _ = fixture(unused)
    manifest = unused / 'left/hangar.toml'
    manifest.write_text(manifest.read_text().replace('[modules]\n', '[modules]\nother = "src/other.fk"\n').replace('[exports]\n', '[exports]\nmissing = "other::absent"\n'))
    (unused / 'left/src/other.fk').write_text('task present() -> int { give back 1 }\n')
    for backend in ('c', 'llvm'):
        result = run([str(probe), str(unused_app), str(unused_app / 'src/main.fk'), backend, str(work / f'unused-{backend}')], cwd=unrelated, env=env)
        log = result.stdout + result.stderr
        (work / f'negative-unused-export-{backend}.log').write_bytes(log)
        location = f'{unused / "left/src/other.fk"}:1:1'.encode()
        if result.returncode == 0 or b'missing or unsupported manifest export' not in log or location not in log:
            raise RuntimeError(f'unused export metadata missing rejection: {log!r}')
        records.append({'case': 'unused-public-missing-export', 'backend': backend, 'status': 'rejected'})
    evidence = {'status': 'PASS', 'scope': 'native binding component; source-store/public CLI integration remains separate',
                'compiler_sha256': hashlib.sha256(args.compiler.read_bytes()).hexdigest(),
                'probe_sha256': hashlib.sha256(probe.read_bytes()).hexdigest(),
                'binding_sha256': hashlib.sha256((repo / 'src/cli/package_binding.fk').read_bytes()).hexdigest(),
                'records': records}
    args.evidence.write_text(json.dumps(evidence, indent=2) + '\n')
    print(f'PASS {len(records)} native package binding checks')


if __name__ == '__main__':
    main()
