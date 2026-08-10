# FREAK Language Installer - Windows
# Usage: irm https://raw.githubusercontent.com/FREAK-lang-dev/Freak-lang/main/install.ps1 | iex
# With compiler dependencies: $env:FREAK_INSTALL_DEPS=1; irm .../install.ps1 | iex
param(
    [switch]$InstallDeps,
    [switch]$SkipDeps,
    [switch]$Upgrade
)

$ErrorActionPreference = "Stop"
$Repo = "FREAK-lang-dev/Freak-lang"

function Info($msg) { Write-Host "> $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "> $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "> $msg" -ForegroundColor Yellow }
function Err($msg)  { Write-Host "> $msg" -ForegroundColor Red; throw $msg }
function Test-Truthy($value) { return $value -match '^(1|true|yes|on)$' }

$InstallDependencies = Test-Truthy $env:FREAK_INSTALL_DEPS
if ($InstallDeps) { $InstallDependencies = $true }
if ($SkipDeps) { $InstallDependencies = $false }
$UpgradeMode = $Upgrade -or (Test-Truthy $env:FREAK_INSTALL_UPGRADE)
$SkipPathUpdate = Test-Truthy $env:FREAK_SKIP_PATH_UPDATE
$LocalArchive = $env:FREAK_INSTALL_ARCHIVE
$Latest = $env:FREAK_RELEASE_TAG
$ReleaseBase = if ($env:FREAK_RELEASE_BASE) { $env:FREAK_RELEASE_BASE.TrimEnd('/') } else { "https://github.com/$Repo/releases/download" }

