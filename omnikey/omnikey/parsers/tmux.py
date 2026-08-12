"""Parser for Tmux configuration files (~/.tmux.conf) and official built-in commands."""

import re
from pathlib import Path
from typing import List, Optional, Tuple

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
    "detach-client": "Oturumdan ayrıl (Detach) / Detach session",
    "choose-tree": "İnteraktif oturum ve pencere ağacı / Interactive session tree",
    "choose-window": "İnteraktif pencere listesi / Choose window",
    "rename-window": "Mevcut pencereyi yeniden adlandır / Rename window",
    "rename-session": "Mevcut oturumu yeniden adlandır / Rename session",
    "resize-pane -z": "Paneli tam ekran yap/küçült / Toggle pane zoom",
    "clock-mode": "Ekranda dijital saati göster / Clock mode",
    "display-panes": "Panel numaralarını göster / Display pane numbers",
    "next-layout": "Sonraki panel düzenine geç / Next layout",
    "break-pane": "Mevcut paneli yeni pencereye taşı / Break pane to new window",
}

# Standard built-in Tmux CLI commands and keybindings
TMUX_BUILTIN_STANDARDS: List[Tuple[str, str, str, str, List[str]]] = [
    # CLI Commands
    ("tmux attach -t <isim>", "cli", "attach", "Belirtilen veya önceki Tmux oturumuna bağlan / Attach to Tmux session", ["tmux", "attach", "session", "baglan", "oturum", "a"]),
    ("tmux a", "cli", "attach last", "En son aktif Tmux oturumuna bağlan / Attach to last active session", ["tmux", "attach", "last", "son", "baglan", "oturum"]),
    ("tmux ls", "cli", "list-sessions", "Çalışan tüm Tmux oturumlarını listele / List running Tmux sessions", ["tmux", "list", "ls", "sessions", "oturumlar"]),
    ("tmux new -s <isim>", "cli", "new-session", "Yeni isimlendirilmiş Tmux oturumu başlat / Create new Tmux session", ["tmux", "new", "create", "session", "yeni", "oturum"]),
    ("tmux kill-session -t <isim>", "cli", "kill-session", "Belirtilen Tmux oturumunu sonlandır / Kill specified session", ["tmux", "kill", "session", "kapat", "sonlandir"]),
    ("tmux kill-server", "cli", "kill-server", "Tüm Tmux sunucusunu ve oturumlarını kapat / Kill entire Tmux server", ["tmux", "kill", "server", "kapat", "durdur"]),
    ("tmux source-file ~/.tmux.conf", "cli", "reload", "Tmux konfigürasyon dosyasını yeniden yükle / Reload Tmux config", ["tmux", "source", "reload", "config", "yenile"]),

    # Standard Default Keybindings
    ("prefix+d", "prefix", "detach-client", "Tmux oturumunu arka plana gönder ve ayrıl (Detach) / Detach session", ["tmux", "detach", "ayril", "arka-plan", "oturum"]),
    ("prefix+s", "prefix", "choose-tree -s", "İnteraktif oturum listesi ve geçiş / Interactive session tree", ["tmux", "session", "tree", "secici", "gecis"]),
    ("prefix+w", "prefix", "choose-tree -w", "İnteraktif pencere listesi ve geçiş / Interactive window list", ["tmux", "window", "list", "pencere", "secici"]),
    ("prefix+c", "prefix", "new-window", "Yeni pencere aç / Create new window", ["tmux", "new", "window", "yeni", "pencere"]),
    ("prefix+,", "prefix", "rename-window", "Mevcut pencereyi yeniden adlandır / Rename current window", ["tmux", "rename", "window", "adlandir", "pencere"]),
    ("prefix+$", "prefix", "rename-session", "Mevcut oturumu yeniden adlandır / Rename current session", ["tmux", "rename", "session", "adlandir", "oturum"]),
    ("prefix+&", "prefix", "kill-window", "Mevcut pencereyi kapat / Kill active window", ["tmux", "kill", "window", "kapat", "sil", "pencere"]),
    ("prefix+x", "prefix", "kill-pane", "Mevcut paneli kapat / Kill active pane", ["tmux", "kill", "pane", "kapat", "sil", "panel"]),
    ("prefix+%", "prefix", "split-window -h", "Pencereyi dikey böl (yan yana) / Split pane vertically", ["tmux", "split", "vertical", "dikey", "bol"]),
    ("prefix+\"", "prefix", "split-window -v", "Pencereyi yatay böl (alt alta) / Split pane horizontally", ["tmux", "split", "horizontal", "yatay", "bol"]),
    ("prefix+z", "prefix", "resize-pane -z", "Paneli tam ekran yap/küçült / Toggle pane zoom", ["tmux", "zoom", "fullscreen", "tam-ekran", "buyut"]),
    ("prefix+[", "prefix", "copy-mode", "Kopyalama ve geçmiş kaydırma moduna gir / Enter copy/scroll mode", ["tmux", "copy", "scrollback", "gecmis", "tampon"]),
    ("prefix+]", "prefix", "paste-buffer", "Tmux panosundaki metni yapıştır / Paste buffer", ["tmux", "paste", "yapistir", "pano"]),
    ("prefix+q", "prefix", "display-panes", "Panel numaralarını göster / Display pane numbers", ["tmux", "display", "panes", "numara"]),
    ("prefix+t", "prefix", "clock-mode", "Ekranda dijital saati göster / Clock mode", ["tmux", "clock", "saat", "zaman"]),
    ("prefix+o", "prefix", "select-pane -t :.+", "Sonraki panele odaklan / Focus next pane", ["tmux", "focus", "next", "pane", "sonraki"]),
    ("prefix+{", "prefix", "swap-pane -U", "Paneli önceki panelle yer değiştir / Swap pane up", ["tmux", "swap", "pane", "yer-degistir"]),
    ("prefix+}", "prefix", "swap-pane -D", "Paneli sonraki panelle yer değiştir / Swap pane down", ["tmux", "swap", "pane", "yer-degistir"]),
    ("prefix+!", "prefix", "break-pane", "Paneli ayrı bir pencereye dönüştür / Break pane into window", ["tmux", "break", "pane", "ayir", "pencere"]),
    ("prefix+Space", "prefix", "next-layout", "Sonraki panel düzenine geç (Layout) / Switch next layout", ["tmux", "layout", "duzen", "space"]),
]


