"""Compile FREAK's C runtime once per flag set and reuse the objects.

Suites that link many small case binaries against the same runtime with the
same flags used to recompile the whole runtime (thousands of lines, often with
ASan) for every case. `runtime_objects` compiles each runtime source once per
(clang, sources, flags, cache directory) and hands back object files to link
instead. The flags are exactly the ones the case binary is built with, so the
linked program is the same as before; only the repeated work goes away.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

_BUILT: dict[tuple[str, tuple[str, ...], tuple[str, ...], str], list[str]] = {}


def runtime_objects(clang: str, sources: list[Path], flags: list[str], cache_dir: Path,
                    timeout: int = 300) -> list[str]:
    """Return object paths for `sources` compiled with `flags`, building them on first use."""
    key = (clang, tuple(str(source) for source in sources), tuple(flags), str(cache_dir))
    if key not in _BUILT:
        tag = hashlib.sha256(repr(key).encode("utf-8")).hexdigest()[:12]
        objects = []
        for source in sources:
            obj = cache_dir / f"runtime-{tag}-{source.stem}.o"
            built = subprocess.run([clang, *flags, "-c", str(source), "-o", str(obj)],
                                   capture_output=True, text=True, timeout=timeout)
            if built.returncode != 0:
                raise AssertionError(f"runtime object build failed for {source}\n{built.stdout}{built.stderr}")
            objects.append(str(obj))
        _BUILT[key] = objects
    return _BUILT[key]
