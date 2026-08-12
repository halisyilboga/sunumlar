"""Built-in standard Shell / Readline / ZLE / Vim keybindings for terminal and editor mastery."""

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
        "tags": ["transpose", "degistir", "değiştir", "kelime", "word", "zsh", "bash", "shell"],
        "tool": "zsh",
    },
    {
        "combo": "alt+.",
        "action": "insert-last-word",
        "desc": "Önceki komutun son argümanını yapıştır / Insert last argument of previous command",
        "tags": ["argument", "arguman", "onceki", "gecmis", "history", "yapistir", "zsh", "bash", "shell"],
        "tool": "zsh",
    },
    {
        "combo": "ctrl+x ctrl+e",
        "action": "edit-command-line",
        "desc": "Mevcut komutu tam $EDITOR içinde düzenle / Edit command line in full editor (Vim/Nvim)",
        "tags": ["editor", "vim", "nvim", "duzenle", "edit", "command", "satir", "zsh", "bash"],
        "tool": "zsh",
    },
    {
        "combo": "alt+q",
        "action": "push-line-or-edit",
        "desc": "Yazılan komutu geçici olarak sakla, acil komut çalıştır ve geri getir / Push line to buffer",
        "tags": ["push", "buffer", "gecici", "sakla", "zsh", "zle"],
        "tool": "zsh",
    },
]


# Universal Vim & Neovim motions, operators, and essential commands
NEOVIM_BUILTIN_BINDINGS = [
    # --- Line & Word Deletion / Change ---
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

    # --- Search & Replace Commands ---
    {
        "combo": ":%s/eski/yeni/g",
        "action": "search-replace-all",
        "desc": "Tüm dosya içinde metni bul ve değiştir / Global find and replace",
        "tags": ["replace", "degistir", "değiştir", "bul", "search", "global", "tum", "tüm", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
    {
        "combo": ":%s/eski/yeni/gc",
        "action": "search-replace-confirm",
        "desc": "Tüm dosya içinde onay isteyerek bul ve değiştir / Find and replace with confirmation",
        "tags": ["replace", "degistir", "değiştir", "onay", "confirm", "search", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
    {
        "combo": ":g/desen/d",
        "action": "delete-matching-lines",
        "desc": "Belirtilen desene uyan tüm satırları sil / Delete all lines matching pattern",
        "tags": ["delete", "sil", "desen", "pattern", "matching", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },

    # --- Windows, Splits & Buffers ---
    {
        "combo": "ctrl+w v",
        "action": "vsplit",
        "desc": "Pencereyi dikey böl (yan yana) / Split window vertically",
        "tags": ["split", "vsplit", "dikey", "bol", "window", "pencere", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
    {
        "combo": "ctrl+w s",
        "action": "split",
        "desc": "Pencereyi yatay böl (alt alta) / Split window horizontally",
        "tags": ["split", "yatay", "bol", "window", "pencere", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
    {
        "combo": "ctrl+w =",
        "action": "equalize-windows",
        "desc": "Tüm açık bölme pencerelerinin boyutunu eşitle / Equalize split window sizes",
        "tags": ["split", "esitle", "boyut", "equal", "window", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
    {
        "combo": "ctrl+w q",
        "action": "quit-window",
        "desc": "Mevcut bölme penceresini kapat / Close current split window",
        "tags": ["quit", "close", "kapat", "window", "split", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
    {
        "combo": ":bd",
        "action": "bdelete",
        "desc": "Mevcut açık dosyayı (buffer) kapat / Delete current buffer",
        "tags": ["buffer", "tampon", "kapat", "bdelete", "dosya", "close", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
    {
        "combo": ":bnext",
        "action": "bnext",
        "desc": "Sonraki açık tampon dosyaya geç / Switch to next buffer",
        "tags": ["buffer", "tampon", "next", "sonraki", "gecis", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
    {
        "combo": ":bprev",
        "action": "bprev",
        "desc": "Önceki açık tampon dosyaya geç / Switch to previous buffer",
        "tags": ["buffer", "tampon", "prev", "onceki", "gecis", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
    {
        "combo": ":ls",
        "action": "list-buffers",
        "desc": "Açık olan tüm tampon dosyaları listele / List all open buffers",
        "tags": ["buffer", "tampon", "list", "ls", "dosyalar", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },

    # --- Navigation, Folding & Macros ---
    {
        "combo": "gg",
        "action": "top-of-file",
        "desc": "Dosyanın en başına git / Jump to top of file",
        "tags": ["top", "bas", "başa", "git", "goto", "jump", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
    {
        "combo": "G",
        "action": "bottom-of-file",
        "desc": "Dosyanın en sonuna git / Jump to bottom of file",
        "tags": ["bottom", "son", "sonuna", "git", "goto", "jump", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
    {
        "combo": "%",
        "action": "match-paren",
        "desc": "Eşleşen parantez veya bloğa atla / Jump to matching parenthesis or bracket",
        "tags": ["bracket", "paren", "parantez", "eslesen", "atla", "jump", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
    {
        "combo": "*",
        "action": "search-word-forward",
        "desc": "İmlecin altındaki kelimeyi ileriye doğru ara / Search current word forward",
        "tags": ["search", "ara", "kelime", "word", "ileri", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
    {
        "combo": "ctrl+v",
        "action": "visual-block",
        "desc": "Sütun/blok görsel seçim moduna geç / Enter visual block mode",
        "tags": ["visual", "block", "sutun", "kolon", "secim", "select", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
    {
        "combo": "za",
        "action": "toggle-fold",
        "desc": "Kod bloğu katlamasını aç/kapat / Toggle code fold",
        "tags": ["fold", "katla", "ac", "kapat", "toggle", "kod", "blok", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
    {
        "combo": "qa",
        "action": "record-macro",
        "desc": "'a' harfine makro kaydetmeye başla (q ile durdur) / Record macro into register 'a'",
        "tags": ["macro", "makro", "kaydet", "record", "otomasyon", "neovim", "nvim", "vim"],
        "tool": "neovim",
    },
    {
        "combo": "@a",
        "action": "play-macro",
        "desc": "'a' harfine kaydedilen makroyu oynat / Execute macro 'a'",
        "tags": ["macro", "makro", "oynat", "calistir", "play", "neovim", "nvim", "vim"],
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
