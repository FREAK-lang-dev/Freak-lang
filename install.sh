#!/usr/bin/env bash
# FREAK Language Installer - Linux / macOS
# Usage: curl -fsSL https://raw.githubusercontent.com/FREAK-lang-dev/Freak-lang/main/install.sh | bash
# With compiler dependencies: curl -fsSL .../install.sh | bash -s -- --with-deps
set -euo pipefail

REPO="FREAK-lang-dev/Freak-lang"
INSTALL_DIR="${FREAK_HOME:-$HOME/.freak}"
INSTALL_DEPS="${FREAK_INSTALL_DEPS:-0}"
SKIP_PATH_UPDATE="${FREAK_SKIP_PATH_UPDATE:-0}"
LOCAL_ARCHIVE="${FREAK_INSTALL_ARCHIVE:-}"
LATEST="${FREAK_RELEASE_TAG:-}"
RELEASE_BASE="${FREAK_RELEASE_BASE:-https://github.com/$REPO/releases/download}"
RAW_BASE_OVERRIDE="${FREAK_RAW_BASE:-}"
EXTRA_PATH_DIR=""
DEPENDENCY_PENDING=false

info()  { printf "\033[1;34m>\033[0m %s\n" "$*"; }
ok()    { printf "\033[1;32m>\033[0m %s\n" "$*"; }
warn()  { printf "\033[1;33m>\033[0m %s\n" "$*" >&2; }
err()   { printf "\033[1;31m>\033[0m %s\n" "$*" >&2; exit 1; }

truthy() {
    case "${1:-}" in
        1|true|TRUE|yes|YES|on|ON) return 0 ;;
        *) return 1 ;;
    esac
}

for arg in "$@"; do
    case "$arg" in
        --with-deps) INSTALL_DEPS=1 ;;
        --without-deps|--skip-deps) INSTALL_DEPS=0 ;;
        --upgrade) ;;
        *) err "Unknown installer option: $arg" ;;
    esac
done

if [ -z "$INSTALL_DIR" ]; then
    err "Refusing an empty FREAK install directory"
fi
mkdir -p -- "$INSTALL_DIR"
INSTALL_DIR=$(cd "$INSTALL_DIR" && pwd -P)
if [ "$INSTALL_DIR" = "/" ]; then
    err "Refusing unsafe FREAK install directory: $INSTALL_DIR"
fi
BIN_DIR="$INSTALL_DIR/bin"

# Detect platform.
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
if [ "$PLATFORM" = "macos" ] && [ "$ARCH_TAG" = "x64" ]; then
    err "Intel macOS is not available in the current release matrix (macOS arm64 only)"
fi
TARGET="freak-${PLATFORM}-${ARCH_TAG}"
info "Detected platform: ${PLATFORM}-${ARCH_TAG}"

have_clang() {
    local candidate=""
    if [ -n "${FREAK_CLANG:-}" ]; then
        candidate="$FREAK_CLANG"
    elif command -v clang >/dev/null 2>&1; then
        candidate=$(command -v clang)
    fi
    [ -n "$candidate" ] || return 1

    local probe_dir probe_source probe_binary probe_status
    probe_dir=$(mktemp -d "${TMPDIR:-/tmp}/freak-clang-probe.XXXXXX") || return 1
    probe_source="$probe_dir/probe.c"
    probe_binary="$probe_dir/probe"
    printf '#include <stdio.h>\nint main(void) { return 0; }\n' > "$probe_source"
    probe_status=0
    "$candidate" -x c "$probe_source" -o "$probe_binary" >/dev/null 2>&1 || probe_status=$?
    if [ "$probe_status" -eq 0 ] && [ ! -s "$probe_binary" ]; then probe_status=1; fi
    rm -rf -- "$probe_dir"
    return "$probe_status"
}

run_privileged() {
    if [ "$(id -u)" -eq 0 ]; then
        "$@"
    elif command -v sudo >/dev/null 2>&1; then
        sudo "$@"
    else
        warn "Administrator privileges are required to install compiler dependencies."
        return 1
    fi
}

