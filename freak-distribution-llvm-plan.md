# FREAK — Distribution & LLVM Backend Implementation Plan

---

## Part 1 — Rethinking the Compiler Backend

### Why Drop C as the Primary Target

The C backend was the right call to reach M15 (self-hosting). It got you there fast.
But it comes with real costs now that you're past bootstrap:

- **Clang dependency** — users need a working C toolchain just to run FREAK code
- **Slow compile cycle** — FREAK → C → Clang → binary is three hops
- **Limited optimization** — you're relying on Clang to clean up your emitted C
- **JIT is awkward** — you can't easily JIT from C output
- **Debug info is indirect** — source maps go through C line numbers

Since you're already adding LLVM LLD, the right move is to go **FREAK → LLVM IR → LLD → native binary** directly.

### New Primary Pipeline

```
freak source
    ↓  lexer / parser (unchanged)
    ↓  type checker (unchanged)
    ↓  IR lowering (new)
LLVM IR (.ll text or bitcode)
    ↓  llc / opt (LLVM optimizer passes)
    ↓  LLD (LLVM's linker)
native binary
```

The C backend doesn't die — it becomes an optional target (`freak build --target c`) for portability to embedded platforms or environments without LLVM.

### What LLVM IR Buys You

| Feature | C backend | LLVM IR backend |
|---|---|---|
| JIT compilation | ❌ painful | ✅ native (OrcJIT) |
| Optimization passes | Clang does it | LLVM does it directly |
| Cross-compilation | Need cross-Clang | Built into LLVM |
| Debug info (DWARF) | Indirect | Direct via DIBuilder |
| LTO (link-time opt) | Limited | Full LLVM LTO |
| Clang dependency | Required | Not needed |
| Compile speed | 3 hops | 2 hops |

---

## Part 2 — LLVM IR Backend Implementation

### Milestone Map

```
LB1 — LLVM IR emitter: hello world compiles via llc + lld
LB2 — All FREAK primitives map to LLVM types
LB3 — All control flow emits correct IR (if/when/loops)
LB4 — Shapes (structs) and impl methods work
LB5 — freak_runtime.h functions replaced by IR intrinsics
LB6 — freak build uses LLVM backend by default
LB7 — JIT mode: freak run executes via OrcJIT without writing a binary
LB8 — Optimization levels: --opt=0/1/2/3 pass through to LLVM opt
LB9 — Cross-compilation: freak build --target x86_64-linux from any host
LB10 — Debug info: source line numbers in DWARF via DIBuilder
```

### Type Mapping: FREAK → LLVM IR

| FREAK type | LLVM IR type |
|---|---|
| `int` | `i64` |
| `uint` | `i64` (unsigned semantics) |
| `num` | `double` |
| `tiny` | `i8` |
| `bool` | `i1` |
| `word` | `%freak_word = type { i8*, i64, i64 }` (ptr, byte_len, char_count) |
| `maybe<T>` | `%freak_maybe_T = type { i1, T }` |
| `result<T,E>` | `%freak_result_T_E = type { i1, T, E }` (tagged union) |
| `List<T>` | `%freak_list_T = type { T*, i64, i64 }` (ptr, len, cap) |
| `shape Foo { }` | `%Foo = type { field1_type, field2_type, ... }` |
| `task f(...) -> T` | `define T @f(...)` |

### IR Emitter Structure

```
freakc/
  ir/
    emitter.py       # main LLVM IR emitter (replaces c_emitter.py as primary)
    types.py         # FREAK type → LLVM IR type string
    runtime.py       # IR declarations for runtime functions (word, list ops)
    intrinsics.py    # LLVM intrinsics (memcpy, memset, llvm.expect, etc.)
    debug.py         # DIBuilder wrappers for DWARF debug info
    jit.py           # OrcJIT integration via llvmlite or ctypes
```

### Runtime Strategy: Header → IR Declarations

The old `freak_runtime.h` becomes a set of `declare` statements at the top of every emitted `.ll` file:

```llvm
; word type
%freak_word = type { i8*, i64, i64 }

; runtime function declarations
declare %freak_word @freak_word_lit(i8*)
declare void @freak_say(%freak_word)
declare %freak_word @freak_word_concat(%freak_word, %freak_word)
declare %freak_word @freak_interpolate(i8*, ...)
declare void @freak_panic(%freak_word)
```

The runtime `.c` file compiles once to a `.a` static library. LLD links it in. Users never see it.

### JIT Mode (LB7)

`freak run file.fk` today: compiles to binary → executes.
`freak run file.fk` after LB7: loads LLVM IR into OrcJIT → executes in-process, no binary written.

