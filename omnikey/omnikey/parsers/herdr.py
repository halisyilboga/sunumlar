"""Herdr TOML configuration parser and official standard built-in actions."""

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # Python < 3.11 fallback
    except ImportError:
        tomllib = None

from omnikey.models import Keybinding
from omnikey.parsers.base import BaseParser
from omnikey.semantic.tagger import SemanticTagger


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
    "close_pane": "Mevcut paneli kapat / Close active pane",
    "rename_pane": "Paneli yeniden adlandır / Rename pane",
    "zoom": "Paneli tam ekran büyüt/küçült / Toggle pane zoom",
    "resize_mode": "Panel boyutlandırma moduna geç / Enter resize mode",
    "toggle_sidebar": "Kenar çubuğunu aç/kapat / Toggle sidebar",
    "previous_agent": "Önceki AI ajanına odaklan / Focus previous agent",
    "next_agent": "Sonraki AI ajanına odaklan / Focus next agent",
    "focus_agent": "İndeksli AI ajanına odaklan (1-9) / Focus agent 1-9",
    "open_notification_target": "Bildirim hedefine veya ajana git / Jump to active agent notification",
    "last_pane": "Son kullanılan panele hızlı geçiş yap / Jump to last active pane",
    "detach": "Oturumdan ayrıl (detach) / Detach session",
    "reload_config": "Yapılandırma dosyasını yeniden yükle / Reload config",
    "help": "Herdr yardım menüsünü aç / Open Herdr help",
    "settings": "Ayarlar menüsünü aç / Open settings",
    "goto": "Hızlı navigasyon modu (Goto) / Quick navigate mode",
    "edit_scrollback": "Geçmiş ekran çıktısını düzenle / Edit scrollback buffer",
    "cycle_pane_next": "Sonraki panele odaklan / Cycle next pane",
    "cycle_pane_previous": "Önceki panele odaklan / Cycle previous pane",
    "focus_pane_left": "Soldaki panele odaklan / Focus pane left",
    "focus_pane_right": "Sağdaki panele odaklan / Focus pane right",
    "focus_pane_up": "Yukarıdaki panele odaklan / Focus pane up",
    "focus_pane_down": "Aşağıdaki panele odaklan / Focus pane down",
}

