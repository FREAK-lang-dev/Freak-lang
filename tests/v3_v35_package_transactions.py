#!/usr/bin/env python3
"""Native package generation journal: durability faults and killed writers."""
from __future__ import annotations
import argparse
import contextlib
import hashlib
import os
from pathlib import Path
import tempfile
import tomllib
import v3_word_foundation as foundation
from v3_v35_hangar import probe_transpile, require_resource_conservation
from v3_v35_package_sources import package_probe_source, project as graph_project

PROGRAM = r'''
task transaction_unit() {
    pilot directory = fs::open_dir_ticket(process::arg(1))
    pilot private = package_private_directory(directory, ".freak")
    pilot held = fs::lock_dir_ticket(private, "graph.lock")
    pilot valid = false
    if not fs::result_ok(held) { hangar_graph_fail("fixture lock unavailable") } else {
        if process::arg(2) == "recover" { valid = package_recover_transaction(directory, private) } else {
            pilot manifest = fs::read_ticket(process::arg(3))
            pilot lock = fs::read_bytes_ticket(process::arg(4))
            pilot bytes: ByteBuffer = fs::result_bytes(lock)
            pilot before = fs::read_relative_bytes_ticket(directory, "hangar.toml")
            pilot previous = fs::read_relative_bytes_ticket(directory, "hangar.lock")
            pilot old: ByteBuffer = fs::result_bytes(before)
            pilot expected = fs::sha256_bytes(old)
            old.release()
            pilot previous_hash = ""
            if fs::result_ok(previous) {
                old = fs::result_bytes(previous)
                previous_hash = fs::sha256_bytes(old)
                old.release()
            }
            fs::result_release(before)
            fs::result_release(previous)
            if process::arg(2) == "stale" { expected = "0000000000000000000000000000000000000000000000000000000000000000" }
            valid = package_commit_transaction(directory, private, "hangar.toml", fs::result_word(manifest), bytes, expected, previous_hash)
            bytes.release()
            fs::result_release(manifest)
            fs::result_release(lock)
        }
    }
    if valid { say "ready" } else { say "error:" + hangar_graph_error }
    fs::result_release(held)
    fs::result_release(private)
    fs::result_release(directory)
    package_release_graph()
}
task main() {
    if process::arg(2) == "graph" {
        pilot valid = package_prepare_graph(package_join_host(process::arg(1), "hangar.toml"), false, false, false, "")
        if valid { say "ready" } else { say "error:" + hangar_graph_error }
        package_release_graph()
    } else { transaction_unit() }
}
'''

INTERPOSE = r'''#include <sys/stat.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
extern int __real_fsync(int);
int __wrap_fsync(int fd) {
    struct stat information;
    const char *wanted=getenv("FREAK_TX_FAULT_DIRECTORY");
    const char *rank=getenv("FREAK_TX_FAULT_NUMBER");
    static int seen;
    if (wanted && rank && fstat(fd,&information)==0 && S_ISDIR(information.st_mode)) {
        char source[64], path[4096];
        snprintf(source,sizeof(source),"/proc/self/fd/%d",fd);
        ssize_t length=readlink(source,path,sizeof(path)-1);
        if (length>=0) {
            path[length]=0;
            if (!strcmp(path,wanted) && ++seen==atoi(rank)) {
                if (getenv("FREAK_TX_KILL_AFTER_SYNC")) {
                    if (__real_fsync(fd)!=0) _exit(87);
                    _exit(86);
                }
                errno=EIO; return -1;
            }
        }
    }
    return __real_fsync(fd);
}
'''


