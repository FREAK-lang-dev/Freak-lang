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
$InstallLockPath = Join-Path $InstallDir ".freak-install.lock"
$InstallLockStream = $null
$RecoveredPendingUpgrade = $false
$DeferredHelperUnsafe = $false
$LegacyV014Archive = $false

function Acquire-InstallLock {
    [System.IO.Directory]::CreateDirectory($InstallDir) | Out-Null
    try {
        $script:InstallLockStream = [System.IO.File]::Open(
            $InstallLockPath,
            [System.IO.FileMode]::OpenOrCreate,
            [System.IO.FileAccess]::ReadWrite,
            [System.IO.FileShare]::None
        )
    } catch {
        Err "Another FREAK installer is already updating $InstallDir"
    }
    Recover-OrphanedDeferredUpgrade
    Recover-OrphanedPayloadTransaction
}

function Release-InstallLock {
    if ($script:InstallLockStream) {
        $script:InstallLockStream.Dispose()
        $script:InstallLockStream = $null
        Remove-Item -LiteralPath $InstallLockPath -Force -ErrorAction SilentlyContinue
    }
}

function Test-DeferredUpgradeHelperLockHeld {
    $helperLockPath = Join-Path $BinDir ".freak-upgrade-helper.lock"
    if (-not (Test-Path -LiteralPath $helperLockPath -PathType Leaf)) { return $false }
    try {
        $probe = [System.IO.File]::Open(
            $helperLockPath,
            [System.IO.FileMode]::OpenOrCreate,
            [System.IO.FileAccess]::ReadWrite,
            [System.IO.FileShare]::None
        )
        $probe.Dispose()
        return $false
    } catch {
        return $true
    }
}

function Test-DeferredUpgradeHelperActive {
    $readyPath = Join-Path $BinDir ".freak-upgrade-helper.ready"
    if (-not (Test-Path -LiteralPath $readyPath -PathType Leaf)) { return $false }
    try {
        $parts = (Get-Content -LiteralPath $readyPath -Raw).Trim().Split('|')
        if ($parts.Count -ne 2) { return $false }
        $helperPid = [int]$parts[0]
        $helperStart = [long]$parts[1]
        $helper = Get-Process -Id $helperPid -ErrorAction Stop
        if ($helper.StartTime.ToFileTimeUtc() -ne $helperStart) { return $false }
        return $true
    } catch {
        return $false
    }
}

function Restore-OrphanedBinaryBackup {
    $backupRoot = Join-Path $BinDir ".freak-binary-backup"
    if (-not (Test-Path -LiteralPath $backupRoot -PathType Container)) { return $true }
    $restoreFailed = $false
    foreach ($name in @("freak.exe", "hangar.exe")) {
        $live = Join-Path $BinDir $name
        $backup = Join-Path $backupRoot $name
        $missing = Join-Path $backupRoot ($name + ".missing")
        try {
            if (Test-Path -LiteralPath $backup -PathType Leaf) {
                Remove-Item -LiteralPath $live -Force -ErrorAction SilentlyContinue
                Move-Item -LiteralPath $backup -Destination $live
            } elseif (Test-Path -LiteralPath $missing -PathType Leaf) {
                Remove-Item -LiteralPath $live -Force -ErrorAction SilentlyContinue
            }
        } catch {
            $restoreFailed = $true
        }
    }
    if (-not $restoreFailed) {
        try { Remove-Item -LiteralPath $backupRoot -Recurse -Force } catch { $restoreFailed = $true }
    }
    return -not $restoreFailed
}

function Recover-OrphanedDeferredUpgrade {
    $pending = Join-Path $BinDir ".freak-upgrade-pending"
    if (-not (Test-Path -LiteralPath $pending -PathType Leaf)) { return }
    if (Test-DeferredUpgradeHelperActive) {
        Err "A FREAK binary replacement helper is still active: $pending"
    }
    if (Test-DeferredUpgradeHelperLockHeld) {
        Err "An unrecognized process holds the FREAK deferred-upgrade lock: $pending"
    }
    if (-not (Restore-OrphanedBinaryBackup)) {
        Err "Could not restore the orphaned FREAK binary transaction: $pending"
    }
    Remove-Item -LiteralPath (Join-Path $BinDir ".freak-binary-retired") -Recurse -Force -ErrorAction SilentlyContinue
    $script:RecoveredPendingUpgrade = $true
    Warn "Recovered an orphaned deferred upgrade; the pending guard remains until this install commits."
}

