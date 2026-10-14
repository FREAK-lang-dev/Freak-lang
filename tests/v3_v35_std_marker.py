#!/usr/bin/env python3
"""Check the native marker entry with an empty PATH and hostile payload bytes.

The supplied native entry must print cli_payload_std_api_value(arg(1)). This
focused gate does not claim public Doctor dispatch or JSON integration proof.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    candidate = args.candidate.resolve(strict=True)
    checks: list[str] = []
    env = {**os.environ, 'PATH': ''}
    with tempfile.TemporaryDirectory(prefix='freak-v35-marker-') as temporary:
        root = Path(temporary).resolve()
        payload = root / ('selected payload é & %LITERAL%' if os.name == 'nt' else "selected payload é '$(touch INJECTED)' & %LITERAL%")
        payload.mkdir()
        marker = payload / 'freak_std_api'

        def check(name: str, expected: str) -> None:
            result = subprocess.run([str(candidate), str(payload)], cwd=root, env=env,
                                    capture_output=True, timeout=10, check=False)
            assert result.returncode == 0 and result.stdout == (expected + '\n').encode('ascii'), (name, result)
            assert not result.stderr and not root.joinpath('INJECTED').exists(), (name, result)
            checks.append(name)

        check('missing-selected-marker', 'missing')
        for name, data, expected in (
            ('valid-token', b'freak-v3-std-api-1', 'freak-v3-std-api-1'),
            ('edge-whitespace', b' \t\r\nfreak-v3-std-api-1\r\n\t ', 'freak-v3-std-api-1'),
            ('empty-marker', b'', 'unreadable'),
            ('whitespace-marker', b' \t\r\n', ''),
            ('interior-newline', b'first\nsecond', 'invalid-marker'),
            ('interior-tab', b'first\tsecond', 'invalid-marker'),
            ('interior-carriage-return', b'first\rsecond', 'invalid-marker'),
            ('exact-limit', b'x' * 4096, 'x' * 4096),
            ('over-limit', b'x' * 4097, 'oversized-marker'),
            ('unicode-capability-token', 'é'.encode('utf-8'), 'invalid-marker'),
        ):
            marker.write_bytes(data)
            check(name, expected)
        for value in range(256):
            if value in (9, 10, 13) or 32 <= value <= 126:
                continue
            marker.write_bytes(bytes((value,)))
            check(f'forbidden-byte-{value:02x}', 'invalid-marker')
        marker.unlink()
        marker.mkdir()
        check('directory-marker', 'unreadable')
        marker.rmdir()
        if os.name == 'posix':
            target = root / 'outside-marker'
            target.write_bytes(b'freak-v3-std-api-1')
            marker.symlink_to(target)
            check('symlink-marker', 'unreadable')
            marker.unlink()
            marker.symlink_to(root / 'absent-target')
            check('dangling-symlink-marker', 'unreadable')
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps({'status': 'pass', 'candidate_sha256': hashlib.sha256(candidate.read_bytes()).hexdigest(),
                                            'scope': 'native marker entry; public Doctor integration is a separate gate',
                                            'empty_path': True, 'checks': checks}, indent=2) + '\n')
    print(f'V3.5 native marker contracts: OK ({len(checks)} checks)', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
