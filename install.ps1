# FREAK Language Installer — Windows
# Usage: irm https://raw.githubusercontent.com/FREAK-lang-dev/Freak-lang/main/install.ps1 | iex
$ErrorActionPreference = "Stop"

$Repo = "FREAK-lang-dev/Freak-lang"
$InstallDir = if ($env:FREAK_HOME) { $env:FREAK_HOME } else { "$env:APPDATA\freak" }
$BinDir = "$InstallDir\bin"

function Info($msg)  { Write-Host "> $msg" -ForegroundColor Cyan }
function Ok($msg)    { Write-Host "> $msg" -ForegroundColor Green }
function Err($msg)   { Write-Host "> $msg" -ForegroundColor Red; throw $msg }

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

        # Install from extracted zip
        New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
        New-Item -ItemType Directory -Path "$InstallDir\runtime" -Force | Out-Null
        New-Item -ItemType Directory -Path "$InstallDir\std" -Force | Out-Null

        Copy-Item "$TmpDir\freak\bin\freak.exe" "$BinDir\freak.exe" -Force
        Copy-Item "$TmpDir\freak\bin\hangar.exe" "$BinDir\hangar.exe" -Force -ErrorAction SilentlyContinue
        if (-not (Test-Path "$BinDir\hangar.exe")) { Copy-Item "$BinDir\freak.exe" "$BinDir\hangar.exe" }
        Copy-Item "$TmpDir\freak\runtime\*" "$InstallDir\runtime\" -Force -ErrorAction SilentlyContinue
        Copy-Item "$TmpDir\freak\std\*" "$InstallDir\std\" -Force -ErrorAction SilentlyContinue
    } else {
        # Fallback: download standalone binary + individual files from source
        Info "Zip not available, falling back to standalone binary..."
        $DownloadUrl = "https://github.com/$Repo/releases/download/$Latest/$Target.exe"

        New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
        $OutPath = "$BinDir\freak.exe"

        try {
            Invoke-WebRequest -Uri $DownloadUrl -OutFile $OutPath -UseBasicParsing
        } catch {
            Err "Download failed: $_"
        }

        # Create hangar.exe (BusyBox pattern — same binary, dispatches on argv[0])
        Copy-Item "$BinDir\freak.exe" "$BinDir\hangar.exe" -Force

        # Download runtime files from source tree
        $RuntimeDir = "$InstallDir\runtime"
        New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null
        $RuntimeUrl = "https://raw.githubusercontent.com/$Repo/$Latest/freakc/runtime"

        foreach ($file in @("freak_runtime.c", "freak_runtime.h", "freak_llvm_runtime.c")) {
            try {
                Invoke-WebRequest -Uri "$RuntimeUrl/$file" -OutFile "$RuntimeDir\$file" -UseBasicParsing 2>$null
            } catch {
                # Non-fatal
            }
        }

        # Download standard library
        $StdDir = "$InstallDir\std"
        New-Item -ItemType Directory -Path $StdDir -Force | Out-Null
        $StdUrl = "https://raw.githubusercontent.com/$Repo/$Latest/std"

        foreach ($file in @("math.fk", "math3d.fk", "string.fk", "convert.fk", "algorithm.fk", "json.fk", "http.fk", "version.fk")) {
            try {
                Invoke-WebRequest -Uri "$StdUrl/$file" -OutFile "$StdDir\$file" -UseBasicParsing 2>$null
            } catch {
                # Non-fatal
            }
        }
    }
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
