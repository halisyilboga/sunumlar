"""Conflict detection engine across different tools and modal configurations."""

import re
from typing import Dict, List, Set, Tuple

from omnikey.models import AuditEntry, Conflict, Keybinding


def normalize_key_combo(combo: str) -> str:
    """Normalize key chord representations across tools (Vim, Tmux, Herdr, Zsh)."""
    if not combo:
        return ""
    c = combo.strip().lower()

    # Strip command prefix words like "bind-key", "bind"
    c = re.sub(r"^bind(?:-key)?\s+", "", c)

    # Normalize Vim chords like <C-s>, <M-x>, <A-j>, <leader>

    c = re.sub(r"<c-([a-z0-9])>", r"ctrl+\1", c)
    c = re.sub(r"<m-([a-z0-9])>", r"alt+\1", c)
    c = re.sub(r"<a-([a-z0-9])>", r"alt+\1", c)
    c = re.sub(r"<s-([a-z0-9])>", r"shift+\1", c)
    c = c.replace("<leader>", "leader+")
    c = c.replace("<esc>", "esc")
    c = c.replace("<cr>", "enter")
    c = c.replace("<space>", "space")

    # Normalize Tmux chords like C-s, M-x
    c = re.sub(r"\bc-([a-z0-9])\b", r"ctrl+\1", c)
    c = re.sub(r"\bm-([a-z0-9])\b", r"alt+\1", c)

    # Normalize delimiters
    c = c.replace("-", "+")
    parts = [p.strip() for p in c.split("+") if p.strip()]

    # Sort modifier ordering: ctrl, alt, shift, cmd, leader, prefix, followed by main key
    modifier_order = {"ctrl": 1, "alt": 2, "shift": 3, "cmd": 4, "super": 4, "prefix": 5, "leader": 6}
    mods = sorted([p for p in parts if p in modifier_order], key=lambda x: modifier_order[x])
    keys = [p for p in parts if p not in modifier_order]

    return "+".join(mods + keys)


class ConflictDetector:
    """Detects keybinding collisions across tools and configuration files."""

    @classmethod
    def detect_conflicts(cls, keybindings: List[Keybinding]) -> List[Conflict]:
        """Analyze keybindings and identify potential key chord collisions."""
        grouped: Dict[Tuple[str, str], List[Keybinding]] = {}

        for kb in keybindings:
            norm_key = normalize_key_combo(kb.key_combo)
            if not norm_key:
                continue
            # Group by normalized key combo
            key = (norm_key, kb.mode)
            grouped.setdefault(key, []).append(kb)

        conflicts: List[Conflict] = []

        for (norm_key, mode), kbs in grouped.items():
            if len(kbs) <= 1:
                continue

            tools = sorted(list(set(kb.tool for kb in kbs)))

            # If bindings are across distinct tools or in the same tool with different actions
            if len(tools) > 1:
                severity = "HIGH" if "prefix" not in norm_key and mode == "normal" else "MEDIUM"
                tools_str = ", ".join(tools)
                msg = f"Key combo '{norm_key}' is assigned in multiple tools ({tools_str}) in mode '{mode}'."
                conflicts.append(
                    Conflict(
                        key_combo=norm_key,
                        bindings=kbs,
                        tools=tools,
                        severity=severity,
                        message=msg,
                    )
                )
            elif len(kbs) > 1:
                # Same tool, multiple definitions
                actions = set(kb.action_raw for kb in kbs)
                if len(actions) > 1:
                    msg = f"Multiple distinct actions mapped to '{norm_key}' in tool '{tools[0]}': {', '.join(actions)}"
                    conflicts.append(
                        Conflict(
                            key_combo=norm_key,
                            bindings=kbs,
                            tools=tools,
                            severity="HIGH",
                            message=msg,
                        )
                    )

        return conflicts
