# Interactive opencode/kilo attach to their shared launchd servers (dev.agent-shared-server.*)
# instead of starting a private ~1 GB server per pane. Subcommands and flags attach doesn't
# know fall through to the real binary. --dir "$PWD" is required: a bare attach runs in the
# server's cwd ($HOME), not the current project. Bypass: `command opencode ...`, or
# OPENCODE_STANDALONE=1 / KILO_STANDALONE=1.
_agent_attach() {
  local bin=$1 port=$2 standalone=$3; shift 3
  local a has_dir= skip=
  if [[ -z $standalone ]]; then
    for a in "$@"; do
      if [[ -n $skip ]]; then skip=; continue; fi
      case $a in
        -s|--session) skip=1 ;;
        --dir) skip=1; has_dir=1 ;;
        --dir=*) has_dir=1 ;;
        --session=*|-c|--continue|--fork|--mini) ;;
        *) command $bin "$@"; return ;;
      esac
    done
    if curl -fs --max-time 1 -o /dev/null http://127.0.0.1:$port/config; then
      if [[ -n $has_dir ]]; then
        command $bin attach http://127.0.0.1:$port "$@"
      else
        command $bin attach http://127.0.0.1:$port --dir "$PWD" "$@"
      fi
      return
    fi
  fi
  command $bin "$@"
}
opencode() { _agent_attach opencode 4096 "$OPENCODE_STANDALONE" "$@"; }
kilo() { _agent_attach kilo 4097 "$KILO_STANDALONE" "$@"; }
