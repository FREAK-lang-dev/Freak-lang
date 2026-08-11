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
    if [ "$probe_status" -eq 0 ]; then
        "$probe_binary" >/dev/null 2>&1 || probe_status=$?
    fi
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
INSTALL_LOCK=""
INSTALL_LOCK_OWNER=""
TRANSACTION_ACTIVE=0
release_install_lock() {
    if [ -z "$INSTALL_LOCK" ]; then return; fi
    local current_owner=""
    if [ -f "$INSTALL_LOCK/owner" ]; then current_owner=$(cat "$INSTALL_LOCK/owner" 2>/dev/null || true); fi
    if [ -n "$INSTALL_LOCK_OWNER" ] && [ "$current_owner" = "$INSTALL_LOCK_OWNER" ]; then
        rm -f -- "$INSTALL_LOCK/owner"
        rmdir -- "$INSTALL_LOCK" 2>/dev/null || true
    fi
    INSTALL_LOCK=""
    INSTALL_LOCK_OWNER=""
}
cleanup_install() {
    local status=$?
    trap - EXIT INT TERM HUP
    if [ "$TRANSACTION_ACTIVE" -eq 1 ]; then
        if restore_previous_payload; then
            TRANSACTION_ACTIVE=0
            warn "Interrupted payload transaction was rolled back"
        else
            local recovery_backup="$BACKUP_ROOT"
            BACKUP_ROOT=""
            TRANSACTION_ACTIVE=0
            warn "Rollback was incomplete; the previous payload backup is preserved at $recovery_backup"
        fi
    fi
    rm -rf -- "$TMPDIR_INSTALL"
    if [ -n "$APPLY_ROOT" ]; then rm -rf -- "$APPLY_ROOT"; fi
    if [ -n "$BACKUP_ROOT" ]; then rm -rf -- "$BACKUP_ROOT"; fi
    release_install_lock
    exit "$status"
}
trap cleanup_install EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP
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

sha256_file() {
    local path="$1"
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$path" | awk '{print $1}'
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$path" | awk '{print $1}'
    else
        err "SHA-256 verification requires sha256sum or shasum"
    fi
}

verify_downloaded_asset() {
    local archive="$1"
    local asset="$2"
    local checksums="$TMPDIR_INSTALL/SHA256SUMS"
    if [ ! -s "$checksums" ]; then
        fetch_file "$RELEASE_BASE/$LATEST/SHA256SUMS" "$checksums" || err "Could not download SHA256SUMS for $LATEST"
    fi
    local matches match_count expected
    matches=$(awk -v asset="$asset" '$2 == asset || $2 == "./" asset || $2 == "*" asset || $2 == "*./" asset { print $1 }' "$checksums")
    match_count=$(printf '%s\n' "$matches" | awk 'NF { count += 1 } END { print count + 0 }')
    [ "$match_count" -ne 0 ] || err "SHA256SUMS has no exact entry for $asset"
    [ "$match_count" -eq 1 ] || err "SHA256SUMS has duplicate entries for $asset"
    expected=$(printf '%s\n' "$matches" | awk 'NF { print; exit }')
    [ "${#expected}" -eq 64 ] || err "SHA256SUMS has an invalid hash for $asset"
    case "$expected" in
        *[!0-9a-fA-F]*) err "SHA256SUMS has an invalid hash for $asset" ;;
    esac
    local actual
    actual=$(sha256_file "$archive")
    expected=$(printf '%s' "$expected" | tr 'A-F' 'a-f')
    actual=$(printf '%s' "$actual" | tr 'A-F' 'a-f')
    [ "$actual" = "$expected" ] || err "SHA256 mismatch for $asset"
    ok "Verified SHA-256 for $asset"
}

