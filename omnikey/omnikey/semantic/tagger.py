"""Semantic tagger generating bilingual (TR/EN) search keywords from keybindings."""

import re
from typing import Dict, List, Set

# Bilingual domain synonym dictionaries
SYNONYM_MAP: Dict[str, List[str]] = {
    # Delete / Remove / Close
    "delete": ["sil", "silme", "kaldir", "kapat", "remove", "kill", "close", "destroy"],
    "remove": ["sil", "silme", "kaldir", "kapat", "delete", "kill", "close"],
    "kill": ["oldur", "kapat", "sonlandir", "terminate", "kill", "sil"],
    "close": ["kapat", "kapan", "exit", "quit", "cikis", "close"],
    "quit": ["cikis", "kapat", "exit", "quit"],
    "detach": ["ayril", "arka-plan", "detach", "disconnect"],

    # Create / New / Open
    "new": ["yeni", "olustur", "ac", "create", "open", "add"],
    "create": ["olustur", "yeni", "create", "new", "make"],
    "open": ["ac", "acma", "open", "start", "launch"],
    "add": ["ekle", "ekleme", "add", "insert"],
    "spawn": ["baslat", "olustur", "spawn", "fork"],

    # Navigation / Movement / Switch
    "next": ["sonraki", "ileri", "next", "forward"],
    "previous": ["onceki", "geri", "prev", "previous", "backward"],
    "prev": ["onceki", "geri", "prev", "previous"],
    "switch": ["gecis", "degistir", "switch", "toggle", "sec"],
    "toggle": ["ac-kapa", "degistir", "toggle", "switch"],
    "focus": ["odaklan", "sec", "focus", "select"],
    "select": ["sec", "secim", "select", "choose", "focus"],
    "goto": ["git", "yonlen", "goto", "jump"],
    "cycle": ["döngü", "gezin", "cycle", "rotate"],

    # Workspaces & Tabs & Panes
    "workspace": ["calisma-alani", "alan", "workspace", "space", "proje"],
    "workspaces": ["calisma-alanlari", "alanlar", "spaces", "workspaces", "workspace"],
    "space": ["calisma-alani", "alan", "workspace", "space"],
    "spaces": ["calisma-alanlari", "alanlar", "spaces", "workspaces", "workspace"],
    "worktree": ["worktree", "git-dal", "calisma-agaci", "dal", "branch", "repo"],
    "worktrees": ["worktree", "git-dal", "calisma-agaci", "dal", "branch", "repo"],
    "tab": ["sekme", "tab", "pencere", "sayfa"],
    "tabs": ["sekme", "tab", "sekmeler", "pencere"],
    "pane": ["panel", "bolme", "pane", "bolum", "cerceve"],
    "panes": ["paneller", "bolmeler", "pane", "panel"],
    "window": ["pencere", "window", "ekran"],
    "windows": ["pencereler", "window", "pencere"],
    "split": ["bol", "bolme", "split", "divide", "ayir"],
    "vertical": ["dikey", "vertical", "vsplit", "dik"],
    "horizontal": ["yatay", "horizontal", "hsplit", "yan"],
    "resize": ["boyutlandir", "yeniden-boyutlandir", "resize", "scale"],
    "zoom": ["buyut", "odak", "zoom", "fullscreen", "tam-ekran"],

    # Agents & AI
    "agent": ["ajan", "ai", "yapay-zeka", "bot", "agent", "asistan"],
    "agents": ["ajanlar", "ai", "yapay-zeka", "bot", "agent", "asistan"],
    "ai": ["yapay-zeka", "ai", "agent", "llm"],

    # Search & Files & Buffers
    "search": ["ara", "arama", "bul", "search", "find", "grep"],
    "find": ["bul", "arama", "find", "search", "lookup"],
    "grep": ["metin-ara", "ara", "grep", "search"],
    "file": ["dosya", "file", "belge"],
    "files": ["dosya", "dosyalar", "file", "belge"],
    "buffer": ["tampon", "buffer", "dosya", "sekme"],
    "buffers": ["tamponlar", "buffer", "dosya", "sekme"],
    "save": ["kaydet", "yaz", "save", "write"],
    "edit": ["duzenle", "yaz", "edit", "modify"],

    # Terminal & System
    "reload": ["yenile", "tekrar-yukle", "reload", "refresh"],
    "restart": ["yeniden-baslat", "restart", "reboot"],
    "history": ["gecmis", "scrollback", "history", "kayit"],
    "scrollback": ["kaydirma-gecmisi", "scrollback", "history"],
    "prefix": ["prefix", "on-ek", "lider", "leader"],
    "leader": ["leader", "lider-tus", "prefix"],
    "help": ["yardim", "destek", "help", "kilavuz", "rehber"],
    "sidebar": ["kenar-cubugu", "yan-panel", "sidebar", "panel"],
    "command": ["komut", "command", "cmd", "terminal"],
    "alias": ["kisayol", "alias", "takma-ad"],
}


class SemanticTagger:
    """Extracts multilingual semantic tags from keybinding definitions."""

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        if not text:
            return []
        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", text)
        s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
        tokens = re.findall(r"[a-zA-Z0-9_\-]+", s2.lower())
        results: List[str] = []
        for t in tokens:
            for part in re.split(r"[_\-\s:\+]+", t):
                part = part.strip()
                if len(part) >= 2:
                    results.append(part)
        return results

    @classmethod
    def generate_tags(
        cls,
        tool: str,
        key_combo: str,
        action_raw: str,
        description: str,
        mode: str = "normal",
    ) -> List[str]:
        """Generate comprehensive search tags for a keybinding."""
        tags: Set[str] = set()

        # Tool tag
        tool_clean = tool.lower().strip()
        tags.add(tool_clean)
        if tool_clean in ("nvim", "neovim"):
            tags.update(["nvim", "neovim", "vim"])
        elif tool_clean == "herdr":
            tags.update(["herdr", "multiplexer", "terminal-manager"])
        elif tool_clean == "tmux":
            tags.update(["tmux", "multiplexer"])
        elif tool_clean == "zsh":
            tags.update(["zsh", "shell", "terminal", "alias"])

        # Mode tags
        if mode and mode != "normal":
            tags.add(mode.lower())

        # Collect raw words
        corpus = f"{action_raw} {description} {key_combo}"
        tokens = cls._tokenize(corpus)

        for token in tokens:
            tags.add(token)
            if token in SYNONYM_MAP:
                tags.update(SYNONYM_MAP[token])
            # Check singular if plural
            if token.endswith("s") and token[:-1] in SYNONYM_MAP:
                tags.update(SYNONYM_MAP[token[:-1]])

        # Key chord breakdown tags
        combo_lower = key_combo.lower()
        if "prefix" in combo_lower:
            tags.add("prefix")
        if "ctrl" in combo_lower or "<c-" in combo_lower or "c-" in combo_lower:
            tags.add("ctrl")
        if "alt" in combo_lower or "<a-" in combo_lower or "m-" in combo_lower:
            tags.add("alt")
        if "shift" in combo_lower:
            tags.add("shift")
        if "leader" in combo_lower:
            tags.add("leader")

        clean_results = sorted(list(set(t.strip().lower() for t in tags if len(t.strip()) >= 2)))
        return clean_results
