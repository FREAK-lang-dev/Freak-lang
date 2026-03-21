#!/usr/bin/env bash
# FREAK Language Installer — Linux / macOS
# Usage: curl -fsSL https://raw.githubusercontent.com/OttoApocalypse69/Freak-lang/main/install.sh | bash
set -euo pipefail

REPO="OttoApocalypse69/Freak-lang"
INSTALL_DIR="${FREAK_HOME:-$HOME/.freak}"
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

TARGET="freakc-${PLATFORM}-${ARCH_TAG}"
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

# Download
DOWNLOAD_URL="https://github.com/$REPO/releases/download/$LATEST/$TARGET"
info "Downloading $TARGET..."

mkdir -p "$BIN_DIR"

if command -v curl &>/dev/null; then
    curl -fsSL "$DOWNLOAD_URL" -o "$BIN_DIR/freakc"
else
    wget -q "$DOWNLOAD_URL" -O "$BIN_DIR/freakc"
fi

chmod +x "$BIN_DIR/freakc"

# Download runtime files
RUNTIME_URL="https://raw.githubusercontent.com/$REPO/$LATEST/freakc/runtime"
mkdir -p "$INSTALL_DIR/runtime"
for file in freak_runtime.c freak_runtime.h freak_llvm_runtime.c; do
    if command -v curl &>/dev/null; then
        curl -fsSL "$RUNTIME_URL/$file" -o "$INSTALL_DIR/runtime/$file" 2>/dev/null || true
    else
        wget -q "$RUNTIME_URL/$file" -O "$INSTALL_DIR/runtime/$file" 2>/dev/null || true
    fi
done

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
ok "  Compiler: $BIN_DIR/freakc"
ok "  Runtime:  $INSTALL_DIR/runtime/"
ok ""
ok "Restart your shell or run:"
ok "  export PATH=\"$BIN_DIR:\$PATH\""
ok ""
ok "Then try:"
ok "  freakc build hello.fk -o hello"
ok ""
ok "\"It was always going to end this way.\""
