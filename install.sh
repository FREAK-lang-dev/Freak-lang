#!/usr/bin/env bash
# FREAK Language Installer — Linux / macOS
# Usage: curl -fsSL https://raw.githubusercontent.com/FREAK-lang-dev/Freak-lang/main/install.sh | bash
set -euo pipefail

REPO="FREAK-lang-dev/Freak-lang"
INSTALL_DIR="${FREAK_HOME:-$HOME/.freak}"

if [ -z "$INSTALL_DIR" ]; then
    printf "Refusing unsafe FREAK install directory: %s\n" "$INSTALL_DIR" >&2
    exit 1
fi
mkdir -p -- "$INSTALL_DIR"
INSTALL_DIR=$(cd "$INSTALL_DIR" && pwd -P)
if [ "$INSTALL_DIR" = "/" ]; then
    printf "Refusing unsafe FREAK install directory: %s\n" "$INSTALL_DIR" >&2
    exit 1
fi
BIN_DIR="$INSTALL_DIR/bin"

info()  { printf "\033[1;34m>\033[0m %s\n" "$*"; }
ok()    { printf "\033[1;32m>\033[0m %s\n" "$*"; }
err()   { printf "\033[1;31m>\033[0m %s\n" "$*" >&2; exit 1; }

# Detect platform
OS="$(uname -s)"
ARCH="$(uname -m)"

case "$OS" in
    Linux)  PLATFORM="linux" ;;
    Darwin) PLATFORM="macos" ;;
    *)      err "Unsupported OS: $OS" ;;
esac

case "$ARCH" in
    x86_64|amd64)  ARCH_TAG="x64" ;;
    aarch64|arm64) ARCH_TAG="arm64" ;;
    *)             err "Unsupported architecture: $ARCH" ;;
esac

TARGET="freak-${PLATFORM}-${ARCH_TAG}"
info "Detected platform: ${PLATFORM}-${ARCH_TAG}"

# Get latest release tag
info "Fetching latest release..."
if command -v curl &>/dev/null; then
    LATEST=$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" | grep '"tag_name"' | head -1 | cut -d'"' -f4)
elif command -v wget &>/dev/null; then
    LATEST=$(wget -qO- "https://api.github.com/repos/$REPO/releases/latest" | grep '"tag_name"' | head -1 | cut -d'"' -f4)
else
    err "Neither curl nor wget found. Install one and retry."
fi

if [ -z "$LATEST" ]; then
    err "Could not determine latest release. Check https://github.com/$REPO/releases"
fi

info "Latest version: $LATEST"

# Try downloading the full distribution tarball first (includes runtime .o + std)
TARBALL_URL="https://github.com/$REPO/releases/download/$LATEST/${TARGET}.tar.gz"
TARBALL_OK=false

TMPDIR_INSTALL=$(mktemp -d)
trap "rm -rf '$TMPDIR_INSTALL'" EXIT
STAGE_DIR="$TMPDIR_INSTALL/stage"
STAGE_BIN="$STAGE_DIR/bin"
STAGE_RUNTIME="$STAGE_DIR/runtime"
STAGE_STD="$STAGE_DIR/std"
mkdir -p "$STAGE_BIN" "$STAGE_RUNTIME/ui" "$STAGE_STD"

RUNTIME_FILES=(freak_runtime.c freak_runtime.h freak_llvm_runtime.c)
RUNTIME_UI_FILES=(win32_backend.c freak_ui_platform.h)
STD_FILES=(math.fk math3d.fk zip.fk string.fk convert.fk algorithm.fk json.fk http.fk version.fk runtime.fk)

fetch_file() {
    local url="$1"
    local destination="$2"
    if command -v curl &>/dev/null; then
        curl -fsSL "$url" -o "$destination"
    else
        wget -q "$url" -O "$destination"
    fi
}

validate_stage() {
    [ -f "$STAGE_BIN/freak" ] || err "Staged compiler is missing"
    [ -f "$STAGE_BIN/hangar" ] || err "Staged Hangar is missing"
    local file
    for file in "${RUNTIME_FILES[@]}"; do
        [ -f "$STAGE_RUNTIME/$file" ] || err "Staged runtime is missing $file"
    done
    for file in "${RUNTIME_UI_FILES[@]}"; do
        [ -f "$STAGE_RUNTIME/ui/$file" ] || err "Staged runtime is missing ui/$file"
    done
    for file in "${STD_FILES[@]}"; do
        [ -f "$STAGE_STD/$file" ] || err "Staged stdlib is missing $file"
    done
}

