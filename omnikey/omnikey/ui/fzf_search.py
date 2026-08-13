"""Interactive FZF search integration with live preview card, word-boundary scoring, and tool filters."""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from omnikey.db import Database
from omnikey.models import Keybinding
from omnikey.ui.formatter import (
    BLUE,
    BOLD,
    CYAN,
    DIM,
    GREEN,
    MAGENTA,
    RED,
    RESET,
    YELLOW,
    color_tool,
    format_keybinding_detail,
    format_keybinding_row,
)


def find_fzf_binary() -> Optional[str]:
    """Find fzf binary in PATH or common user paths."""
    found = shutil.which("fzf")
    if found:
        return found
    home_fzf = Path.home() / ".fzf" / "bin" / "fzf"
    if home_fzf.exists():
        return str(home_fzf)
    return None


def copy_to_clipboard(text: str) -> bool:
    """Copy given text to clipboard using pbcopy or xclip."""
    try:
        if shutil.which("pbcopy"):
            p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            p.communicate(text.encode("utf-8"))
            return p.returncode == 0
        elif shutil.which("xclip"):
            p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
            p.communicate(text.encode("utf-8"))
            return p.returncode == 0
    except Exception:
        pass
    return False


def run_fzf_search(
    db: Database,
    query: Optional[str] = None,
    tool: Optional[str] = None,
    tools: Optional[List[str]] = None,
) -> None:
    """Run interactive fzf search with live preview card, word boundary matching, and quick filters."""
    fzf_bin = find_fzf_binary()

    # Pre-sort with NLP relevance engine if query provided, else list all
    if query and query.strip() and not query.strip().startswith("@") and not query.strip().startswith("'"):
        kbs = db.list_keybindings(tool=tool, tools=tools, search=query)
        all_kbs = db.list_keybindings(tool=tool, tools=tools)
        seen_ids = {k.id for k in kbs}
        for k in all_kbs:
            if k.id not in seen_ids:
                kbs.append(k)
    else:
        kbs = db.list_keybindings(tool=tool, tools=tools)

    if not kbs:
        print(f"{YELLOW}No keybindings found in database. Run 'omnikey sync' to scan your files.{RESET}")
        return

    if not fzf_bin:
        # Fallback to plain text search
        filtered = db.list_keybindings(tool=tool, tools=tools, search=query)
        if not filtered:
            print(f"{YELLOW}No matching keybindings or commands for: '{query}'{RESET}")
            return
        print(f"\n{BOLD}OmniKey Search Results ({len(filtered)} items):{RESET}")
        for kb in filtered:
            print(format_keybinding_row(kb))
        return

    # Build FZF formatted list
    # Format: 1: ID \t 2: [TOOL] @tool \t 3: KEY_COMBO \t 4: CLEAN_DESC \t 5: TAGS
    lines: List[str] = []
    kb_map = {}

    for kb in kbs:
        kb_id = str(kb.id)
        kb_map[kb_id] = kb
        tool_name = kb.tool.lower()

        # Tool badge with color and @tag alias for instant filtering
        badge_colored = color_tool(tool_name)
        tool_tag = f"@{tool_name}"
        if tool_name in ("neovim", "nvim"):
            tool_tag += " @nvim"
        elif tool_name in ("linux", "cli"):
            tool_tag += " @cli"
        elif tool_name in ("git", "vcs"):
            tool_tag += " @vcs"

        # Clean bilingual breakdown
        desc = kb.description or kb.action_raw
        if " / " in desc:
            tr_part, en_part = desc.split(" / ", 1)
            clean_desc = f"{tr_part.strip()} {DIM}│{RESET} {en_part.strip()}"
        else:
            clean_desc = desc

        tags_str = " ".join(f"#{t}" for t in kb.tags) if kb.tags else ""
        line = f"{kb_id}\t{badge_colored:<18} {DIM}{tool_tag:<10}{RESET}\t{BOLD}{YELLOW}{kb.key_combo:<24}{RESET}\t{clean_desc}\t{DIM}{tags_str}{RESET}"
        lines.append(line)

    fzf_input = "\n".join(lines)

    header_text = (
        "OmniKey Universal Cheat & Shortcut Hub\n"
        "⚡ Filters: Ctrl+A (All) | Ctrl+G (Git) | Ctrl+H (Herdr) | Ctrl+N (Nvim) | Ctrl+L (Linux) | Ctrl+T (Tmux) | Ctrl+Z (Zsh)\n"
        "🏷️  Exact Tags: '@git | '@herdr | '@nvim | '@linux | '@tmux | '@zsh (Press Ctrl+G/H/N/L/T/Z for 1-click filter)\n"
        "⏎ Action: Enter to copy key/command to clipboard | Esc: Exit"
    )

    # Preview command using omnikey show
    py_exec = sys.executable or "python3"
    preview_cmd = f"{py_exec} -m omnikey show {{1}}"

    fzf_cmd = [
        fzf_bin,
        "--ansi",
        "--delimiter=\t",
        "--with-nth=2..",  # Present from tool badge onwards, preserving all columns
        "--tiebreak=begin,length,chunk",  # Rank exact word starts highest
        "--height=85%",
        "--layout=reverse",
        "--border=rounded",
        f"--header={header_text}",
        "--prompt=🔍 Search > ",
        "--pointer=▶",
        "--marker=✓",
        "--preview-window=right:48%:wrap:border-left",
        f"--preview={preview_cmd}",
        # Interactive Tool switching keybindings (Exact matching with ')
        "--bind=ctrl-a:change-query()",
        "--bind=ctrl-g:change-query('@git )",
        "--bind=ctrl-h:change-query('@herdr )",
        "--bind=ctrl-n:change-query('@nvim )",
        "--bind=ctrl-l:change-query('@linux )",
        "--bind=ctrl-t:change-query('@tmux )",
        "--bind=ctrl-z:change-query('@zsh )",
    ]

    if query:
        fzf_cmd.extend(["--query", query])

    try:
        proc = subprocess.Popen(
            fzf_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,
            text=True,
        )
        selected_line, _ = proc.communicate(input=fzf_input)

        if proc.returncode == 0 and selected_line.strip():
            parts = selected_line.split("\t")
            selected_id = parts[0].strip()
            selected_kb = kb_map.get(selected_id) or db.get_keybinding(int(selected_id))

            if selected_kb:
                print("\n" + "=" * 62)
                print(format_keybinding_detail(selected_kb))
                print("=" * 62)

                copied = copy_to_clipboard(selected_kb.key_combo)
                if copied:
                    label = "command" if selected_kb.tool == "linux" else "keybinding"
                    print(f"{GREEN}✓ Copied {label} '{selected_kb.key_combo}' to clipboard!{RESET}\n")
    except Exception as e:
        print(f"{RED}Error running fzf: {e}{RESET}")
