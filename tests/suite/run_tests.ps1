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
    & $FreakBin build $fk.FullName 2>&1 | Out-Null

    if (-not (Test-Path $BinPath)) {
        Write-Host "  FAIL  $Name  (build failed)"
        $Fail++
        continue
    }

    # Run and compare
    $Actual = & $BinPath 2>&1 | Out-String
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
