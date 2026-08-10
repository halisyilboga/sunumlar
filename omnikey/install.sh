#!/usr/bin/env bash
# ==============================================================================
# OmniKey One-Click Installation & Setup Script
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "  🚀 Installing OmniKey Tracker System..."
echo "=================================================="

# 1. Install dependencies
echo "📦 Installing Python dependencies..."
if command -v uv >/dev/null 2>&1; then
    uv pip install -e . --system 2>/dev/null || uv pip install -e . 2>/dev/null || pip3 install -e .
else
    pip3 install -e . --user || pip3 install -e .
fi

# 2. Add ~/.local/bin to PATH if needed
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"
if [ ! -f "$BIN_DIR/omnikey" ]; then
    ln -sf "$SCRIPT_DIR/omnikey/cli.py" "$BIN_DIR/omnikey"
    chmod +x "$BIN_DIR/omnikey"
fi

# 3. Synchronize configuration files
echo "🔍 Synchronizing system keybindings (Herdr, Neovim, Tmux, Zsh)..."
python3 -m omnikey sync

# 4. Integrate into Zsh if ~/.zshrc exists
ZSHRC="$HOME/.zshrc"
ZSH_INTEGRATION_LINE="source \"$SCRIPT_DIR/omnikey/integrations/omnikey.zsh\""

if [ -f "$ZSHRC" ]; then
    if ! grep -q "omnikey.zsh" "$ZSHRC"; then
        echo "" >> "$ZSHRC"
        echo "# OmniKey Keybinding Tracker Integration" >> "$ZSHRC"
        echo "$ZSH_INTEGRATION_LINE" >> "$ZSHRC"
        echo "✨ Added OmniKey widget to $ZSHRC (Ctrl+Space / Alt+K)"
    else
        echo "✓ OmniKey is already integrated in $ZSHRC"
    fi
fi

# 5. Export initial backup state for Git
echo "💾 Exporting initial snapshot for Git backup..."
python3 -m omnikey export --output "$SCRIPT_DIR/omnikey_export.json"

echo "=================================================="
echo "  ✅ OmniKey Installation Completed Successfully!"
echo "=================================================="
echo "Quick Commands:"
echo "  • omnikey search        (Interactive search)"
echo "  • omnikey list          (List all keybindings)"
echo "  • omnikey conflicts     (Detect collisions)"
echo "  • omnikey watch         (Start background watcher)"
echo "  • omnikey export        (Backup for GitHub)"
echo "  • ./restore.sh          (One-click disaster recovery)"
echo "=================================================="
