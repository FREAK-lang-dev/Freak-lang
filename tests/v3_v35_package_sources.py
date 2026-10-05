#!/usr/bin/env python3
"""Native immutable local graph/lock/source checkpoints; no Git closure claim."""
from __future__ import annotations
import argparse
import hashlib
import os
import shutil
import subprocess
from pathlib import Path
import struct
import tempfile
import tomllib
import contextlib
import concurrent.futures
import v3_word_foundation as foundation
from v3_v35_hangar import task_source, probe_transpile, require_resource_conservation

PROGRAM = r'''
task main() {
    pilot mode = process::arg(2)
    pilot held = 0
    if mode == "snapshot-lock" {
        pilot parent = fs::open_dir_ticket(package_parent_path(process::arg(1)))
        pilot private = fs::open_relative_dir_ticket(parent, ".freak")
        held = fs::lock_dir_ticket(private, "graph.lock")
        fs::result_release(private)
        fs::result_release(parent)
        if not fs::result_ok(held) { say "fixture-error:" + fs::result_error(held) }
    }
    pilot update = ""
    if mode == "update" { update = "*" }
    pilot valid = false
    if mode == "snapshot" or mode == "snapshot-lock" { valid = package_load_graph_snapshot(process::arg(3), process::arg(1), true) } else {
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
    package_release_graph()
    if held != 0 { fs::result_release(held) }
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


def git(command: list[str], cwd: Path) -> str:
    tool = shutil.which('git')
    assert tool, 'native Git prerequisite missing'
    result = subprocess.run([tool, *command], cwd=cwd, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, (command, result.stdout, result.stderr)
    return result.stdout.strip()


def git_fixture(directory: Path) -> tuple[Path,str]:
    directory.mkdir()
    git(['init','--quiet'], directory)
    git(['config','user.name','Fixture'], directory)
    git(['config','user.email','fixture@example.invalid'], directory)
    (directory/'hangar.toml').write_text('[project]\nname="c"\nversion="1.0.0"\nkind="lib"\n[modules]\ncore="core.fk"\n[exports]\nvalue="core::value"\n[assets]\nbinary="assets/raw.bin"\n',encoding='utf-8')
    (directory/'core.fk').write_bytes(b'task value() -> int { give back 42 }\n')
    (directory/'.gitattributes').write_text('*.fk text eol=crlf\n',encoding='ascii')
    (directory/'assets').mkdir()
    (directory/'assets/raw.bin').write_bytes(b'A\0\xffB\r\n')
    (directory/'tests').mkdir()
    (directory/'tests/z_test.fk').write_bytes(b'task main() { say 42 }\n')
    (directory/'.env').write_bytes(b'UNDECLARED SECRET')
    git(['add','--','hangar.toml','core.fk','.gitattributes','assets/raw.bin','tests/z_test.fk','.env'],directory)
    git(['commit','--quiet','-m','First fixture'],directory)
    git(['tag','v1'],directory)
    return directory,git(['rev-parse','HEAD'],directory)


def git_move_tag(directory: Path, body: bytes) -> str:
    (directory/'core.fk').write_bytes(body)
    git(['add','--','core.fk'],directory)
    git(['commit','--quiet','-m','Moved source'],directory)
    git(['tag','--force','v1'],directory)
    return git(['rev-parse','HEAD'],directory)


def git_move_symlink(directory: Path) -> None:
    (directory/'core.fk').unlink()
    (directory/'core.fk').symlink_to('outside-source.fk')
    git(['add','--','core.fk'],directory)
    git(['commit','--quiet','-m','Symlink source'],directory)
    git(['tag','--force','v1'],directory)


def build_git_shim(clang: Path, root: Path) -> Path:
    real = shutil.which('git')
    assert real, 'native Git prerequisite missing'
    source=root/'git-native-fixture.c'
    source.write_text(r'''#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
