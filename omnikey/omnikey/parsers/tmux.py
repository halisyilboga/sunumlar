"""Parser for Tmux configuration files (~/.tmux.conf)."""

import re
from pathlib import Path
from typing import List, Optional

from omnikey.models import Keybinding
from omnikey.parsers.base import BaseParser
from omnikey.semantic.tagger import SemanticTagger

# Common Tmux action mappings to friendly descriptions
TMUX_ACTION_DESCRIPTIONS = {
    "select-pane -l": "Soldaki pane'e odaklan / Select pane left",
    "select-pane -r": "Sağdaki pane'e odaklan / Select pane right",
    "select-pane -u": "Yukarıdaki pane'e odaklan / Select pane up",
    "select-pane -d": "Aşağıdaki pane'e odaklan / Select pane down",
    "select-window -t :-": "Önceki pencereye geç / Previous window",
    "select-window -t :+": "Sonraki pencereye geç / Next window",
    "send-prefix": "Prefix tuşunu gönder / Send prefix key",
    "split-window -h": "Pencereyi dikey böl (yan yana) / Split horizontally",
    "split-window -v": "Pencereyi yatay böl (alt alta) / Split vertically",
    "new-window": "Yeni pencere aç / Create new window",
    "kill-pane": "Mevcut pane'i kapat / Kill active pane",
    "kill-window": "Mevcut pencereyi kapat / Kill active window",
    "copy-mode": "Kopyalama moduna gir / Enter copy mode",
    "paste-buffer": "Panodan yapıştır / Paste buffer",
    "resize-pane -l": "Pane sola genişlet / Resize pane left",
    "resize-pane -r": "Pane sağa genişlet / Resize pane right",
    "resize-pane -u": "Pane yukarı genişlet / Resize pane up",
    "resize-pane -d": "Pane aşağı genişlet / Resize pane down",
}


class TmuxParser(BaseParser):
    """Parses ~/.tmux.conf keybindings."""

    @property
    def tool_name(self) -> str:
        return "tmux"

    def can_handle(self, file_path: Path) -> bool:
        p = str(file_path).lower()
        return "tmux" in p and (p.endswith(".conf") or p.endswith(".conf.local") or "tmux" in file_path.name)

    def parse(self, file_path: Path) -> List[Keybinding]:
        if not file_path.exists():
            return []

        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except Exception:
            return []

        keybindings: List[Keybinding] = []
        recent_comment = ""

        # Check for prefix definitions
        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                recent_comment = ""
                continue

            if trimmed.startswith("#"):
                recent_comment = trimmed.lstrip("#").strip()
                continue

            # Prefix detection: set -g prefix C-b or set -g prefix2 C-s
            prefix_match = re.match(r"^set\s+(-g\s+)?(prefix\d?)\s+([^\s]+)", trimmed)
            if prefix_match:
                pref_name, pref_key = prefix_match.group(2), prefix_match.group(3)
                desc = f"Tmux {pref_name} ön-ek tuşu ({pref_key})"
                tags = SemanticTagger.generate_tags("tmux", pref_key, pref_name, desc, mode="normal")
                keybindings.append(
                    Keybinding(
                        tool="tmux",
                        key_combo=pref_key,
                        action_raw=f"set {pref_name} {pref_key}",
                        description=desc,
                        source_file=str(file_path.resolve()),
                        mode="normal",
                        tags=tags,
                    )
                )
                recent_comment = ""
                continue

            # Key binding detection: bind-key or bind
            # Examples:
            # bind-key h select-pane -L
            # bind-key -r C-h select-window -t :-
            # bind -n M-Left select-pane -L
            bind_match = re.match(
                r"^bind(?:-key)?\s+(?:-[a-zA-Z0-9]+\s+)*([^\s]+)\s+(.+)$", trimmed
            )
            if bind_match:
                key_raw = bind_match.group(1).strip()
                action_raw = bind_match.group(2).strip()

                # Determine if -n (root/no prefix) was used
                is_root = " -n " in f" {trimmed} "
                mode = "global" if is_root else "prefix"

                # Check if inline comment exists
                inline_comment = ""
                if "#" in action_raw:
                    parts = action_raw.split("#", 1)
                    action_raw = parts[0].strip()
                    inline_comment = parts[1].strip()

                action_key_lookup = action_raw.lower()
                desc = (
                    inline_comment
                    or recent_comment
                    or TMUX_ACTION_DESCRIPTIONS.get(action_key_lookup)
                    or f"Tmux komutu: {action_raw}"
                )

                full_key = key_raw if is_root else f"prefix+{key_raw}"
                tags = SemanticTagger.generate_tags(
                    tool="tmux",
                    key_combo=full_key,
                    action_raw=action_raw,
                    description=desc,
                    mode=mode,
                )

                keybindings.append(
                    Keybinding(
                        tool="tmux",
                        key_combo=full_key,
                        action_raw=action_raw,
                        description=desc,
                        source_file=str(file_path.resolve()),
                        mode=mode,
                        tags=tags,
                    )
                )
                recent_comment = ""

        return keybindings
