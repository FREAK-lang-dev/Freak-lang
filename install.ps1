# FREAK Language Installer — Windows
# Usage: irm https://raw.githubusercontent.com/FREAK-lang-dev/Freak-lang/main/install.ps1 | iex
$ErrorActionPreference = "Stop"

$Repo = "FREAK-lang-dev/Freak-lang"
$InstallDir = if ($env:FREAK_HOME) { $env:FREAK_HOME } else { "$env:APPDATA\freak" }
$InstallDir = [System.IO.Path]::GetFullPath($InstallDir)
$BinDir = "$InstallDir\bin"

function Info($msg)  { Write-Host "> $msg" -ForegroundColor Cyan }
function Ok($msg)    { Write-Host "> $msg" -ForegroundColor Green }
function Err($msg)   { Write-Host "> $msg" -ForegroundColor Red; throw $msg }

if ($InstallDir -eq [System.IO.Path]::GetPathRoot($InstallDir)) {
    Err "Refusing unsafe FREAK install directory: $InstallDir"
}
$InstallDir = $InstallDir.TrimEnd([char[]]@('\', '/'))
$BinDir = "$InstallDir\bin"

# Only x64 Windows binaries for now — ARM64 will come later
$Target = "freak-windows-x64"
Info "Detected platform: windows-x64"

# Get latest release
Info "Fetching latest release..."
try {
    $Release = Invoke-RestMethod "https://api.github.com/repos/$Repo/releases/latest"
    $Latest = $Release.tag_name
} catch {
    Err "Could not fetch latest release. Check https://github.com/$Repo/releases"
}

Info "Latest version: $Latest"

# Try downloading the full distribution zip first (includes runtime .o + std)
$ZipUrl = "https://github.com/$Repo/releases/download/$Latest/$Target.zip"
$ZipOk = $false

$TmpDir = Join-Path ([System.IO.Path]::GetTempPath()) "freak-install-$(Get-Random)"
New-Item -ItemType Directory -Path $TmpDir -Force | Out-Null
$StageDir = Join-Path $TmpDir "stage"
$StageBin = Join-Path $StageDir "bin"
$StageRuntime = Join-Path $StageDir "runtime"
$StageRuntimeUi = Join-Path $StageRuntime "ui"
$StageStd = Join-Path $StageDir "std"
New-Item -ItemType Directory -Path $StageBin, $StageRuntimeUi, $StageStd -Force | Out-Null

$RuntimeFiles = @("freak_runtime.c", "freak_runtime.h", "freak_llvm_runtime.c")
$RuntimeUiFiles = @("win32_backend.c", "freak_ui_platform.h")
$StdFiles = @("math.fk", "math3d.fk", "zip.fk", "string.fk", "convert.fk", "algorithm.fk", "json.fk", "http.fk", "version.fk", "runtime.fk")

function Assert-StagedPayload {
    foreach ($path in @("$StageBin\freak.exe", "$StageBin\hangar.exe")) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { Err "Staged payload is missing $path" }
    }
    foreach ($file in $RuntimeFiles) {
        if (-not (Test-Path -LiteralPath "$StageRuntime\$file" -PathType Leaf)) { Err "Staged runtime is missing $file" }
    }
    foreach ($file in $RuntimeUiFiles) {
        if (-not (Test-Path -LiteralPath "$StageRuntimeUi\$file" -PathType Leaf)) { Err "Staged runtime is missing ui\$file" }
    }
    foreach ($file in $StdFiles) {
        if (-not (Test-Path -LiteralPath "$StageStd\$file" -PathType Leaf)) { Err "Staged stdlib is missing $file" }
    }
}

function Install-StagedPayload {
    Assert-StagedPayload
    New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
    Copy-Item -LiteralPath "$StageBin\freak.exe" -Destination "$BinDir\freak.exe" -Force
    Copy-Item -LiteralPath "$StageBin\hangar.exe" -Destination "$BinDir\hangar.exe" -Force

    # runtime and std are installer-managed trees. Replace only those exact
    # direct children so files retired by a newer release cannot linger.
    foreach ($managed in @("runtime", "std")) {
        $target = [System.IO.Path]::GetFullPath((Join-Path $InstallDir $managed))
        if ([System.IO.Directory]::GetParent($target).FullName -ne $InstallDir) {
            Err "Refusing unsafe managed payload path: $target"
        }
        if (Test-Path -LiteralPath $target) {
            Remove-Item -LiteralPath $target -Recurse -Force
        }
        New-Item -ItemType Directory -Path $target -Force | Out-Null
    }
    Copy-Item -Path "$StageRuntime\*" -Destination "$InstallDir\runtime" -Recurse -Force
    Copy-Item -Path "$StageStd\*" -Destination "$InstallDir\std" -Recurse -Force
}

try {
    Info "Downloading $Target.zip..."
    $ZipPath = "$TmpDir\freak.zip"
    try {
        Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath -UseBasicParsing
        $ZipOk = $true
    } catch {
        # Zip not available, fall back to standalone binary
    }

    if ($ZipOk) {
        Info "Extracting distribution..."
        Expand-Archive -Path $ZipPath -DestinationPath $TmpDir -Force

        Copy-Item -LiteralPath "$TmpDir\freak\bin\freak.exe" -Destination "$StageBin\freak.exe" -Force
        if (Test-Path -LiteralPath "$TmpDir\freak\bin\hangar.exe") {
            Copy-Item -LiteralPath "$TmpDir\freak\bin\hangar.exe" -Destination "$StageBin\hangar.exe" -Force
        } else {
            Copy-Item -LiteralPath "$StageBin\freak.exe" -Destination "$StageBin\hangar.exe" -Force
        }
        Copy-Item -Path "$TmpDir\freak\runtime\*" -Destination $StageRuntime -Recurse -Force
        Copy-Item -Path "$TmpDir\freak\std\*" -Destination $StageStd -Recurse -Force
    } else {
        # Fallback: download standalone binary + individual files from source
        Info "Zip not available, falling back to standalone binary..."
        $DownloadUrl = "https://github.com/$Repo/releases/download/$Latest/$Target.exe"

        $OutPath = "$StageBin\freak.exe"

        try {
            Invoke-WebRequest -Uri $DownloadUrl -OutFile $OutPath -UseBasicParsing
        } catch {
            Err "Download failed: $_"
        }

        # Create hangar.exe (BusyBox pattern — same binary, dispatches on argv[0])
        Copy-Item -LiteralPath "$StageBin\freak.exe" -Destination "$StageBin\hangar.exe" -Force

        # Download runtime files from source tree
        $RuntimeUrl = "https://raw.githubusercontent.com/$Repo/$Latest/freakc/runtime"

        foreach ($file in $RuntimeFiles) {
            Invoke-WebRequest -Uri "$RuntimeUrl/$file" -OutFile "$StageRuntime\$file" -UseBasicParsing
        }
        foreach ($file in $RuntimeUiFiles) {
            Invoke-WebRequest -Uri "$RuntimeUrl/ui/$file" -OutFile "$StageRuntimeUi\$file" -UseBasicParsing
        }

        # Download standard library
        $StdUrl = "https://raw.githubusercontent.com/$Repo/$Latest/std"

        foreach ($file in $StdFiles) {
            Invoke-WebRequest -Uri "$StdUrl/$file" -OutFile "$StageStd\$file" -UseBasicParsing
        }
    }

    Install-StagedPayload
} finally {
    Remove-Item -Path $TmpDir -Recurse -Force -ErrorAction SilentlyContinue
}

# Add to PATH
$UserPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($UserPath -notlike "*$BinDir*") {
    [Environment]::SetEnvironmentVariable("PATH", "$BinDir;$UserPath", "User")
    Info "Added $BinDir to user PATH"
}

# Update current session PATH too
if ($env:PATH -notlike "*$BinDir*") {
    $env:PATH = "$BinDir;$env:PATH"
}

Ok ""
Ok "FREAK $Latest installed successfully!"
Ok ""
Ok "  Compiler: $BinDir\freak.exe"
Ok "  Hangar:   $BinDir\hangar.exe"
Ok "  Runtime:  $InstallDir\runtime\"
Ok "  Std lib:  $InstallDir\std\"
Ok ""
Ok "Open a new terminal, then try:"
Ok "  freak version"
Ok "  freak build hello.fk"
Ok "  freak run hello.fk"
Ok "  hangar init my-project"
Ok ""
Ok "`"It was always going to end this way.`""
