"""Parser for Herdr TOML configuration files (~/.config/herdr/config.toml)."""

import re
from pathlib import Path
from typing import Any, Dict, List

from omnikey.models import Keybinding
from omnikey.parsers.base import BaseParser
from omnikey.semantic.tagger import SemanticTagger

# Try to use standard library tomllib if available (Python 3.11+), else fallback to regex
try:
    import tomllib
except ImportError:
    tomllib = None  # type: ignore


# Built-in friendly descriptions for Herdr actions
HERDR_ACTION_DESCRIPTIONS = {
    "open_worktree": "Git worktree aç ve seç / Open Git worktree",
    "remove_worktree": "Git worktree sil veya kapat / Remove Git worktree",
    "new_worktree": "Yeni Git worktree oluştur / Create new Git worktree",
    "new_workspace": "Yeni çalışma alanı (workspace) oluştur / New workspace",
    "rename_workspace": "Çalışma alanını yeniden adlandır / Rename workspace",
    "close_workspace": "Çalışma alanını kapat / Close workspace",
    "previous_workspace": "Önceki çalışma alanına geç / Previous workspace",
    "next_workspace": "Sonraki çalışma alanına geç / Next workspace",
    "switch_workspace": "İndeksli çalışma alanına geç (1-9) / Switch workspace 1-9",
    "workspace_picker": "Çalışma alanı seçici penceresi / Workspace picker",
    "new_tab": "Yeni sekme aç / Open new tab",
    "rename_tab": "Sekmeyi yeniden adlandır / Rename tab",
    "close_tab": "Sekmeyi kapat / Close tab",
    "previous_tab": "Önceki sekmeye geç / Previous tab",
    "next_tab": "Sonraki sekmeye geç / Next tab",
    "switch_tab": "İndeksli sekmeye geç (1-9) / Switch tab 1-9",
    "split_vertical": "Paneli dikey böl / Split pane vertically",
    "split_horizontal": "Paneli yatay böl / Split pane horizontally",
    "close_pane": "Paneli kapat / Close pane",
    "zoom": "Paneli tam ekran büyüt/küçült / Toggle pane zoom",
    "resize_mode": "Panel boyutlandırma moduna geç / Enter resize mode",
    "toggle_sidebar": "Kenar çubuğunu aç/kapat / Toggle sidebar",
    "previous_agent": "Önceki AI ajanına odaklan / Focus previous agent",
    "next_agent": "Sonraki AI ajanına odaklan / Focus next agent",
    "focus_agent": "İndeksli AI ajanına odaklan (1-9) / Focus agent 1-9",
    "detach": "Oturumdan ayrıl (detach) / Detach session",
    "reload_config": "Yapılandırma dosyasını yeniden yükle / Reload config",
    "help": "Herdr yardım menüsünü aç / Open Herdr help",
    "settings": "Ayarlar menüsünü aç / Open settings",
}


class HerdrParser(BaseParser):
    """Parses Herdr config.toml keybindings."""

    @property
    def tool_name(self) -> str:
        return "herdr"

    def can_handle(self, file_path: Path) -> bool:
        p = str(file_path).lower()
        return ("herdr" in p and p.endswith(".toml")) or file_path.name == "config.toml"

    def _parse_toml_dict(self, content: str) -> Dict[str, Any]:
        if tomllib:
            try:
                return tomllib.loads(content)
            except Exception:
                pass

        # Fallback simple line parser for [keys]
        result: Dict[str, Any] = {"keys": {}}
        current_section = None
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            section_match = re.match(r"^\[([^\]]+)\]", line)
            if section_match:
                current_section = section_match.group(1).strip()
                if current_section not in result:
                    result[current_section] = {}
                continue

            if current_section == "keys":
                kv_match = re.match(r"^([a-zA-Z0-9_\-]+)\s*=\s*[\"']([^\"']+)[\"']", line)
                if kv_match:
                    k, v = kv_match.groups()
                    result["keys"][k] = v
        return result

    def parse(self, file_path: Path) -> List[Keybinding]:
        if not file_path.exists():
            return []

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return []

        data = self._parse_toml_dict(content)
        keys_section = data.get("keys", {})
        if not isinstance(keys_section, dict):
            return []

        prefix_key = keys_section.get("prefix", "ctrl+b")
        keybindings: List[Keybinding] = []

        # 1. Base Prefix Key
        if prefix_key:
            desc = f"Herdr komut modu ön-eki (Prefix: {prefix_key})"
            tags = SemanticTagger.generate_tags("herdr", prefix_key, "prefix", desc, mode="normal")
            keybindings.append(
                Keybinding(
                    tool="herdr",
                    key_combo=prefix_key,
                    action_raw="prefix",
                    description=desc,
                    source_file=str(file_path.resolve()),
                    mode="normal",
                    tags=tags,
                )
            )

        # 2. Key Actions in [keys]
        for action_name, combo in keys_section.items():
            if action_name == "prefix" or not isinstance(combo, str) or not combo.strip():
                continue

            # Format combo
            full_combo = combo.strip()
            mode = "prefix" if "prefix+" in full_combo.lower() else "global"

            # Derive human readable description
            desc = HERDR_ACTION_DESCRIPTIONS.get(
                action_name,
                f"Herdr {action_name.replace('_', ' ')} eylemi"
            )

            tags = SemanticTagger.generate_tags(
                tool="herdr",
                key_combo=full_combo,
                action_raw=action_name,
                description=desc,
                mode=mode,
            )

            keybindings.append(
                Keybinding(
                    tool="herdr",
                    key_combo=full_combo,
                    action_raw=action_name,
                    description=desc,
                    source_file=str(file_path.resolve()),
                    mode=mode,
                    tags=tags,
                )
            )

        # 3. Custom Commands in [[keys.command]]
        commands = keys_section.get("command", [])
        if isinstance(commands, list):
            for cmd_entry in commands:
                if isinstance(cmd_entry, dict):
                    cmd_key = cmd_entry.get("key", "")
                    cmd_exec = cmd_entry.get("command", "")
                    cmd_type = cmd_entry.get("type", "popup")
                    if cmd_key and cmd_exec:
                        desc = f"Özel komut çalıştır ({cmd_type}): {cmd_exec}"
                        tags = SemanticTagger.generate_tags(
                            tool="herdr",
                            key_combo=cmd_key,
                            action_raw=cmd_exec,
                            description=desc,
                            mode="prefix" if "prefix+" in cmd_key else "global",
                        )
                        keybindings.append(
                            Keybinding(
                                tool="herdr",
                                key_combo=cmd_key,
                                action_raw=cmd_exec,
                                description=desc,
                                source_file=str(file_path.resolve()),
                                mode="prefix" if "prefix+" in cmd_key else "global",
                                tags=tags,
                            )
                        )

        return keybindings