dependency_hint() {
    if [ "$PLATFORM" = "macos" ]; then
        warn "Install Apple Command Line Tools with: xcode-select --install"
        warn "Or install Homebrew LLVM with: brew install llvm"
    elif command -v apt-get >/dev/null 2>&1; then
        warn "Install dependencies with: sudo apt-get install clang lld build-essential"
    elif command -v dnf >/dev/null 2>&1; then
        warn "Install dependencies with: sudo dnf install clang lld gcc glibc-devel"
    elif command -v pacman >/dev/null 2>&1; then
        warn "Install dependencies with: sudo pacman -S clang lld base-devel"
    else
        warn "Install Clang and a native C development toolchain, then run freak doctor."
    fi
}

install_compiler_dependencies() {
    if have_clang; then
        ok "Clang is available"
        return 0
    fi
    if ! truthy "$INSTALL_DEPS"; then
        warn "Clang is not available; FREAK will install, but native builds need it."
        dependency_hint
        warn "Re-run this installer with --with-deps to install supported toolchain packages."
        return 0
    fi

    info "Installing Clang, LLD, and native build prerequisites..."
    if [ -n "${FREAK_INSTALL_DEP_COMMAND:-}" ]; then
        if ! bash -c "$FREAK_INSTALL_DEP_COMMAND"; then
            err "The custom dependency installation command failed"
        fi
    elif [ "$PLATFORM" = "macos" ]; then
        if command -v brew >/dev/null 2>&1; then
            brew install llvm
            EXTRA_PATH_DIR="$(brew --prefix llvm)/bin"
            export PATH="$EXTRA_PATH_DIR:$PATH"
        else
            xcode-select --install >/dev/null 2>&1 || true
            DEPENDENCY_PENDING=true
            warn "Complete the Apple Command Line Tools prompt, then run freak doctor."
            return 0
        fi
    elif command -v apt-get >/dev/null 2>&1; then
        run_privileged apt-get update
        run_privileged apt-get install -y clang lld build-essential
    elif command -v dnf >/dev/null 2>&1; then
        run_privileged dnf install -y clang lld gcc glibc-devel
    elif command -v yum >/dev/null 2>&1; then
        run_privileged yum install -y clang lld gcc glibc-devel
    elif command -v pacman >/dev/null 2>&1; then
        run_privileged pacman -S --needed --noconfirm clang lld base-devel
    elif command -v zypper >/dev/null 2>&1; then
        run_privileged zypper --non-interactive install clang lld gcc
    elif command -v apk >/dev/null 2>&1; then
        run_privileged apk add clang lld build-base musl-dev
    else
        dependency_hint
        err "No supported package manager was found for automatic dependency installation"
    fi

    if ! have_clang; then
        dependency_hint
        err "The dependency installer finished, but clang is still unavailable"
    fi
    ok "Compiler dependencies are ready"
}

install_compiler_dependencies

# Resolve the release unless a local archive is supplied for offline install/tests.
if [ -n "$LOCAL_ARCHIVE" ]; then
    [ -f "$LOCAL_ARCHIVE" ] || err "Local distribution archive not found: $LOCAL_ARCHIVE"
    if [ -z "$LATEST" ]; then LATEST="local"; fi
elif [ -z "$LATEST" ]; then
    info "Fetching latest release..."
    if command -v curl >/dev/null 2>&1; then
        LATEST=$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" | grep '"tag_name"' | head -1 | cut -d'"' -f4)
    elif command -v wget >/dev/null 2>&1; then
        LATEST=$(wget -qO- "https://api.github.com/repos/$REPO/releases/latest" | grep '"tag_name"' | head -1 | cut -d'"' -f4)
    else
        err "Neither curl nor wget was found. Install one and retry."
    fi
fi
[ -n "$LATEST" ] || err "Could not determine the latest release. Check https://github.com/$REPO/releases"
info "Release: $LATEST"

