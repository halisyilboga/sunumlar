## Machine / herdr rules (29 Sep 2026)
Before any work on herdr, agent processes, opencode/kilo servers or machine slowness, read
`~/.codex/memories/herdr-session-recovery.md` (top section) and follow it. Key rules:
- Never SIGSTOP/SIGTSTP agents in herdr panes, and never write idle "freeze" scripts (root cause of the Sep 2026 slowdown).
- opencode runs on ONE shared launchd server at http://127.0.0.1:4096; panes use `opencode attach`. Never start the server from a herdr pane.
- Ask the user before killing or relaunching agent sessions in bulk.