int main(int argc,char **argv) {
    char **args=calloc((size_t)argc+1,sizeof(char*));
    if (!args) return 70;
    args[0]=getenv("FREAK_GIT_FIXTURE_TOOL");
    if (!args[0]) return 70;
    for (int i=1;i<argc;i++) {
        args[i]=argv[i];
        if (!strcmp(argv[i],"https://fixture.invalid/c")) args[i]=getenv("FREAK_GIT_FIXTURE_REPO");
        if (!strcmp(argv[i],"fetch") && getenv("FREAK_GIT_FORBID_FETCH")) return 71;
        if (!strcmp(argv[i],"fetch") && getenv("FREAK_GIT_PARTIAL_FAIL")) {
            FILE *file=fopen("partial-before-failure","wb");
            if (!file) return 72;
            fputs("partial native fetch",file); fclose(file); return 23;
        }
    }
    /* Fixture-only transport redirection: production retains https-only. */
    setenv("GIT_ALLOW_PROTOCOL","https:file",1);
    execv(args[0],args);
    return 73;
}
''',encoding='ascii')
    binary=root/'git-native-fixture'
    built=foundation.run([str(clang),str(source),'-o',str(binary)],root,timeout=30)
    assert built.returncode==0,(built.stdout,built.stderr)
    os.environ['FREAK_GIT_FIXTURE_TOOL']=real
    return binary


def package_probe_source(repo: Path) -> str:
    hangar = (repo/'src/cli/hangar.fk').read_text()
    toml = (repo/'src/cli/toml.fk').read_text()
    for name in ('toml_load', 'toml_write_file'):
        toml = toml.replace(task_source(toml, name), '')
    return ((repo/'std/version.fk').read_text() + '\n' + toml + '\n' +
              task_source(hangar, 'hangar_valid_package_name') + '\n' +
              task_source(hangar, 'hangar_checked_fs') + '\n' +
              '\n'.join(task_source(hangar, name) for name in ('hangar_git_command','hangar_valid_git_source','hangar_valid_revision')) + '\n' +
              '\n'.join((repo/f'src/cli/{name}.fk').read_text() for name in ('package_graph','package_paths','package_inputs','package_sources','package_lock','package_transaction')))


def run_gate(compiler: Path, clang: Path, runtime: Path, root: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    source = package_probe_source(repo) + '\n' + PROGRAM
    git_shim = build_git_shim(clang, root)
    for backend in ('c','llvm'):
        program = root/f'sources-{backend}.fk'
        program.write_text(source, encoding='utf-8')
        generated = probe_transpile(foundation, None, compiler, repo, program, backend)
        binary = root/f'sources-{backend}'
        foundation.compile_generated(clang=str(clang), repo=repo, runtime_root=runtime, generated=generated, backend=backend, binary=binary)
        def execute(manifest: Path, mode='ordinary', snapshot='', extra_env=None) -> str:
            environment = foundation.sanitizer_env()
            if extra_env: environment.update(extra_env)
            result = foundation.run([str(binary), str(manifest), mode, str(snapshot)], root, environment, timeout=45)
            assert result.returncode == 0, (backend, mode, result.returncode, result.stdout, result.stderr)
            require_resource_conservation(foundation, result.stderr)
            return result.stdout
        for label, declaration, reason in (
            ('reserved-fact', '\n[__package]\ntests_declared="true"\n', 'reserved package admission fact'),
            ('nested-tests', '\n[tests.nested]\npath="main.fk"\n', 'flat name-to-relative-source map'),
        ):
            invalid = project(root/f'invalid-{backend}-{label}')
            invalid.write_text(invalid.read_text()+declaration, encoding='utf-8')
            rejected = execute(invalid)
            assert rejected.startswith('error:') and reason in rejected, rejected
            assert not invalid.with_name('hangar.lock').exists()
            print(f'native:{backend}:sources:{label}:passed', flush=True)
        manifest = project(root/f'diamond-{backend}')
        initial = execute(manifest)
        assert initial.startswith('ready: 4:4\n'), initial
        validate_lock(manifest.with_name('hangar.lock'))
        print(f'native:{backend}:sources:local-diamond:passed', flush=True)
        print(f'native:{backend}:sources:canonical-lock-inventory:passed', flush=True)
        snapshot = initial.splitlines()[1]
        snapshot_file=Path(snapshot)
        snapshot_bytes=snapshot_file.read_bytes()
        original_lock=manifest.with_name('hangar.lock').read_bytes()
        snapshot_file.write_bytes(b'CORRUPT IMMUTABLE SNAPSHOT')
        rejected=execute(manifest)
        assert rejected.startswith('error:') and 'existing immutable graph snapshot is corrupt' in rejected,rejected
        assert snapshot_file.read_bytes()==b'CORRUPT IMMUTABLE SNAPSHOT'
        assert manifest.with_name('hangar.lock').read_bytes()==original_lock
        snapshot_file.write_bytes(snapshot_bytes)
        print(f'native:{backend}:sources:corrupt-snapshot-preserved:passed',flush=True)
        locked = execute(manifest, 'locked')
        assert locked == initial, locked
        print(f'native:{backend}:sources:locked-no-refresh:passed', flush=True)
        frozen = execute(manifest, 'frozen')
        assert frozen == initial, frozen
        print(f'native:{backend}:sources:frozen-clean:passed', flush=True)
        assert execute(manifest, 'snapshot', snapshot) == initial
        print(f'native:{backend}:sources:snapshot-reuse:passed', flush=True)
        before = {str(path): (path.read_bytes(), path.stat().st_mtime_ns) for path in manifest.parent.rglob('*') if path.is_file()}
        assert execute(manifest, 'snapshot-lock', snapshot) == initial
        print(f'native:{backend}:sources:snapshot-with-writer-lock:passed', flush=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as readers:
            results = list(readers.map(lambda _: execute(manifest, 'snapshot', snapshot), range(4)))
        assert results == [initial] * 4, results
        after = {str(path): (path.read_bytes(), path.stat().st_mtime_ns) for path in manifest.parent.rglob('*') if path.is_file()}
        assert after == before, 'immutable snapshot reader changed files or file mtimes'
        print(f'native:{backend}:sources:snapshot-concurrent-read-only:passed', flush=True)
        cache = manifest.parent/'.freak/store'
        parked = cache.with_name('store.parked')
        cache.rename(parked)
        try:
            rejected = execute(manifest, 'snapshot', snapshot)
            assert rejected.startswith('error:') and 'existing safe source store' in rejected, rejected
            assert not cache.exists(), 'snapshot reader recreated missing store'
        finally:
            parked.rename(cache)
        print(f'native:{backend}:sources:snapshot-missing-cache-no-repair:passed', flush=True)
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
        git_manifest = project(root/f'git-diamond-{backend}')
        for name in ('a', 'b'):
            item = git_manifest.parent.parent/name/'hangar.toml'
            item.write_text(item.read_text().replace('c={path="../c"}', 'c={git="https://fixture.invalid/c",rev="v1"}'), encoding='utf-8')
        repository, old_commit = git_fixture(root/f'git-repository-{backend}')
        git_env = {"FREAK_GIT":str(git_shim), "FREAK_GIT_FIXTURE_REPO":str(repository)}
        rejected = execute(git_manifest, extra_env=git_env)
        assert rejected.startswith('error:') and 'unlocked mutable Git revision requires explicit' in rejected, rejected
        assert not git_manifest.with_name('hangar.lock').exists()
        print(f'native:{backend}:sources:git-mutable-explicit-only:passed', flush=True)
        installed = execute(git_manifest, 'update', extra_env=git_env)
        assert installed.startswith('ready: 4:4\n'), installed
        locked_git = tomllib.loads(git_manifest.with_name('hangar.lock').read_text())
        node = next(item for item in locked_git['node'].values() if item['kind']=='git')
        assert node['commit'] == old_commit and node['origin'] == 'https://fixture.invalid/c'
        git_tree = git_manifest.parent/'.freak/store'/node['tree_sha256']
        assert (git_tree/'core.fk').read_bytes() == b'task value() -> int { give back 42 }\n'
        assert (git_tree/'assets/raw.bin').read_bytes() == b'A\0\xffB\r\n'
        assert sorted(path.relative_to(git_tree).as_posix() for path in git_tree.rglob('*') if path.is_file()) == ['assets/raw.bin','core.fk','hangar.toml','tests/z_test.fk']
        records = [item for item in locked_git['file'].values() if item['node'] == next(int(index) for index,item in locked_git['node'].items() if item['kind']=='git')]
        canonical = b'FREAK-source-input-tree-v2\n'+struct.pack('>q',len(records))
        for record in records:
            blob = subprocess.run([shutil.which('git'), 'show', old_commit+':'+record['path']], cwd=repository, capture_output=True, timeout=30)
            assert blob.returncode == 0, blob.stderr
            relative = record['path'].encode('utf-8')
            assert blob.stdout == (git_tree/record['path']).read_bytes()
            assert hashlib.sha256(blob.stdout).hexdigest() == record['sha256'] and len(blob.stdout) == record['length']
            canonical += struct.pack('>q',len(relative))+relative+struct.pack('>qqq',1,0,len(blob.stdout))+blob.stdout
        assert hashlib.sha256(canonical).hexdigest() == node['tree_sha256']
        print(f'native:{backend}:sources:git-raw-objects-no-checkout:passed', flush=True)
        print(f'native:{backend}:sources:git-declared-only-binary-default-tests:passed', flush=True)
        old_lock = git_manifest.with_name('hangar.lock').read_bytes()
        new_commit = git_move_tag(repository, b'task value() -> int { give back 43 }\n')
        no_fetch = {**git_env, 'FREAK_GIT_FORBID_FETCH':'1'}
        assert execute(git_manifest, 'locked', extra_env=no_fetch) == installed
        assert execute(git_manifest, 'offline', extra_env=no_fetch) == installed
        assert git_manifest.with_name('hangar.lock').read_bytes() == old_lock
        print(f'native:{backend}:sources:git-moved-tag-locked-offline:passed', flush=True)
        failed = execute(git_manifest, 'update', extra_env={**git_env,'FREAK_GIT_PARTIAL_FAIL':'1'})
        assert failed.startswith('error:') and 'Git object operation failed' in failed, failed
        assert git_manifest.with_name('hangar.lock').read_bytes() == old_lock
        assert not list((git_manifest.parent/'.freak').glob('.git-fetch-*')) and not list((git_manifest.parent/'.freak').glob('.git-input-*'))
        print(f'native:{backend}:sources:git-failure-preserves-generation:passed', flush=True)
        refreshed = execute(git_manifest, 'update', extra_env=git_env)
        assert refreshed.startswith('ready: 4:4\n') and refreshed != installed, refreshed
        current = tomllib.loads(git_manifest.with_name('hangar.lock').read_text())
        fresh_node = next(item for item in current['node'].values() if item['kind']=='git')
        assert fresh_node['commit'] == new_commit and (git_tree/'core.fk').read_bytes().endswith(b'42 }\n')
        print(f'native:{backend}:sources:git-explicit-update:passed', flush=True)
        new_lock = git_manifest.with_name('hangar.lock').read_bytes()
        git_move_symlink(repository)
        rejected = execute(git_manifest, 'update', extra_env=git_env)
        assert rejected.startswith('error:') and 'ordinary blob' in rejected, rejected
        assert git_manifest.with_name('hangar.lock').read_bytes() == new_lock
        assert not list((git_manifest.parent/'.freak').glob('.git-fetch-*')) and not list((git_manifest.parent/'.freak').glob('.git-input-*'))
        print(f'native:{backend}:sources:git-symlink-refused:passed', flush=True)



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
