# FREAK Compiler Test Suite Runner (PowerShell)
# Usage: .\tests\suite\run_tests.ps1 [freak_binary]
# Default freak binary: build\freak.exe (relative to repo root)

param(
    [string]$FreakBin = ""
)

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$SuiteDir = Join-Path $RepoRoot "tests\suite"

if ($FreakBin -eq "") {
    $FreakBin = Join-Path $RepoRoot "build\freak.exe"
}

if (-not (Test-Path $FreakBin)) {
    Write-Host "ERROR: freak binary not found at $FreakBin"
    Write-Host "Usage: run_tests.ps1 [path\to\freak.exe]"
    exit 1
}

$Pass = 0
$Fail = 0
$Skip = 0

Write-Host ""
Write-Host "  FREAK Compiler Test Suite"
Write-Host "  freak: $FreakBin"
Write-Host "  suite: $SuiteDir"
Write-Host ""

$TestFiles = Get-ChildItem -Path $SuiteDir -Filter "*.fk" |
    Where-Object { $_.Name -match '^\d' } |
    Sort-Object Name

foreach ($fk in $TestFiles) {
    $Name = $fk.BaseName
    $ExpectedFile = Join-Path $SuiteDir "$Name.expected"

    if (-not (Test-Path $ExpectedFile)) {
        Write-Host "  SKIP  $Name  (no .expected file)"
        $Skip++
        continue
    }

    # Compile
    $BinPath = Join-Path $SuiteDir "$Name.exe"
    try {
        if (Test-Path -LiteralPath $BinPath) {
            if (-not (Test-Path -LiteralPath $BinPath -PathType Leaf)) {
                throw "generated output path is not a file"
            }
            Remove-Item -LiteralPath $BinPath -Force -ErrorAction Stop
        }
    } catch {
        Write-Host "  FAIL  $Name  (could not remove stale generated output)"
        $Fail++
        continue
    }

    try {
        $LASTEXITCODE = $null
        & $FreakBin build $fk.FullName 2>&1 | Out-Null
        $BuildExitCode = $LASTEXITCODE
    } catch {
        Write-Host "  FAIL  $Name  (compiler invocation failed)"
        $Fail++
        continue
    }

    if ($null -eq $BuildExitCode -or $BuildExitCode -ne 0) {
        Write-Host "  FAIL  $Name  (compiler failed, exit $BuildExitCode)"
        $Fail++
        continue
    }

    if (-not (Test-Path -LiteralPath $BinPath -PathType Leaf)) {
        Write-Host "  FAIL  $Name  (build produced no fresh executable)"
        $Fail++
        continue
    }

    # Run and compare
    try {
        $LASTEXITCODE = $null
        $Actual = & $BinPath 2>&1 | Out-String
        $RunExitCode = $LASTEXITCODE
    } catch {
        Write-Host "  FAIL  $Name  (program invocation failed)"
        $Fail++
        continue
    }
    if ($null -eq $RunExitCode -or $RunExitCode -ne 0) {
        Write-Host "  FAIL  $Name  (program failed, exit $RunExitCode)"
        $Fail++
        continue
    }
    $Actual = $Actual.TrimEnd("`r`n")
    $Expected = (Get-Content $ExpectedFile -Raw).TrimEnd("`r`n")

    if ($Actual -eq $Expected) {
        Write-Host "  PASS  $Name"
        $Pass++
    } else {
        Write-Host "  FAIL  $Name"
        Write-Host "        expected:"
        $Expected -split "`n" | ForEach-Object { Write-Host "          $_" }
        Write-Host "        actual:"
        $Actual -split "`n" | ForEach-Object { Write-Host "          $_" }
        $Fail++
    }
}

Write-Host ""
Write-Host "  Results: $Pass passed, $Fail failed, $Skip skipped"
Write-Host ""

if ($Fail -gt 0) { exit 1 }
exit 0
