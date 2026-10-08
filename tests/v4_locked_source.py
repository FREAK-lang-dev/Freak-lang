"""Materialize the immutable bootstrap sources beside current development code."""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess

from windows_private_fixture import WindowsPrivateFixture


def materialize(repo: Path, checkout: Path) -> tuple[Path, dict]:
    """Read pinned source blobs from Git and independently verify profile bytes."""
    profile = repo / 'src/compiler/v4'
    lock = (profile / 'bootstrap.lock').read_bytes()
    lines = lock.decode('utf-8').splitlines()
    assert lines[0] == 'FREAK-V4-BOOTSTRAP-LOCK-1'
    pin = lines[1].split()[1]
    records = [line.split(' ', 2) for line in lines[2:] if line]
    assert len(records) == 28
    checkout.mkdir(parents=True, exist_ok=False)
    private = WindowsPrivateFixture(checkout)
    # Let the host's Git create its shared-object path spelling. The fresh
    # checkout and git directory must be caller-owned on native Windows too.
    cloned = subprocess.run(['git', 'clone', '--shared', '--no-checkout', str(repo), str(checkout)],
                            capture_output=True, timeout=30)
    assert cloned.returncode == 0, (cloned.args, cloned.stdout, cloned.stderr)
    private.claim_fresh_directories(checkout / '.git')
    selected = subprocess.run(['git', 'update-ref', '--no-deref', 'HEAD', pin], cwd=checkout,
                              capture_output=True, timeout=30)
    assert selected.returncode == 0, (selected.args, selected.stdout, selected.stderr)
    source = checkout / 'src/compiler/v4'
    inventory = []
    for role, expected, relative in records:
        if role in ('source', 'entry'):
            origin = f'{pin}:src/compiler/v4/{relative}'
            contents = subprocess.check_output(['git', 'cat-file', 'blob', origin], cwd=repo, timeout=30)
        else:
            origin = str(profile / relative)
            contents = (profile / relative).read_bytes()
        actual = hashlib.sha256(contents).hexdigest()
        assert actual == expected, (role, relative, actual, expected)
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(contents)
        inventory.append({'role': role, 'path': relative, 'origin': origin, 'sha256': actual})
    assert sum(row['role'] in ('source', 'entry') for row in inventory) == 23
    (source / 'bootstrap.lock').write_bytes(lock)
    return source, {'source_commit': pin, 'lock_sha256': hashlib.sha256(lock).hexdigest(),
                    'inventory': inventory}