validate_manifest_entry() {
    local source="$1"
    local destination="$2"
    case "$source" in
        /*|[A-Za-z]:*|*\\*|..|../*|*/../*|*/..|./*|*/./*|*/.|*//* )
            err "Unsafe distribution source in manifest: $source" ;;
    esac
    case "$destination" in
        /*|[A-Za-z]:*|*\\*|..|../*|*/../*|*/..|./*|*/./*|*/.|*//* )
            err "Unsafe distribution destination in manifest: $destination" ;;
    esac
    case "$source" in
        freakc/runtime/*|std/*) ;;
        *) err "Unsafe distribution source in manifest: $source" ;;
    esac
    case "$destination" in
        runtime/*|std/*) ;;
        *) err "Unsafe distribution destination in manifest: $destination" ;;
    esac
}

validate_stage() {
    [ -s "$STAGE_BIN/freak" ] || err "Staged compiler is missing"
    [ -s "$STAGE_BIN/hangar" ] || err "Staged Hangar is missing"
    [ -s "$STAGE_MANIFEST" ] || err "Staged distribution manifest is missing"
    local source destination
    while IFS='|' read -r source destination || [ -n "$source$destination" ]; do
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
    verify_downloaded_asset "$STAGE_BIN/freak" "$TARGET"
    fetch_file "$RELEASE_BASE/$LATEST/hangar-${PLATFORM}-${ARCH_TAG}" "$STAGE_BIN/hangar"
    verify_downloaded_asset "$STAGE_BIN/hangar" "hangar-${PLATFORM}-${ARCH_TAG}"
    fetch_file "$RAW_BASE/packaging/distribution-files.manifest" "$STAGE_MANIFEST"
    verify_downloaded_asset "$STAGE_MANIFEST" "raw/packaging/distribution-files.manifest"
    local source destination
    while IFS='|' read -r source destination || [ -n "$source$destination" ]; do
        source=${source%$'\r'}
        destination=${destination%$'\r'}
        if [ -z "$source" ] || [[ "$source" == \#* ]]; then continue; fi
        [ -n "$destination" ] || err "Malformed distribution manifest entry: $source"
        validate_manifest_entry "$source" "$destination"
        mkdir -p "$(dirname "$STAGE_DIR/$destination")"
        fetch_file "$RAW_BASE/$source" "$STAGE_DIR/$destination"
        verify_downloaded_asset "$STAGE_DIR/$destination" "raw/$source"
    done < "$STAGE_MANIFEST"
}

ARCHIVE_PATH="$TMPDIR_INSTALL/freak.tar.gz"
ARCHIVE_NAME="${TARGET}.tar.gz"
ARCHIVE_OK=false
if [ -n "$LOCAL_ARCHIVE" ]; then
    cp "$LOCAL_ARCHIVE" "$ARCHIVE_PATH"
    ARCHIVE_OK=true
elif command -v tar >/dev/null 2>&1; then
    info "Downloading $ARCHIVE_NAME..."
    if fetch_file "$TARBALL_URL" "$ARCHIVE_PATH" 2>/dev/null; then ARCHIVE_OK=true; fi
fi

if [ "$ARCHIVE_OK" = true ] && [ -z "$LOCAL_ARCHIVE" ]; then
    verify_downloaded_asset "$ARCHIVE_PATH" "$ARCHIVE_NAME"
fi

if [ "$ARCHIVE_OK" = true ]; then
    info "Extracting distribution..."
    if ! tar xzf "$ARCHIVE_PATH" -C "$TMPDIR_INSTALL"; then
        [ -z "$LOCAL_ARCHIVE" ] || err "Could not extract local distribution archive"
        stage_fallback_payload
    else
        [ -d "$TMPDIR_INSTALL/freak" ] || err "Distribution archive has no freak/ root"
        cp "$TMPDIR_INSTALL/freak/bin/freak" "$STAGE_BIN/freak"
        [ -s "$TMPDIR_INSTALL/freak/bin/hangar" ] || err "Distribution archive is missing Hangar"
        cp "$TMPDIR_INSTALL/freak/bin/hangar" "$STAGE_BIN/hangar"
        cp -R "$TMPDIR_INSTALL/freak/runtime/." "$STAGE_RUNTIME/"
        cp -R "$TMPDIR_INSTALL/freak/std/." "$STAGE_STD/"
        cp "$TMPDIR_INSTALL/freak/distribution-files.manifest" "$STAGE_MANIFEST"
    fi
else
    [ -z "$LOCAL_ARCHIVE" ] || err "tar is required to extract the local distribution archive"
    stage_fallback_payload
fi

validate_stage

process_start_token() {
    local pid="$1"
    if [ -r "/proc/$pid/stat" ]; then
        sed 's/^[0-9][0-9]* (.*) //' "/proc/$pid/stat" 2>/dev/null | awk '{ print $20 }' || true
        return
    fi
    ps -o lstart= -p "$pid" 2>/dev/null | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' || true
}

lock_owner_is_active() {
    local record="$1"
    local owner_pid owner_start owner_nonce
    IFS='|' read -r owner_pid owner_start owner_nonce <<EOF
$record
EOF
    case "$owner_pid" in ''|*[!0-9]*) return 1 ;; esac
    [ -n "$owner_start" ] || return 1
    [ -n "$owner_nonce" ] || return 1
    local current_start
    current_start=$(process_start_token "$owner_pid")
    if [ -n "$current_start" ]; then
        [ "$owner_start" = "$current_start" ]
        return
    fi
    # If this platform cannot expose a start token, fail closed whenever the
    # process still appears to exist. This never declares EPERM to be stale.
    if kill -0 "$owner_pid" 2>/dev/null || ps -p "$owner_pid" >/dev/null 2>&1; then return 0; fi
    return 1
}

lock_directory_identity() {
    ls -di -- "$1" 2>/dev/null | awk '{ print $1 }'
}

acquire_install_lock() {
    mkdir -p "$INSTALL_DIR"
    local candidate="$INSTALL_DIR/.freak-install.lock"
    local own_start own_nonce attempt owner owner_identity breaker current_owner current_identity missing_identity missing_attempts
    own_start=$(process_start_token "$$")
    if [ -z "$own_start" ]; then own_start="pid-only"; fi
    own_nonce=$(basename "$TMPDIR_INSTALL")
    INSTALL_LOCK_OWNER="$$|$own_start|$own_nonce"
    attempt=0
    missing_identity=""
    missing_attempts=0
    while [ "$attempt" -lt 100 ]; do
        if mkdir -- "$candidate" 2>/dev/null; then
            INSTALL_LOCK="$candidate"
            printf '%s\n' "$INSTALL_LOCK_OWNER" > "$INSTALL_LOCK/owner"
            return
        fi
        if [ -L "$candidate" ] || [ ! -d "$candidate" ]; then
            err "Unsafe FREAK installer lock path: $candidate"
        fi
        owner=""
        if [ -f "$candidate/owner" ]; then owner=$(cat "$candidate/owner" 2>/dev/null || true); fi
        if [ -z "$owner" ]; then
            # A new owner writes this file immediately after mkdir. Give that
            # atomic acquisition window time to finish; an unowned directory
            # that persists is a recoverable crash remnant.
            current_identity=$(lock_directory_identity "$candidate")
            if [ "$current_identity" != "$missing_identity" ]; then
                missing_identity="$current_identity"
                missing_attempts=0
            fi
            missing_attempts=$((missing_attempts + 1))
            attempt=$((attempt + 1))
            if [ "$missing_attempts" -lt 50 ]; then sleep 0.1; continue; fi
        elif lock_owner_is_active "$owner"; then
            err "Another FREAK installer is already updating $INSTALL_DIR"
        else
            missing_identity=""
            missing_attempts=0
        fi
        owner_identity=$(lock_directory_identity "$candidate")
        [ -n "$owner_identity" ] || { attempt=$((attempt + 1)); continue; }
        breaker="$candidate/.freak-stale-takeover"
        if ! mkdir -- "$breaker" 2>/dev/null; then
            attempt=$((attempt + 1))
            sleep 0.1
            continue
        fi
        current_owner=""
        if [ -f "$candidate/owner" ]; then current_owner=$(cat "$candidate/owner" 2>/dev/null || true); fi
        current_identity=$(lock_directory_identity "$candidate")
        if [ "$current_owner" != "$owner" ] || [ "$current_identity" != "$owner_identity" ] || { [ -n "$current_owner" ] && lock_owner_is_active "$current_owner"; }; then
            rmdir -- "$breaker" 2>/dev/null || true
            attempt=$((attempt + 1))
            sleep 0.1
            continue
        fi
        rm -f -- "$candidate/owner"
        rmdir -- "$breaker" 2>/dev/null || err "Could not release stale-lock takeover: $breaker"
        rmdir -- "$candidate" 2>/dev/null || err "Could not recover stale installer lock: $candidate"
        info "Recovered stale installer lock${owner:+ from process ${owner%%|*}}"
        attempt=$((attempt + 1))
    done
    err "Could not acquire FREAK installer lock for $INSTALL_DIR"
}

acquire_install_lock

restore_previous_payload() {
    local live backup
    local restore_failed=0
    if truthy "${FREAK_INSTALL_TEST_FAIL_RESTORE:-0}"; then
        return 1
    fi
    for live in "$BIN_DIR/freak" "$BIN_DIR/hangar" "$INSTALL_DIR/runtime" "$INSTALL_DIR/std" "$INSTALL_DIR/distribution-files.manifest"; do
        backup="$BACKUP_ROOT/${live#"$INSTALL_DIR/"}"
        if [ -e "$backup" ]; then
            if ! rm -rf -- "$live"; then restore_failed=1; continue; fi
            if ! mkdir -p "$(dirname "$live")"; then restore_failed=1; continue; fi
            if ! mv -- "$backup" "$live"; then restore_failed=1; fi
        elif [ -e "$backup.missing" ]; then
            if ! rm -rf -- "$live"; then restore_failed=1; fi
        fi
    done
    if [ -n "$APPLY_ROOT" ]; then rm -rf -- "$APPLY_ROOT" || true; fi
    if [ "$restore_failed" -ne 0 ]; then return 1; fi
    rm -rf -- "$BACKUP_ROOT"
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

reconcile_orphaned_transaction() {
    local candidate orphan_backup="" orphan_count=0
    for candidate in "$INSTALL_DIR"/.freak-backup-*; do
        [ -d "$candidate" ] || continue
        orphan_backup="$candidate"
        orphan_count=$((orphan_count + 1))
    done
    if [ "$orphan_count" -gt 1 ]; then
        err "Multiple interrupted installer backups require manual recovery under $INSTALL_DIR"
    fi
    if [ "$orphan_count" -eq 1 ]; then
        BACKUP_ROOT="$orphan_backup"
        APPLY_ROOT=""
        TRANSACTION_ACTIVE=1
        if restore_previous_payload; then
            TRANSACTION_ACTIVE=0
            BACKUP_ROOT=""
            info "Recovered the previous payload from an interrupted installer transaction"
        else
            local recovery_backup="$BACKUP_ROOT"
            BACKUP_ROOT=""
            TRANSACTION_ACTIVE=0
            err "Could not recover the interrupted payload; backup preserved at $recovery_backup"
        fi
    fi
    for candidate in "$INSTALL_DIR"/.freak-apply-*; do
        [ -d "$candidate" ] || continue
        rm -rf -- "$candidate"
    done
}

reconcile_orphaned_transaction

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

apply_failed=0
TRANSACTION_ACTIVE=1
for live in "$BIN_DIR/freak" "$BIN_DIR/hangar" "$INSTALL_DIR/runtime" "$INSTALL_DIR/std" "$INSTALL_DIR/distribution-files.manifest"; do
    if ! backup_live_path "$live"; then apply_failed=1; break; fi
done
if [ "$apply_failed" -eq 0 ] && truthy "${FREAK_INSTALL_TEST_PAUSE_AFTER_BACKUP:-0}"; then
    if [ -n "${FREAK_INSTALL_TEST_TRANSACTION_READY:-}" ]; then
        printf 'ready\n' > "$FREAK_INSTALL_TEST_TRANSACTION_READY"
    fi
    sleep 30
fi
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
    if restore_previous_payload; then
        TRANSACTION_ACTIVE=0
        BACKUP_ROOT=""
        err "Could not apply the staged distribution; the previous payload was restored"
    fi
    recovery_backup="$BACKUP_ROOT"
    BACKUP_ROOT=""
    TRANSACTION_ACTIVE=0
    err "Could not restore the previous payload; recovery backup preserved at $recovery_backup"
fi
TRANSACTION_ACTIVE=0
rm -rf -- "$APPLY_ROOT" "$BACKUP_ROOT"
APPLY_ROOT=""
BACKUP_ROOT=""
release_install_lock

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
