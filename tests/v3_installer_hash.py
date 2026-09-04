#!/usr/bin/env python3
"""Exercise installer SHA-256 without PowerShell module autoloading."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    source = (repo / "install.ps1").read_text(encoding="utf-8")
    assert "Get-FileHash" not in source
    assert "$hashFunctionDefinition = ${function:Get-FreakFileSha256}.ToString()" in source
    assert source.count("Get-FreakFileSha256") == 8
    if sys.platform != "win32":
        print("PASS installer hash source contract; Windows execution unavailable")
        return 0
    with tempfile.TemporaryDirectory(prefix="freak-installer-hash-") as temporary:
        root = Path(temporary)
        samples = (b"", b"abc", bytes(range(256)) * 8193)
        names = ("empty", "literal [one]' é", "streamed")
        for name, data in zip(names, samples):
            (root / name).write_bytes(data)
        script = root / "probe.ps1"
        script.write_text(r"""
param([string]$Installer, [string]$Samples)
$ErrorActionPreference = 'Stop'
$PSModuleAutoLoadingPreference = 'None'
function Get-FileHash { throw 'Get-FileHash must not be called' }
$tokens = $null
$parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($Installer, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count -ne 0) { throw 'installer has parse errors' }
$definition = $ast.Find({ param($node)
    $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Get-FreakFileSha256'
}, $false)
if (-not $definition) { throw 'missing hash function' }
. ([scriptblock]::Create($definition.Extent.Text))
foreach ($name in @('empty', "literal [one]' é", 'streamed')) {
    $path = [System.IO.Path]::Combine($Samples, $name)
    [Console]::WriteLine((Get-FreakFileSha256 $path))
    $exclusive = [System.IO.File]::Open($path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
    $exclusive.Dispose()
}
$rejected = $false
try { Get-FreakFileSha256 ([System.IO.Path]::Combine($Samples, 'missing')) } catch { $rejected = $true }
if (-not $rejected) { throw 'missing file did not fail closed' }
""", encoding="utf-8-sig")
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
             "-File", str(script), str(repo / "install.ps1"), str(root)],
            env=os.environ.copy(), capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert result.stdout.splitlines() == [hashlib.sha256(data).hexdigest() for data in samples], result.stdout
        assert not result.stderr, result.stderr
    print("PASS installer SHA-256: no modules, known hashes, binary stream, literal paths, closed handles, missing-file rejection")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
