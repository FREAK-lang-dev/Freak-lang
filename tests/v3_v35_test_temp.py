#!/usr/bin/env python3
"""Qualify system temporary-parent admission through a supplied installed CLI.

No compiler reconstruction, source concatenation or runtime replacement occurs.
The public `freak test` command builds/runs one ordinary declared native test.
POSIX aliases deliberately retain their spelling in TMPDIR. An optional old
CLI supplies the physical-parent positive and alias-refusal counterfactual.
Each invocation needs a new evidence directory; failed receipts stay intact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

from v3_v35_acceptance import inventory, run_command, sha


PROGRAM = ('task main() { say "SYSTEM_TEMP_ADMISSION_OK"; '
           'say process::executable_path() }\n')
OUTPUT = b'SYSTEM_TEMP_ADMISSION_OK'
MANIFEST = ('[project]\nname = "temporary_parent_probe"\nversion = "1.0.0"\n'
            'entry = "src/main.fk"\n[tests]\n'
            'temporary_parent = "tests/temporary_parent.fk"\n')


def write_report(path: Path, report: dict) -> None:
    staged = path.with_suffix('.next')
    with staged.open('w', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    staged.replace(path)


def result_report(process, *, passed: bool, selected: Path,
                  physical_parent: Path, failure: str | None = None) -> dict:
    assert not process.stderr, (process.returncode, process.stdout, process.stderr)
    report = json.loads(process.stdout)
    assert report['schema'] == 1, report
    if not passed:
        assert process.returncode == 1 and report['cases'] == [], report
        assert report['summary'] == {'total': 0, 'passed': 0, 'failed': 0}, report
        assert isinstance(report['error'], str) and report['error'], report
        if failure is not None:
            assert report['error'].startswith(failure), report
            assert str(selected) in report['error'], report
        return report
    assert process.returncode == 0 and report['error'] == '', report
    assert report['summary'] == {'total': 1, 'passed': 1, 'failed': 0}, report
    assert len(report['cases']) == 1, report
    case = report['cases'][0]
    assert case['name'] == 'temporary_parent' and case['status'] == 'passed', case
    for phase in ('build', 'run'):
        child = case[phase]
        assert child['process_status'] == 2 and child['exit_code'] == 0, child
        assert child['encoding'] == 'hex' and not child['timed_out'], child
        assert len(bytes.fromhex(child['stdout_hex'])) == child['stdout_bytes'], child
        assert len(bytes.fromhex(child['stderr_hex'])) == child['stderr_bytes'], child
    assert bytes.fromhex(case['run']['stderr_hex']) == b'', case
    output = bytes.fromhex(case['run']['stdout_hex'])
    lines = output.splitlines()
    assert len(lines) == 2 and lines[0] == OUTPUT, case
    executed = Path(lines[1].decode('utf-8'))
    assert executed.is_absolute() and executed.name == ('test_0.exe' if os.name == 'nt' else 'test_0'), executed
    assert executed.parent.name.startswith('freak-tests-'), executed
    assert executed.parent.parent.resolve() == physical_parent, executed
    assert output == OUTPUT + b'\n' + lines[1] + b'\n', output
    return report


def check_inputs(project: Path, physical_parent: Path, pins: dict[str, str]) -> None:
    assert all(sha(project / path) == digest for path, digest in pins.items()), pins
    assert not list(physical_parent.glob('freak-tests-*')), physical_parent
    assert inventory(physical_parent) == {'sentinel': hashlib.sha256(b'preserve temp parent\n').hexdigest()}
    for folder in ('src', 'tests'):
        assert sorted(path.name for path in (project / folder).iterdir()) == (
            ['main.fk'] if folder == 'src' else ['temporary_parent.fk'])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('freak', type=Path, help='actual installed native candidate; never rebuilt')
    parser.add_argument('--payload-home', type=Path, required=True)
    parser.add_argument('--clang', type=Path, required=True)
    parser.add_argument('--baseline-cli', type=Path)
    parser.add_argument('--backend', choices=('both', 'c', 'llvm'), default='both')
    parser.add_argument('--evidence-dir', type=Path, required=True, help='new receipt directory, never reused')
    args = parser.parse_args()
    freak = args.freak.resolve(strict=True)
    home = args.payload_home.resolve(strict=True)
    clang = args.clang.resolve(strict=True)
    baseline = args.baseline_cli.resolve(strict=True) if args.baseline_cli else None
    evidence = args.evidence_dir
    evidence.mkdir(parents=True)  # Refuse receipt overwrite, including an existing failed run.
    evidence = evidence.resolve(strict=True)
    root = evidence / 'fixtures'
    root.mkdir()
    project = root / 'project'
    (project / 'src').mkdir(parents=True)
    (project / 'tests').mkdir()
    (project / 'hangar.toml').write_text(MANIFEST, encoding='utf-8')
    (project / 'src/main.fk').write_text('task main() { say "APP_ENTRY_MUST_NOT_RUN" }\n', encoding='utf-8')
    (project / 'tests/temporary_parent.fk').write_text(PROGRAM, encoding='utf-8')
    fixture_pins = inventory(project)
    physical = root / 'physical temp & parent'
    physical.mkdir()
    (physical / 'sentinel').write_bytes(b'preserve temp parent\n')
    missing = root / 'absent-parent'
    regular = root / 'regular-parent'
    regular.write_bytes(b'preserve regular parent\n')
    aliases = []
    if os.name == 'posix':
        direct = root / 'alias-parent'
        direct.symlink_to(physical, target_is_directory=True)
        ancestor = root / 'alias-ancestor'
        ancestor.symlink_to(root, target_is_directory=True)
        aliases = [('final-alias', direct), ('ancestor-alias', ancestor / physical.name)]
    env = os.environ.copy()
    env.update(FREAK_HOME=str(home), FREAK_CLANG=str(clang), NO_COLOR='1')
    capture_helper = Path(run_command.__code__.co_filename).resolve(strict=True)
    report = {'schema': 1, 'outcome': 'running', 'host': sys.platform,
              'candidate': {'path': str(freak), 'sha256': sha(freak)},
              'baseline': {'path': str(baseline), 'sha256': sha(baseline)} if baseline else None,
              'clang': {'path': str(clang), 'sha256': sha(clang)},
              'payload_home': str(home), 'payload_pins': {
                  'runtime': inventory(home / 'runtime'), 'std': inventory(home / 'std')},
              'fixture_pins': fixture_pins, 'gate_sha256': sha(Path(__file__)),
              'capture_helper': {'path': str(capture_helper), 'sha256': sha(capture_helper)},
              'cases': [], 'commands': [],
              'skips': [] if aliases else ['POSIX temporary-parent alias controls unavailable on this host']}
    report_path = evidence / 'report.json'

    def probe(cli: Path, backend: str, name: str, selected: Path, *,
              passed: bool, locked: bool = True, failure: str | None = None) -> None:
        case_env = {**env, 'TMPDIR': str(selected), 'TEMP': str(selected), 'TMP': str(selected)}
        command = [str(cli), 'test', f'--manifest-path={project / "hangar.toml"}',
                   f'--{backend}', '--jobs=1', '--timeout-ms=30000',
                   '--stdout-limit=1048576', '--stderr-limit=1048576', '--json']
        if locked:
            command += ['--locked', '--offline']
        report['active'] = {'case': name, 'backend': backend, 'selected_parent': str(selected)}
        write_report(report_path, report)
        process = run_command(command, cwd=root, env=case_env, label=f'{backend}-{name}',
                              prefix=evidence / f'{backend}-{name}', records=report['commands'],
                              expected=0 if passed else 1, timeout=180,
                              on_record=lambda _: write_report(report_path, report))
        parsed = result_report(process, passed=passed, selected=selected,
                               physical_parent=physical, failure=failure)
        check_inputs(project, physical, fixture_pins)
        assert not missing.exists()
        assert regular.read_bytes() == b'preserve regular parent\n'
        report['cases'].append({'case': name, 'backend': backend, 'selected_parent': str(selected),
                                'expected': 'passed' if passed else 'setup_failure',
                                'public_report': parsed})
        write_report(report_path, report)

    try:
        for backend in (('c', 'llvm') if args.backend == 'both' else (args.backend,)):
            if baseline:
                probe(baseline, backend, 'baseline-physical', physical, passed=True, locked=False)
                for name, alias in aliases:
                    probe(baseline, backend, 'baseline-' + name, alias, passed=False)
            probe(freak, backend, 'physical', physical, passed=True, locked=False)
            for name, alias in aliases:
                probe(freak, backend, name, alias, passed=True)
            probe(freak, backend, 'absent-parent', missing, passed=False,
                  failure='cannot canonicalize selected system temporary parent')
            probe(freak, backend, 'regular-parent', regular, passed=False,
                  failure='cannot create owned test output directory under selected parent')
            if os.name == 'posix':
                unusable = root / f'unwritable-parent-{backend}'
                unusable.mkdir()
                unusable.chmod(0o500)
                try:
                    assert not os.access(unusable, os.W_OK), 'unwritable control requires an unprivileged host'
                    probe(freak, backend, 'unwritable-parent', unusable, passed=False,
                          failure='cannot create owned test output directory under selected parent')
                    assert list(unusable.iterdir()) == []
                finally:
                    unusable.chmod(0o700)
        assert sha(freak) == report['candidate']['sha256']
        assert sha(clang) == report['clang']['sha256']
        if baseline:
            assert sha(baseline) == report['baseline']['sha256']
        assert sha(Path(__file__)) == report['gate_sha256']
        assert sha(capture_helper) == report['capture_helper']['sha256']
        check_inputs(project, physical, fixture_pins)
        assert inventory(home / 'runtime') == report['payload_pins']['runtime']
        assert inventory(home / 'std') == report['payload_pins']['std']
        report['outcome'] = 'passed'
        report.pop('active', None)
    except BaseException as error:
        report['outcome'] = 'failed'
        report['error'] = repr(error)
        raise
    finally:
        primary = sys.exc_info()[1]
        try:
            write_report(report_path, report)
        except BaseException as secondary:
            if primary is None:
                raise
            try:
                primary.add_note('Terminal temporary-parent receipt failed: ' + repr(secondary))
            except BaseException:
                pass
    print(f'PASS public project tests: physical/alias admission and rejected-parent cleanup ({len(report["cases"])} cases)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
