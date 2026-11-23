#!/usr/bin/env python3
"""Hangar must update a project folder that other accounts can also write.

Folders on a second Windows drive (D:\\) inherit "Authenticated Users: Modify"
from the drive root, and umask 002 makes POSIX project folders group-writable.
hangar init/add/remove publish hangar.toml and hangar.lock there through the
workspace rename policy; Hangar's own private state must stay private.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import stat
import subprocess
import tempfile


LIBRARY_MANIFEST = '''[project]
name = "sharedlib"
version = "0.1.0"
kind = "lib"

[modules]
shared = "src/shared.fk"

[exports]
shared_greeting = "shared::shared_greeting"
'''
LIBRARY_SOURCE = '''launch task shared_greeting() -> word {
    give back "shared"
}
'''


def share(path: Path) -> None:
    if os.name == 'nt':
        # Authenticated Users, inherited by children, like a D:\ drive root grants.
        subprocess.run(['icacls', str(path), '/grant', '*S-1-5-11:(OI)(CI)M'], check=True, capture_output=True)
    else:
        path.chmod(0o777)


def hangar(freak: Path, cwd: Path, *arguments: str) -> str:
    result = subprocess.run([str(freak), 'hangar', *arguments], cwd=cwd, capture_output=True, text=True, timeout=300)
    output = result.stdout + result.stderr
    assert result.returncode == 0, (arguments, result.returncode, output)
    assert 'requires safe owned' not in output and 'refused' not in output, (arguments, output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('freak', type=Path)
    freak = parser.parse_args().freak.resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix='freak-shared-project-') as temporary:
        # macOS temp dirs live under the /var -> /private/var symlink, and Hangar
        # refuses to follow links when anchoring a package root.
        root = Path(temporary).resolve(strict=True)
        library = root / 'sharedlib'
        (library / 'src').mkdir(parents=True)
        (library / 'hangar.toml').write_text(LIBRARY_MANIFEST)
        (library / 'src' / 'shared.fk').write_text(LIBRARY_SOURCE)
        project = root / 'project'
        project.mkdir()
        share(project)
        hangar(freak, project, 'init', '.')
        assert (project / 'hangar.toml').is_file(), 'init published the manifest'
        hangar(freak, project, 'add', 'sharedlib', '--path', str(library))
        manifest = (project / 'hangar.toml').read_text()
        assert 'sharedlib' in manifest, manifest
        assert 'sharedlib' in (project / 'hangar.lock').read_text()
        hangar(freak, project, 'remove', 'sharedlib')
        assert 'sharedlib' not in (project / 'hangar.toml').read_text()
        if os.name != 'nt':
            assert not stat.S_IMODE((project / '.freak').stat().st_mode) & 0o077, 'Hangar private state stays private'
    print('PASS hangar init/add/remove in a shared-writable project folder', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
