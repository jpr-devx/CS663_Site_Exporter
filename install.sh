#!/usr/bin/env bash
# install.sh — configure and register the CS631 Site Exporter launchd agent
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"
PLIST_SRC="$SCRIPT_DIR/CS631-Site-Exporter.plist"
PLIST_DST="$HOME/Library/LaunchAgents/CS631-Site-Exporter.plist"
BINARY="$SCRIPT_DIR/CS631-Site-Exporter"
LOG_PATH="$HOME/Library/Logs/cs631-exporter.log"

# ── Load existing config ───────────────────────────────────────────────────────
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
fi

# ── Prompt for vault root if not set ──────────────────────────────────────────
if [ -z "${VAULT_ROOT:-}" ]; then
    echo ""
    echo "Enter the path to your Obsidian vault directory:"
    read -r -p "> " VAULT_ROOT
    # Expand leading ~ if present
    VAULT_ROOT="${VAULT_ROOT/#\~/$HOME}"
fi

if [ -z "$VAULT_ROOT" ]; then
    echo "Error: vault path cannot be empty." >&2
    exit 1
fi

# ── Derive dependent paths ────────────────────────────────────────────────────
OUTPUT_DIR="$VAULT_ROOT/output"
WATCH_PATH="$VAULT_ROOT/.obsidian/workspace.json"

# ── Save config ───────────────────────────────────────────────────────────────
echo "VAULT_ROOT=$VAULT_ROOT" > "$ENV_FILE"
echo "OUTPUT_DIR=$OUTPUT_DIR" >> "$ENV_FILE"

# ── Compile launcher binary if needed ─────────────────────────────────────────
if [ ! -f "$BINARY" ]; then
    echo "Building launcher binary..."
    clang -o "$BINARY" "$SCRIPT_DIR/launcher.c"
fi

# ── Substitute placeholders into plist ────────────────────────────────────────
sed \
    -e "s|__BINARY_PATH__|$BINARY|g" \
    -e "s|__WATCH_PATH__|$WATCH_PATH|g" \
    -e "s|__LOG_PATH__|$LOG_PATH|g" \
    "$PLIST_SRC" > "$PLIST_DST"

# ── Register launchd agent (unregister first if already loaded) ───────────────
if launchctl list | grep -q "CS631-Site-Exporter"; then
    echo "Updating existing launchd agent..."
    launchctl bootout "gui/$(id -u)" "$PLIST_DST" 2>/dev/null || true
fi

launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"

echo ""
echo "Done. The exporter will run automatically when the vault is opened."
echo "Logs: $LOG_PATH"