# Official Herdr CLI subcommands & built-in bindings catalog
HERDR_BUILTIN_STANDARDS: List[Tuple[str, str, str, str, List[str]]] = [
    # CLI Commands
    ("herdr", "cli", "herdr", "Önceki veya ana Herdr oturumuna bağlan / Launch or attach to persistent session", ["herdr", "attach", "session", "start", "baglan", "oturum", "launch"]),
    ("herdr session attach <name>", "cli", "session attach", "Belirtilen veya önceki isimlendirilmiş oturuma bağlan / Attach named session", ["herdr", "attach", "session", "name", "onceki", "baglan", "oturum"]),
    ("herdr session list", "cli", "session list", "Mevcut aktif Herdr oturumlarını listele / List active Herdr sessions", ["herdr", "session", "list", "ls", "oturumlar", "aktif"]),
    ("herdr session new <name>", "cli", "session new", "Yeni isimlendirilmiş oturum başlat / Create new persistent session", ["herdr", "session", "new", "create", "yeni", "oturum"]),
    ("herdr session kill <name>", "cli", "session kill", "Belirtilen Herdr oturumunu sonlandır / Kill persistent session", ["herdr", "session", "kill", "close", "kapat", "sonlandir"]),
    ("herdr server stop", "cli", "server stop", "Çalışan arka plan Herdr sunucusunu durdur / Stop running Herdr server", ["herdr", "server", "stop", "durdur", "kapat"]),
    ("herdr server reload-config", "cli", "server reload-config", "Canlı sunucu config.toml dosyasını yeniden yükle / Reload config in running server", ["herdr", "server", "reload", "config", "yenile"]),
    ("herdr update", "cli", "update", "Herdr'ı en son sürüme güncelle / Download and install latest Herdr version", ["herdr", "update", "guncelle", "upgrade"]),
    ("herdr status", "cli", "status", "Herdr sunucu ve istemci durumunu göster / Show server and client status", ["herdr", "status", "durum", "server", "client"]),
    ("herdr workspace list", "cli", "workspace list", "Mevcut çalışma alanlarını listele / List workspaces", ["herdr", "workspace", "list", "alan"]),
    ("herdr worktree list", "cli", "worktree list", "Mevcut Git worktree'lerini listele / List Git worktrees", ["herdr", "worktree", "list", "git"]),
    ("herdr --remote <ssh-target>", "cli", "remote attach", "SSH üzerinden uzak sunucudaki Herdr'a bağlan / Attach to remote Herdr via SSH", ["herdr", "remote", "ssh", "uzak", "baglan"]),

    # Built-in Default Keybindings
    ("prefix+?", "prefix", "help", "Herdr yardım ve kısayol rehberini aç / Open Herdr help", ["herdr", "help", "yardim", "rehber", "kisayol"]),
    ("prefix+s", "prefix", "settings", "Herdr ayarlar menüsünü aç / Open settings", ["herdr", "settings", "ayarlar"]),
    ("prefix+d", "prefix", "detach", "Oturumu arka plana gönder ve ayrıl (Detach) / Detach session", ["herdr", "detach", "ayril", "arka-plan", "oturum"]),
    ("prefix+q", "prefix", "detach", "Oturumu arka plana gönder ve ayrıl (Detach) / Detach session", ["herdr", "detach", "ayril", "arka-plan"]),
    ("prefix+w", "prefix", "workspace_picker", "Çalışma alanı seçici penceresi / Workspace picker", ["herdr", "workspace", "picker", "secici", "alan"]),
    ("prefix+g", "prefix", "goto", "Hızlı navigasyon modu (Goto) / Quick navigate mode", ["herdr", "goto", "navigate", "yonlen", "git"]),
    ("prefix+shift+n", "prefix", "new_workspace", "Yeni çalışma alanı oluştur / Create new workspace", ["herdr", "new", "workspace", "yeni", "alan"]),
    ("prefix+shift+g", "prefix", "new_worktree", "Yeni Git worktree oluştur / Create new Git worktree", ["herdr", "new", "worktree", "git", "dal"]),
    ("prefix+shift+o", "prefix", "open_worktree", "Git worktree aç ve seç / Open Git worktree", ["herdr", "open", "worktree", "ac", "git", "sec"]),
    ("prefix+shift+w", "prefix", "rename_workspace", "Çalışma alanını yeniden adlandır / Rename workspace", ["herdr", "rename", "workspace", "adlandir"]),
    ("prefix+shift+d", "prefix", "close_workspace", "Çalışma alanını kapat / Close workspace", ["herdr", "close", "workspace", "kapat", "sil"]),
    ("prefix+c", "prefix", "new_tab", "Yeni sekme aç / Open new tab", ["herdr", "new", "tab", "yeni", "sekme"]),
    ("prefix+shift+x", "prefix", "close_tab", "Sekmeyi kapat / Close tab", ["herdr", "close", "tab", "kapat", "sekme"]),
    ("prefix+e", "prefix", "edit_scrollback", "Geçmiş ekran çıktısını editörde aç / Edit scrollback buffer", ["herdr", "scrollback", "edit", "gecmis", "tampon"]),
    ("prefix+v", "prefix", "split_vertical", "Paneli dikey böl / Split pane vertically", ["herdr", "split", "vertical", "dikey", "bol"]),
    ("prefix+minus", "prefix", "split_horizontal", "Paneli yatay böl / Split pane horizontally", ["herdr", "split", "horizontal", "yatay", "bol"]),
    ("prefix+x", "prefix", "close_pane", "Mevcut paneli kapat / Close active pane", ["herdr", "close", "pane", "kapat", "sil", "panel"]),
    ("prefix+alt+x", "prefix", "remove_worktree", "Git worktree sil veya kapat / Remove Git worktree", ["herdr", "remove", "worktree", "sil", "kapat", "git"]),
    ("prefix+shift+p", "prefix", "rename_pane", "Paneli yeniden adlandır / Rename pane", ["herdr", "rename", "pane", "adlandir", "panel"]),
    ("prefix+z", "prefix", "zoom", "Paneli tam ekran büyüt/küçült / Toggle pane zoom", ["herdr", "zoom", "fullscreen", "tam-ekran", "buyut"]),
    ("prefix+r", "prefix", "resize_mode", "Panel boyutlandırma modu / Enter resize mode", ["herdr", "resize", "boyutlandir", "panel"]),
    ("prefix+b", "prefix", "toggle_sidebar", "Kenar çubuğunu aç/kapat / Toggle sidebar", ["herdr", "sidebar", "toggle", "kenar", "cubuk"]),
    ("prefix+tab", "prefix", "cycle_pane_next", "Sonraki panele odaklan / Cycle next pane", ["herdr", "cycle", "pane", "next", "sonraki", "panel"]),
    ("prefix+shift+tab", "prefix", "cycle_pane_previous", "Önceki panele odaklan / Cycle previous pane", ["herdr", "cycle", "pane", "prev", "onceki", "panel"]),
    ("prefix+l", "prefix", "last_pane", "Son kullanılan panele hızlı geçiş yap / Jump to last active pane", ["herdr", "last", "pane", "son", "panel", "gecis"]),
    ("prefix+p", "prefix", "previous_workspace", "Önceki çalışma alanına geç / Previous workspace", ["herdr", "prev", "workspace", "onceki", "alan"]),
    ("prefix+n", "prefix", "next_workspace", "Sonraki çalışma alanına geç / Next workspace", ["herdr", "next", "workspace", "sonraki", "alan"]),
    ("prefix+1..9", "prefix", "switch_workspace", "İndeksli çalışma alanına geç (1-9) / Switch workspace 1-9", ["herdr", "switch", "workspace", "gecis", "alan"]),
    ("prefix+j", "prefix", "next_agent", "Sonraki AI ajanına odaklan / Focus next agent", ["herdr", "next", "agent", "sonraki", "ajan", "ai", "asistan"]),
    ("prefix+k", "prefix", "previous_agent", "Önceki AI ajanına odaklan / Focus previous agent", ["herdr", "prev", "agent", "onceki", "ajan", "ai", "asistan"]),
    ("prefix+alt+1..9", "prefix", "focus_agent", "İndeksli AI ajanına odaklan (1-9) / Focus agent 1-9", ["herdr", "focus", "agent", "odaklan", "ajan", "ai", "asistan"]),
    ("prefix+o", "prefix", "open_notification_target", "Bildirim hedefine veya ajana git / Jump to active agent notification", ["herdr", "notification", "agent", "bildirim", "ajan", "ai", "odaklan"]),
    ("prefix+[", "prefix", "previous_tab", "Önceki sekmeye geç / Previous tab", ["herdr", "prev", "tab", "onceki", "sekme"]),
    ("prefix+]", "prefix", "next_tab", "Sonraki sekmeye geç / Next tab", ["herdr", "next", "tab", "sonraki", "sekme"]),
]


