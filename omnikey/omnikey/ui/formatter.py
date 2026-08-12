"""Terminal formatting and ANSI color helpers."""

import sys
from typing import List

from omnikey.models import AuditEntry, Conflict, Keybinding

# ANSI Color codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"

TOOL_COLORS = {
    "git": RED,
    "herdr": CYAN,
    "tmux": GREEN,
    "neovim": MAGENTA,
    "nvim": MAGENTA,
    "zsh": YELLOW,
    "linux": BLUE,
    "cli": BLUE,
    "custom": BLUE,
}


def color_tool(tool: str) -> str:
    col = TOOL_COLORS.get(tool.lower(), BLUE)
    return f"{col}{BOLD}[{tool.upper()}]{RESET}"


def format_keybinding_row(kb: Keybinding) -> str:
    """Format a single keybinding for CLI list view."""
    tool_badge = color_tool(kb.tool)
    key_str = f"{BOLD}{YELLOW}{kb.key_combo:<18}{RESET}"
    desc_str = f"{kb.description or kb.action_raw}"
    mode_badge = f"{DIM}({kb.mode}){RESET}" if kb.mode != "normal" else ""
    return f"{tool_badge:<18} {key_str} ➜ {desc_str} {mode_badge}"


def format_keybinding_detail(kb: Keybinding) -> str:
    """Format a detailed preview card of a keybinding."""
    tool_badge = color_tool(kb.tool)
    is_builtin = kb.source_file.startswith("builtin://")
    source_label = f"{CYAN}[Built-in Standard]{RESET}" if is_builtin else f"{GREEN}[User Config File]{RESET}"

    # Clean bilingual breakdown
    desc = kb.description or kb.action_raw
    if " / " in desc:
        tr_part, en_part = desc.split(" / ", 1)
        desc_formatted = f"\n│  🇹🇷 {BOLD}{tr_part.strip()}{RESET}\n│  🇬🇧 {DIM}{en_part.strip()}{RESET}"
    else:
        desc_formatted = f" {BOLD}{desc}{RESET}"

    tags_str = ", ".join(f"#{t}" for t in kb.tags[:12]) if kb.tags else "None"

    lines = [
        f"┌─────────────────────────────────────────────────────────────",
        f"│ {tool_badge}  {BOLD}{YELLOW}{kb.key_combo}{RESET}  {DIM}(mode: {kb.mode}){RESET}",
        f"├─────────────────────────────────────────────────────────────",
        f"│ {BOLD}Action / Command:{RESET} {CYAN}{kb.action_raw}{RESET}",
        f"│ {BOLD}Description:{RESET}{desc_formatted}",
        f"│",
        f"│ {BOLD}Source:{RESET} {source_label}",
        f"│   {DIM}{kb.source_file}{RESET}",
        f"│",
        f"│ {BOLD}Semantic Tags:{RESET}",
        f"│   {DIM}{tags_str}{RESET}",
        f"└─────────────────────────────────────────────────────────────",
    ]
    return "\n".join(lines)


def format_conflicts(conflicts: List[Conflict]) -> str:
    """Format a list of detected conflicts."""
    if not conflicts:
        return f"{GREEN}✓ No keybinding conflicts detected.{RESET}"

    output = [f"{BOLD}{RED}⚠ Detected {len(conflicts)} Keybinding Conflict(s):{RESET}\n"]
    for i, c in enumerate(conflicts, 1):
        sev_color = RED if c.severity == "HIGH" else YELLOW
        output.append(f"{BOLD}{i}. Combo: {YELLOW}{c.key_combo}{RESET} {sev_color}[{c.severity}]{RESET}")
        output.append(f"   {c.message}")
        for kb in c.bindings:
            output.append(f"   - {color_tool(kb.tool)} in {DIM}{kb.source_file}{RESET} ➜ {kb.description or kb.action_raw}")
        output.append("")
    return "\n".join(output)


def format_audit_history(entries: List[AuditEntry]) -> str:
    """Format audit log entries for terminal display."""
    if not entries:
        return f"{DIM}No audit log entries recorded yet.{RESET}"

    output = [f"{BOLD}OmniKey Audit Log (Trackability History):{RESET}\n"]
    for e in entries:
        change_col = GREEN if e.change_type == "ADDED" else (YELLOW if e.change_type == "UPDATED" else RED)
        ts = f"{DIM}[{e.timestamp}]{RESET}"
        type_str = f"{change_col}{BOLD}{e.change_type:<10}{RESET}"
        details = e.details or ""
        output.append(f"{ts} {type_str} {details}")
    return "\n".join(output)
