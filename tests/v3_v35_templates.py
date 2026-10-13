#!/usr/bin/env python3
"""Native template generation and installed project build/run/test acceptance.

The small creator harness supplies only the existing payload/platform selector
interfaces. Its generation code and checked FS operations are production code.
Passing --cli additionally exercises real init dispatch, package imports,
native build/run/test and default HTTP exposure from the installed payload.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import select
import shutil
import subprocess
import tempfile
import time
import uuid
from v3_v35_acceptance import run_command
from v3_v35_http import assert_response, parse_response, request


class TemplateProgress:
    """Retain bounded, current-run checkpoints before each long operation."""

    MAX_REPORT_BYTES = 1024 * 1024

    def __init__(self, path: Path | None, report: dict, creator_matrices: list[dict],
                 installed_matrices: list[dict]):
        self._expectations(creator_matrices, installed_matrices)
        self.path = path.parent.resolve() / path.name if path is not None else None
        self.report = report
        self.logs = None
        self.run_id = uuid.uuid4().hex
        report['creator_matrices'] = []
        report['installed_cli_matrices'] = []
        report['installed_cli_verified'] = False
        report['matrices'] = []
        report['commands'] = []
        report['progress'] = {
            'schema': 1, 'run_id': self.run_id, 'outcome': 'running', 'sequence': 0,
            'expected_creator_matrices': creator_matrices,
            'expected_installed_matrices': installed_matrices,
            'completed_creator_matrices': 0, 'completed_installed_matrices': 0,
            'completed_matrices': 0, 'expected_matrices': len(creator_matrices) + len(installed_matrices),
            'active': {'phase': 'report-start'},
        }

    def __enter__(self):
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            # Never read or credit a preceding invocation's terminal report.
            if os.path.lexists(self.path):
                previous = self.path.with_name(self.path.name + '.previous-' + self.run_id)
                os.replace(self.path, previous)
                self.report['previous_report'] = {'path': str(previous), 'scope': 'preceding invocation'}
            self.logs = self.path.parent / (self.path.stem + '-logs') / self.run_id
            self.logs.mkdir(parents=True, exist_ok=False)
            self.report['logs'] = str(self.logs)
        self._write()
        return self

    def __exit__(self, kind, error, traceback):
        if error is not None:
            self.report['progress'].update(outcome='failed', exception_type=kind.__name__)
            try:
                self._write()
            except BaseException as secondary:
                self._note(error, 'Template checkpoint recording failed', secondary)
            return False
        if self.report['progress']['outcome'] != 'passed':
            error = RuntimeError('Template verification ended without a passing checkpoint')
            self.report['progress'].update(outcome='failed', exception_type=type(error).__name__)
            try:
                self._write()
            except BaseException as secondary:
                self._note(error, 'Template checkpoint recording failed', secondary)
            raise error
        return False

    @staticmethod
    def _note(primary, label, secondary):
        try:
            primary.add_note(label + ': ' + type(secondary).__name__[:160])
        except BaseException:
            pass

    @staticmethod
    def _label(value):
        if not isinstance(value, str) or not value or len(value) > 160:
            raise ValueError('invalid template checkpoint label')
        return value

    def matrix_started(self, matrix: str, backend: str | None = None,
                       optimization: int | None = None, fixture: str | None = None):
        if matrix not in ('creator', 'installed-cli') or backend not in (None, 'c', 'llvm'):
            raise ValueError('invalid template checkpoint matrix')
        if optimization is not None and (type(optimization) is not int or optimization not in (0, 2, 3)):
            raise ValueError('invalid template checkpoint optimization')
        active = {'phase': 'matrix-start', 'matrix': matrix}
        if backend is not None:active['backend'] = backend
        if optimization is not None:active['optimization'] = optimization
        if fixture is not None:active['fixture'] = self._label(fixture)
        self.report['progress']['active'] = active
        self._write()

    def stage(self, phase: str, fixture: str | None = None):
        active = self.report['progress']['active']
        active['phase'] = self._label(phase)
        if fixture is not None:active['fixture'] = self._label(fixture)
        self._write()

    def matrix_finished(self):
        progress = self.report['progress']
        progress['completed_creator_matrices'] = len(self.report['creator_matrices'])
        progress['completed_installed_matrices'] = len(self.report['installed_cli_matrices'])
        self.report['matrices'] = self._matrix_summary(self.report)
        progress['completed_matrices'] = len(self.report['matrices'])
        self.stage('matrix-finish')

    @staticmethod
    def _expectations(creators, installed):
        if (not isinstance(creators, list) or not creators or
                not isinstance(installed, list) or
                any(not isinstance(item, dict) or set(item) != {'backend', 'optimization'} or
                    item['backend'] not in ('c', 'llvm') or type(item['optimization']) is not int or
                    item['optimization'] not in (0, 2, 3) for item in creators) or
                any(not isinstance(item, dict) or set(item) != {'template', 'backend'} or
                    item['template'] not in ('cli', 'lib', 'http') or item['backend'] not in ('c', 'llvm')
                    for item in installed)):
            raise ValueError('invalid template checkpoint expectations')

    @staticmethod
    def _matrix_summary(report):
        creators, installed = TemplateProgress._matrix_keys(report)
        return ([dict(kind='creator', status='PASS', **item) for item in creators] +
                [dict(kind='installed-cli', status='PASS', **item) for item in installed])

    @staticmethod
    def _matrix_keys(report):
        creators = [{'backend': item['backend'], 'optimization': item['optimization']}
                    for item in report['creator_matrices']]
        installed = [{'template': item['template'], 'backend': item['backend']}
                     for item in report['installed_cli_matrices']]
        return creators, installed

    def passed(self):
        creators, installed = self._matrix_keys(self.report)
        progress = self.report['progress']
        if (self.report.get('pinned_inputs_unchanged') is not True or
                creators != progress['expected_creator_matrices'] or
                installed != progress['expected_installed_matrices'] or
                progress['completed_creator_matrices'] != len(creators) or
                progress['completed_installed_matrices'] != len(installed) or
                self.report['matrices'] != self._matrix_summary(self.report) or
                progress['completed_matrices'] != len(creators) + len(installed) or
                progress['expected_matrices'] != len(creators) + len(installed) or
                self.report['installed_cli_verified'] is not bool(installed)):
            raise RuntimeError('Template checkpoint cannot pass before all original matrices and input verification')
        progress.update(outcome='passed', active={'phase': 'complete'})
        self._write()

    def _write(self):
        if self.path is None:return
        self.report['progress']['sequence'] += 1
        payload = (json.dumps(self.report, indent=2) + '\n').encode('utf-8')
        if len(payload) > self.MAX_REPORT_BYTES:
            raise ValueError('template checkpoint exceeds bounded report size')
        temporary = None
        primary = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.path.parent, prefix='.' + self.path.name + '-', delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(payload);stream.flush();os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        except BaseException as error:
            primary = error
            raise
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except BaseException as secondary:
                    if primary is None:raise
                    self._note(primary, 'Template staged-file cleanup failed', secondary)

    @classmethod
    def read(cls, path: Path):
        with path.open('rb') as stream:payload = stream.read(cls.MAX_REPORT_BYTES + 1)
        if len(payload) > cls.MAX_REPORT_BYTES:
            raise ValueError('template checkpoint exceeds bounded report size')
        report = json.loads(payload)
        progress = report['progress']
        cls._expectations(progress['expected_creator_matrices'], progress['expected_installed_matrices'])
        creators, installed = cls._matrix_keys(report)
        if (type(progress['schema']) is not int or progress['schema'] != 1 or
                progress['outcome'] not in ('running', 'failed', 'passed') or
                type(progress['sequence']) is not int or progress['sequence'] < 1 or
                not isinstance(progress['run_id'], str) or not re.fullmatch('[0-9a-f]{32}', progress['run_id']) or
                type(progress['completed_creator_matrices']) is not int or
                type(progress['completed_installed_matrices']) is not int or
                progress['completed_creator_matrices'] != len(creators) or
                progress['completed_installed_matrices'] != len(installed) or
                type(progress['completed_matrices']) is not int or
                type(progress['expected_matrices']) is not int or
                progress['completed_matrices'] != len(creators) + len(installed) or
                progress['expected_matrices'] != len(progress['expected_creator_matrices']) + len(progress['expected_installed_matrices']) or
                report['matrices'] != cls._matrix_summary(report) or
                not isinstance(progress['expected_creator_matrices'], list) or
                not isinstance(progress['expected_installed_matrices'], list) or
                creators != progress['expected_creator_matrices'][:len(creators)] or
                installed != progress['expected_installed_matrices'][:len(installed)] or
                len(creators) > len(progress['expected_creator_matrices']) or
                len(installed) > len(progress['expected_installed_matrices']) or
                not isinstance(progress['active'], dict)):
            raise ValueError('inconsistent template checkpoint')
        cls._label(progress['active']['phase'])
        if progress['outcome'] == 'passed' and (
                report.get('pinned_inputs_unchanged') is not True or
                creators != progress['expected_creator_matrices'] or
                installed != progress['expected_installed_matrices'] or
                report['installed_cli_verified'] is not bool(installed) or
                progress['active'] != {'phase': 'complete'}):
            raise ValueError('incomplete template checkpoint cannot pass')
        return report

    def process_record(self, command, *, cwd, label, timeout):
        record = {'case': self._label(label), 'argv': list(map(str, command)), 'cwd': str(cwd),
                  'timeout_seconds': timeout, 'began_monotonic': time.monotonic()}
        self.report['commands'].append(record)
        self.stage('command-start', label)
        return record

    def process_finished(self, record, child, stdout, stderr, primary):
        secondary = None
        record.update(returncode=child.returncode if child is not None else None,
                      elapsed_seconds=time.monotonic() - record.pop('began_monotonic'),
                      stdout_sha256=hashlib.sha256(stdout).hexdigest(),
                      stderr_sha256=hashlib.sha256(stderr).hexdigest(), raw_files={})
        if primary is not None:record['error_type'] = type(primary).__name__
        if self.logs is not None:
            index = self.report['commands'].index(record) + 1
            for channel, data in (('stdout', stdout), ('stderr', stderr)):
                path = self.logs / (str(index) + '.' + channel)
                retained = {'path': str(path), 'written': False}
                record['raw_files'][channel] = retained
                try:
                    path.write_bytes(data);retained['written'] = True
                except BaseException as error:
                    retained['error_type'] = type(error).__name__
                    if secondary is None:secondary = error
        try:
            self._write()
        except BaseException as error:
            if secondary is None:secondary = error
        if secondary is not None:
            if primary is None:raise secondary
            self._note(primary, 'Template command recording failed', secondary)


def cleanup_owned_child(child, record, *, timeout, primary=None, stdout=None, stderr=None):
    """Bound cleanup without replacing the operation that caused it."""
    stdout = (getattr(primary, 'output', None) if stdout is None else stdout)
    stderr = (getattr(primary, 'stderr', None) if stderr is None else stderr)
    stdout = b'' if stdout is None else stdout
    stderr = b'' if stderr is None else stderr
    errors = []
    first_error = None
    try:
        running = child.poll() is None
    except BaseException as error:
        errors.append(type(error).__name__);first_error = error;running = True
    if running or primary is not None:
        try:
            if os.name == 'nt':
                stopped = subprocess.run(['taskkill', '/PID', str(child.pid), '/T', '/F'], capture_output=True, timeout=10)
                record['tree_cleanup'] = {'returncode': stopped.returncode,
                                          'stdout_hex': stopped.stdout.hex(), 'stderr_hex': stopped.stderr.hex()}
                if stopped.returncode != 0:errors.append('taskkill did not confirm tree termination')
            # POSIX children inherit the release gate's group. Never kill that
            # group from inside it; its outer owner handles abrupt parent exit.
        except ProcessLookupError:
            pass
        except BaseException as error:
            errors.append(type(error).__name__)
            if first_error is None:first_error = error
        try:
            if child.poll() is None:child.kill()
        except BaseException as error:
            errors.append(type(error).__name__)
            if first_error is None:first_error = error
        try:
            recovered_out, recovered_err = child.communicate(timeout=timeout)
        except BaseException as error:
            errors.append(type(error).__name__)
            recovered_out, recovered_err = getattr(error, 'output', None), getattr(error, 'stderr', None)
            if first_error is None:first_error = error
        result = (stdout if recovered_out is None else recovered_out,
                  stderr if recovered_err is None else recovered_err)
        record['cleanup_errors'] = errors
        record['cleanup_failed'] = bool(errors) or child.returncode is None
        if first_error is not None:
            if primary is None:raise first_error
            TemplateProgress._note(primary, 'Template process cleanup failed', first_error)
        return result
    return None

SELECTORS=r'''
task cli_find_runtime_dir() -> word { give back process::env("TEMPLATE_RUNTIME") }
task cli_is_windows() -> bool { give back process::env("OS") == "Windows_NT" }
task cli_payload_is_resolution_error(value: word) -> bool { give back value.starts_with("!freak-payload-resolution-error!") }
'''
MAIN=r'''
task main() {
    pilot success = cli_create_template(process::arg(1), process::arg(2))
    if success { say "OK" } else { say "ERROR " + cli_template_error }
    cli_template_error = ""
}
'''

def text_channel(data: bytes):
    # Match subprocess.run(text=True, encoding='utf-8') universal newlines.
    return data.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')


def run(command,*,cwd,env=None,timeout=90,progress=None,label='command'):
    if progress is None or progress.logs is None:
        return subprocess.run(list(map(str,command)),cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8',timeout=timeout)
    progress.stage('command-start', label)
    prefix = progress.logs / str(len(progress.report['commands']) + 1)
    result = run_command(list(map(str, command)), cwd=cwd, env=env, label=label,
                         prefix=prefix, records=progress.report['commands'], expected=None,
                         timeout=timeout, on_record=lambda record: progress._write())
    return subprocess.CompletedProcess(result.args, result.returncode,
                                       text_channel(result.stdout), text_channel(result.stderr))

def tree(path:Path):
    return {str(p.relative_to(path)).replace(os.sep,'/'):p.read_bytes() for p in path.rglob('*') if p.is_file()}

def expected(canonical:Path,kind:str,name:str):
    consumer='template-consumer-app' if name=='template-consumer' else 'template-consumer'
    return {k:v.replace(b'@@NAME@@',name.encode()).replace(b'@@CONSUMER_NAME@@',consumer.encode()) for k,v in tree(canonical/kind).items()}

def creator_case(binary:Path,kind:str,destination:Path,env,*,success:bool,progress=None):
    r=run([binary,kind,destination],cwd=destination.parent if destination.parent.exists() else destination.parents[1],env=env,progress=progress,label='creator-'+kind+'-'+destination.name)
    assert r.returncode==0 and not r.stderr,(kind,destination,r.returncode,r.stdout,r.stderr)
    assert r.stdout.startswith('OK\n' if success else 'ERROR '),(kind,destination,success,r.stdout)
    return r

def directory_has_entry(destination:Path):
    # Check owned directory entries without following the candidate leaf.
    # Windows stat/exists can expose a NUL device even when no entry was made.
    name=destination.name.casefold() if os.name=='nt' else destination.name
    return any((entry.name.casefold() if os.name=='nt' else entry.name)==name
               for entry in destination.parent.iterdir())

def creator_corpus(binary:Path,canonical:Path,root:Path,env,progress=None):
    parent=root/'parent space🚀';parent.mkdir();env=env.copy()
    # Selector points at an existing repo or installed payload; CWD contains no
    # templates. The native selector itself remains the CLI owner's gate.
    payload=canonical.parents[1];selected_runtime=payload/'runtime'
    if not selected_runtime.is_dir():selected_runtime=payload/'freakc/runtime'
    assert selected_runtime.is_dir(),selected_runtime
    env['TEMPLATE_RUNTIME']=str(selected_runtime)
    for kind in ('cli','lib','http'):
        name=kind+'-demo';destination=parent/name;creator_case(binary,kind,destination,env,success=True,progress=progress)
        assert tree(destination)==expected(canonical,kind,name),kind
        original=tree(destination);creator_case(binary,kind,destination,env,success=False,progress=progress);assert tree(destination)==original
    destination=parent/('a'*64);creator_case(binary,'lib',destination,env,success=True,progress=progress);assert tree(destination)==expected(canonical,'lib','a'*64)
    destination=parent/'template-consumer';creator_case(binary,'lib',destination,env,success=True,progress=progress);assert tree(destination)==expected(canonical,'lib','template-consumer')
    sentinel=parent/'sentinel';sentinel.mkdir();(sentinel/'keep').write_bytes(b'unknown existing work\0')
    creator_case(binary,'cli',sentinel,env,success=False,progress=progress);assert (sentinel/'keep').read_bytes()==b'unknown existing work\0'
    empty=parent/'empty';empty.mkdir();creator_case(binary,'cli',empty,env,success=False,progress=progress);assert list(empty.iterdir())==[]
    regular=parent/'regular';regular.write_bytes(b'preserve');creator_case(binary,'cli',regular,env,success=False,progress=progress);assert regular.read_bytes()==b'preserve'
    for name in ('bad name','bad"name','bad$name','bad&name','é','9start','CON','nul','LPT9','COM1','x'*65):
        destination=parent/name;creator_case(binary,'cli',destination,env,success=False,progress=progress);assert not directory_has_entry(destination),name
    creator_case(binary,'unknown',parent/'unknown',env,success=False,progress=progress);assert not (parent/'unknown').exists()
    creator_case(binary,'cli',parent/'missing-parent'/'child',env,success=False,progress=progress);assert not (parent/'missing-parent').exists()
    if os.name!='nt':
        for name,target in [('linked',sentinel),('broken',parent/'absent')]:
            linked=parent/name;linked.symlink_to(target,target_is_directory=True);creator_case(binary,'cli',linked,env,success=False,progress=progress);assert linked.is_symlink()
        linkparent=root/'linkparent';linkparent.symlink_to(parent,target_is_directory=True)
        creator_case(binary,'cli',linkparent/'escape',env,success=False,progress=progress);assert not (parent/'escape').exists()
    # Two real creators race for one name. Publication must preserve one whole
    # generation and both creators must clean only their own staging tickets.
    destination=parent/'race';processes=[];records=[];results=[];partial={};primary=None
    try:
        for index in range(2):
            command=[str(binary),'cli',str(destination)]
            record=progress.process_record(command,cwd=parent,label='creator-race-'+str(index),timeout=10) if progress else {}
            records.append(record)
            child=subprocess.Popen(command,cwd=parent,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            processes.append(child);record.update(pid=child.pid,process_tree='taskkill /T' if os.name=='nt' else 'inherited parent process group')
            if progress:progress._write()
        for index,p in enumerate(processes):
            try:results.append(p.communicate(timeout=10))
            except BaseException as error:
                partial[index]=(getattr(error,'output',None) or b'',getattr(error,'stderr',None) or b'')
                raise
        assert sorted(out.startswith(b'OK\n') for out,err in results)==[False,True],results
        assert all(p.returncode==0 and not err for p,(out,err) in zip(processes,results)),results
    except BaseException as error:
        primary=error
        raise
    finally:
        recording_error=None
        for index,record in enumerate(records):
            child=processes[index] if index<len(processes) else None
            out,err=results[index] if index<len(results) else partial.get(index,(b'',b''))
            try:
                if child is not None:
                    recovered=cleanup_owned_child(child,record,timeout=10,primary=primary if primary is not None else recording_error,stdout=out,stderr=err)
                    if recovered is not None:out,err=recovered
                if progress:progress.process_finished(record,child,out,err,primary if primary is not None else recording_error)
            except BaseException as error:
                if primary is not None:TemplateProgress._note(primary,'Template race recording failed',error)
                elif recording_error is None:recording_error=error
        if primary is None and recording_error is not None:raise recording_error
    assert tree(destination)==expected(canonical,'cli','race')
    # The authoritative selector error cannot fall back to an ambient tree.
    failure_env=env.copy();failure_env['TEMPLATE_RUNTIME']='!freak-payload-resolution-error!ambiguous|root'
    creator_case(binary,'cli',parent/'resolution',failure_env,success=False,progress=progress);assert not (parent/'resolution').exists()
    variants=['missing','oversized','invalid-utf8','embedded-nul']
    if os.name!='nt':variants+=['linked-file','linked-template-root']
    for variant in variants:
        payload=root/variant;source=payload/'templates/v35/cli';shutil.copytree(canonical/'cli',source);(payload/'runtime').mkdir()
        readme=source/'README.md'
        if variant=='missing':readme.unlink()
        elif variant=='oversized':readme.write_bytes(b'x'*131073)
        elif variant=='invalid-utf8':readme.write_bytes(b'\xff')
        elif variant=='embedded-nul':readme.write_bytes(b'a\0b')
        elif variant=='linked-file':readme.unlink();readme.symlink_to(sentinel/'keep')
        else:shutil.rmtree(source);source.symlink_to(canonical/'cli',target_is_directory=True)
        failure_env=env.copy();failure_env['TEMPLATE_RUNTIME']=str(payload/'runtime')
        before=sorted(p.name for p in parent.iterdir());creator_case(binary,'cli',parent/('fail-'+variant),failure_env,success=False,progress=progress)
        assert sorted(p.name for p in parent.iterdir())==before,variant
        assert (sentinel/'keep').read_bytes()==b'unknown existing work\0'
    assert not any(p.name.startswith('freak-template-') for p in parent.iterdir()),list(parent.iterdir())
    return {'canonical_kinds':3,'no_clobber_and_race':True,'bounded_partial_failure_variants':len(variants),'unicode_parent':True,'library_max_name_and_consumer_identity':True,'source_template_sha256':{f'{kind}/{path}':hashlib.sha256(data).hexdigest() for kind in ('cli','lib','http') for path,data in tree(canonical/kind).items()}}

def http_once(cli:Path,project:Path,backend:str,env,progress=None):
    import socket
    child_env=env.copy();child_env['FREAK_HTTP_PORT']='0';child_env.pop('FREAK_HTTP_BIND',None);child_env.pop('FREAK_HTTP_ALLOW_NON_LOOPBACK',None)
    command=[str(cli),'run','--'+backend,'--','--once']
    record=progress.process_record(command,cwd=project,label='installed-http-once',timeout=30) if progress else {}
    child=None;primary=None;raw_lines=[];raw_out=raw_err=b''
    try:
        child=subprocess.Popen(command,cwd=project,env=child_env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)
        record.update(pid=child.pid,process_tree='taskkill /T' if os.name=='nt' else 'inherited parent process group')
        if progress:progress.stage('http-listen','http')
        assert child.stdout is not None;deadline=time.monotonic()+30;lines=[];port=None
        while time.monotonic()<deadline:
            if os.name!='nt' and not select.select([child.stdout],[],[],min(1,max(0,deadline-time.monotonic())))[0]:continue
            raw_line=child.stdout.readline();raw_lines.append(raw_line);line=text_channel(raw_line);lines.append(line)
            if line.startswith('HTTP http://127.0.0.1:'):port=int(line.rstrip().rsplit(':',1)[1]);break
            if not line and child.poll() is not None:break
        assert port,lines
        if progress:progress.stage('http-request','health')
        with socket.create_connection(('127.0.0.1',port),timeout=4) as client:
            client.sendall(request('/health'));wire=b''
            while data:=client.recv(4096):wire+=data
        assert_response(parse_response(wire),200,b'healthy')
        if progress:progress.stage('http-exit','http')
        raw_out,raw_err=child.communicate(timeout=10);out,err=text_channel(raw_out),text_channel(raw_err);assert child.returncode==0,(lines,out,err)
        assert not err,(lines,out,err)
    except BaseException as error:
        primary=error
        raw_out=getattr(error,'output',None) or raw_out;raw_err=getattr(error,'stderr',None) or raw_err
        raise
    finally:
        if child is not None:
            recovered=cleanup_owned_child(child,record,timeout=5,primary=primary,stdout=raw_out,stderr=raw_err)
            if recovered is not None:raw_out,raw_err=recovered
        if progress:progress.process_finished(record,child,b''.join(raw_lines)+raw_out,raw_err,primary)

def installed_corpus(cli:Path,canonical:Path,root:Path,env,backends,progress=None):
    report=progress.report['installed_cli_matrices'] if progress else []
    for kind in ('cli','lib','http'):
        name=kind+'-installed';project=root/name
        if progress:progress.matrix_started('installed-cli',fixture=kind)
        created=run([cli,'init',name,'--template='+kind],cwd=root,env=env,progress=progress,label='installed-init-'+kind);assert created.returncode==0,(created.stdout,created.stderr)
        assert tree(project)==expected(canonical,kind,name),(kind,tree(project).keys())
        preserved=tree(project);duplicate=run([cli,'init',name,'--template='+kind],cwd=root,env=env,progress=progress,label='installed-duplicate-'+kind);assert duplicate.returncode!=0,(kind,duplicate.stdout,duplicate.stderr);assert tree(project)==preserved
        for backend in backends:
            if progress:progress.matrix_started('installed-cli',backend,fixture=kind)
            tested=run([cli,'test','--'+backend],cwd=project,env=env,progress=progress,label='installed-test-'+kind);assert tested.returncode==0,(kind,backend,tested.stdout,tested.stderr)
            # Break the actual function and prove the generated named test fails.
            module=project/('src/routes.fk' if kind=='http' else 'src/greet.fk');original=module.read_text();module.write_text(original.replace('"Hello, "','"Broken, "'))
            failed=run([cli,'test','--'+backend],cwd=project,env=env,progress=progress,label='installed-failing-test-'+kind);assert failed.returncode!=0,(kind,backend,failed.stdout,failed.stderr);module.write_text(original)
            app=project/'examples/consumer' if kind=='lib' else project
            built=run([cli,'build','--'+backend],cwd=app,env=env,progress=progress,label='installed-build-'+kind);assert built.returncode==0,(kind,backend,built.stdout,built.stderr)
            if kind=='http':http_once(cli,app,backend,env,progress)
            else:
                command=[cli,'run','--'+backend]
                if kind=='cli':command+=['--','Ada $ & % \\']
                executed=run(command,cwd=app,env=env,progress=progress,label='installed-run-'+kind);assert executed.returncode==0,(kind,backend,executed.stdout,executed.stderr)
                expected_line='Hello, consumer!' if kind=='lib' else 'Hello, Ada $ & % \\!'
                assert expected_line in executed.stdout.splitlines(),executed.stdout
                if kind=='lib':assert executed.stdout.splitlines().count('Hello, consumer!')==1,executed.stdout
            if kind=='lib':
                tested=run([cli,'test','--'+backend],cwd=app,env=env,progress=progress,label='installed-consumer-test-'+kind);assert tested.returncode==0,(kind,backend,tested.stdout,tested.stderr)
            report.append({'template':kind,'backend':backend,'build_run_test':True,'failing_test_control':True})
            if progress:progress.matrix_finished()
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--compiler',type=Path,required=True);p.add_argument('--clang',default=os.environ.get('FREAK_CLANG','clang'));p.add_argument('--runtime-root',type=Path,required=True);p.add_argument('--templates-root',type=Path);p.add_argument('--optimization',type=int,choices=(0,2,3),action='append');p.add_argument('--backend',choices=('c','llvm'),action='append');p.add_argument('--sanitize',action='store_true');p.add_argument('--cli',type=Path);p.add_argument('--payload-home',type=Path);p.add_argument('--report',type=Path);args=p.parse_args()
    repo=Path(__file__).resolve().parents[1];canonical=(args.templates_root or repo/'templates/v35').resolve(strict=True);compiler=args.compiler.resolve(strict=True);runtime=args.runtime_root.resolve(strict=True)
    generator=(repo/'src/cli/templates.fk').read_text();backends=args.backend or ('c','llvm');env=os.environ.copy();env['ASAN_OPTIONS']='detect_leaks=1:halt_on_error=1';env['UBSAN_OPTIONS']='halt_on_error=1'
    vendor=runtime/'third_party/llhttp'
    if not vendor.exists():vendor=runtime.parents[1]/'third_party/llhttp'
    pinned=[compiler,repo/'src/cli/templates.fk',*sorted(p for p in canonical.rglob('*') if p.is_file()),*sorted(runtime.glob('*.c')),*sorted(runtime.glob('*.h')),*sorted(runtime.glob('*.inc')),*sorted(p for p in vendor.rglob('*') if p.is_file())]
    if args.cli:pinned.append(args.cli.resolve(strict=True))
    if args.payload_home:pinned+=sorted(p for p in args.payload_home.resolve(strict=True).rglob('*') if p.is_file())
    before={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in pinned}
    clang=Path(shutil.which(args.clang) or args.clang).resolve(strict=True)
    evidence={'compiler_sha256':before[str(compiler)],'generator_sha256':hashlib.sha256(generator.encode()).hexdigest(),'pinned_input_sha256':before,
        'clang':str(clang),'clang_sha256':hashlib.sha256(clang.read_bytes()).hexdigest(),
        'strict_borrow':True,'sanitize':args.sanitize}
    expected_creators=[{'backend':backend,'optimization':opt} for backend in backends for opt in args.optimization or (0,2,3)]
    expected_installed=[{'template':kind,'backend':backend} for kind in ('cli','lib','http') for backend in backends] if args.cli else []
    with TemplateProgress(args.report,evidence,expected_creators,expected_installed) as progress:
        tool_version=run([clang,'--version'],cwd=repo,progress=progress,label='clang-version');assert tool_version.returncode==0,(tool_version.stdout,tool_version.stderr)
        evidence['clang_version']=tool_version.stdout.splitlines()[0]
        with tempfile.TemporaryDirectory(prefix='freak-native-templates-') as temporary:
            root=Path(temporary).resolve(strict=True);source=root/'creator.fk';source.write_text(SELECTORS+'\n'+generator+'\n'+MAIN)
            if args.sanitize:
                control=root/'control.c';control.write_text('#include <stdlib.h>\nint main(int n,char **v){volatile char *p=malloc(1);p[n+4]=3;free((void*)p);return 0;}\n');binary=root/'control'
                linked=run([args.clang,control,'-O0','-fsanitize=address,undefined','-o',binary],cwd=root,progress=progress,label='sanitizer-control-link');assert linked.returncode==0,(linked.stdout,linked.stderr)
                failed=run([binary],cwd=root,env=env,progress=progress,label='sanitizer-failing-control');assert failed.returncode!=0 and 'AddressSanitizer' in failed.stderr,failed.stderr;evidence['sanitizer_failing_control']=True
            for backend in backends:
                progress.matrix_started('creator',backend)
                compiled=run([compiler,source,'--'+backend,'--strict-borrow'],cwd=root,progress=progress,label='creator-compile-'+backend);assert compiled.returncode==0,(compiled.stdout,compiled.stderr)
                generated=Path(str(source)+('.c' if backend=='c' else '.ll'))
                for opt in args.optimization or (0,2,3):
                    progress.matrix_started('creator',backend,opt)
                    binary=root/f'creator-{backend}-O{opt}';command=[args.clang,'-O'+str(opt),generated,runtime/'freak_runtime.c','-I'+str(runtime),'-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1','-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1','-o',binary]
                    if args.sanitize:command+=['-fsanitize=address,undefined,function','-fno-omit-frame-pointer','-g']
                    if backend=='llvm':command.append(runtime/'freak_llvm_runtime.c')
                    command+=['-lws2_32','-lshell32'] if os.name=='nt' else ['-lm']
                    linked=run(command,cwd=root,progress=progress,label='creator-link');assert linked.returncode==0,(linked.stdout,linked.stderr)
                    scratch=root/f'cases-{backend}-O{opt}';scratch.mkdir();corpus=creator_corpus(binary,canonical,scratch,env,progress)
                    evidence['creator_matrices'].append({'backend':backend,'optimization':opt,'corpus':corpus});progress.matrix_finished();print(f'PASS native template creator {backend} O{opt}: fixed canonical bytes,owned staging,no-clobber,race,links,bounded failures',flush=True)
            if args.cli:
                cli=args.cli.resolve(strict=True);cli_env=env.copy()
                if args.payload_home:cli_env['FREAK_HOME']=str(args.payload_home.resolve(strict=True))
                projects=root/'installed-projects';projects.mkdir();evidence['installed_cli_matrices']=installed_corpus(cli,canonical,projects,cli_env,backends,progress);evidence['installed_cli_verified']=True;evidence['cli_sha256']=hashlib.sha256(cli.read_bytes()).hexdigest()
        progress.stage('input-verification')
        after={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in pinned};assert before==after,'pinned compiler/runtime/templates changed during gate';evidence['pinned_inputs_unchanged']=True
        progress.passed()
if __name__=='__main__':main()
