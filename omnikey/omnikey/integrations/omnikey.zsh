#!/usr/bin/env zsh
# OmniKey Zsh Integration & Global Keybinding Widget
# Source this file in ~/.zshrc: source path/to/omnikey.zsh

# Ensure ~/.local/bin is in PATH for direct 'omnikey' CLI calls
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
  export PATH="$HOME/.local/bin:$PATH"
fi

# Interactive search function triggered by widget
omnikey-widget() {
  # Run omnikey search via fzf popup/terminal
  if command -v omnikey >/dev/null 2>&1; then
    omnikey search
  else
    python3 -m omnikey search
  fi
  zle reset-prompt 2>/dev/null || true
}

# Register ZLE widget
if [[ -n "$ZSH_VERSION" ]]; then
  zle -N omnikey-widget
  # Bind to Ctrl+Space (^\x00) or Alt+K
  bindkey '^ ' omnikey-widget 2>/dev/null || true
  bindkey '\ek' omnikey-widget 2>/dev/null || true
fi

# Convenient CLI aliases
alias ok="omnikey"
alias oks="omnikey search"
alias okl="omnikey list"
alias okc="omnikey conflicts"
alias okh="omnikey history"
alias okw="omnikey watch"
alias oke="omnikey export"
alias oksy="omnikey sync"

# Auto-sync & export helper function
omnikey_auto_export() {
  (python3 -m omnikey export >/dev/null 2>&1 &)
}
