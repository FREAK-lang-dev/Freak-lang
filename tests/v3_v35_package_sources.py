#!/usr/bin/env python3
"""Native immutable local graph/lock/source checkpoints; no Git closure claim."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import struct
import tempfile
import tomllib
import contextlib
import v3_word_foundation as foundation
from v3_v35_hangar import task_source, probe_transpile, require_resource_conservation

PROGRAM = r'''
task main() {
    pilot mode = process::arg(2)
    pilot update = ""
    if mode == "update" { update = "*" }
    pilot valid = false
    if mode == "snapshot" { valid = package_load_graph_snapshot(process::arg(3), process::arg(1), true) } else {
        valid = package_prepare_graph(process::arg(1), mode == "locked", mode == "offline", mode == "frozen", update)
    }
    if not valid { say "error:" + hangar_graph_error } else {
        pilot content = package_lock_render()
        if not package_lock_parse(content) { say "error:lock roundtrip:" + package_lock_error } else {
            say "ready: " + word_from_int(hangar_graph_count) + ":" + word_from_int(hangar_graph_edge_count)
            say package_graph_snapshot_path
            say package_read_graph_source(0, "main.fk")
        }
    }
    package_sources_release()
    package_inputs_release()
    hangar_graph_release()
    package_lock_release()
    toml_release()
}
'''


def project(root: Path) -> Path:
    for name in ('consumer', 'a', 'b', 'c'):
        directory = root / name
        directory.mkdir(parents=True)
        if name == 'consumer':
            text = '[project]\nname="consumer"\nversion="1.0.0"\nkind="app"\nentry="main.fk"\n[dependencies]\na={path="../a"}\nb={path="../b"}\n'
            (directory / 'main.fk').write_text('task main() { say 42 }\n', encoding='utf-8')
        else:
            text = f'[project]\nname="{name}"\nversion="1.0.0"\nkind="lib"\n[modules]\ncore="core.fk"\n[exports]\nvalue="core::value"\n'
            (directory / 'core.fk').write_text('task value() -> int { give back 42 }\n', encoding='utf-8')
            if name in ('a', 'b'):
                text += '[dependencies]\nc={path="../c"}\n'
        (directory / 'hangar.toml').write_text(text, encoding='utf-8')
    return root / 'consumer' / 'hangar.toml'


def validate_lock(path: Path) -> dict:
    lock = tomllib.loads(path.read_text(encoding='utf-8'))
    assert lock['lock']['schema'] == 2 and lock['lock']['node_count'] == 4
    assert lock['lock']['edge_count'] == 4 and lock['lock']['file_count'] == 8
    for index in range(4):
        node = lock['node'][str(index)]
        records = [lock['file'][str(file)] for file in range(8) if lock['file'][str(file)]['node'] == index]
        assert len(records) == node['input_count'] == 2
        data = b'FREAK-source-input-tree-v2\n' + struct.pack('>q', len(records))
        for record in records:
            relative = record['path'].encode('utf-8')
            contents = (Path(node['origin']) / record['path']).read_bytes()
            assert hashlib.sha256(contents).hexdigest() == record['sha256'] and len(contents) == record['length']
            data += struct.pack('>q', len(relative)) + relative + struct.pack('>qqq', 1, 0, len(contents)) + contents
        assert hashlib.sha256(data).hexdigest() == node['tree_sha256']
    assert lock['lock']['manifest_sha256'] == lock['node']['0']['manifest_sha256']
    return lock


def run_gate(compiler: Path, clang: Path, runtime: Path, root: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    hangar = (repo/'src/cli/hangar.fk').read_text()
    toml = (repo/'src/cli/toml.fk').read_text()
    for name in ('toml_load', 'toml_write_file'):
        toml = toml.replace(task_source(toml, name), '')
    source = ((repo/'std/version.fk').read_text() + '\n' + toml + '\n' +
              task_source(hangar, 'hangar_valid_package_name') + '\n' +
              task_source(hangar, 'hangar_checked_fs') + '\n' +
              '\n'.join((repo/f'src/cli/{name}.fk').read_text() for name in ('package_graph','package_paths','package_inputs','package_sources','package_lock')) + '\n' + PROGRAM)
    for backend in ('c','llvm'):
        program = root/f'sources-{backend}.fk'
        program.write_text(source, encoding='utf-8')
        generated = probe_transpile(foundation, None, compiler, repo, program, backend)
        binary = root/f'sources-{backend}'
        foundation.compile_generated(clang=str(clang), repo=repo, runtime_root=runtime, generated=generated, backend=backend, binary=binary)
        def execute(manifest: Path, mode='ordinary', snapshot='') -> str:
            result = foundation.run([str(binary), str(manifest), mode, str(snapshot)], root, foundation.sanitizer_env(), timeout=30)
            assert result.returncode == 0, (backend, mode, result.returncode, result.stdout, result.stderr)
            require_resource_conservation(foundation, result.stderr)
            return result.stdout
        manifest = project(root/f'diamond-{backend}')
        initial = execute(manifest)
        assert initial.startswith('ready: 4:4\n'), initial
        validate_lock(manifest.with_name('hangar.lock'))
        print(f'native:{backend}:sources:local-diamond:passed', flush=True)
        print(f'native:{backend}:sources:canonical-lock-inventory:passed', flush=True)
        snapshot = initial.splitlines()[1]
        locked = execute(manifest, 'locked')
        assert locked == initial, locked
        print(f'native:{backend}:sources:locked-no-refresh:passed', flush=True)
        frozen = execute(manifest, 'frozen')
        assert frozen == initial, frozen
        print(f'native:{backend}:sources:frozen-clean:passed', flush=True)
        assert execute(manifest, 'snapshot', snapshot) == initial
        print(f'native:{backend}:sources:snapshot-reuse:passed', flush=True)
        old_lock = manifest.with_name('hangar.lock').read_bytes()
        (manifest.parent.parent/'c/core.fk').write_text('task value() -> int { give back 43 }\n', encoding='utf-8')
        rejected = execute(manifest, 'frozen')
        assert rejected.startswith('error:') and 'frozen source input tree changed' in rejected, rejected
        assert manifest.with_name('hangar.lock').read_bytes() == old_lock
        print(f'native:{backend}:sources:frozen-transitive-edit:passed', flush=True)
        rejected = execute(manifest, 'snapshot', snapshot)
        assert rejected.startswith('error:') and 'frozen source input tree changed' in rejected, rejected
        print(f'native:{backend}:sources:snapshot-transitive-edit:passed', flush=True)
        updated = execute(manifest)
        assert updated.startswith('ready: 4:4\n') and updated.splitlines()[1] != snapshot, updated
        print(f'native:{backend}:sources:ordinary-local-edit:passed', flush=True)
        malformed = project(root/f'malformed-{backend}')
        malformed.with_name('hangar.lock').write_text('[[package]]\nname="legacy"\n', encoding='utf-8')
        before = malformed.with_name('hangar.lock').read_bytes()
        rejected = execute(malformed)
        assert rejected.startswith('error:') and 'legacy hangar.lock' in rejected, rejected
        assert malformed.with_name('hangar.lock').read_bytes() == before
        assert execute(malformed, 'update').startswith('ready: 4:4\n')
        print(f'native:{backend}:sources:explicit-legacy-migration:passed', flush=True)


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler',type=Path,required=True)
    parser.add_argument('--clang',type=Path,required=True)
    parser.add_argument('--runtime-root',type=Path,required=True)
    parser.add_argument('--probe-root',type=Path)
    args=parser.parse_args()
    if args.probe_root:
        args.probe_root.mkdir(parents=True,exist_ok=False)
    context=contextlib.nullcontext(str(args.probe_root.resolve())) if args.probe_root else tempfile.TemporaryDirectory(prefix='freak-v35-sources-')
    with context as location:
        run_gate(args.compiler.resolve(strict=True),args.clang.resolve(strict=True),args.runtime_root.resolve(strict=True),Path(location))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