RAW_BASE="${RAW_BASE_OVERRIDE:-https://raw.githubusercontent.com/$REPO/$LATEST}"
TARBALL_URL="$RELEASE_BASE/$LATEST/${TARGET}.tar.gz"
TMPDIR_INSTALL=$(mktemp -d)
APPLY_ROOT=""
BACKUP_ROOT=""
cleanup_install() {
    rm -rf -- "$TMPDIR_INSTALL"
    if [ -n "$APPLY_ROOT" ]; then rm -rf -- "$APPLY_ROOT"; fi
    if [ -n "$BACKUP_ROOT" ]; then rm -rf -- "$BACKUP_ROOT"; fi
}
trap cleanup_install EXIT
STAGE_DIR="$TMPDIR_INSTALL/stage"
STAGE_BIN="$STAGE_DIR/bin"
STAGE_RUNTIME="$STAGE_DIR/runtime"
STAGE_STD="$STAGE_DIR/std"
STAGE_MANIFEST="$STAGE_DIR/distribution-files.manifest"
mkdir -p "$STAGE_BIN" "$STAGE_RUNTIME" "$STAGE_STD"

fetch_file() {
    local url="$1"
    local destination="$2"
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "$url" -o "$destination"
    elif command -v wget >/dev/null 2>&1; then
        wget -q "$url" -O "$destination"
    else
        err "Neither curl nor wget was found"
    fi
}