$InstallDir = if ($env:FREAK_HOME) { $env:FREAK_HOME } else { "$env:APPDATA\freak" }
$InstallDir = [System.IO.Path]::GetFullPath($InstallDir)
if ($InstallDir -eq [System.IO.Path]::GetPathRoot($InstallDir)) {
    Err "Refusing unsafe FREAK install directory: $InstallDir"
}
$InstallDir = $InstallDir.TrimEnd([char[]]@('\', '/'))
$BinDir = Join-Path $InstallDir "bin"

function Test-ClangToolchain($candidate) {
    if (-not $candidate -or -not (Test-Path -LiteralPath $candidate -PathType Leaf)) { return $false }
    $probeDir = Join-Path ([System.IO.Path]::GetTempPath()) "freak-clang-probe-$(Get-Random)"
    New-Item -ItemType Directory -Path $probeDir -Force | Out-Null
    try {
        $source = Join-Path $probeDir "probe.c"
        $binary = Join-Path $probeDir "probe.exe"
        [System.IO.File]::WriteAllText($source, "#include <stdio.h>`nint main(void) { return 0; }`n")
        & $candidate -x c $source -o $binary 2>$null
        return $LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $binary -PathType Leaf)
    } catch {
        return $false
    } finally {
        Remove-Item -LiteralPath $probeDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function Find-Clang {
    $candidates = [System.Collections.Generic.List[string]]::new()
    if ($env:FREAK_CLANG) { $candidates.Add($env:FREAK_CLANG) }

    $wingetRoot = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
    if (Test-Path -LiteralPath $wingetRoot -PathType Container) {
        Get-ChildItem -LiteralPath $wingetRoot -Directory -Filter "MartinStorsjo.LLVM-MinGW.UCRT_*" -ErrorAction SilentlyContinue |
            ForEach-Object {
                Get-ChildItem -LiteralPath $_.FullName -Recurse -File -Filter "clang.exe" -ErrorAction SilentlyContinue |
                    ForEach-Object { $candidates.Add($_.FullName) }
            }
    }
    foreach ($command in Get-Command clang.exe -All -ErrorAction SilentlyContinue) {
        $candidates.Add($command.Source)
    }
    foreach ($candidate in @(
        "$env:ProgramFiles\LLVM\bin\clang.exe",
        "$env:ProgramW6432\LLVM\bin\clang.exe",
        "${env:ProgramFiles(x86)}\LLVM\bin\clang.exe",
        "$env:LOCALAPPDATA\Programs\LLVM\bin\clang.exe"
    )) {
        if ($candidate) { $candidates.Add($candidate) }
    }
    foreach ($candidate in $candidates | Select-Object -Unique) {
        if (Test-ClangToolchain $candidate) { return $candidate }
    }
    return $null
}

function Install-CompilerDependencies {
    $clang = Find-Clang
    if ($clang) {
        Ok "Clang is available: $clang"
        return
    }
    if (-not $InstallDependencies) {
        Warn "Clang is not available; FREAK will install, but native builds need LLVM/Clang."
        Warn "Re-run with `$env:FREAK_INSTALL_DEPS=1, or install: winget install --id MartinStorsjo.LLVM-MinGW.UCRT -e"
        return
    }

    Info "Installing LLVM/Clang and LLD..."
    $installed = $false
    if (Get-Command winget.exe -ErrorAction SilentlyContinue) {
        & winget.exe install --id MartinStorsjo.LLVM-MinGW.UCRT -e --silent --accept-package-agreements --accept-source-agreements
        $installed = $LASTEXITCODE -eq 0
    }
    if (-not $installed -and (Get-Command scoop.cmd -ErrorAction SilentlyContinue)) {
        & scoop.cmd install llvm-mingw
        $installed = $LASTEXITCODE -eq 0
    }
    if (-not $installed) {
        Err "Could not install a complete LLVM toolchain. Try: winget install --id MartinStorsjo.LLVM-MinGW.UCRT -e"
    }

    $clang = Find-Clang
    if (-not $clang) {
        Err "The LLVM installer finished, but no clang could compile and link a C probe. Reopen the terminal and run freak doctor."
    }
    $clangBin = Split-Path -Parent $clang
    if ($env:PATH -notlike "*$clangBin*") { $env:PATH = "$clangBin;$env:PATH" }
    Ok "Compiler dependencies are ready"
}

# Only x64 Windows binaries ship today.
$Target = "freak-windows-x64"
Info "Detected platform: windows-x64"
Install-CompilerDependencies
$ResolvedClang = Find-Clang
if ($ResolvedClang) {
    $env:FREAK_CLANG = $ResolvedClang
    if (-not $SkipPathUpdate) {
        [Environment]::SetEnvironmentVariable("FREAK_CLANG", $ResolvedClang, "User")
    }
    Info "Configured FREAK_CLANG: $ResolvedClang"
}

if ($LocalArchive) {
    $LocalArchive = [System.IO.Path]::GetFullPath($LocalArchive)
    if (-not (Test-Path -LiteralPath $LocalArchive -PathType Leaf)) {
        Err "Local distribution archive not found: $LocalArchive"
    }
    if (-not $Latest) { $Latest = "local" }
} elseif (-not $Latest) {
    Info "Fetching latest release..."
    try {
        $Release = Invoke-RestMethod "https://api.github.com/repos/$Repo/releases/latest"
        $Latest = $Release.tag_name
    } catch {
        Err "Could not fetch latest release. Check https://github.com/$Repo/releases"
    }
}
if (-not $Latest) { Err "Could not determine the release tag" }
Info "Release: $Latest"

$RawBase = if ($env:FREAK_RAW_BASE) { $env:FREAK_RAW_BASE.TrimEnd('/') } else { "https://raw.githubusercontent.com/$Repo/$Latest" }
$ZipUrl = "$ReleaseBase/$Latest/$Target.zip"
$TmpDir = Join-Path ([System.IO.Path]::GetTempPath()) "freak-install-$(Get-Random)"
$ExtractDir = Join-Path $TmpDir "extract"
$StageDir = Join-Path $TmpDir "stage"
$StageBin = Join-Path $StageDir "bin"
$StageRuntime = Join-Path $StageDir "runtime"
$StageStd = Join-Path $StageDir "std"
$StageManifest = Join-Path $StageDir "distribution-files.manifest"
New-Item -ItemType Directory -Path $ExtractDir, $StageBin, $StageRuntime, $StageStd -Force | Out-Null

function Get-ManifestEntries {
    if (-not (Test-Path -LiteralPath $StageManifest -PathType Leaf)) {
        Err "Staged distribution manifest is missing"
    }
    foreach ($rawLine in Get-Content -LiteralPath $StageManifest) {
        $line = $rawLine.Trim()
        if (-not $line -or $line.StartsWith('#')) { continue }
        $parts = $line.Split([char]'|', 2)
        if ($parts.Count -ne 2 -or -not $parts[1]) { Err "Malformed distribution manifest entry: $line" }
        $source = $parts[0].Replace('\', '/')
        $destination = $parts[1].Replace('\', '/')
        if (($source -notlike 'freakc/runtime/*' -and $source -notlike 'std/*') -or
            ($destination -notlike 'runtime/*' -and $destination -notlike 'std/*') -or
            $source.Contains('../') -or $destination.Contains('../')) {
            Err "Unsafe distribution manifest entry: $line"
        }
        [pscustomobject]@{ Source = $source; Destination = $destination }
    }
}

function Assert-StagedPayload {
    foreach ($path in @("$StageBin\freak.exe", "$StageBin\hangar.exe", $StageManifest)) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { Err "Staged payload is missing $path" }
        if ((Get-Item -LiteralPath $path).Length -eq 0) { Err "Staged payload is empty: $path" }
    }
    foreach ($entry in Get-ManifestEntries) {
        $path = Join-Path $StageDir $entry.Destination
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { Err "Staged payload is missing $($entry.Destination)" }
        if ((Get-Item -LiteralPath $path).Length -eq 0) { Err "Staged payload is empty: $($entry.Destination)" }
    }
}

function Stage-FallbackPayload {
    Info "Distribution archive unavailable; staging standalone compatibility assets..."
    Invoke-WebRequest -Uri "$ReleaseBase/$Latest/$Target.exe" -OutFile "$StageBin\freak.exe" -UseBasicParsing
    try {
        Invoke-WebRequest -Uri "$ReleaseBase/$Latest/hangar-windows-x64.exe" -OutFile "$StageBin\hangar.exe" -UseBasicParsing
    } catch {
        Copy-Item -LiteralPath "$StageBin\freak.exe" -Destination "$StageBin\hangar.exe" -Force
    }
    Invoke-WebRequest -Uri "$RawBase/packaging/distribution-files.manifest" -OutFile $StageManifest -UseBasicParsing
    foreach ($entry in Get-ManifestEntries) {
        $destination = Join-Path $StageDir $entry.Destination
        New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
        Invoke-WebRequest -Uri "$RawBase/$($entry.Source)" -OutFile $destination -UseBasicParsing
    }
}

function Start-DeferredBinaryReplacement {
    $quotedBin = $BinDir.Replace("'", "''")
    $apply = @"
`$ErrorActionPreference = 'Stop'
Start-Sleep -Milliseconds 750
for (`$attempt = 0; `$attempt -lt 120; `$attempt++) {
    try {
        foreach (`$name in @('freak.exe', 'hangar.exe')) {
            `$next = Join-Path '$quotedBin' (`$name + '.next')
            `$target = Join-Path '$quotedBin' `$name
            if (Test-Path -LiteralPath `$next) { Move-Item -LiteralPath `$next -Destination `$target -Force }
        }
        exit 0
    } catch {
        Start-Sleep -Milliseconds 250
    }
}
exit 1
"@
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($apply))
    Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile -NonInteractive -ExecutionPolicy Bypass -EncodedCommand $encoded" -WindowStyle Hidden | Out-Null
}

function Install-StagedPayload {
    Assert-StagedPayload
    New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
    $applyId = Get-Random
    $applyRoot = Join-Path $InstallDir ".freak-apply-$applyId"
    $backupRoot = Join-Path $InstallDir ".freak-backup-$applyId"
    $items = @()
    try {
        New-Item -ItemType Directory -Path "$applyRoot\bin", "$applyRoot\runtime", "$applyRoot\std", "$backupRoot\bin" -Force | Out-Null
        Copy-Item -LiteralPath "$StageBin\freak.exe" -Destination "$applyRoot\bin\freak.exe" -Force
        Copy-Item -LiteralPath "$StageBin\hangar.exe" -Destination "$applyRoot\bin\hangar.exe" -Force
        Copy-Item -Path "$StageRuntime\*" -Destination "$applyRoot\runtime" -Recurse -Force
        Copy-Item -Path "$StageStd\*" -Destination "$applyRoot\std" -Recurse -Force
        Copy-Item -LiteralPath $StageManifest -Destination "$applyRoot\distribution-files.manifest" -Force

        $items = @(
            [pscustomobject]@{ Live = "$InstallDir\runtime"; Pending = "$applyRoot\runtime"; Backup = "$backupRoot\runtime"; Prepared = $false; HadOriginal = $false },
            [pscustomobject]@{ Live = "$InstallDir\std"; Pending = "$applyRoot\std"; Backup = "$backupRoot\std"; Prepared = $false; HadOriginal = $false },
            [pscustomobject]@{ Live = "$InstallDir\distribution-files.manifest"; Pending = "$applyRoot\distribution-files.manifest"; Backup = "$backupRoot\distribution-files.manifest"; Prepared = $false; HadOriginal = $false }
        )
        if (-not $UpgradeMode) {
            $items += [pscustomobject]@{ Live = "$BinDir\freak.exe"; Pending = "$applyRoot\bin\freak.exe"; Backup = "$backupRoot\bin\freak.exe"; Prepared = $false; HadOriginal = $false }
            $items += [pscustomobject]@{ Live = "$BinDir\hangar.exe"; Pending = "$applyRoot\bin\hangar.exe"; Backup = "$backupRoot\bin\hangar.exe"; Prepared = $false; HadOriginal = $false }
        }

        foreach ($item in $items) {
            $item.HadOriginal = Test-Path -LiteralPath $item.Live
            if ($item.HadOriginal) {
                New-Item -ItemType Directory -Path (Split-Path -Parent $item.Backup) -Force | Out-Null
                Move-Item -LiteralPath $item.Live -Destination $item.Backup
            }
            $item.Prepared = $true
        }
        for ($index = 0; $index -lt $items.Count; $index++) {
            $item = $items[$index]
            Move-Item -LiteralPath $item.Pending -Destination $item.Live
            if ($index -eq 0 -and (Test-Truthy $env:FREAK_INSTALL_TEST_FAIL_APPLY)) {
                throw "injected apply failure"
            }
        }
        if ($UpgradeMode) {
            Remove-Item -LiteralPath "$BinDir\freak.exe.next", "$BinDir\hangar.exe.next" -Force -ErrorAction SilentlyContinue
            Copy-Item -LiteralPath "$applyRoot\bin\freak.exe" -Destination "$BinDir\freak.exe.next" -Force
            Copy-Item -LiteralPath "$applyRoot\bin\hangar.exe" -Destination "$BinDir\hangar.exe.next" -Force
            Start-DeferredBinaryReplacement
        }
    } catch {
        $applyError = $_.Exception.Message
        Remove-Item -LiteralPath "$BinDir\freak.exe.next", "$BinDir\hangar.exe.next" -Force -ErrorAction SilentlyContinue
        for ($index = $items.Count - 1; $index -ge 0; $index--) {
            $item = $items[$index]
            if (-not $item.Prepared) { continue }
            if (Test-Path -LiteralPath $item.Live) { Remove-Item -LiteralPath $item.Live -Recurse -Force }
            if ($item.HadOriginal -and (Test-Path -LiteralPath $item.Backup)) {
                Move-Item -LiteralPath $item.Backup -Destination $item.Live
            }
        }
        Remove-Item -LiteralPath $applyRoot, $backupRoot -Recurse -Force -ErrorAction SilentlyContinue
        Err "Could not apply the staged distribution; the previous payload was restored ($applyError)"
    }
    Remove-Item -LiteralPath $applyRoot, $backupRoot -Recurse -Force -ErrorAction SilentlyContinue
}

try {
    $ZipPath = Join-Path $TmpDir "freak.zip"
    $ZipOk = $false
    if ($LocalArchive) {
        Copy-Item -LiteralPath $LocalArchive -Destination $ZipPath -Force
        $ZipOk = $true
    } else {
        Info "Downloading $Target.zip..."
        try {
            Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath -UseBasicParsing
            $ZipOk = $true
        } catch {
            $ZipOk = $false
        }
    }

    if ($ZipOk) {
        try {
            Info "Extracting distribution..."
            Expand-Archive -LiteralPath $ZipPath -DestinationPath $ExtractDir -Force
            Copy-Item -LiteralPath "$ExtractDir\freak\bin\freak.exe" -Destination "$StageBin\freak.exe" -Force
            if (Test-Path -LiteralPath "$ExtractDir\freak\bin\hangar.exe") {
                Copy-Item -LiteralPath "$ExtractDir\freak\bin\hangar.exe" -Destination "$StageBin\hangar.exe" -Force
            } else {
                Copy-Item -LiteralPath "$StageBin\freak.exe" -Destination "$StageBin\hangar.exe" -Force
            }
            Copy-Item -Path "$ExtractDir\freak\runtime\*" -Destination $StageRuntime -Recurse -Force
            Copy-Item -Path "$ExtractDir\freak\std\*" -Destination $StageStd -Recurse -Force
            Copy-Item -LiteralPath "$ExtractDir\freak\distribution-files.manifest" -Destination $StageManifest -Force
        } catch {
            if ($LocalArchive) { throw }
            Remove-Item -LiteralPath $StageDir -Recurse -Force
            New-Item -ItemType Directory -Path $StageBin, $StageRuntime, $StageStd -Force | Out-Null
            Stage-FallbackPayload
        }
    } else {
        Stage-FallbackPayload
    }
    Install-StagedPayload
} finally {
    Remove-Item -LiteralPath $TmpDir -Recurse -Force -ErrorAction SilentlyContinue
}

if (-not $SkipPathUpdate) {
    $UserPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    if (-not $UserPath) { $UserPath = "" }
    if ($UserPath -notlike "*$BinDir*") {
        [Environment]::SetEnvironmentVariable("PATH", "$BinDir;$UserPath", "User")
        Info "Added $BinDir to user PATH"
    }
}
if ($env:PATH -notlike "*$BinDir*") { $env:PATH = "$BinDir;$env:PATH" }

Ok ""
Ok "FREAK $Latest installed successfully!"
Ok "  Compiler: $BinDir\freak.exe"
Ok "  Hangar:   $BinDir\hangar.exe"
Ok "  Runtime:  $InstallDir\runtime\"
Ok "  Std lib:  $InstallDir\std\"
if ($UpgradeMode) { Ok "  Binary replacement is scheduled for this process exit." }
if (-not (Find-Clang)) { Warn "Clang is still missing. Install LLVM before building FREAK programs." }
Ok "Open a new terminal and verify the complete toolchain with: freak doctor"
Ok '"It was always going to end this way."'
