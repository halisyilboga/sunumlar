#!/bin/zsh
# Agent machine setup (herdr + opencode/kilo shared servers + paced resurrect).
# Rebuilds the configuration from 29-30 Sep 2026 on a fresh Mac. Safe to re-run:
# every step checks first and skips what is already in place.
#
#   ./setup.sh              apply
#   ./setup.sh --dry-run    only print what would change
#   ./setup.sh --force-config   also overwrite an existing ~/.config/herdr/config.toml (backed up)
#
# Prerequisites (install first): herdr, opencode, kilo (npm i -g @kilocode/cli), node, curl.

set -u
HERE=${0:A:h}
FILES=$HERE/files
DRY=0; FORCE_CONFIG=0
for a in "$@"; do
  case $a in
    --dry-run) DRY=1 ;;
    --force-config) FORCE_CONFIG=1 ;;
    *) echo "unknown option: $a"; exit 2 ;;
  esac
done

say()  { print -P "%F{cyan}==>%f $*"; }
ok()   { print -P "    %F{green}ok%f   $*"; }
todo() { print -P "    %F{yellow}do%f   $*"; }
warn() { print -P "    %F{red}!!%f   $*"; }
run()  { if (( DRY )); then todo "$*"; else eval "$@"; fi; }

UID_=$(id -u)
BIN=$HOME/.local/bin
STATE=$HOME/.local/state/agent-shared-server
PLUGIN_DIR=$HOME/.local/share/herdr-resurrect-paced
PLUGIN_CFG=$HOME/.config/herdr/plugins/config/ntindle.herdr-resurrect
BACKUP=$HOME/.local/state/agent-machine-setup/backup-$(date +%Y%m%d-%H%M%S)

backup() { # backup <file>
  [[ -e $1 ]] || return 0
  run "mkdir -p '$BACKUP' && cp -p '$1' '$BACKUP/'"
}

# --- 1. prerequisites ------------------------------------------------------
say "Prerequisites"
missing=0
for c in herdr opencode kilo node curl; do
  if command -v $c >/dev/null 2>&1; then ok "$c: $(command -v $c)"; else warn "$c not found"; missing=1; fi
done
(( missing )) && warn "install the missing tools, then re-run. Continuing with what is possible."

# --- 2. shared servers (launchd) --------------------------------------------
say "Shared servers: opencode :4096, kilo :4097"
mkdir -p "$BIN" "$STATE" "$HOME/Library/LaunchAgents" 2>/dev/null
if cmp -s "$FILES/agent-shared-server" "$BIN/agent-shared-server"; then
  ok "launcher up to date"
else
  run "install -m 755 '$FILES/agent-shared-server' '$BIN/agent-shared-server'"; (( DRY )) || ok "launcher installed"
fi

