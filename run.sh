#!/usr/bin/env bash
# run.sh — export CS 631 site content to the Obsidian vault
set -euo pipefail

# launchd runs with a minimal PATH; extend it for Homebrew python3
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/.venv"

# Load user config
ENV_FILE="$SCRIPT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env not found. Run ./install.sh first." >&2
    exit 1
fi
source "$ENV_FILE"

if [ -z "${OUTPUT_DIR:-}" ]; then
    echo "Error: OUTPUT_DIR not set in .env." >&2
    exit 1
fi

cd "$SCRIPT_DIR"

# Create venv if missing
if [ ! -d "$VENV" ]; then
    python3 -m venv "$VENV"
fi

# Install/upgrade dependencies (fast no-op when already satisfied)
"$VENV/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"

# Install Playwright Chromium once
if [ ! -f "$SCRIPT_DIR/.playwright_installed" ]; then
    "$VENV/bin/playwright" install chromium
    touch "$SCRIPT_DIR/.playwright_installed"
fi

"$VENV/bin/python" "$SCRIPT_DIR/update.py" "$OUTPUT_DIR"
