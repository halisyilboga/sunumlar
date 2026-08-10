#!/usr/bin/env zsh
# OmniKey Zsh Integration & Global Keybinding Widget
# Source this file in ~/.zshrc: source path/to/omnikey.zsh

# Interactive search function
omnikey-widget() {
  local selected
  # Run omnikey search via fzf
  python3 -m omnikey search
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
alias ok="python3 -m omnikey"
alias oks="python3 -m omnikey search"
alias okl="python3 -m omnikey list"
alias okc="python3 -m omnikey conflicts"
alias okh="python3 -m omnikey history"
alias okw="python3 -m omnikey watch"
