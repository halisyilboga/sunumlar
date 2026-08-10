"""Interactive FZF search integration with live preview."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from omnikey.db import Database
from omnikey.models import Keybinding
from omnikey.ui.formatter import (
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


def run_fzf_search(db: Database, query: Optional[str] = None, tool: Optional[str] = None) -> None:
    """Run interactive fzf search over database keybindings."""
    fzf_bin = find_fzf_binary()
    kbs = db.list_keybindings(tool=tool)

    if not kbs:
        print(f"{YELLOW}No keybindings found in database. Run 'omnikey sync' to scan your files.{RESET}")
        return

    if not fzf_bin:
        # Fallback to plain text search
        filtered = db.list_keybindings(tool=tool, search=query)
        if not filtered:
            print(f"{YELLOW}No matching keybindings for: '{query}'{RESET}")
            return
        print(f"\n{BOLD}OmniKey Search Results ({len(filtered)} items):{RESET}")
        for kb in filtered:
            print(format_keybinding_row(kb))
        return

    # Build FZF formatted list
    # Format: ID \t [TOOL] \t KEY_COMBO \t DESCRIPTION \t TAGS
    lines: List[str] = []
    kb_map = {}
    for kb in kbs:
        kb_id = str(kb.id)
        kb_map[kb_id] = kb
        tool_str = f"[{kb.tool.upper()}]"
        tags_preview = f"({', '.join(kb.tags[:6])})" if kb.tags else ""
        line = f"{kb_id}\t{tool_str:<10}\t{kb.key_combo:<16}\t{kb.description or kb.action_raw}\t{tags_preview}"
        lines.append(line)

    fzf_input = "\n".join(lines)

    # Temporary script or command for fzf preview
    fzf_cmd = [
        fzf_bin,
        "--ansi",
        "--delimiter=\t",
        "--with-nth=2..5",
        "--height=85%",
        "--layout=reverse",
        "--border",
        "--header=OmniKey Keybinding Search (Enter: Copy Combo, Esc: Exit)",
        "--preview-window=right:45%:wrap",
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
                print("\n" + "=" * 55)
                print(format_keybinding_detail(selected_kb))
                print("=" * 55)

                copied = copy_to_clipboard(selected_kb.key_combo)
                if copied:
                    print(f"{GREEN}✓ Copied '{selected_kb.key_combo}' to clipboard!{RESET}\n")
    except Exception as e:
        print(f"{RED}Error running fzf: {e}{RESET}")