This makes the REPL and hot-reload viable later.

Implementation via **llvmlite** (Python LLVM bindings) or by shelling out to `lli` (LLVM interpreter) as a stepping stone.

---

## Part 3 — Hangar Bootstrapping Itself

### The Model: Hangar IS the Installer

Current assumption: install script → download freakc binary → user can now use FREAK.

New model:
```
install.sh / install.ps1
    ↓
downloads hangar binary (pre-compiled, tiny, standalone)
    ↓
hangar install freak@latest
    ↓
downloads freakc binary from GitHub Releases
sets up PATH, shell integration, autocomplete
```

This is exactly the Rustup model. Hangar becomes the universal entry point for the entire ecosystem — not just packages, but the compiler itself.

### Why This Is Better

- One tool manages everything: compiler versions, packages, toolchain updates
- `hangar upgrade freak` updates the compiler
- `hangar install freak@0.9.0` pins a specific version
- `hangar list installed` shows what's on the system
- Future: `hangar toolchain add llvm` installs LLVM support

### Hangar Binary Distribution

Hangar itself needs to be distributable without FREAK installed. Two options:

**Option A — Rewrite Hangar bootstrapper in Python or Go (short term)**
A tiny ~500 line Python or Go script that does only: download binary from GitHub Releases, verify checksum, place in PATH. This becomes the `install.sh` payload. The full Hangar (written in FREAK) runs after freakc is installed.

**Option B — Ship Hangar as a pre-compiled FREAK binary (correct long-term)**
Since you have a self-hosting compiler, CI builds `hangar` for all platforms and uploads to GitHub Releases alongside `freakc`. The install script downloads the `hangar` binary, not `freakc` directly. Hangar then fetches `freakc`.

**Recommendation: Do Option A now, migrate to B after CI is set up.**

### Hangar New Commands

```
hangar install freak           # installs latest freakc
hangar install freak@1.2.0     # pins version
hangar upgrade freak           # upgrades compiler
hangar upgrade                 # upgrades all installed tools
hangar self-update             # updates hangar itself
hangar toolchain list          # shows installed compiler versions
hangar toolchain switch 1.1.0  # switches active compiler version
```

---

## Part 4 — Distribution Infrastructure

### GitHub Releases — Binary Matrix

Every git tag triggers the release workflow. Artifacts:

| Binary | Platform |
|---|---|
| `freakc-linux-x64` | Linux x86_64 |
| `freakc-linux-arm64` | Linux aarch64 |
| `freakc-macos-x64` | macOS Intel |
| `freakc-macos-arm64` | macOS Apple Silicon |
| `freakc-windows-x64.exe` | Windows x86_64 |
| `hangar-linux-x64` | same matrix |
| `hangar-linux-arm64` | |
| `hangar-macos-x64` | |
| `hangar-macos-arm64` | |
| `hangar-windows-x64.exe` | |
| `SHA256SUMS` | checksum file for all above |

### GitHub Actions Workflow

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags: ['v*']

jobs:
  build:
    strategy:
      matrix:
        include:
          - os: ubuntu-latest
            target: x86_64-linux
            binary: freakc-linux-x64
          - os: ubuntu-latest
            target: aarch64-linux
            binary: freakc-linux-arm64
          - os: macos-latest
            target: x86_64-macos
            binary: freakc-macos-x64
          - os: macos-latest
            target: aarch64-macos
            binary: freakc-macos-arm64
          - os: windows-latest
            target: x86_64-windows
            binary: freakc-windows-x64.exe

    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Build freakc binary
        run: python build.py --target ${{ matrix.target }} --out ${{ matrix.binary }}

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: ${{ matrix.binary }}
          path: ${{ matrix.binary }}

  release:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4

      - name: Generate checksums
        run: sha256sum freakc-* hangar-* > SHA256SUMS

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          files: |
            freakc-*
            hangar-*
            SHA256SUMS
          generate_release_notes: true