install_stage() {
    validate_stage
    mkdir -p "$BIN_DIR"
    install -m 755 "$STAGE_BIN/freak" "$BIN_DIR/freak"
    install -m 755 "$STAGE_BIN/hangar" "$BIN_DIR/hangar"

    # runtime/ and std/ are installer-managed trees. Replacing those exact
    # directories removes files retired by a newer distribution.
    rm -rf -- "$INSTALL_DIR/runtime" "$INSTALL_DIR/std"
    mkdir -p "$INSTALL_DIR/runtime" "$INSTALL_DIR/std"
    cp -R "$STAGE_RUNTIME/." "$INSTALL_DIR/runtime/"
    cp -R "$STAGE_STD/." "$INSTALL_DIR/std/"
}

info "Downloading ${TARGET}.tar.gz..."
if command -v curl &>/dev/null; then
    if curl -fsSL "$TARBALL_URL" -o "$TMPDIR_INSTALL/freak.tar.gz" 2>/dev/null; then
        TARBALL_OK=true
    fi
else
    if wget -q "$TARBALL_URL" -O "$TMPDIR_INSTALL/freak.tar.gz" 2>/dev/null; then
        TARBALL_OK=true
    fi
fi

if [ "$TARBALL_OK" = true ]; then
    info "Extracting distribution..."
    tar xzf "$TMPDIR_INSTALL/freak.tar.gz" -C "$TMPDIR_INSTALL"

    cp "$TMPDIR_INSTALL/freak/bin/freak" "$STAGE_BIN/freak"
    cp "$TMPDIR_INSTALL/freak/bin/hangar" "$STAGE_BIN/hangar" 2>/dev/null || cp "$STAGE_BIN/freak" "$STAGE_BIN/hangar"
    cp -R "$TMPDIR_INSTALL/freak/runtime/." "$STAGE_RUNTIME/"
    cp -R "$TMPDIR_INSTALL/freak/std/." "$STAGE_STD/"
else
    # Fallback: download standalone binary + individual files from source
    info "Tarball not available, falling back to standalone binary..."
    DOWNLOAD_URL="https://github.com/$REPO/releases/download/$LATEST/$TARGET"

    fetch_file "$DOWNLOAD_URL" "$STAGE_BIN/freak"
    cp "$STAGE_BIN/freak" "$STAGE_BIN/hangar"

    # Download runtime files from source tree
    RUNTIME_URL="https://raw.githubusercontent.com/$REPO/$LATEST/freakc/runtime"
    for file in "${RUNTIME_FILES[@]}"; do
        fetch_file "$RUNTIME_URL/$file" "$STAGE_RUNTIME/$file"
    done
    for file in "${RUNTIME_UI_FILES[@]}"; do
        fetch_file "$RUNTIME_URL/ui/$file" "$STAGE_RUNTIME/ui/$file"
    done

    # Download standard library
    STD_URL="https://raw.githubusercontent.com/$REPO/$LATEST/std"
    for file in "${STD_FILES[@]}"; do
        fetch_file "$STD_URL/$file" "$STAGE_STD/$file"
    done
fi

install_stage

# Add to PATH
add_to_path() {
    local rc_file="$1"
    local line="export PATH=\"$BIN_DIR:\$PATH\""
    if [ -f "$rc_file" ] && grep -qF "$BIN_DIR" "$rc_file" 2>/dev/null; then
        return
    fi
    echo "" >> "$rc_file"
    echo "# FREAK language" >> "$rc_file"
    echo "$line" >> "$rc_file"
    info "Added $BIN_DIR to PATH in $rc_file"
}

if [ -n "${ZSH_VERSION:-}" ] || [ -f "$HOME/.zshrc" ]; then
    add_to_path "$HOME/.zshrc"
fi
if [ -f "$HOME/.bashrc" ]; then
    add_to_path "$HOME/.bashrc"
fi
if [ -f "$HOME/.bash_profile" ] && ! [ -f "$HOME/.bashrc" ]; then
    add_to_path "$HOME/.bash_profile"
fi

ok ""
ok "FREAK $LATEST installed successfully!"
ok ""
ok "  Compiler: $BIN_DIR/freak"
ok "  Hangar:   $BIN_DIR/hangar"
ok "  Runtime:  $INSTALL_DIR/runtime/"
ok "  Std lib:  $INSTALL_DIR/std/"
ok ""
ok "Restart your shell or run:"
ok "  export PATH=\"$BIN_DIR:\$PATH\""
ok ""
ok "Then try:"
ok "  freak version"
ok "  freak build hello.fk"
ok "  freak run hello.fk"
ok "  hangar init my-project"
ok ""
ok "\"It was always going to end this way.\""
