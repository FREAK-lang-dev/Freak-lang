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
    if mode == "host" {
        say package_parent_path(process::arg(1))
        say package_leaf_path(process::arg(1))
        say package_join_host(process::arg(1), "child")
        say package_local_path(process::arg(1), "../sibling")
        package_release_graph()
        give back
    }
    if mode == "discover" {
        if not package_prepare_project_sources(process::arg(1)) { say "error:" + hangar_graph_error } else {
            if package_graph_no_manifest { say "standalone" } else { say "manifest:" + package_graph_manifest_path }
        }
        package_release_graph()
        give back
    }
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
    if mode.starts_with("candidate") {
        pilot candidate = fs::read_ticket(process::arg(3))
        if not fs::result_ok(candidate) { hangar_graph_fail("fixture candidate read failed") } else {
            valid = package_prepare_manifest_change(process::arg(1), fs::result_word(candidate), process::arg(4), mode == "candidate-locked", mode == "candidate-offline", mode == "candidate-frozen", "")
        }
        fs::result_release(candidate)
    } else if mode == "snapshot" or mode == "snapshot-lock" { valid = package_load_graph_snapshot(process::arg(3), process::arg(1), true) } else {
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
        if (!strcmp(argv[i],"fetch") && getenv("FREAK_GIT_FETCH_LOG")) {
            FILE *log=fopen(getenv("FREAK_GIT_FETCH_LOG"),"ab");
            if (!log) return 74;
            fputs("fetch\n",log); fclose(log);
        }
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


def run_gate(compiler: Path, clang: Path, runtime: Path, root: Path, paths_only: bool = False, physical_roots: bool = False) -> None:
    repo = Path(__file__).resolve().parents[1]
    source = package_probe_source(repo) + '\n' + PROGRAM
    git_shim = build_git_shim(clang, root)
    for backend in ('c','llvm'):
        candidate_boundary=root/f'candidate-boundary-{backend}.fk'
        boundary='''pilot mut package_manifest_candidate_active = false
pilot mut package_manifest_candidate_text: word = ""
pilot mut package_manifest_candidate_before: word = ""
pilot hangar_graph_manifest_limit = 1048576
task hangar_graph_fail(message: word) {}
task package_lock_hex(text: word, length: int) -> bool { give back true }
task package_prepare_graph(manifest_path: word, locked: bool, offline: bool, frozen: bool, update_name: word) -> bool { give back true }
'''+task_source((repo/'src/cli/package_sources.fk').read_text(),'package_prepare_manifest_change')
        candidate_boundary.write_text(boundary+'\ntask main() { package_prepare_manifest_change("","","",false,false,false,"") }\n')
        checked=foundation.run([str(compiler),str(candidate_boundary),'--'+backend,'--strict-borrow'],repo,timeout=45)
        assert checked.returncode==0,(checked.stdout,checked.stderr)
        print(f'native:{backend}:sources:candidate-boundary-strict-ownership:passed',flush=True)
        program = root/f'sources-{backend}.fk'
        program.write_text(source, encoding='utf-8')
        generated = probe_transpile(foundation, None, compiler, repo, program, backend)
        binary = root/f'sources-{backend}'
        foundation.compile_generated(clang=str(clang), repo=repo, runtime_root=runtime, generated=generated, backend=backend, binary=binary)
        def execute(manifest: Path, mode='ordinary', snapshot='', extra_env=None, fingerprint='') -> str:
            environment = foundation.sanitizer_env()
            if extra_env: environment.update(extra_env)
            result = foundation.run([str(binary), str(manifest), mode, str(snapshot),fingerprint], root, environment, timeout=45)
            assert result.returncode == 0, (backend, mode, result.returncode, result.stdout, result.stderr)
            require_resource_conservation(foundation, result.stderr)
            return result.stdout
        if os.name!='nt':
            for value in ('/tmp/Literal\\Backslash/CaseΩ','/tmp/Colon:Name/CaseΩ','/tmp/Name. /CaseΩ','\\\\?\\C:\\literal'):
                path=Path(value)
                parent=value.rsplit('/',1)[0] if '/' in value else '.'
                leaf=value.rsplit('/',1)[-1]
                local=parent+'/sibling' if value.startswith('/') else ''
                expected=f'{parent}\n{leaf}\n{value}/child\n{local}\n'
                checked=execute(path,'host',extra_env={'OS':'Windows_NT'})
                assert checked==expected,(value,checked,expected)
            print(f'native:{backend}:sources:host-platform-paths-ignore-os-env:passed',flush=True)
            manifest=project(root/f'neighbor-paths-{backend}')
            neighbor=manifest.parent/'neighbor'
            neighbor.mkdir()
            (neighbor/'hangar.toml').write_bytes(b'UNRELATED NEIGHBOR MANIFEST')
            selected=manifest.parent/'neighbor\\source.fk'
            selected.write_bytes(b'task main() { say 99 }\n')
            previous={str(path):path.read_bytes() for path in neighbor.rglob('*') if path.is_file()}
            assert execute(selected,'discover',extra_env={'OS':'Windows_NT'})=='manifest:'+str(manifest)+'\n'
            assert {str(path):path.read_bytes() for path in neighbor.rglob('*') if path.is_file()}==previous
            print(f'native:{backend}:sources:literal-backslash-source-preserves-neighbor:passed',flush=True)
            if physical_roots:
                for label in ('Literal\\Backslash','Colon:Root','CaseΩ'):
                    manifest=project(root/f'physical-{backend}-{label}')
                    result=execute(manifest,extra_env={'OS':'Windows_NT'})
                    assert result.startswith('ready: 4:4\n'),result
                    validate_lock(manifest.with_name('hangar.lock'))
                print(f'native:{backend}:sources:physical-posix-special-roots:passed',flush=True)
                standalone=root/f'standalone-{backend}'
                standalone.mkdir()
                selected=standalone/'ordinary\\source.fk'
                selected.write_bytes(b'task main() { say 42 }\n')
                assert execute(selected,'discover',extra_env={'OS':'Windows_NT'})=='standalone\n'
                assert not (standalone/'.freak').exists()
                print(f'native:{backend}:sources:standalone-nearest-discovery-through-root:passed',flush=True)
        if paths_only: continue
        manifest=project(root/f'candidate-{backend}')
        assert execute(manifest).startswith('ready: 4:4\n')
        previous_manifest=manifest.read_bytes()
        previous_lock=manifest.with_name('hangar.lock').read_bytes()
        before_sha=hashlib.sha256(previous_manifest).hexdigest()
        previous_cache={str(path):path.read_bytes() for path in (manifest.parent/'.freak').rglob('*') if path.is_file()}
        candidate=root/f'candidate-manifest-{backend}.toml'
        candidate.write_bytes(previous_manifest.replace(b'b={path="../b"}',b'b={path="../missing"}'))
        failed=execute(manifest,'candidate',candidate,fingerprint=before_sha)
        assert failed.startswith('error:') and 'cannot open local package' in failed,failed
        assert manifest.read_bytes()==previous_manifest and manifest.with_name('hangar.lock').read_bytes()==previous_lock
        assert all(Path(path).read_bytes()==data for path,data in previous_cache.items())
        print(f'native:{backend}:sources:candidate-closure-failure-preserves-generation:passed',flush=True)
        candidate.write_bytes(previous_manifest.replace(b'b={path="../b"}\n',b''))
        for mode in ('candidate-locked','candidate-frozen'):
            failed=execute(manifest,mode,candidate,fingerprint=before_sha)
            assert failed.startswith('error:') and 'locked/frozen' in failed,failed
            assert manifest.read_bytes()==previous_manifest and manifest.with_name('hangar.lock').read_bytes()==previous_lock
        print(f'native:{backend}:sources:candidate-strict-modes-refused-unchanged:passed',flush=True)
        failed=execute(manifest,'candidate',candidate,fingerprint='0'*64)
        assert failed.startswith('error:') and 'changed before candidate' in failed,failed
        assert manifest.read_bytes()==previous_manifest and manifest.with_name('hangar.lock').read_bytes()==previous_lock
        print(f'native:{backend}:sources:candidate-stale-origin-preserved:passed',flush=True)
        assert execute(manifest,'candidate-offline',candidate,fingerprint=before_sha).startswith('ready: 3:2\n')
        changed=tomllib.loads(manifest.with_name('hangar.lock').read_text())
        assert manifest.read_bytes()==candidate.read_bytes() and manifest.with_name('hangar.lock').read_bytes()!=previous_lock
        assert changed['lock']['manifest_sha256']==hashlib.sha256(candidate.read_bytes()).hexdigest()
        root_node=changed['node']['0']
        root_manifest=Path(manifest.parent/'.freak/store')/root_node['tree_sha256']/'hangar.toml'
        assert root_manifest.read_bytes()==candidate.read_bytes()
        print(f'native:{backend}:sources:candidate-offline-atomic-generation:passed',flush=True)
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
        sub_manifest=project(root/f'git-subpackages-{backend}')
        for name in ('a','b'):
            item=sub_manifest.parent.parent/name/'hangar.toml'
            item.write_text(item.read_text().replace('c={path="../c"}', 'c={git="https://fixture.invalid/c",rev="v1"}'),encoding='utf-8')
        sub_repository,_=git_fixture(root/f'git-sub-repository-{backend}')
        item=sub_repository/'hangar.toml'
        item.write_text(item.read_text()+'[dependencies]\nd={path="libd"}\n',encoding='utf-8')
        for name in ('libd','libe'):
            directory=sub_repository/name
            directory.mkdir()
            text=f'[project]\nname="{name}"\nversion="1.0.0"\nkind="lib"\n[modules]\ncore="core.fk"\n[exports]\nvalue="core::value"\n'
            if name=='libd': text+='[dependencies]\ne={path="../libe"}\n'
            (directory/'hangar.toml').write_text(text,encoding='utf-8')
            (directory/'core.fk').write_bytes(b'task value() -> int { give back 42 }\n')
        git(['add','--','hangar.toml','libd/hangar.toml','libd/core.fk','libe/hangar.toml','libe/core.fk'],sub_repository)
        git(['commit','--quiet','-m','Subpackage fixture'],sub_repository)
        git(['tag','--force','v1'],sub_repository)
        sub_commit=git(['rev-parse','HEAD'],sub_repository)
        fetch_log=root/f'fetch-subpackages-{backend}.log'
        sub_env={'FREAK_GIT':str(git_shim),'FREAK_GIT_FIXTURE_REPO':str(sub_repository),'FREAK_GIT_FETCH_LOG':str(fetch_log)}
        installed_sub=execute(sub_manifest,'update',extra_env=sub_env)
        assert installed_sub.startswith('ready: 6:6\n'),installed_sub
        assert fetch_log.read_bytes()==b'fetch\n','same Git selector/commit fetched more than once'
        print(f'native:{backend}:sources:git-subpackage-closure-one-fetch:passed',flush=True)
        sub_lock=tomllib.loads(sub_manifest.with_name('hangar.lock').read_text())
        for index,node in sub_lock['node'].items():
            if node['kind']!='git': continue
            prefix='' if node['name']=='c' else node['name']
            expected_identity='git:https://fixture.invalid/c@'+sub_commit+(':'+prefix if prefix else '')
            assert node['identity']==expected_identity and node['origin']=='https://fixture.invalid/c' and node['commit']==sub_commit
            records=[record for record in sub_lock['file'].values() if record['node']==int(index)]
            canonical=b'FREAK-source-input-tree-v2\n'+struct.pack('>q',len(records))
            for record in records:
                object_path=(prefix+'/' if prefix else '')+record['path']
                blob=subprocess.run([shutil.which('git'),'show',sub_commit+':'+object_path],cwd=sub_repository,capture_output=True,timeout=30)
                assert blob.returncode==0,blob.stderr
                relative=record['path'].encode('utf-8')
                assert hashlib.sha256(blob.stdout).hexdigest()==record['sha256'] and len(blob.stdout)==record['length']
                assert (sub_manifest.parent/'.freak/store'/node['tree_sha256']/record['path']).read_bytes()==blob.stdout
                canonical+=struct.pack('>q',len(relative))+relative+struct.pack('>qqq',1,0,len(blob.stdout))+blob.stdout
            assert hashlib.sha256(canonical).hexdigest()==node['tree_sha256']
        print(f'native:{backend}:sources:git-subpackage-raw-object-integrity:passed',flush=True)
        no_fetch_sub={**sub_env,'FREAK_GIT_FORBID_FETCH':'1'}
        assert execute(sub_manifest,'snapshot',installed_sub.splitlines()[1],extra_env=no_fetch_sub)==installed_sub
        print(f'native:{backend}:sources:git-subpackage-snapshot-offline:passed',flush=True)
        for name in ('a','b'):
            item=sub_manifest.parent.parent/name/'hangar.toml'
            item.write_text(item.read_text().replace('rev="v1"','rev="'+sub_commit+'"'),encoding='utf-8')
        sub_manifest.with_name('hangar.lock').unlink()
        indexed=execute(sub_manifest,'offline',extra_env=no_fetch_sub)
        assert indexed.startswith('ready: 6:6\n'),indexed
        assert fetch_log.read_bytes()==b'fetch\n'
        print(f'native:{backend}:sources:git-index-offline-without-lock-pins:passed',flush=True)
        previous_sub_lock=sub_manifest.with_name('hangar.lock').read_bytes()
        index_name=hashlib.sha256(('FREAK-git-source-index-v2\nhttps://fixture.invalid/c\n'+sub_commit+'\nlibd\n').encode()).hexdigest()+'.toml'
        index_path=sub_manifest.parent/'.freak/git-index'/index_name
        index_bytes=index_path.read_bytes()
        index_path.write_bytes(index_bytes.replace(b'prefix = "libd"',b'prefix = "unexpected"'))
        corrupted=index_path.read_bytes()
        rejected=execute(sub_manifest,'offline',extra_env=no_fetch_sub)
        assert rejected.startswith('error:') and 'Git source index metadata is corrupt' in rejected,rejected
        assert index_path.read_bytes()==corrupted and sub_manifest.with_name('hangar.lock').read_bytes()==previous_sub_lock
        index_path.write_bytes(index_bytes)
        print(f'native:{backend}:sources:git-corrupt-index-preserved:passed',flush=True)
        d_node=next(node for node in tomllib.loads(previous_sub_lock.decode())['node'].values() if node['name']=='libd')
        d_tree=sub_manifest.parent/'.freak/store'/d_node['tree_sha256']
        parked=d_tree.with_name(d_tree.name+'.parked')
        d_tree.rename(parked)
        try:
            rejected=execute(sub_manifest,'offline',extra_env=no_fetch_sub)
            assert rejected.startswith('error:') and 'offline Git cache miss' in rejected,rejected
            assert not d_tree.exists() and sub_manifest.with_name('hangar.lock').read_bytes()==previous_sub_lock
        finally: parked.rename(d_tree)
        print(f'native:{backend}:sources:git-subpackage-cache-miss-no-fetch-repair:passed',flush=True)
        item=sub_repository/'libd/hangar.toml'
        item.write_text(item.read_text().replace('e={path="../libe"}','c={path=".."}'),encoding='utf-8')
        git(['add','--','libd/hangar.toml'],sub_repository)
        git(['commit','--quiet','-m','Cyclic subpackage fixture'],sub_repository)
        git(['tag','--force','v1'],sub_repository)
        for name in ('a','b'):
            item=sub_manifest.parent.parent/name/'hangar.toml'
            item.write_text(item.read_text().replace('rev="'+sub_commit+'"','rev="v1"'),encoding='utf-8')
        rejected=execute(sub_manifest,'update',extra_env=sub_env)
        assert rejected.startswith('error:') and 'cycle' in rejected,rejected
        assert sub_manifest.with_name('hangar.lock').read_bytes()==previous_sub_lock
        print(f'native:{backend}:sources:git-subpackage-cycle-preserves-generation:passed',flush=True)
        item=sub_repository/'hangar.toml'
        item.write_text(item.read_text().replace('d={path="libd"}','d={path="../outside"}'),encoding='utf-8')
        git(['add','--','hangar.toml'],sub_repository)
        git(['commit','--quiet','-m','Escaping subpackage fixture'],sub_repository)
        git(['tag','--force','v1'],sub_repository)
        rejected=execute(sub_manifest,'update',extra_env=sub_env)
        assert rejected.startswith('error:') and 'escapes its filesystem root' in rejected,rejected
        assert sub_manifest.with_name('hangar.lock').read_bytes()==previous_sub_lock
        assert not list((sub_manifest.parent/'.freak').glob('.git-fetch-*')) and not list((sub_manifest.parent/'.freak').glob('.git-input-*'))
        print(f'native:{backend}:sources:git-subpackage-escape-preserves-generation:passed',flush=True)
        item=sub_repository/'hangar.toml'
        item.write_text(item.read_text().replace('d={path="../outside"}','d={path="libd"}'),encoding='utf-8')
        for filename in ('hangar.toml','core.fk'): (sub_repository/'libd'/filename).unlink()
        (sub_repository/'libd').rmdir()
        (sub_repository/'libd').symlink_to('libe',target_is_directory=True)
        git(['add','--','hangar.toml','libd'],sub_repository)
        git(['commit','--quiet','-m','Symlink subpackage fixture'],sub_repository)
        git(['tag','--force','v1'],sub_repository)
        rejected=execute(sub_manifest,'update',extra_env=sub_env)
        assert rejected.startswith('error:') and 'missing directory, symlink or submodule' in rejected,rejected
        assert sub_manifest.with_name('hangar.lock').read_bytes()==previous_sub_lock
        print(f'native:{backend}:sources:git-subpackage-symlink-preserves-generation:passed',flush=True)



def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler',type=Path,required=True)
    parser.add_argument('--clang',type=Path,required=True)
    parser.add_argument('--runtime-root',type=Path,required=True)
    parser.add_argument('--probe-root',type=Path)
    parser.add_argument('--paths-only',action='store_true')
    parser.add_argument('--physical-roots',action='store_true')
    args=parser.parse_args()
    if args.probe_root:
        args.probe_root.mkdir(parents=True,exist_ok=False)
    context=contextlib.nullcontext(str(args.probe_root.resolve())) if args.probe_root else tempfile.TemporaryDirectory(prefix='freak-v35-sources-')
    with context as location:
        run_gate(args.compiler.resolve(strict=True),args.clang.resolve(strict=True),args.runtime_root.resolve(strict=True),Path(location),args.paths_only,args.physical_roots)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
