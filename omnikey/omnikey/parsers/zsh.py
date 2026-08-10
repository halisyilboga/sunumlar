"""Parser for Zsh aliases and keybindings (~/.zshrc, ~/.aliases)."""

import re
from pathlib import Path
from typing import List

from omnikey.models import Keybinding
from omnikey.parsers.base import BaseParser
from omnikey.semantic.tagger import SemanticTagger


class ZshParser(BaseParser):
    """Parses aliases and bindkey commands from Zsh configuration files."""

    @property
    def tool_name(self) -> str:
        return "zsh"

    def can_handle(self, file_path: Path) -> bool:
        p = str(file_path).lower()
        return "zsh" in p or "alias" in p or file_path.name in (".zshrc", ".zshrc.local", ".aliases", ".aliases.local")

    def parse(self, file_path: Path) -> List[Keybinding]:
        if not file_path.exists() or not file_path.is_file():
            return []

        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except Exception:
            return []

        keybindings: List[Keybinding] = []
        recent_comment = ""

        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                recent_comment = ""
                continue

            if trimmed.startswith("#"):
                recent_comment = trimmed.lstrip("#").strip()
                continue

            # 1. Alias match: alias name="cmd" or alias -- -="cd -"
            alias_match = re.match(
                r"^alias\s+(?:--\s+)?([a-zA-Z0-9_\-\.]+)\s*=\s*[\"'](.*)[\"']\s*(?:#\s*(.*))?$",
                trimmed,
            )
            if alias_match:
                alias_name = alias_match.group(1).strip()
                cmd_exec = alias_match.group(2).strip()
                inline_desc = alias_match.group(3) or ""

                desc = inline_desc or recent_comment or f"Zsh takma adı: {alias_name} -> {cmd_exec}"
                tags = SemanticTagger.generate_tags(
                    tool="zsh",
                    key_combo=alias_name,
                    action_raw=cmd_exec,
                    description=desc,
                    mode="alias",
                )

                keybindings.append(
                    Keybinding(
                        tool="zsh",
                        key_combo=alias_name,
                        action_raw=cmd_exec,
                        description=desc,
                        source_file=str(file_path.resolve()),
                        mode="alias",
                        tags=tags,
                    )
                )
                recent_comment = ""
                continue

            # 2. Bindkey match: bindkey '^R' history-incremental-search-backward
            bind_match = re.match(
                r"^bindkey\s+[\"']?([^\"'\s]+)[\"']?\s+([^\s#]+)(?:\s*#\s*(.*))?$",
                trimmed,
            )
            if bind_match:
                key_raw = bind_match.group(1).strip()
                widget = bind_match.group(2).strip()
                inline_desc = bind_match.group(3) or ""

                # Normalize ^R -> ctrl+r
                key_combo = key_raw
                if key_raw.startswith("^") and len(key_raw) == 2:
                    key_combo = f"ctrl+{key_raw[1].lower()}"

                desc = inline_desc or recent_comment or f"Zsh widget çağrısı: {widget}"
                tags = SemanticTagger.generate_tags(
                    tool="zsh",
                    key_combo=key_combo,
                    action_raw=widget,
                    description=desc,
                    mode="global",
                )

                keybindings.append(
                    Keybinding(
                        tool="zsh",
                        key_combo=key_combo,
                        action_raw=widget,
                        description=desc,
                        source_file=str(file_path.resolve()),
                        mode="global",
                        tags=tags,
                    )
                )
                recent_comment = ""

        return keybindings