function Recover-OrphanedPayloadTransaction {
    $backups = @(Get-ChildItem -LiteralPath $InstallDir -Directory -Filter ".freak-backup-*" -ErrorAction SilentlyContinue)
    $applies = @(Get-ChildItem -LiteralPath $InstallDir -Directory -Filter ".freak-apply-*" -ErrorAction SilentlyContinue)
    if ($backups.Count -gt 1) {
        Err "Multiple interrupted installer backups require manual recovery under $InstallDir"
    }

    if ($backups.Count -eq 1) {
        $backupRoot = $backups[0].FullName
        $allowedTopLevel = @("bin", "runtime", "runtime.missing", "std", "std.missing", "distribution-files.manifest", "distribution-files.manifest.missing")
        foreach ($entry in Get-ChildItem -LiteralPath $backupRoot -Force -ErrorAction SilentlyContinue) {
            if ($allowedTopLevel -notcontains $entry.Name) {
                Err "Interrupted installer backup contains an unexpected entry; backup preserved at $backupRoot"
            }
        }
        $backupBin = Join-Path $backupRoot "bin"
        if (Test-Path -LiteralPath $backupBin -PathType Container) {
            foreach ($entry in Get-ChildItem -LiteralPath $backupBin -Force -ErrorAction SilentlyContinue) {
                if (@("freak.exe", "freak.exe.missing", "hangar.exe", "hangar.exe.missing") -notcontains $entry.Name) {
                    Err "Interrupted installer backup contains an unexpected binary entry; backup preserved at $backupRoot"
                }
            }
        }

        $records = @(
            [pscustomobject]@{ Live = "$InstallDir\runtime"; Backup = "$backupRoot\runtime" },
            [pscustomobject]@{ Live = "$InstallDir\std"; Backup = "$backupRoot\std" },
            [pscustomobject]@{ Live = "$InstallDir\distribution-files.manifest"; Backup = "$backupRoot\distribution-files.manifest" },
            [pscustomobject]@{ Live = "$BinDir\freak.exe"; Backup = "$backupRoot\bin\freak.exe" },
            [pscustomobject]@{ Live = "$BinDir\hangar.exe"; Backup = "$backupRoot\bin\hangar.exe" }
        )
        try {
            foreach ($record in $records) {
                $missing = "$($record.Backup).missing"
                if (Test-Path -LiteralPath $record.Backup) {
                    Remove-Item -LiteralPath $record.Live -Recurse -Force -ErrorAction SilentlyContinue
                    New-Item -ItemType Directory -Path (Split-Path -Parent $record.Live) -Force | Out-Null
                    Move-Item -LiteralPath $record.Backup -Destination $record.Live
                } elseif (Test-Path -LiteralPath $missing -PathType Leaf) {
                    Remove-Item -LiteralPath $record.Live -Recurse -Force -ErrorAction SilentlyContinue
                }
            }
            Remove-Item -LiteralPath $backupRoot -Recurse -Force
        } catch {
            Err "Could not recover the interrupted payload; backup preserved at $backupRoot ($($_.Exception.Message))"
        }
        Warn "Recovered the previous payload from an interrupted Windows installer transaction"
    }

    foreach ($apply in $applies) {
        Remove-Item -LiteralPath $apply.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function Test-ClangToolchain($candidate) {
    if (-not $candidate -or -not (Test-Path -LiteralPath $candidate -PathType Leaf)) { return $false }
    $probeDir = Join-Path ([System.IO.Path]::GetTempPath()) "freak-clang-probe-$(Get-Random)"
    New-Item -ItemType Directory -Path $probeDir -Force | Out-Null
    try {
        $source = Join-Path $probeDir "probe.c"
        $binary = Join-Path $probeDir "probe.exe"
        [System.IO.File]::WriteAllText($source, "#include <stdio.h>`nint main(void) { return 0; }`n")
        & $candidate -x c $source -o $binary 2>$null
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $binary -PathType Leaf)) { return $false }
        & $binary *> $null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    } finally {
        Remove-Item -LiteralPath $probeDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function Find-Clang {
    $candidates = [System.Collections.Generic.List[string]]::new()
    if ($env:FREAK_CLANG) { $candidates.Add($env:FREAK_CLANG) }

    if ($env:USERPROFILE) {
        $candidates.Add((Join-Path $env:USERPROFILE "scoop\apps\mingw-mstorsjo-llvm-ucrt\current\bin\clang.exe"))
    }
    if ($env:ProgramData) {
        $candidates.Add((Join-Path $env:ProgramData "scoop\apps\mingw-mstorsjo-llvm-ucrt\current\bin\clang.exe"))
    }

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
        & scoop.cmd install mingw-mstorsjo-llvm-ucrt
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
        $sourceParts = @($source.Split('/') | Where-Object { $_ })
        $destinationParts = @($destination.Split('/') | Where-Object { $_ })
        if (($source -notlike 'freakc/runtime/*' -and $source -notlike 'std/*') -or
            ($destination -notlike 'runtime/*' -and $destination -notlike 'std/*') -or
            [System.IO.Path]::IsPathRooted($source) -or [System.IO.Path]::IsPathRooted($destination) -or
            $source.StartsWith('/') -or $destination.StartsWith('/') -or
            $source.Contains('//') -or $destination.Contains('//') -or
            $source.StartsWith('./') -or $destination.StartsWith('./') -or
            $source.EndsWith('/.') -or $destination.EndsWith('/.') -or
            $sourceParts -contains '.' -or $destinationParts -contains '.' -or
            $sourceParts -contains '..' -or $destinationParts -contains '..') {
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

function Assert-DownloadedAssetChecksum($ArchivePath, $AssetName) {
    $checksumsPath = Join-Path $TmpDir "SHA256SUMS"
    if (-not (Test-Path -LiteralPath $checksumsPath -PathType Leaf)) {
        try {
            Invoke-WebRequest -Uri "$ReleaseBase/$Latest/SHA256SUMS" -OutFile $checksumsPath -UseBasicParsing
        } catch {
            Err "Could not download SHA256SUMS for $Latest"
        }
    }
    $expected = $null
    foreach ($rawLine in Get-Content -LiteralPath $checksumsPath) {
        $parts = $rawLine.Trim() -split '\s+', 2
        if ($parts.Count -ne 2) { continue }
        $listedName = $parts[1].TrimStart('*').Replace('\', '/')
        if ($listedName.StartsWith('./')) { $listedName = $listedName.Substring(2) }
        if ($listedName -ceq $AssetName) {
            if ($expected) { Err "SHA256SUMS has duplicate entries for $AssetName" }
            $expected = $parts[0]
        }
    }
    if (-not $expected) {
        if ($Latest -eq "v0.14.0" -and $AssetName -eq "freak-windows-x64.zip") {
            $expected = "4d1f43eb79838a100010b6b2d6a303921d75f6b0a5f947ee0104d86de3783699"
            $script:LegacyV014Archive = $true
            Warn "Release v0.14.0 predates archive entries in SHA256SUMS; verifying the pinned immutable archive hash."
        } else {
            Err "SHA256SUMS has no exact entry for $AssetName"
        }
    }
    if ($expected -notmatch '^[0-9a-fA-F]{64}$') {
        Err "SHA256SUMS has an invalid hash for $AssetName"
    }
    $actual = (Get-FileHash -LiteralPath $ArchivePath -Algorithm SHA256).Hash
    if ($actual -ine $expected) { Err "SHA256 mismatch for $AssetName" }
    Ok "Verified SHA-256 for $AssetName"
}

function Stage-FallbackPayload {
    Info "Distribution archive unavailable; staging standalone compatibility assets..."
    Invoke-WebRequest -Uri "$ReleaseBase/$Latest/$Target.exe" -OutFile "$StageBin\freak.exe" -UseBasicParsing
    Assert-DownloadedAssetChecksum "$StageBin\freak.exe" "$Target.exe"
    Invoke-WebRequest -Uri "$ReleaseBase/$Latest/hangar-windows-x64.exe" -OutFile "$StageBin\hangar.exe" -UseBasicParsing
    Assert-DownloadedAssetChecksum "$StageBin\hangar.exe" "hangar-windows-x64.exe"
    Invoke-WebRequest -Uri "$RawBase/packaging/distribution-files.manifest" -OutFile $StageManifest -UseBasicParsing
    Assert-DownloadedAssetChecksum $StageManifest "raw/packaging/distribution-files.manifest"
    foreach ($entry in Get-ManifestEntries) {
        $destination = Join-Path $StageDir $entry.Destination
        New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
        Invoke-WebRequest -Uri "$RawBase/$($entry.Source)" -OutFile $destination -UseBasicParsing
        Assert-DownloadedAssetChecksum $destination "raw/$($entry.Source)"
    }
}

function Start-DeferredBinaryReplacement {
    $quotedBin = $BinDir.Replace("'", "''")
    $quotedInstallDir = $InstallDir.Replace("'", "''")
    $replacementWaitPid = $PID
    $replacementWaitStart = (Get-Process -Id $PID).StartTime.ToFileTimeUtc()
    $pendingPath = Join-Path $BinDir ".freak-upgrade-pending"
    $failedPath = Join-Path $BinDir ".freak-upgrade-failed"
    $expectedFreakHash = (Get-FileHash -LiteralPath (Join-Path $BinDir "freak.exe.next") -Algorithm SHA256).Hash
    $expectedHangarHash = (Get-FileHash -LiteralPath (Join-Path $BinDir "hangar.exe.next") -Algorithm SHA256).Hash
    $helperLockPath = Join-Path $BinDir ".freak-upgrade-helper.lock"
    $helperReadyPath = Join-Path $BinDir ".freak-upgrade-helper.ready"
    Remove-Item -LiteralPath $helperLockPath, $helperReadyPath -Force -ErrorAction SilentlyContinue
    $helperStartDelayMs = 0
    if ($env:FREAK_INSTALL_TEST_HELPER_START_DELAY_MS -match '^[0-9]+$') {
        $helperStartDelayMs = [int]$env:FREAK_INSTALL_TEST_HELPER_START_DELAY_MS
    }
    Set-Content -LiteralPath $pendingPath -Value "$Latest|wait-pid=$replacementWaitPid|wait-start=$replacementWaitStart|freak-sha256=$expectedFreakHash|hangar-sha256=$expectedHangarHash" -Encoding UTF8
    Remove-Item -LiteralPath $failedPath -Force -ErrorAction SilentlyContinue
    $apply = @"
`$ErrorActionPreference = 'Stop'
`$bin = '$quotedBin'
`$installDir = '$quotedInstallDir'
`$installLockPath = Join-Path `$installDir '.freak-install.lock'
`$pending = Join-Path `$bin '.freak-upgrade-pending'
`$failed = Join-Path `$bin '.freak-upgrade-failed'
`$helperLockPath = Join-Path `$bin '.freak-upgrade-helper.lock'
`$helperReadyPath = Join-Path `$bin '.freak-upgrade-helper.ready'
if ($helperStartDelayMs -gt 0) { Start-Sleep -Milliseconds $helperStartDelayMs }
`$helperLock = [System.IO.File]::Open(
    `$helperLockPath,
    [System.IO.FileMode]::OpenOrCreate,
    [System.IO.FileAccess]::ReadWrite,
    [System.IO.FileShare]::None
)
`$helperStart = (Get-Process -Id `$PID).StartTime.ToFileTimeUtc()
Set-Content -LiteralPath `$helperReadyPath -Value "`$PID|`$helperStart" -Encoding UTF8
`$backupRoot = Join-Path `$bin '.freak-binary-backup'
`$retiredRoot = Join-Path `$bin '.freak-binary-retired'
`$names = @('freak.exe', 'hangar.exe')
`$expectedHashes = @{
    'freak.exe' = '$expectedFreakHash'
    'hangar.exe' = '$expectedHangarHash'
}
`$retiredCleanupFailuresRemaining = 0
if (`$env:FREAK_INSTALL_TEST_RETIRED_CLEANUP_FAILURES -match '^[0-9]+$') {
    `$retiredCleanupFailuresRemaining = [int]`$env:FREAK_INSTALL_TEST_RETIRED_CLEANUP_FAILURES
}
`$terminalCleanupFailuresRemaining = 0
if (`$env:FREAK_INSTALL_TEST_TERMINAL_CLEANUP_FAILURES -match '^[0-9]+$') {
    `$terminalCleanupFailuresRemaining = [int]`$env:FREAK_INSTALL_TEST_TERMINAL_CLEANUP_FAILURES
}

function Restore-BinaryBackup {
    if (-not (Test-Path -LiteralPath `$backupRoot -PathType Container)) { return `$true }
    `$restoreFailed = `$false
    foreach (`$name in `$names) {
        `$live = Join-Path `$bin `$name
        `$backup = Join-Path `$backupRoot `$name
        `$missing = Join-Path `$backupRoot (`$name + '.missing')
        try {
            if (Test-Path -LiteralPath `$backup) {
                Remove-Item -LiteralPath `$live -Force -ErrorAction SilentlyContinue
                Move-Item -LiteralPath `$backup -Destination `$live
            } elseif (Test-Path -LiteralPath `$missing) {
                Remove-Item -LiteralPath `$live -Force -ErrorAction SilentlyContinue
            }
        } catch {
            `$restoreFailed = `$true
        }
    }
    if (-not `$restoreFailed) {
        try { Remove-Item -LiteralPath `$backupRoot -Recurse -Force } catch { `$restoreFailed = `$true }
    }
    return -not `$restoreFailed
}

# The installer cannot replace the executable that launched it. Wait for that
# exact process, then retain durable .next/pending state until both binaries
# have been swapped and hash-verified as one recoverable transaction.
`$waitDeadline = [DateTime]::UtcNow.AddHours(24)
while ([DateTime]::UtcNow -lt `$waitDeadline) {
    `$owner = Get-Process -Id $replacementWaitPid -ErrorAction SilentlyContinue
    if (-not `$owner) { break }
    if (`$owner.StartTime.ToFileTimeUtc() -ne $replacementWaitStart) { break }
    Start-Sleep -Milliseconds 250
}
if ([DateTime]::UtcNow -ge `$waitDeadline) {
    Set-Content -LiteralPath `$failed -Value 'timed out waiting for the invoking installer process' -Encoding UTF8
    exit 1
}
`$installLock = `$null
`$installLockDeadline = [DateTime]::UtcNow.AddMinutes(5)
while (-not `$installLock -and [DateTime]::UtcNow -lt `$installLockDeadline) {
    try {
        `$installLock = [System.IO.FileStream]::new(
            `$installLockPath,
            [System.IO.FileMode]::OpenOrCreate,
            [System.IO.FileAccess]::ReadWrite,
            [System.IO.FileShare]::None,
            1,
            [System.IO.FileOptions]::DeleteOnClose
        )
    } catch {
        Start-Sleep -Milliseconds 100
    }
}
if (-not `$installLock) {
    Set-Content -LiteralPath `$failed -Value 'timed out acquiring the deferred installer lock' -Encoding UTF8
    exit 1
}
`$deadline = [DateTime]::UtcNow.AddHours(24)
while ([DateTime]::UtcNow -lt `$deadline) {
    try {
        if (-not (Restore-BinaryBackup)) { throw 'could not restore an interrupted binary transaction' }
        Remove-Item -LiteralPath `$retiredRoot -Recurse -Force -ErrorAction SilentlyContinue
        # Validate both durable staged files against the installer-recorded
        # hashes before moving either live binary out of the way.
        foreach (`$name in `$names) {
            `$next = Join-Path `$bin (`$name + '.next')
            if (-not (Test-Path -LiteralPath `$next -PathType Leaf)) { throw "missing staged binary: `$next" }
            if ((Get-FileHash -LiteralPath `$next -Algorithm SHA256).Hash -ne `$expectedHashes[`$name]) {
                throw "staged binary hash mismatch: `$name"
            }
        }
        New-Item -ItemType Directory -Path `$backupRoot -Force | Out-Null
        foreach (`$name in `$names) {
            `$target = Join-Path `$bin `$name
            `$backup = Join-Path `$backupRoot `$name
            if (Test-Path -LiteralPath `$target -PathType Leaf) {
                Move-Item -LiteralPath `$target -Destination `$backup
            } else {
                New-Item -ItemType File -Path (Join-Path `$backupRoot (`$name + '.missing')) -Force | Out-Null
            }
        }
        foreach (`$name in `$names) {
            `$next = Join-Path `$bin (`$name + '.next')
            `$target = Join-Path `$bin `$name
            Copy-Item -LiteralPath `$next -Destination `$target -Force
            if ((Get-FileHash -LiteralPath `$target -Algorithm SHA256).Hash -ne `$expectedHashes[`$name]) {
                throw "binary verification failed: `$name"
            }
        }
        # Renaming the complete old-binary directory is the commit point.
        # Both live binaries now match their staged hashes. Keep the durable
        # .next inputs until every retired binary is gone so a cleanup retry
        # can validate and reapply the committed pair safely.
        Move-Item -LiteralPath `$backupRoot -Destination `$retiredRoot
        `$retiredClean = `$false
        for (`$attempt = 0; `$attempt -lt 200; `$attempt++) {
            if (`$retiredCleanupFailuresRemaining -gt 0) {
                `$retiredCleanupFailuresRemaining--
            } else {
                Remove-Item -LiteralPath `$retiredRoot -Recurse -Force -ErrorAction SilentlyContinue
            }
            if (-not (Test-Path -LiteralPath `$retiredRoot)) {
                `$retiredClean = `$true
                break
            }
            Start-Sleep -Milliseconds 50
        }
        if (-not `$retiredClean) {
            throw "retired binary cleanup did not complete"
        }
        `$terminalClean = `$false
        for (`$attempt = 0; `$attempt -lt 200; `$attempt++) {
            if (`$terminalCleanupFailuresRemaining -gt 0) {
                `$terminalCleanupFailuresRemaining--
            } else {
                foreach (`$name in `$names) {
                    Remove-Item -LiteralPath (Join-Path `$bin (`$name + '.next')) -Force -ErrorAction SilentlyContinue
                }
                Remove-Item -LiteralPath `$failed -Force -ErrorAction SilentlyContinue
            }
            `$nextRemain = @(`$names | Where-Object {
                Test-Path -LiteralPath (Join-Path `$bin (`$_ + '.next'))
            })
            if (`$nextRemain.Count -eq 0 -and -not (Test-Path -LiteralPath `$failed)) {
                `$terminalClean = `$true
                break
            }
            Start-Sleep -Milliseconds 50
        }
        if (-not `$terminalClean) {
            throw "terminal transaction cleanup did not complete"
        }

        `$helperLock.Dispose()
        `$helperLock = `$null
        `$helperMarkersClean = `$false
        for (`$attempt = 0; `$attempt -lt 200; `$attempt++) {
            Remove-Item -LiteralPath `$helperReadyPath, `$helperLockPath -Force -ErrorAction SilentlyContinue
            if (-not (Test-Path -LiteralPath `$helperReadyPath) -and
                -not (Test-Path -LiteralPath `$helperLockPath)) {
                `$helperMarkersClean = `$true
                break
            }
            Start-Sleep -Milliseconds 50
        }
        if (-not `$helperMarkersClean) {
            Set-Content -LiteralPath `$failed -Value 'helper marker cleanup did not complete' -Encoding UTF8
            exit 1
        }

        # Test-only barrier for the terminal ownership window. The shared
        # installer lock must remain authoritative after helper markers are
        # gone and until the durable pending marker is removed.
        if (`$env:FREAK_INSTALL_TEST_PENDING_CLEANUP_READY) {
            Set-Content -LiteralPath `$env:FREAK_INSTALL_TEST_PENDING_CLEANUP_READY -Value 'ready' -Encoding UTF8
        }
        if (`$env:FREAK_INSTALL_TEST_PENDING_CLEANUP_RELEASE) {
            `$testBarrierDeadline = [DateTime]::UtcNow.AddMinutes(3)
            while (-not (Test-Path -LiteralPath `$env:FREAK_INSTALL_TEST_PENDING_CLEANUP_RELEASE) -and
                [DateTime]::UtcNow -lt `$testBarrierDeadline) {
                Start-Sleep -Milliseconds 50
            }
        }

        # Pending is the externally visible completion signal. Remove it only
        # after all transaction state, retired binaries, and helper markers are gone.
        `$pendingClean = `$false
        for (`$attempt = 0; `$attempt -lt 200; `$attempt++) {
            Remove-Item -LiteralPath `$pending -Force -ErrorAction SilentlyContinue
            if (-not (Test-Path -LiteralPath `$pending)) {
                `$pendingClean = `$true
                break
            }
            Start-Sleep -Milliseconds 50
        }
        if (-not `$pendingClean) {
            Set-Content -LiteralPath `$failed -Value 'pending marker cleanup did not complete' -Encoding UTF8
            exit 1
        }
        `$installLock.Dispose()
        `$installLock = `$null
        exit 0
    } catch {
        `$detail = `$_.Exception.Message
        if (`$env:FREAK_INSTALL_TEST_RETRY_OBSERVED) {
            Add-Content -LiteralPath `$env:FREAK_INSTALL_TEST_RETRY_OBSERVED -Value `$detail -Encoding UTF8
        }
        Restore-BinaryBackup | Out-Null
        Set-Content -LiteralPath `$failed -Value `$detail -Encoding UTF8
        Start-Sleep -Seconds 1
    }
}
exit 1
"@
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($apply))
    $helper = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile -NonInteractive -ExecutionPolicy Bypass -EncodedCommand $encoded" -WindowStyle Hidden -PassThru
    if ($env:FREAK_INSTALL_TEST_HELPER_PID) {
        Set-Content -LiteralPath $env:FREAK_INSTALL_TEST_HELPER_PID -Value $helper.Id -Encoding UTF8
    }
    $helperReady = $false
    for ($attempt = 0; $attempt -lt 100; $attempt++) {
        if ($helper.HasExited) { break }
        try {
            if (Test-Path -LiteralPath $helperReadyPath -PathType Leaf) {
                $parts = (Get-Content -LiteralPath $helperReadyPath -Raw).Trim().Split('|')
                if ($parts.Count -eq 2 -and [int]$parts[0] -eq $helper.Id -and
                    [long]$parts[1] -eq $helper.StartTime.ToFileTimeUtc() -and
                    (Test-DeferredUpgradeHelperLockHeld)) {
                    $helperReady = $true
                    break
                }
            }
        } catch { }
        Start-Sleep -Milliseconds 50
    }
    if (-not $helperReady -and (Test-Path -LiteralPath $pendingPath -PathType Leaf)) {
        $helperTerminated = $false
        try {
            if (-not $helper.HasExited) { Stop-Process -Id $helper.Id -Force -ErrorAction Stop }
            $helperTerminated = $helper.WaitForExit(5000)
        } catch { }
        try { $helper.Refresh(); $helperTerminated = $helper.HasExited } catch { }
        if (-not $helperTerminated) {
            $script:DeferredHelperUnsafe = $true
            Set-Content -LiteralPath $helperReadyPath -Value "$($helper.Id)|$($helper.StartTime.ToFileTimeUtc())" -Encoding UTF8
            throw "Deferred FREAK binary replacement helper could not be stopped safely"
        }
        if (Test-DeferredUpgradeHelperLockHeld) {
            $script:DeferredHelperUnsafe = $true
            throw "Deferred FREAK binary replacement helper could not be stopped safely"
        }
        Remove-Item -LiteralPath $helperReadyPath, $helperLockPath -Force -ErrorAction SilentlyContinue
        throw "Deferred FREAK binary replacement helper did not become ready"
    }
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

        if ($UpgradeMode) {
            # This marker is the public build/run exclusion guard.  Publish it
            # before the first live payload path moves, then replace its
            # preparing state with the hash-bound deferred transaction state.
            New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
            Set-Content -LiteralPath "$BinDir\.freak-upgrade-pending" -Value "$Latest|preparing=1" -Encoding UTF8
            if (Test-Truthy $env:FREAK_INSTALL_TEST_PAUSE_AFTER_PENDING) {
                if ($env:FREAK_INSTALL_TEST_PENDING_READY) {
                    Set-Content -LiteralPath $env:FREAK_INSTALL_TEST_PENDING_READY -Value "ready" -Encoding UTF8
                }
                Start-Sleep -Seconds 3
            }
        }

        foreach ($item in $items) {
            $item.HadOriginal = Test-Path -LiteralPath $item.Live
            if ($item.HadOriginal) {
                New-Item -ItemType Directory -Path (Split-Path -Parent $item.Backup) -Force | Out-Null
                Move-Item -LiteralPath $item.Live -Destination $item.Backup
            } else {
                New-Item -ItemType Directory -Path (Split-Path -Parent $item.Backup) -Force | Out-Null
                Set-Content -LiteralPath "$($item.Backup).missing" -Value "missing" -Encoding UTF8
            }
            $item.Prepared = $true
        }
        if (Test-Truthy $env:FREAK_INSTALL_TEST_PAUSE_AFTER_BACKUP) {
            if ($env:FREAK_INSTALL_TEST_TRANSACTION_READY) {
                Set-Content -LiteralPath $env:FREAK_INSTALL_TEST_TRANSACTION_READY -Value "ready" -Encoding UTF8
            }
            Start-Sleep -Seconds 30
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
        } elseif ($script:RecoveredPendingUpgrade) {
            # A direct installer replaces both binaries synchronously. Once
            # that transaction commits it also resolves any orphaned deferred
            # state discovered while acquiring the install lock.
            Remove-Item -LiteralPath "$BinDir\freak.exe.next", "$BinDir\hangar.exe.next" -Force -ErrorAction SilentlyContinue
            Remove-Item -LiteralPath "$BinDir\.freak-upgrade-failed", "$BinDir\.freak-upgrade-pending", "$BinDir\.freak-upgrade-helper.ready", "$BinDir\.freak-upgrade-helper.lock" -Force -ErrorAction SilentlyContinue
        }
    } catch {
        $applyError = $_.Exception.Message
        if ($script:DeferredHelperUnsafe) {
            Err "Could not safely roll back while the deferred binary helper remains active; pending state was preserved ($applyError)"
        }
        Remove-Item -LiteralPath "$BinDir\freak.exe.next", "$BinDir\hangar.exe.next" -Force -ErrorAction SilentlyContinue
        if ($UpgradeMode -and -not $script:RecoveredPendingUpgrade) {
            Remove-Item -LiteralPath "$BinDir\.freak-upgrade-pending" -Force -ErrorAction SilentlyContinue
        }
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
    Acquire-InstallLock
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
        if ($ZipOk) { Assert-DownloadedAssetChecksum $ZipPath "$Target.zip" }
    }

    if ($ZipOk) {
        try {
            Info "Extracting distribution..."
            Expand-Archive -LiteralPath $ZipPath -DestinationPath $ExtractDir -Force
            Copy-Item -LiteralPath "$ExtractDir\freak\bin\freak.exe" -Destination "$StageBin\freak.exe" -Force
            if (-not (Test-Path -LiteralPath "$ExtractDir\freak\bin\hangar.exe" -PathType Leaf)) {
                Err "Distribution archive is missing Hangar"
            }
            Copy-Item -LiteralPath "$ExtractDir\freak\bin\hangar.exe" -Destination "$StageBin\hangar.exe" -Force
            Copy-Item -Path "$ExtractDir\freak\runtime\*" -Destination $StageRuntime -Recurse -Force
            Copy-Item -Path "$ExtractDir\freak\std\*" -Destination $StageStd -Recurse -Force
            $archiveManifest = "$ExtractDir\freak\distribution-files.manifest"
            if (Test-Path -LiteralPath $archiveManifest -PathType Leaf) {
                Copy-Item -LiteralPath $archiveManifest -Destination $StageManifest -Force
            } elseif ($script:LegacyV014Archive) {
                $legacyEntries = [System.Collections.Generic.List[string]]::new()
                foreach ($file in Get-ChildItem -LiteralPath $StageRuntime -File -Recurse | Sort-Object FullName) {
                    $relative = $file.FullName.Substring($StageRuntime.Length).TrimStart([char[]]@('\', '/')).Replace('\', '/')
                    $legacyEntries.Add("freakc/runtime/$relative|runtime/$relative")
                }
                foreach ($file in Get-ChildItem -LiteralPath $StageStd -File -Recurse | Sort-Object FullName) {
                    $relative = $file.FullName.Substring($StageStd.Length).TrimStart([char[]]@('\', '/')).Replace('\', '/')
                    $legacyEntries.Add("std/$relative|std/$relative")
                }
                if ($legacyEntries.Count -eq 0) { Err "Legacy v0.14.0 archive contained no runtime or standard-library payload" }
                [System.IO.File]::WriteAllLines(
                    $StageManifest,
                    $legacyEntries,
                    [System.Text.UTF8Encoding]::new($false)
                )
                Info "Generated a compatibility manifest for the verified v0.14.0 archive"
            } else {
                Err "Distribution archive is missing distribution-files.manifest"
            }
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
    Release-InstallLock
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
if ($UpgradeMode) {
    Ok "FREAK $Latest payload staged successfully!"
} else {
    Ok "FREAK $Latest installed successfully!"
}
Ok "  Compiler: $BinDir\freak.exe"
Ok "  Hangar:   $BinDir\hangar.exe"
Ok "  Runtime:  $InstallDir\runtime\"
Ok "  Std lib:  $InstallDir\std\"
if ($UpgradeMode) {
    Ok "  Binary replacement will complete after the invoking process exits."
    Ok "  Durable state: $BinDir\.freak-upgrade-pending"
}
if (-not (Find-Clang)) { Warn "Clang is still missing. Install LLVM before building FREAK programs." }
Ok "Open a new terminal and verify the complete toolchain with: freak doctor"
Ok '"It was always going to end this way."'
