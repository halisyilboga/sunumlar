# Agent machine setup

Rebuilds the herdr + AI agent configuration from 29–30 Sep 2026 on a fresh Mac.

## Why this exists
The Mac (24 GB) became slow and hard to wake because:
1. Every standalone `opencode`/`kilo` TUI runs its own ~1 GB server. With ~38 panes macOS needed
   58–72 GB, swapped heavily and killed its own unlock/login services.
2. `../vpn_caffeinate_manager.sh` froze (SIGSTOP) all agents after 10 min idle; they never
   recovered and herdr/resurrect opened duplicates. Freezing is now off (`FREEZE_ENABLED=0`).

## What `setup.sh` installs
| What | Where |
|---|---|
| Shared servers: opencode `:4096`, kilo `:4097` (start at login, auto-restart) | `~/Library/LaunchAgents/dev.agent-shared-server.*.plist`, launcher `~/.local/bin/agent-shared-server` |
| `opencode` / `kilo` shell wrappers → `attach --dir "$PWD"` to the shared server | sourced from `~/.zshrc` |
| herdr config (`resume_agents_on_restore = false`, keybindings) | `~/.config/herdr/config.toml` (only if missing, or `--force-config`) |
| Paced resurrect plugin (5 agents at a time, 3 s apart, 10 s between batches) | `~/.local/share/herdr-resurrect-paced`, settings in `~/.config/herdr/plugins/config/ntindle.herdr-resurrect/` |
| herdr integrations for claude, codex, opencode, kilo, antigravity-cli | via `herdr integration install` |
| Rules for every agent session (don't freeze agents, use shared servers, ask before bulk kills) | `~/.codex/AGENTS.md`, `~/.config/opencode/AGENTS.md`, `~/.config/kilo/AGENTS.md`, `~/.claude/CLAUDE.md`, full notes `~/.codex/memories/herdr-session-recovery.md` |

## Usage
```sh
# after installing herdr, opencode, kilo (npm i -g @kilocode/cli), node
./setup.sh --dry-run     # see what would change
./setup.sh               # apply (safe to re-run)
./health-check.sh        # any time, e.g. before sleeping
```
After setup: open a new terminal, run `herdr`, then press **prefix + Ctrl+R** to restore agents.
(herdr doesn't tell the plugin when it has restarted, so the restore must be triggered by hand.)

Backups of anything replaced go to `~/.local/state/agent-machine-setup/backup-<time>/`.

## Updating the bundle
`files/` is a snapshot. After changing the live config, refresh it, e.g.:
```sh
cp ~/.config/herdr/plugins/config/ntindle.herdr-resurrect/settings.json files/resurrect-settings.json
rsync -a --exclude .git ~/.local/share/herdr-resurrect-paced/ files/herdr-resurrect-paced/
```