```

### install.sh (Linux / macOS)

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO="your-username/freak-lang"
INSTALL_DIR="$HOME/.freak/bin"
GITHUB_API="https://api.github.com/repos/$REPO/releases/latest"

echo "🎌 FREAK installer — detecting platform..."

OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

case "$OS-$ARCH" in
  linux-x86_64)   BINARY="hangar-linux-x64" ;;
  linux-aarch64)  BINARY="hangar-linux-arm64" ;;
  darwin-x86_64)  BINARY="hangar-macos-x64" ;;
  darwin-arm64)   BINARY="hangar-macos-arm64" ;;
  *)
    echo "❌ Unsupported platform: $OS-$ARCH"
    echo "   Please build from source: https://github.com/$REPO"
    exit 1
    ;;
esac

echo "📡 Fetching latest release..."
DOWNLOAD_URL=$(curl -fsSL "$GITHUB_API" \
  | grep "browser_download_url" \
  | grep "$BINARY" \
  | cut -d '"' -f 4)

if [ -z "$DOWNLOAD_URL" ]; then
  echo "❌ Could not find binary for $BINARY in latest release."
  exit 1
fi

mkdir -p "$INSTALL_DIR"
echo "⬇️  Downloading $BINARY..."
curl -fsSL "$DOWNLOAD_URL" -o "$INSTALL_DIR/hangar"
chmod +x "$INSTALL_DIR/hangar"

# Add to PATH in shell config
SHELL_CONFIG=""
if [ -f "$HOME/.zshrc" ]; then SHELL_CONFIG="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then SHELL_CONFIG="$HOME/.bashrc"
fi

if [ -n "$SHELL_CONFIG" ]; then
  if ! grep -q 'freak/bin' "$SHELL_CONFIG"; then
    echo 'export PATH="$HOME/.freak/bin:$PATH"' >> "$SHELL_CONFIG"
  fi
fi

export PATH="$INSTALL_DIR:$PATH"

echo "🚀 Installing FREAK compiler via Hangar..."
hangar install freak

echo ""
echo "✅ Sortie complete. FREAK is ready, pilot."
echo "   Run: freak run hello.fk"
echo "   Docs: https://freak-lang.dev"
echo ""
echo "   Restart your terminal or run: source $SHELL_CONFIG"
```

### install.ps1 (Windows)

```powershell
$ErrorActionPreference = "Stop"

$Repo = "your-username/freak-lang"
$InstallDir = "$env:APPDATA\freak\bin"
$ApiUrl = "https://api.github.com/repos/$Repo/releases/latest"
$Binary = "hangar-windows-x64.exe"

Write-Host "🎌 FREAK installer — Windows"

Write-Host "📡 Fetching latest release..."
$Release = Invoke-RestMethod -Uri $ApiUrl
$Asset = $Release.assets | Where-Object { $_.name -eq $Binary }

if (-not $Asset) {
    Write-Error "Could not find $Binary in latest release."
    exit 1
}

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

Write-Host "⬇️  Downloading $Binary..."
Invoke-WebRequest -Uri $Asset.browser_download_url -OutFile "$InstallDir\hangar.exe"

# Add to user PATH
$CurrentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($CurrentPath -notlike "*freak\bin*") {
    [Environment]::SetEnvironmentVariable("PATH", "$InstallDir;$CurrentPath", "User")
}

$env:PATH = "$InstallDir;$env:PATH"

Write-Host "🚀 Installing FREAK compiler via Hangar..."
& "$InstallDir\hangar.exe" install freak

Write-Host ""
Write-Host "✅ Sortie complete. FREAK is ready, pilot."
Write-Host "   Run: freak run hello.fk"
Write-Host "   Restart your terminal for PATH changes to take effect."
```

---

## Part 5 — Package Manager Submissions (Later)

Do these after the GitHub Actions CI is stable and you have at least a few real users.

| Manager | Platform | Priority | Notes |
|---|---|---|---|
| **Homebrew** | macOS + Linux | High | Needs a Formula in homebrew-core or a tap |
| **Scoop** | Windows | High | Just a JSON manifest, very easy |
| **Winget** | Windows | Medium | Microsoft review, takes a week |
| **AUR** | Arch Linux | Low | Community will probably submit it themselves |
| **nixpkgs** | Nix/NixOS | Low | Community driven |

---

## Execution Order

### Phase A — LLVM IR Backend (parallel to distribution)
```
LB1 → LB2 → LB3 → LB4 → LB5 → LB6 (switch default)
↓ (once LB6 is done)
LB7 (JIT) → LB8 (opt levels) → LB9 (cross-compile) → LB10 (debug info)
```

### Phase B — Distribution (can start immediately)
```
1. GitHub Actions release workflow (unblocks everything)
2. install.sh + install.ps1 (simple once GH Actions is done)
3. Hangar bootstrapper v1 (Python script, Option A)
4. Hangar new commands (install/upgrade/toolchain)
5. Migrate to Option B (Hangar binary in CI) once LLVM backend is stable
6. Homebrew tap + Scoop manifest
```

### Phase C — JIT + Future
```
LB7 → REPL prototype → hot-reload in freak-ui → Sortie IDE integration
```
