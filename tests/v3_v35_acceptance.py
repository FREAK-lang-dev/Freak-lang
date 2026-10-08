#!/usr/bin/env python3
"""Exercise permanent projects through a supplied, extracted native archive.

No compiler reconstruction or source concatenation occurs here. The independent
client checks HTTP wire bytes and JSON values. These are package/service/testing
component gates; bootstrap, V4 syntax parity and full release acceptance remain
separate gates. A provisional archive requires explicit opt-in and stays labeled.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import queue
import re
import shutil
import socket
import subprocess
import tarfile
import tempfile
import threading
import time
import tomllib
import zipfile


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root: Path) -> dict[str, str]:
    assert root.is_dir() and not root.is_symlink(), root
    assert all(not path.is_symlink() for path in root.rglob('*')), 'input tree contains a symlink'
    return {path.relative_to(root).as_posix(): sha(path)
            for path in sorted(root.rglob('*')) if path.is_file()}


def archive_payload(archive: Path) -> dict[str, bytes]:
    """Read ordinary, uniquely named archive files without trusting extraction."""
    files: dict[str, bytes] = {}

    def admit(name: str, data: bytes) -> None:
        path = PurePosixPath(name)
        assert name.startswith('freak/') and '..' not in path.parts, name
        relative = name[6:]
        assert relative and relative not in files, name
        files[relative] = data

    if archive.name.endswith('.zip'):
        with zipfile.ZipFile(archive) as source:
            for entry in source.infolist():
                if not entry.is_dir():
                    assert (entry.external_attr >> 16) & 0o170000 in (0, 0o100000), entry.filename
                    admit(entry.filename, source.read(entry))
    else:
        with tarfile.open(archive) as source:
            for entry in source.getmembers():
                assert entry.isdir() or entry.isfile(), entry.name
                if entry.isfile():
                    stream = source.extractfile(entry)
                    assert stream is not None
                    admit(entry.name, stream.read())
    assert files, 'archive has no product files'
    return files


def request(port: int, wire: bytes, *, head: bool = False,
            cuts: tuple[int, ...] = (), end_stream: bool = False,
            delay: float = 0, transcript: Path | None = None,
            ) -> tuple[int, dict[bytes, bytes], bytes, bytes, str]:
    response = bytearray()
    termination = 'incomplete'
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=10) as peer:
            peer.settimeout(10)
            start = 0
            for end in (*cuts, len(wire)):
                assert start <= end <= len(wire)
                peer.sendall(wire[start:end])
                start = end
                if delay and start < len(wire):
                    time.sleep(delay)
            if end_stream:
                peer.shutdown(socket.SHUT_WR)
            while True:
                try:
                    part = peer.recv(65536)
                except ConnectionResetError:
                    # A rejection may close with unread request bytes. A reset
                    # is usable only when the response below is fully framed.
                    termination = 'reset'
                    break
                if not part:
                    termination = 'eof'
                    break
                response.extend(part)
                assert len(response) <= 1048576, 'unbounded response'
    finally:
        if transcript is not None:
            transcript.with_suffix('.request').write_bytes(wire)
            transcript.with_suffix('.response').write_bytes(response)
            transcript.with_suffix('.transport.json').write_text(json.dumps({'termination': termination, 'response_bytes': len(response)}) + '\n')
    header, boundary, body = bytes(response).partition(b'\r\n\r\n')
    assert boundary, response
    lines = header.split(b'\r\n')
    assert lines[0].startswith(b'HTTP/1.1 '), lines[0]
    status = int(lines[0].split(b' ')[1])
    fields: dict[bytes, bytes] = {}
    for line in lines[1:]:
        name, separator, value = line.partition(b':')
        assert separator and name.lower() not in fields, line
        fields[name.lower()] = value.strip()
    assert fields.get(b'connection', b'').lower() == b'close', fields
    length = int(fields[b'content-length'])
    assert length >= 0, fields
    assert len(body) == (0 if head else length), (status, fields, body)
    return status, fields, body, bytes(response), termination


def startup(child: subprocess.Popen[bytes], transcript: Path) -> tuple[int, bytes]:
    assert child.stdout is not None
    # Windows selectors cannot select ordinary anonymous pipe handles.
    lines: queue.Queue[bytes] = queue.Queue()
    threading.Thread(target=lambda: lines.put(child.stdout.readline(4096)), daemon=True).start()
    try:
        line = lines.get(timeout=15)
    except queue.Empty as error:
        raise AssertionError('service startup exceeded 15 seconds') from error
    transcript.write_bytes(line)
    assert line.startswith(b'HTTP http://127.0.0.1:') and line.endswith(b'\n'), line
    return int(line.strip().rsplit(b':', 1)[1]), line


def test_summary(process: subprocess.CompletedProcess[bytes], *, passed: bool,
                 kind: str | None = None) -> dict:
    assert not process.stderr, process.stderr
    report = json.loads(process.stdout)
    assert report['schema'] == 1 and len(report['cases']) == 1, report
    assert report['summary'] == {'total': 1, 'passed': int(passed), 'failed': int(not passed)}, report
    assert report['error'] == '', report
    case = report['cases'][0]
    assert case['build'] is not None, case
    for phase in ('build', 'run'):
        child = case[phase]
        if child is not None:
            assert child['encoding'] == 'hex', child
            for stream in ('stdout', 'stderr'):
                assert len(bytes.fromhex(child[stream + '_hex'])) == child[stream + '_bytes'], child
    if passed:
        assert case['status'] == 'passed' and case['run'] is not None, case
        for phase in ('build', 'run'):
            child = case[phase]
            assert child['status'] == 'passed' and child['process_status'] == 2, child
            assert child['exit_code'] == 0 and child['signal'] is None and not child['timed_out'], child
    elif kind in ('named', 'exit'):
        child = case['run']
        assert case['status'] == child['status'] == 'failed' and child['process_status'] == 2, case
        assert child['signal'] is None and not child['timed_out'], child
    if kind == 'named':
        assert case['run']['exit_code'] == 1, case
        assert b'TEST FAILED [acceptance mismatch]' in bytes.fromhex(case['run']['stdout_hex']), case
    elif kind == 'exit':
        assert case['run']['exit_code'] == 7, case
        assert bytes.fromhex(case['run']['stdout_hex']) == b'preserved child output\n', case
    elif kind == 'timeout':
        assert case['run']['process_status'] == 5 and case['run']['timed_out'], case
        assert case['run']['exit_code'] is None, case
    elif kind == 'compile':
        assert case['status'] == 'build_failed' and case['run'] is None, case
        assert case['build']['exit_code'] != 0, case
    return report


def diamond_lock(project: Path) -> bytes:
    """Observe the public lock without calling the producer's graph helpers."""
    raw = (project / 'hangar.lock').read_bytes()
    lock = tomllib.loads(raw.decode('utf-8'))
    assert lock['lock']['schema'] == 2 and lock['lock']['node_count'] == 4, lock['lock']
    assert lock['lock']['edge_count'] == 4, lock['lock']
    nodes = lock['node']
    assert {node['name'] for node in nodes.values()} == {'package-consumer', 'diamond-left', 'diamond-right', 'diamond-core'}, nodes
    core = next(int(index) for index, node in nodes.items() if node['name'] == 'diamond-core')
    parents = {int(index) for index, node in nodes.items() if node['name'] in ('diamond-left', 'diamond-right')}
    shared = [edge for edge in lock['edge'].values() if edge['alias'] == 'core']
    assert len(shared) == 2 and {edge['parent'] for edge in shared} == parents, shared
    assert {edge['target'] for edge in shared} == {core}, shared
    return raw


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freak', type=Path, required=True)
    parser.add_argument('--payload-home', type=Path, required=True)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--allow-provisional', action='store_true')
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--clang', type=Path, required=True)
    parser.add_argument('--story', choices=('package', 'service', 'testing', 'freshness'), action='append')
    parser.add_argument('--backend', choices=('c', 'llvm'), action='append')
    parser.add_argument('--soak', type=int, default=1000)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if not 100 <= args.soak <= 3000:
        parser.error('--soak must be 100..3000')
    stories = args.story or ['package', 'service', 'testing']
    backends = args.backend or ['c', 'llvm']
    assert len(stories) == len(set(stories)) and len(backends) == len(set(backends)), 'duplicate selections'
    repo = args.repo.resolve(strict=True)
    candidate = args.freak.resolve(strict=True)
    home = args.payload_home.resolve(strict=True)
    archive = args.archive.resolve(strict=True)
    clang = args.clang.resolve(strict=True)
    assert candidate == home / ('freak.exe' if os.name == 'nt' else 'freak'), 'use the extracted archive CLI'
    assert not home.is_relative_to(repo), 'payload must be outside the source checkout'
    report_path = args.report.resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    logs = report_path.parent / (report_path.stem + '-logs')
    logs.mkdir(exist_ok=False)
    fixtures_source = repo / 'examples/v35'
    before = inventory(fixtures_source)
    payload_before = inventory(home)
    report: dict = {'schema': 1, 'status': 'RUNNING', 'scope': 'package/service/testing component acceptance',
                    'stories': stories, 'backends': backends, 'candidate_sha256': sha(candidate),
                    'archive_sha256': sha(archive), 'clang': str(clang), 'clang_sha256': sha(clang),
                    'driver_sha256': sha(Path(__file__)), 'payload_inputs': payload_before,
                    'fixture_inputs': before, 'commands': [], 'records': []}
    report['separate_required_gates'] = ['native platform matrix', 'sanitizers and allocation counters',
                                        'full adversarial HTTP corpus', 'public Git/Hangar commands',
                                        'bootstrap B', 'development V4 syntax L', 'final release archive']
    if 'freshness' not in stories:
        report['separate_required_gates'].append('transitive run freshness: select --story=freshness')
    started = time.monotonic()
    env = dict(os.environ, FREAK_HOME=str(home), FREAK_CLANG=str(clang), NO_COLOR='1', FREAK_ASCII='1')
    # Explicit payload/tool selection must not inherit unrelated user overrides.
    for name in ('FREAK_RUNTIME_DIR', 'FREAK_STD_DIR', 'FREAK_DOCTOR_INSTALL_COMMAND'):
        env.pop(name, None)

    def run(command: list[str], *, cwd: Path, label: str, expected: int = 0,
            timeout: int = 180) -> subprocess.CompletedProcess[bytes]:
        serial = len(report['commands']) + 1
        prefix = logs / f'{serial:03}-{label}'
        began = time.monotonic()
        child = subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            stdout, stderr = child.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            child.kill()
            stdout, stderr = child.communicate(timeout=10)
            prefix.with_suffix('.stdout').write_bytes(stdout)
            prefix.with_suffix('.stderr').write_bytes(stderr)
            report['commands'].append({'case': label, 'argv': command, 'cwd': str(cwd),
                                       'pid': child.pid, 'returncode': child.returncode, 'timed_out': True})
            raise
        prefix.with_suffix('.stdout').write_bytes(stdout)
        prefix.with_suffix('.stderr').write_bytes(stderr)
        report['commands'].append({'case': label, 'argv': command, 'cwd': str(cwd), 'pid': child.pid,
                                   'returncode': child.returncode, 'expected': expected,
                                   'elapsed_seconds': time.monotonic() - began,
                                   'stdout_sha256': hashlib.sha256(stdout).hexdigest(),
                                   'stderr_sha256': hashlib.sha256(stderr).hexdigest()})
        assert child.returncode == expected, (label, child.returncode, stdout[-4000:], stderr[-4000:])
        return subprocess.CompletedProcess(command, child.returncode, stdout, stderr)

    try:
        files = archive_payload(archive)
        assert payload_before == {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}, 'extracted payload differs from archive'
        info = json.loads(files['build-info.json'])
        assert not info['provisional'] or args.allow_provisional, 'provisional candidate requires --allow-provisional'
        report['archive_provenance'] = info
        report['release_acceptance'] = False
        with tempfile.TemporaryDirectory(prefix='freak-v35-acceptance-') as temporary:
            root = Path(temporary).resolve()
            fixtures = root / "projects é 日本 ' $ &"
            shutil.copytree(fixtures_source, fixtures)
            binaries = root / 'native-output'
            binaries.mkdir()
            unrelated = root / 'unrelated-working-directory'
            unrelated.mkdir()
            doctor = json.loads(run([str(candidate), 'doctor', '--json'], cwd=unrelated, label='extracted-doctor').stdout)
            assert doctor['status'] == 'ok' and doctor['checks']['clang']['probe_ok'], doctor
            assert doctor['checks']['runtime']['ok'], doctor
            for backend in backends:
                suffix = '.exe' if os.name == 'nt' else ''
                if 'package' in stories:
                    library = fixtures / 'freak-sequences'
                    test_summary(run([str(candidate), 'test', '--' + backend, '--jobs=2', '--json'], cwd=library, label='library-test-' + backend), passed=True)
                    report['records'].append({'case': 'library-test-' + backend, 'status': 'PASS'})
                if 'package' in stories or 'testing' in stories:
                    project = fixtures / 'package-consumer'
                    binary = binaries / ('diamond-' + backend + suffix)
                    build = [str(candidate), 'build', '--' + backend, '--strict-borrow', '--output=' + str(binary)]
                    run(build, cwd=project, label='diamond-build-' + backend)
                    lock = diamond_lock(project)
                    (logs / ('diamond-' + backend + '.lock')).write_bytes(lock)
                    result = run([str(binary)], cwd=unrelated, label='diamond-run-' + backend)
                    assert result.stdout.replace(b'\r\n', b'\n') == b'42\n' and not result.stderr, result
                    test = [str(candidate), 'test', '--' + backend, '--jobs=2', '--json']
                    tested = run([*test, '--frozen'], cwd=project, label='diamond-test-' + backend)
                    test_summary(tested, passed=True)
                    if 'package' in stories:
                        source = project / 'src/main.fk'
                        original = source.read_bytes()
                        try:
                            source.write_text('use core::{seed}\ntask main(){say seed()}\n', encoding='utf-8')
                            run(build, cwd=project, label='undeclared-transitive-' + backend, expected=1)
                            assert not binary.exists(), 'failed build retained a success binary'
                        finally:
                            source.write_bytes(original)
                        run(build, cwd=project, label='diamond-recovery-' + backend)
                        run([*build, '--frozen', '--offline'], cwd=project, label='diamond-frozen-offline-' + backend)
                        report['records'].append({'case': 'package-' + backend, 'status': 'PASS'})
                    if 'testing' in stories:
                        source = project / 'tests/diamond_test.fk'
                        original = source.read_bytes()
                        controls = {
                            'named': 'use std::test::{test_assert_int}\ntask main(){test_assert_int("acceptance mismatch",1,2)}\n',
                            'exit': 'task main(){say "preserved child output";process::exit(7)}\n',
                            'compile': 'task main(){say acceptance_missing_name}\n',
                            'timeout': 'task main(){repeat until false {}}\n',
                        }
                        try:
                            for kind, program in controls.items():
                                source.write_text(program, encoding='utf-8')
                                options = ['--timeout-ms=250'] if kind == 'timeout' else []
                                failed = run([*test, *options], cwd=project, label='test-' + kind + '-' + backend, expected=1)
                                test_summary(failed, passed=False, kind=kind)
                        finally:
                            source.write_bytes(original)
                        test_summary(run(test, cwd=project, label='test-recovery-' + backend), passed=True)
                        report['records'].append({'case': 'testing-' + backend, 'status': 'PASS', 'controls': list(controls)})
                if 'freshness' in stories:
                    project = fixtures / 'package-consumer'
                    command = [str(candidate), 'run', '--' + backend, '--strict-borrow']
                    first = run(command, cwd=project, label='freshness-before-' + backend)
                    assert re.findall(rb'(?m)^42\r?$', first.stdout), first.stdout
                    source = project / 'core/src/core.fk'
                    original = source.read_bytes()
                    probe = {'backend': backend, 'source': 'package-consumer/core/src/core.fk',
                             'original_sha256': hashlib.sha256(original).hexdigest()}
                    report.setdefault('freshness_probes', []).append(probe)
                    try:
                        source.write_bytes(original.replace(b'back 20', b'back 21'))
                        assert source.read_bytes() != original
                        probe['modified_sha256'] = sha(source)
                        (logs / ('freshness-edited-core-' + backend + '.fk')).write_bytes(source.read_bytes())
                        second = run(command, cwd=project, label='freshness-after-' + backend)
                        binary = binaries / ('freshness-control-' + backend + suffix)
                        run([str(candidate), 'build', '--' + backend, '--strict-borrow', '--output=' + str(binary)], cwd=project, label='freshness-control-build-' + backend)
                        rebuilt = run([str(binary)], cwd=unrelated, label='freshness-control-run-' + backend)
                        assert rebuilt.stdout.replace(b'\r\n', b'\n') == b'44\n' and not rebuilt.stderr, rebuilt
                        assert re.findall(rb'(?m)^44\r?$', second.stdout), ('transitive dependency edit ran stale output', second.stdout)
                    finally:
                        source.write_bytes(original)
                        probe['restored_sha256'] = sha(source)
                        assert probe['restored_sha256'] == probe['original_sha256']
                    report['records'].append({'case': 'freshness-' + backend, 'status': 'PASS'})
                if 'service' in stories:
                    project = fixtures / 'sequence-service'
                    binary = binaries / ('service-' + backend + suffix)
                    run([str(candidate), 'build', '--' + backend, '--strict-borrow', '--output=' + str(binary)], cwd=project, label='service-build-' + backend)
                    test_summary(run([str(candidate), 'test', '--' + backend, '--jobs=2', '--json', '--frozen'], cwd=project, label='service-test-' + backend), passed=True)
                    controls: list[tuple[bytes, int, object, bool]] = [
                        (b'GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n', 200, b'healthy', False),
                        (b'HEAD /health HTTP/1.1\r\nHost: localhost\r\n\r\n', 200, b'', True),
                        (b'GET /missing HTTP/1.1\r\nHost: localhost\r\n\r\n', 404, b'missing', False),
                        (b'PUT /health HTTP/1.1\r\nHost: localhost\r\n\r\n', 405, b'method not allowed', False),
                        (b'GET /sequences/arithmetic?start=2&step=3&count=5 HTTP/1.1\r\nHost: localhost\r\n\r\n', 200, {'values': [2, 5, 8, 11, 14]}, False),
                        (b'GET /sequences/arithmetic?start=2&step=bad&count=5 HTTP/1.1\r\nHost: localhost\r\n\r\n', 422, None, False),
                        (b'GET /sequences/arithmetic?start=2&step=1&step=2&count=5 HTTP/1.1\r\nHost: localhost\r\n\r\n', 422, None, False),
                        (b'GET /health HTTP/1.1\r\nHost: a\r\nHost: b\r\n\r\n', 400, None, False),
                        (b'POST /sequences/arithmetic HTTP/1.1\r\nHost: localhost\r\nTransfer-Encoding: chunked\r\nContent-Length: 0\r\n\r\n', 400, None, False),
                    ]
                    for body, expected, oracle in (
                        (b'{"start":2,"step":3,"count":5}', 200, {'values': [2, 5, 8, 11, 14]}),
                        (b'{"start":2,"step":-3,"count":3}', 200, {'values': [2, -1, -4]}),
                        ('{"start":2,"step":3,"count":3,"note":"雪\\n\\\""}'.encode(), 200, {'values': [2, 5, 8]}),
                        (b'{"start":2,"step":3,"count":0}', 422, None),
                        (b'{"start":2,"step":3,"count":"5"}', 422, None),
                        (b'{"start":2,"start":4,"step":3,"count":5}', 400, None),
                        (b'{"start":2,"step":3,"count":5}junk', 400, None),
                        (b'{"start":"\\ud800","step":3,"count":5}', 400, None),
                    ):
                        wire = b'POST /sequences/arithmetic HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: ' + str(len(body)).encode() + b'\r\n\r\n' + body
                        controls.append((wire, expected, oracle, False))
                    binary_body = b'a\x00' + '雪'.encode() + b'\xff'
                    echo_header = b'POST /echo HTTP/1.1\r\nHost: localhost\r\nContent-Length: '
                    controls.append((echo_header + str(len(binary_body)).encode() + b'\r\n\r\n' + binary_body, 200, binary_body, False))
                    controls.append((echo_header + b'8193\r\n\r\n', 413, None, False))
                    chunked = b'POST /echo HTTP/1.1\r\nHost: localhost\r\nTransfer-Encoding: chunked\r\n\r\n3\r\na\x00b\r\n0\r\n\r\n'
                    controls.append((chunked, 200, b'a\x00b', False))
                    adverse = [
                        ('premature-body', echo_header + b'8\r\n\r\na', 400, {'end_stream': True}),
                        ('idle-peer', b'', 408, {}),
                        ('absolute-trickle', b'GET /', 408, {'cuts': (1, 2, 3, 4), 'delay': 0.22}),
                    ]
                    total = len(controls) + len(adverse) + args.soak
                    child = subprocess.Popen([str(binary), '--requests', str(total)], cwd=unrelated, env=dict(env, FREAK_HTTP_PORT='0'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    first_line = b''
                    service_started = time.monotonic()
                    wire_records: list[dict] = []
                    soak_digest = hashlib.sha256()
                    try:
                        port, first_line = startup(child, logs / ('service-' + backend + '.startup'))
                        plateau: list[dict[str, int]] = []
                        for index, (wire, expected, oracle, head) in enumerate(controls):
                            status, fields, body, raw, termination = request(port, wire, head=head, cuts=(1, len(wire) // 2, len(wire) - 1), transcript=logs / f'http-{backend}-{index:03}')
                            wire_records.append({'case': index, 'status': status, 'expected': expected,
                                                 'termination': termination,
                                                 'request_sha256': hashlib.sha256(wire).hexdigest(),
                                                 'response_sha256': hashlib.sha256(raw).hexdigest()})
                            assert status == expected, (index, status, expected, body)
                            if head:
                                assert fields[b'content-length'] == b'7', fields
                            if status == 405:
                                assert fields.get(b'allow') == b'GET, HEAD'
                            if isinstance(oracle, dict):
                                assert fields[b'content-type'] == b'application/json' and json.loads(body) == oracle
                            elif oracle is not None:
                                assert body == oracle
                        for label, wire, expected, options in adverse:
                            began = time.monotonic()
                            status, _, body, raw, termination = request(port, wire, transcript=logs / f'http-{backend}-{label}', **options)
                            elapsed = time.monotonic() - began
                            wire_records.append({'case': label, 'status': status, 'expected': expected,
                                                 'termination': termination,
                                                 'elapsed_seconds': elapsed,
                                                 'request_sha256': hashlib.sha256(wire).hexdigest(),
                                                 'response_sha256': hashlib.sha256(raw).hexdigest()})
                            assert status == expected, (label, status, expected, body)
                            if label == 'absolute-trickle':
                                assert 0.8 <= elapsed < 2, ('absolute header deadline', elapsed)
                        for index in range(args.soak):
                            status, _, body, raw, termination = request(port, controls[4][0])
                            soak_digest.update(raw)
                            assert termination == 'eof' and status == 200 and json.loads(body) == {'values': [2, 5, 8, 11, 14]}
                            if Path(f'/proc/{child.pid}/status').exists() and 50 <= index < args.soak - 1 and index % 50 == 0:
                                details = Path(f'/proc/{child.pid}/status').read_text().splitlines()
                                rss = next(int(line.split()[1]) for line in details if line.startswith('VmRSS:'))
                                plateau.append({'request': index, 'rss_kib': rss, 'open_descriptors': len(list(Path(f'/proc/{child.pid}/fd').iterdir()))})
                        output, errors = child.communicate(timeout=15)
                        assert child.returncode == 0 and not output and not errors, (child.returncode, output, errors)
                        if plateau:
                            assert max(row['open_descriptors'] for row in plateau) - min(row['open_descriptors'] for row in plateau) <= 1, plateau
                            assert max(row['rss_kib'] for row in plateau) - min(row['rss_kib'] for row in plateau) <= 4096, plateau
                        report['records'].append({'case': 'service-' + backend, 'status': 'PASS', 'pid': child.pid,
                                                  'requests': total, 'wire_controls': wire_records,
                                                  'soak_response_sha256': soak_digest.hexdigest(), 'plateau': plateau,
                                                  'resource_scope': 'Linux FD/RSS observations when available; allocation counters are separate'})
                    finally:
                        if child.poll() is None:
                            child.terminate()
                            try:
                                child.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                child.kill()
                                child.wait(timeout=5)
                        output, errors = child.communicate(timeout=5)
                        (logs / ('service-' + backend + '.stdout')).write_bytes(first_line + output)
                        (logs / ('service-' + backend + '.stderr')).write_bytes(errors)
                        report['commands'].append({'case': 'service-process-' + backend,
                                                   'argv': [str(binary), '--requests', str(total)],
                                                   'cwd': str(unrelated), 'pid': child.pid, 'returncode': child.returncode,
                                                   'elapsed_seconds': time.monotonic() - service_started,
                                                   'stdout_sha256': hashlib.sha256(first_line + output).hexdigest(),
                                                   'stderr_sha256': hashlib.sha256(errors).hexdigest(), 'wire_controls': wire_records})
            report['status'] = 'PASS'
    except BaseException as error:
        report['status'] = 'FAIL'
        report['error'] = repr(error)
        raise
    finally:
        report['fixture_inputs_unchanged'] = before == inventory(fixtures_source)
        report['payload_inputs_unchanged'] = payload_before == inventory(home)
        report['candidate_unchanged'] = report['candidate_sha256'] == sha(candidate)
        report['archive_unchanged'] = report['archive_sha256'] == sha(archive)
        report['elapsed_seconds'] = time.monotonic() - started
        unchanged = all(report[key] for key in ('fixture_inputs_unchanged', 'payload_inputs_unchanged', 'candidate_unchanged', 'archive_unchanged'))
        if not unchanged:
            report['status'] = 'FAIL'
        report_path.write_text(json.dumps(report, indent=2) + '\n')
        assert unchanged, 'immutable inputs changed during acceptance'
    print(json.dumps({key: report[key] for key in ('status', 'stories', 'backends', 'elapsed_seconds')}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