class TmuxParser(BaseParser):
    """Parses ~/.tmux.conf keybindings and standard commands."""

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

        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                recent_comment = ""
                continue

            if trimmed.startswith("#"):
                recent_comment = trimmed.lstrip("#").strip()
                continue

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

            bind_match = re.match(
                r"^bind(?:-key)?\s+(?:-[a-zA-Z0-9]+\s+)*([^\s]+)\s+(.+)$", trimmed
            )
            if bind_match:
                key_raw = bind_match.group(1).strip()
                action_raw = bind_match.group(2).strip()

                is_root = " -n " in f" {trimmed} "
                mode = "global" if is_root else "prefix"

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

    @classmethod
    def get_all_tmux_defaults(cls) -> List[Keybinding]:
        """Return full standard built-in Tmux CLI commands and default keybindings."""
        results: List[Keybinding] = []
        for combo, mode, action, desc, custom_tags in TMUX_BUILTIN_STANDARDS:
            tags = SemanticTagger.generate_tags(
                tool="tmux",
                key_combo=combo,
                action_raw=action,
                description=desc,
                mode=mode,
            )
            tags.extend(["tmux", "multiplexer", "terminal", "session", "window", "pane"])
            tags.extend(custom_tags)
            clean_tags = sorted(list(set(t.strip().lower() for t in tags if len(t.strip()) >= 2)))

            results.append(
                Keybinding(
                    tool="tmux",
                    key_combo=combo,
                    action_raw=action,
                    description=desc,
                    source_file="builtin://tmux_standards",
                    mode=mode,
                    tags=clean_tags,
                )
            )
        return results