for spec in opencode:4096 kilo:4097; do
  name=${spec%%:*}; port=${spec##*:}
  label=dev.agent-shared-server.$name
  plist=$HOME/Library/LaunchAgents/$label.plist
  want=$(cat <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$label</string>
  <key>ProgramArguments</key>
  <array>
    <string>$BIN/agent-shared-server</string>
    <string>$name</string>
    <string>$port</string>
  </array>
  <key>WorkingDirectory</key><string>$HOME</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>ThrottleInterval</key><integer>15</integer>
  <key>ProcessType</key><string>Interactive</string>
  <key>StandardOutPath</key><string>$STATE/$name.log</string>
  <key>StandardErrorPath</key><string>$STATE/$name.log</string>
</dict>
</plist>
EOF
)
  changed=0
  if [[ -f $plist ]] && [[ "$(cat $plist)" == "$want" ]]; then
    ok "$label plist up to date"
  else
    changed=1
    if (( DRY )); then todo "write $plist"; else print -r -- "$want" > $plist; ok "$label plist written"; fi
  fi
  if launchctl print gui/$UID_/$label >/dev/null 2>&1; then
    if (( changed )); then
      run "launchctl bootout gui/$UID_/$label; launchctl bootstrap gui/$UID_ '$plist'"; (( DRY )) || ok "$label reloaded"
    else
      ok "$label loaded"
    fi
  else
    run "launchctl bootstrap gui/$UID_ '$plist'"; (( DRY )) || ok "$label started"
  fi
done

# --- 3. zsh wrappers: `opencode` / `kilo` attach to the shared servers -------
say "zsh wrappers"
ZRC=$HOME/.zshrc
[[ -L $ZRC ]] && ZRC=${ZRC:A}   # follow dotfiles symlink
WRAP=$HOME/.config/agent-shared-server/agent-wrappers.zsh
if [[ -f $ZRC ]] && grep -q '_agent_attach' $ZRC; then
  ok "wrappers already defined in $ZRC"
else
  run "mkdir -p '${WRAP:h}' && cp '$FILES/agent-wrappers.zsh' '$WRAP'"
  if [[ -f $ZRC ]] && grep -qF "$WRAP" $ZRC; then
    ok "$ZRC already sources $WRAP"
  else
    backup $ZRC
    run "print -r -- '\n# opencode/kilo -> shared servers (agent-machine-setup)\n[[ -f $WRAP ]] && source $WRAP' >> '$ZRC'"
    (( DRY )) || ok "source line added to $ZRC"
  fi
fi

# --- 4. herdr config ----------------------------------------------------------
say "herdr config"
HCFG=$HOME/.config/herdr/config.toml
if [[ ! -f $HCFG ]]; then
  run "mkdir -p '${HCFG:h}' && cp '$FILES/herdr-config.toml' '$HCFG'"; (( DRY )) || ok "config.toml installed"
elif cmp -s "$FILES/herdr-config.toml" "$HCFG"; then
  ok "config.toml identical"
elif (( FORCE_CONFIG )); then
  backup $HCFG; run "cp '$FILES/herdr-config.toml' '$HCFG'"; (( DRY )) || ok "config.toml replaced (backup in $BACKUP)"
else
  warn "config.toml differs; kept yours (use --force-config to replace). Make sure it has [session] resume_agents_on_restore = false"
fi

# --- 5. paced resurrect plugin --------------------------------------------------
say "herdr-resurrect (paced local copy)"
if [[ -d $PLUGIN_DIR ]]; then
  ok "plugin present at $PLUGIN_DIR (not overwritten)"
else
  run "mkdir -p '${PLUGIN_DIR:h}' && cp -R '$FILES/herdr-resurrect-paced' '$PLUGIN_DIR'"; (( DRY )) || ok "plugin copied"
fi
if command -v herdr >/dev/null && herdr plugin list 2>/dev/null | grep -q "local:$PLUGIN_DIR"; then
  ok "plugin linked"
else
  run "herdr plugin link '$PLUGIN_DIR'"
fi
if cmp -s "$FILES/resurrect-settings.json" "$PLUGIN_CFG/settings.json"; then
  ok "plugin settings identical"
else
  backup "$PLUGIN_CFG/settings.json"
  run "mkdir -p '$PLUGIN_CFG' && cp '$FILES/resurrect-settings.json' '$PLUGIN_CFG/settings.json'"; (( DRY )) || ok "plugin settings installed"
fi

# --- 6. herdr agent integrations (status reporting per pane) ----------------------
say "herdr integrations"
if command -v herdr >/dev/null; then
  for i in claude codex opencode kilo antigravity-cli; do
    st=$(herdr integration status 2>/dev/null | grep -E "^$i:" | cut -d' ' -f2)
    if [[ $st == current ]]; then ok "$i current"; else run "herdr integration install $i >/dev/null"; (( DRY )) || ok "$i installed/updated"; fi
  done
fi

# --- 7. rules for every agent session -------------------------------------------
say "Agent rules"
mkdir -p "$HOME/.codex/memories" 2>/dev/null
if cmp -s "$FILES/herdr-session-recovery.md" "$HOME/.codex/memories/herdr-session-recovery.md"; then
  ok "recovery notes identical"
else
  backup "$HOME/.codex/memories/herdr-session-recovery.md"
  run "cp '$FILES/herdr-session-recovery.md' '$HOME/.codex/memories/herdr-session-recovery.md'"
fi
for f in $HOME/.codex/AGENTS.md $HOME/.config/opencode/AGENTS.md $HOME/.config/kilo/AGENTS.md $HOME/.claude/CLAUDE.md; do
  if [[ -f $f ]] && grep -q 'Machine / herdr rules' $f; then
    ok "rules present in $f"
  else
    run "mkdir -p '${f:h}' && { [[ -s '$f' ]] && print >> '$f'; cat '$FILES/agent-rules.md' >> '$f'; }"; (( DRY )) || ok "rules added to $f"
  fi
done

# --- 8. check ---------------------------------------------------------------------
say "Health check"
if (( DRY )); then todo "$HERE/health-check.sh"; else zsh "$HERE/health-check.sh"; fi

cat <<'EOF'

Next:
  1. Open a NEW terminal (so the zsh wrappers load), then run `herdr`.
  2. After herdr opens, restore agents with  prefix + Ctrl+R
     (or: herdr plugin action invoke ntindle.herdr-resurrect.restore).
     They start 5 at a time; opencode/kilo attach to the shared servers.
  3. Never re-enable agent freezing (FREEZE_ENABLED) in vpn_caffeinate_manager.sh.
EOF
