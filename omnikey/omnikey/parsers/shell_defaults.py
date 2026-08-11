"""Built-in standard Shell / Readline / ZLE / Vim keybindings for terminal mastery."""

from pathlib import Path
from typing import List

from omnikey.models import Keybinding
from omnikey.parsers.base import BaseParser
from omnikey.semantic.tagger import SemanticTagger


# Universal Unix Shell / Readline / Zsh ZLE standard bindings
SHELL_BUILTIN_BINDINGS = [
    {
        "combo": "ctrl+k",
        "action": "kill-line",
        "desc": "Satırın sonuna kadar sil / Kill line from cursor to end",
        "tags": ["line", "satir", "satır", "kill", "sil", "silme", "delete", "end", "son", "sonuna", "cursor", "imlec", "imleç", "zsh", "bash", "shell", "readline", "hepsini", "kes"],
        "tool": "zsh",
    },
    {
        "combo": "ctrl+u",
        "action": "backward-kill-line",
        "desc": "Satırın başına kadar sil veya tüm satırı temizle / Kill line from cursor to beginning (clear line)",
        "tags": ["line", "satir", "satır", "clear", "temizle", "sil", "silme", "delete", "beginning", "baş", "basa", "başa", "start", "all", "hepsini", "zsh", "bash", "shell", "readline"],
        "tool": "zsh",
    },
    {
        "combo": "ctrl+w",
        "action": "backward-kill-word",
        "desc": "İmleçten önceki kelimeyi sil / Backward kill word before cursor",
        "tags": ["word", "kelime", "sil", "silme", "delete", "kill", "backward", "geri", "zsh", "bash", "shell", "readline"],
        "tool": "zsh",
    },
    {
        "combo": "alt+d",
        "action": "kill-word",
        "desc": "İmleçten sonraki kelimeyi sil / Kill word forward after cursor",
        "tags": ["word", "kelime", "sil", "silme", "delete", "kill", "forward", "ileri", "zsh", "bash", "shell", "readline"],
        "tool": "zsh",
    },
    {
        "combo": "ctrl+a",
        "action": "beginning-of-line",
        "desc": "Satırın en başına git / Move cursor to beginning of line",
        "tags": ["line", "satir", "satır", "beginning", "baş", "basa", "başa", "start", "cursor", "imlec", "imleç", "home", "git", "goto", "zsh", "bash", "shell", "readline"],
        "tool": "zsh",
    },
    {
        "combo": "ctrl+e",
        "action": "end-of-line",
        "desc": "Satırın en sonuna git / Move cursor to end of line",
        "tags": ["line", "satir", "satır", "end", "son", "sonuna", "cursor", "imlec", "imleç", "git", "goto", "zsh", "bash", "shell", "readline"],
        "tool": "zsh",
    },
    {
        "combo": "alt+f",
        "action": "forward-word",
        "desc": "Bir kelime ileri git / Move cursor forward one word",
        "tags": ["word", "kelime", "forward", "ileri", "cursor", "imlec", "imleç", "git", "goto", "zsh", "bash", "shell", "readline"],
        "tool": "zsh",
    },
    {
        "combo": "alt+b",
        "action": "backward-word",
        "desc": "Bir kelime geri git / Move cursor backward one word",
        "tags": ["word", "kelime", "backward", "geri", "cursor", "imlec", "imleç", "git", "goto", "zsh", "bash", "shell", "readline"],
        "tool": "zsh",
    },
    {
        "combo": "ctrl+l",
        "action": "clear-screen",
        "desc": "Terminal ekranını temizle / Clear terminal screen buffer",
        "tags": ["clear", "temizle", "ekran", "screen", "terminal", "zsh", "bash", "shell"],
        "tool": "zsh",
    },
    {
        "combo": "ctrl+c",
        "action": "send-break",
        "desc": "Satırı iptal et / yeni satıra geç / Cancel current line or interrupt running process",
        "tags": ["cancel", "iptal", "vazgec", "vazgeç", "interrupt", "line", "satir", "satır", "stop", "durdur", "zsh", "bash", "shell"],
        "tool": "zsh",
    },
    {
        "combo": "ctrl+r",
        "action": "history-incremental-search-backward",
        "desc": "Komut geçmişinde arama yap / Search command history backwards",
        "tags": ["history", "gecmis", "geçmiş", "search", "ara", "arama", "find", "bul", "zsh", "bash", "shell"],
        "tool": "zsh",
    },
    {
        "combo": "ctrl+z",
        "action": "suspend-process",
        "desc": "İşlemi arka plana gönder / Suspend current foreground job to background",
        "tags": ["suspend", "background", "arkaplan", "durdur", "zsh", "bash", "shell"],
        "tool": "zsh",
    },
    {
        "combo": "ctrl+d",
        "action": "delete-char-or-list",
        "desc": "Karakter sil veya kabuk oturumunu kapat (EOF) / Delete char or exit shell",
        "tags": ["delete", "sil", "exit", "cikis", "çıkış", "eof", "quit", "kapat", "zsh", "bash", "shell"],
        "tool": "zsh",
    },
    {
        "combo": "ctrl+_",
        "action": "undo",
        "desc": "Satır düzenlemesini geri al / Undo last editing change on line",
        "tags": ["undo", "geri-al", "geri", "revert", "edit", "duzenle", "zsh", "bash", "shell", "readline"],
        "tool": "zsh",
    },
    {
        "combo": "ctrl+t",
        "action": "transpose-chars",
        "desc": "İki karakterin yerini değiştir / Transpose characters",
        "tags": ["transpose", "degistir", "değiştir", "karakter", "zsh", "bash", "shell"],
        "tool": "zsh",
    },
    {
        "combo": "alt+t",
        "action": "transpose-words",
        "desc": "İki kelimenin yerini değiştir / Transpose words",
        "tags": ["transpose", "degistir", "değiştir", "word", "kelime", "zsh", "bash", "shell"],
        "tool": "zsh",
    },
    {
        "combo": "alt+u",
        "action": "up-case-word",
        "desc": "Kelimeyi BÜYÜK harfe çevir / Uppercase word",
        "tags": ["uppercase", "buyuk-harf", "büyük-harf", "word", "kelime", "zsh", "bash", "shell"],
        "tool": "zsh",
    },
    {
        "combo": "alt+l",
        "action": "down-case-word",
        "desc": "Kelimeyi küçük harfe çevir / Lowercase word",
        "tags": ["lowercase", "kucuk-harf", "küçük-harf", "word", "kelime", "zsh", "bash", "shell"],
        "tool": "zsh",
    },
    {
        "combo": "alt+c",
        "action": "capitalize-word",
        "desc": "Kelimenin ilk harfini büyük yap / Capitalize word",
        "tags": ["capitalize", "bas-harf", "baş-harf", "word", "kelime", "zsh", "bash", "shell"],
        "tool": "zsh",
    },
]

