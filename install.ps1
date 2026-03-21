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
$Target = "freakc-windows-x64.exe"
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

# Download compiler
$DownloadUrl = "https://github.com/$Repo/releases/download/$Latest/$Target"
Info "Downloading $Target..."

New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
$OutPath = "$BinDir\freakc.exe"

try {
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $OutPath -UseBasicParsing
} catch {
    Err "Download failed: $_"
}

# Download runtime files
$RuntimeDir = "$InstallDir\runtime"
New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null
$RuntimeUrl = "https://raw.githubusercontent.com/$Repo/$Latest/freakc/runtime"

foreach ($file in @("freak_runtime.c", "freak_runtime.h", "freak_llvm_runtime.c")) {
    try {
        Invoke-WebRequest -Uri "$RuntimeUrl/$file" -OutFile "$RuntimeDir\$file" -UseBasicParsing 2>$null
    } catch {
        # Non-fatal — runtime files are optional for --llvm-only workflows
    }
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
Ok "  Compiler: $OutPath"
Ok "  Runtime:  $RuntimeDir\"
Ok ""
Ok "Open a new terminal, then try:"
Ok "  freakc version"
Ok "  freakc build hello.fk"
Ok "  freakc run hello.fk"
Ok "  freakc hangar init my-project"
Ok ""
Ok "`"It was always going to end this way.`""