def run_gate(compiler: Path, clang: Path, runtime: Path, root: Path) -> None:
    repo=Path(__file__).resolve().parents[1]
    wrapper=root/'journal-fsync.c'
    wrapper.write_text(INTERPOSE,encoding='ascii')
    old_manifest=b'[project]\nname="old"\nversion="1.0.0"\nkind="app"\nentry="main.fk"\n'
    new_manifest=old_manifest.replace(b'name="old"',b'name="new"')
    old_lock=b'PREVIOUS COMPLETE LOCK GENERATION\n'
    new_lock=b'NEW COMPLETE LOCK GENERATION\n'
    candidate_manifest=root/'candidate.toml'
    candidate_lock=root/'candidate.lock'
    candidate_manifest.write_bytes(new_manifest)
    candidate_lock.write_bytes(new_lock)
    for backend in ('c','llvm'):
        program=root/f'transaction-{backend}.fk'
        program.write_text(package_probe_source(repo)+'\n'+PROGRAM,encoding='utf-8')
        generated=probe_transpile(foundation,None,compiler,repo,program,backend)
        binary=root/f'transaction-{backend}'
        command=[str(clang),'-g','-O1','-DFREAK_WORD_FOUNDATION_AUDIT=1','-o',str(binary),str(generated)]
        if backend=='llvm': command+=['-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1',str(runtime/'freak_llvm_runtime.c')]
        else: command+=['-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1']
        command += [str(runtime/'freak_runtime.c'),str(wrapper),'-I',str(runtime),'-lm','-fsanitize=address,undefined','-fno-omit-frame-pointer','-Wl,--wrap=fsync']
        built=foundation.run(command,repo,timeout=120)
        assert built.returncode==0,(built.stdout,built.stderr)

        def fixture(label: str, present=True) -> Path:
            project=root/f'{backend}-{label}'
            project.mkdir()
            (project/'.freak').mkdir(mode=0o700)
            (project/'hangar.toml').write_bytes(old_manifest)
            (project/'main.fk').write_bytes(b'task main() { say 42 }\n')
            if present: (project/'hangar.lock').write_bytes(old_lock)
            return project

        def execute(project: Path, mode='commit', fault=None, kill=False) -> str:
            environment=foundation.sanitizer_env()
            if fault:
                directory,number=fault
                environment.update(FREAK_TX_FAULT_DIRECTORY=str(directory),FREAK_TX_FAULT_NUMBER=str(number))
                if kill: environment['FREAK_TX_KILL_AFTER_SYNC']='1'
            checked=foundation.run([str(binary),str(project),mode,str(candidate_manifest),str(candidate_lock)],root,environment,timeout=30)
            if kill:
                assert checked.returncode==86,(checked.returncode,checked.stdout,checked.stderr)
            else:
                assert checked.returncode==0,(checked.returncode,checked.stdout,checked.stderr)
                require_resource_conservation(foundation,checked.stderr)
            return checked.stdout

        for label,target,number in (
            ('manifest-before-sync','private',1),('lock-before-sync','private',2),
            ('pending-marker-sync','private',3),('manifest-publish-sync','project',1),
            ('lock-publish-sync','project',2),('commit-marker-sync','private',4),
        ):
            project=fixture(label)
            directory=project/'.freak' if target=='private' else project
            failed=execute(project,fault=(directory,number))
            assert failed.startswith('error:') and 'synchronization failed' in failed,failed
            assert (project/'hangar.toml').read_bytes()==old_manifest,label
            assert (project/'hangar.lock').read_bytes()==old_lock,label
            assert execute(project,'recover')=='ready\n'
            assert execute(project)=='ready\n'
            assert (project/'hangar.toml').read_bytes()==new_manifest and (project/'hangar.lock').read_bytes()==new_lock
            print(f'native:{backend}:transactions:{label}:passed',flush=True)
        project=fixture('cleanup-sync')
        assert execute(project,fault=(project/'.freak',5))=='ready\n'
        assert (project/'hangar.toml').read_bytes()==new_manifest and (project/'hangar.lock').read_bytes()==new_lock
        assert execute(project,'recover')=='ready\n'
        print(f'native:{backend}:transactions:committed-cleanup-sync:passed',flush=True)
        for label,target,number,committed in (
            ('pending','private',3,False),('manifest','project',1,False),
            ('lock','project',2,False),('committed','private',4,True),
        ):
            project=fixture('killed-'+label)
            directory=project/'.freak' if target=='private' else project
            execute(project,fault=(directory,number),kill=True)
            marker=tomllib.loads((project/'.freak/transaction.marker').read_text())
            assert marker['phase']==('committed' if committed else 'pending')
            assert execute(project,'recover')=='ready\n'
            assert (project/'hangar.toml').read_bytes()==(new_manifest if committed else old_manifest)
            assert (project/'hangar.lock').read_bytes()==(new_lock if committed else old_lock)
            assert not (project/'.freak/transaction.marker').exists()
            print(f'native:{backend}:transactions:killed-{label}-recovery:passed',flush=True)
        project=fixture('absent-lock',present=False)
        assert execute(project,fault=(project,2)).startswith('error:')
        assert (project/'hangar.toml').read_bytes()==old_manifest and not (project/'hangar.lock').exists()
        assert execute(project)=='ready\n'
        print(f'native:{backend}:transactions:absent-lock-rollback:passed',flush=True)
        for label,path in (('changed-current','hangar.toml'),('corrupt-before','.freak/transaction.manifest.before')):
            project=fixture(label)
            execute(project,fault=(project,1),kill=True)
            (project/path).write_bytes(b'UNEXPECTED THIRD GENERATION')
            before={str(item):item.read_bytes() for item in project.rglob('*') if item.is_file()}
            failed=execute(project,'recover')
            assert failed.startswith('error:') and 'unverified before images or unexpected project bytes' in failed,failed
            after={str(item):item.read_bytes() for item in project.rglob('*') if item.is_file()}
            assert after==before
            print(f'native:{backend}:transactions:{label}-preserved:passed',flush=True)
        project=fixture('interrupted-recovery')
        execute(project,fault=(project,1),kill=True)
        execute(project,'recover',fault=(project,1),kill=True)
        assert execute(project,'recover')=='ready\n'
        assert (project/'hangar.toml').read_bytes()==old_manifest and (project/'hangar.lock').read_bytes()==old_lock
        print(f'native:{backend}:transactions:interrupted-recovery-resumes:passed',flush=True)
        project=fixture('stale-admission')
        rejected=execute(project,'stale')
        assert rejected.startswith('error:') and 'changed after graph admission' in rejected,rejected
        assert (project/'hangar.toml').read_bytes()==old_manifest and (project/'hangar.lock').read_bytes()==old_lock
        assert not (project/'.freak/transaction.marker').exists()
        print(f'native:{backend}:transactions:stale-admission-preserved:passed',flush=True)
        for label, suffix in (('unknown-marker-table','\n[unexpected]\n'),('unknown-marker-field','\nunknown="value"\n')):
            project=fixture(label)
            execute(project,fault=(project/'.freak',3),kill=True)
            marker=project/'.freak/transaction.marker'
            marker.write_text(marker.read_text()+suffix,encoding='utf-8')
            before={str(item):item.read_bytes() for item in project.rglob('*') if item.is_file()}
            failed=execute(project,'recover')
            assert failed.startswith('error:') and 'unknown or missing fields' in failed,failed
            assert {str(item):item.read_bytes() for item in project.rglob('*') if item.is_file()}==before
            print(f'native:{backend}:transactions:{label}-preserved:passed',flush=True)
        manifest=graph_project(root/f'{backend}-whole-graph')
        (manifest.parent/'.freak').mkdir(mode=0o700)
        assert execute(manifest.parent,'graph')=='ready\n'
        previous_lock=manifest.with_name('hangar.lock').read_bytes()
        previous_manifest=manifest.read_bytes()
        previous_cache={str(item):item.read_bytes() for item in (manifest.parent/'.freak').rglob('*') if item.is_file() and item.name!='graph.lock'}
        (manifest.parent.parent/'c/core.fk').write_bytes(b'task value() -> int { give back 43 }\n')
        failed=execute(manifest.parent,'graph',fault=(manifest.parent,1))
        assert failed.startswith('error:') and 'new lock publication failed' in failed,failed
        assert manifest.with_name('hangar.lock').read_bytes()==previous_lock and manifest.read_bytes()==previous_manifest
        assert all(Path(path).read_bytes()==data for path,data in previous_cache.items())
        assert not (manifest.parent/'.freak/transaction.marker').exists()
        assert execute(manifest.parent,'graph')=='ready\n'
        assert manifest.with_name('hangar.lock').read_bytes()!=previous_lock
        print(f'native:{backend}:transactions:whole-graph-publication-rollback-retry:passed',flush=True)


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler',type=Path,required=True)
    parser.add_argument('--clang',type=Path,required=True)
    parser.add_argument('--runtime-root',type=Path,required=True)
    parser.add_argument('--probe-root',type=Path)
    args=parser.parse_args()
    if args.probe_root: args.probe_root.mkdir(parents=True,exist_ok=False)
    context=contextlib.nullcontext(str(args.probe_root.resolve())) if args.probe_root else tempfile.TemporaryDirectory(prefix='freak-v35-journal-')
    with context as directory: run_gate(args.compiler.resolve(strict=True),args.clang.resolve(strict=True),args.runtime_root.resolve(strict=True),Path(directory))
    return 0


if __name__=='__main__': raise SystemExit(main())