validate_manifest_entry() {
    local source="$1"
    local destination="$2"
    case "$source" in
        freakc/runtime/*|std/*) ;;
        *) err "Unsafe distribution source in manifest: $source" ;;
    esac
    case "$destination" in
        runtime/*|std/*) ;;
        *) err "Unsafe distribution destination in manifest: $destination" ;;
    esac
    case "$source|$destination" in
        *../*|*/..|/*) err "Unsafe traversal in distribution manifest" ;;
    esac
}

validate_stage() {
    [ -s "$STAGE_BIN/freak" ] || err "Staged compiler is missing"
    [ -s "$STAGE_BIN/hangar" ] || err "Staged Hangar is missing"
    [ -s "$STAGE_MANIFEST" ] || err "Staged distribution manifest is missing"
    local source destination
    while IFS='|' read -r source destination; do
        source=${source%$'\r'}
        destination=${destination%$'\r'}
        if [ -z "$source" ] || [[ "$source" == \#* ]]; then continue; fi
        [ -n "$destination" ] || err "Malformed distribution manifest entry: $source"
        validate_manifest_entry "$source" "$destination"
        [ -s "$STAGE_DIR/$destination" ] || err "Staged payload is missing $destination"
    done < "$STAGE_MANIFEST"
}

stage_fallback_payload() {
    info "Distribution archive unavailable; staging standalone compatibility assets..."
    fetch_file "$RELEASE_BASE/$LATEST/$TARGET" "$STAGE_BIN/freak"
    if ! fetch_file "$RELEASE_BASE/$LATEST/hangar-${PLATFORM}-${ARCH_TAG}" "$STAGE_BIN/hangar"; then
        cp "$STAGE_BIN/freak" "$STAGE_BIN/hangar"
    fi
    fetch_file "$RAW_BASE/packaging/distribution-files.manifest" "$STAGE_MANIFEST"
    local source destination
    while IFS='|' read -r source destination; do
        source=${source%$'\r'}
        destination=${destination%$'\r'}
        if [ -z "$source" ] || [[ "$source" == \#* ]]; then continue; fi
        [ -n "$destination" ] || err "Malformed distribution manifest entry: $source"
        validate_manifest_entry "$source" "$destination"
        mkdir -p "$(dirname "$STAGE_DIR/$destination")"
        fetch_file "$RAW_BASE/$source" "$STAGE_DIR/$destination"
    done < "$STAGE_MANIFEST"
}

ARCHIVE_PATH="$TMPDIR_INSTALL/freak.tar.gz"
ARCHIVE_OK=false
if [ -n "$LOCAL_ARCHIVE" ]; then
    cp "$LOCAL_ARCHIVE" "$ARCHIVE_PATH"
    ARCHIVE_OK=true
elif command -v tar >/dev/null 2>&1; then
    info "Downloading ${TARGET}.tar.gz..."
    if fetch_file "$TARBALL_URL" "$ARCHIVE_PATH" 2>/dev/null; then ARCHIVE_OK=true; fi
fi

if [ "$ARCHIVE_OK" = true ]; then
    info "Extracting distribution..."
    if ! tar xzf "$ARCHIVE_PATH" -C "$TMPDIR_INSTALL"; then
        [ -z "$LOCAL_ARCHIVE" ] || err "Could not extract local distribution archive"
        stage_fallback_payload
    else
        [ -d "$TMPDIR_INSTALL/freak" ] || err "Distribution archive has no freak/ root"
        cp "$TMPDIR_INSTALL/freak/bin/freak" "$STAGE_BIN/freak"
        if [ -f "$TMPDIR_INSTALL/freak/bin/hangar" ]; then
            cp "$TMPDIR_INSTALL/freak/bin/hangar" "$STAGE_BIN/hangar"
        else
            cp "$STAGE_BIN/freak" "$STAGE_BIN/hangar"
        fi
        cp -R "$TMPDIR_INSTALL/freak/runtime/." "$STAGE_RUNTIME/"
        cp -R "$TMPDIR_INSTALL/freak/std/." "$STAGE_STD/"
        cp "$TMPDIR_INSTALL/freak/distribution-files.manifest" "$STAGE_MANIFEST"
    fi
else
    [ -z "$LOCAL_ARCHIVE" ] || err "tar is required to extract the local distribution archive"
    stage_fallback_payload
fi

validate_stage

# Prepare replacements on the destination filesystem so every final move is
# an atomic rename. If any apply step fails, restore the exact previous set.
APPLY_ROOT=$(mktemp -d "$INSTALL_DIR/.freak-apply-XXXXXX") || err "Could not create the destination apply directory"
if ! BACKUP_ROOT=$(mktemp -d "$INSTALL_DIR/.freak-backup-XXXXXX"); then
    rm -rf -- "$APPLY_ROOT"
    err "Could not create the destination rollback directory"
fi
mkdir -p "$APPLY_ROOT/bin" "$APPLY_ROOT/runtime" "$APPLY_ROOT/std" "$BACKUP_ROOT/bin"
install -m 755 "$STAGE_BIN/freak" "$APPLY_ROOT/bin/freak"
install -m 755 "$STAGE_BIN/hangar" "$APPLY_ROOT/bin/hangar"
cp -R "$STAGE_RUNTIME/." "$APPLY_ROOT/runtime/"
cp -R "$STAGE_STD/." "$APPLY_ROOT/std/"
cp "$STAGE_MANIFEST" "$APPLY_ROOT/distribution-files.manifest"
mkdir -p "$BIN_DIR"

restore_previous_payload() {
    local live backup
    for live in "$BIN_DIR/freak" "$BIN_DIR/hangar" "$INSTALL_DIR/runtime" "$INSTALL_DIR/std" "$INSTALL_DIR/distribution-files.manifest"; do
        backup="$BACKUP_ROOT/${live#"$INSTALL_DIR/"}"
        if [ -e "$backup" ]; then
            rm -rf -- "$live"
            mkdir -p "$(dirname "$live")"
            mv -- "$backup" "$live" || true
        elif [ -e "$backup.missing" ]; then
            rm -rf -- "$live"
        fi
    done
    rm -rf -- "$APPLY_ROOT" "$BACKUP_ROOT"
}

backup_live_path() {
    local live="$1"
    local backup="$BACKUP_ROOT/${live#"$INSTALL_DIR/"}"
    mkdir -p "$(dirname "$backup")"
    if [ -e "$live" ]; then
        mv -- "$live" "$backup"
    else
        : > "$backup.missing"
    fi
}

apply_failed=0
for live in "$BIN_DIR/freak" "$BIN_DIR/hangar" "$INSTALL_DIR/runtime" "$INSTALL_DIR/std" "$INSTALL_DIR/distribution-files.manifest"; do
    if ! backup_live_path "$live"; then apply_failed=1; break; fi
done
if [ "$apply_failed" -eq 0 ]; then
    mv -- "$APPLY_ROOT/runtime" "$INSTALL_DIR/runtime" || apply_failed=1
fi
if [ "$apply_failed" -eq 0 ] && truthy "${FREAK_INSTALL_TEST_FAIL_APPLY:-0}"; then
    apply_failed=1
fi
if [ "$apply_failed" -eq 0 ]; then mv -- "$APPLY_ROOT/std" "$INSTALL_DIR/std" || apply_failed=1; fi
if [ "$apply_failed" -eq 0 ]; then mv -- "$APPLY_ROOT/distribution-files.manifest" "$INSTALL_DIR/distribution-files.manifest" || apply_failed=1; fi
if [ "$apply_failed" -eq 0 ]; then mv -- "$APPLY_ROOT/bin/freak" "$BIN_DIR/freak" || apply_failed=1; fi
if [ "$apply_failed" -eq 0 ]; then mv -- "$APPLY_ROOT/bin/hangar" "$BIN_DIR/hangar" || apply_failed=1; fi
if [ "$apply_failed" -ne 0 ]; then
    restore_previous_payload
    err "Could not apply the staged distribution; the previous payload was restored"
fi
rm -rf -- "$APPLY_ROOT" "$BACKUP_ROOT"

add_to_path() {
    local rc_file="$1"
    local path_dir="$2"
    local line="export PATH=\"$path_dir:\$PATH\""
    if [ -f "$rc_file" ] && grep -qF "$path_dir" "$rc_file" 2>/dev/null; then return; fi
    printf "\n# FREAK language\n%s\n" "$line" >> "$rc_file"
    info "Added $path_dir to PATH in $rc_file"
}

if ! truthy "$SKIP_PATH_UPDATE"; then
    if [ -n "${ZSH_VERSION:-}" ] || [ -f "$HOME/.zshrc" ]; then
        add_to_path "$HOME/.zshrc" "$BIN_DIR"
        if [ -n "$EXTRA_PATH_DIR" ]; then add_to_path "$HOME/.zshrc" "$EXTRA_PATH_DIR"; fi
    fi
    if [ -f "$HOME/.bashrc" ]; then
        add_to_path "$HOME/.bashrc" "$BIN_DIR"
        if [ -n "$EXTRA_PATH_DIR" ]; then add_to_path "$HOME/.bashrc" "$EXTRA_PATH_DIR"; fi
    fi
    if [ -f "$HOME/.bash_profile" ] && ! [ -f "$HOME/.bashrc" ]; then
        add_to_path "$HOME/.bash_profile" "$BIN_DIR"
        if [ -n "$EXTRA_PATH_DIR" ]; then add_to_path "$HOME/.bash_profile" "$EXTRA_PATH_DIR"; fi
    fi
fi

ok ""
ok "FREAK $LATEST installed successfully!"
ok "  Compiler: $BIN_DIR/freak"
ok "  Hangar:   $BIN_DIR/hangar"
ok "  Runtime:  $INSTALL_DIR/runtime/"
ok "  Std lib:  $INSTALL_DIR/std/"
if [ "$DEPENDENCY_PENDING" = true ]; then
    warn "Compiler dependency installation is waiting for the macOS system prompt."
elif ! have_clang; then
    warn "Clang is still missing. Install it before building FREAK programs."
fi
ok "Restart your shell or run:"
ok "  export PATH=\"$BIN_DIR:\$PATH\""
ok "Then verify the complete toolchain with: freak doctor"
ok "\"It was always going to end this way.\""