# Neovim / Vim Essential Builtin Line & Text Editing Bindings
NEOVIM_BUILTIN_BINDINGS = [
    {
        "combo": "D",
        "action": "delete-to-eol",
        "desc": "İmleçten satırın sonuna kadar sil / Delete from cursor to end of line",
        "tags": ["line", "satir", "satır", "kill", "sil", "silme", "delete", "end", "son", "sonuna", "cursor", "imlec", "imleç", "neovim", "nvim", "vim", "hepsini", "kes"],
        "tool": "neovim",
    },
    {
        "combo": "d0",
        "action": "delete-to-bol",
        "desc": "İmleçten satırın başına kadar sil / Delete from cursor to start of line",
        "tags": ["line", "satir", "satır", "sil", "silme", "delete", "beginning", "baş", "basa", "başa", "start", "cursor", "imlec", "imleç", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
    {
        "combo": "dd",
        "action": "delete-line",
        "desc": "Tüm satırı sil / Delete entire current line",
        "tags": ["line", "satir", "satır", "sil", "silme", "delete", "all", "hepsini", "tum", "tüm", "entire", "neovim", "nvim", "vim", "cut", "kes"],
        "tool": "neovim",
    },
    {
        "combo": "C",
        "action": "change-to-eol",
        "desc": "Satır sonuna kadar sil ve yazma moduna geç / Change to end of line (Insert mode)",
        "tags": ["line", "satir", "satır", "sil", "degistir", "değiştir", "change", "end", "son", "sonuna", "insert", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
    {
        "combo": "cc",
        "action": "change-line",
        "desc": "Tüm satırı sil ve yazma moduna geç / Change whole line",
        "tags": ["line", "satir", "satır", "sil", "degistir", "değiştir", "change", "insert", "all", "hepsini", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
    {
        "combo": "ciw",
        "action": "change-inner-word",
        "desc": "Kelimeyi sil ve yazma moduna geç / Change inner word",
        "tags": ["word", "kelime", "sil", "degistir", "değiştir", "change", "insert", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
    {
        "combo": "diw",
        "action": "delete-inner-word",
        "desc": "İmlecin altındaki kelimeyi sil / Delete inner word",
        "tags": ["word", "kelime", "sil", "silme", "delete", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
    {
        "combo": "daw",
        "action": "delete-around-word",
        "desc": "Kelimeyi boşluğuyla birlikte sil / Delete a word with whitespace",
        "tags": ["word", "kelime", "sil", "silme", "delete", "around", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
    {
        "combo": "yy",
        "action": "yank-line",
        "desc": "Satırı kopyala / Yank (copy) current line to register",
        "tags": ["copy", "kopyala", "yank", "line", "satir", "satır", "panoya-al", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
    {
        "combo": "p",
        "action": "put-after",
        "desc": "İmleçten sonrasına yapıştır / Paste clipboard/register after cursor",
        "tags": ["paste", "yapistir", "yapıştır", "put", "clipboard", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
    {
        "combo": "P",
        "action": "put-before",
        "desc": "İmleçten öncesine yapıştır / Paste clipboard/register before cursor",
        "tags": ["paste", "yapistir", "yapıştır", "put", "clipboard", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
    {
        "combo": "u",
        "action": "undo",
        "desc": "Son değişikliği geri al / Undo last change",
        "tags": ["undo", "geri-al", "geri", "revert", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
    {
        "combo": "ctrl+r",
        "action": "redo",
        "desc": "Geri alınan değişikliği ileri al / Redo last undone change",
        "tags": ["redo", "ileri-al", "yinele", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
]


class ShellDefaultsParser(BaseParser):
    """Provides standard, universal Readline, Shell, and Vim built-in bindings."""

    @property
    def tool_name(self) -> str:
        return "builtin"

    def can_handle(self, file_path: Path) -> bool:
        return "builtin" in str(file_path).lower()

    def parse(self, file_path: Path) -> List[Keybinding]:
        return self.get_all_builtins()

    @classmethod
    def get_all_builtins(cls) -> List[Keybinding]:
        """Return all built-in shell and editor keybindings."""
        results: List[Keybinding] = []
        source_shell = "builtin://shell_defaults"
        source_nvim = "builtin://neovim_defaults"

        for b in SHELL_BUILTIN_BINDINGS:
            tags = SemanticTagger.generate_tags(
                tool=b["tool"],
                key_combo=b["combo"],
                action_raw=b["action"],
                description=b["desc"],
                mode="builtin",
            )
            # Add explicit extra tags
            tags = sorted(list(set(tags + b["tags"])))
            results.append(
                Keybinding(
                    tool=b["tool"],
                    key_combo=b["combo"],
                    action_raw=b["action"],
                    description=b["desc"],
                    source_file=source_shell,
                    mode="builtin",
                    tags=tags,
                )
            )

        for b in NEOVIM_BUILTIN_BINDINGS:
            tags = SemanticTagger.generate_tags(
                tool=b["tool"],
                key_combo=b["combo"],
                action_raw=b["action"],
                description=b["desc"],
                mode="normal",
            )
            tags = sorted(list(set(tags + b["tags"])))
            results.append(
                Keybinding(
                    tool=b["tool"],
                    key_combo=b["combo"],
                    action_raw=b["action"],
                    description=b["desc"],
                    source_file=source_nvim,
                    mode="normal",
                    tags=tags,
                )
            )

        return results
