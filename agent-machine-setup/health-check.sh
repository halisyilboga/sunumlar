#!/bin/zsh
# Quick health check for the agent machine setup. Read-only.
# Run any time, e.g. before putting the Mac to sleep.

g() { print -P "  %F{green}OK%f    $*"; }
y() { print -P "  %F{yellow}WARN%f  $*"; }
r() { print -P "  %F{red}FAIL%f  $*"; }

print "Shared servers"
for spec in opencode:4096 kilo:4097; do
  n=${spec%%:*}; p=${spec##*:}
  if curl -fs --max-time 3 -o /dev/null http://127.0.0.1:$p/config; then g "$n server on :$p"
  else r "$n server on :$p not answering (log: ~/.local/state/agent-shared-server/$n.log)"; fi
done

print "Agents"
frozen=$(ps -Ao stat=,comm= | awk '{n=$2; sub(".*/","",n)} n~/^(opencode|claude|kilo|codex|agy)$/ && $1 ~ /^T/' | wc -l | xargs)
standalone=$(ps -Ao command= | grep -E '^opencode( |$)' | grep -vE 'attach|serve|run ' | wc -l | xargs)
if (( frozen )); then r "$frozen frozen (T) agent processes — something sent SIGSTOP"; else g "no frozen agents"; fi
if (( standalone > 3 )); then y "$standalone standalone opencode TUIs (~1 GB each) — use \`opencode\` from a new shell so it attaches"
else g "standalone opencode TUIs: $standalone"; fi
if ps eww -Ao command= 2>/dev/null | grep -q '[F]REEZE_ENABLED=1'; then r "a freeze script is running with FREEZE_ENABLED=1"; fi

print "Memory"
free=$(memory_pressure | awk -F': ' '/free percentage/{gsub("%","",$2); print $2}')
swap=$(sysctl -n vm.swapusage | awk '{v=$6; sub("M","",v); printf "%d", v/1024}')
if (( free >= 25 )); then g "free memory ${free}%%"; else y "free memory ${free}%% (close panes/tabs before sleeping)"; fi
if (( swap <= 5 )); then g "swap used ${swap} GB"; else y "swap used ${swap} GB (above 5 GB: sleep/wake may be slow)"; fi

print "herdr / resurrect"
if herdr status server 2>/dev/null | grep -q 'status: running'; then g "herdr server running"; else y "herdr server not running"; fi
if herdr plugin list 2>/dev/null | grep -q 'ntindle.herdr-resurrect.*enabled'; then g "resurrect plugin enabled"; else r "resurrect plugin not enabled"; fi
if grep -q 'resume_agents_on_restore = false' ~/.config/herdr/config.toml 2>/dev/null; then g "herdr native agent resume off (paced queue owns launches)"
else y "set [session] resume_agents_on_restore = false in ~/.config/herdr/config.toml"; fi