class HerdrParser(BaseParser):
    """Parses Herdr config.toml keybindings and built-in commands."""

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

        # Fallback simple line parser for [keys] and [[keys.command]]
        result: Dict[str, Any] = {"keys": {"command": []}}
        current_section = None
        current_cmd_entry = None

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            array_table_match = re.match(r"^\[\[([^\]]+)\]\]", line)
            if array_table_match:
                current_section = array_table_match.group(1).strip()
                if current_section == "keys.command":
                    current_cmd_entry = {}
                    result["keys"]["command"].append(current_cmd_entry)
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
            elif current_section == "keys.command" and current_cmd_entry is not None:
                kv_match = re.match(r"^([a-zA-Z0-9_\-]+)\s*=\s*[\"']([^\"']+)[\"']", line)
                if kv_match:
                    k, v = kv_match.groups()
                    current_cmd_entry[k] = v

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
            desc = f"Herdr komut modu ön-eki (Prefix: {prefix_key}) / Herdr command prefix key"
            tags = SemanticTagger.generate_tags("herdr", prefix_key, "prefix", desc, mode="normal")
            tags.extend(["herdr", "prefix", "on-ek", "leader", "trigger"])
            keybindings.append(
                Keybinding(
                    tool="herdr",
                    key_combo=prefix_key,
                    action_raw="prefix",
                    description=desc,
                    source_file=str(file_path.resolve()),
                    mode="normal",
                    tags=sorted(list(set(tags))),
                )
            )

        # 2. Key Actions in [keys]
        for action_name, combo in keys_section.items():
            if action_name in ("prefix", "command") or not isinstance(combo, str) or not combo.strip():
                continue

            full_combo = combo.strip()
            mode = "prefix" if "prefix+" in full_combo.lower() else "global"

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
            tags.extend(["herdr", "multiplexer", action_name])

            keybindings.append(
                Keybinding(
                    tool="herdr",
                    key_combo=full_combo,
                    action_raw=action_name,
                    description=desc,
                    source_file=str(file_path.resolve()),
                    mode=mode,
                    tags=sorted(list(set(tags))),
                )
            )

        # 3. Custom Commands in [[keys.command]]
        commands = keys_section.get("command", [])
        if isinstance(commands, list):
            for cmd_entry in commands:
                if not isinstance(cmd_entry, dict):
                    continue
                k = cmd_entry.get("key")
                c = cmd_entry.get("command")
                t = cmd_entry.get("type", "shell")
                if k and c:
                    desc = f"Herdr özel {t} komutu: {c} / Custom {t} command: {c}"
                    tags = SemanticTagger.generate_tags("herdr", k, c, desc, mode="custom")
                    tags.extend(["herdr", "command", "popup", "custom", c])
                    keybindings.append(
                        Keybinding(
                            tool="herdr",
                            key_combo=k,
                            action_raw=c,
                            description=desc,
                            source_file=str(file_path.resolve()),
                            mode="custom",
                            tags=sorted(list(set(tags))),
                        )
                    )

        return keybindings

    @classmethod
    def get_all_herdr_defaults(cls) -> List[Keybinding]:
        """Return full standard built-in Herdr CLI commands and default keybindings."""
        results: List[Keybinding] = []
        for combo, mode, action, desc, custom_tags in HERDR_BUILTIN_STANDARDS:
            tags = SemanticTagger.generate_tags(
                tool="herdr",
                key_combo=combo,
                action_raw=action,
                description=desc,
                mode=mode,
            )
            tags.extend(["herdr", "multiplexer", "workspace", "terminal", "session"])
            tags.extend(custom_tags)
            clean_tags = sorted(list(set(t.strip().lower() for t in tags if len(t.strip()) >= 2)))

            results.append(
                Keybinding(
                    tool="herdr",
                    key_combo=combo,
                    action_raw=action,
                    description=desc,
                    source_file="builtin://herdr_standards",
                    mode=mode,
                    tags=clean_tags,
                )
            )
        return results
