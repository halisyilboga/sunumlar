#!/usr/bin/env bash
# ==============================================================================
# OmniKey Disaster Recovery & Restore Script
# Use this when setting up a fresh machine after reformatting
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "  🔄 Running OmniKey Disaster Recovery..."
echo "=================================================="

# 1. Install dependencies
echo "📦 Installing Python package..."
if command -v uv >/dev/null 2>&1; then
    uv pip install -e . --system 2>/dev/null || uv pip install -e . 2>/dev/null || pip3 install -e .
else
    pip3 install -e . --user || pip3 install -e .
fi

# 2. Import backup snapshot from Git
EXPORT_FILE="$SCRIPT_DIR/omnikey_export.json"
if [ -f "$EXPORT_FILE" ]; then
    echo "📥 Restoring keybindings from $EXPORT_FILE..."
    python3 -m omnikey import "$EXPORT_FILE" --replace
else
    echo "⚠ No backup snapshot found at $EXPORT_FILE. Running fresh sync..."
fi

# 3. Synchronize with any active config files on the fresh machine
echo "🔄 Synchronizing local files..."
python3 -m omnikey sync

# 4. Integrate into Zsh
ZSHRC="$HOME/.zshrc"
ZSH_INTEGRATION_LINE="source \"$SCRIPT_DIR/omnikey/integrations/omnikey.zsh\""
if [ -f "$ZSHRC" ] && ! grep -q "omnikey.zsh" "$ZSHRC"; then
    echo "" >> "$ZSHRC"
    echo "# OmniKey Keybinding Tracker Integration" >> "$ZSHRC"
    echo "$ZSH_INTEGRATION_LINE" >> "$ZSHRC"
fi

echo "=================================================="
echo "  ✅ OmniKey System Successfully Restored!"
echo "=================================================="
python3 -m omnikey doctor
